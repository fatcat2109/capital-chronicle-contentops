"""One query-only CC-199 reading through the installed publication consumers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
STORE = LIVE.parent / "Runtime/ContentOps/contentops_daily_app_v1.sqlite3"
sys.path.insert(0, str(LIVE))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_publication_v1 import DESTINATION, publication_projection
from live_contentops.native_publication_latency_v1 import (
    FINISHED_PIECE_YOUTUBE_EXCEPTION_AT, publication_timing,
)
from live_contentops.neo_destination_handoff_v1 import suspended_routes
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def info(path):
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()).hexdigest()}


def project(conn, run, reviews):
    # Native source/write payloads and retained media are outside this reading.
    # Only the installed timing consumer's exact input rows are loaded.
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM outbox_messages WHERE work_item_id IN (?,?) "
        "AND destination IN (?,?,?) ORDER BY created_at,message_id",
        (run, "cc-opportunity-" + sha256_of(run), DESTINATION,
         "internal:native-publication-timing", "internal:native-neo-tool"))]
    rows += [{**dict(r), "payload": "{}"} for r in conn.execute(
        "SELECT message_id,work_item_id,destination,status,created_at "
        "FROM outbox_messages WHERE work_item_id=? AND destination NOT LIKE 'internal:%'",
        (run,))]
    extra = {"native-operation-binding-" + sha256_of(run)}
    for row in rows:
        if row["destination"] == "internal:native-neo-tool":
            request = json.loads(row["payload"]).get("request", {})
            if request.get("request_sha256"):
                extra.update("native-neo-" + sha256_of([run, request["request_sha256"], kind])
                             for kind in ("started", "response"))
    for message in sorted(extra - {r["message_id"] for r in rows}):
        row = conn.execute("SELECT * FROM outbox_messages WHERE message_id=?", (message,)).fetchone()
        if row:
            rows.append(dict(row))
    rows.sort(key=lambda r: (r["created_at"], r["message_id"]))
    dispatches = [dict(r) for r in conn.execute(
        "SELECT p.* FROM platform_dispatches p JOIN outbox_messages o "
        "ON o.message_id=p.message_id WHERE o.work_item_id=? "
        "ORDER BY p.dispatched_at,p.dispatch_id", (run,))]
    reconciliations = [dict(r) for r in conn.execute(
        "SELECT * FROM reconciliations WHERE work_item_id=? ORDER BY reconciled_at", (run,))]
    readbacks = [dict(r) for r in conn.execute(
        "SELECT r.* FROM readbacks r JOIN platform_dispatches p ON p.dispatch_id=r.dispatch_id "
        "JOIN outbox_messages o ON o.message_id=p.message_id WHERE o.work_item_id=? "
        "ORDER BY r.read_at,r.readback_id", (run,))]
    result = publication_projection(rows, dispatches, reconciliations,
        run_id=run, reviews=reviews, readbacks=readbacks)
    if not any(r["destination"] == DESTINATION for r in rows):
        # Structured pieces have their own contract and no native approval clock.
        # Retain their real channel observations without inventing that clock.
        statuses = {r["reconciliation_id"]: r["status"] for r in reconciliations}
        entries = []
        for row in rows:
            if row["destination"].startswith("internal:") or not row["message_id"].startswith("outbox_"):
                continue
            dispatch_id = "dispatch_" + row["message_id"].removeprefix("outbox_")
            original = next((d for d in dispatches if d["dispatch_id"] == dispatch_id), {})
            dispatch = DurablePublicationCoordinator.effective_dispatch(original, dispatches)
            actual_id = dispatch.get("dispatch_id", dispatch_id)
            entries.append({"destination": row["destination"], "dispatch_id": actual_id,
                "status": dispatch.get("status", row["status"]),
                "public_object_id": dispatch.get("public_object_id"),
                "public_object_url": dispatch.get("public_object_url"),
                "reconciliation_status": statuses.get(
                    "reconciliation_" + actual_id.removeprefix("dispatch_"))})
        result["destinations"] = entries
        result["timing"] = publication_timing(rows, reviews, run_id=run,
            destinations=entries, readbacks=readbacks)
    timing = result["timing"]
    return {"run_id": run, "state": result["state"], "timing": timing,
        "destinations": [{k: e.get(k) for k in ("destination", "dispatch_id", "status",
            "reconciliation_status", "public_object_id", "public_object_url")}
            for e in result["destinations"]],
        "record_counts": {"dispatches": len(dispatches), "readbacks": len(readbacks)},
        "passes_current_acceptance": bool(
            timing["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"]
            and timing.get("data_to_publication", {}).get("within_60_minutes") is True)}


with sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("BEGIN")
    assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
    reviews = [dict(r) for r in conn.execute(
        "SELECT * FROM review_records WHERE reviewer_ref=? ORDER BY reviewed_at,review_id",
        ("NATIVE_DESKTOP_ARTICLE_REVIEW",))]
    runs = sorted({json.loads(r["notes"])["run_id"] for r in reviews})
    approvals = {run: publication_timing([], reviews, run_id=run, destinations=[])["text_approved_at_utc"]
                 for run in runs}
    new_runs = sorted((run for run in runs if approvals[run]
        and utc(approvals[run]) >= utc(FINISHED_PIECE_YOUTUBE_EXCEPTION_AT)),
        key=lambda run: (utc(approvals[run]), run))
    pieces = [project(conn, run, reviews) for run in new_runs[:3]]
    baseline_runs = []
    for row in conn.execute(
        "SELECT o.work_item_id FROM platform_dispatches d JOIN outbox_messages o "
        "ON o.message_id=d.message_id WHERE d.platform='substack' "
        "AND d.status='DISPATCH_CONFIRMED' AND d.public_object_id IS NOT NULL "
        "ORDER BY d.dispatched_at DESC"):
        run = row[0]
        if run.startswith(("cc143-digest-", "plan-analysis-")) or run in baseline_runs:
            continue
        baseline_runs.append(run)
        if len(baseline_runs) == 3:
            break
    baseline = [project(conn, run, reviews) for run in baseline_runs]
    pending = []
    for operation in ("cc124-asia-risk-20261117", "cc124-btc-range-20261117-r2"):
        path = STORE.parent / "daily_app_outputs/owner-manual" / operation / "binding.json"
        if path.exists():
            binding = json.loads(path.read_bytes())
            pending.append({"operation_id": operation, "binding": info(path),
                            **project(conn, binding["run_id"], reviews)})

value = {"item": "CC-199", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "store": str(STORE), "store_access": "SQLITE_MODE_RO_QUERY_ONLY_CONSISTENT_SNAPSHOT",
    "sample_starts_at_utc": FINISHED_PIECE_YOUTUBE_EXCEPTION_AT,
    "sample_authority": "CC-199 Ops Product, 16 Nov 2026 01:25 GMT+7",
    "selection": "First three original approvals after reopening; original clocks retained; source deadline and every required image/readback must pass.",
    "native_review_count": len(reviews), "native_review_runs": len(runs),
    "current_suspended_routes": suspended_routes(),
    "reviewed_pieces_since_reopening": len(new_runs), "required_pieces": 3,
    "passing_pieces": sum(p["passes_current_acceptance"] for p in pieces),
    "pieces": pieces, "retained_baseline": baseline, "current_unapproved_operations": pending,
    "installed_consumers": [info(LIVE / "live_contentops" / name) for name in
        ("native_desktop_publication_v1.py", "native_publication_latency_v1.py",
         "reader_article_contract_v1.py", "publication_coordinator_v1.py")],
    "limits": "Durable observations only; no new platform readback, editorial call or public/store write."}
(HERE / "installed-three-piece-acceptance.json").write_text(
    json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: value[k] for k in ("observed_at_utc", "native_review_count",
    "native_review_runs", "reviewed_pieces_since_reopening", "passing_pieces",
    "required_pieces", "current_suspended_routes")}))
