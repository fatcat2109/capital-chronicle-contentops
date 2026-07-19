from dataclasses import fields, replace
import json
from pathlib import Path

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import generic_foundation_hardening_v2 as hardening


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return adapters.load_foundation_config(ROOT)


def _rehash(config, **changes):
    return hardening._rehashed_config(config, **changes)


def _capabilities(**changes):
    base = contracts.CapabilityDimensionsV1(
        evidence_modalities=(contracts.EvidenceModality.OFFICIAL_DOCUMENT,),
        temporal_characters=(contracts.TemporalCharacter.SCHEDULED,),
        story_modes=(contracts.StoryMode.POLICY_DECISION,),
        geography_ids=("geo_a", "geo_b"), entity_ids=("entity_a",),
        affected_economic_domains=("policy",), affected_asset_classes=("rates", "fx"),
        source_family_ids=("source_a", "source_b"), source_authority_classes=("official",),
        numeric_evidence_present=False, nonnumeric_evidence_present=True, scheduled_event_state=True,
    )
    return replace(base, **changes)


def _candidate(*, authorized=True, capabilities=None, feature_inputs=(), relationship=contracts.EventRelationship.INITIAL_EVENT, **changes):
    refs = tuple(dict.fromkeys(("evidence:a", *(ref for item in feature_inputs for ref in item.evidence_refs))))
    candidate = core.LearningCandidateV2(
        candidate_id="candidate-a", story_id="story-a", cluster_id="cluster-a", update_chain_id="chain-a",
        source_relationship=relationship, evidence_state="GOVERNED", authority_state="AUTHORIZED" if authorized else "BLOCKED",
        authority_ready=authorized, reporting_allowed=authorized,
        authority_blockers=() if authorized else ("authority_missing",), history_identity_match=False,
        material_reader_contribution=True, feature_inputs=tuple(feature_inputs), evidence_refs=refs,
        governed_evidence_bindings=(contracts.build_governed_evidence_binding_v1(
            evidence_ref=refs[0], evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT,),
            producer_artifact_binding_hash="f" * 64, as_of_utc="2026-01-01T00:00:00Z",
        ),),
        capabilities=capabilities or _capabilities(),
    )
    return replace(candidate, **changes)


def _feature(candidate, feature_id, config=None, observations=None):
    rows = core.evaluate_features(candidate, config or _config(), observations or contracts.PerformanceObservationSetV1("observations"))
    return next(row for row in rows if row.feature_id == feature_id)


def test_all_declared_config_fields_are_consumed():
    report = hardening._source_field_usage(ROOT)
    assert report["status"] == "PASS"
    assert report["unused_material_field_count"] == 0
    assert {row["field"] for row in report["rows"] if row["contract"] == "FeatureDefinitionV1"} == {row.name for row in fields(contracts.FeatureDefinitionV1)}


def test_config_numeric_and_version_validation():
    config = _config()
    assert config.validate() == ()
    cases = (
        (replace(config.features[0], weight=float("inf")), "feature_weight_not_finite"),
        (replace(config.features[0], minimum_evidence=-1), "minimum_evidence_invalid"),
        (replace(config.features[0], minimum_evidence=True), "minimum_evidence_invalid"),
    )
    for feature, expected in cases:
        blockers = replace(config, features=(feature, *config.features[1:])).validate()
        assert any(value.startswith(expected) for value in blockers)
    assert "config_version_empty" in replace(config, config_version="").validate()
    assert any(value.startswith("threshold_not_finite") for value in replace(config, thresholds={**config.thresholds, "breadth_full_count": float("nan")}).validate())


def test_config_reference_and_normalization_validation():
    config = _config()
    missing_gate = replace(config.features[0], authority_gate="missing")
    assert any(value.startswith("authority_gate_missing") for value in replace(config, features=(missing_gate, *config.features[1:])).validate())
    missing_normalization = replace(config.features[0], normalization="missing")
    assert any(value.startswith("normalization_rule_missing") for value in replace(config, features=(missing_normalization, *config.features[1:])).validate())
    invalid_bounds = {**config.normalization_rules, "min_max": {"kind": "min_max", "minimum": 1.0, "maximum": 1.0}}
    assert "normalization_bounds_invalid:min_max" in replace(config, normalization_rules=invalid_bounds).validate()


