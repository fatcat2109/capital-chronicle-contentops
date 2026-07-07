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
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes the two-step Threads Graph API publishing flow."""
    threads_user_id = _threads_user_id(threads_user_id)
    access_token = _threads_token(access_token)
    missing = [name for name, value in (("threads_user_id", threads_user_id), ("access_token", access_token), ("text", text)) if not value]
    if missing:
        return _validation_failed(missing)

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


def execute_threads_edit(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Threads API does not support editing existing posts."""
    return {"status": "UNSUPPORTED", "action": "edit", "platform_id": "threads", "reason": "threads_api_does_not_support_post_edit"}
