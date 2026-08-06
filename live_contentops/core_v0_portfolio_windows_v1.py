"""CORE V0 portfolio windows, concentration penalties, and selection.

TASK_CONTENTOPS_CORE_V0_PORTFOLIO_SELECTION_AND_PLATFORM_VISUAL_ADAPTATION_CORRECTION_V1
— ``SHADOW_ONLY``.

This module makes portfolio concentration *operational* rather than report-only. It sits
between the governed hard gates and package production:

``hard gates -> eligible set -> base rank -> rolling penalties -> portfolio decision``

It owns no editorial judgement and no numeric authority. Base ranking is delegated to the
accepted ``universal_news_candidate_fabric_v2.score_candidate`` where a governed candidate
exists, and otherwise derived only from exact governed fields already present on the case
(authorized claim count, numeric claim count, governed timestamps). Nothing here invents a
score, a fact, a permission, or a publication history.

Two distinct windows are produced:

* ``daily`` covers only the current decision window — the candidates being decided now;
* ``rolling`` covers an explicit prior interval of *accepted* history plus the current
  selected state.

Blocked, deferred, and rejected candidates never count as prior published concentration;
they are retained separately as candidate-universe diagnostics so an operator can see what
was considered without it inflating the published portfolio.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "contentops.core_v0_portfolio_windows.v1"

#: Concentration dimensions measured across a portfolio window.
CONCENTRATION_DIMENSIONS = (
    "domain_family",
    "entities",
    "sector",
    "geography",
    "source_family",
    "content_mode",
    "visual_type",
)

#: Default share above which a dimension value counts as concentrated. Configurable per
#: run: a penalty only reorders *already eligible* candidates and can never open a gate.
DEFAULT_CONCENTRATION_THRESHOLD = 0.34
DEFAULT_CONCENTRATION_PENALTY = 12.0

#: How far back the rolling window reaches from the decision window start.
DEFAULT_ROLLING_HISTORY_DAYS = 90

#: Portfolio dispositions. Hard-gate outcomes are decided upstream and are not in this set.
SELECTED = "SELECTED"
HELD = "HELD_LOWER_PRIORITY"
DEFERRED = "DEFER_FOR_PORTFOLIO_BALANCE"

#: Dispositions that may contribute to *published* rolling concentration. A blocked,
#: rejected, or deferred case is never published history.
ACCEPTED_HISTORY_DISPOSITIONS = frozenset({SELECTED})


class PortfolioWindowError(RuntimeError):
    """Fail-closed portfolio window error."""


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()


def _parse_utc(value: Any) -> datetime | None:
    """Parse a committed governed timestamp without inventing one.

    Returns ``None`` rather than substituting a wall-clock or default date, so a case with
    no governed timestamp is excluded from a dated window instead of being back-dated.
    """
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        # Date-only governed fields (e.g. "2026-05-01") are legitimate.
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def case_event_time(case: Mapping[str, Any]) -> datetime | None:
    """The governed event time for a case, preferring the most specific committed field."""
    for field in (
        "as_of_utc",
        "published_at_utc",
        "known_at_utc",
        "generated_at_utc",
    ):
        parsed = _parse_utc(case.get(field))
        if parsed is not None:
            return parsed
    return None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value else None


def classify_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Project one case onto the taxonomy dimensions used for concentration."""
    return {
        "case_id": case.get("case_id"),
        "domain_family": case.get("domain_family"),
        "sector": case.get("sector"),
        "entities": list(case.get("entities") or []),
        "geography": case.get("geography"),
        "source_family": case.get("source_family"),
        "content_mode": case.get("content_mode"),
        "update_chain": case.get("update_chain"),
        "visual_type": case.get("visual_type"),
        "lane": case.get("lane"),
    }


def _dimension_values(row: Mapping[str, Any], dimension: str) -> list[str]:
    value = row.get(dimension)
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value not in (None, "") else []


