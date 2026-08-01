from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import live_contentops.eight_platform_substack_first_pipeline_v1 as pipeline

from live_contentops.cc_evidence_bridge_v2 import build_evidence_packet_from_cc_root, validate_evidence_packet
from live_contentops.distribution_identity_registry_v2 import load_identity_registry, validate_fresh_run_action, verify_distribution_identity
from live_contentops.editorial_review_orchestrator_v2 import run_editorial_review
from live_contentops.editorial_visual_research_v2 import GoogleImageSearchGroundingProvider, evaluate_visual_composition, validate_chart_methodology
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.generic_editorial_fabric_v2 import (
    evaluate_assignment_readiness,
    run_generic_database_preflight,
    run_generic_prepare_only,
)
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_platform_visual_expectation,
    resolve_story_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]
REAL_REQUEST = ROOT / "tests/fixtures/generic_fabric/real_cc_wti_analysis_request_v2.json"


def _fresh_packet() -> dict:
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "packet-fixture-001",
        "generated_at_utc": "2026-07-11T01:00:00Z",
        "as_of_utc": "2026-07-11T02:00:00Z",
        "story_window": {"hours": 24},
        "events": [{"event_time_utc": "2026-07-11T00:00:00Z"}],
        "headlines": [{"published_at_utc": "2026-07-11T00:10:00Z"}],
        "official_source_documents": [{"published_at_utc": "2026-07-11T00:00:00Z", "title": "Output returns toward pre-conflict levels", "summary": "Official source"}],
        "numeric_claims": [{"claim_id": "c1", "metric": "WTI", "value": 70, "unit": "usd_per_barrel", "observation_time_utc": "2026-07-11T01:30:00Z", "source_id": "cc", "source_artifact_ref": "state#WTI", "public_claim_allowed": True, "llm_numeric_authority": False}],
        "market_snapshots": [{"generated_at_utc": "2026-07-11T01:30:00Z", "market_session_state": "regular"}],
        "source_state": {"dqr_status": "ready"},
        "candidate_visual_inputs": [],
        "citation_map": {"c1": ["state#WTI"]},
        "provenance": {},
        "public_claim_permissions": {"decision": "ALLOW"},
        "blockers": [],
        "validation_blockers": [],
    }


def _asset(asset_id: str, role: str, modality: str, dimension: str, series=()) -> dict:
    return {"asset_id": asset_id, "role": role, "modality": modality, "evidence_dimension": dimension, "source_page_url": "https://official.example/item", "publisher": "Official owner", "publication_date": "2026-07-11", "rights_status": "public_domain", "caption": "Grounded caption", "alt_text": "Grounded visual", "width": 1400, "height": 900, "sha256": (asset_id[0] * 64), "article_section": asset_id, "relevance_rationale": "Supports the assigned evidence role", "supports_headline": role == "lead_contextual", "is_logo": False, "is_avatar": False, "is_thumbnail": False, "is_synthetic": False, "is_manipulated": False, "underlying_series_ids": list(series), **({"chart_title": f"{asset_id} through July 11", "quantitative_method": {"metric_definition": asset_id, "units": "index", "frequency": "daily", "sample_window": "30 sessions", "transformation_owner": "Capital Chronicle", "calculation": "indexed levels", "partial_period": False}} if modality == "chart" else {})}


