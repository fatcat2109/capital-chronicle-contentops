"""Additive generic editorial evidence packet superseding the frozen V2 contract.

V3 preserves every frozen V2 field at the top level and embeds the exact V2
packet under ``v2_compatibility_projection``. Generic claim graph nodes are
canonical governed V2 claim objects; this module does not copy, reinterpret,
or upgrade their authority or permission.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from live_contentops.cc_evidence_bridge_v2 import validate_evidence_packet
from live_contentops.universal_governed_registry_v1 import logical_hash, without_hash


SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v3"
V2_SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v2"
CLAIM_SCHEMA_VERSION = "contentops.universal_news_claim.v2"
SUPPORTED_CLAIM_TYPES = frozenset({
    "numeric_observation",
    "factual_text",
    "official_action",
    "legal_or_regulatory_action",
    "corporate_filing_fact",
    "event_occurrence",
    "entity_relationship",
    "correction_or_revision",
    "market_reaction",
    "model_assisted_judgment",
})
PUBLIC_PERMISSION = "PUBLIC_CLAIM_ALLOWED"
_REQUIRED_CLAIM_FIELDS = (
    "schema_version",
    "claim_id",
    "claim_type",
    "structured_payload",
    "source_document_ids",
    "evidence_refs",
    "authority_class",
    "permission_state",
    "observed_at_utc",
    "event_time_utc",
    "published_at_utc",
    "known_at_utc",
    "revision_at_utc",
    "entities",
    "geographies",
    "citations",
    "limitations",
    "market_evidence_refs",
    "logical_hash",
)


def _numeric_projection_from_claim(
    claim: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> dict[str, Any] | None:
    numeric = claim.get("numeric")
    if not isinstance(numeric, Mapping):
        return None
    return {
        "claim_id": str(claim["claim_id"]),
        "metric": numeric.get("metric"),
        "value": numeric.get("value"),
        "unit": numeric.get("unit"),
        "observation_time_utc": claim.get("observed_at_utc"),
        "source_id": candidate.get("adapter_id"),
        "source_artifact_ref": (claim.get("evidence_refs") or [None])[0],
        "public_claim_allowed": (
            claim.get("permission_state") == PUBLIC_PERMISSION
            and candidate.get("reporting_allowed") is True
        ),
        "llm_numeric_authority": False,
    }


def _approval_blockers(
    claim: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if candidate.get("reporting_allowed") is not True:
        blockers.append("candidate_reporting_not_allowed")
    if claim.get("permission_state") != PUBLIC_PERMISSION:
        blockers.append("claim_public_permission_not_granted")
    if not claim.get("citations"):
        blockers.append("claim_exact_citations_missing")
    if not claim.get("evidence_refs"):
        blockers.append("claim_exact_evidence_refs_missing")
    if not claim.get("source_document_ids"):
        blockers.append("claim_source_document_ids_missing")
    if claim.get("claim_type") == "market_reaction" and not claim.get(
        "market_evidence_refs"
    ):
        blockers.append("market_reaction_separate_evidence_missing")
    if claim.get("claim_type") == "model_assisted_judgment":
        blockers.append("model_assisted_judgment_requires_separate_editorial_review")
    return blockers


def build_content_evidence_packet_v3(
    candidate: Mapping[str, Any],
    *,
    generated_at_utc: str,
    v2_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build V3 from an exact candidate and its already-built V2 projection."""

    frozen_v2 = deepcopy(dict(v2_packet))
    v2_blockers = validate_evidence_packet(frozen_v2)
    if v2_blockers:
        raise ValueError(
            "v3_v2_compatibility_projection_invalid:" + ",".join(v2_blockers)
        )
    if frozen_v2.get("schema_version") != V2_SCHEMA_VERSION:
        raise ValueError("v3_v2_compatibility_schema_mismatch")

    claims = deepcopy(list(candidate.get("claims") or []))
    approval_decisions = []
    approved_claim_ids = []
    for claim in claims:
        blockers = _approval_blockers(claim, candidate=candidate)
        approved = not blockers
        claim_id = str(claim.get("claim_id") or "")
        if approved:
            approved_claim_ids.append(claim_id)
        approval_decisions.append({
            "claim_id": claim_id,
            "claim_type": claim.get("claim_type"),
            "authority_class": claim.get("authority_class"),
            "permission_state": claim.get("permission_state"),
            "approved_for_reporting": approved,
            "blockers": blockers,
            "decision_source": "DERIVED_FROM_GOVERNED_CLAIM_AND_CANDIDATE",
        })

    numeric_projection = [
        row
        for row in (
            _numeric_projection_from_claim(claim, candidate=candidate)
            for claim in claims
        )
        if row is not None
    ]
    if numeric_projection != frozen_v2.get("numeric_claims"):
        raise ValueError("v3_numeric_projection_not_exact_v2_projection")

    packet = {
        **deepcopy(frozen_v2),
        "schema_version": SCHEMA_VERSION,
        "supersedes_schema_version": V2_SCHEMA_VERSION,
        "governed_claim_graph": {
            "graph_version": "contentops.governed_generic_claim_graph.v1",
            "claims": claims,
            "edges": [],
            "approved_claim_ids": approved_claim_ids,
            "approval_decisions": approval_decisions,
        },
        "generic_claim_permissions": {
            "approved_claim_ids": approved_claim_ids,
            "reporting_claims_allowed": bool(approved_claim_ids),
            "decision": "ALLOW" if approved_claim_ids else "BLOCK",
            "no_editorial_permission_upgrade": True,
        },
        "v2_compatibility_projection": frozen_v2,
        "v2_compatibility": {
            "projection_schema_version": V2_SCHEMA_VERSION,
            "top_level_numeric_claims_exact": True,
            "numeric_consumer_breaking_change": False,
            "nonnumeric_claim_requires_numeric_projection": False,
        },
    }
    packet["validation_blockers"] = validate_content_evidence_packet_v3(packet)
    packet["status"] = (
        "PASS_CONTRACT_BLOCKED_PUBLICATION"
        if not packet["validation_blockers"]
        else "FAIL_SCHEMA"
    )
    packet["logical_hash"] = logical_hash({
        key: value for key, value in packet.items() if key != "logical_hash"
    })
    return packet


