"""V6 Supervised Dispatch Input Contract.

Defines required inputs for the supervised dispatch contract.
"""
from __future__ import annotations

from typing import Any


def make_supervised_dispatch_input_contract() -> dict[str, Any]:
    """Generates the supervised dispatch input contract."""
    inputs = [
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
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_supervised_dispatch": True
        })

    return {
        "contract_status": "FUTURE_SUPERVISED_DISPATCH_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
