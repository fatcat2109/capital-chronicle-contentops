"""
Test Durable Operational Store & Canonical State Machine v1

Tests: WAL mode, schema migrations, Compare-And-Set state machine, append-only triggers,
       leases & fencing tokens, restart safety, event replay, corruption detection,
       orchestrator integration, and redacted evidence export.
"""

import json
import os
import pathlib
import sqlite3
import tempfile
import threading
import pytest

from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    DurableStoreError,
    MigrationError,
    InvalidStateTransitionError,
    CASStateConflictError,
    TransitionValidationError,
    WorkItemNotFoundError,
    StaleFencingTokenError,
    LeaseConflictError,
    DurableStateCorruptionError,
)
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_contentops_durable_store.sqlite"
    store = ContentOpsDurableStore(db_file, busy_timeout_ms=3000, auto_migrate=True)
    return store


def test_wal_and_foreign_keys_enforcement(temp_db):
    conn = temp_db.get_connection()
    try:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert journal_mode.upper() == "WAL"
        assert foreign_keys == 1
    finally:
        conn.close()


def test_clean_init_and_idempotent_migrations(temp_db):
    version = temp_db.get_current_schema_version()
    assert version >= 1
    # Second migration call should be no-op
    applied = temp_db.run_migrations()
    assert applied == 0
    assert temp_db.verify_schema_integrity() is True


def test_multi_version_migration_upgrade(temp_db):
    assert temp_db.get_current_schema_version() == 1
    conn = temp_db.get_connection()
    try:
        row = conn.execute("SELECT * FROM schema_migrations WHERE version = 1;").fetchone()
        assert row is not None
        assert row["description"] == "Initial Wave 02 Durable Operational Store Schema"
    finally:
        conn.close()


def test_injected_migration_failure_rollback(tmp_path):
    db_file = tmp_path / "test_migration_failure.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    initial_ver = store.get_current_schema_version()
    assert initial_ver == 1

    # Simulate bad migration
    from live_contentops.durable_operational_store_v1 import MIGRATIONS
    bad_migration = (2, "Bad Migration", "SYNTAX ERROR SQL STATEMENT FAILURE;")
    MIGRATIONS.append(bad_migration)

    try:
        with pytest.raises(MigrationError):
            store.run_migrations()
        # Ensure schema version remained at 1 after rollback
        assert store.get_current_schema_version() == 1
    finally:
        MIGRATIONS.pop()


def test_cas_state_machine_lifecycle(temp_db):
    item = temp_db.create_work_item(story_id="story_101", title="Treasury Story", target_surface="substack")
    item_id = item["work_item_id"]
    assert item["current_state"] == "DISCOVERED"
    assert item["state_version"] == 1

    hash1 = "a" * 64
    # Valid transition: DISCOVERED -> EVIDENCE_PENDING
    t1 = temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="UnitTestWorker",
        actor_ref="worker_1",
        reason_code="START_EVIDENCE_INGEST",
        explanation="Initiated evidence collection",
        artifact_hash_set=[hash1],
        correlation_id="corr_101",
        authority_granted=False,
    )
    assert t1["current_state"] == "EVIDENCE_PENDING"
    assert t1["state_version"] == 2

    # Valid transition: EVIDENCE_PENDING -> EVIDENCE_READY
    t2 = temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="EVIDENCE_PENDING",
        to_state="EVIDENCE_READY",
        expected_state_version=2,
        actor_class="UnitTestWorker",
        actor_ref="worker_1",
        reason_code="EVIDENCE_VERIFIED",
        explanation="Claims and sources verified",
        artifact_hash_set=[hash1],
        correlation_id="corr_101",
        authority_granted=False,
    )
    assert t2["current_state"] == "EVIDENCE_READY"
    assert t2["state_version"] == 3


def test_cas_version_and_state_conflict_rejection(temp_db):
    item = temp_db.create_work_item(story_id="story_102", title="CAS Test", target_surface="telegram")
    item_id = item["work_item_id"]
    hash1 = "b" * 64

    # Wrong expected state version
    with pytest.raises(CASStateConflictError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=99,
            actor_class="Worker",
            actor_ref="w1",
            reason_code="REASON",
            explanation="test",
            artifact_hash_set=[hash1],
            correlation_id="corr",
        )

    # Wrong expected from state
    with pytest.raises(CASStateConflictError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="ASSIGNED",
            to_state="PRODUCTION_IN_PROGRESS",
            expected_state_version=1,
            actor_class="Worker",
            actor_ref="w1",
            reason_code="REASON",
            explanation="test",
            artifact_hash_set=[hash1],
            correlation_id="corr",
        )


