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

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **4 Free Data Sources** | Himalayas.app, Remotive.com, Jobicy.com, RemoteOK.com |
| 🎓 **Student-Friendly** | Separate "Internships" section in every email |
| 🧠 **Smart Deduplication** | `seen_jobs.json` ensures no opportunity is sent twice |
| 🎯 **Keyword Filtering** | Only get listings relevant to your skills |
| 📬 **Multiple Recipients** | Send to any number of email addresses |
| 💅 **Beautiful HTML Email** | Responsive, modern design with cards, badges & buttons |
| ⏰ **Fully Automated** | GitHub Actions runs it daily — completely free |
| 🔒 **Secure** | Credentials stay in `.env` locally and GitHub Secrets in CI |

---

## 📁 Project Structure

```
daily-job-internship-alerts/
├── .env.example              ← Template for your environment variables
├── .gitignore                ← Keeps .env and secrets out of git
├── requirements.txt          ← Python dependencies (requests, python-dotenv)
├── job_alert.py              ← Main script (fetch → deduplicate → email)
├── seen_jobs.json            ← Auto-created; tracks jobs already sent
├── README.md
└── .github/
    └── workflows/
        └── daily-alert.yml   ← GitHub Actions: runs daily at 02:30 UTC
```

---

## 🚀 Quick Start (Run Locally)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/daily-job-internship-alerts.git
cd daily-job-internship-alerts
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up your `.env` file

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in your values:

```dotenv
EMAIL_FROM=your_gmail@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx    # Gmail App Password (see below)
EMAIL_TO=you@gmail.com,friend@gmail.com
KEYWORDS=python,data science          # Leave blank for all jobs
```

### 4. Run it!

```bash
python job_alert.py
```

You should receive an email within a few seconds. Check your inbox (and spam folder the first time).

---

## 🔑 How to Get a Gmail App Password

> [!IMPORTANT]
> You **must** use a Gmail App Password — not your real Gmail password.
> Google blocks "less secure" logins by default.

**Step-by-step:**

1. Go to your Google Account → **Security**:
   👉 https://myaccount.google.com/security

2. Enable **2-Step Verification** (required for App Passwords).

3. Search for **"App Passwords"** in the search bar at the top:
   👉 https://myaccount.google.com/apppasswords

4. Click **"Create"**, give it a name like `job-alerts`, and click **Create**.

5. Google will show you a **16-character password** like `xxxx xxxx xxxx xxxx`.

6. Copy it into your `.env` as `EMAIL_PASSWORD`.

> [!TIP]
> The spaces in the App Password are optional — both `abcdabcdabcdabcd` and `abcd abcd abcd abcd` work the same.

---

## ⚙️ Configuration Reference

All configuration is done via environment variables in your `.env` file:

| Variable | Required | Description |
|---|---|---|
| `EMAIL_FROM` | ✅ Yes | Gmail address used to **send** the email |
| `EMAIL_PASSWORD` | ✅ Yes | Gmail **App Password** (16 chars) |
| `EMAIL_TO` | ✅ Yes | Comma-separated list of recipient email addresses |
| `KEYWORDS` | ❌ No | Comma-separated keywords to filter jobs (leave blank for all) |

### Adding More Recipients

Simply add more addresses to `EMAIL_TO`, separated by commas:

```dotenv
EMAIL_TO=alice@gmail.com,bob@outlook.com,charlie@yahoo.com
```

### Changing Keywords

```dotenv
# Only show Python / data / AI jobs:
KEYWORDS=python,data,machine learning,AI,LLM

# Only frontend roles:
KEYWORDS=react,vue,frontend,javascript,typescript

# Remove all filters (receive everything):
KEYWORDS=
```

---

## 🤖 Deploy with GitHub Actions (Free Automation)

GitHub Actions runs your script **every day for free** on GitHub's servers.
No server, no cloud, no cost.

