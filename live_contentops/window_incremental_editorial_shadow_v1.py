"""Registry-driven evidence-window intake and canonical editorial shadow handoff.

This module performs no network, credential, scheduler, publication, or public
write operation.  Source-specific selection is carried by append-only registry
records; the scanner itself advances one generic four-part cursor.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    build_content_evidence_packet_v3,
    validate_content_evidence_packet_v3,
)
from live_contentops.cc_evidence_bridge_v2 import validate_evidence_packet
from live_contentops.cross_domain_continuous_shadow_v1 import (
    _build_v1_candidate,
    _utc,
)
from live_contentops.editorial_review_orchestrator_v2 import (
    ROLE_ORDER,
    run_editorial_review,
)
from live_contentops.editorial_visual_research_v2 import (
    evaluate_visual_composition,
)
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.governed_upstream_bridge_v1 import (
    GovernedArtifactBlocked,
    GovernedUpstreamBridgeV1,
)
from live_contentops.universal_evidence_receipt_verifier_v1 import (
    EvidenceReceiptVerifierV1,
    VerifiedEvidenceIndexV1,
    verify_runtime_implementation,
)
from live_contentops.universal_governed_registry_v1 import (
    GovernedRegistrySnapshotV1,
    build_governed_claim,
    build_governed_pool,
    load_governed_registry_authority,
    logical_hash,
    validate_governed_pool,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    assign_generic_id,
    build_candidate,
    evaluate_v2_window_decision,
)


SCHEMA_VERSION = (
    "contentops.verified_evidence_window_incremental_editorial_shadow.v1"
)
FIVE_WINDOWS = (
    {"window_id": "asia_open", "target_cutoff_utc": "00:30:00"},
    {"window_id": "europe_open", "target_cutoff_utc": "07:30:00"},
    {"window_id": "us_open", "target_cutoff_utc": "13:30:00"},
    {"window_id": "us_midday", "target_cutoff_utc": "17:00:00"},
    {"window_id": "us_close", "target_cutoff_utc": "22:30:00"},
)
DEFAULT_HISTORY_DATES = (
    "2026-07-10",
    "2026-07-11",
    "2026-07-12",
    "2026-07-13",
    "2026-07-14",
    "2026-07-15",
)
INITIAL_CURSOR = (
    "2026-07-09T23:59:59Z",
    "",
    "",
    "",
)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_missing")
    return parsed.astimezone(timezone.utc)


def _cursor(
    *,
    known_at_utc: str,
    target_id: str,
    stable_record_id: str,
    version_id: str,
) -> tuple[str, str, str, str]:
    return (
        known_at_utc,
        target_id,
        stable_record_id,
        version_id,
    )


def _path_value(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


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
        "known_at_utc": record["known_at_utc"],
        "target_id": record["target_id"],
    }


def adapt_verified_dbh2_record_v2(
    *,
    record: Mapping[str, Any],
    route: Mapping[str, Any],
    authority: GovernedRegistrySnapshotV1,
    verifier: EvidenceReceiptVerifierV1,
    relationship: str,
) -> dict[str, Any]:
    """Adapt one verifier-bound DBH2 record using only registry route fields."""

    family_id = str(route["source_family_id"])
    adapter_id = str(route["adapter_id"])
    discovery = route["discovery_contract"]
    document = _source_document(record)
    binding = dict(verifier.verify_dbh2_record_binding(
        record=record,
        source_family_id=family_id,
        adapter_id=adapter_id,
    ))
    document = {
        **document,
        "document_id": binding["document_id"],
        "source_native_id": binding["source_native_id"],
        "authorized_urls": list(binding["receipt"]["authorized_urls"]),
        "content_sha256": binding["content_sha256"],
    }
    evidence_ref = str(binding["evidence_ref"])
    payload = {
        output: _path_value(record, str(path))
        for output, path in sorted(
            (discovery.get("structured_payload_fields") or {}).items()
        )
    }
    citations = [
        {
            "source_document_id": document["document_id"],
            "url": url,
            "citation_state": "EXACT_SOURCE_NATIVE_URL",
        }
        for url in document["authorized_urls"]
    ]
    claim_type = str(discovery["claim_type"])
    claim_id = assign_generic_id("claim", {
        "stable_record_id": record["stable_record_id"],
        "version_id": record["version_id"],
        "claim_type": claim_type,
    })
    event_time = record.get("published_at_utc") or record["known_at_utc"]
    claim, decision = build_governed_claim(
        authority=authority,
        trusted_evidence_index=verifier.index,
        claim_id=claim_id,
        claim_type=claim_type,
        evidence_refs=[evidence_ref],
        statement=str(discovery["statement"]),
        structured_payload=payload,
        source_document_ids=[document["document_id"]],
        observed_at_utc=(
            event_time if discovery.get("observation_time_from_event") else None
        ),
        event_time_utc=event_time,
        published_at_utc=record.get("published_at_utc"),
        known_at_utc=record["known_at_utc"],
        revision_at_utc=_utc(str(record.get("updated_at") or "")),
        citations=citations,
        entities=list(discovery.get("entities") or []),
        geographies=[
            str(value)
            for value in (
                _path_value(record, str(discovery["geography_field"])),
            )
            if value not in (None, "")
        ],
        limitations=list(discovery.get("limitations") or []),
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
        "source_family_ids": [family_id],
        "adapter_id": adapter_id,
        "adapter_binding_record_id": route["record_id"],
        "evidence_requirement_profile_id": discovery["profile_id"],
        "capabilities": {
            "claim_capabilities": [claim_type],
            "numeric_evidence_required": False,
            "nonnumeric_evidence_supported": True,
        },
        "title": str(record.get("title") or record["provider_record_id"]),
        "summary": str(discovery["statement"]),
        "relationship": relationship,
        "delta_signals": {
            "verified_new_version": relationship != "initial_event",
            "correction": relationship == "correction",
        },
        "claims": [claim],
        "claim_authority_decisions": [decision],
        "numeric_claims": [],
        "source_documents": [document],
        "entities": list(discovery.get("entities") or []),
        "geographies": [
            str(value)
            for value in (
                _path_value(record, str(discovery["geography_field"])),
            )
            if value not in (None, "")
        ],
        "evidence_refs": [evidence_ref],
        "event_evidence_refs": [evidence_ref],
        "evidence_bindings": [binding],
        "market_evidence_records": [],
        "authority_state": claim["authority_class"],
        "reporting_allowed": False,
        "evidence_state": str(discovery["evidence_state"]),
        "event_time_utc": event_time,
        "observation_time_utc": (
            event_time if discovery.get("observation_time_from_event") else None
        ),
        "published_at_utc": record.get("published_at_utc"),
        "known_at_utc": record["known_at_utc"],
        "revision_at_utc": _utc(str(record.get("updated_at") or "")),
        "cutoff_time_utc": None,
        "evidence_completeness": {
            "availability": "AVAILABLE",
            "value": 1.0,
            "reason_codes": ["verifier_bound_exact_dbh2_record"],
        },
        "freshness": {
            "availability": "UNAVAILABLE",
            "value": None,
            "reason_codes": ["registry_grants_no_reporting_freshness"],
        },
        "ranking_inputs": {
            "source_authority": {
                "availability": "AVAILABLE",
                "score": 100.0,
                "reason_codes": ["verifier_bound_official_source"],
                "evidence_refs": [evidence_ref],
            },
        },
        "limitations": [
            *list(discovery.get("limitations") or []),
            "context_only_permission_ceiling",
            "candidate_grants_no_publication_authority",
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


def adapt_verified_v1_candidate_pool_v2(
    *,
    route: Mapping[str, Any],
    authority: GovernedRegistrySnapshotV1,
    verifier: EvidenceReceiptVerifierV1,
    upstream_root: Path,
    observed_upstream_head: str,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    """Compatibility adapter whose authority is produced by exact Git receipts."""

    return _build_v1_candidate(
        upstream_root=upstream_root,
        observed_head=observed_upstream_head,
        authority=authority,
        verifier=verifier,
        trusted_evidence_index=verifier.index,
    )


def enabled_discovery_routes(
    authority: GovernedRegistrySnapshotV1,
) -> tuple[Mapping[str, Any], ...]:
    records = [
        row
        for row in authority.registries["adapter_source_bindings"]["records"]
        if row.get("enabled") is True
        and isinstance(row.get("discovery_contract"), Mapping)
    ]
    latest: dict[str, Mapping[str, Any]] = {}
    for record in records:
        latest[str(record["adapter_id"])] = record
    return tuple(latest[key] for key in sorted(latest))


def _read_dbh2_increment(
    *,
    bridge: GovernedUpstreamBridgeV1,
    route: Mapping[str, Any],
    prior_cursor: tuple[str, str, str, str],
    cutoff_utc: str,
) -> list[dict[str, Any]]:
    discovery = route["discovery_contract"]
    statuses = tuple(str(value) for value in discovery["accepted_statuses"])
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
             WHERE target_id = ? AND provider_record_type = ?
            """,
            [discovery["target_id"], discovery["provider_record_type"]],
        ).fetchall()
        columns = [value[0] for value in connection.description]
    finally:
        connection.close()
    cutoff = _parse_utc(cutoff_utc)
    result: list[dict[str, Any]] = []
    for raw in rows:
        record = dict(zip(columns, raw))
        if str(record.get("status")) not in statuses:
            continue
        known = _utc(
            str(record.get("updated_at") or record.get("published_at") or "")
        )
        if not known or _parse_utc(known) > cutoff:
            continue
        record["known_at_utc"] = known
        record["published_at_utc"] = _utc(
            str(record.get("published_at") or "")
        )
        record["payload"] = json.loads(record.pop("payload_json") or "{}")
        record_cursor = _cursor(
            known_at_utc=known,
            target_id=str(record["target_id"]),
            stable_record_id=str(record["stable_record_id"]),
            version_id=str(record["version_id"]),
        )
        if record_cursor > prior_cursor:
            result.append(record)
    result.sort(key=lambda value: _cursor(
        known_at_utc=str(value["known_at_utc"]),
        target_id=str(value["target_id"]),
        stable_record_id=str(value["stable_record_id"]),
        version_id=str(value["version_id"]),
    ))
    return result


