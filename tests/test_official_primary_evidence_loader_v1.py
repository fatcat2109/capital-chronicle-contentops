from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest

import live_contentops.official_primary_evidence_loader_v1 as loader_module

from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
    _default_http_get,
)


AS_OF = "2026-08-08T12:00:00Z"
BEA_SCHEDULE_URL = "https://www.bea.gov/news/schedule"
BEA_SCHEDULE_HTML = b"""
<html><head><title>Release Schedule | U.S. Bureau of Economic Analysis (BEA)</title>
<meta name="date" content="2026-08-08T10:00:00Z"></head><body><table><tbody>
<tr class="scheduled-releases-type-press">
  <td class="scheduled-date no-wrap"><div class="release-date">August 26</div>
  <small class="text-muted">8:30 AM</small></td>
  <td class="release-title views-field">GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026</td>
</tr>
<tr class="scheduled-releases-type-press">
  <td class="scheduled-date no-wrap"><div class="release-date">August 26</div>
  <small class="text-muted">8:30 AM</small></td>
  <td class="release-title views-field">Personal Income and Outlays, July 2026</td>
</tr></tbody></table></body></html>
"""


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
    assert packet["provenance"]["evaluation_as_of_utc"] == AS_OF
    assert packet["provenance"]["retrieved_at_utc"] is not None


def test_official_html_release_date_with_public_month_name_is_point_in_time_bound():
    url = "https://www.eia.gov/outlooks/steo/"
    body = b"""
      <html><head><title>Short-Term Energy Outlook - EIA</title></head><body>
      <h1>Short-Term Energy Outlook</h1>
      <strong>Release Date:</strong> August 11, 2026
      <p>Current forecast values.</p></body></html>
    """
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-12T08:00:00Z",
        http_get=lambda *_args: _response(url, body, "text/html"),
    )(_request(
        family="official_macro",
        required=["official_release", "release_timestamps"],
        url=url,
    ))

    assert packet["status"] == "PASS"
    document = packet["official_source_documents"][0]
    assert document["published_at_utc"] == "2026-08-11T00:00:00Z"
    assert document["source_headline_id"] == "headline-1"
    assert document["title"] == "Short-Term Energy Outlook - EIA"
    assert set(packet["provided_evidence_capabilities"]) >= {
        "official_release",
        "release_timestamps",
    }


def test_official_pdf_uses_bounded_injected_text_extraction_for_factual_depth():
    url = "https://www.bls.gov/news.release/pdf/cpi.pdf"
    body = b"%PDF-1.7 bounded fixture bytes"
    extracted = (
        "Consumer Price Index news release. The all items index increased 0.2 percent in July "
        "and 2.7 percent over the last 12 months. The index for shelter rose. Data are "
        "seasonally adjusted; see the technical note and definitions."
    )
    response = _response(url, body, "application/pdf")
    response["headers"]["last-modified"] = "Sat, 08 Aug 2026 11:00:00 GMT"
    calls = []
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: response,
        pdf_text_extractor=lambda value: calls.append(value) or extracted,
    )(_request(
        family="official_macro",
        required=[
            "official_release",
            "authorized_release_values",
            "release_definitions",
        ],
        url=url,
    ))

    assert packet["status"] == "PASS"
    assert calls == [body]
    document = packet["official_source_documents"][0]
    assert document["content_type"] == "application/pdf"
    assert document["canonical_content_text"] == extracted
    assert set(packet["provided_evidence_capabilities"]) >= {
        "official_release",
        "authorized_release_values",
        "release_definitions",
    }


def test_generic_dated_official_page_does_not_gain_release_capability():
    url = "https://www.eia.gov/about/"
    body = b"""
      <html><head><title>About EIA</title></head><body>
      <h1>About EIA</h1><strong>Release Date:</strong> August 11, 2026
      <p>Contact and organization information.</p></body></html>
    """
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-12T08:00:00Z",
        http_get=lambda *_args: _response(url, body, "text/html"),
    )(_request(
        family="official_macro",
        required=["official_release"],
        url=url,
    ))

    assert packet["status"] == "BLOCKED"
    assert "official_release" not in packet["provided_evidence_capabilities"]


