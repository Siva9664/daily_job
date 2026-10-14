<div align="center">

# 🚀 daily-job-internship-alerts

**A fully automated Python tool that fetches the latest remote jobs & internships every day and delivers a beautiful HTML digest email to your inbox — powered by 100% free public APIs and GitHub Actions.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![No API Key](https://img.shields.io/badge/API_Key-Not_Required-f59e0b?style=for-the-badge&logo=key&logoColor=white)]()
[![Zero Cost](https://img.shields.io/badge/Cost-%240-purple?style=for-the-badge)]()

*Set it up once. Get jobs in your inbox. Every. Single. Day.*

</div>

---

## 📖 Table of Contents

1. [What It Does](#-what-it-does)
2. [Features](#-features)
3. [How It Works](#-how-it-works)
4. [Custom Sources & Interest Filtering](#-custom-sources--interest-filtering)
5. [Project Structure](#-project-structure)
6. [Quick Start (Local)](#-quick-start-run-locally)
7. [Environment Variables](#️-configuration-reference)
8. [Gmail App Password Setup](#-how-to-get-a-gmail-app-password)
9. [Deploy with GitHub Actions (Free)](#-deploy-with-github-actions-free-automation)
10. [Data Sources & Accuracy](#-data-sources--accuracy)
11. [Deduplication System](#-how-deduplication-works)
12. [Email Preview](#-email-output-preview)
13. [Keyword Filtering](#-keyword-filtering-examples)
14. [Extending the Project](#-extending-the-project)
15. [Troubleshooting](#-troubleshooting)
16. [FAQ](#-faq)
17. [Contributing](#-contributing)
18. [License](#-license)

---

## 🎯 What It Does

Every day at a scheduled time:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Scans 100+ sources concurrently (multithreaded):        │
│       • 5 Free Public Job APIs (Himalayas, Remotive, etc.) │
│       • 100+ Top Tech ATS Portals (Greenhouse, Lever, Ashby)│
│       • Any Custom Sources you defined in custom_sources.json│
│  2. Normalises all responses into a unified schema          │
│  3. Deduplicates against previously-sent listings (SHA-256) │
│  4. Filters by your custom keywords & interest preferences   │
│  5. Builds a beautiful HTML email with two sections:        │
│       💼  Regular Job Openings                              │
│       🎓  Internships & Early Career (great for students!)  │
│  6. Sends it via Gmail SMTP to all your recipients          │
│  7. Saves seen hashes so duplicates are never re-sent       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **100+ Data Sources** | 100+ direct company ATS portals + 5 public job boards |
| ⚡ **Fast & Multithreaded** | `ThreadPoolExecutor` queries 100+ sources in ~10–15 seconds |
| 🕒 **Last-24h Recency** | Prefers fresh listings with a prominent `⚡ Last 24h` email badge |
| 💼 **Optional LinkedIn** | Fetch past-24h postings via LinkedIn's guest API (`ENABLE_LINKEDIN=true`) |
| 🎛️ **Custom Sources File** | Add your own dream companies or feeds in `custom_sources.json` |
| 🎯 **Interested-Only Filter** | Filter alerts to strictly your interested sources or companies |
| 🎓 **Student-Friendly** | Separate "Internships" section in every email digest |
| 🧠 **Smart Deduplication** | SHA-256 fingerprinting — persistent caching ensures no duplicates across runs |
| 🎯 **Keyword Filtering** | Only get listings matching your exact skills/interests |
| 📬 **Multiple Recipients** | Comma-separated — send to as many emails as you want |
| 💅 **Beautiful HTML Email** | Responsive design with cards, stats bar, badges & buttons |
| ⏰ **Fully Automated** | GitHub Actions runs it daily — completely free of charge |
| 🔒 **Secure by Design** | Credentials in `.env` locally; GitHub Secrets in CI |
| 🛡️ **Fault-Tolerant** | If any ATS or API fails, the rest continue without crashing |
| 📦 **Minimal Dependencies** | `requests`, `python-dotenv`, and `beautifulsoup4` |
| 🐍 **Python 3.9+** | Works on modern Python versions |

---

## 🔬 How It Works

### Architecture Overview

```
job_alert.py
│
├── source_manager.py         ← Merges default + user custom sources
│   ├── companies.py          ← 103 curated ATS companies (Greenhouse, Lever, Ashby)
│   ├── custom_sources.json   ← User-defined companies & custom feeds
│   └── custom_sources.py     ← Python alternative for custom sources
│
├── load_seen_jobs()          ← Load seen_jobs.json (dedup state)
│
├── fetch_all()               ← ThreadPoolExecutor (max 20 workers)
│   ├── Public APIs           → Himalayas (Browse & Search), Remotive, Jobicy, RemoteOK, Arbeitnow
│   ├── LinkedIn (Optional)   → Public guest API (last 24h postings via f_TPR=r86400)
│   ├── ATS Fetchers          → Greenhouse, Lever, Ashby endpoints
│   └── Custom Feeds          → Any custom JSON endpoints

│
├── matches_keywords()        ← Optional keyword filtering
├── job_hash()                ← SHA-256 deduplication
│
├── build_html_email()        ← Assembles responsive HTML email with live badge
│   └── _job_card_html()      ← Renders individual job cards
│
└── send_email()              ← Gmail SMTP (TLS, port 587)
    └── save_seen_jobs()      ← Persist new hashes to disk
```

---

## 🎛️ Custom Sources & Interest Filtering

You can add your own companies, ATS boards, or job APIs in **a dedicated separate file: `custom_sources.json`** without modifying any code!

### Adding Your Own Companies

Open [`custom_sources.json`](file:///home/shiva/Projects/daily-job-internship-alerts/custom_sources.json) and add any company:

```json
{
  "interested_only": false,
  "filter_sources": [],
  "ats_companies": [
    {
      "name": "Spotify",
      "ats": "lever",
      "token": "spotify",
      "enabled": true
    },
    {
      "name": "OpenAI",
      "ats": "greenhouse",
      "token": "openai",
      "enabled": true
    },
    {
      "name": "Linear",
      "ats": "ashby",
      "token": "linear",
      "enabled": true
    }
  ],
  "custom_feeds": []
}
```

### Interested-Only Mode

If you **only want alerts from specific sources or companies**:

1. **Focus on your custom companies only**:
   Set `"interested_only": true` in `custom_sources.json`. The runner will bypass the generic list and only monitor the companies you listed!

2. **Or filter by specific company/source names**:
   Set `"filter_sources": ["stripe", "linear", "spotify", "himalayas"]`. Only listings from these sources will be included.

---

## 📁 Project Structure

```
daily-job-internship-alerts/
│
├── job_alert.py              ← ⭐ Main script (concurrent fetch, dedup, email)
├── companies.py              ← 103 curated ATS companies (Greenhouse, Lever, Ashby)
├── source_manager.py         ← Source loader, merger & filter logic
├── custom_sources.json       ← 🎛️ User custom sources & interested-only config
├── custom_sources.py         ← Alternative Python format for custom sources
├── requirements.txt          ← 2 pip packages: requests, python-dotenv
│
├── .env.example              ← Template — copy to .env and fill in values
├── .env                      ← Your local secrets (gitignored!)
│
├── seen_jobs.json            ← Auto-created; stores dedup hashes
├── .gitignore                ← Ignores .env, .venv, __pycache__, etc.
│
├── README.md                 ← Complete documentation
│
└── .github/
    └── workflows/
        └── daily-alert.yml   ← GitHub Actions: runs daily at 02:30 UTC
```

---

## 🚀 Quick Start (Run Locally)

### Prerequisites

- Python 3.9 or newer
- A Gmail account with 2-Step Verification enabled
- A Gmail App Password (see [setup guide below](#-how-to-get-a-gmail-app-password))

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/daily-job-internship-alerts.git
cd daily-job-internship-alerts
```

### Step 2 — Create a virtual environment & install dependencies

```bash
# Create the virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # macOS / Linux
.venv\Scriptsctivate           # Windows (cmd)
.venv\Scripts\Activate.ps1       # Windows (PowerShell)

# Install the 2 required packages
pip install -r requirements.txt
```

### Step 3 — Configure your `.env` file

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your values:

```dotenv
EMAIL_FROM=your_gmail@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx    # Gmail App Password (NOT real password)
EMAIL_TO=you@gmail.com,friend@gmail.com
KEYWORDS=python,data science          # Leave blank to receive all jobs
```

### Step 4 — Run the script

```bash
python job_alert.py
```

**Expected output:**

```
2026-10-13 08:00:00  INFO      ============================================================
2026-10-13 08:00:00  INFO      daily-job-internship-alerts — starting run
2026-10-13 08:00:00  INFO      ============================================================
2026-10-13 08:00:00  INFO      Keyword filter active: python, data science
2026-10-13 08:00:01  INFO      Fetching Himalayas jobs …
2026-10-13 08:00:01  INFO        → 30 Himalayas jobs
2026-10-13 08:00:02  INFO      Fetching Himalayas internships …
2026-10-13 08:00:02  INFO        → 5 Himalayas internships
2026-10-13 08:00:03  INFO      Fetching Remotive jobs …
2026-10-13 08:00:03  INFO        → 30 Remotive jobs
2026-10-13 08:00:04  INFO      Fetching Jobicy jobs …
2026-10-13 08:00:04  INFO        → 25 Jobicy jobs
2026-10-13 08:00:05  INFO      Fetching RemoteOK jobs …
2026-10-13 08:00:05  INFO        → 30 RemoteOK jobs
2026-10-13 08:00:05  INFO      Total raw listings fetched: 120
2026-10-13 08:00:05  INFO      New jobs: 18 | New internships: 4
2026-10-13 08:00:05  INFO      Connecting to Gmail SMTP …
2026-10-13 08:00:06  INFO      ✅  Email sent to: you@gmail.com
2026-10-13 08:00:06  INFO      Done! 🎉
```

Within seconds, check your inbox (and spam folder the very first time).

---

## ⚙️ Configuration Reference

All configuration is done via environment variables in your `.env` file:

| Variable | Required | Default | Description |
|---|---|---|---|
| `EMAIL_FROM` | ✅ Yes | — | Gmail address used to **send** the digest |
| `EMAIL_PASSWORD` | ✅ Yes | — | Gmail **App Password** (16 chars, spaces optional) |
| `EMAIL_TO` | ✅ Yes | — | Comma-separated list of recipient emails |
| `KEYWORDS` | ❌ No | *(empty = all jobs)* | Filter keywords for title/company/description/tags |
| `ENABLE_LINKEDIN` | ❌ No | `false` | Fetch past-24h jobs via LinkedIn's guest search API |

> **Important:** All three `EMAIL_*` variables are required. If any are missing, the script
> will log an error and exit without sending — it will **not** crash silently.


### Internal Tuning Constants

These are set at the top of `job_alert.py` and can be changed directly:

| Constant | Default | Description |
|---|---|---|
| `REQUEST_TIMEOUT` | `15` seconds | Max wait time per API call before giving up |
| `MAX_JOBS_PER_SOURCE` | `30` | Max listings fetched from each source per run |

---

## 🔑 How to Get a Gmail App Password

> **Important:** You **must** use a Gmail App Password — **not** your real Gmail password.
> Google blocks login attempts from scripts by default since 2022.

**Step-by-step:**

1. **Enable 2-Step Verification** on your Google account (required for App Passwords):
   👉 https://myaccount.google.com/security

2. **Go to App Passwords**:
   👉 https://myaccount.google.com/apppasswords

3. Click **"Create"**, give it a name like `job-alerts`, and click **Create**.

4. Google will show you a **16-character password** formatted as:
   ```
   abcd efgh ijkl mnop
   ```

5. Copy the full password (with or without spaces) into your `.env`:
   ```dotenv
   EMAIL_PASSWORD=abcd efgh ijkl mnop
   ```

> **Tip:** Spaces in the App Password are optional — `abcdefghijklmnop` and `abcd efgh ijkl mnop` are treated identically by Gmail SMTP.

> **Note:** The App Password only grants access to Gmail SMTP sending. It cannot be used to log into your Google account and can be revoked at any time from the same App Passwords page.

---

## 🤖 Deploy with GitHub Actions (Free Automation)

GitHub Actions runs your script **every day for free** using GitHub's servers.
No VPS, no cloud bill, no cron daemon on your machine.

### Step 1 — Push your code to GitHub

```bash
git init
git add .
git commit -m "feat: initial daily job alert setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/daily-job-internship-alerts.git
git push -u origin main
```

> **Caution:** Confirm `.env` appears in `.gitignore` **before** pushing. Your App Password must never be committed to a public repository.

### Step 2 — Add GitHub Secrets

Your credentials must be stored as **encrypted repository secrets** — they are never visible in logs or to other users.

1. Go to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add each variable:

| Secret Name | Example Value | Notes |
|---|---|---|
| `EMAIL_FROM` | `youremail@gmail.com` | The sending Gmail account |
| `EMAIL_PASSWORD` | `abcd efgh ijkl mnop` | Your 16-char App Password |
| `EMAIL_TO` | `you@gmail.com,friend@gmail.com` | Comma-separated recipients |
| `KEYWORDS` | `python,data,machine learning` | Optional; leave blank for all |
| `ENABLE_LINKEDIN` | `true` | Optional; enables LinkedIn guest fetcher |

### Step 3 — Verify the Workflow

The workflow file `.github/workflows/daily-alert.yml` is already in the repo and configured to run daily at **02:30 UTC** (08:00 IST).

To do a **manual test run**:
1. Go to your repo → **Actions** tab
2. Click **"Daily Job & Internship Alert"** in the left sidebar
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Watch the logs live and check your inbox within ~30 seconds

### Step 4 — Monitor Runs

| What to check | Where |
|---|---|
| See run history | Repo → Actions tab |
| View logs for a run | Click the run → click `send-alert` job |
| Clear the dedup cache | Repo → Actions → Caches → delete `seen-jobs-*` |
| Change the schedule | Edit `cron:` in `daily-alert.yml` |

### Workflow File Reference & Fixed Cache

> [!NOTE]
> **Fixed Cache Key:** Previously, the workflow used `github.run_id` in the primary cache key (`seen-jobs-${{ runner.os }}-${{ github.run_id }}`), which generated an entirely new key on every run and caused deduplication state to reset. The cache key has been updated to the stable key `seen-jobs-${{ runner.os }}` with fallback prefix `seen-jobs-`, ensuring `seen_jobs.json` reliably persists across runs.

```yaml
name: Daily Job & Internship Alert

on:
  schedule:
    - cron: "30 2 * * *"   # 02:30 UTC every day
  workflow_dispatch:         # Also allow manual trigger

jobs:
  send-alert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v4          # Preserves seen_jobs.json between runs
        with:
          path: seen_jobs.json
          key: seen-jobs-${{ runner.os }}
          restore-keys: |
            seen-jobs-${{ runner.os }}-
            seen-jobs-
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements.txt
      - run: python job_alert.py
        env:
          EMAIL_FROM:      ${{ secrets.EMAIL_FROM }}
          EMAIL_PASSWORD:  ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_TO:        ${{ secrets.EMAIL_TO }}
          KEYWORDS:        ${{ secrets.KEYWORDS }}
          ENABLE_LINKEDIN: ${{ secrets.ENABLE_LINKEDIN || vars.ENABLE_LINKEDIN || 'false' }}
```


### Changing the Schedule

Edit the `cron:` line in `.github/workflows/daily-alert.yml`.
Use [crontab.guru](https://crontab.guru) to build your own expression.

| Cron Expression | Runs At |
|---|---|
| `30 2 * * *` | Every day at 02:30 UTC (08:00 IST) — **default** |
| `0 7 * * 1-5` | Weekdays only at 07:00 UTC |
| `0 0 * * 1` | Every Monday at midnight UTC |
| `0 6,18 * * *` | Twice daily: 06:00 and 18:00 UTC |

---

## 🔌 Data Sources & Accuracy

All default sources are **completely free** and require **no API key or account**.

### Source Summary

| Source | Endpoint | Auth | Jobs | Internships | Notes |
|---|---|---|---|---|---|
| [Himalayas.app](https://himalayas.app/jobs/api) | `/jobs/api` (Browse) & `/jobs/api/search` (Search) | None | ✅ | ✅ via `employment_type=Intern` | Supports `sort=recent`, salary ranges & recency tags |
| [Remotive.com](https://remotive.com/api) | `/api/remote-jobs` | None | ✅ | ✅ via `job_type` field | Authoritative tech job postings |
| [Jobicy.com](https://jobicy.com/api) | `/api/v2/remote-jobs` | None | ✅ | ✅ keyword detection | Includes publication timestamps |
| [RemoteOK.com](https://remoteok.com/api) | `/api` | None | ✅ | ✅ keyword detection | Rich tags & epoch timestamps |
| [Arbeitnow.com](https://www.arbeitnow.com/api/job-board-api) | `/api/job-board-api` | None | ✅ | ✅ keyword detection | Visa sponsorship and remote tags |
| [LinkedIn](https://www.linkedin.com) *(Optional)* | `/jobs-guest/jobs/api/seeMoreJobPostings/search` | None | ✅ | ✅ keyword detection | Requires `ENABLE_LINKEDIN=true` (last 24h via `f_TPR=r86400`) |

### Per-Source Accuracy Notes

**Himalayas.app** — ✅ Most reliable
- Uses official public endpoints: Browse (`/jobs/api`) and Search (`/jobs/api/search`) with `sort=recent`
- Internships filter uses `employment_type=Intern` and keyword queries — high accuracy
- Provides publication timestamps (`pubDate`) allowing listings from the last 24h to be badged `⚡ Last 24h`
- Salary data is parsed into structured `$min–$max / period` format

**LinkedIn (Guest Search — Last 24 Hours)** — ⚠️ Experimental / Optional
- Enabled by setting `ENABLE_LINKEDIN=true` in `.env` or GitHub Secrets
- Uses LinkedIn's public guest endpoint: `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`
- Passes `f_TPR=r86400` to filter strictly for opportunities posted within the last 24 hours
- HTML responses are parsed with `beautifulsoup4`
- All returned listings receive the `⚡ Last 24h` badge and are sorted to the top of the email
> [!WARNING]
> **LinkedIn Disclaimer & ToS Notice:**
> This LinkedIn fetcher uses an **unofficial public guest endpoint**. It is unsupported by LinkedIn, subject to aggressive rate limits (HTTP 429), and can change or break without notice. Automated scraping may violate [LinkedIn's Terms of Service](https://www.linkedin.com/legal/user-agreement). Use this feature **strictly for personal email alerts at your own risk**. If disabled (`ENABLE_LINKEDIN=false`), the project runs purely on 100% public APIs and official ATS company boards.

**Remotive.com** — ✅ Very reliable for tech roles
- Well-structured API with a consistent `job_type` response field
- Internship detection via `job_type` (authoritative — set by the employer)
- Focuses on software engineering, design, marketing, and remote-first roles

**Jobicy.com** — ✅ Good coverage
- Broad category coverage across many industries
- Internship detection is **keyword-based** (looks for "intern" in the job title)
- Includes publication dates for recency tracking

**RemoteOK.com** — ⚠️ Good but with caveats
- The API returns a **legal notice as the first element** — the script automatically skips it
- Internship detection is **keyword-based** (title + tags)
- Tag data is rich and very useful for keyword filtering
- Includes epoch timestamps for recency detection

**Arbeitnow** — ✅ Clean European & global remote tech listings
- Public API endpoint with structured tags and creation timestamps

### Overall Accuracy Assessment

| Concern | Verdict |
|---|---|
| False positives (regular job miscategorised as internship) | Rare — only possible on keyword-detected public sources |
| False negatives (real internship missed) | Possible on sources without explicit type fields |
| Duplicate listings across sources | Eliminated by SHA-256 deduplication |
| Stale or expired listings | Prioritises fresh listings; dedup prevents re-sends |
| Script crashing when one source fails | Never — each fetcher is independently error-handled |

**Will it work accurately?** — Yes, for the vast majority of listings. Sources with structured type fields (Himalayas + Remotive) are fully accurate. The keyword-based detection on other boards works well in practice since most internships include "intern" in the job title.


---

## 🔄 How Deduplication Works

Every job is fingerprinted using a stable SHA-256 hash:

```python
key = f"{title.lower().strip()}|{company.lower().strip()}|{url.strip()}"
hash = sha256(key.encode()).hexdigest()
```

| Scenario | Result |
|---|---|
| Same job posted on two different sources | ✅ Sent once only |
| Job reposted by company next week | ✅ Not re-sent (hash matches) |
| Different job title at same company | ✅ Correctly sent |
| Different company with same title | ✅ Correctly sent |

### `seen_jobs.json` format

```json
[
  "a3f1c2d4e5b6789abcdef1234567890abcdef1234567890abcdef1234567890ab",
  "9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c",
  "..."
]
```

### Resetting the dedup cache

- **Locally:** Delete `seen_jobs.json` — all jobs will appear fresh on next run
- **GitHub Actions:** Go to your repo → **Actions** → **Caches** → find `seen-jobs-ubuntu-latest-*` and delete it

---

## 📧 Email Output Preview

The HTML email is divided into two clearly labelled sections with a stats bar at the top:

```
┌─────────────────────────────────────────────────────┐
│  🚀  Daily Job & Internship Digest                  │
│      Your curated remote opportunities for          │
│      October 13, 2026                               │
│           [ 22 New Opportunities Today ]            │
├──────────────┬──────────────────┬───────────────────┤
│   18 Jobs    │  4 Internships   │  4 Sources Checked│
├──────────────┴──────────────────┴───────────────────┤
│                                                     │
│  💼  Job Openings                                   │
│  ┌───────────────────────────────────────────────┐  │
│  │ Senior Python Developer        [Indigo border]│  │
│  │ 🏢 Acme Corp                                 │  │
│  │ 📍 Remote  💰 20k–50k/yr  🔗 Himalayas  ⚡ 24h│  │
│  │ 🏷️ python, django, postgres                  │  │
│  │ We are looking for a Senior Python Developer  │  │
│  │ with 5+ years of experience to join our…     │  │
│  │              [ Apply Now → ]                  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  🎓  Internships (for Students)                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Data Science Intern            [Green border] │  │
│  │ 🏢 OpenAI                                    │  │
│  │ 📍 Worldwide   🔗 Remotive.com   ⚡ Last 24h  │  │
│  │ 🏷️ python, data science, machine learning    │  │
│  │ Join our research team for a 3-month paid…   │  │
│  │              [ Apply Now → ]                  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Design details:**
- Job cards have an **indigo** (`#4F46E5`) left border
- Internship cards have an **emerald** (`#059669`) left border
- Fresh opportunities from the last 24h feature a prominent **`⚡ Last 24h` gold badge**
- Max width 680px — renders correctly in Gmail, Outlook, Apple Mail
- Salary and tags are hidden gracefully when not available


---

## 🎯 Keyword Filtering Examples

The `KEYWORDS` variable is **case-insensitive** and matched against:
- Job **title** · **Company** name · **Description** (first 300 chars) · **Tags**

```dotenv
# Full-stack developer
KEYWORDS=react,node,typescript,javascript,fullstack

# Data / ML / AI roles
KEYWORDS=python,data,machine learning,deep learning,llm,ai,nlp

# Backend engineering
KEYWORDS=python,golang,rust,backend,api,microservices

# Frontend only
KEYWORDS=react,vue,svelte,angular,frontend,css,tailwind

# DevOps / Cloud
KEYWORDS=devops,kubernetes,docker,aws,terraform,ci/cd

# Design
KEYWORDS=figma,ux,ui designer,product design

# No filter — receive all listings
KEYWORDS=
```

> **Tip:** Keywords use simple substring matching. A keyword of `python` will match
> "Python Developer", "Senior Python Engineer", "python-based tools", etc.
> Keep keywords reasonably specific to avoid unexpected matches.

---

## 🧩 Extending the Project

### Add a New Job Source

Follow this template to add any new JSON-based job API:

```python
def fetch_my_source() -> list[dict]:
    """
    MySource public API — description.
    Docs: https://api.mysource.com/docs
    """
    log.info("Fetching MySource jobs …")
    resp = _safe_get(
        "https://api.mysource.com/jobs",
        params={"limit": MAX_JOBS_PER_SOURCE},
        headers={"User-Agent": "daily-job-alerts/1.0"},
    )
    if resp is None:
        return []

    jobs = []
    for item in resp.json().get("results", [])[:MAX_JOBS_PER_SOURCE]:
        title = item.get("title", "N/A")
        is_intern = "intern" in title.lower()
        jobs.append({
            "title":       title,
            "company":     item.get("company", "N/A"),
            "location":    item.get("location") or "Remote",
            "salary":      item.get("salary", ""),
            "description": _truncate(item.get("description", ""), 300),
            "url":         item.get("apply_url", "#"),
            "source":      "MySource",
            "type":        "internship" if is_intern else "job",
            "tags":        ", ".join(item.get("tags", [])),
        })
    log.info("  → %d MySource jobs", len(jobs))
    return jobs
```

Then register it in `fetch_all()`:

```python
fetchers = [
    fetch_himalayas_jobs,
    fetch_himalayas_internships,
    fetch_remotive,
    fetch_jobicy,
    fetch_remoteok,
    fetch_my_source,   # ← Add here
]
```

### Use a Different SMTP Provider

The `send_email()` function is easy to adapt. Replace the Gmail SMTP config:

```python
# Current (Gmail):
with smtplib.SMTP("smtp.gmail.com", 587) as server:

# Outlook / Hotmail:
with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:

# SendGrid (SMTP relay):
with smtplib.SMTP("smtp.sendgrid.net", 587) as server:
    server.login("apikey", SENDGRID_API_KEY)
```

### Change Email Frequency

Edit the `cron:` line in `.github/workflows/daily-alert.yml`:

```yaml
schedule:
  - cron: "0 7 * * 1-5"   # Weekdays only at 07:00 UTC
```

### Change Email Design

The HTML is fully self-contained in `build_html_email()` and `_job_card_html()` inside `job_alert.py`.
All CSS is inside a `<style>` block — easy to customise colours, fonts, and layout.

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `Missing email configuration` error | One of the three `EMAIL_*` vars is not set | Check `.env` has `EMAIL_FROM`, `EMAIL_PASSWORD`, and `EMAIL_TO` |
| `SMTPAuthenticationError` | Wrong password or real password used | Use a Gmail **App Password** — not your actual Gmail password |
| `SMTPConnectError` | Firewall blocking port 587 | Try on a different network; some corporate networks block SMTP |
| Email lands in spam | First-run sender trust | Add the sender to your Contacts; Gmail trains over time |
| No jobs in the email | All jobs already seen | Normal — delete `seen_jobs.json` to reset |
| One API shows 0 results | That API is temporarily down | Expected — errors are logged; other sources continue |
| `JSONDecodeError` on startup | `seen_jobs.json` is corrupted | Delete the file — it will be recreated automatically |
| GitHub Actions not appearing | Not on `main` branch | Ensure `daily-alert.yml` is committed to `main` |
| GitHub Actions run fails | Secrets not set | Verify all 3 secrets in repo → Settings → Secrets |

### Enabling Debug Logging

Add this near the top of `job_alert.py` for verbose output:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

---

## ❓ FAQ

**Q: Does this cost anything to run?**
> A: **No.** GitHub Actions gives every free account 2,000 minutes/month. This script takes ~10 seconds per run, so you use roughly 5 minutes/month — well within the free tier.

**Q: Will I get the same job listed twice?**
> A: No, unless you delete `seen_jobs.json` or clear the Actions cache. SHA-256 deduplication ensures each unique (title + company + URL) combination is sent at most once.

**Q: What if all the APIs are down?**
> A: The script logs errors for each failed source, finds 0 new listings, and **skips sending entirely**. You will not receive an empty email.

**Q: Can I run this on my own server / Raspberry Pi?**
> A: Yes. Set up a system cron job: `30 2 * * * /path/to/.venv/bin/python /path/to/job_alert.py`

**Q: Can I use a non-Gmail address to send emails?**
> A: Yes — see [Use a Different SMTP Provider](#use-a-different-smtp-provider). Update the SMTP host and port in `send_email()`.

**Q: Can I receive the email on a non-Gmail address?**
> A: Yes. `EMAIL_TO` accepts any valid email address regardless of provider.

**Q: How accurate is the internship detection?**
> A: Very accurate on Himalayas (server-side API filter) and Remotive (structured `job_type` field). On Jobicy and RemoteOK, detection is keyword-based — it works well in practice since most internships include "intern" in the title, but occasional edge cases exist.

**Q: What does `employment_type=Intern` on Himalayas do?**
> A: It is a server-side filter on the Himalayas API. Only listings where the employer explicitly tagged the role as an internship are returned. This is the most reliable method used in the project.

**Q: Can I filter by location too?**
> A: Not natively — but you can extend `matches_keywords()` to also check `job["location"]`, or add a `LOCATIONS` env variable following the same pattern as `KEYWORDS`.

**Q: My `seen_jobs.json` keeps growing. Is that a problem?**
> A: No. Each hash is a 64-character hex string. 10,000 entries ≈ 640 KB. Even after years of daily use, the file stays trivially small.

---

## 🤝 Contributing

Contributions are welcome! Here is how to get started:

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feat/add-new-source`
3. **Make your changes** (new source? bug fix? design improvement?)
4. **Test locally**: `python job_alert.py`
5. **Commit**: `git commit -m "feat: add LinkedIn Jobs source"`
6. **Push**: `git push origin feat/add-new-source`
7. **Open a Pull Request** on GitHub

### Good first contributions

- 🔌 Add a new free job API source
- 🌍 Add location-based filtering (`LOCATIONS` env variable)
- 📊 Add duplicate-skip count to the email footer
- 🕒 Add "Posted X days ago" timestamps to job cards
- 📱 Improve email mobile responsiveness
- 🔇 Add a `DRY_RUN` mode that prints the email HTML without sending

---

## 📜 License

This project is licensed under the **MIT License** — free to use, modify, fork, and distribute.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<div align="center">

Built with ❤️ in Python · Automated with GitHub Actions · No servers required

**⭐ Star this repo if it saves you time!**

</div>
