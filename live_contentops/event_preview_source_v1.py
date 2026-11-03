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

HOST_BACKLOG = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\BACKLOG.md")
FROZEN_PREVIEW = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029\20261103-midterm-dossier\PREVIEW.md")


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
    review = approval.decode("utf-8").replace("\r\n", "\n")
    required = ("CC-107", "Ops reviewed it against decisions 35 and 40",
                "It passes.", "Publish it web-only (decision 42)")
    if not all(value in review for value in required):
        raise ValueError("EVENT_PREVIEW_EXACT_OPS_REVIEW_REQUIRED")
    if review.split("\n", 1)[1].strip() not in HOST_BACKLOG.read_text(encoding="utf-8"):
        raise ValueError("EVENT_PREVIEW_REVIEW_NOT_IN_HOST_BACKLOG")
    if (Path(spec["frozen_manifest_path"]).resolve() != FROZEN_PREVIEW.with_name("MANIFEST.sha256").resolve()
            or sha256(FROZEN_PREVIEW.read_bytes()).hexdigest() != digest):
        raise ValueError("EVENT_PREVIEW_HOST_ORIGIN_MISMATCH")
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


def public_preview_event_evidence(source_pack):
    """Code binds exact numeric displays from the admitted preview before writing."""
    from live_contentops.event_article_guard_v1 import _NUMBER
    selected = [d for d in source_pack if (d.get("source_reuse_constraints") or {}).get("scope")
                == "EXACT_OPS_REVIEWED_CAPITAL_CHRONICLE_PUBLIC_PREVIEW_ONLY"]
    if not selected:
        return None
    if len(selected) != 1:
        raise ValueError("ONE_EXACT_PUBLIC_EVENT_PREVIEW_REQUIRED")
    doc = selected[0]
    raw = FROZEN_PREVIEW.read_bytes()
    text = raw.decode("utf-8")
    if (doc["canonical_content_sha256"] != sha256(raw).hexdigest()
            or doc["canonical_content_text"] != text):
        raise ValueError("EVENT_PREVIEW_WRITER_SOURCE_CHANGED")
    facts = {}
    spans = {(m.start(), m.end()) for m in _NUMBER.finditer(text)}
    # A range separator is not an arithmetic negative. Both literal displays
    # remain source-owned, with exact spans; no conversion or rounding occurs.
    spans.update((m.start(), m.end()) for m in re.finditer(r"\d+(?:\.\d+)?%?", text))
    for index, (start, end) in enumerate(sorted(spans)):
        facts[f"preview-number-{index}"] = {
            "display": text[start:end].strip(), "source_ref": doc["url"],
            "source_sha256": sha256(raw).hexdigest(),
            "known_at_utc": "2026-11-02T23:35:08Z",
            "rights_class": "CC_OWNED_PUBLIC_PREVIEW_OPS_APPROVED",
            "public_use_allowed": True,
            "rights_evidence_ref": doc["source_reuse_constraints"]["approval_capture_sha256"],
            "use_label": "PUBLIC_CC_AUTHORED_PREVIEW",
            "source_span": [start, end],
            "source_excerpt": text[max(0, start - 100):min(len(text), end + 100)],
        }
    return {"schema_version": "contentops.event_article_evidence.v1",
            "event_id": "US_MIDTERMS_20261103", "facts": facts, "private_text": []}


def public_preview_chart_rights_bound(document):
    """The exact CC-owned preview uses its Ops approval, not an external licence."""
    rights = document.get("source_reuse_constraints") or {}
    if (rights.get("scope") != "EXACT_OPS_REVIEWED_CAPITAL_CHRONICLE_PUBLIC_PREVIEW_ONLY"
            or rights.get("public_expression_reuse_allowed") is not True
            or not re.fullmatch(r"[a-f0-9]{64}", rights.get("approval_capture_sha256", ""))):
        return False
    raw = FROZEN_PREVIEW.read_bytes()
    return (rights.get("source_capture_sha256") == sha256(raw).hexdigest()
            and document.get("canonical_content_text") == raw.decode("utf-8"))


def validate_native_event_preview(governed, output):
    """Bind the guarded event packet to the canonical copy before native acceptance."""
    evidence = governed.get("public_event_evidence")
    if evidence is None:
        return None
    from live_contentops.event_article_guard_v1 import (
        _NUMBER, _display_text, _strings, check_public_event_article, check_publication_copy,
    )
    article = output.get("article", {})
    event = article.get("event_article")
    if not isinstance(event, dict) or article.get("article_type") != "EVENT_PREVIEW":
        raise ValueError("NATIVE_EVENT_PREVIEW_PACKET_REQUIRED")
    if (event.get("event_time_utc") != "2026-11-03T23:00:00Z"
            or event.get("cutoff_utc") != governed["cutoff_utc"]
            or event.get("article_type") != "EVENT_PREVIEW"):
        raise ValueError("NATIVE_EVENT_PREVIEW_FROZEN_CLOCK_REQUIRED")
    checked = check_public_event_article(event, evidence=evidence)
    copy = event["copy"]
    if copy["headline"] != article.get("title") or copy["dek"] != article.get("dek"):
        raise ValueError("NATIVE_EVENT_CANONICAL_COPY_CHANGED")
    body = re.sub(r"\[\[SOURCE:SOURCE_\d+\]\]", "", article.get("substack_body_markdown", ""))
    def compact(text):
        return re.sub(r"\s+", " ", text).strip()
    for path, text in _strings(copy):
        if path not in {"copy.headline", "copy.dek"} and compact(text) not in compact(body):
            raise ValueError("NATIVE_EVENT_CANONICAL_SECTION_MISSING")
    visible = {key: article.get(key, "") for key in (
        "title", "dek", "search_title", "meta_description", "social_hook",
        "social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary",
    )}
    visible["body"] = body
    roots = article.get("event_preview_root_copy", {})
    if article.get("event_preview_linkless"):
        from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
        if set(roots) != {"x", "threads"}:
            raise ValueError("EVENT_PREVIEW_EXACT_NATIVE_ROOTS_REQUIRED")
        for destination, limit in (("x", 280), ("threads", 500)):
            text = roots[destination]
            if (not isinstance(text, str) or len(text) > limit or "http" in text
                    or "Capital Chronicle" not in text or PUBLIC_NOTICE not in text
                    or CONFLICTS_NOTICE not in text or "Readers decide whether to trade." not in text):
                raise ValueError("EVENT_PREVIEW_ROOT_NOTICE_OR_SCOPE_INVALID")
            visible[destination + "_root"] = text
    check_publication_copy(visible, conditional_calls=event.get("conditional_calls", []))
    allowed = {_display_text(f["display"]) for f in evidence["facts"].values()}
    for text in visible.values():
        for match in _NUMBER.finditer(text):
            if _display_text(match.group()) not in allowed:
                raise ValueError("NATIVE_EVENT_CANONICAL_NUMBER_UNBOUND")
    return checked
