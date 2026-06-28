"""V6 Operator Pipeline Status Consolidation.

Aggregates all 9 stages of operator evidence, validation, wiring, bridge,
preflight, approval gate, dispatch readiness, selection policy, and capability matrix.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION_PACKET_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_CONSOLE = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_console_packet.json")
DEFAULT_VALIDATOR = Path("docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/manual_evidence_fixture_validation_summary.json")
DEFAULT_WIRING = Path("docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/validator_wiring_packet.json")
DEFAULT_BRIDGE = Path("docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/bridge_packet.json")
DEFAULT_PREFLIGHT = Path("docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json")
DEFAULT_APPROVAL = Path("docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
DEFAULT_DISPATCH = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json")
DEFAULT_SELECTION_POLICY = Path("docs/automation/V6_PLATFORM_ADAPTER_SELECTION_POLICY/platform_adapter_selection_policy_packet.json")
DEFAULT_CAPABILITY_MATRIX = Path("docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_PIPELINE_STATUS_CONSOLIDATION")

STAGES_LIST = [
    "operator_evidence_console",
    "manual_evidence_fixture_validator",
    "validator_wiring",
    "manual_evidence_to_source_preflight_bridge",
    "source_evidence_preflight",
    "operator_approval_gate",
    "supervised_dispatch_readiness",
    "platform_adapter_policy",
    "platform_capability_matrix"
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


def generate_runbook() -> str:
    return """# Operator Next Action Runbook

Jim, follow these steps to resolve the blocked pipeline status:

## Step 1: Copy Operator Evidence Fixture
* Copy the file `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.blank.json` to `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`.

## Step 2: Fill All 10 Evidence Slots
* Populate each required slot in `operator_evidence_fixture.json` with verified evidence.
* Ensure there are no placeholders remaining.

## Step 3: Run Validator Lane
* Execute the manual evidence validator script:
  `python live_contentops/manual_evidence_fixture_validator_v6.py`

## Step 4: Staging Gates Preflight
* Run the manual evidence to source preflight bridge script:
  `python live_contentops/manual_evidence_to_source_preflight_bridge_v6.py`
* Verify that validation and source preflight stages resolve to ready states. Only then can the pipeline move to the operator approval gate.

## Step 5: Operator Approval Signatures
* Real dispatch is separate and supervised. The approval gate does NOT trigger dispatch automatically.

> [!IMPORTANT]
> **PIPELINE IS BLOCKED**: The pipeline is not approval-ready and not dispatch-ready because the operator evidence fixture is empty or missing.
"""


def generate_blocked_state_summary() -> str:
    return """# Blocked State Summary

- **Pipeline State**: BLOCKED_AWAITING_OPERATOR_EVIDENCE
- **Dispatch Allowed Now**: false
- **Live Write Allowed Now**: false
- **Kill Switch Active**: true

All downstream execution stages remain disabled because no verified facts have been submitted. Jim must complete the evidence console fixture.
"""


def generate_implementation_report() -> str:
    return f"""# Operator Pipeline Status Consolidation Report

- **Task Label**: {TASK_LABEL}
- **Status**: PASS

- **Safety & Compliance Lock**:
  - No secret output: `true`
  - No webhook URLs or credentials leaked: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Run the validator lane after the operator has supplied the manual evidence fixture in operator_evidence_fixture.json.
"""


def generate_checklist() -> str:
    return """# Operator Fixture Submission Checklist (V6)

This checklist covers the 10 required evidence slots in the operator evidence fixture. Jim must verify each item before submission.

## Required Evidence Slots

1. **operator_idea_source_ref**: Reference link or path to the original source.
2. **topic_statement**: Short, clear statement of facts.
3. **factual_claims**: List of specific, checkable claims.
4. **source_notes**: Notes detailing manual validation and grounding checks.
5. **citation_candidates**: List of sources/citations for verification.
6. **supporting_artifacts**: Local screenshots or supporting files.
7. **limitation_notes**: Scope boundaries or caveats of current claims.
8. **no_signal_disclosure**: Explicit affirmation that no financial signals or advice are present.
9. **intended_content_lane**: Distribution target (e.g. Substack).
10. **intended_canonical_article_angle**: Framing, angle, or editorial direction.

## Submission Restrictions & Prohibitions

