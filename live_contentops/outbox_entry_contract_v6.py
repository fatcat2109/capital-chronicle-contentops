"""V6 Outbox Entry Contract Coordinator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import outbox_entry_packet_v6 as packet_builder
from live_contentops import outbox_entry_input_contract_v6 as contract_builder
from live_contentops import outbox_entry_validator_v6 as validator

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OUTBOX_ENTRY_CONTRACT")


def make_outbox_entry_blocked_template() -> dict[str, Any]:
    """Generates default blocked outbox template."""
    return {
        "outbox_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_OUTBOX_ENTRY",
        "runtime_truth": False,
        "outbox_entry_id": None,
        "approval_queue_entry_id": None,
        "approval_id": None,
        "approval_hash": None,
        "payload_hash": None,
        "outbox_payload_hash": None,
        "exact_payload_preview_ref": None,
        "platform_payload_manifest_ref": None,
        "destination_binding_ref": None,
        "account_binding_ref": None,
        "dispatch_policy_ref": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "created_at_redacted": None,
        "dispatch_statement": None,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "outbox_entry_creation_allowed": False,
        "dispatch_attempt_created": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "live_write_allowed_now": False
    }


def make_outbox_entry_blocked_output() -> dict[str, Any]:
    """Generates default blocked outbox output."""
    return {
        "outbox_output_status": "BLOCKED_NO_OUTBOX_ENTRY_CREATED",
        "runtime_truth": False,
        "outbox_entry_created": False,
        "outbox_entry_id_created": False,
        "outbox_payload_hash_created": False,
        "dispatch_attempt_created": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "destination_binding_completed": False,
        "account_binding_completed": False,
        "platform_payloads": [],
        "exact_payload_previews": [],
        "platform_payload_hashes": [],
        "outbox_entries": [],
        "outbox_ledger_entries": [],
        "dispatch_attempts": [],
        "destination_bindings": [],
        "account_bindings": [],
        "public_urls": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "platform_metrics": [],
        "outbox_entry_count": 0,
        "dispatch_attempt_count": 0,
        "payload_hash_count": 0,
        "destination_binding_count": 0,
        "public_url_count": 0,
        "blockers": [
            "approved_exact_payload_review_missing",
            "rendered_platform_payloads_missing",
            "payload_hash_missing",
            "destination_binding_missing",
            "account_binding_missing",
            "outbox_entry_creation_blocked",
            "dispatch_authorization_missing",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_outbox_entry_gate_matrix() -> list[dict[str, Any]]:
    """Generates default blocked outbox gate matrix rows."""
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
            "outbox_gate_status": "blocked_missing_approved_payload_and_destination",
            "approved_exact_payload_review_available": False,
            "rendered_platform_payload_available": False,
            "exact_payload_preview_available": False,
            "payload_hash_available": False,
            "destination_binding_completed": False,
            "account_binding_completed": False,
            "approval_id_available": False,
            "approval_hash_available": False,
            "approval_valid_for_dispatch": False,
            "outbox_entry_creation_allowed": False,
            "outbox_entry_created": False,
            "outbox_entry_id_created": False,
            "dispatch_attempt_created": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "platform_api_request_performed": False,
            "webhook_request_performed": False,
            "public_url_created": False,
            "valid_for_publication": False,
            "blocks_publication": True,
            "blockers": [
                "approved_exact_payload_review_missing",
                "rendered_platform_payloads_missing",
                "payload_hash_missing",
                "destination_binding_missing",
                "account_binding_missing",
                "outbox_entry_creation_blocked",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_outbox_entry_checklist() -> dict[str, Any]:
    """Generates default blocked outbox checklist."""
    items = [
        "approved_exact_payload_review_required",
        "rendered_platform_payloads_required",
        "exact_payload_preview_required",
        "payload_hash_required",
        "destination_binding_required",
        "account_binding_required",
        "approval_id_required",
        "approval_hash_required",
        "dispatch_policy_required",
        "outbox_entry_creation_blocked",
        "dispatch_authorization_missing",
        "no_outbox_entry_id_created",
        "no_outbox_payload_hash_created",
        "no_dispatch_attempt_created",
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
            "blocks_outbox_entry_creation": True,
            "blocks_publication": True,
            "evidence_ref": "outbox_entry_input_contract.json"
        })

    return {
        "checklist_status": "OUTBOX_ENTRY_BLOCKED_PENDING_APPROVED_PAYLOAD_AND_DESTINATION",
        "items": checklist_items
    }


def main(argv: list[str] | None = None) -> int:
    """Executes the coordinator script."""
    parser = argparse.ArgumentParser(description="V6 Outbox Entry Contract Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = packet_builder.make_outbox_entry_packet()
    contract = contract_builder.make_outbox_entry_input_contract()
    template = make_outbox_entry_blocked_template()
    output = make_outbox_entry_blocked_output()
    matrix = make_outbox_entry_gate_matrix()
    checklist = make_outbox_entry_checklist()

    report, blockers = validator.validate_outbox_entry_contract(
        packet, contract, template, output, matrix, checklist
    )

    blocker_report_md = "# Outbox Entry Blocker Report\n\n"
    blocker_report_md += f"Status: **{report['validation_status']}**\n"
    blocker_report_md += f"Active Blocker Count: **{report['blocker_count']}**\n\n"
    blocker_report_md += "## Active Blockers\n\n"
    for b in report["blockers"]:
        blocker_report_md += f"- `{b}`\n"

    runbook_md = (
        "# Outbox Entry Runbook\n\n"
        "1. Check that approved exact payload reviews are available.\n"
        "2. Confirm payload hashes and destination bindings.\n"
        "3. Bind account/destination and request dispatch authorization.\n"
        "4. Obtain Jim final review and record dispatch statements.\n"
    )

    impl_report_md = (
        "# Implementation Report - V6 Outbox Entry Contract\n\n"
        "Offline dry-run outbox entry contract setup completed successfully.\n"
    )

    next_task_pointer_md = (
        "# Recommended Next Task\n\n"
        "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_CONTRACT_DRY_RUN_HEAVY_BATCH_V0\n"
    )

    # Write files
    (out_dir / "outbox_entry_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_input_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_blocked_template.json").write_text(json.dumps(template, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_blocked_output.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_gate_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_checklist.json").write_text(json.dumps(checklist, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "outbox_entry_blocker_report.md").write_text(blocker_report_md, encoding="utf-8")
    (out_dir / "outbox_entry_runbook.md").write_text(runbook_md, encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(impl_report_md, encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
