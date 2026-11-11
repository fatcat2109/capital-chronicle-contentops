"""CC-464: private Telegram delivery of sourced X drafts; Jim alone sends on X.

Chat identity and the one-time nonce stay in the existing runtime binding file.
Delivery and Skip state reuse the operational store's internal outbox. No public
Telegram destination, X write, webhook, scheduler or secondary store is used.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
import hmac
from html import escape
import json
from pathlib import Path
import urllib.error
import urllib.request
from uuid import uuid4

from live_contentops import x_reply_pack_v1 as packs
from live_contentops.secret_store_v1 import read_secret

BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\control\x_reply_bot_binding.json")
BOT_NAME = "CapitalChroniclePublisherBot"
DELIVERY = "internal:x-reply-bot-delivery"
EVENTS = "internal:x-reply-bot-event"
RUNS = "internal:x-reply-bot-run"


class BotError(RuntimeError):
    """A deliberately redacted failure: never include request/response objects."""


class TelegramBot:
    def __init__(self, *, opener=None):
        self.opener = opener or urllib.request.urlopen

    def call(self, method, payload=None):
        token = read_secret("TELEGRAM_BOT_TOKEN")
        if not token:
            raise BotError("TELEGRAM_BOT_TOKEN_UNAVAILABLE")
        request = urllib.request.Request(
            "https://api.telegram.org/bot" + token + "/" + method,
            data=json.dumps(payload or {}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with self.opener(request, timeout=8) as response:
                value = json.load(response)
        except urllib.error.HTTPError as exc:
            raise BotError("TELEGRAM_HTTP_" + str(exc.code)) from None
        except Exception:
            raise BotError("TELEGRAM_TRANSPORT_UNCERTAIN") from None
        if not value.get("ok"):
            raise BotError("TELEGRAM_API_" + str(value.get("error_code", "ERROR")))
        return value.get("result")

    def private_chat(self, binding):
        chat_id = binding.get("bound_chat_id")
        if not str(chat_id or "").isdigit() or int(chat_id) <= 0:
            raise BotError("JIM_PRIVATE_CHAT_NOT_BOUND")
        chat = self.call("getChat", {"chat_id": chat_id})
        if chat.get("type") != "private" or str(chat.get("id")) != str(chat_id):
            raise BotError("NON_PRIVATE_OR_WRONG_CHAT_REFUSED")
        return chat_id


def record(store, destination, value, *, key=None, status=None):
    key = key or "x-reply-bot-" + packs.digest(value)
    store.create_work_item(story_id="x-reply-bot", work_item_id="x-reply-bot",
                           title="Jim's private X reply drafts", target_surface="PRIVATE")
    return store.register_outbox_message(message_id=key, work_item_id="x-reply-bot",
        destination=destination, payload=json.dumps(value, sort_keys=True),
        status=status or value.get("status", "SAVED"))


def process_updates(store, *, binding_path=BINDING, bot=None, now=None):
    """One getUpdates call. Only an exact private /start binds; no chat ids escape."""
    bot, now = bot or TelegramBot(), now or packs.utcnow()
    binding = packs.read_json(binding_path)
    identity = bot.call("getMe")
    if identity.get("username", "").casefold() != BOT_NAME.casefold():
        raise BotError("TELEGRAM_BOT_IDENTITY_MISMATCH")
    if bot.call("getWebhookInfo").get("url"):
        raise BotError("TELEGRAM_WEBHOOK_ALREADY_SET")
    updates = bot.call("getUpdates", {"offset": binding.get("update_offset", 0), "timeout": 0,
        "limit": 100, "allowed_updates": ["message", "callback_query"]})
    causes, skipped, bound_now = Counter(), 0, False
    for update in updates:
        binding["update_offset"] = max(binding.get("update_offset", 0), update["update_id"] + 1)
        message = update.get("message", {})
        chat = message.get("chat", {})
        nonce = binding.get("start_nonce")
        text = message.get("text", "").split()
        if (not binding.get("bound_chat_id") and nonce and len(text) == 2
                and text[0].casefold() in {"/start", "/start@" + BOT_NAME.casefold()}
                and hmac.compare_digest(text[1], nonce)):
            if (chat.get("type") != "private" or int(chat.get("id", 0)) <= 0
                    or chat.get("id") != message.get("from", {}).get("id")):
                causes["START_REQUIRES_PRIVATE_SENDER_CHAT"] += 1
                continue
            binding.update(bound_chat_id=chat["id"], bound_at_utc=now.isoformat(),
                           start_nonce=None, acknowledgement="PENDING")
            packs.save_json(binding_path, binding)
            bound_now = True
        callback = update.get("callback_query", {})
        if callback:
            cchat = callback.get("message", {}).get("chat", {})
            data = callback.get("data", "")
            if (not binding.get("bound_chat_id") or cchat.get("type") != "private"
                    or str(cchat.get("id")) != str(binding["bound_chat_id"])
                    or str(callback.get("from", {}).get("id")) != str(binding["bound_chat_id"])):
                causes["CALLBACK_OUTSIDE_BOUND_PRIVATE_CHAT"] += 1
                continue
            key = data.removeprefix("skip:")
            delivery = store.get_outbox_message(key) if data.startswith("skip:") else None
            if not delivery or delivery["destination"] != DELIVERY:
                causes["SKIP_DELIVERY_NOT_FOUND"] += 1
                continue
            store.set_outbox_status(key, "SKIPPED_BY_JIM")
            record(store, EVENTS, {"kind": "skip", "delivery_id": key, "at_utc": now.isoformat()},
                   key="x-reply-skip-" + str(update["update_id"]))
            skipped += 1
            bot.call("answerCallbackQuery", {"callback_query_id": callback["id"], "text": "Skipped"})
    packs.save_json(binding_path, binding)
    if bound_now and binding.get("acknowledgement") == "PENDING":
        chat_id = bot.private_chat(binding)
        # Save before the send; an interrupted acknowledgement is never retried blindly.
        binding["acknowledgement"] = "SENDING"
        packs.save_json(binding_path, binding)
        try:
            bot.call("sendMessage", {"chat_id": chat_id, "text":
                "Connected. Fresh X reply drafts will arrive here. Open reply on X fills the text; only you press Reply. Skip dismisses a draft."})
            binding["acknowledgement"] = "CONFIRMED"
        except BotError:
            binding["acknowledgement"] = "UNKNOWN_WRITE"
        packs.save_json(binding_path, binding)
    return {"status": "BOUND" if binding.get("bound_chat_id") else "PENDING_JIM_BOT_START",
            "bound_now": bound_now, "updates_processed": len(updates), "skipped": skipped,
            "causes": dict(causes), "public_submit_actions": 0}


def quoted_post(text):
    """Never cut a sentence or append an ellipsis to the quoted target."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    selected = ""
    for sentence in sentences:
        if len((selected + " " + sentence).strip()) > 200:
            break
        selected = (selected + " " + sentence).strip()
    return selected or "[Long post: open the original below.]"


def message_for(item, *, number, now):
    age = max(0, int((now - packs.clock(item["post_time_utc"])).total_seconds() / 60))
    expiry = packs.clock(item["stale_at_utc"]).astimezone(packs.LOCAL)
    count = item.get("reply_count")
    replies = str(count) + " replies" if count is not None else "reply count unavailable"
    return (f"REPLY {number} of 5 today · @{escape(item['author_handle'])} · posted {age} min ago · {replies}\n"
        f"“{escape(quoted_post(item['post_text']))}”\n{escape(item['post_url'])}\n\n"
        f"<code>{escape(item['draft_text'])}</code>\n\n"
        f"Fact: {escape(item['fact_text'])} ({escape(item['fact_source'])})\n"
        f"Good until {expiry:%H:%M} (GMT+7) · {len(item['draft_text'])} of 240 characters")
