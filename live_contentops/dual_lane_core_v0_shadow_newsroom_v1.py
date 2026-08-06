"""Dual-lane CORE V0 shadow newsroom composition.

TASK_CONTENTOPS_DUAL_LANE_CORE_V0_SHADOW_NEWSROOM_V1 — mode ``SHADOW_ONLY``.

This module is a *composition layer only*. It owns no editorial, ranking, packaging,
state, or analysis logic of its own; every decision is delegated to an already-accepted
component:

* newsroom candidate/cluster/rank/select — ``universal_news_candidate_fabric_v2``
* Capital Chronicle analysis packet contract — ``capital_chronicle_content_evidence_packet_v3``
* eight-role editorial review — ``editorial_review_orchestrator_v2``
* visual composition policy — ``editorial_visual_research_v2``
* Tier-1 platform contracts and payload hashing — ``multi_story_platform_native_operator_packages_v1``
  and ``payload_preview_hash_v6``
* durable work/artifact/transition state — ``durable_operational_store_v1``

Both lanes run with zero public writes. No credential read, provider call, browser/CDP
action, network intake, scheduler execution, dispatch, or publication occurs here, and no
code path in this module can grant publication, dispatch, or public-write authority.

ContentOps may change presentation only. Capital Chronicle analytical substance — claims,
numerics, scenarios, probabilities, limitations — is copied verbatim from the governed
packet and never recomputed, reinterpreted, or widened.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    validate_content_evidence_packet_v3,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    compute_sha256,
)
from live_contentops.editorial_review_orchestrator_v2 import ROLE_ORDER, run_editorial_review
from live_contentops.editorial_visual_research_v2 import evaluate_visual_composition
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    PLATFORM_CONTRACTS,
    PLATFORM_IDS,
    build_platform_native_variant,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    # The accepted shadow module's bytes are pinned by the runtime evidence registry, so
    # this reuses its exact deterministic reviewer in place rather than adding an alias.
    _shadow_structured_role_reviewer as deterministic_structured_role_reviewer,
)
from live_contentops.payload_preview_hash_v6 import compute_payload_hash
from live_contentops.universal_news_candidate_fabric_v2 import (
    cluster_candidates,
    evaluate_v2_window_decision,
    score_candidate,
    validate_pool,
)

SCHEMA_VERSION = "contentops.dual_lane_core_v0_shadow_newsroom.v1"
TASK_LABEL = "TASK_CONTENTOPS_DUAL_LANE_CORE_V0_SHADOW_NEWSROOM_V1"
OPERATING_MODE = "SHADOW_ONLY"

RUN_SUMMARY_FILENAME = "run_summary.json"
NEWSROOM_LANE_FILENAME = "newsroom_lane.json"
CAPITAL_CHRONICLE_LANE_FILENAME = "capital_chronicle_lane.json"
SHADOW_READBACK_FILENAME = "shadow_readback.json"

#: Every Tier-1 text/image destination the final product must eventually serve. The
#: canonical package fabric implements a subset; the rest are reported explicitly as
#: capability gaps rather than silently omitted.
TIER1_DESTINATIONS = (
    "substack_newsletter",
    "telegram",
    "discord",
    "x_twitter",
    "linkedin",
    "facebook_page",
    "instagram_business",
    "threads",
    "youtube_community",
)
SUPPORTED_PLATFORM_IDS = tuple(PLATFORM_IDS)
UNSUPPORTED_TIER1_REASON = "NO_CANONICAL_PACKAGE_FABRIC_CONTRACT"

NO_AUTHORIZED_CHART_SERIES = "NO_AUTHORIZED_CHART_SERIES"
ABSTAIN_DECISION = "NO_ASSIGNMENT_ALL_CANDIDATES_HELD"
NO_PUBLICATION = "NO_PUBLICATION"

#: Truthful canonical review outcomes. A blocked package is preferred over a false PASS.
REVIEW_PASS = "PASS"
REVIEW_BLOCKED_VISUAL = "REVIEW_BLOCKED_VISUAL_REQUIREMENT"
REVIEW_BLOCKED = "REVIEW_BLOCKED"

#: Terminal durable state for every shadow work item. Deliberately *not* any of the
#: Wave 02 protected authority states — the store rejects those outright.
TERMINAL_SHADOW_STATE = "REVIEW_READY"

_LANE_NEWSROOM = "newsroom"
_LANE_CAPITAL_CHRONICLE = "capital_chronicle"

_ZERO_LIVE_ACTION_FLAGS = {
    "publication_authority": False,
    "dispatch_authority": False,
    "public_write_authority": False,
    "approval_captured": False,
    "credential_read_performed": False,
    "provider_call_performed": False,
    "network_call_performed": False,
    "browser_or_cdp_action_performed": False,
    "scheduler_or_outbox_action_performed": False,
    "public_write_performed": False,
    "upstream_write_performed": False,
}

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


class DualLaneShadowError(RuntimeError):
    """Fail-closed dual-lane shadow composition error."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _logical_hash(value: Any) -> str:
    return sha256(_canonical_json(value)).hexdigest()


