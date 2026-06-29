"""V6 Platform Variant Input Contract Queue Coordinator.

Orchestrates empty platform variant queue artifacts and enforces safety invariants.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from live_contentops import platform_variant_queue_packet_v6 as packet_builder
from live_contentops import platform_variant_input_contract_v6 as contract_builder
from live_contentops import platform_variant_queue_validator_v6 as validator_module

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_VARIANT_INPUT_CONTRACT_QUEUE")
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_V6_PLATFORM_VARIANT_RENDERER_BLOCKED_OUTPUT_DRY_RUN_HEAVY_BATCH_V0"


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")


def make_blocked_platform_variant_output() -> dict[str, Any]:
    return {
        "platform_variant_output_status": "BLOCKED_NO_PLATFORM_VARIANTS_RENDERED",
        "runtime_truth": False,
        "platform_variant_generation_performed": False,
        "platform_copy_generated": False,
        "substack_title": None,
        "substack_body": None,
        "substack_subtitle": None,
        "discord_message": None,
        "telegram_message": None,
        "x_thread": [],
        "linkedin_post": None,
        "platform_payloads": [],
        "platform_payload_hashes": [],
        "destination_bindings": [],
        "account_bindings": [],
        "public_urls": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "platform_metrics": [],
        "body_word_count": 0,
        "platform_variant_count": 0,
        "platform_payload_count": 0,
        "public_url_count": 0,
        "public_postable": False,
        "allowed_for_publication": False,
        "dispatch_allowed_now": False,
        "blockers": [
            "approved_canonical_article_missing",
            "seo_metadata_missing",
            "platform_variant_generation_blocked",
            "destination_binding_missing",
            "exact_payload_approval_missing",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_platform_variant_readiness_matrix() -> list[dict[str, Any]]:
    platforms = [
        ("substack", "long_form"),
        ("discord", "chat"),
        ("telegram", "chat"),
        ("x", "microblog"),
        ("linkedin", "professional"),
        ("threads", "microblog")
    ]
    matrix = []
    for platform, family in platforms:
        matrix.append({
            "platform": platform,
            "platform_family": family,
            "variant_generation_status": "blocked_missing_approved_canonical_article",
            "approved_canonical_article_available": False,
            "seo_metadata_available": False,
            "platform_style_rules_available": False,
            "destination_binding_completed": False,
            "exact_payload_approval_completed": False,
            "platform_copy_generated": False,
            "payload_hash_created": False,
            "outbox_entry_created": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "public_url_created": False,
            "valid_for_publication": False,
            "blocks_publication": True,
            "blockers": [
                "approved_canonical_article_missing",
                "seo_metadata_missing",
                "destination_binding_missing",
                "exact_payload_approval_missing",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_platform_variant_checklist() -> dict[str, Any]:
    checklist_items = [
        "approved_canonical_article_required",
        "refined_draft_required",
        "seo_metadata_required",
        "platform_style_rules_required",
        "destination_binding_required",
        "exact_payload_approval_required",
        "no_platform_copy_generated",
        "no_outbox_entry_created",
        "no_publication_ready_claim",
        "no_dispatch_ready_claim",
        "no_financial_advice_language",
        "jim_final_review_required"
    ]
    items_dict = {}
    for item in checklist_items:
        items_dict[item] = {
            "current_status": "pending",
            "blocks_variant_generation": True,
            "blocks_publication": True,
            "evidence_ref": "platform_variant_queue_packet.json"
        }
    return {
        "checklist_status": "PLATFORM_VARIANTS_BLOCKED_PENDING_APPROVED_CANONICAL_ARTICLE",
        "items": items_dict
    }


def make_blocker_report_markdown(blockers: list[str]) -> str:
    lines = [
        "# V6 Platform Variant Input Contract Queue Blocker Report",
        "",
        "The following active blockers prevent platform variant input queue, generation, or dispatch operations:",
        ""
    ]
    for b in blockers:
        lines.append(f"- **{b}**: Locked by default dry-run configuration.")
    lines.extend([
        "",
        "## Offline Safety Guarantees",
        "- Raw sources and operators are strictly redacted.",
        "- Platform API and webhook dispatches are disabled.",
        "- Jim's review signature is completely absent."
    ])
    return "\n".join(lines)


def make_runbook_markdown() -> str:
    return """# V6 Platform Variant Input Contract Queue Runbook

This runbook documents operator and system actions for the offline simulated platform variant contract queue state.

## Operator Review Checklist
1. Confirm that all platform output fields remain unpopulated (null or empty list).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Approved canonical article is required to clear `approved_canonical_article_missing` and route to platform variant generation.
"""


def make_implementation_report_markdown() -> str:
    return """# V6 Platform Variant Input Contract Queue Implementation Report

## Summary
The Platform Variant Input Contract Queue lane is established as an offline, dry-run state.

## Verified Invariants
- `platform_variant_queue_status` = `PLATFORM_VARIANTS_BLOCKED_WAITING_FOR_APPROVED_CANONICAL_ARTICLE`
- All active post/dispatch flags are hardlocked to `false`.
"""


def make_next_task_pointer_markdown() -> str:
    return f"""# Next recommended task
{NEXT_RECOMMENDED_TASK}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Platform Variant Input Contract Queue Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create packets, contracts, outputs
    platform_variant_queue_packet = packet_builder.make_platform_variant_queue_packet()
    platform_variant_input_contract = contract_builder.make_platform_variant_input_contract()
    platform_variant_blocked_output = make_blocked_platform_variant_output()
    platform_variant_readiness_matrix = make_platform_variant_readiness_matrix()
    platform_variant_checklist = make_platform_variant_checklist()

    # 2. Run validator
    report, blockers = validator_module.validate_platform_variant_input_contract_queue(
        platform_variant_queue_packet, platform_variant_input_contract,
        platform_variant_blocked_output, platform_variant_readiness_matrix,
        platform_variant_checklist
    )

    # 3. Write all 10 artifacts
    write_json(out_dir / "platform_variant_queue_packet.json", platform_variant_queue_packet)
    write_json(out_dir / "platform_variant_input_contract.json", platform_variant_input_contract)
    write_json(out_dir / "platform_variant_blocked_output.json", platform_variant_blocked_output)
    write_json(out_dir / "platform_variant_readiness_matrix.json", platform_variant_readiness_matrix)
    write_json(out_dir / "platform_variant_checklist.json", platform_variant_checklist)
    write_json(out_dir / "platform_variant_queue_validation_report.json", report)
    write_text(out_dir / "platform_variant_blocker_report.md", make_blocker_report_markdown(blockers))
    write_text(out_dir / "platform_variant_runbook.md", make_runbook_markdown())
    write_text(out_dir / "implementation_report.md", make_implementation_report_markdown())
    write_text(out_dir / "next_task_pointer.md", make_next_task_pointer_markdown())

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
