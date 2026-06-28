"""V6 Operator Approval Gate.

Evaluates delegated evidence candidate-readiness, writes approval packets,
review checklists, blocker reports, and signature templates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
NEXT_PAYLOAD_TASK = "TASK_CONTENTOPS_V6_REPAIR_PAYLOAD_PREVIEW_HASH_PLACEHOLDER_AND_SCOPE_CONTAMINATION_V0"
NEXT_APPROVAL_TASK = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE")


def write_json(path: str | Path, data: Any) -> None:
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


def packet_has_valid_payload_hash(packet: dict[str, Any]) -> bool:
    payload_hash = packet.get("payload_hash")
    if packet.get("payload_hash_created") is not True:
        return False
    if packet.get("exact_payload_preview_created") is not True:
        return False
    if packet.get("payload_preview_status") != "READY_FOR_OPERATOR_REVIEW":
        return False
    if not isinstance(payload_hash, str) or len(payload_hash) < 32:
        return False
    return "placeholder" not in json.dumps(packet, sort_keys=True).lower()


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# Operator Approval Gate Blocker Report

- **Approval Gate Status**: {status}
- **Active Dispatch Blockers**:

{blocker_lines}

## Active Blockers Details

1. **operator_approval_incomplete**
   - *Detail*: Jim must fill in the approval signature template to sign off on preflight candidate review.
2. **payload_hash_incomplete**
   - *Detail*: Exact safe review payload and deterministic hash must exist before approval signature binding can advance.
3. **kill_switch_active**
   - *Detail*: Safety kill switch blocks dispatch.
"""


def generate_approval_runbook() -> str:
    return """# Operator Approval Gate Runbook

Jim, follow these steps to sign off and approve evidence candidate review intent:

## Approval Steps

- [ ] **Step 1**: Open `operator_approval_signature_template.json` in `docs/automation/V6_OPERATOR_APPROVAL_GATE/`.
- [ ] **Step 2**: Fill in your operator ID:
  - `"operator_id": "JIM_OPERATOR"`
- [ ] **Step 3**: Update the approval decision to APPROVED:
  - `"approval_decision": "APPROVED"`
- [ ] **Step 4**: Keep `valid_for_dispatch=false` (do NOT mark dispatch-valid in this lane). Fill only operator identity and review decision intent.
- [ ] **Step 5**: Save the file.
- [ ] **Step 6**: Proceed to `TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0` only after exact payload preview and payload hash controls exist.
- [ ] **Step 7**: Note that dispatch validity can only be evaluated after payload hash, operator signature binding, destination binding, approval ledger, outbox, and dispatch-readiness gates exist.
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Operator Approval Gate Implementation Report

- **Task Label**: {TASK_LABEL}
- **Approval Status**: {status}

- **Compliance Rules**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer(evidence_complete: bool, payload_hash_created: bool) -> str:
    if evidence_complete and payload_hash_created:
        next_task = NEXT_APPROVAL_TASK
        goal = "Use exact payload preview and deterministic hash as review controls for approval gate progression."
    elif evidence_complete:
        next_task = NEXT_PAYLOAD_TASK
        goal = "Create exact safe payload preview and deterministic non-placeholder payload hash."
    else:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_AND_DELEGATED_EVIDENCE_ROLLUP_REPAIR_HEAVY_BATCH_V0"
        goal = "Re-run approval gate check once evidence console is complete."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Approval Gate")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--fixture-file", default=None)
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    is_default = args.output_dir == str(DEFAULT_OUTPUT_DIR)
    if is_default:
        gate_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        gate_dir = out_dir / "V6_OPERATOR_APPROVAL_GATE"
        gate_dir.mkdir(parents=True, exist_ok=True)
        base_automation_dir = out_dir

    evidence_complete = False
    source_preflight_ready = False

    delegated_result = load_json(base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json")
    if delegated_result:
        evidence_complete = delegated_result.get("evidence_complete", False)
        source_preflight_ready = delegated_result.get("source_preflight_ready", False)

    if evidence_complete and source_preflight_ready:
        status = "AWAITING_OPERATOR_SIGNATURE"
    else:
        status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"

    blockers = [
        "destination_binding_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "payload_hash_incomplete",
        "safety_review_incomplete",
        "outbox_creation_blocked"
    ]

    payload_packet_path = base_automation_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json"
    payload_packet = load_json(payload_packet_path) or {}
    payload_hash_created = packet_has_valid_payload_hash(payload_packet)
    payload_hash_ref = payload_packet.get("payload_hash") if payload_hash_created else None

    gate_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "approval_gate_status": status,
        "evidence_complete": evidence_complete,
        "source_preflight_ready": source_preflight_ready,
        "source_ref_resolved": evidence_complete,
        "operator_idea_source_ref_resolved": evidence_complete,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "payload_hash_created": payload_hash_created,
        "payload_hash_reference": payload_hash_ref,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": NEXT_APPROVAL_TASK if payload_hash_created else (NEXT_PAYLOAD_TASK if evidence_complete else TASK_LABEL)
    }
    write_json(gate_dir / "operator_approval_gate_packet.json", gate_packet)

    review_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "evidence_summary_ref": "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json",
        "source_map_ref": "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json",
        "refresh_result_ref": "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json",
        "review_required": True,
        "operator_signature_required": True,
        "dispatch_not_authorized": True,
        "live_write_not_authorized": True,
        "exact_approved_content_unavailable": True
    }
    write_json(gate_dir / "operator_approval_review_packet.json", review_packet)

    signature_template = {
        "operator_id": "PLACEHOLDER_OPERATOR_ID",
        "approval_decision": "PENDING",
        "payload_hash": None,
        "valid_for_dispatch": False,
        "expires_at": None,
        "revoked": False
    }
    write_json(gate_dir / "operator_approval_signature_template.json", signature_template)

    (gate_dir / "operator_approval_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (gate_dir / "operator_approval_runbook.md").write_text(generate_approval_runbook(), encoding="utf-8")
    (gate_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")
    (gate_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(evidence_complete, payload_hash_created), encoding="utf-8")

    print(json.dumps({
        "approval_gate_status": status,
        "evidence_complete": evidence_complete,
        "source_preflight_ready": source_preflight_ready
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
