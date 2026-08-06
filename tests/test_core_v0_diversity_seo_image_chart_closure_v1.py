"""Focused tests for the CORE V0 diversity / SEO / visual / chart closure (SHADOW_ONLY).

Covers the Work Package D capabilities: the diversified governed evaluation corpus,
domain taxonomy and portfolio concentration, the complete SEO contract, the
rights/provenance-aware visual policy resolver, deterministic chart production, the
nine Tier-1 package contracts, canonical review, and durable replay.

Every case is historical governed evaluation material. No network, credential,
provider, browser, scheduler, dispatch, or public-write path is exercised.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.core_v0_closure_capabilities_v1 import (
    CONCENTRATION_DIMENSIONS,
    SEO_CONTRACT_FIELDS,
    apply_concentration_penalties,
    build_authorized_chart,
    build_portfolio_report,
    build_seo_contract,
    classify_case,
    evaluate_story_visuals,
    resolve_visual_policy,
    run_chart_methodology_qa,
    run_seo_contract_qa,
)
from live_contentops.core_v0_cohort_shadow_runner_v1 import (
    OPERATING_MODE,
    build_v5_cohort_snapshot,
    persist_cohort,
    run_cohort,
    verify_cohort_replay,
)
from live_contentops.core_v0_evaluation_corpus_v1 import (
    DOMAIN_FAMILIES,
    UNREVIEWED_ASSET,
    _load,
    _packet_from,
    build_evaluation_corpus,
    corpus_domain_coverage,
    load_authorized_prior_observations,
    load_governed_visual_assets,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    ALL_TIER1_PLATFORM_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

GENERIC_PACKET_PATH = (
    REPO_ROOT
    / "docs/automation/CONTENTOPS_VERIFIER_DERIVED_PERMISSION_GENERIC_CLAIM_PACKET_AND_CROSS_DOMAIN_EDITORIAL_SHADOW_V1"
    / "generic_v3_claim_packet_and_editorial_outcome.json"
)


@pytest.fixture(scope="module")
def corpus() -> dict:
    return build_evaluation_corpus(REPO_ROOT)


@pytest.fixture(scope="module")
def assets() -> list:
    return load_governed_visual_assets(REPO_ROOT)


@pytest.fixture(scope="module")
def priors() -> dict:
    return load_authorized_prior_observations(REPO_ROOT)


@pytest.fixture(scope="module")
def cohort(tmp_path_factory) -> dict:
    chart_dir = tmp_path_factory.mktemp("cohort_charts")
    return run_cohort(repo_root=REPO_ROOT, chart_output_dir=chart_dir)


# --------------------------------------------------------------------------- corpus


def test_corpus_covers_every_required_domain_family(corpus):
    coverage = corpus_domain_coverage(corpus)

    assert coverage["all_families_represented"] is True
    assert set(coverage["cases_by_family"]) == set(DOMAIN_FAMILIES)
    assert corpus["domain_family_count"] == len(DOMAIN_FAMILIES)


def test_corpus_is_governed_historical_material_not_current_news(corpus):
    assert corpus["fabricated_content"] is False
    assert corpus["material_class"] == "historical_evaluation_material"
    assert corpus["governed_artifact_paths"]
    for case in corpus["cases"]:
        assert case["presented_as_current_news"] is False


def test_corpus_includes_both_lanes_and_every_required_outcome_shape(corpus):
    lanes = {str(case["lane"]) for case in corpus["cases"]}
    dispositions = {str(case["expected_disposition"]) for case in corpus["cases"]}

    assert lanes == {"newsroom", "capital_chronicle"}
    assert "ELIGIBLE_CANDIDATE" in dispositions
    assert "DUPLICATE_OR_LOW_DELTA" in dispositions
    assert "HISTORICAL_NOT_CURRENT" in dispositions
    assert "VISUAL_RIGHTS_BLOCKED" in dispositions


def test_corpus_is_deterministic():
    first = build_evaluation_corpus(REPO_ROOT)
    second = build_evaluation_corpus(REPO_ROOT)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ------------------------------------------------------------------------ taxonomy


def test_classify_case_emits_every_concentration_dimension(corpus):
    row = classify_case(corpus["cases"][0])

    for dimension in CONCENTRATION_DIMENSIONS:
        assert dimension in row


def test_portfolio_report_measures_every_dimension(corpus):
    report = build_portfolio_report(corpus["cases"], label="daily")

    assert set(report["dimensions"]) == set(CONCENTRATION_DIMENSIONS)
    for dimension in report["dimensions"].values():
        assert dimension["distinct_values"] >= 1
        assert 0.0 < dimension["max_share"] <= 1.0


def test_concentration_penalties_reorder_but_never_add_a_case(corpus):
    report = build_portfolio_report(corpus["cases"], label="daily")
    eligible = [
        case
        for case in corpus["cases"]
        if str(case["expected_disposition"]) == "ELIGIBLE_CANDIDATE"
    ]

    penalties = apply_concentration_penalties(eligible=eligible, portfolio=report)

    assert len(penalties) == len(eligible)
    assert {row["case_id"] for row in penalties} == {
        str(case["case_id"]) for case in eligible
    }


# --------------------------------------------------------------------------- visual


def test_visual_policy_resolver_is_story_type_specific():
    data_release = resolve_visual_policy("data_release")
    official_action = resolve_visual_policy("official_action")

    assert data_release["required_visual_count"] >= 1
    assert data_release["text_only_permitted"] is False
    assert official_action["text_only_permitted"] is True
    assert (
        data_release["permitted_visual_strategy"]
        != official_action["permitted_visual_strategy"]
    )
    for policy in (data_release, official_action):
        assert policy["rights_requirements"]
        assert policy["platform_adaptation_required"] is True


def test_rights_cleared_assets_produce_a_passing_visual_composition(assets):
    result = evaluate_story_visuals(story_type="data_release", assets=assets)

    assert result["status"] == "PASS"
    assert result["blockers"] == []
    assert result["rights_audit"]["assets_rights_cleared"] >= 1


def test_text_only_story_passes_without_any_asset():
    result = evaluate_story_visuals(story_type="official_action", assets=[])

    assert result["status"] == "PASS"
    assert result["blockers"] == []


def test_unreviewed_rights_asset_is_withheld_and_blocks(assets):
    unreviewed = dict(assets[0])
    unreviewed["asset_id"] = "img_generic_fallback"
    unreviewed["rights_status"] = UNREVIEWED_ASSET["rights_status"]

    result = evaluate_story_visuals(story_type="supply_chain_event", assets=[unreviewed])

    assert result["status"] == "BLOCK"
    assert "img_generic_fallback" in {
        row["asset_id"] for row in result["withheld_assets"]
    }


def test_committed_visual_assets_carry_full_provenance(assets):
    required = ("source_page_url", "publisher", "rights_status", "sha256")
    assert assets
    for asset in assets:
        for field in required:
            assert asset.get(field), f"{asset.get('asset_id')} missing {field}"


# ---------------------------------------------------------------------------- chart


@pytest.fixture(scope="module")
def chart_manifest(priors, tmp_path_factory) -> dict:
    packet = _packet_from(_load(GENERIC_PACKET_PATH))
    return build_authorized_chart(
        chart_id="ust_curve",
        title="U.S. Treasury Par Yield Curve: 2026-07-13",
        packet=packet,
        authorized_claim_ids=packet["governed_claim_graph"]["approved_claim_ids"],
        prior_observations=priors,
        output_dir=tmp_path_factory.mktemp("charts"),
    )


def test_chart_passes_methodology_qa(chart_manifest):
    qa = run_chart_methodology_qa(chart_manifest)

    assert qa["status"] == "PASS"
    assert qa["failed_checks"] == []
    assert qa["checks_run"] >= 20


def test_chart_binds_full_method_metadata(chart_manifest):
    methodology = chart_manifest["methodology"]

    for field in (
        "metric_definitions",
        "series_ids",
        "units",
        "observation_times_utc",
        "release_times_utc",
        "frequency",
        "sample_period",
        "transformations",
        "seasonal_adjustment",
        "annualization",
        "revision_state",
        "partial_period_state",
        "missing_data_handling",
        "source_note",
        "renderer",
        "generator",
    ):
        assert methodology.get(field) not in (None, "", [], {}), field
    assert chart_manifest["chart_sha256"]
    assert chart_manifest["depicts_real_scene_as_photograph"] is False


def test_chart_never_creates_new_analysis(chart_manifest):
    for flag in (
        "forecast_created",
        "probability_created",
        "market_regime_created",
        "scenario_created",
        "analytical_calculation_created",
        "values_originated_by_contentops",
    ):
        assert chart_manifest[flag] is False, flag


def test_chart_plots_one_unit_on_one_axis(chart_manifest):
    units = {str(series["unit"]) for series in chart_manifest["series"]}

    assert len(units) == 1
    assert chart_manifest["methodology"]["single_unit_axis"] is True
    assert chart_manifest["series_count"] == len(chart_manifest["series"])


def test_a_differently_united_claim_is_excluded_and_disclosed(chart_manifest):
    assert chart_manifest["excluded_claim_count"] >= 1
    assert chart_manifest["methodology"]["excluded_claim_disclosure"]
    for excluded in chart_manifest["methodology"]["excluded_claims"]:
        assert excluded["unit"] != chart_manifest["methodology"]["chart_unit"]


def test_chart_values_come_only_from_authorized_claims(chart_manifest):
    packet = _packet_from(_load(GENERIC_PACKET_PATH))
    approved = set(packet["governed_claim_graph"]["approved_claim_ids"])

    for series in chart_manifest["series"]:
        assert str(series["claim_id"]) in approved
        assert series["value_origin"] == "COPIED_VERBATIM_FROM_GOVERNED_PACKET"


def test_chart_is_byte_deterministic(priors, tmp_path):
    packet = _packet_from(_load(GENERIC_PACKET_PATH))
    kwargs = dict(
        chart_id="ust_curve",
        title="U.S. Treasury Par Yield Curve: 2026-07-13",
        packet=packet,
        authorized_claim_ids=packet["governed_claim_graph"]["approved_claim_ids"],
        prior_observations=priors,
    )
    first = build_authorized_chart(output_dir=tmp_path / "a", **kwargs)
    second = build_authorized_chart(output_dir=tmp_path / "b", **kwargs)

    assert first["chart_sha256"] == second["chart_sha256"]


# ------------------------------------------------------------------------------ seo


@pytest.fixture(scope="module")
def seo_contract(assets, chart_manifest) -> dict:
    return build_seo_contract(
        headline="Official U.S. Treasury Par Yield Curve Record",
        summary="The Treasury published its official daily par yield curve record.",
        body_sections=[{"heading": "What the record shows", "text": "x"}],
        citations=[
            {"source_document_id": "d1", "url": "https://home.treasury.gov/x"}
        ],
        domain_family="rates_or_credit",
        story_type="data_release",
        target_reader="institutional rates desk",
        primary_intent="treasury par yield curve today",
        secondary_intent="2s10s spread value",
        keyword_cluster=["treasury yield curve"],
        canonical_angle="exact official record",
        competitive_differentiation="exact governed values",
        update_timestamp_utc="2026-07-15T22:30:00Z",
        visual_assets=assets,
        chart_manifest=chart_manifest,
        internal_links=[{"anchor": "Treasury curve", "path": "/rates/treasury-curve"}],
    )


def test_seo_contract_is_complete(seo_contract):
    qa = run_seo_contract_qa(seo_contract)

    assert qa["status"] == "COMPLETE"
    assert qa["missing_fields"] == []
    assert qa["fields_present"] == qa["fields_required"] == len(SEO_CONTRACT_FIELDS)


def test_seo_qa_never_claims_observed_search_success(seo_contract):
    qa = run_seo_contract_qa(seo_contract)

    assert qa["observed_search_success_claimed"] is False


def test_seo_measurement_hooks_start_empty(seo_contract):
    hooks = seo_contract["measurement_hooks"]

    assert hooks["collection_state"] == "NOT_COLLECTED_SHADOW_ONLY_NO_PUBLIC_OBJECT"
    for name, value in hooks.items():
        if name == "collection_state":
            continue
        assert value is None, name


def test_seo_qa_reports_an_incomplete_contract_truthfully(seo_contract):
    incomplete = dict(seo_contract)
    incomplete["meta_description"] = ""

    qa = run_seo_contract_qa(incomplete)

    assert qa["status"] != "COMPLETE"
    assert "meta_description" in qa["missing_fields"]


# --------------------------------------------------------------------------- cohort


def test_cohort_runs_in_shadow_only_with_zero_live_action(cohort):
    assert cohort["operating_mode"] == OPERATING_MODE
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


def test_both_input_lanes_produce_a_passing_package(cohort):
    assert sorted(cohort["lanes_with_passing_package"]) == [
        "capital_chronicle",
        "newsroom",
    ]
    assert cohort["outcome_counts"]["eligible_review_passed"] >= 2


def test_cohort_records_the_required_truthful_non_publishing_outcomes(cohort):
    counts = cohort["outcome_counts"]

    assert counts["no_publication"] >= 1
    assert counts["duplicate_or_low_delta"] >= 1
    assert counts["visual_rights_blocked"] >= 1


def test_every_case_has_an_explicit_outcome_and_terminal_state(cohort):
    assert len(cohort["cases"]) == cohort["corpus"]["case_count"]
    for case in cohort["cases"]:
        assert case["outcome"]
        assert case["terminal_state"]


def test_only_a_review_passing_case_reaches_review_ready(cohort):
    for case in cohort["cases"]:
        if case["outcome"] != "PACKAGE_REVIEW_PASSED":
            assert case["terminal_state"] != "REVIEW_READY"


def test_passing_cases_use_the_canonical_review_engine(cohort):
    assert cohort["review_engine"] == (
        "editorial_review_orchestrator_v2.run_editorial_review"
    )
    for case in cohort["cases"]:
        if case["outcome"] == "PACKAGE_REVIEW_PASSED":
            assert case["review_result"] == "PASS"
            assert case["review_role_count"] == 8
            assert case["review_blocked_roles"] == []


def test_passing_cases_have_nine_explicit_tier1_outcomes(cohort):
    passing = [c for c in cohort["cases"] if c["outcome"] == "PACKAGE_REVIEW_PASSED"]

    assert passing
    assert len(ALL_TIER1_PLATFORM_IDS) == 9
    for case in passing:
        platform = (case.get("package") or {}).get("platform") or {}
        assert platform["explicit_outcome_count"] == len(ALL_TIER1_PLATFORM_IDS)


def test_instagram_fails_closed_without_a_rights_cleared_asset(cohort):
    blocked_anywhere = False
    for case in cohort["cases"]:
        platform = (case.get("package") or {}).get("platform") or {}
        blocked = {
            row["platform_id"] for row in platform.get("blocked_destinations") or []
        }
        if "instagram_business" not in blocked:
            continue
        blocked_anywhere = True
        assert case.get("visual_status") != "PASS" or not (
            (case.get("package") or {}).get("visual") or {}
        ).get("assets")

    assert blocked_anywhere, "no case exercised the Instagram fail-closed path"


def test_at_least_one_chart_and_one_non_chart_visual_pass(cohort):
    charted = [c for c in cohort["cases"] if c.get("chart_qa_status") == "PASS"]
    visual_passed = [c for c in cohort["cases"] if c.get("visual_status") == "PASS"]

    assert charted
    assert visual_passed


# -------------------------------------------------------------- durable + snapshot


def test_cohort_persists_and_replays_exactly(cohort, tmp_path):
    store = ContentOpsDurableStore(tmp_path / "cohort.sqlite")
    durable = persist_cohort(store, cohort)

    replay = verify_cohort_replay(store, durable["work_item_ids"])

    assert replay["all_replays_valid"] is True
    assert replay["work_items_replayed"] == len(cohort["cases"])
    for row in replay["replays"]:
        assert row["verification_status"] == "PASS"


def test_reopening_the_store_replays_the_same_terminal_states(cohort, tmp_path):
    store_path = tmp_path / "reopen.sqlite"
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
    for work_item_id, state in before.items():
        assert reopened.get_work_item(work_item_id)["current_state"] == state
    for row in replay["replays"]:
        assert row["replayed_state"] == before[row["work_item_id"]]


def test_v5_snapshot_is_generated_from_the_real_run(cohort, tmp_path):
    store = ContentOpsDurableStore(tmp_path / "snapshot.sqlite")
    durable = persist_cohort(store, cohort)
    replay = verify_cohort_replay(store, durable["work_item_ids"])

    snapshot = build_v5_cohort_snapshot(
        cohort=cohort, durable=durable, replay=replay
    )

    assert snapshot["generated_from_real_run"] is True
    assert snapshot["operating_mode"] == OPERATING_MODE
    assert snapshot["tier1_destination_count"] == 9
    assert len(snapshot["cases"]) == len(cohort["cases"])
    assert snapshot["shadow_readback"]["public_objects_created"] == 0
    assert snapshot["shadow_readback"]["public_urls"] == []