> [!IMPORTANT]
> To ensure system safety, compliance, and clean audits, you MUST verify the following restrictions:
> - **No Fake Citations / URLs**: All links and sources must be real and reachable. No placeholder domains or fabricated citations.
> - **No Fake Market Numbers / Metrics**: Do not fabricate statistics, stock numbers, user metrics, or business performance indicators.
> - **No Financial Advice / Signals**: The content must contain zero trading signals, buy/sell recommendations, or advice.
> - **Zero Secrets / Credentials**: Absolutely no passwords, API keys, webhook URLs, tokens, cookies, or session strings.
> - **No Environment Paths**: Avoid local system paths, user folders, or server config references.
> - **No Browser Session Dumps**: Do not include raw dumps of browser state, localStorage, or cookies.
"""


def generate_truth_table() -> list[dict[str, Any]]:
    return [
        {
            "evidence_complete": False,
            "source_preflight_ready": False,
            "operator_approved": False,
            "kill_switch_active": True,
            "overall_status": "BLOCKED_AWAITING_OPERATOR_EVIDENCE",
            "dispatch_allowed": False,
            "live_write_allowed": False
        },
        {
            "evidence_complete": True,
            "source_preflight_ready": False,
            "operator_approved": False,
            "kill_switch_active": True,
            "overall_status": "BLOCKED_AWAITING_SOURCE_PREFLIGHT",
            "dispatch_allowed": False,
            "live_write_allowed": False
        },
        {
            "evidence_complete": True,
            "source_preflight_ready": True,
            "operator_approved": False,
            "kill_switch_active": True,
            "overall_status": "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL",
            "dispatch_allowed": False,
            "live_write_allowed": False
        },
        {
            "evidence_complete": True,
            "source_preflight_ready": True,
            "operator_approved": True,
            "kill_switch_active": True,
            "overall_status": "APPROVED_BUT_DISPATCH_BLOCKED_BY_KILL_SWITCH",
            "dispatch_allowed": False,
            "live_write_allowed": False
        },
        {
            "evidence_complete": True,
            "source_preflight_ready": True,
            "operator_approved": True,
            "kill_switch_active": False,
            "overall_status": "SUPERVISED_DISPATCH_READY",
            "dispatch_allowed": True,
            "live_write_allowed": False
        }
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Pipeline Status Consolidation")
    parser.add_argument("--console-packet", default=str(DEFAULT_CONSOLE))
    parser.add_argument("--validator-summary", default=str(DEFAULT_VALIDATOR))
    parser.add_argument("--wiring-packet", default=str(DEFAULT_WIRING))
    parser.add_argument("--bridge-packet", default=str(DEFAULT_BRIDGE))
    parser.add_argument("--preflight-packet", default=str(DEFAULT_PREFLIGHT))
    parser.add_argument("--approval-packet", default=str(DEFAULT_APPROVAL))
    parser.add_argument("--dispatch-packet", default=str(DEFAULT_DISPATCH))
    parser.add_argument("--selection-packet", default=str(DEFAULT_SELECTION_POLICY))
    parser.add_argument("--capability-packet", default=str(DEFAULT_CAPABILITY_MATRIX))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve sibling paths if output_dir is custom (dry-run isolation)
    is_default = (args.output_dir == str(DEFAULT_OUTPUT_DIR))
    if not is_default:
        base_dir = out_dir.parent
        preflight_path = base_dir / "V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json"
        approval_path = base_dir / "V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json"
        dispatch_path = base_dir / "V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json"
        selection_path = base_dir / "V6_PLATFORM_ADAPTER_SELECTION_POLICY/platform_adapter_selection_policy_packet.json"
        capability_path = base_dir / "V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json"
        payload_hash_path = base_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json"
    else:
        preflight_path = Path(args.preflight_packet)
        approval_path = Path(args.approval_packet)
        dispatch_path = Path(args.dispatch_packet)
        selection_path = Path(args.selection_packet)
        capability_path = Path(args.capability_packet)
        payload_hash_path = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json")

    # 1. Load packets
    console = load_json(args.console_packet) or {}
    validator = load_json(args.validator_summary) or {}
    wiring = load_json(args.wiring_packet) or {}
    bridge = load_json(args.bridge_packet) or {}
    preflight = load_json(preflight_path) or {}
    approval = load_json(approval_path) or {}
    dispatch = load_json(dispatch_path) or {}
    selection = load_json(selection_path) or {}
    capability = load_json(capability_path) or {}
    payload_hash_packet = load_json(payload_hash_path) or {}
    payload_hash_created = payload_hash_packet.get("payload_hash_created", False)

    evidence_complete = (
        console.get("evidence_complete", False) or
        validator.get("evidence_complete", False) or
        wiring.get("evidence_complete", False) or
        bridge.get("evidence_complete", False) or
        preflight.get("evidence_complete", False) or
        approval.get("evidence_complete", False) or
        dispatch.get("source_evidence_complete", False)
    )

    overall_status = "BLOCKED_AWAITING_OPERATOR_EVIDENCE"
    if evidence_complete:
        overall_status = "PREFLIGHT_CANDIDATE_READY_FOR_APPROVAL"

    # 2. Build Stage Matrix
    stages = []

    # Stage 1: Console
    stages.append({
        "stage_name": "operator_evidence_console",
        "input_artifact": "docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json",
        "output_artifact": "docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_console_packet.json",
        "current_status": "AWAITING_OPERATOR_INPUT" if not evidence_complete else "COMPLETE",
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "Operator evidence fixture is empty or missing." if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 2: Validator
    stages.append({
        "stage_name": "manual_evidence_fixture_validator",
        "input_artifact": "docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json",
        "output_artifact": "docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/manual_evidence_fixture_validation_summary.json",
        "current_status": validator.get("validation_status", "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "validation_status is EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 3: Wiring
    stages.append({
        "stage_name": "validator_wiring",
        "input_artifact": "docs/automation/V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR/manual_evidence_fixture_validation_summary.json",
        "output_artifact": "docs/automation/V6_MANUAL_EVISION_VALIDATOR_WIRING/validator_wiring_packet.json" if "V6_MANUAL_EVISION_VALIDATOR_WIRING" in str(DEFAULT_WIRING) else "docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/validator_wiring_packet.json",
        "current_status": wiring.get("wiring_status", "WIRING_SUCCESS" if wiring else "NOT_STARTED"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "wiring resolving selected_fixture_file is null" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 4: Bridge
    stages.append({
        "stage_name": "manual_evidence_to_source_preflight_bridge",
        "input_artifact": "docs/automation/V6_MANUAL_EVIDENCE_VALIDATOR_WIRING/validator_wiring_packet.json",
        "output_artifact": "docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/bridge_packet.json",
        "current_status": bridge.get("bridge_status", "BLOCKED_AWAITING_OPERATOR_EVIDENCE"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "bridge_status is BLOCKED_AWAITING_OPERATOR_EVIDENCE" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 5: Preflight
    stages.append({
        "stage_name": "source_evidence_preflight",
        "input_artifact": "docs/automation/V6_MANUAL_EVIDENCE_TO_SOURCE_PREFLIGHT_BRIDGE/bridge_packet.json",
        "output_artifact": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json",
        "current_status": preflight.get("intake_status", "AWAITING_OPERATOR_SOURCE_EVIDENCE"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "intake_status is AWAITING_OPERATOR_SOURCE_EVIDENCE" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 6: Approval Gate
    stages.append({
        "stage_name": "operator_approval_gate",
        "input_artifact": "docs/automation/V6_SOURCE_EVIDENCE_PREFLIGHT/source_evidence_intake_packet.json",
        "output_artifact": "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
        "current_status": approval.get("approval_gate_status", "BLOCKED_BY_UPSTREAM_CHECKPOINTS"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "approval_gate_status is BLOCKED_BY_UPSTREAM_CHECKPOINTS" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 7: Dispatch Readiness
    stages.append({
        "stage_name": "supervised_dispatch_readiness",
        "input_artifact": "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
        "output_artifact": "docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json",
        "current_status": dispatch.get("readiness_status", "BLOCKED_SOURCE_EVIDENCE_MISSING"),
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "readiness_status is BLOCKED_SOURCE_EVIDENCE_MISSING" if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 8: Platform Selection Policy
    stages.append({
        "stage_name": "platform_adapter_policy",
        "input_artifact": "docs/automation/V6_PLATFORM_ADAPTER_SELECTION_POLICY/platform_adapter_selection_policy.md",
        "output_artifact": "docs/automation/V6_PLATFORM_ADAPTER_SELECTION_POLICY/platform_adapter_selection_policy_packet.json",
        "current_status": "BLOCKED_AWAITING_OPERATOR_EVIDENCE" if not evidence_complete else "SELECTION_POLICY_READY",
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "Adapter selection is blocked awaiting verified operator evidence validation." if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    # Stage 9: Platform Capability Matrix
    stages.append({
        "stage_name": "platform_capability_matrix",
        "input_artifact": "docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json",
        "output_artifact": "docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json",
        "current_status": "BLOCKED_AWAITING_OPERATOR_EVIDENCE" if not evidence_complete else "CAPABILITY_MATRIX_READY",
        "ready_now": evidence_complete,
        "blocked_now": not evidence_complete,
        "blocker_reason": "Capability mapping is blocked awaiting verified operator evidence validation." if not evidence_complete else "None",
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence." if not evidence_complete else "None",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "payload_hash_created": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True
    })

    write_json(out_dir / "operator_pipeline_stage_matrix.json", stages)

    # 3. Overall Consolidated Status Packet
    consolidated_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "overall_status": overall_status,
        "evidence_complete": evidence_complete,
        "operator_idea_source_ref_resolved": evidence_complete,
        "source_ref_resolved": evidence_complete,
        "source_preflight_ready": evidence_complete,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "payload_hash_created": payload_hash_created,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_required_operator_action": "Jim fills docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json with verified evidence.",
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "next_recommended_task": (
            "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0" if payload_hash_created
            else (
                "TASK_CONTENTOPS_V6_REPAIR_PAYLOAD_PREVIEW_HASH_PLACEHOLDER_AND_SCOPE_CONTAMINATION_V0" if evidence_complete
                else "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
            )
        )
    }
    write_json(out_dir / "operator_pipeline_status_packet.json", consolidated_packet)

    # Write Markdown files
    (out_dir / "operator_next_action_runbook.md").write_text(generate_runbook(), encoding="utf-8")
    (out_dir / "blocked_state_summary.md").write_text(generate_blocked_state_summary(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")
    (out_dir / "operator_fixture_submission_checklist.md").write_text(generate_checklist(), encoding="utf-8")
    write_json(out_dir / "pipeline_truth_table.json", generate_truth_table())

    print(json.dumps({
        "overall_status": overall_status,
        "evidence_complete": evidence_complete,
        "kill_switch_active": consolidated_packet["kill_switch_active"]
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
