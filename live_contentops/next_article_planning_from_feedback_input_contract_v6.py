"""V6 Next Article Planning From Feedback Input Contract.

Defines required inputs for the next article planning from feedback contract.
"""
from __future__ import annotations

from typing import Any


def make_next_article_planning_from_feedback_input_contract() -> dict[str, Any]:
    """Generates the next article planning from feedback input contract."""
    inputs = [
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
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_next_article_planning": True
        })

    return {
        "contract_status": "FUTURE_NEXT_ARTICLE_PLANNING_FROM_FEEDBACK_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
