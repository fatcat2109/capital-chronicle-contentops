"""Test V6 Platform Variant Input Contract."""
from __future__ import annotations

from live_contentops import platform_variant_input_contract_v6 as contract_builder


def test_make_platform_variant_input_contract():
    contract = contract_builder.make_platform_variant_input_contract()

    assert contract["contract_status"] == "FUTURE_PLATFORM_VARIANT_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 8

    names = [item["input_name"] for item in contract["required_inputs"]]
    expected_names = [
        "approved_canonical_article_ref",
        "refined_canonical_draft_ref",
        "seo_metadata_ref",
        "platform_style_rules_ref",
        "platform_capability_matrix_ref",
        "destination_binding_ref",
        "exact_payload_approval_ref",
        "jim_review_ref"
    ]
    assert names == expected_names

    for item in contract["required_inputs"]:
        assert item["required"] is True
        assert item["current_status"] == "missing"
        assert item["value_ref"] is None
        assert item["raw_value_persisted"] is False
        assert item["blocks_platform_variant_generation"] is True
