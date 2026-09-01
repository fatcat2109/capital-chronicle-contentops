from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import urllib.request
import urllib.parse
import urllib.error

import pytest

from live_contentops import public_secondary_evidence_loader_v1 as loader_module
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
    NEWS_RSS_ENDPOINT,
    _default_public_http_get,
    _rss_relevance_score,
)
from live_contentops.browser_rendered_source_recovery_v1 import RETRIEVAL_METHOD


AS_OF = "2026-08-19T10:23:11Z"
RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=QATAR+FOREIGN+MINISTRY+SPOKESPERSON+SAYS+IRANIAN+REQUEST+ICRC+"
    "INVOLVEMENT+IRANIAN+PILOTS+ISSUE&hl=en-US&gl=US&ceid=US%3Aen"
)
GOOGLE_ARTICLE_URL = "https://news.google.com/rss/articles/opaque-discovery-id?oc=5"
SITEMAP_URL = "https://www.aljazeera.com/news-sitemap.xml"
PUBLISHER_URL = (
    "https://www.aljazeera.com/news/2026/8/18/"
    "qatar-rejects-irans-false-claims-about-missing-pilots"
)
AP_SITEMAP_INDEX_URL = "https://apnews.com/news-sitemap.xml"
AP_SITEMAP_CHILD_URL = "https://apnews.com/news-sitemap-content.xml"
AP_PUBLISHER_URL = (
    "https://apnews.com/article/"
    "china-evergrande-founder-real-estate-fraud-5573868904b3ced0c5c9b0314c56ae5a"
)


