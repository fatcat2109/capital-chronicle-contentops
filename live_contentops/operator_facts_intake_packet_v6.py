"""V6 Operator Facts Intake Packet + Manual Evidence Fixture.

Defines the facts/evidence intake structure to turn 'operator_idea_source_ref_missing'
into fillable fact slots and templates for Jim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_FACTS_INTAKE_PACKET_AND_MANUAL_EVIDENCE_FIXTURE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_INTAKE_SOURCE = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json")
DEFAULT_REGISTRY_SOURCE = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_reference_registry.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_FACTS_INTAKE")

REQUIRED_SLOT_IDS = [
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


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_unsafe_value(val: Any) -> bool:
    if isinstance(val, list):
        return any(is_unsafe_value(item) for item in val)
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
        "private_key",
        "session",
        "localstorage",
        "sessionstorage",
        "header"
    ]
    for pattern in unsafe_patterns:
        if pattern in val_lower:
            return True
    return False


def validate_fixture(fixture_data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    is_empty = True
    for slot_id in REQUIRED_SLOT_IDS:
        if fixture_data.get(slot_id) is not None:
            is_empty = False
            break

    slots = []
    unsafe_values_detected = False
    validation_errors = []
    rejected_slots = []

    for slot_id in REQUIRED_SLOT_IDS:
        supplied = fixture_data.get(slot_id)
        unsafe = False
        if supplied is not None:
            if is_unsafe_value(supplied):
                unsafe = True
                unsafe_values_detected = True
                rejected_slots.append(slot_id)
                validation_errors.append(f"Slot '{slot_id}' contains unsafe values (secret, token, webhook, env, cookie, etc.).")
        
        if slot_id == "operator_idea_source_ref":
            accepted = ["local_doc_path", "repo_file_path", "screenshot_path", "official_source_url_to_be_reviewed_later", "operator_note"]
        elif slot_id in ["factual_claims", "citation_candidates", "supporting_artifacts"]:
            accepted = ["list[str]"]
        else:
            accepted = ["str"]

        slots.append({
            "slot_id": slot_id,
            "source_ref_id": "operator_idea_source_ref",
            "required": True,
            "supplied_value": supplied,
            "accepted_value_types": accepted,
            "validation_required": True,
            "verified": supplied is not None and not unsafe,
            "public_claim_allowed": False,
            "unsafe_value_detected": unsafe,
            "notes": f"Slot for {slot_id} details."
        })

    if is_empty:
        status = "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
        validation_errors.append("Fixture is empty. Operator must supply values for required slots.")
    elif unsafe_values_detected:
        status = "FIXTURE_REJECTED_UNSAFE_VALUES"
    else:
        missing_fields = [s for s in REQUIRED_SLOT_IDS if fixture_data.get(s) is None]
        if missing_fields:
            status = "FIXTURE_INCOMPLETE_MISSING_SLOTS"
            validation_errors.append(f"Fixture is missing required slots: {', '.join(missing_fields)}")
        else:
            status = "VALIDATION_SUCCESS_READY_FOR_REVIEW"

    evidence_complete = (status == "VALIDATION_SUCCESS_READY_FOR_REVIEW")
    operator_idea_source_ref_resolved = evidence_complete

    report = {
        "validation_status": status,
        "evidence_complete": evidence_complete,
        "operator_idea_source_ref_resolved": operator_idea_source_ref_resolved,
        "unsafe_values_detected": unsafe_values_detected,
        "validation_errors": validation_errors,
        "rejected_slots": rejected_slots
    }

    return report, slots


def generate_guide_markdown() -> str:
    return """# Operator Facts Intake Guide (V6 Readiness)

This guide documents what the operator (Jim) must fill to resolve the missing evidence block on the ContentOps pipeline.

## 1. What the Operator Must Fill
You must complete the fields defined in `manual_evidence_fixture_template.json` to verify the factual grounding of the content.

## 2. Accepted Evidence Shapes
- **local_doc_path**: Paths to verified local PDF or document records.
- **repo_file_path**: Relative repository paths to markdown/JSON sources.
- **screenshot_path**: Relative paths to captured confirmation images.
- **official_source_url_to_be_reviewed_later**: Web links pointing directly to primary data sources.
- **operator_note**: Written description explaining verification steps.

## 3. Rejected Unsafe Values
Under no circumstances should any slot contain:
- Webhook endpoints (e.g. `discord.com/api/webhooks`)
- Tokens or environment file variables (e.g. `.env`)
- Local browser profile references or session cookies

## 4. Safety Constraints
> [!WARNING]
> **No Fake Citations**: Do not invent fake sources, references, or metrics.
> **No Signal Service Framing**: Do not include financial advice, trading signals, or long/short recommendations.
> **Validation Only**: This lane verifies slot completeness and input hygiene; it does not validate truth or make content publishable.
"""


def generate_implementation_report_markdown(packet_status: str, validation_status: str) -> str:
    return f"""# V6 Operator Facts Intake Implementation Report

- **Task Label**: {TASK_LABEL}
- **Facts Intake Status**: {packet_status}
- **Validation Status**: {validation_status}

