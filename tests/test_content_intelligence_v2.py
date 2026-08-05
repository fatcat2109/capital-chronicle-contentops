from dataclasses import replace
import json
from pathlib import Path

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_EXPORT = ROOT / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_dced71f_immutable_export.json"


def _config():
    return adapters.load_foundation_config(ROOT)


def _candidate(relationship=contracts.EventRelationship.INITIAL_EVENT, *, authorized=True, **changes):
    if relationship == contracts.EventRelationship.MATERIAL_UPDATE and changes.get("governed_material_delta"):
        changes.setdefault("material_delta_evidence_ref", "evidence:a")
    relationship_ref = {
        contracts.EventRelationship.MATERIAL_UPDATE: changes.get("material_delta_evidence_ref"),
        contracts.EventRelationship.CONFIRMATION: changes.get("governed_new_evidence_ref"),
        contracts.EventRelationship.CONTRADICTION: changes.get("conflicting_evidence_ref"),
        contracts.EventRelationship.CORRECTION: changes.get("authoritative_correction_ref"),
        contracts.EventRelationship.NEW_PHASE: changes.get("distinct_new_event_ref"),
    }.get(relationship)
    relationship_role = {
        contracts.EventRelationship.MATERIAL_UPDATE: contracts.EvidenceRole.MATERIAL_DELTA,
        contracts.EventRelationship.CONFIRMATION: contracts.EvidenceRole.CONFIRMATION,
        contracts.EventRelationship.CONTRADICTION: contracts.EvidenceRole.CONTRADICTION,
        contracts.EventRelationship.CORRECTION: contracts.EvidenceRole.CORRECTION,
        contracts.EventRelationship.NEW_PHASE: contracts.EvidenceRole.NEW_PHASE,
    }.get(relationship)
    refs = tuple(dict.fromkeys(ref for ref in (
        "evidence:a", relationship_ref, changes.get("prior_testable_proposition_ref"),
        changes.get("prior_error_ref"), changes.get("update_justification_ref"),
    ) if ref))
    bindings = []
    if relationship_ref and relationship_role:
        bindings.append(contracts.build_governed_evidence_binding_v1(
            evidence_ref=relationship_ref, evidence_roles=(relationship_role,),
            producer_artifact_binding_hash="a" * 64, as_of_utc="2026-01-01T00:00:00Z",
        ))
    if changes.get("update_justification_ref"):
        bindings.append(contracts.build_governed_evidence_binding_v1(
            evidence_ref=changes["update_justification_ref"],
            evidence_roles=(contracts.EvidenceRole.EVERGREEN_JUSTIFICATION,),
            producer_artifact_binding_hash="b" * 64, as_of_utc="2026-01-01T00:00:00Z",
        ))
    candidate = core.LearningCandidateV2(
        candidate_id="candidate-a",
        story_id="story-a",
        cluster_id="cluster-a",
        update_chain_id="chain-a",
        source_relationship=relationship,
        evidence_state="GOVERNED_EVIDENCE",
        authority_state="AUTHORIZED" if authorized else "UNAUTHORIZED",
        authority_ready=authorized,
        reporting_allowed=authorized,
        authority_blockers=() if authorized else ("authority_missing",),
        history_identity_match=False,
        material_reader_contribution=True,
        feature_inputs=(
            core.FeatureInputV1("authority_readiness", True, contracts.AvailabilityState.AVAILABLE, 1.0 if authorized else 0.0, evidence_refs=("evidence:a",)),
            core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=("evidence:a",)),
            core.FeatureInputV1("duplication_risk", True, contracts.AvailabilityState.EXPLICIT_ZERO, 0.0, evidence_refs=("evidence:a",)),
        ),
        evidence_refs=refs,
        governed_evidence_bindings=tuple(bindings),
        internal_brief_ids=("brief:a",),
    )
    return adapters.attach_trusted_context_to_candidate(replace(candidate, **changes), repo_root=ROOT)


def _empty_inputs(candidate_count=1):
    candidates = tuple(replace(_candidate(), candidate_id=f"candidate-{index}", story_id=f"story-{index}", cluster_id=f"cluster-{index}", update_chain_id=f"chain-{index}") for index in range(candidate_count))
    return (
        candidates,
        contracts.PublishedContentHistoryV1("history"),
        contracts.ContentGapSetV1("gaps"),
        contracts.PerformanceObservationSetV1("observations"),
    )