def test_exact_eia_weekly_storage_table_verifies_release_values_and_timestamp():
    url = "https://www.eia.gov/dnav/ng/ng_stor_wkly_s1_w.htm"
    body = b"""
      <html><head><title>Weekly Working Gas in Underground Storage</title></head>
      <body><h1>Weekly Working Gas in Underground Storage</h1>
      <p>Total Lower 48 States: 3,169 billion cubic feet</p>
      <a>Definitions, Sources & Notes</a>
      <td>Release Date: 8/20/2026</td></body></html>
    """
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-21T12:00:00Z",
        http_get=lambda *_args: _response(url, body, "text/html"),
    )(_request(
        family="official_macro",
        required=[
            "official_release",
            "authorized_release_values",
            "release_timestamps",
        ],
        url=url,
    ))

    assert packet["status"] == "PASS", packet.get("blockers")
    assert packet["official_source_documents"][0]["published_at_utc"] == (
        "2026-08-20T00:00:00Z"
    )
    assert set(packet["provided_evidence_capabilities"]) >= {
        "official_release",
        "authorized_release_values",
        "release_timestamps",
    }


def test_exact_philadelphia_fed_mbos_page_verifies_release_values():
    url = (
        "https://www.philadelphiafed.org/surveys-and-data/"
        "regional-economic-analysis/mbos-2026-08"
    )
    body = b"""
      <html><head><title>Manufacturing Business Outlook Survey (MBOS) - August 2026 Report</title>
      </head><body><h1>Manufacturing Business Outlook Survey</h1>
      <p>August 20, 2026. The current general activity index was 47.4.</p>
      <p>Seasonally adjusted series and definitions are provided.</p></body></html>
    """
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-21T12:00:00Z",
        http_get=lambda *_args: {
            **_response(url, body, "text/html"),
            "headers": {
                "content-type": "text/html",
                "last-modified": "Thu, 20 Aug 2026 12:00:00 GMT",
            },
        },
    )(_request(
        family="official_macro",
        required=["official_release", "authorized_release_values"],
        url=url,
    ))

    assert packet["status"] == "PASS", packet.get("blockers")
    assert set(packet["provided_evidence_capabilities"]) >= {
        "official_release",
        "authorized_release_values",
        "release_timestamps",
    }


def test_narrow_waymo_company_publication_verifies_release_without_widening_other_blogs():
    url = "https://waymo.com/blog/2026/08/look-under-our-trunk/"
    body = b"""
      <html><head><title>A look under our trunk: what's in our compute</title>
      <meta property="article:published_time" content="2026-08-20T00:00:00Z"></head>
      <body><h1>Waymo compute</h1><p>Our purpose-built 5nm ASIC is custom silicon
      for the Waymo Driver and robotaxi compute.</p></body></html>
    """
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-21T12:00:00Z",
        http_get=lambda *_args: _response(url, body, "text/html"),
    )(_request(
        family="company_primary",
        required=[
            "company_filing_or_release",
            "filing_or_release_timeline",
            "affected_entities",
        ],
        url=url,
    ))

    assert packet["status"] == "PASS", packet.get("blockers")
    assert set(packet["provided_evidence_capabilities"]) >= {
        "company_filing_or_release",
        "filing_or_release_timeline",
        "affected_entities",
    }
    assert packet["publication_authority"] is False


