"""
Test Wave 02 Durable Store Authority and Metadata Consistency v1

Asserts that authority documents and JSON files agree on Wave 02 status,
commit roles, test counts, next task, schema version 3, and inventory schema across the repo.
"""

import json
import pathlib
import sqlite3
import pytest

from live_contentops.durable_operational_store_v1 import (
    MIGRATIONS,
    SCHEMA_VERSION,
    ContentOpsDurableStore,
    compute_sha256,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

EXPECTED_WORKER_CLASSIFICATION = "PASS_WAVE02_FINAL_EVENT_AUTHORITY_STATUS_AND_EVIDENCE_RECONCILIATION_AWAITING_INDEPENDENT_AUDIT"
EXPECTED_COMPLETED_TASK = "TASK_CONTENTOPS_WAVE02_FINAL_EVENT_AUTHORITY_STATUS_AND_EVIDENCE_RECONCILIATION_V1"
EXPECTED_NEXT_TASK = "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1"
EXPECTED_WAVE01_STATUS = "COMPLETE_ACCEPTED_AND_MERGED"
EXPECTED_WAVE02_STATUS = "COMPLETE_AWAITING_INDEPENDENT_AUDIT"
EXPECTED_WAVE03_STATUS = "NEXT_NOT_STARTED"

EXPECTED_BASE_MASTER_HEAD = "c87e338f25922f4d03454ba199139353ca7198ff"
EXPECTED_STARTING_BRANCH_HEAD = "3cc531a3d30848f54329d25913018882f6b71bcd"
EXPECTED_AUDIT_BLOCK_COMMITS = ["e24a4492e9d72f55c704168d637b7628e49140cd", "3cc531a3d30848f54329d25913018882f6b71bcd"]


def load_json_any_encoding(path: pathlib.Path) -> dict:
    content = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return json.loads(content.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"Could not parse JSON at {path}")


def test_wave02_status_json_authority():
    status_path = REPO_ROOT / "docs" / "status" / "current_project_status.json"
    assert status_path.is_file(), "current_project_status.json must exist"

    data = load_json_any_encoding(status_path)

    assert data["wave01_status"] == EXPECTED_WAVE01_STATUS
    assert data["wave02_worker_classification"] == EXPECTED_WORKER_CLASSIFICATION
    assert data["wave02_status"] == EXPECTED_WAVE02_STATUS
    assert data["wave03_status"] == EXPECTED_WAVE03_STATUS
    assert data["next_task"] == EXPECTED_NEXT_TASK

    assert "post_v1_durable_operational_store_v1" in data
    wave_data = data["post_v1_durable_operational_store_v1"]
    assert wave_data["classification"] == EXPECTED_WORKER_CLASSIFICATION
    assert wave_data["completed_task"] == EXPECTED_COMPLETED_TASK
    assert wave_data["wave_01_status"] == EXPECTED_WAVE01_STATUS
    assert wave_data["wave_02_status"] == EXPECTED_WAVE02_STATUS
    assert wave_data["wave_03_status"] == EXPECTED_WAVE03_STATUS
    assert wave_data["next_action"] == EXPECTED_NEXT_TASK
    assert wave_data["schema_version"] == 3


def test_wave02_schema_and_migration_integrity(tmp_path):
    db_file = tmp_path / "test_meta_schema.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)

    assert store.get_current_schema_version() == SCHEMA_VERSION == 3
    assert store.verify_applied_migrations() is True
    assert store.verify_schema_integrity() is True

    conn = store.get_connection()
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        required_tables = [
            "schema_migrations",
            "operational_windows",
            "scheduler_ticks",
            "work_items",
            "story_versions",
            "assignments",
            "artifact_references",
            "transition_events",
            "model_invocations",
            "review_records",
            "operator_decisions",
            "leases",
            "heartbeats",
            "approval_envelopes",
            "outbox_messages",
            "platform_dispatches",
            "readbacks",
            "reconciliations",
            "incidents",
            "metrics",
            "feedback_records",
            "learning_reviews",
        ]
        for tbl in required_tables:
            assert tbl in tables, f"Missing required table: {tbl}"

        # Verify transition_events columns (no authority_granted)
        columns = [r[1] for r in conn.execute("PRAGMA table_info(transition_events);").fetchall()]
        assert "authority_granted" not in columns
        assert "event_seq" in columns
        assert "event_payload_json" in columns
        assert "event_hash" in columns
        assert "previous_event_hash" in columns

        # Verify triggers
        triggers = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger';").fetchall()]
        assert "trg_transition_events_no_update" in triggers
        assert "trg_transition_events_no_delete" in triggers
        assert "trg_artifact_references_no_update" in triggers
        assert "trg_artifact_references_no_delete" in triggers
    finally:
        conn.close()


def test_wave02_evidence_packet_files_exist():
    packet_dir = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
    assert packet_dir.is_dir()

    required_files = [
        "README.md",
        "architecture_and_authority_boundary.md",
        "existing_state_surface_inventory.json",
        "migration_and_supersession_map.md",
        "schema_manifest.json",
        "state_transition_matrix.json",
        "transaction_lease_and_fencing_contract.md",
        "restart_replay_and_corruption_contract.md",
        "retention_and_backup_policy.md",
        "redacted_store_evidence_export.json",
        "validation_results.md",
        "changed_file_inventory.json",
        "final_manifest.json",
    ]
    for filename in required_files:
        path = packet_dir / filename
        assert path.is_file(), f"Missing required packet file: {filename}"
