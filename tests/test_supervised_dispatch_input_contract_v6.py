"""Unit tests for supervised dispatch input contract."""
from __future__ import annotations

from live_contentops import supervised_dispatch_input_contract_v6 as builder


def test_input_contract_structure():
    contract = builder.make_supervised_dispatch_input_contract()
    assert contract["contract_status"] == "FUTURE_SUPERVISED_DISPATCH_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 13

    expected_names = {
        "valid_outbox_entry_ref",
        "approved_exact_payload_review_ref",
        "rendered_platform_payload_ref",
        "exact_payload_preview_ref",
        "payload_hash_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "dispatch_policy_ref",
        "platform_endpoint_allowlist_ref",
        "credential_scope_proof_ref",
        "kill_switch_state_ref",
        "operator_dispatch_authorization_ref",
        "jim_review_ref"
    }
    names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert names == expected_names
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_supervised_dispatch"] is True
