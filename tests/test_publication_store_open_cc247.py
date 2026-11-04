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
