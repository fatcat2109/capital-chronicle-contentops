"""Fail-closed shadow reconciliation for one injected canonical destination readback."""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = "contentops.destination_readback_shadow_gate.v1"
CONFIRMED_SHADOW = "CONFIRMED_SHADOW"
MISMATCH = "MISMATCH"
MISSING = "MISSING"
HUMAN_REQUIRED = "HUMAN_REQUIRED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"
_REDACTED = "<REDACTED>"
_SENSITIVE = ("cookie", "storage", "token", "authorization", "password", "secret", "credential", "session")
_SECRET_RE = re.compile(
    r"(?i)(\b(?:access[_ -]?token|refresh[_ -]?token|authorization|cookie|password|secret|credential|session(?:[_ -]?id)?)\b\s*[:=]\s*)([^\s,;]+)"
)


def _sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
    return any(part in normalized for part in _SENSITIVE)


def _redact(value: Any, *, key: str = "") -> Any:
    if _sensitive_key(key):
        return _REDACTED
    if isinstance(value, Mapping):
        return {
            str(item_key): _redact(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _SECRET_RE.sub(r"\1" + _REDACTED, value)
    return value


def _hash(value: Any) -> str:
    material = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _base(*, enabled: bool, expected: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": DISABLED_BY_DEFAULT if not enabled else None,
        "gate_enabled": bool(enabled),
        "shadow_only": True,
        "expected_destination_platform": expected.get("platform"),
        "expected_canonical_destination_kind": expected.get("destination_kind"),
        "expected_destination_binding_id": expected.get("destination_binding_id"),
        "expected_public_object_id": expected.get("public_object_id"),
        "expected_public_object_url": expected.get("public_object_url"),
        "expected_payload_sha256": expected.get("payload_sha256"),
        "observed_destination_platform": None,
        "observed_canonical_destination_kind": None,
        "observed_destination_binding_id": None,
        "observed_public_object_id": None,
        "observed_public_object_url": None,
        "observed_payload_sha256": None,
        "observed_readback_sha256": None,
        "readback_evidence_sha256": None,
        "reconciliation_identity_sha256": None,
        "redaction_applied": False,
        "account_identity_proven": False,
        "publication_success_proven": False,
        "runtime_readiness_proven": False,
        "public_write_performed": False,
        "publication_authority": False,
    }


def evaluate_destination_readback_shadow(
    *,
    enabled: bool = False,
    expected_platform: str | None,
    expected_destination_kind: str | None,
    expected_destination_binding_id: str | None = None,
    expected_public_object_id: str | None = None,
    expected_public_object_url: str | None = None,
    expected_payload_sha256: str | None = None,
    readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one hypothetical readback without performing or claiming a public write."""

    expected = {
        "platform": expected_platform,
        "destination_kind": expected_destination_kind,
        "destination_binding_id": expected_destination_binding_id,
        "public_object_id": expected_public_object_id,
        "public_object_url": expected_public_object_url,
        "payload_sha256": expected_payload_sha256,
    }
    result = _base(enabled=enabled, expected=expected)
    if not enabled:
        result["failure_detail"] = "destination_readback_shadow_is_disabled_by_default"
        return result

    if not isinstance(readback, Mapping):
        result.update({"status": MISSING, "failure_detail": "readback_missing"})
        return result
    redacted = _redact(readback)
    result["redaction_applied"] = redacted != readback
    result["readback_evidence_sha256"] = _hash(redacted)

    status = str(readback.get("status") or readback.get("dispatch_status") or "")
    if bool(readback.get("unknown_write")) or status == UNKNOWN_WRITE:
        result.update(
            {
                "status": UNKNOWN_WRITE,
                "failure_detail": "unknown_write_stop_retry_readback_reconcile",
                "retry_forbidden": True,
            }
        )
        return result
    if any(
        bool(readback.get(key))
        for key in ("truncated", "content_truncated", "access_denied", "identity_ambiguous")
    ):
        result.update({"status": HUMAN_REQUIRED, "failure_detail": "readback_evidence_incomplete_or_ambiguous"})
        return result

    observed = {
        "platform": readback.get("platform") or readback.get("destination_platform"),
        "destination_kind": readback.get("destination_kind") or readback.get("canonical_destination_kind"),
        "destination_binding_id": readback.get("destination_binding_id"),
        "public_object_id": readback.get("public_object_id") or readback.get("object_id"),
        "public_object_url": readback.get("public_object_url") or readback.get("canonical_url"),
        "payload_sha256": readback.get("payload_sha256") or readback.get("content_sha256") or readback.get("content_hash"),
    }
    result.update(
        {
            "observed_destination_platform": observed["platform"],
            "observed_canonical_destination_kind": observed["destination_kind"],
            "observed_destination_binding_id": observed["destination_binding_id"],
            "observed_public_object_id": observed["public_object_id"],
            "observed_public_object_url": observed["public_object_url"],
            "observed_payload_sha256": observed["payload_sha256"],
            "observed_readback_sha256": readback.get("readback_sha256"),
        }
    )
    required = [expected_platform, expected_destination_kind, expected_payload_sha256]
    if expected_destination_binding_id:
        required.append(expected_destination_binding_id)
    if expected_public_object_id:
        required.append(expected_public_object_id)
    if expected_public_object_url:
        required.append(expected_public_object_url)
    if any(not str(value or "") for value in required) or not str(readback.get("readback_sha256") or ""):
        result.update({"status": MISSING, "failure_detail": "required_destination_readback_identity_missing"})
        return result

    mismatches = []
    for key, expected_value in expected.items():
        if expected_value is not None and str(observed[key] or "") != str(expected_value):
            mismatches.append(key)
    if mismatches:
        result.update({"status": MISMATCH, "failure_detail": "destination_readback_mismatch:" + ",".join(mismatches)})
        return result
    if str(readback.get("reconciliation_status") or "") != "RECONCILED_CONFIRMED":
        result.update({"status": MISMATCH, "failure_detail": "readback_not_reconciled_confirmed"})
        return result

    reconciliation_identity = {
        "platform": observed["platform"],
        "destination_kind": observed["destination_kind"],
        "destination_binding_id": observed["destination_binding_id"],
        "public_object_id": observed["public_object_id"],
        "public_object_url": observed["public_object_url"],
        "payload_sha256": observed["payload_sha256"],
        "readback_sha256": readback.get("readback_sha256"),
        "reconciliation_status": readback.get("reconciliation_status"),
    }
    result.update(
        {
            "status": CONFIRMED_SHADOW,
            "failure_detail": None,
            "reconciliation_identity_sha256": _hash(reconciliation_identity),
        }
    )
    return result
