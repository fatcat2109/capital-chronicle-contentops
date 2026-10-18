"""Materialized three-trigger ContentOps research and editorial flow.

This is a deterministic integration layer on top of the Goal 15 shared-contract adapter.  It
turns the three current operational entries into bounded research packets while retaining the
existing Simple Gemini, publication, store, scheduler, and derivative owners.  The module never
opens the production store, starts a runtime, publishes, or reads private account material.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops.four_trigger_data_resolution_adapter_v1 import (
    CONSUMER_ROUTE,
    DESTINATIONS,
    EDITORIAL_OPERATION,
    EDITORIAL_OWNER,
    EPISTEMIC_LAYERS,
    FourTriggerAdapterError,
    PUBLICATION_OWNER,
    build_analysis_run_receipt,
    build_data_need_plan,
    build_editorial_consumer_packet,
    build_epistemic_derivative_manifest,
    build_existing_contentops_source_layers,
    build_existing_eight_derivative_epistemic_manifest,
    build_trigger_request,
    deduplicate_trigger_request,
    prepare_simple_gemini_handoff,
    resolve_data_need_plan,
    write_resolution_checkpoint,
)


SCHEMA_VERSION = "contentops.three_trigger_editorial_flow.v1"
OPERATIONAL_TRIGGER_KINDS = (
    "SCHEDULED_LATEST_INTELLIGENCE",
    "SCHEDULED_PORTFOLIO_CONTEXT",
    "JIM_MANUAL_CODEX_DESKTOP",
)
FOUNDATION_DATA_PLANE_KIND = "FOUNDATION_COVERAGE_SERVING"
ROUTINE_WINDOWS = ("17:00", "21:00", "23:00", "01:00")
CDP_INGESTION_PORT = 9222
CDP_PUBLICATION_READBACK_PORT = 9223
SIMPLE_OWNER = EDITORIAL_OWNER
SIMPLE_OPERATION = EDITORIAL_OPERATION
SIMPLE_CEILINGS = {
    "candidate_packet_max": 32,
    "admitted_candidates_max": 3,
    "source_gets_max": 6,
    "writer_calls_max": 1,
    "revision_max": 1,
    "logical_flash_calls_max": 3,
    "codex_runtime_model_calls_max": 0,
}
FLOW_DISPOSITIONS = (
    "READY_FOR_EDITORIAL_RESEARCH",
    "EDITORIAL_CONTEXT_READY",
    "REVIEW_READY",
    "DRAFT_ONLY",
    "PUBLISHABLE",
    "ABSTAIN",
    "DEFERRED",
    "DATA_BLOCKED",
    "UNAVAILABLE",
    "TERMINAL_REUSED",
)
PRIVATE_FIELD_TOKENS = (
    "private",
    "credential",
    "cookie",
    "session",
    "token",
    "password",
    "secret",
    "broker",
    "account",
    "position",
    "balance",
    "equity",
    "margin",
    "order",
    "fill",
    "execution",
    "pnl",
)
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class ThreeTriggerFlowError(FourTriggerAdapterError):
    """Fail-closed flow input or authority error."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _without(value: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    excluded = set(keys)
    return {key: deepcopy(item) for key, item in value.items() if key not in excluded}


def _iso(value: datetime | str) -> str:
    if isinstance(value, datetime):
        current = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value or "").strip()
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    if not _UTC_RE.fullmatch(text):
        raise ThreeTriggerFlowError("flow_time_must_be_utc")
    return text


def _text(value: Any, field: str, *, limit: int = 512) -> str:
    text = " ".join(str(value or "").split())
    if not text or len(text) > limit:
        raise ThreeTriggerFlowError(f"{field}_required_or_too_long")
    return text


def _contains_private(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).casefold()
            current = f"{path}.{key}" if path else str(key)
            if any(token in key_text for token in PRIVATE_FIELD_TOKENS):
                return current
            found = _contains_private(item, path=current)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _contains_private(item, path=f"{path}[{index}]")
            if found:
                return found
    return None


