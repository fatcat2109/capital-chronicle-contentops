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

EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION = (
    "PASS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
)
EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION = (
    "PASS_WITH_CAVEAT_WAVE02_INDEPENDENT_AUDIT_AND_SELECTIVE_CORRECTION_AWAITING_CHATGPT_AUDIT"
)

EXPECTED_IMPLEMENTATION_TASK = (
    "TASK_CONTENTOPS_WAVE02_HISTORICAL_SCHEMA_LINEAGE_AND_LEGACY_REPLAY_FINAL_CORRECTION_V1"
)
EXPECTED_CLOSEOUT_TASK = (
    "TASK_CONTENTOPS_WAVE02_INDEPENDENT_AUDIT_AND_SELECTIVE_CORRECTION_OF_DC228AAA_V1"
)

# Work F executed under exact owner scope and correctly produced no publication. These
# constants track the current evidence-refresh blocker, not the historical cohort ceremony.
EXPECTED_NEXT_TASK = "REFRESH_GOVERNED_CAPITAL_CHRONICLE_PUBLICATION_EVIDENCE_AND_RERUN_CANONICAL_CYCLE"
EXPECTED_NEXT_TASK_MODE = "AUTONOMOUS_DEFAULT"
DELIVERED_CORE_V0_TASK = "TASK_CONTENTOPS_DUAL_LANE_CORE_V0_SHADOW_NEWSROOM_V1"
SUPERSEDED_NEXT_TASK = "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1"
EXPECTED_PRODUCT_DIRECTION = "CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED"
EXPECTED_WAVE01_STATUS = "COMPLETE_ACCEPTED_AND_MERGED"
EXPECTED_WAVE02_STATUS = "COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE"
EXPECTED_WAVE03_STATUS = "SUPERSEDED_AS_AUTOMATIC_NEXT_TASK"

EXPECTED_BASE_MASTER_HEAD = "6b6f8718532a4c3f077b09e14f3ca9a4083d4734"
HISTORICAL_PACKET_MASTER_HEAD = "c87e338f25922f4d03454ba199139353ca7198ff"
EXPECTED_RELEASE_COMMIT = "6983bfb3ef300414b744f3f8f97ca81ff699348b"

EXPECTED_IMPLEMENTATION_STARTING_HEAD = "615a96fb20aa97fd76bb3343e9150daec40d9031"
EXPECTED_CLOSEOUT_STARTING_HEAD = "dc228aaa0fa3ad4a478a9252f9b3cff6f8f37703"

IMPLEMENTATION_ROLE_PACKET_FILES = [
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
]

INDEPENDENT_CLOSEOUT_AUDIT_ROLE_FILES = [
    "validation_results.md",
    "changed_file_inventory.json",
    "final_manifest.json",
]


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
    assert data["wave02_worker_classification"] == EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION
    assert data["wave02_status"] == EXPECTED_WAVE02_STATUS
    assert data["wave03_status"] == EXPECTED_WAVE03_STATUS
    assert data["next_task"] == EXPECTED_NEXT_TASK
    assert data["next_task_mode"] == EXPECTED_NEXT_TASK_MODE

    # Owner-approved final product direction is current authority.
    assert data["product_direction_classification"] == EXPECTED_PRODUCT_DIRECTION
    assert data["product_direction_owner_approved"] is True
    assert data["durable_prerequisite_status"] == EXPECTED_WAVE02_STATUS

    # The old Wave 03 approval/outbox routing is no longer the current next task.
    assert data["next_task"] != SUPERSEDED_NEXT_TASK
    assert data["next_recommended_task"] != SUPERSEDED_NEXT_TASK
    assert data["current_next_recommended_task"] != SUPERSEDED_NEXT_TASK
    assert data["superseded_automatic_next_task"] == SUPERSEDED_NEXT_TASK

    # Negative assertions rejecting stale Wave 02 classifications
    assert (
        data["wave02_worker_classification"]
        != "PASS_WAVE02_FINAL_EVENT_AUTHORITY_STATUS_AND_EVIDENCE_RECONCILIATION_AWAITING_INDEPENDENT_AUDIT"
    )
    assert (
        data["wave02_worker_classification"]
        != "PASS_WAVE02_DURABLE_STATE_TRANSACTION_FENCING_AND_AUTHORITY_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
    )
    assert (
        data["wave02_worker_classification"]
        != "PASS_WAVE02_MIGRATION_REPLAY_ASSIGNMENT_AND_EVIDENCE_FINAL_ACCEPTANCE_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
    )
    assert data["wave02_status"] != "NEXT_NOT_STARTED"
    assert data["wave02_status"] != "COMPLETE_AWAITING_INDEPENDENT_AUDIT"

    assert "post_v1_durable_operational_store_v1" in data
    wave_data = data["post_v1_durable_operational_store_v1"]
    assert wave_data["classification"] == EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION
    assert wave_data["completed_task"] == EXPECTED_IMPLEMENTATION_TASK
    assert wave_data["wave_01_status"] == EXPECTED_WAVE01_STATUS
    assert wave_data["wave_02_status"] == EXPECTED_WAVE02_STATUS
    assert wave_data["wave_03_status"] == EXPECTED_WAVE03_STATUS
    assert wave_data["next_action"] == EXPECTED_NEXT_TASK
    assert wave_data["next_action_mode"] == EXPECTED_NEXT_TASK_MODE
    assert wave_data["schema_version"] == 4
    assert wave_data["tables_count"] == 26
    assert data["base_master_head"] == EXPECTED_BASE_MASTER_HEAD
    roles = data["authority_roles"]
    assert set(roles) == {
        "accepted_master_authority",
        "historical_release_authority",
        "product_direction_authority",
        "durable_prerequisite_authority",
        "current_next_task_authority",
    }
    assert roles["accepted_master_authority"]["head"] == EXPECTED_BASE_MASTER_HEAD
    assert roles["historical_release_authority"]["release_commit"] == EXPECTED_RELEASE_COMMIT
    assert roles["product_direction_authority"]["classification"] == EXPECTED_PRODUCT_DIRECTION
    assert roles["product_direction_authority"]["owner_approved"] is True
    assert roles["durable_prerequisite_authority"]["task"] == EXPECTED_IMPLEMENTATION_TASK
    assert roles["durable_prerequisite_authority"]["status"] == EXPECTED_WAVE02_STATUS
    assert roles["durable_prerequisite_authority"]["merged"] is True
    assert roles["current_next_task_authority"]["task"] == EXPECTED_NEXT_TASK
    assert roles["current_next_task_authority"]["mode"] == EXPECTED_NEXT_TASK_MODE


