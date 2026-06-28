"""Test V6 Canonical Draft from Approved Redacted Source Pack Coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import canonical_draft_from_approved_redacted_source_pack_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "canonical_draft_eligibility_packet.json",
        "test_only_approved_redacted_source_pack_summary.json",
        "canonical_draft_claim_eligibility_matrix.json",
        "canonical_draft_generation_blocked_preview.md",
        "canonical_draft_eligibility_validation_report.json",
        "canonical_draft_eligibility_blocker_report.md",
        "canonical_draft_eligibility_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Verify no raw/fake credentials or signature values leaked
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
        
    # Check for the required banner in the markdown preview
    preview_content = (out_dir / "canonical_draft_generation_blocked_preview.md").read_text(encoding="utf-8")
    assert "TEST-ONLY APPROVAL SIMULATION" in preview_content
    assert "NOT RUNTIME TRUTH" in preview_content
    assert "NO ARTICLE COPY GENERATED" in preview_content
