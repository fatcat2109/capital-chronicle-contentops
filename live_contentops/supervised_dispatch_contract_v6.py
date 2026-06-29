"""V6 Supervised Dispatch Contract Coordinator.

Generates default artifacts for supervised dispatch contract dry-run lane.
"""
from __future__ import annotations

import json
import os
from typing import Any

from live_contentops.supervised_dispatch_packet_v6 import make_supervised_dispatch_packet
from live_contentops.supervised_dispatch_input_contract_v6 import make_supervised_dispatch_input_contract
from live_contentops.supervised_dispatch_validator_v6 import validate_supervised_dispatch_contract


def make_supervised_dispatch_blocked_template() -> dict[str, Any]:
    """Generates the default blocked dispatch template."""
    return {
        "dispatch_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_DISPATCH",
        "runtime_truth": False,
        "dispatch_attempt_id": None,
        "outbox_entry_id": None,
        "approval_id": None,
        "approval_hash": None,
        "payload_hash": None,
        "destination_binding_ref": None,
        "account_binding_ref": None,
        "platform_endpoint_ref": None,
        "credential_scope_ref": None,
        "request_payload_ref": None,
        "response_ref": None,
        "public_url": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "dispatched_at_redacted": None,
        "dispatch_statement": None,
        "dispatch_preflight_performed": False,
        "dispatch_attempt_created": False,
        "dispatch_request_sent": False,
        "live_write_attempted": False,
        "retry_attempted": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "live_write_allowed_now": False
    }


def make_supervised_dispatch_blocked_output() -> dict[str, Any]:
    """Generates the default blocked dispatch output."""
    return {
        "dispatch_output_status": "BLOCKED_NO_DISPATCH_ATTEMPT_CREATED",
        "runtime_truth": False,
        "dispatch_preflight_performed": False,
        "dispatch_attempt_created": False,
        "dispatch_request_prepared": False,
        "dispatch_request_sent": False,
        "live_write_attempted": False,
        "retry_attempted": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "public_url_created": False,
        "public_postable": False,
        "platform_payloads": [],
        "request_payloads": [],
        "response_payloads": [],
        "dispatch_attempts": [],
        "dispatch_ledger_entries": [],
        "public_urls": [],
        "destination_bindings": [],
        "account_bindings": [],
        "credential_refs": [],
        "endpoint_refs": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "platform_metrics": [],
        "dispatch_attempt_count": 0,
        "request_payload_count": 0,
        "response_payload_count": 0,
        "public_url_count": 0,
        "retry_attempt_count": 0,
        "blockers": [
            "valid_outbox_entry_missing",
            "approved_exact_payload_review_missing",
            "payload_hash_missing",
            "destination_binding_missing",
            "account_binding_missing",
            "credential_scope_proof_missing",
            "platform_endpoint_allowlist_missing",
            "kill_switch_active",
            "dispatch_authorization_missing",
            "dispatch_blocked"
        ]
    }


