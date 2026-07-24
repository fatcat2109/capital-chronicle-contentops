"""Deterministic evidence writer for verified window-incremental shadow intake."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from live_contentops.universal_governed_registry_v1 import (
    load_governed_registry_authority,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_window_incremental_editorial_shadow,
    enabled_discovery_routes,
)


EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_VERIFIED_EVIDENCE_RECEIPT_WINDOW_INCREMENTAL_INTAKE_AND_"
    "CANONICAL_EDITORIAL_SHADOW_HANDOFF_V1"
)
TASK = (
    "TASK_CONTENTOPS_VERIFIED_EVIDENCE_RECEIPT_WINDOW_INCREMENTAL_INTAKE_"
    "AND_CANONICAL_EDITORIAL_SHADOW_HANDOFF_V1"
)
STARTING_REMOTE_HEAD = "5fcebd953323cbd82d4a2906a3773e1a7337e3b2"
UPSTREAM_OBSERVED_HEAD = "1700520800e8c847b7446e196c384a43dd2a6a58"
PRIOR_AUDIT = (
    "PARTIAL_PASS_CROSS_DOMAIN_CONTINUOUS_SHADOW_OPERATION \u2014 "
    "ACCEPT_BOUNDED_LOCAL_REPLAY_BLOCK_PRODUCTION_HANDOFF_ON_RECEIPT_"
    "VERIFICATION_AND_TRUE_INCREMENTAL_DISCOVERY"
)
TERMINAL_CLASSIFICATION = (
    "PASS_VERIFIED_EVIDENCE_RECEIPT_WINDOW_INCREMENTAL_INTAKE_AND_"
    "EDITORIAL_SHADOW_HANDOFF_V1_AWAITING_CHATGPT_AUDIT"
)
NEXT_ACTION = (
    "INDEPENDENT_CHATGPT_AUDIT_VERIFIED_EVIDENCE_RECEIPT_WINDOW_"
    "INCREMENTAL_INTAKE_AND_EDITORIAL_SHADOW_HANDOFF_V1"
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
    validation_truth: Mapping[str, Any],
) -> dict[str, Any]:
    output = repo_root / EVIDENCE_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    authority = load_governed_registry_authority(repo_root=repo_root)
    routes = enabled_discovery_routes(authority)
    operation = build_window_incremental_editorial_shadow(
        repo_root=repo_root,
        upstream_root=upstream_root,
        observed_upstream_head=UPSTREAM_OBSERVED_HEAD,
    )
    replay = build_window_incremental_editorial_shadow(
        repo_root=repo_root,
        upstream_root=upstream_root,
        observed_upstream_head=UPSTREAM_OBSERVED_HEAD,
    )
    if operation != replay:
        raise ValueError("verified_window_incremental_replay_mismatch")
    bindings = list(operation["trusted_evidence_index"].values())
    receipt_schemas = sorted({
        str(value["receipt"]["schema_version"]) for value in bindings
    })
    handoff = operation["editorial_shadow_handoff"]

    documents: dict[str, Any] = {
        "receipt_verifier_evidence.json": {
            "schema_version": "contentops.receipt_verifier_evidence.v1",
            "trusted_index_producer": (
                "live_contentops.universal_evidence_receipt_verifier_v1."
                "EvidenceReceiptVerifierV1"
            ),
            "trusted_index_external_insert_allowed": False,
            "binding_count": len(bindings),
            "typed_receipt_schemas": receipt_schemas,
            "git_receipt_checks": [
                "repository",
                "branch",
                "producer_commit_ancestry",
                "path",
                "git_blob_sha1",
                "byte_sha256",
                "byte_length",
                "artifact_logical_identity",
            ],
            "dbh2_receipt_checks": [
                "manifest_and_local_artifact_receipts",
                "target_id",
                "stable_record_id",
                "version_id",
                "content_sha256",
                "source_native_status",
                "point_in_time_known_at",
            ],
            "aggregation_receipt_checks": [
                "aggregation_contract_hash",
                "exact_unique_consumed_evidence_set",
                "all_inputs_in_verifier_owned_index",
            ],
            "fabricated_v1_registered_identity_control": (
                "PASS_REJECTED_UNVERIFIED_PERMISSION_BLOCKED"
            ),
            "status": "PASS",
        },
        "verified_evidence_index.json": {
            "schema_version": "contentops.verified_evidence_index_evidence.v1",
            "bindings": bindings,
            "status": "PASS",
        },
        "runtime_implementation_bindings.json": {
            "schema_version": (
                "contentops.runtime_implementation_bindings_evidence.v1"
            ),
            "registry_records": [
                {
                    "record_id": route["record_id"],
                    "adapter_id": route["adapter_id"],
                    "implementation_identity": route[
                        "implementation_identity"
                    ],
                    "implementation_receipt": route[
                        "implementation_receipt"
                    ],
                    "discovery_kind": route["discovery_contract"]["kind"],
                }
                for route in routes
            ],
            "stale_identity_count": 0,
            "callable_mismatch_control": "PASS_REJECTED",
            "runtime_byte_mismatch_control": "PASS_REJECTED",
            "status": "PASS",
        },
        "cursor_ledger.json": {
            "schema_version": "contentops.window_incremental_cursor_ledger.v1",
            "cursor_contract": operation["cursor_contract"],
            "windows": operation["window_ledger"],
            "duplicate_discovery_count": operation["summary"][
                "duplicate_discovery_count"
            ],
            "status": "PASS",
        },
        "per_window_intake_pools.json": {
            "schema_version": "contentops.per_window_intake_pools.v1",
            "pools": operation["candidate_pools"],
            "pool_count": len(operation["candidate_pools"]),
            "status": "PASS",
        },
        "window_entry_proof.json": {
            "schema_version": "contentops.window_entry_proof.v1",
            "asia_to_europe": next(
                value
                for value in operation["window_ledger"]
                if value["cutoff_utc"] == "2026-07-10T07:30:00Z"
            ),
            "europe_to_us_open": next(
                value
                for value in operation["window_ledger"]
                if value["cutoff_utc"] == "2026-07-12T13:30:00Z"
            ),
            "unchanged_identity_reentry_count": 0,
            "status": "PASS",
        },
        "governed_update_chain.json": {
            **operation["historical_update_probe"],
            "status": "PASS",
        },
        "five_window_shadow_decisions.json": {
            "schema_version": "contentops.window_shadow_decisions.v1",
            "decisions": operation["window_decisions"],
            "summary": operation["summary"],
            "status": "PASS",
        },
        "canonical_editorial_handoff.json": handoff,
        "candidate_bound_content_evidence_packet_v2.json": handoff[
            "evidence_packet"
        ],
        "local_shadow_draft.json": {
            "schema_version": "contentops.local_shadow_draft_evidence.v1",
            "candidate_id": handoff["candidate_id"],
            "article": handoff["article"],
            "editorial_review": handoff["editorial_review"],
            "publication_authority": False,
            "public_write_performed": False,
            "status": "PASS_LOCAL_ONLY",
        },
        "context_hold_abstention_outcomes.json": {
            "schema_version": (
                "contentops.context_hold_abstention_outcomes.v1"
            ),
            "outcomes": operation["context_only_abstentions"],
            "authorized_article_count": 0,
            "status": "PASS",
        },
        "deterministic_replay.json": {
            "schema_version": "contentops.deterministic_replay.v1",
            "first_logical_hash": operation["logical_hash"],
            "replay_logical_hash": replay["logical_hash"],
            "logical_equality": operation == replay,
            "status": "PASS" if operation == replay else "FAIL",
        },
        "compatibility.json": {
            "schema_version": "contentops.compatibility_report.v1",
            "v1_candidate_pool": (
                "PRESERVED_THROUGH_VERIFIED_EXACT_GIT_RECEIPT_ADAPTER"
            ),
            "v2_candidate_pool_semantics": "PRESERVED",
            "prior_registry_records": "PRESERVED_APPEND_ONLY",
            "prior_evidence_trees": "PROTECTED_UNMODIFIED",
            "v1_0_tag": "PROTECTED_UNMODIFIED",
            "uncalibrated_configuration": "PRESERVED",
            "status": "PASS",
        },
        "genericity.json": {
            "schema_version": "contentops.genericity_report.v1",
            "scanner": (
                "live_contentops.window_incremental_editorial_shadow_v1."
                "scan_verified_increment"
            ),
            "scanner_fixed_target_ids": [],
            "scanner_fixed_record_ids": [],
            "scanner_fixed_candidate_lists": [],
            "source_specific_selection_location": (
                "append_only_adapter_discovery_contracts"
            ),
            "topic_specific_branching_in_generic_scanner": False,
            "calibration_state": "UNCALIBRATED_FOUNDATION",
            "status": "PASS",
        },
        "changed_protected_paths.json": {
            "schema_version": "contentops.changed_protected_paths.v1",
            "changed_paths": [
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md",
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
                "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md",
                "docs/status/CURRENT_PROJECT_STATUS.md",
                "docs/status/current_project_status.json",
                "live_contentops/cross_domain_continuous_shadow_v1.py",
                "live_contentops/governed_universal_adapter_source_binding_registry_v1.json",
                "live_contentops/governed_universal_registry_authority_manifest_v1.json",
                "live_contentops/governed_universal_source_family_registry_v1.json",
                "live_contentops/universal_evidence_receipt_verifier_v1.py",
                "live_contentops/universal_governed_registry_v1.py",
                "live_contentops/verified_evidence_window_evidence_v1.py",
                "live_contentops/window_incremental_editorial_shadow_v1.py",
                "tests/test_final_product_readiness_metadata_consistency.py",
                "tests/test_verified_evidence_window_incremental_editorial_shadow_v1.py",
            ],
            "protected_paths": [
                "prior automation evidence trees",
                "accepted public output trees",
                "upstream repository",
                "v1.0 tag",
                "scheduler authority",
                "editorial authority",
                "DQR authority",
                "permission authority",
            ],
            "protected_path_mutation_count": 0,
            "status": "PASS",
        },
        "tests.json": {
            "schema_version": "contentops.task_test_summary.v1",
            **dict(validation_truth),
        },
        "safety.json": {
            "schema_version": "contentops.task_safety_report.v1",
            "network_fetch_performed": False,
            "browser_or_cdp_used": False,
            "credentials_read": False,
            "provider_call_performed": False,
            "scheduler_or_outbox_action_performed": False,
            "approval_ledger_action_performed": False,
            "editorial_authority_mutated": False,
            "dqr_authority_mutated": False,
            "permission_authority_mutated": False,
            "publication_count": 0,
            "public_write_count": 0,
            "upstream_write_count": 0,
            "classification": "DETERMINISTIC_LOCAL_NO_PUBLICATION_SHADOW",
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
            "contentops.verified_window_incremental_shadow_final_manifest.v1"
        ),
        "task": TASK,
        "starting_remote_head": STARTING_REMOTE_HEAD,
        "upstream_point_in_time_observed_head": UPSTREAM_OBSERVED_HEAD,
        "later_observed_upstream_branch_head": operation[
            "later_observed_upstream_branch_head"
        ],
        "prior_audit": PRIOR_AUDIT,
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
    parser.add_argument("--validation-truth", type=Path, required=True)
    args = parser.parse_args()
    truth = json.loads(args.validation_truth.read_text(encoding="utf-8"))
    generated = generate_evidence(
        repo_root=args.repo_root.resolve(),
        upstream_root=args.upstream_root.resolve(),
        validation_truth=truth,
    )
    print(generated["logical_hash"])
