"""
custom_sources.py — Custom company boards and job sources
==========================================================
Add any companies or resources you are interested in here!

You can also use custom_sources.json if you prefer JSON format.
Settings here and in custom_sources.json are loaded automatically.
"""

# If True, the alert runner will ONLY check sources defined as custom/interested
INTERESTED_ONLY = False

# Optional: filter to specific source or company names (case-insensitive)
# E.g.: ["Stripe", "Linear", "Spotify", "Himalayas"]
# Leave empty [] to check all sources.
FILTER_SOURCES: list[str] = []

# Custom ATS company listings
# Supported 'ats' values: "greenhouse", "lever", "ashby"
CUSTOM_COMPANIES: list[dict] = [
    {"name": "Spotify", "ats": "lever", "token": "spotify", "enabled": True},
    {"name": "Palantir", "ats": "lever", "token": "palantir", "enabled": True},
    {"name": "OpenAI", "ats": "greenhouse", "token": "openai", "enabled": True},
    {"name": "Linear", "ats": "ashby", "token": "linear", "enabled": True},
]

# Custom JSON job feeds (endpoints returning job arrays or objects)
CUSTOM_FEEDS: list[dict] = [
    # {
    #     "name": "My Custom Feed",
    #     "url": "https://example.com/api/jobs",
    #     "type": "json",
    #     "enabled": False,
    # }
]
