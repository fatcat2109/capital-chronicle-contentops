"""Read-only acceptance observation of CC-394's installed consumer and object."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
BUILDER = HERE.parents[3]
sys.path.insert(0, str(OPERATING))
from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE


def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def clock():
    return datetime.now(timezone.utc).isoformat()


class ReadOnlyStore(ContentOpsDurableStore):
    get_connection = ContentOpsDurableStore.get_read_only_connection


store = ReadOnlyStore(PRODUCTION_STORE, auto_migrate=False)
revisions = store.list_outbox_messages(destination=scorecard.DESTINATION)
readbacks = {r["message_id"].removesuffix("-readback"): json.loads(r["payload"])
             for r in store.list_outbox_messages(destination=scorecard.DESTINATION + "-readback")}
retained = json.loads(revisions[-1]["payload"])
source_error = None
try:
    export = scorecard.read_export()
    record = scorecard.project(export, retained_rows=retained["rows"])
except (OSError, ValueError, KeyError, TypeError) as exc:
    source_error = str(exc)[:240]
    record = retained
save("installed-projection.json", {**record, "observed_at_utc": clock(), "source_error": source_error})

timings = []
for row in record["rows"]:
    if not row["scored"]:
        continue
    observations = []
    for revision in revisions:
        observation = readbacks.get(revision["message_id"])
        if not observation or revision["status"] != "CONFIRMED":
            continue
        prior = json.loads(revision["payload"])
        match = next((r for r in prior["rows"] if r["plan_id"] == row["plan_id"]
                      and r.get("score_hash") == row.get("score_hash") and r["scored"]), None)
        if match:
            observations.append((utc(observation["observed_at_utc"]), revision, observation, match))
    first = min(observations, key=lambda v: v[0]) if observations else None
    scored = utc(row["scored_at_utc"]) if row.get("scored_at_utc") else None
    elapsed = (first[0] - scored).total_seconds() if first and scored else None
    timings.append({"plan_id": row["plan_id"], "outcome_id": row["outcome_id"],
        "score_hash": row["score_hash"], "result": row["result"], "symbol": row["symbol"],
        "resolved_at_utc": row["at_utc"], "scored_at_utc": row.get("scored_at_utc"),
        "first_bot_observed_at_utc": first[0].isoformat() if first else None,
        "latency_from_main_score_seconds": elapsed,
        "within_60_minutes": elapsed is not None and 0 <= elapsed <= 3600,
        "message_id": first[2]["message_id"] if first else None,
        "revision": first[1]["message_id"] if first else None,
        "visible_in_first_pinned_text": first[3]["line"] in first[2]["text"] if first else None,
        "visible_in_current_text": row["line"] in record["text"]})
save("score-timing.json", {"observed_at_utc": clock(), "scored_results": timings,
    "newest_by_main_score": max(timings, key=lambda r: r["scored_at_utc"] or "") if timings else None})

bot = {"started_at_utc": clock(), "operation": "getChat", "public_writes": 0,
       "expected_message_id": "134"}
try:
    chat = scorecard.TelegramScorecardAPI().call("getChat")
    pinned = chat.get("pinned_message") or {}
    text = pinned.get("text", "")
    bot.update(status="VERIFIED" if scorecard._message_matches(pinned, record["text"], "134") else "MISMATCH",
        chat_username=chat.get("username"), chat_type=chat.get("type"),
        message_id=str(pinned.get("message_id")), text=text,
        text_sha256=sha256(text.encode()).hexdigest(), utf16_units=scorecard.text_length(text),
        message_date_utc=datetime.fromtimestamp(pinned["date"], timezone.utc).isoformat() if pinned.get("date") else None,
        message_edit_date_utc=datetime.fromtimestamp(pinned["edit_date"], timezone.utc).isoformat() if pinned.get("edit_date") else None)
except scorecard.TelegramScorecardError as exc:
    bot.update(status="NOT_CONFIRMED", cause=str(exc))
bot["observed_at_utc"] = clock()
save("bot-readback.json", bot)

runs_dir = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\plan_status_post_runs")
runs = []
for path in sorted(runs_dir.glob("runs-*.jsonl")):
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            try:
                value = json.loads(line)
            except ValueError:
                continue  # A concurrent append may have an unfinished final line.
            if "scorecard" in value:
                runs.append({k: value.get(k) for k in (
                    "at_utc", "status", "cause", "export_generated_at_utc", "scorecard")})
with store.get_connection() as conn:
    feed_count = conn.execute("SELECT count(*) FROM outbox_messages WHERE work_item_id=? AND destination=?",
                             (scorecard.WORK, posts.DESTINATION)).fetchone()[0]
    destinations = [dict(r) for r in conn.execute(
        "SELECT destination,count(*) AS rows FROM outbox_messages WHERE work_item_id=? GROUP BY destination",
        (scorecard.WORK,)).fetchall()]
    dispatch_count = conn.execute("SELECT count(*) FROM platform_dispatches WHERE message_id IN "
        "(SELECT message_id FROM outbox_messages WHERE work_item_id=?)", (scorecard.WORK,)).fetchone()[0]
save("live-consumer.json", {"observed_at_utc": clock(), "run_artifact_directory": str(runs_dir),
    "scorecard_run_records": len(runs),
    "scorecard_created_message_count": sum((r["scorecard"] or {}).get("created_messages", 0) for r in runs),
    "nonzero_extra_feed_post_records": sum(bool((r["scorecard"] or {}).get("extra_result_feed_posts")) for r in runs),
    "public_message_ids": sorted({str(r["scorecard"]["message_id"]) for r in runs
                                  if (r["scorecard"] or {}).get("message_id")}),
    "outbox_destinations_for_work_item": destinations, "scorecard_feed_outbox_count": feed_count,
    "scorecard_feed_destination": posts.DESTINATION,
    "platform_dispatches_for_scorecard_work_item": dispatch_count,
    "object_binding": json.loads(store.get_outbox_message(scorecard.OBJECT)["payload"]),
    "latest_runs": runs[-3:], "public_writes_this_observation": 0})

files = ["live_contentops/pinned_result_scorecard_v1.py", "live_contentops/plan_status_posts_v1.py",
         "live_contentops/publication_coordinator_v1.py", "scripts/plan_status_posts.py",
         "tests/test_pinned_result_scorecard_cc394.py"]
source = {}
for name in files:
    a, b = (BUILDER / name).read_bytes(), (OPERATING / name).read_bytes()
    source[name] = {"builder_sha256": sha256(a).hexdigest(), "operating_sha256": sha256(b).hexdigest(),
                   "matches_after_newline_normalization": a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")}
save("installed-source.json", {"observed_at_utc": clock(),
    "operating_head": subprocess.check_output(["git", "-C", str(OPERATING), "rev-parse", "HEAD"], text=True).strip(),
    "imported_module": scorecard.__file__, "source_files": source, "production_source_changes": 0})
print(json.dumps({"counts": record["counts"], "shown": record["shown"],
    "utf16_units": scorecard.text_length(record["text"]), "bot": bot["status"],
    "source_error": source_error, "scorecard_runs": len(runs), "scored_results": len(timings),
    "newest_score": max(timings, key=lambda r: r["scored_at_utc"] or "") if timings else None}))