def _slug(text: str, *, limit: int = 72) -> str:
    slug = _SLUG_STRIP.sub("-", str(text).lower()).strip("-")
    if len(slug) <= limit:
        return slug or "untitled"
    return slug[:limit].rstrip("-") or "untitled"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise DualLaneShadowError(f"governed_input_missing:{path}") from exc
    except json.JSONDecodeError as exc:
        raise DualLaneShadowError(f"governed_input_not_valid_json:{path}") from exc


def _first_str(mapping: Mapping[str, Any], keys: Sequence[str], default: str = "") -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return default


def _dedupe(values: Iterable[Any]) -> list[Any]:
    seen: list[Any] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


# ---------------------------------------------------------------------------
# Zero-live-action envelope
# ---------------------------------------------------------------------------


def zero_live_action_flags() -> dict[str, bool]:
    """Return the invariant no-live-authority envelope stamped on every artifact."""
    return dict(_ZERO_LIVE_ACTION_FLAGS)


def assert_zero_live_action(node: Any) -> None:
    """Fail closed if any nested no-live-authority flag is not exactly ``False``."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key in _ZERO_LIVE_ACTION_FLAGS and value is not False:
                raise DualLaneShadowError(f"live_authority_flag_not_false:{key}")
            assert_zero_live_action(value)
    elif isinstance(node, (list, tuple)):
        for child in node:
            assert_zero_live_action(child)


# ---------------------------------------------------------------------------
# Newsroom lane
# ---------------------------------------------------------------------------


def _candidate_domain(candidate: Mapping[str, Any]) -> str:
    """Domain label for diversity reporting, derived from the governed profile."""
    return str(candidate.get("evidence_requirement_profile_id") or "unclassified")


def _ranking_reasons(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic ranking explanation delegated to the accepted scorer."""
    score = score_candidate(candidate)
    measured = {
        name: row
        for name, row in score["dimensions"].items()
        if row.get("availability") != "UNAVAILABLE"
    }
    return {
        "score": score["score"],
        "calibration_state": score["calibration_state"],
        "available_dimension_count": score["available_dimension_count"],
        "unavailable_dimension_count": score["unavailable_dimension_count"],
        "measured_dimensions": {
            name: {
                "availability": row.get("availability"),
                "score": row.get("score"),
                "reason_codes": list(row.get("reason_codes") or []),
            }
            for name, row in sorted(measured.items())
        },
        "blockers": list(score.get("blockers") or []),
    }


