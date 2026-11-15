"""One read-only CC-199 reading through the installed publication consumers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
sys.path.insert(0, str(LIVE))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.contentops_editorial_desk_v1 import read_reviews
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_publication_latency_v1 import publication_timing
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


class ReadOnlyStore(ContentOpsDurableStore):
    def get_connection(self):
        return self.get_read_only_connection()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def info(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}


store = ReadOnlyStore(RUNTIME / "contentops_daily_app_v1.sqlite3", auto_migrate=False)
with store.get_connection() as conn:
    assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
    canonicals = [dict(row) for row in conn.execute(
        "SELECT o.work_item_id,d.dispatch_id,d.dispatched_at,d.public_object_id,d.public_object_url "
        "FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id "
        "WHERE d.platform='substack' AND d.status='DISPATCH_CONFIRMED' "
        "AND d.public_object_id IS NOT NULL ORDER BY d.dispatched_at DESC")]

selected, excluded, seen = [], [], set()
for canonical in canonicals:
    run = canonical["work_item_id"]
    if run in seen:
        continue
    seen.add(run)
    if run.startswith("cc143-digest-") or run.startswith("plan-analysis-"):
        excluded.append({"run_id": run, "reason": "DIGEST_OR_PLAN_SEPARATE_CONTRACT"})
    else:
        selected.append(canonical)
    if len(selected) == 3:
        break

reviews = read_reviews(store)
dispatches = store.list_platform_dispatches()
pieces = []
for canonical in selected:
    run = canonical["work_item_id"]
    own_reviews = [r for r in reviews if json.loads(r["notes"]).get("run_id") == run
                   and r["reviewer_ref"] == "NATIVE_DESKTOP_ARTICLE_REVIEW"]
    rows = store.list_outbox_messages(work_item_id=run)
    rows += store.list_outbox_messages(work_item_id="cc-opportunity-" + sha256_of(run))
    rows.sort(key=lambda row: (row["created_at"], row["message_id"]))
    message_ids = {row["message_id"] for row in rows}
    own_dispatches = [d for d in dispatches if d["message_id"] in message_ids]
    readbacks = [r for d in own_dispatches for r in store.list_readbacks_for_dispatch(d["dispatch_id"])]
    binding_row = store.get_outbox_message("native-operation-binding-" + sha256_of(run))
    if binding_row:
        # This path includes the stored opportunity's reviews. The previous
        # export filtered by the article's run id alone and lost these clocks.
        projection = NativeReviewedPublication(store, json.loads(binding_row["payload"]),
                                              native_invocation_id=None).projection()
        entries, timing, state = projection["destinations"], projection["timing"], projection["state"]
    else:
        reconciliations = {r["reconciliation_id"]: r["status"]
                           for r in store.get_reconciliations_for_work_item(run)}
        entries = []
        for row in rows:
            if row["destination"].startswith("internal:") or not row["message_id"].startswith("outbox_"):
                continue
            dispatch_id = "dispatch_" + row["message_id"].removeprefix("outbox_")
            original = next((d for d in own_dispatches if d["dispatch_id"] == dispatch_id), {})
            dispatch = DurablePublicationCoordinator.effective_dispatch(original, own_dispatches)
            entries.append({"destination": row["destination"], "dispatch_id": dispatch.get("dispatch_id", dispatch_id),
                            "status": dispatch.get("status", row["status"]),
                            "public_object_id": dispatch.get("public_object_id"),
                            "public_object_url": dispatch.get("public_object_url"),
                            "reconciliation_status": reconciliations.get(
                                "reconciliation_" + dispatch.get("dispatch_id", dispatch_id).removeprefix("dispatch_"))})
        timing = publication_timing(rows, reviews, run_id=run, destinations=entries, readbacks=readbacks)
        state = "STRUCTURED_PIECE_NO_NATIVE_TEXT_REVIEW_RECORD" if not own_reviews else "STRUCTURED_PIECE"
    # Known clocks must survive the evidence export. No store rows are repaired
    # or rewritten to obtain a more favorable reading.
    if own_reviews:
        assert timing["text_approved_at_utc"] is not None, run
    channels = {c["destination"]: c for c in timing["channels"]}
    pieces.append({"run_id": run, "canonical_url": canonical["public_object_url"],
        "public_object_id": canonical["public_object_id"], "state": state,
        "record_counts": {"outbox": len(rows), "dispatches": len(own_dispatches),
                          "reviews": len(own_reviews), "readbacks": len(readbacks)},
        "review_bindings": [{"review_id": r["review_id"], "decision": r["decision"],
                             "reviewed_at_utc": r["reviewed_at"],
                             "text_approved_at_utc": json.loads(r["notes"]).get("text_approved_at_utc"),
                             "text_revision_sha256": json.loads(r["notes"]).get("text_revision_sha256")}
                            for r in own_reviews],
        "timing": timing,
        "destinations": [{**{k: e.get(k) for k in ("destination", "dispatch_id", "status", "reconciliation_status",
                                                  "public_object_id", "public_object_url")},
                          **channels.get(e["destination"], {})} for e in entries]})

passed = sum(p["timing"]["finished_piece_acceptance"]["all_destinations_with_image_readbacks_within_target"]
             for p in pieces)
save("installed-three-piece-acceptance.json", {
    "item": "CC-199", "read_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_store": str(store.db_path), "source_store_opened_read_only": True,
    "consumer_modules": [info(LIVE / "live_contentops" / name) for name in
                         ("native_desktop_publication_v1.py", "native_publication_latency_v1.py",
                          "contentops_editorial_desk_v1.py")],
    "selection": "Latest three confirmed original articles; retained readings do not replace three new prospective pieces.",
    "excluded_recent_objects": excluded, "passing_pieces": passed, "pieces": pieces,
    "new_original_canonicals_since_12_nov_ops_check": [c["work_item_id"] for c in selected
        if c["dispatched_at"] >= "2026-11-12T14:15:00+00:00"],
    "prior_export_correction": "The 14 November export omitted opportunity-bound review records. The installed native projection retains them; the outcome remains failing.",
    "public_write_performed": False, "live_store_mutated": False,
    "limits": ["Stored proof is read here; this run makes no new platform observation.",
               "CC-536 has no observed native text approval clock; creation and publish clocks do not replace one."]})
print(json.dumps({"pieces": len(pieces), "passing_pieces": passed,
                  "approval_clocks": {p["run_id"]: p["timing"]["text_approved_at_utc"] for p in pieces}}))
