"""Read-only consumer for one self-contained Main App analysis handoff.

The producer owns the analytical packet and all authority decisions.  This module only
verifies the producer receipt, preserves the supplied claim bytes, builds the accepted V3
packet with its frozen V2 projection, and composes the existing shadow owners.  It never
creates authority, writes a store, calls a model/provider, navigates a browser, or publishes.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    build_content_evidence_packet_v3,
    validate_content_evidence_packet_v3,
)
from live_contentops.cc_evidence_bridge_v2 import validate_evidence_packet
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    DualLaneShadowError,
    build_package,
    review_package,
    run_capital_chronicle_lane,
    run_newsroom_lane,
)
from live_contentops.editorial_visual_research_v2 import evaluate_visual_composition
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    build_platform_native_variant,
)
from live_contentops.scheduled_shadow_production_day_v1 import (
    run_scheduled_shadow_production_day,
)
from live_contentops.universal_news_candidate_fabric_v2 import validate_claim
from live_contentops.universal_governed_registry_v1 import logical_hash


SCHEMA_VERSION = "contentops.main_analysis_handoff_consumer.v1"
MAIN_PACKET_SCHEMA = "capital_chronicle.main_app_daily_intelligence_decision_packet.v1"
V2_SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v2"
V3_SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v3"
STATUS_SHADOW_REVIEW_READY = "SHADOW_REVIEW_READY"
STATUS_REJECTED = "REJECTED"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"
STATUS_DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"
UNKNOWN_WRITE = "UNKNOWN_WRITE"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CLAIM_RELATIONSHIPS = frozenset(
    {"duplicate", "incremental_update", "material_update", "correction", "contradiction"}
)
_EXACT_SCOPE = "EXACT_CORE"
_PROXY_SCOPE = "PROXY_CONTEXT"
_PUBLIC_RIGHTS = frozenset({"PUBLIC_REPORTING_ALLOWED", "CC_PUBLICATION_AUTHORIZED"})
_CONTEXT_RIGHTS = frozenset({"CONTEXT_ONLY_READ_ONLY", "READ_ONLY_CONTEXT"})
_FORBIDDEN_AUTHORITY_FLAGS = (
    "contentops_numeric_authority",
    "contentops_forecast_authority",
    "contentops_market_decision_authority",
    "contentops_publication_authority",
    "contentops_permission_upgrade",
    "contentops_recalculation_performed",
)
_FORBIDDEN_INPUT_SIDE_EFFECT_FLAGS = (
    "scheduler_started",
    "database_mutation",
    "model_call_performed",
    "provider_call_performed",
    "browser_action_performed",
    "public_write_performed",
)
_DESTINATION_TO_PLATFORM = {
    "telegram": "telegram",
    "x": "x_twitter",
    "discord": "discord",
    "linkedin": "linkedin",
    "facebook_page": "facebook_page",
    "instagram_business": "instagram_business",
    "threads": "threads",
    "youtube": "youtube_community",
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _hash(value: Any) -> str:
    return sha256(_canonical_json(value)).hexdigest()


def _without_hash(value: Mapping[str, Any], *fields: str) -> dict[str, Any]:
    ignored = {"logical_hash", "packet_logical_hash", "packet_identity_sha256", *fields}
    return {key: item for key, item in value.items() if key not in ignored}


def _parse_utc(value: Any, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _status(component: Mapping[str, Any] | None) -> str:
    return str((component or {}).get("status") or "")


def _base(bridge: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_DISABLED_BY_DEFAULT if not enabled else None,
        "enabled": bool(enabled),
        "shadow_only": True,
        "immutable_receipt": True,
        "input_packet_id": bridge.get("packet_id"),
        "input_packet_logical_hash": bridge.get("packet_logical_hash"),
        "receipt_sha256": None,
        "v3_packet_logical_hash": None,
        "v2_projection_sha256": None,
        "claim_lineage_sha256": None,
        "quarantined_claim_ids": [],
        "exact_core_claim_ids": [],
        "proxy_context_claim_ids": [],
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "database_mutation": False,
        "model_call_count": 0,
        "provider_call_count": 0,
        "browser_action_count": 0,
        "public_write_performed": False,
        "publication_authority": False,
        "numeric_authority_created": False,
        "forecast_authority_created": False,
        "market_decision_authority_created": False,
    }


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["receipt_sha256"] = _hash(
        {key: value for key, value in result.items() if key != "receipt_sha256"}
    )
    return result


def _reject(result: dict[str, Any], blockers: Sequence[str], *, status: str = STATUS_REJECTED) -> dict[str, Any]:
    result.update(
        {
            "status": status,
            "validation_blockers": list(dict.fromkeys(str(value) for value in blockers)),
            "failure_detail": ";".join(str(value) for value in blockers),
        }
    )
    return _finish(result)


def _mapping_rows(value: Any, *, field: str, blockers: list[str]) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        blockers.append(f"{field}_must_be_list")
        return []
    rows = [row for row in value if isinstance(row, Mapping)]
    if len(rows) != len(value):
        blockers.append(f"{field}_row_must_be_object")
    return rows


def _validate_packet_identity(bridge: Mapping[str, Any], blockers: list[str]) -> None:
    if bridge.get("schema_version") != MAIN_PACKET_SCHEMA:
        blockers.append("main_packet_schema_invalid")
    packet_id = str(bridge.get("packet_id") or "")
    identity = bridge.get("packet_identity")
    if not packet_id or not isinstance(identity, Mapping):
        blockers.append("packet_identity_missing")
        return
    if str(identity.get("packet_id") or "") != packet_id:
        blockers.append("packet_identity_id_mismatch")
    identity_hash = str(bridge.get("packet_identity_sha256") or "")
    if not _SHA256_RE.fullmatch(identity_hash) or identity_hash != _hash(identity):
        blockers.append("packet_identity_hash_invalid")
    supplied_hash = str(bridge.get("packet_logical_hash") or bridge.get("logical_hash") or "")
    expected_hash = _hash(_without_hash(bridge))
    if not _SHA256_RE.fullmatch(supplied_hash):
        blockers.append("main_packet_logical_hash_invalid")
    elif supplied_hash != expected_hash:
        blockers.append("main_packet_logical_hash_mismatch")


def _validate_clock_surface(
    bridge: Mapping[str, Any],
    *,
    now_utc: str,
    blockers: list[str],
) -> str | None:
    clocks = bridge.get("clocks")
    if not isinstance(clocks, Mapping):
        blockers.append("clock_surface_missing")
        return None
    parsed: dict[str, datetime] = {}
    for field in (
        "event_time_utc",
        "revision_at_utc",
        "observed_at_utc",
        "known_at_utc",
        "pit_cutoff_utc",
    ):
        try:
            parsed[field] = _parse_utc(clocks.get(field), field=f"clock_{field}")
        except ValueError as exc:
            blockers.append(str(exc))
    if not parsed:
        return None
    pit = parsed.get("pit_cutoff_utc")
    if pit is None:
        return None
    try:
        now = _parse_utc(now_utc, field="consumer_now_utc")
    except ValueError as exc:
        blockers.append(str(exc))
        now = None
    if now is not None and pit > now:
        blockers.append("pit_cutoff_in_future")
    for field, value in parsed.items():
        if value > pit:
            blockers.append(f"clock_{field}_after_pit_cutoff")
    for earlier, later in (
        ("event_time_utc", "observed_at_utc"),
        ("observed_at_utc", "known_at_utc"),
        ("revision_at_utc", "known_at_utc"),
    ):
        if earlier in parsed and later in parsed and parsed[earlier] > parsed[later]:
            blockers.append(f"clock_order_invalid:{earlier}>{later}")
    return _utc_text(pit)


def _validate_freshness_and_rights(
    bridge: Mapping[str, Any],
    *,
    pit_cutoff_utc: str | None,
    blockers: list[str],
) -> dict[str, Mapping[str, Any]]:
    freshness = bridge.get("freshness")
    if not isinstance(freshness, Mapping):
        blockers.append("freshness_surface_missing")
    else:
        if freshness.get("status") != "FRESH":
            blockers.append("freshness_not_fresh")
        try:
            age = float(freshness.get("age_seconds"))
            maximum = float(freshness.get("max_age_seconds"))
            if age > maximum:
                blockers.append("freshness_age_exceeds_maximum")
        except (TypeError, ValueError):
            blockers.append("freshness_age_or_maximum_invalid")

    documents = _mapping_rows(
        bridge.get("evidence_documents"), field="evidence_documents", blockers=blockers
    )
    by_id: dict[str, Mapping[str, Any]] = {}
    for document in documents:
        document_id = str(document.get("document_id") or "")
        if not document_id or document_id in by_id:
            blockers.append(f"evidence_document_id_invalid_or_duplicate:{document_id or 'missing'}")
        by_id[document_id] = document
        if not _SHA256_RE.fullmatch(str(document.get("content_sha256") or "")):
            blockers.append(f"evidence_document_hash_invalid:{document_id or 'missing'}")
        rights = str(document.get("rights_status") or "")
        if rights not in _PUBLIC_RIGHTS | _CONTEXT_RIGHTS:
            blockers.append(f"evidence_document_rights_invalid:{document_id or 'missing'}")
        if str(document.get("freshness_status") or "") != "FRESH":
            blockers.append(f"evidence_document_stale:{document_id or 'missing'}")
        if pit_cutoff_utc:
            try:
                if _parse_utc(document.get("known_at_utc"), field="document_known_at") > _parse_utc(
                    pit_cutoff_utc, field="pit_cutoff_utc"
                ):
                    blockers.append(f"evidence_document_known_at_after_pit:{document_id}")
            except ValueError as exc:
                blockers.append(f"{document_id}:{exc}")
    return by_id


def _validate_claims_and_authority(
    bridge: Mapping[str, Any],
    *,
    documents: Mapping[str, Mapping[str, Any]],
    pit_cutoff_utc: str | None,
    blockers: list[str],
) -> tuple[list[Mapping[str, Any]], list[str], list[str]]:
    claims = _mapping_rows(bridge.get("claims"), field="claims", blockers=blockers)
    claim_ids: set[str] = set()
    exact_ids: list[str] = []
    proxy_ids: list[str] = []
    cutoff = pit_cutoff_utc or str(bridge.get("generated_at_utc") or "")
    provenance_refs = {
        str(value) for value in (bridge.get("provenance") or {}).get("evidence_refs") or []
    }
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id or claim_id in claim_ids:
            blockers.append(f"claim_id_invalid_or_duplicate:{claim_id or 'missing'}")
        claim_ids.add(claim_id)
        blockers.extend(
            f"{claim_id or 'unknown'}:{value}"
            for value in validate_claim(claim, cutoff_utc=cutoff)
        )
        scope = str(claim.get("claim_scope") or "")
        if scope == _EXACT_SCOPE:
            exact_ids.append(claim_id)
            if claim.get("permission_state") != "PUBLIC_CLAIM_ALLOWED":
                blockers.append(f"exact_core_claim_not_publicly_eligible:{claim_id}")
            if claim.get("authority_origin") != "MAIN_APP_CORE_ANALYZER":
                blockers.append(f"exact_core_claim_origin_invalid:{claim_id}")
        elif scope == _PROXY_SCOPE:
            proxy_ids.append(claim_id)
            if claim.get("authority_class") != "CONTEXT_ONLY":
                blockers.append(f"proxy_claim_authority_not_context_only:{claim_id}")
            if claim.get("permission_state") != "CONTEXT_ONLY":
                blockers.append(f"proxy_claim_permission_not_context_only:{claim_id}")
            if claim.get("numeric") is not None or claim.get("qualitative_only") is not True:
                blockers.append(f"proxy_claim_not_qualitative_only:{claim_id}")
        else:
            blockers.append(f"claim_scope_invalid:{claim_id or 'missing'}")
        references = {str(value) for value in claim.get("evidence_refs") or []}
        if not references.issubset(provenance_refs):
            blockers.append(f"claim_provenance_ref_missing:{claim_id}")
        document_ids = {str(value) for value in claim.get("source_document_ids") or []}
        if not document_ids.issubset(documents):
            blockers.append(f"claim_source_document_missing:{claim_id}")
        for document_id in document_ids:
            document = documents.get(document_id) or {}
            rights = str(document.get("rights_status") or "")
            if claim.get("permission_state") == "PUBLIC_CLAIM_ALLOWED" and rights not in _PUBLIC_RIGHTS:
                blockers.append(f"claim_public_rights_invalid:{claim_id}:{document_id}")
            if claim.get("permission_state") == "CONTEXT_ONLY" and rights not in _CONTEXT_RIGHTS:
                blockers.append(f"claim_context_rights_invalid:{claim_id}:{document_id}")
        for citation in claim.get("citations") or []:
            document = documents.get(str(citation.get("source_document_id") or "")) or {}
            if str(citation.get("url") or "") not in {
                str(value) for value in document.get("authorized_urls") or []
            }:
                blockers.append(f"claim_citation_not_authorized:{claim_id}")
    authority = bridge.get("authority_boundary")
    if not isinstance(authority, Mapping):
        blockers.append("authority_boundary_missing")
    else:
        for field in _FORBIDDEN_AUTHORITY_FLAGS:
            if authority.get(field) is not False:
                blockers.append(f"authority_flag_not_false:{field}")
        if authority.get("authority_origin") != "MAIN_APP_CORE_ANALYZER":
            blockers.append("authority_origin_not_main_core")
    return claims, exact_ids, proxy_ids


def _validate_lineage(bridge: Mapping[str, Any], *, claim_ids: set[str], pit_cutoff_utc: str | None, blockers: list[str]) -> tuple[list[str], str | None]:
    lineage = bridge.get("claim_lineage")
    rows = _mapping_rows(lineage, field="claim_lineage", blockers=blockers)
    relationship_ids: set[str] = set()
    for row in rows:
        relationship_id = str(row.get("relationship_id") or "")
        if not relationship_id or relationship_id in relationship_ids:
            blockers.append(f"claim_relationship_id_invalid_or_duplicate:{relationship_id or 'missing'}")
        relationship_ids.add(relationship_id)
        if row.get("relationship") not in _CLAIM_RELATIONSHIPS:
            blockers.append(f"claim_relationship_invalid:{relationship_id or 'missing'}")
        for field in ("claim_id", "related_claim_id"):
            if str(row.get(field) or "") not in claim_ids:
                blockers.append(f"claim_relationship_ref_missing:{relationship_id}:{field}")
        if pit_cutoff_utc:
            try:
                if _parse_utc(row.get("revision_at_utc"), field="relationship_revision") > _parse_utc(
                    pit_cutoff_utc, field="pit_cutoff_utc"
                ):
                    blockers.append(f"claim_relationship_revision_after_pit:{relationship_id}")
            except ValueError as exc:
                blockers.append(f"{relationship_id}:{exc}")
        supplied_hash = str(row.get("logical_hash") or "")
        if not _SHA256_RE.fullmatch(supplied_hash) or supplied_hash != logical_hash(_without_hash(row)):
            blockers.append(f"claim_relationship_hash_invalid:{relationship_id or 'missing'}")

    contradictions = _mapping_rows(
        bridge.get("contradictions"), field="contradictions", blockers=blockers
    )
    quarantined: list[str] = []
    for row in contradictions:
        contradiction_id = str(row.get("contradiction_id") or "")
        related = [str(value) for value in row.get("claim_ids") or []]
        if row.get("status") != "UNRESOLVED" or row.get("quarantine") != "REQUIRED":
            blockers.append(f"contradiction_not_quarantined:{contradiction_id or 'missing'}")
        for claim_id in related:
            if claim_id not in claim_ids:
                blockers.append(f"contradiction_claim_missing:{contradiction_id}:{claim_id}")
            elif claim_id not in quarantined:
                quarantined.append(claim_id)
        supplied_hash = str(row.get("logical_hash") or "")
        if not _SHA256_RE.fullmatch(supplied_hash) or supplied_hash != logical_hash(_without_hash(row)):
            blockers.append(f"contradiction_hash_invalid:{contradiction_id or 'missing'}")
    return quarantined, _hash(rows)


def _validate_context_boundaries(bridge: Mapping[str, Any], blockers: list[str]) -> None:
    for field in _FORBIDDEN_INPUT_SIDE_EFFECT_FLAGS:
        if bridge.get(field) is True:
            blockers.append(f"input_side_effect_flag_not_false:{field}")
    context_rows = _mapping_rows(
        bridge.get("context_sources"), field="context_sources", blockers=blockers
    )
    for row in context_rows:
        channel = str(row.get("channel") or "")
        if channel == "browseros":
            if row.get("read_only") is not True or row.get("credential_material_read") is not False:
                blockers.append("browseros_context_not_read_only")
        elif channel == "x":
            if row.get("cdp_port") != 9222 or row.get("ingestion_only") is not True:
                blockers.append("x_context_not_cdp_9222_ingestion_only")
        else:
            blockers.append(f"context_channel_invalid:{channel or 'missing'}")
        if any(row.get(key) is True for key in ("public_write_performed", "browser_action_performed", "provider_call_performed")):
            blockers.append(f"context_live_side_effect:{channel or 'unknown'}")


def _validate_candidate_surface(
    bridge: Mapping[str, Any],
    *,
    claims: Sequence[Mapping[str, Any]],
    documents: Mapping[str, Mapping[str, Any]],
    blockers: list[str],
) -> Mapping[str, Any] | None:
    candidate = bridge.get("candidate")
    if not isinstance(candidate, Mapping):
        blockers.append("candidate_missing")
        return None
    supplied_claims = list(candidate.get("claims") or [])
    if supplied_claims != [dict(row) for row in claims]:
        blockers.append("candidate_claim_bytes_not_exact_bridge_claim_bytes")
    supplied_hash = str(candidate.get("logical_hash") or "")
    if not _SHA256_RE.fullmatch(supplied_hash) or supplied_hash != logical_hash(_without_hash(candidate)):
        blockers.append("candidate_logical_hash_invalid")
    refs = {str(value) for value in candidate.get("evidence_refs") or []}
    expected_refs = {str(value) for claim in claims for value in claim.get("evidence_refs") or []}
    if refs != expected_refs:
        blockers.append("candidate_evidence_refs_not_exact_claim_union")
    producer_provenance = bridge.get("provenance")
    if isinstance(producer_provenance, Mapping) and producer_provenance.get(
        "candidate_logical_hash"
    ) != candidate.get("logical_hash"):
        blockers.append("producer_candidate_logical_hash_mismatch")
    candidate_document_ids = {
        str(row.get("document_id") or "") for row in candidate.get("source_documents") or []
    }
    if candidate_document_ids != set(documents):
        blockers.append("candidate_source_document_set_mismatch")
    if candidate.get("publication_authority") is not False or candidate.get("public_write_allowed") is not False:
        blockers.append("candidate_live_authority_flag_not_false")
    return candidate


def _build_derivative_shadow_rows(
    *,
    package: Mapping[str, Any],
    authority_hash: str,
    claim_ids: Sequence[str],
    citations: Sequence[Mapping[str, Any]],
    limitations: Sequence[str],
    visual_assets: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    article = package["article"]
    platform = package["platform"]
    headline = str(article["headline"])
    summary = str(article["answer_first_summary"])
    source_label = str(platform["payloads"][0].get("source_label") or "Main Core Analyzer")
    citation_urls = [str(row.get("url")) for row in citations if row.get("url")]
    visual_ids = [str(row.get("asset_id")) for row in visual_assets if row.get("asset_id")]
    visual_hashes = [str(row.get("sha256")) for row in visual_assets if row.get("sha256")]
    rows: list[dict[str, Any]] = []
    for destination, platform_id in _DESTINATION_TO_PLATFORM.items():
        variant = build_platform_native_variant(
            platform_id=platform_id,
            subject_id=str(package["package_id"]),
            candidate_id=str(package["package_id"]),
            authority_logical_hash=authority_hash,
            authorized_claim_ids=claim_ids,
            headline=headline,
            summary=summary,
            source_label=source_label,
            citation_urls=citation_urls,
            limitations=limitations,
            visual_asset_ids=visual_ids if platform_id == "instagram_business" else (),
            visual_asset_hashes=visual_hashes if platform_id == "instagram_business" else (),
        )
        rows.append(
            {
                "destination": destination,
                "status": "SHADOW_READY",
                "payload_sha256": str(variant["payload_hash"]),
                "platform_id": platform_id,
                "package_id": package["package_id"],
                "public_write_performed": False,
                "dispatch_authority": False,
            }
        )
    return rows


def consume_main_analysis_handoff_shadow(
    bridge: Mapping[str, Any],
    *,
    enabled: bool = False,
    now_utc: str | None = None,
    schedule_date: str | None = None,
    window: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Consume one producer-owned Main handoff and return an immutable shadow receipt."""

    result = _base(bridge, enabled=enabled)
    if not enabled:
        return _reject(result, ["main_analysis_handoff_consumer_disabled_by_default"], status=STATUS_DISABLED_BY_DEFAULT)
    if not isinstance(bridge, Mapping):
        return _reject(result, ["main_analysis_handoff_must_be_object"])

    blockers: list[str] = []
    _validate_packet_identity(bridge, blockers)
    consumer_now = now_utc or _utc_text(datetime.now(timezone.utc))
    pit_cutoff = _validate_clock_surface(bridge, now_utc=consumer_now, blockers=blockers)
    documents = _validate_freshness_and_rights(bridge, pit_cutoff_utc=pit_cutoff, blockers=blockers)
    claims, exact_ids, proxy_ids = _validate_claims_and_authority(
        bridge, documents=documents, pit_cutoff_utc=pit_cutoff, blockers=blockers
    )
    quarantined, lineage_hash = _validate_lineage(
        bridge,
        claim_ids={str(row.get("claim_id") or "") for row in claims},
        pit_cutoff_utc=pit_cutoff,
        blockers=blockers,
    )
    _validate_context_boundaries(bridge, blockers)
    candidate = _validate_candidate_surface(
        bridge, claims=claims, documents=documents, blockers=blockers
    )
    v2_packet = bridge.get("v2_compatibility_projection")
    if not isinstance(v2_packet, Mapping):
        blockers.append("v2_compatibility_projection_missing")
    else:
        if v2_packet.get("schema_version") != V2_SCHEMA_VERSION:
            blockers.append("v2_compatibility_schema_invalid")
        blockers.extend(f"v2:{item}" for item in validate_evidence_packet(v2_packet))
        if v2_packet.get("generated_at_utc") != bridge.get("generated_at_utc"):
            blockers.append("v2_projection_generated_at_mismatch")
        supplied_v2_hash = str(bridge.get("v2_projection_sha256") or "")
        if not _SHA256_RE.fullmatch(supplied_v2_hash) or supplied_v2_hash != _hash(v2_packet):
            blockers.append("v2_projection_hash_invalid")
        if v2_packet.get("packet_id") != bridge.get("packet_id"):
            blockers.append("v2_projection_packet_identity_mismatch")

    if blockers:
        result.update(
            {
                "input_packet_logical_hash": bridge.get("packet_logical_hash"),
                "exact_core_claim_ids": exact_ids,
                "proxy_context_claim_ids": proxy_ids,
                "quarantined_claim_ids": quarantined,
                "claim_lineage_sha256": lineage_hash,
            }
        )
        return _reject(result, blockers)
    assert candidate is not None
    assert isinstance(v2_packet, Mapping)

    try:
        packet = build_content_evidence_packet_v3(
            candidate,
            generated_at_utc=str(bridge["generated_at_utc"]),
            v2_packet=v2_packet,
        )
    except (TypeError, ValueError, KeyError) as exc:
        return _reject(result, [f"v3_build_failed:{exc}"])
    v3_blockers = validate_content_evidence_packet_v3(packet)
    if v3_blockers:
        return _reject(result, [f"v3:{item}" for item in v3_blockers])
    if packet.get("v2_compatibility_projection") != dict(v2_packet):
        return _reject(result, ["v3_v2_projection_not_byte_preserved"])
    if list(packet.get("governed_claim_graph", {}).get("claims") or []) != [dict(row) for row in claims]:
        return _reject(result, ["v3_claim_substance_not_byte_preserved"])

    try:
        newsroom_pool = bridge["newsroom_pool"]
        lane_date = schedule_date or str(bridge.get("schedule_date") or "")
        lane_window = dict(window or bridge.get("window") or {})
        newsroom_lane = run_newsroom_lane(
            pool=newsroom_pool,
            schedule_date=lane_date,
            window=lane_window,
        )
        if str(newsroom_lane.get("selected_candidate_id")) != str(candidate.get("candidate_id")):
            raise DualLaneShadowError("newsroom_selected_candidate_not_bridge_candidate")
        capital_lane = run_capital_chronicle_lane(packet=packet)
        approved_ids = list(capital_lane.get("authorized_claim_ids") or [])
        claim_map = {
            str(row.get("claim_id")): row
            for row in packet.get("governed_claim_graph", {}).get("claims") or []
        }
        approved_statements = [
            str(claim_map[claim_id].get("statement") or "")
            for claim_id in approved_ids
            if claim_id in claim_map
        ]
        lead_statement = approved_statements[0] if approved_statements else "Governed Main analysis handoff"
        drafted = {
            "headline": lead_statement,
            "answer_first_summary": lead_statement,
            "body_sections": [
                {"heading": "Supplied Core claim", "text": "\n".join(approved_statements)},
                {
                    "heading": "Analytical fidelity",
                    "text": (
                        "The Main analytical substance is reproduced verbatim. ContentOps did not "
                        "recalculate, reinterpret, forecast, or create market-decision authority."
                    ),
                },
                {
                    "heading": "Context boundary",
                    "text": (
                        "BrowserOS and X rows remain qualitative context and are not promoted into "
                        "Core or publication authority."
                    ),
                },
            ],
            "claim_ids": approved_ids,
            "citations": list(capital_lane.get("citations") or []),
            "limitations": list(capital_lane.get("limitations") or []),
            "known_unknowns": [
                "An unresolved context contradiction remains quarantined.",
                "Publication and dispatch authority remain false.",
            ],
            "primary_intent": "what the supplied Main Core claim states",
            "secondary_intent": "how qualitative context is bounded",
            "story_type": "official_action",
        }
        package = build_package(
            package_id=f"pkg-main-handoff-{_hash(packet['packet_id'])[:16]}",
            lane="capital_chronicle",
            story_id=str(packet["packet_id"]),
            source_label="Main App Core Analyzer",
            authority_logical_hash=str(packet["logical_hash"]),
            internal_links=(),
            **drafted,
        )
        visual_assets = _mapping_rows(
            bridge.get("visual_assets"), field="visual_assets", blockers=blockers
        )
        if blockers:
            return _reject(result, blockers)
        visual_decision = evaluate_visual_composition(
            visual_assets,
            story_type="official_action",
            policy_context={"source": "MAIN_BRIDGE_FIXTURE", "network_call_made": False},
        )
        review_package_input = deepcopy(package)
        review_package_input["visual"] = {
            **dict(package.get("visual") or {}),
            "decision": visual_decision,
            "status": visual_decision["status"],
            "asset_count": visual_decision["asset_count"],
            "blockers": list(visual_decision.get("blockers") or []),
            "decision_hash": visual_decision["decision_hash"],
            "image_provenance": [dict(row) for row in visual_assets],
        }
        request = {
            "story_type": "official_action",
            "article_mode": "evidence_bound_shadow_draft",
            "workflow_mode": "evidence_bound_shadow_draft",
            "market_sensitive": False,
            "market_snapshot_required": False,
            "fresh_material_delta": False,
            "readiness_evaluation_basis": "HISTORICAL_POINT_IN_TIME_REPLAY",
        }
        from live_contentops.freshness_market_state_v2 import evaluate_freshness

        freshness = evaluate_freshness(packet, request)
        editorial_review = review_package(
            package=review_package_input,
            lane_result=capital_lane,
            evidence_packet=packet,
            request=request,
            freshness_decision=freshness,
        )
        derivatives = _build_derivative_shadow_rows(
            package=package,
            authority_hash=str(packet["logical_hash"]),
            claim_ids=approved_ids,
            citations=list(capital_lane.get("citations") or []),
            limitations=list(capital_lane.get("limitations") or []),
            visual_assets=visual_assets,
        )
        article = review_package_input["article"]
        article_hash = _hash(article)
        destination_readback = {
            "status": "CONFIRMED_SHADOW",
            "platform": "substack",
            "destination_kind": "canonical_substack_article",
            "destination_binding_id": "shadow:capitalchronicle.substack.com",
            "public_object_id": f"shadow-object:{packet['packet_id']}",
            "public_object_url": f"https://shadow.invalid/p/{packet['packet_id']}",
            "payload_sha256": article_hash,
            "readback_sha256": _hash({"article_hash": article_hash, "packet_hash": packet["logical_hash"]}),
            "reconciliation_status": "RECONCILED_CONFIRMED",
            "public_write_performed": False,
            "publication_authority": False,
        }
        scheduled = run_scheduled_shadow_production_day(
            enabled=True,
            source_recovery=bridge.get("source_recovery"),
            browser_preflight=bridge.get("browser_preflight"),
            x_ingestion=bridge.get("x_ingestion"),
            grounded_evidence={
                "status": "GROUNDED_EVIDENCE_READY",
                "evidence_ids": sorted(
                    str(value) for value in (bridge.get("provenance") or {}).get("evidence_refs") or []
                ),
                "claim_bindings_sha256": _hash(claims),
                "report_truth": "MAIN_PRODUCER_GOVERNED_HANDOFF",
            },
            candidate_decision={
                "status": "SELECTED",
                "candidate_id": candidate.get("candidate_id"),
                "decision_sha256": newsroom_lane.get("lane_logical_hash"),
            },
            canonical_article={
                "status": "QUALIFIED",
                "article_id": f"shadow-article:{packet['packet_id']}",
                "payload_sha256": article_hash,
                "epistemic_state": bridge.get("epistemic_state") or "PARTIALLY_CONFIRMED",
                "public_write_performed": False,
            },
            derivative_packages=derivatives,
            destination_readback=destination_readback,
            recovery_state=bridge.get("recovery_state"),
        )
    except (DualLaneShadowError, KeyError, TypeError, ValueError) as exc:
        return _reject(result, [f"shadow_composition_failed:{exc}"], status=STATUS_FAIL_CLOSED)

    if scheduled.get("status") != "SHADOW_CONFIRMED":
        return _reject(result, [f"scheduled_shadow:{scheduled.get('status')}:{scheduled.get('failure_detail')}"], status=STATUS_FAIL_CLOSED)
    result.update(
        {
            "status": STATUS_SHADOW_REVIEW_READY,
            "failure_detail": None,
            "validation_blockers": [],
            "input_packet_logical_hash": bridge.get("packet_logical_hash"),
            "v2_projection_sha256": _hash(v2_packet),
            "v3_packet_logical_hash": packet.get("logical_hash"),
            "producer_packet_identity": deepcopy(bridge.get("packet_identity")),
            "evidence_packet": packet,
            "claim_lineage": deepcopy(bridge.get("claim_lineage") or []),
            "contradictions": deepcopy(bridge.get("contradictions") or []),
            "claim_lineage_sha256": lineage_hash,
            "exact_core_claim_ids": exact_ids,
            "proxy_context_claim_ids": proxy_ids,
            "quarantined_claim_ids": quarantined,
            "frozen_v2_projection_preserved": True,
            "analytical_substance_preserved": True,
            "proxy_rows_qualitative_only": True,
            "core_claims_attributable": all(
                str(row.get("authority_origin")) == "MAIN_APP_CORE_ANALYZER"
                for row in claims
                if str(row.get("claim_scope")) == _EXACT_SCOPE
            ),
            "newsroom_lane": newsroom_lane,
            "capital_chronicle_lane": capital_lane,
            "package": package,
            "editorial_review": editorial_review,
            "scheduled_shadow": scheduled,
            "zero_live_action": {
                "scheduler_started": False,
                "durable_store_write_count": 0,
                "database_mutation": False,
                "model_call_count": 0,
                "provider_call_count": 0,
                "browser_action_count": 0,
                "public_write_performed": False,
                "publication_authority": False,
                "v2_activation": False,
            },
        }
    )
    return _finish(result)


__all__ = [
    "MAIN_PACKET_SCHEMA",
    "SCHEMA_VERSION",
    "STATUS_DISABLED_BY_DEFAULT",
    "STATUS_FAIL_CLOSED",
    "STATUS_REJECTED",
    "STATUS_SHADOW_REVIEW_READY",
    "consume_main_analysis_handoff_shadow",
]
