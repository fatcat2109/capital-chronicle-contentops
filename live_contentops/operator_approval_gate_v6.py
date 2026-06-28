"""V6 Operator Approval Gate.

Evaluates delegated evidence candidate-readiness, writes approval packets,
review checklists, blocker reports, and signature templates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_AND_DELEGATED_EVIDENCE_ROLLUP_REPAIR_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

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


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# Operator Approval Gate Blocker Report

- **Approval Gate Status**: {status}
- **Active Dispatch Blockers**:

{blocker_lines}

## Active Blockers Details

1. **operator_approval_incomplete**
   - *Detail*: Jim must fill in the approval signature template to sign off on the preflight drop.
2. **payload_hash_incomplete**
   - *Detail*: The final drop payload must be hashed for integrity before dispatch.
3. **kill_switch_active**
   - *Detail*: Safety kill switch blocks dispatch.
"""


def generate_approval_runbook() -> str:
    return """# Operator Approval Gate Runbook

Jim, follow these steps to sign off and approve the evidence candidate:

## Approval Steps

- [ ] **Step 1**: Open `operator_approval_signature_template.json` in `docs/automation/V6_OPERATOR_APPROVAL_GATE/`.
- [ ] **Step 2**: Fill in your operator ID:
  - `"operator_id": "JIM_OPERATOR"`
- [ ] **Step 3**: Update the approval decision to APPROVED:
  - `"approval_decision": "APPROVED"`
- [ ] **Step 4**: Confirm that `valid_for_dispatch` is updated to true if authorized.
- [ ] **Step 5**: Save the file.
- [ ] **Step 6**: Execute the approval validation check.
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


def generate_next_task_pointer(evidence_complete: bool) -> str:
    if evidence_complete:
        next_task = "TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_V0"
        goal = "Generate the final drop payload preview and verify its integrity hash."
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

    # Resolve output subdirectories
    is_default = (args.output_dir == str(DEFAULT_OUTPUT_DIR))
    if is_default:
        gate_dir = out_dir
    else:
        gate_dir = out_dir / "V6_OPERATOR_APPROVAL_GATE"
        gate_dir.mkdir(parents=True, exist_ok=True)

    # Determine candidate readiness
    evidence_complete = False
    source_preflight_ready = False

    # Check delegated refresh result
    delegated_result = load_json("docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json")
    if delegated_result:
        evidence_complete = delegated_result.get("evidence_complete", False)
        source_preflight_ready = delegated_result.get("source_preflight_ready", False)

    # Check local console fixture on disk or if explicitly passed
    fixture_path = args.fixture_file or "docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json"
    if Path(fixture_path).exists():
        evidence_complete = True
        source_preflight_ready = True

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

    # 1. operator_approval_gate_packet.json
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
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": "TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_V0" if evidence_complete else TASK_LABEL
    }
    write_json(gate_dir / "operator_approval_gate_packet.json", gate_packet)

    # 2. operator_approval_review_packet.json
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

    # 3. operator_approval_signature_template.json
    signature_template = {
        "operator_id": "PLACEHOLDER_OPERATOR_ID",
        "approval_decision": "PENDING",
        "payload_hash": None,
        "valid_for_dispatch": False,
        "expires_at": None,
        "revoked": False
    }
    write_json(gate_dir / "operator_approval_signature_template.json", signature_template)

    # 4. operator_approval_blocker_report.md
    (gate_dir / "operator_approval_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")

    # 5. operator_approval_runbook.md
    (gate_dir / "operator_approval_runbook.md").write_text(generate_approval_runbook(), encoding="utf-8")

    # 6. reports & pointer
    (gate_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")
    (gate_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(evidence_complete), encoding="utf-8")

    print(json.dumps({
        "approval_gate_status": status,
        "evidence_complete": evidence_complete,
        "source_preflight_ready": source_preflight_ready
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