def test_real_cc_bridge_prefers_story_scoped_publication_authority_without_global_dqr_override():
    cc_root = Path(r"A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion")
    if not cc_root.exists():
        pytest.skip("local ingestion repo unavailable")
    packet = build_evidence_packet_from_cc_root(cc_root)
    assert packet["status"] == "PASS_PUBLICATION_AUTHORIZED"
    assert packet["public_claim_permissions"]["decision"] == "ALLOW"
    assert packet["source_state"]["dqr_status"] == "BLOCKED"
    assert packet["source_state"]["global_dqr_reporting_allowed"] is False
    assert packet["source_state"]["story_scoped_reporting_allowed"] is True
    assert packet["governed_contract"]["mode"] == "story_scoped_publication_evidence_v1"
    assert packet["governed_contract"]["global_dqr_override"] is False
    assert packet["bridge_safety"] == {
        "source_repo_modified": False,
        "secret_files_read": False,
        "network_call_made": False,
        "database_open_mode": "packet_read_only",
        "legacy_state_fallback_used": False,
    }
    assert not validate_evidence_packet(packet)
    assert packet["events"]
    assert packet["numeric_claims"]
    assert all(row["public_claim_allowed"] is True for row in packet["numeric_claims"])
    assert "contentops_publication" in packet["public_claim_permissions"]["consumer_class"]


def test_governed_bridge_does_not_treat_candidate_consumers_as_reporting_permission():
    from live_contentops.cc_evidence_bridge_v2 import _has_public_reporting_permission

    assert not _has_public_reporting_permission([
        {"allowed_consumers": ["point_in_time_candidate", "bounded_outcome_candidate"]}
    ])
    assert _has_public_reporting_permission([
        {"allowed_consumers": ["contentops_publication"]}
    ])


def test_generic_database_preflight_blocks_before_any_write_adapter(tmp_path):
    packet = _fresh_packet()
    packet["public_claim_permissions"]["decision"] = "BLOCK"
    packet["blockers"] = ["governed_reporting_permission_not_granted"]
    packet["headlines"] = []
    packet["official_source_documents"][0]["source_url"] = None
    packet["events"][0]["public_claim_allowed"] = False
    packet["numeric_claims"][0]["public_claim_allowed"] = False
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    result = run_generic_database_preflight(
        output_dir=tmp_path / "out",
        evidence_packet_path=packet_path,
    )
    assert result["classification"] == "BLOCKED_GENERIC_DATABASE_PREFLIGHT"
    assert result["publication_eligible"] is False
    assert result["public_write_performed"] is False
    assert result["browser_or_cdp_used"] is False
    assert result["platform_adapter_called"] is False
    assert "no_governed_headline_candidates" in result["blockers"]


def test_assignment_readiness_never_uses_topic_fallback():
    packet = _fresh_packet()
    decision = evaluate_assignment_readiness(packet)
    assert decision["selection_method"] == "governed_packet_only_no_topic_fallback"
    assert decision["selected_story"] is None
    assert decision["decision"] == "BLOCK"


def test_packet_and_registry_json_schemas_validate():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/capital_chronicle_content_evidence_packet_v2.schema.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(_fresh_packet())
    assert load_source_capability_registry()["schema_version"].endswith(".v2")
    assert load_identity_registry()["schema_version"].endswith(".v2")


def test_freshness_modes_and_market_snapshot_policy():
    packet = _fresh_packet()
    for mode in ("straight_news", "analysis"):
        decision = evaluate_freshness(packet, {"article_mode": mode, "market_sensitive": True, "fresh_material_delta": mode == "analysis"})
        assert decision["decision"] == "PASS"
    stale = json.loads(json.dumps(packet))
    stale["as_of_utc"] = "2026-07-15T02:00:00Z"
    assert evaluate_freshness(stale, {"article_mode": "straight_news", "market_sensitive": True})["decision"] == "BLOCK"
    assert evaluate_freshness(stale, {"article_mode": "explainer", "market_sensitive": False, "title": "Latest oil explainer"})["decision"] == "BLOCK"


