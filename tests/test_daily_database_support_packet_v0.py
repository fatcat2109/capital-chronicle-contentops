# -*- coding: utf-8 -*-
"""Tests for daily database support packet builder."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_database_support_packet_v0 import build_database_support_packet

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock idea selection file
    idea_selection = {
        "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
        "selected_title": "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails",
        "selected_topic_family": "macro_policy_rates_liquidity",
        "database_support_needed": [
            "Japan Yield Curve (JGB)",
            "USD/JPY FX Spot & Volatility",
            "Global Central Bank Liquidity Measures"
        ]
    }
    
    idea_file = tmp_path / "article_idea_selection_v0.json"
    with open(idea_file, "w", encoding="utf-8") as f:
        json.dump(idea_selection, f, indent=2)

    # Setup mock database repo structure
    db_repo = tmp_path / "mock_db_repo"
    
    jgb_dir = db_repo / "docs/research/database_foundation/apac_china_japan_official_macro_contracts"
    jgb_dir.mkdir(parents=True, exist_ok=True)
    jgb_file = jgb_dir / "APAC_CHINA_JAPAN_API_SOURCE_CONTRACTS_V1.json"
    with open(jgb_file, "w", encoding="utf-8") as f:
        json.dump({"contract_status": "candidate_only"}, f, indent=2)

    oanda_dir = db_repo / "data/audit/data_sufficiency/task_usdjpy_oanda_practice_readonly_source_review_and_contract_v1"
    oanda_dir.mkdir(parents=True, exist_ok=True)
    oanda_file = oanda_dir / "usdjpy_oanda_practice_source_contract.json"
    with open(oanda_file, "w", encoding="utf-8") as f:
        json.dump({"authority_status": "candidate_only"}, f, indent=2)

    return idea_file, tmp_path / "output", db_repo

def test_build_database_support_packet(temp_workspace):
    idea_file, output_dir, db_repo = temp_workspace

    res = build_database_support_packet(
        idea_selection_file=idea_file,
        output_dir=output_dir,
        main_db_repo=db_repo
    )

    # Verify files created
    assert (output_dir / "database_support_packet_v0.json").exists()
    assert (output_dir / "database_support_summary_v0.md").exists()
    assert (output_dir / "source_gap_report_v0.json").exists()
    assert (output_dir / "run_evidence_v0.json").exists()

    packet = res["packet"]
    gap = res["gap"]
    evidence = res["evidence"]

    # Assert correct idea mapping
    assert packet["selected_idea_id"] == "idea_macro_policy_rates_liquidity_20260709"
    assert packet["selected_title"] == "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails"

    # Assert honest availability mapping
    assert packet["support_items"]["Japan Yield Curve (JGB)"]["availability"] == "partial"
    assert packet["support_items"]["USD/JPY FX Spot & Volatility"]["availability"] == "partial"
    assert packet["support_items"]["Global Central Bank Liquidity Measures"]["availability"] == "missing"

    # Gaps exist, ready_for_article_draft must be false
    assert packet["ready_for_article_draft"] is False
    assert len(packet["support_families_missing"]) == 1
    assert "Global Central Bank Liquidity Measures" in packet["support_families_missing"]

    # Verify gap report content
    assert gap["task_label"] == "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_PACKET_V0"
    assert "Global Central Bank Liquidity Measures" in gap["missing_families"]
    assert len(gap["recommended_next_data_ingestion_tasks"]) > 0

    # Verify evidence content
    assert evidence["classification"] == "PASS_WITH_GAPS_DAILY_DATABASE_SUPPORT_PACKET_V0"
    assert evidence["available_count"] == 0
    assert evidence["partial_count"] == 2
    assert evidence["missing_count"] == 1

    # Invariant safety checks
    assert packet["main_repo_mutated"] is False
    assert packet["external_fetch_performed"] is False
    assert packet["exact_numeric_claims_made"] is False

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

def test_missing_database_repo_fallback(tmp_path):
    # Setup mock idea selection file
    idea_selection = {
        "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
        "selected_title": "Japan's Debt Crisis",
        "selected_topic_family": "macro_policy_rates_liquidity",
        "database_support_needed": ["Japan Yield Curve (JGB)"]
    }
    
    idea_file = tmp_path / "article_idea_selection_v0.json"
    with open(idea_file, "w", encoding="utf-8") as f:
        json.dump(idea_selection, f, indent=2)

    # Call with non-existent database repo
    res = build_database_support_packet(
        idea_selection_file=idea_file,
        output_dir=tmp_path / "output",
        main_db_repo=tmp_path / "non_existent_db_repo"
    )

    # Should fall back to missing
    assert res["packet"]["support_items"]["Japan Yield Curve (JGB)"]["availability"] == "missing"
    assert res["packet"]["ready_for_article_draft"] is False
    assert res["evidence"]["missing_count"] == 1
