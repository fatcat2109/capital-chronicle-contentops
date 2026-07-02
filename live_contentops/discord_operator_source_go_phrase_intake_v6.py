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
TASK_LABEL = "TASK_CONTENTOPS_V6_FIXTURE_REVIEW_READY_TO_REAL_OPERATOR_ARTIFACT_INTAKE_OR_BLOCKED_LIVE_PREFLIGHT_V0"
SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_GO_PHRASE_INTAKE_TO_REVIEW_ONLY_DRY_RUN_ENVELOPE_NORMALIZATION_V0"
SOURCE_DRY_RUN_GATE_PACKET_ID = "discord_dry_run_gate_f9d4f7f1945dc120"
SOURCE_DRY_RUN_GATE_HASH = "f9d4f7f1945dc120e02c372436122068a76d3b8d117b5cf88b17c45ffe49838a"
GO_PHRASE = "CAPITAL_CHRONICLE_SUPERVISED_DISCORD_PILOT_VERIFIED_GO_PHRASE_2026"
GO_PHRASE_HASH = hashlib.sha256(GO_PHRASE.encode("utf-8")).hexdigest()

SOURCE_GATE_FILE = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE" / "discord_supervised_live_dispatch_dry_run_gate_packet.json"
INTAKE_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_SOURCE_AND_GO_PHRASE_INTAKE"
INBOX_DIR = INTAKE_DIR / "inbox"
FIXTURE_DIR = INTAKE_DIR / "fixtures"
FIXTURE_EXAMPLE_FILE = FIXTURE_DIR / "non_real_operator_source_fixture.example.json"
NORMALIZED_FILE = INTAKE_DIR / "normalized_candidate" / "normalized_operator_source_go_phrase_candidate.json"
ENVELOPE_FILE = INTAKE_DIR / "review_only_dry_run_envelope" / "discord_review_only_dry_run_envelope_normalization.json"
INTAKE_PACKET_FILE = INTAKE_DIR / "operator_source_go_phrase_intake_packet.json"
PHRASE_EVIDENCE_FILE = INTAKE_DIR / "operator_go_phrase_evidence.json"
DESTINATION_PROOF_FILE = INTAKE_DIR / "destination_binding_proof.json"
KILL_SWITCH_FILE = INTAKE_DIR / "kill_switch_evidence" / "discord_kill_switch_evidence.json"
CREDENTIAL_PRESENCE_FILE = INTAKE_DIR / "credential_presence_evidence" / "discord_credential_presence_evidence.json"
PRE_DISPATCH_FILE = INTAKE_DIR / "pre_dispatch_readiness" / "discord_pre_dispatch_readiness.json"
FIXTURE_REVIEW_FILE = INTAKE_DIR / "fixture_review" / "discord_operator_source_artifact_fixture_review.json"
SAFETY_SIGNATURE_FILE = INTAKE_DIR / "operator_source_go_phrase_safety_signature.json"
LIVE_PREFLIGHT_FILE = INTAKE_DIR / "live_preflight" / "discord_blocked_live_preflight.json"

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
NON_REAL_FIXTURE_KIND = "non_real_fixture"
MISSING_SOURCE_KIND = "missing"
OPERATOR_SUPPLIED_SOURCE_KIND = "real_operator_artifact"
AMBIGUOUS_SOURCE_KIND = "ambiguous_or_conflicting_artifact"


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


def _fixture_marked(parsed: dict[str, Any]) -> bool:
    return parsed.get("non_real_fixture") is True or parsed.get("fixture_only") is True


