"""V6 Operator Source Evidence Submission Validator Lane.

Consumes preflight registries, templates, and preflight packets to validate
operator-supplied evidence slots deterministically and prevent leak/safety risk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION_VALIDATOR_AND_PREFLIGHT_POINTER_REPAIR_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_REGISTRY = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_reference_registry.json")
DEFAULT_INTAKE = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json")
DEFAULT_PREFLIGHT = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/approval_preflight_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION")
DEFAULT_SUBMISSION_OUTPUT = DEFAULT_OUTPUT_DIR / "operator_source_evidence_submission_packet.json"


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_unsafe_value(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    val_lower = val.lower()
    unsafe_patterns = [
        "webhook",
        "discord.com/api/webhooks",
        "token",
        "cookie",
        "authorization",
        "bearer",
        ".env",
        "secret",
        "password",
        "pkey",
        "private_key"
    ]
    for pattern in unsafe_patterns:
        if pattern in val_lower:
            return True
    return False


def generate_guide_markdown(packet: dict[str, Any]) -> str:
    return f"""# Operator Source Evidence Submission Guide

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This is an operator staging document. It must not be published or sent to any live Discord channel.

## Purpose
This lane provides operator guidelines for submitting verified underlying evidence to unblock facts or claims.

## Accepted Evidence Shapes
- **local_doc_path**: Local PDF/Word paths such as `docs/evidence/jim_verified_audit_notes.pdf`.
- **repo_file_path**: Path of verified repo markdown/JSON documents.
- **screenshot_path**: Path of verified operator screenshots.
- **official_source_url_to_be_reviewed_later**: URL pointers to official filings or reports.
- **operator_note**: Custom text statements detailing manual audits.

## Unsafe / Forbidden Input Examples (Will Be Rejected)
- Webhook endpoints (`discord.com/api/webhooks/...`)
- Security/auth strings containing `token`, `cookie`, `secret`, `bearer`, or `authorization`
- System configuration paths pointing to `.env` files

## Factual Validation Constraint
- This task validates slot completeness and safe reference formatting only. It does not verify factual truth itself.
- Do not invent sources, citations, CPC figures, or market statistics.
"""


def generate_validation_checklist_markdown(packet: dict[str, Any], report: dict[str, Any]) -> str:
    unresolved = report.get("unresolved_source_refs", [])
    rejected = report.get("rejected_source_refs", [])
    unresolved_str = ", ".join(f"`{r}`" for r in unresolved) or "None"
    rejected_str = ", ".join(f"`{r}`" for r in rejected) or "None"

    return f"""# Evidence Validation Checklist

## Checklist State
- **Evidence Complete**: {packet.get('evidence_complete')}
- **Unresolved References**: {unresolved_str}
- **Rejected References**: {rejected_str}

## Preflight Status Locks
- [ ] Ensure all required reference slots have a safe, non-null value.
- [ ] Confirm no `.env` or credential-containing values exist in the registry.
- [ ] Exact payload hash remains absent (must be validated in a later live task).
- [ ] Destination channel binding remains unconfirmed (must be validated in a later live task).

