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
BOT_USER_AGENT = "DiscordBot (https://capitalchronicle.substack.com, 1.0)"


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
    thread_parent_id: str | None = None,
    thread_name: str | None = None,
    reply_to_message_id: str | None = None,
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

    bot_token = None
    if thread_parent_id:
        bot_token = read_secret("DISCORD_BOT_TOKEN")
        if not bot_token:
            return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True,
                    "reason_code": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE", "platform": "discord"}
        thread = _ensure_call_thread(target_webhook, str(thread_parent_id), thread_name, bot_token)
        if thread.get("status") != "READY":
            return thread
        post_url = f"https://discord.com/api/v10/channels/{thread_parent_id}/messages"

    payload: dict[str, Any] = {"content": message}
    if thread_parent_id:
        payload["allowed_mentions"] = {"parse": []}
        # A thread's starter is in its parent channel. Sending into the thread
        # already replies under it; a message_reference to it is invalid there.
        if reply_to_message_id and str(reply_to_message_id) != str(thread_parent_id):
            payload["message_reference"] = {"message_id": str(reply_to_message_id),
                                             "channel_id": str(thread_parent_id), "fail_if_not_exists": True}
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
    if bot_token:
        req.add_header("Authorization", "Bot " + bot_token)
    # Discord's HTTP API requires the bot's client-library identity and version.
    req.add_header("User-Agent", BOT_USER_AGENT if bot_token else
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

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


def _ensure_call_thread(webhook, parent_id, name, token):
    """A Discord thread uses its starter message id. Read it before creating it.

    The webhook identifies the approved announcement channel. Bot access is
    needed only for the official create-thread endpoint and replies in it.
    A lost thread-create response is recovered by its deterministic channel id;
    no call message has been sent by this helper.
    """
    def request(url, data=None, method=None):
        req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                     method=method or ("POST" if data else "GET"))
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CapitalChronicleContentOps/1.0" if url.startswith(webhook) else BOT_USER_AGENT)
        if not url.startswith(webhook):
            req.add_header("Authorization", "Bot " + token)
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    try:
        metadata = request(webhook.split("?", 1)[0])
        channel = str(metadata.get("channel_id") or "")
        from .destination_transport_registry_v1 import registration_for_destination
        expected = registration_for_destination("discord").expected_stable_id
        if channel != expected or not parent_id.isdigit():
            return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True,
                    "reason_code": "DISCORD_CALL_THREAD_WRONG_CHANNEL", "platform": "discord"}
        try:
            thread = request(f"https://discord.com/api/v10/channels/{parent_id}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            thread = request(f"https://discord.com/api/v10/channels/{channel}/messages/{parent_id}/threads",
                             {"name": str(name or "Capital Chronicle calls")[:100], "auto_archive_duration": 1440})
        if (str(thread.get("id")) != parent_id or str(thread.get("parent_id")) != channel
                or thread.get("type") not in {10, 11, 12}):
            return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True,
                    "reason_code": "DISCORD_CALL_THREAD_IDENTITY_MISMATCH", "platform": "discord"}
        if (thread.get("thread_metadata") or {}).get("archived"):
            thread = request(f"https://discord.com/api/v10/channels/{parent_id}", {"archived": False}, "PATCH")
            if (thread.get("thread_metadata") or {}).get("archived"):
                return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True,
                        "reason_code": "DISCORD_CALL_THREAD_ARCHIVED", "platform": "discord"}
        return {"status": "READY", "id": parent_id}
    except Exception as exc:
        return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True, "platform": "discord",
                "reason_code": "DISCORD_CALL_THREAD_UNAVAILABLE", "safe_error_classification": type(exc).__name__}


def _reply_parent_matches(payload, thread_id, expected_parent_id):
    parent = str((payload.get("message_reference") or {}).get("message_id") or "")
    return (not expected_parent_id or parent == str(expected_parent_id)
            or (str(thread_id) == str(expected_parent_id) and not parent
                and str(payload.get("channel_id")) == str(thread_id)))


