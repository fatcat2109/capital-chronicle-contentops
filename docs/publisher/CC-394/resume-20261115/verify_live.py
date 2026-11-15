"""Bounded, read-only CC-394 acceptance observation using the installed owners."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.neo_endpoint_executor_v1 import NeoMcpClient, NeoEndpointError
from live_contentops.published_content_v1 import PRODUCTION_STORE


def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ReadOnlyStore(ContentOpsDurableStore):
    get_connection = ContentOpsDurableStore.get_read_only_connection


store = ReadOnlyStore(PRODUCTION_STORE, auto_migrate=False)
revisions = store.list_outbox_messages(destination=scorecard.DESTINATION)
readbacks = {r["message_id"].removesuffix("-readback"): json.loads(r["payload"])
             for r in store.list_outbox_messages(destination=scorecard.DESTINATION + "-readback")}
retained = json.loads(revisions[-1]["payload"])
export = scorecard.read_export()
record = scorecard.project(export, retained_rows=retained["rows"])
save("installed-projection.json", record)
baseline = utc("2026-11-10T10:13:35.942326+00:00")
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
    timings.append({"plan_id": row["plan_id"], "outcome_id": row["outcome_id"],
        "score_hash": row["score_hash"], "result": row["result"], "symbol": row["symbol"],
        "resolved_at_utc": row["at_utc"], "scored_at_utc": row.get("scored_at_utc"),
        "after_initial_acceptance": bool(scored and scored > baseline),
        "first_bot_observed_at_utc": first[0].isoformat() if first else None,
        "latency_from_main_score_seconds": (first[0] - scored).total_seconds() if first and scored else None,
        "within_60_minutes": bool(first and scored and 0 <= (first[0] - scored).total_seconds() <= 3600),
        "message_id": first[2]["message_id"] if first else None,
        "revision": first[1]["message_id"] if first else None,
        "visible_in_first_pinned_text": first[3]["line"] in first[2]["text"] if first else None,
        "visible_in_current_text": row["line"] in record["text"]})
save("score-timing.json", {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "initial_acceptance_clock_utc": baseline.isoformat(), "scored_results": timings,
    "newest_by_main_score": max(timings, key=lambda r: r["scored_at_utc"] or "") if timings else None,
    "read_only": True})

bot = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "operation": "getChat",
       "public_writes": 0, "expected_message_id": "134"}
try:
    chat = scorecard.TelegramScorecardAPI().call("getChat")
    pinned = chat.get("pinned_message") or {}
    text = pinned.get("text", "")
    bot.update(status="VERIFIED" if scorecard._message_matches(pinned, record["text"], "134") else "MISMATCH",
        chat_username=chat.get("username"), chat_type=chat.get("type"),
        message_id=str(pinned.get("message_id")), text=text,
        text_sha256=sha256(text.encode()).hexdigest(), characters=scorecard.text_length(text),
        message_date_utc=datetime.fromtimestamp(pinned["date"], timezone.utc).isoformat() if pinned.get("date") else None,
        message_edit_date_utc=datetime.fromtimestamp(pinned["edit_date"], timezone.utc).isoformat() if pinned.get("edit_date") else None)
except scorecard.TelegramScorecardError as exc:
    bot.update(status="NOT_CONFIRMED", cause=str(exc))
bot["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
save("bot-readback.json", bot)

neo = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
       "endpoint": "http://127.0.0.1:9010/mcp", "operation": "initialize",
       "public_url": "https://t.me/s/CapitalChronicle/134", "public_writes": 0}
client = NeoMcpClient(task_name="cc394 scorecard readback", group_title="codex/cc394-scorecard-readback")
try:
    client.initialize()
    neo.update(status="CONNECTED", operation="public_page_snapshot")
    page = client.open("telegram-public", neo["public_url"])
    snapshot = client.snapshot(page)
    save("public-page-snapshot.json", snapshot)
    neo.update(status="OBSERVED", page=page, snapshot_artifact="public-page-snapshot.json")
except NeoEndpointError as exc:
    neo.update(status="NOT_OBSERVED", cause=str(exc))
finally:
    client.http.close()
neo["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
save("public-readback.json", neo)

files = ["live_contentops/pinned_result_scorecard_v1.py", "live_contentops/plan_status_posts_v1.py",
         "live_contentops/publication_coordinator_v1.py", "scripts/plan_status_posts.py",
         "tests/test_pinned_result_scorecard_cc394.py"]
builder = HERE.parents[3]
source = {}
for name in files:
    a, b = (builder / name).read_bytes(), (OPERATING / name).read_bytes()
    source[name] = {"builder_sha256": sha256(a).hexdigest(), "operating_sha256": sha256(b).hexdigest(),
                    "matches_after_newline_normalization": a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")}
save("installed-source.json", {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "operating_head": subprocess.check_output(["git", "-C", str(OPERATING), "rev-parse", "HEAD"], text=True).strip(),
    "imported_module": scorecard.__file__, "source_files": source, "source_changes": 0})
print(json.dumps({"counts": record["counts"], "shown": record["shown"],
    "characters": scorecard.text_length(record["text"]), "bot": bot["status"],
    "neo": neo["status"], "neo_cause": neo.get("cause"), "scored_timing_rows": len(timings)}))
