"""V6 Manual Evidence Fixture Validator and Source Submission Refresh.

Validates the operator-supplied manual evidence fixture slots, performs safety
hygiene filtering, compiles blocker matrices, and generates staging reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR")
DEFAULT_FIXTURE_INPUT = DEFAULT_OUTPUT_DIR / "operator_fillable_fixture.json"

REQUIRED_SLOTS = [
    "operator_idea_source_ref",
    "topic_statement",
    "factual_claims",
    "source_notes",
    "citation_candidates",
    "supporting_artifacts",
    "limitation_notes",
    "no_signal_disclosure",
    "intended_content_lane",
    "intended_canonical_article_angle"
]

UNSAFE_PATTERNS = [
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
    "private_key",
    "session",
    "localstorage",
    "sessionstorage",
    "header"
]


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def is_unsafe_value(val: Any) -> bool:
    if isinstance(val, list):
        return any(is_unsafe_value(item) for item in val)
    if not isinstance(val, str):
        return False
    val_lower = val.lower()
    for pattern in UNSAFE_PATTERNS:
        if pattern in val_lower:
            return True
    return False


def is_empty_or_placeholder(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, list):
        return len(val) == 0 or all(is_empty_or_placeholder(item) for item in val)
    if isinstance(val, str):
        v = val.strip()
        return len(v) == 0 or "placeholder" in v.lower() or "replace_" in v.lower()
    return False


def validate_fixture(fixture_data: dict[str, Any]) -> tuple[str, list[str], list[str], bool, bool]:
    # Check if empty
    all_empty = True
    for slot in REQUIRED_SLOTS:
        val = fixture_data.get(slot)
        if not is_empty_or_placeholder(val):
            all_empty = False
            break

    validation_errors = []
    rejected_slots = []
    unsafe_detected = False

    # Check for unsafe values first
    for slot in REQUIRED_SLOTS:
        val = fixture_data.get(slot)
        if val is not None:
            if is_unsafe_value(val):
                unsafe_detected = True
                rejected_slots.append(slot)
                validation_errors.append(f"Slot '{slot}' contains unsafe values (token/webhook/cookie/env).")

    if all_empty:
        status = "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
        validation_errors.append("Fixture is empty. Operator must supply values for required slots.")
        evidence_complete = False
    elif unsafe_detected:
        status = "FIXTURE_REJECTED_UNSAFE_VALUES"
        evidence_complete = False
    else:
        # Check completeness
        missing_slots = []
        for slot in REQUIRED_SLOTS:
            val = fixture_data.get(slot)
            if is_empty_or_placeholder(val):
                missing_slots.append(slot)
        
        if missing_slots:
            status = "FIXTURE_INCOMPLETE_MISSING_SLOTS"
            validation_errors.append(f"Fixture is incomplete. Missing or empty required slots: {', '.join(missing_slots)}")
            evidence_complete = False
        else:
            evidence_complete = True
            # Distinguish validation success vs preflight readiness based on request flags
            if fixture_data.get("submit_to_preflight") is True or fixture_data.get("ready_for_preflight") is True:
                status = "EVIDENCE_SUBMISSION_READY_FOR_PREFLIGHT_REVIEW"
            else:
                status = "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"

    return status, validation_errors, rejected_slots, unsafe_detected, evidence_complete


def generate_submission_guide() -> str:
    return """# Operator Evidence Submission Guide

This guide documents the procedures for submitting verified underlying evidence using the manual evidence fixture.

## Required Slots
All 10 slots must be supplied with non-empty, non-placeholder values:
1. `operator_idea_source_ref`: Reference path to verified source.
2. `topic_statement`: Short summary of the topic.
3. `factual_claims`: List of factual statements.
4. `source_notes`: Verification notes.
5. `citation_candidates`: List of citations.
6. `supporting_artifacts`: Local verification files/records.
7. `limitation_notes`: Contextual warnings or limitations.
8. `no_signal_disclosure`: Explicit confirmation of no financial advice.
9. `intended_content_lane`: Substack, Discord, or other channel.
10. `intended_canonical_article_angle`: Article framing angle.

