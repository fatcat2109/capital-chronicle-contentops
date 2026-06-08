import json
import os
import pytest
from live_contentops import editorial_preview

def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_preview_generation():
    req = load_fixture("preview_input.json")
    variants = editorial_preview.generate_preview(req)
    
    # 2 platforms * 1 audience * 2 styles = 4 variants
    assert len(variants) == 4
    
    for v in variants:
        assert v["not_public_postable_reason"] is not None
        assert v["advisory_only"] is True
        assert "not_public_postable" in v["guardrail_status"].lower()
        
        # Original text has caveat
        assert v["limitations_preserved"] is True
        # Original text has source
        assert v["source_references_preserved"] is True

def test_missing_limitation_warning():
    req = {
        "text": "A great new insight with no limits.",
        "platforms": ["x"],
        "is_synthetic_demo": True
    }
    variants = editorial_preview.generate_preview(req)
    v = variants[0]
    assert v["limitations_preserved"] is False
    assert any("limitation" in w.lower() for w in v["warnings"])

def test_blocked_claims_preview():
    req = {
        "text": "You must buy this stock guaranteed 100% sure.",
        "platforms": ["linkedin"],
        "is_synthetic_demo": True
    }
    variants = editorial_preview.generate_preview(req)
    v = variants[0]
    assert len(v["blockers"]) > 0
    assert v["guardrail_status"] == "NOT_PUBLIC_POSTABLE"
    assert "forbidden claims" in v["not_public_postable_reason"].lower()

def test_no_approval_authority():
    req = load_fixture("preview_input.json")
    variants = editorial_preview.generate_preview(req)
    for v in variants:
        assert v["advisory_only"] is True