def _request():
    return {
        "cluster_id": "cluster-qatar-pilots",
        "headline_ids": ["headline-qatar-pilots"],
        "request_logical_hash": "a" * 64,
        "story_type": "general_public_event",
        "requested_article_mode": "BREAKING_BRIEF",
        "effective_article_mode": "BREAKING_BRIEF",
        "required_evidence_capabilities": [
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "story_context": {
            "leaf_summaries": [
                "QATAR FOREIGN MINISTRY SPOKESPERSON SAYS IRANIAN REQUEST FOR ICRC "
                "INVOLVEMENT IN IRANIAN PILOTS ISSUE IS A MEDIA PLOY"
            ],
            "grounded_research_queries": [
                "QATAR FOREIGN MINISTRY SPOKESPERSON SAYS IRANIAN REQUEST FOR ICRC "
                "INVOLVEMENT IN IRANIAN PILOTS ISSUE"
            ],
        },
    }


def _response(url: str, body: bytes, content_type: str):
    return {
        "status": 200,
        "final_url": url,
        "headers": {"content-type": content_type},
        "body": body,
        "content_truncated": False,
    }


def _rendered_response(url: str) -> dict:
    markdown = """# Bond Investors Wary After Warsh Speech Fuels Rate-Hike Bets

Bloomberg reports that bond investors at ABN AMRO Investment Solutions and Brandywine
Global Investment Management are skeptical about speculation that Federal Reserve Chair
Kevin Warsh is poised to raise interest rates. The rendered publisher article describes
the disagreement, the market pricing, and the policy-sensitive Treasury move in enough
detail to support a narrow attributed report while the broader interpretation remains
subject to the existing claim and epistemic validators.
""".strip()
    canonical = " ".join(markdown.replace("# ", "", 1).split())
    return {
        "schema_version": "contentops.browser_rendered_source_recovery.v1",
        "status": "PASS",
        "requested_url": url,
        "final_url": url,
        "source_identity": "www.bloomberg.com",
        "title": "Bond Investors Wary After Warsh Speech Fuels Rate-Hike Bets",
        "rendered_markdown": markdown,
        "canonical_content_text": canonical,
        "rendered_page_sha256": sha256(markdown.encode()).hexdigest(),
        "canonical_content_sha256": sha256(canonical.encode()).hexdigest(),
        "byte_length": len(markdown.encode()),
        "content_truncated": False,
        "retrieval_method": RETRIEVAL_METHOD,
        "observed_at_utc": "2026-08-19T10:20:00Z",
        "semantic_scope": "article",
        "browser_runtime": {
            "server_name": "browseros-neo",
            "server_version": "0.0.test",
            "mcp_protocol_version": "2025-06-18",
        },
        "tool_policy": {
            "allowed_tools_used": ["name_session", "tabs", "read"],
            "act_tool_used": False,
            "evaluate_tool_used": False,
            "upload_tool_used": False,
            "download_tool_used": False,
        },
        "persistent_browser_profile_used": True,
        "browser_authentication_state": "NOT_INSPECTED",
        "login_or_consent_interaction_performed": False,
        "credential_or_session_material_read": False,
        "paywall_or_access_control_bypass": False,
        "model_call_count": 0,
        "public_write_performed": False,
        "publication_authority": False,
        "factual_authority_granted_by_browser": False,
        "numeric_authority_granted": False,
    }


def test_exact_bound_403_recovers_through_distinct_browser_rendered_provenance():
    url = "https://www.bloomberg.com/news/articles/2026-08-18/example-story"
    http_calls: list[str] = []
    browser_calls: list[str] = []

    def http_get(requested_url: str, _timeout: float, _maximum: int):
        http_calls.append(requested_url)
        raise urllib.error.HTTPError(requested_url, 403, "Forbidden", {}, None)

    def rendered_get(requested_url: str, _timeout: float, _maximum: int):
        browser_calls.append(requested_url)
        return _rendered_response(requested_url)

    request = _request()
    request["story_evidence_scope_id"] = "browser-rendered-bloomberg"
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-qatar-pilots",
            "url": url,
            "source_timestamp_utc": "2026-08-18T09:00:00Z",
        }
    ]
    request["story_context"]["report_provenance"] = {
        "explicit_reputable_attribution": True,
        "primary_reporting_source_identity": "bloomberg.com",
        "attributed_reputable_sources": [
            {"normalized_host": "bloomberg.com"}
        ],
    }

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=3,
        max_requests_per_candidate=3,
        http_get=http_get,
        rendered_source_get=rendered_get,
        clock=lambda: datetime(2026, 8, 19, 10, 20, tzinfo=timezone.utc),
    )(request)

    assert result["status"] == "PASS"
    assert http_calls == browser_calls == [url]
    assert result["provenance"]["request_count_for_call"] == 2
    assert result["provenance"]["browser_rendered_recovery_attempt_count"] == 1
    assert result["provenance"]["browser_rendered_recovery_success_count"] == 1
    assert result["provenance"]["browser_rendered_recovery_triggers"] == [
        "HTTP Error 403: Forbidden"
    ]
    assert result["provenance"]["browser_rendered_acquisitions_share_request_ledger"] is True
    assert result["provenance"]["browser_rendered_acquisitions_are_raw_http_bytes"] is False
    assert result["provenance"]["browser_rendered_model_call_count"] == 0
    assert result["provenance"]["browser_rendered_public_write_count"] == 0
    document = result["evidence_documents"][0]
    assert document["retrieval_method"] == RETRIEVAL_METHOD
    assert document["canonical_resolution_status"] == (
        "DIRECT_PUBLISHER_URL_BROWSER_RENDERED"
    )
    assert document["published_at_source"] == "EXACT_BOUND_DISCOVERY_TIMESTAMP"
    assert document["browser_rendered_acquisition"]["browser_grants_factual_authority"] is False
    assert document["browser_rendered_acquisition"]["model_call_count"] == 0
    assert document["public_claim_allowed"] is True


def test_401_authentication_failure_never_invokes_browser_recovery():
    url = "https://www.bloomberg.com/news/articles/2026-08-18/private-story"
    browser_calls: list[str] = []

    def http_get(requested_url: str, _timeout: float, _maximum: int):
        raise urllib.error.HTTPError(requested_url, 401, "Unauthorized", {}, None)

    def rendered_get(requested_url: str, _timeout: float, _maximum: int):
        browser_calls.append(requested_url)
        return _rendered_response(requested_url)

    request = _request()
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-qatar-pilots",
            "url": url,
            "source_timestamp_utc": "2026-08-18T09:00:00Z",
        }
    ]

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=2,
        max_requests_per_candidate=2,
        http_get=http_get,
        rendered_source_get=rendered_get,
    )(request)

    assert result["status"] == "BLOCKED"
    assert browser_calls == []
    assert result["provenance"]["browser_rendered_recovery_attempt_count"] == 0
    assert "HTTP Error 401: Unauthorized" in result["blockers"]


