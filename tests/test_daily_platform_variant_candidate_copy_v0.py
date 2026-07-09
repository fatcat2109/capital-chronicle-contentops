# -*- coding: utf-8 -*-
"""Tests for daily platform variant candidate copy."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_platform_variant_candidate_copy_v0 import generate_platform_variant_copy

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock metadata file
    draft_metadata = {
        "task_label": "TASK_CONTENTOPS_DAILY_SEO_ARTICLE_DRAFTING_V0",
        "selected_idea_id": "idea_energy_commodities_20260709",
        "editorial_title": "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets",
        "topic_family": "energy_commodities",
        "draft_status": "candidate_only",
        "source_support_families": [
            "US Crude Oil Exports (EIA)",
            "WTI Crude Spot Price",
            "SPR Inventory Levels"
        ]
    }
    meta_file = tmp_path / "article_draft_metadata_v0.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(draft_metadata, f, indent=2)
    draft_file = tmp_path / "article_draft_v0.md"
    draft_file.write_text("# Candidate SEO Draft\n\nDraft body placeholder.\n", encoding="utf-8")

    # Setup mock media plan file
    media_plan = {
        "task_label": "TASK_CONTENTOPS_DAILY_MEDIA_PLAN_SPEC_V0",
        "editorial_title": "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets",
        "draft_status": "candidate_only",
        "media_generation_status": "planning_only"
    }
    media_file = tmp_path / "media_plan_spec_v0.json"
    with open(media_file, "w", encoding="utf-8") as f:
        json.dump(media_plan, f, indent=2)

    return meta_file, media_file, tmp_path / "output"

def test_generate_platform_variant_copy(temp_workspace):
    meta_file, media_file, output_dir = temp_workspace

    res = generate_platform_variant_copy(
        article_metadata_file=meta_file,
        media_plan_file=media_file,
        output_dir=output_dir
    )

    # Verify output files exist
    assert (output_dir / "platform_variant_candidate_copy_v0.json").exists()
    assert (output_dir / "platform_variant_candidate_copy_v0.md").exists()
    assert (output_dir / "platform_copy_safety_review_v0.json").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    copy_json = res["copy_json"]
    safety = res["safety"]
    evidence = res["evidence"]

    # Verify platform copy loading and status preservation
    assert copy_json["draft_status"] == "candidate_only"
    assert copy_json["platform_copy_status"] == "candidate_only"
    assert copy_json["source_article_draft"] == str(meta_file.parent / "article_draft_v0.md")
    assert evidence["source_article_draft"] == str(meta_file.parent / "article_draft_v0.md")
    assert "article_brief_v0.json" not in copy_json["source_article_draft"]

    # Verify Substack, Telegram, and Twitter variants created
    platforms = [v["platform"] for v in copy_json["variants"]]
    assert "substack" in platforms
    assert "telegram" in platforms
    assert "twitter" in platforms

    # Verify specific platform properties
    for variant in copy_json["variants"]:
        assert variant["copy_status"] == "candidate_only"
        assert variant["media_reference_policy"] == "planned_only_no_asset_generated"
        assert variant["dispatch_allowed_now"] is False
        assert "candidate" in variant["caveat_line"].lower()

        # Verify no financial advice or price targets
        for keyword in ("buy", "sell", "hold", "sizing", "price target"):
            assert keyword not in variant["body_copy"].lower()

    # Telegram has a meaningful text body (not only a link or CTA)
    tg = next(v for v in copy_json["variants"] if v["platform"] == "telegram")
    assert len(tg["body_copy"].split()) > 10
    assert "us crude oil exports" in tg["body_copy"].lower()

    # Safety reviews
    assert safety["candidate_only"] is True
    assert safety["platform_payload_created"] is False
    assert safety["dispatch_allowed_now"] is False
    assert safety["actual_media_generated"] is False
    assert safety["exact_numeric_claims_made"] is False
    assert safety["financial_advice_detected"] is False
    assert safety["trading_signal_detected"] is False
    assert safety["price_target_detected"] is False
    assert safety["telegram_has_meaningful_text_body"] is True
    assert safety["required_caveat_present"] is True

    # Evidence checks
    assert evidence["classification"] == "PASS_CONTENTOPS_DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0"
    assert evidence["platform_copy_status"] == "candidate_only"
    assert evidence["no_actual_media_generated_confirmation"] is True
    assert evidence["no_platform_api_confirmation"] is True
    assert evidence["no_dispatch_confirmation"] is True

    # Secrets verification
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