def scan_verified_increment(
    *,
    bridge: GovernedUpstreamBridgeV1,
    routes: Sequence[Mapping[str, Any]],
    prior_cursor: tuple[str, str, str, str],
    cutoff_utc: str,
) -> tuple[list[tuple[Mapping[str, Any], dict[str, Any]]], tuple[str, str, str, str]]:
    """Scan every enabled DBH2 route after one generic stable cursor."""

    discovered: list[tuple[Mapping[str, Any], dict[str, Any]]] = []
    for route in routes:
        if route["discovery_contract"]["kind"] != "DBH2_RECORDS":
            continue
        discovered.extend(
            (route, record)
            for record in _read_dbh2_increment(
                bridge=bridge,
                route=route,
                prior_cursor=prior_cursor,
                cutoff_utc=cutoff_utc,
            )
        )
    discovered.sort(key=lambda item: _cursor(
        known_at_utc=str(item[1]["known_at_utc"]),
        target_id=str(item[1]["target_id"]),
        stable_record_id=str(item[1]["stable_record_id"]),
        version_id=str(item[1]["version_id"]),
    ))
    cursor = prior_cursor
    if discovered:
        last = discovered[-1][1]
        cursor = _cursor(
            known_at_utc=str(last["known_at_utc"]),
            target_id=str(last["target_id"]),
            stable_record_id=str(last["stable_record_id"]),
            version_id=str(last["version_id"]),
        )
    return discovered, cursor


