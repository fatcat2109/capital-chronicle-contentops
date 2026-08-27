from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import urllib.error

from live_contentops.v1_simple_evidence_resolver_v1 import (
    SimpleFirstPartyAwareEvidenceResolver,
)

CUTOFF = "2026-08-27T12:00:00Z"
NOW = datetime(2026, 8, 27, 12, 1, tzinfo=timezone.utc)

BEA_LISTING = "https://www.bea.gov/news/current-releases"
BEA_DOCUMENT = "https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026"
IMF_FEED = "https://www.imf.org/en/news/rss"
IMF_DOCUMENT = (
    "https://www.imf.org/en/news/articles/2026/08/26/"
    "pr26278-chile-imf-executive-board-approves-new-two-year-flexible-credit-line-arrangement"
)
COMPANY_FEED = "https://nvidianews.nvidia.com/cats/press_release.xml"
COMPANY_DOCUMENT = (
    "https://nvidianews.nvidia.com/news/"
    "nvidia-announces-financial-results-for-second-quarter-fiscal-2027/"
)

BEA_LISTING_BYTES = f"""
<html><body><table><tr class="release-row">
<td><a href="/news/2026/personal-income-and-outlays-july-2026">Personal Income and Outlays, July 2026</a></td>
<td><time datetime="2026-08-26T08:30:00-04:00">August 26, 2026</time></td>
</tr></table></body></html>
""".encode()
BEA_DOCUMENT_BYTES = b"""
<html><head><title>Personal Income and Outlays, July 2026</title>
<meta itemprop="datePublished" content="2026-08-26T08:30:00-04:00"></head>
<body><h1>Personal Income and Outlays, July 2026</h1><p>News Release.</p>
<p>The core PCE price index increased 3.3 percent from one year ago.</p></body></html>
"""
IMF_FEED_BYTES = f"""
<rss><channel><item>
<title>IMF Executive Board Approves New Two-Year Flexible Credit Line Arrangement with Chile</title>
<link>{IMF_DOCUMENT}</link><pubDate>Wed, 26 Aug 2026 15:00:00 GMT</pubDate>
</item></channel></rss>
""".encode()
IMF_DOCUMENT_BYTES = b"""
<html><head><title>IMF Executive Board Approves New Two-Year Flexible Credit Line Arrangement with Chile</title>
<meta property="article:published_time" content="2026-08-26T15:00:00Z"></head>
<body><h1>Press Release No. 26/278</h1><p>International Monetary Fund (IMF).</p>
<p>The IMF approved a two-year Flexible Credit Line arrangement with Chile.</p></body></html>
"""
COMPANY_FEED_BYTES = f"""
<rss><channel><item><title>NVIDIA Announces Financial Results for Second Quarter Fiscal 2027</title>
<link>{COMPANY_DOCUMENT.rstrip('/')}</link><pubDate>Wed, 26 Aug 2026 20:00:00 GMT</pubDate>
</item></channel></rss>
""".encode()
COMPANY_DOCUMENT_BYTES = b"""
<html><head><title>NVIDIA Announces Financial Results for Second Quarter Fiscal 2027</title>
<meta property="article:published_time" content="2026-08-26T20:00:00Z"></head>
<body><h1>NVIDIA Announces Financial Results for Second Quarter Fiscal 2027</h1>
<p>Press Release. NVIDIA reported revenue of $96.2 billion for the quarter.</p></body></html>
"""


def _response(url: str, body: bytes, content_type: str = "text/html"):
    return {
        "status": 200,
        "final_url": url,
        "headers": {"content-type": content_type},
        "body": body,
    }


def _request(headline: str, *, remaining: int = 0):
    return {
        "cluster_id": "candidate-test",
        "headline_ids": ["headline-test"],
        "request_logical_hash": "hash-test",
        "story_evidence_scope_id": "candidate-test",
        "story_type": "selected_current_news",
        "remaining_admitted_candidate_count": remaining,
        "required_evidence_capabilities": [
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "story_context": {
            "leaf_summaries": [headline],
            "headline_text": headline,
            "grounded_research_queries": [headline],
            "public_source_url_bindings": [
                {
                    "headline_id": "headline-test",
                    "url": "https://x.com/example/status/1",
                    "source_timestamp_utc": "2026-08-26T20:00:00Z",
                }
            ],
        },
    }


def test_bea_official_macro_locator_then_document_wins_before_secondary():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        assert "news.google.com" not in url
        if url == BEA_LISTING:
            return _response(url, BEA_LISTING_BYTES)
        if url == BEA_DOCUMENT:
            return _response(url, BEA_DOCUMENT_BYTES)
        raise AssertionError(url)

    resolver = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )
    result = resolver(
        _request("US core PCE price index advanced 3.3% in July", remaining=2)
    )

    assert result["status"] == "PASS"
    assert calls == [BEA_LISTING, BEA_DOCUMENT]
    assert result["provenance"]["selected_route"] == "OFFICIAL_PRIMARY"
    assert result["provenance"]["request_count_total"] == 2
    assert result["provenance"]["route_history"][0]["locator_surface_id"] == "bea_current_releases_v1"
    document = result["evidence_documents"][0]
    assert document["source_url"] == BEA_DOCUMENT
    assert document["published_at_utc"] == "2026-08-26T12:30:00Z"
    assert document["canonical_content_sha256"] == sha256(BEA_DOCUMENT_BYTES).hexdigest()


