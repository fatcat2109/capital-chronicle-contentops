"""Unit tests for community feedback capture input contract."""
from __future__ import annotations

from live_contentops import community_feedback_capture_input_contract_v6 as builder


def test_input_contract_structure():
    contract = builder.make_community_feedback_capture_input_contract()
    assert contract["contract_status"] == "FUTURE_COMMUNITY_FEEDBACK_CAPTURE_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 12

    expected_names = {
        "publication_audit_record_ref",
        "supervised_dispatch_result_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "feedback_capture_policy_ref",
        "feedback_source_binding_ref",
        "community_channel_binding_ref",
        "audit_redaction_policy_ref",
        "operator_feedback_capture_authorization_ref",
        "jim_feedback_review_ref"
    }
    names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert names == expected_names
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_community_feedback_capture"] is True
