from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from urllib.parse import parse_qs, urlparse

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


def mobile_input(setup, *, age=2):
    store, binding, root = setup
    packs.save_json(binding, {"bound_chat_id": 123456789, "start_nonce": None})
    key = "public-yen-fact"
    store.create_work_item(story_id=key, work_item_id=key, title="Public yen facts", target_surface="PRIVATE")
    store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:plan-status-post",
        payload=json.dumps({"kind": "setup", "symbol": "USDJPY", "at_utc": (NOW - timedelta(hours=1)).isoformat(),
            "text": "CFTC data for 3 Nov show speculators net long 102,321 yen contracts, 27% of open interest."}))
    feed = root / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{"handle": "FirstSquawk",
        "text": "BOJ AND JAPAN DISCUSS THE YEN", "url": "https://x.com/FirstSquawk/status/123",
        "tweet_id": "123", "posted_utc": (NOW - timedelta(minutes=age)).isoformat(), "metrics": {"replies": 3}}]})
    return feed


def authored(request):
    return {"request_sha256": request["request_sha256"], "editorial_call": {"configured_model": "test-model"},
        "items": [{"post_id": "123", "source_id": request["sources"][0]["source_id"],
            "draft_text": "CFTC data for 3 Nov show speculators net long 102,321 yen contracts, 27% of open interest. That makes a stronger yen vulnerable to long liquidation when rate support fades.",
            "fact_text": "102,321 yen contracts", "source_name": "CFTC", "date_text": "3 Nov",
            "addition": "long liquidation", "point": "Crowded positioning limits the headline's implication", "reply_shape": "positioning"}],
        "omissions": []}


def draft_fixture(request_path, *, output_dir):
    path = output_dir / "response.json"
    packs.save_json(path, authored(packs.read_json(request_path)))
    return path


def test_minute_consumer_uses_held_fact_delivers_exact_intent_and_parks_tabs_without_public_writes(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    tabs_control = binding.parent / "x_reply_tabs.json"
    packs.save_json(tabs_control, {"enabled": True})
    bot = FakeBot()
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=draft_fixture, now=NOW)
    assert result["status"] == "DELIVERED", result
    messages = [p for m, p in bot.calls if m == "sendMessage"]
    assert len(messages) == 1 and messages[0]["chat_id"] == 123456789
    message = messages[0]
    assert "<code>CFTC" in message["text"] and "Good until" in message["text"]
    assert "Fact: 102,321 yen contracts (CFTC, 3 Nov)" in message["text"]
    buttons = message["reply_markup"]["inline_keyboard"][0]
    intent = urlparse(buttons[0]["url"])
    assert intent.netloc == "x.com" and intent.path == "/intent/tweet"
    assert parse_qs(intent.query)["in_reply_to"] == ["123"]
    assert parse_qs(intent.query)["text"][0] == authored({"request_sha256": "", "sources": [{"source_id": ""}]})["items"][0]["draft_text"]
    assert buttons[1]["callback_data"] == "skip:xrb-123"
    assert packs.read_json(tabs_control)["enabled"] is False
    assert "Restore:" in (binding.parent / "PARKED.md").read_text(encoding="utf-8")
    proof = result["delivery"]["delivered"][0]
    assert proof["post_to_delivery_minutes"] == 2 and proof["post_to_draft_minutes"] == 2
    assert not store.list_platform_dispatches() and not store.list_outbox_messages(destination="x")
    assert "123456789" not in json.dumps(result)
    assert "123456789" not in json.dumps(store.list_outbox_messages())
    again = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                bot=bot, drafter=draft_fixture, now=NOW)
    assert again["status"] == "NO_NEW_ELIGIBLE_TARGETS"
    assert len([c for c in bot.calls if c[0] == "sendMessage"]) == 1


def test_non_private_destination_is_refused_before_any_draft_send(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    bot = FakeBot(chat_type="channel")
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=draft_fixture, now=NOW)
    assert result["status"] == "REPLY_BOT_FAILED" and result["cause"] == "NON_PRIVATE_OR_WRONG_CHAT_REFUSED"
    assert not any(m.startswith("send") for m, _ in bot.calls)


