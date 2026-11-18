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


def verified_dispatch_readback(row, dispatch):
    """Read the coordinator's envelope and the older flat observation format."""
    if row.get("dispatch_id") != dispatch["dispatch_id"]:
        return False


    try:
        payload = _json(row["readback_data"])
        if not isinstance(payload, dict):
            return False
        observed = payload.get("readback", payload)
        if not isinstance(observed, dict) or observed.get("verified") is not True:
            return False
        if "readback" in payload:
            if (payload.get("dispatch_id") != dispatch["dispatch_id"]
                    or payload.get("destination") != dispatch["platform"]
                    or observed.get("identity_match") is not True
                    or str(observed.get("observed_public_object_id")) != str(dispatch["public_object_id"])
                    or observed.get("observed_public_object_url") != dispatch.get("public_object_url")):
                return False
        return True
    except (ValueError, TypeError, KeyError):
        return False


def verified_dispatch_identity(row, dispatch):
    """An observed object with damaged content still has useful audience metrics."""
    try:
        payload = _json(row["readback_data"])
        observed = payload["readback"]
        return (row.get("dispatch_id") == dispatch["dispatch_id"]
                and payload.get("dispatch_id") == dispatch["dispatch_id"]
                and payload.get("destination") == dispatch["platform"]
                and observed.get("identity_match") is True
                and str(observed.get("observed_public_object_id")) == str(dispatch["public_object_id"])
                and observed.get("observed_public_object_url") == dispatch.get("public_object_url"))
    except (ValueError, TypeError, KeyError):
        return False


def engagement_readback_basis(dispatch, reconciliation_status, readbacks):
    """Both reports use the same exact-object criteria, including damaged public copy."""
    if not DurablePublicationCoordinator._confirmed_public_object(
            {**dispatch, "reconciliation_status": reconciliation_status}, destination=dispatch["platform"]):
        return None
    if any(verified_dispatch_identity(row, dispatch) for row in readbacks):
        return "EXACT_IDENTITY"
    if any(verified_dispatch_readback(row, dispatch) for row in readbacks):
        return "VERIFIED_READBACK"
    return None


def _observation_matches(observation, dispatch, basis):
    return (basis is not None and observation.get("platform") == dispatch["platform"]
            and observation.get("dispatch_id") == dispatch["dispatch_id"]
            and str(observation.get("public_object_id")) == str(dispatch["public_object_id"])
            and (observation.get("learning_eligible") in (True, 1) or basis == "EXACT_IDENTITY"))


def _valid_native_metric(value):
    return type(value) in (float, int) and value >= 0 and (type(value) is int or math.isfinite(value))


PIECE_METRICS = {"views": ("views", "total_views"), "likes": ("likes",), "replies": ("replies", "comments")}


def piece_engagement(dispatch, basis, observations, *, as_of):
    """Read native counters from the weekly export's inputs before it sums them."""
    samples, causes = [], set()
    for observation in observations:
        if not _observation_matches(observation, dispatch, basis):
            causes.add("UNCONFIRMED_OR_MISMATCHED_PUBLIC_OBJECT")
            continue
        if observation.get("collection_status") == "SCHEDULED":
            try:
                if _clock(observation.get("scheduled_for_utc")) <= as_of:
                    causes.add("METRIC_COLLECTION_PENDING")
            except (ValueError, TypeError):
                causes.add("MISSING_COLLECTION_CLOCK")
            continue
        try:
            clock = _clock(observation.get("collected_at_utc"))
        except (ValueError, TypeError):
            causes.add("MISSING_COLLECTION_CLOCK")
            continue
        if clock <= as_of:
            samples.append((clock, observation))

    if not samples:
        cause = next((name for name in ("UNCONFIRMED_OR_MISMATCHED_PUBLIC_OBJECT",
            "MISSING_COLLECTION_CLOCK", "METRIC_COLLECTION_PENDING") if name in causes),
            "NO_COLLECTED_OBSERVATION_BY_CUTOFF")
        return {}, {}, cause

    values, gaps = {}, {}
    for clock, observation in sorted(samples, key=lambda pair: pair[0], reverse=True):
        try:
            metrics = _json(observation["metrics_native_json"])
            states = _json(observation["metric_availability_json"])
            if not isinstance(metrics, dict) or not isinstance(states, dict):
                raise ValueError("INVALID_METRIC_JSON")
        except (ValueError, TypeError):
            for name in PIECE_METRICS:
                gaps.setdefault(name, "INVALID_METRIC_JSON")
            continue
        for name, candidates in PIECE_METRICS.items():
            if name in values:
                continue
            for native in candidates:
                if states.get(native) == "AVAILABLE" and _valid_native_metric(metrics.get(native)):
                    values[name] = {"value": metrics[native], "source_metric": native,
                                    "collected_at_utc": observation["collected_at_utc"]}
                    break
            else:
                state = next((states[native] for native in candidates if states.get(native)), None)
                if state == "AVAILABLE":
                    state = "INVALID_OR_MISSING_NATIVE_VALUE"
                status = observation.get("collection_status")
                gaps.setdefault(name, state or (status if status != "COLLECTED" else None) or "METRIC_NOT_RECORDED")
        if len(values) == len(PIECE_METRICS):
            break
    missing = {name: gaps[name] for name in PIECE_METRICS if name not in values}
    return values, missing, None