def _decision(candidates=None, history=None, gaps=None, observations=None, **kwargs):
    default_candidates, default_history, default_gaps, default_observations = _empty_inputs()
    selected_candidates = default_candidates if candidates is None else candidates
    context = selected_candidates[0].evidence_context if selected_candidates else adapters.build_synthetic_validation_context(("synthetic:empty-cohort",), repo_root=ROOT)
    return core.build_learning_decision_v2(
        candidates=selected_candidates,
        history=default_history if history is None else history,
        gaps=default_gaps if gaps is None else gaps,
        observations=default_observations if observations is None else observations,
        config=_config(),
        input_bindings=kwargs.pop("input_bindings", {"test": "binding"}),
        logical_time_basis=kwargs.pop("logical_time_basis", "test-logical-time"),
        decision_cutoff_utc=context.decision_cutoff_utc,
        evidence_context=context,
        **kwargs,
    )


def test_vocabulary_contains_all_required_orthogonal_values():
    assert len(contracts.EventRelationship) == 11
    assert len(contracts.EvidenceModality) == 14
    assert len(contracts.TemporalCharacter) == 9
    assert len(contracts.StoryMode) == 10
    assert len(contracts.GapType) == 12


@pytest.mark.parametrize("count", [0, 1, 4])
def test_published_history_supports_empty_singleton_and_multi(count):
    items = tuple(contracts.PublishedContentItemV1(f"content-{index}", f"story-{index}", None, None, None) for index in range(count))
    history = contracts.PublishedContentHistoryV1("history", items)
    assert history.validate() == ()
    assert len(history.items) == count


def test_published_history_validates_current_and_superseded_versions():
    versions = (
        contracts.ArticleVersionV1("old", "SUPERSEDED", "0" * 64, False),
        contracts.ArticleVersionV1("current", "ACCEPTED", "1" * 64, True, "old"),
    )
    item = contracts.PublishedContentItemV1("content", "story", None, None, None, versions, current_article_version_id="current")
    assert contracts.PublishedContentHistoryV1("history", (item,)).validate() == ()


@pytest.mark.parametrize("gap_count,idea_count", [(0, 0), (1, 1), (5, 3)])
def test_gap_set_supports_arbitrary_gap_and_idea_counts(gap_count, idea_count):
    findings = tuple(contracts.ContentGapFindingV1(f"gap-{index}", contracts.GapType.UNANSWERED_QUESTION, "fixture") for index in range(gap_count))
    gaps = contracts.ContentGapSetV1("gaps", findings, tuple(f"idea-{index}" for index in range(idea_count)))
    assert len(gaps.findings) == gap_count
    assert len(gaps.idea_ids) == idea_count


def test_observation_cardinalities_distinguish_variants_content_story_and_chain():
    rows = tuple(contracts.PerformanceObservationV1(
        f"observation-{index}", "content-a", "story-a", "chain-a", f"variant-{index}",
        "views", None, contracts.AvailabilityState.UNAVAILABLE,
        contracts.MetricAuthorityClass.UNAVAILABLE, unavailable_reason="not_collected",
    ) for index in range(9))
    cardinalities = contracts.PerformanceObservationSetV1("set", rows).cardinalities()
    assert cardinalities == {
        "observation_count": 9,
        "metric_bearing_observation_count": 0,
        "platform_variant_count": 9,
        "distinct_content_count": 1,
        "distinct_story_count": 1,
        "distinct_update_chain_count": 1,
    }


def test_observation_explicit_zero_is_metric_bearing_not_unavailable():
    row = contracts.PerformanceObservationV1(
        "observation", "content", "story", "chain", "variant", "views", 0.0,
        contracts.AvailabilityState.EXPLICIT_ZERO,
        contracts.MetricAuthorityClass.OFFICIAL_DASHBOARD_EXPORT,
    )
    observations = contracts.PerformanceObservationSetV1("set", (row,))
    assert observations.validate() == ()
    assert observations.cardinalities()["metric_bearing_observation_count"] == 1


