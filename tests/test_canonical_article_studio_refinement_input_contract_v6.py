"""Test V6 Canonical Article Studio Refinement Input Contract."""
from __future__ import annotations

from live_contentops import canonical_article_studio_refinement_input_contract_v6 as contract_builder


def test_make_canonical_article_studio_refinement_input_contract():
    contract = contract_builder.make_canonical_article_studio_refinement_input_contract()

    assert contract["contract_status"] == "FUTURE_REFINEMENT_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 6

    names = [item["input_name"] for item in contract["required_inputs"]]
    expected_names = [
        "rendered_canonical_draft_ref",
        "source_approved_renderer_output_ref",
        "citation_manifest_ref",
        "seo_brief_ref",
        "editorial_style_guide_ref",
        "jim_review_ref"
    ]
    assert names == expected_names

    for item in contract["required_inputs"]:
        assert item["required"] is True
        assert item["current_status"] == "missing"
        assert item["value_ref"] is None
        assert item["raw_value_persisted"] is False
        assert item["blocks_refinement_execution"] is True