def _assert_no_private(value: Any, *, field: str) -> None:
    found = _contains_private(value)
    if found:
        raise ThreeTriggerFlowError(f"{field}_private_context_forbidden:{found}")


def _validate_request_hash(record: Mapping[str, Any], field: str) -> None:
    supplied = str(record.get(field) or "")
    if not supplied or supplied != _sha(_without(record, field)):
        raise ThreeTriggerFlowError(f"{field}_mismatch")


def _top_headline(rolling_input: Mapping[str, Any] | None) -> dict[str, Any] | None:
    rows = [
        row
        for row in (rolling_input or {}).get("headlines") or []
        if isinstance(row, Mapping)
    ]
    if not rows:
        return None
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("source_timestamp_utc") or ""),
            str(row.get("headline_id") or ""),
        ),
        reverse=True,
    )
    return dict(ordered[0])


def derive_latest_research_question(
    rolling_input: Mapping[str, Any] | None,
    *,
    audience: str = "PUBLIC_READER",
) -> dict[str, Any]:
    """Turn the newest retained headline into one bounded question without adding facts."""
    headline = _top_headline(rolling_input)
    if headline is None:
        return {
            "question_status": "UNAVAILABLE",
            "research_question": "No retained headline/event interval is available for a governed editorial question.",
            "headline_id": None,
            "headline_text": None,
            "source_timestamp_utc": None,
            "bounded_scope": "NO_CURRENT_HEADLINE",
        }
    external = (
        headline.get("external_content")
        if isinstance(headline.get("external_content"), Mapping)
        else {}
    )
    text = _text(
        external.get("headline_text") or headline.get("headline_text"),
        "headline_text",
        limit=1000,
    )
    return {
        "question_status": "READY",
        "research_question": (
            "What does this retained report say, what evidence establishes the underlying event, "
            f"and what remains uncertain for {audience}: {text}"
        ),
        "headline_id": str(headline.get("headline_id") or "") or None,
        "headline_text": text,
        "source_timestamp_utc": headline.get("source_timestamp_utc"),
        "bounded_scope": "ONE_HEADLINE_EVENT_INTERVAL",
    }


def _source_layers(
    *,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Mapping[str, Any]] = (),
    admitted_records: Sequence[Mapping[str, Any]] = (),
    read_models: Sequence[Mapping[str, Any]] = (),
) -> dict[str, list[dict[str, Any]]]:
    layers = build_existing_contentops_source_layers(
        rolling_input=rolling_input,
        published_memory=published_memory,
        admitted_records=admitted_records,
        read_models=read_models,
    )
    _assert_no_private(layers, field="source_layers")
    return layers


def _need(
    *,
    need_id: str,
    data_class: str,
    fields: Sequence[str],
    as_of_utc: str,
    permitted_routes: Sequence[str],
    exact_or_proxy: str = "EXACT",
    browseros_allowed: bool = False,
    browseros_url: str | None = None,
    pit_required: bool = True,
    basis_risk: str | None = None,
) -> dict[str, Any]:
    return {
        "need_id": need_id,
        "data_class": data_class,
        "required_fields": list(fields),
        "unit": "TEXT",
        "currency": "NONE",
        "clock": "UTC",
        "as_of_utc": as_of_utc,
        "freshness_budget_seconds": 86400,
        "revision_policy": "PRESERVE_VINTAGE",
        "pit_required": pit_required,
        "rights_class": "PUBLIC_READ_ONLY",
        "query_references": [f"contentops.{data_class}.v1"],
        "permitted_routes": list(permitted_routes),
        "browseros_allowed": browseros_allowed,
        "browseros_url": browseros_url,
        "exact_or_proxy": exact_or_proxy,
        "basis_risk": basis_risk,
        "missingness_behavior": "DATA_BLOCKED",
    }


