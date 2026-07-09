# -*- coding: utf-8 -*-
"""Tests for daily article brief generation."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_article_brief_generation_v0 import generate_article_brief

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock reselection packet file
    reselection_packet = {
        "task_label": "TASK_CONTENTOPS_SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0",
        "original_selected_idea": {
            "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
            "selected_title": "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails",
            "selected_topic_family": "macro_policy_rates_liquidity"
        },
        "original_idea_blocked": True,
        "original_block_reason": "insufficient trusted database support",
        "do_not_draft_original_idea": True,
        "reselected_idea_id": "idea_energy_commodities_20260709",
        "reselected_title": "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets",
        "reselected_topic_family": "energy_commodities",
        "reselected_angle": "Analyzing the rapid growth of US crude oil exports...",
        "supporting_headline_ids": ["78d38021a9eae8bd51a35044"],
        "expected_support_families": [
            "US Crude Oil Exports (EIA)",
            "WTI Crude Spot Price",
            "SPR Inventory Levels"
        ]
    }

    packet_file = tmp_path / "reselection_packet_v0.json"
    with open(packet_file, "w", encoding="utf-8") as f:
        json.dump(reselection_packet, f, indent=2)

    return packet_file, tmp_path / "output"

def test_generate_article_brief(temp_workspace):
    packet_file, output_dir = temp_workspace

    res = generate_article_brief(
        reselection_packet_file=packet_file,
        output_dir=output_dir
    )

    # Verify output files exist
    assert (output_dir / "article_brief_v0.json").exists()
    assert (output_dir / "article_brief_v0.md").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    brief = res["brief_json"]
    evidence = res["evidence"]

    # Original Japan idea is blocked check
    assert brief["original_idea_blocked"] is True

    # Reselected parameters
    assert brief["selected_idea_id"] == "idea_energy_commodities_20260709"
    assert len(brief["editorial_title"]) <= 120
    assert brief["editorial_title"] == "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets"

    # Check outline sections and support families
    assert len(brief["outline_sections"]) > 0
    assert "US Crude Oil Exports (EIA)" in brief["source_support_needed"]

    # Confirm safety confirmations
    assert brief["no_full_article_confirmation"] is True
    assert brief["no_media_confirmation"] is True
    assert brief["no_platform_variant_confirmation"] is True
    assert brief["no_dispatch_confirmation"] is True

    # Run evidence checks
    assert evidence["classification"] == "PASS_CANDIDATE_ONLY_CONTENTOPS_DAILY_ARTICLE_BRIEF_GENERATION_V0"
    assert evidence["original_idea_blocked"] is True
    assert evidence["draft_readiness"] == "candidate_only"
    assert evidence["no_full_article_confirmation"] is True
    assert evidence["no_media_confirmation"] is True

    # Secret check
    def assert_no_secrets(val):
        if isinstance(val, str):
            s = val.lower()
            for forbidden in ("secret", "token", "cookie", "password", "session", "webhook"):
                if forbidden in s and not any(ext in s for ext in ("v0.json", "v0.md", "v0.jsonl", "py")):
                    raise AssertionError(f"Forbidden term '{forbidden}' found in value: {val}")
        elif isinstance(val, dict):
            for v in val.values():
                assert_no_secrets(v)
        elif isinstance(val, list):
            for v in val:
                assert_no_secrets(v)

    assert_no_secrets(res)

def test_generate_article_brief_refuses_if_original_not_blocked(temp_workspace):
    packet_file, output_dir = temp_workspace

    # Modify packet so original Japan JGB idea is NOT marked blocked
    with open(packet_file, "r", encoding="utf-8") as f:
        packet = json.load(f)
    packet["original_idea_blocked"] = False

    with open(packet_file, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2)

    with pytest.raises(ValueError, match="Original Japan JGB idea is not blocked"):
        generate_article_brief(
            reselection_packet_file=packet_file,
            output_dir=output_dir
        )
