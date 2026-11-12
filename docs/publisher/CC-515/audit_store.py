"""Read-only CC-515 channel evidence. Writes only the named item evidence file.

No credentials, browser calls, publication, deployment or production-store writes.
Retains fixed cause codes and exact attempt identities, never public copy/tool bytes.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

STORE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")
START = "2026-11-09T17:00:00Z"
END = "2026-11-12T17:00:00Z"
RESTORED_ARTICLE_ROUTES_AT = "2026-11-11T00:08:20.233397+00:00"


def clock(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def audit(store=STORE):
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(store.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN")
    dispatches = [dict(r) for r in conn.execute("SELECT d.*, o.work_item_id, o.payload FROM platform_dispatches d "
        "JOIN outbox_messages o USING(message_id) WHERE julianday(d.dispatched_at)>=julianday(?) "
        "AND julianday(d.dispatched_at)<julianday(?) ORDER BY d.dispatched_at, d.dispatch_id", (START, END))]
    candidates = defaultdict(list)

    def cause(dispatch_id, at, value, evidence, **extra):
        if value and isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_:./ -]{1,200}", value):
            candidates[dispatch_id].append({"at_utc": at, "cause": value, "evidence": evidence, **extra})

    native = [dict(r) for r in conn.execute("SELECT message_id,payload,created_at FROM outbox_messages "
        "WHERE destination='internal:native-neo-tool' AND julianday(created_at)>=julianday(?) "
        "AND julianday(created_at)<julianday(?) ORDER BY created_at, message_id", (START, END))]
    native_by_id = {r["message_id"]: r for r in native}
    requests_per_day = Counter()
    internal_records_per_day = Counter()
    for row in native:
        packet = json.loads(row["payload"])
        local_day = (clock(row["created_at"]).timestamp() + 7 * 3600)
        day = datetime.fromtimestamp(local_day, timezone.utc).date().isoformat()
        internal_records_per_day[day] += 1
        request = packet.get("request")
        if not isinstance(request, dict):
            continue
        requests_per_day[day] += 1
        response = native_by_id.get("native-neo-" + sha256_of([
            packet["operation_id"], request["request_sha256"], "response"]))
        if not response:
            continue
        result = json.loads(response["payload"]).get("result") or {}
        if result.get("status") != "FAILED_BEFORE_WRITE":
            continue
        cause(request.get("dispatch_attempt_identity"), response["created_at"],
            result.get("reason_code") or result.get("safe_error_classification"),
            "outbox:" + response["message_id"],
            detail=result.get("safe_error_classification"), request_sha256=request["request_sha256"])
    for row in conn.execute("SELECT incident_id,description,created_at FROM incidents WHERE "
                            "julianday(created_at)>=julianday(?) ORDER BY created_at", (START,)):
        try:
            data = json.loads(row["description"])
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("status") == "DEFINITE_NO_WRITE":
            cause(data.get("dispatch_id"), row["created_at"], data.get("reason_code") or
                  data.get("safe_error_classification"), "incident:" + row["incident_id"])
    by_work_destination = {(r["work_item_id"],r["platform"]):r["dispatch_id"] for r in dispatches}
    run_folder = store.parent / "daily_app_outputs/plan_status_post_runs"
    for day in ("20261109", "20261110", "20261111", "20261112"):
        path = run_folder / ("runs-" + day + ".jsonl")
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle,1):
                record = json.loads(line)
                at = record.get("at_utc")
                for post in record.get("posts") or []:
                    for dest, value in (post.get("destination_causes") or {}).items():
                        did = by_work_destination.get((post.get("key"),dest))
                        if did and (post.get("per_destination") or {}).get(dest) == "DEFINITE_NO_WRITE" and value not in {
                                "RECONCILED_ABSENT_SAFE_TO_RETRY", "DEFINITE_NO_WRITE", "NATIVE_NEO_TOOL_PENDING",
                                "RECONCILIATION_PENDING", "NOT_DISPATCHED"}:
                            cause(did,at,value,str(path)+":"+str(line_number))
                for post in record.get("analysis_links") or []:
                    for dest, failure in (post.get("first_failures") or {}).items():
                        if isinstance(failure,dict):
                            cause(failure.get("dispatch_id"), at, failure.get("reason_code") or
                                  failure.get("safe_error_classification"),str(path)+":"+str(line_number))
    no_writes = []
    by_destination = defaultdict(Counter)
    first_causes = defaultdict(Counter)
    for dispatch in dispatches:
        dest = dispatch["platform"]
        by_destination[dest][dispatch["status"]] += 1
        if dispatch["status"] not in {"DEFINITE_NO_WRITE", "DERIVATIVE_EXPIRED_STALE_NO_WRITE",
                                      "DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE"}:
            continue
        did = dispatch["dispatch_id"]
        for row in conn.execute("SELECT readback_id,readback_data,read_at FROM readbacks "
                                "WHERE dispatch_id=? ORDER BY read_at", (did,)):
            data = json.loads(row["readback_data"])
            if data.get("reason_code"):
                cause(did, row["read_at"], data["reason_code"], "readback:" + row["readback_id"])
        rid = "reconciliation_" + did.removeprefix("dispatch_")
        rec = conn.execute("SELECT status,reconciled_at FROM reconciliations WHERE reconciliation_id=?", (rid,)).fetchone()
        if rec and ("PROHIBITED" in rec["status"] or "STALE" in rec["status"]):
            cause(did, dispatch["dispatched_at"], rec["status"], "reconciliation:" + rid)
        intent = json.loads(dispatch["payload"])
        image_failure = intent.get("post_image_floor_failure")
        if image_failure:
            cause(did, dispatch["dispatched_at"], "EVERY_POST_IMAGE_REQUIRED:" + dest,
                  "outbox:" + dispatch["message_id"] + ".post_image_floor_failure")
        attempts = []
        seen = set()
        for candidate in sorted(candidates[did], key=lambda r: clock(r["at_utc"])):
            identity = (candidate["cause"], candidate.get("detail"))
            if identity not in seen:
                attempts.append(candidate)
                seen.add(identity)
        first = attempts[0] if attempts else {"cause": "ATTEMPT_CAUSE_NOT_RETAINED",
            "evidence": "dispatch:" + did, "at_utc": dispatch["dispatched_at"]}
        first_causes[dest][first["cause"]] += 1
        no_writes.append({"destination": dest, "dispatch_id": did, "message_id": dispatch["message_id"],
            "work_item_id": dispatch["work_item_id"], "dispatched_at_utc": dispatch["dispatched_at"],
            "status": dispatch["status"], "first_failure": first, "attempt_causes": attempts})
    article_routes = {}
    for destination in ("linkedin_company","youtube"):
        new_rows = conn.execute("SELECT message_id,created_at FROM outbox_messages WHERE destination=? "
            "AND julianday(created_at)>=julianday(?) ORDER BY created_at",
            (destination,RESTORED_ARTICLE_ROUTES_AT)).fetchall()
        confirmed = conn.execute("SELECT dispatch_id,public_object_id,public_object_url FROM platform_dispatches "
            "WHERE platform=? AND status='DISPATCH_CONFIRMED' AND julianday(dispatched_at)>=julianday(?)",
            (destination,RESTORED_ARTICLE_ROUTES_AT)).fetchall()
        article_routes[destination] = {"source":"docs/publisher/CC-454/integration.json",
            "installed_at_utc":RESTORED_ARTICLE_ROUTES_AT,
            "new_article_intents_since_install":[dict(r) for r in new_rows],
            "confirmed_since_install":[dict(r) for r in confirmed],
            "first_cause":"NO_NEW_ARTICLE_INTENT_SINCE_CC454_INSTALL" if not new_rows else None}
    pending = []
    for row in conn.execute("SELECT message_id,status,payload FROM outbox_messages WHERE destination=? "
                            "AND status IN ('READY_FOR_PUBLISHER','PUBLISHING')", ("internal:plan-status-post",)):
        payload = json.loads(row["payload"])
        age = (now - clock(payload["at_utc"])).total_seconds() / 3600
        pending.append({"key": row["message_id"], "status": row["status"], "kind": payload.get("kind"),
            "age_hours": round(age, 3), "parent_key": payload.get("parent_key"),
            "source_at_utc": payload["at_utc"]})
    conn.close()
    return {"observed_at_utc": now.isoformat(), "period_start_utc": START, "period_end_utc": END,
        "period_days_gmt7": ["2026-11-10", "2026-11-11", "2026-11-12"],
        "period_complete": now >= clock(END), "article_routes_after_reopening":article_routes,
        "store": str(store), "store_access": "sqlite mode=ro; one read transaction",
        "dispatch_counts": dict(by_destination), "first_cause_counts": dict(first_causes),
        "no_writes": no_writes, "internal_neo_request_packets_by_gmt7_day": dict(requests_per_day),
        "internal_neo_records_by_gmt7_day": dict(internal_records_per_day),
        "pending_posts": pending, "pending_older_than_24_hours": sum(r["age_hours"] > 24 for r in pending),
        "public_write_performed": False, "production_store_writes": 0}


if __name__ == "__main__":
    output = Path(__file__).with_name("channel-health.json")
    data = audit()
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(output), "bytes": output.stat().st_size,
        "sha256": sha256(output.read_bytes()).hexdigest(),
        "dispatch_counts": data["dispatch_counts"], "first_cause_counts": data["first_cause_counts"],
        "pending_older_than_24_hours": data["pending_older_than_24_hours"]}, indent=2))
