"""Test V6 Canonical Article Studio Renderer Input Contract."""
from __future__ import annotations

from live_contentops import canonical_article_studio_renderer_input_contract_v6 as contract_builder


def test_make_canonical_article_studio_renderer_input_contract():
    contract = contract_builder.make_canonical_article_studio_renderer_input_contract()

    assert contract["contract_status"] == "FUTURE_INPUT_CONTRACT_ONLY"
    assert contract["runtime_truth"] is False
    assert len(contract["required_inputs"]) == 7

    names = [item["input_name"] for item in contract["required_inputs"]]
    expected_names = [
        "approved_source_pack_ref",
        "operator_approval_ref",
        "source_approval_hash_ref",
        "redacted_claim_binding_ref",
        "placeholder_binding_ref",
        "editor_shell_ref",
        "jim_review_ref"
    ]
    assert names == expected_names

    for item in contract["required_inputs"]:
        assert item["required"] is True
        assert item["current_status"] == "missing"
        assert item["value_ref"] is None
        assert item["raw_value_persisted"] is False
        assert item["blocks_renderer_execution"] is True
