"""Read-only visible-UI identity shadow gate for the BrowserOS dry-run seam.

This module consumes only caller-supplied visible labels and snapshot text. It never opens a page,
selects an account, reads cookies/storage/tokens, or performs browser actions. A confirmed result is
still shadow evidence only; it does not grant publication or runtime authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = "contentops.browseros.identity_shadow_gate.v1"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_MISSING = "MISSING"
STATUS_HUMAN_REQUIRED = "HUMAN_REQUIRED"
STATUS_DISABLED = "DISABLED_BY_DEFAULT"

_REDACTED = "<REDACTED>"
_SENSITIVE_KEY_PARTS = (
    "cookie",
    "storage",
    "token",
    "authorization",
    "password",
    "secret",
    "credential",
    "session",
)
_INLINE_SECRET_RE = re.compile(
    r"(?i)(\b(?:access[_ -]?token|refresh[_ -]?token|authorization|cookie|"
    r"password|secret|credential|session(?:[_ -]?id)?)\b\s*[:=]\s*)"
    r"([^\s,;]+)"
)
_ACCOUNT_LINE_RE = re.compile(
    r"(?im)^\s*(?:account|profile|workspace|user)\s*[:=]\s*(.+?)\s*$"
)
_DESTINATION_LINE_RE = re.compile(
    r"(?im)^\s*(?:destination|surface|channel|target)\s*[:=]\s*(.+?)\s*$"
)
_TRUNCATED_MARKERS = (
    "content truncated",
    "snapshot truncated",
    "text truncated",
    "…",
    "...",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    material = value if isinstance(value, str) else _canonical(value)
    return sha256(material.encode("utf-8")).hexdigest()


def _sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact(value: Any, *, key: str = "") -> Any:
    if _sensitive_key(key):
        return _REDACTED
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for item_key in value:
            normalized_key = str(item_key)
            if _sensitive_key(normalized_key):
                redacted[normalized_key] = _REDACTED
            else:
                redacted[normalized_key] = _redact(
                    value[item_key], key=normalized_key
                )
        return redacted
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _INLINE_SECRET_RE.sub(r"\1" + _REDACTED, value)
    return value


def _clean_label(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _redaction_present(value: Any, *, key: str = "") -> bool:
    if _sensitive_key(key):
        return True
    if isinstance(value, Mapping):
        for item_key in value:
            normalized_key = str(item_key)
            if _sensitive_key(normalized_key) or _redaction_present(
                value[item_key], key=normalized_key
            ):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_redaction_present(item) for item in value)
    return isinstance(value, str) and _INLINE_SECRET_RE.search(value) is not None


def _values_from_metadata(metadata: Mapping[str, Any] | None) -> tuple[list[str], list[str], bool]:
    if not isinstance(metadata, Mapping):
        return [], [], False
    account_values: list[str] = []
    destination_values: list[str] = []
    truncated = bool(metadata.get("truncated") or metadata.get("content_truncated"))
    for key, value in metadata.items():
        normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
        if normalized in {"account", "accountlabel", "profile", "profilelabel", "workspacelabel"}:
            label = _clean_label(value)
            if label:
                account_values.append(label)
        if normalized in {
            "destination",
            "destinationlabel",
            "surface",
            "surfacelabel",
            "channel",
            "target",
        }:
            label = _clean_label(value)
            if label:
                destination_values.append(label)
    return account_values, destination_values, truncated


def _values_from_snapshot(snapshot_text: str | None) -> tuple[list[str], list[str], bool]:
    text = str(snapshot_text or "").strip()
    if not text:
        return [], [], False
    redacted = _redact(text)
    account_values = [_clean_label(match) for match in _ACCOUNT_LINE_RE.findall(redacted)]
    destination_values = [_clean_label(match) for match in _DESTINATION_LINE_RE.findall(redacted)]
    truncated = any(marker in redacted.casefold() for marker in _TRUNCATED_MARKERS)
    return [value for value in account_values if value], [
        value for value in destination_values if value
    ], truncated


def _distinct(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        identity = value.casefold()
        if identity not in seen:
            seen.add(identity)
            result.append(value)
    return result


def evaluate_browseros_identity_shadow(
    *,
    enabled: bool = False,
    expected_account_label: str | None,
    expected_destination: str | None,
    visible_ui_metadata: Mapping[str, Any] | None = None,
    snapshot_text: str | None = None,
) -> dict[str, Any]:
    """Evaluate exact visible labels without performing any browser or account action."""

    base = {
        "schema_version": SCHEMA_VERSION,
        "gate_enabled": bool(enabled),
        "expected_account_label": _clean_label(expected_account_label),
        "expected_destination": _clean_label(expected_destination),
        "observed_account_label": None,
        "observed_destination": None,
        "visible_ui_sha256": None,
        "snapshot_sha256": None,
        "identity_evidence_sha256": None,
        "evidence_hash_algorithm": "sha256",
        "visible_ui_metadata_present": isinstance(visible_ui_metadata, Mapping),
        "snapshot_present": bool(_clean_label(snapshot_text)),
        "redaction_applied": False,
        "credential_or_session_material_read": False,
        "account_identity_proven": False,
        "public_write_performed": False,
        "publication_authority": False,
        "browser_action_performed": False,
    }
    if not enabled:
        return {
            **base,
            "status": STATUS_DISABLED,
            "failure_detail": "browseros_identity_shadow_is_disabled_by_default",
        }

    redacted_metadata = _redact(visible_ui_metadata) if isinstance(visible_ui_metadata, Mapping) else None
    redacted_snapshot = _redact(snapshot_text) if isinstance(snapshot_text, str) else ""
    base["redaction_applied"] = _redaction_present(
        visible_ui_metadata
    ) or _redaction_present(snapshot_text)
    if redacted_metadata is not None:
        base["visible_ui_sha256"] = _hash(redacted_metadata)
    if redacted_snapshot:
        base["snapshot_sha256"] = _hash(redacted_snapshot)

    account_values, destination_values, metadata_truncated = _values_from_metadata(redacted_metadata)
    snapshot_accounts, snapshot_destinations, snapshot_truncated = _values_from_snapshot(redacted_snapshot)
    accounts = _distinct(account_values + snapshot_accounts)
    destinations = _distinct(destination_values + snapshot_destinations)
    expected_account = _clean_label(expected_account_label)
    expected_destination_value = _clean_label(expected_destination)
    evidence_material = {
        "expected_account_label": expected_account,
        "expected_destination": expected_destination_value,
        "observed_account_labels": accounts,
        "observed_destinations": destinations,
        "visible_ui_sha256": base["visible_ui_sha256"],
        "snapshot_sha256": base["snapshot_sha256"],
    }
    base["identity_evidence_sha256"] = _hash(evidence_material)
    base["observed_account_label"] = accounts[0] if len(accounts) == 1 else None
    base["observed_destination"] = destinations[0] if len(destinations) == 1 else None

    if metadata_truncated or snapshot_truncated:
        return {**base, "status": STATUS_HUMAN_REQUIRED, "failure_detail": "visible_identity_evidence_truncated"}
    if not expected_account or not expected_destination_value or not accounts or not destinations:
        return {**base, "status": STATUS_MISSING, "failure_detail": "visible_identity_label_missing"}
    if len(accounts) != 1 or len(destinations) != 1:
        return {**base, "status": STATUS_AMBIGUOUS, "failure_detail": "multiple_visible_identity_labels"}
    if accounts[0].casefold() != expected_account.casefold() or destinations[0].casefold() != expected_destination_value.casefold():
        return {**base, "status": STATUS_AMBIGUOUS, "failure_detail": "visible_identity_mismatch"}
    return {
        **base,
        "status": STATUS_CONFIRMED,
        "failure_detail": None,
        "account_identity_proven": True,
    }
