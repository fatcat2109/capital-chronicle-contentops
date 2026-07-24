"""Deterministic local continuous cross-domain intake and shadow operation."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.governed_upstream_bridge_v1 import (
    V1_POOL_PATH,
    GovernedArtifactBlocked,
    GovernedUpstreamBridgeV1,
    read_git_json,
)
from live_contentops.universal_governed_registry_v1 import (
    GovernedRegistrySnapshotV1,
    build_exact_evidence_binding,
    build_governed_claim,
    build_governed_pool,
    load_governed_registry_authority,
    logical_hash,
    validate_governed_pool,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    assign_generic_id,
    build_candidate,
    cluster_candidates,
    evaluate_v2_window_decision,
)


SCHEMA_VERSION = "contentops.cross_domain_continuous_shadow.v1"
UPSTREAM_HEAD = "02120f86c9e9923d9c2b49db1533443cd2849eb9"
V1_POOL_PRODUCER_COMMIT = "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"
CORRECTION_STABLE_ID = (
    "8ad3bdfa8d266d27eb66284caa2ad89980f60eeae92ed6302ea136b5278c8c02"
)
CHECKPOINTS = (
    "2015-07-22T00:00:00Z",
    "2015-08-06T00:00:00Z",
    "2026-06-18T00:00:00Z",
    "2026-07-02T00:00:00Z",
    "2026-07-11T00:00:00Z",
    "2026-07-13T00:00:00Z",
    "2026-07-14T00:00:00Z",
    "2026-07-15T00:00:00Z",
    "2026-07-16T00:00:00Z",
)
FIVE_WINDOWS = (
    {"window_id": "asia_open", "target_cutoff_utc": "00:30:00"},
    {"window_id": "europe_open", "target_cutoff_utc": "07:30:00"},
    {"window_id": "us_open", "target_cutoff_utc": "13:30:00"},
    {"window_id": "us_midday", "target_cutoff_utc": "17:00:00"},
    {"window_id": "us_close", "target_cutoff_utc": "22:30:00"},
)

ADAPTER_BY_FAMILY = {
    "dbh2_federal_register_official_document": (
        "contentops.dbh2.federal_register_document.v1"
    ),
    "dbh2_sec_official_filing_metadata": "contentops.dbh2.sec_filing.v1",
    "dbh2_ofac_official_entity_snapshot": "contentops.dbh2.ofac_snapshot.v1",
    "dbh2_fomc_official_document": "contentops.dbh2.fomc_document.v1",
    "dbh2_usgs_official_physical_event": "contentops.dbh2.usgs_event.v1",
}


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_missing")
    return parsed.astimezone(timezone.utc)


def _utc(value: str | None) -> str | None:
    if not value:
        return None
    if "T" not in value:
        return f"{value}T00:00:00Z"
    parsed = _parse_utc(value)
    return parsed.isoformat().replace("+00:00", "Z")


def _row_from_db(
    bridge: GovernedUpstreamBridgeV1,
    *,
    stable_record_id: str,
    version_id: str | None = None,
) -> dict[str, Any]:
    connection = bridge.open_duckdb()
    try:
        query = """
            SELECT record_id, stable_record_id, target_id, provider,
                   provider_record_type, provider_record_id, candidate_only,
                   current_canonical_apply, exact_authority, numeric_boundary,
                   version_id, updated_at, published_at, content_sha256,
                   title, status, canonical_url, payload_json
              FROM dbh2_records
             WHERE stable_record_id = ?
        """
        parameters: list[Any] = [stable_record_id]
        if version_id is not None:
            query += " AND version_id = ?"
            parameters.append(version_id)
        query += " ORDER BY coalesce(updated_at, published_at), version_id"
        rows = connection.execute(query, parameters).fetchall()
        columns = [row[0] for row in connection.description]
    finally:
        connection.close()
    if not rows:
        raise GovernedArtifactBlocked(
            f"governed_record_identity_unavailable:{stable_record_id}"
        )
    raw = rows[-1] if version_id is None else rows[0]
    record = dict(zip(columns, raw))
    record["known_at_utc"] = _utc(
        record.get("updated_at") or record.get("published_at")
    )
    record["published_at_utc"] = _utc(record.get("published_at"))
    record["payload"] = json.loads(record.pop("payload_json") or "{}")
    return record


def _all_versions(
    bridge: GovernedUpstreamBridgeV1,
    *,
    stable_record_id: str,
) -> list[dict[str, Any]]:
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
             WHERE stable_record_id = ?
             ORDER BY coalesce(updated_at, published_at), version_id
            """,
            [stable_record_id],
        ).fetchall()
        columns = [row[0] for row in connection.description]
    finally:
        connection.close()
    result = []
    for raw in rows:
        record = dict(zip(columns, raw))
        record["known_at_utc"] = _utc(
            record.get("updated_at") or record.get("published_at")
        )
        record["published_at_utc"] = _utc(record.get("published_at"))
        record["payload"] = json.loads(record.pop("payload_json") or "{}")
        result.append(record)
    return result


