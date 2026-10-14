"""
daily-job-internship-alerts — job_alert.py
==========================================
Fetches remote jobs & internships from 100+ sources:
  - 5 Public APIs: Himalayas, Remotive, Jobicy, RemoteOK, Arbeitnow
  - Optional LinkedIn guest search (past 24h jobs, via ENABLE_LINKEDIN=true)
  - 100+ Top Tech Companies via ATS APIs (Greenhouse, Lever, Ashby)
  - Custom sources & resources configured in custom_sources.json / custom_sources.py

Deduplicates listings, applies keyword and interest filters, highlights fresh
postings (last 24 hours), and delivers a modern, responsive HTML digest email.
"""

import os
import json
import hashlib
import smtplib
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from source_manager import get_active_companies, get_custom_feeds

# ---------------------------------------------------------------------------
# Bootstrap & Logging
# ---------------------------------------------------------------------------

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EMAIL_FROM      = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD  = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO_RAW    = os.getenv("EMAIL_TO", "")
EMAIL_TO        = [e.strip() for e in EMAIL_TO_RAW.split(",") if e.strip()]
KEYWORDS_RAW    = os.getenv("KEYWORDS", "")
KEYWORDS        = [k.strip().lower() for k in KEYWORDS_RAW.split(",") if k.strip()]

ENABLE_LINKEDIN = os.getenv("ENABLE_LINKEDIN", "false").strip().lower() in ("true", "1", "yes")

SEEN_JOBS_FILE  = Path("seen_jobs.json")
REQUEST_TIMEOUT = 12            # seconds per ATS / API call
MAX_WORKERS     = 20            # concurrent HTTP worker threads
MAX_JOBS_PER_SOURCE = 25        # cap per source to keep email digest curated

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) daily-job-alerts/2.0"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

# ---------------------------------------------------------------------------
# Deduplication helpers
# ---------------------------------------------------------------------------

def load_seen_jobs() -> set:
    """Load previously seen job hashes from disk."""
    if SEEN_JOBS_FILE.exists():
        try:
            data = json.loads(SEEN_JOBS_FILE.read_text(encoding="utf-8"))
            return set(data)
        except (json.JSONDecodeError, IOError) as exc:
            log.warning("Could not load seen_jobs.json: %s", exc)
    return set()


def save_seen_jobs(seen: set) -> None:
    """Persist seen job hashes to disk."""
    try:
        SEEN_JOBS_FILE.write_text(
            json.dumps(sorted(seen), indent=2), encoding="utf-8"
        )
    except IOError as exc:
        log.warning("Could not save seen_jobs.json: %s", exc)


