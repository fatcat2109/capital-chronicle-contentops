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
import uuid
from pathlib import Path
from typing import Any, Mapping

from .secret_store_v1 import read_secret

TASK_LABEL = "TASK_CONTENTOPS_V6_FAST_SHIP_LIVE_DISPATCH_DISCORD_AND_TELEGRAM_V0"


def _get_default_webhook_url() -> str:
    # CC-297: Credential Manager, then the live user environment, then the process environment.
    return (
        read_secret("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
        or read_secret("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK")
        or ""
    )


def execute_discord_post(
    message: str,
    webhook_url: str | None = None,
    embeds: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
    image_path: str | None = None,
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
                "image_attached": bool(image_path),
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
    parts = urllib.parse.urlsplit(target_webhook)
    query = dict(urllib.parse.parse_qsl(parts.query))
    query["wait"] = "true"
    post_url = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))

    payload: dict[str, Any] = {"content": message}
    if embeds:
        payload["embeds"] = embeds

    content_type = "application/json"
    if image_path:
        from PIL import Image

        path = Path(image_path)
        try:
            with Image.open(path) as image:
                image.verify()
                image_format = image.format
            mime, extension = {"PNG": ("image/png", "png"), "JPEG": ("image/jpeg", "jpg")}[image_format]
            image_bytes = path.read_bytes()
        except (OSError, ValueError, KeyError):
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "reason_code": "DISCORD_IMAGE_FILE_INVALID", "platform": "discord"}
        filename = "article-image." + extension
        payload["attachments"] = [{"id": 0, "filename": filename}]
        # A real attachment travels with the message; it needs no hosted URL.
        if embeds:
            payload["embeds"] = [{**embed, "image": {"url": "attachment://" + filename}}
                                  if index == 0 else dict(embed) for index, embed in enumerate(embeds)]
        boundary = "cc-discord-" + uuid.uuid4().hex
        data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\n"
                "Content-Type: application/json\r\n\r\n").encode() + json.dumps(payload).encode("utf-8")
        data += (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"files[0]\"; "
                 f"filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n").encode()
        data += image_bytes + f"\r\n--{boundary}--\r\n".encode()
        content_type = "multipart/form-data; boundary=" + boundary
    else:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(post_url, data=data, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body) if res_body else {}
            result = {
                "status": "SUCCESS",
                "platform": "discord",
                "action": "post",
                "id": res_json.get("id"),
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
    expected_image_sha256: str | None = None,
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
    attachments = [a for a in payload.get("attachments", []) if isinstance(a, Mapping)
                   and str(a.get("content_type") or "").startswith("image/") and a.get("url")]
    media_verified = media_verified or bool(attachments)
    image_hash_match = None
    if expected_image_sha256:
        image_hash_match = False
        # Discord may move a multipart image into embed.image and return an empty
        # attachments list (CC-359, 9 Nov). Verify the delivered bytes either way.
        image_candidates = [*attachments, *((row.get("image") or {}) for row in embeds if isinstance(row, Mapping))]
        for attachment in image_candidates:
            if not attachment.get("url"):
                continue
            parsed = urllib.parse.urlsplit(str(attachment["url"]))
            if parsed.scheme != "https" or parsed.hostname not in {"cdn.discordapp.com", "media.discordapp.net"}:
                continue
            try:
                with urllib.request.urlopen(str(attachment["url"]), timeout=15) as image_response:
                    data = image_response.read(25 * 1024 * 1024 + 1)
                if len(data) <= 25 * 1024 * 1024 and hashlib.sha256(data).hexdigest() == expected_image_sha256:
                    image_hash_match = True
                    break
            except (OSError, ValueError):
                continue
        media_verified = image_hash_match
    verified = bool(exact_identity and text_verified and canonical_verified and media_verified)
    public_url = (
        f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        if guild_id and channel_id
        else None
    )
    if public_url is None and channel_id == "1519311669216673802":
        from live_contentops.published_content_v1 import DISCORD_LINK_PREFIX
        public_url = DISCORD_LINK_PREFIX + str(message_id)
    return {
        "status": "SUCCESS" if verified else "FAILED_DISCORD_STRICT_READBACK",
        "verified": verified,
        "write_exists": exact_identity,
        "message_id": observed_id or None,
        "public_url": public_url,
        "body_text_visible": text_verified,
        "substack_url_visible": canonical_verified,
        "meaningful_media_visible": media_verified,
        "attached_article_visual": bool(attachments),
        "image_sha256_match": image_hash_match,
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
    embeds: list[dict[str, Any]] | None = None,
    image_path: str | None = None,
) -> dict[str, Any]:
    """Edits a previously published Discord webhook message via PATCH."""
    target_webhook = webhook_url or _get_default_webhook_url()

    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "platform": "discord",
            "action": "edit",
            "payload_redacted": {
                "message_id": message_id,
                "new_message": new_message,
                **({"embeds": embeds} if embeds is not None else {}),
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
    if embeds is not None:
        payload["embeds"] = embeds
    content_type = "application/json"
    data = json.dumps(payload).encode("utf-8")
    if image_path:
        from PIL import Image
        path = Path(image_path)
        try:
            with Image.open(path) as image:
                image.verify()
                image_format = image.format
            mime, extension = {"PNG": ("image/png", "png"), "JPEG": ("image/jpeg", "jpg")}[image_format]
            image_bytes = path.read_bytes()
        except (OSError, ValueError, KeyError):
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                "reason_code": "DISCORD_IMAGE_FILE_INVALID", "platform": "discord"}
        filename = "article-image." + extension
        payload["attachments"] = [{"id": 0, "filename": filename}]
        boundary = "cc-discord-" + uuid.uuid4().hex
        data = (f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
            'Content-Type: application/json\r\n\r\n').encode() + json.dumps(payload).encode()
        data += (f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="files[0]"; '
            f'filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n').encode()
        data += image_bytes + f"\r\n--{boundary}--\r\n".encode()
        content_type = "multipart/form-data; boundary=" + boundary
    req = urllib.request.Request(edit_url, data=data, method="PATCH")
    req.add_header("Content-Type", content_type)
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
