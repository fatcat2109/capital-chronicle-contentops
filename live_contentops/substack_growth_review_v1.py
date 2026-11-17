"""Read CC-468's exact coordinator outcomes and existing performance records."""
from datetime import date, datetime, timedelta, timezone
import json
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from . import plan_analysis_pages_v1 as pages
from .substack_daily_note_v1 import utc


def acquisition_snapshot(observation):
    """Use a retained visible first-party observation; no browser or new store."""
    url = urlparse(observation["source_url"])
    if (url.scheme != "https" or url.hostname != "capitalchronicle.substack.com"
            or not url.path.startswith("/publish/") or url.username or url.password):
        raise ValueError("SUBSTACK_FIRST_PARTY_SOURCE_REQUIRED")
    raw = Path(observation["readback_path"]).read_bytes()
    if sha256(raw).hexdigest() != observation["readback_sha256"]:
        raise ValueError("SUBSCRIBER_SOURCE_READBACK_CHANGED")
    text = raw.decode("utf-8")
    start, end, seen = (utc(observation[k]) for k in ("period_start_utc", "period_end_utc", "observed_at_utc"))
    if not start < end <= seen:
        raise ValueError("SUBSCRIBER_SOURCE_PERIOD_INVALID")
    rows = []
    for row in observation["sources"]:
        value = row.get("new_free_subscribers")
        if row.get("availability") == "AVAILABLE":
            excerpt = row.get("excerpt", "")
            display = row.get("display", "")
            if (type(value) is not int or value < 0 or not row.get("source")
                    or not excerpt or excerpt not in text or row["source"] not in excerpt
                    or not display or display not in excerpt or display.replace(',', '') != str(value)):
                raise ValueError("SUBSCRIBER_SOURCE_COUNT_UNBOUND")
        else:
            value = None
        rows.append({"source": row["source"], "new_free_subscribers": value,
                     "availability": row.get("availability", "UNAVAILABLE")})
    return {**{k: observation[k] for k in ("source_url", "observed_at_utc", "period_start_utc", "period_end_utc",
                                          "readback_path", "readback_sha256")}, "by_source": rows}


def report(store, *, now=None, acquisition_observation=None):
    now = utc(now or datetime.now(timezone.utc))
    notes = []
    dispatch_ids = set()
    from .publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    for row in store.list_outbox_messages(destination=pages.DESTINATION):
        value = json.loads(row["payload"])
        if value.get("kind") != "daily_note":
            continue
        status = pages.link_status(store, value)
        ids = Coordinator._ids(value["link_id"], value["plan"]["plan_hash"], "substack_notes")
        dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
        # The coordinator's attempt/updated clocks are never presented as an
        # independently observed platform publication clock.
        notes.append({"note_id": value["link_id"], "day_et": value["day_et"], **status,
            "source_data_cutoff_utc": value["source_clock"]["data_cutoff_utc"],
            "dispatch_updated_at_utc": dispatch.get("updated_at"), "observed_publication_at_utc": None})
        if status["confirmed"]:
            dispatch_ids.add(ids["dispatch_id"])
    notes.sort(key=lambda n: n["day_et"])
    days = sorted({date.fromisoformat(n["day_et"]) for n in notes if n["confirmed"]})
    longest, streak, previous = 0, 0, None
    for day in days:
        streak = streak + 1 if previous is not None and day == previous + timedelta(days=1) else 1
        longest, previous = max(longest, streak), day
    # Keep only the latest collected snapshot of an exact dispatch, never sum
    # cumulative observation windows. Missing/native-unexposed metrics stay null.
    latest = {}
    for observation in store.list_performance_observations():
        if observation.get("dispatch_id") not in dispatch_ids or observation.get("collection_status") != "COLLECTED":
            continue
        old = latest.get(observation["dispatch_id"])
        if old is None or str(observation.get("collected_at_utc") or "") > str(old.get("collected_at_utc") or ""):
            latest[observation["dispatch_id"]] = observation
    metrics, acquisition = [], []
    for dispatch_id, observation in sorted(latest.items()):
        values = json.loads(observation.get("metrics_native_json") or "{}")
        availability = json.loads(observation.get("metric_availability_json") or "{}")
        free = values.get("free_subscriptions") if availability.get("free_subscriptions") == "AVAILABLE" else None
        metrics.append({"dispatch_id": dispatch_id, "observation_id": observation["observation_id"],
            "collected_at_utc": observation.get("collected_at_utc"), "source_identity": observation.get("source_identity"),
            "new_free_subscribers": free, "availability": availability.get("free_subscriptions", "UNAVAILABLE")})
        if availability.get("free_subscriptions_by_source") == "AVAILABLE":
            acquisition.append({"observation_id": observation["observation_id"],
                "collected_at_utc": observation.get("collected_at_utc"),
                "by_source": values.get("free_subscriptions_by_source"),
                "source_identity": observation.get("source_identity")})
    if acquisition_observation is not None:
        acquisition.append(acquisition_snapshot(acquisition_observation))
    due_day = days[0] + timedelta(days=14) if days else None
    due = bool(due_day and now.astimezone(ZoneInfo("America/New_York")).date() >= due_day)
    return {"item": "CC-468", "observed_at_utc": now.isoformat(), "notes": notes,
        "confirmed_note_count": len(days), "longest_consecutive_confirmed_days": longest,
        "seven_day_note_readbacks": longest >= 7,
        "fourteen_day_review_due_on_et": due_day.isoformat() if due_day else None,
        "fourteen_day_review_due": due, "note_performance": metrics,
        "new_free_subscribers_by_source": acquisition or None,
        "subscriber_source_cause": None if acquisition else "SUBSTACK_ACQUISITION_SOURCE_METRIC_NOT_COLLECTED",
        "decision_state": "REVIEW_DUE" if due else "MEASUREMENT_PERIOD_IN_PROGRESS" if days else "NOT_STARTED",
        "next_action": ("Compare Substack's observed new free subscribers by source and decide what continues. "
                        "Use the existing performance records and a retained visible Substack source table; "
                        "unavailable is not zero.")}