def job_hash(title: str, company: str, url: str) -> str:
    """Stable SHA-256 fingerprint for a job listing."""
    key = f"{title.lower().strip()}|{company.lower().strip()}|{url.strip()}"
    return hashlib.sha256(key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Keyword filtering & text helpers
# ---------------------------------------------------------------------------

def matches_keywords(job: dict) -> bool:
    """Return True if job matches configured keywords (or if no keywords set)."""
    if not KEYWORDS:
        return True
    haystack = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()
    return any(kw in haystack for kw in KEYWORDS)


def _truncate(text: str, max_len: int = 280) -> str:
    """Strip HTML tags crudely and truncate cleanly to max_len characters."""
    import re
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > max_len:
        return clean[:max_len].rsplit(" ", 1)[0] + "…"
    return clean


def _is_internship(title: str, tags: str = "", commitment: str = "") -> bool:
    """Detect if listing is an internship, co-op, or apprentice role."""
    combined = f"{title} {tags} {commitment}".lower()
    keywords = ["intern", "internship", "co-op", "apprentice", "working student", "student worker"]
    return any(k in combined for k in keywords)


def is_within_last_24h(date_val: Any) -> bool:
    """
    Determine if date_val represents a publication date or timestamp within the last 24 hours.
    Handles Unix timestamps (seconds or ms), ISO-8601 datetimes, and boolean flags.
    """
    if date_val is None or date_val == "":
        return False
    if isinstance(date_val, bool):
        return date_val
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        if isinstance(date_val, (int, float)):
            # Handle timestamps in milliseconds
            if date_val > 1e11:
                date_val = date_val / 1000.0
            dt = datetime.datetime.fromtimestamp(date_val, tz=datetime.timezone.utc)
            diff = (now - dt).total_seconds()
            return 0 <= diff <= 86400
        elif isinstance(date_val, str):
            clean_str = date_val.strip().replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            diff = (now - dt).total_seconds()
            return 0 <= diff <= 86400
    except Exception:
        pass
    return False


def _safe_get(url: str, **kwargs) -> requests.Response | None:
    """Polite GET request with error handling and custom User-Agent."""
    try:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        h = dict(HEADERS)
        if "headers" in kwargs:
            h.update(kwargs.pop("headers"))
        resp = requests.get(url, headers=h, **kwargs)
        if resp.status_code == 200:
            return resp
        return None
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# 1. Public Free Job Boards
# ---------------------------------------------------------------------------


def fetch_himalayas_jobs() -> list[dict]:
    """Himalayas.app public Browse API — Remote tech jobs."""
    resp = _safe_get("https://himalayas.app/jobs/api", params={"limit": MAX_JOBS_PER_SOURCE, "sort": "recent"})
    if not resp:
        return []
    try:
        data = resp.json()
    except Exception:
        return []

    jobs = []
    for item in data.get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        s_min = item.get("minSalary") or item.get("salaryMin")
        s_max = item.get("maxSalary") or item.get("salaryMax")
        curr = item.get("currency") or "USD"
        sym = "$" if curr == "USD" else f"{curr} "
        period = f" / {item.get('salaryPeriod')}" if item.get("salaryPeriod") else " / yr"
        salary = f"{sym}{s_min:,}–{sym}{s_max:,}{period}" if s_min and s_max else (f"{sym}{s_min:,}+{period}" if s_min else "")

        title = item.get("title", "N/A")
        loc = item.get("locationRestrictions") or "Remote"
        if isinstance(loc, list):
            loc = ", ".join(loc) if loc else "Remote"

        pub_date = item.get("pubDate")
        is_recent = is_within_last_24h(pub_date)

        emp_type = str(item.get("employmentType", ""))
        is_intern = "intern" in emp_type.lower() or _is_internship(title)

        desc = item.get("excerpt") or _truncate(item.get("description", ""))
        url = item.get("applicationLink") or item.get("url") or "#"
        categories = item.get("categories", [])
        tag_str = ", ".join(categories) if isinstance(categories, list) else str(categories)

        jobs.append({
            "title":       title,
            "company":     item.get("companyName", "N/A"),
            "location":    loc,
            "salary":      salary,
            "description": desc,
            "url":         url,
            "source":      "Himalayas.app",
            "type":        "internship" if is_intern else "job",
            "tags":        tag_str,
            "is_recent":   is_recent,
            "posted_ts":   pub_date if isinstance(pub_date, (int, float)) else 0,
        })
    return jobs


def fetch_himalayas_internships() -> list[dict]:
    """Himalayas.app public Search API — Internships filter."""
    params: dict[str, Any] = {
        "employment_type": "Intern",
        "sort": "recent",
        "limit": MAX_JOBS_PER_SOURCE,
    }
    if KEYWORDS:
        params["q"] = " ".join(KEYWORDS)

    resp = _safe_get("https://himalayas.app/jobs/api/search", params=params)
    if not resp:
        return []
    try:
        data = resp.json()
    except Exception:
        return []

    internships = []
    for item in data.get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        s_min = item.get("minSalary") or item.get("salaryMin")
        s_max = item.get("maxSalary") or item.get("salaryMax")
        curr = item.get("currency") or "USD"
        sym = "$" if curr == "USD" else f"{curr} "
        period = f" / {item.get('salaryPeriod')}" if item.get("salaryPeriod") else " / yr"
        salary = f"{sym}{s_min:,}–{sym}{s_max:,}{period}" if s_min and s_max else (f"{sym}{s_min:,}+{period}" if s_min else "")

        title = item.get("title", "N/A")
        loc = item.get("locationRestrictions") or "Remote"
        if isinstance(loc, list):
            loc = ", ".join(loc) if loc else "Remote"

        pub_date = item.get("pubDate")
        is_recent = is_within_last_24h(pub_date)
        desc = item.get("excerpt") or _truncate(item.get("description", ""))
        url = item.get("applicationLink") or item.get("url") or "#"
        categories = item.get("categories", [])
        tag_str = ", ".join(categories) if isinstance(categories, list) else str(categories)

        internships.append({
            "title":       title,
            "company":     item.get("companyName", "N/A"),
            "location":    loc,
            "salary":      salary,
            "description": desc,
            "url":         url,
            "source":      "Himalayas.app",
            "type":        "internship",
            "tags":        tag_str,
            "is_recent":   is_recent,
            "posted_ts":   pub_date if isinstance(pub_date, (int, float)) else 0,
        })
    return internships


def fetch_remotive() -> list[dict]:
    """Remotive free public API."""
    resp = _safe_get("https://remotive.com/api/remote-jobs", params={"limit": MAX_JOBS_PER_SOURCE})
    if not resp:
        return []
    jobs = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("title", "N/A")
        tags = item.get("tags") or ""
        if isinstance(tags, list):
            tags = ", ".join(tags)
        is_intern = _is_internship(title, tags=tags, commitment=item.get("job_type", ""))
        pub_date = item.get("publication_date")
        is_recent = is_within_last_24h(pub_date)

        jobs.append({
            "title":       title,
            "company":     item.get("company_name", "N/A"),
            "location":    item.get("candidate_required_location") or "Worldwide",
            "salary":      item.get("salary", ""),
            "description": _truncate(item.get("description", "")),
            "url":         item.get("url", "#"),
            "source":      "Remotive.com",
            "type":        "internship" if is_intern else "job",
            "tags":        tags,
            "is_recent":   is_recent,
            "posted_ts":   pub_date or 0,
        })
    return jobs


def fetch_jobicy() -> list[dict]:
    """Jobicy public API."""
    resp = _safe_get("https://jobicy.com/api/v2/remote-jobs", params={"count": MAX_JOBS_PER_SOURCE})
    if not resp:
        return []
    jobs = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("jobTitle", "N/A")
        pub_date = item.get("pubDate")
        is_recent = is_within_last_24h(pub_date)

        jobs.append({
            "title":       title,
            "company":     item.get("companyName", "N/A"),
            "location":    item.get("jobGeo") or "Remote",
            "salary":      item.get("annualSalaryMax", ""),
            "description": _truncate(item.get("jobExcerpt", "")),
            "url":         item.get("url", "#"),
            "source":      "Jobicy.com",
            "type":        "internship" if _is_internship(title) else "job",
            "tags":        ", ".join(item.get("jobIndustry", [])),
            "is_recent":   is_recent,
            "posted_ts":   pub_date or 0,
        })
    return jobs


def fetch_remoteok() -> list[dict]:
    """RemoteOK public API."""
    resp = _safe_get("https://remoteok.com/api")
    if not resp:
        return []
    raw = resp.json()
    if isinstance(raw, list) and len(raw) > 1:
        raw = raw[1:]  # first element is legal notice
    else:
        return []
    jobs = []
    for item in raw[:MAX_JOBS_PER_SOURCE]:
        if not isinstance(item, dict):
            continue
        title = item.get("position", "N/A")
        tags = item.get("tags", [])
        tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
        epoch = item.get("epoch") or item.get("date")
        is_recent = is_within_last_24h(epoch)

        jobs.append({
            "title":       title,
            "company":     item.get("company", "N/A"),
            "location":    item.get("location") or "Remote",
            "salary":      item.get("salary", ""),
            "description": _truncate(item.get("description", "")),
            "url":         item.get("url") or f"https://remoteok.com/l/{item.get('id', '')}",
            "source":      "RemoteOK.com",
            "type":        "internship" if _is_internship(title, tags=tag_str) else "job",
            "tags":        tag_str,
            "is_recent":   is_recent,
            "posted_ts":   item.get("epoch") or 0,
        })
    return jobs


def fetch_arbeitnow() -> list[dict]:
    """Arbeitnow public job board API."""
    resp = _safe_get("https://www.arbeitnow.com/api/job-board-api")
    if not resp:
        return []
    jobs = []
    for item in resp.json().get("data", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("title", "N/A")
        tags = ", ".join(item.get("tags", []))
        created_at = item.get("created_at")
        is_recent = is_within_last_24h(created_at)

        jobs.append({
            "title":       title,
            "company":     item.get("company_name", "N/A"),
            "location":    item.get("location") or "Remote",
            "salary":      "",
            "description": _truncate(item.get("description", "")),
            "url":         item.get("url", "#"),
            "source":      "Arbeitnow",
            "type":        "internship" if _is_internship(title, tags=tags) else "job",
            "tags":        tags,
            "is_recent":   is_recent,
            "posted_ts":   created_at or 0,
        })
    return jobs


def fetch_linkedin_jobs() -> list[dict]:
    """
    Fetch public job listings from LinkedIn's guest job search endpoint from the last 24 hours.

    DISCLAIMER & WARNING:
    This endpoint (linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search) is unofficial,
    unsupported, and may break at any time. It enforces aggressive rate limits (HTTP 429)
    and scraping LinkedIn may violate LinkedIn's Terms of Service.
    Use exclusively for personal email alerts at your own risk.
    """
    if not ENABLE_LINKEDIN:
        return []

    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    query = " ".join(KEYWORDS) if KEYWORDS else "software"
    params = {
        "keywords": query,
        "location": "Remote",
        "f_TPR": "r86400",  # past 24 hours (86,400 seconds)
        "start": 0,
    }
    linkedin_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, params=params, headers=linkedin_headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            log.warning("LinkedIn guest API rate limited (HTTP 429). Skipping LinkedIn fetch.")
            return []
        if resp.status_code != 200:
            log.warning("LinkedIn guest API returned HTTP %d. Skipping LinkedIn fetch.", resp.status_code)
            return []

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            log.error("beautifulsoup4 is required to parse LinkedIn jobs. Run 'pip install beautifulsoup4'.")
            return []

        import re
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("li")
        if not items:
            items = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))

        jobs = []
        for item in items[:MAX_JOBS_PER_SOURCE]:
            title_el = item.find(["h3", "h4"], class_=re.compile(r"base-search-card__title|job-title"))
            title = title_el.get_text(strip=True) if title_el else ""
            if not title or title.lower() == "n/a":
                continue

            comp_el = item.find(["h4", "h3", "a"], class_=re.compile(r"base-search-card__subtitle|hidden-nested-link|company-name"))
            company = comp_el.get_text(strip=True) if comp_el else "Unknown"

            loc_el = item.find("span", class_=re.compile(r"job-search-card__location"))
            location = loc_el.get_text(strip=True) if loc_el else "Remote"

            link_el = item.find("a", class_=re.compile(r"base-card__full-link|job-search-card"))
            job_url = link_el["href"] if link_el and link_el.has_attr("href") else "#"
            if "?" in job_url:
                job_url = job_url.split("?")[0]

            time_el = item.find("time")
            posted_text = time_el.get_text(strip=True) if time_el else "Past 24h"

            is_intern = _is_internship(title)

            jobs.append({
                "title":       title,
                "company":     company,
                "location":    location,
                "salary":      "",
                "description": f"Posted recently on LinkedIn ({posted_text}). Apply directly on LinkedIn.",
                "url":         job_url,
                "source":      "LinkedIn",
                "type":        "internship" if is_intern else "job",
                "tags":        "LinkedIn, 24h",
                "is_recent":   True,
                "posted_ts":   datetime.datetime.now(datetime.timezone.utc).timestamp(),
            })
        return jobs
    except Exception as exc:
        log.warning("Could not fetch LinkedIn jobs: %s", exc)
        return []



