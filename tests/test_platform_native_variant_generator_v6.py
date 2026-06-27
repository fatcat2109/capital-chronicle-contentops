import json
from pathlib import Path
from live_contentops import platform_native_variant_generator_v6 as generator


def write_temp_inputs(tmp_path, article_status="OUTLINE_SCAFFOLD_READY", grounding_status="RESEARCH_BACKLOG_READY", refinement_status="SEO_EDITORIAL_REVIEW_READY_WITH_SOURCE_GAP", **kwargs):
    # Mimics canonical_substack_article_v6 output
    article_data = {
        "article_id": "substack_article_053c35205d67",
        "source_intent_id": "discord_operator_intent_d1720f70a937",
        "article_status": article_status,
        "source_mode": "operator_idea_only",
        "title": "Draft Outline: Editorial Workflow",
        "sections": ["General"],
        "source_refs": kwargs.get("source_refs", []),
        "source_needed": kwargs.get("source_needed", True),
        "source_evidence_required": kwargs.get("source_evidence_required", False),
        "blocked_reasons": kwargs.get("blocked_reasons", []),
    }
    
    # Mimics ai_research_grounding_lane_v6 output
    grounding_data = {
        "research_packet_id": "substack_research_6a7a2be45f6e",
        "grounding_status": grounding_status,
        "source_mode": "operator_idea_only",
        "missing_source_refs": kwargs.get("missing_source_refs", ["operator_idea_source_ref"]),
        "source_needed": kwargs.get("source_needed", True),
        "source_evidence_required": kwargs.get("source_evidence_required", False),
        "blocked_reasons": kwargs.get("blocked_reasons", []),
    }
    
    # Mimics seo_editorial_refinement_lane_v6 output
    seo_data = {
        "seo_editorial_packet_id": "seo_editorial_69ec0b8ce1a0",
        "refinement_status": refinement_status,
        "blocked_reasons": kwargs.get("blocked_reasons", []),
    }
    
    art_p = tmp_path / "canonical_article_packet.json"
    art_p.write_text(json.dumps(article_data, indent=2), encoding="utf-8")
    
    gnd_p = tmp_path / "research_grounding_packet.json"
    gnd_p.write_text(json.dumps(grounding_data, indent=2), encoding="utf-8")
    
    seo_p = tmp_path / "seo_editorial_packet.json"
    seo_p.write_text(json.dumps(seo_data, indent=2), encoding="utf-8")
    
    return art_p, gnd_p, seo_p


def test_source_gap_produces_ready_with_source_gap_status(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path, missing_source_refs=["operator_idea_source_ref"], source_needed=True)
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    assert packet["variant_status"] == "VARIANT_SCAFFOLD_READY_WITH_SOURCE_GAP"
    assert packet["public_postable"] is False
    assert packet["not_public_postable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_blocked_article_produces_blocked_by_source_article(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path, article_status="BLOCKED_BY_OPERATOR_INTENT", blocked_reasons=["trading_signal_language_blocked"])
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    assert packet["variant_status"] == "BLOCKED_BY_SOURCE_ARTICLE"
    assert "trading_signal_language_blocked" in packet["blocked_reasons"]


def test_blocked_grounding_produces_blocked_by_research_grounding(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path, grounding_status="BLOCKED_BY_SOURCE_ARTICLE", blocked_reasons=["trading_signal_language_blocked"])
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    assert packet["variant_status"] == "BLOCKED_BY_RESEARCH_GROUNDING"


def test_blocked_seo_produces_blocked_by_seo_editorial(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path, refinement_status="BLOCKED_BY_SOURCE_ARTICLE", blocked_reasons=["trading_signal_language_blocked"])
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    assert packet["variant_status"] == "BLOCKED_BY_SEO_EDITORIAL"


def test_source_refs_present_produces_ready_variants(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path, missing_source_refs=[], source_needed=False)
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    assert packet["variant_status"] == "VARIANT_SCAFFOLD_READY"
    assert packet["not_public_postable"] is True


def test_all_six_platform_variant_files_and_warnings(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path)
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    
    for plat in packet["target_platforms"]:
        text = generator.generate_scaffold_text(plat, packet)
        assert "NO-PUBLICATION WARNING" in text
        assert "dispatch_allowed_now` is false" in text
        assert "Source Mode" in text
        assert "operator_idea_only" in text
        # Asserts no fake metrics are invented
        assert "CPC" not in text
        assert "search_volume" not in text
        assert "traffic" not in text


def test_packet_contains_no_sensitive_values(tmp_path):
    art_p, gnd_p, seo_p = write_temp_inputs(tmp_path)
    packet = generator.materialize_variant_packet(art_p, gnd_p, seo_p)
    dump = json.dumps(packet)
    assert "discord.com/api/webhooks" not in dump
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(generator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