def test_http_200_javascript_shell_recovers_rendered_article_text():
    url = "https://www.bloomberg.com/news/articles/2026-08-18/js-shell-story"
    browser_calls: list[str] = []

    def http_get(requested_url: str, _timeout: float, _maximum: int):
        return _response(
            requested_url,
            b"<html><body><script>hydrate()</script><div id='root'></div></body></html>",
            "text/html",
        )

    def rendered_get(requested_url: str, _timeout: float, _maximum: int):
        browser_calls.append(requested_url)
        return _rendered_response(requested_url)

    request = _request()
    request["story_evidence_scope_id"] = "browser-rendered-js-shell"
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-qatar-pilots",
            "url": url,
            "source_timestamp_utc": "2026-08-18T09:00:00Z",
        }
    ]
    request["story_context"]["report_provenance"] = {
        "explicit_reputable_attribution": True,
        "primary_reporting_source_identity": "bloomberg.com",
        "attributed_reputable_sources": [{"normalized_host": "bloomberg.com"}],
    }

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=3,
        max_requests_per_candidate=3,
        http_get=http_get,
        rendered_source_get=rendered_get,
    )(request)

    assert result["status"] == "PASS"
    assert browser_calls == [url]
    assert result["provenance"]["browser_rendered_recovery_triggers"] == [
        "public_source_relevant_text_unavailable"
    ]
    assert result["evidence_documents"][0]["retrieval_method"] == RETRIEVAL_METHOD


def test_browser_response_claiming_public_write_is_rejected():
    url = "https://www.bloomberg.com/news/articles/2026-08-18/unsafe-story"

    def http_get(requested_url: str, _timeout: float, _maximum: int):
        raise urllib.error.HTTPError(requested_url, 403, "Forbidden", {}, None)

    def rendered_get(requested_url: str, _timeout: float, _maximum: int):
        response = _rendered_response(requested_url)
        response["public_write_performed"] = True
        return response

    request = _request()
    request["story_evidence_scope_id"] = "browser-rendered-unsafe"
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-qatar-pilots",
            "url": url,
            "source_timestamp_utc": "2026-08-18T09:00:00Z",
        }
    ]

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=2,
        max_requests_per_candidate=2,
        http_get=http_get,
        rendered_source_get=rendered_get,
    )(request)

    assert result["status"] == "BLOCKED"
    assert result["evidence_documents"] == []
    assert result["provenance"]["browser_rendered_recovery_attempt_count"] == 1
    assert result["provenance"]["browser_rendered_recovery_success_count"] == 0
    assert result["provenance"]["browser_rendered_recovery_diagnostics"] == [
        "browser_rendered_safety_boundary_invalid"
    ]


def test_short_exact_publisher_title_is_not_rejected_by_long_query_denominator():
    query = [
        "QATAR",
        "FOREIGN",
        "MINISTRY",
        "SPOKESPERSON",
        "SAYS",
        "IRANIAN",
        "REQUEST",
        "ICRC",
        "INVOLVEMENT",
        "PILOTS",
        "ISSUE",
    ]

    score = _rss_relevance_score(
        query, "Qatar rejects Iran's false claims about missing pilots"
    )

    assert score >= 0.34


