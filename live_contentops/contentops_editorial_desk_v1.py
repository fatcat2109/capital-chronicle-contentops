"""Revision-bound editorial decisions in the EXISTING review_records table.

This thin desk projection grants no provider, qualification or publication authority.
Legacy fixture review ledgers are not adopted as a second durable owner.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private

SCHEMA = "contentops.editorial_desk_review.v1"
ENDPOINT = "/api/daily-app/editorial-review"


def read_reviews(store):
    with store.get_read_only_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM review_records ORDER BY rowid")]


def desk_projection(library, records):
    histories = {}
    for row in records:
        try:
            note = json.loads(row["notes"])
        except (ValueError, TypeError):
            continue
        if note.get("schema_version") == SCHEMA:
            histories.setdefault(note["brief_id"], []).append({**row, **note})
    queue = []
    for p in library["packages"]:
        history = histories.get(p["brief_id"], [])
        latest = history[-1] if history else None
        current = bool(latest and latest["package_revision"] == p["package_revision"] and p["source_revision_current"])
        p["review"] = {"state": latest["decision"] if current else "STALE" if latest else "UNREVIEWED",
                       "latest_review_id": latest["review_id"] if latest else None,
                       "rationale": latest["rationale"] if latest else None,
                       "reviewer_ref": latest["reviewer_ref"] if latest else None,
                       "history": history, "publication_authority": False}
        p["validation"] = {**p["validation"], "semantic_editorial_review":
                           "COMPLETED_RESEARCH_" + latest["decision"] if current else "REQUIRED_FOR_CURRENT_REVISION"}
        brief = next((b for b in library["briefs"] if b["brief_id"] == p["brief_id"]), {})
        p["supporting_claims"] = [i for i in library["items"] if i["item_id"] in brief.get("source_item_ids", [])]
        p["counterevidence"] = brief.get("counterevidence", [])
        p["missing_current_inputs"] = brief.get("missing_inputs", [])
        p["editorial_kind"] = brief.get("editorial_kind", "BACKGROUND")
        if p["review"]["state"] in {"STALE", "REVISE", "UNREVIEWED"} or not p["source_revision_current"]:
            queue.append({"brief_id": p["brief_id"], "package_revision": p["package_revision"],
                          "reason": "DEPENDENT_INPUT_CHANGED" if not p["source_revision_current"] else p["review"]["state"],
                          "owner": "EXISTING_RESEARCH_RENDERER_THEN_SIMPLE_GEMINI_RUNTIME",
                          "provider_call_allowed_now": False})
    states = [p["review"]["state"] for p in library["packages"]]
    library["desk"] = {"review_endpoint": ENDPOINT, "decisions": {s: states.count(s) for s in ("KEEP", "REVISE", "HOLD", "STALE", "UNREVIEWED")},
                       "useful_research_packages": sum(p["review"]["state"] == "KEEP" and p["source_revision_current"] for p in library["packages"]),
                       "missing_current_input_coordinates": sorted({s for p in library["packages"] for s in p["missing_current_inputs"]}),
                       "kind_counts": {k: sum(p["editorial_kind"] == k for p in library["packages"]) for k in ("NEWS", "BACKGROUND", "ANALYSIS")},
                       "affected_work": queue, "fresh_simple_output": 0, "qualified": 0, "published": 0,
                       "provider_resume_operation": "Existing MainReportFeed.opportunity with the configured research_root at the next existing Simple window; only after a separate actual pause release. No research approval releases pause or publishes."}
    library["input_composition"]["editorial_decisions"] = library["desk"]["decisions"]
    return library


def record_review(store, *, brief_id, package_revision, decision, rationale, expected_review_id):
    """CAS against exact live package and prior decision, in one existing-store transaction."""
    from live_contentops.contentops_foundation_library_v1 import library_projection, PACKAGE
    if decision not in {"KEEP", "REVISE", "HOLD"} or not isinstance(rationale, str) or not 20 <= len(rationale.strip()) <= 3000:
        raise ValueError("REASONED_KEEP_REVISE_HOLD_REQUIRED")
    if _private({"rationale": rationale}):
        raise ValueError("PRIVATE_REVIEW_CONTEXT_EXCLUDED")
    with store.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY rowid")]
            reviews = [dict(r) for r in conn.execute("SELECT * FROM review_records ORDER BY rowid")]
            library = library_projection(rows, reviews)
            p = next((p for p in (library or {}).get("packages", []) if p["brief_id"] == brief_id), None)
            if not p or not p["source_revision_current"] or p["package_revision"] != package_revision:
                raise ValueError("PACKAGE_REVISION_CONFLICT_REFRESH_DESK")
            if p["review"]["latest_review_id"] != expected_review_id:
                raise ValueError("REVIEW_VERSION_CONFLICT_REFRESH_DESK")
            if decision == "KEEP" and p["validation"].get("blockers"):
                raise ValueError("VALIDATION_BLOCKED_CANNOT_KEEP")
            package_row = next(r for r in reversed(rows) if r["destination"] == PACKAGE and json.loads(r["payload"])["brief_id"] == brief_id)
            note = {"schema_version": SCHEMA, "brief_id": brief_id, "package_revision": package_revision,
                    "source_binding_sha256": p.get("source_binding_sha256"), "brief_sha256": p["brief_sha256"],
                    "article_identity": p["article_identity"], "rationale": rationale.strip(),
                    "supporting_claim_hashes": {i["item_id"]: i["text_sha256"] for i in p["supporting_claims"]},
                    "publication_authority": False}
            review_id = "editorial-review-" + uuid4().hex
            conn.execute("INSERT INTO review_records VALUES (?,?,?,?,?,?)", (review_id, package_row["work_item_id"],
                         "LOCAL_EDITORIAL_REVIEW", decision, json.dumps(note, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    if decision == "REVISE":
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
        from live_contentops.contentops_foundation_library_v1 import reconcile_affected_work
        reconcile_affected_work(LatestReportDeliveryTracker(store))
    return {"status": "EDITORIAL_REVIEW_RECORDED", "review_id": review_id, "decision": decision, "publication_authority": False}
