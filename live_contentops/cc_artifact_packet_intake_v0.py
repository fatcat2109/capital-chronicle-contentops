"""ContentOps intake adapter for Capital Chronicle Content Artifact Packet V0.

ContentOps consumes exported packets from the Capital Chronicle database/exporter
pipeline. This adapter validates, renders, hashes, and prepares local-only
review artifacts; it does not fetch macro sources, verify numeric truth, mutate
the main repo, read credentials/sessions, or invoke platform adapters.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from .cc_artifact_packet_approval_v0 import (
    HANDOFF_COMMIT,
    build_approval_hash,
    canonical_json_hash,
    compute_component_hashes,
)
from .cc_artifact_packet_rehearsal_bridge_v0 import build_rehearsal_intent
from .cc_artifact_packet_render_v0 import render_internal_draft

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = ROOT / "schemas" / "cc_content_artifact_packet_v0.schema.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "automation" / "CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0"

TASK_LABEL = "TASK_CONTENTOPS_CC_ARTIFACT_PACKET_INTAKE_TO_REHEARSAL_BRIDGE_HEAVY_BATCH_V0"
CLASSIFICATION_WITH_CAVEAT = "PASS_WITH_CAVEAT_CONTENTOPS_CC_PACKET_INTAKE_V0"


class PacketValidationError(ValueError):
    """Raised when a packet fails schema or ContentOps guard validation."""


def load_packet(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_schema(path: str | Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_schema(packet: dict[str, Any], schema: dict[str, Any]) -> None:
    try:
        jsonschema.validate(instance=packet, schema=schema)
    except jsonschema.ValidationError as exc:
        raise PacketValidationError(f"schema validation failed: {exc.message}") from exc


def _require_non_empty_list(packet: dict[str, Any], field: str) -> None:
    value = packet.get(field)
    if not isinstance(value, list) or not value:
        raise PacketValidationError(f"{field} is required and must be non-empty")


def _is_negated_instruction(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered.startswith(("do not ", "never ", "must not ", "no "))


def _forbidden_instruction_hit(instruction: str) -> str | None:
    lowered = instruction.lower()
    if _is_negated_instruction(lowered):
        return None
    forbidden_phrases = (
        "fetch source",
        "fetch macro",
        "download source",
        "scrape",
        "verify numeric truth",
        "verify source truth",
        "parse macro",
        "ingest macro",
        "mutate main repo",
        "write main repo",
        "modify main repo",
        "write database",
        "mutate database",
        "publish externally",
        "public dispatch",
        "post externally",
        "send externally",
        "auto publish",
    )
    for phrase in forbidden_phrases:
        if phrase in lowered:
            return phrase
    return None


def _text_blob(values: Any) -> str:
    return json.dumps(values, sort_keys=True, ensure_ascii=False).lower()


def _has_required_renderable_caveats(packet: dict[str, Any]) -> bool:
    renderable = _text_blob({
        "forbidden_use_notes": packet.get("forbidden_use_notes"),
        "limitations": packet.get("limitations"),
        "contentops_instructions": packet.get("contentops_instructions"),
        "source_quality_status": packet.get("source_quality_status"),
    })
    return (
        "dqr" in renderable
        and "blocked" in renderable
        and ("candidate" in renderable or "non-authoritative" in renderable or "degraded" in renderable)
    )


def validate_contentops_guards(packet: dict[str, Any]) -> None:
    if "dqr_status" not in packet:
        raise PacketValidationError("missing dqr_status")
    if packet.get("dqr_status") != "BLOCKED":
        raise PacketValidationError("V0 ContentOps intake only accepts dqr_status=BLOCKED")
    if packet.get("candidate_only") is not True:
        raise PacketValidationError("candidate_only must be true")

    publish_eligibility = packet.get("publish_eligibility")
    if publish_eligibility == "public_auto":
        raise PacketValidationError("publish_eligibility=public_auto is forbidden")
    if isinstance(publish_eligibility, str) and packet.get("dqr_status") == "BLOCKED":
        if "public" in publish_eligibility and publish_eligibility not in {"internal_draft_only", "manual_review_only"}:
            raise PacketValidationError("DQR BLOCKED packet cannot imply public dispatch")

    _require_non_empty_list(packet, "forbidden_use_notes")
    _require_non_empty_list(packet, "source_trail")
    _require_non_empty_list(packet, "claim_ledger")
    if "numeric_anchors" not in packet:
        raise PacketValidationError("missing numeric_anchors")
    if not isinstance(packet.get("numeric_anchors"), list):
        raise PacketValidationError("numeric_anchors must be a list")
    _require_non_empty_list(packet, "limitations")

    for index, anchor in enumerate(packet.get("numeric_anchors", [])):
        if "authority_status" not in anchor:
            raise PacketValidationError(f"numeric_anchors[{index}] missing authority_status")
        caveat = anchor.get("caveat")
        if not isinstance(caveat, str) or not caveat.strip():
            raise PacketValidationError(f"numeric_anchors[{index}] missing caveat")
        authority_status = anchor.get("authority_status")
        source_and_caveat = f"{anchor.get('source_ref', '')} {caveat}".lower()
        contradiction_terms = (
            "candidate",
            "proxy",
            "non-authoritative",
            "blocked",
            "unavailable",
            "staging",
            "deferred_paid_proxy",
            "fred",
            "mt5",
            "yahoo",
            "polymarket",
        )
        if authority_status == "exact" and any(term in source_and_caveat for term in contradiction_terms):
            raise PacketValidationError(f"numeric_anchors[{index}] silently promotes candidate/proxy data to exact")

    for index, claim in enumerate(packet.get("claim_ledger", [])):
        if claim.get("support_status") in {"unsupported", "blocked"} and not claim.get("forbidden_wording"):
            raise PacketValidationError(f"claim_ledger[{index}] lacks forbidden wording for unsupported/blocked claim")

    for instruction in packet.get("contentops_instructions", []):
        hit = _forbidden_instruction_hit(instruction)
        if hit:
            raise PacketValidationError(f"forbidden ContentOps instruction: {hit}")

    if not _has_required_renderable_caveats(packet):
        raise PacketValidationError("renderable DQR/source-quality/candidate caveats are missing")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_summary(
    packet: dict[str, Any],
    internal_draft: dict[str, Any],
    rehearsal_intent: dict[str, Any],
    output_dir: Path,
    dry_run: bool,
) -> dict[str, Any]:
    component_hashes = compute_component_hashes(packet)
    return {
        "task_label": TASK_LABEL,
        "classification": CLASSIFICATION_WITH_CAVEAT,
        "dry_run": dry_run,
        "packet_id": packet["packet_id"],
        "schema_version": packet["schema_version"],
        "handoff_commit": HANDOFF_COMMIT,
        "sample_packet.main_repo_head": packet["main_repo_head"],
        "dqr_status": packet["dqr_status"],
        "candidate_only": packet["candidate_only"],
        "publish_eligibility": packet["publish_eligibility"],
        "source_quality_status": packet["source_quality_status"],
        "component_hashes": component_hashes,
        "approval_hash": internal_draft["approval_hash"],
        "internal_draft_path": str(output_dir / "internal_draft_v0.json"),
        "approval_hash_path": str(output_dir / "approval_hash_v0.txt"),
        "rehearsal_intent_path": str(output_dir / "rehearsal_intent_v0.json"),
        "approval_queue_integration_status": "caveated_dry_run_output_only_existing_queue_not_stable_for_v0_packet",
        "dry_run_bridge_status": rehearsal_intent["bridge_status"],
        "public_ready": False,
        "public_dispatch_performed": False,
        "platform_api_call_performed": False,
        "network_call_performed": False,
        "credential_or_session_read_performed": False,
        "main_repo_write_performed": False,
        "contentops_source_brain_added": False,
        "next_required_operator_step": "Separate operator decision and future packet-to-public-candidate task.",
    }


def intake_packet(
    packet_path: str | Path,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = True,
) -> dict[str, Any]:
    if dry_run is not True:
        raise PacketValidationError("V0 intake adapter only supports dry_run=True")

    packet = load_packet(packet_path)
    schema = load_schema(schema_path)
    validate_schema(packet, schema)
    validate_contentops_guards(packet)

    internal_draft = render_internal_draft(packet)
    rehearsal_intent = build_rehearsal_intent(internal_draft)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    _write_json(output / "internal_draft_v0.json", internal_draft)
    _write_json(output / "rehearsal_intent_v0.json", rehearsal_intent)
    (output / "approval_hash_v0.txt").write_text(internal_draft["approval_hash"] + "\n", encoding="utf-8")
    summary = _build_summary(packet, internal_draft, rehearsal_intent, output, dry_run)
    _write_json(output / "intake_dry_run_summary_v0.json", summary)
    return summary


__all__ = [
    "CLASSIFICATION_WITH_CAVEAT",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_SCHEMA_PATH",
    "HANDOFF_COMMIT",
    "PacketValidationError",
    "TASK_LABEL",
    "build_approval_hash",
    "canonical_json_hash",
    "compute_component_hashes",
    "intake_packet",
    "load_packet",
    "load_schema",
    "validate_contentops_guards",
    "validate_schema",
]
