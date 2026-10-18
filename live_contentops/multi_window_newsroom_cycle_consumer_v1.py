"""Read-only consumer for the Main multi-window intelligence bundle.

The consumer keeps the three Main windows in one immutable newsroom shadow receipt.  It admits
only exact/current claims, carries proxy/context claims as qualitative context, quarantines
contradictions and stale or unauthorized rows, and delegates any admitted composition to the
existing scheduled shadow owner.  It does not own a scheduler, store, publisher, status ledger,
browser, provider, model, or public-write boundary.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping, Sequence

from live_contentops.scheduled_shadow_production_day_v1 import (
    SHADOW_CONFIRMED,
    UNKNOWN_WRITE,
    run_scheduled_shadow_production_day,
)


SCHEMA_VERSION = "CapitalChronicleMultiWindowIntelligenceCycleBundleV1"
RECEIPT_SCHEMA_VERSION = "contentops.multi_window_newsroom_cycle_receipt.v1"
VERSION = "1.0.0"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
WINDOW_IDS = ("CURRENT_REAL", "RECENT_REPLAY", "PROXY_CONTEXT")
EXACT_SCOPE = "EXACT_CORE"
PROXY_SCOPE = "PROXY_CONTEXT"
CONTEXT_SCOPE = "CONTEXT_ONLY"
CLASSIFICATIONS = frozenset(
    {
        "SHADOW_CONFIRMED",
        "NOT_VERIFIED",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "PACKET_HASH_MISMATCH",
        "PROOF_LAYER_MISMATCH",
        "SOURCE_HEAD_MISMATCH",
    }
)
AUTHORITY_FLAGS = (
    "main_authority",
    "public_write",
    "runtime_proven",
    "provider_call",
    "model_call",
    "network_call",
    "external_effect",
)
ZERO_EFFECT_KEYS = (
    "scheduler_started",
    "durable_store_write_count",
    "database_mutation",
    "model_call_count",
    "provider_call_count",
    "browser_action_count",
    "public_write_performed",
    "publication_authority",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|"
    r"api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)"
)
SECRET_VALUE_RE = re.compile(r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,})")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def bundle_sha256(value: Mapping[str, Any]) -> str:
    return sha256(canonical_bytes({k: v for k, v in value.items() if k != "bundle_sha256"})).hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256(canonical_bytes({k: v for k, v in value.items() if k != "receipt_sha256"})).hexdigest()


def _parse_utc(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _status(value: Mapping[str, Any] | None) -> str:
    return str((value or {}).get("status") or "")


def _unknown_write(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("unknown_write") is True or str(value.get("status") or "") == UNKNOWN_WRITE:
            return True
        return any(_unknown_write(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_unknown_write(item) for item in value)
    return False


def _walk_secret(value: Any, *, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                raise ValueError(f"secret_material:{path}.{key}")
            _walk_secret(item, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _walk_secret(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        raise ValueError(f"secret_material:{path}")


def _zero_effect(value: Mapping[str, Any]) -> dict[str, Any]:
    source = value.get("zero_effect") if isinstance(value.get("zero_effect"), Mapping) else {}
    return {key: source.get(key) for key in ZERO_EFFECT_KEYS}


def _observed_host_facts(bundle: Mapping[str, Any]) -> dict[str, Any]:
    core = bundle.get("core_projection") if isinstance(bundle.get("core_projection"), Mapping) else {}
    facts = core.get("host_facts") if isinstance(core.get("host_facts"), Mapping) else {}
    return {
        "browseros": facts.get("browseros"),
        "x_ingestion_cdp": facts.get("x_ingestion_cdp"),
        "publication_cdp": facts.get("publication_cdp"),
        "scheduler_tasks": facts.get("scheduler_tasks"),
        "identity": facts.get("identity"),
        "destination": facts.get("destination"),
        "store": facts.get("store"),
        "zero_effect": _zero_effect(core),
        "runtime_proven": facts.get("runtime_proven", False),
        "publicly_proven": facts.get("publicly_proven", False),
    }


def _claim_rows(window: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = window.get("claims")
    return [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, Sequence) else []


def _validate_window(window: Mapping[str, Any], *, as_of: datetime, blockers: list[str]) -> None:
    window_id = str(window.get("window_id") or "")
    if window_id not in WINDOW_IDS:
        blockers.append(f"window_id_invalid:{window_id}")
    if not SHA256_RE.fullmatch(str(window.get("source_hash") or "")):
        blockers.append(f"window_source_hash_invalid:{window_id}")
    if not SHA256_RE.fullmatch(str(window.get("claim_hash") or "")):
        blockers.append(f"window_claim_hash_invalid:{window_id}")
    freshness = window.get("freshness") if isinstance(window.get("freshness"), Mapping) else {}
    if freshness.get("status") not in {"FRESH", "STALE", "UNAVAILABLE"}:
        blockers.append(f"window_freshness_invalid:{window_id}")
    try:
        observed = _parse_utc(freshness.get("observed_at_utc"), f"{window_id}.observed_at_utc")
        known = _parse_utc(freshness.get("known_at_utc"), f"{window_id}.known_at_utc")
        if observed > known or known > as_of:
            blockers.append(f"window_clock_invalid:{window_id}")
        if freshness.get("status") != "FRESH":
            blockers.append(f"window_stale:{window_id}")
    except ValueError as exc:
        blockers.append(str(exc))
    rights = window.get("rights") if isinstance(window.get("rights"), Mapping) else {}
    if rights.get("status") != "READ_ONLY_OPERATOR_OBSERVATION" or rights.get("raw_payload_included") is not False:
        blockers.append(f"window_rights_invalid:{window_id}")
    proof = window.get("proof_layers") if isinstance(window.get("proof_layers"), Mapping) else {}
    for layer in ("IMPLEMENTED", "TESTED", "INTEGRATED", "HOST_OBSERVED", "RUNTIME_PROVEN", "PUBLICLY_PROVEN"):
        if proof.get(layer) is None:
            blockers.append(f"window_proof_missing:{window_id}:{layer}")
    labels = window.get("labels") if isinstance(window.get("labels"), Mapping) else {}
    if window_id == "CURRENT_REAL" and labels.get("host_readiness") != "NOT_VERIFIED":
        blockers.append("current_real_host_readiness_promoted")
    for claim in _claim_rows(window):
        claim_id = str(claim.get("claim_id") or "")
        claim_hash = str(claim.get("claim_hash") or "")
        if not claim_id or not SHA256_RE.fullmatch(claim_hash):
            blockers.append(f"claim_identity_or_hash_invalid:{window_id}:{claim_id}")
        if claim.get("claim_scope") not in {EXACT_SCOPE, PROXY_SCOPE, CONTEXT_SCOPE}:
            blockers.append(f"claim_scope_invalid:{window_id}:{claim_id}")
        if claim.get("rights") not in {"READ_ONLY", "PUBLIC_REPORTING_ALLOWED", "CONTEXT_ONLY_READ_ONLY"}:
            blockers.append(f"claim_rights_invalid:{window_id}:{claim_id}")
        if _unknown_write(claim):
            blockers.append(f"claim_unknown_write:{window_id}:{claim_id}")
        if claim.get("future") is True:
            blockers.append(f"claim_future:{window_id}:{claim_id}")


def validate_multi_window_bundle(bundle: Mapping[str, Any], *, now_utc: str | None = None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(bundle, Mapping):
        return ["bundle_not_mapping"]
    required = {
        "schema",
        "version",
        "cycle_id",
        "generated_at_utc",
        "as_of_utc",
        "parent_reconciliation",
        "windows",
        "core_projection",
        "editorial_projection",
        "drift_summary",
        "authority_flags",
        "bundle_sha256",
    }
    if set(bundle) != required:
        blockers.append("bundle_top_level_shape_invalid")
    if bundle.get("schema") != SCHEMA_VERSION or bundle.get("version") != VERSION:
        blockers.append("bundle_schema_or_version_invalid")
    supplied_hash = str(bundle.get("bundle_sha256") or "")
    if not SHA256_RE.fullmatch(supplied_hash) or supplied_hash != bundle_sha256(bundle):
        blockers.append("bundle_hash_invalid")
    try:
        as_of = _parse_utc(bundle.get("as_of_utc"), "bundle.as_of_utc")
        generated = _parse_utc(bundle.get("generated_at_utc"), "bundle.generated_at_utc")
        if generated > as_of:
            blockers.append("bundle_generated_after_as_of")
        if now_utc is not None and as_of > _parse_utc(now_utc, "now_utc"):
            blockers.append("bundle_future_as_of")
    except ValueError as exc:
        blockers.append(str(exc))
        as_of = datetime.now(timezone.utc)
    parent = bundle.get("parent_reconciliation") if isinstance(bundle.get("parent_reconciliation"), Mapping) else {}
    if not SHA256_RE.fullmatch(str(parent.get("receipt_sha256") or "")):
        blockers.append("parent_reconciliation_hash_invalid")
    if parent.get("classification") not in {"NOT_VERIFIED", "SHADOW_CONFIRMED", "BLOCKED"}:
        blockers.append("parent_reconciliation_classification_invalid")
    parent_source = parent.get("source") if isinstance(parent.get("source"), Mapping) else {}
    if not SHA1_RE.fullmatch(str(parent_source.get("main_head") or "")) or not SHA1_RE.fullmatch(str(parent_source.get("contentops_head") or "")):
        blockers.append("parent_source_heads_invalid")
    core = bundle.get("core_projection") if isinstance(bundle.get("core_projection"), Mapping) else {}
    source = core.get("source") if isinstance(core.get("source"), Mapping) else {}
    if (
        not SHA1_RE.fullmatch(str(source.get("main_head") or ""))
        or not SHA1_RE.fullmatch(str(source.get("contentops_head") or ""))
        or str(source.get("main_head")) == "0" * 40
        or str(source.get("contentops_head")) == "0" * 40
    ):
        blockers.append("core_source_heads_invalid")
    if source.get("main_repository") != "fatcat2109/capital-chronicle-main":
        blockers.append("core_main_repository_invalid")
    if source.get("contentops_repository") != "fatcat2109/capital-chronicle-contentops":
        blockers.append("core_contentops_repository_invalid")
    parent_source = parent.get("source") if isinstance(parent.get("source"), Mapping) else {}
    if parent_source.get("main_head") != source.get("main_head"):
        blockers.append("parent_main_head_mismatch")
    if not SHA1_RE.fullmatch(str(parent_source.get("contentops_head") or "")):
        blockers.append("parent_contentops_head_invalid")
    core_rights = core.get("rights") if isinstance(core.get("rights"), Mapping) else {}
    if core_rights.get("status") != "READ_ONLY_OPERATOR_OBSERVATION" or core_rights.get("raw_payload_included") is not False:
        blockers.append("core_rights_invalid")
    core_proof = core.get("proof_layers") if isinstance(core.get("proof_layers"), Mapping) else {}
    for layer in ("IMPLEMENTED", "TESTED", "INTEGRATED", "HOST_OBSERVED", "RUNTIME_PROVEN", "PUBLICLY_PROVEN"):
        if core_proof.get(layer) is None:
            blockers.append(f"core_proof_missing:{layer}")
    zero = core.get("zero_effect") if isinstance(core.get("zero_effect"), Mapping) else {}
    if set(zero) != set(ZERO_EFFECT_KEYS) or any(zero.get(key) not in (False, 0, None) for key in ZERO_EFFECT_KEYS):
        blockers.append("core_zero_effect_not_zero")
    authority = bundle.get("authority_flags") if isinstance(bundle.get("authority_flags"), Mapping) else {}
    if set(authority) != set(AUTHORITY_FLAGS) or any(authority.get(key) is not False for key in AUTHORITY_FLAGS):
        blockers.append("authority_flags_not_all_false")
    windows = bundle.get("windows")
    if not isinstance(windows, Sequence) or len(windows) != 3:
        blockers.append("windows_exactly_three_required")
    else:
        ids = [str(row.get("window_id") or "") for row in windows if isinstance(row, Mapping)]
        if tuple(ids) != WINDOW_IDS:
            blockers.append("window_order_or_identity_invalid")
        for window in windows:
            if isinstance(window, Mapping):
                _validate_window(window, as_of=as_of, blockers=blockers)
            else:
                blockers.append("window_not_mapping")
    drift = bundle.get("drift_summary") if isinstance(bundle.get("drift_summary"), Mapping) else {}
    if _unknown_write(drift):
        blockers.append("drift_summary_unknown_write")
    try:
        _walk_secret(bundle)
    except ValueError as exc:
        blockers.append(str(exc))
    return list(dict.fromkeys(blockers))


def _candidate_walk(bundle: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    windows = bundle.get("windows") or []
    selected: list[dict[str, Any]] = []
    abstained: list[str] = []
    quarantined: list[dict[str, Any]] = []
    context: list[dict[str, Any]] = []
    duplicate_ids: set[str] = set()
    for window in windows:
        if not isinstance(window, Mapping):
            continue
        for group in window.get("contradiction_groups") or []:
            if isinstance(group, Mapping):
                quarantined.append({"window_id": window.get("window_id"), **dict(group), "reason": "CONTRADICTION_QUARANTINE"})
                quarantined_ids = {str(value) for value in group.get("claim_ids") or []}
            else:
                quarantined_ids = set()
            for claim in _claim_rows(window):
                if str(claim.get("claim_id")) in quarantined_ids:
                    abstained.append(str(claim.get("claim_id")))
        for decision in window.get("dedupe") or []:
            if isinstance(decision, Mapping) and decision.get("decision") == "COLLAPSED":
                duplicate_ids.update(str(value) for value in decision.get("duplicate_ids") or [])
    for window in windows:
        if not isinstance(window, Mapping):
            continue
        for claim in _claim_rows(window):
            claim_id = str(claim.get("claim_id") or "")
            if claim_id in duplicate_ids:
                abstained.append(claim_id)
            elif claim.get("claim_scope") in {PROXY_SCOPE, CONTEXT_SCOPE}:
                context.append({"window_id": window.get("window_id"), **dict(claim), "promotion": "QUALITATIVE_CONTEXT_ONLY"})
            elif claim.get("claim_scope") == EXACT_SCOPE and claim.get("status") == "ELIGIBLE" and claim_id not in abstained and not claim.get("blockers"):
                selected.append({"window_id": window.get("window_id"), **dict(claim)})
            else:
                abstained.append(claim_id)
    unique_selected = {row["claim_id"]: row for row in selected}
    return [unique_selected[key] for key in sorted(unique_selected)], sorted(set(abstained)), quarantined, context


def _receipt_base(bundle: Mapping[str, Any], *, classification: str, blockers: Sequence[str], production_day: Mapping[str, Any] | None, selected: Sequence[Mapping[str, Any]], abstained: Sequence[str], quarantined: Sequence[Mapping[str, Any]], context: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    editorial = bundle.get("editorial_projection") if isinstance(bundle.get("editorial_projection"), Mapping) else {}
    derivatives = list((production_day or {}).get("derivative_destinations") or [])
    result = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "version": VERSION,
        "canonicalization": CANONICALIZATION,
        "cycle_id": bundle.get("cycle_id"),
        "status": "SHADOW_CONFIRMED" if classification == "SHADOW_CONFIRMED" else "BLOCKED",
        "immutable_receipt": True,
        "shadow_only": True,
        "bundle_sha256": bundle.get("bundle_sha256"),
        "parent_reconciliation_sha256": (bundle.get("parent_reconciliation") or {}).get("receipt_sha256"),
        "source_heads": {
            "main": (bundle.get("core_projection") or {}).get("source", {}).get("main_head"),
            "contentops": (bundle.get("core_projection") or {}).get("source", {}).get("contentops_head"),
        },
        "clocks": {
            "generated_at_utc": bundle.get("generated_at_utc"),
            "as_of_utc": bundle.get("as_of_utc"),
            "parent_known_at_utc": (bundle.get("parent_reconciliation") or {}).get("known_at_utc"),
        },
        "window_bindings": [
            {
                "window_id": row.get("window_id"),
                "source_hash": row.get("source_hash"),
                "claim_hash": row.get("claim_hash"),
                "dedupe": row.get("dedupe"),
                "contradiction_groups": row.get("contradiction_groups"),
                "labels": row.get("labels"),
                "unsupported_dimensions": row.get("unsupported_dimensions"),
                "blockers": row.get("blockers"),
            }
            for row in bundle.get("windows") or []
            if isinstance(row, Mapping)
        ],
        "selected_claim_ids": [str(row.get("claim_id")) for row in selected],
        "abstained_claim_ids": list(abstained),
        "qualitative_context_claim_ids": [str(row.get("claim_id")) for row in context],
        "contradiction_quarantine": [dict(row) for row in quarantined],
        "unsupported_dimensions": list((bundle.get("drift_summary") or {}).get("unsupported_dimensions") or []),
        "candidate_selection": dict(editorial.get("candidate_selection") or {}),
        "article_package": (production_day or {}).get("canonical_article_id"),
        "derivative_hashes": {
            "production_day_receipt_sha256": (production_day or {}).get("production_day_receipt_sha256"),
            "destination_readback_sha256": (production_day or {}).get("destination_readback_sha256"),
            "destinations": derivatives,
            "count": len(derivatives),
        },
        "interruption_resume": (production_day or {}).get("interruption_recovery", "NOT_ATTEMPTED"),
        "current_host_facts": _observed_host_facts(bundle),
        "authority_flags": dict(bundle.get("authority_flags") or {}),
        "zero_effect": _zero_effect(bundle.get("core_projection") or {}),
        "runtime_proven": False,
        "publicly_proven": False,
        "classification": classification,
        "blockers": list(dict.fromkeys(str(item) for item in blockers)),
        "next": "RETAIN_SHADOW_RECEIPT_AND_HAND_TO_MAIN_FOR_RECONCILIATION" if classification != "SHADOW_CONFIRMED" else "MAIN_MAY_CONSUME_SHADOW_RECEIPT_WITHOUT_RUNTIME_OR_PUBLIC_PROMOTION",
        "receipt_sha256": None,
    }
    result["receipt_sha256"] = receipt_sha256(result)
    return result


def consume_multi_window_newsroom_cycle(
    bundle: Mapping[str, Any],
    *,
    shadow_runner: Callable[..., Mapping[str, Any]] | None = None,
    now_utc: str | None = None,
) -> dict[str, Any]:
    """Validate one Main bundle and compose one read-only newsroom shadow cycle."""

    blockers = validate_multi_window_bundle(bundle, now_utc=now_utc)
    selected, abstained, quarantined, context = _candidate_walk(bundle if isinstance(bundle, Mapping) else {})
    if blockers:
        classification = "UNKNOWN_WRITE" if any("unknown_write" in item or "zero_effect" in item for item in blockers) else (
            "AUTHORITY_FLAG" if any("authority" in item for item in blockers) else (
                "STALE" if any("stale" in item or "future" in item or "clock" in item for item in blockers) else (
            "PACKET_HASH_MISMATCH" if any("hash" in item for item in blockers) else (
                "SOURCE_HEAD_MISMATCH" if any("head" in item or "repository" in item for item in blockers) else (
                    "PROOF_LAYER_MISMATCH" if any("proof" in item for item in blockers) else "NOT_VERIFIED"
                )
            )
                )
            )
        )
        return _receipt_base(bundle if isinstance(bundle, Mapping) else {}, classification=classification, blockers=blockers, production_day=None, selected=selected, abstained=abstained, quarantined=quarantined, context=context)
    core = bundle.get("core_projection") or {}
    if core.get("evidence_mode") == "CURRENT_REAL":
        blockers.append("current_real_host_boundary_not_verified")
        return _receipt_base(bundle, classification="NOT_VERIFIED", blockers=blockers, production_day=None, selected=selected, abstained=abstained, quarantined=quarantined, context=context)
    if not selected:
        return _receipt_base(bundle, classification="NOT_VERIFIED", blockers=["no_eligible_exact_current_claim"], production_day=None, selected=selected, abstained=abstained, quarantined=quarantined, context=context)
    editorial = bundle.get("editorial_projection") if isinstance(bundle.get("editorial_projection"), Mapping) else {}
    components = editorial.get("shadow_components")
    if not isinstance(components, Mapping):
        return _receipt_base(bundle, classification="NOT_VERIFIED", blockers=["shadow_components_missing"], production_day=None, selected=selected, abstained=abstained, quarantined=quarantined, context=context)
    runner = shadow_runner or run_scheduled_shadow_production_day
    try:
        production_day = runner(enabled=True, **dict(components))
    except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
        return _receipt_base(bundle, classification="BLOCKED", blockers=[f"shadow_composition_exception:{type(exc).__name__}"], production_day=None, selected=selected, abstained=abstained, quarantined=quarantined, context=context)
    if production_day.get("status") == UNKNOWN_WRITE:
        classification = "UNKNOWN_WRITE"
    elif production_day.get("status") != SHADOW_CONFIRMED:
        classification = "BLOCKED"
    else:
        classification = "SHADOW_CONFIRMED"
    blockers = [] if classification == "SHADOW_CONFIRMED" else [f"scheduled_shadow:{production_day.get('status')}:{production_day.get('failure_detail')}" ]
    return _receipt_base(bundle, classification=classification, blockers=blockers, production_day=production_day, selected=selected, abstained=abstained, quarantined=quarantined, context=context)


__all__ = [
    "AUTHORITY_FLAGS",
    "CANONICALIZATION",
    "CLASSIFICATIONS",
    "RECEIPT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "WINDOW_IDS",
    "bundle_sha256",
    "canonical_bytes",
    "consume_multi_window_newsroom_cycle",
    "receipt_sha256",
    "validate_multi_window_bundle",
]
