"""Domain-neutral adaptive content analysis and shadow learning engine V2."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from live_contentops.content_intelligence_contracts_v2 import (
    AdaptiveLearningConfigV1,
    AvailabilityState,
    CalibrationState,
    ContentGapSetV1,
    ContentOpsLearningDecisionV2,
    EventRelationship,
    FeatureEvaluationV1,
    GapType,
    OutcomeDecisionV1,
    PerformanceObservationSetV1,
    PublishedContentHistoryV1,
    RankingRowV1,
    logical_hash,
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
    frozenset({"GOVERNED_MATERIAL_UPDATE", "DUPLICATE_NO_NEW_DELTA"}),
    frozenset({"GOVERNED_CORRECTION", "DUPLICATE_NO_NEW_DELTA"}),
    frozenset({"GOVERNED_NEW_PHASE", "DUPLICATE_NO_NEW_DELTA"}),
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


def _authorized(candidate: LearningCandidateV2) -> bool:
    return bool(
        candidate.authority_ready
        and candidate.reporting_allowed
        and not candidate.authority_blockers
    )


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

    if relationship == EventRelationship.MATERIAL_UPDATE:
        if authorized and candidate.governed_material_delta and not duplicate:
            outcomes.append("GOVERNED_MATERIAL_UPDATE")
        else:
            reasons.append("material_update_requires_authority_governed_delta_and_nonduplicate_identity")
    if relationship == EventRelationship.CONFIRMATION:
        if authorized and candidate.prior_testable_proposition_ref and candidate.governed_new_evidence_ref:
            outcomes.append("GOVERNED_CONFIRMATION")
        else:
            reasons.append("confirmation_requires_authority_prior_proposition_and_new_evidence")
    if relationship == EventRelationship.CONTRADICTION:
        if authorized and candidate.prior_testable_proposition_ref and candidate.conflicting_evidence_ref:
            outcomes.append("GOVERNED_CONTRADICTION")
        else:
            reasons.append("contradiction_requires_authority_prior_proposition_and_conflicting_evidence")
    if relationship == EventRelationship.CORRECTION:
        if authorized and (candidate.prior_error_ref or candidate.authoritative_correction_ref):
            outcomes.append("GOVERNED_CORRECTION")
        else:
            reasons.append("correction_requires_authority_and_identified_error_or_authoritative_correction")
    if relationship == EventRelationship.NEW_PHASE:
        if authorized and candidate.update_chain_continuity and candidate.distinct_new_event_ref and not duplicate:
            outcomes.append("GOVERNED_NEW_PHASE")
        else:
            reasons.append("new_phase_requires_authority_chain_continuity_distinct_event_and_nonduplicate_identity")
    if packaging_gap:
        outcomes.append("DERIVATIVE_PACKAGING_GAP")
        reasons.append("packaging_gap_changes_payload_structure_not_factual_authority")
    if duplicate:
        outcomes.append("DUPLICATE_NO_NEW_DELTA")
        reasons.append("duplicate_is_identity_relationship_not_automatic_filler")
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
        and candidate.durability is not None
        and candidate.content_age_hours is not None
        and candidate.reader_utility is not None
        and candidate.update_justification_ref
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
        history_relationship="duplicate" if duplicate else "not_matched",
        content_gap_state=";".join(sorted(gap.value for gap in candidate.gap_types)) or "none",
        actionable_outcomes=tuple(dict.fromkeys(outcomes)),
        publication_disposition=publication,
        reason_codes=tuple(dict.fromkeys(reasons)),
        evidence_refs=tuple(dict.fromkeys(candidate.evidence_refs)),
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
        return max(0.0, min(1.0, (numeric - minimum) / (maximum - minimum)))
    if method == "inverse_min_max":
        minimum, maximum = float(rule["minimum"]), float(rule["maximum"])
        if maximum <= minimum:
            raise ValueError("invalid_inverse_min_max_normalization")
        return 1.0 - max(0.0, min(1.0, (numeric - minimum) / (maximum - minimum)))
    raise ValueError(f"unsupported_normalization:{method}")


def evaluate_features(
    candidate: LearningCandidateV2,
    config: AdaptiveLearningConfigV1,
    observations: PerformanceObservationSetV1,
) -> tuple[FeatureEvaluationV1, ...]:
    """Evaluate registered features while preserving unavailable and zero."""
    supplied = {row.feature_id: row for row in candidate.feature_inputs}
    metric_count = observations.cardinalities()["metric_bearing_observation_count"]
    derived: dict[str, FeatureInputV1] = {
        "performance_evidence_availability": FeatureInputV1(
            "performance_evidence_availability",
            True,
            AvailabilityState.AVAILABLE if metric_count else AvailabilityState.UNAVAILABLE,
            1.0 if metric_count else None,
            None if metric_count else "no_metric_bearing_observations",
            reason_codes=("content_analysis_remains_available",),
        ),
        "sample_size_confidence": FeatureInputV1(
            "sample_size_confidence",
            True,
            AvailabilityState.AVAILABLE if metric_count else AvailabilityState.UNAVAILABLE,
            min(1.0, metric_count / max(1.0, float(config.thresholds.get("minimum_metric_observations", 1.0)))) if metric_count else None,
            None if metric_count else "no_metric_bearing_observations",
        ),
    }
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
        if not item.applicable:
            rows.append(FeatureEvaluationV1(
                definition.feature_id, False, AvailabilityState.UNSUPPORTED,
                item.unavailable_reason or "not_applicable", item.raw_value,
                definition.normalization, None, definition.weight, None, None,
                item.evidence_refs, item.reason_codes,
            ))
            continue
        if item.availability in {AvailabilityState.UNAVAILABLE, AvailabilityState.BLOCKED, AvailabilityState.UNSUPPORTED}:
            if item.raw_value is not None:
                raise ValueError(f"unavailable_feature_carries_value:{definition.feature_id}")
            rows.append(FeatureEvaluationV1(
                definition.feature_id, True, item.availability,
                item.unavailable_reason or "reason_required", None,
                definition.normalization, None, definition.weight, None, None,
                item.evidence_refs, item.reason_codes,
            ))
            continue
        if item.raw_value is None:
            raise ValueError(f"available_feature_missing_value:{definition.feature_id}")
        normalized = _normalize(
            item.raw_value,
            definition.normalization,
            config.normalization_rules[definition.normalization],
        )
        penalty = abs(definition.weight * normalized) if definition.penalty else 0.0
        contribution = 0.0 if definition.penalty else definition.weight * normalized
        rows.append(FeatureEvaluationV1(
            definition.feature_id, True, item.availability,
            item.unavailable_reason, item.raw_value, definition.normalization,
            round(normalized, 8), definition.weight, round(contribution, 8),
            round(penalty, 8), item.evidence_refs, item.reason_codes,
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
    blockers = [*history.validate(), *observations.validate(), *config.validate()]
    if blockers:
        raise ValueError("invalid_learning_inputs:" + ",".join(blockers))
    if prior_decision and not supersession_reason:
        raise ValueError("supersession_reason_required")
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
        "supersession_reason": supersession_reason,
        "config_version": config.config_version,
        "input_bindings": dict(sorted(input_bindings.items())),
        "cohort_identity": logical_hash({
            "candidate_ids": sorted(candidate.candidate_id for candidate in candidates),
            "history_id": history.history_id,
            "gap_set_id": gaps.gap_set_id,
            "observation_set_id": observations.observation_set_id,
        }),
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
) -> tuple[str, ...]:
    blockers = []
    if successor.prior_decision_id != prior.decision_id:
        blockers.append("prior_decision_id_mismatch")
    if not successor.supersession_reason:
        blockers.append("supersession_reason_missing")
    if successor.decision_id == prior.decision_id:
        blockers.append("successor_identity_must_change")
    if successor.logical_hash == prior.logical_hash:
        blockers.append("successor_logical_hash_must_change")
    return tuple(blockers)
