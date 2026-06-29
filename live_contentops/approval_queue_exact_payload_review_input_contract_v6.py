"""V6 Approval Queue Exact Payload Review Input Contract.

Defines required inputs for the approval queue exact payload review contract.
"""
from __future__ import annotations

from typing import Any


def make_approval_queue_exact_payload_review_input_contract() -> dict[str, Any]:
    """Generates the approval queue exact payload review input contract."""
    inputs = [
        "platform_variant_approval_packet_ref",
        "rendered_platform_payloads_ref",
        "exact_payload_preview_ref",
        "platform_payload_manifest_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "payload_hash_policy_ref",
        "approval_policy_ref",
        "jim_review_ref"
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_exact_payload_review": True
        })

    return {
        "contract_status": "FUTURE_APPROVAL_QUEUE_EXACT_PAYLOAD_REVIEW_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
