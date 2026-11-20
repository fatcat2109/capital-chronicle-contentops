"""The installed plan consumer sends state alerts independently of analysis."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_plan_call_cards_cc399 import controlled_tradingview, write, rows  # noqa: F401
from test_plan_status_posts_cc306 import main_root, event  # noqa: F401
from test_plan_status_publication_cc306 import fake_host
from test_publication_coordinator_v1 import FixtureTransport, _set_mode
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_analysis_distribution_cc435 import confirm


GOLD = Path(__file__).parents[1] / "docs/publisher/CC-543/fixtures/gold-plan-20261112.json"


@pytest.fixture
def replay(tmp_path, monkeypatch, main_root):
    raw = json.loads(GOLD.read_bytes())
    now = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=1)
    store = ContentOpsDurableStore(tmp_path / "replay.sqlite3")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    from live_contentops import secret_store_v1
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: "fixture-bot" if name == "DISCORD_BOT_TOKEN" else None)
    # This is a replay of the current policy against the retained 12 Nov plan.
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            observed = posts._utc(json.loads((folder / "plan-status.public.json").read_bytes())["generated_at_utc"])
            return observed.astimezone(tz) if tz else observed.replace(tzinfo=None)
    monkeypatch.setattr(cards, "datetime", Clock)
    folder = write(tmp_path / "export", [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
                   generated_at_utc=now.isoformat())
    monkeypatch.setattr(posts, "EXPORT_DIR", folder)
    reader = posts.read_export
    def read_export(path=folder, **options):
        return reader(path, main_root=options.get("main_root", main_root), python=options.get("python", sys.executable))
    monkeypatch.setattr(posts, "read_export", read_export)
    return store, folder, raw, now


def test_gold_replay_queues_a_complete_alert_without_page_or_variants(replay, main_root, monkeypatch):
    store, folder, raw, now = replay
    def forbidden(*a, **k):
        raise AssertionError("MODEL_OR_BROWSER_UNAVAILABLE")
    monkeypatch.setattr(editorial, "prepare_social_row", forbidden)
    monkeypatch.setattr(editorial, "text_call", forbidden)
    monkeypatch.setattr(pages, "continue_page", forbidden)
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK", queued
    row, = rows(store)
    assert row["text"], "The first alert cannot wait for a page or a model."
    assert row["state_alert_contract"] == "CC543_V1"
    for value in ("Gold", "bearish", "3,954", "3,964", "3,972.6", "3,876", "ET"):
        assert value in row["text"]
    assert "https://" not in row["text"] and not row.get("parent_key")
    assert "demo" not in row["text"].lower() and "model position" not in row["text"].lower()
    assert posts.PUBLIC_NOTICE in row["text"] and posts.CONFLICTS_NOTICE in row["text"]
    assert "Spot close above 3,972.6" in row["text"]
    assert "MGC" not in row["text"]  # No instrument prices were exported in this older snapshot.


def test_gold_replay_delivers_both_apis_with_chart_before_ten_minutes(replay, main_root, monkeypatch, tmp_path, source):
    store, folder, raw, now = replay
    def failed(*a, **k):
        raise AssertionError("Every model and browser step is unavailable")
    monkeypatch.setattr(editorial, "prepare_social_row", failed)
    monkeypatch.setattr(editorial, "text_call", failed)
    monkeypatch.setattr(pages, "continue_page", failed)
    from live_contentops import image_quality_v1, light_model_caller_v1
    monkeypatch.setattr(image_quality_v1, "review_vision", failed)
    monkeypatch.setattr(light_model_caller_v1, "call_light", failed)
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    class Recorded(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.intents = []
        def publish(self, *, destination, intent, authorization_context):
            assert destination in {"telegram", "discord"}
            if intent.get("plan_status_post"):
                assert intent["native_payload"]["media_asset_ids"]
            else:
                assert intent["native_payload"]["reply_to_id"]
            self.intents.append(deepcopy(intent))
            self.publish_calls.append(destination)
            return {"status": "SUCCESS", "id": str(len(self.intents)),
                    "public_url": f"https://example.test/{destination}/{len(self.intents)}"}
        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if not any(i["work_item_id"] == intent["work_item_id"] and i["destination_plan"]["destination"] == destination
                       for i in self.intents):
                return {"status": "NOT_FOUND", "verified": False}
            return super().readback(destination=destination, public_object_id=public_object_id,
                                    public_object_url=public_object_url, intent=intent)
    transport = Recorded()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now,
        published_content_path=tmp_path / "published.jsonl")
    result = posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
        host=fake_host, coordinator_for=lambda *a: coordinator, immediate_only=True)
    assert len(transport.intents) == 2, result
    assert set(transport.publish_calls) == {"telegram", "discord"}
    assert (now - posts._utc(raw["registered_at_utc"])).total_seconds() < 600
    for intent in transport.intents:
        context = json.loads((Path(intent["output_dir"]) / "run_context_v1.json").read_bytes())
        assert context["media"]["assets"][0]["modality"] == "tradingview_chart_snapshot"
        posts.validate_status_post_intent(store, intent)
    posts.publish_ready(store, now=now, root=tmp_path / "posts", host=fake_host,
        coordinator_for=lambda *a: coordinator, immediate_only=True)
    assert len(transport.intents) == 2
    original = rows(store)[0]
    frozen_payload = store.get_outbox_message(original["key"])["payload"]
    assert original["x_analysis_thread"] is True
    assert "x" in cards._ready_destinations(store, original)
    missing_page = cards.prepare_post(store, original["key"], root=tmp_path / "posts", destinations=("x",))
    assert [d["destination"] for d in missing_page["destinations"]] == ["x"]
    assert not missing_page["deferred_destinations"]
    # The external page completes later. Its controlled source fixture tests the
    # existing exact page/link consumer, without performing a browser write.
    run_root, _, plan, manuscript = source
    plan.update(plan_id=raw["plan_id"], registration_hash=raw["registration_hash"])
    manuscript.update(plan_id=plan["plan_id"], registration_hash=plan["registration_hash"])
    packet = pages.register_page(store, pages.render(plan, manuscript, run_root=run_root, output_dir=tmp_path / "page"))
    confirm(store, packet["page_id"], packet["plan"]["plan_hash"], "substack", "confirmed-page",
            "https://capitalchronicle.substack.com/p/controlled-gold-analysis")
    coordinator.allow_prior_confirmed_distribution = True
    for destination in ("telegram", "discord"):
        value = pages.register_link(store, packet, original_key=original["key"], destination=destination)
        assert value["native_payload"]["reply_to_id"] == cards._reference(store, original["key"], destination)["public_object_id"]
        assert "https://capitalchronicle.substack.com/p/controlled-gold-analysis" in value["native_payload"]["full_text"]
        coordinator.recovery_scope = {"work_item_id": value["link_id"], "plan": value["plan"], "exact_work_item_only": True}
        outcome = coordinator.publish_plan(value["link_id"], value["plan"])
        assert outcome["per_destination"][destination]["status"] == "DISPATCH_CONFIRMED", outcome
        coordinator.publish_plan(value["link_id"], value["plan"])
    assert len(transport.intents) == 4  # two alerts, then two replies; no edits
    assert store.get_outbox_message(original["key"])["payload"] == frozen_payload
    landscape_hash = context["media"]["assets"][0]["sha256"]
    later = cards.prepare_post(store, original["key"], root=tmp_path / "posts", host=fake_host,
                               destinations=("instagram_business",))
    copies = posts._expected(store, original["key"], later["output_dir"])[1]
    expanded = json.loads((Path(later["output_dir"]) / "run_context_v1.json").read_bytes())
    assert expanded["media"]["assets"][0]["sha256"] == landscape_hash
    portrait_id, = copies["instagram_business"]["media_asset_ids"]
    portrait = next(a for a in expanded["media"]["assets"] if a["asset_id"] == portrait_id)
    assert portrait["width"] / portrait["height"] == pytest.approx(4 / 5)
    first_telegram = next(i for i in transport.intents if i.get("plan_status_post") and i["destination_plan"]["destination"] == "telegram")
    assert copies["telegram"] == first_telegram["native_payload"]

    # A later page cannot replace the export's frozen scenario with its own odds.
    assert "x" in cards._ready_destinations(store, original)
    x_plan = cards.prepare_post(store, original["key"], root=tmp_path / "posts", destinations=("x",))
    assert [d["destination"] for d in x_plan["destinations"]] == ["x"]
    registered = coordinator.register_plan(original["key"], x_plan)["registered"][0]
    x_intent = json.loads(store.get_outbox_message(registered["message_id"])["payload"])
    posts.validate_status_post_intent(store, x_intent)
    x = x_intent["native_payload"]
    assert "Scenarios: Alternative: A haven and short-covering squeeze" in x["full_text"]
    assert "Main (50%)" not in x["full_text"] and "Alternative (35%)" not in x["full_text"]
    assert "https://" not in x["text"]
    assert x["posts"][0]["media_asset_ids"]
    assert "https://capitalchronicle.substack.com/p/controlled-gold-analysis" not in x["full_text"]
    assert posts.PUBLIC_NOTICE in x["reply_texts"][0]
    assert cards.prepare_post(store, original["key"], root=tmp_path / "posts", destinations=("x",)) == x_plan
    assert pages.register_link(store, packet, original_key=original["key"], destination="x")["state"] == (
        "PLAN_ANALYSIS_PARENT_NOT_CONFIRMED")
    assert not store.get_outbox_message("plan-analysis-link-" + raw["plan_id"] + "-x")
    assert store.get_outbox_message(original["key"])["payload"] == frozen_payload
    assert posts._expected(store, original["key"], x_plan["output_dir"])[1]["telegram"] == first_telegram["native_payload"]


def test_missing_chart_sends_nothing_and_source_changes_fail(replay, main_root, monkeypatch, tmp_path):
    store, folder, _, now = replay
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    monkeypatch.setattr(posts, "_post_image", lambda *a, **k: (None, False))
    def forbidden(*a, **k):
        raise AssertionError("A chartless alert must never reach a transport")
    result = posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
        coordinator_for=forbidden, immediate_only=True)
    assert result["posts"][0]["cause"] == "EVERY_POST_IMAGE_REQUIRED:PLAN_SETUP"
    from live_contentops.plan_state_alerts_v1 import validate
    altered = deepcopy(rows(store)[0])
    altered["levels"]["zone_low"] += 1
    with pytest.raises(ValueError, match="PLAN_ALERT_SOURCE_FIELD_CHANGED"):
        validate(altered)


def test_later_states_use_the_same_api_consumer_without_editorial(replay, main_root, monkeypatch, tmp_path):
    store, folder, raw, now = replay
    runtime = FixtureTransport()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now,
        published_content_path=tmp_path / "published.jsonl")
    def failed(*a, **k):
        raise AssertionError("No state update needs a page or model")
    monkeypatch.setattr(editorial, "prepare_social_row", failed)
    events = [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])]
    for state in ("WAITING", "FILLED", "CLOSED"):
        raw["status"] = state
        if state != "WAITING":
            now += timedelta(minutes=1)
            events.append(event(raw["plan_id"], state, now.isoformat()))
        write(folder, [raw], events, generated_at_utc=now.isoformat())
        queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
        result = posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
            host=fake_host, coordinator_for=lambda *a: coordinator, immediate_only=True)
        assert any(r.get("per_destination", {}).get("telegram") == "DISPATCH_CONFIRMED" for r in result["posts"]), result
    assert runtime.publish_calls.count("telegram") == runtime.publish_calls.count("discord") == 3
    assert len(rows(store)) == 3
    setup = next(r for r in rows(store) if r["kind"] == "setup")
    for state in ("CANCELLED", "EXPIRED"):
        update = {**setup, "kind": "update", "state": state}
        text = cards.compose(update)["text"]
        assert ("withdrawn" if state == "CANCELLED" else "window ended") in text
        assert cards.NOTICES in text


def test_source_refusal_does_not_take_the_next_ending_delivery_slot(replay, main_root, tmp_path):
    from hashlib import sha256

    store, folder, raw, now = replay
    events = [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])]
    posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    setup, = rows(store)
    setup_key = setup["key"]
    store.create_work_item(story_id=setup_key, work_item_id=setup_key, title="Call card",
                           target_surface="MULTI_PLATFORM")
    confirm(store, setup_key, sha256(("plan-status-post:" + setup_key).encode()).hexdigest(),
            "telegram", "700", "https://t.me/CapitalChronicle/700")
    store.set_outbox_status(setup_key, "SETTLED")

    raw.update(status="EXPIRED", outcome={"state": "NOT_SCORED_UNTRIGGERED"})
    events.append(event(raw["plan_id"], "EXPIRED", now.isoformat()))
    now += timedelta(minutes=1)
    write(folder, [raw], events, generated_at_utc=now.isoformat())
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    ending, = [row for row in rows(store) if row["kind"] == "result"]

    # A newer ending omitted the target even though its bound source supplies one.
    invalid = deepcopy(ending)
    invalid.update(key="ending-with-unbound-target", at_utc=now.isoformat())
    assert invalid["levels"]["target"]
    invalid["levels"]["target"] = None
    invalid.update(cards.compose(invalid))
    invalid_bytes = json.dumps(invalid, sort_keys=True)
    store.register_outbox_message(message_id=invalid["key"], work_item_id=posts.WORK_ITEM_ID,
        destination=posts.DESTINATION, payload=invalid_bytes, status=posts.READY)

    runtime = FixtureTransport()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now,
        published_content_path=tmp_path / "published.jsonl")
    result = posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
        host=fake_host, coordinator_for=lambda *args: coordinator, immediate_only=True, limit=1)

    refused, delivered = result["posts"]
    assert refused == {"key": invalid["key"], "status": "NOT_STARTED", "cause": "PLAN_ALERT_SOURCE_FIELD_CHANGED:target"}
    assert delivered["key"] == ending["key"]
    assert delivered.get("per_destination", {}).get("telegram") == "DISPATCH_CONFIRMED", result
    dispatch = cards._dispatch(store, ending["key"], "telegram")
    intent = json.loads(store.get_outbox_message(dispatch["message_id"])["payload"])
    assert intent["native_payload"]["reply_to_id"] == "700"
    assert set(runtime.publish_calls) == {"telegram", "discord"}
    assert cards._dispatch(store, invalid["key"], "telegram") is None
    assert store.get_outbox_message(invalid["key"])["payload"] == invalid_bytes


@pytest.mark.parametrize("failure", ["refused-telegram", "superseded-before-fanout", "superseded-with-uncertain-x"])
def test_current_state_reaches_every_destination_on_next_tick(replay, main_root, tmp_path, failure, monkeypatch):
    from threading import Event
    from test_minute_consumer_cc515 import dispatch

    store, folder, raw, now = replay
    events = [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])]
    posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    setup, = rows(store)
    setup_key = setup["key"]
    setup_hash = sha256(("plan-status-post:" + setup_key).encode()).hexdigest()
    store.create_work_item(story_id=setup_key, work_item_id=setup_key, title="Call card",
                           target_surface="MULTI_PLATFORM")
    confirm(store, setup_key, setup_hash, "discord", "600",
            "https://discord.com/channels/42/1519311669216673802/600")
    if failure == "refused-telegram":
        dispatch(store, setup, "telegram", "DEFINITE_NO_WRITE")
    elif failure == "superseded-with-uncertain-x":
        old_x = dispatch(store, setup, "x", "UNKNOWN_WRITE")
    else:
        store.set_outbox_status(setup_key, posts.SUPERSEDED)

    raw.update(status="EXPIRED", outcome={"state": "NOT_SCORED_UNTRIGGERED"})
    events.append(event(raw["plan_id"], "EXPIRED", now.isoformat()))
    now += timedelta(minutes=1)
    write(folder, [raw], events, generated_at_utc=now.isoformat())
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    ending, = [row for row in rows(store) if row["kind"] == "result"]
    key = ending["key"]
    if failure == "refused-telegram":
        store.register_incident(incident_id=cards._settlement_id(key, "telegram"),
            work_item_id=posts.WORK_ITEM_ID, severity="RECOVERY_AUDIT",
            description=json.dumps({"cause": "CARD_PARENT_DEFINITE_NO_WRITE", "dispatch_id": None}))

    class ConcurrentRoutes(FixtureTransport):
        x_started = Event()

        def publish(self, *, destination, intent, authorization_context):
            if destination == "facebook_page":
                assert self.x_started.wait(10), "A slow destination serialized the alert fanout"
            if destination == "x":
                self.x_started.set()
            return super().publish(destination=destination, intent=intent,
                                   authorization_context=authorization_context)

    runtime = ConcurrentRoutes()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now,
        published_content_path=tmp_path / "published.jsonl")
    retired_readbacks = []
    if failure == "superseded-with-uncertain-x":
        def remember_readback(dispatch_id):
            assert "x" in runtime.publish_calls, "An old readback ran before the new alert's X copy"
            retired_readbacks.append(dispatch_id)
            return {"status": "UNKNOWN_WRITE", "publish_called": False}

        coordinator.readback_existing_dispatch = remember_readback
    options = {"now": now, "latest_states": queued["latest_states"], "root": tmp_path / "posts",
               "host": fake_host, "coordinator_for": lambda *args: coordinator}
    posts.publish_ready(store, **options, immediate_only=True)
    assert not retired_readbacks
    discord = cards._dispatch(store, key, "discord")
    assert discord["status"] == "DISPATCH_CONFIRMED"
    telegram = cards._dispatch(store, key, "telegram")
    assert telegram["status"] == "DISPATCH_CONFIRMED"
    telegram_intent = json.loads(store.get_outbox_message(telegram["message_id"])["payload"])
    assert "reply_to_id" not in telegram_intent["native_payload"]
    discord_bytes = store.get_outbox_message(discord["message_id"])["payload"]
    assert json.loads(discord_bytes)["native_payload"]["reply_to_id"] == "600"
    channel_reply = cards._dispatch(store, f"{key}-part-{cards.DISCORD_CHANNEL_PART}", "discord")
    assert channel_reply["status"] == "DISPATCH_CONFIRMED"
    channel_bytes = store.get_outbox_message(channel_reply["message_id"])["payload"]
    assert json.loads(channel_bytes)["native_payload"]["discord_channel_reply"] is True

    now += timedelta(minutes=1)
    options["now"] = now
    post_image = posts._post_image

    def capture_after_landscape(row, *args, **kwargs):
        if row["key"] == key and kwargs.get("ratio") == "4:5":
            for destination in set(cards.destinations_for(ending)) - {"instagram_business"}:
                assert cards._dispatch(store, key, destination)["status"] == "DISPATCH_CONFIRMED"
        return post_image(row, *args, **kwargs)

    monkeypatch.setattr(posts, "_post_image", capture_after_landscape)
    recovered = posts.publish_ready(store, **options, alert_filter=True, automatic_neo=True)
    assert set(runtime.publish_calls) == set(cards.destinations_for(ending)), recovered
    for destination in cards.destinations_for(ending):
        delivery = cards._dispatch(store, key, destination)
        assert delivery["status"] == "DISPATCH_CONFIRMED", recovered
        if destination not in {"telegram", "discord"}:
            intent = json.loads(store.get_outbox_message(delivery["message_id"])["payload"])
            assert "reply_to_id" not in intent["native_payload"]
    assert store.get_outbox_message(discord["message_id"])["payload"] == discord_bytes
    assert store.get_outbox_message(channel_reply["message_id"])["payload"] == channel_bytes
    assert store.get_outbox_message(setup_key)["status"] == posts.SUPERSEDED
    if failure == "superseded-with-uncertain-x":
        assert retired_readbacks == [old_x["dispatch_id"]]
        assert store.get_platform_dispatch(old_x["dispatch_id"])["status"] == "UNKNOWN_WRITE"
    posts.publish_ready(store, **options, alert_filter=True, automatic_neo=True)
    assert runtime.publish_calls.count("discord") == 2  # the thread entry and one channel reply
    assert len(runtime.publish_calls) == len(cards.destinations_for(ending)) + 1


@pytest.mark.parametrize("dry", [False, True])
def test_actual_minute_entry_sends_alerts_before_models_and_browser(tmp_path, monkeypatch, dry):
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("cc543_minute", Path(__file__).parents[1] / "scripts/plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    from live_contentops import x_reply_bot_v1 as bot, x_reply_tabs_v1 as tabs
    from live_contentops import event_timestamp_v1, event_pack_v1, audience_collection_v1, model_invocation_usage_v1
    from live_contentops import pinned_result_scorecard_v1, neo_endpoint_executor_v1, call_followups_v1
    from live_contentops import daily_trend_board_v1, heavy_news_quotes_v1, substack_daily_note_v1
    monkeypatch.setattr(call_followups_v1, "minute_due", lambda *a, **k: {"status": "NO_DUE_WORK"})
    monkeypatch.setattr(daily_trend_board_v1, "run_due", lambda *a, **k: {"status": "NO_DUE_WORK"})
    monkeypatch.setattr(heavy_news_quotes_v1, "refresh_due", lambda *a, **k: {"status": "NO_DUE_WORK"})
    monkeypatch.setattr(substack_daily_note_v1, "run_due", lambda *a, **k: {"status": "NO_DUE_WORK"})
    order = []
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **k: order.append("export") or {
        "status": "OK", "active_page_plan_ids": ["new-plan"],
        "latest_states": {"new-plan": "WAITING", "old-transition": "WAITING"}})
    def publish(*a, **kw):
        order.append("immediate" if kw.get("immediate_only") else
                     "alert-fanout" if kw.get("alert_filter") else "later-destinations")
        return {"status": "OK", "posts": []}
    def page(*a, **k):
        order.append("model-page")
        raise RuntimeError("MODEL_QUOTA_UNAVAILABLE")
    def draft(*a, **k):
        assert k["active_plan_ids"] == ["new-plan"]
        order.append("draft-worker")
        return {"status": "PAGE_DRAFT_WORKER_STARTED"}
    monkeypatch.setattr(posts, "publish_ready", publish)
    monkeypatch.setattr(posts, "read_export", lambda *a, **k: {})
    monkeypatch.setattr(posts, "record_run", lambda *a, **k: tmp_path / "runs.jsonl")
    monkeypatch.setattr(editorial, "run_due", page)
    monkeypatch.setattr(editorial, "start_page_draft_worker", draft)
    monkeypatch.setattr(bot, "refresh_due", lambda *a, **k: order.append("private-replies") or {})
    monkeypatch.setattr(bot, "observe_due", lambda *a, **k: {})
    monkeypatch.setattr(tabs, "refresh_due", lambda *a, **k: {})
    monkeypatch.setattr(pages, "resume_discord_links", lambda *a, **k: [])
    monkeypatch.setattr(neo_endpoint_executor_v1, "resume_stored_requests", lambda *a, **k: {"status": "BROWSER_UNAVAILABLE"})
    monkeypatch.setattr(pinned_result_scorecard_v1, "refresh_scorecard", lambda *a, **k: {})
    monkeypatch.setattr(event_timestamp_v1, "maintain_timestamps", lambda: {})
    monkeypatch.setattr(event_pack_v1, "run_due_packs", lambda *a, **k: {})
    monkeypatch.setattr(audience_collection_v1, "run_collection", lambda *a, **k: {"collected": 0})
    monkeypatch.setattr(model_invocation_usage_v1, "import_native_invocations", lambda *a, **k: {})
    class Output(io.StringIO):
        def reconfigure(self, **kw):
            pass
    output = Output()
    monkeypatch.setattr(sys, "stdout", output)
    assert cli.main(["--store", str(tmp_path / "cli.sqlite3"), "--publish", *(["--dry-run"] if dry else [])]) == 0
    assert order == (["export"] if dry else [
        "export", "immediate", "draft-worker", "alert-fanout", "private-replies", "model-page", "later-destinations"])
    if not dry:
        result = json.loads(output.getvalue())
        assert result["plan_pages"]["cause"] == "RuntimeError:MODEL_QUOTA_UNAVAILABLE"
        assert result["plan_pages"]["draft_worker"]["status"] == "PAGE_DRAFT_WORKER_STARTED"


def test_unknown_api_acceptance_is_read_back_without_republishing(replay, main_root, tmp_path):
    store, folder, _, now = replay
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    runtime = FixtureTransport(raise_after_write=True, ambiguous=True)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now,
        published_content_path=tmp_path / "published.jsonl")
    for _ in range(2):
        posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
            host=fake_host, coordinator_for=lambda *a: coordinator, immediate_only=True)
    assert sorted(runtime.publish_calls) == ["discord", "telegram"]
    row, = rows(store)
    assert all(cards._dispatch(store, row["key"], d)["status"] == "UNKNOWN_WRITE" for d in ("telegram", "discord"))


@pytest.mark.parametrize("change,result,headline", [
    ("FILLED", None, "an entry filled"),
    ("CLOSED", "HIT", "hit its target"),
    ("CLOSED", "STOPPED", "stopped at its invalidation level"),
    ("CLOSED", "EXPIRED", "closed at its time exit"),
    ("EXPIRED", "NOT_TRIGGERED", None),
    ("VIEW_CHANGED", None, "the view changed"),
])
def test_minute_consumer_sends_major_discord_updates_to_the_channel_and_thread(
        replay, main_root, tmp_path, change, result, headline):
    store, folder, raw, now = replay
    posts.queue_posts(store, folder, now=now, main_root=main_root)
    setup, = rows(store)
    store.create_work_item(story_id=setup["key"], title="Original call", target_surface="MULTI_PLATFORM",
                           work_item_id=setup["key"])
    channel, starter = "1519311669216673802", "700"
    prefix = "https://discord.com/channels/42/"
    card_id, card_channel = starter, channel
    if result == "STOPPED":
        # A retained card may live in the older shared run thread.
        run = setup["run_key"]
        store.create_work_item(story_id=run, title="Earlier call run", target_surface="MULTI_PLATFORM", work_item_id=run)
        confirm(store, run, sha256(("plan-status-post:" + run).encode()).hexdigest(),
                "discord", starter, f"{prefix}{channel}/{starter}")
        card_id, card_channel = "701", starter
    card_hash = sha256(("plan-status-post:" + setup["key"]).encode()).hexdigest()
    confirm(store, setup["key"], card_hash, "discord", card_id, f"{prefix}{card_channel}/{card_id}")
    store.set_outbox_status(setup["key"], "PUBLISHED")
    previous = store.get_outbox_message(setup["key"])["payload"]

    at = now + timedelta(minutes=1)
    updated = deepcopy(raw)
    updated.update(status=change)
    if result:
        outcome_id = "gold-result"
        updated["outcome"] = {"state": "SCORED_UNTRIGGERED" if result == "NOT_TRIGGERED" else "SCORED",
            "result": result, "outcome_id": outcome_id,
            "score": {"plan_id": raw["plan_id"], "asset_id": raw["asset_id"], "outcome_id": outcome_id,
                      "result": result, "resolved_at_utc": at.isoformat()}}
    write(folder, [updated], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"]),
                             event(raw["plan_id"], change, at.isoformat())], generated_at_utc=at.isoformat())
    queued = posts.queue_posts(store, folder, now=at, main_root=main_root)
    update = next(row for row in rows(store) if row["key"] != setup["key"])

    class Recorded(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.discord = []
            self.accepted = {}
            self.channel_readback_available = change != "FILLED"
            self.channel_readbacks = 0

        def publish(self, *, destination, intent, authorization_context):
            if destination != "discord":
                return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
            payload = intent["native_payload"]
            where = channel if payload.get("discord_channel_reply") else payload["discord_thread_parent_id"]
            message = str(901 + len(self.discord))
            self.discord.append(deepcopy(intent))
            receipt = {"status": "SUCCESS", "id": message, "public_url": f"{prefix}{where}/{message}"}
            self.accepted[intent["work_item_id"]] = receipt
            if change == "FILLED" and where == channel:
                raise TimeoutError("Discord accepted the reply and lost the response")
            return receipt

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            if destination != "discord":
                return super().readback(destination=destination, public_object_id=public_object_id,
                                        public_object_url=public_object_url, intent=intent)
            if intent["native_payload"].get("discord_channel_reply"):
                self.channel_readbacks += 1
                if not self.channel_readback_available:
                    return {"status": "READBACK_UNAVAILABLE", "verified": False}
            receipt = self.accepted[intent["work_item_id"]]
            return {"status": "SUCCESS", "verified": True,
                    "public_object_id": receipt["id"], "public_object_url": receipt["public_url"]}

    transport = Recorded()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: at)
    runs = []
    immediate_passes = (True, True, False) if change == "FILLED" else (True, True)
    for attempt, immediate in enumerate(immediate_passes):
        previous_readbacks = transport.channel_readbacks
        run = posts.publish_ready(store, now=at, latest_states=queued["latest_states"], root=tmp_path / "posts",
            host=fake_host, coordinator_for=lambda *a: coordinator, immediate_only=immediate, alert_filter=True)
        runs.append(run)
        if change == "FILLED" and immediate:
            first, = run["posts"]
            assert first["discord_channel_reply"]["status"] == "UNKNOWN_WRITE"
            assert first["discord_channel_reply"]["reconciliation_status"] == "RECONCILIATION_PENDING"
            assert coordinator._destination_day_failure("discord") is None
            if attempt:
                assert transport.channel_readbacks == previous_readbacks
            transport.channel_readback_available = True

    major = change != "VIEW_CHANGED"
    assert len(transport.discord) == (2 if major else 1), runs
    thread, *other = transport.discord
    archive = thread["native_payload"]
    assert archive["discord_thread_parent_id"] == starter
    assert archive["reply_to_id"] == card_id
    assert "Plan thread:" not in archive["text"]
    assert store.get_outbox_message(setup["key"])["payload"] == previous
    if headline:
        assert headline in archive["text"]
    if not major:
        return

    channel_intent, = other
    payload = channel_intent["native_payload"]
    assert payload["discord_channel_reply"] is True and "discord_thread_parent_id" not in payload
    assert payload["reply_to_id"] == starter
    assert payload["reply_to_url"] == f"{prefix}{channel}/{starter}"
    thread_link = f"{prefix}{starter}" if starter == card_id else f"{prefix}{starter}/{card_id}"
    assert f"Plan thread: <{thread_link}>" in payload["text"]
    assert archive["media_asset_ids"] == payload["media_asset_ids"] and payload["media_asset_ids"]
    assert payload["text"].replace(f"\n\nPlan thread: <{thread_link}>", "") == archive["text"]
    for intent in (thread, channel_intent):
        assert intent["plan_status_post"] == update["key"]
        posts.validate_status_post_intent(store, intent)
        dispatch = cards._dispatch(store, intent["work_item_id"], "discord")
        assert dispatch["status"] == "DISPATCH_CONFIRMED"
        assert dispatch["public_object_url"] == transport.accepted[intent["work_item_id"]]["public_url"]
    assert any(post["discord_channel_reply"]["reconciliation_status"] == "RECONCILED_CONFIRMED"
               for run in runs for post in run["posts"] if post.get("discord_channel_reply"))
    altered = deepcopy(channel_intent)
    altered["native_payload"]["reply_to_id"] = "unrelated"
    with pytest.raises(ValueError, match="PLAN_CARD_DISCORD_CHANNEL_REPLY_PARENT_CHANGED"):
        posts.validate_status_post_intent(store, altered)


def test_fast_fanout_delivers_new_copies_before_reading_back_the_uncertain_copy(replay, main_root, tmp_path):
    store, folder, _, now = replay
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)

    class MixedDelivery(FixtureTransport):
        steps = []

        def publish(self, *, destination, intent, authorization_context):
            self.steps.append(("publish", destination))
            if destination == "telegram":
                raise TimeoutError("first Telegram reply lost")
            return super().publish(destination=destination, intent=intent,
                                   authorization_context=authorization_context)

        def readback(self, *, destination, **request):
            self.steps.append(("readback", destination))
            if destination == "telegram":
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(destination=destination, **request)

    runtime = MixedDelivery()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now)
    opts = {"now": now, "latest_states": queued["latest_states"], "root": tmp_path / "posts",
            "host": fake_host, "coordinator_for": lambda *a: coordinator}
    posts.publish_ready(store, **opts, immediate_only=True)
    runtime.steps.clear()
    posts.publish_ready(store, **opts, automatic_neo=True, alert_filter=True)
    assert runtime.steps.index(("publish", "x")) < runtime.steps.index(("readback", "telegram"))
    assert ("publish", "telegram") not in runtime.steps
    assert ("readback", "discord") not in runtime.steps
    row, = rows(store)
    assert cards._dispatch(store, row["key"], "x")["status"] == "DISPATCH_CONFIRMED"
    assert cards._dispatch(store, row["key"], "telegram")["status"] == "UNKNOWN_WRITE"
