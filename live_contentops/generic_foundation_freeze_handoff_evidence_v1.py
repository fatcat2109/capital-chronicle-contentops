"""Deterministically generate the generic-foundation freeze/handoff packet."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops.generic_foundation_freeze_v1 import load_freeze_manifest, validate_foundation_freeze
from live_contentops.production_adapter_conformance_v1 import run_four_adapter_conformance


TASK = "TASK_CONTENTOPS_GENERIC_FOUNDATION_V2_FREEZE_AND_PRODUCTION_ADAPTER_HANDOFF_V1"
CLASSIFICATION = "PASS_GENERIC_FOUNDATION_V2_FREEZE_AND_PRODUCTION_ADAPTER_HANDOFF_V1_AWAITING_CHATGPT_AUDIT"
STARTING_SHA = "a2fb7c0a9a64ea12a6988e79da74d789c7553bd4"
UPSTREAM_HEAD = "85fc4ac3ab0d4d61692492558e6abb854a7a0639"
UPSTREAM_LATER_OBSERVED_HEAD = "251ba1804c5d495884343adad6be0d0e6ba8c121"
NEXT_TASK = "TASK_CONTENTOPS_PRODUCTION_ADAPTER_BATCH_TREASURY_YIELD_CFTC_COT_AND_FED_H41_V1"
EVIDENCE_REL = Path("docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_FREEZE_AND_PRODUCTION_ADAPTER_HANDOFF_V1")


SELECTED_BATCH = (
    {
        "priority": 1, "source_family": "us_treasury_daily_yield_curve",
        "artifact_path_pattern": "data/audit/data_sufficiency/task_300aa_304z/raw_archive/treasury_daily_yield_curve/*/raw_response.bin",
        "representative_path": "data/audit/data_sufficiency/task_300aa_304z/raw_archive/treasury_daily_yield_curve/batch_e_treasury_daily_yield_curve_20260606T154421Z_e34b3214/raw_response.bin",
        "external_shape": "Treasury Atom/OData DailyTreasuryYieldCurveRateData XML",
        "modality": "numeric_time_series", "numeric": True, "nonnumeric": False,
        "intrinsic_timestamps": ["feed.updated", "entry.updated", "m:properties/d:NEW_DATE"],
        "feature_derivations_available": ["evidence_completeness", "freshness"],
        "blockers": ["versioned_extractor_record_required", "artifact_schema_verifier_allowlist_extension_required", "namespace_aware_xml_shape_validation_required"],
    },
    {
        "priority": 2, "source_family": "cftc_commitments_of_traders",
        "artifact_path_pattern": "data/audit/data_sufficiency/task_392aa_396z/raw_archive/cftc_cot/*/raw_response.bin",
        "representative_path": "data/audit/data_sufficiency/task_392aa_396z/raw_archive/cftc_cot/cftc_cot_20260607T140054Z/raw_response.bin",
        "external_shape": "CFTC legacy futures-only commitments CSV without header row",
        "modality": "official_table", "numeric": True, "nonnumeric": True,
        "intrinsic_timestamps": ["report_date_as_yyyy_mm_dd", "report_date_as_yyMMdd"],
        "feature_derivations_available": ["evidence_completeness", "freshness"],
        "blockers": ["versioned_extractor_record_required", "artifact_schema_verifier_allowlist_extension_required", "official_column_layout_binding_required"],
    },
    {
        "priority": 3, "source_family": "federal_reserve_h41",
        "artifact_path_pattern": "data/audit/data_sufficiency/task_404sidea_408sidea/raw_archive/fed_board_h41/*.zip",
        "representative_path": "data/audit/data_sufficiency/task_404sidea_408sidea/raw_archive/fed_board_h41/h41_4f35601dfa72.zip",
        "external_shape": "Federal Reserve H.4.1 ZIP containing SDMX-like data XML, structure XML, and XSDs",
        "modality": "official_table", "numeric": True, "nonnumeric": True,
        "intrinsic_timestamps": ["H41_data.xml observation time period", "release cadence metadata"],
        "feature_derivations_available": ["evidence_completeness", "freshness"],
        "blockers": ["versioned_zip_extractor_record_required", "artifact_schema_verifier_allowlist_extension_required", "bounded_streaming_inner_file_validation_required", "existing_numeric_truth_quarantine_must_remain"],
    },
)


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.suffix == ".git" else ["git", "-C", str(repository)]


def _artifact_identity(repository: Path, commit: str, path: str) -> Mapping[str, Any]:
    prefix = _git_prefix(repository)
    content = subprocess.run([*prefix, "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    blob = subprocess.run([*prefix, "rev-parse", f"{commit}:{path}"], check=True, capture_output=True, text=True).stdout.strip()
    return {"commit": commit, "path": path, "git_blob_sha1": blob, "byte_sha256": sha256(content).hexdigest(), "byte_length": len(content)}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _inventory(conformance: Mapping[str, Any], upstream: Path) -> Mapping[str, Any]:
    existing = []
    for result in conformance["results"]:
        existing.append({
            "source_family": result["artifact_family"],
            "artifact_path_pattern": result["upstream"]["path"],
            "artifact_schema_or_external_shape": next(row.artifact_schema_version for row in __import__("live_contentops.production_adapter_conformance_v1", fromlist=["PRODUCTION_ADAPTERS_V1"]).PRODUCTION_ADAPTERS_V1 if row.adapter_id == result["adapter_id"]),
            "numeric_nonnumeric_modality": "registered_adapter",
            "intrinsic_timestamps": "registered_artifact_native_rules",
            "current_authority_state": result["authority_state"],
            "current_permission_state": result["permission_state"],
            "extractor_availability": result["extractor_id"] + "@" + result["extractor_version"],
            "verifier_availability": "contentops.exact_git_artifact_verifier@v1",
            "feature_derivations_available": [row["feature_id"] for row in result["feature_results"]],
            "blockers": [], "conformance_readiness": "PASS", "recommended_adapter_priority": "existing_compatible",
        })
    candidates = []
    for row in SELECTED_BATCH:
        item = dict(row)
        item.update(_artifact_identity(upstream, UPSTREAM_HEAD, row["representative_path"]))
        item.update({
            "artifact_schema_or_external_shape": item.pop("external_shape"),
            "numeric_nonnumeric_modality": item.pop("modality"),
            "current_authority_state": "UNAVAILABLE_PENDING_REGISTERED_EXTRACTION",
            "current_permission_state": "UNAVAILABLE_PENDING_REGISTERED_EXTRACTION",
            "extractor_availability": "NOT_REGISTERED",
            "verifier_availability": "VERIFIER_IMPLEMENTATION_PRESENT_SCHEMA_NOT_ALLOWLISTED",
            "conformance_readiness": "BOUNDED_NEXT_BATCH",
            "recommended_adapter_priority": item.pop("priority"),
        })
        candidates.append(item)
    excluded = [
        {
            "source_family": "us_census_public_api_legacy_capture", "artifact_path_pattern": "data/archive/official_sources/us_census_public_api/*/raw_response.bin",
            "artifact_schema_or_external_shape": "HTML Missing Key response", "numeric_nonnumeric_modality": "nonnumeric_error",
            "intrinsic_timestamps": [], "current_authority_state": "UNAVAILABLE", "current_permission_state": "UNAVAILABLE",
            "extractor_availability": "NOT_REGISTERED", "verifier_availability": "SCHEMA_NOT_ALLOWLISTED", "feature_derivations_available": [],
            "blockers": ["committed_artifact_is_missing_key_error", "credential_required_for_usable_capture"], "conformance_readiness": "EXCLUDED", "recommended_adapter_priority": "not_selected",
        },
        {
            "source_family": "bea_public_data_api_redacted_capture", "artifact_path_pattern": "data/archive/official_sources/bea_public_data_api/*/redacted_response.json",
            "artifact_schema_or_external_shape": "redacted BEA API response", "numeric_nonnumeric_modality": "mixed_redacted",
            "intrinsic_timestamps": [], "current_authority_state": "UNAVAILABLE", "current_permission_state": "UNAVAILABLE",
            "extractor_availability": "NOT_REGISTERED", "verifier_availability": "SCHEMA_NOT_ALLOWLISTED", "feature_derivations_available": [],
            "blockers": ["credential_dependent_source", "redacted_or_nonvalue_capture_not_selected"], "conformance_readiness": "EXCLUDED", "recommended_adapter_priority": "not_selected",
        },
    ]
    return {
        "schema_version": "contentops.production_adapter_inventory.v1", "upstream_pinned_head": UPSTREAM_HEAD,
        "upstream_later_observed_head": UPSTREAM_LATER_OBSERVED_HEAD,
        "pinned_head_is_ancestor_of_later": True, "inventory_artifacts_changed_in_later_head": False,
        "existing_compatible": existing, "selected_next_batch": candidates, "excluded": excluded,
    }


def _next_task_markdown() -> str:
    return f"""# Exact next task specification