# ---------------------------------------------------------------------------
# 2. Company ATS Fetchers (Greenhouse, Lever, Ashby)
# ---------------------------------------------------------------------------

def fetch_greenhouse_company(company: dict) -> list[dict]:
    """Fetch live jobs directly from a company's Greenhouse job board."""
    name = company.get("name", "Unknown")
    token = company.get("token", "")
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    resp = _safe_get(url)
    if not resp:
        return []

    jobs = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("title", "N/A")
        loc_obj = item.get("location") or {}
        location = loc_obj.get("name") if isinstance(loc_obj, dict) else str(loc_obj)
        departments = [d.get("name") for d in item.get("departments", []) if isinstance(d, dict) and d.get("name")]
        tag_str = ", ".join(departments)
        updated_at = item.get("updated_at")
        is_recent = is_within_last_24h(updated_at)

        jobs.append({
            "title":       title,
            "company":     name,
            "location":    location or "Remote",
            "salary":      "",
            "description": f"Direct opening on {name}'s official career board ({tag_str})." if tag_str else f"Direct opening on {name}'s official career board.",
            "url":         item.get("absolute_url") or "#",
            "source":      f"{name} (Greenhouse)",
            "type":        "internship" if _is_internship(title, tags=tag_str) else "job",
            "tags":        tag_str,
            "is_recent":   is_recent,
            "posted_ts":   updated_at or 0,
        })
    return jobs


