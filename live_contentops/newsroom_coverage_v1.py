"""Weekly digest measures over the existing outbox and publication records.

This is a read-only projection, with no source capture, model, scheduler or ledger.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
import json
from zoneinfo import ZoneInfo

from live_contentops.newsroom_production_day_v1 import newsroom_production_date
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

ZONE = ZoneInfo("Asia/Bangkok")


def _clock(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC_OFFSET_REQUIRED")
    return parsed


def weekly_newsroom_coverage(*, outbox, dispatches, reconciliations, readbacks, week_ending):
    end_day = date.fromisoformat(week_ending)
    days = [(end_day - timedelta(days=n)).isoformat() for n in reversed(range(7))]
    start = datetime.combine(date.fromisoformat(days[0]), time(2), ZONE)
    end = datetime.combine(end_day + timedelta(days=1), time(2), ZONE)
    daily = {day: {"day": day, "news_articles": 0, "main_articles": 0,
        "unclassified_canonicals": 0, "luna_headlines_filtered": 0,
        "source_walks": 0, "source_walks_succeeded": 0} for day in days}
    gaps, finals, accepted, walks = [], {}, {}, {}
    by_message = {r["message_id"]: r for r in outbox}

    def in_week(value, identity):
        try:
            clock = _clock(value)
        except (ValueError, TypeError):
            gaps.append({"record": identity, "cause": "MISSING_OR_INVALID_OBSERVATION_CLOCK"})
            return None
        return newsroom_production_date(clock).isoformat() if start <= clock < end else None

    for row in outbox:
        if (row["destination"] not in {"internal:native-desktop-editorial", "internal:cc-report-editorial-stage"}
                and not row["message_id"].startswith("cc-editorial-final-")):
            continue
        try:
            value = json.loads(row["payload"])
        except (ValueError, TypeError):
            gaps.append({"record": row["message_id"], "cause": "INVALID_PAYLOAD"})
            continue
        if row["message_id"].startswith("cc-editorial-final-") and value.get("qualified_article_count"):
            run = value.get("simple_result", {}).get("run_id")
            if run:
                finals[run] = value
        output = value.get("output", {})
        if output.get("schema_version") == "contentops.native_headline_filter.v1":
            day = in_week(row.get("created_at"), row["message_id"])
            try:
                accepted_at = _clock(row.get("created_at"))
            except (ValueError, TypeError):
                continue
            observation = value.get("invocation_observation", {})
            if observation.get("model") != "gpt-6-luna" or observation.get("reasoning_effort") != "max":
                if day:
                    gaps.append({"record": row["message_id"], "cause": "LUNA_ACTUAL_MODEL_OR_EFFORT_UNVERIFIED"})
                continue
            for decision in output.get("decisions", []):
                identity = decision.get("input_sha256")
                if identity and (identity not in accepted or accepted_at < accepted[identity][0]):
                    accepted[identity] = (accepted_at, day)
        if row["destination"] == "internal:cc-report-editorial-stage" and str(value.get("stage", "")).startswith("source:"):
            day = in_week(row.get("created_at"), row["message_id"])
            result = value.get("result", {})
            if day and result.get("status") in {"PASS", "BLOCKED"}:
                # One candidate walk, including recovery, never one count per GET.
                cluster = value.get("identity", {}).get("cluster_id")
                cluster = cluster or value["stage"].split(":", 2)[1]
                key = (row["work_item_id"], cluster)
                old = walks.get(key)
                if old is None or _clock(row["created_at"]) > old[0]:
                    walks[key] = (_clock(row["created_at"]), day,
                        result["status"] == "PASS" and bool(result.get("evidence_documents")))
    for _, day in accepted.values():
        if day:
            daily[day]["luna_headlines_filtered"] += 1
    for _, day, succeeded in walks.values():
        daily[day]["source_walks"] += 1
        daily[day]["source_walks_succeeded"] += int(succeeded)

    reconciled = {r["dispatch_id"]: r for r in reconciliations if r.get("dispatch_id")}
    # Existing reconciliation identities also support older records without a dispatch_id column.
    by_reconciliation = {r["reconciliation_id"]: r for r in reconciliations}
    seen_objects = set()
    for dispatch in sorted(dispatches, key=lambda d: str(d.get("dispatched_at") or "")):
        if dispatch.get("platform") != "substack":
            continue
        rid = "reconciliation_" + dispatch["dispatch_id"].removeprefix("dispatch_")
        reconciliation = reconciled.get(dispatch["dispatch_id"], by_reconciliation.get(rid, {}))
        outcome = {**dispatch, "reconciliation_status": reconciliation.get("status")}
        if not DurablePublicationCoordinator._confirmed_public_object(outcome, destination="substack"):
            continue
        day = in_week(dispatch.get("dispatched_at"), dispatch["dispatch_id"])
        if not day:
            continue
        exact_reads = [r for r in readbacks if r["dispatch_id"] == dispatch["dispatch_id"]
            and json.loads(r["readback_data"]).get("verified") is True]
        if not exact_reads:
            gaps.append({"record": dispatch["dispatch_id"], "cause": "NO_VERIFIED_READBACK"})
            continue
        object_id = str(dispatch["public_object_id"])
        if object_id in seen_objects:
            continue
        seen_objects.add(object_id)
        message = by_message.get(dispatch["message_id"], {})
        final = finals.get(message.get("work_item_id"), {})
        kind = ("news_articles" if final.get("classification") == "INDEPENDENT_NEWS_DRAFT"
            else "main_articles" if final.get("report_id") else "unclassified_canonicals")
        daily[day][kind] += 1

    rows = list(daily.values())
    for row in rows:
        row["source_walk_success_rate"] = (row["source_walks_succeeded"] / row["source_walks"]
            if row["source_walks"] else None)
    total_walks = sum(r["source_walks"] for r in rows)
    successes = sum(r["source_walks_succeeded"] for r in rows)
    return {"schema_version": "contentops.weekly_newsroom_coverage.v1", "week_ending": week_ending,
        "timezone": "Asia/Bangkok", "production_day_boundary_hour": 2,
        "status": "PARTIAL" if gaps else "COMPLETE_RECORD_PROJECTION", "daily": rows,
        "source_walk_success_rate": successes / total_walks if total_walks else None,
        "source_walks": total_walks, "source_walks_succeeded": successes, "gaps": gaps,
        "clock_basis": {"articles": "actual dispatch time; exact confirmation from current snapshot",
            "luna": "durable native return time", "source_walks": "latest completed durable candidate walk time"},
        "source_walk_denominator": "Distinct work-item/candidate walks completed in the interval; recovery is one walk; a zero-GET permitted relay can succeed.",
        "public_write_performed": False, "model_calls": 0}


def render_coverage_digest(value):
    lines = [f"ContentOps weekly coverage — through {value['week_ending']} (GMT+7)", "",
        "| Production day | News articles | Main articles | Unclassified | Luna headlines | Source walks | Success rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in value["daily"]:
        rate = f"{row['source_walk_success_rate']:.1%}" if row["source_walk_success_rate"] is not None else "UNAVAILABLE (no completed walk)"
        lines.append(f"| {row['day']} | {row['news_articles']} | {row['main_articles']} | {row['unclassified_canonicals']} | {row['luna_headlines_filtered']} | {row['source_walks']} | {rate} |")
    lines.extend(["", "Production days start at 02:00 GMT+7. Articles require exact canonical identity, verified readback and reconciliation.",
        "News counts independent newsroom stories; Main-derived articles are shown separately. Drafts are excluded.",
        value["source_walk_denominator"], f"Data quality: {value['status']}; excluded-record gaps: {len(value['gaps'])}.", ""])
    return "\n".join(lines)
