"""Domain-neutral adaptive content analysis and shadow learning engine V2."""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Any, Mapping, Sequence

from live_contentops.content_intelligence_contracts_v2 import (
    AdaptiveLearningConfigV1,
    AvailabilityState,
    CANONICAL_AUTHORITY_GATE_IDS,
    CalibrationState,
    CapabilityDimensionsV1,
    ContentGapSetV1,
    ContentOpsLearningDecisionV2,
    EvidenceReferenceV1,
    EventRelationship,
    FeatureEvaluationV1,
    GapType,
    IDENTIFIER_RE,
    OutcomeDecisionV1,
    PerformanceObservationSetV1,
    PublishedContentHistoryV1,
    RankingRowV1,
    logical_hash,
    canonical_json,
    parse_utc,
    primitive,
)


FORBIDDEN_LEARNING_EFFECTS = (
    "factual_claims",
    "source_authority",
    "permissions",
    "dqr",
    "exact_proxy_context_labels",
    "citation_requirements",
    "risk_language",
    "numeric_truth",
    "publication_blockers",
    "automatic_publication",
    "dispatch",
)

INCOMPATIBLE_ACTIONABLE_OUTCOMES = (
    *(frozenset({outcome, "DUPLICATE_NO_NEW_DELTA"}) for outcome in (
        "GOVERNED_MATERIAL_UPDATE",
        "GOVERNED_CONFIRMATION",
        "GOVERNED_CONTRADICTION",
        "GOVERNED_CORRECTION",
        "GOVERNED_NEW_PHASE",
    )),
    frozenset({"FILLER_NO_READER_CONTRIBUTION", "GOVERNED_MATERIAL_UPDATE"}),
    frozenset({"FILLER_NO_READER_CONTRIBUTION", "GOVERNED_CONFIRMATION"}),
    frozenset({"FILLER_NO_READER_CONTRIBUTION", "GOVERNED_CONTRADICTION"}),
    frozenset({"FILLER_NO_READER_CONTRIBUTION", "GOVERNED_CORRECTION"}),
    frozenset({"FILLER_NO_READER_CONTRIBUTION", "GOVERNED_NEW_PHASE"}),
)


@dataclass(frozen=True)
class FeatureInputV1:
    feature_id: str
    applicable: bool
    availability: AvailabilityState
    raw_value: float | bool | None
    unavailable_reason: str | None = None
    evidence_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    evidence_count: int | None = None