def build_candidate_bound_evidence_packet(
    candidate: Mapping[str, Any],
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Build a V2 packet from one assigned candidate's exact evidence lineage."""

    numeric_claims = []
    citation_map: dict[str, list[str]] = {}
    for claim in candidate.get("claims") or []:
        claim_id = str(claim["claim_id"])
        citation_map[claim_id] = sorted({
            str(value["url"])
            for value in claim.get("citations") or []
            if value.get("url")
        })
        numeric = claim.get("numeric")
        if not isinstance(numeric, Mapping):
            continue
        numeric_claims.append({
            "claim_id": claim_id,
            "metric": numeric["metric"],
            "value": numeric["value"],
            "unit": numeric["unit"],
            "observation_time_utc": claim.get("observed_at_utc"),
            "source_id": candidate["adapter_id"],
            "source_artifact_ref": claim["evidence_refs"][0],
            "public_claim_allowed": (
                claim.get("permission_state") == "PUBLIC_CLAIM_ALLOWED"
                and candidate.get("reporting_allowed") is True
            ),
            "llm_numeric_authority": False,
        })
    allow = (
        candidate.get("reporting_allowed") is True
        and bool(numeric_claims)
        and all(row["public_claim_allowed"] for row in numeric_claims)
    )
    packet = {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": assign_generic_id("cc-evidence", {
            "candidate_id": candidate["candidate_id"],
            "evidence_refs": candidate["evidence_refs"],
        }),
        "generated_at_utc": generated_at_utc,
        "as_of_utc": generated_at_utc,
        "story_window": {
            "hours": 24,
            "start_utc": None,
            "end_utc": generated_at_utc,
        },
        "events": [],
        "official_source_documents": list(candidate["source_documents"]),
        "numeric_claims": numeric_claims,
        "market_snapshots": [],
        "source_state": {
            "candidate_id": candidate["candidate_id"],
            "authority_state": candidate["authority_state"],
            "reporting_allowed": candidate["reporting_allowed"],
        },
        "candidate_visual_inputs": [],
        "citation_map": citation_map,
        "provenance": {
            "candidate_logical_hash": candidate["logical_hash"],
            "evidence_refs": list(candidate["evidence_refs"]),
            "evidence_binding_hashes": [
                value["logical_hash"]
                for value in candidate["evidence_bindings"]
            ],
        },
        "public_claim_permissions": {
            "numeric_claims_allowed": allow,
            "narrative_synthesis_allowed": allow,
            "llm_numeric_authority": False,
            "decision": "ALLOW" if allow else "BLOCK",
        },
        "blockers": [] if allow else ["candidate_public_claim_permission_blocked"],
        "bridge_safety": {
            "source_repo_modified": False,
            "network_call_made": False,
            "public_write_performed": False,
        },
    }
    packet["validation_blockers"] = validate_evidence_packet(packet)
    packet["status"] = (
        "PASS_CONTRACT_BLOCKED_PUBLICATION"
        if not packet["validation_blockers"]
        else "FAIL_SCHEMA"
    )
    return packet


