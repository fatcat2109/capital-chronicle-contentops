"""Already-migrated publication resumes avoid repeating a full production DB scan."""
from scripts import run_native_desktop_editorial as entry


def test_registered_publication_checks_migration_hashes_without_integrity_scan(tmp_path, monkeypatch):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(path)
    monkeypatch.setattr(ContentOpsDurableStore, "run_migrations",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("repeated full migration/integrity scan")))
    opened = entry._bound_store({"store_path": str(path)}, "publication-reader-derivative")
    assert opened.get_current_schema_version() > 0
    opened.verify_applied_migrations()


def test_bound_publication_indexes_exact_artifact_and_destination_reads(tmp_path):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(path)
    version = store.get_current_schema_version()
    # A status read does not install indexes or change canonical records.
    entry._bound_store({"store_path": str(path)}, "status")
    with store.get_read_only_connection() as conn:
        assert not conn.execute("SELECT name FROM sqlite_master WHERE name LIKE 'idx_outbox_%_read'").fetchall()
    opened = entry._bound_store({"store_path": str(path)}, "publication-tool-begin")
    entry._bound_store({"store_path": str(path)}, "publication-tool-begin")
    with opened.get_read_only_connection() as conn:
        artifact = conn.execute("EXPLAIN QUERY PLAN SELECT payload FROM outbox_messages "
            "WHERE work_item_id=? AND destination=? ORDER BY rowid DESC", ("work", "internal:source")).fetchall()
        destination = conn.execute("EXPLAIN QUERY PLAN SELECT rowid FROM outbox_messages "
            "WHERE destination=? ORDER BY created_at,message_id", ("internal:native-neo",)).fetchall()
        assert any("idx_outbox_work_destination_read" in r[3] for r in artifact)
        assert any("idx_outbox_destination_order_read" in r[3] for r in destination)
        assert conn.execute("SELECT count(*) FROM outbox_messages").fetchone()[0] == 0
    assert opened.get_current_schema_version() == version
    assert opened.verify_applied_migrations()


def test_atomic_publication_step_does_not_rescan_the_whole_production_day(monkeypatch):
    from types import SimpleNamespace
    store = SimpleNamespace(acquire_lease=lambda *a, **kw: {"lease_id": "fixture", "fencing_token": 1},
        release_lease=lambda *a: None)
    monkeypatch.setattr(entry, "validate_binding", lambda *a, **kw: None)
    monkeypatch.setattr(entry, "_bound_store", lambda *a: store)
    monkeypatch.setattr(entry, "_operation", lambda *a, **kw: {"classification": "NATIVE_NEO_ACTION_BEGUN"})
    monkeypatch.setattr("live_contentops.native_newsroom_volume_v1.persist_native_day_measurement",
        lambda *a: (_ for _ in ()).throw(AssertionError("whole-day rescan before the next browser step")))
    result = entry.operation({"run_id": "fixture", "owner_manual_validation": True, "owner_manual_live": True},
        command="publication-tool-begin")
    assert result["classification"] == "NATIVE_NEO_ACTION_BEGUN"


def test_live_projection_retains_current_edition_without_loading_other_editions(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded
    from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
    store, binding, *_ = seeded(tmp_path, monkeypatch)
    publication = NativeReviewedPublication(store, binding, native_invocation_id="controlled")
    before = publication.projection()
    store.create_work_item(story_id="unrelated", work_item_id="unrelated", title="Other edition", target_surface="TEST")
    store.register_outbox_message(message_id="unrelated-retained-media", work_item_id="unrelated",
        destination="internal:old-media", payload='{"retained_media":"' + "x" * 100000 + '"}', status="EDITORIAL_INTERNAL")
    original = store.list_outbox_messages
    def scoped_only(**kwargs):
        assert kwargs.get("work_item_id") or kwargs.get("destination"), "unbounded historical payload scan"
        return original(**kwargs)
    monkeypatch.setattr(store, "list_outbox_messages", scoped_only)
    assert publication.projection() == before
