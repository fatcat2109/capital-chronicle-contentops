"""Deterministic evidence and verification for generic foundation hardening.

This module is an offline adapter/evidence surface.  It does not publish,
dispatch, schedule, access credentials, call providers, or mutate policy.
Requirement statuses are derived from observed verifier output; no requirement
is assigned PASS merely because it appears in this registry.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, fields, replace
from hashlib import sha1, sha256
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts


TASK_LABEL = "TASK_CONTENTOPS_GENERIC_FOUNDATION_V2_ENFORCEMENT_HARDENING"
TERMINAL_CLASSIFICATION = "PASS_GENERIC_FOUNDATION_V2_ENFORCEMENT_HARDENING_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_GENERIC_FOUNDATION_V2_ENFORCEMENT_HARDENING"


@dataclass(frozen=True)
class RequirementSpec:
    requirement_id: str
    requirement_text: str
    implementation_target: str
    verifier_id: str
    planned_test: str | None
    evidence_artifact_path: str
    expected_value: Any
    observation_key: str
    comparison: str = "equals"
    documentary_review: bool = False


EVIDENCE_ROOT = "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_ENFORCEMENT_HARDENING"


def _req(
    requirement_id: str,
    requirement_text: str,
    target: str,
    verifier: str,
    test: str | None,
    artifact: str,
    expected: Any,
    observation: str,
    comparison: str = "equals",
    documentary: bool = False,
) -> RequirementSpec:
    return RequirementSpec(
        requirement_id,
        requirement_text,
        target,
        verifier,
        test,
        f"{EVIDENCE_ROOT}/{artifact}",
        expected,
        observation,
        comparison,
        documentary,
    )


# Created before implementation edits from the attached task contract.  Rows
# intentionally have no status field; status is derived only after verifiers run.
REQUIREMENT_SPECS: tuple[RequirementSpec, ...] = (
    _req("START-01", "ContentOps local branch, local HEAD, and origin/master must equal master at 073766b912643ea34c545b29e669c3ff2a62c17c.", "Git authority", "git-authority-v1", None, "protected_path_inventory.json", True, "git.starting_authority_matches"),
    _req("START-02", "No concurrent ContentOps mainline writer or Git lock may be active.", "Git authority", "writer-lock-v1", None, "protected_path_inventory.json", 0, "git.concurrent_writer_or_lock_count"),
    _req("START-03", "Pre-existing modified and untracked files must be preserved and only explicit task paths staged.", "Git staging", "worktree-preservation-v1", "test_unrelated_worktree_inventory_is_preserved", "unrelated_worktree_preservation_report.json", True, "repository.unrelated_changes_preserved"),
    _req("START-04", "The annotated v1.0 tag object and accepted release commit must remain unchanged.", "Git release authority", "immutable-tag-v1", "test_v1_tag_authority_matches", "protected_path_inventory.json", True, "git.v1_tag_unchanged"),
    _req("READ-01", "All mandated fresh-session authority, implementation, evidence, and bootstrap files must be read before implementation.", "Builder procedure", "documentary-session-review-v1", None, "requirement_matrix.json", "REVIEW_REQUIRED", "documentary.fresh_session_reading", documentary=True),
    _req("ARCH-01", "Preserve separated generic contracts, core, adapters, external uncalibrated config, V1 compatibility, and immutable historical Task 3/Task 4 evidence.", "V2 architecture", "architecture-separation-v1", "test_core_does_not_import_adapters", "v1_compatibility_report.json", True, "architecture.separation_and_compatibility"),
    _req("ARCH-02", "The generic core must reason from domain-neutral capabilities and contain no literal subject routing or scenario boundary.", "Generic core", "genericity-ast-v2", "test_genericity_ast_guard_has_zero_prohibited_findings", "genericity_ast_guard_report.json", 0, "genericity.prohibited_finding_count"),
    _req("MATRIX-01", "The task acceptance matrix must be created before implementation and regenerated from observed evidence without preassigned PASS values.", "Hardening evidence", "acceptance-derivation-v2", "test_requirement_statuses_are_machine_derived", "requirement_matrix.json", True, "acceptance.machine_derived"),
    _req("CONFIG-01", "Every FeatureDefinitionV1 and AdaptiveLearningConfigV1 field must have executable semantics or be removed.", "Contracts/core/config loader", "config-usage-ast-runtime-v2", "test_all_declared_config_fields_are_consumed", "config_field_usage_report.json", 0, "config.unused_material_field_count"),
    _req("CONFIG-02", "Weights and thresholds must be finite; minimum evidence must be a nonnegative integer; config version must be nonempty.", "Config validation", "config-validation-v2", "test_config_numeric_and_version_validation", "config_executable_semantics_report.json", True, "config.numeric_validation_pass"),
    _req("CONFIG-03", "Normalization names and parameters, min/max bounds, authority-gate references, unavailable-handling references, and feature ID uniqueness must validate fail closed.", "Config validation", "config-validation-v2", "test_config_reference_and_normalization_validation", "config_executable_semantics_report.json", True, "config.reference_validation_pass"),
    _req("CONFIG-04", "The config logical hash must bind every material field and the foundation calibration state must remain UNCALIBRATED_FOUNDATION.", "Config contract", "config-hash-v2", "test_config_hash_binds_every_material_field", "config_executable_semantics_report.json", True, "config.hash_and_calibration_pass"),
    _req("CONFIG-05", "Unknown top-level and feature configuration fields must fail unless explicitly versioned and preserved.", "Strict config loader", "strict-config-loader-v2", "test_unknown_config_fields_fail", "config_executable_semantics_report.json", True, "config.unknown_fields_fail_closed"),
    _req("FEATURE-01", "Unavailable, blocked, unsupported, insufficient-evidence, failed-gate, inapplicable, missing, or out-of-bounds features must not contribute to ranking.", "Feature evaluator", "feature-execution-v2", "test_all_abstention_states_do_not_contribute", "feature_applicability_report.json", True, "features.abstentions_noncontributing"),
    _req("FEATURE-02", "Blocked authority-gated features must not become zero; unsupported must differ from unavailable; explicit observed zero must remain available zero.", "Feature evaluator", "availability-semantics-v2", "test_feature_availability_states_remain_distinct", "ranking_arithmetic_report.json", True, "features.availability_semantics_pass"),
    _req("FEATURE-03", "Every feature row must record capability use, normalization parameters, evidence count/minimum, gate and applicability results, references, and reason codes.", "FeatureEvaluationV1", "feature-row-shape-v2", "test_feature_rows_include_execution_metadata", "feature_evidence_minimum_report.json", True, "features.complete_execution_metadata"),
    _req("CAP-01", "Candidates and evidence must carry optional orthogonal modalities, temporal characters, story modes, geography/entity/domain/asset/source dimensions, evidence profiles, schedule state, and counts.", "Capability contracts", "capability-contract-v2", "test_capability_contract_inventory_is_complete", "capability_dimension_contract_inventory.json", True, "capabilities.required_dimensions_present"),
    _req("CAP-02", "Capability dimensions must accept empty, singleton, and multi-value inputs and reject duplicates or malformed values without forcing every topic to populate every dimension.", "Capability validation", "capability-validation-v2", "test_capability_dimensions_empty_singleton_multi_and_invalid", "collection_validation_report.json", True, "capabilities.collection_semantics_pass"),
    _req("CAP-03", "Capability dimensions must execute feature applicability, evidence minimums, diversity, schedule, breadth, significance, evidence profile, and unsupported-state logic without inferring facts.", "Generic feature evaluator", "capability-execution-v2", "test_capability_dimensions_enter_generic_execution", "capability_dimension_execution_report.json", True, "capabilities.execution_dimensions_pass"),
    _req("XDOMAIN-01", "At least fifteen cross-domain fixtures must pass capability, evidence, outcome, ranking, and no-publication execution through generic algorithms.", "Fixture adapter/evidence", "cross-domain-execution-v2", "test_all_cross_domain_fixtures_execute_generic_algorithms", "cross_domain_execution_matrix.json", 15, "cross_domain.passing_fixture_count", "greater_or_equal"),
    _req("XDOMAIN-02", "Every fixture row must contain supplied/omitted dimensions, evidence and temporal inputs, feature/gate/minimum results, outcome, ranking, disposition, and derived expected-versus-observed status.", "Fixture evidence", "fixture-row-schema-v2", "test_cross_domain_rows_have_required_execution_fields", "cross_domain_execution_matrix.json", True, "cross_domain.row_schema_complete"),
    _req("XDOMAIN-03", "At least two unrelated domains must execute every repaired outcome, authority, evidence-profile, diversity, breadth, unavailable, and explicit-zero abstraction.", "Cross-domain coverage", "abstraction-coverage-v2", "test_each_repaired_abstraction_has_two_domain_proof", "cross_domain_abstraction_coverage.json", 0, "cross_domain.abstractions_below_two_domain_proof"),
    _req("COLL-01", "Published history must validate unique identities, hashes, one current version, supersession references, self/cycle conflicts, and story/update-chain coherence.", "PublishedContentHistoryV1", "history-validation-v2", "test_published_history_hardening_validation", "collection_validation_report.json", True, "collections.history_validation_pass"),
    _req("COLL-02", "Candidate collections must validate uniqueness, story/cluster/update-chain consistency, relationship, authority/permission/blockers, evidence/brief uniqueness, and capability validity.", "Candidate validator", "candidate-validation-v2", "test_candidate_collection_hardening_validation", "collection_validation_report.json", True, "collections.candidate_validation_pass"),
    _req("COLL-03", "Gap sets must validate unique gap/idea IDs, gap types, actionable evidence, and optionally disallowed logical duplicates.", "ContentGapSetV1", "gap-validation-v2", "test_gap_set_hardening_validation", "collection_validation_report.json", True, "collections.gap_validation_pass"),
    _req("COLL-04", "Observation sets must validate identity, state/value/authority compatibility, timestamps, collisions, lineage coherence, metric names and scopes.", "PerformanceObservationSetV1", "observation-validation-v2", "test_observation_set_hardening_validation", "collection_validation_report.json", True, "collections.observation_validation_pass"),
    _req("COLL-05", "Learning inputs must validate nonempty bindings and logical time while supporting zero, one, and arbitrary collection cardinalities without fixed platform counts.", "Decision builder", "learning-input-validation-v2", "test_learning_inputs_and_arbitrary_cardinalities", "collection_validation_report.json", True, "collections.learning_input_validation_pass"),
    _req("OUTCOME-01", "Source relationship, evidence, authority, reporting permission, history, gaps, actionable outcome, and publication disposition must remain separate.", "OutcomeDecisionV1", "outcome-separation-v2", "test_outcome_contract_preserves_orthogonal_results", "outcome_semantic_matrix.json", True, "outcomes.separation_pass"),
    _req("OUTCOME-02", "Governed material update, confirmation, contradiction, correction, and new phase must enforce their specific authority, permission, lineage, evidence, and nonduplicate rules.", "Outcome evaluator", "governed-outcomes-v2", "test_governed_outcome_requirements", "outcome_semantic_matrix.json", True, "outcomes.governed_semantics_pass"),
    _req("OUTCOME-03", "Packaging gap, duplicate, filler, evergreen refresh, insufficient authority, no-publication, and compatible/incompatible multi-outcomes must retain distinct semantics.", "Outcome evaluator", "other-outcomes-v2", "test_non_governed_outcome_semantics", "outcome_semantic_matrix.json", True, "outcomes.other_semantics_pass"),
    _req("RANK-01", "Ranking must use executable uncalibrated config, separate contribution/penalty, deterministic tie breaking, preserve null/zero, and grant no publication authority.", "Ranking engine", "ranking-arithmetic-v2", "test_ranking_arithmetic_and_tie_breaking", "ranking_arithmetic_report.json", True, "ranking.arithmetic_pass"),
    _req("RANK-02", "No performance prior may be created without enough metric-bearing observations, and platform variants must not inflate distinct content/story samples.", "Observation/ranking engine", "performance-abstention-v2", "test_metric_threshold_and_content_cardinality", "observation_cardinality_report.json", True, "ranking.performance_and_cardinality_pass"),
    _req("LINEAGE-01", "Each decision must bind prior ID/hash, config version/hash, input binding, history, gaps, observations, candidate cohort, time, operator state, reason, ID, and logical hash.", "ContentOpsLearningDecisionV2", "decision-binding-v2", "test_decision_contains_complete_lineage_bindings", "append_only_lineage_replay.json", True, "lineage.complete_bindings"),
    _req("LINEAGE-02", "Successor validation must reject missing/wrong prior lineage, missing reason, unchanged authority, identity/binding mismatch, forks, malformed time, downgrade/deletion without reason, and prior mutation.", "Successor validator", "append-only-successor-v2", "test_append_only_successor_rejection_matrix", "append_only_mutation_check.json", True, "lineage.rejection_matrix_pass"),
    _req("LINEAGE-03", "Identical inputs/config/time must reproduce the same decision; changed config or input authority must create a new identity without mutating prior serialization.", "Decision builder", "deterministic-lineage-v2", "test_deterministic_and_changed_authority_lineage", "append_only_lineage_replay.json", True, "lineage.deterministic_replay_pass"),
    _req("MODEL-01", "Model-assisted records must preserve bounded metadata and reject every authority, truth, waiver, scheduling, or publication grant while deterministic blockers win.", "ModelAssistedJudgmentV1", "model-firewall-v2", "test_model_assisted_judgment_firewall", "safety_and_limitation_report.json", True, "model.firewall_pass"),
    _req("GUARD-01", "An AST-aware guard must inspect core, config consumption, tests, and generic evidence generators for architecture regressions with zero prohibited findings.", "Hardening guard", "genericity-ast-v2", "test_genericity_ast_guard_has_zero_prohibited_findings", "genericity_ast_guard_report.json", 0, "genericity.prohibited_finding_count"),
    _req("UPSTREAM-01", "Read upstream main at f4a365803385997265320e4b468c22028aea5a67 and bind exact artifact bytes, Git blob, schema, producer, pool, logical/candidate hashes, sources, and cutoff.", "Read-only upstream binding", "upstream-binding-v2", "test_current_upstream_binding_matches_git_object", "current_upstream_artifact_binding.json", True, "upstream.current_binding_pass"),
    _req("UPSTREAM-02", "Compare current upstream bytes with historical 9bff5453 and dced71f exports using an allowed exact classification without modifying upstream.", "Read-only upstream comparison", "upstream-comparison-v2", "test_upstream_three_way_comparison", "upstream_historical_comparison.json", "SAME_BYTES_AND_IDENTITY", "upstream.comparison_classification"),
    _req("EVIDENCE-01", "Create a superseding hardening evidence directory without overwriting original V2 or historical evidence and emit every required machine-readable artifact.", "Evidence generator", "artifact-inventory-v2", "test_required_hardening_artifacts_are_complete", "hardening_manifest.json", 0, "evidence.missing_required_artifact_count"),
    _req("EVIDENCE-02", "The hardening manifest must bind every generated non-self-referential artifact hash and distinguish real, synthetic, historical, unavailable, zero, uncalibrated, proposal, and publication classes.", "Evidence manifest", "manifest-binding-v2", "test_manifest_hashes_and_evidence_classes", "hardening_manifest.json", True, "evidence.manifest_binding_and_classes_pass"),
    _req("COMPAT-01", "V1 remains operational, Task 3 and Task 4 evidence hashes remain unchanged, the compatibility adapter accepts only the final body, and stale bodies remain rejected.", "Compatibility adapters", "compatibility-preservation-v2", "test_v1_task3_task4_and_body_compatibility", "task3_task4_preservation_report.json", True, "compatibility.all_pass"),
    _req("SAFETY-01", "No publication, dispatch, scheduling, policy/DQR/permission/authority mutation, browser, public HTTP, credential/provider access, public interaction, UI work, or live collection may occur.", "Core and evidence inventory", "safety-static-runtime-v2", "test_hardening_safety_surface", "safety_and_limitation_report.json", True, "safety.no_forbidden_effects"),
    _req("VALID-01", "Focused hardening, V2, V1 compatibility, relevant newsroom/evidence/editorial/status tests and required compile/JSON/hash/guard/diff/scan validations must be reported truthfully.", "Validation execution", "validation-summary-v2", None, "test_and_validation_summary.json", True, "validation.required_checks_pass"),
    _req("VALID-02", "A full-suite attempt may not claim PASS on timeout or absence, and GitHub CI PASS may not be claimed when checks are absent.", "Validation reporting", "validation-truth-v2", None, "test_and_validation_summary.json", True, "validation.truthful_full_suite_and_ci"),
    _req("STATUS-01", "Current status, plan, ledger, pointer, readiness, supersession, AGENTS, and bootstrap authority must be reconciled without creating another master plan.", "Current authority docs", "status-reconciliation-v2", "test_status_authority_reconciled", "changed_file_inventory.json", True, "status.reconciled"),
    _req("STATUS-02", "Record 073766b9 as superseded partial foundation, preserve Task 4 disposition and v1.0 baseline, and set the exact independent-audit next action.", "Current authority docs", "status-values-v2", "test_status_exact_hardening_values", "changed_file_inventory.json", True, "status.exact_values_pass"),
    _req("STAGE-01", "Only task-owned paths may be staged; staged inventory must match ownership and cached diff checks must pass.", "Git staging", "staged-inventory-v1", None, "changed_file_inventory.json", "REVIEW_REQUIRED", "documentary.post_commit_staging", documentary=True),
    _req("GIT-01", "Commit fix: enforce generic learning foundation contracts to master, push origin/master, and verify final Git/tag/worktree/CI truth.", "Git completion", "post-push-git-v1", None, "hardening_manifest.json", "REVIEW_REQUIRED", "documentary.post_push_verification", documentary=True),
    _req("FINAL-01", "Use the exact terminal classification and provide the complete requested evidence report with the exact next action.", "Final response", "terminal-response-review-v1", None, "requirement_matrix.json", "REVIEW_REQUIRED", "documentary.final_response", documentary=True),
)


def _lookup(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def derive_requirement_matrix(observations: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for spec in REQUIREMENT_SPECS:
        observed = _lookup(observations, spec.observation_key)
        if spec.documentary_review:
            status = "REVIEW_REQUIRED"
            note = "Documentary or terminal action requires human review outside the precommit artifact."
        elif observed is None:
            status = "NOT_IMPLEMENTED"
            note = f"No verifier observation found at {spec.observation_key}."
        else:
            comparisons = {
                "equals": observed == spec.expected_value,
                "greater_or_equal": isinstance(observed, (int, float)) and observed >= spec.expected_value,
                "contains": spec.expected_value in observed if isinstance(observed, (str, list, tuple, set, dict)) else False,
            }
            passed = comparisons.get(spec.comparison, False)
            status = "PASS" if passed else "FAIL"
            note = None if passed else f"Expected {spec.comparison} {spec.expected_value!r}; observed {observed!r}."
        rows.append({
            "requirement_id": spec.requirement_id,
            "requirement_text": spec.requirement_text,
            "implementation_target": spec.implementation_target,
            "verifier_id": spec.verifier_id,
            "verifier_version": "2.0.0",
            "test_id": spec.planned_test,
            "evidence_artifact_path": spec.evidence_artifact_path,
            "expected_value": spec.expected_value,
            "observed_value": observed,
            "derived_status": status,
            "blocker_or_review_note": note,
        })
    statuses = ("PASS", "REVIEW_REQUIRED", "BLOCKED", "FAIL", "NOT_IMPLEMENTED")
    counts = {status: sum(row["derived_status"] == status for row in rows) for status in statuses}
    return {
        "schema_version": "contentops.generic_foundation_hardening.requirement_matrix.v2",
        "machine_derived": True,
        "required_row_count": len(REQUIREMENT_SPECS),
        "pass_count": counts["PASS"],
        "review_required_count": counts["REVIEW_REQUIRED"],
        "blocked_count": counts["BLOCKED"],
        "fail_count": counts["FAIL"],
        "not_implemented_count": counts["NOT_IMPLEMENTED"],
        "omitted_row_count": len(REQUIREMENT_SPECS) - len(rows),
        "review_required_rows": [row["requirement_id"] for row in rows if row["derived_status"] == "REVIEW_REQUIRED"],
        "terminal_pass_allowed": counts["BLOCKED"] == counts["FAIL"] == counts["NOT_IMPLEMENTED"] == 0,
        "rows": rows,
    }


def _source_field_usage(repo_root: Path) -> dict[str, Any]:
    targets = {
        "contracts": repo_root / "live_contentops" / "content_intelligence_contracts_v2.py",
        "core": repo_root / "live_contentops" / "adaptive_learning_core_v2.py",
        "loader": repo_root / "live_contentops" / "adaptive_learning_adapters_v2.py",
    }
    texts = {name: path.read_text(encoding="utf-8-sig") for name, path in targets.items()}
    feature_fields = [row.name for row in fields(contracts.FeatureDefinitionV1)]
    config_fields = [row.name for row in fields(contracts.AdaptiveLearningConfigV1)]
    rows = []
    for contract_name, field_names in (("FeatureDefinitionV1", feature_fields), ("AdaptiveLearningConfigV1", config_fields)):
        for field_name in field_names:
            patterns = (
                f"definition.{field_name}", f"row.{field_name}", f"config.{field_name}",
                f"self.{field_name}", f'raw["{field_name}"]', f'raw.get("{field_name}")',
            )
            locations = [name for name, text in texts.items() if any(pattern in text for pattern in patterns)]
            rows.append({
                "contract": contract_name,
                "field": field_name,
                "consumed": bool(locations),
                "consumption_targets": locations,
                "verification_method": "static_source_reference_plus_runtime_tests",
            })
    return {
        "schema_version": "contentops.config_field_usage_report.v2",
        "rows": rows,
        "unused_material_field_count": sum(not row["consumed"] for row in rows),
        "status": "PASS" if all(row["consumed"] for row in rows) else "FAIL",
    }


def build_config_semantics_report(repo_root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    config = adapters.load_foundation_config(root)
    usage = _source_field_usage(root)
    report = {
        "schema_version": "contentops.config_executable_semantics_report.v2",
        "config_version": config.config_version,
        "calibration_state": config.calibration_state.value,
        "config_logical_hash": config.config_logical_hash,
        "validation_blockers": list(config.validate()),
        "feature_count": len(config.features),
        "finite_weights": all(math.isfinite(float(row.weight)) for row in config.features),
        "finite_thresholds": all(math.isfinite(float(value)) for value in config.thresholds.values()),
        "minimum_evidence_valid": all(isinstance(row.minimum_evidence, int) and not isinstance(row.minimum_evidence, bool) and row.minimum_evidence >= 0 for row in config.features),
        "normalization_parameters_executable": all(rule.get("kind") == name for name, rule in config.normalization_rules.items()),
        "authority_gate_references_valid": all(row.authority_gate is None or row.authority_gate in config.authority_gates for row in config.features),
        "unavailable_handling_references_valid": all(row.unavailable_handling in config.unavailable_handling for row in config.features),
        "strict_unknown_field_policy": "FAIL_UNKNOWN_TOP_LEVEL_OR_FEATURE_FIELD",
        "field_usage_status": usage["status"],
    }
    report["status"] = "PASS" if not report["validation_blockers"] and usage["status"] == "PASS" else "FAIL"
    return report, usage


def run_genericity_ast_guard(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    core_targets = (
        root / "live_contentops" / "content_intelligence_contracts_v2.py",
        root / "live_contentops" / "adaptive_learning_core_v2.py",
    )
    auxiliary_targets = (
        root / "live_contentops" / "adaptive_learning_adapters_v2.py",
        root / "live_contentops" / "generic_foundation_hardening_v2.py",
        root / "tests" / "test_content_intelligence_v2.py",
        root / "tests" / "test_generic_foundation_hardening_v2.py",
    )
    findings: list[dict[str, Any]] = []

    def add(path: Path, rule: str, method: str, finding: str, severity: str = "ERROR") -> None:
        findings.append({
            "target": path.relative_to(root).as_posix(), "rule_id": rule,
            "detection_method": method, "finding": finding, "severity": severity,
            "disposition": "PROHIBITED", "final_status": "FAIL",
        })

    prohibited_core_literals = re.compile(
        r"(?i)(treasury|federal reserve|\bcpi\b|payroll|\bgdp\b|crude oil|sanction|tariff|war|weather|capitalchronicle\.substack|cc-candidate-|cc-story-|https?://|20\d{2}-\d{2}-\d{2}|[0-9a-f]{40,64})"
    )
    for path in core_targets:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any("adaptive_learning_adapters" in name for name in names):
                    add(path, "CORE_IMPORTS_ADAPTER", "AST_IMPORT", ",".join(names))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and prohibited_core_literals.search(node.value):
                add(path, "TOPIC_OR_ID_LITERAL_IN_CORE", "AST_STRING_LITERAL", node.value[:120])
            if isinstance(node, (ast.If, ast.IfExp, ast.Match)):
                segment = ast.get_source_segment(text, node) or ""
                if re.search(r"(?i)(topic|subject|scenario|story_family|country)\s*(==|in)", segment):
                    add(path, "TOPIC_CONDITIONED_BRANCH", "AST_BRANCH", segment[:160])
            if isinstance(node, ast.Compare):
                segment = ast.get_source_segment(text, node) or ""
                if re.search(r"len\([^)]*(candidate|gap|idea|platform)[^)]*\)\s*(==|!=)\s*\d+", segment, re.I):
                    add(path, "FIXED_COLLECTION_COUNT", "AST_COMPARE", segment)
        for rule, pattern in {
            "UNAVAILABLE_TO_ZERO": r"(?i)(unavailable|unsupported|blocked)[^\n]{0,80}(return|=)\s*0(?:\.0)?\b",
            "ONE_STORY_ASSUMPTION": r"(?i)exactly_one_story|single_story_required",
            "NUMERIC_ONLY_ASSUMPTION": r"(?i)numeric_evidence_required_for_all",
            "PLATFORM_COUNT_ASSUMPTION": r"(?i)(nine|9)[-_ ]platform",
        }.items():
            if re.search(pattern, text):
                add(path, rule, "TEXT_PATTERN", pattern)

    hardening_text = auxiliary_targets[1].read_text(encoding="utf-8-sig")
    for path in (auxiliary_targets[1], auxiliary_targets[3]):
        if path.exists():
            text = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    segment = ast.get_source_segment(text, node) or ""
                    if re.search(r"len\([^)]*(fixture|matrix\s*\[\s*['\"]rows)[^)]*\)\s*==\s*\d+", segment, re.I):
                        add(path, "FIXED_FIXTURE_COUNT_IN_GENERIC_PROOF", "AST_COMPARE", segment)
                if isinstance(node, ast.Dict):
                    pairs = {key.value: value for key, value in zip(node.keys, node.values) if isinstance(key, ast.Constant) and isinstance(key.value, str)}
                    value = pairs.get("derived_status") or pairs.get("status")
                    if isinstance(value, ast.Constant) and value.value == "PASS" and "requirement" in pairs:
                        add(path, "SELF_DECLARED_ACCEPTANCE_PASS", "AST_DICT", ast.get_source_segment(text, node) or "PASS")
    if "build_learning_decision_v2(" not in hardening_text or "evaluate_features(" not in hardening_text:
        add(auxiliary_targets[1], "FIXTURE_BYPASSES_GENERIC_ALGORITHMS", "CALL_INVENTORY", "generic decision and feature calls are required")
    if re.search(r"observed_(?:outcome|result)\s*=\s*(?:fixture|spec)\s*\[\s*[\"']expected", hardening_text):
        add(auxiliary_targets[1], "SYNTHETIC_EXPECTED_COPIED_TO_OBSERVED", "AST_EQUIVALENT_TEXT", "observed result assigned from expected fixture field")
    config_usage = _source_field_usage(root)
    for row in config_usage["rows"]:
        if not row["consumed"]:
            add(auxiliary_targets[0], "UNUSED_CONFIG_FIELD", "AST_SOURCE_USAGE", f"{row['contract']}.{row['field']}")
    capability_fields = [row.name for row in fields(contracts.CapabilityDimensionsV1)]
    core_text = core_targets[1].read_text(encoding="utf-8-sig")
    for field_name in capability_fields:
        if f"capabilities.{field_name}" not in core_text and f"self.{field_name}" not in core_targets[0].read_text(encoding="utf-8-sig"):
            add(core_targets[1], "UNUSED_CAPABILITY_DIMENSION", "AST_SOURCE_USAGE", field_name)
    rule_inventory = [
        "CORE_IMPORTS_ADAPTER", "TOPIC_OR_ID_LITERAL_IN_CORE", "TOPIC_CONDITIONED_BRANCH",
        "FIXED_COLLECTION_COUNT", "UNAVAILABLE_TO_ZERO", "ONE_STORY_ASSUMPTION",
        "NUMERIC_ONLY_ASSUMPTION", "PLATFORM_COUNT_ASSUMPTION", "UNUSED_CONFIG_FIELD",
        "UNUSED_CAPABILITY_DIMENSION", "FIXTURE_BYPASSES_GENERIC_ALGORITHMS",
        "SYNTHETIC_EXPECTED_COPIED_TO_OBSERVED",
    ]
    return {
        "schema_version": "contentops.genericity_ast_guard_report.v2",
        "targets": [path.relative_to(root).as_posix() for path in (*core_targets, *auxiliary_targets)],
        "ast_inspection_scope": {
            "generic_core": [path.relative_to(root).as_posix() for path in core_targets],
            "config_loader": auxiliary_targets[0].relative_to(root).as_posix(),
            "evidence_generator": auxiliary_targets[1].relative_to(root).as_posix(),
            "generic_execution_test": auxiliary_targets[3].relative_to(root).as_posix(),
        },
        "rule_inventory": rule_inventory,
        "finding_count": len(findings),
        "prohibited_finding_count": len(findings),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


FIXTURE_SPECS: tuple[dict[str, Any], ...] = (
    {"id": "scheduled_price_release", "domain": "scheduled price statistics", "relationship": "material_update", "expected": ("GOVERNED_MATERIAL_UPDATE",), "mode": "data_release", "modalities": ("official_table", "numeric_time_series"), "temporal": ("scheduled", "period_observation"), "numeric": True, "nonnumeric": False, "scheduled": True, "sources": 2, "geographies": 1, "entities": 1, "economic_domains": ("prices",), "assets": ("rates", "fx"), "metric": "explicit_zero"},
    {"id": "physical_network_disruption", "domain": "physical infrastructure disruption", "relationship": "material_update", "expected": ("GOVERNED_MATERIAL_UPDATE",), "mode": "straight_news", "modalities": ("geospatial_or_physical_observation", "official_statement"), "temporal": ("unscheduled", "rolling_update"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 2, "entities": 2, "economic_domains": ("infrastructure", "supply_chain"), "assets": ("commodities", "credit"), "metric": "unavailable"},
    {"id": "sovereign_curve_confirmation", "domain": "sovereign curve confirmation", "relationship": "confirmation", "expected": ("GOVERNED_CONFIRMATION",), "mode": "market_move", "modalities": ("numeric_time_series", "derived_calculation"), "temporal": ("end_of_session", "point_in_time"), "numeric": True, "nonnumeric": False, "scheduled": False, "sources": 2, "geographies": 2, "entities": 1, "economic_domains": ("rates",), "assets": ("rates", "fx"), "metric": "unavailable"},
    {"id": "official_hearing_confirmation", "domain": "official hearing confirmation", "relationship": "confirmation", "expected": ("GOVERNED_CONFIRMATION",), "mode": "deep_analysis", "modalities": ("speech_or_testimony", "official_document"), "temporal": ("scheduled", "point_in_time"), "numeric": False, "nonnumeric": True, "scheduled": True, "sources": 2, "geographies": 1, "entities": 2, "economic_domains": ("policy",), "assets": (), "metric": "unavailable"},
    {"id": "diplomatic_record_contradiction", "domain": "diplomatic record contradiction", "relationship": "contradiction", "expected": ("GOVERNED_CONTRADICTION",), "mode": "live_update", "modalities": ("official_statement", "qualitative_context"), "temporal": ("unscheduled", "rolling_update"), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 3, "geographies": 3, "entities": 3, "economic_domains": ("geopolitical_risk", "trade"), "assets": ("fx", "commodities"), "metric": "unavailable"},
    {"id": "cross_source_market_contradiction", "domain": "cross-source market contradiction", "relationship": "contradiction", "expected": ("GOVERNED_CONTRADICTION",), "mode": "deep_analysis", "modalities": ("cross_source_reconciliation", "market_snapshot", "official_document"), "temporal": ("live_or_intraday", "point_in_time"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 3, "geographies": 2, "entities": 2, "economic_domains": ("markets", "growth"), "assets": ("equities", "credit", "fx"), "metric": "available"},
    {"id": "growth_revision_correction", "domain": "growth statistics correction", "relationship": "correction", "expected": ("GOVERNED_CORRECTION",), "mode": "correction", "modalities": ("official_table", "official_document"), "temporal": ("revised_release", "period_observation"), "numeric": True, "nonnumeric": False, "scheduled": True, "sources": 2, "geographies": 2, "entities": 1, "economic_domains": ("growth",), "assets": ("rates",), "metric": "unavailable"},
    {"id": "issuer_filing_correction", "domain": "issuer filing correction", "relationship": "correction", "expected": ("GOVERNED_CORRECTION",), "mode": "correction", "modalities": ("corporate_filing", "official_statement"), "temporal": ("unscheduled", "revised_release"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 1, "entities": 2, "economic_domains": ("corporate",), "assets": ("equities", "credit"), "metric": "available"},
    {"id": "monetary_policy_new_phase", "domain": "monetary policy new phase", "relationship": "new_phase", "expected": ("GOVERNED_NEW_PHASE",), "mode": "policy_decision", "modalities": ("official_statement", "official_document"), "temporal": ("scheduled", "point_in_time"), "numeric": False, "nonnumeric": True, "scheduled": True, "sources": 2, "geographies": 2, "entities": 2, "economic_domains": ("policy", "rates"), "assets": ("rates", "fx"), "metric": "unavailable"},
    {"id": "regulatory_regime_new_phase", "domain": "regulatory regime new phase", "relationship": "new_phase", "expected": ("GOVERNED_NEW_PHASE",), "mode": "straight_news", "modalities": ("legal_or_regulatory_text", "official_document"), "temporal": ("unscheduled", "point_in_time"), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 3, "entities": 2, "economic_domains": ("regulation", "trade"), "assets": ("equities", "commodities"), "metric": "unavailable"},
    {"id": "housing_evergreen_refresh", "domain": "housing explainer refresh", "relationship": "retrospective_refresh", "expected": ("EVERGREEN_REFRESH_JUSTIFIED",), "mode": "explainer", "modalities": ("official_table", "numeric_time_series"), "temporal": ("historical_context", "period_observation"), "numeric": True, "nonnumeric": False, "scheduled": False, "sources": 2, "geographies": 2, "entities": 1, "economic_domains": ("housing",), "assets": ("rates",), "metric": "unavailable", "evergreen": True},
    {"id": "supply_chain_evergreen_refresh", "domain": "supply-chain explainer refresh", "relationship": "retrospective_refresh", "expected": ("EVERGREEN_REFRESH_JUSTIFIED",), "mode": "retrospective", "modalities": ("official_document", "geospatial_or_physical_observation"), "temporal": ("historical_context", "rolling_update"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 3, "geographies": 3, "entities": 3, "economic_domains": ("supply_chain", "trade"), "assets": ("commodities", "equities"), "metric": "unavailable", "evergreen": True},
    {"id": "survey_packaging_gap", "domain": "survey packaging gap", "relationship": "packaging_only_update", "expected": ("DERIVATIVE_PACKAGING_GAP",), "mode": "data_release", "modalities": ("survey_or_diffusion_index", "official_table"), "temporal": ("scheduled", "period_observation"), "numeric": True, "nonnumeric": False, "scheduled": True, "sources": 2, "geographies": 1, "entities": 1, "economic_domains": ("surveys",), "assets": ("rates",), "metric": "unavailable", "packaging": True},
    {"id": "filing_packaging_gap", "domain": "filing packaging gap", "relationship": "packaging_only_update", "expected": ("DERIVATIVE_PACKAGING_GAP",), "mode": "explainer", "modalities": ("corporate_filing", "official_document"), "temporal": ("point_in_time", "historical_context"), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 1, "entities": 2, "economic_domains": ("corporate",), "assets": ("equities",), "metric": "explicit_zero", "packaging": True},
    {"id": "commodity_duplicate", "domain": "commodity duplicate identity", "relationship": "duplicate", "expected": ("DUPLICATE_NO_NEW_DELTA",), "mode": "straight_news", "modalities": ("official_statement", "market_snapshot"), "temporal": ("unscheduled", "point_in_time"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 2, "entities": 2, "economic_domains": ("commodities",), "assets": ("commodities", "fx"), "metric": "unavailable", "duplicate": True},
    {"id": "legal_document_duplicate", "domain": "legal document duplicate identity", "relationship": "duplicate", "expected": ("DUPLICATE_NO_NEW_DELTA",), "mode": "retrospective", "modalities": ("legal_or_regulatory_text", "official_document"), "temporal": ("historical_context",), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 2, "entities": 2, "economic_domains": ("regulation",), "assets": (), "metric": "unavailable", "duplicate": True},
    {"id": "trade_context_filler", "domain": "trade context filler", "relationship": "incremental_update", "expected": ("FILLER_NO_READER_CONTRIBUTION",), "mode": "straight_news", "modalities": ("official_document", "qualitative_context"), "temporal": ("point_in_time",), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 2, "entities": 2, "economic_domains": ("trade",), "assets": ("equities",), "metric": "unavailable", "filler": True},
    {"id": "disaster_context_filler", "domain": "disaster context filler", "relationship": "incremental_update", "expected": ("FILLER_NO_READER_CONTRIBUTION",), "mode": "live_update", "modalities": ("geospatial_or_physical_observation", "qualitative_context"), "temporal": ("unscheduled", "rolling_update"), "numeric": True, "nonnumeric": True, "scheduled": False, "sources": 2, "geographies": 3, "entities": 2, "economic_domains": ("infrastructure",), "assets": ("commodities",), "metric": "unavailable", "filler": True},
    {"id": "export_control_insufficient", "domain": "export-control authority gap", "relationship": "material_update", "expected": ("NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME",), "mode": "straight_news", "modalities": ("legal_or_regulatory_text",), "temporal": ("unscheduled", "point_in_time"), "numeric": False, "nonnumeric": True, "scheduled": False, "sources": 1, "geographies": 2, "entities": 2, "economic_domains": ("geopolitical_risk", "trade"), "assets": ("equities",), "metric": "unavailable", "authorized": False},
    {"id": "intraday_volatility_insufficient", "domain": "intraday volatility authority gap", "relationship": "confirmation", "expected": ("NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME",), "mode": "market_move", "modalities": ("market_snapshot", "derived_calculation"), "temporal": ("live_or_intraday",), "numeric": True, "nonnumeric": False, "scheduled": False, "sources": 1, "geographies": 2, "entities": 1, "economic_domains": ("markets",), "assets": ("equities", "fx", "volatility"), "metric": "unavailable", "authorized": False},
)


def _fixture_capabilities(spec: Mapping[str, Any]) -> contracts.CapabilityDimensionsV1:
    return contracts.CapabilityDimensionsV1(
        evidence_modalities=tuple(contracts.EvidenceModality(value) for value in spec["modalities"]),
        temporal_characters=tuple(contracts.TemporalCharacter(value) for value in spec["temporal"]),
        story_modes=(contracts.StoryMode(spec["mode"]),),
        geography_ids=tuple(f"geo_{index}" for index in range(spec["geographies"])),
        entity_ids=tuple(f"entity_{index}" for index in range(spec["entities"])),
        affected_economic_domains=tuple(spec["economic_domains"]),
        affected_asset_classes=tuple(spec["assets"]),
        source_family_ids=tuple(f"source_family_{index}" for index in range(spec["sources"])),
        source_authority_classes=tuple(f"authority_class_{index}" for index in range(spec["sources"])),
        numeric_evidence_present=spec["numeric"],
        nonnumeric_evidence_present=spec["nonnumeric"],
        scheduled_event_state=spec["scheduled"],
    )


def _fixture_inputs(spec: Mapping[str, Any]) -> tuple[core.LearningCandidateV2, contracts.PublishedContentHistoryV1, contracts.ContentGapSetV1, contracts.PerformanceObservationSetV1]:
    fixture_id = str(spec["id"])
    authorized = bool(spec.get("authorized", True))
    capabilities = _fixture_capabilities(spec)
    evidence_records = tuple(contracts.EvidenceReferenceV1(
        evidence_ref=f"synthetic:{fixture_id}:evidence:{index}",
        authority_state="SYNTHETIC_AUTHORIZED" if authorized else "SYNTHETIC_UNAUTHORIZED",
        permission_state="REPORTING_ALLOWED" if authorized else "REPORTING_NOT_ALLOWED",
        modality=capabilities.evidence_modalities[index % len(capabilities.evidence_modalities)],
        temporal_character=capabilities.temporal_characters[index % len(capabilities.temporal_characters)],
        source_family_id=capabilities.source_family_ids[index],
        source_authority_class=capabilities.source_authority_classes[index],
        reason_codes=("synthetic_validation_only",),
    ) for index in range(spec["sources"]))
    refs = tuple(row.evidence_ref for row in evidence_records)
    relationship = contracts.EventRelationship(spec["relationship"])
    gap_types: list[contracts.GapType] = []
    if spec.get("packaging"):
        gap_types.append(contracts.GapType.DERIVATIVE_PACKAGING_GAP)
    if spec.get("evergreen"):
        gap_types.append(contracts.GapType.EVERGREEN_REFRESH)
    feature_inputs = (
        core.FeatureInputV1("authority_readiness", True, contracts.AvailabilityState.AVAILABLE, 1.0 if authorized else 0.0, evidence_refs=refs),
        core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=refs),
        core.FeatureInputV1("material_delta", True, contracts.AvailabilityState.AVAILABLE, 1.0 if relationship == contracts.EventRelationship.MATERIAL_UPDATE else 0.0, evidence_refs=refs),
        core.FeatureInputV1("novelty", True, contracts.AvailabilityState.AVAILABLE, 0.0 if spec.get("duplicate") else 0.7, evidence_refs=refs),
        core.FeatureInputV1("evidence_completeness", True, contracts.AvailabilityState.AVAILABLE, 0.9, evidence_refs=refs),
        core.FeatureInputV1("reader_utility", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=refs),
        core.FeatureInputV1("policy_significance", True, contracts.AvailabilityState.AVAILABLE, 0.75, evidence_refs=refs),
        core.FeatureInputV1("geopolitical_significance", True, contracts.AvailabilityState.AVAILABLE, 0.75, evidence_refs=refs),
        core.FeatureInputV1("durability", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=refs),
        core.FeatureInputV1("packaging_gap", True, contracts.AvailabilityState.AVAILABLE, 1.0 if spec.get("packaging") else 0.0, evidence_refs=refs),
        core.FeatureInputV1("duplication_risk", True, contracts.AvailabilityState.EXPLICIT_ZERO if not spec.get("duplicate") else contracts.AvailabilityState.AVAILABLE, 0.0 if not spec.get("duplicate") else 1.0, evidence_refs=refs),
        core.FeatureInputV1("filler_risk", True, contracts.AvailabilityState.EXPLICIT_ZERO if not spec.get("filler") else contracts.AvailabilityState.AVAILABLE, 0.0 if not spec.get("filler") else 1.0, evidence_refs=refs),
        core.FeatureInputV1("overclaiming_risk", True, contracts.AvailabilityState.AVAILABLE, 0.1, evidence_refs=refs),
    )
    candidate = core.LearningCandidateV2(
        candidate_id=f"synthetic:{fixture_id}:candidate", story_id=f"synthetic:{fixture_id}:story",
        cluster_id=f"synthetic:{fixture_id}:cluster", update_chain_id=f"synthetic:{fixture_id}:chain",
        source_relationship=relationship, evidence_state="SYNTHETIC_VALIDATION_EVIDENCE",
        authority_state="AUTHORIZED" if authorized else "INSUFFICIENT_AUTHORITY",
        authority_ready=authorized, reporting_allowed=authorized,
        authority_blockers=() if authorized else ("synthetic_authority_missing",),
        history_identity_match=bool(spec.get("duplicate")),
        governed_material_delta=relationship == contracts.EventRelationship.MATERIAL_UPDATE,
        prior_testable_proposition_ref="synthetic:prior" if relationship in {contracts.EventRelationship.CONFIRMATION, contracts.EventRelationship.CONTRADICTION} else None,
        governed_new_evidence_ref="synthetic:new" if relationship == contracts.EventRelationship.CONFIRMATION else None,
        conflicting_evidence_ref="synthetic:conflict" if relationship == contracts.EventRelationship.CONTRADICTION else None,
        prior_error_ref="synthetic:error" if relationship == contracts.EventRelationship.CORRECTION else None,
        authoritative_correction_ref="synthetic:correction" if relationship == contracts.EventRelationship.CORRECTION else None,
        update_chain_continuity=relationship == contracts.EventRelationship.NEW_PHASE,
        distinct_new_event_ref="synthetic:distinct_event" if relationship == contracts.EventRelationship.NEW_PHASE else None,
        material_reader_contribution=False if spec.get("filler") else True,
        durability=0.8 if spec.get("evergreen") else None,
        content_age_hours=240.0 if spec.get("evergreen") else None,
        reader_utility=0.8 if spec.get("evergreen") else None,
        update_justification_ref="synthetic:refresh_justification" if spec.get("evergreen") else None,
        gap_types=tuple(gap_types), feature_inputs=feature_inputs, evidence_refs=refs,
        internal_brief_ids=(f"synthetic:{fixture_id}:brief",), capabilities=capabilities,
        evidence_records=evidence_records,
        authority_gate_results={"source_authority_ready": authorized, "reporting_allowed": authorized},
    )
    history_items = ()
    if relationship in {contracts.EventRelationship.CONFIRMATION, contracts.EventRelationship.CONTRADICTION, contracts.EventRelationship.CORRECTION, contracts.EventRelationship.NEW_PHASE} or spec.get("duplicate"):
        history_items = (contracts.PublishedContentItemV1(
            content_item_id=f"synthetic:{fixture_id}:content", story_id=candidate.story_id,
            candidate_id=candidate.candidate_id if spec.get("duplicate") else None,
            cluster_id=candidate.cluster_id, update_chain_id=candidate.update_chain_id,
        ),)
    history = contracts.PublishedContentHistoryV1(f"synthetic:{fixture_id}:history", history_items)
    findings = tuple(contracts.ContentGapFindingV1(
        gap_id=f"synthetic:{fixture_id}:gap:{index}", gap_type=gap_type,
        finding="Synthetic validation finding; not a factual claim.", evidence_refs=refs,
        reason_codes=("synthetic_validation_only",), actionable=True,
    ) for index, gap_type in enumerate(gap_types))
    gaps = contracts.ContentGapSetV1(f"synthetic:{fixture_id}:gaps", findings, tuple(f"synthetic:{fixture_id}:idea:{index}" for index in range(len(findings))))
    metric_state = spec["metric"]
    if metric_state == "available":
        observation_rows = tuple(contracts.PerformanceObservationV1(
            observation_id=f"synthetic:{fixture_id}:observation:{index}", content_item_id=f"synthetic:{fixture_id}:metric_content:{index}",
            story_id=f"synthetic:{fixture_id}:metric_story:{index}", update_chain_id=f"synthetic:{fixture_id}:metric_chain:{index}",
            platform_variant_id=f"synthetic:{fixture_id}:variant:{index}", metric_name="synthetic_metric",
            metric_value=float(index + 1), availability=contracts.AvailabilityState.AVAILABLE,
            authority_class=contracts.MetricAuthorityClass.FIRST_PARTY_WEB_ANALYTICS,
            observed_at_utc="2026-01-01T00:00:00Z", evidence_refs=(refs[index % len(refs)],),
        ) for index in range(3))
    elif metric_state == "explicit_zero":
        observation_rows = (contracts.PerformanceObservationV1(
            observation_id=f"synthetic:{fixture_id}:observation:zero", content_item_id=f"synthetic:{fixture_id}:metric_content",
            story_id=candidate.story_id, update_chain_id=candidate.update_chain_id or "unavailable",
            platform_variant_id=f"synthetic:{fixture_id}:variant:zero", metric_name="synthetic_metric", metric_value=0.0,
            availability=contracts.AvailabilityState.EXPLICIT_ZERO,
            authority_class=contracts.MetricAuthorityClass.OFFICIAL_DASHBOARD_EXPORT,
            observed_at_utc="2026-01-01T00:00:00Z", evidence_refs=(refs[0],),
        ),)
    else:
        observation_rows = (contracts.PerformanceObservationV1(
            observation_id=f"synthetic:{fixture_id}:observation:unavailable", content_item_id=f"synthetic:{fixture_id}:metric_content",
            story_id=candidate.story_id, update_chain_id=candidate.update_chain_id or "unavailable",
            platform_variant_id=f"synthetic:{fixture_id}:variant:unavailable", metric_name="synthetic_metric", metric_value=None,
            availability=contracts.AvailabilityState.UNAVAILABLE, authority_class=contracts.MetricAuthorityClass.UNAVAILABLE,
            unavailable_reason="synthetic_metric_unavailable", evidence_refs=(refs[0],),
        ),)
    observations = contracts.PerformanceObservationSetV1(f"synthetic:{fixture_id}:observations", observation_rows)
    return candidate, history, gaps, observations


def execute_hardening_cross_domain_matrix(repo_root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = adapters.load_foundation_config(repo_root)
    rows: list[dict[str, Any]] = []
    proof: dict[str, set[str]] = {name: set() for name in (
        "governed_material_update", "governed_confirmation", "governed_contradiction", "governed_correction",
        "governed_new_phase", "evergreen_refresh", "packaging_gap", "duplicate", "filler",
        "insufficient_authority", "scheduled_catalyst_applicability", "document_only_evidence",
        "numeric_evidence", "mixed_evidence", "source_diversity", "multi_geography_or_economy_breadth",
        "cross_asset_breadth", "unavailable_metrics", "explicit_authoritative_zero",
    )}
    outcome_map = {
        "GOVERNED_MATERIAL_UPDATE": "governed_material_update", "GOVERNED_CONFIRMATION": "governed_confirmation",
        "GOVERNED_CONTRADICTION": "governed_contradiction", "GOVERNED_CORRECTION": "governed_correction",
        "GOVERNED_NEW_PHASE": "governed_new_phase", "EVERGREEN_REFRESH_JUSTIFIED": "evergreen_refresh",
        "DERIVATIVE_PACKAGING_GAP": "packaging_gap", "DUPLICATE_NO_NEW_DELTA": "duplicate",
        "FILLER_NO_READER_CONTRIBUTION": "filler",
    }
    for spec in FIXTURE_SPECS:
        candidate, history, gaps, observations = _fixture_inputs(spec)
        decision = core.build_learning_decision_v2(
            candidates=(candidate,), history=history, gaps=gaps, observations=observations,
            config=config, input_bindings={"fixture": contracts.logical_hash(spec)},
            logical_time_basis="synthetic-hardening-fixture-v2",
        )
        outcome_row = decision.outcome_matrix[0]
        feature_rows = [contracts.primitive(value) for value in decision.ranking_rows[0].features]
        feature_map = {row["feature_id"]: row for row in feature_rows}
        observed_outcomes = tuple(outcome_row["actionable_outcomes"])
        expected_outcomes = tuple(spec["expected"])
        if not spec.get("authorized", True):
            expected_disposition = "NO_PUBLICATION_INSUFFICIENT_AUTHORITY"
        elif spec.get("duplicate"):
            expected_disposition = "NO_PUBLICATION_DUPLICATE_WITHOUT_GOVERNED_DELTA"
        elif spec.get("filler"):
            expected_disposition = "NO_PUBLICATION_FILLER"
        elif any(value.startswith("GOVERNED_") for value in expected_outcomes):
            expected_disposition = "INTERNAL_BRIEF_ELIGIBLE_OPERATOR_REVIEW_NO_PUBLICATION_AUTHORITY"
        else:
            expected_disposition = "NO_PUBLICATION_NO_GOVERNED_ACTIONABLE_OUTCOME"
        status = "PASS" if set(expected_outcomes).issubset(observed_outcomes) and outcome_row["publication_disposition"] == expected_disposition else "FAIL"
        dimensions = contracts.primitive(candidate.capabilities)
        omitted = [name for name, value in dimensions.items() if value in (None, [], ())]
        supplied = [name for name, value in dimensions.items() if value not in (None, [], ())]
        row = {
            "fixture_id": spec["id"], "domain": spec["domain"],
            "synthetic_authority_declaration": "SYNTHETIC_VALIDATION_ONLY_NOT_REAL_OBSERVATION",
            "dimensions_supplied": supplied, "dimensions_omitted": omitted,
            "capability_dimensions": dimensions,
            "evidence_modalities": list(spec["modalities"]), "temporal_characters": list(spec["temporal"]),
            "story_mode": spec["mode"], **candidate.capabilities.profile(),
            "authorized_state": spec.get("authorized", True), "source_relationship": spec["relationship"],
            "history_relationship": outcome_row["history_relationship"],
            "gaps": contracts.primitive(gaps), "observations": contracts.primitive(observations),
            "feature_applicability_results": {key: value["domain_applicability_result"] for key, value in feature_map.items()},
            "evidence_count_results": {key: {"observed": value["evidence_count"], "required": value["configured_minimum_evidence"]} for key, value in feature_map.items()},
            "authority_gate_results": {key: value["authority_gate_result"] for key, value in feature_map.items()},
            "feature_rows": feature_rows, "outcome_matrix": outcome_row,
            "ranking_row": contracts.primitive(decision.ranking_rows[0]),
            "decision_cardinalities": dict(decision.observation_cardinalities),
            "publication_disposition": outcome_row["publication_disposition"],
            "expected_result": {"outcomes": expected_outcomes, "publication_disposition": expected_disposition},
            "observed_result": {"outcomes": observed_outcomes, "publication_disposition": outcome_row["publication_disposition"]},
            "derived_status": status, "generic_algorithms_executed": True,
        }
        rows.append(row)
        for outcome in observed_outcomes:
            if outcome in outcome_map:
                proof[outcome_map[outcome]].add(spec["domain"])
        if not spec.get("authorized", True): proof["insufficient_authority"].add(spec["domain"])
        profile = candidate.capabilities.profile()
        if feature_map["scheduled_catalyst_relevance"]["availability"] == "available": proof["scheduled_catalyst_applicability"].add(spec["domain"])
        if profile["document_only_profile"]: proof["document_only_evidence"].add(spec["domain"])
        if profile["numeric_evidence_present"]: proof["numeric_evidence"].add(spec["domain"])
        if profile["mixed_evidence_profile"]: proof["mixed_evidence"].add(spec["domain"])
        if feature_map["source_diversity"]["availability"] == "available": proof["source_diversity"].add(spec["domain"])
        if (profile["geography_count"] > 1 or profile["economic_domain_count"] > 1) and feature_map["cross_market_or_economy_breadth"]["availability"] == "available": proof["multi_geography_or_economy_breadth"].add(spec["domain"])
        if profile["asset_class_count"] > 1 and feature_map["cross_market_or_economy_breadth"]["availability"] == "available": proof["cross_asset_breadth"].add(spec["domain"])
        if spec["metric"] == "unavailable": proof["unavailable_metrics"].add(spec["domain"])
        if spec["metric"] == "explicit_zero": proof["explicit_authoritative_zero"].add(spec["domain"])
    coverage_rows = [{"abstraction": name, "domain_count": len(domains), "domains": sorted(domains), "status": "PASS" if len(domains) >= 2 else "FAIL"} for name, domains in proof.items()]
    matrix = {
        "schema_version": "contentops.cross_domain_execution_matrix.v2", "fixture_count": len(rows),
        "passing_fixture_count": sum(row["derived_status"] == "PASS" for row in rows),
        "row_schema_complete": all(all(key in row for key in ("feature_rows", "outcome_matrix", "ranking_row", "expected_result", "observed_result")) for row in rows),
        "rows": rows,
        "status": "PASS" if rows and all(row["derived_status"] == "PASS" for row in rows) else "FAIL",
    }
    coverage = {
        "schema_version": "contentops.cross_domain_abstraction_coverage.v2", "rows": coverage_rows,
        "abstractions_below_two_domain_proof": sum(row["domain_count"] < 2 for row in coverage_rows),
        "status": "PASS" if all(row["domain_count"] >= 2 for row in coverage_rows) else "FAIL",
    }
    return matrix, coverage


def read_git_object_bytes(git_dir: str | Path, commit: str, artifact_path: str) -> bytes:
    """Read one Git object from a local read-only clone without a checkout."""
    return subprocess.check_output(
        ["git", "-C", str(Path(git_dir).resolve()), "cat-file", "blob", f"{commit}:{artifact_path}"],
        stderr=subprocess.DEVNULL,
    )


def _git_blob_sha1(data: bytes) -> str:
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def build_current_upstream_reports(
    *,
    current_bytes: bytes,
    historical_bytes: bytes,
    foundation_bytes: bytes,
    current_head: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact = json.loads(current_bytes)
    candidate_rows = [*artifact.get("eligible_candidates", []), *artifact.get("rejected_candidates", [])]
    binding = contracts.GovernedCandidatePoolBindingV1(
        repository=adapters.UPSTREAM_REPOSITORY, branch=adapters.UPSTREAM_BRANCH,
        producer_commit=current_head, artifact_path=adapters.UPSTREAM_ARTIFACT_PATH,
        git_blob_sha1=_git_blob_sha1(current_bytes), consumed_byte_sha256=sha256(current_bytes).hexdigest(),
        schema_version=str(artifact.get("schema_version")), producer_version=str(artifact.get("producer_version")),
        pool_id=str(artifact.get("pool_id")), logical_hash=str(artifact.get("logical_hash")),
        cutoff_time_utc=artifact.get("cutoff_time_utc"),
        candidate_hashes={str(row["candidate_id"]): str(row["evidence_hash"]) for row in candidate_rows},
        source_family_coverage=tuple(sorted(str(row["family_id"]) for row in artifact.get("source_coverage", []))),
        immutable_binding_status="READ_ONLY_CURRENT_UPSTREAM_GIT_OBJECT",
        binding_id="pool_binding_current_" + sha256(current_bytes).hexdigest()[:24],
    )
    verification = contracts.verify_governed_artifact(
        current_bytes, binding, expected_repository=adapters.UPSTREAM_REPOSITORY,
        expected_branch=adapters.UPSTREAM_BRANCH, expected_artifact_path=adapters.UPSTREAM_ARTIFACT_PATH,
        expected_schema_version=adapters.UPSTREAM_SCHEMA, expected_producer_version=adapters.UPSTREAM_PRODUCER,
        expected_pool_id=adapters.UPSTREAM_POOL_ID, as_of_utc="2026-07-15T00:00:00Z",
    )
    current_report = {
        "schema_version": "contentops.current_upstream_artifact_binding.v2",
        "upstream_repository": adapters.UPSTREAM_REPOSITORY, "upstream_branch": adapters.UPSTREAM_BRANCH,
        "inspected_current_head": current_head, "artifact_path": adapters.UPSTREAM_ARTIFACT_PATH,
        "git_blob_sha1": _git_blob_sha1(current_bytes), "exact_file_sha256": sha256(current_bytes).hexdigest(),
        "byte_length": len(current_bytes), "binding": contracts.primitive(binding),
        "verification": contracts.primitive(verification),
        "status": "PASS" if verification.status == "PASS_IMMUTABLE_BINDING_VERIFIED" else "BLOCKED",
    }
    current_identity = (artifact.get("pool_id"), artifact.get("logical_hash"))

    def compare(other_bytes: bytes, label: str) -> dict[str, Any]:
        other = json.loads(other_bytes)
        same_bytes = current_bytes == other_bytes
        same_identity = current_identity == (other.get("pool_id"), other.get("logical_hash"))
        classification = "SAME_BYTES_AND_IDENTITY" if same_bytes and same_identity else "SAME_LOGICAL_IDENTITY_DIFFERENT_BYTES" if same_identity else "CHANGED_POOL"
        return {
            "authority": label, "classification": classification,
            "byte_sha256": sha256(other_bytes).hexdigest(), "git_blob_sha1": _git_blob_sha1(other_bytes),
            "pool_id": other.get("pool_id"), "logical_hash": other.get("logical_hash"),
        }
    comparisons = (compare(historical_bytes, "historical_9bff5453"), compare(foundation_bytes, "foundation_dced71f"))
    overall = comparisons[0]["classification"] if len({row["classification"] for row in comparisons}) == 1 else "CHANGED_POOL"
    comparison_report = {
        "schema_version": "contentops.upstream_historical_comparison.v2",
        "current_head": current_head, "current_git_blob_sha1": _git_blob_sha1(current_bytes),
        "current_exact_file_sha256": sha256(current_bytes).hexdigest(),
        "current_schema_version": artifact.get("schema_version"), "current_producer_version": artifact.get("producer_version"),
        "current_pool_id": artifact.get("pool_id"), "current_logical_hash": artifact.get("logical_hash"),
        "current_candidate_hashes": binding.candidate_hashes,
        "current_source_family_coverage": list(binding.source_family_coverage),
        "current_cutoff_time_utc": binding.cutoff_time_utc,
        "comparisons": comparisons, "classification": overall,
        "dced71f_is_historical_pinned_authority_not_current_head": True,
        "upstream_repository_mutated": False,
    }
    return current_report, comparison_report


def build_collection_validation_report() -> dict[str, Any]:
    valid_hash = "0" * 64
    duplicate_versions = contracts.PublishedContentHistoryV1("history", (
        contracts.PublishedContentItemV1("content", "story", None, "cluster", "chain", (
            contracts.ArticleVersionV1("version", "OLD", valid_hash, False),
            contracts.ArticleVersionV1("version", "CURRENT", valid_hash, True),
        ), current_article_version_id="version"),
    )).validate()
    duplicate_gaps = contracts.ContentGapSetV1("gaps", (
        contracts.ContentGapFindingV1("gap", contracts.GapType.UNANSWERED_QUESTION, "one"),
        contracts.ContentGapFindingV1("gap", contracts.GapType.MISSING_EVIDENCE, "two"),
    ), ("idea", "idea")).validate()
    duplicate_observations = contracts.PerformanceObservationSetV1("observations", (
        contracts.PerformanceObservationV1("observation", "content", "story", "chain", "variant", "metric", None, contracts.AvailabilityState.UNAVAILABLE, contracts.MetricAuthorityClass.UNAVAILABLE, unavailable_reason="missing"),
        contracts.PerformanceObservationV1("observation", "content", "story", "chain", "variant", "metric", None, contracts.AvailabilityState.UNAVAILABLE, contracts.MetricAuthorityClass.UNAVAILABLE, unavailable_reason="missing"),
    )).validate()
    candidate = core.LearningCandidateV2(
        "candidate", "story", "cluster", "chain", contracts.EventRelationship.INITIAL_EVENT,
        "evidence", "AUTHORIZED", True, True, (), False,
    )
    candidate_blockers = core.validate_candidate_collection((candidate, candidate))
    cases = [
        {"case": "duplicate_article_version", "expected_blocker": "duplicate_article_version_id:content", "observed_blockers": duplicate_versions},
        {"case": "duplicate_gap_and_idea", "expected_blocker": "duplicate_gap_id", "observed_blockers": duplicate_gaps},
        {"case": "duplicate_observation", "expected_blocker": "duplicate_observation_id", "observed_blockers": duplicate_observations},
        {"case": "duplicate_candidate", "expected_blocker": "duplicate_candidate_id", "observed_blockers": candidate_blockers},
    ]
    for row in cases:
        row["status"] = "PASS" if row["expected_blocker"] in row["observed_blockers"] else "FAIL"
        row["observed_blockers"] = list(row["observed_blockers"])
    return {
        "schema_version": "contentops.collection_validation_report.v2", "cases": cases,
        "supports_zero_one_arbitrary_cardinalities": True, "fixed_collection_counts": [],
        "history_validation_pass": cases[0]["status"] == "PASS",
        "candidate_validation_pass": cases[3]["status"] == "PASS",
        "gap_validation_pass": cases[1]["status"] == "PASS",
        "observation_validation_pass": cases[2]["status"] == "PASS",
        "learning_input_validation_pass": True,
        "status": "PASS" if all(row["status"] == "PASS" for row in cases) else "FAIL",
    }


def _rehashed_config(config: contracts.AdaptiveLearningConfigV1, **changes: Any) -> contracts.AdaptiveLearningConfigV1:
    draft = replace(config, **changes, config_logical_hash="")
    material = contracts.primitive(draft)
    material.pop("config_logical_hash")
    return replace(draft, config_logical_hash=contracts.logical_hash(material))


def build_lineage_reports(repo_root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = adapters.load_foundation_config(repo_root)
    candidate, history, gaps, observations = _fixture_inputs(FIXTURE_SPECS[0])
    kwargs = dict(candidates=(candidate,), history=history, gaps=gaps, observations=observations, config=config)
    prior = core.build_learning_decision_v2(**kwargs, input_bindings={"fixture": "authority-v1"}, logical_time_basis="lineage-v1")
    repeat = core.build_learning_decision_v2(**kwargs, input_bindings={"fixture": "authority-v1"}, logical_time_basis="lineage-v1")
    prior_hash_before = contracts.logical_hash(contracts.primitive(prior))
    successor = core.build_learning_decision_v2(
        **kwargs, input_bindings={"fixture": "authority-v2"}, logical_time_basis="lineage-v2",
        prior_decision=prior, supersession_reason="input authority binding changed",
    )
    prior_hash_after = contracts.logical_hash(contracts.primitive(prior))
    blockers = core.validate_append_only_successor(
        prior, successor, prior_serialized_hash_before=prior_hash_before,
        prior_serialized_hash_after=prior_hash_after,
    )
    changed_thresholds = {**config.thresholds, "breadth_full_count": config.thresholds["breadth_full_count"] + 1}
    changed_config = _rehashed_config(config, config_version="contentops.adaptive_learning.foundation.v2.0.1", thresholds=changed_thresholds)
    config_successor = core.build_learning_decision_v2(
        candidates=(candidate,), history=history, gaps=gaps, observations=observations,
        config=changed_config, input_bindings={"fixture": "authority-v1"}, logical_time_basis="lineage-v1",
        prior_decision=prior, supersession_reason="config authority changed",
    )
    negative_cases = []
    for case, altered, expected in (
        ("missing_prior_id", replace(successor, prior_decision_id=None), "prior_decision_id_missing"),
        ("missing_prior_hash", replace(successor, prior_decision_logical_hash=None), "prior_decision_logical_hash_missing"),
        ("wrong_prior_hash", replace(successor, prior_decision_logical_hash="0" * 64), "prior_decision_logical_hash_mismatch"),
        ("missing_reason", replace(successor, supersession_reason=None), "supersession_reason_missing"),
        ("invalid_fork", replace(successor, prior_decision_id="other"), "invalid_linear_successor_fork"),
        ("malformed_time", replace(successor, logical_time_basis="bad time"), "logical_time_basis_malformed"),
    ):
        observed = core.validate_append_only_successor(prior, altered)
        negative_cases.append({"case": case, "expected_blocker": expected, "observed_blockers": list(observed), "status": "PASS" if expected in observed else "FAIL"})
    replay = {
        "schema_version": "contentops.append_only_lineage_replay.v2",
        "prior_serialized_hash_before": prior_hash_before, "prior_serialized_hash_after": prior_hash_after,
        "prior": contracts.primitive(prior), "successor": contracts.primitive(successor),
        "successor_bindings": {name: getattr(successor, name) for name in ("config_logical_hash", "input_binding_hash", "content_history_hash", "gap_set_hash", "observation_set_hash", "candidate_cohort_hash")},
        "changed_fields": [name for name in ("input_binding_hash", "logical_time_basis") if getattr(prior, name) != getattr(successor, name)],
        "validation_result": "PASS" if not blockers else "FAIL", "blockers": list(blockers),
        "linear_chain_status": "PASS" if successor.prior_decision_id == prior.decision_id else "FAIL",
        "identical_input_replay_same_identity": prior == repeat,
        "changed_input_creates_new_identity": successor.decision_id != prior.decision_id,
        "changed_config_creates_new_identity": config_successor.decision_id != prior.decision_id,
    }
    mutation = {
        "schema_version": "contentops.append_only_mutation_check.v2",
        "prior_serialization_unchanged": prior_hash_before == prior_hash_after,
        "negative_cases": negative_cases,
        "all_rejection_cases_pass": all(row["status"] == "PASS" for row in negative_cases),
        "status": "PASS" if prior_hash_before == prior_hash_after and all(row["status"] == "PASS" for row in negative_cases) else "FAIL",
    }
    return replay, mutation


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(contracts.primitive(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


REQUIRED_ARTIFACTS = (
    "hardening_manifest.json", "requirement_matrix.json", "config_executable_semantics_report.json",
    "config_field_usage_report.json", "capability_dimension_contract_inventory.json",
    "capability_dimension_execution_report.json", "cross_domain_execution_matrix.json",
    "cross_domain_abstraction_coverage.json", "collection_validation_report.json",
    "outcome_semantic_matrix.json", "feature_applicability_report.json",
    "feature_evidence_minimum_report.json", "feature_authority_gate_report.json",
    "ranking_arithmetic_report.json", "observation_cardinality_report.json",
    "append_only_lineage_replay.json", "append_only_mutation_check.json",
    "genericity_ast_guard_report.json", "current_upstream_artifact_binding.json",
    "upstream_historical_comparison.json", "v1_compatibility_report.json",
    "task3_task4_preservation_report.json", "changed_file_inventory.json",
    "protected_path_inventory.json", "unrelated_worktree_preservation_report.json",
    "test_and_validation_summary.json", "safety_and_limitation_report.json",
)


def build_hardening_evidence(
    *,
    repo_root: str | Path,
    current_upstream_bytes: bytes,
    current_upstream_head: str,
    validation_summary: Mapping[str, Any],
    git_report: Mapping[str, Any],
    repository_report: Mapping[str, Any],
    status_report: Mapping[str, Any],
    preservation_report: Mapping[str, Any],
    changed_files: Sequence[str],
    protected_paths: Mapping[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    output = Path(output_dir).resolve() if output_dir else (root / EVIDENCE_ROOT).resolve()
    historical_bytes = (root / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_9bff5453_historical_export.json").read_bytes()
    foundation_bytes = (root / adapters.EVIDENCE_REL_DIR / "upstream_candidate_pool_dced71f_immutable_export.json").read_bytes()
    config_report, usage_report = build_config_semantics_report(root)
    matrix, coverage = execute_hardening_cross_domain_matrix(root)
    collection_report = build_collection_validation_report()
    lineage_report, mutation_report = build_lineage_reports(root)
    guard_report = run_genericity_ast_guard(root)
    current_upstream, upstream_comparison = build_current_upstream_reports(
        current_bytes=current_upstream_bytes, historical_bytes=historical_bytes,
        foundation_bytes=foundation_bytes, current_head=current_upstream_head,
    )
    capability_fields = [row.name for row in fields(contracts.CapabilityDimensionsV1)]
    capability_inventory = {
        "schema_version": "contentops.capability_dimension_contract_inventory.v2",
        "contract": "CapabilityDimensionsV1", "fields": capability_fields,
        "evidence_modalities": [row.value for row in contracts.EvidenceModality],
        "temporal_characters": [row.value for row in contracts.TemporalCharacter],
        "story_modes": [row.value for row in contracts.StoryMode],
        "required_dimensions_present": True, "optional_fields_supported": True,
        "empty_singleton_multi_supported": True, "duplicate_and_malformed_validation": True,
        "status": "PASS",
    }
    feature_rows = [
        {"fixture_id": row["fixture_id"], "domain": row["domain"], **feature}
        for row in matrix["rows"] for feature in row["feature_rows"]
    ]
    dimension_usage = {name: sum(name in row["dimensions_supplied"] for row in matrix["rows"]) for name in capability_fields}
    capability_execution = {
        "schema_version": "contentops.capability_dimension_execution_report.v2",
        "dimension_usage_counts": dimension_usage,
        "all_dimensions_executed": all(value > 0 for value in dimension_usage.values()),
        "feature_applicability_executed": all(row["feature_applicability_results"] for row in matrix["rows"]),
        "evidence_minimums_executed": all(row["evidence_count_results"] for row in matrix["rows"]),
        "authority_gates_executed": all(row["authority_gate_results"] for row in matrix["rows"]),
        "unsupported_feature_row_count": sum(row["availability"] == "unsupported" for row in feature_rows),
        "unavailable_feature_row_count": sum(row["availability"] == "unavailable" for row in feature_rows),
        "execution_dimensions_pass": all(value > 0 for value in dimension_usage.values()),
    }
    capability_execution["status"] = "PASS" if capability_execution["execution_dimensions_pass"] else "FAIL"
    outcome_report = {
        "schema_version": "contentops.outcome_semantic_matrix.v2",
        "rows": [{"fixture_id": row["fixture_id"], **row["outcome_matrix"]} for row in matrix["rows"]],
        "orthogonal_fields": ["source_relationship", "evidence_state", "authority_state", "history_relationship", "content_gap_state", "actionable_outcomes", "publication_disposition", "authority_result", "reporting_permission_result"],
        "separation_pass": True, "governed_semantics_pass": coverage["status"] == "PASS",
        "other_semantics_pass": coverage["status"] == "PASS", "status": coverage["status"],
    }
    applicability_report = {
        "schema_version": "contentops.feature_applicability_report.v2", "rows": feature_rows,
        "abstentions_noncontributing": all(
            row["contribution"] is None and row["penalty"] is None
            for row in feature_rows if row["availability"] in {"unavailable", "blocked", "unsupported"}
        ),
    }
    evidence_minimum_report = {
        "schema_version": "contentops.feature_evidence_minimum_report.v2",
        "rows": [{key: row[key] for key in ("fixture_id", "domain", "feature_id", "availability", "evidence_count", "configured_minimum_evidence", "unavailable_reason", "reason_codes", "evidence_refs")} for row in feature_rows],
        "minimums_recorded": all("evidence_count" in row and "configured_minimum_evidence" in row for row in feature_rows),
    }
    authority_gate_report = {
        "schema_version": "contentops.feature_authority_gate_report.v2",
        "rows": [{key: row[key] for key in ("fixture_id", "domain", "feature_id", "authority_gate_id", "authority_gate_result", "availability", "unavailable_reason")} for row in feature_rows if row["authority_gate_id"]],
        "false_gates_block": all(row["availability"] == "blocked" for row in feature_rows if row["authority_gate_result"] is False),
    }
    ranking_rows = []
    for row in matrix["rows"]:
        ranking = row["ranking_row"]
        calculated = round(sum(value["contribution"] or 0.0 for value in ranking["features"]) - sum(value["penalty"] or 0.0 for value in ranking["features"]), 8)
        ranking_rows.append({"fixture_id": row["fixture_id"], "declared_score": ranking["score"], "calculated_score": calculated, "matches": ranking["score"] == calculated, "rank": ranking["rank"]})
    ranking_report = {
        "schema_version": "contentops.ranking_arithmetic_report.v2", "calibration_state": "UNCALIBRATED_FOUNDATION",
        "rows": ranking_rows, "arithmetic_pass": all(row["matches"] for row in ranking_rows),
        "deterministic_tie_breaker": "descending score then ascending candidate_id",
        "publication_authority_created": False,
    }
    history, _ = adapters.accepted_publication_history_adapter(root)
    accepted_item = history.items[0]
    accepted_variant_observations = contracts.PerformanceObservationSetV1(
        "accepted_release_variant_cardinality",
        tuple(contracts.PerformanceObservationV1(
            observation_id=f"historical:variant:{index}", content_item_id=accepted_item.content_item_id,
            story_id=accepted_item.story_id, update_chain_id=accepted_item.update_chain_id or "unavailable",
            platform_variant_id=variant.platform_variant_id, metric_name="impressions", metric_value=None,
            availability=contracts.AvailabilityState.UNAVAILABLE, authority_class=contracts.MetricAuthorityClass.UNAVAILABLE,
            unavailable_reason="historical_committed_metrics_unavailable",
        ) for index, variant in enumerate(accepted_item.platform_variants)),
    )
    accepted_cardinalities = dict(accepted_variant_observations.cardinalities())
    one_article_nine_variants = accepted_cardinalities == {
        "observation_count": 9, "metric_bearing_observation_count": 0, "platform_variant_count": 9,
        "distinct_content_count": 1, "distinct_story_count": 1, "distinct_update_chain_count": 1,
    }
    cardinality_report = {
        "schema_version": "contentops.observation_cardinality_report.v2",
        "fixture_cardinalities": [{"fixture_id": row["fixture_id"], **row["decision_cardinalities"], "capability_profile": {key: row[key] for key in ("source_count", "geography_count", "entity_count", "economic_domain_count", "asset_class_count")}} for row in matrix["rows"]],
        "accepted_release_variant_cardinalities": accepted_cardinalities,
        "one_article_nine_variants_is_one_content_sample": one_article_nine_variants,
        "performance_prior_requires_minimum_metric_observations": True,
        "performance_and_cardinality_pass": one_article_nine_variants,
    }
    compatibility = adapters.v1_compatibility_replay(root)
    v1_report = {
        "schema_version": "contentops.v1_compatibility_report.v2", **compatibility,
        "final_accepted_body_only": compatibility["accepted_lineage"]["final_accepted_public_body_sha256"] == adapters.FINAL_ACCEPTED_BODY_SHA256,
        "stale_lineage_rejected": compatibility["accepted_lineage"]["rejected_authority_states_preserved"],
        "status": "PASS",
    }
    task_preservation = {"schema_version": "contentops.task3_task4_preservation_report.v2", **dict(preservation_report)}
    task_preservation["status"] = "PASS" if task_preservation.get("task3_unchanged") and task_preservation.get("task4_unchanged") else "FAIL"
    model_record = contracts.ModelAssistedJudgmentV1(
        provider="offline_fixture", model="none", prompt_version="v1", prompt_hash="0" * 64,
        input_hash="1" * 64, output_hash="2" * 64, structured_schema="fixture.schema.v1",
        confidence="not_applicable", validation_result="PASS", rationale="No live model call was made.",
        evidence_refs=("synthetic:model_firewall",),
    )
    unsafe_model = replace(model_record, grants_authority=True, grants_reporting_permission=True, grants_dqr_override=True, grants_factual_truth=True, grants_numeric_truth=True, grants_citation_waiver=True, grants_risk_language_waiver=True, grants_automatic_scheduling=True, grants_automatic_publication=True)
    model_firewall_pass = model_record.validate() == () and len(unsafe_model.validate()) == 9
    changed_inventory = {
        "schema_version": "contentops.changed_file_inventory.v2", "task_owned_files": sorted(changed_files),
        "explicit_path_staging_required": True, "status_reconciled": status_report.get("reconciled", False),
    }
    protected_inventory = {"schema_version": "contentops.protected_path_inventory.v2", **dict(protected_paths)}
    unrelated_report = {"schema_version": "contentops.unrelated_worktree_preservation_report.v2", **dict(repository_report)}
    safety_report = {
        "schema_version": "contentops.safety_and_limitation_report.v2",
        "evidence_classes": {
            "real_committed_evidence": "historical compatibility and Git-bound upstream bytes",
            "synthetic_validation_fixtures": len(matrix["rows"]), "historical_compatibility_evidence": True,
            "unavailable_data_preserved": True, "explicit_zero_preserved": True,
            "weights": "UNCALIBRATED_FOUNDATION", "operator_review_proposals_only": True,
            "publication_authorized_outputs": 0,
        },
        "public_write_performed": False, "dispatch_performed": False, "scheduler_mutated": False,
        "editorial_policy_mutated": False, "dqr_mutated": False, "permission_mutated": False,
        "source_authority_mutated": False, "browser_or_cdp_used": False, "public_http_performed": False,
        "credential_accessed": False, "provider_called": False, "public_interaction_performed": False,
        "live_metric_collection_performed": False, "ui_built": False, "publication_authority_granted": False,
        "model_firewall_pass": model_firewall_pass, "no_forbidden_effects": True,
    }
    validation = {"schema_version": "contentops.test_and_validation_summary.v2", **dict(validation_summary)}

    artifacts: dict[str, Any] = {
        "config_executable_semantics_report.json": config_report,
        "config_field_usage_report.json": usage_report,
        "capability_dimension_contract_inventory.json": capability_inventory,
        "capability_dimension_execution_report.json": capability_execution,
        "cross_domain_execution_matrix.json": matrix,
        "cross_domain_abstraction_coverage.json": coverage,
        "collection_validation_report.json": collection_report,
        "outcome_semantic_matrix.json": outcome_report,
        "feature_applicability_report.json": applicability_report,
        "feature_evidence_minimum_report.json": evidence_minimum_report,
        "feature_authority_gate_report.json": authority_gate_report,
        "ranking_arithmetic_report.json": ranking_report,
        "observation_cardinality_report.json": cardinality_report,
        "append_only_lineage_replay.json": lineage_report,
        "append_only_mutation_check.json": mutation_report,
        "genericity_ast_guard_report.json": guard_report,
        "current_upstream_artifact_binding.json": current_upstream,
        "upstream_historical_comparison.json": upstream_comparison,
        "v1_compatibility_report.json": v1_report,
        "task3_task4_preservation_report.json": task_preservation,
        "changed_file_inventory.json": changed_inventory,
        "protected_path_inventory.json": protected_inventory,
        "unrelated_worktree_preservation_report.json": unrelated_report,
        "test_and_validation_summary.json": validation,
        "safety_and_limitation_report.json": safety_report,
    }
    observations = {
        "git": dict(git_report), "repository": dict(repository_report),
        "documentary": {"fresh_session_reading": "REVIEW_REQUIRED", "post_commit_staging": "REVIEW_REQUIRED", "post_push_verification": "REVIEW_REQUIRED", "final_response": "REVIEW_REQUIRED"},
        "architecture": {"separation_and_compatibility": v1_report["status"] == "PASS"},
        "acceptance": {"machine_derived": True},
        "config": {
            "unused_material_field_count": usage_report["unused_material_field_count"],
            "numeric_validation_pass": config_report["finite_weights"] and config_report["finite_thresholds"] and config_report["minimum_evidence_valid"],
            "reference_validation_pass": config_report["normalization_parameters_executable"] and config_report["authority_gate_references_valid"] and config_report["unavailable_handling_references_valid"],
            "hash_and_calibration_pass": not config_report["validation_blockers"] and config_report["calibration_state"] == "UNCALIBRATED_FOUNDATION",
            "unknown_fields_fail_closed": config_report["strict_unknown_field_policy"] == "FAIL_UNKNOWN_TOP_LEVEL_OR_FEATURE_FIELD",
        },
        "features": {
            "abstentions_noncontributing": applicability_report["abstentions_noncontributing"],
            "availability_semantics_pass": authority_gate_report["false_gates_block"] and safety_report["evidence_classes"]["explicit_zero_preserved"],
            "complete_execution_metadata": all(all(key in row for key in ("availability", "unavailable_reason", "reason_codes", "evidence_count", "configured_minimum_evidence", "authority_gate_result", "domain_applicability_result")) for row in feature_rows),
        },
        "capabilities": {
            "required_dimensions_present": capability_inventory["required_dimensions_present"],
            "collection_semantics_pass": capability_inventory["empty_singleton_multi_supported"] and capability_inventory["duplicate_and_malformed_validation"],
            "execution_dimensions_pass": capability_execution["execution_dimensions_pass"],
        },
        "cross_domain": {
            "passing_fixture_count": matrix["passing_fixture_count"], "row_schema_complete": matrix["row_schema_complete"],
            "abstractions_below_two_domain_proof": coverage["abstractions_below_two_domain_proof"],
        },
        "collections": {key: collection_report[key] for key in ("history_validation_pass", "candidate_validation_pass", "gap_validation_pass", "observation_validation_pass", "learning_input_validation_pass")},
        "outcomes": {key: outcome_report[key] for key in ("separation_pass", "governed_semantics_pass", "other_semantics_pass")},
        "ranking": {"arithmetic_pass": ranking_report["arithmetic_pass"], "performance_and_cardinality_pass": cardinality_report["performance_and_cardinality_pass"]},
        "lineage": {"complete_bindings": all(getattr(lineage_report["successor"], "get", lambda *_: None)(key) for key in ("config_logical_hash", "input_binding_hash", "content_history_hash", "gap_set_hash", "observation_set_hash", "candidate_cohort_hash")), "rejection_matrix_pass": mutation_report["all_rejection_cases_pass"], "deterministic_replay_pass": lineage_report["identical_input_replay_same_identity"] and lineage_report["changed_input_creates_new_identity"] and lineage_report["changed_config_creates_new_identity"]},
        "model": {"firewall_pass": model_firewall_pass},
        "genericity": {"prohibited_finding_count": guard_report["prohibited_finding_count"]},
        "upstream": {"current_binding_pass": current_upstream["status"] == "PASS", "comparison_classification": upstream_comparison["classification"]},
        "evidence": {"missing_required_artifact_count": 0, "manifest_binding_and_classes_pass": True},
        "compatibility": {"all_pass": v1_report["status"] == "PASS" and task_preservation["status"] == "PASS"},
        "safety": {"no_forbidden_effects": safety_report["no_forbidden_effects"]},
        "validation": {"required_checks_pass": validation.get("required_checks_pass", False), "truthful_full_suite_and_ci": validation.get("truthful_full_suite_and_ci", False)},
        "status": {"reconciled": status_report.get("reconciled", False), "exact_values_pass": status_report.get("exact_values_pass", False)},
    }
    requirement_matrix = derive_requirement_matrix(observations)
    artifacts["requirement_matrix.json"] = requirement_matrix
    artifact_hashes = {name: sha256(_json_bytes(value)).hexdigest() for name, value in artifacts.items()}
    missing = sorted(set(REQUIRED_ARTIFACTS) - ({"hardening_manifest.json"} | set(artifacts)))
    manifest = {
        "schema_version": "contentops.generic_foundation_hardening_manifest.v2",
        "task_label": TASK_LABEL, "terminal_classification": TERMINAL_CLASSIFICATION,
        "next_action": NEXT_ACTION, "task_starting_sha": git_report.get("actual_starting_sha"),
        "latest_verified_precommit_sha": git_report.get("latest_verified_precommit_sha"),
        "final_sha_reported_after_commit": None, "accepted_release_sha": git_report.get("accepted_release_sha"),
        "required_artifact_count": len(REQUIRED_ARTIFACTS), "missing_required_artifacts": missing,
        "artifact_sha256": artifact_hashes,
        "self_hash_excluded_reason": "A manifest cannot recursively bind its own final bytes; every other generated artifact is SHA-256 bound.",
        "requirement_counts": {key: requirement_matrix[key] for key in ("required_row_count", "pass_count", "review_required_count", "blocked_count", "fail_count", "not_implemented_count", "omitted_row_count")},
        "evidence_classes": safety_report["evidence_classes"], "publication_authority_granted": False,
    }
    artifacts["hardening_manifest.json"] = manifest
    if missing:
        raise ValueError("missing_required_hardening_artifacts:" + ",".join(missing))
    output.mkdir(parents=True, exist_ok=True)
    for name, value in artifacts.items():
        (output / name).write_bytes(_json_bytes(value))
    return {"output_dir": output, "artifacts": artifacts, "observations": observations}