def _source_kind(parsed: dict[str, Any], path: Path | None) -> str:
    if path is None:
        return MISSING_SOURCE_KIND
    if _fixture_marked(parsed) and parsed.get("real_operator_artifact_claimed") is True:
        return AMBIGUOUS_SOURCE_KIND
    if _fixture_marked(parsed):
        return NON_REAL_FIXTURE_KIND
    if parsed.get("real_operator_artifact_claimed") is True:
        return OPERATOR_SUPPLIED_SOURCE_KIND
    return AMBIGUOUS_SOURCE_KIND


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
                "operator_source_artifact_kind": MISSING_SOURCE_KIND,
                "operator_source_artifact_real_claimed": False,
                "fixture_only": False,
                "non_real_fixture": False,
                "not_public_postable": True,
                "real_operator_artifact_present": False,
                "real_operator_artifact_intake_ready": False,
                "fixture_vs_real_separation_enforced": True,
                "fixture_review_required": True,
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

    kind = _source_kind(parsed, path)
    non_real_fixture = kind == NON_REAL_FIXTURE_KIND
    fixture_only = non_real_fixture
    real_claimed = kind == OPERATOR_SUPPLIED_SOURCE_KIND
    not_public_postable = bool(parsed.get("not_public_postable", True))
    fixture_vs_real_conflict = _fixture_marked(parsed) and parsed.get("real_operator_artifact_claimed") is True
    if fixture_vs_real_conflict:
        reasons.append("blocked_conflicting_fixture_and_real_artifact_markers")
    if kind == AMBIGUOUS_SOURCE_KIND and not fixture_vs_real_conflict:
        reasons.append("blocked_real_operator_artifact_claim_missing")
    if real_claimed and not_public_postable:
        reasons.append("blocked_real_operator_artifact_not_public_postable")

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

    return (
        {
            "body": body,
            "go_phrase_present": phrase_present,
            "go_phrase_valid": phrase_valid,
            "destination_label": destination_label,
            "destination_binding_confirmed": destination_confirmed,
            "kill_switch_active": kill_switch_active,
            "source_artifact_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "source_artifact_hash": source_hash,
            "content_type": content_type,
            "operator_source_artifact_kind": kind,
            "operator_source_artifact_real_claimed": real_claimed,
            "fixture_only": fixture_only,
            "non_real_fixture": non_real_fixture,
            "not_public_postable": not_public_postable,
            "real_operator_artifact_present": real_claimed,
            "real_operator_artifact_intake_ready": real_claimed and not reasons,
            "fixture_vs_real_separation_enforced": not fixture_vs_real_conflict,
            "fixture_review_required": True,
        },
        reasons,
    )


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
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "fixture_only": source["fixture_only"],
        "not_public_postable": source["not_public_postable"],
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