def _truth_boundaries(resolution: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in resolution.get("resolutions") or [] if isinstance(row, Mapping)
    ]
    resolved = [row for row in rows if str(row.get("state") or "") == "RESOLVED"]
    report_states = sorted(
        {
            str(row.get("epistemic_state") or "")
            for row in resolved
            if row.get("epistemic_state")
        }
    )
    event_verified = any(
        bool((row.get("values") or {}).get("event_truth_verified"))
        and str(row.get("epistemic_state") or "") == "OBSERVED_FACT"
        for row in resolved
    )
    return {
        "report_truth": report_states or ["UNAVAILABLE"],
        "underlying_event_truth": "OBSERVED_FACT"
        if event_verified
        else "NOT_ESTABLISHED",
        "capital_chronicle_analysis": {
            "layer": "CAPITAL_CHRONICLE_ANALYSIS",
            "authority": False,
        },
        "scenario_or_uncertainty": {
            "layer": "SCENARIO_OR_UNCERTAINTY",
            "required_when_missing_or_contradictory": True,
        },
        "contradictions_preserved": [
            row.get("need_id")
            for row in rows
            if str((row.get("contradiction") or {}).get("state") or "NONE") != "NONE"
        ],
    }


def _resolution_disposition(
    resolution: Mapping[str, Any], *, ready: str, requested_output: str
) -> str:
    state = str(resolution.get("resolution_state") or "UNAVAILABLE")
    if state == "RESOLVED":
        return ready if requested_output == "RESEARCH_ONLY" else requested_output
    if state == "STALE":
        return "DEFERRED"
    if state == "UNAVAILABLE":
        return "ABSTAIN"
    if state == "DATA_BLOCKED":
        return "DATA_BLOCKED"
    return "ABSTAIN"


def _analysis_class(disposition: str) -> str:
    return {
        "PUBLISHABLE": "EDITORIAL_PUBLISHABLE",
        "DRAFT_ONLY": "EDITORIAL_DRAFT",
        "DATA_BLOCKED": "DATA_BLOCKED",
    }.get(disposition, "ANALYSIS_ONLY")


def _downstream_resolution(resolution: Mapping[str, Any]) -> dict[str, Any]:
    """Remove the replay marker before downstream consumers recheck the immutable hash."""
    value = deepcopy(dict(resolution))
    value.pop("idempotency_replayed", None)
    return value


def _flow_core(
    *,
    trigger_kind: str,
    request: Mapping[str, Any],
    plan: Mapping[str, Any],
    resolution: Mapping[str, Any],
    disposition: str,
    research_question: Mapping[str, Any] | None = None,
    editorial_packet: Mapping[str, Any] | None = None,
    handoff: Mapping[str, Any] | None = None,
    context_packet: Mapping[str, Any] | None = None,
    manual_review_packet: Mapping[str, Any] | None = None,
    analysis_receipt: Mapping[str, Any] | None = None,
    dedupe_receipt: Mapping[str, Any] | None = None,
    resumed: bool = False,
) -> dict[str, Any]:
    core = {
        "schema_version": SCHEMA_VERSION,
        "trigger_kind": trigger_kind,
        "request": deepcopy(dict(request)),
        "plan": deepcopy(dict(plan)),
        "resolution": deepcopy(dict(resolution)),
        "resolution_state": resolution.get("resolution_state"),
        "disposition": disposition,
        "research_question": deepcopy(dict(research_question or {})),
        "truth_boundaries": _truth_boundaries(resolution),
        "editorial_packet": deepcopy(dict(editorial_packet or {})),
        "simple_gemini_handoff": deepcopy(dict(handoff or {})),
        "editorial_context_packet": deepcopy(dict(context_packet or {})),
        "manual_review_packet": deepcopy(dict(manual_review_packet or {})),
        "analysis_receipt": deepcopy(dict(analysis_receipt or {})),
        "dedupe_receipt": deepcopy(dict(dedupe_receipt or {})),
        "resumed": bool(resumed),
        "owner_bindings": {
            "editorial_owner": SIMPLE_OWNER,
            "editorial_operation": SIMPLE_OPERATION,
            "publication_owner": PUBLICATION_OWNER,
            "routine_windows": list(ROUTINE_WINDOWS),
            "creates_scheduler": False,
            "creates_store": False,
            "creates_publisher": False,
        },
        "ceilings": deepcopy(SIMPLE_CEILINGS),
        "cdp_boundaries": {
            "ingestion_only": CDP_INGESTION_PORT,
            "publication_media_readback": CDP_PUBLICATION_READBACK_PORT,
        },
        "no_write": True,
        "public_write_performed": False,
        "broker_write_performed": False,
        "unknown_write": False,
        "automatic_runtime_invoked": False,
        "epistemic_layers": list(EPISTEMIC_LAYERS),
    }
    return {**core, "flow_hash": _sha(core)}


