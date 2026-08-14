"""Continuous cheap X headline ingestion lane for the Final Daily App supervisor.

Owner decision 2026-08-10 (V1 realignment): headline ingestion is continuous/cheap while the
Daily App host is available. It is a housekeeping lane INSIDE the canonical supervisor tick:
no second scheduler authority, no second Daily App, no second production DB, and ZERO
LLM/provider calls. Editorial windows do not own headline ingestion; Run Now does not own
headline ingestion. The lane keeps the canonical single-folder per-day sidecar store current
so every editorial decision can reconstruct the complete rolling 24-hour headline universe.

Cadence policy (versioned configuration, not universal truth):

- normal interval 30 minutes;
- after CAPTURED_NEW, at most one 15-minute follow-up before returning to normal;
- CAPTURED_NO_NEW_HEADLINES backs off to 60 minutes and stays there while empty;
- one bounded capture per due iteration; no parallel captures (single-flight per supervisor);
- transient failure retries no sooner than 30 minutes;
- REAUTH_REQUIRED is reported when the exact locked X session expires; the lane never
  automates login and never substitutes another profile.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from live_contentops.browser_interaction_budget_v1 import (
    BROWSER_INTERACTION_BUDGET_V1,
    browser_activity,
    record_browser_interaction_event,
)

LANE_SCHEMA_VERSION = "contentops.continuous_headline_ingest.v3"
ATTEMPT_DETAIL_SCHEMA_VERSION = "contentops.x_capture_attempt_detail.v1"
ATTEMPT_DETAIL_FILENAME = "last_capture_attempt_v1.json"
ATTEMPT_DETAIL_MAX_BYTES = 4096
FAILURE_DETAIL_MAX_LENGTH = 160
X_INGESTION_BROWSER_ROLE = "CHROME_CDP_9222_INGESTION_ONLY"

NORMAL_INTERVAL_SECONDS = BROWSER_INTERACTION_BUDGET_V1.x_normal_interval_seconds
HOT_FOLLOWUP_INTERVAL_SECONDS = BROWSER_INTERACTION_BUDGET_V1.x_hot_followup_interval_seconds
EMPTY_INTERVAL_SECONDS = BROWSER_INTERACTION_BUDGET_V1.x_empty_interval_seconds
TRANSIENT_RETRY_INTERVAL_SECONDS = BROWSER_INTERACTION_BUDGET_V1.x_transient_retry_min_seconds
# Compatibility names now expose the sustainable normal/max policy.
ACTIVE_INTERVAL_SECONDS = NORMAL_INTERVAL_SECONDS
MAX_INTERVAL_SECONDS = EMPTY_INTERVAL_SECONDS
CAPTURE_MAX_SECONDS = 60.0
CAPTURE_MAX_EMPTY_SCROLLS = 1
STALE_SYNC_THRESHOLD_SECONDS = NORMAL_INTERVAL_SECONDS

METRIC_LAST_SUCCESS_EPOCH = "metric_headline_ingest_last_success_epoch"
METRIC_LAST_OUTCOME_CODE = "metric_headline_ingest_last_outcome_code"
METRIC_CONSECUTIVE_EMPTY = "metric_headline_ingest_consecutive_empty"
METRIC_ROWS_LAST_ITERATION = "metric_headline_ingest_rows_last_iteration"
METRIC_LAST_ATTEMPT_EPOCH = "metric_headline_ingest_last_attempt_epoch"
METRIC_HOT_FOLLOWUP_PENDING = "metric_headline_ingest_hot_followup_pending"

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

_INGESTION_CAPTURE_LOCK = threading.Lock()


def _safe_diagnostic_label(value: Any, *, fallback: str) -> str:
    text = str(value or "").strip().upper()
    if any(marker in text for marker in (
        "TOKEN", "COOKIE", "AUTHORIZATION", "BEARER", "PASSWORD", "LOCALSTORAGE",
        "SESSIONSTORAGE", "CLIENT_SECRET", "ACCESS_KEY",
    )):
        return fallback
    safe = "".join(character for character in text if character.isalnum() or character in "_.:-")
    return (safe[:FAILURE_DETAIL_MAX_LENGTH] or fallback)


def _attempt_detail_path(store: Any) -> Path:
    return Path(store.db_path).resolve().parent / "headline_ingestion" / ATTEMPT_DETAIL_FILENAME


def _write_attempt_detail(store: Any, payload: Mapping[str, Any]) -> None:
    path = _attempt_detail_path(store)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    if len(body.encode("utf-8")) > ATTEMPT_DETAIL_MAX_BYTES:
        raise ValueError("attempt_detail_exceeds_bounded_size")
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(body)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _read_attempt_detail(store: Any, *, last_attempt_epoch: Optional[float]) -> dict[str, Any] | None:
    if last_attempt_epoch is None:
        return None
    try:
        raw = _attempt_detail_path(store).read_bytes()
        if len(raw) > ATTEMPT_DETAIL_MAX_BYTES:
            return None
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, Mapping) or value.get("schema_version") != ATTEMPT_DETAIL_SCHEMA_VERSION:
            return None
        if abs(float(value.get("attempt_epoch")) - float(last_attempt_epoch)) > 0.001:
            return None
        return dict(value)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _eligibility_reason(checkpoint: Mapping[str, Any]) -> str:
    outcome = checkpoint.get("last_outcome_code")
    if checkpoint.get("last_attempt_epoch") is None and checkpoint.get("last_success_epoch") is None:
        return "NO_PRIOR_ATTEMPT"
    if checkpoint.get("hot_followup_pending") and outcome == OUTCOME_CAPTURED_NEW:
        return "HOT_FOLLOWUP_DUE"
    if outcome == OUTCOME_CAPTURED_NONE:
        return "EMPTY_BACKOFF_DUE"
    if outcome in {
        OUTCOME_CDP_UNAVAILABLE, OUTCOME_CAPTURE_FAILED,
        OUTCOME_BROWSER_BINDING_MISSING, OUTCOME_PORT_OWNER_UNPROVEN,
    }:
        return "TRANSIENT_RETRY_DUE"
    return "NORMAL_INTERVAL_DUE"


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
                "SELECT metric_id, metric_value FROM metrics WHERE metric_id IN (?,?,?,?,?,?)",
                (
                    METRIC_LAST_SUCCESS_EPOCH,
                    METRIC_LAST_OUTCOME_CODE,
                    METRIC_CONSECUTIVE_EMPTY,
                    METRIC_ROWS_LAST_ITERATION,
                    METRIC_LAST_ATTEMPT_EPOCH,
                    METRIC_HOT_FOLLOWUP_PENDING,
                ),
            ).fetchall()
        }
    checkpoint = {
        "last_success_epoch": rows.get(METRIC_LAST_SUCCESS_EPOCH),
        "last_outcome_code": rows.get(METRIC_LAST_OUTCOME_CODE),
        "consecutive_empty": int(rows.get(METRIC_CONSECUTIVE_EMPTY) or 0),
        "rows_last_iteration": int(rows.get(METRIC_ROWS_LAST_ITERATION) or 0),
        "last_attempt_epoch": rows.get(METRIC_LAST_ATTEMPT_EPOCH),
        "hot_followup_pending": bool(rows.get(METRIC_HOT_FOLLOWUP_PENDING) or 0),
    }
    checkpoint["last_attempt_detail"] = _read_attempt_detail(
        store, last_attempt_epoch=checkpoint["last_attempt_epoch"]
    )
    return checkpoint


def write_ingestion_checkpoint(
    store: Any,
    *,
    now: datetime,
    last_success_epoch: Optional[float],
    outcome_code: float,
    consecutive_empty: int,
    rows_iteration: int,
    last_attempt_epoch: Optional[float] = None,
    hot_followup_pending: bool = False,
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
            if last_attempt_epoch is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                    (METRIC_LAST_ATTEMPT_EPOCH, "headline_ingest_last_attempt_epoch", float(last_attempt_epoch), iso_now),
                )
            conn.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                (METRIC_HOT_FOLLOWUP_PENDING, "headline_ingest_hot_followup_pending", 1.0 if hot_followup_pending else 0.0, iso_now),
            )
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise


def next_due_interval_seconds(
    consecutive_empty: int = 0,
    *,
    last_outcome_code: Optional[float] = None,
    hot_followup_pending: bool = False,
) -> float:
    del consecutive_empty  # retained for compatibility; repeated empty captures stay at 60m.
    if hot_followup_pending and last_outcome_code == OUTCOME_CAPTURED_NEW:
        return HOT_FOLLOWUP_INTERVAL_SECONDS
    if last_outcome_code == OUTCOME_CAPTURED_NONE:
        return EMPTY_INTERVAL_SECONDS
    if last_outcome_code in {
        OUTCOME_CDP_UNAVAILABLE,
        OUTCOME_CAPTURE_FAILED,
        OUTCOME_BROWSER_BINDING_MISSING,
        OUTCOME_PORT_OWNER_UNPROVEN,
    }:
        return TRANSIENT_RETRY_INTERVAL_SECONDS
    return NORMAL_INTERVAL_SECONDS


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
            "normal_interval_seconds": NORMAL_INTERVAL_SECONDS,
            "hot_followup_interval_seconds": HOT_FOLLOWUP_INTERVAL_SECONDS,
            "hot_followup_max": BROWSER_INTERACTION_BUDGET_V1.x_hot_followup_max,
            "empty_interval_seconds": EMPTY_INTERVAL_SECONDS,
            "transient_retry_min_seconds": TRANSIENT_RETRY_INTERVAL_SECONDS,
        },
        "cadence_state": None,
        "next_eligible_capture_utc": None,
        "material_event_due": False,
        "new_material_event_count": 0,
        "new_material_event_identity": None,
        "new_headline_ids": [],
        "new_headline_source_refs": [],
        "eligibility_reason": None,
        "browser_role": X_INGESTION_BROWSER_ROLE,
        "chrome_9222_readiness": "NOT_EVALUATED",
        "auth_classification": "NOT_EVALUATED",
        "capture_state": None,
        "capture_phase": None,
        "timeline_responses_observed": 0,
        "failure_class": None,
        "failure_detail": None,
        "attempt_detail_persisted": False,
    }

    def _finish(
        outcome_code: float,
        *,
        last_success: Optional[float] = None,
        rows: int = 0,
        consecutive_empty: Optional[int] = None,
        hot_followup_pending: bool = False,
    ) -> dict[str, Any]:
        empty_count = checkpoint["consecutive_empty"] if consecutive_empty is None else consecutive_empty
        checkpoint_persisted = True
        try:
            write_ingestion_checkpoint(
                store,
                now=moment,
                last_success_epoch=last_success if last_success is not None else checkpoint["last_success_epoch"],
                outcome_code=outcome_code,
                consecutive_empty=empty_count,
                rows_iteration=rows,
                last_attempt_epoch=_epoch(moment),
                hot_followup_pending=hot_followup_pending,
            )
        except Exception as exc:  # noqa: BLE001 - checkpoint persistence is best-effort
            checkpoint_persisted = False
            exception_type = _safe_diagnostic_label(type(exc).__name__, fallback="EXCEPTION")
            result["detail"] = f"CHECKPOINT_WRITE_FAILED:{exception_type}"
            result["failure_class"] = "CHECKPOINT_PERSISTENCE_FAILURE"
            result["failure_detail"] = result["detail"]
        result["lane_state"] = ingestion_lane_state(outcome_code)
        interval = next_due_interval_seconds(
            empty_count,
            last_outcome_code=outcome_code,
            hot_followup_pending=hot_followup_pending,
        )
        result["cadence_state"] = (
            "HOT_FOLLOWUP" if hot_followup_pending and outcome_code == OUTCOME_CAPTURED_NEW
            else "EMPTY_BACKOFF" if outcome_code == OUTCOME_CAPTURED_NONE
            else "TRANSIENT_RETRY" if outcome_code in {
                OUTCOME_CDP_UNAVAILABLE, OUTCOME_CAPTURE_FAILED,
                OUTCOME_BROWSER_BINDING_MISSING, OUTCOME_PORT_OWNER_UNPROVEN,
            }
            else "REAUTH_WAIT" if outcome_code == OUTCOME_REAUTH_REQUIRED
            else "NORMAL"
        )
        if outcome_code != OUTCOME_REAUTH_REQUIRED:
            result["next_eligible_capture_utc"] = (
                moment + timedelta(seconds=interval)
            ).isoformat().replace("+00:00", "Z")
        if result.get("failure_class"):
            result["failure_class"] = _safe_diagnostic_label(
                result["failure_class"], fallback="OTHER_CAPTURE_FAILURE"
            )
        if result.get("failure_detail"):
            result["failure_detail"] = _safe_diagnostic_label(
                result["failure_detail"], fallback="REDACTED_UNSAFE_DIAGNOSTIC"
            )
        attempt_payload = {
            "schema_version": ATTEMPT_DETAIL_SCHEMA_VERSION,
            "attempt_at_utc": result["iteration_at_utc"],
            "attempt_epoch": _epoch(moment),
            "eligibility_reason": result.get("eligibility_reason"),
            "browser_role": X_INGESTION_BROWSER_ROLE,
            "chrome_9222_readiness": result.get("chrome_9222_readiness"),
            "auth_classification": result.get("auth_classification"),
            "capture_state": result.get("capture_state"),
            "capture_phase": result.get("capture_phase"),
            "timeline_responses_observed": int(result.get("timeline_responses_observed") or 0),
            "failure_class": result.get("failure_class"),
            "failure_detail": result.get("failure_detail"),
            "outcome_code": float(outcome_code),
            "rows_captured": int(rows),
            "newest_source_event_at_utc": result.get("newest_source_event_at_utc"),
            "lane_state": result.get("lane_state"),
            "cadence_state": result.get("cadence_state"),
            "next_eligible_capture_utc": result.get("next_eligible_capture_utc"),
            "checkpoint_persisted": checkpoint_persisted,
            "contains_secrets_or_session_material": False,
        }
        try:
            _write_attempt_detail(store, attempt_payload)
            result["attempt_detail_persisted"] = True
        except Exception as exc:  # noqa: BLE001 - result still truthfully exposes persistence loss
            exception_type = _safe_diagnostic_label(type(exc).__name__, fallback="EXCEPTION")
            result["attempt_detail_persisted"] = False
            result["attempt_detail_persistence_error"] = f"ATTEMPT_DETAIL_WRITE_FAILED:{exception_type}"
        return result

    try:
        operating_mode = str(store.get_operating_control().get("operating_mode") or "KILL_SWITCH")
    except Exception:
        operating_mode = "KILL_SWITCH"
    if operating_mode == "KILL_SWITCH":
        result.update({
            "lane_state": "PAUSED_KILL_SWITCH",
            "detail": "NETWORK_INTAKE_PAUSED_BY_OPERATOR_KILL_SWITCH",
            "cadence_state": "KILL_SWITCH",
        })
        return result

    # ``force`` means the caller requested a freshness check, not permission to bypass the
    # browser budget. Run Now therefore observes the same next-eligible boundary.
    last_attempt = checkpoint["last_attempt_epoch"]
    if last_attempt is None:
        last_attempt = checkpoint["last_success_epoch"]
    elapsed = (_epoch(moment) - float(last_attempt)) if last_attempt is not None else None
    if checkpoint["last_outcome_code"] == OUTCOME_REAUTH_REQUIRED:
        result["lane_state"] = LANE_STATE_REAUTH_REQUIRED
        result["detail"] = "reauth_required_waiting_for_operator"
        result["cadence_state"] = "REAUTH_WAIT"
        return result
    due_interval = next_due_interval_seconds(
        checkpoint["consecutive_empty"],
        last_outcome_code=checkpoint["last_outcome_code"],
        hot_followup_pending=checkpoint["hot_followup_pending"],
    )
    if elapsed is not None and elapsed < due_interval:
        result["lane_state"] = ingestion_lane_state(checkpoint["last_outcome_code"])
        result["detail"] = "not_due"
        result["cadence_state"] = (
            "HOT_FOLLOWUP" if checkpoint["hot_followup_pending"] else
            "EMPTY_BACKOFF" if checkpoint["last_outcome_code"] == OUTCOME_CAPTURED_NONE else
            "TRANSIENT_RETRY" if checkpoint["last_outcome_code"] in {
                OUTCOME_CDP_UNAVAILABLE, OUTCOME_CAPTURE_FAILED,
                OUTCOME_BROWSER_BINDING_MISSING, OUTCOME_PORT_OWNER_UNPROVEN,
            } else "NORMAL"
        )
        result["next_eligible_capture_utc"] = datetime.fromtimestamp(
            float(last_attempt) + due_interval, tz=timezone.utc
        ).isoformat().replace("+00:00", "Z")
        return result
    result["due"] = True
    result["eligibility_reason"] = _eligibility_reason(checkpoint)

    if state_fn is not None:
        process_state = dict(state_fn())
    else:
        from live_contentops.ingestion_bootstrap_v1 import ingestion_process_state

        process_state = dict(ingestion_process_state())
    state_name = str(process_state.get("state") or "")
    result["chrome_9222_readiness"] = state_name or "UNKNOWN"

    if state_name not in {"READY"}:
        from live_contentops.ingestion_bootstrap_v1 import (
            STATE_PORT_OWNER_UNPROVEN,
            STATE_PROFILE_BINDING_MISSING,
            STATE_RUNNING_WITHOUT_CDP,
        )

        if state_name == STATE_PROFILE_BINDING_MISSING:
            result["detail"] = "PROFILE_BINDING_MISSING_FAIL_CLOSED"
            result["failure_class"] = "PROFILE_PORT_OWNERSHIP_PROBLEM"
            result["failure_detail"] = result["detail"]
            return _finish(OUTCOME_BROWSER_BINDING_MISSING, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if state_name == STATE_PORT_OWNER_UNPROVEN:
            result["detail"] = "PORT_OWNER_UNPROVEN_FAIL_CLOSED"
            result["failure_class"] = "PROFILE_PORT_OWNERSHIP_PROBLEM"
            result["failure_detail"] = result["detail"]
            return _finish(OUTCOME_PORT_OWNER_UNPROVEN, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if state_name == STATE_RUNNING_WITHOUT_CDP:
            result["detail"] = "CANONICAL_PROFILE_RUNNING_WITHOUT_CDP"
            result["failure_class"] = "CDP_BROWSER_UNAVAILABLE"
            result["failure_detail"] = result["detail"]
            return _finish(OUTCOME_CDP_UNAVAILABLE, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if ensure_fn is not None:
            ensured = dict(ensure_fn())
        else:
            from live_contentops.ingestion_bootstrap_v1 import canonical_ingestion_readiness

            ensured = dict(canonical_ingestion_readiness(session_timeout_seconds=8.0))
        ensured_state = str(ensured.get("chrome_9222_ingestion") or "")
        result["chrome_9222_readiness"] = ensured_state or state_name or "UNKNOWN"
        if ensured_state == "REAUTH_REQUIRED":
            result["detail"] = "LOGIN_REDIRECT_OBSERVED"
            result["auth_classification"] = "REAUTH_REQUIRED"
            result["failure_class"] = "AUTH_REAUTH_REQUIRED"
            result["failure_detail"] = result["detail"]
            return _finish(OUTCOME_REAUTH_REQUIRED, consecutive_empty=checkpoint["consecutive_empty"] + 1)
        if ensured_state not in {"READY", "READY_AUTH_UNVERIFIED"}:
            result["detail"] = f"CDP_UNAVAILABLE:{ensured_state}"
            result["failure_class"] = "CDP_BROWSER_UNAVAILABLE"
            result["failure_detail"] = result["detail"]
            return _finish(OUTCOME_CDP_UNAVAILABLE, consecutive_empty=checkpoint["consecutive_empty"] + 1)

    if not _INGESTION_CAPTURE_LOCK.acquire(blocking=False):
        result.update({
            "lane_state": LANE_STATE_READY,
            "detail": "parallel_capture_suppressed",
            "due": False,
            "cadence_state": "SINGLE_FLIGHT_ACTIVE",
        })
        return result
    capture_error: Exception | None = None
    try:
        if session_fn is not None:
            session_state = dict(session_fn())
        else:
            from live_contentops.x_list_ingest_capture_v1 import probe_session_visible_state

            session_state = dict(probe_session_visible_state(timeout_seconds=10.0))
        result["auth_classification"] = str(session_state.get("session_state") or "INCONCLUSIVE")
        if session_state.get("session_state") != "REAUTH_REQUIRED":
            record_browser_interaction_event(
                "x_capture", reason="DUE_LOW_FREQUENCY_X_INGESTION", destination="x_ingestion"
            )
            with browser_activity(
                "INGESTION_ACTIVE",
                reason="DUE_LOW_FREQUENCY_X_INGESTION",
                destination="x_ingestion",
            ):
                if capture_fn is not None:
                    capture = dict(capture_fn(max_seconds=CAPTURE_MAX_SECONDS, max_empty_scrolls=CAPTURE_MAX_EMPTY_SCROLLS))
                else:
                    from live_contentops.x_list_ingest_capture_v1 import run_bounded_x_list_capture

                    capture = dict(
                        run_bounded_x_list_capture(
                            max_seconds=CAPTURE_MAX_SECONDS, max_empty_scrolls=CAPTURE_MAX_EMPTY_SCROLLS
                        )
                    )
        else:
            capture = {}
    except Exception as exc:  # noqa: BLE001 - a failed attempt must still advance durable cadence
        capture = {}
        capture_error = exc
    finally:
        _INGESTION_CAPTURE_LOCK.release()
    if capture_error is not None:
        from live_contentops.x_list_ingest_capture_v1 import classify_capture_exception

        failure_class, failure_detail = classify_capture_exception(capture_error, phase="CAPTURE_CALL")
        result["capture_attempted"] = True
        result["capture_state"] = "CAPTURE_FAILED"
        result["capture_phase"] = "CAPTURE_CALL"
        result["failure_class"] = failure_class
        result["failure_detail"] = failure_detail
        result["detail"] = f"CAPTURE_FAILED:{failure_class}"
        return _finish(
            OUTCOME_CAPTURE_FAILED,
            consecutive_empty=checkpoint["consecutive_empty"] + 1,
        )
    if session_state.get("session_state") == "REAUTH_REQUIRED":
        result["detail"] = "LOGIN_REDIRECT_OBSERVED"
        result["failure_class"] = "AUTH_REAUTH_REQUIRED"
        result["failure_detail"] = result["detail"]
        return _finish(OUTCOME_REAUTH_REQUIRED, consecutive_empty=checkpoint["consecutive_empty"] + 1)
    result["capture_attempted"] = True
    capture_state = str(capture.get("capture_state") or "CAPTURE_FAILED")
    result["capture_state"] = capture_state
    result["capture_phase"] = capture.get("capture_phase")
    result["timeline_responses_observed"] = int(capture.get("timeline_responses_observed") or 0)
    result["failure_class"] = capture.get("failure_class")
    result["failure_detail"] = capture.get("failure_detail") or capture.get("detail")
    rows_added = int(capture.get("new_headlines") or 0)
    result["rows_added"] = rows_added
    result["new_headline_ids"] = sorted({
        str(value) for value in (capture.get("new_headline_ids") or []) if str(value)
    })
    result["new_headline_source_refs"] = [
        dict(value) for value in (capture.get("new_headline_source_refs") or [])
        if isinstance(value, Mapping)
    ]
    source_times = sorted(
        str(value.get("headline_timestamp") or "")
        for value in result["new_headline_source_refs"]
        if str(value.get("headline_timestamp") or "")
    )
    result["newest_source_event_at_utc"] = source_times[-1] if source_times else None
    if capture_state == "REAUTH_REQUIRED":
        result["detail"] = "LOGIN_REDIRECT_OBSERVED"
        result["auth_classification"] = "REAUTH_REQUIRED"
        result["failure_class"] = "AUTH_REAUTH_REQUIRED"
        result["failure_detail"] = result["detail"]
        return _finish(OUTCOME_REAUTH_REQUIRED, rows=rows_added, consecutive_empty=checkpoint["consecutive_empty"] + 1)
    if capture_state not in {"CAPTURED", "CAPTURED_NO_NEW_HEADLINES"}:
        failure_class = _safe_diagnostic_label(
            result.get("failure_class"), fallback="MALFORMED_EMPTY_CAPTURE_RESPONSE"
        )
        failure_detail = _safe_diagnostic_label(
            result.get("failure_detail"), fallback="CAPTURE_RETURNED_NO_SUCCESS_STATE"
        )
        result["failure_class"] = failure_class
        result["failure_detail"] = failure_detail
        result["detail"] = f"CAPTURE_FAILED:{failure_class}"
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
        # A normal capture may arm one 15-minute follow-up. A follow-up can never re-arm itself.
        arm_hot_followup = not checkpoint["hot_followup_pending"]
        return _finish(
            OUTCOME_CAPTURED_NEW,
            last_success=_epoch(moment),
            rows=rows_added,
            consecutive_empty=0,
            hot_followup_pending=arm_hot_followup,
        )
    result["detail"] = "CAPTURED_NO_NEW_HEADLINES"
    return _finish(
        OUTCOME_CAPTURED_NONE,
        last_success=_epoch(moment),
        rows=0,
        consecutive_empty=checkpoint["consecutive_empty"] + 1,
        hot_followup_pending=False,
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
