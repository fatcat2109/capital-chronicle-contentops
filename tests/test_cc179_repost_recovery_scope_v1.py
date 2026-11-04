"""A replacement's readback stays owed without inventing another canonical."""
import json
import pytest

from test_repost_after_removal_cc247 import _setup
from test_publication_coordinator_v1 import _plan


@pytest.mark.parametrize("fault", [None, "article", "record", "canonical"])
def test_replacement_uses_bound_original_canonical_and_new_article_continues(tmp_path, fault):
    store, co, transport, original = _setup(tmp_path, "instagram_business")
    original_intent = json.loads(store.get_outbox_message(original["message_id"])["payload"])
    canonical = co._ids("sec", original_intent["plan_hash"], "substack")
    co.readback_existing_dispatch(canonical["dispatch_id"])
    result = co.complete_dated_distribution_recovery(original["message_id"],
        review_reference={"request_sha256": "a" * 64})
    replacement = store.get_platform_dispatch(result["repost_dispatch_id"])
    message = store.get_outbox_message(replacement["message_id"])
    payload = json.loads(message["payload"])
    if fault == "article":
        payload["article_identity"] = "wrong-article"
    if fault == "record":
        payload["repost_record"] = "missing-record"
    if fault in {"article", "record"}:
        with store.get_connection() as conn:
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
                         (json.dumps(payload), message["message_id"]))
    if fault == "canonical":
        store.set_dispatch_status(canonical["dispatch_id"], "UNKNOWN_WRITE")
    co.allow_prior_confirmed_distribution = True
    recovery = {"backlog_remaining": 1, "backlog_remaining_obligations": [
        {"work_item_id": "sec", "destination": "instagram_business"}]}
    plan = _plan("substack")
    plan.update(plan_hash="next-plan", article_identity="next-article", story_identity="next-story")
    assert co.recovery_blocks_new_publication(recovery, "next", plan=plan) is (fault is not None)
    if fault is None:
        store.create_work_item(work_item_id="next", story_id="next", title="Next", target_surface="TEST")
        store.set_reconciliation_status(co._ids("sec", payload["plan_hash"], "instagram_business")["reconciliation_id"],
                                        "RECONCILIATION_PENDING")
        before = list(transport.publish_calls)
        outcome = co.execute_plan("next", plan)
        assert outcome["canonical_article_real_published"] is True
        assert transport.publish_calls == before + ["substack"]
        assert store.get_platform_dispatch(original["dispatch_id"])["status"] == "EXTERNAL_REMOVAL_REPORTED_NO_RETRY"
