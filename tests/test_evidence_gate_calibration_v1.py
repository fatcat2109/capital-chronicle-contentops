from __future__ import annotations

from datetime import datetime, timezone
import json

from live_contentops.claim_evidence_contract_v1 import build_claim_evidence_contract
from live_contentops.newsroom_assignment_scheduler_v1 import (
    ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
    select_first_viable_rolling_x_cluster,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
)
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)


AS_OF = "2026-08-11T12:00:00Z"


def _document(*, authority="official_public_primary_source", text="Agency confirms the policy took effect today.", publisher="Agency"):
    return {
        "document_id": "doc-1-" + publisher.casefold().replace(" ", "-"),
        "title": text,
        "publisher": publisher,
        "source_identity": publisher,
        "source_authority_class": authority,
        "source_url": "https://example.invalid/" + publisher.casefold().replace(" ", "-"),
        "published_at_utc": "2026-08-11T10:00:00Z",
        "event_time_utc": "2026-08-11T10:00:00Z",
        "canonical_content_text": text,
        "canonical_content_sha256": "a" * 64,
        "public_claim_allowed": True,
    }


def _request(*, story_type, product_mode="BREAKING_BRIEF", summaries=None):
    registry = load_source_capability_registry()
    capability_mode = {
        "BREAKING_BRIEF": "straight_news",
        "FOLLOW_UP_UPDATE": "straight_news",
        "STANDARD_NEWS_ANALYSIS": "analysis",
        "CAPITAL_CHRONICLE_DEEP_DIVE": "deep_analysis",
    }[product_mode]
    capability = resolve_story_capabilities(
        {"story_type": story_type, "article_mode": capability_mode}, registry
    )
    return {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": "cluster-1",
        "rank": 1,
        "headline_ids": ["headline-1"],
        "story_type": story_type,
        "article_mode": capability["article_mode"],
        "requested_article_mode": product_mode,
        "effective_article_mode": product_mode,
        "resolved_article_mode": product_mode,
        "required_evidence_capabilities": capability["required_evidence_capabilities"],
        "optional_evidence_capabilities": capability["optional_evidence_capabilities"],
        "source_adapter_families": capability["source_adapter_families"],
        "freshness_policy": capability["freshness_policy"],
        "capital_chronicle_numeric_or_analytical_authority_required": bool(
            capability.get("capital_chronicle_authority_required")
        ),
        "story_context": {"leaf_summaries": list(summaries or [])},
        "x_content_is_discovery_and_ranking_only": True,
        "request_logical_hash": "a" * 64,
    }


def _pass_receipt(request, *, authority=False):
    return {
        "status": "PASS",
        "cluster_id": request["cluster_id"],
        "headline_ids": request["headline_ids"],
        "provided_evidence_capabilities": request["required_evidence_capabilities"],
        "evidence_documents": [_document()],
        "claim_evidence_contract": {
            "status": "PASS",
            "supported_claim_count": 1,
            "fabricated_claim_count": 0,
            "supported_claims": [{"claim_id": "claim-1", "claim_text": "Agency confirms the policy took effect today."}],
            "omitted_unsupported_claims": [],
        },
        "capital_chronicle_authority_verified": authority,
        "numeric_evidence_required": False,
        "blockers": [],
    }


def test_a_breaking_brief_uses_minimum_claim_sufficiency_not_institutional_completeness():
    request = _request(
        story_type="company_sector_event",
        summaries=["Example Company announced a new public product today."],
    )
    assert request["required_evidence_capabilities"] == [
        "credible_event_confirmation", "basic_attributed_facts"
    ]
    assert "company_filing_or_release" in request["optional_evidence_capabilities"]
    assert "affected_entities" in request["optional_evidence_capabilities"]
    assert "market_snapshot" not in request["required_evidence_capabilities"]


def test_b_precise_company_number_is_omitted_without_primary_numeric_authority():
    request = _request(
        story_type="company_sector_event",
        summaries=["Example Company reported revenue of $12.4 billion today."],
    )
    secondary = _document(
        authority="reputable_secondary_source",
        text="Example Company reported revenue today.",
        publisher="Reuters",
    )
    contract = build_claim_evidence_contract(request, [secondary])
    assert contract["fabricated_claim_count"] == 0
    assert contract["supported_claim_count"] >= 1
    assert any(
        row["reason"] == "candidate_claim_not_found_in_evidence"
        or row["reason"] == "numeric_primary_authority_unavailable"
        for row in contract["omitted_unsupported_claims"]
    )
    assert all(not row.get("numeric_claim") for row in contract["supported_claims"])


def test_c_policy_story_has_no_company_filing_requirement():
    capability = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "straight_news"},
        load_source_capability_registry(),
    )
    assert capability["status"] == "PASS"
    assert "company_filing_or_release" not in capability["required_evidence_capabilities"]
    assert capability["capital_chronicle_authority_required"] is False


def test_d_follow_up_requires_prior_identity_and_new_delta_but_not_historical_completeness():
    cluster = {
        "cluster_id": "follow-up",
        "rank": 1,
        "headline_ids": ["headline-1"],
        "article_mode": "breaking",
        "resolved_article_mode": "FOLLOW_UP_UPDATE",
        "material_follow_up_context": {
            "previous_article_identity": "article-previous",
            "material_delta_reason_codes": ["NEW_CONFIRMED_EVENT"],
        },
    }
    result = select_first_viable_rolling_x_cluster(
        assignment={
            "schema_version": ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
            "decision": "SELECT_STORY",
            "ranked_clusters": [cluster],
        },
        acquire_evidence=_pass_receipt,
        story_type_by_cluster={"follow-up": "policy_decision"},
    )
    assert result["status"] == "SUCCESS"
    assert result["rank_attempts"][0]["effective_article_mode"] == "FOLLOW_UP_UPDATE"


