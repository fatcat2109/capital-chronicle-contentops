"""Test V6 Canonical Draft Operator Source Pack Review UI Coordinator."""
from __future__ import annotations

import json
from pathlib import Path

from live_contentops import canonical_draft_operator_source_pack_review_ui_v6 as ui_coordinator


def test_ui_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW"
    ui_coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "operator_source_pack_review_packet.json",
        "operator_source_pack_review_checklist.json",
        "operator_source_pack_approval_template.json",
        "operator_source_pack_review_validation_report.json",
        "operator_source_pack_review_local_mock.html",
        "operator_source_pack_review_screenshot_manifest.json",
        "operator_source_pack_review_blocker_report.md",
        "operator_source_pack_review_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Verify task label in reports
    blocker_md = (out_dir / "operator_source_pack_review_blocker_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_IMPORT_UI_AND_APPROVAL_REVIEW_HEAVY_BATCH_V0" in blocker_md

    impl_md = (out_dir / "implementation_report.md").read_text(encoding="utf-8")
    assert "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_IMPORT_UI_AND_APPROVAL_REVIEW_HEAVY_BATCH_V0" in impl_md

    # Check for zero leakage of operator_jim_sig, real URLs, or fake evidence hashes in output files
    for name in expected_files:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
