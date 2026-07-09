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

    # Verify files created
    assert (output_dir / "database_support_gap_repair_plan_v0.json").exists()
    assert (output_dir / "database_support_gap_repair_summary_v0.md").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    plan = res["plan"]
    evidence = res["evidence"]

    # Assert correct idea mapping
    assert plan["selected_idea_id"] == "idea_macro_policy_rates_liquidity_20260709"
    assert plan["selected_title"] == "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails"

    # Assert recommended task mappings
    repairs = plan["gap_repairs"]
    assert repairs["Global Central Bank Liquidity Measures"]["recommended_task"] == "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1"
    assert repairs["Japan Yield Curve (JGB)"]["recommended_task"] == "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1"
    assert repairs["USD/JPY FX Spot & Volatility"]["recommended_task"] == "TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1"

    # Safety: ready_for_article_draft must be false
    assert plan["ready_for_article_draft"] is False
    assert plan["ready_for_data_ingestion_runs"] is True

    # Verify evidence content
    assert evidence["classification"] == "PASS_WITH_GAPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"

    # Invariant safety checks
    assert evidence["main_repo_mutated"] is False
    assert evidence["external_fetch_performed"] is False
    assert evidence["no_article_draft_confirmation"] is True
    assert evidence["no_media_confirmation"] is True
    assert evidence["no_platform_write_confirmation"] is True
    assert evidence["no_dispatch_confirmation"] is True
    assert evidence["no_raw_secret_read_confirmation"] is True

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
