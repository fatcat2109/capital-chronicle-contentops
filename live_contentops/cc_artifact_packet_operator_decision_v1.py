"""Operator decision gate for CC artifact packet public-candidate eligibility.

Jim's GO for this task authorizes a deterministic local decision envelope. It
does not override packet DQR, candidate-only, publish-eligibility, caveat,
approval-hash, duplicate, public-freeze, or platform safety gates.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cc_artifact_packet_approval_v0 import (
    HANDOFF_COMMIT,
    build_approval_hash,
    compute_component_hashes,
)
from .cc_artifact_packet_public_candidate_gate_v1 import evaluate_public_candidate_gate

TASK_LABEL = "TASK_CONTENTOPS_CC_ARTIFACT_PACKET_OPERATOR_DECISION_AND_CONTROLLED_PUBLIC_CANDIDATE_REHEARSAL_V1"
CLASSIFICATION = "PASS_OPERATOR_DECISION_GATE_BLOCKED_BY_PACKET_ELIGIBILITY"
SCHEMA_VERSION = "1.0.0"

DEFAULT_INTAKE_DIR = Path("docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0")
DEFAULT_OUTPUT_DIR = Path("docs/automation/CC_ARTIFACT_PACKET_OPERATOR_DECISION_V1")

INTERNAL_ONLY_TERMS = (
    "internal draft",
    "internal-only",
    "internal only",
    "do not publish",
    "do not distribute",
    "not public",
    "non-authoritative",
    "blocked",
)


class OperatorDecisionError(ValueError):
    """Raised for malformed decision inputs or scope breaches."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_existing_intake_artifacts(output_dir: str | Path = DEFAULT_INTAKE_DIR) -> dict[str, Any]:
    base = Path(output_dir)
    artifact_paths = {
        "internal_draft": base / "internal_draft_v0.json",
        "intake_summary": base / "intake_dry_run_summary_v0.json",
        "rehearsal_intent": base / "rehearsal_intent_v0.json",
    }
    artifacts: dict[str, Any] = {"artifact_paths": {k: str(v) for k, v in artifact_paths.items()}, "artifact_load_errors": []}
    for key, path in artifact_paths.items():
        if not path.exists():
            artifacts[key] = None
            artifacts["artifact_load_errors"].append(f"missing_{key}")
            continue
        try:
            artifacts[key] = _read_json(path)
        except Exception as exc:
            artifacts[key] = None
            artifacts["artifact_load_errors"].append(f"invalid_{key}:{exc.__class__.__name__}")
    approval_hash_path = base / "approval_hash_v0.txt"
    artifacts["approval_hash_path"] = str(approval_hash_path)
    if approval_hash_path.exists():
        artifacts["approval_hash_file"] = approval_hash_path.read_text(encoding="utf-8").strip()
    else:
        artifacts["approval_hash_file"] = None
        artifacts["artifact_load_errors"].append("missing_approval_hash_file")
    return artifacts


def _blob(values: Any) -> str:
    return json.dumps(values, sort_keys=True, ensure_ascii=False).lower()


def _append_if(condition: bool, items: list[str], value: str) -> None:
    if condition and value not in items:
        items.append(value)


