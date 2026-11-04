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
