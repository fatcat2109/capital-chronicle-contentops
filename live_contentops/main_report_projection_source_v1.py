"""Exact public excerpts of retained Main reports in the existing source adapter.

Decision 89 keeps Main-report articles operating. This is a source projection,
not another report producer, store or publisher. Private originals stay local.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private, _time, sha256_of
from live_contentops.event_article_guard_v1 import check_publication_copy

AUTHORSHIP = "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION"
PLATFORM = "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION"
REPORT_ROOTS = (
    Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029"),
    Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\report_upgrade_review_20261105"),
)


def verify_projection(spec):
    """Reconstruct every public word from pinned, bounded report spans.

    No raw rows, numerical prediction-market odds, account facts or arbitrary
    filesystem reads enter the public source packet.
    """
    if spec.get("authority_ref") != "JIM_DECISION_89" or _private(spec):
        raise ValueError("MAIN_REPORT_PROJECTION_SCOPE_INVALID")
    if not re.fullmatch(r"urn:cc-public-report:[a-zA-Z0-9:_-]+", spec.get("source_url", "")):
        raise ValueError("MAIN_REPORT_PROJECTION_LOCATOR_INVALID")
    passages = spec.get("passages")
    if not isinstance(passages, list) or not 1 <= len(passages) <= 40:
        raise ValueError("MAIN_REPORT_EXACT_PASSAGES_REQUIRED")
    texts, sources = [], {}
    for passage in passages:
        path = Path(passage["source_path"]).resolve()
        if (path.suffix.lower() != ".md" or not any(path.is_relative_to(root.resolve()) for root in REPORT_ROOTS)
                or path.stat().st_size > 1_000_000):
            raise ValueError("MAIN_REPORT_SOURCE_PATH_INVALID")
        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        if digest != passage["source_sha256"]:
            raise ValueError("MAIN_REPORT_SOURCE_BYTES_CHANGED")
        original = raw.decode("utf-8-sig")
        fragments = passage.get("fragments")
        if not isinstance(fragments, list) or not 1 <= len(fragments) <= 12:
            raise ValueError("MAIN_REPORT_EXACT_FRAGMENTS_REQUIRED")
        extracted = []
        for fragment in fragments:
            start, end = fragment["start"], fragment["end"]
            if (type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(original) or end - start > 1800):
                raise ValueError("MAIN_REPORT_FRAGMENT_RANGE_INVALID")
            text = original[start:end]
            if "|" in text or re.search(r"(?:Kalshi|Polymarket|prediction.market).{0,80}\d", text, re.I):
                raise ValueError("MAIN_REPORT_RAW_OR_PREDICTION_NUMBERS_FORBIDDEN")
            extracted.append(text.strip())
        texts.append(" ".join(extracted))
        sources[str(path)] = digest
    text = "\n\n".join(texts)
    check_publication_copy({"text": text, "title": spec["headline_text"]}, require_notice=False)
    if _time(spec["known_at_utc"]) > _time(spec["revision_at_utc"]):
        raise ValueError("MAIN_REPORT_PROJECTION_CLOCK_ORDER_INVALID")
    capture_hash = sha256_of({"sources": sources, "passages": passages})
    locator = "urn:cc-public-report:main-retained:" + capture_hash
    permission = {"scope": "CAPITAL_CHRONICLE_OWN_REPORT_PUBLIC_EXCERPTS", "authority_ref": "JIM_DECISION_89",
        "provider_safe": True, "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
        "INTERNAL_ANALYSIS_ALLOWED": True, "permitted_consumers": ["internal_research", "narrative_context"],
        "attribution_required": True, "public_expression_reuse_allowed": True,
        "underlying_event_truth_granted": False, "source_capture_sha256": capture_hash}
    document = {"document_id": spec["headline_id"], "title": spec["headline_text"],
        "publisher": "Capital Chronicle", "source_identity": spec["headline_id"],
        "source_url": locator, "reader_source_url": locator,
        "source_authority_class": "governed_capital_chronicle_report_only",
        "source_adapter_family": "capital_chronicle_main_report",
        "published_at_utc": spec["known_at_utc"], "known_at_utc": spec["known_at_utc"],
        "published_at_source": "RETAINED_MAIN_REPORT_KNOWN_AT_NOT_PUBLICATION_CLOCK",
        "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
        "source_capture_sha256": capture_hash, "source_reuse_constraints": permission,
        "public_claim_allowed": True, "report_truth_only": True, "underlying_event_truth_granted": False,
        "retrieval_method": "EXACT_RETAINED_MAIN_REPORT_PUBLIC_SPANS",
        "report_lineage": {"report_id": spec["headline_id"], "report_projection_sha256": capture_hash,
            "origin": "RETAINED_MAIN_REPORT_EXACT_SPANS", "independent_confirmation": False}}
    return {"headline_id": spec["headline_id"], "headline_text": spec["headline_text"],
        "text_sha256": sha256(spec["headline_text"].encode()).hexdigest(),
        "source_identity": spec["headline_id"], "source_account": "Capital Chronicle",
        "source_platform": PLATFORM, "source_url": locator, "official_source_urls": [],
        "source_timestamp_utc": spec["known_at_utc"], "headline_timestamp": spec["known_at_utc"],
        "known_at_utc": spec["known_at_utc"], "retrieval_time_utc": spec["revision_at_utc"],
        "revision_at_utc": spec["revision_at_utc"], "rights_state": "MAIN_PUBLIC_REPORT_PROJECTION",
        "rights_evidence_sha256": sha256_of(permission), "source_capture_sha256": capture_hash,
        "source_permission_record_sha256": sha256_of(permission), "source_permissions": permission,
        "candidate_catalyst_tags": ["midterms", "election", "market-reaction"],
        "originality": "MAIN_ORIGIN_RECIRCULATION", "correction_of": None,
        "document": document, "source_chart": None, "permitted_source_text": text,
        "supporting_headline_ids": [], "research_metadata": {"source_hashes": sources,
            "authority_ref": "JIM_DECISION_89", "independent_event_confirmation": False}}


def projection_evidence(records, request):
    """Same report-truth semantics as the live desk-record evidence route."""
    docs = [r["document"] for r in records]
    return {"status": "PASS", "blockers": [], "evidence_documents": docs,
        "provided_evidence_capabilities": ["credible_report_or_event_confirmation", "basic_attributed_facts"],
        "epistemic_state": {"schema_version": "contentops.v1_simple_epistemic_state.v1",
            "evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT", "event_confirmation_state": "UNCONFIRMED",
            "origin_character": "ON_RECORD", "source_multiplicity": "SINGLE_SOURCE",
            "primary_reporting_publisher": "Capital Chronicle",
            "primary_reporting_source_identity": records[0]["source_identity"],
            "report_proposition": records[0]["headline_text"],
            "event_proposition": "The retained Main report records dated analysis and market observations.",
            "report_truth_supported": True, "event_truth_supported": False,
            "reader_visible_epistemic_label": "DATED CAPITAL CHRONICLE REVIEW",
            "supporting_document_ids": [d["document_id"] for d in docs], "analysis_must_be_conditional": True,
            "underlying_event_may_be_stated_as_confirmed": False, "authority_granted_by_adapter": False,
            "public_write_authority": False,
            "report_scope_notice": "This is a retrospective of Capital Chronicle's dated dossier and review, not a performance record."},
        "provenance": {"request_count_for_call": 0, "new_external_acquisition": False,
            "retrieval_method": "EXACT_RETAINED_MAIN_REPORT_PUBLIC_SPANS"}}


def projection_bytes_already_frozen(record, frozen_records):
    """A new excerpt of the exact held report is not a later factual observation."""
    if record.get("source_platform") != PLATFORM:
        return False
    hashes = record.get("research_metadata", {}).get("source_hashes") or {}
    held = {}
    for prior in frozen_records.values():
        if prior.get("source_platform") == PLATFORM:
            held.update(prior.get("research_metadata", {}).get("source_hashes") or {})
    return bool(hashes) and all(held.get(path) == digest for path, digest in hashes.items())
