"""Test next canonical article packet generation and selection driver."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops import next_canonical_article_packet_v6 as coordinator


def test_select_candidate():
    ideas = [
        {"refined_idea_id": "idea_1", "priority_score": 5.0},
        {"refined_idea_id": "idea_2", "priority_score": 8.0},
        {"refined_idea_id": "idea_3", "priority_score": 8.0}
    ]
    # deterministic sort: priority score DESC, then ID DESC for ties
    selected = coordinator.select_candidate(ideas)
    assert selected["refined_idea_id"] == "idea_3"
    assert selected["priority_score"] == 8.0


def test_main_execution(tmp_path):
    out_dir = tmp_path / "V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG"
    coordinator.main(["--output-dir", str(out_dir)])

    expected_files = [
        "next_canonical_article_packet.json",
        "selected_backlog_candidate.json",
        "article_research_requirements.json",
        "source_verification_checklist.json",
        "article_claim_ledger_scaffold.json",
        "article_outline_packet.json",
        "editorial_risk_matrix.json",
        "downstream_platform_readiness_placeholders.json",
        "article_planning_validation_report.json",
        "article_planning_blocker_report.md",
        "article_planning_runbook.md",
        "implementation_report.md",
        "next_task_pointer.md"
    ]

    for name in expected_files:
        assert (out_dir / name).exists()

    # Verify packet flags
    packet = json.loads((out_dir / "next_canonical_article_packet.json").read_text(encoding="utf-8"))
    assert packet["source_verification_required"] is True
    assert packet["claim_ledger_required"] is True
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["human_review_required"] is True
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["kill_switch_active"] is True

    # Verify downstream placeholders
    placeholders = json.loads((out_dir / "downstream_platform_readiness_placeholders.json").read_text(encoding="utf-8"))
    for k, v in placeholders.items():
        assert v["generated"] is False
        assert v["public_postable"] is False
        assert v["dispatch_allowed_now"] is False
        assert v["source_verification_required"] is True
        assert v["human_review_required"] is True
