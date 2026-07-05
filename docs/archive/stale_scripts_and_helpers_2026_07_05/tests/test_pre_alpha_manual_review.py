"""Tests for the pre-alpha manual review workflow + approval packet (Task 0098)."""

import json
import os

from live_contentops import pre_alpha_manual_review as mr

FIX_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_manual_review"
)


def _fix(name):
    return os.path.abspath(os.path.join(FIX_DIR, name))


def test_schemas_load():
    assert mr.load_decision_schema()["title"] == "PreAlphaManualReviewDecision"
    assert mr.load_approval_packet_schema()["title"] == "PreAlphaApprovalPacket"


def test_valid_approve_manual_only():
    p = mr.build_from_input_file(_fix("valid_approve_manual_only.json"))
    assert p["approval_status"] == "approved_manual_publish_prep"
    assert p["manual_publish_prep_ready"] is True
    assert p["blocked_reasons"] == []
    assert p["approved_text"]  # text carried only on clean approval
    assert p["public_postable"] is False
    assert p["publish_allowed_now"] is False
    assert p["platform_publish_allowed_now"] is False
    assert p["live_execution_allowed_now"] is False
    assert p["final_operator_check_required"] is True
    assert p["limitations"]
    assert p["is_general_process_content"] is True
    assert any(s.startswith("status:approved") for s in p["approval_audit_trail"])


def test_valid_request_revision():
    p = mr.build_from_input_file(_fix("valid_request_revision.json"))
    assert p["approval_status"] == "revision_requested"
    assert p["manual_publish_prep_ready"] is False
    assert p["blocked_reasons"] == []
    assert p["approved_text"] == ""  # never carry text unless approved
    assert p["final_operator_check_required"] is True


def test_request_revision_requires_notes():
    bundle = json.load(open(_fix("valid_request_revision.json"), encoding="utf-8"))
    bundle["decision"]["required_revision_notes"] = []
    p = mr.build_approval_packet(
        bundle["rendered_packet_id"], bundle["review_item"], bundle["decision"]
    )
    assert p["approval_status"] == "rejected"
    assert "request_revision_requires_notes" in p["blocked_reasons"]


def test_valid_reject_guardrail():
    p = mr.build_from_input_file(_fix("valid_reject_guardrail.json"))
    assert p["approval_status"] == "rejected"
    assert p["manual_publish_prep_ready"] is False
    assert p["approved_text"] == ""


def test_reject_requires_reason():
    bundle = json.load(open(_fix("valid_reject_guardrail.json"), encoding="utf-8"))
    bundle["decision"]["decision_reason"] = "  "
    p = mr.build_approval_packet(
        bundle["rendered_packet_id"], bundle["review_item"], bundle["decision"]
    )
    assert "reject_requires_reason" in p["blocked_reasons"]


def test_invalid_auto_approval_blocks():
    p = mr.build_from_input_file(_fix("invalid_auto_approval.json"))
    assert p["approval_status"] == "rejected"
    assert p["manual_publish_prep_ready"] is False
    assert "auto_approval_not_allowed" in p["blocked_reasons"]


def test_invalid_publish_allowed_now_blocks():
    p = mr.build_from_input_file(_fix("invalid_publish_allowed_now.json"))
    assert p["approval_status"] == "rejected"
    assert "publish_allowed_now_must_be_false" in p["blocked_reasons"]
    assert p["publish_allowed_now"] is False  # output flag always pinned


def test_invalid_missing_reviewer_blocks():
    p = mr.build_from_input_file(_fix("invalid_missing_reviewer.json"))
    assert p["approval_status"] == "rejected"
    assert "missing_reviewer_placeholder" in p["blocked_reasons"]


def test_invalid_unresolved_guardrail_findings_blocks():
    p = mr.build_from_input_file(_fix("invalid_unresolved_guardrail_findings.json"))
    assert p["approval_status"] == "rejected"
    assert p["manual_publish_prep_ready"] is False
    assert "approve_with_unresolved_findings" in p["blocked_reasons"]
    assert any("forbidden_language" in r for r in p["blocked_reasons"])


def test_validate_decision_clean_approve():
    bundle = json.load(open(_fix("valid_approve_manual_only.json"), encoding="utf-8"))
    v = mr.validate_decision(bundle["decision"], bundle["review_item"])
    assert v["valid"] is True
    assert v["errors"] == []


def test_validate_decision_unknown_decision():
    v = mr.validate_decision({"decision": "publish_live"})
    assert v["valid"] is False
    assert "decision_value_not_allowed" in v["errors"]


def test_validate_decision_live_flag_blocks():
    bundle = json.load(open(_fix("valid_approve_manual_only.json"), encoding="utf-8"))
    bundle["decision"]["live_execution_allowed_now"] = True
    v = mr.validate_decision(bundle["decision"], bundle["review_item"])
    assert v["valid"] is False
    assert "live_execution_allowed_now_must_be_false" in v["errors"]


def test_summary_posture_is_safe():
    s = mr.summary()
    assert s["local_only"] is True
    assert s["manual_review_enabled"] is True
    assert s["approval_packet_enabled"] is True
    assert s["integrates_with_0097_review_queue"] is True
    assert s["auto_approval"] is False
    assert s["provider_call_made"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["fake_alpha_output"] is False
    assert s["public_postable_output"] is False
    assert s["publish_allowed_now"] is False
    assert s["platform_publish_allowed_now"] is False
    assert s["live_execution_allowed_now"] is False
    assert s["final_operator_check_required"] is True
    assert sorted(s["supported_decisions"]) == [
        "approve_manual_publish_prep",
        "reject",
        "request_revision",
    ]

