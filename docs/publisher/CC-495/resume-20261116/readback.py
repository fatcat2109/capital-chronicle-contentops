"""Read CC-495's saved private deliveries; never tick the bot or call a transport.

Run from the repository root. SQLite enforces read-only access. Output contains
identities, clocks, our facts and hashes, never retained target text or chat IDs.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops import x_reply_bot_v1 as bot  # noqa: E402
from live_contentops import x_reply_pack_v1 as packs  # noqa: E402


LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
OUT = Path(__file__).resolve().parent
SINCE = "2026-11-11T20:55:03.587558+00:00"  # Original installed CC-495 readback.
RECORDED_CAUSES = {
    "JSONDecodeError": "JSON_DECODE_ERROR",
    "The supplied Bitcoin base rates concern daily losses or CPI reactions, not annual returns. "
    "No supplied source directly addresses the annual-growth assumption or STRC payout coverage.": "WRITER_FACT_NOT_RELEVANT_TO_TARGET",
}


def digest(raw):
    return sha256(raw if isinstance(raw, bytes) else raw.encode()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def fingerprint(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}


def model_record(call):
    keys = ("status", "configured_model", "configured_effort", "runtime_model",
            "runtime_effort", "configuration_status", "elapsed_seconds",
            "started_at_utc", "ended_at_utc", "observed_session_id")
    return {k: call.get(k) for k in keys}


def delivery_readback(db, delivery, event_row):
    payload = json.loads(delivery["payload"])
    proof = json.loads(event_row["payload"])
    pack_row = db.execute("SELECT * FROM outbox_messages WHERE message_id=?",
                          (payload["pack_message_id"],)).fetchone()
    pack = json.loads(pack_row["payload"])
    item = next(i for i in pack["items"] if i["post_id"] == payload["post_id"])
    sent_at = packs.clock(proof["delivered_at_utc"])
    # The persisted source check is immediately before this send attempt. Replay
    # the actual policy against the exact immutable source, at that original time.
    checked_at = packs.clock(proof["fact_binding"]["checked_at_utc"])
    checked = packs.recheck_mobile_item(None, item, now=checked_at)
    assert checked["age_text"] == proof["fact_binding"]["age_text"]
    assert checked["kind"] in {"session", "base_rate"}
    posted_at = packs.clock(item["post_time_utc"])
    elapsed = (sent_at - posted_at).total_seconds() / 60
    assert abs(elapsed - proof["post_to_delivery_minutes"]) < 1e-8
    assert 0 <= elapsed <= 15
    assert 0 <= proof["post_to_send_attempt_minutes"] <= 15
    assert delivery["status"] == "DELIVERED"
    assert proof["public_submit_actions"] == 0
    assert {"filter", "ranking", "drafting", "checks", "telegram_send"} <= proof["stage_seconds"].keys()
    item = deepcopy(item)
    item["fact_binding"] = proof["fact_binding"]
    # This is a formatter replay from the saved pack, not a Telegram body readback.
    rendered = bot.message_for(item, number=1, now=checked_at)
    age_line = next(unescape(s) for s in rendered.splitlines() if s.startswith("Fact age: "))
    bound = item["sources"][0]
    source = packs.resolve_fact_source(None, bound)
    relation = "same market" if packs.fact_policy.markets(item["post_text"]) & set(checked["markets"]) else "expressly stated driver"
    calls = pack.get("editorial_call", {})
    return {
        "delivery_id": delivery["message_id"], "delivery_status": delivery["status"],
        "delivery_payload_sha256": digest(delivery["payload"]),
        "receipt_id": event_row["message_id"], "receipt_payload_sha256": digest(event_row["payload"]),
        "pack_message_id": pack_row["message_id"], "pack_payload_sha256": digest(pack_row["payload"]),
        "telegram_message_id": proof["message_id"], "post_id": item["post_id"],
        "target_text_sha256": digest(item["post_text"]), "draft_text_sha256": digest(item["draft_text"]),
        "post_time_utc": item["post_time_utc"], "draft_ready_at_utc": item["draft_ready_at_utc"],
        "delivered_at_utc": proof["delivered_at_utc"],
        "post_to_draft_minutes": proof["post_to_draft_minutes"],
        "post_to_send_attempt_minutes": proof["post_to_send_attempt_minutes"],
        "post_to_delivery_minutes": elapsed, "five_minute_target_met": elapsed <= 5,
        "stage_seconds": proof["stage_seconds"], "latency_seconds": proof.get("latency_seconds"),
        "feed_seen_at_utc": item.get("feed_seen_at_utc"),
        "selected_at_utc": item.get("selected_at_utc"),
        "fact_binding": proof["fact_binding"], "fact_source": item["fact_source"],
        "fact_text": item["fact_text"], "source_id": bound["source_id"],
        "source_payload_sha256": bound["store_payload_sha256"],
        "source_known_at_utc": source["known_at_utc"],
        "source_artifact": bound.get("artifact_binding"),
        "source_binding_recheck": "PASS", "fact_and_send_policy_recheck": "PASS",
        "market_relation": relation, "age_line_formatter_replay": age_line,
        "age_rendering_evidence": "Saved send-time fact binding and production formatter; no Telegram body readback.",
        "editorial_calls": {name: model_record(call) for name, call in calls.items()},
    }


def dropped_readback(db, through):
    """Stream original run payloads; group repeated causes without retaining X text."""
    candidates, causes, statuses = {}, Counter(), Counter()
    runs, appearances, missing = 0, 0, 0
    cursor = db.execute(
        "SELECT message_id,created_at,payload FROM outbox_messages "
        "WHERE destination=? AND created_at>=? AND created_at<=? ORDER BY created_at,message_id",
        (bot.RUNS, SINCE, through))
    for row in cursor:
        run = json.loads(row["payload"])
        runs += 1
        statuses[run.get("status", "MISSING_STATUS")] += 1
        for drop in run.get("dropped_candidates", []):
            appearances += 1
            post_id, cause = str(drop.get("post_id", "")), drop.get("cause")
            if not post_id or not cause:
                missing += 1
            safe_cause = (cause if isinstance(cause, str) and re.fullmatch(r"[A-Z0-9_]+", cause)
                          else RECORDED_CAUSES.get(cause, "UNSTRUCTURED_RECORDED_CAUSE"))
            cause_hash = digest(json.dumps(cause, sort_keys=True))
            key = (post_id, safe_cause, cause_hash)
            causes[safe_cause] += 1
            if key not in candidates:
                candidates[key] = {
                    "post_id": post_id, "cause": safe_cause, "recorded_cause_sha256": cause_hash,
                    "first_seen_at_utc": row["created_at"], "first_run_id": row["message_id"],
                    "first_run_payload_sha256": digest(row["payload"]),
                    "first_artifact": run.get("artifact_path"), "appearances": 0,
                }
                if cause in RECORDED_CAUSES:
                    candidates[key]["recorded_cause"] = cause
            entry = candidates[key]
            entry["appearances"] += 1
            entry["last_seen_at_utc"] = row["created_at"]
    assert missing == 0, "A saved dropped candidate lacks its identity or cause."
    result = {"since_utc": SINCE, "through_utc": through, "runs_read": runs,
              "run_status_counts": statuses, "drop_appearances": appearances,
              "distinct_candidates": len({key[0] for key in candidates}),
              "distinct_candidate_causes": len(candidates), "missing_identity_or_cause": missing,
              "cause_counts": causes, "candidates": list(candidates.values()),
              "grouping": "Repeated occurrences of the same post and cause retain first/last clocks and their count; original artifacts remain unchanged."}
    save("dropped-candidates.json", result)
    return {key: value for key, value in result.items() if key != "candidates"}


def main():
    now = datetime.now(timezone.utc).isoformat()
    db_path = RUNTIME / "contentops_daily_app_v1.sqlite3"
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True, timeout=5) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        events = db.execute(
            "SELECT * FROM outbox_messages WHERE destination=? AND created_at>=? AND created_at<=? "
            "ORDER BY created_at,message_id", (bot.EVENTS, SINCE, now)).fetchall()
        receipts = [row for row in events if json.loads(row["payload"]).get("kind") == "private_draft_delivered"]
        assert len(receipts) >= 3, "The next three natural delivery receipts are not yet present."
        next_three = []
        for event in receipts[:3]:
            proof = json.loads(event["payload"])
            delivery = db.execute("SELECT * FROM outbox_messages WHERE message_id=?",
                                  (proof["delivery_id"],)).fetchone()
            next_three.append(delivery_readback(db, delivery, event))
        latest = db.execute(
            "SELECT message_id,created_at,payload FROM outbox_messages WHERE destination=? "
            "AND created_at<=? ORDER BY created_at DESC LIMIT 1", (bot.RUNS, now)).fetchone()
        latest_data = json.loads(latest["payload"])
        drop_summary = dropped_readback(db, now)
        delivery_counts = dict(db.execute(
            "SELECT status,count(*) FROM outbox_messages WHERE destination=? AND created_at>=? "
            "AND created_at<=? GROUP BY status", (bot.DELIVERY, SINCE, now)).fetchall())
    sources = {}
    for name in ("live_contentops/x_reply_bot_v1.py", "live_contentops/x_reply_pack_v1.py",
                 "live_contentops/x_reply_fact_policy_v1.py", "live_contentops/x_reply_fact_sources_v1.py",
                 "live_contentops/x_reply_topics_v1.py", "live_contentops/x_reply_trading_dates_v1.py",
                 "live_contentops/public_market_quote_v1.py", "scripts/plan_status_posts.py"):
        installed, lane = fingerprint(LIVE / name), fingerprint(REPO / name)
        assert installed["sha256"] == lane["sha256"], name
        sources[name] = {"installed": installed, "worktree_sha256": lane["sha256"], "matches_worktree": True}
    summary = {
        "item": "CC-495", "read_at_utc": now, "policy_live_since_readback_utc": SINCE,
        "database_access": "SQLite mode=ro with query_only=ON; bounded original outbox rows, streamed run payloads.",
        "operating_head_at_read": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
        "acceptance": "PASS_THREE_NATURAL_PRIVATE_DELIVERIES", "next_three": next_three,
        "all_post_to_delivery_minutes_at_most_15": all(r["post_to_delivery_minutes"] <= 15 for r in next_three),
        "five_minute_target_met_in_next_three": sum(r["five_minute_target_met"] for r in next_three),
        "new_policy_delivery_status_counts": delivery_counts, "confirmed_receipts_since_policy": len(receipts),
        "dropped_candidates": {"artifact": "dropped-candidates.json", **drop_summary},
        "latest_run": {"message_id": latest["message_id"], "stored_at_utc": latest["created_at"],
                       "payload_sha256": digest(latest["payload"]),
                       **{k: latest_data.get(k) for k in ("status", "cause", "started_at_utc", "ended_at_utc", "artifact_path")}},
        "installed_sources": sources, "phone_open_observed": False,
        "delivery_evidence_limit": "Bot API-confirmed private delivery and saved input bindings; no phone-screen, message-body or public-reply readback.",
        "manual_consumer_ticks": 0, "model_calls": 0, "transport_calls": 0,
        "schedule_changed": False, "applications_restarted": False,
    }
    save("readback.json", summary)
    print(json.dumps({"readback": str(OUT / "readback.json"), "acceptance": summary["acceptance"],
                      "next_three_minutes": [round(r["post_to_delivery_minutes"], 4) for r in next_three],
                      "dropped_candidates": drop_summary["distinct_candidates"],
                      "missing_drop_causes": drop_summary["missing_identity_or_cause"]}))


if __name__ == "__main__":
    main()
