"""V6 Platform Variant Approval Input Contract.

Defines required inputs for the platform variant approval packet contract.
"""
from __future__ import annotations

from typing import Any


def make_platform_variant_approval_input_contract() -> dict[str, Any]:
    """Generates the platform variant approval input contract."""
    inputs = [
        "rendered_platform_variants_ref",
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
            "blocks_approval_packet_creation": True
        })

    return {
        "contract_status": "FUTURE_PLATFORM_VARIANT_APPROVAL_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
