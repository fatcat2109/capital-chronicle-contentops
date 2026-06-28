"""Test LLM feedback summarizer main dry-run coordinator."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import llm_feedback_summarizer_dry_run_v6 as coordinator


def test_main_execution(tmp_path):
    out_dir = tmp_path / "V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA"
    
    # Run with default dry_run_stub provider mode
    coordinator.main(["--output-dir", str(out_dir), "--provider-mode", "dry_run_stub"])

    expected_files = [
        "llm_feedback_summarizer_packet.json",
        "feedback_summarizer_prompt_contract.json",
        "feedback_summary_dry_run_output.json",
        "next_idea_generator_packet.json",
        "refined_next_canonical_article_ideas.json",
        "refined_content_backlog_candidates.json",
        "unsafe_feedback_handling_report.json",
        "llm_summary_safety_validation_report.json",
        "llm_feedback_summarizer_blocker_report.md",
        "llm_feedback_summarizer_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Load status packet and check values
    status_data = json.loads((out_dir / "llm_feedback_summarizer_packet.json").read_text(encoding="utf-8"))
    assert status_data["llm_feedback_summarizer_status"] == "READY_FOR_REVIEW_ONLY_DRY_RUN"
    assert status_data["summarizer_mode"] == "dry_run_stub"
    assert status_data["output_mode"] == "dry_run_stub_not_model_output"
    assert status_data["llm_provider_call_performed"] is False
    assert status_data["provider_credentials_hydrated"] is False
    assert status_data["env_read_performed"] is False
    assert status_data["live_platform_read_performed"] is False
    assert status_data["scraping_performed"] is False
    assert status_data["dm_read_performed"] is False
    assert status_data["reply_or_comment_created"] is False
    assert status_data["autonomous_engagement_enabled"] is False
    assert status_data["browser_session_started"] is False
    assert status_data["allowed_for_publication"] is False
    assert status_data["public_postable"] is False
    assert status_data["dispatch_allowed_now"] is False
    assert status_data["live_write_allowed_now"] is False
    assert status_data["human_review_required"] is True
    assert status_data["kill_switch_active"] is True


def test_main_execution_scoping_blocker(tmp_path):
    out_dir = tmp_path / "V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA"
    
    # Run with live_provider_deferred provider mode, which is not scoped in this task
    coordinator.main(["--output-dir", str(out_dir), "--provider-mode", "live_provider_deferred"])

    status_data = json.loads((out_dir / "llm_feedback_summarizer_packet.json").read_text(encoding="utf-8"))
    assert "live_provider_mode_not_scoped" in status_data["blockers"]
