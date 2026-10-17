"""One injected, read-only scheduled production-day shadow cycle.

This is a deterministic composition seam, not a scheduler or a publication owner. It consumes
the existing source, BrowserOS, X-ingestion, editorial, package, destination-readback, and
coordinator recovery contracts and returns one immutable receipt without writing the store or
calling a model/provider/browser/transport.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Sequence

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


SCHEMA_VERSION = "contentops.scheduled_shadow_production_day.v1"
SHADOW_CONFIRMED = "SHADOW_CONFIRMED"
DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"
MISSING = "MISSING"
MISMATCH = "MISMATCH"
HUMAN_REQUIRED = "HUMAN_REQUIRED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
FAIL_CLOSED = "FAIL_CLOSED"


def _hash(value: Any) -> str:
    material = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _status(component: Mapping[str, Any] | None) -> str:
    return str((component or {}).get("status") or "")


def _has_side_effect(component: Mapping[str, Any] | None) -> bool:
    row = component or {}
    return any(
        row.get(key) is True
        for key in (
            "public_write_performed",
            "publication_authority",
            "durable_store_written",
            "scheduler_started",
            "model_call_performed",
            "provider_call_performed",
            "browser_action_performed",
        )
    )


def _base(enabled: bool, inputs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": DISABLED_BY_DEFAULT if not enabled else None,
        "enabled": bool(enabled),
        "shadow_only": True,
        "immutable_receipt": True,
        "input_evidence_sha256": _hash(inputs),
        "receipt_sha256": None,
        "production_day_receipt_sha256": None,
        "source_order": [
            "HTTP_OR_OFFICIAL_API_FIRST",
            "ONE_BROWSEROS_RENDERED_RECOVERY_IF_ELIGIBLE",
        ],
        "shared_request_budget": True,
        "max_browser_rendered_recovery_attempts": 1,
        "x_ingestion_cdp_port": 9222,
        "x_ingestion_only": True,
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "database_mutation": False,
        "model_call_count": 0,
        "provider_call_count": 0,
        "browser_action_count": 0,
        "public_write_performed": False,
        "publication_success_proven": False,
        "runtime_readiness_proven": False,
        "account_identity_proven": False,
        "publication_authority": False,
    }


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in result.items() if key != "receipt_sha256"}
    result["receipt_sha256"] = _hash(body)
    return result


def _fail(result: dict[str, Any], status: str, detail: str) -> dict[str, Any]:
    result.update({"status": status, "failure_detail": detail})
    return _finish(result)


def run_scheduled_shadow_production_day(
    *,
    enabled: bool = False,
    source_recovery: Mapping[str, Any] | None = None,
    browser_preflight: Mapping[str, Any] | None = None,
    preflight_runner: Callable[..., Mapping[str, Any]] | None = None,
    x_ingestion: Mapping[str, Any] | None = None,
    grounded_evidence: Mapping[str, Any] | None = None,
    candidate_decision: Mapping[str, Any] | None = None,
    canonical_article: Mapping[str, Any] | None = None,
    derivative_packages: Sequence[Mapping[str, Any]] | None = None,
    destination_readback: Mapping[str, Any] | None = None,
    recovery_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one end-to-end shadow receipt from injected owner outputs."""

    if enabled and browser_preflight is None and preflight_runner is not None:
        try:
            browser_preflight = dict(
                preflight_runner(auto_open=True, reconnect_once=True)
            )
        except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
            browser_preflight = {
                "status": "BROWSER_UNAVAILABLE",
                "failure_detail": str(exc) or type(exc).__name__,
            }
    inputs = {
        "source_recovery": source_recovery,
        "browser_preflight": browser_preflight,
        "x_ingestion": x_ingestion,
        "grounded_evidence": grounded_evidence,
        "candidate_decision": candidate_decision,
        "canonical_article": canonical_article,
        "derivative_packages": list(derivative_packages or []),
        "destination_readback": destination_readback,
        "recovery_state": recovery_state,
    }
    result = _base(enabled, inputs)
    if not enabled:
        return _fail(result, DISABLED_BY_DEFAULT, "scheduled_shadow_production_day_disabled_by_default")

    components = {
        "source_recovery": source_recovery,
        "browser_preflight": browser_preflight,
        "x_ingestion": x_ingestion,
        "grounded_evidence": grounded_evidence,
        "candidate_decision": candidate_decision,
        "canonical_article": canonical_article,
        "destination_readback": destination_readback,
    }
    unknown = [
        name
        for name, row in components.items()
        if isinstance(row, Mapping)
        and (
            _status(row) == UNKNOWN_WRITE
            or bool(row.get("unknown_write"))
        )
    ]
    unknown.extend(
        f"derivative:{index}"
        for index, row in enumerate(derivative_packages or [])
        if isinstance(row, Mapping)
        and (_status(row) == UNKNOWN_WRITE or bool(row.get("unknown_write")))
    )
    if unknown:
        return _fail(result, UNKNOWN_WRITE, "unknown_write_stop_retry_readback_reconcile:" + ",".join(unknown))
    side_effects = [name for name, row in components.items() if _has_side_effect(row)]
    side_effects.extend(
        f"derivative:{index}"
        for index, row in enumerate(derivative_packages or [])
        if _has_side_effect(row)
    )
    if side_effects:
        return _fail(result, FAIL_CLOSED, "shadow_side_effect_flag_present:" + ",".join(side_effects))

    missing = [name for name, row in components.items() if not isinstance(row, Mapping)]
    if not derivative_packages:
        missing.append("derivative_packages")
    if missing:
        return _fail(result, MISSING, "missing_components:" + ",".join(missing))

    if _status(source_recovery) not in {
        "HTTP_SUCCESS_NO_BROWSER",
        "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
    }:
        return _fail(result, FAIL_CLOSED, "source_recovery_not_admitted")
    recovery_attempts = int(
        (source_recovery or {}).get("browser_rendered_recovery_attempt_count")
        or (source_recovery or {}).get("attempt_count")
        or 0
    )
    if (
        (source_recovery or {}).get("http_first") is False
        or (source_recovery or {}).get("shared_request_budget") is False
        or recovery_attempts > 1
    ):
        return _fail(result, MISMATCH, "source_recovery_order_budget_or_attempt_contract_invalid")
    if _status(browser_preflight) != "PASS":
        return _fail(result, HUMAN_REQUIRED if _status(browser_preflight) in {"AMBIGUOUS", HUMAN_REQUIRED} else FAIL_CLOSED, "browser_preflight_not_pass")
    if _status(x_ingestion) not in {"INGESTION_ONLY_READY", "NOT_REQUESTED"} or (x_ingestion or {}).get("cdp_port") not in {None, 9222}:
        return _fail(result, MISMATCH, "x_ingestion_boundary_invalid")

    if _status(grounded_evidence) != "GROUNDED_EVIDENCE_READY":
        return _fail(result, HUMAN_REQUIRED if _status(grounded_evidence) in {"STALE", "TRUNCATED", HUMAN_REQUIRED} else FAIL_CLOSED, "grounded_evidence_not_ready")
    if not (grounded_evidence or {}).get("evidence_ids") or not (grounded_evidence or {}).get("claim_bindings_sha256"):
        return _fail(result, MISSING, "grounded_evidence_ids_or_claim_bindings_missing")
    if _status(candidate_decision) != "SELECTED" or not (candidate_decision or {}).get("candidate_id"):
        return _fail(result, MISMATCH, "candidate_decision_not_selected")
    if _status(canonical_article) != "QUALIFIED":
        return _fail(result, MISMATCH, "canonical_article_not_qualified")
    article_hash = str((canonical_article or {}).get("payload_sha256") or "")
    if len(article_hash) != 64 or not (canonical_article or {}).get("article_id"):
        return _fail(result, MISSING, "canonical_article_identity_or_payload_hash_missing")
    if str((canonical_article or {}).get("epistemic_state") or "") not in {
        "CONFIRMED", "UNCONFIRMED", "PARTIALLY_CONFIRMED", "DISPUTED_OR_DENIED", "SUPERSEDED"
    }:
        return _fail(result, MISMATCH, "canonical_article_epistemic_state_invalid")

    packages = list(derivative_packages or [])
    destinations = [str(row.get("destination") or "") for row in packages]
    if len(packages) != 8 or set(destinations) != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
        return _fail(result, MISMATCH, "derivative_package_destination_set_invalid")
    if any(str(row.get("status") or "") != "SHADOW_READY" or len(str(row.get("payload_sha256") or "")) != 64 for row in packages):
        return _fail(result, MISSING, "derivative_package_payload_or_status_missing")
    if _status(destination_readback) != "CONFIRMED_SHADOW":
        return _fail(result, MISMATCH if _status(destination_readback) else MISSING, "destination_readback_shadow_not_confirmed")

    recovery = recovery_state or {}
    if bool(recovery.get("interrupted")):
        if recovery.get("resume_status") != "RESUMABLE" or recovery.get("semantic_rerun_forbidden") is not True:
            return _fail(result, HUMAN_REQUIRED, "interruption_resume_contract_invalid")
        result["interruption_recovery"] = "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    else:
        result["interruption_recovery"] = "NOT_INTERRUPTED"
    result.update(
        {
            "status": SHADOW_CONFIRMED,
            "failure_detail": None,
            "production_day_id": str(recovery.get("production_day_id") or "shadow-day-unknown"),
            "selected_candidate_id": candidate_decision.get("candidate_id"),
            "canonical_article_id": canonical_article.get("article_id"),
            "canonical_payload_sha256": article_hash,
            "derivative_destination_count": len(packages),
            "derivative_destinations": sorted(destinations),
            "grounded_evidence_ids": list(grounded_evidence.get("evidence_ids") or []),
            "candidate_decision_sha256": _hash(candidate_decision),
            "editorial_evidence_sha256": _hash(grounded_evidence),
            "canonical_article_sha256": _hash(canonical_article),
            "derivative_packages_sha256": _hash(packages),
            "destination_readback_sha256": _hash(destination_readback),
            "recovery_state_sha256": _hash(recovery),
        }
    )
    result["production_day_receipt_sha256"] = _hash(result)
    return _finish(result)
