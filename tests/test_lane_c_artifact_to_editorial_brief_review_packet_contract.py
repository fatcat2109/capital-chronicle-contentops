"""Unit tests for Lane C artifact-to-editorial-brief review packet contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_artifact_to_editorial_brief_review_packet_contract import (
    build_contract_packet,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    write_artifacts,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_brief_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_consumes_0175ai_ingestion_foundation_packet():
    """Verify that the contract successfully consumes and registers candidate bindings from 0175AI."""
    p = build_contract_packet()
    bindings = p["source_bindings"]
    assert len(bindings) == 8

    # All candidate IDs from 0175AI must be bound
    bound_ids = {b["candidate_id"] for b in bindings}
    expected_ids = {
        "candidate_shape_valid_but_not_authorized",
        "candidate_missing_lineage_manifest",
        "candidate_stale_or_missing_freshness",
        "candidate_degraded_proxy_label_required",
        "candidate_missing_operator_approval",
        "candidate_forbidden_public_ready_claim",
        "candidate_local_fixture_only",
        "candidate_quarantined_review_only",
    }
    assert bound_ids == expected_ids


def test_creates_review_packets_only_for_eligible_candidates():
    """Ensure that only non-rejected candidates get a brief review packet."""
    p = build_contract_packet()
    briefs = p["brief_packets"]

    # 8 candidates, candidate_forbidden_public_ready_claim is rejected, so 7 briefs should be created.
    assert len(briefs) == 7

    brief_source_ids = {b["source_candidate_id"] for b in briefs}
    assert "candidate_forbidden_public_ready_claim" not in brief_source_ids


def test_rejected_forbidden_public_ready_candidate_remains_rejected():
    """Ensure the forbidden public ready candidate is explicitly rejected in decisions."""
    p = build_contract_packet()
    decisions = p["decisions"]

    forbidden_decision = next(d for d in decisions if d["source_candidate_id"] == "candidate_forbidden_public_ready_claim")
    assert forbidden_decision["verdict"] == "rejected"
    assert "forbidden_public_ready_claim" in forbidden_decision["blocked_reasons"]


def test_public_postable_and_dispatch_ready_are_false():
    """Verify that all briefs have public_postable and dispatch_ready set to False."""
    p = build_contract_packet()
    for b in p["brief_packets"]:
        assert b["public_postable"] is False
        assert b["dispatch_ready"] is False


def test_human_review_required_is_true():
    """Verify that human_review_required is True for every generated brief review packet."""
    p = build_contract_packet()
    for b in p["brief_packets"]:
        assert b["human_review_required"] is True


def test_dqr_readiness_current_truth_never_cleared():
    """Verify that DQR, readiness, and current truth safety flags remain False."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False


def test_missing_degraded_proxy_labels_preserved():
    """Ensure that missing, degraded, or proxy labels are preserved in generated briefs."""
    p = build_contract_packet()
    briefs = {b["source_candidate_id"]: b for b in p["brief_packets"]}

    degraded_brief = briefs["candidate_degraded_proxy_label_required"]
    assert "degraded_proxy" in degraded_brief["missing_degraded_proxy_labels"]
    assert "source_health_degraded" in degraded_brief["missing_degraded_proxy_labels"]


def test_limitations_and_citation_refs_preserved():
    """Ensure citation refs and limitations from the ingestion candidates are preserved."""
    p = build_contract_packet()
    briefs = {b["source_candidate_id"]: b for b in p["brief_packets"]}

    stale_brief = briefs["candidate_stale_or_missing_freshness"]
    assert "Data age exceeds maximum tolerated limit. Freshness metadata is expired or absent." in stale_brief["limitations"]


def test_no_fake_numeric_truth_or_market_numbers():
    """Verify the guardrail checking that no market numbers are generated."""
    p = build_contract_packet()
    guardrails = {g["guardrail_id"]: g for g in p["guardrails"]}
    assert guardrails["no_market_numbers"]["passed"] is True
    assert guardrails["no_public_ready_draft"]["passed"] is True


def test_safety_flags_verification():
    """Verify that the safety flags strictly enforce local-only and mock-only constraints."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["local_only"] is True
    assert safety["fixture_only"] is True
    assert safety["network_performed"] is False
    assert safety["env_read"] is False
    assert safety["credential_values_loaded"] is False
    assert safety["platform_api_called"] is False
    assert safety["provider_api_called"] is False
    assert safety["ingestion_repo_mutated"] is False
    assert safety["financial_advice"] is False
    assert safety["signal_language"] is False
    assert safety["broker_order_execution"] is False
    assert safety["raw_vendor_redistribution"] is False
    assert safety["approved_internal_alpha_artifacts_available"] is False
    assert safety["writer_generated_public_draft"] is False


def test_no_credential_network_or_env_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/lane_c_artifact_to_editorial_brief_review_packet_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_write_artifacts_path_restrictions():
    """Verify that write_artifacts fails with ValueError outside docs/automation/0175AJ."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AJ"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registered():
    """Verify ledger family is correctly registered in entry families."""
    assert "lane_c_artifact_to_editorial_brief_review_packet_future" in ENTRY_FAMILIES


def test_progress_ledger_file_is_updated():
    """Verify that the progress ledger includes 0175AJ and the next recommended task."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_0175AJ" in content
    assert "TASK_CONTENTOPS_0175AK_LANE_C_EDITORIAL_BRIEF_TO_DRAFT_REVIEW_ONLY_PACKET_V0" in content
