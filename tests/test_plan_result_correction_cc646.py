"""The held wrong result stops, and its exact correction reaches each original reply."""
import json

import pytest

from live_contentops import plan_result_correction_cc646 as correction
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from test_publication_coordinator_v1 import _coordinator, _set_mode
from test_plan_status_publication_cc306 import recorded_snapshot, fake_host


def prepare(store, root):
    from live_contentops import tradingview_snapshot_v1 as tv
    from live_contentops.publication_image_contract_v1 import not_compared
    source = root / "source-chart"
    snap = recorded_snapshot("USDJPY", "240", source)
    snap["price_scale_check"] = not_compared("USDJPY", snap, "CONTROLLED_FIXTURE_NO_QUOTE", [])
    asset = tv.snapshot_asset(snapshot=snap, market="USDJPY", title="Original plan", out_dir=source)
    (source / "run_context_v1.json").write_text(json.dumps({"media": {"assets": [asset]}}), encoding="utf-8")
    hosted = fake_host(work_item_id="original", delivery_only_assets=[asset], article_assets=[],
        existing_manifest=None, article={}, source_documents=[])
    (source / "delivery_media_manifest_v1.json").write_text(json.dumps(hosted["manifest"]), encoding="utf-8")
    return correction.prepare(store, root=root / "posts", media_source=source)


def original(tmp_path):
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    key = correction.ORIGINAL
    store.create_work_item(story_id=key, title="Original USD/JPY result", target_surface="MULTI_PLATFORM", work_item_id=key)
    store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Status posts", target_surface="MULTI_PLATFORM", work_item_id=posts.WORK_ITEM_ID)
    store.register_outbox_message(message_id=key, work_item_id=posts.WORK_ITEM_ID,
        destination=posts.DESTINATION, payload=json.dumps({"text": "USD/JPY: not triggered."}), status="PUBLISHING")
    for destination in ("telegram", "discord", "facebook_page", "instagram_business", "threads", "x"):
        ids = coordinator._ids(key, "original-plan", destination)
        intent = {"work_item_id": key, "plan_status_post": key, "plan_hash": "original-plan",
                  "native_payload": {"discord_thread_parent_id": "1572136686857748551"}}
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=key,
            destination=destination, payload=json.dumps(intent), status="READY")
        if destination in {"telegram", "discord"}:
            store.set_outbox_status(ids["message_id"], "DISPATCH_CONFIRMED")
            object_id = "189" if destination == "telegram" else "1572145031173906523"
            url = "https://t.me/CapitalChronicle/189" if destination == "telegram" else (
                "https://discord.com/channels/1519310996030750782/1572136686857748551/1572145031173906523")
            store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
                platform=destination, status="DISPATCH_CONFIRMED", public_object_id=object_id, public_object_url=url)
    return store, transport, coordinator


def cancel(store, coordinator):
    results = []
    for row in store.list_outbox_messages():
        if row["work_item_id"] == correction.ORIGINAL and row["status"] == "READY":
            results.append(coordinator.cancel_unclaimed_status_post(row["message_id"], reason=correction.CANCEL_REASON))
    return results


def test_untouched_rows_stop_once_without_changing_any_payload_or_public_object(tmp_path):
    store, transport, coordinator = original(tmp_path)
    before = {r["message_id"]: r["payload"] for r in store.list_outbox_messages()}
    public = store.get_dispatches_for_work_item(correction.ORIGINAL)
    stopped = cancel(store, coordinator)
    assert {r["destination"] for r in stopped} == {"facebook_page", "instagram_business", "threads", "x"}
    for result in stopped:
        assert result["public_write_performed"] is False
        assert coordinator.cancel_unclaimed_status_post(result["message_id"], reason=correction.CANCEL_REASON) == result
        assert not store.claim_platform_dispatch_attempt(dispatch_id=result["dispatch_id"],
            message_id=result["message_id"], platform=result["destination"])
        assert not store.claim_platform_dispatch_attempt(dispatch_id=result["dispatch_id"],
            message_id=result["message_id"], platform=result["destination"], expected_status="DEFINITE_NO_WRITE")
    assert before == {r["message_id"]: r["payload"] for r in store.list_outbox_messages()}
    assert public == [r for r in store.get_dispatches_for_work_item(correction.ORIGINAL) if r["status"] == "DISPATCH_CONFIRMED"]
    assert transport.publish_calls == []


@pytest.mark.parametrize("status", ["DISPATCH_ATTEMPT_STARTED", "UNKNOWN_WRITE", "NATIVE_NEO_TOOL_PENDING", "DISPATCH_CONFIRMED"])
def test_cancellation_never_erases_a_claim_or_uncertain_write(tmp_path, status):
    store, _, coordinator = original(tmp_path)
    ids = coordinator._ids(correction.ORIGINAL, "original-plan", "x")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="x", status=status)
    with pytest.raises(ValueError, match="ALREADY_CLAIMED_READBACK_REQUIRED"):
        coordinator.cancel_unclaimed_status_post(ids["message_id"], reason=correction.CANCEL_REASON)
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == status
    assert store.get_outbox_message(ids["message_id"])["status"] == "READY"


