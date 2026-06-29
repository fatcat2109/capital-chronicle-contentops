"""Unit tests for publication audit record input contract."""
from __future__ import annotations

from live_contentops import publication_audit_record_input_contract_v6 as builder


def test_input_contract_structure():
    contract = builder.make_publication_audit_record_input_contract()
    assert contract["contract_status"] == "FUTURE_PUBLICATION_AUDIT_RECORD_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 12

    expected_names = {
        "supervised_dispatch_result_ref",
        "dispatch_attempt_ref",
        "dispatch_response_ref",
        "outbox_entry_ref",
        "approved_exact_payload_review_ref",
        "payload_hash_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "audit_redaction_policy_ref",
        "jim_audit_review_ref"
    }
    names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert names == expected_names
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_publication_audit_record_creation"] is True
