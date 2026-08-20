from __future__ import annotations

from copy import deepcopy

from live_contentops.newsroom_assignment_scheduler_v1 import (
    ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
    _logical_hash,
    select_first_viable_rolling_x_cluster,
)
from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
)
from live_contentops.source_capability_registry_v2 import (
    effective_rolling_x_capability_registry,
    load_source_capability_registry,
    resolve_story_capabilities,
)

AS_OF = "2026-08-08T12:00:00Z"
BEA_SCHEDULE_URL = "https://www.bea.gov/news/schedule"
BEA_SCHEDULE_HTML = b"""
<html><head><title>Release Schedule | U.S. Bureau of Economic Analysis (BEA)</title>
<meta name="date" content="2026-08-08T10:00:00Z"></head><body><table><tbody>
<tr class="scheduled-releases-type-press"><td><div class="release-date">August 26</div>
<small class="text-muted">8:30 AM</small></td><td class="release-title views-field">
GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026</td></tr>
<tr class="scheduled-releases-type-press"><td><div class="release-date">August 26</div>
<small class="text-muted">8:30 AM</small></td><td class="release-title views-field">
Personal Income and Outlays, July 2026</td></tr>
</tbody></table></body></html>
"""


def _request(
    *,
    cluster_id="cluster-1",
    headline_ids=None,
    story_type="market_move",
    article_mode=None,
    required=None,
    families=None,
):
    registry = effective_rolling_x_capability_registry()
    capability = resolve_story_capabilities(
        {
            "story_type": story_type,
            **({"article_mode": article_mode} if article_mode else {}),
        },
        registry,
    )
    request = {
        "schema_version": "capital_chronicle.rolling_x_story_evidence_request.v1",
        "cluster_id": cluster_id,
        "rank": 1,
        "headline_ids": headline_ids or ["headline-1"],
        "story_type": story_type,
        "article_mode": capability.get("article_mode") or "straight_news",
        "needed_evidence": ["official record"],
        "required_evidence_capabilities": list(
            required or capability["required_evidence_capabilities"]
        ),
        "source_adapter_families": list(
            families or capability["source_adapter_families"]
        ),
        "freshness_policy": capability["freshness_policy"],
        "market_sensitive": bool(capability.get("market_sensitive")),
        "market_snapshot_required": bool(capability.get("market_snapshot_required")),
        "capital_chronicle_numeric_or_analytical_authority_required": bool(
            capability.get("capital_chronicle_authority_required")
        ),
        "x_content_is_discovery_and_ranking_only": True,
    }
    request["request_logical_hash"] = _logical_hash(request)
    return request


def _packet(request, *, prior=True):
    claim = {
        "claim_id": "claim-1",
        "metric": "official market metric",
        "value": 100.0,
        "unit": "index",
        "observation_time_utc": "2026-08-08T11:00:00Z",
        "known_at_utc": "2026-08-08T11:05:00Z",
        "source_id": "governed-source",
        "source_artifact_ref": "packet#numeric_claims/0",
        "public_claim_allowed": True,
        "llm_numeric_authority": False,
    }
    if prior:
        claim["prior_value"] = 99.0
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "packet-1",
        "status": "PASS_PUBLICATION_AUTHORIZED",
        "generated_at_utc": "2026-08-08T11:05:00Z",
        "as_of_utc": AS_OF,
        "story_window": {"hours": 24},
        "rolling_x_story_binding": {
            "cluster_id": request["cluster_id"],
            "headline_ids": list(request["headline_ids"]),
            "request_logical_hash": request["request_logical_hash"],
        },
        "provided_evidence_capabilities": list(
            request["required_evidence_capabilities"]
        ),
        "events": [{"event_time_utc": "2026-08-08T10:30:00Z"}],
        "headlines": [{"published_at_utc": "2026-08-08T10:30:00Z"}],
        "official_source_documents": [
            {
                "document_id": "document-1",
                "title": "Official release",
                "publisher": "Official Agency",
                "source_authority_class": "official_public_primary_source",
                "source_url": "https://official.example/release",
                "published_at_utc": "2026-08-08T10:30:00Z",
                "raw_sha256": "a" * 64,
                "public_claim_allowed": True,
            }
        ],
        "numeric_claims": [claim],
        "market_snapshots": [
            {
                "snapshot_id": "snapshot-1",
                "generated_at_utc": "2026-08-08T11:05:00Z",
                "observation_time_utc": "2026-08-08T11:00:00Z",
                "claim_ids": ["claim-1"],
            }
        ],
        "source_state": {"reporting_allowed": True},
        "candidate_visual_inputs": [],
        "citation_map": {"claim-1": ["packet#numeric_claims/0"]},
        "provenance": {
            "retrieved_at_utc": "2026-08-08T11:05:00Z",
            "raw_sha256": "b" * 64,
        },
        "public_claim_permissions": {
            "decision": "ALLOW",
            "reporting_allowed": True,
            "numeric_claims_allowed": True,
            "consumer_class": ["contentops_publication"],
            "llm_numeric_authority": False,
        },
        "blockers": [],
        "publication_assignment": {"fresh_material_delta": True},
    }