## Safety & Compliance Lock
- **Dispatch Blocked Note**: Dispatch remains strictly blocked. `dispatch_allowed_now` is false.
"""


def materialize_submission_packets(
    registry_path: str | Path = DEFAULT_REGISTRY,
    intake_path: str | Path = DEFAULT_INTAKE,
    preflight_path: str | Path = DEFAULT_PREFLIGHT,
    operator_input_fixture: list[dict[str, Any]] | None = None
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    upstream_blocked = False
    blocked_reasons = []

    try:
        registry_data = load_json(registry_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"registry_unreadable:{exc.__class__.__name__}")
        registry_data = []

    try:
        intake_data = load_json(intake_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"intake_unreadable:{exc.__class__.__name__}")
        intake_data = {}

    try:
        preflight_data = load_json(preflight_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        upstream_blocked = True
        blocked_reasons.append(f"preflight_unreadable:{exc.__class__.__name__}")
        preflight_data = {}

    blocked_reasons.extend(intake_data.get("blocked_reasons", []))
    blocked_reasons = sorted(list(set(blocked_reasons)))

    required_refs = [r["source_ref_id"] for r in registry_data] if isinstance(registry_data, list) else []
    if not required_refs and intake_data.get("missing_source_refs"):
        required_refs = intake_data["missing_source_refs"]

    # Construct Template
    template = []
    for ref in required_refs:
        template.append({
            "source_ref_id": ref,
            "supplied_value": None,
            "evidence_type": None,
            "operator_note": None,
            "expected_evidence_types": [
                "local_doc_path",
                "repo_file_path",
                "screenshot_path",
                "official_source_url_to_be_reviewed_later",
                "operator_note"
            ],
            "local_validation_required": True,
            "verified": False
        })

    # Validate Supplied Operator Input
    supplied_source_refs = []
    unresolved_source_refs = list(required_refs)
    rejected_source_refs = []
    unsafe_values_detected = False

    if operator_input_fixture:
        for slot in template:
            ref_id = slot["source_ref_id"]
            # Find in operator inputs
            match = next((item for item in operator_input_fixture if item.get("source_ref_id") == ref_id), None)
            if match and match.get("supplied_value") is not None:
                val = match["supplied_value"]
                if is_unsafe_value(val):
                    unsafe_values_detected = True
                    rejected_source_refs.append(ref_id)
                    slot["supplied_value"] = "[REJECTED_UNSAFE_VALUE]"
                    slot["verified"] = False
                else:
                    supplied_source_refs.append(ref_id)
                    if ref_id in unresolved_source_refs:
                        unresolved_source_refs.remove(ref_id)
                    slot["supplied_value"] = val
                    slot["evidence_type"] = match.get("evidence_type", "operator_note")
                    slot["operator_note"] = match.get("operator_note")
                    slot["verified"] = True

    # Submission Status Logic
    if upstream_blocked or intake_data.get("intake_status") == "BLOCKED_BY_UPSTREAM_PACKET" or blocked_reasons:
        submission_status = "BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT"
    elif unresolved_source_refs or unsafe_values_detected:
        submission_status = "AWAITING_OPERATOR_EVIDENCE"
    else:
        submission_status = "EVIDENCE_SUBMISSION_READY_FOR_HUMAN_REVIEW"

    evidence_complete = (not unresolved_source_refs) and (not unsafe_values_detected) and (submission_status != "BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT")

    hasher = hashlib.sha256(f"{intake_data.get('source_evidence_intake_packet_id')}_{submission_status}".encode("utf-8"))
    operator_source_evidence_submission_packet_id = f"submission_{hasher.hexdigest()[:12]}"

    # Submission Packet
    submission_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_source_evidence_submission_packet_id": operator_source_evidence_submission_packet_id,
        "source_evidence_intake_packet_id": intake_data.get("source_evidence_intake_packet_id"),
        "source_reference_registry_file": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_reference_registry.json",
        "approval_preflight_packet_id": preflight_data.get("approval_preflight_packet_id"),
        "submission_status": submission_status,
        "submission_stage": "operator_source_evidence_submission_validation",
        "required_source_refs": required_refs,
        "supplied_source_refs": supplied_source_refs,
        "unresolved_source_refs": unresolved_source_refs,
        "rejected_source_refs": rejected_source_refs,
        "evidence_complete": evidence_complete,
        "validation_report_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_validation_report.json",
        "submission_template_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/operator_source_evidence_template.json",
        "dispatch_unlock_blockers_snapshot_file": "docs/automation/V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION/dispatch_unlock_blockers_snapshot.json",
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": blocked_reasons,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_EVIDENCE_SUBMISSION_VALIDATOR_AND_PREFLIGHT_POINTER_REPAIR_HEAVY_BATCH_V0" if submission_status == "BLOCKED_BY_SOURCE_EVIDENCE_PREFLIGHT" else "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0"
    }

    # Validation Report
    validation_report = {
        "current_validation_status": "AWAITING_OPERATOR_EVIDENCE" if unresolved_source_refs or unsafe_values_detected else "VALIDATION_SUCCESS_READY_FOR_PREFLIGHT_REVIEW",
        "unresolved_source_refs": unresolved_source_refs,
        "rejected_source_refs": rejected_source_refs,
        "evidence_complete": evidence_complete,
        "unsafe_values_detected": unsafe_values_detected,
        "dispatch_allowed_now": False,
        "public_postable": False
    }

    # Dispatch Unlock Blockers Snapshot
    snapshot = {
        "source_evidence_complete": evidence_complete,
        "operator_approval_complete": False,
        "destination_binding_complete": False,
        "exact_payload_hash_complete": False,
        "safety_review_complete": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "next_required_operator_action": "Fill out source references in the submission template with verified safety paths." if not evidence_complete else "Proceed to operator review approval gate signature verification."
    }

    return submission_packet, template, validation_report, snapshot


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Operator Source Evidence Submission Validation

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Operator evidence template created: `true`
- Validation checkpoint built: `true`
- Fake public-postable content created: `false`

The operator source evidence validator lane has been successfully initialized. All dispatches remain securely locked.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, refinement, variant, or preflight staging block conditions."
    else:
        goal = "Proceed to Operator Review Approval Gate Lane verification loop."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Source Evidence Validator")
    parser.add_argument("--registry-packet", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--intake-packet", default=str(DEFAULT_INTAKE))
    parser.add_argument("--preflight-packet", default=str(DEFAULT_PREFLIGHT))
    parser.add_argument("--output-packet", default=str(DEFAULT_SUBMISSION_OUTPUT))
    args = parser.parse_args(argv)

    sub, temp, report, snap = materialize_submission_packets(
        args.registry_packet, args.intake_packet, args.preflight_packet
    )
    write_json(args.output_packet, sub)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "operator_source_evidence_template.json", temp)
    write_json(out_dir / "operator_source_evidence_validation_report.json", report)
    write_json(out_dir / "dispatch_unlock_blockers_snapshot.json", snap)

    # Write guides/checklists
    (out_dir / "operator_source_evidence_submission_guide.md").write_text(generate_guide_markdown(sub), encoding="utf-8")
    (out_dir / "evidence_validation_checklist.md").write_text(generate_validation_checklist_markdown(sub, report), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(sub), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(sub), encoding="utf-8")

    print(json.dumps({
        "operator_source_evidence_submission_packet_id": sub["operator_source_evidence_submission_packet_id"],
        "submission_status": sub["submission_status"],
        "blocked_reasons": sub["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
