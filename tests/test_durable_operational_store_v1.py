"""
Comprehensive Unit, Resilience, CAS, Lease, Fencing, Artifact Integrity, Replay, Authority Guard,
and Redaction Tests for Durable Operational Store v1 (Wave 02 Final Correction).
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
    assert version == 3
    applied = temp_db.run_migrations()
    assert applied == 0
    assert temp_db.verify_schema_integrity() is True


def test_real_multi_version_migration_upgrade(tmp_path):
    db_file = tmp_path / "test_upgrade.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 3

    conn = store.get_connection()
    try:
        rows = conn.execute("SELECT version, description FROM schema_migrations ORDER BY version ASC;").fetchall()
        assert len(rows) == 3
        assert rows[0]["version"] == 1
        assert rows[1]["version"] == 2
        assert rows[2]["version"] == 3
    finally:
        conn.close()


def test_applied_migration_checksum_drift_rejection(temp_db):
    # Tamper with schema_migrations recorded checksum
    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE schema_migrations SET checksum = 'bad_checksum' WHERE version = 1;")
    finally:
        conn.close()

    with pytest.raises(MigrationError, match="Checksum drift"):
        temp_db.verify_applied_migrations()


def test_partial_migration_failure_rollback_and_restore(tmp_path):
    db_file = tmp_path / "test_migration_failure.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 3

    store.create_work_item(story_id="story_pre_fail", title="Pre Fail Story", target_surface="substack", work_item_id="wi_pre_fail")

    from live_contentops.durable_operational_store_v1 import MIGRATIONS
    bad_sql = "CREATE TABLE temp_test_table (id INT); INVALID SYNTAX ERROR STATEMENT;"
    MIGRATIONS.append((4, "Bad Migration 4", bad_sql))

    try:
        with pytest.raises(MigrationError):
            store.run_migrations()

        assert store.get_current_schema_version() == 3

        conn = store.get_connection()
        try:
            tbl_check = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='temp_test_table';"
            ).fetchone()[0]
            assert tbl_check == 0

            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = 'wi_pre_fail';").fetchone()
            assert item is not None
            assert item["title"] == "Pre Fail Story"
        finally:
            conn.close()
    finally:
        MIGRATIONS.pop()


def test_atomic_genesis_event_and_work_item_creation(temp_db):
    item = temp_db.create_work_item(story_id="story_gen", title="Genesis Test", target_surface="substack", work_item_id="wi_gen")
    assert item["work_item_id"] == "wi_gen"
    assert item["current_state"] == "DISCOVERED"
    assert item["state_version"] == 1

    conn = temp_db.get_connection()
    try:
        events = conn.execute("SELECT * FROM transition_events WHERE work_item_id = 'wi_gen';").fetchall()
        assert len(events) == 1
        genesis = events[0]
        assert genesis["event_seq"] == 1
        assert genesis["reason_code"] == "WORK_ITEM_INITIALIZATION"
        assert genesis["previous_event_hash"] == GENESIS_PREVIOUS_HASH
        assert genesis["from_state"] == "DISCOVERED"
        assert genesis["to_state"] == "DISCOVERED"
    finally:
        conn.close()


def test_projection_without_genesis_fails(temp_db):
    conn = temp_db.get_connection()
    try:
        conn.execute(
            "INSERT INTO work_items (work_item_id, story_id, title, current_state, state_version, target_surface, created_at, updated_at) "
            "VALUES ('wi_nogen', 'story_nogen', 'No Gen', 'DISCOVERED', 1, 'substack', 'now', 'now');"
        )
    finally:
        conn.close()

    with pytest.raises(DurableStateCorruptionError, match="has no transition events|missing valid genesis event"):
        temp_db.replay_work_item_events("wi_nogen")


def test_artifact_registration_derived_from_bytes_or_verified_receipt(temp_db):
    payload = b"Sample input artifact content for test"
    length = len(payload)
    sha256 = compute_sha256(payload)

    art = temp_db.register_artifact(
        artifact_id="art_101",
        artifact_type="raw_headline_packet",
        storage_class="local_file",
        schema_version="contentops.artifact.v1",
        producer_ref="unit_test_producer",
        content_bytes=payload,
        story_id="story_101",
    )
    assert art["artifact_id"] == "art_101"
    assert art["sha256_hash"] == sha256
    assert art["byte_length"] == length

    with pytest.raises(ArtifactValidationError):
        temp_db.register_artifact(
            artifact_id="art_bad",
            artifact_type="raw_headline_packet",
            storage_class="local_file",
            schema_version="contentops.artifact.v1",
            producer_ref="unit_test_producer",
        )


def test_artifact_update_and_delete_triggers_reject_direct_modification(temp_db):
    temp_db.register_artifact(
        artifact_id="art_trig",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"test bytes",
    )

    conn = temp_db.get_connection()
    try:
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="artifact_references are immutable"):
            conn.execute("UPDATE artifact_references SET storage_class = 'hacked' WHERE artifact_id = 'art_trig';")

        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="artifact_references are immutable"):
            conn.execute("DELETE FROM artifact_references WHERE artifact_id = 'art_trig';")
    finally:
        conn.close()


def test_complete_event_payload_hash_verification(temp_db):
    temp_db.create_work_item(story_id="story_hash", title="Hash Envelope Test", target_surface="x", work_item_id="wi_hash")
    art = temp_db.register_artifact(
        artifact_id="art_hash_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"input bytes",
        work_item_id="wi_hash",
    )

    claim = temp_db.claim_work_item(lease_key="key_hash", work_item_id="wi_hash", owner_ref="worker_hash", ttl_seconds=10)

    t1 = temp_db.transition_state(
        work_item_id="wi_hash",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_hash",
        reason_code="STEP_1",
        explanation="Step 1 transition",
        lease_key="key_hash",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_hash_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )

    replay = temp_db.replay_work_item_events("wi_hash")
    assert replay["verification_status"] == "PASS"


def test_unauthorized_direct_event_insertion_and_update_rejection(temp_db):
    temp_db.create_work_item(story_id="story_tamper", title="Tamper Test", target_surface="x", work_item_id="wi_tamper")
    art = temp_db.register_artifact(
        artifact_id="art_tamper_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"tamper bytes",
        work_item_id="wi_tamper",
    )
    claim = temp_db.claim_work_item(lease_key="key_tamper", work_item_id="wi_tamper", owner_ref="worker_tamper", ttl_seconds=10)

    temp_db.transition_state(
        work_item_id="wi_tamper",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_tamper",
        reason_code="STEP_1",
        explanation="Step 1 transition",
        lease_key="key_tamper",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_tamper_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )

    conn = temp_db.get_connection()
    try:
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="transition_events are append-only"):
            conn.execute(
                "UPDATE transition_events SET reason_code = 'HACKED' WHERE work_item_id = 'wi_tamper' AND event_seq = 2;"
            )
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="transition_events are append-only"):
            conn.execute(
                "DELETE FROM transition_events WHERE work_item_id = 'wi_tamper' AND event_seq = 2;"
            )
    finally:
        conn.close()


def test_concurrent_claims_only_one_winner(temp_db):
    temp_db.create_work_item(story_id="story_conc", title="Concurrent Test", target_surface="x", work_item_id="wi_conc")

    results = []

    def attempt_claim(worker_name):
        try:
            res = temp_db.claim_work_item(lease_key="key_conc", work_item_id="wi_conc", owner_ref=worker_name, ttl_seconds=5)
            results.append((worker_name, res))
        except Exception as exc:
            results.append((worker_name, exc))

    t1 = threading.Thread(target=attempt_claim, args=("Worker_1",))
    t2 = threading.Thread(target=attempt_claim, args=("Worker_2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [r for r in results if isinstance(r[1], dict)]
    failures = [r for r in results if isinstance(r[1], Exception)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0][1], LeaseConflictError)


def test_lease_expiry_and_stale_fencing_token_rejection(temp_db):
    temp_db.create_work_item(story_id="story_fence", title="Fencing Test", target_surface="substack", work_item_id="wi_fence")
    art = temp_db.register_artifact(
        artifact_id="art_in_1",
        artifact_type="input_claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"fence bytes",
        work_item_id="wi_fence",
    )

    claim_A = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_A", ttl_seconds=1)
    assert claim_A["fencing_token"] == 1

    temp_db.release_lease(claim_A["lease_id"], "worker_A", 1)

    claim_B = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_B", ttl_seconds=10)
    assert claim_B["fencing_token"] == 2

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


def test_heartbeat_freshness_and_stale_disposition(temp_db):
    lease = temp_db.acquire_lease("l_hb", "worker_live", 60)
    temp_db.upsert_heartbeat(worker_id="worker_live", lease_id=lease["lease_id"])
    fresh = temp_db.query_fresh_heartbeats(ttl_seconds=60)
    assert len(fresh) == 1
    assert fresh[0]["worker_id"] == "worker_live"

    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE heartbeats SET last_seen_at = '2000-01-01T00:00:00+00:00' WHERE worker_id = 'worker_live';")
    finally:
        conn.close()

    stale = temp_db.dispose_stale_heartbeats(ttl_seconds=60)
    assert "worker_live" in stale

    fresh_after = temp_db.query_fresh_heartbeats(ttl_seconds=60)
    assert len(fresh_after) == 0


def test_wave02_authority_fail_closed_guard(temp_db):
    temp_db.create_work_item(story_id="story_auth", title="Auth Guard Test", target_surface="substack", work_item_id="wi_auth")
    art = temp_db.register_artifact(
        artifact_id="art_auth_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"auth bytes",
        work_item_id="wi_auth",
    )
    claim = temp_db.claim_work_item(lease_key="key_auth", work_item_id="wi_auth", owner_ref="worker_auth", ttl_seconds=10)

    states = ["EVIDENCE_PENDING", "EVIDENCE_READY", "ASSIGNMENT_CANDIDATE", "ASSIGNED", "PRODUCTION_IN_PROGRESS", "REVIEW_READY", "OPERATOR_PENDING"]
    current_state = "DISCOVERED"
    version = 1

    for next_st in states:
        temp_db.transition_state(
            work_item_id="wi_auth",
            expected_from_state=current_state,
            to_state=next_st,
            expected_state_version=version,
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
        current_state = next_st
        version += 1

    with pytest.raises(Wave02AuthorityViolationError):
        temp_db.transition_state(
            work_item_id="wi_auth",
            expected_from_state="OPERATOR_PENDING",
            to_state="APPROVED_EXACT",
            expected_state_version=version,
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


def test_adversarial_redacted_evidence_export(temp_db):
    temp_db.create_work_item(story_id="story_secret", title="Secret Story Title", target_surface="substack", work_item_id="wi_secret")
    temp_db.register_artifact(
        artifact_id="art_secret_1",
        artifact_type="secret_claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"secret bytes",
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

    export1 = temp_db.export_redacted_store_evidence()
    export2 = temp_db.export_redacted_store_evidence()
    assert json.dumps(export1, sort_keys=True) == json.dumps(export2, sort_keys=True)

    export_json = json.dumps(export1)
    assert "my_secret_password" not in export_json
    assert "abc123xyz" not in export_json
    assert "secret_agent_007" not in export_json
    assert "Secret Story Title" not in export_json


def test_orchestrator_store_integration_with_durable_context(temp_db, tmp_path):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)

    with pytest.raises(ValueError, match="durable_context_required_when_store_active"):
        orchestrator.execute("prepare_text_image_release_candidate", run_id="test_run_101", output_dir=tmp_path)

    temp_db.create_work_item(story_id="treasury_20260714", title="Orchestrator Story", target_surface="eight_platform_all", work_item_id="wi_orch_101")
    art = temp_db.register_artifact(
        artifact_id="art_orch_1",
        artifact_type="rc_input",
        storage_class="local_file",
        schema_version="v1",
        producer_ref="test_orch",
        content_bytes=b"orch input bytes",
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
    )

    claim = temp_db.claim_work_item(lease_key="key_orch", work_item_id="wi_orch_101", owner_ref="orch_worker", ttl_seconds=10)

    ctx = ContentOpsDurableContext(
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
        title="Orchestrator Story",
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


def test_orchestrator_context_mismatch_rejection(temp_db):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    temp_db.create_work_item(story_id="story_real", title="Real Title", target_surface="eight_platform_all", work_item_id="wi_mismatch")
    claim = temp_db.claim_work_item(lease_key="key_mis", work_item_id="wi_mismatch", owner_ref="w_mis", ttl_seconds=10)

    ctx_bad = ContentOpsDurableContext(
        story_id="wrong_story",
        work_item_id="wi_mismatch",
        title="Real Title",
        correlation_id="corr_mis",
        actor_ref="w_mis",
        lease_key="key_mis",
        fencing_token=claim["fencing_token"],
    )

    with pytest.raises(ValueError, match="story_id_mismatch"):
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx_bad)


def test_gitignore_database_family_patterns():
    gitignore_path = pathlib.Path(__file__).resolve().parent.parent / ".gitignore"
    text = gitignore_path.read_text(encoding="utf-8")
    assert "*.sqlite" in text
    assert "*.db" in text
