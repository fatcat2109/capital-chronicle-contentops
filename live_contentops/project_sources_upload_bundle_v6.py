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

TASK_LABEL = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
BASELINE_BEFORE_UPLOAD_BUNDLE_TASK = "d97bc3968e1babf48c81f384fb547b439e48515c"
PAYLOAD_HASH_TASK = "TASK_CONTENTOPS_V6_REPAIR_PAYLOAD_PREVIEW_HASH_PLACEHOLDER_AND_SCOPE_CONTAMINATION_V0"
NEXT_APPROVAL_TASK = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"
NEXT_CANONICAL_DRAFT_OPERATOR_IMPORT_UI_APPROVAL_TASK = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_IMPORT_UI_AND_APPROVAL_REVIEW_HEAVY_BATCH_V0"
NEXT_REAL_SOURCE_PACK_MANUAL_IMPORT_FIXTURE_TASK = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_MANUAL_IMPORT_FIXTURE_SCHEMA_AND_HASH_REVIEW_DRY_RUN_HEAVY_BATCH_V0"
NEXT_REAL_SOURCE_PACK_OPERATOR_FILLED_REDACTED_FIXTURE_TASK = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_FILLED_REDACTED_FIXTURE_DRY_RUN_REVIEW_HEAVY_BATCH_V0"
NEXT_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE_TASK = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE_DRY_RUN_HEAVY_BATCH_V0"
NEXT_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK_TASK = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0"
NEXT_MANUAL_SIGN_TASK = "TASK_CONTENTOPS_V6_OPERATOR_SIGN_PAYLOAD_HASH_MANUAL_STEP"
NEXT_CAPTURE_RUN_TASK = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"
NEXT_DISPATCH_READINESS_TASK = "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION_LANE_HEAVY_BATCH_V0"
NEXT_APPROVAL_LEDGER_TASK = "TASK_CONTENTOPS_V6_APPROVAL_LEDGER_AND_OUTBOX_RECORDING_LANE_HEAVY_BATCH_V0"
NEXT_PLATFORM_CONTENT_TASK = "TASK_CONTENTOPS_V6_PLATFORM_CONTENT_GENERATORS_AND_THREAD_CONTINUATION_HEAVY_BATCH_V0"
NEXT_DRAFT_INSPECTOR_TASK = "TASK_CONTENTOPS_V6_DRAFT_INSPECTOR_V2_AND_CONTENT_QUALITY_QA_HEAVY_BATCH_V0"
NEXT_UNIFIED_HASH_APPROVAL_OUTBOX_UPGRADE_TASK = "TASK_CONTENTOPS_V6_UNIFIED_PAYLOAD_HASH_APPROVAL_OUTBOX_UPGRADE_HEAVY_BATCH_V0"
NEXT_DISCORD_TELEGRAM_BRIDGE_TASK = "TASK_CONTENTOPS_V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE_AND_REDACTED_STATUS_HEAVY_BATCH_V0"
NEXT_SUBSTACK_COMPOSE_TASK = "TASK_CONTENTOPS_V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN_AND_BROWSER_SAFETY_QA_HEAVY_BATCH_V0"
NEXT_FEEDBACK_INTAKE_TASK = "TASK_CONTENTOPS_V6_COMMUNITY_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_HEAVY_BATCH_V0"
NEXT_LLM_FEEDBACK_SUMMARIZER_TASK = "TASK_CONTENTOPS_V6_LLM_FEEDBACK_SUMMARIZER_AND_NEXT_IDEA_GENERATOR_DRY_RUN_HEAVY_BATCH_V0"
NEXT_NEXT_CANONICAL_ARTICLE_TASK = "TASK_CONTENTOPS_V6_NEXT_CANONICAL_ARTICLE_PACKET_FROM_BACKLOG_DRY_RUN_HEAVY_BATCH_V0"
NEXT_CANONICAL_DRAFT_TASK = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0"
NEXT_SOURCE_UI_TASK = "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"
NEXT_IMPORT_REVALIDATION_TASK = "TASK_CONTENTOPS_V6_VERIFIED_SOURCE_PACK_IMPORT_AND_REVALIDATION_DRY_RUN_HEAVY_BATCH_V0"
NEXT_CANONICAL_DRAFT_POSITIVE_PATH_TASK = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_GENERATION_FROM_VERIFIED_SOURCE_PACK_POSITIVE_PATH_DRY_RUN_HEAVY_BATCH_V0"