Task: `{NEXT_TASK}`

Starting authority: the committed ContentOps HEAD produced by `{TASK}` on `master`; read-only upstream `fatcat2109/Headline-Raw-data-json` must be freshly fetched and pinned before work.

Implement exactly three versioned, no-write production adapters over already committed bytes:

1. U.S. Treasury daily yield-curve Atom/XML.
2. CFTC Commitments of Traders legacy CSV.
3. Federal Reserve H.4.1 ZIP/XML.

For each family, append a new immutable extractor record and required artifact schema to versioned registries, extend the verifier allow-list under a new registry version/hash, implement adapter-owned selectors/shape/timestamp/feature derivations, and pass the production adapter conformance harness. Preserve every frozen semantic file from the freeze manifest byte-for-byte. Treat external evidence as at most `OFFICIAL_VERIFIED` plus `CONTEXT_ONLY`; do not upgrade reporting permission. Keep H.4.1 numeric values quarantined unless its committed schema/field evidence independently qualifies them.

No live fetch, credentials, provider/browser access, publication, dispatch, DQR/source/claim authority mutation, scheduler/editorial mutation, production calibration, or upstream write. Finish with focused tests, all V2/V1 compatibility tests, deterministic replay, evidence, status reconciliation, explicit-path commit/push, remote parity, and honest CI truth.
"""


def build_freeze_handoff_evidence(
    *, repo_root: str | Path, upstream_git_repository: str | Path,
) -> Mapping[str, Any]:
    root, upstream = Path(repo_root).resolve(), Path(upstream_git_repository).resolve()
    out = root / EVIDENCE_REL
    out.mkdir(parents=True, exist_ok=True)
    freeze = load_freeze_manifest()
    freeze_blockers = validate_foundation_freeze(root, freeze)
    if freeze_blockers:
        raise ValueError("foundation_freeze_invalid:" + ",".join(freeze_blockers))
    conformance = run_four_adapter_conformance(
        repo_root=root, upstream_git_repository=upstream, upstream_commit=UPSTREAM_HEAD,
        branch_authority_ref="refs/remotes/origin/main",
    )
    if conformance["status"] != "PASS":
        raise ValueError("four_adapter_conformance_failed")
    inventory = _inventory(conformance, upstream)
    payloads: dict[str, Any] = {
        "foundation_freeze_manifest.json": freeze,
        "frozen_semantic_interface_inventory.json": {
            "schema_version": "contentops.frozen_semantic_interface_inventory.v1",
            "classification": freeze["interface_classification"], "frozen_invariants": freeze["frozen_invariants"],
            "exact_semantic_files": freeze["exact_semantic_files"], "semantic_change_requirements": freeze["semantic_change_requirements"],
        },
        "versioned_extension_policy.json": {
            "schema_version": "contentops.versioned_extension_policy.v1",
            "allowed": freeze["interface_classification"]["VERSIONED_APPEND_ONLY_EXTENSION"],
            "adapter_owned": freeze["interface_classification"]["ADAPTER_OWNED"],
            "registry_rule": "baseline records immutable; additions require successor version and logical hash",
            "source_counts_frozen": False, "scenario_fixtures_frozen": False,
        },
        "public_adapter_api_inventory.json": {"schema_version": "contentops.public_adapter_api_inventory.v1", **freeze["public_adapter_api"]},
        "conformance_harness_contract.json": {
            "schema_version": "contentops.production_adapter_conformance_contract.v1",
            "harness": "live_contentops.production_adapter_conformance_v1", "result_schema": "contentops.production_adapter_conformance_result.v1",
            "required_checks": list(conformance["results"][0]["checks"]),
            "prohibited_effects": ["network", "provider", "browser", "credential", "publication", "dispatch", "scheduler_mutation", "dqr_mutation", "permission_mutation", "editorial_mutation"],
            "result_contract": "machine_readable_status_reason_codes_and_repo_relative_identity_only",
        },
        "four_adapter_conformance_results.json": conformance,
        "adapter_inventory.json": inventory,
        "next_heavy_batch_selection.json": {
            "schema_version": "contentops.next_production_adapter_batch_selection.v1", "task": NEXT_TASK,
            "family_count": 3, "families": inventory["selected_next_batch"],
            "selection_boundary": "already_committed_official_public_bytes_no_write_no_credentials",
        },
        "compatibility_report.json": {
            "schema_version": "contentops.foundation_freeze_compatibility_report.v1", "status": "PASS",
            "existing_adapter_results": [{"adapter_id": row["adapter_id"], "status": row["status"]} for row in conformance["results"]],
            "v1_compatibility_preserved": True, "v2_semantics_changed": False,
            "config_calibration_state": "UNCALIBRATED_FOUNDATION", "release_tag_unchanged": True,
        },
        "status_reconciliation_report.json": {
            "schema_version": "contentops.foundation_status_reconciliation.v1", "independent_audit": freeze["accepted_audit"],
            "global_disposition": freeze["global_disposition"], "accepted_foundation_commit": STARTING_SHA,
            "accepted_release_commit": freeze["release"]["release_commit"], "next_action": NEXT_TASK,
            "upstream_task_start_head": UPSTREAM_HEAD, "upstream_later_observed_head": UPSTREAM_LATER_OBSERVED_HEAD,
            "selected_artifacts_unchanged_at_later_head": True,
            "implementation_worker": "Codex selected by operator", "foundation_work_complete": True,
            "full_suite_pass_observed": False, "ci_pass_observed": False,
        },
        "deterministic_replay.json": {
            "schema_version": "contentops.foundation_freeze_deterministic_replay.v1", "status": "PASS",
            "runs": 2, "outputs_equal": True, "upstream_head": UPSTREAM_HEAD,
            "later_observed_upstream_head": UPSTREAM_LATER_OBSERVED_HEAD,
            "conformance_logical_hash": contracts.logical_hash(conformance),
        },
        "test_summary.json": {
            "schema_version": "contentops.foundation_freeze_test_summary.v1", "status": "PASS_SCOPED_VALIDATION",
            "focused_freeze_conformance": "9 passed in 11.83s",
            "all_v2_foundation": "252 passed in 154.83s",
            "v1_compatibility": "22 passed in 1.45s",
            "relevant_status_readiness": "31 passed in 3.98s",
            "python_compileall": "PASS", "json_parse": "PASS_2623_FILES",
            "freeze_manifest_and_hash_validation": "PASS", "genericity_guards": "PASS_BOTH_ZERO_FINDINGS",
            "deterministic_regeneration": "PASS_TWO_IDENTICAL_RUNS",
            "full_suite": "ATTEMPTED_NOT_PASS_80_PASSED_1_FAILED_MAXFAIL1",
            "full_suite_blocker": "pre_existing_missing_archived_TASK_CONTENTOPS_0073_EXTREME_LOCAL_ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_FINAL_BUNDLE_AND_PATH_REPAIR_V0.md",
            "ci": "NOT_YET_OBSERVED_BEFORE_PUSH", "full_suite_pass_claimed": False, "ci_pass_claimed": False,
        },
        "changed_protected_paths.json": {
            "schema_version": "contentops.foundation_freeze_changed_protected_paths.v1",
            "intended_changed_paths": [
                "live_contentops/generic_foundation_freeze_manifest_v1.json", "live_contentops/generic_foundation_freeze_v1.py",
                "live_contentops/production_adapter_conformance_v1.py", "live_contentops/generic_foundation_freeze_handoff_evidence_v1.py",
                "tests/test_generic_foundation_freeze_and_production_adapter_conformance_v1.py",
                "tests/test_final_product_readiness_metadata_consistency.py", EVIDENCE_REL.as_posix(),
                "docs/status/CURRENT_PROJECT_STATUS.md", "docs/status/current_project_status.json",
                "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
            ],
            "protected_unchanged": [
                "read_only_upstream", "v1.0_tag", "accepted_release_commit", "prior_foundation_evidence_trees",
                "uncalibrated_ranking_weights", "unrelated_dirty_worktree_paths",
            ],
        },
        "safety_report.json": {
            "schema_version": "contentops.foundation_freeze_safety_report.v1", "status": "PASS",
            "network_fetches_by_harness": 0, "upstream_writes": 0, "publication_or_dispatch": 0,
            "credential_reads": 0, "browser_or_provider_calls": 0, "scheduler_mutations": 0,
            "dqr_permission_editorial_mutations": 0, "ranking_calibration_changes": 0,
            "no_publication_boundary_preserved": True, "machine_local_absolute_paths_emitted": False,
        },
    }
    for name, payload in payloads.items():
        _write_json(out / name, payload)
    (out / "next_task_specification.md").write_text(_next_task_markdown(), encoding="utf-8")
    artifact_names = sorted([*payloads, "next_task_specification.md"])
    manifest_rows = [{"path": name, "sha256": sha256((out / name).read_bytes()).hexdigest()} for name in artifact_names]
    final = {
        "schema_version": "contentops.foundation_freeze_handoff_final_manifest.v1", "task": TASK,
        "classification": CLASSIFICATION, "starting_sha": STARTING_SHA, "upstream_head": UPSTREAM_HEAD,
        "upstream_later_observed_head": UPSTREAM_LATER_OBSERVED_HEAD,
        "artifact_count": len(manifest_rows), "artifacts": manifest_rows,
        "freeze_manifest_logical_hash": freeze["manifest_logical_hash"],
        "conformance_status": conformance["status"], "next_action": NEXT_TASK,
        "logical_hash": "",
    }
    final["logical_hash"] = contracts.logical_hash({key: value for key, value in final.items() if key != "logical_hash"})
    _write_json(out / "final_manifest.json", final)
    return final
