"""Controlled chart consumption with retained text plus independent typed history."""
import hashlib
import json

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.official_primary_evidence_loader_v1 import _html_canonical_visible_text
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_editorial_data_chart, validate_editorial_data_chart,
)


def controlled_sources(root):
    root.mkdir()
    raw = b"<p>In September 2026, controlled goods payrolls changed by 18 thousands of persons.</p>"
    policy = b"<p>Everything that we publish is in the public domain, except for previously copyrighted photographs.</p>"
    digest = lambda b: hashlib.sha256(b).hexdigest()
    text = _html_canonical_visible_text(raw.decode())
    url = "https://www.bls.gov/news.release/archives/empsit_10022026.htm"
    doc = {"document_id": "controlled-retained", "source_url": url,
        "publisher": "U.S. Bureau of Labor Statistics", "raw_sha256": digest(raw),
        "canonical_content_text": text, "canonical_content_sha256": digest(text.encode()),
        "source_adapter_family": "official_macro", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2026-10-02T12:30:00Z", "content_truncated": False}
    (root / "capture.html").write_bytes(raw)
    (root / "policy.html").write_bytes(policy)
    (root / "admission.json").write_text(json.dumps({"status": "PASS", "official_source_documents": [doc],
        "provenance": {"retrieved_at_utc": "2026-10-30T00:00:00Z"}}))
    (root / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
        "records": [{"headline_id": "controlled-retained", "headline_text": text,
            "capture_path": "capture.html", "source_capture_sha256": digest(raw),
            "loader_result_path": "admission.json", "policy_capture_path": "policy.html",
            "policy_url": "https://www.bls.gov/bls/linksite.htm", "policy_capture_sha256": digest(policy),
            "policy_retrieved_at_utc": "2026-10-30T00:00:00Z", "revision_at_utc": "2026-10-30T00:00:00Z",
            "proposition_span": [0, len(text)]}]}))
    research = RetainedSourceResearch(root)
    assert not research.gaps
    record = research.records["controlled-retained"]
    document = {**doc, "url": url, "rights_evidence_sha256": record["rights_evidence_sha256"]}
    binding = {"research_root": str(root), "research_revision": research.revision,
        "source_capture_hashes": {doc["document_id"]: digest(raw)}}
    packet = {"asset_id": "controlled-sector", "chart_type": "horizontal_diverging_bar",
        "title": "Controlled sector", "question": "What is the reported change?", "unit": "thousands of persons",
        "source_caption": "Source: controlled BLS test fixture", "series": [{"name": "Controlled payrolls",
            "points": [{"period": "2026-09", "value": 18, "observation_kind": "REPORTED_ACTUAL",
                "inputs": [{"document_id": doc["document_id"], "support_excerpt": text,
                    "value_text": "18", "source_period_text": "2026", "metric": "controlled payroll change",
                    "source_content_sha256": digest(text.encode()), "unit": "thousands of persons",
                    "prepared_period": "2026-09", "period_basis": {"basis": "CONTROLLED_REPORTED_MONTH"}}]}]}]}
    other = {"document_id": "controlled-independent-history", "canonical_content_text": "Independent typed history"}
    return document, other, binding, packet


@pytest.mark.parametrize("fault", [None, "text", "capture", "missing_document"])
def test_chart_consumes_selected_source_alongside_independent_history(tmp_path, fault):
    doc, other, binding, packet = controlled_sources(tmp_path / "sources")
    if fault == "text":
        doc["canonical_content_text"] += " changed"
    elif fault == "capture":
        binding["source_capture_hashes"][doc["document_id"]] = "0" * 64
    elif fault == "missing_document":
        binding["source_capture_hashes"] = {"absent-source": "0" * 64}
    if fault:
        with pytest.raises(ValueError, match="RETAINED_SOURCE_BINDING_CHANGED"):
            build_editorial_data_chart(packet, [doc, other], output_dir=tmp_path, retained_source_binding=binding)
        return
    asset = build_editorial_data_chart(packet, [doc, other], output_dir=tmp_path, retained_source_binding=binding)
    assert asset["computed_values"] == [[18.0]]
    validate_editorial_data_chart(asset, [doc, other])
    assert other == {"document_id": "controlled-independent-history", "canonical_content_text": "Independent typed history"}
