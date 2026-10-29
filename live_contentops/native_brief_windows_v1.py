"""Additional App-owned briefs; deterministic eligibility, never a scheduler."""
from dataclasses import replace
from datetime import datetime, timezone
import json

from live_contentops.daily_app_supervisor_v1 import (
    CoreEditorialWindow, NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID, owner_locked_editorial_opportunities,
)
from live_contentops.native_newsroom_volume_v1 import volume_policy
from live_contentops.newsroom_production_day_v1 import newsroom_production_date

BRIEF_WINDOWS = {
    "v1-newsroom-brief-asia-0900": ("asia_brief_0900_saigon", 2),
    "v1-newsroom-brief-europe-1500": ("europe_brief_1500_saigon", 8),
    "v1-newsroom-brief-us-1900": ("us_brief_1900_saigon", 12),
}


def automation_sessions():
    return {**NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID, **{k: v[0] for k, v in BRIEF_WINDOWS.items()}}


def native_opportunities(policy, **kwargs):
    full = owner_locked_editorial_opportunities(policy, **kwargs)
    brief_policy = replace(policy, core_windows=tuple(CoreEditorialWindow(start_hour_utc=hour,
        end_hour_utc=hour + 1, session=session) for session, hour in BRIEF_WINDOWS.values()))
    extra = owner_locked_editorial_opportunities(brief_policy, **kwargs)
    return sorted(full + [{**row, "brief_only": True} for row in extra if volume_policy(row["start_utc"], brief_only=True)],
        key=lambda row: (row["start_utc"], row["opportunity_id"]))


def _utc_instant(value):
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("QUOTA_OBSERVATION_UTC_OFFSET_REQUIRED")
    return instant.astimezone(timezone.utc)


def quota_stop_observations(store, *, production_date):
    """Read actual scoped observations from the same existing outbox."""
    events = []
    for row in store.list_outbox_messages():
        if row["destination"] != "internal:native-quota-stop":
            continue
        event = json.loads(row["payload"])
        if (event.get("cause") == "CODEX_QUOTA_STOP" and event.get("lane") in {"CONTENTOPS_BUILDER", "DATABASE"}
                and event.get("observation_source") and event.get("source_identity")
                and event.get("production_date") == production_date):
            events.append(event)
    return sorted(events, key=lambda event: _utc_instant(event["observed_at_utc"]))


def observed_quota_stop(store, *, cutoff_utc):
    """Only saved, actually observed stop evidence cuts added briefs; no lane polling."""
    cutoff = _utc_instant(cutoff_utc)
    events = quota_stop_observations(store, production_date=newsroom_production_date(cutoff).isoformat())
    return next((event for event in reversed(events) if _utc_instant(event["observed_at_utc"]) <= cutoff), None)


def record_quota_stop(store, binding, observation):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes
    from live_contentops.newsroom_production_day_v1 import newsroom_production_date
    if (observation.get("cause") != "CODEX_QUOTA_STOP" or not observation.get("source_identity")
            or not observation.get("observation_source") or observation.get("lane") not in {"CONTENTOPS_BUILDER", "DATABASE"}):
        raise ValueError("ACTUAL_SCOPED_QUOTA_STOP_OBSERVATION_REQUIRED")
    observed_at = _utc_instant(observation["observed_at_utc"])
    if observed_at > datetime.now(timezone.utc):
        raise ValueError("FUTURE_QUOTA_OBSERVATION_FORBIDDEN")
    event = {**observation, "production_date": newsroom_production_date(observation["observed_at_utc"]).isoformat(),
        "public_write_performed": False, "added_briefs_cut_first": True}
    return store.register_outbox_message(message_id="native-quota-stop-" + sha256_of(event),
        work_item_id="cc-opportunity-" + sha256_of(binding["run_id"]), destination="internal:native-quota-stop",
        payload=canonical_bytes(event).decode(), status="EDITORIAL_INTERNAL")
