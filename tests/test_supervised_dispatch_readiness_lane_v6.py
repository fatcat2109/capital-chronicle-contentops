import json
from pathlib import Path
from live_contentops import supervised_dispatch_readiness_lane_v6 as readiness_lane


def write_temp_inputs(tmp_path, gate_status="APPROVAL_GATE_BLOCKED_PENDING_REQUIREMENTS", **kwargs):
    # Mimics operator_approval_gate_packet.json output
    gate_data = {
        "operator_approval_gate_packet_id": "gate_972fb41b37c5",
        "approval_gate_status": gate_status,
        "evidence_complete": kwargs.get("evidence_complete", False),
        "payload_hash_complete": kwargs.get("payload_hash_complete", False),
        "destination_binding_complete": kwargs.get("destination_binding_complete", False),
        "safety_review_complete": kwargs.get("safety_review_complete", False),
        "operator_approval_complete": kwargs.get("operator_approval_complete", False),
        "blockers": kwargs.get("blockers", ["evidence_incomplete"]),
        "blocked_reasons": kwargs.get("blocked_reasons", [])
    }

    # Mimics dispatch_lock_report.json output
    lock_report_data = {
        "dispatch_lock_status": "LOCKED_APPROVAL_REQUIREMENTS_INCOMPLETE"
    }

    # Mimics payload_hash_placeholder.json output
    payload_hash_data = {
        "final_payload_hash_present": False
    }

    # Mimics destination_binding_placeholder.json output
    binding_data = {
        "destination_binding_present": False
    }

    # Mimics approval_decision_record_template.json output
    decision_data = {
        "operator_decision": None
    }

    # Mimics discord_drop_packet.json output
    drop_data = {
        "discord_drop_packet_id": "discord_drop_ce89baf48671"
    }

    gate_p = tmp_path / "operator_approval_gate_packet.json"
    gate_p.write_text(json.dumps(gate_data, indent=2), encoding="utf-8")

    lock_p = tmp_path / "dispatch_lock_report.json"
    lock_p.write_text(json.dumps(lock_report_data, indent=2), encoding="utf-8")

    hash_p = tmp_path / "payload_hash_placeholder.json"
    hash_p.write_text(json.dumps(payload_hash_data, indent=2), encoding="utf-8")

    bind_p = tmp_path / "destination_binding_placeholder.json"
    bind_p.write_text(json.dumps(binding_data, indent=2), encoding="utf-8")

    dec_p = tmp_path / "approval_decision_record_template.json"
    dec_p.write_text(json.dumps(decision_data, indent=2), encoding="utf-8")

    drop_p = tmp_path / "discord_drop_packet.json"
    drop_p.write_text(json.dumps(drop_data, indent=2), encoding="utf-8")

    return gate_p, lock_p, hash_p, bind_p, dec_p, drop_p


def test_current_blocked_approval_gate_produces_readiness_blocked(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(
        tmp_path, gate_status="BLOCKED_BY_SOURCE_EVIDENCE_SUBMISSION", blocked_reasons=["submission_blocked"]
    )
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert sub["readiness_status"] == "BLOCKED_BY_OPERATOR_APPROVAL_GATE"
    assert sub["dispatch_allowed_now"] is False
    assert "submission_blocked" in sub["blocked_reasons"]


def test_incomplete_requirements_produce_readiness_blocked_pending(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(
        tmp_path, gate_status="APPROVAL_GATE_BLOCKED_PENDING_REQUIREMENTS", blockers=["evidence_incomplete"]
    )
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert sub["readiness_status"] == "DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS"
    assert "evidence_incomplete" in sub["blockers"]
    assert sub["dispatch_allowed_now"] is False


def test_future_ready_for_human_decision_fixture_produces_review_only(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(
        tmp_path, gate_status="APPROVAL_GATE_READY_FOR_HUMAN_DECISION", blockers=[]
    )
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert sub["readiness_status"] == "SUPERVISED_DISPATCH_READY_FOR_OPERATOR_REVIEW_ONLY"
    assert sub["dispatch_allowed_now"] is False
    assert sub["approval_valid_for_dispatch"] is False


def test_blocker_matrix_includes_all_required_gates(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    gates = [row["gate_name"] for row in matrix]
    expected = [
        "source_evidence", "payload_hash", "destination_binding",
        "safety_review", "operator_approval", "kill_switch",
        "live_write_authorization", "outbox_creation"
    ]
    for g in expected:
        assert g in gates


def test_dry_run_dispatch_plan_placeholder(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert dry_plan["dry_run_only"] is True
    assert dry_plan["final_payload_present"] is False
    assert dry_plan["real_destination_present"] is False
    assert dry_plan["outbox_entry_created"] is False
    assert dry_plan["execution_allowed_now"] is False


def test_idempotency_key_placeholder(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert idempotency["idempotency_key_present"] is False
    assert idempotency["idempotency_key_value"] is None
    assert idempotency["generation_allowed_now"] is False


def test_kill_switch_snapshot(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    assert kill["kill_switch_active"] is True
    assert kill["dispatch_globally_disabled"] is True


def test_readiness_markdown_contents(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    report = readiness_lane.generate_readiness_report_markdown(sub, "LOCKED", sub["blockers"])
    assert "NO-PUBLICATION WARNING" in report
    assert "Dry-Run-Only Warning" in report
    assert "Kill-Switch Status" in report
    assert "No Outbox / Ledger Created" in report
    
    checklist = readiness_lane.generate_pre_dispatch_checklist_markdown(sub, matrix)
    assert "Source Evidence Checklist" in checklist
    assert "Payload Hash Checklist" in checklist
    assert "Safety Review Checklist" in checklist
    assert "Dispatch Blocked Note" in checklist


def test_packet_contains_no_sensitive_values(tmp_path):
    gate_p, lock_p, hash_p, bind_p, dec_p, drop_p = write_temp_inputs(tmp_path)
    sub, matrix, dry_plan, idempotency, kill = readiness_lane.materialize_readiness_packets(
        gate_p, lock_p, hash_p, bind_p, dec_p, drop_p
    )
    
    for obj in [sub, matrix, dry_plan, idempotency, kill]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token_value" not in dump.lower()
        assert "cookie_value" not in dump.lower()
        assert "secret_key" not in dump.lower() or "secret_keys_present" in dump
        if isinstance(obj, dict):
            assert obj.get("raw_secret_output", False) is False
            assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(readiness_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
