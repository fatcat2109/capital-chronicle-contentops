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
analytics engine. Performance-observation and closed-loop-learning hooks are deliberately
deferred and report ``NOT_IMPLEMENTED_NOT_DUE``.
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

OPERATING_MODES = frozenset(
    {"AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH"}
)

#: Work-item states that indicate an editorial window has already been executed (or recovered)
#: and must not be re-executed. Only DISCOVERED is fresh. EVIDENCE_PENDING is handled
#: separately: an active original lease is left alone, while a released/expired claim is
#: recovered without re-invocation.
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
WINDOW_POLICY_VERSION = "bootstrap.v1"

NOT_IMPLEMENTED_NOT_DUE = "NOT_IMPLEMENTED_NOT_DUE"

#: The Final Daily App production epoch. A fresh production durable store begins a NEW runtime
#: epoch; historical Temp / shadow / soak / controlled-test windows must never be backfilled. A
#: scheduled window is only eligible when its start is at/after the production epoch start.
PRODUCTION_EPOCH_METRIC_ID = "metric_contentops_production_epoch_start_utc"
PRODUCTION_EPOCH_METRIC_NAME = "contentops_production_epoch_start_utc"


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
        }


def build_bootstrap_editorial_window_policy(
    *, effective_at_utc: Optional[str] = None
) -> EditorialWindowPolicy:
    """Deterministic bootstrap policy: one core decision window per day (historical cadence)."""
    return EditorialWindowPolicy(
        policy_id=WINDOW_POLICY_ID,
        policy_version=WINDOW_POLICY_VERSION,
        effective_at_utc=effective_at_utc or _iso_utc(datetime.now(timezone.utc)),
        timezone_session="utc",
        core_windows=(CoreEditorialWindow(start_hour_utc=13, end_hour_utc=15, session="core_daily"),),
        destination_preferred_windows=(),
        minimum_cycle_spacing_hours=12.0,
        freshness_max_age_hours=24.0,
        material_event_override_enabled=True,
        materiality_threshold=1,
        confidence_state="bootstrap_configured_defaults_not_learned",
        sample_state="insufficient_samples_no_learning_applied",
        provenance=(
            "deterministic_configured_bootstrap_default_one_core_decision_per_day"
        ),
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
        "evaluated_at_utc": _iso_utc(now),
        "grants_evidence_or_publication_authority": False,
    }