def weekly_channel_engagement(*, dispatches, reconciliations, readbacks, observations, week_ending, call_bindings=None):
    ending = date.fromisoformat(week_ending)
    start = datetime.combine(ending - timedelta(days=6), time(), ZoneInfo("Asia/Bangkok"))
    end = datetime.combine(ending + timedelta(days=1), time(), ZoneInfo("Asia/Bangkok"))
    reconciliation_by_id = {r["reconciliation_id"]: r for r in reconciliations}
    eligible = {}
    readbacks_by_dispatch = {}
    for row in readbacks:
        readbacks_by_dispatch.setdefault(row.get("dispatch_id"), []).append(row)
    for dispatch in dispatches:
        channel = dispatch.get("platform")
        if channel not in CHANNELS:
            continue
        reconciliation = reconciliation_by_id.get("reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_"), {})
        basis = engagement_readback_basis(dispatch, reconciliation.get("status"), readbacks_by_dispatch.get(dispatch["dispatch_id"], ()))
        if basis:
            eligible[dispatch["dispatch_id"]] = (dispatch, basis)

    latest, excluded, calls_by_object = {}, Counter(), {}
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
        dispatch, basis = eligible.get(observation.get("dispatch_id"), ({}, None))
        if not _observation_matches(observation, dispatch, basis):
            excluded[(channel, "UNCONFIRMED_OR_MISMATCHED_PUBLIC_OBJECT")] += 1
            continue
        key = (channel, str(observation["public_object_id"]))
        try:
            calls = (call_bindings.get(observation["dispatch_id"], []) if call_bindings is not None else
                     _json(observation.get("metrics_native_json") or "{}").get("_call_ids", []))
            for call in calls:
                calls_by_object.setdefault(key, {})[call["call_id"]] = call
        except (ValueError, TypeError, KeyError):
            pass
        if key not in latest or clock > latest[key][0]:
            latest[key] = (clock, observation)

    capabilities = {r["destination"]: r for r in current_metrics_capability_matrix()}
    channels = []
    call_totals = {}
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
                if not _valid_native_metric(value):
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
                bound_calls = list(calls_by_object.get((channel, object_id), {}).values())
                for call in bound_calls:
                    key = (channel, call["call_id"])
                    total = call_totals.setdefault(key, {"channel": channel, **call, "posts": 0, "native_counter_sums": {}, "shared_object_metrics": False})
                    total["shared_object_metrics"] |= len(bound_calls) > 1 or metrics.get("_shared_public_object") is True
                    total["posts"] += 1
                    for name in COUNTERS:
                        if availability.get(name) == "AVAILABLE" and _valid_native_metric(metrics.get(name)):
                            total["native_counter_sums"][name] = total["native_counter_sums"].get(name, 0) + metrics[name]
            else:
                causes[str(observation.get("collection_status") or "NO_AVAILABLE_NATIVE_METRIC")] += 1
        confirmed_objects = {str(d["public_object_id"]) for d, _ in eligible.values() if d["platform"] == channel}
        if not confirmed_objects:
            causes["NO_ELIGIBLE_CONFIRMED_PUBLIC_OBJECT"] += 1
        elif not samples:
            causes["NO_COLLECTED_OBSERVATION_IN_WEEK"] += 1
        for (destination, cause), count in excluded.items():
            if destination == channel:
                causes[cause] += count
        account_snapshots = []
        for observation in observations:
            if observation.get("platform") != channel:
                continue
            try:
                account = _json(observation.get("metrics_native_json") or "{}").get("_account_snapshot", {})
                stamp = _clock(account.get("collected_at_utc"))
                if stamp < end and account.get("metrics"):
                    account_snapshots.append((stamp, account))
            except (ValueError, TypeError):
                continue
        account_snapshots.sort(key=lambda pair: pair[0])
        account_latest = account_snapshots[-1][1] if account_snapshots else None
        account_prior = next((account for stamp, account in reversed(account_snapshots) if stamp <= start), None)
        follower_key = "members_count" if channel in {"telegram", "discord"} else "followers_count"
        if channel == "discord":
            follower_key = "approximate_members_count"
        follower_now = (account_latest or {}).get("metrics", {}).get(follower_key)
        follower_before = (account_prior or {}).get("metrics", {}).get(follower_key)
        net_followers = follower_now - follower_before if type(follower_now) is int and type(follower_before) is int else None
        posted = set()
        for dispatch, _ in eligible.values():
            try:
                if dispatch["platform"] == channel and start <= _clock(dispatch.get("dispatched_at")) < end:
                    posted.add(str(dispatch["public_object_id"]))
            except (ValueError, TypeError):
                continue
        channels.append({"channel": channel, "status": "OBSERVED" if objects else "UNAVAILABLE",
            "posts_in_week": len(posted), "account_snapshot": account_latest,
            "net_new_followers_or_members": net_followers,
            "follower_change_state": "OBSERVED_SNAPSHOT_DIFFERENCE" if net_followers is not None else "PRIOR_WEEK_ACCOUNT_SNAPSHOT_UNAVAILABLE",
            "account_count_is_approximate": channel == "discord",
            "objects_with_metrics": len(objects), "objects_with_observations": len(samples),
            "eligible_objects_in_store": len(confirmed_objects),
            "native_counter_sums": dict(totals) or None, "support_per_metric": dict(support),
            "non_additive_native_values": rates or None, "missing_causes": dict(causes),
            "collection_path": capabilities[channel]["collector_state"],
            "native_read_only_path": "audience-observe on an exact due observation; no login, scope change or public action"})
    return {"schema_version": "contentops.weekly_channel_engagement.v1", "week_ending": week_ending,
        "timezone": "Asia/Bangkok", "channels": channels,
        "calls": list(call_totals.values()),
        "metric_basis": "Latest cumulative native snapshot per channel/public object collected in this week; not incremental weekly activity. Per-object reach can overlap. Rates are not summed or averaged.",
        "content_incomplete_objects_included": sum(1 for dispatch, _ in eligible.values()
            if reconciliation_by_id.get("reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_"), {}).get("status") == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"),
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


def weekly_audience_lines(value):
    """One plain line per platform for the existing 07:00 digest consumer."""
    lines = []
    for row in value["channels"]:
        counters = row.get("native_counter_sums") or {}
        audience = next((f"{name} {counters[name]:g}" for name in ("views", "total_views", "reach", "impressions") if name in counters), "views/reach unavailable")
        replies = next((f"{name} {counters[name]:g}" for name in ("replies", "comments") if name in counters), "replies unavailable")
        change = row.get("net_new_followers_or_members")
        label = "estimated net members" if row.get("account_count_is_approximate") else "net followers/members"
        followers = f"{label} {change:+d}" if change is not None else "new followers/members unavailable (no comparable account baseline)"
        lines.append(f"{row['channel']}: posts {row.get('posts_in_week', 0)}; {audience}; {replies}; {followers}.")
    return lines
