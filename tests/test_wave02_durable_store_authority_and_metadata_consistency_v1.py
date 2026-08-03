"""
Wave 02 Metadata, Authority, and Audit Consistency Verification Suite v1.
"""

import json
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_wave02_metadata_and_authority_consistency():
    agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    curr_ctx = (REPO_ROOT / "docs" / "CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    bootstrap = (REPO_ROOT / "docs" / "AI_BUILDER_BOOTSTRAP.md").read_text(encoding="utf-8")
    next_pointer = (REPO_ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md").read_text(encoding="utf-8")
    status_json = json.loads((REPO_ROOT / "docs" / "status" / "current_project_status.json").read_text(encoding="utf-8"))

    # Classification
    expected_classification = "PASS_WAVE02_DURABLE_STATE_TRANSACTION_FENCING_AND_AUTHORITY_CORRECTION_AWAITING_INDEPENDENT_AUDIT"
    expected_status = "COMPLETE_AWAITING_INDEPENDENT_AUDIT"
    expected_wave03 = "NEXT_NOT_STARTED"
    expected_next_task = "TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1"

    assert expected_classification in agents_md or expected_classification in curr_ctx
    assert status_json["wave02_status"] == expected_status
    assert status_json["wave03_status"] == expected_wave03
    assert status_json["next_task"] == expected_next_task

    # Wave 01 metadata must remain unchanged
    assert status_json["wave01_classification"] == "PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED"
    assert status_json["wave01_status"] == "COMPLETE_ACCEPTED_AND_MERGED"


def test_wave02_store_schema_and_integrity():
    from live_contentops.durable_operational_store_v1 import (
        ContentOpsDurableStore,
        SCHEMA_VERSION,
        CANONICAL_STATES,
        WAVE02_PROTECTED_STATES,
    )

    assert SCHEMA_VERSION == 2
    assert len(CANONICAL_STATES) == 29
    assert "APPROVED_EXACT" in WAVE02_PROTECTED_STATES
    assert "OUTBOX_READY" in WAVE02_PROTECTED_STATES
    assert "DISPATCHING" in WAVE02_PROTECTED_STATES
