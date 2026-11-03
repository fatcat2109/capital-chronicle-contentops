"""Synthetic CNBC source admission and clock/rights regressions; no network or live store."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_contentops_source_research_v1 import REPORT_ROOT


def _write(root, name, value):
    path = root / name
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(root):
    root.mkdir()
    policy = json.loads((REPORT_ROOT / "index.json").read_bytes())["records"][0]
    shutil.copyfile(REPORT_ROOT / policy["policy_capture_path"], root / "policy.json")
    url = "https://www.cnbc.com/2026/10/29/stock-market-today-live-updates.html"
    stamp = "Fri, Oct 30 202612:25 PM EDT"
    title = "Controlled supplier considers an all-stock purchase, CNBC reports"
    excerpt = stamp + "\n\n## " + title + "\n\nCNBC reports that a controlled supplier is considering a share-funded purchase; no agreement is announced."
    text = "[CNBC](https://www.cnbc.com/world/)\nUpdated Sat, Oct 31 2026 4:20 PM EDT\n\n" + excerpt + "\n\n— Controlled Reporter\n"
    start = text.index(stamp)
    original_hash = _write(root, "original.json", {"url": url, "title": "Controlled market updates", "text": text})
    capture = {"status": "PASS", "url": url, "reporting_publisher": "CNBC", "byline": "Controlled Reporter",
        "attribution_text": "Controlled Reporter, CNBC", "retrieval_method": "READ_ONLY_BROWSEROS_NEO_BOUNDED_EXTRACTS",
        "credential_or_session_material_read": False, "public_write_performed": False,
        "observed_at_utc": "2026-11-02T04:00:00Z", "full_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "full_text_characters": len(text), "publication_timestamp_span": [start, start + len(stamp)],
        "excerpts": [{"start": start, "end": start + len(excerpt), "text": excerpt}]}
    capture_hash = _write(root, "capture.json", capture)
    doc = {"document_id": "controlled-cnbc", "title": title, "source_url": url, "publisher": "CNBC",
        "source_identity": "cnbc.com", "raw_sha256": capture_hash, "canonical_content_text": excerpt,
        "canonical_content_sha256": hashlib.sha256(excerpt.encode()).hexdigest(), "source_adapter_family": "reputable_secondary_report",
        "source_authority_class": "reputable_secondary_source", "report_truth_only": True,
        "published_at_utc": "2026-10-30T16:25:00Z", "published_at_source": stamp, "content_truncated": False}
    _write(root, "admission.json", {"status": "PASS", "official_source_documents": [doc], "provenance": {"retrieved_at_utc": capture["observed_at_utc"]}})
    offset = excerpt.index(title)
    spec = {"authorship_class": "REPUTABLE_REPORT_FACTS_ONLY", "headline_id": "controlled-cnbc", "headline_text": title,
        "capture_path": "capture.json", "source_capture_sha256": capture_hash,
        "original_capture_path": "original.json", "original_capture_sha256": original_hash, "loader_result_path": "admission.json",
        "policy_url": policy["policy_url"], "policy_capture_path": "policy.json",
        "policy_capture_sha256": hashlib.sha256((root / "policy.json").read_bytes()).hexdigest(),
        "policy_retrieved_at_utc": "2026-10-21T21:02:03.468Z", "revision_at_utc": "2026-11-02T04:01:00Z",
        "proposition_span": [offset, offset + len(title)], "public_expression_reuse_allowed": False}
    _write(root, "index.json", {"schema_version": "contentops.retained_source_research.v1", "records": [spec]})
    return root


def _mutate_capture(root, change):
    capture = json.loads((root / "capture.json").read_bytes())
    change(capture)
    capture_hash = _write(root, "capture.json", capture)
    index = json.loads((root / "index.json").read_bytes())
    index["records"][0]["source_capture_sha256"] = capture_hash
    _write(root, "index.json", index)
    admission = json.loads((root / "admission.json").read_bytes())
    admission["official_source_documents"][0]["raw_sha256"] = capture_hash
    _write(root, "admission.json", admission)


def test_exact_cnbc_entry_preserves_report_truth_and_facts_only_scope(tmp_path):
    research = RetainedSourceResearch(_fixture(tmp_path / "source"))
    assert not research.gaps and len(research.records) == 1, research.gaps
    record = research.records["controlled-cnbc"]
    assert record["source_identity"] == "cnbc.com"
    assert record["source_timestamp_utc"] == "2026-10-30T16:25:00Z"
    assert record["known_at_utc"] == "2026-11-02T04:00:00Z"
    permission = record["source_permissions"]
    assert permission["scope"] == "ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"
    assert permission["MODEL_INPUT_ALLOWED"] and permission["attribution_required"]
    for name in ("public_expression_reuse_allowed", "images_logos_exhibits_reuse_allowed", "underlying_event_truth_granted", "government_authorship"):
        assert permission[name] is False
    from live_contentops.v1_simple_epistemic_state_v1 import candidate_report_provenance
    request = {"headline_ids": ["controlled-cnbc"], "story_context": {
        "leaf_summaries": [record["headline_text"]], "report_provenance": candidate_report_provenance({
            "headline_text": record["headline_text"] + " - CNBC"})}}
    evidence = research.evidence(request, cutoff_utc="2026-11-02T04:02:00Z")
    assert evidence["status"] == "PASS", evidence.get("blockers")
    assert evidence["epistemic_state"]["primary_reporting_publisher"] == "CNBC"
    assert evidence["epistemic_state"]["report_truth_supported"] is True
    assert evidence["epistemic_state"]["event_truth_supported"] is False
    assert evidence["publication_authority"] is False
    request["story_context"]["report_provenance"]["primary_reporting_source_identity"] = "reuters.com"
    refused = research.evidence(request, cutoff_utc="2026-11-02T04:02:00Z")
    assert refused["status"] == "BLOCKED" and "epistemic_report_provenance_not_governed" in refused["blockers"]


@pytest.mark.parametrize("mutation", [
    lambda c: c.pop("publication_timestamp_span"),
    lambda c: c.update(publication_timestamp_span=[0, 5]),
    lambda c: c.update(full_text_sha256="0" * 64),
    lambda c: c.update(byline="Unobserved reporter"),
    lambda c: c["excerpts"][0].update(text=c["excerpts"][0]["text"].replace("share-funded", "cash-funded")),
])
def test_cnbc_rejects_unbound_original_timestamp_byline_or_passage(tmp_path, mutation):
    root = _fixture(tmp_path / "source")
    _mutate_capture(root, mutation)
    research = RetainedSourceResearch(root)
    assert not research.records and research.gaps


@pytest.mark.parametrize("published", ["2026-10-30T12:25:00Z", "2026-10-31T20:20:00Z"])
def test_cnbc_cannot_substitute_local_time_or_later_global_update_for_entry(tmp_path, published):
    root = _fixture(tmp_path / "source")
    admission = json.loads((root / "admission.json").read_bytes())
    admission["official_source_documents"][0]["published_at_utc"] = published
    _write(root, "admission.json", admission)
    research = RetainedSourceResearch(root)
    assert not research.records and research.gaps[0]["state"] == "PUBLIC_REPORT_PUBLICATION_CLOCK_NOT_VERIFIED"


@pytest.mark.parametrize("field,value", [("public_expression_reuse_allowed", True), ("policy_capture_sha256", "0" * 64)])
def test_cnbc_cannot_expand_reuse_or_drop_policy_evidence(tmp_path, field, value):
    root = _fixture(tmp_path / "source")
    index = json.loads((root / "index.json").read_bytes())
    index["records"][0][field] = value
    _write(root, "index.json", index)
    research = RetainedSourceResearch(root)
    assert not research.records and research.gaps


def test_cnbc_rejects_changed_original_even_with_resealed_excerpt_capture(tmp_path):
    root = _fixture(tmp_path / "source")
    original = json.loads((root / "original.json").read_bytes())
    original["text"] = original["text"].replace("share-funded", "cash-funded")
    _write(root, "original.json", original)
    research = RetainedSourceResearch(root)
    assert not research.records and research.gaps[0]["state"] == "PUBLIC_REPORT_ORIGINAL_IDENTITY_OR_SPANS_INVALID"