def _shadow_structured_role_reviewer(
    role: str,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive a role decision from the exact V3 packet and final render."""

    packet = context["evidence_packet"]
    article = context["article"]
    request = context["request"]
    graph = packet.get("governed_claim_graph") or {}
    claim_map = {
        str(row["claim_id"]): row
        for row in graph.get("claims") or []
        if row.get("claim_id")
    }
    approved = {
        str(value) for value in graph.get("approved_claim_ids") or []
    }
    used = {
        str(value) for value in article.get("claim_ids_used") or []
    }
    common_checks = {
        "v3_packet_hash_bound": bool(packet.get("logical_hash")),
        "claim_set_governed": bool(used) and used.issubset(approved),
    }
    citations = article.get("claim_citations") or {}
    authority_used = article.get("claim_authority_used") or {}
    permission_used = article.get("claim_permissions_used") or {}
    role_checks: dict[str, dict[str, bool]] = {
        "assignment_editor": {
            "assignment_mode_bound": (
                request.get("article_mode") == article.get("article_mode")
            ),
            "story_type_present": bool(request.get("story_type")),
        },
        "evidence_planner": {
            "packet_contract_valid": not validate_content_evidence_packet_v3(
                packet
            ),
            "claim_lineage_complete": all(
                claim_map[claim_id].get("evidence_refs")
                and claim_map[claim_id].get("source_document_ids")
                for claim_id in used & set(claim_map)
            ),
        },
        "reporter_writer": {
            "body_claim_set_exact": {
                str(value)
                for value in article.get("body_claim_ids_used") or []
            } == used,
            "governed_statements_present": all(
                str(claim_map[claim_id].get("statement") or "").strip()
                for claim_id in used & set(claim_map)
            ),
        },
        "quantitative_editor": {
            "numeric_authority_not_delegated": (
                article.get("numeric_claims_from_llm") is False
            ),
            "numeric_claims_typed": all(
                claim_map[claim_id].get("claim_type")
                == "numeric_observation"
                for claim_id in context.get("numeric_claim_ids") or []
            ),
        },
        "visual_editor": {
            "visual_decision_passed": (
                context["visual_decision"].get("status") == "PASS"
            ),
            "visuals_do_not_claim_authority": (
                not article.get("visual_claim_ids_used")
            ),
        },
        "copy_editor": {
            "final_render_present": bool(article.get("rendered_body")),
            "single_financial_disclaimer": (
                str(article.get("rendered_body") or "")
                .casefold()
                .count("not financial advice")
                == 1
            ),
        },
        "platform_editor": {
            "hard_truncation_absent": (
                article.get("hard_truncation_used") is False
            ),
            "draft_has_no_publication_authority": (
                article.get("publication_authority") is False
            ),
        },
        "adversarial_final_reviewer": {
            "prior_roles_clear": not context.get("accumulated_blockers"),
            "freshness_decision_passed": (
                context["freshness_decision"].get("decision") == "PASS"
            ),
            "citation_bindings_exact": all(
                sorted({
                    str(value)
                    for value in citations.get(claim_id) or []
                    if value
                })
                == sorted({
                    str(row["url"])
                    for row in claim_map[claim_id].get("citations") or []
                    if row.get("url")
                })
                for claim_id in used & set(claim_map)
            ),
            "authority_and_permission_not_upgraded": all(
                authority_used.get(claim_id)
                == claim_map[claim_id].get("authority_class")
                and permission_used.get(claim_id)
                == claim_map[claim_id].get("permission_state")
                for claim_id in used & set(claim_map)
            ),
        },
    }
    checks = {**common_checks, **role_checks[role]}
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "decision": "PASS" if not failed else "BLOCK",
        "publication_authority": False,
        "reviewer_kind": "DETERMINISTIC_EVIDENCE_BOUND_ROLE_CHECK",
        "review_basis": {
            "role": role,
            "checks_derived_from_final_render_and_v3_packet": True,
        },
        "reviewed_claim_ids": sorted(used),
        "evidence_packet_logical_hash": packet.get("logical_hash"),
        "checks": checks,
        "blockers": failed,
    }


def build_canonical_editorial_shadow_handoff(
    candidate: Mapping[str, Any],
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    v2_packet = build_candidate_bound_evidence_packet(
        candidate,
        generated_at_utc=generated_at_utc,
    )
    packet = build_content_evidence_packet_v3(
        candidate,
        generated_at_utc=generated_at_utc,
        v2_packet=v2_packet,
    )
    validation_blockers = validate_content_evidence_packet_v3(packet)
    if validation_blockers:
        raise ValueError(
            "canonical_editorial_v3_packet_invalid:"
            + ",".join(validation_blockers)
        )
    approval_by_id = {
        str(row["claim_id"]): row
        for row in packet["governed_claim_graph"]["approval_decisions"]
    }
    source_authority_adjudication = [
        {
            "claim_id": str(claim["claim_id"]),
            "claim_type": claim.get("claim_type"),
            "source_document_ids": list(
                claim.get("source_document_ids") or []
            ),
            "evidence_refs": list(claim.get("evidence_refs") or []),
            "authority_class": claim.get("authority_class"),
            "permission_state": claim.get("permission_state"),
            "approved_for_reporting": approval_by_id[
                str(claim["claim_id"])
            ]["approved_for_reporting"],
            "blockers": list(
                approval_by_id[str(claim["claim_id"])]["blockers"]
            ),
        }
        for claim in packet["governed_claim_graph"]["claims"]
    ]
    if packet["generic_claim_permissions"]["decision"] != "ALLOW":
        return {
            "schema_version": "contentops.canonical_editorial_shadow_handoff.v1",
            "candidate_id": candidate["candidate_id"],
            "disposition": "ABSTAIN_CONTEXT_ONLY_OR_UNAUTHORIZED",
            "evidence_packet_contract": (
                "V3_GENERIC_WITH_EXACT_V2_COMPATIBILITY_PROJECTION"
            ),
            "evidence_packet": packet,
            "source_authority_adjudication": source_authority_adjudication,
            "canonical_role_order": list(ROLE_ORDER),
            "editorial_review": None,
            "article": None,
            "publication_authority": False,
            "public_write_performed": False,
        }
    claim_map = {
        str(row["claim_id"]): row
        for row in packet["governed_claim_graph"]["claims"]
    }
    claim_ids = list(
        packet["governed_claim_graph"]["approved_claim_ids"]
    )
    approved = [claim_map[claim_id] for claim_id in claim_ids]
    statements = [
        str(claim.get("statement") or "").strip() for claim in approved
    ]
    lead_claim_ids = claim_ids[:1]
    lead_statement = statements[0] if statements else ""
    article = {
        "title": lead_statement,
        "summary": lead_statement,
        "rendered_body": (
            "\n\n".join(statements) + "\n\nNot financial advice."
        ),
        "article_mode": "evidence_bound_shadow_draft",
        "as_of_utc": generated_at_utc,
        "claim_ids_used": claim_ids,
        "title_claim_ids_used": lead_claim_ids,
        "summary_claim_ids_used": lead_claim_ids,
        "body_claim_ids_used": claim_ids,
        "claim_citations": {
            claim_id: sorted({
                str(row["url"])
                for row in claim_map[claim_id].get("citations") or []
                if row.get("url")
            })
            for claim_id in claim_ids
        },
        "claim_authority_used": {
            claim_id: claim_map[claim_id]["authority_class"]
            for claim_id in claim_ids
        },
        "claim_permissions_used": {
            claim_id: claim_map[claim_id]["permission_state"]
            for claim_id in claim_ids
        },
        "market_reaction_claim_ids": [
            claim_id
            for claim_id in claim_ids
            if claim_map[claim_id].get("claim_type") == "market_reaction"
        ],
        "numeric_claims_from_llm": False,
        "cross_asset_assertions": False,
        "hard_truncation_used": False,
        "quantitative_blockers": [],
        "publication_authority": False,
    }
    review_request = {
        "story_type": "evidence_bound_news_analysis",
        "article_mode": "analysis",
        "workflow_mode": "evidence_bound_shadow_draft",
        "market_sensitive": True,
        "fresh_material_delta": False,
    }
    article["article_mode"] = review_request["article_mode"]
    article["workflow_mode"] = review_request["workflow_mode"]
    freshness_decision = evaluate_freshness(packet, review_request)
    visual_decision = evaluate_visual_composition(
        list(packet.get("candidate_visual_inputs") or []),
        story_type=str(review_request["story_type"]),
    )
    review = run_editorial_review(
        request=review_request,
        packet=packet,
        article=article,
        freshness_decision=freshness_decision,
        visual_decision=visual_decision,
        structured_reviewer=_shadow_structured_role_reviewer,
    )
    return {
        "schema_version": "contentops.canonical_editorial_shadow_handoff.v1",
        "candidate_id": candidate["candidate_id"],
        "disposition": (
            "LOCAL_SHADOW_DRAFT_REVIEWED_NO_PUBLICATION"
            if review["status"] == "PASS"
            else "LOCAL_SHADOW_DRAFT_HELD"
        ),
        "evidence_packet_contract": (
            "V3_GENERIC_WITH_EXACT_V2_COMPATIBILITY_PROJECTION"
        ),
        "evidence_packet": packet,
        "source_authority_adjudication": source_authority_adjudication,
        "canonical_role_order": list(ROLE_ORDER),
        "editorial_review": review,
        "freshness_decision": freshness_decision,
        "visual_decision": visual_decision,
        "article": article,
        "publication_authority": False,
        "public_write_performed": False,
    }


def _relationship_for_record(
    *,
    bridge: GovernedUpstreamBridgeV1,
    record: Mapping[str, Any],
    prior_versions: Sequence[Mapping[str, Any]],
) -> str:
    if not prior_versions:
        return "initial_event"
    relationships = bridge.relationships_for_record(
        stable_record_id=str(record["stable_record_id"])
    )
    if any(
        value.get("relation_type") == "corrects"
        and str(record["version_id"]) in {
            str(value.get("from_version_id")),
            str(value.get("to_version_id")),
        }
        for value in relationships
    ):
        return "correction"
    return "material_update"


def build_historical_update_probe(
    *,
    bridge: GovernedUpstreamBridgeV1,
    routes: Sequence[Mapping[str, Any]],
    authority: GovernedRegistrySnapshotV1,
    verifier: EvidenceReceiptVerifierV1,
) -> dict[str, Any]:
    """Prove that a later governed version re-enters through the same cursor."""

    initial_rows, first_cursor = scan_verified_increment(
        bridge=bridge,
        routes=routes,
        prior_cursor=("2015-07-20T00:00:00Z", "", "", ""),
        cutoff_utc="2015-07-22T00:00:00Z",
    )
    later_rows, second_cursor = scan_verified_increment(
        bridge=bridge,
        routes=routes,
        prior_cursor=first_cursor,
        cutoff_utc="2015-08-06T00:00:00Z",
    )
    initial_by_stable = {
        str(record["stable_record_id"]): (route, record)
        for route, record in initial_rows
    }
    later_by_stable = {
        str(record["stable_record_id"]): (route, record)
        for route, record in later_rows
    }
    matches = []
    for stable_id in sorted(set(initial_by_stable).intersection(later_by_stable)):
        first_route, first = initial_by_stable[stable_id]
        later_route, later = later_by_stable[stable_id]
        relationships = bridge.relationships_for_record(
            stable_record_id=stable_id
        )
        correction = next(
            (
                value
                for value in relationships
                if value.get("relation_type") == "corrects"
                and {
                    str(value.get("from_version_id")),
                    str(value.get("to_version_id")),
                }
                == {
                    str(first["version_id"]),
                    str(later["version_id"]),
                }
            ),
            None,
        )
        if correction is not None:
            matches.append(
                (first_route, first, later_route, later, correction)
            )
    if len(matches) != 1:
        raise ValueError("historical_governed_correction_match_not_unique")
    first_route, first, later_route, later, correction = matches[0]
    first_candidate = adapt_verified_dbh2_record_v2(
        record=first,
        route=first_route,
        authority=authority,
        verifier=verifier,
        relationship="initial_event",
    )
    later_candidate = adapt_verified_dbh2_record_v2(
        record=later,
        route=later_route,
        authority=authority,
        verifier=verifier,
        relationship="correction",
    )
    return {
        "schema_version": "contentops.historical_incremental_update_probe.v1",
        "first_cursor": list(first_cursor),
        "second_cursor": list(second_cursor),
        "stable_record_id": first["stable_record_id"],
        "initial_version_id": first["version_id"],
        "reentered_version_id": later["version_id"],
        "initial_known_at_utc": first["known_at_utc"],
        "reentered_known_at_utc": later["known_at_utc"],
        "relationship": dict(correction),
        "candidate_relationships": [
            first_candidate["relationship"],
            later_candidate["relationship"],
        ],
        "candidate_ids": [
            first_candidate["candidate_id"],
            later_candidate["candidate_id"],
        ],
        "later_version_reentered": True,
        "duplicate_discovery_count": 0,
    }


def build_window_incremental_editorial_shadow(
    *,
    repo_root: Path,
    upstream_root: Path,
    observed_upstream_head: str,
    history_dates: Sequence[str] = DEFAULT_HISTORY_DATES,
) -> dict[str, Any]:
    authority = load_governed_registry_authority(repo_root=repo_root)
    bridge = GovernedUpstreamBridgeV1(
        root=upstream_root,
        observed_head=observed_upstream_head,
    )
    bridge.verify_all_local_artifacts()
    verifier = EvidenceReceiptVerifierV1(
        authority=authority,
        primary_root=repo_root,
        upstream_root=upstream_root,
        observed_upstream_head=observed_upstream_head,
        bridge=bridge,
    )
    routes = enabled_discovery_routes(authority)
    if not routes:
        raise GovernedArtifactBlocked("governed_discovery_routes_missing")
    for route in routes:
        verify_runtime_implementation(
            repo_root=repo_root,
            observed_commit=authority.observed_commit,
            implementation_receipt=route["implementation_receipt"],
            expected_identity=str(route["implementation_identity"]),
        )
    historical_update_probe = build_historical_update_probe(
        bridge=bridge,
        routes=routes,
        authority=authority,
        verifier=verifier,
    )

    cursor = INITIAL_CURSOR
    candidates: list[dict[str, Any]] = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    versions_by_stable: dict[str, list[Mapping[str, Any]]] = {}
    seen_cursors: set[tuple[str, str, str, str]] = set()
    assigned: list[Mapping[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    pools: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    git_route_added = False
    git_receipt: Mapping[str, Any] | None = None

    for schedule_date in history_dates:
        for window in FIVE_WINDOWS:
            cutoff = f"{schedule_date}T{window['target_cutoff_utc']}Z"
            prior_cursor = cursor
            discovered, cursor = scan_verified_increment(
                bridge=bridge,
                routes=routes,
                prior_cursor=cursor,
                cutoff_utc=cutoff,
            )
            new_candidate_ids: list[str] = []
            for route, record in discovered:
                record_cursor = _cursor(
                    known_at_utc=str(record["known_at_utc"]),
                    target_id=str(record["target_id"]),
                    stable_record_id=str(record["stable_record_id"]),
                    version_id=str(record["version_id"]),
                )
                if record_cursor in seen_cursors:
                    raise ValueError("incremental_cursor_duplicate_discovery")
                seen_cursors.add(record_cursor)
                stable_id = str(record["stable_record_id"])
                prior_versions = versions_by_stable.setdefault(stable_id, [])
                relationship = _relationship_for_record(
                    bridge=bridge,
                    record=record,
                    prior_versions=prior_versions,
                )
                candidate = adapt_verified_dbh2_record_v2(
                    record=record,
                    route=route,
                    authority=authority,
                    verifier=verifier,
                    relationship=relationship,
                )
                prior_versions.append(record)
                candidates.append(candidate)
                candidates_by_id[candidate["candidate_id"]] = candidate
                new_candidate_ids.append(candidate["candidate_id"])

            for route in routes:
                discovery = route["discovery_contract"]
                if (
                    discovery["kind"] == "GIT_CANDIDATE_POOL"
                    and not git_route_added
                    and _parse_utc(str(discovery["known_at_utc"]))
                    <= _parse_utc(cutoff)
                ):
                    candidate, git_receipt = adapt_verified_v1_candidate_pool_v2(
                        route=route,
                        authority=authority,
                        verifier=verifier,
                        upstream_root=upstream_root,
                        observed_upstream_head=observed_upstream_head,
                    )
                    candidates.append(candidate)
                    candidates_by_id[candidate["candidate_id"]] = candidate
                    new_candidate_ids.append(candidate["candidate_id"])
                    git_route_added = True

            consumed_refs = sorted({
                str(ref)
                for candidate in candidates
                for ref in candidate.get("evidence_refs") or []
            })
            index = verifier.index.subset(consumed_refs)
            families = sorted({
                str(value)
                for candidate in candidates
                for value in candidate.get("source_family_ids") or []
            })
            pool = build_governed_pool(
                authority=authority,
                trusted_evidence_index=index,
                candidates=candidates,
                source_family_ids=families,
                generated_at_utc=cutoff,
                cutoff_time_utc=cutoff,
                upstream_binding={
                    "repository": "fatcat2109/Headline-Raw-data-json",
                    "branch": "main",
                    "observed_head": observed_upstream_head,
                    "later_observed_branch_head": bridge.current_branch_head,
                    "git_candidate_pool_receipt": (
                        git_receipt.as_dict()
                        if hasattr(git_receipt, "as_dict")
                        else git_receipt
                    ),
                },
                category_blockers={},
            )
            blockers = validate_governed_pool(
                pool,
                authority=authority,
                trusted_evidence_index=index,
            )
            if blockers:
                raise ValueError(
                    "window_incremental_pool_invalid:" + ",".join(blockers)
                )
            decision = evaluate_v2_window_decision(
                window=window,
                schedule_date=schedule_date,
                pool=pool,
                previously_assigned=assigned,
                no_publication_boundary=True,
            )
            selected_id = decision.get("selected_candidate_id")
            if selected_id:
                assigned.append(candidates_by_id[str(selected_id)])
            ledger.append({
                "schedule_date": schedule_date,
                "window_id": window["window_id"],
                "prior_cursor": list(prior_cursor),
                "cursor": list(cursor),
                "cutoff_utc": cutoff,
                "new_candidate_ids": sorted(new_candidate_ids),
                "new_candidate_count": len(new_candidate_ids),
                "cumulative_candidate_count": len(candidates),
                "duplicate_discovery_count": 0,
            })
            pools.append(pool)
            decisions.append(decision)

    assigned_authorized = next(
        (
            candidates_by_id[str(value["selected_candidate_id"])]
            for value in decisions
            if value.get("selected_candidate_id")
            and candidates_by_id[str(value["selected_candidate_id"])].get(
                "reporting_allowed"
            )
        ),
        None,
    )
    if assigned_authorized is None:
        raise ValueError("authorized_candidate_not_assigned_in_history_window")
    handoff = build_canonical_editorial_shadow_handoff(
        assigned_authorized,
        generated_at_utc=pools[-1]["cutoff_time_utc"],
    )
    context_abstentions = [
        build_canonical_editorial_shadow_handoff(
            candidate,
            generated_at_utc=pools[-1]["cutoff_time_utc"],
        )
        for candidate in candidates
        if candidate.get("reporting_allowed") is not True
    ]
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation_mode": "DETERMINISTIC_LOCAL_VERIFIED_INCREMENTAL_SHADOW",
        "observed_upstream_head": observed_upstream_head,
        "later_observed_upstream_branch_head": bridge.current_branch_head,
        "registry_authority_packet": authority.authority_packet(),
        "enabled_discovery_route_record_ids": [
            route["record_id"] for route in routes
        ],
        "cursor_contract": [
            "known_at_utc",
            "target_id",
            "stable_record_id",
            "version_id",
        ],
        "historical_update_probe": historical_update_probe,
        "window_ledger": ledger,
        "candidate_pools": pools,
        "window_decisions": decisions,
        "trusted_evidence_index": verifier.index,
        "editorial_shadow_handoff": handoff,
        "context_only_abstentions": context_abstentions,
        "summary": {
            "history_day_count": len(history_dates),
            "window_count": len(history_dates) * len(FIVE_WINDOWS),
            "discovered_version_count": len(seen_cursors),
            "candidate_count": len(candidates),
            "duplicate_discovery_count": 0,
            "context_only_candidate_count": len(context_abstentions),
            "authorized_editorial_handoff_count": 1,
            "publication_count": 0,
            "public_write_count": 0,
            "upstream_write_count": 0,
        },
        "calibration_state": "UNCALIBRATED_FOUNDATION",
        "publication_authority": False,
        "public_write_performed": False,
        "upstream_write_performed": False,
        "network_intake_performed": False,
        "credential_read_performed": False,
    }
    result["logical_hash"] = logical_hash(result)
    return result
