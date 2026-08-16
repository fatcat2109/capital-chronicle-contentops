"""Deterministic preselection intelligence inside the canonical rolling-X newsroom.

This seam performs two cheap, authority-free operations before expensive story work:

* it compacts a very large rolling intake to a fresh, evidence-reachable assignment universe;
* it enriches/reranks/holds the compact global-editor shortlist before targeted evidence.

Both operations perform zero model/provider calls and grant no factual authority.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

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
ASSIGNMENT_COMPACTION_SCHEMA_VERSION = "contentops.rolling_x_assignment_compaction.v1"
# Live telemetry proved that 128 headlines can consume nearly the entire 250k hard cycle cap
# before the quality-first writer/reviewer run.  Sixty-four preserves a broad ranked universe
# while leaving circuit-breaker headroom for the final editorial stages.
DEFAULT_MAX_ASSIGNMENT_HEADLINES = 64

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
    "STANDARD_NEWS_ANALYSIS": "analysis",
    "EVERGREEN_EXPLAINER": "explainer",
}

_KNOWN_OFFICIAL_SUFFIXES = (
    ".gov", ".gov.au", ".gov.uk", ".europa.eu", ".int",
)


def _evidence_reachability(cluster: Mapping[str, Any], cc_context: Mapping[str, Any]) -> dict[str, Any]:
    """Cheap feasibility signal only; it never grants factual authority."""
    from live_contentops.official_primary_evidence_loader_v1 import (
        OFFICIAL_HOSTS_BY_FAMILY,
    )
    from live_contentops.public_secondary_evidence_loader_v1 import REPUTABLE_SECONDARY_HOSTS

    urls = [
        str(value)
        for value in (
            cluster.get("public_source_urls")
            or cluster.get("official_source_urls")
            or []
        )
        if str(value).startswith("https://")
    ]
    hosts = {str(urlsplit(value).hostname or "").casefold() for value in urls}
    exact_official_hosts = {
        host
        for family_hosts in OFFICIAL_HOSTS_BY_FAMILY.values()
        for host in family_hosts
    }
    official = bool(hosts.intersection(exact_official_hosts))
    official_suffix_candidate = any(host.endswith(_KNOWN_OFFICIAL_SUFFIXES) for host in hosts)
    reputable_secondary = any(host in REPUTABLE_SECONDARY_HOSTS for host in hosts)
    cc_relevant = float(cc_context.get("cc_context_richness") or 0.0) >= 0.35
    score = min(
        1.0,
        (0.55 if official else 0.0)
        + (0.4 if reputable_secondary else 0.0)
        + (0.2 if cc_relevant else 0.0)
        + (0.1 if urls else 0.0),
    )
    return {
        "score": round(score, 4),
        "known_official_path": official,
        "unregistered_official_suffix_candidate": official_suffix_candidate and not official,
        "reputable_public_secondary_path": reputable_secondary,
        "capital_chronicle_relevant_context": cc_relevant,
        "public_source_candidate_count": len(urls),
        "mode_downgrade_viable": True,
        "factual_authority_granted": False,
    }


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _source_timestamp(row: Mapping[str, Any]) -> datetime:
    raw = str(row.get("source_timestamp_utc") or "")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _raw_assignment_reachability(row: Mapping[str, Any]) -> tuple[int, int]:
    """Return cheap locator signals only; never claim that a source supports a fact."""
    external = row.get("external_content")
    if not isinstance(external, Mapping):
        return 0, 0
    urls = [
        str(value)
        for value in (external.get("official_source_urls") or [])
        if str(value).startswith("https://")
    ]
    follow_up_locators = [
        str(value)
        for value in (external.get("follow_up_data_need_candidates") or [])
        if str(value).strip()
    ]
    return int(bool(urls)), int(bool(follow_up_locators))


def compact_rolling_x_assignment_universe(
    rolling_input: Mapping[str, Any],
    *,
    max_headlines: int = DEFAULT_MAX_ASSIGNMENT_HEADLINES,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bound semantic assignment cost while preserving the full intake as durable evidence.

    Selection is deterministic: known public locator signals rank first, then freshness and the
    stable headline identity. Held headlines remain in the original intake artifact and are
    represented here by counts and an identity hash. They may re-enter a later rolling window;
    this seam does not declare them false, duplicate, or permanently rejected.
    """
    if max_headlines < 1:
        raise ValueError("rolling_x_assignment_compaction_limit_invalid")
    headlines = rolling_input.get("headlines")
    if not isinstance(headlines, list) or not all(isinstance(row, Mapping) for row in headlines):
        raise ValueError("rolling_x_assignment_compaction_headlines_invalid")
    unique_ids = [str(value) for value in (rolling_input.get("unique_headline_ids") or [])]
    row_ids = [str(row.get("headline_id") or "") for row in headlines]
    if any(not value for value in row_ids) or len(row_ids) != len(set(row_ids)):
        raise ValueError("rolling_x_assignment_compaction_identity_invalid")
    if set(row_ids) != set(unique_ids):
        raise ValueError("rolling_x_assignment_compaction_coverage_invalid")

    ranked = sorted(
        (dict(row) for row in headlines),
        key=lambda row: (
            -_raw_assignment_reachability(row)[0],
            -_raw_assignment_reachability(row)[1],
            -_source_timestamp(row).timestamp(),
            str(row.get("headline_id") or ""),
        ),
    )
    selected = ranked[:max_headlines]
    selected_ids = [str(row["headline_id"]) for row in selected]
    held_ids = [str(row["headline_id"]) for row in ranked[max_headlines:]]
    counts = dict(rolling_input.get("counts") or {})
    counts["accepted_in_full_rolling_intake"] = len(headlines)
    counts["accepted"] = len(selected)

    compacted = {
        **dict(rolling_input),
        "headlines": selected,
        "unique_headline_ids": selected_ids,
        "counts": counts,
        "complete_input_coverage": True,
        "assignment_compaction_applied": len(held_ids) > 0,
        "full_rolling_input_canonical_hash": rolling_input.get("canonical_input_hash"),
    }
    canonical_material = {
        "schema_version": compacted.get("schema_version"),
        "cutoff_time_utc": compacted.get("cutoff_time_utc"),
        "window_start_utc": compacted.get("window_start_utc"),
        "window_hours": compacted.get("window_hours"),
        "unique_headline_ids": compacted.get("unique_headline_ids"),
        "headlines": [
            {key: value for key, value in row.items() if key != "source_locator"}
            for row in selected
        ],
    }
    compacted["canonical_input_hash"] = _logical_hash(canonical_material)
    evidence = {
        "schema_version": ASSIGNMENT_COMPACTION_SCHEMA_VERSION,
        "full_rolling_headline_count": len(headlines),
        "assignment_headline_count": len(selected),
        "held_before_semantic_assignment_count": len(held_ids),
        "max_assignment_headlines": int(max_headlines),
        "full_rolling_input_canonical_hash": rolling_input.get("canonical_input_hash"),
        "assignment_input_canonical_hash": compacted["canonical_input_hash"],
        "selected_headline_ids_hash": _logical_hash(selected_ids),
        "held_headline_ids_hash": _logical_hash(held_ids),
        "selection_order": [
            "known_public_locator_signal",
            "follow_up_locator_signal",
            "source_timestamp_descending",
            "headline_id",
        ],
        "full_intake_artifact_preserved": True,
        "llm_or_provider_calls": 0,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }
    evidence["compaction_logical_hash"] = _logical_hash(evidence)
    return compacted, evidence


