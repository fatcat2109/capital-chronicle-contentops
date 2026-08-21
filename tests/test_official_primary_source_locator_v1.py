from __future__ import annotations

from datetime import datetime, timezone
import json

from live_contentops.official_primary_source_locator_v1 import (
    BoundedOfficialPrimarySourceLocator,
)


def _request(family):
    return {
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "story_type": "data_release",
        "article_mode": "straight_news",
        "source_adapter_families": [family],
        "evaluation_as_of_utc": "2026-08-08T12:00:00Z",
        "story_context": {
            "entities_topics": ["Employment", "United States"],
            "why_now": "Employment Situation release",
            "headline_text": "UNTRUSTED X TEXT",
        },
    }


def _response(url, body):
    return {"status": 200, "final_url": url, "headers": {}, "body": body}


def test_macro_locator_returns_discovery_metadata_without_authority():
    clock = datetime(2026, 8, 8, 12, 1, tzinfo=timezone.utc)
    html = b'<a href="/news.release/empsit.toc.htm">Employment Situation</a>'
    locator = BoundedOfficialPrimarySourceLocator(
        clock=lambda: clock,
        http_get=lambda url, *_args: _response(url, html),
    )

    result = locator(_request("official_macro"))

    assert result["status"] == "PASS"
    assert result["candidate_official_url"] == "https://www.bls.gov/news.release/empsit.nr0.htm"
    assert result["retrieved_at_utc"] == "2026-08-08T12:01:00Z"
    assert result["evaluation_as_of_utc"] == "2026-08-08T12:00:00Z"
    assert len(result["locator_query_logical_hash"]) == 64
    assert len(result["locator_response_sha256"]) == 64
    assert result["discovery_only"] is True
    assert result["factual_authority"] is False
    assert result["evidence_capabilities"] == []
    assert result["publication_authority"] is False


def test_sec_locator_uses_first_party_ticker_index_and_returns_sec_candidate():
    body = json.dumps({"0": {
        "cik_str": 320193,
        "ticker": "AAPL",
        "title": "Apple Inc",
    }}).encode()
    request = _request("sec_regulatory")
    request["story_context"]["entities_topics"] = ["Apple Inc"]
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: _response(url, body),
    )

    result = locator(request)

    assert result["status"] == "PASS"
    assert result["candidate_official_url"] == "https://data.sec.gov/submissions/CIK0000320193.json"


def test_sec_locator_reads_current_bounded_index_shape_beyond_old_500kb_ceiling():
    body = json.dumps(
        {
            "0": {"title": "X" * 600_000},
            "1": {
                "cik_str": 315189,
                "ticker": "DE",
                "title": "Deere & Company",
            },
        }
    ).encode()
    assert 500_000 < len(body) < 1_000_000
    request = _request("company_primary")
    request["story_context"]["entities_topics"] = ["Deere"]

    def http_get(url, _timeout, maximum):
        assert maximum == 1_000_000
        return {**_response(url, body), "content_truncated": False}

    result = BoundedOfficialPrimarySourceLocator(http_get=http_get)(request)

    assert result["status"] == "PASS"
    assert result["candidate_official_url"] == (
        "https://data.sec.gov/submissions/CIK0000315189.json"
    )


def test_sec_locator_prefers_named_entity_over_later_generic_term_tie():
    body = json.dumps(
        {
            "0": {
                "cik_str": 75398,
                "ticker": "PAI",
                "title": "Western Asset Investment Grade Income Fund Inc.",
            },
            "1": {
                "cik_str": 315189,
                "ticker": "DE",
                "title": "Deere & Company",
            },
        }
    ).encode()
    request = _request("company_primary")
    request["story_context"] = {
        "entities_topics": [],
        "leaf_summaries": [
            "DEERE Q3 EARNINGS HIGHLIGHTS Revenue EPS Net Income"
        ],
    }

    result = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: _response(url, body)
    )(request)

    assert result["status"] == "PASS"
    assert result["candidate_official_url"] == (
        "https://data.sec.gov/submissions/CIK0000315189.json"
    )


