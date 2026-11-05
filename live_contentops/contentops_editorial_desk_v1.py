"""Revision-bound editorial decisions in the EXISTING review_records table.

This thin desk projection grants no provider, qualification or publication authority.
Legacy fixture review ledgers are not adopted as a second durable owner.
"""
from __future__ import annotations

from live_contentops.native_manual_candidate_v1 import native_artifact_key

import json
from datetime import datetime, timezone
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private

SCHEMA = "contentops.editorial_desk_review.v1"
ENDPOINT = "/api/daily-app/editorial-review"
SOURCE_REVIEW = "internal:native-story-source-review"
STORY_PREPARATION = "internal:native-story-preparation"


def record_pre_event_preparation(store, packet):
    """Retain dated background; preview operations can admit its verified sources."""
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    if (_private(packet) or not all(packet.get(k) for k in ("event_id", "title", "known_at_utc",
            "official_sources", "reader_question", "background", "release_work", "missing_inputs"))
            or packet.get("released_facts_admitted") is not False or packet.get("publication_authority") is not False):
        raise ValueError("EXACT_DATED_PRE_EVENT_PREPARATION_REQUIRED")
    for source in packet["official_sources"]:
        from pathlib import Path
        from hashlib import sha256
        if (not source.get("url", "").startswith("https://") or not source.get("capture_path")
                or sha256(Path(source["capture_path"]).read_bytes()).hexdigest() != source.get("capture_sha256")):
            raise ValueError("PREPARATION_OFFICIAL_CAPTURE_BINDING_REQUIRED")
    value = {"schema_version": "contentops.native_story_preparation.v1", **packet,
        "source_admission_state": "HASH_BOUND_BACKGROUND_AVAILABLE_FOR_PREVIEW", "public_write_performed": False}
    key = "native-story-preparation-" + sha256_of(value)
    _persist(store, key, value, STORY_PREPARATION)
    return {"message_id": key, "event_id": packet["event_id"], "source_admission_state": value["source_admission_state"]}