def test_exact_bound_official_document_is_shortest_route_and_skips_locator():
    calls: list[str] = []
    request = _request("US core PCE price index advanced 3.3% in July", remaining=2)
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-test",
            "url": BEA_DOCUMENT,
            "source_timestamp_utc": "2026-08-26T12:30:00Z",
        }
    ]

    def get(url, *_args):
        calls.append(url)
        assert url != BEA_LISTING
        return _response(url, BEA_DOCUMENT_BYTES)

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(request)

    assert result["status"] == "PASS"
    assert calls == [BEA_DOCUMENT]
    assert result["provenance"]["request_count_total"] == 1
    assert result["provenance"]["route_history"][0]["locator_surface_id"] is None


def test_imf_press_release_route_resolves_same_authority_exact_bytes():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url == IMF_FEED:
            return _response(url, IMF_FEED_BYTES, "text/xml")
        if url.rstrip("/") == IMF_DOCUMENT:
            return _response(url, IMF_DOCUMENT_BYTES)
        raise AssertionError(url)

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(_request("IMF executive board approves a new Chile Flexible Credit Line"))

    assert result["status"] == "PASS"
    assert calls == [IMF_FEED, IMF_DOCUMENT]
    assert result["evidence_documents"][0]["publisher"] == "www.imf.org"
    assert result["provenance"]["route_history"][0]["locator_surface_id"] == "imf_press_release_feed_v1"


def test_configured_company_release_feed_resolves_earnings_without_article_hardcode():
    calls: list[str] = []
    request = _request("NVIDIA Q2 fiscal 2027 earnings and financial results")
    assert COMPANY_DOCUMENT not in str(request)

    def get(url, *_args):
        calls.append(url)
        if url == COMPANY_FEED:
            return _response(url, COMPANY_FEED_BYTES, "text/xml")
        if url == COMPANY_DOCUMENT:
            return _response(url, COMPANY_DOCUMENT_BYTES)
        raise AssertionError(url)

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(request)

    assert result["status"] == "PASS"
    assert calls == [COMPANY_FEED, COMPANY_DOCUMENT]
    route = result["provenance"]["route_history"][0]
    assert route["locator_surface_id"] == "company_investor_relations_release_feed_v1"
    assert result["evidence_documents"][0]["source_adapter_family"] == "company_primary"


def test_configured_company_release_abstraction_routes_financing_disclosure_too():
    request = _request(
        "NVIDIA financing platforms to mobilize more than 500 billion of third-party capital"
    )

    def get(url, *_args):
        if url == COMPANY_FEED:
            financing_url = (
                "https://nvidianews.nvidia.com/news/nvidia-partners-establish-"
                "ai-compute-infrastructure-financing-platforms"
            )
            feed = f"""<rss><channel><item>
            <title>NVIDIA Partners Establish AI Compute Infrastructure Financing Platforms</title>
            <link>{financing_url}</link><pubDate>Wed, 26 Aug 2026 19:00:00 GMT</pubDate>
            </item></channel></rss>""".encode()
            return _response(url, feed, "text/xml")
        if "financing-platforms" in url:
            body = b"""<html><head><title>NVIDIA Partners Establish AI Compute Infrastructure Financing Platforms</title>
            <meta property="article:published_time" content="2026-08-26T19:00:00Z"></head>
            <body><p>Press Release. NVIDIA announced financing platforms to mobilize third-party capital.</p></body></html>"""
            return _response(url, body)
        raise AssertionError(url)

    result = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )(request)

    assert result["status"] == "PASS"
    assert result["provenance"]["route_history"][0]["locator_surface_id"] == "company_investor_relations_release_feed_v1"


def test_failed_primary_and_secondary_continue_to_next_candidate_on_same_ledger():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url == IMF_FEED:
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        if url.startswith("https://news.google.com/rss/search"):
            return _response(url, b"<rss><channel></channel></rss>", "text/xml")
        if url == BEA_LISTING:
            return _response(url, BEA_LISTING_BYTES)
        if url == BEA_DOCUMENT:
            return _response(url, BEA_DOCUMENT_BYTES)
        raise AssertionError(url)

    resolver = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )
    first = resolver(
        _request("IMF executive board approves Chile Flexible Credit Line", remaining=1)
    )
    second = resolver(
        _request("US core PCE price index advanced 3.3% in July", remaining=0)
    )

    assert first["status"] == "BLOCKED"
    assert first["provenance"]["request_count_for_call"] == 2
    assert second["status"] == "PASS"
    assert second["provenance"]["request_count_total"] == 4
    assert resolver.request_count == 4 <= 6


def test_locator_bytes_alone_never_satisfy_evidence_and_global_ledger_never_exceeds_six():
    calls: list[str] = []

    def get(url, *_args):
        calls.append(url)
        if url == BEA_LISTING:
            return _response(url, BEA_LISTING_BYTES)
        if url == BEA_DOCUMENT:
            return {"status": 500, "final_url": url, "headers": {}, "body": b""}
        if url.startswith("https://news.google.com/rss/search"):
            return _response(url, b"<rss><channel></channel></rss>", "text/xml")
        raise AssertionError(url)

    resolver = SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=CUTOFF,
        http_get=get,
        clock=lambda: NOW,
    )
    result = resolver(
        _request("US core PCE price index advanced 3.3% in July", remaining=0)
    )

    assert result["status"] == "BLOCKED"
    assert result["evidence_documents"] == []
    assert result["provenance"]["locator_or_search_bytes_are_factual_authority"] is False
    assert resolver.request_count <= 6
    assert any(row["locator_bytes_grant_factual_authority"] is False for row in result["provenance"]["route_history"])
