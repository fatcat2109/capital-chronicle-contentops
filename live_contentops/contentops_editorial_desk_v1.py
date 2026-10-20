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


def _source_delta(before, after):
    """Propositions/rights/corrections change work; a scan clock alone is not news."""
    old, new = {i["item_id"]: i for i in before}, {i["item_id"]: i for i in after}
    changes = []
    keys = ("text_sha256", "permission_sha256", "context_kind", "correction_of", "stage")
    for identity in sorted(old.keys() | new.keys()):
        a, b = old.get(identity), new.get(identity)
        kind = "ADDED" if not a else "REMOVED" if not b else "CORRECTED" if any(a.get(k) != b.get(k) for k in keys) else "UNCHANGED"
        changes.append({"item_id": identity, "state": kind, "before": a, "after": b,
                        "material": kind != "UNCHANGED"})
    return changes


def story_projection(library, rows):
    """Evolving-story read model over existing library/package/report outbox identities.

    Package history is explicitly unpublished. No independent story ledger, approval,
    source authority, scheduler or publication memory is created here.
    """
    from live_contentops.contentops_foundation_library_v1 import LIBRARY, PACKAGE, source_binding
    snapshots, packages, reports = [], {}, {}
    withdrawals = {json.loads(r["payload"]).get("source_report_sha256") for r in rows
                   if r["destination"] == "internal:cc-report-withdrawal"}
    for row in rows:
        dest = row["destination"]
        if dest not in {LIBRARY, PACKAGE, "internal:cc-report-receipt"}:
            continue
        value = json.loads(row["payload"])
        if dest == LIBRARY:
            snapshots.append(value)
        elif dest == PACKAGE:
            packages.setdefault(value["brief_id"], []).append(value)
        else:
            reports.setdefault(value["report_id"], []).append(value)
    snapshots.sort(key=lambda s: s.get("library_sequence", 0))
    stories = []
    current_packages = {p["brief_id"]: p for p in library["packages"]}
    for brief in library["briefs"]:
        identity = brief["brief_id"]
        package = current_packages.get(identity, {})
        history = sorted(packages.get(identity, []), key=lambda p: p.get("package_sequence", 0))
        distinct = []
        for p in history:
            if not distinct or p["article_identity"] != distinct[-1]["article_identity"]:
                distinct.append(p)
        current = bool(package.get("source_revision_current"))
        prior = distinct[-2] if current and len(distinct) > 1 else distinct[-1] if distinct and not current else None
        baseline = next((s for s in reversed(snapshots) if any(
            b["brief_id"] == identity and b["brief_sha256"] == (prior or {}).get("brief_sha256")
            and (not (prior or {}).get("source_binding_sha256") or source_binding([
                i for i in s["items"] if i["item_id"] in b["source_item_ids"]]) == prior["source_binding_sha256"])
            for b in s["briefs"])), {})
        old_brief = next((b for b in baseline.get("briefs", []) if b["brief_id"] == identity), {})
        before = [i for i in baseline.get("items", []) if i["item_id"] in old_brief.get("source_item_ids", [])]
        after = [i for i in library["items"] if i["item_id"] in brief["source_item_ids"]]
        delta = _source_delta(before, after) if prior else []
        state = package.get("review", {}).get("state", "UNREVIEWED")
        changed = [d for d in delta if d["material"]]
        updated_brief = bool(prior and prior.get("brief_sha256") != brief["brief_sha256"])
        disposition = "HOLD" if state == "HOLD" or brief.get("hold_reason") else (
            "FOLLOW_UP" if prior and (changed or updated_brief) else "NEW" if len(distinct) <= 1 else "NO_MATERIAL_CHANGE")
        reason = (brief.get("hold_reason") or package.get("review", {}).get("rationale")) if disposition == "HOLD" else (
            brief.get("update_reason") or "Luận điểm hoặc cách giải thích của bản trước đã thay đổi; xem so sánh và nguồn." if disposition == "FOLLOW_UP" else
            "Bản nghiên cứu đầu tiên của câu chuyện; chưa có bài trước trong chuỗi này." if disposition == "NEW" else
            "Không có thay đổi nội dung kể từ gói hiện tại; giữ bài và media, không gọi lại model.")
        main_history = []
        for binding in brief.get("main_report_bindings", []):
            chain = sorted(reports.get(binding["report_id"], []), key=lambda r: r["report_version"])
            for index, r in enumerate(chain):
                previous = chain[index - 1] if index else {}
                old_claims = {c["claim_id"]: c for c in previous.get("claims", [])}
                new_claims = {c["claim_id"]: c for c in r.get("claims", [])}
                main_history.append({**{k: r.get(k) for k in ("report_id", "report_version", "source_report_sha256", "parent_report_sha256", "status", "change_kind", "known_at_cutoff_utc", "withdrawal_only")},
                    "withdrawn": r.get("source_report_sha256") in withdrawals or bool(r.get("withdrawal_only")),
                    "originality": "MAIN_ORIGIN_RECIRCULATION", "independent_confirmation": False,
                    "changed_claims": [{"claim_id": key, "before": old_claims.get(key), "after": new_claims.get(key)}
                        for key in sorted(old_claims.keys() | new_claims.keys()) if old_claims.get(key) != new_claims.get(key)]})
        stories.append({"story_identity": (package.get("article") or {}).get("cluster_id") or identity,
            "update_chain_identity": (package.get("article") or {}).get("cluster_id") or identity,
            "brief_id": identity, "title": brief["title"], "families": brief.get("families", []),
            "entities_topics": brief.get("entities_topics") or sorted({a for i in after for a in i.get("assets", [])}
                | ({"EIA", "Natural Gas"} if "ENERGY" in brief.get("families", []) else set())),
            "source_item_ids": brief["source_item_ids"], "main_report_ids": [b["report_id"] for b in brief.get("main_report_bindings", [])],
            "disposition": disposition, "reason": reason, "reader_question": brief["next_question"],
            "follow_up_value": brief.get("update_reason") or brief["audience_value"],
            "evidence_delta": delta, "changed_source_count": len(changed), "brief_changed": updated_brief,
            "prior_package": {"article_identity": prior["article_identity"], "title": prior["article"]["title"],
                "full_text": prior["article"]["substack_body_markdown"], "stage": "UNPUBLISHED_RESEARCH_PACKAGE"} if prior else None,
            "package_history": [{"article_identity": p["article_identity"], "title": p["article"]["title"],
                "package_sequence": p.get("package_sequence"), "full_text": p["article"]["substack_body_markdown"],
                "stage": "UNPUBLISHED_RESEARCH_PACKAGE"} for p in distinct],
            "main_history": main_history, "current_review": package.get("review"),
            "work_required": not current or state in {"STALE", "REVISE", "UNREVIEWED"},
            "missing_inputs": brief.get("missing_inputs", []), "counterevidence": brief.get("counterevidence", []),
            "confirmation_state": "ATTRIBUTED_RETAINED_SOURCE_FACTS_CONDITIONAL_ANALYSIS",
            "epistemic_states": [{"item_id": i["item_id"], "state": "SUPERSEDED" if i.get("stage") == "RESEARCH_SUPERSEDED"
                else (brief.get("source_epistemic_states") or {}).get(i["item_id"], "CONFIRMED_AS_ATTRIBUTED_SOURCE_TEXT"),
                "scope": "SOURCE_REPORT_NOT_MARKET_IMPACT", "context_kind": i["context_kind"]} for i in after],
            "publication_state": "UNPUBLISHED_RESEARCH", "published_prior": None,
            "independent_confirmation_from_main": False})
    return stories


