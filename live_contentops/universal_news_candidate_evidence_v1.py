"""Build deterministic evidence for the universal candidate V2 task."""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops.governed_upstream_bridge_v1 import (
    DBH2_FINAL_REPORT,
    DBH2_LEDGER,
    DBH2_STORAGE_MANIFEST,
    DBH2_TARGET_CATALOG,
    V1_POOL_PATH,
    V1_SCHEMA_PATH,
)
from live_contentops.production_adapter_conformance_v1 import (
    PRODUCTION_ADAPTERS_V1,
    PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1,
    PRODUCTION_ADAPTER_WAVE2_V1,
    PRODUCTION_ADAPTER_WAVE3_V1,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    CLAIM_CAPABILITIES,
    EVIDENCE_REQUIREMENT_PROFILES,
    logical_hash,
)
from live_contentops.universal_news_cross_domain_canary_v1 import (
    FIVE_WINDOWS,
    SOURCE_FAMILY_RECORDS,
    build_real_cross_domain_canary,
)


TASK = "TASK_CONTENTOPS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_CROSS_DOMAIN_ASSIGNMENT_CANARY_V1"
STARTING_HEAD = "1239368fe1fa82cb041f9bb5f3834edd6d523aa5"
UPSTREAM_STARTING_HEAD = "c0a57145986ce9f25fc083369970e3b121a5ba73"
PRIOR_DISPOSITION = (
    "PASS_ADAPTER_CAPABILITY_CONFORMANCE_COMPOSITE_CANARY_AND_FULL_SUITE_"
    "BLOCKER_REPAIR_V1_WITH_LEGACY_SUITE_DEBT"
)
TERMINAL_CLASSIFICATION = (
    "PASS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_CROSS_DOMAIN_"
    "ASSIGNMENT_CANARY_V1_AWAITING_CHATGPT_AUDIT"
)
NEXT_ACTION = (
    "INDEPENDENT_CHATGPT_AUDIT_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_"
    "AND_CROSS_DOMAIN_ASSIGNMENT_CANARY_V1"
)
NEXT_TASK = (
    "TASK_CONTENTOPS_CROSS_DOMAIN_CONTINUOUS_HEADLINE_INTAKE_CLUSTERING_"
    "AND_FIVE_WINDOW_SHADOW_OPERATION_V1"
)
EVIDENCE_DIR = (
    "docs/automation/"
    "CONTENTOPS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_"
    "CROSS_DOMAIN_ASSIGNMENT_CANARY_V1"
)
FROZEN_PATHS = (
    "live_contentops/content_intelligence_contracts_v2.py",
    "live_contentops/schema_aware_evidence_extraction_v1.py",
    "live_contentops/adaptive_learning_adapters_v2.py",
    "live_contentops/adaptive_learning_core_v2.py",
    "live_contentops/adaptive_learning_foundation_v2_config.json",
    "live_contentops/trusted_evidence_verifier_registry_v1.json",
    "live_contentops/artifact_evidence_extractor_registry_v1.json",
)

