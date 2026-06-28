"""V6 Canonical Article Studio SEO Input Contract.

Defines the required inputs for SEO metadata contract.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_seo_input_contract() -> dict[str, Any]:
    """Generates the SEO input contract."""
    inputs = [
        "refined_canonical_draft_ref",
        "editorial_refinement_output_ref",
        "keyword_brief_ref",
        "seo_style_guide_ref",
        "canonical_article_slug_policy_ref",
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
            "blocks_seo_generation": True
        })

    return {
        "contract_status": "FUTURE_SEO_INPUT_CONTRACT_ONLY",
        "runtime_truth": False,
        "required_inputs": required_inputs_list
    }