def make_supervised_dispatch_gate_matrix() -> list[dict[str, Any]]:
    """Generates the platform dispatch gate matrix."""
    platforms = [
        ("substack", "email_newsletter"),
        ("discord", "chat_community"),
        ("telegram", "broadcast_channel"),
        ("x", "social_microblog"),
        ("linkedin", "professional_network"),
        ("threads", "social_network")
    ]
    matrix = []
    for platform, family in platforms:
        matrix.append({
            "platform": platform,
            "platform_family": family,
            "dispatch_gate_status": "blocked_missing_outbox_authorization_and_kill_switch",
            "valid_outbox_entry_available": False,
            "approved_exact_payload_review_available": False,
            "payload_hash_available": False,
            "destination_binding_completed": False,
            "account_binding_completed": False,
            "credential_scope_proof_available": False,
            "platform_endpoint_allowlist_available": False,
            "kill_switch_open": False,
            "operator_dispatch_authorization_present": False,
            "jim_dispatch_authorization_present": False,
            "dispatch_preflight_allowed": False,
            "dispatch_preflight_performed": False,
            "dispatch_attempt_allowed": False,
            "dispatch_attempt_created": False,
            "dispatch_request_sent": False,
            "live_write_attempted": False,
            "retry_attempted": False,
            "platform_api_request_performed": False,
            "webhook_request_performed": False,
            "public_url_created": False,
            "valid_for_publication": False,
            "dispatch_allowed_now": False,
            "live_write_allowed_now": False,
            "blocks_publication": True,
            "blockers": [
                "valid_outbox_entry_missing",
                "approved_exact_payload_review_missing",
                "payload_hash_missing",
                "destination_binding_missing",
                "account_binding_missing",
                "credential_scope_proof_missing",
                "platform_endpoint_allowlist_missing",
                "kill_switch_active",
                "dispatch_authorization_missing",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_supervised_dispatch_checklist() -> dict[str, Any]:
    """Generates the supervised dispatch checklist."""
    items = [
        "valid_outbox_entry_required",
        "approved_exact_payload_review_required",
        "payload_hash_required",
        "destination_binding_required",
        "account_binding_required",
        "dispatch_policy_required",
        "credential_scope_proof_required",
        "platform_endpoint_allowlist_required",
        "kill_switch_must_be_open",
        "operator_dispatch_authorization_required",
        "jim_dispatch_authorization_required",
        "dispatch_preflight_blocked",
        "no_dispatch_attempt_created",
        "no_live_write_attempted",
        "no_retry_attempted",
        "no_public_url_created",
        "no_publication_ready_claim",
        "no_dispatch_ready_claim",
        "no_financial_advice_language"
    ]
    checklist_items = []
    for item in items:
        checklist_items.append({
            "item_name": item,
            "current_status": "blocked",
            "blocks_supervised_dispatch": True,
            "blocks_publication": True,
            "evidence_ref": "supervised_dispatch_input_contract.json"
        })

    return {
        "checklist_status": "SUPERVISED_DISPATCH_BLOCKED_PENDING_OUTBOX_AUTHORIZATION_AND_KILL_SWITCH",
        "items": checklist_items
    }


def main() -> None:
    """Coordinator entry point to generate artifacts."""
    packet = make_supervised_dispatch_packet()
    contract = make_supervised_dispatch_input_contract()
    template = make_supervised_dispatch_blocked_template()
    output = make_supervised_dispatch_blocked_output()
    matrix = make_supervised_dispatch_gate_matrix()
    checklist = make_supervised_dispatch_checklist()

    report, blockers = validate_supervised_dispatch_contract(
        packet, contract, template, output, matrix, checklist
    )

    out_dir = "docs/automation/V6_SUPERVISED_DISPATCH_CONTRACT"
    os.makedirs(out_dir, exist_ok=True)

    def write_json(filename: str, data: Any) -> None:
        with open(os.path.join(out_dir, filename), "w") as f:
            json.dump(data, f, indent=2)

    write_json("supervised_dispatch_packet.json", packet)
    write_json("supervised_dispatch_input_contract.json", contract)
    write_json("supervised_dispatch_blocked_template.json", template)
    write_json("supervised_dispatch_blocked_output.json", output)
    write_json("supervised_dispatch_gate_matrix.json", matrix)
    write_json("supervised_dispatch_checklist.json", checklist)
    write_json("supervised_dispatch_validation_report.json", report)

    # Write blocker report markdown
    blocker_lines = [f"- {b}" for b in blockers]
    blocker_report_md = f"""# V6 Supervised Dispatch Blocker Report

The following is the active blocker checklist for the browserless dry-run supervised dispatch lane.

## Blocker Counts
- **Total Blockers**: {len(blockers)}
- **Validation Status**: {report['validation_status']}

## Blockers List
{os.linesep.join(blocker_lines)}
"""
    with open(os.path.join(out_dir, "supervised_dispatch_blocker_report.md"), "w") as f:
        f.write(blocker_report_md)

    # Write runbook markdown
    runbook_md = """# V6 Supervised Dispatch Runbook

This runbook guides operators on dealing with a blocked supervised dispatch contract.

## Overview
The V6 Supervised Dispatch Contract protects target platforms by blocking dispatch until:
1. A valid outbox entry is created.
2. Credentials and endpoint allowlists stage properly.
3. Operator and Jim dispatch approvals are signed and verified.
4. The global kill-switch is verified open.

## Resolution
If this lane blocks:
- Confirm that the outbox entry contract validation report is clean.
- Verify that credentials and token proofs are fully staged in dry-run mode.
- Trigger explicit operator dispatch authorization flags.
"""
    with open(os.path.join(out_dir, "supervised_dispatch_runbook.md"), "w") as f:
        f.write(runbook_md)

    # Write implementation report markdown
    impl_report_md = f"""# V6 Supervised Dispatch Implementation Report

- **Task Label**: TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_CONTRACT_DRY_RUN_HEAVY_BATCH_V0
- **Validation Status**: {report['validation_status']}
- **Blockers**: {len(blockers)}
"""
    with open(os.path.join(out_dir, "implementation_report.md"), "w") as f:
        f.write(impl_report_md)

    # Write next task pointer markdown
    next_task_md = """# Next Recommended Task Pointer

The next task in the V6 loop mapping is:
`TASK_CONTENTOPS_V6_PUBLICATION_AUDIT_RECORD_CONTRACT_DRY_RUN_HEAVY_BATCH_V0`
"""
    with open(os.path.join(out_dir, "next_task_pointer.md"), "w") as f:
        f.write(next_task_md)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
