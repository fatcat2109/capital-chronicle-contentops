"""A dropped Note link is repaired once as a reply, without editing the call."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from live_contentops import call_followups_v1 as f
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.publication_image_contract_v1 import validate_write
from test_call_followups_cc603 import ready, candidate, bars, NOW
from test_plan_status_publication_cc306 import fake_host


@pytest.fixture
def parent(ready):
    store, transport, coordinator, record = ready
    hit = candidate()
    key = f.queue_followup(store, hit, f.check_path(hit, bars()), record, now=NOW)["key"]
    row = posts._row_payload(store, key)
    for destination in row["cc603_destinations"]:
        identity = "dispatch_" + key + "_" + destination
        message = "message_" + identity
        object_id = "c-603" if destination == "substack_notes" else "603"
        url = "https://substack.com/@capitalchronicle/note/c-603" if destination == "substack_notes" else "https://t.me/CapitalChronicle/603"
        store.register_outbox_message(message_id=message, work_item_id=key, destination=destination, payload="{}")
        store.register_platform_dispatch(dispatch_id=identity, message_id=message, platform=destination,
            status="DISPATCH_CONFIRMED", public_object_id=object_id, public_object_url=url)
        store.register_reconciliation(reconciliation_id="reconciliation_" + identity.removeprefix("dispatch_"),
            work_item_id=key, status="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE" if destination == "substack_notes" else "RECONCILED_CONFIRMED")
        if destination == "substack_notes":
            dispatch = identity
            store.register_readback(readback_id="parent-readback", dispatch_id=identity, readback_data=json.dumps({
                "readback": {"write_exists": True, "identity_match": True, "meaningful_media_visible": True,
                    "observed_public_object_id": object_id, "observed_public_object_url": url,
                    "content_binding_checks": {"text_match": False, "media_match": True, "thread_match": True}}}))
    text = f.destination_payloads(row, card_id="parent-chart", chart_credit=True)["substack_notes"]["full_text"]
    text = text.replace(hit["original_url"], "").replace(record["url"], "")
    store.set_outbox_status(key, "SETTLED")
    return store, transport, coordinator, row, text, dispatch


def test_missing_links_use_one_real_coordinator_reply_and_preserve_the_issued_note(parent, tmp_path, monkeypatch):
    store, transport, coordinator, original, observed, dispatch = parent
    before = store.get_outbox_message(original["key"])["payload"]
    queued = f.queue_missing_links_reply(store, original["key"], observed_text=observed, now=NOW)
    assert queued["status"] == "QUEUED"
    assert f.queue_missing_links_reply(store, original["key"], observed_text=observed)["status"] == "EXISTING"
    assert not f.post_complete(store, original)
    monkeypatch.setattr(f, "discover", lambda *a: [])
    monkeypatch.setattr(f, "article_candidates", lambda *a: ([], []))
    def unavailable_export():
        raise AssertionError("an owed link reply does not need a fresh Main plan")
    def no_image(*args):
        raise AssertionError("the original Note already carries its reviewed chart")
    f.minute_due(store, unavailable_export, now=NOW, root=tmp_path / "posts", host=fake_host,
        coordinator_for=lambda *a: coordinator, asset_for=no_image)
    child = posts._row_payload(store, queued["key"])
    intents = [json.loads(r["payload"]) for r in store.list_outbox_messages(work_item_id=child["key"])
               if r["destination"] == "substack_notes"]
    assert len(intents) == 1
    intent = intents[0]
    payload = intent["native_payload"]
    assert payload["reply_to_id"] == "c-603"
    assert payload["reply_to_url"] == "https://substack.com/@capitalchronicle/note/c-603"
    assert not payload["media_asset_ids"]
    assert original["candidate"]["original_url"] in payload["text"] and original["record"]["url"] in payload["text"]
    assert f.post_complete(store, original) and store.get_outbox_message(original["key"])["status"] == "PUBLISHED"
    assert store.get_outbox_message(original["key"])["payload"] == before
    assert store.get_platform_dispatch(dispatch)["public_object_id"] == "c-603"
    rec = next(r for r in store.get_reconciliations_for_work_item(original["key"])
               if r["reconciliation_id"] == "reconciliation_" + dispatch.removeprefix("dispatch_"))
    assert rec["status"] == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
    f.run_due(store, {"status": {"plans": []}}, now=NOW, root=tmp_path / "posts",
        coordinator_for=lambda *a: coordinator, host=fake_host, asset_for=no_image)
    assert transport.publish_calls == ["substack_notes"]
    coordinator._clock = lambda: datetime(2026, 11, 17, tzinfo=timezone.utc)
    assert validate_write(coordinator, intent, "substack_notes")["policy"] == "CC603_MISSING_LINK_REPLY"
    changed = deepcopy(intent)
    changed["native_payload"]["reply_to_id"] = "c-604"
    with pytest.raises(ValueError, match="CC603_LINK_REPLY_COPY_OR_PARENT_CHANGED"):
        validate_write(coordinator, changed, "substack_notes")


def test_a_missing_analytical_sentence_cannot_be_replaced_by_a_link_reply(parent):
    store, _, _, original, observed, _ = parent
    with pytest.raises(ValueError, match="CC603_LINK_REPLY_OTHER_CONTENT_MISSING"):
        f.queue_missing_links_reply(store, original["key"], observed_text=observed.replace("The entry zone traded before the move.", ""))
    assert store.get_outbox_message(original["key"] + "-missing-links") is None


@pytest.mark.parametrize("failure", ["identity", "media", "thread", "object"])
def test_a_link_reply_requires_exact_illustrated_parent_evidence(parent, failure):
    store, _, _, original, observed, dispatch = parent
    proof = json.loads(store.list_readbacks_for_dispatch(dispatch)[-1]["readback_data"])
    readback = proof["readback"]
    if failure == "object":
        readback["observed_public_object_id"] = "c-604"
    elif failure == "identity":
        readback["identity_match"] = False
    else:
        readback["content_binding_checks"][failure + "_match"] = False
    store.register_readback(readback_id="bad-parent-readback", dispatch_id=dispatch, readback_data=json.dumps(proof))
    with pytest.raises(ValueError, match="CC603_LINK_REPLY_ILLUSTRATED_PARENT_READBACK_REQUIRED"):
        f.queue_missing_links_reply(store, original["key"], observed_text=observed)


def test_a_changed_reply_does_not_complete_the_parent(parent):
    store, _, _, original, observed, _ = parent
    queued = f.queue_missing_links_reply(store, original["key"], observed_text=observed)
    reply = posts._row_payload(store, queued["key"])
    reply["text"] += " Extra claim."
    with pytest.raises(ValueError, match="CC603_LINK_REPLY_COPY_CHANGED"):
        f.validate_link_reply(store, reply)
    assert not f.post_complete(store, original)
