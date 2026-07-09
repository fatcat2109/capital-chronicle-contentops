# -*- coding: utf-8 -*-
"""Tests for daily database support gap repair plan builder."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_database_support_gap_repair_plan_v0 import build_database_support_gap_repair_plan

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock support packet file
    support_packet = {
        "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
        "selected_title": "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails",
        "selected_topic_family": "macro_policy_rates_liquidity",
        "support_families_requested": [
            "Japan Yield Curve (JGB)",
            "USD/JPY FX Spot & Volatility",
            "Global Central Bank Liquidity Measures"
        ],
        "support_families_resolved": [],
        "support_families_partial": [
            "Japan Yield Curve (JGB)",
            "USD/JPY FX Spot & Volatility"
        ],
        "support_families_missing": [
            "Global Central Bank Liquidity Measures"
        ]
    }

    packet_file = tmp_path / "database_support_packet_v0.json"
    with open(packet_file, "w", encoding="utf-8") as f:
        json.dump(support_packet, f, indent=2)

    return packet_file, tmp_path / "output"

def test_build_database_support_gap_repair_plan(temp_workspace):
    packet_file, output_dir = temp_workspace

    res = build_database_support_gap_repair_plan(
        support_packet_file=packet_file,
        output_dir=output_dir
    )

    # Verify correct normalized files are written
    assert (output_dir / "support_gap_repair_plan_v0.json").exists()
    assert (output_dir / "support_gap_repair_plan_v0.md").exists()
    assert (output_dir / "next_database_tasks_v0.json").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    plan = res["plan"]
    tasks = res["tasks"]
    evidence = res["evidence"]

    # Assert correct idea mapping
    assert plan["selected_idea_id"] == "idea_macro_policy_rates_liquidity_20260709"
    assert plan["selected_title"] == "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails"

    # Assert repair items exist for each requested family
    repairs = plan["gap_repairs"]
    assert "Global Central Bank Liquidity Measures" in repairs
    assert "Japan Yield Curve (JGB)" in repairs
    assert "USD/JPY FX Spot & Volatility" in repairs

    assert repairs["Global Central Bank Liquidity Measures"]["recommended_task"] == "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1"
    assert repairs["Japan Yield Curve (JGB)"]["recommended_task"] == "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1"
    assert repairs["USD/JPY FX Spot & Volatility"]["recommended_task"] == "TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1"

    # Recommended first task exists and is not article drafting
    assert tasks["recommended_first_task"] == "TASK_CAPITAL_CHRONICLE_JAPAN_FX_LIQUIDITY_SOURCE_SUPPORT_VERIFICATION_V0"
    first_task = next(t for t in tasks["tasks"] if t["task_label"] == tasks["recommended_first_task"])
    assert "article_drafting" in first_task["forbidden_actions"]

    # Safety: article_draft_blocked remains true, ready_for_article_draft should not be true
    assert plan["article_draft_blocked"] is True
    assert plan["article_draft_allowed_as_candidate_only"] is False

    # Verify evidence content
    assert evidence["classification"] == "PASS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"
    assert evidence["task_label"] == "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"
    assert evidence["article_draft_blocked"] is True

    # Invariant safety checks
    assert evidence["main_repo_mutated"] is False
    assert evidence["external_fetch_performed"] is False
    assert evidence["no_article_draft_confirmation"] is True
    assert evidence["no_media_confirmation"] is True
    assert evidence["no_platform_write_confirmation"] is True
    assert evidence["no_dispatch_confirmation"] is True
    assert evidence["no_raw_secret_read_confirmation"] is True

    # Ensure no status/pointer files are modified
    # We check that the module does not output anything to status folders, and verify output_paths keys
    for path_val in evidence["output_paths"].values():
        assert "status" not in path_val.replace("\\", "/").split("/")
        assert "next_task_pointer" not in path_val

    # No secrets/sessions/webhooks in values
    def assert_no_secrets(val):
        if isinstance(val, str):
            s = val.lower()
            for forbidden in ("secret", "token", "cookie", "password", "session", "webhook"):
                # Allow path/keys containing these
                if forbidden in s and not any(ext in s for ext in ("v0.json", "v0.md", "v0.jsonl", "py")):
                    raise AssertionError(f"Forbidden term '{forbidden}' found in value: {val}")
        elif isinstance(val, dict):
            for v in val.values():
                assert_no_secrets(v)
        elif isinstance(val, list):
            for v in val:
                assert_no_secrets(v)

    assert_no_secrets(res)
