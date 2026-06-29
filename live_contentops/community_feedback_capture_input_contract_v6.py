"""V6 Community Feedback Capture Input Contract.

Defines required inputs for the community feedback capture contract.
"""
from __future__ import annotations

from typing import Any


def make_community_feedback_capture_input_contract() -> dict[str, Any]:
    """Generates the community feedback capture input contract."""
    inputs = [
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
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_community_feedback_capture": True
        })

    return {
        "contract_status": "FUTURE_COMMUNITY_FEEDBACK_CAPTURE_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
