"""Test V6 Canonical Article Studio Editor Shell Coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import canonical_article_studio_editor_shell_v6 as coordinator


def test_coordinator_execution(tmp_path):
    out_dir = tmp_path / "V6_CANONICAL_ARTICLE_STUDIO_EDITOR_DRAFT_SHELL"
    coordinator.main(["--output-dir", str(out_dir)])

    expected = [
        "canonical_article_studio_draft_shell_packet.json",
        "canonical_article_studio_draft_slot_schema.json",
        "canonical_article_studio_draft_shell_instance.json",
        "canonical_article_studio_editor_shell_checklist.json",
        "canonical_article_studio_editor_shell_validation_report.json",
        "canonical_article_studio_editor_shell_local_mock.html",
        "canonical_article_studio_editor_shell_screenshot_manifest.json",
        "canonical_article_studio_editor_shell_blocker_report.md",
        "canonical_article_studio_editor_shell_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected:
        assert (out_dir / name).exists()

    # Verify no raw/fake credentials, signatures, names or URLs leaked
    for name in expected:
        content = (out_dir / name).read_text(encoding="utf-8")
        assert "operator_jim_sig" not in content
        assert "federalreserve.gov" not in content
        assert "test.treasury.gov" not in content
        assert "e3b0c442" not in content
        
    # Check for static HTML mock guidelines
    html_mock = (out_dir / "canonical_article_studio_editor_shell_local_mock.html").read_text(encoding="utf-8")
    assert "<script" not in html_mock.lower()
    assert "visual-pass" not in html_mock.lower()
    
    # Check for screenshot manifest settings
    manifest_data = json.loads((out_dir / "canonical_article_studio_editor_shell_screenshot_manifest.json").read_text(encoding="utf-8"))
    assert manifest_data["visual_pass_claimed"] is False
    assert manifest_data["screenshot_created"] is False
