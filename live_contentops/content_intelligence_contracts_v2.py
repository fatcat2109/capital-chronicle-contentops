"""Versioned, domain-neutral contracts for ContentOps learning.

This module is deterministic and local.  It contains no provider, browser,
network, credential, dispatch, publication, or policy-mutation behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha1, sha256
import json
import math
import re
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_DECISION_V2 = "contentops.learning_decision.v2"
SCHEMA_HISTORY_V1 = "contentops.published_content_history.v1"
SCHEMA_POOL_BINDING_V1 = "contentops.governed_candidate_pool_binding.v1"
SCHEMA_GAP_SET_V1 = "contentops.content_gap_set.v1"
SCHEMA_OBSERVATION_SET_V1 = "contentops.performance_observation_set.v1"
SCHEMA_CONFIG_V1 = "contentops.adaptive_learning_config.v1"
SCHEMA_MODEL_JUDGMENT_V1 = "contentops.model_assisted_judgment.v1"
SCHEMA_GOVERNED_EVIDENCE_BINDING_V1 = "contentops.governed_evidence_binding.v1"
SCHEMA_TRUSTED_VERIFIER_REGISTRY_V1 = "contentops.trusted_evidence_verifier_registry.v1"
SCHEMA_PRODUCER_ARTIFACT_RECEIPT_V1 = "contentops.verified_producer_artifact_receipt.v1"
SCHEMA_EVIDENCE_EXTRACTOR_REGISTRY_V1 = "contentops.artifact_evidence_extractor_registry.v1"
SCHEMA_EXTRACTED_EVIDENCE_RECORD_V1 = "contentops.extracted_evidence_record.v1"
SCHEMA_EXTRACTED_FEATURE_VALUE_V1 = "contentops.extracted_feature_value.v1"
SCHEMA_FEATURE_EVIDENCE_AGGREGATION_V1 = "contentops.feature_evidence_aggregation.v1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]*$")
CANONICAL_AUTHORITY_GATE_IDS = frozenset({"source_authority_ready", "reporting_allowed"})
QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES = frozenset({
    "VERIFIED_GOVERNED",
    "OFFICIAL_VERIFIED",
    "FIRST_PARTY_VERIFIED",
    "SYNTHETIC_AUTHORIZED",
})
QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES = frozenset({
    "REPORTING_ALLOWED",
    "PUBLIC_CLAIM_ALLOWED",
})
DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES = frozenset({
    "authority_blocked",
    "context_only",
    "malformed",
    "permission_blocked",
    "unavailable",
    "unverified",
})
KNOWN_GOVERNED_EVIDENCE_AUTHORITY_STATES = frozenset({
    *QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES,
    "UNVERIFIED", "BLOCKED", "CONTEXT_ONLY", "UNAVAILABLE",
    "SYNTHETIC_UNAUTHORIZED",
})
KNOWN_GOVERNED_EVIDENCE_PERMISSION_STATES = frozenset({
    *QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES,
    "CONTEXT_ONLY", "REPORTING_NOT_ALLOWED", "PERMISSION_BLOCKED", "UNAVAILABLE",
})
AUTHORITY_STATE_RANK = {
    "UNAVAILABLE": 0, "UNVERIFIED": 0, "BLOCKED": 0,
    "SYNTHETIC_UNAUTHORIZED": 0, "CONTEXT_ONLY": 1,
    "VERIFIED_GOVERNED": 2, "OFFICIAL_VERIFIED": 2,
    "FIRST_PARTY_VERIFIED": 2, "SYNTHETIC_AUTHORIZED": 2,
}
PERMISSION_STATE_RANK = {
    "UNAVAILABLE": 0, "PERMISSION_BLOCKED": 0,
    "REPORTING_NOT_ALLOWED": 0, "CONTEXT_ONLY": 1,
    "REPORTING_ALLOWED": 2, "PUBLIC_CLAIM_ALLOWED": 3,
}


class EventRelationship(str, Enum):
    INITIAL_EVENT = "initial_event"
    DUPLICATE = "duplicate"
    CORRECTION = "correction"
    INCREMENTAL_UPDATE = "incremental_update"
    MATERIAL_UPDATE = "material_update"
    CONFIRMATION = "confirmation"
    CONTRADICTION = "contradiction"
    NEW_PHASE = "new_phase"
    SCHEDULED_FOLLOW_UP = "scheduled_follow_up"
    RETROSPECTIVE_REFRESH = "retrospective_refresh"
    PACKAGING_ONLY_UPDATE = "packaging_only_update"


class EvidenceModality(str, Enum):
    NUMERIC_TIME_SERIES = "numeric_time_series"
    OFFICIAL_TABLE = "official_table"
    OFFICIAL_DOCUMENT = "official_document"
    OFFICIAL_STATEMENT = "official_statement"
    SPEECH_OR_TESTIMONY = "speech_or_testimony"
    LEGAL_OR_REGULATORY_TEXT = "legal_or_regulatory_text"
    CORPORATE_FILING = "corporate_filing"
    MARKET_SNAPSHOT = "market_snapshot"
    SURVEY_OR_DIFFUSION_INDEX = "survey_or_diffusion_index"
    EVENT_CALENDAR = "event_calendar"
    GEOSPATIAL_OR_PHYSICAL_OBSERVATION = "geospatial_or_physical_observation"
    QUALITATIVE_CONTEXT = "qualitative_context"
    DERIVED_CALCULATION = "derived_calculation"
    CROSS_SOURCE_RECONCILIATION = "cross_source_reconciliation"


class TemporalCharacter(str, Enum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    POINT_IN_TIME = "point_in_time"
    PERIOD_OBSERVATION = "period_observation"
    REVISED_RELEASE = "revised_release"
    ROLLING_UPDATE = "rolling_update"
    LIVE_OR_INTRADAY = "live_or_intraday"
    END_OF_SESSION = "end_of_session"
    HISTORICAL_CONTEXT = "historical_context"


class StoryMode(str, Enum):
    STRAIGHT_NEWS = "straight_news"
    DATA_RELEASE = "data_release"
    POLICY_DECISION = "policy_decision"
    MARKET_MOVE = "market_move"
    EXPLAINER = "explainer"
    DEEP_ANALYSIS = "deep_analysis"
    SCENARIO_OUTLOOK = "scenario_outlook"
    CORRECTION = "correction"
    LIVE_UPDATE = "live_update"
    RETROSPECTIVE = "retrospective"


class GapType(str, Enum):
    UNANSWERED_QUESTION = "unanswered_question"
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_TRANSMISSION_ANALYSIS = "missing_transmission_analysis"
    MISSING_VISUAL_EXPLANATION = "missing_visual_explanation"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    SCHEDULED_FOLLOW_UP = "scheduled_follow_up"
    THESIS_REEVALUATION = "thesis_re_evaluation"
    CORRECTION = "correction"
    EVERGREEN_REFRESH = "evergreen_refresh"
    DERIVATIVE_PACKAGING_GAP = "derivative_packaging_gap"
    STALE_EVIDENCE = "stale_evidence"
    REPEATED_TOPIC_NO_NEW_DELTA = "repeated_topic_with_no_new_delta"


class AvailabilityState(str, Enum):
    AVAILABLE = "available"
    EXPLICIT_ZERO = "explicit_zero"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"


class MetricAuthorityClass(str, Enum):
    OFFICIAL_API = "official_api"
    OFFICIAL_DASHBOARD_EXPORT = "official_dashboard_export"
    OFFICIAL_BROWSER_READBACK = "official_browser_readback"
    FIRST_PARTY_WEB_ANALYTICS = "first_party_web_analytics"
    FIRST_PARTY_REDIRECT_ANALYTICS = "first_party_redirect_analytics"
    PUBLIC_COUNTER = "public_counter"
    MANUAL_OPERATOR_ENTRY = "manual_operator_entry"
    DERIVED_METRIC = "derived_metric"
    UNAVAILABLE = "unavailable"


class CalibrationState(str, Enum):
    UNCALIBRATED_FOUNDATION = "UNCALIBRATED_FOUNDATION"
    SHADOW_CALIBRATION = "SHADOW_CALIBRATION"
    OPERATOR_ACCEPTED = "OPERATOR_ACCEPTED"


class EvidenceRole(str, Enum):
    MATERIAL_DELTA = "material_delta"
    CONFIRMATION = "confirmation"
    CONTRADICTION = "contradiction"
    CORRECTION = "correction"
    NEW_PHASE = "new_phase"
    EVERGREEN_JUSTIFICATION = "evergreen_justification"
    FEATURE_SUPPORT = "feature_support"


class EvidenceScope(str, Enum):
    FEATURE_SPECIFIC = "FEATURE_SPECIFIC"
    CANDIDATE_WIDE = "CANDIDATE_WIDE"
    PERFORMANCE_OBSERVATION = "PERFORMANCE_OBSERVATION"
    CONTENT_HISTORY = "CONTENT_HISTORY"
    DERIVED_CAPABILITY = "DERIVED_CAPABILITY"


class EvidenceVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class TrustedVerifierRecordV1:
    """Governed allow-list entry for one verifier implementation/version."""

    verifier_id: str
    verifier_version: str
    implementation_contract_id: str
    allowed_authority_states: tuple[str, ...]
    allowed_permission_states: tuple[str, ...]
    allowed_evidence_roles: tuple[EvidenceRole, ...]
    allowed_evidence_scopes: tuple[EvidenceScope, ...]
    allowed_artifact_schema_versions: tuple[str, ...]
    allowed_repositories: tuple[str, ...]
    allowed_source_authority_classes: tuple[str, ...]
    point_in_time_policy: str
    candidate_wide_reuse_allowed: bool
    enabled: bool

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for name, value in (
            ("verifier_id", self.verifier_id),
            ("verifier_version", self.verifier_version),
            ("implementation_contract_id", self.implementation_contract_id),
            ("point_in_time_policy", self.point_in_time_policy),
        ):
            if not value or not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        for name, values in (
            ("authority_state", self.allowed_authority_states),
            ("permission_state", self.allowed_permission_states),
            ("artifact_schema_version", self.allowed_artifact_schema_versions),
            ("repository", self.allowed_repositories),
            ("source_authority_class", self.allowed_source_authority_classes),
        ):
            if not values:
                blockers.append(f"empty_allowed_{name}")
            if len(values) != len(set(values)):
                blockers.append(f"duplicate_allowed_{name}")
            if any(not isinstance(value, str) or not value.strip() for value in values):
                blockers.append(f"malformed_allowed_{name}")
        if any(value not in KNOWN_GOVERNED_EVIDENCE_AUTHORITY_STATES for value in self.allowed_authority_states):
            blockers.append("unknown_allowed_authority_state")
        if any(value not in KNOWN_GOVERNED_EVIDENCE_PERMISSION_STATES for value in self.allowed_permission_states):
            blockers.append("unknown_allowed_permission_state")
        if not self.allowed_evidence_roles or len(self.allowed_evidence_roles) != len(set(self.allowed_evidence_roles)):
            blockers.append("invalid_allowed_evidence_roles")
        if any(not isinstance(value, EvidenceRole) for value in self.allowed_evidence_roles):
            blockers.append("unknown_allowed_evidence_role")
        if not self.allowed_evidence_scopes or len(self.allowed_evidence_scopes) != len(set(self.allowed_evidence_scopes)):
            blockers.append("invalid_allowed_evidence_scopes")
        if any(not isinstance(value, EvidenceScope) for value in self.allowed_evidence_scopes):
            blockers.append("unknown_allowed_evidence_scope")
        if self.point_in_time_policy != "STRICT_OBSERVED_AS_OF_CUTOFF_V1":
            blockers.append("unsupported_point_in_time_policy")
        if not isinstance(self.candidate_wide_reuse_allowed, bool) or not isinstance(self.enabled, bool):
            blockers.append("invalid_verifier_boolean_policy")
        return _unique(blockers)


@dataclass(frozen=True)
class TrustedVerifierRegistryV1:
    registry_version: str
    records: tuple[TrustedVerifierRecordV1, ...]
    registry_logical_hash: str
    schema_version: str = SCHEMA_TRUSTED_VERIFIER_REGISTRY_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "registry_logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_TRUSTED_VERIFIER_REGISTRY_V1:
            blockers.append("trusted_verifier_registry_schema_mismatch")
        if not self.registry_version or not IDENTIFIER_RE.fullmatch(self.registry_version):
            blockers.append("malformed_registry_version")
        keys = [(row.verifier_id, row.verifier_version) for row in self.records]
        if len(keys) != len(set(keys)):
            blockers.append("duplicate_verifier_id_version")
        blockers.extend(blocker for row in self.records for blocker in row.validate())
        if not SHA256_RE.fullmatch(self.registry_logical_hash or ""):
            blockers.append("malformed_registry_logical_hash")
        elif self.registry_logical_hash != self.calculated_logical_hash():
            blockers.append("registry_logical_hash_mismatch")
        return _unique(blockers)

    def resolve(self, verifier_id: str, verifier_version: str) -> TrustedVerifierRecordV1 | None:
        return next((row for row in self.records if row.verifier_id == verifier_id and row.verifier_version == verifier_version), None)


@dataclass(frozen=True)
class VerifiedProducerArtifactReceiptV1:
    receipt_id: str
    repository: str
    branch: str
    producer_commit: str
    artifact_path: str
    git_blob_sha1: str
    consumed_byte_sha256: str
    artifact_schema_version: str
    producer_version: str
    artifact_logical_hash: str
    artifact_cutoff_utc: str
    verification_status: EvidenceVerificationStatus
    verifier_id: str
    verifier_version: str
    implementation_contract_id: str
    registry_version: str
    registry_logical_hash: str
    evidence_refs: tuple[str, ...]
    evidence_ref_derivations: Mapping[str, str]
    source_authority_class: str
    logical_hash: str
    branch_head_observed: str = ""
    producer_commit_reachable_from_branch: bool = False
    verification_time_utc: str = ""
    schema_version: str = SCHEMA_PRODUCER_ARTIFACT_RECEIPT_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_PRODUCER_ARTIFACT_RECEIPT_V1:
            blockers.append("producer_receipt_schema_mismatch")
        for name, value in (
            ("receipt_id", self.receipt_id), ("repository", self.repository),
            ("branch", self.branch), ("artifact_schema_version", self.artifact_schema_version),
            ("producer_version", self.producer_version), ("verifier_id", self.verifier_id),
            ("verifier_version", self.verifier_version),
            ("implementation_contract_id", self.implementation_contract_id),
            ("registry_version", self.registry_version),
            ("source_authority_class", self.source_authority_class),
        ):
            if not value or (name not in {"repository"} and not IDENTIFIER_RE.fullmatch(value)):
                blockers.append(f"malformed_{name}")
        if not self.artifact_path or self.artifact_path.startswith(("/", "\\")) or ".." in self.artifact_path.replace("\\", "/").split("/"):
            blockers.append("malformed_artifact_path")
        if not COMMIT_RE.fullmatch(self.producer_commit or ""):
            blockers.append("malformed_producer_commit")
        if not COMMIT_RE.fullmatch(self.branch_head_observed or ""):
            blockers.append("malformed_branch_head_observed")
        if self.producer_commit_reachable_from_branch is not True:
            blockers.append("producer_commit_not_reachable_from_branch")
        if not SHA1_RE.fullmatch(self.git_blob_sha1 or ""):
            blockers.append("malformed_git_blob_sha1")
        for name, value in (
            ("consumed_byte_sha256", self.consumed_byte_sha256),
            ("artifact_logical_hash", self.artifact_logical_hash),
            ("registry_logical_hash", self.registry_logical_hash),
            ("logical_hash", self.logical_hash),
        ):
            if not SHA256_RE.fullmatch(value or ""):
                blockers.append(f"malformed_{name}")
        try:
            parse_utc(self.artifact_cutoff_utc, field_name="artifact_cutoff_utc")
        except ValueError as error:
            blockers.append(str(error))
        try:
            parse_utc(self.verification_time_utc, field_name="verification_time_utc")
        except ValueError as error:
            blockers.append(str(error))
        if self.verification_status != EvidenceVerificationStatus.VERIFIED:
            blockers.append("producer_receipt_not_verified")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            blockers.append("duplicate_producer_receipt_evidence_ref")
        if any(not IDENTIFIER_RE.fullmatch(ref) for ref in self.evidence_refs):
            blockers.append("malformed_producer_receipt_evidence_ref")
        if set(self.evidence_ref_derivations) != set(self.evidence_refs):
            blockers.append("producer_receipt_evidence_ref_derivation_keys_mismatch")
        for ref, derivation_hash in self.evidence_ref_derivations.items():
            expected = logical_hash({
                "artifact_logical_hash": self.artifact_logical_hash,
                "evidence_ref": ref,
                "derivation_contract": "contentops.artifact_evidence_ref_derivation.v1",
            })
            if not SHA256_RE.fullmatch(derivation_hash or "") or derivation_hash != expected:
                blockers.append(f"producer_receipt_evidence_ref_derivation_mismatch:{ref}")
        if SHA256_RE.fullmatch(self.logical_hash or "") and self.logical_hash != self.calculated_logical_hash():
            blockers.append("producer_receipt_logical_hash_mismatch")
        return _unique(blockers)


@dataclass(frozen=True)
class ArtifactEvidenceExtractorRecordV1:
    """Allow-listed semantic extractor contract; transport verification is separate."""

    extractor_id: str
    extractor_version: str
    implementation_contract_id: str
    supported_repositories: tuple[str, ...]
    supported_path_patterns: tuple[str, ...]
    supported_artifact_schema_versions: tuple[str, ...]
    shape_contract_id: str
    schema_authority: str
    required_fields: tuple[str, ...]
    evidence_ref_derivation_rule: str
    timestamp_extraction_rules: Mapping[str, str]
    authority_derivation_rule: str
    permission_derivation_rule: str
    role_derivation_rule: str
    role_required_fields: Mapping[str, tuple[str, ...]]
    supported_evidence_roles: tuple[EvidenceRole, ...]
    supported_evidence_scopes: tuple[EvidenceScope, ...]
    supported_feature_ids: tuple[str, ...]
    value_derivation_rules: Mapping[str, str]
    enabled: bool

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for name, value in (
            ("extractor_id", self.extractor_id),
            ("extractor_version", self.extractor_version),
            ("implementation_contract_id", self.implementation_contract_id),
            ("shape_contract_id", self.shape_contract_id),
            ("authority_derivation_rule", self.authority_derivation_rule),
            ("permission_derivation_rule", self.permission_derivation_rule),
            ("role_derivation_rule", self.role_derivation_rule),
        ):
            if not value or not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if self.schema_authority not in {"INTERNAL_DECLARED", "EXTERNAL_ASSIGNED"}:
            blockers.append("unsupported_schema_authority")
        for name, values in (
            ("repository", self.supported_repositories),
            ("path_pattern", self.supported_path_patterns),
            ("artifact_schema_version", self.supported_artifact_schema_versions),
            ("required_field", self.required_fields),
            ("feature_id", self.supported_feature_ids),
        ):
            if not values:
                blockers.append(f"empty_supported_{name}")
            if len(values) != len(set(values)):
                blockers.append(f"duplicate_supported_{name}")
            if any(not isinstance(value, str) or not value.strip() for value in values):
                blockers.append(f"malformed_supported_{name}")
        if self.evidence_ref_derivation_rule != "EXTRACTED_RECORD_HASH_V1":
            blockers.append("unsupported_evidence_ref_derivation_rule")
        if not self.timestamp_extraction_rules:
            blockers.append("timestamp_extraction_rules_empty")
        if set(self.role_required_fields) - {role.value for role in self.supported_evidence_roles}:
            blockers.append("role_required_fields_not_supported")
        if any(not isinstance(values, tuple) or not values for values in self.role_required_fields.values()):
            blockers.append("invalid_role_required_fields")
        if not self.supported_evidence_roles or any(not isinstance(value, EvidenceRole) for value in self.supported_evidence_roles):
            blockers.append("invalid_extractor_evidence_roles")
        if not self.supported_evidence_scopes or any(not isinstance(value, EvidenceScope) for value in self.supported_evidence_scopes):
            blockers.append("invalid_extractor_evidence_scopes")
        if not isinstance(self.enabled, bool):
            blockers.append("invalid_extractor_enabled_state")
        return _unique(blockers)


@dataclass(frozen=True)
class ArtifactEvidenceExtractorRegistryV1:
    registry_version: str
    records: tuple[ArtifactEvidenceExtractorRecordV1, ...]
    registry_logical_hash: str
    schema_version: str = SCHEMA_EVIDENCE_EXTRACTOR_REGISTRY_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "registry_logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_EVIDENCE_EXTRACTOR_REGISTRY_V1:
            blockers.append("evidence_extractor_registry_schema_mismatch")
        keys = [(row.extractor_id, row.extractor_version) for row in self.records]
        if len(keys) != len(set(keys)):
            blockers.append("duplicate_extractor_id_version")
        blockers.extend(blocker for row in self.records for blocker in row.validate())
        if not SHA256_RE.fullmatch(self.registry_logical_hash or ""):
            blockers.append("malformed_extractor_registry_logical_hash")
        elif self.registry_logical_hash != self.calculated_logical_hash():
            blockers.append("extractor_registry_logical_hash_mismatch")
        return _unique(blockers)

    def resolve(self, extractor_id: str, extractor_version: str) -> ArtifactEvidenceExtractorRecordV1 | None:
        return next((row for row in self.records if row.extractor_id == extractor_id and row.extractor_version == extractor_version), None)


@dataclass(frozen=True)
class ExtractedEvidenceRecordV1:
    producer_receipt_id: str
    producer_receipt_logical_hash: str
    extractor_id: str
    extractor_version: str
    record_selector: str
    record_key: str
    extracted_record_hash: str
    evidence_ref: str
    source_fields_used: tuple[str, ...]
    observed_at_utc: str | None
    known_at_utc: str | None
    published_at_utc: str | None
    revision_at_utc: str | None
    cutoff_utc: str
    evidence_roles: tuple[EvidenceRole, ...]
    evidence_scope: EvidenceScope
    feature_targets: tuple[str, ...]
    derivation_contract: str
    authority_state: str
    permission_state: str
    source_authority_class: str
    artifact_schema_version: str
    schema_authority: str
    artifact_schema_verified: bool
    producer_version_verified: bool
    internal_logical_hash_verified: bool | None
    extraction_logical_hash: str
    authority_derivation_rule: str = "LEGACY_CALLER_ASSERTED"
    permission_derivation_rule: str = "LEGACY_CALLER_ASSERTED"
    role_derivation_rule: str = "LEGACY_CALLER_ASSERTED"
    qualification_status: str = "LEGACY_UNSPECIFIED"
    qualification_reason_codes: tuple[str, ...] = ()
    schema_version: str = SCHEMA_EXTRACTED_EVIDENCE_RECORD_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "extraction_logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_EXTRACTED_EVIDENCE_RECORD_V1:
            blockers.append("extracted_evidence_schema_mismatch")
        for name, value in (
            ("producer_receipt_id", self.producer_receipt_id),
            ("extractor_id", self.extractor_id),
            ("extractor_version", self.extractor_version),
            ("evidence_ref", self.evidence_ref),
            ("derivation_contract", self.derivation_contract),
            ("artifact_schema_version", self.artifact_schema_version),
            ("authority_derivation_rule", self.authority_derivation_rule),
            ("permission_derivation_rule", self.permission_derivation_rule),
            ("role_derivation_rule", self.role_derivation_rule),
            ("qualification_status", self.qualification_status),
        ):
            if not value or not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if not self.record_selector or not self.record_key:
            blockers.append("missing_extracted_record_selector_or_key")
        for name, value in (
            ("producer_receipt_logical_hash", self.producer_receipt_logical_hash),
            ("extracted_record_hash", self.extracted_record_hash),
            ("extraction_logical_hash", self.extraction_logical_hash),
        ):
            if not SHA256_RE.fullmatch(value or ""):
                blockers.append(f"malformed_{name}")
        if not self.source_fields_used or len(self.source_fields_used) != len(set(self.source_fields_used)):
            blockers.append("invalid_source_fields_used")
        if not self.evidence_roles or any(not isinstance(value, EvidenceRole) for value in self.evidence_roles):
            blockers.append("invalid_extracted_evidence_roles")
        if self.authority_state not in KNOWN_GOVERNED_EVIDENCE_AUTHORITY_STATES:
            blockers.append("unknown_extracted_authority_state")
        if self.permission_state not in KNOWN_GOVERNED_EVIDENCE_PERMISSION_STATES:
            blockers.append("unknown_extracted_permission_state")
        if self.qualification_status not in {"QUALIFYING_GOVERNED", "NOT_QUALIFYING_GOVERNED", "LEGACY_UNSPECIFIED"}:
            blockers.append("unknown_extracted_qualification_status")
        if (
            self.qualification_status == "QUALIFYING_GOVERNED"
            and (
                self.authority_state not in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
                or self.permission_state not in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
                or set(self.qualification_reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES
            )
        ):
            blockers.append("contradictory_extracted_qualification")
        if any(not IDENTIFIER_RE.fullmatch(value) for value in self.qualification_reason_codes):
            blockers.append("malformed_qualification_reason_code")
        if not isinstance(self.evidence_scope, EvidenceScope):
            blockers.append("invalid_extracted_evidence_scope")
        if self.schema_authority not in {"INTERNAL_DECLARED", "EXTERNAL_ASSIGNED"}:
            blockers.append("invalid_extracted_schema_authority")
        if not self.artifact_schema_verified or not self.producer_version_verified:
            blockers.append("artifact_shape_or_producer_unverified")
        for field_name in ("observed_at_utc", "known_at_utc", "published_at_utc", "revision_at_utc"):
            value = getattr(self, field_name)
            if value is not None:
                try:
                    parse_utc(value, field_name=field_name)
                except ValueError as error:
                    blockers.append(str(error))
        try:
            parse_utc(self.cutoff_utc, field_name="extracted_cutoff_utc")
        except ValueError as error:
            blockers.append(str(error))
        if SHA256_RE.fullmatch(self.extraction_logical_hash or "") and self.extraction_logical_hash != self.calculated_logical_hash():
            blockers.append("extraction_logical_hash_mismatch")
        return _unique(blockers)


@dataclass(frozen=True)
class ExtractedFeatureValueV1:
    feature_id: str
    availability: AvailabilityState
    value: float | None
    evidence_refs: tuple[str, ...]
    derivation_contract: str
    reason_code: str | None
    logical_hash: str
    schema_version: str = SCHEMA_EXTRACTED_FEATURE_VALUE_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_EXTRACTED_FEATURE_VALUE_V1:
            blockers.append("extracted_feature_value_schema_mismatch")
        if not IDENTIFIER_RE.fullmatch(self.feature_id or ""):
            blockers.append("malformed_extracted_feature_id")
        if self.availability in {AvailabilityState.AVAILABLE, AvailabilityState.EXPLICIT_ZERO} and self.value is None:
            blockers.append("available_extracted_feature_missing_value")
        if self.availability not in {AvailabilityState.AVAILABLE, AvailabilityState.EXPLICIT_ZERO} and self.value is not None:
            blockers.append("unavailable_extracted_feature_has_value")
        if not self.evidence_refs or len(self.evidence_refs) != len(set(self.evidence_refs)):
            blockers.append("invalid_extracted_feature_evidence_refs")
        if not IDENTIFIER_RE.fullmatch(self.derivation_contract or ""):
            blockers.append("malformed_feature_derivation_contract")
        if self.logical_hash != self.calculated_logical_hash():
            blockers.append("extracted_feature_logical_hash_mismatch")
        return _unique(blockers)


@dataclass(frozen=True)
class FeatureEvidenceAggregationV1:
    """Registered, hash-bound derivation over an exact evidence set."""

    aggregation_id: str
    aggregation_version: str
    feature_id: str
    input_evidence_refs: tuple[str, ...]
    individual_values: Mapping[str, float]
    aggregation_rule: str
    output_value: float
    logical_hash: str
    schema_version: str = SCHEMA_FEATURE_EVIDENCE_AGGREGATION_V1

    def calculated_output(self) -> float:
        ordered = [float(self.individual_values[ref]) for ref in self.input_evidence_refs]
        if self.aggregation_rule == "ARITHMETIC_MEAN_V1":
            return sum(ordered) / len(ordered)
        if self.aggregation_rule == "MINIMUM_V1":
            return min(ordered)
        if self.aggregation_rule == "MAXIMUM_V1":
            return max(ordered)
        if self.aggregation_rule == "BOOLEAN_ALL_V1":
            if any(value not in {0.0, 1.0} for value in ordered):
                raise ValueError("boolean_aggregation_requires_zero_or_one")
            return 1.0 if all(ordered) else 0.0
        raise ValueError("unregistered_feature_aggregation_rule")

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_FEATURE_EVIDENCE_AGGREGATION_V1:
            blockers.append("feature_aggregation_schema_mismatch")
        for name, value in (("aggregation_id", self.aggregation_id), ("aggregation_version", self.aggregation_version), ("feature_id", self.feature_id)):
            if not IDENTIFIER_RE.fullmatch(value or ""):
                blockers.append(f"malformed_{name}")
        if not self.input_evidence_refs or len(self.input_evidence_refs) != len(set(self.input_evidence_refs)):
            blockers.append("invalid_aggregation_input_refs")
        if set(self.individual_values) != set(self.input_evidence_refs):
            blockers.append("aggregation_individual_value_refs_mismatch")
        if self.aggregation_rule not in {"ARITHMETIC_MEAN_V1", "MINIMUM_V1", "MAXIMUM_V1", "BOOLEAN_ALL_V1"}:
            blockers.append("unregistered_feature_aggregation_rule")
        try:
            if not blockers and not math.isclose(float(self.output_value), self.calculated_output(), rel_tol=0.0, abs_tol=1e-12):
                blockers.append("feature_aggregation_output_mismatch")
        except (KeyError, TypeError, ValueError):
            blockers.append("feature_aggregation_inputs_invalid")
        if self.logical_hash != self.calculated_logical_hash():
            blockers.append("feature_aggregation_logical_hash_mismatch")
        return _unique(blockers)


@dataclass(frozen=True)
class EvidenceDecisionContextV1:
    verifier_registry: TrustedVerifierRegistryV1
    producer_receipts: tuple[VerifiedProducerArtifactReceiptV1, ...]
    decision_cutoff_utc: str
    extractor_registry: ArtifactEvidenceExtractorRegistryV1 | None = None
    extracted_evidence_records: tuple[ExtractedEvidenceRecordV1, ...] = ()
    extracted_feature_values: tuple[ExtractedFeatureValueV1, ...] = ()
    registered_feature_aggregations: tuple[FeatureEvidenceAggregationV1, ...] = ()

    def validate(self) -> tuple[str, ...]:
        blockers = list(self.verifier_registry.validate())
        if self.extractor_registry is not None:
            blockers.extend(self.extractor_registry.validate())
        elif any(receipt.source_authority_class != "governed_synthetic_validation" for receipt in self.producer_receipts):
            blockers.append("semantic_extractor_registry_missing")
        try:
            cutoff = parse_utc(self.decision_cutoff_utc, field_name="decision_cutoff_utc")
        except ValueError as error:
            blockers.append(str(error))
            cutoff = None
        ids = [row.receipt_id for row in self.producer_receipts]
        if len(ids) != len(set(ids)):
            blockers.append("duplicate_producer_receipt_id")
        for receipt in self.producer_receipts:
            blockers.extend(receipt.validate())
            if receipt.registry_version != self.verifier_registry.registry_version:
                blockers.append(f"producer_receipt_registry_version_mismatch:{receipt.receipt_id}")
            if receipt.registry_logical_hash != self.verifier_registry.registry_logical_hash:
                blockers.append(f"producer_receipt_registry_hash_mismatch:{receipt.receipt_id}")
            if cutoff is not None:
                try:
                    if parse_utc(receipt.artifact_cutoff_utc) > cutoff:
                        blockers.append(f"future_producer_receipt:{receipt.receipt_id}")
                except ValueError:
                    pass
        record_refs = [row.evidence_ref for row in self.extracted_evidence_records]
        if len(record_refs) != len(set(record_refs)):
            blockers.append("duplicate_extracted_evidence_ref")
        for row in self.extracted_evidence_records:
            blockers.extend(row.validate())
            receipt = next((item for item in self.producer_receipts if item.receipt_id == row.producer_receipt_id), None)
            if receipt is None or receipt.logical_hash != row.producer_receipt_logical_hash:
                blockers.append(f"extracted_evidence_receipt_mismatch:{row.evidence_ref}")
            extractor = self.extractor_registry.resolve(row.extractor_id, row.extractor_version) if self.extractor_registry else None
            if self.extractor_registry is not None and extractor is None:
                blockers.append(f"unsupported_extractor:{row.extractor_id}")
            elif extractor is not None and not extractor.enabled:
                blockers.append(f"extractor_disabled:{row.extractor_id}")
            elif extractor is not None:
                if row.authority_derivation_rule != extractor.authority_derivation_rule:
                    blockers.append(f"authority_derivation_rule_mismatch:{row.evidence_ref}")
                if row.permission_derivation_rule != extractor.permission_derivation_rule:
                    blockers.append(f"permission_derivation_rule_mismatch:{row.evidence_ref}")
                if row.role_derivation_rule != extractor.role_derivation_rule:
                    blockers.append(f"role_derivation_rule_mismatch:{row.evidence_ref}")
                if any(role not in extractor.supported_evidence_roles for role in row.evidence_roles):
                    blockers.append(f"extracted_role_not_supported:{row.evidence_ref}")
                if any(feature not in extractor.supported_feature_ids for feature in row.feature_targets):
                    blockers.append(f"extracted_feature_not_supported:{row.evidence_ref}")
        for row in self.extracted_feature_values:
            blockers.extend(row.validate())
            if any(ref not in record_refs for ref in row.evidence_refs):
                blockers.append(f"extracted_feature_ref_missing:{row.feature_id}")
        aggregation_ids = [row.aggregation_id for row in self.registered_feature_aggregations]
        if len(aggregation_ids) != len(set(aggregation_ids)):
            blockers.append("duplicate_feature_aggregation_id")
        for row in self.registered_feature_aggregations:
            blockers.extend(row.validate())
            if any(ref not in record_refs for ref in row.input_evidence_refs):
                blockers.append(f"feature_aggregation_ref_missing:{row.feature_id}")
        return _unique(blockers)


def primitive(value: Any) -> Any:
    if is_dataclass(value):
        return {key: primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def logical_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_utc(value: str, *, field_name: str = "timestamp") -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_{field_name}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid_{field_name}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"timezone_required_{field_name}")
    return parsed.astimezone(timezone.utc)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _validate_identifier_values(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    blockers: list[str] = []
    if len(values) != len(set(values)):
        blockers.append(f"duplicate_{field_name}")
    for value in values:
        if not isinstance(value, str) or not value.strip() or not IDENTIFIER_RE.fullmatch(value):
            blockers.append(f"malformed_{field_name}:{value}")
    return _unique(blockers)


@dataclass(frozen=True)
class CapabilityDimensionsV1:
    evidence_modalities: tuple[EvidenceModality, ...] = ()
    temporal_characters: tuple[TemporalCharacter, ...] = ()
    story_modes: tuple[StoryMode, ...] = ()
    geography_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    affected_economic_domains: tuple[str, ...] = ()
    affected_asset_classes: tuple[str, ...] = ()
    source_family_ids: tuple[str, ...] = ()
    source_authority_classes: tuple[str, ...] = ()
    numeric_evidence_present: bool | None = None
    nonnumeric_evidence_present: bool | None = None
    scheduled_event_state: bool | None = None

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        enum_fields = {
            "evidence_modality": (self.evidence_modalities, EvidenceModality),
            "temporal_character": (self.temporal_characters, TemporalCharacter),
            "story_mode": (self.story_modes, StoryMode),
        }
        for name, (values, enum_type) in enum_fields.items():
            if len(values) != len(set(values)):
                blockers.append(f"duplicate_{name}")
            if any(not isinstance(value, enum_type) for value in values):
                blockers.append(f"invalid_{name}")
        for name, values in (
            ("geography_id", self.geography_ids),
            ("entity_id", self.entity_ids),
            ("economic_domain", self.affected_economic_domains),
            ("asset_class", self.affected_asset_classes),
            ("source_family_id", self.source_family_ids),
            ("source_authority_class", self.source_authority_classes),
        ):
            blockers.extend(_validate_identifier_values(values, name))
        for name, value in (
            ("numeric_evidence_present", self.numeric_evidence_present),
            ("nonnumeric_evidence_present", self.nonnumeric_evidence_present),
            ("scheduled_event_state", self.scheduled_event_state),
        ):
            if value is not None and not isinstance(value, bool):
                blockers.append(f"invalid_{name}")
        if self.scheduled_event_state is True and TemporalCharacter.UNSCHEDULED in self.temporal_characters:
            blockers.append("scheduled_state_conflicts_with_unscheduled_character")
        if self.scheduled_event_state is False and TemporalCharacter.SCHEDULED in self.temporal_characters:
            blockers.append("unscheduled_state_conflicts_with_scheduled_character")
        return _unique(blockers)

    def profile(self) -> Mapping[str, bool | int | None]:
        numeric = self.numeric_evidence_present
        nonnumeric = self.nonnumeric_evidence_present
        return {
            "numeric_evidence_present": numeric,
            "nonnumeric_evidence_present": nonnumeric,
            "mixed_evidence_profile": bool(numeric and nonnumeric),
            "document_only_profile": bool(
                nonnumeric
                and not numeric
                and self.evidence_modalities
                and set(self.evidence_modalities).issubset({
                    EvidenceModality.OFFICIAL_DOCUMENT,
                    EvidenceModality.OFFICIAL_STATEMENT,
                    EvidenceModality.SPEECH_OR_TESTIMONY,
                    EvidenceModality.LEGAL_OR_REGULATORY_TEXT,
                    EvidenceModality.CORPORATE_FILING,
                    EvidenceModality.QUALITATIVE_CONTEXT,
                })
            ),
            "scheduled_event_state": self.scheduled_event_state,
            "source_count": len(self.source_family_ids),
            "geography_count": len(self.geography_ids),
            "entity_count": len(self.entity_ids),
            "economic_domain_count": len(self.affected_economic_domains),
            "asset_class_count": len(self.affected_asset_classes),
        }


@dataclass(frozen=True)
class EvidenceReferenceV1:
    evidence_ref: str
    authority_state: str
    permission_state: str
    modality: EvidenceModality | None = None
    observed_at_utc: str | None = None
    reason_codes: tuple[str, ...] = ()
    temporal_character: TemporalCharacter | None = None
    source_family_id: str | None = None
    source_authority_class: str | None = None
    evidence_roles: tuple[EvidenceRole, ...] = ()
    evidence_scope: EvidenceScope | None = None
    verifier_id: str | None = None
    verifier_version: str | None = None
    verification_status: EvidenceVerificationStatus | None = None
    producer_artifact_binding_hash: str | None = None
    producer_receipt_id: str | None = None
    producer_receipt_logical_hash: str | None = None
    target_feature_ids: tuple[str, ...] = ()
    as_of_utc: str | None = None
    logical_hash: str | None = None

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.evidence_ref or not IDENTIFIER_RE.fullmatch(self.evidence_ref):
            blockers.append("malformed_evidence_ref")
        if not self.authority_state:
            blockers.append("missing_evidence_authority_state")
        if not self.permission_state:
            blockers.append("missing_evidence_permission_state")
        if self.authority_state not in KNOWN_GOVERNED_EVIDENCE_AUTHORITY_STATES:
            blockers.append("unknown_evidence_authority_state")
        if self.permission_state not in KNOWN_GOVERNED_EVIDENCE_PERMISSION_STATES:
            blockers.append("unknown_evidence_permission_state")
        if len(self.evidence_roles) != len(set(self.evidence_roles)):
            blockers.append("duplicate_evidence_role")
        if any(not isinstance(value, EvidenceRole) for value in self.evidence_roles):
            blockers.append("unknown_evidence_role")
        if self.evidence_scope is not None and not isinstance(self.evidence_scope, EvidenceScope):
            blockers.append("unknown_evidence_scope")
        if self.verification_status is not None and not isinstance(self.verification_status, EvidenceVerificationStatus):
            blockers.append("unknown_evidence_verification_status")
        for name, value in (
            ("source_family_id", self.source_family_id),
            ("source_authority_class", self.source_authority_class),
        ):
            if value is not None and not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if self.observed_at_utc:
            try:
                parse_utc(self.observed_at_utc, field_name="evidence_observed_at_utc")
            except ValueError as error:
                blockers.append(str(error))
        if self.as_of_utc:
            try:
                parse_utc(self.as_of_utc, field_name="evidence_as_of_utc")
            except ValueError as error:
                blockers.append(str(error))
        if self.verifier_id is not None and not IDENTIFIER_RE.fullmatch(self.verifier_id):
            blockers.append("malformed_evidence_verifier_id")
        if self.verifier_version is not None and not IDENTIFIER_RE.fullmatch(self.verifier_version):
            blockers.append("malformed_evidence_verifier_version")
        if self.producer_artifact_binding_hash is not None and not SHA256_RE.fullmatch(self.producer_artifact_binding_hash):
            blockers.append("malformed_producer_artifact_binding_hash")
        if self.producer_receipt_id is not None and not IDENTIFIER_RE.fullmatch(self.producer_receipt_id):
            blockers.append("malformed_producer_receipt_id")
        if self.producer_receipt_logical_hash is not None and not SHA256_RE.fullmatch(self.producer_receipt_logical_hash):
            blockers.append("malformed_producer_receipt_logical_hash")
        blockers.extend(_validate_identifier_values(self.target_feature_ids, "target_feature_id"))
        if self.logical_hash is not None and not SHA256_RE.fullmatch(self.logical_hash):
            blockers.append("malformed_evidence_logical_hash")
        if self.logical_hash is not None and self.logical_hash != self.calculated_logical_hash():
            blockers.append("evidence_logical_hash_mismatch")
        return _unique(blockers)

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "logical_hash"}
        return logical_hash(material)

    def provenance_blockers(self) -> tuple[str, ...]:
        blockers = list(self.validate())
        if not self.evidence_roles:
            blockers.append("missing_evidence_roles")
        if self.evidence_scope is None:
            blockers.append("missing_evidence_scope")
        if not self.verifier_id:
            blockers.append("missing_evidence_verifier_id")
        if not self.verifier_version:
            blockers.append("missing_evidence_verifier_version")
        if self.verification_status is None:
            blockers.append("missing_evidence_verification_status")
        if not self.producer_artifact_binding_hash:
            blockers.append("missing_producer_artifact_binding_hash")
        if not self.producer_receipt_id:
            blockers.append("missing_producer_receipt_id")
        if not self.producer_receipt_logical_hash:
            blockers.append("missing_producer_receipt_logical_hash")
        if not self.as_of_utc:
            blockers.append("missing_evidence_as_of_utc")
        if not self.logical_hash:
            blockers.append("missing_evidence_logical_hash")
        return _unique(blockers)

    def qualifies_for_governed_outcome(self) -> bool:
        """Return whether this record may support a governed outcome.

        Validation, authority, and permission are deliberately independent.
        Context-only, blocked, unavailable, malformed, and unverified records
        remain valid evidence records but cannot satisfy governed evidence.
        """
        return bool(
            not self.provenance_blockers()
            and self.authority_state in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
            and self.permission_state in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
            and self.verification_status == EvidenceVerificationStatus.VERIFIED
            and not (set(self.reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES)
        )


@dataclass(frozen=True)
class GovernedEvidenceBindingV1:
    evidence_ref: str
    authority_state: str
    permission_state: str
    evidence_roles: tuple[EvidenceRole, ...]
    verifier_id: str
    verifier_version: str
    verification_status: EvidenceVerificationStatus
    producer_artifact_binding_hash: str
    as_of_utc: str
    logical_hash: str
    evidence_scope: EvidenceScope = EvidenceScope.CANDIDATE_WIDE
    source_family_id: str | None = None
    source_authority_class: str | None = None
    reason_codes: tuple[str, ...] = ()
    producer_receipt_id: str = ""
    producer_receipt_logical_hash: str = ""
    target_feature_ids: tuple[str, ...] = ()
    schema_version: str = SCHEMA_GOVERNED_EVIDENCE_BINDING_V1

    def calculated_logical_hash(self) -> str:
        material = {key: value for key, value in asdict(self).items() if key != "logical_hash"}
        return logical_hash(material)

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_GOVERNED_EVIDENCE_BINDING_V1:
            blockers.append("unknown_governed_evidence_binding_schema")
        if not self.evidence_ref or not IDENTIFIER_RE.fullmatch(self.evidence_ref):
            blockers.append("malformed_evidence_ref")
        if self.authority_state not in KNOWN_GOVERNED_EVIDENCE_AUTHORITY_STATES:
            blockers.append("unknown_evidence_authority_state")
        if self.permission_state not in KNOWN_GOVERNED_EVIDENCE_PERMISSION_STATES:
            blockers.append("unknown_evidence_permission_state")
        if not self.evidence_roles:
            blockers.append("missing_evidence_roles")
        if len(self.evidence_roles) != len(set(self.evidence_roles)):
            blockers.append("duplicate_evidence_role")
        if any(not isinstance(value, EvidenceRole) for value in self.evidence_roles):
            blockers.append("unknown_evidence_role")
        if not isinstance(self.evidence_scope, EvidenceScope):
            blockers.append("unknown_evidence_scope")
        if not isinstance(self.verification_status, EvidenceVerificationStatus):
            blockers.append("unknown_evidence_verification_status")
        for name, value in (("verifier_id", self.verifier_id), ("verifier_version", self.verifier_version)):
            if not value or not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if not SHA256_RE.fullmatch(self.producer_artifact_binding_hash or ""):
            blockers.append("malformed_producer_artifact_binding_hash")
        if not self.producer_receipt_id or not IDENTIFIER_RE.fullmatch(self.producer_receipt_id):
            blockers.append("malformed_producer_receipt_id")
        if not SHA256_RE.fullmatch(self.producer_receipt_logical_hash or ""):
            blockers.append("malformed_producer_receipt_logical_hash")
        blockers.extend(_validate_identifier_values(self.target_feature_ids, "target_feature_id"))
        try:
            parse_utc(self.as_of_utc, field_name="evidence_as_of_utc")
        except ValueError as error:
            blockers.append(str(error))
        for name, value in (("source_family_id", self.source_family_id), ("source_authority_class", self.source_authority_class)):
            if value is not None and not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if not SHA256_RE.fullmatch(self.logical_hash or ""):
            blockers.append("malformed_evidence_logical_hash")
        elif self.logical_hash != self.calculated_logical_hash():
            blockers.append("evidence_logical_hash_mismatch")
        return _unique(blockers)

    def qualifies_for_governed_outcome(self) -> bool:
        return bool(
            not self.validate()
            and self.authority_state in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
            and self.permission_state in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
            and self.verification_status == EvidenceVerificationStatus.VERIFIED
            and not (set(self.reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES)
        )


def build_evidence_reference_v1(
    *, evidence_ref: str, authority_state: str, permission_state: str,
    evidence_roles: Sequence[EvidenceRole], producer_artifact_binding_hash: str,
    as_of_utc: str, evidence_scope: EvidenceScope,
    verifier_id: str = "contentops.evidence_reference_verifier",
    verifier_version: str = "v1",
    verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.VERIFIED,
    modality: EvidenceModality | None = None,
    observed_at_utc: str | None = None,
    reason_codes: Sequence[str] = (),
    temporal_character: TemporalCharacter | None = None,
    source_family_id: str | None = None,
    source_authority_class: str | None = None,
    producer_receipt_id: str | None = None,
    producer_receipt_logical_hash: str | None = None,
    target_feature_ids: Sequence[str] = (),
) -> EvidenceReferenceV1:
    values = dict(
        evidence_ref=evidence_ref, authority_state=authority_state,
        permission_state=permission_state, modality=modality,
        observed_at_utc=observed_at_utc, reason_codes=tuple(reason_codes),
        temporal_character=temporal_character, source_family_id=source_family_id,
        source_authority_class=source_authority_class,
        evidence_roles=tuple(evidence_roles), evidence_scope=evidence_scope,
        verifier_id=verifier_id, verifier_version=verifier_version,
        verification_status=verification_status,
        producer_artifact_binding_hash=producer_artifact_binding_hash,
        producer_receipt_id=producer_receipt_id,
        producer_receipt_logical_hash=producer_receipt_logical_hash,
        target_feature_ids=tuple(target_feature_ids),
        as_of_utc=as_of_utc, logical_hash=None,
    )
    draft = EvidenceReferenceV1(**values)
    return EvidenceReferenceV1(**{**values, "logical_hash": draft.calculated_logical_hash()})


def build_governed_evidence_binding_v1(
    *, evidence_ref: str, evidence_roles: Sequence[EvidenceRole],
    producer_artifact_binding_hash: str, as_of_utc: str,
    authority_state: str = "VERIFIED_GOVERNED",
    permission_state: str = "REPORTING_ALLOWED",
    verifier_id: str = "contentops.governed_evidence_verifier",
    verifier_version: str = "v1",
    verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.VERIFIED,
    evidence_scope: EvidenceScope = EvidenceScope.CANDIDATE_WIDE,
    source_family_id: str | None = None,
    source_authority_class: str | None = None,
    reason_codes: Sequence[str] = (),
    producer_receipt_id: str = "",
    producer_receipt_logical_hash: str = "",
    target_feature_ids: Sequence[str] = (),
) -> GovernedEvidenceBindingV1:
    values = dict(
        evidence_ref=evidence_ref, authority_state=authority_state,
        permission_state=permission_state, evidence_roles=tuple(evidence_roles),
        verifier_id=verifier_id, verifier_version=verifier_version,
        verification_status=verification_status,
        producer_artifact_binding_hash=producer_artifact_binding_hash,
        as_of_utc=as_of_utc, logical_hash="", evidence_scope=evidence_scope,
        source_family_id=source_family_id,
        source_authority_class=source_authority_class,
        reason_codes=tuple(reason_codes),
        producer_receipt_id=producer_receipt_id,
        producer_receipt_logical_hash=producer_receipt_logical_hash,
        target_feature_ids=tuple(target_feature_ids),
    )
    draft = GovernedEvidenceBindingV1(**values)
    return GovernedEvidenceBindingV1(**{**values, "logical_hash": draft.calculated_logical_hash()})


@dataclass(frozen=True)
class PlatformVariantV1:
    platform_variant_id: str
    platform_id: str
    publication_timestamp_utc: str | None
    payload_hash: str
    current: bool = True


@dataclass(frozen=True)
class ArticleVersionV1:
    article_version_id: str
    body_authority: str
    body_sha256: str
    current: bool
    supersedes_article_version_id: str | None = None
    correction_refs: tuple[str, ...] = ()
    bounded_repair_refs: tuple[str, ...] = ()
    created_at_utc: str | None = None


@dataclass(frozen=True)
class PublishedContentItemV1:
    content_item_id: str
    story_id: str
    candidate_id: str | None
    cluster_id: str | None
    update_chain_id: str | None
    article_versions: tuple[ArticleVersionV1, ...] = ()
    platform_variants: tuple[PlatformVariantV1, ...] = ()
    source_refs: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    current_article_version_id: str | None = None
    superseded: bool = False


@dataclass(frozen=True)
class PublishedContentHistoryV1:
    history_id: str
    items: tuple[PublishedContentItemV1, ...] = ()
    schema_version: str = SCHEMA_HISTORY_V1

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        ids = [item.content_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            blockers.append("duplicate_content_item_id")
        for item in self.items:
            if not item.content_item_id:
                blockers.append("empty_content_item_id")
            if not item.story_id:
                blockers.append(f"empty_story_id:{item.content_item_id}")
            if item.cluster_id and not item.update_chain_id:
                blockers.append(f"cluster_requires_update_chain:{item.content_item_id}")
            version_ids = [row.article_version_id for row in item.article_versions]
            if len(version_ids) != len(set(version_ids)):
                blockers.append(f"duplicate_article_version_id:{item.content_item_id}")
            variant_ids = [row.platform_variant_id for row in item.platform_variants]
            if len(variant_ids) != len(set(variant_ids)):
                blockers.append(f"duplicate_platform_variant_id:{item.content_item_id}")
            versions = {row.article_version_id: row for row in item.article_versions}
            if item.current_article_version_id and item.current_article_version_id not in versions:
                blockers.append(f"current_article_version_missing:{item.content_item_id}")
            current_rows = [row for row in item.article_versions if row.current]
            if item.current_article_version_id and len(current_rows) != 1:
                blockers.append(f"exactly_one_current_article_version_required:{item.content_item_id}")
            if len(current_rows) > 1:
                blockers.append(f"multiple_current_article_versions:{item.content_item_id}")
            if item.current_article_version_id in versions and not versions[item.current_article_version_id].current:
                blockers.append(f"current_article_version_not_current:{item.content_item_id}")
            if item.superseded and current_rows:
                blockers.append(f"superseded_item_cannot_have_current_version:{item.content_item_id}")
            for row in item.article_versions:
                if not row.article_version_id:
                    blockers.append(f"empty_article_version_id:{item.content_item_id}")
                if not SHA256_RE.fullmatch(row.body_sha256):
                    blockers.append(f"invalid_body_sha256:{row.article_version_id}")
                parent = row.supersedes_article_version_id
                if parent == row.article_version_id:
                    blockers.append(f"article_version_self_supersession:{row.article_version_id}")
                elif parent and parent not in versions:
                    blockers.append(f"superseded_article_version_missing:{row.article_version_id}")
                if row.created_at_utc:
                    try:
                        parse_utc(row.created_at_utc, field_name="article_version_created_at_utc")
                    except ValueError as error:
                        blockers.append(f"{error}:{row.article_version_id}")
            for start in version_ids:
                seen: set[str] = set()
                cursor: str | None = start
                while cursor and cursor in versions:
                    if cursor in seen:
                        blockers.append(f"article_version_cycle:{item.content_item_id}")
                        break
                    seen.add(cursor)
                    cursor = versions[cursor].supersedes_article_version_id
            for row in item.platform_variants:
                if not row.platform_variant_id or not row.platform_id:
                    blockers.append(f"invalid_platform_variant_identity:{item.content_item_id}")
                if not SHA256_RE.fullmatch(row.payload_hash):
                    blockers.append(f"invalid_payload_hash:{row.platform_variant_id}")
                if row.publication_timestamp_utc:
                    try:
                        parse_utc(row.publication_timestamp_utc, field_name="publication_timestamp_utc")
                    except ValueError as error:
                        blockers.append(f"{error}:{row.platform_variant_id}")
        return _unique(blockers)


@dataclass(frozen=True)
class GovernedCandidatePoolBindingV1:
    repository: str
    branch: str
    producer_commit: str
    artifact_path: str
    git_blob_sha1: str | None
    consumed_byte_sha256: str
    schema_version: str
    producer_version: str
    pool_id: str
    logical_hash: str
    cutoff_time_utc: str | None
    candidate_hashes: Mapping[str, str]
    source_family_coverage: tuple[str, ...]
    immutable_binding_status: str
    binding_id: str = ""
    contract_schema_version: str = SCHEMA_POOL_BINDING_V1


@dataclass(frozen=True)
class ArtifactVerificationResultV1:
    verification_id: str
    status: str
    actual_byte_sha256: str
    actual_git_blob_sha1: str
    calculated_logical_hash: str | None
    candidate_hashes_verified: int
    point_in_time_fields_checked: int
    blockers: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True)
class ContentGapFindingV1:
    gap_id: str
    gap_type: GapType
    finding: str
    evidence_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    actionable: bool = False


@dataclass(frozen=True)
class ContentGapSetV1:
    gap_set_id: str
    findings: tuple[ContentGapFindingV1, ...] = ()
    idea_ids: tuple[str, ...] = ()
    schema_version: str = SCHEMA_GAP_SET_V1

    def validate(self, *, disallow_duplicate_logical_findings: bool = False) -> tuple[str, ...]:
        blockers: list[str] = []
        gap_ids = [row.gap_id for row in self.findings]
        if len(gap_ids) != len(set(gap_ids)):
            blockers.append("duplicate_gap_id")
        if len(self.idea_ids) != len(set(self.idea_ids)):
            blockers.append("duplicate_idea_id")
        blockers.extend(_validate_identifier_values(self.idea_ids, "idea_id"))
        logical_findings: set[tuple[str, str]] = set()
        for row in self.findings:
            if not row.gap_id:
                blockers.append("empty_gap_id")
            if not isinstance(row.gap_type, GapType):
                blockers.append(f"invalid_gap_type:{row.gap_id}")
            if not row.finding.strip():
                blockers.append(f"empty_gap_finding:{row.gap_id}")
            if row.actionable and not row.evidence_refs:
                blockers.append(f"actionable_gap_requires_evidence:{row.gap_id}")
            if len(row.evidence_refs) != len(set(row.evidence_refs)):
                blockers.append(f"duplicate_gap_evidence_ref:{row.gap_id}")
            identity = (row.gap_type.value if isinstance(row.gap_type, GapType) else str(row.gap_type), row.finding.strip().casefold())
            if disallow_duplicate_logical_findings and identity in logical_findings:
                blockers.append("duplicate_logical_gap_finding")
            logical_findings.add(identity)
        return _unique(blockers)


@dataclass(frozen=True)
class PerformanceObservationV1:
    observation_id: str
    content_item_id: str
    story_id: str
    update_chain_id: str
    platform_variant_id: str
    metric_name: str
    metric_value: float | None
    availability: AvailabilityState
    authority_class: MetricAuthorityClass
    observed_at_utc: str | None = None
    unavailable_reason: str | None = None
    evidence_refs: tuple[str, ...] = ()
    metric_scope: str = "content_item_platform_variant"

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        for name, value in (
            ("observation_id", self.observation_id),
            ("content_item_id", self.content_item_id),
            ("story_id", self.story_id),
            ("update_chain_id", self.update_chain_id),
            ("platform_variant_id", self.platform_variant_id),
        ):
            if not value or not IDENTIFIER_RE.fullmatch(value):
                blockers.append(f"malformed_{name}")
        if not self.metric_name.strip() or not self.metric_scope.strip():
            blockers.append("metric_name_and_scope_required")
        if isinstance(self.metric_value, bool) or (self.metric_value is not None and not math.isfinite(float(self.metric_value))):
            blockers.append("metric_value_must_be_finite_numeric_or_null")
        if self.availability == AvailabilityState.EXPLICIT_ZERO and self.metric_value != 0:
            blockers.append("explicit_zero_requires_numeric_zero")
        if self.availability == AvailabilityState.AVAILABLE and self.metric_value is None:
            blockers.append("available_metric_requires_value")
        if self.availability in {AvailabilityState.UNAVAILABLE, AvailabilityState.BLOCKED, AvailabilityState.UNSUPPORTED}:
            if self.metric_value is not None:
                blockers.append("unavailable_state_must_not_carry_value")
            if not self.unavailable_reason:
                blockers.append("unavailable_state_requires_reason")
        if self.availability in {AvailabilityState.AVAILABLE, AvailabilityState.EXPLICIT_ZERO} and self.authority_class == MetricAuthorityClass.UNAVAILABLE:
            blockers.append("metric_bearing_observation_requires_authority")
        if self.availability == AvailabilityState.UNAVAILABLE and self.authority_class != MetricAuthorityClass.UNAVAILABLE:
            blockers.append("unavailable_observation_requires_unavailable_authority_class")
        if self.observed_at_utc:
            try:
                parse_utc(self.observed_at_utc, field_name="observation_observed_at_utc")
            except ValueError as error:
                blockers.append(str(error))
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            blockers.append("duplicate_observation_evidence_ref")
        return _unique(blockers)


@dataclass(frozen=True)
class PerformanceObservationSetV1:
    observation_set_id: str
    observations: tuple[PerformanceObservationV1, ...] = ()
    schema_version: str = SCHEMA_OBSERVATION_SET_V1

    def cardinalities(self) -> Mapping[str, int]:
        return {
            "observation_count": len(self.observations),
            "metric_bearing_observation_count": sum(
                row.availability in {AvailabilityState.AVAILABLE, AvailabilityState.EXPLICIT_ZERO}
                for row in self.observations
            ),
            "platform_variant_count": len({row.platform_variant_id for row in self.observations}),
            "distinct_content_count": len({row.content_item_id for row in self.observations}),
            "distinct_story_count": len({row.story_id for row in self.observations}),
            "distinct_update_chain_count": len({row.update_chain_id for row in self.observations}),
        }

    def authority_counts(self) -> Mapping[str, int]:
        return {
            authority.value: sum(row.authority_class == authority for row in self.observations)
            for authority in MetricAuthorityClass
        }

    def validate(self) -> tuple[str, ...]:
        blockers = [blocker for observation in self.observations for blocker in observation.validate()]
        ids = [row.observation_id for row in self.observations]
        if len(ids) != len(set(ids)):
            blockers.append("duplicate_observation_id")
        collision_keys: set[tuple[str, str, str, str]] = set()
        identity_map: dict[str, tuple[str, str]] = {}
        for row in self.observations:
            key = (row.content_item_id, row.platform_variant_id, row.metric_name, row.observed_at_utc or "unavailable")
            if key in collision_keys:
                blockers.append("duplicate_observation_collision")
            collision_keys.add(key)
            identity = (row.story_id, row.update_chain_id)
            if row.content_item_id in identity_map and identity_map[row.content_item_id] != identity:
                blockers.append(f"observation_content_identity_mismatch:{row.content_item_id}")
            identity_map[row.content_item_id] = identity
        return _unique(blockers)


@dataclass(frozen=True)
class FeatureDefinitionV1:
    feature_id: str
    normalization: str
    weight: float
    penalty: bool
    minimum_evidence: int
    authority_gate: str | None
    domain_applicability: tuple[str, ...]
    unavailable_handling: str


@dataclass(frozen=True)
class AdaptiveLearningConfigV1:
    config_version: str
    calibration_state: CalibrationState
    features: tuple[FeatureDefinitionV1, ...]
    thresholds: Mapping[str, float]
    authority_gates: Mapping[str, bool]
    normalization_rules: Mapping[str, Mapping[str, Any]]
    threshold_rules: Mapping[str, Mapping[str, Any]]
    unavailable_handling: Mapping[str, str]
    config_logical_hash: str
    schema_version: str = SCHEMA_CONFIG_V1

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.schema_version != SCHEMA_CONFIG_V1:
            blockers.append("config_schema_version_mismatch")
        if not self.config_version.strip():
            blockers.append("config_version_empty")
        ids = [row.feature_id for row in self.features]
        if len(ids) != len(set(ids)):
            blockers.append("duplicate_feature_id")
        if self.calibration_state != CalibrationState.UNCALIBRATED_FOUNDATION:
            blockers.append("foundation_config_must_be_uncalibrated")
        if not self.features:
            blockers.append("feature_registry_empty")
        material = primitive(self)
        material.pop("config_logical_hash", None)
        if logical_hash(material) != self.config_logical_hash:
            blockers.append("config_logical_hash_mismatch")
        for row in self.features:
            if not row.feature_id or not IDENTIFIER_RE.fullmatch(row.feature_id):
                blockers.append("feature_id_malformed")
            if isinstance(row.weight, bool) or not isinstance(row.weight, (int, float)) or not math.isfinite(float(row.weight)):
                blockers.append(f"feature_weight_not_finite:{row.feature_id}")
            if isinstance(row.minimum_evidence, bool) or not isinstance(row.minimum_evidence, int) or row.minimum_evidence < 0:
                blockers.append(f"minimum_evidence_invalid:{row.feature_id}")
            if not isinstance(row.penalty, bool):
                blockers.append(f"penalty_flag_invalid:{row.feature_id}")
            if row.normalization not in self.normalization_rules:
                blockers.append(f"normalization_rule_missing:{row.feature_id}")
            if row.authority_gate is not None and row.authority_gate not in self.authority_gates:
                blockers.append(f"authority_gate_missing:{row.feature_id}")
            if row.unavailable_handling not in self.unavailable_handling:
                blockers.append(f"unavailable_rule_missing:{row.feature_id}")
            if not row.domain_applicability:
                blockers.append(f"domain_applicability_empty:{row.feature_id}")
            elif any(not isinstance(value, str) or not value.strip() for value in row.domain_applicability):
                blockers.append(f"domain_applicability_invalid:{row.feature_id}")
        supported_normalizations = {"boolean", "bounded_0_1", "min_max", "inverse_min_max"}
        for name, rule in self.normalization_rules.items():
            kind = rule.get("kind")
            if kind not in supported_normalizations or kind != name:
                blockers.append(f"normalization_kind_invalid:{name}")
            if kind in {"min_max", "inverse_min_max"}:
                minimum, maximum = rule.get("minimum"), rule.get("maximum")
                if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in (minimum, maximum)):
                    blockers.append(f"normalization_bounds_not_finite:{name}")
                elif float(maximum) <= float(minimum):
                    blockers.append(f"normalization_bounds_invalid:{name}")
        if set(self.thresholds) != set(self.threshold_rules):
            blockers.append("threshold_rule_keys_mismatch")
        for name, value in self.thresholds.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                blockers.append(f"threshold_not_finite:{name}")
                continue
            rule = self.threshold_rules.get(name, {})
            minimum, maximum = rule.get("minimum"), rule.get("maximum")
            if minimum is not None and float(value) < float(minimum):
                blockers.append(f"threshold_below_minimum:{name}")
            if maximum is not None and float(value) > float(maximum):
                blockers.append(f"threshold_above_maximum:{name}")
            if rule.get("integer") is True and not float(value).is_integer():
                blockers.append(f"threshold_requires_integer:{name}")
            if rule.get("kind") not in {"count", "duration_hours", "bounded_0_1"}:
                blockers.append(f"threshold_kind_invalid:{name}")
        for name, value in self.authority_gates.items():
            if not IDENTIFIER_RE.fullmatch(name) or not isinstance(value, bool):
                blockers.append(f"authority_gate_invalid:{name}")
        missing_canonical_gates = CANONICAL_AUTHORITY_GATE_IDS - set(self.authority_gates)
        for name in sorted(missing_canonical_gates):
            blockers.append(f"canonical_authority_gate_missing:{name}")
        for name in sorted(CANONICAL_AUTHORITY_GATE_IDS & set(self.authority_gates)):
            if self.authority_gates[name] is not True:
                blockers.append(f"canonical_authority_gate_must_be_enabled:{name}")
        for name, value in self.unavailable_handling.items():
            if not IDENTIFIER_RE.fullmatch(name) or not isinstance(value, str) or not value.strip():
                blockers.append(f"unavailable_handling_invalid:{name}")
        return _unique(blockers)


@dataclass(frozen=True)
class FeatureEvaluationV1:
    feature_id: str
    applicable: bool
    availability: AvailabilityState
    unavailable_reason: str | None
    raw_value: float | bool | None
    normalization_method: str
    normalized_value: float | None
    configured_weight: float
    contribution: float | None
    penalty: float | None
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    capability_dimensions_used: tuple[str, ...] = ()
    normalization_parameters: Mapping[str, Any] = field(default_factory=dict)
    evidence_count: int = 0
    configured_minimum_evidence: int = 0
    authority_gate_id: str | None = None
    authority_gate_result: bool | None = None
    domain_applicability_result: bool = True
    evidence_roles: tuple[EvidenceRole, ...] = ()
    evidence_scope: EvidenceScope = EvidenceScope.FEATURE_SPECIFIC
    excluded_evidence_refs: tuple[str, ...] = ()
    evidence_exclusion_reasons: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    target_feature_id: str | None = None
    resolved_evidence_types: tuple[str, ...] = ()
    producer_receipt_ids: tuple[str, ...] = ()
    verifier_id_versions: tuple[str, ...] = ()
    point_in_time_result: str = "NOT_EVALUATED"


@dataclass(frozen=True)
class DisqualifiedEvidenceV1:
    evidence_ref: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeDecisionV1:
    source_relationship: EventRelationship
    evidence_state: str
    authority_state: str
    history_relationship: str
    content_gap_state: str
    actionable_outcomes: tuple[str, ...]
    publication_disposition: str
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    authority_result: bool = False
    reporting_permission_result: bool = False
    history_identity_match: bool = False
    governed_delta_present: bool = False
    qualifying_governed_evidence_refs: tuple[str, ...] = ()
    complete_evidence_lineage: tuple[str, ...] = ()
    relationship_specific_qualifying_refs: tuple[str, ...] = ()
    historical_only_refs: tuple[str, ...] = ()
    disqualified_evidence: tuple[DisqualifiedEvidenceV1, ...] = ()


@dataclass(frozen=True)
class RankingRowV1:
    candidate_id: str
    story_id: str
    update_chain_id: str
    features: tuple[FeatureEvaluationV1, ...]
    score: float
    rank: int
    selected_internal_brief_ids: tuple[str, ...]
    publication_disposition: str


@dataclass(frozen=True)
class ModelAssistedJudgmentV1:
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str
    input_hash: str
    output_hash: str
    structured_schema: str
    confidence: str
    validation_result: str
    rationale: str
    evidence_refs: tuple[str, ...]
    grants_authority: bool = False
    grants_publication_permission: bool = False
    grants_reporting_permission: bool = False
    grants_dqr_override: bool = False
    grants_factual_truth: bool = False
    grants_numeric_truth: bool = False
    grants_citation_waiver: bool = False
    grants_risk_language_waiver: bool = False
    grants_automatic_scheduling: bool = False
    grants_automatic_publication: bool = False
    schema_version: str = SCHEMA_MODEL_JUDGMENT_V1

    def validate(self) -> tuple[str, ...]:
        blockers = []
        if self.grants_authority:
            blockers.append("model_must_not_grant_authority")
        if self.grants_publication_permission:
            blockers.append("model_must_not_grant_publication_permission")
        for field_name in (
            "grants_reporting_permission", "grants_dqr_override", "grants_factual_truth",
            "grants_numeric_truth", "grants_citation_waiver", "grants_risk_language_waiver",
            "grants_automatic_scheduling", "grants_automatic_publication",
        ):
            if getattr(self, field_name):
                blockers.append("model_must_not_" + field_name.removeprefix("grants_"))
        return tuple(blockers)


@dataclass(frozen=True)
class ContentOpsLearningDecisionV2:
    decision_id: str
    prior_decision_id: str | None
    prior_decision_logical_hash: str | None
    supersession_reason: str | None
    config_version: str
    config_logical_hash: str
    input_bindings: Mapping[str, str]
    input_binding_hash: str
    content_history_hash: str
    gap_set_hash: str
    observation_set_hash: str
    candidate_cohort_hash: str
    cohort_identity: str
    observation_cardinalities: Mapping[str, int]
    feature_availability: Mapping[str, str]
    outcome_matrix: tuple[Mapping[str, Any], ...]
    authority_matrix: tuple[Mapping[str, Any], ...]
    ranking_rows: tuple[RankingRowV1, ...]
    selected_internal_briefs: tuple[str, ...]
    no_publication_decisions: tuple[Mapping[str, Any], ...]
    proposals: tuple[Mapping[str, Any], ...]
    confidence: str
    calibration_state: CalibrationState
    forbidden_effects_checked: tuple[str, ...]
    operator_state: str
    logical_time_basis: str
    decision_cutoff_utc: str
    verifier_registry_version: str
    verifier_registry_logical_hash: str
    logical_hash: str
    schema_version: str = SCHEMA_DECISION_V2


def _git_blob_sha1(data: bytes) -> str:
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def build_verified_producer_artifact_receipt_v1(
    consumed_bytes: bytes,
    *,
    registry: TrustedVerifierRegistryV1,
    verifier_id: str,
    verifier_version: str,
    repository: str,
    branch: str,
    producer_commit: str,
    artifact_path: str,
    expected_git_blob_sha1: str,
    artifact_schema_version: str,
    producer_version: str,
    artifact_cutoff_utc: str,
    evidence_refs: Sequence[str],
    source_authority_class: str,
    declared_artifact_logical_hash: str | None = None,
    resolved_repository: str | None = None,
    resolved_branch: str | None = None,
    resolved_commit: str | None = None,
    resolved_artifact_path: str | None = None,
    branch_head_observed: str | None = None,
    producer_commit_reachable_from_branch: bool = True,
    verification_time_utc: str | None = None,
) -> VerifiedProducerArtifactReceiptV1:
    """Create a receipt only after exact consumed bytes match the Git blob binding."""
    registry_blockers = registry.validate()
    if registry_blockers:
        raise ValueError("invalid_trusted_verifier_registry:" + ",".join(registry_blockers))
    verifier = registry.resolve(verifier_id, verifier_version)
    if verifier is None:
        raise ValueError("unknown_verifier_id_version")
    if not verifier.enabled:
        raise ValueError("trusted_verifier_disabled")
    if verifier.implementation_contract_id != "contentops.exact_git_artifact_verifier.v1":
        raise ValueError("verifier_implementation_contract_mismatch")
    if repository not in verifier.allowed_repositories:
        raise ValueError("verifier_repository_not_allowed")
    if resolved_repository != repository:
        raise ValueError("producer_repository_identity_mismatch")
    if resolved_branch != branch:
        raise ValueError("producer_branch_identity_mismatch")
    if resolved_commit != producer_commit:
        raise ValueError("producer_commit_identity_mismatch")
    if resolved_artifact_path != artifact_path:
        raise ValueError("producer_artifact_path_identity_mismatch")
    if artifact_schema_version not in verifier.allowed_artifact_schema_versions:
        raise ValueError("verifier_artifact_schema_not_allowed")
    if source_authority_class not in verifier.allowed_source_authority_classes:
        raise ValueError("verifier_source_authority_class_not_allowed")
    actual_blob = _git_blob_sha1(consumed_bytes)
    if not SHA1_RE.fullmatch(expected_git_blob_sha1 or "") or actual_blob != expected_git_blob_sha1:
        raise ValueError("producer_git_blob_mismatch")
    if not COMMIT_RE.fullmatch(producer_commit or ""):
        raise ValueError("producer_commit_malformed")
    parsed: Any
    try:
        parsed = json.loads(consumed_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = {"byte_sha256": sha256(consumed_bytes).hexdigest()}
    artifact_hash = logical_hash(parsed)
    if declared_artifact_logical_hash is not None and declared_artifact_logical_hash != artifact_hash:
        raise ValueError("producer_artifact_logical_hash_mismatch")
    byte_hash = sha256(consumed_bytes).hexdigest()
    receipt_material = {
        "repository": repository,
        "branch": branch,
        "producer_commit": producer_commit,
        "artifact_path": artifact_path,
        "git_blob_sha1": actual_blob,
        "consumed_byte_sha256": byte_hash,
        "artifact_schema_version": artifact_schema_version,
        "producer_version": producer_version,
        "artifact_logical_hash": artifact_hash,
        "artifact_cutoff_utc": artifact_cutoff_utc,
        "verification_status": EvidenceVerificationStatus.VERIFIED,
        "verifier_id": verifier_id,
        "verifier_version": verifier_version,
        "implementation_contract_id": verifier.implementation_contract_id,
        "registry_version": registry.registry_version,
        "registry_logical_hash": registry.registry_logical_hash,
        "evidence_refs": _unique(evidence_refs),
        "evidence_ref_derivations": {
            ref: logical_hash({
                "artifact_logical_hash": artifact_hash,
                "evidence_ref": ref,
                "derivation_contract": "contentops.artifact_evidence_ref_derivation.v1",
            })
            for ref in _unique(evidence_refs)
        },
        "source_authority_class": source_authority_class,
        "branch_head_observed": branch_head_observed or producer_commit,
        "producer_commit_reachable_from_branch": producer_commit_reachable_from_branch,
        "verification_time_utc": verification_time_utc or artifact_cutoff_utc,
        "schema_version": SCHEMA_PRODUCER_ARTIFACT_RECEIPT_V1,
    }
    identity = logical_hash(receipt_material)
    values = {
        **receipt_material,
        "receipt_id": "producer_receipt:" + identity[:24],
        "logical_hash": "",
    }
    draft = VerifiedProducerArtifactReceiptV1(**values)
    receipt = VerifiedProducerArtifactReceiptV1(**{**values, "logical_hash": draft.calculated_logical_hash()})
    blockers = receipt.validate()
    if blockers:
        raise ValueError("invalid_producer_receipt:" + ",".join(blockers))
    return receipt


def trusted_evidence_blockers(
    evidence: EvidenceReferenceV1 | GovernedEvidenceBindingV1,
    context: EvidenceDecisionContextV1,
    *,
    required_role: EvidenceRole | None = None,
    required_scope: EvidenceScope | None = None,
    target_feature_id: str | None = None,
) -> tuple[str, ...]:
    """Validate registry, receipt, state, role/scope, and point-in-time binding."""
    blockers = list(context.validate())
    verifier = context.verifier_registry.resolve(evidence.verifier_id or "", evidence.verifier_version or "")
    if verifier is None:
        blockers.append("unknown_verifier_id_version")
        return _unique(blockers)
    if not verifier.enabled:
        blockers.append("trusted_verifier_disabled")
    receipt = next((row for row in context.producer_receipts if row.receipt_id == evidence.producer_receipt_id), None)
    if receipt is None:
        blockers.append("producer_receipt_missing")
        return _unique(blockers)
    if receipt.logical_hash != evidence.producer_receipt_logical_hash:
        blockers.append("producer_receipt_hash_mismatch")
    if receipt.consumed_byte_sha256 != evidence.producer_artifact_binding_hash:
        blockers.append("producer_byte_hash_mismatch")
    if receipt.verifier_id != evidence.verifier_id or receipt.verifier_version != evidence.verifier_version:
        blockers.append("producer_receipt_verifier_mismatch")
    if receipt.implementation_contract_id != verifier.implementation_contract_id:
        blockers.append("producer_receipt_implementation_contract_mismatch")
    if receipt.artifact_schema_version not in verifier.allowed_artifact_schema_versions:
        blockers.append("producer_receipt_schema_not_allowed")
    if receipt.repository not in verifier.allowed_repositories:
        blockers.append("producer_receipt_repository_not_allowed")
    if receipt.source_authority_class not in verifier.allowed_source_authority_classes:
        blockers.append("producer_receipt_authority_class_not_allowed")
    if evidence.source_authority_class and evidence.source_authority_class not in verifier.allowed_source_authority_classes:
        blockers.append("evidence_authority_class_not_allowed")
    if evidence.authority_state not in verifier.allowed_authority_states:
        blockers.append("evidence_authority_state_not_allowed")
    if evidence.permission_state not in verifier.allowed_permission_states:
        blockers.append("evidence_permission_state_not_allowed")
    if (
        evidence.authority_state in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
        and evidence.permission_state in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
        and set(evidence.reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES
    ):
        blockers.append("contradictory_qualification_reason_codes")
    if any(role not in verifier.allowed_evidence_roles for role in evidence.evidence_roles):
        blockers.append("evidence_role_not_allowed")
    if evidence.evidence_scope not in verifier.allowed_evidence_scopes:
        blockers.append("evidence_scope_not_allowed")
    if required_role is not None and required_role not in evidence.evidence_roles:
        blockers.append("required_evidence_role_missing")
    if required_scope is not None and evidence.evidence_scope != required_scope:
        blockers.append("required_evidence_scope_mismatch")
    if evidence.evidence_scope == EvidenceScope.CANDIDATE_WIDE and not verifier.candidate_wide_reuse_allowed:
        blockers.append("candidate_wide_reuse_not_allowed")
    if target_feature_id is not None and evidence.evidence_scope == EvidenceScope.FEATURE_SPECIFIC and target_feature_id not in evidence.target_feature_ids:
        blockers.append("feature_target_mismatch")
    extracted = next((row for row in context.extracted_evidence_records if row.evidence_ref == evidence.evidence_ref), None)
    if context.extractor_registry is not None:
        if extracted is None:
            blockers.append("evidence_ref_absent_from_extracted_records")
        else:
            extractor = context.extractor_registry.resolve(extracted.extractor_id, extracted.extractor_version)
            if extractor is None:
                blockers.append("unsupported_extractor")
            elif not extractor.enabled:
                blockers.append("extractor_disabled")
            if extracted.producer_receipt_id != receipt.receipt_id or extracted.producer_receipt_logical_hash != receipt.logical_hash:
                blockers.append("extracted_record_receipt_mismatch")
            if extracted.source_authority_class != receipt.source_authority_class:
                blockers.append("extracted_record_authority_class_mismatch")
            if evidence.authority_state != extracted.authority_state:
                if AUTHORITY_STATE_RANK.get(evidence.authority_state, 99) >= AUTHORITY_STATE_RANK.get(extracted.authority_state, -1):
                    blockers.append("evidence_authority_upgrade_from_extracted_record")
                elif "caller_authority_narrowed" not in evidence.reason_codes:
                    blockers.append("evidence_authority_narrowing_reason_missing")
            if evidence.permission_state != extracted.permission_state:
                if PERMISSION_STATE_RANK.get(evidence.permission_state, 99) >= PERMISSION_STATE_RANK.get(extracted.permission_state, -1):
                    blockers.append("evidence_permission_upgrade_from_extracted_record")
                elif "caller_permission_narrowed" not in evidence.reason_codes:
                    blockers.append("evidence_permission_narrowing_reason_missing")
            if not set(evidence.evidence_roles).issubset(set(extracted.evidence_roles)):
                blockers.append("evidence_roles_absent_from_extracted_record")
            if evidence.evidence_scope != extracted.evidence_scope and not (
                extracted.evidence_scope == EvidenceScope.CANDIDATE_WIDE
                and evidence.evidence_scope == EvidenceScope.FEATURE_SPECIFIC
            ):
                blockers.append("evidence_scope_absent_from_extracted_record")
            if not set(evidence.target_feature_ids).issubset(set(extracted.feature_targets)):
                blockers.append("feature_targets_absent_from_extracted_record")
            expected_reasons = list(extracted.qualification_reason_codes)
            if evidence.authority_state != extracted.authority_state:
                expected_reasons.append("caller_authority_narrowed")
            if evidence.permission_state != extracted.permission_state:
                expected_reasons.append("caller_permission_narrowed")
            if tuple(evidence.reason_codes) != _unique(expected_reasons):
                blockers.append("evidence_qualification_reason_mismatch")
            derived_qualifying = bool(
                evidence.authority_state in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
                and evidence.permission_state in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
                and not (set(evidence.reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES)
            )
            if derived_qualifying and extracted.qualification_status != "QUALIFYING_GOVERNED":
                blockers.append("evidence_qualification_status_mismatch")
            elif (
                evidence.authority_state == extracted.authority_state
                and evidence.permission_state == extracted.permission_state
                and derived_qualifying != (extracted.qualification_status == "QUALIFYING_GOVERNED")
            ):
                blockers.append("evidence_qualification_status_mismatch")
    elif evidence.evidence_ref not in receipt.evidence_refs:
        blockers.append("evidence_ref_absent_from_producer_receipt")
    else:
        expected_derivation = logical_hash({
            "artifact_logical_hash": receipt.artifact_logical_hash,
            "evidence_ref": evidence.evidence_ref,
            "derivation_contract": "contentops.artifact_evidence_ref_derivation.v1",
        })
        if receipt.evidence_ref_derivations.get(evidence.evidence_ref) != expected_derivation:
            blockers.append("evidence_ref_derivation_mismatch")
    try:
        cutoff = parse_utc(context.decision_cutoff_utc)
        as_of = parse_utc(evidence.as_of_utc or "", field_name="evidence_as_of_utc")
        if as_of > cutoff:
            blockers.append("future_evidence_as_of")
        producer_cutoff = parse_utc(receipt.artifact_cutoff_utc)
        if producer_cutoff > cutoff:
            blockers.append("future_producer_cutoff")
        if producer_cutoff > as_of:
            blockers.append("producer_cutoff_after_evidence_as_of")
        observed_at = getattr(evidence, "observed_at_utc", None)
        if observed_at and parse_utc(observed_at) > as_of:
            blockers.append("observed_after_evidence_as_of")
        if extracted is not None:
            for field_name in ("observed_at_utc", "known_at_utc", "published_at_utc", "revision_at_utc"):
                timestamp = getattr(extracted, field_name)
                if timestamp and parse_utc(timestamp, field_name=field_name) > cutoff:
                    blockers.append(f"future_extracted_timestamp:{field_name}")
            if parse_utc(extracted.cutoff_utc, field_name="extracted_cutoff_utc") > cutoff:
                blockers.append("future_extracted_cutoff")
    except ValueError as error:
        blockers.append(str(error))
    return _unique(blockers)


def _timestamps(value: Any, *, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(item, str) and str(key).endswith("_utc"):
                yield path, item
            else:
                yield from _timestamps(item, prefix=path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _timestamps(item, prefix=f"{prefix}[{index}]")


def verify_governed_artifact(
    consumed_bytes: bytes,
    binding: GovernedCandidatePoolBindingV1,
    *,
    expected_repository: str,
    expected_branch: str,
    expected_artifact_path: str,
    expected_schema_version: str,
    expected_producer_version: str,
    expected_pool_id: str,
    as_of_utc: str,
    logical_hash_excluded_fields: Sequence[str] = ("logical_hash", "pool_id"),
) -> ArtifactVerificationResultV1:
    """Verify an immutable JSON artifact from the exact consumed bytes."""
    blockers: list[str] = []
    actual_byte_hash = sha256(consumed_bytes).hexdigest()
    actual_blob_hash = _git_blob_sha1(consumed_bytes)
    if binding.repository != expected_repository:
        blockers.append("repository_identity_mismatch")
    if binding.branch != expected_branch:
        blockers.append("branch_identity_mismatch")
    if not COMMIT_RE.fullmatch(binding.producer_commit):
        blockers.append("producer_commit_malformed")
    if binding.artifact_path != expected_artifact_path:
        blockers.append("artifact_path_mismatch")
    if binding.consumed_byte_sha256 != actual_byte_hash:
        blockers.append("consumed_byte_sha256_mismatch")
    if binding.git_blob_sha1 and binding.git_blob_sha1 != actual_blob_hash:
        blockers.append("git_blob_sha1_mismatch")
    if binding.git_blob_sha1 and not SHA1_RE.fullmatch(binding.git_blob_sha1):
        blockers.append("git_blob_sha1_malformed")

    calculated_logical: str | None = None
    verified_hashes = 0
    checked_times = 0
    try:
        artifact = json.loads(consumed_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        artifact = None
        blockers.append("artifact_json_invalid")
    if isinstance(artifact, Mapping):
        if artifact.get("schema_version") != expected_schema_version or binding.schema_version != expected_schema_version:
            blockers.append("schema_version_mismatch")
        if artifact.get("producer_version") != expected_producer_version or binding.producer_version != expected_producer_version:
            blockers.append("producer_version_mismatch")
        if artifact.get("pool_id") != expected_pool_id or binding.pool_id != expected_pool_id:
            blockers.append("pool_id_mismatch")
        material = {key: value for key, value in artifact.items() if key not in logical_hash_excluded_fields}
        calculated_logical = logical_hash(material)
        if artifact.get("logical_hash") != calculated_logical or binding.logical_hash != calculated_logical:
            blockers.append("logical_hash_mismatch")
        cutoff = artifact.get("cutoff_time_utc")
        if not cutoff or not binding.cutoff_time_utc:
            blockers.append("cutoff_time_missing")
        elif cutoff != binding.cutoff_time_utc:
            blockers.append("cutoff_binding_mismatch")
        else:
            try:
                cutoff_dt = parse_utc(cutoff, field_name="cutoff_time_utc")
                if cutoff_dt > parse_utc(as_of_utc, field_name="as_of_utc"):
                    blockers.append("future_cutoff")
                for path, timestamp in _timestamps(artifact):
                    checked_times += 1
                    try:
                        if parse_utc(timestamp, field_name=path) > cutoff_dt:
                            blockers.append(f"future_dated_evidence:{path}")
                    except ValueError:
                        blockers.append(f"invalid_point_in_time_field:{path}")
            except ValueError as error:
                blockers.append(str(error))
        records = [
            *list(artifact.get("eligible_candidates", [])),
            *list(artifact.get("rejected_candidates", [])),
        ]
        actual_candidate_hashes = {
            str(row.get("candidate_id")): str(row.get("evidence_hash"))
            for row in records
            if isinstance(row, Mapping) and row.get("candidate_id")
        }
        if dict(binding.candidate_hashes) != actual_candidate_hashes:
            blockers.append("candidate_hashes_mismatch")
        else:
            verified_hashes = len(actual_candidate_hashes)
        actual_families = tuple(sorted(str(row.get("family_id")) for row in artifact.get("source_coverage", [])))
        if tuple(sorted(binding.source_family_coverage)) != actual_families:
            blockers.append("source_family_coverage_mismatch")
    elif artifact is not None:
        blockers.append("artifact_root_must_be_object")

    blockers_tuple = _unique(blockers)
    binding_material = primitive(binding)
    result_material = {
        "actual_byte_sha256": actual_byte_hash,
        "actual_git_blob_sha1": actual_blob_hash,
        "calculated_logical_hash": calculated_logical,
        "blockers": blockers_tuple,
        "binding_hash": logical_hash(binding_material),
    }
    result_hash = logical_hash(result_material)
    return ArtifactVerificationResultV1(
        verification_id="artifact_verification_" + result_hash[:24],
        status="PASS_IMMUTABLE_BINDING_VERIFIED" if not blockers_tuple else "BLOCKED_ARTIFACT_BINDING",
        actual_byte_sha256=actual_byte_hash,
        actual_git_blob_sha1=actual_blob_hash,
        calculated_logical_hash=calculated_logical,
        candidate_hashes_verified=verified_hashes,
        point_in_time_fields_checked=checked_times,
        blockers=blockers_tuple,
        binding_hash=logical_hash(binding_material),
    )