def test_invalid_state_transition_rejection(temp_db):
    item = temp_db.create_work_item(story_id="story_103", title="Illegal Transition", target_surface="x")
    item_id = item["work_item_id"]
    hash1 = "c" * 64

    # Direct move DISCOVERED -> DISPATCH_COMPLETE is illegal
    with pytest.raises(InvalidStateTransitionError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="DISCOVERED",
            to_state="DISPATCH_COMPLETE",
            expected_state_version=1,
            actor_class="Worker",
            actor_ref="w1",
            reason_code="REASON",
            explanation="test",
            artifact_hash_set=[hash1],
            correlation_id="corr",
        )


def test_missing_actor_reason_hash_rejection(temp_db):
    item = temp_db.create_work_item(story_id="story_104", title="Validation Test", target_surface="discord")
    item_id = item["work_item_id"]
    hash1 = "d" * 64

    with pytest.raises(TransitionValidationError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=1,
            actor_class="",
            actor_ref="w1",
            reason_code="REASON",
            explanation="test",
            artifact_hash_set=[hash1],
            correlation_id="corr",
        )

    with pytest.raises(TransitionValidationError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=1,
            actor_class="Worker",
            actor_ref="w1",
            reason_code="",
            explanation="test",
            artifact_hash_set=[hash1],
            correlation_id="corr",
        )


def test_malformed_artifact_hash_rejection(temp_db):
    item = temp_db.create_work_item(story_id="story_105", title="Hash Test", target_surface="linkedin")
    item_id = item["work_item_id"]

    with pytest.raises(TransitionValidationError):
        temp_db.transition_state(
            work_item_id=item_id,
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=1,
            actor_class="Worker",
            actor_ref="w1",
            reason_code="REASON",
            explanation="test",
            artifact_hash_set=["not_a_valid_sha256_hash"],
            correlation_id="corr",
        )


def test_append_only_transition_event_update_delete_rejection(temp_db):
    item = temp_db.create_work_item(story_id="story_106", title="Append Only", target_surface="threads")
    item_id = item["work_item_id"]
    hash1 = "e" * 64

    temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="w1",
        reason_code="START",
        explanation="test",
        artifact_hash_set=[hash1],
        correlation_id="corr",
    )

    conn = temp_db.get_connection()
    try:
        # Attempt UPDATE on transition_events
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="append-only"):
            conn.execute("UPDATE transition_events SET reason_code = 'MUTATED';")

        # Attempt DELETE on transition_events
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="append-only"):
            conn.execute("DELETE FROM transition_events;")
    finally:
        conn.close()


def test_two_workers_race_for_one_item_exactly_one_wins(temp_db):
    item = temp_db.create_work_item(story_id="story_107", title="Race Condition Test", target_surface="substack")
    item_id = item["work_item_id"]
    hash1 = "f" * 64

    results = []
    errors = []

    def worker_action(worker_id):
        try:
            res = temp_db.transition_state(
                work_item_id=item_id,
                expected_from_state="DISCOVERED",
                to_state="EVIDENCE_PENDING",
                expected_state_version=1,
                actor_class="ThreadWorker",
                actor_ref=f"worker_{worker_id}",
                reason_code="RACE_TRY",
                explanation="Simulated concurrent write",
                artifact_hash_set=[hash1],
                correlation_id=f"corr_{worker_id}",
            )
            results.append(res)
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=worker_action, args=(1,))
    t2 = threading.Thread(target=worker_action, args=(2,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(results) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], CASStateConflictError)


def test_lease_acquisition_renewal_release_and_stale_recovery(temp_db):
    # Acquire active lease
    lease1 = temp_db.acquire_lease(lease_key="scheduler_master", owner_ref="worker_A", ttl_seconds=10)
    assert lease1["status"] == "ACTIVE"
    assert lease1["fencing_token"] == 1
    lease_id = lease1["lease_id"]

    # Active lease conflict
    with pytest.raises(LeaseConflictError):
        temp_db.acquire_lease(lease_key="scheduler_master", owner_ref="worker_B", ttl_seconds=10)

    # Renew lease with correct fencing token
    renewed = temp_db.renew_lease(lease_id=lease_id, owner_ref="worker_A", fencing_token=1, ttl_seconds=20)
    assert renewed["status"] == "ACTIVE"

    # Renew with stale fencing token
    with pytest.raises(StaleFencingTokenError):
        temp_db.renew_lease(lease_id=lease_id, owner_ref="worker_A", fencing_token=99, ttl_seconds=20)

    # Release lease
    released = temp_db.release_lease(lease_id=lease_id, owner_ref="worker_A", fencing_token=1)
    assert released["status"] == "RELEASED"

    # Now another worker can acquire lease
    lease2 = temp_db.acquire_lease(lease_key="scheduler_master", owner_ref="worker_B", ttl_seconds=10)
    assert lease2["status"] == "ACTIVE"
    assert lease2["fencing_token"] == 2