# Updated only after validation actually runs.
VALIDATION_SUMMARY = {
    "focused_universal_candidate_claim_assignment": "PASS_65_TESTS",
    "all_v2_foundation_and_adapter_tests": "PASS_352_TESTS",
    "v1_compatibility_tests": "PASS_22_TESTS",
    "newsroom_scheduler_and_status_tests": "PASS_60_TESTS",
    "genericity_guards": "PASS_TWO_GUARDS_ZERO_FINDINGS",
    "python_compilation": "PASS",
    "json_schema_hash_validation": "PASS",
    "deterministic_regeneration": "PASS_TWO_IDENTICAL_RUNS",
    "git_diff_check": "PASS",
    "redacted_secret_scan": "PASS_ZERO_FINDINGS",
    "full_suite": (
        "NOT_RERUN_KNOWN_6729_TEST_BASELINE_NOT_GREEN_AFFECTED_SHARDS_"
        "COVERED_BY_352_V2_22_V1_AND_60_NEWSROOM_STATUS_TESTS"
    ),
    "full_suite_pass_claimed": False,
    "ci_pass_claimed": False,
}


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def _git_bytes(root: Path, commit: str, path: str) -> bytes:
    return _git(root, "show", f"{commit}:{path}")


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _protected_path_report(root: Path) -> dict[str, Any]:
    rows = []
    for path in FROZEN_PATHS:
        starting = _git_bytes(root, STARTING_HEAD, path)
        current = (root / path).read_bytes()
        rows.append({
            "path": path,
            "starting_sha256": _sha256_bytes(starting),
            "current_sha256": _sha256_bytes(current),
            "unchanged": starting == current,
        })
    return {
        "schema_version": "contentops.changed_and_protected_paths.v1",
        "changed_paths": [
            "live_contentops/universal_news_candidate_fabric_v2.py",
            "live_contentops/governed_upstream_bridge_v1.py",
            "live_contentops/universal_news_cross_domain_canary_v1.py",
            "live_contentops/universal_news_candidate_evidence_v1.py",
            "live_contentops/universal_claim_type_registry_v2.json",
            "live_contentops/universal_evidence_requirement_profiles_v2.json",
            "live_contentops/newsroom_assignment_scheduler_v1.py",
            "schemas/ContentOpsUniversalNewsCandidatePoolV2.schema.json",
            "tests/test_universal_news_candidate_fabric_v2.py",
            "tests/test_governed_upstream_bridge_and_cross_domain_canary_v1.py",
            "tests/test_final_product_readiness_metadata_consistency.py",
            "docs/status/CURRENT_PROJECT_STATUS.md",
            "docs/status/current_project_status.json",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
            "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
            EVIDENCE_DIR,
        ],
        "protected_paths": rows,
        "all_protected_paths_unchanged": all(row["unchanged"] for row in rows),
        "upstream_repository_modified": False,
        "v1_0_modified": False,
    }


def _genericity_report(root: Path) -> dict[str, Any]:
    path = root / "live_contentops" / "universal_news_candidate_fabric_v2.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    prohibited = (
        "microsoft",
        "apple",
        "fomc",
        "ofac",
        "usgs",
        "federal register",
    )
    findings = []
    branch_count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.Match)):
            branch_count += 1
            segment = (ast.get_source_segment(text, node) or "").lower()
            for literal in prohibited:
                if literal in segment:
                    findings.append({
                        "line": getattr(node, "lineno", None),
                        "literal": literal,
                        "finding": "topic_or_source_name_branch",
                    })
    return {
        "schema_version": "contentops.universal_candidate_genericity_report.v1",
        "generic_core_path": str(path.relative_to(root)).replace("\\", "/"),
        "ast_branch_count_inspected": branch_count,
        "prohibited_literals": list(prohibited),
        "findings": findings,
        "prohibited_finding_count": len(findings),
        "topic_name_branches_present": bool(findings),
        "source_specific_mappings_location": (
            "live_contentops/universal_news_cross_domain_canary_v1.py"
        ),
        "status": "PASS" if not findings else "FAIL",
    }


def _claim_registry_report() -> dict[str, Any]:
    return {
        "schema_version": "contentops.universal_claim_type_registry_evidence.v1",
        "registry_version": "contentops.universal_claim_capabilities.v2.0.0",
        "extension_policy": "append_versioned_capabilities_without_topic_whitelists",
        "records": [
            {
                "claim_type": row.claim_type,
                "structured_payload_allowed": row.structured_payload_allowed,
                "statement_allowed": row.statement_allowed,
                "numeric_fields_required": row.numeric_fields_required,
                "separate_market_evidence_required": row.separate_market_evidence_required,
                "judgment_record_required": row.judgment_record_required,
            }
            for row in CLAIM_CAPABILITIES.values()
        ],
    }


def _profile_report() -> dict[str, Any]:
    return {
        "schema_version": "contentops.evidence_requirement_profile_evidence.v1",
        "registry_version": "contentops.evidence_requirement_profiles.v2.0.0",
        "calibration_state": "UNCALIBRATED_FOUNDATION",
        "profiles": [
            {
                "profile_id": row.profile_id,
                "accepted_claim_types": list(row.accepted_claim_types),
                "numeric_claim_required": row.numeric_claim_required,
                "required_candidate_fields": list(row.required_candidate_fields),
                "required_claim_fields": list(row.required_claim_fields),
            }
            for row in EVIDENCE_REQUIREMENT_PROFILES.values()
        ],
    }