def test_discovery_listing_resolves_same_publisher_sitemap_then_exact_article_bytes():
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss><channel><item>
      <title>Qatar rejects Iran's false claims about missing pilots - Al Jazeera</title>
      <link>{GOOGLE_ARTICLE_URL}</link>
      <pubDate>Tue, 18 Aug 2026 12:42:08 GMT</pubDate>
      <source url="https://www.aljazeera.com">Al Jazeera</source>
    </item></channel></rss>""".encode()
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
      <url><loc>{PUBLISHER_URL}</loc><news:news>
        <news:publication_date>2026-08-18T12:39:43+00:00</news:publication_date>
        <news:title>Qatar rejects Iran's false claims about missing pilots</news:title>
      </news:news></url>
    </urlset>""".encode()
    article = b"""<html><head>
      <meta data-rh="true" name="publishedDate" content="2026-08-18T12:39:43"/>
      <meta property="og:title" content="Qatar rejects Iran's false claims about missing pilots"/>
      </head><body><main>
      Qatar rejected claims about missing pilots. The foreign ministry spokesperson said the
      request for International Committee of the Red Cross involvement was a media ploy.
      This publisher article contains enough directly retrieved factual text for the ordinary
      evidence-depth boundary and remains bound to the exact publisher URL and bytes.
      </main></body></html>"""
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search?"):
            return _response(url, rss, "application/xml")
        if url == SITEMAP_URL:
            return _response(url, sitemap, "application/xml")
        if url == PUBLISHER_URL:
            return _response(url, article, "text/html")
        raise AssertionError(f"unexpected URL: {url}")

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        clock=lambda: datetime(2026, 8, 19, 10, 20, tzinfo=timezone.utc),
    )(_request())

    assert result["status"] == "PASS"
    assert len(result["evidence_documents"]) == 1
    document = result["evidence_documents"][0]
    assert document["source_url"] == PUBLISHER_URL
    assert document["reader_source_url"] == PUBLISHER_URL
    assert document["published_at_utc"] == "2026-08-18T12:39:43Z"
    assert document["published_at_source"] == "PUBLISHER_BYTES_OR_HEADERS"
    assert document["canonical_resolution_status"] == (
        "RESOLVED_FROM_PUBLISHER_NEWS_SITEMAP"
    )
    assert document["discovery_path_url"] == GOOGLE_ARTICLE_URL
    assert document["discovery_path_is_reader_authority"] is False
    assert document["canonical_content_sha256"]
    assert calls == [RSS_URL, SITEMAP_URL, PUBLISHER_URL]
    provenance = result["provenance"]
    assert provenance["request_count_for_candidate"] == 3
    assert provenance["locator_candidate_count"] == 1
    assert provenance["publisher_resolution_attempt_count"] == 1
    assert provenance["paywall_or_access_control_bypass"] is False


def test_unresolved_discovery_listing_never_becomes_factual_authority():
    rss = f"""<rss><channel><item>
      <title>Costco will offer Medicare plans - WSJ</title>
      <link>{GOOGLE_ARTICLE_URL}</link>
      <pubDate>Tue, 18 Aug 2026 09:30:00 GMT</pubDate>
      <source url="https://www.wsj.com">WSJ</source>
    </item></channel></rss>""".encode()

    def http_get(url: str, _timeout: float, _maximum: int):
        if url.startswith("https://news.google.com/rss/search?"):
            return _response(url, rss, "application/xml")
        if url == "https://www.wsj.com/news-sitemap.xml":
            return _response(url, b"<urlset/>", "application/xml")
        if url == GOOGLE_ARTICLE_URL:
            return _response(url, b"<html>discovery listing only</html>", "text/html")
        raise AssertionError(f"unexpected URL: {url}")

    request = _request()
    request["story_context"]["grounded_research_queries"] = [
        "Costco Medicare plans"
    ]
    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
    )(request)

    assert result["status"] == "BLOCKED"
    assert result["evidence_documents"] == []
    assert result["provenance"]["locator_only_record_count"] == 1
    assert result["locator_only_records"][0]["public_claim_allowed"] is False
    assert result["locator_only_records"][0]["canonical_resolution_status"] == (
        "PUBLISHER_URL_UNRESOLVED_ATTRIBUTION_ONLY"
    )


