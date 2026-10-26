"""ContentOps adapter for the shared four-trigger evidence-resolution contracts.

This module is deliberately a consumer adapter.  It binds ContentOps requests to the
Main-owned ``CapitalChronicle*V1`` contract names, but does not implement Core numeric
authority, a database, a scheduler, a publisher, or a private portfolio reader.

The resolver is deterministic and dependency-injected.  Existing sidecar, published-memory,
admitted-record, read-model and BrowserOS readers can be supplied as callables or fixture
records.  BrowserOS is accepted only as a bounded read-only recovery result after the ordered
database-first attempts have been recorded.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


SCHEMA_VERSION = "contentops.four_trigger_data_resolution_adapter.v1"
DESIGN_PR81_HEAD = "dd03470ae06a2fce4f1c1358005f3854de904738"
DESIGN_PR81_PATH = "docs/automation/CONTENTOPS_FOUR_TRIGGER_DATA_RESOLUTION_AND_EDITORIAL_OPERATING_MODEL_V1.md"
DESIGN_PR81_BYTES = 7871
DESIGN_PR81_SHA256 = "2b33888f2f87111bee6f560bdfd9a6fb99caf6ddcb1477115327ec076a2686db"
MAIN_MODEL_PATH = "docs/strategy/ACTIVE_CONTEXT/CAPITAL_CHRONICLE_FOUR_TRIGGER_ANALYSIS_AND_DATA_OPERATING_MODEL_V1.md"
MAIN_MODEL_BYTES = 15569
MAIN_MODEL_SHA256 = "b1fc4c192b1865890a3f0ad2833b4f9b7cfb654eb7dee2306fdb48abbe2ee35a"

TRIGGER_REQUEST_SCHEMA = "CapitalChronicleTriggerRequestV1"
DATA_NEED_PLAN_SCHEMA = "CapitalChronicleDataNeedPlanV1"
DATA_RESOLUTION_RECEIPT_SCHEMA = "CapitalChronicleDataResolutionReceiptV1"
ANALYSIS_RUN_RECEIPT_SCHEMA = "CapitalChronicleAnalysisRunReceiptV1"
SERVING_COVERAGE_PROJECTION_SCHEMA = "CapitalChronicleServingCoverageProjectionV1"

CONSUMER_ROUTE = "CONTENTOPS_EDITORIAL"
EDITORIAL_OWNER = "NATIVE_CODEX_DESKTOP"
EDITORIAL_OPERATION = "run_v1_simple_gemini_newsroom"
PUBLICATION_OWNER = "DurablePublicationCoordinator"
CDP_INGESTION_PORT = 9222
CDP_PUBLICATION_READBACK_PORT = 9223

TRIGGER_KINDS = (
    "FOUNDATION_COVERAGE_SERVING",
    "SCHEDULED_LATEST_INTELLIGENCE",
    "SCHEDULED_PORTFOLIO_CONTEXT",
    "JIM_MANUAL_CODEX_DESKTOP",
)
REQUEST_STATUSES = ("ACCEPTED", "DEFERRED", "UNAVAILABLE", "REJECTED")
RESOLUTION_STATES = ("RESOLVED", "PARTIAL", "STALE", "UNAVAILABLE", "DATA_BLOCKED")
OUTPUT_INTENTS = ("RESEARCH_ONLY", "DRAFT_ONLY", "PUBLISHABLE", "DATA_BLOCKED")
ROUTES = (
    "RETAINED_HEADLINE_SIDECAR",
    "PUBLISHED_MEMORY",
    "ADMITTED_OFFICIAL_FILING_PROVIDER",
    "EXISTING_MARKET_READ_MODEL",
    "BROWSEROS_READ_ONLY",
    "UNAVAILABLE",
)
EPISTEMIC_LAYERS = (
    "OBSERVED_FACT",
    "ATTRIBUTED_REPORT_OR_INTERPRETATION",
    "CAPITAL_CHRONICLE_ANALYSIS",
    "SCENARIO_OR_UNCERTAINTY",
)
DESTINATIONS = (
    "telegram",
    "discord",
    "x",
    "linkedin",
    "facebook_page",
    "instagram_business",
    "threads",
    "youtube",
)
EXISTING_OWNER_BINDINGS = {
    "sidecars": "live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars",
    "published_memory": "live_contentops.published_corpus_read_model_v1.load_canonical_published_memory_read_only",
    "sourceability_dedupe": "live_contentops.v1_simple_gemini_newsroom_v1",
    "selector_writer_validator": "live_contentops.v1_simple_gemini_newsroom_v1",
    "eight_derivative_compiler": "live_contentops._eight_platform_substack_first_pipeline_impl_v1.build_native_derivative_payloads",
    "canonical_publication_readback": "live_contentops.publication_coordinator_v1.DurablePublicationCoordinator",
}

_SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|cookie|session[_-]?id|private[_-]?key|password)"
)
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class FourTriggerAdapterError(ValueError):
    """Fail-closed adapter input or evidence error."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _without(value: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key not in set(keys)}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | str | None) -> str:
    if isinstance(value, datetime):
        current = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value or "").strip()
    if not text:
        return _iso(_now_utc())
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def _require_text(value: Any, field: str, *, max_len: int = 512) -> str:
    text = " ".join(str(value or "").split())
    if not text or len(text) > max_len:
        raise FourTriggerAdapterError(f"{field}_required_or_too_long")
    return text


def _ensure_utc(value: Any, field: str) -> str:
    text = _iso(value)
    if not _UTC_RE.fullmatch(text):
        raise FourTriggerAdapterError(f"{field}_must_be_utc")
    return text


