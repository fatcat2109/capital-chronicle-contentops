"""Unit tests for Lane C editorial-brief-to-draft review-only packet contract."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from live_contentops.lane_c_editorial_brief_to_draft_review_only_packet_contract import (
    build_contract_packet,
    TASK_LABEL,
    MATRIX_VERSION,
    SOURCE_BASELINE_COMMIT,
    write_artifacts,
)
from live_contentops.redacted_immutable_audit_ledger_v2_contract import ENTRY_FAMILIES


def test_draft_packet_builds_deterministically():
    """Verify that build_contract_packet creates deterministic hashes."""
    p1 = build_contract_packet()
    p2 = build_contract_packet()
    assert p1["packet_hash"] == p2["packet_hash"]
    assert p1["task_label"] == TASK_LABEL
    assert p1["matrix_version"] == MATRIX_VERSION
    assert p1["source_baseline_commit"] == SOURCE_BASELINE_COMMIT


def test_consumes_0175aj_brief_packet_data():
    """Verify that the contract successfully consumes and registers the 7 briefs from 0175AJ."""
    p = build_contract_packet()
    drafts = p["draft_packets"]
    assert len(drafts) == 7

    draft_source_ids = {d["source_candidate_id"] for d in drafts}
    expected_ids = {
        "candidate_shape_valid_but_not_authorized",
        "candidate_missing_lineage_manifest",
        "candidate_stale_or_missing_freshness",
        "candidate_degraded_proxy_label_required",
        "candidate_missing_operator_approval",
        "candidate_local_fixture_only",
        "candidate_quarantined_review_only",
    }
    assert draft_source_ids == expected_ids


def test_creates_review_only_drafts_from_eligible_briefs():
    """Ensure all draft packets are review-only."""
    p = build_contract_packet()
    for d in p["draft_packets"]:
        assert d["review_only"] is True
        assert d["public_postable"] is False
        assert d["dispatch_ready"] is False


def test_preserves_rejected_forbidden_public_ready_precedent():
    """Verify that the rejected candidate from 0175AJ is preserved in rejected_decisions."""
    p = build_contract_packet()
    rejected = p["rejected_decisions"]
    assert len(rejected) == 1
    assert rejected[0]["source_candidate_id"] == "candidate_forbidden_public_ready_claim"
    assert rejected[0]["verdict"] == "rejected"


def test_human_review_required_is_true():
    """Verify human review remains required for all stubs/packets."""
    p = build_contract_packet()
    for d in p["draft_packets"]:
        assert d["human_review_required"] is True
        assert d["operator_approval_required"] is True


def test_claim_ledger_no_fake_numeric_truth():
    """Ensure claim ledger items exist but contain no numeric/market truths."""
    p = build_contract_packet()
    for d in p["draft_packets"]:
        assert len(d["claim_ledger"]) > 0
        for item in d["claim_ledger"]:
            text = item["claim_text"].lower()
            # Ensure no numbers, forecasts or targets are mentioned
            assert not any(t in text for t in ["price", "yield", "spread", "forecast", "target"])


def test_citation_and_limitations_preserved():
    """Verify citation requirements and limitation blocks are preserved in draft packets."""
    p = build_contract_packet()
    drafts = {d["source_candidate_id"]: d for d in p["draft_packets"]}

    stale_draft = drafts["candidate_stale_or_missing_freshness"]
    assert len(stale_draft["limitation_blocks"]) > 0
    assert stale_draft["limitation_blocks"][0]["severity"] == "blocker"


def test_unresolved_evidence_flags_preserved():
    """Verify unresolved evidence flags are preserved."""
    p = build_contract_packet()
    for d in p["draft_packets"]:
        assert "cryptographic_lineage_unverified" in d["unresolved_evidence_flags"]


def test_dqr_readiness_current_truth_not_cleared():
    """Ensure safety flags prevent DQR/readiness clearance."""
    p = build_contract_packet()
    safety = p["safety_flags"]
    assert safety["dqr_cleared_by_contentops"] is False
    assert safety["readiness_cleared_by_contentops"] is False
    assert safety["current_truth_promoted"] is False


def test_no_credential_network_or_env_imports():
    """Verify that no sensitive environment/network/credential modules are imported."""
    with open("live_contentops/lane_c_editorial_brief_to_draft_review_only_packet_contract.py", encoding="utf-8") as f:
        content = f.read()
    forbidden = ["import os", "from os", "import requests", "urllib", "dotenv", "socket"]
    for pattern in forbidden:
        assert pattern not in content, f"Forbidden import or keyword '{pattern}' found."


def test_write_artifacts_path_restrictions():
    """Verify that write_artifacts fails with ValueError outside docs/automation/0175AK."""
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0175AK"):
        write_artifacts(repo_root=".", output_dir="docs/automation/other")


def test_ledger_family_registered():
    """Verify ledger family is correctly registered in entry families."""
    assert "lane_c_editorial_brief_to_draft_review_only_packet_future" in ENTRY_FAMILIES


def test_progress_ledger_file_is_updated():
    """Verify that the progress ledger includes 0175AK and the next recommended task."""
    path = Path("docs/CONTENTOPS_PROGRESS_LEDGER_AND_FINAL_PRODUCT_CHECKLIST.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_0175AK" in content
    assert "TASK_CONTENTOPS_0175AL" in content
