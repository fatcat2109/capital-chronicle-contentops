"""CC-268: passive readiness states are return-only, and the store names a state it cannot hold.

The destination_readiness table's CHECK holds ten states; STALE_NEEDS_JIT_VERIFICATION and
LAST_VERIFIED_READY are passive states that only the read model returns.
"""
import sqlite3

import pytest

from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager, TIER1_SURFACES
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore, DESTINATION_READINESS_STATES, PERSISTABLE_DESTINATION_READINESS_STATES,
)


def _row(state):
    return {"surface": "X_POST", "platform": "x", "transport_registry_version": "v1",
            "transport_type": "BROWSEROS_NEO_MCP", "readiness_state": state, "identity_match": False,
            "probe_kind": "CONTROLLED_TEST", "probed_at_utc": "2026-11-06T00:00:00+00:00"}


def test_passive_snapshots_are_return_only_by_default(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    manager = DestinationReadinessManager(store=store)
    row = manager.passive_surface("X_POST")
    assert row["readiness_state"] == "STALE_NEEDS_JIT_VERIFICATION"
    snapshot = manager.probe_all()
    assert set(snapshot["surfaces"]) == set(TIER1_SURFACES)
    assert store.list_destination_readiness() == []


@pytest.mark.parametrize("state", sorted(DESTINATION_READINESS_STATES - PERSISTABLE_DESTINATION_READINESS_STATES))
def test_a_state_the_table_cannot_hold_fails_with_a_named_error(tmp_path, state):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    with pytest.raises(ValueError, match=f"destination_readiness_state_not_persistable:{state}"):
        store.upsert_destination_readiness(row=_row(state))
    # Asking a passive snapshot to persist gets the same named error, never a bare IntegrityError.
    with pytest.raises(ValueError, match="destination_readiness_state_not_persistable"):
        DestinationReadinessManager(store=store).passive_surface("X_POST", persist=True)
    assert store.list_destination_readiness() == []


def test_the_ten_persistable_states_match_the_table_check(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    assert len(PERSISTABLE_DESTINATION_READINESS_STATES) == 10
    for state in sorted(PERSISTABLE_DESTINATION_READINESS_STATES):
        try:
            store.upsert_destination_readiness(row=_row(state))
        except sqlite3.IntegrityError as exc:  # the Python set and the table CHECK must agree
            pytest.fail(f"{state} passes the store's check but not the table CHECK: {exc}")
    assert {r["readiness_state"] for r in store.list_destination_readiness()} <= PERSISTABLE_DESTINATION_READINESS_STATES
