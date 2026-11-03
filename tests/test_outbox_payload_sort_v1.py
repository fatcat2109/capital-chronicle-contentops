"""Large retained payloads never enter the SQLite ordering temporary table."""
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def test_outbox_orders_and_filters_exact_rows_without_sorting_payloads(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    store.create_work_item(story_id="fixture", work_item_id="fixture", title="Fixture", target_surface="TEST")
    for identity, status in [("z", "ONE"), ("a", "ONE"), ("m", "TWO")]:
        store.register_outbox_message(message_id=identity, work_item_id="fixture", destination="internal:fixture",
            payload="retained fixture text " * 10000, status=status)
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET created_at=?", ("2026-11-03T00:00:00Z",))
        expected = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY created_at,message_id")]
    calls = []
    original = store.get_connection

    def connection():
        conn = original()
        conn.set_trace_callback(calls.append)
        return conn

    monkeypatch.setattr(store, "get_connection", connection)
    assert store.list_outbox_messages() == expected
    assert store.list_outbox_messages(status="ONE") == [r for r in expected if r["status"] == "ONE"]
    assert store.list_outbox_messages(status="MISSING") == []
    ordered_queries = [q.upper() for q in calls if "ORDER BY" in q.upper()]
    assert ordered_queries and all("SELECT ROWID" in q and "PAYLOAD" not in q for q in ordered_queries)
    assert sum(q == "BEGIN" for q in calls) == 3