def test_wave02_schema_and_migration_integrity(tmp_path):
    db_file = tmp_path / "test_meta_schema.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)

    assert store.get_current_schema_version() == SCHEMA_VERSION == 7
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
            "performance_observations",
            "learning_policy_versions",
            "operating_controls",
        ]
        for tbl in required_tables:
            assert tbl in tables, f"Missing required table: {tbl}"

        # Migration v5: platform_dispatches persists the exact external public-object identity.
        dispatch_columns = [r[1] for r in conn.execute("PRAGMA table_info(platform_dispatches);").fetchall()]
        assert "public_object_id" in dispatch_columns
        assert "public_object_url" in dispatch_columns
        assert "public_object_url_hash" in dispatch_columns

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
    packet_dir = (
        REPO_ROOT
        / "docs"
        / "automation"
        / "CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
    )
    assert packet_dir.is_dir()

    # 1. Implementation role packet files check
    for filename in IMPLEMENTATION_ROLE_PACKET_FILES:
        path = packet_dir / filename
        assert path.is_file(), f"Missing required implementation packet file: {filename}"
        if filename.endswith(".json"):
            data = load_json_any_encoding(path)
            assert data["worker_classification"] == EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION
        else:
            assert EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION in path.read_text(encoding="utf-8")

    # 2. Independent closeout audit role files check
    for filename in INDEPENDENT_CLOSEOUT_AUDIT_ROLE_FILES:
        path = packet_dir / filename
        assert path.is_file(), f"Missing required closeout audit packet file: {filename}"
        if filename.endswith(".json"):
            data = load_json_any_encoding(path)
            assert data["worker_classification"] == EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION
            assert data["task"] == EXPECTED_CLOSEOUT_TASK
        else:
            content = path.read_text(encoding="utf-8")
            assert EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION in content
            assert EXPECTED_CLOSEOUT_TASK in content

    # 3. Schema manifest checks
    schema_manifest = load_json_any_encoding(packet_dir / "schema_manifest.json")
    assert schema_manifest["current_schema_version"] == SCHEMA_VERSION == 7
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

    # 4. Final manifest checks
    final_manifest = load_json_any_encoding(packet_dir / "final_manifest.json")
    assert final_manifest["task"] == EXPECTED_CLOSEOUT_TASK
    assert final_manifest["worker_classification"] == EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION

    roles = final_manifest["authority_roles"]
    assert set(roles) == {
        "accepted_master_authority",
        "historical_release_authority",
        "candidate_branch_authority",
        "planned_next_wave_after_candidate_acceptance",
    }
    assert roles["accepted_master_authority"]["head"] == HISTORICAL_PACKET_MASTER_HEAD
    assert roles["historical_release_authority"]["annotated_tag"] == "v1.0"
    assert roles["historical_release_authority"]["release_commit"] == EXPECTED_RELEASE_COMMIT
    assert roles["candidate_branch_authority"]["starting_head"] == EXPECTED_CLOSEOUT_STARTING_HEAD
    assert roles["candidate_branch_authority"]["task"] == EXPECTED_CLOSEOUT_TASK
    assert roles["candidate_branch_authority"]["classification"] == EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION
    assert roles["candidate_branch_authority"]["completing_commit_sha"] is None
    assert roles["candidate_branch_authority"]["merged"] is False
    # The historical evidence packet legitimately retains the historical Wave 03 routing
    # it was written under. Current routing lives in the status files, not here.
    assert roles["planned_next_wave_after_candidate_acceptance"]["next_task"] == SUPERSEDED_NEXT_TASK
    assert roles["planned_next_wave_after_candidate_acceptance"]["wave_03_status"] == "NEXT_NOT_STARTED"

    # Check role-aware classification model
    class_model = final_manifest["evidence_packet"]["classification_model"]
    assert (
        class_model["implementation_packet_role"]["classification"]
        == EXPECTED_IMPLEMENTATION_WORKER_CLASSIFICATION
    )
    assert class_model["implementation_packet_role"]["consistent"] is True
    assert (
        class_model["independent_closeout_audit_role"]["classification"]
        == EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION
    )
    assert class_model["independent_closeout_audit_role"]["consistent"] is True
    assert class_model["cross_role_uniform_classification_required"] is False

    # Check validation summary focused closeout scope & monolithic comparison
    val_sum = final_manifest["validation_summary"]
    focused = val_sum["focused_closeout_scope"]
    assert focused["passed"] == 229
    assert focused["preexisting_failures"] == 1
    assert (
        focused["failing_test"]
        == "tests/test_current_project_status_guardrail_v6.py::test_status_markdown_explicit_authority_statements"
    )

    mono = val_sum["monolithic_repository_suite_comparison"]
    assert mono["baseline_dc228aaa"] == {"failed": 393, "passed": 6423, "skipped": 73, "errors": 160}
    assert mono["corrected_worktree"] == {"failed": 390, "passed": 6432, "skipped": 73, "errors": 160}
    assert mono["introduced_failures_found"] == 2
    assert mono["introduced_failures_corrected"] == 2

    assert val_sum["ci_status_checks"] == "NOT_RUN_OR_AVAILABLE"
    assert val_sum["independent_audit"] == "AWAITING_CHATGPT_AUDIT"

    # Reject stale fields explicitly
    assert "candidate_pass_total" not in val_sum or val_sum.get("candidate_pass_total") != 142
    assert val_sum.get("monolithic_repository_suite") != "NOT_RUN"
    assert final_manifest["task"] != EXPECTED_IMPLEMENTATION_TASK

    # 5. Changed inventory checks
    changed_inventory = load_json_any_encoding(packet_dir / "changed_file_inventory.json")
    assert changed_inventory["task"] == EXPECTED_CLOSEOUT_TASK
    assert changed_inventory["worker_classification"] == EXPECTED_CLOSEOUT_WORKER_CLASSIFICATION
    assert changed_inventory["starting_branch_head"] == EXPECTED_CLOSEOUT_STARTING_HEAD
    assert (
        "tests/test_wave02_durable_store_authority_and_metadata_consistency_v1.py"
        in changed_inventory["staged_authorized_paths"]
    )
    assert (
        "tests/test_wave01_master_authority_and_metadata_consistency_v1.py"
        not in changed_inventory["staged_authorized_paths"]
    )