def test_bea_schedule_rows_are_exactly_bound_to_official_bytes_and_document_hash():
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-08T12:00:00Z",
        http_get=lambda *_args: _response(
            BEA_SCHEDULE_URL, BEA_SCHEDULE_HTML, "text/html"
        ),
    )(_request(
        family="official_macro",
        required=[
            "official_schedule",
            "scheduled_event_identity",
            "scheduled_event_date_time",
        ],
        url=BEA_SCHEDULE_URL,
    ))

    assert packet["status"] == "PASS"
    assert set(packet["provided_evidence_capabilities"]) >= {
        "official_schedule",
        "scheduled_event_identity",
        "scheduled_event_date_time",
        "scheduled_period_or_edition_label",
    }
    document = packet["official_source_documents"][0]
    rows = document["scheduled_event_rows"]
    assert [row["source_text"] for row in rows] == [
        "August 26 8:30 AM — GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026",
        "August 26 8:30 AM — Personal Income and Outlays, July 2026",
    ]
    assert [row["period_or_edition_label"] for row in rows] == [
        "2nd Quarter 2026",
        "July 2026",
    ]
    assert all(
        row["evidence_document_id"] == document["document_id"]
        and row["source_content_sha256"] == document["canonical_content_sha256"]
        and row["inferred_fields"] == []
        and row["llm_factual_or_numeric_authority"] is False
        and row["publication_authority"] is False
        for row in rows
    )
    assert document[
        "schedule_extraction_grants_factual_numeric_permission_or_publication_authority"
    ] is False


def test_official_schedule_without_complete_date_time_title_row_fails_closed():
    incomplete = BEA_SCHEDULE_HTML.replace(
        b'<small class="text-muted">8:30 AM</small>', b"", 2
    )
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-08T12:00:00Z",
        http_get=lambda *_args: _response(BEA_SCHEDULE_URL, incomplete, "text/html"),
    )(_request(
        family="official_macro",
        required=[
            "official_schedule",
            "scheduled_event_identity",
            "scheduled_event_date_time",
        ],
        url=BEA_SCHEDULE_URL,
    ))

    assert packet["status"] == "BLOCKED"
    assert packet["official_source_documents"][0]["scheduled_event_rows"] == []
    assert set(packet["provided_evidence_capabilities"]).isdisjoint({
        "official_schedule",
        "scheduled_event_identity",
        "scheduled_event_date_time",
    })


def test_retrieval_provenance_uses_actual_clock_not_evaluation_cutoff_or_request_payload():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({
        "title": "Final rule",
        "publication_date": "2026-08-07T18:30:00Z",
    }).encode()
    retrieved_at = datetime(2026, 8, 8, 12, 0, 1, 123456, tzinfo=timezone.utc)
    request = _request(
        family="official_regulatory_fiscal",
        required=["official_document"],
        url=url,
    )
    request["retrieved_at_utc"] = "1999-01-01T00:00:00Z"
    request["provenance"] = {"retrieved_at_utc": "1999-01-01T00:00:00Z"}

    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        clock=lambda: retrieved_at,
        http_get=lambda *_args: _response(url, body),
    )(request)

    assert packet["status"] == "PASS"
    assert packet["provenance"]["retrieved_at_utc"] == "2026-08-08T12:00:01.123456Z"
    assert packet["provenance"]["retrieved_at_utc"] != AS_OF
    assert packet["provenance"]["evaluation_as_of_utc"] == AS_OF
    document = packet["official_source_documents"][0]
    assert document["published_at_utc"] == "2026-08-07T18:30:00Z"


def test_naive_retrieval_clock_fails_closed():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({"publication_date": "2026-08-08"}).encode()

    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        clock=lambda: datetime(2026, 8, 8, 12, 0, 1),
        http_get=lambda *_args: _response(url, body),
    )(_request(
        family="official_regulatory_fiscal",
        required=["official_document"],
        url=url,
    ))

    assert packet["status"] == "BLOCKED"
    assert "official_source_retrieval_time_timezone_required" in packet["blockers"]
    assert packet["provenance"]["retrieved_at_utc"] is None
    assert packet["provenance"]["evaluation_as_of_utc"] == AS_OF


def test_naive_evaluation_cutoff_is_rejected():
    try:
        BoundedOfficialPrimaryEvidenceLoader(
            evaluation_as_of_utc="2026-08-08T12:00:00"
        )
    except ValueError as exc:
        assert str(exc) == "official_source_evaluation_time_timezone_required"
    else:
        raise AssertionError("timezone-naive evaluation cutoff was accepted")


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
    document = packet["official_source_documents"][0]
    assert document["discovery_only_source_index"] is True
    assert document["public_claim_allowed"] is False
    assert document["source_index_grants_event_fact_or_numeric_authority"] is False


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

    company_packet = loader(_request(
        family="company_primary",
        required=["company_filing_or_release"],
        url="https://arbitrary-company.example/blog/release",
    ))
    assert company_packet["status"] == "BLOCKED"
    assert "official_source_url_family_binding_invalid" in company_packet["blockers"]
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