def _adapter(packet):
    return RollingXTargetedEvidenceAdapter(
        packet_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )


def test_neutral_fallback_request_and_adapter_share_effective_registry():
    public_secondary_calls = []

    def public_secondary_loader(request):
        public_secondary_calls.append(dict(request))
        return {
            "status": "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "request_logical_hash": request["request_logical_hash"],
            },
            "evidence_documents": [],
            "provided_evidence_capabilities": [],
            "blockers": ["public_source_unavailable"],
            "provenance": {"request_count": 1},
        }

    adapter = RollingXTargetedEvidenceAdapter(
        public_secondary_loader=public_secondary_loader,
        evaluation_as_of_utc=AS_OF,
    )
    result = select_first_viable_rolling_x_cluster(
        assignment={
            "schema_version": ROLLING_X_ASSIGNMENT_SCHEMA_VERSION,
            "decision": "SELECT_STORY",
            "ranked_clusters": [
                {
                    "cluster_id": "neutral-current-event",
                    "rank": 1,
                    "headline_ids": ["neutral-headline"],
                    "article_mode": "breaking",
                    "market_sensitive": False,
                    "needed_evidence": ["Corroborate the event."],
                }
            ],
        },
        acquire_evidence=adapter,
        story_type_by_cluster={
            "neutral-current-event": "general_public_event"
        },
    )

    assert len(public_secondary_calls) == 1
    request = public_secondary_calls[0]
    assert request["story_type"] == "general_public_event"
    assert request["required_evidence_capabilities"] == [
        "credible_event_confirmation",
        "basic_attributed_facts",
    ]
    assert request["source_adapter_families"] == ["public_secondary"]
    assert result["status"] == "NO_PUBLICATION"
    blockers = result["rank_attempts"][0]["blockers"]
    assert "unsupported_story_type" not in blockers
    assert "evidence_request_capability_registry_mismatch" not in blockers
    assert "evidence_request_source_adapter_registry_mismatch" not in blockers


def test_effective_registry_preserves_specialized_story_profiles_exactly():
    base = load_source_capability_registry()
    effective = effective_rolling_x_capability_registry(base)

    for story_type in (
        "company_sector_event",
        "geopolitical_event",
        "data_release",
        "policy_decision",
        "market_move",
    ):
        request = {"story_type": story_type}
        assert resolve_story_capabilities(
            request, effective
        ) == resolve_story_capabilities(request, base)

    neutral = resolve_story_capabilities(
        {"story_type": "general_public_event", "article_mode": "straight_news"},
        effective,
    )
    assert neutral["status"] == "PASS"
    assert neutral["required_evidence_capabilities"] == [
        "credible_event_confirmation",
        "basic_attributed_facts",
    ]
    assert neutral["source_adapter_families"] == ["public_secondary"]
    assert neutral["market_context_required"] is False
    assert neutral["capital_chronicle_authority_required"] is False


def test_week_ahead_profile_is_distinct_without_weakening_data_release_analysis():
    registry = effective_rolling_x_capability_registry()
    week_ahead = resolve_story_capabilities(
        {
            "story_type": "data_release",
            "product_article_mode": "WEEK_AHEAD_OR_WATCH",
        },
        registry,
    )
    analysis = resolve_story_capabilities(
        {
            "story_type": "data_release",
            "product_article_mode": "DATA_OR_DOCUMENT_LENS",
        },
        registry,
    )
    breaking = resolve_story_capabilities(
        {
            "story_type": "data_release",
            "product_article_mode": "BREAKING_BRIEF",
        },
        registry,
    )

    assert week_ahead["status"] == "PASS"
    assert week_ahead["article_mode"] == "week_ahead"
    assert week_ahead["required_evidence_capabilities"] == [
        "official_schedule",
        "scheduled_event_identity",
        "scheduled_event_date_time",
    ]
    assert week_ahead["capital_chronicle_authority_required"] is False
    assert week_ahead["source_adapter_families"] == ["official_macro"]
    assert analysis["required_evidence_capabilities"] == [
        "official_release",
        "governed_analytical_context",
    ]
    assert analysis["capital_chronicle_authority_required"] is True
    assert breaking["required_evidence_capabilities"] == [
        "credible_event_confirmation",
        "basic_attributed_facts",
    ]
    assert breaking["capital_chronicle_authority_required"] is False


