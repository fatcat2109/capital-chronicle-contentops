"""Official Treasury source bytes feed the existing evidence consumer."""
import json
from hashlib import sha256

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_eia_official_workbook_source_v1 import fixture


@pytest.mark.parametrize("series", ["daily_treasury_yield_curve", "daily_treasury_real_yield_curve"])
def test_treasury_yield_source_reaches_evidence_consumer(tmp_path, series):
    fixture(tmp_path, "WCESTUS1")
    url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView"
           "?type=" + series + "&field_tdr_date_value=2026")
    index = json.loads((tmp_path / "index.json").read_bytes())
    spec = index["records"][0]
    original = json.loads((tmp_path / "original.json").read_bytes())
    original["url"] = url
    raw = json.dumps(original).encode()
    (tmp_path / "original.json").write_bytes(raw)
    spec["original_capture_sha256"] = sha256(raw).hexdigest()
    capture = json.loads((tmp_path / "capture.json").read_bytes())
    capture.update(url=url, source_capture_sha256=spec["original_capture_sha256"])
    raw = json.dumps(capture).encode()
    (tmp_path / "capture.json").write_bytes(raw)
    spec["source_capture_sha256"] = sha256(raw).hexdigest()
    admission = json.loads((tmp_path / "admission.json").read_bytes())
    admission["official_source_documents"][0].update(source_url=url, publisher="U.S. Treasury",
                                                     raw_sha256=spec["source_capture_sha256"])
    (tmp_path / "admission.json").write_text(json.dumps(admission))
    (tmp_path / "index.json").write_text(json.dumps(index))
    research = RetainedSourceResearch(tmp_path)
    assert not research.gaps
    result = research.evidence({"headline_ids": ["eia-history"], "story_context": {}},
                               cutoff_utc="2026-11-05T09:00:00Z")
    assert result["status"] == "PASS"
    assert result["official_source_documents"][0]["source_url"] == url
    # An altered downloaded file cannot supply a chart or article.
    (tmp_path / "history.xls").write_bytes(b"changed source bytes")
    assert RetainedSourceResearch(tmp_path).gaps


def test_treasury_other_page_cannot_impersonate_yield_source(tmp_path):
    fixture(tmp_path, "WCESTUS1")
    admission = json.loads((tmp_path / "admission.json").read_bytes())
    admission["official_source_documents"][0]["source_url"] = "https://home.treasury.gov/news/press-releases/other"
    (tmp_path / "admission.json").write_text(json.dumps(admission))
    assert RetainedSourceResearch(tmp_path).gaps
