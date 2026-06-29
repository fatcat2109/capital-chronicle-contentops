"""V6 Next Article Planning From Feedback Contract Coordinator.

Generates default artifacts for next article planning from feedback contract dry-run lane.
"""
from __future__ import annotations

import json
import os
from typing import Any

from live_contentops.next_article_planning_from_feedback_packet_v6 import make_next_article_planning_from_feedback_packet
from live_contentops.next_article_planning_from_feedback_input_contract_v6 import make_next_article_planning_from_feedback_input_contract
from live_contentops.next_article_planning_from_feedback_validator_v6 import validate_next_article_planning_from_feedback_contract


def make_next_article_planning_blocked_template() -> dict[str, Any]:
    """Generates the default blocked next article planning template."""
    return {
        "feedback_template_status": "BLOCKED_TEMPLATE_ONLY_NOT_NEXT_ARTICLE_PLANNING",
        "runtime_truth": False,
        "article_planning_id": None,
        "article_idea_id": None,
        "research_question_id": None,
        "source_pack_request_id": None,
        "canonical_draft_request_id": None,
        "feedback_summary_backlog_ref": None,
        "feedback_summary_ref": None,
        "backlog_items_ref": None,
        "next_article_signals_ref": None,
        "redacted_feedback_records_ref": None,
        "public_url_proof_ref": None,
        "platform_publication_id_ref": None,
        "planning_policy_ref": None,
        "source_research_policy_ref": None,
        "audit_redaction_policy_ref": None,
        "operator_id_redacted": None,
        "operator_signature_redacted": None,
        "created_at_redacted": None,
        "article_idea_statement": None,
        "research_question_statement": None,
        "source_pack_request_statement": None,
        "canonical_draft_request_statement": None,
        "article_planning_performed": False,
        "article_idea_created": False,
        "research_question_created": False,
        "source_pack_request_created": False,
        "canonical_draft_requested": False,
        "audit_record_mutated": False
    }


def make_next_article_planning_blocked_output() -> dict[str, Any]:
    """Generates the default blocked next article planning output."""
    return {
        "feedback_output_status": "BLOCKED_NO_NEXT_ARTICLE_PLANNING_CREATED",
        "runtime_truth": False,
        "article_planning_performed": False,
        "article_idea_created": False,
        "research_question_created": False,
        "source_pack_request_created": False,
        "canonical_draft_requested": False,
        "audit_record_mutated": False,
        "public_url_created": False,
        "article_ideas": [],
        "research_questions": [],
        "source_pack_requests": [],
        "canonical_draft_requests": [],
        "feedback_summaries": [],
        "backlog_items": [],
        "next_article_signals": [],
        "redacted_feedback_records": [],
        "public_urls": [],
        "public_url_proofs": [],
        "platform_publication_ids": [],
        "citations": [],
        "evidence_refs": [],
        "source_names": [],
        "request_payloads": [],
        "response_payloads": [],
        "article_idea_count": 0,
        "research_question_count": 0,
        "source_pack_request_count": 0,
        "canonical_draft_request_count": 0,
        "feedback_summary_count": 0,
        "backlog_item_count": 0,
        "next_article_signal_count": 0,
        "redacted_record_count": 0,
        "blockers": [
            "feedback_summary_backlog_missing",
            "feedback_summary_missing",
            "backlog_items_missing",
            "next_article_signals_missing",
            "planning_policy_missing",
            "source_research_policy_missing",
            "next_article_planning_blocked",
            "source_pack_request_blocked",
            "jim_planning_review_required",
            "audit_mutation_blocked",
            "human_review_required"
        ]
    }


def make_next_article_planning_gate_matrix() -> list[dict[str, Any]]:
    """Generates the next article planning gate matrix."""
    domains = [
        "article_idea_planning",
        "research_question_planning",
        "source_pack_request_planning",
        "canonical_draft_request_planning"
    ]
    matrix = []
    for domain in domains:
        matrix.append({
            "gate_domain": domain,
            "planning_gate_status": "blocked_missing_feedback_summary_and_planning_policy",
            "feedback_summary_available": False,
            "backlog_items_available": False,
            "next_article_signals_available": False,
            "redacted_feedback_records_available": False,
            "public_url_proof_available": False,
            "platform_publication_id_available": False,
            "planning_policy_available": False,
            "source_research_policy_available": False,
            "operator_planning_authorization_present": False,
            "jim_planning_review_completed": False,
            "article_planning_allowed": False,
            "article_planning_performed": False,
            "article_idea_created": False,
            "research_question_created": False,
            "source_pack_request_created": False,
            "canonical_draft_requested": False,
            "model_provider_call_performed": False,
            "provider_call_performed": False,
            "browser_session_started": False,
            "env_read_performed": False,
            "credentials_hydrated": False,
            "platform_api_request_performed": False,
            "webhook_request_performed": False,
            "scraping_performed": False,
            "audit_record_mutated": False,
            "live_write_attempted": False,
            "retry_attempted": False,
            "public_url_created": False,
            "blocks_publication": True,
            "blockers": [
                "feedback_summary_backlog_missing",
                "feedback_summary_missing",
                "backlog_items_missing",
                "next_article_signals_missing",
                "planning_policy_missing",
                "source_research_policy_missing",
                "next_article_planning_blocked",
                "source_pack_request_blocked",
                "jim_planning_review_required",
                "audit_mutation_blocked"
            ]
        })
    return matrix