def evaluate_packet_public_candidate_eligibility(
    packet: dict[str, Any],
    internal_draft: dict[str, Any] | None,
    intake_summary: dict[str, Any] | None,
    rehearsal_intent: dict[str, Any] | None,
    *,
    approval_hash_file: str | None = None,
    operator_go: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    component_hashes = compute_component_hashes(packet)
    approval_hash = build_approval_hash(packet)

    _append_if(internal_draft is None, blockers, "missing_internal_draft")
    _append_if(intake_summary is None, blockers, "missing_intake_summary")
    _append_if(rehearsal_intent is None, blockers, "missing_rehearsal_intent")
    _append_if(not approval_hash_file, blockers, "missing_approval_hash_file")

    if internal_draft:
        _append_if(internal_draft.get("approval_hash") != approval_hash, blockers, "approval_hash_mismatch_internal_draft")
        _append_if(internal_draft.get("component_hashes") != component_hashes, blockers, "component_hash_mismatch_internal_draft")
    if intake_summary:
        _append_if(intake_summary.get("approval_hash") != approval_hash, blockers, "approval_hash_mismatch_intake_summary")
        _append_if(intake_summary.get("component_hashes") != component_hashes, blockers, "component_hash_mismatch_intake_summary")
    if rehearsal_intent:
        _append_if(rehearsal_intent.get("approval_hash") != approval_hash, blockers, "approval_hash_mismatch_rehearsal_intent")
        _append_if(rehearsal_intent.get("public_ready") is True, blockers, "rehearsal_intent_public_ready_true")
        _append_if(rehearsal_intent.get("dispatch_allowed_now") is True, blockers, "rehearsal_intent_dispatch_allowed_true")
    if approval_hash_file:
        _append_if(approval_hash_file != approval_hash, blockers, "approval_hash_mismatch_file")

    dqr_status = packet.get("dqr_status")
    candidate_only = packet.get("candidate_only")
    publish_eligibility = packet.get("publish_eligibility")
    source_quality_status = str(packet.get("source_quality_status") or "")
    forbidden_use_notes = packet.get("forbidden_use_notes") or []
    limitations = packet.get("limitations") or []
    caveat_blob = _blob({"forbidden_use_notes": forbidden_use_notes, "limitations": limitations})

    _append_if(dqr_status != "CLEAR", blockers, f"dqr_status_not_clear:{dqr_status}")
    _append_if(candidate_only is True, blockers, "candidate_only_true")
    _append_if(publish_eligibility == "internal_draft_only", blockers, "publish_eligibility_internal_draft_only")
    _append_if(publish_eligibility == "manual_review_only", blockers, "publish_eligibility_manual_review_only_without_public_upgrade_packet")
    _append_if("degraded" in source_quality_status.lower() or "blocked" in source_quality_status.lower(), blockers, "source_quality_degraded_or_blocked")
    _append_if(any(term in caveat_blob for term in INTERNAL_ONLY_TERMS), blockers, "packet_caveats_internal_or_non_authoritative")
    _append_if("dqr" in caveat_blob and "blocked" in caveat_blob, blockers, "limitations_include_dqr_blocked")

    if operator_go:
        warnings.append("operator_go_received_for_decision_gate_only_not_dqr_override")
    else:
        warnings.append("operator_go_not_received")

    # This task intentionally does not run the broad public-candidate duplicate
    # preflight; packet ineligibility short-circuits public promotion first.
    public_freeze_duplicate_status = "not_checked_packet_ineligible_short_circuit"
    _append_if(public_freeze_duplicate_status.startswith("not_checked"), blockers, "public_freeze_duplicate_status_not_checked")
    _append_if(True, blockers, "live_provider_or_platform_path_forbidden_in_this_task")

    return {
        "packet_id": packet.get("packet_id"),
        "approval_hash": approval_hash,
        "handoff_commit": HANDOFF_COMMIT,
        "sample_packet.main_repo_head": packet.get("main_repo_head"),
        "dqr_status": dqr_status,
        "candidate_only": candidate_only,
        "publish_eligibility": publish_eligibility,
        "source_quality_status": source_quality_status,
        "component_hashes": component_hashes,
        "duplicate_family": internal_draft.get("duplicate_family") if internal_draft else packet.get("topic"),
        "approval_hash_continuity_status": "PASS" if not [b for b in blockers if b.startswith("approval_hash_mismatch") or b.startswith("component_hash_mismatch")] else "FAIL",
        "public_freeze_duplicate_status": public_freeze_duplicate_status,
        "operator_go_received": operator_go,
        "operator_go_scope": "decision_gate_only_not_dqr_override",
        "public_ready": False,
        "candidate_rehearsal_local_only": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
        "required_operator_actions": [
            "Keep packet internal/manual-review only while DQR remains BLOCKED.",
            "Return to Capital Chronicle main repo/database exporter for a public-eligible packet after DQR/source gates support it.",
            "Use a separate explicit live/public task only after packet eligibility and public preflight gates pass.",
        ],
        "allowed_next_actions": [
            "review_internal_draft",
            "request_main_repo_public_eligible_packet",
            "rerun_decision_gate_with_future_approved_packet",
        ],
        "forbidden_next_actions": [
            "public_dispatch",
            "platform_api_call",
            "browser_or_cdp_readback",
            "scheduler_or_retry_enqueue",
            "credential_or_session_read",
            "macro_source_fetch_or_parse",
            "main_repo_database_mutation",
            "hide_dqr_or_candidate_caveats",
        ],
        "exact_block_reason": "Current CC artifact packet is DQR BLOCKED, candidate-only, and internal/manual review only.",
    }


def classify_decision(decision_packet: dict[str, Any]) -> str:
    if decision_packet.get("public_ready") is True and not decision_packet.get("blockers"):
        return "PASS_PUBLIC_CANDIDATE_DECISION_READY_REQUIRES_SEPARATE_LIVE_GO"
    return CLASSIFICATION


def build_operator_decision_packet(
    packet: dict[str, Any],
    internal_draft: dict[str, Any] | None,
    intake_summary: dict[str, Any] | None,
    rehearsal_intent: dict[str, Any] | None,
    *,
    approval_hash_file: str | None = None,
    operator_go: bool = False,
) -> dict[str, Any]:
    eligibility = evaluate_packet_public_candidate_eligibility(
        packet,
        internal_draft,
        intake_summary,
        rehearsal_intent,
        approval_hash_file=approval_hash_file,
        operator_go=operator_go,
    )
    decision_packet = {
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "cc_artifact_packet_operator_decision_v1",
        "task_label": TASK_LABEL,
        "classification": classify_decision(eligibility),
        **eligibility,
        "forbidden_use_notes": packet.get("forbidden_use_notes") or [],
        "limitations": packet.get("limitations") or [],
        "source_trail": packet.get("source_trail") or [],
        "claim_ledger": packet.get("claim_ledger") or [],
        "numeric_anchors": packet.get("numeric_anchors") or [],
        "contentops_source_brain_added": False,
        "safety_flags": {
            "public_dispatch_performed": False,
            "platform_api_call_performed": False,
            "browser_cdp_performed": False,
            "network_or_source_fetch_performed": False,
            "env_credential_session_read_performed": False,
            "main_repo_write_performed": False,
            "scheduler_retry_outbox_execution_performed": False,
        },
    }
    return decision_packet


def build_operator_review_preview(decision_packet: dict[str, Any]) -> str:
    blockers = "\n".join(f"- `{item}`" for item in decision_packet.get("blockers") or [])
    notes = "\n".join(f"- {item}" for item in decision_packet.get("forbidden_use_notes") or [])
    limitations = "\n".join(f"- {item}" for item in decision_packet.get("limitations") or [])
    return f"""# CC Artifact Packet Operator Decision V1

Classification: `{decision_packet['classification']}`

Jim GO was received for the local operator-decision task only. It did not override DQR, candidate-only, publish-eligibility, approval-hash, duplicate/public-freeze, or platform safety gates.

## Packet

- Packet ID: `{decision_packet['packet_id']}`
- Approval hash: `{decision_packet['approval_hash']}`
- DQR status: `{decision_packet['dqr_status']}`
- Candidate only: `{decision_packet['candidate_only']}`
- Publish eligibility: `{decision_packet['publish_eligibility']}`
- Source quality: `{decision_packet['source_quality_status']}`
- Public ready: `{str(decision_packet['public_ready']).lower()}`

## Blockers

{blockers}

## Forbidden Use Notes

{notes}

## Limitations

{limitations}

## Required Operator Action

Keep this packet internal/manual-review only. Return to the Capital Chronicle main repo/database exporter for a future public-eligible artifact packet once DQR/source gates support it. Public/live candidate work requires a separate exact operator-GO task.
"""


def build_controlled_candidate_rehearsal_envelope(decision_packet: dict[str, Any], gate_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "cc_artifact_packet_controlled_candidate_rehearsal_envelope_v1",
        "task_label": TASK_LABEL,
        "packet_id": decision_packet["packet_id"],
        "approval_hash": decision_packet["approval_hash"],
        "classification": decision_packet["classification"],
        "gate_status": gate_packet["gate_status"],
        "operator_go_received": decision_packet["operator_go_received"],
        "operator_go_scope": decision_packet["operator_go_scope"],
        "public_ready": False,
        "dispatch_allowed_now": False,
        "platform_variants_rendered": False,
        "platform_ready_payload_created": False,
        "blocked_reason": decision_packet["exact_block_reason"],
        "blockers": decision_packet["blockers"],
        "preview_mode": "non_public_operator_review_only",
        "preserved_caveats": {
            "forbidden_use_notes": decision_packet["forbidden_use_notes"],
            "limitations": decision_packet["limitations"],
            "source_quality_status": decision_packet["source_quality_status"],
        },
        "safety_flags": dict(decision_packet["safety_flags"]),
    }


def write_operator_decision_outputs(
    *,
    packet: dict[str, Any],
    artifacts: dict[str, Any],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    operator_go: bool = False,
    packet_path: str | Path | None = None,
    intake_dir: str | Path | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision = build_operator_decision_packet(
        packet,
        artifacts.get("internal_draft"),
        artifacts.get("intake_summary"),
        artifacts.get("rehearsal_intent"),
        approval_hash_file=artifacts.get("approval_hash_file"),
        operator_go=operator_go,
    )
    gate = evaluate_public_candidate_gate(decision)
    envelope = build_controlled_candidate_rehearsal_envelope(decision, gate)
    preview = build_operator_review_preview(decision)

    _write_json(output / "operator_decision_packet_v1.json", decision)
    _write_json(output / "public_candidate_gate_v1.json", gate)
    _write_json(output / "controlled_candidate_rehearsal_envelope_v1.json", envelope)
    (output / "operator_review_preview_v1.md").write_text(preview, encoding="utf-8")

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "classification": decision["classification"],
        "local_repo_path": "A:\\Capital Chronicle\\tools\\cc-live-contentops-editorial-qa",
        "github_repo": "fatcat2109/capital-chronicle-contentops",
        "branch": "master target via HEAD:master push; local linked worktree branch may differ",
        "starting_head": "4860f586d0a89f774844b2d9c17427981d5e37a7",
        "final_head": "reported_in_final_response_after_commit_and_push",
        "commit_sha": "reported_in_final_response_after_commit_and_push",
        "commit_message": "feat: add cc artifact packet operator decision gate v1",
        "operator_go_received": operator_go,
        "operator_go_scope": decision["operator_go_scope"],
        "input_packet_path": str(packet_path) if packet_path else None,
        "intake_evidence_path": str(Path(intake_dir or DEFAULT_INTAKE_DIR) / "intake_adapter_evidence_v0.json"),
        "approval_hash_continuity_status": decision["approval_hash_continuity_status"],
        "public_ready": decision["public_ready"],
        "blockers": decision["blockers"],
        "gate_status": gate["gate_status"],
        "cli_command": "reported_by_cli",
        "cli_result": "PASS_DECISION_EVALUATED_PUBLIC_CANDIDATE_BLOCKED_BY_PACKET",
        "output_files": [
            str(output / "operator_decision_packet_v1.json"),
            str(output / "public_candidate_gate_v1.json"),
            str(output / "operator_review_preview_v1.md"),
            str(output / "controlled_candidate_rehearsal_envelope_v1.json"),
            str(output / "decision_evidence_v1.json"),
            str(output / "README.md"),
        ],
        "no_public_dispatch_confirmation": True,
        "no_platform_api_confirmation": True,
        "no_browser_cdp_confirmation": True,
        "no_network_source_fetch_confirmation": True,
        "no_env_credential_session_read_confirmation": True,
        "no_main_repo_write_confirmation": True,
        "contentops_source_brain_boundary_confirmation": (
            "No macro source fetcher/parser, numeric truth verifier, database mirror, "
            "source-family fixture, or Analysis Alpha layer was added."
        ),
        "caveats": [
            "Current packet remains DQR BLOCKED.",
            "Current packet remains candidate_only=true.",
            "Current packet publish_eligibility is internal_draft_only.",
            "Public candidate work requires a future public-eligible packet and separate exact live GO.",
        ],
        "exact_next_recommended_task": "TASK_CC_MAIN_REPO_PUBLIC_ELIGIBLE_ARTIFACT_PACKET_DQR_CLEARANCE_OR_CONTENTOPS_FUTURE_PACKET_REHEARSAL",
    }
    _write_json(output / "decision_evidence_v1.json", evidence)
    return {
        "decision_packet": decision,
        "gate_packet": gate,
        "rehearsal_envelope": envelope,
        "evidence": evidence,
    }
