"""V6 Platform Variant Approval Packet Contract Coordinator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_variant_approval_packet_v6 as packet_builder
from live_contentops import platform_variant_approval_input_contract_v6 as contract_builder
from live_contentops import platform_variant_approval_validator_v6 as validator

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_VARIANT_APPROVAL_PACKET_CONTRACT")


def make_platform_variant_blocked_approval_template() -> dict[str, Any]:
    """Generates default blocked approval template."""
    return {
        "approval_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_APPROVAL",
        "runtime_truth": False,
        "approval_id": None,
        "approval_hash": None,
        "payload_hash": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "approved_at_redacted": None,
        "destination_binding_ref": None,
        "account_binding_ref": None,
        "platform_payload_manifest_ref": None,
        "approval_statement": None,
        "approval_valid_for_dispatch": False,
        "approval_packet_created": False,
        "exact_payload_approval_completed": False,
        "outbox_entry_created": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "live_write_allowed_now": False
    }


def make_blocked_platform_variant_approval_output() -> dict[str, Any]:
    """Generates default blocked approval output."""
    return {
        "approval_output_status": "BLOCKED_NO_APPROVAL_PACKET_CREATED",
        "runtime_truth": False,
        "approval_packet_created": False,
        "approval_id_created": False,
        "approval_hash_created": False,
        "payload_hash_created": False,
        "operator_signature_present": False,
        "approval_valid_for_dispatch": False,
        "exact_payload_approval_completed": False,
        "destination_binding_completed": False,
        "account_binding_completed": False,
        "platform_payloads": [],
        "platform_payload_hashes": [],
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
        "approval_record_count": 0,
        "payload_hash_count": 0,
        "outbox_entry_count": 0,
        "destination_binding_count": 0,
        "public_url_count": 0,
        "blockers": [
            "rendered_platform_variants_missing",
            "exact_payload_preview_missing",
            "destination_binding_missing",
            "account_binding_missing",
            "approval_packet_creation_blocked",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_platform_variant_approval_gate_matrix() -> list[dict[str, Any]]:
    """Generates default blocked approval gate matrix rows."""
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
            "approval_gate_status": "blocked_missing_rendered_payload_and_destination",
            "rendered_platform_variant_available": False,
            "exact_payload_preview_available": False,
            "destination_binding_completed": False,
            "account_binding_completed": False,
            "payload_hash_created": False,
            "approval_packet_created": False,
            "approval_hash_created": False,
            "operator_signature_present": False,
            "exact_payload_approval_completed": False,
            "approval_valid_for_dispatch": False,
            "outbox_entry_created": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "public_url_created": False,
            "valid_for_publication": False,
            "blocks_publication": True,
            "blockers": [
                "rendered_platform_variants_missing",
                "exact_payload_preview_missing",
                "destination_binding_missing",
                "account_binding_missing",
                "approval_packet_creation_blocked",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_platform_variant_approval_checklist() -> dict[str, Any]:
    """Generates default blocked approval checklist."""
    items = [
        "rendered_platform_variants_required",
        "exact_payload_preview_required",
        "destination_binding_required",
        "account_binding_required",
        "payload_hash_policy_required",
        "approval_policy_required",
        "operator_signature_absent",
        "approval_packet_creation_blocked",
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
            "blocks_approval_packet_creation": True,
            "blocks_publication": True,
            "evidence_ref": "platform_variant_approval_input_contract.json"
        })

    return {
        "checklist_status": "APPROVAL_PACKET_CONTRACT_BLOCKED_PENDING_RENDERED_PAYLOADS",
        "items": checklist_items
    }


def main(argv: list[str] | None = None) -> int:
    """Executes the coordinator script."""
    parser = argparse.ArgumentParser(description="V6 Platform Variant Approval Packet Contract Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = packet_builder.make_platform_variant_approval_packet()
    contract = contract_builder.make_platform_variant_approval_input_contract()
    template = make_platform_variant_blocked_approval_template()
    output = make_blocked_platform_variant_approval_output()
    matrix = make_platform_variant_approval_gate_matrix()
    checklist = make_platform_variant_approval_checklist()

    report, blockers = validator.validate_platform_variant_approval_packet_contract(
        packet, contract, template, output, matrix, checklist
    )

    blocker_report_md = "# Platform Variant Approval Packet Blocker Report\n\n"
    blocker_report_md += f"Status: **{report['validation_status']}**\n"
    blocker_report_md += f"Active Blocker Count: **{report['blocker_count']}**\n\n"
    blocker_report_md += "## Active Blockers\n\n"
    for b in report["blockers"]:
        blocker_report_md += f"- `{b}`\n"

    runbook_md = (
        "# Platform Variant Approval Packet Contract Runbook\n\n"
        "1. Check that rendered platform variants are available.\n"
        "2. Check that exact payload preview is created.\n"
        "3. Bind destinations and accounts.\n"
        "4. Confirm Jim review and sign the approval payload.\n"
    )

    impl_report_md = (
        "# Implementation Report - V6 Platform Variant Approval Packet Contract\n\n"
        "Offline dry-run approval contract setup completed successfully.\n"
    )

    next_task_pointer_md = (
        "# Recommended Next Task\n\n"
        "TASK_CONTENTOPS_V6_APPROVAL_QUEUE_EXACT_PAYLOAD_REVIEW_CONTRACT_DRY_RUN_HEAVY_BATCH_V0\n"
    )

    # Write files
    (out_dir / "platform_variant_approval_contract_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_approval_input_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_blocked_approval_template.json").write_text(json.dumps(template, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_blocked_approval_output.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_approval_gate_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_approval_checklist.json").write_text(json.dumps(checklist, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_approval_validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "platform_variant_approval_blocker_report.md").write_text(blocker_report_md, encoding="utf-8")
    (out_dir / "platform_variant_approval_runbook.md").write_text(runbook_md, encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(impl_report_md, encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
