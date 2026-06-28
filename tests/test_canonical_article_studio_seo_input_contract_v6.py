"""Test V6 Canonical Article Studio SEO Input Contract."""
from __future__ import annotations

from live_contentops import canonical_article_studio_seo_input_contract_v6 as contract_builder


def test_make_canonical_article_studio_seo_input_contract():
    contract = contract_builder.make_canonical_article_studio_seo_input_contract()

    assert contract["contract_status"] == "FUTURE_SEO_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 6

    names = [item["input_name"] for item in contract["required_inputs"]]
    expected_names = [
        "refined_canonical_draft_ref",
        "editorial_refinement_output_ref",
        "keyword_brief_ref",
        "seo_style_guide_ref",
        "canonical_article_slug_policy_ref",
        "jim_review_ref"
    ]
    assert names == expected_names

    for item in contract["required_inputs"]:
        assert item["required"] is True
        assert item["current_status"] == "missing"
        assert item["value_ref"] is None
        assert item["raw_value_persisted"] is False
        assert item["blocks_seo_generation"] is True