def test_recent_failed_exact_route_is_reused_across_candidates_without_host_wide_suppression():
    calls: list[str] = []

    def first_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        return {"status": 403, "final_url": url, "headers": {}, "body": b""}

    first = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=first_get,
        clock=lambda: datetime(2026, 8, 19, 10, 20, tzinfo=timezone.utc),
    )
    failed_url = "https://www.reuters.com/world/exact-failed-route"
    assert first._get(failed_url)["status"] == 403
    snapshot = first.source_route_health_snapshot()

    second_calls: list[str] = []

    def second_get(url: str, _timeout: float, _maximum: int):
        second_calls.append(url)
        return _response(url, b"ok", "text/plain")

    second = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=second_get,
        clock=lambda: datetime(2026, 8, 19, 10, 21, tzinfo=timezone.utc),
        source_route_health=snapshot,
    )
    with pytest.raises(RuntimeError, match="route_suppressed_by_recent_health"):
        second._get(failed_url)
    recovery_url = "https://www.reuters.com/world/distinct-same-publisher-route"
    assert second._get(recovery_url)["status"] == 200
    assert calls == [failed_url]
    assert second_calls == [recovery_url]
    assert snapshot["routing_only"] is True
    assert snapshot["sourceability_or_health_grants_factual_authority"] is False


def test_recent_failed_exact_route_can_trigger_browser_recovery_without_erasing_health():
    failed_url = "https://www.bloomberg.com/news/articles/exact-failed-browser-route"
    first = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda url, *_args: {
            "status": 403,
            "final_url": url,
            "headers": {},
            "body": b"",
        },
        clock=lambda: datetime(2026, 8, 19, 10, 20, tzinfo=timezone.utc),
    )
    assert first._get(failed_url)["status"] == 403
    snapshot = first.source_route_health_snapshot()
    browser_calls: list[str] = []

    def rendered_get(url: str, _timeout: float, _maximum: int):
        browser_calls.append(url)
        return _rendered_response(url)

    request = _request()
    request["story_evidence_scope_id"] = "browser-route-health-suppression"
    request["story_context"]["public_source_url_bindings"] = [
        {
            "headline_id": "headline-qatar-pilots",
            "url": failed_url,
            "source_timestamp_utc": "2026-08-18T09:00:00Z",
        }
    ]
    request["story_context"]["report_provenance"] = {
        "explicit_reputable_attribution": True,
        "primary_reporting_source_identity": "bloomberg.com",
        "attributed_reputable_sources": [{"normalized_host": "bloomberg.com"}],
    }
    second = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=1,
        max_requests_per_candidate=1,
        http_get=lambda *_args: pytest.fail("suppressed HTTP route must not be retried"),
        rendered_source_get=rendered_get,
        source_route_health=snapshot,
        clock=lambda: datetime(2026, 8, 19, 10, 21, tzinfo=timezone.utc),
    )

    result = second(request)

    assert result["status"] == "PASS"
    assert browser_calls == [failed_url]
    assert result["provenance"]["request_count_for_call"] == 1
    assert result["provenance"]["browser_rendered_recovery_triggers"] == [
        "public_source_route_suppressed_by_recent_health"
    ]
    assert result["provenance"]["browser_rendered_recovery_success_count"] == 1
    health = second.source_route_health_snapshot()
    assert health["routes"][0]["failure_count"] == 1
    assert health["routes"][0]["success_count"] == 0


def test_public_transport_rejects_unsafe_cross_publisher_redirect(monkeypatch):
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
                    "https://www.reuters.com/world/different-publisher",
                )

        return FakeOpener()

    monkeypatch.setattr(loader_module.urllib.request, "build_opener", fake_build_opener)
    monkeypatch.setattr(
        loader_module,
        "_public_host",
        lambda url, **_kwargs: urllib.parse.urlsplit(url).hostname,
    )
    with pytest.raises(ValueError, match="public_source_redirect_authority_invalid"):
        _default_public_http_get(
            "https://www.apnews.com/article/exact-story", 12.0, 800_000
        )


