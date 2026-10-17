"""Read-only end-to-end shadow packet for the accepted ContentOps hybrid path.

The packet composes injected results from existing owners: bounded HTTP/rendered-source recovery,
BrowserOS lifecycle preflight, visible identity shadow, canonical destination readback shadow, and
the existing Chrome CDP 9222 ingestion-only boundary. It creates no scheduler, store, transport,
browser session, provider call, or public write.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


SCHEMA_VERSION = "contentops.hybrid_pipeline_shadow.v1"
CONFIRMED_SHADOW = "CONFIRMED_SHADOW"
MISMATCH = "MISMATCH"
MISSING = "MISSING"
HUMAN_REQUIRED = "HUMAN_REQUIRED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
FAIL_CLOSED = "FAIL_CLOSED"
DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"


def _hash(value: Any) -> str:
    material = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(material.encode("utf-8")).hexdigest()


def _component_status(component: Mapping[str, Any] | None) -> str:
    return str((component or {}).get("status") or "")


def _classify_failure(components: Mapping[str, Mapping[str, Any] | None]) -> tuple[str, str | None]:
    for name, component in components.items():
        status = _component_status(component)
        if status == UNKNOWN_WRITE:
            return UNKNOWN_WRITE, f"{name}:unknown_write_stop_retry_readback_reconcile"
        if status in {HUMAN_REQUIRED, "AMBIGUOUS"}:
            return HUMAN_REQUIRED, f"{name}:human_review_required"
        if status in {MISMATCH, "PROFILE_IDENTITY_AMBIGUOUS", "RECOVERY_CONTRACT_INVALID"}:
            return MISMATCH, f"{name}:{status}"
        if status in {MISSING, "BROWSER_UNAVAILABLE", "FAIL_CLOSED"}:
            return FAIL_CLOSED, f"{name}:{status}"
    return FAIL_CLOSED, "component_status_not_admitted"


def evaluate_hybrid_pipeline_shadow(
    *,
    enabled: bool = False,
    source_recovery: Mapping[str, Any] | None = None,
    browser_preflight: Mapping[str, Any] | None = None,
    identity_shadow: Mapping[str, Any] | None = None,
    destination_shadow: Mapping[str, Any] | None = None,
    x_ingestion_boundary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one injected end-to-end packet and return fail-closed shadow evidence."""

    components = {
        "source_recovery": source_recovery,
        "browser_preflight": browser_preflight,
        "identity_shadow": identity_shadow,
        "destination_shadow": destination_shadow,
        "x_ingestion_boundary": x_ingestion_boundary,
    }
    redacted_components = {
        key: dict(value) if isinstance(value, Mapping) else None
        for key, value in components.items()
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": DISABLED_BY_DEFAULT if not enabled else None,
        "gate_enabled": bool(enabled),
        "shadow_only": True,
        "source_order": ["HTTP_OR_OFFICIAL_API", "BROWSEROS_RENDERED_RECOVERY_IF_ELIGIBLE"],
        "shared_request_budget": True,
        "max_browser_rendered_recovery_attempts": 1,
        "x_ingestion_cdp_port": 9222,
        "x_ingestion_only": True,
        "components": redacted_components,
        "evidence_sha256": _hash(redacted_components),
        "pipeline_identity_sha256": None,
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "model_call_count": 0,
        "provider_call_count": 0,
        "public_write_performed": False,
        "publication_success_proven": False,
        "runtime_readiness_proven": False,
        "account_identity_proven": False,
        "publication_authority": False,
    }
    if not enabled:
        result["failure_detail"] = "hybrid_pipeline_shadow_is_disabled_by_default"
        return result

    required = {
        "source_recovery": {
            "HTTP_SUCCESS_NO_BROWSER",
            "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
        },
        "browser_preflight": {"PASS"},
        "identity_shadow": {"CONFIRMED"},
        "destination_shadow": {"CONFIRMED_SHADOW"},
        "x_ingestion_boundary": {"INGESTION_ONLY_READY", "NOT_REQUESTED"},
    }
    missing = [name for name, allowed in required.items() if not components[name]]
    if missing:
        result.update({"status": MISSING, "failure_detail": "missing_components:" + ",".join(missing)})
        return result
    for name, allowed in required.items():
        if _component_status(components[name]) not in allowed:
            status, detail = _classify_failure(components)
            result.update({"status": status, "failure_detail": detail})
            return result
    recovery = source_recovery or {}
    if recovery.get("http_first") is False or recovery.get("shared_request_budget") is False:
        result.update({"status": MISMATCH, "failure_detail": "source_recovery_order_or_budget_contract_invalid"})
        return result
    if int(recovery.get("browser_rendered_recovery_attempt_count") or recovery.get("attempt_count") or 0) > 1:
        result.update({"status": MISMATCH, "failure_detail": "browser_rendered_recovery_attempt_budget_exceeded"})
        return result
    if any(
        (component or {}).get("public_write_performed") is True
        or (component or {}).get("publication_authority") is True
        for component in components.values()
    ):
        result.update({"status": FAIL_CLOSED, "failure_detail": "side_effect_or_authority_flag_present"})
        return result
    result["pipeline_identity_sha256"] = _hash(
        {
            "source_recovery": recovery,
            "identity_shadow": identity_shadow,
            "destination_shadow": destination_shadow,
            "x_ingestion_boundary": x_ingestion_boundary,
        }
    )
    result.update({"status": CONFIRMED_SHADOW, "failure_detail": None})
    return result
