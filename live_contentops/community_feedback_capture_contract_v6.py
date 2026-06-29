"""V6 Community Feedback Capture Contract Coordinator.

Generates default artifacts for community feedback capture contract dry-run lane.
"""
from __future__ import annotations

import json
import os
from typing import Any

from live_contentops.community_feedback_capture_packet_v6 import make_community_feedback_capture_packet
from live_contentops.community_feedback_capture_input_contract_v6 import make_community_feedback_capture_input_contract
from live_contentops.community_feedback_capture_validator_v6 import validate_community_feedback_capture_contract


def make_community_feedback_capture_blocked_template() -> dict[str, Any]:
    """Generates the default blocked feedback template."""
    return {
        "feedback_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_FEEDBACK_CAPTURE",
        "runtime_truth": False,
        "feedback_capture_id": None,
        "audit_record_id": None,
        "public_url": None,
        "public_url_proof_ref": None,
        "platform_publication_id": None,
        "feedback_source_binding_ref": None,
        "community_channel_binding_ref": None,
        "destination_binding_ref": None,
        "account_binding_ref": None,
        "feedback_capture_policy_ref": None,
        "audit_redaction_policy_ref": None,
        "request_payload_ref": None,
        "response_payload_ref": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "captured_at_redacted": None,
        "feedback_capture_statement": None,
        "feedback_capture_performed": False,
        "comment_capture_performed": False,
        "reaction_capture_performed": False,
        "metric_capture_performed": False,
        "feedback_summary_created": False,
        "backlog_item_created": False,
        "audit_record_mutated": False
    }


def make_community_feedback_capture_blocked_output() -> dict[str, Any]:
    """Generates the default blocked feedback output."""
    return {
        "feedback_output_status": "BLOCKED_NO_COMMUNITY_FEEDBACK_CAPTURE_CREATED",
        "runtime_truth": False,
        "feedback_capture_performed": False,
        "comment_capture_performed": False,
        "reaction_capture_performed": False,
        "metric_capture_performed": False,
        "feedback_summary_created": False,
        "backlog_item_created": False,
        "audit_record_mutated": False,
        "public_url_created": False,
        "feedback_records": [],
        "comments": [],
        "reactions": [],
        "platform_metrics": [],
        "feedback_summaries": [],
        "backlog_items": [],
        "public_urls": [],
        "public_url_proofs": [],
        "platform_publication_ids": [],
        "community_channel_bindings": [],
        "feedback_source_bindings": [],
        "destination_bindings": [],
        "account_bindings": [],
        "credential_refs": [],
        "endpoint_refs": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "user_handles": [],
        "private_messages": [],
        "feedback_record_count": 0,
        "comment_count": 0,
        "reaction_count": 0,
        "metric_count": 0,
        "backlog_item_count": 0,
        "blockers": [
            "publication_audit_record_missing",
            "publication_confirmation_missing",
            "public_url_proof_missing",
            "platform_publication_id_missing",
            "feedback_capture_policy_missing",
            "feedback_source_binding_missing",
            "community_channel_binding_missing",
            "feedback_capture_blocked",
            "jim_feedback_review_required",
            "audit_mutation_blocked"
        ]
    }


def make_community_feedback_capture_gate_matrix() -> list[dict[str, Any]]:
    """Generates the feedback gate matrix."""
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
            "feedback_gate_status": "blocked_missing_publication_audit_and_feedback_source_binding",
            "publication_audit_record_available": False,
            "publication_confirmed": False,
            "public_url_proof_available": False,
            "platform_publication_id_available": False,
            "destination_binding_completed": False,
            "account_binding_completed": False,
            "feedback_capture_policy_available": False,
            "feedback_source_binding_completed": False,
            "community_channel_binding_completed": False,
            "operator_feedback_capture_authorization_present": False,
            "jim_feedback_review_completed": False,
            "feedback_capture_allowed": False,
            "feedback_capture_performed": False,
            "comment_capture_performed": False,
            "reaction_capture_performed": False,
            "metric_capture_performed": False,
            "feedback_summary_created": False,
            "backlog_item_created": False,
            "audit_record_mutation_allowed": False,
            "audit_record_mutated": False,
            "provider_call_performed": False,
            "browser_session_started": False,
            "env_read_performed": False,
            "credentials_hydrated": False,
            "platform_api_request_performed": False,
            "webhook_request_performed": False,
            "scraping_performed": False,
            "live_write_attempted": False,
            "retry_attempted": False,
            "public_url_created": False,
            "blocks_publication": True,
            "blockers": [
                "publication_audit_record_missing",
                "publication_confirmation_missing",
                "public_url_proof_missing",
                "platform_publication_id_missing",
                "feedback_capture_policy_missing",
                "feedback_source_binding_missing",
                "community_channel_binding_missing",
                "feedback_capture_blocked",
                "jim_feedback_review_required",
                "audit_mutation_blocked"
            ]
        })
    return matrix


