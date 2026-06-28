"""V6 Canonical Article Studio Renderer Input Contract.

Defines the required inputs for draft rendering.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_renderer_input_contract() -> dict[str, Any]:
    """Generates the renderer input contract."""
    inputs = [
        "approved_source_pack_ref",
        "operator_approval_ref",
        "source_approval_hash_ref",
        "redacted_claim_binding_ref",
        "placeholder_binding_ref",
        "editor_shell_ref",
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
            "blocks_renderer_execution": True
        })

    return {
        "contract_status": "FUTURE_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