def test_visual_diversity_rights_and_methodology_regressions():
    diverse = [_asset("lead", "lead_contextual", "official_photo", "physical"), _asset("price", "primary_quantitative_chart", "chart", "price", ["WTI"]), _asset("map", "map_geography", "map", "geography")]
    assert evaluate_visual_composition(diverse)["status"] == "PASS"
    same_series = [_asset("lead", "lead_contextual", "chart", "price", ["WTI"]), _asset("two", "primary_quantitative_chart", "chart", "price", ["WTI"]), _asset("three", "cross_asset_chart", "chart", "price", ["WTI"])]
    decision = evaluate_visual_composition(same_series)
    assert "underlying_series_overused:WTI:3" in decision["blockers"]
    mislabeled = _asset("vol", "primary_quantitative_chart", "chart", "risk", ["WTI"])
    mislabeled["chart_title"] = "WTI realized volatility"
    mislabeled["quantitative_method"]["calculation"] = "rolling average absolute daily move"
    assert "average_absolute_move_mislabeled_as_volatility" in validate_chart_methodology(mislabeled)
    partial = _asset("annual", "primary_quantitative_chart", "chart", "range", ["WTI"])
    partial["chart_title"] = "WTI annual range 2026"
    partial["quantitative_method"]["partial_period"] = True
    assert "partial_period_not_explicitly_labeled" in validate_chart_methodology(partial)
    weak = _asset("weak", "lead_contextual", "official_photo", "physical")
    weak.update({"rights_status": "unknown", "is_thumbnail": True})
    assert evaluate_visual_composition([weak, _asset("p", "primary_quantitative_chart", "chart", "price", ["WTI"]), _asset("m", "map_geography", "map", "geography")])["status"] == "BLOCK"
    charts_only = [_asset("lead", "lead_contextual", "chart", "price", ["WTI"]), _asset("p", "primary_quantitative_chart", "chart", "price", ["WTI"]), _asset("x", "cross_asset_chart", "chart", "cross", ["YIELD"])]
    assert "physical_or_geopolitical_story_requires_contextual_nonprice_visual" in evaluate_visual_composition(charts_only, story_type="geopolitical_event")["blockers"]


def test_editorial_regression_corpus_blocks_rc_defects_and_unapproved_claims():
    packet = _fresh_packet()
    article = {"title": "Output Returns to Pre-War Levels", "rendered_body": "The relevant transmission channel is Reopened transit. This manifest-bound chart proves it.", "claim_ids_used": ["invented"], "numeric_claims_from_llm": True, "quantitative_blockers": ["partial_period_not_explicitly_labeled"], "hard_truncation_used": False}
    visual = {"status": "BLOCK", "blockers": ["underlying_series_overused:WTI:3"]}
    review = run_editorial_review(request={"story_type": "geopolitical_event"}, packet=packet, article=article, freshness_decision={"decision": "PASS", "blockers": []}, visual_decision=visual, structured_reviewer=lambda *_: {"decision": "PASS", "publication_authority": False})
    joined = " ".join(review["blockers"])
    for expected in ("pre_conflict_to_pre_war", "manifest-bound", "awkward_templated", "unapproved_claim", "llm_numeric_authority", "partial_period", "underlying_series_overused"):
        assert expected in joined


def test_identity_registry_accepts_persona_and_founder_but_blocks_drift():
    registry = load_identity_registry()
    assert verify_distribution_identity("discord", "The Macro Pigeon", registry)["status"] == "PASS"
    assert verify_distribution_identity("linkedin", "Jim Pham", registry)["identity_class"] == "founder_led_personal_distribution"
    assert verify_distribution_identity("discord", "Capital Chronicle", registry)["status"] == "BLOCK_WRONG_ACCOUNT_OR_PERSONA"


def test_fresh_run_integrity_blocks_historical_linkedin_edit_and_empty_threads_parent():
    linkedin = validate_fresh_run_action(platform="linkedin", fresh_run=True, action="edit_existing_post", story_id="oil-20260711", existing_story_id="fed-20260710")
    assert linkedin["status"] == "BLOCK"
    assert "fresh_linkedin_story_cannot_edit_historical_activity" in linkedin["blockers"]
    threads = validate_fresh_run_action(platform="threads", fresh_run=True, action="reply", story_id="oil-20260711", parent_id="")
    assert threads["status"] == "BLOCK"


