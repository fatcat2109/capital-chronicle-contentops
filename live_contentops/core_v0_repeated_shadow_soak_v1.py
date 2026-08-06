"""Repeated multi-day SHADOW_ONLY soak over the accepted CORE V0 pipeline.

Work Package E. This module does **not** introduce a second production runner, state
store, scheduler, approval system, outbox, provider gateway, or analytical engine. It is
a deterministic driver that calls the accepted Work Package C/D pipeline
(:func:`live_contentops.core_v0_cohort_shadow_runner_v1.run_cohort`) once per logical
newsroom day, against the accepted Wave 02 durable operational store.

Three properties make the soak auditable:

* **Deterministic logical clock.** Every timestamp comes from an explicit logical clock
  seeded from a committed base date. Nothing reads the wall clock, so two runs with the
  same inputs produce byte-identical artifacts (runtime measurements excepted, and those
  are reported separately and explicitly).
* **Accelerated, not calendar.** The soak compresses N logical newsroom days into one
  local command. It is never described as N calendar days of availability; live calendar
  uptime remains for the separately authorized live cohort.
* **Zero live action.** Every artifact carries the accepted zero-live-action envelope and
  is asserted before it is written.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.core_v0_cohort_shadow_runner_v1 import (
    persist_cohort,
    run_cohort,
    verify_cohort_replay,
)
from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
    policy_binding,
    verify_policy_integrity,
)
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    DualLaneShadowError,
    _canonical_json,
    _logical_hash,
    assert_zero_live_action,
    zero_live_action_flags,
)

SCHEMA_VERSION = "contentops.core_v0_repeated_shadow_soak.v1"
TASK_LABEL = "TASK_CONTENTOPS_CORE_V0_REPEATED_SHADOW_SOAK_AND_RECOVERY_V1"
OPERATING_MODE = "SHADOW_ONLY"

#: The soak is time-compressed. This label is stamped on every artifact so no reader can
#: mistake it for a calendar-duration availability claim.
SOAK_CLASS = "ACCELERATED_LOGICAL_SOAK_NOT_CALENDAR_UPTIME"

#: First logical newsroom day. Chosen to continue the accepted Work Package D window
#: (`2026-07-15`) rather than invent an unrelated date.
DEFAULT_FIRST_LOGICAL_DAY = "2026-07-15"
DEFAULT_LOGICAL_DAYS = 10

#: Each logical newsroom day runs these intake windows. Three windows per day over ten
#: days gives thirty window decisions without lowering any evidence or quality gate.
INTAKE_WINDOWS: tuple[dict[str, str], ...] = (
    {"window_slot": "pre_open", "opens_utc": "00:00:00", "cutoff_utc": "13:30:00"},
    {"window_slot": "us_open", "opens_utc": "13:30:00", "cutoff_utc": "20:00:00"},
    {"window_slot": "us_close", "opens_utc": "20:00:00", "cutoff_utc": "24:00:00"},
)

SOAK_SUMMARY_FILENAME = "soak_run_summary.json"
SOAK_DAYS_FILENAME = "soak_logical_days.json"
SOAK_DRILLS_FILENAME = "soak_recovery_drills.json"
SOAK_SLO_FILENAME = "soak_slo_report.json"
SOAK_LAUNCH_EDGE_FILENAME = "soak_launch_edge.json"
SOAK_REPORT_MD_FILENAME = "soak_report.md"
SOAK_V5_SNAPSHOT_FILENAME = "v5_soak_snapshot.json"


class SoakError(RuntimeError):
    """Fail-closed repeated-soak composition error."""


# ---------------------------------------------------------------------------
# Deterministic logical clock
# ---------------------------------------------------------------------------


class LogicalClock:
    """A deterministic, explicitly advanced clock.

    The durable store accepts a ``now_fn``; handing it this clock makes lease expiry,
    heartbeat freshness, and every recorded timestamp a function of logical time rather
    than wall-clock time. That is what lets a ten-day soak with real lease-expiry drills
    run in seconds and still be replayable.
    """

    def __init__(self, start_utc: str) -> None:
        self._start = _parse_utc(start_utc)
        self._now = self._start
        self._ticks = 0

    def now(self) -> datetime:
        return self._now

    def now_iso(self) -> str:
        return _iso(self._now)

    def advance(self, *, seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0) -> str:
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        if delta < timedelta(0):
            raise SoakError("logical_clock_cannot_move_backwards")
        self._now = self._now + delta
        self._ticks += 1
        return _iso(self._now)

    def set_to(self, value: str) -> str:
        target = _parse_utc(value)
        if target < self._now:
            raise SoakError(f"logical_clock_cannot_move_backwards:{value}")
        self._now = target
        self._ticks += 1
        return _iso(self._now)

    @property
    def tick_count(self) -> int:
        return self._ticks

    @property
    def elapsed_logical_seconds(self) -> int:
        return int((self._now - self._start).total_seconds())


def _parse_utc(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive
        raise SoakError(f"unparseable_utc_timestamp:{value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Logical newsroom days and intake windows
# ---------------------------------------------------------------------------


def build_logical_day_plan(
    *,
    first_day: str = DEFAULT_FIRST_LOGICAL_DAY,
    logical_days: int = DEFAULT_LOGICAL_DAYS,
) -> list[dict[str, Any]]:
    """Produce the deterministic logical-day / intake-window plan for the soak."""
    if logical_days < 1:
        raise SoakError(f"logical_days_must_be_positive:{logical_days}")
    base = _parse_utc(f"{first_day}T00:00:00Z")
    if _iso(base)[:10] != str(first_day):
        raise SoakError(f"first_day_must_be_a_utc_date:{first_day}")

    plan: list[dict[str, Any]] = []
    for index in range(logical_days):
        day_start = base + timedelta(days=index)
        day_end = day_start + timedelta(days=1)
        day_id = _iso(day_start)[:10]
        windows = [
            {
                "window_id": f"{day_id}-{slot['window_slot']}",
                "logical_day_id": day_id,
                "window_slot": slot["window_slot"],
                "window_index": position,
                "window_opens_utc": _iso(day_start + _clock_offset(slot["opens_utc"])),
                "window_cutoff_utc": _iso(day_start + _clock_offset(slot["cutoff_utc"])),
            }
            for position, slot in enumerate(INTAKE_WINDOWS)
        ]
        plan.append(
            {
                "logical_day_id": day_id,
                "logical_day_index": index,
                "decision_window_id": day_id,
                "decision_window_start_utc": _iso(day_start),
                "decision_window_end_utc": _iso(day_end),
                "intake_windows": windows,
                "intake_window_count": len(windows),
            }
        )
    return plan


def _clock_offset(hhmmss: str) -> timedelta:
    hours, minutes, seconds = (int(part) for part in str(hhmmss).split(":"))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


# ---------------------------------------------------------------------------
# One logical newsroom day
# ---------------------------------------------------------------------------


def run_logical_day(
    *,
    repo_root: Path,
    day: Mapping[str, Any],
    chart_output_dir: Path,
    derivative_output_dir: Path,
    accepted_history: Sequence[Mapping[str, Any]],
    clock: LogicalClock,
    concentration_threshold: float | None = None,
    concentration_penalty: float | None = None,
    portfolio_balance_floor: float | None = None,
    max_selected: int | None = None,
) -> dict[str, Any]:
    """Run one logical newsroom day through the accepted cohort pipeline.

    The accepted pipeline is called exactly as Work Package D calls it; only the decision
    window and the accumulated accepted-publication history differ per day. That is what
    makes each day a genuinely different decision rather than the same run repeated.
    """
    clock.set_to(str(day["decision_window_start_utc"]))
    started = time.perf_counter()

    cohort = run_cohort(
        repo_root=repo_root,
        chart_output_dir=chart_output_dir,
        derivative_output_dir=derivative_output_dir,
        concentration_threshold=concentration_threshold,
        concentration_penalty=concentration_penalty,
        portfolio_balance_floor=portfolio_balance_floor,
        decision_window_id=str(day["decision_window_id"]),
        decision_window_start_utc=str(day["decision_window_start_utc"]),
        decision_window_end_utc=str(day["decision_window_end_utc"]),
        accepted_publication_history=list(accepted_history),
        max_selected=max_selected,
    )
    runtime_seconds = round(time.perf_counter() - started, 4)

    # Each intake window is an explicit governed decision, including the truthful
    # no-op windows. A window that produced nothing is still a completed decision.
    decision = cohort["portfolio_decision"]
    selected_ids = list(decision.get("selected_case_ids") or [])
    window_decisions = _window_decisions(day, cohort, selected_ids)

    clock.set_to(str(day["decision_window_end_utc"]))
    result = {
        "schema_version": SCHEMA_VERSION,
        "logical_day_id": str(day["logical_day_id"]),
        "logical_day_index": int(day["logical_day_index"]),
        "decision_window_id": str(day["decision_window_id"]),
        "decision_window_start_utc": str(day["decision_window_start_utc"]),
        "decision_window_end_utc": str(day["decision_window_end_utc"]),
        "soak_class": SOAK_CLASS,
        "intake_windows": window_decisions,
        "intake_window_count": len(window_decisions),
        "windows_completed": sum(1 for row in window_decisions if row["window_completed"]),
        "outcome_counts": dict(cohort["outcome_counts"]),
        "selected_case_ids": selected_ids,
        "deferred_case_ids": list(decision.get("deferred_case_ids") or []),
        "held_case_ids": list(decision.get("held_case_ids") or []),
        "no_publication": bool(decision.get("no_publication")),
        "portfolio_daily_report_id": cohort["portfolio_daily"]["report_id"],
        "portfolio_daily_logical_hash": cohort["portfolio_daily"]["report_logical_hash"],
        "portfolio_rolling_report_id": cohort["portfolio_rolling"]["report_id"],
        "portfolio_rolling_logical_hash": cohort["portfolio_rolling"]["report_logical_hash"],
        "rolling_report_logical_hash_used_by_selection": cohort[
            "rolling_report_logical_hash_used_by_selection"
        ],
        "accepted_history_case_count": len(accepted_history),
        "runtime_seconds": runtime_seconds,
        "cohort": cohort,
        **policy_binding(),
        **zero_live_action_flags(),
    }
    result["logical_day_hash"] = _logical_hash(
        {k: v for k, v in result.items() if k not in {"runtime_seconds", "cohort"}}
    )
    return result


def _window_decisions(
    day: Mapping[str, Any],
    cohort: Mapping[str, Any],
    selected_ids: Sequence[str],
) -> list[dict[str, Any]]:
    """Attribute the day's governed decision across its intake windows.

    Selection is a whole-day portfolio decision in the accepted pipeline, so the soak
    does not pretend each window ran an independent selection. It records the window as a
    completed decision and attributes selected stories deterministically to windows. A
    window with no attributed story is a truthful governed no-op, not a failure.
    """
    windows = list(day["intake_windows"])
    rows: list[dict[str, Any]] = []
    for position, window in enumerate(windows):
        attributed = [
            case_id
            for index, case_id in enumerate(sorted(selected_ids))
            if index % len(windows) == position
        ]
        rows.append(
            {
                "window_id": str(window["window_id"]),
                "logical_day_id": str(window["logical_day_id"]),
                "window_slot": str(window["window_slot"]),
                "window_index": int(window["window_index"]),
                "window_opens_utc": str(window["window_opens_utc"]),
                "window_cutoff_utc": str(window["window_cutoff_utc"]),
                "window_completed": True,
                "window_outcome": (
                    "SELECTION_ATTRIBUTED" if attributed else "GOVERNED_NO_OP_WINDOW"
                ),
                "attributed_selected_case_ids": attributed,
                "decision_window_id": str(cohort["decision_window_id"]),
            }
        )
    return rows


def accepted_history_rows_for_day(day_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project one day's selected cases into accepted-publication history rows.

    Only a case the portfolio actually selected *and* whose canonical review passed is
    projected. A blocked, deferred, or duplicate case never enters published history —
    that is the same rule the accepted rolling report already enforces.
    """
    cohort = day_result["cohort"]
    selected = set(day_result["selected_case_ids"])
    rows: list[dict[str, Any]] = []
    for case in cohort["cases"]:
        case_id = str(case["case_id"])
        if case_id not in selected or case.get("review_result") != "PASS":
            continue
        rows.append(
            {
                "case_id": f"{day_result['logical_day_id']}-{case_id}",
                "lane": case.get("lane"),
                "domain_family": case.get("domain_family"),
                "sector": case.get("sector"),
                "entities": list(case.get("entities") or []),
                "geography": case.get("geography"),
                "source_family": case.get("source_family"),
                "content_mode": case.get("content_mode"),
                "visual_type": case.get("visual_type"),
                "story_type": case.get("story_type"),
                "update_chain": case.get("update_chain"),
                "duplicate_key": case.get("duplicate_key") or case.get("update_chain"),
                "disposition": "SELECTED",
                "history_class": "SOAK_LOGICAL_DAY_SELECTED",
                "material_class": "historical_evaluation_material",
                "presented_as_current_news": False,
                "published_at_utc": str(day_result["decision_window_start_utc"]),
                "as_of_utc": str(day_result["decision_window_start_utc"]),
            }
        )
    return rows
