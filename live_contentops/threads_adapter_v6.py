"""Threads official REST API adapter for ContentOps V6.

Supports thread creation, publishing, replies, and explicit unsupported edit
results using urllib.request. Secrets are env fallbacks and never logged.
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
THREADS_GRAPH_VERSION = "v1.0"


def _first_nonblank(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _threads_token(access_token: str | None = None) -> str:
    return _first_nonblank(access_token, os.environ.get("THREADS_USER_ACCESS_TOKEN"), os.environ.get("THREADS_ACCESS_TOKEN"))


def _threads_user_id(threads_user_id: str | None = None) -> str:
    return _first_nonblank(threads_user_id, os.environ.get("THREADS_USER_ID"))


def _validation_failed(missing: list[str]) -> dict[str, Any]:
    return {"status": "VALIDATION_FAILED", "missing": missing}


def _parse_http_error(error: urllib.error.HTTPError, status: str = "FAILED") -> dict[str, Any]:
    body = error.read().decode("utf-8", errors="replace")
    try:
        parsed: Any = json.loads(body)
    except Exception:
        parsed = {"raw_error": body}
    return {"status": status, "error_code": error.code, "error_response": parsed}


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


def compile_threads_payload(text: str, media_type: str = "TEXT", image_url: str | None = None, reply_to_id: str | None = None) -> dict[str, Any]:
    """Compiles the payload for creating a Threads media container."""
    payload: dict[str, Any] = {"media_type": media_type, "text": text}
    if image_url:
        payload["image_url"] = image_url
    if reply_to_id:
        payload["reply_to_id"] = reply_to_id
    return payload


def execute_threads_post(
    threads_user_id: str | None = None,
    access_token: str | None = None,
    text: str = "",
    media_type: str | None = None,
    image_url: str | None = None,
    reply_to_id: str | None = None,
    expected_media_sha256: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes the two-step Threads Graph API publishing flow."""
    threads_user_id = _threads_user_id(threads_user_id)
    access_token = _threads_token(access_token)
    missing = [name for name, value in (("threads_user_id", threads_user_id), ("access_token", access_token), ("text", text)) if not value]
    if missing:
        return _validation_failed(missing)
    if image_url and expected_media_sha256:
        try:
            if sha256_bytes(read_public_image_bytes(image_url)) != expected_media_sha256:
                return {"status": "VALIDATION_FAILED", "validation_failures": ["media_manifest_hash_continuity_failed"]}
        except Exception as exc:
            return {"status": "VALIDATION_FAILED", "validation_failures": [f"media_manifest_url_unreadable:{type(exc).__name__}"]}

    media_type = media_type or ("IMAGE" if image_url else "TEXT")
    create_url = f"https://graph.threads.net/{THREADS_GRAPH_VERSION}/{threads_user_id}/threads"
    create_payload = compile_threads_payload(text, media_type, image_url, reply_to_id)

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": create_url,
            "container_payload_redacted": {**create_payload, "access_token": "<redacted>"},
            "response": {"id": f"{threads_user_id}_mock_thread_12345"},
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    create_payload["access_token"] = access_token
    payload_size = len(urllib.parse.urlencode(create_payload).encode("utf-8"))
    try:
        response, payload_size = _post_form(create_url, create_payload)
        container_id = response.get("id")
        if not container_id:
            result = {"status": "FAILED", "error": "No container ID returned in Step 1", "response": response}
        else:
            time.sleep(3)  # Give Meta's async container registration time to complete
            publish_url = f"https://graph.threads.net/{THREADS_GRAPH_VERSION}/{threads_user_id}/threads_publish"
            publish_payload = {"creation_id": container_id, "access_token": access_token}
            publish_response, publish_size = _post_form(publish_url, publish_payload)
            payload_size += publish_size
            result = {"status": "SUCCESS", "id": publish_response.get("id"), "container_id": container_id, "response": publish_response}
    except urllib.error.HTTPError as error:
        status = "FAILED_STEP_1" if "container_id" not in locals() else "FAILED_STEP_2"
        result = _parse_http_error(error, status)
        if "container_id" in locals():
            result["container_id"] = container_id
    except Exception as error:
        status = "FAILED_STEP_1" if "container_id" not in locals() else "FAILED_STEP_2"
        result = {"status": status, "error": str(error)}
        if "container_id" in locals():
            result["container_id"] = container_id

    classify_and_record_dispatch("threads", "reply" if reply_to_id else "post", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def readback_threads_post(
    *,
    post_id: str,
    expected_text: str,
    canonical_url: str | None = None,
    expected_media_local_path: str | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    access_token = _threads_token(access_token)
    if not post_id or not access_token:
        return _validation_failed([name for name, value in (("post_id", post_id), ("access_token", access_token)) if not value])
    try:
        value = _get_json(
            f"https://graph.threads.net/{THREADS_GRAPH_VERSION}/{post_id}",
            {"fields": "id,text,media_type,media_url,permalink,username,timestamp", "access_token": access_token},
        )
    except urllib.error.HTTPError as error:
        return _parse_http_error(error, "FAILED_READBACK")
    except Exception as error:
        return {"status": "FAILED_READBACK", "error_class": type(error).__name__}
    visible_text = " ".join(str(value.get("text") or "").split())
    expected_normalized = " ".join(expected_text.split())
    text_verified = bool(expected_normalized and expected_normalized.casefold() in visible_text.casefold())
    media_url = str(value.get("media_url") or "")
    similarity = None
    if media_url and expected_media_local_path:
        try:
            similarity = visual_similarity_to_local_file(read_public_image_bytes(media_url), expected_media_local_path)
        except Exception:
            similarity = None
    media_verified = True if not expected_media_local_path else bool(
        similarity is not None and similarity >= PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM
    )
    meaningful_media_visible = bool(
        media_url
        and (
            not expected_media_local_path
            or (similarity is not None and similarity >= PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM)
        )
    )
    link_verified = True if not canonical_url else canonical_url in visible_text
    permalink = str(value.get("permalink") or "") or None
    username = str(value.get("username") or "")
    verified = bool(text_verified and media_verified and link_verified and permalink and username.casefold() == "official.capitalchronicle")
    return {
        "status": "SUCCESS" if verified else "FAILED_THREADS_STRICT_READBACK",
        "platform": "threads",
        "post_id": str(value.get("id") or post_id),
        "public_url": permalink,
        "destination_identity": username,
        "account_identity_verified": username.casefold() == "official.capitalchronicle",
        "visible_body_text": visible_text,
        "body_text_visible": text_verified,
        "substack_url_visible": link_verified,
        "meaningful_media_visible": meaningful_media_visible,
        "expected_chart_visual_similarity": similarity,
        "media_type": value.get("media_type"),
    }


def readback_threads_chain(
    *,
    root_id: str,
    reply_expectations: list[dict[str, Any]],
    access_token: str | None = None,
) -> dict[str, Any]:
    access_token = _threads_token(access_token)
    if not root_id or not access_token:
        return _validation_failed([name for name, value in (("root_id", root_id), ("access_token", access_token)) if not value])
    try:
        edge = _get_json(
            f"https://graph.threads.net/{THREADS_GRAPH_VERSION}/{root_id}/replies",
            {"fields": "id,text,media_type,media_url,permalink,username,timestamp", "reverse": "true", "access_token": access_token},
        )
    except Exception as error:
        return {"status": "FAILED_THREADS_REPLY_EDGE_READBACK", "error_class": type(error).__name__}
    rows = list(edge.get("data") or [])
    edge_ids = [str(row.get("id") or "") for row in rows]
    ordered: list[dict[str, Any]] = []
    for index, expectation in enumerate(reply_expectations, start=1):
        reply_id = str(expectation.get("id") or "")
        row = next((item for item in rows if str(item.get("id") or "") == reply_id), None)
        text = " ".join(str((row or {}).get("text") or "").split())
        expected_text = " ".join(str(expectation.get("text") or "").split())
        ordered.append(
            {
                "order": index,
                "id": reply_id,
                "public_url": (row or {}).get("permalink"),
                "parent_root_id": root_id,
                "parent_child_verified": reply_id in edge_ids,
                "text_verified": bool(expected_text and expected_text.casefold() in text.casefold()),
            }
        )
    expected_ids = [str(item.get("id") or "") for item in reply_expectations]
    chronological_ids = [
        str(row.get("id") or "")
        for row in sorted(rows, key=lambda row: str(row.get("timestamp") or ""))
    ]
    provider_positions = [chronological_ids.index(reply_id) for reply_id in expected_ids if reply_id in chronological_ids]
    provider_order_verified = len(provider_positions) == len(expected_ids) and provider_positions == sorted(provider_positions)
    success = bool(
        ordered
        and provider_order_verified
        and all(row["parent_child_verified"] and row["text_verified"] for row in ordered)
    )
    return {
        "status": "SUCCESS" if success else "FAILED_THREADS_REPLY_CHAIN_READBACK",
        "platform": "threads",
        "root_id": root_id,
        "reply_ids_in_provider_order": edge_ids,
        "reply_ids_in_chronological_order": chronological_ids,
        "provider_order_verified": provider_order_verified,
        "ordered_replies": ordered,
    }


def execute_threads_edit(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Threads API does not support editing existing posts."""
    return {"status": "UNSUPPORTED", "action": "edit", "platform_id": "threads", "reason": "threads_api_does_not_support_post_edit"}