def test_generic_cross_asset_prose_requires_claim_ids():
    packet = _fresh_packet()
    article = {"title": "Oil context", "rendered_body": "Cross assets moved.", "claim_ids_used": [], "cross_asset_assertions": ["Dollar and yields repriced"], "cross_asset_claim_ids": [], "quantitative_blockers": [], "hard_truncation_used": False}
    review = run_editorial_review(request={"story_type": "market_move"}, packet=packet, article=article, freshness_decision={"decision": "PASS", "blockers": []}, visual_decision={"status": "PASS", "blockers": []}, structured_reviewer=lambda *_: {"decision": "PASS", "publication_authority": False})
    assert "generic_cross_asset_assertions_without_evidence" in review["blockers"]


def test_structured_final_review_fails_closed_when_missing_or_claiming_authority():
    base = dict(request={"story_type": "market_move"}, packet=_fresh_packet(), article={"title": "x", "rendered_body": "As-of analysis.", "claim_ids_used": [], "quantitative_blockers": [], "hard_truncation_used": False}, freshness_decision={"decision": "PASS", "blockers": []}, visual_decision={"status": "PASS", "blockers": []})
    assert "structured_adversarial_review_unavailable" in run_editorial_review(**base, structured_reviewer=None)["blockers"]
    bad = run_editorial_review(**base, structured_reviewer=lambda *_: {"decision": "PASS", "publication_authority": True})
    assert "structured_adversarial_review_failed_or_claimed_authority" in bad["blockers"]


@pytest.mark.parametrize(
    ("story_type", "caller_mode"),
    [
        ("policy_decision", None),
        ("data_release", None),
        ("geopolitical_event", "straight_news"),
        ("market_move", None),
        ("regulatory_fiscal_event", "straight_news"),
        ("company_sector_event", None),
    ],
)
def test_six_generalized_story_families_resolve_without_topic_hardcoding(story_type, caller_mode):
    request = {"story_type": story_type}
    if caller_mode:
        request["article_mode"] = caller_mode
    decision = resolve_story_capabilities(request, load_source_capability_registry())
    assert decision["status"] == "PASS"
    assert decision["required_evidence_capabilities"]
    assert decision["visual_roles"]


def test_registry_mode_is_explicit_for_data_release_and_analysis_packages():
    registry = load_source_capability_registry()
    assert resolve_story_capabilities({"story_type": "data_release"}, registry)["article_mode"] == "data_release"
    for source_family in ("federal_reserve_fomc", "sec_edgar", "usgs_comcat"):
        assert resolve_story_capabilities({"source_family_id": source_family}, registry)["article_mode"] == "analysis"


def test_caller_mode_is_preserved_when_registry_has_no_mode_and_missing_mode_fails_closed():
    registry = load_source_capability_registry()
    preserved = resolve_story_capabilities(
        {"story_type": "geopolitical_event", "article_mode": "straight_news"}, registry
    )
    assert preserved["status"] == "PASS"
    assert preserved["article_mode"] == "straight_news"
    assert preserved["article_mode_source"] == "caller"
    unresolved = resolve_story_capabilities({"story_type": "geopolitical_event"}, registry)
    assert unresolved["status"] == "BLOCK"
    assert unresolved["article_mode"] == ""
    assert unresolved["blockers"] == ["article_mode_unresolved"]


def test_caller_mode_mismatch_with_explicit_registry_policy_fails_closed():
    decision = resolve_story_capabilities(
        {"story_type": "policy_decision", "article_mode": "straight_news"},
        load_source_capability_registry(),
    )
    assert decision["status"] == "BLOCK"
    assert "article_mode_mismatch_with_capability" in decision["blockers"]


def test_invalid_caller_mode_does_not_fill_an_undeclared_registry_mode():
    decision = resolve_story_capabilities(
        {"story_type": "geopolitical_event", "article_mode": "generic_analysis"},
        load_source_capability_registry(),
    )
    assert decision["status"] == "BLOCK"
    assert decision["blockers"] == ["caller_article_mode_invalid"]


