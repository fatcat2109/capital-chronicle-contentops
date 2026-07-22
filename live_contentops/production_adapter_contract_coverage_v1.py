"""Deterministic registry-to-runtime coverage audit for production adapters."""
from __future__ import annotations

from typing import Any, Mapping

from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import production_evidence_adapters_wave2_v1 as wave2
from live_contentops import production_evidence_adapters_wave3_v1 as wave3


SCHEMA_VERSION = "contentops.production_adapter_contract_coverage.v1"

# These enabled pre-existing records remain immutable and are implemented by the
# accepted generic, Wave-1, and Wave-2-v1 extractors. They are classified
# separately from the exact declaration-to-code maps introduced by this repair.
HISTORICAL_RUNTIME_IMPLEMENTED_RECORDS = frozenset({
    ("contentops.bls_series_observation_extractor", "v1"),
    ("contentops.treasury_auction_announcement_extractor", "v1"),
    ("contentops.nyfed_reference_rate_extractor", "v1"),
    ("contentops.newsroom_candidate_extractor", "v1"),
    ("contentops.treasury_daily_yield_curve_atom_extractor", "v1"),
    ("contentops.cftc_legacy_futures_only_cot_extractor", "v1"),
    ("contentops.federal_reserve_h41_zip_structure_extractor", "v1"),
    (wave2.TREASURY_EXTRACTOR_ID, "v1"),
    (wave2.BLS_EXTRACTOR_ID, "v1"),
    (wave2.FOMC_EXTRACTOR_ID, "v1"),
})

DOCUMENTARY_NON_RUNTIME_RECORDS = frozenset({
    ("contentops.disabled_legacy_extractor", "v1"),
})

RUNTIME_IMPLEMENTATION_CONTRACTS: Mapping[tuple[str, str], Mapping[str, Any]] = {
    **wave2.IMPLEMENTATION_CONTRACT_COVERAGE,
    **wave3.IMPLEMENTATION_CONTRACT_COVERAGE,
}


def validate_registry_contract_coverage(
    registry: contracts.ArtifactEvidenceExtractorRegistryV1,
) -> Mapping[str, Any]:
    """Prove each registry declaration is runtime-covered or explicitly documentary."""
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for record in registry.records:
        identity = (record.extractor_id, record.extractor_version)
        declaration = RUNTIME_IMPLEMENTATION_CONTRACTS.get(identity)
        if declaration is not None:
            shape_ok = declaration.get("shape_contract_id") == record.shape_contract_id
            fields_ok = tuple(declaration.get("required_fields", ())) == record.required_fields
            timestamps_ok = dict(declaration.get("timestamp_extraction_rules", {})) == dict(record.timestamp_extraction_rules)
            status = "RUNTIME_IMPLEMENTED" if shape_ok and fields_ok and timestamps_ok else "MISMATCH"
            if status == "MISMATCH":
                blockers.append(f"registry_runtime_contract_mismatch:{record.extractor_id}:{record.extractor_version}")
            rows.append({
                "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
                "classification": status, "shape_rule_covered": shape_ok,
                "required_field_rules_declared": len(record.required_fields),
                "required_field_rules_covered": len(record.required_fields) if fields_ok else 0,
                "timestamp_rules_declared": len(record.timestamp_extraction_rules),
                "timestamp_rules_covered": len(record.timestamp_extraction_rules) if timestamps_ok else 0,
            })
        elif identity in HISTORICAL_RUNTIME_IMPLEMENTED_RECORDS:
            rows.append({
                "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
                "classification": "RUNTIME_IMPLEMENTED_HISTORICAL_ACCEPTED", "shape_rule_covered": True,
                "required_field_rules_declared": len(record.required_fields),
                "required_field_rules_covered": len(record.required_fields),
                "timestamp_rules_declared": len(record.timestamp_extraction_rules),
                "timestamp_rules_covered": len(record.timestamp_extraction_rules),
            })
        elif identity in DOCUMENTARY_NON_RUNTIME_RECORDS:
            rows.append({
                "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
                "classification": "EXPLICIT_DOCUMENTARY_NON_RUNTIME", "shape_rule_covered": True,
                "required_field_rules_declared": len(record.required_fields),
                "required_field_rules_covered": len(record.required_fields),
                "timestamp_rules_declared": len(record.timestamp_extraction_rules),
                "timestamp_rules_covered": len(record.timestamp_extraction_rules),
            })
        else:
            blockers.append(f"registry_contract_unclassified:{record.extractor_id}:{record.extractor_version}")
            rows.append({
                "extractor_id": record.extractor_id, "extractor_version": record.extractor_version,
                "classification": "UNCLASSIFIED", "shape_rule_covered": False,
                "required_field_rules_declared": len(record.required_fields), "required_field_rules_covered": 0,
                "timestamp_rules_declared": len(record.timestamp_extraction_rules), "timestamp_rules_covered": 0,
            })
    return {
        "schema_version": SCHEMA_VERSION,
        "registry_version": registry.registry_version,
        "status": "PASS" if not blockers else "FAIL",
        "record_count": len(rows),
        "rows": rows,
        "blockers": blockers,
    }
