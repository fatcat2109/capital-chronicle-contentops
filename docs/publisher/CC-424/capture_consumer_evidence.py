"""Read held consumer evidence for this audit; no coordinator or writes to runtime."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from live_contentops.pinned_result_scorecard_v1 import project

out = Path(__file__).parent
folder = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1")
source = folder / "plan-status.public.json"
raw = source.read_bytes()
export = json.loads(raw)
transitions = json.loads((folder / "plan-transitions.public.json").read_bytes())
pinned = json.loads((out / "pinned-scorecard-readback.json").read_text(encoding="utf-8"))
connection = sqlite3.connect(
    "file:A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3?mode=ro",
    uri=True, timeout=3,
)
connection.row_factory = sqlite3.Row
connection.execute("PRAGMA query_only=ON")
record = {
    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_export": {"path": str(source), "sha256": hashlib.sha256(raw).hexdigest(),
        "content_hash": export["content_hash"], "generated_at_utc": export["generated_at_utc"],
        "plans": len(export["plans"]), "scored_call_count": export["scored_call_count"]},
    "public_entry_counts": {}, "public_new_plan_why": {},
}
for plan in export["plans"]:
    count = str(len(plan.get("entries") or []))
    record["public_entry_counts"][count] = record["public_entry_counts"].get(count, 0) + 1
    if plan["plan_id"] == "plan_5a5b965487f7fe4318d12140":
        record["public_new_plan_why"]["source_plan"] = {k: plan.get(k) for k in (
            "plan_id", "registered_at_utc", "asset_id", "registration_hash",
            "public_instrument", "entries", "scenario_analysis")}
row = connection.execute(
    "SELECT o.payload,d.public_object_url FROM outbox_messages o JOIN platform_dispatches d "
    "ON d.message_id=o.message_id WHERE o.work_item_id=? AND o.destination='telegram'",
    ("plan-status-post-67a7a2cb3435d7a6a19d1d07cf47d0e0",),
).fetchone()
payload = json.loads(row["payload"])
record["public_new_plan_why"].update(public_url=row["public_object_url"],
    published_text=payload["native_payload"].get("full_text") or payload["native_payload"]["text"])
revisions = connection.execute(
    "SELECT message_id,destination,status,created_at,payload FROM outbox_messages "
    "WHERE work_item_id='pinned-result-scorecard-v1' ORDER BY rowid DESC"
).fetchall()
latest = next(r for r in revisions if r["destination"] == "internal:pinned-result-scorecard")
saved = json.loads(latest["payload"])
rendered = project({"status": export, "transitions": transitions}, retained_rows=saved["rows"])
score = max(export["scored_calls"], key=lambda r: r["scored_at_utc"])
readback = next(r for r in revisions if r["destination"] == "internal:pinned-result-scorecard-readback")
latency = (datetime.fromisoformat(readback["created_at"]) -
    datetime.fromisoformat(score["scored_at_utc"].replace("Z", "+00:00"))).total_seconds()
record["scorecard"] = {
    "public_url": "https://t.me/CapitalChronicle/134",
    "source_latest_score": {k: score[k] for k in ("plan_id", "result", "resolved_at_utc", "scored_at_utc")},
    "confirmed_at_utc": readback["created_at"], "latency_seconds_from_main_score": latency,
    "within_60_minutes": 0 <= latency <= 3600,
    "same_pinned_message_id": pinned.get("message_id") == 134,
    "current_export_projection_equals_bot_api_text": rendered["text"] == pinned["text"],
    "stored_confirmed_revision_equals_bot_api_text": saved["text"] == pinned["text"],
    "counts": saved["counts"],
    "anchor_count": sum(r["destination"] == "internal:pinned-result-scorecard-anchor" for r in revisions),
    "anchor_statuses": [r["status"] for r in revisions if r["destination"] == "internal:pinned-result-scorecard-anchor"],
    "bound_objects": [json.loads(r["payload"]) for r in revisions if r["destination"] == "internal:pinned-result-scorecard-object"],
}
route = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\route-1900\20261110T121457Z\result.json")
value = json.loads(route.read_bytes())
record["digest"] = {"source_path": str(route), "source_sha256": hashlib.sha256(route.read_bytes()).hexdigest(),
    **{k: value[k] for k in ("digest_id", "final_route_state", "public_object_url", "articles",
        "first_blocking_cause", "recorded_at_utc")}}
assist = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc338-cpi-preview-20261110-v1\agy_light_assist_v1.json")
value = json.loads(assist.read_bytes())
record["agy"] = {"source_path": str(assist), "source_sha256": hashlib.sha256(assist.read_bytes()).hexdigest(),
    **{k: value.get(k) for k in ("status", "cause", "model", "effort", "configuration_status",
        "publisher_decisions", "flags", "started_utc", "ended_utc")}}
freeze = Path(r"A:\Capital Chronicle\ResearchRuns\frozen-public-calls\bls-cpi-20261110.json")
record["freeze"] = {"path": str(freeze), "exists": freeze.exists(),
    "fallback_event": "bls-ppi-20261113", "retained_cc338_result": "docs/publisher/CC-338/run-20261110/FINAL.json"}
(out / "consumer-evidence.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
connection.close()
print(json.dumps({"scorecard": record["scorecard"], "entry_counts": record["public_entry_counts"],
    "freeze_exists": record["freeze"]["exists"], "agy_status": record["agy"]["status"]}))