def test_market_sensitivity_and_snapshot_requirement_are_independent():
    registry = deepcopy(load_source_capability_registry())
    registry["story_types"]["physical_event"]["market_sensitive"] = True
    registry["story_types"]["physical_event"]["market_snapshot_required"] = False
    decision = resolve_story_capabilities({"story_type": "physical_event"}, registry)
    assert decision["status"] == "PASS"
    assert decision["market_sensitive"] is True
    assert decision["market_snapshot_required"] is False


@pytest.mark.parametrize(
    ("source_family_id", "story_type", "market_snapshot_required"),
    [
        ("federal_reserve_fomc", "policy_decision", True),
        ("sec_edgar", "company_sector_event", True),
        ("usgs_comcat", "physical_event", False),
    ],
)
def test_source_family_capabilities_derive_mode_and_market_sensitivity(
    source_family_id, story_type, market_snapshot_required
):
    decision = resolve_story_capabilities(
        {"source_family_id": source_family_id},
        load_source_capability_registry(),
    )
    assert decision["status"] == "PASS"
    assert decision["story_type"] == story_type
    assert decision["article_mode"] == "analysis"
    assert decision["market_snapshot_required"] is market_snapshot_required
    assert decision["market_sensitive"] is market_snapshot_required
    assert decision["freshness_requirements"]["requires_market_snapshot"] is market_snapshot_required


def test_usgs_physical_event_does_not_require_market_snapshot():
    capability = resolve_story_capabilities(
        {"source_family_id": "usgs_comcat", "article_mode": "analysis"},
        load_source_capability_registry(),
    )
    request = {
        "article_mode": capability["article_mode"],
        "market_sensitive": capability["market_snapshot_required"],
        "fresh_material_delta": True,
    }
    packet = _fresh_packet()
    packet["numeric_claims"] = []
    packet["market_snapshots"] = []
    decision = evaluate_freshness(packet, request)
    assert "market_sensitive_story_snapshot_stale_or_missing" not in decision["blockers"]
    assert "market_sensitive_story_ingest_stale_or_missing" not in decision["blockers"]


def test_long_form_and_text_only_visual_policies_are_distinct():
    registry = load_source_capability_registry()
    long_form = resolve_platform_visual_expectation(
        platform_id="substack_newsletter",
        content_surface="newsletter_note",
        variant_mode="manual_export",
        registry=registry,
    )
    text_only = resolve_platform_visual_expectation(
        platform_id="youtube_community",
        content_surface="community_text_post",
        variant_mode="dry_run",
        registry=registry,
    )
    assert "fewer_than_three_useful_visuals" in evaluate_visual_composition(
        [], requirements=long_form
    )["blockers"]
    text_decision = evaluate_visual_composition([], requirements=text_only)
    assert text_decision["status"] == "PASS"
    assert text_decision["blockers"] == []


@pytest.mark.parametrize("future_mode", ["image", "mixed_media", "video"])
def test_unregistered_visual_modes_do_not_inherit_text_only_waiver(future_mode):
    decision = resolve_platform_visual_expectation(
        platform_id="youtube_community",
        content_surface="community_text_post",
        variant_mode=future_mode,
        registry=load_source_capability_registry(),
    )
    assert decision["status"] == "BLOCK"
    assert decision["minimum_visual_count"] > 0
    assert decision["blockers"] == ["unsupported_platform_visual_mode"]


def test_registered_non_text_mode_cannot_claim_a_zero_visual_waiver():
    registry = deepcopy(load_source_capability_registry())
    rule = registry["platform_visual_expectations"]["youtube_community"]["rules"][0]
    rule["variant_mode"] = "image"
    rule["effective_visual_mode"] = "image"
    decision = resolve_platform_visual_expectation(
        platform_id="youtube_community",
        content_surface="community_text_post",
        variant_mode="image",
        registry=registry,
    )
    assert decision["status"] == "BLOCK"
    assert decision["minimum_visual_count"] > 0
    assert decision["blockers"] == ["malformed_platform_visual_policy"]


