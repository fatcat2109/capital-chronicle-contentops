from dataclasses import fields, replace
from pathlib import Path

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import generic_foundation_governed_evidence_provenance_role_binding_v2 as repair


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return adapters.load_foundation_config(ROOT)


def _binding(
    ref: str,
    role: contracts.EvidenceRole,
    *,
    scope: contracts.EvidenceScope = contracts.EvidenceScope.CANDIDATE_WIDE,
    authority: str = "VERIFIED_GOVERNED",
    permission: str = "REPORTING_ALLOWED",
    status: contracts.EvidenceVerificationStatus = contracts.EvidenceVerificationStatus.VERIFIED,
    reasons: tuple[str, ...] = (),
):
    return contracts.build_governed_evidence_binding_v1(
        evidence_ref=ref,
        evidence_roles=(role,),
        evidence_scope=scope,
        authority_state=authority,
        permission_state=permission,
        verification_status=status,
        producer_artifact_binding_hash="9" * 64,
        as_of_utc="2026-07-19T00:00:00Z",
        reason_codes=reasons,
    )


def _candidate(*, relationship=contracts.EventRelationship.INITIAL_EVENT, bindings=(), evidence_refs=None, feature_inputs=(), **changes):
    refs = tuple(evidence_refs) if evidence_refs is not None else tuple(dict.fromkeys(row.evidence_ref for row in bindings))
    candidate = core.LearningCandidateV2(
        candidate_id="provenance:candidate", story_id="provenance:story",
        cluster_id="provenance:cluster", update_chain_id="provenance:chain",
        source_relationship=relationship, evidence_state="GOVERNED_EVIDENCE",
        authority_state="AUTHORIZED", authority_ready=True, reporting_allowed=True,
        authority_blockers=(), history_identity_match=False,
        material_reader_contribution=True, feature_inputs=tuple(feature_inputs),
        evidence_refs=refs, governed_evidence_bindings=tuple(bindings),
    )
    return replace(candidate, **changes)


def _outcome_candidate(relationship, ref, role):
    changes = {
        contracts.EventRelationship.MATERIAL_UPDATE: dict(governed_material_delta=True, material_delta_evidence_ref=ref),
        contracts.EventRelationship.CONFIRMATION: dict(prior_testable_proposition_ref="history:proposition", governed_new_evidence_ref=ref),
        contracts.EventRelationship.CONTRADICTION: dict(prior_testable_proposition_ref="history:proposition", conflicting_evidence_ref=ref),
        contracts.EventRelationship.CORRECTION: dict(prior_error_ref="history:error", authoritative_correction_ref=ref),
        contracts.EventRelationship.NEW_PHASE: dict(update_chain_continuity=True, distinct_new_event_ref=ref),
    }[relationship]
    return _candidate(relationship=relationship, bindings=(_binding(ref, role),), **changes)


def test_bare_governed_ref_shortcut_is_removed_and_plain_ref_is_disqualified():
    assert "governed_evidence_refs" not in {row.name for row in fields(core.LearningCandidateV2)}
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_refs=("evidence:caller",), governed_material_delta=True,
        material_delta_evidence_ref="evidence:caller",
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert "GOVERNED_MATERIAL_UPDATE" not in outcome.actionable_outcomes
    assert outcome.disqualified_evidence[0].reason_codes == ("caller_only_assertion_without_validated_provenance",)


@pytest.mark.parametrize("mutation,expected", [
    ({"verifier_id": ""}, "invalid_governed_evidence_binding"),
    ({"producer_artifact_binding_hash": ""}, "invalid_governed_evidence_binding"),
    ({"logical_hash": "0" * 64}, "evidence_logical_hash_mismatch"),
])
def test_missing_verifier_binding_hash_and_logical_mismatch_are_rejected(mutation, expected):
    binding = replace(_binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA), **mutation)
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(binding,), governed_material_delta=True,
        material_delta_evidence_ref="evidence:delta",
    )
    with pytest.raises(ValueError, match=expected):
        core.evaluate_outcome(candidate, _config())


def test_binding_ref_absent_from_candidate_lineage_is_rejected():
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(_binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA),),
        evidence_refs=(), governed_material_delta=True,
        material_delta_evidence_ref="evidence:delta",
    )
    with pytest.raises(ValueError, match="governed_evidence_ref_missing_from_lineage"):
        core.evaluate_outcome(candidate, _config())


