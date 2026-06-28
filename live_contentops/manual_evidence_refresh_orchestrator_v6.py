"""V6 Manual Evidence Refresh Orchestrator.

Sequentially executes the 8 pipeline lanes, ensures all intermediate outputs
are refreshed in the correct dependency order, and builds a blocker rollup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops import scoped_network_policy_v6 as network_scope
from live_contentops import operator_evidence_intake_studio_v6 as intake_studio
from live_contentops import operator_evidence_console_v6 as console
from live_contentops import manual_evidence_fixture_validator_v6 as validator
from live_contentops import manual_evidence_to_source_preflight_bridge_v6 as bridge
from live_contentops import operator_evidence_fixture_lifecycle_v6 as lifecycle
from live_contentops import operator_pipeline_status_consolidation_v6 as consolidation
from live_contentops import project_sources_upload_bundle_v6 as upload_bundle

TASK_LABEL = "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR_AND_BLOCKED_PIPELINE_ROLLUP_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR")

EXECUTION_ORDER = [
    "scoped_network_policy_v6",
    "operator_evidence_intake_studio_v6",
    "operator_evidence_console_v6",
    "manual_evidence_fixture_validator_v6",
    "manual_evidence_to_source_preflight_bridge_v6",
    "operator_evidence_fixture_lifecycle_v6",
    "operator_pipeline_status_consolidation_v6",
    "project_sources_upload_bundle_v6"
]


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


def generate_blocker_report(overall_status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# Manual Evidence Refresh Blocker Report

- **Overall Pipeline Status**: {overall_status}
- **Active Dispatch Blockers**:

{blocker_lines}

## Blocker Descriptions

1. **destination_binding_incomplete**
   - *Detail*: No target endpoint or destination has been authorized for write operations.
2. **evidence_incomplete**
   - *Detail*: Required evidence slots are empty or contain default placeholders.
3. **operator_idea_source_ref_missing**
   - *Detail*: Jim has not supplied a verified source reference in the console fixture.
4. **kill_switch_active**
   - *Detail*: Safe-mode override is active, blocking all outbound network publish requests.
"""


