"""Verify CC-515's completed GMT+7 day from the existing read-only store and runs."""
import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
STORE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")
GMT7 = timezone(timedelta(hours=7))


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def verify(day):
    now = datetime.now(timezone.utc)
    start = datetime.combine(date.fromisoformat(day), time(), GMT7).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    assert now >= end, "The requested day is unfinished"
    baseline = json.loads((HERE / "live-before-integration.json").read_bytes())
    baseline_keys = {r["key"] for r in baseline["roots"]}
    conn = sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN")
    roots = {r["message_id"]: dict(r) for r in conn.execute(
        "SELECT message_id,status,payload,created_at FROM outbox_messages "
        "WHERE destination='internal:plan-status-post'")}
    dispatches = {r["dispatch_id"]: dict(r) for r in conn.execute(
        "SELECT dispatch_id,status,public_object_id,public_object_url FROM platform_dispatches")}
    changed_drafts = []
    issued_keys = {r["key"] for r in baseline["dispatches"]}
    for old in baseline["roots"]:
        assert old["key"] in roots, ("Root lost", old["key"])
        current = roots[old["key"]]
        digest = sha256(current["payload"].encode()).hexdigest()
        if digest == old["payload_sha256"]:
            continue
        # An unissued draft can complete its existing editorial preparation.
        # An already dispatched root cannot use that exception.
        assert old["key"] not in issued_keys, ("Issued root changed", old["key"])
        payload = json.loads(current["payload"])
        assert payload.get("reader_contract") == "CC466_V1"
        calls = payload.get("variant_calls") or []
        assert calls and all(c.get("ended_at_utc") for c in calls)
        first = conn.execute(
            "SELECT min(d.dispatched_at) FROM platform_dispatches d "
            "JOIN outbox_messages o USING(message_id) WHERE o.work_item_id=?",
            (old["key"],)).fetchone()[0]
        assert first and all(utc(c["ended_at_utc"]) < utc(first) for c in calls)
        changed_drafts.append({"key": old["key"], "baseline_sha256": old["payload_sha256"],
            "current_sha256": digest, "baseline_had_dispatch": False,
            "reader_contract": payload["reader_contract"],
            "last_preparation_end_utc": max(c["ended_at_utc"] for c in calls),
            "first_dispatch_utc": first, "current_status": current["status"],
            "evidence": "docs/publisher/CC-432/resume-20261112/integration.json"})
    reconciled = []
    for old in baseline["dispatches"]:
        current = dispatches[old["dispatch_id"]]
        for field in ("public_object_id", "public_object_url"):
            assert not old[field] or old[field] == current[field], ("Public identity changed", old)
        if old["status"] != current["status"]:
            readbacks = [dict(r) for r in conn.execute(
                "SELECT readback_id,read_at FROM readbacks WHERE dispatch_id=? ORDER BY read_at",
                (old["dispatch_id"],))]
            assert readbacks, ("State change without readback", old["dispatch_id"])
            reconciled.append({"dispatch_id": old["dispatch_id"], "before": old["status"],
                               "after": current["status"], "readbacks": readbacks})
    pending = []
    for key, row in roots.items():
        if row["status"] in {"READY_FOR_PUBLISHER", "PUBLISHING"}:
            payload = json.loads(row["payload"])
            pending.append({"key": key, "age_hours": (now - utc(payload["at_utc"])).total_seconds() / 3600})
    assert not any(r["age_hours"] > 24 for r in pending), "Old work remains in the automatic queue"
    native = conn.execute(
        "SELECT message_id,payload,created_at FROM outbox_messages "
        "WHERE destination='internal:native-neo-tool' AND julianday(created_at)>=julianday(?) "
        "AND julianday(created_at)<julianday(?) ORDER BY created_at", (start.isoformat(), end.isoformat()))
    records = 0
    packets = []
    for row in native:
        records += 1
        request = json.loads(row["payload"]).get("request")
        if isinstance(request, dict):
            packets.append({"message_id": row["message_id"], "created_at_utc": row["created_at"],
                            "action": request.get("action"), "destination": request.get("destination")})
    assert len(packets) < 200 and records < 200
    outcomes = []
    for row in conn.execute(
        "SELECT d.dispatch_id,d.platform,d.status,d.dispatched_at,d.public_object_id,d.public_object_url "
        "FROM platform_dispatches d WHERE d.platform IN ('x','linkedin','linkedin_company','youtube') "
        "AND julianday(d.dispatched_at)>=julianday(?) ORDER BY d.dispatched_at",
        (baseline["observed_at_utc"],)):
        result = dict(row)
        result["causes"] = []
        for readback in conn.execute(
            "SELECT readback_id,read_at,readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at",
            (row["dispatch_id"],)):
            data = json.loads(readback["readback_data"])
            if data.get("reason_code"):
                result["causes"].append({"readback_id": readback["readback_id"],
                    "at_utc": readback["read_at"], "cause": data["reason_code"]})
        outcomes.append(result)
    article_routes = {}
    for destination in ("linkedin_company", "youtube"):
        rows = [dict(r) for r in conn.execute(
            "SELECT message_id,created_at,status FROM outbox_messages WHERE destination=? "
            "AND julianday(created_at)>=julianday(?) ORDER BY created_at",
            (destination, "2026-11-11T00:08:20.233397Z"))]
        article_routes[destination] = {"intents_since_cc454_install": rows,
            "cause": "NO_NEW_ARTICLE_INTENT_SINCE_CC454_INSTALL" if not rows else None}
    conn.close()
    times, statuses, phases, queue_samples = [], Counter(), Counter(), []
    folder = STORE.parent / "daily_app_outputs/plan_status_post_runs"
    source_files, x_causes, new_roots = [], {}, {}
    current_day = start.date()
    while current_day <= now.date():
        path = folder / ("runs-" + current_day.strftime("%Y%m%d") + ".jsonl")
        current_day += timedelta(days=1)
        if not path.is_file():
            continue
        source_files.append(str(path))
        for number, line in enumerate(path.open(encoding="utf-8"), 1):
            row = json.loads(line)
            at = utc(row["at_utc"])
            evidence = {"at_utc": row["at_utc"], "record_sha256": sha256(line.rstrip("\n").encode()).hexdigest(),
                        "source": str(path) + ":" + str(number)}
            if start <= at < end:
                times.append(at)
                statuses[row["status"]] += 1
                phases[row.get("phase", "DEFAULT")] += 1
                if row.get("pending_post_queue"):
                    queue_samples.append({**evidence, **row["pending_post_queue"]})
            if at < utc(baseline["observed_at_utc"]):
                continue
            for post in row.get("posts") or []:
                if post.get("key") and post["key"] not in baseline_keys:
                    item = {**evidence, "outcome": post}
                    history = new_roots.setdefault(post["key"], {"first": item})
                    history["latest"] = item
            for link in row.get("analysis_links") or []:
                if link.get("destination") == "x" and link.get("status") not in {
                        "DISPATCH_CONFIRMED", "RECONCILED_CONFIRMED", "SETTLED"}:
                    x_causes.setdefault(link.get("status"), {**evidence, "outcome": link})
    times.sort()
    assert times and queue_samples
    assert queue_samples[-1]["older_than_24_hours"] == 0
    assert x_causes and all(r["cause"] or r["intents_since_cc454_install"] for r in article_routes.values())
    return {"observed_at_utc": now.isoformat(), "observed_at_gmt7": now.astimezone(GMT7).isoformat(),
        "day_gmt7": day, "start_utc": start.isoformat(), "end_utc": end.isoformat(), "day_complete": True,
        "store_access": "sqlite mode=ro; one read transaction", "production_store_writes": 0,
        "public_writes": 0, "neo_request_packets": len(packets), "neo_internal_records": records,
        "request_packets": packets, "below_200": True,
        "preservation": {"baseline_roots_retained": len(baseline["roots"]),
            "baseline_dispatches_retained": len(baseline["dispatches"]),
            "missing_roots": [], "missing_dispatches": [], "changed_public_identities": [],
            "issued_root_payload_changes": [], "pre_dispatch_draft_preparation": changed_drafts,
            "dispatch_state_changes_with_readbacks": reconciled},
        "current_root_statuses": dict(Counter(r["status"] for r in roots.values())),
        "current_pending": pending, "current_pending_older_than_24_hours": 0,
        "run_coverage": {"count": len(times), "first_at_utc": times[0].isoformat(),
            "last_at_utc": times[-1].isoformat(), "statuses": dict(statuses), "phases": dict(phases),
            "largest_gap_seconds": max((b-a).total_seconds() for a,b in zip(times,times[1:])),
            "source_files": source_files, "last_day_queue_observation": queue_samples[-1],
            "queue_samples_older_than_24_hours": sum(q["older_than_24_hours"] > 0 for q in queue_samples)},
        "new_post_outcomes": new_roots, "x_analysis_outcomes": x_causes,
        "destination_dispatch_outcomes": outcomes, "article_routes": article_routes,
        "scope": "CC-515 queue/request acceptance; stale exports and absence of fresh articles still limit throughput"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--day", required=True)
    args = parser.parse_args()
    result = verify(args.day)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(args.output), **{k: result[k] for k in (
        "day_gmt7", "neo_request_packets", "neo_internal_records", "current_pending_older_than_24_hours")}}))