### Step 1: Push your code to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/daily-job-internship-alerts.git
git push -u origin main
```

> [!CAUTION]
> Make sure `.env` is in `.gitignore` (it already is) before pushing!
> Never commit your email credentials to GitHub.

### Step 2: Add GitHub Secrets

Your email credentials need to be added as **repository secrets** — they are encrypted and never visible in logs.

1. Go to your repository on GitHub.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **"New repository secret"** and add each of these:

| Secret Name | Value |
|---|---|
| `EMAIL_FROM` | `your_gmail@gmail.com` |
| `EMAIL_PASSWORD` | Your 16-char Gmail App Password |
| `EMAIL_TO` | `you@gmail.com,friend@gmail.com` |
| `KEYWORDS` | `python,data` *(optional, leave blank for all)* |

### Step 3: Enable the workflow

The workflow file at [`.github/workflows/daily-alert.yml`](.github/workflows/daily-alert.yml) is already configured to run daily at **02:30 UTC**.

To verify it's active:
1. Go to your repo → **Actions** tab.
2. You should see **"Daily Job & Internship Alert"** listed.
3. Click **"Run workflow"** to trigger a manual test run right now.

### Step 4: Check the run

After triggering manually or waiting for the scheduled run:
1. Click on the workflow run in the **Actions** tab.
2. Click on the **"send-alert"** job to see logs.
3. Check your inbox!

### Changing the Schedule

Edit `.github/workflows/daily-alert.yml`:

```yaml
schedule:
  - cron: "30 2 * * *"    # 02:30 UTC daily (default)
```

Use [crontab.guru](https://crontab.guru) to easily build your own cron expression.

Some examples:

| Cron | Schedule |
|---|---|
| `30 2 * * *` | Every day at 02:30 UTC (default) |
| `0 7 * * 1-5` | Weekdays only at 07:00 UTC |
| `0 0 * * 1` | Every Monday at midnight UTC |

---

## 🔌 Data Sources

All sources are **free** and require **no API key**:

| Source | Jobs | Internships | Notes |
|---|---|---|---|
| [Himalayas.app](https://himalayas.app) | ✅ | ✅ | `employment_type=Intern` filter |
| [Remotive.com](https://remotive.com) | ✅ | ✅ | Job type in response data |
| [Jobicy.com](https://jobicy.com) | ✅ | ✅ | Keyword-based detection |
| [RemoteOK.com](https://remoteok.com) | ✅ | ✅ | Keyword-based detection |

---

## 🔄 How Deduplication Works

Every job listing is fingerprinted with:
```
SHA-256(title + company + url)
```

All sent hashes are stored in `seen_jobs.json`. On each run, only listings with **new hashes** are included in the email.

**For GitHub Actions**: The workflow uses `actions/cache` to persist `seen_jobs.json` between runs, so you won't receive the same jobs twice across scheduled runs.

**To reset** (receive all listings fresh): Delete `seen_jobs.json` locally, or clear the Actions cache in your GitHub repo settings.

---

## 🧩 Extending the Project

### Add a New Job Source

1. Create a new fetch function following the existing pattern:

```python
def fetch_my_source() -> list[dict]:
    log.info("Fetching MySource jobs …")
    resp = _safe_get("https://api.mysource.com/jobs")
    if resp is None:
        return []
    jobs = []
    for item in resp.json().get("results", []):
        jobs.append({
            "title":       item.get("title", "N/A"),
            "company":     item.get("company", "N/A"),
            "location":    item.get("location") or "Remote",
            "salary":      item.get("salary", ""),
            "description": _truncate(item.get("description", ""), 300),
            "url":         item.get("apply_url", "#"),
            "source":      "MySource",
            "type":        "job",       # or "internship"
            "tags":        "",
        })
    return jobs
```

2. Add it to the `fetchers` list in `fetch_all()`.

### Change Email Design

The entire email HTML is generated in `build_html_email()` and `_job_card_html()` in `job_alert.py`. The CSS is inline-compatible and easy to customise.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `Missing email configuration` error | Check all three env vars are set in `.env` |
| Email lands in spam | Add sender to contacts; first-run is often flagged |
| `SMTPAuthenticationError` | Make sure you're using an App Password, not your real Gmail password |
| No jobs in email | Check if `seen_jobs.json` has all jobs cached; delete it to reset |
| GitHub Actions not running | Ensure the workflow file is on the `main` branch and secrets are set |
| One source fails | That's expected — errors are caught and logged; other sources still run |

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

<p align="center">Built with ❤️ in Python · Automated with GitHub Actions · No servers required</p>
# daily_job