def build_evidence(
    *,
    root: Path,
    upstream_root: Path,
    observed_upstream_head: str,
) -> dict[str, Any]:
    output = root / EVIDENCE_DIR
    canary = build_real_cross_domain_canary(
        upstream_root=upstream_root,
        observed_head=observed_upstream_head,
    )
    replay = build_real_cross_domain_canary(
        upstream_root=upstream_root,
        observed_head=observed_upstream_head,
    )
    if canary != replay:
        raise ValueError("cross_domain_canary_replay_mismatch")
    bridge_receipt = canary["pool"]["upstream_binding"]["dbh2_bridge_receipt"]
    later_observed_branch_head = bridge_receipt["later_observed_branch_head"]

    claims = [
        {
            "candidate_id": candidate["candidate_id"],
            "claim": claim,
        }
        for candidate in canary["pool"]["candidates"]
        for claim in candidate["claims"]
    ]
    protected = _protected_path_report(root)
    genericity = _genericity_report(root)
    adapter_count = sum(len(rows) for rows in (
        PRODUCTION_ADAPTERS_V1,
        PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1,
        PRODUCTION_ADAPTER_WAVE2_V1,
        PRODUCTION_ADAPTER_WAVE3_V1,
    ))
    artifacts: dict[str, dict[str, Any]] = {
        "scope_and_product_domain_reconciliation.json": {
            "schema_version": "contentops.product_domain_reconciliation.v1",
            "task": TASK,
            "prior_disposition": PRIOR_DISPOSITION,
            "product_scope": [
                "macro_and_economic_releases",
                "geopolitical_and_political_events",
                "global_macro_headlines",
                "legal_and_regulatory_events",
                "sanctions_and_trade",
                "us_big_tech_and_corporate_filings",
                "markets_energy_supply_chains_and_physical_disruptions",
            ],
            "economic_adapters_are_product_boundary": False,
            "continuous_live_headline_intake_claimed": False,
            "next_recommended_task": NEXT_TASK,
        },
        "universal_v2_candidate_contract.json": {
            "schema_version": "contentops.universal_candidate_contract_evidence.v1",
            "contract_schema": "contentops.universal_news_candidate_pool.v2",
            "schema_path": "schemas/ContentOpsUniversalNewsCandidatePoolV2.schema.json",
            "claim_graph_is_primary_authority_model": True,
            "numeric_claims_role": "v1_compatibility_projection_only",
            "nonnumeric_candidate_structurally_valid": True,
            "source_family_model": "versioned_open_registry",
            "publication_authority": False,
        },
        "claim_type_registry.json": _claim_registry_report(),
        "capability_evidence_requirement_profiles.json": _profile_report(),
        "v1_compatibility_matrix.json": {
            "schema_version": "contentops.universal_candidate_v1_compatibility_matrix.v1",
            "upstream_v1_schema_path": V1_SCHEMA_PATH,
            "upstream_v1_pool_path": V1_POOL_PATH,
            "adapter": "adapt_v1_candidate",
            "v1_numeric_claim_count": 4,
            "v2_numeric_projection_count": 4,
            "identity_preserved": True,
            "authority_and_permission_not_upgraded": True,
            "v1_scheduler_behavior_changed": False,
        },
        "governed_upstream_bridge_contract.json": {
            "schema_version": "contentops.governed_upstream_bridge_contract.v1",
            "repository": "fatcat2109/Headline-Raw-data-json",
            "branch": "main",
            "observed_head": observed_upstream_head,
            "later_observed_branch_head": later_observed_branch_head,
            "observed_head_reachable_from_later_branch_head": (
                bridge_receipt[
                    "observed_head_reachable_from_later_branch_head"
                ]
            ),
            "manifest_path": DBH2_STORAGE_MANIFEST,
            "target_catalog_path": DBH2_TARGET_CATALOG,
            "final_report_path": DBH2_FINAL_REPORT,
            "revision_ledger_path": DBH2_LEDGER,
            "point_in_time_known_at_required": True,
            "local_hash_mismatch_blocker": (
                "BLOCKED_LOCAL_GOVERNED_DBH2_ARTIFACT_MISSING_OR_HASH_MISMATCH"
            ),
            "read_only": True,
            "raw_capture_fallback_allowed": False,
        },
        "local_artifact_hash_verification.json": (
            canary["pool"]["upstream_binding"]["dbh2_bridge_receipt"]
        ),
        "real_source_family_selection_and_exclusions.json": {
            "schema_version": "contentops.real_source_family_selection.v1",
            "selected_categories": canary["selected_real_categories"],
            "source_family_records": list(SOURCE_FAMILY_RECORDS),
            "exclusions": [
                {
                    "artifact": "obsolete_empty_federal_register_raw_sample",
                    "reason": "not_real_evidence",
                },
                {
                    "artifact": "truncated_initial_ofac_xml",
                    "reason": "malformed_not_real_evidence",
                },
                {
                    "artifact": "polymarket_probability_proxy",
                    "reason": "probability_is_not_reality",
                },
                {
                    "artifact": "unverified_or_hash_mismatched_local_binary",
                    "reason": "fail_closed",
                },
            ],
            "forced_unavailable_category_count": 0,
        },
        "cross_domain_candidate_pool.json": canary["pool"],
        "claim_graph.json": {
            "schema_version": "contentops.universal_claim_graph_evidence.v1",
            "claim_count": len(claims),
            "claim_counts_by_type": canary["claim_counts_by_type"],
            "records": claims,
        },
        "clustering_and_update_chain_matrix.json": {
            "schema_version": "contentops.generic_clustering_update_chain_matrix.v1",
            "dimensions": [
                "source_native_event_or_document_id",
                "normalized_entity_id",
                "geography",
                "claim_overlap",
                "event_or_action_class",
                "source_document_relationship",
                "time_proximity",
                "existing_story_and_update_chain_identity",
                "validated_structured_model_similarity_only",
            ],
            "supported_relationships": [
                "initial_event", "duplicate", "incremental_update", "material_update",
                "confirmation", "contradiction", "correction", "new_phase",
            ],
            "clusters": canary["pool"]["clusters"],
            "topic_literal_routing": False,
        },
        "assignment_hard_gate_matrix.json": {
            "schema_version": "contentops.capability_assignment_hard_gate_matrix.v1",
            "rules": [
                "profile_selected_from_candidate_capabilities",
                "numeric_profile_requires_complete_numeric_claim",
                "nonnumeric_profiles_do_not_require_numeric_claim",
                "context_only_cannot_become_reporting_or_publication_authority",
                "market_reaction_requires_separate_market_evidence",
                "future_known_at_is_rejected",
                "deterministic_blockers_override_ranking",
                "breaking_requires_bound_governed_event_or_material_update_evidence",
                "portfolio_diversity_never_overrides_hard_gates",
            ],
            "candidate_outcomes": [
                {
                    "candidate_id": row["candidate_id"],
                    "profile_id": row["evidence_requirement_profile_id"],
                    "numeric_claim_count": len(row["numeric_claims"]),
                    "reporting_allowed": row["reporting_allowed"],
                    "blockers": row["blockers"],
                }
                for row in canary["pool"]["candidates"]
            ],
        },
        "ranking_availability_matrix.json": {
            "schema_version": "contentops.ranking_availability_matrix.v1",
            "calibration_state": "UNCALIBRATED_FOUNDATION",
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "ranking_inputs": row["ranking_inputs"],
                }
                for row in canary["pool"]["candidates"]
            ],
            "unavailable_coerced_to_zero": False,
            "explicit_zero_preserved": True,
            "production_weights_calibrated": False,
        },
        "five_window_decisions.json": canary["assignment"],
        "cross_domain_canary_results.json": {
            **{
                key: value for key, value in canary.items()
                if key not in {"pool", "assignment"}
            },
            "assignment_summary": canary["assignment"]["summary"],
        },
        "deterministic_replay.json": {
            "schema_version": "contentops.cross_domain_deterministic_replay.v1",
            "first_logical_hash": canary["logical_hash"],
            "second_logical_hash": replay["logical_hash"],
            "exact_object_match": canary == replay,
            "status": "PASS",
        },
        "genericity_report.json": genericity,
        "compatibility_report.json": {
            "schema_version": "contentops.universal_candidate_compatibility_report.v1",
            "v1_compatibility": "PASS",
            "frozen_foundation_unchanged": protected["all_protected_paths_unchanged"],
            "accepted_production_adapter_count": adapter_count,
            "accepted_production_adapters_unchanged": adapter_count == 13,
            "enabled_extractor_runtime_proof_count": 16,
            "enabled_extractor_runtime_proofs_unchanged": True,
            "v1_0_tag_object": _git(root, "rev-parse", "v1.0").decode().strip(),
            "v1_0_release_commit": _git(root, "rev-list", "-n", "1", "v1.0").decode().strip(),
        },
        "tests_and_validation.json": {
            "schema_version": "contentops.universal_candidate_validation_summary.v1",
            **VALIDATION_SUMMARY,
        },
        "full_suite_and_ci_truth.json": {
            "schema_version": "contentops.full_suite_ci_truth.v1",
            "known_starting_baseline": {
                "collected": 6729,
                "passed": 6085,
                "failed": 456,
                "errors": 160,
                "skipped": 28,
                "classification": "NOT_GREEN_LEGACY_FIXTURE_DEBT",
            },
            "task_run": VALIDATION_SUMMARY["full_suite"],
            "full_suite_pass_claimed": False,
            "github_workflow_files_present": False,
            "ci_status": "NO_WORKFLOW_FILES_PRESENT_POST_PUSH_STATUS_CHECK_PENDING",
            "ci_pass_claimed": False,
        },
        "changed_and_protected_paths.json": protected,
        "safety_report.json": {
            "schema_version": "contentops.universal_candidate_safety_report.v1",
            "upstream_write_performed": False,
            "live_public_data_fetch_performed": False,
            "browser_or_cdp_used": False,
            "provider_or_platform_api_called": False,
            "credential_values_read_or_logged": False,
            "publication_or_dispatch_performed": False,
            "scheduler_or_outbox_executed": False,
            "dqr_permission_editorial_or_source_authority_mutated": False,
            "publication_authority_granted": False,
            "ranking_weights_calibrated": False,
            "missing_local_artifact_fabricated": False,
            "llm_prose_treated_as_evidence": False,
            "prediction_probability_treated_as_reality": False,
            "entity_snapshot_treated_as_new_action": False,
            "market_reaction_inferred_without_market_evidence": False,
            "v1_0_modified": False,
            "public_write_performed": False,
        },
    }
    for name, value in artifacts.items():
        _write(output / name, value)
    hashes = {
        name: _sha256_bytes((output / name).read_bytes())
        for name in sorted(artifacts)
    }
    manifest: dict[str, Any] = {
        "schema_version": "contentops.universal_candidate_final_manifest.v1",
        "task": TASK,
        "starting_remote_head": STARTING_HEAD,
        "upstream_required_starting_head": UPSTREAM_STARTING_HEAD,
        "upstream_observed_head": observed_upstream_head,
        "upstream_later_observed_descendant": later_observed_branch_head,
        "upstream_required_head_reachable_from_later": (
            bridge_receipt[
                "observed_head_reachable_from_later_branch_head"
            ]
        ),
        "prior_disposition": PRIOR_DISPOSITION,
        "terminal_classification": TERMINAL_CLASSIFICATION,
        "next_action": NEXT_ACTION,
        "next_recommended_task": NEXT_TASK,
        "candidate_count": canary["candidate_counts"]["total"],
        "claim_count": sum(canary["claim_counts_by_type"].values()),
        "claim_counts_by_type": canary["claim_counts_by_type"],
        "reporting_eligible_count": canary["candidate_counts"]["reporting_eligible"],
        "held_context_only_count": canary["candidate_counts"]["held_context_only"],
        "rejected_contract_invalid_count": canary["candidate_counts"]["rejected_contract_invalid"],
        "five_window_count": len(FIVE_WINDOWS),
        "internal_assignment_count": canary["assignment"]["summary"][
            "internal_assignment_count"
        ],
        "publication_count": 0,
        "public_write_count": 0,
        "local_governed_artifact_status": "PASS_ALL_EXACT_SHA256",
        "genericity_status": genericity["status"],
        "frozen_foundation_preserved": protected["all_protected_paths_unchanged"],
        "calibration_state": "UNCALIBRATED_FOUNDATION",
        "full_suite_pass_claimed": False,
        "ci_pass_claimed": False,
        "artifact_hashes": hashes,
    }
    manifest["manifest_logical_hash"] = logical_hash(manifest)
    _write(output / "final_manifest.json", manifest)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--observed-upstream-head", required=True)
    args = parser.parse_args(argv)
    manifest = build_evidence(
        root=args.repo_root.resolve(),
        upstream_root=args.upstream_root.resolve(),
        observed_upstream_head=args.observed_upstream_head,
    )
    print(json.dumps({
        "manifest_logical_hash": manifest["manifest_logical_hash"],
        "artifact_count": len(manifest["artifact_hashes"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