def _measure(rows: Sequence[Mapping[str, Any]], threshold: float) -> dict[str, Any]:
    dimensions: dict[str, Any] = {}
    for dimension in CONCENTRATION_DIMENSIONS:
        counter: Counter[str] = Counter()
        for row in rows:
            counter.update(_dimension_values(row, dimension))
        total = sum(counter.values())
        shares = {
            key: round(count / total, 6) if total else 0.0 for key, count in counter.items()
        }
        concentrated = sorted(key for key, share in shares.items() if share > threshold)
        dimensions[dimension] = {
            "distinct_values": len(counter),
            "counts": dict(sorted(counter.items())),
            "shares": dict(sorted(shares.items())),
            "max_share": max(shares.values()) if shares else 0.0,
            "concentrated_values": concentrated,
            "is_concentrated": bool(concentrated),
        }
    return dimensions


# ---------------------------------------------------------------------------
# 1. Portfolio windows
# ---------------------------------------------------------------------------


def build_daily_portfolio_report(
    *,
    decision_window_id: str,
    candidates: Sequence[Mapping[str, Any]],
    excluded: Sequence[Mapping[str, Any]] = (),
    concentration_threshold: float = DEFAULT_CONCENTRATION_THRESHOLD,
) -> dict[str, Any]:
    """Measure concentration across the *current decision window only*.

    Membership is exactly the candidates being decided now. Cases excluded by a hard gate
    are recorded with their exclusion reason as candidate-universe diagnostics; they do not
    contribute to the measured concentration.
    """
    rows = [classify_case(case) for case in candidates]
    times = [t for t in (case_event_time(case) for case in candidates) if t]
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_label": "daily",
        "report_id": f"portfolio-daily-{decision_window_id}",
        "decision_window_id": decision_window_id,
        "basis": "CURRENT_DECISION_WINDOW_CANDIDATES",
        "window_start_utc": _iso(min(times)) if times else None,
        "window_end_utc": _iso(max(times)) if times else None,
        # A daily report measures now, not history: the history window is explicitly empty
        # rather than silently reusing the decision window.
        "history_window_start_utc": None,
        "history_window_end_utc": None,
        "included_current_candidate_ids": sorted(
            str(case.get("case_id")) for case in candidates
        ),
        "included_prior_selected_ids": [],
        "excluded_ids": sorted(str(row.get("case_id")) for row in excluded),
        "exclusion_reasons": {
            str(row.get("case_id")): str(row.get("exclusion_reason"))
            for row in sorted(excluded, key=lambda r: str(r.get("case_id")))
        },
        "case_count": len(rows),
        "concentration_threshold": concentration_threshold,
        "dimensions": _measure(rows, concentration_threshold),
        "diversity_never_forces_filler": True,
        "hard_gates_remain_authoritative": True,
    }
    report["concentrated_dimensions"] = sorted(
        name for name, row in report["dimensions"].items() if row["is_concentrated"]
    )
    report["report_logical_hash"] = _logical_hash(
        {k: v for k, v in report.items() if k != "report_logical_hash"}
    )
    return report


