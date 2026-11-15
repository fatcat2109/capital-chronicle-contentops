"""Re-read CC-509's original live consumers without fetching or sending anything.

SQLite is read-only. Only item evidence is written. Raw target text, private
chat identities, provider responses and image bytes stay in their original stores.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops import publication_image_contract_v1 as image  # noqa: E402
from live_contentops import public_market_quote_v1 as quotes  # noqa: E402
from live_contentops import x_reply_bot_v1 as bot  # noqa: E402
from live_contentops import x_reply_pack_v1 as packs  # noqa: E402
from live_contentops.published_images_v1 import PublishedImages  # noqa: E402

OUT = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
SINCE = "2026-11-12T11:48:34.290020+00:00"  # Original final source-order installation.
PLAN = "plan-analysis-plan_230a9464a193ca7a377d0c41"
POST = "plan-status-post-37f4a7ca63df69d5864655fbe2494bae"
SOURCE_FILES = (
    "live_contentops/public_market_quote_v1.py",
    "live_contentops/chart_price_reference_v1.py",
    "live_contentops/tradingview_snapshot_v1.py",
    "live_contentops/publication_image_contract_v1.py",
    "live_contentops/publication_coordinator_v1.py",
    "live_contentops/published_images_v1.py",
    "live_contentops/x_reply_fact_sources_v1.py",
    "live_contentops/x_reply_fact_policy_v1.py",
    "live_contentops/x_reply_pack_v1.py",
    "live_contentops/x_reply_bot_v1.py",
    "scripts/plan_status_posts.py",
)


def digest(raw):
    return sha256(raw if isinstance(raw, bytes) else raw.encode()).hexdigest()


def fingerprint(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}


def model_record(call):
    keys = ("status", "configured_model", "configured_effort", "runtime_model",
            "runtime_effort", "configuration_status", "elapsed_seconds",
            "started_at_utc", "ended_at_utc", "observed_session_id")
    return {key: call.get(key) for key in keys}


def delivered_quote(db, event):
    receipt = json.loads(event["payload"])
    delivery = db.execute("SELECT * FROM outbox_messages WHERE message_id=?",
                          (receipt["delivery_id"],)).fetchone()
    payload = json.loads(delivery["payload"])
    row = db.execute("SELECT * FROM outbox_messages WHERE message_id=?",
                     (payload["pack_message_id"],)).fetchone()
    pack = json.loads(row["payload"])
    item = next(i for i in pack["items"] if i["post_id"] == payload["post_id"])
    checked_at = packs.clock(receipt["fact_binding"]["checked_at_utc"])
    checked = packs.recheck_mobile_item(None, item, now=checked_at)
    assert checked["kind"] == "session"
    assert checked["age_text"] == receipt["fact_binding"]["age_text"]
    bound = item["sources"][0]["artifact_binding"]
    assert bound["kind"] == "quote_observation"
    observation = quotes.resolve(bound["path"], bound["sha256"])
    quotes.validate(observation, observation["market"], now=checked_at)
    posted, sent = packs.clock(item["post_time_utc"]), packs.clock(receipt["delivered_at_utc"])
    observed = packs.clock(observation["observed_at_utc"])
    assert observed.astimezone(packs.fact_policy.ET).date() == posted.astimezone(packs.fact_policy.ET).date()
    minutes = (sent - posted).total_seconds() / 60
    assert 0 <= minutes <= 15 and abs(minutes - receipt["post_to_delivery_minutes"]) < 1e-8
    assert delivery["status"] == "DELIVERED" and receipt["public_submit_actions"] == 0
    assert observation["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    rendered_item = deepcopy(item)
    rendered_item["fact_binding"] = receipt["fact_binding"]
    rendered = bot.message_for(rendered_item, number=1, now=checked_at)
    age_line = next(unescape(s) for s in rendered.splitlines() if s.startswith("Fact age: "))
    assert "min old" in age_line
    runs = db.execute(
        "SELECT * FROM outbox_messages WHERE destination=? AND created_at>=? AND created_at<=? "
        "ORDER BY created_at", (bot.RUNS, row["created_at"],
                                (packs.clock(event["created_at"]) + timedelta(minutes=1)).isoformat())).fetchall()
    run_row = next(r for r in runs if json.loads(r["payload"]).get("pack", {}).get("store_message_id") == row["message_id"])
    run = json.loads(run_row["payload"])
    fetches = run["quote_fetches"]
    matched = [f for f in fetches if f.get("source_symbol") == observation["source_symbol"]
               and f.get("observed_at_utc") == observation["observed_at_utc"] and f.get("status") == "USED"]
    assert matched and matched[0]["fetch_seconds"] >= 0
    return {
        "delivery_id": delivery["message_id"], "delivery_payload_sha256": digest(delivery["payload"]),
        "receipt_id": event["message_id"], "receipt_payload_sha256": digest(event["payload"]),
        "pack_message_id": row["message_id"], "pack_payload_sha256": digest(row["payload"]),
        "telegram_message_id": receipt["message_id"], "post_id": item["post_id"],
        "target_text_sha256": digest(item["post_text"]), "draft_text_sha256": digest(item["draft_text"]),
        "posted_at_utc": item["post_time_utc"], "delivered_at_utc": receipt["delivered_at_utc"],
        "post_to_delivery_minutes": minutes, "fact_age_seconds_at_delivery": (sent - observed).total_seconds(),
        "age_line_formatter_replay": age_line,
        "age_evidence": "Original send-time binding and production formatter; no Telegram body or phone-screen read.",
        "source_observation": {**observation, "artifact": bound},
        "source_hash_and_production_fact_recheck": "PASS",
        "run_id": run_row["message_id"], "run_payload_sha256": digest(run_row["payload"]),
        "run_artifact": run["artifact_path"], "fetch_seconds_per_symbol": fetches,
        "stage_seconds": receipt["stage_seconds"],
        "editorial_calls": {k: model_record(v) for k, v in pack.get("editorial_call", {}).items()},
    }


def posted_chart(db):
    register = RUNTIME / "published_images_v1.jsonl"
    rows = {r["record_id"]: r for r in PublishedImages(register).records()}
    candidates = [(r, i) for r in rows.values() if r["state"] == "PUBLISHED"
                  and not r.get("counts_as_article", True)
                  for i in r["images"] if i.get("image_type") == "TRADINGVIEW_MARKET_CHART"
                  and i.get("price_scale_check", {}).get("captured_at_utc", "") >= SINCE]
    candidates.sort(key=lambda pair: (pair[0]["published_at_utc"] or pair[0]["recorded_at_utc"], pair[0]["record_id"]))
    assert candidates, "No post-install published plan chart."
    first, lead = candidates[0]
    check = lead["price_scale_check"]
    capture_path = RUNTIME / "daily_app_outputs" / "plan_analysis" / PLAN / "tradingview_capture_v1.json"
    capture = json.loads(capture_path.read_bytes())
    snapshot = capture["snapshot"]
    assert snapshot["sha256"] == check["chart_sha256"]
    assert fingerprint(snapshot["path"])["sha256"] == snapshot["sha256"]
    measured = image.compare_scale(check["market"], snapshot, check["quote"])
    assert measured == check
    quote = check["quote"]
    assert quote["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    observation = quotes.resolve(quote["source_path"], quote["source_sha256"])
    quotes.validate(observation, check["market"], now=quotes.utc(check["captured_at_utc"]), max_age_seconds=120)
    assert observation["value"] == quote["price"]
    assert observation["observed_at_utc"] == quote["quoted_at_utc"]
    assert observation["source_symbol"] == quote["source_symbol"]
    assert quotes.utc(observation["known_at_utc"]) <= quotes.utc(check["captured_at_utc"])
    dispatches = db.execute(
        "SELECT p.*,o.work_item_id,o.payload FROM platform_dispatches p "
        "JOIN outbox_messages o ON o.message_id=p.message_id "
        "WHERE o.work_item_id IN (?,?) AND p.status='DISPATCH_CONFIRMED' ORDER BY p.dispatched_at",
        (PLAN, POST)).fetchall()
    confirmed = []
    for row in dispatches:
        payload = json.loads(row["payload"])
        readbacks = db.execute("SELECT * FROM readbacks WHERE dispatch_id=? ORDER BY read_at",
                               (row["dispatch_id"],)).fetchall()
        assert readbacks
        confirmed.append({**{k: row[k] for k in row.keys() if k != "payload"},
            "outbox_payload_sha256": digest(row["payload"]),
            "selected_media_asset_ids": payload["native_payload"].get("media_asset_ids", []),
            "readbacks": [{"id": r["readback_id"], "read_at_utc": r["read_at"],
                           "payload_sha256": digest(r["readback_data"])} for r in readbacks]})
    assert {"substack", "telegram", "discord", "threads"} <= {r["platform"] for r in confirmed}
    assert first["canonical_url"] == next(r["public_object_url"] for r in confirmed if r["platform"] == "substack")
    bound_records = [{k: r.get(k) for k in ("record_id", "piece_id", "state", "destination",
                     "published_at_utc", "recorded_at_utc", "canonical_url")}
                     for r, i in candidates if i["price_scale_check"]["chart_sha256"] == snapshot["sha256"]]
    return {"first_published_chart_record": first["record_id"],
        "capture_metadata": fingerprint(capture_path), "original_image": fingerprint(snapshot["path"]),
        "published_lead_image_sha256": lead["sha256"],
        "price_scale_check": check, "source_observation": observation,
        "comparison_and_immutable_source_recheck": "PASS", "publication_records": bound_records,
        "confirmed_dispatches": confirmed,
        "distinct_original_captures": 1,
        "record_count_note": "Repeated registrations and destinations of this capture count once.",
        "register_snapshot": fingerprint(register)}


def main(*, output=OUT / "readback.json"):
    now = datetime.now(timezone.utc).isoformat()
    db_path = RUNTIME / "contentops_daily_app_v1.sqlite3"
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True, timeout=5) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        events = db.execute(
            "SELECT * FROM outbox_messages WHERE destination=? AND created_at>=? AND created_at<=? ORDER BY created_at,message_id",
            (bot.EVENTS, SINCE, now)).fetchall()
        receipts = [r for r in events if json.loads(r["payload"]).get("kind") == "private_draft_delivered"]
        assert len(receipts) >= 3
        deliveries = [delivered_quote(db, r) for r in receipts[:3]]
        chart = posted_chart(db)
        latest = db.execute(
            "SELECT * FROM outbox_messages WHERE destination=? AND created_at<=? ORDER BY created_at DESC LIMIT 1",
            (bot.RUNS, now)).fetchone()
        run = json.loads(latest["payload"])
    installed = {}
    for name in SOURCE_FILES:
        live, lane = fingerprint(LIVE / name), fingerprint(REPO / name)
        assert live["sha256"] == lane["sha256"], name
        installed[name] = {"installed": live, "worktree_sha256": lane["sha256"], "matches": True}
    result = {"item": "CC-509", "read_at_utc": now, "original_final_installation_at_utc": SINCE,
        "acceptance": "PASS_LIVE_REPLY_QUOTE_AND_POSTED_COMPARED_CHART",
        "database_access": "SQLite mode=ro and query_only=ON, one read transaction.",
        "executed_source_root": str(REPO),
        "operating_head_at_read": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
        "next_three_natural_deliveries": deliveries, "posted_chart": chart,
        "latest_bot_run": {"message_id": latest["message_id"], "payload_sha256": digest(latest["payload"]),
                           **{k: run.get(k) for k in ("status", "cause", "started_at_utc", "ended_at_utc", "artifact_path")}},
        "installed_sources": installed, "phone_open_observed": False,
        "public_or_private_messages_sent_by_this_readback": 0, "source_fetches_by_this_readback": 0,
        "model_calls_by_this_readback": 0, "schedule_changed": False,
        "limits": "Bot API confirms private delivery, not phone viewing or Jim sending an X reply. Existing chart limits remain; CC-489 owns three-day calibration."}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acceptance": result["acceptance"], "delivery_count": len(deliveries),
                      "chart_market": chart["price_scale_check"]["market"],
                      "chart_source": chart["price_scale_check"]["quote"]["source"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT / "readback.json")
    main(output=parser.parse_args().output)
