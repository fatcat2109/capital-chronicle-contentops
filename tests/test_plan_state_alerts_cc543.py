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


def test_gold_replay_delivers_both_apis_with_chart_before_ten_minutes(replay, main_root, monkeypatch, tmp_path):
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
            assert intent["native_payload"]["media_asset_ids"]
            self.intents.append(deepcopy(intent))
            return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)
    transport = Recorded()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda d: {"readiness_state": "READY_NON_BROWSER_BINDING"}, clock=lambda: now)
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
