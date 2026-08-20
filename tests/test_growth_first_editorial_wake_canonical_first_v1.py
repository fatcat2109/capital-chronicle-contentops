from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from live_contentops.claim_evidence_contract_v1 import build_claim_evidence_contract
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor
from live_contentops.daily_app_supervisor_v1 import (
    build_bootstrap_editorial_window_policy,
)
from live_contentops.editorial_portfolio_v1 import (
    CANONICAL_EDITORIAL_MODE_LADDER,
    DECISION_QUIET_DAY_USEFUL,
    PublishedArticleRef,
)
from live_contentops.preselection_intelligence_v1 import apply_preselection_intelligence
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    validate_generated_article,
)
from live_contentops.source_capability_registry_v2 import editorial_mode_contract


CANONICAL_MODES = (
    "BREAKING_BRIEF",
    "FOLLOW_UP_UPDATE",
    "STANDARD_NEWS_ANALYSIS",
    "CAPITAL_CHRONICLE_VIEW",
    "WHAT_THE_MARKET_IS_MISSING",
    "EVERGREEN_EXPLAINER",
    "DATA_OR_DOCUMENT_LENS",
    "WEEK_AHEAD_OR_WATCH",
)


def _request(claim: str) -> dict:
    return {
        "cluster_id": "growth-cluster",
        "headline_ids": ["growth-headline"],
        "effective_article_mode": "BREAKING_BRIEF",
        "story_context": {"leaf_summaries": [claim]},
    }


def _document(*, authority: str, claim: str, publisher: str) -> dict:
    return {
        "document_id": "growth-document",
        "title": claim,
        "publisher": publisher,
        "source_identity": publisher,
        "source_authority_class": authority,
        "source_url": "https://example.test/growth-document",
        "published_at_utc": "2026-08-20T02:00:00Z",
        "canonical_content_text": claim,
        "canonical_content_sha256": "a" * 64,
        "public_claim_allowed": True,
    }


def test_narrow_official_primary_breaking_fact_qualifies_without_extra_ceremony():
    claim = "The agency announced that the final rule takes effect today."
    contract = build_claim_evidence_contract(
        _request(claim),
        [
            _document(
                authority="official_public_primary_source",
                claim=claim,
                publisher="Public Agency",
            )
        ],
    )

    assert contract["status"] == "PASS"
    assert contract["supported_claim_count"] == 1
    assert contract["supported_claims"][0]["support_status"] == "SUPPORTED_PRIMARY"
    assert contract["supported_claims"][0]["evidence_document_ids"] == [
        "growth-document"
    ]
    assert contract["omitted_unsupported_claims"] == []


def test_interested_party_primary_does_not_prove_disputed_allegation():
    claim = "Example Company concealed material misconduct."
    contract = build_claim_evidence_contract(
        _request(claim),
        [
            _document(
                authority="first_party_public_source",
                claim=claim,
                publisher="Example Company",
            )
        ],
    )

    assert contract["status"] == "BLOCKED"
    assert contract["supported_claims"] == []
    assert contract["omitted_unsupported_claims"]


def test_quiet_day_low_delta_candidate_enters_useful_mode_ladder():
    now = datetime(2026, 8, 20, 5, 0, tzinfo=timezone.utc)
    prior = PublishedArticleRef(
        story_identity="prior-story",
        title="Prior policy explanation",
        published_at_utc=(now - timedelta(hours=2)).isoformat(),
        public_object_id="substack-prior",
        canonical_url_hash="b" * 64,
        content_hash="c" * 64,
        entities=("Policy Agency",),
        update_chain_identity="policy-chain",
        article_mode="BREAKING_BRIEF",
    )
    result = apply_preselection_intelligence(
        [
            {
                "cluster_id": "policy-chain",
                "rank": 1,
                "headline_ids": ["quiet-headline"],
                "article_mode": "EVERGREEN_EXPLAINER",
                "selection_case": "Explain how the policy process works on a quiet day.",
                "why_now": "Useful context remains timely.",
                "entities_topics": ["Policy Agency"],
                "leaf_summaries": ["Policy process context without a new material delta."],
            }
        ],
        published_corpus=[prior],
        cc_catalog={
            "stores": [],
            "store_count_discovered": 0,
            "discovery_complete": True,
            "root_exists": False,
        },
        now=now,
    )

    assert CANONICAL_EDITORIAL_MODE_LADDER == CANONICAL_MODES
    assert result["eligible_shortlist_count"] == 1
    assert result["held_shortlist_count"] == 0
    candidate = result["ranked_clusters"][0]
    assert candidate["editorial_classification"] == DECISION_QUIET_DAY_USEFUL
    assert candidate["resolved_article_mode"] == "EVERGREEN_EXPLAINER"
    assert candidate["growth_editorial_mode_resolution"][
        "quiet_day_utility_candidate"
    ] is True
    assert candidate["growth_editorial_mode_resolution"][
        "changes_evidence_or_permission_standards"
    ] is False


