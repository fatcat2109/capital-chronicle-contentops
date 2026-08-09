from __future__ import annotations

from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    OFFICIAL_HOSTS_BY_FAMILY,
    BoundedOfficialPrimaryEvidenceLoader,
)
from live_contentops.official_primary_source_locator_v1 import (
    BoundedOfficialPrimarySourceLocator,
    LOCATOR_FAMILIES,
)
from live_contentops.newsroom_assignment_scheduler_v1 import (
    _leaf_evidence_reachability,
)


# --- policy_decision article-mode profiles (Phase 13) -----------------------------


def test_policy_straight_news_does_not_require_capital_chronicle_authority():
    registry = load_source_capability_registry()
    capability = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "straight_news"}, registry
    )
    # Base policy_decision row is market_sensitive, but straight_news must not need CC authority.
    assert capability["capital_chronicle_authority_required"] is False
    assert capability["market_snapshot_required"] is False
    assert capability["market_context_required"] is False
    assert "official_statement" in capability["required_evidence_capabilities"]
    assert "decision_timeline" in capability["required_evidence_capabilities"]
    assert "issuing_authority" in capability["required_evidence_capabilities"]
    assert capability["source_adapter_families"] == ["official_policy"]


def test_policy_analysis_still_requires_capital_chronicle_authority():
    registry = load_source_capability_registry()
    capability = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "analysis"}, registry
    )
    assert capability["capital_chronicle_authority_required"] is True
    assert capability["market_snapshot_required"] is True
    assert "governed_analytical_context" in capability["required_evidence_capabilities"]


def test_market_sensitive_metadata_alone_never_adds_capital_chronicle_authority():
    registry = load_source_capability_registry()
    # regulatory_fiscal_event straight_news remains CC-free even if market metadata present.
    capability = resolve_story_capabilities(
        {"story_type": "regulatory_fiscal_event", "article_mode": "straight_news"}, registry
    )
    assert capability["capital_chronicle_authority_required"] is False
    assert capability["market_snapshot_required"] is False


# --- official_policy loader (Phase 14) --------------------------------------------


FR_STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260809a.htm"


def _fr_statement_html(date="2026-08-08"):
    return (
        f'<html><head><meta name="date" content="{date}"></head><body>'
        "Federal Open Market Committee statement on monetary policy. "
        "The Committee reaffirmed the target range for the federal funds rate.</body></html>"
    ).encode()


def _response(url, body, status=200, content_type="text/html"):
    return {
        "status": status,
        "final_url": url,
        "headers": {"content-type": content_type},
        "body": body,
    }


def _policy_request(url=FR_STATEMENT_URL):
    return {
        "cluster_id": "c1",
        "headline_ids": ["h1"],
        "request_logical_hash": "a" * 64,
        "source_adapter_families": ["official_policy"],
        "required_evidence_capabilities": [
            "official_statement",
            "decision_timeline",
            "issuing_authority",
        ],
        "story_context": {
            "official_source_url_bindings": [{"url": url, "headline_id": "h1"}],
        },
    }


def test_official_policy_family_is_allowlisted():
    assert "www.federalreserve.gov" in OFFICIAL_HOSTS_BY_FAMILY["official_policy"]


def test_official_policy_loader_validates_statement_capabilities_and_binding():
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-09T00:00:00Z",
        http_get=lambda url, timeout, maximum: _response(url, _fr_statement_html()),
    )
    packet = loader(_policy_request())
    assert packet["status"] == "PASS", packet["blockers"]
    provided = set(packet["provided_evidence_capabilities"])
    assert {"official_statement", "decision_timeline", "issuing_authority"} <= provided
    document = packet["official_source_documents"][0]
    assert document["source_authority_class"] == "official_public_primary_source"
    assert document["source_url"] == FR_STATEMENT_URL
    assert document["source_headline_id"] == "h1"
    assert document["published_at_utc"] == "2026-08-08T00:00:00Z"
    assert packet["provenance"]["retrieved_at_utc"] is not None
    assert packet["provenance"]["evaluation_as_of_utc"] == "2026-08-09T00:00:00Z"


def test_official_policy_loader_fails_closed_for_post_cutoff_publication():
    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc="2026-08-09T00:00:00Z",
        http_get=lambda url, timeout, maximum: _response(
            url, _fr_statement_html(date="2026-08-10")
        ),
    )
    packet = loader(_policy_request())
    assert packet["status"] == "BLOCKED"
    assert "official_source_published_after_evaluation_cutoff" in packet["blockers"]


# --- official_policy locator (Phase 14) -------------------------------------------


def test_official_policy_locator_finds_federal_reserve_statement_discovery_only():
    index_html = (
        '<html><a href="/newsevents/pressreleases/monetary20260809a.htm">'
        "FOMC issues implementation note</a></html>"
    ).encode()
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, timeout, maximum: _response(url, index_html)
    )
    result = locator(
        {
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "source_adapter_families": ["official_policy"],
            "evaluation_as_of_utc": "2026-08-09T00:00:00Z",
            "story_context": {"why_now": "FOMC decision", "entities_topics": ["Federal Reserve"]},
        }
    )
    assert result["status"] == "PASS", result.get("blockers")
    assert result["candidate_official_url"] == FR_STATEMENT_URL
    assert result["discovery_only"] is True
    assert result["factual_authority"] is False
    assert result["publication_authority"] is False
    assert result["evidence_capabilities"] == []


def test_official_policy_locator_fails_closed_when_no_statement_found():
    locator = BoundedOfficialPrimarySourceLocator(
        http_get=lambda url, timeout, maximum: _response(url, b"<html>nothing here</html>")
    )
    result = locator(
        {
            "cluster_id": "c1",
            "headline_ids": ["h1"],
            "source_adapter_families": ["official_policy"],
        }
    )
    assert result["status"] == "BLOCKED"


# --- evidence reachability (Phase 15) ---------------------------------------------


def _records(headline_ids_to_urls):
    return {
        headline_id: {
            "headline_id": headline_id,
            "source_timestamp_utc": "2026-08-08T00:00:00Z",
            "external_content": {"official_source_urls": urls},
        }
        for headline_id, urls in headline_ids_to_urls.items()
    }


def test_reachability_supported_now_when_bound_official_url_matches_family():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": [FR_STATEMENT_URL]})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is True
    assert "official_policy" in reach["supported_source_families"]
    assert reach["bounded_locator_available"] is True
    assert reach["current_v1_path"] == "SUPPORTED_NOW"
    assert reach["grants_factual_or_evidence_or_publication_authority"] is False


def test_reachability_no_current_path_when_no_bound_official_url():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": []})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is False
    assert reach["supported_source_families"] == []
    assert reach["current_v1_path"] == "NO_CURRENT_PATH"


def test_reachability_conditional_when_urls_bound_but_outside_supported_family():
    cluster = {"member_headline_ids": ["h1"]}
    records = _records({"h1": ["https://www.reuters.com/world/some-story"]})
    reach = _leaf_evidence_reachability(cluster, records)
    assert reach["direct_primary_binding"] is False
    assert reach["current_v1_path"] == "CONDITIONAL"
    assert reach["supported_source_families"] == []


def test_locator_families_cover_supported_official_paths():
    assert {"official_regulatory_fiscal", "official_macro", "company_primary",
            "sec_regulatory", "official_policy"} <= set(LOCATOR_FAMILIES)
