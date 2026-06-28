import re
from live_contentops import substack_compose_payload_mapper_v6 as mapper

def test_payload_mapping():
    contract = {
        "canonical_article": {
            "title": "Bond Volatility",
            "subtitle": "Overview",
            "body_markdown": "Test body text.",
            "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"]
        },
        "seo_packet": {
            "meta_description": "Real SEO description"
        }
    }
    hash_manifest = {
        "unified_payload_bundle_hash": "a" * 64,
        "canonical_article_hash": "b" * 64
    }
    preview = mapper.map_canonical_to_preview(contract, hash_manifest)
    assert preview["title"] == "Bond Volatility"
    assert preview["slug_candidate"] == "bond-volatility"
    assert preview["source_verification_required"] is True
    assert preview["seo_meta_description"] == "Real SEO description"
    assert preview["payload_hash"] == "a" * 64
    assert preview["canonical_article_hash"] == "b" * 64
    
    # Validation report checks
    report = mapper.validate_compose_payload(preview)
    assert "source_verification_required" in report["blockers"]
    assert "payload_hash_unhashed" not in report["blockers"]
    assert "payload_hash_invalid" not in report["blockers"]
    assert "canonical_article_hash_invalid" not in report["blockers"]
    assert "seo_meta_description_missing" not in report["blockers"]

def test_payload_mapping_failures():
    contract_bad = {
        "canonical_article": {
            "title": "Bond Volatility",
            "citations": []
        },
        "seo_packet": {
            "seo_meta_description": "SEO Description Stub"
        }
    }
    # Test unhashed fallback
    preview = mapper.map_canonical_to_preview(contract_bad, {})
    report = mapper.validate_compose_payload(preview)
    assert "payload_hash_unhashed" in report["blockers"]
    assert "canonical_article_hash_invalid" in report["blockers"]
    assert "seo_meta_description_stub_detected" in report["blockers"]
    
    # Test invalid hex formats
    preview["payload_hash"] = "shorthex"
    preview["canonical_article_hash"] = "shorthex2"
    report_invalid = mapper.validate_compose_payload(preview)
    assert "payload_hash_invalid" in report_invalid["blockers"]
    assert "canonical_article_hash_invalid" in report_invalid["blockers"]

def test_financial_advice_detection():
    contract_unsafe = {
        "canonical_article": {
            "title": "Yields",
            "body_markdown": "We advice to buy stock XYZ.",
            "citations": []
        }
    }
    preview_unsafe = mapper.map_canonical_to_preview(contract_unsafe, {"unified_payload_bundle_hash": "a" * 64, "canonical_article_hash": "b" * 64})
    report = mapper.validate_compose_payload(preview_unsafe)
    assert "unsafe_financial_advice_phrase_detected" in report["blockers"]

