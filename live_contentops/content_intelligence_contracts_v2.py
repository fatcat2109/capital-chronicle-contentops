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

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.evidence_ref or not IDENTIFIER_RE.fullmatch(self.evidence_ref):
            blockers.append("malformed_evidence_ref")
        if not self.authority_state:
            blockers.append("missing_evidence_authority_state")
        if not self.permission_state:
            blockers.append("missing_evidence_permission_state")
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
        return _unique(blockers)

    def qualifies_for_governed_outcome(self) -> bool:
        """Return whether this record may support a governed outcome.

        Validation, authority, and permission are deliberately independent.
        Context-only, blocked, unavailable, malformed, and unverified records
        remain valid evidence records but cannot satisfy governed evidence.
        """
        return bool(
            not self.validate()
            and self.authority_state in QUALIFYING_GOVERNED_EVIDENCE_AUTHORITY_STATES
            and self.permission_state in QUALIFYING_GOVERNED_EVIDENCE_PERMISSION_STATES
            and not (set(self.reason_codes) & DISQUALIFYING_GOVERNED_EVIDENCE_REASON_CODES)
        )


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
    logical_hash: str
    schema_version: str = SCHEMA_DECISION_V2


def _git_blob_sha1(data: bytes) -> str:
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


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
