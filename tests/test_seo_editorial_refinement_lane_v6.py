import json
from pathlib import Path
from live_contentops import seo_editorial_refinement_lane_v6 as refinement


def write_temp_inputs(tmp_path, article_status="OUTLINE_SCAFFOLD_READY", grounding_status="RESEARCH_BACKLOG_READY", **kwargs):
    # Mimics canonical_substack_article_v6 output
    article_data = {
        "article_id": "substack_article_053c35205d67",
        "source_intent_id": "discord_operator_intent_d1720f70a937",
        "article_status": article_status,
        "source_mode": "operator_idea_only",
        "title": "Draft Outline: Editorial Workflow",
        "sections": [
            "Thesis Placeholder",
            "Why It Matters",
            "Architecture & Product Context",
            "Evidence Needed Before Publish",
            "Risk & Compliance Notes",
            "Next Operator Review Checklist"
        ],
        "source_refs": kwargs.get("source_refs", []),
        "source_needed": kwargs.get("source_needed", True),
        "source_evidence_required": kwargs.get("source_evidence_required", False),
        "blocked_reasons": kwargs.get("blocked_reasons", []),
        "dispatch_requested_from_intent": False,
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
    
    art_p = tmp_path / "canonical_article_packet.json"
    art_p.write_text(json.dumps(article_data, indent=2), encoding="utf-8")
    
    gnd_p = tmp_path / "research_grounding_packet.json"
    gnd_p.write_text(json.dumps(grounding_data, indent=2), encoding="utf-8")
    
    return art_p, gnd_p


def test_safe_backlog_with_missing_refs_produces_source_gap_status(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path, missing_source_refs=["operator_idea_source_ref"], source_needed=True)
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    assert packet["refinement_status"] == "SEO_EDITORIAL_REVIEW_READY_WITH_SOURCE_GAP"
    assert packet["public_postable"] is False
    assert packet["not_public_postable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_blocked_article_produces_blocked_by_source_article(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path, article_status="BLOCKED_BY_OPERATOR_INTENT", blocked_reasons=["trading_signal_language_blocked"])
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    assert packet["refinement_status"] == "BLOCKED_BY_SOURCE_ARTICLE"
    assert "trading_signal_language_blocked" in packet["blocked_reasons"]


def test_blocked_grounding_produces_blocked_by_research_grounding(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path, grounding_status="BLOCKED_BY_SOURCE_ARTICLE", blocked_reasons=["trading_signal_language_blocked"])
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    assert packet["refinement_status"] == "BLOCKED_BY_RESEARCH_GROUNDING"


def test_source_refs_present_produces_ready_review(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path, missing_source_refs=[], source_needed=False)
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    assert packet["refinement_status"] == "SEO_EDITORIAL_REVIEW_READY"
    assert packet["not_public_postable"] is True


def test_generated_metadata_does_not_invent_metrics(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path)
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    
    dump = json.dumps(packet)
    # Assert no fake metric keys/terms are listed in output
    assert "CPC" not in dump
    assert "search_volume" not in dump
    assert "traffic" not in dump
    
    # Keyword themes must be topic labels only
    for th in packet["keyword_theme_candidates"]:
        assert isinstance(th, str)
        assert len(th.split()) <= 4  # Short thematic strings


def test_generated_markdown_contains_warnings(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path)
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    
    checklist_md = refinement.generate_checklist_markdown(packet)
    assert "NO-PUBLICATION WARNING" in checklist_md
    assert "Source Mode" in checklist_md
    assert "Anti-Hype" in checklist_md
    
    metadata_md = refinement.generate_metadata_markdown(packet)
    assert "SEO DATA LIMITATION NOTE" in metadata_md
    # Confirms no structured metric block of CPC values is present
    assert "CPC value" not in metadata_md
    assert "CPC: " not in metadata_md


def test_packet_contains_no_sensitive_values(tmp_path):
    art_p, gnd_p = write_temp_inputs(tmp_path)
    packet = refinement.materialize_refinement_packet(art_p, gnd_p)
    dump = json.dumps(packet)
    assert "discord.com/api/webhooks" not in dump
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(refinement)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
