"""Read saved CC-510 consumer evidence without calling a model or transport."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import subprocess


REPO = Path(__file__).resolve().parents[4]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
BOT = RUNTIME / "daily_app_outputs/x_reply_pack/bot"
SINCE = "2026-11-12T12:31:37.228267+00:00"
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_bytes())


def fingerprint(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256(data).hexdigest()}


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    now = datetime.now(timezone.utc).isoformat()
    db = RUNTIME / "contentops_daily_app_v1.sqlite3"
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=5) as conn:
        deliveries = conn.execute(
            "SELECT message_id,status,created_at,payload FROM outbox_messages "
            "WHERE destination=? AND created_at>=? AND created_at<=? ORDER BY created_at",
            ("internal:x-reply-bot-delivery", SINCE, now),
        ).fetchall()
        events = conn.execute(
            "SELECT message_id,created_at,payload FROM outbox_messages "
            "WHERE destination=? AND created_at>=? AND created_at<=? ORDER BY created_at",
            ("internal:x-reply-bot-event", SINCE, now),
        ).fetchall()
        latest = conn.execute(
            "SELECT message_id,created_at,payload FROM outbox_messages "
            "WHERE destination=? AND created_at<=? ORDER BY created_at DESC LIMIT 1",
            ("internal:x-reply-bot-run", now),
        ).fetchone()
    receipt_rows = []
    for key, created, raw in events:
        event = json.loads(raw)
        if event.get("kind") != "private_draft_delivered":
            continue
        fact = event.get("fact_binding", {})
        receipt_rows.append({
            "event_id": key, "event_payload_sha256": sha256(raw.encode()).hexdigest(),
            **{k: event.get(k) for k in ("delivery_id", "post_id", "message_id", "delivered_at_utc")},
            "fact_kind": fact.get("kind"), "fact_markets": fact.get("markets"),
            "count": fact.get("count"), "sample_count": fact.get("sample_count"),
            "period_text": fact.get("period_text"), "through_date": fact.get("through_date"),
        })
    latest_run = json.loads(latest[2])
    upper = datetime.fromisoformat(latest[1]).strftime("%Y%m%dT%H%M%S")
    counts, targets, above_floor, errors = Counter(), {}, [], []
    for prompt_path in sorted(BOT.glob("2026111[234]*/editorial/rank/prompt.txt")):
        run_root = prompt_path.parents[2]
        if not "20261112T123137" <= run_root.name[:15] <= upper:
            continue
        counts["rank_prompts_examined"] += 1
        text = prompt_path.read_text(encoding="utf-8")
        if not re.search(r"higher (?:next|five)-session closes after", text):
            continue  # Excludes the older CPI facts from this producer's count.
        try:
            ranked_input = json.loads(text[text.index("\n") + 1:])
            rank_path = prompt_path.with_name("response.json")
            ranked = read(rank_path) if rank_path.exists() else {}
            scores = {r["post_id"]: r for r in ranked.get("ranking", [])}
            response_path = prompt_path.parents[1] / "response.json"
            response = read(response_path) if response_path.exists() else {}
            run = read(run_root / "result.json")
        except (OSError, ValueError, KeyError) as exc:
            errors.append({"path": str(prompt_path), "error": type(exc).__name__})
            continue
        for post in ranked_input["candidates"]:
            facts = [f for f in post.get("available_facts", [])
                     if f.get("kind") == "base_rate" and
                     re.search(r"higher (?:next|five)-session closes after", f.get("text", ""))]
            if not facts:
                continue
            counts["statistics_target_appearances"] += 1
            key = post["post_id"]
            ranked_row = scores.get(key, {})
            score = ranked_row.get("quality_score")
            omissions = [o for o in response.get("omissions", []) if o.get("post_id") == key]
            omission = omissions[0].get("cause") if omissions else None
            if omission and not re.fullmatch(r"[A-Z0-9_]+", omission):
                omission = "WRITER_OMITTED_TARGET"
            row = {
                "post_id": key, "run": run_root.name, "quality_score": score,
                "rank_prompt": fingerprint(prompt_path),
                "rank_response": fingerprint(rank_path) if rank_path.exists() else None,
                "ranker_reason_sha256": sha256(ranked_row.get("reason", "").encode()).hexdigest(),
                "run_status": run.get("status"), "run_cause": run.get("cause"),
                "omission": omission,
                "facts": facts,  # Our producer's counts; no retained X text.
                "authored_source_ids": [i.get("source_id") for i in response.get("items", [])
                                        if i.get("post_id") == key],
            }
            old = targets.get(key)
            if old is None or (score or 0) > (old["quality_score"] or 0):
                targets[key] = row
            if isinstance(score, int) and score >= 80:
                above_floor.append(row)
    ranking = {
        "since_utc": SINCE, "latest_stored_run_at_utc": latest[1],
        "counts": counts, "distinct_statistics_targets": len(targets),
        "above_floor_attempts": above_floor,
        "targets": sorted(targets.values(), key=lambda row: -(row["quality_score"] or 0)),
        "errors": errors,
    }
    sources = {}
    for name in ("x_reply_base_rates_v1.py", "x_reply_pack_v1.py", "x_reply_bot_v1.py",
                 "x_reply_fact_policy_v1.py"):
        installed, lane = fingerprint(LIVE / "live_contentops" / name), fingerprint(REPO / "live_contentops" / name)
        sources[name] = {"installed": installed, "worktree_sha256": lane["sha256"],
                         "matches_worktree": installed["sha256"] == lane["sha256"]}
    summary = {
        "item": "CC-510", "read_at_utc": now, "since_utc": SINCE,
        "database_access": "SQLite mode=ro; delivery/event rows and latest stored run only",
        "operating_head_at_read": subprocess.check_output(
            ["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
        "deliveries_since_installation": [
            {"delivery_id": key, "status": status, "created_at_utc": created,
             "pack_message_id": json.loads(raw).get("pack_message_id")}
            for key, status, created, raw in deliveries],
        "delivery_receipts": receipt_rows,
        "base_rate_delivery_count": sum(r["fact_kind"] == "base_rate" for r in receipt_rows),
        "latest_run": {"message_id": latest[0], "stored_at_utc": latest[1],
                       "payload_sha256": sha256(latest[2].encode()).hexdigest(),
                       **{k: latest_run.get(k) for k in
                          ("artifact_path", "started_at_utc", "ended_at_utc", "status", "cause")}},
        "installed_sources": sources,
        "statistics_targets_in_actual_rank_inputs": len(targets),
        "statistics_target_appearances": counts["statistics_target_appearances"],
        "statistics_ranked_above_floor_attempts": len(above_floor),
        "phone_acceptance": "BASE_RATE_PHONE_PROOF_PENDING",
        "continuation": "Read back the next natural base-rate delivery from the existing minute consumer.",
        "manual_ticks": 0, "model_calls": 0, "transport_calls": 0,
        "schedule_changed": False, "applications_restarted": False,
    }
    save("ranking-scan.json", ranking)
    save("readback.json", summary)
    print(json.dumps({"readback": str(OUT / "readback.json"),
                      "base_rate_deliveries": summary["base_rate_delivery_count"],
                      "statistics_targets": len(targets), "above_floor": len(above_floor),
                      "errors": len(errors)}, indent=2))


if __name__ == "__main__":
    main()
