from __future__ import annotations

import json

from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
)


AS_OF = "2026-08-08T12:00:00Z"


def _request(*, family, required, url):
    return {
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "request_logical_hash": "a" * 64,
        "source_adapter_families": [family],
        "required_evidence_capabilities": required,
        "story_context": {
            "official_source_urls": [url],
            "official_source_url_bindings": [
                {"url": url, "headline_id": "headline-1"}
            ],
        },
    }


def _response(url, body, content_type="application/json"):
    return {
        "status": 200,
        "final_url": url,
        "headers": {"content-type": content_type},
        "body": body,
    }


def test_regulatory_primary_source_supplies_document_timeline_and_entities():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({
        "title": "Final rule",
        "publication_date": "2026-08-08",
        "effective_on": "2026-09-08",
        "agencies": [{"name": "Official Agency"}],
    }).encode()
    calls = []
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda requested, timeout, maximum: calls.append(
            (requested, timeout, maximum)
        ) or _response(url, body),
    )

    packet = loader(_request(
        family="official_regulatory_fiscal",
        required=["official_document", "implementation_timeline", "affected_entities"],
        url=url,
    ))

    assert packet["status"] == "PASS"
    assert len(calls) == 1
    assert packet["provided_evidence_capabilities"] == [
        "affected_entities", "implementation_timeline", "official_document"
    ]
    document = packet["official_source_documents"][0]
    assert document["source_authority_class"] == "official_public_primary_source"
    assert document["raw_sha256"] == document["canonical_content_sha256"]
    assert document["published_at_utc"] == "2026-08-08T00:00:00Z"
    assert document["retrieval_method"] == "READ_ONLY_HTTP_GET"
    assert document["source_headline_id"] == "headline-1"


def test_sec_company_primary_source_supplies_exact_filing_facts():
    url = "https://data.sec.gov/submissions/CIK0000320193.json"
    body = json.dumps({
        "cik": "0000320193",
        "name": "Example Issuer",
        "filings": {"recent": {
            "accessionNumber": ["0000320193-26-000001"],
            "filingDate": ["2026-08-08"],
            "form": ["8-K"],
            "primaryDocument": ["event.htm"],
        }},
    }).encode()
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: _response(url, body),
    )

    packet = loader(_request(
        family="sec_regulatory",
        required=[
            "company_filing_or_release", "filing_or_release_timeline", "affected_entities"
        ],
        url=url,
    ))

    assert packet["status"] == "PASS"
    assert set(packet["provided_evidence_capabilities"]) == {
        "company_filing_or_release", "filing_or_release_timeline", "affected_entities"
    }


def test_official_macro_source_supplies_exact_release_values_timestamps_definitions():
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0"
    body = json.dumps({
        "status": "REQUEST_SUCCEEDED",
        "releaseDate": "2026-08-08",
        "Results": {"series": [{
            "seriesID": "CUUR0000SA0",
            "data": [{"year": "2026", "period": "M07", "periodName": "July", "value": "321.5"}],
        }]},
    }).encode()
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: _response(url, body),
    )

    packet = loader(_request(
        family="official_macro",
        required=[
            "official_release", "authorized_release_values", "release_timestamps", "release_definitions"
        ],
        url=url,
    ))

    assert packet["status"] == "PASS"
    assert set(packet["provided_evidence_capabilities"]) == {
        "official_release", "authorized_release_values", "release_timestamps", "release_definitions"
    }


def test_x_arbitrary_hosts_and_missing_exact_capabilities_fail_closed():
    network_calls = []
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: network_calls.append(_args),
    )
    x_packet = loader(_request(
        family="official_macro",
        required=["official_release"],
        url="https://x.com/source/status/1",
    ))
    assert x_packet["status"] == "BLOCKED"
    assert "official_source_url_family_binding_invalid" in x_packet["blockers"]
    assert network_calls == []

    url = "https://www.bls.gov/news.release/empty.htm"
    weak = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: _response(
            url,
            b'<html><time datetime="2026-08-08">Updated</time></html>',
            "text/html",
        ),
    )(_request(
        family="official_macro",
        required=["official_release", "authorized_release_values"],
        url=url,
    ))
    assert weak["status"] == "BLOCKED"
    assert "authorized_release_values" not in weak["provided_evidence_capabilities"]
    assert any(
        row == "required_evidence_capability_missing:authorized_release_values"
        for row in weak["blockers"]
    )


def test_source_url_without_exact_headline_binding_does_not_trigger_network():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    calls = []
    request = _request(
        family="official_regulatory_fiscal",
        required=["official_document"],
        url=url,
    )
    request["story_context"]["official_source_url_bindings"][0]["headline_id"] = "other"
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: calls.append(_args),
    )(request)

    assert packet["status"] == "BLOCKED"
    assert "exact_official_source_url_unavailable" in packet["blockers"]
    assert calls == []
