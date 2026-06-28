import json
import re
from live_contentops import draft_inspector_v2 as draft_inspector

def test_draft_inspector_blocks_on_financial_advice_keyword(tmp_path):
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Treasury yield volatility buy signals.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Yield analysis is uncertain.",
        "disclosure": "No financial advice.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {
        "readability_score": 85.0,
        "editorial_score": 90.0,
        "audience_fit_score": 95.0,
        "rejected_clickbait": [],
        "blockers": ["source_verification_required"]
    }
    variants = {}
    from live_contentops import platform_variant_inspector_v2 as vi
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
        
    art_file = tmp_path / "art.json"
    seo_file = tmp_path / "seo.json"
    var_file = tmp_path / "var.json"
    thread_file = tmp_path / "thread.json"
    
    art_file.write_text(json.dumps(article), encoding="utf-8")
    seo_file.write_text(json.dumps(seo), encoding="utf-8")
    var_file.write_text(json.dumps(variants), encoding="utf-8")
    thread_file.write_text(json.dumps({}), encoding="utf-8")
    
    out_dir = tmp_path / "out"
    draft_inspector.main([
        "--output-dir", str(out_dir),
        "--article-packet", str(art_file),
        "--seo-packet", str(seo_file),
        "--variant-pack", str(var_file),
        "--thread-pack", str(thread_file)
    ])
    
    packet = json.loads((out_dir / "draft_inspector_v2_packet.json").read_text(encoding="utf-8"))
    assert "financial_advice_or_signal_language_detected" in packet["blockers"]

def test_draft_inspector_hashing_and_unverified_ref(tmp_path):
    article = {
        "article_id": "art_123",
        "title": "Study of Volatility",
        "subtitle": "Unverified deep dive",
        "body_markdown": "Treasury yield volatility historical observations.",
        "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
        "limitations": "Yield analysis is uncertain.",
        "disclosure": "No financial advice.",
        "draft_status": "review_only_draft_requires_source_verification"
    }
    seo = {
        "readability_score": 85.0,
        "editorial_score": 90.0,
        "audience_fit_score": 95.0,
        "rejected_clickbait": [],
        "blockers": ["source_verification_required"]
    }
    variants = {}
    from live_contentops import platform_variant_inspector_v2 as vi
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
        
    art_file = tmp_path / "art.json"
    seo_file = tmp_path / "seo.json"
    var_file = tmp_path / "var.json"
    thread_file = tmp_path / "thread.json"
    
    art_file.write_text(json.dumps(article), encoding="utf-8")
    seo_file.write_text(json.dumps(seo), encoding="utf-8")
    var_file.write_text(json.dumps(variants), encoding="utf-8")
    thread_file.write_text(json.dumps({}), encoding="utf-8")
    
    out_dir = tmp_path / "out"
    draft_inspector.main([
        "--output-dir", str(out_dir),
        "--article-packet", str(art_file),
        "--seo-packet", str(seo_file),
        "--variant-pack", str(var_file),
        "--thread-pack", str(thread_file)
    ])
    
    # Read the output packet
    packet = json.loads((out_dir / "draft_inspector_v2_packet.json").read_text(encoding="utf-8"))
    assert packet["draft_inspector_status"] == "BLOCKED_REVIEW_ONLY_ISSUES_FOUND"
    assert "source_verification_required" in packet["blockers"]
    assert "publication_blocked_until_source_verification" in packet["blockers"]
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["kill_switch_active"] is True
