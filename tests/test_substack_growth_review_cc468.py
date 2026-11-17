from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json

import pytest

from live_contentops.substack_growth_review_v1 import report, acquisition_snapshot
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops import plan_analysis_pages_v1 as pages
from test_plan_analysis_distribution_cc435 import confirm


def test_seven_days_requires_real_coordinator_reconciliation_and_unknown_is_not_zero(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    start = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
    for i in range(7):
        day = (start + timedelta(days=i)).date().isoformat()
        key = "substack-daily-note-" + day
        value = {"kind": "daily_note", "link_id": key, "day_et": day, "destination": "substack_notes",
                 "plan": {"plan_hash": str(i) * 64}, "source_clock": {"data_cutoff_utc": start.isoformat()}}
        store.create_work_item(story_id=key, work_item_id=key, title="Note", target_surface="SUBSTACK_NOTE")
        store.register_outbox_message(message_id=key, work_item_id=key, destination=pages.DESTINATION,
                                      payload=json.dumps(value), status="EDITORIAL_INTERNAL")
        if i < 6:
            confirm(store, key, value["plan"]["plan_hash"], "substack_notes", "c-" + str(i),
                    "https://substack.com/@capitalchronicle/note/c-" + str(i))
    result = report(store, now=start + timedelta(days=16))
    assert result["confirmed_note_count"] == 6 and result["seven_day_note_readbacks"] is False
    assert result["new_free_subscribers_by_source"] is None
    assert result["fourteen_day_review_due"] is True
    assert result["decision_state"] == "REVIEW_DUE"
    assert all(row["observed_publication_at_utc"] is None for row in result["notes"])
    key = value["link_id"]
    confirm(store, key, value["plan"]["plan_hash"], "substack_notes", "c-6",
            "https://substack.com/@capitalchronicle/note/c-6")
    assert report(store, now=start + timedelta(days=16))["seven_day_note_readbacks"] is True


def test_first_party_source_table_feeds_the_fourteen_day_comparison_with_bound_counts(tmp_path):
    readback = tmp_path / "visible-source-table.txt"
    readback.write_text("New free subscribers\nSubstack network: 12\nDirect: unavailable\n", encoding="utf-8")
    observation = {"source_url": "https://capitalchronicle.substack.com/publish/stats",
        "period_start_utc": "2026-11-12T05:00:00Z", "period_end_utc": "2026-11-26T05:00:00Z",
        "observed_at_utc": "2026-11-26T12:00:00Z", "readback_path": str(readback),
        "readback_sha256": sha256(readback.read_bytes()).hexdigest(), "sources": [
            {"source": "Substack network", "new_free_subscribers": 12, "display": "12",
             "availability": "AVAILABLE", "excerpt": "Substack network: 12"},
            {"source": "Direct", "new_free_subscribers": None, "availability": "NOT_EXPOSED"}]}
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = report(store, acquisition_observation=observation)
    assert result["new_free_subscribers_by_source"][0]["by_source"] == [
        {"source": "Substack network", "new_free_subscribers": 12, "availability": "AVAILABLE"},
        {"source": "Direct", "new_free_subscribers": None, "availability": "NOT_EXPOSED"}]
    observation["sources"][0]["new_free_subscribers"] = 13
    with pytest.raises(ValueError, match="COUNT_UNBOUND"):
        acquisition_snapshot(observation)


def test_review_cli_uses_query_only_connections_and_keeps_the_store_bytes(tmp_path):
    import gc
    import sqlite3
    from scripts.substack_growth import main, ReadOnlyStore
    path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(path)
    gc.collect()
    before = path.read_bytes()
    assert main(["report", "--store", str(path), "--out", str(tmp_path / "review")]) == 0
    value = json.loads((tmp_path / "review/report-result.json").read_bytes())
    assert value["decision_state"] == "NOT_STARTED" and value["new_free_subscribers_by_source"] is None
    assert path.read_bytes() == before
    with ReadOnlyStore(path, auto_migrate=False).get_connection() as connection:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE must_not_write (id INTEGER)")
