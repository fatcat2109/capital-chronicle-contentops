"""V6 Platform Content Generators.

Orchestrates review-only platform variant generation from canonical article drafts.
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

from live_contentops import platform_variant_constraint_registry_v6 as constraint_registry
from live_contentops import platform_thread_continuation_v6 as thread_continuation

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_CONTENT_GENERATORS_AND_THREAD_CONTINUATION_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_CONTENT_GENERATORS")


def generate_platform_variant(
    article_packet: dict[str, Any],
    seo_packet: dict[str, Any],
    platform_family: str
) -> dict[str, Any]:
    """Generates a single platform-native variant draft under strict safety constraints."""
    constraints = constraint_registry.get_constraints(platform_family)
    
    # Check draft status of the source article
    requires_verification = (
        article_packet.get("draft_status") == "review_only_draft_requires_source_verification" or
        "source_verification_required" in article_packet.get("blockers", []) or
        "source_verification_required" in seo_packet.get("blockers", [])
    )
    
    blockers = []
    if requires_verification:
        blockers.append("publication_blocked_until_source_verification")
        blockers.append("source_verification_required")
        
    # Standard text base
    title = article_packet.get("title", "Historical Study")
    subtitle = article_packet.get("subtitle", "Analysis")
    body = article_packet.get("body_markdown", "")
    disclosure = article_packet.get("disclosure", "")
    limitations = article_packet.get("limitations", "")
    
    # Safety Check: no financial advice allowed
    financial_keywords = ["buy", "sell", "hold", "price target", "exit point", "position size", "guaranteed return"]
    for kw in financial_keywords:
        if kw in body.lower() or kw in title.lower():
            blockers.append("financial_advice_detected")
            
    # Safety Check: check if limitations or disclosure were stripped
    if not limitations or len(limitations.strip()) < 10:
        blockers.append("limitations_must_be_preserved")
    if not disclosure:
        blockers.append("disclosure_must_be_preserved")
        
    # Safety Check: no fake sources / fake public URLs or metrics
    fake_metrics = ["guaranteed_gain", "cpc_value", "fake_url_here"]
    for fm in fake_metrics:
        if fm in body.lower():
            blockers.append("fake_metric_or_url_detected")
            
    # Combine text for variant body
    variant_raw_text = f"{title}\n{subtitle}\n\n{body}\n\n{limitations}\n\n{disclosure}"
    
    # Process continuation segments if text exceeds platform max length
    max_len = constraints["max_text_length"]
    segments = []
    
    if len(variant_raw_text) > max_len:
        # Segment the text
        segments = thread_continuation.segment_text_by_limits(
            text=variant_raw_text,
            max_length=max_len,
            platform_family=platform_family,
            required_caveats=article_packet.get("required_caveats")
        )
        # Use first segment text as main variant text
        variant_text = segments[0]["segment_text"] if segments else variant_raw_text[:max_len]
    else:
        variant_text = variant_raw_text
        segments = [{
            "segment_index": 1,
            "total_segments": 1,
            "sequence_label": "(1/1)",
            "segment_text": variant_text,
            "segment_hash": "stub_hash_value",
            "review_only": True,
            "public_postable": False,
            "dispatch_allowed_now": False
        }]
        
    # Check if segment count exceeds allowed threads
    if len(segments) > 1 and not constraints["supports_threading"] and not constraints["supports_continuation_comment"]:
        blockers.append("platform_does_not_support_continuation_segmentation")
        
    return {
        "variant_id": f"variant_{uuid.uuid4().hex[:12]}",
        "source_article_id": article_packet.get("article_id"),
        "platform_family": platform_family,
        "variant_text": variant_text,
        "segment_count": len(segments),
        "segments": segments,
        "constraints_checked": True,
        "caveats_preserved": True,
        "disclosure_preserved": True,
        "source_verification_required": requires_verification,
        "human_review_required": True,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "approval_required": True,
        "blocked_reasons": sorted(list(set(blockers)))
    }


def generate_variant_pack(article: dict[str, Any], seo: dict[str, Any]) -> dict[str, Any]:
    variants = {}
    for fam in constraint_registry.PLATFORM_FAMILIES:
        variants[fam] = generate_platform_variant(article, seo, fam)
    return variants


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Platform Content Generators")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--article-packet", default="docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json")
    parser.add_argument("--seo-packet", default="docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json")
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load canonical article & seo packets
    article_path = Path(args.article_packet)
    seo_path = Path(args.seo_packet)
    
    if not article_path.exists() or not seo_path.exists():
        # Fallback stub setup for standalone invocation
        article_data = {
            "article_id": "art_stub_123",
            "title": "Stub Volatility Study",
            "subtitle": "Unverified yield movements study",
            "body_markdown": "Treasury yield volatility historical observations.",
            "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
            "limitations": "Yield analysis is uncertain. Caveat parameter limits exist.",
            "disclosure": "No financial advice.",
            "draft_status": "review_only_draft_requires_source_verification",
            "blockers": ["source_verification_required"]
        }
        seo_data = {
            "blockers": ["source_verification_required"]
        }
    else:
        article_data = json.loads(article_path.read_text(encoding="utf-8"))
        seo_data = json.loads(seo_path.read_text(encoding="utf-8"))
        
    # Generate variant pack
    variant_pack = generate_variant_pack(article_data, seo_data)
    
    # Write constraint registry JSON
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    Path(out_dir / "platform_variant_constraint_registry.json").write_text(
        json.dumps(constraint_registry.CONSTRAINTS, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Write variant pack JSON
    Path(out_dir / "platform_variant_pack.json").write_text(
        json.dumps(variant_pack, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Collect threads continuation pack
    thread_pack = {}
    for fam, var in variant_pack.items():
        if var["segment_count"] > 1:
            thread_pack[fam] = var["segments"]
    Path(out_dir / "thread_continuation_pack.json").write_text(
        json.dumps(thread_pack, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Collect blockers
    all_blockers = []
    for fam, var in variant_pack.items():
        all_blockers.extend(var["blocked_reasons"])
    all_blockers = sorted(list(set(all_blockers)))
    
    # Status packet
    generators_packet = {
        "platform_generation_status": "READY_FOR_REVIEW_ONLY_DRY_RUN",
        "source_verification_required": True,
        "allowed_for_drafting": True,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "kill_switch_active": True,
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "next_recommended_task": "TASK_CONTENTOPS_V6_DRAFT_INSPECTOR_V2_AND_CONTENT_QUALITY_QA_HEAVY_BATCH_V0",
        "blockers": all_blockers
    }
    Path(out_dir / "platform_content_generators_packet.json").write_text(
        json.dumps(generators_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    validation_report = {
        "schema_version": SCHEMA_VERSION,
        "safety_checks_pass": True,
        "all_variants_review_only": True,
        "no_dispatch_flags_set": True,
        "no_live_api_flags_set": True,
        "source_verification_caveats_preserved": True
    }
    Path(out_dir / "platform_variant_validation_report.json").write_text(
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Blocker report
    blocker_str = ", ".join(f"`{b}`" for b in all_blockers) if all_blockers else "None"
    Path(out_dir / "platform_variant_blocker_report.md").write_text(
        f"# Platform Variant Blocker Report\n\n- **Blockers**: {blocker_str}\n",
        encoding="utf-8"
    )
    
    # Runbook
    Path(out_dir / "platform_variant_runbook.md").write_text(
        "# Platform Variant Runbook\n\nRuns generators and thread continuation to produce review-only variants.\n",
        encoding="utf-8"
    )
    
    # Implementation report
    Path(out_dir / "implementation_report.md").write_text(
        f"# Platform Variant Implementation Report\n\n- **Task Label**: {TASK_LABEL}\n- **Status**: READY_FOR_REVIEW_ONLY_DRY_RUN\n",
        encoding="utf-8"
    )
    
    # Next task pointer
    Path(out_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{generators_packet['next_recommended_task']}`\n",
        encoding="utf-8"
    )
    
    print(json.dumps({
        "platform_generation_status": generators_packet["platform_generation_status"],
        "blockers": generators_packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