def test_observation_unavailable_requires_reason_and_null():
    invalid = contracts.PerformanceObservationV1(
        "observation", "content", "story", "chain", "variant", "views", 1.0,
        contracts.AvailabilityState.UNAVAILABLE, contracts.MetricAuthorityClass.UNAVAILABLE,
    )
    assert set(invalid.validate()) == {"unavailable_state_must_not_carry_value", "unavailable_state_requires_reason"}


def test_foundation_config_is_hash_validated_and_uncalibrated():
    config = _config()
    assert config.validate() == ()
    assert config.calibration_state == contracts.CalibrationState.UNCALIBRATED_FOUNDATION
    assert len(config.features) == 21
    assert {feature.weight for feature in config.features} == {1.0}


def test_config_hash_tampering_fails_closed():
    config = _config()
    assert "config_logical_hash_mismatch" in replace(config, config_version="tampered").validate()


def test_exact_upstream_export_matches_declared_blob_byte_and_logical_identity():
    data = UPSTREAM_EXPORT.read_bytes()
    binding, result = adapters.verify_upstream_export(data)
    assert result.status == "PASS_IMMUTABLE_BINDING_VERIFIED"
    assert result.blockers == ()
    assert result.actual_byte_sha256 == adapters.UPSTREAM_FILE_SHA256
    assert result.actual_git_blob_sha1 == adapters.UPSTREAM_GIT_BLOB_SHA1
    assert result.calculated_logical_hash == adapters.UPSTREAM_LOGICAL_HASH
    assert binding.pool_id == adapters.UPSTREAM_POOL_ID


def test_verifier_rejects_line_ending_forged_bytes():
    """Byte-exact verification must detect line-ending mutation.

    Regression guard. The verifier once normalised CRLF to LF *before* hashing, so a
    CRLF-mutated payload reported the declared SHA-256 and returned PASS with no
    blockers. Every other test still passed, because none of them fed altered bytes in.
    The correct fix is to pin worktree bytes via .gitattributes (``*.json text eol=lf``)
    and hash exactly what was supplied -- never to rewrite input inside the verifier.
    """
    good = UPSTREAM_EXPORT.read_bytes()
    assert b"\r\n" not in good, (
        "fixture must be LF on disk; check the *.json eol=lf rule in .gitattributes"
    )

    forged = good.replace(b"\n", b"\r\n")
    assert forged != good

    binding, result = adapters.verify_upstream_export(forged)
    assert result.status == "BLOCKED_ARTIFACT_BINDING"
    assert result.blockers, "forged bytes must produce at least one blocker"

    # The reported hash must describe the bytes actually supplied, not a normalised
    # rewrite of them, and must not collide with the declared value.
    true_forged_sha = __import__("hashlib").sha256(forged).hexdigest()
    assert result.actual_byte_sha256 == true_forged_sha
    assert result.actual_byte_sha256 != adapters.UPSTREAM_FILE_SHA256


def test_binding_does_not_coerce_malformed_identity_fields():
    """Identity fields must fail closed rather than be laundered into valid-looking strings.

    Regression guard. Wrapping these reads in ``str()`` turned ``12345`` into ``"12345"``
    and ``None`` into ``"None"``, so malformed evidence could satisfy a string-typed
    comparison instead of tripping the corresponding ``*_mismatch`` blocker.
    """
    payload = json.loads(UPSTREAM_EXPORT.read_bytes())
    for bad_value in (12345, None, ["x"], {"a": 1}):
        mutated = dict(payload)
        mutated["logical_hash"] = bad_value
        data = json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode()
        binding = adapters.build_upstream_binding(data)
        assert binding.logical_hash == bad_value, (
            f"logical_hash {bad_value!r} was coerced to {binding.logical_hash!r}"
        )
        assert binding.logical_hash != str(bad_value) or isinstance(bad_value, str)


