"""V6 Operator Approval Gate Lane.

Consumes operator evidence submission results, validation reports, preflight snapshots,
and staging drop packets to compile comprehensive operator approval gate states
and dispatch-lock reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_AND_SAFE_DOC_TIGHTENING_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_SUBMISSION = Path("docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_submission_packet.json")
DEFAULT_VAL_REPORT = Path("docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_validation_report.json")
DEFAULT_SNAPSHOT = Path("docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/dispatch_unlock_blockers_snapshot.json")
DEFAULT_PREFLIGHT = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/approval_preflight_packet.json")
DEFAULT_DROP = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_packet.json")
DEFAULT_REVIEW = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/operator_review_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")
DEFAULT_GATE_OUTPUT = DEFAULT_OUTPUT_DIR / "operator_approval_gate_packet.json"


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_gate_checklist_markdown(packet: dict[str, Any]) -> str:
    return f"""# Operator Approval Gate Checklist

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains preflight staging checklists. It is not publish-ready and must not be posted or used for live dispatch.

## Preflight Status
- **Approval Gate Status**: {packet.get('approval_gate_status')}
- **Approval Valid for Dispatch**: {packet.get('approval_valid_for_dispatch')}

## Requirements Checklist
- [ ] **Source Evidence Complete**: {packet.get('evidence_complete')}
- [ ] **Payload Hash Verified**: {packet.get('payload_hash_complete')}
- [ ] **Destination Binding Matches**: {packet.get('destination_binding_complete')}
- [ ] **Safety Review Passed**: {packet.get('safety_review_complete')}
- [ ] **Operator Approval Completed**: {packet.get('operator_approval_complete')}

## Dispatch Status Lock
- **No-Live / No-Dispatch Warning**: Dispatch of this community drop is strictly blocked because `dispatch_allowed_now` is false.
"""


def generate_readme_markdown(packet: dict[str, Any]) -> str:
    return f"""# Operator Approval Gate Readme

## What This Gate Does
- Safely aggregates multi-layer review results from previous tasks.
- Asserts that all staging parameters are valid before letting human decisions execute.

## What This Gate Does NOT Do
- It does not make live writes, publish drafts, calculate real hashes, or update outbox queues.
- This gate does not authorize real dispatch. Real authorizations occur in later explicit live-write tasks.

## Why Approval Remains Invalid
- Factual source evidence, payload hashes, channel bindings, and operator approval are not yet fully resolved.

