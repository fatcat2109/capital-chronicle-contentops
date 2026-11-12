"""Read CC-515's live consumer and exact queue without changing production state."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

STORE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")


def observe(since=None):
    now = datetime.now(timezone.utc)
    local = now.astimezone(timezone(timedelta(hours=7)))
    day_start = local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    conn = sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN")
    roots = []
    copies = []
    for record in conn.execute("SELECT message_id,status,payload FROM outbox_messages WHERE destination=?",
                               (posts.DESTINATION,)):
        row = json.loads(record["payload"])
        key = record["message_id"]
        roots.append({"key": key, "status": record["status"], "at_utc": row["at_utc"],
            "age_hours": round(posts._age_minutes(row, now) / 60, 4),
            "payload_sha256": sha256(record["payload"].encode()).hexdigest(),
            "format": row.get("format"), "kind": row.get("kind")})
        plan_hash = sha256(("plan-status-post:" + key).encode()).hexdigest()
        for destination in ("telegram", "discord", "threads", "x", "substack_notes", "linkedin"):
            ids = DurablePublicationCoordinator._ids(key, plan_hash, destination)
            dispatch = conn.execute("SELECT dispatch_id,status,public_object_id,public_object_url "
                "FROM platform_dispatches WHERE dispatch_id=?", (ids["dispatch_id"],)).fetchone()
            if dispatch:
                copies.append({"key": key, "destination": destination, **dict(dispatch)})
    packets = Counter()
    packet_actions = Counter()
    records = 0
    since_records = 0
    for record in conn.execute("SELECT payload,created_at FROM outbox_messages WHERE "
            "destination='internal:native-neo-tool' AND julianday(created_at)>=julianday(?)",
            (day_start.isoformat(),)):
        records += 1
        packet = json.loads(record["payload"])
        fresh = since and posts._utc(record["created_at"]) >= posts._utc(since)
        since_records += bool(fresh)
        request = packet.get("request")
        if isinstance(request, dict):
            packets["today"] += 1
            packet_actions[request.get("action", "UNKNOWN")] += 1
            if fresh:
                packets["since_install"] += 1
    pending = [r for r in roots if r["status"] in {posts.READY, "PUBLISHING"}]
    settlement_causes = Counter()
    for record in conn.execute("SELECT description FROM incidents WHERE incident_id LIKE 'plan-post-settled-%'"):
        settlement_causes[json.loads(record["description"])["cause"]] += 1
    recent_dispatches = [dict(r) for r in conn.execute("SELECT dispatch_id,platform,status,dispatched_at,"
        "public_object_id,public_object_url FROM platform_dispatches WHERE platform IN "
        "('x','linkedin','linkedin_company','youtube') AND julianday(dispatched_at)>=julianday(?) "
        "ORDER BY dispatched_at DESC LIMIT 20", (since or day_start.isoformat(),))]
    conn.close()
    run_path = STORE.parent / posts.RUN_RECORD_FOLDER / ("runs-" + now.strftime("%Y%m%d") + ".jsonl")
    runs = []
    if run_path.is_file():
        for line in run_path.read_text(encoding="utf-8").splitlines()[-3:]:
            value = json.loads(line)
            runs.append({"record_sha256": sha256(line.encode()).hexdigest(),
                **{k: value[k] for k in ("at_utc", "status", "cause", "queued", "existing",
                "export_generated_at_utc", "export_age_seconds", "quarantined_rows", "publication",
                "posts_by_status", "posts", "neo_stored_requests", "analysis_links",
                "pending_post_queue") if k in value}})
    return {"observed_at_utc": now.isoformat(), "observed_at_gmt7": local.isoformat(),
        "store_access": "mode=ro; one read transaction", "since_install_utc": since,
        "pending_posts": len(pending), "pending_older_than_24_hours": sum(r["age_hours"] > 24 for r in pending),
        "root_status_counts": dict(Counter(r["status"] for r in roots)), "roots": roots,
        "dispatches": copies, "settlement_causes": dict(settlement_causes),
        "neo_request_packets": dict(packets), "neo_request_actions_today": dict(packet_actions),
        "neo_internal_records_today": records, "neo_internal_records_since_install": since_records,
        "recent_destination_dispatches": recent_dispatches, "last_minute_records": runs,
        "minute_record_path": str(run_path),
        "public_write_performed_by_observer": False, "production_store_writes_by_observer": 0}


if __name__ == "__main__":
    output = Path(sys.argv[1])
    result = observe(sys.argv[2] if len(sys.argv) > 2 else None)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(output), "observed_at_gmt7": result["observed_at_gmt7"],
        "pending_posts": result["pending_posts"], "pending_older_than_24_hours": result["pending_older_than_24_hours"],
        "neo_request_packets": result["neo_request_packets"], "settlement_causes": result["settlement_causes"]}))
