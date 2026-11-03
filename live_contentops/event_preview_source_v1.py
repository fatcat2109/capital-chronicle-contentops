"""Read an Ops-approved public preview, never its private event dossier.

This is an input adapter for the existing retained-research owner. Approval covers
the exact authored preview, not its private inputs or independent event truth.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from live_contentops.event_article_guard_v1 import check_publication_copy
from live_contentops.capital_chronicle_latest_report_consumer_v1 import _time, sha256_of


def approved_preview_record(spec, *, read):
    raw = read(spec["capture_path"])
    digest = sha256(raw).hexdigest()
    if digest != spec["source_capture_sha256"]:
        raise ValueError("EVENT_PREVIEW_BYTES_CHANGED")
    manifest = Path(spec["frozen_manifest_path"]).read_text(encoding="utf-8")
    if not re.search(r"(?m)^" + digest + r"\s+PREVIEW\.md\s*$", manifest):
        raise ValueError("EVENT_PREVIEW_FROZEN_MANIFEST_MISMATCH")
    approval = read(spec["approval_capture_path"])
    if sha256(approval).hexdigest() != spec["approval_capture_sha256"]:
        raise ValueError("EVENT_PREVIEW_APPROVAL_CHANGED")
    # The configured owner pins an actual backlog review, separately from copy.
    # Keep this route narrow until Main's public event export is wired.
    review = approval.decode("utf-8")
    required = ("CC-107", "Ops reviewed it against decisions 35 and 40",
                "It passes.", "Publish it web-only (decision 42)")
    if not all(value in review for value in required):
        raise ValueError("EVENT_PREVIEW_EXACT_OPS_REVIEW_REQUIRED")
    text = raw.decode("utf-8")
    check_publication_copy({"text": text}, require_notice=False)
    title = text.splitlines()[0].removeprefix("# ").strip()
    if not title or not spec.get("known_at_utc") or not spec.get("source_url"):
        raise ValueError("EVENT_PREVIEW_SOURCE_BINDING_REQUIRED")
    if _time(spec["known_at_utc"]) > _time(spec["revision_at_utc"]):
        raise ValueError("EVENT_PREVIEW_CLOCK_ORDER_INVALID")
    permission = {
        "scope": "EXACT_OPS_REVIEWED_CAPITAL_CHRONICLE_PUBLIC_PREVIEW_ONLY",
        "source_capture_sha256": digest,
        "approval_capture_sha256": spec["approval_capture_sha256"],
        "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True,
        "INTERNAL_ANALYSIS_ALLOWED": True, "provider_safe": True,
        "public_expression_reuse_allowed": True,
        "images_logos_exhibits_reuse_allowed": False,
        "underlying_event_truth_granted": False,
    }
    document = {
        "document_id": spec["headline_id"], "title": title,
        "publisher": "Capital Chronicle", "source_identity": spec["headline_id"],
        "source_authority_class": "governed_capital_chronicle_report_only",
        "source_adapter_family": "ops_approved_event_preview",
        "source_url": spec["source_url"], "reader_source_url": spec["source_url"],
        "published_at_utc": spec["known_at_utc"],
        "published_at_source": "FROZEN_PREVIEW_NOT_PUBLICATION_TIME",
        "known_at_utc": spec["known_at_utc"],
        "canonical_content_text": text, "canonical_content_sha256": digest,
        "raw_sha256": digest, "source_capture_sha256": digest,
        "content_truncated": False, "public_claim_allowed": True,
        "report_truth_only": True, "underlying_event_truth_granted": False,
        "retrieval_method": "READ_ONLY_FROZEN_OPS_APPROVED_PUBLIC_PREVIEW",
        "source_reuse_constraints": permission,
    }
    return {
        "headline_id": spec["headline_id"], "headline_text": title,
        "text_sha256": sha256(title.encode()).hexdigest(),
        "source_identity": spec["headline_id"], "source_account": "Capital Chronicle",
        "source_platform": "CAPITAL_CHRONICLE_APPROVED_PUBLIC_EVENT_PREVIEW",
        "source_url": spec["source_url"], "official_source_urls": [],
        "source_timestamp_utc": spec["known_at_utc"],
        "headline_timestamp": spec["known_at_utc"], "known_at_utc": spec["known_at_utc"],
        "retrieval_time_utc": spec["known_at_utc"], "revision_at_utc": spec["revision_at_utc"],
        "rights_state": "EXACT_CC_AUTHORED_PUBLIC_PREVIEW_OPS_APPROVED",
        "rights_evidence_sha256": spec["approval_capture_sha256"],
        "source_capture_sha256": digest, "source_permissions": permission,
        "source_permission_record_sha256": sha256_of(permission),
        "candidate_catalyst_tags": ["midterms", "policy", "rates", "equities"],
        "originality": "GOVERNED_CAPITAL_CHRONICLE_PUBLIC_PREVIEW",
        "document": document, "source_chart": None,
        "permitted_source_text": text, "supporting_headline_ids": [],
        "research_metadata": {"context_kind": "DATED_PRE_EVENT_SCENARIOS_NOT_EVENT_CONFIRMATION",
                              "family": "MACRO", "assets": ["US_RATES", "USD", "GOLD", "OIL", "US_INDICES"]},
    }


def approved_preview_evidence(records, request, *, revision):
    """Preserve the established CC-report epistemic boundary; never officialise it."""
    docs = [r["document"] for r in records]
    return {
        "status": "PASS", "blockers": [], "evidence_documents": docs,
        "publication_authority": False,
        "epistemic_state": {
            "schema_version": "contentops.v1_simple_epistemic_state.v1",
            "evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT",
            "event_confirmation_state": "UNCONFIRMED", "origin_character": "ON_RECORD",
            "source_multiplicity": "SINGLE_SOURCE", "primary_reporting_publisher": "Capital Chronicle",
            "primary_reporting_source_identity": docs[0]["source_identity"],
            "report_proposition": "Capital Chronicle's dated, Ops-reviewed pre-event preview.",
            "event_proposition": "Scenarios are conditional; the election outcome is unknown.",
            "report_truth_supported": True, "event_truth_supported": False,
            "reader_visible_epistemic_label": "CC PREVIEW / CONDITIONAL SCENARIOS",
            "supporting_document_ids": [d["document_id"] for d in docs],
            "analysis_must_be_conditional": True, "underlying_event_may_be_stated_as_confirmed": False,
            "authority_granted_by_adapter": False, "public_write_authority": False,
        },
        "rolling_x_story_binding": {k: request.get(k) for k in ("cluster_id", "headline_ids", "request_logical_hash")},
        "provenance": {"request_count_for_call": 0, "new_external_acquisition": False,
                       "retained_research_revision": revision,
                       "retrieval_method": "READ_ONLY_FROZEN_OPS_APPROVED_PUBLIC_PREVIEW"},
    }
