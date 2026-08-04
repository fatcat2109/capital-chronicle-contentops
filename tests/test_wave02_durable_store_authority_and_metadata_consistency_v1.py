"""
Test Wave 02 Durable Store Authority and Metadata Consistency v1

Asserts that authority documents and JSON files agree on Wave 02 status,
commit roles, test counts, next task, schema version 4, and inventory schema across the repo.
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

EXPECTED_WORKER_CLASSIFICATION = "PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
EXPECTED_COMPLETED_TASK = "TASK_CONTENTOPS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_V1"
EXPECTED_NEXT_TASK = "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1"
EXPECTED_WAVE01_STATUS = "COMPLETE_ACCEPTED_AND_MERGED"
EXPECTED_WAVE02_STATUS = "COMPLETE_AWAITING_INDEPENDENT_AUDIT"
EXPECTED_WAVE03_STATUS = "NEXT_NOT_STARTED"
PACKET_CLASSIFICATION_FIELDS = {
    "README.md": None,
    "architecture_and_authority_boundary.md": None,
    "existing_state_surface_inventory.json": "worker_classification",
    "migration_and_supersession_map.md": None,
    "schema_manifest.json": "worker_classification",
    "state_transition_matrix.json": "worker_classification",
    "transaction_lease_and_fencing_contract.md": None,
    "restart_replay_and_corruption_contract.md": None,
    "retention_and_backup_policy.md": None,
    "redacted_store_evidence_export.json": "worker_classification",
    "validation_results.md": None,
    "changed_file_inventory.json": "worker_classification",
    "final_manifest.json": "worker_classification",
}

EXPECTED_BASE_MASTER_HEAD = "c87e338f25922f4d03454ba199139353ca7198ff"
EXPECTED_RELEASE_COMMIT = "6983bfb3ef300414b744f3f8f97ca81ff699348b"
EXPECTED_STARTING_BRANCH_HEAD = "615a96fb20aa97fd76bb3343e9150daec40d9031"
EXPECTED_CANDIDATE_PASS_TOTAL = 142


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

    # Negative assertions rejecting stale Wave 02 classifications
    assert data["wave02_worker_classification"] != "PASS_WAVE02_FINAL_EVENT_AUTHORITY_STATUS_AND_EVIDENCE_RECONCILIATION_AWAITING_INDEPENDENT_AUDIT"
    assert data["wave02_worker_classification"] != "PASS_WAVE02_DURABLE_STATE_TRANSACTION_FENCING_AND_AUTHORITY_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
    assert data["wave02_worker_classification"] != "PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
    assert data["wave02_status"] != "NEXT_NOT_STARTED"

    assert "post_v1_durable_operational_store_v1" in data
    wave_data = data["post_v1_durable_operational_store_v1"]
    assert wave_data["classification"] == EXPECTED_WORKER_CLASSIFICATION
    assert wave_data["completed_task"] == EXPECTED_COMPLETED_TASK
    assert wave_data["wave_01_status"] == EXPECTED_WAVE01_STATUS
    assert wave_data["wave_02_status"] == EXPECTED_WAVE02_STATUS
    assert wave_data["wave_03_status"] == EXPECTED_WAVE03_STATUS
    assert wave_data["next_action"] == EXPECTED_NEXT_TASK
    assert wave_data["schema_version"] == 4
    assert wave_data["tables_count"] == 26
    assert data["base_master_head"] == EXPECTED_BASE_MASTER_HEAD
    assert data["starting_branch_head"] == EXPECTED_STARTING_BRANCH_HEAD
    roles = data["authority_roles"]
    assert set(roles) == {
        "accepted_master_authority",
        "historical_release_authority",
        "candidate_branch_authority",
        "planned_next_wave_after_candidate_acceptance",
    }
    assert roles["accepted_master_authority"]["head"] == EXPECTED_BASE_MASTER_HEAD
    assert roles["historical_release_authority"]["release_commit"] == EXPECTED_RELEASE_COMMIT
    assert roles["candidate_branch_authority"]["starting_head"] == EXPECTED_STARTING_BRANCH_HEAD
    assert roles["candidate_branch_authority"]["task"] == EXPECTED_COMPLETED_TASK
    assert roles["candidate_branch_authority"]["classification"] == EXPECTED_WORKER_CLASSIFICATION
    assert roles["candidate_branch_authority"]["completing_commit_sha"] is None
    assert roles["candidate_branch_authority"]["merged"] is False
    assert roles["planned_next_wave_after_candidate_acceptance"]["task"] == EXPECTED_NEXT_TASK
    assert roles["planned_next_wave_after_candidate_acceptance"]["status"] == EXPECTED_WAVE03_STATUS


def test_wave02_schema_and_migration_integrity(tmp_path):
    db_file = tmp_path / "test_meta_schema.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)

    assert store.get_current_schema_version() == SCHEMA_VERSION == 4
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
            "schema_lineage_metadata",
            "legacy_projection_baselines",
            "legacy_artifact_evidence",
            "migration_failure_receipts",
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

        # Verify the internal append guard and immutable event/artifact triggers.
        triggers = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger';").fetchall()]
        assert "trg_transition_events_append_authorized" in triggers
        assert "trg_transition_events_no_update" in triggers
        assert "trg_transition_events_no_delete" in triggers
        assert "trg_artifact_references_insert_authorized" in triggers
        assert "trg_artifact_references_no_update" in triggers
        assert "trg_artifact_references_no_delete" in triggers
    finally:
        conn.close()


def test_wave02_evidence_packet_files_exist():
    packet_dir = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
    assert packet_dir.is_dir()

    required_files = list(PACKET_CLASSIFICATION_FIELDS)
    for filename in required_files:
        path = packet_dir / filename
        assert path.is_file(), f"Missing required packet file: {filename}"
        json_field = PACKET_CLASSIFICATION_FIELDS[filename]
        if json_field is None:
            assert EXPECTED_WORKER_CLASSIFICATION in path.read_text(encoding="utf-8")
        else:
            assert load_json_any_encoding(path)[json_field] == EXPECTED_WORKER_CLASSIFICATION

    schema_manifest = load_json_any_encoding(packet_dir / "schema_manifest.json")
    assert schema_manifest["current_schema_version"] == SCHEMA_VERSION
    assert schema_manifest["current_schema_version"] == 4
    assert len(schema_manifest["triggers"]) == 6
    expected_triggers = [
        "trg_transition_events_append_authorized",
        "trg_transition_events_no_update",
        "trg_transition_events_no_delete",
        "trg_artifact_references_insert_authorized",
        "trg_artifact_references_no_update",
        "trg_artifact_references_no_delete",
    ]
    assert schema_manifest["triggers"] == expected_triggers
    assert [item["semantic_checksum"] for item in schema_manifest["migrations"]] == [
        migration.checksum for migration in MIGRATIONS
    ]
    assert [item["sql_sha256"] for item in schema_manifest["migrations"]] == [
        compute_sha256(migration.sql) for migration in MIGRATIONS
    ]

    final_manifest = load_json_any_encoding(packet_dir / "final_manifest.json")
    roles = final_manifest["authority_roles"]
    assert set(roles) == {
        "accepted_master_authority",
        "historical_release_authority",
        "candidate_branch_authority",
        "planned_next_wave_after_candidate_acceptance",
    }
    assert roles["accepted_master_authority"]["head"] == EXPECTED_BASE_MASTER_HEAD
    assert roles["historical_release_authority"]["annotated_tag"] == "v1.0"
    assert roles["historical_release_authority"]["release_commit"] == EXPECTED_RELEASE_COMMIT
    assert roles["candidate_branch_authority"]["starting_head"] == EXPECTED_STARTING_BRANCH_HEAD
    assert roles["candidate_branch_authority"]["task"] == EXPECTED_COMPLETED_TASK
    assert roles["candidate_branch_authority"]["classification"] == EXPECTED_WORKER_CLASSIFICATION
    assert roles["candidate_branch_authority"]["completing_commit_sha"] is None
    assert roles["candidate_branch_authority"]["merged"] is False
    assert roles["planned_next_wave_after_candidate_acceptance"]["next_task"] == EXPECTED_NEXT_TASK
    assert final_manifest["validation_summary"]["candidate_pass_total"] == EXPECTED_CANDIDATE_PASS_TOTAL
    assert final_manifest["validation_summary"]["monolithic_repository_suite"] == "NOT_RUN"
    assert final_manifest["validation_summary"]["ci_status_checks"] == "NOT_RUN_OR_AVAILABLE"

    changed_inventory = load_json_any_encoding(packet_dir / "changed_file_inventory.json")
    assert changed_inventory["starting_branch_head"] == EXPECTED_STARTING_BRANCH_HEAD
    expected_touched_paths = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in packet_dir.iterdir()
        if path.is_file()
    )
    required_candidate_paths = {
        ".gitignore",
        "AGENTS.md",
        "docs/AI_BUILDER_BOOTSTRAP.md",
        "docs/CURRENT_CONTEXT.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/post_v1_full_automation_maturity_ledger.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md",
        "docs/status/CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md",
        "docs/status/CURRENT_PROJECT_STATUS.md",
        "docs/status/current_project_status.json",
        "live_contentops/durable_operational_store_v1.py",
        "live_contentops/historical_schema_compatibility_v1.py",
        "live_contentops/historical_schema_lineage_v1.py",
        "live_contentops/production_orchestrator_v1.py",
        "tests/fixtures/historical_wave02_schema_lineage_v1.py",
        "tests/fixtures/historical_wave02_schema_objects_v1.json",
        "tests/test_durable_operational_store_v1.py",
        "tests/test_wave02_durable_store_authority_and_metadata_consistency_v1.py",
    }
    assert sorted(changed_inventory["touched_paths"]) == sorted(
        set(expected_touched_paths) | required_candidate_paths
    )
    assert "tests/test_wave01_master_authority_and_metadata_consistency_v1.py" not in changed_inventory["touched_paths"]



def test_existing_state_surface_inventory_paths_and_symbols_exist(tmp_path):
    import importlib

    packet_dir = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
    inventory_path = packet_dir / "existing_state_surface_inventory.json"
    data = load_json_any_encoding(inventory_path)

    surfaces = data.get("surfaces", [])
    assert len(surfaces) >= 7, "Inventory must contain all existing state surfaces"
    assert data["surface_count"] == len(surfaces)
    assert data["inventory_status"] == "COMPLETE_AST_VERIFIED"

    def resolve_reference(reference: str):
        parts = reference.split(".")
        assert parts[:1] == ["live_contentops"] and len(parts) >= 3, f"Invalid reference: {reference}"
        module = importlib.import_module(".".join(parts[:2]))
        resolved = module
        for attribute in parts[2:]:
            assert hasattr(resolved, attribute), f"Reference {reference} is missing {attribute}"
            resolved = getattr(resolved, attribute)
        return resolved

    db_file = tmp_path / "inventory_schema.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    conn = store.get_connection()
    try:
        durable_entities = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
    finally:
        conn.close()

    required_fields = {
        "path",
        "surface_name",
        "owner",
        "authority_class",
        "mutability",
        "symbol",
        "current_reader",
        "current_writer",
        "disposition",
        "superseding_entity",
    }
    for surf in surfaces:
        assert required_fields.issubset(surf), f"Incomplete inventory row: {surf.get('surface_name')}"
        file_path = REPO_ROOT / surf["path"]
        assert file_path.is_file(), f"Inventoried path {surf['path']} does not exist"

        module = importlib.import_module(surf["owner"])
        assert hasattr(module, surf["symbol"]), f"Symbol {surf['symbol']} not found in module {surf['owner']}"
        resolve_reference(surf["current_reader"])

        writer = surf["current_writer"]
        if writer is None:
            assert surf.get("writer_absence_reason") == "read_only_server_quarantine_removed_all_task_mutation_paths"
        else:
            resolve_reference(writer)

        superseding_entities = set(surf["superseding_entity"].split("+"))
        assert superseding_entities <= durable_entities, (
            f"Unknown superseding entities for {surf['surface_name']}: "
            f"{sorted(superseding_entities - durable_entities)}"
        )


def test_markdown_authority_documents_consistency():
    """Assert all authority markdown docs reflect Wave 01 MERGED, Wave 02 AUDIT, Wave 03 NEXT."""
    status_md = (REPO_ROOT / "docs" / "status" / "CURRENT_PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert "Wave 01: Complete" in status_md or "COMPLETE_ACCEPTED_AND_MERGED" in status_md
    assert "Wave 02" in status_md and ("COMPLETE_AWAITING_INDEPENDENT_AUDIT" in status_md or "Awaiting Independent Audit" in status_md)
    assert "Wave 03" in status_md and ("NEXT_NOT_STARTED" in status_md or "Next" in status_md)

    next_task_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1" in next_task_md or "TASK_CONTENTOPS_WAVE02_FINAL_STRONG_AUDIT_COMPLETION_AND_COMPATIBLE_SEMANTIC_MANIFEST_V2" in next_task_md

    master_plan_md = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "current_v6_master_plan.md").read_text(encoding="utf-8")
    assert "Wave 02" in master_plan_md

