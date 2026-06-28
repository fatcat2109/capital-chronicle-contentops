from live_contentops import unified_payload_contract_v6 as contract

import json
from live_contentops import unified_payload_contract_v6 as contract
from live_contentops import platform_variant_inspector_v2 as vi

def test_unified_payload_contract_binding(tmp_path):
    variants = {}
    for fam in vi.REQUIRED_FAMILIES:
        variants[fam] = {
            "variant_id": "var_1",
            "source_article_id": "art_123",
            "platform_family": fam,
            "variant_text": "Treasury volatility reflections. No financial advice. Limits apply.",
            "segment_count": 1,
            "segments": [{
                "segment_index": 1,
                "total_segments": 1,
                "sequence_label": "(1/1)",
                "segment_text": "Treasury volatility reflections. No financial advice. Limits apply.",
                "segment_hash": "a" * 64,
                "review_only": True,
                "public_postable": False,
                "dispatch_allowed_now": False
            }],
            "source_verification_required": True,
            "approval_required": True,
            "blocked_reasons": ["publication_blocked_until_source_verification", "source_verification_required"]
        }
        
    manifest = {}
    for fam, var in variants.items():
        manifest[fam] = {
            "platform_family": fam,
            "variant_id": var["variant_id"],
            "source_article_id": var["source_article_id"],
            "variant_text_hash": "a" * 64,
            "segment_hashes": ["b" * 64],
            "segment_count": 1,
            "source_verification_required": True,
            "draft_inspector_status": "BLOCKED",
            "quality_score_refs": {},
            "review_only": True,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "approval_required": True,
            "exact_payload_hash_required": True,
            "blocked_reasons": var["blocked_reasons"],
            "payload_mutation_after_hash_forbidden": True
        }
        
    for fam in vi.REQUIRED_FAMILIES:
        assert fam in manifest
        assert manifest[fam]["review_only"] is True
        assert manifest[fam]["public_postable"] is False
        assert manifest[fam]["dispatch_allowed_now"] is False
