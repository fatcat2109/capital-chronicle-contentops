"""Unit tests for V5 local operator runbook index contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.v5_local_operator_runbook_index_contract import (
    build_contract_packet,
    walk_contains_banned_language,
    TASK_LABEL,
    CONTRACT_VERSION,
    SOURCE_BASELINE_COMMIT,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_runbook_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["runbook_id"] == p2["runbook_id"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["contract_version"] == CONTRACT_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_five_runbook_steps_represented():
    """Ensure all five local pilot workflow steps are represented."""
    p = build_contract_packet()
    steps = p["runbook_steps"]
    assert len(steps) == 5

    step_ids = [s["step_id"] for s in steps]
    expected_ids = [
        "preflight_bundle",
        "manual_export_pilot_verification",
        "operator_review_queue",
        "manual_pilot_reconciliation",
        "evidence_vault_manual_pilot_audit",
    ]
    assert step_ids == expected_ids

    # Verify key field requirements
    for step in steps:
        assert "step_id" in step
        assert "view_id" in step
        assert "source_packet" in step
        assert "status" in step
        assert "operator_meaning" in step
        assert "what_human_can_do" in step
        assert "what_system_cannot_do" in step
        assert "blocked_reasons" in step
        assert "missing_evidence" in step
        assert "evidence_refs" in step
        assert "next_safe_step" in step


def test_every_step_is_local_only_and_manual():
    """Verify safety state flags enforce local-only bounds."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["local_only"] is True
    assert safety["manual_only"] is True
    assert safety["no_platform_api"] is True
    assert safety["no_credentials"] is True
    assert safety["no_live_dispatch"] is True
    assert safety["public_postable"] is False
    assert safety["dispatch_ready"] is False
    assert safety["approval_mutation"] is False
    assert safety["credential_values_loaded"] is False
    assert safety["network_performed"] is False


def test_banned_language_walking():
    """Verify walk_contains_banned_language checks boundaries only."""
    assert walk_contains_banned_language("This is a sell signal") is True
    assert walk_contains_banned_language("Must hold the asset") is True
    assert walk_contains_banned_language("Banned word pnl detail") is True
    assert walk_contains_banned_language("Normal operator note") is False
    assert walk_contains_banned_language("manual_metrics_placeholder") is False


def test_no_credential_or_network_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/v5_local_operator_runbook_index_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_path_restriction_on_write_artifacts():
    """Verify that write_artifacts refuses to write outside docs/automation/0175AD."""
    from live_contentops.v5_local_operator_runbook_index_contract import write_artifacts
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AD"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registration():
    """Verify that the ledger contract contains the v5_local_operator_runbook_index_future family."""
    assert "v5_local_operator_runbook_index_future" in ENTRY_FAMILIES
