import json
from pathlib import Path
from live_contentops import ai_research_grounding_lane_v6 as grounding


def write_temp_article(tmp_path, status="OUTLINE_SCAFFOLD_READY", **kwargs):
    # Mimics canonical_substack_article_v6 output
    data = {
        "article_id": "substack_article_053c35205d67",
        "source_intent_id": "discord_operator_intent_d1720f70a937",
        "article_status": status,
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
        "source_refs": [],
        "source_needed": True,
        "source_evidence_required": False,
        "blocked_reasons": [],
        "dispatch_requested_from_intent": False,
    }
    data.update(kwargs)
    p = tmp_path / "canonical_article_packet.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def test_safe_outline_article_produces_ready_grounding(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY")
    packet = grounding.materialize_grounding_packet(p)
    assert packet["grounding_status"] == "RESEARCH_BACKLOG_READY"
    assert packet["public_postable"] is False
    assert packet["not_public_postable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_blocked_canonical_article_produces_blocked_grounding(tmp_path):
    p = write_temp_article(tmp_path, "BLOCKED_BY_OPERATOR_INTENT", blocked_reasons=["trading_signal_language_blocked"])
    packet = grounding.materialize_grounding_packet(p)
    assert packet["grounding_status"] == "BLOCKED_BY_SOURCE_ARTICLE"
    assert "trading_signal_language_blocked" in packet["blocked_reasons"]


def test_operator_idea_only_with_no_source_refs_sets_missing_refs(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY", source_mode="operator_idea_only", source_refs=[])
    packet = grounding.materialize_grounding_packet(p)
    assert packet["source_needed"] is True
    assert "operator_idea_source_ref" in packet["missing_source_refs"]


def test_source_refs_present_are_carried_forward(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY", source_refs=["docs/ref.md"])
    packet = grounding.materialize_grounding_packet(p)
    assert "docs/ref.md" in packet["required_source_refs"]
    assert "operator_idea_source_ref" not in packet["missing_source_refs"]


def test_no_fake_citations_created(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY")
    packet = grounding.materialize_grounding_packet(p)
    # Check that it doesn't invent fake sources/citations
    assert packet["claims_to_verify"] == []
    # Verify mapping of questions has no fake citations
    for q in packet["research_questions"]:
        assert "http" not in q["question"]


def test_approval_dispatch_intent_remains_false(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY")
    packet = grounding.materialize_grounding_packet(p)
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_generated_markdown_contains_warnings(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY")
    packet = grounding.materialize_grounding_packet(p)
    
    backlog_md = grounding.generate_backlog_markdown(packet, "Workflow")
    assert "DRAFT RESEARCH BACKLOG" in backlog_md
    assert "Source Mode" in backlog_md
    
    evidence_md = grounding.generate_evidence_markdown(packet)
    assert "NO-PUBLICATION WARNING" in evidence_md
    assert "safety exclusions" in evidence_md.lower()


def test_packet_contains_no_sensitive_values(tmp_path):
    p = write_temp_article(tmp_path, "OUTLINE_SCAFFOLD_READY")
    packet = grounding.materialize_grounding_packet(p)
    dump = json.dumps(packet)
    assert "discord.com/api/webhooks" not in dump
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(grounding)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
