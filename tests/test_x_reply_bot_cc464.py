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
def setup(tmp_path, monkeypatch):
    from live_contentops import x_reply_base_rates_v1
    monkeypatch.setattr(x_reply_base_rates_v1, "collect", lambda *a, **kw: ([], []))
    from live_contentops import x_reply_fact_sources_v1
    monkeypatch.setattr(x_reply_fact_sources_v1, "load", lambda **kwargs: ([], []))
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
            "text": "CFTC data for 9 Nov show speculators net long 102,321 yen contracts, 27% of open interest."}))
    feed = root / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{"handle": "FirstSquawk",
        "text": "CFTC YEN POSITIONING SHOWS CROWDED SPECULATIVE LONGS", "url": "https://x.com/FirstSquawk/status/123",
        "tweet_id": "123", "posted_utc": (NOW - timedelta(minutes=age)).isoformat(), "metrics": {"replies": 3}}]})
    return feed


def authored(request):
    return {"request_sha256": request["request_sha256"], "editorial_call": {"configured_model": "test-model"},
        "items": [{"post_id": "123", "source_id": request["sources"][0]["source_id"],
            "draft_text": "CFTC data for 9 Nov show speculators net long 102,321 yen contracts, 27% of open interest. That makes a stronger yen vulnerable to long liquidation when rate support fades.",
            "fact_text": "102,321 yen contracts", "source_name": "CFTC", "date_text": "9 Nov",
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
    assert "Fact: 102,321 yen contracts (CFTC, 9 Nov)" in message["text"]
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
    # A restart after the saved successful API return recovers parking without a second send.
    store.set_outbox_status("xrb-123", "SENDING")
    packs.save_json(tabs_control, {"enabled": True})
    botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                        bot=bot, drafter=draft_fixture, now=NOW)
    assert packs.read_json(tabs_control)["enabled"] is False
    assert store.get_outbox_message("xrb-123")["status"] == "DELIVERED"
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
    for post_id, age, count in [("1", 14, 2), ("2", 16, 0), ("3", 1, 20), ("4", 1, None)]:
        row = dict(original, tweet_id=post_id, url="https://x.com/FirstSquawk/status/" + post_id,
                   posted_utc=(NOW - timedelta(minutes=age)).isoformat(), metrics={"replies": count})
        rows.append(row)
    selected, causes = packs.select_posts({"rows": rows}, handles={"firstsquawk"}, now=NOW, mobile=True)
    assert {p["post_id"] for p in selected} == {"1", "4"}
    assert next(p for p in selected if p["post_id"] == "4")["reply_count"] is None
    assert causes["POST_ALREADY_HAS_20_REPLIES"] == 1 and causes["TARGET_OVER_15_MINUTES_AT_SEND"] == 1


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
    path = botlane.rank_and_draft(ready["request_path"], output_dir=root / "native", ranker=rank, writer=write, now=NOW)
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
    path = botlane.rank_and_draft(ready["request_path"], output_dir=root / "native", ranker=rank, writer=write, now=NOW)
    assert not packs.read_json(path)["items"]


def test_writer_receives_ranked_facts_with_full_context_and_no_unranked_hydration(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(ready["request_path"])
    source = request["sources"][0]
    for n in range(4):
        extra = {**source, "source_id": "extra-"+str(n), "excerpt": source["excerpt"]+" Context."*(n+1)}
        request["sources"].append(extra)
        request["candidates"][0]["usable_source_ids"].append(extra["source_id"])
    request["request_sha256"] = packs.digest({k:v for k,v in request.items() if k != "request_sha256"})
    packs.save_json(ready["request_path"], request)
    def rank(prompt, **kwargs):
        packet = json.loads(prompt.rsplit("\n", 1)[1])
        assert len(packet["candidates"][0]["available_facts"]) == 3
        assert not any("source_id" in f for f in packet["candidates"][0]["available_facts"])
        return {"ranking": [{"post_id": "123", "quality_score": 92}]}, {}
    def write(prompt, **kwargs):
        packet = json.loads(prompt.rsplit("\n", 1)[1])
        assert len(packet["sources"]) == 3 and len(packet["target"]["usable_source_ids"]) == 3
        assert {s["source_id"] for s in packet["sources"]} == {source["source_id"], "extra-0", "extra-1"}
        assert next(s for s in packet["sources"] if s["source_id"] == "extra-1")["excerpt"].endswith(" Context. Context.")
        return authored(request), {}
    botlane.rank_and_draft(ready["request_path"], output_dir=root/"native", ranker=rank, writer=write, now=NOW)


def two_targets(setup, *, first_age=2):
    feed = mobile_input(setup, age=first_age)
    value = packs.read_json(feed)
    other = {**value["rows"][0], "handle": "financialjuice", "tweet_id": "456",
             "url": "https://x.com/financialjuice/status/456",
             "posted_utc": (NOW-timedelta(minutes=2)).isoformat()}
    value["rows"].append(other)
    packs.save_json(feed, value)
    return feed


def ranked_pair(*args, **kwargs):
    return {"ranking": [{"post_id": "123", "quality_score": 92},
                        {"post_id": "456", "quality_score": 88}]}, {}


def test_one_writer_call_delivers_valid_peer_when_first_quality_draft_fails(setup):
    store, binding, root = setup
    feed = two_targets(setup)
    calls = []
    def draft(request_path, *, output_dir):
        request = packs.read_json(request_path)
        assert request["draft_limit"] == 3
        def write(prompt, **kwargs):
            calls.append("writer")
            packet = json.loads(prompt.rsplit("\n", 1)[1])
            assert [t["post_id"] for t in packet["targets"]] == ["123", "456"]
            response = authored(request)
            peer = {**response["items"][0], "post_id": "456"}
            response["items"][0]["draft_text"] = "No bound fact or date."
            response["items"].append(peer)
            return response, {}
        return botlane.rank_and_draft(request_path, output_dir=output_dir,
                                     ranker=ranked_pair, writer=write, now=NOW)
    transport = FakeBot()
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root/"out",
                                 bot=transport, drafter=draft, now=NOW)
    assert calls == ["writer"] and result["status"] == "DELIVERED"
    assert result["funnel"]["validated_draft_post_ids"] == ["456"]
    assert result["delivery"]["delivered"][0]["five_minute_target_met"] is True
    assert any(d["post_id"] == "123" for d in result["dropped_candidates"])
    assert not any(d["cause"] == "QUALITY_TARGET_QUEUED_FOR_NEXT_TICK" for d in result["dropped_candidates"])
    assert len([m for m, _ in transport.calls if m == "sendMessage"]) == 1
    assert not store.list_platform_dispatches()


def test_batch_respects_last_daily_slot_and_keeps_unwritten_peer_available(setup):
    store, binding, root = setup
    feed = two_targets(setup)
    for n in range(4):
        botlane.record(store, botlane.DELIVERY, {"delivery_day": "2026-11-11", "post_id": str(n)},
                       key="prior-"+str(n), status="UNKNOWN_WRITE" if n == 0 else "DELIVERED")
    def draft(request_path, *, output_dir):
        request = packs.read_json(request_path)
        assert request["draft_limit"] == 1
        def write(prompt, **kwargs):
            packet = json.loads(prompt.rsplit("\n", 1)[1])
            assert packet["max_drafts"] == 1 and packet["target"]["post_id"] == "123"
            return authored(request), {}
        return botlane.rank_and_draft(request_path, output_dir=output_dir,
                                     ranker=ranked_pair, writer=write, now=NOW)
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root/"out",
                                 bot=FakeBot(), drafter=draft, now=NOW)
    assert len(result["delivery"]["delivered"]) == 1
    assert len(store.list_outbox_messages(destination=botlane.DELIVERY)) == 5
    attempts = [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=botlane.ATTEMPTS)
                if r["status"] == "AVAILABLE"]
    assert [p["post_id"] for p in attempts] == ["456"]


