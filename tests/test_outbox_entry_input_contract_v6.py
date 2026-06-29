"""Unit tests for outbox entry input contract module."""
from __future__ import annotations

from live_contentops.outbox_entry_input_contract_v6 import make_outbox_entry_input_contract


def test_input_contract_structure():
    contract = make_outbox_entry_input_contract()
    assert contract["contract_status"] == "FUTURE_OUTBOX_ENTRY_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    
    expected_names = {
        "approved_exact_payload_review_ref",
        "approval_queue_review_output_ref",
        "rendered_platform_payloads_ref",
        "exact_payload_preview_ref",
        "platform_payload_manifest_ref",
        "payload_hash_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "approval_id_ref",
        "approval_hash_ref",
        "dispatch_policy_ref",
        "jim_review_ref"
    }
    
    found_names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert found_names == expected_names
    
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_outbox_entry_creation"] is True
