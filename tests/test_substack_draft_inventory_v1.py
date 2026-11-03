import csv
import json
import sqlite3
from contextlib import closing

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.substack_draft_inventory_v1 import (
    draft_id_from_url, filter_referenced_drafts, inventory_rows, referenced_draft_ids,
    store_draft_ids, write_inventory,
)


def store_with_draft(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(story_id="story", work_item_id="work", title="Same title", target_surface="test")
    store.register_outbox_message(message_id="message", work_item_id="work", destination="substack",
                                 payload=json.dumps({"destination": "substack"}))
    store.register_platform_dispatch(dispatch_id="dispatch", message_id="message", platform="substack",
        status="OWNER_RETAINED_DRAFT_NO_PUBLISH", public_object_id="123")
    return store


def intent():
    return {"work_item_id": "work", "package_identity": "pkg", "payload": "Same title",
            "destination_plan": {"payload_hash": "hash", "surface": "SUBSTACK_ARTICLE"}}


def draft(draft_id):
    return {"id": draft_id, "title": "Same title", "created_at": "2026-09-01T22:16:07.352Z",
            "last_edited_at": "2026-09-02T01:00:00Z", "is_published": False}


def test_readback_ignores_unreferenced_draft_even_with_identical_title(tmp_path):
    store = store_with_draft(tmp_path)
    calls = []
    adapter = NeoDestinationHandoff(store=store, native_executor=lambda request: calls.append(request))
    result = adapter.readback(destination="substack", intent=intent(), public_object_id="999",
        public_object_url="https://capitalchronicle.substack.com/publish/post/999")
    assert calls == []
    assert result["reason_code"] == "UNREFERENCED_SUBSTACK_DRAFT_IGNORED"
    assert result["verified"] is False and result["write_absent"] is False
    assert filter_referenced_drafts([draft("999"), draft("123")], store_draft_ids(store)) == [draft("123")]
    assert store.get_platform_dispatch("dispatch")["status"] == "OWNER_RETAINED_DRAFT_NO_PUBLISH"


def test_referenced_draft_and_exact_public_readback_remain_available(tmp_path):
    store = store_with_draft(tmp_path)
    calls = []
    def executor(request):
        calls.append(request)
        return {"request_sha256": request["request_sha256"], "observed_identity": "capitalchronicle.substack.com"}
    adapter = NeoDestinationHandoff(store=store, native_executor=executor)
    for url in ("https://capitalchronicle.substack.com/publish/post/123",
                "https://capitalchronicle.substack.com/p/article"):
        adapter.readback(destination="substack", intent=intent(), public_object_id="123", public_object_url=url)
    assert len(calls) == 2
    scope = calls[0]["draft_readback_scope"]
    assert scope["referenced_draft_ids"] == ["123"]
    assert scope["scan_unreferenced_drafts"] is False
    assert "UNKNOWN_WRITE" in scope["instructions"]


def test_existing_native_composition_passes_store_to_scan_scope(tmp_path):
    store = store_with_draft(tmp_path)
    coordinator, _ = bind_native_neo_coordinator(store, operation_id="op", output_dir=tmp_path,
                                                native_invocation_id="test")
    adapter = coordinator.transport_runtime._neo_transport
    request = adapter.request(destination="substack", action="READBACK", intent=intent())
    assert request["draft_readback_scope"]["referenced_draft_ids"] == ["123"]


def test_pending_native_results_and_readbacks_count_as_references_without_cross_channel_ids(tmp_path):
    store = store_with_draft(tmp_path)
    store.register_readback(readback_id="rb", dispatch_id="dispatch", readback_data=json.dumps({
        "readback": {"draft_id": "124", "url": "https://capitalchronicle.substack.com/publish/post/125"}}))
    for number, value in enumerate([
        {"request": {"destination": "substack", "public_object_id": "126", "request_sha256": "req"},
         "tool_request_sha256": "h"},
        {"result": {"observed_identity": "capitalchronicle.substack.com", "draft_id": "127"}},
        {"result": {"request_sha256": "req", "draft_id": "128"}},
        {"request": {"destination": "x", "public_object_id": "999"}},
        {"result": {"observed_identity": "@Capitalnicle", "public_object_id": "998"}},
    ]):
        store.register_outbox_message(message_id=f"native-{number}", work_item_id="work",
            destination="internal:native-neo-tool", payload=json.dumps(value))
    assert store_draft_ids(store) == {"123", "124", "125", "126", "127", "128"}
    assert draft_id_from_url("https://other.substack.com/publish/post/999") is None


def test_inventory_writes_complete_csv_preserves_dates_and_never_mutates_store(tmp_path):
    store = store_with_draft(tmp_path)
    before = store.db_path.read_bytes()
    batches = [{"offset": 0, "total": 2, "rows": [draft("999"), draft("123")]}]
    output = tmp_path / "drafts.csv"
    summary = write_inventory(batches=batches, store_path=store.db_path, output_path=output)
    assert summary["total_drafts"] == 2
    assert summary["store_referenced"] == 1 and summary["old_unreferenced"] == 1
    with output.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["classification"] == "OLD_UNREFERENCED"
    assert rows[1]["store_referenced"] == "true"
    assert rows[0]["created_at_utc"] == draft("999")["created_at"]
    assert rows[0]["last_edited_at_utc"] == draft("999")["last_edited_at"]
    assert store.db_path.read_bytes() == before
    with closing(store.get_read_only_connection()) as connection:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("DELETE FROM platform_dispatches")


@pytest.mark.parametrize("batches", [
    [], [{"offset": 0, "total": 2, "rows": [draft("123")]}],
    [{"offset": 1, "total": 1, "rows": [draft("123")]}],
    [{"offset": 0, "total": 1, "isCapped": True, "rows": [draft("123")]}],
    [{"offset": 0, "total": 2, "rows": [draft("123"), draft("123")]}],
    [{"offset": 0, "total": 1, "rows": [{**draft("123"), "is_published": True}]}],
])
def test_partial_duplicate_or_published_inventory_is_rejected(batches):
    with pytest.raises(ValueError, match="DRAFT_INVENTORY"):
        inventory_rows(batches)


def test_unreadable_store_is_not_classified_as_empty(tmp_path):
    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(sqlite3.OperationalError):
            referenced_draft_ids(connection)
    with pytest.raises(sqlite3.OperationalError):
        write_inventory(batches=[{"offset": 0, "total": 1, "rows": [draft("123")]}],
                        store_path=tmp_path / "absent.sqlite3", output_path=tmp_path / "drafts.csv")
    assert not (tmp_path / "absent.sqlite3").exists()
