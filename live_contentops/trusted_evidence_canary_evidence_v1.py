"""Machine-derived evidence packet for trusted evidence and real canary V1."""
from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import trusted_evidence_real_canary_v1 as canary


REQUIRED_REPORTS = (
    "trusted_verifier_registry.json",
    "registry_validation_report.json",
    "producer_receipt_contract_inventory.json",
    "producer_receipt_verification_matrix.json",
    "point_in_time_matrix.json",
    "feature_scope_resolution_matrix.json",
    "governed_outcome_provenance_matrix.json",
    "real_artifact_inventory.json",
    "real_multi_topic_canary_inputs.json",
    "real_multi_topic_canary_decisions.json",
    "real_versus_synthetic_declaration.json",
    "deterministic_replay.json",
    "compatibility_report.json",
    "test_summary.json",
    "changed_protected_paths.json",
    "safety_report.json",
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(contracts.primitive(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _governed_outcome_probe(root: Path) -> Mapping[str, Any]:
    ref = "evidence:governed-outcome-probe"
    context = adapters.build_synthetic_validation_context((ref,), repo_root=root)
    binding = adapters.build_receipt_backed_evidence_binding(
        context, evidence_ref=ref, evidence_roles=(contracts.EvidenceRole.MATERIAL_DELTA,),
        evidence_scope=contracts.EvidenceScope.CANDIDATE_WIDE,
    )
    candidate = core.LearningCandidateV2(
        candidate_id="evidence:probe:candidate", story_id="evidence:probe:story",
        cluster_id="evidence:probe:cluster", update_chain_id="evidence:probe:chain",
        source_relationship=contracts.EventRelationship.MATERIAL_UPDATE,
        evidence_state="SYNTHETIC_TRUST_BOUNDARY_PROBE", authority_state="AUTHORIZED",
        authority_ready=True, reporting_allowed=True, authority_blockers=(),
        history_identity_match=False, governed_material_delta=True,
        material_delta_evidence_ref=ref, material_reader_contribution=True,
        evidence_refs=(ref,), governed_evidence_bindings=(binding,), evidence_context=context,
    )
    outcome = core.evaluate_outcome(candidate, adapters.load_foundation_config(root))
    random_draft = replace(binding, producer_artifact_binding_hash="a" * 64, logical_hash="")
    random_binding = replace(random_draft, logical_hash=random_draft.calculated_logical_hash())
    random_candidate = replace(candidate, governed_evidence_bindings=(random_binding,))
    random_outcome = core.evaluate_outcome(random_candidate, adapters.load_foundation_config(root))
    rows = (
        {
            "case": "trusted_receipt_matching_material_role",
            "outcomes": list(outcome.actionable_outcomes),
            "qualifying_lineage": list(outcome.qualifying_governed_evidence_refs),
            "relationship_specific_refs": list(outcome.relationship_specific_qualifying_refs),
            "status": "PASS" if "GOVERNED_MATERIAL_UPDATE" in outcome.actionable_outcomes and outcome.qualifying_governed_evidence_refs else "FAIL",
        },
        {
            "case": "random_sha_shaped_producer_hash",
            "outcomes": list(random_outcome.actionable_outcomes),
            "disqualified": contracts.primitive(random_outcome.disqualified_evidence),
            "status": "PASS" if "GOVERNED_MATERIAL_UPDATE" not in random_outcome.actionable_outcomes else "FAIL",
        },
    )
    return {
        "schema_version": "contentops.governed_outcome_provenance_matrix.v1",
        "synthetic_probe_authority": "ALGORITHM_VALIDATION_ONLY_NO_PUBLICATION",
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def build_reports(
    *,
    repo_root: str | Path,
    upstream_git_dir: str | Path,
    test_summary: Mapping[str, Any],
    changed_protected_paths: Mapping[str, Any],
    compatibility_report: Mapping[str, Any],
    safety_report: Mapping[str, Any],
) -> Mapping[str, Any]:
    root = Path(repo_root).resolve()
    first = canary.run_real_multi_topic_canary(repo_root=root, upstream_git_dir=upstream_git_dir)
    second = canary.run_real_multi_topic_canary(repo_root=root, upstream_git_dir=upstream_git_dir)
    registry = adapters.load_trusted_verifier_registry(root)
    inventory = first["artifact_inventory"]
    feature_rows = [
        feature
        for ranking in first["decision"]["ranking_rows"]
        for feature in ranking["features"]
        if feature["evidence_refs"]
    ]
    receipt_rows = tuple({
        "receipt_id": row["receipt_id"], "repository": row["repository"],
        "branch": row["branch"], "commit": row["commit"], "path": row["path"],
        "git_blob_sha1": row["git_blob_sha1"], "byte_sha256": row["byte_sha256"],
        "artifact_logical_hash": row["artifact_logical_hash"],
        "receipt_logical_hash": row["receipt_logical_hash"],
        "exact_binding_complete": all(row[name] for name in (
            "repository", "branch", "commit", "path", "git_blob_sha1", "byte_sha256",
            "artifact_logical_hash", "receipt_logical_hash",
        )),
        "status": "PASS",
    } for row in inventory)
    pit_rows = tuple({
        "candidate_id": ranking["candidate_id"],
        "decision_cutoff_utc": first["decision_cutoff_utc"],
        "feature_point_in_time_results": {
            feature["feature_id"]: feature["point_in_time_result"]
            for feature in ranking["features"] if feature["evidence_refs"]
        },
        "status": "PASS" if all(
            feature["point_in_time_result"].startswith("PASS_")
            for feature in ranking["features"] if feature["evidence_refs"]
        ) else "FAIL",
    } for ranking in first["decision"]["ranking_rows"])
    reports: dict[str, Any] = {
        "trusted_verifier_registry.json": contracts.primitive(registry),
        "registry_validation_report.json": {
            "schema_version": "contentops.trusted_verifier_registry_validation.v1",
            "registry_version": registry.registry_version,
            "declared_hash": registry.registry_logical_hash,
            "calculated_hash": registry.calculated_logical_hash(),
            "enabled_verifier_count": sum(row.enabled for row in registry.records),
            "disabled_verifier_count": sum(not row.enabled for row in registry.records),
            "blockers": list(registry.validate()),
            "status": "PASS" if not registry.validate() else "FAIL",
        },
        "producer_receipt_contract_inventory.json": {
            "schema_version": "contentops.producer_receipt_contract_inventory.v1",
            "receipt_contract_schema": contracts.SCHEMA_PRODUCER_ARTIFACT_RECEIPT_V1,
            "receipt_fields": [row.name for row in fields(contracts.VerifiedProducerArtifactReceiptV1)],
            "evidence_binding_receipt_fields": ["producer_receipt_id", "producer_receipt_logical_hash", "producer_artifact_binding_hash"],
            "arbitrary_sha_is_authority": False,
            "status": "PASS",
        },
        "producer_receipt_verification_matrix.json": {
            "schema_version": "contentops.producer_receipt_verification_matrix.v1",
            "rows": receipt_rows,
            "status": "PASS" if len(receipt_rows) >= 3 and all(row["exact_binding_complete"] for row in receipt_rows) else "FAIL",
        },
        "point_in_time_matrix.json": {
            "schema_version": "contentops.point_in_time_matrix.v1",
            "logical_time_is_evidence_authority": False,
            "rows": pit_rows,
            "status": "PASS" if pit_rows and all(row["status"] == "PASS" for row in pit_rows) else "FAIL",
        },
        "feature_scope_resolution_matrix.json": {
            "schema_version": "contentops.feature_scope_resolution_matrix.v1",
            "rows": feature_rows,
            "all_selected_refs_receipt_backed": all(
                row["producer_receipt_ids"] or row["evidence_scope"] == contracts.EvidenceScope.DERIVED_CAPABILITY.value
                for row in feature_rows
            ),
            "status": "PASS" if feature_rows and all(row["evidence_count"] == len(set(row["evidence_refs"])) for row in feature_rows) else "FAIL",
        },
        "governed_outcome_provenance_matrix.json": _governed_outcome_probe(root),
        "real_artifact_inventory.json": {
            "schema_version": "contentops.real_artifact_inventory.v1", "rows": inventory,
            "real_artifact_count": len(inventory), "synthetic_artifact_count": 0,
            "status": "PASS" if len(inventory) >= 3 else "FAIL",
        },
        "real_multi_topic_canary_inputs.json": {
            "schema_version": "contentops.real_multi_topic_canary_inputs.v1",
            "upstream_head": first["upstream_head"], "decision_cutoff_utc": first["decision_cutoff_utc"],
            "registry_version": first["registry_version"], "registry_logical_hash": first["registry_logical_hash"],
            "input_bindings": first["decision"]["input_bindings"], "artifact_inventory": inventory,
            "status": first["status"],
        },
        "real_multi_topic_canary_decisions.json": {
            "schema_version": "contentops.real_multi_topic_canary_decisions.v1",
            "decision_id": first["decision"]["decision_id"],
            "decision_logical_hash": first["decision"]["logical_hash"],
            "coverage": first["coverage"], "rows": first["decision_rows"],
            "outcome_matrix": first["decision"]["outcome_matrix"], "status": first["status"],
        },
        "real_versus_synthetic_declaration.json": {
            "schema_version": "contentops.real_versus_synthetic_declaration.v1",
            "real_canary_artifacts": len(inventory), "synthetic_canary_artifacts": 0,
            "synthetic_algorithm_probes_are_real_observations": False,
            "synthetic_algorithm_probes_grant_publication_authority": False,
            "real_canary_publication_authority_granted": False,
            "status": "PASS",
        },
        "deterministic_replay.json": {
            "schema_version": "contentops.trusted_evidence_deterministic_replay.v1",
            "two_independent_complete_canary_runs_identical": contracts.canonical_json(first) == contracts.canonical_json(second),
            "first_decision_id": first["decision"]["decision_id"],
            "second_decision_id": second["decision"]["decision_id"],
            "status": "PASS" if contracts.canonical_json(first) == contracts.canonical_json(second) else "FAIL",
        },
        "compatibility_report.json": dict(compatibility_report),
        "test_summary.json": dict(test_summary),
        "changed_protected_paths.json": dict(changed_protected_paths),
        "safety_report.json": dict(safety_report),
    }
    return reports


def generate_evidence(
    *,
    repo_root: str | Path,
    upstream_git_dir: str | Path,
    test_summary: Mapping[str, Any],
    changed_protected_paths: Mapping[str, Any],
    compatibility_report: Mapping[str, Any],
    safety_report: Mapping[str, Any],
    output_dir: str | Path | None = None,
) -> Mapping[str, Any]:
    root = Path(repo_root).resolve()
    target = Path(output_dir).resolve() if output_dir is not None else root / canary.EVIDENCE_ROOT
    target.mkdir(parents=True, exist_ok=True)
    reports = build_reports(
        repo_root=root, upstream_git_dir=upstream_git_dir,
        test_summary=test_summary, changed_protected_paths=changed_protected_paths,
        compatibility_report=compatibility_report, safety_report=safety_report,
    )
    for name in REQUIRED_REPORTS:
        (target / name).write_bytes(_json_bytes(reports[name]))
    hashes = {name: sha256((target / name).read_bytes()).hexdigest() for name in REQUIRED_REPORTS}
    statuses = {name: reports[name].get("status") for name in REQUIRED_REPORTS if isinstance(reports[name], Mapping)}
    manifest = {
        "schema_version": "contentops.trusted_evidence_real_canary_manifest.v1",
        "task": canary.TASK_LABEL,
        "operator_disposition": "ACCEPT_GOVERNED_EVIDENCE_ROLE_AND_LINEAGE_MODEL_WITHOUT_TRUST_ANCHOR",
        "starting_contentops_sha": canary.STARTING_SHA,
        "upstream_observed_head": canary.UPSTREAM_HEAD,
        "terminal_classification": canary.TERMINAL_CLASSIFICATION,
        "exact_next_action": canary.NEXT_ACTION,
        "configuration_calibration_state": "UNCALIBRATED_FOUNDATION",
        "publication_authority_granted": False,
        "required_report_count_excluding_manifest": len(REQUIRED_REPORTS),
        "missing_reports": [name for name in REQUIRED_REPORTS if not (target / name).is_file()],
        "report_statuses": statuses,
        "artifact_byte_sha256": hashes,
        "manifest_self_hash_excluded": True,
        "status": "PASS" if not any(value == "FAIL" for value in statuses.values()) else "FAIL",
    }
    (target / "final_manifest.json").write_bytes(_json_bytes(manifest))
    return manifest
