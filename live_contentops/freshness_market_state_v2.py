"""Deterministic article-mode freshness and market-state policy."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

CURRENT_FRAMING_TERMS = ("today", "current", "currently", "just", "latest", "breaking")


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _age_hours(as_of: datetime, value: str | None) -> float | None:
    timestamp = _dt(value)
    return None if timestamp is None else round(max(0.0, (as_of - timestamp).total_seconds() / 3600), 3)


def evaluate_freshness(
    packet: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    policy = {"straight_news_hours": 24.0, "analysis_market_hours": 24.0, "ingest_hours": 24.0, **dict(thresholds or {})}
    as_of = _dt(str(packet.get("as_of_utc") or "")) or datetime.now(timezone.utc)
    events = list(packet.get("events") or [])
    headlines = list(packet.get("headlines") or [])
    docs = list(packet.get("official_source_documents") or [])
    claims = list(packet.get("numeric_claims") or [])
    snapshots = list(packet.get("market_snapshots") or [])
    event_age = min((_age_hours(as_of, row.get("event_time_utc")) for row in events), default=None, key=lambda x: float("inf") if x is None else x)
    headline_age = min((_age_hours(as_of, row.get("published_at_utc")) for row in headlines), default=None, key=lambda x: float("inf") if x is None else x)
    source_age = min((_age_hours(as_of, row.get("published_at_utc") or row.get("release_time_utc")) for row in docs), default=None, key=lambda x: float("inf") if x is None else x)
    market_age = min((_age_hours(as_of, row.get("observation_time_utc")) for row in claims), default=None, key=lambda x: float("inf") if x is None else x)
    ingest_age = min((_age_hours(as_of, row.get("generated_at_utc")) for row in snapshots), default=None, key=lambda x: float("inf") if x is None else x)
    mode = str(request.get("article_mode") or "analysis")
    market_sensitive = bool(request.get("market_sensitive", False))
    market_snapshot_required = bool(
        request.get("market_snapshot_required", market_sensitive)
    )
    fresh_delta = bool(request.get("fresh_material_delta"))
    text = " ".join(str(request.get(key) or "") for key in ("title", "angle", "summary")).casefold()
    blockers = list(packet.get("blockers") or [])
    decision = "PASS"
    if mode == "straight_news" and not any(age is not None and age <= policy["straight_news_hours"] for age in (event_age, headline_age, source_age)):
        blockers.append("straight_news_requires_material_update_inside_window")
    if mode == "analysis" and not fresh_delta and not any(age is not None and age <= policy["straight_news_hours"] for age in (event_age, source_age, market_age)):
        blockers.append("analysis_requires_fresh_material_delta_or_current_reaction")
    if mode == "explainer" and any(term in text.split() for term in CURRENT_FRAMING_TERMS) and not fresh_delta:
        blockers.append("explainer_current_framing_requires_fresh_evidence")
    if market_snapshot_required and (market_age is None or market_age > policy["analysis_market_hours"]):
        blockers.append("market_sensitive_story_snapshot_stale_or_missing")
    if market_snapshot_required and (ingest_age is None or ingest_age > policy["ingest_hours"]):
        blockers.append("market_sensitive_story_ingest_stale_or_missing")
    if blockers:
        decision = "DOWNGRADE_TO_EXPLAINER" if mode in {"straight_news", "analysis"} and not market_sensitive and request.get("allow_mode_downgrade") else "BLOCK"
    return {
        "schema_version": "contentops.freshness_market_state_decision.v2",
        "decision": decision,
        "requested_article_mode": mode,
        "effective_article_mode": "explainer" if decision == "DOWNGRADE_TO_EXPLAINER" else mode,
        "market_sensitive": market_sensitive,
        "market_snapshot_required": market_snapshot_required,
        "event_age_hours": event_age,
        "headline_age_hours": headline_age,
        "primary_source_age_hours": source_age,
        "latest_market_observation_age_hours": market_age,
        "latest_database_ingest_age_hours": ingest_age,
        "expected_source_cadence": request.get("expected_source_cadence", "config_required"),
        "market_session_state": (snapshots[0].get("market_session_state") if snapshots else "unknown"),
        "fresh_material_delta": fresh_delta,
        "thresholds": policy,
        "blockers": list(dict.fromkeys(blockers)),
        "duplicate_policy_is_separate": True,
    }