- **Safety Checks Pass**:
  - No secret output: `true`
  - No webhook URLs or concrete host/path patterns printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No public-postable content produced: `true`
"""


def generate_next_task_pointer_markdown() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_FAST_SHIP_OPERATING_PROFILE_AND_PROMPT_CEREMONY_REDUCTION_HEAVY_BATCH_V0`

Goal: Establish fast ship operating profile and prompt ceremony reduction standards.
"""


def materialize_operator_facts_intake(
    intake_source_path: str | Path = DEFAULT_INTAKE_SOURCE,
    registry_source_path: str | Path = DEFAULT_REGISTRY_SOURCE,
    fixture_input: dict[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    
    source_evidence_intake_packet_id = None
    try:
        intake_source = load_json(intake_source_path)
        source_evidence_intake_packet_id = intake_source.get("source_evidence_intake_packet_id")
    except Exception:
        pass

    if fixture_input is None:
        fixture_input = {slot: None for slot in REQUIRED_SLOT_IDS}

    validation_report, slots = validate_fixture(fixture_input)

    facts_intake_status = "AWAITING_OPERATOR_FACTS_AND_EVIDENCE"
    fixture_status = "EMPTY_TEMPLATE_AWAITING_OPERATOR_INPUT" if not any(fixture_input.values()) else "TEMPLATE_FILLED_AWAITING_VALIDATION"

    hasher = hashlib.sha256(f"{source_evidence_intake_packet_id}_{facts_intake_status}".encode("utf-8"))
    operator_facts_intake_packet_id = f"intake_packet_{hasher.hexdigest()[:12]}"

    # Intake Packet
    intake_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_facts_intake_packet_id": operator_facts_intake_packet_id,
        "source_evidence_intake_packet_id": source_evidence_intake_packet_id,
        "facts_intake_status": facts_intake_status,
        "fixture_status": fixture_status,
        "validation_status": validation_report["validation_status"],
        "evidence_complete": validation_report["evidence_complete"],
        "source_ref_resolved": validation_report["operator_idea_source_ref_resolved"],
        "operator_idea_source_ref_resolved": validation_report["operator_idea_source_ref_resolved"],
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "kill_switch_active": True,
        "outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "live_write_attempted": False,
        "next_recommended_task": "TASK_CONTENTOPS_V6_FAST_SHIP_OPERATING_PROFILE_AND_PROMPT_CEREMONY_REDUCTION_HEAVY_BATCH_V0"
    }

    # Source Ref Resolution Snapshot
    ref_snapshot = {
        "source_ref_id": "operator_idea_source_ref",
        "resolution_status": "MISSING_OPERATOR_SUPPLIED_EVIDENCE" if not validation_report["operator_idea_source_ref_resolved"] else "RESOLVED",
        "requires_manual_evidence": True,
        "requires_validation": True,
        "operator_idea_source_ref_resolved": validation_report["operator_idea_source_ref_resolved"],
        "unresolved_slots": [s for s in REQUIRED_SLOT_IDS if fixture_input.get(s) is None]
    }

    # Dispatch Blocker Snapshot
    blocker_snapshot = {
        "dispatch_allowed_now": False,
        "evidence_complete": validation_report["evidence_complete"],
        "kill_switch_active": True,
        "unresolved_blockers": [
            "destination_binding_incomplete",
            "evidence_incomplete",
            "kill_switch_active",
            "live_write_authorization_missing",
            "operator_approval_incomplete",
            "operator_idea_source_ref_missing",
            "outbox_creation_blocked",
            "payload_hash_incomplete",
            "safety_review_incomplete"
        ],
        "note": "Dispatch remains strictly blocked due to missing operator facts and evidence."
    }

    return intake_packet, fixture_input, validation_report, slots, ref_snapshot, blocker_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Facts Intake")
    parser.add_argument("--intake-source", default=str(DEFAULT_INTAKE_SOURCE))
    parser.add_argument("--registry-source", default=str(DEFAULT_REGISTRY_SOURCE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    intake_packet, fixture_template, report, slots, ref_snap, blocker_snap = materialize_operator_facts_intake(
        args.intake_source, args.registry_source
    )

    write_json(out_dir / "operator_facts_intake_packet.json", intake_packet)
    write_json(out_dir / "manual_evidence_fixture_template.json", fixture_template)
    write_json(out_dir / "manual_evidence_fixture_validation_report.json", report)
    write_json(out_dir / "operator_fact_slots.json", slots)
    write_json(out_dir / "source_ref_resolution_snapshot.json", ref_snap)
    write_json(out_dir / "dispatch_blocker_update_snapshot.json", blocker_snap)

    (out_dir / "operator_facts_intake_guide.md").write_text(generate_guide_markdown(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(
        generate_implementation_report_markdown(intake_packet["facts_intake_status"], report["validation_status"]),
        encoding="utf-8"
    )
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer_markdown(), encoding="utf-8")

    print(json.dumps({
        "operator_facts_intake_packet_id": intake_packet["operator_facts_intake_packet_id"],
        "facts_intake_status": intake_packet["facts_intake_status"],
        "evidence_complete": intake_packet["evidence_complete"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
