"""Focused tests for the portfolio-selection and platform-visual-adaptation correction.

TASK_CONTENTOPS_CORE_V0_PORTFOLIO_SELECTION_AND_PLATFORM_VISUAL_ADAPTATION_CORRECTION_V1
— ``SHADOW_ONLY``.

Covers the three corrected defects: concentration-aware selection *before* production,
genuinely distinct daily and rolling windows, and canonical platform visual adaptation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.core_v0_cohort_shadow_runner_v1 import (
    DECISION_WINDOW_ID,
    DECISION_WINDOW_START_UTC,
    build_v5_cohort_snapshot,
    persist_cohort,
    run_cohort,
    verify_cohort_replay,
)
from live_contentops.core_v0_evaluation_corpus_v1 import (
    build_evaluation_corpus,
    load_accepted_publication_history,
    load_governed_visual_assets,
)
from live_contentops.core_v0_platform_visual_adaptation_v1 import (
    PLATFORM_VISUAL_SPECS,
    adapt_package_visuals,
    build_platform_visual_binding,
    select_source_asset,
)
from live_contentops.core_v0_portfolio_windows_v1 import (
    DEFERRED,
    PortfolioWindowError,
    base_editorial_rank,
    build_daily_portfolio_report,
    build_rolling_portfolio_report,
    decide_portfolio,
)
from live_contentops.core_v0_shadow_selection_calibration_policy_v1 import (
    CALIBRATION_STATE,
    POLICY_ID,
    POLICY_LOGICAL_HASH,
    ShadowCalibrationPolicyError,
    get_policy,
    policy_value,
    verify_policy_integrity,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    ALL_TIER1_PLATFORM_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def corpus() -> dict:
    return build_evaluation_corpus(REPO_ROOT)


@pytest.fixture(scope="module")
def history() -> list:
    return load_accepted_publication_history(REPO_ROOT)


@pytest.fixture(scope="module")
def assets() -> list:
    return load_governed_visual_assets(REPO_ROOT)


@pytest.fixture(scope="module")
def cohort(tmp_path_factory) -> dict:
    return run_cohort(
        repo_root=REPO_ROOT,
        chart_output_dir=tmp_path_factory.mktemp("charts"),
        derivative_output_dir=tmp_path_factory.mktemp("derivatives"),
    )


def _eligible(corpus: dict) -> list:
    return [
        case
        for case in corpus["cases"]
        if str(case["expected_disposition"]) == "ELIGIBLE_CANDIDATE"
    ]


def _ranked(cases: list) -> list:
    return [{"case_id": c["case_id"], "case": c, **base_editorial_rank(c)} for c in cases]


def _rolling(history: list, *, threshold: float = 0.34) -> dict:
    return build_rolling_portfolio_report(
        decision_window_id=DECISION_WINDOW_ID,
        prior_selected=history,
        decision_window_start_utc=DECISION_WINDOW_START_UTC,
        concentration_threshold=threshold,
    )


# --- 1. hard gates are unaffected by concentration configuration -------------------


def test_hard_gate_outcomes_do_not_move_when_concentration_config_changes(
    corpus, history
):
    eligible = _eligible(corpus)
    ranked = _ranked(eligible)
    baseline = {str(c["case_id"]) for c in eligible}

    for threshold in (0.10, 0.34, 0.90, 1.0):
        for penalty in (0.0, 12.0, 250.0):
            decision = decide_portfolio(
                decision_window_id="w",
                eligible=ranked,
                rolling_report=_rolling(history, threshold=threshold),
                penalty=penalty,
                defer_below_adjusted_score=0.0,
            )
            assert decision["eligible_count"] == len(eligible)
            decided = {str(row["case_id"]) for row in decision["decisions"]}
            assert decided == baseline, "diversity changed the eligible set"


def test_a_blocked_case_can_never_be_admitted_by_diversity(cohort):
    for case in cohort["cases"]:
        if case.get("hard_gate_failure") and case["outcome"] != "PACKAGE_REVIEW_BLOCKED":
            assert case["package_produced"] is False
            assert case.get("deferred_by_portfolio_concentration") is False
            assert case["outcome"] != DEFERRED


# --- 2. penalties are applied before package production ----------------------------


def test_penalties_are_applied_before_production(cohort):
    decision = cohort["portfolio_decision"]

    assert decision["penalties_applied_before_production"] is True
    for case in cohort["cases"]:
        portfolio = case.get("portfolio")
        if not portfolio:
            continue
        # Every produced package carries the disposition that authorised its production.
        if case.get("package_produced"):
            assert portfolio["disposition"] == "SELECTED"
        assert portfolio["base_score"] is not None
        assert portfolio["adjusted_score"] is not None


def test_every_penalty_records_dimension_value_amount_and_history_basis(cohort):
    applied = [
        penalty
        for row in cohort["portfolio_decision"]["decisions"]
        for penalty in row["penalties_applied"]
    ]
    assert applied
    for penalty in applied:
        assert penalty["dimension"]
        assert penalty["value"]
        assert penalty["penalty_amount"] > 0
        basis = penalty["prior_history_basis"]
        assert basis["rolling_report_logical_hash"]
        assert basis["prior_share"] is not None
        assert basis["prior_count"] is not None
        assert basis["history_window_start_utc"]
        assert basis["history_window_end_utc"]


# --- 3. an eligible case is genuinely reordered or deferred -------------------------


def test_rolling_concentration_reorders_an_eligible_case(cohort):
    reordered = cohort["portfolio_decision"]["reordered_case_ids"]

    assert reordered, "no eligible case was reordered by rolling concentration"
    for row in cohort["portfolio_decision"]["decisions"]:
        if row["case_id"] in reordered:
            assert row["base_rank"] != row["adjusted_rank"]
            assert row["concentration_penalty"] > 0


def test_changing_threshold_or_history_changes_a_disposition(corpus, history):
    ranked = _ranked(_eligible(corpus))

    with_history = decide_portfolio(
        decision_window_id="w",
        eligible=ranked,
        rolling_report=_rolling(history),
        defer_below_adjusted_score=0.0,
    )
    no_history = decide_portfolio(
        decision_window_id="w",
        eligible=ranked,
        rolling_report=build_rolling_portfolio_report(
            decision_window_id="w",
            prior_selected=[],
            decision_window_start_utc=DECISION_WINDOW_START_UTC,
        ),
        defer_below_adjusted_score=0.0,
    )
    relaxed = decide_portfolio(
        decision_window_id="w",
        eligible=ranked,
        rolling_report=_rolling(history, threshold=1.0),
        defer_below_adjusted_score=0.0,
    )

    assert with_history["deferred_case_ids"] != no_history["deferred_case_ids"]
    assert with_history["deferred_case_ids"] != relaxed["deferred_case_ids"]
    # Hard-gate eligibility is identical in all three.
    assert (
        with_history["eligible_count"]
        == no_history["eligible_count"]
        == relaxed["eligible_count"]
    )


def test_diversity_never_promotes_a_case(corpus, history):
    decision = decide_portfolio(
        decision_window_id="w",
        eligible=_ranked(_eligible(corpus)),
        rolling_report=_rolling(history),
        defer_below_adjusted_score=0.0,
    )
    for row in decision["decisions"]:
        assert row["adjusted_score"] <= row["base_score"]
        assert row["concentration_penalty"] >= 0


# --- 4. DEFER_FOR_PORTFOLIO_BALANCE produces no package ----------------------------


def test_deferred_case_produces_no_package_and_a_truthful_terminal_state(cohort):
    deferred = [c for c in cohort["cases"] if c["outcome"] == DEFERRED]

    assert deferred, "no case exercised the portfolio-defer path"
    for case in deferred:
        assert case["package_produced"] is False
        assert case.get("package") is None
        assert case["review_result"] is None
        assert case["terminal_state"] == "DEFERRED_FOR_PORTFOLIO_BALANCE"
        assert case["hard_gate_failure"] is False
        assert case["deferred_by_portfolio_concentration"] is True


# --- 5-7. real daily and rolling windows -------------------------------------------


def test_daily_and_rolling_reports_differ_in_boundary_membership_and_hash(cohort):
    daily = cohort["portfolio_daily"]
    rolling = cohort["portfolio_rolling"]

    assert daily["report_id"] != rolling["report_id"]
    assert daily["report_logical_hash"] != rolling["report_logical_hash"]
    assert set(daily["included_current_candidate_ids"]) != set(
        rolling["included_prior_selected_ids"]
    )
    assert daily["history_window_start_utc"] is None
    assert rolling["history_window_start_utc"]
    assert rolling["history_window_end_utc"]
    assert daily["basis"] != rolling["basis"]


def test_every_report_binds_the_required_window_metadata(cohort):
    for report in (cohort["portfolio_daily"], cohort["portfolio_rolling"]):
        for field in (
            "report_id",
            "decision_window_id",
            "included_current_candidate_ids",
            "included_prior_selected_ids",
            "excluded_ids",
            "exclusion_reasons",
            "basis",
            "report_logical_hash",
        ):
            assert field in report, field
        assert report["excluded_ids"]
        for case_id in report["excluded_ids"]:
            assert report["exclusion_reasons"][case_id]


def test_rolling_history_excludes_blocked_and_rejected_candidates(cohort):
    rolling = cohort["portfolio_rolling"]
    blocked_ids = {row["case_id"] for row in cohort["hard_gate_excluded"]}

    assert rolling["blocked_or_rejected_counted_as_published_history"] is False
    assert not (set(rolling["included_prior_selected_ids"]) & blocked_ids)
    for case_id in blocked_ids:
        assert case_id in rolling["exclusion_reasons"]


def test_rolling_history_refuses_a_non_accepted_disposition(history):
    rejected = [dict(history[0], disposition="PACKAGE_REVIEW_BLOCKED")]

    with pytest.raises(PortfolioWindowError):
        build_rolling_portfolio_report(
            decision_window_id="w",
            prior_selected=rejected,
            decision_window_start_utc=DECISION_WINDOW_START_UTC,
        )


def test_history_preserves_original_committed_dates(cohort, history):
    assert cohort["portfolio_rolling"]["historical_dates_preserved"] is True
    assert cohort["portfolio_rolling"]["presented_as_current_news"] is False
    for row in history:
        assert row["published_at_utc"].startswith("2026-07-13")
        assert row["presented_as_current_news"] is False


def test_selection_binds_the_exact_rolling_report_hash(cohort):
    rolling_hash = cohort["portfolio_rolling"]["report_logical_hash"]

    assert cohort["rolling_report_logical_hash_used_by_selection"] == rolling_hash
    assert cohort["portfolio_decision"]["rolling_report_logical_hash"] == rolling_hash
    for row in cohort["portfolio_decision"]["decisions"]:
        assert row["rolling_report_logical_hash"] == rolling_hash
        for penalty in row["penalties_applied"]:
            assert (
                penalty["prior_history_basis"]["rolling_report_logical_hash"]
                == rolling_hash
            )


# --- 8-11. platform visual adaptation ----------------------------------------------


REQUIRED_BINDING_FIELDS = (
    "platform_id",
    "source_asset_id",
    "source_asset_sha256",
    "derivative_role",
    "target_aspect_ratio",
    "target_width",
    "target_height",
    "crop_fit_or_padding_strategy",
    "safe_area",
    "text_density_limit_pct",
    "filename",
    "mime_type",
    "caption",
    "alt_text",
    "rights_provenance_reference",
    "source_note",
    "source_note_preservation_rule",
    "chart_label_preservation_rule",
    "derivative_generator",
    "derivative_generator_version",
    "derivative_sha256",
    "operating_mode",
)


def test_platform_visual_bindings_contain_all_required_metadata(cohort):
    bindings = [
        binding
        for case in cohort["cases"]
        for binding in ((case.get("package") or {}).get("visual_adaptation") or {}).get(
            "bindings"
        )
        or []
    ]
    assert bindings
    for binding in bindings:
        for field in REQUIRED_BINDING_FIELDS:
            assert binding.get(field) not in (None, "", {}), f"{binding['platform_id']}:{field}"
        assert binding["operating_mode"] == "SHADOW_ONLY"
        for flag in (
            "publication_authority",
            "dispatch_authority",
            "public_write_authority",
            "external_provider_used",
            "network_call_performed",
            "model_call_performed",
            "depicts_real_scene_as_photograph",
        ):
            assert binding[flag] is False, flag


def test_required_destinations_receive_a_real_derivative(cohort):
    produced = {
        binding["platform_id"]
        for case in cohort["cases"]
        for binding in ((case.get("package") or {}).get("visual_adaptation") or {}).get(
            "bindings"
        )
        or []
    }
    # Instagram, a landscape feed destination, and a chart-bearing destination.
    assert {"instagram_business", "linkedin", "substack_newsletter"} <= produced


def test_instagram_fails_closed_without_a_rights_cleared_derivative(tmp_path):
    result = adapt_package_visuals(
        platform_ids=["instagram_business", "linkedin"],
        assets=[],
        repo_root=REPO_ROOT,
        output_dir=tmp_path,
        caption="c",
        source_note="s",
    )
    blocked = {row["platform_id"] for row in result["blocked_destinations"]}

    assert "instagram_business" in blocked
    assert result["adapted_count"] == 0
    for row in result["blocked_destinations"]:
        assert row["image_fabricated_to_satisfy_platform"] is False
        assert row["derivative_produced"] is False


def test_an_unreviewed_rights_asset_is_never_adapted(assets, tmp_path):
    unreviewed = dict(assets[0])
    unreviewed["rights_status"] = "operator_review_required_search_image"

    assert select_source_asset(platform_id="instagram_business", assets=[unreviewed]) is None

    result = adapt_package_visuals(
        platform_ids=["instagram_business"],
        assets=[unreviewed],
        repo_root=REPO_ROOT,
        output_dir=tmp_path,
        caption="c",
        source_note="s",
    )
    assert result["adapted_count"] == 0
    assert result["blocked_count"] == 1


def test_derivatives_are_byte_identical_across_two_runs(assets, tmp_path):
    kwargs = dict(
        platform_id="instagram_business",
        asset=assets[0],
        repo_root=REPO_ROOT,
        caption="c",
        source_note="Source: U.S. Department of the Treasury.",
    )
    first = build_platform_visual_binding(output_dir=tmp_path / "a", **kwargs)
    second = build_platform_visual_binding(output_dir=tmp_path / "b", **kwargs)

    assert first["derivative_sha256"] == second["derivative_sha256"]
    assert first["binding_logical_hash"] == second["binding_logical_hash"]


def test_chart_labels_axes_and_source_notes_survive_adaptation(cohort):
    chart_bindings = [
        binding
        for case in cohort["cases"]
        for binding in ((case.get("package") or {}).get("visual_adaptation") or {}).get(
            "bindings"
        )
        or []
        if binding["source_modality"] in {"chart", "document_excerpt"}
    ]
    assert chart_bindings
    for binding in chart_bindings:
        # Contain-fit only: nothing is cropped, so no axis, legend, or source note can be
        # cut off by the adaptation.
        assert binding["crop_applied"] is False
        assert binding["pixels_cropped"] == 0
        assert binding["crop_fit_or_padding_strategy"] == "CONTAIN_WITH_PADDING_NO_CROP"
        assert (
            binding["chart_label_preservation_rule"]
            == "CONTAIN_FIT_ONLY_AXES_LEGENDS_UNCERTAINTY_AND_SOURCE_LABELS_RETAINED"
        )
        assert binding["source_note"]
        assert binding["scaled_width"] <= binding["target_width"]
        assert binding["scaled_height"] <= binding["target_height"]


def test_official_excerpts_are_not_turned_into_event_imagery(cohort):
    bindings = [
        binding
        for case in cohort["cases"]
        for binding in ((case.get("package") or {}).get("visual_adaptation") or {}).get(
            "bindings"
        )
        or []
    ]
    for binding in bindings:
        assert binding["source_transformed_into_event_imagery"] is False
        assert binding["depicts_real_scene_as_photograph"] is False
        assert binding["rights_provenance_reference"]["rights_status"]


def test_one_canonical_adaptation_path_covers_every_destination(cohort):
    assert set(PLATFORM_VISUAL_SPECS) == set(ALL_TIER1_PLATFORM_IDS)
    for case in cohort["cases"]:
        adaptation = (case.get("package") or {}).get("visual_adaptation")
        if not adaptation:
            continue
        assert adaptation["single_canonical_adaptation_path"] is True
        assert adaptation["all_destinations_have_explicit_outcome"] is True
        assert adaptation["explicit_outcome_count"] == len(ALL_TIER1_PLATFORM_IDS)


# --- 12-15. cohort, review, durability, zero-live ----------------------------------


def test_all_nine_tier1_outcomes_remain_explicit(cohort):
    produced = [c for c in cohort["cases"] if c.get("package_produced")]

    assert produced
    for case in produced:
        platform = case["package"]["platform"]
        assert platform["explicit_outcome_count"] == len(ALL_TIER1_PLATFORM_IDS) == 9
        assert platform["all_destinations_have_explicit_outcome"] is True


def test_both_lanes_still_pass_canonical_review(cohort):
    assert sorted(cohort["lanes_with_passing_package"]) == [
        "capital_chronicle",
        "newsroom",
    ]
    assert cohort["outcome_counts"]["eligible_review_passed"] >= 2


def test_durable_replay_and_restart_reconstruction_pass(cohort, tmp_path):
    store_path = tmp_path / "cohort.sqlite"
    store = ContentOpsDurableStore(store_path)
    durable = persist_cohort(store, cohort)
    before = {
        work_item_id: store.get_work_item(work_item_id)["current_state"]
        for work_item_id in durable["work_item_ids"]
    }
    del store

    reopened = ContentOpsDurableStore(store_path)
    replay = verify_cohort_replay(reopened, durable["work_item_ids"])

    assert replay["all_replays_valid"] is True
    assert replay["work_items_replayed"] == len(cohort["cases"])
    for work_item_id, state in before.items():
        assert reopened.get_work_item(work_item_id)["current_state"] == state
    assert "DEFERRED" in set(before.values())


def test_snapshot_exposes_the_corrected_portfolio_and_adaptation_surface(
    cohort, tmp_path
):
    store = ContentOpsDurableStore(tmp_path / "snap.sqlite")
    durable = persist_cohort(store, cohort)
    replay = verify_cohort_replay(store, durable["work_item_ids"])

    snapshot = build_v5_cohort_snapshot(cohort=cohort, durable=durable, replay=replay)

    assert snapshot["generated_from_real_run"] is True
    assert snapshot["portfolio_decision"]["deferred_case_ids"]
    assert snapshot["portfolio_daily"]["report_logical_hash"] != (
        snapshot["portfolio_rolling"]["report_logical_hash"]
    )
    assert snapshot["rolling_report_logical_hash_used_by_selection"]
    assert snapshot["platform_visual_adaptation"]["packages_adapted"] >= 1
    deferred = [c for c in snapshot["cases"] if c["portfolio_disposition"] == DEFERRED]
    assert deferred
    reordered = [c for c in snapshot["cases"] if c["rank_changed_by_concentration"]]
    assert reordered
    for case in snapshot["cases"]:
        if case["visual_adaptation_bindings"]:
            for binding in case["visual_adaptation_bindings"]:
                assert binding["derivative_sha256"]
                assert binding["crop_applied"] is False


def test_every_live_authority_flag_remains_false(cohort):
    for flag in (
        "publication_authority",
        "dispatch_authority",
        "public_write_authority",
        "network_call_performed",
        "credential_read_performed",
        "browser_or_cdp_action_performed",
        "scheduler_or_outbox_action_performed",
        "provider_call_performed",
        "public_write_performed",
        "upstream_write_performed",
        "approval_captured",
    ):
        assert cohort[flag] is False, flag
    assert cohort["external_cost"] == "NONE_NO_PAID_API_OR_MODEL_CALL"


# --- Owner override: CORE V0 SHADOW SELECTION CALIBRATION V1 ------------------------
#
# Two audit blockers were corrected under explicit owner authority dated 2026-08-06:
# the daily report's false temporal boundaries, and anonymous module-local selection
# weights. These tests hold both corrections in place.


def test_daily_window_binds_the_declared_decision_interval_not_event_times(cohort):
    """The audit blocker: a July 15 daily report spanning roughly 75 days of event time."""
    daily = cohort["portfolio_daily"]

    assert daily["window_start_utc"] == "2026-07-15T00:00:00Z"
    assert daily["window_end_utc"] == "2026-07-16T00:00:00Z"
    assert daily["window_bound_source"] == "EXPLICIT_DECLARED_DECISION_WINDOW"
    assert daily["window_interval_kind"] == "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE"

    # The committed regression took the boundaries from candidate event times.
    assert daily["window_start_utc"] != daily["candidate_event_time_min_utc"]
    assert daily["window_end_utc"] != daily["candidate_event_time_max_utc"]


def test_daily_window_retains_event_coverage_as_named_diagnostics(cohort):
    daily = cohort["portfolio_daily"]

    assert daily["candidate_event_time_min_utc"]
    assert daily["candidate_event_time_max_utc"]
    # The diagnostics stay truthful about the real spread of source events, and that
    # spread demonstrably reaches outside the one-day decision window.
    assert daily["candidate_event_time_min_utc"] < daily["candidate_event_time_max_utc"]
    assert daily["candidate_event_time_min_utc"] < daily["window_start_utc"]


def test_daily_report_identity_and_boundaries_are_mutually_consistent(cohort, corpus):
    daily = cohort["portfolio_daily"]

    assert daily["decision_window_id"] == DECISION_WINDOW_ID
    assert daily["report_id"] == "portfolio-daily-" + DECISION_WINDOW_ID
    assert daily["window_start_utc"].startswith(DECISION_WINDOW_ID)
    assert daily["report_logical_hash"]

    # The hash must cover the corrected boundaries, so changing the end moves it.
    shifted = build_daily_portfolio_report(
        decision_window_id=DECISION_WINDOW_ID,
        decision_window_start_utc=DECISION_WINDOW_START_UTC,
        decision_window_end_utc="2026-07-17T00:00:00Z",
        candidates=_eligible(corpus),
    )
    assert shifted["report_logical_hash"] != daily["report_logical_hash"]
    assert shifted["window_end_utc"] == "2026-07-17T00:00:00Z"


def test_daily_report_refuses_inconsistent_or_missing_decision_bounds(corpus):
    candidates = _eligible(corpus)

    # A window ID that disagrees with the declared start cannot be labelled truthfully.
    with pytest.raises(PortfolioWindowError):
        build_daily_portfolio_report(
            decision_window_id="2026-07-15",
            decision_window_start_utc="2026-07-20T00:00:00Z",
            decision_window_end_utc="2026-07-21T00:00:00Z",
            candidates=candidates,
        )

    # An empty or inverted interval fails closed rather than reporting a false span.
    with pytest.raises(PortfolioWindowError):
        build_daily_portfolio_report(
            decision_window_id="2026-07-15",
            decision_window_start_utc="2026-07-15T00:00:00Z",
            decision_window_end_utc="2026-07-15T00:00:00Z",
            candidates=candidates,
        )

    with pytest.raises(PortfolioWindowError):
        build_daily_portfolio_report(
            decision_window_id="2026-07-15",
            decision_window_start_utc="",
            decision_window_end_utc="2026-07-16T00:00:00Z",
            candidates=candidates,
        )


def test_calibration_policy_declares_its_full_required_identity():
    policy = get_policy()

    assert policy["policy_id"] == "CONTENTOPS_CORE_V0_SHADOW_SELECTION_CALIBRATION_V1"
    for field in (
        "schema_version",
        "policy_version",
        "owner",
        "authority_date",
        "operating_mode_ceiling",
        "values",
        "intended_evaluation_scope",
        "limitations",
        "live_use_prohibition",
        "policy_logical_hash",
    ):
        assert policy[field], field

    assert policy["authority_date"] == "2026-08-06"
    assert policy["operating_mode_ceiling"] == "SHADOW_ONLY"
    assert policy["authorized_for_live_publication"] is False
    assert policy["authorized_for_public_write_eligibility"] is False
    assert verify_policy_integrity()["integrity_verified"] is True


def test_calibration_policy_carries_the_exact_authorized_values():
    values = get_policy()["values"]

    assert values == {
        "packet_authorized_claim_weight": 15.0,
        "packet_numeric_claim_weight": 10.0,
        "packet_score_cap": 100.0,
        "rolling_concentration_threshold": 0.34,
        "concentration_penalty_per_concentrated_value": 12.0,
        "portfolio_balance_floor": 0.0,
    }


def test_calibration_policy_disclaims_factual_and_numeric_authority():
    limitations = get_policy()["limitations"]

    for disclaimed in (
        "NOT_FACTUAL_AUTHORITY",
        "NOT_ANALYTICAL_AUTHORITY",
        "NOT_MARKET_AUTHORITY",
        "NOT_ECONOMIC_AUTHORITY",
        "NOT_FORECASTING_AUTHORITY",
        "NOT_CAPITAL_CHRONICLE_NUMERIC_AUTHORITY",
    ):
        assert disclaimed in limitations, disclaimed


def test_policy_object_cannot_be_mutated_by_a_caller():
    get_policy()["values"]["packet_authorized_claim_weight"] = 999.0

    assert policy_value("packet_authorized_claim_weight") == 15.0
    assert verify_policy_integrity()["integrity_verified"] is True


def test_an_unauthorized_calibration_value_fails_closed():
    with pytest.raises(ShadowCalibrationPolicyError):
        policy_value("invented_editorial_priority_weight")


def test_packet_base_score_binds_the_policy_and_names_its_authority(corpus):
    packet_cases = [
        case for case in _eligible(corpus) if not case.get("newsroom_candidate")
    ]
    assert packet_cases, "expected governed-packet cases without the newsroom scorer"

    for case in packet_cases:
        rank = base_editorial_rank(case)
        assert rank["score_authority"] == "OWNER_AUTHORIZED_PROVISIONAL_CALIBRATION_POLICY"
        assert rank["calibration_state"] == CALIBRATION_STATE
        assert rank["calibration_policy_id"] == POLICY_ID
        assert rank["calibration_policy_logical_hash"] == POLICY_LOGICAL_HASH
        assert rank["calibration_policy_authorized_for_live_publication"] is False
        # The exact weights that produced the score are auditable from the record.
        assert rank["calibration_inputs_used"]["packet_authorized_claim_weight"] == 15.0
        assert rank["calibration_inputs_used"]["packet_numeric_claim_weight"] == 10.0
        # The anonymous "uncalibrated composition" wording no longer appears.
        assert rank["calibration_state"] != "UNCALIBRATED_GOVERNED_COUNT_COMPOSITION"


def test_packet_base_score_still_equals_the_previously_tested_behavior(corpus):
    """The override authorized these exact values to preserve already-tested behavior."""
    for case in _eligible(corpus):
        if case.get("newsroom_candidate"):
            continue
        authorized = int(case.get("authorized_claim_count") or 0)
        numeric = int(case.get("numeric_claim_count") or 0)
        expected = float(min(100.0, authorized * 15.0 + numeric * 10.0))
        assert base_editorial_rank(case)["base_score"] == round(expected, 8)


def test_accepted_governed_scorer_remains_the_authority_where_it_exists(cohort):
    """Where accepted governed scoring exists, no calibration weight composes the score."""
    scored = {
        row["case_id"]: row for row in cohort["portfolio_decision"]["decisions"]
    }
    newsroom = [
        row
        for row in scored.values()
        if row["base_score_source"]
        == "universal_news_candidate_fabric_v2.score_candidate"
    ]
    assert newsroom, "expected at least one case scored by the accepted governed scorer"

    for row in newsroom:
        assert row["base_score_authority"] == "ACCEPTED_GOVERNED_CANDIDATE_SCORER"


def test_every_penalty_and_disposition_binds_the_calibration_policy(cohort):
    decision = cohort["portfolio_decision"]

    assert decision["calibration_policy_id"] == POLICY_ID
    assert decision["calibration_policy_logical_hash"] == POLICY_LOGICAL_HASH
    assert decision["calibration_policy_operating_mode_ceiling"] == "SHADOW_ONLY"

    for row in decision["decisions"]:
        assert row["calibration_policy_id"] == POLICY_ID
        assert row["calibration_policy_logical_hash"] == POLICY_LOGICAL_HASH
        assert row["calibration_policy_authorized_for_live_publication"] is False
        assert row["adjusted_score"] is not None
        assert row["disposition"]


def test_cohort_run_publishes_the_policy_and_its_effective_values(cohort):
    assert cohort["selection_calibration_policy"]["policy_id"] == POLICY_ID
    assert cohort["selection_calibration_integrity"]["integrity_verified"] is True

    effective = cohort["selection_calibration_effective_values"]
    assert effective["rolling_concentration_threshold"] == 0.34
    assert effective["concentration_penalty_per_concentrated_value"] == 12.0
    assert effective["portfolio_balance_floor"] == 0.0
    # An unmodified run must not claim an override.
    assert not any(effective["overridden_for_this_run"].values())


def test_sensitivity_overrides_are_recorded_as_overrides_not_policy_changes(
    tmp_path_factory,
):
    """Work Package E may sweep these values; it must not silently restate the policy."""
    run = run_cohort(
        repo_root=REPO_ROOT,
        chart_output_dir=tmp_path_factory.mktemp("charts-sweep"),
        derivative_output_dir=tmp_path_factory.mktemp("derivatives-sweep"),
        concentration_penalty=30.0,
        portfolio_balance_floor=5.0,
    )
    effective = run["selection_calibration_effective_values"]

    assert effective["concentration_penalty_per_concentrated_value"] == 30.0
    assert effective["portfolio_balance_floor"] == 5.0
    assert (
        effective["overridden_for_this_run"][
            "concentration_penalty_per_concentrated_value"
        ]
        is True
    )
    assert effective["overridden_for_this_run"]["portfolio_balance_floor"] is True
    # The policy itself is unchanged and still authorizes the original values.
    assert (
        run["selection_calibration_policy"]["values"][
            "concentration_penalty_per_concentrated_value"
        ]
        == 12.0
    )
    assert (
        run["selection_calibration_policy"]["policy_logical_hash"] == POLICY_LOGICAL_HASH
    )
    # A harsher sweep still cannot admit a hard-gate failure.
    assert not (
        set(run["portfolio_decision"]["selected_case_ids"])
        & {row["case_id"] for row in run["hard_gate_excluded"]}
    )


def test_the_calibration_policy_never_grants_live_publication_authority(cohort):
    assert cohort["calibration_policy_authorized_for_live_publication"] is False
    assert cohort["selection_calibration_policy"]["live_use_prohibition"]
    assert cohort["publication_authority"] is False
    assert cohort["public_write_authority"] is False
    assert cohort["operating_mode"] == "SHADOW_ONLY"
