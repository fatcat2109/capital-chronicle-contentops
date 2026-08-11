"""Continuous cheap X headline ingestion lane for the Final Daily App supervisor.

Owner decision 2026-08-10 (V1 realignment): headline ingestion is continuous/cheap while the
Daily App host is available. It is a housekeeping lane INSIDE the canonical supervisor tick:
no second scheduler authority, no second Daily App, no second production DB, and ZERO
LLM/provider calls. Editorial windows do not own headline ingestion; Run Now does not own
headline ingestion. The lane keeps the canonical single-folder per-day sidecar store current
so every editorial decision can reconstruct the complete rolling 24-hour headline universe.

Cadence policy (versioned configuration, not universal truth):

- active interval ~4 minutes while fresh rows keep appearing (freshness-lag target <= ~5 min);
- adaptive idle backoff (x2, capped) when captures keep adding nothing new;
- one bounded capture per due iteration; no parallel captures (single-flight per supervisor);
- immediate safe retry after transient failure on the next due iteration;
- REAUTH_REQUIRED is reported when the exact locked X session expires; the lane never
  automates login and never substitutes another profile.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Optional

LANE_SCHEMA_VERSION = "contentops.continuous_headline_ingest.v2"

ACTIVE_INTERVAL_SECONDS = 240.0
IDLE_BACKOFF_MULTIPLIER = 2.0
MAX_INTERVAL_SECONDS = 300.0
CAPTURE_MAX_SECONDS = 60.0
CAPTURE_MAX_EMPTY_SCROLLS = 1
STALE_SYNC_THRESHOLD_SECONDS = 300.0

METRIC_LAST_SUCCESS_EPOCH = "metric_headline_ingest_last_success_epoch"
METRIC_LAST_OUTCOME_CODE = "metric_headline_ingest_last_outcome_code"
METRIC_CONSECUTIVE_EMPTY = "metric_headline_ingest_consecutive_empty"
METRIC_ROWS_LAST_ITERATION = "metric_headline_ingest_rows_last_iteration"

OUTCOME_CAPTURED_NEW = 0.0
OUTCOME_CAPTURED_NONE = 1.0
OUTCOME_REAUTH_REQUIRED = 2.0
OUTCOME_CDP_UNAVAILABLE = 3.0
OUTCOME_CAPTURE_FAILED = 4.0
OUTCOME_BROWSER_BINDING_MISSING = 5.0
OUTCOME_PORT_OWNER_UNPROVEN = 6.0
OUTCOME_NOT_DUE = 7.0

LANE_STATE_RUNNING = "RUNNING"
LANE_STATE_READY = "READY"
LANE_STATE_REAUTH_REQUIRED = "REAUTH_REQUIRED"
LANE_STATE_DEGRADED = "DEGRADED"
LANE_STATE_UNAVAILABLE = "UNAVAILABLE"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _epoch(value: datetime) -> float:
    return value.timestamp()


def read_ingestion_checkpoint(store: Any) -> dict[str, Any]:
    """Read the durable ingestion checkpoint (metrics table; no second state store)."""
    with store.get_connection() as conn:
        rows = {
            str(row["metric_id"]): float(row["metric_value"])
            for row in conn.execute(
                "SELECT metric_id, metric_value FROM metrics WHERE metric_id IN (?,?,?,?)",
                (
                    METRIC_LAST_SUCCESS_EPOCH,
                    METRIC_LAST_OUTCOME_CODE,
                    METRIC_CONSECUTIVE_EMPTY,
                    METRIC_ROWS_LAST_ITERATION,
                ),
            ).fetchall()
        }
    return {
        "last_success_epoch": rows.get(METRIC_LAST_SUCCESS_EPOCH),
        "last_outcome_code": rows.get(METRIC_LAST_OUTCOME_CODE),
        "consecutive_empty": int(rows.get(METRIC_CONSECUTIVE_EMPTY) or 0),
        "rows_last_iteration": int(rows.get(METRIC_ROWS_LAST_ITERATION) or 0),
    }


def write_ingestion_checkpoint(
    store: Any,
    *,
    now: datetime,
    last_success_epoch: Optional[float],
    outcome_code: float,
    consecutive_empty: int,
    rows_iteration: int,
) -> None:
    iso_now = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    with store.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                (METRIC_LAST_OUTCOME_CODE, "headline_ingest_last_outcome_code", float(outcome_code), iso_now),
            )
            conn.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                (METRIC_CONSECUTIVE_EMPTY, "headline_ingest_consecutive_empty", float(int(consecutive_empty)), iso_now),
            )
            conn.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                (METRIC_ROWS_LAST_ITERATION, "headline_ingest_rows_last_iteration", float(int(rows_iteration)), iso_now),
            )
            if last_success_epoch is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                    (METRIC_LAST_SUCCESS_EPOCH, "headline_ingest_last_success_epoch", float(last_success_epoch), iso_now),
                )
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise


def next_due_interval_seconds(consecutive_empty: int) -> float:
    interval = ACTIVE_INTERVAL_SECONDS * (IDLE_BACKOFF_MULTIPLIER ** max(0, int(consecutive_empty)))
    return min(interval, MAX_INTERVAL_SECONDS)


def ingestion_lane_state(outcome_code: Optional[float], cdp_alive: bool = True) -> str:
    if outcome_code == OUTCOME_REAUTH_REQUIRED:
        return LANE_STATE_REAUTH_REQUIRED
    if outcome_code in {OUTCOME_BROWSER_BINDING_MISSING, OUTCOME_PORT_OWNER_UNPROVEN}:
        return LANE_STATE_UNAVAILABLE
    if outcome_code in {OUTCOME_CDP_UNAVAILABLE, OUTCOME_CAPTURE_FAILED}:
        return LANE_STATE_DEGRADED
    if outcome_code in {OUTCOME_CAPTURED_NEW, OUTCOME_CAPTURED_NONE}:
        return LANE_STATE_RUNNING
    return LANE_STATE_DEGRADED


def run_ingestion_housekeeping_iteration(
    store: Any,
    *,
    now: Optional[datetime] = None,
    force: bool = False,
    state_fn: Optional[Callable[..., Mapping[str, Any]]] = None,
    ensure_fn: Optional[Callable[..., Mapping[str, Any]]] = None,
    session_fn: Optional[Callable[..., Mapping[str, Any]]] = None,
    capture_fn: Optional[Callable[..., Mapping[str, Any]]] = None,
) -> dict[str, Any]:
    """One cheap single-flight intake iteration. Zero LLM/provider calls. Never kills, clones,
    resets, or substitutes the locked CapitalChronicleBot profile; missing/unproven bindings
    fail closed."""
    moment = (now or _utc_now()).astimezone(timezone.utc)
    checkpoint = read_ingestion_checkpoint(store)
    result: dict[str, Any] = {
        "schema_version": LANE_SCHEMA_VERSION,
        "iteration_at_utc": moment.isoformat().replace("+00:00", "Z"),
        "lane_state": None,
        "due": False,
        "forced": bool(force),
        "capture_attempted": False,
        "rows_added": 0,
        "detail": None,
        "llm_or_provider_calls": 0,
        "cadence_policy": {
            "active_interval_seconds": ACTIVE_INTERVAL_SECONDS,
            "idle_max_interval_seconds": MAX_INTERVAL_SECONDS,
            "freshness_lag_target_seconds": 300.0,
        },
        "material_event_due": False,
        "new_material_event_count": 0,
        "new_material_event_identity": None,
        "new_headline_ids": [],
        "new_headline_source_refs": [],
    }

    def _finish(
        outcome_code: float,
        *,
        last_success: Optional[float] = None,
        rows: int = 0,
        consecutive_empty: Optional[int] = None,
    ) -> dict[str, Any]:
        empty_count = checkpoint["consecutive_empty"] if consecutive_empty is None else consecutive_empty
        try:
            write_ingestion_checkpoint(
                store,
                now=moment,
                last_success_epoch=last_success if last_success is not None else checkpoint["last_success_epoch"],
                outcome_code=outcome_code,
                consecutive_empty=empty_count,
                rows_iteration=rows,
            )
        except Exception as exc:  # noqa: BLE001 - checkpoint persistence is best-effort
            result["detail"] = f"checkpoint_write_failed:{type(exc).__name__}"
        result["lane_state"] = ingestion_lane_state(outcome_code)
        return result

    if not force:
        last_success = checkpoint["last_success_epoch"]
        elapsed = (_epoch(moment) - float(last_success)) if last_success is not None else None
        if checkpoint["last_outcome_code"] == OUTCOME_REAUTH_REQUIRED and (
            elapsed is None or elapsed < MAX_INTERVAL_SECONDS
        ):
            result["lane_state"] = LANE_STATE_REAUTH_REQUIRED
            result["detail"] = "reauth_required_waiting_for_operator"
            return result
        if elapsed is not None and elapsed < next_due_interval_seconds(checkpoint["consecutive_empty"]):
            result["lane_state"] = ingestion_lane_state(checkpoint["last_outcome_code"])
            result["detail"] = "not_due"
            return result
    result["due"] = True

    if state_fn is not None:
        process_state = dict(state_fn())
    else:
        from live_contentops.ingestion_bootstrap_v1 import ingestion_process_state

        process_state = dict(ingestion_process_state())
    state_name = str(process_state.get("state") or "")

    if state_name not in {"READY"}:
        from live_contentops.ingestion_bootstrap_v1 import (
            STATE_PORT_OWNER_UNPROVEN,
            STATE_PROFILE_BINDING_MISSING,
            STATE_RUNNING_WITHOUT_CDP,
        )

        if state_name == STATE_PROFILE_BINDING_MISSING:
            result["detail"] = "PROFILE_BINDING_MISSING_FAIL_CLOSED"
            return _finish(OUTCOME_BROWSER_BINDING_MISSING, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if state_name == STATE_PORT_OWNER_UNPROVEN:
            result["detail"] = "PORT_OWNER_UNPROVEN_FAIL_CLOSED"
            return _finish(OUTCOME_PORT_OWNER_UNPROVEN, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if state_name == STATE_RUNNING_WITHOUT_CDP:
            result["detail"] = "CANONICAL_PROFILE_RUNNING_WITHOUT_CDP"
            return _finish(OUTCOME_CDP_UNAVAILABLE, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if ensure_fn is not None:
            ensured = dict(ensure_fn())
        else:
            from live_contentops.ingestion_bootstrap_v1 import canonical_ingestion_readiness

            ensured = dict(canonical_ingestion_readiness(session_timeout_seconds=8.0))
        ensured_state = str(ensured.get("chrome_9222_ingestion") or "")
        if ensured_state == "REAUTH_REQUIRED":
            result["detail"] = "LOGIN_REDIRECT_OBSERVED"
            return _finish(OUTCOME_REAUTH_REQUIRED, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if ensured_state not in {"READY", "READY_AUTH_UNVERIFIED"}:
            result["detail"] = f"CDP_UNAVAILABLE:{ensured_state}"
            return _finish(OUTCOME_CDP_UNAVAILABLE, consecutive_empty=checkpoint["consecutive_empty"] + 1)

    if session_fn is not None:
        session_state = dict(session_fn())
    else:
        from live_contentops.x_list_ingest_capture_v1 import probe_session_visible_state

        session_state = dict(probe_session_visible_state(timeout_seconds=10.0))
    if session_state.get("session_state") == "REAUTH_REQUIRED":
        result["detail"] = "LOGIN_REDIRECT_OBSERVED"
        return _finish(OUTCOME_REAUTH_REQUIRED, consecutive_empty=checkpoint["consecutive_empty"] + 1)

    if capture_fn is not None:
        capture = dict(capture_fn(max_seconds=CAPTURE_MAX_SECONDS, max_empty_scrolls=CAPTURE_MAX_EMPTY_SCROLLS))
    else:
        from live_contentops.x_list_ingest_capture_v1 import run_bounded_x_list_capture

        capture = dict(
            run_bounded_x_list_capture(
                max_seconds=CAPTURE_MAX_SECONDS, max_empty_scrolls=CAPTURE_MAX_EMPTY_SCROLLS
            )
        )
    result["capture_attempted"] = True
    capture_state = str(capture.get("capture_state") or "CAPTURE_FAILED")
    rows_added = int(capture.get("new_headlines") or 0)
    result["rows_added"] = rows_added
    result["new_headline_ids"] = sorted({
        str(value) for value in (capture.get("new_headline_ids") or []) if str(value)
    })
    result["new_headline_source_refs"] = [
        dict(value) for value in (capture.get("new_headline_source_refs") or [])
        if isinstance(value, Mapping)
    ]
    if capture_state == "REAUTH_REQUIRED":
        result["detail"] = "LOGIN_REDIRECT_OBSERVED"
        return _finish(OUTCOME_REAUTH_REQUIRED, rows=rows_added, consecutive_empty=checkpoint["consecutive_empty"] + 1)
    if capture_state not in {"CAPTURED", "CAPTURED_NO_NEW_HEADLINES"}:
        result["detail"] = f"CAPTURE_FAILED:{capture_state}"
        return _finish(OUTCOME_CAPTURE_FAILED, rows=rows_added, consecutive_empty=checkpoint["consecutive_empty"] + 1)
    if rows_added > 0:
        valid_source_refs: list[dict[str, Any]] = []
        for ref in result["new_headline_source_refs"]:
            try:
                source_time = datetime.fromisoformat(
                    str(ref.get("headline_timestamp") or "").replace("Z", "+00:00")
                )
                if source_time.tzinfo is None:
                    source_time = source_time.replace(tzinfo=timezone.utc)
                source_time = source_time.astimezone(timezone.utc)
            except (TypeError, ValueError):
                continue
            if moment - timedelta(hours=24) <= source_time <= moment:
                valid_source_refs.append(ref)
        valid_ids = sorted({
            str(ref.get("headline_id") or "") for ref in valid_source_refs
            if str(ref.get("headline_id") or "")
        })
        if not result["new_headline_source_refs"]:
            # Compatibility capture fixtures may expose already-governed IDs without source
            # refs. Real capture always carries timestamp-bound refs.
            valid_ids = list(result["new_headline_ids"])
        identity_material = {
            "headline_ids": valid_ids,
            "source_refs": valid_source_refs,
            "capture_identity": capture.get("new_headline_identity"),
        }
        # Real capture always supplies ID-bound rows. The fallback remains bounded and is used
        # only by compatible injected capture fixtures.
        if (
            not identity_material["headline_ids"]
            and not identity_material["source_refs"]
            and not result["new_headline_source_refs"]
        ):
            identity_material["compatibility_capture"] = {
                "iteration_at_utc": result["iteration_at_utc"],
                "rows_added": rows_added,
            }
        event_identity = "headline-delta-" + hashlib.sha256(
            json.dumps(
                identity_material, sort_keys=True, separators=(",", ":"), default=str
            ).encode("utf-8")
        ).hexdigest()[:32]
        if valid_ids:
            result.update({
                "material_event_due": True,
                "new_material_event_count": len(valid_ids),
                "new_material_event_identity": event_identity,
                "material_event_grants_evidence_or_publication_authority": False,
            })
        else:
            result["material_event_detail"] = "NO_SOURCE_EVENT_TIME_VALID_NEW_HEADLINES"
        result["detail"] = f"CAPTURED_NEW:{rows_added}"
        return _finish(OUTCOME_CAPTURED_NEW, last_success=_epoch(moment), rows=rows_added, consecutive_empty=0)
    result["detail"] = "CAPTURED_NO_NEW_HEADLINES"
    return _finish(
        OUTCOME_CAPTURED_NONE,
        last_success=_epoch(moment),
        rows=0,
        consecutive_empty=checkpoint["consecutive_empty"] + 1,
    )


def rolling_24h_unique_headline_count(*, sidecar_glob: str, now: Optional[datetime] = None) -> int:
    """Count the complete current rolling-24h unique headline universe (all daily files)."""
    from live_contentops.newsroom_assignment_scheduler_v1 import (
        load_rolling_x_headline_sidecars,
    )

    moment = now or _utc_now()
    intake = load_rolling_x_headline_sidecars(
        cutoff_utc=moment, sidecar_glob=sidecar_glob, window_hours=24.0
    )
    return len(intake.get("headlines") or [])


def intake_is_stale(store: Any, *, now: Optional[datetime] = None, threshold_seconds: float = STALE_SYNC_THRESHOLD_SECONDS) -> bool:
    moment = now or _utc_now()
    checkpoint = read_ingestion_checkpoint(store)
    last_success = checkpoint["last_success_epoch"]
    if last_success is None:
        return True
    return (_epoch(moment.astimezone(timezone.utc)) - float(last_success)) > float(threshold_seconds)