def publication_story_context(stories, published_memory, *, cutoff_utc):
    """Reuse canonical portfolio novelty and prior article context; no draft as published."""
    from live_contentops.editorial_portfolio_v1 import PublishedArticleRef, classify_story_novelty, build_material_follow_up_context
    from live_contentops.published_corpus_read_model_v1 import is_countable_canonical_published_article
    corpus = []
    fields = PublishedArticleRef.__dataclass_fields__
    for row in published_memory:
        if is_countable_canonical_published_article(row):
            corpus.append(row if isinstance(row, PublishedArticleRef) else PublishedArticleRef(**{k: v for k, v in row.items() if k in fields}))
    result = []
    for story in stories:
        changed = [d["after"] for d in story["evidence_delta"] if d["material"] and d["after"]]
        cluster = {"cluster_id": story["story_identity"], "update_chain_identity": story["update_chain_identity"],
            "entities_topics": story["entities_topics"],
            "headline_ids": story["source_item_ids"], "leaf_summaries": [i["proposition"] for i in changed],
            "official_source_urls": [i["source_url"] for i in changed]}
        novelty = classify_story_novelty(cluster, published_corpus=corpus, now=datetime.fromisoformat(cutoff_utc.replace("Z", "+00:00")))
        follow_up = build_material_follow_up_context(cluster, novelty, corpus)
        result.append({**story, "published_novelty": novelty, "material_follow_up_context": follow_up,
            "published_prior": follow_up, "canonical_memory_article_count": len(corpus),
            "canonical_memory_scope": "EXACT_RECONCILED_PUBLICATION_MEMORY_RELATEDNESS_IS_NOT_NEW_FACTUAL_AUTHORITY"})
    return result


