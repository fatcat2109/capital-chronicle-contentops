"""Deterministic registry-to-runtime coverage audit for production adapters."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from live_contentops import content_intelligence_contracts_v2 as contracts


SCHEMA_VERSION = "contentops.production_adapter_contract_coverage.v2"
STARTING_AUTHORITY_SHA = "a00a702dc97c2485852ab82a70707940ed8b2083"

DOCUMENTARY_NON_RUNTIME_RECORDS = frozenset({
    ("contentops.disabled_legacy_extractor", "v1"),
})

_FREEZE_EVIDENCE = {
    "accepted_commit": "c0ace89f807161ad9f5e79d7f72bb7b79cfb34d9",
    "path": "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_FREEZE_AND_PRODUCTION_ADAPTER_HANDOFF_V1/final_manifest.json",
    "logical_hash_field": "logical_hash",
    "logical_hash": "d7aafa550ac2d746d466f82caabd3fb4375ad7622e834f3a48aa6a5074834ec8",
}
_WAVE1_EVIDENCE = {
    "accepted_commit": "ce56a57ced0a8adad9bad2deb2d3bd6dab0976d0",
    "path": "docs/automation/CONTENTOPS_PRODUCTION_ADAPTER_BATCH_TREASURY_YIELD_CFTC_COT_AND_FED_H41_V1/final_manifest.json",
    "logical_hash_field": "manifest_logical_hash",
    "logical_hash": "4c50fa522f866d8f3254884499b31ed8aae3ec949e3b580f1ba6a1ba4e6be818",
}
_WAVE2_EVIDENCE = {
    "accepted_commit": "607a767154e415ea7af393be57eae030185428af",
    "path": "docs/automation/CONTENTOPS_PRODUCTION_ADAPTER_WAVE_2_OFFICIAL_COMMITTED_ARTIFACTS_V1/final_manifest.json",
    "logical_hash_field": "manifest_logical_hash",
    "logical_hash": "f6e5b1e3994bfce98956ef48644de48724ed8435a25b182452d8a9f6c957d354",
}
_WAVE3_EVIDENCE = {
    "accepted_commit": STARTING_AUTHORITY_SHA,
    "path": "docs/automation/CONTENTOPS_PRODUCTION_ADAPTER_WAVE_3_OFFICIAL_ARTIFACTS_AND_WAVE_2_CONTRACT_COVERAGE_REPAIR_V1/final_manifest.json",
    "logical_hash_field": "manifest_logical_hash",
    "logical_hash": "6e7fb2f09d9283c10bbfaa7494ef33510e1210daf13943785d354e320dfffc8f",
}


def _proof(record_hash: str, runtime_callable: str, accepted_evidence: Mapping[str, str]) -> Mapping[str, Any]:
    return {
        "record_logical_hash": record_hash,
        "runtime_callable": runtime_callable,
        "accepted_evidence": dict(accepted_evidence),
    }


_BASE_RUNTIME = "live_contentops.schema_aware_evidence_extraction_v1.extract_artifact_evidence"
_BATCH_RUNTIME = "live_contentops.production_evidence_adapters_batch_v1.extract_production_artifact_evidence"
_WAVE2_RUNTIME = "live_contentops.production_evidence_adapters_wave2_v1.extract_wave2_artifact_evidence"
_WAVE3_RUNTIME = "live_contentops.production_evidence_adapters_wave3_v1.extract_wave3_artifact_evidence"

# Exact immutable proof per enabled extractor record.  No record is accepted by
# family membership or a historical blanket allowlist.
RUNTIME_IMPLEMENTATION_PROOFS: Mapping[tuple[str, str], Mapping[str, Any]] = {
    ("contentops.bls_series_observation_extractor", "v1"): _proof("7b75e1b7592465c25a0938b06764f477f23b35ed6e80ab6e50ce6eefc219c666", _BASE_RUNTIME, _FREEZE_EVIDENCE),
    ("contentops.treasury_auction_announcement_extractor", "v1"): _proof("fd60a28d38820f9c8d01e97fbb2c4e4fa164d849ad74167dd96beaf388c75457", _BASE_RUNTIME, _FREEZE_EVIDENCE),
    ("contentops.nyfed_reference_rate_extractor", "v1"): _proof("890e325a6f17d80b0b95cb80c74bff2ee4474bf2270d49b6afbdd15df1c7056f", _BASE_RUNTIME, _FREEZE_EVIDENCE),
    ("contentops.newsroom_candidate_extractor", "v1"): _proof("229b8e34f6d1b2ea2ed3db2175e0ae7fe03e2ac486920e1237fa92d0f4db3b6e", _BASE_RUNTIME, _FREEZE_EVIDENCE),
    ("contentops.treasury_daily_yield_curve_atom_extractor", "v1"): _proof("595d32f172e672a3e163eee7a7f9c8cc0b310821b8d9e00e174ee0093fd01f21", _BATCH_RUNTIME, _WAVE1_EVIDENCE),
    ("contentops.cftc_legacy_futures_only_cot_extractor", "v1"): _proof("9b80f2654395dbca31c124ce8b34f6a9c62506f2f3626b4796307311313d1f8b", _BATCH_RUNTIME, _WAVE1_EVIDENCE),
    ("contentops.federal_reserve_h41_zip_structure_extractor", "v1"): _proof("65a6616f904574aa5e86513ff839607779a5cceeb435801b998058166cf54189", _BATCH_RUNTIME, _WAVE1_EVIDENCE),
    ("contentops.treasury_debt_to_penny_extractor", "v1"): _proof("a05ecb9388390ec3df074ce8b2f858f688857ed84c05bb0b4d805dc3f128eb32", _WAVE2_RUNTIME, _WAVE2_EVIDENCE),
    ("contentops.bls_unemployment_series_extractor", "v1"): _proof("ccfcbb2002169291cb3075bf8d53abbae7ff53f7f5dd9c21739dbb83fad75548", _WAVE2_RUNTIME, _WAVE2_EVIDENCE),
    ("contentops.fomc_calendar_html_extractor", "v1"): _proof("2dc7f9d83c5b2020b9dba5e5e621f96a8d3e5684ad8338636fda8856c3b42a38", _WAVE2_RUNTIME, _WAVE2_EVIDENCE),
    ("contentops.treasury_debt_to_penny_extractor", "v2"): _proof("b62c6936a68899980c986f80a8abf666aee4be427bef15f77395f8f1d5ac63e9", _WAVE2_RUNTIME, _WAVE3_EVIDENCE),
    ("contentops.bls_unemployment_series_extractor", "v2"): _proof("14ef05ce47ac2da2fd08634aa0dd262172e6c8a9e0b4ff910dcdae58495c6a2f", _WAVE2_RUNTIME, _WAVE3_EVIDENCE),
    ("contentops.fomc_calendar_html_extractor", "v2"): _proof("7382dad30a77baf94c57eb00426e337813c6f7b7a6857ecfdfad761d1925810e", _WAVE2_RUNTIME, _WAVE3_EVIDENCE),
    ("contentops.treasury_tic_html_extractor", "v1"): _proof("10399b1b8c73b7bab9538450028b888f7ccd7aa2d4fa7901299cd160ddf8bc21", _WAVE3_RUNTIME, _WAVE3_EVIDENCE),
    ("contentops.usgs_earthquake_geojson_extractor", "v1"): _proof("4a44cf593ac9035910b464096c56be460f42d9c25a1d8b024386a241e2fe998a", _WAVE3_RUNTIME, _WAVE3_EVIDENCE),
    ("contentops.fhfa_hpi_html_extractor", "v1"): _proof("72a3fb2907cdcf7cbfea853f453d3cb1a4a55c42d8c333f3fd0866f2da79783b", _WAVE3_RUNTIME, _WAVE3_EVIDENCE),
}


@lru_cache(maxsize=32)
def _verify_accepted_evidence(repo_root: str, commit: str, path: str, field: str, expected: str) -> tuple[bool, str | None]:
    try:
        raw = subprocess.run(
            ["git", "-C", repo_root, "show", f"{commit}:{path}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        document = json.loads(raw)
    except (subprocess.CalledProcessError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "immutable_accepted_evidence_unavailable"
    declared = document.pop(field, None)
    if declared != expected or contracts.logical_hash(document) != expected:
        return False, "immutable_accepted_evidence_logical_hash_mismatch"
    return True, None


def validate_registry_contract_coverage(
    registry: contracts.ArtifactEvidenceExtractorRegistryV1,
    *,
    repo_root: str | Path | None = None,
) -> Mapping[str, Any]:
    """Prove every enabled declaration using its exact immutable record proof."""
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    root = str(Path(repo_root).resolve()) if repo_root is not None else None
    for record in registry.records:
        identity = (record.extractor_id, record.extractor_version)
        record_hash = contracts.logical_hash(contracts.primitive(record))
        proof = RUNTIME_IMPLEMENTATION_PROOFS.get(identity)
        if not record.enabled and identity in DOCUMENTARY_NON_RUNTIME_RECORDS:
            rows.append({
                "extractor_id": record.extractor_id,
                "extractor_version": record.extractor_version,
                "implementation_contract_id": record.implementation_contract_id,
                "classification": "EXPLICIT_DOCUMENTARY_NON_RUNTIME",
                "record_logical_hash": record_hash,
            })
            continue
        if proof is None:
            blockers.append(f"registry_contract_unclassified:{record.extractor_id}:{record.extractor_version}")
            rows.append({
                "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
                "classification": "UNCLASSIFIED", "record_logical_hash": record_hash,
            })
            continue

        record_hash_ok = record_hash == proof["record_logical_hash"]
        implementation_id_ok = record.implementation_contract_id == f"{record.extractor_id}.{record.extractor_version}"
        evidence_ok, evidence_reason = True, None
        evidence = proof["accepted_evidence"]
        if root is not None:
            evidence_ok, evidence_reason = _verify_accepted_evidence(
                root, evidence["accepted_commit"], evidence["path"],
                evidence["logical_hash_field"], evidence["logical_hash"],
            )
        if not record_hash_ok:
            blockers.append(f"registry_immutable_record_hash_mismatch:{record.extractor_id}:{record.extractor_version}")
        if not implementation_id_ok:
            blockers.append(f"registry_implementation_id_mismatch:{record.extractor_id}:{record.extractor_version}")
        if not evidence_ok:
            blockers.append(f"{evidence_reason}:{record.extractor_id}:{record.extractor_version}")
        rows.append({
            "extractor_id": record.extractor_id,
            "extractor_version": record.extractor_version,
            "implementation_contract_id": record.implementation_contract_id,
            "runtime_callable": proof["runtime_callable"],
            "classification": "RUNTIME_IMPLEMENTED_IMMUTABLY_BOUND" if record_hash_ok and implementation_id_ok and evidence_ok else "MISMATCH",
            "record_logical_hash": record_hash,
            "record_hash_verified": record_hash_ok,
            "shape_contract_id": record.shape_contract_id,
            "required_fields": list(record.required_fields),
            "timestamp_extraction_rules": dict(record.timestamp_extraction_rules),
            "authority_derivation_rule": record.authority_derivation_rule,
            "permission_derivation_rule": record.permission_derivation_rule,
            "role_derivation_rule": record.role_derivation_rule,
            "supported_evidence_roles": [role.value for role in record.supported_evidence_roles],
            "supported_feature_ids": list(record.supported_feature_ids),
            "accepted_evidence_binding": dict(evidence),
            "accepted_evidence_verified": evidence_ok if root is not None else None,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "starting_authority_sha": STARTING_AUTHORITY_SHA,
        "registry_version": registry.registry_version,
        "status": "PASS" if not blockers else "FAIL",
        "record_count": len(rows),
        "enabled_runtime_record_count": sum(1 for row in rows if row["classification"].startswith("RUNTIME_IMPLEMENTED")),
        "rows": rows,
        "blockers": blockers,
    }
