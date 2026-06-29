"""V6 Feedback Summary Backlog Input Contract.

Defines required inputs for the feedback summary backlog contract.
"""
from __future__ import annotations

from typing import Any


def make_feedback_summary_backlog_input_contract() -> dict[str, Any]:
    """Generates the feedback summary backlog input contract."""
    inputs = [
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
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_feedback_summary_backlog_creation": True
        })

    return {
        "contract_status": "FUTURE_FEEDBACK_SUMMARY_BACKLOG_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