def test_registered_cnbc_short_link_may_canonicalize_only_to_cnbc(monkeypatch):
    redirects: list[str] = []

    def fake_build_opener(handler):
        redirect_handler = handler()

        class FakeResponse:
            status = 200
            headers = {"content-type": "text/html"}

            def read(self, _size):
                return b"<html><body>publisher bytes</body></html>"

            def geturl(self):
                return "https://www.cnbc.com/2026/08/22/exact-story.html"

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

        class FakeOpener:
            def open(self, request, timeout):
                redirected = "https://www.cnbc.com/2026/08/22/exact-story.html"
                redirects.append(redirected)
                redirect_handler.redirect_request(
                    request, None, 302, "Found", {}, redirected
                )
                return FakeResponse()

        return FakeOpener()

    monkeypatch.setattr(loader_module.urllib.request, "build_opener", fake_build_opener)
    monkeypatch.setattr(
        loader_module,
        "_public_host",
        lambda url, **_kwargs: urllib.parse.urlsplit(url).hostname,
    )

    response = _default_public_http_get("https://cnb.cx/registered-short", 12.0, 800_000)

    assert response["status"] == 200
    assert response["final_url"].startswith("https://www.cnbc.com/")
    assert redirects == ["https://www.cnbc.com/2026/08/22/exact-story.html"]


def test_registered_cnbc_short_link_cannot_retarget_another_publisher(monkeypatch):
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
                    "https://www.reuters.com/world/different-publisher",
                )

        return FakeOpener()

    monkeypatch.setattr(loader_module.urllib.request, "build_opener", fake_build_opener)
    monkeypatch.setattr(
        loader_module,
        "_public_host",
        lambda url, **_kwargs: urllib.parse.urlsplit(url).hostname,
    )
    with pytest.raises(ValueError, match="public_source_redirect_authority_invalid"):
        _default_public_http_get("https://cnb.cx/registered-short", 12.0, 800_000)


def test_publisher_sitemap_cannot_retarget_listing_to_another_host():
    rss = f"""<rss><channel><item>
      <title>Qatar rejects Iran's false claims about missing pilots - Al Jazeera</title>
      <link>{GOOGLE_ARTICLE_URL}</link>
      <pubDate>Tue, 18 Aug 2026 12:42:08 GMT</pubDate>
      <source url="https://www.aljazeera.com">Al Jazeera</source>
    </item></channel></rss>""".encode()
    sitemap = b"""<urlset><url>
      <loc>https://example.com/retargeted-article</loc>
      <publication_date>2026-08-18T12:39:43Z</publication_date>
      <title>Qatar rejects Iran's false claims about missing pilots</title>
    </url></urlset>"""
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search?"):
            return _response(url, rss, "application/xml")
        if url == SITEMAP_URL:
            return _response(url, sitemap, "application/xml")
        if url == GOOGLE_ARTICLE_URL:
            return _response(url, b"<html>discovery listing only</html>", "text/html")
        raise AssertionError(f"unexpected URL: {url}")

    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
    )(_request())

    assert result["status"] == "BLOCKED"
    assert result["evidence_documents"] == []
    assert not any("example.com" in value for value in calls)