@pytest.mark.parametrize("change,cause", [
    (lambda d: d.update(draft_text=d["draft_text"] + " Our view."), "TWO_SENTENCES"),
    (lambda d: d.update(draft_text=d["draft_text"].replace("That makes", "Our view makes")), "VOICE"),
    (lambda d: d.update(draft_text=d["draft_text"].replace("That makes", "Capital Chronicle makes")), "VOICE"),
    (lambda d: d.update(draft_text=d["draft_text"].replace("102,321", "102,322")), "EXACT_SOURCE_FACT"),
    (lambda d: d.update(draft_text=d["draft_text"].replace("27%", "28%")), "UNBOUND_OR_CHANGED_NUMBER"),
    (lambda d: d.update(date_text="4 Nov"), "BOUND_DATE_AND_SOURCE"),
    (lambda d: d.update(source_name="Reuters"), "BOUND_DATE_AND_SOURCE"),
    (lambda d: d.update(reply_shape="generic_form"), "SHAPE"),
])
def test_mobile_voice_and_all_numbers_remain_source_bound(setup, change, cause):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    value = authored(packs.read_json(ready["request_path"]))
    change(value["items"][0])
    response = root / "response.json"
    packs.save_json(response, value)
    built = packs.build(store, request_path=ready["request_path"], response_path=response, feed_path=feed, output_root=root, now=NOW)
    assert built["item_count"] == 0 and cause in built["none_reason"]


def test_code_filter_uses_real_reply_counts_and_never_turns_unknown_into_zero(setup):
    store, _, root = setup
    feed_path = mobile_input(setup)
    feed = packs.read_json(feed_path)
    original = feed["rows"][0]
    rows = []
    for post_id, age, count in [("1", 59, 2), ("2", 60, 0), ("3", 1, 20), ("4", 1, None)]:
        row = dict(original, tweet_id=post_id, url="https://x.com/FirstSquawk/status/" + post_id,
                   posted_utc=(NOW - timedelta(minutes=age)).isoformat(), metrics={"replies": count})
        rows.append(row)
    selected, causes = packs.select_posts({"rows": rows}, handles={"firstsquawk"}, now=NOW, mobile=True)
    assert {p["post_id"] for p in selected} == {"1", "4"}
    assert next(p for p in selected if p["post_id"] == "4")["reply_count"] is None
    assert causes["POST_ALREADY_HAS_20_REPLIES"] == 1 and causes["POST_OUTSIDE_60_MINUTE_WINDOW"] == 1


def test_uncertain_telegram_send_is_never_repeated_and_does_not_park_tabs(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    class Uncertain(FakeBot):
        def call(self, method, payload=None):
            if method == "sendMessage":
                self.calls.append((method, deepcopy(payload)))
                raise botlane.BotError("TELEGRAM_TRANSPORT_UNCERTAIN")
            return super().call(method, payload)
    bot = Uncertain()
    packs.save_json(binding.parent / "x_reply_tabs.json", {"enabled": True})
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=draft_fixture, now=NOW)
    assert not result["delivery"]["delivered"]
    assert store.get_outbox_message("xrb-123")["status"] == "UNKNOWN_WRITE"
    assert packs.read_json(binding.parent / "x_reply_tabs.json")["enabled"] is True
    botlane.deliver_pack(store, result["pack"]["store_message_id"], binding_path=binding, bot=bot, now=NOW)
    assert len([c for c in bot.calls if c[0] == "sendMessage"]) == 1


def test_manual_reply_readback_keeps_both_delays_and_feeds_14_day_cohort(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                        bot=FakeBot(), drafter=draft_fixture, now=NOW)
    reply_path = root / "reply.json"
    posted = NOW + timedelta(minutes=3)
    packs.save_json(reply_path, {"rows": [{"tweet_id": "999", "handle": "Capitalnicle",
        "url": "https://x.com/Capitalnicle/status/999", "in_reply_to_status_id": "123",
        "posted_utc": posted.isoformat(), "text": "Jim edited this reply.",
        "metrics_observed_at_utc": (posted + timedelta(hours=24)).isoformat(),
        "metrics": {"views": 120, "likes": 2, "profile_visits": 1}}]})
    observed = packs.observe_manual_replies(store, reply_feed_path=reply_path, now=posted + timedelta(hours=24))
    assert len(observed["observed"]) == 1
    value = json.loads(store.list_outbox_messages(destination=packs.READBACK_DESTINATION)[0]["payload"])
    assert value["post_to_draft_minutes"] == 2 and value["post_to_reply_minutes"] == 5
    cohort = packs.report_manual_replies(store, now=posted + timedelta(hours=24))["cohorts"][0]
    assert cohort["draft_delay"] == "within_5m" and cohort["views"] == 120 and cohort["profile_visits"] == 1