## Safety & Compliance Lock
- **No Fake-Citation Note**: No fake or placeholder citations may be turned into claims.
- **No Fake-Metric Note**: Do not invent metrics or statistics.
- **No Secret-Output Note**: Webhook URLs, headers, and secrets are strictly excluded.
"""


def materialize_gate_packets(
    sub_path: str | Path = DEFAULT_SUBMISSION,
    val_report_path: str | Path = DEFAULT_VAL_REPORT,
    snap_path: str | Path = DEFAULT_SNAPSHOT,
    preflight_path: str | Path = DEFAULT_PREFLIGHT,
    drop_path: str | Path = DEFAULT_DROP,
    review_path: str | Path = DEFAULT_REVIEW,
    override_complete: bool = False
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    upstream_blocked = False
    blocked_reasons = []

    try:
        sub_data = load_json(sub_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"submission_packet_unreadable:{exc.__class__.__name__}")
        sub_data = {}

    try:
        val_report_data = load_json(val_report_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"validation_report_unreadable:{exc.__class__.__name__}")
        val_report_data = {}

    try:
        snap_data = load_json(snap_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"blockers_snapshot_unreadable:{exc.__class__.__name__}")
        snap_data = {}

    try:
        preflight_data = load_json(preflight_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"preflight_packet_unreadable:{exc.__class__.__name__}")
        preflight_data = {}

    try:
        drop_data = load_json(drop_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"drop_packet_unreadable:{exc.__class__.__name__}")
        drop_data = {}

    try:
        review_data = load_json(review_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"review_packet_unreadable:{exc.__class__.__name__}")
        review_data = {}

    blocked_reasons.extend(sub_data.get("blocked_reasons", []))
    blocked_reasons = sorted(list(set(blocked_reasons)))

    # Evaluate completeness
    evidence_complete = sub_data.get("evidence_complete", False) or override_complete
    payload_hash_complete = override_complete
    destination_binding_complete = override_complete
    safety_review_complete = override_complete
    operator_approval_complete = override_complete

    blockers = []
    if not evidence_complete:
        blockers.append("evidence_incomplete")
    if not payload_hash_complete:
        blockers.append("payload_hash_incomplete")
    if not destination_binding_complete:
        blockers.append("destination_binding_incomplete")
    if not safety_review_complete:
        blockers.append("safety_review_incomplete")
    if not operator_approval_complete:
        blockers.append("operator_approval_incomplete")

    # Status Logic
    if upstream_blocked or sub_data.get("submission_status") == "BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT" or blocked_reasons:
        approval_gate_status = "BLOCKED_BY_SOURCE_EVIDENCE_SUBMISSION"
    elif blockers:
        approval_gate_status = "APPROVAL_GATE_BLOCKED_PENDING_REQUIREMENTS"
    else:
        approval_gate_status = "APPROVAL_GATE_READY_FOR_HUMAN_DECISION"

    hasher = hashlib.sha256(f"{sub_data.get('operator_source_evidence_submission_packet_id')}_{approval_gate_status}".encode("utf-8"))
    operator_approval_gate_packet_id = f"gate_{hasher.hexdigest()[:12]}"

    # Operator Approval Gate Packet
    gate_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_approval_gate_packet_id": operator_approval_gate_packet_id,
        "source_submission_packet_id": sub_data.get("operator_source_evidence_submission_packet_id"),
        "source_validation_report_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_validation_report.json",
        "source_dispatch_unlock_blockers_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/dispatch_unlock_blockers_snapshot.json",
        "source_approval_preflight_packet_id": preflight_data.get("approval_preflight_packet_id"),
        "source_discord_drop_packet_id": drop_data.get("discord_drop_packet_id"),
        "source_operator_review_packet_id": review_data.get("operator_review_packet_id"),
        "approval_gate_status": approval_gate_status,
        "approval_stage": "operator_approval_gate_preflight",
        "evidence_complete": evidence_complete,
        "payload_hash_complete": payload_hash_complete,
        "destination_binding_complete": destination_binding_complete,
        "safety_review_complete": safety_review_complete,
        "operator_approval_complete": operator_approval_complete,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "blockers": sorted(blockers),
        "payload_hash_placeholder_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/payload_hash_placeholder.json",
        "destination_binding_placeholder_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/destination_binding_placeholder.json",
        "approval_decision_record_template_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/approval_decision_record_template.json",
        "dispatch_lock_report_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/dispatch_lock_report.json",
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": blocked_reasons,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_AND_SAFE_DOC_TIGHTENING_HEAVY_BATCH_V0" if approval_gate_status == "BLOCKED_BY_SOURCE_EVIDENCE_SUBMISSION" else "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_LANE_V0"
    }

    # Payload Hash Placeholder
    payload_hash = {
        "final_payload_hash_present": False,
        "final_payload_hash_value": None,
        "hash_algorithm": "sha256_placeholder_only",
        "hash_calculation_allowed_now": False,
        "reason": "final public payload is not ready and not approved"
    }

    # Destination Binding Placeholder
    destination_binding = {
        "destination_binding_present": False,
        "target_platform": "discord",
        "channel_family": "community_announcements_placeholder",
        "real_channel_id_present": False,
        "webhook_url_present": False,
        "token_present": False,
        "secret_keys_present": False,
        "binding_allowed_now": False,
        "reason": "real binding requires later explicit live-write authorization"
    }

    # Approval Decision Record Template
    decision_record = {
        "operator_decision": None,
        "approved_by": None,
        "approved_at": None,
        "approval_notes": None,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "exact_payload_hash_confirmed": False,
        "destination_binding_confirmed": False,
        "source_evidence_confirmed": False,
        "safety_review_confirmed": False
    }

    # Dispatch Lock Report
    dispatch_report = {
        "dispatch_lock_status": "LOCKED_APPROVAL_REQUIREMENTS_INCOMPLETE" if blockers else "LOCKED_AWAITING_EXPLICIT_DECISION",
        "blocker_summary": sorted(blockers),
        "dispatch_allowed_now": False,
        "public_postable": False,
        "outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "live_write_attempted": False,
        "next_required_operator_action": "Resolve outstanding blockers in source evidence, payload hash calculation, and manual approval signatures." if blockers else "Submit explicit operator review decision."
    }

    return gate_packet, payload_hash, destination_binding, decision_record, dispatch_report


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Operator Approval Gate

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Approval gate checkers generated: `true`
- Dispatch-lock checkpoints built: `true`
- Fake public-postable content created: `false`

The operator approval gate and safety locking report are initialized.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, refinement, variant, preflight, or validation block conditions."
    else:
        goal = "Proceed to V6 Supervised Dispatch Readiness Lane workflows."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Approval Gate Lane")
    parser.add_argument("--submission-packet", default=str(DEFAULT_SUBMISSION))
    parser.add_argument("--val-report", default=str(DEFAULT_VAL_REPORT))
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--preflight", default=str(DEFAULT_PREFLIGHT))
    parser.add_argument("--drop-packet", default=str(DEFAULT_DROP))
    parser.add_argument("--review-packet", default=str(DEFAULT_REVIEW))
    parser.add_argument("--output-packet", default=str(DEFAULT_GATE_OUTPUT))
    args = parser.parse_args(argv)

    sub, payload_hash, binding, decision, lock_report = materialize_gate_packets(
        args.submission_packet, args.val_report, args.snapshot, args.preflight, args.drop_packet, args.review_packet
    )
    write_json(args.output_packet, sub)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "payload_hash_placeholder.json", payload_hash)
    write_json(out_dir / "destination_binding_placeholder.json", binding)
    write_json(out_dir / "approval_decision_record_template.json", decision)
    write_json(out_dir / "dispatch_lock_report.json", lock_report)

    # Write checklists and READMEs
    (out_dir / "operator_approval_gate_checklist.md").write_text(generate_gate_checklist_markdown(sub), encoding="utf-8")
    (out_dir / "operator_approval_gate_readme.md").write_text(generate_readme_markdown(sub), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(sub), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(sub), encoding="utf-8")

    print(json.dumps({
        "operator_approval_gate_packet_id": sub["operator_approval_gate_packet_id"],
        "approval_gate_status": sub["approval_gate_status"],
        "blocked_reasons": sub["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