def selection_story_context(story):
    """Compact selector view; the writer retains the full exact bound history."""
    result = {k: story.get(k) for k in ("story_identity", "update_chain_identity", "brief_id", "disposition", "reason",
        "reader_question", "follow_up_value", "changed_source_count", "work_required", "missing_inputs", "confirmation_state", "publication_state")}
    result["current_review"] = {k: (story.get("current_review") or {}).get(k) for k in ("state", "rationale")}
    result["changed_evidence"] = [{"item_id": d["item_id"], "state": d["state"],
        "before": (d.get("before") or {}).get("proposition"), "after": (d.get("after") or {}).get("proposition"),
        "source_url": (d.get("after") or d.get("before") or {}).get("source_url"),
        "rights_state": (d.get("after") or d.get("before") or {}).get("rights_state")}
        for d in story["evidence_delta"] if d["material"]]
    result["previous_unpublished_package"] = {k: story["prior_package"][k] for k in ("article_identity", "title", "stage")} if story.get("prior_package") else None
    result["published_novelty"] = story.get("published_novelty")
    result["previous_published_article"] = {k: story["published_prior"].get(k) for k in (
        "previous_story_identity", "previous_article_identity", "previous_title", "previous_canonical_url", "previous_body_sha256")
    } if story.get("published_prior") else None
    result["main_changed_claim_ids"] = sorted({c["claim_id"] for h in story["main_history"] for c in h["changed_claims"]})
    return result


def read_reviews(store):
    with store.get_read_only_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM review_records ORDER BY rowid")]


def record_native_article_review(store, *, run_id, article_identity, decision, rationale, expected_review_id=None):
    """Revision-bound native result review in the existing review table; no publication grant."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    if decision not in {"KEEP", "REVISE", "HOLD"} or not 20 <= len(rationale.strip()) <= 3000 or _private({"rationale": rationale}):
        raise ValueError("REASONED_KEEP_REVISE_HOLD_REQUIRED")
    key = "cc-editorial-final-" + sha256_of(run_id)
    with store.get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT * FROM outbox_messages WHERE message_id=?", (key,)).fetchone()
            value = json.loads(row["payload"]) if row else {}
            if (value.get("model_execution_state") != "NATIVE_DESKTOP_REQUEST_RETURN"
                    or value.get("article_identity") != article_identity or not value.get("qualified_article_count")):
                raise ValueError("NATIVE_ARTICLE_REVISION_CONFLICT")
            prior = conn.execute("SELECT * FROM review_records WHERE work_item_id=? AND reviewer_ref=? ORDER BY rowid DESC LIMIT 1",
                (row["work_item_id"], "NATIVE_DESKTOP_ARTICLE_REVIEW")).fetchone()
            if (prior["review_id"] if prior else None) != expected_review_id:
                raise ValueError("REVIEW_VERSION_CONFLICT_REFRESH_DESK")
            revision = sha256_of([article_identity, value["simple_result"]["publication_lifecycle_plan"]["plan_hash"],
                                  value.get("claim_lineage"), value.get("media_assets")])
            note = {"schema_version": "contentops.native_article_review.v1", "run_id": run_id,
                "article_identity": article_identity, "package_revision": revision,
                "rationale": rationale.strip(), "publication_authority": False}
            review_id = "native-article-review-" + uuid4().hex
            conn.execute("INSERT INTO review_records VALUES (?,?,?,?,?,?)", (review_id, row["work_item_id"],
                "NATIVE_DESKTOP_ARTICLE_REVIEW", decision, json.dumps(note, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"review_id": review_id, "decision": decision, **note}


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
                          "owner": "EXISTING_RESEARCH_RENDERER_THEN_NATIVE_CODEX_DESKTOP",
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
