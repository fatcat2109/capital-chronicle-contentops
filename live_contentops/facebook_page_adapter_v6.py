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

from .media_manifest_authority_v1 import (
    PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM,
    read_public_image_bytes,
    sha256_bytes,
    visual_similarity_to_local_file,
)

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


def _get_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(payload)
    request = urllib.request.Request(f"{url}?{query}", method="GET")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _canonical_link_matches(expected_url: str, observed_url: str) -> bool:
    """Match a canonical link even when Facebook wraps it in its click redirect."""
    try:
        expected = urllib.parse.urlsplit(str(expected_url or ""))
        observed = urllib.parse.urlsplit(str(observed_url or ""))
    except ValueError:
        return False
    if (observed.hostname or "").casefold() in {"l.facebook.com", "lm.facebook.com"}:
        wrapped = urllib.parse.parse_qs(observed.query).get("u") or []
        if len(wrapped) != 1:
            return False
        try:
            observed = urllib.parse.urlsplit(urllib.parse.unquote(wrapped[0]))
        except ValueError:
            return False
    return bool(
        expected.scheme.casefold() == "https"
        and observed.scheme.casefold() == "https"
        and (expected.hostname or "").casefold()
        == (observed.hostname or "").casefold()
        and expected.path.rstrip("/") == observed.path.rstrip("/")
        and expected.username is None
        and expected.password is None
        and observed.username is None
        and observed.password is None
    )


def _attachment_urls(value: Any) -> list[str]:
    """Extract only public link fields from Graph attachment objects."""
    urls: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "url" and isinstance(child, str):
                urls.append(child)
            elif key in {"attachments", "data", "target", "subattachments"}:
                urls.extend(_attachment_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.extend(_attachment_urls(child))
    return urls


def _canonical_link_visible(value: dict[str, Any], canonical_url: str) -> bool:
    message = " ".join(str(value.get("message") or "").split())
    if canonical_url in message:
        return True
    return any(
        _canonical_link_matches(canonical_url, candidate)
        for candidate in _attachment_urls(value.get("attachments") or {})
    )


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
    expected_media_sha256: str | None = None,
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
    if expected_media_sha256:
        try:
            if sha256_bytes(read_public_image_bytes(image_url)) != expected_media_sha256:
                return {"status": "VALIDATION_FAILED", "validation_failures": ["media_manifest_hash_continuity_failed"]}
        except Exception as exc:
            return {"status": "VALIDATION_FAILED", "validation_failures": [f"media_manifest_url_unreadable:{type(exc).__name__}"]}

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


def readback_facebook_post(
    *,
    post_id: str,
    expected_text: str,
    canonical_url: str,
    expected_media_local_path: str | None = None,
    page_id: str | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Verify message, chart, canonical link, page identity, and permalink."""
    page_id = _facebook_page_id(page_id)
    access_token = _facebook_token(access_token)
    if not post_id or not access_token:
        return _validation_failed([name for name, value in (("post_id", post_id), ("access_token", access_token)) if not value])
    try:
        value = _get_json(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{post_id}",
            {
                "fields": (
                    "id,message,permalink_url,full_picture,from,"
                    "attachments{target,url,subattachments{target,url}}"
                ),
                "access_token": access_token,
            },
        )
    except urllib.error.HTTPError as error:
        return _parse_http_error(error, "FAILED_READBACK")
    except Exception as error:
        return {"status": "FAILED_READBACK", "error_class": type(error).__name__}
    message = " ".join(str(value.get("message") or "").split())
    title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
    picture_url = str(value.get("full_picture") or "")
    similarity = None
    if picture_url and expected_media_local_path:
        try:
            similarity = visual_similarity_to_local_file(read_public_image_bytes(picture_url), expected_media_local_path)
        except Exception:
            similarity = None
    permalink = str(value.get("permalink_url") or "") or None
    page_identity_verified = bool(not page_id or str((value.get("from") or {}).get("id") or "") == page_id)
    media_expected = bool(expected_media_local_path)
    media_verified = bool(
        similarity is not None and similarity >= PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM
    )
    canonical_link_visible = _canonical_link_visible(value, canonical_url)
    verified = bool(
        title_line.casefold() in message.casefold()
        and canonical_link_visible
        and (media_verified if media_expected else True)
        and permalink
        and page_identity_verified
    )
    return {
        "status": "SUCCESS" if verified else "FAILED_FACEBOOK_STRICT_READBACK",
        "platform": "facebook_page",
        "post_id": str(value.get("id") or post_id),
        "public_url": permalink,
        "destination_identity": str((value.get("from") or {}).get("name") or "Capital Chronicle"),
        "page_identity_verified": page_identity_verified,
        "visible_body_text": message,
        "body_text_visible": title_line.casefold() in message.casefold(),
        "substack_url_visible": canonical_link_visible,
        "meaningful_media_visible": media_verified,
        "media_expected": media_expected,
        "expected_chart_visual_similarity": similarity,
        "public_image_url_present": bool(picture_url),
    }


def find_recent_facebook_post(
    *,
    expected_text: str,
    canonical_url: str,
    expected_media_local_path: str,
    page_id: str | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Reconcile an uncertain photo write before any retry."""
    page_id = _facebook_page_id(page_id)
    access_token = _facebook_token(access_token)
    if not page_id or not access_token:
        return _validation_failed(["facebook_reconciliation_credentials"])
    try:
        feed = _get_json(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/posts",
            {
                "fields": (
                    "id,message,permalink_url,full_picture,from,"
                    "attachments{target,url,subattachments{target,url}}"
                ),
                "limit": "10",
                "access_token": access_token,
            },
        )
    except urllib.error.HTTPError as error:
        return _parse_http_error(error, "FAILED_RECONCILIATION")
    except Exception as error:
        return {"status": "FAILED_RECONCILIATION", "error_class": type(error).__name__}
    title_line = next((line.strip() for line in expected_text.splitlines() if line.strip()), expected_text)
    for row in feed.get("data") or []:
        message = " ".join(str(row.get("message") or "").split())
        if (
            title_line.casefold() not in message.casefold()
            or not _canonical_link_visible(row, canonical_url)
        ):
            continue
        post_id = str(row.get("id") or "")
        readback = readback_facebook_post(
            post_id=post_id,
            expected_text=expected_text,
            canonical_url=canonical_url,
            expected_media_local_path=expected_media_local_path,
            page_id=page_id,
            access_token=access_token,
        )
        if readback.get("status") == "SUCCESS":
            return readback
    return {"status": "NOT_FOUND", "platform": "facebook_page"}


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
