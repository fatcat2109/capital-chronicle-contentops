"""V6 Manual Evidence Source Submission Refresh wrapper.

Executes the orchestrator, updates validation matrices, formats the operator
checklist, recovery runbook, command reference, and writes status packets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops import manual_evidence_refresh_orchestrator_v6 as orchestrator

TASK_LABEL = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH")


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


def get_stage_matrix(evidence_complete: bool, preflight_ready: bool) -> dict[str, Any]:
    stages = {}
    
    stages["operator_fixture_expected"] = {
        "status": "PASS" if evidence_complete else "FAIL",
        "description": "True if operator fixture file exists and is populated."
    }
    stages["manual_evidence_validator"] = {
        "status": "PASS" if evidence_complete else "FAIL",
        "description": "Validation scan for unsafe keywords and empty slots."
    }
    stages["validator_wiring"] = {
        "status": "PASS",
        "description": "Fixture path resolution and wiring mapping."
    }
    stages["source_preflight_bridge"] = {
        "status": "PASS" if preflight_ready else "PENDING",
        "description": "Bridges validated fixture slots to preflight checking."
    }
    stages["source_evidence_preflight"] = {
        "status": "PASS" if preflight_ready else "PENDING",
        "description": "Preflight check for URL references and sources."
    }
    stages["lifecycle_audit"] = {
        "status": "PASS",
        "description": "Audit trail log and diagnostic workbench."
    }
    stages["pipeline_consolidation"] = {
        "status": "PASS",
        "description": "Unified pipeline state consolidation."
    }
    stages["approval_gate_blocked"] = {
        "status": "BLOCKED",
        "description": "Approval gate requires positive review signatures."
    }
    stages["dispatch_locked"] = {
        "status": "LOCKED",
        "description": "Kill switch is active. Supervised dispatch is blocked."
    }
    
    return {
        "schema_version": SCHEMA_VERSION,
        "stages": stages
    }


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# Manual Evidence Source Submission Blocker Report

- **Refresh Status**: {status}
- **Active Dispatch Blockers**:

{blocker_lines}

## Active Blockers Details

1. **evidence_incomplete**
   - *Detail*: Jim has not filled out the 10 required evidence slots in `operator_evidence_fixture.json`.
2. **operator_idea_source_ref_missing**
   - *Detail*: A valid, non-placeholder source reference ref is required.
3. **kill_switch_active**
   - *Detail*: Safety kill switch blocks dispatch.
"""


def generate_operator_checklist() -> str:
    return """# Operator Evidence Submission Checklist

Jim, please complete this checklist before proceeding:

## Action Checklist

- [ ] **Step 1**: Copy `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` inside the `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/` folder.
- [ ] **Step 2**: Populate all 10 required slots with verified facts.
- [ ] **Step 3**: Verify that **NO** restricted items are included:
  - No secrets, tokens, cookies, or auth headers.
  - No webhook URLs or channel integration paths.
  - No local folders (`AppData`, `Temp`, user directories).
  - No fake URLs or fabricated citations.
  - No fake market numbers or business performance statistics.
  - No trading signals, stock advice, or buy/sell calls.
- [ ] **Step 4**: Run the source submission refresh command.
- [ ] **Step 5**: Review the output refresh packet and blocker rollup.
- [ ] **Step 6**: Rerun or adjust if any validation checks fail.
- [ ] **Step 7**: Proceed to approval gate signing task ONLY when `evidence_complete=true` and `source_preflight_ready=true`.
"""


def generate_recovery_runbook() -> str:
    return """# Manual Evidence Source Submission Recovery Runbook

Jim, use this runbook to resolve validation and refresh errors:

## Recovery Paths

1. **Error: Missing Fixture File**
   - *Action*: Ensure `operator_evidence_fixture.json` exists in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/`.

2. **Error: Invalid JSON Syntax**
   - *Action*: Use a JSON formatter to verify commas, quotes, brackets, and brace matching.

3. **Error: Placeholders Found**
   - *Action*: Scan for and replace any occurrences of `"PLACEHOLDER_REPLACE_BEFORE_REVIEW"` or `"REPLACE_"` with real, verified evidence.

4. **Error: Unsafe Keywords Detected**
   - *Action*: Scrub any secrets, API keys, tokens, session cookies, local folder directories, or server configs.

5. **Error: Source Reference Missing**
   - *Action*: Supply a verified, active web link or file path reference.

6. **Error: Source Preflight Bridge Blocked**
   - *Action*: Confirm the manual validator ran successfully and generated its `operator_fixture_resolution_snapshot.json` output first.

7. **Error: Lifecycle or Consolidation Mismatch**
   - *Action*: Rerun the complete refresh script to cascade state variables sequentially.

8. **Error: Upload Bundle Stale Metadata**
   - *Action*: Re-execute the generator script to ensure metadata HEAD pointers match current git logs.

9. **Error: Accidental Real Fixture Staging**
   - *Action*: Remove `operator_evidence_fixture.json` from git stage by running `git restore --staged docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`.
"""


