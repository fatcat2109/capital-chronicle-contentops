"""Tests for daily headline clustering and idea selection module."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from live_contentops.daily_headline_cluster_rank_article_idea_packet_v0 import (
    build_article_idea_packet,
    classify_headline_to_family,
    TASK_LABEL,
)

MOCK_HEADLINES = [
    # Macro policy & rates & liquidity
    {
        "headline_id": "hl_macro_1",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "source_account_or_list": "FirstSquawk",
        "captured_at": "2026-07-08T12:00:00Z",
        "observed_at": "2026-07-08 19:00:00 GMT+7",
        "url_or_source_ref": "https://x.com/FirstSquawk/status/1",
        "headline_text": "BREAKING: FED TO CUT INTEREST RATES BY 25BPS IN JULY MEETING.",
        "raw_excerpt": "BREAKING: FED TO CUT INTEREST RATES BY 25BPS IN JULY MEETING.",
        "tags": ["central_bank", "rates"],
        "capture_mode": "fixture_local"
    },
    {
        "headline_id": "hl_macro_2",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "source_account_or_list": "FirstSquawk",
        "captured_at": "2026-07-08T12:05:00Z",
        "observed_at": "2026-07-08 19:05:00 GMT+7",
        "url_or_source_ref": "https://x.com/FirstSquawk/status/2",
        "headline_text": "INFLATION IN US FALLS TO 2.9% IN LINE WITH EXPECTATIONS.",
        "raw_excerpt": "INFLATION IN US FALLS TO 2.9% IN LINE WITH EXPECTATIONS.",
        "tags": ["inflation"],
        "capture_mode": "fixture_local"
    },
    # Energy
    {
        "headline_id": "hl_energy_1",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "source_account_or_list": "EIA",
        "captured_at": "2026-07-08T12:10:00Z",
        "observed_at": "2026-07-08 19:10:00 GMT+7",
        "url_or_source_ref": "https://x.com/EIA/status/3",
        "headline_text": "CRUDE INVENTORIES DECREASE BY 1.2M BARRELS.",
        "raw_excerpt": "CRUDE INVENTORIES DECREASE BY 1.2M BARRELS.",
        "tags": ["energy"],
        "capture_mode": "fixture_local"
    },
    # Geopolitics
    {
        "headline_id": "hl_geopol_1",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "source_account_or_list": "FirstSquawk",
        "captured_at": "2026-07-08T12:15:00Z",
        "observed_at": "2026-07-08 19:15:00 GMT+7",
        "url_or_source_ref": "https://x.com/FirstSquawk/status/4",
        "headline_text": "WAR IN UKRAINE ESCALATES WITH NEW MISSILE STRIKES.",
        "raw_excerpt": "WAR IN UKRAINE ESCALATES WITH NEW MISSILE STRIKES.",
        "tags": ["geopolitics"],
        "capture_mode": "fixture_local"
    },
    # Duplicate headline to test deduplication
    {
        "headline_id": "hl_macro_1",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "source_account_or_list": "FirstSquawk",
        "captured_at": "2026-07-08T12:00:00Z",
        "observed_at": "2026-07-08 19:00:00 GMT+7",
        "url_or_source_ref": "https://x.com/FirstSquawk/status/1",
        "headline_text": "BREAKING: FED TO CUT INTEREST RATES BY 25BPS IN JULY MEETING.",
        "raw_excerpt": "BREAKING: FED TO CUT INTEREST RATES BY 25BPS IN JULY MEETING.",
        "tags": ["central_bank", "rates"],
        "capture_mode": "fixture_local"
    }
]

@pytest.fixture
def temp_workspace():
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        headlines_file = tmp_path / "headlines_raw_v0.json"
        with open(headlines_file, "w", encoding="utf-8") as f:
            json.dump(MOCK_HEADLINES, f, indent=2)
        yield tmp_path, headlines_file

def test_classify_headline_to_family():
    h_macro = {"headline_text": "Fed keeps rate unchanged", "tags": ["central_bank"]}
    assert classify_headline_to_family(h_macro) == "macro_policy_rates_liquidity"
    
    h_energy = {"headline_text": "Crude oil output declines", "tags": []}
    assert classify_headline_to_family(h_energy) == "energy_commodities"

    h_other = {"headline_text": "unrelated statement here", "tags": []}
    assert classify_headline_to_family(h_other) == "other_market_structure"

def test_build_article_idea_packet(temp_workspace):
    tmp_path, headlines_file = temp_workspace
    
    res = build_article_idea_packet(
        headlines_file=headlines_file,
        output_dir=tmp_path,
        recently_published_families=["energy_commodities"]
    )
    
    # Verify file generation
    assert (tmp_path / "headline_clusters_v0.json").exists()
    assert (tmp_path / "article_idea_selection_v0.json").exists()
    assert (tmp_path / "topic_balance_state_v0.json").exists()
    assert (tmp_path / "next_article_idea_brief_v0.md").exists()
    assert (tmp_path / "run_evidence_v0.json").exists()
    
    evidence = res["evidence"]
    assert evidence["input_headline_count"] == 5
    # Deduped count in python is 4 (one duplicate hl_macro_1 removed)
    assert res["selection"]["selected_topic_family"] == "macro_policy_rates_liquidity"
    assert any("DFF" in item for item in res["selection"]["database_support_needed"])
    
    # Confirm no database queries or writes are simulated/done
    assert res["selection"]["no_database_query_confirmation"] is True
    assert res["selection"]["no_article_draft_confirmation"] is True
    assert res["selection"]["no_dispatch_confirmation"] is True
    
    # Check no raw secrets in the values of the output structures
    def assert_no_secrets(val):
        if isinstance(val, str):
            s = val.lower()
            for forbidden in ("secret", "token", "cookie", "password"):
                # Allow output paths/keys containing these terms
                if forbidden in s and not any(ext in s for ext in ("v0.json", "v0.md", "v0.jsonl")):
                    raise AssertionError(f"Forbidden term '{forbidden}' found in value: {val}")
        elif isinstance(val, dict):
            for v in val.values():
                assert_no_secrets(v)
        elif isinstance(val, list):
            for v in val:
                assert_no_secrets(v)

    assert_no_secrets(res)

def test_topic_balance_stale_rejection(temp_workspace):
    tmp_path, headlines_file = temp_workspace
    
    # If macro_policy_rates_liquidity is recently published, macro should be skipped/penalized
    # and geopolitics_sanctions should be selected (since macro is stale).
    res = build_article_idea_packet(
        headlines_file=headlines_file,
        output_dir=tmp_path,
        recently_published_families=["macro_policy_rates_liquidity", "energy_commodities"]
    )
    
    assert res["selection"]["selected_topic_family"] == "geopolitics_sanctions"
    assert res["balance"]["stale_topic_rejected"] is True

def test_topic_balance_fallback(temp_workspace):
    tmp_path, headlines_file = temp_workspace
    
    # If ALL families in input are recently published, it should fall back to the highest rated one
    res = build_article_idea_packet(
        headlines_file=headlines_file,
        output_dir=tmp_path,
        recently_published_families=["macro_policy_rates_liquidity", "energy_commodities", "geopolitics_sanctions", "other_market_structure"]
    )
    
    # Should fall back to macro_policy_rates_liquidity
    assert res["selection"]["selected_topic_family"] == "macro_policy_rates_liquidity"
    assert res["balance"]["fallback_topic_balance_used"] is True
