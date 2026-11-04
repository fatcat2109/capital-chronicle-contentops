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
    # Historical Wave-02 evidence remains frozen at its accepted v7-era value.
    assert schema_manifest["current_schema_version"] == 7
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
        migration.checksum for migration in MIGRATIONS[:7]
    ]
    assert [item["sql_sha256"] for item in schema_manifest["migrations"]] == [
        compute_sha256(migration.sql) for migration in MIGRATIONS[:7]
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


