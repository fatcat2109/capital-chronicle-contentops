from __future__ import annotations

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.mvp_canary_acceptance_v1 import (
    build_mvp_canary_launch_gate_record,
    classify_institutional_edge_blockers,
    evaluate_mvp_canary_editorial_gate,
    evaluate_mvp_canary_minimum_useful_floor,
)
from live_contentops.tier1_editorial_quality_v1 import (
    LLM_REVIEW_CHECKS,
    audit_tier1_article,
)
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    _run_bounded_rolling_x_editorial_cycle,
    _validate_rolling_x_release_inputs,
)
from live_contentops.mvp_canary_acceptance_v1 import MVP_CANARY_ACCEPTANCE_PROFILE
from scripts.run_v1_current_multi_frontier_floor_rehearsal import _summary


def _brief() -> dict:
    body = """The Federal Reserve published a current balance-sheet release on Thursday. The release is the source for this narrow update, and the article makes no claim beyond that publication event.

Readers should care because the release updates the official record used to track the central bank's balance sheet. This brief does not infer a market move, a policy shift, or a forecast from the document.

The practical next step is to read the release itself and compare any later analysis with the source record. The narrow scope is deliberate: current evidence supports the publication event, not a broader conclusion."""
    return {
        "title": "Federal Reserve Publishes Current Balance-Sheet Release",
        "subtitle": "A narrow source-grounded brief on the latest official record.",
        "substack_body_markdown": body,
        "effective_article_mode": "BREAKING_BRIEF",
        "article_generation_method": "ROUTED_LLM_GROUNDED_ARTICLE",
        "quote_source_records": [],
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS",
            "risk_tier": "ORDINARY",
            "core_factual_proposition": "Federal Reserve published current balance-sheet release",
            "source_url": "https://example.com/federal-reserve-release",
            "evidence_document_id": "document-1",
        },
        "source_bindings": [
            {"source_id": "source-1", "evidence_document_id": "document-1"}
        ],
        "source_binding_ids_referenced": ["source-1"],
        "evidence_document_ids": ["document-1"],
        "x_content_grants_factual_authority": False,
    }


def _hard_review(**overrides: bool) -> dict:
    checks = {name: True for name in LLM_REVIEW_CHECKS}
    checks.update(overrides)
    return {
        "status": "SUCCESS",
        "decision": "PASS",
        "checks": checks,
        "advisory_failed_checks": [name for name, value in overrides.items() if value is False],
    }


def test_quality_shortfalls_remain_visible_but_do_not_block_hard_safe_canary():
    article = _brief()
    standard = audit_tier1_article(article)
    assert standard["classification"] == "NEEDS_REVISION"
    assert "mode_declared" in standard["hard_editorial_blockers"]

    canary = evaluate_mvp_canary_editorial_gate(
        article=article,
        deterministic_review=standard,
        hard_factual_review=_hard_review(
            clear_news_peg=False,
            mode_consistent=False,
            reader_facing_prose=False,
        ),
    )
    assert canary["classification"] == "PASS"
    assert "mode_declared" in canary["quality_warnings"]
    assert "clear_news_peg" in canary["quality_warnings"]
    assert canary["quality_warnings_grant_factual_authority"] is False


def test_mvp_usefulness_reuses_mode_aware_reader_floor_instead_of_universal_brief_floor():
    breaking = evaluate_mvp_canary_minimum_useful_floor(_brief())
    assert breaking["classification"] == "PASS"
    assert breaking["mode_aware_floor_class"] == "CONCISE_UPDATE"
    assert breaking["mode_aware_utility_floor"] == {
        "minimum_words": 60,
        "minimum_reader_sentences": 3,
    }

    analytical = {
        **_brief(),
        "effective_article_mode": "DATA_OR_DOCUMENT_LENS",
        "editorial_mode": "DOCUMENT_LENS",
    }
    blocked = evaluate_mvp_canary_minimum_useful_floor(analytical)
    assert blocked["classification"] == "BLOCKED_MINIMUM_USEFUL_FLOOR"
    assert blocked["mode_aware_floor_class"] == "DATA_RICH_OR_ANALYTICAL"
    assert blocked["mode_aware_utility_floor"] == {
        "minimum_words": 180,
        "minimum_reader_sentences": 6,
    }
    assert "minimum_reader_substance" in blocked["blockers"]


