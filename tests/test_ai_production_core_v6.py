import json
from pathlib import Path
from live_contentops import ai_production_core_v6 as core_lane

def test_production_core_dry_run_materialization(tmp_path):
    rc = core_lane.main(["--output-dir", str(tmp_path)])
    assert rc == 0
    
    # Verify file structures exist
    packet = json.loads((tmp_path / "ai_production_core_packet.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "ai_production_core_validation_report.json").read_text(encoding="utf-8"))
    provider = json.loads((tmp_path / "provider_gate_packet.json").read_text(encoding="utf-8"))
    prompt = json.loads((tmp_path / "prompt_registry_packet.json").read_text(encoding="utf-8"))
    
    assert packet["ai_production_core_status"] == "READY_FOR_REVIEW_ONLY_DRY_RUN"
    assert packet["live_provider_call_performed"] is False
    assert packet["provider_credentials_hydrated"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["human_review_required"] is True
    assert packet["allowed_for_drafting"] is True
    assert packet["allowed_for_publication"] is False
    
    assert report["safety_checks_pass"] is True
    assert report["operator_intent_valid"] is True
    assert report["research_grounding_valid"] is True
    assert report["canonical_article_valid"] is True
    assert report["seo_refinement_valid"] is True
    
    assert provider["ai_provider_mode"] == "dry_run_stub"
    assert "idea_classifier" in prompt["prompt_families"]
    
    # Assert sample outputs are correctly blocked for publication and require verification
    sample_grounding = json.loads((tmp_path / "sample_research_grounding_packet.json").read_text(encoding="utf-8"))
    assert sample_grounding["allowed_for_publication"] is False
    assert sample_grounding["allowed_for_drafting"] is True
    assert sample_grounding["freshness_status"] == "unverified_dry_run"
    assert sample_grounding["source_quality_status"] == "unverified_stub_source"
    assert "publication_blocked_until_source_verification" in sample_grounding["blocked_reasons"]
    
    sample_article = json.loads((tmp_path / "sample_canonical_article_packet.json").read_text(encoding="utf-8"))
    assert sample_article["draft_status"] == "review_only_draft_requires_source_verification"
    assert "UNVERIFIED_SAMPLE_SOURCE_REF" in sample_article["citations"]
    
    sample_seo = json.loads((tmp_path / "sample_seo_editorial_packet.json").read_text(encoding="utf-8"))
    assert "source_verification_required" in sample_seo["blockers"]

