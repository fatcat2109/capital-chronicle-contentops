"""Ten-channel weekly digest over existing exact publication/observation records."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta
import json
import math
from zoneinfo import ZoneInfo

from live_contentops.daily_app_performance_v1 import current_metrics_capability_matrix
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

CHANNELS = ("substack", "x", "youtube", "linkedin", "linkedin_company", "telegram",
    "discord", "facebook_page", "instagram_business", "threads")
COUNTERS = frozenset({"impressions", "reach", "views", "total_views", "likes", "reactions", "shares",
    "reposts", "comments", "replies", "subscriber_conversions", "free_subscriptions", "paid_subscriptions",
    "recipients", "restacks", "canonical_article_clicks", "bookmarks", "saves", "meaningful_reads", "reply_sample_count"})


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _clock(value):
    clock = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if clock.tzinfo is None:
        raise ValueError("OBSERVATION_OFFSET_REQUIRED")
    return clock


def weekly_channel_engagement(*, dispatches, reconciliations, readbacks, observations, week_ending):
    ending = date.fromisoformat(week_ending)
    start = datetime.combine(ending - timedelta(days=6), time(), ZoneInfo("Asia/Bangkok"))
    end = datetime.combine(ending + timedelta(days=1), time(), ZoneInfo("Asia/Bangkok"))
    reconciliation_by_id = {r["reconciliation_id"]: r for r in reconciliations}
    eligible = {}
    for dispatch in dispatches:
        channel = dispatch.get("platform")
        if channel not in CHANNELS:
            continue
        reconciliation = reconciliation_by_id.get("reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_"), {})
        if reconciliation.get("status") != "RECONCILED_CONFIRMED":
            continue
        if not DurablePublicationCoordinator._confirmed_public_object(
                {**dispatch, "reconciliation_status": reconciliation["status"]}, destination=channel):
            continue
        verified = False
        for readback in readbacks:
            if readback["dispatch_id"] != dispatch["dispatch_id"]:
                continue
            try:
                verified |= _json(readback["readback_data"]).get("verified") is True
            except (ValueError, TypeError, AttributeError):
                pass
        if verified:
            eligible[dispatch["dispatch_id"]] = dispatch

    latest, excluded = {}, Counter()
    for observation in observations:
        channel = observation.get("platform")
        if channel not in CHANNELS:
            continue
        try:
            clock = _clock(observation.get("collected_at_utc"))
        except (ValueError, TypeError):
            if observation.get("collection_status") != "SCHEDULED":
                excluded[(channel, "MISSING_COLLECTION_CLOCK")] += 1
            continue
        if not start <= clock < end:
            continue
        dispatch = eligible.get(observation.get("dispatch_id"))
        if (not dispatch or dispatch["platform"] != channel
                or str(dispatch["public_object_id"]) != str(observation.get("public_object_id"))
                or not observation.get("learning_eligible")):
            excluded[(channel, "UNCONFIRMED_OR_MISMATCHED_PUBLIC_OBJECT")] += 1
            continue
        key = (channel, str(observation["public_object_id"]))
        if key not in latest or clock > latest[key][0]:
            latest[key] = (clock, observation)

    capabilities = {r["destination"]: r for r in current_metrics_capability_matrix()}
    channels = []
    for channel in CHANNELS:
        samples = [(key[1], value[1]) for key, value in latest.items() if key[0] == channel]
        totals, support, rates, causes = Counter(), Counter(), {}, Counter()
        objects = set()
        for object_id, observation in samples:
            try:
                metrics = _json(observation.get("metrics_native_json") or "{}")
                availability = _json(observation.get("metric_availability_json") or "{}")
                if not isinstance(metrics, dict) or not isinstance(availability, dict):
                    raise ValueError("INVALID_METRIC_JSON")
            except (ValueError, TypeError):
                causes["INVALID_METRIC_JSON"] += 1
                continue
            available = False
            for name, state in availability.items():
                if state != "AVAILABLE":
                    causes[str(state)] += 1
                    continue
                value = metrics.get(name)
                if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                    causes["INVALID_OR_MISSING_NATIVE_VALUE"] += 1
                    continue
                available = True
                if name in COUNTERS:
                    totals[name] += value
                    support[name] += 1
                else:
                    # Rates and other non-additive measures retain native values,
                    # clocks and object identity; no invented combined denominator.
                    rates.setdefault(name, []).append({"public_object_id": object_id, "value": value,
                        "collected_at_utc": observation["collected_at_utc"]})
            if available:
                objects.add(object_id)
            else:
                causes[str(observation.get("collection_status") or "NO_AVAILABLE_NATIVE_METRIC")] += 1
        confirmed_objects = {str(d["public_object_id"]) for d in eligible.values() if d["platform"] == channel}
        if not confirmed_objects:
            causes["NO_ELIGIBLE_CONFIRMED_PUBLIC_OBJECT"] += 1
        elif not samples:
            causes["NO_COLLECTED_OBSERVATION_IN_WEEK"] += 1
        for (destination, cause), count in excluded.items():
            if destination == channel:
                causes[cause] += count
        channels.append({"channel": channel, "status": "OBSERVED" if objects else "UNAVAILABLE",
            "objects_with_metrics": len(objects), "objects_with_observations": len(samples),
            "eligible_objects_in_store": len(confirmed_objects),
            "native_counter_sums": dict(totals) or None, "support_per_metric": dict(support),
            "non_additive_native_values": rates or None, "missing_causes": dict(causes),
            "collection_path": capabilities[channel]["collector_state"],
            "native_read_only_path": "audience-observe on an exact due observation; no login, scope change or public action"})
    return {"schema_version": "contentops.weekly_channel_engagement.v1", "week_ending": week_ending,
        "timezone": "Asia/Bangkok", "channels": channels,
        "metric_basis": "Latest cumulative native snapshot per channel/public object collected in this week; not incremental weekly activity. Per-object reach can overlap. Rates are not summed or averaged.",
        "missing_is_zero": False, "public_write_performed": False, "model_calls": 0}


def render_engagement_digest(value):
    lines = [f"ContentOps weekly engagement — through {value['week_ending']} (GMT+7)", "", value["metric_basis"], "",
        "| Channel | Objects with metrics | Observed native counters | Missing metric causes |",
        "| --- | ---: | --- | --- |"]
    for row in value["channels"]:
        counters = "; ".join(f"{name}={count:g} ({row['support_per_metric'][name]} objects)"
            for name, count in sorted((row["native_counter_sums"] or {}).items())) or "UNAVAILABLE"
        if row["non_additive_native_values"]:
            counters += "; native rates retained separately"
        causes = "; ".join(sorted(row["missing_causes"])) or "None in observed fields"
        lines.append(f"| {row['channel']} | {row['objects_with_metrics']} | {counters} | {causes} |")
    return "\n".join([*lines, "", "Missing metrics remain unavailable. Member and company LinkedIn records are separate. No model or public write was used.", ""])