def fetch_lever_company(company: dict) -> list[dict]:
    """Fetch live jobs directly from a company's Lever job board."""
    name = company.get("name", "Unknown")
    token = company.get("token", "")
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    resp = _safe_get(url)
    if not resp:
        return []

    data = resp.json()
    if not isinstance(data, list):
        return []

    jobs = []
    for item in data[:MAX_JOBS_PER_SOURCE]:
        if not isinstance(item, dict):
            continue
        title = item.get("text", "N/A")
        cat = item.get("categories") or {}
        location = cat.get("location") or "Remote"
        commitment = cat.get("commitment") or ""
        team = cat.get("team") or ""
        tag_str = ", ".join([t for t in [team, commitment] if t])
        created_at = item.get("createdAt")
        is_recent = is_within_last_24h(created_at)

        jobs.append({
            "title":       title,
            "company":     name,
            "location":    location,
            "salary":      "",
            "description": f"Direct posting on {name} career portal ({tag_str})." if tag_str else f"Direct posting on {name} career portal.",
            "url":         item.get("hostedUrl") or item.get("applyUrl") or "#",
            "source":      f"{name} (Lever)",
            "type":        "internship" if _is_internship(title, tags=tag_str, commitment=commitment) else "job",
            "tags":        tag_str,
            "is_recent":   is_recent,
            "posted_ts":   created_at or 0,
        })
    return jobs