def test_visual_hash_binds_requirements_and_capability_context_even_when_blockers_match():
    base = evaluate_visual_composition(
        [],
        requirements={"minimum_visual_count": 0, "requires_lead_visual": False, "requires_visual_diversity": False},
        policy_context={"article_mode": "straight_news", "market_sensitive": True, "market_snapshot_required": False},
    )
    requirement_mutation = evaluate_visual_composition(
        [],
        requirements={"minimum_visual_count": 0, "requires_lead_visual": False, "requires_visual_diversity": False, "policy_version": "mutated"},
        policy_context={"article_mode": "straight_news", "market_sensitive": True, "market_snapshot_required": False},
    )
    context_mutation = evaluate_visual_composition(
        [],
        requirements={"minimum_visual_count": 0, "requires_lead_visual": False, "requires_visual_diversity": False},
        policy_context={"article_mode": "straight_news", "market_sensitive": False, "market_snapshot_required": False},
    )
    assert base["blockers"] == requirement_mutation["blockers"] == context_mutation["blockers"] == []
    assert len({base["decision_hash"], requirement_mutation["decision_hash"], context_mutation["decision_hash"]}) == 3


def test_google_visual_provider_is_current_discovery_only_contract():
    request = GoogleImageSearchGroundingProvider().build_request("official port infrastructure photo")
    assert request["tools"][0]["search_types"] == ["web_search", "image_search"]
    assert request["usage_boundary"] == "discovery_only_not_provenance_or_reuse_permission"
    assert request["network_call_made"] is False


def test_generic_prepare_only_real_rehearsal_calls_no_platform(tmp_path, monkeypatch):
    cc_root = Path(r"A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion")
    if not cc_root.exists():
        pytest.skip("local ingestion repo unavailable")
    import live_contentops.edge_cdp_publishing_adapter_v1 as edge
    monkeypatch.setattr(edge, "publish_substack_article_via_edge", lambda **_: (_ for _ in ()).throw(AssertionError("no write")))
    result = run_generic_prepare_only(output_dir=tmp_path, story_request=json.loads(REAL_REQUEST.read_text()), capital_chronicle_root=cc_root, as_of_utc="2026-07-11T02:00:00Z")
    assert result["classification"] == "PASS_GENERIC_FABRIC_FAIL_CLOSED_REHEARSAL"
    assert result["public_write_performed"] is False
    assert result["platform_adapter_called"] is False
    assert result["publication_eligible"] is False
    assert any(blocker.startswith("editorial_revision_v2:") for blocker in result["blockers"])


def test_canonical_runner_generic_mode_cannot_enter_browser_or_publish_paths(tmp_path, monkeypatch):
    cc_root = Path(r"A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion")
    if not cc_root.exists():
        pytest.skip("local ingestion repo unavailable")
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **_: (_ for _ in ()).throw(AssertionError("no substack write")))
    monkeypatch.setattr(pipeline, "publish_x_post_via_edge", lambda **_: (_ for _ in ()).throw(AssertionError("no x write")))
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: (_ for _ in ()).throw(AssertionError("no browser doctor")))
    code = pipeline.main([
        "--run-id", "generic-test", "--output-dir", str(tmp_path), "--prepare-generic-fabric",
        "--capital-chronicle-root", str(cc_root), "--generic-story-request", str(REAL_REQUEST),
        "--generic-as-of-utc", "2026-07-11T02:00:00Z",
    ])
    assert code == 0
    result = json.loads((tmp_path / "generic_fabric_prepare_only_result_v2.json").read_text())
    assert result["public_write_performed"] is False
    assert result["browser_or_cdp_used"] is False


