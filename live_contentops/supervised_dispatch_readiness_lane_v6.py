"""V6 Supervised Dispatch Readiness Lane.

Consumes operator approval gate outputs to construct comprehensive blocker matrices,
safety kill switches, and pre-dispatch checklists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_LANE_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_GATE_PACKET = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
DEFAULT_LOCK_REPORT = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/dispatch_lock_report.json")
DEFAULT_PAYLOAD_HASH = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/payload_hash_placeholder.json")
DEFAULT_BINDING = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/destination_binding_placeholder.json")
DEFAULT_DECISION = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/approval_decision_record_template.json")
DEFAULT_DROP = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS")
DEFAULT_READINESS_OUTPUT = DEFAULT_OUTPUT_DIR / "supervised_dispatch_readiness_packet.json"


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_readiness_report_markdown(packet: dict[str, Any], report_status: str, blockers: list[str]) -> str:
    blocker_str = ", ".join(f"`{b}`" for r in blockers for b in [r]) or "None"
    return f"""# Supervised Dispatch Readiness Report

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains preflight staging checklists. It is not publish-ready and must not be posted or sent to any live Discord channel.

## Preflight Status
- **Readiness Status**: {packet.get('readiness_status')}
- **Staging Status**: {report_status}
- **Blockers**: {blocker_str}

## Warning Checklist
- **Dry-Run-Only Warning**: All dispatch pipelines remain strictly in dry-run-only mockup modes. No real endpoints are active.
- **Kill-Switch Status**: Kill-switch is fully active. All outbound traffic is globally disabled.
- **No-Live / No-Dispatch Warning**: Dispatch remains strictly blocked because `dispatch_allowed_now` is false.
- **No Outbox / Ledger Created**: No real outbox queue or approved ledger entries have been written.

## Operator Safety Lock Notes
- **No Fake-Citation Note**: Do not invent sources, citations, CPC statistics, user numbers, latency totals, or market data.
- **No Fake-Metric Note**: Do not invent metrics or statistics.
- **No Secret-Output Note**: Webhook URLs, tokens, cookies, auth headers, and secrets are strictly excluded.

## Next Operator Remediation Action
- To proceed, human operators must supply factual source evidence and finalize review approval checklist signatures in a separate, later explicit task.
"""


def generate_pre_dispatch_checklist_markdown(packet: dict[str, Any], matrix: list[dict[str, Any]]) -> str:
    return f"""# Pre-Dispatch Checklist

## 1. Source Evidence Checklist
- [ ] Verify that all source reference registry slots are mapped to real-content files.
- [ ] Confirm no `.env` or credential paths are mapped.

## 2. Payload Hash Checklist
- [ ] Calculate deterministic SHA256 of final article drafts.
- [ ] Confirm payload hash is matched and verified.

## 3. Destination Binding Checklist
- [ ] Ensure channel binding status matches a valid announcements channel family.
- [ ] Confirm mock binding layout contains no sensitive secrets or tokens.

## 4. Safety Review Checklist
- [ ] Confirm no hype language is present.
- [ ] Confirm no trading signals, position sizing, or guaranteed predictions exist.

## 5. Operator Approval Checklist
- [ ] Review approval decision record template.
- [ ] Sign checklist and log operator decision.

## 6. Kill Switch Checklist
- [ ] Confirm kill-switch global override is disabled (must occur in a separate live task).

## 7. Live-Write Authorization Checklist
- [ ] Verify that explicit live write authorizations have occurred (must occur in a separate live task).