def fetch_ashby_company(company: dict) -> list[dict]:
    """Fetch live jobs directly from a company's Ashby job board."""
    name = company.get("name", "Unknown")
    token = company.get("token", "")
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    resp = _safe_get(url)
    if not resp:
        return []

    jobs = []
    for item in resp.json().get("jobs", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("title", "N/A")
        location = item.get("location") or "Remote"
        dept = item.get("department") or ""
        published_at = item.get("publishedAt")
        is_recent = is_within_last_24h(published_at)

        jobs.append({
            "title":       title,
            "company":     name,
            "location":    location,
            "salary":      "",
            "description": f"Official position at {name} ({dept})." if dept else f"Official position at {name}.",
            "url":         item.get("jobUrl") or "#",
            "source":      f"{name} (Ashby)",
            "type":        "internship" if _is_internship(title, tags=dept) else "job",
            "tags":        dept,
            "is_recent":   is_recent,
            "posted_ts":   published_at or 0,
        })
    return jobs


def fetch_ats_company(company: dict) -> list[dict]:
    """Route company to the appropriate ATS fetcher."""
    ats = str(company.get("ats", "")).lower().strip()
    try:
        if ats == "greenhouse":
            return fetch_greenhouse_company(company)
        elif ats == "lever":
            return fetch_lever_company(company)
        elif ats == "ashby":
            return fetch_ashby_company(company)
    except Exception as exc:
        log.debug("Error fetching ATS company %s: %s", company.get("name"), exc)
    return []


# ---------------------------------------------------------------------------
# 3. Custom User Feeds (from custom_sources.json / custom_sources.py)
# ---------------------------------------------------------------------------

def fetch_custom_feed(feed: dict) -> list[dict]:
    """Fetch from user-defined custom JSON API feed."""
    name = feed.get("name", "Custom Feed")
    url = feed.get("url", "")
    if not url:
        return []
    resp = _safe_get(url)
    if not resp:
        return []

    jobs = []
    try:
        data = resp.json()
        items = data if isinstance(data, list) else data.get("jobs", data.get("data", []))
        for item in items[:MAX_JOBS_PER_SOURCE]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("jobTitle") or item.get("position") or "N/A"
            company = item.get("company") or item.get("companyName") or name
            location = item.get("location") or "Remote"
            url_link = item.get("url") or item.get("applicationLink") or "#"
            desc = _truncate(item.get("description", ""))
            raw_date = item.get("date") or item.get("pubDate") or item.get("created_at") or item.get("published_at")
            is_recent = is_within_last_24h(raw_date)

            jobs.append({
                "title":       title,
                "company":     company,
                "location":    location,
                "salary":      item.get("salary", ""),
                "description": desc,
                "url":         url_link,
                "source":      name,
                "type":        "internship" if _is_internship(title) else "job",
                "tags":        item.get("tags", ""),
                "is_recent":   is_recent,
                "posted_ts":   raw_date or 0,
            })
    except Exception as exc:
        log.warning("Could not parse custom feed %s: %s", name, exc)
    return jobs


# ---------------------------------------------------------------------------
# Aggregation & Concurrency
# ---------------------------------------------------------------------------

def fetch_all() -> tuple[list[dict], list[dict], int]:
    """
    Fetch from all enabled sources concurrently:
    - Merged default + custom companies
    - Public job boards (+ optional LinkedIn guest search)
    - Custom feeds
    Deduplicates against seen_jobs.json, filters keywords, and sorts by recency.
    Returns (regular_jobs, internships, total_sources_checked).
    """
    seen = load_seen_jobs()
    new_seen = set(seen)

    companies, interested_only, filter_sources = get_active_companies()
    custom_feeds = get_custom_feeds()

    public_board_fetchers = [
        ("Himalayas Jobs", fetch_himalayas_jobs),
        ("Himalayas Internships", fetch_himalayas_internships),
        ("Remotive", fetch_remotive),
        ("Jobicy", fetch_jobicy),
        ("RemoteOK", fetch_remoteok),
        ("Arbeitnow", fetch_arbeitnow),
    ]

    if ENABLE_LINKEDIN:
        public_board_fetchers.append(("LinkedIn (24h)", fetch_linkedin_jobs))

    # If user selected interested_only mode, skip generic public boards
    # unless specifically named in filter_sources
    active_public_fetchers = []
    for name, fn in public_board_fetchers:
        if interested_only:
            if filter_sources and any(f in name.lower() for f in filter_sources):
                active_public_fetchers.append((name, fn))
        else:
            if not filter_sources or any(f in name.lower() for f in filter_sources):
                active_public_fetchers.append((name, fn))

    total_sources_count = len(companies) + len(active_public_fetchers) + len(custom_feeds)
    log.info("Starting concurrent fetch across %d sources (max %d threads) …", total_sources_count, MAX_WORKERS)

    all_listings: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}

        # 1. Dispatch public board fetchers
        for name, fn in active_public_fetchers:
            futures[executor.submit(fn)] = name

        # 2. Dispatch company ATS fetchers
        for co in companies:
            futures[executor.submit(fetch_ats_company, co)] = co.get("name", "ATS Company")

        # 3. Dispatch custom feeds
        for feed in custom_feeds:
            futures[executor.submit(fetch_custom_feed, feed)] = feed.get("name", "Custom Feed")

        # Collect results
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                listings = future.result()
                if listings:
                    all_listings.extend(listings)
                    log.info("  ✓ %-24s: %2d listings", source_name, len(listings))
            except Exception as exc:
                log.debug("Source %s raised error: %s", source_name, exc)

    log.info("Total raw listings gathered: %d", len(all_listings))

    jobs, internships = [], []
    for listing in all_listings:
        h = job_hash(listing["title"], listing["company"], listing["url"])
        if h in seen:
            continue
        if not matches_keywords(listing):
            continue
        new_seen.add(h)
        if listing["type"] == "internship":
            internships.append(listing)
        else:
            jobs.append(listing)

    save_seen_jobs(new_seen)

    # Prefer fresher listings (posted within last 24h) first, then by timestamp
    def _recency_sort_key(item: dict) -> tuple:
        is_rec = 1 if item.get("is_recent") else 0
        ts = item.get("posted_ts", 0)
        if not isinstance(ts, (int, float)):
            ts = 0
        return (is_rec, ts)

    jobs.sort(key=_recency_sort_key, reverse=True)
    internships.sort(key=_recency_sort_key, reverse=True)

    log.info("New unique jobs: %d | New unique internships: %d", len(jobs), len(internships))
    return jobs, internships, total_sources_count


