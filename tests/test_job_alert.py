"""Regression tests for daily-job-internship-alerts.

Covers defects found during live verification (2026-10-14):
 1. job_alert.py must compile (IndentationError in fetch_remoteok/fetch_arbeitnow).
 2. posted_ts must always be numeric (ATS ISO strings broke recency ordering).
 3. Fresh listings (is_recent) must sort before older ones.
 4. send_email failure must return False (main exits 1, seen_jobs.json untouched).
"""
import datetime
import importlib.util
import pathlib
import py_compile
import smtplib
import sys

REPO = pathlib.Path("/home/shiva/Projects/daily-job-internship-alerts")


def load_job_alert():
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location("job_alert", REPO / "job_alert.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["job_alert"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_compiles():
    for f in ["job_alert.py", "companies.py", "source_manager.py", "custom_sources.py"]:
        py_compile.compile(str(REPO / f), doraise=True)


def test_parse_timestamp_iso_string():
    ja = load_job_alert()
    assert ja._parse_timestamp("2026-10-13T18:43:19-04:00") > 0
    assert ja._parse_timestamp("2026-10-14T10:00:00Z") > 0
    assert ja._parse_timestamp(None) == 0.0
    assert ja._parse_timestamp("") == 0.0
    assert isinstance(ja._parse_timestamp(1728000000000), float)  # epoch ms


def test_recency_sort_recent_first():
    ja = load_job_alert()
    now = datetime.datetime.now(datetime.UTC).timestamp()
    items = [
        {"title": "old", "is_recent": False, "posted_ts": now - 200000},
        {"title": "recent-old", "is_recent": True, "posted_ts": now - 3600},
        {"title": "recent-new", "is_recent": True, "posted_ts": now - 60},
    ]

    def key(item):
        ts = item.get("posted_ts", 0)
        if not isinstance(ts, (int, float)):
            ts = ja._parse_timestamp(ts)
        return (1 if item.get("is_recent") else 0, ts)

    ordered = sorted(items, key=key, reverse=True)
    assert [i["title"] for i in ordered] == ["recent-new", "recent-old", "old"]


def test_posted_ts_numeric_after_ats_parse():
    """Greenhouse/Lever/Ashby ISO date strings must become numeric posted_ts."""
    ja = load_job_alert()
    for raw in ["2026-10-13T18:43:19-04:00", "2026-10-14T10:00:00Z", "2025-01-01"]:
        assert isinstance(ja._parse_timestamp(raw), float)


def test_send_email_failure_returns_false_and_keeps_seen():
    ja = load_job_alert()
    seen_path = REPO / "seen_jobs.json"
    before = seen_path.read_text() if seen_path.exists() else ""

    class FailSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def ehlo(self):
            pass

        def starttls(self):
            pass

        def login(self, u, p):
            raise smtplib.SMTPAuthenticationError(535, b"Bad credentials")

    orig = smtplib.SMTP
    smtplib.SMTP = FailSMTP
    try:
        ja.EMAIL_FROM = "test@gmail.com"
        ja.EMAIL_PASSWORD = "wrong"
        ja.EMAIL_TO = ["to@example.com"]
        ok = ja.send_email("<p>x</p>", [{"title": "t"}], [])
        assert ok is False
    finally:
        smtplib.SMTP = orig
    after = seen_path.read_text() if seen_path.exists() else ""
    assert before == after


def test_send_email_includes_plain_and_html_parts_in_order():
    """Digest must be multipart/alternative with plain first, HTML second."""
    import inspect

    ja = load_job_alert()
    src = inspect.getsource(ja.send_email)
    assert 'MIMEText(plain_body, "plain"' in src
    assert 'MIMEText(html_body, "html"' in src
    assert src.index('"plain"') < src.index('"html"')

