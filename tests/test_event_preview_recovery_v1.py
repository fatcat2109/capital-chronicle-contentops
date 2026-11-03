"""A prior derivative gap must not suppress private event-preview preparation."""
from tests.test_native_finished_publication_v1 import ready  # noqa: F401
from tests.test_native_desktop_publication_v1 import composed, finish
from tests.test_native_newsroom_owner_operation_v1 import entry
from live_contentops.native_finished_publication_v1 import release_finished_piece
from live_contentops.native_desktop_workspace_v1 import workspace_snapshot


def test_preparation_reuses_coordinator_policy_without_changing_recovery(ready, monkeypatch):  # noqa: F811
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, _ = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    with target.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET status='UNKNOWN_WRITE' WHERE platform='linkedin'")
    before = workspace_snapshot(target.db_path)
    binding = {"run_id": "distinct-preview", "owner_manual_live": True, "store_path": str(target.db_path)}
    module = entry()
    assert module.editorial_recovery_blockers(target, binding) == []
    assert module.editorial_recovery_blockers(target, {**binding, "owner_manual_live": False})
    assert module.editorial_recovery_blockers(target, {**binding, "run_id": released["binding"]["run_id"]})
    assert workspace_snapshot(target.db_path) == before
    with target.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET status='UNKNOWN_WRITE' WHERE platform='substack'")
    assert module.editorial_recovery_blockers(target, binding)
