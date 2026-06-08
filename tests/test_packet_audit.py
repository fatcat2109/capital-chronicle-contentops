import json
import os

import pytest

from live_contentops import editorial_packet_export as export
from live_contentops import packet_audit


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def clean_packet():
    req = load_fixture("export_packet_input.json")
    return export.build_export_packet(req)


def test_audit_clean_packet_passes(clean_packet):
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] in ("PASS", "WARNING")
    assert result["blocker_count"] == 0
    assert result["missing_components"] == []
    assert result["authority_violations"] == []
    assert result["citation_guardrail_status"] == "PASS"
    assert result["no_public_post_status"] == "NOT_PUBLIC_POSTABLE"
    assert result["safety_status"] == "SAFE"
    assert result["cost_policy_status"] == "ENFORCED"


def test_audit_missing_component_blocks(clean_packet):
    del clean_packet["seo_metadata_pack"]
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert "seo_metadata_pack" in result["missing_components"]
    assert any("missing required component" in b for b in result["blockers"])


def test_audit_authority_grant_blocks(clean_packet):
    clean_packet["approval_granted"] = True
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert any("approval_granted" in v for v in result["authority_violations"])


def test_audit_provider_search_platform_blocks(clean_packet):
    clean_packet["provider_call_allowed"] = True
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert any("provider_call_allowed" in v for v in result["authority_violations"])


def test_audit_human_review_disabled_blocks(clean_packet):
    clean_packet["human_review_required"] = False
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert any("human_review_required" in v for v in result["authority_violations"])


def test_audit_auto_selected_blocks(clean_packet):
    clean_packet["selection_packet"]["auto_selected"] = True
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert any("auto_selected" in v for v in result["authority_violations"])


def test_audit_missing_no_public_post_blocks(clean_packet):
    clean_packet["no_public_post_status"] = {"not_public_postable": False}
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert result["no_public_post_status"] == "MISSING"
    assert any("no_public_post_status missing" in b for b in result["blockers"])


def test_audit_prompt_invent_blocks(clean_packet):
    clean_packet["prompt_packet"]["prompt_sections"] = {
        "system_boundary_section": "Please invent prices for the reader."
    }
    result = packet_audit.audit_packet(clean_packet)
    assert result["audit_status"] == "BLOCKED"
    assert any("invent prices" in b for b in result["blockers"])


def test_audit_blocked_citation_guardrail_surfaces():
    req = {
        "source_fixture_id": "blocked_audit_demo",
        "prompt": {
            "is_synthetic": True,
            "citation_requirements": "Required for all claims",
            "source_context": {"is_current_events": True, "source_items": []},
        },
    }
    packet = export.build_export_packet(req)
    result = packet_audit.audit_packet(packet)
    assert result["citation_guardrail_status"] == "BLOCKED"
    assert result["audit_status"] == "BLOCKED"
    assert any("CITATION_GUARDRAIL_BLOCKED" in b for b in result["blockers"])


def test_audit_is_deterministic(clean_packet):
    r1 = packet_audit.audit_packet(clean_packet)
    r2 = packet_audit.audit_packet(clean_packet)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