@pytest.mark.parametrize(
    "change,expected",
    [
        ({"producer_commit": "bad"}, "producer_commit_malformed"),
        ({"repository": "wrong/repository"}, "repository_identity_mismatch"),
        ({"artifact_path": "wrong/path.json"}, "artifact_path_mismatch"),
        ({"git_blob_sha1": "0" * 40}, "git_blob_sha1_mismatch"),
        ({"consumed_byte_sha256": "0" * 64}, "consumed_byte_sha256_mismatch"),
        ({"logical_hash": "0" * 64}, "logical_hash_mismatch"),
        ({"schema_version": "wrong.schema"}, "schema_version_mismatch"),
        ({"producer_version": "wrong.producer"}, "producer_version_mismatch"),
        ({"pool_id": "wrong-pool"}, "pool_id_mismatch"),
        ({"candidate_hashes": {"wrong": "0" * 64}}, "candidate_hashes_mismatch"),
    ],
)
def test_artifact_verifier_fails_closed_for_binding_mismatches(change, expected):
    data = UPSTREAM_EXPORT.read_bytes()
    binding = replace(adapters.build_upstream_binding(data), **change)
    result = contracts.verify_governed_artifact(
        data, binding,
        expected_repository=adapters.UPSTREAM_REPOSITORY,
        expected_branch=adapters.UPSTREAM_BRANCH,
        expected_artifact_path=adapters.UPSTREAM_ARTIFACT_PATH,
        expected_schema_version=adapters.UPSTREAM_SCHEMA,
        expected_producer_version=adapters.UPSTREAM_PRODUCER,
        expected_pool_id=adapters.UPSTREAM_POOL_ID,
        as_of_utc="2026-07-15T00:00:00Z",
    )
    assert expected in result.blockers
    assert result.status == "BLOCKED_ARTIFACT_BINDING"


def test_artifact_verifier_rejects_future_cutoff():
    data = UPSTREAM_EXPORT.read_bytes()
    binding = adapters.build_upstream_binding(data)
    result = contracts.verify_governed_artifact(
        data, binding,
        expected_repository=adapters.UPSTREAM_REPOSITORY,
        expected_branch=adapters.UPSTREAM_BRANCH,
        expected_artifact_path=adapters.UPSTREAM_ARTIFACT_PATH,
        expected_schema_version=adapters.UPSTREAM_SCHEMA,
        expected_producer_version=adapters.UPSTREAM_PRODUCER,
        expected_pool_id=adapters.UPSTREAM_POOL_ID,
        as_of_utc="2026-07-13T00:00:00Z",
    )
    assert "future_cutoff" in result.blockers


def test_artifact_verifier_rejects_missing_cutoff():
    payload = json.loads(UPSTREAM_EXPORT.read_bytes())
    payload.pop("cutoff_time_utc")
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    binding = replace(adapters.build_upstream_binding(data), git_blob_sha1=None)
    result = contracts.verify_governed_artifact(
        data, binding,
        expected_repository=adapters.UPSTREAM_REPOSITORY,
        expected_branch=adapters.UPSTREAM_BRANCH,
        expected_artifact_path=adapters.UPSTREAM_ARTIFACT_PATH,
        expected_schema_version=adapters.UPSTREAM_SCHEMA,
        expected_producer_version=adapters.UPSTREAM_PRODUCER,
        expected_pool_id=adapters.UPSTREAM_POOL_ID,
        as_of_utc="2026-07-15T00:00:00Z",
    )
    assert "cutoff_time_missing" in result.blockers


