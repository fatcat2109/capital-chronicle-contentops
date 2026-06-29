"""Unit tests for next article planning input contract."""
from __future__ import annotations

from live_contentops import next_article_planning_from_feedback_input_contract_v6 as builder


def test_input_contract_structure():
    contract = builder.make_next_article_planning_from_feedback_input_contract()
    assert contract["contract_status"] == "FUTURE_NEXT_ARTICLE_PLANNING_FROM_FEEDBACK_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 12

    expected_names = {
        "feedback_summary_backlog_ref",
        "feedback_summary_ref",
        "backlog_items_ref",
        "next_article_signals_ref",
        "redacted_feedback_records_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "planning_policy_ref",
        "source_research_policy_ref",
        "audit_redaction_policy_ref",
        "operator_planning_authorization_ref",
        "jim_planning_review_ref"
    }
    names = {inp["input_name"] for inp in contract["required_inputs"]}
    assert names == expected_names
    for inp in contract["required_inputs"]:
        assert inp["required"] is True
        assert inp["current_status"] == "missing"
        assert inp["value_ref"] is None
        assert inp["raw_value_persisted"] is False
        assert inp["blocks_next_article_planning"] is True
