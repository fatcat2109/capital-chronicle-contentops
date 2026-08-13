from __future__ import annotations

from datetime import datetime, timezone

from live_contentops.claim_evidence_contract_v1 import (
    build_minimum_trustworthy_evidence_packet,
    summarize_evidence_substance,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)


AS_OF = "2026-08-13T12:00:00Z"
DISCOVERY_URL = "https://news.google.com/rss/articles/opaque-current-story"
PUBLISHER_URL = "https://www.reuters.com/world/current-story-2026-08-13/"


def _request() -> dict:
    return {
        "cluster_id": "cluster-current",
        "headline_ids": ["headline-current"],
        "story_type": "company_sector_event",
        "article_mode": "straight_news",
        "effective_article_mode": "FULL_ARTICLE",
        "request_logical_hash": "a" * 64,
        "story_context": {
            "leaf_summaries": [
                "Reuters reports a company opened a new public manufacturing facility"
            ],
            "public_source_url_bindings": [
                {"headline_id": "headline-current", "url": DISCOVERY_URL}
            ],
        },
    }


def _listing_document(*, content: str) -> dict:
    return {
        "document_id": "public-news-listing-1",
        "title": "Company opens a new public manufacturing facility",
        "publisher": "Reuters",
        "source_identity": "reuters.com",
        "source_authority_class": "reputable_secondary_source",
        "source_url": DISCOVERY_URL,
        "published_at_utc": "2026-08-13T09:00:00Z",
        "canonical_content_text": content,
        "secondary_listing_only": True,
        "public_claim_allowed": True,
    }


def test_minimum_eligibility_is_independent_from_article_substance_depth():
    request = _request()
    title = "Company opens a new public manufacturing facility"
    thin = _listing_document(content=title)

    packet = build_minimum_trustworthy_evidence_packet(request, [thin])
    depth = summarize_evidence_substance(request, [thin])

    assert packet["status"] == "PASS"
    assert depth["enough_for_useful_article"] is False
    assert depth["enrichment_recommended"] is True
    assert depth["additional_source_is_eligibility_requirement"] is False


def test_compact_current_event_label_binds_to_full_professional_source_title():
    request = _request()
    request["story_context"]["leaf_summaries"] = ["US CPI July 2026 Report"]
    document = _listing_document(
        content="Here are five key takeaways from the July CPI inflation report"
    )
    document["title"] = "Here are five key takeaways from the July CPI inflation report"

    packet = build_minimum_trustworthy_evidence_packet(request, [document])

    assert packet["status"] == "PASS"
    assert packet["core_factual_proposition"] == document["title"]
    assert packet["attribution_required"] is True


def test_transport_filename_uses_only_locally_supported_compact_event_label():
    request = _request()
    request["story_context"]["leaf_summaries"] = ["US CPI July 2026 Report"]
    document = {
        "document_id": "bls-cpi-current",
        "title": "cpi.pdf",
        "publisher": "Bureau of Labor Statistics",
        "source_identity": "bls.gov",
        "source_authority_class": "official_public_primary_source",
        "source_url": "https://www.bls.gov/news.release/pdf/cpi.pdf",
        "published_at_utc": "2026-08-12T11:08:11Z",
        "canonical_content_text": (
            "Consumer Price Index July 2026 detailed report. CPI data for July are published "
            "in this official news release with definitions and technical notes."
        ),
    }

    packet = build_minimum_trustworthy_evidence_packet(request, [document])

    assert packet["status"] == "PASS"
    assert packet["source_title"] == "cpi.pdf"
    assert packet["core_factual_proposition"] == "US CPI July 2026 Report"


def test_discovery_redirect_resolves_one_canonical_publisher_source_and_stops():
    calls = []
    article_text = " ".join(
        [
            "The company opened a manufacturing facility after completing construction and "
            "regulatory inspections. The public report describes the facility, its production "
            "purpose, the opening schedule, the executives present, and the next operational "
            "milestones."
        ]
        * 12
    )
    body = (
        '<html><head><title>Company opens a new public manufacturing facility</title>'
        '<meta property="article:published_time" content="2026-08-13T09:00:00Z">'
        f"</head><body><article>{article_text}</article></body></html>"
    ).encode("utf-8")

    def http_get(url, _timeout, _max_bytes):
        calls.append(url)
        assert url == DISCOVERY_URL
        return {
            "status": 200,
            "final_url": PUBLISHER_URL,
            "headers": {"content-type": "text/html; charset=utf-8"},
            "body": body,
            "content_truncated": False,
        }

    request = _request()
    request["evidence_enrichment_context"] = {
        "requested": True,
        "reason": "ELIGIBLE_EVIDENCE_TOO_THIN_FOR_USEFUL_ARTICLE",
        "existing_evidence_substance": {
            "usable_content_words": 0,
        },
        "additional_source_is_eligibility_requirement": False,
    }
    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=http_get,
        clock=lambda: datetime(2026, 8, 13, 12, tzinfo=timezone.utc),
    )

    receipt = loader(request)

    assert receipt["status"] == "PASS"
    assert calls == [DISCOVERY_URL]
    assert len(receipt["evidence_documents"]) == 1
    document = receipt["evidence_documents"][0]
    assert document["source_url"] == PUBLISHER_URL
    assert document["reader_source_url"] == PUBLISHER_URL
    assert document["discovery_path_url"] == DISCOVERY_URL
    assert document["discovery_path_is_reader_authority"] is False
    assert document["canonical_resolution_status"] == "RESOLVED_FROM_DISCOVERY_REDIRECT"
    assert receipt["provenance"]["stopped_when_useful_depth_reached"] is True
    assert receipt["provenance"]["additional_source_is_eligibility_requirement"] is False
    assert summarize_evidence_substance(
        request, receipt["evidence_documents"]
    )["enough_for_useful_article"] is True