def test_upstream_comparison_is_same_bytes_and_identity():
    current = UPSTREAM_EXPORT.read_bytes()
    historical = (ROOT / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_9bff5453_historical_export.json").read_bytes()
    assert adapters.compare_upstream_pool_exports(current, historical)["classification"] == "SAME_BYTES_AND_IDENTITY"


def test_authorized_material_update_requires_governed_delta():
    outcome = core.evaluate_outcome(_candidate(contracts.EventRelationship.MATERIAL_UPDATE, governed_material_delta=True), _config())
    assert "GOVERNED_MATERIAL_UPDATE" in outcome.actionable_outcomes


def test_unauthorized_material_update_preserves_relationship_but_not_actionable_outcome():
    outcome = core.evaluate_outcome(_candidate(contracts.EventRelationship.MATERIAL_UPDATE, authorized=False, governed_material_delta=True), _config())
    assert outcome.source_relationship == contracts.EventRelationship.MATERIAL_UPDATE
    assert "GOVERNED_MATERIAL_UPDATE" not in outcome.actionable_outcomes
    assert outcome.publication_disposition == "NO_PUBLICATION_INSUFFICIENT_AUTHORITY"


def test_authorized_confirmation_requires_prior_proposition_and_new_evidence():
    candidate = _candidate(contracts.EventRelationship.CONFIRMATION, prior_testable_proposition_ref="prior", governed_new_evidence_ref="new")
    assert "GOVERNED_CONFIRMATION" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_unauthorized_confirmation_is_not_actionable():
    candidate = _candidate(contracts.EventRelationship.CONFIRMATION, authorized=False, prior_testable_proposition_ref="prior", governed_new_evidence_ref="new")
    assert "GOVERNED_CONFIRMATION" not in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_contradiction_requires_conflicting_evidence():
    candidate = _candidate(contracts.EventRelationship.CONTRADICTION, prior_testable_proposition_ref="prior", conflicting_evidence_ref="conflict")
    assert "GOVERNED_CONTRADICTION" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_correction_requires_prior_error_and_authoritative_correction():
    candidate = _candidate(contracts.EventRelationship.CORRECTION, prior_error_ref="prior-error", authoritative_correction_ref="correction")
    assert "GOVERNED_CORRECTION" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_governed_new_phase_requires_chain_continuity_distinct_event_and_authority():
    candidate = _candidate(contracts.EventRelationship.NEW_PHASE, update_chain_continuity=True, distinct_new_event_ref="event")
    assert "GOVERNED_NEW_PHASE" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_unauthorized_source_declared_new_phase_never_becomes_governed_new_phase():
    candidate = _candidate(contracts.EventRelationship.NEW_PHASE, authorized=False, update_chain_continuity=True, distinct_new_event_ref="event")
    outcome = core.evaluate_outcome(candidate, _config())
    assert outcome.source_relationship == contracts.EventRelationship.NEW_PHASE
    assert "GOVERNED_NEW_PHASE" not in outcome.actionable_outcomes


def test_packaging_gap_is_structural_and_grants_no_publication_authority():
    candidate = _candidate(gap_types=(contracts.GapType.DERIVATIVE_PACKAGING_GAP,))
    outcome = core.evaluate_outcome(candidate, _config())
    assert "DERIVATIVE_PACKAGING_GAP" in outcome.actionable_outcomes
    assert outcome.publication_disposition == "NO_PUBLICATION_NO_GOVERNED_ACTIONABLE_OUTCOME"


def test_duplicate_does_not_imply_filler():
    outcome = core.evaluate_outcome(_candidate(history_identity_match=True, material_reader_contribution=True), _config())
    assert "DUPLICATE_NO_NEW_DELTA" in outcome.actionable_outcomes
    assert "FILLER_NO_READER_CONTRIBUTION" not in outcome.actionable_outcomes


def test_filler_requires_explicit_no_reader_contribution():
    outcome = core.evaluate_outcome(_candidate(material_reader_contribution=False), _config())
    assert "FILLER_NO_READER_CONTRIBUTION" in outcome.actionable_outcomes
    assert outcome.publication_disposition == "NO_PUBLICATION_FILLER"


def test_evergreen_refresh_requires_all_configured_criteria():
    candidate = _candidate(
        gap_types=(contracts.GapType.EVERGREEN_REFRESH,), durability=0.8,
        content_age_hours=200.0, reader_utility=0.9, update_justification_ref="justification",
    )
    assert "EVERGREEN_REFRESH_JUSTIFIED" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_invalid_evergreen_refresh_preserves_reason_without_actionable_refresh():
    candidate = _candidate(gap_types=(contracts.GapType.EVERGREEN_REFRESH,), durability=0.1, content_age_hours=1.0, reader_utility=0.1)
    outcome = core.evaluate_outcome(candidate, _config())
    assert "EVERGREEN_REFRESH_JUSTIFIED" not in outcome.actionable_outcomes
    assert "evergreen_refresh_criteria_not_met" in outcome.reason_codes


def test_mutually_incompatible_actionable_outcomes_fail_validation():
    with pytest.raises(ValueError, match="incompatible_actionable_outcomes"):
        core._validate_actionable_outcomes(("GOVERNED_NEW_PHASE", "DUPLICATE_NO_NEW_DELTA"))


def test_feature_unavailable_is_preserved_and_not_scored_as_zero():
    candidate = _candidate(feature_inputs=(core.FeatureInputV1("freshness", True, contracts.AvailabilityState.UNAVAILABLE, None, "not_measured", evidence_refs=("evidence:a",)),))
    features = core.evaluate_features(candidate, _config(), contracts.PerformanceObservationSetV1("empty"))
    freshness = next(row for row in features if row.feature_id == "freshness")
    assert freshness.raw_value is freshness.normalized_value is freshness.contribution is None
    assert freshness.unavailable_reason == "not_measured"


def test_feature_explicit_zero_remains_available_zero():
    candidate = _candidate(feature_inputs=(core.FeatureInputV1("duplication_risk", True, contracts.AvailabilityState.EXPLICIT_ZERO, 0.0, evidence_refs=("evidence:a",)),))
    feature = next(row for row in core.evaluate_features(candidate, _config(), contracts.PerformanceObservationSetV1("empty")) if row.feature_id == "duplication_risk")
    assert feature.raw_value == feature.normalized_value == feature.penalty == 0.0


def test_contribution_arithmetic_uses_versioned_config_only():
    decision = _decision()
    row = decision.ranking_rows[0]
    expected = sum(feature.contribution or 0.0 for feature in row.features) - sum(feature.penalty or 0.0 for feature in row.features)
    assert row.score == round(expected, 8)


def test_no_performance_prior_when_metric_bearing_observation_count_is_zero():
    decision = _decision()
    assert decision.observation_cardinalities["metric_bearing_observation_count"] == 0
    assert decision.feature_availability["candidate-0:performance_evidence_availability"] == "unavailable"
    abstention = [row for row in decision.proposals if row["proposal_type"] == "performance_abstention"]
    assert abstention == [{"proposal_type": "performance_abstention", "reason": "no_metric_bearing_observations", "performance_prior_created": False, "automatic_change": False}]


def test_multiple_stories_and_update_chains_rank_without_fixed_counts():
    candidates, history, gaps, observations = _empty_inputs(7)
    decision = _decision(candidates=candidates, history=history, gaps=gaps, observations=observations)
    assert len(decision.ranking_rows) == 7
    assert decision.observation_cardinalities["candidate_count"] == 7
    assert len({row.update_chain_id for row in decision.ranking_rows}) == 7


def test_empty_candidate_cohort_is_valid():
    decision = _decision(candidates=())
    assert decision.ranking_rows == ()
    assert decision.observation_cardinalities["candidate_count"] == 0


def test_identical_inputs_and_config_produce_identical_decision():
    assert _decision() == _decision()


def test_changed_input_binding_creates_new_append_only_identity():
    prior = _decision()
    successor = _decision(prior_decision=prior, supersession_reason="binding changed", input_bindings={"test": "changed"})
    assert successor.decision_id != prior.decision_id
    assert core.validate_append_only_successor(prior, successor) == ()


def test_successor_requires_supersession_reason():
    with pytest.raises(ValueError, match="supersession_reason_required"):
        _decision(prior_decision=_decision())


def test_model_assisted_judgment_cannot_grant_authority_or_permission():
    record = contracts.ModelAssistedJudgmentV1(
        "fixture", "model", "prompt-v1", "0" * 64, "1" * 64, "2" * 64,
        "schema", "low", "PASS", "Concise rationale.", ("evidence",), True, True,
    )
    assert set(record.validate()) == {"model_must_not_grant_authority", "model_must_not_grant_publication_permission"}


def test_cross_domain_matrix_has_fifteen_domains_and_executes_algorithms():
    matrix = adapters.execute_cross_domain_fixture_matrix(ROOT)
    assert matrix["status"] == "PASS"
    assert len(matrix["rows"]) >= 15
    assert all(row["algorithm_executed"] and row["status"] == "PASS" for row in matrix["rows"])
    assert all(row["synthetic_fixture"] for row in matrix["rows"])


def test_every_repaired_outcome_abstraction_runs_in_unrelated_domains():
    rows = adapters.execute_cross_domain_fixture_matrix(ROOT)["rows"]
    outcomes = {}
    for row in rows:
        outcomes.setdefault(row["observed_outcome"], set()).add(row["domain"])
    for outcome in ("GOVERNED_MATERIAL_UPDATE", "GOVERNED_CORRECTION", "GOVERNED_CONFIRMATION", "GOVERNED_CONTRADICTION", "NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME"):
        assert len(outcomes[outcome]) >= 2


def test_genericity_guard_passes_core_modules():
    report = adapters.run_genericity_guard(ROOT)
    assert report["status"] == "PASS"
    assert report["finding_count"] == 0


def test_generic_core_has_no_live_or_secret_integrations():
    text = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in (
        "live_contentops/content_intelligence_contracts_v2.py",
        "live_contentops/adaptive_learning_core_v2.py",
    ))
    forbidden = ("import requests", "from requests", "urllib", "socket", "os.environ", "dotenv", "playwright", "selenium", "subprocess", "webbrowser", "dispatch(", "publish(")
    assert not [needle for needle in forbidden if needle in text]