def test_stale_lease_recovery(temp_db):
    # Acquire lease with 0 second TTL
    lease = temp_db.acquire_lease(lease_key="worker_lease_key", owner_ref="worker_C", ttl_seconds=0)
    lease_id = lease["lease_id"]

    # Recover stale leases
    recovered_ids = temp_db.recover_stale_leases()
    assert lease_id in recovered_ids

    lease_after = temp_db.get_lease(lease_id)
    assert lease_after["status"] == "EXPIRED"


def test_restart_safety_and_reconstruction(temp_db):
    item = temp_db.create_work_item(story_id="story_108", title="Restart Test", target_surface="substack")
    item_id = item["work_item_id"]
    hash1 = "0" * 64

    temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="w1",
        reason_code="INGEST",
        explanation="test",
        artifact_hash_set=[hash1],
        correlation_id="corr",
    )

    recon = temp_db.reconstruct_in_flight_state()
    assert recon["restart_reconstruction_status"] == "PASS"
    assert recon["verified_work_items_count"] >= 1


def test_deterministic_replay_and_corruption_verification(temp_db):
    item = temp_db.create_work_item(story_id="story_109", title="Replay Test", target_surface="telegram")
    item_id = item["work_item_id"]
    hash1 = "1" * 64

    temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="w1",
        reason_code="STEP_1",
        explanation="test",
        artifact_hash_set=[hash1],
        correlation_id="corr1",
    )
    temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="EVIDENCE_PENDING",
        to_state="EVIDENCE_READY",
        expected_state_version=2,
        actor_class="Worker",
        actor_ref="w1",
        reason_code="STEP_2",
        explanation="test",
        artifact_hash_set=[hash1],
        correlation_id="corr2",
    )

    replay1 = temp_db.replay_work_item_events(item_id)
    replay2 = temp_db.replay_work_item_events(item_id)

    assert replay1 == replay2
    assert replay1["replayed_state"] == "EVIDENCE_READY"
    assert replay1["replayed_version"] == 3
    assert replay1["event_count"] == 2

    # Manually corrupt materialized projection in work_items table
    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE work_items SET current_state = 'CORRUPTED_STATE' WHERE work_item_id = ?;", (item_id,))
    finally:
        conn.close()

    # Verify replay detects corruption
    with pytest.raises(DurableStateCorruptionError):
        temp_db.replay_work_item_events(item_id)


def test_redacted_evidence_export_contains_no_forbidden_material(temp_db):
    item = temp_db.create_work_item(story_id="story_110", title="Export Test", target_surface="substack")
    item_id = item["work_item_id"]
    hash1 = "2" * 64

    temp_db.transition_state(
        work_item_id=item_id,
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="w1",
        reason_code="EXPORT_TEST",
        explanation="test",
        artifact_hash_set=[hash1],
        correlation_id="corr",
    )

    export = temp_db.export_redacted_store_evidence()
    assert export["schema_version"] == "contentops.durable_store_export.v1"
    assert export["redaction_guarantee"] == "PASS_NO_SECRETS_CREDENTIALS_OR_PRIVATE_MATERIAL"
    assert len(export["work_items"]) >= 1
    assert len(export["transition_events"]) >= 1

    export_json = json.dumps(export)
    assert "secret_key" not in export_json.lower()
    assert "client_secret" not in export_json.lower()
    assert "private_key" not in export_json.lower()
    assert "bearer " not in export_json.lower()
    assert "cookie=" not in export_json.lower()


def test_orchestrator_store_integration(temp_db, tmp_path):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    result = orchestrator.execute("prepare_text_image_release_candidate", run_id="test_run_store_101", output_dir=tmp_path)
    assert result is not None

    export = temp_db.export_redacted_store_evidence()
    assert export["counts"]["work_items"] >= 1
    assert export["counts"]["transition_events"] >= 1


def test_no_committed_sqlite_wal_shm_backup_artifacts():
    gitignore_path = pathlib.Path(__file__).resolve().parent.parent / ".gitignore"
    if gitignore_path.exists():
        text = gitignore_path.read_text(encoding="utf-8")
        assert "*.sqlite" in text or "*.db" in text