def test_native_action_claim_cannot_be_cancelled_even_without_a_dispatch(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    store, _, coordinator = original(tmp_path)
    ids = coordinator._ids(correction.ORIGINAL, "original-plan", "x")
    intent = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
    request = {"destination": "x", "action": "PUBLISH", "intent_sha256": sha256_of(intent), "request_sha256": "bound-request"}
    for key, payload in [("native-request", {"request": request}),
        ("native-neo-" + sha256_of([correction.ORIGINAL, "bound-request", "started"]), {})]:
        store.register_outbox_message(message_id=key, work_item_id=correction.ORIGINAL,
            destination="internal:native-neo-tool", payload=json.dumps(payload), status="READY")
    with pytest.raises(ValueError, match="ALREADY_CLAIMED_READBACK_REQUIRED"):
        coordinator.cancel_unclaimed_status_post(ids["message_id"], reason=correction.CANCEL_REASON)
    assert store.get_outbox_message(ids["message_id"])["status"] == "READY"


def test_correction_cannot_overtake_the_unclaimed_wrong_copies(tmp_path):
    store, _, _ = original(tmp_path)
    with pytest.raises(ValueError, match="PENDING_WRITES_MUST_BE_SETTLED"):
        correction.prepare(store, root=tmp_path)


def test_existing_minute_consumer_can_settle_the_cancelled_outbox_projection(tmp_path):
    store, _, coordinator = original(tmp_path)
    cancelled = cancel(store, coordinator)
    for result in cancelled:
        store.set_outbox_status(result["message_id"], "PLAN_POST_SETTLED")
        assert coordinator.cancel_unclaimed_status_post(result["message_id"], reason=correction.CANCEL_REASON) == result
        assert not store.claim_platform_dispatch_attempt(dispatch_id=result["dispatch_id"],
            message_id=result["message_id"], platform=result["destination"])
    assert prepare(store, tmp_path)["plan_status_post"] == correction.KEY


def test_exact_supplied_correction_reaches_both_live_consumers_once(tmp_path):
    store, transport, coordinator = original(tmp_path)
    cancel(store, coordinator)
    source = store.get_outbox_message(correction.ORIGINAL)["payload"]
    plan = prepare(store, tmp_path)
    posts.scope_to_post(coordinator, correction.KEY, plan)
    coordinator.execute_plan(correction.KEY, plan)
    assert sorted(transport.publish_calls) == ["discord", "telegram"]
    for d in store.get_dispatches_for_work_item(correction.KEY):
        intent = json.loads(store.get_outbox_message(d["message_id"])["payload"])
        posts.validate_status_post_intent(store, intent)
        data = pipeline._durable_intent_inputs(intent)
        payload = data["payloads"][d["platform"]]
        assert payload["text"] == correction.DELIVERY_TEXT
        assert data["local_media"] and payload["media_asset_ids"]
        assert payload["reply_to_id"] == ("189" if d["platform"] == "telegram" else "1572145031173906523")
        if d["platform"] == "discord":
            assert payload["discord_thread_parent_id"] == "1572136686857748551"
        changed = {**intent, "native_payload": {**intent["native_payload"], "reply_to_id": "wrong"}}
        with pytest.raises(posts.PlanPostError, match="COPY_CHANGED"):
            posts.validate_status_post_intent(store, changed)
    assert correction.prepare(store, root=tmp_path / "posts") == plan
    coordinator.execute_plan(correction.KEY, plan)
    assert sorted(transport.publish_calls) == ["discord", "telegram"]
    assert store.get_outbox_message(correction.ORIGINAL)["payload"] == source


def test_discord_transport_uses_exact_reply_and_retained_chart(tmp_path, monkeypatch):
    store, _, coordinator = original(tmp_path)
    cancel(store, coordinator)
    plan = prepare(store, tmp_path)
    coordinator.register_plan(correction.KEY, plan)
    intent = json.loads(next(r for r in store.list_outbox_messages()
        if r["work_item_id"] == correction.KEY and r["destination"] == "discord")["payload"])
    sent = []
    monkeypatch.setattr(pipeline, "_publish_discord_verified", lambda **kwargs: sent.append(kwargs) or {"status": "SUCCESS"})
    pipeline._publish_one_destination_from_durable_intent(destination="discord", intent=intent,
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": intent["attempt_identity"]})
    assert sent[0]["text"] == correction.DELIVERY_TEXT and sent[0]["image_path"]
    assert sent[0]["reply_to_message_id"] == "1572145031173906523"
    assert sent[0]["thread_parent_id"] == "1572136686857748551"
