"""ContentOps assignment and five-window scheduler.

This module processes newsroom candidate pools, enforces hard gates, applies
multi-dimensional scoring, concentration penalties, update-chain rules, and
gated preemption to make deterministic daily scheduling decisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "capital_chronicle.newsroom_schedule_decision.v1"

RANKING_MODEL_VERSION = "contentops.newsroom_ranking.v2.0.0"
RANKING_DIMENSION_WEIGHTS = {
    "materiality": 0.12,
    "policy_economic_geopolitical_significance": 0.08,
    "surprise": 0.08,
    "affected_market_economy_breadth": 0.07,
    "source_authority": 0.10,
    "freshness": 0.10,
    "evidence_completeness": 0.10,
    "audience_relevance": 0.07,
    "novelty": 0.07,
    "durability": 0.05,
    "original_analysis_potential": 0.06,
    "visual_feasibility": 0.03,
    "overclaiming_risk": 0.04,
    "topic_source_day_concentration": 0.03,
}
PUBLISH_DECISIONS = frozenset({
    "PUBLISH_BREAKING_OR_HIGH_IMPACT",
    "PUBLISH_FRESH_ANALYSIS",
    "PUBLISH_DEEP_ANALYSIS",
})
BLOCKED_UPDATE_RELATIONSHIPS = frozenset({"duplicate", "incremental_update"})
ALLOWED_REENTRY_RELATIONSHIPS = frozenset({"material_update", "correction", "contradiction", "new_phase"})
ALLOWED_EVIDENCE_CLASSES = frozenset({"exact", "proxy"})
EXPECTED_UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
EXPECTED_UPSTREAM_BRANCH = "main"
EXPECTED_CANDIDATE_POOL_PRODUCER_COMMIT_SHA = "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"
BREAKING_MINIMUM_MATERIALITY = 80.0
BREAKING_MINIMUM_URGENCY = 80.0
BREAKING_MINIMUM_SIGNIFICANCE_OR_BREADTH = 70.0


def _candidate_hard_gate(candidate: Mapping[str, Any], cutoff_dt: datetime) -> list[str]:
    """Return deterministic publication blockers; an empty list is the only pass."""
    blockers = [str(code) for code in (candidate.get("blockers") or [])]
    authority = candidate.get("authority") or {}
    permissions = candidate.get("claim_permissions") or {}
    health = candidate.get("source_health") or {}
    freshness = candidate.get("freshness") or {}
    source_documents = candidate.get("source_documents") or []
    numeric_claims = candidate.get("numeric_claims") or []
    citation_map = candidate.get("citation_map") or {}

    required_ids = ("candidate_id", "story_id", "cluster_id", "update_chain_id", "source_packet_id", "source_family")
    for field in required_ids:
        if not candidate.get(field):
            blockers.append(f"missing_{field}")
    for field in ("evidence_hash", "source_packet_logical_hash"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(candidate.get(field) or "")):
            blockers.append(f"{field}_invalid")
    if candidate.get("eligible") is not True:
        blockers.append("upstream_candidate_not_eligible")
    if authority.get("story_decision") != "ALLOW":
        blockers.append("story_authority_not_allowed")
    if authority.get("global_dqr_override") is not False:
        blockers.append("global_dqr_override_not_false")
    if permissions.get("decision") != "ALLOW" or permissions.get("reporting_allowed") is not True:
        blockers.append("reporting_permission_not_granted")
    if permissions.get("numeric_claims_allowed") is not True:
        blockers.append("numeric_claim_permission_not_granted")
    if candidate.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
        blockers.append("evidence_class_not_publishable")
    if health.get("status") != "HEALTHY" or health.get("parse_status") != "PASS":
        blockers.append("source_health_not_healthy")
    if candidate.get("unresolved_contradictions"):
        blockers.append("unresolved_contradiction")
    if candidate.get("relationship") == "contradiction" and not candidate.get("contradiction_resolved"):
        blockers.append("unresolved_contradiction")

    authorized_urls = {
        str(url)
        for row in source_documents
        for url in (row.get("source_url"), row.get("data_url"))
        if url
    }
    if not source_documents or not authorized_urls:
        blockers.append("public_source_url_missing")
    if not numeric_claims:
        blockers.append("numeric_claims_missing")
    for claim in numeric_claims:
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id or claim.get("public_claim_allowed") is not True:
            blockers.append("claim_public_use_not_allowed")
        if claim.get("value") is None or not claim.get("metric") or not claim.get("unit"):
            blockers.append("numeric_claim_identity_or_unit_missing")
        claim_url = str(claim.get("source_url") or "")
        if not claim_url:
            blockers.append("numeric_claim_source_url_missing")
        citations = {str(url) for url in (citation_map.get(claim_id) or []) if url}
        if not citations:
            blockers.append("numeric_claim_citation_missing")
        if claim_url and claim_url not in authorized_urls:
            blockers.append("numeric_claim_source_not_authorized")
        if citations and not citations.issubset(authorized_urls):
            blockers.append("citation_url_not_authorized")
        for timestamp_field in ("observation_time_utc", "known_at_utc"):
            if claim.get(timestamp_field):
                try:
                    claim_dt = _parse_utc(str(claim[timestamp_field]))
                except (TypeError, ValueError):
                    blockers.append(f"claim_{timestamp_field}_invalid")
                else:
                    if claim_dt > cutoff_dt:
                        blockers.append(f"claim_{timestamp_field}_after_window_cutoff")

    for timestamp_field in ("event_time_utc", "known_at_utc"):
        try:
            parsed_dt = _parse_utc(str(candidate.get(timestamp_field) or ""))
        except (TypeError, ValueError):
            blockers.append(f"{timestamp_field}_invalid")
            continue
        if parsed_dt > cutoff_dt:
            blockers.append(f"candidate_{timestamp_field}_after_window_cutoff")
    try:
        known_dt = _parse_utc(str(candidate.get("known_at_utc") or ""))
    except (TypeError, ValueError):
        known_dt = None
    if known_dt is not None:
        max_age = freshness.get("max_age_hours")
        if max_age is None:
            blockers.append("freshness_limit_missing")
        elif (cutoff_dt - known_dt).total_seconds() > float(max_age) * 3600.0:
            blockers.append("candidate_stale_at_window_cutoff")
    return sorted(set(blockers))


def _available_score(dimensions: Mapping[str, Mapping[str, Any]], name: str) -> float | None:
    row = dimensions.get(name) or {}
    if row.get("availability") != "AVAILABLE" or row.get("score") is None:
        return None
    return float(row["score"])


def _breaking_qualification(scored: Mapping[str, Any]) -> dict[str, Any]:
    """Qualify breaking status from material event evidence, never evidence quality."""
    candidate = scored["candidate"]
    scores = scored["raw_scores"]
    dimensions = scores["dimensions"]
    materiality = _available_score(dimensions, "materiality")
    significance = _available_score(dimensions, "policy_economic_geopolitical_significance")
    breadth = _available_score(dimensions, "affected_market_economy_breadth")
    significance_or_breadth = max(value for value in (significance, breadth) if value is not None) if any(
        value is not None for value in (significance, breadth)
    ) else None
    relationship = str(candidate.get("relationship") or "")
    event_evidence = candidate.get("breaking_event_evidence")
    material_update_evidence = candidate.get("material_update_evidence")
    event_or_update = bool(event_evidence) or (
        relationship == "material_update" and bool(material_update_evidence)
    )
    checks = {
        "materiality": materiality is not None and materiality >= BREAKING_MINIMUM_MATERIALITY,
        "urgency": float(scores["urgency"]) >= BREAKING_MINIMUM_URGENCY,
        "significance_or_breadth": significance_or_breadth is not None and significance_or_breadth >= BREAKING_MINIMUM_SIGNIFICANCE_OR_BREADTH,
        "breaking_event_or_material_update_evidence": event_or_update,
    }
    return {
        "qualified": all(checks.values()),
        "checks": checks,
        "observed": {
            "materiality": materiality,
            "urgency": float(scores["urgency"]),
            "significance": significance,
            "breadth": breadth,
            "relationship": relationship,
        },
    }


def _publication_decision(scored: Mapping[str, Any]) -> str:
    candidate = scored["candidate"]
    if _breaking_qualification(scored)["qualified"]:
        return "PUBLISH_BREAKING_OR_HIGH_IMPACT"
    fallback = evaluate_deep_analysis_fallback(candidate, scored["raw_scores"])["selected_fallback"]
    if fallback == "fresh_official_data_analysis":
        return "PUBLISH_FRESH_ANALYSIS"
    if candidate.get("article_mode") in {"analysis", "deep_analysis", "research_note"}:
        return "PUBLISH_DEEP_ANALYSIS"
    return "PUBLISH_FRESH_ANALYSIS"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _dimension(
    score: float | None,
    reason_codes: Sequence[str],
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    available = score is not None
    return {
        "availability": "AVAILABLE" if available else "UNAVAILABLE",
        "score": round(max(0.0, min(100.0, float(score))), 2) if available else None,
        "reason_codes": list(reason_codes),
        "evidence_refs": list(evidence_refs),
    }


def _explicit_dimension(candidate: Mapping[str, Any], name: str) -> dict[str, Any] | None:
    value = (candidate.get("ranking_inputs") or {}).get(name)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return _dimension(None, ["invalid_explicit_ranking_input"])
    if value.get("availability") == "UNAVAILABLE" or value.get("score") is None:
        return _dimension(None, value.get("reason_codes") or ["explicitly_unavailable"])
    return _dimension(
        float(value["score"]),
        value.get("reason_codes") or ["explicit_governed_ranking_input"],
        value.get("evidence_refs") or [],
    )


def _weighted_available_average(dimensions: Mapping[str, Mapping[str, Any]], names: Sequence[str]) -> float:
    measured = [
        (RANKING_DIMENSION_WEIGHTS[name], float(dimensions[name]["score"]))
        for name in names
        if dimensions[name]["availability"] == "AVAILABLE"
    ]
    if not measured:
        return 0.0
    weight_total = sum(weight for weight, _ in measured)
    return round(sum(weight * score for weight, score in measured) / weight_total, 2)


def calculate_candidate_scores(
    candidate: Mapping[str, Any],
    cutoff_dt: datetime,
    weights: Mapping[str, float],
    concentration_context: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Build an inspectable evidence-derived ranking; unavailable never means zero."""
    dimensions: dict[str, dict[str, Any]] = {}
    explicit_names = set((candidate.get("ranking_inputs") or {}).keys())

    numeric_claims = list(candidate.get("numeric_claims") or [])
    changes = [abs(float(row["change_basis_points"])) for row in numeric_claims if row.get("change_basis_points") is not None]
    dimensions["materiality"] = _explicit_dimension(candidate, "materiality") or (
        _dimension(min(100.0, max(changes) * 10.0), ["measured_numeric_change_basis_points"], [str(row.get("claim_id")) for row in numeric_claims])
        if changes else _dimension(None, ["unavailable_no_measured_change"])
    )
    for name in (
        "policy_economic_geopolitical_significance",
        "surprise",
        "affected_market_economy_breadth",
        "audience_relevance",
        "durability",
        "visual_feasibility",
    ):
        dimensions[name] = _explicit_dimension(candidate, name) or _dimension(None, [f"unavailable_no_explicit_{name}_evidence"])

    authority_score = {"exact": 100.0, "proxy": 60.0}.get(str(candidate.get("evidence_class") or ""))
    dimensions["source_authority"] = _explicit_dimension(candidate, "source_authority") or _dimension(
        authority_score,
        ["evidence_class_exact" if authority_score == 100.0 else "evidence_class_proxy"] if authority_score is not None else ["unavailable_non_publishable_evidence_class"],
        [str(candidate.get("source_packet_id") or "")],
    )

    try:
        known_at = _parse_utc(str(candidate["known_at_utc"]))
        age_seconds = max(0.0, (cutoff_dt - known_at).total_seconds())
        max_age_seconds = float((candidate.get("freshness") or {}).get("max_age_hours")) * 3600.0
        freshness_score = min(100.0, max(0.0, (1.0 - age_seconds / max_age_seconds) * 100.0))
        dimensions["freshness"] = _explicit_dimension(candidate, "freshness") or _dimension(
            freshness_score, ["point_in_time_linear_decay"], [str(candidate.get("known_at_utc"))]
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        dimensions["freshness"] = _explicit_dimension(candidate, "freshness") or _dimension(None, ["unavailable_invalid_freshness_inputs"])

    completeness_checks = {
        "source_documents": bool(candidate.get("source_documents")),
        "numeric_claims": bool(numeric_claims),
        "citation_map": bool(candidate.get("citation_map")),
        "permissions": (candidate.get("claim_permissions") or {}).get("decision") == "ALLOW",
        "source_health": (candidate.get("source_health") or {}).get("status") == "HEALTHY",
    }
    dimensions["evidence_completeness"] = _explicit_dimension(candidate, "evidence_completeness") or _dimension(
        100.0 * sum(completeness_checks.values()) / len(completeness_checks),
        [f"{name}_{'present' if passed else 'missing'}" for name, passed in completeness_checks.items()],
    )
    novelty_scores = {"new_phase": 90.0, "material_update": 80.0, "correction": 75.0}
    novelty_score = novelty_scores.get(str(candidate.get("relationship") or ""))
    dimensions["novelty"] = _explicit_dimension(candidate, "novelty") or _dimension(
        novelty_score,
        [f"update_relationship_{candidate.get('relationship') or 'missing'}"] if novelty_score is not None else ["unavailable_no_qualifying_update_relationship"],
        [str(candidate.get("update_chain_id") or "")],
    )
    calculated_claims = [str(row.get("claim_id")) for row in numeric_claims if row.get("calculation")]
    dimensions["original_analysis_potential"] = _explicit_dimension(candidate, "original_analysis_potential") or (
        _dimension(85.0, ["reproducible_calculated_claim_present"], calculated_claims)
        if calculated_claims else _dimension(None, ["unavailable_no_reproducible_original_calculation"])
    )
    low_overclaim_risk = (
        candidate.get("evidence_class") in ALLOWED_EVIDENCE_CLASSES
        and all(row.get("public_claim_allowed") is True for row in numeric_claims)
        and not candidate.get("blockers")
    )
    dimensions["overclaiming_risk"] = _explicit_dimension(candidate, "overclaiming_risk") or _dimension(
        100.0 if low_overclaim_risk else 25.0,
        ["low_overclaiming_risk_explicit_authority" if low_overclaim_risk else "elevated_overclaiming_risk"],
    )
    concentration_context = dict(concentration_context or {})
    concentration_reasons = [name for name, present in concentration_context.items() if present]
    concentration_score = max(0.0, 100.0 - 25.0 * len(concentration_reasons))
    dimensions["topic_source_day_concentration"] = _explicit_dimension(candidate, "topic_source_day_concentration") or _dimension(
        concentration_score,
        concentration_reasons or ["no_prior_topic_source_or_mode_concentration"],
    )

    # Guard against misspelled explicit inputs silently escaping the inspectable model.
    unknown_inputs = sorted(explicit_names - set(RANKING_DIMENSION_WEIGHTS))
    impact_names = (
        "materiality", "policy_economic_geopolitical_significance", "affected_market_economy_breadth",
        "source_authority", "evidence_completeness", "audience_relevance", "novelty", "durability",
        "original_analysis_potential", "overclaiming_risk",
    )
    urgency_names = ("materiality", "surprise", "freshness", "novelty", "source_authority")
    return {
        "ranking_model_version": RANKING_MODEL_VERSION,
        "dimensions": dimensions,
        "availability_summary": {
            "available": sum(row["availability"] == "AVAILABLE" for row in dimensions.values()),
            "unavailable": sum(row["availability"] == "UNAVAILABLE" for row in dimensions.values()),
            "unknown_explicit_inputs": unknown_inputs,
        },
        "impact": _weighted_available_average(dimensions, impact_names),
        "urgency": _weighted_available_average(dimensions, urgency_names),
        "freshness": float(dimensions["freshness"]["score"] or 0.0),
        "total": _weighted_available_average(dimensions, tuple(RANKING_DIMENSION_WEIGHTS)),
        "legacy_window_weights_observed": dict(weights),
    }


def evaluate_deep_analysis_fallback(candidate: Mapping[str, Any] | None, raw_scores: Mapping[str, Any] | None) -> dict[str, Any]:
    """Evaluate the required fallback ladder in strict order without granting authority."""
    candidate = candidate or {}
    raw_scores = raw_scores or {}
    dimensions = raw_scores.get("dimensions") or {}
    checks = [
        ("material_update", candidate.get("relationship") == "material_update", ["relationship_material_update"]),
        (
            "fresh_official_data_analysis",
            candidate.get("evidence_class") == "exact" and (dimensions.get("freshness") or {}).get("availability") == "AVAILABLE" and float((dimensions.get("freshness") or {}).get("score") or 0.0) > 0.0,
            ["exact_source", "freshness_measured", "numeric_claims_present"],
        ),
        (
            "structural_analysis_with_measurable_new_delta",
            (dimensions.get("original_analysis_potential") or {}).get("availability") == "AVAILABLE" and (dimensions.get("materiality") or {}).get("availability") == "AVAILABLE",
            ["original_calculation_present", "material_delta_measured"],
        ),
        (
            "conditional_scenario",
            candidate.get("article_mode") == "scenario_outlook" and bool(candidate.get("scenario_conditions")),
            ["conditional_scenario_explicit"],
        ),
    ]
    steps = []
    selected = "no_publication"
    for index, (name, available, reasons) in enumerate(checks, start=1):
        steps.append({"order": index, "fallback": name, "available": bool(available), "reason_codes": reasons})
        if selected == "no_publication" and available:
            selected = name
    steps.append({"order": 5, "fallback": "no_publication", "available": selected == "no_publication", "reason_codes": ["no_earlier_fallback_available"]})
    return {"ordered_steps": steps, "selected_fallback": selected, "publication_authority": False}


def evaluate_window_decision(
    *,
    window: Mapping[str, Any],
    schedule_date: str,
    pool: Mapping[str, Any],
    previously_published: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Execute one deterministic, fail-closed newsroom decision window."""
    window_id = str(window["window_id"])
    target_time = time.fromisoformat(str(window["target_cutoff_utc"]))
    base_date = datetime.strptime(schedule_date, "%Y-%m-%d").date()
    cutoff_dt = datetime.combine(base_date, target_time, tzinfo=timezone.utc)
    if pool.get("schema_version") != "capital_chronicle.newsroom_candidate_pool.v1":
        raise ValueError("unsupported_candidate_pool_schema")

    published_topics = {p.get("story_family") for p in previously_published if p.get("story_family")}
    published_modes = {p.get("article_mode") for p in previously_published if p.get("article_mode")}
    published_authorities = {
        auth for p in previously_published
        for auth in (p.get("authority") or {}).get("source_authorities") or []
    }
    published_candidate_ids = {p.get("candidate_id") for p in previously_published if p.get("candidate_id")}
    published_clusters = {p.get("cluster_id") for p in previously_published if p.get("cluster_id")}
    published_chains = {p.get("update_chain_id") for p in previously_published if p.get("update_chain_id")}
    scored_candidates: list[dict[str, Any]] = []
    backlog: list[dict[str, Any]] = []

    for candidate in pool.get("eligible_candidates") or []:
        gate_blockers = _candidate_hard_gate(candidate, cutoff_dt)
        relation = str(candidate.get("relationship") or "")
        reentry_justification = str(candidate.get("article_version_justification") or "").strip()
        same_candidate = candidate.get("candidate_id") in published_candidate_ids
        same_cluster = candidate.get("cluster_id") in published_clusters
        same_chain = candidate.get("update_chain_id") in published_chains
        reentry_allowed = relation in ALLOWED_REENTRY_RELATIONSHIPS and bool(reentry_justification)
        if same_candidate:
            gate_blockers.append("candidate_already_published")
        if relation in BLOCKED_UPDATE_RELATIONSHIPS:
            gate_blockers.append("update_chain_without_material_update")
        if (same_cluster or same_chain) and not reentry_allowed:
            gate_blockers.append("historical_cluster_or_chain_without_justified_new_version")
        if gate_blockers:
            backlog.append({
                "candidate": candidate,
                "raw_scores": None,
                "penalties": [],
                "penalty_total": 0.0,
                "final_score": 0.0,
                "gate_blockers": sorted(set(gate_blockers)),
            })
            continue

        concentration_context = {
            "topic_concentration": candidate.get("story_family") in published_topics,
            "mode_concentration": candidate.get("article_mode") in published_modes,
            "source_concentration": bool(set((candidate.get("authority") or {}).get("source_authorities") or []).intersection(published_authorities)),
        }
        scores = calculate_candidate_scores(candidate, cutoff_dt, window["score_weights"], concentration_context)
        penalties: list[str] = []
        penalty_total = 0.0
        if concentration_context["topic_concentration"]:
            penalties.append("topic_concentration")
            penalty_total += 15.0
        if concentration_context["mode_concentration"]:
            penalties.append("mode_concentration")
            penalty_total += 10.0
        if concentration_context["source_concentration"]:
            penalties.append("source_concentration")
            penalty_total += 12.0
        scored_candidates.append({
            "candidate": candidate,
            "raw_scores": scores,
            "penalties": penalties,
            "penalty_total": penalty_total,
            "final_score": round(max(0.0, scores["total"] - penalty_total), 2),
            "gate_blockers": [],
        })

    scored_candidates.sort(key=lambda row: (
        -row["final_score"],
        -row["raw_scores"]["urgency"],
        -row["raw_scores"]["impact"],
        str(row["candidate"].get("known_at_utc") or ""),
        str(row["candidate"].get("candidate_id") or ""),
    ))
    selected = None
    preemption_contract = None
    decision = "NO_PUBLICATION_THRESHOLD_NOT_MET"
    rationale = "No fully gated candidate met the window urgency and impact thresholds."
    minimum_urgency = float(window["minimum_urgency_threshold"])
    minimum_impact = float(window["minimum_impact_threshold"])

    threshold_candidates = [row for row in scored_candidates if (
        row["raw_scores"]["urgency"] >= minimum_urgency
        and row["raw_scores"]["impact"] >= minimum_impact
        and row["final_score"] >= minimum_urgency
    )]
    at_limit = len(previously_published) >= int(window.get("daily_portfolio_limit", 99))
    if threshold_candidates and not at_limit:
        selected = threshold_candidates[0]
        decision = _publication_decision(selected)
        rationale = f"Top-ranked fully gated candidate meets thresholds: {selected['candidate']['title']}"
    elif threshold_candidates and at_limit and window.get("preemption_allowed"):
        top = threshold_candidates[0]
        prior = min(
            previously_published,
            key=lambda row: (float(row.get("_schedule_final_score", 0.0)), str(row.get("candidate_id") or "")),
            default=None,
        )
        baseline_score = float((prior or {}).get("_schedule_final_score", 0.0))
        impact_delta = round(top["final_score"] - baseline_score, 2)
        minimum_delta = float(window.get("minimum_preemption_impact_delta", 15.0))
        qualification = _breaking_qualification(top)
        if (
            prior
            and prior.get("_schedule_window_id")
            and qualification["qualified"]
            and impact_delta >= minimum_delta
        ):
            selected = top
            decision = "PUBLISH_BREAKING_OR_HIGH_IMPACT"
            rationale = f"Fully gated breaking candidate preempts {prior['_schedule_window_id']} with impact delta {impact_delta:.2f}."
            preemption_contract = {
                "trigger_time": cutoff_dt.isoformat().replace("+00:00", "Z"),
                "selected_candidate": top["candidate"]["candidate_id"],
                "preempted_window": prior["_schedule_window_id"],
                "preempted_candidate": prior.get("candidate_id"),
                "impact_delta": impact_delta,
                "reason_codes": ["explicit_breaking_qualification_passed", "configured_impact_delta_exceeded"],
                "evidence_requirements": ["candidate_hard_gates_passed", "breaking_materiality_urgency_significance_and_event_checks_passed", "minimum_preemption_delta_met"],
                "breaking_qualification": qualification,
                "operator_state": "OPERATOR_REVIEW_REQUIRED",
                "publication_deadline": cutoff_dt.isoformat().replace("+00:00", "Z"),
            }
            preemption_contract["decision_hash"] = _logical_hash(preemption_contract)
    elif scored_candidates and not at_limit:
        top = scored_candidates[0]
        if (
            top["raw_scores"]["urgency"] >= minimum_urgency - 10.0
            or top["raw_scores"]["impact"] >= minimum_impact - 10.0
            or top["final_score"] >= minimum_urgency - 10.0
        ):
            decision = "HOLD_FOR_MORE_EVIDENCE"
            rationale = f"Top fully gated candidate {top['candidate']['title']} is close to thresholds; holding."

    considered = selected or (scored_candidates[0] if scored_candidates else None)
    selected_id = (selected or {}).get("candidate", {}).get("candidate_id")
    ranked_backlog = [row for row in scored_candidates if row["candidate"].get("candidate_id") != selected_id]
    return {
        "window_id": window_id,
        "name": window["name"],
        "cutoff_time_utc": cutoff_dt.isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "rationale": rationale,
        "ranking_model_version": RANKING_MODEL_VERSION,
        "selected_candidate": selected["candidate"] if selected else None,
        "preemption_contract": preemption_contract,
        "breaking_qualification": _breaking_qualification(considered) if considered and considered["raw_scores"] else None,
        "deep_analysis_fallback_evidence": evaluate_deep_analysis_fallback(
            considered["candidate"] if considered else None,
            considered["raw_scores"] if considered else None,
        ),
        "score_details": {
            "raw_scores": considered["raw_scores"] if considered else None,
            "penalties": considered["penalties"] if considered else [],
            "penalty_total": considered["penalty_total"] if considered else 0.0,
            "final_score": considered["final_score"] if considered else 0.0,
        },
        "backlog_candidates": [
            {
                "candidate_id": row["candidate"].get("candidate_id"),
                "title": row["candidate"].get("title"),
                "final_score": row["final_score"],
                "relationship": row["candidate"].get("relationship"),
                "blocked_reasons": row.get("gate_blockers") or [],
            }
            for row in ranked_backlog + sorted(backlog, key=lambda item: str(item["candidate"].get("candidate_id") or ""))
        ],
    }


def build_newsroom_schedule(
    *,
    schedule_date: str,
    pool_path: Path,
    windows_path: Path,
    output_dir: Path,
    historical_publications_path: Path | None = None,
) -> dict[str, Any]:
    """Process all five windows from governed history to produce the newsroom schedule."""
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    config = json.loads(windows_path.read_text(encoding="utf-8"))

    errors = []
    if pool.get("schema_version") != "capital_chronicle.newsroom_candidate_pool.v1":
        errors.append("pool_schema_version_invalid")
    if not pool.get("database_binding") or not pool["database_binding"].get("head_sha"):
        errors.append("database_binding_missing")
    producer = pool.get("producer_binding") or {}
    expected_producer = {
        "upstream_repository": EXPECTED_UPSTREAM_REPOSITORY,
        "upstream_branch": EXPECTED_UPSTREAM_BRANCH,
        "candidate_pool_producer_commit_sha": EXPECTED_CANDIDATE_POOL_PRODUCER_COMMIT_SHA,
    }
    for field, expected in expected_producer.items():
        if producer.get(field) != expected:
            errors.append(f"producer_binding_{field}_missing_or_mismatched")
    required_producer_fields = (
        "candidate_pool_artifact_sha256", "pool_id", "pool_logical_hash", "schema_version",
        "schema_hash", "candidate_hashes", "cutoff_time_utc",
    )
    for field in required_producer_fields:
        if producer.get(field) in (None, "", []):
            errors.append(f"producer_binding_{field}_missing")
    pool_generated_at = pool.get("generated_at_utc")
    try:
        if not isinstance(pool_generated_at, str) or _parse_utc(pool_generated_at).utcoffset() != timedelta(0):
            raise ValueError
    except (TypeError, ValueError):
        errors.append("pool_generated_at_utc_invalid")

    core = {k: v for k, v in pool.items() if k not in ("pool_id", "logical_hash", "producer_binding")}
    expected_hash = _logical_hash(core)
    if pool.get("logical_hash") != expected_hash:
        errors.append("pool_logical_hash_mismatch")
    if producer:
        if producer.get("pool_id") != pool.get("pool_id") or producer.get("pool_logical_hash") != pool.get("logical_hash"):
            errors.append("producer_binding_pool_identity_mismatch")
        if producer.get("schema_version") != pool.get("schema_version") or producer.get("cutoff_time_utc") != pool.get("cutoff_time_utc"):
            errors.append("producer_binding_pool_contract_mismatch")
        actual_candidate_hashes = sorted(
            str(row.get("evidence_hash")) for row in [*(pool.get("eligible_candidates") or []), *(pool.get("rejected_candidates") or [])]
        )
        if producer.get("candidate_hashes") != actual_candidate_hashes:
            errors.append("producer_binding_candidate_hashes_mismatch")

    if errors:
        raise ValueError(f"candidate_pool_invalid: {', '.join(errors)}")

    historical_seed = []
    if historical_publications_path is not None:
        history = json.loads(historical_publications_path.read_text(encoding="utf-8"))
        if history.get("schema_version") != "contentops.historical_publication_seed.v1":
            raise ValueError("historical_publication_seed_schema_invalid")
        historical_seed = list(history.get("publications") or [])
        if not historical_seed:
            raise ValueError("historical_publication_seed_empty")
    previously_published = [dict(row) for row in historical_seed]
    decisions = []
    new_publications = []

    for window in config["windows"]:
        dec = evaluate_window_decision(
            window=window,
            schedule_date=schedule_date,
            pool=pool,
            previously_published=previously_published,
        )
        decisions.append(dec)
        if dec["decision"] in PUBLISH_DECISIONS:
            published = dict(dec["selected_candidate"])
            published["_schedule_window_id"] = dec["window_id"]
            published["_schedule_final_score"] = dec["score_details"]["final_score"]
            previously_published.append(published)
            new_publications.append(published)

    schedule = {
        "schema_version": SCHEMA_VERSION,
        "schedule_date": schedule_date,
        "generated_at_utc": pool_generated_at,
        "database_input_authority_sha": pool["database_binding"]["head_sha"],
        "candidate_pool_producer_binding": producer,
        "pool_id": pool["pool_id"],
        "pool_logical_hash": pool["logical_hash"],
        "historical_publication_seed": {
            "path": str(historical_publications_path).replace("\\", "/") if historical_publications_path else None,
            "count": len(historical_seed),
            "logical_hash": _logical_hash({"publications": historical_seed}) if historical_seed else None,
        },
        "decisions": decisions,
        "summary": {
            "total_windows": len(decisions),
            "historical_publications_seeded": len(historical_seed),
            "publications": len(new_publications),
            "backlog_count": sum(len(d["backlog_candidates"]) for d in decisions),
        }
    }
    
    digest = _logical_hash(schedule)
    schedule["schedule_id"] = f"cc-schedule-{digest[:20]}"
    schedule["logical_hash"] = digest
    
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"newsroom_schedule_{schedule_date.replace('-', '_')}.json"
    out_path.write_text(json.dumps(schedule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return schedule


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic ContentOps daily schedule.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--historical-publications", type=Path)
    args = parser.parse_args(argv)

    try:
        schedule = build_newsroom_schedule(
            schedule_date=args.date,
            pool_path=args.pool,
            windows_path=args.windows,
            output_dir=args.output_dir,
            historical_publications_path=args.historical_publications,
        )
        print(json.dumps({
            "schedule_id": schedule["schedule_id"],
            "publications": schedule["summary"]["publications"],
        }))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
