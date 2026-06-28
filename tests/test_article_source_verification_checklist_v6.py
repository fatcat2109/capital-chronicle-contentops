"""Test article source verification checklist module."""
from __future__ import annotations

from live_contentops import article_source_verification_checklist_v6 as checklist


def test_generate_source_verification_checklist():
    reqs = [
        {"research_requirement_id": "req_1", "required_source_type": "treasury_yield_series", "source_name_placeholder": "Yield", "source_verification_status": "missing"},
        {"research_requirement_id": "req_2", "required_source_type": "yield_curve_calculation", "source_name_placeholder": "Curve", "source_verification_status": "missing"}
    ]

    cl = checklist.generate_source_verification_checklist("article_packet_123", reqs)

    assert cl["source_packet_ref_id"] == "article_packet_123"
    assert cl["requirements_validated"] is False
    assert cl["human_review_required"] is True
    assert cl["audit_pass_ready"] is False
    assert len(cl["checklist_items"]) == 2

    for item in cl["checklist_items"]:
        assert item["verification_status"] == "missing"
        assert item["operator_verification_performed"] is False
        assert item["verification_audit_pass"] is False
