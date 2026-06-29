"""V6 Publication Audit Record Input Contract.

Defines required inputs for the publication audit record contract.
"""
from __future__ import annotations

from typing import Any


def make_publication_audit_record_input_contract() -> dict[str, Any]:
    """Generates the publication audit record input contract."""
    inputs = [
        "supervised_dispatch_result_ref",
        "dispatch_attempt_ref",
        "dispatch_response_ref",
        "outbox_entry_ref",
        "approved_exact_payload_review_ref",
        "payload_hash_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "audit_redaction_policy_ref",
        "jim_audit_review_ref"
    ]
    required_inputs_list = []
    for item in inputs:
        required_inputs_list.append({
            "input_name": item,
            "required": True,
            "current_status": "missing",
            "value_ref": None,
            "raw_value_persisted": False,
            "blocks_publication_audit_record_creation": True
        })

    return {
        "contract_status": "FUTURE_PUBLICATION_AUDIT_RECORD_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
