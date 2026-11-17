"""Summarize the existing reply run artifacts; no tick, model, transport or store write.

Only the requested report is written. Raw target text and private chat data stay
in their original runtime records. Historical unobserved stages stay unknown.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import statistics
from zoneinfo import ZoneInfo

RUNS = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\x_reply_pack\bot")
ET = ZoneInfo("America/New_York")


def utc(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def session_bounds(day):
    date = datetime.fromisoformat(day).date()
    return tuple(datetime.combine(date, time(hour, minute), ET).astimezone(timezone.utc)
                 for hour, minute in ((9, 30), (16, 0)))


def summarize(root, *, start, end, asof):
    start, end, asof = map(utc, (start, end, asof))
    cutoff = min(end, asof)
    posts, artifacts, timings, deliveries, statuses, boundaries, gaps = {}, {}, [], {}, Counter(), [], []
    stage_sets = {name: set() for name in ("seen", "fresh", "on_topic", "with_fact", "ranking_input",
                    "above_floor", "authored", "validated", "sent")}
    runs = []

    def read(path):
        raw = path.read_bytes()
        artifacts[str(path)] = sha256(raw).hexdigest()
        return json.loads(raw)

    def target(key):
        return posts.setdefault(str(key), {"post_id": str(key), "causes": [], "stages": []})

    def reached(name, ids):
        for key in ids:
            key = str(key)
            stage_sets[name].add(key)
            row = target(key)
            if name not in row["stages"]:
                row["stages"].append(name)

    for folder in sorted(Path(root).glob("20*T*-*")):
        path = folder / "result.json"
        # Restrict filename dates before reading the bounded day's records.
        if folder.name[:8] < start.strftime("%Y%m%d") or folder.name[:8] > end.strftime("%Y%m%d"):
            continue
        if not path.is_file():
            continue
        data = json.loads(path.read_bytes())
        at = utc(data["started_at_utc"])
        if not start <= at < cutoff:
            continue
        ended = utc(data["ended_at_utc"]) if data.get("ended_at_utc") else None
        if ended is None or ended > asof:
            gaps.append({"artifact": str(path), "cause": "RUN_NOT_COMPLETE_AT_REPORT_CUTOFF"})
            continue
        read(path)
        statuses[data["status"]] += 1
        boundaries.append((at, ended))
        requests = [read(p) for p in sorted(folder.glob("reply-pack-request-*.json"))]
        candidates = {str(p["post_id"]): p for request in requests for p in request.get("candidates", [])}
        all_drops = [*data.get("dropped_candidates", []),
                     *(p for request in requests for p in request.get("dropped_candidates", []))]
        funnel = data.get("funnel", {})
        reached("seen", [*candidates, *(p["post_id"] for p in all_drops), *funnel.get("seen_post_ids", [])])
        reached("on_topic", [p["post_id"] for p in funnel.get("on_topic", [])])
        for post in [*candidates.values(), *funnel.get("on_topic", [])]:
            target(post["post_id"])["posted_at_utc"] = post.get("post_time_utc")
        # Older request candidates have already passed topic and usable-fact checks.
        reached("on_topic", candidates)
        reached("fresh", candidates)
        reached("fresh", [p["post_id"] for p in funnel.get("on_topic", [])])
        reached("with_fact", [key for key, p in candidates.items() if p.get("usable_source_ids")])
        reached("with_fact", funnel.get("with_fact_post_ids", []))
        reached("ranking_input", funnel.get("ranking_input_post_ids", []))
        for post in all_drops:
            cause, key = post["cause"], str(post["post_id"])
            row = target(key)
            entry = {"cause": cause, "at_utc": at.isoformat(), "artifact": str(path)}
            if not any(prior["cause"] == cause for prior in row["causes"]):
                row["causes"].append(entry)
            if cause not in {"TARGET_OVER_15_MINUTES_AT_SEND", "POST_OUTSIDE_120_MINUTE_BUILD_WINDOW",
                             "POST_IDENTITY_MISMATCH", "POST_TIME_INVALID"}:
                reached("fresh", [key])
            if cause not in {"NO_SIX_MARKET_OR_MACRO_TOPIC", "TARGET_OVER_15_MINUTES_AT_SEND",
                             "POST_OUTSIDE_120_MINUTE_BUILD_WINDOW", "POST_IDENTITY_MISMATCH",
                             "POST_TIME_INVALID", "RETWEET_NOT_ORIGINAL_TARGET", "POST_ALREADY_HAS_20_REPLIES"}:
                reached("on_topic", [key])
            if cause in {"NO_ADDED_FACT_ABOVE_QUALITY_FLOOR", "PREVIOUSLY_ATTEMPTED",
                         "ALREADY_DELIVERED_OR_UNCERTAIN", "RANK_BATCH_LIMIT_12"}:
                reached("with_fact", [key])
        response_path = folder / "editorial/response.json"
        if (folder / "editorial/rank/call.json").is_file() or response_path.is_file():
            reached("ranking_input", [key for key, post in candidates.items() if post.get("attempt_key")])
        rank_path = folder / "editorial/rank/response.json"
        if rank_path.is_file():
            ranking = read(rank_path)
            reached("above_floor", [str(row["post_id"]) for row in ranking.get("ranking", [])
                if str(row.get("post_id")) in candidates and type(row.get("quality_score")) is int
                and 80 <= row["quality_score"] <= 100])
        writer_path = folder / "editorial/writer/response.json"
        if writer_path.is_file():
            authored = read(writer_path)
            reached("authored", [str(row["post_id"]) for row in authored.get("items", [])
                                  if str(row.get("post_id")) in candidates])
        if response_path.is_file():
            response = read(response_path)
            for omission in response.get("omissions", []):
                row = target(omission["post_id"])
                if not any(prior["cause"] == omission["cause"] for prior in row["causes"]):
                    row["causes"].append({"cause": omission["cause"], "at_utc": at.isoformat(),
                                          "artifact": str(response_path)})
            reached("above_floor", response.get("ranked_above_floor_post_ids", []))
            reached("above_floor", response.get("remaining_quality_post_ids", []))
            reached("authored", [str(p["post_id"]) for p in response.get("items", [])])
            if type(response.get("quality_score")) is int and response["quality_score"] >= 80:
                chosen = [str(p["post_id"]) for p in response.get("items", [])]
                reached("above_floor", chosen)
        for key, field in (("above_floor", "ranked_above_floor_post_ids"), ("authored", "authored_post_ids"),
                           ("validated", "validated_draft_post_ids")):
            reached(key, funnel.get(field, []))
        delivery = data.get("delivery", {})
        for proof in delivery.get("delivered", []):
            key = str(proof["post_id"])
            reached("sent", [key])
            reached("validated", [key])
            deliveries[key] = {k: proof[k] for k in ("post_id", "delivered_at_utc", "post_to_delivery_minutes",
                "post_to_send_attempt_minutes", "post_to_draft_minutes", "stage_seconds") if k in proof}
        timings.append({"started_at_utc": at.isoformat(), "stage_seconds": data.get("stage_seconds", {})})
        runs.append({"artifact": str(path), "started_at_utc": at.isoformat(), "ended_at_utc": ended.isoformat(),
                     "status": data["status"]})

    undrafted = []
    unvalidated = []
    for key in sorted(stage_sets["on_topic"] - stage_sets["validated"]):
        row = target(key)
        usable_causes = [c for c in row["causes"] if c["cause"] not in {
            "TARGET_OVER_15_MINUTES_AT_SEND", "POST_OUTSIDE_120_MINUTE_BUILD_WINDOW",
            "NO_SIX_MARKET_OR_MACRO_TOPIC", "POST_TIME_INVALID", "POST_IDENTITY_MISMATCH",
            "RETWEET_NOT_ORIGINAL_TARGET", "POST_ALREADY_HAS_20_REPLIES"}]
        first = usable_causes[0] if usable_causes else {"cause": "FIRST_CAUSE_NOT_RETAINED_IN_LEGACY_RUN"}
        row["first_unvalidated_cause"] = first
        unvalidated.append({"post_id": key, **first})
        if key not in stage_sets["authored"]:
            row["first_undrafted_cause"] = first
            undrafted.append({"post_id": key, **first})

    stage_minutes = {}
    for name in ("filter", "ranking", "drafting", "checks", "whole_tick"):
        values = [r["stage_seconds"][name]/60 for r in timings
                  if isinstance(r["stage_seconds"].get(name), (float, int))]
        active = [value for value in values if value > 0]
        stage_minutes[name] = {"runs_recorded": len(values), "runs_with_work": len(active),
            "total_minutes": sum(values), "median_active_minutes": statistics.median(active) if active else None,
            "max_minutes": max(values) if values else None}
    stage_minutes["telegram_send"] = {"confirmed_sends": len(deliveries),
        "minutes": [r["stage_seconds"]["telegram_send"]/60 for r in deliveries.values()
                    if "telegram_send" in r.get("stage_seconds", {})]}
    if asof < start:
        state = "SESSION_NOT_STARTED"
    elif asof < end:
        state = "PARTIAL_SESSION_OBSERVED"
    else:
        state = "SESSION_WINDOW_ELAPSED" if runs else "NO_COMPLETED_SESSION_RUNS"
    coverage_gaps = [max(0., (right[0]-left[1]).total_seconds()/60)
                     for left, right in zip(boundaries, boundaries[1:])]
    counts = {key: len(value) for key, value in stage_sets.items()}
    return {"item": "CC-511", "recorded_at_utc": asof.isoformat(), "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(), "observed_cutoff_utc": cutoff.isoformat() if cutoff >= start else None,
        "session_state": state, "window_elapsed": asof >= end, "runs_read": len(runs),
        "counts_distinct_posts": counts, "run_statuses": dict(statuses), "stage_minutes": stage_minutes,
        "post_to_send_minutes": list(deliveries.values()), "on_topic_without_authored_draft": undrafted,
        "on_topic_without_validated_draft": unvalidated,
        "first_undrafted_causes": dict(Counter(r["cause"] for r in undrafted)),
        "first_unvalidated_causes": dict(Counter(r["cause"] for r in unvalidated)),
        "coverage": {"first_run_started_at_utc": boundaries[0][0].isoformat() if boundaries else None,
            "last_run_ended_at_utc": boundaries[-1][1].isoformat() if boundaries else None,
            "max_between_run_gap_minutes": max(coverage_gaps) if coverage_gaps else None},
        "gaps": gaps, "posts": list(posts.values()), "runs": runs,
        "artifacts": [{"path": key, "sha256": value} for key, value in artifacts.items()],
        "semantics": {"seen": "Distinct target IDs retained in result, request or funnel records, including stale targets.",
            "on_topic": "Passed topic checks in that original run; the new map is never backdated.",
            "above_floor": "Recorded ranking acceptance; legacy absent scores stay unobserved.",
            "authored": "Writer returned a draft; validated counts separately represent pack checks.",
            "sent": "Bot API confirmation in the original run; a public reply or phone read is not inferred.",
            "timings": "Measured stage duration, not invented candidate latency. Zero sends gives no delivery latency."}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default="2026-11-12")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--asof", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--runs", type=Path, default=RUNS)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("us-session-funnel.json"))
    args = parser.parse_args()
    start, end = session_bounds(args.day)
    report = summarize(args.runs, start=args.start or start, end=args.end or end, asof=args.asof)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("session_state", "runs_read", "counts_distinct_posts",
          "first_undrafted_causes", "coverage")}, indent=2))
