"""Test community feedback intake loop orchestrator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import community_feedback_intake_v6 as intake


def test_mock_snapshots_structures():
    snaps = intake.get_mock_snapshots()
    assert len(snaps) > 0
    for s in snaps:
        assert s["allowed_for_publication"] is False
        assert s["human_review_required"] is True
        assert s["public_url_verified"] is False
        assert s["metrics_verified"] is False


def test_empty_template():
    tpl = intake.get_empty_template()
    assert tpl["allowed_for_publication"] is False
    assert tpl["human_review_required"] is True
    assert tpl["public_url_verified"] is False
    assert tpl["metrics_verified"] is False


def test_main_execution(tmp_path):
    out_dir = tmp_path / "V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP"
    intake.main(["--output-dir", str(out_dir)])

    # Check that all 12 files were created
    expected_files = [
        "community_feedback_intake_packet.json",
        "manual_feedback_snapshot_template.json",
        "redacted_feedback_snapshot_sample.json",
        "community_question_cluster_report.json",
        "feedback_summary_ready_packet.json",
        "content_backlog_candidates.json",
        "next_canonical_article_idea_candidates.json",
        "feedback_loop_validation_report.json",
        "feedback_loop_blocker_report.md",
        "feedback_loop_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Load intake packet and verify status properties
    intake_data = json.loads((out_dir / "community_feedback_intake_packet.json").read_text(encoding="utf-8"))
    assert intake_data["community_feedback_loop_status"] == "READY_FOR_REVIEW_ONLY_MANUAL_INTAKE"
    assert intake_data["live_platform_read_performed"] is False
    assert intake_data["scraping_performed"] is False
    assert intake_data["dm_read_performed"] is False
    assert intake_data["reply_or_comment_created"] is False
    assert intake_data["autonomous_engagement_enabled"] is False
    assert intake_data["llm_provider_call_performed"] is False
    assert intake_data["provider_credentials_hydrated"] is False
    assert intake_data["browser_session_started"] is False
    assert intake_data["credentials_hydrated"] is False
    assert intake_data["allowed_for_publication"] is False
    assert intake_data["public_postable"] is False
    assert intake_data["dispatch_allowed_now"] is False
    assert intake_data["live_write_allowed_now"] is False
    assert intake_data["human_review_required"] is True
    assert intake_data["kill_switch_active"] is True
