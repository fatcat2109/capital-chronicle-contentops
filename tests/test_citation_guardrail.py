import pytest
from live_contentops.citation_guardrail import evaluate_citation_guardrail

def test_citation_required_no_source():
    packet = {
        "citation_requirements": "Required for all claims",
        "source_context": {"source_items": []}
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Claim requires citation but has no source item." in res["blockers"]

def test_current_events_no_source():
    packet = {
        "source_context": {"is_current_events": True, "source_items": []}
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Current-event claim has no grounded context." in res["blockers"]

def test_synthetic_source_public_authority():
    packet = {
        "source_context": {"source_items": [{"synthetic_fixture": True}]},
        "no_public_post_reason": None
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Synthetic fixture source is treated as public authority." in res["blockers"]

def test_missing_freshness():
    packet = {
        "source_context": {"is_current_events": True, "source_items": [{"synthetic_fixture": True}]},
        "freshness_requirements": None,
        "no_public_post_reason": "Synthetic"
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Freshness window is missing for current-news content." in res["blockers"]

def test_blocked_claims_in_instructions():
    packet = {
        "blocked_claims": ["invent facts"],
        "prompt_sections": {"system_boundary_section": "I want to tell the model to invent facts."}
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Blocked claim 'invent facts' appears in prompt instructions." in res["blockers"]

def test_invent_in_instructions():
    packet = {
        "prompt_sections": {"system_boundary_section": "Please invent prices for me."}
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Prompt packet asks the LLM to invent prices." in res["blockers"]

def test_improper_authority_granted():
    packet = {
        "approval_granted": True
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "BLOCKED"
    assert "Prompt packet improperly grants approval/publish authority." in res["blockers"]

def test_clean_packet():
    packet = {
        "citation_requirements": "Required for all claims",
        "freshness_requirements": "24h",
        "no_public_post_reason": "Synthetic",
        "source_context": {
            "is_current_events": True,
            "source_items": [{"synthetic_fixture": True}]
        },
        "blocked_claims": ["invent facts"],
        "prompt_sections": {"system_boundary_section": "Standard section"}
    }
    res = evaluate_citation_guardrail(packet)
    assert res["status"] == "PASS"
    assert not res["blockers"]
