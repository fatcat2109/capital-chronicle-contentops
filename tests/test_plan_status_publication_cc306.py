"""CC-306 posting step: a queued plan-state post goes to X, Threads, Telegram and Discord through the
sole coordinator, with its own frozen copy, a title card and the market's page as its link.
Controlled fixtures and fake transports only; no network or public write.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import sys

import pytest

from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
from live_contentops.plan_status_posts_v1 import (
    DESTINATION, POST_DESTINATIONS, PlanPostError, SITE_ASSET_URL, _x_length, destination_payloads,
    prepare_post, publish_ready, queue_posts, validate_status_post_intent,
)
from test_plan_status_posts_cc306 import NOW, event, export as export_fixture, main_root, plan, write_export  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode


def fake_host(*, work_item_id, delivery_only_assets, existing_manifest, article_assets, article, source_documents):
    from live_contentops.post_visuals_v1 import validate_post_data_card
    card = article_assets[0]
    validate_post_data_card(card, article, source_documents)  # the real check the hosting step runs
    # The real result's shape (cloudinary_delivery_media_v1, read on the 5 Nov first post):
    # status READY, with the manifest itself under "manifest".
    return {"status": "CLOUDINARY_DELIVERY_MEDIA_READY", "provider_calls": 1, "manifest": {"status": "PASS", "assets": [{
        "media_asset_id": card["asset_id"], "sha256": card["sha256"], "public_delivery_sha256": card["sha256"],
        "absolute_local_source_path": card["path"], "local_public_hash_continuity": True,
        "verified_public_delivery_url": "https://res.cloudinary.com/demo/image/upload/" + card["sha256"][:16] + ".png"}]}}


@pytest.fixture
def queued(tmp_path, export_fixture, main_root):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    result = queue_posts(store, export_fixture, now=NOW, main_root=main_root, python=sys.executable)
    keys = {(q["symbol"], q["state"]): q["key"] for q in result["queued"]}
    return store, transport, coordinator, keys, tmp_path / "posts"


def test_each_destination_gets_the_post_the_market_page_and_the_notices(queued):
    store, _, _, keys, root = queued
    plan_ = prepare_post(store, keys[("XAUUSD", "WAITING")], root=root, host=fake_host)
    assert [d["destination"] for d in plan_["destinations"]] == list(POST_DESTINATIONS)
    url = SITE_ASSET_URL.format(symbol="XAUUSD")
    for row in plan_["destinations"]:
        assert row["canonical_url"] == url and url in row["payload"]
        assert row["payload"].startswith("Gold: new plan. If price trades into 4,070–4,085, the desk is bullish")
        assert "Analysis, not financial advice." in row["payload"]
    assert not {"linkedin", "facebook_page", "instagram_business", "substack"} & {d["destination"] for d in plan_["destinations"]}


def test_x_splits_into_a_post_and_a_notice_reply_within_its_limit(queued):
    store, _, _, keys, root = queued
    plan_ = prepare_post(store, keys[("XAUUSD", "WAITING")], root=root, host=fake_host)
    payload = destination_payloads(json.loads(store.get_outbox_message(keys[("XAUUSD", "WAITING")])["payload"]),
                                   card_id=plan_["status_post_card_id"])["x"]
    assert all(_x_length(p["text"]) <= 280 for p in payload["posts"])
    assert payload["posts"][0]["media_asset_ids"] == [plan_["status_post_card_id"]]
    assert payload["posts"][1]["text"].startswith("Analysis, not financial advice.")


def test_the_registered_intents_carry_the_frozen_copy_card_and_hosted_url(queued):
    store, _, coordinator, keys, root = queued
    key = keys[("USOIL", "CANCELLED")]
    plan_ = prepare_post(store, key, root=root, host=fake_host)
    store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM", work_item_id=key)
    coordinator.register_plan(key, plan_)
    intents = {r["destination"]: json.loads(r["payload"]) for r in store.list_outbox_messages() if r["work_item_id"] == key}
    assert set(intents) == set(POST_DESTINATIONS)
    for destination in ("telegram", "discord", "threads"):
        intent = intents[destination]
        validate_status_post_intent(store, intent)
        data = _durable_intent_inputs(intent)
        assert data["payloads"][destination] == intent["native_payload"]
        assert data["payloads"][destination]["text"].startswith("US crude oil: the plan with the 61.2–61.8 entry zone is cancelled")
        assert data["local_media"].endswith(".png") and data["public_image_url"].startswith("https://res.cloudinary.com/")
        assert "published_content_export" not in intent


def test_a_changed_frozen_copy_is_refused_before_any_write(queued):
    store, _, coordinator, keys, root = queued
    key = keys[("XAUUSD", "TRIGGERED")]
    plan_ = prepare_post(store, key, root=root, host=fake_host)
    store.create_work_item(story_id=key, title="Plan status post", target_surface="MULTI_PLATFORM", work_item_id=key)
    coordinator.register_plan(key, plan_)
    intent = next(json.loads(r["payload"]) for r in store.list_outbox_messages()
                  if r["work_item_id"] == key and r["destination"] == "telegram")
    intent["native_payload"] = {**intent["native_payload"], "text": "Gold: buy now."}
    with pytest.raises(PlanPostError, match="PLAN_STATUS_POST_INTENT_COPY_CHANGED"):
        validate_status_post_intent(store, intent)


def test_publish_ready_runs_each_post_once_through_the_coordinator(queued):
    store, transport, coordinator, keys, root = queued
    first = publish_ready(store, now=NOW, coordinator_for=lambda key, folder: coordinator, root=root, host=fake_host, limit=10)
    assert {p["status"] for p in first["posts"]} == {"PUBLISHED"}
    calls = list(transport.publish_calls)
    assert sorted(calls) == sorted(list(POST_DESTINATIONS) * len(keys))
    again = publish_ready(store, now=NOW, coordinator_for=lambda key, folder: coordinator, root=root, host=fake_host, limit=10)
    assert again["posts"] == [] and transport.publish_calls == calls  # published rows are not run again
    assert {r["status"] for r in store.list_outbox_messages(destination=DESTINATION)} == {"PUBLISHED"}


def test_a_hosting_failure_posts_nothing(queued):
    store, transport, coordinator, keys, root = queued
    result = publish_ready(store, now=NOW, coordinator_for=lambda key, folder: coordinator, root=root, limit=1,
                           host=lambda **kw: {"status": "BLOCKED_CLOUDINARY_CREDENTIALS_MISSING"})
    assert result["posts"][0]["status"] == "NOT_STARTED"
    assert "PLAN_STATUS_CARD_HOSTING_BLOCKED_CLOUDINARY_CREDENTIALS_MISSING" in result["posts"][0]["cause"]
    assert transport.publish_calls == []


def test_a_row_older_than_sixty_minutes_when_reached_is_marked_stale_and_never_posted(queued):
    from datetime import timedelta
    store, transport, coordinator, keys, root = queued
    later = NOW + timedelta(minutes=50)  # gold's setup (11:45) is now 95 minutes old; oil's cancel 70
    result = publish_ready(store, now=later, coordinator_for=lambda key, folder: coordinator, root=root,
                           host=fake_host, limit=10)
    statuses = {p["key"]: (p["status"], p.get("cause")) for p in result["posts"]}
    assert statuses[keys[("XAUUSD", "WAITING")]] == ("STALE_NOT_POSTED",
                                                    "TRANSITION_OLDER_THAN_60_MINUTES_WHEN_POSTER_REACHED_IT")
    assert statuses[keys[("XAUUSD", "TRIGGERED")]][0] == "PUBLISHED"  # 12:20, 60 minutes: still fresh
    assert transport.publish_calls.count("telegram") == 1


def test_a_new_plan_post_for_a_plan_that_already_triggered_never_goes_out(queued):
    store, transport, coordinator, keys, root = queued
    latest = {"plan_gold": "TRIGGERED", "plan_oil": "CANCELLED"}
    result = publish_ready(store, latest_states=latest, now=NOW, coordinator_for=lambda key, folder: coordinator,
                           root=root, host=fake_host, limit=10)
    statuses = {p["key"]: (p["status"], p.get("cause")) for p in result["posts"]}
    assert statuses[keys[("XAUUSD", "WAITING")]] == ("SUPERSEDED_NOT_POSTED", "PLAN_ALREADY_TRIGGERED")
    assert statuses[keys[("USOIL", "WAITING")]] == ("SUPERSEDED_NOT_POSTED", "PLAN_ALREADY_CANCELLED")
    assert statuses[keys[("XAUUSD", "TRIGGERED")]][0] == "PUBLISHED"
    assert statuses[keys[("USOIL", "CANCELLED")]][0] == "PUBLISHED"


def test_a_stale_x_request_is_never_claimed_for_a_write(queued, monkeypatch):
    from datetime import timedelta
    from live_contentops.plan_status_posts_v1 import begin_x

    class Packet:
        def __init__(self, *a, **k):
            pass

        def _get(self, request_hash, kind):
            return {"request": {"destination": "x", "action": "PUBLISH", "request_sha256": request_hash}}

        def begin(self, request_hash):
            raise AssertionError("a stale X post must not be claimed")

    monkeypatch.setattr("live_contentops.native_neo_executor_v1.NativeNeoExecutor", Packet)
    store, _, _, keys, _ = queued
    with pytest.raises(PlanPostError, match="PLAN_STATUS_X_STALE_NOT_POSTED"):
        begin_x(store, keys[("XAUUSD", "TRIGGERED")], "a" * 64, native_invocation_id="agent",
                now=NOW + timedelta(minutes=61))
