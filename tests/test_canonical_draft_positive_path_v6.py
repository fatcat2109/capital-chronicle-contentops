"""Test V6 Canonical Draft Positive Path Coordinator."""
from __future__ import annotations

import json
from pathlib import Path

from live_contentops import canonical_draft_positive_path_v6 as coordinator


def test_coordinator_main_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN"
    coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "canonical_draft_positive_path_packet.json",
        "test_only_verified_source_pack_fixture_summary.json",
        "test_only_claim_source_binding_proof.json",
        "canonical_draft_review_only_packet.json",
        "canonical_draft_review_only_preview.md",
        "canonical_draft_positive_path_validation_report.json",
        "canonical_draft_positive_path_blocker_report.md",
        "canonical_draft_positive_path_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Verify task label in reports
    blocker_md = (out_dir / "canonical_draft_positive_path_blocker_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_GENERATION_FROM_VERIFIED_SOURCE_PACK_POSITIVE_PATH_DRY_RUN_HEAVY_BATCH_V0" in blocker_md

    impl_md = (out_dir / "implementation_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_GENERATION_FROM_VERIFIED_SOURCE_PACK_POSITIVE_PATH_DRY_RUN_HEAVY_BATCH_V0" in impl_md

    # Check for zero leakage of operator_jim_sig, real URLs, or fake evidence hashes in output files
    for name in expected_files:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        # Check that we don't leak mock URLs or hashes to runtime artifacts
        assert "https://test.treasury.gov" not in content
        assert "e3b0c442" not in content