def test_mode_proportional_document_lens_can_pass_without_full_formatting_perfection():
    sentences = [
        "The official document records the agency decision, identifies the parties, and defines the proposal without converting that proposal into a completed transaction.",
        "Its itemized request gives readers the concrete scale of the package while preserving the document's distinction between a possible sale and a final agreement.",
        "The notice also supplies the notification date and transmittal identifier, which make the source record independently traceable for a later update.",
        "That procedural context matters because congressional notification is a documented step in the record, not proof that delivery, payment, or operational use has occurred.",
        "For readers, the useful analytical boundary is therefore the combination of stated scope, requested quantity, and formal status rather than an unsupported market or policy forecast.",
        "A subsequent official notice, contract record, or delivery disclosure would be the evidence needed to establish a later phase, and none is inferred here.",
        "This document-lens treatment keeps the factual record separate from analysis while explaining what the record changes, what it leaves open, and what would confirm the next step.",
        "The result is useful without claiming that the request fixes a delivery schedule, contract value, operational outcome, or broader strategic consequence that the accepted document does not establish.",
    ]
    article = {
        **_brief(),
        "effective_article_mode": "DATA_OR_DOCUMENT_LENS",
        "editorial_mode": "DOCUMENT_LENS",
        "substack_body_markdown": "\n\n".join(sentences),
    }
    result = evaluate_mvp_canary_minimum_useful_floor(article)
    assert result["classification"] == "PASS"
    assert result["checks"]["minimum_reader_substance"] is True
    assert result["reader_value_telemetry"]["formatting_targets_are_advisory"] is True


def test_factual_or_numeric_failure_can_never_be_downgraded_to_warning():
    article = _brief()
    canary = evaluate_mvp_canary_editorial_gate(
        article=article,
        deterministic_review=audit_tier1_article(article),
        hard_factual_review=_hard_review(no_fabricated_numbers=False),
    )
    assert canary["classification"] == "BLOCKED_HARD_GATE"
    assert "no_fabricated_numbers" in canary["hard_gate_blockers"]
    assert "no_fabricated_numbers" not in canary["quality_warnings"]


def test_institutional_integrity_is_hard_while_seo_perfection_is_warning():
    split = classify_institutional_edge_blockers(
        [
            "unsupported_causality",
            "numeric_source_binding_violation",
            "structured_data_packet_missing",
            "keyword_stuffing",
            "search_freshness_class_invalid",
        ]
    )
    assert split["hard_gate_blockers"] == [
        "numeric_source_binding_violation",
        "unsupported_causality",
    ]
    assert split["quality_warnings"] == [
        "keyword_stuffing",
        "search_freshness_class_invalid",
        "structured_data_packet_missing",
    ]


def test_unknown_institutional_validator_code_fails_closed():
    split = classify_institutional_edge_blockers(["future_validator_finding_v2"])
    assert split["hard_gate_blockers"] == ["future_validator_finding_v2"]
    assert split["quality_warnings"] == []


def test_one_canary_never_satisfies_4_32_or_authorizes_more_writes():
    editorial_gate = {
        "classification": "PASS",
        "quality_warnings": ["seo_title"],
        "standard_editorial_score": 71,
        "standard_seo_score": 58,
    }
    record = build_mvp_canary_launch_gate_record(
        editorial_gate=editorial_gate,
        worker_validation={"classification": "PASS_BOUND_XHIGH_EDITORIAL_RETURN"},
        derivative_destinations=V1_REQUIRED_DERIVATIVE_DESTINATIONS,
        publication_plan_destinations=V1_REQUIRED_PUBLICATION_DESTINATIONS,
        jit_preflight={"status": "READY", "all_required_destinations_ready": True},
        rights_or_zero_media_pass=True,
    )
    assert record["classification"] == "CANARY_READY_FOR_OWNER_PUBLIC_WRITE_GATE"
    assert record["owner_public_write_grant_present"] is False
    assert record["authorizes_second_article"] is False
    assert record["authorizes_automation_enablement"] is False
    assert record["satisfies_post_launch_4_32_throughput_gate"] is False


