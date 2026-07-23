"""Source adapters for the real, local, no-write cross-domain V2 canary."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.governed_upstream_bridge_v1 import (
    DBH2_TARGET_CATALOG,
    V1_POOL_PATH,
    GovernedArtifactBlocked,
    GovernedUpstreamBridgeV1,
    read_git_json,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    adapt_v1_candidate,
    assign_generic_id,
    build_candidate,
    build_claim,
    build_pool,
    logical_hash,
    run_five_window_assignment,
    validate_pool,
)


CANARY_SCHEMA = "contentops.cross_domain_assignment_canary.v1"
CANARY_CUTOFF = "2026-07-14T00:00:00Z"
CANARY_SCHEDULE_DATE = "2026-07-14"
V1_POOL_PRODUCER_COMMIT = "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"
SOURCE_FAMILY_RECORDS = (
    {
        "source_family_id": "story_scoped_publication_evidence_v1",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "PUBLIC_CLAIM_ALLOWED",
        "evidence_state": "exact",
        "enabled": True,
    },
    {
        "source_family_id": "dbh2_federal_register_official_document",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "CONTEXT_ONLY",
        "evidence_state": "context",
        "enabled": True,
    },
    {
        "source_family_id": "dbh2_sec_official_filing_metadata",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "CONTEXT_ONLY",
        "evidence_state": "context",
        "enabled": True,
    },
    {
        "source_family_id": "dbh2_ofac_official_entity_snapshot",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "CONTEXT_ONLY",
        "evidence_state": "context",
        "enabled": True,
    },
    {
        "source_family_id": "dbh2_fomc_official_document",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "CONTEXT_ONLY",
        "evidence_state": "context",
        "enabled": True,
    },
    {
        "source_family_id": "dbh2_usgs_official_physical_event",
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_ceiling": "CONTEXT_ONLY",
        "evidence_state": "context",
        "enabled": True,
    },
)

FIVE_WINDOWS = (
    {"window_id": "asia_open", "target_cutoff_utc": "00:30:00"},
    {"window_id": "europe_open", "target_cutoff_utc": "07:30:00"},
    {"window_id": "us_open", "target_cutoff_utc": "13:30:00"},
    {"window_id": "us_midday", "target_cutoff_utc": "17:00:00"},
    {"window_id": "us_close", "target_cutoff_utc": "22:30:00"},
)


def _utc_date(value: str | None) -> str:
    if not value:
        return CANARY_CUTOFF
    return value if "T" in value else f"{value}T00:00:00Z"


def _record_evidence_ref(record: Mapping[str, Any]) -> str:
    return (
        f"dbh2:{record['target_id']}:{record['stable_record_id']}:"
        f"{record['version_id']}"
    )


def _source_document(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "document_id": f"dbh2-document:{record['stable_record_id']}:{record['version_id']}",
        "source_native_id": record["provider_record_id"],
        "title": record.get("title"),
        "source_url": record.get("canonical_url"),
        "content_sha256": record.get("content_sha256"),
        "published_at_utc": record.get("published_at_utc"),
        "known_at_utc": record.get("known_at_utc"),
        "target_id": record.get("target_id"),
    }


def _context_candidate(
    *,
    record: Mapping[str, Any],
    source_family_id: str,
    profile_id: str,
    claim_type: str,
    statement: str,
    structured_payload: Mapping[str, Any],
    entities: Sequence[str],
    geographies: Sequence[str],
    limitations: Sequence[str],
    event_time_utc: str | None,
    observation_time_utc: str | None = None,
    revision_relationships: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    document = _source_document(record)
    evidence_ref = _record_evidence_ref(record)
    claim_id = assign_generic_id("claim", {
        "record": record["stable_record_id"],
        "version": record["version_id"],
        "type": claim_type,
    })
    claim = build_claim(
        claim_id=claim_id,
        claim_type=claim_type,
        statement=statement,
        structured_payload=structured_payload,
        source_document_ids=[document["document_id"]],
        evidence_refs=[evidence_ref],
        authority_class="OFFICIAL_VERIFIED",
        permission_state="CONTEXT_ONLY",
        observed_at_utc=observation_time_utc,
        event_time_utc=event_time_utc,
        published_at_utc=record.get("published_at_utc"),
        known_at_utc=record["known_at_utc"],
        revision_at_utc=_utc_date(record.get("updated_at")) if record.get("updated_at") else None,
        citations=[{
            "source_document_id": document["document_id"],
            "url": record.get("canonical_url"),
            "citation_state": "EXACT_SOURCE_NATIVE_URL",
        }],
        entities=entities,
        geographies=geographies,
        limitations=limitations,
    )
    identity = {
        "source_native_id": record["provider_record_id"],
        "profile": profile_id,
        "entities": sorted(entities),
    }
    cluster_material = {"source_native_id": record["provider_record_id"], "profile": profile_id}
    values = {
        "candidate_id": assign_generic_id("cc-candidate", identity),
        "story_id": assign_generic_id("cc-story", cluster_material),
        "cluster_id": assign_generic_id("cc-cluster", cluster_material),
        "update_chain_id": assign_generic_id("cc-update-chain", cluster_material),
        "source_native_ids": [str(record["provider_record_id"])],
        "source_family_ids": [source_family_id],
        "evidence_requirement_profile_id": profile_id,
        "capabilities": {
            "claim_capabilities": [claim_type],
            "numeric_evidence_required": False,
            "nonnumeric_evidence_supported": True,
        },
        "title": str(record.get("title") or record.get("provider_record_id")),
        "summary": statement,
        "relationship": "initial_event",
        "claims": [claim],
        "source_documents": [document],
        "entities": list(entities),
        "geographies": list(geographies),
        "evidence_refs": [evidence_ref],
        "authority_state": "OFFICIAL_VERIFIED",
        "reporting_allowed": False,
        "evidence_state": "context",
        "event_time_utc": event_time_utc,
        "observation_time_utc": observation_time_utc,
        "published_at_utc": record.get("published_at_utc"),
        "known_at_utc": record["known_at_utc"],
        "revision_at_utc": _utc_date(record.get("updated_at")) if record.get("updated_at") else None,
        "cutoff_time_utc": CANARY_CUTOFF,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": ["exact_dbh2_record_and_manifest_lineage"],
        },
        "freshness": {
            "availability": "UNAVAILABLE",
            "value": None,
            "reason_codes": ["source_catalog_does_not_grant_reporting_freshness"],
        },
        "ranking_inputs": {
            "source_authority": {
                "availability": "AVAILABLE",
                "score": 100.0,
                "reason_codes": ["official_verified_exact_local_bytes"],
                "evidence_refs": [evidence_ref],
            },
            "audience_relevance": {
                "availability": "UNAVAILABLE",
                "score": None,
                "reason_codes": ["not_governed_in_source_artifact"],
                "evidence_refs": [],
            },
        },
        "limitations": [
            *limitations,
            "source_catalog_permission_ceiling_context_only",
            "candidate_contract_grants_no_publication_authority",
        ],
        "blockers": ["context_only_evidence"],
        "publication_authority": False,
        "public_write_allowed": False,
        "global_dqr_override": False,
        "producer_binding": {
            "target_id": record["target_id"],
            "stable_record_id": record["stable_record_id"],
            "version_id": record["version_id"],
            "content_sha256": record.get("content_sha256"),
            "revision_relationships": [dict(row) for row in revision_relationships],
        },
    }
    return build_candidate(values)


def _select_fomc_document(
    bridge: GovernedUpstreamBridgeV1,
    *,
    cutoff_utc: str,
) -> dict[str, Any]:
    from live_contentops.universal_news_candidate_fabric_v2 import parse_utc

    cutoff = parse_utc(cutoff_utc, field_name="cutoff_utc")
    connection = bridge.open_duckdb()
    try:
        rows = connection.execute(
            """
            SELECT record_id, stable_record_id, target_id, provider,
                   provider_record_type, provider_record_id, candidate_only,
                   current_canonical_apply, exact_authority, numeric_boundary,
                   version_id, updated_at, published_at, content_sha256,
                   title, status, canonical_url, payload_json
              FROM dbh2_records
             WHERE target_id = 'DBH2_FED_FOMC_CALENDAR_ARCHIVE'
               AND provider_record_type = 'fomc_official_document'
               AND json_extract_string(payload_json, '$.document_class') = 'minutes'
             ORDER BY published_at DESC, provider_record_id DESC
            """
        ).fetchall()
        columns = [row[0] for row in connection.description]
    finally:
        connection.close()
    for raw in rows:
        row = dict(zip(columns, raw))
        known = _utc_date(row.get("updated_at") or row.get("published_at"))
        if parse_utc(known, field_name="known_at_utc") > cutoff:
            continue
        row["known_at_utc"] = known
        row["published_at_utc"] = _utc_date(row.get("published_at"))
        row["payload"] = json.loads(row.pop("payload_json") or "{}")
        return row
    raise GovernedArtifactBlocked("governed_fomc_document_unavailable")


def build_real_cross_domain_canary(
    *,
    upstream_root: Path,
    observed_head: str,
) -> dict[str, Any]:
    bridge = GovernedUpstreamBridgeV1(
        root=upstream_root,
        observed_head=observed_head,
    )
    bridge.verify_all_local_artifacts()
    target_catalog, target_catalog_receipt = bridge.target_catalog()
    target_by_id = {row["target_id"]: row for row in target_catalog["targets"]}

    v1_pool, v1_pool_receipt = read_git_json(
        root=upstream_root,
        observed_head=observed_head,
        artifact_path=V1_POOL_PATH,
        producer_commit=V1_POOL_PRODUCER_COMMIT,
    )
    if not v1_pool.get("eligible_candidates"):
        raise GovernedArtifactBlocked("governed_v1_numeric_candidate_unavailable")
    numeric = adapt_v1_candidate(
        v1_pool["eligible_candidates"][0],
        source_family_id="story_scoped_publication_evidence_v1",
    )
    numeric["cutoff_time_utc"] = CANARY_CUTOFF
    numeric["ranking_inputs"] = {
        "source_authority": {
            "availability": "AVAILABLE",
            "score": 100.0,
            "reason_codes": ["story_scoped_official_public_authority"],
            "evidence_refs": list(numeric["evidence_refs"]),
        },
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "score": 100.0,
            "reason_codes": ["v1_claim_document_citation_projection_complete"],
            "evidence_refs": list(numeric["evidence_refs"]),
        },
        "surprise": {
            "availability": "EXPLICIT_ZERO",
            "score": 0,
            "reason_codes": ["explicit_governed_zero_no_surprise_measure"],
            "evidence_refs": list(numeric["evidence_refs"]),
        },
        "audience_relevance": {
            "availability": "UNAVAILABLE",
            "score": None,
            "reason_codes": ["not_available_from_governed_artifact"],
            "evidence_refs": [],
        },
    }
    numeric["producer_binding"] = {
        "v1_pool_receipt": v1_pool_receipt.as_dict(),
        "v1_pool_id": v1_pool["pool_id"],
        "v1_pool_logical_hash": v1_pool["logical_hash"],
    }
    numeric = build_candidate(numeric)

    regulatory_record = bridge.select_record(
        target_id="DBH2_FEDERAL_REGISTER_SEC",
        provider_record_type="federal_register_document",
        cutoff_utc=CANARY_CUTOFF,
    )
    regulatory = _context_candidate(
        record=regulatory_record,
        source_family_id="dbh2_federal_register_official_document",
        profile_id="official_action",
        claim_type="legal_or_regulatory_action",
        statement="An official regulatory notice was published with the source-native document identity and title.",
        structured_payload={
            "document_number": regulatory_record["provider_record_id"],
            "document_type": regulatory_record["status"],
            "agencies": regulatory_record["payload"].get("agencies") or [],
        },
        entities=regulatory_record["payload"].get("agencies") or [],
        geographies=["US"],
        limitations=["document_metadata_does_not_establish_market_effect_or_final_rule_status"],
        event_time_utc=regulatory_record["published_at_utc"],
        revision_relationships=bridge.relationships_for_record(
            stable_record_id=regulatory_record["stable_record_id"]
        ),
    )

    filing_record = bridge.select_record(
        target_id="DBH2_SEC_MSFT_SUBMISSIONS",
        provider_record_type="sec_filing",
        cutoff_utc=CANARY_CUTOFF,
        required_status="filed",
    )
    filing = _context_candidate(
        record=filing_record,
        source_family_id="dbh2_sec_official_filing_metadata",
        profile_id="corporate_filing",
        claim_type="corporate_filing_fact",
        statement="The configured issuer submitted the identified form under the source-native accession.",
        structured_payload={
            "accession": filing_record["provider_record_id"],
            "form": filing_record["payload"].get("form"),
            "issuer_entity_id": filing_record["payload"].get("entity_id"),
            "primary_document": filing_record["payload"].get("primary_document"),
        },
        entities=[str(filing_record["payload"].get("entity_id"))],
        geographies=["US"],
        limitations=[
            "filing_metadata_only",
            "no_earnings_revenue_valuation_or_market_reaction_claim",
        ],
        event_time_utc=filing_record["published_at_utc"],
        revision_relationships=bridge.relationships_for_record(
            stable_record_id=filing_record["stable_record_id"]
        ),
    )

    snapshot, entity_record = bridge.select_snapshot_entity(cutoff_utc=CANARY_CUTOFF)
    geopolitical = _context_candidate(
        record=snapshot,
        source_family_id="dbh2_ofac_official_entity_snapshot",
        profile_id="geopolitical_or_sanctions",
        claim_type="entity_relationship",
        statement="The exact official current snapshot contains the identified entity record.",
        structured_payload={
            "relationship_type": "snapshot_contains",
            "snapshot_id": snapshot["provider_record_id"],
            "entity_source_native_id": entity_record["provider_record_id"],
            "programs": entity_record["payload"].get("programs") or [],
        },
        entities=[str(entity_record["provider_record_id"])],
        geographies=["global"],
        limitations=[
            "current_entity_snapshot_is_context_not_a_new_sanctions_action",
            "no_action_date_or_delta_is_inferred",
        ],
        event_time_utc=snapshot["published_at_utc"],
        revision_relationships=bridge.relationships_for_record(
            stable_record_id=snapshot["stable_record_id"],
            counterpart_stable_record_id=entity_record["stable_record_id"],
        ),
    )

    fomc_record = _select_fomc_document(bridge, cutoff_utc=CANARY_CUTOFF)
    global_macro = _context_candidate(
        record=fomc_record,
        source_family_id="dbh2_fomc_official_document",
        profile_id="official_action",
        claim_type="factual_text",
        statement="The official archive contains the identified central-bank minutes document.",
        structured_payload={
            "document_class": fomc_record["payload"].get("document_class"),
            "source_native_document_id": fomc_record["provider_record_id"],
        },
        entities=["FOMC"],
        geographies=["US"],
        limitations=["document_presence_does_not_grant_numeric_policy_or_market_reaction_authority"],
        event_time_utc=fomc_record["published_at_utc"],
        revision_relationships=bridge.relationships_for_record(
            stable_record_id=fomc_record["stable_record_id"]
        ),
    )

    physical_record = bridge.select_record(
        target_id="DBH2_USGS_SIGNIFICANT_GLOBAL",
        provider_record_type="usgs_event",
        cutoff_utc=CANARY_CUTOFF,
        required_status="reviewed",
    )
    physical = _context_candidate(
        record=physical_record,
        source_family_id="dbh2_usgs_official_physical_event",
        profile_id="physical_disruption",
        claim_type="event_occurrence",
        statement="The official reviewed event record exists at the source-native event identity and chronology.",
        structured_payload={
            "event_id": physical_record["provider_record_id"],
            "place_text": physical_record["payload"].get("place"),
            "review_status": physical_record["status"],
        },
        entities=[],
        geographies=[str(physical_record["payload"].get("place"))],
        limitations=[
            "physical_event_context_only",
            "magnitude_text_is_not_promoted_to_numeric_reporting_authority",
            "affected_assets_or_transmission_channels_not_inferred",
        ],
        event_time_utc=physical_record["published_at_utc"],
        observation_time_utc=physical_record["published_at_utc"],
        revision_relationships=bridge.relationships_for_record(
            stable_record_id=physical_record["stable_record_id"]
        ),
    )

    candidates = [numeric, regulatory, filing, geopolitical, global_macro, physical]
    pool = build_pool(
        candidates=candidates,
        source_family_records=SOURCE_FAMILY_RECORDS,
        generated_at_utc=CANARY_CUTOFF,
        cutoff_time_utc=CANARY_CUTOFF,
        upstream_binding={
            "repository": "fatcat2109/Headline-Raw-data-json",
            "branch": "main",
            "observed_head": observed_head,
            "v1_pool_receipt": v1_pool_receipt.as_dict(),
            "target_catalog_receipt": target_catalog_receipt.as_dict(),
            "dbh2_bridge_receipt": bridge.authority_packet(),
        },
        category_blockers={},
    )
    pool_blockers = validate_pool(pool)
    if pool_blockers:
        raise ValueError("real_cross_domain_pool_invalid:" + ",".join(pool_blockers))
    assignments = run_five_window_assignment(
        pool=pool,
        schedule_date=CANARY_SCHEDULE_DATE,
        windows=FIVE_WINDOWS,
    )
    claim_counts: dict[str, int] = {}
    for candidate in pool["candidates"]:
        for claim in candidate["claims"]:
            claim_counts[claim["claim_type"]] = claim_counts.get(claim["claim_type"], 0) + 1
    result: dict[str, Any] = {
        "schema_version": CANARY_SCHEMA,
        "generated_at_utc": CANARY_CUTOFF,
        "upstream_observed_head": observed_head,
        "pool": pool,
        "assignment": assignments,
        "selected_real_categories": [
            "numeric_macro_release",
            "official_regulatory_document",
            "corporate_filing",
            "sanctions_entity_context",
            "central_bank_official_document",
            "physical_event",
        ],
        "source_target_authority": {
            target_id: {
                "authority_class": target_by_id[target_id]["authority_class"],
                "narrative_context_status": target_by_id[target_id]["narrative_context_status"],
                "access_class": target_by_id[target_id]["access_class"],
            }
            for target_id in (
                "DBH2_FEDERAL_REGISTER_SEC",
                "DBH2_SEC_MSFT_SUBMISSIONS",
                "DBH2_OFAC_SDN_CURRENT_SNAPSHOT",
                "DBH2_FED_FOMC_CALENDAR_ARCHIVE",
                "DBH2_USGS_SIGNIFICANT_GLOBAL",
            )
        },
        "candidate_counts": {
            "total": len(pool["candidates"]),
            "reporting_eligible": pool["counts"]["reporting_eligible"],
            "held_context_only": pool["counts"]["held"],
            "rejected_contract_invalid": pool["counts"]["rejected"],
        },
        "claim_counts_by_type": dict(sorted(claim_counts.items())),
        "publication_authority": False,
        "public_write_performed": False,
        "upstream_write_performed": False,
        "browser_or_provider_call_performed": False,
        "classification": "PASS_REAL_CROSS_DOMAIN_CANARY_NO_PUBLICATION",
    }
    result["logical_hash"] = logical_hash(result)
    return result
