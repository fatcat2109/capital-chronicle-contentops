import json
from pathlib import Path
from live_contentops import operator_approval_gate_lane_v6 as gate_lane


def write_temp_inputs(tmp_path, sub_status="AWAITING_OPERATOR_EVIDENCE", preflight_status="AWAITING_SOURCE_EVIDENCE", **kwargs):
    # Mimics operator_source_evidence_submission_packet.json output
    sub_data = {
        "operator_source_evidence_submission_packet_id": "submission_e8cb7ab9d7e1",
        "submission_status": sub_status,
        "evidence_complete": kwargs.get("evidence_complete", False),
        "blocked_reasons": kwargs.get("blocked_reasons", [])
    }

    # Mimics operator_source_evidence_validation_report.json output
    val_report_data = {
        "current_validation_status": "AWAITING_OPERATOR_EVIDENCE",
        "evidence_complete": kwargs.get("evidence_complete", False)
    }

    # Mimics dispatch_unlock_blockers_snapshot.json output
    snap_data = {
        "source_evidence_complete": kwargs.get("evidence_complete", False)
    }

    # Mimics approval_preflight_packet.json output
    preflight_data = {
        "approval_preflight_packet_id": "preflight_a01e278a",
        "review_status": preflight_status
    }

    # Mimics discord_drop_packet.json output
    drop_data = {
        "discord_drop_packet_id": "discord_drop_ce89baf48671"
    }

    # Mimics operator_review_packet.json output
    review_data = {
        "operator_review_packet_id": "review_packet_ce89baf4"
    }

    sub_p = tmp_path / "operator_source_evidence_submission_packet.json"
    sub_p.write_text(json.dumps(sub_data, indent=2), encoding="utf-8")

    val_p = tmp_path / "operator_source_evidence_validation_report.json"
    val_p.write_text(json.dumps(val_report_data, indent=2), encoding="utf-8")

    snp_p = tmp_path / "dispatch_unlock_blockers_snapshot.json"
    snp_p.write_text(json.dumps(snap_data, indent=2), encoding="utf-8")

    pre_p = tmp_path / "approval_preflight_packet.json"
    pre_p.write_text(json.dumps(preflight_data, indent=2), encoding="utf-8")

    drp_p = tmp_path / "discord_drop_packet.json"
    drp_p.write_text(json.dumps(drop_data, indent=2), encoding="utf-8")

    rev_p = tmp_path / "operator_review_packet.json"
    rev_p.write_text(json.dumps(review_data, indent=2), encoding="utf-8")

    return sub_p, val_p, snp_p, pre_p, drp_p, rev_p


def test_incomplete_current_packets_produce_blocked_status(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path, evidence_complete=False)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert gate["approval_gate_status"] == "APPROVAL_GATE_BLOCKED_PENDING_REQUIREMENTS"
    assert gate["approval_valid_for_dispatch"] is False
    assert "evidence_incomplete" in gate["blockers"]


def test_blocked_source_evidence_submission(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(
        tmp_path, sub_status="BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT", blocked_reasons=["intake_unreadable"]
    )
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert gate["approval_gate_status"] == "BLOCKED_BY_SOURCE_EVIDENCE_SUBMISSION"
    assert "intake_unreadable" in gate["blocked_reasons"]


def test_future_complete_fixture_produces_ready_for_decision(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path, sub_status="EVIDENCE_SUBMISSION_READY_FOR_HUMAN_REVIEW", evidence_complete=True)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p, override_complete=True
    )
    
    assert gate["approval_gate_status"] == "APPROVAL_GATE_READY_FOR_HUMAN_DECISION"
    assert gate["approval_valid_for_dispatch"] is False
    assert gate["dispatch_allowed_now"] is False
    assert gate["public_postable"] is False
    assert len(gate["blockers"]) == 0


def test_payload_hash_placeholder(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert payload_hash["final_payload_hash_present"] is False
    assert payload_hash["final_payload_hash_value"] is None
    assert payload_hash["hash_calculation_allowed_now"] is False


def test_destination_binding_placeholder(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert binding["destination_binding_present"] is False
    assert binding["real_channel_id_present"] is False
    assert binding["webhook_url_present"] is False
    assert binding["token_present"] is False
    assert binding["secret_keys_present"] is False
    assert binding["binding_allowed_now"] is False


def test_approval_decision_template(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert decision["operator_decision"] is None
    assert decision["approved_by"] is None
    assert decision["approval_valid_for_dispatch"] is False
    assert decision["exact_payload_hash_confirmed"] is False
    assert decision["source_evidence_confirmed"] is False


def test_dispatch_lock_report(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    assert lock_report["dispatch_lock_status"] == "LOCKED_APPROVAL_REQUIREMENTS_INCOMPLETE"
    assert lock_report["dispatch_allowed_now"] is False
    assert lock_report["outbox_entry_created"] is False
    assert lock_report["approval_ledger_entry_created"] is False
    assert lock_report["live_write_attempted"] is False


def test_generated_markdown_checklists(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    checklist = gate_lane.generate_gate_checklist_markdown(gate)
    assert "NO-PUBLICATION WARNING" in checklist
    assert "Approval Gate Checklist" in checklist
    assert "strictly blocked" in checklist.lower()
    
    readme = gate_lane.generate_readme_markdown(gate)
    assert "Operator Approval Gate Readme" in readme
    assert "does not make live writes" in readme.lower()
    assert "no secret-output note" in readme.lower()


def test_packet_contains_no_sensitive_values(tmp_path):
    sub_p, val_p, snp_p, pre_p, drp_p, rev_p = write_temp_inputs(tmp_path)
    gate, payload_hash, binding, decision, lock_report = gate_lane.materialize_gate_packets(
        sub_p, val_p, snp_p, pre_p, drp_p, rev_p
    )
    
    for obj in [gate, payload_hash, binding, decision, lock_report]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token_value" not in dump.lower()
        assert "cookie_value" not in dump.lower()
        assert "secret_key" not in dump.lower() or "secret_keys_present" in dump
        assert obj.get("raw_secret_output", False) is False
        assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(gate_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
