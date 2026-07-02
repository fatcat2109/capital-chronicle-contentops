"""Fail-closed V6 Discord operator source + GO phrase intake builder.

Local/manual only: no Discord send, no webhook validation, no executable outbox,
no approval ledger write, no scheduler, no retry, no provider call, no platform API,
and no credential/env value read.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_GO_PHRASE_INTAKE_TO_REVIEW_ONLY_DRY_RUN_ENVELOPE_NORMALIZATION_V0"
SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_SUPERVISED_DISCORD_DRY_RUN_GATE_TO_OPERATOR_SOURCE_ARTIFACT_AND_GO_PHRASE_INTAKE_V0"
SOURCE_DRY_RUN_GATE_PACKET_ID = "discord_dry_run_gate_f9d4f7f1945dc120"
SOURCE_DRY_RUN_GATE_HASH = "f9d4f7f1945dc120e02c372436122068a76d3b8d117b5cf88b17c45ffe49838a"
GO_PHRASE = "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026"
GO_PHRASE_HASH = hashlib.sha256(GO_PHRASE.encode("utf-8")).hexdigest()

SOURCE_GATE_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE" / "discord_supervised_live_dispatch_dry_run_gate_packet.json"
INTAKE_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_SOURCE_AND_GO_PHRASE_INTAKE"
INBOX_DIR = INTAKE_DIR / "inbox"
NORMALIZED_FILE = INTAKE_DIR / "normalized_candidate" / "normalized_operator_source_go_phrase_candidate.json"
ENVELOPE_FILE = INTAKE_DIR / "review_only_dry_run_envelope" / "discord_review_only_dry_run_envelope_normalization.json"
INTAKE_PACKET_FILE = INTAKE_DIR / "operator_source_go_phrase_intake_packet.json"
PHRASE_EVIDENCE_FILE = INTAKE_DIR / "operator_go_phrase_evidence.json"
DESTINATION_PROOF_FILE = INTAKE_DIR / "destination_binding_proof.json"
SAFETY_SIGNATURE_FILE = INTAKE_DIR / "operator_source_go_phrase_safety_signature.json"

PLACEHOLDER_WORDS = ("todo", "placeholder", "lorem ipsum", "sample only", "viết nội dung thật ở đây")
FORBIDDEN_FINANCIAL_WORDS = (
    "buy", "sell", "hold", "price target", "position sizing", "entry/exit",
    "trade recommendation", "guaranteed prediction", "signal-service",
)
CREDENTIAL_KEYS = (
    "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
    "DISCORD_LIVE_ANNOUNCEMENTS_CHANNEL_LABEL",
    "CONTENTOPS_LIVE_KILL_SWITCH",
)


def _sha(payload: dict[str, Any], *drop_keys: str) -> str:
    clone = dict(payload)
    for key in drop_keys:
        clone.pop(key, None)
    return hashlib.sha256(json.dumps(clone, sort_keys=True, indent=2).encode("utf-8")).hexdigest()


def _load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def _presence(key: str) -> str:
    return "present" if key in os.environ else "missing"


def _first_inbox_file(inbox_dir: Path) -> Path | None:
    files = sorted(path for path in inbox_dir.glob("*") if path.name != ".gitkeep" and path.suffix.lower() in {".json", ".md"})
    return files[0] if files else None


def _extract_source(path: Path | None) -> tuple[dict[str, Any], list[str]]:
    if path is None:
        return (
            {
                "body": "",
                "go_phrase_present": False,
                "go_phrase_valid": False,
                "destination_label": "",
                "destination_binding_confirmed": False,
                "kill_switch_active": False,
                "source_artifact_path": "",
                "source_artifact_hash": "",
                "content_type": "",
            },
            [
                "blocked_missing_operator_source_artifact",
                "blocked_operator_go_phrase_not_recorded",
                "blocked_operator_go_phrase_not_valid",
                "blocked_destination_label_missing",
                "blocked_destination_binding_not_confirmed",
                "blocked_kill_switch_not_active",
            ],
        )

    content = path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    reasons: list[str] = []
    parsed: dict[str, Any] = {}
    body = content
    content_type = "markdown"

    if path.suffix.lower() == ".json":
        content_type = "json"
        try:
            loaded = json.loads(content)
        except json.JSONDecodeError:
            loaded = {}
            reasons.append("blocked_invalid_json_source_artifact")
        if isinstance(loaded, dict):
            parsed = loaded
            body = str(loaded.get("body", ""))
        else:
            reasons.append("blocked_json_source_artifact_not_object")

    lower = body.lower()
    reasons.extend(f"blocked_placeholder_text:{word}" for word in PLACEHOLDER_WORDS if word in lower)
    reasons.extend(f"blocked_forbidden_financial_advice:{word}" for word in FORBIDDEN_FINANCIAL_WORDS if word in lower)
    if not body.strip():
        reasons.append("blocked_missing_discord_body")

    phrase = parsed.get("go_phrase")
    phrase_present = isinstance(phrase, str) and bool(phrase.strip())
    phrase_valid = phrase_present and hashlib.sha256(phrase.encode("utf-8")).hexdigest() == GO_PHRASE_HASH
    destination_label = str(parsed.get("destination_label", "")) if parsed else ""
    destination_confirmed = parsed.get("destination_binding_confirmed") is True
    kill_switch_active = parsed.get("kill_switch_active") is True

    if not phrase_present:
        reasons.append("blocked_operator_go_phrase_not_recorded")
    if not phrase_valid:
        reasons.append("blocked_operator_go_phrase_not_valid")
    if not destination_label.strip():
        reasons.append("blocked_destination_label_missing")
    if not destination_confirmed:
        reasons.append("blocked_destination_binding_not_confirmed")
    if not kill_switch_active:
        reasons.append("blocked_kill_switch_not_active")

    return ({"body": body, "go_phrase_present": phrase_present, "go_phrase_valid": phrase_valid, "destination_label": destination_label, "destination_binding_confirmed": destination_confirmed, "kill_switch_active": kill_switch_active, "source_artifact_path": str(path.relative_to(ROOT)).replace("\\", "/"), "source_artifact_hash": source_hash, "content_type": content_type}, reasons)


def _normalize_review_only_envelope(source: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    body = source["body"]
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else ""
    request_body_preview = {
        "content_hash": body_hash,
        "content_value_stored": False,
        "allowed_mentions": {"parse": []},
    }
    request_body_hash = hashlib.sha256(json.dumps(request_body_preview, sort_keys=True, indent=2).encode("utf-8")).hexdigest()
    envelope = {
        "envelope_kind": "discord_review_only_dry_run_envelope_normalization_v0",
        "envelope_status": "blocked" if reasons else "ready_for_operator_review_not_dispatch",
        "platform_family": "discord",
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "body_hash_preview": body_hash,
        "body_value_stored": False,
        "go_phrase_present": source["go_phrase_present"],
        "go_phrase_valid": source["go_phrase_valid"],
        "go_phrase_value_stored": False,
        "destination_label": source["destination_label"],
        "destination_binding_confirmed": source["destination_binding_confirmed"],
        "normalized_request_method": "POST_JSON",
        "normalized_request_url_value_stored": False,
        "normalized_request_body_hash_preview": request_body_hash,
        "normalized_allowed_mentions_parse": [],
        "review_only": True,
        "dry_run_request_envelope_preview_created": True,
        "dry_run_envelope_normalization_performed": True,
        "dry_run_envelope_value_stored": False,
        "request_envelope_executable": False,
        "dispatchable": False,
        "approved": False,
        "approval_required": True,
        "executable_outbox_entry_created": False,
        "approval_ledger_entry_created": False,
        "webhook_validation_performed": False,
        "discord_api_call_made": False,
        "platform_api_call_made": False,
        "provider_call_made": False,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "blocked_reasons": sorted(set(reasons)),
    }
    envelope["dry_run_request_envelope_hash"] = _sha(envelope, "dry_run_request_envelope_hash", "dry_run_request_envelope_id")
    envelope["dry_run_request_envelope_id"] = f"discord_review_envelope_{envelope['dry_run_request_envelope_hash'][:16]}"
    return envelope


def build_operator_source_go_phrase_intake() -> dict[str, Any]:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENVELOPE_FILE.parent.mkdir(parents=True, exist_ok=True)
    gate = _load_json(SOURCE_GATE_FILE, {})
    credential_presence = {key: _presence(key) for key in CREDENTIAL_KEYS}
    source, reasons = _extract_source(_first_inbox_file(INBOX_DIR))

    if gate.get("dry_run_gate_packet_id") != SOURCE_DRY_RUN_GATE_PACKET_ID:
        reasons.append("source_dry_run_gate_packet_id_mismatch")
    if gate.get("exact_payload_hash") != SOURCE_DRY_RUN_GATE_HASH:
        reasons.append("source_dry_run_gate_hash_mismatch")
    for key, state in credential_presence.items():
        if state != "present":
            reasons.append(f"blocked_{key.lower()}_key_missing")

    body_hash = hashlib.sha256(source["body"].encode("utf-8")).hexdigest() if source["body"] else ""
    normalized = {
        "candidate_kind": "discord_operator_source_go_phrase_candidate_v0",
        "candidate_status": "blocked" if reasons else "ready_for_operator_review_not_dispatch",
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "platform_family": "discord",
        "content_type": source["content_type"],
        "body_hash_preview": body_hash,
        "body_value_stored": False,
        "go_phrase_present": source["go_phrase_present"],
        "go_phrase_valid": source["go_phrase_valid"],
        "go_phrase_value_stored": False,
        "destination_label": source["destination_label"],
        "destination_binding_confirmed": source["destination_binding_confirmed"],
        "kill_switch_active": source["kill_switch_active"],
        "dry_run_envelope_normalization_performed": True,
        "request_envelope_executable": False,
        "dispatchable": False,
        "blocked_reasons": sorted(set(reasons)),
    }
    normalized["candidate_hash"] = _sha(normalized, "candidate_hash")
    normalized["candidate_id"] = f"discord_operator_source_go_{normalized['candidate_hash'][:16]}"
    NORMALIZED_FILE.write_text(json.dumps(normalized, sort_keys=True, indent=2), encoding="utf-8")

    envelope = _normalize_review_only_envelope(source, reasons)
    ENVELOPE_FILE.write_text(json.dumps(envelope, sort_keys=True, indent=2), encoding="utf-8")

    phrase = {"phrase_evidence_kind": "discord_operator_go_phrase_evidence_v0", "expected_phrase_hash": GO_PHRASE_HASH, "phrase_present": source["go_phrase_present"], "phrase_exact_match": source["go_phrase_valid"], "phrase_value_stored": False, "phrase_value_logged": False}
    phrase["phrase_evidence_hash"] = _sha(phrase, "phrase_evidence_hash")
    PHRASE_EVIDENCE_FILE.write_text(json.dumps(phrase, sort_keys=True, indent=2), encoding="utf-8")

    destination = {"destination_proof_kind": "discord_destination_binding_proof_v0", "destination_label": source["destination_label"], "destination_binding_confirmed": source["destination_binding_confirmed"], "webhook_url_value_read_made": False, "webhook_validation_performed": False, "platform_api_request_count": 0}
    destination["destination_proof_hash"] = _sha(destination, "destination_proof_hash")
    DESTINATION_PROOF_FILE.write_text(json.dumps(destination, sort_keys=True, indent=2), encoding="utf-8")

    safety = {"safety_signature_kind": "discord_operator_source_go_phrase_intake_safety_signature_v0", "review_only": True, "source_dry_run_gate_packet_id": SOURCE_DRY_RUN_GATE_PACKET_ID, "source_dry_run_gate_hash": SOURCE_DRY_RUN_GATE_HASH, "dry_run_envelope_normalization_performed": True, "dry_run_request_envelope_preview_created": True, "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"], "request_envelope_executable": False, "executable_outbox_entry_created": False, "approval_ledger_entry_created": False, "webhook_validation_performed": False, "discord_api_call_made": False, "platform_api_call_made": False, "provider_call_made": False, "credential_value_read_made": False, "env_value_read_made": False, "dispatch_request_count": 0, "webhook_request_count": 0, "platform_api_request_count": 0, "ready_for_dispatch": False, "live_action_allowed": False, "blocked_reasons": sorted(set(reasons))}
    safety["safety_signature_hash"] = _sha(safety, "safety_signature_hash")
    SAFETY_SIGNATURE_FILE.write_text(json.dumps(safety, sort_keys=True, indent=2), encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL, "packet_kind": "discord_operator_source_go_phrase_intake_v0", "intake_status": normalized["candidate_status"], "source_task_label": SOURCE_TASK_LABEL, "source_dry_run_gate_packet_id": SOURCE_DRY_RUN_GATE_PACKET_ID, "source_dry_run_gate_exact_payload_hash": SOURCE_DRY_RUN_GATE_HASH, "source_dry_run_gate_path": "docs/automation/V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE/discord_supervised_live_dispatch_dry_run_gate_packet.json", "normalized_candidate_id": normalized["candidate_id"], "normalized_candidate_hash": normalized["candidate_hash"], "operator_source_artifact_path": source["source_artifact_path"], "operator_source_artifact_hash": source["source_artifact_hash"], "operator_go_phrase_expected_hash": GO_PHRASE_HASH, "operator_go_phrase_recorded": source["go_phrase_present"], "operator_go_phrase_valid": source["go_phrase_valid"], "operator_go_phrase_value_stored": False, "destination_label": source["destination_label"], "destination_binding_confirmed": source["destination_binding_confirmed"], "destination_proof_hash": destination["destination_proof_hash"], "credential_presence_check_performed": True, "credential_presence_key_names_only": True, "credential_presence_states": credential_presence, "credential_value_read_made": False, "env_value_read_made": False, "webhook_url_value_read_made": False, "webhook_validation_performed": False, "dry_run_envelope_normalization_performed": True, "dry_run_request_envelope_preview_created": True, "dry_run_request_envelope_id": envelope["dry_run_request_envelope_id"], "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"], "dry_run_request_body_hash_preview": envelope["normalized_request_body_hash_preview"], "dry_run_envelope_value_stored": False, "request_envelope_executable": False, "approval_ledger_entry_created": False, "executable_outbox_entry_created": False, "real_outbox_entry_created": False, "dispatch_outbox_ready": False, "dispatch_attempted": False, "dispatch_request_count": 0, "webhook_request_count": 0, "platform_api_request_count": 0, "scheduler_enabled": False, "retry_enabled": False, "kill_switch_required": True, "kill_switch_active": source["kill_switch_active"], "ready_for_auto_publish": False, "ready_for_dispatch": False, "live_action_allowed": False, "public_url_verification_performed": False, "llm_provider_call_made": False, "provider_call_made": False, "platform_api_used": False, "public_url_fetch_made": False, "browser_session_used": False, "live_publish_performed_by_contentops": False, "enabled_publish_send_dispatch_approve_controls": False, "phrase_evidence_hash": phrase["phrase_evidence_hash"], "safety_signature_hash": safety["safety_signature_hash"], "blocked_reasons": sorted(set(reasons)),
    }
    packet["exact_payload_hash"] = _sha(packet, "exact_payload_hash", "intake_packet_id")
    packet["intake_packet_id"] = f"discord_source_go_intake_{packet['exact_payload_hash'][:16]}"
    INTAKE_PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet


if __name__ == "__main__":
    build_operator_source_go_phrase_intake()
    print("Discord operator source + GO phrase intake generated successfully.")
