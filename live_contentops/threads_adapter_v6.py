"""Threads official REST API adapter for ContentOps V6.

Supports threads creation, publishing, and replying using urllib.request.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"


def compile_threads_payload(
    text: str,
    media_type: str = "TEXT",
    image_url: str | None = None,
    reply_to_id: str | None = None,
) -> dict[str, Any]:
    """Compiles the payload for creating a Threads media container."""
    payload: dict[str, Any] = {
        "media_type": media_type,
        "text": text,
    }
    if image_url:
        payload["image_url"] = image_url
    if reply_to_id:
        payload["reply_to_id"] = reply_to_id
    return payload


def execute_threads_post(
    threads_user_id: str,
    access_token: str,
    text: str,
    image_url: str | None = None,
    reply_to_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes the two-step Threads Graph API publishing flow:

    1. Create threads container
    2. Publish threads container
    """
    create_url = f"https://graph.threads.net/v1.0/{threads_user_id}/threads"
    create_payload = compile_threads_payload(text, "TEXT" if not image_url else "IMAGE", image_url, reply_to_id)
    create_payload["access_token"] = access_token

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": create_url,
            "container_payload_redacted": {
                "media_type": "TEXT" if not image_url else "IMAGE",
                "text": text,
                "image_url": image_url,
                "reply_to_id": reply_to_id,
                "access_token": "<redacted>",
            },
            "response": {
                "id": f"{threads_user_id}_mock_thread_12345",
            },
        }

    # Step 1: Create threads container
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

    # Step 2: Publish threads container
    publish_url = f"https://graph.threads.net/v1.0/{threads_user_id}/threads_publish"
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
