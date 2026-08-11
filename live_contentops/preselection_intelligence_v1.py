"""Deterministic preselection intelligence inside the canonical rolling-X newsroom.

This seam runs only over the compact global-editor shortlist. It enriches/reranks/holds before
targeted evidence, writing, review, or packaging and performs zero model/provider calls.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_data_catalog_v1 import (
    query_story_scoped_cc_context,
)
from live_contentops.editorial_portfolio_v1 import (
    DECISION_BREAKING_NEW_STORY,
    DECISION_DEEPEN_EXISTING_STORY,
    DECISION_HOLD,
    DECISION_LOW_DELTA_REPEAT,
    DECISION_MATERIAL_FOLLOW_UP,
    PublishedArticleRef,
    build_material_follow_up_context,
    classify_story_novelty,
    concentration_penalty,
    portfolio_state_today,
)

SCHEMA_VERSION = "contentops.preselection_intelligence.v1"

_DECISION_BONUS = {
    DECISION_BREAKING_NEW_STORY: 12.0,
    DECISION_MATERIAL_FOLLOW_UP: 11.0,
    DECISION_DEEPEN_EXISTING_STORY: 7.0,
    DECISION_LOW_DELTA_REPEAT: -1000.0,
    DECISION_HOLD: -1000.0,
}

_CAPABILITY_MODE = {
    "BREAKING_BRIEF": "straight_news",
    "FOLLOW_UP_UPDATE": "straight_news",
    "CAPITAL_CHRONICLE_DEEP_DIVE": "deep_analysis",
}


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def apply_preselection_intelligence(
    clusters: Sequence[Mapping[str, Any]],
    *,
    published_corpus: Sequence[PublishedArticleRef],
    cc_catalog: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Enrich and rerank the compact shortlist before any expensive story path."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    portfolio = portfolio_state_today(published_corpus, now=moment)
    evaluated: list[dict[str, Any]] = []
    original_order = [str(row.get("cluster_id") or "") for row in clusters]
    for cluster_value in clusters:
        cluster = dict(cluster_value)
        original_rank = int(cluster.get("rank") or 0)
        # ``cluster_id`` is already the canonical story identity on this route. Propagate it as
        # the update-chain identity instead of inventing an unrelated second identifier.
        update_chain_identity = str(
            cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
        )
        cluster["update_chain_identity"] = update_chain_identity
        cc_context = query_story_scoped_cc_context(
            cc_catalog, [str(value) for value in (cluster.get("entities_topics") or [])]
        )
        novelty = classify_story_novelty(
            cluster,
            published_corpus=published_corpus,
            cc_context_richness=float(cc_context.get("cc_context_richness") or 0.0),
            now=moment,
        )
        decision = str(novelty["decision"])
        concentration = concentration_penalty(
            [str(value) for value in (cluster.get("entities_topics") or [])], portfolio
        )
        # Material follow-ups can overcome the soft concentration penalty; it remains visible.
        effective_concentration = (
            concentration * 0.25 if decision == DECISION_MATERIAL_FOLLOW_UP else concentration
        )
        base_score = 100.0 - (max(1, original_rank) - 1) * 8.0
        score = (
            base_score
            + _DECISION_BONUS[decision]
            + 36.0 * float(cc_context.get("cc_context_richness") or 0.0)
            - 24.0 * effective_concentration
        )
        resolved_mode = str(novelty.get("recommended_article_mode") or "HOLD")
        follow_up_context = build_material_follow_up_context(
            cluster, novelty, published_corpus
        )
        cluster.update({
            "preselection_original_rank": original_rank,
            "editorial_classification": decision,
            "resolved_article_mode": resolved_mode,
            "capability_article_mode": _CAPABILITY_MODE.get(resolved_mode),
            "capital_chronicle_context": cc_context,
            "portfolio_concentration_penalty": concentration,
            "portfolio_concentration_penalty_effective": round(effective_concentration, 4),
            "preselection_score": round(score, 4),
            "preselection_novelty": novelty,
            "material_follow_up_context": follow_up_context,
            "preselection_occurs_before_targeted_evidence": True,
            "preselection_occurs_before_article_generation": True,
            "x_and_cc_editorial_context_grant_factual_or_numeric_authority": False,
        })
        evaluated.append(cluster)

    eligible = [
        row for row in evaluated
        if row["editorial_classification"] not in {DECISION_LOW_DELTA_REPEAT, DECISION_HOLD}
    ]
    held = [
        row for row in evaluated
        if row["editorial_classification"] in {DECISION_LOW_DELTA_REPEAT, DECISION_HOLD}
    ]
    eligible.sort(key=lambda row: (
        -float(row["preselection_score"]),
        int(row["preselection_original_rank"]),
        str(row.get("cluster_id") or ""),
    ))
    for rank, row in enumerate(eligible, start=1):
        row["rank"] = rank
    result = {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": moment.isoformat().replace("+00:00", "Z"),
        "input_shortlist_count": len(clusters),
        "eligible_shortlist_count": len(eligible),
        "held_shortlist_count": len(held),
        "original_order": original_order,
        "reranked_order": [str(row.get("cluster_id") or "") for row in eligible],
        "ranking_order_changed": original_order[:len(eligible)] != [
            str(row.get("cluster_id") or "") for row in eligible
        ],
        "ranked_clusters": eligible,
        "held_clusters": held,
        "portfolio_state": portfolio,
        "published_corpus_article_count": len(published_corpus),
        "cc_catalog_store_count": int(cc_catalog.get("store_count_discovered") or 0),
        "cc_catalog_complete": cc_catalog.get("discovery_complete") is True,
        "occurs_before_targeted_evidence": True,
        "occurs_before_article_generation": True,
        "llm_or_provider_calls": 0,
        "publication_authority_granted": False,
    }
    result["preselection_logical_hash"] = _logical_hash({
        key: value for key, value in result.items() if key != "preselection_logical_hash"
    })
    return result
