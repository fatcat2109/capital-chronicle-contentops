"""Test V6 Canonical Article Studio Refinement Queue Coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import canonical_article_studio_editorial_refinement_queue_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_ARTICLE_STUDIO_EDITORIAL_REFINEMENT_QUEUE"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "canonical_article_studio_refinement_queue_packet.json",
        "canonical_article_studio_refinement_input_contract.json",
        "canonical_article_studio_blocked_refinement_output.json",
        "canonical_article_studio_refinement_slot_status_matrix.json",
        "canonical_article_studio_refinement_checklist.json",
        "canonical_article_studio_refinement_validation_report.json",
        "canonical_article_studio_refinement_blocker_report.md",
        "canonical_article_studio_refinement_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Verify no leaks
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