def test_authorized_ap_news_listing_resolves_through_one_same_host_sitemap_index_child():
    rss = f"""<rss><channel><item>
      <title>Chinese court sentences founder of troubled property developer Evergrande to life in prison - AP News</title>
      <link>{GOOGLE_ARTICLE_URL}</link>
      <pubDate>Thu, 20 Aug 2026 11:31:00 GMT</pubDate>
      <source url="https://apnews.com">AP News</source>
    </item></channel></rss>""".encode()
    sitemap_index = f"""<sitemapindex>
      <sitemap><loc>{AP_SITEMAP_CHILD_URL}</loc></sitemap>
      <sitemap><loc>https://example.com/forbidden-cross-host.xml</loc></sitemap>
    </sitemapindex>""".encode()
    sitemap_child = f"""<urlset><url>
      <loc>{AP_PUBLISHER_URL}</loc>
      <publication_date>2026-08-20T00:21:25-04:00</publication_date>
      <title>Founder of embattled Chinese real estate company Evergrande gets life in prison</title>
    </url></urlset>""".encode()
    article = b"""<html><head>
      <meta property="article:published_time" content="2026-08-20T00:21:25-04:00"/>
      <meta property="og:title" content="Chinese court sentences founder of troubled property developer Evergrande to life in prison"/>
      </head><body><main>
      A Chinese court sentenced the founder of troubled property developer Evergrande
      to life in prison. This exact publisher article contains sufficient directly
      retrieved factual text and remains bound to the publisher URL and source bytes.
      </main></body></html>"""
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search?"):
            return _response(url, rss, "application/xml")
        if url == AP_SITEMAP_INDEX_URL:
            return _response(url, sitemap_index, "application/xml")
        if url == AP_SITEMAP_CHILD_URL:
            return _response(url, sitemap_child, "application/xml")
        if url == AP_PUBLISHER_URL:
            return _response(url, article, "text/html")
        raise AssertionError(f"unexpected URL: {url}")

    request = _request()
    request["story_context"]["grounded_research_queries"] = [
        "Xu Jiayin founder China Evergrande sentenced life prison"
    ]
    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-20T23:37:06.897041Z",
        http_get=http_get,
    )(request)

    assert result["status"] == "PASS"
    document = result["evidence_documents"][0]
    assert document["source_url"] == AP_PUBLISHER_URL
    assert document["published_at_utc"] == "2026-08-20T04:21:25Z"
    assert document["canonical_resolution_status"] == (
        "RESOLVED_FROM_PUBLISHER_NEWS_SITEMAP"
    )
    assert [row["url"] for row in document["publisher_locator_chain"]] == [
        AP_SITEMAP_INDEX_URL,
        AP_SITEMAP_CHILD_URL,
    ]
    assert calls == [
        RSS_URL.replace(
            "QATAR+FOREIGN+MINISTRY+SPOKESPERSON+SAYS+IRANIAN+REQUEST+ICRC+INVOLVEMENT+IRANIAN+PILOTS+ISSUE",
            "Xu+Jiayin+founder+China+Evergrande+sentenced+life+prison",
        ),
        AP_SITEMAP_INDEX_URL,
        AP_SITEMAP_CHILD_URL,
        AP_PUBLISHER_URL,
    ]


def test_missing_news_sitemap_uses_same_host_robots_declared_sitemap_safely():
    publisher_url = "https://www.cnbc.com/2026/08/23/trump-june-stock-trades.html"
    declared_sitemap = "https://www.cnbc.com/sitemaps/latest-news.xml"
    rss = f"""<rss><channel><item>
      <title>Trump disclosure shows more than 1,000 June stock trades - CNBC</title>
      <link>{GOOGLE_ARTICLE_URL}</link>
      <pubDate>Sun, 23 Aug 2026 15:30:00 GMT</pubDate>
      <source url="https://www.cnbc.com">CNBC</source>
    </item></channel></rss>""".encode()
    robots = (
        "User-agent: *\n"
        "Sitemap: https://example.com/forbidden-cross-host.xml\n"
        f"Sitemap: {declared_sitemap}\n"
    ).encode()
    sitemap = f"""<urlset><url>
      <loc>{publisher_url}</loc>
      <publication_date>2026-08-23T15:25:00Z</publication_date>
      <title>Trump disclosure shows more than 1,000 June stock trades</title>
    </url></urlset>""".encode()
    article = b"""<html><head>
      <meta property="article:published_time" content="2026-08-23T15:25:00Z"/>
      <meta property="og:title" content="Trump disclosure shows more than 1,000 June stock trades"/>
      </head><body><main>
      A newly filed disclosure shows more than one thousand stock trades during June.
      This exact publisher article contains sufficient directly retrieved reporting text,
      remains bound to CNBC publisher bytes, and supplies no authority from the locator.
      </main></body></html>"""
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        if url.startswith("https://news.google.com/rss/search?"):
            return _response(url, rss, "application/xml")
        if url == "https://www.cnbc.com/news-sitemap.xml":
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if url == "https://www.cnbc.com/robots.txt":
            return _response(url, robots, "text/plain")
        if url == declared_sitemap:
            return _response(url, sitemap, "application/xml")
        if url == publisher_url:
            return _response(url, article, "text/html")
        raise AssertionError(f"unexpected URL: {url}")

    request = _request()
    request["story_context"]["grounded_research_queries"] = [
        "Trump disclosure 1000 June stock trades"
    ]
    result = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-23T22:41:06Z",
        http_get=http_get,
        max_requests_per_candidate=8,
    )(request)

    assert result["status"] == "PASS"
    document = result["evidence_documents"][0]
    assert document["source_url"] == publisher_url
    assert document["canonical_resolution_status"] == (
        "RESOLVED_FROM_PUBLISHER_DECLARED_SITEMAP"
    )
    assert [row["url"] for row in document["publisher_locator_chain"]] == [
        "https://www.cnbc.com/robots.txt",
        declared_sitemap,
    ]
    assert not any("example.com" in url for url in calls)
    assert calls == [
        next(url for url in calls if url.startswith(NEWS_RSS_ENDPOINT)),
        "https://www.cnbc.com/news-sitemap.xml",
        "https://www.cnbc.com/robots.txt",
        declared_sitemap,
        publisher_url,
    ]
    assert result["provenance"]["publisher_resolution_diagnostics"] == [
        "HTTP Error 404: Not Found"
    ]


