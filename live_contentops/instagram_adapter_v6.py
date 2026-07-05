"""Instagram Business official REST API adapter for ContentOps V6.

Supports media container creation, media publishing, and commenting on media using urllib.request.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"


def compile_instagram_media_payload(image_url: str, caption: str) -> dict[str, Any]:
    """Compiles the payload for creating an Instagram media container."""
    return {
        "image_url": image_url,
        "caption": caption,
    }


def execute_instagram_post(
    ig_id: str,
    access_token: str,
    image_url: str,
    caption: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes the two-step Instagram Graph API media publishing flow:

    1. Create media container
    2. Publish media container
    """
    create_url = f"https://graph.facebook.com/v21.0/{ig_id}/media"
    create_payload = compile_instagram_media_payload(image_url, caption)
    create_payload["access_token"] = access_token

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": create_url,
            "container_payload_redacted": {
                "image_url": image_url,
                "caption": caption,
                "access_token": "<redacted>",
            },
            "response": {
                "id": f"{ig_id}_mock_media_12345",
            },
        }

    # Step 1: Create media container
    data = urllib.parse.urlencode(create_payload).encode("utf-8")
    req = urllib.request.Request(create_url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            container_id = res_data.get("id")
            if not container_id:
                return {
                    "status": "FAILED",
                    "error": "No container ID returned in Step 1",
                    "response": res_data,
                }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        return {
            "status": "FAILED_STEP_1",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        return {
            "status": "FAILED_STEP_1",
            "error": str(e),
        }

    # Step 2: Publish media container
    publish_url = f"https://graph.facebook.com/v21.0/{ig_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }
    data_publish = urllib.parse.urlencode(publish_payload).encode("utf-8")
    req_publish = urllib.request.Request(publish_url, data=data_publish, method="POST")
    req_publish.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req_publish, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return {
                "status": "SUCCESS",
                "id": res_data.get("id"),
                "container_id": container_id,
                "response": res_data,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        return {
            "status": "FAILED_STEP_2",
            "error_code": e.code,
            "error_response": err_json,
            "container_id": container_id,
        }
    except Exception as e:
        return {
            "status": "FAILED_STEP_2",
            "error": str(e),
            "container_id": container_id,
        }


def execute_instagram_comment(
    media_id: str,
    access_token: str,
    message: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a comment on a media object."""
    url = f"https://graph.facebook.com/v21.0/{media_id}/comments"
    payload = {
        "message": message,
        "access_token": access_token,
    }

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": url,
            "payload_redacted": {
                "message": message,
                "access_token": "<redacted>",
            },
            "response": {
                "id": f"{media_id}_mock_comment_67890",
            },
        }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return {
                "status": "SUCCESS",
                "id": res_data.get("id"),
                "response": res_data,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        return {
            "status": "FAILED",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
        }
