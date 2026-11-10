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
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.plan_status_posts_v1 import (
    DESTINATION, POST_DESTINATIONS, PlanPostError, _x_length, destination_payloads,
    prepare_post, publish_ready, queue_posts, validate_status_post_intent,
)
from test_plan_status_posts_cc306 import NOW, event, export as export_fixture, main_root, plan, write_export  # noqa: F401
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode


@pytest.fixture(autouse=True)
def ended_posts_on(monkeypatch):
    """Decision 106 turns ended-without-entry posts off; these tests cover their machinery."""
    from live_contentops import plan_status_posts_v1
    monkeypatch.setattr(plan_status_posts_v1, "POST_ENDED_WITHOUT_ENTRY", True)


@pytest.fixture(autouse=True)
def no_real_snapshot(monkeypatch, tmp_path):
    """CC-314: these tests never open TradingView; a refused snapshot takes the plan's fact card."""
    from live_contentops import tradingview_snapshot_v1 as tv

    def refused(*args, **kwargs):
        raise tv.SnapshotError("CONTROLLED_TEST_NO_BROWSER")
    monkeypatch.setattr(tv, "capture", refused)
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "snapshot-outcomes.jsonl")


def fake_host(*, work_item_id, delivery_only_assets, existing_manifest, article_assets, article, source_documents):
    if article_assets:
        from live_contentops.post_visuals_v1 import validate_post_data_card
        card = article_assets[0]
        validate_post_data_card(card, article, source_documents)  # the real check the hosting step runs
    else:
        # CC-314: post images are delivery-only; the hosting step checks their flags and provenance.
        from live_contentops.cloudinary_delivery_media_v1 import _validated_local_asset
        card = delivery_only_assets[0]
        _, blockers = _validated_local_asset(card)
        assert not blockers, blockers
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
    # Oil's setup went out earlier, so its cancellation is news readers can follow (Jim, 6 Nov).
    from live_contentops.plan_status_posts_v1 import DESTINATION as _D, WORK_ITEM_ID as _W
    store.create_work_item(story_id=_W, title="Plan status posts (decision 79)", target_surface="MULTI_PLATFORM", work_item_id=_W)
    store.register_outbox_message(message_id="announced-plan_oil", work_item_id=_W, destination=_D, status="PUBLISHED",
                                  payload=json.dumps({"plan_id": "plan_oil", "state": "WAITING"}))
    result = queue_posts(store, export_fixture, now=NOW, main_root=main_root, python=sys.executable)
    keys = {(q["symbol"], q["state"]): q["key"] for q in result["queued"]}
    return store, transport, coordinator, keys, tmp_path / "posts"


def test_each_destination_gets_the_post_and_the_notices_and_no_link(queued):
    store, _, _, keys, root = queued
    plan_ = prepare_post(store, keys[("XAUUSD", "WAITING")], root=root, host=fake_host)
    assert [d["destination"] for d in plan_["destinations"]] == list(POST_DESTINATIONS)
    for row in plan_["destinations"]:
        # Jim's decision 83: a status post carries no site link, only its text and image.
        assert row["canonical_url"] is None and "https://" not in row["payload"]
        assert row["payload"].startswith("Gold: new plan. If price trades into 4,070–4,085, the desk is bullish")
        assert PUBLIC_NOTICE in row["payload"]
    assert not {"linkedin", "facebook_page", "instagram_business", "substack"} & {d["destination"] for d in plan_["destinations"]}


def test_x_splits_into_a_post_and_a_notice_reply_within_its_limit(queued):
    store, _, _, keys, root = queued
    plan_ = prepare_post(store, keys[("XAUUSD", "WAITING")], root=root, host=fake_host)
    payload = destination_payloads(json.loads(store.get_outbox_message(keys[("XAUUSD", "WAITING")])["payload"]),
                                   card_id=plan_["status_post_card_id"])["x"]
    assert all(_x_length(p["text"]) <= 280 for p in payload["posts"])
    assert payload["posts"][0]["media_asset_ids"] == [plan_["status_post_card_id"]]
    assert payload["posts"][1]["text"].startswith(PUBLIC_NOTICE)


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
    # The minute task posts the API destinations only; X goes through the agent route.
    from live_contentops.plan_status_posts_v1 import API_DESTINATIONS
    assert sorted(calls) == sorted(list(API_DESTINATIONS) * len(keys)) and "x" not in calls
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
    monkeypatch.setattr("live_contentops.plan_status_posts_v1.read_transitions", lambda *a, **kw: [])
    store, _, _, keys, _ = queued
    with pytest.raises(PlanPostError, match="PLAN_STATUS_X_STALE_NOT_POSTED"):
        begin_x(store, keys[("XAUUSD", "TRIGGERED")], "a" * 64, native_invocation_id="agent",
                now=NOW + timedelta(minutes=61))


def test_recovery_sees_only_the_posts_own_rows(queued):
    """5 Nov first post: a store-wide recovery pass filed other pieces' readbacks under the post."""
    store, transport, coordinator, keys, root = queued
    seen = []
    real = coordinator.recover_pending

    def recover():
        seen.append(dict(coordinator.recovery_scope or {}))
        return real()

    coordinator.recover_pending = recover
    publish_ready(store, now=NOW, coordinator_for=lambda key, folder: coordinator, root=root, host=fake_host, limit=1)
    assert seen and seen[0]["exact_work_item_only"] is True
    assert seen[0]["work_item_id"] in keys.values()


def test_an_idle_run_touches_no_coordinator_and_no_host(queued):
    """5 Nov 11:10Z: the first --publish run outlived its minute with nothing fresh to post."""
    store, transport, coordinator, keys, root = queued
    publish_ready(store, now=NOW, coordinator_for=lambda key, folder: coordinator, root=root, host=fake_host, limit=10)
    calls = list(transport.publish_calls)

    def no_coordinator(key, folder):
        raise AssertionError("an idle run must not build a coordinator")

    def no_host(**kw):
        raise AssertionError("an idle run must not call the hosting provider")

    idle = publish_ready(store, now=NOW, coordinator_for=no_coordinator, root=root, host=no_host, limit=10)
    assert idle == {"status": "OK", "posts": []} and transport.publish_calls == calls


def test_a_hosted_card_is_reused_without_a_provider_call(queued):
    store, _, _, keys, root = queued
    key = keys[("XAUUSD", "TRIGGERED")]
    prepare_post(store, key, root=root, host=fake_host)

    def no_host(**kw):
        raise AssertionError("the verified hosted card must be reused")

    plan_ = prepare_post(store, key, root=root, host=no_host)
    assert plan_["status_post_card_id"]


def test_x_is_only_issued_by_the_agent_route_and_never_when_stale(queued, monkeypatch):
    from datetime import timedelta
    from live_contentops.plan_status_posts_v1 import start_x
    monkeypatch.setattr("live_contentops.plan_status_posts_v1.read_transitions", lambda *a, **kw: [])
    store, _, _, keys, root = queued
    key = keys[("XAUUSD", "TRIGGERED")]
    with pytest.raises(PlanPostError, match="PLAN_STATUS_X_STALE_NOT_POSTED"):
        start_x(store, key, native_invocation_id="agent", now=NOW + timedelta(minutes=61), root=root, host=fake_host)
    plan_ = prepare_post(store, key, root=root, host=fake_host, destinations=("x",))
    assert [d["destination"] for d in plan_["destinations"]] == ["x"]
