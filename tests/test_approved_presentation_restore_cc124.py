import json
from types import SimpleNamespace

import pytest

from live_contentops.approved_presentation_restore_v1 import restore_intent
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.neo_destination_handoff_v1 import _text


def test_original_copy_and_media_reach_live_edit_and_current_review(monkeypatch):
    original = {"work_item_id": "run", "native_payload": {"title": "exact", "body_markdown": "facts"},
        "media_assets": [{"asset_id": "photo", "source_page_url": "https://commons.wikimedia.org/wiki/File:X_(1).jpg"}]}
    calls = []
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.require_current_final_visual_review",
        lambda store, **kw: calls.append(kw))
    store = SimpleNamespace(get_platform_dispatch=lambda _: {"platform": "substack", "status": "DISPATCH_CONFIRMED",
        "message_id": "message", "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/exact"},
        get_outbox_message=lambda _: {"destination": "substack", "payload": json.dumps(original)})
    restored = restore_intent(store, "dispatch")
    assert calls == [{"run_id": "run"}]
    assert restored["native_payload"] == original["native_payload"]
    assert restored["media_assets"] == original["media_assets"]
    assert restored["approved_presentation_restore"]["original_intent_sha256"] == sha256_of(original)


@pytest.mark.parametrize("platform,status", [("youtube", "DISPATCH_CONFIRMED"), ("substack", "UNKNOWN_WRITE")])
def test_restore_does_not_create_or_retry_another_object(platform, status):
    store = SimpleNamespace(get_platform_dispatch=lambda _: {"platform": platform, "status": status},
        get_outbox_message=lambda _: {})
    with pytest.raises(ValueError, match="EXACT_CONFIRMED_SUBSTACK"):
        restore_intent(store, "dispatch")


def test_commons_parentheses_are_one_link_in_public_caption_comparison():
    assert _text("Photo: [Federalreserve](https://commons.wikimedia.org/wiki/File:Eccles_Building_(26088200676).jpg).") == "Photo: Federalreserve."


@pytest.mark.parametrize("changed", [False, True])
def test_live_readback_consumes_restore_but_refuses_changed_proof(monkeypatch, changed):
    from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
    original = {"work_item_id": "run"}
    dispatch = {"dispatch_id": "d", "message_id": "m", "platform": "substack", "status": "DISPATCH_CONFIRMED",
        "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/exact"}
    store = SimpleNamespace(get_platform_dispatch=lambda _: dispatch,
        get_dispatches_for_work_item=lambda _: [dispatch],
        get_outbox_message=lambda _: {"destination": "substack", "work_item_id": "run", "payload": json.dumps(original)})
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.require_current_final_visual_review", lambda *a, **kw: None)
    restored = restore_intent(store, "d")
    request = {"action": "READBACK", "destination": "substack", "work_item_id": "run", "public_object_id": "123",
        "intent_sha256": sha256_of(restored), "approved_presentation_restore": dict(restored["approved_presentation_restore"])}
    if changed:
        request["approved_presentation_restore"]["original_intent_sha256"] = "different"
    owner = NativeReviewedPublication.__new__(NativeReviewedPublication)
    owner.store, owner.binding = store, {"run_id": "run"}
    owner._authorize_and_bind = lambda: None
    owner.coordinator = SimpleNamespace(_effective_message=store.get_outbox_message)
    owner.executor = SimpleNamespace(_get=lambda *a: {"request": request}, begin=lambda h: {"begun": h})
    if changed:
        with pytest.raises(ValueError, match="EXACT_EXISTING_READBACK"):
            owner.tool("begin", request_hash="request")
    else:
        assert owner.tool("begin", request_hash="request") == {"begun": "request"}
