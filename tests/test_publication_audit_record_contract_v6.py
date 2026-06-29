"""Unit tests for publication audit record contract coordinator."""
from __future__ import annotations

from live_contentops import publication_audit_record_contract_v6 as coordinator


def test_coordinator_outputs():
    packet = coordinator.make_publication_audit_record_packet()
    contract = coordinator.make_publication_audit_record_input_contract()
    template = coordinator.make_publication_audit_record_blocked_template()
    output = coordinator.make_publication_audit_record_blocked_output()
    matrix = coordinator.make_publication_audit_record_gate_matrix()
    checklist = coordinator.make_publication_audit_record_checklist()

    assert packet["publication_audit_record_status"] == "PUBLICATION_AUDIT_RECORD_BLOCKED_WAITING_FOR_SUPERVISED_DISPATCH_RESULT"
    assert contract["contract_status"] == "FUTURE_PUBLICATION_AUDIT_RECORD_INPUT_CONTRACT_ONLY"
    assert template["audit_template_status"] == "BLOCKED_TEMPLATE_ONLY_NOT_PUBLICATION_AUDIT_RECORD"
    assert output["audit_output_status"] == "BLOCKED_NO_PUBLICATION_AUDIT_RECORD_CREATED"
    assert len(matrix) == 6
    assert checklist["checklist_status"] == "PUBLICATION_AUDIT_RECORD_BLOCKED_PENDING_DISPATCH_RESULT_AND_PUBLIC_URL_PROOF"