def readback_discord_post(
    *,
    message_id: str,
    expected_text: str,
    canonical_url: str,
    webhook_url: str | None = None,
    expected_image_sha256: str | None = None,
    thread_id: str | None = None,
    expected_parent_id: str | None = None,
    require_media: bool = True,
) -> dict[str, Any]:
    """Read one exact webhook message without exposing the webhook credential."""
    target_webhook = webhook_url or _get_default_webhook_url()
    if not target_webhook or not str(message_id or "").isdigit():
        return {"status": "READBACK_UNAVAILABLE", "verified": False}
    url = f"{target_webhook.rstrip('/')}/messages/{message_id}"
    token = read_secret("DISCORD_BOT_TOKEN") if thread_id else None
    if thread_id:
        if not token or not str(thread_id).isdigit():
            return {"status": "READBACK_UNAVAILABLE", "verified": False}
        url = f"https://discord.com/api/v10/channels/{thread_id}/messages/{message_id}"
    request = urllib.request.Request(url, method="GET")
    if token:
        request.add_header("Authorization", "Bot " + token)
    request.add_header("User-Agent", BOT_USER_AGENT if token else "CapitalChronicleContentOps/1.0")
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
    if thread_id and not guild_id:
        # Discord's GET-message response normally omits guild_id. Read the
        # registered thread metadata so its public permalink stays verifiable.
        metadata_request = urllib.request.Request(
            "https://discord.com/api/v10/channels/" + str(thread_id), method="GET")
        metadata_request.add_header("Authorization", "Bot " + token)
        metadata_request.add_header("User-Agent", BOT_USER_AGENT)
        try:
            with urllib.request.urlopen(metadata_request, timeout=15) as response:
                thread = json.loads(response.read().decode("utf-8"))
            from .destination_transport_registry_v1 import registration_for_destination
            if (str(thread.get("id")) != str(thread_id)
                    or str(thread.get("parent_id")) != registration_for_destination("discord").expected_stable_id
                    or thread.get("type") not in {10, 11, 12}
                    or not str(thread.get("guild_id") or "").isdigit()):
                return {"status": "READBACK_UNAVAILABLE", "verified": False, "write_exists": True}
            guild_id = str(thread["guild_id"])
        except (OSError, ValueError, KeyError, TypeError):
            return {"status": "READBACK_UNAVAILABLE", "verified": False, "write_exists": True}
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
    thread_verified = not thread_id or channel_id == str(thread_id)
    parent_verified = _reply_parent_matches(payload, thread_id, expected_parent_id)
    verified = bool(exact_identity and text_verified and canonical_verified
                    and (media_verified or (not require_media and not expected_image_sha256))
                    and thread_verified and parent_verified)
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
        "thread_verified": thread_verified, "reply_parent_verified": parent_verified,
    }


def find_discord_thread_post(*, thread_id, expected_text, canonical_url,
                            expected_parent_id=None, expected_image_sha256=None,
                            require_media=True):
    """Recover a lost bot-message id by reading its exact registered thread.

    A full 100-message page is incomplete evidence of absence. A wrong thread,
    foreign author, changed body or multiple exact matches stays uncertain.
    This operation sends only GET requests and never creates/unarchives a thread.
    """
    unavailable = {"status": "READBACK_UNAVAILABLE", "verified": False, "write_absent": False}
    token = read_secret("DISCORD_BOT_TOKEN")
    if not token or not str(thread_id or "").isdigit() or not expected_text:
        return unavailable

    def get(path):
        request = urllib.request.Request("https://discord.com/api/v10/" + path, method="GET")
        request.add_header("Authorization", "Bot " + token)
        request.add_header("User-Agent", BOT_USER_AGENT)
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        from .destination_transport_registry_v1 import registration_for_destination
        channel = get("channels/" + str(thread_id))
        if (str(channel.get("id")) != str(thread_id)
                or str(channel.get("parent_id")) != registration_for_destination("discord").expected_stable_id
                or channel.get("type") not in {10, 11, 12}):
            return {**unavailable, "cause": "DISCORD_CALL_THREAD_IDENTITY_MISMATCH"}
        author = get("users/@me")
        if not author.get("bot") or not str(author.get("id") or "").isdigit():
            return {**unavailable, "cause": "DISCORD_BOT_IDENTITY_UNAVAILABLE"}
        messages = get("channels/" + str(thread_id) + "/messages?limit=100")
        if (not isinstance(messages, list)
                or any(not isinstance(m, dict) or str(m.get("channel_id")) != str(thread_id)
                       or not str(m.get("id") or "").isdigit() for m in messages)):
            return {**unavailable, "cause": "DISCORD_THREAD_HISTORY_IDENTITY_MISMATCH"}
        matches, uncertain = [], False
        for message in messages:
            content = str(message.get("content") or "")
            own = str((message.get("author") or {}).get("id")) == str(author["id"])
            if content == expected_text:
                if own and _reply_parent_matches(message, thread_id, expected_parent_id):
                    matches.append(message)
                else:
                    uncertain = True
            elif own and ((canonical_url and canonical_url in content)
                          or content.startswith(expected_text.splitlines()[0])):
                uncertain = True
        if uncertain or len(matches) > 1:
            return {**unavailable, "cause": "DISCORD_THREAD_MATCH_AMBIGUOUS", "messages_read": len(messages)}
        if not matches:
            complete = len(messages) < 100
            return {"status": "NOT_FOUND" if complete else "READBACK_UNAVAILABLE", "verified": False,
                    "write_absent": complete, "messages_read": len(messages), "thread_id": str(thread_id),
                    "absence_basis": "COMPLETE_REGISTERED_DISCORD_THREAD_HISTORY" if complete else None}
        result = readback_discord_post(message_id=matches[0]["id"], expected_text=expected_text,
            canonical_url=canonical_url or "", thread_id=str(thread_id), expected_parent_id=expected_parent_id,
            expected_image_sha256=expected_image_sha256, require_media=require_media)
        return {**result, "id": matches[0]["id"], "messages_read": len(messages)}
    except (OSError, ValueError, KeyError, TypeError):
        return unavailable


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
