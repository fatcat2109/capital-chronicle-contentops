"""Instagram Business official REST API adapter for ContentOps V6.

Supports media container creation, publishing, comments, and explicit unsupported
edit results using urllib.request. Secrets are env fallbacks and never logged.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_FACEBOOK_INSTAGRAM_AND_THREADS_V0"
GRAPH_VERSION = "v21.0"


def _first_nonblank(*values: str | None) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _instagram_token(access_token: str | None = None) -> str:
    return _first_nonblank(access_token, os.environ.get("INSTAGRAM_ACCESS_TOKEN"), os.environ.get("META_ACCESS_TOKEN"))


def _instagram_id(ig_id: str | None = None) -> str:
    return _first_nonblank(ig_id, os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID"), os.environ.get("INSTAGRAM_IG_ID"))


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


def compile_instagram_media_payload(image_url: str, caption: str) -> dict[str, Any]:
    """Compiles the payload for creating an Instagram media container."""
    return {"image_url": image_url, "caption": caption}


def _read_remote_image_dimensions(image_url: str, timeout_seconds: int) -> tuple[int, int] | None:
    try:
        from PIL import Image
    except Exception:
        return None

    req = urllib.request.Request(image_url, method="GET", headers={"User-Agent": "ContentOps/6.0"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if not content_type.startswith("image/"):
            raise ValueError(f"image_url_not_image:{content_type or 'missing_content_type'}")
        data = response.read(8 * 1024 * 1024)
    image = Image.open(BytesIO(data))
    image.load()
    return int(image.width), int(image.height)


def validate_instagram_image_url(image_url: str, timeout_seconds: int = 10) -> list[str]:
    if not image_url.startswith(("https://", "http://")):
        return ["image_url_not_http"]

    def _validate(method: str) -> list[str]:
        headers = {"User-Agent": "ContentOps/6.0"}
        if method == "GET":
            headers["Range"] = "bytes=0-0"
        req = urllib.request.Request(image_url, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                return [f"image_url_not_image:{content_type or 'missing_content_type'}"]
        return []

    try:
        failures = _validate("HEAD")
        if failures:
            return failures
    except urllib.error.HTTPError as exc:
        if exc.code != 405:
            return [f"image_url_unreachable:{exc}"]
    except Exception as exc:
        return [f"image_url_unreachable:{exc}"]

    try:
        dimensions = _read_remote_image_dimensions(image_url, timeout_seconds)
    except Exception as exc:
        reason = str(exc)
        if reason.startswith("image_url_not_image:"):
            return [reason]
        return [f"image_url_unreachable:{exc}"]
    if not dimensions:
        return []
    width, height = dimensions
    if width <= 0 or height <= 0:
        return ["image_dimensions_unreadable"]
    aspect = width / height
    if aspect < 0.8 or aspect > 1.91:
        return [f"image_aspect_ratio_unsupported:{width}x{height}:{aspect:.3f}"]
    return []


def execute_instagram_post(
    ig_id: str | None = None,
    access_token: str | None = None,
    image_url: str = "",
    caption: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes the two-step Instagram Graph API media publishing flow."""
    ig_id = _instagram_id(ig_id)
    access_token = _instagram_token(access_token)
    missing = [name for name, value in (("ig_id", ig_id), ("access_token", access_token), ("image_url", image_url), ("caption", caption)) if not value]
    if missing:
        return _validation_failed(missing)

    create_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_id}/media"
    create_payload = compile_instagram_media_payload(image_url, caption)

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": create_url,
            "container_payload_redacted": {**create_payload, "access_token": "<redacted>"},
            "response": {"id": f"{ig_id}_mock_media_12345"},
        }

    media_failures = validate_instagram_image_url(image_url)
    if media_failures:
        return {"status": "VALIDATION_FAILED", "missing": [], "validation_failures": media_failures}

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
            publish_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_id}/media_publish"
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

    classify_and_record_dispatch("instagram", "post", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def execute_instagram_comment(
    media_id: str,
    access_token: str | None = None,
    message: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to publish a comment on an Instagram media object."""
    access_token = _instagram_token(access_token)
    missing = [name for name, value in (("media_id", media_id), ("access_token", access_token), ("message", message)) if not value]
    if missing:
        return _validation_failed(missing)

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{media_id}/comments"
    payload = {"message": message}
    if dry_run:
        return {"status": "DRY_RUN_PASS", "url": url, "payload_redacted": {**payload, "access_token": "<redacted>"}, "response": {"id": f"{media_id}_mock_comment_67890"}}

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

    classify_and_record_dispatch("instagram", "comment", result, (time.perf_counter() - t0) * 1000.0, payload_size)
    return result


def execute_instagram_edit(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Instagram Graph API does not provide a normal post-edit endpoint."""
    return {"status": "UNSUPPORTED", "action": "edit", "platform_id": "instagram", "reason": "instagram_content_publishing_api_does_not_support_post_edit"}
