"""Discord Live Dispatch Adapter for ContentOps V6 (Fast Ship Mode).

Executes post publishing, commenting, and editing on Discord via Webhooks
using environment credentials under Fast Ship Mode.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_DISCORD_AND_TELEGRAM_V0"


def _get_default_webhook_url() -> str:
    return (
        os.environ.get("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
        or os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK")
        or ""
    )


def execute_discord_post(
    message: str,
    webhook_url: str | None = None,
    embeds: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Publishes a message or announcement to a Discord channel via Webhook."""
    target_webhook = webhook_url or _get_default_webhook_url()
    payload_hash = hashlib.md5(f"{target_webhook}:{message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "discord",
            "action": "post",
            "payload_redacted": {
                "message": message,
                "embeds_count": len(embeds) if embeds else 0,
                "webhook_url": "<redacted>",
            },
            "response": {
                "id": f"discord_mock_msg_{payload_hash}",
            },
        }

    if not target_webhook:
        return {
            "status": "FAILED",
            "platform": "discord",
            "action": "post",
            "error": "No Discord webhook URL configured.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    post_url = target_webhook
    if "?" in post_url:
        post_url += "&wait=true"
    else:
        post_url += "?wait=true"

    payload: dict[str, Any] = {"content": message}
    if embeds:
        payload["embeds"] = embeds

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(post_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            result = {
                "status": "SUCCESS",
                "platform": "discord",
                "action": "post",
                "id": res_json.get("id", f"msg_{payload_hash}"),
                "response": res_json,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "post",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "post",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="discord",
        action="post",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result


def readback_discord_post(
    *,
    message_id: str,
    expected_text: str,
    canonical_url: str,
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Read one exact webhook message without exposing the webhook credential."""
    target_webhook = webhook_url or _get_default_webhook_url()
    if not target_webhook or not str(message_id or "").isdigit():
        return {"status": "READBACK_UNAVAILABLE", "verified": False}
    request = urllib.request.Request(
        f"{target_webhook.rstrip('/')}/messages/{message_id}", method="GET"
    )
    request.add_header("User-Agent", "CapitalChronicleContentOps/1.0")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return {
            "status": "NOT_FOUND" if error.code == 404 else "READBACK_UNAVAILABLE",
            "verified": False,
            "write_absent": error.code == 404,
        }
    except Exception:
        return {"status": "READBACK_UNAVAILABLE", "verified": False}
    observed_id = str(payload.get("id") or "")
    content = str(payload.get("content") or "")
    embeds = payload.get("embeds") if isinstance(payload.get("embeds"), list) else []
    channel_id = str(payload.get("channel_id") or "")
    guild_id = str(payload.get("guild_id") or "")
    exact_identity = observed_id == str(message_id)
    text_verified = bool(expected_text and expected_text in content)
    canonical_verified = canonical_url in content
    media_verified = any(
        bool((row.get("image") or {}).get("url"))
        for row in embeds
        if isinstance(row, Mapping)
    )
    verified = bool(exact_identity and text_verified and canonical_verified and media_verified)
    public_url = (
        f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        if guild_id and channel_id
        else None
    )
    return {
        "status": "SUCCESS" if verified else "FAILED_DISCORD_STRICT_READBACK",
        "verified": verified,
        "write_exists": exact_identity,
        "message_id": observed_id or None,
        "public_url": public_url,
        "body_text_visible": text_verified,
        "substack_url_visible": canonical_verified,
        "meaningful_media_visible": media_verified,
    }


def execute_discord_comment(
    thread_id_or_url: str,
    message: str,
    webhook_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Posts a comment or thread reply on Discord via Webhook."""
    target_webhook = webhook_url or _get_default_webhook_url()
    payload_hash = hashlib.md5(f"{thread_id_or_url}:{message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "discord",
            "action": "comment",
            "payload_redacted": {
                "thread_id": thread_id_or_url,
                "message": message,
            },
            "response": {
                "id": f"discord_mock_comment_{payload_hash}",
            },
        }

    if not target_webhook:
        return {
            "status": "FAILED",
            "platform": "discord",
            "action": "comment",
            "error": "No Discord webhook URL configured.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    post_url = target_webhook
    params = ["wait=true"]
    if thread_id_or_url and thread_id_or_url.isdigit():
        params.append(f"thread_id={thread_id_or_url}")

    sep = "&" if "?" in post_url else "?"
    post_url += sep + "&".join(params)

    payload = {"content": message}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(post_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            result = {
                "status": "SUCCESS",
                "platform": "discord",
                "action": "comment",
                "id": res_json.get("id", f"msg_{payload_hash}"),
                "response": res_json,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "comment",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "comment",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="discord",
        action="comment",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result


def execute_discord_edit(
    message_id: str,
    new_message: str,
    webhook_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Edits a previously published Discord webhook message via PATCH."""
    target_webhook = webhook_url or _get_default_webhook_url()
    payload_hash = hashlib.md5(f"{message_id}:{new_message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "discord",
            "action": "edit",
            "payload_redacted": {
                "message_id": message_id,
                "new_message": new_message,
            },
            "response": {
                "id": message_id,
            },
        }

    if not target_webhook or not message_id:
        return {
            "status": "FAILED",
            "platform": "discord",
            "action": "edit",
            "error": "Missing Discord webhook URL or message_id.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    edit_url = f"{target_webhook.rstrip('/')}/messages/{message_id}"
    payload = {"content": new_message}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(edit_url, data=data, method="PATCH")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            result = {
                "status": "SUCCESS",
                "platform": "discord",
                "action": "edit",
                "id": message_id,
                "response": res_json,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "edit",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "discord",
            "action": "edit",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="discord",
        action="edit",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result
