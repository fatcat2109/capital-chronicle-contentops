"""Test source pack verification UI coordinator execution."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import source_pack_verification_ui_v6 as coordinator


def test_main_execution(tmp_path):
    out_dir = tmp_path / "V6_SOURCE_PACK_VERIFICATION_UI"
    coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "source_pack_verification_ui_packet.json",
        "operator_research_checklist.json",
        "source_evidence_entry_template.json",
        "source_pack_draft_template.json",
        "source_pack_draft_validation_report.json",
        "source_pack_operator_workflow.md",
        "source_pack_verification_local_mock.html",
        "source_pack_ui_screenshot_manifest.json",
        "source_pack_verification_blocker_report.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Load UI packet and verify review-only/blocked flags
    packet = json.loads((out_dir / "source_pack_verification_ui_packet.json").read_text(encoding="utf-8"))
    assert packet["source_pack_verification_ui_status"] == "READY_FOR_REVIEW_ONLY_OPERATOR_RESEARCH"
    assert packet["real_source_fetch_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["provider_call_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["source_pack_verified"] is False
    assert packet["source_pack_complete"] is False
    assert packet["draft_generation_allowed"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["human_review_required"] is True
    assert packet["source_verification_required"] is True
    assert packet["kill_switch_active"] is True

    # Check html
    html = (out_dir / "source_pack_verification_local_mock.html").read_text(encoding="utf-8")
    assert "OFFLINE CONTROL TOWER: REVIEW-ONLY PREVIEW" in html
    assert "Compliance Blockers" in html
    assert "operator_source_entries_missing" in html