def test_week_ahead_adapter_preserves_exact_schedule_facts_model_omits():
    request = _request(story_type="data_release", article_mode="week_ahead")
    request.update({
        "requested_article_mode": "WEEK_AHEAD_OR_WATCH",
        "effective_article_mode": "WEEK_AHEAD_OR_WATCH",
        "resolved_article_mode": "WEEK_AHEAD_OR_WATCH",
        "story_context": {
            "leaf_summaries": ["BEA release schedule for the week ahead."],
            "official_source_urls": [BEA_SCHEDULE_URL],
            "official_source_url_bindings": [{
                "headline_id": "headline-1",
                "url": BEA_SCHEDULE_URL,
            }],
        },
    })
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )

    def response(url, body):
        return {
            "status": 200,
            "final_url": url,
            "headers": {"content-type": "text/html"},
            "body": body,
        }

    official = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=AS_OF,
        http_get=lambda *_args: response(BEA_SCHEDULE_URL, BEA_SCHEDULE_HTML),
    )

    def grounded_research(_request, *, initial_documents):
        documents = []
        sources = []
        for raw in initial_documents:
            row = {**dict(raw), "grounded_source_ref": "SRC_BEA_SCHEDULE"}
            documents.append(row)
            sources.append({
                "source_ref": "SRC_BEA_SCHEDULE",
                "evidence_document_id": row["document_id"],
            })
        return {
            "status": "PASS",
            "blockers": [],
            "evidence_documents": documents,
            "research_packet": {
                "research_status": "PASS",
                "core_factual_proposition": "BEA maintains an official Release Schedule.",
                "confirmed_facts": [{
                    "fact_id": "model-generic",
                    "factual_statement": "BEA maintains an official Release Schedule.",
                    "source_refs": ["SRC_BEA_SCHEDULE"],
                    "confidence_class": "HIGH",
                    "direct_or_inferred": "DIRECT",
                }],
                "attributed_numeric_facts": [],
                "sources": sources,
                "suggested_article_mode": "BREAKING_BRIEF",
                "cc_context": {},
            },
            "evidence_substance": {},
            "latest_event_state_closure": {"status": "NOT_REQUIRED"},
        }

    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=official,
        grounded_researcher=grounded_research,
        evaluation_as_of_utc=AS_OF,
    )(request)

    assert receipt["status"] == "PASS"
    assert receipt["capital_chronicle_authority_verified"] is False
    assert receipt["numeric_evidence_required"] is False
    assert receipt["publication_authority"] is False
    assert set(receipt["provided_evidence_capabilities"]) >= {
        "official_schedule",
        "scheduled_event_identity",
        "scheduled_event_date_time",
    }
    facts = receipt["deterministic_official_schedule_facts"]
    assert [row["factual_statement"] for row in facts] == [
        "August 26 8:30 AM — GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026",
        "August 26 8:30 AM — Personal Income and Outlays, July 2026",
    ]
    assert all(
        row["source_content_sha256"]
        == receipt["evidence_documents"][0]["canonical_content_sha256"]
        and row["evidence_document_id"] == receipt["evidence_documents"][0]["document_id"]
        and row["llm_factual_or_numeric_authority"] is False
        and row["publication_authority"] is False
        for row in facts
    )
    grounded = receipt["grounded_research_packet"]
    assert grounded["model_omitted_deterministic_schedule_fact_count"] == 2
    assert grounded["suggested_article_mode"] == "WEEK_AHEAD_OR_WATCH"
    assert [row["factual_statement"] for row in grounded["confirmed_facts"][:2]] == [
        row["factual_statement"] for row in facts
    ]
    assert receipt["editorial_mode_contract"][
        "narrow_official_schedule_fact_lane"
    ] is True


