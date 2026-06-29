"""V6 Outbox Entry Input Contract.

Defines required inputs for the outbox entry contract.
"""
from __future__ import annotations

from typing import Any


def make_outbox_entry_input_contract() -> dict[str, Any]:
    """Generates the outbox entry input contract."""
    inputs = [
        "approved_exact_payload_review_ref",
        "approval_queue_review_output_ref",
        "rendered_platform_payloads_ref",
        "exact_payload_preview_ref",
        "platform_payload_manifest_ref",
        "payload_hash_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "approval_id_ref",
        "approval_hash_ref",
        "dispatch_policy_ref",
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
            "blocks_outbox_entry_creation": True
        })

    return {
        "contract_status": "FUTURE_OUTBOX_ENTRY_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
