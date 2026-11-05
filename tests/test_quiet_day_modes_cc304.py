"""CC-304: quiet-day explainers and week-ahead pieces are possible again for a general public event.

Since 330f1978 (23 Aug) preselection checks each mode against the general-public-event profile,
which offered straight_news and analysis only: an explainer fell back to a breaking brief and a
week-ahead piece failed. Both modes are back, under the same evidence gates. Controlled fixtures.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from live_contentops.newsroom_assignment_scheduler_v1 import _logical_hash
from live_contentops.official_primary_evidence_loader_v1 import BoundedOfficialPrimaryEvidenceLoader
from live_contentops.preselection_intelligence_v1 import apply_preselection_intelligence
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import RollingXTargetedEvidenceAdapter
from live_contentops.source_capability_registry_v2 import (
    effective_rolling_x_capability_registry,
    resolve_story_capabilities,
)
from test_rolling_x_targeted_evidence_adapter_v1 import AS_OF, BEA_SCHEDULE_HTML, BEA_SCHEDULE_URL, _request

EMPTY_CATALOG = {"stores": [], "store_count_discovered": 0, "discovery_complete": True, "root_exists": False}


def resolved(product_mode):
    return resolve_story_capabilities({"story_type": "general_public_event", "product_article_mode": product_mode},
                                      effective_rolling_x_capability_registry())


def test_a_general_public_event_can_take_each_quiet_day_mode_with_its_evidence_gates():
    explainer, week_ahead, brief = (resolved(m) for m in (
        "EVERGREEN_EXPLAINER", "WEEK_AHEAD_OR_WATCH", "BREAKING_BRIEF"))
    assert explainer["status"] == week_ahead["status"] == brief["status"] == "PASS"
    assert explainer["article_mode"] == "explainer"
    assert explainer["required_evidence_capabilities"] == ["credible_event_confirmation", "basic_attributed_facts"]
    assert week_ahead["article_mode"] == "week_ahead"
    assert week_ahead["required_evidence_capabilities"] == [
        "official_schedule", "scheduled_event_identity", "scheduled_event_date_time", "basic_attributed_facts"]
    assert "official_macro" in week_ahead["source_adapter_families"]
    for capability in (explainer, week_ahead):
        assert capability["editorial_mode_contract"]["factual_premises_must_be_source_bound"] is True
        assert capability["editorial_mode_contract"]["quiet_day_may_lower_truth_or_permission_standards"] is False
    assert brief["article_mode"] == "straight_news"


def preselected(article_mode, summary):
    result = apply_preselection_intelligence(
        [{"cluster_id": "event-chain", "rank": 1, "headline_ids": ["event-headline"],
          "article_mode": article_mode, "selection_case": "A general public event.",
          "why_now": "Useful now.", "entities_topics": ["Public Body"], "leaf_summaries": [summary]}],
        published_corpus=[], cc_catalog=EMPTY_CATALOG, now=datetime(2026, 8, 20, 5, 0, tzinfo=timezone.utc))
    return result["ranked_clusters"][0]


@pytest.mark.parametrize("mode", ["EVERGREEN_EXPLAINER", "WEEK_AHEAD_OR_WATCH"])
def test_preselection_keeps_the_quiet_day_mode_instead_of_a_brief(mode):
    candidate = preselected(mode, "Context on how the process works and what is scheduled next.")
    assert candidate["resolved_article_mode"] == mode
    assert "preselection_capability_fallback_from" not in candidate["growth_editorial_mode_resolution"]


def test_a_breaking_event_still_prefers_the_brief():
    candidate = preselected("BREAKING_BRIEF", "The agency announced a new decision today.")
    assert candidate["resolved_article_mode"] == "BREAKING_BRIEF"


def week_ahead_request():
    request = _request(story_type="general_public_event", article_mode="week_ahead")
    request.update({
        "requested_article_mode": "WEEK_AHEAD_OR_WATCH",
        "effective_article_mode": "WEEK_AHEAD_OR_WATCH",
        "resolved_article_mode": "WEEK_AHEAD_OR_WATCH",
        "story_context": {
            "leaf_summaries": ["BEA release schedule for the week ahead."],
            "official_source_urls": [BEA_SCHEDULE_URL],
            "official_source_url_bindings": [{"headline_id": "headline-1", "url": BEA_SCHEDULE_URL}],
        },
    })
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"})
    return request


def receipt_for(body):
    official = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: {"status": 200, "final_url": BEA_SCHEDULE_URL,
                                 "headers": {"content-type": "text/html"}, "body": body})

    def grounded_research(_request, *, initial_documents):
        documents = [{**dict(raw), "grounded_source_ref": "SRC_1"} for raw in initial_documents]
        return {"status": "PASS", "blockers": [], "evidence_documents": documents,
                "research_packet": {
                    "research_status": "PASS",
                    "core_factual_proposition": "BEA publishes an official release schedule.",
                    "confirmed_facts": [{"fact_id": "f1", "factual_statement": "BEA publishes an official release schedule.",
                                         "source_refs": ["SRC_1"], "confidence_class": "HIGH",
                                         "direct_or_inferred": "DIRECT"}],
                    "attributed_numeric_facts": [],
                    "sources": [{"source_ref": "SRC_1", "evidence_document_id": d["document_id"]} for d in documents],
                    "suggested_article_mode": "WEEK_AHEAD_OR_WATCH", "cc_context": {}},
                "evidence_substance": {}, "latest_event_state_closure": {"status": "NOT_REQUIRED"}}

    return RollingXTargetedEvidenceAdapter(official_evidence_loader=official, grounded_researcher=grounded_research,
                                           evaluation_as_of_utc=AS_OF)(week_ahead_request())


def test_a_week_ahead_piece_with_official_schedule_facts_passes():
    receipt = receipt_for(BEA_SCHEDULE_HTML)
    assert receipt["status"] == "PASS"
    assert set(receipt["provided_evidence_capabilities"]) >= {
        "official_schedule", "scheduled_event_identity", "scheduled_event_date_time", "basic_attributed_facts"}
    assert receipt["deterministic_official_schedule_facts"]
    assert receipt["publication_authority"] is False


def test_a_week_ahead_piece_without_its_schedule_evidence_is_refused():
    page = (b"<html><head><title>Release Schedule | U.S. Bureau of Economic Analysis (BEA)</title>"
            b"<meta name=\"date\" content=\"2026-08-08T10:00:00Z\"></head><body><p>BEA publishes an official "
            b"release schedule.</p></body></html>")
    receipt = receipt_for(page)
    assert receipt["status"] != "PASS"
    assert "deterministic_official_schedule_fact_binding_missing" in receipt["blockers"]
    assert "required_evidence_capability_missing:official_schedule" in receipt["blockers"]