## Final Readiness Check
- **Dispatch Blocked Note**: Dispatch remains strictly blocked. `dispatch_allowed_now` is false.
"""


def materialize_readiness_packets(
    gate_path: str | Path = DEFAULT_GATE_PACKET,
    lock_report_path: str | Path = DEFAULT_LOCK_REPORT,
    payload_hash_path: str | Path = DEFAULT_PAYLOAD_HASH,
    binding_path: str | Path = DEFAULT_BINDING,
    decision_path: str | Path = DEFAULT_DECISION,
    drop_path: str | Path = DEFAULT_DROP,
    override_ready: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    upstream_blocked = False
    blocked_reasons = []

    try:
        gate_data = load_json(gate_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"gate_packet_unreadable:{exc.__class__.__name__}")
        gate_data = {}

    try:
        lock_report_data = load_json(lock_report_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"lock_report_unreadable:{exc.__class__.__name__}")
        lock_report_data = {}

    try:
        payload_hash_data = load_json(payload_hash_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"payload_hash_unreadable:{exc.__class__.__name__}")
        payload_hash_data = {}

    try:
        binding_data = load_json(binding_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"binding_unreadable:{exc.__class__.__name__}")
        binding_data = {}

    try:
        decision_data = load_json(decision_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"decision_template_unreadable:{exc.__class__.__name__}")
        decision_data = {}

    try:
        drop_data = load_json(drop_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"drop_packet_unreadable:{exc.__class__.__name__}")
        drop_data = {}

    blocked_reasons.extend(gate_data.get("blocked_reasons", []))
    blocked_reasons = sorted(list(set(blocked_reasons)))

    # Evaluate completeness
    evidence_complete = gate_data.get("evidence_complete", False) or override_ready
    payload_hash_complete = gate_data.get("payload_hash_complete", False) or override_ready
    destination_binding_complete = gate_data.get("destination_binding_complete", False) or override_ready
    safety_review_complete = gate_data.get("safety_review_complete", False) or override_ready
    operator_approval_complete = gate_data.get("operator_approval_complete", False) or override_ready

    blockers = list(gate_data.get("blockers", []))
    if not blockers and not override_ready:
        if not evidence_complete: blockers.append("evidence_incomplete")
        if not payload_hash_complete: blockers.append("payload_hash_incomplete")
        if not destination_binding_complete: blockers.append("destination_binding_incomplete")
        if not safety_review_complete: blockers.append("safety_review_incomplete")
        if not operator_approval_complete: blockers.append("operator_approval_incomplete")

    # Add downstream preflight blockers
    if not override_ready:
        blockers.extend(["kill_switch_active", "live_write_authorization_missing", "outbox_creation_blocked"])
    blockers = sorted(list(set(blockers)))

    # Evaluate Status
    gate_status = gate_data.get("approval_gate_status")
    if upstream_blocked or gate_status == "BLOCKED_BY_SOURCE_EVIDENCE_SUBMISSION" or blocked_reasons:
        readiness_status = "BLOCKED_BY_OPERATOR_APPROVAL_GATE"
    elif gate_status == "APPROVAL_GATE_READY_FOR_HUMAN_DECISION" and not override_ready:
        readiness_status = "SUPERVISED_DISPATCH_READY_FOR_OPERATOR_REVIEW_ONLY"
    elif blockers:
        readiness_status = "DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS"
    else:
        readiness_status = "SUPERVISED_DISPATCH_READY"

    hasher = hashlib.sha256(f"{gate_data.get('operator_approval_gate_packet_id')}_{readiness_status}".encode("utf-8"))
    supervised_dispatch_readiness_packet_id = f"readiness_{hasher.hexdigest()[:12]}"

    # Supervised Dispatch Readiness Packet
    readiness_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "supervised_dispatch_readiness_packet_id": supervised_dispatch_readiness_packet_id,
        "source_operator_approval_gate_packet_id": gate_data.get("operator_approval_gate_packet_id"),
        "source_dispatch_lock_report_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/dispatch_lock_report.json",
        "source_payload_hash_placeholder_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/payload_hash_placeholder.json",
        "source_destination_binding_placeholder_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/destination_binding_placeholder.json",
        "source_approval_decision_record_template_file": "docs/automation/V6_OPERATOR_APPROVAL_GATE/approval_decision_record_template.json",
        "source_discord_drop_packet_id": drop_data.get("discord_drop_packet_id"),
        "readiness_status": readiness_status,
        "readiness_stage": "supervised_dispatch_readiness_preflight",
        "target_platform": "discord",
        "target_channel_family": "community_announcements_placeholder",
        "evidence_complete": evidence_complete,
        "payload_hash_complete": payload_hash_complete,
        "destination_binding_complete": destination_binding_complete,
        "safety_review_complete": safety_review_complete,
        "operator_approval_complete": operator_approval_complete,
        "kill_switch_active": not override_ready,
        "outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "live_write_attempted": False,
        "dry_run_only": True,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "blockers": blockers,
        "blocker_matrix_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/pre_dispatch_blocker_matrix.json",
        "dry_run_dispatch_plan_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/dry_run_dispatch_plan_placeholder.json",
        "idempotency_key_placeholder_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/idempotency_key_placeholder.json",
        "kill_switch_snapshot_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/kill_switch_snapshot.json",
        "operator_readiness_report_file": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/operator_readiness_report.md",
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
        "next_recommended_task": "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_LANE_V0" if readiness_status == "BLOCKED_BY_OPERATOR_APPROVAL_GATE" else "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_AND_SAFE_DOC_TIGHTENING_HEAVY_BATCH_V0"
    }

    # Pre-dispatch Blocker Matrix
    blocker_matrix = [
        {
            "gate_name": "source_evidence",
            "required": True,
            "complete": evidence_complete,
            "blocker_reason": "operator_evidence_missing_from_registry",
            "current_status": "LOCKED_AWAITING_EVIDENCE_MAPPING",
            "remediation_hint": "Supply safe PDF, repo file, screenshot, or URL pointers to resolve reference gap."
        },
        {
            "gate_name": "payload_hash",
            "required": True,
            "complete": payload_hash_complete,
            "blocker_reason": "sha256_uncalculated_pending_final_draft",
            "current_status": "LOCKED_AWAITING_HASH_VERIFICATION",
            "remediation_hint": "Calculate final content draft SHA256 and confirm digest matching."
        },
        {
            "gate_name": "destination_binding",
            "required": True,
            "complete": destination_binding_complete,
            "blocker_reason": "mock_placeholder_active_no_sensitive_endpoints_loaded",
            "current_status": "LOCKED_AWAITING_BINDING_VERIFICATION",
            "remediation_hint": "Verify channel family matches non-sensitive platform destination signatures."
        },
        {
            "gate_name": "safety_review",
            "required": True,
            "complete": safety_review_complete,
            "blocker_reason": "safety_checks_unverified",
            "current_status": "LOCKED_AWAITING_COMPLIANCE_SIGNATURE",
            "remediation_hint": "Review draft content to guarantee zero trading signal, position sizing, or guaranteed predictions exist."
        },
        {
            "gate_name": "operator_approval",
            "required": True,
            "complete": operator_approval_complete,
            "blocker_reason": "operator_signatures_unrecorded",
            "current_status": "LOCKED_AWAITING_APPROVAL_DECISION",
            "remediation_hint": "Complete manual review checklist and submit signed decision record template."
        },
        {
            "gate_name": "kill_switch",
            "required": True,
            "complete": override_ready,
            "blocker_reason": "kill_switch_override_enabled_blocking_dispatch",
            "current_status": "LOCKED_SAFETY_SHUTDOWN_ACTIVE",
            "remediation_hint": "Disable emergency kill-switch globally to enable outbound routing (requires separate live task)."
        },
        {
            "gate_name": "live_write_authorization",
            "required": True,
            "complete": override_ready,
            "blocker_reason": "unauthorized_live_write_attempt_blocked_failsafe",
            "current_status": "LOCKED_AWAITING_WRITE_AUTHORIZATION",
            "remediation_hint": "Obtain explicit, supervisor-level write authorizations (requires separate live task)."
        },
        {
            "gate_name": "outbox_creation",
            "required": True,
            "complete": override_ready,
            "blocker_reason": "outbox_staging_disabled_pending_approval",
            "current_status": "LOCKED_OUTBOX_BLOCKED",
            "remediation_hint": "Complete approval checklists to unblock outbox packet staging queues."
        }
    ]

    # Dry-run Dispatch Plan Placeholder
    dry_run_plan = {
        "dry_run_only": True,
        "target_platform": "discord",
        "target_channel_family": "community_announcements_placeholder",
        "final_payload_present": False,
        "final_payload_hash_present": False,
        "real_destination_present": False,
        "outbox_entry_created": False,
        "dispatch_allowed_now": False,
        "execution_allowed_now": False,
        "note": "strictly non-sendable preview plan for staging dry-runs only."
    }

    # Idempotency Key Placeholder
    idempotency_key = {
        "idempotency_key_present": False,
        "idempotency_key_value": None,
        "final_payload_hash_present": False,
        "destination_binding_present": False,
        "dispatch_attempt_number": None,
        "generation_allowed_now": False,
        "reason": "requires final payload hash, destination binding, and explicit operator approval"
    }

    # Kill-switch Snapshot
    kill_switch = {
        "kill_switch_active": not override_ready,
        "dispatch_globally_disabled": not override_ready,
        "live_write_authorization_present": override_ready,
        "emergency_stop_required_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_attempted": False
    }

    return readiness_packet, blocker_matrix, dry_run_plan, idempotency_key, kill_switch


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Supervised Dispatch Readiness Lane

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Pre-dispatch blocker matrix compiled: `true`
- Dry-run dispatch plan placeholders staged: `true`
- Globally disabling kill-switch snapshot active: `true`
- Fake public-postable content created: `false`

The pre-dispatch readiness state machine is successfully initialized and locked. All routes remain un-sendable.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, refinement, variant, preflight, validation, or gate block conditions."
    else:
        goal = "Proceed back to Operator Approval Gate for decision loop reconciliation once requirements are ready."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Supervised Dispatch Readiness Lane")
    parser.add_argument("--gate-packet", default=str(DEFAULT_GATE_PACKET))
    parser.add_argument("--lock-report", default=str(DEFAULT_LOCK_REPORT))
    parser.add_argument("--payload-hash", default=str(DEFAULT_PAYLOAD_HASH))
    parser.add_argument("--binding-packet", default=str(DEFAULT_BINDING))
    parser.add_argument("--decision-template", default=str(DEFAULT_DECISION))
    parser.add_argument("--drop-packet", default=str(DEFAULT_DROP))
    parser.add_argument("--output-packet", default=str(DEFAULT_READINESS_OUTPUT))
    args = parser.parse_args(argv)

    sub, matrix, dry_plan, idempotency, kill = materialize_readiness_packets(
        args.gate_packet, args.lock_report, args.payload_hash, args.binding_packet, args.decision_template, args.drop_packet
    )
    write_json(args.output_packet, sub)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "pre_dispatch_blocker_matrix.json", matrix)
    write_json(out_dir / "dry_run_dispatch_plan_placeholder.json", dry_plan)
    write_json(out_dir / "idempotency_key_placeholder.json", idempotency)
    write_json(out_dir / "kill_switch_snapshot.json", kill)

    # Write guides and checklists
    (out_dir / "operator_readiness_report.md").write_text(generate_readiness_report_markdown(sub, "LOCKED_PRE_DISPATCH_BLOCKED", sub["blockers"]), encoding="utf-8")
    (out_dir / "pre_dispatch_checklist.md").write_text(generate_pre_dispatch_checklist_markdown(sub, matrix), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(sub), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(sub), encoding="utf-8")

    print(json.dumps({
        "supervised_dispatch_readiness_packet_id": sub["supervised_dispatch_readiness_packet_id"],
        "readiness_status": sub["readiness_status"],
        "blocked_reasons": sub["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
