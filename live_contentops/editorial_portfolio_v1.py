"""Editorial portfolio, novelty, and update-chain intelligence for the Final Daily App.

Owner decision 2026-08-10 (V1 realignment): every editorial decision must know what ContentOps
already published, classify each viable cluster explicitly as
BREAKING_NEW_STORY / MATERIAL_FOLLOW_UP / DEEPEN_EXISTING_STORY / LOW_DELTA_REPEAT / HOLD, and
operate under the owner-locked four-opportunity quality probation with no publication minimum.
The broader 5-8 useful-article band remains long-term portfolio context only and creates no
filler pressure, automatic wakeup, or schedule-scaling authority.

This module is deterministic editorial intelligence feeding the existing canonical newsroom
boundary. It is not a second newsroom, not a second scheduler, and not a second store.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Optional, Sequence

DECISION_BREAKING_NEW_STORY = "BREAKING_NEW_STORY"
DECISION_MATERIAL_FOLLOW_UP = "MATERIAL_FOLLOW_UP"
DECISION_DEEPEN_EXISTING_STORY = "DEEPEN_EXISTING_STORY"
DECISION_LOW_DELTA_REPEAT = "LOW_DELTA_REPEAT"
DECISION_HOLD = "HOLD"
DECISION_NO_PUBLICATION = "NO_PUBLICATION"

DAILY_TARGET_BAND = (0, 4)
LONG_TERM_USEFUL_ARTICLE_PORTFOLIO_GOAL = (5, 8)
CORE_DECISION_OPPORTUNITIES_PER_DAY = 4

ARTICLE_MODE_BREAKING_BRIEF = "BREAKING_BRIEF"
ARTICLE_MODE_FOLLOW_UP_UPDATE = "FOLLOW_UP_UPDATE"
ARTICLE_MODE_STANDARD_NEWS_ANALYSIS = "STANDARD_NEWS_ANALYSIS"
ARTICLE_MODE_CAPITAL_CHRONICLE_DEEP_DIVE = "CAPITAL_CHRONICLE_DEEP_DIVE"
ARTICLE_MODE_EVERGREEN_CONTEXT = "EVERGREEN_CONTEXT"


@dataclass(frozen=True)
class PublishedArticleRef:
    story_identity: str
    title: str
    published_at_utc: str
    public_object_id: Optional[str]
    canonical_url_hash: Optional[str]
    content_hash: Optional[str]
    entities: tuple
    update_chain_identity: Optional[str]
    article_mode: Optional[str]
    article_identity: Optional[str] = None
    canonical_url: Optional[str] = None
    full_text: Optional[str] = None
    content_status: str = "CONTENT_UNAVAILABLE"
    body_source: Optional[str] = None
    source_work_item_id: Optional[str] = None
    derivative_public_objects: tuple = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "story_identity": self.story_identity,
            "title": self.title,
            "published_at_utc": self.published_at_utc,
            "public_object_id": self.public_object_id,
            "canonical_url_hash": self.canonical_url_hash,
            "content_hash": self.content_hash,
            "entities": list(self.entities),
            "update_chain_identity": self.update_chain_identity,
            "article_mode": self.article_mode,
            "article_identity": self.article_identity,
            "canonical_url": self.canonical_url,
            "full_text": self.full_text,
            "content_status": self.content_status,
            "body_source": self.body_source,
            "source_work_item_id": self.source_work_item_id,
            "derivative_public_objects": [dict(value) for value in self.derivative_public_objects],
        }


def _normalize_entity(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _entity_tokens(entity: str) -> set:
    return {token for token in entity.split(" ") if len(token) >= 3}


def entity_overlap_score(cluster_entities: Sequence[str], article_entities: Sequence[str]) -> float:
    """Deterministic Jaccard-style overlap between entity sets (>= 3-char tokens)."""
    left: set = set()
    right: set = set()
    for value in cluster_entities:
        left |= _entity_tokens(_normalize_entity(value))
    for value in article_entities:
        right |= _entity_tokens(_normalize_entity(value))
    if not left or not right:
        return 0.0
    return len(left & right) / float(len(left | right))


def material_delta_evaluation(
    cluster: Mapping[str, Any], article: PublishedArticleRef
) -> dict[str, Any]:
    """Explain the deterministic update delta without treating X as factual evidence."""
    summary_blob = " ".join(str(value) for value in (cluster.get("leaf_summaries") or []))
    lowered = summary_blob.lower()
    markers = (
        "updated", "revises", "corrects", "new data", "confirmed", "announced",
        "released", "according to new", "follow", "effective", "filed", "approved",
    )
    marker_hits = sorted({marker for marker in markers if marker in lowered})
    official_urls = sorted({
        str(value) for value in (cluster.get("official_source_urls") or []) if str(value).strip()
    })
    reason_codes: list[str] = []
    if marker_hits:
        reason_codes.append("NEW_INFORMATION_LANGUAGE_PRESENT")
    if official_urls:
        reason_codes.append("NEW_OFFICIAL_SOURCE_CANDIDATE_PRESENT")
    chain_identity = str(cluster.get("update_chain_identity") or cluster.get("cluster_id") or "")
    if chain_identity and article.update_chain_identity == chain_identity:
        reason_codes.append("CANONICAL_UPDATE_CHAIN_MATCH")
    signal_count = len(marker_hits) + int(bool(official_urls))
    return {
        "signal_count": signal_count,
        "reason_codes": reason_codes,
        "marker_hits": marker_hits,
        "new_official_source_candidate_count": len(official_urls),
        "delta_summary": (
            "; ".join(reason_codes) if reason_codes else "No explicit material delta signal detected."
        ),
        "x_content_grants_factual_authority": False,
    }


def material_delta_signals(cluster: Mapping[str, Any], article: PublishedArticleRef) -> int:
    """Backward-compatible integer projection of the auditable delta evaluation."""
    return int(material_delta_evaluation(cluster, article)["signal_count"])


def classify_story_novelty(
    cluster: Mapping[str, Any],
    *,
    published_corpus: Sequence[PublishedArticleRef],
    cc_context_richness: float = 0.0,
    now: Optional[datetime] = None,
    recent_coverage_window_hours: float = 72.0,
) -> dict[str, Any]:
    """Explicit deterministic classification of a viable cluster against the published corpus.

    X content never grants factual authority here: this only measures novelty/update-chain
    relations against what ContentOps already published, plus Capital Chronicle context
    richness (editorial intelligence), never numeric truth.
    """
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    entities = [str(value) for value in (cluster.get("entities_topics") or [])]
    best_match: Optional[PublishedArticleRef] = None
    best_overlap = 0.0
    for article in published_corpus:
        overlap = entity_overlap_score(entities, article.entities)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = article
    high_overlap = best_overlap >= 0.45
    moderate_overlap = best_overlap >= 0.25
    recent_match = False
    matched_age_hours: Optional[float] = None
    if best_match is not None and best_match.published_at_utc:
        try:
            published_dt = datetime.fromisoformat(str(best_match.published_at_utc).replace("Z", "+00:00"))
            if published_dt.tzinfo is None:
                published_dt = published_dt.replace(tzinfo=timezone.utc)
            matched_age_hours = (moment - published_dt.astimezone(timezone.utc)).total_seconds() / 3600.0
            recent_match = matched_age_hours <= recent_coverage_window_hours
        except ValueError:
            matched_age_hours = None
    delta = material_delta_evaluation(cluster, best_match) if best_match else {
        "signal_count": 0,
        "reason_codes": [],
        "marker_hits": [],
        "new_official_source_candidate_count": 0,
        "delta_summary": "No prior article matched.",
        "x_content_grants_factual_authority": False,
    }
    delta_signals = int(delta["signal_count"])
    chain_identity = str(cluster.get("update_chain_identity") or cluster.get("cluster_id") or "")

    if best_match and chain_identity and best_match.update_chain_identity == chain_identity:
        if delta_signals >= 1:
            decision = DECISION_MATERIAL_FOLLOW_UP
        else:
            decision = DECISION_LOW_DELTA_REPEAT
    elif high_overlap and recent_match and delta_signals == 0:
        decision = DECISION_LOW_DELTA_REPEAT
    elif high_overlap and delta_signals >= 1:
        decision = DECISION_MATERIAL_FOLLOW_UP
    elif moderate_overlap and not recent_match and cc_context_richness >= 0.5:
        decision = DECISION_DEEPEN_EXISTING_STORY
    elif not moderate_overlap:
        decision = DECISION_BREAKING_NEW_STORY
    else:
        decision = DECISION_HOLD

    recommended_mode = {
        DECISION_BREAKING_NEW_STORY: ARTICLE_MODE_BREAKING_BRIEF,
        DECISION_MATERIAL_FOLLOW_UP: ARTICLE_MODE_FOLLOW_UP_UPDATE,
        DECISION_DEEPEN_EXISTING_STORY: ARTICLE_MODE_CAPITAL_CHRONICLE_DEEP_DIVE,
        DECISION_LOW_DELTA_REPEAT: "HOLD",
        DECISION_HOLD: "HOLD",
    }[decision]
    return {
        "schema_version": "contentops.editorial_story_novelty.v1",
        "decision": decision,
        "recommended_article_mode": recommended_mode,
        "best_prior_article": best_match.story_identity if best_match else None,
        "best_prior_title": best_match.title if best_match else None,
        "entity_overlap": round(best_overlap, 4),
        "matched_article_age_hours": round(matched_age_hours, 3) if matched_age_hours is not None else None,
        "material_delta_signals": delta_signals,
        "material_delta_evaluation": delta,
        "update_chain_match": bool(best_match and chain_identity and best_match.update_chain_identity == chain_identity),
        "cc_context_richness": round(float(cc_context_richness), 4),
        "grants_factual_or_numeric_authority": False,
    }


def build_material_follow_up_context(
    cluster: Mapping[str, Any],
    decision: Mapping[str, Any],
    published_corpus: Sequence[PublishedArticleRef],
) -> Optional[dict[str, Any]]:
    """Build the compact previous-vs-new context carried to evidence and writing."""
    prior_identity = str(decision.get("best_prior_article") or "")
    prior = next(
        (article for article in published_corpus if article.story_identity == prior_identity),
        None,
    )
    if prior is None:
        return None
    return {
        "schema_version": "contentops.material_follow_up_context.v1",
        "previous_story_identity": prior.story_identity,
        "previous_article_identity": prior.article_identity,
        "previous_title": prior.title,
        "previous_body_sha256": prior.content_hash,
        "previous_published_at_utc": prior.published_at_utc,
        "previous_content_status": prior.content_status,
        "previous_full_text": prior.full_text,
        "previous_canonical_url": prior.canonical_url,
        "current_update_chain_identity": str(
            cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
        ),
        "new_headline_ids": [str(value) for value in (cluster.get("headline_ids") or [])],
        "new_official_source_candidates": [
            str(value) for value in (cluster.get("official_source_urls") or [])
        ],
        "material_delta_reason_codes": list(
            (decision.get("material_delta_evaluation") or {}).get("reason_codes") or []
        ),
        "material_delta_summary": str(
            (decision.get("material_delta_evaluation") or {}).get("delta_summary") or ""
        ),
        "grants_factual_or_numeric_authority": False,
    }


def portfolio_state_today(
    published_corpus: Sequence[PublishedArticleRef],
    *,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Current-day portfolio awareness: counts, modes, entity concentration, recency."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    day_start = datetime(moment.year, moment.month, moment.day, tzinfo=timezone.utc)
    todays: list[PublishedArticleRef] = []
    for article in published_corpus:
        try:
            published_dt = datetime.fromisoformat(str(article.published_at_utc).replace("Z", "+00:00"))
            if published_dt.tzinfo is None:
                published_dt = published_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        published_utc = published_dt.astimezone(timezone.utc)
        if day_start <= published_utc < day_start + timedelta(days=1):
            todays.append(article)
    entity_counts: dict[str, int] = {}
    for article in todays:
        for entity in article.entities:
            normalized = _normalize_entity(entity)
            if normalized:
                entity_counts[normalized] = entity_counts.get(normalized, 0) + 1
    mode_counts: dict[str, int] = {}
    for article in todays:
        mode = str(article.article_mode or "UNKNOWN")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    return {
        "schema_version": "contentops.editorial_portfolio_state.v1",
        "as_of_utc": moment.isoformat().replace("+00:00", "Z"),
        "published_today_count": len(todays),
        "daily_target_band": list(DAILY_TARGET_BAND),
        "publication_minimum": 0,
        "routine_publication_ceiling": 4,
        "remaining_target_min": 0,
        "long_term_useful_article_portfolio_goal": list(
            LONG_TERM_USEFUL_ARTICLE_PORTFOLIO_GOAL
        ),
        "long_term_goal_creates_filler_pressure": False,
        "article_mode_counts": mode_counts,
        "entity_concentration_top": sorted(
            ({"entity": entity, "count": count} for entity, count in entity_counts.items()),
            key=lambda row: (-row["count"], row["entity"]),
        )[:8],
        "recent_publication_timestamps_utc": sorted(
            (article.published_at_utc for article in todays), reverse=True
        ),
    }


def concentration_penalty(cluster_entities: Sequence[str], portfolio: Mapping[str, Any]) -> float:
    """Deterministic 0..1 penalty: higher when the cluster's entities were already covered
    repeatedly today. Repetition is only justified by an explicit material delta elsewhere."""
    concentration = {row["entity"]: int(row["count"]) for row in (portfolio.get("entity_concentration_top") or [])}
    if not concentration:
        return 0.0
    scores: list[float] = []
    for entity in cluster_entities:
        normalized = _normalize_entity(entity)
        if not normalized:
            continue
        for covered_entity, count in concentration.items():
            overlap = entity_overlap_score([normalized], [covered_entity])
            if overlap > 0.0:
                scores.append(min(1.0, overlap * min(count, 4) / 4.0))
    return round(max(scores), 4) if scores else 0.0


def bootstrap_portfolio_policy() -> dict[str, Any]:
    """Owner-locked four-window quality-probation portfolio configuration."""
    return {
        "schema_version": "contentops.editorial_portfolio_policy.v1",
        "policy_version": "portfolio.quality_probation_four_window.v1",
        "daily_target_band": list(DAILY_TARGET_BAND),
        "publication_minimum": 0,
        "routine_publication_ceiling": 4,
        "long_term_useful_article_portfolio_goal": list(
            LONG_TERM_USEFUL_ARTICLE_PORTFOLIO_GOAL
        ),
        "core_decision_opportunities_per_day": CORE_DECISION_OPPORTUNITIES_PER_DAY,
        "material_event_wakeups_enabled": False,
        "material_event_priority_next_scheduled_opportunity": True,
        "manual_go_exception_enabled": True,
        "automatic_schedule_scaling_enabled": False,
        "schedule_owner_locked": True,
        "min_spacing_minutes": 60,
        "saturation_daily_hard_cap": 10,
        "concentration_same_entity_daily_soft_cap": 2,
        "filler_fabrication_permitted": False,
        "weakened_factual_or_numeric_authority_permitted": False,
    }
