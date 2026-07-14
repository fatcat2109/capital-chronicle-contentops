"""Deterministic verifier for the human-labeled Capital Chronicle editorial corpus."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "contentops.editorial_evaluation_corpus_verifier.v1"
RUBRIC_FIELDS = (
    "accuracy", "source_quality", "claim_traceability", "materiality", "originality",
    "information_density", "structure", "headline_calibration", "mechanism_quality",
    "uncertainty_handling", "reader_utility", "seo_hygiene", "visual_utility",
    "overall_acceptance",
)
REQUIRED_COVERAGE = {
    "strong_headline", "weak_headline", "factual_error", "semantic_error", "overclaiming",
    "stale_story", "proxy_misuse", "repetition", "poor_seo", "excellent_original_value",
    "malformed_reviewer_output", "scenario_correctly_labeled", "scenario_masquerading_as_forecast",
    "unsupported_numeric_claim", "missing_citation", "proxy_promoted_to_exact",
    "semantic_paraphrase_repetition", "repeated_conclusion", "internal_workflow_vocabulary",
    "clickbait_headline",
}


def _logical_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def verify_editorial_evaluation_corpus(corpus: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    cases = list(corpus.get("cases") or [])
    pairs = list(corpus.get("pairwise_judgments") or [])
    case_ids = [str(row.get("case_id") or "") for row in cases]
    labels = {str(label) for row in cases for label in (row.get("coverage_labels") or [])}
    dispositions = {str(row.get("expected_disposition") or "") for row in cases}
    story_types = {str(row.get("story_type") or "") for row in cases}
    if corpus.get("schema_version") != "contentops.editorial_evaluation_corpus.v1": blockers.append("schema_version_invalid")
    if corpus.get("publication_authority") is not False or corpus.get("fixture_only") is not True: blockers.append("corpus_must_be_fixture_only_without_publication_authority")
    if len(cases) < 15: blockers.append("minimum_case_count_not_met")
    if len(story_types) < 5: blockers.append("multiple_story_types_not_met")
    if dispositions != {"ACCEPT", "REJECT"}: blockers.append("accepted_and_rejected_cases_required")
    if len(case_ids) != len(set(case_ids)) or not all(case_ids): blockers.append("case_ids_invalid_or_duplicate")
    configured_coverage = {str(label) for label in (corpus.get("required_coverage_labels") or [])}
    if configured_coverage != REQUIRED_COVERAGE:
        blockers.append("configured_coverage_matrix_mismatch")
    missing_coverage = sorted(REQUIRED_COVERAGE - labels)
    if missing_coverage: blockers.append("required_coverage_missing:" + ",".join(missing_coverage))
    for row in cases:
        rubric = row.get("human_rubric") if isinstance(row.get("human_rubric"), Mapping) else {}
        missing = [field for field in RUBRIC_FIELDS if field not in rubric]
        if missing: blockers.append(f"{row.get('case_id')}:rubric_fields_missing:" + ",".join(missing)); continue
        numeric = [rubric[field] for field in RUBRIC_FIELDS[:-1]]
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > 5 for value in numeric): blockers.append(f"{row.get('case_id')}:rubric_score_out_of_range")
        if rubric["overall_acceptance"] != row.get("expected_disposition"): blockers.append(f"{row.get('case_id')}:acceptance_label_mismatch")
        if not str(row.get("human_rationale") or "").strip(): blockers.append(f"{row.get('case_id')}:human_rationale_missing")
    known_ids = set(case_ids)
    for pair in pairs:
        preferred, rejected = pair.get("preferred_case_id"), pair.get("rejected_case_id")
        if preferred not in known_ids or rejected not in known_ids or preferred == rejected: blockers.append(f"{pair.get('pair_id')}:pair_references_invalid")
        else:
            by_id = {row["case_id"]: row for row in cases}
            if by_id[preferred]["expected_disposition"] != "ACCEPT" or by_id[rejected]["expected_disposition"] != "REJECT": blockers.append(f"{pair.get('pair_id')}:pair_direction_invalid")
    summary = {"case_count": len(cases), "story_type_count": len(story_types), "accepted_count": sum(row.get("expected_disposition") == "ACCEPT" for row in cases), "rejected_count": sum(row.get("expected_disposition") == "REJECT" for row in cases), "pairwise_count": len(pairs), "coverage_labels": sorted(labels)}
    return {"schema_version": SCHEMA_VERSION, "status": "PASS" if not blockers else "BLOCKED", "blockers": blockers, "summary": summary, "corpus_logical_hash": _logical_hash(corpus), "publication_authority": False}


def verify_corpus_file(path: Path) -> dict[str, Any]:
    return verify_editorial_evaluation_corpus(json.loads(path.read_text(encoding="utf-8")))
