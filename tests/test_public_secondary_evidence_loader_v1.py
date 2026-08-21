from __future__ import annotations

from datetime import datetime, timezone

from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
    _rss_relevance_score,
)


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