def test_canonical_runner_database_preflight_passes_story_scoped_publication_packet(tmp_path, monkeypatch):
    cc_root = Path(r"A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion")
    if not cc_root.exists():
        pytest.skip("local ingestion repo unavailable")
    monkeypatch.setattr(pipeline, "publish_substack_article_via_edge", lambda **_: (_ for _ in ()).throw(AssertionError("no substack write")))
    monkeypatch.setattr(pipeline, "browser_doctor", lambda: (_ for _ in ()).throw(AssertionError("no browser doctor")))
    code = pipeline.main([
        "--run-id", "governed-preflight", "--output-dir", str(tmp_path),
        "--prepare-generic-fabric", "--capital-chronicle-root", str(cc_root),
        "--generic-as-of-utc", "2026-07-14T12:00:00Z",
    ])
    assert code == 0
    result = json.loads((tmp_path / "generic_database_preflight_result_v1.json").read_text())
    assert result["publication_eligible"] is True
    assert result["public_write_performed"] is False


def test_legacy_topic_prepare_is_not_canonical_without_explicit_opt_in(tmp_path):
    code = pipeline.main(["--run-id", "legacy-block", "--output-dir", str(tmp_path), "--prepare-only"])
    assert code == 2
    assert not (tmp_path / "run_context_v1.json").exists()


def test_newsroom_pool_and_schedule_integration(tmp_path):
    # Create mock schedule
    schedule = {
        "decisions": [
            {
                "window_id": "us_open",
                "decision": "PUBLISH_BREAKING_OR_HIGH_IMPACT",
                "selected_candidate": {
                    "candidate_id": "cc-candidate-11111111111111111111"
                }
            },
            {
                "window_id": "us_close",
                "decision": "NO_PUBLICATION_THRESHOLD_NOT_MET",
                "selected_candidate": None
            }
        ]
    }
    schedule_path = tmp_path / "schedule.json"
    schedule_path.write_text(json.dumps(schedule), encoding="utf-8")
    
    # Create mock packet
    packet = {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "cc-evidence-test",
        "generated_at_utc": "2026-07-14T12:00:00Z",
        "as_of_utc": "2026-07-14T12:00:00Z",
        "story_window": {"hours": 24, "start_utc": "2026-07-13T12:00:00Z", "end_utc": "2026-07-14T12:00:00Z"},
        "blockers": [],
        "headlines": [{"headline_id": "test"}],
        "events": [
            {
                "event_id": "event1",
                "event_time_utc": "2026-07-14T12:00:00Z",
                "public_claim_allowed": True
            }
        ],
        "official_source_documents": [{"document_id": "doc1", "source_url": "https://test.url"}],
        "numeric_claims": [
            {
                "claim_id": "claim1",
                "metric": "UST:10Y",
                "value": 4.56,
                "unit": "percent",
                "observation_time_utc": "2026-07-14T12:00:00Z",
                "source_id": "doc1",
                "source_artifact_ref": "ref1",
                "llm_numeric_authority": False,
                "public_claim_allowed": True
            }
        ],
        "market_snapshots": [],
        "source_state": {
            "dqr_status": "BLOCKED",
            "global_dqr_reporting_allowed": False,
            "story_scoped_reporting_allowed": True,
            "source_health_status": "HEALTHY",
            "global_state_unchanged": True,
        },
        "candidate_visual_inputs": [],
        "citation_map": {"claim1": ["doc1"]},
        "provenance": {},
        "public_claim_permissions": {
            "numeric_claims_allowed": True,
            "narrative_synthesis_allowed": True,
            "reporting_allowed": True,
            "decision": "ALLOW",
            "consumer_class": ["contentops_publication"]
        },
        "governed_contract": {
            "upstream_candidate_id": "cc-candidate-11111111111111111111"
        },
    }
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    
    # Case A: Candidate is in schedule as PUBLISH -> Should be eligible
    res_a = run_generic_database_preflight(
        output_dir=tmp_path / "out_a",
        evidence_packet_path=packet_path,
        newsroom_schedule_path=schedule_path,
    )
    assert res_a["publication_eligible"] is True
    assert "newsroom_schedule_decision_not_publish" not in res_a["blockers"]
    
    # Case B: Candidate is not in schedule as PUBLISH -> Should be blocked
    packet["governed_contract"]["upstream_candidate_id"] = "cc-candidate-22222222222222222222"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    
    res_b = run_generic_database_preflight(
        output_dir=tmp_path / "out_b",
        evidence_packet_path=packet_path,
        newsroom_schedule_path=schedule_path,
    )
    assert res_b["publication_eligible"] is False
    assert "newsroom_schedule_decision_not_publish" in res_b["blockers"]

    # Case C: Retired ambiguous PUBLISH token must not grant authority.
    packet["governed_contract"]["upstream_candidate_id"] = "cc-candidate-11111111111111111111"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    schedule["decisions"][0]["decision"] = "PUBLISH"
    schedule_path.write_text(json.dumps(schedule), encoding="utf-8")
    res_c = run_generic_database_preflight(
        output_dir=tmp_path / "out_c",
        evidence_packet_path=packet_path,
        newsroom_schedule_path=schedule_path,
    )
    assert res_c["publication_eligible"] is False
    assert "newsroom_schedule_decision_not_publish" in res_c["blockers"]



