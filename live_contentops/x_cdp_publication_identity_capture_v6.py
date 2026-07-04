"""Pure helpers for no-API X browser/CDP publication identity capture."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from live_contentops.platform_publication_identity_registry_v6 import extract_x_status_identity, is_x_status_url

DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")


def normalize_visible_text(text: str) -> str:
    """Normalizes visible X text for browser-only matching."""
    text = unicodedata.normalize("NFKC", text or "").translate(DASHES)
    return re.sub(r"\s+", " ", text).strip()


def visible_text_matches(expected: str, observed: str) -> bool:
    return normalize_visible_text(expected) in normalize_visible_text(observed)


def capture_current_x_post_detail_identity(current_url: str, visible_text: str, expected_text: str) -> dict[str, Any]:
    """Captures identity from an already-open X post detail page."""
    if not is_x_status_url(current_url):
        return {"result_class": "BLOCKED_NOT_X_STATUS_URL", "public_url_captured": False}
    if not visible_text_matches(expected_text, visible_text):
        return {"result_class": "BLOCKED_EXPECTED_TEXT_NOT_VISIBLE", "public_url_captured": False}
    identity = extract_x_status_identity(current_url)
    return {"result_class": "X_POST_IDENTITY_CAPTURED", "public_url_captured": True, **identity}


def capture_after_x_post_click(current_url: str, visible_text: str, expected_text: str) -> dict[str, Any]:
    """Classifies post-click browser state without using API or storage."""
    captured = capture_current_x_post_detail_identity(current_url, visible_text, expected_text)
    if captured["public_url_captured"]:
        captured["capture_method"] = "x_cdp_post_detail_after_click"
        return captured
    return {"result_class": "BLOCKED_POST_URL_NOT_CAPTURED_AFTER_CLICK", "public_url_captured": False}


def reconcile_latest_x_timeline_post(candidate_urls: list[str], visible_texts: list[str], expected_text: str) -> dict[str, Any]:
    """Chooses one matching visible status URL from timeline candidates."""
    matches = []
    for url, text in zip(candidate_urls, visible_texts):
        if is_x_status_url(url) and visible_text_matches(expected_text, text):
            matches.append(extract_x_status_identity(url))
    if len(matches) == 1:
        return {"result_class": "X_TIMELINE_RECONCILE_CONFIDENT", "public_url_captured": True, **matches[0]}
    if not matches:
        return {"result_class": "BLOCKED_NO_TIMELINE_MATCH", "public_url_captured": False}
    return {"result_class": "BLOCKED_AMBIGUOUS_TIMELINE_MATCH", "public_url_captured": False, "match_count": len(matches)}