def test_house_view_contract_and_validator_keep_core_analyzer_boundary():
    for mode in ("CAPITAL_CHRONICLE_VIEW", "WHAT_THE_MARKET_IS_MISSING"):
        contract = editorial_mode_contract(mode)
        assert contract["qualitative_editorial_inference_permitted"] is True
        assert contract["editorial_inference_must_be_explicit"] is True
        assert contract["editorial_inference_authority_class"] == (
            "CONTENTOPS_QUALITATIVE_EDITORIAL_JUDGMENT"
        )
        assert contract["editorial_inference_is_core_analyzer_authority"] is False
        assert contract[
            "proprietary_numeric_forecast_scenario_regime_valuation_decision_forbidden_without_exact_cc_authority"
        ] is True

        context = {
            "cluster_id": "house-cluster",
            "headline_ids": ["house-headline"],
            "effective_article_mode": mode,
            "evidence_documents": [
                {
                    "document_id": "house-document",
                    "canonical_content_text": "The agency changed the incentive design.",
                }
            ],
            "capital_chronicle_authority_verified": False,
            "capital_chronicle_publication_authority": {},
            "publication_authorized_cc_projection": {},
        }
        article = {
            "title": "The incentive design deserves scrutiny",
            "substack_body_markdown": (
                "The agency changed the incentive design. Capital Chronicle’s view is that "
                "the bull case is too generous."
            ),
            "cluster_id": "house-cluster",
            "headline_ids": ["house-headline"],
            "evidence_document_ids": ["house-document"],
            "x_content_grants_factual_authority": False,
        }
        blockers = validate_generated_article(
            article, context=context, visual_asset_ids=[]
        )
        assert "house_view_editorial_inference_label_missing" not in blockers
        assert (
            "house_view_proprietary_analysis_requires_exact_publication_authorized_cc"
            in blockers
        )

        article["substack_body_markdown"] = (
            "The agency changed the incentive design. Capital Chronicle inference: "
            "the new structure may weaken compliance incentives."
        )
        clean = validate_generated_article(article, context=context, visual_asset_ids=[])
        assert "house_view_editorial_inference_label_missing" not in clean
        assert not any("proprietary_analysis" in value for value in clean)


