from dataclasses import replace
from pathlib import Path

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import generic_foundation_authority_integrity_repair_v2 as repair


ROOT = Path(__file__).resolve().parents[1]


def _config() -> contracts.AdaptiveLearningConfigV1:
    return adapters.load_foundation_config(ROOT)


def _rehash(config: contracts.AdaptiveLearningConfigV1, **changes) -> contracts.AdaptiveLearningConfigV1:
    draft = replace(config, **changes, config_logical_hash="")
    material = contracts.primitive(draft)
    material.pop("config_logical_hash")
    return replace(draft, config_logical_hash=contracts.logical_hash(material))


def _record(
    ref: str = "evidence:a",
    *,
    authority: str = "VERIFIED_GOVERNED",
    permission: str = "REPORTING_ALLOWED",
    reasons: tuple[str, ...] = (),
) -> contracts.EvidenceReferenceV1:
    return contracts.EvidenceReferenceV1(ref, authority, permission, reason_codes=reasons)


def _candidate(
    relationship: contracts.EventRelationship = contracts.EventRelationship.INITIAL_EVENT,
    *,
    authorized: bool = True,
    evidence_refs: tuple[str, ...] = ("evidence:a",),
    evidence_records: tuple[contracts.EvidenceReferenceV1, ...] = (),
    governed_evidence_refs: tuple[str, ...] = ("evidence:a",),
    feature_inputs: tuple[core.FeatureInputV1, ...] = (),
    **changes,
) -> core.LearningCandidateV2:
    candidate = core.LearningCandidateV2(
        candidate_id="candidate:a",
        story_id="story:a",
        cluster_id="cluster:a",
        update_chain_id="chain:a",
        source_relationship=relationship,
        evidence_state="GOVERNED_EVIDENCE",
        authority_state="AUTHORIZED" if authorized else "BLOCKED",
        authority_ready=authorized,
        reporting_allowed=authorized,
        authority_blockers=() if authorized else ("authority_missing",),
        history_identity_match=False,
        material_reader_contribution=True,
        feature_inputs=feature_inputs,
        evidence_refs=evidence_refs,
        evidence_records=evidence_records,
        governed_evidence_refs=governed_evidence_refs,
    )
    return replace(candidate, **changes)


def _feature(candidate: core.LearningCandidateV2, feature_id: str, config=None):
    rows = core.evaluate_features(
        candidate,
        config or _config(),
        contracts.PerformanceObservationSetV1("observations"),
    )
    return next(row for row in rows if row.feature_id == feature_id)


def test_canonical_gate_true_override_cannot_create_authority_contribution():
    feature = core.FeatureInputV1(
        "authority_readiness", True, contracts.AvailabilityState.AVAILABLE, 1.0,
        evidence_refs=("evidence:a",),
    )
    unauthorized = _candidate(
        authorized=False,
        feature_inputs=(feature,),
        governed_evidence_refs=(),
    )
    blocked = _feature(unauthorized, "authority_readiness")
    assert blocked.availability == contracts.AvailabilityState.BLOCKED
    assert blocked.contribution is None
    overridden = replace(
        unauthorized,
        authority_gate_results={"source_authority_ready": True},
    )
    with pytest.raises(ValueError, match="canonical_authority_gate_override_forbidden"):
        core.evaluate_features(overridden, _config(), contracts.PerformanceObservationSetV1("observations"))


@pytest.mark.parametrize("gate_id", sorted(contracts.CANONICAL_AUTHORITY_GATE_IDS))
def test_all_candidate_supplied_canonical_gate_results_are_rejected(gate_id):
    candidate = _candidate(authority_gate_results={gate_id: False})
    blockers = core.validate_candidate_collection((candidate,), _config())
    assert any(f"canonical_authority_gate_override_forbidden:{gate_id}" in row for row in blockers)


def test_unknown_and_contradictory_extension_gate_results_are_rejected():
    config = _config()
    unknown = _candidate(authority_gate_results={"extension:unknown": True})
    with pytest.raises(ValueError, match="unknown_extension_authority_gate"):
        core.evaluate_features(unknown, config, contracts.PerformanceObservationSetV1("observations"))

    disabled = _rehash(
        config,
        authority_gates={**config.authority_gates, "extension:editorial_review": False},
    )
    contradictory = _candidate(authority_gate_results={"extension:editorial_review": True})
    with pytest.raises(ValueError, match="contradictory_extension_authority_gate"):
        core.evaluate_features(contradictory, disabled, contracts.PerformanceObservationSetV1("observations"))


