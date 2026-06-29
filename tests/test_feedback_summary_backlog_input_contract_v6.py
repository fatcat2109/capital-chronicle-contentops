"""Unit tests for feedback summary backlog input contract."""
from __future__ import annotations

from live_contentops import feedback_summary_backlog_input_contract_v6 as builder


def test_input_contract_structure():
    contract = builder.make_feedback_summary_backlog_input_contract()
    assert contract["contract_status"] == "FUTURE_FEEDBACK_SUMMARY_BACKLOG_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 10

    expected_names = {
        "community_feedback_capture_ref",
        "redacted_feedback_records_ref",
        "feedback_capture_policy_ref",
        "feedback_summarization_policy_ref",
        "backlog_routing_policy_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "audit_redaction_policy_ref",
        "operator_summary_authorization_ref",
        "jim_feedback_review_ref"
    }
    names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert names == expected_names
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_feedback_summary_backlog_creation"] is True