def test_existing_state_surface_inventory_paths_and_symbols_exist(tmp_path):
    import importlib

    packet_dir = (
        REPO_ROOT
        / "docs"
        / "automation"
        / "CONTENTOPS_DURABLE_OPERATIONAL_STORE_AND_CANONICAL_STATE_MACHINE_V1"
    )
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
    """Assert authority markdown reflects the owner-authorized Work F evidence blocker."""
    status_md = (REPO_ROOT / "docs" / "status" / "CURRENT_PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert "Wave 01: Complete" in status_md or EXPECTED_WAVE01_STATUS in status_md
    assert "Wave 02" in status_md and EXPECTED_WAVE02_STATUS in status_md
    assert EXPECTED_PRODUCT_DIRECTION in status_md
    assert EXPECTED_NEXT_TASK in status_md
    assert EXPECTED_NEXT_TASK_MODE in status_md

    next_task_md = (
        REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md"
    ).read_text(encoding="utf-8")
    assert EXPECTED_NEXT_TASK in next_task_md
    assert EXPECTED_NEXT_TASK_MODE in next_task_md
    assert EXPECTED_WAVE02_STATUS in next_task_md
    # CORE V0 is delivered and recorded, not the current next task.
    assert EXPECTED_NEXT_TASK != DELIVERED_CORE_V0_TASK
    # The superseded Wave 03 task must not remain as current routing in the pointer.
    assert SUPERSEDED_NEXT_TASK not in next_task_md

    master_plan_md = (
        REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "current_v6_master_plan.md"
    ).read_text(encoding="utf-8")
    assert EXPECTED_WAVE02_STATUS in master_plan_md
    assert EXPECTED_NEXT_TASK_MODE in master_plan_md