def test_config_hash_binds_every_material_field():
    config = _config()
    for change in (
        {"config_version": "changed"}, {"thresholds": {**config.thresholds, "breadth_full_count": 9}},
        {"authority_gates": {**config.authority_gates, "reporting_allowed": False}},
        {"threshold_rules": {**config.threshold_rules, "breadth_full_count": {"kind": "count", "minimum": 2}}},
    ):
        assert "config_logical_hash_mismatch" in replace(config, **change).validate()


def test_duplicate_feature_id_and_unknown_config_fields_fail(tmp_path, monkeypatch):
    config = _config()
    assert "duplicate_feature_id" in replace(config, features=(config.features[0], config.features[0])).validate()
    raw = json.loads((ROOT / adapters.CONFIG_REL_PATH).read_text(encoding="utf-8"))
    raw["unknown_field"] = True
    repo = tmp_path / "repo"
    path = repo / adapters.CONFIG_REL_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown_foundation_config_fields"):
        adapters.load_foundation_config(repo)
    raw.pop("unknown_field")
    raw["features"][0]["unknown_feature_field"] = True
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown_feature_config_fields"):
        adapters.load_foundation_config(repo)


@pytest.mark.parametrize("capabilities", [
    contracts.CapabilityDimensionsV1(),
    contracts.CapabilityDimensionsV1(geography_ids=("geo",)),
    _capabilities(),
])
def test_capability_dimensions_empty_singleton_multi(capabilities):
    assert capabilities.validate() == ()
    assert contracts.primitive(capabilities) == contracts.primitive(capabilities)


@pytest.mark.parametrize("capabilities,expected", [
    (contracts.CapabilityDimensionsV1(geography_ids=("geo", "geo")), "duplicate_geography_id"),
    (contracts.CapabilityDimensionsV1(entity_ids=("bad value",)), "malformed_entity_id:bad value"),
    (contracts.CapabilityDimensionsV1(temporal_characters=(contracts.TemporalCharacter.UNSCHEDULED,), scheduled_event_state=True), "scheduled_state_conflicts_with_unscheduled_character"),
])
def test_capability_dimension_validation_rejects_duplicates_and_malformed(capabilities, expected):
    assert expected in capabilities.validate()


def test_document_numeric_mixed_and_breadth_profiles():
    document = _capabilities(numeric_evidence_present=False, nonnumeric_evidence_present=True)
    numeric = _capabilities(evidence_modalities=(contracts.EvidenceModality.NUMERIC_TIME_SERIES,), numeric_evidence_present=True, nonnumeric_evidence_present=False)
    mixed = _capabilities(numeric_evidence_present=True, nonnumeric_evidence_present=True)
    assert document.profile()["document_only_profile"] is True
    assert numeric.profile()["numeric_evidence_present"] is True
    assert mixed.profile()["mixed_evidence_profile"] is True
    assert mixed.profile()["geography_count"] == mixed.profile()["asset_class_count"] == 2


def test_capability_dimensions_enter_generic_execution():
    candidate = _candidate()
    source = _feature(candidate, "source_diversity")
    schedule = _feature(candidate, "scheduled_catalyst_relevance")
    breadth = _feature(candidate, "cross_market_or_economy_breadth")
    policy = _feature(candidate, "policy_significance")
    assert all(row.domain_applicability_result and row.availability == contracts.AvailabilityState.AVAILABLE for row in (source, schedule, breadth))
    assert policy.domain_applicability_result and policy.capability_dimensions_used


def test_unsupported_feature_applicability_is_distinct():
    candidate = _candidate(capabilities=contracts.CapabilityDimensionsV1())
    row = _feature(candidate, "scheduled_catalyst_relevance")
    assert row.availability == contracts.AvailabilityState.UNSUPPORTED
    assert row.contribution is row.penalty is None
    assert row.domain_applicability_result is False