def test_e_deep_dive_downgrades_to_standard_when_cc_authority_is_unavailable():
    cluster = {
        "cluster_id": "deep",
        "rank": 1,
        "headline_ids": ["headline-1"],
        "article_mode": "deep_dive",
        "resolved_article_mode": "CAPITAL_CHRONICLE_DEEP_DIVE",
    }

    def acquire(request):
        receipt = _pass_receipt(request)
        if request["capital_chronicle_numeric_or_analytical_authority_required"]:
            receipt["status"] = "BLOCKED"
            receipt["provided_evidence_capabilities"] = [
                value
                for value in receipt["provided_evidence_capabilities"]
                if value != "governed_analytical_context"
            ]
            receipt["blockers"] = ["capital_chronicle_authority_not_verified"]
        return receipt

    result = select_first_viable_rolling_x_cluster(
        assignment={
            "schema_version": ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
            "decision": "SELECT_STORY",
            "ranked_clusters": [cluster],
        },
        acquire_evidence=acquire,
        story_type_by_cluster={"deep": "company_sector_event"},
    )
    attempt = result["rank_attempts"][0]
    assert result["status"] == "SUCCESS"
    assert [row["effective_mode"] for row in attempt["mode_attempts"]] == [
        "CAPITAL_CHRONICLE_DEEP_DIVE", "STANDARD_NEWS_ANALYSIS"
    ]
    assert attempt["effective_article_mode"] == "STANDARD_NEWS_ANALYSIS"
    assert attempt["mode_downgrade_reason"] == "EVIDENCE_DEPTH_UNAVAILABLE_SCOPE_REDUCED"


def test_f_large_official_document_uses_bounded_verified_prefix():
    url = "https://api.federalregister.gov/v1/documents/2026-12345.json"
    body = json.dumps(
        {
            "title": "Final public rule",
            "publication_date": "2026-08-11",
            "effective_on": "2026-09-01",
            "agencies": [{"name": "Official Agency"}],
        }
    ).encode()
    packet = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "application/json"},
            "body": body,
            "content_truncated": True,
        },
    )(
        {
            "cluster_id": "cluster-1",
            "headline_ids": ["headline-1"],
            "request_logical_hash": "a" * 64,
            "source_adapter_families": ["official_regulatory_fiscal"],
            "required_evidence_capabilities": ["official_document"],
            "story_context": {"official_source_url_bindings": [{"url": url, "headline_id": "headline-1"}]},
        }
    )
    assert packet["status"] == "PASS"
    document = packet["official_source_documents"][0]
    assert document["content_truncated"] is True
    assert document["retrieval_method"] == "READ_ONLY_HTTP_GET_BOUNDED_PREFIX"
    assert document["raw_sha256"]


def test_g_two_independent_reputable_rss_sources_can_corroborate_nonnumeric_breaking_claim():
    rss = b"""<?xml version='1.0'?><rss><channel>
    <item><title>Port authority confirms the main channel has reopened - Reuters</title><link>https://news.google.com/a</link><pubDate>Tue, 11 Aug 2026 10:00:00 GMT</pubDate><source url='https://reuters.com'>Reuters</source></item>
    <item><title>Main shipping channel reopens after closure - Associated Press</title><link>https://news.google.com/b</link><pubDate>Tue, 11 Aug 2026 10:05:00 GMT</pubDate><source url='https://apnews.com'>Associated Press</source></item>
    </channel></rss>"""
    loader = BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        clock=lambda: datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
        http_get=lambda url, *_args: {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "application/rss+xml"},
            "body": rss,
        },
    )
    request = _request(
        story_type="geopolitical_event",
        summaries=["The main shipping channel has reopened after a temporary closure."],
    )
    packet = loader(request)
    contract = build_claim_evidence_contract(request, packet["evidence_documents"])
    assert packet["status"] == "PASS"
    assert len({row["publisher"] for row in packet["evidence_documents"]}) == 2
    assert contract["status"] == "PASS"
    assert any(
        row["support_status"] in {"SUPPORTED_CORROBORATED_SECONDARY", "SUPPORTED_SOURCE_TITLE"}
        for row in contract["supported_claims"]
    )


def test_only_x_discovery_with_no_corroborating_document_fails_closed():
    request = _request(
        story_type="geopolitical_event",
        summaries=["An X account claims an unconfirmed event occurred."],
    )
    adapter = RollingXTargetedEvidenceAdapter(
        evaluation_as_of_utc=AS_OF,
        public_secondary_loader=lambda _request: {
            "status": "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "request_logical_hash": request["request_logical_hash"],
            },
            "evidence_documents": [],
            "provided_evidence_capabilities": [],
            "blockers": ["public_source_unavailable"],
        },
    )
    receipt = adapter(request)
    assert receipt["status"] == "BLOCKED"
    assert "evidence_documents_missing" in receipt["blockers"]
    assert receipt["claim_evidence_contract"]["fabricated_claim_count"] == 0


def test_unsupported_quote_is_omitted_not_invented():
    request = _request(
        story_type="company_sector_event",
        summaries=['Example Company said "the deal is guaranteed to close" today.'],
    )
    document = _document(text="Example Company announced that discussions remain ongoing.")
    contract = build_claim_evidence_contract(request, [document])
    assert contract["fabricated_claim_count"] == 0
    assert any(row["reason"] in {"quote_exact_support_unavailable", "candidate_claim_not_found_in_evidence"} for row in contract["omitted_unsupported_claims"])
