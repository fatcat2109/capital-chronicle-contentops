"""Registered, byte-derived semantic evidence extraction for ContentOps V2.

This module is deterministic and local. It consumes bytes already proven by a
transport receipt; it performs no fetch, publication, credential, or policy action.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from fnmatch import fnmatch
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops import content_intelligence_contracts_v2 as contracts


REGISTRY_REL_PATH = Path("live_contentops/artifact_evidence_extractor_registry_v1.json")


def load_extractor_registry(repo_root: str | Path | None = None) -> contracts.ArtifactEvidenceExtractorRegistryV1:
    root = Path(__file__).resolve().parents[1] if repo_root is None else Path(repo_root).resolve()
    raw = json.loads((root / REGISTRY_REL_PATH).read_text(encoding="utf-8"))
    records = tuple(contracts.ArtifactEvidenceExtractorRecordV1(
        extractor_id=str(row["extractor_id"]),
        extractor_version=str(row["extractor_version"]),
        implementation_contract_id=str(row["implementation_contract_id"]),
        supported_repositories=tuple(row["supported_repositories"]),
        supported_path_patterns=tuple(row["supported_path_patterns"]),
        supported_artifact_schema_versions=tuple(row["supported_artifact_schema_versions"]),
        shape_contract_id=str(row["shape_contract_id"]),
        schema_authority=str(row["schema_authority"]),
        required_fields=tuple(row["required_fields"]),
        evidence_ref_derivation_rule=str(row["evidence_ref_derivation_rule"]),
        timestamp_extraction_rules=dict(row["timestamp_extraction_rules"]),
        authority_derivation_rule=str(row["authority_derivation_rule"]),
        permission_derivation_rule=str(row["permission_derivation_rule"]),
        role_derivation_rule=str(row["role_derivation_rule"]),
        role_required_fields={key: tuple(values) for key, values in row.get("role_required_fields", {}).items()},
        supported_evidence_roles=tuple(contracts.EvidenceRole(value) for value in row["supported_evidence_roles"]),
        supported_evidence_scopes=tuple(contracts.EvidenceScope(value) for value in row["supported_evidence_scopes"]),
        supported_feature_ids=tuple(row["supported_feature_ids"]),
        value_derivation_rules=dict(row["value_derivation_rules"]),
        enabled=bool(row["enabled"]),
    ) for row in raw["records"])
    registry = contracts.ArtifactEvidenceExtractorRegistryV1(
        registry_version=str(raw["registry_version"]),
        records=records,
        registry_logical_hash=str(raw["registry_logical_hash"]),
        schema_version=str(raw["schema_version"]),
    )
    blockers = registry.validate()
    if blockers:
        raise ValueError("invalid_evidence_extractor_registry:" + ",".join(blockers))
    return registry


def _required(value: Mapping[str, Any], fields: Sequence[str]) -> None:
    missing = [field for field in fields if value.get(field) in (None, "")]
    if missing:
        raise ValueError("extractor_required_fields_missing:" + ",".join(missing))


def _date_start_utc(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError("invalid_artifact_native_date") from error
    return parsed.isoformat().replace("+00:00", "Z")


def _internal_pool_logical_hash(artifact: Mapping[str, Any]) -> str:
    return contracts.logical_hash({key: value for key, value in artifact.items() if key not in {"logical_hash", "pool_id"}})


def _select_record(
    extractor: contracts.ArtifactEvidenceExtractorRecordV1,
    artifact: Mapping[str, Any],
    selector: Mapping[str, str],
) -> tuple[Mapping[str, Any], str, tuple[str, ...], dict[str, str | None]]:
    implementation = extractor.implementation_contract_id
    if implementation == "contentops.bls_series_observation_extractor.v1":
        _required(selector, ("series_id", "year", "period"))
        if artifact.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError("bls_response_status_not_success")
        series_rows = artifact.get("Results", {}).get("series", [])
        series = next((row for row in series_rows if row.get("seriesID") == selector["series_id"]), None)
        if series is None:
            raise ValueError("bls_series_not_found")
        row = next((item for item in series.get("data", []) if item.get("year") == selector["year"] and item.get("period") == selector["period"]), None)
        if row is None:
            raise ValueError("bls_period_not_found")
        _required(row, ("year", "period", "value"))
        selected = {"seriesID": series["seriesID"], **row}
        key = f"{series['seriesID']}:{row['year']}:{row['period']}"
        fields = ("seriesID", "year", "period", "periodName", "value")
        times = {"observed_at_utc": None, "known_at_utc": None, "published_at_utc": None, "revision_at_utc": None}
        return selected, key, fields, times
    if implementation == "contentops.treasury_auction_announcement_extractor.v1":
        _required(selector, ("cusip", "announcement_date"))
        if not isinstance(artifact.get("data"), list) or not isinstance(artifact.get("meta"), Mapping):
            raise ValueError("treasury_auction_external_shape_mismatch")
        row = next((item for item in artifact["data"] if item.get("cusip") == selector["cusip"] and item.get("announcemt_date") == selector["announcement_date"]), None)
        if row is None:
            raise ValueError("treasury_auction_record_not_found")
        fields = ("cusip", "announcemt_date", "auction_date", "security_type", "security_term", "auction_format", "offering_amt", "reopening")
        _required(row, fields[:-1])
        timestamp = _date_start_utc(str(row["announcemt_date"]))
        times = {"observed_at_utc": timestamp, "known_at_utc": timestamp, "published_at_utc": timestamp, "revision_at_utc": None}
        return {key: row.get(key) for key in fields}, f"{row['cusip']}:{row['announcemt_date']}", fields, times
    if implementation == "contentops.nyfed_reference_rate_extractor.v1":
        _required(selector, ("rate_type", "effective_date"))
        if not isinstance(artifact.get("refRates"), list):
            raise ValueError("nyfed_reference_rate_external_shape_mismatch")
        row = next((item for item in artifact["refRates"] if item.get("type") == selector["rate_type"] and item.get("effectiveDate") == selector["effective_date"]), None)
        if row is None:
            raise ValueError("nyfed_reference_rate_record_not_found")
        fields = ("effectiveDate", "type", "percentRate", "volumeInBillions", "revisionIndicator")
        _required(row, fields[:3])
        timestamp = _date_start_utc(str(row["effectiveDate"]))
        revision = timestamp if str(row.get("revisionIndicator") or "").strip() else None
        times = {"observed_at_utc": timestamp, "known_at_utc": timestamp, "published_at_utc": None, "revision_at_utc": revision}
        return {key: row.get(key) for key in fields}, f"{row['type']}:{row['effectiveDate']}", fields, times
    if implementation == "contentops.newsroom_candidate_extractor.v1":
        _required(selector, ("candidate_id",))
        rows = [*artifact.get("eligible_candidates", []), *artifact.get("rejected_candidates", [])]
        row = next((item for item in rows if item.get("candidate_id") == selector["candidate_id"]), None)
        if row is None:
            raise ValueError("newsroom_candidate_not_found")
        fields = (
            "candidate_id", "evidence_hash", "authority", "claim_permissions", "event_time_utc",
            "known_at_utc", "source_packet_id", "source_packet_logical_hash", "relationship",
            "eligible", "blockers", "update_chain_id", "governed_material_delta",
            "material_delta_evidence_ref", "prior_testable_proposition_ref",
            "governed_new_evidence_ref", "conflicting_evidence_ref", "prior_error_ref",
            "authoritative_correction_ref", "update_chain_continuity",
            "distinct_new_event_ref", "update_justification_ref", "numeric_claims", "source_documents",
        )
        _required(row, fields[:9])
        if row["authority"].get("story_decision") not in {"ALLOW", "BLOCK", "NOT_GRANTED"}:
            raise ValueError("newsroom_candidate_authority_malformed")
        if row["claim_permissions"].get("reporting_allowed") not in {True, False}:
            raise ValueError("newsroom_candidate_permission_malformed")
        published = None
        if row.get("source_documents"):
            published = row["source_documents"][0].get("published_at_utc")
        times = {
            "observed_at_utc": row.get("event_time_utc"), "known_at_utc": row.get("known_at_utc"),
            "published_at_utc": published, "revision_at_utc": None,
        }
        selected = {key: row.get(key) for key in fields}
        selected["eligible"] = row.get("eligible", any(
            item.get("candidate_id") == row.get("candidate_id")
            for item in artifact.get("eligible_candidates", [])
        ))
        selected["blockers"] = tuple(row.get("blockers") or ())
        return selected, str(row["candidate_id"]), fields, times
    raise ValueError("unsupported_extractor_implementation")


def _derive_authority_permission_roles(
    extractor: contracts.ArtifactEvidenceExtractorRecordV1,
    record: Mapping[str, Any],
) -> tuple[str, str, tuple[contracts.EvidenceRole, ...], str, tuple[str, ...]]:
    """Derive maximum semantic authority from bytes under the registered contract."""
    if extractor.schema_authority == "EXTERNAL_ASSIGNED":
        authority = "OFFICIAL_VERIFIED"
        permission = "CONTEXT_ONLY"
        roles = (contracts.EvidenceRole.FEATURE_SUPPORT,)
        return authority, permission, roles, "NOT_QUALIFYING_GOVERNED", ("context_only", "external_official_context_only")

    authority_payload = record.get("authority") or {}
    permission_payload = record.get("claim_permissions") or {}
    blockers = tuple(str(value) for value in (record.get("blockers") or ()))
    authority_ready = bool(
        record.get("eligible") is True
        and authority_payload.get("story_decision") == "ALLOW"
        and not blockers
    )
    authority = "VERIFIED_GOVERNED" if authority_ready else "BLOCKED"
    reporting_allowed = bool(
        authority_ready
        and permission_payload.get("reporting_allowed") is True
        and permission_payload.get("decision", "ALLOW") == "ALLOW"
    )
    public_markers = [
        bool(row.get("public_claim_allowed"))
        for row in (*tuple(record.get("numeric_claims") or ()), *tuple(record.get("source_documents") or ()))
        if isinstance(row, Mapping) and "public_claim_allowed" in row
    ]
    if reporting_allowed and public_markers and all(public_markers):
        permission = "PUBLIC_CLAIM_ALLOWED"
    elif reporting_allowed:
        permission = "REPORTING_ALLOWED"
    else:
        permission = "REPORTING_NOT_ALLOWED"

    roles: list[contracts.EvidenceRole] = [contracts.EvidenceRole.FEATURE_SUPPORT]
    relationship = str(record.get("relationship") or "")
    role_for_relationship = {
        "material_update": contracts.EvidenceRole.MATERIAL_DELTA,
        "confirmation": contracts.EvidenceRole.CONFIRMATION,
        "contradiction": contracts.EvidenceRole.CONTRADICTION,
        "correction": contracts.EvidenceRole.CORRECTION,
        "new_phase": contracts.EvidenceRole.NEW_PHASE,
    }.get(relationship)
    if authority_ready and reporting_allowed and role_for_relationship is not None:
        required = extractor.role_required_fields.get(role_for_relationship.value, ())
        if required and all(record.get(field) not in (None, "", False) for field in required):
            roles.append(role_for_relationship)
    reason_codes = []
    if not authority_ready:
        reason_codes.extend(("authority_blocked", *blockers))
    if not reporting_allowed:
        reason_codes.append("permission_blocked")
    status = "QUALIFYING_GOVERNED" if authority_ready and reporting_allowed else "NOT_QUALIFYING_GOVERNED"
    return authority, permission, tuple(roles), status, tuple(dict.fromkeys(reason_codes))


def _narrow_state(requested: str | None, derived: str, ranks: Mapping[str, int], kind: str) -> str:
    if requested is None or requested == derived:
        return derived
    if requested not in ranks:
        raise ValueError(f"unknown_requested_{kind}_state")
    if ranks[requested] >= ranks[derived]:
        raise ValueError(f"caller_{kind}_upgrade_forbidden")
    return requested


def _feature_value(
    feature_id: str,
    record: Mapping[str, Any],
    source_fields: Sequence[str],
    times: Mapping[str, str | None],
    evidence_ref: str,
    cutoff_utc: str,
    derivation_contract: str,
) -> contracts.ExtractedFeatureValueV1:
    value: float | None = None
    reason: str | None = None
    availability = contracts.AvailabilityState.UNAVAILABLE
    if feature_id == "evidence_completeness":
        if "seriesID" in record:
            required = ("seriesID", "year", "period", "value")
        elif "cusip" in record:
            required = ("cusip", "announcemt_date", "auction_date", "security_type", "auction_format", "offering_amt")
        elif "effectiveDate" in record:
            required = ("effectiveDate", "type", "percentRate")
        else:
            required = tuple(source_fields)
        present = sum(record.get(field) not in (None, "") for field in required)
        value = present / len(required)
        availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
    elif feature_id == "freshness":
        basis = times.get("known_at_utc") or times.get("published_at_utc") or times.get("observed_at_utc")
        if basis is None:
            reason = "artifact_native_timestamp_unavailable"
        else:
            age_hours = max(0.0, (contracts.parse_utc(cutoff_utc) - contracts.parse_utc(basis)).total_seconds() / 3600.0)
            value = max(0.0, 1.0 - age_hours / 24.0)
            availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
    elif feature_id == "policy_significance":
        reason = "policy_materiality_derivation_contract_unavailable"
    elif feature_id == "authority_readiness":
        authority = record.get("authority", {})
        permissions = record.get("claim_permissions", {})
        value = 1.0 if authority.get("story_decision") == "ALLOW" and permissions.get("reporting_allowed") is True else 0.0
        availability = contracts.AvailabilityState.AVAILABLE if value else contracts.AvailabilityState.EXPLICIT_ZERO
    elif feature_id == "material_delta":
        value = 1.0 if record.get("relationship") in {"material_update", "correction", "contradiction", "new_phase"} else 0.0
        availability = contracts.AvailabilityState.AVAILABLE if value else contracts.AvailabilityState.EXPLICIT_ZERO
    else:
        reason = "feature_derivation_not_supported_by_extractor"
    values = dict(
        feature_id=feature_id, availability=availability, value=value,
        evidence_refs=(evidence_ref,), derivation_contract=derivation_contract,
        reason_code=reason, logical_hash="",
    )
    draft = contracts.ExtractedFeatureValueV1(**values)
    result = replace(draft, logical_hash=draft.calculated_logical_hash())
    blockers = result.validate()
    if blockers:
        raise ValueError("invalid_extracted_feature_value:" + ",".join(blockers))
    return result


def extract_artifact_evidence(
    consumed_bytes: bytes,
    *,
    receipt: contracts.VerifiedProducerArtifactReceiptV1,
    registry: contracts.ArtifactEvidenceExtractorRegistryV1,
    extractor_id: str,
    extractor_version: str,
    selector: Mapping[str, str],
    feature_targets: Sequence[str],
    decision_cutoff_utc: str,
    evidence_roles: Sequence[contracts.EvidenceRole] | None = None,
    evidence_scope: contracts.EvidenceScope = contracts.EvidenceScope.FEATURE_SPECIFIC,
    authority_state: str | None = None,
    permission_state: str | None = None,
) -> tuple[contracts.ExtractedEvidenceRecordV1, tuple[contracts.ExtractedFeatureValueV1, ...]]:
    """Emit semantic refs only after registered extraction from exact receipt bytes."""
    if registry.validate():
        raise ValueError("invalid_evidence_extractor_registry")
    extractor = registry.resolve(extractor_id, extractor_version)
    if extractor is None:
        raise ValueError("unsupported_extractor")
    if not extractor.enabled:
        raise ValueError("extractor_disabled")
    if sha256(consumed_bytes).hexdigest() != receipt.consumed_byte_sha256:
        raise ValueError("extractor_consumed_bytes_receipt_mismatch")
    if receipt.repository not in extractor.supported_repositories:
        raise ValueError("extractor_repository_mismatch")
    if not any(fnmatch(receipt.artifact_path, pattern) for pattern in extractor.supported_path_patterns):
        raise ValueError("extractor_path_mismatch")
    if receipt.artifact_schema_version not in extractor.supported_artifact_schema_versions:
        raise ValueError("extractor_schema_mismatch")
    if evidence_scope not in extractor.supported_evidence_scopes:
        raise ValueError("extractor_evidence_scope_unsupported")
    if any(feature not in extractor.supported_feature_ids for feature in feature_targets):
        raise ValueError("extractor_feature_target_unsupported")
    try:
        artifact = json.loads(consumed_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("extractor_artifact_json_invalid") from error
    if not isinstance(artifact, Mapping):
        raise ValueError("extractor_artifact_root_not_object")
    internal_hash_verified: bool | None = None
    if extractor.schema_authority == "INTERNAL_DECLARED":
        if artifact.get("schema_version") != receipt.artifact_schema_version:
            raise ValueError("internal_artifact_schema_mismatch")
        if artifact.get("producer_version") != receipt.producer_version:
            raise ValueError("internal_producer_version_mismatch")
        internal_hash_verified = artifact.get("logical_hash") == _internal_pool_logical_hash(artifact)
        if not internal_hash_verified:
            raise ValueError("internal_logical_hash_mismatch")
        artifact_cutoff = artifact.get("cutoff_time_utc")
        if artifact_cutoff != receipt.artifact_cutoff_utc:
            raise ValueError("internal_cutoff_mismatch")
    elif receipt.producer_version != extractor.shape_contract_id:
        raise ValueError("external_shape_contract_producer_mismatch")
    record, record_key, source_fields, times = _select_record(extractor, artifact, selector)
    (
        derived_authority, derived_permission, derived_roles,
        qualification_status, qualification_reason_codes,
    ) = _derive_authority_permission_roles(extractor, record)
    selected_roles = derived_roles if evidence_roles is None else tuple(evidence_roles)
    if any(role not in derived_roles for role in selected_roles):
        raise ValueError("caller_evidence_role_addition_forbidden")
    if any(role not in extractor.supported_evidence_roles for role in selected_roles):
        raise ValueError("extractor_evidence_role_unsupported")
    selected_authority = _narrow_state(authority_state, derived_authority, contracts.AUTHORITY_STATE_RANK, "authority")
    selected_permission = _narrow_state(permission_state, derived_permission, contracts.PERMISSION_STATE_RANK, "permission")
    if selected_authority != derived_authority:
        qualification_reason_codes = (*qualification_reason_codes, "caller_authority_narrowed")
        qualification_status = "NOT_QUALIFYING_GOVERNED"
    if selected_permission != derived_permission:
        qualification_reason_codes = (*qualification_reason_codes, "caller_permission_narrowed")
        if selected_permission not in contracts.QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES:
            qualification_status = "NOT_QUALIFYING_GOVERNED"
    cutoff = contracts.parse_utc(decision_cutoff_utc, field_name="decision_cutoff_utc")
    for name, timestamp in times.items():
        if timestamp and contracts.parse_utc(timestamp, field_name=name) > cutoff:
            raise ValueError(f"internal_future_timestamp:{name}")
    record_hash = contracts.logical_hash(record)
    evidence_material = {
        "producer_receipt_logical_hash": receipt.logical_hash,
        "extractor_id": extractor.extractor_id,
        "extractor_version": extractor.extractor_version,
        "record_selector": dict(sorted(selector.items())),
        "record_key": record_key,
        "extracted_record_hash": record_hash,
        "derivation_rule": extractor.evidence_ref_derivation_rule,
    }
    evidence_ref = "extracted:" + contracts.logical_hash(evidence_material)[:32]
    values = dict(
        producer_receipt_id=receipt.receipt_id,
        producer_receipt_logical_hash=receipt.logical_hash,
        extractor_id=extractor.extractor_id,
        extractor_version=extractor.extractor_version,
        record_selector=contracts.canonical_json(dict(sorted(selector.items()))),
        record_key=record_key,
        extracted_record_hash=record_hash,
        evidence_ref=evidence_ref,
        source_fields_used=tuple(source_fields),
        observed_at_utc=times["observed_at_utc"], known_at_utc=times["known_at_utc"],
        published_at_utc=times["published_at_utc"], revision_at_utc=times["revision_at_utc"],
        cutoff_utc=receipt.artifact_cutoff_utc,
        evidence_roles=tuple(selected_roles), evidence_scope=evidence_scope,
        feature_targets=tuple(feature_targets),
        derivation_contract=extractor.implementation_contract_id,
        authority_state=selected_authority, permission_state=selected_permission,
        source_authority_class=receipt.source_authority_class,
        artifact_schema_version=receipt.artifact_schema_version,
        schema_authority=extractor.schema_authority,
        artifact_schema_verified=True, producer_version_verified=True,
        internal_logical_hash_verified=internal_hash_verified,
        extraction_logical_hash="",
        authority_derivation_rule=extractor.authority_derivation_rule,
        permission_derivation_rule=extractor.permission_derivation_rule,
        role_derivation_rule=extractor.role_derivation_rule,
        qualification_status=qualification_status,
        qualification_reason_codes=tuple(dict.fromkeys(qualification_reason_codes)),
    )
    draft = contracts.ExtractedEvidenceRecordV1(**values)
    extracted = replace(draft, extraction_logical_hash=draft.calculated_logical_hash())
    blockers = extracted.validate()
    if blockers:
        raise ValueError("invalid_extracted_evidence_record:" + ",".join(blockers))
    feature_values = tuple(_feature_value(
        feature, record, source_fields, times, evidence_ref, decision_cutoff_utc,
        extractor.value_derivation_rules[feature],
    ) for feature in feature_targets)
    return extracted, feature_values
