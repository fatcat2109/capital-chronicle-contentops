"""V6 Draft Inspector V2.

Orchestrates all draft inspections and quality QAs for the V6 content pipeline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import content_quality_qa_v2 as quality_qa
from live_contentops import thread_continuation_quality_v2 as thread_qa
from live_contentops import platform_variant_inspector_v2 as variant_inspector

TASK_LABEL = "TASK_CONTENTOPS_V6_DRAFT_INSPECTOR_V2_AND_CONTENT_QUALITY_QA_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_DRAFT_INSPECTOR_V2")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Draft Inspector V2")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--article-packet", default="docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json")
    parser.add_argument("--seo-packet", default="docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json")
    parser.add_argument("--variant-pack", default="docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json")
    parser.add_argument("--thread-pack", default="docs/automation/V6_PLATFORM_CONTENT_GENERATORS/thread_continuation_pack.json")
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load packets
    article_path = Path(args.article_packet)
    seo_path = Path(args.seo_packet)
    variant_path = Path(args.variant_pack)
    thread_path = Path(args.thread_pack)
    
    if not article_path.exists() or not seo_path.exists() or not variant_path.exists():
        # Fallback mocks for tests/isolated execution
        article_data = {
            "article_id": "art_stub_123",
            "title": "Stub Volatility Study",
            "subtitle": "Unverified deep dive",
            "body_markdown": "Treasury yield volatility historical observations.",
            "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"],
            "limitations": "Yield analysis is uncertain. Caveat parameter limits exist.",
            "disclosure": "No financial advice.",
            "draft_status": "review_only_draft_requires_source_verification",
            "blockers": ["source_verification_required"]
        }
        seo_data = {
            "readability_score": 85.0,
            "editorial_score": 90.0,
            "audience_fit_score": 95.0,
            "rejected_clickbait": [],
            "blockers": ["source_verification_required"]
        }
        variant_data = {
            "x_manual_thread": {
                "variant_id": "var_stub",
                "source_article_id": "art_stub_123",
                "platform_family": "x_manual_thread",
                "variant_text": "stub",
                "segment_count": 1,
                "segments": [{
                    "segment_index": 1,
                    "total_segments": 1,
                    "sequence_label": "(1/1)",
                    "segment_text": "stub content",
                    "segment_hash": "a" * 64,
                    "review_only": True,
                    "public_postable": False,
                    "dispatch_allowed_now": False
                }],
                "source_verification_required": True,
                "blocked_reasons": ["publication_blocked_until_source_verification"]
            }
        }
        thread_data = {}
    else:
        article_data = json.loads(article_path.read_text(encoding="utf-8"))
        seo_data = json.loads(seo_path.read_text(encoding="utf-8"))
        variant_data = json.loads(variant_path.read_text(encoding="utf-8"))
        thread_data = json.loads(thread_path.read_text(encoding="utf-8"))
        
    blockers = []
    
    # 1. Source Truth and Citation check
    source_verification_required = (
        article_data.get("draft_status") == "review_only_draft_requires_source_verification" or
        "source_verification_required" in article_data.get("blockers", []) or
        "source_verification_required" in seo_data.get("blockers", [])
    )
    if source_verification_required:
        blockers.append("source_verification_required")
        blockers.append("publication_blocked_until_source_verification")
        
    source_truth_report = {
        "source_verification_required": source_verification_required,
        "allowed_for_publication": not source_verification_required,
        "citations_integrity": "UNVERIFIED_SAMPLE_SOURCE_REF" in str(article_data.get("citations", [])),
        "source_truth_status": "review_only_unverified" if source_verification_required else "verified"
    }
    Path(out_dir / "source_truth_and_citation_report.json").write_text(
        json.dumps(source_truth_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 2. Financial advice check
    financial_keywords = ["buy", "sell", "hold", "price target", "entry", "exit", "stop loss", "position size", "guaranteed return", "signal", "trade setup", "alpha call"]
    financial_advice_detected = False
    
    # Check article body/title and variant texts
    combined_texts = [article_data.get("title", ""), article_data.get("body_markdown", "")]
    for var in variant_data.values():
        combined_texts.append(var.get("variant_text", ""))
        for s in var.get("segments", []):
            combined_texts.append(s.get("segment_text", ""))
            
    for text in combined_texts:
        for kw in financial_keywords:
            if f" {kw} " in f" {text.lower()} " or text.lower().startswith(kw) or text.lower().endswith(kw):
                financial_advice_detected = True
                break
                
    if financial_advice_detected:
        blockers.append("financial_advice_or_signal_language_detected")
        
    financial_report = {
        "no_financial_advice_safety_checks_pass": not financial_advice_detected,
        "detected_keywords": [kw for kw in financial_keywords if any(kw in t.lower() for t in combined_texts)]
    }
    Path(out_dir / "no_financial_advice_report.json").write_text(
        json.dumps(financial_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 3. SEO / Editorial check
    seo_quality_report = {
        "seo_integrity_valid": "source_verification_required" in seo_data.get("blockers", []),
        "clickbait_filtered": seo_data.get("rejected_clickbait") == []
    }
    Path(out_dir / "seo_editorial_quality_report.json").write_text(
        json.dumps(seo_quality_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 4. Platform Variant check
    variant_report = variant_inspector.inspect_platform_variants(variant_data)
    if variant_report["blockers"]:
        blockers.extend(variant_report["blockers"])
    Path(out_dir / "platform_variant_inspection_report.json").write_text(
        json.dumps(variant_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 5. Thread Continuation check
    from live_contentops import platform_variant_constraint_registry_v6 as constraint_registry
    max_limits = {}
    for fam in constraint_registry.PLATFORM_FAMILIES:
        max_limits[fam] = constraint_registry.get_constraints(fam)["max_text_length"]
        
    raw_reference_text = f"{article_data.get('title', '')}\n{article_data.get('subtitle', '')}\n\n{article_data.get('body_markdown', '')}\n\n{article_data.get('limitations', '')}\n\n{article_data.get('disclosure', '')}"
    thread_report = thread_qa.inspect_thread_continuation(variant_data, max_limits, raw_reference_text)
    if thread_report["blockers"]:
        blockers.extend(thread_report["blockers"])
    Path(out_dir / "thread_continuation_quality_report.json").write_text(
        json.dumps(thread_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 6. Quality Scorecard
    scorecard = quality_qa.score_draft_quality(article_data, seo_data, variant_data)
    Path(out_dir / "content_quality_scorecard.json").write_text(
        json.dumps(scorecard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    blockers = sorted(list(set(blockers)))
    
    # Final status packet
    status = "BLOCKED_REVIEW_ONLY_ISSUES_FOUND" if blockers else "READY_FOR_OPERATOR_REVIEW"
    
    packet = {
        "draft_inspector_status": status,
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
        "human_review_required": True,
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "next_recommended_task": "TASK_CONTENTOPS_V6_UNIFIED_PAYLOAD_HASH_APPROVAL_OUTBOX_UPGRADE_HEAVY_BATCH_V0",
        "blockers": blockers
    }
    Path(out_dir / "draft_inspector_v2_packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Blocker report
    blocker_str = ", ".join(f"`{b}`" for b in blockers) if blockers else "None"
    Path(out_dir / "draft_inspector_blocker_report.md").write_text(
        f"# Draft Inspector Blocker Report\n\n- **Blockers**: {blocker_str}\n",
        encoding="utf-8"
    )
    
    # Runbook
    Path(out_dir / "draft_inspector_runbook.md").write_text(
        "# Draft Inspector Runbook\n\nRuns Draft Inspector V2 checks.\n",
        encoding="utf-8"
    )
    
    # Implementation report
    Path(out_dir / "implementation_report.md").write_text(
        f"# Draft Inspector Implementation Report\n\n- **Task Label**: {TASK_LABEL}\n- **Status**: {status}\n",
        encoding="utf-8"
    )
    
    # Next task pointer
    Path(out_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{packet['next_recommended_task']}`\n",
        encoding="utf-8"
    )
    
    print(json.dumps({
        "draft_inspector_status": packet["draft_inspector_status"],
        "blockers": packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