def build_rolling_portfolio_report(
    *,
    decision_window_id: str,
    prior_selected: Sequence[Mapping[str, Any]],
    current_selected: Sequence[Mapping[str, Any]] = (),
    excluded: Sequence[Mapping[str, Any]] = (),
    decision_window_start_utc: str | None = None,
    history_days: int = DEFAULT_ROLLING_HISTORY_DAYS,
    concentration_threshold: float = DEFAULT_CONCENTRATION_THRESHOLD,
) -> dict[str, Any]:
    """Measure concentration across accepted prior history plus current selected state.

    Only accepted/selected history counts. Permission-blocked, evidence-blocked,
    rights-blocked, deferred, and rejected cases are recorded as diagnostics with their
    exclusion reason and never inflate published concentration.

    Every prior entry keeps its original committed timestamp: this window reports when
    governed material was actually dated, and never re-dates history to look current.
    """
    for row in prior_selected:
        disposition = str(row.get("disposition") or SELECTED)
        if disposition not in ACCEPTED_HISTORY_DISPOSITIONS:
            raise PortfolioWindowError(
                f"rolling_history_requires_accepted_disposition:{row.get('case_id')}:{disposition}"
            )

    window_start = _parse_utc(decision_window_start_utc)
    history_end = window_start
    history_start = (
        window_start - timedelta(days=history_days) if window_start else None
    )

    in_window: list[Mapping[str, Any]] = []
    out_of_window: list[dict[str, Any]] = []
    for row in prior_selected:
        event_time = case_event_time(row)
        if history_start and history_end and event_time:
            if history_start <= event_time < history_end:
                in_window.append(row)
            else:
                out_of_window.append(
                    {
                        "case_id": str(row.get("case_id")),
                        "event_time_utc": _iso(event_time),
                        "exclusion_reason": "OUTSIDE_ROLLING_HISTORY_INTERVAL",
                    }
                )
        else:
            out_of_window.append(
                {
                    "case_id": str(row.get("case_id")),
                    "event_time_utc": _iso(event_time),
                    "exclusion_reason": "NO_GOVERNED_EVENT_TIME_OR_WINDOW_BOUND",
                }
            )

    members = list(in_window) + list(current_selected)
    rows = [classify_case(case) for case in members]
    prior_times = [t for t in (case_event_time(row) for row in in_window) if t]
    current_times = [t for t in (case_event_time(row) for row in current_selected) if t]
    all_times = prior_times + current_times

    diagnostics = list(excluded) + out_of_window
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_label": "rolling",
        "report_id": f"portfolio-rolling-{decision_window_id}",
        "decision_window_id": decision_window_id,
        "basis": "ACCEPTED_PUBLICATION_HISTORY_PLUS_CURRENT_SELECTED_STATE",
        "history_window_days": history_days,
        "history_window_start_utc": _iso(history_start),
        "history_window_end_utc": _iso(history_end),
        "window_start_utc": _iso(min(all_times)) if all_times else None,
        "window_end_utc": _iso(max(all_times)) if all_times else None,
        "included_prior_selected_ids": sorted(
            str(row.get("case_id")) for row in in_window
        ),
        "included_current_candidate_ids": sorted(
            str(row.get("case_id")) for row in current_selected
        ),
        "excluded_ids": sorted(str(row.get("case_id")) for row in diagnostics),
        "exclusion_reasons": {
            str(row.get("case_id")): str(row.get("exclusion_reason"))
            for row in sorted(diagnostics, key=lambda r: str(r.get("case_id")))
        },
        "blocked_or_rejected_counted_as_published_history": False,
        "case_count": len(rows),
        "concentration_threshold": concentration_threshold,
        "dimensions": _measure(rows, concentration_threshold),
        "historical_dates_preserved": True,
        "presented_as_current_news": False,
        "diversity_never_forces_filler": True,
        "hard_gates_remain_authoritative": True,
    }
    report["concentrated_dimensions"] = sorted(
        name for name, row in report["dimensions"].items() if row["is_concentrated"]
    )
    report["report_logical_hash"] = _logical_hash(
        {k: v for k, v in report.items() if k != "report_logical_hash"}
    )
    return report


# ---------------------------------------------------------------------------
# 2. Base editorial rank
# ---------------------------------------------------------------------------


