"""An exact EIA stock workbook feeds source preparation with its binary bound."""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_contentops_source_research_v1 import ROOT, FILING_ROOT


def fixture(root, series):
    def write(name, value):
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return sha256(path.read_bytes()).hexdigest()
    policy = (FILING_ROOT / "facts-policy.json").read_bytes()
    (root / "facts-policy.json").write_bytes(policy)
    spec = next(r for r in json.loads((ROOT / "index.json").read_bytes())["records"]
                if r["policy_url"] == "https://www.eia.gov/about/copyrights_reuse.php")
    terms = (ROOT / spec["policy_capture_path"]).read_bytes()
    (root / "terms.html").write_bytes(terms)
    url = "https://www.eia.gov/dnav/pet/hist_xls/" + series + "w.xls"
    text = "EIA weekly stock estimates (thousand barrels)\n2026-10-23 410625\n2026-10-30 409760"
    known = "2026-11-05T08:00:00Z"
    binary = b"Controlled parser-output binding fixture, not a workbook-format test."
    (root / "history.xls").write_bytes(binary)
    original = write("original.json", {"url": url, "text": text, "observed": known,
        "binary_capture": {"path": "history.xls", "sha256": sha256(binary).hexdigest(),
            "extracted_text_sha256": sha256(text.encode()).hexdigest()}})
    capture = write("capture.json", {"status": "PASS", "url": url,
        "public_write_performed": False, "credential_or_session_material_read": False,
        "source_capture_sha256": original, "canonical_content_text": text,
        "observed_at_utc": known, "excerpts": [{"start": 0, "end": len(text), "text": text}]})
    document = {"document_id": "eia-history", "source_url": url, "publisher": "EIA",
        "source_interest_role": "ORIGINAL_DATA_PRODUCER", "raw_sha256": capture,
        "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
        "source_adapter_family": "official_macro", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2026-11-04T00:00:00Z", "content_truncated": False}
    write("admission.json", {"status": "PASS", "official_source_documents": [document],
        "provenance": {"retrieved_at_utc": known}})
    write("index.json", {"schema_version": "contentops.retained_source_research.v1", "records": [{
        "authorship_class": "ORIGINAL_PUBLIC_FACTS_ONLY", "headline_id": "eia-history",
        "headline_text": text.splitlines()[0], "capture_path": "capture.json", "source_capture_sha256": capture,
        "original_capture_path": "original.json", "original_capture_sha256": original,
        "loader_result_path": "admission.json", "policy_url": "https://www.copyright.gov/help/faq/faq-protect.html",
        "policy_capture_path": "facts-policy.json", "policy_capture_sha256": sha256(policy).hexdigest(),
        "policy_retrieved_at_utc": known, "revision_at_utc": known, "proposition_span": [0, len(text.splitlines()[0])],
        "public_expression_reuse_allowed": False,
        "data_terms": {"url": spec["policy_url"], "capture_path": "terms.html", "sha256": sha256(terms).hexdigest()}}]})


@pytest.mark.parametrize("series", ["WCESTUS1", "WGTSTUS1"])
def test_official_stock_series_reaches_source_consumer(tmp_path, series):
    fixture(tmp_path, series)
    research = RetainedSourceResearch(tmp_path)
    assert not research.gaps
    result = research.evidence({"headline_ids": ["eia-history"], "story_context": {}},
                               cutoff_utc="2026-11-05T09:00:00Z")
    assert result["status"] == "PASS"
    assert "2026-10-30 409760" in result["official_source_documents"][0]["canonical_content_text"]
    (tmp_path / "history.xls").write_bytes(b"changed source bytes")
    assert RetainedSourceResearch(tmp_path).gaps


def test_other_workbook_is_not_admitted_by_the_stock_routes(tmp_path):
    fixture(tmp_path, "OTHER")
    assert RetainedSourceResearch(tmp_path).gaps
