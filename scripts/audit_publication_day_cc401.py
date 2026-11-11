"""One read-only CC-401 acceptance check. Never dispatches, retries or schedules."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.publication_coordinator_v1 import LOCAL_REFUSALS_NOT_PLATFORM_FAILURES


def _resolved_failure(conn, row, detail, dispatch):
    """Follow the live circuit's recorded repairs; preserve every original alarm."""
    cause = detail.get("reason_code") or detail.get("safe_error_classification")
    local = cause in LOCAL_REFUSALS_NOT_PLATFORM_FAILURES
    if cause in {"NEO_COMPOSER_PAYLOAD_MISMATCH", "NEO_COMPOSER_PREPARATION_FAILED"}:
        local = detail.get("status") == "DEFINITE_NO_WRITE"
    if local:
        return "LOCAL_REFUSAL_BEFORE_PLATFORM_CALL"
    marker = conn.execute("SELECT severity FROM incidents WHERE incident_id=?",
        (row["incident_id"] + "_local_prewrite_resolved",)).fetchone()
    if marker and marker["severity"] == "RESOLVED_LOCAL_PREWRITE":
        return "RECORDED_LOCAL_PREWRITE_REPAIR"
    dispatch_id = detail.get("dispatch_id", "")
    reconciliation = conn.execute("SELECT status FROM reconciliations WHERE reconciliation_id=?",
        ("reconciliation_" + dispatch_id.removeprefix("dispatch_"),)).fetchone()
    if (dispatch.get("platform") == detail.get("destination")
            and dispatch.get("status") == "DISPATCH_CONFIRMED"
            and dispatch.get("public_object_id") and dispatch.get("public_object_url")
            and reconciliation and reconciliation["status"] == "RECONCILED_CONFIRMED"):
        return "EXACT_OBJECT_RECONCILED_CONFIRMED"
    if (dispatch.get("platform") == detail.get("destination") and cause == "ValueError"
            and dispatch.get("status") == "RECONCILED_ABSENT_SAFE_TO_RETRY"
            and reconciliation and reconciliation["status"] == "RECONCILED_ABSENT_SAFE_TO_RETRY"):
        return "LOCAL_VALIDATION_RECONCILED_ABSENT"
    return None


def audit(store_path, day, *, now=None):
    et = ZoneInfo("America/New_York")
    start = datetime.combine(datetime.fromisoformat(day).date(), time(), et)
    end = start + timedelta(days=1)
    now = now or datetime.now(timezone.utc)
    posts = {"discord": 0, "threads": 0}
    false_unknowns = []
    incidents = {}
    active_incidents = {}
    resolved_incidents = []
    invalid_incidents = []
    conn = sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        dispatches = {r["dispatch_id"]: dict(r) for r in conn.execute("SELECT * FROM platform_dispatches")}
        for row in dispatches.values():
            if (row["platform"] in posts and row["status"] == "DISPATCH_CONFIRMED"
                    and start <= datetime.fromisoformat(row["dispatched_at"].replace("Z", "+00:00")) < end):
                posts[row["platform"]] += 1
        for row in conn.execute("SELECT * FROM incidents WHERE severity='DISPATCH_FAILURE'"):
            instant = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            if not start <= instant < end:
                continue
            try:
                detail = json.loads(row["description"])
                if not isinstance(detail, dict):
                    raise ValueError("incident description is not an object")
            except (ValueError, TypeError):
                invalid_incidents.append(row["incident_id"])
                continue
            destination = detail.get("destination")
            if destination:
                incidents[destination] = incidents.get(destination, 0) + 1
            dispatch = dispatches.get(detail.get("dispatch_id"), {})
            if (destination in posts and detail.get("status") == "UNKNOWN_WRITE"
                    and dispatch.get("status") == "DISPATCH_CONFIRMED"):
                false_unknowns.append(row["incident_id"])
            # A confirmed API false alarm always fails, even if later repaired.
            # The live circuit releases local refusals and exact reconciled
            # objects; historical rows must not masquerade as active failures.
            resolution = _resolved_failure(conn, row, detail, dispatch)
            if resolution:
                resolved_incidents.append({"incident_id": row["incident_id"],
                    "destination": destination, "resolution": resolution})
            elif destination:
                active_incidents[destination] = active_incidents.get(destination, 0) + 1
    finally:
        conn.close()
    complete = now >= end
    status = ("OBSERVATION_PENDING" if not complete else
              "FAIL" if false_unknowns or invalid_incidents or any(n > 1 for n in active_incidents.values()) else
              "NO_CONFIRMED_WRITES_OBSERVED" if not all(posts.values()) else "PASS")
    return {"status": status, "et_day": day, "day_complete": complete,
        "window_start_utc": start.astimezone(timezone.utc).isoformat(),
        "window_end_utc": end.astimezone(timezone.utc).isoformat(),
        "next_check_gmt7": end.astimezone(ZoneInfo("Asia/Bangkok")).isoformat(),
        "confirmed_posts": posts, "false_unknown_write_incidents": false_unknowns,
        "destination_failure_incidents": incidents,
        "active_destination_failure_incidents": active_incidents,
        "resolved_destination_failure_incidents": resolved_incidents,
        "invalid_incidents": invalid_incidents,
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "public_write_performed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--day", required=True, help="ET calendar date, YYYY-MM-DD")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.store, args.day)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