def retain_reviewed_preview_background(store, *, event_id, run_id):
    """Feed an accepted background back to the existing event-preparation owner."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    binding_row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(binding_row["payload"]) if binding_row else {}
    row = store.get_outbox_message(native_artifact_key(store, run_id, "cc-editorial-final-"))
    result = json.loads(row["payload"]) if row else {}
    if binding.get("preview_event_id") != event_id or not result.get("qualified_article_count"):
        raise ValueError("EXACT_PREVIEW_EVENT_BACKGROUND_REQUIRED")
    with store.get_read_only_connection() as conn:
        review = conn.execute("SELECT * FROM review_records WHERE work_item_id=? AND reviewer_ref=? "
            "ORDER BY rowid DESC LIMIT 1", (row["work_item_id"], "NATIVE_DESKTOP_ARTICLE_REVIEW")).fetchone()
        preparations = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
            (STORY_PREPARATION,)).fetchall()
    note = json.loads(review["notes"]) if review else {}
    revision = native_review_revision(result)
    if (not review or review["decision"] != "KEEP" or note.get("package_revision") != revision
            or not note.get("final_visual_review")):
        raise ValueError("REVIEWED_PREVIEW_BACKGROUND_REVISION_REQUIRED")
    prior = [(r["message_id"], json.loads(r["payload"])) for r in preparations
        if json.loads(r["payload"]).get("event_id") == event_id]
    message_id, packet = prior[-1] if prior else (None, {})
    if not packet:
        raise ValueError("PREPARATION_EVENT_NOT_FOUND:" + event_id)
    old = packet.get("reviewed_background") or {}
    if old.get("article_revision") == revision and old.get("review_id") == review["review_id"]:
        return {"message_id": message_id, "event_id": event_id, "run_id": run_id,
            "article_revision": revision, "classification": "REVIEWED_BACKGROUND_ALREADY_RETAINED"}
    from copy import deepcopy
    background = {"run_id": run_id, "article_identity": result["article_identity"],
        "article_revision": revision, "review_id": review["review_id"], "reviewed_at_utc": review["reviewed_at"],
        "article": deepcopy(result["article"]), "original_source_pack": deepcopy(result["evidence"]),
        "media_assets": [{k: deepcopy(a[k]) for k in ("asset_id", "path", "sha256", "modality", "caption",
            "alt_text", "placement_after", "source_links") if k in a} for a in result.get("media_assets", [])],
        "final_visual_review": deepcopy(note["final_visual_review"]),
        "final_result_message_id": row["message_id"], "final_result_sha256": sha256_of(result),
        "scope": "REVIEWED_PRE_EVENT_BACKGROUND", "dossier_scenarios_added": False}
    # Exact media/renders remain binary in their owned folders; references and
    # hashes are enough for the next native planner/writer to reuse those files.
    background["final_visual_review"] = {k: v for k, v in background["final_visual_review"].items()
        if k not in {"assets", "renders"}}
    packet = {**packet, "known_at_utc": review["reviewed_at"],
        "original_preparation_message_id": message_id,
        "background_source_known_at_utc": packet.get("background_source_known_at_utc", packet["known_at_utc"]),
        "reviewed_background": background}
    receipt = record_pre_event_preparation(store, packet)
    return {**receipt, "run_id": run_id, "article_revision": revision,
        "classification": "REVIEWED_BACKGROUND_FEEDS_PREVIEW_PREPARATION"}


def preview_preparation_research(store, *, event_id, cutoff_utc, article_type="EVENT_PREVIEW"):
    """Use our existing preparation in the preview's ordinary source/writer path.

    The preparation's prose is editorial context. Only exact, captured BLS spans
    establish past facts. Neither the future print nor dossier probabilities are
    invented. The original outbox record, rights and source clocks stay unchanged.
    """
    from hashlib import sha256
    from pathlib import Path
    from urllib.parse import urlsplit
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _time
    from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

    if article_type != "EVENT_PREVIEW":
        raise ValueError("PREPARATION_REUSE_IS_FOR_EVENT_PREVIEWS")
    eligible = []
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
                            (STORY_PREPARATION,)).fetchall()
    for row in rows:
        packet = json.loads(row["payload"])
        if packet.get("event_id") != event_id or _time(packet["known_at_utc"]) > _time(cutoff_utc):
            continue
        if row["message_id"] != "native-story-preparation-" + sha256_of(packet):
            raise ValueError("PREPARATION_IMMUTABLE_PACKET_CHANGED")
        eligible.append((row["message_id"], packet))
    if not eligible:
        raise ValueError("PREPARATION_EVENT_NOT_FOUND:" + event_id)
    message_id, packet = max(eligible, key=lambda x: _time(x[1]["known_at_utc"]))
    if not packet.get("planned_release_utc") or _time(cutoff_utc) >= _time(packet["planned_release_utc"]):
        raise ValueError("PREVIEW_EVENT_HAS_PASSED_USE_EVENT_REVIEW")
    sources = {}
    for source in packet["official_sources"]:
        raw = Path(source["capture_path"]).read_bytes()
        if sha256(raw).hexdigest() != source["capture_sha256"]:
            raise ValueError("PREPARATION_OFFICIAL_CAPTURE_BINDING_REQUIRED")
        sources[source["capture_sha256"]] = (source, raw.decode("utf-8-sig"))
    records = {}
    grouped = {}
    for span in packet.get("prior_fact_spans", []):
        digest = span["capture_sha256"]
        source, text = sources[digest]
        url = urlsplit(source["url"])
        if (url.scheme != "https" or url.netloc != "www.bls.gov"
                or not url.path.startswith("/news.release/")):
            raise ValueError("PREPARATION_PUBLIC_BLS_TEXT_RIGHTS_REQUIRED")
        excerpt = span["exact_source_span"]
        if not excerpt or " ".join(excerpt.split()) not in " ".join(text.split()):
            raise ValueError("PREPARATION_PRIOR_FACT_SPAN_CHANGED")
        published = source.get("published_at_utc")
        known = source.get("observed_at_utc") or source.get("retained_at_utc") or packet["known_at_utc"]
        if not published or _time(published) > _time(known) or _time(known) > _time(cutoff_utc):
            raise ValueError("PREPARATION_PRIOR_SOURCE_CLOCK_INVALID")
        grouped.setdefault(digest, []).append(excerpt)
    if not grouped:
        raise ValueError("PREPARATION_NO_CAPTURED_PRIOR_FACTS:" + event_id)
    for digest, excerpts in grouped.items():
        source, _ = sources[digest]
        identity = "preview-background-" + sha256_of([message_id, digest])
        text = "\n\n".join(excerpts)
        content_hash = sha256(text.encode()).hexdigest()
        rights = {"scope": "BLS_AGENCY_AUTHORED_PUBLIC_DOMAIN_TEXT_PREVIEW_BACKGROUND",
            "authority_ref": "JIM_DECISION_41_AND_BACKLOG_CC216",
            "article_types": ["EVENT_PREVIEW"], "attribution_required": True,
            "source_capture_sha256": digest, "content_sha256": content_hash,
            "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
            "INTERNAL_ANALYSIS_ALLOWED": True,
            "excludes": ["third_party_photographs", "unreleased_facts", "invented_consensus"]}
        known = source.get("observed_at_utc") or source.get("retained_at_utc") or packet["known_at_utc"]
        doc = {"document_id": identity, "source_url": source["url"],
            "publisher": "U.S. Bureau of Labor Statistics",
            "published_at_utc": source["published_at_utc"],
            "source_adapter_family": "official_macro",
            "source_authority_class": "official_public_primary_source",
            "canonical_content_text": text, "canonical_content_sha256": content_hash,
            "raw_sha256": digest, "content_truncated": False, "public_claim_allowed": True,
            "preview_preparation": {"message_id": message_id, "event_id": event_id,
                "planned_release_utc": packet["planned_release_utc"],
                "known_at_utc": packet["known_at_utc"], "background": packet["background"],
                "reader_question": packet["reader_question"], "watchpoints": packet.get("watchpoints", []),
                "missing_inputs": packet["missing_inputs"],
                **({"reviewed_background": packet["reviewed_background"]}
                   if packet.get("reviewed_background") and not records else {}),
                "future_release_values": None, "dossier_scenarios": None,
                "background_is_editorial_context_not_new_official_facts": True},
            "source_reuse_constraints": rights}
        records[identity] = {"headline_id": identity,
            "headline_text": excerpts[0],
            "text_sha256": content_hash, "source_identity": doc["publisher"],
            "source_platform": "CONTENTOPS_PRE_EVENT_PREPARATION",
            "source_account": doc["publisher"], "source_url": source["url"],
            "official_source_urls": [source["url"]], "source_timestamp_utc": source["published_at_utc"],
            "headline_timestamp": source["published_at_utc"], "known_at_utc": known,
            "retrieval_time_utc": known, "revision_at_utc": packet["known_at_utc"],
            "rights_state": "BLS_US_FEDERAL_PUBLIC_DOMAIN_TEXT",
            "source_capture_sha256": digest, "rights_evidence_sha256": sha256_of(rights),
            "source_permissions": rights, "source_permission_record_sha256": sha256_of(rights),
            "candidate_catalyst_tags": ["EVENT_PREVIEW", event_id],
            "originality": "EXISTING_NEWSROOM_PREPARATION_WITH_EXACT_PRIOR_OFFICIAL_SOURCES",
            "correction_of": None, "document": doc, "source_chart": None,
            "permitted_source_text": text, "supporting_headline_ids": [],
            "research_metadata": {"event_id": event_id, "article_type": "EVENT_PREVIEW",
                "preparation_message_id": message_id}}
    if consensus := packet.get("single_consensus_fact"):
        projection_raw = Path(consensus["projection_path"]).read_bytes()
        if sha256(projection_raw).hexdigest() != consensus["projection_sha256"]:
            raise ValueError("PREVIEW_CONSENSUS_PROJECTION_CHANGED")
        projection = json.loads(projection_raw)
        if projection["release_id"] != consensus["release_id"]:
            raise ValueError("PREVIEW_CONSENSUS_EVENT_CHANGED")
        rows = [r for r in projection["records"] if r["source"] == consensus["source"]
            and r["measure_key"] == consensus["measure_key"]]
        if len(rows) != 1:
            raise ValueError("PREVIEW_EXACTLY_ONE_ATTRIBUTED_CONSENSUS_REQUIRED")
        row = rows[0]
        capture_root = Path(consensus["capture_root"]).resolve()
        capture = (capture_root / row["raw_path"]).resolve()
        if not capture.is_relative_to(capture_root) or sha256(capture.read_bytes()).hexdigest() != row["raw_sha256"]:
            raise ValueError("PREVIEW_CONSENSUS_SOURCE_CAPTURE_CHANGED")
        if (not row.get("pre_release_eligible") or not row.get("source_value_text")
                or _time(row["known_at_utc"]) > _time(cutoff_utc)
                or _time(row["released_at_utc"]) != _time(packet["planned_release_utc"])):
            raise ValueError("PREVIEW_CONSENSUS_PERIOD_OR_CLOCK_INVALID")
        text = (f"{row['source']} {row['source_statistic_label']} for {row['measure_key']} "
            f"({row['reference_period']}, release {row['release_date']}): {row['source_value_text']}; "
            f"unit {row['unit']}; observed {row['known_at_utc']}. "
            "One source's published expectation, not the release result or a Capital Chronicle forecast.")
        identity = "preview-consensus-" + sha256_of([message_id, consensus])
        constraints = {"scope": "SINGLE_ATTRIBUTED_CONSENSUS_FACT_NO_TABLE_SERIES_OR_CHART",
            "authority_ref": "JIM_DECISION_44_AND_HOST_RULE_7_CITATIONS",
            "original_capture_rights_class": row.get("rights_class"),
            "raw_capture_public_redistribution": False, "attribution_required": True,
            "source_capture_sha256": row["raw_sha256"], "article_types": ["EVENT_PREVIEW"]}
        template = dict(next(iter(records.values())))
        template.update(headline_id=identity, headline_text=text, text_sha256=sha256(text.encode()).hexdigest(),
            context_only=True,
            source_identity=row["source"], source_account=row["source"], source_url=row["source_url"],
            source_timestamp_utc=None, headline_timestamp=row["known_at_utc"],
            known_at_utc=row["known_at_utc"], retrieval_time_utc=row["acquired_at_utc"],
            revision_at_utc=row["known_at_utc"], official_source_urls=[],
            source_capture_sha256=row["raw_sha256"], source_permissions=constraints,
            source_permission_record_sha256=sha256_of(constraints), rights_evidence_sha256=sha256_of(constraints),
            rights_state="SINGLE_ATTRIBUTED_FACT_JIM_DECISION_44", permitted_source_text=text,
            document={"document_id": identity, "source_url": row["source_url"], "publisher": row["source"],
                "published_at_utc": None, "canonical_content_text": text,
                "canonical_content_sha256": sha256(text.encode()).hexdigest(), "raw_sha256": row["raw_sha256"],
                "source_authority_class": "reputable_secondary_source", "report_truth_only": True,
                "source_reuse_constraints": constraints})
        for record in records.values():
            record["supporting_headline_ids"] = [identity]
        # Context belongs to this preview's source pack, never its own candidate.
        template["research_metadata"] = {"event_id": event_id, "context_only": True}
        records[identity] = template
    snapshot = {"root": str(Path(__file__).resolve().parents[1]),
        "revision": sha256_of([message_id, records]), "records": records, "gaps": []}
    return RetainedSourceResearch.from_frozen_snapshot({**snapshot, "snapshot_sha256": sha256_of(snapshot)})


def record_owner_edition(store, *, edition_id, title, operation_ids, held_candidates=(), opportunity_outcomes=()):
    """Group owner-requested articles in the existing outbox, without allocating work."""
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    if (not edition_id or not title or not 1 <= len(operation_ids) <= 8
            or len(set(operation_ids)) != len(operation_ids) or _private(held_candidates)):
        raise ValueError("BOUNDED_OWNER_EDITION_REQUIRED")
    value = {"schema_version": "contentops.native_owner_edition.v1", "edition_id": edition_id,
             "title": title, "operation_ids": list(operation_ids), "held_candidates": list(held_candidates),
             "publication_authority": False}
    if opportunity_outcomes:
        held_ids = {h.get("operation_id") for h in held_candidates}
        if (len(opportunity_outcomes) > 8 or _private(opportunity_outcomes)
                or len({o.get("operation_id") for o in opportunity_outcomes}) != len(opportunity_outcomes)
                or any(o.get("outcome") not in {"NEW", "UPDATE", "KEEP", "HOLD"}
                       or not o.get("reason") or type(o.get("source_blocked")) is not bool
                       or o.get("operation_id") not in (held_ids if o.get("outcome") == "HOLD" else set(operation_ids))
                       for o in opportunity_outcomes)):
            raise ValueError("EXACT_EDITION_OPPORTUNITY_OUTCOMES_REQUIRED")
        value["opportunity_outcomes"] = list(opportunity_outcomes)
    _persist(store, "native-owner-edition-" + sha256_of(value), value, "internal:native-owner-edition")
    return value


def source_review_projection(rows):
    return [json.loads(r["payload"]) for r in rows if r["destination"] == SOURCE_REVIEW]


def record_story_editorial_revision(store, *, run_id, article_identity, review_operation_id, reason):
    """A warranted owner editorial revision, explicitly without new factual evidence.

    Reuse the source/history owner; never manufacture a material source update to
    allocate a writer. The original accepted article and review remain unchanged.
    """
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes
    if not isinstance(reason, str) or len(reason.strip()) < 20:
        raise ValueError("SUBSTANTIVE_EDITORIAL_REVISION_REASON_REQUIRED")
    row = store.get_outbox_message(native_artifact_key(store, run_id, "cc-editorial-final-"))
    result = json.loads(row["payload"]) if row else {}
    if result.get("article_identity") != article_identity or not result.get("qualified_article_count"):
        raise ValueError("EXACT_EXISTING_STORY_REQUIRED")
    evidence = result.get("evidence") or []
    if not evidence or any(not d.get("canonical_content_sha256") for d in evidence):
        raise ValueError("RETAINED_SOURCE_IDENTITY_REQUIRED")
    prior = result["article"]
    review = {"schema_version": "contentops.native_story_source_review.v1",
        "review_id": "native-editorial-revision-" + sha256_of([run_id, review_operation_id]),
        "run_id": run_id, "article_identity": article_identity, "title": prior["title"],
        "cutoff_utc": result["simple_result"]["cutoff_utc"],
        "decision": "EDITORIAL_REVISION", "reader_change_summary": reason,
        "source_editions": [{"item_id": d["document_id"], "source_url": d["url"],
            "published_at_utc": d.get("published_at_utc"), "text_sha256": d["canonical_content_sha256"]} for d in evidence],
        "previous_sources": evidence, "source_attempts": [], "source_changes": [],
        "source_coverage_complete": True, "new_factual_evidence": False,
        "invalidates_prepared_review": False, "removed_main_claim_ids": [],
        "changed_research_descriptor_claim_ids": [], "main_receipt_id": None,
        "media_state": "REPLAN_LAWFUL_CONTEXTUAL_PHOTO_AND_SOURCE_BOUND_CHART",
        "prior_story": {"story_identity": prior.get("update_chain_identity") or prior["story_identity"],
            "article_identity": article_identity, "title": prior["title"],
            "full_text": prior["substack_body_markdown"], "stage": "UNPUBLISHED_REVIEWED_ARTICLE"},
        "writer_required": True, "publication_authority": False, "public_write_performed": False}
    review["request_sha256"] = sha256_of(review)
    store.register_outbox_message(message_id=review["review_id"], work_item_id=row["work_item_id"],
        destination=SOURCE_REVIEW, payload=canonical_bytes(review).decode(), status="EDITORIAL_INTERNAL")
    return review


def record_story_source_review(store, *, run_id, article_identity, review_operation_id,
                               research, source_ids, attempts, cutoff_utc, reason,
                               main_receipt_id=None):
    """Append a source-bound decision to the existing story/review outbox.

    Retrieval clocks cannot establish a new period. Missing access is a named gap,
    not evidence that the old source was corrected. Original packages stay immutable.
    """
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, canonical_bytes, _time
    key = "native-source-review-" + sha256_of([run_id, review_operation_id])
    request_sha = sha256_of([article_identity, research.revision, source_ids, attempts, cutoff_utc, reason, main_receipt_id])
    prior = store.get_outbox_message(key)
    if prior:
        value = json.loads(prior["payload"])
        if value.get("request_sha256", request_sha) != request_sha:
            raise ValueError("SOURCE_REVIEW_INPUT_CHANGED_USE_NEW_IDENTITY")
        return value
    row = store.get_outbox_message(native_artifact_key(store, run_id, "cc-editorial-final-"))
    result = json.loads(row["payload"]) if row else {}
    if result.get("article_identity") != article_identity or not result.get("qualified_article_count"):
        raise ValueError("EXACT_EXISTING_STORY_REQUIRED")
    if not reason or not 0 < len(attempts) <= 6 or _private(attempts):
        raise ValueError("BOUNDED_PUBLIC_SOURCE_ATTEMPTS_REQUIRED")
    records = [research.records[h] for h in source_ids]
    if any(_time(r["known_at_utc"]) > _time(cutoff_utc) for r in records):
        raise ValueError("SOURCE_EDITION_AFTER_CUTOFF")
    evidence = result.get("evidence", [])
    before_text = " ".join(" ".join(str(d.get("canonical_content_text") or "").split()) for d in evidence)
    editions = [{"item_id": r["headline_id"], "source_url": r["source_url"],
        "proposition": r["headline_text"], "text_sha256": r["text_sha256"],
        "permission_sha256": r["source_permission_record_sha256"],
        "capture_sha256": r["source_capture_sha256"], "published_at_utc": r["source_timestamp_utc"],
        "retrieved_at_utc": r["retrieval_time_utc"], "observation_date": r["research_metadata"].get("observation_date"),
        "period_relation": r["research_metadata"].get("period_relation", "NO_NEW_PERIOD_PROVEN"),
        "rights_state": r["rights_state"], "originality": r["originality"],
        "context_kind": r["research_metadata"].get("context_kind"), "stage": "RESEARCH_READY"} for r in records]
    additions = [e for e in editions if " ".join(e["proposition"].split()) not in before_text]
    # A changed capture/URL/wording alone cannot allocate a writer. The verified
    # source edition must identify a new period, correction, or additional fact.
    material_additions = [e for e in additions if e["period_relation"] in {
        "SAME_PERIOD_ADDITIONAL_SEASONAL_COMPARATOR", "NEW_OBSERVATION_PERIOD",
        "PUBLISHER_CORRECTION_OF_SAME_OBSERVATION", "MATERIAL_NEW_SOURCE_PROPOSITION"}]
    main, removed, research_changes = None, [], []
    if main_receipt_id:
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
        from live_contentops.capital_chronicle_report_editorial_workspace_v1 import CURRENT
        main = next((r for r in LatestReportDeliveryTracker(store).receipts() if r["receipt_id"] == main_receipt_id), None)
        if not main or main["status"] not in CURRENT or _time(main["known_at_cutoff_utc"]) > _time(cutoff_utc):
            raise ValueError("ACCEPTED_PUBLIC_MAIN_RECEIPT_REQUIRED")
        if result.get("report_id") != main["report_id"]:
            raise ValueError("MAIN_RECEIPT_NOT_BOUND_TO_PRIOR_STORY")
        old_claims = {c["claim_id"] for d in evidence for c in d.get("report_lineage", {}).get("claims", [])}
        removed = sorted(old_claims - {c["claim_id"] for c in main.get("claims", [])})
        from live_contentops.capital_chronicle_public_research_semantics_v1 import descriptor_changes
        research_changes = descriptor_changes([c for d in evidence for c in d.get("report_lineage", {}).get("claims", [])], main)
    unavailable = [a for a in attempts if a["status"] != "PASS"]
    if (main and (main.get("withdrawal_only") or removed or research_changes)) or any(
            e["period_relation"] == "PUBLISHER_CORRECTION_OF_SAME_OBSERVATION" for e in material_additions):
        decision = "CORRECTION_OR_WITHDRAWAL"
    elif material_additions:
        decision = "MATERIAL_FOLLOW_UP"
    elif unavailable and not records:
        decision = "STALE_OR_SOURCE_GAP"
    else:
        decision = "USE_UNCHANGED"
    review = {"schema_version": "contentops.native_story_source_review.v1", "review_id": key,
        "request_sha256": request_sha,
        "run_id": run_id, "article_identity": article_identity, "title": result["article"]["title"],
        "cutoff_utc": cutoff_utc, "decision": decision, "reader_change_summary": reason,
        "source_editions": editions, "source_attempts": attempts,
        "source_coverage_complete": not unavailable,
        "source_changes": _source_delta([], material_additions), "removed_main_claim_ids": removed,
        "changed_research_descriptor_claim_ids": research_changes,
        "previous_sources": [{k: d.get(k) for k in ("source_id", "url", "published_at_utc", "canonical_content_sha256", "canonical_content_text")}
                             for d in evidence],
        "main_receipt_id": main_receipt_id, "research_revision": research.revision,
        "invalidates_prepared_review": decision in {"MATERIAL_FOLLOW_UP", "CORRECTION_OR_WITHDRAWAL", "STALE_OR_SOURCE_GAP"},
        "media_state": "REVALIDATE_CHANGED_SUPPORT" if additions or removed else "RETAIN_EXACT_BYTES_DATED_SUPPORT",
        "prior_story": {"story_identity": result["article"].get("update_chain_identity") or result["article"].get("story_identity"),
            "article_identity": article_identity, "title": result["article"]["title"],
            "full_text": result["article"]["substack_body_markdown"], "stage": "UNPUBLISHED_REVIEWED_ARTICLE"},
        "writer_required": decision in {"MATERIAL_FOLLOW_UP", "CORRECTION_OR_WITHDRAWAL"}, "publication_authority": False,
        "public_write_performed": False}
    store.register_outbox_message(message_id=key, work_item_id=row["work_item_id"], destination=SOURCE_REVIEW,
        payload=canonical_bytes(review).decode(), status="EDITORIAL_INTERNAL")
    return review


def native_story_projection(edition, rows, *, observed_at_utc=None):
    """Pure completed native-story/revision view over existing outbox and reviews.

    No model, filesystem, network, new state machine or factual freshness verdict.
    Source comparison decisions and exact parent identities remain the owners.
    """
    import re
    observed = observed_at_utc or datetime.now(timezone.utc).isoformat()
    finals, checks, groups = {}, {}, {}
    for row in rows:
        if row["destination"] == SOURCE_REVIEW:
            value = json.loads(row["payload"])
            value = {**value, "reviewed_at_utc": row.get("created_at")}
            checks.setdefault(value["article_identity"], []).append(value)
        elif row["destination"] == "internal:cc-report-simple-result":
            value = json.loads(row["payload"])
            if value.get("qualified_article_count") and value.get("model_execution_state") == "NATIVE_DESKTOP_REQUEST_RETURN":
                finals[value["article_identity"]] = (value, row.get("created_at"))

    def age(clock):
        if not clock:
            return None
        try:
            a = datetime.fromisoformat(str(clock).replace("Z", "+00:00"))
            b = datetime.fromisoformat(observed.replace("Z", "+00:00"))
            return int((b - a).total_seconds()) if a.tzinfo and b >= a else None
        except (TypeError, ValueError):
            return None

    for identity, item in edition.items():
        result, accepted = finals.get(identity, ({}, None))
        article = item.get("article") or {}
        if not all(isinstance(article.get(k), str) and article[k].strip()
                   for k in ("title", "substack_body_markdown")):
            # Legacy partial/media-only records remain in their owning view;
            # they are not a completed story and must not crash this join.
            continue
        chain = article.get("update_chain_identity") or article.get("story_identity") or identity
        simple = result.get("simple_result") or {}
        cutoff = simple.get("cutoff_utc")
        own_checks = checks.get(identity, [])
        source_dates = [{k: e.get(k) for k in ("source_id", "document_id", "url", "publisher",
            "published_at_utc", "published_at_source", "canonical_content_sha256")}
            | {"age_seconds": age(e.get("published_at_utc")) if e.get("published_at_source") != "MAIN_REPORT_CUTOFF_NOT_SOURCE_RELEASE_TIME" else None,
               "clock_kind": "MAIN_REPORT_CUTOFF" if e.get("published_at_source") == "MAIN_REPORT_CUTOFF_NOT_SOURCE_RELEASE_TIME" else "SOURCE_PUBLICATION"}
            for e in item.get("evidence") or []]
        watch, watch_origin = None, None
        for preview in item.get("previews") or []:
            payload = preview.get("payload") or {}
            text = payload.get("full_text") or payload.get("text") or payload.get("caption") or ""
            match = re.search(r"(?:What to watch|Watch):\s*(.+?)(?:\n\s*\n|$)", text, re.S)
            if match and match[1].strip() != "What would change that assessment?":
                watch, watch_origin = match[1].strip(), preview["destination"]
                break
        version = {**item, "accepted_at_utc": accepted, "analysis_as_of_utc": cutoff,
            "analysis_age_seconds": age(cutoff), "source_dates": source_dates,
            "next_observation": watch, "next_observation_origin": watch_origin,
            "source_checks": own_checks, "last_source_check_utc": own_checks[-1].get("reviewed_at_utc") if own_checks else None,
            "source_check_scope": "An assessment clock is not a new event, a new source date or current market coverage."}
        groups.setdefault(chain, []).append(version)
    result = []
    for chain, versions in groups.items():
        # Topological parent order first; arrival order breaks ties. Never infer
        # ancestry from a common issuer, title, retrieval clock or market topic.
        remaining = list(versions)
        ordered = []
        while remaining:
            ready = next((v for v in remaining if not v["article"].get("prior_article_identity") or
                v["article"]["prior_article_identity"] not in {p["article_identity"] for p in remaining}), remaining[0])
            ordered.append(ready)
            remaining.remove(ready)
        current = ordered[-1]
        parent_identity = current["article"].get("prior_article_identity")
        prior = next((v for v in ordered if v["article_identity"] == parent_identity), None)
        current_checks = current["source_checks"]
        parent_review_id = current["article"].get("source_review_id")
        origin = next((c for values in checks.values() for c in values if c["review_id"] == parent_review_id), None)
        review = current_checks[-1] if current_checks else origin
        comparison = origin or review
        if not current["last_source_check_utc"] and origin:
            current["last_source_check_utc"] = origin.get("reviewed_at_utc")
        decision = review["decision"] if review else None
        state = ("HOLD" if decision == "STALE_OR_SOURCE_GAP" or (current.get("review") or {}).get("decision") == "HOLD"
            else "CORRECTION_OR_WITHDRAWAL" if decision == "CORRECTION_OR_WITHDRAWAL"
            else "KEEP" if decision == "USE_UNCHANGED"
            else "UPDATE" if decision == "MATERIAL_FOLLOW_UP" or prior else "NEW")
        old_copy = prior["article"].get("social_mechanism_summary") if prior else None
        new_copy = current["article"].get("social_mechanism_summary")
        # Only an explicit producer-authored marker supplies an observation.
        # Do not infer a date/event from a conditional derivative or issuer name.
        observation = None
        if review:
            summary = review.get("reader_change_summary") or ""
            marker = "Next observation:"
            if marker in summary and summary.split(marker, 1)[1].strip():
                observable = summary.split(marker, 1)[1].strip()
                observation = {"observable": observable, "expected_at_utc": None,
                    "date_state": "UNKNOWN_NOT_SUPPLIED", "source_review_id": review["review_id"],
                    "sources": [a["url"] for a in review.get("source_attempts", []) if a.get("status") == "PASS"],
                    "discriminator": current["next_observation"],
                    "missing_evidence": "The subsequent disclosure and its event date have not been established.",
                    "scope": "PRODUCER_REVIEW_OBSERVATION_NOT_NEW_EVENT"}
        result.append({"story_identity": chain, "title": current["article"]["title"], "state": state,
            "current_article_identity": current["article_identity"],
            "prior_article_identity": prior["article_identity"] if prior else None,
            "declared_prior_article_identity": parent_identity,
            "lineage_gap": bool(parent_identity and prior is None),
            "reader_question": current.get("reader_question") or current["article"].get("primary_reader_question"),
            "current_view": current["article"].get("dek"),
            "countercase": current["article"].get("social_policy_summary"),
            "next_observation": observation["observable"] if observation else current["next_observation"],
            "next_observation_origin": "SOURCE_REVIEW_EXPLICIT_OBSERVATION" if observation else current["next_observation_origin"],
            "next_observation_details": observation,
            "conditional_thesis_test": current["next_observation"],
            "latest_assessment": {"decision": review["decision"], "summary": review["reader_change_summary"],
                "cutoff_utc": review["cutoff_utc"], "reviewed_at_utc": review.get("reviewed_at_utc"),
                "missing_sources": [a for a in review.get("source_attempts", []) if a.get("status") != "PASS"]}
                if review and comparison and review["review_id"] != comparison["review_id"] else None,
            "change": {"decision": comparison["decision"] if comparison else None,
                "summary": comparison.get("reader_change_summary") if comparison else None,
                "source_changes": comparison.get("source_changes", []) if comparison else [],
                "interpretation_changed": bool(prior and old_copy != new_copy),
                "prior_interpretation": old_copy, "current_interpretation": new_copy,
                "coverage_complete": comparison.get("source_coverage_complete", all(a.get("status") == "PASS"
                    for a in comparison.get("source_attempts", []))) if comparison else None,
                "missing_sources": [a for a in comparison.get("source_attempts", []) if a.get("status") != "PASS"] if comparison else []},
            "versions": ordered, "current_version": current, "observed_at_utc": observed,
            "publication_authority": False})
    result.sort(key=lambda story: min((n for n in (
        age(story["current_version"]["last_source_check_utc"]),
        age(story["current_version"]["analysis_as_of_utc"])) if n is not None), default=float("inf")))
    return result


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


def story_projection(library, rows, review_records=()):
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
    from live_contentops.capital_chronicle_desk_record_source_v1 import story_context
    return [*stories, *story_context(rows, review_records)]


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
        "reader_question", "follow_up_value", "changed_source_count", "work_required", "missing_inputs", "confirmation_state", "publication_state", "source_item_ids")}
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


def record_native_article_review(store, *, run_id, article_identity, decision, rationale, expected_review_id=None,
                                final_visual_review=None):
    """Revision-bound native result review in the existing review table; no publication grant."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    if decision not in {"KEEP", "REVISE", "HOLD"} or not 20 <= len(rationale.strip()) <= 3000 or _private({"rationale": rationale}):
        raise ValueError("REASONED_KEEP_REVISE_HOLD_REQUIRED")
    key = native_artifact_key(store, run_id, "cc-editorial-final-")
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
            metadata_sha = sha256_of(value["article"])
            from live_contentops.native_desktop_editorial_v1 import native_review_revision
            revision = native_review_revision(value)
            note = {"schema_version": "contentops.native_article_review.v1", "run_id": run_id,
                "article_identity": article_identity, "package_revision": revision, "article_metadata_sha256": metadata_sha,
                "rationale": rationale.strip(), "publication_authority": False}
            from live_contentops.native_publication_latency_v1 import text_revision, text_approval
            approved_at = datetime.now(timezone.utc).isoformat()
            note["text_revision_sha256"] = text_revision(value)
            if decision == "KEEP":
                history = [dict(r) for r in conn.execute("SELECT * FROM review_records WHERE work_item_id=? ORDER BY rowid",
                    (row["work_item_id"],))]
                note["text_approved_at_utc"] = text_approval(history, run_id=run_id,
                    article_identity=article_identity, revision=note["text_revision_sha256"]) or approved_at
                adopted = store.get_outbox_message("native-approved-text-speed-" + sha256_of(run_id))
                if adopted:
                    from live_contentops.native_publication_latency_v1 import _approved_text_speed_basis
                    basis = _approved_text_speed_basis(store, run_id=run_id, result=value)
                    if basis != json.loads(adopted["payload"]):
                        raise ValueError("APPROVED_TEXT_POLICY_BINDING_CHANGED")
                    note["text_approved_at_utc"] = basis["original_approval_clock_utc"]
                from live_contentops.native_publication_latency_v1 import uses_short_path, automated_media_check, SPEED_POLICY
                if uses_short_path(store, run_id=run_id, result=value):
                    note["publication_speed_policy"] = {"policy": SPEED_POLICY, "target_minutes": 15}
                    previous_check = next((json.loads(r["notes"])["automated_media_check"] for r in reversed(history)
                        if json.loads(r["notes"]).get("package_revision") == revision
                        and json.loads(r["notes"]).get("automated_media_check")), None)
                    note["automated_media_check"] = previous_check or automated_media_check(value)
            if final_visual_review is not None:
                from live_contentops.native_desktop_editorial_v1 import final_visual_acceptance
                note["final_visual_review"] = final_visual_acceptance(store, run_id=run_id,
                    result=value, reference=final_visual_review)
            review_id = "native-article-review-" + uuid4().hex
            conn.execute("INSERT INTO review_records VALUES (?,?,?,?,?,?)", (review_id, row["work_item_id"],
                "NATIVE_DESKTOP_ARTICLE_REVIEW", decision, json.dumps(note, ensure_ascii=False), approved_at))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"review_id": review_id, "decision": decision, **note,
        **({"next_operation": "publication-prepare", "publication_priority": "DISPATCH_NOW_WITHIN_15_MINUTES"}
            if decision == "KEEP" and (final_visual_review or note.get("publication_speed_policy")) else {})}


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
