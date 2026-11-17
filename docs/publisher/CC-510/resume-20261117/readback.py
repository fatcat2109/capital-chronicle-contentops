"""Verify the existing natural base-rate delivery; never invoke a transport."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import ast
import json
import sqlite3
import subprocess
import sys


REPO = Path(__file__).resolve().parents[4]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
OUT = Path(__file__).resolve().parent
SINCE = "2026-11-12T12:31:37.228267+00:00"
INSTALLED_HEAD = "d346c0d688cdc41f5238d5384a0c7a3f111f0595"
sys.path.insert(0, str(REPO))

from live_contentops import x_reply_base_rates_v1 as rates
from live_contentops import x_reply_bot_v1 as bot
from live_contentops import x_reply_fact_policy_v1 as policy


def digest(value):
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def fingerprint(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}


def function_digest(source, name):
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return digest(ast.get_source_segment(source, node))


def main():
    now = datetime.now(timezone.utc).isoformat()
    database = RUNTIME / "contentops_daily_app_v1.sqlite3"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as conn:
        conn.execute("PRAGMA query_only=ON")
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
        receipts = [(key, created, raw, json.loads(raw)) for key, created, raw in events
                    if json.loads(raw).get("kind") == "private_draft_delivered"]
        base_receipts = [r for r in receipts if r[3].get("fact_binding", {}).get("kind") == "base_rate"]
        assert base_receipts, "No natural base-rate receipt in the bounded store interval"
        event_id, event_created, event_raw, event = base_receipts[0]
        delivery = next(r for r in deliveries if r[0] == event["delivery_id"])
        assert delivery[1] == "DELIVERED"
        delivery_value = json.loads(delivery[3])
        pack_id = delivery_value["pack_message_id"]
        pack_row = conn.execute(
            "SELECT status,created_at,payload FROM outbox_messages WHERE message_id=?", (pack_id,)
        ).fetchone()
    pack = json.loads(pack_row[2])
    item = next(i for i in pack["items"] if i["post_id"] == event["post_id"])
    bound = item["sources"][0]
    artifact = bound["artifact_binding"]
    answer = artifact["producer_answer"]
    # Rebuild the source from its saved producer answer, without recounting history.
    source = rates.source_from_answer(
        answer, condition=artifact["condition"], query=artifact["query"],
        condition_text=artifact["condition_text"], now=artifact["as_of_utc"],
        completed_before=artifact["completed_before_utc"], census=artifact.get("census"),
        bindings=artifact["bindings"],
    )
    assert source["source_id"] == bound["source_id"] == item["draft_binding"]["source_id"]
    assert source["store_payload_sha256"] == bound["store_payload_sha256"]
    checked = policy.check_fact(item, source, now=event["fact_binding"]["checked_at_utc"],
                                draft=item["draft_binding"])
    assert checked == event["fact_binding"]
    assert checked["count"] == answer["terminal_up"]["hits"]
    assert checked["sample_count"] == answer["terminal_up"]["n"] == answer["case_count"]
    assert item["draft_text"] == item["draft_binding"]["draft_text"]
    send_minutes = policy.check_send_time(item, now=event["delivered_at_utc"])
    assert event["public_submit_actions"] == 0 and pack["public_write_performed"] is False

    formatted = bot.message_for({**item, "fact_binding": checked}, number=1,
                                now=policy.utc(event["delivered_at_utc"]))
    lines = formatted.splitlines()
    cutoff_line = "Fact: base rate through " + checked["through_date"]
    position = lines.index(cutoff_line)
    fact_lines = lines[position:position + 2]
    assert f"{checked['count']} of {checked['sample_count']}" in fact_lines[1]
    assert checked["period_text"] in fact_lines[1]
    original_bot = subprocess.check_output(
        ["git", "show", INSTALLED_HEAD + ":live_contentops/x_reply_bot_v1.py"],
        cwd=REPO, text=True, encoding="utf-8",
    )
    formatter_hash = function_digest((LIVE / "live_contentops/x_reply_bot_v1.py").read_text(encoding="utf-8"), "message_for")
    assert formatter_hash == function_digest(original_bot, "message_for")
    installed_sources = {}
    for name in ("x_reply_base_rates_v1.py", "x_reply_pack_v1.py", "x_reply_bot_v1.py", "x_reply_fact_policy_v1.py"):
        installed = fingerprint(LIVE / "live_contentops" / name)
        lane = fingerprint(REPO / "live_contentops" / name)
        assert installed["sha256"] == lane["sha256"]
        installed_sources[name] = {"installed": installed, "worktree_sha256": lane["sha256"], "matches_worktree": True}

    latest_value = json.loads(latest[2])
    calls = {role: {k: call.get(k) for k in (
        "status", "answered_by", "configured_model", "configured_effort", "configuration_status",
        "runtime_model", "runtime_effort", "elapsed_seconds", "started_at_utc", "ended_at_utc", "observed_session_id",
    )} for role, call in item["editorial_call"].items()}
    result = {
        "item": "CC-510", "read_at_utc": now, "since_utc": SINCE,
        "database_access": "SQLite mode=ro with query_only=ON; bounded delivery/event rows and exact saved pack",
        "operating_head_at_read": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
        "acceptance": "PASS_NATURAL_BASE_RATE_PRIVATE_DELIVERY",
        "delivery_status_counts": {status: sum(d[1] == status for d in deliveries) for status in sorted({d[1] for d in deliveries})},
        "base_rate_delivery_count": len(base_receipts),
        "delivery_receipts": [{"receipt_id": key, "delivery_id": e["delivery_id"],
            "telegram_message_id": e["message_id"], "delivered_at_utc": e["delivered_at_utc"],
            "fact_kind": e["fact_binding"]["kind"]} for key, _, _, e in receipts],
        "base_rate_delivery": {
            "delivery_id": delivery[0], "delivery_status": delivery[1], "delivery_payload_sha256": digest(delivery[3]),
            "receipt_id": event_id, "receipt_created_at_utc": event_created, "receipt_payload_sha256": digest(event_raw),
            "pack_message_id": pack_id, "pack_payload_sha256": digest(pack_row[2]),
            "telegram_message_id": event["message_id"], "post_id": event["post_id"],
            "target_text_sha256": digest(item["post_text"]), "draft_text": item["draft_text"],
            "draft_text_sha256": digest(item["draft_text"]), "fact_text": item["fact_text"], "fact_source": item["fact_source"],
            "post_time_utc": item["post_time_utc"], "draft_ready_at_utc": item["draft_ready_at_utc"],
            "delivered_at_utc": event["delivered_at_utc"], "post_to_delivery_minutes": send_minutes,
            "fact_binding": checked, "source_id": source["source_id"], "source_payload_sha256": source["store_payload_sha256"],
            "source_known_at_utc": source["known_at_utc"], "rights_class": source["rights_class"],
            "producer_answer_sha256": rates.digest(answer),
            "producer_query": artifact["query"], "producer_as_of_utc": artifact["as_of_utc"],
            "completed_before_utc": artifact["completed_before_utc"],
            "source_binding_recheck": "PASS_SAVED_PRODUCER_ANSWER",
            "fact_and_send_policy_recheck": "PASS", "fact_lines_formatter_replay": fact_lines,
            "formatter_function_sha256": formatter_hash,
            "formatter_matches_original_installation": True, "editorial_calls": calls,
        },
        "latest_run": {"message_id": latest[0], "stored_at_utc": latest[1], "payload_sha256": digest(latest[2]),
            **{k: latest_value.get(k) for k in ("artifact_path", "status", "cause", "started_at_utc", "ended_at_utc")}},
        "installed_sources": installed_sources,
        "phone_open_observed": False, "telegram_body_readback": False,
        "delivery_evidence_limit": "Bot API-confirmed delivery and saved exact bindings; fact lines replay the unchanged send formatter. No phone-screen or Telegram body readback.",
        "manual_consumer_ticks": 0, "model_calls": 0, "transport_calls": 0,
        "public_submit_actions": 0, "producer_queries": 0,
        "schedule_changed": False, "applications_restarted": False,
    }
    target = OUT / "readback.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(target), "acceptance": result["acceptance"],
                      "telegram_message_id": event["message_id"], "count": checked["count"],
                      "sample_count": checked["sample_count"], "period": checked["period_text"],
                      "through_date": checked["through_date"]}, indent=2))


if __name__ == "__main__":
    main()
