"""One always-on Final Daily App supervisor over the canonical production boundary.

This module is the first user-visible capability of the Final Daily App V1. It is a thin
coordination layer that:

* loads a deterministic, versioned bootstrap ``EditorialWindowPolicy``;
* gives every editorial decision window a deterministic idempotency identity;
* persists window state through the EXISTING ``durable_operational_store_v1`` store;
* routes the ACTUAL newsroom/publication work through the canonical
  ``ContentOpsProductionOrchestrator`` public facade (never a second pipeline);
* stays cheap when idle (no LLM / provider calls unless a window is due);
* survives restart and duplicate ticks without creating a second editorial cycle;
* exposes a small material-event wakeup seam over governed discovery metadata;
* exposes a one-shot/tick mode that exercises the SAME idempotency code as run-forever.

It is NOT a second newsroom, state store, approval engine, publisher, provider gateway, or
analytics engine. Performance observation, passive interaction analysis, and bounded learning
reuse the canonical durable store and publication coordinator.
"""
from __future__ import annotations

import json
import os
import time
from uuid import uuid4
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

SCHEMA_VERSION = "contentops.daily_app_supervisor.v1"

TRIGGER_SCHEDULED = "SCHEDULED"
TRIGGER_MATERIAL_EVENT = "MATERIAL_EVENT"
#: Operator "run editorial cycle now" requests. Per owner decision 2026-08-10 (V1 realignment):
#: Run Now uses the SAME canonical newsroom authority as scheduled/material-event cycles. It
#: means "make an editorial decision now using the continuously maintained current intelligence
#: universe" — no second newsroom, no weakened factual/numeric/evidence/review authority.
TRIGGER_OPERATOR_REQUESTED = "OPERATOR_REQUESTED"

#: Canonical Capital Chronicle main-project root, bound read-only into editorial cycles so the
#: canonical evidence acquirer and the Capital Chronicle data catalog can refine decisions with
#: actual Capital Chronicle context. ContentOps never mutates anything under this root.
CANONICAL_CAPITAL_CHRONICLE_ROOT = Path(r"A:\Capital Chronicle\Main App")

OPERATING_MODES = frozenset(
    {"AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH"}
)
SCHEDULED_EDITORIAL_OWNER_FDA_G = "FDA_G_SUPERVISOR"
SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP = "NATIVE_DESKTOP_AUTOMATION"
SCHEDULED_EDITORIAL_OWNERS = frozenset(
    {SCHEDULED_EDITORIAL_OWNER_FDA_G, SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP}
)
NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID = {
    "v1-newsroom-london-1700": "london_1700_bangkok",
    "v1-newsroom-new-york-2100": "new_york_2100_bangkok",
    "v1-newsroom-new-york-2300": "new_york_2300_bangkok",
    "v1-newsroom-new-york-0100": "new_york_0100_bangkok",
}

#: Work-item states that indicate an editorial window has already been executed (or recovered)
#: and must not be re-executed. Only DISCOVERED is fresh. EVIDENCE_PENDING is handled
#: separately: an active original lease is left alone, while a released/expired claim resumes
#: from the durable opportunity/stage checkpoints when they exist.
WINDOW_EXECUTED_STATES = frozenset(
    {
        "EVIDENCE_READY",
        "EVIDENCE_BLOCKED",
        "ASSIGNMENT_CANDIDATE",
        "ASSIGNED",
        "DEFERRED",
        "DUPLICATE",
        "REJECTED",
        "PRODUCTION_IN_PROGRESS",
        "REVIEW_BLOCKED",
        "REVIEW_READY",
        "OPERATOR_PENDING",
        "APPROVED_EXACT",
        "HELD",
        "EXPIRED",
        "OUTBOX_READY",
        "DISPATCHING",
        "PARTIAL_SUCCESS",
        "UNKNOWN_WRITE",
        "DISPATCH_BLOCKED",
        "DISPATCH_COMPLETE",
        "RECONCILING",
        "COMPLETE",
        "DEAD_LETTER",
        "OPERATOR_RECOVERY_REQUIRED",
        "OBSERVATION_PENDING",
        "LEARNING_REVIEW_READY",
        "CLOSED",
    }
)

WINDOW_POLICY_ID = "contentops.editorial_window_policy.v1"
WINDOW_POLICY_VERSION = "autonomous_daily_output_four_window.v1"

NOT_IMPLEMENTED_NOT_DUE = "NOT_IMPLEMENTED_NOT_DUE"

#: The Final Daily App production epoch. A fresh production durable store begins a NEW runtime
#: epoch; historical Temp / shadow / soak / controlled-test windows must never be backfilled. A
#: scheduled window is only eligible when its start is at/after the production epoch start.
PRODUCTION_EPOCH_METRIC_ID = "metric_contentops_production_epoch_start_utc"
PRODUCTION_EPOCH_METRIC_NAME = "contentops_production_epoch_start_utc"
PREPARED_CANDIDATE_CHECKPOINT_NAME = "rolling_x_prepared_candidate_state_v1.json"
SOURCE_ROUTE_HEALTH_STATE_NAME = "source_route_health_v1.json"


class ProductionEpochConflictError(RuntimeError):
    """A configured production epoch conflicts with the write-once persisted epoch.

    The persisted production epoch is write-once runtime authority for the historical-replay
    boundary. It may be initialized exactly once and re-read idempotently, but it must NEVER be
    overwritten by a conflicting configured value (CLI restart flags, drift, etc.). This failure
    is raised closed instead of silently rewriting the boundary.
    """

    def __init__(self, *, persisted: Optional[datetime], configured: Optional[datetime]) -> None:
        self.persisted = persisted
        self.configured = configured
        super().__init__(
            "production_epoch_conflict: persisted={} configured={} (persisted epoch is immutable)"
            .format(
                _iso_utc(persisted) if persisted else None,
                _iso_utc(configured) if configured else None,
            )
        )


#: Canonical publication-lifecycle statuses (write-once durable truth).
STATUS_DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
STATUS_UNKNOWN_WRITE = "UNKNOWN_WRITE"
STATUS_CONTROLLED_NO_WRITE = "CONTROLLED_NO_PUBLIC_WRITE"

RECONCILE_CONFIRMED = "RECONCILED_CONFIRMED"
RECONCILE_CONTROLLED_NO_WRITE = "RECONCILED_CONTROLLED_NO_WRITE"
RECONCILE_PENDING_READBACK = "RECONCILIATION_PENDING_READBACK"
RECONCILE_PENDING_OPERATOR = "RECONCILIATION_PENDING_OPERATOR_RECOVERY"
RECONCILE_ABSENT_SAFE = "RECONCILED_ABSENT_SAFE_TO_RETRY"
RECONCILE_PUBLIC_OBJECT_CONTENT_INCOMPLETE = (
    "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
)

READBACK_UNAVAILABLE = "READBACK_UNAVAILABLE"

#: Safe lifecycle recovery is cheap but may still call a platform readback provider. Persisted
#: readback timestamps provide a restart-safe minimum cadence without another scheduler/table.
READBACK_RECONCILIATION_COOLDOWN_SECONDS = 60


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class CoreEditorialWindow:
    """One deterministic daily editorial decision window (UTC hours)."""

    start_hour_utc: int
    end_hour_utc: int
    session: str = "core_daily"
    eligible_weekdays_utc: tuple = (0, 1, 2, 3, 4)


@dataclass(frozen=True)
class EditorialWindowPolicy:
    """Versioned editorial-window policy. Bootstrap = deterministic configured defaults.

    These are NOT optimal or learned; they are safe configured defaults. Real learning may
    refine them later from observed qualified engagement, never from unmeasured assumptions.
    """

    policy_id: str
    policy_version: str
    effective_at_utc: str
    timezone_session: str
    core_windows: tuple
    destination_preferred_windows: tuple
    minimum_cycle_spacing_hours: float
    freshness_max_age_hours: float
    material_event_override_enabled: bool
    materiality_threshold: int
    confidence_state: str
    sample_state: str
    provenance: str
    daily_publication_target_band: tuple = (5, 8)
    routine_opportunity_limit: int = 4
    publication_minimum: int = 5
    build_qualified_floor: int = 4
    final_published_target_min: int = 5
    final_published_target_max: int = 8
    schedule_owner_locked: bool = True
    automatic_schedule_scaling_enabled: bool = False
    material_event_daily_saturation_limit: int = 4

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "effective_at_utc": self.effective_at_utc,
            "timezone_session": self.timezone_session,
            "core_windows": [asdict(window) for window in self.core_windows],
            "destination_preferred_windows": list(self.destination_preferred_windows),
            "minimum_cycle_spacing_hours": self.minimum_cycle_spacing_hours,
            "freshness_max_age_hours": self.freshness_max_age_hours,
            "material_event_override_enabled": self.material_event_override_enabled,
            "materiality_threshold": self.materiality_threshold,
            "confidence_state": self.confidence_state,
            "sample_state": self.sample_state,
            "provenance": self.provenance,
            "daily_publication_target_band": list(self.daily_publication_target_band),
            "routine_opportunity_limit": self.routine_opportunity_limit,
            "publication_minimum": self.publication_minimum,
            "build_qualified_floor": self.build_qualified_floor,
            "final_published_target_min": self.final_published_target_min,
            "final_published_target_max": self.final_published_target_max,
            "schedule_owner_locked": self.schedule_owner_locked,
            "automatic_schedule_scaling_enabled": self.automatic_schedule_scaling_enabled,
            "material_event_daily_saturation_limit": self.material_event_daily_saturation_limit,
        }


def build_bootstrap_editorial_window_policy(
    *, effective_at_utc: Optional[str] = None
) -> EditorialWindowPolicy:
    """Owner-locked daily-output policy: exactly four routine weekday opportunities.

    The UTC hours map to 17:00, 21:00, 23:00, and 01:00 Asia/Bangkok.  Because the 01:00
    Bangkok opportunity is 18:00 UTC on the prior day, all four rows are Monday-Friday in UTC.
    Learning may record timing recommendations but cannot mutate this schedule or add a fifth
    scheduled task. Material events may wake this same supervisor only in SHADOW/NO_PUBLIC_WRITE
    scope until a separate owner grant exists; autonomous mode retains them as durable priority
    metadata for the next routine opportunity.
    """
    return EditorialWindowPolicy(
        policy_id=WINDOW_POLICY_ID,
        policy_version=WINDOW_POLICY_VERSION,
        effective_at_utc=effective_at_utc or _iso_utc(datetime.now(timezone.utc)),
        timezone_session="utc",
        core_windows=(
            CoreEditorialWindow(start_hour_utc=10, end_hour_utc=11, session="london_1700_bangkok"),
            CoreEditorialWindow(start_hour_utc=14, end_hour_utc=15, session="new_york_2100_bangkok"),
            CoreEditorialWindow(start_hour_utc=16, end_hour_utc=17, session="new_york_2300_bangkok"),
            CoreEditorialWindow(start_hour_utc=18, end_hour_utc=19, session="new_york_0100_bangkok"),
        ),
        destination_preferred_windows=(),
        minimum_cycle_spacing_hours=1.0,
        freshness_max_age_hours=24.0,
        material_event_override_enabled=True,
        materiality_threshold=1,
        confidence_state="bootstrap_configured_defaults_not_learned",
        sample_state="insufficient_samples_no_learning_applied",
        provenance=(
            "owner_locked_autonomous_daily_output_four_routine_opportunities_build_floor_four_"
            "final_published_target_five_to_eight_no_filler_not_learned"
        ),
        daily_publication_target_band=(5, 8),
        routine_opportunity_limit=4,
        publication_minimum=5,
        build_qualified_floor=4,
        final_published_target_min=5,
        final_published_target_max=8,
        schedule_owner_locked=True,
        automatic_schedule_scaling_enabled=False,
        material_event_daily_saturation_limit=4,
    )


def editorial_window_id(
    *,
    policy_version: str,
    window_start_utc: datetime,
    window_end_utc: datetime,
    session: str,
    trigger_kind: str,
) -> str:
    """Deterministic identity for one editorial decision window."""
    identity = {
        "policy_version": policy_version,
        "window_start_utc": _iso_utc(window_start_utc),
        "window_end_utc": _iso_utc(window_end_utc),
        "session": session,
        "trigger_kind": trigger_kind,
    }
    return "editorial-window-" + _logical_hash(identity)[:32]


def owner_locked_editorial_opportunities(
    policy: EditorialWindowPolicy,
    *,
    reference_utc: datetime | str,
    through_utc: datetime | str,
    active_window_grace_hours: float = 1.0,
    capacity: int = 12,
) -> list[dict[str, Any]]:
    """Enumerate real scheduled opportunities available in a bounded UTC interval.

    The policy owns the Bangkok-equivalent calendar. This helper derives dates, weekdays, and
    sessions from that policy instead of assuming a fixed gap between opportunities. A currently
    due window remains available through the supervisor's existing one-hour grace.
    """
    reference = _parse_utc(reference_utc) if isinstance(reference_utc, str) else reference_utc
    through = _parse_utc(through_utc) if isinstance(through_utc, str) else through_utc
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if through.tzinfo is None:
        through = through.replace(tzinfo=timezone.utc)
    reference = reference.astimezone(timezone.utc)
    through = through.astimezone(timezone.utc)
    if through < reference:
        raise ValueError("editorial_opportunity_interval_invalid")
    if capacity < 1:
        raise ValueError("editorial_opportunity_capacity_invalid")
    grace = timedelta(hours=float(active_window_grace_hours))
    rows: list[dict[str, Any]] = []
    first_day = (reference - timedelta(days=1)).date()
    last_day = through.date()
    day_count = (last_day - first_day).days
    for day_offset in range(day_count + 1):
        day = first_day + timedelta(days=day_offset)
        base = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        for core in policy.core_windows:
            if base.weekday() not in set(core.eligible_weekdays_utc):
                continue
            start = base + timedelta(hours=core.start_hour_utc)
            end = base + timedelta(hours=core.end_hour_utc)
            if end + grace < reference or start > through:
                continue
            rows.append({
                "opportunity_id": editorial_window_id(
                    policy_version=policy.policy_version,
                    window_start_utc=start,
                    window_end_utc=end,
                    session=core.session,
                    trigger_kind=TRIGGER_SCHEDULED,
                ),
                "trigger": TRIGGER_SCHEDULED,
                "policy_id": policy.policy_id,
                "policy_version": policy.policy_version,
                "session": core.session,
                "start_utc": _iso_utc(start),
                "end_utc": _iso_utc(end),
                "capacity": int(capacity),
            })
    return sorted(rows, key=lambda row: (row["start_utc"], row["opportunity_id"]))


def material_event_due(
    materiality_metadata: Optional[Mapping[str, Any]],
    policy: EditorialWindowPolicy,
    now: datetime,
) -> Optional[dict[str, Any]]:
    """Deterministic material-event wakeup seam over governed discovery metadata.

    Returns a material-event signal when governed discovery/update metadata indicates a genuinely
    new material event meeting the configured threshold. This is discovery/input metadata only and
    grants NO evidence, factual, or publication authority; it merely asks whether an editorial
    cycle is warranted before the next scheduled window. The same evidence/review/publication
    gates apply to any cycle it triggers.
    """
    if not policy.material_event_override_enabled:
        return None
    if not isinstance(materiality_metadata, Mapping):
        return None
    if materiality_metadata.get("material_event_due") is not True:
        return None
    count = int(materiality_metadata.get("new_material_event_count") or 0)
    if count < max(1, int(policy.materiality_threshold)):
        return None
    identity_seed = str(
        materiality_metadata.get("new_material_event_identity")
        or materiality_metadata.get("material_event_identity")
        or _logical_hash(dict(materiality_metadata))
    )
    trigger_identity = "material-event-" + _logical_hash(
        {"identity": identity_seed, "policy_version": policy.policy_version}
    )[:32]
    return {
        "trigger_kind": TRIGGER_MATERIAL_EVENT,
        "trigger_identity": trigger_identity,
        "new_material_event_count": count,
        "headline_ids": sorted({
            str(value)
            for value in (materiality_metadata.get("new_headline_ids") or [])
            if str(value)
        }),
        "source_refs": sorted({
            str(value)
            for value in (materiality_metadata.get("new_headline_source_refs") or [])
            if str(value)
        }),
        "update_chain_identities": sorted({
            str(value)
            for value in (materiality_metadata.get("update_chain_identities") or [])
            if str(value)
        }),
        "evaluated_at_utc": _iso_utc(now),
        "grants_evidence_or_publication_authority": False,
    }


def material_event_window_id(
    *, policy_version: str, trigger_identity: str
) -> str:
    """Stable durable work identity for one material headline delta."""
    return "editorial-window-" + _logical_hash({
        "policy_version": policy_version,
        "trigger_kind": TRIGGER_MATERIAL_EVENT,
        "trigger_identity": trigger_identity,
    })[:32]


