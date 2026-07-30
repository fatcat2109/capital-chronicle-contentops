"""Consume the first exact-Git nonnumeric story authority in the V3 shadow path.

This adapter is intentionally packet-specific. It accepts no caller-provided claims,
authority labels, permissions, story identities, or source URLs. Those values enter
the candidate only through verifier-produced evidence bindings.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from live_contentops.universal_evidence_receipt_verifier_v1 import (
    EvidenceReceiptVerifierV1,
)
from live_contentops.universal_governed_registry_v1 import (
    GovernedRegistryError,
    GovernedRegistrySnapshotV1,
    build_governed_claim,
    validate_governed_candidate,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    assign_generic_id,
    build_candidate,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_canonical_editorial_shadow_handoff,
)

SOURCE_FAMILY_ID = "nonnumeric_story_scoped_publication_evidence_v1"
ADAPTER_ID = "contentops.nonnumeric_story_authority_consumer.v1"
ADAPTER_RECORD_ID = "adapter-binding:nonnumeric_story_authority:v1"
UPSTREAM_PRODUCER_COMMIT = "ce4d011059b4a78eec47455821f93c418090d944"
UPSTREAM_PACKET_PATH = (
    "docs/research/publication_evidence/current/"
    "CapitalChronicleNonnumericStoryScopedReportingAuthorityV1.json"
)
AUTHORIZED_CLAIM_IDS = (
    "claim-bfca0e50bb4f64d0",
    "claim-1936ed019eb6602d",
)
CANONICAL_CLAIM_TYPES = {
    "official_regulatory_action": "official_action",
    "official_regulatory_limitation": "legal_or_regulatory_action",
}


def _day_to_utc(value: str) -> str:
    """Project an exact day-precision packet timestamp without adding precision."""

    return f"{value}T00:00:00Z"


def _single_receipt(bindings: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    if len(bindings) != len(AUTHORIZED_CLAIM_IDS):
        raise GovernedRegistryError("nonnumeric_story_binding_set_incomplete")
    receipts = [binding.get("receipt") or {} for binding in bindings]
    hashes = {str(receipt.get("logical_hash") or "") for receipt in receipts}
    if len(hashes) != 1 or "" in hashes:
        raise GovernedRegistryError("nonnumeric_story_receipt_not_exact_singleton")
    return receipts[0]


def build_nonnumeric_story_candidate_v1(
    *,
    authority: GovernedRegistrySnapshotV1,
    verifier: EvidenceReceiptVerifierV1,
    cutoff_utc: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build and validate one candidate from the exact verifier-authorized claims."""

    adapter = authority.adapter_bindings.get(ADAPTER_ID)
    if (
        not adapter
        or adapter.get("record_id") != ADAPTER_RECORD_ID
        or adapter.get("source_family_id") != SOURCE_FAMILY_ID
    ):
        raise GovernedRegistryError("nonnumeric_story_adapter_authority_missing")
    discovery = adapter.get("discovery_contract") or {}
    if (
        discovery.get("producer_commit") != UPSTREAM_PRODUCER_COMMIT
        or discovery.get("artifact_path") != UPSTREAM_PACKET_PATH
        or tuple(discovery.get("required_claim_ids") or ()) != AUTHORIZED_CLAIM_IDS
    ):
        raise GovernedRegistryError("nonnumeric_story_discovery_contract_mismatch")

    bindings = tuple(verifier.verify_nonnumeric_story_authority_bindings(
        artifact_path=UPSTREAM_PACKET_PATH,
        producer_commit=UPSTREAM_PRODUCER_COMMIT,
        source_family_id=SOURCE_FAMILY_ID,
        adapter_id=ADAPTER_ID,
        requested_claim_ids=AUTHORIZED_CLAIM_IDS,
        requested_consumer_permission="PUBLIC_CLAIM_ALLOWED",
        requested_dqr_reporting_allowed=True,
    ))
    receipt = _single_receipt(bindings)
    bindings_by_claim_id = {
        str(binding["evidence_ref"]).rsplit(":", 1)[-1]: binding
        for binding in bindings
    }
    if tuple(bindings_by_claim_id) != AUTHORIZED_CLAIM_IDS:
        raise GovernedRegistryError("nonnumeric_story_binding_claim_order_mismatch")

    timestamps = receipt["timestamps"]
    event_time_utc = _day_to_utc(str(timestamps["event_at"]))
    published_at_utc = _day_to_utc(str(timestamps["published_at"]))
    revision_at_utc = _day_to_utc(str(timestamps["provider_updated_at"]))
    known_at_utc = str(timestamps["known_at_utc"])
    document = {
        "document_id": receipt["document_id"],
        "source_native_id": receipt["source_native_id"],
        "title": "Financial Data Transparency Act Joint Data Standards",
        "authorized_urls": list(receipt["authorized_urls"]),
        "content_sha256": receipt["content_sha256"],
        "published_at_utc": published_at_utc,
        "known_at_utc": known_at_utc,
        "target_id": receipt["target_id"],
        "stable_record_id": receipt["stable_record_id"],
        "version_id": receipt["version_id"],
        "public_use_scope": dict(receipt["public_use_scope"]),
    }
    citations = [
        {
            "source_document_id": document["document_id"],
            "url": url,
            "citation_state": "EXACT_VERIFIER_AUTHORIZED_OFFICIAL_URL",
            "attribution": "Federal Register and GovInfo official public record",
        }
        for url in document["authorized_urls"]
    ]

    upstream_claims = receipt.get("authorized_claims") or []
    if tuple(str(row.get("claim_id") or "") for row in upstream_claims) != AUTHORIZED_CLAIM_IDS:
        raise GovernedRegistryError("nonnumeric_story_authorized_claim_set_mismatch")
    claims: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for upstream_claim in upstream_claims:
        claim_id = str(upstream_claim["claim_id"])
        upstream_type = str(upstream_claim["claim_type"])
        canonical_type = CANONICAL_CLAIM_TYPES.get(upstream_type)
        if canonical_type is None:
            raise GovernedRegistryError(
                f"nonnumeric_story_claim_type_not_supported:{upstream_type}"
            )
        binding = bindings_by_claim_id[claim_id]
        claim, decision = build_governed_claim(
            authority=authority,
            trusted_evidence_index=verifier.index,
            claim_id=claim_id,
            claim_type=canonical_type,
            evidence_refs=[str(binding["evidence_ref"])],
            statement=str(upstream_claim["text"]),
            structured_payload={
                "upstream_claim_type": upstream_type,
                "source_field": upstream_claim["source_field"],
                "contains_numeric_assertion": False,
                "interpretation_allowed": False,
                "reporting_allowed": True,
                "timestamp_precision": {
                    "event": timestamps["event_precision"],
                    "published": timestamps["published_precision"],
                    "known_at": timestamps["known_at_precision"],
                    "revision": timestamps["revision_precision"],
                },
            },
            source_document_ids=[str(document["document_id"])],
            observed_at_utc=None,
            event_time_utc=event_time_utc,
            published_at_utc=published_at_utc,
            known_at_utc=known_at_utc,
            revision_at_utc=revision_at_utc,
            citations=citations,
            entities=[],
            geographies=["United States"],
            limitations=[
                "exact_story_only",
                "strictly_nonnumeric",
                "interpretation_forbidden",
                "numeric_reporting_forbidden",
                "forecast_financial_advice_trading_and_dispatch_forbidden",
            ],
            numeric=None,
            market_evidence_refs=(),
            judgment_record=None,
        )
        claims.append(claim)
        decisions.append(decision)

    identity = {
        "stable_record_id": receipt["stable_record_id"],
        "packet_id": receipt["packet_id"],
    }
    evidence_refs = [str(binding["evidence_ref"]) for binding in bindings]
    candidate = build_candidate({
        "candidate_id": assign_generic_id("cc-candidate", {
            **identity,
            "version_id": receipt["version_id"],
            "authorized_claim_ids": list(AUTHORIZED_CLAIM_IDS),
        }),
        "story_id": assign_generic_id("cc-story", identity),
        "cluster_id": assign_generic_id("cc-cluster", identity),
        "update_chain_id": assign_generic_id("cc-update-chain", identity),
        "source_native_ids": [str(receipt["source_native_id"])],
        "source_family_ids": [SOURCE_FAMILY_ID],
        "adapter_id": ADAPTER_ID,
        "adapter_binding_record_id": ADAPTER_RECORD_ID,
        "evidence_requirement_profile_id": "official_action",
        "capabilities": {
            "claim_capabilities": sorted({claim["claim_type"] for claim in claims}),
            "numeric_evidence_required": False,
            "nonnumeric_evidence_supported": True,
        },
        "title": document["title"],
        "summary": str(claims[0]["statement"]),
        "relationship": "initial_event",
        "delta_signals": {"verified_new_version": False, "correction": False},
        "claims": claims,
        "claim_authority_decisions": decisions,
        "numeric_claims": [],
        "source_documents": [document],
        "entities": [],
        "geographies": ["United States"],
        "evidence_refs": evidence_refs,
        "event_evidence_refs": evidence_refs,
        "evidence_bindings": [dict(binding) for binding in bindings],
        "market_evidence_records": [],
        "authority_state": claims[0]["authority_class"],
        "reporting_allowed": True,
        "evidence_state": "exact",
        "event_time_utc": event_time_utc,
        "observation_time_utc": None,
        "published_at_utc": published_at_utc,
        "known_at_utc": known_at_utc,
        "revision_at_utc": revision_at_utc,
        "cutoff_time_utc": cutoff_utc,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": [
                "exact_git_story_packet_verified",
                "exact_authorized_claim_set_complete",
            ],
        },
        "freshness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": ["known_at_bound_to_exact_packet_receipt"],
        },
        "ranking_inputs": {
            "source_authority": {
                "availability": "AVAILABLE",
                "score": 100.0,
                "reason_codes": ["verifier_bound_official_public_record"],
                "evidence_refs": evidence_refs,
            },
        },
        "limitations": [
            "exact_two_claim_story_scope_only",
            "no_numeric_assertions",
            "no_interpretation_or_policy_consequence",
            "no_market_reaction_or_affected_company_claims",
            "global_dqr_remains_blocked",
            "ofac_context_only",
            "candidate_grants_no_publication_authority",
        ],
        "blockers": [],
        "publication_authority": False,
        "public_write_allowed": False,
        "global_dqr_override": False,
        "dispatch_allowed": False,
        "producer_binding": {
            "repository": receipt["repository"],
            "branch": receipt["branch"],
            "producer_commit": receipt["producer_commit"],
            "path": receipt["path"],
            "packet_id": receipt["packet_id"],
            "packet_logical_hash": receipt["packet_logical_hash"],
            "target_id": receipt["target_id"],
            "stable_record_id": receipt["stable_record_id"],
            "version_id": receipt["version_id"],
            "content_sha256": receipt["content_sha256"],
        },
    })
    validation = validate_governed_candidate(
        candidate,
        authority=authority,
        trusted_evidence_index=verifier.index,
        cutoff_utc=cutoff_utc,
    )
    if validation["status"] != "PASS":
        raise GovernedRegistryError(
            "nonnumeric_story_candidate_invalid:"
            + ",".join(validation["blockers"])
        )
    return candidate, validation


