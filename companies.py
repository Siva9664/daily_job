"""
companies.py — Curated ATS company board list
==============================================
103 popular tech companies organised by their ATS (Applicant Tracking System).
Each entry drives a live API call to that company's public job board.

ATS endpoint templates:
  Greenhouse  https://boards-api.greenhouse.io/v1/boards/{token}/jobs
  Lever       https://api.lever.co/v0/postings/{token}?mode=json
  Ashby       https://api.ashbyhq.com/posting-api/job-board/{token}

Adding a company
  1. Find their public job board URL.
  2. Identify the ATS platform (Greenhouse / Lever / Ashby).
  3. Extract the board token (the slug in the URL).
  4. Append a dict: {"name": "...", "ats": "...", "token": "..."}.

Note: tokens that no longer resolve (company rebranded / switched ATS) are
      silently skipped — the request returns 0 results and logs nothing.
"""

COMPANIES: list[dict] = [

    # ══════════════════════════════════════════════════════════════════════════
    # GREENHOUSE  (60 companies)
    # Endpoint: https://boards-api.greenhouse.io/v1/boards/{token}/jobs
    # ══════════════════════════════════════════════════════════════════════════

    # ── Fintech / Payments ────────────────────────────────────────────────────
    {"name": "Stripe",          "ats": "greenhouse", "token": "stripe"},
    {"name": "Brex",            "ats": "greenhouse", "token": "brex"},
    {"name": "Plaid",           "ats": "greenhouse", "token": "plaid"},
    {"name": "Robinhood",       "ats": "greenhouse", "token": "robinhood"},
    {"name": "Chime",           "ats": "greenhouse", "token": "chime"},
    {"name": "Affirm",          "ats": "greenhouse", "token": "affirm"},
    {"name": "Coinbase",        "ats": "greenhouse", "token": "coinbase"},
    {"name": "Gusto",           "ats": "greenhouse", "token": "gusto"},
    {"name": "Klaviyo",         "ats": "greenhouse", "token": "klaviyo"},

    # ── SaaS / Productivity ───────────────────────────────────────────────────
    {"name": "Notion",          "ats": "greenhouse", "token": "notion"},
    {"name": "Asana",           "ats": "greenhouse", "token": "asana"},
    {"name": "Airtable",        "ats": "greenhouse", "token": "airtable"},
    {"name": "monday.com",      "ats": "greenhouse", "token": "mondaycom"},
    {"name": "Lattice",         "ats": "greenhouse", "token": "lattice"},
    {"name": "Front",           "ats": "greenhouse", "token": "front"},
    {"name": "Intercom",        "ats": "greenhouse", "token": "intercom"},
    {"name": "Mixpanel",        "ats": "greenhouse", "token": "mixpanel"},
    {"name": "Amplitude",       "ats": "greenhouse", "token": "amplitude"},
    {"name": "Pendo",           "ats": "greenhouse", "token": "pendo"},
    {"name": "SurveyMonkey",    "ats": "greenhouse", "token": "surveymonkey"},

    # ── Cloud / Infrastructure / DevTools ─────────────────────────────────────
    {"name": "Cloudflare",      "ats": "greenhouse", "token": "cloudflare"},
    {"name": "Datadog",         "ats": "greenhouse", "token": "datadoghq"},
    {"name": "HashiCorp",       "ats": "greenhouse", "token": "hashicorp"},
    {"name": "Sentry",          "ats": "greenhouse", "token": "sentry"},
    {"name": "Snowflake",       "ats": "greenhouse", "token": "snowflake"},
    {"name": "Databricks",      "ats": "greenhouse", "token": "databricks"},
    {"name": "MongoDB",         "ats": "greenhouse", "token": "mongodb"},
    {"name": "Okta",            "ats": "greenhouse", "token": "okta"},
    {"name": "PagerDuty",       "ats": "greenhouse", "token": "pagerduty"},
    {"name": "Twilio",          "ats": "greenhouse", "token": "twilio"},
    {"name": "GitLab",          "ats": "greenhouse", "token": "gitlab"},
    {"name": "Box",             "ats": "greenhouse", "token": "box"},
    {"name": "Outreach",        "ats": "greenhouse", "token": "outreach"},
    {"name": "Benchling",       "ats": "greenhouse", "token": "benchling"},

    # ── Consumer / Social ─────────────────────────────────────────────────────
    {"name": "Airbnb",          "ats": "greenhouse", "token": "airbnb"},
    {"name": "Lyft",            "ats": "greenhouse", "token": "lyft"},
    {"name": "DoorDash",        "ats": "greenhouse", "token": "doordash"},
    {"name": "Discord",         "ats": "greenhouse", "token": "discord"},
    {"name": "Reddit",          "ats": "greenhouse", "token": "reddit"},
    {"name": "Twitch",          "ats": "greenhouse", "token": "twitch"},
    {"name": "Pinterest",       "ats": "greenhouse", "token": "pinterest"},
    {"name": "Dropbox",         "ats": "greenhouse", "token": "dropbox"},
    {"name": "Squarespace",     "ats": "greenhouse", "token": "squarespace"},
    {"name": "Duolingo",        "ats": "greenhouse", "token": "duolingo"},
    {"name": "Calm",            "ats": "greenhouse", "token": "calm"},
    {"name": "Peloton",         "ats": "greenhouse", "token": "peloton"},
    {"name": "Udemy",           "ats": "greenhouse", "token": "udemy"},

    # ── Design / Creative ─────────────────────────────────────────────────────
    {"name": "Figma",           "ats": "greenhouse", "token": "figma"},
    {"name": "Canva",           "ats": "greenhouse", "token": "canva"},
    {"name": "Loom",            "ats": "greenhouse", "token": "loom"},

    # ── E-commerce / Retail ───────────────────────────────────────────────────
    {"name": "Instacart",       "ats": "greenhouse", "token": "instacart"},
    {"name": "Stitch Fix",      "ats": "greenhouse", "token": "stitchfix"},
    {"name": "Opendoor",        "ats": "greenhouse", "token": "opendoor"},
    {"name": "Flexport",        "ats": "greenhouse", "token": "flexport"},

    # ── AI / Data ─────────────────────────────────────────────────────────────
    {"name": "Scale AI",        "ats": "greenhouse", "token": "scaleai"},
    {"name": "Waymo",           "ats": "greenhouse", "token": "waymo"},

    # ── Other Tech ────────────────────────────────────────────────────────────
    {"name": "Zendesk",         "ats": "greenhouse", "token": "zendesk"},
    {"name": "HubSpot",         "ats": "greenhouse", "token": "hubspot"},
    {"name": "Quora",           "ats": "greenhouse", "token": "quora"},
    {"name": "Segment",         "ats": "greenhouse", "token": "segment"},

    # ══════════════════════════════════════════════════════════════════════════
    # LEVER  (23 companies)
    # Endpoint: https://api.lever.co/v0/postings/{token}?mode=json
    # ══════════════════════════════════════════════════════════════════════════

    # ── Streaming / Entertainment ─────────────────────────────────────────────
    {"name": "Netflix",         "ats": "lever", "token": "netflix"},

    # ── Dev Tools / Infrastructure ────────────────────────────────────────────
    {"name": "Vercel",          "ats": "lever", "token": "vercel"},
    {"name": "Netlify",         "ats": "lever", "token": "netlify"},
    {"name": "Postman",         "ats": "lever", "token": "postman"},
    {"name": "Sourcegraph",     "ats": "lever", "token": "sourcegraph"},
    {"name": "LaunchDarkly",    "ats": "lever", "token": "launchdarkly"},
    {"name": "CockroachLabs",   "ats": "lever", "token": "cockroachlabs"},
    {"name": "Grafana Labs",    "ats": "lever", "token": "grafanalabs"},

    # ── Fintech / Banking ─────────────────────────────────────────────────────
    {"name": "Mercury",         "ats": "lever", "token": "mercury"},

    # ── SaaS / Productivity ───────────────────────────────────────────────────
    {"name": "Retool",          "ats": "lever", "token": "retool"},
    {"name": "Contentful",      "ats": "lever", "token": "contentful"},
    {"name": "Miro",            "ats": "lever", "token": "miro"},
    {"name": "Zapier",          "ats": "lever", "token": "zapier"},
    {"name": "Coda",            "ats": "lever", "token": "coda"},
    {"name": "Calendly",        "ats": "lever", "token": "calendly"},
    {"name": "Braze",           "ats": "lever", "token": "braze"},

    # ── AI / ML ───────────────────────────────────────────────────────────────
    {"name": "Weights & Biases","ats": "lever", "token": "wandb"},
    {"name": "Anyscale",        "ats": "lever", "token": "anyscale"},
    {"name": "Replit",          "ats": "lever", "token": "replit"},

    # ── Media / Creative ──────────────────────────────────────────────────────
    {"name": "Descript",        "ats": "lever", "token": "descript"},
    {"name": "Wistia",          "ats": "lever", "token": "wistia"},

    # ── Data / APIs ───────────────────────────────────────────────────────────
    {"name": "Lob",             "ats": "lever", "token": "lob"},
    {"name": "Temporal",        "ats": "lever", "token": "temporal"},

    # ══════════════════════════════════════════════════════════════════════════
    # ASHBY  (20 companies)
    # Endpoint: https://api.ashbyhq.com/posting-api/job-board/{token}
    # ══════════════════════════════════════════════════════════════════════════

    # ── Project Management / SaaS ─────────────────────────────────────────────
    {"name": "Linear",          "ats": "ashby", "token": "linear"},
    {"name": "Superhuman",      "ats": "ashby", "token": "superhuman"},
    {"name": "Coda (Ashby)",    "ats": "ashby", "token": "coda"},

    # ── Fintech / HR Tech ─────────────────────────────────────────────────────
    {"name": "Ramp",            "ats": "ashby", "token": "ramp"},
    {"name": "Deel",            "ats": "ashby", "token": "deel"},
    {"name": "Rippling",        "ats": "ashby", "token": "rippling"},
    {"name": "Vanta",           "ats": "ashby", "token": "vanta"},

    # ── Climate / Sustainability ──────────────────────────────────────────────
    {"name": "Watershed",       "ats": "ashby", "token": "watershed"},

    # ── Data / Analytics ──────────────────────────────────────────────────────
    {"name": "dbt Labs",        "ats": "ashby", "token": "dbtlabs"},
    {"name": "Hex",             "ats": "ashby", "token": "hex"},

    # ── Developer Tools ───────────────────────────────────────────────────────
    {"name": "Warp",            "ats": "ashby", "token": "warp"},
    {"name": "Cursor",          "ats": "ashby", "token": "anysphere"},   # Cursor's Ashby slug

    # ── AI / LLM / Foundation Models ─────────────────────────────────────────
    {"name": "Anthropic",       "ats": "ashby", "token": "anthropic"},
    {"name": "Perplexity AI",   "ats": "ashby", "token": "perplexityai"},
    {"name": "ElevenLabs",      "ats": "ashby", "token": "elevenlabs"},
    {"name": "Mistral AI",      "ats": "ashby", "token": "mistral"},
    {"name": "Cohere",          "ats": "ashby", "token": "cohere"},
    {"name": "Together AI",     "ats": "ashby", "token": "togetherai"},
    {"name": "Modal",           "ats": "ashby", "token": "modal"},

    # ── Creative AI ───────────────────────────────────────────────────────────
    {"name": "Runway",          "ats": "ashby", "token": "runwayml"},
]


# ── Quick validation ──────────────────────────────────────────────────────────

def _validate() -> None:
    """Warn about duplicate (ats, token) pairs."""
    seen: set[tuple] = set()
    for co in COMPANIES:
        key = (co["ats"], co["token"])
        if key in seen:
            import warnings
            warnings.warn(
                f"Duplicate ATS token detected: ats={co['ats']!r}, token={co['token']!r} "
                f"(company={co['name']!r}). One copy will produce duplicate listings.",
                stacklevel=2,
            )
        seen.add(key)


_validate()
