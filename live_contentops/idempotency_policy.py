"""Deterministic idempotency policy for dispatch preparation.

Pure stdlib value helpers. No network, process environment, credential hydration, or retry behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_R1_COMPLETION_PATCH_V0"
MODEL = "contentops.idempotency_policy"
MODEL_VERSION = "0174U2_IDEMPOTENCY_POLICY_R1"

IDEMPOTENCY_KEY_FIELDS: tuple[str, ...] = (
    "payload_hash",
    "platform_id",
    "payload_class_id",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "policy_snapshot_id",
    "approval_ledger_entry_id",
    "approval_event_id",
    "dispatch_intent_class",
)

SECRET_KEY_RE = re.compile(
    r"(?i)(token|secret|password|cookie|session|authorization|bearer|api[_-]?key|private_key)"
)
SECRET_VALUE_RE = re.compile(
    r"(\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b|bearer\s+[A-Za-z0-9._\-]{20,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IdempotencyDecision:
    """Value-only idempotency decision."""

    status: str
    idempotency_key: str | None
    idempotency_key_short: str | None
    duplicate: bool
    blocked_reasons: tuple[str, ...]
    duplicate_action: str = "new_candidate_allowed"
    manual_fallback_status: str = "manual_fallback_not_required"
    request_budget: int = 1
    dispatch_performed: bool = False
    live_request_performed: bool = False
    platform_api_called: bool = False
    credential_hydrated: bool = False
    auto_retry_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "idempotency_key_short": self.idempotency_key_short,
            "duplicate": self.duplicate,
            "duplicate_action": self.duplicate_action,
            "manual_fallback_status": self.manual_fallback_status,
            "request_budget": self.request_budget,
            "blocked_reasons": list(self.blocked_reasons),
            "dispatch_performed": self.dispatch_performed,
            "live_request_performed": self.live_request_performed,
            "platform_api_called": self.platform_api_called,
            "credential_hydrated": self.credential_hydrated,
            "auto_retry_allowed": self.auto_retry_allowed,
        }


def canonical_json(value: Any) -> str:
    """Stable JSON serialization used for hashes and audit checksums."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def scan_for_secret_risk(value: Any) -> list[str]:
    """Return sorted secret-risk paths. Conservative and fail-closed."""
    findings: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                key_s = str(key)
                child_path = f"{path}.{key_s}" if path else key_s
                if SECRET_KEY_RE.search(key_s):
                    findings.append(child_path)
                walk(child, child_path)
        elif isinstance(node, (list, tuple)):
            for idx, child in enumerate(node):
                walk(child, f"{path}[{idx}]")
        elif isinstance(node, str) and SECRET_VALUE_RE.search(node):
            findings.append(path or "<value>")

    walk(value, "")
    return sorted(set(findings))


def compute_idempotency_basis(candidate: dict[str, Any]) -> dict[str, Any]:
    """Extract non-secret authority fields used for idempotency."""
    return {field: candidate.get(field) for field in IDEMPOTENCY_KEY_FIELDS}


def compute_idempotency_key(candidate: dict[str, Any]) -> str:
    """Compute SHA-256 over canonical non-secret idempotency basis."""
    findings = scan_for_secret_risk(candidate)
    if findings:
        raise ValueError(f"secret risk in idempotency candidate: {findings}")
    basis = compute_idempotency_basis(candidate)
    missing = [field for field, val in basis.items() if val in (None, "")]
    if missing:
        raise ValueError(f"missing idempotency fields: {missing}")
    return sha256(canonical_json(basis).encode("utf-8")).hexdigest()


def idempotency_key_short(key: str | None) -> str | None:
    return key[:12] if key else None


def is_duplicate_success(result: dict[str, Any] | IdempotencyDecision) -> bool:
    """True only when prior successful key exists and must suppress candidate."""
    data = result.as_dict() if isinstance(result, IdempotencyDecision) else dict(result or {})
    status = str(data.get("status") or "")
    return data.get("duplicate") is True and status in {"duplicate_blocked", "success_duplicate", "duplicate_success"}


def classify_duplicate_action(result: dict[str, Any] | IdempotencyDecision | None) -> dict[str, Any]:
    """Classify duplicate result. Unknown never auto-retries; route manual."""
    data = result.as_dict() if isinstance(result, IdempotencyDecision) else dict(result or {})
    status = data.get("status")
    duplicate = data.get("duplicate")
    if duplicate is True and status in {"duplicate_blocked", "success_duplicate", "duplicate_success"}:
        action = "suppress_candidate_duplicate_success"
        manual = "manual_fallback_not_required"
        blockers = ["duplicate_idempotency_key"]
    elif status in (None, "", "unknown", "unknown_result"):
        action = "manual_reconciliation_required_unknown_result"
        manual = "manual_fallback_required"
        blockers = ["idempotency_result_unknown_manual_reconciliation_required"]
    elif status == "blocked":
        action = "block_candidate"
        manual = "manual_fallback_required"
        blockers = list(data.get("blocked_reasons") or ["idempotency_blocked"])
    else:
        action = "allow_new_local_candidate"
        manual = "manual_fallback_not_required"
        blockers = []
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "duplicate_action": action,
        "manual_fallback_status": manual,
        "auto_retry_allowed": False,
        "request_budget": 1,
        "blocked_reasons": blockers,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
    }


def decide_idempotency(candidate: dict[str, Any], existing_keys: set[str] | tuple[str, ...] | list[str] | None = None) -> IdempotencyDecision:
    """Decide new vs duplicate without mutating caller state."""
    existing = set(existing_keys or ())
    try:
        key = compute_idempotency_key(candidate)
    except ValueError as exc:
        return IdempotencyDecision(
            status="blocked",
            idempotency_key=None,
            idempotency_key_short=None,
            duplicate=False,
            blocked_reasons=(str(exc),),
            duplicate_action="block_candidate",
            manual_fallback_status="manual_fallback_required",
        )
    duplicate = key in existing
    classified = classify_duplicate_action({"status": "duplicate_blocked" if duplicate else "new_key_allowed_for_local_outbox_only", "duplicate": duplicate})
    return IdempotencyDecision(
        status="duplicate_blocked" if duplicate else "new_key_allowed_for_local_outbox_only",
        idempotency_key=key,
        idempotency_key_short=idempotency_key_short(key),
        duplicate=duplicate,
        blocked_reasons=("duplicate_idempotency_key",) if duplicate else (),
        duplicate_action=classified["duplicate_action"],
        manual_fallback_status=classified["manual_fallback_status"],
    )


def idempotency_policy_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "helper_api_completed": ["is_duplicate_success", "classify_duplicate_action"],
        "idempotency_key_algorithm": "sha256",
        "idempotency_key_fields": list(IDEMPOTENCY_KEY_FIELDS),
        "same_inputs_same_key": True,
        "authority_field_changes_change_key": [
            "payload_hash",
            "destination_binding_id",
            "credential_handle_id",
            "platform_id",
            "approval_event_id",
        ],
        "duplicate_success_suppresses_candidate": True,
        "unknown_result_auto_retry_allowed": False,
        "unknown_result_routes_to": "manual_reconciliation_manual_fallback",
        "secret_risk_scanner": "fail_closed_key_and_value_pattern_scan",
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