def test_minimum_evidence_and_authority_gate_are_enforced():
    config = _config()
    freshness = next(row for row in config.features if row.feature_id == "freshness")
    features = tuple(replace(row, minimum_evidence=2) if row.feature_id == "freshness" else row for row in config.features)
    changed = _rehash(config, features=features)
    minimum = _feature(_candidate(feature_inputs=(core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=("one",)),)), "freshness", changed)
    gated = _feature(_candidate(authorized=False, feature_inputs=(core.FeatureInputV1("authority_readiness", True, contracts.AvailabilityState.AVAILABLE, 0.0, evidence_refs=("one",)),)), "authority_readiness")
    assert minimum.availability == contracts.AvailabilityState.UNAVAILABLE and minimum.unavailable_reason == "minimum_evidence_not_met"
    assert gated.availability == contracts.AvailabilityState.BLOCKED and gated.authority_gate_result is False


@pytest.mark.parametrize("state,value", [
    (contracts.AvailabilityState.UNAVAILABLE, None),
    (contracts.AvailabilityState.BLOCKED, None),
    (contracts.AvailabilityState.UNSUPPORTED, None),
])
def test_all_abstention_states_do_not_contribute(state, value):
    item = core.FeatureInputV1("freshness", state != contracts.AvailabilityState.UNSUPPORTED, state, value, "fixture", evidence_refs=("evidence",))
    row = _feature(_candidate(feature_inputs=(item,)), "freshness")
    assert row.contribution is row.penalty is row.normalized_value is None


def test_explicit_zero_and_out_of_bounds_semantics():
    zero = _feature(_candidate(feature_inputs=(core.FeatureInputV1("duplication_risk", True, contracts.AvailabilityState.EXPLICIT_ZERO, 0.0, evidence_refs=("evidence",)),)), "duplication_risk")
    invalid = _feature(_candidate(feature_inputs=(core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 2.0, evidence_refs=("evidence",)),)), "freshness")
    assert zero.availability == contracts.AvailabilityState.EXPLICIT_ZERO and zero.penalty == 0.0
    assert invalid.availability == contracts.AvailabilityState.BLOCKED and invalid.contribution is None


def test_feature_rows_include_execution_metadata():
    row = _feature(_candidate(), "source_diversity")
    primitive = contracts.primitive(row)
    for key in ("capability_dimensions_used", "normalization_parameters", "evidence_count", "configured_minimum_evidence", "authority_gate_id", "authority_gate_result", "domain_applicability_result", "reason_codes", "evidence_refs"):
        assert key in primitive


def test_published_history_hardening_validation():
    versions = (
        contracts.ArticleVersionV1("old", "OLD", "0" * 64, False, "current"),
        contracts.ArticleVersionV1("current", "CURRENT", "1" * 64, True, "old"),
    )
    item = contracts.PublishedContentItemV1("content", "story", None, "cluster", "chain", versions, current_article_version_id="current")
    blockers = contracts.PublishedContentHistoryV1("history", (item,)).validate()
    assert "article_version_cycle:content" in blockers
    duplicate = replace(item, article_versions=(versions[0], versions[0]))
    assert "duplicate_article_version_id:content" in contracts.PublishedContentHistoryV1("history", (duplicate,)).validate()


def test_candidate_collection_hardening_validation():
    candidate = _candidate()
    assert core.validate_candidate_collection((candidate, candidate)) == ("duplicate_candidate_id",)
    inconsistent = replace(candidate, candidate_id="other", update_chain_id="other-chain")
    assert "cluster_update_chain_inconsistent:cluster-a" in core.validate_candidate_collection((candidate, inconsistent))


def test_gap_set_hardening_validation():
    row = contracts.ContentGapFindingV1("gap", contracts.GapType.MISSING_EVIDENCE, "finding", actionable=True)
    blockers = contracts.ContentGapSetV1("gaps", (row, row), ("idea", "idea")).validate(disallow_duplicate_logical_findings=True)
    assert {"duplicate_gap_id", "duplicate_idea_id", "actionable_gap_requires_evidence:gap", "duplicate_logical_gap_finding"}.issubset(blockers)


