"""Unit tests for approval queue exact payload review input contract module."""
from __future__ import annotations

from live_contentops.approval_queue_exact_payload_review_input_contract_v6 import make_approval_queue_exact_payload_review_input_contract


def test_input_contract_structure():
    contract = make_approval_queue_exact_payload_review_input_contract()
    assert contract["contract_status"] == "FUTURE_APPROVAL_QUEUE_EXACT_PAYLOAD_REVIEW_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    
    expected_names = {
        "platform_variant_approval_packet_ref",
        "rendered_platform_payloads_ref",
        "exact_payload_preview_ref",
        "platform_payload_manifest_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "payload_hash_policy_ref",
        "approval_policy_ref",
        "jim_review_ref"
    }
    
    found_names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert found_names == expected_names
    
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_exact_payload_review"] is True