def test_material_event_shadow_wake_is_idempotent_spacing_aware_and_zero_write(
    tmp_path,
):
    now = datetime(2026, 8, 20, 4, 30, tzinfo=timezone.utc)
    calls: list[dict] = []

    def controlled_cycle(**kwargs):
        calls.append(dict(kwargs))
        return {
            "classification": "NO_PUBLICATION",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode="SHADOW_ONLY",
        clock=lambda: now,
        newsroom_cycle=controlled_cycle,
    )
    supervisor._run_continuous_intake_housekeeping = lambda _now: {
        "material_event_due": False,
        "llm_or_provider_calls": 0,
    }
    first_metadata = {
        "material_event_due": True,
        "new_material_event_count": 1,
        "new_material_event_identity": "stable-material-event",
        "new_headline_ids": ["material-headline"],
        "new_headline_source_refs": ["material-source"],
        "update_chain_identities": ["material-chain"],
    }

    first = supervisor.tick(now=now, materiality_metadata=first_metadata)
    duplicate = supervisor.tick(now=now, materiality_metadata=first_metadata)
    update_chain_duplicate = supervisor.tick(
        now=now,
        materiality_metadata={
            **first_metadata,
            "new_material_event_identity": "rewritten-material-event-identity",
            "new_headline_ids": ["rewritten-material-headline"],
            "new_headline_source_refs": ["rewritten-material-source"],
        },
    )

    assert first["windows_dispatched"] == 1
    assert first["newsroom_cycle_invocations"] == 1
    assert first["material_event_wake"]["wake_execution_scope"] == (
        "SHADOW_NO_PUBLIC_WRITE"
    )
    assert first["material_event_wake"]["wake_eligibility"]["eligible"] is True
    assert calls[0]["publication_enabled"] is False
    assert first["public_write_performed"] is False
    assert duplicate["material_event_wake"]["window_id"] == first[
        "material_event_wake"
    ]["window_id"]
    assert duplicate["material_event_wake"]["duplicate_update_chain_suppressed"] is True
    assert duplicate["windows_dispatched"] == 0
    assert update_chain_duplicate["material_event_wake"]["window_id"] == first[
        "material_event_wake"
    ]["window_id"]
    assert update_chain_duplicate["material_event_wake"][
        "duplicate_update_chain_suppressed"
    ] is True
    assert update_chain_duplicate["windows_dispatched"] == 0
    assert len(calls) == 1

    distinct = supervisor.tick(
        now=now + timedelta(minutes=5),
        materiality_metadata={
            **first_metadata,
            "new_material_event_identity": "distinct-material-event",
            "new_headline_ids": ["distinct-headline"],
            "update_chain_identities": ["distinct-chain"],
        },
    )
    assert distinct["material_event_wake"]["wake_eligibility"] == {
        "eligible": False,
        "reason": "MINIMUM_CYCLE_SPACING_ACTIVE",
    }
    assert distinct["windows_dispatched"] == 0
    assert len(calls) == 1
    with supervisor._store.get_read_only_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM work_items "
            "WHERE target_surface='daily_app_material_event_window'"
        ).fetchone()[0]
    assert count == 2  # one executed identity plus one distinct spacing-held identity

    saturated_calls: list[dict] = []
    saturated_supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "saturated-store.sqlite3",
        output_root=tmp_path / "saturated-out",
        operating_mode="SHADOW_ONLY",
        clock=lambda: now,
        newsroom_cycle=lambda **kwargs: (
            saturated_calls.append(dict(kwargs))
            or {
                "classification": "NO_PUBLICATION",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
        ),
        policy=replace(
            build_bootstrap_editorial_window_policy(),
            minimum_cycle_spacing_hours=0.0,
            material_event_daily_saturation_limit=1,
        ),
    )
    saturated_supervisor._run_continuous_intake_housekeeping = lambda _now: {
        "material_event_due": False,
        "llm_or_provider_calls": 0,
    }
    saturated_supervisor.tick(now=now, materiality_metadata=first_metadata)
    saturated = saturated_supervisor.tick(
        now=now + timedelta(minutes=5),
        materiality_metadata={
            **first_metadata,
            "new_material_event_identity": "saturated-material-event",
            "new_headline_ids": ["saturated-headline"],
            "update_chain_identities": ["saturated-chain"],
        },
    )
    assert saturated["material_event_wake"]["wake_eligibility"] == {
        "eligible": False,
        "reason": "MATERIAL_EVENT_DAILY_SATURATION_LIMIT",
    }
    assert saturated["windows_dispatched"] == 0
    assert len(saturated_calls) == 1


