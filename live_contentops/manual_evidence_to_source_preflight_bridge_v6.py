"""V6 Manual Evidence to Source Preflight Bridge.

Bridges operator evidence validation records into candidate inputs for the
source evidence preflight check lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_WIRING_PACKET = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/validator_wiring_packet.json")
DEFAULT_RESOLUTION_SNAPSHOT = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/operator_fixture_resolution_snapshot.json")
DEFAULT_VALIDATION_SUMMARY = Path("docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/manual_evidence_fixture_validation_summary.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE")

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


def get_slot_status(fixture_data: dict[str, Any], slot: str) -> str:
    val = fixture_data.get(slot)
    if val is None or is_empty_or_placeholder(val):
        return "MISSING_OR_EMPTY"
    if is_unsafe_value(val):
        return "REJECTED_UNSAFE_VALUES"
    return "PROVIDED_VAL_READY"


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Manual Evidence to Source Preflight Bridge Implementation Report

- **Task Label**: {TASK_LABEL}
- **Bridge Status**: {status}

- **Compliance Rules**:
  - No secret output: `true`
  - No webhook URLs printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No browser/CDP session launched: `true`
"""


def generate_next_task_pointer(preflight_ready: bool) -> str:
    if preflight_ready:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0"
        goal = "Proceed to the operator review and approval gate signature verification."
    else:
        next_task = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
        goal = "Re-run validation once the operator has supplied the manual evidence fixture in operator_evidence_fixture.json."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Manual Evidence to Source Preflight Bridge")
    parser.add_argument("--wiring-packet", default=str(DEFAULT_WIRING_PACKET))
    parser.add_argument("--resolution-snapshot", default=str(DEFAULT_RESOLUTION_SNAPSHOT))
    parser.add_argument("--validation-summary", default=str(DEFAULT_VALIDATION_SUMMARY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read input packets
    wiring = load_json(args.wiring_packet) or {}
    snap = load_json(args.resolution_snapshot) or {}
    summary = load_json(args.validation_summary) or {}

    evidence_complete = snap.get("evidence_complete", False)
    status_at_resolution = snap.get("status_at_resolution", "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT")
    selected_fixture_file = snap.get("selected_fixture_file")

    # Load actual fixture if path resolved
    fixture_data = {}
    if selected_fixture_file and Path(selected_fixture_file).exists():
        fixture_data = load_json(selected_fixture_file) or {}

    # Define bridge status based on validator outputs
    if status_at_resolution == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT" or not evidence_complete:
        bridge_status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
        source_preflight_ready = False
    elif status_at_resolution == "FIXTURE_REJECTED_UNSAFE_VALUES":
        bridge_status = "BLOCKED_REJECTED_UNSAFE_VALUES"
        source_preflight_ready = False
    elif status_at_resolution == "FIXTURE_INCOMPLETE_MISSING_SLOTS":
        bridge_status = "BLOCKED_INCOMPLETE_MISSING_SLOTS"
        source_preflight_ready = False
    elif evidence_complete and status_at_resolution in ["VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW", "EVIDENCE_SUBMISSION_READY_FOR_PREFLIGHT_REVIEW"]:
        bridge_status = "PREFLIGHT_CANDIDATE_READY_FOR_REVIEW"
        source_preflight_ready = True
    else:
        bridge_status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
        source_preflight_ready = False

    # Collect blockers
    blockers = []
    if bridge_status != "PREFLIGHT_CANDIDATE_READY_FOR_REVIEW":
        blockers.append("missing_or_incomplete_operator_evidence")
    blockers.append("operator_approval_signature_pending")
    blockers.append("payload_hash_verification_incomplete")
    blockers.append("kill_switch_active")

    # Construct projection slots
    projection = {
        "operator_idea_source_ref_status": get_slot_status(fixture_data, "operator_idea_source_ref"),
        "topic_statement_status": get_slot_status(fixture_data, "topic_statement"),
        "factual_claims_status": get_slot_status(fixture_data, "factual_claims"),
        "citation_candidates_status": get_slot_status(fixture_data, "citation_candidates"),
        "supporting_artifacts_status": get_slot_status(fixture_data, "supporting_artifacts"),
        "limitation_notes_status": get_slot_status(fixture_data, "limitation_notes"),
        "no_signal_disclosure_status": get_slot_status(fixture_data, "no_signal_disclosure"),
        "intended_content_lane_status": get_slot_status(fixture_data, "intended_content_lane"),
        "intended_canonical_article_angle_status": get_slot_status(fixture_data, "intended_canonical_article_angle"),
        "bridge_blockers": sorted(blockers),
        "next_required_operator_action": (
            "Jim must fill operator_evidence_fixture.json with verified manual evidence."
            if not evidence_complete else "Submit the preflight candidate for operator approval signatures."
        )
    }
    write_json(out_dir / "source_preflight_input_projection.json", projection)

    # Bridge Packet
    hasher = hashlib.sha256(f"{bridge_status}_{evidence_complete}".encode("utf-8"))
    bridge_packet_id = f"bridge_{hasher.hexdigest()[:12]}"
    bridge_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "bridge_packet_id": bridge_packet_id,
        "bridge_status": bridge_status,
        "evidence_complete": evidence_complete,
        "operator_idea_source_ref_resolved": evidence_complete,
        "source_ref_resolved": evidence_complete,
        "source_preflight_ready": source_preflight_ready,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" if source_preflight_ready else "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    }
    write_json(out_dir / "bridge_packet.json", bridge_packet)

    # Status Snapshot
    snapshot = {
        "source_evidence_status": status_at_resolution,
        "preflight_bridge_status": bridge_status,
        "source_preflight_ready": source_preflight_ready,
        "evidence_complete": evidence_complete,
        "dispatch_blocked": True,
        "kill_switch_active": True,
        "next_required_action": projection["next_required_operator_action"]
    }
    write_json(out_dir / "evidence_to_preflight_status_snapshot.json", snapshot)

    # Write text documents
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(bridge_status), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(source_preflight_ready), encoding="utf-8")

    print(json.dumps({
        "bridge_packet_id": bridge_packet_id,
        "bridge_status": bridge_status,
        "source_preflight_ready": source_preflight_ready,
        "evidence_complete": evidence_complete
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