def test_generic_prepare_only_blocks_missing_mandatory_revision_contract(tmp_path) -> None:
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(_fresh_packet()), encoding="utf-8")
    request = json.loads(REAL_REQUEST.read_text())
    request.pop("editorial_revision_v2")

    result = run_generic_prepare_only(
        output_dir=tmp_path / "out_missing",
        story_request=request,
        evidence_packet_path=packet_path,
    )
    contract = json.loads((tmp_path / "out_missing" / "editorial_revision_contract_v2.json").read_text())
    review = json.loads((tmp_path / "out_missing" / "editorial_review_orchestrator_v2.json").read_text())
    assert result["publication_eligible"] is False
    assert "editorial_revision_v2_required" in result["blockers"]
    assert contract["status"] == "BLOCK"
    assert review["status"] == "BLOCK"
    assert "editorial_revision_v2:editorial_revision_v2_required" in review["blockers"]
    assert result["public_write_performed"] is False


def test_generic_prepare_only_blocks_explicit_invalid_revision_contract(tmp_path) -> None:
    packet = _fresh_packet()
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    request = {
        "story_type": "market_move", "article_mode": "analysis", "market_sensitive": True,
        "fresh_material_delta": True, "expected_source_cadence": "market_session",
        "article_candidate": {
            "title": "Official WTI data update", "article_mode": "analysis",
            "as_of_utc": "2026-07-11T02:00:00Z",
            "rendered_body": "WTI printed 70 dollars.", "claim_ids_used": ["c1"],
            "numeric_claims_from_llm": False, "quantitative_blockers": [], "hard_truncation_used": False,
        },
        "visual_assets": [
            _asset("lead", "lead_contextual", "official_photo", "physical"),
            _asset("price", "primary_quantitative_chart", "chart", "price", ["WTI"]),
            _asset("map", "map_geography", "map", "geography"),
        ],
        "editorial_revision_v2": {
            "content_unit_mappings": [{
                "content_unit_id": "sentence-001", "content_unit_type": "fact",
                "claim_ids": ["not-approved"], "source_urls": ["https://official.example/item"],
            }],
            "revision_stages": [],
        },
    }
    result = run_generic_prepare_only(output_dir=tmp_path / "out", story_request=request, evidence_packet_path=packet_path)
    contract = json.loads((tmp_path / "out" / "editorial_revision_contract_v2.json").read_text())
    review = json.loads((tmp_path / "out" / "editorial_review_orchestrator_v2.json").read_text())
    assert result["publication_eligible"] is False
    assert contract["status"] == "BLOCK"
    assert review["status"] == "BLOCK"
    assert any(value.startswith("editorial_revision_v2:") for value in review["blockers"])
    assert result["public_write_performed"] is False