def make_next_article_planning_checklist() -> dict[str, Any]:
    """Generates the next article planning checklist."""
    items = [
        "feedback_summary_backlog_required",
        "feedback_summary_required",
        "backlog_items_required",
        "next_article_signals_required",
        "redacted_feedback_records_required",
        "public_url_proof_required",
        "platform_publication_id_required",
        "planning_policy_required",
        "source_research_policy_required",
        "operator_planning_authorization_required",
        "jim_planning_review_required",
        "next_article_planning_blocked",
        "source_pack_request_blocked",
        "no_article_ideas_created",
        "no_research_questions_created",
        "no_source_pack_requests_created",
        "no_canonical_draft_requests_created",
        "no_feedback_summaries_created",
        "no_backlog_items_created",
        "no_next_article_signals_created",
        "no_redacted_feedback_records_created",
        "no_public_url_created",
        "no_publication_ready_claim",
        "no_financial_advice_language"
    ]
    checklist_items = []
    for item in items:
        checklist_items.append({
            "item_name": item,
            "current_status": "blocked",
            "blocks_next_article_planning": True,
            "blocks_publication": True,
            "evidence_ref": "next_article_planning_from_feedback_input_contract.json"
        })

    return {
        "checklist_status": "NEXT_ARTICLE_PLANNING_BLOCKED_PENDING_FEEDBACK_SUMMARY_AND_PLANNING_POLICY",
        "items": checklist_items
    }


def main() -> None:
    """Coordinator entry point to generate artifacts."""
    packet = make_next_article_planning_from_feedback_packet()
    contract = make_next_article_planning_from_feedback_input_contract()
    template = make_next_article_planning_blocked_template()
    output = make_next_article_planning_blocked_output()
    matrix = make_next_article_planning_gate_matrix()
    checklist = make_next_article_planning_checklist()

    report, blockers = validate_next_article_planning_from_feedback_contract(
        packet, contract, template, output, matrix, checklist
    )

    out_dir = "docs/automation/V6_NEXT_ARTICLE_PLANNING_FROM_FEEDBACK_CONTRACT"
    os.makedirs(out_dir, exist_ok=True)

    def write_json(filename: str, data: Any) -> None:
        with open(os.path.join(out_dir, filename), "w") as f:
            json.dump(data, f, indent=2)

    write_json("next_article_planning_from_feedback_packet.json", packet)
    write_json("next_article_planning_from_feedback_input_contract.json", contract)
    write_json("next_article_planning_blocked_template.json", template)
    write_json("next_article_planning_blocked_output.json", output)
    write_json("next_article_planning_gate_matrix.json", matrix)
    write_json("next_article_planning_checklist.json", checklist)
    write_json("next_article_planning_validation_report.json", report)

    # Write blocker report markdown
    blocker_lines = [f"- {b}" for b in blockers]
    blocker_report_md = f"""# V6 Next Article Planning Blocker Report

The following is the active blocker checklist for the browserless dry-run next article planning lane.

## Blocker Counts
- **Total Blockers**: {len(blockers)}
- **Validation Status**: {report['validation_status']}

## Blockers List
{os.linesep.join(blocker_lines)}
"""
    with open(os.path.join(out_dir, "next_article_planning_blocker_report.md"), "w") as f:
        f.write(blocker_report_md)

    # Write runbook markdown
    runbook_md = """# V6 Next Article Planning Runbook

This runbook guides operators on dealing with a blocked next article planning contract.

## Overview
The V6 Next Article Planning Contract protects target communities by blocking planning generation until:
1. Feedback summary backlog contract is verified.
2. Policies and authorized bindings exist.
3. Explicit operator/Jim review is completed.

## Resolution
If this lane blocks:
- Confirm that the feedback summary backlog contract validation report is clean.
- Verify that planning and source research policies are fully verified.
- Confirm template is correctly staged in dry-run mode.
"""
    with open(os.path.join(out_dir, "next_article_planning_runbook.md"), "w") as f:
        f.write(runbook_md)

    # Write implementation report markdown
    impl_report_md = f"""# V6 Next Article Planning Implementation Report

- **Task Label**: TASK_CONTENTOPS_V6_NEXT_ARTICLE_PLANNING_PACKET_FROM_FEEDBACK_CONTRACT_DRY_RUN_HEAVY_BATCH_V0
- **Validation Status**: {report['validation_status']}
- **Blockers**: {len(blockers)}
"""
    with open(os.path.join(out_dir, "implementation_report.md"), "w") as f:
        f.write(impl_report_md)

    # Write next task pointer markdown
    next_task_md = """# Next Recommended Task Pointer

The next task in the V6 loop mapping is:
`TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_AND_UPLOAD_BUNDLE_AFTER_V6_LOOP_CONTRACTS_V0`
"""
    with open(os.path.join(out_dir, "next_task_pointer.md"), "w") as f:
        f.write(next_task_md)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