@pytest.mark.parametrize("binding", [
    _binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA, authority="UNVERIFIED"),
    _binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA, permission="CONTEXT_ONLY"),
    _binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA, status=contracts.EvidenceVerificationStatus.BLOCKED),
    _binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA, reasons=("unavailable",)),
])
def test_unverified_context_blocked_and_unavailable_bindings_cannot_govern(binding):
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(binding,), governed_material_delta=True,
        material_delta_evidence_ref="evidence:delta",
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert "GOVERNED_MATERIAL_UPDATE" not in outcome.actionable_outcomes
    assert outcome.disqualified_evidence


@pytest.mark.parametrize("relationship,role,expected", [
    (contracts.EventRelationship.MATERIAL_UPDATE, contracts.EvidenceRole.MATERIAL_DELTA, "GOVERNED_MATERIAL_UPDATE"),
    (contracts.EventRelationship.CONFIRMATION, contracts.EvidenceRole.CONFIRMATION, "GOVERNED_CONFIRMATION"),
    (contracts.EventRelationship.CONTRADICTION, contracts.EvidenceRole.CONTRADICTION, "GOVERNED_CONTRADICTION"),
    (contracts.EventRelationship.CORRECTION, contracts.EvidenceRole.CORRECTION, "GOVERNED_CORRECTION"),
    (contracts.EventRelationship.NEW_PHASE, contracts.EvidenceRole.NEW_PHASE, "GOVERNED_NEW_PHASE"),
])
def test_each_governed_relationship_requires_and_emits_its_matching_role(relationship, role, expected):
    outcome = core.evaluate_outcome(_outcome_candidate(relationship, "evidence:relationship", role), _config())
    assert expected in outcome.actionable_outcomes
    assert outcome.relationship_specific_qualifying_refs == ("evidence:relationship",)
    assert outcome.qualifying_governed_evidence_refs


def test_unrelated_qualifying_role_cannot_satisfy_relationship():
    candidate = _outcome_candidate(
        contracts.EventRelationship.CONFIRMATION,
        "evidence:confirmation",
        contracts.EvidenceRole.FEATURE_SUPPORT,
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert "GOVERNED_CONFIRMATION" not in outcome.actionable_outcomes
    assert outcome.relationship_specific_qualifying_refs == ()


def test_evergreen_requires_justification_ref_itself_to_have_evergreen_role():
    valid = _candidate(
        bindings=(_binding("evidence:refresh", contracts.EvidenceRole.EVERGREEN_JUSTIFICATION),),
        gap_types=(contracts.GapType.EVERGREEN_REFRESH,), durability=0.9,
        content_age_hours=240.0, reader_utility=0.9,
        update_justification_ref="evidence:refresh",
    )
    wrong = replace(valid, governed_evidence_bindings=(_binding("evidence:refresh", contracts.EvidenceRole.CONFIRMATION),))
    assert "EVERGREEN_REFRESH_JUSTIFIED" in core.evaluate_outcome(valid, _config()).actionable_outcomes
    assert "EVERGREEN_REFRESH_JUSTIFIED" not in core.evaluate_outcome(wrong, _config()).actionable_outcomes


def test_equivalent_provenance_evidence_reference_can_support_governed_outcome():
    record = contracts.build_evidence_reference_v1(
        evidence_ref="evidence:record", authority_state="OFFICIAL_VERIFIED",
        permission_state="PUBLIC_CLAIM_ALLOWED",
        evidence_roles=(contracts.EvidenceRole.MATERIAL_DELTA,),
        evidence_scope=contracts.EvidenceScope.CANDIDATE_WIDE,
        producer_artifact_binding_hash="8" * 64,
        as_of_utc="2026-07-19T00:00:00Z",
    )
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_refs=(record.evidence_ref,), governed_material_delta=True,
        material_delta_evidence_ref=record.evidence_ref,
        evidence_records=(record,),
    )
    assert "GOVERNED_MATERIAL_UPDATE" in core.evaluate_outcome(candidate, _config()).actionable_outcomes


