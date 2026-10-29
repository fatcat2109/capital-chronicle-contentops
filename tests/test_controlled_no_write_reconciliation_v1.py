"""Focused lifecycle controls: no fixture here is a real public publication."""
import hashlib
import json

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor
from live_contentops.publication_coordinator_v1 import (
    CONTROLLED_NO_PUBLIC_WRITE, RECONCILED_CONTROLLED_NO_WRITE, DurablePublicationCoordinator,
)


def fixture_chain(tmp_path, destination="substack", *, status="DISPATCH_CONFIRMED_NO_WRITE", typed=False,
                  actor_ref="controlled-fda-c-e2e"):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "editorial-window-controlled-fixture"
    store.create_work_item(work_item_id=work, story_id=work, title="Controlled fixture",
        target_surface="daily_app_editorial_window", actor_ref=actor_ref)
    payload = json.dumps({"window_id": work, "destination": destination,
        "package_identity": "controlled-fda-c-package-v1"}, sort_keys=True)
    suffix = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]
    message, dispatch, reconciliation = "outbox_" + suffix, "dispatch_" + suffix, "reconciliation_" + suffix
    store.register_outbox_message(message_id=message, work_item_id=work, destination=destination,
        payload=payload, status="READY")
    store.register_platform_dispatch(dispatch_id=dispatch, message_id=message, platform=destination, status=status)
    readback = {"dispatch_id": dispatch, "destination": destination, "verified": True}
    if typed:
        readback.update(verified=False, public_write_performed=False, readback_status=CONTROLLED_NO_PUBLIC_WRITE)
    store.register_readback(readback_id="original-" + suffix, dispatch_id=dispatch, readback_data=json.dumps(readback))
    store.register_reconciliation(reconciliation_id=reconciliation, work_item_id=work,
        status=RECONCILED_CONTROLLED_NO_WRITE if typed else "RECONCILED_CONFIRMED")
    return store, message, dispatch, reconciliation


@pytest.mark.parametrize("destination", ["substack", "telegram"])
@pytest.mark.parametrize("typed", [False, True])
def test_exact_terminal_fixture_reconciles_idempotently_without_transport(tmp_path, destination, typed):
    status = CONTROLLED_NO_PUBLIC_WRITE if typed else "DISPATCH_CONFIRMED_NO_WRITE"
    store, message, dispatch, reconciliation = fixture_chain(tmp_path, destination, status=status, typed=typed)
    unrelated = store.register_outbox_message(message_id="unrelated-pending", work_item_id=store.get_outbox_message(message)["work_item_id"],
        destination="telegram", payload="unrelated exact bytes", status="PENDING")
    original_message = store.get_outbox_message(message)
    original_dispatch = store.get_platform_dispatch(dispatch)
    original_readback = store.list_readbacks_for_dispatch(dispatch)[0]
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    result = coordinator.reconcile_controlled_no_write_dispatch(dispatch)
    after = store.get_outbox_message(message)
    assert after == {**original_message, "status": CONTROLLED_NO_PUBLIC_WRITE}
    assert store.get_platform_dispatch(dispatch) == original_dispatch
    assert original_readback in store.list_readbacks_for_dispatch(dispatch)
    assert len(store.list_readbacks_for_dispatch(dispatch)) == 2
    assert coordinator.reconcile_controlled_no_write_dispatch(dispatch) == result
    assert len(store.list_readbacks_for_dispatch(dispatch)) == 2
    assert result["provider_calls"] == 0 and result["publish_called"] is False
    assert result["real_publication"] is False and result["public_write_performed"] is False
    assert store.get_outbox_message("unrelated-pending") == unrelated
    assert next(r for r in store.get_reconciliations_for_work_item(after["work_item_id"])
                if r["reconciliation_id"] == reconciliation)["status"] == RECONCILED_CONTROLLED_NO_WRITE


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED", "NATIVE_NEO_TOOL_PENDING",
                                   "PENDING", "DISPATCH_CONFIRMED", "DEFINITE_NO_WRITE"])
