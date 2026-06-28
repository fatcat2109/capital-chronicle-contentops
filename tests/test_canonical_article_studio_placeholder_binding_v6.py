"""Test V6 Canonical Article Studio Placeholder Binding Coordinator."""
from __future__ import annotations

from pathlib import Path
from live_contentops import canonical_article_studio_placeholder_binding_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_ARTICLE_STUDIO_PLACEHOLDER_BINDING"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "canonical_article_studio_placeholder_binding_packet.json",
        "canonical_article_studio_slot_binding_map.json",
        "canonical_article_studio_placeholder_binding_review.json",
        "canonical_article_studio_placeholder_bound_shell_instance.json",
        "canonical_article_studio_placeholder_binding_validation_report.json",
        "canonical_article_studio_placeholder_binding_blocker_report.md",
        "canonical_article_studio_placeholder_binding_runbook.md",
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