def test_effective_registry_keeps_unknown_and_tampered_requests_fail_closed():
    adapter = RollingXTargetedEvidenceAdapter(
        public_secondary_loader=lambda _request: (_ for _ in ()).throw(
            AssertionError("registry-invalid request must stop before acquisition")
        ),
        evaluation_as_of_utc=AS_OF,
    )
    unknown = _request(story_type="general_public_event")
    unknown["story_type"] = "arbitrary_unregistered_event"
    unknown_receipt = adapter(unknown)
    assert unknown_receipt["status"] == "BLOCKED"
    assert "unsupported_story_type" in unknown_receipt["blockers"]

    capability_tamper = _request(story_type="general_public_event")
    capability_tamper["required_evidence_capabilities"] = [
        "credible_event_confirmation"
    ]
    capability_receipt = adapter(capability_tamper)
    assert capability_receipt["status"] == "BLOCKED"
    assert "evidence_request_capability_registry_mismatch" in capability_receipt[
        "blockers"
    ]

    family_tamper = _request(story_type="general_public_event")
    family_tamper["source_adapter_families"] = ["official_macro"]
    family_receipt = adapter(family_tamper)
    assert family_receipt["status"] == "BLOCKED"
    assert "evidence_request_source_adapter_registry_mismatch" in family_receipt[
        "blockers"
    ]


def test_valid_exact_governed_market_packet_satisfies_all_declared_capabilities():
    request = _request()
    receipt = _adapter(_packet(request))(request)

    assert receipt["status"] == "PASS"
    assert receipt["provided_evidence_capabilities"] == [
        "catalyst_evidence",
        "current_market_snapshot",
        "prior_close",
    ]
    assert receipt["capital_chronicle_authority_verified"] is True
    assert receipt["publication_authority"] is False
    assert receipt["capital_chronicle_publication_authority"]["state"] == (
        "PUBLICATION_PACKET_AVAILABLE"
    )
    assert receipt["publication_authorized_cc_projection"]["exact_numeric_claims"] == (
        _packet(request)["numeric_claims"]
    )
    assert receipt["cc_authority_utilization"]["authorized_claim_count_consumed"] == 1
    assert receipt["cc_authority_utilization"]["values_regenerated_or_repaired"] is False
    document = receipt["evidence_documents"][0]
    assert document["cluster_id"] == request["cluster_id"]
    assert document["headline_ids"] == request["headline_ids"]
    assert document["content_sha256"] == "a" * 64


def test_market_prior_close_is_never_synthesized_by_contentops():
    request = _request()
    receipt = _adapter(_packet(request, prior=False))(request)

    assert receipt["status"] == "BLOCKED"
    assert "governed_prior_close_missing" in receipt["blockers"]
    assert "prior_close" not in receipt["provided_evidence_capabilities"]
    assert receipt["capital_chronicle_authority_verified"] is False


def test_x_or_candidate_context_cannot_satisfy_evidence():
    request = _request()
    packet = _packet(request)
    packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION"
    packet["public_claim_permissions"]["decision"] = "BLOCK"
    packet["public_claim_permissions"]["reporting_allowed"] = False
    packet["official_source_documents"][0]["public_claim_allowed"] = False
    packet["numeric_claims"][0]["public_claim_allowed"] = False

    receipt = _adapter(packet)(request)

    assert receipt["status"] == "BLOCKED"
    assert "governed_packet_not_publication_authorized" in receipt["blockers"]
    assert "governed_reporting_permission_not_granted" in receipt["blockers"]
    assert receipt["capital_chronicle_authority_verified"] is False
    assert receipt["capital_chronicle_publication_authority"]["state"] == (
        "PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED"
    )
    assert receipt["publication_authorized_cc_projection"] == {}


def test_stale_governed_packet_fails_current_operator_readiness():
    request = _request()
    packet = _packet(request)
    packet["events"][0]["event_time_utc"] = "2026-07-13T00:00:00Z"
    packet["headlines"][0]["published_at_utc"] = "2026-07-13T00:00:00Z"
    packet["official_source_documents"][0]["published_at_utc"] = (
        "2026-07-13T00:00:00Z"
    )
    packet["numeric_claims"][0]["observation_time_utc"] = (
        "2026-07-13T00:00:00Z"
    )
    packet["market_snapshots"][0]["generated_at_utc"] = (
        "2026-07-13T00:00:00Z"
    )

    receipt = _adapter(packet)(request)

    assert receipt["status"] == "BLOCKED"
    assert "market_sensitive_story_snapshot_stale_or_missing" in receipt["blockers"]
    assert "market_sensitive_story_ingest_stale_or_missing" in receipt["blockers"]
    assert receipt["capital_chronicle_publication_authority"]["state"] == (
        "PUBLICATION_PACKET_STALE_OR_BLOCKED"
    )