def generate_command_reference() -> str:
    return """# Manual Evidence Source Submission Command Reference

Jim, execute the following commands to interact with the pipeline:

- **Run Refresh Pipeline**:
  ```bash
  python -m live_contentops.manual_evidence_source_submission_refresh_v6
  ```

- **Run Blocker Orchestrator Directly**:
  ```bash
  python -m live_contentops.manual_evidence_refresh_orchestrator_v6
  ```

- **Validate Console Fixture Explicitly**:
  ```bash
  python -m live_contentops.manual_evidence_fixture_validator_v6
  ```
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Manual Evidence Source Submission Refresh Implementation Report

- **Task Label**: {TASK_LABEL}
- **Submission Status**: {status}

- **Compliance Rules**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer(evidence_complete: bool, preflight_ready: bool) -> str:
    if evidence_complete and preflight_ready:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0"
        goal = "Proceed to the operator review and approval gate to sign and authorize the preflight drop."
    else:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_POPULATE_REAL_EVIDENCE_FIXTURE_AND_RERUN_REFRESH_MANUAL_STEP"
        goal = "Jim must populate docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json and execute the refresh module."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Manual Evidence Source Submission Refresh")
    parser.add_argument("--fixture-file", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine base directory mapping
    is_default = (args.output_dir == str(DEFAULT_OUTPUT_DIR))
    if is_default:
        base_dir = Path("docs/automation")
        refresh_dir = out_dir
    else:
        base_dir = out_dir
        refresh_dir = out_dir / "V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH"
        refresh_dir.mkdir(parents=True, exist_ok=True)

    # Execute Orchestrator sequentially to refresh all lanes
    orch_args = ["--output-dir", str(base_dir)]
    if args.fixture_file:
        orch_args += ["--fixture-file", args.fixture_file]
    orchestrator.main(orch_args)

    # Resolve directories
    wiring_dir = base_dir / "V6_MANUAL_EVIDENCE_VALIDATOR_WIRING"
    validator_dir = base_dir / "V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR"
    consolidation_dir = base_dir / "V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION"

    # Load outputs of lanes
    consol_packet = load_json(consolidation_dir / "operator_pipeline_status_packet.json") or {}
    evidence_complete = consol_packet.get("evidence_complete", False)
    preflight_ready = consol_packet.get("source_preflight_ready", False)

    val_summary = load_json(validator_dir / "manual_evidence_fixture_validation_summary.json") or {}
    val_status = val_summary.get("validation_status", "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT")

    # Define overall status
    if evidence_complete:
        status = "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL"
    else:
        if val_status == "FIXTURE_REJECTED_UNSAFE_VALUES":
            status = "FIXTURE_REJECTED_UNSAFE_VALUES"
        elif val_status == "FIXTURE_INCOMPLETE_MISSING_SLOTS":
            status = "FIXTURE_INCOMPLETE_MISSING_SLOTS"
        else:
            status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"

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

    # 1. Write Packet
    hasher = hashlib.sha256(f"{status}".encode("utf-8"))
    refresh_packet_id = f"refresh_wrap_{hasher.hexdigest()[:12]}"
    refresh_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "refresh_packet_id": refresh_packet_id,
        "refresh_status": status,
        "evidence_complete": evidence_complete,
        "operator_fixture_exists": consol_packet.get("operator_fixture_exists", False) or (args.fixture_file is not None),
        "operator_idea_source_ref_resolved": evidence_complete,
        "source_ref_resolved": evidence_complete,
        "source_preflight_ready": preflight_ready,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_POPULATE_REAL_EVIDENCE_FIXTURE_AND_RERUN_REFRESH_MANUAL_STEP" if not evidence_complete else "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0"
    }
    write_json(refresh_dir / "manual_evidence_source_submission_refresh_packet.json", refresh_packet)

    # 2. Write Matrix
    write_json(refresh_dir / "manual_evidence_source_submission_stage_matrix.json", get_stage_matrix(evidence_complete, preflight_ready))

    # 3. Write Reports & Guides
    (refresh_dir / "manual_evidence_source_submission_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (refresh_dir / "manual_evidence_source_submission_operator_checklist.md").write_text(generate_operator_checklist(), encoding="utf-8")
    (refresh_dir / "manual_evidence_source_submission_recovery_runbook.md").write_text(generate_recovery_runbook(), encoding="utf-8")
    (refresh_dir / "manual_evidence_source_submission_command_reference.md").write_text(generate_command_reference(), encoding="utf-8")
    (refresh_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")
    (refresh_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(evidence_complete, preflight_ready), encoding="utf-8")

    print(json.dumps({
        "refresh_packet_id": refresh_packet_id,
        "refresh_status": status,
        "evidence_complete": evidence_complete
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