def generate_operator_runbook() -> str:
    return """# Manual Evidence Refresh Operator Runbook

Jim, follow this workflow to refresh the evidence pipeline:

## Step-by-Step Instructions

1. **Step 1: Populate the console fixture**
   - Copy `operator_evidence_fixture.blank.json` to `operator_evidence_fixture.json` in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/`.
   - Complete all 10 required factual slots (refer to `operator_evidence_fill_instructions.md` for guidance).

2. **Step 2: Run the Orchestrator**
   - Execute: `python live_contentops/manual_evidence_refresh_orchestrator_v6.py`

3. **Step 3: Review the Rollup**
   - Verify `manual_evidence_refresh_rollup.json` inside the orchestrator directory.
   - If `evidence_complete` is `true` and the rollup status is `PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL`, proceed to the operator approval gate lane.

4. **Step 4: Approval & Dispatch**
   - Signing approval does not trigger auto-dispatch. All publishing actions remain supervised.
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Manual Evidence Refresh Orchestrator Implementation Report

- **Task Label**: {TASK_LABEL}
- **Orchestrator Status**: {status}

- **Compliance Rules**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Manual Evidence Refresh Orchestrator")
    parser.add_argument("--fixture-file", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine base directory mapping
    is_default = (args.output_dir == str(DEFAULT_OUTPUT_DIR))
    if is_default:
        base_dir = Path("docs/automation")
        orchestrator_dir = out_dir
    else:
        base_dir = out_dir
        orchestrator_dir = out_dir / "V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR"
        orchestrator_dir.mkdir(parents=True, exist_ok=True)

    # Set up subdirectories
    network_policy_dir = base_dir / "V6_NETWORK_SCOPE_POLICY"
    intake_studio_dir = base_dir / "V6_OPERATOR_EVIDENCE_INTAKE_STUDIO"
    console_dir = base_dir / "V6_OPERATOR_EVIDENCE_CONSOLE"
    validator_dir = base_dir / "V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR"
    wiring_dir = base_dir / "V6_MANUAL_EVIDENCE_VALIDATOR_WIRING"
    bridge_dir = base_dir / "V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE"
    lifecycle_dir = base_dir / "V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE"
    consolidation_dir = base_dir / "V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION"
    upload_bundle_dir = base_dir / "V6_PROJECT_SOURCES_UPLOAD_BUNDLE"

    # 1. Execute Lanes Sequentially
    executed = []
    failed = []
    skipped = []

    # Lane 1: scoped_network_policy_v6
    try:
        network_scope.main(["--output-dir", str(network_policy_dir)])
        executed.append("scoped_network_policy_v6")
    except Exception as e:
        failed.append(f"scoped_network_policy_v6: {e}")

    # Lane 2: operator_evidence_intake_studio_v6
    try:
        intake_args = ["--output-dir", str(intake_studio_dir)]
        if args.fixture_file:
            intake_args += ["--fixture-file", args.fixture_file]
        intake_studio.main(intake_args)
        executed.append("operator_evidence_intake_studio_v6")
    except Exception as e:
        failed.append(f"operator_evidence_intake_studio_v6: {e}")

    # Lane 3: operator_evidence_console_v6
    try:
        console.main(["--output-dir", str(console_dir)])
        executed.append("operator_evidence_console_v6")
    except Exception as e:
        failed.append(f"operator_evidence_console_v6: {e}")

    # Lane 4: manual_evidence_fixture_validator_v6
    try:
        val_args = ["--output-dir", str(validator_dir), "--wiring-output-dir", str(wiring_dir)]
        # Check precedence if no CLI override
        fixture_override = args.fixture_file
        if not fixture_override and not is_default:
            # Check if console fixture was created in the console_dir
            console_fixture_path = console_dir / "operator_evidence_fixture.json"
            if console_fixture_path.exists():
                fixture_override = str(console_fixture_path)
        if fixture_override:
            val_args += ["--fixture-file", fixture_override]
        validator.main(val_args)
        executed.append("manual_evidence_fixture_validator_v6")
    except Exception as e:
        failed.append(f"manual_evidence_fixture_validator_v6: {e}")

    # Lane 5: manual_evidence_to_source_preflight_bridge_v6
    try:
        bridge.main([
            "--wiring-packet", str(wiring_dir / "validator_wiring_packet.json"),
            "--resolution-snapshot", str(wiring_dir / "operator_fixture_resolution_snapshot.json"),
            "--validation-summary", str(validator_dir / "manual_evidence_fixture_validation_summary.json"),
            "--output-dir", str(bridge_dir)
        ])
        executed.append("manual_evidence_to_source_preflight_bridge_v6")
    except Exception as e:
        failed.append(f"manual_evidence_to_source_preflight_bridge_v6: {e}")

    # Lane 6: operator_evidence_fixture_lifecycle_v6
    try:
        life_args = ["--output-dir", str(lifecycle_dir)]
        if fixture_override:
            life_args += ["--fixture-file", fixture_override]
        lifecycle.main(life_args)
        executed.append("operator_evidence_fixture_lifecycle_v6")
    except Exception as e:
        failed.append(f"operator_evidence_fixture_lifecycle_v6: {e}")

    # Lane 7: operator_pipeline_status_consolidation_v6
    try:
        consolidation.main([
            "--console-packet", str(console_dir / "operator_evidence_console_packet.json"),
            "--validator-summary", str(validator_dir / "manual_evidence_fixture_validation_summary.json"),
            "--wiring-packet", str(wiring_dir / "validator_wiring_packet.json"),
            "--bridge-packet", str(bridge_dir / "bridge_packet.json"),
            "--output-dir", str(consolidation_dir)
        ])
        executed.append("operator_pipeline_status_consolidation_v6")
    except Exception as e:
        failed.append(f"operator_pipeline_status_consolidation_v6: {e}")

    # Lane 8: project_sources_upload_bundle_v6
    try:
        upload_bundle.main(["--output-dir", str(upload_bundle_dir)])
        executed.append("project_sources_upload_bundle_v6")
    except Exception as e:
        failed.append(f"project_sources_upload_bundle_v6: {e}")

    # 2. Gather Status & Compile Rollup
    consol_packet = load_json(consolidation_dir / "operator_pipeline_status_packet.json") or {}
    evidence_complete = consol_packet.get("evidence_complete", False)
    
    val_summary = load_json(validator_dir / "manual_evidence_fixture_validation_summary.json") or {}
    val_status = val_summary.get("validation_status", "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT")

    overall_status = consol_packet.get("overall_status", "BLOCKED_AWAITING_OPERATOR_EVIDENCE")
    if not evidence_complete:
        if val_status == "FIXTURE_REJECTED_UNSAFE_VALUES":
            overall_status = "FIXTURE_REJECTED_UNSAFE_VALUES"
        elif val_status == "FIXTURE_INCOMPLETE_MISSING_SLOTS":
            overall_status = "FIXTURE_INCOMPLETE_MISSING_SLOTS"
        else:
            overall_status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"

    # Read active blockers
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

    # Unique orchestrator packet ID
    hasher = hashlib.sha256(f"{overall_status}_{evidence_complete}".encode("utf-8"))
    orchestrator_packet_id = f"orchestrator_{hasher.hexdigest()[:12]}"

    orchestrator_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "orchestrator_packet_id": orchestrator_packet_id,
        "orchestrator_status": overall_status,
        "evidence_complete": evidence_complete,
        "operator_fixture_exists": consol_packet.get("operator_fixture_exists", False) or (args.fixture_file is not None),
        "source_preflight_ready": consol_packet.get("source_preflight_ready", False),
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    }
    write_json(orchestrator_dir / "manual_evidence_refresh_orchestrator_packet.json", orchestrator_packet)

    # Execution Order
    write_json(orchestrator_dir / "manual_evidence_refresh_execution_order.json", {
        "schema_version": SCHEMA_VERSION,
        "execution_order": EXECUTION_ORDER
    })

    # Blocker Rollup
    rollup = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "orchestrator_status": overall_status,
        "evidence_complete": evidence_complete,
        "operator_fixture_exists": orchestrator_packet["operator_fixture_exists"],
        "current_blockers": sorted(blockers),
        "executed_lanes": executed,
        "skipped_lanes": skipped,
        "failed_lanes": failed,
        "generated_artifacts": [
            "manual_evidence_refresh_orchestrator_packet.json",
            "manual_evidence_refresh_execution_order.json",
            "manual_evidence_refresh_rollup.json",
            "manual_evidence_refresh_blocker_report.md",
            "manual_evidence_refresh_operator_runbook.md",
            "implementation_report.md",
            "next_task_pointer.md"
        ],
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence.",
        "next_recommended_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "final_head_requires_post_push_audit": True
    }
    write_json(orchestrator_dir / "manual_evidence_refresh_rollup.json", rollup)

    # 3. Write markdown reports
    (orchestrator_dir / "manual_evidence_refresh_blocker_report.md").write_text(generate_blocker_report(overall_status, blockers), encoding="utf-8")
    (orchestrator_dir / "manual_evidence_refresh_operator_runbook.md").write_text(generate_operator_runbook(), encoding="utf-8")
    (orchestrator_dir / "implementation_report.md").write_text(generate_implementation_report(overall_status), encoding="utf-8")
    (orchestrator_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")

    print(json.dumps({
        "orchestrator_packet_id": orchestrator_packet_id,
        "orchestrator_status": overall_status,
        "evidence_complete": evidence_complete,
        "failed_lanes_count": len(failed)
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