## Verification Constraints
* Governance policies are dictated by the V6 Fast Ship Operating Profile.
* Under no circumstances should any slot contain raw credentials, webhook URLs, local config files, or authorization headers.
* Empty template placeholders are rejected as incomplete.
"""


def generate_next_task_pointer(status: str) -> str:
    if status in ["VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW", "EVIDENCE_SUBMISSION_READY_FOR_PREFLIGHT_REVIEW"]:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0"
        goal = "Proceed to the operator review and approval gate to authorize preflight drop."
    else:
        next_task = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
        goal = "Re-run validation once the operator has filled in the manual evidence fixture."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Manual Evidence Fixture Validator Implementation Report

- **Task Label**: {TASK_LABEL}
- **Validation Status**: {status}

- **Safety & Hygiene Verification**:
  - No secret output: `true`
  - No webhook URLs or concrete host/path patterns printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No public-postable content produced: `true`
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Manual Evidence Fixture Validator")
    parser.add_argument("--fixture-file", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--wiring-output-dir", default="docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING")
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve fixture file path based on precedence rules
    selected_file = None
    resolution_reason = ""

    if args.fixture_file is not None:
        selected_file = args.fixture_file
        resolution_reason = "Explicit CLI --fixture-file argument supplied."
    else:
        console_path = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json")
        default_val_path = Path("docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/operator_fillable_fixture.json")
        if console_path.exists():
            selected_file = str(console_path)
            resolution_reason = "No CLI --fixture-file supplied; loaded operator console fixture path."
        elif default_val_path.exists():
            selected_file = str(default_val_path)
            resolution_reason = "No CLI --fixture-file or operator console fixture found; fallback to manual validator default fixture."
        else:
            selected_file = None
            resolution_reason = "No fixture files found on disk."

    # 1. Fillable template
    template = {slot: [] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else None for slot in REQUIRED_SLOTS}
    write_json(out_dir / "operator_fillable_fixture_template.json", template)

    # 2. Example with safe placeholders
    example = {slot: ["PLACEHOLDER_REPLACE_BEFORE_REVIEW"] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else "PLACEHOLDER_REPLACE_BEFORE_REVIEW" for slot in REQUIRED_SLOTS}
    write_json(out_dir / "operator_fillable_fixture_example.safe_placeholder.json", example)

    # Load fixture data
    fixture_data = None
    if selected_file is not None:
        fixture_data = load_json(selected_file)
    if fixture_data is None:
        fixture_data = {}

    status, errors, rejected, unsafe_detected, evidence_complete = validate_fixture(fixture_data)

    # 3. Validation Summary
    summary = {
        "validation_status": status,
        "evidence_complete": evidence_complete,
        "unsafe_values_detected": unsafe_detected,
        "validation_errors": errors,
        "rejected_slots": rejected
    }
    write_json(out_dir / "manual_evidence_fixture_validation_summary.json", summary)

    # 4. Refresh Packet
    hasher = hashlib.sha256(f"{status}_{evidence_complete}".encode("utf-8"))
    refresh_packet_id = f"refresh_{hasher.hexdigest()[:12]}"
    refresh_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "refresh_packet_id": refresh_packet_id,
        "validation_status": status,
        "evidence_complete": evidence_complete,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "kill_switch_active": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" if evidence_complete else TASK_LABEL
    }
    write_json(out_dir / "manual_evidence_fixture_refresh_packet.json", refresh_packet)

    # 5. Carry Forward Blockers
    blockers = [
        "destination_binding_incomplete",
        "evidence_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "operator_idea_source_ref_missing",
        "outbox_creation_blocked",
        "payload_hash_incomplete",
        "safety_review_incomplete"
    ]
    if evidence_complete:
        if "evidence_incomplete" in blockers:
            blockers.remove("evidence_incomplete")
        if "operator_idea_source_ref_missing" in blockers:
            blockers.remove("operator_idea_source_ref_missing")

    snap = {
        "dispatch_allowed_now": False,
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "kill_switch_active": True,
        "unresolved_blockers": sorted(blockers),
        "next_required_action": "Operator must submit verified facts and evidence via the manual evidence fixture to resolve operator_idea_source_ref_missing." if not evidence_complete else "Proceed to operator approval gate signature verification."
    }
    write_json(out_dir / "dispatch_blocker_carry_forward_snapshot.json", snap)

    # 6. Submission guide
    (out_dir / "operator_submission_guide.md").write_text(generate_submission_guide(), encoding="utf-8")

    # 7. Next task pointer
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(status), encoding="utf-8")

    # 8. Staging report
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")

    # --- Part C: Generate Wiring Artifacts under args.wiring_output_dir ---
    wiring_dir = Path(args.wiring_output_dir)
    wiring_dir.mkdir(parents=True, exist_ok=True)

    wiring_packet = {
        "task_label": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_VALIDATOR_WIRING_AND_SAFE_FIXTURE_IMPORT_V0",
        "schema_version": SCHEMA_VERSION,
        "wiring_status": "WIRING_SUCCESS",
        "resolved_fixture_file": selected_file,
        "resolution_reason": resolution_reason,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "public_postable": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "kill_switch_active": True
    }
    write_json(wiring_dir / "validator_wiring_packet.json", wiring_packet)

    resolution_snapshot = {
        "selected_fixture_file": selected_file,
        "resolution_reason": resolution_reason,
        "file_exists": selected_file is not None,
        "status_at_resolution": status,
        "evidence_complete": evidence_complete
    }
    write_json(wiring_dir / "operator_fixture_resolution_snapshot.json", resolution_snapshot)

    wiring_report = f"""# Manual Evidence Validator Wiring Report

- **Task Label**: TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_VALIDATOR_WIRING_AND_SAFE_FIXTURE_IMPORT_V0
- **Wiring Status**: WIRING_SUCCESS
- **Resolved Fixture File**: {selected_file or "None (Not found)"}
- **Resolution Reason**: {resolution_reason}

- **Safety & Compliance Lock**:
  - No secret output: `true`
  - No webhook URLs or credentials leaked: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""
    (wiring_dir / "implementation_report.md").write_text(wiring_report, encoding="utf-8")

    wiring_pointer = f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{"TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" if evidence_complete else "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"}`

Goal: {"Proceed to the operator review and approval gate to authorize preflight drop." if evidence_complete else "Re-run validation once the operator has filled in the manual evidence fixture."}
"""
    (wiring_dir / "next_task_pointer.md").write_text(wiring_pointer, encoding="utf-8")

    print(json.dumps({
        "refresh_packet_id": refresh_packet_id,
        "validation_status": status,
        "evidence_complete": evidence_complete
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