def test_treasury_history_adapter_preserves_final_and_rejected_lineage():
    history, lineage = adapters.accepted_publication_history_adapter(ROOT)
    assert history.validate() == ()
    assert lineage["final_accepted_public_body_sha256"] == adapters.FINAL_ACCEPTED_BODY_SHA256
    assert lineage["stale_article_export_sha256"] == adapters.STALE_ARTICLE_EXPORT_SHA256
    assert lineage["historical_manifest_body_sha256"] == adapters.HISTORICAL_MANIFEST_BODY_SHA256
    assert lineage["pre_final_repair_body_sha256"] == adapters.PRE_FINAL_REPAIR_BODY_SHA256
    assert len(history.items[0].platform_variants) == 9


def test_task3_and_task4_adapters_preserve_historical_evidence_without_rewrite():
    task3 = adapters.task3_historical_adapter(ROOT)
    task4 = adapters.task4_shadow_prototype_adapter(ROOT)
    assert task3["historical_status"] == "IMMUTABLE_TASK3_EVIDENCE_ADAPTED_NOT_REWRITTEN"
    assert task4["historical_status"] == "ACCEPTED_TREASURY_SPECIFIC_SHADOW_PROTOTYPE_SUPERSEDED_AS_FOUNDATION_BY_V2"
    assert task4["historical_value_preserved"] is True


