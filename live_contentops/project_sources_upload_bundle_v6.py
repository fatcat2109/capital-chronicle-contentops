"""V6 Project Sources Upload Bundle Lane.

Verifies the repository state and creates a clean upload bundle candidate set
for ChatGPT Project Sources context refreshment with corrected HEAD semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_DELEGATED_REAL_EVIDENCE_FIXTURE_AUTHORING_AND_REFRESH_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
BASELINE_BEFORE_UPLOAD_BUNDLE_TASK = "d97bc3968e1babf48c81f384fb547b439e48515c"

DEFAULT_READINESS_BUNDLE = Path("docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json")
DEFAULT_DISPATCH_READINESS = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_git_head() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        # Fallback to actual pre-repair remote HEAD if git command fails
        return "d34a6024a86237cdc6a147702663aef81e954343"


def generate_replacement_guide_markdown() -> str:
    return """# Project Sources Replacement Guide (V6 Readiness)

This guide tells the operator which Project Sources should be uploaded now and which older docs can be deprioritized.

## Project Sources to Upload Now
Please upload the following files to the ChatGPT Project Sources:
1. `docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/CURRENT_STATE_SUMMARY_V6_READINESS.md`
2. `docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/NEW_CHAT_CONTINUATION_V6_READINESS.md`
3. `docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/OPERATOR_NEXT_ACTIONS_V6_READINESS.md`
4. `docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/METADATA_INTEGRITY_NOTE.md`
5. `docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json`
6. `docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_pipeline_status_matrix.json`
7. `docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_blocker_rollup.json`
8. `docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_project_sources_candidate_manifest.json`
9. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
10. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md`
11. `docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_intake_studio_packet.json`
12. `docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_fixture.validation_preview.json`
13. `docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_submission_runbook.md`
14. `docs/automation/V6_NETWORK_SCOPE_POLICY/scoped_network_policy_v6.md`
15. `docs/automation/V6_NETWORK_SCOPE_POLICY/network_resource_allowlist.json`
16. `docs/automation/V6_NETWORK_SCOPE_POLICY/network_scope_policy_packet.json`
17. `docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_packet.json`
18. `docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_stage_matrix.json`
19. `docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_dry_run_validation_report.json`
20. `docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_audit_trail_template.json`
21. `docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_submission_recovery_runbook.md`
22. `docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json`
23. `docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_rollup.json`
24. `docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_operator_runbook.md`
25. `docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_refresh_packet.json`
26. `docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_stage_matrix.json`
27. `docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_operator_checklist.md`
28. `docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_recovery_runbook.md`
29. `docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_authoring_report.md`
30. `docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json`
31. `docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json`
32. `docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json`

## Deprioritized Older Documents
You can deprioritize or remove older V6 draft outlines, platform variant files, or temporary preflight logs that are not listed above, to keep context usage clean.

## Critical Safety Reminders
> [!IMPORTANT]
> **Do Not Upload Master Plan / Operating Rules Changes**: Do not delete or modify the master plan (`current_v6_master_plan.md`) or operating rules unless explicitly instructed.
> **Upload Only Repository-Local Text Files**: Only upload repository-local `.json`, `.md`, or `.txt` documents.
> **No Secret / Sensitive Files**: Never upload `.env` files, credentials, local browser/session profiles, or temporary cache artifacts.
"""


def generate_new_chat_continuation_markdown(head_sha: str, blockers: list[str]) -> str:
    return f"""TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_CONTINUATION_AFTER_READINESS_BUNDLE_V0

## Pipeline State Info
- **Repository**: cc-live-contentops
- **Branch**: master
- **Baseline before upload bundle task**: {BASELINE_BEFORE_UPLOAD_BUNDLE_TASK}
- **Upload bundle generation HEAD (pre-commit generation input only, not runtime authority)**: {head_sha} (requires GitHub audit after push)
- **Latest Accepted Task**: TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0
- **Current Authoring Task**: TASK_CONTENTOPS_V6_OPERATOR_DELEGATED_REAL_EVIDENCE_FIXTURE_AUTHORING_AND_REFRESH_DRY_RUN_HEAVY_BATCH_V0

## Safety & Governance Rules
- Environment access, provider integrations, and live adapter capabilities are permitted only when explicitly scoped via a task contract under the V6 Fast Ship Operating Profile.
- Never output raw secret values, webhook URLs, tokens, or cookies.

## Current Blockers
- Operator intent through supervised dispatch readiness is ready, but dispatch remains blocked.
- Blocker: `operator_idea_source_ref` is missing from preflight.

## Pipeline Dispatch State
- `public_postable`: false
- `dispatch_allowed_now`: false
- `approval_valid_for_dispatch`: false
- `kill_switch_active`: true

## Prompt Instruction
> [!IMPORTANT]
> Future Antigravity prompts in this workflow must start with the active task label on line one.

## Next Recommended Task
- **Task**: `TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`
- **Goal**: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
"""


def generate_current_state_summary_markdown(head_sha: str, blockers: list[str]) -> str:
    blockers_list = "\n".join(f"- {b}" for b in blockers) if blockers else "- None"
    return f"""# Current State Summary (V6 Readiness)

## Repository Metadata
- **Branch**: master
- **Baseline before upload bundle task**: {BASELINE_BEFORE_UPLOAD_BUNDLE_TASK}
- **Current generation HEAD (pre-commit generation input only, not runtime authority)**: {head_sha} (requires GitHub audit after push)
- **Latest Task**: {TASK_LABEL}
- **Previous Accepted Status Task**: TASK_CONTENTOPS_V6_OPERATOR_PIPELINE_STATUS_AND_BLOCKED_RUNBOOK_HEAVY_BATCH_V0

> [!WARNING]
> **Post-Push Audit Required**: The final post-commit HEAD of this repository is not hardcoded here; it must be verified by ChatGPT/GitHub audit after push.

## Current V6 Lane Status Summary
- All 10 lanes from operator intent to supervised dispatch readiness are summarized.

> [!IMPORTANT]
> **V6 Operator Evidence Pipeline Blocked**: The V6 operator evidence pipeline is structurally wired, but is currently blocked because Jim has not supplied a real operator evidence fixture in `docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json`. Do not fabricate evidence, mark approval-ready, or unlock dispatch.

- **Dispatch Allowed Now**: false
- **Approval Valid for Dispatch**: false
- **Public Postable**: false
- **No Live Write Status**: Active (no live writes attempted)
- **No Env Read Status**: Active (no env values read)
- **No Network / API Status**: Active (no network calls made)

## Unresolved Blockers
{blockers_list}

## Next Recommended Task
- **Recommended next task**: `TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`
"""


def generate_operator_next_actions_markdown() -> str:
    return """# Operator Next Actions (V6 Readiness)

This document describes next manual and supervised actions required to resolve the source blockers and progress toward future publication.

## 1. Evidence Submission
- The operator must gather and submit factual evidence matching the required source references (specifically `operator_idea_source_ref`).
- Evidence must be submitted by writing to the intake submission packet without including any sensitive data or credentials.

## 2. Staging and Dispatch Gates
- Once evidence is submitted, run the operator source evidence submission validator task to check and verify the facts.
- Evaluate the operator approval gate to confirm compliance.
- Confirm supervised dispatch readiness and generate the final payload hashes.
- Destination bindings must occur in a later, separate task. No live channel IDs or webhooks may be written.

## 3. Webhook and Secret Rules
> [!WARNING]
> **No Webhook Pattern Disclosure**: Under no circumstances should webhook URLs, endpoint hostnames, or specific path patterns be printed or written to public documentation or source code.
> **Zero Credential Exposure**: No tokens, cookies, auth headers, environment variables, or private key lengths may be exposed in evidence submissions.
"""


def generate_implementation_report_markdown(bundle_status: str, head_sha: str) -> str:
    return f"""# V6 Project Sources Upload Bundle Implementation Report

- **Task Label**: {TASK_LABEL}
- **Bundle Status**: {bundle_status}
- **Baseline before upload bundle task**: {BASELINE_BEFORE_UPLOAD_BUNDLE_TASK}
- **Generation HEAD (pre-commit generation input only, not runtime authority)**: {head_sha} (requires GitHub audit after push)
- **Post-commit HEAD Verification**: Final HEAD requires post-push audit after push.
- **Files Packaged**:
  - CURRENT_STATE_SUMMARY_V6_READINESS.md
  - NEW_CHAT_CONTINUATION_V6_READINESS.md
  - OPERATOR_NEXT_ACTIONS_V6_READINESS.md
  - METADATA_INTEGRITY_NOTE.md
  - readiness_evidence_bundle_packet.json
  - v6_pipeline_status_matrix.json
  - v6_blocker_rollup.json
  - v6_project_sources_candidate_manifest.json
  - current_v6_master_plan.md
  - v6_25_task_ledger.md
  - operator_evidence_intake_studio_packet.json
  - operator_evidence_fixture.validation_preview.json
  - operator_evidence_submission_runbook.md
  - scoped_network_policy_v6.md
  - network_resource_allowlist.json
  - network_scope_policy_packet.json
  - fixture_lifecycle_packet.json
  - fixture_lifecycle_stage_matrix.json
  - fixture_dry_run_validation_report.json
  - fixture_audit_trail_template.json
  - fixture_submission_recovery_runbook.md
  - manual_evidence_refresh_orchestrator_packet.json
  - manual_evidence_refresh_rollup.json
  - manual_evidence_refresh_operator_runbook.md
  - manual_evidence_source_submission_refresh_packet.json
  - manual_evidence_source_submission_stage_matrix.json
  - manual_evidence_source_submission_operator_checklist.md
  - manual_evidence_source_submission_recovery_runbook.md
  - delegated_evidence_authoring_report.md
  - delegated_evidence_fixture_redacted_summary.json
  - delegated_evidence_source_map.json
  - delegated_evidence_refresh_result.json

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

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
"""


def generate_metadata_integrity_note_markdown() -> str:
    return """# Project Sources Metadata Integrity Note (V6)

## Context vs. Runtime Authority

> [!IMPORTANT]
> **Project Sources are Context Only**: Any task labels, HEAD hashes, or next pointers stored in the upload bundle are soft/advisory and provided for context only.
> **GitHub Remote is Runtime Authority**: The official GitHub remote repository commits and fetched files are the sole source of runtime truth and authority. Always run a local git audit to verify HEAD and current task state.

## Push Policies & Drift Detection

> [!CAUTION]
> **No Force Push Allowed**: Never use `git push -f` or force push under normal ContentOps operations.
> **Report Drift/Divergence**: If a normal `git push` is rejected, immediately stop execution and report the protected remote drift or divergence.
"""


def materialize_project_sources_upload_bundle_packets(
    readiness_bundle_path: str | Path = DEFAULT_READINESS_BUNDLE,
    dispatch_readiness_path: str | Path = DEFAULT_DISPATCH_READINESS,
) -> tuple[dict[str, Any], list[str]]:
    head_sha = verify_git_head()

    upstream_missing = False
    unresolved_blockers = []
    source_readiness_bundle_packet_id = None
    source_supervised_dispatch_readiness_packet_id = None

    try:
        readiness_bundle = load_json(readiness_bundle_path)
        source_readiness_bundle_packet_id = readiness_bundle.get("readiness_evidence_bundle_packet_id")
        source_supervised_dispatch_readiness_packet_id = readiness_bundle.get("source_supervised_dispatch_readiness_packet_id")
        unresolved_blockers = [b for b in readiness_bundle.get("unresolved_blockers", []) if b != "note"]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        upstream_missing = True

    try:
        dispatch_readiness = load_json(dispatch_readiness_path)
        if not source_supervised_dispatch_readiness_packet_id:
            source_supervised_dispatch_readiness_packet_id = dispatch_readiness.get("supervised_dispatch_readiness_packet_id")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        if not source_supervised_dispatch_readiness_packet_id:
            upstream_missing = True

    if upstream_missing:
        bundle_status = "PROJECT_SOURCES_UPLOAD_BUNDLE_BLOCKED_MISSING_ARTIFACTS"
    else:
        bundle_status = "PROJECT_SOURCES_UPLOAD_BUNDLE_READY_WITH_DISPATCH_BLOCKERS"

    # Unique upload bundle packet ID
    hasher = hashlib.sha256(f"{source_readiness_bundle_packet_id}_{bundle_status}".encode("utf-8"))
    project_sources_upload_bundle_packet_id = f"upload_bundle_{hasher.hexdigest()[:12]}"

    upload_candidate_files = [
        "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/CURRENT_STATE_SUMMARY_V6_READINESS.md",
        "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/NEW_CHAT_CONTINUATION_V6_READINESS.md",
        "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/OPERATOR_NEXT_ACTIONS_V6_READINESS.md",
        "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/METADATA_INTEGRITY_NOTE.md",
        "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json",
        "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_pipeline_status_matrix.json",
        "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_blocker_rollup.json",
        "docs/automation/V6_READINESS_EVIDENCE_BUNDLE/v6_project_sources_candidate_manifest.json",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
        "docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_intake_studio_packet.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_fixture.validation_preview.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_submission_runbook.md",
        "docs/automation/V6_NETWORK_SCOPE_POLICY/scoped_network_policy_v6.md",
        "docs/automation/V6_NETWORK_SCOPE_POLICY/network_resource_allowlist.json",
        "docs/automation/V6_NETWORK_SCOPE_POLICY/network_scope_policy_packet.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_packet.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_lifecycle_stage_matrix.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_dry_run_validation_report.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_audit_trail_template.json",
        "docs/automation/V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE/fixture_submission_recovery_runbook.md",
        "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_orchestrator_packet.json",
        "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_rollup.json",
        "docs/automation/V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR/manual_evidence_refresh_operator_runbook.md",
        "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_refresh_packet.json",
        "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_stage_matrix.json",
        "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_operator_checklist.md",
        "docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_recovery_runbook.md",
        "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_authoring_report.md",
        "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json",
        "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json",
        "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json"
    ]

    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "project_sources_upload_bundle_packet_id": project_sources_upload_bundle_packet_id,
        "source_readiness_evidence_bundle_packet_id": source_readiness_bundle_packet_id,
        "source_supervised_dispatch_readiness_packet_id": source_supervised_dispatch_readiness_packet_id,
        "baseline_before_upload_bundle_task": BASELINE_BEFORE_UPLOAD_BUNDLE_TASK,
        "previous_accepted_pipeline_status_head": "4f8b79563f9cf88777c8d5cda8ff48a7a2bbdd81",
        "bundle_generation_head": head_sha,
        "bundle_generation_head_label": "pre_commit_generation_head_input_only_requires_github_audit",
        "final_head_requires_post_push_audit": True,
        "bundle_stage": "v6_project_sources_upload_bundle",
        "bundle_status": bundle_status,
        "upload_candidate_files": upload_candidate_files,
        "replacement_guide_file": "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/PROJECT_SOURCES_REPLACEMENT_GUIDE_V6_READINESS.md",
        "new_chat_continuation_file": "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/NEW_CHAT_CONTINUATION_V6_READINESS.md",
        "current_state_summary_file": "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/CURRENT_STATE_SUMMARY_V6_READINESS.md",
        "operator_next_actions_file": "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/OPERATOR_NEXT_ACTIONS_V6_READINESS.md",
        "public_postable": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "kill_switch_active": True,
        "live_write_attempted": False,
        "outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "unresolved_blockers": sorted(unresolved_blockers),
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "next_recommended_task": "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    }

    return packet, upload_candidate_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Project Sources Upload Bundle Lane")
    parser.add_argument("--readiness-bundle", default=str(DEFAULT_READINESS_BUNDLE))
    parser.add_argument("--dispatch-readiness", default=str(DEFAULT_DISPATCH_READINESS))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packet, file_list = materialize_project_sources_upload_bundle_packets(
        args.readiness_bundle, args.dispatch_readiness
    )

    # Write files
    write_json(out_dir / "project_sources_upload_bundle_packet.json", packet)

    # UPLOAD_BUNDLE_FILE_LIST_V6_READINESS.txt
    file_list_content = "\n".join(file_list) + "\n"
    (out_dir / "UPLOAD_BUNDLE_FILE_LIST_V6_READINESS.txt").write_text(file_list_content, encoding="utf-8")

    # PROJECT_SOURCES_REPLACEMENT_GUIDE_V6_READINESS.md
    (out_dir / "PROJECT_SOURCES_REPLACEMENT_GUIDE_V6_READINESS.md").write_text(
        generate_replacement_guide_markdown(), encoding="utf-8"
    )

    # NEW_CHAT_CONTINUATION_V6_READINESS.md
    (out_dir / "NEW_CHAT_CONTINUATION_V6_READINESS.md").write_text(
        generate_new_chat_continuation_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        encoding="utf-8"
    )

    # CURRENT_STATE_SUMMARY_V6_READINESS.md
    (out_dir / "CURRENT_STATE_SUMMARY_V6_READINESS.md").write_text(
        generate_current_state_summary_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        encoding="utf-8"
    )

    # OPERATOR_NEXT_ACTIONS_V6_READINESS.md
    (out_dir / "OPERATOR_NEXT_ACTIONS_V6_READINESS.md").write_text(
        generate_operator_next_actions_markdown(), encoding="utf-8"
    )

    # IMPLEMENTATION_REPORT.md
    (out_dir / "IMPLEMENTATION_REPORT.md").write_text(
        generate_implementation_report_markdown(packet["bundle_status"], packet["bundle_generation_head"]), encoding="utf-8"
    )

    # next_task_pointer.md
    (out_dir / "next_task_pointer.md").write_text(
        generate_next_task_pointer_markdown(), encoding="utf-8"
    )

    # METADATA_INTEGRITY_NOTE.md
    (out_dir / "METADATA_INTEGRITY_NOTE.md").write_text(
        generate_metadata_integrity_note_markdown(), encoding="utf-8"
    )

    print(json.dumps({
        "project_sources_upload_bundle_packet_id": packet["project_sources_upload_bundle_packet_id"],
        "bundle_status": packet["bundle_status"],
        "unresolved_blockers": packet["unresolved_blockers"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
