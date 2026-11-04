"""CC-247 point 3: an owner-approved repost after Jim deletes an X, Telegram or Discord post.

Local fixtures only: no provider, browser, model or production-store write.
"""
import json
from datetime import datetime, timezone

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import (
    DurablePublicationCoordinator, EXTERNAL_REMOVAL_REPORTED_NO_RETRY,
)
from test_publication_coordinator_v1 import _plan, FixtureTransport

CANONICAL = "https://capitalchronicle.substack.com/p/fixture-article-1"


class CapturingTransport(FixtureTransport):
    def __init__(self):
        super().__init__()
        self.sent = []

    def publish(self, *, destination, intent, authorization_context):
        self.sent.append(intent)
        return super().publish(destination=destination, intent=intent, authorization_context=authorization_context)


def _setup(tmp_path, destination="telegram", *, removed=True, verified=True):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(work_item_id="sec", story_id="sec", title="SEC", target_surface="test")
    transport = CapturingTransport()
    co = DurablePublicationCoordinator(store=store, transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"})
    plan = _plan("substack", destination)
    co.register_plan("sec", plan)
    canonical = co._ids("sec", plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=canonical["dispatch_id"], message_id=canonical["message_id"],
        platform="substack", status="DISPATCH_CONFIRMED", public_object_id="223408612", public_object_url=CANONICAL)
    store.register_reconciliation(reconciliation_id=canonical["reconciliation_id"], work_item_id="sec",
        status="RECONCILED_CONFIRMED")
    original = co._ids("sec", plan["plan_hash"], destination)
    intent = json.loads(store.get_outbox_message(original["message_id"])["payload"])
    intent["canonical_url"] = CANONICAL
    store.finalize_outbox_payload_before_dispatch(message_id=original["message_id"], payload=json.dumps(intent),
        status="DISPATCH_CONFIRMED")
    store.register_platform_dispatch(dispatch_id=original["dispatch_id"], message_id=original["message_id"],
        platform=destination, status="DISPATCH_CONFIRMED", public_object_id="75",
        public_object_url="https://t.me/CapitalChronicle/75")
    if removed:
        co.reconcile_owner_removed_object(original["dispatch_id"], disposition=EXTERNAL_REMOVAL_REPORTED_NO_RETRY,
            observation={"destination": destination, "public_object_id": "75",
                "authority_ref": "Jim, 4 Nov ~21:05 GMT+7, via Ops", "observation_ref": "controlled-fixture",
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "observation_basis": "PUBLIC_PAGE_ABSENT", "exact_object_absence_verified": verified})
    reviewed = {**intent, "native_payload": {"text": "Reviewed copy with the new card " + CANONICAL,
        "media_asset_ids": ["sec-card-cc245"]}, "payload": "Reviewed copy with the new card " + CANONICAL,
        "media_assets": [{"asset_id": "sec-card-cc245", "sha256": "c" * 64}],
        "reader_presentation_review": {"request_sha256": "a" * 64}}
    co._reader_presentation_intent = lambda message, reference: (
        {**reviewed, "reader_presentation_review": reference}, {}, {}, {})
    return store, co, transport, original


@pytest.mark.parametrize("destination", ["x", "telegram", "discord"])
def test_repost_goes_once_under_its_own_dispatch_and_reads_back(tmp_path, destination):
    store, co, transport, original = _setup(tmp_path, destination)
    message_id = original["message_id"]
    ref = {"request_sha256": "a" * 64}
    outcome = co.repost_after_owner_removal(message_id, review_reference=ref)
    assert outcome["publish_called"] is True and transport.publish_calls == [destination]
    assert outcome["repost_dispatch_id"] != original["dispatch_id"]
    repost = store.get_platform_dispatch(outcome["repost_dispatch_id"])
    assert repost and repost["status"] == "DISPATCH_CONFIRMED"
    assert destination in transport.readback_calls
    sent = transport.sent[0]
    assert sent["native_payload"]["text"].startswith("Reviewed copy with the new card")
    assert sent["media_assets"][0]["asset_id"] == "sec-card-cc245"
    assert sent["repost_of_dispatch_id"] == original["dispatch_id"]
    # The deleted object's own dispatch and history stay as recorded.
    assert store.get_platform_dispatch(original["dispatch_id"])["status"] == EXTERNAL_REMOVAL_REPORTED_NO_RETRY
    # Nothing goes out twice: the same review reads back only; a new review is refused.
    again = co.repost_after_owner_removal(message_id, review_reference=ref)
    assert again["status"] == "REPOST_ALREADY_ATTEMPTED_READBACK_ONLY" and again["publish_called"] is False
    with pytest.raises(ValueError, match="REPOST_IMMUTABLE_REVIEW_CONFLICT"):
        co.repost_after_owner_removal(message_id, review_reference={"request_sha256": "b" * 64})
    assert transport.publish_calls == [destination]


@pytest.mark.parametrize("removed,verified", [(False, True), (True, False)])
def test_repost_needs_jims_recorded_removal_with_verified_absence(tmp_path, removed, verified):
    _, co, transport, original = _setup(tmp_path, removed=removed, verified=verified)
    with pytest.raises(ValueError, match="REPOST_VERIFIED_OWNER_REMOVAL_REQUIRED"):
        co.repost_after_owner_removal(original["message_id"], review_reference={"request_sha256": "a" * 64})
    assert transport.publish_calls == []


def test_repost_path_is_only_for_x_telegram_and_discord(tmp_path):
    _, co, transport, original = _setup(tmp_path, "facebook_page")
    with pytest.raises(ValueError, match="REPOST_EXACT_ORIGINAL_DESTINATION_REQUIRED"):
        co.repost_after_owner_removal(original["message_id"], review_reference={"request_sha256": "a" * 64})
    assert transport.publish_calls == []


def test_repost_refuses_a_changed_canonical(tmp_path):
    _, co, transport, original = _setup(tmp_path)
    reviewed, *_ = co._reader_presentation_intent(None, {"request_sha256": "a" * 64})
    co._reader_presentation_intent = lambda message, reference: (
        {**reviewed, "canonical_url": "https://capitalchronicle.substack.com/p/other"}, {}, {}, {})
    with pytest.raises(ValueError, match="CANONICAL_IDENTITY_CHANGED"):
        co.repost_after_owner_removal(original["message_id"], review_reference={"request_sha256": "a" * 64})
    assert transport.publish_calls == []


@pytest.mark.parametrize("destination", ["facebook_page", "instagram_business", "youtube", "linkedin"])
def test_dated_route_reposts_verified_removed_object_with_reviewed_media(tmp_path, destination):
    store, co, transport, original = _setup(tmp_path, destination)
    outcome = co.complete_dated_distribution_recovery(original["message_id"],
        review_reference={"request_sha256": "a" * 64})
    assert outcome["publish_called"] is True
    assert outcome["repost_dispatch_id"] != original["dispatch_id"]
    assert transport.sent[0]["native_payload"]["media_asset_ids"] == ["sec-card-cc245"]
    assert store.get_platform_dispatch(outcome["repost_dispatch_id"])["status"] == "DISPATCH_CONFIRMED"
    again = co.complete_dated_distribution_recovery(original["message_id"],
        review_reference={"request_sha256": "a" * 64})
    assert again["publish_called"] is False and transport.publish_calls == [destination]
