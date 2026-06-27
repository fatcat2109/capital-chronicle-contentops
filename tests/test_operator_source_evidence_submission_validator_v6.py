import json
from pathlib import Path
from live_contentops import operator_source_evidence_submission_validator_v6 as validator_lane


def write_temp_inputs(tmp_path, intake_status="AWAITING_OPERATOR_SOURCE_EVIDENCE", preflight_status="AWAITING_SOURCE_EVIDENCE", **kwargs):
    # Mimics source_reference_registry.json output
    registry_data = [
        {
            "source_ref_id": "operator_idea_source_ref",
            "required": True,
            "status": "MISSING_OPERATOR_SUPPLIED_EVIDENCE",
            "accepted_evidence_types": [
                "local_doc_path",
                "repo_file_path",
                "screenshot_path",
                "official_source_url_to_be_reviewed_later",
                "operator_note"
            ],
            "supplied_value": None,
            "verified": False,
            "verification_notes": None
        }
    ]

    # Mimics source_evidence_intake_packet.json output
    intake_data = {
        "source_evidence_intake_packet_id": "intake_a01e278a6d47",
        "intake_status": intake_status,
        "missing_source_refs": ["operator_idea_source_ref"],
        "blocked_reasons": kwargs.get("blocked_reasons", [])
    }

    # Mimics approval_preflight_packet.json output
    preflight_data = {
        "approval_preflight_packet_id": "preflight_a01e278a",
        "review_status": preflight_status
    }

    reg_p = tmp_path / "source_reference_registry.json"
    reg_p.write_text(json.dumps(registry_data, indent=2), encoding="utf-8")

    int_p = tmp_path / "source_evidence_intake_packet.json"
    int_p.write_text(json.dumps(intake_data, indent=2), encoding="utf-8")

    pre_p = tmp_path / "approval_preflight_packet.json"
    pre_p.write_text(json.dumps(preflight_data, indent=2), encoding="utf-8")

    return reg_p, int_p, pre_p


def test_missing_evidence_template_produces_awaiting_operator_evidence(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    assert sub["submission_status"] == "AWAITING_OPERATOR_EVIDENCE"
    assert sub["evidence_complete"] is False
    assert sub["dispatch_allowed_now"] is False
    assert report["current_validation_status"] == "AWAITING_OPERATOR_EVIDENCE"
    assert "operator_idea_source_ref" in report["unresolved_source_refs"]


def test_safe_future_fixture_produces_submission_ready_for_review(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    fixture = [
        {
            "source_ref_id": "operator_idea_source_ref",
            "supplied_value": "docs/evidence/jim_verified_audit_notes.pdf",
            "evidence_type": "local_doc_path",
            "operator_note": "verified local PDF manual ledger review done"
        }
    ]
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p, operator_input_fixture=fixture)
    
    assert sub["submission_status"] == "EVIDENCE_SUBMISSION_READY_FOR_HUMAN_REVIEW"
    assert sub["evidence_complete"] is True
    assert sub["dispatch_allowed_now"] is False
    assert sub["public_postable"] is False
    assert report["current_validation_status"] == "VALIDATION_SUCCESS_READY_FOR_PREFLIGHT_REVIEW"


def test_blocked_preflight_packet(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path, intake_status="BLOCKED_BY_UPSTREAM_PACKET", blocked_reasons=["grounding_blocked"])
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    assert sub["submission_status"] == "BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT"
    assert "grounding_blocked" in sub["blocked_reasons"]


def test_template_creates_slots_with_no_invented_values(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    assert len(temp) == 1
    assert temp[0]["source_ref_id"] == "operator_idea_source_ref"
    assert temp[0]["supplied_value"] is None
    assert temp[0]["verified"] is False


def test_webhook_unsafe_supplied_value_rejected(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    fixture = [
        {
            "source_ref_id": "operator_idea_source_ref",
            "supplied_value": "https://discord.com/api/webhooks/12345/tokenabc"
        }
    ]
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p, operator_input_fixture=fixture)
    
    assert sub["submission_status"] == "AWAITING_OPERATOR_EVIDENCE"
    assert sub["evidence_complete"] is False
    assert "operator_idea_source_ref" in sub["rejected_source_refs"]
    assert report["unsafe_values_detected"] is True
    assert temp[0]["supplied_value"] == "[REJECTED_UNSAFE_VALUE]"


def test_dotenv_path_rejected(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    fixture = [
        {
            "source_ref_id": "operator_idea_source_ref",
            "supplied_value": ".env"
        }
    ]
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p, operator_input_fixture=fixture)
    
    assert sub["submission_status"] == "AWAITING_OPERATOR_EVIDENCE"
    assert sub["evidence_complete"] is False
    assert "operator_idea_source_ref" in sub["rejected_source_refs"]
    assert report["unsafe_values_detected"] is True
    assert temp[0]["supplied_value"] == "[REJECTED_UNSAFE_VALUE]"


def test_dispatch_unlock_blockers_and_validation_report_blocked(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    assert report["dispatch_allowed_now"] is False
    assert report["public_postable"] is False
    assert report["evidence_complete"] is False
    
    assert snap["source_evidence_complete"] is False
    assert snap["dispatch_allowed_now"] is False


def test_generated_markdown_checklists(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    guide = validator_lane.generate_guide_markdown(sub)
    assert "NO-PUBLICATION WARNING" in guide
    assert "Accepted Evidence Shapes" in guide
    assert "Unsafe / Forbidden Input Examples" in guide
    assert "Do not invent sources" in guide
    
    checklist = validator_lane.generate_validation_checklist_markdown(sub, report)
    assert "Evidence Validation Checklist" in checklist
    assert "unresolved references" in checklist.lower()
    assert "dispatch remains strictly blocked" in checklist.lower()


def test_packet_contains_no_sensitive_values(tmp_path):
    reg_p, int_p, pre_p = write_temp_inputs(tmp_path)
    sub, temp, report, snap = validator_lane.materialize_submission_packets(reg_p, int_p, pre_p)
    
    for obj in [sub, report, snap]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token" not in dump.lower()
        assert "cookie" not in dump.lower()
        assert obj.get("raw_secret_output", False) is False
        assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(validator_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