@dataclass(frozen=True)
class LearningCandidateV2:
    candidate_id: str
    story_id: str
    cluster_id: str | None
    update_chain_id: str | None
    source_relationship: EventRelationship
    evidence_state: str
    authority_state: str
    authority_ready: bool
    reporting_allowed: bool
    authority_blockers: tuple[str, ...]
    history_identity_match: bool
    governed_material_delta: bool = False
    prior_testable_proposition_ref: str | None = None
    governed_new_evidence_ref: str | None = None
    conflicting_evidence_ref: str | None = None
    prior_error_ref: str | None = None
    authoritative_correction_ref: str | None = None
    update_chain_continuity: bool = False
    distinct_new_event_ref: str | None = None
    material_reader_contribution: bool | None = None
    durability: float | None = None
    content_age_hours: float | None = None
    reader_utility: float | None = None
    update_justification_ref: str | None = None
    gap_types: tuple[GapType, ...] = ()
    feature_inputs: tuple[FeatureInputV1, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    internal_brief_ids: tuple[str, ...] = ()
    capabilities: CapabilityDimensionsV1 = CapabilityDimensionsV1()
    evidence_records: tuple[EvidenceReferenceV1, ...] = ()
    governed_evidence_refs: tuple[str, ...] = ()
    authority_gate_results: Mapping[str, bool] | None = None


def _authorized(candidate: LearningCandidateV2) -> bool:
    return bool(
        candidate.authority_ready
        and candidate.reporting_allowed
        and not candidate.authority_blockers
    )


def _deduplicated_valid_evidence_refs(*groups: Sequence[str]) -> tuple[str, ...]:
    refs: list[str] = []
    for group in groups:
        for ref in group:
            if not isinstance(ref, str) or not IDENTIFIER_RE.fullmatch(ref):
                raise ValueError(f"malformed_evidence_ref:{ref}")
            refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _complete_evidence_lineage(
    candidate: LearningCandidateV2,
    *additional_groups: Sequence[str],
    include_semantic_refs: bool = False,
) -> tuple[str, ...]:
    record_refs: list[str] = []
    for record in candidate.evidence_records:
        blockers = record.validate()
        if blockers:
            raise ValueError("invalid_evidence_record:" + ",".join(blockers))
        record_refs.append(record.evidence_ref)
    semantic_refs = ()
    if include_semantic_refs:
        semantic_refs = tuple(ref for ref in (
            candidate.governed_new_evidence_ref,
            candidate.conflicting_evidence_ref,
            candidate.authoritative_correction_ref,
            candidate.distinct_new_event_ref,
            candidate.update_justification_ref,
        ) if ref)
    return _deduplicated_valid_evidence_refs(
        *additional_groups,
        candidate.evidence_refs,
        tuple(record_refs),
        candidate.governed_evidence_refs,
        semantic_refs,
    )


def _feature_evidence_lineage(
    candidate: LearningCandidateV2,
    item_refs: Sequence[str],
) -> tuple[str, ...]:
    record_refs: list[str] = []
    for record in candidate.evidence_records:
        blockers = record.validate()
        if blockers:
            raise ValueError("invalid_evidence_record:" + ",".join(blockers))
        record_refs.append(record.evidence_ref)
    primary_refs = tuple(item_refs) if item_refs else candidate.evidence_refs
    return _deduplicated_valid_evidence_refs(primary_refs, tuple(record_refs))


def _qualifying_governed_evidence_refs(candidate: LearningCandidateV2) -> tuple[str, ...]:
    lineage = set(_deduplicated_valid_evidence_refs(
        candidate.evidence_refs,
        tuple(record.evidence_ref for record in candidate.evidence_records),
    ))
    verified_refs = _deduplicated_valid_evidence_refs(candidate.governed_evidence_refs)
    if any(ref not in lineage for ref in verified_refs):
        raise ValueError("verified_governed_evidence_ref_missing_from_lineage")
    qualified_records = tuple(
        record.evidence_ref
        for record in candidate.evidence_records
        if record.qualifies_for_governed_outcome()
    )
    return _deduplicated_valid_evidence_refs(verified_refs, qualified_records)


def _authority_gate_input_blockers(
    candidate: LearningCandidateV2,
    config: AdaptiveLearningConfigV1,
) -> tuple[str, ...]:
    blockers: list[str] = []
    for gate_id, value in (candidate.authority_gate_results or {}).items():
        if not isinstance(gate_id, str) or not IDENTIFIER_RE.fullmatch(gate_id) or not isinstance(value, bool):
            blockers.append(f"invalid_authority_gate_result:{gate_id}")
            continue
        if gate_id in CANONICAL_AUTHORITY_GATE_IDS:
            blockers.append(f"canonical_authority_gate_override_forbidden:{gate_id}")
        elif gate_id not in config.authority_gates:
            blockers.append(f"unknown_extension_authority_gate:{gate_id}")
        elif value and config.authority_gates[gate_id] is not True:
            blockers.append(f"contradictory_extension_authority_gate:{gate_id}")
    return tuple(dict.fromkeys(blockers))


def _validate_actionable_outcomes(outcomes: Sequence[str]) -> None:
    selected = set(outcomes)
    for incompatible in INCOMPATIBLE_ACTIONABLE_OUTCOMES:
        if incompatible.issubset(selected):
            raise ValueError("incompatible_actionable_outcomes:" + ",".join(sorted(incompatible)))


def evaluate_outcome(
    candidate: LearningCandidateV2,
    config: AdaptiveLearningConfigV1,
) -> OutcomeDecisionV1:
    """Separate source relationship, authority, history, gaps, and action."""
    authorized = _authorized(candidate)
    relationship = candidate.source_relationship
    outcomes: list[str] = []
    reasons: list[str] = []
    duplicate = candidate.history_identity_match or relationship == EventRelationship.DUPLICATE
    packaging_gap = GapType.DERIVATIVE_PACKAGING_GAP in candidate.gap_types
    complete_evidence_lineage = _complete_evidence_lineage(candidate, include_semantic_refs=True)
    qualifying_governed_refs = _qualifying_governed_evidence_refs(candidate)
    governed_evidence_present = bool(qualifying_governed_refs)

    if relationship == EventRelationship.MATERIAL_UPDATE:
        if authorized and candidate.governed_material_delta and governed_evidence_present:
            outcomes.append("GOVERNED_MATERIAL_UPDATE")
        else:
            reasons.append("material_update_requires_authority_permission_governed_delta_and_evidence")
    if relationship == EventRelationship.CONFIRMATION:
        if authorized and candidate.prior_testable_proposition_ref and candidate.governed_new_evidence_ref and governed_evidence_present:
            outcomes.append("GOVERNED_CONFIRMATION")
        else:
            reasons.append("confirmation_requires_authority_prior_proposition_and_new_evidence")
    if relationship == EventRelationship.CONTRADICTION:
        if authorized and candidate.prior_testable_proposition_ref and candidate.conflicting_evidence_ref and governed_evidence_present:
            outcomes.append("GOVERNED_CONTRADICTION")
        else:
            reasons.append("contradiction_requires_authority_prior_proposition_and_conflicting_evidence")
    if relationship == EventRelationship.CORRECTION:
        if authorized and (candidate.prior_error_ref or candidate.authoritative_correction_ref) and governed_evidence_present:
            outcomes.append("GOVERNED_CORRECTION")
        else:
            reasons.append("correction_requires_authority_and_identified_error_or_authoritative_correction")
    if relationship == EventRelationship.NEW_PHASE:
        if authorized and candidate.update_chain_continuity and candidate.distinct_new_event_ref and governed_evidence_present:
            outcomes.append("GOVERNED_NEW_PHASE")
        else:
            reasons.append("new_phase_requires_authority_chain_continuity_distinct_event_and_governed_evidence")
    governed_delta_present = any(value in outcomes for value in (
        "GOVERNED_MATERIAL_UPDATE",
        "GOVERNED_CONFIRMATION",
        "GOVERNED_CONTRADICTION",
        "GOVERNED_CORRECTION",
        "GOVERNED_NEW_PHASE",
    ))
    if packaging_gap:
        outcomes.append("DERIVATIVE_PACKAGING_GAP")
        reasons.append("packaging_gap_changes_payload_structure_not_factual_authority")
    if duplicate and not governed_delta_present:
        outcomes.append("DUPLICATE_NO_NEW_DELTA")
        reasons.append("duplicate_is_identity_relationship_not_automatic_filler")
    elif duplicate:
        reasons.append("published_identity_match_preserved_with_governed_delta")
    if candidate.material_reader_contribution is False:
        outcomes.append("FILLER_NO_READER_CONTRIBUTION")
        reasons.append("evidence_review_found_no_material_reader_contribution")

    evergreen_thresholds = {
        "durability": float(config.thresholds.get("evergreen_min_durability", 0.0)),
        "age": float(config.thresholds.get("evergreen_min_age_hours", 0.0)),
        "utility": float(config.thresholds.get("evergreen_min_reader_utility", 0.0)),
    }
    evergreen_requested = GapType.EVERGREEN_REFRESH in candidate.gap_types
    evergreen_valid = bool(
        evergreen_requested
        and authorized
        and candidate.durability is not None
        and candidate.content_age_hours is not None
        and candidate.reader_utility is not None
        and candidate.update_justification_ref
        and governed_evidence_present
        and candidate.durability >= evergreen_thresholds["durability"]
        and candidate.content_age_hours >= evergreen_thresholds["age"]
        and candidate.reader_utility >= evergreen_thresholds["utility"]
    )
    if evergreen_valid:
        outcomes.append("EVERGREEN_REFRESH_JUSTIFIED")
    elif evergreen_requested:
        reasons.append("evergreen_refresh_criteria_not_met")

    if not authorized:
        reasons.append("insufficient_authority_is_disposition_not_topic")
    if not outcomes:
        outcomes.append("NO_ACTIONABLE_CONTENT_LEARNING_OUTCOME")
    _validate_actionable_outcomes(outcomes)

    if not authorized:
        publication = "NO_PUBLICATION_INSUFFICIENT_AUTHORITY"
    elif duplicate and not any(value.startswith("GOVERNED_") for value in outcomes):
        publication = "NO_PUBLICATION_DUPLICATE_WITHOUT_GOVERNED_DELTA"
    elif "FILLER_NO_READER_CONTRIBUTION" in outcomes:
        publication = "NO_PUBLICATION_FILLER"
    elif any(value.startswith("GOVERNED_") for value in outcomes):
        publication = "INTERNAL_BRIEF_ELIGIBLE_OPERATOR_REVIEW_NO_PUBLICATION_AUTHORITY"
    else:
        publication = "NO_PUBLICATION_NO_GOVERNED_ACTIONABLE_OUTCOME"

    return OutcomeDecisionV1(
        source_relationship=relationship,
        evidence_state=candidate.evidence_state,
        authority_state=candidate.authority_state,
        history_relationship=(
            "PUBLISHED_IDENTITY_MATCH_WITH_GOVERNED_DELTA"
            if duplicate and governed_delta_present
            else "PUBLISHED_IDENTITY_MATCH_NO_NEW_DELTA"
            if duplicate
            else "NOT_MATCHED"
        ),
        content_gap_state=";".join(sorted(gap.value for gap in candidate.gap_types)) or "none",
        actionable_outcomes=tuple(dict.fromkeys(outcomes)),
        publication_disposition=publication,
        reason_codes=tuple(dict.fromkeys(reasons)),
        evidence_refs=complete_evidence_lineage,
        authority_result=candidate.authority_ready and not candidate.authority_blockers,
        reporting_permission_result=candidate.reporting_allowed,
        history_identity_match=duplicate,
        governed_delta_present=governed_delta_present,
        qualifying_governed_evidence_refs=qualifying_governed_refs,
    )


def _normalize(raw: float | bool, method: str, rule: Mapping[str, Any]) -> float:
    numeric = float(raw)
    if method == "boolean":
        if numeric not in {0.0, 1.0}:
            raise ValueError("boolean_normalization_requires_zero_or_one")
        return numeric
    if method == "bounded_0_1":
        if numeric < 0.0 or numeric > 1.0:
            raise ValueError("bounded_normalization_out_of_range")
        return numeric
    if method == "min_max":
        minimum, maximum = float(rule["minimum"]), float(rule["maximum"])
        if maximum <= minimum:
            raise ValueError("invalid_min_max_normalization")
        if numeric < minimum or numeric > maximum:
            raise ValueError("min_max_normalization_out_of_range")
        return (numeric - minimum) / (maximum - minimum)
    if method == "inverse_min_max":
        minimum, maximum = float(rule["minimum"]), float(rule["maximum"])
        if maximum <= minimum:
            raise ValueError("invalid_inverse_min_max_normalization")
        if numeric < minimum or numeric > maximum:
            raise ValueError("inverse_min_max_normalization_out_of_range")
        return 1.0 - (numeric - minimum) / (maximum - minimum)
    raise ValueError(f"unsupported_normalization:{method}")


def _capability_tokens(capabilities: CapabilityDimensionsV1) -> set[str]:
    profile = capabilities.profile()
    tokens = {
        *(f"evidence_modality:{value.value}" for value in capabilities.evidence_modalities),
        *(f"temporal_character:{value.value}" for value in capabilities.temporal_characters),
        *(f"story_mode:{value.value}" for value in capabilities.story_modes),
        *(f"geography:{value}" for value in capabilities.geography_ids),
        *(f"entity:{value}" for value in capabilities.entity_ids),
        *(f"economic_domain:{value}" for value in capabilities.affected_economic_domains),
        *(f"asset_class:{value}" for value in capabilities.affected_asset_classes),
        *(f"source_family:{value}" for value in capabilities.source_family_ids),
        *(f"source_authority:{value}" for value in capabilities.source_authority_classes),
    }
    for name, value in profile.items():
        if value is True:
            tokens.add(f"profile:{name.removesuffix('_profile')}")
    if int(profile["source_count"] or 0) > 0:
        tokens.add("profile:source_present")
    for name in ("source", "geography", "entity", "economic_domain", "asset_class"):
        if int(profile[f"{name}_count"] or 0) > 1:
            tokens.add(f"profile:multi_{name}")
    return tokens


def _applicability(definition: Any, capabilities: CapabilityDimensionsV1) -> tuple[bool, tuple[str, ...]]:
    selectors = tuple(definition.domain_applicability)
    if "*" in selectors:
        return True, ("*",)
    tokens = _capability_tokens(capabilities)
    matched = tuple(selector for selector in selectors if selector in tokens)
    return bool(matched), matched


def _derived_feature_inputs(
    candidate: LearningCandidateV2,
    config: AdaptiveLearningConfigV1,
    observations: PerformanceObservationSetV1,
) -> dict[str, FeatureInputV1]:
    metric_count = observations.cardinalities()["metric_bearing_observation_count"]
    profile = candidate.capabilities.profile()
    evidence_refs = tuple(dict.fromkeys((
        *candidate.evidence_refs,
        *(row.evidence_ref for row in candidate.evidence_records),
    )))
    source_count = int(profile["source_count"] or 0)
    diversity_target = max(1.0, float(config.thresholds["source_diversity_full_count"]))
    breadth_count = max(
        int(profile["geography_count"] or 0),
        int(profile["economic_domain_count"] or 0),
        int(profile["asset_class_count"] or 0),
    )
    breadth_target = max(1.0, float(config.thresholds["breadth_full_count"]))
    return {
        "source_diversity": FeatureInputV1(
            "source_diversity", source_count > 0,
            AvailabilityState.AVAILABLE if source_count else AvailabilityState.UNSUPPORTED,
            min(1.0, source_count / diversity_target) if source_count else None,
            None if source_count else "source_dimension_not_supplied", evidence_refs,
            ("derived_from_source_family_count",),
        ),
        "scheduled_catalyst_relevance": FeatureInputV1(
            "scheduled_catalyst_relevance", candidate.capabilities.scheduled_event_state is True,
            AvailabilityState.AVAILABLE if candidate.capabilities.scheduled_event_state is True else AvailabilityState.UNSUPPORTED,
            1.0 if candidate.capabilities.scheduled_event_state is True else None,
            None if candidate.capabilities.scheduled_event_state is True else "scheduled_event_not_applicable",
            evidence_refs, ("derived_from_scheduled_event_state",),
        ),
        "cross_market_or_economy_breadth": FeatureInputV1(
            "cross_market_or_economy_breadth", breadth_count > 1,
            AvailabilityState.AVAILABLE if breadth_count > 1 else AvailabilityState.UNSUPPORTED,
            min(1.0, (breadth_count - 1) / breadth_target) if breadth_count > 1 else None,
            None if breadth_count > 1 else "cross_dimension_breadth_not_applicable",
            evidence_refs, ("derived_from_orthogonal_breadth_counts",),
        ),
        "performance_evidence_availability": FeatureInputV1(
            "performance_evidence_availability", True,
            AvailabilityState.AVAILABLE if metric_count else AvailabilityState.UNAVAILABLE,
            1.0 if metric_count else None,
            None if metric_count else "no_metric_bearing_observations", (),
            ("content_analysis_remains_available",),
        ),
        "sample_size_confidence": FeatureInputV1(
            "sample_size_confidence", True,
            AvailabilityState.AVAILABLE if metric_count else AvailabilityState.UNAVAILABLE,
            min(1.0, metric_count / max(1.0, float(config.thresholds["minimum_metric_observations"]))) if metric_count else None,
            None if metric_count else "no_metric_bearing_observations", (), (),
        ),
    }


def evaluate_features(
    candidate: LearningCandidateV2,
    config: AdaptiveLearningConfigV1,
    observations: PerformanceObservationSetV1,
) -> tuple[FeatureEvaluationV1, ...]:
    """Evaluate registered features while preserving unavailable and zero."""
    config_blockers = config.validate()
    if config_blockers:
        raise ValueError("invalid_adaptive_learning_config:" + ",".join(config_blockers))
    gate_blockers = _authority_gate_input_blockers(candidate, config)
    if gate_blockers:
        raise ValueError("invalid_candidate_authority_gates:" + ",".join(gate_blockers))
    supplied = {row.feature_id: row for row in candidate.feature_inputs}
    if len(supplied) != len(candidate.feature_inputs):
        raise ValueError("duplicate_feature_input_id")
    derived = _derived_feature_inputs(candidate, config, observations)
    rows: list[FeatureEvaluationV1] = []
    for definition in config.features:
        item = supplied.get(definition.feature_id) or derived.get(definition.feature_id)
        if item is None:
            item = FeatureInputV1(
                definition.feature_id,
                True,
                AvailabilityState.UNAVAILABLE,
                None,
                "feature_input_not_supplied",
            )
        domain_applicable, dimensions_used = _applicability(definition, candidate.capabilities)
        applicable = bool(item.applicable and domain_applicable)
        effective_refs = _feature_evidence_lineage(candidate, item.evidence_refs)
        evidence_count = len(effective_refs)
        if item.evidence_count is not None:
            if isinstance(item.evidence_count, bool) or not isinstance(item.evidence_count, int) or item.evidence_count < 0:
                raise ValueError(f"declared_evidence_count_invalid:{definition.feature_id}")
            if item.evidence_count != evidence_count:
                raise ValueError(
                    f"declared_evidence_count_mismatch:{definition.feature_id}:"
                    f"declared={item.evidence_count}:derived={evidence_count}"
                )
        gate_result: bool | None = None
        if definition.authority_gate:
            canonical_gates = {
                "source_authority_ready": candidate.authority_ready and not candidate.authority_blockers,
                "reporting_allowed": candidate.reporting_allowed,
            }
            if definition.authority_gate in CANONICAL_AUTHORITY_GATE_IDS:
                gate_result = canonical_gates[definition.authority_gate]
            else:
                gate_result = bool(
                    config.authority_gates[definition.authority_gate]
                    and (candidate.authority_gate_results or {}).get(definition.authority_gate, False)
                )

        def abstain(state: AvailabilityState, reason: str, extra_codes: tuple[str, ...] = ()) -> FeatureEvaluationV1:
            return FeatureEvaluationV1(
                feature_id=definition.feature_id,
                applicable=applicable,
                availability=state,
                unavailable_reason=reason,
                raw_value=item.raw_value if state == AvailabilityState.UNSUPPORTED else None,
                normalization_method=definition.normalization,
                normalized_value=None,
                configured_weight=definition.weight,
                contribution=None,
                penalty=None,
                evidence_refs=effective_refs,
                reason_codes=tuple(dict.fromkeys((*item.reason_codes, *extra_codes))),
                capability_dimensions_used=dimensions_used,
                normalization_parameters=dict(config.normalization_rules[definition.normalization]),
                evidence_count=evidence_count,
                configured_minimum_evidence=definition.minimum_evidence,
                authority_gate_id=definition.authority_gate,
                authority_gate_result=gate_result,
                domain_applicability_result=domain_applicable,
            )

        if not applicable:
            rows.append(abstain(AvailabilityState.UNSUPPORTED, item.unavailable_reason or "domain_or_input_not_applicable", ("feature_not_applicable",)))
            continue
        if gate_result is False:
            rows.append(abstain(AvailabilityState.BLOCKED, "authority_gate_false", ("authority_gate_failed",)))
            continue
        if evidence_count < definition.minimum_evidence:
            state = AvailabilityState.BLOCKED if definition.unavailable_handling == "block" else AvailabilityState.UNAVAILABLE
            rows.append(abstain(state, "minimum_evidence_not_met", ("minimum_evidence_failed",)))
            continue
        if item.availability in {AvailabilityState.UNAVAILABLE, AvailabilityState.BLOCKED, AvailabilityState.UNSUPPORTED}:
            if item.raw_value is not None:
                raise ValueError(f"unavailable_feature_carries_value:{definition.feature_id}")
            rows.append(abstain(item.availability, item.unavailable_reason or "reason_required"))
            continue
        if item.raw_value is None:
            rows.append(abstain(AvailabilityState.UNAVAILABLE, "available_feature_missing_raw_value", ("raw_value_missing",)))
            continue
        try:
            normalized = _normalize(item.raw_value, definition.normalization, config.normalization_rules[definition.normalization])
        except (KeyError, TypeError, ValueError) as error:
            rows.append(abstain(AvailabilityState.BLOCKED, str(error), ("normalization_failed",)))
            continue
        penalty = abs(definition.weight * normalized) if definition.penalty else 0.0
        contribution = 0.0 if definition.penalty else definition.weight * normalized
        rows.append(FeatureEvaluationV1(
            feature_id=definition.feature_id, applicable=True, availability=item.availability,
            unavailable_reason=item.unavailable_reason, raw_value=item.raw_value,
            normalization_method=definition.normalization, normalized_value=round(normalized, 8),
            configured_weight=definition.weight, contribution=round(contribution, 8),
            penalty=round(penalty, 8), evidence_refs=effective_refs,
            reason_codes=item.reason_codes, capability_dimensions_used=dimensions_used,
            normalization_parameters=dict(config.normalization_rules[definition.normalization]),
            evidence_count=evidence_count, configured_minimum_evidence=definition.minimum_evidence,
            authority_gate_id=definition.authority_gate, authority_gate_result=gate_result,
            domain_applicability_result=domain_applicable,
        ))
    return tuple(rows)


def _score(features: Sequence[FeatureEvaluationV1]) -> float:
    return round(sum(row.contribution or 0.0 for row in features) - sum(row.penalty or 0.0 for row in features), 8)


def _proposals(
    candidates: Sequence[LearningCandidateV2],
    outcomes: Mapping[str, OutcomeDecisionV1],
    observations: PerformanceObservationSetV1,
) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    for candidate in candidates:
        outcome = outcomes[candidate.candidate_id]
        if "DERIVATIVE_PACKAGING_GAP" in outcome.actionable_outcomes:
            rows.append({
                "proposal_type": "packaging_hypothesis",
                "candidate_id": candidate.candidate_id,
                "operator_review_required": True,
                "automatic_change": False,
                "evidence_refs": list(outcome.evidence_refs),
            })
        if "EVERGREEN_REFRESH_JUSTIFIED" in outcome.actionable_outcomes:
            rows.append({
                "proposal_type": "evergreen_refresh_internal_brief",
                "candidate_id": candidate.candidate_id,
                "operator_review_required": True,
                "automatic_change": False,
                "evidence_refs": list(outcome.evidence_refs),
            })
    if observations.cardinalities()["metric_bearing_observation_count"] == 0:
        rows.append({
            "proposal_type": "performance_abstention",
            "reason": "no_metric_bearing_observations",
            "performance_prior_created": False,
            "automatic_change": False,
        })
    return tuple(rows)


LOGICAL_TIME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{2,127}$")


def validate_candidate_collection(
    candidates: Sequence[LearningCandidateV2],
    config: AdaptiveLearningConfigV1 | None = None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    ids = [row.candidate_id for row in candidates]
    if len(ids) != len(set(ids)):
        blockers.append("duplicate_candidate_id")
    cluster_chains: dict[str, str | None] = {}
    for row in candidates:
        if not row.candidate_id:
            blockers.append("empty_candidate_id")
        if not row.story_id:
            blockers.append(f"empty_candidate_story_id:{row.candidate_id}")
        if not isinstance(row.source_relationship, EventRelationship):
            blockers.append(f"invalid_source_relationship:{row.candidate_id}")
        if row.cluster_id and not row.update_chain_id:
            blockers.append(f"cluster_requires_update_chain:{row.candidate_id}")
        if row.cluster_id in cluster_chains and cluster_chains[row.cluster_id] != row.update_chain_id:
            blockers.append(f"cluster_update_chain_inconsistent:{row.cluster_id}")
        if row.cluster_id:
            cluster_chains[row.cluster_id] = row.update_chain_id
        if row.authority_ready and row.authority_blockers:
            blockers.append(f"authority_ready_conflicts_with_blockers:{row.candidate_id}")
        if row.reporting_allowed and not row.authority_ready:
            blockers.append(f"reporting_permission_without_authority:{row.candidate_id}")
        if len(row.evidence_refs) != len(set(row.evidence_refs)):
            blockers.append(f"duplicate_candidate_evidence_ref:{row.candidate_id}")
        if any(not isinstance(ref, str) or not IDENTIFIER_RE.fullmatch(ref) for ref in row.evidence_refs):
            blockers.append(f"malformed_candidate_evidence_ref:{row.candidate_id}")
        if len(row.governed_evidence_refs) != len(set(row.governed_evidence_refs)):
            blockers.append(f"duplicate_governed_evidence_ref:{row.candidate_id}")
        if any(not isinstance(ref, str) or not IDENTIFIER_RE.fullmatch(ref) for ref in row.governed_evidence_refs):
            blockers.append(f"malformed_governed_evidence_ref:{row.candidate_id}")
        if len(row.internal_brief_ids) != len(set(row.internal_brief_ids)):
            blockers.append(f"duplicate_internal_brief_id:{row.candidate_id}")
        blockers.extend(f"{value}:{row.candidate_id}" for value in row.capabilities.validate())
        evidence_ids = [value.evidence_ref for value in row.evidence_records]
        if len(evidence_ids) != len(set(evidence_ids)):
            blockers.append(f"duplicate_evidence_record:{row.candidate_id}")
        blockers.extend(f"{value}:{row.candidate_id}" for evidence in row.evidence_records for value in evidence.validate())
        available_lineage = set(row.evidence_refs) | set(evidence_ids)
        if any(ref not in available_lineage for ref in row.governed_evidence_refs):
            blockers.append(f"verified_governed_evidence_ref_missing_from_lineage:{row.candidate_id}")
        if config is not None:
            blockers.extend(f"{value}:{row.candidate_id}" for value in _authority_gate_input_blockers(row, config))
        elif row.authority_gate_results is not None:
            for key, value in row.authority_gate_results.items():
                if not key or not isinstance(value, bool):
                    blockers.append(f"invalid_authority_gate_result:{row.candidate_id}")
                elif key in CANONICAL_AUTHORITY_GATE_IDS:
                    blockers.append(f"canonical_authority_gate_override_forbidden:{key}:{row.candidate_id}")
        try:
            for item in row.feature_inputs:
                refs = _feature_evidence_lineage(row, item.evidence_refs)
                if item.evidence_count is not None:
                    if isinstance(item.evidence_count, bool) or not isinstance(item.evidence_count, int) or item.evidence_count < 0:
                        blockers.append(f"declared_evidence_count_invalid:{item.feature_id}:{row.candidate_id}")
                    elif item.evidence_count != len(refs):
                        blockers.append(f"declared_evidence_count_mismatch:{item.feature_id}:{row.candidate_id}")
        except ValueError as error:
            blockers.append(f"{error}:{row.candidate_id}")
    return tuple(dict.fromkeys(blockers))


def _validate_learning_inputs(
    *,
    candidates: Sequence[LearningCandidateV2],
    history: PublishedContentHistoryV1,
    gaps: ContentGapSetV1,
    observations: PerformanceObservationSetV1,
    config: AdaptiveLearningConfigV1,
    input_bindings: Mapping[str, str],
    logical_time_basis: str,
) -> tuple[str, ...]:
    blockers = [
        *history.validate(), *gaps.validate(), *observations.validate(), *config.validate(),
        *validate_candidate_collection(candidates, config),
    ]
    for key, value in input_bindings.items():
        if not isinstance(key, str) or not key.strip():
            blockers.append("input_binding_key_empty")
        if not isinstance(value, str) or not value.strip():
            blockers.append(f"input_binding_value_empty:{key}")
    if not LOGICAL_TIME_RE.fullmatch(logical_time_basis or ""):
        blockers.append("logical_time_basis_malformed")
    return tuple(dict.fromkeys(blockers))


def build_learning_decision_v2(
    *,
    candidates: Sequence[LearningCandidateV2],
    history: PublishedContentHistoryV1,
    gaps: ContentGapSetV1,
    observations: PerformanceObservationSetV1,
    config: AdaptiveLearningConfigV1,
    input_bindings: Mapping[str, str],
    logical_time_basis: str,
    prior_decision: ContentOpsLearningDecisionV2 | None = None,
    supersession_reason: str | None = None,
) -> ContentOpsLearningDecisionV2:
    """Build a deterministic, append-only shadow decision for any cohort size."""
    blockers = _validate_learning_inputs(
        candidates=candidates, history=history, gaps=gaps, observations=observations,
        config=config, input_bindings=input_bindings, logical_time_basis=logical_time_basis,
    )
    if blockers:
        raise ValueError("invalid_learning_inputs:" + ",".join(blockers))
    if prior_decision and not supersession_reason:
        raise ValueError("supersession_reason_required")
    sorted_bindings = dict(sorted(input_bindings.items()))
    input_binding_hash = logical_hash(sorted_bindings)
    content_history_hash = logical_hash(history)
    gap_set_hash = logical_hash(gaps)
    observation_set_hash = logical_hash(observations)
    candidate_cohort_hash = logical_hash(tuple(sorted((primitive(candidate) for candidate in candidates), key=lambda row: row["candidate_id"])))
    if prior_decision:
        material_changed = any((
            prior_decision.config_logical_hash != config.config_logical_hash,
            prior_decision.input_binding_hash != input_binding_hash,
            prior_decision.content_history_hash != content_history_hash,
            prior_decision.gap_set_hash != gap_set_hash,
            prior_decision.observation_set_hash != observation_set_hash,
            prior_decision.candidate_cohort_hash != candidate_cohort_hash,
            prior_decision.logical_time_basis != logical_time_basis,
        ))
        if not material_changed:
            raise ValueError("successor_requires_material_binding_config_or_authority_change")
    outcomes = {candidate.candidate_id: evaluate_outcome(candidate, config) for candidate in candidates}
    provisional: list[RankingRowV1] = []
    for candidate in candidates:
        features = evaluate_features(candidate, config, observations)
        outcome = outcomes[candidate.candidate_id]
        briefs = candidate.internal_brief_ids if outcome.publication_disposition.startswith("INTERNAL_BRIEF") else ()
        provisional.append(RankingRowV1(
            candidate_id=candidate.candidate_id,
            story_id=candidate.story_id,
            update_chain_id=candidate.update_chain_id or "unavailable",
            features=features,
            score=_score(features),
            rank=0,
            selected_internal_brief_ids=briefs,
            publication_disposition=outcome.publication_disposition,
        ))
    ordered = sorted(provisional, key=lambda row: (-row.score, row.candidate_id))
    ranking_rows = tuple(replace(row, rank=index) for index, row in enumerate(ordered, 1))
    observation_cardinalities = dict(observations.cardinalities())
    observation_cardinalities.update({
        "history_content_item_count": len(history.items),
        "candidate_count": len(candidates),
        "gap_count": len(gaps.findings),
        "idea_count": len(gaps.idea_ids),
    })
    feature_availability = {
        f"{row.candidate_id}:{feature.feature_id}": feature.availability.value
        for row in ranking_rows
        for feature in row.features
    }
    outcome_matrix = tuple({
        "candidate_id": candidate.candidate_id,
        **primitive(outcomes[candidate.candidate_id]),
    } for candidate in candidates)
    authority_matrix = tuple({
        "candidate_id": candidate.candidate_id,
        "authority_ready": candidate.authority_ready,
        "reporting_allowed": candidate.reporting_allowed,
        "authority_blockers": list(candidate.authority_blockers),
        "authority_state": candidate.authority_state,
    } for candidate in candidates)
    selected_briefs = tuple(dict.fromkeys(
        brief
        for row in ranking_rows
        for brief in row.selected_internal_brief_ids
    ))
    no_publication = tuple({
        "candidate_id": candidate.candidate_id,
        "decision": outcomes[candidate.candidate_id].publication_disposition,
        "reason_codes": list(outcomes[candidate.candidate_id].reason_codes),
    } for candidate in candidates)
    metric_count = observation_cardinalities["metric_bearing_observation_count"]
    confidence = (
        "CONTENT_AND_PERFORMANCE_SHADOW_EVIDENCE"
        if metric_count >= int(config.thresholds.get("minimum_metric_observations", 1))
        else "CONTENT_ANALYSIS_ONLY_PERFORMANCE_EVIDENCE_INSUFFICIENT"
    )
    draft = {
        "schema_version": "contentops.learning_decision.v2",
        "prior_decision_id": prior_decision.decision_id if prior_decision else None,
        "prior_decision_logical_hash": prior_decision.logical_hash if prior_decision else None,
        "supersession_reason": supersession_reason,
        "config_version": config.config_version,
        "config_logical_hash": config.config_logical_hash,
        "input_bindings": sorted_bindings,
        "input_binding_hash": input_binding_hash,
        "content_history_hash": content_history_hash,
        "gap_set_hash": gap_set_hash,
        "observation_set_hash": observation_set_hash,
        "candidate_cohort_hash": candidate_cohort_hash,
        "cohort_identity": candidate_cohort_hash,
        "observation_cardinalities": observation_cardinalities,
        "feature_availability": feature_availability,
        "outcome_matrix": outcome_matrix,
        "authority_matrix": authority_matrix,
        "ranking_rows": ranking_rows,
        "selected_internal_briefs": selected_briefs,
        "no_publication_decisions": no_publication,
        "proposals": _proposals(candidates, outcomes, observations),
        "confidence": confidence,
        "calibration_state": CalibrationState.UNCALIBRATED_FOUNDATION,
        "forbidden_effects_checked": FORBIDDEN_LEARNING_EFFECTS,
        "operator_state": "OPERATOR_REVIEW_REQUIRED_SHADOW_ONLY",
        "logical_time_basis": logical_time_basis,
    }
    digest = logical_hash(draft)
    return ContentOpsLearningDecisionV2(
        decision_id="learning_decision_v2_" + digest[:24],
        logical_hash=digest,
        **draft,
    )


def validate_append_only_successor(
    prior: ContentOpsLearningDecisionV2,
    successor: ContentOpsLearningDecisionV2,
    *,
    prior_serialized_hash_before: str | None = None,
    prior_serialized_hash_after: str | None = None,
    linear_succession_required: bool = True,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not successor.prior_decision_id:
        blockers.append("prior_decision_id_missing")
    elif successor.prior_decision_id != prior.decision_id:
        blockers.append("prior_decision_id_mismatch")
    if not successor.prior_decision_logical_hash:
        blockers.append("prior_decision_logical_hash_missing")
    elif successor.prior_decision_logical_hash != prior.logical_hash:
        blockers.append("prior_decision_logical_hash_mismatch")
    if not successor.supersession_reason:
        blockers.append("supersession_reason_missing")
    if not LOGICAL_TIME_RE.fullmatch(successor.logical_time_basis or ""):
        blockers.append("logical_time_basis_malformed")
    binding_fields = (
        "config_logical_hash", "input_binding_hash", "content_history_hash", "gap_set_hash",
        "observation_set_hash", "candidate_cohort_hash", "logical_time_basis", "operator_state",
    )
    changed_fields = [name for name in binding_fields if getattr(prior, name) != getattr(successor, name)]
    if not changed_fields:
        blockers.append("successor_authority_unchanged")
        if successor.decision_id != prior.decision_id:
            blockers.append("different_successor_identity_without_material_change")
    elif successor.decision_id == prior.decision_id or successor.logical_hash == prior.logical_hash:
        blockers.append("successor_identity_unchanged_after_material_change")
    if linear_succession_required and successor.prior_decision_id != prior.decision_id:
        blockers.append("invalid_linear_successor_fork")
    removed_bindings = set(prior.input_bindings) - set(successor.input_bindings)
    reason = (successor.supersession_reason or "").casefold()
    if removed_bindings and "input binding deletion" not in reason:
        blockers.append("input_binding_deletion_requires_explicit_reason")
    version_pattern = re.compile(r"(\d+)\.(\d+)\.(\d+)$")
    old_match, new_match = version_pattern.search(prior.config_version), version_pattern.search(successor.config_version)
    if old_match and new_match and tuple(map(int, new_match.groups())) < tuple(map(int, old_match.groups())) and "config downgrade" not in reason:
        blockers.append("config_downgrade_requires_explicit_reason")
    serialized_hash = logical_hash(primitive(prior))
    if prior_serialized_hash_before and prior_serialized_hash_before != serialized_hash:
        blockers.append("prior_serialization_before_mismatch")
    if prior_serialized_hash_after and prior_serialized_hash_after != serialized_hash:
        blockers.append("prior_serialization_mutated")
    successor_material = primitive(successor)
    declared_logical_hash = successor_material.pop("logical_hash")
    successor_material.pop("decision_id")
    if logical_hash(successor_material) != declared_logical_hash:
        blockers.append("successor_logical_hash_invalid")
    return tuple(dict.fromkeys(blockers))