def test_due_unexecuted_scheduled_window_absorbs_material_priority_once(tmp_path):
    now = datetime(2026, 8, 20, 10, 15, tzinfo=timezone.utc)
    calls: list[dict] = []
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode="SHADOW_ONLY",
        clock=lambda: now,
        newsroom_cycle=lambda **kwargs: (
            calls.append(dict(kwargs))
            or {
                "classification": "NO_PUBLICATION",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
        ),
    )
    supervisor._run_continuous_intake_housekeeping = lambda _now: {
        "material_event_due": False,
        "llm_or_provider_calls": 0,
    }
    metadata = {
        "material_event_due": True,
        "new_material_event_count": 1,
        "new_material_event_identity": "routine-collision-event",
        "new_headline_ids": ["routine-collision-headline"],
        "new_headline_source_refs": ["routine-collision-source"],
        "update_chain_identities": ["routine-collision-chain"],
    }

    first = supervisor.tick(now=now, materiality_metadata=metadata)
    priority_id = first["material_event_wake"]["window_id"]

    assert first["material_event_wake"]["wake_eligibility"]["eligible"] is False
    assert first["material_event_wake"]["wake_eligibility"]["reason"] == (
        "CURRENTLY_DUE_SCHEDULED_OPPORTUNITY_AVAILABLE"
    )
    assert first["windows_dispatched"] == 1
    assert first["newsroom_cycle_invocations"] == 1
    assert first["public_write_performed"] is False
    assert len(calls) == 1
    assert calls[0]["run_id"] != priority_id
    assert calls[0]["publication_enabled"] is False
    assert calls[0]["material_event_priority"]["priority_ids"] == [priority_id]
    assert supervisor._store.get_work_item(priority_id)["current_state"] == "REJECTED"
    with supervisor._store.get_read_only_connection() as connection:
        material_reasons = {
            str(row["reason_code"])
            for row in connection.execute(
                "SELECT reason_code FROM transition_events WHERE work_item_id=?",
                (priority_id,),
            ).fetchall()
        }
        material_opportunities = connection.execute(
            "SELECT COUNT(*) FROM work_items "
            "WHERE target_surface='daily_app_material_event_window'"
        ).fetchone()[0]
        scheduled_opportunities = connection.execute(
            "SELECT COUNT(*) FROM work_items "
            "WHERE target_surface='daily_app_editorial_window'"
        ).fetchone()[0]
    assert material_reasons == {
        "WORK_ITEM_INITIALIZATION",
        "MATERIAL_EVENT_PRIORITY_CONSUMED",
    }
    assert material_opportunities == 1
    assert scheduled_opportunities == 1

    second = supervisor.tick(
        now=now + timedelta(minutes=5),
        materiality_metadata=metadata,
    )

    assert second["material_event_wake"]["window_id"] == priority_id
    assert second["material_event_wake"]["duplicate_update_chain_suppressed"] is True
    assert second["windows_dispatched"] == 0
    assert second["newsroom_cycle_invocations"] == 0
    assert second["public_write_performed"] is False
    assert len(calls) == 1
    with supervisor._store.get_read_only_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM work_items "
            "WHERE target_surface='daily_app_material_event_window'"
        ).fetchone()[0] == 1


def test_terminal_scheduled_window_in_grace_does_not_block_later_material_wake(
    tmp_path,
):
    scheduled_now = datetime(2026, 8, 20, 10, 15, tzinfo=timezone.utc)
    calls: list[dict] = []
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode="SHADOW_ONLY",
        clock=lambda: scheduled_now,
        newsroom_cycle=lambda **kwargs: (
            calls.append(dict(kwargs))
            or {
                "classification": "NO_PUBLICATION",
                "public_write_performed": False,
                "unknown_write_detected": False,
            }
        ),
        policy=replace(
            build_bootstrap_editorial_window_policy(),
            minimum_cycle_spacing_hours=0.25,
        ),
    )
    supervisor._run_continuous_intake_housekeeping = lambda _now: {
        "material_event_due": False,
        "llm_or_provider_calls": 0,
    }

    scheduled = supervisor.tick(
        now=scheduled_now,
        materiality_metadata={"material_event_due": False},
    )
    assert scheduled["windows_dispatched"] == 1
    scheduled_run_id = calls[0]["run_id"]
    assert supervisor._store.get_work_item(scheduled_run_id)[
        "current_state"
    ] == "REJECTED"

    later = scheduled_now + timedelta(hours=1, minutes=5)
    material = supervisor.tick(
        now=later,
        materiality_metadata={
            "material_event_due": True,
            "new_material_event_count": 1,
            "new_material_event_identity": "post-terminal-material-event",
            "new_headline_ids": ["post-terminal-headline"],
            "new_headline_source_refs": ["post-terminal-source"],
            "update_chain_identities": ["post-terminal-chain"],
        },
    )
    material_id = material["material_event_wake"]["window_id"]

    assert material["material_event_wake"]["wake_eligibility"]["eligible"] is True
    assert material["windows_dispatched"] == 1
    assert material["newsroom_cycle_invocations"] == 1
    assert material["public_write_performed"] is False
    assert len(calls) == 2
    assert calls[1]["run_id"] == material_id
    assert calls[1]["run_id"] != scheduled_run_id
    assert calls[1]["publication_enabled"] is False