def base_editorial_rank(case: Mapping[str, Any], *, candidate: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Derive a base editorial score from governed authority only.

    Where a governed candidate exists, the accepted
    ``universal_news_candidate_fabric_v2.score_candidate`` is the authority. Otherwise the
    score is composed from exact committed governed counts already present on the case —
    never from an invented editorial judgement.
    """
    if candidate is not None:
        from live_contentops.universal_news_candidate_fabric_v2 import score_candidate

        scored = score_candidate(candidate)
        if scored.get("blockers"):
            raise PortfolioWindowError(
                f"governed_scorer_blocked:{case.get('case_id')}:{scored['blockers']}"
            )
        return {
            "case_id": case.get("case_id"),
            "base_score": scored["score"],
            "score_source": "universal_news_candidate_fabric_v2.score_candidate",
            "calibration_state": scored["calibration_state"],
            "available_dimension_count": scored["available_dimension_count"],
            "governed_fields_used": ["ranking_inputs"],
        }

    # Governed-packet case: compose only from exact committed counts on the packet.
    authorized = int(case.get("authorized_claim_count") or 0)
    numeric = int(case.get("numeric_claim_count") or 0)
    score = float(min(100, authorized * 15 + numeric * 10))
    return {
        "case_id": case.get("case_id"),
        "base_score": round(score, 8),
        "score_source": "governed_packet_authorized_claim_counts",
        "calibration_state": "UNCALIBRATED_GOVERNED_COUNT_COMPOSITION",
        "available_dimension_count": 2,
        "governed_fields_used": ["authorized_claim_count", "numeric_claim_count"],
    }


# ---------------------------------------------------------------------------
# 3. Concentration-aware selection
# ---------------------------------------------------------------------------


def apply_concentration_penalties(
    *,
    ranked: Sequence[Mapping[str, Any]],
    rolling_report: Mapping[str, Any],
    penalty: float = DEFAULT_CONCENTRATION_PENALTY,
) -> list[dict[str, Any]]:
    """Penalise already-eligible candidates for over-represented rolling dimensions.

    A penalty can only reorder eligible candidates. It can never admit a case that failed
    an evidence, permission, freshness, or material-delta gate, and it can never manufacture
    a selection when nothing is eligible.

    Every applied penalty records its dimension, the concentrated value, the amount, and
    the prior-history basis (share and counts from the exact rolling report) so an operator
    can audit why a candidate moved.
    """
    dimensions = rolling_report.get("dimensions") or {}
    rolling_hash = str(rolling_report.get("report_logical_hash") or "")
    if not rolling_hash:
        raise PortfolioWindowError("rolling_report_hash_required_for_penalties")

    scored: list[dict[str, Any]] = []
    for row in ranked:
        taxonomy = classify_case(row["case"])
        applied: list[dict[str, Any]] = []
        total_penalty = 0.0
        for dimension in CONCENTRATION_DIMENSIONS:
            measured = dimensions.get(dimension) or {}
            concentrated = set(measured.get("concentrated_values") or [])
            shares = measured.get("shares") or {}
            counts = measured.get("counts") or {}
            for value in _dimension_values(taxonomy, dimension):
                if value not in concentrated:
                    continue
                total_penalty += penalty
                applied.append(
                    {
                        "dimension": dimension,
                        "value": value,
                        "penalty_amount": penalty,
                        "prior_history_basis": {
                            "rolling_report_id": rolling_report.get("report_id"),
                            "rolling_report_logical_hash": rolling_hash,
                            "prior_share": shares.get(value),
                            "prior_count": counts.get(value),
                            "threshold": rolling_report.get("concentration_threshold"),
                            "history_window_start_utc": rolling_report.get(
                                "history_window_start_utc"
                            ),
                            "history_window_end_utc": rolling_report.get(
                                "history_window_end_utc"
                            ),
                        },
                    }
                )
        base_score = float(row["base_score"])
        scored.append(
            {
                "case_id": str(row["case_id"]),
                "lane": row["case"].get("lane"),
                "domain_family": row["case"].get("domain_family"),
                "base_score": round(base_score, 8),
                "base_score_source": row.get("score_source"),
                "concentration_penalty": round(total_penalty, 8),
                "adjusted_score": round(base_score - total_penalty, 8),
                "penalties_applied": applied,
                "rolling_report_logical_hash": rolling_hash,
            }
        )
    return scored


def _rank(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    """Rank descending by score, breaking ties on case_id for determinism."""
    ordered = sorted(rows, key=lambda row: (-float(row[key]), str(row["case_id"])))
    return {str(row["case_id"]): index + 1 for index, row in enumerate(ordered)}


def decide_portfolio(
    *,
    decision_window_id: str,
    eligible: Sequence[Mapping[str, Any]],
    rolling_report: Mapping[str, Any],
    penalty: float = DEFAULT_CONCENTRATION_PENALTY,
    defer_below_adjusted_score: float | None = None,
    max_selected: int | None = None,
) -> dict[str, Any]:
    """Produce an explicit portfolio disposition for every eligible candidate.

    Runs *before* package production so a deferred case never consumes production work.
    Both the base editorial rank and the diversity-adjusted rank are preserved, and the
    decision binds the exact rolling report hash the penalties came from.

    Diversity never forces a selection: a case is only ever moved *down* by concentration,
    never promoted, and a candidate that no longer clears the configured bar is deferred
    rather than replaced by a weaker one.
    """
    if not eligible:
        return {
            "schema_version": SCHEMA_VERSION,
            "decision_window_id": decision_window_id,
            "rolling_report_id": rolling_report.get("report_id"),
            "rolling_report_logical_hash": rolling_report.get("report_logical_hash"),
            "eligible_count": 0,
            "decisions": [],
            "selected_case_ids": [],
            "deferred_case_ids": [],
            "held_case_ids": [],
            "no_publication": True,
            "no_publication_reason": "NO_ELIGIBLE_CANDIDATE_AFTER_HARD_GATES",
            "penalties_applied_before_production": True,
            "diversity_never_forces_filler": True,
        }

    scored = apply_concentration_penalties(
        ranked=eligible, rolling_report=rolling_report, penalty=penalty
    )
    base_ranks = _rank(scored, "base_score")
    adjusted_ranks = _rank(scored, "adjusted_score")

    ordered = sorted(
        scored, key=lambda row: (-float(row["adjusted_score"]), str(row["case_id"]))
    )
    decisions: list[dict[str, Any]] = []
    selected_count = 0
    for row in ordered:
        case_id = str(row["case_id"])
        base_rank = base_ranks[case_id]
        adjusted_rank = adjusted_ranks[case_id]
        reason: str
        if (
            defer_below_adjusted_score is not None
            and float(row["adjusted_score"]) < defer_below_adjusted_score
        ):
            disposition = DEFERRED
            reason = (
                "Adjusted score "
                f"{row['adjusted_score']} is below the configured portfolio balance floor "
                f"{defer_below_adjusted_score} after concentration penalties from "
                f"{rolling_report.get('report_id')}."
            )
        elif max_selected is not None and selected_count >= max_selected:
            disposition = HELD
            reason = (
                f"Portfolio slot limit {max_selected} already filled by higher "
                "diversity-adjusted candidates."
            )
        else:
            disposition = SELECTED
            selected_count += 1
            reason = "Cleared hard gates and holds the top diversity-adjusted position."
        decisions.append(
            {
                **row,
                "base_rank": base_rank,
                "adjusted_rank": adjusted_rank,
                "rank_changed_by_concentration": base_rank != adjusted_rank,
                "disposition": disposition,
                "disposition_reason": reason,
                "produces_package": disposition == SELECTED,
            }
        )

    decision = {
        "schema_version": SCHEMA_VERSION,
        "decision_window_id": decision_window_id,
        "rolling_report_id": rolling_report.get("report_id"),
        "rolling_report_logical_hash": rolling_report.get("report_logical_hash"),
        "concentration_threshold": rolling_report.get("concentration_threshold"),
        "penalty_per_concentrated_value": penalty,
        "defer_below_adjusted_score": defer_below_adjusted_score,
        "max_selected": max_selected,
        "eligible_count": len(decisions),
        "decisions": decisions,
        "selected_case_ids": sorted(
            row["case_id"] for row in decisions if row["disposition"] == SELECTED
        ),
        "deferred_case_ids": sorted(
            row["case_id"] for row in decisions if row["disposition"] == DEFERRED
        ),
        "held_case_ids": sorted(
            row["case_id"] for row in decisions if row["disposition"] == HELD
        ),
        "reordered_case_ids": sorted(
            row["case_id"] for row in decisions if row["rank_changed_by_concentration"]
        ),
        "no_publication": not any(row["disposition"] == SELECTED for row in decisions),
        "penalties_applied_before_production": True,
        "diversity_never_forces_filler": True,
        "hard_gates_remain_authoritative": True,
    }
    decision["decision_logical_hash"] = _logical_hash(
        {k: v for k, v in decision.items() if k != "decision_logical_hash"}
    )
    return decision
