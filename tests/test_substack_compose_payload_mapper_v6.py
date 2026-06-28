from live_contentops import substack_compose_payload_mapper_v6 as mapper

def test_payload_mapping():
    contract = {
        "canonical_article": {
            "title": "Bond Volatility",
            "subtitle": "Overview",
            "body_markdown": "Test body text.",
            "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"]
        }
    }
    preview = mapper.map_canonical_to_preview(contract)
    assert preview["title"] == "Bond Volatility"
    assert preview["slug_candidate"] == "bond-volatility"
    assert preview["source_verification_required"] is True
    
    # Financial advice keyword detection
    contract_unsafe = {
        "canonical_article": {
            "title": "Yields",
            "body_markdown": "We advice to buy stock XYZ.",
            "citations": []
        }
    }
    preview_unsafe = mapper.map_canonical_to_preview(contract_unsafe)
    report = mapper.validate_compose_payload(preview_unsafe)
    assert "unsafe_financial_advice_phrase_detected" in report["blockers"]
