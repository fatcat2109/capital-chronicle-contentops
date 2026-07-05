"""Facebook Page official REST API adapter for ContentOps V6.

Supports posting to Page feed and commenting on posts using urllib.request.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_SUBSTACK_AND_X_V0"


def compile_facebook_post_payload(message: str, link: str | None = None) -> dict[str, Any]:
    """Compiles the payload for a Facebook page feed post."""
    payload: dict[str, Any] = {
        "message": message,
    }
    if link:
        payload["link"] = link
    return payload


def execute_facebook_post(
    page_id: str,
    access_token: str,
    message: str,
    link: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a page feed post."""
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    payload = compile_facebook_post_payload(message, link)
    payload["access_token"] = access_token

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "url": f"https://graph.facebook.com/v21.0/{page_id}/feed",
            "payload_redacted": {
                "message": message,
                "link": link,
                "access_token": "<redacted>",
            },
            "response": {
                "id": f"{page_id}_mock_post_12345",
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


def execute_facebook_comment(
    post_id: str,
    access_token: str,
    message: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executes a POST request to graph.facebook.com to publish a comment on a post."""
    url = f"https://graph.facebook.com/v21.0/{post_id}/comments"
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
                "id": f"{post_id}_mock_comment_67890",
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