def test_exact_cluster_headline_and_request_hash_binding_is_required():
    request = _request()
    for field, value, expected in (
        ("cluster_id", "other", "governed_evidence_cluster_binding_mismatch"),
        ("headline_ids", ["other"], "governed_evidence_headline_binding_mismatch"),
        ("request_logical_hash", "other", "governed_evidence_request_hash_mismatch"),
    ):
        packet = _packet(request)
        packet["rolling_x_story_binding"][field] = value
        receipt = _adapter(packet)(request)
        assert receipt["status"] == "BLOCKED"
        assert expected in receipt["blockers"]


def test_valid_official_primary_packet_can_satisfy_nonnumeric_capability():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["regulatory_fiscal_event"] = {
        "required_evidence_capabilities": ["official_document"],
        "market_context_required": False,
        "freshness_policy": "event_24h",
        "source_adapter_families": ["official_regulatory_fiscal"],
    }
    request = _request(
        story_type="regulatory_fiscal_event",
        required=["official_document"],
        families=["official_regulatory_fiscal"],
    )
    request["market_sensitive"] = False
    request["market_snapshot_required"] = False
    request["capital_chronicle_numeric_or_analytical_authority_required"] = False
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    packet = _packet(request)
    packet["status"] = "PASS"
    packet["provided_evidence_capabilities"] = ["official_document"]
    adapter = RollingXTargetedEvidenceAdapter(
        packet_loader=lambda _request: (_ for _ in ()).throw(
            AssertionError("official-only story must not load Capital Chronicle packet")
        ),
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
        capability_registry=registry,
    )

    receipt = adapter(request)

    assert receipt["status"] == "PASS"
    assert set(receipt["provided_evidence_capabilities"]) == {
        "official_document", "credible_event_confirmation", "basic_attributed_facts"
    }
    assert receipt["minimum_trustworthy_evidence_packet"]["status"] == "PASS"
    assert receipt["evidence_review_tier"] == "ORDINARY_MINIMUM"
    assert receipt["capital_chronicle_authority_verified"] is False


def test_breaking_brief_official_primary_fast_lane_skips_secondary_and_cc():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["regulatory_fiscal_event"] = {
        "required_evidence_capabilities": [
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "market_context_required": False,
        "article_mode": "straight_news",
        "freshness_policy": "event_24h",
        "freshness_requirements": {"max_age_hours": 36},
        "source_adapter_families": [
            "official_regulatory_fiscal",
            "public_secondary",
        ],
    }
    request = _request(
        story_type="regulatory_fiscal_event",
        required=["credible_event_confirmation", "basic_attributed_facts"],
        families=["official_regulatory_fiscal", "public_secondary"],
    )
    request["effective_article_mode"] = "BREAKING_BRIEF"
    request["resolved_article_mode"] = "BREAKING_BRIEF"
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    packet = _packet(request)
    packet["status"] = "PASS"
    packet["provided_evidence_capabilities"] = list(
        request["required_evidence_capabilities"]
    )
    packet["official_source_documents"][0]["canonical_content_text"] = " ".join(
        [
            "The agency's final rule takes effect today and the official release "
            "sets out the affected entities, implementation date, transition terms, "
            "and public compliance process."
        ]
        * 8
    )
    adapter = RollingXTargetedEvidenceAdapter(
        packet_loader=lambda _request: (_ for _ in ()).throw(
            AssertionError("breaking fast lane must not load Capital Chronicle")
        ),
        official_evidence_loader=lambda _request: packet,
        public_secondary_loader=lambda _request: (_ for _ in ()).throw(
            AssertionError("sufficient official primary must not trigger secondary")
        ),
        evaluation_as_of_utc=AS_OF,
        capability_registry=registry,
    )

    receipt = adapter(request)

    assert receipt["status"] == "PASS"
    assert receipt["capital_chronicle_authority_verified"] is False
    assert receipt["editorial_mode_contract"]["product_article_mode"] == (
        "BREAKING_BRIEF"
    )
    assert receipt["editorial_mode_contract"][
        "narrow_official_primary_fast_lane"
    ] is True
    assert receipt["evidence_acquisition_provenance"]["public_secondary"][
        "status"
    ] == "NOT_NEEDED_EVIDENCE_DEPTH_SUFFICIENT"


def test_supply_chain_request_routes_exact_eia_url_to_official_macro_loader():
    request = _request(story_type="supply_chain_event", article_mode="straight_news")
    request["story_context"] = {
        "leaf_summaries": ["EIA released its Short-Term Energy Outlook."],
        "official_source_url_bindings": [
            {
                "headline_id": "headline-1",
                "url": "https://www.eia.gov/outlooks/steo/",
            }
        ],
    }
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    official_calls = []

    def official_loader(effective_request):
        official_calls.append(effective_request)
        assert effective_request["source_adapter_families"] == ["official_macro"]
        assert effective_request["required_evidence_capabilities"] == []
        return {
            "status": "PASS",
            "provided_evidence_capabilities": ["official_or_owner_source"],
            "official_source_documents": [
                {
                    "document_id": "eia-steo",
                    "title": "EIA released its Short-Term Energy Outlook.",
                    "publisher": "U.S. Energy Information Administration",
                    "source_authority_class": "official_public_primary_source",
                    "source_url": "https://www.eia.gov/outlooks/steo/",
                    "published_at_utc": "2026-08-08T11:00:00Z",
                    "canonical_content_text": (
                        "EIA released its Short-Term Energy Outlook."
                    ),
                    "canonical_content_sha256": "c" * 64,
                    "public_claim_allowed": True,
                }
            ],
            "provenance": {"retrieved_at_utc": "2026-08-08T11:05:00Z"},
        }

    def secondary_loader(_effective_request):
        return {
            "status": "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "request_logical_hash": request["request_logical_hash"],
            },
            "evidence_documents": [],
            "provided_evidence_capabilities": [],
            "blockers": ["public_source_unavailable"],
        }

    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=official_loader,
        public_secondary_loader=secondary_loader,
        evaluation_as_of_utc=AS_OF,
    )(request)

    assert len(official_calls) == 1
    assert receipt["status"] == "PASS"
    assert receipt["minimum_trustworthy_evidence_packet"]["status"] == "PASS"
    assert receipt["minimum_trustworthy_evidence_packet"][
        "core_factual_proposition"
    ] == "EIA released its Short-Term Energy Outlook."
    assert receipt["evidence_documents"][0]["source_authority_class"] == (
        "official_public_primary_source"
    )


