# -*- coding: utf-8 -*-
"""Tests for daily SEO article drafting."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_seo_article_drafting_v0 import generate_article_draft

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock article brief file
    article_brief = {
        "task_label": "TASK_CONTENTOPS_DAILY_ARTICLE_BRIEF_GENERATION_V0",
        "original_idea_blocked": True,
        "selected_idea_id": "idea_energy_commodities_20260709",
        "editorial_title": "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets",
        "working_slug": "us-oil-export-surge-spr-dynamics",
        "topic_family": "energy_commodities",
        "source_support_needed": [
            "US Crude Oil Exports (EIA)",
            "WTI Crude Spot Price",
            "SPR Inventory Levels"
        ]
    }

    brief_file = tmp_path / "article_brief_v0.json"
    with open(brief_file, "w", encoding="utf-8") as f:
        json.dump(article_brief, f, indent=2)

    return brief_file, tmp_path / "output"

def test_generate_article_draft(temp_workspace):
    brief_file, output_dir = temp_workspace

    res = generate_article_draft(
        article_brief_file=brief_file,
        output_dir=output_dir
    )

    # Verify output files exist
    assert (output_dir / "article_draft_v0.md").exists()
    assert (output_dir / "article_draft_metadata_v0.json").exists()
    assert (output_dir / "draft_safety_review_v0.json").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    body = res["body"]
    metadata = res["metadata"]
    safety = res["safety"]
    evidence = res["evidence"]

    # Verify caveat block in draft
    expected_caveat = "Candidate editorial draft. Numeric references require final source verification before publication."
    assert expected_caveat in body

    # Verify H1 title and H2 sections
    assert "# US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets" in body
    assert "## Introduction" in body
    assert "## Section 1" in body
    assert "## Section 2" in body
    assert "## Section 3" in body
    assert "## Conclusion" in body

    # Metadata checks
    assert metadata["draft_status"] == "candidate_only"
    assert metadata["selected_idea_id"] == "idea_energy_commodities_20260709"
    assert metadata["seo_meta_title"] == "US Oil Export Surge: SPR and Production Realignment"
    assert len(metadata["seo_meta_title"]) <= 60
    assert len(metadata["seo_meta_description"]) <= 160
    assert metadata["exact_numeric_claims_made"] is False
    assert metadata["financial_advice_detected"] is False

    # Safety checks
    assert safety["candidate_only"] is True
    assert safety["exact_numeric_claims_made"] is False
    assert safety["financial_advice_detected"] is False
    assert safety["trading_signal_detected"] is False
    assert safety["price_target_detected"] is False
    assert safety["media_generated"] is False
    assert safety["dispatch_ready"] is False
    assert safety["required_caveat_present"] is True

    # Evidence checks
    assert evidence["classification"] == "PASS_CANDIDATE_ONLY_CONTENTOPS_DAILY_SEO_ARTICLE_DRAFTING_V0"
    assert evidence["draft_status"] == "candidate_only"
    assert evidence["no_media_confirmation"] is True
    assert evidence["no_platform_variant_confirmation"] is True
    assert evidence["no_dispatch_confirmation"] is True

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

def test_generate_article_draft_refuses_if_original_not_blocked(temp_workspace):
    brief_file, output_dir = temp_workspace

    # Modify brief so original Japan JGB idea is NOT marked blocked
    with open(brief_file, "r", encoding="utf-8") as f:
        brief = json.load(f)
    brief["original_idea_blocked"] = False

    with open(brief_file, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)

    with pytest.raises(ValueError, match="Original Japan JGB idea is not blocked"):
        generate_article_draft(
            article_brief_file=brief_file,
            output_dir=output_dir
        )