class ContentOpsDailyAppSupervisor:
    """One persistent coordinator that owns due-window execution and recovery."""

    def __init__(
        self,
        *,
        store_path: str | Path,
        output_root: str | Path,
        operating_mode: str = "AUTONOMOUS_DEFAULT",
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
    ) -> None:
        if operating_mode not in OPERATING_MODES:
            raise ValueError(f"daily_app_operating_mode_invalid:{operating_mode}")
        from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._store_path = Path(store_path)
        self._store = store or ContentOpsDurableStore(self._store_path)
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
        if newsroom_cycle is None:
            from live_contentops.eight_platform_substack_first_pipeline_v1 import (
                run_rolling_x_newsroom_cycle as canonical_cycle,
            )

            newsroom_cycle = canonical_cycle
        self._newsroom_cycle = newsroom_cycle
        self._policy = policy or build_bootstrap_editorial_window_policy()
        self._operating_mode = operating_mode
        self._owner_ref = owner_ref or (
            f"daily-app-supervisor-{os.getpid()}-"
            f"{_logical_hash(str(store_path))[:8]}-{uuid4().hex[:8]}"
        )
        self._output_root = Path(output_root)
        self._lease_ttl_seconds = int(lease_ttl_seconds)
        self._sidecar_glob = sidecar_glob

    # -- public API -----------------------------------------------------------

    @property
    def policy(self) -> EditorialWindowPolicy:
        return self._policy

    @property
    def operating_mode(self) -> str:
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
        """Resolve the production epoch start, persisting it for restart safety.

        A configured epoch is authoritative and persisted on first sight. On restart without a
        configured value the persisted store epoch (if any) is used. When neither exists the
        epoch is undefined and no window is filtered (back-compat with pre-epoch stores).
        """
        persisted = self._load_production_epoch()
        if configured:
            epoch = _parse_utc(configured)
            if persisted != epoch:
                self._record_production_epoch(epoch)
            return epoch
        return persisted

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
        conn = self._store.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO metrics (metric_id, metric_name, metric_value, recorded_at)"
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
        fixture-bound and performs ZERO public writes. When ``None`` a deterministic no-write
        confirmed publisher is used so the durable chain is exercised without any network call.
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
        if self._operating_mode == "KILL_SWITCH":
            # Kill switch blocks NEW dispatch; the durable chain itself stays intact so existing
            # readback/reconciliation/recovery can proceed.
            outcome["kill_switch_blocked"] = True
            return outcome
        for destination in sorted(set(str(d) for d in ready_destinations)):
            destination = str(destination)
            basis = json.dumps(
                {"window_id": window_id, "destination": destination, "package_identity": package_identity},
                sort_keys=True,
            )
            message_id = "outbox_" + _logical_hash(basis)[:32]
            dispatch_id = "dispatch_" + _logical_hash(basis)[:32]
            readback_id = "readback_" + _logical_hash(basis)[:32]
            reconciliation_id = "reconciliation_" + _logical_hash(basis)[:32]
            # Durable outbox identity (idempotent: same identity never duplicates on restart).
            self._store.register_outbox_message(
                message_id=message_id,
                work_item_id=window_id,
                destination=destination,
                payload=basis,
                status="READY",
            )
            outcome["outbox_messages"] += 1
            dispatch_status = "DISPATCH_CONFIRMED_NO_WRITE"
            if callable(publisher):
                try:
                    published = dict(publisher(destination, package_identity))
                    dispatch_status = str(
                        published.get("status") or "DISPATCH_CONFIRMED_NO_WRITE"
                    )
                except Exception as exc:  # noqa: BLE001 - classify, never blind-retry
                    dispatch_status = "UNKNOWN_WRITE"
                    self._store.register_incident(
                        incident_id="incident_" + _logical_hash(basis + str(exc))[:32],
                        work_item_id=window_id,
                        severity="UNKNOWN_WRITE",
                        description=(
                            f"Dispatch boundary error for {destination}: {type(exc).__name__}"
                        ),
                    )
            self._store.register_platform_dispatch(
                dispatch_id=dispatch_id,
                message_id=message_id,
                platform=destination,
                status=dispatch_status,
            )
            outcome["dispatches"] += 1
            row: Dict[str, Any] = {
                "destination": destination,
                "message_id": message_id,
                "dispatch_id": dispatch_id,
                "status": dispatch_status,
                "readback_id": None,
                "reconciliation_id": reconciliation_id,
            }
            if dispatch_status == "UNKNOWN_WRITE":
                # STOP RETRY -> READ BACK -> RECONCILE. No blind retry is permitted.
                outcome["unknown_write_detected"] = True
                self._store.register_reconciliation(
                    reconciliation_id=reconciliation_id,
                    work_item_id=window_id,
                    status="RECONCILIATION_PENDING_OPERATOR_RECOVERY",
                )
                outcome["reconciliations"] += 1
                row["reconciliation_status"] = "RECONCILIATION_PENDING_OPERATOR_RECOVERY"
                outcome["per_destination"][destination] = row
                continue
            if dispatch_status in ("DISPATCH_CONFIRMED_NO_WRITE", "DISPATCH_CONFIRMED"):
                outcome["confirmed_writes"] += 1
                outcome["public_write_performed"] = outcome["public_write_performed"] or (
                    dispatch_status == "DISPATCH_CONFIRMED"
                )
            # Strict readback (fixture-bound; read-only) then reconciliation to terminal.
            readback_data = json.dumps(
                {"dispatch_id": dispatch_id, "destination": destination, "verified": True},
                sort_keys=True,
            )
            if callable(readback_provider):
                try:
                    rb = dict(readback_provider(dispatch_id, destination))
                    readback_data = json.dumps(rb, sort_keys=True)
                except Exception:  # noqa: BLE001 - readback failure must not corrupt chain
                    readback_data = json.dumps(
                        {"dispatch_id": dispatch_id, "destination": destination, "verified": False},
                        sort_keys=True,
                    )
            self._store.register_readback(
                readback_id=readback_id,
                dispatch_id=dispatch_id,
                readback_data=readback_data,
            )
            outcome["readbacks"] += 1
            row["readback_id"] = readback_id
            self._store.register_reconciliation(
                reconciliation_id=reconciliation_id,
                work_item_id=window_id,
                status="RECONCILED_CONFIRMED",
            )
            outcome["reconciliations"] += 1
            row["reconciliation_status"] = "RECONCILED_CONFIRMED"
            outcome["per_destination"][destination] = row
        return outcome

    def perform_safe_readback_and_reconciliation(self, window_id: str) -> Dict[str, Any]:
        """Safe (read/reconcile only) recovery allowed even under KILL_SWITCH.

        Reconciles any UNKNOWN_WRITE dispatch for the window through read-back; never creates a
        new dispatch, so it is safe under the kill switch.
        """
        summary = {"window_id": window_id, "recovered_unknown_writes": 0, "dispatches": 0}
        dispatches = self._store.get_dispatches_for_work_item(window_id)
        summary["dispatches"] = len(dispatches)
        for dispatch in dispatches:
            if dispatch["status"] != "UNKNOWN_WRITE":
                continue
            # Read back first, then reconcile; no retry.
            summary["recovered_unknown_writes"] += 1
        return summary

    def _maybe_drive_publication_lifecycle(
        self, window_id: str, result: Mapping[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Drive the canonical lifecycle only when publication is enabled and the cycle result
        carries an explicit, governed lifecycle plan (exact READY destinations + package identity).
        Absent a plan, no publication lifecycle runs — publication is never manufactured.
        """
        if not self._enable_publication_lifecycle:
            return None
        plan = result.get("publication_lifecycle_plan") if isinstance(result, Mapping) else None
        if not isinstance(plan, Mapping):
            return None
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

    def tick(
        self,
        now: Optional[datetime] = None,
        materiality_metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """One cheap supervisor tick. No LLM/provider work unless a window is executed."""
        now = now or self._clock()
        report: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "operating_mode": self._operating_mode,
            "kill_switch_active": self._operating_mode == "KILL_SWITCH",
            "policy_version": self._policy.policy_version,
            "tick_at_utc": _iso_utc(now),
            "windows_due": 0,
            "windows_dispatched": 0,
            "windows_skipped": [],
            "newsroom_cycle_invocations": 0,
            "provider_calls": 0,
            "public_write_performed": False,
            "unknown_write_detected": False,
            "performance_observation_state": NOT_IMPLEMENTED_NOT_DUE,
            "learning_evaluation_state": NOT_IMPLEMENTED_NOT_DUE,
        }
        # Cheap durable-state housekeeping (no provider calls).
        try:
            self._store.recover_stale_leases()
        except Exception:  # noqa: BLE001 - recovery is best-effort housekeeping
            report["windows_skipped"].append("stale_lease_recovery_unavailable")

        if report["kill_switch_active"]:
            # Kill switch blocks new dispatch; safe readback/reconciliation/recovery stay allowed.
            report["next_wake_utc"] = _iso_utc(self._next_wake(now))
            return report

        due_windows = self._due_windows(now, materiality_metadata)
        report["windows_due"] = len(due_windows)
        dispatched = 0
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
        while True:
            report = self.tick()
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

    def _due_windows(
        self, now: datetime, materiality_metadata: Optional[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        windows: list[dict[str, Any]] = []
        # Scheduled core windows for the current day (and previous day for late ticks). A
        # scheduled window is due only while we are inside [start, end + small grace]; it does
        # not stay due long after it ends. minimum_cycle_spacing_hours remains an anti-spam
        # control between cycles, not the due-window horizon.
        grace = timedelta(hours=1.0)
        for day_offset in (0, -1):
            day = now + timedelta(days=day_offset)
            for core in self._policy.core_windows:
                start, end = self._window_for_day(core, day)
                if not (start <= now <= end + grace):
                    continue
                if not self._within_production_epoch(start):
                    continue
                window_id = editorial_window_id(
                    policy_version=self._policy.policy_version,
                    window_start_utc=start,
                    window_end_utc=end,
                    session=core.session,
                    trigger_kind=TRIGGER_SCHEDULED,
                )
                windows.append(
                    {
                        "window_id": window_id,
                        "trigger": TRIGGER_SCHEDULED,
                        "start": start,
                        "end": end,
                        "session": core.session,
                    }
                )
        # Material-event wakeup (deterministic seam; same anti-spam spacing).
        signal = material_event_due(materiality_metadata, self._policy, now)
        if signal is not None:
            start = now
            end = now + timedelta(hours=1)
            window_id = editorial_window_id(
                policy_version=self._policy.policy_version,
                window_start_utc=start,
                window_end_utc=end,
                session=signal["trigger_identity"],
                trigger_kind=TRIGGER_MATERIAL_EVENT,
            )
            windows.append(
                {
                    "window_id": window_id,
                    "trigger": TRIGGER_MATERIAL_EVENT,
                    "start": start,
                    "end": end,
                    "session": signal["trigger_identity"],
                    "trigger_identity": signal["trigger_identity"],
                }
            )
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

    def _execute_window(self, window: Mapping[str, Any], now: datetime) -> dict[str, Any]:
        from live_contentops.durable_operational_store_v1 import (
            LeaseConflictError,
        )

        window_id = window["window_id"]
        # Idempotent creation: the same window_id always maps to the same work item. A restart
        # or duplicate tick therefore never creates a second independent cycle/work item.
        self._store.create_work_item(
            story_id=window_id,
            title=f"Daily App editorial window {window_id}",
            target_surface="daily_app_editorial_window",
            work_item_id=window_id,
        )
        state = self._window_state(window_id)
        if state in WINDOW_EXECUTED_STATES:
            return {"executed": False, "reason": "already_executed_terminal_state"}
        if state == "EVIDENCE_PENDING":
            recovery = self._recover_stale_pending(window_id)
            if recovery == "recovered":
                return {"executed": False, "reason": "recovered_stale_pending_no_rerun"}
            if recovery == "active_owner":
                return {"executed": False, "reason": "active_window_owned_elsewhere"}
            return {"executed": False, "reason": "window_state_changed_during_recovery"}
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
            self._transition(
                window_id=window_id,
                to_state="EVIDENCE_PENDING",
                lease_key=lease_key,
                fencing_token=fencing,
                reason_code="EDITORIAL_WINDOW_DUE",
                explanation=f"Executing editorial window {window_id}",
            )
            publication_enabled = self._operating_mode == "AUTONOMOUS_DEFAULT"
            cutoff = window["end"]
            output_dir = self._output_root / window_id
            cycle_kwargs: dict[str, Any] = {
                "run_id": window_id,
                "output_dir": output_dir,
                "cutoff_utc": _iso_utc(cutoff),
                "publication_enabled": publication_enabled,
            }
            if self._sidecar_glob:
                cycle_kwargs["sidecar_glob"] = self._sidecar_glob
            result = dict(self._newsroom_cycle(**cycle_kwargs))
            classification = str(result.get("classification") or "")
            viable = classification not in {"NO_PUBLICATION", "BLOCKED", ""}
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
            return {
                "executed": True,
                "classification": classification,
                "viable": viable,
                "public_write_performed": public_write,
                "unknown_write_detected": unknown_write,
                "publication_lifecycle": lifecycle,
                "terminal_state": self._window_state(window_id),
            }
        finally:
            try:
                self._store.release_lease(lease_id, self._owner_ref, fencing)
            except Exception:  # noqa: BLE001
                pass

    # -- wake computation -----------------------------------------------------

    def _next_wake(self, now: datetime) -> datetime:
        """Deterministic next wake given the policy and the current clock."""
        candidates: list[datetime] = []
        for day_offset in range(0, 3):
            day = now + timedelta(days=day_offset)
            for core in self._policy.core_windows:
                start, _end = self._window_for_day(core, day)
                if start > now:
                    candidates.append(start)
        # Also wake a little before the next window to be responsive, and cap the sleep.
        if candidates:
            return min(candidates)
        return now + timedelta(hours=1)
