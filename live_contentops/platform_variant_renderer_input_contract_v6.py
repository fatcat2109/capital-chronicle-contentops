"""V6 Platform Variant Renderer Input Contract.

Defines required inputs for the platform variant renderer.
"""
from __future__ import annotations

from typing import Any


def make_platform_variant_renderer_input_contract() -> dict[str, Any]:
    """Generates the platform variant renderer input contract."""
    inputs = [
        "approved_canonical_article_ref",
        "refined_canonical_draft_ref",
        "seo_metadata_ref",
        "platform_variant_input_contract_ref",
        "platform_style_rules_ref",
        "platform_capability_matrix_ref",
        "destination_binding_ref",
        "exact_payload_approval_ref",
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
        "contract_status": "FUTURE_PLATFORM_VARIANT_RENDERER_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