def _dedupe(
    request: Mapping[str, Any],
    terminal_by_idempotency_key: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    normalized: dict[str, Mapping[str, Any]] = {}
    for key, existing in (terminal_by_idempotency_key or {}).items():
        if not isinstance(existing, Mapping):
            continue
        if existing.get("request_hash"):
            normalized[key] = existing
            continue
        nested_request = existing.get("request")
        if isinstance(nested_request, Mapping) and nested_request.get("request_hash"):
            normalized[key] = {
                **dict(existing),
                "request_hash": nested_request.get("request_hash"),
                "request_status": existing.get("disposition") or existing.get("status"),
            }
    return deduplicate_trigger_request(request, normalized)


def run_latest_intelligence_trigger(
    *,
    request_id: str,
    idempotency_key: str,
    requested_at_utc: datetime | str,
    cutoff_utc: datetime | str,
    rolling_input: Mapping[str, Any] | None,
    published_memory: Sequence[Mapping[str, Any]] = (),
    admitted_records: Sequence[Mapping[str, Any]] = (),
    read_models: Sequence[Mapping[str, Any]] = (),
    browser_recovery: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    terminal_by_idempotency_key: Mapping[str, Mapping[str, Any]] | None = None,
    checkpoint: Mapping[str, Any] | None = None,
    output_dir: str | Path = "shadow/latest-intelligence",
    publication_intent: str = "RESEARCH_ONLY",
    article_validation_state: str = "NOT_RUN",
) -> dict[str, Any]:
    """Materialize one latest-headline research opportunity for the existing Simple owner."""
    requested = _iso(requested_at_utc)
    cutoff = _iso(cutoff_utc)
    question = derive_latest_research_question(rolling_input)
    checkpoint_request = (
        checkpoint.get("flow_request") if isinstance(checkpoint, Mapping) else None
    )
    checkpoint_plan = (
        checkpoint.get("flow_plan") if isinstance(checkpoint, Mapping) else None
    )
    if isinstance(checkpoint_request, Mapping) and isinstance(checkpoint_plan, Mapping):
        request = deepcopy(dict(checkpoint_request))
        _validate_request_hash(request, "request_hash")
        if (
            str(request.get("request_id") or "") != request_id
            or str(request.get("idempotency_key") or "") != idempotency_key
        ):
            raise ThreeTriggerFlowError("resume_request_identity_mismatch")
        question = {
            "question_status": "RESUMED",
            "research_question": str(request.get("decision_purpose") or ""),
            "headline_id": None,
            "headline_text": None,
            "source_timestamp_utc": None,
            "bounded_scope": "CHECKPOINT_BOUND_REQUEST",
        }
    else:
        request = build_trigger_request(
            request_id=request_id,
            idempotency_key=idempotency_key,
            trigger_kind="SCHEDULED_LATEST_INTELLIGENCE",
            requester=SIMPLE_OWNER,
            target_assets=[],
            decision_purpose=question["research_question"],
            requested_at_utc=requested,
            editorial_mode="STANDARD_NEWS_ANALYSIS",
            audience="PUBLIC_READER",
            requested_format="EDITORIAL_RESEARCH_PACKET",
            publication_intent=publication_intent,
            required_epistemic_state="ATTRIBUTED_REPORT_OR_INTERPRETATION",
        )
    dedupe = _dedupe(request, terminal_by_idempotency_key)
    if dedupe.get("terminal_request_reused"):
        existing = terminal_by_idempotency_key.get(idempotency_key) or {}
        if isinstance(existing, Mapping) and existing.get("flow_hash"):
            return {
                **deepcopy(dict(existing)),
                "disposition": "TERMINAL_REUSED",
                "dedupe_receipt": dedupe,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "disposition": "TERMINAL_REUSED",
            "dedupe_receipt": dedupe,
            "flow_hash": _sha(dedupe),
        }
    layers = _source_layers(
        rolling_input=rolling_input,
        published_memory=published_memory,
        admitted_records=admitted_records,
        read_models=read_models,
    )
    needs = [
        _need(
            need_id="latest-headline-event",
            data_class="headline_event",
            fields=["headline_text"],
            as_of_utc=cutoff,
            permitted_routes=[
                "RETAINED_HEADLINE_SIDECAR",
                "PUBLISHED_MEMORY",
                "ADMITTED_OFFICIAL_FILING_PROVIDER",
                "BROWSEROS_READ_ONLY",
            ],
            browseros_allowed=browser_recovery is not None,
            browseros_url="https://www.example.com/public-event"
            if browser_recovery is not None
            else None,
        )
    ]
    plan = (
        deepcopy(dict(checkpoint_plan))
        if isinstance(checkpoint_plan, Mapping)
        else build_data_need_plan(request, needs, as_of_utc=cutoff)
    )
    resolution = resolve_data_need_plan(
        plan,
        source_layers=layers,
        browser_recovery=browser_recovery,
        checkpoint=checkpoint,
    )
    consumer_resolution = _downstream_resolution(resolution)
    disposition = _resolution_disposition(
        consumer_resolution,
        ready="READY_FOR_EDITORIAL_RESEARCH",
        requested_output=publication_intent,
    )
    if disposition == "PUBLISHABLE" and article_validation_state != "PASS":
        disposition = (
            "DRAFT_ONLY"
            if article_validation_state == "DRAFT"
            else "READY_FOR_EDITORIAL_RESEARCH"
        )
    editorial_packet = build_editorial_consumer_packet(
        request, plan, consumer_resolution
    )
    handoff = prepare_simple_gemini_handoff(
        editorial_packet, output_dir=output_dir, cutoff_utc=cutoff
    )
    analysis = build_analysis_run_receipt(
        request,
        plan,
        consumer_resolution,
        analysis_context={
            "research_question": question,
            "truth_boundaries": _truth_boundaries(consumer_resolution),
        },
        output_class=_analysis_class(disposition),
        decision_version="three-trigger-shadow-v1",
    )
    return _flow_core(
        trigger_kind=request["trigger_kind"],
        request=request,
        plan=plan,
        resolution=resolution,
        disposition=disposition,
        research_question=question,
        editorial_packet=editorial_packet,
        handoff=handoff,
        analysis_receipt=analysis,
        dedupe_receipt=dedupe,
        resumed=bool(
            resolution.get("idempotency_replayed")
            or resolution.get("resume_mode") == "RESUME"
        ),
    )


def _public_context_packet(
    *,
    request: Mapping[str, Any],
    resolution: Mapping[str, Any],
    context: Mapping[str, Any],
    disposition: str,
) -> dict[str, Any]:
    safe_values = {
        str(key): deepcopy(value)
        for key, value in context.items()
        if str(key).casefold() not in {"scope", "target_assets", "requested_fields"}
    }
    return {
        "schema_version": "contentops.public_safe_editorial_context_packet.v1",
        "request_id": request.get("request_id"),
        "consumer_route": CONSUMER_ROUTE,
        "portfolio_scope": "PUBLIC_SAFE_CONTEXT_ONLY",
        "disposition": disposition,
        "context": safe_values,
        "resolution_receipt_hash": resolution.get("receipt_hash"),
        "source_identity": [
            row.get("source_identity")
            for row in resolution.get("resolutions") or []
            if row.get("source_identity")
        ],
        "freshness_states": [
            row.get("freshness_state") for row in resolution.get("resolutions") or []
        ],
        "rights_states": [
            row.get("rights_state") for row in resolution.get("resolutions") or []
        ],
        "pit_states": [
            row.get("pit_state") for row in resolution.get("resolutions") or []
        ],
        "exact_or_proxy": [
            row.get("exact_or_proxy") for row in resolution.get("resolutions") or []
        ],
        "missing_fields": list(resolution.get("remaining_missing_fields") or []),
        "stale_fields": list(resolution.get("remaining_stale_fields") or []),
        "contradiction_states": list(resolution.get("contradiction_states") or []),
        "private_portfolio_data_included": False,
        "portfolio_decision": False,
        "broker_action": False,
        "no_write": True,
        "public_write_performed": False,
    }


def run_portfolio_safe_context_trigger(
    *,
    request_id: str,
    idempotency_key: str,
    requested_at_utc: datetime | str,
    as_of_utc: datetime | str,
    public_context: Mapping[str, Any],
    needs: Sequence[Mapping[str, Any]],
    source_layers: Mapping[str, Any],
    browser_recovery: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    terminal_by_idempotency_key: Mapping[str, Mapping[str, Any]] | None = None,
    checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve only owner-approved public-safe context; never return portfolio state or a trade."""
    _assert_no_private(public_context, field="public_context")
    _assert_no_private(source_layers, field="portfolio_source_layers")
    scope = str(public_context.get("scope") or "")
    if scope != "PUBLIC_SAFE_CONTEXT_ONLY":
        raise ThreeTriggerFlowError("portfolio_scope_not_public_safe")
    target_assets = public_context.get("target_assets") or []
    request = build_trigger_request(
        request_id=request_id,
        idempotency_key=idempotency_key,
        trigger_kind="SCHEDULED_PORTFOLIO_CONTEXT",
        requester="MAIN_APP_PORTFOLIO_CONTROL_PLANE",
        target_assets=target_assets,
        portfolio_scope=scope,
        decision_purpose="Provide public-safe context for editorial planning only.",
        requested_at_utc=_iso(requested_at_utc),
        editorial_mode="STANDARD_NEWS_ANALYSIS",
        requested_format="EDITORIAL_CONTEXT_PACKET",
        publication_intent="RESEARCH_ONLY",
        required_epistemic_state="CAPITAL_CHRONICLE_ANALYSIS",
    )
    dedupe = _dedupe(request, terminal_by_idempotency_key)
    if dedupe.get("terminal_request_reused"):
        existing = terminal_by_idempotency_key.get(idempotency_key) or {}
        if existing.get("flow_hash"):
            return {
                **deepcopy(dict(existing)),
                "disposition": "TERMINAL_REUSED",
                "dedupe_receipt": dedupe,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "disposition": "TERMINAL_REUSED",
            "dedupe_receipt": dedupe,
            "flow_hash": _sha(dedupe),
        }
    plan = build_data_need_plan(request, needs, as_of_utc=_iso(as_of_utc))
    resolution = resolve_data_need_plan(
        plan,
        source_layers=source_layers,
        browser_recovery=browser_recovery,
        checkpoint=checkpoint,
    )
    consumer_resolution = _downstream_resolution(resolution)
    disposition = _resolution_disposition(
        consumer_resolution,
        ready="EDITORIAL_CONTEXT_READY",
        requested_output="RESEARCH_ONLY",
    )
    context_packet = _public_context_packet(
        request=request,
        resolution=consumer_resolution,
        context=public_context,
        disposition=disposition,
    )
    analysis = build_analysis_run_receipt(
        request,
        plan,
        consumer_resolution,
        analysis_context={
            "public_safe_context": context_packet["context"],
            "portfolio_authority": False,
        },
        output_class="ANALYSIS_ONLY",
        decision_version="three-trigger-portfolio-context-shadow-v1",
    )
    return _flow_core(
        trigger_kind=request["trigger_kind"],
        request=request,
        plan=plan,
        resolution=resolution,
        disposition=disposition,
        context_packet=context_packet,
        analysis_receipt=analysis,
        dedupe_receipt=dedupe,
        resumed=bool(
            resolution.get("idempotency_replayed")
            or resolution.get("resume_mode") == "RESUME"
        ),
    )


def run_jim_manual_trigger(
    *,
    request_id: str,
    idempotency_key: str,
    requested_at_utc: datetime | str,
    scope: str,
    target_assets: Sequence[str],
    needs: Sequence[Mapping[str, Any]],
    source_layers: Mapping[str, Any],
    browser_recovery: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    terminal_by_idempotency_key: Mapping[str, Mapping[str, Any]] | None = None,
    checkpoint: Mapping[str, Any] | None = None,
    requested_format: str = "MANUAL_RESEARCH_REVIEW_PACKET",
) -> dict[str, Any]:
    """Return a reviewable Jim-scoped research packet without publication authority."""
    _assert_no_private(scope, field="manual_scope")
    _assert_no_private(source_layers, field="manual_source_layers")
    request = build_trigger_request(
        request_id=request_id,
        idempotency_key=idempotency_key,
        trigger_kind="JIM_MANUAL_CODEX_DESKTOP",
        requester="Jim",
        target_assets=target_assets,
        decision_purpose=_text(scope, "manual_scope", limit=512),
        requested_at_utc=_iso(requested_at_utc),
        editorial_mode="STANDARD_NEWS_ANALYSIS",
        audience="JIM_OWNER_REVIEW",
        requested_format=requested_format,
        publication_intent="RESEARCH_ONLY",
        required_epistemic_state="OBSERVED_FACT",
    )
    dedupe = _dedupe(request, terminal_by_idempotency_key)
    if dedupe.get("terminal_request_reused"):
        existing = terminal_by_idempotency_key.get(idempotency_key) or {}
        if existing.get("flow_hash"):
            return {
                **deepcopy(dict(existing)),
                "disposition": "TERMINAL_REUSED",
                "dedupe_receipt": dedupe,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "disposition": "TERMINAL_REUSED",
            "dedupe_receipt": dedupe,
            "flow_hash": _sha(dedupe),
        }
    plan = build_data_need_plan(request, needs, as_of_utc=_iso(requested_at_utc))
    resolution = resolve_data_need_plan(
        plan,
        source_layers=source_layers,
        browser_recovery=browser_recovery,
        checkpoint=checkpoint,
    )
    consumer_resolution = _downstream_resolution(resolution)
    disposition = _resolution_disposition(
        consumer_resolution, ready="REVIEW_READY", requested_output="RESEARCH_ONLY"
    )
    manual_packet = {
        "schema_version": "contentops.jim_manual_research_review_packet.v1",
        "request_id": request["request_id"],
        "scope": scope,
        "target_assets": list(request.get("target_assets") or []),
        "resolution_receipt_hash": resolution.get("receipt_hash"),
        "disposition": disposition,
        "source_identity": [
            row.get("source_identity")
            for row in consumer_resolution.get("resolutions") or []
            if row.get("source_identity")
        ],
        "observed_retrieved_known_at": [
            {
                key: row.get(key)
                for key in ("observed_at_utc", "retrieved_at_utc", "known_at_utc")
            }
            for row in consumer_resolution.get("resolutions") or []
        ],
        "rights": [
            row.get("rights_state")
            for row in consumer_resolution.get("resolutions") or []
        ],
        "freshness": [
            row.get("freshness_state")
            for row in consumer_resolution.get("resolutions") or []
        ],
        "pit": [
            row.get("pit_state") for row in consumer_resolution.get("resolutions") or []
        ],
        "epistemic_states": [
            row.get("epistemic_state")
            for row in consumer_resolution.get("resolutions") or []
        ],
        "exact_or_proxy": [
            row.get("exact_or_proxy")
            for row in consumer_resolution.get("resolutions") or []
        ],
        "contradictions": consumer_resolution.get("contradiction_states") or [],
        "missing_fields": list(
            consumer_resolution.get("remaining_missing_fields") or []
        ),
        "stale_fields": list(consumer_resolution.get("remaining_stale_fields") or []),
        "next_action": (
            "Review source-bound evidence and unresolved fields before drafting."
            if disposition == "REVIEW_READY"
            else "Resolve the listed blocker before any draft or publication consideration."
        ),
        "publication_authority": False,
        "public_write_performed": False,
        "no_write": True,
    }
    analysis = build_analysis_run_receipt(
        request,
        plan,
        consumer_resolution,
        analysis_context={"manual_review_scope": scope, "publication_authority": False},
        output_class="ANALYSIS_ONLY",
        decision_version="three-trigger-manual-shadow-v1",
    )
    return _flow_core(
        trigger_kind=request["trigger_kind"],
        request=request,
        plan=plan,
        resolution=resolution,
        disposition=disposition,
        manual_review_packet=manual_packet,
        analysis_receipt=analysis,
        dedupe_receipt=dedupe,
        resumed=bool(
            resolution.get("idempotency_replayed")
            or resolution.get("resume_mode") == "RESUME"
        ),
    )


def persist_flow_checkpoint(path: str | Path, flow: Mapping[str, Any]) -> str:
    """Persist the immutable resolution checkpoint embedded in a flow receipt."""
    flow_hash = str(flow.get("flow_hash") or "")
    if not flow_hash or flow_hash != _sha(_without(flow, "flow_hash")):
        raise ThreeTriggerFlowError("flow_hash_mismatch")
    resolution = flow.get("resolution")
    if not isinstance(resolution, Mapping):
        raise ThreeTriggerFlowError("flow_resolution_missing")
    envelope = deepcopy(dict(resolution))
    envelope.pop("idempotency_replayed", None)
    if isinstance(flow.get("request"), Mapping):
        envelope["flow_request"] = deepcopy(dict(flow["request"]))
    if isinstance(flow.get("plan"), Mapping):
        envelope["flow_plan"] = deepcopy(dict(flow["plan"]))
    core = _without(envelope, "receipt_hash")
    envelope["receipt_hash"] = _sha(core)
    return write_resolution_checkpoint(path, envelope)


def build_article_derivative_shadow_manifest(
    *,
    article: Mapping[str, Any],
    derivative_payloads: Mapping[str, Mapping[str, Any]] | None = None,
    selection: Mapping[str, Any] | None = None,
    canonical_url: str,
    media_asset_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Preserve article epistemic claims through the existing eight-intent compiler in shadow mode."""
    if derivative_payloads is None:
        if selection is None:
            raise ThreeTriggerFlowError(
                "selection_required_for_existing_derivative_compiler"
            )
        return build_existing_eight_derivative_epistemic_manifest(
            article=article,
            selection=selection,
            canonical_url=canonical_url,
            media_asset_ids=media_asset_ids,
        )
    return build_epistemic_derivative_manifest(
        article, derivative_payloads, canonical_url=canonical_url
    )


def flow_contract_bindings() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operational_trigger_kinds": list(OPERATIONAL_TRIGGER_KINDS),
        "foundation_data_plane_kind": FOUNDATION_DATA_PLANE_KIND,
        "consumer_route": CONSUMER_ROUTE,
        "editorial_owner": SIMPLE_OWNER,
        "editorial_operation": SIMPLE_OPERATION,
        "publication_owner": PUBLICATION_OWNER,
        "routine_windows": list(ROUTINE_WINDOWS),
        "cdp_boundaries": {
            "ingestion_only": CDP_INGESTION_PORT,
            "publication_media_readback": CDP_PUBLICATION_READBACK_PORT,
        },
        "derivative_destinations": list(DESTINATIONS),
        "no_write": True,
    }