def test_v1_compatibility_replay_keeps_v1_operational():
    replay = adapters.v1_compatibility_replay(ROOT)
    assert replay["v1_module_remains_operational"] is True
    assert replay["historical_artifacts_mutated"] is False


def test_treasury_compatibility_replay_grants_no_new_publication():
    replay = adapters.build_treasury_compatibility_replay(ROOT)
    assert replay["new_publication_authorized"] is False
    assert replay["v2_decision"]["operator_state"] == "OPERATOR_REVIEW_REQUIRED_SHADOW_ONLY"
    assert replay["v2_decision"]["observation_cardinalities"]["distinct_content_count"] == 1
    assert replay["v2_decision"]["observation_cardinalities"]["platform_variant_count"] == 9


def test_safety_firewall_is_complete_and_no_policy_mutation_is_exposed():
    decision = _decision()
    assert tuple(decision.forbidden_effects_checked) == core.FORBIDDEN_LEARNING_EFFECTS
    assert decision.operator_state == "OPERATOR_REVIEW_REQUIRED_SHADOW_ONLY"
    assert all(row["decision"].startswith(("NO_PUBLICATION", "INTERNAL_BRIEF")) for row in decision.no_publication_decisions)


def test_legacy_acceptance_entrypoint_no_longer_self_declares_pass():
    rows = adapters.foundation_acceptance_matrix()
    assert len(rows) >= 40
    assert len({row["requirement_id"] for row in rows}) == len(rows)
    assert "status" not in rows[0]
    assert {row["derived_status"] for row in rows}.issubset({"PASS", "REVIEW_REQUIRED", "BLOCKED", "FAIL", "NOT_IMPLEMENTED"})
    assert "NOT_IMPLEMENTED" in {row["derived_status"] for row in rows}
