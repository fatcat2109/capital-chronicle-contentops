"""Unit tests for V5 manual pilot trail reconciliation audit contract."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import re
from unittest.mock import patch

import pytest

from live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract import (
    build_audit_packet,
    run_audit,
    walk_contains_banned_language,
    TASK_LABEL,
    CONTRACT_VERSION,
    SOURCE_BASELINE_COMMIT,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_audit_packet_builds_deterministically():
    """Verify that build_audit_packet creates deterministic hashes."""
    p1 = build_audit_packet()
    p2 = build_audit_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["audit_id"] == p2["audit_id"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["contract_version"] == CONTRACT_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_three_source_packets_consumed():
    """Ensure all three source packets are successfully audited."""
    p = build_audit_packet()
    sources = p["source_packets"]
    assert "0174UW_manual_export" in sources
    assert "0174UY_operator_review" in sources
    assert "0174UZ_reconciliation" in sources

    for name in ("0174UW_manual_export", "0174UY_operator_review", "0174UZ_reconciliation"):
        assert sources[name]["packet_hash"] is not None
        assert sources[name]["contract_version"] is not None


def test_chain_links_are_correct():
    """Ensure chain link hashes and IDs are matched correctly."""
    p = build_audit_packet()
    links = p["chain_links"]
    assert links["uy_to_uw_link"] == "277fb7d44b247efc6021f038e362256f746cc039"
    assert links["uz_to_uw_link"] == "277fb7d44b247efc6021f038e362256f746cc039"
    assert links["uz_to_uy_packet_hash"] == "473a376d9ff812ff830391e24d3cd75fd71b4faf576414f8b8a157b2ea9f284c"
    assert links["uz_to_uy_queue_id"] == "v5_operator_review_queue_473a376d9ff812ff830391e2"


def test_committed_packet_status_verified():
    """Verify that the committed audit packet status is verified_blocked_manual_only."""
    p = build_audit_packet()
    assert p["audit_status"] == "verified_blocked_manual_only"
    assert not p["contradiction_results"]["contradictions_found"]
    assert not p["blocked_reason_results"]["reasons"]


def test_placeholder_integrity_passes_when_empty():
    """Ensure placeholder verification flag is True in the baseline state."""
    p = build_audit_packet()
    assert p["placeholder_integrity_results"]["passed"] is True
    assert p["invariant_results"]["placeholders_remain_empty"] is True


def test_banned_language_walking():
    """Verify recursive walk identifies banned terms on word boundaries only."""
    # Matches exact word boundary
    assert walk_contains_banned_language("Must buy some stocks") is True
    assert walk_contains_banned_language("This is a sell signal") is True
    assert walk_contains_banned_language({"key": "holding pnl details"}) is True
    assert walk_contains_banned_language(["normal text", "trading order fill"]) is True

    # No false positives on subwords
    assert walk_contains_banned_language("manual_metrics_placeholder") is False
    assert walk_contains_banned_language("placeholders") is False
    assert walk_contains_banned_language("operator_notes") is False


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_fake_evidence_fails_audit(mock_load):
    """Test that fake URL, metric, post ID, permalink, or signature fails the audit."""
    def side_effect(path: Path):
        # Load real data
        real_json = json.loads(path.read_text(encoding="utf-8"))
        # Inject fake publish url in UZ
        if "0174UZ" in str(path):
            for field in real_json.get("placeholder_fields", []):
                if field.get("field_id") == "manual_publish_url":
                    field["value"] = "https://fake-substack-url.com/p/my-post"
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:placeholders_remain_empty" in res["blocked_reasons"]
    assert "failed_invariant:no_pretend_evidence" in res["blocked_reasons"]


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_banned_keyword_fails_audit(mock_load):
    """Test that any banned word in any packet fails the audit."""
    def side_effect(path: Path):
        real_json = json.loads(path.read_text(encoding="utf-8"))
        if "0174UW" in str(path):
            real_json["task_label"] = "This is a trading test"
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:no_banned_financial_language" in res["blocked_reasons"]


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_live_action_flag_fails_audit(mock_load):
    """Test that live_dispatch_enabled=True fails the audit."""
    def side_effect(path: Path):
        real_json = json.loads(path.read_text(encoding="utf-8"))
        if "0174UY" in str(path):
            real_json["disabled_live_action_state"]["live_dispatch_enabled"] = True
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:disabled_live_action_states_correct" in res["blocked_reasons"]


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_public_postable_fails_audit(mock_load):
    """Test that public_postable=True fails the audit."""
    def side_effect(path: Path):
        real_json = json.loads(path.read_text(encoding="utf-8"))
        if "0174UW" in str(path):
            real_json["safety_flags"]["public_postable"] = True
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:public_postable_false" in res["blocked_reasons"]


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_dispatch_ready_fails_audit(mock_load):
    """Test that dispatch_ready=True fails the audit."""
    def side_effect(path: Path):
        real_json = json.loads(path.read_text(encoding="utf-8"))
        if "0174UZ" in str(path):
            real_json["safety_flags"]["dispatch_ready"] = True
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:dispatch_ready_false" in res["blocked_reasons"]


@patch("live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract.load_json_packet")
def test_approval_mutation_fails_audit(mock_load):
    """Test that approval_mutation=True fails the audit."""
    def side_effect(path: Path):
        real_json = json.loads(path.read_text(encoding="utf-8"))
        if "0174UZ" in str(path):
            real_json["safety_flags"]["approval_mutation"] = True
        return real_json

    mock_load.side_effect = side_effect
    res = run_audit(Path("."))
    assert res["audit_status"] == "failed_invariant_check"
    assert "failed_invariant:approval_mutation_false" in res["blocked_reasons"]


def test_no_credential_or_network_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/v5_manual_pilot_trail_reconciliation_audit_contract.py", encoding="utf-8") as f:
        content = f.read()
    # Check for imports of os, dotenv, requests, urllib, socket, etc.
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found in contract."


def test_path_restriction_on_write_artifacts():
    """Verify that write_artifacts refuses to write outside docs/automation/0175AA."""
    from live_contentops.v5_manual_pilot_trail_reconciliation_audit_contract import write_artifacts
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AA"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registration():
    """Verify that the ledger contract contains the v5_manual_pilot_trail_reconciliation_audit_future family."""
    assert "v5_manual_pilot_trail_reconciliation_audit_future" in ENTRY_FAMILIES
