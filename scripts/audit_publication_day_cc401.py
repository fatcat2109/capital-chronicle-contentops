"""One read-only CC-401 acceptance check. Never dispatches, retries or schedules."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def audit(store_path, day, *, now=None):
    et = ZoneInfo("America/New_York")
    start = datetime.combine(datetime.fromisoformat(day).date(), time(), et)
    end = start + timedelta(days=1)
    now = now or datetime.now(timezone.utc)
    posts = {"discord": 0, "threads": 0}
    false_unknowns = []
    incidents = {}
    conn = sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
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
            except (ValueError, TypeError):
                continue
            destination = detail.get("destination")
            if destination:
                incidents[destination] = incidents.get(destination, 0) + 1
            dispatch = dispatches.get(detail.get("dispatch_id"), {})
            if (destination in posts and detail.get("status") == "UNKNOWN_WRITE"
                    and dispatch.get("status") == "DISPATCH_CONFIRMED"):
                false_unknowns.append(row["incident_id"])
    finally:
        conn.close()
    complete = now >= end
    status = ("OBSERVATION_PENDING" if not complete else
              "FAIL" if false_unknowns or any(n > 1 for n in incidents.values()) else
              "NO_CONFIRMED_WRITES_OBSERVED" if not all(posts.values()) else "PASS")
    return {"status": status, "et_day": day, "day_complete": complete,
        "window_start_utc": start.astimezone(timezone.utc).isoformat(),
        "window_end_utc": end.astimezone(timezone.utc).isoformat(),
        "next_check_gmt7": end.astimezone(ZoneInfo("Asia/Bangkok")).isoformat(),
        "confirmed_posts": posts, "false_unknown_write_incidents": false_unknowns,
        "destination_failure_incidents": incidents, "public_write_performed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--day", required=True, help="ET calendar date, YYYY-MM-DD")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.store, args.day)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