def test_unrelated_candidate_records_do_not_inflate_feature_evidence_count():
    reusable = _binding("evidence:reusable", contracts.EvidenceRole.FEATURE_SUPPORT)
    unrelated = _binding("evidence:unrelated", contracts.EvidenceRole.CONFIRMATION)
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_scope=contracts.EvidenceScope.CANDIDATE_WIDE,
    )
    candidate = _candidate(bindings=(reusable, unrelated), feature_inputs=(item,))
    row = next(row for row in core.evaluate_features(candidate, _config(), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert row.evidence_refs == ("evidence:reusable",)
    assert row.evidence_count == 1
    assert row.excluded_evidence_refs == ("evidence:unrelated",)
    assert row.evidence_exclusion_reasons["evidence:unrelated"] == ("feature_support_role_missing",)


def test_feature_specific_scope_does_not_reuse_candidate_wide_evidence_implicitly():
    binding = _binding("evidence:reusable", contracts.EvidenceRole.FEATURE_SUPPORT)
    item = core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8)
    candidate = _candidate(bindings=(binding,), feature_inputs=(item,))
    row = next(row for row in core.evaluate_features(candidate, _config(), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert row.evidence_count == 0
    assert row.availability == contracts.AvailabilityState.UNAVAILABLE


def test_complete_qualifying_historical_relationship_and_disqualified_lineage_are_separate():
    qualifying = _binding("evidence:confirmation", contracts.EvidenceRole.CONFIRMATION)
    blocked = _binding("evidence:context", contracts.EvidenceRole.CONFIRMATION, permission="CONTEXT_ONLY")
    candidate = _candidate(
        relationship=contracts.EventRelationship.CONFIRMATION,
        bindings=(qualifying, blocked),
        evidence_refs=("evidence:confirmation", "evidence:context", "history:proposition"),
        prior_testable_proposition_ref="history:proposition",
        governed_new_evidence_ref="evidence:confirmation",
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert set(outcome.complete_evidence_lineage) == {"evidence:confirmation", "evidence:context", "history:proposition"}
    assert outcome.qualifying_governed_evidence_refs == ("evidence:confirmation",)
    assert outcome.relationship_specific_qualifying_refs == ("evidence:confirmation",)
    assert outcome.historical_only_refs == ("history:proposition",)
    assert outcome.disqualified_evidence[0].evidence_ref == "evidence:context"


def test_synthetic_governed_binding_never_grants_publication():
    candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(contracts.build_governed_evidence_binding_v1(
            evidence_ref="synthetic:delta", evidence_roles=(contracts.EvidenceRole.MATERIAL_DELTA,),
            authority_state="SYNTHETIC_AUTHORIZED",
            producer_artifact_binding_hash="7" * 64,
            as_of_utc="2026-07-19T00:00:00Z",
        ),),
        governed_material_delta=True, material_delta_evidence_ref="synthetic:delta",
    )
    outcome = core.evaluate_outcome(candidate, _config())
    assert outcome.publication_disposition == "INTERNAL_BRIEF_ELIGIBLE_OPERATOR_REVIEW_NO_PUBLICATION_AUTHORITY"


def test_machine_derived_repair_reports_are_pass_and_deterministic():
    first = repair.build_core_reports(ROOT)
    second = repair.build_core_reports(ROOT)
    assert all(report["status"] == "PASS" for report in first.values())
    assert contracts.canonical_json(first) == contracts.canonical_json(second)


def test_final_manifest_hashes_every_nonself_artifact(tmp_path):
    manifest = repair.generate_evidence(
        repo_root=ROOT,
        validation_summary={"schema_version": "test", "status": "PASS"},
        changed_paths=("live_contentops/adaptive_learning_core_v2.py",),
        protected_paths={"v1_0_modified": False},
        unrelated_worktree={"preserved": True},
        upstream_observation={"pinned_sha": repair.PINNED_UPSTREAM_HEAD},
        output_dir=tmp_path,
    )
    assert manifest["terminal_classification"] == repair.TERMINAL_CLASSIFICATION
    assert set(manifest["artifact_hashes"]) == set(repair.REQUIRED_ARTIFACTS) - {"final_manifest.json"}
    assert all((tmp_path / name).is_file() for name in repair.REQUIRED_ARTIFACTS)