def validate_content_evidence_packet_v3(packet: Mapping[str, Any]) -> list[str]:
    """Validate V3 lineage and its exact frozen V2 compatibility projection."""

    blockers: list[str] = []
    if packet.get("schema_version") != SCHEMA_VERSION:
        blockers.append("v3_schema_version_invalid")
    if packet.get("supersedes_schema_version") != V2_SCHEMA_VERSION:
        blockers.append("v3_supersedes_schema_version_invalid")

    projection = packet.get("v2_compatibility_projection")
    if not isinstance(projection, Mapping):
        blockers.append("v3_v2_compatibility_projection_missing")
        projection = {}
    else:
        blockers.extend(
            f"v3_v2_projection:{item}"
            for item in validate_evidence_packet(projection)
        )
        if projection.get("schema_version") != V2_SCHEMA_VERSION:
            blockers.append("v3_v2_projection_schema_invalid")
        if packet.get("numeric_claims") != projection.get("numeric_claims"):
            blockers.append("v3_top_level_numeric_projection_mismatch")
        for key in (
            "packet_id",
            "generated_at_utc",
            "as_of_utc",
            "story_window",
            "events",
            "official_source_documents",
            "market_snapshots",
            "source_state",
            "candidate_visual_inputs",
            "citation_map",
            "provenance",
            "public_claim_permissions",
            "blockers",
            "bridge_safety",
        ):
            if packet.get(key) != projection.get(key):
                blockers.append(f"v3_v2_projection_field_mismatch:{key}")

    graph = packet.get("governed_claim_graph")
    if not isinstance(graph, Mapping):
        blockers.append("v3_governed_claim_graph_missing")
        graph = {}
    claims = list(graph.get("claims") or [])
    approved_claim_ids = list(graph.get("approved_claim_ids") or [])
    decisions = list(graph.get("approval_decisions") or [])
    if len(decisions) != len(claims):
        blockers.append("v3_claim_approval_decision_count_mismatch")

    document_by_id = {
        str(row.get("document_id")): row
        for row in packet.get("official_source_documents") or []
        if row.get("document_id")
    }
    provenance_refs = set(
        str(value)
        for value in (packet.get("provenance") or {}).get("evidence_refs") or []
    )
    claim_ids: list[str] = []
    derived_approved_ids: list[str] = []
    numeric_claim_ids: list[str] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "unknown")
        claim_ids.append(claim_id)
        missing = [key for key in _REQUIRED_CLAIM_FIELDS if key not in claim]
        blockers.extend(f"v3_claim:{claim_id}:missing:{key}" for key in missing)
        if claim.get("schema_version") != CLAIM_SCHEMA_VERSION:
            blockers.append(f"v3_claim:{claim_id}:schema_version_invalid")
        if claim.get("claim_type") not in SUPPORTED_CLAIM_TYPES:
            blockers.append(f"v3_claim:{claim_id}:claim_type_unsupported")
        if claim.get("logical_hash") != logical_hash(without_hash(claim)):
            blockers.append(f"v3_claim:{claim_id}:logical_hash_mismatch")
        evidence_refs = [str(value) for value in claim.get("evidence_refs") or []]
        if not evidence_refs or not set(evidence_refs).issubset(provenance_refs):
            blockers.append(f"v3_claim:{claim_id}:evidence_lineage_mismatch")
        document_ids = [
            str(value) for value in claim.get("source_document_ids") or []
        ]
        if not document_ids or not set(document_ids).issubset(document_by_id):
            blockers.append(f"v3_claim:{claim_id}:source_document_lineage_mismatch")
        citations = list(claim.get("citations") or [])
        if not citations:
            blockers.append(f"v3_claim:{claim_id}:exact_citations_missing")
        for citation in citations:
            document_id = str(citation.get("source_document_id") or "")
            if document_id not in document_ids:
                blockers.append(f"v3_claim:{claim_id}:citation_document_mismatch")
                continue
            url = citation.get("url")
            authorized_urls = set(
                str(value)
                for value in document_by_id.get(document_id, {}).get(
                    "authorized_urls"
                ) or []
            )
            if not url or str(url) not in authorized_urls:
                blockers.append(f"v3_claim:{claim_id}:citation_url_not_authorized")
        if claim.get("claim_type") == "numeric_observation":
            numeric_claim_ids.append(claim_id)
            if not isinstance(claim.get("numeric"), Mapping):
                blockers.append(f"v3_claim:{claim_id}:numeric_payload_missing")
        elif claim.get("numeric") is not None:
            blockers.append(f"v3_claim:{claim_id}:nonnumeric_claim_has_numeric_payload")
        if claim.get("claim_type") == "market_reaction" and not claim.get(
            "market_evidence_refs"
        ):
            blockers.append(f"v3_claim:{claim_id}:market_evidence_missing")
        if claim.get("claim_type") == "model_assisted_judgment" and not isinstance(
            claim.get("judgment_record"), Mapping
        ):
            blockers.append(f"v3_claim:{claim_id}:judgment_record_missing")
        decision_blockers = _approval_blockers(
            claim,
            candidate={
                "reporting_allowed": (
                    packet.get("source_state") or {}
                ).get("reporting_allowed")
            },
        )
        expected_decision = {
            "claim_id": claim_id,
            "claim_type": claim.get("claim_type"),
            "authority_class": claim.get("authority_class"),
            "permission_state": claim.get("permission_state"),
            "approved_for_reporting": not decision_blockers,
            "blockers": decision_blockers,
            "decision_source": "DERIVED_FROM_GOVERNED_CLAIM_AND_CANDIDATE",
        }
        decision_index = len(claim_ids) - 1
        if decision_index >= len(decisions) or decisions[decision_index] != expected_decision:
            blockers.append(f"v3_claim:{claim_id}:approval_decision_mismatch")
        if not decision_blockers:
            derived_approved_ids.append(claim_id)

    if len(claim_ids) != len(set(claim_ids)):
        blockers.append("v3_duplicate_claim_id")
    if approved_claim_ids != derived_approved_ids:
        blockers.append("v3_approved_claim_ids_not_permission_derived")
    generic_permissions = packet.get("generic_claim_permissions") or {}
    if generic_permissions.get("approved_claim_ids") != approved_claim_ids:
        blockers.append("v3_generic_permission_claim_set_mismatch")
    if generic_permissions.get("reporting_claims_allowed") is not bool(
        approved_claim_ids
    ):
        blockers.append("v3_generic_permission_decision_mismatch")
    projected_numeric_ids = [
        str(row.get("claim_id")) for row in packet.get("numeric_claims") or []
    ]
    if projected_numeric_ids != numeric_claim_ids:
        blockers.append("v3_numeric_claim_id_projection_mismatch")

    if packet.get("logical_hash") is not None:
        expected_hash = logical_hash({
            key: value for key, value in packet.items() if key != "logical_hash"
        })
        if packet.get("logical_hash") != expected_hash:
            blockers.append("v3_packet_logical_hash_mismatch")
    return list(dict.fromkeys(blockers))