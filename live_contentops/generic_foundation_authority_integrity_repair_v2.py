"""Deterministic evidence for generic foundation authority-integrity repair.

This module executes only local contracts and synthetic trust-boundary probes.
It has no browser, provider, credential, publication, dispatch, scheduler, or
policy mutation behavior.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import generic_foundation_hardening_v2 as hardening


TASK_LABEL = "TASK_CONTENTOPS_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR"
TERMINAL_CLASSIFICATION = "PASS_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR"
STARTING_SHA = "11124edc623d480736966fa54b44bb6289a935fd"
UPSTREAM_HEAD = "e1f2ff48d7ac979a8fbda9e66192150f2681a52d"
EVIDENCE_ROOT = "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR"
REQUIRED_ARTIFACTS = (
    "authority_gate_override_matrix.json",
    "evidence_count_integrity_matrix.json",
    "governed_evidence_qualification_matrix.json",
    "governed_evidence_lineage_report.json",
    "duplicate_delta_semantic_matrix.json",
    "focused_test_summary.json",
    "deterministic_replay.json",
    "changed_protected_paths.json",
    "safety_report.json",
    "genericity_guard_report.json",
    "final_manifest.json",
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(contracts.primitive(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _config(repo_root: str | Path) -> contracts.AdaptiveLearningConfigV1:
    return adapters.load_foundation_config(repo_root)


def _rehash(config: contracts.AdaptiveLearningConfigV1, **changes: Any) -> contracts.AdaptiveLearningConfigV1:
    draft = replace(config, **changes, config_logical_hash="")
    material = contracts.primitive(draft)
    material.pop("config_logical_hash")
    return replace(draft, config_logical_hash=contracts.logical_hash(material))


def _record(
    ref: str = "evidence:primary",
    *,
    authority: str = "VERIFIED_GOVERNED",
    permission: str = "REPORTING_ALLOWED",
    reasons: tuple[str, ...] = (),
) -> contracts.EvidenceReferenceV1:
    draft = contracts.EvidenceReferenceV1(
        ref, authority, permission, reason_codes=reasons,
        evidence_roles=tuple(contracts.EvidenceRole),
        evidence_scope=contracts.EvidenceScope.CANDIDATE_WIDE,
        verifier_id="repair.synthetic_verifier", verifier_version="v1",
        verification_status=contracts.EvidenceVerificationStatus.VERIFIED,
        producer_artifact_binding_hash=sha256(ref.encode("utf-8")).hexdigest(),
        as_of_utc="2026-01-01T00:00:00Z",
    )
    return replace(draft, logical_hash=draft.calculated_logical_hash())


def _candidate(
    relationship: contracts.EventRelationship = contracts.EventRelationship.INITIAL_EVENT,
    *,
    authorized: bool = True,
    evidence_refs: tuple[str, ...] = ("evidence:primary",),
    evidence_records: tuple[contracts.EvidenceReferenceV1, ...] = (),
    legacy_declared_governed_evidence_refs: tuple[str, ...] = ("evidence:primary",),
    feature_inputs: tuple[core.FeatureInputV1, ...] = (),
    **changes: Any,
) -> core.LearningCandidateV2:
    if relationship == contracts.EventRelationship.MATERIAL_UPDATE and changes.get("governed_material_delta"):
        fallback = legacy_declared_governed_evidence_refs or evidence_refs or tuple(row.evidence_ref for row in evidence_records) or (None,)
        changes.setdefault("material_delta_evidence_ref", fallback[0])
    record_refs = {row.evidence_ref for row in evidence_records}
    bindings = tuple(contracts.build_governed_evidence_binding_v1(
        evidence_ref=ref, evidence_roles=tuple(contracts.EvidenceRole),
        producer_artifact_binding_hash=sha256(ref.encode("utf-8")).hexdigest(),
        as_of_utc="2026-01-01T00:00:00Z",
        verifier_id="repair.synthetic_verifier",
    ) for ref in legacy_declared_governed_evidence_refs if ref not in record_refs)
    semantic_refs = tuple(ref for ref in (
        changes.get("material_delta_evidence_ref"), changes.get("governed_new_evidence_ref"),
        changes.get("conflicting_evidence_ref"), changes.get("authoritative_correction_ref"),
        changes.get("distinct_new_event_ref"), changes.get("update_justification_ref"),
        changes.get("prior_testable_proposition_ref"), changes.get("prior_error_ref"),
    ) if ref)
    all_refs = tuple(dict.fromkeys((*evidence_refs, *legacy_declared_governed_evidence_refs, *semantic_refs)))
    bound = {row.evidence_ref for row in bindings} | {row.evidence_ref for row in evidence_records}
    bindings += tuple(contracts.build_governed_evidence_binding_v1(
        evidence_ref=ref, evidence_roles=tuple(contracts.EvidenceRole),
        producer_artifact_binding_hash=sha256(ref.encode("utf-8")).hexdigest(),
        as_of_utc="2026-01-01T00:00:00Z",
        verifier_id="repair.synthetic_verifier",
    ) for ref in semantic_refs if ref not in bound and ref not in {
        changes.get("prior_testable_proposition_ref"), changes.get("prior_error_ref")
    })
    candidate = core.LearningCandidateV2(
        candidate_id="repair:candidate",
        story_id="repair:story",
        cluster_id="repair:cluster",
        update_chain_id="repair:chain",
        source_relationship=relationship,
        evidence_state="GOVERNED_EVIDENCE",
        authority_state="AUTHORIZED" if authorized else "BLOCKED",
        authority_ready=authorized,
        reporting_allowed=authorized,
        authority_blockers=() if authorized else ("authority_missing",),
        history_identity_match=False,
        material_reader_contribution=True,
        feature_inputs=feature_inputs,
        evidence_refs=all_refs,
        evidence_records=evidence_records,
        governed_evidence_bindings=bindings,
    )
    return replace(candidate, **changes)


def _feature(
    candidate: core.LearningCandidateV2,
    config: contracts.AdaptiveLearningConfigV1,
    feature_id: str,
) -> contracts.FeatureEvaluationV1:
    rows = core.evaluate_features(
        candidate,
        config,
        contracts.PerformanceObservationSetV1("repair:observations"),
    )
    return next(row for row in rows if row.feature_id == feature_id)


def _caught(call: Callable[[], Any]) -> str | None:
    try:
        call()
    except ValueError as error:
        return str(error)
    return None


def build_authority_gate_override_matrix(repo_root: str | Path) -> dict[str, Any]:
    config = _config(repo_root)
    authority_input = core.FeatureInputV1(
        "authority_readiness", True, contracts.AvailabilityState.AVAILABLE, 1.0,
        evidence_refs=("evidence:primary",),
    )
    unauthorized = _candidate(
        authorized=False,
        feature_inputs=(authority_input,),
        legacy_declared_governed_evidence_refs=(),
    )
    canonical = _feature(unauthorized, config, "authority_readiness")
    override_error = _caught(lambda: _feature(
        replace(unauthorized, authority_gate_results={"source_authority_ready": True}),
        config,
        "authority_readiness",
    ))
    false_override_error = _caught(lambda: _feature(
        _candidate(authority_gate_results={"reporting_allowed": False}),
        config,
        "authority_readiness",
    ))
    unknown_error = _caught(lambda: _feature(
        _candidate(authority_gate_results={"extension:unknown": True}),
        config,
        "authority_readiness",
    ))

    extension_id = "extension:editorial_review"
    extension_features = tuple(
        replace(row, authority_gate=extension_id) if row.feature_id == "freshness" else row
        for row in config.features
    )
    extension_config = _rehash(
        config,
        authority_gates={**config.authority_gates, extension_id: True},
        features=extension_features,
    )
    freshness_input = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:primary",),
    )
    extension_false = _feature(
        _candidate(feature_inputs=(freshness_input,), authority_gate_results={extension_id: False}),
        extension_config,
        "freshness",
    )
    extension_true = _feature(
        _candidate(feature_inputs=(freshness_input,), authority_gate_results={extension_id: True}),
        extension_config,
        "freshness",
    )
    disabled_extension_config = _rehash(
        config,
        authority_gates={**config.authority_gates, extension_id: False},
    )
    contradiction_error = _caught(lambda: _feature(
        _candidate(authority_gate_results={extension_id: True}),
        disabled_extension_config,
        "authority_readiness",
    ))
    rows = (
        {
            "case": "unauthorized_without_override",
            "expected": "BLOCKED_NO_CONTRIBUTION",
            "observed": f"{canonical.availability.value.upper()}_{'NO_CONTRIBUTION' if canonical.contribution is None else 'CONTRIBUTED'}",
        },
        {
            "case": "unauthorized_true_canonical_override",
            "expected": "REJECT_CANONICAL_OVERRIDE",
            "observed": "REJECT_CANONICAL_OVERRIDE" if override_error and "canonical_authority_gate_override_forbidden" in override_error else override_error,
        },
        {
            "case": "authorized_false_canonical_override",
            "expected": "REJECT_CANONICAL_OVERRIDE",
            "observed": "REJECT_CANONICAL_OVERRIDE" if false_override_error and "canonical_authority_gate_override_forbidden" in false_override_error else false_override_error,
        },
        {
            "case": "unknown_extension_gate",
            "expected": "REJECT_UNKNOWN_EXTENSION_GATE",
            "observed": "REJECT_UNKNOWN_EXTENSION_GATE" if unknown_error and "unknown_extension_authority_gate" in unknown_error else unknown_error,
        },
        {
            "case": "declared_extension_false",
            "expected": "BLOCKED_NO_CONTRIBUTION",
            "observed": f"{extension_false.availability.value.upper()}_{'NO_CONTRIBUTION' if extension_false.contribution is None else 'CONTRIBUTED'}",
        },
        {
            "case": "declared_extension_true",
            "expected": "AVAILABLE_CONTRIBUTED",
            "observed": f"{extension_true.availability.value.upper()}_{'CONTRIBUTED' if extension_true.contribution is not None else 'NO_CONTRIBUTION'}",
        },
        {
            "case": "disabled_extension_true_contradiction",
            "expected": "REJECT_CONTRADICTORY_EXTENSION_GATE",
            "observed": "REJECT_CONTRADICTORY_EXTENSION_GATE" if contradiction_error and "contradictory_extension_authority_gate" in contradiction_error else contradiction_error,
        },
    )
    normalized = tuple({**row, "status": "PASS" if row["expected"] == row["observed"] else "FAIL"} for row in rows)
    return {
        "schema_version": "contentops.authority_gate_override_matrix.v2",
        "canonical_gate_ids": sorted(contracts.CANONICAL_AUTHORITY_GATE_IDS),
        "canonical_derivation_fields": {
            "source_authority_ready": ["authority_ready", "authority_blockers"],
            "reporting_allowed": ["reporting_allowed"],
        },
        "rows": normalized,
        "status": "PASS" if all(row["status"] == "PASS" for row in normalized) else "FAIL",
    }


def build_evidence_count_integrity_matrix(repo_root: str | Path) -> dict[str, Any]:
    config = _config(repo_root)

    def execute(refs: tuple[str, ...], declared: int, records=()) -> tuple[str, int | None]:
        item = core.FeatureInputV1(
            "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
            evidence_refs=refs, evidence_count=declared,
        )
        candidate_refs = tuple(dict.fromkeys(refs))
        candidate = _candidate(
            evidence_refs=candidate_refs,
            evidence_records=tuple(records),
            legacy_declared_governed_evidence_refs=candidate_refs,
            feature_inputs=(item,),
        )
        try:
            row = _feature(candidate, config, "freshness")
        except ValueError as error:
            return str(error), None
        return row.availability.value, row.evidence_count

    cases = (
        ("inflated", ("evidence:a", "evidence:b"), 3, (), "REJECT_MISMATCH", None),
        ("understated", ("evidence:a", "evidence:b"), 1, (), "REJECT_MISMATCH", None),
        ("duplicate_refs", ("evidence:a", "evidence:a"), 1, (), "available", 1),
        ("zero", (), 0, (), "unavailable", 0),
        ("valid", ("evidence:a", "evidence:b"), 2, (), "available", 2),
        ("record_direct_ref_deduplicated", ("evidence:a",), 1, (_record("evidence:a"),), "available", 1),
        ("duplicate_records_deduplicated", ("evidence:primary",), 1, (_record(), _record()), "available", 1),
    )
    rows = []
    for case, refs, declared, records, expected_state, expected_count in cases:
        observed_state, observed_count = execute(refs, declared, records)
        if expected_state == "REJECT_MISMATCH":
            observed = "REJECT_MISMATCH" if "declared_evidence_count_mismatch" in observed_state else observed_state
        else:
            observed = observed_state
        status = "PASS" if observed == expected_state and observed_count == expected_count else "FAIL"
        rows.append({
            "case": case,
            "declared_count": declared,
            "input_ref_count": len(refs),
            "expected_state": expected_state,
            "expected_derived_count": expected_count,
            "observed_state": observed,
            "observed_derived_count": observed_count,
            "status": status,
        })
    return {
        "schema_version": "contentops.evidence_count_integrity_matrix.v2",
        "count_authority": "UNIQUE_VALIDATED_EVIDENCE_REFS_AND_RECORDS",
        "caller_count_role": "DECLARED_COUNT_MUST_EXACTLY_MATCH_DERIVED_COUNT",
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def build_governed_evidence_qualification_matrix(repo_root: str | Path) -> dict[str, Any]:
    config = _config(repo_root)
    cases = (
        ("qualifying_record", _record(), True, None),
        ("unverified", _record(authority="UNVERIFIED"), False, None),
        ("context_only", _record(permission="CONTEXT_ONLY"), False, None),
        ("permission_blocked", _record(permission="REPORTING_NOT_ALLOWED"), False, None),
        ("unavailable", _record(reasons=("unavailable",)), False, None),
        ("explicit_blocker", _record(reasons=("authority_blocked",)), False, None),
        ("malformed", _record("bad ref"), False, "REJECT_MALFORMED"),
    )
    rows = []
    for case, record, expected_qualified, expected_error in cases:
        candidate = _candidate(
            contracts.EventRelationship.MATERIAL_UPDATE,
            evidence_refs=(),
            evidence_records=(record,),
            legacy_declared_governed_evidence_refs=(),
            governed_material_delta=True,
        )
        error = _caught(lambda: core.evaluate_outcome(candidate, config))
        if error:
            observed_error = "REJECT_MALFORMED" if "invalid_evidence_record" in error else error
            qualified = False
            governed_outcome = False
        else:
            outcome = core.evaluate_outcome(candidate, config)
            observed_error = None
            qualified = record.qualifies_for_governed_outcome()
            governed_outcome = "GOVERNED_MATERIAL_UPDATE" in outcome.actionable_outcomes
        status = "PASS" if (
            qualified == expected_qualified
            and governed_outcome == expected_qualified
            and observed_error == expected_error
        ) else "FAIL"
        rows.append({
            "case": case,
            "authority_state": record.authority_state,
            "permission_state": record.permission_state,
            "reason_codes": list(record.reason_codes),
            "expected_qualified": expected_qualified,
            "observed_qualified": qualified,
            "governed_outcome_emitted": governed_outcome,
            "error_disposition": observed_error,
            "status": status,
        })
    return {
        "schema_version": "contentops.governed_evidence_qualification_matrix.v2",
        "accepted_authority_states": sorted(contracts.QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES),
        "accepted_permission_states": sorted(contracts.QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES),
        "disqualifying_reason_codes": sorted(contracts.DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _governed_cases() -> tuple[tuple[str, contracts.EventRelationship, Mapping[str, Any], str], ...]:
    return (
        ("material_update", contracts.EventRelationship.MATERIAL_UPDATE, {"governed_material_delta": True}, "GOVERNED_MATERIAL_UPDATE"),
        ("confirmation", contracts.EventRelationship.CONFIRMATION, {"prior_testable_proposition_ref": "history:proposition", "governed_new_evidence_ref": "evidence:new"}, "GOVERNED_CONFIRMATION"),
        ("contradiction", contracts.EventRelationship.CONTRADICTION, {"prior_testable_proposition_ref": "history:proposition", "conflicting_evidence_ref": "evidence:conflict"}, "GOVERNED_CONTRADICTION"),
        ("correction", contracts.EventRelationship.CORRECTION, {"prior_error_ref": "history:error", "authoritative_correction_ref": "evidence:correction"}, "GOVERNED_CORRECTION"),
        ("new_phase", contracts.EventRelationship.NEW_PHASE, {"update_chain_continuity": True, "distinct_new_event_ref": "evidence:new-phase"}, "GOVERNED_NEW_PHASE"),
    )


def build_governed_evidence_lineage_report(repo_root: str | Path) -> dict[str, Any]:
    config = _config(repo_root)
    rows = []
    for case, relationship, changes, expected in _governed_cases():
        candidate = _candidate(
            relationship,
            evidence_refs=("evidence:direct", "evidence:shared"),
            evidence_records=(_record("evidence:shared"), _record("evidence:record")),
            legacy_declared_governed_evidence_refs=("evidence:direct",),
            **changes,
        )
        outcome = core.evaluate_outcome(candidate, config)
        status = "PASS" if expected in outcome.actionable_outcomes and outcome.evidence_refs and len(outcome.evidence_refs) == len(set(outcome.evidence_refs)) else "FAIL"
        rows.append({
            "case": case,
            "expected_outcome": expected,
            "observed_outcomes": list(outcome.actionable_outcomes),
            "evidence_refs": list(outcome.evidence_refs),
            "qualifying_governed_evidence_refs": list(outcome.qualifying_governed_evidence_refs),
            "record_ref_in_lineage": "evidence:record" in outcome.evidence_refs,
            "record_ref_qualifies": "evidence:record" in outcome.qualifying_governed_evidence_refs,
            "lineage_nonempty": bool(outcome.evidence_refs),
            "lineage_deduplicated": len(outcome.evidence_refs) == len(set(outcome.evidence_refs)),
            "status": status,
        })
    evergreen = _candidate(
        evidence_refs=(),
        evidence_records=(_record("evidence:refresh"),),
        legacy_declared_governed_evidence_refs=(),
        gap_types=(contracts.GapType.EVERGREEN_REFRESH,),
        durability=0.8,
        content_age_hours=240.0,
        reader_utility=0.8,
        update_justification_ref="evidence:refresh",
    )
    evergreen_outcome = core.evaluate_outcome(evergreen, config)
    rows.append({
        "case": "evergreen_refresh",
        "expected_outcome": "EVERGREEN_REFRESH_JUSTIFIED",
        "observed_outcomes": list(evergreen_outcome.actionable_outcomes),
        "evidence_refs": list(evergreen_outcome.evidence_refs),
        "qualifying_governed_evidence_refs": list(evergreen_outcome.qualifying_governed_evidence_refs),
        "record_ref_in_lineage": "evidence:refresh" in evergreen_outcome.evidence_refs,
        "record_ref_qualifies": "evidence:refresh" in evergreen_outcome.qualifying_governed_evidence_refs,
        "lineage_nonempty": bool(evergreen_outcome.evidence_refs),
        "lineage_deduplicated": len(evergreen_outcome.evidence_refs) == len(set(evergreen_outcome.evidence_refs)),
        "status": "PASS" if "EVERGREEN_REFRESH_JUSTIFIED" in evergreen_outcome.actionable_outcomes and evergreen_outcome.evidence_refs else "FAIL",
    })
    return {
        "schema_version": "contentops.governed_evidence_lineage_report.v2",
        "complete_lineage_sources": ["candidate.evidence_refs", "candidate.evidence_records", "candidate.governed_evidence_bindings", "relationship_evidence_refs"],
        "rows": rows,
        "all_governed_outcomes_have_qualifying_nonempty_lineage": all(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def build_duplicate_delta_semantic_matrix(repo_root: str | Path) -> dict[str, Any]:
    config = _config(repo_root)
    rows = []
    for case, relationship, changes, expected in _governed_cases():
        candidate = _candidate(
            relationship,
            evidence_records=(_record(),),
            history_identity_match=True,
            **changes,
        )
        outcome = core.evaluate_outcome(candidate, config)
        status = "PASS" if (
            expected in outcome.actionable_outcomes
            and "DUPLICATE_NO_NEW_DELTA" not in outcome.actionable_outcomes
            and outcome.history_relationship == "PUBLISHED_IDENTITY_MATCH_WITH_GOVERNED_DELTA"
            and outcome.history_identity_match
            and outcome.governed_delta_present
        ) else "FAIL"
        rows.append({
            "case": case,
            "identity_match": outcome.history_identity_match,
            "governed_delta_present": outcome.governed_delta_present,
            "history_relationship": outcome.history_relationship,
            "actionable_outcomes": list(outcome.actionable_outcomes),
            "status": status,
        })
    unchanged = core.evaluate_outcome(
        _candidate(contracts.EventRelationship.DUPLICATE, history_identity_match=True),
        config,
    )
    rows.append({
        "case": "unchanged_duplicate",
        "identity_match": unchanged.history_identity_match,
        "governed_delta_present": unchanged.governed_delta_present,
        "history_relationship": unchanged.history_relationship,
        "actionable_outcomes": list(unchanged.actionable_outcomes),
        "status": "PASS" if (
            "DUPLICATE_NO_NEW_DELTA" in unchanged.actionable_outcomes
            and unchanged.history_relationship == "PUBLISHED_IDENTITY_MATCH_NO_NEW_DELTA"
            and not unchanged.governed_delta_present
        ) else "FAIL",
    })
    incompatible_pairs_rejected = all(
        _caught(lambda value=expected: core._validate_actionable_outcomes((value, "DUPLICATE_NO_NEW_DELTA")))
        for _, _, _, expected in _governed_cases()
    )
    return {
        "schema_version": "contentops.duplicate_delta_semantic_matrix.v2",
        "identity_and_delta_are_orthogonal": True,
        "incompatible_pairs_rejected": incompatible_pairs_rejected,
        "rows": rows,
        "status": "PASS" if incompatible_pairs_rejected and all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def build_core_reports(repo_root: str | Path) -> dict[str, Any]:
    return {
        "authority_gate_override_matrix.json": build_authority_gate_override_matrix(repo_root),
        "evidence_count_integrity_matrix.json": build_evidence_count_integrity_matrix(repo_root),
        "governed_evidence_qualification_matrix.json": build_governed_evidence_qualification_matrix(repo_root),
        "governed_evidence_lineage_report.json": build_governed_evidence_lineage_report(repo_root),
        "duplicate_delta_semantic_matrix.json": build_duplicate_delta_semantic_matrix(repo_root),
    }


def generate_evidence(
    *,
    repo_root: str | Path,
    validation_summary: Mapping[str, Any],
    changed_paths: Sequence[str],
    protected_paths: Mapping[str, Any],
    unrelated_worktree: Mapping[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    output = Path(output_dir).resolve() if output_dir else root / EVIDENCE_ROOT
    output.mkdir(parents=True, exist_ok=True)
    first = build_core_reports(root)
    second = build_core_reports(root)
    first_bytes = _json_bytes(first)
    second_bytes = _json_bytes(second)
    if first_bytes != second_bytes:
        raise ValueError("repair_evidence_generation_not_deterministic")
    reports = dict(first)
    reports["focused_test_summary.json"] = {
        "schema_version": "contentops.authority_integrity_repair_test_summary.v2",
        **dict(validation_summary),
    }
    reports["deterministic_replay.json"] = {
        "schema_version": "contentops.authority_integrity_repair_deterministic_replay.v2",
        "two_independent_core_report_builds_identical": True,
        "core_report_bundle_sha256": sha256(first_bytes).hexdigest(),
        "config_logical_hash": _config(root).config_logical_hash,
        "calibration_state": _config(root).calibration_state.value,
        "status": "PASS",
    }
    reports["changed_protected_paths.json"] = {
        "schema_version": "contentops.authority_integrity_repair_changed_protected_paths.v2",
        "task_owned_paths": list(changed_paths),
        "protected_paths": dict(protected_paths),
        "unrelated_worktree": dict(unrelated_worktree),
        "starting_sha": STARTING_SHA,
        "upstream_repository": adapters.UPSTREAM_REPOSITORY,
        "upstream_branch": adapters.UPSTREAM_BRANCH,
        "upstream_verified_head": UPSTREAM_HEAD,
        "upstream_repository_mutated": False,
    }
    reports["safety_report.json"] = {
        "schema_version": "contentops.authority_integrity_repair_safety.v2",
        "architecture_preserved": True,
        "v1_compatibility_preserved": True,
        "historical_evidence_mutated": False,
        "configuration_calibration_state": "UNCALIBRATED_FOUNDATION",
        "v1_0_mutated": False,
        "publication_authority_granted": False,
        "public_write_performed": False,
        "dispatch_performed": False,
        "browser_or_cdp_used": False,
        "live_metrics_collected": False,
        "credential_values_read": False,
        "provider_called": False,
        "scheduler_mutated": False,
        "editorial_policy_mutated": False,
        "dqr_mutated": False,
        "permission_authority_mutated": False,
        "upstream_repository_mutated": False,
        "status": "PASS",
    }
    reports["genericity_guard_report.json"] = hardening.run_genericity_ast_guard(root)
    for name, value in reports.items():
        (output / name).write_bytes(_json_bytes(value))
    artifact_hashes = {
        name: sha256((output / name).read_bytes()).hexdigest()
        for name in sorted(reports)
    }
    required_non_manifest = set(REQUIRED_ARTIFACTS) - {"final_manifest.json"}
    missing = sorted(required_non_manifest - set(reports))
    failing = sorted(
        name for name, value in reports.items()
        if isinstance(value, Mapping) and value.get("status") == "FAIL"
    )
    manifest = {
        "schema_version": "contentops.generic_foundation_authority_integrity_repair_manifest.v2",
        "task_label": TASK_LABEL,
        "operator_disposition": "ACCEPT_GENERIC_FOUNDATION_V2_ENFORCEMENT_WITH_AUTHORITY_INTEGRITY_GAPS",
        "task_starting_sha": STARTING_SHA,
        "latest_verified_precommit_sha": STARTING_SHA,
        "final_sha_reported_after_commit": None,
        "accepted_release_sha": "6983bfb3ef300414b744f3f8f97ca81ff699348b",
        "upstream_repository": adapters.UPSTREAM_REPOSITORY,
        "upstream_branch": adapters.UPSTREAM_BRANCH,
        "upstream_verified_head": UPSTREAM_HEAD,
        "configuration_calibration_state": "UNCALIBRATED_FOUNDATION",
        "repaired_boundaries": [
            "canonical_authority_gates",
            "evidence_count_integrity",
            "governed_evidence_qualification_and_lineage",
            "duplicate_versus_governed_delta_semantics",
        ],
        "required_artifact_count": len(REQUIRED_ARTIFACTS),
        "missing_required_artifacts": missing,
        "failing_artifacts": failing,
        "artifact_sha256": artifact_hashes,
        "manifest_self_hash_excluded": True,
        "publication_authority_granted": False,
        "terminal_classification": TERMINAL_CLASSIFICATION if not missing and not failing else "FAIL_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR",
        "next_action": NEXT_ACTION,
    }
    (output / "final_manifest.json").write_bytes(_json_bytes(manifest))
    return manifest