def apply_preselection_intelligence(
    clusters: Sequence[Mapping[str, Any]],
    *,
    published_corpus: Sequence[PublishedArticleRef],
    cc_catalog: Mapping[str, Any],
    learning_policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Enrich and rerank the compact shortlist before any expensive story path."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    portfolio = portfolio_state_today(published_corpus, now=moment)
    evaluated: list[dict[str, Any]] = []
    original_order = [str(row.get("cluster_id") or "") for row in clusters]
    active_policy = dict(learning_policy or {})
    content_policy = dict(active_policy.get("content") or {})
    content_preferences = [
        dict(row) for row in (content_policy.get("recommendations") or [])
        if isinstance(row, Mapping)
    ][:3]
    seo_policy = dict(active_policy.get("seo") or {})
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
        # The expanded pool can contain dozens of candidates. Keep editorial rank as a useful
        # tiebreaker without allowing linear decay to make an exact-official path unreachable.
        base_score = 100.0 - min(max(1, original_rank) - 1, 8) * 2.0
        reachability = _evidence_reachability(cluster, cc_context)
        score = (
            base_score
            + _DECISION_BONUS[decision]
            + 36.0 * float(cc_context.get("cc_context_richness") or 0.0)
            - 24.0 * effective_concentration
            + 28.0 * float(reachability["score"])
        )
        resolved_mode = str(novelty.get("recommended_article_mode") or "HOLD")
        learning_bonus = 0.0
        learning_matches: list[dict[str, Any]] = []
        feature_values = {
            "article_mode": resolved_mode,
            "update_mode": decision,
            "topic_family": [str(value) for value in (cluster.get("entities_topics") or [])],
            "story_type": str(cluster.get("story_type") or ""),
        }
        for preference in content_preferences:
            feature = str(preference.get("feature") or "")
            preferred = str(preference.get("preferred_value") or "").casefold()
            candidate_value = feature_values.get(feature)
            if isinstance(candidate_value, list):
                matched = preferred in {
                    str(value).casefold() for value in candidate_value
                }
            else:
                matched = bool(preferred and str(candidate_value or "").casefold() == preferred)
            if matched:
                learning_bonus += 2.0
                learning_matches.append({
                    "feature": feature,
                    "preferred_value": preference.get("preferred_value"),
                    "support_count": preference.get("support_count"),
                })
        learning_bonus = min(6.0, learning_bonus)
        score += learning_bonus
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
            "learning_priority_bonus": round(learning_bonus, 4),
            "learning_preference_matches": learning_matches,
            "learning_policy_version": active_policy.get("policy_version"),
            "learning_policy_sample_count": active_policy.get("sample_count", 0),
            "learning_policy_confidence": active_policy.get("confidence", 0.0),
            "seo_learning_preferences": list(seo_policy.get("recommendations") or [])[:3],
            "learning_preferences_grant_factual_or_numeric_authority": False,
            "learning_preferences_change_evidence_or_publication_gates": False,
            "evidence_reachability": reachability,
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
        "learning_policy_version": active_policy.get("policy_version"),
        "learning_policy_consumed": bool(active_policy),
        "learning_policy_priority_bonus_cap": 6.0,
        "learning_policy_grants_factual_or_numeric_authority": False,
        "occurs_before_targeted_evidence": True,
        "occurs_before_article_generation": True,
        "llm_or_provider_calls": 0,
        "publication_authority_granted": False,
    }
    result["preselection_logical_hash"] = _logical_hash({
        key: value for key, value in result.items() if key != "preselection_logical_hash"
    })
    return result
