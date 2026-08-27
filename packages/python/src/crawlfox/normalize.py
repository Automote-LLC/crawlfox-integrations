"""Normalize API camelCase payloads to snake_case for typed models."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union

Json = Union[Dict[str, Any], List[Any], Any]

# Known API keys → snake_case (also used when auto-convert would be ambiguous).
_KEY_MAP = {
    "sourceURL": "source_url",
    "statusCode": "status_code",
    "scrapeId": "scrape_id",
    "creditsUsed": "credits_used",
    "cacheState": "cache_state",
    "rawHtml": "raw_html",
    "extractMainContent": "extract_main_content",
    "skipCache": "skip_cache",
    "jsonOptions": "json_options",
}


def camel_to_snake(name: str) -> str:
    if name in _KEY_MAP:
        return _KEY_MAP[name]
    # already snake
    if "_" in name and name.lower() == name:
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case request kwargs that need camelCase on the wire."""
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def normalize_keys(obj: Json) -> Json:
    """Recursively convert dict keys from camelCase to snake_case."""
    if isinstance(obj, list):
        return [normalize_keys(x) for x in obj]
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            out[camel_to_snake(str(k))] = normalize_keys(v)
        return out
    return obj
