"""CC-338: a projection of published calls, never another ledger or scorer.

Original calls come from the existing publication feed and plan-post outbox.
One confirmed destination establishes a public call even while others are pending.
Main owns numerical scoring; a public state is not a return or a successful trade.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, check_publication_copy, conditional_call_text,
)
from live_contentops.published_content_v1 import DEFAULT_FEED, canonical, read_records, utc

SINCE = "2026-11-06T05:00:00Z"  # 6 November, 00:00 ET (decision 90)
SCHEMA = "contentops.public_call_scorecard.v1"
PUBLIC_STATES = {"WAITING", "TRIGGERED", "INVALIDATED", "CANCELLED", "EXPIRED", "VIEW_CHANGED"}
CONFIRMED = ("DISPATCH_CONFIRMED", "EXTERNAL_REMOVAL_REPORTED_NO_RETRY")


def public_time(value):
    return utc(value).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S ET")


def build_scorecard(store, *, feed_path=DEFAULT_FEED, since_utc=SINCE, as_of_utc=None):
    """Read every published call and its public transitions, without age/state filters.

    A removed publication remains in the population. A fill never resolves a call.
    Queued and ambiguous sends without a confirmed public destination are not public.
    Repeated state updates retain the original call and do not inflate the denominator.
    """
    as_of_utc = as_of_utc or datetime.now(timezone.utc).isoformat()
    start, end = utc(since_utc), utc(as_of_utc)
    if start > end:
        raise ValueError("SCORECARD_TIME_RANGE_INVALID")
    entries = {}

    def add(identity, call, at, publications, *, clock_fallback=None):
        known = at or clock_fallback
        if not start <= utc(known) <= end:
            return
        original = deepcopy(call)
        check_publication_copy({"notice": PUBLIC_NOTICE, "conflicts": CONFLICTS_NOTICE},
                               conditional_calls=[original], require_call_text=False)
        # A changed call is a separate version, never an edit of the earlier one.
        key = sha256(canonical([identity, original])).hexdigest()
        entry = entries.setdefault(key, {
            "call_id": "call-" + key[:24], "call": original,
            "first_published_at_utc": at, "call_known_at_utc": known,
            "publications": [], "public_history": [],
            "state": "UNRESOLVED", "score": None,
        })
        if at and (entry["first_published_at_utc"] is None or utc(at) < utc(entry["first_published_at_utc"])):
            entry["first_published_at_utc"] = at
        for publication in publications:
            if publication not in entry["publications"]:
                entry["publications"].append(publication)
        return entry

    for record in read_records(feed_path):
        for index, call in enumerate(record["conditional_calls"]):
            identity = call.get("call_id") or [record["content_id"], index]
            add(identity, call, record["published_at_utc"], record["outlets"])

    with store.get_read_only_connection() as conn:
        messages = conn.execute(
            "SELECT message_id,status,payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
            ("internal:plan-status-post",),
        ).fetchall()
        # Channel outbox rows belong to the original plan-post message's work item.
        dispatches = conn.execute(
            "SELECT o.work_item_id,d.platform,d.public_object_url,d.dispatched_at "
            "FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
            "WHERE d.status IN (?,?) AND d.public_object_url IS NOT NULL",
            CONFIRMED,
        ).fetchall()
    destinations = {}
    for work_item, platform, url, at in dispatches:
        if at and utc(at) <= end:
            destinations.setdefault(work_item, []).append({"name": platform, "url": url, "at_utc": at})
    plans = {}
    history = {}
    for message_id, status, raw in messages:
        packet = json.loads(raw)
        publications = destinations.get(message_id, [])
        if status != "PUBLISHED" and not publications:
            continue
        state, at = packet.get("state"), packet.get("at_utc")
        if state not in PUBLIC_STATES or not at or utc(at) > end:
            continue  # decision 40: FILLED and other execution states stay private
        plan_id = packet["plan_id"]
        history.setdefault(plan_id, []).append({"state": state, "at_utc": at})
        for call in packet.get("conditional_calls") or []:
            # The event clock and the first public-write clock stay distinct.
            public_at = min((p["at_utc"] for p in publications), key=utc) if publications else None
            entry = add(["plan", plan_id], call, public_at, publications, clock_fallback=at)
            if entry is not None:
                plans.setdefault(plan_id, []).append(entry)
    for plan_id, calls in plans.items():
        events = sorted(history.get(plan_id, []), key=lambda r: utc(r["at_utc"]))
        for entry in calls:
            entry["public_history"] = deepcopy(events)
            latest = events[-1]["state"] if events else "WAITING"
            entry["state"] = {
                "WAITING": "UNRESOLVED", "TRIGGERED": "TRIGGERED", "INVALIDATED": "INVALIDATED",
                "CANCELLED": "WITHDRAWN", "VIEW_CHANGED": "WITHDRAWN",
                "EXPIRED": "UNRESOLVED" if any(e["state"] == "TRIGGERED" for e in events) else "NOT_TRIGGERED",
            }[latest]
    rows = sorted(entries.values(), key=lambda r: (utc(r["call_known_at_utc"]), r["call_id"]))
    return {"schema_version": SCHEMA, "since_utc": since_utc, "as_of_utc": as_of_utc,
            "total_calls": len(rows), "state_counts": dict(sorted(Counter(r["state"] for r in rows).items())),
            "calls": rows, "notice": PUBLIC_NOTICE, "conflicts_notice": CONFLICTS_NOTICE,
            "scoring_note": "Public states are shown. Numerical resolution and benchmark scores await Main's scored output; no performance claim."}


def render_scorecard(scorecard):
    """A structured public table; the native writer owns surrounding review prose."""
    lines = [f"Public calls since {public_time(scorecard['since_utc'])}",
             f"As of {public_time(scorecard['as_of_utc'])}. Total calls: {scorecard['total_calls']}.",
             "", "| First published (ET) | Original call | Public state |", "| --- | --- | --- |"]
    for row in scorecard["calls"]:
        wording = conditional_call_text(row["call"]).replace("|", "&#124;").replace("\n", " ")
        when = public_time(row["first_published_at_utc"]) if row["first_published_at_utc"] else "Time not retained"
        lines.append(f"| {when} | {wording} | {row['state'].lower().replace('_', ' ')} |")
    lines.extend(["", scorecard["scoring_note"], "", PUBLIC_NOTICE, CONFLICTS_NOTICE])
    return "\n".join(lines) + "\n"