def test_observation_set_hardening_validation():
    row = contracts.PerformanceObservationV1("observation", "content", "story", "chain", "variant", "metric", None, contracts.AvailabilityState.UNAVAILABLE, contracts.MetricAuthorityClass.OFFICIAL_API, unavailable_reason="missing")
    blockers = contracts.PerformanceObservationSetV1("set", (row, row)).validate()
    assert {"unavailable_observation_requires_unavailable_authority_class", "duplicate_observation_id", "duplicate_observation_collision"}.issubset(blockers)


def test_learning_inputs_empty_and_arbitrary_cardinalities():
    config = _config()
    common = dict(history=contracts.PublishedContentHistoryV1("history"), gaps=contracts.ContentGapSetV1("gaps"), observations=contracts.PerformanceObservationSetV1("observations"), config=config, input_bindings={"input": "binding"}, logical_time_basis="fixture-time")
    assert core.build_learning_decision_v2(candidates=(), **common).ranking_rows == ()
    candidates = tuple(replace(_candidate(), candidate_id=f"candidate-{i}", story_id=f"story-{i}", cluster_id=f"cluster-{i}", update_chain_id=f"chain-{i}") for i in range(11))
    assert len(core.build_learning_decision_v2(candidates=candidates, **common).ranking_rows) == 11
    with pytest.raises(ValueError, match="input_binding_value_empty"):
        core.build_learning_decision_v2(candidates=(), **{**common, "input_bindings": {"input": ""}})


@pytest.mark.parametrize("spec_index", range(len(hardening.FIXTURE_SPECS)))
def test_all_cross_domain_fixtures_execute_generic_algorithms(spec_index):
    matrix, _ = hardening.execute_hardening_cross_domain_matrix(ROOT)
    row = matrix["rows"][spec_index]
    assert row["derived_status"] == "PASS" and row["generic_algorithms_executed"]


def test_cross_domain_rows_have_required_execution_fields():
    matrix, coverage = hardening.execute_hardening_cross_domain_matrix(ROOT)
    assert matrix["fixture_count"] >= 15 and matrix["row_schema_complete"]
    required = {"dimensions_supplied", "dimensions_omitted", "evidence_modalities", "temporal_characters", "story_mode", "feature_applicability_results", "evidence_count_results", "authority_gate_results", "feature_rows", "outcome_matrix", "ranking_row", "publication_disposition", "expected_result", "observed_result", "derived_status"}
    assert all(required.issubset(row) for row in matrix["rows"])
    assert coverage["status"] == "PASS"


def test_each_repaired_abstraction_has_two_domain_proof():
    _, coverage = hardening.execute_hardening_cross_domain_matrix(ROOT)
    assert coverage["abstractions_below_two_domain_proof"] == 0
    assert all(row["domain_count"] >= 2 for row in coverage["rows"])


def test_decision_contains_complete_lineage_bindings():
    replay, _ = hardening.build_lineage_reports(ROOT)
    for key in ("prior_decision_logical_hash", "config_logical_hash", "input_binding_hash", "content_history_hash", "gap_set_hash", "observation_set_hash", "candidate_cohort_hash", "logical_time_basis", "operator_state", "supersession_reason"):
        assert replay["successor"].get(key)


def test_append_only_successor_rejection_matrix():
    _, mutation = hardening.build_lineage_reports(ROOT)
    assert mutation["all_rejection_cases_pass"]
    assert {row["case"] for row in mutation["negative_cases"]} == {"missing_prior_id", "missing_prior_hash", "wrong_prior_hash", "missing_reason", "invalid_fork", "malformed_time"}


def test_deterministic_and_changed_authority_lineage():
    replay, mutation = hardening.build_lineage_reports(ROOT)
    assert replay["identical_input_replay_same_identity"]
    assert replay["changed_input_creates_new_identity"] and replay["changed_config_creates_new_identity"]
    assert mutation["prior_serialization_unchanged"]