def _secret_found(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if _SECRET_RE.search(str(key)):
                return key_path
            found = _secret_found(item, path=key_path)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _secret_found(item, path=f"{path}[{index}]")
            if found:
                return found
    return None


def _validate_hash(record: Mapping[str, Any], field: str) -> None:
    supplied = str(record.get(field) or "")
    if not supplied or supplied != _sha(_without(record, field)):
        raise FourTriggerAdapterError(f"{field}_mismatch")


def _normalise_assets(values: Iterable[Any]) -> list[str]:
    assets = sorted(
        {" ".join(str(value).split()) for value in values if str(value).strip()}
    )
    if len(assets) > 64:
        raise FourTriggerAdapterError("target_assets_too_many")
    return assets


def _route_for_trigger(trigger_kind: str) -> dict[str, Any]:
    routes = {
        "FOUNDATION_COVERAGE_SERVING": {
            "channel": "FOUNDATION_COVERAGE_AND_SERVING",
            "owner": "SHARED_MAIN_COVERAGE_PROJECTION",
            "routine_window": False,
            "creates_scheduler": False,
        },
        "SCHEDULED_LATEST_INTELLIGENCE": {
            "channel": "SCHEDULED_LATEST_INTELLIGENCE",
            "owner": EDITORIAL_OWNER,
            "operation": EDITORIAL_OPERATION,
            "routine_window": True,
            "routine_windows_reused": ["17:00", "21:00", "23:00", "01:00"],
            "creates_scheduler": False,
        },
        "SCHEDULED_PORTFOLIO_CONTEXT": {
            "channel": "SCHEDULED_PORTFOLIO_CONTEXT",
            "owner": "MAIN_APP_PORTFOLIO_CONTROL_PLANE",
            "editorial_consumer": CONSUMER_ROUTE,
            "routine_window": True,
            "creates_scheduler": False,
            "private_portfolio_access": False,
        },
        "JIM_MANUAL_CODEX_DESKTOP": {
            "channel": "OWNER_MANUAL_CODEX_DESKTOP",
            "owner": "JIM_MANUAL_REQUEST",
            "routine_window": False,
            "automatic_publication": False,
            "creates_scheduler": False,
        },
    }
    return deepcopy(routes[trigger_kind])


def build_trigger_request(
    *,
    request_id: str,
    idempotency_key: str,
    trigger_kind: str,
    requester: str,
    target_assets: Sequence[str] = (),
    exact_exness_symbols: Sequence[str] = (),
    portfolio_scope: str | None = None,
    position_scope: str | None = None,
    analysis_horizon: str = "CURRENT",
    decision_purpose: str,
    requested_at_utc: datetime | str,
    deadline_utc: datetime | str | None = None,
    max_fallback_cost: int = 1,
    editorial_mode: str = "STANDARD_NEWS_ANALYSIS",
    audience: str = "PUBLIC_READER",
    language: str = "en",
    requested_format: str = "EDITORIAL_PACKET",
    claim_sensitivity: str = "ORDINARY",
    harm_class: str = "ORDINARY",
    sourceability_threshold: str = "GOVERNED_SOURCE_REQUIRED",
    publication_intent: str = "RESEARCH_ONLY",
    required_epistemic_state: str = "OBSERVED_FACT",
    parent_request_id: str | None = None,
    no_write: bool = True,
) -> dict[str, Any]:
    """Create one deduplicable request while retaining the existing owner boundaries."""
    kind = _require_text(trigger_kind, "trigger_kind", max_len=80).upper()
    if kind not in TRIGGER_KINDS:
        raise FourTriggerAdapterError("trigger_kind_invalid")
    if no_write is not True:
        raise FourTriggerAdapterError("contentops_adapter_requires_no_write")
    if max_fallback_cost < 0 or max_fallback_cost > 1:
        raise FourTriggerAdapterError("max_fallback_cost_invalid")
    if publication_intent not in OUTPUT_INTENTS:
        raise FourTriggerAdapterError("publication_intent_invalid")
    if required_epistemic_state not in EPISTEMIC_LAYERS:
        raise FourTriggerAdapterError("required_epistemic_state_invalid")
    requester_text = _require_text(requester, "requester")
    if kind == "JIM_MANUAL_CODEX_DESKTOP" and requester_text.casefold() != "jim":
        raise FourTriggerAdapterError("manual_request_requires_jim")
    if kind == "SCHEDULED_PORTFOLIO_CONTEXT" and not portfolio_scope:
        raise FourTriggerAdapterError("portfolio_scope_required")
    request = {
        "schema_version": TRIGGER_REQUEST_SCHEMA,
        "request_id": _require_text(request_id, "request_id", max_len=128),
        "idempotency_key": _require_text(
            idempotency_key, "idempotency_key", max_len=256
        ),
        "trigger_kind": kind,
        "requested_at_utc": _ensure_utc(requested_at_utc, "requested_at_utc"),
        "requester": requester_text,
        "target_assets": _normalise_assets(target_assets),
        "exact_exness_symbols": _normalise_assets(exact_exness_symbols),
        "portfolio_scope": str(portfolio_scope or "") or None,
        "position_scope": str(position_scope or "") or None,
        "analysis_horizon": _require_text(
            analysis_horizon, "analysis_horizon", max_len=80
        ),
        "decision_purpose": _require_text(
            decision_purpose, "decision_purpose", max_len=512
        ),
        "consumer_route": CONSUMER_ROUTE,
        "deadline_utc": _ensure_utc(deadline_utc, "deadline_utc")
        if deadline_utc
        else None,
        "max_fallback_cost": int(max_fallback_cost),
        "parent_request_id": str(parent_request_id or "") or None,
        "no_write": True,
        "owner_authority": "CONTENTOPS_EDITORIAL_CONSUMER_ONLY",
        "editorial": {
            "editorial_mode": _require_text(
                editorial_mode, "editorial_mode", max_len=80
            ),
            "audience": _require_text(audience, "audience", max_len=120),
            "language": _require_text(language, "language", max_len=32),
            "requested_format": _require_text(
                requested_format, "requested_format", max_len=80
            ),
            "claim_sensitivity": _require_text(
                claim_sensitivity, "claim_sensitivity", max_len=80
            ),
            "harm_class": _require_text(harm_class, "harm_class", max_len=80),
            "sourceability_threshold": _require_text(
                sourceability_threshold, "sourceability_threshold", max_len=120
            ),
            "publication_intent": publication_intent,
            "required_epistemic_state": required_epistemic_state,
        },
        "route": _route_for_trigger(kind),
        "request_status": "ACCEPTED",
    }
    return {**request, "request_hash": _sha(request)}


def deduplicate_trigger_request(
    request: Mapping[str, Any],
    terminal_by_idempotency_key: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a terminal request receipt without creating a second request."""
    _validate_hash(request, "request_hash")
    key = str(request.get("idempotency_key") or "")
    existing = terminal_by_idempotency_key.get(key)
    if existing is None:
        return {
            "schema_version": "contentops.trigger_request_dedupe_receipt.v1",
            "request_id": request.get("request_id"),
            "idempotency_key": key,
            "disposition": "NEW",
            "terminal_request_reused": False,
            "request_hash": request.get("request_hash"),
        }
    if str(existing.get("request_hash") or "") != str(
        request.get("request_hash") or ""
    ):
        raise FourTriggerAdapterError("idempotency_key_payload_conflict")
    return {
        "schema_version": "contentops.trigger_request_dedupe_receipt.v1",
        "request_id": request.get("request_id"),
        "idempotency_key": key,
        "disposition": "TERMINAL_REUSED",
        "terminal_request_reused": True,
        "terminal_status": existing.get("request_status") or existing.get("status"),
        "request_hash": request.get("request_hash"),
    }


def build_data_need_plan(
    request: Mapping[str, Any],
    needs: Sequence[Mapping[str, Any]],
    *,
    as_of_utc: datetime | str,
    resolver_version: str = "contentops.four_trigger_resolver.v1",
    stopping_rule: str = "RESOLVE_REQUIRED_FIELDS_OR_DATA_BLOCK",
) -> dict[str, Any]:
    """Bind explicit fields, units, clocks, rights and permitted fallback to one plan."""
    _validate_hash(request, "request_hash")
    if str(request.get("consumer_route") or "") != CONSUMER_ROUTE:
        raise FourTriggerAdapterError("consumer_route_invalid")
    if not needs:
        raise FourTriggerAdapterError("data_need_plan_requires_needs")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(needs, start=1):
        if not isinstance(raw, Mapping):
            raise FourTriggerAdapterError("data_need_not_object")
        need_id = _require_text(
            raw.get("need_id") or f"need-{index}", "need_id", max_len=128
        )
        if need_id in seen:
            raise FourTriggerAdapterError("data_need_id_duplicate")
        seen.add(need_id)
        required_fields = [
            _require_text(value, "required_field", max_len=160)
            for value in (raw.get("required_fields") or [raw.get("field")])
            if str(value or "").strip()
        ]
        if not required_fields:
            raise FourTriggerAdapterError("required_fields_missing")
        exact_or_proxy = str(raw.get("exact_or_proxy") or "EXACT").upper()
        if exact_or_proxy not in {"EXACT", "PROXY_ALLOWED", "PROXY_ONLY"}:
            raise FourTriggerAdapterError("exact_or_proxy_invalid")
        route_candidates = [
            str(value).upper() for value in (raw.get("permitted_routes") or ROUTES)
        ]
        if any(value not in ROUTES for value in route_candidates):
            raise FourTriggerAdapterError("permitted_route_invalid")
        normalized.append(
            {
                "need_id": need_id,
                "data_class": _require_text(
                    raw.get("data_class"), "data_class", max_len=120
                ),
                "required_fields": sorted(set(required_fields)),
                "unit": _require_text(
                    raw.get("unit") or "UNSPECIFIED", "unit", max_len=80
                ),
                "currency": _require_text(
                    raw.get("currency") or "UNSPECIFIED", "currency", max_len=40
                ),
                "clock": _require_text(raw.get("clock") or "UTC", "clock", max_len=80),
                "target_instrument": str(raw.get("target_instrument") or "") or None,
                "exact_or_proxy": exact_or_proxy,
                "as_of_utc": _ensure_utc(
                    raw.get("as_of_utc") or as_of_utc, "need_as_of_utc"
                ),
                "freshness_budget_seconds": int(
                    raw.get("freshness_budget_seconds") or 0
                ),
                "revision_policy": _require_text(
                    raw.get("revision_policy") or "PRESERVE_VINTAGE",
                    "revision_policy",
                    max_len=120,
                ),
                "pit_required": bool(raw.get("pit_required", True)),
                "rights_class": _require_text(
                    raw.get("rights_class") or "PUBLIC_READ_ONLY",
                    "rights_class",
                    max_len=120,
                ),
                "query_references": sorted(
                    {
                        _require_text(value, "query_reference", max_len=240)
                        for value in (raw.get("query_references") or [])
                    }
                ),
                "permitted_routes": sorted(set(route_candidates)),
                "browseros_allowed": bool(raw.get("browseros_allowed", False)),
                "browseros_url": str(raw.get("browseros_url") or "") or None,
                "expected_consumer": CONSUMER_ROUTE,
                "basis_risk": str(raw.get("basis_risk") or "") or None,
                "unsupported_dimensions": sorted(
                    {
                        _require_text(value, "unsupported_dimension", max_len=160)
                        for value in (raw.get("unsupported_dimensions") or [])
                    }
                ),
                "missingness_behavior": _require_text(
                    raw.get("missingness_behavior") or "DATA_BLOCKED",
                    "missingness_behavior",
                    max_len=80,
                ),
            }
        )
    core = {
        "schema_version": DATA_NEED_PLAN_SCHEMA,
        "request_id": request.get("request_id"),
        "request_hash": request.get("request_hash"),
        "consumer_route": CONSUMER_ROUTE,
        "as_of_utc": _ensure_utc(as_of_utc, "as_of_utc"),
        "needs": sorted(normalized, key=lambda row: row["need_id"]),
        "resolver_version": _require_text(
            resolver_version, "resolver_version", max_len=120
        ),
        "stopping_rule": _require_text(stopping_rule, "stopping_rule", max_len=240),
        "no_write": True,
        "database_first_order": [
            "RETAINED_HEADLINE_SIDECAR",
            "PUBLISHED_MEMORY",
            "ADMITTED_OFFICIAL_FILING_PROVIDER",
            "EXISTING_MARKET_READ_MODEL",
            "BROWSEROS_READ_ONLY",
            "UNAVAILABLE",
        ],
    }
    return {**core, "plan_hash": _sha(core)}


def existing_owner_bindings() -> dict[str, Any]:
    """Return the exact existing ContentOps owners this adapter consumes."""
    return {
        "routine_editorial_owner": EDITORIAL_OWNER,
        "editorial_operation": EDITORIAL_OPERATION,
        "publication_owner": PUBLICATION_OWNER,
        "bindings": deepcopy(EXISTING_OWNER_BINDINGS),
        "routine_windows_reused": ["17:00", "21:00", "23:00", "01:00"],
        "creates_scheduler": False,
        "creates_store": False,
        "creates_publisher": False,
    }


def build_existing_contentops_source_layers(
    *,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Mapping[str, Any]] = (),
    admitted_records: Sequence[Mapping[str, Any]] = (),
    read_models: Sequence[Mapping[str, Any]] = (),
) -> dict[str, list[dict[str, Any]]]:
    """Normalize existing sidecars and published memory for database-first resolution.

    The caller owns the existing readers and may supply their exact read-only output.  The
    adapter only projects it into need-shaped rows; it does not open the production store or
    create another intake path.
    """
    sidecars: list[dict[str, Any]] = []
    for row in (rolling_input or {}).get("headlines") or []:
        if not isinstance(row, Mapping):
            continue
        external = (
            row.get("external_content")
            if isinstance(row.get("external_content"), Mapping)
            else {}
        )
        headline_text = external.get("headline_text") or row.get("headline_text")
        if not headline_text:
            continue
        sidecars.append(
            {
                "need_id": str(row.get("need_id") or ""),
                "source_identity": str(
                    external.get("url_or_source_ref")
                    or external.get("source_platform")
                    or row.get("headline_id")
                    or "retained_headline_sidecar"
                ),
                "source_class": "RETAINED_HEADLINE_SIDECAR",
                "query_reference": "headline.sidecar.latest",
                "source_hash": str(
                    row.get("canonical_input_hash") or row.get("headline_id") or ""
                ),
                "observed_at_utc": row.get("source_timestamp_utc"),
                "retrieved_at_utc": row.get("source_timestamp_utc"),
                "known_at_utc": row.get("source_timestamp_utc"),
                "freshness_state": str(row.get("freshness_state") or "FRESH"),
                "rights_state": str(row.get("rights_state") or "PUBLIC_READ_ONLY"),
                "pit_state": str(row.get("pit_state") or "PASS"),
                "epistemic_state": "ATTRIBUTED_REPORT_OR_INTERPRETATION",
                "exact_or_proxy": "EXACT",
                "contradiction_state": str(row.get("contradiction_state") or "NONE"),
                "values": {"headline_text": headline_text},
            }
        )
    memory_rows = [dict(row) for row in published_memory if isinstance(row, Mapping)]
    return {
        "sidecars": sidecars,
        "published_memory": memory_rows,
        "admitted_records": [
            dict(row) for row in admitted_records if isinstance(row, Mapping)
        ],
        "read_models": [dict(row) for row in read_models if isinstance(row, Mapping)],
    }


def _source_value(row: Mapping[str, Any], field: str) -> Any:
    if field in row:
        return row.get(field)
    values = row.get("values")
    if isinstance(values, Mapping):
        return values.get(field)
    return None


def _source_hash(row: Mapping[str, Any]) -> str:
    supplied = str(row.get("source_hash") or row.get("evidence_hash") or "")
    if supplied:
        return supplied
    return _sha(_without(row, "source_hash", "evidence_hash"))


def _row_eligible(
    row: Mapping[str, Any], need: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if row.get("admissible", True) is not True:
        blockers.append("not_admissible")
    if str(row.get("freshness_state") or "FRESH").upper() not in {"FRESH", "CURRENT"}:
        blockers.append("stale")
    if str(row.get("rights_state") or "ALLOWED").upper() not in {
        "ALLOWED",
        "PUBLIC_READ_ONLY",
    }:
        blockers.append("rights_denied")
    if need.get("pit_required") and str(row.get("pit_state") or "PASS").upper() not in {
        "PASS",
        "AVAILABLE",
    }:
        blockers.append("pit_unavailable")
    missing = [
        field
        for field in need.get("required_fields") or []
        if _source_value(row, str(field)) in (None, "")
    ]
    if missing:
        blockers.append("missing:" + ",".join(sorted(missing)))
    epistemic = str(row.get("epistemic_state") or "OBSERVED_FACT")
    if epistemic not in EPISTEMIC_LAYERS:
        blockers.append("epistemic_state_invalid")
    if (
        need.get("exact_or_proxy") == "EXACT"
        and str(row.get("exact_or_proxy") or "EXACT") != "EXACT"
    ):
        blockers.append("proxy_not_allowed")
    return not blockers, blockers


def _normalize_browser_result(
    result: Mapping[str, Any], need: Mapping[str, Any]
) -> dict[str, Any]:
    if (
        result.get("public_write_performed") is True
        or result.get("credential_or_session_material_read") is True
    ):
        raise FourTriggerAdapterError("browseros_recovery_write_or_secret_violation")
    tool_policy = result.get("tool_policy")
    if isinstance(tool_policy, Mapping) and (
        tool_policy.get("act_tool_used") is True
        or tool_policy.get("upload_tool_used") is True
        or tool_policy.get("download_tool_used") is True
    ):
        raise FourTriggerAdapterError("browseros_recovery_mutating_tool_violation")
    visible_hash = str(
        result.get("visible_evidence_sha256")
        or result.get("canonical_content_sha256")
        or result.get("rendered_page_sha256")
        or ""
    )
    if not re.fullmatch(r"[0-9a-f]{64}", visible_hash):
        raise FourTriggerAdapterError("browseros_visible_evidence_hash_required")
    return {
        "need_id": need["need_id"],
        "source_identity": _require_text(
            result.get("source_identity")
            or result.get("final_url")
            or "BROWSEROS_PUBLIC_SOURCE",
            "browser_source_identity",
            max_len=512,
        ),
        "source_class": "BROWSEROS_RENDERED_PUBLIC_SOURCE",
        "source_hash": visible_hash,
        "query_reference": "browseros.read_only_recovery",
        "retrieved_at_utc": _ensure_utc(
            result.get("retrieved_at_utc") or result.get("observed_at_utc"),
            "browser_retrieved_at_utc",
        ),
        "observed_at_utc": _ensure_utc(
            result.get("observed_at_utc") or result.get("retrieved_at_utc"),
            "browser_observed_at_utc",
        ),
        "known_at_utc": _ensure_utc(
            result.get("known_at_utc")
            or result.get("observed_at_utc")
            or result.get("retrieved_at_utc"),
            "browser_known_at_utc",
        ),
        "rights_state": str(result.get("rights_state") or "PUBLIC_READ_ONLY").upper(),
        "freshness_state": str(result.get("freshness_state") or "FRESH").upper(),
        "pit_state": str(result.get("pit_state") or "PASS").upper(),
        "epistemic_state": str(
            result.get("epistemic_state") or "ATTRIBUTED_REPORT_OR_INTERPRETATION"
        ),
        "exact_or_proxy": str(result.get("exact_or_proxy") or "EXACT").upper(),
        "values": deepcopy(
            result.get("values")
            or {field: result.get(field) for field in need["required_fields"]}
        ),
        "contradiction_state": str(result.get("contradiction_state") or "UNRESOLVED"),
        "fallback_reason": "database_missing_or_stale_required_field",
        "browser_runtime": deepcopy(result.get("browser_runtime") or {}),
        "tool_policy": deepcopy(
            tool_policy or {"allowed_tools_used": ["name_session", "tabs", "read"]}
        ),
        "public_write_performed": False,
    }


def _source_layers(source_layers: Mapping[str, Any]) -> list[tuple[str, Any]]:
    return [
        ("RETAINED_HEADLINE_SIDECAR", source_layers.get("sidecars")),
        ("PUBLISHED_MEMORY", source_layers.get("published_memory")),
        ("ADMITTED_OFFICIAL_FILING_PROVIDER", source_layers.get("admitted_records")),
        ("EXISTING_MARKET_READ_MODEL", source_layers.get("read_models")),
    ]


def _rows(value: Any, need: Mapping[str, Any]) -> list[dict[str, Any]]:
    if callable(value):
        value = value(need)
    if value is None:
        return []
    if isinstance(value, Mapping):
        value = [value]
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise FourTriggerAdapterError("source_layer_rows_invalid")
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _need_resolution(
    need: Mapping[str, Any],
    source_layers: Mapping[str, Any],
    browser_recovery: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    contradiction_rows: list[dict[str, Any]] = []
    for route, source in _source_layers(source_layers):
        if route not in need.get("permitted_routes", ROUTES):
            continue
        for row in _rows(source, need):
            row["need_id"] = str(row.get("need_id") or need["need_id"])
            if row["need_id"] != need["need_id"]:
                continue
            ok, blockers = _row_eligible(row, need)
            contradiction = str(row.get("contradiction_state") or "NONE").upper()
            if contradiction in {"CONTRADICTORY", "UNRESOLVED"}:
                contradiction_rows.append(row)
            attempts.append(
                {
                    "route": route,
                    "source_identity": row.get("source_identity"),
                    "source_hash": _source_hash(row),
                    "freshness_state": row.get("freshness_state") or "FRESH",
                    "rights_state": row.get("rights_state") or "ALLOWED",
                    "pit_state": row.get("pit_state") or "PASS",
                    "accepted": bool(ok),
                    "blockers": list(blockers),
                }
            )
            if ok:
                eligible.append({**row, "_route": route})
        if eligible:
            break

    if len(eligible) > 1:
        values = {
            _sha(
                {field: _source_value(row, field) for field in need["required_fields"]}
            )
            for row in eligible
        }
        if len(values) > 1:
            contradiction_rows.extend(eligible)
    if contradiction_rows:
        return {
            "need_id": need["need_id"],
            "state": "DATA_BLOCKED",
            "route": "UNAVAILABLE",
            "source_identity": None,
            "source_hash": None,
            "attempts": attempts,
            "contradiction": {
                "state": "UNRESOLVED",
                "source_hashes": sorted(
                    {_source_hash(row) for row in contradiction_rows}
                ),
            },
            "missing_fields": list(need["required_fields"]),
            "stale_fields": [],
            "rights_blocked_fields": [],
            "fallback_reason": "contradictory_database_evidence",
            "epistemic_state": "SCENARIO_OR_UNCERTAINTY",
        }
    if eligible:
        row = eligible[0]
        return {
            "need_id": need["need_id"],
            "state": "RESOLVED",
            "route": row["_route"],
            "source_identity": row.get("source_identity"),
            "source_class": row.get("source_class"),
            "source_hash": _source_hash(row),
            "query_reference": row.get("query_reference"),
            "retrieved_at_utc": row.get("retrieved_at_utc"),
            "observed_at_utc": row.get("observed_at_utc"),
            "known_at_utc": row.get("known_at_utc"),
            "rights_state": row.get("rights_state") or "ALLOWED",
            "freshness_state": row.get("freshness_state") or "FRESH",
            "pit_state": row.get("pit_state") or "PASS",
            "epistemic_state": row.get("epistemic_state") or "OBSERVED_FACT",
            "exact_or_proxy": row.get("exact_or_proxy") or "EXACT",
            "values": deepcopy(
                row.get("values")
                or {
                    field: _source_value(row, field)
                    for field in need["required_fields"]
                }
            ),
            "attempts": attempts,
            "contradiction": {"state": "NONE", "source_hashes": []},
            "missing_fields": [],
            "stale_fields": [],
            "rights_blocked_fields": [],
            "fallback_reason": None,
        }

    db_blockers = [
        blocker for attempt in attempts for blocker in attempt.get("blockers") or []
    ]
    if need.get("browseros_allowed") and "BROWSEROS_READ_ONLY" in need.get(
        "permitted_routes", ()
    ):
        if not need.get("browseros_url"):
            db_blockers.append("browseros_url_missing")
        elif browser_recovery is not None:
            recovered = _normalize_browser_result(browser_recovery(need), need)
            ok, browser_blockers = _row_eligible(recovered, need)
            attempts.append(
                {
                    "route": "BROWSEROS_READ_ONLY",
                    "source_identity": recovered.get("source_identity"),
                    "source_hash": recovered.get("source_hash"),
                    "freshness_state": recovered.get("freshness_state"),
                    "rights_state": recovered.get("rights_state"),
                    "pit_state": recovered.get("pit_state"),
                    "accepted": bool(ok),
                    "blockers": list(browser_blockers),
                }
            )
            if ok:
                return {
                    "need_id": need["need_id"],
                    "state": "RESOLVED",
                    "route": "BROWSEROS_READ_ONLY",
                    "source_identity": recovered["source_identity"],
                    "source_class": recovered["source_class"],
                    "source_hash": recovered["source_hash"],
                    "query_reference": recovered["query_reference"],
                    "retrieved_at_utc": recovered["retrieved_at_utc"],
                    "observed_at_utc": recovered["observed_at_utc"],
                    "known_at_utc": recovered["known_at_utc"],
                    "rights_state": recovered["rights_state"],
                    "freshness_state": recovered["freshness_state"],
                    "pit_state": recovered["pit_state"],
                    "epistemic_state": recovered["epistemic_state"],
                    "exact_or_proxy": recovered["exact_or_proxy"],
                    "values": recovered["values"],
                    "attempts": attempts,
                    "contradiction": {
                        "state": recovered.get("contradiction_state", "NONE"),
                        "source_hashes": [],
                    },
                    "missing_fields": [],
                    "stale_fields": [],
                    "rights_blocked_fields": [],
                    "fallback_reason": recovered["fallback_reason"],
                    "browser_runtime": recovered.get("browser_runtime"),
                    "tool_policy": recovered.get("tool_policy"),
                }
            db_blockers.extend(browser_blockers)
    missing_fields = list(need["required_fields"])
    stale = ["stale"] if "stale" in db_blockers else []
    rights = ["rights_denied"] if "rights_denied" in db_blockers else []
    state = "STALE" if stale and not rights else "DATA_BLOCKED"
    if not attempts and not browser_recovery:
        state = "UNAVAILABLE"
    return {
        "need_id": need["need_id"],
        "state": state,
        "route": "UNAVAILABLE",
        "source_identity": None,
        "source_hash": None,
        "attempts": attempts,
        "contradiction": {"state": "NONE", "source_hashes": []},
        "missing_fields": missing_fields,
        "stale_fields": stale,
        "rights_blocked_fields": rights,
        "fallback_reason": ";".join(sorted(set(db_blockers)))
        or "database_no_admissible_record",
        "epistemic_state": "SCENARIO_OR_UNCERTAINTY",
    }


def _resolution_core(
    plan: Mapping[str, Any], resolutions: Sequence[Mapping[str, Any]], *, resumed: bool
) -> dict[str, Any]:
    states = [str(row.get("state") or "UNAVAILABLE") for row in resolutions]
    if all(state == "RESOLVED" for state in states):
        state = "RESOLVED"
    elif any(state == "DATA_BLOCKED" for state in states):
        state = "DATA_BLOCKED"
    elif any(state == "STALE" for state in states):
        state = "STALE"
    elif any(state == "RESOLVED" for state in states):
        state = "PARTIAL"
    else:
        state = "UNAVAILABLE"
    core = {
        "schema_version": DATA_RESOLUTION_RECEIPT_SCHEMA,
        "request_id": plan.get("request_id"),
        "request_hash": plan.get("request_hash"),
        "plan_hash": plan.get("plan_hash"),
        "consumer_route": CONSUMER_ROUTE,
        "resolution_state": state,
        "resolutions": sorted(
            (deepcopy(dict(row)) for row in resolutions), key=lambda row: row["need_id"]
        ),
        "database_first_order": list(plan.get("database_first_order") or []),
        "resolver_version": plan.get("resolver_version"),
        "no_write": True,
        "public_write_performed": False,
        "resume_mode": "RESUME" if resumed else "INITIAL",
        "remaining_missing_fields": sorted(
            {field for row in resolutions for field in row.get("missing_fields") or []}
        ),
        "remaining_stale_fields": sorted(
            {field for row in resolutions for field in row.get("stale_fields") or []}
        ),
        "rights_blocked_fields": sorted(
            {
                field
                for row in resolutions
                for field in row.get("rights_blocked_fields") or []
            }
        ),
        "contradiction_states": sorted(
            {
                str((row.get("contradiction") or {}).get("state") or "NONE")
                for row in resolutions
            }
        ),
    }
    return core


def resolve_data_need_plan(
    plan: Mapping[str, Any],
    *,
    source_layers: Mapping[str, Any],
    browser_recovery: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve needs in order, optionally resuming an immutable terminal checkpoint."""
    _validate_hash(plan, "plan_hash")
    if str(plan.get("consumer_route") or "") != CONSUMER_ROUTE:
        raise FourTriggerAdapterError("consumer_route_invalid")
    prior_by_need: dict[str, Mapping[str, Any]] = {}
    if checkpoint is not None:
        if str(checkpoint.get("plan_hash") or "") != str(plan.get("plan_hash") or ""):
            raise FourTriggerAdapterError("checkpoint_plan_hash_mismatch")
        supplied = str(checkpoint.get("receipt_hash") or "")
        expected = _sha(_without(checkpoint, "receipt_hash", "idempotency_replayed"))
        if supplied != expected:
            raise FourTriggerAdapterError("checkpoint_receipt_hash_mismatch")
        prior_by_need = {
            str(row.get("need_id")): row
            for row in checkpoint.get("resolutions") or []
            if isinstance(row, Mapping) and str(row.get("state") or "") == "RESOLVED"
        }
        if str(checkpoint.get("resolution_state") or "") in RESOLUTION_STATES:
            replay = deepcopy(dict(checkpoint))
            replay["idempotency_replayed"] = True
            return replay
    resolutions: list[dict[str, Any]] = []
    for need in plan.get("needs") or []:
        need_id = str(need.get("need_id") or "")
        if need_id in prior_by_need:
            resolutions.append(deepcopy(dict(prior_by_need[need_id])))
            continue
        resolutions.append(_need_resolution(need, source_layers, browser_recovery))
    core = _resolution_core(plan, resolutions, resumed=bool(prior_by_need))
    return {**core, "receipt_hash": _sha(core)}


def write_resolution_checkpoint(path: str | Path, receipt: Mapping[str, Any]) -> str:
    """Persist one adapter checkpoint atomically; this is not the production durable store."""
    _validate_hash(receipt, "receipt_hash")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(_canonical(receipt) + b"\n")
    temporary.replace(target)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def load_resolution_checkpoint(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise FourTriggerAdapterError("checkpoint_not_object")
    _validate_hash(value, "receipt_hash")
    return dict(value)


def build_analysis_run_receipt(
    request: Mapping[str, Any],
    plan: Mapping[str, Any],
    resolution: Mapping[str, Any],
    *,
    analysis_context: Mapping[str, Any] | None = None,
    selected_consumer: str = CONSUMER_ROUTE,
    output_class: str = "ANALYSIS_ONLY",
    decision_version: str | None = None,
) -> dict[str, Any]:
    """Bind the shared resolution to an editorial analysis consumer without Core authority."""
    for record, field in (
        (request, "request_hash"),
        (plan, "plan_hash"),
        (resolution, "receipt_hash"),
    ):
        _validate_hash(record, field)
    if output_class not in {
        "ANALYSIS_ONLY",
        "EDITORIAL_DRAFT",
        "EDITORIAL_PUBLISHABLE",
        "DATA_BLOCKED",
    }:
        raise FourTriggerAdapterError("analysis_output_class_invalid")
    blocked = str(resolution.get("resolution_state") or "") != "RESOLVED"
    effective_class = "DATA_BLOCKED" if blocked else output_class
    context = deepcopy(dict(analysis_context or {}))
    if _secret_found(context):
        raise FourTriggerAdapterError("analysis_context_secret_material_forbidden")
    core = {
        "schema_version": ANALYSIS_RUN_RECEIPT_SCHEMA,
        "request_id": request.get("request_id"),
        "request_hash": request.get("request_hash"),
        "plan_hash": plan.get("plan_hash"),
        "resolution_receipt_hash": resolution.get("receipt_hash"),
        "consumer_route": selected_consumer,
        "selected_consumer": selected_consumer,
        "editorial_owner": EDITORIAL_OWNER,
        "output_class": effective_class,
        "requested_output_class": output_class,
        "decision_version": decision_version,
        "analysis_context": context,
        "epistemic_layers": list(EPISTEMIC_LAYERS),
        "exact_proxy_dimensions": sorted(
            {
                str(row.get("exact_or_proxy") or "")
                for row in resolution.get("resolutions") or []
            }
        ),
        "contradictory_evidence": [
            row.get("need_id")
            for row in resolution.get("resolutions") or []
            if str((row.get("contradiction") or {}).get("state") or "NONE") != "NONE"
        ],
        "deferred_needs": [
            row.get("need_id")
            for row in resolution.get("resolutions") or []
            if str(row.get("state") or "") != "RESOLVED"
        ],
        "no_write": True,
        "broker_write_performed": False,
        "public_write_performed": False,
        "authority": {
            "core_numeric_truth": False,
            "forecast_authority": False,
            "portfolio_authority": False,
            "publication_authority": False,
        },
        "terminal_state": "DATA_BLOCKED" if blocked else "COMPLETE_SHADOW",
    }
    return {**core, "analysis_receipt_hash": _sha(core)}


def build_serving_coverage_projection(
    rows: Sequence[Mapping[str, Any]], *, snapshot_id: str, as_of_utc: datetime | str
) -> dict[str, Any]:
    """Create a public-safe capability/readiness projection with null unknown denominators."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if _secret_found(row):
            raise FourTriggerAdapterError("coverage_secret_material_forbidden")
        normalized.append(
            {
                "capability_id": _require_text(
                    row.get("capability_id"), "capability_id", max_len=160
                ),
                "asset_class": _require_text(
                    row.get("asset_class") or "UNSPECIFIED", "asset_class", max_len=80
                ),
                "instrument_or_underlying": str(
                    row.get("instrument_or_underlying") or ""
                )
                or None,
                "query_reference": str(row.get("query_reference") or "") or None,
                "implemented": row.get("implemented")
                if isinstance(row.get("implemented"), bool)
                else None,
                "queryable": row.get("queryable")
                if isinstance(row.get("queryable"), bool)
                else None,
                "admissible": row.get("admissible")
                if isinstance(row.get("admissible"), bool)
                else None,
                "freshness_state": str(row.get("freshness_state") or "UNKNOWN"),
                "last_known_at_utc": row.get("last_known_at_utc"),
                "pit_state": str(row.get("pit_state") or "UNKNOWN"),
                "rights_state": str(row.get("rights_state") or "UNKNOWN"),
                "exact_or_proxy": str(row.get("exact_or_proxy") or "UNKNOWN"),
                "proxy_basis_risk": str(row.get("proxy_basis_risk") or "") or None,
                "missing_dimensions": sorted(
                    {str(v) for v in row.get("missing_dimensions") or []}
                ),
                "deployed": row.get("deployed")
                if isinstance(row.get("deployed"), bool)
                else None,
                "operating_state": str(row.get("operating_state") or "UNKNOWN"),
                "naturally_demonstrated": row.get("naturally_demonstrated")
                if isinstance(row.get("naturally_demonstrated"), bool)
                else None,
                "source_hash": str(row.get("source_hash") or "") or None,
            }
        )
    core = {
        "schema_version": SERVING_COVERAGE_PROJECTION_SCHEMA,
        "consumer_route": CONSUMER_ROUTE,
        "snapshot_id": _require_text(snapshot_id, "snapshot_id", max_len=160),
        "as_of_utc": _ensure_utc(as_of_utc, "as_of_utc"),
        "rows": sorted(normalized, key=lambda row: row["capability_id"]),
        "unknown_denominators": None,
        "public_safe": True,
        "private_portfolio_fields_included": False,
        "no_write": True,
    }
    return {**core, "projection_hash": _sha(core)}


def build_editorial_consumer_packet(
    request: Mapping[str, Any],
    plan: Mapping[str, Any],
    resolution: Mapping[str, Any],
    *,
    article_builder: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Project an admissible resolution into the existing Simple editorial owner seam."""
    for record, field in (
        (request, "request_hash"),
        (plan, "plan_hash"),
        (resolution, "receipt_hash"),
    ):
        _validate_hash(record, field)
    if str(request.get("consumer_route") or "") != CONSUMER_ROUTE:
        raise FourTriggerAdapterError("consumer_route_invalid")
    state = str(resolution.get("resolution_state") or "UNAVAILABLE")
    blocked = state != "RESOLVED"
    packet = {
        "schema_version": "contentops.editorial_shared_resolution_packet.v1",
        "request_id": request.get("request_id"),
        "request_hash": request.get("request_hash"),
        "plan_hash": plan.get("plan_hash"),
        "resolution_receipt_hash": resolution.get("receipt_hash"),
        "consumer_route": CONSUMER_ROUTE,
        "editorial_owner": EDITORIAL_OWNER,
        "editorial_operation": EDITORIAL_OPERATION,
        "sourceability_owner": "v1_simple_gemini_newsroom_v1",
        "dedupe_owner": "v1_simple_gemini_newsroom_v1",
        "selector_owner": "v1_simple_gemini_newsroom_v1",
        "writer_owner": "v1_simple_gemini_newsroom_v1",
        "validator_owner": "v1_simple_gemini_newsroom_v1",
        "publication_owner": PUBLICATION_OWNER,
        "canonical_destination": "substack",
        "derivative_destinations": list(DESTINATIONS),
        "cdp_boundaries": {
            "ingestion_only": CDP_INGESTION_PORT,
            "publication_media_readback": CDP_PUBLICATION_READBACK_PORT,
        },
        "epistemic_layers": list(EPISTEMIC_LAYERS),
        "resolution_state": state,
        "editorial_disposition": "DATA_BLOCKED"
        if blocked
        else "READY_FOR_EXISTING_OWNER",
        "resolved_evidence": deepcopy(list(resolution.get("resolutions") or [])),
        "missing_fields": list(resolution.get("remaining_missing_fields") or []),
        "stale_fields": list(resolution.get("remaining_stale_fields") or []),
        "rights_blocked_fields": list(resolution.get("rights_blocked_fields") or []),
        "public_write_performed": False,
        "no_write": True,
        "creates_scheduler": False,
        "creates_store": False,
        "creates_publisher": False,
        "article_builder_injected": callable(article_builder),
    }
    if callable(article_builder) and not blocked:
        packet["article_builder_result"] = article_builder(packet)
    return {**packet, "packet_hash": _sha(packet)}


def prepare_simple_gemini_handoff(
    packet: Mapping[str, Any], *, output_dir: str | Path, cutoff_utc: datetime | str
) -> dict[str, Any]:
    """Prepare arguments for the existing Simple Gemini owner without invoking runtime."""
    _validate_hash(packet, "packet_hash")
    if str(packet.get("editorial_disposition") or "") == "DATA_BLOCKED":
        return {
            "schema_version": "contentops.simple_gemini_handoff.v1",
            "disposition": "DATA_BLOCKED",
            "editorial_owner": EDITORIAL_OWNER,
            "operation": EDITORIAL_OPERATION,
            "invoked": False,
            "public_write_performed": False,
            "packet_hash": packet.get("packet_hash"),
        }
    context = {
        "schema_version": "contentops.simple_gemini_context_adapter.v1",
        "consumer_route": CONSUMER_ROUTE,
        "request_id": packet.get("request_id"),
        "resolution_receipt_hash": packet.get("resolution_receipt_hash"),
        "epistemic_layers": list(packet.get("epistemic_layers") or EPISTEMIC_LAYERS),
        "resolved_evidence": deepcopy(list(packet.get("resolved_evidence") or [])),
        "missing_fields": list(packet.get("missing_fields") or []),
        "stale_fields": list(packet.get("stale_fields") or []),
        "rights_blocked_fields": list(packet.get("rights_blocked_fields") or []),
        "grants_capital_chronicle_numeric_authority": False,
        "grants_publication_authority": False,
        "public_write_performed": False,
    }
    return {
        "schema_version": "contentops.simple_gemini_handoff.v1",
        "disposition": "READY_FOR_EXISTING_OWNER",
        "editorial_owner": EDITORIAL_OWNER,
        "operation": EDITORIAL_OPERATION,
        "invoked": False,
        "runner_arguments": {
            "output_dir": str(Path(output_dir)),
            "cutoff_utc": _ensure_utc(cutoff_utc, "cutoff_utc"),
            "capital_chronicle_context": context,
        },
        "no_new_scheduler": True,
        "no_new_store": True,
        "no_new_publisher": True,
        "public_write_performed": False,
        "packet_hash": packet.get("packet_hash"),
    }


def build_epistemic_derivative_manifest(
    article: Mapping[str, Any],
    derivative_payloads: Mapping[str, Mapping[str, Any]],
    *,
    canonical_url: str,
) -> dict[str, Any]:
    """Attach the article's epistemic bindings to existing eight derivative intents."""
    claims = article.get("epistemic_claims") or []
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
        raise FourTriggerAdapterError("article_epistemic_claims_invalid")
    normalized_claims = []
    for claim in claims:
        if (
            not isinstance(claim, Mapping)
            or str(claim.get("layer") or "") not in EPISTEMIC_LAYERS
        ):
            raise FourTriggerAdapterError("article_epistemic_claim_layer_invalid")
        normalized_claims.append(
            {
                "claim_id": _require_text(
                    claim.get("claim_id"), "claim_id", max_len=160
                ),
                "layer": str(claim["layer"]),
                "source_ids": sorted(
                    {str(value) for value in claim.get("source_ids") or []}
                ),
            }
        )
    claim_hash = _sha(normalized_claims)
    rows: dict[str, dict[str, Any]] = {}
    for destination in DESTINATIONS:
        payload = derivative_payloads.get(destination)
        if not isinstance(payload, Mapping):
            raise FourTriggerAdapterError(
                f"derivative_destination_missing:{destination}"
            )
        rows[destination] = {
            "destination": destination,
            "intent_status": "SHADOW_ONLY",
            "canonical_url": canonical_url,
            "canonical_url_state": "RECONCILED_CANONICAL_URL_REQUIRED",
            "payload_hash": _sha(dict(payload)),
            "epistemic_claim_hash": claim_hash,
            "epistemic_claim_ids": [row["claim_id"] for row in normalized_claims],
            "epistemic_layers": sorted({row["layer"] for row in normalized_claims}),
            "public_write_performed": False,
            "unknown_write": False,
        }
    core = {
        "schema_version": "contentops.eight_derivative_epistemic_manifest.v1",
        "canonical_article_epistemic_claims": normalized_claims,
        "derivatives": rows,
        "derivative_count": len(rows),
        "canonical_url": canonical_url,
        "all_layers_preserved": all(
            set(row["epistemic_claim_ids"])
            == {claim["claim_id"] for claim in normalized_claims}
            for row in rows.values()
        ),
        "public_write_performed": False,
        "unknown_write": False,
    }
    return {**core, "manifest_hash": _sha(core)}


def build_existing_eight_derivative_epistemic_manifest(
    *,
    article: Mapping[str, Any],
    selection: Mapping[str, Any],
    canonical_url: str,
    media_asset_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Compile through the existing eight-destination compiler, then bind epistemic state."""
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
        build_native_derivative_payloads,
    )

    payloads = build_native_derivative_payloads(
        article=article,
        selection=selection,
        canonical_url=canonical_url,
        media_asset_ids=media_asset_ids,
    )
    return build_epistemic_derivative_manifest(
        article, payloads, canonical_url=canonical_url
    )


def validate_adapter_artifact(
    artifact: Mapping[str, Any], hash_field: str
) -> list[str]:
    """Return deterministic blockers for a request/plan/receipt/packet artifact."""
    blockers: list[str] = []
    if _secret_found(artifact):
        blockers.append("secret_or_session_material")
    if artifact.get("no_write") is not True:
        blockers.append("no_write_false")
    if (
        artifact.get("public_write_performed") is True
        or artifact.get("broker_write_performed") is True
    ):
        blockers.append("write_performed")
    supplied = str(artifact.get(hash_field) or "")
    if not supplied or supplied != _sha(
        _without(artifact, hash_field, "idempotency_replayed")
    ):
        blockers.append(f"{hash_field}_mismatch")
    return blockers


def contract_bindings() -> dict[str, Any]:
    """Expose exact contract names and source hashes without redefining Main schemas."""
    return {
        "design_target": {
            "pr": 81,
            "head": DESIGN_PR81_HEAD,
            "path": DESIGN_PR81_PATH,
            "bytes": DESIGN_PR81_BYTES,
            "sha256": DESIGN_PR81_SHA256,
            "state": "OPEN_DESIGN_TARGET",
        },
        "main_model": {
            "path": MAIN_MODEL_PATH,
            "bytes": MAIN_MODEL_BYTES,
            "sha256": MAIN_MODEL_SHA256,
        },
        "contracts": {
            "trigger_request": TRIGGER_REQUEST_SCHEMA,
            "data_need_plan": DATA_NEED_PLAN_SCHEMA,
            "data_resolution_receipt": DATA_RESOLUTION_RECEIPT_SCHEMA,
            "analysis_run_receipt": ANALYSIS_RUN_RECEIPT_SCHEMA,
            "serving_coverage_projection": SERVING_COVERAGE_PROJECTION_SCHEMA,
        },
    }