def build_nonnumeric_story_shadow_packet_v1(
    *,
    authority: GovernedRegistrySnapshotV1,
    verifier: EvidenceReceiptVerifierV1,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Run the exact two-claim candidate through the canonical V3 shadow handoff."""

    candidate, validation = build_nonnumeric_story_candidate_v1(
        authority=authority,
        verifier=verifier,
        cutoff_utc=generated_at_utc,
    )
    handoff = build_canonical_editorial_shadow_handoff(
        candidate,
        generated_at_utc=generated_at_utc,
    )
    result = {
        "schema_version": "contentops.nonnumeric_story_editorial_shadow.v1",
        "candidate": candidate,
        "candidate_validation": validation,
        "handoff": handoff,
        "authorized_claim_ids": list(AUTHORIZED_CLAIM_IDS),
        "global_dqr_status": "BLOCKED",
        "global_dqr_override": False,
        "ofac_context_only": True,
        "numeric_reporting_allowed": False,
        "interpretation_allowed": False,
        "forecast_allowed": False,
        "financial_advice_allowed": False,
        "trading_allowed": False,
        "dispatch_allowed": False,
        "publication_authority": False,
        "public_write_performed": False,
    }
    if (
        handoff.get("publication_authority") is not False
        or handoff.get("public_write_performed") is not False
    ):
        raise GovernedRegistryError("nonnumeric_story_shadow_authority_escalation")
    return result
