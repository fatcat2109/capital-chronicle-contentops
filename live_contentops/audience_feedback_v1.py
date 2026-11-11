"""CC-402 audience rows for the installed desk and measured post-type decisions."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

SCHEMA = "contentops.audience_weekly.cc402.v1"
STOP = "POST_TYPE_STOPPED_NO_READERS_THREE_WEEKS"
TYPES = {
    "setup": "Call", "call": "Call", "conditional_call": "Call", "run": "Call",
    "event": "Event", "event_preview": "Event", "event_review": "Result",
    "result": "Result", "closed": "Result", "exit": "Result",
    "scorecard": "Scorecard", "weekly_scorecard": "Scorecard",
    "map": "Map", "morning_map": "Map", "daily_wrap": "Daily note",
    "daily_note": "Daily note", "weekly_review": "Weekly review",
    "reply": "Reply", "sourced_reply": "Reply", "state": "Update", "why": "Update",
    "note": "Note", "article": "Article",
}
READER_METRICS = ("views", "total_views", "reach", "impressions", "meaningful_reads")
INTERACTIONS = ("likes", "reactions", "comments", "replies", "shares", "reposts", "saves")


def clock(value):
    try:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return at.astimezone(timezone.utc) if at.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def post_type(intent, source=None):
    """Use retained structured fields, never infer a type from a headline."""
    source = source or {}
    article = intent.get("article") or {}
    kind = source.get("kind") or intent.get("post_type") or article.get("post_type") or intent.get("kind")
    if kind in TYPES.values():
        return kind
    return TYPES.get(str(kind).lower(), "Article" if article else "Unspecified")


def _mapping(value):
    try:
        result = json.loads(value or "{}") if isinstance(value, str) or value is None else value
        return result if isinstance(result, dict) else {}
    except ValueError:
        return {}


def project_audience(*, dispatches, reconciliations, readbacks, observations, metadata, now, previous=None):
    from .channel_engagement_v1 import verified_dispatch_readback, verified_dispatch_identity
    from .publication_coordinator_v1 import DurablePublicationCoordinator

    now = now.astimezone(timezone.utc)
    end = now.astimezone(ZoneInfo("Asia/Bangkok")).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=21)
    statuses = {r["reconciliation_id"]: r["status"] for r in reconciliations}
    reads = defaultdict(list)
    for row in readbacks:
        reads[row["dispatch_id"]].append(row)
    eligible, objects = {}, {}
    for row in dispatches:
        posted = clock(row.get("dispatched_at"))
        if not posted or not start <= posted <= now:
            continue
        status = statuses.get("reconciliation_" + row["dispatch_id"].removeprefix("dispatch_"))
        if not DurablePublicationCoordinator._confirmed_public_object({**row, "reconciliation_status": status}, destination=row["platform"]):
            continue
        if not any(verified_dispatch_readback(r, row) or verified_dispatch_identity(r, row) for r in reads[row["dispatch_id"]]):
            continue
        eligible[row["dispatch_id"]] = row
        key = (row["platform"], str(row["public_object_id"]))
        if key not in objects or posted < clock(objects[key]["dispatched_at"]):
            objects[key] = row
    latest = {}
    for row in observations:
        at = clock(row.get("collected_at_utc"))
        dispatch = eligible.get(row["dispatch_id"])
        if (not at or at > now or not dispatch or row["platform"] != dispatch["platform"]
                or str(row["public_object_id"]) != str(dispatch["public_object_id"])):
            continue
        key = (row["platform"], str(row["public_object_id"]))
        if key not in latest or at > clock(latest[key]["collected_at_utc"]):
            latest[key] = row
    samples = []
    for key, dispatch in objects.items():
        row = latest.get(key, {})
        native = _mapping(row.get("metrics_native_json"))
        states = _mapping(row.get("metric_availability_json"))
        available = {k: v for k, v in native.items() if states.get(k) == "AVAILABLE"
                     and type(v) in (int, float) and math.isfinite(v) and v >= 0}
        readers = [available[k] for k in READER_METRICS if k in available]
        positive = any(available.get(k, 0) > 0 for k in (*READER_METRICS, *INTERACTIONS))
        samples.append({"post_type": metadata.get(dispatch["dispatch_id"], "Unspecified"),
            "platform": key[0], "public_object_id": key[1], "dispatch_id": dispatch["dispatch_id"],
            "work_item_id": row.get("work_item_id"), "url": dispatch.get("public_object_url"),
            "posted_at_utc": dispatch["dispatched_at"], "collected_at_utc": row.get("collected_at_utc"),
            "observation_id": row.get("observation_id"), "views": available.get("views"),
            "reader_zero": False if positive else True if readers else None,
            "hour_et": clock(dispatch["dispatched_at"]).astimezone(ZoneInfo("America/New_York")).hour,
            "cause": None if "views" in available else "VIEWS_" + str(states.get("views") or row.get("collection_status") or "NOT_COLLECTED")})
    weekly = [s for s in samples if clock(s["posted_at_utc"]) >= end - timedelta(days=6)]
    groups, hours = defaultdict(list), defaultdict(list)
    for row in weekly:
        groups[(row["post_type"], row["platform"])].append(row)
        hours[row["hour_et"]].append(row)
    def summary(rows):
        values = [r["views"] for r in rows if r["views"] is not None]
        return {"posts": rows, "n": len(values), "median_views": median(values) if values else None,
                "cause": None if values else "NO_AVAILABLE_VIEW_COUNTER"}
    policy = dict((previous or {}).get("post_type_policy") or {})
    for kind in sorted({s["post_type"] for s in samples} - {"Unspecified"}):
        if policy.get(kind, {}).get("state") == "STOPPED":
            continue
        rows = [s for s in samples if s["post_type"] == kind]
        weeks = [[s for s in rows if start + timedelta(days=7*i) <= clock(s["posted_at_utc"]) < start + timedelta(days=7*(i+1))] for i in range(3)]
        stop = all(week and all(s["reader_zero"] is True for s in week) for week in weeks)
        policy[kind] = {"state": "STOPPED" if stop else "CONTINUE",
            "reason": STOP if stop else "THREE_COMPLETE_WEEKS_OF_MEASURED_ZERO_READERS_NOT_OBSERVED",
            "window_start_utc": start.astimezone(timezone.utc).isoformat(),
            "window_end_utc": end.astimezone(timezone.utc).isoformat(),
            "weekly_objects": [len(w) for w in weeks],
            **({"stopped_at_utc": now.isoformat(), "observation_ids": [s["observation_id"] for w in weeks for s in w]} if stop else {})}
    return {"schema_version": SCHEMA, "as_of_utc": now.isoformat(),
        "rows": [{"type": k[0], "platform": k[1], **summary(v)} for k, v in sorted(groups.items())],
        "hours": [{"hour_et": h, **summary(v)} for h, v in sorted(hours.items())],
        "post_type_policy": policy,
        "basis": "Latest cumulative native views per public object, median by post type/platform; publication hour in ET. Missing views stay unavailable. Stop only after all objects in each of three complete weeks have measured zero readers; positive interactions prevent a zero-reader conclusion."}


def stopped_type_for_new_message(store, message, intent):
    """The sole publisher consumes the desk export; issued objects keep recovery."""
    path = Path(store.db_path).parent / "audience-weekly/latest.json"
    try:
        value = json.loads(path.read_bytes())
        if value.get("schema_version") != SCHEMA or value.get("input_store") != str(Path(store.db_path).resolve()):
            return None
        source = store.get_outbox_message(intent.get("plan_status_post")) if intent.get("plan_status_post") else None
        kind = post_type(intent, json.loads((source or {}).get("payload") or "{}"))
        policy = value.get("post_type_policy", {}).get(kind, {})
        stopped, created = clock(policy.get("stopped_at_utc")), clock(message.get("created_at"))
        # Issued messages, prior attempts and their exact recovery stay available.
        if policy.get("state") == "STOPPED" and stopped and created and stopped < created:
            return {"reason_code": STOP, "post_type": kind, "evidence": policy, "source": str(path)}
    except (OSError, ValueError, TypeError):
        pass
    return None