def make_community_feedback_capture_checklist() -> dict[str, Any]:
    """Generates the feedback checklist."""
    items = [
        "publication_audit_record_required",
        "publication_confirmation_required",
        "public_url_proof_required",
        "platform_publication_id_required",
        "feedback_capture_policy_required",
        "feedback_source_binding_required",
        "community_channel_binding_required",
        "operator_feedback_capture_authorization_required",
        "jim_feedback_review_required",
        "feedback_capture_blocked",
        "no_comment_capture_performed",
        "no_reaction_capture_performed",
        "no_metric_capture_performed",
        "no_feedback_summary_created",
        "no_backlog_item_created",
        "no_audit_record_mutated",
        "no_public_url_created",
        "no_publication_ready_claim",
        "no_financial_advice_language"
    ]
    checklist_items = []
    for item in items:
        checklist_items.append({
            "item_name": item,
            "current_status": "blocked",
            "blocks_community_feedback_capture": True,
            "blocks_publication": True,
            "evidence_ref": "community_feedback_capture_input_contract.json"
        })

    return {
        "checklist_status": "COMMUNITY_FEEDBACK_CAPTURE_BLOCKED_PENDING_PUBLICATION_AUDIT_AND_SOURCE_BINDING",
        "items": checklist_items
    }


def main() -> None:
    """Coordinator entry point to generate artifacts."""
    packet = make_community_feedback_capture_packet()
    contract = make_community_feedback_capture_input_contract()
    template = make_community_feedback_capture_blocked_template()
    output = make_community_feedback_capture_blocked_output()
    matrix = make_community_feedback_capture_gate_matrix()
    checklist = make_community_feedback_capture_checklist()

    report, blockers = validate_community_feedback_capture_contract(
        packet, contract, template, output, matrix, checklist
    )

    out_dir = "docs/automation/V6_COMMUNITY_FEEDBACK_CAPTURE_CONTRACT"
    os.makedirs(out_dir, exist_ok=True)

    def write_json(filename: str, data: Any) -> None:
        with open(os.path.join(out_dir, filename), "w") as f:
            json.dump(data, f, indent=2)

    write_json("community_feedback_capture_packet.json", packet)
    write_json("community_feedback_capture_input_contract.json", contract)
    write_json("community_feedback_capture_blocked_template.json", template)
    write_json("community_feedback_capture_blocked_output.json", output)
    write_json("community_feedback_capture_gate_matrix.json", matrix)
    write_json("community_feedback_capture_checklist.json", checklist)
    write_json("community_feedback_capture_validation_report.json", report)

    # Write blocker report markdown
    blocker_lines = [f"- {b}" for b in blockers]
    blocker_report_md = f"""# V6 Community Feedback Capture Blocker Report

The following is the active blocker checklist for the browserless dry-run community feedback capture lane.

## Blocker Counts
- **Total Blockers**: {len(blockers)}
- **Validation Status**: {report['validation_status']}

## Blockers List
{os.linesep.join(blocker_lines)}
"""
    with open(os.path.join(out_dir, "community_feedback_capture_blocker_report.md"), "w") as f:
        f.write(blocker_report_md)

    # Write runbook markdown
    runbook_md = """# V6 Community Feedback Capture Runbook

This runbook guides operators on dealing with a blocked community feedback capture contract.

## Overview
The V6 Community Feedback Capture Contract protects target communities by blocking capture until:
1. Publication audit record is verified.
2. Feedback capture policy and authorized bindings exist.
3. Explicit operator/Jim review is completed.

## Resolution
If this lane blocks:
- Confirm that the publication audit record contract validation report is clean.
- Verify that community source bindings are fully verified.
- Confirm capture policy is correctly staged in dry-run mode.
"""
    with open(os.path.join(out_dir, "community_feedback_capture_runbook.md"), "w") as f:
        f.write(runbook_md)

    # Write implementation report markdown
    impl_report_md = f"""# V6 Community Feedback Capture Implementation Report

- **Task Label**: TASK_CONTENTOPS_V6_COMMUNITY_FEEDBACK_CAPTURE_CONTRACT_DRY_RUN_HEAVY_BATCH_V0
- **Validation Status**: {report['validation_status']}
- **Blockers**: {len(blockers)}
"""
    with open(os.path.join(out_dir, "implementation_report.md"), "w") as f:
        f.write(impl_report_md)

    # Write next task pointer markdown
    next_task_md = """# Next Recommended Task Pointer

The next task in the V6 loop mapping is:
`TASK_CONTENTOPS_V6_FEEDBACK_SUMMARY_BACKLOG_CONTRACT_DRY_RUN_HEAVY_BATCH_V0`
"""
    with open(os.path.join(out_dir, "next_task_pointer.md"), "w") as f:
        f.write(next_task_md)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