def test_official_evidence_cannot_substitute_for_market_authority():
    request = _request()
    packet = _packet(request)
    packet["status"] = "PASS"
    adapter = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )

    receipt = adapter(request)

    assert receipt["status"] == "BLOCKED"
    assert "capital_chronicle_evidence_root_not_bound" in receipt["blockers"]


def test_default_adapter_binds_bounded_official_primary_loader():
    adapter = RollingXTargetedEvidenceAdapter(evaluation_as_of_utc=AS_OF)

    assert isinstance(
        adapter._official_evidence_loader, BoundedOfficialPrimaryEvidenceLoader
    )


def test_official_acquisition_provenance_survives_into_receipt():
    request = _request(story_type="regulatory_fiscal_event", article_mode="straight_news")
    packet = _packet(request)
    packet["status"] = "BLOCKED"
    packet["blockers"] = ["official_source_locator_candidate_unavailable"]
    packet["provenance"] = {
        "locator_request_count": 1,
        "official_evidence_get_count": 1,
        "request_count": 2,
        "request_limit": 6,
    }
    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )(request)

    # A transport-level locator diagnostic no longer kills a claim when verified document bytes
    # are already present. The diagnostic remains visible in composite provenance.
    assert receipt["status"] == "PASS"
    assert receipt["evidence_acquisition_provenance"]["official"]["provenance"] == packet["provenance"]


def test_stale_official_primary_evidence_fails_closed():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["regulatory_fiscal_event"] = {
        "required_evidence_capabilities": ["official_document"],
        "market_context_required": False,
        "article_mode": "straight_news",
        "freshness_policy": "event_24h",
        "freshness_requirements": {"max_age_hours": 24},
        "source_adapter_families": ["official_regulatory_fiscal"],
    }
    request = _request(
        story_type="regulatory_fiscal_event",
        required=["official_document"],
        families=["official_regulatory_fiscal"],
    )
    request["capital_chronicle_numeric_or_analytical_authority_required"] = False
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    packet = _packet(request)
    packet["status"] = "PASS"
    packet["provided_evidence_capabilities"] = ["official_document"]
    packet["official_source_documents"][0]["published_at_utc"] = "2026-08-01T00:00:00Z"
    adapter = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
        capability_registry=registry,
    )

    receipt = adapter(request)

    assert receipt["status"] == "BLOCKED"
    assert "official_evidence_document_0_stale_or_future" in receipt["blockers"]


