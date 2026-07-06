"""Telegram Live Dispatch Adapter for ContentOps V6 (Fast Ship Mode).

Executes channel posting, commenting/replying, and message editing on Telegram
via Bot API using environment credentials under Fast Ship Mode.
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


def _get_default_bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN") or ""


def _get_default_chat_id() -> str:
    return (
        os.environ.get("TELEGRAM_TARGET_CHAT_ID")
        or os.environ.get("TEST_TELEGRAM_CHANNEL")
        or os.environ.get("TELEGRAM_CHANNEL_ID")
        or ""
    )


def execute_telegram_post(
    message: str,
    chat_id: str | None = None,
    bot_token: str | None = None,
    parse_mode: str = "HTML",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Publishes a message to a Telegram channel or chat via Bot API."""
    token = bot_token or _get_default_bot_token()
    target_chat = chat_id or _get_default_chat_id()
    payload_hash = hashlib.md5(f"{target_chat}:{message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "telegram",
            "action": "post",
            "payload_redacted": {
                "chat_id": target_chat,
                "message": message,
                "parse_mode": parse_mode,
            },
            "response": {
                "id": f"telegram_mock_msg_{payload_hash}",
            },
        }

    if not token or not target_chat:
        return {
            "status": "FAILED",
            "platform": "telegram",
            "action": "post",
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_TARGET_CHAT_ID.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": parse_mode,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            msg_id = str(res_json.get("result", {}).get("message_id", f"msg_{payload_hash}"))
            result = {
                "status": "SUCCESS",
                "platform": "telegram",
                "action": "post",
                "id": msg_id,
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
            "platform": "telegram",
            "action": "post",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "telegram",
            "action": "post",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="telegram",
        action="post",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result


def execute_telegram_photo(
    photo_url: str,
    caption: str,
    chat_id: str | None = None,
    bot_token: str | None = None,
    parse_mode: str = "HTML",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Publishes a photo with caption via Telegram Bot API sendPhoto."""
    token = bot_token or _get_default_bot_token()
    target_chat = chat_id or _get_default_chat_id()
    payload_hash = hashlib.md5(f"{target_chat}:{photo_url}:{caption}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "telegram",
            "action": "photo",
            "payload_redacted": {
                "chat_id": target_chat,
                "photo_url": photo_url,
                "caption": caption,
                "parse_mode": parse_mode,
            },
            "response": {"id": f"telegram_mock_photo_{payload_hash}"},
        }

    if not token or not target_chat:
        return {
            "status": "FAILED",
            "platform": "telegram",
            "action": "photo",
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_TARGET_CHAT_ID.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    api_url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": target_chat, "photo": photo_url, "caption": caption, "parse_mode": parse_mode}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            msg_id = str(res_json.get("result", {}).get("message_id", f"photo_{payload_hash}"))
            result = {"status": "SUCCESS", "platform": "telegram", "action": "photo", "id": msg_id, "response": res_json}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw_error": err_body}
        result = {"status": "FAILED", "platform": "telegram", "action": "photo", "error_code": e.code, "error_response": err_json}
    except Exception as e:
        result = {"status": "FAILED", "platform": "telegram", "action": "photo", "error": str(e)}

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="telegram",
        action="photo",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result


def execute_telegram_comment(
    reply_to_message_id: int | str,
    message: str,
    chat_id: str | None = None,
    bot_token: str | None = None,
    parse_mode: str = "HTML",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Posts a reply to a specific message in a Telegram chat/channel."""
    token = bot_token or _get_default_bot_token()
    target_chat = chat_id or _get_default_chat_id()
    payload_hash = hashlib.md5(f"{reply_to_message_id}:{message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "telegram",
            "action": "comment",
            "payload_redacted": {
                "chat_id": target_chat,
                "reply_to_message_id": reply_to_message_id,
                "message": message,
            },
            "response": {
                "id": f"telegram_mock_reply_{payload_hash}",
            },
        }

    if not token or not target_chat:
        return {
            "status": "FAILED",
            "platform": "telegram",
            "action": "comment",
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_TARGET_CHAT_ID.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "reply_to_message_id": int(reply_to_message_id) if str(reply_to_message_id).isdigit() else reply_to_message_id,
        "parse_mode": parse_mode,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            msg_id = str(res_json.get("result", {}).get("message_id", f"msg_{payload_hash}"))
            result = {
                "status": "SUCCESS",
                "platform": "telegram",
                "action": "comment",
                "id": msg_id,
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
            "platform": "telegram",
            "action": "comment",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "telegram",
            "action": "comment",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="telegram",
        action="comment",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result


def execute_telegram_edit(
    message_id: int | str,
    new_message: str,
    chat_id: str | None = None,
    bot_token: str | None = None,
    parse_mode: str = "HTML",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Edits a previously sent Telegram message via Bot API editMessageText."""
    token = bot_token or _get_default_bot_token()
    target_chat = chat_id or _get_default_chat_id()
    payload_hash = hashlib.md5(f"{message_id}:{new_message}".encode("utf-8")).hexdigest()[:12]

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "telegram",
            "action": "edit",
            "payload_redacted": {
                "chat_id": target_chat,
                "message_id": message_id,
                "new_message": new_message,
            },
            "response": {
                "id": str(message_id),
            },
        }

    if not token or not target_chat or not message_id:
        return {
            "status": "FAILED",
            "platform": "telegram",
            "action": "edit",
            "error": "Missing TELEGRAM_BOT_TOKEN, chat_id, or message_id.",
        }

    from .live_telemetry_v6 import classify_and_record_dispatch

    t0 = time.perf_counter()
    api_url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": target_chat,
        "message_id": int(message_id) if str(message_id).isdigit() else message_id,
        "text": new_message,
        "parse_mode": parse_mode,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            result = {
                "status": "SUCCESS",
                "platform": "telegram",
                "action": "edit",
                "id": str(message_id),
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
            "platform": "telegram",
            "action": "edit",
            "error_code": e.code,
            "error_response": err_json,
        }
    except Exception as e:
        result = {
            "status": "FAILED",
            "platform": "telegram",
            "action": "edit",
            "error": str(e),
        }

    latency_ms = (time.perf_counter() - t0) * 1000.0
    classify_and_record_dispatch(
        platform_id="telegram",
        action="edit",
        adapter_result=result,
        latency_ms=latency_ms,
        payload_size_bytes=len(data),
    )
    return result
