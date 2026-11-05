"""The SEC's exact bulletin reaches the existing newsroom source consumer."""
import hashlib
import json

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.official_primary_evidence_loader_v1 import _html_canonical_visible_text
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack

URL = "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/ETPBulletinSeptember2024"


def source(root, *, url=URL, permitted=True):
    def write(name, data):
        raw = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        (root / name).write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    body = "<p>Spot bitcoin products hold bitcoin and expose investors to its price volatility.</p>"
    text = _html_canonical_visible_text(body)
    raw_hash = write("source.html", body)
    policy = ("Information presented on SEC.gov may be copied or further distributed. "
              "Please do not use the SEC seal.") if permitted else "All rights reserved."
    policy_hash = write("policy.html", policy)
    document = {"document_id": "sec-bulletin", "title": "Bitcoin ETP bulletin",
        "source_url": url, "publisher": "SEC Office of Investor Education and Advocacy",
        "source_identity": "www.investor.gov", "raw_sha256": raw_hash,
        "canonical_content_text": text, "canonical_content_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_adapter_family": "sec_regulatory", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2024-09-09T00:00:00Z", "content_truncated": False}
    write("admission.json", {"status": "PASS", "official_source_documents": [document],
        "provenance": {"retrieved_at_utc": "2026-11-05T18:00:00Z"}})
    write("index.json", {"schema_version": "contentops.retained_source_research.v1", "records": [{
        "headline_id": "sec-bulletin", "headline_text": text, "capture_path": "source.html",
        "source_capture_sha256": raw_hash, "loader_result_path": "admission.json",
        "policy_url": "https://www.sec.gov/about/privacy-information", "policy_capture_path": "policy.html",
        "policy_capture_sha256": policy_hash, "policy_retrieved_at_utc": "2026-11-05T18:00:00Z",
        "revision_at_utc": "2026-11-05T18:00:00Z", "proposition_span": [0, len(text)]}]})
    return RetainedSourceResearch(root)


def test_verified_bulletin_reaches_writer_source_pack(tmp_path):
    research = source(tmp_path)
    assert not research.gaps
    evidence = research.evidence({"headline_ids": ["sec-bulletin"]}, cutoff_utc="2026-11-05T18:01:00Z")
    assert evidence["status"] == "PASS"
    pack = _source_pack(evidence["evidence_documents"])
    assert len(pack) == 1 and pack[0]["url"] == URL
    assert "price volatility" in pack[0]["canonical_content_text"]
    assert pack[0]["underlying_reuse_classification"] == "governed_government_public_domain"


@pytest.mark.parametrize("url,permitted,cause", [
    (URL + "-unbound", True, "SOURCE_REUSE_POLICY_NOT_SUPPORTED"),
    (URL, False, "SOURCE_PERMISSION_TEXT_NOT_VERIFIED"),
])
def test_other_pages_and_unverified_rights_do_not_inherit_bulletin_permission(tmp_path, url, permitted, cause):
    research = source(tmp_path, url=url, permitted=permitted)
    assert not research.records and research.gaps[0]["state"] == cause
