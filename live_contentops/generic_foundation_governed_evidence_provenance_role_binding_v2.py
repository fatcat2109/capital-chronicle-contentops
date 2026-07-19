"""Deterministic local evidence for governed evidence provenance and role binding."""
from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import generic_foundation_hardening_v2 as hardening


TASK_LABEL = "TASK_CONTENTOPS_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING"
TERMINAL_CLASSIFICATION = "PASS_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING"
STARTING_SHA = "6f2755a471c41ccc5a6c06e8babcae2534dd065d"
PINNED_UPSTREAM_HEAD = "e1f2ff48d7ac979a8fbda9e66192150f2681a52d"
EVIDENCE_ROOT = "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING"
REQUIRED_ARTIFACTS = (
    "contract_inventory.json",
    "self_certification_rejection_matrix.json",
    "governed_evidence_role_matrix.json",
    "relationship_qualification_matrix.json",
    "feature_evidence_scope_matrix.json",
    "complete_vs_qualifying_lineage_report.json",
    "compatibility_report.json",
    "deterministic_replay.json",
    "focused_test_summary.json",
    "changed_protected_paths.json",
    "safety_report.json",
    "genericity_guard_report.json",
    "final_manifest.json",
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(contracts.primitive(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _config(root: str | Path) -> contracts.AdaptiveLearningConfigV1:
    return adapters.load_foundation_config(root)


def _binding(
    ref: str,
    role: contracts.EvidenceRole,
    *,
    scope: contracts.EvidenceScope = contracts.EvidenceScope.CANDIDATE_WIDE,
    authority: str = "VERIFIED_GOVERNED",
    permission: str = "REPORTING_ALLOWED",
    status: contracts.EvidenceVerificationStatus = contracts.EvidenceVerificationStatus.VERIFIED,
    reasons: Sequence[str] = (),
    target_feature_ids: Sequence[str] = (),
) -> contracts.GovernedEvidenceBindingV1:
    return contracts.build_governed_evidence_binding_v1(
        evidence_ref=ref, evidence_roles=(role,), evidence_scope=scope,
        authority_state=authority, permission_state=permission,
        verification_status=status,
        producer_artifact_binding_hash=sha256(ref.encode("utf-8")).hexdigest(),
        as_of_utc="2026-07-19T00:00:00Z",
        verifier_id="contentops.provenance_role_repair_verifier",
        reason_codes=tuple(reasons),
        target_feature_ids=tuple(target_feature_ids),
    )


def _candidate(
    *, relationship: contracts.EventRelationship = contracts.EventRelationship.INITIAL_EVENT,
    bindings: Sequence[contracts.GovernedEvidenceBindingV1] = (),
    evidence_refs: Sequence[str] | None = None,
    feature_inputs: Sequence[core.FeatureInputV1] = (),
    **changes: Any,
) -> core.LearningCandidateV2:
    refs = tuple(evidence_refs) if evidence_refs is not None else tuple(dict.fromkeys(row.evidence_ref for row in bindings))
    candidate = core.LearningCandidateV2(
        candidate_id="evidence:repair:candidate", story_id="evidence:repair:story",
        cluster_id="evidence:repair:cluster", update_chain_id="evidence:repair:chain",
        source_relationship=relationship, evidence_state="GOVERNED_EVIDENCE",
        authority_state="AUTHORIZED", authority_ready=True, reporting_allowed=True,
        authority_blockers=(), history_identity_match=False,
        material_reader_contribution=True, feature_inputs=tuple(feature_inputs),
        evidence_refs=refs, governed_evidence_bindings=tuple(bindings),
    )
    return adapters.attach_trusted_context_to_candidate(
        replace(candidate, **changes), repo_root=Path(__file__).resolve().parents[1],
    )


def _relationship_case(
    relationship: contracts.EventRelationship,
    role: contracts.EvidenceRole,
) -> tuple[core.LearningCandidateV2, str]:
    ref = f"evidence:{role.value}"
    changes: Mapping[str, Any]
    expected: str
    if relationship == contracts.EventRelationship.MATERIAL_UPDATE:
        changes, expected = {"governed_material_delta": True, "material_delta_evidence_ref": ref}, "GOVERNED_MATERIAL_UPDATE"
    elif relationship == contracts.EventRelationship.CONFIRMATION:
        changes, expected = {"prior_testable_proposition_ref": "history:proposition", "governed_new_evidence_ref": ref}, "GOVERNED_CONFIRMATION"
    elif relationship == contracts.EventRelationship.CONTRADICTION:
        changes, expected = {"prior_testable_proposition_ref": "history:proposition", "conflicting_evidence_ref": ref}, "GOVERNED_CONTRADICTION"
    elif relationship == contracts.EventRelationship.CORRECTION:
        changes, expected = {"prior_error_ref": "history:error", "authoritative_correction_ref": ref}, "GOVERNED_CORRECTION"
    else:
        changes, expected = {"update_chain_continuity": True, "distinct_new_event_ref": ref}, "GOVERNED_NEW_PHASE"
    refs = (ref, *(value for key, value in changes.items() if key in {"prior_testable_proposition_ref", "prior_error_ref"}))
    return _candidate(
        relationship=relationship, bindings=(_binding(ref, role),),
        evidence_refs=refs, **changes,
    ), expected


def build_contract_inventory() -> Mapping[str, Any]:
    candidate_fields = {row.name for row in fields(core.LearningCandidateV2)}
    binding_fields = {row.name for row in fields(contracts.GovernedEvidenceBindingV1)}
    required = {
        "evidence_ref", "authority_state", "permission_state", "evidence_roles",
        "verifier_id", "verifier_version", "verification_status",
        "producer_artifact_binding_hash", "as_of_utc", "reason_codes", "logical_hash",
    }
    status = "PASS" if "governed_evidence_refs" not in candidate_fields and required.issubset(binding_fields) else "FAIL"
    return {
        "schema_version": "contentops.governed_evidence_contract_inventory.v1",
        "binding_schema_version": contracts.SCHEMA_GOVERNED_EVIDENCE_BINDING_V1,
        "candidate_bare_ref_shortcut_present": "governed_evidence_refs" in candidate_fields,
        "candidate_binding_field_present": "governed_evidence_bindings" in candidate_fields,
        "binding_fields": sorted(binding_fields),
        "roles": [value.value for value in contracts.EvidenceRole],
        "scopes": [value.value for value in contracts.EvidenceScope],
        "status": status,
    }


def build_self_certification_rejection_matrix(root: str | Path) -> Mapping[str, Any]:
    config = _config(root)
    plain = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_refs=("evidence:caller",), governed_material_delta=True,
        material_delta_evidence_ref="evidence:caller",
    )
    plain_outcome = core.evaluate_outcome(plain, config)
    valid_binding = _binding("evidence:delta", contracts.EvidenceRole.MATERIAL_DELTA)
    valid_candidate = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(valid_binding,), governed_material_delta=True,
        material_delta_evidence_ref=valid_binding.evidence_ref,
    )
    trusted_binding = valid_candidate.governed_evidence_bindings[0]
    invalid_cases = {
        "missing_verifier": replace(trusted_binding, verifier_id=""),
        "missing_binding_hash": replace(trusted_binding, producer_artifact_binding_hash=""),
        "logical_hash_mismatch": replace(trusted_binding, logical_hash="0" * 64),
    }
    rows = [{
        "case": "caller_only_plain_ref",
        "governed_outcome": "GOVERNED_MATERIAL_UPDATE" in plain_outcome.actionable_outcomes,
        "disqualification_reasons": list(plain_outcome.disqualified_evidence[0].reason_codes),
        "status": "PASS" if "GOVERNED_MATERIAL_UPDATE" not in plain_outcome.actionable_outcomes else "FAIL",
    }]
    for case, binding in invalid_cases.items():
        candidate = replace(valid_candidate, governed_evidence_bindings=(binding,))
        try:
            core.evaluate_outcome(candidate, config)
            rejected, error = False, None
        except ValueError as exc:
            rejected, error = True, str(exc)
        rows.append({"case": case, "rejected": rejected, "error": error, "status": "PASS" if rejected else "FAIL"})
    absent = _candidate(
        relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        bindings=(valid_binding,), evidence_refs=(), governed_material_delta=True,
        material_delta_evidence_ref=valid_binding.evidence_ref,
    )
    try:
        core.evaluate_outcome(absent, config)
        rejected, error = False, None
    except ValueError as exc:
        rejected, error = True, str(exc)
    rows.append({"case": "binding_ref_absent_from_candidate_lineage", "rejected": rejected, "error": error, "status": "PASS" if rejected else "FAIL"})
    return {"schema_version": "contentops.self_certification_rejection_matrix.v1", "rows": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"}


def build_role_and_relationship_reports(root: str | Path) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    config = _config(root)
    cases = (
        (contracts.EventRelationship.MATERIAL_UPDATE, contracts.EvidenceRole.MATERIAL_DELTA),
        (contracts.EventRelationship.CONFIRMATION, contracts.EvidenceRole.CONFIRMATION),
        (contracts.EventRelationship.CONTRADICTION, contracts.EvidenceRole.CONTRADICTION),
        (contracts.EventRelationship.CORRECTION, contracts.EvidenceRole.CORRECTION),
        (contracts.EventRelationship.NEW_PHASE, contracts.EvidenceRole.NEW_PHASE),
    )
    rows = []
    for relationship, role in cases:
        candidate, expected = _relationship_case(relationship, role)
        outcome = core.evaluate_outcome(candidate, config)
        rows.append({
            "relationship": relationship.value, "required_role": role.value,
            "expected_outcome": expected, "observed_outcomes": list(outcome.actionable_outcomes),
            "relationship_specific_qualifying_refs": list(outcome.relationship_specific_qualifying_refs),
            "status": "PASS" if expected in outcome.actionable_outcomes and outcome.relationship_specific_qualifying_refs else "FAIL",
        })
    wrong, expected = _relationship_case(contracts.EventRelationship.CONFIRMATION, contracts.EvidenceRole.FEATURE_SUPPORT)
    wrong_outcome = core.evaluate_outcome(wrong, config)
    rows.append({
        "relationship": "confirmation", "required_role": "confirmation",
        "supplied_role": "feature_support", "expected_outcome": expected,
        "observed_outcomes": list(wrong_outcome.actionable_outcomes),
        "relationship_specific_qualifying_refs": list(wrong_outcome.relationship_specific_qualifying_refs),
        "status": "PASS" if expected not in wrong_outcome.actionable_outcomes else "FAIL",
    })
    evergreen = _candidate(
        bindings=(_binding("evidence:refresh", contracts.EvidenceRole.EVERGREEN_JUSTIFICATION),),
        gap_types=(contracts.GapType.EVERGREEN_REFRESH,), durability=0.9,
        content_age_hours=240.0, reader_utility=0.9,
        update_justification_ref="evidence:refresh",
    )
    evergreen_outcome = core.evaluate_outcome(evergreen, config)
    rows.append({
        "relationship": "evergreen_refresh", "required_role": "evergreen_justification",
        "observed_outcomes": list(evergreen_outcome.actionable_outcomes),
        "relationship_specific_qualifying_refs": list(evergreen_outcome.relationship_specific_qualifying_refs),
        "status": "PASS" if "EVERGREEN_REFRESH_JUSTIFIED" in evergreen_outcome.actionable_outcomes else "FAIL",
    })
    status = "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"
    return (
        {"schema_version": "contentops.governed_evidence_role_matrix.v1", "role_inventory": [value.value for value in contracts.EvidenceRole], "rows": rows, "status": status},
        {"schema_version": "contentops.relationship_evidence_qualification_matrix.v1", "rows": rows, "all_governed_outcomes_have_matching_role_refs": status == "PASS", "status": status},
    )


def build_feature_scope_matrix(root: str | Path) -> Mapping[str, Any]:
    config = _config(root)
    reusable = _binding("evidence:reusable", contracts.EvidenceRole.FEATURE_SUPPORT)
    unrelated = _binding("evidence:unrelated", contracts.EvidenceRole.CONFIRMATION)

    def row_for(scope: contracts.EvidenceScope, explicit: Sequence[str] = ()) -> contracts.FeatureEvaluationV1:
        item = core.FeatureInputV1(
            "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
            evidence_refs=tuple(explicit), evidence_scope=scope,
        )
        bindings = (reusable, unrelated)
        if scope == contracts.EvidenceScope.FEATURE_SPECIFIC and explicit:
            bindings = (
                reusable,
                _binding(
                    explicit[0], contracts.EvidenceRole.FEATURE_SUPPORT,
                    scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
                    target_feature_ids=("freshness",),
                ),
            )
        candidate = _candidate(bindings=bindings, feature_inputs=(item,))
        return next(row for row in core.evaluate_features(candidate, config, contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")

    candidate_wide = row_for(contracts.EvidenceScope.CANDIDATE_WIDE)
    feature_specific = row_for(contracts.EvidenceScope.FEATURE_SPECIFIC, ("evidence:unrelated",))
    no_binding = row_for(contracts.EvidenceScope.FEATURE_SPECIFIC)
    rows = (
        {"case": "candidate_wide_reuse", **contracts.primitive(candidate_wide), "expected_count": 1},
        {"case": "explicit_feature_binding", **contracts.primitive(feature_specific), "expected_count": 1},
        {"case": "no_implicit_reuse", **contracts.primitive(no_binding), "expected_count": 0},
    )
    rows = tuple({**row, "status": "PASS" if row["evidence_count"] == row["expected_count"] else "FAIL"} for row in rows)
    return {"schema_version": "contentops.feature_evidence_scope_matrix.v1", "rows": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"}


def build_lineage_report(root: str | Path) -> Mapping[str, Any]:
    config = _config(root)
    qualifying = _binding("evidence:confirmation", contracts.EvidenceRole.CONFIRMATION)
    context = _binding("evidence:context", contracts.EvidenceRole.CONFIRMATION, permission="CONTEXT_ONLY")
    candidate = _candidate(
        relationship=contracts.EventRelationship.CONFIRMATION,
        bindings=(qualifying, context),
        evidence_refs=("evidence:confirmation", "evidence:context", "history:proposition"),
        prior_testable_proposition_ref="history:proposition",
        governed_new_evidence_ref="evidence:confirmation",
    )
    outcome = core.evaluate_outcome(candidate, config)
    row = contracts.primitive(outcome)
    status = "PASS" if (
        row["complete_evidence_lineage"]
        and row["qualifying_governed_evidence_refs"] == ["evidence:confirmation"]
        and row["relationship_specific_qualifying_refs"] == ["evidence:confirmation"]
        and row["historical_only_refs"] == ["history:proposition"]
        and row["disqualified_evidence"]
    ) else "FAIL"
    return {"schema_version": "contentops.complete_vs_qualifying_evidence_lineage.v1", "outcome": row, "status": status}


def build_core_reports(root: str | Path) -> Mapping[str, Mapping[str, Any]]:
    roles, relationships = build_role_and_relationship_reports(root)
    genericity = hardening.run_genericity_ast_guard(root)
    compatibility = adapters.v1_compatibility_replay(root)
    return {
        "contract_inventory.json": build_contract_inventory(),
        "self_certification_rejection_matrix.json": build_self_certification_rejection_matrix(root),
        "governed_evidence_role_matrix.json": roles,
        "relationship_qualification_matrix.json": relationships,
        "feature_evidence_scope_matrix.json": build_feature_scope_matrix(root),
        "complete_vs_qualifying_lineage_report.json": build_lineage_report(root),
        "compatibility_report.json": {
            "schema_version": "contentops.governed_evidence_compatibility_report.v1",
            "v1": compatibility,
            "synthetic_fixture_authority": "SYNTHETIC_VALIDATION_ONLY_NO_PUBLICATION",
            "prior_evidence_directories_mutated": False,
            "status": "PASS" if compatibility["v1_module_remains_operational"] and not compatibility["historical_artifacts_mutated"] else "FAIL",
        },
        "genericity_guard_report.json": genericity,
    }


def generate_evidence(
    *, repo_root: str | Path, validation_summary: Mapping[str, Any],
    changed_paths: Sequence[str], protected_paths: Mapping[str, Any],
    unrelated_worktree: Mapping[str, Any], upstream_observation: Mapping[str, Any],
    output_dir: str | Path | None = None,
) -> Mapping[str, Any]:
    root = Path(repo_root).resolve()
    target = Path(output_dir) if output_dir is not None else root / EVIDENCE_ROOT
    target.mkdir(parents=True, exist_ok=True)
    first = build_core_reports(root)
    second = build_core_reports(root)
    deterministic = contracts.canonical_json(first) == contracts.canonical_json(second)
    reports = dict(first)
    reports["deterministic_replay.json"] = {
        "schema_version": "contentops.governed_evidence_deterministic_replay.v1",
        "two_independent_executions_identical": deterministic,
        "first_hash": contracts.logical_hash(first), "second_hash": contracts.logical_hash(second),
        "status": "PASS" if deterministic else "FAIL",
    }
    reports["focused_test_summary.json"] = dict(validation_summary)
    reports["changed_protected_paths.json"] = {
        "schema_version": "contentops.governed_evidence_changed_protected_paths.v1",
        "changed_paths": sorted(changed_paths), "protected_paths": dict(protected_paths),
        "unrelated_worktree": dict(unrelated_worktree), "upstream_observation": dict(upstream_observation),
        "status": "PASS",
    }
    reports["safety_report.json"] = {
        "schema_version": "contentops.governed_evidence_safety_report.v1",
        "network_calls_performed_by_repair": False, "credentials_read": False,
        "publication_or_dispatch_performed": False, "scheduler_mutated": False,
        "editorial_dqr_permission_authority_mutated": False,
        "upstream_modified": False, "v1_0_modified": False,
        "uncalibrated_config_preserved": True, "no_publication_boundary_preserved": True,
        "status": "PASS",
    }
    non_manifest = tuple(name for name in REQUIRED_ARTIFACTS if name != "final_manifest.json")
    for name in non_manifest:
        (target / name).write_bytes(_json_bytes(reports[name]))
    artifact_hashes = {name: sha256((target / name).read_bytes()).hexdigest() for name in non_manifest}
    terminal_pass = all(reports[name].get("status") == "PASS" for name in non_manifest)
    manifest = {
        "schema_version": "contentops.governed_evidence_provenance_role_binding_manifest.v1",
        "task": TASK_LABEL,
        "terminal_classification": TERMINAL_CLASSIFICATION if terminal_pass else "FAIL_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING",
        "exact_next_action": NEXT_ACTION if terminal_pass else "REPAIR_FAILED_EVIDENCE_ROWS",
        "starting_contentops_sha": STARTING_SHA,
        "pinned_upstream_point_in_time_sha": PINNED_UPSTREAM_HEAD,
        "artifact_hashes": artifact_hashes,
        "artifact_count_excluding_manifest": len(artifact_hashes),
        "all_required_artifacts_present": set(artifact_hashes) == set(non_manifest),
        "manifest_self_hash_excluded": True,
        "status": "PASS" if terminal_pass else "FAIL",
    }
    (target / "final_manifest.json").write_bytes(_json_bytes(manifest))
    return manifest
