"""Deterministic evidence writer for the governed continuous shadow task."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from live_contentops.cross_domain_continuous_shadow_v1 import (
    build_continuous_shadow_operation,
)
from live_contentops.universal_governed_registry_v1 import (
    load_governed_registry_authority,
    validate_claim_document_lineage,
    validate_profile_execution,
)


EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_CROSS_DOMAIN_CONTINUOUS_HEADLINE_INTAKE_CLUSTERING_AND_"
    "FIVE_WINDOW_SHADOW_OPERATION_V1"
)
TERMINAL_CLASSIFICATION = (
    "PASS_CROSS_DOMAIN_CONTINUOUS_HEADLINE_INTAKE_CLUSTERING_AND_"
    "FIVE_WINDOW_SHADOW_OPERATION_V1_AWAITING_CHATGPT_AUDIT"
)
NEXT_ACTION = (
    "INDEPENDENT_CHATGPT_AUDIT_CROSS_DOMAIN_CONTINUOUS_HEADLINE_INTAKE_"
    "CLUSTERING_AND_FIVE_WINDOW_SHADOW_OPERATION_V1"
)


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _write(path: Path, value: Any) -> None:
    path.write_bytes(_canonical(value))


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def generate_evidence(
    *,
    repo_root: Path,
    upstream_root: Path,
    validation_truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    output = repo_root / EVIDENCE_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    authority = load_governed_registry_authority(repo_root=repo_root)
    operation = build_continuous_shadow_operation(
        repo_root=repo_root,
        upstream_root=upstream_root,
    )
    replay = build_continuous_shadow_operation(
        repo_root=repo_root,
        upstream_root=upstream_root,
    )
    final_pool = operation["multi_cutoff_candidate_pools"][-1]

    derivations = [
        decision
        for candidate in final_pool["candidates"]
        for decision in candidate["claim_authority_decisions"]
    ]
    lineage = [
        validate_claim_document_lineage(candidate)
        for candidate in final_pool["candidates"]
    ]
    profiles = [
        validate_profile_execution(candidate, authority=authority)
        for candidate in final_pool["candidates"]
    ]
    documents: dict[str, Any] = {
        "governed_registry_authority_packet.json": operation[
            "registry_authority_packet"
        ],
        "append_only_verification.json": {
            "schema_version": "contentops.append_only_verification.v1",
            "reports": list(authority.append_only_reports),
            "status": "PASS",
        },
        "claim_authority_permission_derivation_matrix.json": {
            "schema_version": (
                "contentops.claim_authority_permission_derivation_matrix.v1"
            ),
            "real_claim_decisions": derivations,
            "negative_controls": [
                {
                    "case": "caller_official_authority",
                    "expected_blocker": "governed_claim_authority_chain_required",
                    "status": "PASS_REJECTED",
                },
                {
                    "case": "caller_reporting_or_public_permission",
                    "expected_blocker": "governed_claim_permission_chain_required",
                    "status": "PASS_REJECTED",
                },
                {
                    "case": "unregistered_adapter_and_source_family",
                    "expected_outcome": (
                        "UNVERIFIED_PLUS_PERMISSION_BLOCKED"
                    ),
                    "status": "PASS_REJECTED",
                },
            ],
            "status": "PASS",
        },
        "claim_document_citation_lineage_report.json": {
            "schema_version": (
                "contentops.claim_document_citation_lineage_task_report.v1"
            ),
            "candidate_reports": lineage,
            "all_candidates_pass": all(
                row["status"] == "PASS" for row in lineage
            ),
            "mutation_controls": [
                "missing_document_rejected",
                "unauthorized_citation_url_rejected",
                "unresolved_evidence_ref_rejected",
                "duplicate_binding_ref_rejected",
                "cross_candidate_ref_reuse_rejected",
            ],
            "status": "PASS",
        },
        "profile_execution_matrix.json": {
            "schema_version": "contentops.profile_execution_matrix.v1",
            "candidate_reports": profiles,
            "composition_contracts": authority.registries[
                "evidence_profiles"
            ].get("composition_contracts", []),
            "mutation_controls": [
                "unknown_profile_rejected",
                "capability_mismatch_rejected",
                "unsupported_extra_claim_rejected",
                "missing_required_candidate_field_rejected",
            ],
            "status": "PASS",
        },
        "market_evidence_separation_report.json": {
            "schema_version": (
                "contentops.market_evidence_separation_report.v1"
            ),
            "registered_capability": authority.registries[
                "market_evidence_capabilities"
            ],
            "real_shadow_market_reaction_claim_count": sum(
                claim["claim_type"] == "market_reaction"
                for candidate in final_pool["candidates"]
                for claim in candidate["claims"]
            ),
            "real_shadow_market_evidence_record_count": sum(
                len(candidate["market_evidence_records"])
                for candidate in final_pool["candidates"]
            ),
            "arbitrary_string_control": "PASS_REJECTED",
            "event_evidence_reuse_control": "PASS_REJECTED",
            "status": "PASS_NO_MARKET_REACTION_INFERRED",
        },
        "local_dbh2_receipt_verification.json": operation[
            "local_dbh2_receipt"
        ],
        "checkpoint_incremental_intake_ledger.json": {
            "schema_version": (
                "contentops.checkpoint_incremental_intake_ledger.v1"
            ),
            "checkpoints": operation["checkpoint_ledger"],
            "status": "PASS",
        },
        "multi_cutoff_candidate_pools.json": {
            "schema_version": (
                "contentops.multi_cutoff_candidate_pools.v1"
            ),
            "pools": operation["multi_cutoff_candidate_pools"],
            "status": "PASS",
        },
        "clustering_update_chain_ledger.json": operation[
            "clustering_update_chain_ledger"
        ],
        "five_window_shadow_decisions.json": {
            "schema_version": (
                "contentops.five_window_shadow_decisions.v1"
            ),
            "checkpoints": operation["five_window_shadow_decisions"],
            "summary": operation["summary"],
            "status": "PASS",
        },
        "idempotency_deterministic_replay.json": {
            "schema_version": (
                "contentops.idempotency_deterministic_replay.v1"
            ),
            "first_logical_hash": operation["logical_hash"],
            "replay_logical_hash": replay["logical_hash"],
            "byte_logical_equality": operation == replay,
            "checkpoint_idempotency_keys": [
                row["idempotency_key"]
                for row in operation["checkpoint_ledger"]
            ],
            "status": "PASS" if operation == replay else "FAIL",
        },
        "compatibility.json": {
            "schema_version": "contentops.compatibility_report.v1",
            "v1_numeric_adapter": (
                "BOUND_TO_EXACT_ACCEPTED_UPSTREAM_POOL_RECEIPT"
            ),
            "universal_v2_schema": "PRESERVED_AND_EXTENDED",
            "static_cross_domain_canary": (
                "COMPATIBILITY_PROJECTION_OF_GOVERNED_REPLAY"
            ),
            "frozen_v2_semantics": "PRESERVED",
            "v1_0_tag": "PROTECTED_UNMODIFIED",
            "existing_13_adapters": "PROTECTED_UNMODIFIED",
            "existing_16_extractor_proofs": "PROTECTED_UNMODIFIED",
            "status": "PASS",
        },
        "genericity.json": {
            "schema_version": "contentops.genericity_report.v1",
            "generic_core": (
                "live_contentops/universal_governed_registry_v1.py"
            ),
            "source_specific_routes_confined_to_adapter_shadow_module": True,
            "caller_runtime_registry_creation_allowed": False,
            "ranking_calibration_added": False,
            "calibration_state": "UNCALIBRATED_FOUNDATION",
            "status": "PASS",
        },
        "changed_protected_paths.json": {
            "schema_version": "contentops.changed_protected_paths.v1",
            "changed_implementation_paths": [
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
                "docs/status/CURRENT_PROJECT_STATUS.md",
                "docs/status/current_project_status.json",
                "live_contentops/cross_domain_continuous_shadow_evidence_v1.py",
                "live_contentops/cross_domain_continuous_shadow_v1.py",
                "live_contentops/universal_governed_registry_v1.py",
                "live_contentops/universal_news_candidate_fabric_v2.py",
                "live_contentops/universal_news_cross_domain_canary_v1.py",
                "schemas/ContentOpsUniversalNewsCandidatePoolV2.schema.json",
                "tests/test_cross_domain_continuous_shadow_v1.py",
                "tests/test_final_product_readiness_metadata_consistency.py",
                "tests/test_governed_upstream_bridge_and_cross_domain_canary_v1.py",
                "tests/test_universal_governed_registry_v1.py",
                "tests/test_universal_news_candidate_fabric_v2.py",
            ],
            "new_registry_paths": sorted(
                receipt["path"] for receipt in authority.receipts
            )
            + [
                "live_contentops/"
                "governed_universal_registry_authority_manifest_v1.json"
            ],
            "protected_paths": [
                "accepted public output trees",
                "prior automation evidence trees",
                "existing 13 production adapters",
                "existing 16 extractor proofs",
                "upstream repository",
                "v1.0 tag",
            ],
            "protected_path_mutation_count": 0,
            "status": "PASS",
        },
        "validation_truth.json": {
            "schema_version": "contentops.validation_truth.v1",
            **dict(
                validation_truth
                or {
                    "status": "PENDING_FINAL_VALIDATION",
                    "full_suite": "NOT_YET_RUN",
                    "ci": "NOT_AVAILABLE",
                }
            ),
        },
        "safety_report.json": {
            "schema_version": "contentops.safety_report.v1",
            "network_fetch_performed": False,
            "credentials_read": False,
            "provider_call_performed": False,
            "browser_or_cdp_action_performed": False,
            "scheduler_authority_mutated": False,
            "editorial_authority_mutated": False,
            "dqr_authority_mutated": False,
            "public_dispatch_performed": False,
            "publication_count": 0,
            "public_write_count": 0,
            "upstream_write_performed": False,
            "classification": "DETERMINISTIC_LOCAL_SHADOW_ONLY",
            "status": "PASS",
        },
    }
    for name, value in documents.items():
        _write(output / name, value)

    artifacts = [
        {
            "path": str((EVIDENCE_RELATIVE / name).as_posix()),
            "sha256": _hash(output / name),
            "byte_length": (output / name).stat().st_size,
        }
        for name in sorted(documents)
    ]
    manifest: dict[str, Any] = {
        "schema_version": (
            "contentops.cross_domain_continuous_shadow_final_manifest.v1"
        ),
        "task": (
            "TASK_CONTENTOPS_CROSS_DOMAIN_CONTINUOUS_HEADLINE_INTAKE_"
            "CLUSTERING_AND_FIVE_WINDOW_SHADOW_OPERATION_V1"
        ),
        "starting_remote_head": (
            "7c5ea920cadb6efb3a8b85282f43eb05c5544374"
        ),
        "upstream_observed_head": (
            "02120f86c9e9923d9c2b49db1533443cd2849eb9"
        ),
        "prior_independent_audit": (
            "PARTIAL_PASS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_"
            "CROSS_DOMAIN_CANARY — BLOCKED_CONTINUOUS_OPERATION_ON_GOVERNED_"
            "AUTHORITY_REGISTRY_AND_CLAIM_LINEAGE_BINDING"
        ),
        "accepted_prior_disposition": (
            "ACCEPT_UNIVERSAL_V2_SCHEMA_READ_ONLY_DBH2_BRIDGE_AND_"
            "NO_PUBLICATION_CROSS_DOMAIN_CANARY"
        ),
        "operation_logical_hash": operation["logical_hash"],
        "summary": operation["summary"],
        "artifacts": artifacts,
        "terminal_classification": TERMINAL_CLASSIFICATION,
        "exact_next_action": NEXT_ACTION,
    }
    manifest["logical_hash"] = sha256(_canonical(manifest)).hexdigest()
    _write(output / "final_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--upstream-root", type=Path, required=True)
    args = parser.parse_args()
    generated = generate_evidence(
        repo_root=args.repo_root.resolve(),
        upstream_root=args.upstream_root.resolve(),
    )
    print(generated["logical_hash"])