def test_expiry_during_ranking_skips_old_winner_and_writes_fresh_peer(setup):
    store, _, root = setup
    feed = two_targets(setup, first_age=14)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    def write(prompt, **kwargs):
        packet = json.loads(prompt.rsplit("\n", 1)[1])
        assert packet["target"]["post_id"] == "456"
        response = authored(packs.read_json(ready["request_path"]))
        response["items"][0]["post_id"] = "456"
        return response, {}
    path = botlane.rank_and_draft(ready["request_path"], output_dir=root/"native", ranker=ranked_pair,
                                 writer=write, now=NOW+timedelta(minutes=2))
    value = packs.read_json(path)
    assert [d["post_id"] for d in value["items"]] == ["456"]
    assert {"post_id": "123", "cause": "TARGET_OVER_15_MINUTES_AT_SEND"} in value["omissions"]


@pytest.mark.parametrize("age", [2, 6])
def test_delivery_measures_ingestion_and_tick_delays_without_relaxing_late_send_rule(setup, age):
    store, binding, root = setup
    feed = mobile_input(setup, age=age)
    value = packs.read_json(feed)
    value["rows"][0]["ingested_utc"] = (NOW-timedelta(minutes=1)).isoformat()
    packs.save_json(feed, value)
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root/"out",
                                 bot=FakeBot(), drafter=draft_fixture, now=NOW)
    proof = result["delivery"]["delivered"][0]
    assert proof["five_minute_target_met"] is (age <= 5)
    assert proof["latency_seconds"] == {"post_to_ingestion": (age-1)*60,
        "ingestion_to_filter": 60, "filter_to_delivery": 0, "total": age*60}