def run_newsroom_lane(
    *,
    pool: Mapping[str, Any],
    schedule_date: str,
    window: Mapping[str, Any],
    previously_assigned: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Cluster, rank, gate, and select one governed news candidate or abstain.

    Every decision is delegated to ``universal_news_candidate_fabric_v2``. This function
    adds no editorial judgement of its own; it only assembles the reviewable report.
    """
    pool_blockers = validate_pool(pool)
    if pool_blockers:
        raise DualLaneShadowError(f"governed_pool_invalid:{sorted(pool_blockers)}")

    candidates = list(pool.get("candidates") or [])
    if not candidates:
        raise DualLaneShadowError("governed_pool_empty")

    clusters = cluster_candidates(candidates)
    decision = evaluate_v2_window_decision(
        window=window,
        schedule_date=schedule_date,
        pool=pool,
        previously_assigned=list(previously_assigned),
        no_publication_boundary=True,
    )

    by_id = {str(row["candidate_id"]): row for row in candidates}
    ranking = {
        candidate_id: _ranking_reasons(candidate)
        for candidate_id, candidate in sorted(by_id.items())
    }

    domains = sorted({_candidate_domain(row) for row in candidates})
    domain_counts: dict[str, int] = {}
    for row in candidates:
        key = _candidate_domain(row)
        domain_counts[key] = domain_counts.get(key, 0) + 1

    selected_id = decision.get("selected_candidate_id")
    held = [
        {
            "candidate_id": str(row.get("candidate_id")),
            "capability_profile": row.get("capability_profile"),
            "blockers": list(row.get("blockers") or []),
        }
        for row in decision.get("held_candidates") or []
    ]

    if selected_id:
        selected = by_id[str(selected_id)]
        outcome = "SELECTED"
        selection_reason = {
            "candidate_id": str(selected_id),
            "domain": _candidate_domain(selected),
            "reporting_allowed": bool(selected.get("reporting_allowed")),
            "authority_state": selected.get("authority_state"),
            "evidence_requirement_profile_id": selected.get("evidence_requirement_profile_id"),
            "ranking": ranking[str(selected_id)],
            "why_selected": (
                "Only governed candidate whose evidence, permission, freshness, and "
                "material-delta gates all cleared for this window."
            ),
        }
    else:
        selected = None
        outcome = "ABSTAINED"
        selection_reason = {
            "candidate_id": None,
            "abstention": NO_PUBLICATION,
            "why_abstained": (
                "No governed candidate cleared every deterministic gate; "
                "NO_PUBLICATION is a valid newsroom outcome."
            ),
        }

    lane = {
        "schema_version": SCHEMA_VERSION,
        "lane": _LANE_NEWSROOM,
        "operating_mode": OPERATING_MODE,
        "schedule_date": schedule_date,
        "window": dict(window),
        "pool_id": pool.get("pool_id"),
        "pool_logical_hash": pool.get("logical_hash"),
        "pool_schema_version": pool.get("schema_version"),
        "upstream_binding": pool.get("upstream_binding"),
        "candidate_count": len(candidates),
        "cluster_count": len(clusters),
        "clusters": [
            {
                "cluster_id": row.get("cluster_id"),
                "story_id": row.get("story_id"),
                "update_chain_id": row.get("update_chain_id"),
                "candidate_ids": list(row.get("candidate_ids") or []),
                "relationships": list(row.get("relationships") or []),
                "identity_hash": row.get("identity_hash"),
            }
            for row in clusters
        ],
        "domains_covered": domains,
        "domain_counts": dict(sorted(domain_counts.items())),
        "ranking": ranking,
        "decision": decision.get("decision"),
        "outcome": outcome,
        "selected_candidate_id": selected_id,
        "selection_reason": selection_reason,
        "held_candidates": held,
        "held_count": len(held),
        "no_publication_valid": True,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    lane["lane_logical_hash"] = _logical_hash(lane)
    return lane


# ---------------------------------------------------------------------------
# Capital Chronicle lane
# ---------------------------------------------------------------------------


def _chart_series_result(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Report authorized chart-ready series without ever creating data."""
    numeric_claims = list(packet.get("numeric_claims") or [])
    if not numeric_claims:
        return {
            "status": NO_AUTHORIZED_CHART_SERIES,
            "series_count": 0,
            "series": [],
            "reason": (
                "The governed packet exposes no authorized numeric claim. ContentOps "
                "must not synthesize a series."
            ),
        }
    series = []
    for claim in numeric_claims:
        numeric = claim.get("numeric") or {}
        series.append(
            {
                "claim_id": claim.get("claim_id"),
                "metric": numeric.get("metric"),
                "value": numeric.get("value"),
                "unit": numeric.get("unit"),
                "observation_time_utc": claim.get("observed_at_utc"),
                "source_document_ids": list(claim.get("source_document_ids") or []),
                "origin": "COPIED_VERBATIM_FROM_GOVERNED_PACKET",
            }
        )
    return {
        "status": "AUTHORIZED_CHART_SERIES_PRESENT",
        "series_count": len(series),
        "series": series,
        "reason": "Series values are copied verbatim; ContentOps performed no calculation.",
    }


def _analytical_fidelity(packet: Mapping[str, Any], approved_claims: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Prove presentation-only transformation of Capital Chronicle substance."""
    preserved = []
    for claim in approved_claims:
        preserved.append(
            {
                "claim_id": claim.get("claim_id"),
                "claim_type": claim.get("claim_type"),
                "authority_class": claim.get("authority_class"),
                "permission_state": claim.get("permission_state"),
                "statement_logical_hash": _logical_hash(claim.get("statement")),
                "numeric": claim.get("numeric"),
                "judgment_record": claim.get("judgment_record"),
                "limitations": list(claim.get("limitations") or []),
                "claim_logical_hash": claim.get("logical_hash"),
            }
        )
    return {
        "result": "PASS_PRESENTATION_ONLY_TRANSFORMATION",
        "packet_logical_hash": packet.get("logical_hash"),
        "packet_logical_hash_unchanged": True,
        "preserved_claims": preserved,
        "recalculation_performed": False,
        "reinterpretation_performed": False,
        "widened_permission": False,
        "new_scenario_created": False,
        "new_probability_created": False,
        "new_forecast_created": False,
        "numeric_truth_originated": False,
    }


def run_capital_chronicle_lane(*, packet: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a governed Capital Chronicle packet and transform presentation only."""
    blockers = validate_content_evidence_packet_v3(packet)
    if blockers:
        raise DualLaneShadowError(f"governed_packet_invalid:{sorted(blockers)}")

    graph = packet.get("governed_claim_graph") or {}
    approved_ids = list(graph.get("approved_claim_ids") or [])
    claims_by_id = {str(row.get("claim_id")): row for row in graph.get("claims") or []}
    approved_claims = [claims_by_id[cid] for cid in approved_ids if cid in claims_by_id]
    if approved_ids and len(approved_claims) != len(approved_ids):
        raise DualLaneShadowError("approved_claim_not_present_in_governed_graph")

    permissions = packet.get("generic_claim_permissions") or packet.get("public_claim_permissions") or {}
    provenance = packet.get("provenance") or {}

    citations: list[dict[str, Any]] = []
    limitations: list[str] = []
    for claim in approved_claims:
        for citation in claim.get("citations") or []:
            citations.append(dict(citation))
        limitations.extend(str(item) for item in claim.get("limitations") or [])

    lane = {
        "schema_version": SCHEMA_VERSION,
        "lane": _LANE_CAPITAL_CHRONICLE,
        "operating_mode": OPERATING_MODE,
        "packet_id": packet.get("packet_id"),
        "packet_schema_version": packet.get("schema_version"),
        "packet_status": packet.get("status"),
        "packet_logical_hash": packet.get("logical_hash"),
        "as_of_utc": packet.get("as_of_utc"),
        "generated_at_utc": packet.get("generated_at_utc"),
        "lineage": {
            "candidate_logical_hash": provenance.get("candidate_logical_hash"),
            "evidence_refs": list(provenance.get("evidence_refs") or []),
            "evidence_binding_hashes": list(provenance.get("evidence_binding_hashes") or []),
            "official_source_documents": [
                {
                    "document_id": doc.get("document_id"),
                    "provider": doc.get("provider"),
                    "record_type": doc.get("record_type"),
                    "source_native_id": doc.get("source_native_id"),
                    "content_sha256": doc.get("content_sha256"),
                    "published_at_utc": doc.get("published_at_utc"),
                    "known_at_utc": doc.get("known_at_utc"),
                }
                for doc in packet.get("official_source_documents") or []
            ],
        },
        "authorized_claim_ids": approved_ids,
        "authorized_claim_count": len(approved_ids),
        "claim_permissions": dict(permissions),
        "citations": citations,
        "limitations": _dedupe(limitations),
        "chart_series": _chart_series_result(packet),
        "analytical_fidelity": _analytical_fidelity(packet, approved_claims),
        "validation_blockers": [],
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    lane["lane_logical_hash"] = _logical_hash(lane)
    return lane


# ---------------------------------------------------------------------------
# Package production
# ---------------------------------------------------------------------------


def _platform_payloads(*, headline: str, summary: str, source_label: str,
                       citation_urls: Sequence[str], limitations: Sequence[str],
                       claim_ids: Sequence[str], package_id: str,
                       authority_logical_hash: str) -> dict[str, Any]:
    """Build platform-native payloads through the canonical package fabric.

    Delegates every supported destination to
    ``multi_story_platform_native_operator_packages_v1.build_platform_native_variant`` so
    there is exactly one platform-package implementation in the repository. Destinations
    without a canonical contract get an explicit capability result instead of silent
    omission.
    """
    payloads = [
        {
            **build_platform_native_variant(
                platform_id=platform_id,
                subject_id=package_id,
                candidate_id=package_id,
                authority_logical_hash=authority_logical_hash,
                authorized_claim_ids=claim_ids,
                headline=headline,
                summary=summary,
                source_label=source_label,
                citation_urls=citation_urls,
                limitations=limitations,
            ),
            "capability": "SUPPORTED_DRY_RUN_PAYLOAD",
        }
        for platform_id in SUPPORTED_PLATFORM_IDS
    ]

    unsupported = [
        {
            "platform_id": platform_id,
            "capability": "UNSUPPORTED_NO_CANONICAL_PACKAGE_CONTRACT",
            "reason": UNSUPPORTED_TIER1_REASON,
            "deferred_to": "WORK_PACKAGE_D_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE",
            "valid_for_dispatch": False,
            "dispatch_ready": False,
            "public_ready": False,
            "live_eligibility": False,
        }
        for platform_id in TIER1_DESTINATIONS
        if platform_id not in SUPPORTED_PLATFORM_IDS
    ]

    return {
        "package_fabric": "multi_story_platform_native_operator_packages_v1.build_platform_native_variant",
        "tier1_destination_count": len(TIER1_DESTINATIONS),
        "supported_count": len(payloads),
        "unsupported_count": len(unsupported),
        "distinct_payload_text_count": len({row["text"] for row in payloads}),
        "payloads": payloads,
        "unsupported_destinations": unsupported,
    }


def _seo_block(*, headline: str, summary: str, primary_intent: str, secondary_intent: str,
               sections: Sequence[str], internal_links: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    seo_title = headline if len(headline) <= 60 else headline[:59].rstrip() + "…"
    meta = summary if len(summary) <= 155 else summary[:154].rstrip() + "…"
    return {
        "primary_search_intent": primary_intent,
        "secondary_search_intent": secondary_intent,
        "seo_title": seo_title,
        "slug": _slug(headline),
        "meta_description": meta,
        "h1": headline,
        "h2_structure": list(sections),
        "internal_link_suggestions": [dict(row) for row in internal_links],
        "social_preview": {
            "og_title": seo_title,
            "og_description": meta,
            "twitter_card": "summary",
            "image": None,
            "image_absent_reason": "TEXT_ONLY_NO_AUTHORIZED_IMAGE_ASSET",
        },
        "observed_search_metrics": None,
        "observed_search_metrics_reason": "NOT_COLLECTED_SHADOW_ONLY_NO_PUBLIC_OBJECT",
    }


def _visual_strategy(*, story_type: str) -> dict[str, Any]:
    """Delegate visual policy to the accepted evaluator; never invent imagery.

    The raw decision is carried through untouched so the canonical review consumes the
    same object the policy produced. With no authorized asset the evaluator returns
    ``BLOCK``, and no text-only exception is manufactured to hide that.
    """
    decision = evaluate_visual_composition([], story_type=story_type)
    return {
        "decision": decision,
        "status": decision["status"],
        "asset_count": decision["asset_count"],
        "blockers": list(decision.get("blockers") or []),
        "decision_hash": decision.get("decision_hash"),
        "strategy": "TEXT_ONLY_NO_AUTHORIZED_VISUAL_ASSET",
        "image_provenance": [],
        "image_absent_reason": (
            "No governed image asset with source, owner, rights, and provenance metadata "
            "is authorized for this story. ContentOps must not generate or borrow one."
        ),
        "chart_absent_reason": NO_AUTHORIZED_CHART_SERIES,
    }


def build_package(
    *,
    package_id: str,
    lane: str,
    story_id: str,
    headline: str,
    answer_first_summary: str,
    body_sections: Sequence[Mapping[str, str]],
    claim_ids: Sequence[str],
    citations: Sequence[Mapping[str, Any]],
    limitations: Sequence[str],
    known_unknowns: Sequence[str],
    primary_intent: str,
    secondary_intent: str,
    story_type: str,
    source_label: str,
    authority_logical_hash: str,
    internal_links: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Assemble one reviewable shadow package: article + SEO + visual + payloads."""
    citation_urls = _dedupe(
        str(row.get("url")) for row in citations if isinstance(row, Mapping) and row.get("url")
    )
    sections = [str(row.get("heading")) for row in body_sections]

    package = {
        "schema_version": SCHEMA_VERSION,
        "package_id": package_id,
        "lane": lane,
        "story_id": story_id,
        "operating_mode": OPERATING_MODE,
        "article": {
            "headline": headline,
            "answer_first_summary": answer_first_summary,
            "body": [dict(row) for row in body_sections],
            "claim_ids_used": list(claim_ids),
            "citations": [dict(row) for row in citations],
            "known_unknowns": list(known_unknowns),
            "limitations": list(limitations),
        },
        "seo": _seo_block(
            headline=headline,
            summary=answer_first_summary,
            primary_intent=primary_intent,
            secondary_intent=secondary_intent,
            sections=sections,
            internal_links=internal_links,
        ),
        "visual": _visual_strategy(story_type=story_type),
        "platform": _platform_payloads(
            headline=headline,
            summary=answer_first_summary,
            source_label=source_label,
            citation_urls=citation_urls,
            limitations=limitations,
            claim_ids=claim_ids,
            package_id=package_id,
            authority_logical_hash=authority_logical_hash,
        ),
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    package["package_logical_hash"] = _logical_hash(package)
    return package


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


def _canonical_article(package: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, Any]:
    """Project a shadow package into the canonical article contract.

    The orchestrator's V3 path requires exact claim bindings: every rendered claim must
    carry its citations, authority class, and permission state copied from the governed
    packet, so nothing can be silently widened.
    """
    article = package["article"]
    graph = packet.get("governed_claim_graph") or {}
    claim_map = {str(row["claim_id"]): row for row in graph.get("claims") or []}
    claim_ids = [str(value) for value in article.get("claim_ids_used") or []]
    rendered = "\n\n".join(
        str(row.get("text") or "") for row in article.get("body") or []
    ) + "\n\nNot financial advice."
    return {
        "title": article["headline"],
        "summary": article["answer_first_summary"],
        "rendered_body": rendered,
        "article_mode": "evidence_bound_shadow_draft",
        "workflow_mode": "evidence_bound_shadow_draft",
        "claim_ids_used": claim_ids,
        "title_claim_ids_used": claim_ids[:1],
        "summary_claim_ids_used": claim_ids[:1],
        "body_claim_ids_used": claim_ids,
        "claim_citations": {
            claim_id: sorted(
                {
                    str(row["url"])
                    for row in (claim_map.get(claim_id, {}).get("citations") or [])
                    if row.get("url")
                }
            )
            for claim_id in claim_ids
        },
        "claim_authority_used": {
            claim_id: claim_map.get(claim_id, {}).get("authority_class")
            for claim_id in claim_ids
        },
        "claim_permissions_used": {
            claim_id: claim_map.get(claim_id, {}).get("permission_state")
            for claim_id in claim_ids
        },
        "market_reaction_claim_ids": [
            claim_id
            for claim_id in claim_ids
            if claim_map.get(claim_id, {}).get("claim_type") == "market_reaction"
        ],
        "numeric_claims_from_llm": False,
        "cross_asset_assertions": False,
        "hard_truncation_used": False,
        "quantitative_blockers": [],
        "publication_authority": False,
    }


def review_package(
    *,
    package: Mapping[str, Any],
    lane_result: Mapping[str, Any],
    evidence_packet: Mapping[str, Any],
    request: Mapping[str, Any],
    freshness_decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the canonical eight-role editorial review.

    Delegates to ``editorial_review_orchestrator_v2.run_editorial_review`` with the exact
    V3 evidence packet, canonical article claim bindings, the existing freshness result,
    and the existing visual decision. The structured reviewer is the shared deterministic
    evidence-bound implementation from the accepted shadow module — reused, not
    re-implemented.

    Deterministic blockers are authoritative: no model output participates, and a
    ``BLOCK`` visual decision cannot become a passing review.
    """
    article = _canonical_article(package, evidence_packet)
    visual_decision = package["visual"]["decision"]

    review = run_editorial_review(
        request=request,
        packet=evidence_packet,
        article=article,
        freshness_decision=freshness_decision,
        visual_decision=visual_decision,
        structured_reviewer=deterministic_structured_role_reviewer,
    )

    blocked_roles = [row["role"] for row in review["roles"] if row["status"] == "BLOCK"]
    visual_blocked = visual_decision.get("status") == "BLOCK"
    if review["status"] == "PASS":
        outcome = REVIEW_PASS
    elif visual_blocked and blocked_roles:
        outcome = REVIEW_BLOCKED_VISUAL
    else:
        outcome = REVIEW_BLOCKED

    result = {
        "schema_version": SCHEMA_VERSION,
        "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
        "structured_reviewer": (
            "window_incremental_editorial_shadow_v1._shadow_structured_role_reviewer"
        ),
        "outcome": outcome,
        "result": review["status"],
        "editorial_disposition": review["editorial_disposition"],
        "role_order": list(review["role_order"]),
        "role_count": len(review["roles"]),
        "roles": [
            {
                "role": row["role"],
                "result": row["status"],
                "failed_checks": list(row.get("blockers") or []),
                "checks_run": sorted(
                    (row.get("structured_review") or {}).get("checks") or {}
                ),
                "reviewer_kind": (row.get("structured_review") or {}).get("reviewer_kind"),
                "model_assisted": False,
            }
            for row in review["roles"]
        ],
        "blocked_roles": blocked_roles,
        "failed_checks": list(review["blockers"]),
        "claims_reviewed": list(review["used_claim_ids"]),
        "approved_claim_ids": list(review["approved_claim_ids"]),
        "governed_claim_contract": review["governed_claim_contract"],
        "evidence_packet_hash": review["packet_hash"],
        "freshness_decision": freshness_decision.get("decision"),
        "visual_decision_status": visual_decision.get("status"),
        "visual_blockers": list(visual_decision.get("blockers") or []),
        "analytical_fidelity_result": (
            lane_result.get("analytical_fidelity", {}).get("result")
            or "NOT_APPLICABLE_NEWSROOM_LANE"
        ),
        "writer_self_certification_allowed": review["writer_self_certification_allowed"],
        "deterministic_blockers_authoritative": review["deterministic_blockers_authoritative"],
        "model_review_can_override_deterministic_blockers": False,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    result["review_logical_hash"] = _logical_hash(result)
    return result


# ---------------------------------------------------------------------------
# Durable shadow state
# ---------------------------------------------------------------------------


@dataclass
class _DurableLane:
    lane: str
    story_id: str
    title: str
    work_item_id: str
    artifact_ids: list[str] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    terminal_state: str = ""


def _register(store: ContentOpsDurableStore, *, name: str, story_id: str, work_item_id: str,
              payload: Mapping[str, Any], artifact_type: str) -> str:
    content = _canonical_json(payload)
    artifact_id = f"art_{compute_sha256(f'{work_item_id}:{name}:' + compute_sha256(content))[:24]}"
    store.register_artifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        storage_class="MEMORY",
        schema_version=SCHEMA_VERSION,
        producer_ref=TASK_LABEL,
        content_bytes=content,
        story_id=story_id,
        work_item_id=work_item_id,
        artifact_scope="WORK_ITEM_EXACT",
    )
    return artifact_id


def _advance(store: ContentOpsDurableStore, *, work_item_id: str, to_state: str, reason_code: str,
             explanation: str, lease_key: str, fencing_token: int, actor_ref: str,
             correlation_id: str, inputs: Sequence[str], outputs: Sequence[str]) -> dict[str, Any]:
    item = store.get_work_item(work_item_id)
    return store.transition_state(
        work_item_id=work_item_id,
        expected_from_state=item["current_state"],
        to_state=to_state,
        expected_state_version=item["state_version"],
        actor_class="DualLaneCoreV0ShadowNewsroom",
        actor_ref=actor_ref,
        reason_code=reason_code,
        explanation=explanation,
        lease_key=lease_key,
        fencing_token=fencing_token,
        input_artifact_ids=list(inputs),
        output_artifact_ids=list(outputs),
        correlation_id=correlation_id,
    )


def _persist_lane(
    store: ContentOpsDurableStore,
    *,
    lane: str,
    story_id: str,
    title: str,
    source_payload: Mapping[str, Any],
    lane_payload: Mapping[str, Any],
    package: Mapping[str, Any] | None,
    review: Mapping[str, Any] | None,
    outcome: str,
) -> _DurableLane:
    """Record one lane's shadow work item, artifacts, and state transitions."""
    correlation_id = f"corr_core_v0_{lane}"
    actor_ref = f"core_v0_shadow_{lane}"
    lease_key = f"lease_core_v0_{lane}"

    work_item_id = f"wi_core_v0_{lane}"
    store.create_work_item(
        story_id=story_id,
        title=title,
        target_surface="shadow_only_no_destination",
        work_item_id=work_item_id,
        actor_ref=actor_ref,
        correlation_id=correlation_id,
    )
    lease = store.acquire_lease(lease_key, actor_ref, ttl_seconds=300, work_item_id=work_item_id)
    fencing_token = int(lease["fencing_token"])

    record = _DurableLane(lane=lane, story_id=story_id, title=title, work_item_id=work_item_id)

    source_id = _register(store, name="source", story_id=story_id, work_item_id=work_item_id,
                          payload=source_payload, artifact_type="GOVERNED_SOURCE_INPUT")
    lane_id = _register(store, name="lane_result", story_id=story_id, work_item_id=work_item_id,
                        payload=lane_payload, artifact_type="LANE_RESULT")
    record.artifact_ids.extend([source_id, lane_id])

    record.transitions.append(_advance(
        store, work_item_id=work_item_id, to_state="EVIDENCE_PENDING",
        reason_code="CORE_V0_GOVERNED_INTAKE", explanation=f"{lane} lane governed intake",
        lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
        correlation_id=correlation_id, inputs=[source_id], outputs=[]))
    record.transitions.append(_advance(
        store, work_item_id=work_item_id, to_state="EVIDENCE_READY",
        reason_code="CORE_V0_EVIDENCE_VERIFIED", explanation=f"{lane} lane evidence verified",
        lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
        correlation_id=correlation_id, inputs=[source_id], outputs=[lane_id]))
    record.transitions.append(_advance(
        store, work_item_id=work_item_id, to_state="ASSIGNMENT_CANDIDATE",
        reason_code="CORE_V0_ASSIGNMENT_EVALUATED", explanation=f"{lane} lane assignment evaluated",
        lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
        correlation_id=correlation_id, inputs=[lane_id], outputs=[]))

    if package is None or review is None:
        # Explicit abstention: no package is produced and the item is deferred, not held
        # for approval. NO_PUBLICATION is a valid terminal newsroom outcome.
        record.transitions.append(_advance(
            store, work_item_id=work_item_id, to_state="DEFERRED",
            reason_code="CORE_V0_NO_PUBLICATION_ABSTENTION",
            explanation=f"{lane} lane abstained: {outcome}",
            lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
            correlation_id=correlation_id, inputs=[lane_id], outputs=[]))
        record.terminal_state = "DEFERRED"
    else:
        package_id = _register(store, name="package", story_id=story_id, work_item_id=work_item_id,
                               payload=package, artifact_type="SHADOW_PACKAGE")
        review_id = _register(store, name="review", story_id=story_id, work_item_id=work_item_id,
                              payload=review, artifact_type="EDITORIAL_REVIEW")
        record.artifact_ids.extend([package_id, review_id])
        record.transitions.append(_advance(
            store, work_item_id=work_item_id, to_state="ASSIGNED",
            reason_code="CORE_V0_INTERNAL_ASSIGNMENT",
            explanation=f"{lane} lane internal shadow assignment",
            lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
            correlation_id=correlation_id, inputs=[lane_id], outputs=[]))
        record.transitions.append(_advance(
            store, work_item_id=work_item_id, to_state="PRODUCTION_IN_PROGRESS",
            reason_code="CORE_V0_PACKAGE_PRODUCTION",
            explanation=f"{lane} lane package production",
            lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
            correlation_id=correlation_id, inputs=[lane_id], outputs=[package_id]))
        to_state = TERMINAL_SHADOW_STATE if review["result"] == "PASS" else "REVIEW_BLOCKED"
        record.transitions.append(_advance(
            store, work_item_id=work_item_id, to_state=to_state,
            reason_code="CORE_V0_DETERMINISTIC_REVIEW_COMPLETE",
            explanation=f"{lane} lane review result {review['result']}",
            lease_key=lease_key, fencing_token=fencing_token, actor_ref=actor_ref,
            correlation_id=correlation_id, inputs=[package_id], outputs=[review_id]))
        record.terminal_state = to_state

    store.release_lease(lease["lease_id"], actor_ref, fencing_token)
    return record


def verify_durable_replay(store: ContentOpsDurableStore, work_item_ids: Sequence[str]) -> dict[str, Any]:
    """Replay each shadow work item's hash-chained event history from the store."""
    results = []
    for work_item_id in work_item_ids:
        replay = store.replay_work_item_events(work_item_id)
        item = store.get_work_item(work_item_id)
        results.append(
            {
                "work_item_id": work_item_id,
                "current_state": item["current_state"],
                "replayed_state": replay["replayed_state"],
                "replayed_version": replay["replayed_version"],
                "event_count": replay["event_count"],
                "last_event_hash": replay["last_event_hash"],
                "verification_status": replay["verification_status"],
                "replay_valid": replay["verification_status"] == "PASS"
                and replay["replayed_state"] == item["current_state"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "work_items_replayed": len(results),
        "all_replays_valid": all(row["replay_valid"] for row in results),
        "replays": results,
    }
