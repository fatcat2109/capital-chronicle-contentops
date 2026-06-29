"""Unit tests for platform variant approval input contract module."""
from __future__ import annotations

from live_contentops.platform_variant_approval_input_contract_v6 import make_platform_variant_approval_input_contract


def test_input_contract_structure():
    contract = make_platform_variant_approval_input_contract()
    assert contract["contract_status"] == "FUTURE_PLATFORM_VARIANT_APPROVAL_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    
    expected_names = {
        "rendered_platform_variants_ref",
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
        assert inp["blocks_approval_packet_creation"] is True