def test_pack_revalidation_keeps_original_ingestion_and_selection_clocks(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    value = packs.read_json(feed)
    ingested = (NOW-timedelta(minutes=1)).isoformat()
    value["rows"][0]["ingested_utc"] = ingested
    packs.save_json(feed, value)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    response = root/"response.json"
    packs.save_json(response, authored(packs.read_json(ready["request_path"])))
    built = packs.build(store, request_path=ready["request_path"], response_path=response,
                        feed_path=feed, output_root=root, now=NOW+timedelta(minutes=1))
    item = packs.read_json(built["pack_path"])["items"][0]
    assert item["feed_seen_at_utc"] == ingested and item["selected_at_utc"] == NOW.isoformat()


def test_writer_consumes_completed_jsonl_turn_and_keeps_max_effort(tmp_path):
    import subprocess
    def run(args, **kwargs):
        assert "--json" in args and 'model_reasoning_effort="max"' in args
        for feature in ("shell_tool", "multi_agent", "apps", "remote_plugin", "hooks"):
            assert args[args.index(feature)-1] == "--disable"
        events = [{"type": "thread.started", "thread_id": "test-writer-session"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": '{"items":[],"omissions":[]}'}},
                  {"type": "turn.completed", "usage": {"output_tokens": 10}}]
        result = subprocess.CompletedProcess(args, 0, "\n".join(json.dumps(e) for e in events).encode(), b"")
        result.turn_completed, result.completion_seconds = True, 7.5
        return result
    answer, call = botlane._text_call("Return JSON only.", root=tmp_path, writer=True, runner=run)
    assert answer == {"items": [], "omissions": []}
    assert call["turn_completed_seconds"] == 7.5 and call["observed_session_id"] == "test-writer-session"
    assert call["configuration_status"] == "CONFIGURED_NOT_OBSERVED"


def test_paraphrased_private_addition_metadata_never_blocks_an_exact_public_fact(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    value = authored(packs.read_json(ready["request_path"]))
    value["items"][0]["addition"] = "Dated crowd positioning adds context absent from the original post."
    path = root / "response.json"
    packs.save_json(path, value)
    result = packs.build(store, request_path=ready["request_path"], response_path=path, feed_path=feed, output_root=root, now=NOW)
    assert result["item_count"] == 1


def test_dated_positioning_description_is_not_a_new_unconditional_call(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(ready["request_path"])
    draft = authored(request)["items"][0]
    draft["draft_text"] = "CFTC data for 9 Nov show speculators net long 102,321 yen contracts, 27% of open interest. That earlier bullish positioning can unwind when rate support fades."
    assert packs.validate_mobile_draft(draft, request["candidates"][0], request["sources"][0], now=NOW) == draft["draft_text"]
    draft["draft_text"] = draft["draft_text"].split(". ")[0] + ". The yen is bullish from here."
    with pytest.raises(ValueError, match="UNCONDITIONAL_CALL_FORBIDDEN"):
        packs.validate_mobile_draft(draft, request["candidates"][0], request["sources"][0], now=NOW)


def test_reconciliation_preserves_actual_writer_clock_instead_of_rebuild_time(setup):
    store, _, root = setup
    feed = mobile_input(setup)
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    response = authored(packs.read_json(ready["request_path"]))
    response["editorial_call"] = {"writer": {"ended_at_utc": (NOW - timedelta(minutes=1)).isoformat()}}
    path = root / "response.json"
    packs.save_json(path, response)
    result = packs.build(store, request_path=ready["request_path"], response_path=path, feed_path=feed, output_root=root, now=NOW)
    item = packs.read_json(result["pack_path"])["items"][0]
    assert item["post_to_draft_minutes"] == 1 and item["draft_ready_at_utc"] == (NOW - timedelta(minutes=1)).isoformat()


def test_headless_writer_has_explicit_model_effort_and_no_project_or_mcp_inheritance(tmp_path):
    import subprocess
    seen = []
    def run(args, **kwargs):
        seen.extend(args)
        assert kwargs["input"] == b"Return JSON only."
        assert kwargs["timeout"] == 90
        return subprocess.CompletedProcess(args, 0, b'{"items":[],"omissions":[]}', b"")
    _, call = botlane._text_call("Return JSON only.", root=tmp_path, writer=True, runner=run)
    assert seen[seen.index("--model") + 1] == "gpt-6.1-sol"
    assert 'model_reasoning_effort="max"' in seen
    assert "--ignore-user-config" in seen and "--ephemeral" in seen and "read-only" in seen
    assert call["configuration_status"] == "CONFIGURED_NOT_OBSERVED" and call["runtime_model"] is None


def test_native_timeout_keeps_partial_return_in_existing_call_artifacts(tmp_path):
    import subprocess
    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, kwargs["timeout"], output=b"partial native return", stderr=b"partial stderr")
    with pytest.raises(ValueError, match="AGY_RANK_TIMEOUT_65S"):
        botlane._text_call("Return ranking.", root=tmp_path, runner=run)
    assert (tmp_path / "stdout.txt").read_bytes() == b"partial native return"
    assert packs.read_json(tmp_path / "call.json")["status"] == "TIMEOUT"


def test_real_reply_observer_remains_wired_after_tab_gate_is_parked(setup):
    store, binding, root = setup
    feed = mobile_input(setup)
    botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                        bot=FakeBot(), drafter=draft_fixture, now=NOW)
    class Reader:
        def connect(self):
            pass
        def capture_inputs(self, owner, directory, **options):
            assert owner is store and options == {"include_mentions": False, "max_details": 1,
                                                  "group_title": "codex/cc464-reply-readback"}
            path = directory / "replies.json"
            packs.save_json(path, {"rows": [{"handle": "Capitalnicle", "tweet_id": "998",
                "url": "https://x.com/Capitalnicle/status/998", "posted_utc": (NOW + timedelta(minutes=3)).isoformat(),
                "in_reply_to_status_id": "123", "text": "Jim's manually sent reply."}]})
            return path, None
    result = botlane.observe_due(store, output_root=root / "out", reader=Reader(), now=NOW + timedelta(minutes=4))
    assert result["status"] == "OBSERVED" and result["readback"]["observed"][0]["parent_post_id"] == "123"
    value = json.loads(store.list_outbox_messages(destination=packs.READBACK_DESTINATION)[0]["payload"])
    assert value["post_to_draft_minutes"] == 2 and value["post_to_reply_minutes"] == 5
    assert packs.read_json(binding.parent / "x_reply_tabs.json")["enabled"] is False
    assert botlane.observe_due(store, output_root=root / "out", reader=Reader(), now=NOW + timedelta(minutes=5))["status"] == "OBSERVATION_NOT_DUE"


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
    assert expired["causes"]["TARGET_OVER_15_MINUTES_AT_SEND"] == 1


@pytest.mark.parametrize("corrupt", [False, True])
def test_source_bound_chart_is_sent_before_draft_and_original_bytes_are_preserved(setup, corrupt):
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
                "value": 102321, "display": "CFTC data for 9 Nov show speculators net long 102,321 yen contracts, 27% of open interest.",
                "rights_class": "CC_OWN_ANALYSIS", "image": image}]}}]}))
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW, reply_policy=packs.MOBILE_POLICY)
    value = authored(packs.read_json(ready["request_path"]))
    value["items"][0]["include_image"] = True
    response_path = root / "response.json"
    packs.save_json(response_path, value)
    result = packs.build(store, request_path=ready["request_path"], response_path=response_path, feed_path=feed, output_root=root, now=NOW)
    pack = packs.read_json(result["pack_path"])
    assert pack["items"][0]["image"] == image
    if corrupt:
        chart.write_bytes(b"changed bytes")
    class WithPhoto(FakeBot):
        def send_photo(self, chat_id, path):
            assert chat_id == 123456789 and sha256(path.read_bytes()).hexdigest() == image["sha256"]
            self.calls.append(("sendPhoto", str(path)))
            return {"message_id": 41}
    bot = WithPhoto()
    delivered = botlane.deliver_pack(store, result["store_message_id"], binding_path=binding, bot=bot, now=NOW)
    assert delivered["status"] == "DELIVERED"
    assert [m for m, _ in bot.calls if m.startswith("send")] == (["sendMessage"] if corrupt else ["sendPhoto", "sendMessage"])
    if not corrupt:
        assert sha256(chart.read_bytes()).hexdigest() == image["sha256"]
    else:
        assert delivered["causes"]["OPTIONAL_IMAGE_BOUND_CHART_BYTES_OR_RIGHTS_CHANGED"] == 1
