"""Fail-closed ContentOps use of publication-authorized Capital Chronicle material.

This module is deliberately a projection/validation seam, not an analytical engine.  It never
calculates, repairs, or widens upstream values or permissions.  Both V1 and V2 consume the same
lossless projection so the two lanes cannot drift into separate authority interpretations.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = "contentops.cc_publication_authority_resolution.v1"
PROJECTION_SCHEMA_VERSION = "contentops.cc_publication_authorized_projection.v1"

PUBLICATION_PACKET_AVAILABLE = "PUBLICATION_PACKET_AVAILABLE"
PUBLICATION_PACKET_NOT_AVAILABLE = "PUBLICATION_PACKET_NOT_AVAILABLE"
PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED = (
    "PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED"
)
PUBLICATION_PACKET_STALE_OR_BLOCKED = "PUBLICATION_PACKET_STALE_OR_BLOCKED"
CONTEXT_ONLY_AVAILABLE = "CONTEXT_ONLY_AVAILABLE"
NO_RELEVANT_CC_CONTEXT = "NO_RELEVANT_CC_CONTEXT"

PUBLICATION_AUTHORITY_CLASS = "CONTENTOPS_PUBLICATION_AUTHORIZED_CC"
INTERNAL_AUTHORITY_CLASS = "CORE_ANALYZER_GOVERNED_INTERNAL"
CONTEXT_AUTHORITY_CLASS = "CONTEXT_DISCOVERY_ONLY"

_SUPPORTED_BRIDGE_SCHEMAS = {"capital_chronicle_content_evidence_packet.v2"}
_STALE_OR_HEALTH_MARKERS = (
    "stale",
    "freshness",
    "source_health",
    "outside_story_window",
    "future",
)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
    ).hexdigest()


def _binding_blockers(
    packet: Mapping[str, Any], story_binding: Mapping[str, Any]
) -> list[str]:
    binding = packet.get("rolling_x_story_binding")
    if not isinstance(binding, Mapping):
        assignment = packet.get("publication_assignment")
        assignment = assignment if isinstance(assignment, Mapping) else {}
        expected_story_id = str(story_binding.get("story_id") or "")
        observed_story_id = str(
            assignment.get("duplicate_key")
            or assignment.get("story_id")
            or assignment.get("assignment_id")
            or ""
        )
        if expected_story_id and observed_story_id == expected_story_id:
            return []
        return ["CC_PUBLICATION_PACKET_STORY_BINDING_MISSING"]
    blockers: list[str] = []
    if str(binding.get("cluster_id") or "") != str(
        story_binding.get("cluster_id") or ""
    ):
        blockers.append("CC_PUBLICATION_PACKET_STORY_BINDING_MISMATCH:cluster_id")
    if [str(value) for value in (binding.get("headline_ids") or [])] != [
        str(value) for value in (story_binding.get("headline_ids") or [])
    ]:
        blockers.append("CC_PUBLICATION_PACKET_STORY_BINDING_MISMATCH:headline_ids")
    expected_hash = str(story_binding.get("request_logical_hash") or "")
    if expected_hash and str(binding.get("request_logical_hash") or "") != expected_hash:
        blockers.append("CC_PUBLICATION_PACKET_STORY_BINDING_MISMATCH:request_logical_hash")
    return blockers


def resolve_publication_authority(
    packet: Mapping[str, Any] | None,
    *,
    story_binding: Mapping[str, Any],
    intended_consumer: str = "contentops_publication",
    intended_use: str = "public_reporting",
    current_readiness_blockers: list[str] | None = None,
) -> dict[str, Any]:
    """Classify exact story/use authority without treating absence as a story veto."""
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION,
            "state": PUBLICATION_PACKET_NOT_AVAILABLE,
            "authority_class": CONTEXT_AUTHORITY_CLASS,
            "intended_consumer": intended_consumer,
            "intended_use": intended_use,
            "authorized": False,
            "packet_id": None,
            "packet_sha256": None,
            "reason_codes": ["NO_PUBLICATION_AUTHORIZED_CC_PACKET_FOR_STORY"],
            "ordinary_latest_web_article_may_continue": True,
            "llm_numeric_authority": False,
        }

    contract = packet.get("governed_contract")
    contract = contract if isinstance(contract, Mapping) else {}
    provenance = packet.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    publication_provenance = provenance.get("publication_packet")
    publication_provenance = (
        publication_provenance
        if isinstance(publication_provenance, Mapping)
        else {}
    )
    packet_hash = str(
        contract.get("upstream_packet_sha256")
        or publication_provenance.get("sha256")
        or packet.get("content_sha256")
        or ""
    ) or None
    reason_codes: list[str] = []
    mode = str(contract.get("mode") or "")
    if mode and mode != "story_scoped_publication_evidence_v1":
        reason_codes.append("CC_INTERNAL_ANALYZER_HANDOFF_NOT_PUBLICATION_AUTHORITY")
    if packet.get("schema_version") not in _SUPPORTED_BRIDGE_SCHEMAS:
        reason_codes.append("CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED")
    reason_codes.extend(_binding_blockers(packet, story_binding))

    permissions = packet.get("public_claim_permissions")
    permissions = permissions if isinstance(permissions, Mapping) else {}
    consumers = {str(value) for value in (permissions.get("consumer_class") or [])}
    if intended_consumer not in consumers:
        reason_codes.append("CC_PUBLICATION_PACKET_PERMISSION_BLOCKED:consumer")
    if (
        permissions.get("decision") != "ALLOW"
        or permissions.get("reporting_allowed") is not True
    ):
        reason_codes.append("CC_PUBLICATION_PACKET_PERMISSION_BLOCKED:reporting")
    if permissions.get("llm_numeric_authority") is not False:
        reason_codes.append("CC_PUBLICATION_PACKET_LLM_NUMERIC_AUTHORITY_INVALID")
    if packet.get("status") != "PASS_PUBLICATION_AUTHORIZED":
        reason_codes.append("CC_PUBLICATION_PACKET_PRESENT_NOT_AUTHORIZED")

    source_state = packet.get("source_state")
    source_state = source_state if isinstance(source_state, Mapping) else {}
    authority_state = " ".join(
        str(source_state.get(key) or "")
        for key in (
            "authority_class",
            "authority_state",
            "quality_state",
            "freshness_state",
            "source_health_status",
        )
    ).casefold()
    if source_state.get("candidate_snapshot_only") is True or "candidate" in authority_state:
        reason_codes.append("CC_CANDIDATE_ONLY_NOT_PUBLICATION_AUTHORITY")
    if "proxy" in authority_state:
        reason_codes.append("CC_PROXY_STATE_NOT_PUBLICATION_AUTHORITY")
    if "degraded" in authority_state:
        reason_codes.append("CC_DEGRADED_STATE_NOT_PUBLICATION_AUTHORITY")
    health = str(source_state.get("source_health_status") or "").upper()
    if health and health not in {"HEALTHY", "PASS", "READY", "FRESH"}:
        reason_codes.append("CC_PUBLICATION_PACKET_SOURCE_HEALTH_BLOCKED:" + health)

    packet_blockers = [str(value) for value in (packet.get("blockers") or [])]
    readiness_blockers = [str(value) for value in (current_readiness_blockers or [])]
    reason_codes.extend(packet_blockers)
    reason_codes.extend(readiness_blockers)
    reason_codes = list(dict.fromkeys(reason_codes))
    stale_or_health = any(
        marker in reason.casefold()
        for reason in [*packet_blockers, *readiness_blockers]
        for marker in _STALE_OR_HEALTH_MARKERS
    )
    authorized = not reason_codes
    state = (
        PUBLICATION_PACKET_AVAILABLE
        if authorized
        else PUBLICATION_PACKET_STALE_OR_BLOCKED
        if stale_or_health
        else PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "authority_class": (
            PUBLICATION_AUTHORITY_CLASS
            if authorized
            else INTERNAL_AUTHORITY_CLASS
            if mode and mode != "story_scoped_publication_evidence_v1"
            else CONTEXT_AUTHORITY_CLASS
        ),
        "intended_consumer": intended_consumer,
        "intended_use": intended_use,
        "authorized": authorized,
        "packet_id": packet.get("packet_id"),
        "upstream_packet_id": contract.get("upstream_packet_id"),
        "packet_sha256": packet_hash,
        "story_binding": dict(
            packet.get("rolling_x_story_binding")
            or packet.get("publication_assignment")
            or {}
        ),
        "reason_codes": reason_codes,
        "ordinary_latest_web_article_may_continue": not authorized,
        "llm_numeric_authority": False,
    }


def build_publication_authorized_projection(
    packet: Mapping[str, Any], resolution: Mapping[str, Any]
) -> dict[str, Any]:
    """Copy exact permitted upstream structures; never derive a new value."""
    if resolution.get("state") != PUBLICATION_PACKET_AVAILABLE:
        raise ValueError("publication_authorized_cc_projection_requires_authority")
    permissions = dict(packet.get("public_claim_permissions") or {})
    if permissions.get("llm_numeric_authority") is not False:
        raise ValueError("publication_authorized_cc_projection_llm_authority_invalid")
    has_numeric_material = bool(
        packet.get("numeric_claims")
        or packet.get("time_series")
        or packet.get("candidate_visual_inputs")
    )
    if has_numeric_material and permissions.get("numeric_claims_allowed") is not True:
        raise ValueError("publication_authorized_cc_projection_numeric_permission_missing")
    claims = [
        dict(row)
        for row in (packet.get("numeric_claims") or [])
        if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
    ]
    if any(row.get("llm_numeric_authority") is not False for row in claims):
        raise ValueError("publication_authorized_cc_projection_claim_authority_invalid")
    chart_inputs = [
        dict(row)
        for row in (packet.get("candidate_visual_inputs") or [])
        if isinstance(row, Mapping)
        and row.get("public_claim_allowed") is True
        and row.get("public_display_allowed") is not False
    ]
    core = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "authority_class": PUBLICATION_AUTHORITY_CLASS,
        "upstream_packet_id": resolution.get("upstream_packet_id")
        or packet.get("packet_id"),
        "upstream_packet_sha256": resolution.get("packet_sha256"),
        "story_binding": dict(
            packet.get("rolling_x_story_binding")
            or packet.get("publication_assignment")
            or {}
        ),
        "consumer_binding": list(permissions.get("consumer_class") or []),
        "permitted_use": resolution.get("intended_use"),
        "packet_schema_version": packet.get("schema_version"),
        "packet_fingerprint": resolution.get("packet_sha256"),
        "known_at_utc": packet.get("generated_at_utc"),
        "as_of_utc": packet.get("as_of_utc"),
        "story_window": dict(packet.get("story_window") or {}),
        "exact_numeric_claims": claims,
        "exact_time_series": dict(packet.get("time_series") or {}),
        "time_series_references": list(packet.get("time_series_references") or []),
        "exact_chart_inputs": chart_inputs,
        "market_snapshots": [
            dict(row)
            for row in (packet.get("market_snapshots") or [])
            if isinstance(row, Mapping)
        ],
        "calculation_identities": [
            {
                key: row.get(key)
                for key in (
                    "claim_id",
                    "series_id",
                    "calculation_id",
                    "metric",
                    "unit",
                    "transformation",
                    "observation_time_utc",
                    "release_time_utc",
                    "revision_time_utc",
                    "known_at_utc",
                    "state",
                    "observed_forecast_scenario_state",
                )
                if key in row
            }
            for row in claims
        ],
        "citation_map": dict(packet.get("citation_map") or {}),
        "provenance": dict(packet.get("provenance") or {}),
        "source_state": dict(packet.get("source_state") or {}),
        "public_display_permission": {
            "decision": permissions.get("decision"),
            "reporting_allowed": permissions.get("reporting_allowed"),
            "numeric_claims_allowed": permissions.get("numeric_claims_allowed"),
        },
        "limitations": list(packet.get("limitations") or []),
        "blockers": [],
        "values_regenerated_or_repaired": False,
        "llm_numeric_authority": False,
    }
    return {**core, "projection_fingerprint": _hash(core)}


def validate_projection_for_consumer(
    projection: Mapping[str, Any], *, consumer: str
) -> list[str]:
    blockers: list[str] = []
    if projection.get("schema_version") != PROJECTION_SCHEMA_VERSION:
        blockers.append("cc_projection_schema_incompatible")
    expected = _hash(
        {key: value for key, value in projection.items() if key != "projection_fingerprint"}
    )
    if projection.get("projection_fingerprint") != expected:
        blockers.append("cc_projection_fingerprint_mismatch")
    if consumer not in {"v1_article", "v2_media"}:
        blockers.append("cc_projection_consumer_unsupported")
    if projection.get("authority_class") != PUBLICATION_AUTHORITY_CLASS:
        blockers.append("cc_projection_authority_class_invalid")
    if projection.get("llm_numeric_authority") is not False:
        blockers.append("cc_projection_llm_numeric_authority_invalid")
    if projection.get("values_regenerated_or_repaired") is not False:
        blockers.append("cc_projection_value_regeneration_forbidden")
    return blockers
