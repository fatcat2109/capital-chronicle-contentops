"""Universal, capability-driven news candidate and assignment contracts.

This module is deterministic and domain-neutral.  It contains no provider,
network, credential, browser, publication, dispatch, or policy-mutation code.
Source-specific extraction belongs in adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


POOL_SCHEMA = "contentops.universal_news_candidate_pool.v2"
CANDIDATE_SCHEMA = "contentops.universal_news_candidate.v2"
CLAIM_SCHEMA = "contentops.universal_news_claim.v2"
CLAIM_REGISTRY_VERSION = "contentops.universal_claim_capabilities.v2.0.0"
PROFILE_REGISTRY_VERSION = "contentops.evidence_requirement_profiles.v2.0.0"
SOURCE_FAMILY_REGISTRY_VERSION = "contentops.source_family_registry.v2.0.0"
ASSIGNMENT_SCHEMA = "contentops.cross_domain_five_window_assignment.v1"
UNCALIBRATED_STATE = "UNCALIBRATED_FOUNDATION"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]*$")
REPORTING_PERMISSIONS = frozenset({"REPORTING_ALLOWED", "PUBLIC_CLAIM_ALLOWED"})
KNOWN_PERMISSIONS = frozenset({
    *REPORTING_PERMISSIONS,
    "CONTEXT_ONLY",
    "REPORTING_NOT_ALLOWED",
    "PERMISSION_BLOCKED",
    "UNAVAILABLE",
})
KNOWN_AUTHORITIES = frozenset({
    "VERIFIED_GOVERNED",
    "OFFICIAL_VERIFIED",
    "FIRST_PARTY_VERIFIED",
    "CONTEXT_ONLY",
    "UNVERIFIED",
    "BLOCKED",
    "UNAVAILABLE",
})
AUTHORITY_RANK = {
    "UNAVAILABLE": 0,
    "UNVERIFIED": 0,
    "BLOCKED": 0,
    "CONTEXT_ONLY": 1,
    "VERIFIED_GOVERNED": 2,
    "OFFICIAL_VERIFIED": 2,
    "FIRST_PARTY_VERIFIED": 2,
}
PERMISSION_RANK = {
    "UNAVAILABLE": 0,
    "PERMISSION_BLOCKED": 0,
    "REPORTING_NOT_ALLOWED": 0,
    "CONTEXT_ONLY": 1,
    "REPORTING_ALLOWED": 2,
    "PUBLIC_CLAIM_ALLOWED": 3,
}
RELATIONSHIPS = frozenset({
    "initial_event",
    "duplicate",
    "incremental_update",
    "material_update",
    "confirmation",
    "contradiction",
    "correction",
    "new_phase",
})
AVAILABILITY_STATES = frozenset({"AVAILABLE", "EXPLICIT_ZERO", "UNAVAILABLE"})
RANKING_DIMENSIONS = (
    "materiality",
    "policy_economic_geopolitical_significance",
    "surprise",
    "affected_market_economy_breadth",
    "source_authority",
    "freshness",
    "evidence_completeness",
    "audience_relevance",
    "novelty",
    "durability",
    "original_analysis_potential",
    "visual_feasibility",
    "overclaiming_risk",
    "portfolio_diversity",
)


@dataclass(frozen=True)
class ClaimCapabilityV2:
    claim_type: str
    structured_payload_allowed: bool
    statement_allowed: bool
    numeric_fields_required: bool = False
    separate_market_evidence_required: bool = False
    judgment_record_required: bool = False


@dataclass(frozen=True)
class EvidenceRequirementProfileV2:
    profile_id: str
    accepted_claim_types: tuple[str, ...]
    numeric_claim_required: bool
    required_candidate_fields: tuple[str, ...]
    required_claim_fields: tuple[str, ...]


CLAIM_CAPABILITIES: Mapping[str, ClaimCapabilityV2] = {
    row.claim_type: row
    for row in (
        ClaimCapabilityV2("numeric_observation", True, True, numeric_fields_required=True),
        ClaimCapabilityV2("factual_text", True, True),
        ClaimCapabilityV2("official_action", True, True),
        ClaimCapabilityV2("event_occurrence", True, True),
        ClaimCapabilityV2("legal_or_regulatory_action", True, True),
        ClaimCapabilityV2("corporate_filing_fact", True, True),
        ClaimCapabilityV2("entity_relationship", True, True),
        ClaimCapabilityV2("market_reaction", True, True, separate_market_evidence_required=True),
        ClaimCapabilityV2("correction_or_revision", True, True),
        ClaimCapabilityV2("model_assisted_judgment", True, True, judgment_record_required=True),
    )
}

EVIDENCE_REQUIREMENT_PROFILES: Mapping[str, EvidenceRequirementProfileV2] = {
    row.profile_id: row
    for row in (
        EvidenceRequirementProfileV2(
            "numeric_economic_release",
            ("numeric_observation", "correction_or_revision"),
            True,
            ("observation_time_utc", "published_at_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
        EvidenceRequirementProfileV2(
            "official_action",
            ("official_action", "legal_or_regulatory_action", "factual_text", "correction_or_revision"),
            False,
            ("event_time_utc", "published_at_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
        EvidenceRequirementProfileV2(
            "corporate_filing",
            ("corporate_filing_fact", "factual_text", "correction_or_revision"),
            False,
            ("published_at_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
        EvidenceRequirementProfileV2(
            "geopolitical_or_sanctions",
            ("official_action", "event_occurrence", "entity_relationship", "factual_text", "correction_or_revision"),
            False,
            ("event_time_utc", "published_at_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
        EvidenceRequirementProfileV2(
            "physical_disruption",
            ("event_occurrence", "factual_text", "correction_or_revision"),
            False,
            ("event_time_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
        EvidenceRequirementProfileV2(
            "market_reaction",
            ("market_reaction", "correction_or_revision"),
            False,
            ("observation_time_utc", "known_at_utc"),
            ("source_document_ids", "evidence_refs", "citations"),
        ),
    )
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def logical_hash(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def _without_hash(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "logical_hash"}


def parse_utc(value: str, *, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(f"{field_name}_invalid") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def build_claim(
    *,
    claim_id: str,
    claim_type: str,
    statement: str | None,
    structured_payload: Mapping[str, Any] | None,
    source_document_ids: Sequence[str],
    evidence_refs: Sequence[str],
    authority_class: str,
    permission_state: str,
    known_at_utc: str,
    citations: Sequence[Mapping[str, Any]],
    observed_at_utc: str | None = None,
    event_time_utc: str | None = None,
    published_at_utc: str | None = None,
    revision_at_utc: str | None = None,
    entities: Sequence[str] = (),
    geographies: Sequence[str] = (),
    limitations: Sequence[str] = (),
    numeric: Mapping[str, Any] | None = None,
    market_evidence_refs: Sequence[str] = (),
    judgment_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "schema_version": CLAIM_SCHEMA,
        "claim_id": claim_id,
        "claim_type": claim_type,
        "statement": statement,
        "structured_payload": dict(structured_payload or {}),
        "source_document_ids": list(source_document_ids),
        "evidence_refs": list(evidence_refs),
        "authority_class": authority_class,
        "permission_state": permission_state,
        "observed_at_utc": observed_at_utc,
        "event_time_utc": event_time_utc,
        "published_at_utc": published_at_utc,
        "known_at_utc": known_at_utc,
        "revision_at_utc": revision_at_utc,
        "entities": list(entities),
        "geographies": list(geographies),
        "citations": [dict(row) for row in citations],
        "limitations": list(limitations),
        "numeric": dict(numeric) if numeric is not None else None,
        "market_evidence_refs": list(market_evidence_refs),
        "judgment_record": dict(judgment_record) if judgment_record is not None else None,
    }
    values["logical_hash"] = logical_hash(values)
    return values


def validate_claim(
    claim: Mapping[str, Any],
    *,
    cutoff_utc: str,
    registry: Mapping[str, ClaimCapabilityV2] = CLAIM_CAPABILITIES,
) -> list[str]:
    blockers: list[str] = []
    if claim.get("schema_version") != CLAIM_SCHEMA:
        blockers.append("claim_schema_invalid")
    claim_id = str(claim.get("claim_id") or "")
    if not IDENTIFIER_RE.fullmatch(claim_id):
        blockers.append("claim_id_invalid")
    capability = registry.get(str(claim.get("claim_type") or ""))
    if capability is None:
        blockers.append("claim_type_not_registered")
    statement = claim.get("statement")
    payload = claim.get("structured_payload")
    if not statement and not payload:
        blockers.append("claim_statement_or_payload_missing")
    if statement is not None and not isinstance(statement, str):
        blockers.append("claim_statement_invalid")
    if payload is not None and not isinstance(payload, Mapping):
        blockers.append("claim_structured_payload_invalid")
    for field in ("source_document_ids", "evidence_refs", "citations"):
        value = claim.get(field)
        if not isinstance(value, list) or not value:
            blockers.append(f"claim_{field}_missing")
    refs = claim.get("evidence_refs") or []
    if len(refs) != len(set(refs)):
        blockers.append("claim_evidence_refs_duplicate")
    if claim.get("authority_class") not in KNOWN_AUTHORITIES:
        blockers.append("claim_authority_class_invalid")
    if claim.get("permission_state") not in KNOWN_PERMISSIONS:
        blockers.append("claim_permission_state_invalid")
    try:
        cutoff = parse_utc(cutoff_utc, field_name="cutoff_utc")
    except ValueError as error:
        blockers.append(str(error))
        cutoff = None
    for field in (
        "observed_at_utc",
        "event_time_utc",
        "published_at_utc",
        "known_at_utc",
        "revision_at_utc",
    ):
        value = claim.get(field)
        if value is None:
            continue
        try:
            parsed = parse_utc(str(value), field_name=f"claim_{field}")
        except ValueError as error:
            blockers.append(str(error))
        else:
            if cutoff is not None and parsed > cutoff:
                blockers.append(f"claim_{field}_after_cutoff")
    if claim.get("known_at_utc") is None:
        blockers.append("claim_known_at_utc_missing")
    if capability is not None and capability.numeric_fields_required:
        numeric = claim.get("numeric")
        if not isinstance(numeric, Mapping):
            blockers.append("numeric_claim_payload_missing")
        else:
            for field in ("metric", "value", "unit", "transformation", "numeric_authority_class"):
                if numeric.get(field) is None or numeric.get(field) == "":
                    blockers.append(f"numeric_claim_{field}_missing")
    if capability is not None and capability.separate_market_evidence_required:
        market_refs = claim.get("market_evidence_refs") or []
        if not market_refs:
            blockers.append("market_reaction_separate_evidence_missing")
        elif not set(market_refs).issubset(set(refs)):
            blockers.append("market_reaction_evidence_not_in_claim_lineage")
        payload = claim.get("structured_payload") or {}
        for field in ("instrument_id", "observation_time_utc", "evidence_relationship"):
            if not payload.get(field):
                blockers.append(f"market_reaction_{field}_missing")
    if capability is not None and capability.judgment_record_required:
        judgment = claim.get("judgment_record")
        if not isinstance(judgment, Mapping):
            blockers.append("model_judgment_record_missing")
        else:
            expected = logical_hash(_without_hash(judgment))
            if judgment.get("logical_hash") != expected:
                blockers.append("model_judgment_record_hash_invalid")
            if not judgment.get("evidence_refs"):
                blockers.append("model_judgment_evidence_missing")
    if not SHA256_RE.fullmatch(str(claim.get("logical_hash") or "")):
        blockers.append("claim_logical_hash_invalid")
    elif claim["logical_hash"] != logical_hash(_without_hash(claim)):
        blockers.append("claim_logical_hash_mismatch")
    return sorted(set(blockers))


def build_candidate(values: Mapping[str, Any]) -> dict[str, Any]:
    candidate = dict(values)
    candidate.setdefault("schema_version", CANDIDATE_SCHEMA)
    candidate.setdefault("publication_authority", False)
    candidate.setdefault("public_write_allowed", False)
    candidate.setdefault("global_dqr_override", False)
    candidate.setdefault("numeric_claims", [
        claim for claim in candidate.get("claims", [])
        if claim.get("claim_type") == "numeric_observation"
    ])
    candidate["logical_hash"] = logical_hash(_without_hash(candidate))
    return candidate


def validate_candidate(
    candidate: Mapping[str, Any],
    *,
    cutoff_utc: str,
    source_family_registry: Mapping[str, Mapping[str, Any]],
    claim_registry: Mapping[str, ClaimCapabilityV2] = CLAIM_CAPABILITIES,
    profile_registry: Mapping[str, EvidenceRequirementProfileV2] = EVIDENCE_REQUIREMENT_PROFILES,
) -> list[str]:
    blockers: list[str] = []
    if candidate.get("schema_version") != CANDIDATE_SCHEMA:
        blockers.append("candidate_schema_invalid")
    for field in ("candidate_id", "story_id", "cluster_id", "update_chain_id"):
        if not IDENTIFIER_RE.fullmatch(str(candidate.get(field) or "")):
            blockers.append(f"{field}_invalid")
    source_families = candidate.get("source_family_ids") or []
    if not source_families:
        blockers.append("source_family_ids_missing")
    for family_id in source_families:
        record = source_family_registry.get(str(family_id))
        if not record or record.get("enabled") is not True:
            blockers.append(f"source_family_not_registered:{family_id}")
    profile = profile_registry.get(str(candidate.get("evidence_requirement_profile_id") or ""))
    if profile is None:
        blockers.append("evidence_requirement_profile_not_registered")
    claims = candidate.get("claims")
    if not isinstance(claims, list) or not claims:
        blockers.append("candidate_claims_missing")
        claims = []
    for claim in claims:
        blockers.extend(
            f"{claim.get('claim_id') or 'unknown'}:{value}"
            for value in validate_claim(claim, cutoff_utc=cutoff_utc, registry=claim_registry)
        )
    claim_ids = [str(claim.get("claim_id") or "") for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        blockers.append("candidate_claim_ids_duplicate")
    if profile is not None:
        present_types = {str(claim.get("claim_type") or "") for claim in claims}
        if not present_types.intersection(profile.accepted_claim_types):
            blockers.append("candidate_profile_claim_capability_missing")
        if profile.numeric_claim_required and "numeric_observation" not in present_types:
            blockers.append("candidate_numeric_claim_required")
        for field in profile.required_candidate_fields:
            if not candidate.get(field):
                blockers.append(f"candidate_profile_{field}_missing")
    projected_numeric = candidate.get("numeric_claims") or []
    actual_numeric = [claim for claim in claims if claim.get("claim_type") == "numeric_observation"]
    if [row.get("logical_hash") for row in projected_numeric] != [row.get("logical_hash") for row in actual_numeric]:
        blockers.append("numeric_claims_compatibility_projection_mismatch")
    if candidate.get("relationship") not in RELATIONSHIPS:
        blockers.append("candidate_relationship_invalid")
    try:
        cutoff = parse_utc(cutoff_utc, field_name="cutoff_utc")
    except ValueError as error:
        blockers.append(str(error))
        cutoff = None
    for field in (
        "event_time_utc",
        "observation_time_utc",
        "published_at_utc",
        "known_at_utc",
        "revision_at_utc",
    ):
        value = candidate.get(field)
        if value is None:
            continue
        try:
            parsed = parse_utc(str(value), field_name=f"candidate_{field}")
        except ValueError as error:
            blockers.append(str(error))
        else:
            if cutoff is not None and parsed > cutoff:
                blockers.append(f"candidate_{field}_after_cutoff")
    if not candidate.get("known_at_utc"):
        blockers.append("candidate_known_at_utc_missing")
    candidate_refs = set(candidate.get("evidence_refs") or [])
    claim_refs = {ref for claim in claims for ref in (claim.get("evidence_refs") or [])}
    if candidate_refs != claim_refs:
        blockers.append("candidate_evidence_lineage_not_exact_claim_union")
    permissions = {str(claim.get("permission_state") or "") for claim in claims}
    if candidate.get("reporting_allowed") is True and not permissions.issubset(REPORTING_PERMISSIONS):
        blockers.append("candidate_reporting_permission_upgrade")
    claim_authority_ranks = [
        AUTHORITY_RANK.get(str(claim.get("authority_class") or ""), -1)
        for claim in claims
    ]
    candidate_authority_rank = AUTHORITY_RANK.get(
        str(candidate.get("authority_state") or ""), -1
    )
    if (
        claim_authority_ranks
        and candidate_authority_rank > min(claim_authority_ranks)
    ):
        blockers.append("candidate_authority_upgrade")
    family_records = [
        source_family_registry.get(str(family_id))
        for family_id in source_families
        if source_family_registry.get(str(family_id))
    ]
    family_authority_ceiling = min(
        (
            AUTHORITY_RANK.get(str(row.get("authority_class") or ""), -1)
            for row in family_records
        ),
        default=-1,
    )
    family_permission_ceiling = min(
        (
            PERMISSION_RANK.get(str(row.get("permission_ceiling") or ""), -1)
            for row in family_records
        ),
        default=-1,
    )
    if family_records and candidate_authority_rank > family_authority_ceiling:
        blockers.append("candidate_authority_exceeds_source_family_ceiling")
    if family_records and any(
        PERMISSION_RANK.get(str(claim.get("permission_state") or ""), -1)
        > family_permission_ceiling
        for claim in claims
    ):
        blockers.append("claim_permission_exceeds_source_family_ceiling")
    if candidate.get("publication_authority") is not False:
        blockers.append("candidate_publication_authority_forbidden")
    if candidate.get("public_write_allowed") is not False:
        blockers.append("candidate_public_write_forbidden")
    if candidate.get("global_dqr_override") is not False:
        blockers.append("candidate_global_dqr_override_forbidden")
    if not SHA256_RE.fullmatch(str(candidate.get("logical_hash") or "")):
        blockers.append("candidate_logical_hash_invalid")
    elif candidate["logical_hash"] != logical_hash(_without_hash(candidate)):
        blockers.append("candidate_logical_hash_mismatch")
    return sorted(set(blockers))


def adapt_v1_candidate(
    candidate: Mapping[str, Any],
    *,
    source_family_id: str,
) -> dict[str, Any]:
    claims = []
    source_documents = list(candidate.get("source_documents") or [])
    document_ids = [str(row.get("document_id") or "") for row in source_documents if row.get("document_id")]
    for row in candidate.get("numeric_claims") or []:
        claim_id = str(row.get("claim_id") or "")
        citations = [
            {"url": url, "source_document_id": document_ids[0] if document_ids else None}
            for url in (candidate.get("citation_map") or {}).get(claim_id, [])
        ]
        claims.append(build_claim(
            claim_id=claim_id,
            claim_type="numeric_observation",
            statement=None,
            structured_payload={"source_native_claim_id": claim_id},
            source_document_ids=document_ids,
            evidence_refs=[f"v1:{candidate.get('evidence_hash')}:{claim_id}"],
            authority_class="OFFICIAL_VERIFIED",
            permission_state="PUBLIC_CLAIM_ALLOWED" if row.get("public_claim_allowed") is True else "REPORTING_NOT_ALLOWED",
            observed_at_utc=row.get("observation_time_utc"),
            published_at_utc=row.get("observation_time_utc"),
            known_at_utc=str(row.get("known_at_utc") or candidate.get("known_at_utc")),
            citations=citations,
            entities=(),
            geographies=(),
            limitations=[str(row.get("authority_scope") or "v1_numeric_compatibility_projection")],
            numeric={
                "metric": row.get("metric"),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "transformation": row.get("calculation") or "source_native_value",
                "numeric_authority_class": row.get("source_authority"),
            },
        ))
    evidence_refs = sorted({ref for claim in claims for ref in claim["evidence_refs"]})
    values = {
        "candidate_id": str(candidate["candidate_id"]),
        "story_id": str(candidate["story_id"]),
        "cluster_id": str(candidate["cluster_id"]),
        "update_chain_id": str(candidate["update_chain_id"]),
        "source_native_ids": [str(candidate.get("source_packet_id"))],
        "source_family_ids": [source_family_id],
        "evidence_requirement_profile_id": "numeric_economic_release",
        "capabilities": {
            "claim_capabilities": ["numeric_observation"],
            "numeric_evidence_required": True,
            "nonnumeric_evidence_supported": False,
        },
        "title": candidate.get("title"),
        "summary": candidate.get("summary"),
        "relationship": "initial_event" if candidate.get("relationship") == "new_phase" else candidate.get("relationship"),
        "claims": claims,
        "source_documents": source_documents,
        "entities": [],
        "geographies": [],
        "evidence_refs": evidence_refs,
        "authority_state": "OFFICIAL_VERIFIED",
        "reporting_allowed": (candidate.get("claim_permissions") or {}).get("reporting_allowed") is True,
        "evidence_state": candidate.get("evidence_class"),
        "event_time_utc": candidate.get("event_time_utc"),
        "observation_time_utc": candidate.get("event_time_utc"),
        "published_at_utc": candidate.get("event_time_utc"),
        "known_at_utc": candidate.get("known_at_utc"),
        "revision_at_utc": None,
        "cutoff_time_utc": None,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": ["v1_exact_claim_document_citation_projection_complete"],
        },
        "freshness": candidate.get("freshness") or {"availability": "UNAVAILABLE", "value": None},
        "ranking_inputs": candidate.get("ranking_inputs") or {},
        "limitations": _unique([
            *(str(value) for value in candidate.get("limitations") or []),
            "v1_compatibility_adapter_preserves_numeric_claims_projection",
            "candidate_contract_grants_no_publication_authority",
        ]),
        "blockers": list(candidate.get("blockers") or []),
        "publication_authority": False,
        "public_write_allowed": False,
        "global_dqr_override": False,
        "producer_binding": candidate.get("producer_binding"),
    }
    return build_candidate(values)


def classify_update_relationship(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any],
) -> str:
    if previous is None:
        return "initial_event"
    signals = current.get("delta_signals") or {}
    for signal, relationship in (
        ("correction", "correction"),
        ("contradiction", "contradiction"),
        ("confirmation", "confirmation"),
        ("new_phase", "new_phase"),
        ("material_delta", "material_update"),
    ):
        if signals.get(signal) is True:
            return relationship
    previous_hashes = {str(row.get("logical_hash")) for row in previous.get("claims") or []}
    current_hashes = {str(row.get("logical_hash")) for row in current.get("claims") or []}
    if previous_hashes == current_hashes:
        return "duplicate"
    if previous_hashes.issubset(current_hashes):
        return "incremental_update"
    return "incremental_update"


def assign_generic_id(prefix: str, material: Mapping[str, Any]) -> str:
    return f"{prefix}-{logical_hash(material)[:20]}"


def cluster_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for candidate in candidates:
        identity = {
            "source_native_ids": sorted(candidate.get("source_native_ids") or []),
            "entities": sorted(candidate.get("entities") or []),
            "geographies": sorted(candidate.get("geographies") or []),
            "profile": candidate.get("evidence_requirement_profile_id"),
            "claim_types": sorted(
                str(row.get("claim_type"))
                for row in candidate.get("claims") or []
                if row.get("claim_type")
            ),
            "time_bucket": str(
                candidate.get("event_time_utc")
                or candidate.get("observation_time_utc")
                or candidate.get("published_at_utc")
                or ""
            )[:10],
            "source_document_ids": sorted(
                str(row.get("document_id"))
                for row in candidate.get("source_documents") or []
                if row.get("document_id")
            ),
        }
        key = logical_hash(identity)
        groups.setdefault(key, []).append(candidate)
    clusters = []
    for key, rows in sorted(groups.items()):
        ordered = sorted(rows, key=lambda row: (
            str(row.get("known_at_utc") or ""),
            str(row.get("candidate_id") or ""),
        ))
        declared_clusters = {str(row.get("cluster_id")) for row in ordered if row.get("cluster_id")}
        declared_stories = {str(row.get("story_id")) for row in ordered if row.get("story_id")}
        declared_chains = {
            str(row.get("update_chain_id")) for row in ordered if row.get("update_chain_id")
        }
        relationships = []
        previous = None
        for row in ordered:
            relationships.append({
                "candidate_id": row["candidate_id"],
                "previous_candidate_id": previous["candidate_id"] if previous else None,
                "relationship": classify_update_relationship(previous, row),
            })
            previous = row
        clusters.append({
            "cluster_id": (
                next(iter(declared_clusters)) if len(declared_clusters) == 1
                else assign_generic_id("cc-cluster", {"identity_hash": key})
            ),
            "story_id": (
                next(iter(declared_stories)) if len(declared_stories) == 1
                else assign_generic_id("cc-story", {"identity_hash": key})
            ),
            "update_chain_id": (
                next(iter(declared_chains)) if len(declared_chains) == 1
                else assign_generic_id("cc-update-chain", {"identity_hash": key})
            ),
            "candidate_ids": [row["candidate_id"] for row in ordered],
            "relationships": relationships,
            "identity_hash": key,
        })
    return clusters


def validate_ranking_input(name: str, row: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if name not in RANKING_DIMENSIONS:
        blockers.append(f"unknown_ranking_dimension:{name}")
    availability = row.get("availability")
    if availability not in AVAILABILITY_STATES:
        blockers.append(f"ranking_availability_invalid:{name}")
    value = row.get("score")
    if availability == "UNAVAILABLE" and value is not None:
        blockers.append(f"unavailable_ranking_dimension_has_value:{name}")
    if availability in {"AVAILABLE", "EXPLICIT_ZERO"}:
        if not isinstance(value, (int, float)):
            blockers.append(f"available_ranking_dimension_value_missing:{name}")
        elif not 0.0 <= float(value) <= 100.0:
            blockers.append(f"ranking_dimension_out_of_range:{name}")
    if availability == "EXPLICIT_ZERO" and value != 0:
        blockers.append(f"explicit_zero_ranking_dimension_nonzero:{name}")
    judgment = row.get("model_assisted_judgment")
    if judgment is not None:
        if not isinstance(judgment, Mapping):
            blockers.append(f"model_judgment_invalid:{name}")
        elif judgment.get("logical_hash") != logical_hash(_without_hash(judgment)):
            blockers.append(f"model_judgment_hash_invalid:{name}")
        elif not judgment.get("evidence_refs"):
            blockers.append(f"model_judgment_evidence_missing:{name}")
    return blockers


def score_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    inputs = candidate.get("ranking_inputs") or {}
    blockers = [
        blocker
        for name, row in inputs.items()
        for blocker in validate_ranking_input(str(name), row if isinstance(row, Mapping) else {})
    ]
    candidate_evidence_refs = set(candidate.get("evidence_refs") or [])
    for name, row in inputs.items():
        if not isinstance(row, Mapping):
            continue
        judgment = row.get("model_assisted_judgment")
        if isinstance(judgment, Mapping) and not set(
            judgment.get("evidence_refs") or []
        ).issubset(candidate_evidence_refs):
            blockers.append(f"model_judgment_evidence_not_bound:{name}")
    dimensions: dict[str, dict[str, Any]] = {}
    for name in RANKING_DIMENSIONS:
        row = inputs.get(name)
        if not isinstance(row, Mapping):
            dimensions[name] = {
                "availability": "UNAVAILABLE",
                "score": None,
                "reason_codes": ["no_governed_ranking_input"],
                "evidence_refs": [],
            }
        else:
            dimensions[name] = {
                "availability": row.get("availability"),
                "score": row.get("score"),
                "reason_codes": list(row.get("reason_codes") or []),
                "evidence_refs": list(row.get("evidence_refs") or []),
            }
    measured = [
        float(row["score"])
        for row in dimensions.values()
        if row["availability"] in {"AVAILABLE", "EXPLICIT_ZERO"} and row["score"] is not None
    ]
    return {
        "calibration_state": UNCALIBRATED_STATE,
        "dimensions": dimensions,
        "score": round(sum(measured) / len(measured), 8) if measured else None,
        "available_dimension_count": len(measured),
        "unavailable_dimension_count": len(dimensions) - len(measured),
        "blockers": sorted(set(blockers)),
    }


def breaking_qualification(candidate: Mapping[str, Any]) -> dict[str, Any]:
    evidence_ref = candidate.get("breaking_event_evidence_ref")
    checks = {
        "governed_event_or_material_update": (
            candidate.get("relationship") in {"initial_event", "material_update"}
        ),
        "evidence_ref_bound_to_candidate": bool(
            evidence_ref and evidence_ref in set(candidate.get("evidence_refs") or [])
        ),
        "authority_ready": candidate.get("authority_state") in {
            "VERIFIED_GOVERNED",
            "OFFICIAL_VERIFIED",
            "FIRST_PARTY_VERIFIED",
        },
        "reporting_allowed": candidate.get("reporting_allowed") is True,
        "deterministic_materiality_available": (
            ((candidate.get("ranking_inputs") or {}).get("materiality") or {}).get(
                "availability"
            )
            in {"AVAILABLE", "EXPLICIT_ZERO"}
        ),
    }
    return {
        "qualified": all(checks.values()),
        "checks": checks,
        "publication_authority": False,
    }


def candidate_hard_gate(
    candidate: Mapping[str, Any],
    *,
    cutoff_utc: str,
    source_family_registry: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    blockers = list(candidate.get("blockers") or [])
    blockers.extend(validate_candidate(
        candidate,
        cutoff_utc=cutoff_utc,
        source_family_registry=source_family_registry,
    ))
    if candidate.get("reporting_allowed") is not True:
        blockers.append("reporting_permission_not_granted")
    if candidate.get("evidence_state") not in {"exact", "proxy"}:
        blockers.append("evidence_state_not_reporting_eligible")
    if candidate.get("relationship") == "duplicate":
        blockers.append("duplicate_no_new_delta")
    if candidate.get("relationship") == "incremental_update":
        blockers.append("incremental_update_not_material")
    ranking = score_candidate(candidate)
    blockers.extend(ranking["blockers"])
    return sorted(set(blockers))


def evaluate_v2_window_decision(
    *,
    window: Mapping[str, Any],
    schedule_date: str,
    pool: Mapping[str, Any],
    previously_assigned: Sequence[Mapping[str, Any]],
    no_publication_boundary: bool = True,
) -> dict[str, Any]:
    if pool.get("schema_version") != POOL_SCHEMA:
        raise ValueError("unsupported_universal_candidate_pool_schema")
    cutoff = datetime.combine(
        datetime.strptime(schedule_date, "%Y-%m-%d").date(),
        time.fromisoformat(str(window["target_cutoff_utc"])),
        tzinfo=timezone.utc,
    )
    cutoff_utc = cutoff.isoformat().replace("+00:00", "Z")
    registry = {
        str(row["source_family_id"]): row
        for row in (pool.get("source_family_registry") or {}).get("records") or []
    }
    rows = []
    held = []
    prior_clusters = {row.get("cluster_id") for row in previously_assigned}
    prior_chains = {row.get("update_chain_id") for row in previously_assigned}
    for candidate in pool.get("candidates") or []:
        blockers = candidate_hard_gate(
            candidate,
            cutoff_utc=cutoff_utc,
            source_family_registry=registry,
        )
    cluster_by_candidate = {
        candidate_id: cluster
        for cluster in pool.get("clusters") or []
        for candidate_id in cluster.get("candidate_ids") or []
    }
    for candidate in pool.get("candidates") or []:
        cluster = cluster_by_candidate.get(candidate.get("candidate_id"))
        if cluster is None:
            blockers.append(
                f"{candidate.get('candidate_id') or 'unknown'}:candidate_cluster_missing"
            )
            continue
        for field in ("cluster_id", "story_id", "update_chain_id"):
            if candidate.get(field) != cluster.get(field):
                blockers.append(
                    f"{candidate.get('candidate_id') or 'unknown'}:{field}_cluster_mismatch"
                )
        if (
            candidate.get("cluster_id") in prior_clusters
            or candidate.get("update_chain_id") in prior_chains
        ) and candidate.get("relationship") not in {
            "material_update", "correction", "contradiction", "new_phase"
        }:
            blockers.append("prior_identity_without_governed_delta")
        scored = score_candidate(candidate)
        row = {
            "candidate": candidate,
            "ranking": scored,
            "hard_blockers": sorted(set(blockers)),
        }
        if blockers:
            held.append(row)
        else:
            rows.append(row)
    rows.sort(key=lambda row: (
        -(row["ranking"]["score"] if row["ranking"]["score"] is not None else -1.0),
        str(row["candidate"].get("known_at_utc") or ""),
        str(row["candidate"].get("candidate_id") or ""),
    ))
    selected = rows[0] if rows else None
    if selected is None:
        decision = "NO_ASSIGNMENT_ALL_CANDIDATES_HELD"
    elif no_publication_boundary:
        decision = "ASSIGN_INTERNAL_NO_PUBLICATION_TASK_BOUNDARY"
    else:
        decision = "ASSIGN_OPERATOR_REVIEW_REQUIRED"
    return {
        "window_id": window["window_id"],
        "cutoff_time_utc": cutoff_utc,
        "decision": decision,
        "selected_candidate_id": selected["candidate"]["candidate_id"] if selected else None,
        "selected_capability_profile": (
            selected["candidate"]["evidence_requirement_profile_id"] if selected else None
        ),
        "ranking": selected["ranking"] if selected else None,
        "breaking_qualification": (
            breaking_qualification(selected["candidate"]) if selected else None
        ),
        "held_candidates": [
            {
                "candidate_id": row["candidate"]["candidate_id"],
                "capability_profile": row["candidate"]["evidence_requirement_profile_id"],
                "blockers": row["hard_blockers"],
            }
            for row in sorted(held, key=lambda value: value["candidate"]["candidate_id"])
        ],
        "publication_authority": False,
        "public_write_performed": False,
    }


def run_five_window_assignment(
    *,
    pool: Mapping[str, Any],
    schedule_date: str,
    windows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    assignments: list[Mapping[str, Any]] = []
    decisions = []
    for window in windows:
        decision = evaluate_v2_window_decision(
            window=window,
            schedule_date=schedule_date,
            pool=pool,
            previously_assigned=assignments,
            no_publication_boundary=True,
        )
        decisions.append(decision)
        if decision["selected_candidate_id"]:
            candidate = next(
                row for row in pool["candidates"]
                if row["candidate_id"] == decision["selected_candidate_id"]
            )
            assignments.append(candidate)
    result: dict[str, Any] = {
        "schema_version": ASSIGNMENT_SCHEMA,
        "schedule_date": schedule_date,
        "candidate_pool_id": pool["pool_id"],
        "calibration_state": UNCALIBRATED_STATE,
        "decisions": decisions,
        "summary": {
            "window_count": len(decisions),
            "internal_assignment_count": sum(
                row["selected_candidate_id"] is not None for row in decisions
            ),
            "publication_count": 0,
            "public_write_count": 0,
        },
        "publication_authority": False,
        "public_write_performed": False,
    }
    result["logical_hash"] = logical_hash(result)
    return result


def build_pool(
    *,
    candidates: Sequence[Mapping[str, Any]],
    source_family_records: Sequence[Mapping[str, Any]],
    generated_at_utc: str,
    cutoff_time_utc: str,
    upstream_binding: Mapping[str, Any],
    category_blockers: Mapping[str, str],
) -> dict[str, Any]:
    records = sorted((dict(row) for row in source_family_records), key=lambda row: row["source_family_id"])
    registry = {
        "schema_version": "contentops.source_family_registry.v2",
        "registry_version": SOURCE_FAMILY_REGISTRY_VERSION,
        "records": records,
    }
    registry["logical_hash"] = logical_hash(registry)
    registry_lookup = {str(row["source_family_id"]): row for row in records}
    ordered = sorted((dict(row) for row in candidates), key=lambda row: row["candidate_id"])
    contract_invalid_count = sum(
        bool(validate_candidate(
            row,
            cutoff_utc=cutoff_time_utc,
            source_family_registry=registry_lookup,
        ))
        for row in ordered
    )
    values: dict[str, Any] = {
        "schema_version": POOL_SCHEMA,
        "producer_version": "contentops.universal_news_candidate_pool.v2.0.0",
        "generated_at_utc": generated_at_utc,
        "cutoff_time_utc": cutoff_time_utc,
        "candidate_only": True,
        "global_dqr_override": False,
        "publication_authority": False,
        "public_write_allowed": False,
        "calibration_state": UNCALIBRATED_STATE,
        "claim_registry_version": CLAIM_REGISTRY_VERSION,
        "evidence_profile_registry_version": PROFILE_REGISTRY_VERSION,
        "source_family_registry": registry,
        "upstream_binding": dict(upstream_binding),
        "candidates": ordered,
        "clusters": cluster_candidates(ordered),
        "category_blockers": dict(sorted(category_blockers.items())),
        "counts": {
            "candidates": len(ordered),
            "claims": sum(len(row.get("claims") or []) for row in ordered),
            "numeric_claims": sum(
                claim.get("claim_type") == "numeric_observation"
                for row in ordered for claim in row.get("claims") or []
            ),
            "nonnumeric_claims": sum(
                claim.get("claim_type") != "numeric_observation"
                for row in ordered for claim in row.get("claims") or []
            ),
            "reporting_eligible": sum(row.get("reporting_allowed") is True for row in ordered),
            "held": sum(row.get("reporting_allowed") is not True for row in ordered),
            "rejected": contract_invalid_count,
        },
    }
    digest = logical_hash(values)
    values["pool_id"] = f"cc-universal-pool-{digest[:20]}"
    values["logical_hash"] = logical_hash(values)
    return values


def validate_pool(pool: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if pool.get("schema_version") != POOL_SCHEMA:
        blockers.append("pool_schema_invalid")
    if pool.get("candidate_only") is not True:
        blockers.append("pool_candidate_only_required")
    if pool.get("global_dqr_override") is not False:
        blockers.append("pool_global_dqr_override_forbidden")
    if pool.get("publication_authority") is not False:
        blockers.append("pool_publication_authority_forbidden")
    if pool.get("public_write_allowed") is not False:
        blockers.append("pool_public_write_forbidden")
    if pool.get("calibration_state") != UNCALIBRATED_STATE:
        blockers.append("pool_calibration_state_invalid")
    registry_block = pool.get("source_family_registry") or {}
    records = registry_block.get("records") or []
    registry = {str(row.get("source_family_id")): row for row in records}
    if len(registry) != len(records):
        blockers.append("source_family_registry_duplicate")
    if registry_block.get("logical_hash") != logical_hash(_without_hash(registry_block)):
        blockers.append("source_family_registry_hash_mismatch")
    cutoff = str(pool.get("cutoff_time_utc") or "")
    for candidate in pool.get("candidates") or []:
        blockers.extend(
            f"{candidate.get('candidate_id') or 'unknown'}:{value}"
            for value in validate_candidate(
                candidate,
                cutoff_utc=cutoff,
                source_family_registry=registry,
            )
        )
    expected_counts = {
        "candidates": len(pool.get("candidates") or []),
        "claims": sum(len(row.get("claims") or []) for row in pool.get("candidates") or []),
        "numeric_claims": sum(
            claim.get("claim_type") == "numeric_observation"
            for row in pool.get("candidates") or [] for claim in row.get("claims") or []
        ),
        "nonnumeric_claims": sum(
            claim.get("claim_type") != "numeric_observation"
            for row in pool.get("candidates") or [] for claim in row.get("claims") or []
        ),
        "reporting_eligible": sum(row.get("reporting_allowed") is True for row in pool.get("candidates") or []),
        "held": sum(row.get("reporting_allowed") is not True for row in pool.get("candidates") or []),
        "rejected": sum(
            bool(validate_candidate(
                row,
                cutoff_utc=cutoff,
                source_family_registry=registry,
            ))
            for row in pool.get("candidates") or []
        ),
    }
    if pool.get("counts") != expected_counts:
        blockers.append("pool_counts_mismatch")
    if not SHA256_RE.fullmatch(str(pool.get("logical_hash") or "")):
        blockers.append("pool_logical_hash_invalid")
    elif pool["logical_hash"] != logical_hash(_without_hash(pool)):
        blockers.append("pool_logical_hash_mismatch")
    return sorted(set(blockers))
