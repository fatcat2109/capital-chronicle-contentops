"""
Comprehensive Unit, Resilience, CAS, Lease, Fencing, Artifact Integrity, Replay, Authority Guard,
and Redaction Tests for Durable Operational Store v1 (Wave 02 Correction).
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
    Wave02AuthorityViolationError,
    ArtifactNotFoundError,
    ArtifactValidationError,
    compute_sha256,
    GENESIS_PREVIOUS_HASH,
)
from live_contentops.production_orchestrator_v1 import (
    ContentOpsProductionOrchestrator,
    ContentOpsDurableContext,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_contentops_durable_store.sqlite"
    store = ContentOpsDurableStore(db_file, busy_timeout_ms=3000, auto_migrate=True)
    return store


def test_wal_and_foreign_keys_enforcement(temp_db):
    pragmas = temp_db.query_pragmas()
    assert pragmas["journal_mode"] == "WAL"
    assert pragmas["foreign_keys"] == 1
    assert pragmas["busy_timeout_ms"] == 3000


def test_clean_init_and_idempotent_migrations(temp_db):
    version = temp_db.get_current_schema_version()
    assert version == 2
    applied = temp_db.run_migrations()
    assert applied == 0
    assert temp_db.verify_schema_integrity() is True


def test_multi_version_migration_upgrade(tmp_path):
    db_file = tmp_path / "test_upgrade.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 2

    conn = store.get_connection()
    try:
        rows = conn.execute("SELECT version, description FROM schema_migrations ORDER BY version ASC;").fetchall()
        assert len(rows) == 2
        assert rows[0]["version"] == 1
        assert rows[1]["version"] == 2
    finally:
        conn.close()


def test_partial_migration_failure_rollback_and_restore(tmp_path):
    db_file = tmp_path / "test_migration_failure.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 2

    # Add a work item to verify data remains readable after rollback
    store.create_work_item(story_id="story_pre_fail", title="Pre Fail Story", target_surface="substack", work_item_id="wi_pre_fail")

    from live_contentops.durable_operational_store_v1 import MIGRATIONS
    # Inject bad Migration 3 that creates a table then fails with bad SQL
    bad_sql = "CREATE TABLE temp_test_table (id INT); INVALID SYNTAX ERROR STATEMENT;"
    MIGRATIONS.append((3, "Bad Migration 3", bad_sql))

    try:
        with pytest.raises(MigrationError):
            store.run_migrations()

        # Verify schema version remained at 2
        assert store.get_current_schema_version() == 2

        # Verify partial table temp_test_table does NOT exist
        conn = store.get_connection()
        try:
            tbl_check = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='temp_test_table';"
            ).fetchone()[0]
            assert tbl_check == 0

            # Verify prior data remains intact
            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = 'wi_pre_fail';").fetchone()
            assert item is not None
            assert item["title"] == "Pre Fail Story"
        finally:
            conn.close()
    finally:
        MIGRATIONS.pop()


def test_immutable_artifact_registration(temp_db):
    payload = "Sample input artifact content for test"
    length = len(payload)
    sha256 = compute_sha256(payload)

    art = temp_db.register_artifact(
        artifact_id="art_101",
        artifact_type="raw_headline_packet",
        storage_class="local_file",
        byte_length=length,
        sha256_hash=sha256,
        schema_version="contentops.artifact.v1",
        producer_ref="unit_test_producer",
        story_id="story_101",
    )
    assert art["artifact_id"] == "art_101"
    assert art["sha256_hash"] == sha256

    # Re-registering identical artifact is idempotent
    art_dupe = temp_db.register_artifact(
        artifact_id="art_101",
        artifact_type="raw_headline_packet",
        storage_class="local_file",
        byte_length=length,
        sha256_hash=sha256,
        schema_version="contentops.artifact.v1",
        producer_ref="unit_test_producer",
        story_id="story_101",
    )
    assert art_dupe["artifact_id"] == "art_101"

    # Conflicting registration fails
    with pytest.raises(ArtifactValidationError):
        temp_db.register_artifact(
            artifact_id="art_101",
            artifact_type="raw_headline_packet",
            storage_class="local_file",
            byte_length=length,
            sha256_hash="f" * 64,
            schema_version="contentops.artifact.v1",
            producer_ref="unit_test_producer",
        )


def test_exact_fencing_token_mutation_rejection(temp_db):
    # Register work item and initial input artifact
    item = temp_db.create_work_item(story_id="story_fence", title="Fencing Test", target_surface="substack", work_item_id="wi_fence")
    art = temp_db.register_artifact(
        artifact_id="art_in_1",
        artifact_type="input_claim",
        storage_class="memory",
        byte_length=100,
        sha256_hash="a" * 64,
        schema_version="v1",
        producer_ref="test",
        work_item_id="wi_fence",
    )

    # 1. Worker A claims item with lease_key="key_fence", getting fencing token 1
    claim_A = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_A", ttl_seconds=1)
    assert claim_A["fencing_token"] == 1
    assert claim_A["owner_ref"] == "worker_A"

    # 2. Worker A's lease expires (simulated by releasing / forcing expiry)
    temp_db.release_lease(claim_A["lease_id"], "worker_A", 1)

    # 3. Worker B claims item with token 2
    claim_B = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_B", ttl_seconds=10)
    assert claim_B["fencing_token"] == 2
    assert claim_B["owner_ref"] == "worker_B"

    # 4. Worker A attempts state transition using token 1 and is REJECTED
    with pytest.raises(StaleFencingTokenError):
        temp_db.transition_state(
            work_item_id="wi_fence",
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=1,
            actor_class="WorkerA",
            actor_ref="worker_A",
            reason_code="STALE_TRY",
            explanation="Stale worker A transition",
            lease_key="key_fence",
            fencing_token=1,
            input_artifact_ids=["art_in_1"],
            output_artifact_ids=[],
            correlation_id="corr_A",
        )

    # 5. Worker B performs the same transition successfully
    trans_B = temp_db.transition_state(
        work_item_id="wi_fence",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="WorkerB",
        actor_ref="worker_B",
        reason_code="VALID_TRY",
        explanation="Valid worker B transition",
        lease_key="key_fence",
        fencing_token=2,
        input_artifact_ids=["art_in_1"],
        output_artifact_ids=[],
        correlation_id="corr_B",
    )
    assert trans_B["current_state"] == "EVIDENCE_PENDING"
    assert trans_B["state_version"] == 2

    # 6. Verify exactly 1 transition event exists
    conn = temp_db.get_connection()
    try:
        events = conn.execute("SELECT * FROM transition_events WHERE work_item_id = 'wi_fence';").fetchall()
        assert len(events) == 1
        assert events[0]["actor_ref"] == "worker_B"
        assert events[0]["event_seq"] == 1
    finally:
        conn.close()


def test_wave02_authority_fail_closed_guard(temp_db):
    item = temp_db.create_work_item(story_id="story_auth", title="Auth Guard Test", target_surface="substack", work_item_id="wi_auth")
    art = temp_db.register_artifact(
        artifact_id="art_auth_1",
        artifact_type="claim",
        storage_class="memory",
        byte_length=50,
        sha256_hash="b" * 64,
        schema_version="v1",
        producer_ref="test",
        work_item_id="wi_auth",
    )
    claim = temp_db.claim_work_item(lease_key="key_auth", work_item_id="wi_auth", owner_ref="worker_auth", ttl_seconds=10)

    # Transition to REVIEW_READY
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="EVIDENCE_PENDING",
        to_state="EVIDENCE_READY",
        expected_state_version=2,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="EVIDENCE_READY",
        to_state="ASSIGNMENT_CANDIDATE",
        expected_state_version=3,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="ASSIGNMENT_CANDIDATE",
        to_state="ASSIGNED",
        expected_state_version=4,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="ASSIGNED",
        to_state="PRODUCTION_IN_PROGRESS",
        expected_state_version=5,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="PRODUCTION_IN_PROGRESS",
        to_state="REVIEW_READY",
        expected_state_version=6,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )
    temp_db.transition_state(
        work_item_id="wi_auth",
        expected_from_state="REVIEW_READY",
        to_state="OPERATOR_PENDING",
        expected_state_version=7,
        actor_class="Worker",
        actor_ref="worker_auth",
        reason_code="REASON",
        explanation="test",
        lease_key="key_auth",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_auth_1"],
        output_artifact_ids=[],
        correlation_id="corr",
    )

    # Attempting move to APPROVED_EXACT must fail closed with Wave02AuthorityViolationError
    with pytest.raises(Wave02AuthorityViolationError):
        temp_db.transition_state(
            work_item_id="wi_auth",
            expected_from_state="OPERATOR_PENDING",
            to_state="APPROVED_EXACT",
            expected_state_version=8,
            actor_class="Worker",
            actor_ref="worker_auth",
            reason_code="APPROVE",
            explanation="test",
            lease_key="key_auth",
            fencing_token=claim["fencing_token"],
            input_artifact_ids=["art_auth_1"],
            output_artifact_ids=[],
            correlation_id="corr",
        )


def test_event_hash_chain_and_replay_integrity(temp_db):
    temp_db.create_work_item(story_id="story_chain", title="Chain Test", target_surface="x", work_item_id="wi_chain")
    temp_db.register_artifact(
        artifact_id="art_chain_1",
        artifact_type="claim",
        storage_class="memory",
        byte_length=10,
        sha256_hash="c" * 64,
        schema_version="v1",
        producer_ref="test",
        work_item_id="wi_chain",
    )
    claim = temp_db.claim_work_item(lease_key="key_chain", work_item_id="wi_chain", owner_ref="worker_chain", ttl_seconds=10)

    t1 = temp_db.transition_state(
        work_item_id="wi_chain",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_chain",
        reason_code="STEP_1",
        explanation="Step 1 transition",
        lease_key="key_chain",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_chain_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )
    assert t1["event_seq"] == 1
    assert t1["previous_event_hash"] == GENESIS_PREVIOUS_HASH

    t2 = temp_db.transition_state(
        work_item_id="wi_chain",
        expected_from_state="EVIDENCE_PENDING",
        to_state="EVIDENCE_READY",
        expected_state_version=2,
        actor_class="Worker",
        actor_ref="worker_chain",
        reason_code="STEP_2",
        explanation="Step 2 transition",
        lease_key="key_chain",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_chain_1"],
        output_artifact_ids=[],
        correlation_id="corr_2",
    )
    assert t2["event_seq"] == 2
    assert t2["previous_event_hash"] == t1["event_hash"]

    # Replay verification
    replay = temp_db.replay_work_item_events("wi_chain")
    assert replay["verification_status"] == "PASS"
    assert replay["replayed_state"] == "EVIDENCE_READY"
    assert replay["replayed_version"] == 3
    assert replay["event_count"] == 2


def test_replay_corruption_detection(temp_db):
    temp_db.create_work_item(story_id="story_corrupt", title="Corrupt Test", target_surface="telegram", work_item_id="wi_corrupt")
    temp_db.register_artifact(
        artifact_id="art_corrupt_1",
        artifact_type="claim",
        storage_class="memory",
        byte_length=10,
        sha256_hash="d" * 64,
        schema_version="v1",
        producer_ref="test",
        work_item_id="wi_corrupt",
    )
    claim = temp_db.claim_work_item(lease_key="key_corrupt", work_item_id="wi_corrupt", owner_ref="worker_corrupt", ttl_seconds=10)

    temp_db.transition_state(
        work_item_id="wi_corrupt",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_corrupt",
        reason_code="STEP_1",
        explanation="test",
        lease_key="key_corrupt",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_corrupt_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )

    # Tamper with materialized work_items state projection
    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE work_items SET current_state = 'EVIDENCE_READY' WHERE work_item_id = 'wi_corrupt';")
    finally:
        conn.close()

    with pytest.raises(DurableStateCorruptionError):
        temp_db.replay_work_item_events("wi_corrupt")


def test_adversarial_redacted_evidence_export(temp_db):
    temp_db.create_work_item(story_id="story_secret", title="Secret Story Title", target_surface="substack", work_item_id="wi_secret")
    temp_db.register_artifact(
        artifact_id="art_secret_1",
        artifact_type="secret_claim",
        storage_class="memory",
        byte_length=10,
        sha256_hash="e" * 64,
        schema_version="v1",
        producer_ref="test",
        work_item_id="wi_secret",
    )
    claim = temp_db.claim_work_item(lease_key="key_secret", work_item_id="wi_secret", owner_ref="secret_agent_007", ttl_seconds=10)

    temp_db.transition_state(
        work_item_id="wi_secret",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="secret_agent_007",
        reason_code="REASON_SECRET",
        explanation="Secret explanation containing password=my_secret_password and bearer_token=abc123xyz",
        lease_key="key_secret",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_secret_1"],
        output_artifact_ids=[],
        correlation_id="corr_secret",
    )

    export = temp_db.export_redacted_store_evidence()
    assert export["database_pragmas"]["journal_mode"] == "WAL"
    assert export["database_pragmas"]["foreign_keys"] == 1

    export_json = json.dumps(export)
    assert "my_secret_password" not in export_json
    assert "abc123xyz" not in export_json
    assert "secret_agent_007" not in export_json
    assert "Secret Story Title" not in export_json


def test_orchestrator_store_integration_with_durable_context(temp_db, tmp_path):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)

    # Calling execute with store active WITHOUT durable_context fails closed
    with pytest.raises(ValueError, match="durable_context_required_when_store_active"):
        orchestrator.execute("prepare_text_image_release_candidate", run_id="test_run_101", output_dir=tmp_path)

    # Create work item & register input artifact
    temp_db.create_work_item(story_id="treasury_20260714", title="Orchestrator Story", target_surface="eight_platform_all", work_item_id="wi_orch_101")
    art = temp_db.register_artifact(
        artifact_id="art_orch_1",
        artifact_type="rc_input",
        storage_class="local_file",
        byte_length=100,
        sha256_hash="f" * 64,
        schema_version="v1",
        producer_ref="test_orch",
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
    )

    claim = temp_db.claim_work_item(lease_key="key_orch", work_item_id="wi_orch_101", owner_ref="orch_worker", ttl_seconds=10)

    ctx = ContentOpsDurableContext(
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
        correlation_id="corr_orch_101",
        actor_ref="orch_worker",
        lease_key="key_orch",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_orch_1"],
    )

    result = orchestrator.execute(
        "prepare_text_image_release_candidate",
        run_id="test_run_101",
        output_dir=tmp_path,
        durable_context=ctx,
    )
    assert result is not None

    export = temp_db.export_redacted_store_evidence()
    assert export["counts"]["work_items"] >= 1
    assert export["counts"]["transition_events"] >= 1


def test_gitignore_database_family_patterns():
    gitignore_path = pathlib.Path(__file__).resolve().parent.parent / ".gitignore"
    text = gitignore_path.read_text(encoding="utf-8")
    assert "*.sqlite" in text
    assert "*.sqlite.bak.*" in text or "*.sqlite*" in text
    assert "*.db" in text
    assert "*-wal" in text or "*.sqlite-wal" in text