def test_official_locator_reports_truncation_instead_of_candidate_miss():
    request = _request("company_primary")
    request["story_context"]["entities_topics"] = ["Deere"]
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: {
            **_response(url, b'{"0":'),
            "content_truncated": True,
        }
    )

    result = locator(request)

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["official_source_locator_response_truncated"]


def test_unsupported_family_never_calls_network():
    calls = []
    result = BoundedOfficialPrimarySourceLocator(
        http_get=lambda *_args: calls.append(_args),
    )(_request("licensed_news"))

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["official_source_locator_family_unsupported"]
    assert calls == []


# --- Federal Reserve official_policy discovery (Phase 4) -------------------------


_FED_CALENDAR_HTML = b"""
<html><body>
<a href="/monetarypolicy/fomccalendars.htm">FOMC Calendars</a>
<a href="/newsevents/pressreleases/monetary20260429a.htm">FOMC Statement - April 29, 2026</a>
<a href="/newsevents/pressreleases/monetary20260617a.htm">FOMC Statement - June 17, 2026</a>
<a href="/monetarypolicy/fomcprojtabl20260617.htm">Projections - June 2026</a>
</body></html>
"""


def _policy_request(cutoff="2026-08-08T12:00:00Z"):
    return {
        "cluster_id": "cluster-policy",
        "headline_ids": ["headline-policy"],
        "story_type": "policy_decision",
        "article_mode": "straight_news",
        "source_adapter_families": ["official_policy"],
        "evaluation_as_of_utc": cutoff,
        "story_context": {
            "entities_topics": ["Federal Reserve", "policy decision"],
            "why_now": "FOMC held the target range",
            "headline_text": "UNTRUSTED X TEXT",
        },
    }


def test_policy_locator_uses_fed_calendar_route_and_returns_statement_candidate():
    seen_urls = []

    def http_get(url, *_args):
        seen_urls.append(url)
        return _response(url, _FED_CALENDAR_HTML)

    clock = datetime(2026, 8, 8, 12, 1, tzinfo=timezone.utc)
    locator = BoundedOfficialPrimarySourceLocator(
        clock=lambda: clock, http_get=http_get
    )
    result = locator(_policy_request())

    # The discovery request goes to the official Federal Reserve calendar page only.
    assert seen_urls == ["https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"]
    assert result["status"] == "PASS", result.get("blockers")
    assert result["candidate_official_url"] == (
        "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm"
    )
    # Most recent candidate <= cutoff is the June statement (not April, not the calendar page).
    assert "monetary20260429a.htm" not in result["candidate_official_url"]
    assert "fomccalendars" not in result["candidate_official_url"]


def test_policy_locator_never_selects_a_statement_after_the_cutoff():
    html = b"""
    <html><body>
    <a href="/newsevents/pressreleases/monetary20260905a.htm">FOMC Statement - September 05, 2026</a>
    <a href="/newsevents/pressreleases/monetary20260617a.htm">FOMC Statement - June 17, 2026</a>
    </body></html>
    """
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: _response(url, html)
    )
    result = locator(_policy_request(cutoff="2026-08-01T00:00:00Z"))
    assert result["status"] == "PASS"
    assert result["candidate_official_url"] == (
        "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm"
    )
    assert "monetary20260905a.htm" not in result["candidate_official_url"]


def test_policy_locator_returns_no_candidate_when_no_fomc_links():
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: _response(url, b"<html>no policy links</html>")
    )
    result = locator(_policy_request())
    assert result["status"] == "BLOCKED"
    assert "official_source_locator_candidate_unavailable" in result["blockers"]


def test_policy_locator_output_grants_no_evidence_authority():
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, *_args: _response(url, _FED_CALENDAR_HTML)
    )
    result = locator(_policy_request())
    assert result["status"] == "PASS"
    assert result["discovery_only"] is True
    assert result["factual_authority"] is False
    assert result["evidence_capabilities"] == []
    assert result["publication_authority"] is False