def test_explicitly_declared_extension_gate_can_block_or_contribute():
    config = _config()
    extension_id = "extension:editorial_review"
    features = tuple(
        replace(row, authority_gate=extension_id) if row.feature_id == "freshness" else row
        for row in config.features
    )
    extended = _rehash(
        config,
        authority_gates={**config.authority_gates, extension_id: True},
        features=features,
    )
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:a",),
    )
    blocked = _feature(
        _candidate(feature_inputs=(item,), authority_gate_results={extension_id: False}),
        "freshness",
        extended,
    )
    allowed = _feature(
        _candidate(feature_inputs=(item,), authority_gate_results={extension_id: True}),
        "freshness",
        extended,
    )
    assert blocked.availability == contracts.AvailabilityState.BLOCKED
    assert blocked.contribution is None
    assert allowed.authority_gate_result is True and allowed.contribution == pytest.approx(0.8)


@pytest.mark.parametrize(
    ("case", "refs", "declared", "error"),
    (
        ("inflated", ("evidence:a", "evidence:b"), 3, "declared=3:derived=2"),
        ("understated", ("evidence:a", "evidence:b"), 1, "declared=1:derived=2"),
    ),
)
def test_declared_evidence_count_must_exactly_match_derived_unique_count(case, refs, declared, error):
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=refs, evidence_count=declared,
    )
    candidate = _candidate(
        evidence_refs=refs,
        governed_evidence_refs=refs,
        feature_inputs=(item,),
    )
    with pytest.raises(ValueError, match=error):
        _feature(candidate, "freshness")


def test_duplicate_refs_do_not_increase_effective_evidence_count():
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:a", "evidence:a"), evidence_count=1,
    )
    row = _feature(
        _candidate(feature_inputs=(item,), evidence_refs=("evidence:a",), governed_evidence_refs=("evidence:a",)),
        "freshness",
    )
    assert row.evidence_count == 1
    assert row.evidence_refs == ("evidence:a",)


def test_record_and_direct_ref_are_deduplicated_for_evidence_count():
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:a",), evidence_count=1,
    )
    row = _feature(
        _candidate(feature_inputs=(item,), evidence_records=(_record(),)),
        "freshness",
    )
    assert row.evidence_count == 1


def test_duplicate_evidence_records_do_not_inflate_direct_feature_count():
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:a",), evidence_count=1,
    )
    row = _feature(
        _candidate(feature_inputs=(item,), evidence_records=(_record(), _record())),
        "freshness",
    )
    assert row.evidence_count == 1
    assert row.evidence_refs == ("evidence:a",)


def test_zero_and_valid_declared_evidence_counts_are_distinct():
    zero_item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=(), evidence_count=0,
    )
    zero = _feature(
        _candidate(evidence_refs=(), governed_evidence_refs=(), feature_inputs=(zero_item,)),
        "freshness",
    )
    valid_item = replace(zero_item, evidence_refs=("evidence:a", "evidence:b"), evidence_count=2)
    valid = _feature(
        _candidate(
            evidence_refs=("evidence:a", "evidence:b"),
            governed_evidence_refs=("evidence:a", "evidence:b"),
            feature_inputs=(valid_item,),
        ),
        "freshness",
    )
    assert zero.evidence_count == 0 and zero.availability == contracts.AvailabilityState.UNAVAILABLE
    assert valid.evidence_count == 2 and valid.availability == contracts.AvailabilityState.AVAILABLE