def test_story_scope_cannot_reset_per_candidate_allowance_and_other_story_is_isolated():
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        body = (
            b"<html><head><meta property='article:published_time' "
            b"content='2026-08-18T12:39:43Z'/></head><body>"
            + b"Bound public evidence text. " * 20
            + b"</body></html>"
        )
        return _response(url, body, "text/html")

    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=4,
        max_requests_per_candidate=1,
        http_get=http_get,
    )
    first = _request()
    first["story_evidence_scope_id"] = "story-scope-one"
    first["story_context"]["public_source_url_bindings"] = [{
        "headline_id": "headline-qatar-pilots",
        "url": "https://www.reuters.com/world/first-story",
    }]
    first_result = loader(first)
    assert first_result["status"] == "PASS"

    same_story = _request()
    same_story["story_evidence_scope_id"] = "story-scope-one"
    same_story["story_context"]["public_source_url_bindings"] = [{
        "headline_id": "headline-qatar-pilots",
        "url": "https://apnews.com/article/delta-source",
    }]
    same_result = loader(same_story)
    assert same_result["status"] == "BLOCKED"
    assert same_result["provenance"]["request_count_for_candidate"] == 1
    assert same_result["provenance"]["request_count_for_call"] == 0
    assert same_result["provenance"]["candidate_request_boundary_reused"] is True
    assert "public_source_candidate_request_budget_exhausted" in same_result["blockers"]

    different_story = _request()
    different_story["story_evidence_scope_id"] = "story-scope-two"
    different_story["story_context"]["public_source_url_bindings"] = [{
        "headline_id": "headline-qatar-pilots",
        "url": "https://apnews.com/article/other-story",
    }]
    other_result = loader(different_story)
    assert other_result["status"] == "PASS"
    assert other_result["provenance"]["request_count_for_candidate"] == 1
    assert other_result["provenance"]["request_count_for_call"] == 1
    assert calls == [
        "https://www.reuters.com/world/first-story",
        "https://apnews.com/article/other-story",
    ]


def test_same_story_delta_reuses_identical_request_signature_without_network_read():
    calls: list[str] = []

    def http_get(url: str, _timeout: float, _maximum: int):
        calls.append(url)
        body = (
            b"<html><head><meta property='article:published_time' "
            b"content='2026-08-18T12:39:43Z'/></head><body>"
            + b"Bound public evidence text. " * 20
            + b"</body></html>"
        )
        return _response(url, body, "text/html")

    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        max_requests=4,
        max_requests_per_candidate=2,
        http_get=http_get,
    )
    request = _request()
    request["story_evidence_scope_id"] = "same-story-scope"
    request["story_context"]["public_source_url_bindings"] = [{
        "headline_id": "headline-qatar-pilots",
        "url": "https://www.reuters.com/world/same-story",
    }]

    first = loader(request)
    second = loader({**request, "request_logical_hash": "b" * 64})

    assert first["status"] == second["status"] == "PASS"
    assert calls == [
        "https://www.reuters.com/world/same-story",
        RSS_URL,
    ]
    assert second["provenance"]["request_count_for_call"] == 0
    assert second["provenance"]["request_count_for_candidate"] == 2
    assert second["provenance"]["network_reads_avoided_for_call"] == 2
    assert len(second["provenance"]["reused_request_signatures"]) == 2
