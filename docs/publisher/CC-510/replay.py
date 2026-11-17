"""Bounded CC-510 replay: saved 12 November omissions, no model or delivery call.

Run from this worktree: python docs/publisher/CC-510/replay.py
Only the named output is written. Raw retained X text is never exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from live_contentops import x_reply_base_rates_v1 as rates
from live_contentops import x_reply_bot_v1 as bot
from live_contentops import x_reply_pack_v1 as packs

RUNS = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\x_reply_pack\bot")
SIDECARS = Path(r"A:\Capital Chronicle\Runtime\ContentOps\headline_ingestion\data\intake\headline_sidecars")
CAUSES = {"NO_USABLE_FACT", "NO_ADDED_FACT_ABOVE_QUALITY_FLOOR"}


def replay(*, start, cutoff, output):
    started = perf_counter()
    start, cutoff = rates.policy.utc(start), rates.policy.utc(cutoff)
    first, posts, records = {}, {}, []
    # Jim's 12 November starts at 17:00Z on 11 November (GMT+7).
    folders = sorted([*RUNS.glob("20261111T*"), *RUNS.glob("20261112T*")])
    for folder in folders:
        if folder.name[:15] < start.strftime("%Y%m%dT%H%M%S") or folder.name[:15] > cutoff.strftime("%Y%m%dT%H%M%S"):
            continue
        path = folder / "result.json"
        if not path.is_file():
            continue
        raw = path.read_bytes()
        data = json.loads(raw)
        at = rates.policy.utc(data["started_at_utc"])
        if at < start or at > cutoff:
            continue
        records.append({"path": str(path), "sha256": sha256(raw).hexdigest()})
        for row in data.get("dropped_candidates", []):
            if row.get("cause") in CAUSES:
                first.setdefault(row["post_id"], {"cause": row["cause"], "at_utc": at.isoformat(),
                                                  "result": str(path), "result_sha256": sha256(raw).hexdigest()})
        for request in folder.glob("reply-pack-request-*.json"):
            request_raw = request.read_bytes()
            for row in json.loads(request_raw).get("candidates", []):
                if row["post_id"] in first and row["post_id"] not in posts:
                    posts[row["post_id"]] = {"post": row, "text_source": str(request),
                        "source_sha256": sha256(request_raw).hexdigest(), "basis": "saved request"}
    # NO_USABLE_FACT targets were removed before request construction. Recover
    # their exact headline from the append-only intake known before that run.
    for path in [SIDECARS / f"step1_headline_sidecar_2026_11_{day}.jsonl" for day in (11, 12)]:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8-sig") as file:
            for number, line in enumerate(file, 1):
                row = json.loads(line)
                key = str(row.get("tweet_id"))
                if key not in first or key in posts:
                    continue
                known = row.get("captured_at_utc_precise") or row.get("captured_at_utc")
                if not known or rates.policy.utc(known) > rates.policy.utc(first[key]["at_utc"]):
                    continue
                posts[key] = {"post": {"post_id": key, "post_text": row["headline_text"],
                    "post_time_utc": row["headline_timestamp"], "post_url": row.get("tweet_url"),
                    "author_handle": row["author_handle"], "reply_count": row.get("metrics", {}).get("replies")},
                    "text_source": str(path), "source_line": number, "source_sha256": sha256(line.encode()).hexdigest(),
                    "basis": "append-only intake captured before original run", "text_known_at_utc": known}
    outcomes, counters = [], Counter()
    with tempfile.TemporaryDirectory(prefix="cc510-replay-") as temporary:
        temporary = Path(temporary)
        for key, cause in first.items():
            held = posts.get(key)
            result = {"post_id": key, "first_cause": cause["cause"], "original_check_at_utc": cause["at_utc"],
                "result_artifact": cause["result"], "result_sha256": cause["result_sha256"],
                "reaches_ranking_with_base_rate": False}
            if not held:
                result["replay_cause"] = "ORIGINAL_TARGET_TEXT_NOT_RECOVERED"
                outcomes.append(result)
                continue
            post = held["post"]
            result.update({k: v for k, v in held.items() if k != "post"})
            result["post_text_sha256"] = sha256(post["post_text"].encode()).hexdigest()
            sources, gaps = rates.collect([post], now=cause["at_utc"])
            usable = []
            for source in sources:
                try:
                    rates.policy.check_send_time(post, now=cause["at_utc"])
                    rates.policy.check_fact(post, source, now=cause["at_utc"])
                    usable.append(source)
                except (ValueError, KeyError) as exc:
                    gaps.append({"cause": str(exc)})
            supplied = []
            def capture_rank_input(prompt, **kwargs):
                supplied.extend(json.loads(prompt.split("\n", 1)[1])["candidates"])
                return {"ranking": []}, {"caller": "offline rank-input capture; no editorial model invoked"}
            if usable:
                request = {"prepared_at_utc": cause["at_utc"], "request_sha256": "offline-replay-" + key,
                    "candidates": [{**post, "usable_source_ids": [s["source_id"] for s in usable]}],
                    "sources": usable, "audience_feedback": {}}
                path = temporary / (key + ".json")
                path.write_text(json.dumps(request), encoding="utf-8")
                bot.rank_and_draft(path, output_dir=temporary / key, ranker=capture_rank_input,
                                   now=rates.policy.utc(cause["at_utc"]))
            result["reaches_ranking_with_base_rate"] = bool(supplied and supplied[0]["available_facts"])
            result["facts"] = [{k: source["fact_binding"][k] for k in
                ("markets", "count", "sample_count", "period_text", "through_date", "condition_text",
                 "horizon_sessions", "series_id")} for source in usable]
            result["producer_seconds"] = [s["artifact_binding"]["producer_answer"]["elapsed_seconds"] for s in sources]
            result["source_gaps"] = gaps
            if not sources and not gaps:
                result["replay_cause"] = "NO_EXPLICIT_SUPPORTED_MARKET_MOVE_IN_TARGET"
            counters[cause["cause"] + ":targets"] += 1
            counters[cause["cause"] + ":with_base_rate_at_ranking"] += int(result["reaches_ranking_with_base_rate"])
            outcomes.append(result)
    evidence = {"item": "CC-510", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "replay_run_start_utc": start.isoformat(), "replay_run_cutoff_utc": cutoff.isoformat(), "runs_read": len(records),
        "code_files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
            [ROOT / "live_contentops" / name for name in ("x_reply_base_rates_v1.py", "x_reply_bot_v1.py", "x_reply_fact_policy_v1.py", "x_reply_pack_v1.py")]},
        "source_result_set_sha256": rates.digest(records), "distinct_targets": len(first),
        "targets_recovered": len(posts), "first_causes": dict(Counter(v["cause"] for v in first.values())),
        "ranking_input_counts": dict(counters), "reaches_ranking_with_base_rate": sum(
            x["reaches_ranking_with_base_rate"] for x in outcomes),
        "meaning": "Exact original check clocks and as-known history; the production rank-input builder was called with an offline capture function. No new quality score, writer, Telegram send or live step is claimed.",
        "public_submit_actions": 0, "schedule_changed": False,
        "elapsed_seconds": perf_counter() - started, "targets": outcomes}
    Path(output).write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {k: v for k, v in evidence.items() if k != "targets"}


def producer_check(output):
    """Query real held history for six explicit fixture conditions, without a bot tick."""
    now, started = datetime.now(timezone.utc), perf_counter()
    headlines = ["Gold rises 0.5%", "EUR/USD falls 0.3%", "USD/JPY gains 0.4%",
                 "WTI crude oil falls 0.3%", "S&P 500 rises 2.1%", "Bitcoin rises 1.2%"]
    posts = [{"post_text": text, "post_time_utc": now.isoformat()} for text in headlines]
    sources, gaps = rates.collect(posts, now=now)
    rows = []
    for source in sources:
        fact = source["fact_binding"]
        target = next(p for p in posts if fact["markets"][0] in rates.policy.markets(p["post_text"]))
        rates.policy.check_fact(target, source, now=now)
        answer, census = source["artifact_binding"]["producer_answer"], source["artifact_binding"].get("census") or {}
        rows.append({**{k: fact[k] for k in ("markets", "count", "sample_count", "period_text", "through_date",
            "condition_text", "horizon_sessions", "series_id")}, "producer_seconds": answer["elapsed_seconds"],
            "source_id": source["source_id"], "source_count": len(answer["sources"]),
            "desk_odds_market": census.get("market"), "desk_odds_active_rows": census.get("active_market_rows", []),
            "producer_answer_sha256": rates.digest({k: v for k, v in answer.items() if k != "elapsed_seconds"})})
    evidence = {"item": "CC-510", "recorded_at_utc": now.isoformat(),
        "mode": "READ_ONLY_PRODUCER_QUERIES_FOR_SIX_FIXTURE_CONDITIONS; no bot tick or live/deploy step",
        "source_count": len(rows), "six_markets": sorted({r["markets"][0] for r in rows}),
        "horizons": sorted({r["horizon_sessions"] for r in rows}),
        "all_tool_calls_under_two_seconds": bool(rows) and all(r["producer_seconds"] < 2 for r in rows),
        "elapsed_seconds": perf_counter() - started, "gaps": gaps,
        "bindings_path": str(rates.BINDINGS), "bindings_sha256": sha256(rates.BINDINGS.read_bytes()).hexdigest(),
        "desk_odds_path": str(rates.ODDS), "desk_odds_sha256": sha256(rates.ODDS.read_bytes()).hexdigest(),
        "adapter_sha256": sha256((ROOT / "live_contentops/x_reply_base_rates_v1.py").read_bytes()).hexdigest(),
        "facts": rows, "public_submit_actions": 0}
    Path(output).write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {k: v for k, v in evidence.items() if k != "facts"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-11-11T17:00:00Z")
    parser.add_argument("--cutoff", default="2026-11-12T11:21:37Z")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("replay.json"))
    parser.add_argument("--producer-check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(producer_check(args.output) if args.producer_check else
                     replay(start=args.start, cutoff=args.cutoff, output=args.output), indent=2))
