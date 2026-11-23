"""A spec-built correction reaches each confirmed public object of the original once, with its exact text."""
import json

import pytest

from live_contentops import correction_reply_v1 as correction
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from test_publication_coordinator_v1 import _coordinator, _set_mode
from test_plan_status_publication_cc306 import recorded_snapshot, fake_host

ORIGINAL = "plan-result-post-a8e253acc319a25824a6ef48ffa8355d"
SPEC = {"key": "correction-reply-usdjpy-230-20261123", "original": ORIGINAL, "destinations": ["telegram", "discord"],
        "symbol": "USDJPY", "title": "USD/JPY: a note on the post above",
        "body": ("USD/JPY: a note on the post above. It is the final result of the plan registered on 17 Nov, whose "
                 "time exit was 18 Nov 13:30 ET."),
        "authority": "test"}


def original(tmp_path, destinations=("telegram", "discord")):
    from live_contentops import tradingview_snapshot_v1 as tv
    from live_contentops.publication_image_contract_v1 import not_compared
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = tmp_path / "original-post"
    snap = recorded_snapshot("USDJPY", "240", folder)
    snap["price_scale_check"] = not_compared("USDJPY", snap, "CONTROLLED_FIXTURE_NO_QUOTE", [])
    asset = tv.snapshot_asset(snapshot=snap, market="USDJPY", title="Original result", out_dir=folder)
    (folder / "run_context_v1.json").write_text(json.dumps({"media": {"assets": [asset]}}), encoding="utf-8")
    hosted = fake_host(work_item_id=ORIGINAL, delivery_only_assets=[asset], article_assets=[],
                       existing_manifest=None, article={}, source_documents=[])
    (folder / "delivery_media_manifest_v1.json").write_text(json.dumps(hosted["manifest"]), encoding="utf-8")
    store.create_work_item(story_id=ORIGINAL, title="Original result", target_surface="MULTI_PLATFORM", work_item_id=ORIGINAL)
    store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Status posts", target_surface="MULTI_PLATFORM",
                           work_item_id=posts.WORK_ITEM_ID)
    store.register_outbox_message(message_id=ORIGINAL, work_item_id=posts.WORK_ITEM_ID, destination=posts.DESTINATION,
                                  payload=json.dumps({"text": "USD/JPY: price reached the entry zone."}), status="SETTLED")
    for destination in destinations:
        ids = coordinator._ids(ORIGINAL, "original-plan", destination)
        intent = {"work_item_id": ORIGINAL, "plan_status_post": ORIGINAL, "plan_hash": "original-plan",
                  "output_dir": str(folder), "native_payload": {"discord_thread_parent_id": "1572136686857748551"}}
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=ORIGINAL, destination=destination,
                                      payload=json.dumps(intent), status="DISPATCH_CONFIRMED")
        object_id = "230" if destination == "telegram" else "1574256463226863707"
        url = ("https://t.me/CapitalChronicle/230" if destination == "telegram" else
               "https://discord.com/channels/1519310996030750782/1572136686857748551/1574256463226863707")
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
                                         platform=destination, status="DISPATCH_CONFIRMED",
                                         public_object_id=object_id, public_object_url=url)
    return store, transport, coordinator, folder


def test_spec_correction_reaches_each_confirmed_parent_once_with_its_exact_text(tmp_path):
    store, transport, coordinator, _ = original(tmp_path)
    plan = correction.prepare(store, SPEC, root=tmp_path / "posts")
    posts.scope_to_post(coordinator, SPEC["key"], plan)
    coordinator.execute_plan(SPEC["key"], plan)
    assert sorted(transport.publish_calls) == ["discord", "telegram"]
    expected = correction.text_for(SPEC["body"]) + "\n\n" + posts.CHART_CREDIT
    for d in store.get_dispatches_for_work_item(SPEC["key"]):
        intent = json.loads(store.get_outbox_message(d["message_id"])["payload"])
        posts.validate_status_post_intent(store, intent)
        payload = pipeline._durable_intent_inputs(intent)["payloads"][d["platform"]]
        assert payload["text"] == expected and payload["media_asset_ids"]
        assert payload["reply_to_id"] == ("230" if d["platform"] == "telegram" else "1574256463226863707")
        if d["platform"] == "discord":
            assert payload["discord_thread_parent_id"] == "1572136686857748551"
        changed = {**intent, "native_payload": {**intent["native_payload"], "reply_to_id": "wrong"}}
        with pytest.raises(posts.PlanPostError, match="COPY_CHANGED"):
            posts.validate_status_post_intent(store, changed)
    assert correction.prepare(store, SPEC, root=tmp_path / "posts") == plan
    coordinator.execute_plan(SPEC["key"], plan)
    assert sorted(transport.publish_calls) == ["discord", "telegram"]


def test_a_missing_confirmed_parent_refuses_before_any_write(tmp_path):
    store, transport, _, _ = original(tmp_path, destinations=("telegram",))
    with pytest.raises(ValueError, match="CORRECTION_PUBLIC_PARENTS_REQUIRED:discord"):
        correction.prepare(store, SPEC, root=tmp_path / "posts")
    assert transport.publish_calls == [] and not store.get_outbox_message(SPEC["key"])


def test_the_key_never_carries_another_spec_or_an_unsupported_destination(tmp_path):
    store, _, _, _ = original(tmp_path)
    correction.prepare(store, SPEC, root=tmp_path / "posts")
    with pytest.raises(ValueError, match="CORRECTION_KEY_HOLDS_ANOTHER_SPEC"):
        correction.prepare(store, {**SPEC, "body": SPEC["body"] + " Changed."}, root=tmp_path / "posts")
    with pytest.raises(ValueError, match="CORRECTION_DESTINATIONS_UNSUPPORTED"):
        correction.prepare(store, {**SPEC, "key": "correction-reply-x", "destinations": ["x"]}, root=tmp_path / "posts")
    with pytest.raises(ValueError, match="CORRECTION_KEY_PREFIX_REQUIRED"):
        correction.prepare(store, {**SPEC, "key": "plan-result-post-x"}, root=tmp_path / "posts")


def test_a_changed_retained_chart_or_text_is_refused(tmp_path):
    store, _, _, _ = original(tmp_path)
    correction.prepare(store, SPEC, root=tmp_path / "posts")
    row = posts._row_payload(store, SPEC["key"])
    with pytest.raises(ValueError, match="CORRECTION_SUPPLIED_TEXT_OR_PARENT_CHANGED"):
        correction.validate(store, {**row, "text": row["text"] + " Extra."})
    with open(row["retained_chart"]["path"], "ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError, match="CORRECTION_ORIGINAL_CHART_CHANGED"):
        correction.validate(store, row)


def test_the_cc646_row_keeps_its_own_module():
    from live_contentops import plan_result_correction_cc646 as cc646
    assert posts._correction_module({"correction_reply_contract": cc646.CONTRACT}) is cc646
    assert posts._correction_module({"correction_reply_contract": correction.CONTRACT}) is correction