def test_stale_official_depth_is_excluded_before_bounded_secondary_enrichment():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["regulatory_fiscal_event"] = {
        "required_evidence_capabilities": ["official_document"],
        "market_context_required": False,
        "article_mode": "straight_news",
        "freshness_policy": "event_24h",
        "freshness_requirements": {"max_age_hours": 24},
        "source_adapter_families": ["official_regulatory_fiscal", "public_secondary"],
    }
    request = _request(
        story_type="regulatory_fiscal_event",
        required=["official_document"],
        families=["official_regulatory_fiscal", "public_secondary"],
    )
    request["story_context"] = {
        "leaf_summaries": ["Agency publishes current rule implementation update"],
    }
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    official = _packet(request)
    official["status"] = "PASS"
    official["provided_evidence_capabilities"] = ["official_document"]
    official["official_source_documents"][0].update(
        {
            "title": "Agency publishes current rule implementation update",
            "published_at_utc": "2026-08-01T00:00:00Z",
            "canonical_content_text": " ".join(["stale official detail"] * 120),
        }
    )
    enrichment_requests = []

    def secondary_loader(enrichment_request):
        enrichment_requests.append(enrichment_request)
        return {
            "status": "PASS",
            "rolling_x_story_binding": {
                "cluster_id": request["cluster_id"],
                "headline_ids": request["headline_ids"],
                "request_logical_hash": request["request_logical_hash"],
            },
            "evidence_documents": [
                {
                    "document_id": "fresh-professional-report",
                    "title": "Agency publishes current rule implementation update",
                    "publisher": "Reuters",
                    "source_identity": "reuters.com",
                    "source_authority_class": "reputable_secondary_source",
                    "source_url": "https://www.reuters.com/world/current-rule-update/",
                    "reader_source_url": "https://www.reuters.com/world/current-rule-update/",
                    "published_at_utc": "2026-08-08T11:00:00Z",
                    "canonical_content_sha256": "e" * 64,
                    "canonical_content_text": " ".join(
                        ["current implementation detail from the public report"] * 45
                    ),
                    "public_claim_allowed": True,
                }
            ],
            "provided_evidence_capabilities": ["official_document"],
            "provenance": {"retrieved_at_utc": AS_OF},
            "blockers": [],
        }

    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: official,
        public_secondary_loader=secondary_loader,
        evaluation_as_of_utc=AS_OF,
        capability_registry=registry,
    )(request)

    assert len(enrichment_requests) == 1
    context = enrichment_requests[0]["evidence_enrichment_context"]
    assert context["requested"] is True
    assert context["existing_evidence_substance"]["usable_content_words"] == 0
    assert receipt["status"] == "PASS"
    assert [row["document_id"] for row in receipt["evidence_documents"]] == [
        "fresh-professional-report"
    ]
    assert receipt["evidence_acquisition_provenance"]["public_secondary"][
        "enrichment_requested"
    ] is True
    assert receipt["evidence_substance"]["enough_for_useful_article"] is True


def test_fresh_professional_article_can_carry_ordinary_data_brief_when_official_page_is_undated():
    request = _request(story_type="data_release", article_mode="straight_news")
    request["story_context"] = {
        "leaf_summaries": ["EIA published its August Short-Term Energy Outlook."],
        "official_source_url_bindings": [
            {
                "headline_id": "headline-1",
                "url": "https://www.eia.gov/outlooks/steo/",
                "feed_published_at_utc": "2026-08-08T11:00:00Z",
                "feed_publisher_handle": "financialjuice",
                "feed_source_platform": "x_cdp_list_latest_tweets_timeline",
            }
        ],
        "public_source_url_bindings": [
            {
                "headline_id": "headline-1",
                "url": "https://www.eia.gov/outlooks/steo/",
                "feed_published_at_utc": "2026-08-08T11:00:00Z",
                "feed_publisher_handle": "financialjuice",
                "feed_source_platform": "x_cdp_list_latest_tweets_timeline",
            }
        ],
    }
    request["request_logical_hash"] = _logical_hash(
        {key: value for key, value in request.items() if key != "request_logical_hash"}
    )
    official = {
        "status": "PASS",
        "provided_evidence_capabilities": ["official_release"],
        "official_source_documents": [
            {
                "document_id": "eia-steo",
                "title": "Short-Term Energy Outlook",
                "publisher": "U.S. Energy Information Administration",
                "source_authority_class": "official_public_primary_source",
                "source_url": "https://www.eia.gov/outlooks/steo/",
                "published_at_utc": None,
                "canonical_content_text": "EIA Short-Term Energy Outlook",
                "canonical_content_sha256": "c" * 64,
                "public_claim_allowed": True,
            }
        ],
        "provenance": {"retrieved_at_utc": AS_OF},
    }
    secondary = {
        "status": "BLOCKED",
        "rolling_x_story_binding": {
            "cluster_id": request["cluster_id"],
            "headline_ids": request["headline_ids"],
            "request_logical_hash": request["request_logical_hash"],
        },
        "evidence_documents": [],
        "provided_evidence_capabilities": [],
        "provenance": {"retrieved_at_utc": AS_OF},
        "blockers": ["public_source_published_timestamp_unavailable"],
    }

    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: official,
        public_secondary_loader=lambda _request: secondary,
        evaluation_as_of_utc=AS_OF,
    )(request)

    assert receipt["status"] == "PASS"
    assert [row["document_id"] for row in receipt["evidence_documents"]] == ["eia-steo"]
    assert receipt["minimum_trustworthy_evidence_packet"][
        "core_factual_proposition"
    ] == "Short-Term Energy Outlook"
    assert receipt["evidence_documents"][0]["freshness_timestamp_source"] == (
        "EXACT_BOUND_PROFESSIONAL_FEED"
    )
    assert receipt["evidence_documents"][0][
        "professional_feed_grants_factual_authority"
    ] is False