def test_unchanged_successor_is_rejected():
    config = _config()
    candidate, history, gaps, observations = hardening._fixture_inputs(hardening.FIXTURE_SPECS[0])
    prior = core.build_learning_decision_v2(candidates=(candidate,), history=history, gaps=gaps, observations=observations, config=config, input_bindings={"input": "same"}, logical_time_basis="same-time")
    with pytest.raises(ValueError, match="successor_requires_material"):
        core.build_learning_decision_v2(candidates=(candidate,), history=history, gaps=gaps, observations=observations, config=config, input_bindings={"input": "same"}, logical_time_basis="same-time", prior_decision=prior, supersession_reason="no change")


def test_model_assisted_judgment_firewall():
    record = contracts.ModelAssistedJudgmentV1("provider", "model", "v1", "0" * 64, "1" * 64, "2" * 64, "schema", "low", "PASS", "rationale", ("evidence",))
    assert record.validate() == ()
    unsafe = replace(record, grants_authority=True, grants_reporting_permission=True, grants_publication_permission=True, grants_dqr_override=True, grants_factual_truth=True, grants_numeric_truth=True, grants_citation_waiver=True, grants_risk_language_waiver=True, grants_automatic_scheduling=True, grants_automatic_publication=True)
    assert len(unsafe.validate()) == 10


def test_genericity_ast_guard_has_zero_prohibited_findings():
    report = hardening.run_genericity_ast_guard(ROOT)
    assert report["status"] == "PASS"
    assert report["prohibited_finding_count"] == 0
    assert all(key in report for key in ("targets", "rule_inventory", "findings"))


def test_requirement_statuses_are_machine_derived():
    observations = {"acceptance": {"machine_derived": True}}
    result = hardening.derive_requirement_matrix(observations)
    row = next(row for row in result["rows"] if row["requirement_id"] == "MATRIX-01")
    missing = next(row for row in result["rows"] if row["requirement_id"] == "CONFIG-01")
    assert row["derived_status"] == "PASS"
    assert missing["derived_status"] == "NOT_IMPLEMENTED"
    assert result["machine_derived"] is True


def test_current_upstream_binding_and_three_way_comparison_from_committed_blob():
    current = (ROOT / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_dced71f_immutable_export.json").read_bytes()
    historical = (ROOT / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_9bff5453_historical_export.json").read_bytes()
    binding, comparison = hardening.build_current_upstream_reports(current_bytes=current, historical_bytes=historical, foundation_bytes=current, current_head="f4a365803385997265320e4b468c22028aea5a67")
    assert binding["status"] == "PASS"
    assert binding["git_blob_sha1"] == "e4f60146e26d5f52dec91f92a345e81d0fb1cc8d"
    assert comparison["classification"] == "SAME_BYTES_AND_IDENTITY"


def test_hardening_safety_surface():
    text = "\n".join((ROOT / path).read_text(encoding="utf-8-sig") for path in (
        "live_contentops/content_intelligence_contracts_v2.py", "live_contentops/adaptive_learning_core_v2.py",
    ))
    forbidden = ("requests", "urllib", "socket", "os.environ", "dotenv", "playwright", "selenium", "webbrowser", "publish(", "dispatch(")
    assert not [value for value in forbidden if value in text]


def test_v1_task3_task4_and_body_compatibility():
    replay = adapters.v1_compatibility_replay(ROOT)
    assert replay["v1_module_remains_operational"] and not replay["historical_artifacts_mutated"]
    assert replay["accepted_lineage"]["final_accepted_public_body_sha256"] == adapters.FINAL_ACCEPTED_BODY_SHA256
    assert replay["accepted_lineage"]["rejected_authority_states_preserved"]


def test_required_hardening_artifact_inventory_is_complete():
    assert len(hardening.REQUIRED_ARTIFACTS) == len(set(hardening.REQUIRED_ARTIFACTS))
    assert {"hardening_manifest.json", "requirement_matrix.json", "genericity_ast_guard_report.json", "safety_and_limitation_report.json"}.issubset(hardening.REQUIRED_ARTIFACTS)
