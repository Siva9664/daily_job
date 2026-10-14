"""
source_manager.py — Centralized manager for default + custom job sources
=======================================================================
Loads curated companies (companies.py), merges user custom sources
(custom_sources.json and/or custom_sources.py), and applies interest filters.
"""

import json
import logging
from pathlib import Path
from typing import Any

from companies import COMPANIES as DEFAULT_COMPANIES

log = logging.getLogger(__name__)

CUSTOM_SOURCES_JSON = Path("custom_sources.json")
_CONFIG_CACHE: dict[str, Any] | None = None


def load_custom_config(refresh: bool = False) -> dict[str, Any]:
    """
    Load custom sources and filter settings.
    Prioritizes custom_sources.json, then falls back to/merges custom_sources.py.
    Caches result unless refresh=True.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not refresh:
        return _CONFIG_CACHE

    config: dict[str, Any] = {
        "interested_only": False,
        "filter_sources": [],
        "ats_companies": [],
        "custom_feeds": [],
    }

    # 1. Load from custom_sources.json if it exists
    if CUSTOM_SOURCES_JSON.exists():
        try:
            data = json.loads(CUSTOM_SOURCES_JSON.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config["interested_only"] = bool(data.get("interested_only", False))
                config["filter_sources"] = [
                    s.lower().strip()
                    for s in data.get("filter_sources", [])
                    if isinstance(s, str) and s.strip()
                ]
                config["ats_companies"] = [
                    c for c in data.get("ats_companies", [])
                    if isinstance(c, dict) and c.get("enabled", True)
                ]
                config["custom_feeds"] = [
                    f for f in data.get("custom_feeds", [])
                    if isinstance(f, dict) and f.get("enabled", True)
                ]
                log.info(
                    "Loaded custom_sources.json (%d custom companies, %d custom feeds)",
                    len(config["ats_companies"]),
                    len(config["custom_feeds"]),
                )
        except Exception as exc:
            log.warning("Could not read custom_sources.json: %s", exc)

    # 2. Check custom_sources.py if present
    try:
        import custom_sources
        if not config["ats_companies"] and getattr(custom_sources, "CUSTOM_COMPANIES", None):
            config["ats_companies"] = [
                c for c in custom_sources.CUSTOM_COMPANIES
                if isinstance(c, dict) and c.get("enabled", True)
            ]
        if not config["custom_feeds"] and getattr(custom_sources, "CUSTOM_FEEDS", None):
            config["custom_feeds"] = [
                f for f in custom_sources.CUSTOM_FEEDS
                if isinstance(f, dict) and f.get("enabled", True)
            ]
        if not config["filter_sources"] and getattr(custom_sources, "FILTER_SOURCES", None):
            config["filter_sources"] = [
                s.lower().strip()
                for s in custom_sources.FILTER_SOURCES
                if isinstance(s, str) and s.strip()
            ]
        if getattr(custom_sources, "INTERESTED_ONLY", False):
            config["interested_only"] = True
    except ImportError:
        pass
    except Exception as exc:
        log.warning("Could not import custom_sources.py: %s", exc)

    _CONFIG_CACHE = config
    return config


def get_active_companies(config: dict[str, Any] | None = None) -> tuple[list[dict], bool, list[str]]:
    """
    Returns (companies_list, interested_only, filter_sources).
    Merges default ATS companies with custom companies, deduplicating by (ats, token).
    """
    if config is None:
        config = load_custom_config()
    interested_only = config["interested_only"]
    filter_sources = config["filter_sources"]
    custom_cos = config["ats_companies"]

    if interested_only:
        base_list = custom_cos
    else:
        # Merge default companies + custom companies
        seen_keys = set()
        merged = []

        # Add custom companies first so user can override or prioritize them
        for c in custom_cos:
            ats = str(c.get("ats", "")).lower().strip()
            token = str(c.get("token", "")).lower().strip()
            if ats and token:
                key = (ats, token)
                if key not in seen_keys:
                    seen_keys.add(key)
                    merged.append(c)

        for c in DEFAULT_COMPANIES:
            ats = str(c.get("ats", "")).lower().strip()
            token = str(c.get("token", "")).lower().strip()
            if ats and token:
                key = (ats, token)
                if key not in seen_keys:
                    seen_keys.add(key)
                    merged.append(c)

        base_list = merged

    # Apply filter_sources if specified
    if filter_sources:
        base_list = [
            c for c in base_list
            if any(f in c.get("name", "").lower() or f in c.get("token", "").lower() for f in filter_sources)
        ]

    return base_list, interested_only, filter_sources


def get_custom_feeds(config: dict[str, Any] | None = None) -> list[dict]:
    """Returns active custom API feeds from config."""
    if config is None:
        config = load_custom_config()
    return config.get("custom_feeds", [])

