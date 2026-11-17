"""Bounded CC-172 readback through the installed publication projection."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
STORE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")
sys.path.insert(0, str(LIVE))
from live_contentops.native_desktop_publication_v1 import publication_projection, DESTINATION

with sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("BEGIN")
    reviews = [dict(r) for r in conn.execute(
        "SELECT * FROM review_records WHERE reviewer_ref=? ORDER BY reviewed_at,review_id",
        ("NATIVE_DESKTOP_ARTICLE_REVIEW",))]
    runs = sorted({json.loads(r["notes"])["run_id"] for r in reviews})
    # The two current CC-124 operations have no KEEP yet. Include them explicitly
    # without treating a prepared article as approved or dispatched.
    operations = ["cc124-asia-risk-20261117", "cc124-btc-range-20261117-r2"]
    for operation in operations:
        p = STORE.parent / "daily_app_outputs" / "owner-manual" / operation / "binding.json"
        if p.exists():
            binding = json.loads(p.read_bytes())
            if binding["run_id"] not in runs:
                runs.append(binding["run_id"])
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    articles = []
    for run in runs:
        # Scope before reading payloads: native source/write artifacts are large
        # and irrelevant to the installed timing consumer.
        # Editorial rows belong to the opportunity work item; their payload
        # binds the article run. Coordinator public rows use run as work item.
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM outbox_messages WHERE work_item_id IN (?,?) AND destination IN (?,?,?) "
            "ORDER BY created_at,message_id", (run, "cc-opportunity-" + sha256_of(run),
            DESTINATION, "internal:native-publication-timing", "internal:native-neo-tool"))]
        ids = [r[0] for r in conn.execute(
            "SELECT message_id FROM outbox_messages WHERE work_item_id=? AND "
            "destination NOT LIKE 'internal:%'", (run,))]
        for message in ids:
            r = conn.execute("SELECT message_id,work_item_id,destination,status,created_at "
                "FROM outbox_messages WHERE message_id=?", (message,)).fetchone()
            rows.append({**dict(r), "payload": "{}"})
        # Native begin/submit envelopes belong to this run. Their destination
        # varies by envelope type, so fetch their exact identities from requests.
        extra = {"native-operation-binding-" + sha256_of(run)}
        for row in rows:
            if row["destination"] == "internal:native-neo-tool":
                value = json.loads(row["payload"])
                request = value.get("request", {})
                if request.get("request_sha256"):
                    for kind in ("started", "response"):
                        extra.add("native-neo-" + sha256_of([run, request["request_sha256"], kind]))
        known = {r["message_id"] for r in rows}
        for message in sorted(extra - known):
            row = conn.execute("SELECT * FROM outbox_messages WHERE message_id=?", (message,)).fetchone()
            if row:
                rows.append(dict(row))
        rows.sort(key=lambda r: (r["created_at"], r["message_id"]))
        dispatches = [dict(r) for r in conn.execute("SELECT p.* FROM platform_dispatches p "
            "JOIN outbox_messages o ON o.message_id=p.message_id WHERE o.work_item_id=? "
            "ORDER BY p.dispatched_at,p.dispatch_id", (run,))]
        reconciliations = [dict(r) for r in conn.execute(
            "SELECT * FROM reconciliations WHERE work_item_id=? ORDER BY reconciled_at", (run,))]
        readbacks = [dict(r) for r in conn.execute("SELECT r.* FROM readbacks r "
            "JOIN platform_dispatches p ON p.dispatch_id=r.dispatch_id "
            "JOIN outbox_messages o ON o.message_id=p.message_id WHERE o.work_item_id=? "
            "ORDER BY r.read_at,r.readback_id", (run,))]
        result = publication_projection(rows, dispatches, reconciliations,
            run_id=run, reviews=reviews, readbacks=readbacks)
        articles.append({"run_id": run, "state": result["state"],
            "timing": result["timing"], "destinations": result["destinations"],
            "dispatch_count": len(dispatches), "readback_count": len(readbacks)})

value = {"item": "CC-172", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "store_path": str(STORE), "store_access": "SQLITE_MODE_RO_QUERY_ONLY_CONSISTENT_SNAPSHOT",
    "consumer": "installed native_desktop_publication_v1.publication_projection",
    "native_review_count": len(reviews), "native_review_runs": len({json.loads(r['notes'])['run_id'] for r in reviews}),
    "latest_native_review_utc": max((r["reviewed_at"] for r in reviews), default=None),
    "articles": articles, "passing_samples": sum(a["timing"]["all_channels_dispatched_within_target"] for a in articles),
    "scope": "Native articles only; digest link indexes and plan/status posts have separate contracts. Durable observations, not new browser readbacks."}
(HERE / "live-timing-observation.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in value.items() if k != "articles"}))