def test_pending_ambiguous_or_real_dispatch_is_never_relabelled_as_fixture(tmp_path, status):
    store, message, dispatch, _ = fixture_chain(tmp_path, status=status)
    before = (store.get_outbox_message(message), store.get_platform_dispatch(dispatch), store.list_readbacks_for_dispatch(dispatch))
    with pytest.raises(ValueError, match="EXACT_TERMINAL_CONTROLLED"):
        DurablePublicationCoordinator(store=store, transport_runtime=None).reconcile_controlled_no_write_dispatch(dispatch)
    assert (store.get_outbox_message(message), store.get_platform_dispatch(dispatch), store.list_readbacks_for_dispatch(dispatch)) == before


@pytest.mark.parametrize("broken", ["object", "pending-reconciliation", "no-readback", "missing-controlled-lineage", "contradictory-readback"])
def test_missing_or_conflicting_evidence_preserves_ready_row(tmp_path, broken):
    store, message, dispatch, reconciliation = fixture_chain(tmp_path,
        actor_ref="fixture-without-controlled-lineage" if broken == "missing-controlled-lineage" else "controlled-fda-c-e2e")
    if broken == "object":
        store.register_platform_dispatch(dispatch_id=dispatch, message_id=message, platform="substack",
            status="DISPATCH_CONFIRMED_NO_WRITE", public_object_id="actual-object")
    elif broken == "pending-reconciliation":
        store.set_reconciliation_status(reconciliation, "RECONCILIATION_PENDING")
    elif broken == "contradictory-readback":
        store.register_readback(readback_id="contradiction", dispatch_id=dispatch,
            readback_data=json.dumps({"dispatch_id": dispatch, "destination": "substack", "public_write_performed": True}))
    elif broken == "no-readback":
        with store.get_connection() as conn:
            conn.execute("DELETE FROM readbacks WHERE dispatch_id=?", (dispatch,))
    before = (store.get_outbox_message(message), store.get_platform_dispatch(dispatch), store.list_readbacks_for_dispatch(dispatch))
    with pytest.raises(ValueError):
        DurablePublicationCoordinator(store=store, transport_runtime=None).reconcile_controlled_no_write_dispatch(dispatch)
    assert (store.get_outbox_message(message), store.get_platform_dispatch(dispatch), store.list_readbacks_for_dispatch(dispatch)) == before


@pytest.mark.parametrize("destination", ["substack", "telegram"])
def test_supervisor_resume_consumes_legacy_no_write_without_publisher(tmp_path, destination):
    store, message, _, _ = fixture_chain(tmp_path, destination)
    supervisor = ContentOpsDailyAppSupervisor(store_path=tmp_path / "state.sqlite3",
        output_root=tmp_path / "outputs", operating_mode="AUTONOMOUS_DEFAULT")
    result = supervisor.drive_canonical_publication_lifecycle(
        store.get_outbox_message(message)["work_item_id"], [destination], "controlled-fda-c-package-v1",
        publisher=lambda *_: pytest.fail("Terminal no-write must not invoke publisher"))
    assert result["confirmed_writes"] == 0 and result["public_write_performed"] is False
    assert result["per_destination"][destination]["resumed_terminal_no_write"] is True
    assert store.get_outbox_message(message)["status"] == CONTROLLED_NO_PUBLIC_WRITE


def test_new_controlled_lifecycle_closes_outbox_and_replay_never_publishes(tmp_path):
    supervisor = ContentOpsDailyAppSupervisor(store_path=tmp_path / "state.sqlite3",
        output_root=tmp_path / "outputs", operating_mode="AUTONOMOUS_DEFAULT")
    store = supervisor._store
    work = "editorial-window-new-controlled-fixture"
    store.create_work_item(work_item_id=work, story_id=work, title="Controlled fixture",
        target_surface="daily_app_editorial_window", actor_ref="controlled-lifecycle-test")
    first = supervisor.drive_canonical_publication_lifecycle(work, ["substack", "telegram"], "controlled-package",
        publisher=lambda *_: {"status": CONTROLLED_NO_PUBLIC_WRITE})
    assert first["confirmed_writes"] == 0 and first["public_write_performed"] is False
    assert all(row["status"] == CONTROLLED_NO_PUBLIC_WRITE for row in store.list_outbox_messages())
    second = supervisor.drive_canonical_publication_lifecycle(work, ["substack", "telegram"], "controlled-package",
        publisher=lambda *_: pytest.fail("Controlled replay must not invoke publisher"))
    assert second["confirmed_writes"] == 0 and second["public_write_performed"] is False
    assert all(row["resumed_terminal_no_write"] for row in second["per_destination"].values())