def test_jit_or_unknown_write_failure_blocks_canary_ready_classification():
    record = build_mvp_canary_launch_gate_record(
        editorial_gate={"classification": "PASS"},
        worker_validation={"classification": "PASS_BOUND_XHIGH_EDITORIAL_RETURN"},
        derivative_destinations=V1_REQUIRED_DERIVATIVE_DESTINATIONS,
        publication_plan_destinations=V1_REQUIRED_PUBLICATION_DESTINATIONS,
        jit_preflight={"status": "HOLD", "all_required_destinations_ready": False},
        rights_or_zero_media_pass=True,
        unknown_write_count=1,
    )
    assert record["classification"] == "BLOCKED_MVP_CANARY_LAUNCH_GATE"
    assert "jit_nine_surface_identity_and_readiness" in record["hard_gate_blockers"]
    assert "unknown_write_zero" in record["hard_gate_blockers"]


def test_opt_in_canary_profile_changes_only_quality_disposition_not_normal_validation():
    article = _brief()
    normal = _run_bounded_rolling_x_editorial_cycle(
        article=article,
        media_assets=(),
        editorial_reviewer=lambda _article: (_ for _ in ()).throw(
            AssertionError("ordinary hard review must stay deterministic")
        ),
        article_reviser=lambda *_args: (_ for _ in ()).throw(
            AssertionError("ordinary path must not invoke router revision")
        ),
    )
    assert normal["status"] == "NO_PUBLICATION"

    canary = _run_bounded_rolling_x_editorial_cycle(
        article=article,
        media_assets=(),
        editorial_reviewer=lambda _article: (_ for _ in ()).throw(
            AssertionError("ordinary hard review must stay deterministic")
        ),
        article_reviser=lambda *_args: (_ for _ in ()).throw(
            AssertionError("ordinary path must not invoke router revision")
        ),
        acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
    )
    assert canary["status"] == "PASS"
    assert "mode_declared" in canary["canary_quality_warnings"]
    assert canary["publication_authority_granted"] is False


def test_exhausted_canary_walk_is_not_misclassified_as_a_4_32_campaign():
    state = {
        "acceptance_profile": MVP_CANARY_ACCEPTANCE_PROFILE,
        "full_current_headline_count": 48,
        "evaluated_headline_ids": [f"headline-{index}" for index in range(48)],
        "qualified_article_records": [],
        "mvp_canary_artifact_records": [],
        "frontiers": [
            {
                "attempted_headline_ids": [f"headline-{frontier * 12 + index}" for index in range(12)],
                "exact_headline_identity_coverage": True,
            }
            for frontier in range(4)
        ],
        "pending_frontier": None,
    }
    summary = _summary(state)
    assert summary["classification"] == (
        "MVP_CANARY_CURRENT_WALK_EXHAUSTED_NO_ACCEPTED_EVIDENCE"
    )
    assert summary["daily_floor_is_post_launch_only"] is True
    assert summary["mvp_canary_does_not_count_toward_4_32"] is True


def test_release_validation_preserves_institutional_quality_warning_disposition():
    article = {
        **_brief(),
        "cluster_id": "cluster-1",
        "headline_ids": ["headline-1"],
        "institutional_edge_editorial_packet_sha256": "a" * 64,
        "institutional_edge_editorial_validation": {
            "classification": "NEEDS_REVISION",
            "blockers": ["structured_data_packet_missing"],
        },
    }
    viability = {
        "selected_cluster_id": "cluster-1",
        "selected_headline_ids": ["headline-1"],
        "selected_evidence": {
            "evidence_documents": [{"document_id": "document-1"}]
        },
    }
    canary_blockers = _validate_rolling_x_release_inputs(
        article=article,
        media_assets=(),
        viability=viability,
        acceptance_profile=MVP_CANARY_ACCEPTANCE_PROFILE,
    )
    assert "institutional_edge_editorial_validation_missing_or_blocked" not in canary_blockers

    normal_blockers = _validate_rolling_x_release_inputs(
        article=article,
        media_assets=(),
        viability=viability,
    )
    assert "institutional_edge_editorial_validation_missing_or_blocked" in normal_blockers
