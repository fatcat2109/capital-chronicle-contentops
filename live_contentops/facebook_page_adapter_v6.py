"""Facebook Page official REST API adapter for ContentOps V6.

Supports posting to Page feed, commenting on posts, and best-effort post edits
using urllib.request. Secrets are read from env only as fallback and never logged.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_FACEBOOK_INSTAGRAM_AND_THREADS_V0"
GRAPH_VERSION = "v21.0"


def _first_nonblank(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _facebook_token(access_token: str | None = None) -> str:
    return _first_nonblank(access_token, os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN"), os.environ.get("META_ACCESS_TOKEN"))


def _facebook_page_id(page_id: str | None = None) -> str:
    return _first_nonblank(page_id, os.environ.get("FACEBOOK_PAGE_ID"))


def _validation_failed(missing: list[str]) -> dict[str, Any]:
    return {"status": "VALIDATION_FAILED", "missing": missing}


def _parse_http_error(error: urllib.error.HTTPError) -> dict[str, Any]:
    body = error.read().decode("utf-8", errors="replace")
    try:
        parsed: Any = json.loads(body)
    except Exception:
        parsed = {"raw_error": body}
    return {"status": "FAILED", "error_code": error.code, "error_response": parsed}


def _post_form(url: str, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8")), len(data)


def compile_facebook_post_payload(message: str, link: str | None = None) -> dict[str, Any]:
    """Compiles the payload for a Facebook page feed post."""
    payload: dict[str, Any] = {"message": message}
    if link:
        payload["link"] = link
    return payload


def compile_facebook_photo_payload(message: str, image_url: str) -> dict[str, Any]:
    """Compiles the payload for a Facebook Page photo post."""
    return {"caption": message, "url": image_url}


def execute_facebook_post(
    page_id: str | None = None,
    access_token: str | None = None,
    message: str = "",
    link: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a page feed post."""
    page_id = _facebook_page_id(page_id)
    access_token = _facebook_token(access_token)
    missing = [name for name, value in (("page_id", page_id), ("access_token", access_token), ("message", message)) if not value]
    if missing:
        return _validation_failed(missing)

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/feed"
    payload = compile_facebook_post_payload(message, link)

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": url,
            "payload_redacted": {**payload, "access_token": "<redacted>"},
            "response": {"id": f"{page_id}_mock_post_12345"},
        }

    payload["access_token"] = access_token
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    payload_size = len(urllib.parse.urlencode(payload).encode("utf-8"))
    try:
        response, payload_size = _post_form(url, payload)
        result = {"status": "SUCCESS", "id": response.get("id"), "response": response}
    except urllib.error.HTTPError as error:
        result = _parse_http_error(error)
    except Exception as error:
        result = {"status": "FAILED", "error": str(error)}

    classify_and_record_dispatch("facebook_page", "post", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def execute_facebook_photo(
    page_id: str | None = None,
    access_token: str | None = None,
    message: str = "",
    image_url: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a Page photo."""
    page_id = _facebook_page_id(page_id)
    access_token = _facebook_token(access_token)
    missing = [
        name
        for name, value in (("page_id", page_id), ("access_token", access_token), ("message", message), ("image_url", image_url))
        if not value
    ]
    if missing:
        return _validation_failed(missing)

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/photos"
    payload = compile_facebook_photo_payload(message, image_url)

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": url,
            "payload_redacted": {**payload, "access_token": "<redacted>"},
            "response": {"id": f"{page_id}_mock_photo_12345", "post_id": f"{page_id}_mock_post_12345"},
        }

    payload["access_token"] = access_token
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    payload_size = len(urllib.parse.urlencode(payload).encode("utf-8"))
    try:
        response, payload_size = _post_form(url, payload)
        result = {"status": "SUCCESS", "id": response.get("post_id") or response.get("id"), "response": response}
    except urllib.error.HTTPError as error:
        result = _parse_http_error(error)
    except Exception as error:
        result = {"status": "FAILED", "error": str(error)}

    classify_and_record_dispatch("facebook_page", "photo", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def execute_facebook_comment(
    post_id: str,
    access_token: str | None = None,
    message: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a comment on a post."""
    access_token = _facebook_token(access_token)
    missing = [name for name, value in (("post_id", post_id), ("access_token", access_token), ("message", message)) if not value]
    if missing:
        return _validation_failed(missing)

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{post_id}/comments"
    payload = {"message": message}

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": url,
            "payload_redacted": {**payload, "access_token": "<redacted>"},
            "response": {"id": f"{post_id}_mock_comment_67890"},
        }

    payload["access_token"] = access_token
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    payload_size = len(urllib.parse.urlencode(payload).encode("utf-8"))
    try:
        response, payload_size = _post_form(url, payload)
        result = {"status": "SUCCESS", "id": response.get("id"), "response": response}
    except urllib.error.HTTPError as error:
        result = _parse_http_error(error)
    except Exception as error:
        result = {"status": "FAILED", "error": str(error)}

    classify_and_record_dispatch("facebook_page", "comment", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def execute_facebook_edit(
    post_id: str,
    access_token: str | None = None,
    message: str | None = None,
    link: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Best-effort Graph object update for Page posts where Meta permits it."""
    access_token = _facebook_token(access_token)
    missing = [name for name, value in (("post_id", post_id), ("access_token", access_token)) if not value]
    if not _first_nonblank(message, link):
        missing.append("message_or_link")
    if missing:
        return _validation_failed(missing)

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{post_id}"
    payload: dict[str, Any] = {}
    if message is not None:
        payload["message"] = message
    if link is not None:
        payload["link"] = link

    if dry_run:
        return {"status": "DRY_RUN_PASS", "url": url, "payload_redacted": {**payload, "access_token": "<redacted>"}}

    payload["access_token"] = access_token
    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    payload_size = len(urllib.parse.urlencode(payload).encode("utf-8"))
    try:
        response, payload_size = _post_form(url, payload)
        result = {"status": "SUCCESS", "id": post_id, "response": response}
    except urllib.error.HTTPError as error:
        result = _parse_http_error(error)
    except Exception as error:
        result = {"status": "FAILED", "error": str(error)}

    classify_and_record_dispatch("facebook_page", "edit", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result
