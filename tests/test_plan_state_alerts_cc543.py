"""The installed plan consumer sends state alerts independently of analysis."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
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
def replay(tmp_path, monkeypatch):
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
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(cards, "datetime", Clock)
    folder = write(tmp_path / "export", [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
                   generated_at_utc=now.isoformat())
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
    for value in ("gold", "bearish", "3,954", "3,964", "3,972.6", "3,876", "ET"):
        assert value in row["text"]
    assert "https://" not in row["text"] and not row.get("parent_key")
    assert "demo" not in row["text"].lower() and "model position" not in row["text"].lower()
    assert posts.PUBLIC_NOTICE in row["text"] and posts.CONFLICTS_NOTICE in row["text"]


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


def test_missing_chart_sends_nothing_and_source_changes_fail(replay, main_root, monkeypatch, tmp_path):
    store, folder, _, now = replay
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    monkeypatch.setattr(posts, "_post_image", lambda *a, **k: (None, False))
    def forbidden(*a, **k):
        raise AssertionError("A chartless alert must never reach a transport")
    result = posts.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
        coordinator_for=forbidden, immediate_only=True)
    assert result["posts"][0]["cause"] == "JIM_DECISION_82_TRADINGVIEW_CHART_REQUIRED"
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


@pytest.mark.parametrize("dry", [False, True])
def test_actual_minute_entry_sends_alerts_before_models_and_browser(tmp_path, monkeypatch, dry):
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("cc543_minute", Path(__file__).parents[1] / "scripts/plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    from live_contentops import x_reply_bot_v1 as bot, x_reply_tabs_v1 as tabs
    from live_contentops import event_timestamp_v1, event_pack_v1, audience_collection_v1, model_invocation_usage_v1
    from live_contentops import pinned_result_scorecard_v1, neo_endpoint_executor_v1
    order = []
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **k: order.append("export") or {"status": "OK"})
    def publish(*a, **kw):
        order.append("immediate" if kw.get("immediate_only") else "later-destinations")
        return {"status": "OK", "posts": []}
    def page(*a, **k):
        order.append("model-page")
        raise RuntimeError("MODEL_QUOTA_UNAVAILABLE")
    monkeypatch.setattr(posts, "publish_ready", publish)
    monkeypatch.setattr(posts, "read_export", lambda *a, **k: {})
    monkeypatch.setattr(posts, "record_run", lambda *a, **k: tmp_path / "runs.jsonl")
    monkeypatch.setattr(editorial, "run_due", page)
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
    assert order == (["export"] if dry else ["export", "immediate", "private-replies", "model-page", "later-destinations"])
    if not dry:
        result = json.loads(output.getvalue())
        assert result["plan_pages"]["cause"] == "RuntimeError:MODEL_QUOTA_UNAVAILABLE"
