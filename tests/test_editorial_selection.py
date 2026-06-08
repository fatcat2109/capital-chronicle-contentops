import json
import os
import pytest
from live_contentops import editorial_preview
from live_contentops import editorial_selection

def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_selection_packet_generation():
    req = load_fixture("preview_input.json")
    variants = editorial_preview.generate_preview(req)
    packet = editorial_selection.generate_selection_packet(variants, req.get("source_fixture_id"))
    
    assert packet["variants_compared"] == 4
    assert packet["manual_selection_required"] is True
    assert packet["auto_selected"] is False
    assert packet["approval_granted"] is False
    assert packet["publish_ready"] is False
    assert packet["advisory_only"] is True
    assert packet["no_public_post_reason"] is not None
    assert "manual_selection_placeholder" in packet
    assert packet["manual_selection_placeholder"]["selection_status"] == "PENDING_MANUAL_SELECTION"

def test_selection_packet_preserves_limitations():
    req = load_fixture("preview_input.json")
    variants = editorial_preview.generate_preview(req)
    packet = editorial_selection.generate_selection_packet(variants, req.get("source_fixture_id"))
    
    for item in packet["comparison_items"]:
        # The preview test showed we preserve limitations now
        assert item["limitation_status"] == "PRESERVED"
        assert item["source_reference_status"] == "PRESERVED"
        assert item["not_public_postable_reason"] is not None
        assert item["operator_decision_placeholder"] == "PENDING_MANUAL_REVIEW"

def test_selection_packet_unsafe_claims():
    req = {
        "text": "You must buy this stock guaranteed 100% sure.",
        "platforms": ["linkedin"],
        "is_synthetic_demo": True
    }
    variants = editorial_preview.generate_preview(req)
    packet = editorial_selection.generate_selection_packet(variants, "unsafe_1")
    
    item = packet["comparison_items"][0]
    assert "contains_blocked_claims" in item["safety_notes"]
    assert item["not_public_postable_reason"] is not None
    assert packet["publish_ready"] is False
