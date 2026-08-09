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


def test_unsupported_family_never_calls_network():
    calls = []
    result = BoundedOfficialPrimarySourceLocator(
        http_get=lambda *_args: calls.append(_args),
    )(_request("licensed_news"))

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["official_source_locator_family_unsupported"]
    assert calls == []
