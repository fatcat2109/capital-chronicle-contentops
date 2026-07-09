# -*- coding: utf-8 -*-
"""Tests for daily media plan specification."""

import json
import pytest
from pathlib import Path
from live_contentops.daily_media_plan_spec_v0 import generate_media_plan_spec

@pytest.fixture
def temp_workspace(tmp_path):
    # Setup mock draft file
    draft_body = "# US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets"
    draft_file = tmp_path / "article_draft_v0.md"
    with open(draft_file, "w", encoding="utf-8") as f:
        f.write(draft_body)

    # Setup mock draft metadata file
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

    return draft_file, meta_file, tmp_path / "output"

def test_generate_media_plan_spec(temp_workspace):
    draft_file, meta_file, output_dir = temp_workspace

    res = generate_media_plan_spec(
        article_draft_file=draft_file,
        article_metadata_file=meta_file,
        output_dir=output_dir
    )

    # Verify output files exist
    assert (output_dir / "media_plan_spec_v0.json").exists()
    assert (output_dir / "media_plan_spec_v0.md").exists()
    assert (output_dir / "media_safety_review_v0.json").exists()
    assert (output_dir / "run_evidence_v0.json").exists()
    assert (output_dir / "README.md").exists()

    spec = res["spec_json"]
    safety = res["safety"]
    evidence = res["evidence"]

    # Verify metadata loading and status preservation
    assert spec["editorial_title"] == "US Oil Export Surge: Production and SPR Dynamics Reshape Global Markets"
    assert spec["draft_status"] == "candidate_only"
    assert spec["media_generation_status"] == "planning_only"

    # Verify at least 2 media asset specs created
    assert len(spec["assets"]) >= 2
    for asset in spec["assets"]:
        assert asset["should_generate_now"] is False
        assert "caveat_text_required" in asset

    # Safety parameters
    assert spec["generation_allowed_now"] is False
    assert spec["chart_render_allowed_now"] is False
    assert spec["platform_payload_created"] is False
    assert spec["dispatch_ready"] is False

    # Safety review JSON assertions
    assert safety["candidate_only"] is True
    assert safety["actual_media_generated"] is False
    assert safety["chart_rendered"] is False
    assert safety["exact_numeric_claims_made"] is False
    assert safety["unverified_numeric_references_flagged"] is True
    assert safety["platform_payload_created"] is False
    assert safety["dispatch_ready"] is False
    assert safety["required_caveat_present"] is True

    # Evidence checks
    assert evidence["classification"] == "PASS_CONTENTOPS_DAILY_MEDIA_PLAN_SPEC_V0"
    assert evidence["draft_status"] == "candidate_only"
    assert evidence["no_actual_media_generated_confirmation"] is True
    assert evidence["no_chart_render_confirmation"] is True
    assert evidence["no_platform_variant_confirmation"] is True

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
