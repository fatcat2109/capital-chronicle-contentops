"""Editorial preparation can progress while public dispatch remains serialized."""
import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_native_newsroom_owner_operation_v1 import entry


@pytest.mark.parametrize("command", ["advance", "publication-resume"])
def test_other_public_worker_only_serializes_public_dispatch(tmp_path, monkeypatch, command):
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    other = store.acquire_lease("pinned-result-scorecard-v1", "controlled-other", ttl_seconds=900)
    module = entry()
    monkeypatch.setattr(module, "validate_binding", lambda *a, **k: None)
    monkeypatch.setattr(module, "_bound_store", lambda *a: store)
    monkeypatch.setattr("live_contentops.native_newsroom_volume_v1.bound_volume_policy", lambda _: None)
    calls = []
    def prepare(binding, **kwargs):
        calls.append(kwargs["operation_lease"]["lease_id"])
        return {"classification": "EDITORIAL_PREPARED", "public_write_performed": False}
    monkeypatch.setattr(module, "_operation", prepare)
    binding = {"run_id": "controlled-cpi", "store_path": str(store.db_path)}
    try:
        if command == "publication-resume":
            with pytest.raises(ValueError, match="NEWSROOM_LEASE_ACTIVE:pinned-result-scorecard-v1"):
                module.operation(binding, command=command)
            assert calls == []
        else:
            result = module.operation(binding, command=command)
            assert result["classification"] == "EDITORIAL_PREPARED" and len(calls) == 1
        with store.get_read_only_connection() as conn:
            assert conn.execute("SELECT status FROM leases WHERE lease_id=?", (other["lease_id"],)).fetchone()[0] == "ACTIVE"
    finally:
        store.release_lease(other["lease_id"], "controlled-other", other["fencing_token"])