def test_default_transport_forbids_cross_authority_redirect_even_within_family(monkeypatch):
    def fake_build_opener(handler):
        redirect_handler = handler()

        class FakeOpener:
            def open(self, request, timeout):
                redirect_handler.redirect_request(
                    request,
                    None,
                    302,
                    "Found",
                    {},
                    "https://www.bls.gov/news.release/empsit.nr0.htm",
                )

        return FakeOpener()

    monkeypatch.setattr(loader_module.urllib.request, "build_opener", fake_build_opener)
    with pytest.raises(
        ValueError, match="official_source_cross_authority_redirect_forbidden"
    ):
        _default_http_get(
            "https://www.eia.gov/dnav/ng/ng_stor_wkly_s1_w.htm",
            12.0,
            1_000_000,
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


def test_bound_url_is_preferred_without_locator_call():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({"publication_date": "2026-08-08"}).encode()
    locator_calls = []
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        source_locator=lambda request: locator_calls.append(request),
        http_get=lambda *_args: _response(url, body),
    )(_request(
        family="official_regulatory_fiscal",
        required=["official_document"],
        url=url,
    ))

    assert packet["status"] == "PASS"
    assert locator_calls == []
    assert packet["provenance"]["locator_request_count"] == 0
    assert packet["provenance"]["official_evidence_get_count"] == 1


def test_missing_bound_url_locates_then_gets_exact_official_document_with_bindings():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({
        "publication_date": "2026-08-08",
        "effective_on": "2026-08-09",
        "agencies": [{"name": "Official Agency"}],
    }).encode()
    calls = []
    times = iter([
        datetime(2026, 8, 8, 12, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 8, 12, 2, tzinfo=timezone.utc),
    ])
    request = _request(
        family="official_regulatory_fiscal",
        required=["official_document", "implementation_timeline", "affected_entities"],
        url=url,
    )
    request["story_context"]["official_source_urls"] = []
    request["story_context"]["official_source_url_bindings"] = []
    request["story_context"]["entities_topics"] = ["Official Agency", "Final Rule"]

    def get(requested, *_args):
        calls.append(requested)
        if "documents.json" in requested:
            return _response(requested, json.dumps({"results": [{
                "json_url": url,
                "publication_date": "2026-08-08",
                "title": "Official Agency Final Rule",
                "agencies": [{"name": "Official Agency"}],
            }]}).encode())
        return _response(url, body)

    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        clock=lambda: next(times),
        http_get=get,
    )(request)

    assert packet["status"] == "PASS"
    assert len(calls) == 2
    assert packet["provenance"]["request_count"] == 2
    assert packet["provenance"]["locator_request_count"] == 1
    assert packet["provenance"]["official_evidence_get_count"] == 1
    locator = packet["provenance"]["locator"]
    assert locator["retrieved_at_utc"] == "2026-08-08T12:01:00Z"
    assert locator["evaluation_as_of_utc"] == AS_OF
    assert locator["candidate_official_url"] == url
    assert locator["discovery_only"] is True
    assert locator["evidence_capabilities"] == []
    assert packet["provenance"]["retrieved_at_utc"] == "2026-08-08T12:02:00Z"
    assert packet["official_source_documents"][0]["source_headline_id"] == "headline-1"
    assert packet["rolling_x_story_binding"] == {
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "request_logical_hash": "a" * 64,
    }


def test_locator_candidate_is_discovery_only_and_nonofficial_candidate_is_rejected():
    request = _request(
        family="official_macro",
        required=["official_release"],
        url="https://www.bls.gov/news.release/empsit.nr0.htm",
    )
    request["story_context"]["official_source_url_bindings"] = []
    calls = []
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        source_locator=lambda _request: {
            "status": "PASS",
            "candidate_official_url": "https://example.com/fabricated",
            "evidence_capabilities": ["official_release"],
        },
        http_get=lambda *_args: calls.append(_args),
    )(request)

    assert packet["status"] == "BLOCKED"
    assert packet["provided_evidence_capabilities"] == []
    assert "official_source_url_family_binding_invalid" in packet["blockers"]
    assert calls == []


