"""V6 Approval Queue Exact Payload Review Contract Coordinator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import approval_queue_exact_payload_review_packet_v6 as packet_builder
from live_contentops import approval_queue_exact_payload_review_input_contract_v6 as contract_builder
from live_contentops import approval_queue_exact_payload_review_validator_v6 as validator

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_APPROVAL_QUEUE_EXACT_PAYLOAD_REVIEW_CONTRACT")


def make_approval_queue_blocked_review_template() -> dict[str, Any]:
    """Generates default blocked review template."""
    return {
        "review_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_EXACT_PAYLOAD_REVIEW",
        "runtime_truth": False,
        "approval_queue_entry_id": None,
        "approval_id": None,
        "approval_hash": None,
        "payload_hash": None,
        "exact_payload_preview_ref": None,
        "platform_payload_manifest_ref": None,
        "destination_binding_ref": None,
        "account_binding_ref": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "reviewed_at_redacted": None,
        "review_statement": None,
        "approval_valid_for_dispatch": False,
        "exact_payload_review_performed": False,
        "exact_payload_approval_completed": False,
        "approval_queue_entry_created": False,
        "outbox_entry_created": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "live_write_allowed_now": False
    }


def make_approval_queue_blocked_review_output() -> dict[str, Any]:
    """Generates default blocked review output."""
    return {
        "review_output_status": "BLOCKED_NO_EXACT_PAYLOAD_REVIEW_CREATED",
        "runtime_truth": False,
        "exact_payload_review_performed": False,
        "exact_payload_approval_completed": False,
        "approval_queue_entry_created": False,
        "approval_id_created": False,
        "approval_hash_created": False,
        "payload_hash_created": False,
        "operator_signature_present": False,
        "approval_valid_for_dispatch": False,
        "destination_binding_completed": False,
        "account_binding_completed": False,
        "platform_payloads": [],
        "platform_payload_hashes": [],
        "exact_payload_previews": [],
        "review_records": [],
        "approval_records": [],
        "approval_ledger_entries": [],
        "destination_bindings": [],
        "account_bindings": [],
        "public_urls": [],
        "outbox_entries": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "platform_metrics": [],
        "review_record_count": 0,
        "approval_record_count": 0,
        "payload_hash_count": 0,
        "outbox_entry_count": 0,
        "destination_binding_count": 0,
        "public_url_count": 0,
        "blockers": [
            "platform_variant_approval_packet_missing",
            "rendered_platform_payloads_missing",
            "exact_payload_preview_missing",
            "destination_binding_missing",
            "account_binding_missing",
            "exact_payload_review_blocked",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_approval_queue_review_gate_matrix() -> list[dict[str, Any]]:
    """Generates default blocked review gate matrix rows."""
    platforms = [
        ("substack", "newsletter"),
        ("discord", "chat"),
        ("telegram", "chat"),
        ("x", "social"),
        ("linkedin", "social"),
        ("threads", "social")
    ]
    matrix = []
    for platform, family in platforms:
        matrix.append({
            "platform": platform,
            "platform_family": family,
            "review_gate_status": "blocked_missing_approval_packet_and_payload",
            "platform_variant_approval_packet_available": False,
            "rendered_platform_payload_available": False,
            "exact_payload_preview_available": False,
            "destination_binding_completed": False,
            "account_binding_completed": False,
            "payload_hash_created": False,
            "approval_queue_entry_created": False,
            "approval_id_created": False,
            "approval_hash_created": False,
            "operator_signature_present": False,
            "exact_payload_review_performed": False,
            "exact_payload_approval_completed": False,
            "approval_valid_for_dispatch": False,
            "outbox_entry_created": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "public_url_created": False,
            "valid_for_publication": False,
            "blocks_publication": True,
            "blockers": [
                "platform_variant_approval_packet_missing",
                "rendered_platform_payloads_missing",
                "exact_payload_preview_missing",
                "destination_binding_missing",
                "account_binding_missing",
                "exact_payload_review_blocked",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_approval_queue_review_checklist() -> dict[str, Any]:
    """Generates default blocked review checklist."""
    items = [
        "platform_variant_approval_packet_required",
        "rendered_platform_payloads_required",
        "exact_payload_preview_required",
        "destination_binding_required",
        "account_binding_required",
        "payload_hash_policy_required",
        "approval_policy_required",
        "exact_payload_review_blocked",
        "operator_signature_absent",
        "no_approval_queue_entry_created",
        "no_approval_id_created",
        "no_approval_hash_created",
        "no_payload_hash_created",
        "no_outbox_entry_created",
        "no_publication_ready_claim",
        "no_dispatch_ready_claim",
        "no_financial_advice_language",
        "jim_final_review_required"
    ]
    checklist_items = []
    for item in items:
        checklist_items.append({
            "item_name": item,
            "current_status": "blocked",
            "blocks_exact_payload_review": True,
            "blocks_publication": True,
            "evidence_ref": "approval_queue_exact_payload_review_input_contract.json"
        })

    return {
        "checklist_status": "EXACT_PAYLOAD_REVIEW_BLOCKED_PENDING_APPROVAL_PACKET_AND_PAYLOADS",
        "items": checklist_items
    }


def main(argv: list[str] | None = None) -> int:
    """Executes the coordinator script."""
    parser = argparse.ArgumentParser(description="V6 Approval Queue Exact Payload Review Contract Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = packet_builder.make_approval_queue_exact_payload_review_packet()
    contract = contract_builder.make_approval_queue_exact_payload_review_input_contract()
    template = make_approval_queue_blocked_review_template()
    output = make_approval_queue_blocked_review_output()
    matrix = make_approval_queue_review_gate_matrix()
    checklist = make_approval_queue_review_checklist()

    report, blockers = validator.validate_approval_queue_exact_payload_review_contract(
        packet, contract, template, output, matrix, checklist
    )

    blocker_report_md = "# Approval Queue Exact Payload Review Blocker Report\n\n"
    blocker_report_md += f"Status: **{report['validation_status']}**\n"
    blocker_report_md += f"Active Blocker Count: **{report['blocker_count']}**\n\n"
    blocker_report_md += "## Active Blockers\n\n"
    for b in report["blockers"]:
        blocker_report_md += f"- `{b}`\n"

    runbook_md = (
        "# Approval Queue Exact Payload Review Runbook\n\n"
        "1. Check that platform variant approval packets are available.\n"
        "2. Check that rendered platform payloads are available.\n"
        "3. Check exact payload previews and destination bindings.\n"
        "4. Confirm Jim review and sign the review record.\n"
    )

    impl_report_md = (
        "# Implementation Report - V6 Approval Queue Exact Payload Review Contract\n\n"
        "Offline dry-run approval queue review contract setup completed successfully.\n"
    )

    next_task_pointer_md = (
        "# Recommended Next Task\n\n"
        "TASK_CONTENTOPS_V6_OUTBOX_ENTRY_CONTRACT_DRY_RUN_HEAVY_BATCH_V0\n"
    )

    # Write files
    (out_dir / "approval_queue_exact_payload_review_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_exact_payload_review_input_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_blocked_review_template.json").write_text(json.dumps(template, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_blocked_review_output.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_review_gate_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_review_checklist.json").write_text(json.dumps(checklist, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_review_validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "approval_queue_review_blocker_report.md").write_text(blocker_report_md, encoding="utf-8")
    (out_dir / "approval_queue_review_runbook.md").write_text(runbook_md, encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(impl_report_md, encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
