"""V6 Canonical Article Studio Refinement Input Contract.

Defines the required inputs for editorial refinement.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_refinement_input_contract() -> dict[str, Any]:
    """Generates the refinement input contract."""
    inputs = [
        "rendered_canonical_draft_ref",
        "source_approved_renderer_output_ref",
        "citation_manifest_ref",
        "seo_brief_ref",
        "editorial_style_guide_ref",
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
            "blocks_refinement_execution": True
        })

    return {
        "contract_status": "FUTURE_REFINEMENT_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