def _destination_proof(source: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    proof_reasons = sorted(
        reason for reason in set(reasons)
        if reason.startswith("blocked_destination_") or reason == "blocked_missing_operator_source_artifact"
    )
    proof = {
        "destination_proof_kind": "discord_destination_binding_proof_v1",
        "destination_proof_status": "blocked" if proof_reasons else "destination_binding_proof_present",
        "platform_family": "discord",
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "fixture_only": source["fixture_only"],
        "destination_label": source["destination_label"],
        "destination_label_present": bool(source["destination_label"].strip()),
        "destination_label_value_stored": True,
        "destination_binding_confirmed": source["destination_binding_confirmed"],
        "destination_binding_source": "operator_source_artifact" if source["source_artifact_path"] else "missing_operator_source_artifact",
        "webhook_url_value_read_made": False,
        "webhook_url_value_stored": False,
        "webhook_validation_performed": False,
        "discord_api_call_made": False,
        "platform_api_request_count": 0,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "blocked_reasons": proof_reasons,
    }
    proof["destination_proof_hash"] = _sha(proof, "destination_proof_hash", "destination_proof_id")
    proof["destination_proof_id"] = f"discord_destination_proof_{proof['destination_proof_hash'][:16]}"
    return proof


def _kill_switch_evidence(source: dict[str, Any], credential_presence: dict[str, str], reasons: list[str]) -> dict[str, Any]:
    key_state = credential_presence["CONTENTOPS_LIVE_KILL_SWITCH"]
    proof = {
        "kill_switch_evidence_kind": "discord_kill_switch_evidence_v0",
        "kill_switch_status": "active" if source["kill_switch_active"] and key_state == "present" else "blocked",
        "platform_family": "discord",
        "kill_switch_required": True,
        "kill_switch_key_name": "CONTENTOPS_LIVE_KILL_SWITCH",
        "kill_switch_key_presence": key_state,
        "kill_switch_key_presence_checked": True,
        "kill_switch_key_name_only": True,
        "kill_switch_active": source["kill_switch_active"],
        "kill_switch_value_read_made": False,
        "env_value_read_made": False,
        "credential_value_read_made": False,
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "fixture_only": source["fixture_only"],
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "blocked_reasons": sorted(reason for reason in set(reasons) if "kill_switch" in reason),
    }
    proof["kill_switch_evidence_hash"] = _sha(proof, "kill_switch_evidence_hash", "kill_switch_evidence_id")
    proof["kill_switch_evidence_id"] = f"discord_kill_switch_{proof['kill_switch_evidence_hash'][:16]}"
    return proof


def _credential_presence_evidence(credential_presence: dict[str, str], reasons: list[str]) -> dict[str, Any]:
    missing = [key for key, state in credential_presence.items() if state != "present"]
    proof = {
        "credential_presence_evidence_kind": "discord_key_name_only_credential_presence_evidence_v0",
        "credential_presence_status": "blocked" if missing else "all_required_keys_present",
        "platform_family": "discord",
        "required_key_names": list(CREDENTIAL_KEYS),
        "credential_presence_states": credential_presence,
        "missing_key_names": missing,
        "credential_presence_check_performed": True,
        "credential_presence_key_names_only": True,
        "credential_values_read_made": False,
        "env_values_read_made": False,
        "webhook_url_value_read_made": False,
        "webhook_validation_performed": False,
        "platform_api_request_count": 0,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "blocked_reasons": sorted(reason for reason in set(reasons) if reason.endswith("_key_missing")),
    }
    proof["credential_presence_evidence_hash"] = _sha(proof, "credential_presence_evidence_hash", "credential_presence_evidence_id")
    proof["credential_presence_evidence_id"] = f"discord_credential_presence_{proof['credential_presence_evidence_hash'][:16]}"
    return proof


def _fixture_review(
    source: dict[str, Any],
    normalized: dict[str, Any],
    envelope: dict[str, Any],
    destination: dict[str, Any],
    kill_switch: dict[str, Any],
    credential_presence: dict[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    fixture_ready = source["non_real_fixture"] and not reasons
    proof = {
        "fixture_review_kind": "discord_operator_source_artifact_fixture_review_v0",
        "fixture_review_status": "ready_for_fixture_review_not_dispatch" if fixture_ready else "blocked",
        "platform_family": "discord",
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "operator_source_artifact_real_claimed": source["operator_source_artifact_real_claimed"],
        "non_real_fixture": source["non_real_fixture"],
        "fixture_only": source["fixture_only"],
        "not_public_postable": source["not_public_postable"],
        "fixture_review_required": True,
        "fixture_review_ready": fixture_ready,
        "real_operator_artifact_claimed": source["operator_source_artifact_real_claimed"],
        "real_operator_artifact_present": source["real_operator_artifact_present"],
        "real_operator_artifact_intake_ready": source["real_operator_artifact_intake_ready"],
        "fixture_vs_real_separation_enforced": source["fixture_vs_real_separation_enforced"],
        "real_operator_artifact_required_for_dispatch": True,
        "normalized_candidate_id": normalized["candidate_id"],
        "normalized_candidate_hash": normalized["candidate_hash"],
        "dry_run_request_envelope_id": envelope["dry_run_request_envelope_id"],
        "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"],
        "destination_proof_id": destination["destination_proof_id"],
        "destination_proof_hash": destination["destination_proof_hash"],
        "kill_switch_evidence_id": kill_switch["kill_switch_evidence_id"],
        "kill_switch_evidence_hash": kill_switch["kill_switch_evidence_hash"],
        "credential_presence_evidence_id": credential_presence["credential_presence_evidence_id"],
        "credential_presence_evidence_hash": credential_presence["credential_presence_evidence_hash"],
        "go_phrase_valid": source["go_phrase_valid"],
        "go_phrase_value_stored": False,
        "body_value_stored": False,
        "review_only": True,
        "request_envelope_executable": False,
        "dispatchable": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "webhook_validation_performed": False,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "fixture_caveats": [
            "non_real_fixture_never_claimed_as_real",
            "fixture_review_ready_is_not_dispatch_ready",
            "real_operator_artifact_required_before_live_authorization",
        ],
        "blocked_reasons": sorted(set(reasons)),
    }
    proof["fixture_review_hash"] = _sha(proof, "fixture_review_hash", "fixture_review_id")
    proof["fixture_review_id"] = f"discord_fixture_review_{proof['fixture_review_hash'][:16]}"
    return proof


def _live_preflight(
    source: dict[str, Any],
    normalized: dict[str, Any],
    envelope: dict[str, Any],
    destination: dict[str, Any],
    kill_switch: dict[str, Any],
    credential_presence: dict[str, Any],
    fixture_review: dict[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    preflight_reasons = set(reasons)
    if source["operator_source_artifact_kind"] != OPERATOR_SUPPLIED_SOURCE_KIND:
        preflight_reasons.add("blocked_real_operator_artifact_required")
    if source["non_real_fixture"] or source["fixture_only"]:
        preflight_reasons.add("blocked_non_real_fixture_cannot_satisfy_real_operator_artifact")
    if not source["fixture_vs_real_separation_enforced"]:
        preflight_reasons.add("blocked_fixture_vs_real_separation_failed")
    if not source["real_operator_artifact_intake_ready"]:
        preflight_reasons.add("blocked_real_operator_artifact_intake_not_ready")
    if credential_presence["credential_presence_status"] != "all_required_keys_present":
        preflight_reasons.add("blocked_required_credential_key_presence_incomplete")
    if kill_switch["kill_switch_status"] != "active":
        preflight_reasons.add("blocked_kill_switch_evidence_not_active")
    if destination["destination_proof_status"] != "destination_binding_proof_present":
        preflight_reasons.add("blocked_destination_proof_not_present")
    ready_for_real_intake_review = not preflight_reasons
    proof = {
        "live_preflight_kind": "discord_real_operator_artifact_blocked_live_preflight_v0",
        "live_preflight_status": "ready_for_real_operator_artifact_review_not_dispatch" if ready_for_real_intake_review else "blocked",
        "platform_family": "discord",
        "source_artifact_path": source["source_artifact_path"],
        "source_artifact_hash": source["source_artifact_hash"],
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "operator_source_artifact_real_claimed": source["operator_source_artifact_real_claimed"],
        "real_operator_artifact_present": source["real_operator_artifact_present"],
        "real_operator_artifact_intake_ready": source["real_operator_artifact_intake_ready"],
        "fixture_vs_real_separation_enforced": source["fixture_vs_real_separation_enforced"],
        "non_real_fixture": source["non_real_fixture"],
        "fixture_only": source["fixture_only"],
        "not_public_postable": source["not_public_postable"],
        "fixture_review_id": fixture_review["fixture_review_id"],
        "fixture_review_hash": fixture_review["fixture_review_hash"],
        "normalized_candidate_id": normalized["candidate_id"],
        "normalized_candidate_hash": normalized["candidate_hash"],
        "dry_run_request_envelope_id": envelope["dry_run_request_envelope_id"],
        "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"],
        "destination_proof_id": destination["destination_proof_id"],
        "destination_proof_hash": destination["destination_proof_hash"],
        "kill_switch_evidence_id": kill_switch["kill_switch_evidence_id"],
        "kill_switch_evidence_hash": kill_switch["kill_switch_evidence_hash"],
        "credential_presence_evidence_id": credential_presence["credential_presence_evidence_id"],
        "credential_presence_evidence_hash": credential_presence["credential_presence_evidence_hash"],
        "go_phrase_present": source["go_phrase_present"],
        "go_phrase_valid": source["go_phrase_valid"],
        "go_phrase_value_stored": False,
        "body_value_stored": False,
        "review_only": True,
        "request_envelope_executable": False,
        "dispatchable": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "webhook_validation_performed": False,
        "credential_value_read_made": False,
        "env_value_read_made": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "blocked_reasons": sorted(preflight_reasons),
    }
    proof["live_preflight_hash"] = _sha(proof, "live_preflight_hash", "live_preflight_id")
    proof["live_preflight_id"] = f"discord_live_preflight_{proof['live_preflight_hash'][:16]}"
    return proof


def _pre_dispatch_readiness(
    normalized: dict[str, Any],
    envelope: dict[str, Any],
    destination: dict[str, Any],
    kill_switch: dict[str, Any],
    credential_presence: dict[str, Any],
    fixture_review: dict[str, Any],
    live_preflight: dict[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    review_ready = not reasons
    readiness = {
        "pre_dispatch_readiness_kind": "discord_normalized_pre_dispatch_readiness_v0",
        "pre_dispatch_readiness_status": "ready_for_operator_review_not_dispatch" if review_ready else "blocked",
        "platform_family": "discord",
        "normalized_candidate_id": normalized["candidate_id"],
        "normalized_candidate_hash": normalized["candidate_hash"],
        "dry_run_request_envelope_id": envelope["dry_run_request_envelope_id"],
        "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"],
        "destination_proof_id": destination["destination_proof_id"],
        "destination_proof_hash": destination["destination_proof_hash"],
        "kill_switch_evidence_id": kill_switch["kill_switch_evidence_id"],
        "kill_switch_evidence_hash": kill_switch["kill_switch_evidence_hash"],
        "credential_presence_evidence_id": credential_presence["credential_presence_evidence_id"],
        "credential_presence_evidence_hash": credential_presence["credential_presence_evidence_hash"],
        "fixture_review_id": fixture_review["fixture_review_id"],
        "fixture_review_hash": fixture_review["fixture_review_hash"],
        "live_preflight_id": live_preflight["live_preflight_id"],
        "live_preflight_hash": live_preflight["live_preflight_hash"],
        "live_preflight_status": live_preflight["live_preflight_status"],
        "operator_source_artifact_kind": normalized["operator_source_artifact_kind"],
        "fixture_only": normalized["fixture_only"],
        "not_public_postable": normalized["not_public_postable"],
        "real_operator_artifact_present": normalized["real_operator_artifact_present"],
        "real_operator_artifact_intake_ready": normalized["real_operator_artifact_intake_ready"],
        "fixture_vs_real_separation_enforced": normalized["fixture_vs_real_separation_enforced"],
        "operator_review_ready": review_ready,
        "fixture_review_ready": fixture_review["fixture_review_ready"],
        "normalized_pre_dispatch_readiness_evaluated": True,
        "destination_binding_confirmed": destination["destination_binding_confirmed"],
        "kill_switch_active": kill_switch["kill_switch_active"],
        "credential_presence_status": credential_presence["credential_presence_status"],
        "review_only": True,
        "request_envelope_executable": False,
        "dispatchable": False,
        "dispatch_outbox_ready": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "webhook_validation_performed": False,
        "dispatch_request_count": 0,
        "webhook_request_count": 0,
        "platform_api_request_count": 0,
        "blocked_reasons": sorted(set(reasons)),
    }
    readiness["pre_dispatch_readiness_hash"] = _sha(readiness, "pre_dispatch_readiness_hash", "pre_dispatch_readiness_id")
    readiness["pre_dispatch_readiness_id"] = f"discord_pre_dispatch_{readiness['pre_dispatch_readiness_hash'][:16]}"
    return readiness


def _write_fixture_example() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixture = {
        "fixture_kind": "discord_operator_source_artifact_non_real_fixture_v0",
        "non_real_fixture": True,
        "fixture_only": True,
        "not_public_postable": True,
        "real_operator_artifact_claimed": False,
        "body": "Capital Chronicle supervised Discord pilot fixture update. Local review only; not public postable.",
        "go_phrase": GO_PHRASE,
        "destination_label": "discord-live-announcements",
        "destination_binding_confirmed": True,
        "kill_switch_active": True,
        "fixture_caveat": "Non-real fixture for parser/normalizer tests only. Do not treat as live operator artifact.",
    }
    FIXTURE_EXAMPLE_FILE.write_text(json.dumps(fixture, sort_keys=True, indent=2), encoding="utf-8")


def build_operator_source_go_phrase_intake() -> dict[str, Any]:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    _write_fixture_example()
    for path in [NORMALIZED_FILE, ENVELOPE_FILE, DESTINATION_PROOF_FILE, KILL_SWITCH_FILE, CREDENTIAL_PRESENCE_FILE, PRE_DISPATCH_FILE, FIXTURE_REVIEW_FILE, LIVE_PREFLIGHT_FILE]:
        path.parent.mkdir(parents=True, exist_ok=True)
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
        "operator_source_artifact_kind": source["operator_source_artifact_kind"],
        "operator_source_artifact_real_claimed": source["operator_source_artifact_real_claimed"],
        "fixture_only": source["fixture_only"],
        "non_real_fixture": source["non_real_fixture"],
        "not_public_postable": source["not_public_postable"],
        "real_operator_artifact_present": source["real_operator_artifact_present"],
        "real_operator_artifact_intake_ready": source["real_operator_artifact_intake_ready"],
        "fixture_vs_real_separation_enforced": source["fixture_vs_real_separation_enforced"],
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
        "normalized_pre_dispatch_readiness_evaluated": True,
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

    destination = _destination_proof(source, reasons)
    DESTINATION_PROOF_FILE.write_text(json.dumps(destination, sort_keys=True, indent=2), encoding="utf-8")

    kill_switch = _kill_switch_evidence(source, credential_presence, reasons)
    KILL_SWITCH_FILE.write_text(json.dumps(kill_switch, sort_keys=True, indent=2), encoding="utf-8")

    credential_evidence = _credential_presence_evidence(credential_presence, reasons)
    CREDENTIAL_PRESENCE_FILE.write_text(json.dumps(credential_evidence, sort_keys=True, indent=2), encoding="utf-8")

    fixture_review = _fixture_review(source, normalized, envelope, destination, kill_switch, credential_evidence, reasons)
    FIXTURE_REVIEW_FILE.write_text(json.dumps(fixture_review, sort_keys=True, indent=2), encoding="utf-8")

    live_preflight = _live_preflight(source, normalized, envelope, destination, kill_switch, credential_evidence, fixture_review, reasons)
    LIVE_PREFLIGHT_FILE.write_text(json.dumps(live_preflight, sort_keys=True, indent=2), encoding="utf-8")

    pre_dispatch = _pre_dispatch_readiness(normalized, envelope, destination, kill_switch, credential_evidence, fixture_review, live_preflight, reasons)
    PRE_DISPATCH_FILE.write_text(json.dumps(pre_dispatch, sort_keys=True, indent=2), encoding="utf-8")

    safety = {"safety_signature_kind": "discord_operator_source_go_phrase_intake_safety_signature_v2", "review_only": True, "source_dry_run_gate_packet_id": SOURCE_DRY_RUN_GATE_PACKET_ID, "source_dry_run_gate_hash": SOURCE_DRY_RUN_GATE_HASH, "operator_source_artifact_kind": source["operator_source_artifact_kind"], "operator_source_artifact_real_claimed": source["operator_source_artifact_real_claimed"], "fixture_only": source["fixture_only"], "not_public_postable": source["not_public_postable"], "dry_run_envelope_normalization_performed": True, "dry_run_request_envelope_preview_created": True, "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"], "destination_proof_hash": destination["destination_proof_hash"], "kill_switch_evidence_hash": kill_switch["kill_switch_evidence_hash"], "credential_presence_evidence_hash": credential_evidence["credential_presence_evidence_hash"], "fixture_review_hash": fixture_review["fixture_review_hash"], "live_preflight_hash": live_preflight["live_preflight_hash"], "live_preflight_status": live_preflight["live_preflight_status"], "real_operator_artifact_present": source["real_operator_artifact_present"], "real_operator_artifact_intake_ready": source["real_operator_artifact_intake_ready"], "fixture_vs_real_separation_enforced": source["fixture_vs_real_separation_enforced"], "pre_dispatch_readiness_hash": pre_dispatch["pre_dispatch_readiness_hash"], "request_envelope_executable": False, "executable_outbox_entry_created": False, "approval_ledger_entry_created": False, "webhook_validation_performed": False, "discord_api_call_made": False, "platform_api_call_made": False, "provider_call_made": False, "credential_value_read_made": False, "env_value_read_made": False, "dispatch_request_count": 0, "webhook_request_count": 0, "platform_api_request_count": 0, "ready_for_dispatch": False, "live_action_allowed": False, "blocked_reasons": sorted(set(reasons))}
    safety["safety_signature_hash"] = _sha(safety, "safety_signature_hash")
    SAFETY_SIGNATURE_FILE.write_text(json.dumps(safety, sort_keys=True, indent=2), encoding="utf-8")

    packet = {
        "task_label": TASK_LABEL, "packet_kind": "discord_operator_source_go_phrase_intake_v2", "intake_status": normalized["candidate_status"], "source_task_label": SOURCE_TASK_LABEL, "source_dry_run_gate_packet_id": SOURCE_DRY_RUN_GATE_PACKET_ID, "source_dry_run_gate_exact_payload_hash": SOURCE_DRY_RUN_GATE_HASH, "source_dry_run_gate_path": "docs/automation/V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE/discord_supervised_live_dispatch_dry_run_gate_packet.json", "normalized_candidate_id": normalized["candidate_id"], "normalized_candidate_hash": normalized["candidate_hash"], "operator_source_artifact_path": source["source_artifact_path"], "operator_source_artifact_hash": source["source_artifact_hash"], "operator_source_artifact_kind": source["operator_source_artifact_kind"], "operator_source_artifact_real_claimed": source["operator_source_artifact_real_claimed"], "non_real_fixture": source["non_real_fixture"], "fixture_only": source["fixture_only"], "not_public_postable": source["not_public_postable"], "real_operator_artifact_present": source["real_operator_artifact_present"], "real_operator_artifact_intake_ready": source["real_operator_artifact_intake_ready"], "fixture_vs_real_separation_enforced": source["fixture_vs_real_separation_enforced"], "operator_go_phrase_expected_hash": GO_PHRASE_HASH, "operator_go_phrase_recorded": source["go_phrase_present"], "operator_go_phrase_valid": source["go_phrase_valid"], "operator_go_phrase_value_stored": False, "destination_label": source["destination_label"], "destination_binding_confirmed": source["destination_binding_confirmed"], "destination_proof_id": destination["destination_proof_id"], "destination_proof_hash": destination["destination_proof_hash"], "kill_switch_evidence_id": kill_switch["kill_switch_evidence_id"], "kill_switch_evidence_hash": kill_switch["kill_switch_evidence_hash"], "credential_presence_evidence_id": credential_evidence["credential_presence_evidence_id"], "credential_presence_evidence_hash": credential_evidence["credential_presence_evidence_hash"], "fixture_review_id": fixture_review["fixture_review_id"], "fixture_review_hash": fixture_review["fixture_review_hash"], "fixture_review_status": fixture_review["fixture_review_status"], "fixture_review_ready": fixture_review["fixture_review_ready"], "live_preflight_id": live_preflight["live_preflight_id"], "live_preflight_hash": live_preflight["live_preflight_hash"], "live_preflight_status": live_preflight["live_preflight_status"], "pre_dispatch_readiness_id": pre_dispatch["pre_dispatch_readiness_id"], "pre_dispatch_readiness_hash": pre_dispatch["pre_dispatch_readiness_hash"], "normalized_pre_dispatch_readiness_evaluated": True, "operator_review_ready": pre_dispatch["operator_review_ready"], "credential_presence_check_performed": True, "credential_presence_key_names_only": True, "credential_presence_states": credential_presence, "credential_value_read_made": False, "env_value_read_made": False, "webhook_url_value_read_made": False, "webhook_validation_performed": False, "dry_run_envelope_normalization_performed": True, "dry_run_request_envelope_preview_created": True, "dry_run_request_envelope_id": envelope["dry_run_request_envelope_id"], "dry_run_request_envelope_hash": envelope["dry_run_request_envelope_hash"], "dry_run_request_body_hash_preview": envelope["normalized_request_body_hash_preview"], "dry_run_envelope_value_stored": False, "request_envelope_executable": False, "approval_ledger_entry_created": False, "executable_outbox_entry_created": False, "real_outbox_entry_created": False, "dispatch_outbox_ready": False, "dispatch_attempted": False, "dispatch_request_count": 0, "webhook_request_count": 0, "platform_api_request_count": 0, "scheduler_enabled": False, "retry_enabled": False, "kill_switch_required": True, "kill_switch_active": source["kill_switch_active"], "ready_for_auto_publish": False, "ready_for_dispatch": False, "live_action_allowed": False, "public_url_verification_performed": False, "llm_provider_call_made": False, "provider_call_made": False, "platform_api_used": False, "public_url_fetch_made": False, "browser_session_used": False, "live_publish_performed_by_contentops": False, "enabled_publish_send_dispatch_approve_controls": False, "phrase_evidence_hash": phrase["phrase_evidence_hash"], "safety_signature_hash": safety["safety_signature_hash"], "blocked_reasons": sorted(set(reasons)),
    }
    packet["exact_payload_hash"] = _sha(packet, "exact_payload_hash", "intake_packet_id")
    packet["intake_packet_id"] = f"discord_source_go_intake_{packet['exact_payload_hash'][:16]}"
    INTAKE_PACKET_FILE.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding="utf-8")
    return packet


if __name__ == "__main__":
    build_operator_source_go_phrase_intake()
    print("Discord operator source + GO phrase intake generated successfully.")
