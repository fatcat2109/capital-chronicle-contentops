import json
import os
import pytest
from live_contentops import grounded_research
from live_contentops import seo_metadata

def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_grounded_research_generation():
    req = load_fixture("research_input.json")
    ctx = grounded_research.generate_research_context(req)
    
    assert ctx["search_performed"] is False
    assert ctx["advisory_only"] is True
    assert ctx["not_public_postable_reason"] is not None
    assert len(ctx["source_items"]) == 1
    assert len(ctx["warnings"]) == 0

def test_grounded_research_missing_source_for_current_events():
    req = {
        "is_current_events": True,
        "topic": "Breaking news",
        "source_items": []
    }
    ctx = grounded_research.generate_research_context(req)
    
    assert len(ctx["warnings"]) > 0
    assert len(ctx["blockers"]) > 0
    assert "Current event topic lacks grounded research context." in ctx["warnings"]

def test_grounded_research_cost_policy():
    req = load_fixture("research_input.json")
    ctx = grounded_research.generate_research_context(req)
    assert "Search once per content packet" in ctx["cost_budget_notes"]

def test_seo_metadata_blocked_terms():
    req = load_fixture("seo_input_blocked.json")
    pack = seo_metadata.generate_seo_metadata_pack(req)
    
    assert len(pack["blockers"]) == 2
    assert "buy signal guaranteed" in pack["blockers"][0] or "buy signal guaranteed" in pack["blockers"][1]
    assert pack["advisory_only"] is True
    assert pack["not_public_postable_reason"] is not None

def test_seo_metadata_clean():
    req = {
        "topic": "Python programming",
        "is_synthetic": True,
        "suggested_keywords": ["python", "coding"],
        "suggested_hashtags": ["#python"]
    }
    pack = seo_metadata.generate_seo_metadata_pack(req)
    assert len(pack["blockers"]) == 0
    assert pack["not_public_postable_reason"] is not None