def test_locator_candidate_still_requires_successful_evidence_get():
    url = "https://www.bls.gov/news.release/empsit.nr0.htm"
    request = _request(family="official_macro", required=["official_release"], url=url)
    request["story_context"]["official_source_url_bindings"] = []
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        source_locator=lambda _request: {
            "status": "PASS",
            "candidate_official_url": url,
            "discovery_only": True,
            "evidence_capabilities": [],
        },
        http_get=lambda *_args: _response(url, b"not evidence", "text/plain"),
    )(request)

    assert packet["status"] == "BLOCKED"
    assert packet["provided_evidence_capabilities"] == []
    assert "official_source_published_timestamp_unavailable" in packet["blockers"]


def test_document_published_after_evaluation_cutoff_fails_closed():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({"publication_date": "2026-08-09"}).encode()
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: _response(url, body),
    )(_request(
        family="official_regulatory_fiscal",
        required=["official_document"],
        url=url,
    ))

    assert packet["status"] == "BLOCKED"
    assert "official_source_published_after_evaluation_cutoff" in packet["blockers"]


def test_no_locator_candidate_returns_normal_evidence_block_without_get():
    request = _request(
        family="official_macro",
        required=["official_release"],
        url="https://www.bls.gov/news.release/empsit.nr0.htm",
    )
    request["story_context"]["official_source_url_bindings"] = []
    get_calls = []
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        source_locator=lambda _request: {
            "status": "BLOCKED",
            "blockers": ["official_source_locator_candidate_unavailable"],
        },
        http_get=lambda *_args: get_calls.append(_args),
    )(request)

    assert packet["status"] == "BLOCKED"
    assert "official_source_locator_candidate_unavailable" in packet["blockers"]
    assert "exact_official_source_url_unavailable" in packet["blockers"]
    assert get_calls == []


def test_cycle_request_budget_is_shared_across_rank_fallback_calls():
    requests = []
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=1,
        source_locator=lambda request: requests.append(request) or {
            "status": "BLOCKED",
            "blockers": ["official_source_locator_candidate_unavailable"],
        },
    )
    first = _request(
        family="official_macro",
        required=["official_release"],
        url="https://www.bls.gov/news.release/empsit.nr0.htm",
    )
    second = _request(
        family="official_macro",
        required=["official_release"],
        url="https://www.bls.gov/news.release/cpi.nr0.htm",
    )
    first["story_context"]["official_source_url_bindings"] = []
    second["story_context"]["official_source_url_bindings"] = []

    first_packet = loader(first)
    second_packet = loader(second)

    assert len(requests) == 1
    assert first_packet["provenance"]["request_count"] == 1
    assert "official_source_request_budget_exhausted" in second_packet["blockers"]
    assert second_packet["provenance"]["request_count"] == 1


def test_same_story_mode_recheck_reuses_exact_official_bytes_without_network_read():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps({
        "title": "Final rule",
        "publication_date": "2026-08-08",
        "effective_on": "2026-09-08",
    }).encode()
    calls = []
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda requested, *_args: calls.append(requested)
        or _response(url, body),
    )
    request = _request(
        family="official_regulatory_fiscal",
        required=[],
        url=url,
    )
    request["story_evidence_scope_id"] = "official-story-scope"

    first = loader(request)
    second = loader({**request, "request_logical_hash": "b" * 64})

    assert first["official_source_documents"] == second["official_source_documents"]
    assert calls == [url]
    assert second["rolling_x_story_binding"]["request_logical_hash"] == "b" * 64
    assert second["provenance"]["request_count_for_call"] == 0
    assert second["provenance"]["acquisition_cache_reused"] is True
    assert second["provenance"]["network_reads_avoided_for_call"] == 1
