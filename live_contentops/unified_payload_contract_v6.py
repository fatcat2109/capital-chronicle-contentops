"""V6 Unified Payload Contract.

Binds all V6 pipeline outputs into a single deterministic review-only contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops import unified_payload_hash_manifest_v6 as hash_manifest
from live_contentops import unified_approval_outbox_readiness_v6 as readiness_lane
from live_contentops import multi_platform_payload_integrity_v6 as integrity_check

TASK_LABEL = "TASK_CONTENTOPS_V6_UNIFIED_PAYLOAD_HASH_APPROVAL_OUTBOX_UPGRADE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX")


def load_json_or_mock(path_str: str, mock_data: dict[str, Any]) -> dict[str, Any]:
    path = Path(path_str)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return mock_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Unified Payload Contract Builder")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all input packets
    ai_prod = load_json_or_mock(
        "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_packet.json",
        {"ai_production_status": "READY_FOR_REVIEW_ONLY_DRY_RUN"}
    )
    canonical_art = load_json_or_mock(
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json",
        {"title": "Stub Title", "body_markdown": "Stub body.", "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"]}
    )
    seo_packet = load_json_or_mock(
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json",
        {"blockers": ["source_verification_required"]}
    )
    platform_generators = load_json_or_mock(
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_content_generators_packet.json",
        {"blockers": ["source_verification_required"]}
    )
    variant_pack = load_json_or_mock(
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json",
        {}
    )
    thread_pack = load_json_or_mock(
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/thread_continuation_pack.json",
        {}
    )
    variant_validation = load_json_or_mock(
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_validation_report.json",
        {}
    )
    draft_inspector = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_v2_packet.json",
        {"blockers": ["source_verification_required"]}
    )
    scorecard = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/content_quality_scorecard.json",
        {}
    )
    source_truth = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/source_truth_and_citation_report.json",
        {}
    )
    financial_advice = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/no_financial_advice_report.json",
        {}
    )
    variant_inspection = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/platform_variant_inspection_report.json",
        {}
    )
    thread_quality = load_json_or_mock(
        "docs/automation/V6_DRAFT_INSPECTOR_V2/thread_continuation_quality_report.json",
        {}
    )
    
    # Load upstream approval capture and signature binding state
    approval_capture = load_json_or_mock(
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_packet.json",
        {"operator_approved": False}
    )
    signature_binding = load_json_or_mock(
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_packet.json",
        {"operator_signature_valid": False}
    )
    approval_ledger = load_json_or_mock(
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_packet.json",
        {"approval_ledger_entry_created": False}
    )
    destination_outbox = load_json_or_mock(
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_outbox_draft_packet.json",
        {"destination_binding_complete": False}
    )
    
    contract_packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "ai_production": ai_prod,
        "canonical_article": canonical_art,
        "seo_packet": seo_packet,
        "platform_generators": platform_generators,
        "variant_pack": variant_pack,
        "thread_pack": thread_pack,
        "variant_validation": variant_validation,
        "draft_inspector": draft_inspector,
        "scorecard": scorecard,
        "source_truth_report": source_truth,
        "no_financial_advice_report": financial_advice,
        "platform_variant_inspection_report": variant_inspection,
        "thread_continuation_quality_report": thread_quality,
        "approval_capture": approval_capture,
        "signature_binding": signature_binding,
        "approval_ledger": approval_ledger,
        "destination_outbox": destination_outbox
    }
    
    # Generate multi-platform payload manifest
    manifest_data = {}
    for fam, var in variant_pack.items():
        var_text = var.get("variant_text", "")
        # Compute text hash
        v_hash = hashlib.sha256(var_text.encode("utf-8")).hexdigest()
        seg_hashes = [s.get("segment_hash", "") for s in var.get("segments", [])]
        
        manifest_data[fam] = {
            "platform_family": fam,
            "variant_id": var.get("variant_id"),
            "source_article_id": var.get("source_article_id"),
            "variant_text_hash": v_hash,
            "segment_hashes": seg_hashes,
            "segment_count": len(seg_hashes),
            "source_verification_required": var.get("source_verification_required", True),
            "draft_inspector_status": draft_inspector.get("draft_inspector_status"),
            "quality_score_refs": scorecard,
            "review_only": True,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "approval_required": True,
            "exact_payload_hash_required": True,
            "blocked_reasons": var.get("blocked_reasons", []),
            "payload_mutation_after_hash_forbidden": True
        }
        
    # Write initial documents
    Path(out_dir / "unified_payload_contract_packet.json").write_text(
        json.dumps(contract_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    Path(out_dir / "multi_platform_payload_manifest.json").write_text(
        json.dumps(manifest_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Build deterministic hashes manifest
    hash_manifest.generate_hashes(out_dir, contract_packet, manifest_data)
    
    # Run readiness analysis
    readiness_lane.generate_readiness_reports(out_dir, contract_packet, manifest_data)
    
    # Run integrity and mutation validation checks
    integrity_check.validate_integrity(out_dir, manifest_data)
    
    # Unified status check
    status_packet = load_json_or_mock(str(out_dir / "unified_approval_readiness_report.json"), {})
    
    # Write runbook
    Path(out_dir / "unified_payload_runbook.md").write_text(
        "# Unified Payload Runbook\n\nConsolidates V6 content lifecycle pipeline outputs.\n",
        encoding="utf-8"
    )
    
    # Write implementation report
    Path(out_dir / "implementation_report.md").write_text(
        f"# Unified Payload Implementation Report\n\n- **Task Label**: {TASK_LABEL}\n- **Status**: {status_packet.get('unified_payload_status', 'READY_FOR_REVIEW_ONLY_HASHED_PAYLOADS')}\n",
        encoding="utf-8"
    )
    
    # Write next task pointer
    Path(out_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{status_packet.get('next_recommended_task', 'TASK_CONTENTOPS_V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE_AND_REDACTED_STATUS_HEAVY_BATCH_V0')}`\n",
        encoding="utf-8"
    )
    
    print(json.dumps({
        "unified_payload_status": status_packet.get("unified_payload_status"),
        "blockers": status_packet.get("blockers", [])
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