@pytest.mark.parametrize(
    ("authority", "permission", "reasons"),
    (
        ("UNVERIFIED", "REPORTING_ALLOWED", ()),
        ("VERIFIED_GOVERNED", "CONTEXT_ONLY", ()),
        ("VERIFIED_GOVERNED", "REPORTING_NOT_ALLOWED", ()),
        ("VERIFIED_GOVERNED", "REPORTING_ALLOWED", ("permission_blocked",)),
        ("VERIFIED_GOVERNED", "REPORTING_ALLOWED", ("unavailable",)),
    ),
)
def test_nonqualifying_evidence_cannot_support_governed_material_update(authority, permission, reasons):
    record = _record(authority=authority, permission=permission, reasons=reasons)
    candidate = _candidate(
        contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_records=(record,),
        governed_evidence_refs=(),
        governed_material_delta=True,
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert "GOVERNED_MATERIAL_UPDATE" not in outcome.actionable_outcomes
    assert outcome.governed_delta_present is False


def test_malformed_evidence_is_rejected_not_qualified():
    candidate = _candidate(
        contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_refs=(),
        evidence_records=(_record("bad ref"),),
        governed_evidence_refs=(),
        governed_material_delta=True,
    )
    with pytest.raises(ValueError, match="invalid_evidence_record"):
        core.evaluate_outcome(candidate, _config())


@pytest.mark.parametrize(
    ("relationship", "changes", "expected"),
    (
        (contracts.EventRelationship.MATERIAL_UPDATE, {"governed_material_delta": True}, "GOVERNED_MATERIAL_UPDATE"),
        (contracts.EventRelationship.CONFIRMATION, {"prior_testable_proposition_ref": "history:proposition", "governed_new_evidence_ref": "evidence:new"}, "GOVERNED_CONFIRMATION"),
        (contracts.EventRelationship.CONTRADICTION, {"prior_testable_proposition_ref": "history:proposition", "conflicting_evidence_ref": "evidence:conflict"}, "GOVERNED_CONTRADICTION"),
        (contracts.EventRelationship.CORRECTION, {"authoritative_correction_ref": "evidence:correction"}, "GOVERNED_CORRECTION"),
        (contracts.EventRelationship.NEW_PHASE, {"update_chain_continuity": True, "distinct_new_event_ref": "evidence:new-phase"}, "GOVERNED_NEW_PHASE"),
    ),
)
def test_every_governed_delta_requires_and_emits_qualifying_evidence_lineage(relationship, changes, expected):
    record = _record("evidence:record")
    candidate = _candidate(
        relationship,
        evidence_refs=(),
        evidence_records=(record,),
        governed_evidence_refs=(),
        **changes,
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert expected in outcome.actionable_outcomes
    assert outcome.governed_delta_present is True
    assert "evidence:record" in outcome.evidence_refs
    assert "evidence:record" in outcome.qualifying_governed_evidence_refs
    assert outcome.evidence_refs


def test_evergreen_refresh_requires_qualifying_evidence_and_authority():
    changes = {
        "gap_types": (contracts.GapType.EVERGREEN_REFRESH,),
        "durability": 0.8,
        "content_age_hours": 240.0,
        "reader_utility": 0.8,
        "update_justification_ref": "evidence:refresh",
    }
    qualified = _candidate(
        evidence_refs=(), evidence_records=(_record("evidence:record"),),
        governed_evidence_refs=(), **changes,
    )
    blocked = replace(
        qualified,
        evidence_records=(_record("evidence:record", permission="REPORTING_NOT_ALLOWED"),),
    )
    unauthorized = replace(
        qualified,
        authority_ready=False,
        reporting_allowed=False,
        authority_blockers=("authority_missing",),
    )
    assert "EVERGREEN_REFRESH_JUSTIFIED" in core.evaluate_outcome(qualified, _config()).actionable_outcomes
    assert "EVERGREEN_REFRESH_JUSTIFIED" not in core.evaluate_outcome(blocked, _config()).actionable_outcomes
    assert "EVERGREEN_REFRESH_JUSTIFIED" not in core.evaluate_outcome(unauthorized, _config()).actionable_outcomes


def test_outcome_evidence_lineage_is_complete_and_deduplicated():
    candidate = _candidate(
        contracts.EventRelationship.CONFIRMATION,
        evidence_refs=("evidence:a", "evidence:b"),
        evidence_records=(_record("evidence:b"), _record("evidence:c")),
        governed_evidence_refs=("evidence:a",),
        prior_testable_proposition_ref="history:proposition",
        governed_new_evidence_ref="evidence:new",
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert outcome.evidence_refs == ("evidence:a", "evidence:b", "evidence:c", "evidence:new")


@pytest.mark.parametrize(
    ("relationship", "changes", "expected"),
    (
        (contracts.EventRelationship.MATERIAL_UPDATE, {"governed_material_delta": True}, "GOVERNED_MATERIAL_UPDATE"),
        (contracts.EventRelationship.CONFIRMATION, {"prior_testable_proposition_ref": "history:proposition", "governed_new_evidence_ref": "evidence:new"}, "GOVERNED_CONFIRMATION"),
        (contracts.EventRelationship.CONTRADICTION, {"prior_testable_proposition_ref": "history:proposition", "conflicting_evidence_ref": "evidence:conflict"}, "GOVERNED_CONTRADICTION"),
        (contracts.EventRelationship.CORRECTION, {"authoritative_correction_ref": "evidence:correction"}, "GOVERNED_CORRECTION"),
        (contracts.EventRelationship.NEW_PHASE, {"update_chain_continuity": True, "distinct_new_event_ref": "evidence:new-phase"}, "GOVERNED_NEW_PHASE"),
    ),
)
def test_identity_match_with_real_governed_delta_is_not_unchanged_duplicate(relationship, changes, expected):
    candidate = _candidate(
        relationship,
        evidence_records=(_record(),),
        history_identity_match=True,
        **changes,
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert expected in outcome.actionable_outcomes
    assert "DUPLICATE_NO_NEW_DELTA" not in outcome.actionable_outcomes
    assert outcome.history_relationship == "PUBLISHED_IDENTITY_MATCH_WITH_GOVERNED_DELTA"
    assert outcome.history_identity_match is True
    assert outcome.governed_delta_present is True


def test_true_unchanged_duplicate_keeps_duplicate_no_new_delta():
    candidate = _candidate(
        contracts.EventRelationship.DUPLICATE,
        history_identity_match=True,
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert "DUPLICATE_NO_NEW_DELTA" in outcome.actionable_outcomes
    assert outcome.history_relationship == "PUBLISHED_IDENTITY_MATCH_NO_NEW_DELTA"
    assert outcome.history_identity_match is True
    assert outcome.governed_delta_present is False


@pytest.mark.parametrize(
    "governed_outcome",
    (
        "GOVERNED_MATERIAL_UPDATE",
        "GOVERNED_CONFIRMATION",
        "GOVERNED_CONTRADICTION",
        "GOVERNED_CORRECTION",
        "GOVERNED_NEW_PHASE",
    ),
)
def test_governed_delta_and_duplicate_no_new_delta_are_incompatible(governed_outcome):
    with pytest.raises(ValueError, match="incompatible_actionable_outcomes"):
        core._validate_actionable_outcomes((governed_outcome, "DUPLICATE_NO_NEW_DELTA"))


def test_repair_preserves_uncalibrated_config_and_no_publication_boundary():
    config = _config()
    candidate = _candidate(
        contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_records=(_record(),),
        governed_material_delta=True,
    )
    outcome = core.evaluate_outcome(candidate, config)
    assert config.calibration_state == contracts.CalibrationState.UNCALIBRATED_FOUNDATION
    assert outcome.publication_disposition == "INTERNAL_BRIEF_ELIGIBLE_OPERATOR_REVIEW_NO_PUBLICATION_AUTHORITY"


@pytest.mark.parametrize(
    "builder",
    (
        repair.build_authority_gate_override_matrix,
        repair.build_evidence_count_integrity_matrix,
        repair.build_governed_evidence_qualification_matrix,
        repair.build_governed_evidence_lineage_report,
        repair.build_duplicate_delta_semantic_matrix,
    ),
)
def test_machine_derived_repair_matrices_pass(builder):
    report = builder(ROOT)
    assert report["status"] == "PASS"
    assert report["rows"]
    assert all(row["status"] == "PASS" for row in report["rows"])


def test_core_repair_reports_are_deterministic():
    assert contracts.canonical_json(repair.build_core_reports(ROOT)) == contracts.canonical_json(repair.build_core_reports(ROOT))


def test_repair_evidence_manifest_binds_all_nonself_artifacts(tmp_path):
    manifest = repair.generate_evidence(
        repo_root=ROOT,
        validation_summary={"focused_repair_pytest": "pending_test_probe", "status": "PASS"},
        changed_paths=("live_contentops/adaptive_learning_core_v2.py",),
        protected_paths={"v1_0_tag_object": "a021df7fd0264d9f160bdd605509da925f0bf131"},
        unrelated_worktree={"preserved": True},
        output_dir=tmp_path,
    )
    assert manifest["terminal_classification"] == repair.TERMINAL_CLASSIFICATION
    assert set(path.name for path in tmp_path.iterdir()) == set(repair.REQUIRED_ARTIFACTS)
    for name, expected_hash in manifest["artifact_sha256"].items():
        assert contracts.sha256((tmp_path / name).read_bytes()).hexdigest() == expected_hash