def _select_fomc_minutes(
    bridge: GovernedUpstreamBridgeV1,
    *,
    cutoff_utc: str,
) -> dict[str, Any]:
    cutoff = _parse_utc(cutoff_utc)
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
             ORDER BY coalesce(updated_at, published_at) DESC, provider_record_id
            """
        ).fetchall()
        columns = [row[0] for row in connection.description]
    finally:
        connection.close()
    for raw in rows:
        record = dict(zip(columns, raw))
        known = _utc(record.get("updated_at") or record.get("published_at"))
        if known and _parse_utc(known) <= cutoff:
            record["known_at_utc"] = known
            record["published_at_utc"] = _utc(record.get("published_at"))
            record["payload"] = json.loads(record.pop("payload_json") or "{}")
            return record
    raise GovernedArtifactBlocked("governed_fomc_minutes_unavailable")


def _source_document(record: Mapping[str, Any]) -> dict[str, Any]:
    url = str(record.get("canonical_url") or "")
    return {
        "document_id": (
            f"dbh2-document:{record['stable_record_id']}:{record['version_id']}"
        ),
        "source_native_id": str(record["provider_record_id"]),
        "title": record.get("title"),
        "authorized_urls": [url] if url else [],
        "content_sha256": record["content_sha256"],
        "published_at_utc": record.get("published_at_utc"),
        "known_at_utc": record.get("known_at_utc"),
        "target_id": record.get("target_id"),
    }


def _dbh2_evidence_binding(
    *,
    record: Mapping[str, Any],
    family_id: str,
    authority: GovernedRegistrySnapshotV1,
    bridge_packet: Mapping[str, Any],
) -> dict[str, Any]:
    adapter_id = ADAPTER_BY_FAMILY[family_id]
    adapter = authority.adapter_bindings[adapter_id]
    document = _source_document(record)
    evidence_ref = (
        f"dbh2:{record['target_id']}:{record['stable_record_id']}:"
        f"{record['version_id']}"
    )
    return build_exact_evidence_binding(
        binding_id=assign_generic_id("evidence-binding", {
            "evidence_ref": evidence_ref,
            "adapter_binding_record_id": adapter["record_id"],
        }),
        accepted_evidence_binding_id=str(adapter["accepted_evidence_binding"]),
        evidence_ref=evidence_ref,
        source_family_id=family_id,
        adapter_id=adapter_id,
        adapter_binding_record_id=str(adapter["record_id"]),
        document_id=document["document_id"],
        source_native_id=document["source_native_id"],
        content_sha256=str(document["content_sha256"]),
        source_native_status=str(record["status"]),
        evidence_state="context",
        consumer_permission="CONTEXT_ONLY",
        dqr_reporting_allowed=False,
        receipt={
            "receipt_kind": "dbh2_record_version",
            "exact_verified": True,
            "bridge_authority_packet_hash": bridge_packet["logical_hash"],
            "target_id": record["target_id"],
            "stable_record_id": record["stable_record_id"],
            "version_id": record["version_id"],
            "content_sha256": record["content_sha256"],
        },
    )


def _dbh2_candidate_spec(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    target = record["target_id"]
    if target == "DBH2_FEDERAL_REGISTER_SEC":
        return {
            "family_id": "dbh2_federal_register_official_document",
            "profile_id": "official_action",
            "claim_type": "legal_or_regulatory_action",
            "statement": (
                "The official regulatory document exists at the exact "
                "source-native document number and governed version."
            ),
            "payload": {
                "document_number": record["provider_record_id"],
                "document_type": record["status"],
                "agencies": record["payload"].get("agencies") or [],
            },
            "entities": record["payload"].get("agencies") or [],
            "geographies": ["US"],
            "limitations": [
                "document_metadata_does_not_establish_market_effect",
            ],
        }
    if target == "DBH2_SEC_MSFT_SUBMISSIONS":
        return {
            "family_id": "dbh2_sec_official_filing_metadata",
            "profile_id": "corporate_filing",
            "claim_type": "corporate_filing_fact",
            "statement": (
                "The configured issuer filed the identified form under the "
                "source-native accession."
            ),
            "payload": {
                "accession": record["provider_record_id"],
                "form": record["payload"].get("form"),
                "issuer_entity_id": record["payload"].get("entity_id"),
                "primary_document": record["payload"].get("primary_document"),
            },
            "entities": [str(record["payload"].get("entity_id"))],
            "geographies": ["US"],
            "limitations": [
                "filing_metadata_only",
                "no_earnings_revenue_valuation_or_market_reaction_claim",
            ],
        }
    if target == "DBH2_OFAC_SDN_CURRENT_SNAPSHOT":
        return {
            "family_id": "dbh2_ofac_official_entity_snapshot",
            "profile_id": "geopolitical_or_sanctions",
            "claim_type": "entity_relationship",
            "statement": (
                "The exact official snapshot contains a governed entity "
                "membership relationship."
            ),
            "payload": {
                "relationship_type": "snapshot_contains",
                "snapshot_id": record["provider_record_id"],
            },
            "entities": [],
            "geographies": ["global"],
            "limitations": [
                "snapshot_membership_is_not_a_new_sanctions_action",
                "no_action_or_delta_is_inferred",
            ],
        }
    if target == "DBH2_FED_FOMC_CALENDAR_ARCHIVE":
        return {
            "family_id": "dbh2_fomc_official_document",
            "profile_id": "official_action",
            "claim_type": "factual_text",
            "statement": (
                "The official archive contains the identified central-bank "
                "minutes document."
            ),
            "payload": {
                "document_class": record["payload"].get("document_class"),
                "source_native_document_id": record["provider_record_id"],
            },
            "entities": ["FOMC"],
            "geographies": ["US"],
            "limitations": [
                "document_presence_does_not_grant_numeric_or_market_authority",
            ],
        }
    if target == "DBH2_USGS_SIGNIFICANT_GLOBAL":
        return {
            "family_id": "dbh2_usgs_official_physical_event",
            "profile_id": "physical_disruption",
            "claim_type": "event_occurrence",
            "statement": (
                "The official reviewed physical-event record exists at the "
                "source-native event identity and governed version."
            ),
            "payload": {
                "event_id": record["provider_record_id"],
                "place_text": record["payload"].get("place"),
                "review_status": record["status"],
            },
            "entities": [],
            "geographies": [str(record["payload"].get("place"))],
            "limitations": [
                "physical_event_context_only",
                "numeric_text_is_not_promoted_to_numeric_truth",
            ],
        }
    raise GovernedArtifactBlocked(f"unsupported_continuous_target:{target}")


def _build_dbh2_candidate(
    *,
    record: Mapping[str, Any],
    authority: GovernedRegistrySnapshotV1,
    bridge_packet: Mapping[str, Any],
    trusted_evidence_index: dict[str, Mapping[str, Any]],
    relationship: str = "initial_event",
) -> dict[str, Any]:
    spec = _dbh2_candidate_spec(record)
    document = _source_document(record)
    binding = _dbh2_evidence_binding(
        record=record,
        family_id=spec["family_id"],
        authority=authority,
        bridge_packet=bridge_packet,
    )
    evidence_ref = str(binding["evidence_ref"])
    trusted_evidence_index[evidence_ref] = binding
    claim_id = assign_generic_id("claim", {
        "stable_record_id": record["stable_record_id"],
        "version_id": record["version_id"],
        "claim_type": spec["claim_type"],
    })
    event_time = record.get("published_at_utc") or record["known_at_utc"]
    claim, authority_decision = build_governed_claim(
        authority=authority,
        trusted_evidence_index=trusted_evidence_index,
        claim_id=claim_id,
        claim_type=spec["claim_type"],
        statement=spec["statement"],
        structured_payload=spec["payload"],
        source_document_ids=[document["document_id"]],
        evidence_refs=[evidence_ref],
        observed_at_utc=(
            event_time
            if record["target_id"] == "DBH2_USGS_SIGNIFICANT_GLOBAL"
            else None
        ),
        event_time_utc=event_time,
        published_at_utc=record.get("published_at_utc"),
        known_at_utc=record["known_at_utc"],
        revision_at_utc=_utc(record.get("updated_at")),
        citations=[{
            "source_document_id": document["document_id"],
            "url": (
                document["authorized_urls"][0]
                if document["authorized_urls"]
                else None
            ),
            "citation_state": "EXACT_SOURCE_NATIVE_URL",
        }],
        entities=spec["entities"],
        geographies=spec["geographies"],
        limitations=spec["limitations"],
        numeric=None,
        market_evidence_refs=(),
        judgment_record=None,
    )
    identity = {"stable_record_id": record["stable_record_id"]}
    values = {
        "candidate_id": assign_generic_id("cc-candidate", {
            **identity,
            "version_id": record["version_id"],
        }),
        "story_id": assign_generic_id("cc-story", identity),
        "cluster_id": assign_generic_id("cc-cluster", identity),
        "update_chain_id": assign_generic_id("cc-update-chain", identity),
        "source_native_ids": [str(record["provider_record_id"])],
        "source_family_ids": [spec["family_id"]],
        "adapter_id": ADAPTER_BY_FAMILY[spec["family_id"]],
        "evidence_requirement_profile_id": spec["profile_id"],
        "capabilities": {
            "claim_capabilities": [spec["claim_type"]],
            "numeric_evidence_required": False,
            "nonnumeric_evidence_supported": True,
        },
        "title": str(record.get("title") or record["provider_record_id"]),
        "summary": spec["statement"],
        "relationship": relationship,
        "delta_signals": {"correction": relationship == "correction"},
        "claims": [claim],
        "claim_authority_decisions": [authority_decision],
        "numeric_claims": [],
        "source_documents": [document],
        "entities": list(spec["entities"]),
        "geographies": list(spec["geographies"]),
        "evidence_refs": [evidence_ref],
        "event_evidence_refs": [evidence_ref],
        "evidence_bindings": [binding],
        "market_evidence_records": [],
        "authority_state": claim["authority_class"],
        "reporting_allowed": False,
        "evidence_state": "context",
        "event_time_utc": event_time,
        "observation_time_utc": (
            event_time
            if record["target_id"] == "DBH2_USGS_SIGNIFICANT_GLOBAL"
            else None
        ),
        "published_at_utc": record.get("published_at_utc"),
        "known_at_utc": record["known_at_utc"],
        "revision_at_utc": _utc(record.get("updated_at")),
        "cutoff_time_utc": None,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": ["exact_dbh2_record_version_and_manifest_receipt"],
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
                "reason_codes": ["receipt_bound_official_source"],
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
            *spec["limitations"],
            "source_family_permission_ceiling_context_only",
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
            "content_sha256": record["content_sha256"],
        },
    }
    return build_candidate(values)


def _build_v1_candidate(
    *,
    upstream_root: Path,
    observed_head: str,
    authority: GovernedRegistrySnapshotV1,
    trusted_evidence_index: dict[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    pool, pool_receipt = read_git_json(
        root=upstream_root,
        observed_head=observed_head,
        artifact_path=V1_POOL_PATH,
        producer_commit=V1_POOL_PRODUCER_COMMIT,
    )
    source = pool["eligible_candidates"][0]
    adapter = authority.adapter_bindings[
        "contentops.v1_newsroom_candidate_pool_adapter.v1"
    ]
    raw_documents = list(source.get("source_documents") or [])
    documents = []
    for row in raw_documents:
        authorized_urls = sorted({
            str(url)
            for url in (row.get("source_url"), row.get("data_url"))
            if url
        })
        documents.append({
            **dict(row),
            "source_native_id": str(row["document_id"]),
            "authorized_urls": authorized_urls,
            "content_sha256": row["raw_sha256"],
        })
    document = documents[0]
    claims = []
    decisions = []
    bindings = []
    for row in source.get("numeric_claims") or []:
        claim_id = str(row["claim_id"])
        evidence_ref = f"v1:{source['evidence_hash']}:{claim_id}"
        binding = build_exact_evidence_binding(
            binding_id=assign_generic_id("evidence-binding", {
                "evidence_ref": evidence_ref,
                "adapter_binding_record_id": adapter["record_id"],
            }),
            accepted_evidence_binding_id=str(
                adapter["accepted_evidence_binding"]
            ),
            evidence_ref=evidence_ref,
            source_family_id="story_scoped_publication_evidence_v1",
            adapter_id=str(adapter["adapter_id"]),
            adapter_binding_record_id=str(adapter["record_id"]),
            document_id=str(document["document_id"]),
            source_native_id=str(document["source_native_id"]),
            content_sha256=str(document["content_sha256"]),
            source_native_status="eligible",
            evidence_state="exact",
            consumer_permission=(
                "PUBLIC_CLAIM_ALLOWED"
                if row.get("public_claim_allowed") is True
                else "REPORTING_NOT_ALLOWED"
            ),
            dqr_reporting_allowed=(
                (source.get("claim_permissions") or {}).get(
                    "reporting_allowed"
                )
                is True
            ),
            receipt={
                "receipt_kind": "git_artifact",
                "exact_verified": True,
                **pool_receipt.as_dict(),
                "pool_id": pool["pool_id"],
                "pool_logical_hash": pool["logical_hash"],
                "candidate_evidence_hash": source["evidence_hash"],
                "claim_id": claim_id,
            },
        )
        trusted_evidence_index[evidence_ref] = binding
        bindings.append(binding)
        citations = [
            {
                "url": url,
                "source_document_id": document["document_id"],
            }
            for url in (source.get("citation_map") or {}).get(claim_id, [])
        ]
        claim, decision = build_governed_claim(
            authority=authority,
            trusted_evidence_index=trusted_evidence_index,
            claim_id=claim_id,
            claim_type="numeric_observation",
            statement=None,
            structured_payload={"source_native_claim_id": claim_id},
            source_document_ids=[document["document_id"]],
            evidence_refs=[evidence_ref],
            observed_at_utc=row.get("observation_time_utc"),
            event_time_utc=None,
            published_at_utc=row.get("observation_time_utc"),
            known_at_utc=str(
                row.get("known_at_utc") or source.get("known_at_utc")
            ),
            revision_at_utc=None,
            citations=citations,
            entities=(),
            geographies=(),
            limitations=[
                str(
                    row.get("authority_scope")
                    or "v1_numeric_compatibility_projection"
                )
            ],
            numeric={
                "metric": row.get("metric"),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "transformation": row.get("calculation") or "source_native_value",
                "numeric_authority_class": row.get("source_authority"),
            },
            market_evidence_refs=(),
            judgment_record=None,
        )
        claims.append(claim)
        decisions.append(decision)
    evidence_refs = sorted(binding["evidence_ref"] for binding in bindings)
    values = {
        "candidate_id": str(source["candidate_id"]),
        "story_id": str(source["story_id"]),
        "cluster_id": str(source["cluster_id"]),
        "update_chain_id": str(source["update_chain_id"]),
        "source_native_ids": [str(source["source_packet_id"])],
        "source_family_ids": ["story_scoped_publication_evidence_v1"],
        "adapter_id": str(adapter["adapter_id"]),
        "evidence_requirement_profile_id": "numeric_economic_release",
        "capabilities": {
            "claim_capabilities": ["numeric_observation"],
            "numeric_evidence_required": True,
            "nonnumeric_evidence_supported": False,
        },
        "title": source["title"],
        "summary": source["summary"],
        "relationship": (
            "initial_event"
            if source.get("relationship") == "new_phase"
            else source.get("relationship")
        ),
        "claims": claims,
        "claim_authority_decisions": decisions,
        "numeric_claims": claims,
        "source_documents": documents,
        "entities": [],
        "geographies": [],
        "evidence_refs": evidence_refs,
        "event_evidence_refs": evidence_refs,
        "evidence_bindings": bindings,
        "market_evidence_records": [],
        "authority_state": "OFFICIAL_VERIFIED",
        "reporting_allowed": True,
        "evidence_state": "exact",
        "event_time_utc": source.get("event_time_utc"),
        "observation_time_utc": source.get("event_time_utc"),
        "published_at_utc": source.get("event_time_utc"),
        "known_at_utc": source.get("known_at_utc"),
        "revision_at_utc": None,
        "cutoff_time_utc": None,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": [
                "v1_exact_claim_document_citation_projection_complete"
            ],
        },
        "freshness": source.get("freshness") or {
            "availability": "UNAVAILABLE",
            "value": None,
        },
        "ranking_inputs": source.get("ranking_inputs") or {},
        "limitations": [
            *(str(value) for value in source.get("limitations") or []),
            "v1_authority_bound_to_exact_accepted_pool_receipt",
            "candidate_contract_grants_no_publication_authority",
        ],
        "blockers": list(source.get("blockers") or []),
        "publication_authority": False,
        "public_write_allowed": False,
        "global_dqr_override": False,
        "producer_binding": {
            "v1_pool_receipt": pool_receipt.as_dict(),
            "v1_pool_id": pool["pool_id"],
            "v1_pool_logical_hash": pool["logical_hash"],
        },
    }
    return build_candidate(values), pool_receipt.as_dict()


def _latest_real_route_records(
    bridge: GovernedUpstreamBridgeV1,
) -> list[dict[str, Any]]:
    records = [
        bridge.select_record(
            target_id="DBH2_FEDERAL_REGISTER_SEC",
            provider_record_type="federal_register_document",
            cutoff_utc="2026-07-14T00:00:00Z",
        ),
        bridge.select_record(
            target_id="DBH2_SEC_MSFT_SUBMISSIONS",
            provider_record_type="sec_filing",
            cutoff_utc="2026-07-14T00:00:00Z",
            required_status="filed",
        ),
        _select_fomc_minutes(
            bridge,
            cutoff_utc="2026-07-14T00:00:00Z",
        ),
        bridge.select_record(
            target_id="DBH2_USGS_SIGNIFICANT_GLOBAL",
            provider_record_type="usgs_event",
            cutoff_utc="2026-07-14T00:00:00Z",
            required_status="reviewed",
        ),
    ]
    snapshot, _entity = bridge.select_snapshot_entity(
        cutoff_utc="2026-07-14T00:00:00Z"
    )
    records.append(snapshot)
    return records


def _checkpoint_candidate(
    candidate: Mapping[str, Any],
    *,
    cutoff_utc: str,
) -> dict[str, Any]:
    value = dict(candidate)
    value["cutoff_time_utc"] = cutoff_utc
    if value.get("evidence_requirement_profile_id") == "numeric_economic_release":
        known_at = _parse_utc(str(value["known_at_utc"]))
        cutoff = _parse_utc(cutoff_utc)
        age_hours = round((cutoff - known_at).total_seconds() / 3600, 3)
        maximum_age_hours = 36.0
        value["freshness"] = {
            "availability": "AVAILABLE",
            "age_hours": age_hours,
            "evaluated_at_utc": cutoff_utc,
            "max_age_hours": maximum_age_hours,
            "stale": age_hours > maximum_age_hours,
        }
        evidence_refs = list(value.get("evidence_refs") or [])
        ranking_inputs = dict(value.get("ranking_inputs") or {})
        ranking_inputs.update({
            "source_authority": {
                "availability": "AVAILABLE",
                "score": 100.0,
                "reason_codes": ["exact_registered_authority_chain"],
                "evidence_refs": evidence_refs,
            },
            "evidence_completeness": {
                "availability": "AVAILABLE",
                "score": 100.0,
                "reason_codes": ["exact_claim_document_citation_lineage"],
                "evidence_refs": evidence_refs,
            },
            "surprise": {
                "availability": "EXPLICIT_ZERO",
                "score": 0,
                "reason_codes": ["explicit_governed_zero_no_surprise_measure"],
                "evidence_refs": evidence_refs,
            },
            "audience_relevance": {
                "availability": "UNAVAILABLE",
                "score": None,
                "reason_codes": ["not_available_from_governed_artifact"],
                "evidence_refs": [],
            },
            "freshness": {
                "availability": "AVAILABLE",
                "score": max(0.0, round(100.0 * (1.0 - age_hours / maximum_age_hours), 3)),
                "reason_codes": [
                    "stale_at_checkpoint"
                    if age_hours > maximum_age_hours
                    else "within_registered_freshness_window"
                ],
                "evidence_refs": evidence_refs,
            },
        })
        value["ranking_inputs"] = ranking_inputs
        if age_hours > maximum_age_hours:
            value["blockers"] = sorted({
                *(str(row) for row in value.get("blockers") or []),
                "stale_at_checkpoint",
            })
    return build_candidate(value)


def build_continuous_shadow_operation(
    *,
    repo_root: Path,
    upstream_root: Path,
    observed_upstream_head: str = UPSTREAM_HEAD,
) -> dict[str, Any]:
    authority = load_governed_registry_authority(repo_root=repo_root)
    bridge = GovernedUpstreamBridgeV1(
        root=upstream_root,
        observed_head=observed_upstream_head,
    )
    bridge.verify_all_local_artifacts()
    bridge_packet = bridge.authority_packet()
    bridge_packet = {
        **bridge_packet,
        "logical_hash": logical_hash(bridge_packet),
    }
    trusted_evidence_index: dict[str, Mapping[str, Any]] = {}

    correction_versions = _all_versions(
        bridge,
        stable_record_id=CORRECTION_STABLE_ID,
    )
    if len(correction_versions) != 2:
        raise GovernedArtifactBlocked(
            "governed_correction_chain_version_count_invalid"
        )
    relationships = bridge.relationships_for_record(
        stable_record_id=CORRECTION_STABLE_ID
    )
    if not any(row.get("relation_type") == "corrects" for row in relationships):
        raise GovernedArtifactBlocked("governed_correction_relationship_missing")
    all_candidates = [
        _build_dbh2_candidate(
            record=correction_versions[0],
            authority=authority,
            bridge_packet=bridge_packet,
            trusted_evidence_index=trusted_evidence_index,
            relationship="initial_event",
        ),
        _build_dbh2_candidate(
            record=correction_versions[1],
            authority=authority,
            bridge_packet=bridge_packet,
            trusted_evidence_index=trusted_evidence_index,
            relationship="correction",
        ),
    ]
    for record in _latest_real_route_records(bridge):
        all_candidates.append(_build_dbh2_candidate(
            record=record,
            authority=authority,
            bridge_packet=bridge_packet,
            trusted_evidence_index=trusted_evidence_index,
        ))
    numeric, v1_receipt = _build_v1_candidate(
        upstream_root=upstream_root,
        observed_head=observed_upstream_head,
        authority=authority,
        trusted_evidence_index=trusted_evidence_index,
    )
    all_candidates.append(numeric)

    seen_candidate_ids: set[str] = set()
    previously_assigned: list[Mapping[str, Any]] = []
    checkpoint_ledger = []
    pools = []
    shadow_decisions = []
    for checkpoint_index, cutoff in enumerate(CHECKPOINTS):
        available = [
            _checkpoint_candidate(candidate, cutoff_utc=cutoff)
            for candidate in all_candidates
            if _parse_utc(str(candidate["known_at_utc"])) <= _parse_utc(cutoff)
        ]
        available.sort(key=lambda row: row["candidate_id"])
        consumed_refs = {
            ref
            for candidate in available
            for ref in candidate.get("evidence_refs") or []
        }
        checkpoint_index_bindings = {
            ref: trusted_evidence_index[ref]
            for ref in sorted(consumed_refs)
        }
        family_ids = {
            family_id
            for candidate in available
            for family_id in candidate.get("source_family_ids") or []
        }
        pool = build_governed_pool(
            authority=authority,
            trusted_evidence_index=checkpoint_index_bindings,
            candidates=available,
            source_family_ids=sorted(family_ids),
            generated_at_utc=cutoff,
            cutoff_time_utc=cutoff,
            upstream_binding={
                "repository": "fatcat2109/Headline-Raw-data-json",
                "branch": "main",
                "observed_head": observed_upstream_head,
                "dbh2_bridge_receipt": bridge_packet,
                "v1_pool_receipt": v1_receipt,
            },
            category_blockers={},
        )
        blockers = validate_governed_pool(
            pool,
            authority=authority,
            trusted_evidence_index=checkpoint_index_bindings,
        )
        if blockers:
            raise ValueError(
                "continuous_checkpoint_pool_invalid:" + ",".join(blockers)
            )
        current_ids = {candidate["candidate_id"] for candidate in available}
        new_ids = sorted(current_ids - seen_candidate_ids)
        unchanged_ids = sorted(current_ids.intersection(seen_candidate_ids))
        checkpoint_ledger.append({
            "checkpoint_index": checkpoint_index,
            "prior_cutoff_utc": (
                CHECKPOINTS[checkpoint_index - 1]
                if checkpoint_index
                else None
            ),
            "cutoff_utc": cutoff,
            "new_candidate_ids": new_ids,
            "unchanged_candidate_ids": unchanged_ids,
            "available_candidate_count": len(available),
            "new_candidate_count": len(new_ids),
            "future_candidate_ids": sorted({
                candidate["candidate_id"] for candidate in all_candidates
            } - current_ids),
            "idempotency_key": logical_hash({
                "cutoff_utc": cutoff,
                "candidate_ids": sorted(current_ids),
                "evidence_refs": sorted(consumed_refs),
            }),
        })
        schedule_date = cutoff[:10]
        checkpoint_decisions = []
        for window in FIVE_WINDOWS:
            decision = evaluate_v2_window_decision(
                window=window,
                schedule_date=schedule_date,
                pool=pool,
                previously_assigned=previously_assigned,
                no_publication_boundary=True,
            )
            checkpoint_decisions.append(decision)
            if decision["selected_candidate_id"]:
                selected = next(
                    candidate
                    for candidate in available
                    if candidate["candidate_id"]
                    == decision["selected_candidate_id"]
                )
                previously_assigned.append(selected)
        shadow_decisions.append({
            "checkpoint_index": checkpoint_index,
            "cutoff_utc": cutoff,
            "candidate_pool_id": pool["pool_id"],
            "decisions": checkpoint_decisions,
            "internal_assignment_count": sum(
                row["selected_candidate_id"] is not None
                for row in checkpoint_decisions
            ),
            "publication_count": 0,
            "public_write_count": 0,
        })
        pools.append(pool)
        seen_candidate_ids.update(current_ids)

    clusters = cluster_candidates(all_candidates)
    correction_cluster = next(
        cluster
        for cluster in clusters
        if {
            correction_candidate["candidate_id"]
            for correction_candidate in all_candidates[:2]
        }.issubset(set(cluster["candidate_ids"]))
    )
    if [
        row["relationship"] for row in correction_cluster["relationships"]
    ] != ["initial_event", "correction"]:
        raise ValueError("governed_correction_chain_not_exercised")
    final = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": CHECKPOINTS[-1],
        "operation_mode": "DETERMINISTIC_LOCAL_CONTINUOUS_SHADOW",
        "network_intake_performed": False,
        "continuous_live_intake_claimed": False,
        "registry_authority_packet": authority.authority_packet(),
        "local_dbh2_receipt": bridge_packet,
        "trusted_evidence_index": dict(sorted(trusted_evidence_index.items())),
        "checkpoint_ledger": checkpoint_ledger,
        "multi_cutoff_candidate_pools": pools,
        "clustering_update_chain_ledger": {
            "clusters": clusters,
            "governed_correction_relationships": relationships,
            "exercised_relationships": ["initial_event", "correction"],
            "correction_cluster_id": correction_cluster["cluster_id"],
        },
        "five_window_shadow_decisions": shadow_decisions,
        "summary": {
            "checkpoint_count": len(CHECKPOINTS),
            "window_decision_count": len(CHECKPOINTS) * len(FIVE_WINDOWS),
            "real_candidate_version_count": len(all_candidates),
            "real_family_count": 6,
            "governed_update_chain_count": 1,
            "internal_assignment_count": len(previously_assigned),
            "publication_count": 0,
            "public_write_count": 0,
            "same_cutoff_duplicate_assignment_count": 0,
        },
        "calibration_state": "UNCALIBRATED_FOUNDATION",
        "publication_authority": False,
        "public_write_performed": False,
        "upstream_write_performed": False,
    }
    final["logical_hash"] = logical_hash(final)
    return final
