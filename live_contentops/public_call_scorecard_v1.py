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
ANNOTATIONS = "internal:public-call-annotation"


def record_article_call_annotation(store, annotation, *, feed_path=DEFAULT_FEED):
    """Add exact published spans in the existing outbox; never rewrite a sealed feed."""
    from pathlib import Path
    from live_contentops.neo_destination_handoff_v1 import _text
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes
    published = next((r for r in read_records(feed_path)
        if r["content_id"] == "substack:" + str(annotation.get("confirmed_post_id"))), None)
    if (not published or not any(o["name"] == "substack" and o["url"] == annotation.get("canonical_url")
            for o in published["outlets"]) or published["conditional_calls"]):
        raise ValueError("CALL_ANNOTATION_EXACT_CONFIRMED_UNANNOTATED_ARTICLE_REQUIRED")
    dispatches = [d for d in store.get_dispatches_for_work_item(annotation["run_id"])
        if d["platform"] == "substack" and d["status"] in CONFIRMED
        and d.get("public_object_id") == annotation["confirmed_post_id"]]
    if len(dispatches) != 1:
        raise ValueError("CALL_ANNOTATION_CONFIRMED_OBJECT_REQUIRED")
    intent = json.loads(store.get_outbox_message(dispatches[0]["message_id"])["payload"])
    root = Path(intent["output_dir"])
    context = json.loads((root / "run_context_v1.json").read_bytes())
    article = json.loads((root / "article_manifest_v1.json").read_bytes())
    if annotation["article_identity"] != sha256(article["substack_body_markdown"].encode()).hexdigest():
        raise ValueError("CALL_ANNOTATION_AUTHORED_BODY_CHANGED")
    operation = json.loads(store.get_outbox_message("native-operation-binding-" + sha256_of(annotation["run_id"]))["payload"])
    public_path = Path(operation["output_dir"]) / "public-readback-dom.json"
    if sha256(public_path.read_bytes()).hexdigest() != annotation["public_dom_sha256"]:
        raise ValueError("CALL_ANNOTATION_PUBLIC_OBSERVATION_CHANGED")
    public = json.loads(public_path.read_bytes())["body"]
    documents = {d["document_id"]: d for d in context["source_documents"]}
    calls = annotation["calls"]
    if not calls or len(calls) != annotation["allcall_count"] or len({c["call_id"] for c in calls}) != len(calls):
        raise ValueError("CALL_ANNOTATION_FULL_UNIQUE_COUNT_REQUIRED")
    for call in calls:
        span, binding = call["public_span"], call["material_claim_binding"]
        text = call["original_text"]
        document = documents.get(binding["document_id"], {})
        if (public[span["start"]:span["end"]] != text or span["text"] != text
                or _text(text) not in _text(article["substack_body_markdown"])
                or _text(binding["support_excerpt"]) not in _text(document.get("canonical_content_text", ""))):
            raise ValueError("CALL_ANNOTATION_PUBLIC_SPAN_OR_MAIN_SOURCE_CHANGED")
    value = {"schema_version": "contentops.confirmed_call_annotation.v1", "content_id": published["content_id"],
        "annotation": deepcopy(annotation), "published_at_utc": published["published_at_utc"],
        "outlets": published["outlets"], "article_body_sha256": annotation["article_identity"]}
    return store.register_outbox_message(message_id="public-call-annotation-" + sha256_of(published["content_id"]),
        work_item_id=annotation["run_id"], destination=ANNOTATIONS,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")


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

    for message in store.list_outbox_messages(destination=ANNOTATIONS):
        value = json.loads(message["payload"])
        at = value["published_at_utc"]
        if not start <= utc(at) <= end:
            continue
        for call in value["annotation"]["calls"]:
            key = sha256(canonical([value["content_id"], call["call_id"]])).hexdigest()
            entries[key] = {"call_id": "call-" + key[:24], "call": deepcopy(call),
                "original_text": call["original_text"], "market": call["market"],
                "annotation_source": message["message_id"], "first_published_at_utc": at, "call_known_at_utc": at,
                "publications": value["outlets"], "public_history": [], "state": "UNRESOLVED", "score": None}

    with store.get_read_only_connection() as conn:
        conn.execute("BEGIN")  # One read snapshot while normal publication continues.
        messages = conn.execute(
            "SELECT message_id,status,payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
            ("internal:plan-status-post",),
        ).fetchall()
        # Channel outbox rows belong to the original plan-post message's work item.
        dispatches = conn.execute(
            "SELECT o.work_item_id,d.platform,d.public_object_url,d.dispatched_at,d.dispatch_id "
            "FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
            "JOIN outbox_messages p ON p.message_id=o.work_item_id "
            "WHERE d.status IN (?,?) AND d.public_object_url IS NOT NULL AND p.destination=?",
            (*CONFIRMED, "internal:plan-status-post"),
        ).fetchall()
        observations = conn.execute(
            "SELECT r.dispatch_id,r.read_at,r.readback_data FROM readbacks r "
            "JOIN platform_dispatches d ON d.dispatch_id=r.dispatch_id "
            "JOIN outbox_messages o ON o.message_id=d.message_id "
            "JOIN outbox_messages p ON p.message_id=o.work_item_id WHERE d.status IN (?,?) AND p.destination=?",
            (*CONFIRMED, "internal:plan-status-post"),
        ).fetchall()
    publication_clocks = {}
    for dispatch_id, read_at, raw in observations:
        if utc(read_at) > end:
            continue
        observation = json.loads(raw)
        observation = observation.get("readback", observation)
        published = observation.get("published_at_utc") or observation.get("observed_published_at_utc")
        if published and utc(published) <= utc(read_at):
            publication_clocks.setdefault(dispatch_id, []).append(published)
    destinations = {}
    for work_item, platform, url, at, dispatch_id in dispatches:
        if at and utc(at) <= end:
            clocks = publication_clocks.get(dispatch_id, [])
            destinations.setdefault(work_item, []).append({"name": platform, "url": url,
                "dispatch_at_utc": at, "published_at_utc": min(clocks, key=utc) if clocks else None})
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
            clocks = [p["published_at_utc"] for p in publications if p["published_at_utc"]]
            public_at = min(clocks, key=utc) if clocks else None
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
        wording = (row.get("original_text") or conditional_call_text(row["call"])).replace("|", "&#124;").replace("\n", " ")
        if row.get("market"):
            wording = row["market"] + ": " + wording
        when = public_time(row["first_published_at_utc"]) if row["first_published_at_utc"] else "Time not retained"
        lines.append(f"| {when} | {wording} | {row['state'].lower().replace('_', ' ')} |")
    lines.extend(["", scorecard["scoring_note"], "", PUBLIC_NOTICE, CONFLICTS_NOTICE])
    return "\n".join(lines) + "\n"