def test_straight_news_company_and_data_official_packets_need_no_cc_authority():
    for story_type in ("company_sector_event", "data_release"):
        request = _request(story_type=story_type, article_mode="straight_news")
        packet = _packet(request)
        packet["status"] = "PASS"
        packet["provided_evidence_capabilities"] = list(
            request["required_evidence_capabilities"]
        )
        adapter = RollingXTargetedEvidenceAdapter(
            official_evidence_loader=lambda _request, value=packet: value,
            evaluation_as_of_utc=AS_OF,
        )

        receipt = adapter(request)

        assert receipt["status"] == "PASS"
        assert receipt["capital_chronicle_authority_verified"] is False
        assert request["capital_chronicle_numeric_or_analytical_authority_required"] is False


def test_company_standard_analysis_can_narrow_to_official_facts_without_cc_claims():
    request = _request(story_type="company_sector_event", article_mode="analysis")
    packet = _packet(request)
    packet["status"] = "PASS"
    adapter = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )

    receipt = adapter(request)

    assert receipt["status"] == "PASS"
    assert request["capital_chronicle_numeric_or_analytical_authority_required"] is False
    assert receipt["capital_chronicle_authority_verified"] is False


def test_llm_labeled_document_cannot_satisfy_official_primary_evidence():
    request = _request(
        story_type="regulatory_fiscal_event", article_mode="straight_news"
    )
    packet = _packet(request)
    packet["status"] = "PASS"
    packet["provided_evidence_capabilities"] = list(
        request["required_evidence_capabilities"]
    )
    packet["official_source_documents"][0]["source_authority_class"] = (
        "llm_generated_text"
    )
    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: packet,
        evaluation_as_of_utc=AS_OF,
    )(request)

    assert receipt["status"] == "BLOCKED"
    assert any("official_primary_source_authority" in row for row in receipt["blockers"])


def test_public_secondary_budget_exception_preserves_stable_sanitized_code():
    request = _request(story_type="physical_event", article_mode="straight_news")
    receipt = RollingXTargetedEvidenceAdapter(
        public_secondary_loader=lambda _request: (_ for _ in ()).throw(
            RuntimeError("public_source_request_budget_exhausted")
        ),
        evaluation_as_of_utc=AS_OF,
    )(request)

    secondary = receipt["evidence_acquisition_provenance"]["public_secondary"]
    assert receipt["status"] == "BLOCKED"
    assert secondary["blockers"] == ["public_source_request_budget_exhausted"]


def test_official_budget_exception_preserves_stable_sanitized_code():
    request = _request(story_type="data_release", article_mode="straight_news")
    receipt = RollingXTargetedEvidenceAdapter(
        official_evidence_loader=lambda _request: (_ for _ in ()).throw(
            RuntimeError("official_source_request_budget_exhausted")
        ),
        evaluation_as_of_utc=AS_OF,
    )(request)

    official = receipt["evidence_acquisition_provenance"]["official"]
    assert receipt["status"] == "BLOCKED"
    assert official["blockers"] == ["official_source_request_budget_exhausted"]
