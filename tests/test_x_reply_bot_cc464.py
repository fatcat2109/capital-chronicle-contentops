from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from live_contentops import x_reply_bot_v1 as botlane
from live_contentops import x_reply_pack_v1 as packs
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = datetime(2026, 11, 11, 16, tzinfo=timezone.utc)


class FakeBot:
    private_chat = botlane.TelegramBot.private_chat

    def __init__(self, updates=(), chat_type="private"):
        self.updates, self.chat_type, self.calls = list(updates), chat_type, []

    def call(self, method, payload=None):
        self.calls.append((method, deepcopy(payload)))
        if method == "getMe":
            return {"username": botlane.BOT_NAME}
        if method == "getWebhookInfo":
            return {"url": ""}
        if method == "getUpdates":
            return self.updates
        if method == "getChat":
            return {"id": payload["chat_id"], "type": self.chat_type}
        return {"message_id": 42, "date": int(NOW.timestamp())}


@pytest.fixture
def setup(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    binding = tmp_path / "control/x_reply_bot_binding.json"
    packs.save_json(binding, {"start_nonce": "test-once", "bound_chat_id": None})
    return store, binding, tmp_path


def start(chat_type="private", chat_id=123456789):
    return {"update_id": 7, "message": {"chat": {"type": chat_type, "id": chat_id},
        "from": {"id": chat_id}, "text": "/start test-once"}}


def test_start_binds_once_only_private_and_redacts_every_return_and_store_row(setup):
    store, binding, _ = setup
    bot = FakeBot([start()])
    result = botlane.process_updates(store, binding_path=binding, bot=bot, now=NOW)
    saved = packs.read_json(binding)
    assert result["status"] == "BOUND" and saved["bound_chat_id"] == 123456789
    assert saved["start_nonce"] is None and saved["update_offset"] == 8
    assert saved["acknowledgement"] == "CONFIRMED"
    assert "123456789" not in json.dumps(result) and "test-once" not in json.dumps(result)
    assert not store.list_outbox_messages()
    bot.updates = [start(chat_id=987654321)]
    botlane.process_updates(store, binding_path=binding, bot=bot, now=NOW)
    assert packs.read_json(binding)["bound_chat_id"] == 123456789
    assert len([c for c in bot.calls if c[0] == "sendMessage"]) == 1


@pytest.mark.parametrize("chat_type", ["group", "supergroup", "channel"])
def test_non_private_start_never_sends_even_with_correct_nonce(setup, chat_type):
    store, binding, _ = setup
    bot = FakeBot([start(chat_type)])
    result = botlane.process_updates(store, binding_path=binding, bot=bot, now=NOW)
    assert result["status"] == "PENDING_JIM_BOT_START"
    assert not packs.read_json(binding)["bound_chat_id"]
    assert not any(method == "sendMessage" for method, _ in bot.calls)


@pytest.mark.parametrize("chat_id,chat_type", [("@CapitalChronicle", "channel"), (-1001234, "channel"),
                                                        (123456789, "group")])
def test_private_destination_refuses_channel_ids_and_changed_chat_type(chat_id, chat_type):
    bot = FakeBot(chat_type=chat_type)
    with pytest.raises(botlane.BotError):
        botlane.TelegramBot.private_chat(bot, {"bound_chat_id": chat_id})
    assert not any(method.startswith("send") for method, _ in bot.calls)


def test_transport_errors_do_not_serialize_token_url_or_chat(monkeypatch):
    monkeypatch.setattr(botlane, "read_secret", lambda _: "NEVER_PRINT_THIS_TOKEN")
    def fail(*a, **k):
        raise ValueError("NEVER_PRINT_THIS_TOKEN chat 123456789")
    with pytest.raises(botlane.BotError, match="TRANSPORT_UNCERTAIN") as caught:
        botlane.TelegramBot(opener=fail).call("sendMessage", {"chat_id": 123456789})
    assert "NEVER_PRINT" not in str(caught.value) and "123456789" not in str(caught.value)


def test_skip_only_accepts_bound_private_sender(setup):
    store, binding, _ = setup
    packs.save_json(binding, {"bound_chat_id": 123456789, "start_nonce": None})
    key = "xrb-123"
    botlane.record(store, botlane.DELIVERY, {"post_id": "123"}, key=key, status="DELIVERED")
    callback = {"update_id": 9, "callback_query": {"id": "c1", "data": "skip:" + key,
        "from": {"id": 123456789}, "message": {"chat": {"type": "private", "id": 123456789}}}}
    wrong = deepcopy(callback)
    wrong["callback_query"]["message"]["chat"]["type"] = "group"
    result = botlane.process_updates(store, binding_path=binding, bot=FakeBot([wrong]), now=NOW)
    assert result["skipped"] == 0 and store.get_outbox_message(key)["status"] == "DELIVERED"
    result = botlane.process_updates(store, binding_path=binding, bot=FakeBot([callback]), now=NOW)
    assert result["skipped"] == 1 and store.get_outbox_message(key)["status"] == "SKIPPED_BY_JIM"
    assert "123456789" not in json.dumps(store.list_outbox_messages())
