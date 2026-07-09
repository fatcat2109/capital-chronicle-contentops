# -*- coding: utf-8 -*-
"""Tests for daily support-aware article idea reselection."""

import json
import pytest
from pathlib import Path
from live_contentops.support_aware_article_idea_reselection_v0 import reselect_article_idea

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock idea selection file
    idea_selection = {
        "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
        "selected_title": "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails",
        "selected_topic_family": "macro_policy_rates_liquidity"
    }
    idea_file = tmp_path / "article_idea_selection_v0.json"
    with open(idea_file, "w", encoding="utf-8") as f:
        json.dump(idea_selection, f, indent=2)

    # Setup mock support gap repair plan file
    gap_plan = {
        "task_label": "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0",
        "selected_idea_id": "idea_macro_policy_rates_liquidity_20260709",
        "selected_title": "Japan's Debt Crisis: Yield and Currency Gap Widens as Intervention Fails",
        "selected_topic_family": "macro_policy_rates_liquidity",
        "article_draft_blocked": True
    }
    gap_file = tmp_path / "support_gap_repair_plan_v0.json"
    with open(gap_file, "w", encoding="utf-8") as f:
        json.dump(gap_plan, f, indent=2)

    # Setup mock headline clusters file
    headline_clusters = [
        {
            "cluster_id": "cluster_macro_policy_rates_liquidity",
            "topic_family": "macro_policy_rates_liquidity",
            "cluster_title": "Best metric for the debt crisis unfolding in Japan...",
            "top_headline_ids": ["d2d9118cb462be2341370321"]
        },
        {
            "cluster_id": "cluster_energy_commodities",
            "topic_family": "energy_commodities",
            "cluster_title": "The US went from exporting less than 1 mb/d to 5 mb/d now... https://t.co/W92zoMK5Rb",
            "top_headline_ids": ["78d38021a9eae8bd51a35044", "758e08735141150ee4a2a174"]
        }
    ]
    clusters_file = tmp_path / "headline_clusters_v0.json"
    with open(clusters_file, "w", encoding="utf-8") as f:
        json.dump(headline_clusters, f, indent=2)

    return idea_file, gap_file, clusters_file, tmp_path / "output"

def test_reselect_article_idea(temp_workspace):
    idea_file, gap_file, clusters_file, output_dir = temp_workspace

    res = reselect_article_idea(
        idea_selection_file=idea_file,
        gap_repair_plan_file=gap_file,
        headline_clusters_file=clusters_file,
        output_dir=output_dir
    )

    # Verify output files exist
    assert (output_dir / "reselection_packet_v0.json").exists()
    assert (output_dir / "reselected_article_idea_brief_v0.md").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    packet = res["packet"]
    evidence = res["evidence"]

    # Invariant checks
    assert packet["original_idea_blocked"] is True
    assert packet["original_block_reason"] == "insufficient trusted database support"
    assert packet["do_not_draft_original_idea"] is True

    # Reselected parameters
    assert packet["reselected_topic_family"] == "energy_commodities"
    assert packet["reselected_title"] == "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets"
    assert packet["ready_for_article_brief"] is True

    # Confirm safety confirmations are all True
    assert packet["no_database_repair_confirmation"] is True
    assert packet["no_article_draft_confirmation"] is True
    assert packet["no_media_confirmation"] is True
    assert packet["no_platform_write_confirmation"] is True
    assert packet["no_dispatch_confirmation"] is True

    # Run evidence assertions
    assert evidence["classification"] == "PASS_CONTENTOPS_SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0"
    assert evidence["original_idea_blocked"] is True
    assert evidence["ready_for_article_brief"] is True
    assert evidence["no_database_repair_confirmation"] is True
    assert evidence["no_article_draft_confirmation"] is True
    assert evidence["no_media_confirmation"] is True

    # Ensure no status/pointer files are modified
    for path_val in evidence["output_paths"].values():
        assert "status" not in path_val.replace("\\", "/").split("/")
        assert "next_task_pointer" not in path_val

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