def test_ranker_uses_agy_but_only_stronger_writer_authors_source_bound_reply(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    calls = []
    def rank(prompt, **kwargs):
        calls.append("rank")
        assert "reply_count" in prompt and "never draft" in prompt
        return {"ranking": [{"post_id": "123", "quality_score": 92, "reason": "missing crowd positioning"}]}, {"configured_model": "AGY"}
    def write(prompt, **kwargs):
        calls.append("writer")
        assert kwargs["writer"] and "102,321" in prompt
        return authored(packs.read_json(ready["request_path"])), {"configured_model": "gpt-6.1-sol", "configured_effort": "max", "configuration_status": "CONFIGURED_NOT_OBSERVED"}
    path = botlane.rank_and_draft(ready["request_path"], output_dir=root / "native", ranker=rank, writer=write)
    value = packs.read_json(path)
    assert calls == ["rank", "writer"] and value["quality_score"] == 92
    assert value["editorial_call"]["writer"]["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    built = packs.build(store, request_path=ready["request_path"], response_path=path, feed_path=feed, output_root=root, now=NOW)
    assert built["item_count"] == 1


def test_ranker_never_pads_low_quality_candidates_or_calls_writer(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    def rank(*a, **k):
        return {"ranking": [{"post_id": "123", "quality_score": 79}]}, {}
    def write(*a, **k):
        pytest.fail("A weak opportunity is not padded into a draft")
    path = botlane.rank_and_draft(ready["request_path"], output_dir=root / "native", ranker=rank, writer=write)
    assert not packs.read_json(path)["items"]


def test_expired_pack_does_not_send_and_daily_five_limit_is_shared_by_every_tick(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    bot = FakeBot()
    first = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                bot=bot, drafter=draft_fixture, now=NOW)
    for n in range(4):
        botlane.record(store, botlane.DELIVERY, {"delivery_day": "2026-11-11", "post_id": str(n)}, key="limit-" + str(n))
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=draft_fixture, now=NOW)
    assert result["status"] == "FIVE_QUALITY_DRAFTS_TODAY"
    assert len([c for c in bot.calls if c[0] == "sendMessage"]) == 1
    pack = json.loads(store.get_outbox_message(first["pack"]["store_message_id"])["payload"])
    pack["items"][0]["post_id"] = "456"
    key = "expired-pack"
    store.create_work_item(story_id=key, title=key, work_item_id=key, target_surface="PRIVATE")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=packs.PACK_DESTINATION, payload=json.dumps(pack))
    # A different day avoids the day's cap and exercises the actual expiry refusal.
    expired = botlane.deliver_pack(store, key, binding_path=binding, bot=bot, now=NOW + timedelta(days=1))
    assert expired["causes"]["TARGET_OVER_60_MINUTES"] == 1


def test_source_bound_chart_is_sent_before_draft_and_original_bytes_are_preserved(setup):
    from hashlib import sha256
    from PIL import Image
    store, binding, root = setup
    feed = mobile_input(setup)
    chart = root / "fact-chart.png"
    Image.new("RGB", (400, 300), "white").save(chart)
    # This optional chart is bound to a public Main field's existing immutable source message.
    image = {"path": str(chart), "sha256": sha256(chart.read_bytes()).hexdigest(), "kind": "chart", "rights_class": "CC_OWN_ANALYSIS"}
    key = "public-chart-source"
    store.create_work_item(story_id=key, title=key, target_surface="PRIVATE", work_item_id=key)
    store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:cc-report-feed",
        payload=json.dumps({"desk_record_sources": [{"title": "CFTC yen positioning", "known_at_utc": (NOW - timedelta(hours=1)).isoformat(),
            "binding": {"fixture": False, "sources": [{"attribution": "CFTC"}], "fields": [{"citation": "CFTC/yen", "field_path": "/yen",
                "value": 102321, "display": "CFTC data for 3 Nov show speculators net long 102,321 yen contracts, 27% of open interest.",
                "rights_class": "CC_OWN_ANALYSIS", "image": image}]}}]}))
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    value = authored(packs.read_json(ready["request_path"]))
    value["items"][0]["include_image"] = True
    response_path = root / "response.json"
    packs.save_json(response_path, value)
    result = packs.build(store, request_path=ready["request_path"], response_path=response_path, feed_path=feed, output_root=root, now=NOW)
    pack = packs.read_json(result["pack_path"])
    assert pack["items"][0]["image"] == image
    class WithPhoto(FakeBot):
        def send_photo(self, chat_id, path):
            assert chat_id == 123456789 and sha256(path.read_bytes()).hexdigest() == image["sha256"]
            self.calls.append(("sendPhoto", str(path)))
            return {"message_id": 41}
    bot = WithPhoto()
    delivered = botlane.deliver_pack(store, result["store_message_id"], binding_path=binding, bot=bot, now=NOW)
    assert delivered["status"] == "DELIVERED"
    assert [m for m, _ in bot.calls if m.startswith("send")] == ["sendPhoto", "sendMessage"]
    assert sha256(chart.read_bytes()).hexdigest() == image["sha256"]