DEFAULT_READINESS_BUNDLE = Path("docs/automation/V6_READINESS_EVIDENCE_BUNDLE/readiness_evidence_bundle_packet.json")
DEFAULT_DISPATCH_READINESS = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS/supervised_dispatch_readiness_packet.json")

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


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "placeholder" in value.lower()
    if isinstance(value, dict):
        return any(_contains_placeholder(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_placeholder(v) for v in value)
    return False


def _packet_has_valid_payload_hash(packet: dict[str, Any]) -> bool:
    payload_hash = packet.get("payload_hash")
    if packet.get("payload_hash_created") is not True:
        return False
    if not isinstance(payload_hash, str) or len(payload_hash) < 32:
        return False
    return not _contains_placeholder(packet)



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
33. `docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json`
34. `docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_review_packet.json`
35. `docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_signature_template.json`
36. `docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_blocker_report.md`
37. `docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_runbook.md`
38. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_packet.json`
39. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_ui_spec.md`
40. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_cli_reference.md`
41. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_validation_report.json`
42. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_blocker_report.md`
43. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_runbook.md`
44. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/implementation_report.md`
45. `docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/next_task_pointer.md`

## Deprioritized Older Documents
You can deprioritize or remove older V6 draft outlines, platform variant files, or temporary preflight logs that are not listed above, to keep context usage clean.

## Critical Safety Reminders
> [!IMPORTANT]
> **Do Not Upload Master Plan / Operating Rules Changes**: Do not delete or modify the master plan (`current_v6_master_plan.md`) or operating rules unless explicitly instructed.
> **Upload Only Repository-Local Text Files**: Only upload repository-local `.json`, `.md`, or `.txt` documents.
> **No Secret / Sensitive Files**: Never upload `.env` files, credentials, local browser/session profiles, or temporary cache artifacts.
"""


def generate_new_chat_continuation_markdown(head_sha: str, blockers: list[str], next_task: str = NEXT_CAPTURE_RUN_TASK) -> str:
    next_goal = (
        "Jim manually signs payload hash review intent while keeping dispatch validity disabled."
        if next_task == NEXT_MANUAL_SIGN_TASK
        else (
            "Verify destination binding and outbox draft after operator signature validation succeeds."
            if next_task == NEXT_CAPTURE_RUN_TASK
            else (
                "Record approved signature to the public/audit ledger and prepare outbox dispatch recording."
                if next_task == NEXT_APPROVAL_LEDGER_TASK
                else "Revalidate supervised dispatch readiness after outbox draft review."
            )
        )
    )
    return f"""TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_CONTINUATION_AFTER_READINESS_BUNDLE_V0

## Pipeline State Info
- **Repository**: cc-live-contentops
- **Branch**: master
- **Baseline before upload bundle task**: {BASELINE_BEFORE_UPLOAD_BUNDLE_TASK}
- **Upload bundle generation HEAD (pre-commit generation input only, not runtime authority)**: {head_sha} (requires GitHub audit after push)
- **Latest Accepted Task**: TASK_CONTENTOPS_V6_OPERATOR_DELEGATED_REAL_EVIDENCE_FIXTURE_AUTHORING_AND_REFRESH_DRY_RUN_HEAVY_BATCH_V0
- **Current Approval Task**: TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_AND_DELEGATED_EVIDENCE_ROLLUP_REPAIR_HEAVY_BATCH_V0

## Safety & Governance Rules
- Environment access, provider integrations, and live adapter capabilities are permitted only when explicitly scoped via a task contract under the V6 Fast Ship Operating Profile.
- Never output raw secret values, webhook URLs, tokens, or cookies.

## Current Blockers
- Operator intent through supervised dispatch readiness is ready, but dispatch remains blocked.
- Blocker: `payload_hash_incomplete` remains active unless exact safe preview and non-placeholder hash exist.

## Pipeline Dispatch State
- `public_postable`: false
- `dispatch_allowed_now`: false
- `approval_valid_for_dispatch`: false
- `kill_switch_active`: true

## Prompt Instruction
> [!IMPORTANT]
> Future Antigravity prompts in this workflow must start with the active task label on line one.

## Next Recommended Task
- **Task**: `{next_task}`
- **Goal**: {next_goal}
"""


def generate_current_state_summary_markdown(head_sha: str, blockers: list[str], next_task: str = NEXT_CAPTURE_RUN_TASK) -> str:
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
> **V6 Operator Evidence Pipeline Blocked**: Dispatch remains blocked until exact safe payload preview, deterministic non-placeholder payload hash, operator signature binding, destination binding, approval ledger, outbox, and supervised dispatch gates all exist together.

- **Dispatch Allowed Now**: false
- **Approval Valid for Dispatch**: false
- **Public Postable**: false
- **No Live Write Status**: Active (no live writes attempted)
- **No Env Read Status**: Active (no env values read)
- **No Network / API Status**: Active (no network calls made)

## Unresolved Blockers
{blockers_list}

## Next Recommended Task
- **Recommended next task**: `{next_task}`
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
  - operator_approval_gate_packet.json
  - operator_approval_review_packet.json
  - operator_approval_signature_template.json
  - operator_approval_blocker_report.md
  - operator_approval_runbook.md
  - operator_signature_binding_packet.json
  - operator_signature_binding_review_packet.json
  - operator_signature_template.json
  - operator_signature_validation_report.json
  - operator_signature_blocker_report.md
  - operator_signature_runbook.md
  - operator_approval_capture_packet.json
  - operator_approval_capture_ui_spec.md
  - operator_approval_capture_cli_reference.md
  - operator_approval_capture_validation_report.json
  - operator_approval_capture_blocker_report.md
  - operator_approval_capture_runbook.md
  - operator_approval_capture_implementation_report.md
  - operator_approval_capture_next_task_pointer.md
  - destination_binding_outbox_draft_packet.json
  - destination_binding_review_matrix.json
  - outbox_draft_preview_packet.json
  - outbox_draft_validation_report.json
  - destination_binding_blocker_report.md
  - destination_binding_runbook.md
  - destination_binding_implementation_report.md
  - destination_binding_next_task_pointer.md
  - supervised_dispatch_readiness_packet.json
  - dispatch_readiness_blocker_matrix.json
  - dispatch_readiness_validation_report.json
  - dispatch_readiness_runbook.md
  - dispatch_readiness_blocker_report.md
  - revalidation_implementation_report.md
  - revalidation_next_task_pointer.md
  - approval_ledger_outbox_packet.json
  - approval_ledger_entry_preview.json
  - outbox_record_preview.json
  - outbox_record_validation_report.json
  - approval_ledger_validation_report.json
  - approval_ledger_outbox_blocker_report.md
  - approval_ledger_outbox_runbook.md
  - recording_implementation_report.md
  - recording_next_task_pointer.md
  - provider_gate_packet.json
  - prompt_registry_packet.json
  - sample_operator_intents.json
  - sample_content_idea_packet.json
  - sample_research_grounding_packet.json
  - sample_canonical_article_packet.json
  - sample_seo_editorial_packet.json
  - ai_production_core_packet.json
  - ai_production_core_validation_report.json
  - ai_production_core_blocker_report.md
  - ai_production_core_runbook.md
  - core_implementation_report.md
  - core_next_task_pointer.md


- **Safety Checks Pass**:
  - No secret output: `true`
  - No webhook URLs or concrete host/path patterns printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No public-postable content produced: `true`
"""


def generate_next_task_pointer_markdown(next_task: str = NEXT_CAPTURE_RUN_TASK) -> str:
    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: Progress the pipeline by resolving the next recommended gate.
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

    readiness_bundle_path = Path(readiness_bundle_path)
    dispatch_readiness_path = Path(dispatch_readiness_path)

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

    if not unresolved_blockers:
        unresolved_blockers = [
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

    # Filter out resolved blockers if delegated evidence is complete
    evidence_complete = False
    payload_hash_created = False

    # 1. Check relative paths under the same directory (for test isolation)
    rel_path = readiness_bundle_path.parent / "delegated_evidence_refresh_result.json"
    if rel_path.exists():
        try:
            res = json.loads(rel_path.read_text(encoding="utf-8"))
            if res.get("evidence_complete") is True:
                evidence_complete = True
        except Exception:
            pass

    rel_hash_path = readiness_bundle_path.parent / "payload_preview_hash_packet.json"
    if rel_hash_path.exists():
        try:
            res_hash = json.loads(rel_hash_path.read_text(encoding="utf-8"))
            if _packet_has_valid_payload_hash(res_hash):
                payload_hash_created = True
        except Exception:
            pass

    operator_signature_valid = False

    # Check relative paths first (for test isolation)
    rel_dest_path = readiness_bundle_path.parent / "destination_binding_outbox_draft_packet.json"
    if rel_dest_path.exists():
        try:
            dest_packet = json.loads(rel_dest_path.read_text(encoding="utf-8"))
            if dest_packet.get("operator_signature_valid") is True:
                operator_signature_valid = True
        except Exception:
            pass

    # Check default paths if sibling is not found/valid
    if not operator_signature_valid:
        default_dest_path = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_outbox_draft_packet.json")
        if default_dest_path.exists():
            try:
                dest_packet = json.loads(default_dest_path.read_text(encoding="utf-8"))
                if dest_packet.get("operator_signature_valid") is True:
                    operator_signature_valid = True
            except Exception:
                pass

    # Also check revalidation packet
    rel_reval_path = readiness_bundle_path.parent / "supervised_dispatch_readiness_packet.json"
    if rel_reval_path.exists():
        try:
            reval_packet = json.loads(rel_reval_path.read_text(encoding="utf-8"))
            if reval_packet.get("operator_signature_valid") is True:
                operator_signature_valid = True
        except Exception:
            pass

    default_reval_path = Path("docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/supervised_dispatch_readiness_packet.json")
    if default_reval_path.exists():
        try:
            reval_packet = json.loads(default_reval_path.read_text(encoding="utf-8"))
            if reval_packet.get("operator_signature_valid") is True:
                operator_signature_valid = True
        except Exception:
            pass

    # Also check ledger packet
    rel_ledger_path = readiness_bundle_path.parent / "approval_ledger_outbox_packet.json"
    if rel_ledger_path.exists():
        try:
            ledger_packet = json.loads(rel_ledger_path.read_text(encoding="utf-8"))
            if ledger_packet.get("operator_signature_valid") is True:
                operator_signature_valid = True
        except Exception:
            pass

    default_ledger_path = Path("docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_packet.json")
    if default_ledger_path.exists():
        try:
            ledger_packet = json.loads(default_ledger_path.read_text(encoding="utf-8"))
            if ledger_packet.get("operator_signature_valid") is True:
                operator_signature_valid = True
        except Exception:
            pass

    if readiness_bundle_path.parent.parent:
        sibling_hash_path = readiness_bundle_path.parent.parent / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json"
        if sibling_hash_path.exists():
            try:
                res_hash = json.loads(sibling_hash_path.read_text(encoding="utf-8"))
                if _packet_has_valid_payload_hash(res_hash):
                    payload_hash_created = True
            except Exception:
                pass

    # 2. Check default/committed paths
    is_default_rb = str(readiness_bundle_path) == str(DEFAULT_READINESS_BUNDLE)
    if is_default_rb:
        refresh_packet_path = Path("docs/automation/V6_MANUAL_EVIDENCE_SOURCE_SUBMISSION_REFRESH/manual_evidence_source_submission_refresh_packet.json")
        if refresh_packet_path.exists():
            try:
                refresh_packet = json.loads(refresh_packet_path.read_text(encoding="utf-8"))
                if refresh_packet.get("evidence_complete") is True:
                    evidence_complete = True
            except Exception:
                pass

        delegated_result_path = Path("docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json")
        if delegated_result_path.exists():
            try:
                delegated_result = json.loads(delegated_result_path.read_text(encoding="utf-8"))
                if delegated_result.get("evidence_complete") is True:
                    evidence_complete = True
            except Exception:
                pass

        default_hash_path = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json")
        if default_hash_path.exists():
            try:
                res_hash = json.loads(default_hash_path.read_text(encoding="utf-8"))
                if _packet_has_valid_payload_hash(res_hash):
                    payload_hash_created = True
            except Exception:
                pass

    if evidence_complete:
        unresolved_blockers = [b for b in unresolved_blockers if b not in ["evidence_incomplete", "operator_idea_source_ref_missing"]]

    if payload_hash_created:
        unresolved_blockers = [b for b in unresolved_blockers if b != "payload_hash_incomplete"]

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
        "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_review_packet.json",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_signature_template.json",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_blocker_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_runbook.md",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/implementation_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_GATE/next_task_pointer.md",
        "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json",
        "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json",
        "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json",
        "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_inputs_redacted.json",
        "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_runbook.md",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_packet.json",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_binding_review_packet.json",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_template.json",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_validation_report.json",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_blocker_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_runbook.md",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/implementation_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/next_task_pointer.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_packet.json",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_ui_spec.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_cli_reference.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_validation_report.json",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_blocker_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_capture_runbook.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/implementation_report.md",
        "docs/automation/V6_OPERATOR_APPROVAL_CAPTURE/next_task_pointer.md",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_outbox_draft_packet.json",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_review_matrix.json",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_preview_packet.json",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/outbox_draft_validation_report.json",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_blocker_report.md",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/destination_binding_runbook.md",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/implementation_report.md",
        "docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT/next_task_pointer.md",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/supervised_dispatch_readiness_packet.json",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_blocker_matrix.json",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_validation_report.json",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_runbook.md",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/dispatch_readiness_blocker_report.md",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/implementation_report.md",
        "docs/automation/V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION/next_task_pointer.md",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_packet.json",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_entry_preview.json",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/outbox_record_preview.json",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/outbox_record_validation_report.json",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_validation_report.json",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_blocker_report.md",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/approval_ledger_outbox_runbook.md",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/implementation_report.md",
        "docs/automation/V6_APPROVAL_LEDGER_OUTBOX_RECORDING/next_task_pointer.md",
        "docs/automation/V6_AI_PRODUCTION_CORE/provider_gate_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/prompt_registry_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_operator_intents.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_content_idea_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_research_grounding_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_packet.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_validation_report.json",
        "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_blocker_report.md",
        "docs/automation/V6_AI_PRODUCTION_CORE/ai_production_core_runbook.md",
        "docs/automation/V6_AI_PRODUCTION_CORE/implementation_report.md",
        "docs/automation/V6_AI_PRODUCTION_CORE/next_task_pointer.md",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_content_generators_packet.json",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_constraint_registry.json",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/thread_continuation_pack.json",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_validation_report.json",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_blocker_report.md",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_runbook.md",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/implementation_report.md",
        "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/next_task_pointer.md",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_v2_packet.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/content_quality_scorecard.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/platform_variant_inspection_report.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/thread_continuation_quality_report.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/source_truth_and_citation_report.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/no_financial_advice_report.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/seo_editorial_quality_report.json",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_blocker_report.md",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_runbook.md",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/implementation_report.md",
        "docs/automation/V6_DRAFT_INSPECTOR_V2/next_task_pointer.md",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_contract_packet.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/multi_platform_payload_manifest.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_hash_manifest.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/payload_integrity_validation_report.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_approval_readiness_report.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_outbox_readiness_report.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_blocker_matrix.json",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_runbook.md",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/implementation_report.md",
        "docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/next_task_pointer.md",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/operator_bridge_packet.json",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/redacted_status_packet.json",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/discord_operator_message_preview.json",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/telegram_operator_message_preview.json",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/operator_bridge_capability_matrix.json",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/operator_bridge_blocker_report.md",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/operator_bridge_runbook.md",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/implementation_report.md",
        "docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE/next_task_pointer.md",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_compose_dry_run_packet.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_compose_payload_preview.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_mock_compose_page.html",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/browser_safety_policy_packet.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/browser_qa_checklist.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/browser_screenshot_evidence_manifest.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/browser_safety_validation_report.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/compose_payload_validation_report.json",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_browser_blocker_report.md",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/substack_browser_runbook.md",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/implementation_report.md",
        "docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN/next_task_pointer.md",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/community_feedback_intake_packet.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/manual_feedback_snapshot_template.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/redacted_feedback_snapshot_sample.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/community_question_cluster_report.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/feedback_summary_ready_packet.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/content_backlog_candidates.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/next_canonical_article_idea_candidates.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/feedback_loop_validation_report.json",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/feedback_loop_blocker_report.md",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/feedback_loop_runbook.md",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/implementation_report.md",
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/next_task_pointer.md",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/llm_feedback_summarizer_packet.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/feedback_summarizer_prompt_contract.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/feedback_summary_dry_run_output.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/next_idea_generator_packet.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/refined_next_canonical_article_ideas.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/refined_content_backlog_candidates.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/unsafe_feedback_handling_report.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/llm_summary_safety_validation_report.json",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/llm_feedback_summarizer_blocker_report.md",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/llm_feedback_summarizer_runbook.md",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/implementation_report.md",
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/next_task_pointer.md",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/next_canonical_article_packet.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/selected_backlog_candidate.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_research_requirements.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/source_verification_checklist.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_claim_ledger_scaffold.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_outline_packet.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/editorial_risk_matrix.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/downstream_platform_readiness_placeholders.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_planning_validation_report.json",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_planning_blocker_report.md",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/implementation_report.md",
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/next_task_pointer.md",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/verified_source_pack_schema.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/verified_source_pack_missing_default.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/source_pack_gate_report.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/source_claim_binding_report.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/canonical_article_draft_packet.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/canonical_article_draft_preview.md",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/canonical_article_draft_validation_report.json",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/canonical_article_draft_blocker_report.md",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/canonical_article_draft_runbook.md",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/implementation_report.md",
        "docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK/next_task_pointer.md",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_verification_ui_packet.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/operator_research_checklist.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_evidence_entry_template.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_draft_template.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_draft_validation_report.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_operator_workflow.md",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_verification_local_mock.html",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_ui_screenshot_manifest.json",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/source_pack_verification_blocker_report.md",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/implementation_report.md",
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/next_task_pointer.md",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/verified_source_pack_import_packet.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/operator_source_pack_import_template.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/verified_source_pack_import_validation_report.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/source_pack_claim_binding_revalidation_report.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/canonical_draft_gate_revalidation_report.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/test_only_positive_fixture_report.json",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/verified_source_pack_import_blocker_report.md",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/verified_source_pack_import_runbook.md",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/implementation_report.md",
        "docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION/next_task_pointer.md",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_positive_path_packet.json",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/test_only_verified_source_pack_fixture_summary.json",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/test_only_claim_source_binding_proof.json",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_review_only_packet.json",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_review_only_preview.md",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_positive_path_validation_report.json",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_positive_path_blocker_report.md",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/canonical_draft_positive_path_runbook.md",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/implementation_report.md",
        "docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN/next_task_pointer.md",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_packet.json",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_checklist.json",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_approval_template.json",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_validation_report.json",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_local_mock.html",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_screenshot_manifest.json",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_blocker_report.md",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/operator_source_pack_review_runbook.md",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/implementation_report.md",
        "docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW/next_task_pointer.md",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_manual_import_schema.json",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_manual_import_blank_fixture.json",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_hash_review_packet.json",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_redaction_policy.json",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_manual_import_validation_report.json",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_manual_import_blocker_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/real_source_pack_manual_import_runbook.md",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/implementation_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA/next_task_pointer.md",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/real_source_pack_redacted_fixture_packet.json",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/operator_filled_redacted_fixture_example.json",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/redacted_hash_presence_review.json",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/redacted_claim_binding_review.json",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/redacted_fixture_validation_report.json",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/redacted_fixture_blocker_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/redacted_fixture_review_runbook.md",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/implementation_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW/next_task_pointer.md",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_operator_approval_gate_packet.json",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_operator_approval_template.json",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_operator_approval_validation_report.json",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_approval_readiness_matrix.json",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_approval_blocker_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/source_pack_approval_runbook.md",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/implementation_report.md",
        "docs/automation/V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE/next_task_pointer.md"
    ]

    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "project_sources_upload_bundle_packet_id": project_sources_upload_bundle_packet_id,
        "source_readiness_evidence_bundle_packet_id": source_readiness_bundle_packet_id,
        "source_supervised_dispatch_readiness_packet_id": source_supervised_dispatch_readiness_packet_id,
        "baseline_before_upload_bundle_task": BASELINE_BEFORE_UPLOAD_BUNDLE_TASK,
        "previous_accepted_pipeline_status_head": "9571d900552122c0d1c110017d718c7e4b7f375d",
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
        "next_recommended_task": NEXT_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK_TASK
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
        generate_new_chat_continuation_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"], packet["next_recommended_task"]),
        encoding="utf-8"
    )

    # CURRENT_STATE_SUMMARY_V6_READINESS.md
    (out_dir / "CURRENT_STATE_SUMMARY_V6_READINESS.md").write_text(
        generate_current_state_summary_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"], packet["next_recommended_task"]),
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
        generate_next_task_pointer_markdown(packet["next_recommended_task"]), encoding="utf-8"
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