# ---------------------------------------------------------------------------
# HTML Email Digest Builder
# ---------------------------------------------------------------------------

def _job_card_html(job: dict, accent: str) -> str:
    """Render an individual job or internship card."""
    salary_html = (
        f'<span class="salary">💰 {job["salary"]}</span>' if job.get("salary") else ""
    )
    tags_html = (
        f'<p class="tags">🏷️ {job["tags"]}</p>' if job.get("tags") else ""
    )
    recent_badge = (
        '<span class="badge-recent">⚡ Last 24h</span>' if job.get("is_recent") else ""
    )
    return f"""
    <div class="card">
      <div class="card-header" style="border-left: 5px solid {accent};">
        <h3 class="job-title">{job['title']}</h3>
        <p class="company">🏢 {job['company']}</p>
        <div class="meta">
          <span class="location">📍 {job['location']}</span>
          {salary_html}
          <span class="source">🔗 {job['source']}</span>
          {recent_badge}
        </div>
      </div>
      {tags_html}
      <p class="description">{job['description']}</p>
      <a class="apply-btn" href="{job['url']}" target="_blank"
         style="background:{accent};">Apply Now →</a>
    </div>
    """



def build_html_email(jobs: list[dict], internships: list[dict], total_sources: int) -> str:
    """Assemble the complete HTML email body with live source statistics."""
    today = datetime.date.today().strftime("%B %d, %Y")
    total = len(jobs) + len(internships)

    jobs_html = "".join(_job_card_html(j, "#4F46E5") for j in jobs) if jobs else (
        '<p class="empty">No new job openings found matching your criteria today. Check back tomorrow!</p>'
    )
    internships_html = "".join(_job_card_html(i, "#059669") for i in internships) if internships else (
        '<p class="empty">No new internships found matching your criteria today. Check back tomorrow!</p>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Daily Job & Internship Digest — {today}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: #F3F4F6;
    color: #1F2937;
    line-height: 1.6;
  }}
  a {{ color: inherit; text-decoration: none; }}
  .wrapper {{
    max-width: 680px;
    margin: 0 auto;
    background: #FFFFFF;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .header {{
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    padding: 40px 32px;
    text-align: center;
    color: #FFFFFF;
  }}
  .header .emoji {{ font-size: 48px; display: block; margin-bottom: 12px; }}
  .header h1 {{ font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }}
  .header .subtitle {{ font-size: 14px; opacity: 0.85; margin-top: 6px; }}
  .header .badge {{
    display: inline-block;
    margin-top: 14px;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 100px;
    padding: 4px 16px;
    font-size: 13px;
    font-weight: 600;
  }}
  .stats {{
    display: flex;
    background: #1F2937;
    color: #FFFFFF;
    text-align: center;
  }}
  .stat {{ flex: 1; padding: 16px 8px; }}
  .stat .num {{ font-size: 24px; font-weight: 800; color: #A78BFA; }}
  .stat .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.7; margin-top: 2px; }}
  .stat-divider {{ width: 1px; background: rgba(255,255,255,0.1); margin: 12px 0; }}
  .section {{ padding: 32px; }}
  .section-title {{
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 12px;
    margin-bottom: 20px;
    border-bottom: 2px solid #E5E7EB;
  }}
  .section-divider {{ height: 8px; background: #F3F4F6; }}
  .card {{
    background: #FAFAFA;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    margin-bottom: 16px;
    overflow: hidden;
  }}
  .card-header {{ padding: 16px 20px 12px; background: #FFFFFF; }}
  .job-title {{ font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 4px; }}
  .company {{ font-size: 13px; color: #6B7280; margin-bottom: 8px; font-weight: 500; }}
  .meta {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: #6B7280; }}
  .location, .salary, .source, .badge-recent {{
    display: inline-flex; align-items: center; gap: 4px;
    background: #F3F4F6; border-radius: 6px; padding: 2px 8px;
  }}
  .salary {{ color: #065F46; background: #D1FAE5; }}
  .badge-recent {{
    background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D;
    font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px;
  }}
  .tags {{ padding: 8px 20px; font-size: 12px; color: #6B7280; background: #F9FAFB; }}
  .description {{
    padding: 12px 20px;
    font-size: 13px;
    color: #374151;
    line-height: 1.7;
    border-top: 1px solid #F3F4F6;
  }}
  .apply-btn {{
    display: block;
    text-align: center;
    padding: 12px;
    color: #FFFFFF !important;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.3px;
    text-decoration: none;
  }}
  .empty {{
    text-align: center;
    color: #9CA3AF;
    padding: 32px;
    font-size: 14px;
    background: #F9FAFB;
    border-radius: 10px;
    border: 1px dashed #D1D5DB;
  }}
  .footer {{
    background: #1F2937;
    color: #9CA3AF;
    text-align: center;
    padding: 28px 32px;
    font-size: 12px;
    line-height: 1.8;
  }}
  .footer a {{ color: #A78BFA; }}
  .footer .heart {{ color: #F87171; }}
</style>
</head>
<body>
<div class="wrapper">

  <!-- Header -->
  <div class="header">
    <span class="emoji">🚀</span>
    <h1>Daily Job & Internship Digest</h1>
    <p class="subtitle">Curated opportunities for <strong>{today}</strong></p>
    <span class="badge">{total} New Opportunities Today</span>
  </div>

  <!-- Live Stats -->
  <div class="stats">
    <div class="stat">
      <div class="num">{len(jobs)}</div>
      <div class="label">Job Openings</div>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <div class="num">{len(internships)}</div>
      <div class="label">Internships</div>
    </div>
    <div class="stat-divider"></div>
    <div class="stat">
      <div class="num">{total_sources}</div>
      <div class="label">Sources Checked</div>
    </div>
  </div>

  <!-- Jobs Section -->
  <div class="section">
    <div class="section-title">
      <span>💼</span> Job Openings
    </div>
    {jobs_html}
  </div>

  <div class="section-divider"></div>

  <!-- Internships Section -->
  <div class="section">
    <div class="section-title">
      <span>🎓</span> Internships &amp; Early Career
    </div>
    {internships_html}
  </div>

  <!-- Footer -->
  <div class="footer">
    <p>Generated automatically by <strong>daily-job-internship-alerts</strong></p>
    <p>Monitoring {total_sources}+ sources across Greenhouse, Lever, Ashby &amp; public job boards</p>
    <p style="margin-top:10px;">Custom sources configurable in <code>custom_sources.json</code></p>
  </div>

</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Email Sender
# ---------------------------------------------------------------------------

def send_email(html_body: str, jobs: list[dict], internships: list[dict]) -> None:
    """Send the HTML digest via Gmail SMTP (TLS on port 587)."""
    if not EMAIL_FROM or not EMAIL_PASSWORD or not EMAIL_TO or "your_gmail" in EMAIL_FROM or "xxxx" in EMAIL_PASSWORD:
        log.warning("EMAIL_FROM or EMAIL_PASSWORD is not configured (or contains placeholder values). Skipping email delivery.")
        log.info("Tip: Set real credentials in .env or GitHub Secrets to receive email alerts.")
        return False

    today = datetime.date.today().strftime("%B %d, %Y")
    total = len(jobs) + len(internships)
    subject = f"🚀 {total} New Opportunities — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = ", ".join(EMAIL_TO)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        log.info("Connecting to Gmail SMTP …")
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        log.info("✅ Email successfully sent to: %s", ", ".join(EMAIL_TO))
        return True
    except smtplib.SMTPAuthenticationError:
        log.error("❌ Gmail authentication failed: Check that your EMAIL_FROM is correct and EMAIL_PASSWORD is a valid 16-character Google App Password.")
        return False
    except Exception as exc:
        log.error("❌ Could not send email via Gmail SMTP: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("=" * 65)
    log.info("daily-job-internship-alerts — automated run starting")
    log.info("=" * 65)

    if KEYWORDS:
        log.info("Keyword filter active: %s", ", ".join(KEYWORDS))
    else:
        log.info("No keyword filter active — checking all listings")

    jobs, internships, total_sources = fetch_all()

    if not jobs and not internships:
        log.info("No new listings found in this cycle. Skipping email send.")
        return

    html = build_html_email(jobs, internships, total_sources)
    success = send_email(html, jobs, internships)
    if success:
        log.info("Run finished successfully with email delivered! 🎉")
    else:
        log.info("Run finished! (Fetched %d jobs, %d internships across %d sources) 🎉", len(jobs), len(internships), total_sources)


if __name__ == "__main__":
    main()