class ContentOpsDailyAppSupervisor:
    """One persistent coordinator that owns due-window execution and recovery."""

    def __init__(
        self,
        *,
        store_path: str | Path,
        output_root: str | Path,
        operating_mode: Optional[str] = None,
        clock: Optional[Callable[[], datetime]] = None,
        store: Any = None,
        newsroom_cycle: Optional[Callable[..., Mapping[str, Any]]] = None,
        policy: Optional[EditorialWindowPolicy] = None,
        owner_ref: Optional[str] = None,
        lease_ttl_seconds: int = 3600,
        sidecar_glob: Optional[str] = None,
        production_epoch_start_utc: Optional[str] = None,
        enable_publication_lifecycle: bool = False,
        publication_publisher: Optional[Callable[..., Mapping[str, Any]]] = None,
        publication_readback_provider: Optional[Callable[..., Mapping[str, Any]]] = None,
        publication_coordinator: Any = None,
        enable_performance_observation: bool = False,
        performance_collector: Optional[Callable[..., Mapping[str, Any]]] = None,
        interaction_classifier: Optional[Callable[..., Mapping[str, Any]]] = None,
        performance_learning_enabled: bool = False,
        intake_housekeeping: Optional[Callable[..., Mapping[str, Any]]] = None,
        scheduled_editorial_owner: str = SCHEDULED_EDITORIAL_OWNER_FDA_G,
    ) -> None:
        requested_mode = operating_mode or "AUTONOMOUS_DEFAULT"
        if requested_mode not in OPERATING_MODES:
            raise ValueError(f"daily_app_operating_mode_invalid:{operating_mode}")
        from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._store_path = Path(store_path)
        self._store = store or ContentOpsDurableStore(self._store_path)
        self._intake_housekeeping_override = intake_housekeeping
        self._configured_operating_mode = requested_mode
        self._operating_mode = requested_mode
        self._mode_drift_detected = False
        if hasattr(self._store, "get_operating_control"):
            control = self._store.get_operating_control()
            # An explicit first-start configuration may replace only the migration bootstrap
            # default. Once any real control source owns the row, durable state wins on restart.
            if (
                operating_mode is not None
                and control.get("control_source") == "SCHEMA_V7_INITIAL_PRODUCT_DEFAULT"
                and str(control.get("operating_mode")) != requested_mode
            ):
                control = self._store.update_operating_control(
                    expected_state_version=int(control["state_version"]),
                    operating_mode=requested_mode,
                    control_source="SUPERVISOR_STARTUP_CONFIG",
                )
            self._operating_mode = str(control["operating_mode"])
            self._mode_drift_detected = self._operating_mode != requested_mode
        self._production_epoch_start_utc = self._resolve_production_epoch(
            production_epoch_start_utc
        )
        # FDA-C: the supervisor DRIVES the canonical durable publication lifecycle
        # (outbox -> dispatch -> readback -> reconciliation) through the existing durable
        # store tables. It never creates a second publisher or store; the actual dispatch
        # boundary is the injected canonical publisher (fixture-bound under controlled runs).
        self._enable_publication_lifecycle = bool(enable_publication_lifecycle)
        self._publication_publisher = publication_publisher
        self._publication_readback_provider = publication_readback_provider
        self._publication_coordinator = publication_coordinator
        # FDA-D/FDA-E: bounded read-only performance observation + deterministic learning driven
        # from the cheap tick. ZERO LLM calls for metrics collection. No second scheduler/store.
        self._enable_performance_observation = bool(enable_performance_observation)
        self._performance_collector = performance_collector
        self._interaction_classifier = interaction_classifier
        self._performance_learning_enabled = bool(performance_learning_enabled)
        if newsroom_cycle is None:
            from live_contentops.eight_platform_substack_first_pipeline_v1 import (
                run_rolling_x_newsroom_cycle as canonical_cycle,
            )

            newsroom_cycle = canonical_cycle
        self._newsroom_cycle = newsroom_cycle
        self._policy = policy or build_bootstrap_editorial_window_policy()
        self._owner_ref = owner_ref or (
            f"daily-app-supervisor-{os.getpid()}-"
            f"{_logical_hash(str(store_path))[:8]}-{uuid4().hex[:8]}"
        )
        # One stable durable controller identity per canonical store.  A process restart
        # refreshes the same heartbeat row instead of manufacturing a second controller in
        # the read model, while the process-scoped owner_ref continues to fence active work.
        self._heartbeat_worker_id = (
            "contentops-daily-app-supervisor-"
            + _logical_hash(str(self._store_path.resolve()))[:16]
        )
        self._output_root = Path(output_root)
        self._lease_ttl_seconds = int(lease_ttl_seconds)
        self._sidecar_glob = sidecar_glob
        owner = str(scheduled_editorial_owner or "").strip().upper()
        if owner not in SCHEDULED_EDITORIAL_OWNERS:
            raise ValueError(f"scheduled_editorial_owner_invalid:{scheduled_editorial_owner}")
        self._scheduled_editorial_owner = owner

    # -- public API -----------------------------------------------------------

    @property
    def policy(self) -> EditorialWindowPolicy:
        return self._policy

    @property
    def operating_mode(self) -> str:
        return self._operating_mode

    def execute_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Compatibility public seam: execute PREPARE and finish unless a HIGH worker is required."""
        return self.prepare_native_desktop_scheduled_opportunity(
            automation_id=automation_id,
            now=now,
        )

    def _resolve_native_desktop_due_window(
        self, *, automation_id: str, now: Optional[datetime]
    ) -> tuple[str, str, datetime, Optional[dict[str, Any]]]:
        if self._scheduled_editorial_owner != SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP:
            raise ValueError("native_desktop_scheduled_owner_not_configured")
        task_id = str(automation_id or "").strip()
        session = NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID.get(task_id)
        if session is None:
            raise ValueError("native_desktop_automation_id_invalid")
        moment = now or self._clock()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        moment = moment.astimezone(timezone.utc)
        matches = [
            row
            for row in self._currently_due_scheduled_windows(moment)
            if str(row.get("session") or "") == session
        ]
        if not matches:
            return task_id, session, moment, None
        if len(matches) != 1:
            raise RuntimeError("native_desktop_scheduled_opportunity_identity_ambiguous")
        return task_id, session, moment, {
            **matches[0],
            "native_desktop_automation_id": task_id,
            "native_desktop_zero_public_write": True,
        }

    @staticmethod
    def _native_desktop_zero_write_result(
        *,
        task_id: str,
        session: str,
        moment: datetime,
        window: Mapping[str, Any],
        outcome: Mapping[str, Any],
    ) -> dict[str, Any]:
        from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id

        opportunity_id = str(window["window_id"])
        observed_public_write = outcome.get("public_write_performed") is True
        observed_unknown_write = outcome.get("unknown_write_detected") is True
        result = {
            "schema_version": "contentops.native_desktop_scheduled_opportunity.v1",
            "automation_id": task_id,
            "session": session,
            "execution_owner": SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
            "scheduled_at_utc": _iso_utc(window["start"]),
            "actual_start_utc": _iso_utc(moment),
            "newsroom_production_day_id": newsroom_production_day_id(window["start"]),
            "canonical_opportunity_id": opportunity_id,
            "runtime_run_id": opportunity_id,
            "sdk_fallback_identity_compatible": True,
            **dict(outcome),
            "public_write_authority": "ZERO",
            "public_write_performed": observed_public_write,
            "unknown_write_detected": observed_unknown_write,
        }
        if observed_public_write:
            result.update(
                {
                    "classification": "BLOCKED",
                    "exact_next_blocker": "NATIVE_DESKTOP_ZERO_WRITE_CONTRACT_VIOLATION",
                    "retry_authorized": False,
                }
            )
        if observed_unknown_write:
            result.update(
                {
                    "classification": "BLOCKED",
                    "exact_next_blocker": "UNKNOWN_WRITE",
                    "unknown_write_rule": "STOP_RETRY_READ_BACK_RECONCILE",
                    "retry_authorized": False,
                }
            )
        return result

    def prepare_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Claim one exact opportunity and pause durably if a fresh HIGH worker is warranted."""
        task_id, session, moment, window = self._resolve_native_desktop_due_window(
            automation_id=automation_id,
            now=now,
        )
        if window is None:
            return {
                "schema_version": "contentops.native_desktop_scheduled_opportunity.v1",
                "automation_id": task_id,
                "session": session,
                "execution_owner": SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
                "executed": False,
                "reason": "scheduled_opportunity_not_due",
                "public_write_authority": "ZERO",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
        outcome = self._execute_window(
            window,
            moment,
            split_phase_operation="PREPARE",
        )
        return self._native_desktop_zero_write_result(
            task_id=task_id,
            session=session,
            moment=moment,
            window=window,
            outcome=outcome,
        )

    def complete_native_desktop_scheduled_opportunity(
        self,
        *,
        automation_id: str,
        canonical_opportunity_id: str,
        worker_return: Mapping[str, Any],
        coordinator_review_receipt: Mapping[str, Any],
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Resume the same claimed opportunity with one exact hash-bound worker return."""
        if self._scheduled_editorial_owner != SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP:
            raise ValueError("native_desktop_scheduled_owner_not_configured")
        task_id = str(automation_id or "").strip()
        session = NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID.get(task_id)
        if session is None:
            raise ValueError("native_desktop_automation_id_invalid")
        opportunity_id = str(canonical_opportunity_id or "").strip()
        window = self._load_editorial_opportunity_checkpoint(opportunity_id)
        if window is None:
            raise ValueError("native_desktop_opportunity_checkpoint_missing_or_invalid")
        if str(window.get("session") or "") != session:
            raise ValueError("native_desktop_opportunity_session_mismatch")
        moment = now or self._clock()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        moment = moment.astimezone(timezone.utc)
        window = {
            **window,
            "native_desktop_automation_id": task_id,
            "native_desktop_zero_public_write": True,
        }
        outcome = self._execute_window(
            window,
            moment,
            split_phase_operation="COMPLETE",
            split_phase_worker_return=worker_return,
            split_phase_coordinator_review=coordinator_review_receipt,
        )
        return self._native_desktop_zero_write_result(
            task_id=task_id,
            session=session,
            moment=moment,
            window=window,
            outcome=outcome,
        )

    def _load_source_route_health_state(self) -> dict[str, Any]:
        path = self._output_root / SOURCE_ROUTE_HEALTH_STATE_NAME
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError):
            return {}
        if (
            not isinstance(value, Mapping)
            or value.get("schema_version") != "contentops.source_route_health.v1"
            or value.get("routing_only") is not True
        ):
            return {}
        return dict(value)

    def _persist_source_route_health_state(self, result: Mapping[str, Any]) -> dict[str, Any]:
        value = result.get("source_route_health")
        if not isinstance(value, Mapping) or value.get("schema_version") != (
            "contentops.source_route_health.v1"
        ):
            return {}
        snapshot = dict(value)
        if (
            snapshot.get("routing_only") is not True
            or snapshot.get("sourceability_or_health_grants_factual_authority") is not False
            or snapshot.get("sourceability_or_health_grants_publication_authority") is not False
        ):
            raise ValueError("source_route_health_authority_contract_invalid")
        self._output_root.mkdir(parents=True, exist_ok=True)
        path = self._output_root / SOURCE_ROUTE_HEALTH_STATE_NAME
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return snapshot

    def _refresh_operating_mode(self) -> str:
        """Reload durable mode so UI/restart changes cannot be silently ignored."""
        if not hasattr(self._store, "get_operating_control"):
            return self._operating_mode
        try:
            control = self._store.get_operating_control()
            self._operating_mode = str(control["operating_mode"])
            self._mode_drift_detected = (
                self._operating_mode != self._configured_operating_mode
            )
        except Exception:
            # Missing/corrupt control state fails closed for every new public write while
            # leaving reconciliation/readback recovery available.
            self._operating_mode = "KILL_SWITCH"
            self._mode_drift_detected = True
        return self._operating_mode

    @property
    def store_path(self) -> str:
        """The explicit durable-store path this supervisor is bound to."""
        return str(getattr(self._store, "db_path", self._store_path))

    @property
    def production_epoch_start_utc(self) -> Optional[str]:
        if self._production_epoch_start_utc is None:
            return None
        return _iso_utc(self._production_epoch_start_utc)

    # -- production epoch -----------------------------------------------------

    def _resolve_production_epoch(
        self, configured: Optional[str]
    ) -> Optional[datetime]:
        """Resolve the production epoch start with WRITE-ONCE semantics.

        A. persisted epoch ABSENT + configured provided  -> initialize exactly once.
        B. persisted epoch PRESENT + no configured value -> load the exact persisted epoch.
        C. persisted epoch PRESENT + configured EQUAL    -> idempotent PASS; no rewrite.
        D. persisted epoch PRESENT + configured DIFFERS  -> raise
           ``ProductionEpochConflictError``; NEVER overwrite.

        The persisted production epoch is write-once runtime authority for the historical-replay
        boundary. It is never made mutable through CLI restart flags or configuration drift.
        """
        persisted = self._load_production_epoch()
        if not configured:
            return persisted
        epoch = _parse_utc(configured)
        if persisted is None:
            self._record_production_epoch(epoch)
            return epoch
        if persisted == epoch:
            # Idempotent re-supply of the exact persisted epoch; nothing is rewritten.
            return persisted
        raise ProductionEpochConflictError(persisted=persisted, configured=epoch)

    def _load_production_epoch(self) -> Optional[datetime]:
        try:
            with self._store.get_connection() as conn:
                row = conn.execute(
                    "SELECT metric_value FROM metrics WHERE metric_id=?",
                    (PRODUCTION_EPOCH_METRIC_ID,),
                ).fetchone()
        except Exception:  # noqa: BLE001 - epoch lookup is best-effort housekeeping
            return None
        if row is None:
            return None
        return datetime.fromtimestamp(float(row["metric_value"]), tz=timezone.utc)

    def _record_production_epoch(self, epoch: datetime) -> None:
        """Persist the production epoch exactly once (write-once; never a replace)."""
        existing = self._load_production_epoch()
        if existing is not None:
            if existing == epoch:
                return
            raise ProductionEpochConflictError(persisted=existing, configured=epoch)
        conn = self._store.get_connection()
        try:
            conn.execute(
                "INSERT INTO metrics (metric_id, metric_name, metric_value, recorded_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    PRODUCTION_EPOCH_METRIC_ID,
                    PRODUCTION_EPOCH_METRIC_NAME,
                    epoch.timestamp(),
                    _iso_utc(self._clock()),
                ),
            )
        finally:
            conn.close()

    def _within_production_epoch(self, window_start: datetime) -> bool:
        """A scheduled window that started before the production epoch is never backfilled."""
        if self._production_epoch_start_utc is None:
            return True
        return window_start >= self._production_epoch_start_utc

    # -- FDA-C canonical publication lifecycle --------------------------------
    #
    # The supervisor drives ONE canonical durable publication chain per ready destination:
    #   outbox -> dispatch -> readback -> reconciliation
    # persisted through the EXISTING durable-store tables. Identities are deterministic so a
    # restart or duplicate execution never creates duplicate durable rows. New dispatch is
    # blocked under KILL_SWITCH; safe readback/reconciliation/recovery remain allowed. An
    # UNKNOWN_WRITE stops retry and requires read-back + reconcile before any further action.
    #
    # HARD GATES (write-once external truth):
    # * A missing/failed readback provider is NOT a successful readback; it fails closed and can
    #   never synthesise ``verified: true`` or RECONCILED_CONFIRMED.
    # * Only an explicit positive readback whose dispatch/destination/public-object identities
    #   EXACTLY match the dispatched object reconciles to RECONCILED_CONFIRMED.
    # * Controlled no-write fixtures are recorded as CONTROLLED_NO_PUBLIC_WRITE and are never
    #   classified as a real public publication.

    def _lifecycle_identity(
        self, window_id: str, destination: str, package_identity: str
    ) -> Dict[str, str]:
        """Deterministic durable identities for one destination's canonical lifecycle chain."""
        basis = json.dumps(
            {
                "window_id": window_id,
                "destination": destination,
                "package_identity": package_identity,
            },
            sort_keys=True,
        )
        h = _logical_hash(basis)
        return {
            "basis": basis,
            "message_id": "outbox_" + h[:32],
            "dispatch_id": "dispatch_" + h[:32],
            "reconciliation_id": "reconciliation_" + h[:32],
        }

    def _verify_readback_confirmation(
        self,
        *,
        readback_result: Any,
        dispatch_id: str,
        destination: str,
        public_object_id: Optional[str],
    ) -> tuple[bool, str]:
        """Strict canonical readback verification (fail-closed).

        Returns ``(confirmed, reason)``. Only an explicit positive confirmation whose dispatch,
        destination, and public-object identities exactly match the dispatched object confirms.
        Every missing/empty/exception/ambiguous/mismatch case fails closed.
        """
        if readback_result is None:
            return False, "readback_unavailable_or_error"
        if not isinstance(readback_result, Mapping):
            return False, "readback_not_mapping"
        if not readback_result:
            return False, "readback_empty"
        if readback_result.get("verified") is not True:
            return False, "readback_verified_not_true"
        if str(readback_result.get("dispatch_id") or "") != dispatch_id:
            return False, "readback_dispatch_identity_mismatch"
        if str(readback_result.get("destination") or "") != destination:
            return False, "readback_destination_mismatch"
        expected_obj = str(public_object_id or "")
        observed_obj = str(readback_result.get("public_object_id") or "")
        if expected_obj and observed_obj != expected_obj:
            return False, "readback_public_object_identity_mismatch"
        return True, "readback_confirmed"

    def drive_canonical_publication_lifecycle(
        self,
        window_id: str,
        ready_destinations: Sequence[str],
        package_identity: str,
        *,
        publisher: Optional[Callable[[str, str], Mapping[str, Any]]] = None,
        readback_provider: Optional[Callable[[str, str], Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Persist the canonical dispatch lifecycle for every exact READY destination.

        ``publisher`` is the canonical dispatch boundary. Under controlled runs it is
        fixture-bound and performs ZERO public writes. When ``publisher`` is ``None`` no dispatch
        is attempted and the destination is recorded as CONTROLLED_NO_PUBLIC_WRITE. When
        ``readback_provider`` is ``None`` a confirmed external write is never synthesised as
        reconciled; it fails closed to RECONCILIATION_PENDING_READBACK.
        """
        publisher = publisher or self._publication_publisher
        readback_provider = readback_provider or self._publication_readback_provider
        outcome: Dict[str, Any] = {
            "window_id": window_id,
            "package_identity": package_identity,
            "ready_destinations": list(ready_destinations),
            "kill_switch_blocked": False,
            "outbox_messages": 0,
            "dispatches": 0,
            "confirmed_writes": 0,
            "readbacks": 0,
            "reconciliations": 0,
            "unknown_write_detected": False,
            "public_write_performed": False,
            "per_destination": {},
        }
        if self._refresh_operating_mode() == "KILL_SWITCH":
            # Kill switch blocks NEW dispatch; the durable chain itself stays intact so existing
            # readback/reconciliation/recovery can proceed.
            outcome["kill_switch_blocked"] = True
            return outcome
        for destination in sorted(set(str(d) for d in ready_destinations)):
            destination = str(destination)
            ids = self._lifecycle_identity(window_id, destination, package_identity)
            basis = ids["basis"]
            message_id = ids["message_id"]
            dispatch_id = ids["dispatch_id"]
            reconciliation_id = ids["reconciliation_id"]
            # Durable outbox identity (idempotent: same identity never duplicates on restart).
            self._store.register_outbox_message(
                message_id=message_id,
                work_item_id=window_id,
                destination=destination,
                payload=basis,
                status="READY",
            )
            outcome["outbox_messages"] += 1

            # -- Dispatch classification ---------------------------------------
            # Preserve the exact public-object identity the publisher reports; a controlled
            # no-write fixture is recorded distinctly and never as a real public publication.
            public_object_id: Optional[str] = None
            public_object_url: Optional[str] = None
            dispatch_status = STATUS_CONTROLLED_NO_WRITE
            current_mode = self._refresh_operating_mode()
            publisher_allowed = current_mode == "AUTONOMOUS_DEFAULT"
            if callable(publisher) and publisher_allowed:
                try:
                    published = dict(publisher(destination, package_identity))
                    raw_status = str(published.get("status") or "")
                    public_object_id = str(published.get("public_object_id") or "") or None
                    public_object_url = str(published.get("public_object_url") or "") or None
                except Exception as exc:  # noqa: BLE001 - classify, never blind-retry
                    raw_status = STATUS_UNKNOWN_WRITE
                    public_object_id = None
                    public_object_url = None
                    self._store.register_incident(
                        incident_id="incident_" + _logical_hash(basis + str(exc))[:32],
                        work_item_id=window_id,
                        severity="UNKNOWN_WRITE",
                        description=(
                            f"Dispatch boundary error for {destination}: {type(exc).__name__}"
                        ),
                    )
                if raw_status == STATUS_DISPATCH_CONFIRMED:
                    # A confirmed external write without a public-object identity cannot be
                    # verified/read-back; fail closed to unknown-write.
                    dispatch_status = (
                        STATUS_DISPATCH_CONFIRMED if public_object_id else STATUS_UNKNOWN_WRITE
                    )
                elif raw_status in ("DISPATCH_CONFIRMED_NO_WRITE", STATUS_CONTROLLED_NO_WRITE):
                    dispatch_status = STATUS_CONTROLLED_NO_WRITE
                    public_object_id = None
                    public_object_url = None
                else:
                    # Unknown/ambiguous/error outcome -> STOP RETRY -> READ BACK -> RECONCILE.
                    dispatch_status = STATUS_UNKNOWN_WRITE

            # Persist the exact external public-object identity into canonical durable state as
            # part of dispatch registration (write-once; conflict fails closed).
            self._store.register_platform_dispatch(
                dispatch_id=dispatch_id,
                message_id=message_id,
                platform=destination,
                status=dispatch_status,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
            )
            outcome["dispatches"] += 1
            row: Dict[str, Any] = {
                "destination": destination,
                "message_id": message_id,
                "dispatch_id": dispatch_id,
                "status": dispatch_status,
                "public_object_id": public_object_id,
                "public_object_url": public_object_url,
                "readback_id": None,
                "reconciliation_id": reconciliation_id,
            }

            if dispatch_status == STATUS_UNKNOWN_WRITE:
                # STOP RETRY -> READ BACK -> RECONCILE. No blind retry is permitted.
                outcome["unknown_write_detected"] = True
                self._store.register_reconciliation(
                    reconciliation_id=reconciliation_id,
                    work_item_id=window_id,
                    status=RECONCILE_PENDING_OPERATOR,
                )
                outcome["reconciliations"] += 1
                row["reconciliation_status"] = RECONCILE_PENDING_OPERATOR
                outcome["per_destination"][destination] = row
                continue

            if dispatch_status == STATUS_CONTROLLED_NO_WRITE:
                # Controlled / no public write: no external object exists. Record a distinct
                # controlled terminal state; never a real-publication confirmation (no
                # confirmed_writes, no public_write_performed).
                readback_data = json.dumps(
                    {
                        "dispatch_id": dispatch_id,
                        "destination": destination,
                        "readback_status": STATUS_CONTROLLED_NO_WRITE,
                        "verified": False,
                        "public_write_performed": False,
                    },
                    sort_keys=True,
                )
                readback_id = "readback_" + _logical_hash(readback_data)[:32]
                self._store.register_readback(
                    readback_id=readback_id, dispatch_id=dispatch_id, readback_data=readback_data
                )
                outcome["readbacks"] += 1
                row["readback_id"] = readback_id
                self._store.register_reconciliation(
                    reconciliation_id=reconciliation_id,
                    work_item_id=window_id,
                    status=RECONCILE_CONTROLLED_NO_WRITE,
                )
                outcome["reconciliations"] += 1
                row["reconciliation_status"] = RECONCILE_CONTROLLED_NO_WRITE
                outcome["per_destination"][destination] = row
                continue

            # -- Real external write confirmed by publisher --------------------
            outcome["confirmed_writes"] += 1
            outcome["public_write_performed"] = True

            if not callable(readback_provider):
                # Missing readback provider is NOT a successful readback; fail closed. No
                # verified:true, no RECONCILED_CONFIRMED.
                readback_data = json.dumps(
                    {
                        "dispatch_id": dispatch_id,
                        "destination": destination,
                        "readback_status": READBACK_UNAVAILABLE,
                        "verified": False,
                    },
                    sort_keys=True,
                )
                readback_id = "readback_" + _logical_hash(readback_data)[:32]
                self._store.register_readback(
                    readback_id=readback_id, dispatch_id=dispatch_id, readback_data=readback_data
                )
                outcome["readbacks"] += 1
                row["readback_id"] = readback_id
                self._store.register_reconciliation(
                    reconciliation_id=reconciliation_id,
                    work_item_id=window_id,
                    status=RECONCILE_PENDING_READBACK,
                )
                outcome["reconciliations"] += 1
                row["reconciliation_status"] = RECONCILE_PENDING_READBACK
                outcome["per_destination"][destination] = row
                continue

            try:
                # PHASE 7: the readback must be resolved against the identity loaded FROM the
                # durable dispatch state, never against an unpersisted local variable.
                stored_dispatch = self._store.get_platform_dispatch(dispatch_id) or {}
                durable_object_id = str(stored_dispatch.get("public_object_id") or "") or None
                try:
                    rb = dict(readback_provider(dispatch_id, destination, durable_object_id))
                except Exception as exc:  # noqa: BLE001 - provider failure must fail closed
                    rb = {"_readback_error": type(exc).__name__}
                confirmed, reason = self._verify_readback_confirmation(
                    readback_result=rb,
                    dispatch_id=dispatch_id,
                    destination=destination,
                    public_object_id=durable_object_id,
                )
            except Exception as exc:  # noqa: BLE001 - durable lookup failure fails closed
                rb = {"_readback_error": type(exc).__name__}
                confirmed, reason = False, "durable_identity_unavailable"
            readback_data = json.dumps(
                {
                    "observed": rb if isinstance(rb, Mapping) else {},
                    "dispatch_id": dispatch_id,
                    "destination": destination,
                    "verified": bool(confirmed),
                    "verification_reason": reason,
                },
                sort_keys=True,
                default=str,
            )
            readback_id = "readback_" + _logical_hash(readback_data)[:32]
            self._store.register_readback(
                readback_id=readback_id, dispatch_id=dispatch_id, readback_data=readback_data
            )
            outcome["readbacks"] += 1
            row["readback_id"] = readback_id
            recon = RECONCILE_CONFIRMED if confirmed else RECONCILE_PENDING_READBACK
            self._store.register_reconciliation(
                reconciliation_id=reconciliation_id,
                work_item_id=window_id,
                status=recon,
            )
            outcome["reconciliations"] += 1
            row["reconciliation_status"] = recon
            outcome["per_destination"][destination] = row
        return outcome

    def perform_safe_readback_and_reconciliation(
        self,
        window_id: str,
        *,
        readback_provider: Optional[Callable[..., Mapping[str, Any]]] = None,
        attempted_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """READBACK/RECONCILIATION ONLY recovery, safe even under KILL_SWITCH.

        Covers BOTH durable recovery cases after a restart:
          A. UNKNOWN_WRITE  -> STOP RETRY -> READ BACK -> RECONCILE;
          B. DISPATCH_CONFIRMED with RECONCILIATION_PENDING_READBACK -> read back the exact
             persisted public-object identity and reconcile.

        For each case this method NEVER redispatches (zero publisher calls). It resolves the
        exact destination/message/dispatch/public identity FROM DURABLE STATE, calls the
        canonical configured readback provider (if available) with that durable identity,
        persists the readback observation, and reconciles:

        * readback proves a public object exists with a matching identity -> RECONCILED_CONFIRMED;
        * readback proves no write occurred -> RECONCILED_ABSENT_SAFE_TO_RETRY (no automatic retry);
        * ambiguous/unavailable/error/missing durable identity -> remains fail-closed pending.

        The publisher is never invoked here.
        """
        provider = readback_provider or self._publication_readback_provider
        attempted_at_utc = _iso_utc(attempted_at or self._clock())
        summary: Dict[str, Any] = {
            "window_id": window_id,
            "dispatches": 0,
            "unknown_writes": 0,
            "pending_readbacks": 0,
            "publisher_calls": 0,  # this method NEVER invokes the publisher
            "readback_calls": 0,
            "reconciled": 0,
            "still_pending": 0,
            "per_dispatch": {},
        }
        dispatches = self._store.get_dispatches_for_work_item(window_id)
        summary["dispatches"] = len(dispatches)
        # Current reconciliation states keyed by deterministic reconciliation identity.
        recons_by_id = {
            r["reconciliation_id"]: r["status"]
            for r in self._store.get_reconciliations_for_work_item(window_id)
        }
        for dispatch in dispatches:
            status = str(dispatch["status"])
            if status not in (STATUS_UNKNOWN_WRITE, STATUS_DISPATCH_CONFIRMED):
                continue
            if status == STATUS_UNKNOWN_WRITE:
                summary["unknown_writes"] += 1
            else:
                summary["pending_readbacks"] += 1
            dispatch_id = str(dispatch["dispatch_id"])
            destination = str(dispatch["platform"])
            durable_object_id = str(dispatch.get("public_object_id") or "") or None
            # Resolve exact package identity from the durable outbox payload.
            package_identity = ""
            message = self._store.get_outbox_message(str(dispatch["message_id"]))
            if message:
                try:
                    package_identity = str(json.loads(message["payload"]).get("package_identity") or "")
                except Exception:  # noqa: BLE001 - unreadable payload stays fail-closed
                    package_identity = ""
            ids = self._lifecycle_identity(window_id, destination, package_identity)
            reconciliation_id = ids["reconciliation_id"]
            current = recons_by_id.get(reconciliation_id)
            # Already-recovered dispatches are idempotent; do not re-invoke the provider.
            if current in (RECONCILE_CONFIRMED, RECONCILE_ABSENT_SAFE, RECONCILE_CONTROLLED_NO_WRITE):
                summary["per_dispatch"][dispatch_id] = current
                continue
            # Only recover dispatches in the expected pending states.
            if status == STATUS_DISPATCH_CONFIRMED and current != RECONCILE_PENDING_READBACK:
                continue
            if status == STATUS_UNKNOWN_WRITE and current != RECONCILE_PENDING_OPERATOR:
                continue
            pending_state = (
                RECONCILE_PENDING_READBACK if status == STATUS_DISPATCH_CONFIRMED
                else RECONCILE_PENDING_OPERATOR
            )
            # A confirmed dispatch with no persisted external identity cannot be read back
            # without guessing; fail closed. Identity alone never upgrades UNKNOWN_WRITE.
            if status == STATUS_DISPATCH_CONFIRMED and not durable_object_id:
                readback_data = json.dumps(
                    {
                        "dispatch_id": dispatch_id,
                        "destination": destination,
                        "readback_status": "DURABLE_PUBLIC_OBJECT_ID_UNAVAILABLE",
                        "verified": False,
                        "recovery": True,
                        "attempted_at_utc": attempted_at_utc,
                    },
                    sort_keys=True,
                )
                self._store.register_readback(
                    readback_id="readback_" + _logical_hash(readback_data)[:32],
                    dispatch_id=dispatch_id,
                    readback_data=readback_data,
                )
                summary["still_pending"] += 1
                summary["per_dispatch"][dispatch_id] = pending_state
                continue
            if not callable(provider):
                # No readback provider -> cannot read back; remain fail-closed pending.
                readback_data = json.dumps(
                    {
                        "dispatch_id": dispatch_id,
                        "destination": destination,
                        "readback_status": READBACK_UNAVAILABLE,
                        "verified": False,
                        "recovery": True,
                        "attempted_at_utc": attempted_at_utc,
                    },
                    sort_keys=True,
                )
                self._store.register_readback(
                    readback_id="readback_" + _logical_hash(readback_data)[:32],
                    dispatch_id=dispatch_id,
                    readback_data=readback_data,
                )
                summary["still_pending"] += 1
                summary["per_dispatch"][dispatch_id] = pending_state
                continue
            summary["readback_calls"] += 1
            try:
                rb = dict(provider(dispatch_id, destination, durable_object_id))
            except Exception as exc:  # noqa: BLE001 - provider error fails closed, no retry
                rb = {"_readback_error": type(exc).__name__}
            readback_data = json.dumps(
                {
                    "observed": rb if isinstance(rb, Mapping) else {},
                    "dispatch_id": dispatch_id,
                    "destination": destination,
                    "recovery": True,
                    "attempted_at_utc": attempted_at_utc,
                },
                sort_keys=True,
                default=str,
            )
            self._store.register_readback(
                readback_id="readback_" + _logical_hash(readback_data)[:32],
                dispatch_id=dispatch_id,
                readback_data=readback_data,
            )
            if status == STATUS_DISPATCH_CONFIRMED:
                confirmed, _reason = self._verify_readback_confirmation(
                    readback_result=rb,
                    dispatch_id=dispatch_id,
                    destination=destination,
                    public_object_id=durable_object_id,
                )
                if confirmed:
                    self._store.set_reconciliation_status(reconciliation_id, RECONCILE_CONFIRMED)
                    summary["reconciled"] += 1
                    summary["per_dispatch"][dispatch_id] = RECONCILE_CONFIRMED
                else:
                    summary["still_pending"] += 1
                    summary["per_dispatch"][dispatch_id] = RECONCILE_PENDING_READBACK
                continue
            # UNKNOWN_WRITE: readback must still establish truth; identity alone never confirms.
            if (
                not isinstance(rb, Mapping)
                or not rb
                or rb.get("verified") is not True
                or str(rb.get("dispatch_id") or "") != dispatch_id
                or str(rb.get("destination") or "") != destination
            ):
                # Ambiguous/malformed/mismatched/unverified observation stays pending operator.
                summary["still_pending"] += 1
                summary["per_dispatch"][dispatch_id] = RECONCILE_PENDING_OPERATOR
                continue
            observed_object = str(rb.get("public_object_id") or "")
            write_occurred = rb.get("write_occurred")
            if durable_object_id is not None and observed_object:
                if observed_object == durable_object_id:
                    # Readback matched the exact preserved identity -> confirmed.
                    self._store.set_reconciliation_status(
                        reconciliation_id, RECONCILE_CONFIRMED
                    )
                    summary["reconciled"] += 1
                    summary["per_dispatch"][dispatch_id] = RECONCILE_CONFIRMED
                else:
                    # A contradictory object identity can never be converted to absent-safe.
                    summary["still_pending"] += 1
                    summary["per_dispatch"][dispatch_id] = RECONCILE_PENDING_OPERATOR
            elif durable_object_id is None and observed_object:
                # No preserved identity but readback proved a concrete public object exists.
                self._store.set_reconciliation_status(reconciliation_id, RECONCILE_CONFIRMED)
                summary["reconciled"] += 1
                summary["per_dispatch"][dispatch_id] = RECONCILE_CONFIRMED
            elif write_occurred is False:
                # Readback proved no write occurred -> absent-safe; no automatic retry here.
                self._store.set_reconciliation_status(reconciliation_id, RECONCILE_ABSENT_SAFE)
                summary["reconciled"] += 1
                summary["per_dispatch"][dispatch_id] = RECONCILE_ABSENT_SAFE
            else:
                summary["still_pending"] += 1
                summary["per_dispatch"][dispatch_id] = RECONCILE_PENDING_OPERATOR
        return summary

    def _pending_readback_reconciliation_candidates(self) -> list[Dict[str, str]]:
        """Discover exact pending lifecycle recovery from the bound durable store only."""
        candidates: list[Dict[str, str]] = []
        for dispatch in self._store.list_platform_dispatches():
            status = str(dispatch.get("status") or "")
            if status not in (STATUS_UNKNOWN_WRITE, STATUS_DISPATCH_CONFIRMED):
                continue
            message = self._store.get_outbox_message(str(dispatch.get("message_id") or ""))
            if not message:
                continue
            window_id = str(message.get("work_item_id") or "")
            if not window_id:
                continue
            try:
                package_identity = str(
                    json.loads(str(message.get("payload") or "{}")).get("package_identity") or ""
                )
            except Exception:  # noqa: BLE001 - unreadable identity remains fail-closed
                package_identity = ""
            reconciliation_id = self._lifecycle_identity(
                window_id, str(dispatch.get("platform") or ""), package_identity
            )["reconciliation_id"]
            reconciliation_status = next(
                (
                    str(row.get("status") or "")
                    for row in self._store.get_reconciliations_for_work_item(window_id)
                    if str(row.get("reconciliation_id") or "") == reconciliation_id
                ),
                "",
            )
            expected = (
                RECONCILE_PENDING_OPERATOR
                if status == STATUS_UNKNOWN_WRITE
                else RECONCILE_PENDING_READBACK
            )
            if reconciliation_status != expected:
                continue
            candidates.append(
                {
                    "window_id": window_id,
                    "dispatch_id": str(dispatch.get("dispatch_id") or ""),
                    "dispatch_status": status,
                    "reconciliation_status": reconciliation_status,
                }
            )
        return sorted(candidates, key=lambda row: (row["window_id"], row["dispatch_id"]))

    def _latest_recovery_attempt_at(self, dispatch_id: str) -> Optional[datetime]:
        """Return the latest durable readback/attempt time for cooldown calculation."""
        latest: Optional[datetime] = None
        with self._store.get_connection() as conn:
            rows = conn.execute(
                "SELECT readback_data, read_at FROM readbacks WHERE dispatch_id=?"
                " ORDER BY read_at, readback_id",
                (dispatch_id,),
            ).fetchall()
        for row in rows:
            values = [row["read_at"]]
            try:
                payload = json.loads(str(row["readback_data"] or "{}"))
                values.append(payload.get("attempted_at_utc"))
            except Exception:  # noqa: BLE001 - malformed historical row is not timing authority
                pass
            for value in values:
                if not value:
                    continue
                try:
                    parsed = _parse_utc(str(value))
                except Exception:  # noqa: BLE001
                    continue
                if latest is None or parsed > latest:
                    latest = parsed
        return latest

    def _recovery_window_eligible_at(
        self, candidates: Sequence[Mapping[str, str]], now: datetime
    ) -> datetime:
        """One deduplicated window becomes eligible after its latest pending readback attempt."""
        attempts = [
            attempted
            for candidate in candidates
            if (attempted := self._latest_recovery_attempt_at(candidate["dispatch_id"]))
            is not None
        ]
        if not attempts:
            return now
        return max(attempts) + timedelta(seconds=READBACK_RECONCILIATION_COOLDOWN_SECONDS)

    def _next_recovery_wake(self, now: datetime) -> Optional[datetime]:
        candidates = self._pending_readback_reconciliation_candidates()
        if not candidates:
            return None
        by_window: Dict[str, list[Dict[str, str]]] = {}
        for candidate in candidates:
            by_window.setdefault(candidate["window_id"], []).append(candidate)
        return min(
            self._recovery_window_eligible_at(window_candidates, now)
            for window_candidates in by_window.values()
        )

    def _run_readback_reconciliation_housekeeping(self, now: datetime) -> Dict[str, Any]:
        """Run bounded durable READBACK/RECONCILIATION ONLY recovery for this tick."""
        candidates = self._pending_readback_reconciliation_candidates()
        summary: Dict[str, Any] = {
            "state": "NO_PENDING_RECOVERY",
            "candidate_dispatches": len(candidates),
            "candidate_windows": 0,
            "readback_calls": 0,
            "publisher_calls": 0,
            "reconciled": 0,
            "still_pending": 0,
            "cooldown_deferred": 0,
            "next_eligible_at_utc": None,
        }
        if not candidates:
            return summary
        by_window: Dict[str, list[Dict[str, str]]] = {}
        for candidate in candidates:
            by_window.setdefault(candidate["window_id"], []).append(candidate)
        summary["candidate_windows"] = len(by_window)
        attempted = 0
        for window_id in sorted(by_window):
            window_candidates = by_window[window_id]
            eligible_at = self._recovery_window_eligible_at(window_candidates, now)
            if eligible_at > now:
                summary["cooldown_deferred"] += len(window_candidates)
                continue
            attempted += 1
            recovered = self.perform_safe_readback_and_reconciliation(
                window_id, attempted_at=now
            )
            summary["readback_calls"] += int(recovered.get("readback_calls") or 0)
            summary["publisher_calls"] += int(recovered.get("publisher_calls") or 0)
            summary["reconciled"] += int(recovered.get("reconciled") or 0)
            summary["still_pending"] += int(recovered.get("still_pending") or 0)
        pending_after = self._pending_readback_reconciliation_candidates()
        summary["still_pending"] = len(pending_after)
        if pending_after:
            next_wake = self._next_recovery_wake(now)
            summary["next_eligible_at_utc"] = _iso_utc(next_wake) if next_wake else None
        if attempted:
            summary["state"] = (
                "RUN_STILL_PENDING" if pending_after else "RUN_RECONCILED"
            )
        else:
            summary["state"] = "COOLDOWN_NOT_DUE"
            summary["still_pending"] = len(pending_after)
        return summary

    # -- FDA-D/FDA-E performance observation + bounded learning -----------------

    def _reconciliation_status_for_dispatch(self, dispatch: Mapping[str, Any]) -> Optional[str]:
        message = self._store.get_outbox_message(str(dispatch["message_id"]))
        if not message:
            return None
        reconciliations = self._store.get_reconciliations_for_work_item(
            str(message["work_item_id"])
        )
        # The canonical DurablePublicationCoordinator uses one shared deterministic suffix for
        # outbox, dispatch, and reconciliation identities. Follow that exact durable lineage
        # first; reconstructing the older supervisor-local lifecycle basis incorrectly marked
        # real coordinator publications learning-ineligible.
        exact_reconciliation_id = (
            "reconciliation_" + str(dispatch["dispatch_id"]).removeprefix("dispatch_")
        )
        for row in reconciliations:
            if str(row["reconciliation_id"]) == exact_reconciliation_id:
                return str(row["status"])
        try:
            package_identity = str(json.loads(message["payload"]).get("package_identity") or "")
        except Exception:  # noqa: BLE001 - unreadable payload stays fail-closed
            package_identity = ""
        ids = self._lifecycle_identity(
            str(message["work_item_id"]), str(dispatch["platform"]), package_identity
        )
        reconciliation_id = ids["reconciliation_id"]
        for row in reconciliations:
            if row["reconciliation_id"] == reconciliation_id:
                return row["status"]
        return None

    def _next_observation_wake(self, now: datetime) -> Optional[datetime]:
        if not self._enable_performance_observation:
            return None
        next_scheduled: Optional[datetime] = None
        for obs in self._store.list_performance_observations(collection_status="SCHEDULED"):
            try:
                scheduled = _parse_utc(str(obs["scheduled_for_utc"]))
            except Exception:  # noqa: BLE001
                continue
            if scheduled > now and (next_scheduled is None or scheduled < next_scheduled):
                next_scheduled = scheduled
        return next_scheduled

    def _run_performance_observations(self, now: datetime) -> Dict[str, Any]:
        """Cheap, bounded, READ-ONLY performance-observation step (ZERO LLM calls).

        1. Schedules future observation windows for every learning-eligible confirmed dispatch.
        2. Collects due observations through the injected read-only collector.
        3. Optionally evaluates a bounded, deterministic learning decision.
        Never writes to platforms; never schedules a second store or daemon.
        """
        from live_contentops import daily_app_performance_v1 as perf

        summary: Dict[str, Any] = {"scheduled": 0, "collected": 0, "learning": None}
        if not self._enable_performance_observation:
            return summary
        # Ensure the CONFIGURED_DEFAULT bootstrap policy exists (idempotent).
        perf.ensure_bootstrap_policy(self._store, now=now)

        # 1. Schedule observation windows for eligible confirmed dispatches.
        for dispatch in self._store.list_platform_dispatches():
            if dispatch["status"] != perf.DISPATCH_CONFIRMED or not dispatch.get("public_object_id"):
                continue
            existing = self._store.list_performance_observations(dispatch_id=dispatch["dispatch_id"])
            if existing:
                continue  # already scheduled for this dispatch (idempotent)
            reconciliation_status = self._reconciliation_status_for_dispatch(dispatch)
            readback_count = len(
                self._store.list_readbacks_for_dispatch(str(dispatch["dispatch_id"]))
            )
            eligibility = perf.assess_learning_eligibility(
                dispatch_status=dispatch["status"],
                public_object_id=dispatch.get("public_object_id"),
                reconciliation_status=reconciliation_status,
                readback_count=readback_count,
            )
            try:
                dispatched_at = _parse_utc(str(dispatch["dispatched_at"]))
            except Exception:  # noqa: BLE001
                continue
            outbox_message = self._store.get_outbox_message(str(dispatch["message_id"]))
            work_item_id = str((outbox_message or {}).get("work_item_id") or "")
            rows = perf.build_scheduled_observations(
                dispatch=dispatch,
                work_item_id=work_item_id,
                dispatched_at=dispatched_at,
                learning_eligible=bool(eligibility["learning_eligible"]),
            )
            for observation in rows:
                self._store.register_performance_observation(observation=observation)
                summary["scheduled"] += 1

        # 2. Collect due observations (read-only; zero LLM).
        for obs in self._store.list_performance_observations(collection_status="SCHEDULED"):
            try:
                scheduled = _parse_utc(str(obs["scheduled_for_utc"]))
            except Exception:  # noqa: BLE001
                continue
            if scheduled > now:
                continue
            perf.collect_observation(
                self._store, observation_id=obs["observation_id"],
                collector=self._performance_collector,
                interaction_classifier=self._interaction_classifier,
                now=now,
            )
            summary["collected"] += 1

        # 3. Bounded deterministic learning decision (no LLM).
        if self._performance_learning_enabled:
            summary["learning"] = perf.evaluate_learning_decision(
                self._store, evaluation_window=f"supervisor_tick:{_iso_utc(now)}", now=now
            )
        return summary

    def run_desktop_opportunity_housekeeping(
        self, *, now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Run the complete cheap pre-editorial loop for one native Desktop opportunity.

        This deliberately does not execute a newsroom cycle. It recovers exact prior write
        state, drains every safe READY derivative through the sole coordinator, collects due
        read-only observations, evaluates bounded learning, and returns the active policy for
        the fresh HIGH coordinator. UNKNOWN_WRITE is still readback-only and never blindly retried.
        """
        moment = (now or self._clock()).astimezone(timezone.utc)
        self._refresh_operating_mode()
        recovery: Dict[str, Any]
        if self._publication_coordinator is not None:
            recovery = dict(self._publication_coordinator.recover_pending())
        else:
            recovery = self._run_readback_reconciliation_housekeeping(moment)
        performance = self._run_performance_observations(moment)
        from live_contentops.daily_app_performance_v1 import active_policy_briefing

        policy = active_policy_briefing(self._store)
        return {
            "schema_version": "contentops.desktop_opportunity_housekeeping.v1",
            "run_at_utc": _iso_utc(moment),
            "recovery": recovery,
            "performance": performance,
            "active_learning_policy": policy,
            "newsroom_cycle_invocations": 0,
            "schedule_owner_locked": True,
            "routine_opportunity_limit": 4,
            "public_comment_writes": 0,
            "unknown_write_rule": "STOP_RETRY_READ_BACK_RECONCILE",
        }

    def _maybe_drive_publication_lifecycle(
        self, window_id: str, result: Mapping[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Drive the canonical lifecycle only when publication is enabled and the cycle result
        carries an explicit, governed lifecycle plan (exact READY destinations + package identity).
        Absent a plan, no publication lifecycle runs — publication is never manufactured.
        """
        if not self._enable_publication_lifecycle:
            return None
        self._refresh_operating_mode()
        plan = result.get("publication_lifecycle_plan") if isinstance(result, Mapping) else None
        if not isinstance(plan, Mapping):
            return None
        if self._publication_coordinator is not None:
            return dict(self._publication_coordinator.publish_plan(window_id, plan))
        ready = [str(d) for d in (plan.get("ready_destinations") or []) if str(d).strip()]
        package_identity = str(plan.get("package_identity") or "")
        if not ready or not package_identity:
            return None
        publisher = plan.get("publisher")
        readback_provider = plan.get("readback_provider")
        return self.drive_canonical_publication_lifecycle(
            window_id,
            ready,
            package_identity,
            publisher=publisher if callable(publisher) else self._publication_publisher,
            readback_provider=(
                readback_provider
                if callable(readback_provider)
                else self._publication_readback_provider
            ),
        )

    def _run_continuous_intake_housekeeping(self, now: datetime) -> dict[str, Any]:
        """Continuous cheap X headline intake lane (zero LLM calls). Headline ingestion is not
        owned by editorial windows or Run Now; it stays current while the host is available.
        Disabled via CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE=1 (controlled test isolation)."""
        if os.environ.get("CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE") == "1" and self._intake_housekeeping_override is None:
            return {"lane_state": "DISABLED_FOR_CONTROLLED_TEST", "detail": "intake_lane_disabled_by_env", "llm_or_provider_calls": 0}
        if self._intake_housekeeping_override is not None:
            try:
                return dict(self._intake_housekeeping_override(self._store, now=now))
            except Exception as exc:  # noqa: BLE001 - intake lane is best-effort, never fatal
                return {"lane_state": "DEGRADED", "detail": f"INTAKE_LANE_ERROR:{type(exc).__name__}", "llm_or_provider_calls": 0}
        if self._refresh_operating_mode() == "KILL_SWITCH":
            # KILL_SWITCH is an operator-requested quiet posture. Local read-model refreshes
            # and required lifecycle readback/reconciliation continue elsewhere, but the
            # default intake lane must not navigate/reload X in the background. One bounded
            # proof can still be invoked explicitly through the ingestion seam.
            return {
                "lane_state": "PAUSED_KILL_SWITCH",
                "detail": "NETWORK_INTAKE_PAUSED_BY_OPERATOR_KILL_SWITCH",
                "capture_attempted": False,
                "llm_or_provider_calls": 0,
                "public_write_performed": False,
            }
        try:
            from live_contentops.continuous_headline_ingest_v1 import (
                run_ingestion_housekeeping_iteration,
            )

            result = dict(run_ingestion_housekeeping_iteration(self._store, now=now))
            result["prepared_candidate_state"] = self._refresh_prepared_candidate_checkpoint(now)
            return result
        except Exception as exc:  # noqa: BLE001 - intake lane is best-effort, never fatal
            return {"lane_state": "DEGRADED", "detail": f"INTAKE_LANE_ERROR:{type(exc).__name__}", "llm_or_provider_calls": 0}

    @property
    def _prepared_candidate_checkpoint_path(self) -> Path:
        return self._output_root / "_continuous_newsroom" / PREPARED_CANDIDATE_CHECKPOINT_NAME

    def _refresh_prepared_candidate_checkpoint(self, now: datetime) -> dict[str, Any]:
        """Refresh the existing continuous lane's small zero-model publication candidate set."""
        try:
            from live_contentops.newsroom_assignment_scheduler_v1 import (
                DEFAULT_X_SIDECAR_GLOB,
                PREPARED_CANDIDATE_LIMIT,
                build_prepared_rolling_x_candidate_state,
                load_rolling_x_headline_sidecars,
            )
            from live_contentops.codex_desktop_newsroom_operator_v1 import (
                load_terminal_editorial_continuity,
                prepared_candidate_continuity_binding,
            )

            rolling_input = load_rolling_x_headline_sidecars(
                cutoff_utc=now,
                sidecar_glob=self._sidecar_glob or DEFAULT_X_SIDECAR_GLOB,
                window_hours=24.0,
            )
            continuity = load_terminal_editorial_continuity(
                store_path=self._store_path,
                output_root=self._output_root,
            )
            priority = continuity.get("material_event_priority") or {}
            evaluated_ids = list(continuity.get("evaluated_headline_ids") or [])
            reentry_ids = list(priority.get("headline_ids") or [])
            prior_state: Mapping[str, Any] | None = None
            checkpoint_path = self._prepared_candidate_checkpoint_path
            if checkpoint_path.exists():
                try:
                    loaded_prior = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                    if isinstance(loaded_prior, Mapping):
                        prior_state = loaded_prior
                except (OSError, TypeError, ValueError):
                    prior_state = None
            opportunities = owner_locked_editorial_opportunities(
                self._policy,
                reference_utc=now,
                through_utc=now + timedelta(
                    hours=float(rolling_input.get("window_hours") or 24.0)
                ),
                capacity=PREPARED_CANDIDATE_LIMIT,
            )
            opportunities = [
                row for row in opportunities
                if self._window_state(str(row["opportunity_id"]))
                not in WINDOW_EXECUTED_STATES
            ]
            state = build_prepared_rolling_x_candidate_state(
                rolling_input=rolling_input,
                prepared_at_utc=now,
                evaluated_headline_ids=evaluated_ids,
                reentry_headline_ids=reentry_ids,
                editorial_opportunities=opportunities,
                prior_prepared_state=prior_state,
                autonomous_source_discovery_available=True,
                source_route_health=self._load_source_route_health_state(),
                continuity_binding=prepared_candidate_continuity_binding(
                    continuity=continuity,
                    evaluated_headline_ids=evaluated_ids,
                    reentry_headline_ids=reentry_ids,
                ),
            )
            path = checkpoint_path
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = path.with_suffix(path.suffix + ".tmp")
            temporary_path.write_text(
                json.dumps(state, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(path)
            return {
                "status": "READY",
                "checkpoint_updated": True,
                "prepared_at_utc": state.get("prepared_at_utc"),
                "full_rolling_headline_count": state.get("full_rolling_headline_count"),
                "prepared_candidate_count": state.get("prepared_candidate_count"),
                "deferred_candidate_count": int(
                    (state.get("prepared_frontier") or {}).get(
                        "deferred_identity_count"
                    )
                    or 0
                ),
                "continuity_terminal_cutoff_utc": (
                    state.get("continuity_binding") or {}
                ).get("last_terminal_cutoff_utc"),
                "prepared_candidate_logical_hash": state.get(
                    "prepared_candidate_logical_hash"
                ),
                "llm_or_provider_calls": 0,
            }
        except Exception as exc:  # noqa: BLE001 - preparation is best-effort and zero-write
            return {
                "status": "DEGRADED",
                "checkpoint_updated": False,
                "detail": f"PREPARED_CANDIDATE_REFRESH_ERROR:{type(exc).__name__}",
                "llm_or_provider_calls": 0,
            }

    def _load_prepared_candidate_checkpoint(
        self, cutoff: datetime
    ) -> Optional[dict[str, Any]]:
        path = self._prepared_candidate_checkpoint_path
        if not path.exists():
            return None
        try:
            from live_contentops.newsroom_assignment_scheduler_v1 import (
                validate_prepared_rolling_x_candidate_state,
            )

            value = json.loads(path.read_text(encoding="utf-8"))
            return validate_prepared_rolling_x_candidate_state(
                value,
                publication_cutoff_utc=cutoff,
            )
        except Exception:  # noqa: BLE001 - invalid/stale preparation grants no authority
            return None

    def _run_operator_trigger_intake_sync(self, now: datetime) -> dict[str, Any]:
        """Run Now fallback freshness sync: one bounded intake iteration ONLY when the
        continuous lane is stale. The canonical cycle then consumes the full rolling universe."""
        try:
            from live_contentops.continuous_headline_ingest_v1 import (
                intake_is_stale,
                run_ingestion_housekeeping_iteration,
            )

            if not intake_is_stale(self._store, now=now):
                result = {"lane_state": "FRESH", "detail": "intake_fresh_no_sync_needed", "llm_or_provider_calls": 0}
            else:
                result = dict(run_ingestion_housekeeping_iteration(self._store, now=now, force=True))
            result["prepared_candidate_state"] = self._refresh_prepared_candidate_checkpoint(now)
            return result
        except Exception as exc:  # noqa: BLE001 - sync is best-effort, never blocks the decision
            return {"lane_state": "DEGRADED", "detail": f"INTAKE_SYNC_ERROR:{type(exc).__name__}", "llm_or_provider_calls": 0}

    @staticmethod
    def _capture_detail_suffix(capture_summary: Optional[Mapping[str, Any]]) -> str:
        if not capture_summary:
            return ""
        state = str(capture_summary.get("lane_state") or capture_summary.get("capture_state") or "UNKNOWN")
        new_rows = int(capture_summary.get("rows_added") or capture_summary.get("new_headlines") or 0)
        return f":INTAKE.{state}:new{new_rows}"

    def _consume_pending_operator_trigger(self, now: datetime) -> Optional[dict[str, Any]]:
        """Consume at most one durable OPERATOR_REQUESTED trigger through the SAME canonical
        cycle boundary as scheduled windows. Restart-safe: the trigger row stays PENDING until
        consumption, so a pending request survives restart exactly once. An already-executing
        canonical cycle (active EVIDENCE_PENDING lease) defers consumption; no parallel cycle.
        """
        fetch = getattr(self._store, "fetch_pending_operator_trigger", None)
        if fetch is None:
            return None
        trigger = fetch()
        if not trigger:
            return None
        trigger_id = str(trigger["trigger_id"])
        active_windows = []
        try:
            active_windows = list(self._store.active_editorial_cycle_window_ids())
        except Exception:  # noqa: BLE001 - fail closed on durable-state read error
            return {"trigger_id": trigger_id, "state": "DEFERRED_STORE_UNAVAILABLE", "executed": False}
        if active_windows:
            return {
                "trigger_id": trigger_id,
                "state": "DEFERRED_CYCLE_ALREADY_ACTIVE",
                "executed": False,
                "active_window_id": active_windows[0],
            }
        start = _parse_utc(trigger["requested_at_utc"])
        window = {
            "window_id": f"operator-requested-{trigger_id}",
            "trigger": TRIGGER_OPERATOR_REQUESTED,
            "start": start,
            # Run Now is evaluated at the actual execution point, never at a synthetic
            # requested-at-plus-one-hour future cutoff.
            "end": now,
            "session": "operator_requested",
        }
        capture_summary = self._run_operator_trigger_intake_sync(now)
        outcome = self._execute_window(window, now)
        reason = str(outcome.get("reason") or "")
        capture_suffix = self._capture_detail_suffix(capture_summary)
        if outcome.get("executed"):
            self._store.consume_operator_cycle_trigger(
                trigger_id,
                window_id=window["window_id"],
                detail=f"EXECUTED:{str(outcome.get('classification') or 'NO_CLASSIFICATION')}{capture_suffix}",
            )
            return {
                "trigger_id": trigger_id,
                "state": "CONSUMED",
                "executed": True,
                "classification": outcome.get("classification"),
                "viable": bool(outcome.get("viable")),
                "public_write_performed": bool(outcome.get("public_write_performed")),
                "unknown_write_detected": bool(outcome.get("unknown_write_detected")),
                "terminal_state": outcome.get("terminal_state"),
                "window_id": window["window_id"],
                "ingestion_capture": capture_summary,
            }
        if reason in {"active_window_owned_elsewhere", "lease_conflict_another_owner"}:
            return {
                "trigger_id": trigger_id,
                "state": "DEFERRED_ACTIVE_WINDOW_OWNED_ELSEWHERE",
                "executed": False,
                "ingestion_capture": capture_summary,
            }
        self._store.consume_operator_cycle_trigger(
            trigger_id,
            window_id=window["window_id"],
            detail=f"NOT_EXECUTED:{reason or 'terminal_state_present'}{capture_suffix}",
        )
        return {
            "trigger_id": trigger_id,
            "state": "CONSUMED",
            "executed": False,
            "reason": reason or "terminal_state_present",
            "window_id": window["window_id"],
            "ingestion_capture": capture_summary,
        }

    def tick(
        self,
        now: Optional[datetime] = None,
        materiality_metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """One cheap supervisor tick. No LLM/provider work unless a window is executed."""
        now = now or self._clock()
        self._refresh_operating_mode()
        heartbeat = self._store.upsert_heartbeat(self._heartbeat_worker_id)
        report: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "operating_mode": self._operating_mode,
            "configured_operating_mode": self._configured_operating_mode,
            "mode_drift_detected": self._mode_drift_detected,
            "kill_switch_active": self._operating_mode == "KILL_SWITCH",
            "policy_version": self._policy.policy_version,
            "tick_at_utc": _iso_utc(now),
            "heartbeat_worker_id": self._heartbeat_worker_id,
            "heartbeat_at_utc": heartbeat["last_seen_at"],
            "windows_due": 0,
            "windows_dispatched": 0,
            "windows_skipped": [],
            "stale_pending_recovered": 0,
            "stale_pending_resumed": 0,
            "stale_pending_recovery_deferred": 0,
            "newsroom_cycle_invocations": 0,
            "provider_calls": 0,
            "public_write_performed": False,
            "unknown_write_detected": False,
            "readback_reconciliation_state": "NO_PENDING_RECOVERY",
            "recovery_candidates": 0,
            "recovery_candidate_windows": 0,
            "recovery_readback_calls": 0,
            "recovery_publisher_calls": 0,
            "recovery_reconciled": 0,
            "recovery_still_pending": 0,
            "recovery_cooldown_deferred": 0,
            "next_recovery_wake_utc": None,
            "performance_observation_state": NOT_IMPLEMENTED_NOT_DUE,
            "learning_evaluation_state": NOT_IMPLEMENTED_NOT_DUE,
            "headline_ingestion": None,
        }
        # Continuous cheap X headline intake lane: housekeeping, zero LLM calls, independent of
        # editorial windows and Run Now. Runs under every operating mode (ingestion is not a
        # public write); the locked CapitalChronicleBot binding is reused and never replaced.
        report["headline_ingestion"] = self._run_continuous_intake_housekeeping(now)
        effective_materiality = (
            materiality_metadata
            if isinstance(materiality_metadata, Mapping)
            else report["headline_ingestion"]
        )
        signal = material_event_due(effective_materiality, self._policy, now)
        if signal is not None:
            report["material_event_wake"] = self._stage_material_event(signal, now)
            staged_window_id = str(
                (report.get("material_event_wake") or {}).get("window_id") or ""
            )
            if (
                staged_window_id
                and (report.get("material_event_wake") or {}).get("state")
                == "DISCOVERED"
            ):
                report["material_event_wake"]["wake_eligibility"] = (
                    self._material_event_wake_eligibility(
                        {
                            "window_id": staged_window_id,
                            "trigger": TRIGGER_MATERIAL_EVENT,
                        },
                        now,
                    )
                )

        # Cheap durable-state housekeeping (no provider calls).
        try:
            self._store.recover_stale_leases()
        except Exception:  # noqa: BLE001 - recovery is best-effort housekeeping
            report["windows_skipped"].append("stale_lease_recovery_unavailable")
        try:
            for stale_window_id in self._store.stale_editorial_cycle_window_ids():
                resumable_window = self._load_editorial_opportunity_checkpoint(stale_window_id)
                if resumable_window is not None:
                    resumed = self._execute_window(resumable_window, now)
                    if resumed.get("executed"):
                        report["stale_pending_resumed"] += 1
                    elif resumed.get("reason") in {
                        "active_window_owned_elsewhere",
                        "lease_conflict_another_owner",
                    }:
                        report["stale_pending_recovery_deferred"] += 1
                else:
                    # Legacy pending rows predate resumable opportunity checkpoints. They keep
                    # the previous fail-closed terminal recovery behavior.
                    recovery = self._recover_stale_pending(stale_window_id)
                    if recovery == "recovered":
                        report["stale_pending_recovered"] += 1
                    elif recovery == "active_owner":
                        report["stale_pending_recovery_deferred"] += 1
        except Exception:  # noqa: BLE001 - remain alive and fail closed on recovery error
            report["windows_skipped"].append("stale_pending_window_recovery_unavailable")

        # Existing durable public-object state is lifecycle housekeeping, not publication
        # authority. Run it before performance eligibility so a newly reconciled exact object can
        # receive its observation schedule on this same tick under every operating mode.
        try:
            if self._publication_coordinator is not None:
                coordinator_recovery = dict(self._publication_coordinator.recover_pending())
                recovery = {
                    "state": "COORDINATOR_RECOVERY_RUN",
                    "candidate_dispatches": int(coordinator_recovery.get("marked_unknown", 0))
                    + int(coordinator_recovery.get("readbacks", 0)),
                    "candidate_windows": 0,
                    "readback_calls": int(coordinator_recovery.get("readbacks", 0)),
                    "publisher_calls": int(coordinator_recovery.get("publish_calls", 0)),
                    "reconciled": 0,
                    "still_pending": int(coordinator_recovery.get("marked_unknown", 0)),
                    "cooldown_deferred": 0,
                    "next_eligible_at_utc": None,
                }
            else:
                recovery = self._run_readback_reconciliation_housekeeping(now)
            report.update(
                {
                    "readback_reconciliation_state": recovery["state"],
                    "recovery_candidates": recovery["candidate_dispatches"],
                    "recovery_candidate_windows": recovery["candidate_windows"],
                    "recovery_readback_calls": recovery["readback_calls"],
                    "recovery_publisher_calls": recovery["publisher_calls"],
                    "recovery_reconciled": recovery["reconciled"],
                    "recovery_still_pending": recovery["still_pending"],
                    "recovery_cooldown_deferred": recovery["cooldown_deferred"],
                    "next_recovery_wake_utc": recovery["next_eligible_at_utc"],
                }
            )
        except Exception:  # noqa: BLE001 - remain alive and fail closed on durable recovery error
            report["readback_reconciliation_state"] = "RECOVERY_UNAVAILABLE"
            report["windows_skipped"].append("readback_reconciliation_recovery_unavailable")

        # FDA-D/FDA-E: due READ-ONLY performance observations + bounded learning run under EVERY
        # operating mode, including KILL_SWITCH. Metrics collection performs zero LLM calls and
        # zero public writes. KILL_SWITCH blocks NEW public dispatch, not read-only observation,
        # readback, reconciliation, or safe recovery.
        if self._enable_performance_observation:
            perf_summary = self._run_performance_observations(now)
            report["performance_observations"] = {
                "scheduled": perf_summary["scheduled"],
                "collected": perf_summary["collected"],
            }
            report["performance_observation_state"] = "RUN"
            if perf_summary.get("learning") is not None:
                report["learning_evaluation_state"] = "RUN"
                report["learning_decision"] = {
                    "decision": perf_summary["learning"].get("decision"),
                    "policy_version": perf_summary["learning"].get("policy_version"),
                    "reason": perf_summary["learning"].get("reason"),
                }

        if report["kill_switch_active"]:
            # Kill switch blocks NEW public dispatch (no publisher call, no weakened gates).
            # Readback, reconciliation, performance observation, and safe recovery all continue.
            # Existing product policy also defers operator-requested cycles while KILL_SWITCH is
            # active; the durable PENDING trigger is preserved untouched for later consumption.
            report["next_wake_utc"] = _iso_utc(self._next_wake(now))
            return report

        operator_report = self._consume_pending_operator_trigger(now)
        dispatched = 0
        if operator_report is not None:
            report["operator_trigger"] = operator_report
            if operator_report.get("executed"):
                dispatched += 1
                report["newsroom_cycle_invocations"] += 1
                report["public_write_performed"] = report["public_write_performed"] or bool(
                    operator_report.get("public_write_performed")
                )
                report["unknown_write_detected"] = report["unknown_write_detected"] or bool(
                    operator_report.get("unknown_write_detected")
                )

        due_windows = self._due_windows(now, effective_materiality)
        report["windows_due"] = len(due_windows)
        for window in due_windows:
            # Execute at most one due editorial window per tick.
            if dispatched >= 1:
                report["windows_skipped"].append(window["window_id"] + ":one_window_per_tick")
                continue
            outcome = self._execute_window(window, now)
            if outcome.get("executed"):
                dispatched += 1
                report["newsroom_cycle_invocations"] += 1
                report["public_write_performed"] = report["public_write_performed"] or bool(
                    outcome.get("public_write_performed")
                )
                report["unknown_write_detected"] = report["unknown_write_detected"] or bool(
                    outcome.get("unknown_write_detected")
                )
            else:
                report["windows_skipped"].append(
                    window["window_id"] + ":" + str(outcome.get("reason"))
                )
        report["windows_dispatched"] = dispatched
        report["next_wake_utc"] = _iso_utc(self._next_wake(now))
        return report

    def run_forever(
        self, *, poll_seconds: float = 60.0, max_ticks: Optional[int] = None
    ) -> int:
        """Long-running loop used by the product entrypoint. Cheap when idle."""
        ticks = 0
        transient_failures = 0
        while True:
            try:
                report = self.tick()
                transient_failures = 0
            except Exception as exc:  # bounded unattended resilience; writes fail closed per tick
                transient_failures += 1
                incident_basis = f"daily_app_tick:{type(exc).__name__}:{transient_failures}"
                try:
                    self._store.register_incident(
                        incident_id="incident_" + _logical_hash(incident_basis)[:32],
                        work_item_id=None,
                        severity="TRANSIENT_DEGRADED",
                        description=f"Daily App tick failed safely: {type(exc).__name__}",
                    )
                except Exception:
                    # If even safe incident persistence fails, a durable-store fault is fatal.
                    raise
                report = {
                    "next_wake_utc": _iso_utc(
                        self._clock() + timedelta(seconds=min(300.0, max(1.0, poll_seconds) * (2 ** min(transient_failures, 5))))
                    )
                }
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                return ticks
            try:
                next_wake = _parse_utc(report["next_wake_utc"])
            except ValueError:
                next_wake = self._clock() + timedelta(seconds=poll_seconds)
            wait = min(
                float(poll_seconds),
                max(0.0, (next_wake - self._clock()).total_seconds()),
            )
            time.sleep(wait)

    # -- window scheduling ----------------------------------------------------

    def _window_for_day(
        self, core: CoreEditorialWindow, day: datetime
    ) -> tuple[datetime, datetime]:
        base = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        start = base + timedelta(hours=core.start_hour_utc)
        end = base + timedelta(hours=core.end_hour_utc)
        return start, end

    def _timing_policy_offset_minutes(self) -> int:
        """Bounded timing offset (minutes) from the latest ACTIVE learning policy.

        Fails closed to 0 (configured bootstrap offset) when no valid accepted policy exists or
        the payload is malformed, so learned timing can never silently corrupt bootstrap config.
        """
        try:
            from live_contentops.daily_app_performance_v1 import (
                active_policy_timing_offset_minutes,
            )
            return active_policy_timing_offset_minutes(self._store, fallback=0)
        except Exception:  # noqa: BLE001 - missing/broken policy must not alter bootstrap timing
            return 0

    def _active_learning_policy_briefing(self) -> dict[str, Any]:
        """Bounded preference-only context for preselection and the fresh editorial brain."""
        try:
            from live_contentops.daily_app_performance_v1 import active_policy_briefing

            return active_policy_briefing(self._store)
        except Exception:  # noqa: BLE001 - learning context is never truth authority
            return {
                "policy_version": "policy.bootstrap.v1",
                "sample_count": 0,
                "confidence": 0.0,
                "timing": {"owner_locked": True, "routine_opportunity_count": 4},
                "content": {},
                "seo": {},
                "package": {},
                "grants_factual_or_numeric_authority": False,
                "grants_publication_authority": False,
            }

    def _stage_material_event(
        self, signal: Mapping[str, Any], now: datetime
    ) -> dict[str, Any]:
        """Persist a restart-safe material wake as a canonical DISCOVERED work item."""
        window_id = material_event_window_id(
            policy_version=self._policy.policy_version,
            trigger_identity=str(signal["trigger_identity"]),
        )
        existing = self._matching_material_event_opportunity(signal, now)
        if existing is not None:
            return {
                "state": str(existing.get("state") or "DISCOVERED"),
                "window_id": str(existing["window_id"]),
                "trigger_identity": signal.get("trigger_identity"),
                "new_material_event_count": signal.get("new_material_event_count"),
                "staged_at_utc": _iso_utc(now),
                "durable_idempotency": True,
                "duplicate_update_chain_suppressed": True,
                "grants_evidence_or_publication_authority": False,
                "public_write_scope_granted": False,
            }
        item = self._store.create_work_item(
            story_id=window_id,
            title=f"Daily App material event {window_id}",
            target_surface="daily_app_material_event_window",
            work_item_id=window_id,
            actor_ref="ContentOpsContinuousHeadlineIntake",
            correlation_id=f"corr_{window_id}",
        )
        priority_path = self._output_root / window_id / "material_event_priority_v1.json"
        priority_path.parent.mkdir(parents=True, exist_ok=True)
        if priority_path.exists():
            try:
                priority = json.loads(priority_path.read_text(encoding="utf-8"))
            except (OSError, TypeError, ValueError):
                priority = {}
        else:
            priority = {
                "schema_version": "contentops.material_event_priority.v1",
                "priority_id": window_id,
                "trigger_identity": signal.get("trigger_identity"),
                "headline_ids": list(signal.get("headline_ids") or []),
                "source_refs": list(signal.get("source_refs") or []),
                "update_chain_identities": list(
                    signal.get("update_chain_identities") or []
                ),
                "new_material_event_count": int(
                    signal.get("new_material_event_count") or 0
                ),
                "created_at_utc": _iso_utc(now),
                "expires_at_utc": _iso_utc(
                    now + timedelta(hours=self._policy.freshness_max_age_hours)
                ),
                "consumption_state": (
                    "PENDING_SHADOW_WAKE"
                    if self._operating_mode == "SHADOW_ONLY"
                    else "PENDING_NEXT_SCHEDULED_OPPORTUNITY"
                ),
                "wake_execution_scope": "SHADOW_NO_PUBLIC_WRITE",
                "grants_evidence_or_publication_authority": False,
                "changes_candidate_eligibility_gates": False,
            }
            priority["priority_logical_hash"] = _logical_hash(priority)
            temporary_path = priority_path.with_suffix(priority_path.suffix + ".tmp")
            temporary_path.write_text(
                json.dumps(priority, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            temporary_path.replace(priority_path)
        return {
            "state": str(item.get("current_state") or "DISCOVERED"),
            "window_id": window_id,
            "trigger_identity": signal.get("trigger_identity"),
            "new_material_event_count": signal.get("new_material_event_count"),
            "staged_at_utc": _iso_utc(now),
            "durable_idempotency": True,
            "priority_artifact": str(priority_path),
            "headline_ids": list(priority.get("headline_ids") or []),
            "grants_evidence_or_publication_authority": False,
            "public_write_scope_granted": False,
            "wake_execution_scope": "SHADOW_NO_PUBLIC_WRITE",
        }

    def _matching_material_event_opportunity(
        self, signal: Mapping[str, Any], now: datetime
    ) -> Optional[dict[str, Any]]:
        """Return a freshness-safe matching durable material opportunity, if any."""
        try:
            with self._store.get_read_only_connection() as conn:
                rows = conn.execute(
                    "SELECT work_item_id,current_state FROM work_items"
                    " WHERE target_surface='daily_app_material_event_window'"
                    " ORDER BY created_at,work_item_id"
                ).fetchall()
        except Exception:  # noqa: BLE001 - failure simply falls back to stable ID idempotency
            return None
        incoming_headlines = {
            str(value) for value in (signal.get("headline_ids") or []) if str(value)
        }
        incoming_chains = {
            str(value)
            for value in (signal.get("update_chain_identities") or [])
            if str(value)
        }
        for row in rows:
            opportunity_id = str(row["work_item_id"])
            path = self._output_root / opportunity_id / "material_event_priority_v1.json"
            try:
                priority = json.loads(path.read_text(encoding="utf-8"))
                expires = _parse_utc(str(priority.get("expires_at_utc") or ""))
            except (OSError, TypeError, ValueError):
                continue
            if expires <= now:
                continue
            exact_trigger = str(priority.get("trigger_identity") or "") == str(
                signal.get("trigger_identity") or ""
            )
            headline_overlap = bool(
                incoming_headlines.intersection(
                    str(value) for value in (priority.get("headline_ids") or [])
                )
            )
            chain_overlap = bool(
                incoming_chains.intersection(
                    str(value)
                    for value in (priority.get("update_chain_identities") or [])
                )
            )
            if exact_trigger or headline_overlap or chain_overlap:
                return {
                    "window_id": opportunity_id,
                    "state": str(row["current_state"]),
                }
        return None

    def _completed_editorial_opportunity_times(
        self,
        now: datetime,
        *,
        target_surface: Optional[str] = None,
    ) -> list[datetime]:
        """Load terminal canonical opportunity times from hash-bound checkpoints."""
        try:
            with self._store.get_read_only_connection() as conn:
                rows = conn.execute(
                    "SELECT work_item_id,current_state,target_surface FROM work_items"
                    " WHERE target_surface IN"
                    " ('daily_app_editorial_window','daily_app_material_event_window')"
                ).fetchall()
        except Exception:  # noqa: BLE001
            return []
        completed: list[datetime] = []
        for row in rows:
            if target_surface and str(row["target_surface"]) != target_surface:
                continue
            if str(row["current_state"]) not in WINDOW_EXECUTED_STATES:
                continue
            checkpoint = self._load_editorial_opportunity_checkpoint(
                str(row["work_item_id"])
            )
            if checkpoint is None:
                continue
            ended = checkpoint["end"].astimezone(timezone.utc)
            if ended <= now:
                completed.append(ended)
        return sorted(completed)

    def _material_event_wake_eligibility(
        self, window: Mapping[str, Any], now: datetime
    ) -> dict[str, Any]:
        """Apply shadow, competing-cycle, routine-absorption, spacing, and saturation controls."""
        if self._operating_mode != "SHADOW_ONLY":
            return {"eligible": False, "reason": "SHADOW_NO_PUBLIC_WRITE_SCOPE_REQUIRED"}
        active = [
            value
            for value in self._store.active_editorial_cycle_window_ids()
            if str(value) != str(window.get("window_id") or "")
        ]
        if active:
            return {"eligible": False, "reason": "ACTIVE_EDITORIAL_CYCLE_PRESENT"}
        due_unexecuted_scheduled = [
            scheduled
            for scheduled in self._currently_due_scheduled_windows(now)
            if self._window_state(str(scheduled["window_id"]))
            not in WINDOW_EXECUTED_STATES
        ]
        if due_unexecuted_scheduled:
            return {
                "eligible": False,
                "reason": "CURRENTLY_DUE_SCHEDULED_OPPORTUNITY_AVAILABLE",
                "absorbing_scheduled_window_ids": [
                    str(value["window_id"])
                    for value in due_unexecuted_scheduled
                ],
            }
        completed = self._completed_editorial_opportunity_times(now)
        completed_material_events = self._completed_editorial_opportunity_times(
            now,
            target_surface="daily_app_material_event_window",
        )
        day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        completed_material_events_today = [
            value for value in completed_material_events if value >= day_start
        ]
        if len(completed_material_events_today) >= int(
            self._policy.material_event_daily_saturation_limit
        ):
            return {"eligible": False, "reason": "MATERIAL_EVENT_DAILY_SATURATION_LIMIT"}
        if completed and now - completed[-1] < timedelta(
            hours=float(self._policy.minimum_cycle_spacing_hours)
        ):
            return {"eligible": False, "reason": "MINIMUM_CYCLE_SPACING_ACTIVE"}
        return {
            "eligible": True,
            "reason": "SHADOW_MATERIAL_EVENT_WAKE_ELIGIBLE",
            "publication_enabled": False,
            "public_write_scope_granted": False,
        }

    def _finalize_material_event_priority(
        self, priority_id: str, *, reason_code: str
    ) -> str:
        """Terminalize one priority through canonical state transitions."""
        from live_contentops.durable_operational_store_v1 import LeaseConflictError

        if self._window_state(priority_id) != "DISCOVERED":
            return "ALREADY_TERMINAL"
        try:
            lease = self._store.claim_work_item(
                lease_key=priority_id,
                work_item_id=priority_id,
                owner_ref=self._owner_ref,
                ttl_seconds=self._lease_ttl_seconds,
            )
        except LeaseConflictError:
            return "ACTIVE_OWNER"
        try:
            for to_state in ("EVIDENCE_PENDING", "EVIDENCE_BLOCKED", "REJECTED"):
                self._transition(
                    window_id=priority_id,
                    to_state=to_state,
                    lease_key=str(lease["lease_key"]),
                    fencing_token=int(lease["fencing_token"]),
                    reason_code=reason_code,
                    explanation=(
                        f"Material-event priority {priority_id} {reason_code.casefold()}"
                    ),
                )
            return reason_code
        finally:
            try:
                self._store.release_lease(
                    str(lease["lease_id"]), self._owner_ref, int(lease["fencing_token"])
                )
            except Exception:  # noqa: BLE001
                pass

    def _pending_material_event_priorities(
        self, now: datetime, *, expire_stale: bool
    ) -> list[dict[str, Any]]:
        """Load restart-safe current priority artifacts; stale rows terminalize with zero write."""
        priorities: list[dict[str, Any]] = []
        for window in self._pending_material_event_windows(now):
            priority_id = str(window["window_id"])
            path = self._output_root / priority_id / "material_event_priority_v1.json"
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, TypeError, ValueError):
                value = {
                    "schema_version": "contentops.material_event_priority.v1",
                    "priority_id": priority_id,
                    "headline_ids": [],
                    "source_refs": [],
                    "update_chain_identities": [],
                    "created_at_utc": _iso_utc(window["start"]),
                    "expires_at_utc": _iso_utc(
                        window["start"]
                        + timedelta(hours=self._policy.freshness_max_age_hours)
                    ),
                    "artifact_reconstructed": True,
                    "grants_evidence_or_publication_authority": False,
                }
            try:
                expires = _parse_utc(str(value.get("expires_at_utc") or ""))
            except ValueError:
                expires = window["start"] + timedelta(
                    hours=self._policy.freshness_max_age_hours
                )
            if expires <= now:
                if expire_stale:
                    self._finalize_material_event_priority(
                        priority_id, reason_code="MATERIAL_EVENT_PRIORITY_EXPIRED"
                    )
                continue
            priorities.append(dict(value))
        return priorities

    @staticmethod
    def _merge_material_event_priorities(
        priorities: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        return {
            "schema_version": "contentops.material_event_priority_briefing.v1",
            "priority_ids": sorted({str(row.get("priority_id") or "") for row in priorities if str(row.get("priority_id") or "")}),
            "headline_ids": sorted({str(value) for row in priorities for value in (row.get("headline_ids") or []) if str(value)}),
            "source_refs": sorted({str(value) for row in priorities for value in (row.get("source_refs") or []) if str(value)}),
            "update_chain_identities": sorted({str(value) for row in priorities for value in (row.get("update_chain_identities") or []) if str(value)}),
            "priority_count": len(priorities),
            "grants_evidence_or_publication_authority": False,
            "changes_candidate_eligibility_gates": False,
        }

    def _pending_material_event_windows(self, now: datetime) -> list[dict[str, Any]]:
        """Reconstruct durable unconsumed material wakes after restart or KILL_SWITCH."""
        try:
            with self._store.get_read_only_connection() as conn:
                rows = conn.execute(
                    "SELECT work_item_id,created_at FROM work_items"
                    " WHERE target_surface='daily_app_material_event_window'"
                    " AND current_state='DISCOVERED' ORDER BY created_at,work_item_id"
                ).fetchall()
        except Exception:  # noqa: BLE001 - unavailable queue fails closed for this tick
            return []
        windows: list[dict[str, Any]] = []
        for row in rows:
            try:
                start = _parse_utc(str(row["created_at"]))
            except ValueError:
                start = now
            windows.append({
                "window_id": str(row["work_item_id"]),
                "trigger": TRIGGER_MATERIAL_EVENT,
                "start": start,
                "end": now,
                "session": str(row["work_item_id"]),
                "target_surface": "daily_app_material_event_window",
                "durable_pending_material_event": True,
            })
        return windows

    def _currently_due_scheduled_windows(
        self, now: datetime
    ) -> list[dict[str, Any]]:
        """Return canonical routine opportunities inside their due/grace interval.

        Terminal state is deliberately not filtered here: callers decide whether they need the
        historical due row or only an actually available, unexecuted routine opportunity.
        """
        windows: list[dict[str, Any]] = []
        grace = timedelta(hours=1.0)
        timing_offset = timedelta(minutes=self._timing_policy_offset_minutes())
        for day_offset in (0, -1):
            day = now + timedelta(days=day_offset)
            for core in self._policy.core_windows:
                if day.weekday() not in set(core.eligible_weekdays_utc):
                    continue
                start, end = self._window_for_day(core, day)
                start = start + timing_offset
                end = end + timing_offset
                if not (start <= now <= end + grace):
                    continue
                if not self._within_production_epoch(start):
                    continue
                windows.append(
                    {
                        "window_id": editorial_window_id(
                            policy_version=self._policy.policy_version,
                            window_start_utc=start,
                            window_end_utc=end,
                            session=core.session,
                            trigger_kind=TRIGGER_SCHEDULED,
                        ),
                        "trigger": TRIGGER_SCHEDULED,
                        "start": start,
                        "end": end,
                        "session": core.session,
                    }
                )
        return windows

    def _due_windows(
        self, now: datetime, materiality_metadata: Optional[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        # FDA-G maintains intake/state/runtime truth but the native Desktop Automation is the
        # primary routine heavy-editorial brain in production.  When that owner is selected,
        # FDA-G must not create, claim, or terminalize the same scheduled opportunity first.
        windows = (
            []
            if self._scheduled_editorial_owner
            == SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP
            else self._currently_due_scheduled_windows(now)
        )
        # Scheduled core windows for the current day (and previous day for late ticks). A
        # scheduled window is due only while we are inside [start, end + small grace]; it does
        # not stay due long after it ends. minimum_cycle_spacing_hours remains an anti-spam
        # control between cycles, not the due-window horizon.
        # The same supervisor may execute one bounded material opportunity outside routine
        # windows only in SHADOW/NO_PUBLIC_WRITE scope. Autonomous/public scope remains queued
        # for the next scheduled opportunity until a separate exact owner grant exists.
        material_windows = []
        for material_window in self._pending_material_event_windows(now):
            eligibility = self._material_event_wake_eligibility(material_window, now)
            if eligibility.get("eligible"):
                material_window["wake_eligibility"] = eligibility
                material_windows.append(material_window)
        if material_windows:
            windows = material_windows + windows
        # De-duplicate and drop windows already executed.
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for window in windows:
            window_id = window["window_id"]
            if window_id in seen:
                continue
            seen.add(window_id)
            unique.append(window)
        return unique

    def _window_state(self, window_id: str) -> Optional[str]:
        from live_contentops.durable_operational_store_v1 import WorkItemNotFoundError

        try:
            item = self._store.get_work_item(window_id)
            return str(item.get("current_state"))
        except WorkItemNotFoundError:
            return None

    # -- window execution -----------------------------------------------------

    def _editorial_opportunity_checkpoint_path(self, window_id: str) -> Path:
        return self._output_root / window_id / "editorial_opportunity_v1.json"

    def _persist_editorial_opportunity_checkpoint(
        self, window: Mapping[str, Any]
    ) -> None:
        """Persist the claimed opportunity identity before any long network/model activity."""
        window_id = str(window["window_id"])
        payload = {
            "schema_version": "contentops.editorial_opportunity.v1",
            "window_id": window_id,
            "trigger": str(window.get("trigger") or ""),
            "start_utc": _iso_utc(window["start"]),
            "end_utc": _iso_utc(window["end"]),
            "session": str(window.get("session") or ""),
            "target_surface": str(
                window.get("target_surface") or "daily_app_editorial_window"
            ),
            "publication_authority_granted": False,
        }
        payload["opportunity_logical_hash"] = _logical_hash(payload)
        path = self._editorial_opportunity_checkpoint_path(window_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != payload:
                raise ValueError("editorial_opportunity_checkpoint_identity_conflict")
            return
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _load_editorial_opportunity_checkpoint(
        self, window_id: str
    ) -> Optional[dict[str, Any]]:
        path = self._editorial_opportunity_checkpoint_path(window_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            logical_hash = str(payload.get("opportunity_logical_hash") or "")
            material = {
                key: value for key, value in payload.items() if key != "opportunity_logical_hash"
            }
            if (
                payload.get("schema_version") != "contentops.editorial_opportunity.v1"
                or str(payload.get("window_id") or "") != window_id
                or logical_hash != _logical_hash(material)
            ):
                return None
            return {
                "window_id": window_id,
                "trigger": str(payload.get("trigger") or ""),
                "start": _parse_utc(str(payload.get("start_utc") or "")),
                "end": _parse_utc(str(payload.get("end_utc") or "")),
                "session": str(payload.get("session") or ""),
                "target_surface": str(
                    payload.get("target_surface") or "daily_app_editorial_window"
                ),
            }
        except Exception:  # noqa: BLE001 - corrupt checkpoint grants no resume authority
            return None

    def _transition(
        self,
        *,
        window_id: str,
        to_state: str,
        lease_key: str,
        fencing_token: int,
        reason_code: str,
        explanation: str,
    ) -> None:
        item = self._store.get_work_item(window_id)
        self._store.transition_state(
            work_item_id=window_id,
            expected_from_state=str(item["current_state"]),
            to_state=to_state,
            expected_state_version=int(item["state_version"]),
            actor_class="ContentOpsDailyAppSupervisor",
            actor_ref=self._owner_ref,
            reason_code=reason_code,
            explanation=explanation,
            lease_key=lease_key,
            fencing_token=fencing_token,
            input_artifact_ids=[],
            output_artifact_ids=[],
            correlation_id=f"corr_{window_id}",
        )

    def _recover_stale_pending(self, window_id: str) -> str:
        """Recover a stale EVIDENCE_PENDING claim to a terminal state without re-invoking.

        A restart that finds a claimed-but-incomplete window must not create a second
        independent cycle. Recovery must claim the ORIGINAL window lease key so an active
        owner remains protected by the durable store's fencing rules. Only a released or
        expired original lease may be taken over and terminalized without re-execution.
        """
        from live_contentops.durable_operational_store_v1 import LeaseConflictError

        try:
            lease = self._store.claim_work_item(
                lease_key=window_id,
                work_item_id=window_id,
                owner_ref=self._owner_ref,
                ttl_seconds=self._lease_ttl_seconds,
            )
        except LeaseConflictError:
            return "active_owner"
        fencing = int(lease["fencing_token"])
        try:
            # Close the observation-to-claim race: the original owner may have completed
            # between our EVIDENCE_PENDING read and this successful takeover.
            if self._window_state(window_id) != "EVIDENCE_PENDING":
                return "state_changed"
            self._transition(
                window_id=window_id,
                to_state="EVIDENCE_BLOCKED",
                lease_key=lease["lease_key"],
                fencing_token=fencing,
                reason_code="STALE_WINDOW_CLAIM_RECOVERED",
                explanation=f"Recovered stale in-progress window {window_id}",
            )
            self._transition(
                window_id=window_id,
                to_state="REJECTED",
                lease_key=lease["lease_key"],
                fencing_token=fencing,
                reason_code="STALE_WINDOW_CLAIM_RECOVERED_NO_PUBLICATION",
                explanation=f"Stale window {window_id} recovered without re-execution",
            )
            return "recovered"
        finally:
            try:
                self._store.release_lease(lease["lease_id"], self._owner_ref, fencing)
            except Exception:  # noqa: BLE001
                pass

    def _load_editorial_intelligence_runtime(self) -> dict[str, Any]:
        """Load the complete corpus and complete CC metadata catalog for preselection."""
        runtime: dict[str, Any] = {
            "published_corpus": {
                "articles": [], "article_count": 0, "content_hash_coverage": 0,
                "derived_from_existing_durable_truth": True,
            },
            "cc_catalog": {
                "stores": [], "store_count_discovered": 0, "discovery_complete": False,
                "root_exists": False,
            },
        }
        try:
            from live_contentops.published_corpus_read_model_v1 import load_published_corpus

            runtime["published_corpus"] = load_published_corpus(
                self._store, output_root=self._output_root
            )
        except Exception as exc:  # noqa: BLE001
            runtime["published_corpus_error"] = type(exc).__name__
        try:
            from live_contentops.capital_chronicle_data_catalog_v1 import (
                DEFAULT_CC_ROOT,
                discover_cc_data_estate,
            )

            runtime["cc_catalog"] = discover_cc_data_estate(cc_root=DEFAULT_CC_ROOT)
        except Exception as exc:  # noqa: BLE001
            runtime["cc_catalog_error"] = type(exc).__name__
        return runtime

    def _build_editorial_portfolio_context(
        self, output_dir: Path, runtime: Optional[Mapping[str, Any]] = None
    ) -> dict[str, Any]:
        """Deterministic pre-cycle intelligence: complete published corpus, today's portfolio
        state, Capital Chronicle read-model availability, and the versioned portfolio policy.
        Written next to the cycle evidence so every decision is auditable against it."""
        context: dict[str, Any] = {"schema_version": "contentops.editorial_portfolio_context.v1"}
        intelligence = dict(runtime or self._load_editorial_intelligence_runtime())
        try:
            from live_contentops.editorial_portfolio_v1 import (
                bootstrap_portfolio_policy,
                portfolio_state_today,
            )

            corpus = dict(intelligence["published_corpus"])
            context["published_corpus"] = {
                "article_count": corpus["article_count"],
                "content_hash_coverage": corpus["content_hash_coverage"],
                "full_text_article_count": corpus.get("full_text_article_count", 0),
                "content_unavailable_count": corpus.get("content_unavailable_count", 0),
                "derived_from_existing_durable_truth": True,
            }
            context["portfolio_state"] = portfolio_state_today(corpus["articles"])
            context["portfolio_policy"] = bootstrap_portfolio_policy()
        except Exception as exc:  # noqa: BLE001 - portfolio context is best-effort intelligence
            context["published_corpus"] = {"error": type(exc).__name__}
        try:
            estate = dict(intelligence["cc_catalog"])
            context["capital_chronicle_read_model"] = {
                "state": "READY" if estate.get("root_exists") else "UNAVAILABLE",
                "store_count": int(estate.get("store_count_discovered") or 0),
                "store_count_total": int(estate.get("store_count_total") or 0),
                "stores_omitted": int(estate.get("stores_omitted") or 0),
                "discovery_complete": estate.get("discovery_complete") is True,
                "catalog_fingerprint": estate.get("catalog_fingerprint"),
                "cache_state": (estate.get("cache") or {}).get("state"),
            }
        except Exception as exc:  # noqa: BLE001
            context["capital_chronicle_read_model"] = {"state": "DEGRADED", "error": type(exc).__name__}
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "editorial_portfolio_context_v1.json").write_text(
                json.dumps(context, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
            )
        except OSError:
            pass
        return context

    def _record_editorial_novelty_decision(
        self,
        *,
        output_dir: Path,
        cycle_evidence: Mapping[str, Any],
        portfolio_context: Mapping[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Project the already-completed preselection decision for operator compatibility."""
        selected = (cycle_evidence.get("ranked_viability") or {}).get("selected_cluster")
        if not isinstance(selected, Mapping):
            return None
        try:
            decision = dict(selected.get("preselection_novelty") or {})
            if not decision:
                return None
            decision["classification_occurs_before_article_generation"] = True
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "editorial_novelty_decision_v1.json").write_text(
                json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return decision
        except Exception:  # noqa: BLE001 - novelty intelligence is best-effort
            return None

    @staticmethod
    def _published_memory_projection(value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            row = dict(value)
        else:
            serializer = getattr(value, "to_dict", None)
            row = dict(serializer()) if callable(serializer) else {
                key: getattr(value, key, None)
                for key in (
                    "story_identity", "title", "published_at_utc", "public_object_id",
                    "canonical_url", "canonical_url_hash", "content_hash",
                    "update_chain_identity", "article_mode", "article_identity",
                    "content_status", "source_work_item_id",
                )
            }
        return {
            key: row.get(key)
            for key in (
                "story_identity", "title", "published_at_utc", "public_object_id",
                "canonical_url", "canonical_url_hash", "content_hash",
                "update_chain_identity", "article_mode", "article_identity",
                "content_status", "source_work_item_id",
            )
        }

    def _record_published_memory_cycle_proof(
        self,
        *,
        output_dir: Path,
        window: Mapping[str, Any],
        before_runtime: Mapping[str, Any],
        after_corpus: Mapping[str, Any],
        cycle_evidence: Mapping[str, Any],
        portfolio_context: Mapping[str, Any],
        novelty_decision: Optional[Mapping[str, Any]],
        lifecycle: Optional[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Persist the deterministic before/after proof for canonical published memory."""
        before_corpus = dict(before_runtime.get("published_corpus") or {})
        before_articles = [
            self._published_memory_projection(row)
            for row in (before_corpus.get("articles") or [])
        ]
        after_articles = [
            self._published_memory_projection(row)
            for row in (after_corpus.get("articles") or [])
        ]
        before_count = int(before_corpus.get("article_count") or len(before_articles))
        after_count = int(after_corpus.get("article_count") or len(after_articles))
        before_identities = [
            str(row.get("article_identity") or row.get("story_identity") or "")
            for row in before_articles
            if str(row.get("article_identity") or row.get("story_identity") or "")
        ]
        after_identities = [
            str(row.get("article_identity") or row.get("story_identity") or "")
            for row in after_articles
            if str(row.get("article_identity") or row.get("story_identity") or "")
        ]
        selected = dict(
            ((cycle_evidence.get("ranked_viability") or {}).get("selected_cluster") or {})
        )
        novelty = dict(novelty_decision or selected.get("preselection_novelty") or {})
        prior_identity = str(novelty.get("best_prior_article") or "")
        prior_article = next(
            (
                row for row in before_articles
                if str(row.get("story_identity") or "") == prior_identity
            ),
            None,
        )
        window_id = str(window.get("window_id") or "")
        newly_observed = [
            row for row in after_articles
            if str(row.get("article_identity") or row.get("story_identity") or "")
            not in set(before_identities)
        ]
        canonical_observed = next(
            (
                row for row in after_articles
                if str(row.get("source_work_item_id") or "") == window_id
            ),
            newly_observed[0] if newly_observed else None,
        )
        try:
            from live_contentops.editorial_portfolio_v1 import portfolio_state_today

            after_portfolio = portfolio_state_today(after_corpus.get("articles") or [])
        except Exception as exc:  # noqa: BLE001
            after_portfolio = {"error": type(exc).__name__}
        article = dict(cycle_evidence.get("article") or {})
        proof_core = {
            "schema_version": "contentops.published_memory_cycle_proof.v1",
            "window_id": window_id,
            "trigger_kind": str(
                window.get("trigger_kind")
                or window.get("trigger")
                or window.get("target_surface")
                or ""
            ),
            "corpus_before_count": before_count,
            "corpus_after_count": after_count,
            "corpus_count_delta": after_count - before_count,
            "corpus_reload_error": after_corpus.get("published_corpus_error"),
            "before_article_identities": before_identities,
            "after_article_identities": after_identities,
            "before_story_identities": [row.get("story_identity") for row in before_articles],
            "after_story_identities": [row.get("story_identity") for row in after_articles],
            "before_update_chain_identities": [
                row.get("update_chain_identity") for row in before_articles
            ],
            "after_update_chain_identities": [
                row.get("update_chain_identity") for row in after_articles
            ],
            "selected_candidate": {
                "cluster_id": selected.get("cluster_id")
                or (cycle_evidence.get("ranked_viability") or {}).get("selected_cluster_id"),
                "update_chain_identity": selected.get("update_chain_identity"),
                "editorial_classification": selected.get("editorial_classification"),
                "resolved_article_mode": selected.get("resolved_article_mode")
                or article.get("resolved_article_mode"),
            },
            "prior_related_article_lookup": {
                "best_prior_article": novelty.get("best_prior_article"),
                "best_prior_title": novelty.get("best_prior_title"),
                "prior_article": prior_article,
            },
            "novelty_update_chain": {
                "decision": novelty.get("decision"),
                "update_chain_match": novelty.get("update_chain_match"),
                "material_delta_signals": novelty.get("material_delta_signals"),
                "material_delta_evaluation": novelty.get("material_delta_evaluation"),
            },
            "portfolio_concentration": {
                "candidate_penalty": selected.get("portfolio_concentration_penalty"),
                "candidate_effective_penalty": selected.get(
                    "portfolio_concentration_penalty_effective"
                ),
                "before": portfolio_context.get("portfolio_state"),
                "after": after_portfolio,
            },
            "canonical_article_observed_after_lifecycle": canonical_observed,
            "publication_lifecycle": {
                "canonical_article_status": (lifecycle or {}).get("canonical_article_status"),
                "canonical_publication_status": (lifecycle or {}).get(
                    "canonical_publication_status"
                ),
                "canonical_url": (lifecycle or {}).get("canonical_url"),
                "distribution_status": (lifecycle or {}).get("distribution_status"),
                "unknown_write_detected": bool(
                    (lifecycle or {}).get("unknown_write_detected")
                ),
            },
            "cycle_classification": str(cycle_evidence.get("classification") or ""),
            "no_publication_cycle": str(cycle_evidence.get("classification") or "")
            in {"NO_PUBLICATION", "BLOCKED", ""},
            "publication_authority_granted": False,
            "factual_or_numeric_authority_granted": False,
        }
        proof = {
            **proof_core,
            "proof_sha256": sha256(
                json.dumps(
                    proof_core, ensure_ascii=True, separators=(",", ":"),
                    sort_keys=True, default=str,
                ).encode("utf-8")
            ).hexdigest(),
        }
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "published_memory_cycle_proof_v1.json").write_text(
                json.dumps(proof, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return proof

    def _native_desktop_handoff_path(self, window_id: str) -> Path:
        from live_contentops.native_desktop_production_handoff_v1 import (
            HANDOFF_FILE_NAME,
        )

        return self._output_root / window_id / HANDOFF_FILE_NAME

    @staticmethod
    def _native_desktop_pending_handoff_outcome(
        checkpoint: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "executed": True,
            "classification": str(checkpoint.get("handoff_status") or "XHIGH_REQUIRED"),
            "exact_next_blocker": str(
                checkpoint.get("exact_next_blocker")
                or "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
            ),
            "editorial_worker_request": dict(
                checkpoint.get("editorial_worker_request") or {}
            ),
            "governed_input_hash": checkpoint.get("governed_input_hash"),
            "handoff_checkpoint_path": checkpoint.get("handoff_checkpoint_path"),
            "handoff_logical_hash": checkpoint.get("handoff_logical_hash"),
            "resume_sequence": checkpoint.get("resume_sequence"),
            "candidate_rank": checkpoint.get("candidate_rank"),
            "candidate_cluster_id": checkpoint.get("candidate_cluster_id"),
            "terminal_state": "EVIDENCE_PENDING",
            "opportunity_resumable": True,
            "opportunity_terminalized": False,
            "lease_released_after_return": True,
            "legacy_writer_fallback_used": False,
            "sdk_writer_substitution_used": False,
            "public_write_performed": bool(checkpoint.get("public_write_performed")),
            "unknown_write_detected": bool(checkpoint.get("unknown_write_detected")),
        }

    def _persist_native_desktop_pending_handoff(
        self,
        *,
        window: Mapping[str, Any],
        attempt_number: int,
        attempt_run_id: str,
        attempt_output_dir: Path,
        attempt_result: Mapping[str, Any],
        prior_attempt_results: Sequence[Mapping[str, Any]],
        qualified_records: Sequence[Mapping[str, Any]],
        work_budget: int,
    ) -> dict[str, Any]:
        from live_contentops.native_desktop_production_handoff_v1 import (
            WORKER_DECISION,
            load_handoff_checkpoint,
            logical_hash,
            persist_handoff_checkpoint,
            read_json,
            semantic_resume_bindings_from_probe,
            validate_same_worker_revision_contract,
            validate_worker_request_binding,
            validated_viability_checkpoint,
        )

        result = dict(attempt_result)
        reason = str(result.get("exact_next_blocker") or "")
        revision_contract = dict(result.get("same_xhigh_worker_revision_contract") or {})
        route = dict(result.get("editorial_worker_routing") or {})
        if reason == "SAME_XHIGH_WORKER_REVISION_REQUIRED":
            revision_contract = validate_same_worker_revision_contract(
                revision_contract
            )
            worker_request = dict(revision_contract.get("worker_request") or {})
            governed_hash = str(
                revision_contract.get("governed_input_hash")
                or worker_request.get("governed_input_hash")
                or ""
            )
            handoff_status = "SAME_XHIGH_WORKER_REVISION_REQUIRED"
        else:
            if route.get("decision") != WORKER_DECISION:
                raise ValueError("native_desktop_pending_worker_route_missing")
            worker_request = dict(route.get("worker_request") or {})
            governed_hash = str(
                route.get("governed_input_hash")
                or worker_request.get("governed_input_hash")
                or ""
            )
            handoff_status = (
                "XHIGH_REQUIRED_FOR_CANDIDATE_CONTINUATION"
                if reason == "NEXT_NATIVE_XHIGH_WORKER_REQUIRED"
                else "XHIGH_REQUIRED"
            )
        if (
            len(governed_hash) != 64
            or str(worker_request.get("governed_input_hash") or "") != governed_hash
        ):
            raise ValueError("native_desktop_pending_worker_hash_invalid")

        cycle_path = attempt_output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        viability_path = attempt_output_dir / "rolling_x_ranked_viability_v1.json"
        intake_path = attempt_output_dir / "rolling_x_intake_v1.json"
        if not cycle_path.is_file() or not viability_path.is_file() or not intake_path.is_file():
            raise ValueError("native_desktop_pending_canonical_checkpoint_missing")
        semantic_bindings = semantic_resume_bindings_from_probe(result)
        viability = validated_viability_checkpoint(read_json(viability_path))
        worker_request = validate_worker_request_binding(
            worker_request,
            expected_governed_input_hash=governed_hash,
            viability=viability,
            allow_same_worker_revision=bool(revision_contract),
        )

        current_path = self._native_desktop_handoff_path(str(window["window_id"]))
        sequence = 1
        if current_path.exists():
            sequence = int(load_handoff_checkpoint(current_path).get("resume_sequence") or 0) + 1
        checkpoint = {
            "canonical_opportunity_id": str(window["window_id"]),
            "runtime_run_id": str(window["window_id"]),
            "automation_id": str(window.get("native_desktop_automation_id") or ""),
            "session": str(window.get("session") or ""),
            "attempt_number": int(attempt_number),
            "attempt_run_id": str(attempt_run_id),
            "work_budget": int(work_budget),
            "resume_sequence": sequence,
            "handoff_status": handoff_status,
            "exact_next_blocker": (
                reason
                if reason in {
                    "SAME_XHIGH_WORKER_REVISION_REQUIRED",
                    "NEXT_NATIVE_XHIGH_WORKER_REQUIRED",
                }
                else WORKER_DECISION
            ),
            "governed_input_hash": governed_hash,
            "editorial_worker_request": worker_request,
            "same_xhigh_worker_revision_contract": revision_contract,
            "prepare_cycle_evidence_path": str(cycle_path),
            "prepare_cycle_evidence_sha256": logical_hash(read_json(cycle_path)),
            "intake_checkpoint_path": str(intake_path),
            "intake_checkpoint_sha256": logical_hash(read_json(intake_path)),
            "prepared_candidate_checkpoint_path": str(
                attempt_output_dir / "rolling_x_prepared_candidate_state_v1.json"
            ),
            "viability_checkpoint_path": str(viability_path),
            "viability_logical_hash": viability.get("viability_logical_hash"),
            "semantic_resume_bindings": semantic_bindings,
            "candidate_rank": viability.get("selected_rank"),
            "candidate_cluster_id": viability.get("selected_cluster_id"),
            "candidate_headline_ids": list(viability.get("selected_headline_ids") or []),
            "prior_attempt_results": [dict(row) for row in prior_attempt_results],
            "qualified_records": [dict(row) for row in qualified_records],
            "public_write_performed": bool(result.get("public_write_performed")),
            "unknown_write_detected": bool(result.get("unknown_write_detected")),
            "legacy_writer_fallback_used": False,
            "sdk_writer_substitution_used": False,
            "handoff_checkpoint_path": str(current_path),
        }
        persisted = persist_handoff_checkpoint(current_path, checkpoint)
        return persisted

    def _execute_window(
        self,
        window: Mapping[str, Any],
        now: datetime,
        *,
        split_phase_operation: Optional[str] = None,
        split_phase_worker_return: Optional[Mapping[str, Any]] = None,
        split_phase_coordinator_review: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        from live_contentops.durable_operational_store_v1 import (
            LeaseConflictError,
        )

        window_id = window["window_id"]
        split_operation = str(split_phase_operation or "").strip().upper() or None
        if split_operation not in {None, "PREPARE", "COMPLETE"}:
            raise ValueError("native_desktop_split_phase_operation_invalid")
        if split_operation is not None and not bool(
            window.get("native_desktop_zero_public_write")
        ):
            raise ValueError("native_desktop_split_phase_requires_zero_write_window")
        handoff_checkpoint: Optional[dict[str, Any]] = None
        if split_operation == "COMPLETE":
            from live_contentops.native_desktop_production_handoff_v1 import (
                load_handoff_checkpoint,
            )

            handoff_checkpoint = load_handoff_checkpoint(
                self._native_desktop_handoff_path(str(window_id))
            )
            if (
                str(handoff_checkpoint.get("canonical_opportunity_id") or "")
                != str(window_id)
                or str(handoff_checkpoint.get("automation_id") or "")
                != str(window.get("native_desktop_automation_id") or "")
            ):
                raise ValueError("native_desktop_handoff_runtime_identity_mismatch")
            if not isinstance(split_phase_worker_return, Mapping):
                raise ValueError("native_desktop_worker_return_required")
            if not isinstance(split_phase_coordinator_review, Mapping):
                raise ValueError("native_desktop_coordinator_review_receipt_required")
        # Idempotent creation: the same window_id always maps to the same work item. A restart
        # or duplicate tick therefore never creates a second independent cycle/work item.
        if self._window_state(window_id) is None:
            target_surface = str(
                window.get("target_surface") or "daily_app_editorial_window"
            )
            title = (
                f"Daily App material event {window_id}"
                if target_surface == "daily_app_material_event_window"
                else f"Daily App editorial window {window_id}"
            )
            self._store.create_work_item(
                story_id=window_id,
                title=title,
                target_surface=target_surface,
                work_item_id=window_id,
            )
        # This small immutable checkpoint makes a claimed opportunity resumable after a host or
        # provider interruption. It is written before the lease enters long-running work.
        self._persist_editorial_opportunity_checkpoint(window)
        state = self._window_state(window_id)
        if state in WINDOW_EXECUTED_STATES:
            return {"executed": False, "reason": "already_executed_terminal_state"}
        if state == "EVIDENCE_PENDING":
            try:
                claim = self._store.claim_work_item(
                    lease_key=window_id,
                    work_item_id=window_id,
                    owner_ref=self._owner_ref,
                    ttl_seconds=self._lease_ttl_seconds,
                )
            except LeaseConflictError:
                return {"executed": False, "reason": "active_window_owned_elsewhere"}
            if self._window_state(window_id) != "EVIDENCE_PENDING":
                try:
                    self._store.release_lease(
                        claim["lease_id"], self._owner_ref, int(claim["fencing_token"])
                    )
                except Exception:  # noqa: BLE001
                    pass
                return {"executed": False, "reason": "window_state_changed_during_recovery"}
        else:
            # state is DISCOVERED: claim and execute exactly once.
            try:
                claim = self._store.claim_work_item(
                    lease_key=window_id,
                    work_item_id=window_id,
                    owner_ref=self._owner_ref,
                    ttl_seconds=self._lease_ttl_seconds,
                )
            except LeaseConflictError:
                return {"executed": False, "reason": "lease_conflict_another_owner"}
        lease_id = str(claim["lease_id"])
        fencing = int(claim["fencing_token"])
        lease_key = str(claim["lease_key"])
        try:
            if state == "DISCOVERED":
                self._transition(
                    window_id=window_id,
                    to_state="EVIDENCE_PENDING",
                    lease_key=lease_key,
                    fencing_token=fencing,
                    reason_code="EDITORIAL_WINDOW_DUE",
                    explanation=f"Executing editorial window {window_id}",
                )
            if split_operation == "PREPARE":
                handoff_path = self._native_desktop_handoff_path(str(window_id))
                if handoff_path.exists():
                    from live_contentops.native_desktop_production_handoff_v1 import (
                        load_handoff_checkpoint,
                    )

                    existing_handoff = load_handoff_checkpoint(handoff_path)
                    return self._native_desktop_pending_handoff_outcome(existing_handoff)
            native_desktop_zero_write = bool(
                window.get("native_desktop_zero_public_write")
            )
            publication_enabled = (
                self._refresh_operating_mode() == "AUTONOMOUS_DEFAULT"
                and not native_desktop_zero_write
            )
            material_event_shadow = str(window.get("trigger") or "") == TRIGGER_MATERIAL_EVENT
            if material_event_shadow:
                publication_enabled = False
            cutoff = window["end"]
            output_dir = self._output_root / window_id
            from live_contentops.newsroom_production_day_v1 import (
                ROUTINE_SESSION_ORDINAL,
            )

            managed_daily_output = bool(
                str(window.get("trigger") or "") == TRIGGER_SCHEDULED
                and str(window.get("session") or "") in ROUTINE_SESSION_ORDINAL
            )
            # The newsroom cycle never performs a public write.  In SHADOW_ONLY, every warranted
            # final article still uses the real HIGH worker contract and returns a plan; this
            # supervisor simply does not hand that plan to the publication lifecycle.
            cycle_article_worker_required = bool(
                publication_enabled
                or self._operating_mode == "SHADOW_ONLY"
                or native_desktop_zero_write
            )
            cycle_kwargs: dict[str, Any] = {
                "cutoff_utc": _iso_utc(cutoff),
                "publication_enabled": cycle_article_worker_required,
            }
            source_route_health_state = self._load_source_route_health_state()
            if source_route_health_state:
                cycle_kwargs["source_route_health"] = source_route_health_state
            prepared_candidate_state = self._load_prepared_candidate_checkpoint(cutoff)
            if prepared_candidate_state is not None:
                cycle_kwargs["prepared_candidate_state"] = prepared_candidate_state
            if CANONICAL_CAPITAL_CHRONICLE_ROOT.exists():
                cycle_kwargs["capital_chronicle_root"] = CANONICAL_CAPITAL_CHRONICLE_ROOT
            if self._sidecar_glob:
                cycle_kwargs["sidecar_glob"] = self._sidecar_glob
            intelligence = self._load_editorial_intelligence_runtime()
            portfolio_context = self._build_editorial_portfolio_context(
                output_dir, intelligence
            )
            learning_policy = self._active_learning_policy_briefing()
            portfolio_context["active_learning_policy"] = learning_policy
            material_priorities: list[dict[str, Any]] = []
            material_priority: dict[str, Any] = {}
            if str(window.get("trigger") or "") == TRIGGER_SCHEDULED:
                material_priorities = self._pending_material_event_priorities(
                    now, expire_stale=True
                )
                material_priority = self._merge_material_event_priorities(
                    material_priorities
                )
                if material_priorities:
                    cycle_kwargs["material_event_priority"] = material_priority
                    portfolio_context["material_event_priority"] = material_priority
            elif material_event_shadow:
                priority_path = output_dir / "material_event_priority_v1.json"
                try:
                    own_priority = json.loads(priority_path.read_text(encoding="utf-8"))
                except (OSError, TypeError, ValueError):
                    own_priority = {}
                if own_priority:
                    material_priority = self._merge_material_event_priorities(
                        [own_priority]
                    )
                    cycle_kwargs["material_event_priority"] = material_priority
                    portfolio_context["material_event_priority"] = material_priority
            try:
                (output_dir / "editorial_portfolio_context_v1.json").write_text(
                    json.dumps(portfolio_context, indent=2, sort_keys=True, default=str) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            cycle_kwargs.update({
                "operating_mode": self._operating_mode,
                "cc_catalog": dict(intelligence.get("cc_catalog") or {}),
                "learning_policy": learning_policy,
            })
            from live_contentops.newsroom_production_day_v1 import (
                bounded_deficit_work_needed,
                build_production_day_snapshot,
                load_production_day_discovery_accounting,
                persist_production_day_snapshot,
                persist_qualified_article_record,
                qualify_zero_write_article,
                qualified_records_as_published_memory,
                routine_session_ordinal,
            )

            canonical_published_memory = list(
                (intelligence.get("published_corpus") or {}).get("articles") or []
            )
            published_memory = list(canonical_published_memory)
            production_before = build_production_day_snapshot(
                reference=now,
                output_root=self._output_root,
                published_corpus=canonical_published_memory,
            )
            quota_discovery_accounting = load_production_day_discovery_accounting(
                self._output_root,
                production_day_id=production_before.newsroom_production_day_id,
            )
            cycle_kwargs["newsroom_production_day_id"] = (
                production_before.newsroom_production_day_id
            )
            if quota_discovery_accounting:
                cycle_kwargs["quota_discovery_prior_accounting"] = (
                    quota_discovery_accounting
                )
            work_budget = (
                bounded_deficit_work_needed(
                    session=str(window.get("session") or ""),
                    qualified_articles_today=production_before.qualified_articles_today,
                )
                if managed_daily_output
                else 1
            )
            if handoff_checkpoint is not None:
                work_budget = max(
                    work_budget,
                    int(handoff_checkpoint.get("work_budget") or 1),
                )
            attempt_results: list[dict[str, Any]] = []
            qualified_records: list[dict[str, Any]] = []
            start_attempt_number = 1
            if handoff_checkpoint is not None:
                attempt_results = [
                    dict(row)
                    for row in handoff_checkpoint.get("prior_attempt_results") or []
                    if isinstance(row, Mapping)
                ]
                qualified_records = [
                    dict(row)
                    for row in handoff_checkpoint.get("qualified_records") or []
                    if isinstance(row, Mapping)
                ]
                published_memory.extend(
                    qualified_records_as_published_memory(
                        qualified_records, reference=now
                    )
                )
                start_attempt_number = int(
                    handoff_checkpoint.get("attempt_number") or 1
                )
                if not 1 <= start_attempt_number <= work_budget:
                    raise ValueError("native_desktop_handoff_attempt_number_invalid")
                if isinstance(
                    handoff_checkpoint.get("native_llm_first_prevalidation"), Mapping
                ):
                    # One external native HIGH worker return owns exactly one article attempt.
                    # A later article needs a new HIGH selection/worker binding, not silent reuse
                    # of this worker inside deficit catch-up work.
                    work_budget = start_attempt_number
            result: dict[str, Any] = {
                "schema_version": "contentops.daily_output_noop.v1",
                "run_id": window_id,
                "classification": "NO_PUBLICATION",
                "exact_next_blocker": "PRODUCTION_DAY_PROGRESS_ALREADY_RESTORED",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
            from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope

            with llm_cycle_budget_scope(window_id, now=now):
                for attempt_number in range(start_attempt_number, work_budget + 1):
                    attempt_run_id = (
                        window_id
                        if attempt_number == 1
                        else f"{window_id}-catchup-{attempt_number:02d}"
                    )
                    attempt_output_dir = (
                        output_dir
                        if attempt_number == 1
                        else output_dir / f"catchup-{attempt_number:02d}"
                    )
                    bound_resume = bool(
                        split_operation == "COMPLETE"
                        and handoff_checkpoint is not None
                        and attempt_number == start_attempt_number
                    )
                    if bound_resume:
                        attempt_run_id = str(
                            handoff_checkpoint.get("attempt_run_id") or attempt_run_id
                        )
                        attempt_output_dir = output_dir / (
                            "split-phase-resume-"
                            f"{int(handoff_checkpoint.get('resume_sequence') or 1):02d}"
                        )
                    attempt_kwargs = {
                        **cycle_kwargs,
                        "run_id": attempt_run_id,
                        "output_dir": attempt_output_dir,
                        "published_corpus": published_memory,
                    }
                    if split_operation is not None and not bound_resume:
                        attempt_kwargs["native_desktop_prepare"] = True
                    if bound_resume and isinstance(
                        (handoff_checkpoint or {}).get("native_llm_first_prevalidation"),
                        Mapping,
                    ):
                        from live_contentops.native_desktop_production_handoff_v1 import (
                            logical_hash,
                            read_json,
                        )

                        intake = read_json(
                            str(handoff_checkpoint.get("intake_checkpoint_path") or "")
                        )
                        if logical_hash(intake) != str(
                            handoff_checkpoint.get("intake_checkpoint_sha256") or ""
                        ):
                            raise ValueError("native_desktop_handoff_intake_binding_invalid")
                        attempt_kwargs.update(
                            {
                                "rolling_input": intake,
                                "prepared_candidate_state": None,
                                "leaf_checkpoints": {},
                                "global_checkpoint": None,
                            }
                        )
                    elif bound_resume:
                        from live_contentops.native_desktop_production_handoff_v1 import (
                            BoundNativeDesktopWorkerReturnBuilder,
                            build_hash_bound_coordinator_reviewer,
                            logical_hash,
                            read_json,
                            validated_viability_checkpoint,
                            write_json,
                        )

                        bindings = dict(
                            handoff_checkpoint.get("semantic_resume_bindings") or {}
                        )
                        if str(bindings.get("semantic_resume_logical_hash") or "") != (
                            logical_hash(
                                {
                                    "leaf_checkpoints": dict(
                                        bindings.get("leaf_checkpoints") or {}
                                    ),
                                    "global_checkpoint": dict(
                                        bindings.get("global_checkpoint") or {}
                                    ),
                                    "story_type_by_cluster": dict(
                                        bindings.get("story_type_by_cluster") or {}
                                    ),
                                }
                            )
                        ):
                            raise ValueError(
                                "native_desktop_handoff_semantic_binding_invalid"
                            )
                        viability = validated_viability_checkpoint(
                            read_json(
                                str(
                                    handoff_checkpoint.get(
                                        "viability_checkpoint_path"
                                    )
                                    or ""
                                )
                            )
                        )
                        revision_contract = dict(
                            handoff_checkpoint.get(
                                "same_xhigh_worker_revision_contract"
                            )
                            or {}
                        )
                        if revision_contract:
                            viability = {
                                **viability,
                                "same_xhigh_worker_revision_contract": revision_contract,
                            }
                            viability.pop("viability_logical_hash", None)
                            viability["viability_logical_hash"] = logical_hash(viability)
                        write_json(
                            attempt_output_dir / "rolling_x_ranked_viability_v1.json",
                            viability,
                        )
                        intake = read_json(
                            str(handoff_checkpoint.get("intake_checkpoint_path") or "")
                        )
                        if logical_hash(intake) != str(
                            handoff_checkpoint.get("intake_checkpoint_sha256") or ""
                        ):
                            raise ValueError("native_desktop_handoff_intake_binding_invalid")
                        attempt_kwargs.update(
                            {
                                "rolling_input": intake,
                                "prepared_candidate_state": None,
                                "leaf_checkpoints": dict(
                                    bindings.get("leaf_checkpoints") or {}
                                ),
                                "global_checkpoint": dict(
                                    bindings.get("global_checkpoint") or {}
                                ),
                                "story_type_by_cluster": dict(
                                    bindings.get("story_type_by_cluster") or {}
                                ),
                                "article_builder": BoundNativeDesktopWorkerReturnBuilder(
                                    worker_return=dict(split_phase_worker_return or {}),
                                    expected_governed_input_hash=str(
                                        handoff_checkpoint.get(
                                            "governed_input_hash"
                                        )
                                        or ""
                                    ),
                                    viability=viability,
                                    same_worker_revision_contract=revision_contract,
                                ),
                                "editorial_reviewer": (
                                    build_hash_bound_coordinator_reviewer(
                                        dict(split_phase_coordinator_review or {})
                                    )
                                ),
                            }
                        )
                    attempt_result = dict(self._newsroom_cycle(**attempt_kwargs))
                    route = dict(attempt_result.get("editorial_worker_routing") or {})
                    pending_reason = str(
                        attempt_result.get("exact_next_blocker") or ""
                    )
                    initial_worker_required = bool(
                        split_operation == "PREPARE"
                        and route.get("decision")
                        == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
                        and pending_reason
                        == "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID"
                    )
                    candidate_continuation_required = bool(
                        split_operation == "COMPLETE"
                        and route.get("decision")
                        == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
                        and pending_reason == "NEXT_NATIVE_XHIGH_WORKER_REQUIRED"
                    )
                    same_worker_revision_required = bool(
                        split_operation == "COMPLETE"
                        and pending_reason == "SAME_XHIGH_WORKER_REVISION_REQUIRED"
                    )
                    unexpected_write_truth = bool(
                        attempt_result.get("public_write_performed") is True
                        or attempt_result.get("unknown_write_detected") is True
                    )
                    if (
                        not unexpected_write_truth
                        and (
                            initial_worker_required
                            or candidate_continuation_required
                            or same_worker_revision_required
                        )
                    ):
                        pending = self._persist_native_desktop_pending_handoff(
                            window=window,
                            attempt_number=attempt_number,
                            attempt_run_id=attempt_run_id,
                            attempt_output_dir=attempt_output_dir,
                            attempt_result=attempt_result,
                            prior_attempt_results=attempt_results,
                            qualified_records=qualified_records,
                            work_budget=work_budget,
                        )
                        return self._native_desktop_pending_handoff_outcome(pending)
                    current_quota_accounting = attempt_result.get(
                        "quota_efficient_source_discovery"
                    )
                    if (
                        isinstance(current_quota_accounting, Mapping)
                        and str(
                            current_quota_accounting.get(
                                "newsroom_production_day_id"
                            )
                            or ""
                        )
                        == production_before.newsroom_production_day_id
                    ):
                        quota_discovery_accounting = dict(current_quota_accounting)
                        cycle_kwargs["quota_discovery_prior_accounting"] = (
                            quota_discovery_accounting
                        )
                    updated_source_route_health = self._persist_source_route_health_state(
                        attempt_result
                    )
                    if updated_source_route_health:
                        source_route_health_state = updated_source_route_health
                        cycle_kwargs["source_route_health"] = source_route_health_state
                    result = attempt_result
                    qualification: dict[str, Any] | None = None
                    if managed_daily_output and (
                        attempt_result.get("classification") == "PASS_PUBLICATION_PLAN_READY"
                        or attempt_result.get("shadow_publication_plan_ready") is True
                    ):
                        qualification = qualify_zero_write_article(
                            result=attempt_result,
                            output_dir=attempt_output_dir,
                            production_day_id=production_before.newsroom_production_day_id,
                            parent_window_id=window_id,
                        )
                        attempt_result["daily_output_qualification"] = qualification
                        if qualification.get("qualified") is True:
                            persist_qualified_article_record(
                                attempt_output_dir, qualification
                            )
                            qualified_records.append(qualification)
                            published_memory.extend(
                                qualified_records_as_published_memory(
                                    [qualification], reference=now
                                )
                            )
                    attempt_results.append(attempt_result)
                    # One cycle already walks the bounded usable candidate universe.  Only a
                    # newly persisted qualified article justifies another distinct attempt.
                    if qualification is None or qualification.get("qualified") is not True:
                        break
            material_priority_finalization = {
                str(row.get("priority_id") or ""): self._finalize_material_event_priority(
                    str(row.get("priority_id") or ""),
                    reason_code="MATERIAL_EVENT_PRIORITY_CONSUMED",
                )
                for row in material_priorities
                if str(row.get("priority_id") or "")
            }
            current_opportunity_ordinal = routine_session_ordinal(
                str(window.get("session") or "")
            )
            used_after = max(
                production_before.routine_opportunities_used,
                current_opportunity_ordinal
                if managed_daily_output
                else production_before.routine_opportunities_used,
            )
            hard_external_reason = None
            exact_reason = str(result.get("exact_next_blocker") or "")
            if exact_reason in {
                "V1_RUNTIME_PREFLIGHT_BLOCKED",
                "PROVIDER_WIDE_FAILURE_AFTER_BOUNDED_FALLBACK",
                "SOURCE_UNIVERSE_UNAVAILABLE",
                "REQUIRED_CREDENTIAL_OR_REAUTH_UNAVAILABLE",
                "RUNTIME_UNAVAILABLE",
            }:
                hard_external_reason = exact_reason
            production_after = build_production_day_snapshot(
                reference=now,
                output_root=self._output_root,
                published_corpus=canonical_published_memory,
                routine_opportunities_used_override=used_after,
                hard_external_block_reason=hard_external_reason,
            )
            persist_production_day_snapshot(output_dir, production_after)
            result = dict(result)
            result["production_day"] = production_after.to_dict()
            result["production_day_attempts"] = attempt_results
            result["production_day_work_budget"] = work_budget
            result["production_day_deficit_before"] = (
                production_before.remaining_build_deficit
            )
            result["production_day_deficit_after"] = (
                production_after.remaining_build_deficit
            )
            classification = str(result.get("classification") or "")
            viable = (
                bool(qualified_records)
                if managed_daily_output
                else classification not in {"NO_PUBLICATION", "BLOCKED", ""}
            )
            novelty_decision = self._record_editorial_novelty_decision(
                output_dir=output_dir,
                cycle_evidence=result,
                portfolio_context=portfolio_context,
            )
            # The canonical newsroom cycle may run much longer than the initial lease TTL.
            # Re-acquire a fresh active lease before recording the terminal transition so the
            # fencing token remains valid. If another owner legitimately took over while we were
            # executing, we must not record a competing terminal state.
            try:
                renewed = self._store.acquire_lease(
                    lease_key=lease_key,
                    owner_ref=self._owner_ref,
                    ttl_seconds=self._lease_ttl_seconds,
                    work_item_id=window_id,
                )
            except LeaseConflictError:
                return {
                    "executed": True,
                    "classification": classification,
                    "viable": viable,
                    "public_write_performed": bool(result.get("public_write_performed")),
                    "unknown_write_detected": bool(result.get("unknown_write_detected")),
                    "terminal_state": self._window_state(window_id),
                    "reason": "lease_taken_over_during_execution",
                }
            lease_id = str(renewed["lease_id"])
            fencing = int(renewed["fencing_token"])
            lease_key = str(renewed["lease_key"])
            lifecycle: Optional[Dict[str, Any]] = None
            if viable:
                self._transition(
                    window_id=window_id,
                    to_state="EVIDENCE_READY",
                    lease_key=lease_key,
                    fencing_token=fencing,
                    reason_code="EDITORIAL_WINDOW_VIABLE",
                    explanation=f"Window {window_id} produced a viable story",
                )
                if publication_enabled:
                    lifecycle = self._maybe_drive_publication_lifecycle(window_id, result)
            else:
                self._transition(
                    window_id=window_id,
                    to_state="EVIDENCE_BLOCKED",
                    lease_key=lease_key,
                    fencing_token=fencing,
                    reason_code="EDITORIAL_WINDOW_NO_PUBLICATION",
                    explanation=f"Window {window_id} ended without a publishable story",
                )
                self._transition(
                    window_id=window_id,
                    to_state="REJECTED",
                    lease_key=lease_key,
                    fencing_token=fencing,
                    reason_code="EDITORIAL_WINDOW_NO_PUBLICATION",
                    explanation=f"Window {window_id} rejected (no publishable story)",
                )
            public_write = bool(result.get("public_write_performed"))
            unknown_write = bool(result.get("unknown_write_detected"))
            if lifecycle:
                public_write = public_write or bool(lifecycle.get("public_write_performed"))
                unknown_write = unknown_write or bool(lifecycle.get("unknown_write_detected"))
            post_publication_performance = None
            if lifecycle and self._enable_performance_observation:
                # The same opportunity schedules the newly reconciled objects before its
                # terminal report; later checkpoints remain ordinary due observations.
                post_publication_performance = self._run_performance_observations(now)
            try:
                from live_contentops.published_corpus_read_model_v1 import load_published_corpus

                after_corpus = load_published_corpus(
                    self._store, output_root=self._output_root
                )
            except Exception as exc:  # noqa: BLE001
                after_corpus = dict(intelligence.get("published_corpus") or {})
                after_corpus["published_corpus_error"] = type(exc).__name__
            memory_proof = self._record_published_memory_cycle_proof(
                output_dir=output_dir,
                window=window,
                before_runtime=intelligence,
                after_corpus=after_corpus,
                cycle_evidence=result,
                portfolio_context=portfolio_context,
                novelty_decision=novelty_decision,
                lifecycle=lifecycle,
            )
            try:
                from live_contentops.runtime_activity_projection_v1 import RuntimeActivityRecorderV1

                RuntimeActivityRecorderV1(
                    output_dir=output_dir, work_item_id=window_id
                ).finish(
                    terminal_result=self._window_state(window_id) or classification,
                    exact_reason=result.get("exact_next_blocker"),
                )
            except (OSError, TypeError, ValueError):
                # Presentation telemetry is deliberately non-authoritative and best-effort.
                pass
            outcome = {
                "executed": True,
                "classification": classification,
                "viable": viable,
                "public_write_performed": public_write,
                "unknown_write_detected": unknown_write,
                "publication_lifecycle": lifecycle,
                "material_event_priority": material_priority,
                "material_event_priority_finalization": material_priority_finalization,
                "post_publication_performance": post_publication_performance,
                "published_memory_cycle_proof": memory_proof,
                "editorial_novelty_decision": novelty_decision,
                "terminal_state": self._window_state(window_id),
            }
            if split_operation is not None:
                from live_contentops.native_desktop_production_handoff_v1 import (
                    logical_hash,
                    write_json,
                )

                completion = {
                    "schema_version": (
                        "contentops.native_desktop_editorial_handoff_completion.v1"
                    ),
                    "canonical_opportunity_id": str(window_id),
                    "runtime_run_id": str(window_id),
                    "automation_id": str(
                        window.get("native_desktop_automation_id") or ""
                    ),
                    "terminal_state": outcome["terminal_state"],
                    "classification": classification,
                    "prior_handoff_logical_hash": (
                        (handoff_checkpoint or {}).get("handoff_logical_hash")
                    ),
                    "public_write_authority": "ZERO",
                    "public_write_performed": public_write,
                    "unknown_write_detected": unknown_write,
                    "publication_authority_granted": False,
                }
                completion["completion_logical_hash"] = logical_hash(completion)
                completion_path = (
                    output_dir
                    / "native_desktop_editorial_handoff_completion_v1.json"
                )
                write_json(completion_path, completion)
                outcome["handoff_completion_receipt_path"] = str(completion_path)
                outcome["handoff_completion_logical_hash"] = completion[
                    "completion_logical_hash"
                ]
            return outcome
        finally:
            try:
                self._store.release_lease(lease_id, self._owner_ref, fencing)
            except Exception:  # noqa: BLE001
                pass

    # -- wake computation -----------------------------------------------------

    def _next_wake(self, now: datetime) -> datetime:
        """Deterministic next wake combining the edited editorial window (with bounded learned
        timing offset) and the next due read-only performance observation."""
        candidates: list[datetime] = []
        timing_offset = timedelta(minutes=self._timing_policy_offset_minutes())
        for day_offset in range(0, 3):
            day = now + timedelta(days=day_offset)
            for core in self._policy.core_windows:
                if day.weekday() not in set(core.eligible_weekdays_utc):
                    continue
                start, _end = self._window_for_day(core, day)
                start = start + timing_offset
                if start > now:
                    candidates.append(start)
        # Combine editorial wake with the next due performance observation (read-only; zero LLM).
        observation_wake = self._next_observation_wake(now)
        if observation_wake is not None:
            candidates.append(observation_wake)
        recovery_wake = self._next_recovery_wake(now)
        if recovery_wake is not None:
            candidates.append(recovery_wake)
        # Also wake a little before the next window to be responsive, and cap the sleep.
        if candidates:
            return min(candidates)
        return now + timedelta(hours=1)
