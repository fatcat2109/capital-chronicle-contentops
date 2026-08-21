"""Explicit V1 MVP canary acceptance profile.

The profile separates factual/system/public-write safety from editorial-quality telemetry.
It is intentionally opt-in.  The normal production editorial gate remains unchanged, and a
canary-ready result grants neither public-write authority nor production-day throughput credit.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from live_contentops.tier1_editorial_quality_v1 import (
    LLM_MATERIAL_REVIEW_CHECKS,
    evaluate_reader_value,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)


MVP_CANARY_ACCEPTANCE_PROFILE = "MVP_CANARY_LAUNCH_GATE_V1"
STANDARD_ACCEPTANCE_PROFILE = "STANDARD_PRODUCTION_VALIDATION_V1"

MVP_CANARY_HARD_SEMANTIC_CHECKS = frozenset(
    {
        "material_claims_supported",
        "no_factual_contradiction",
        "no_fabricated_numbers",
        "material_evidence_matches",
        "no_misleading_framing",
        "severe_coherence_ok",
        "no_unsupported_certainty",
        "no_fabricated_quotes",
        "no_financial_advice",
    }
)

MVP_CANARY_HARD_DETERMINISTIC_CHECKS = frozenset(
    {
        "no_process_language",
        "no_fabricated_quotes",
        "no_financial_advice",
    }
)

_INSTITUTIONAL_QUALITY_EXACT = frozenset(
    {
        "search_freshness_class_invalid",
        "primary_reader_question_invalid",
        "boilerplate_search_title",
        "duplicated_conclusion",
        "keyword_stuffing",
        "internal_link_candidate_invalid",
        "internal_link_relation_invalid",
        "internal_link_anchor_not_descriptive",
        "structured_data_packet_missing",
        "declared_humor_line_not_present",
    }
)


def is_mvp_canary_profile(value: str | None) -> bool:
    return str(value or "") == MVP_CANARY_ACCEPTANCE_PROFILE


def classify_institutional_edge_blockers(
    blockers: Sequence[Any],
) -> dict[str, list[str]]:
    """Split deterministic institutional findings without deleting observability."""

    hard: list[str] = []
    quality: list[str] = []
    for raw in blockers:
        blocker = str(raw or "").strip()
        if not blocker:
            continue
        if blocker in _INSTITUTIONAL_QUALITY_EXACT:
            quality.append(blocker)
        else:
            # Fail closed. New validator codes must be explicitly reviewed before they can be
            # classified as nonfatal canary quality telemetry.
            hard.append(blocker)
    return {
        "hard_gate_blockers": sorted(set(hard)),
        "quality_warnings": sorted(set(quality)),
    }


def evaluate_mvp_canary_minimum_useful_floor(
    article: Mapping[str, Any],
    *,
    media_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Require useful professional copy without imposing the full production-quality target."""

    reader = evaluate_reader_value(article, media_assets=media_assets)
    title = " ".join(str(article.get("title") or "").split())
    dek = " ".join(
        str(article.get("subtitle") or article.get("dek") or "").split()
    )
    checks = {
        "coherent_headline_present": bool(title and len(title.split()) >= 4),
        "coherent_dek_present": bool(dek and dek.casefold() != title.casefold()),
        "valid_native_serialization": bool(
            (reader.get("checks") or {}).get("native_rich_text_serializable")
        ),
        "not_title_only_or_placeholder": bool(
            (reader.get("checks") or {}).get("title_not_body")
            and int(reader.get("meaningful_paragraph_count") or 0) >= 2
        ),
        "minimum_reader_substance": bool(
            int(reader.get("reader_prose_word_count") or 0) >= 60
            and int(reader.get("reader_sentence_count") or 0) >= 3
        ),
        "no_process_or_pipeline_leakage": bool(
            (reader.get("checks") or {}).get("no_process_or_pipeline_language")
        ),
        "not_attribution_chain_copy": bool(
            (reader.get("checks") or {}).get("not_attribution_chain_copy")
        ),
    }
    blockers = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "contentops.mvp_canary_minimum_useful_floor.v1",
        "classification": "PASS" if not blockers else "BLOCKED_MINIMUM_USEFUL_FLOOR",
        "checks": checks,
        "blockers": blockers,
        "reader_value_telemetry": reader,
        "publication_authority": False,
    }


def evaluate_mvp_canary_editorial_gate(
    *,
    article: Mapping[str, Any],
    deterministic_review: Mapping[str, Any],
    hard_factual_review: Mapping[str, Any],
    media_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Evaluate the canary editorial slice while preserving the standard audit as telemetry."""

    minimum_floor = evaluate_mvp_canary_minimum_useful_floor(
        article, media_assets=media_assets
    )
    deterministic_checks = dict(deterministic_review.get("editorial_checks") or {})
    deterministic_hard_failures = sorted(
        check
        for check in MVP_CANARY_HARD_DETERMINISTIC_CHECKS
        if deterministic_checks.get(check) is not True
    )
    semantic_checks = dict(hard_factual_review.get("checks") or {})
    semantic_hard_failures = sorted(
        check
        for check in MVP_CANARY_HARD_SEMANTIC_CHECKS
        if semantic_checks.get(check) is not True
    )
    malformed_material_checks = sorted(
        check
        for check in LLM_MATERIAL_REVIEW_CHECKS
        if check not in semantic_checks
    )
    hard_gate_blockers = [
        *minimum_floor["blockers"],
        *deterministic_hard_failures,
        *semantic_hard_failures,
        *(
            ["hard_factual_review_invalid_or_unavailable"]
            if hard_factual_review.get("status") != "SUCCESS"
            else []
        ),
        *(
            ["hard_factual_review_material_checks_missing"]
            if malformed_material_checks
            else []
        ),
    ]
    standard_editorial_blockers = {
        str(value) for value in deterministic_review.get("editorial_blockers") or []
    }
    quality_warnings = sorted(
        standard_editorial_blockers.difference(MVP_CANARY_HARD_DETERMINISTIC_CHECKS)
        | {str(value) for value in deterministic_review.get("seo_blockers") or []}
        | {
            str(value)
            for value in hard_factual_review.get("advisory_failed_checks") or []
            if str(value) not in MVP_CANARY_HARD_SEMANTIC_CHECKS
        }
        | {
            check
            for check in (
                "clear_news_peg",
                "mode_consistent",
                "reader_facing_prose",
            )
            if semantic_checks.get(check) is False
        }
    )
    hard_gate_blockers = sorted(set(hard_gate_blockers))
    return {
        "schema_version": "contentops.mvp_canary_editorial_gate.v1",
        "acceptance_profile": MVP_CANARY_ACCEPTANCE_PROFILE,
        "classification": "PASS" if not hard_gate_blockers else "BLOCKED_HARD_GATE",
        "hard_gate_blockers": hard_gate_blockers,
        "quality_warnings": quality_warnings,
        "minimum_useful_floor": minimum_floor,
        "standard_editorial_classification": deterministic_review.get("classification"),
        "standard_editorial_score": deterministic_review.get("editorial_score"),
        "standard_seo_score": deterministic_review.get("seo_score"),
        "standard_findings_remain_observable": True,
        "quality_warnings_grant_factual_authority": False,
        "publication_authority": False,
    }


def institutional_edge_hard_gate(
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    split = classify_institutional_edge_blockers(validation.get("blockers") or [])
    return {
        "classification": "PASS" if not split["hard_gate_blockers"] else "BLOCKED_HARD_GATE",
        **split,
        "full_standard_validation_classification": validation.get("classification"),
        "full_standard_validation_remains_observable": True,
        "publication_authority": False,
    }


def build_mvp_canary_launch_gate_record(
    *,
    editorial_gate: Mapping[str, Any],
    worker_validation: Mapping[str, Any],
    derivative_destinations: Sequence[str],
    publication_plan_destinations: Sequence[str],
    jit_preflight: Mapping[str, Any],
    rights_or_zero_media_pass: bool,
    public_write_count: int = 0,
    unknown_write_count: int = 0,
) -> dict[str, Any]:
    """Build the final zero-write owner-gate record; it never grants the owner decision."""

    derivative_set = {str(value) for value in derivative_destinations}
    publication_set = {str(value) for value in publication_plan_destinations}
    checks = {
        "mvp_canary_editorial_hard_gate": editorial_gate.get("classification") == "PASS",
        "native_xhigh_return_binding": worker_validation.get("classification")
        == "PASS_BOUND_XHIGH_EDITORIAL_RETURN",
        "exactly_eight_derivative_package_intents": derivative_set
        == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
        and len(tuple(derivative_destinations)) == 8,
        "exactly_nine_publication_plan_destinations": publication_set
        == set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
        and len(tuple(publication_plan_destinations)) == 9,
        "jit_nine_surface_identity_and_readiness": jit_preflight.get("status") == "READY"
        and jit_preflight.get("all_required_destinations_ready") is True,
        "rights_safe_or_zero_media": bool(rights_or_zero_media_pass),
        "zero_public_writes": int(public_write_count) == 0,
        "unknown_write_zero": int(unknown_write_count) == 0,
    }
    blockers = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "contentops.mvp_canary_launch_gate_record.v1",
        "acceptance_profile": MVP_CANARY_ACCEPTANCE_PROFILE,
        "classification": (
            "CANARY_READY_FOR_OWNER_PUBLIC_WRITE_GATE"
            if not blockers
            else "BLOCKED_MVP_CANARY_LAUNCH_GATE"
        ),
        "checks": checks,
        "hard_gate_blockers": blockers,
        "quality_warnings": sorted(
            {str(value) for value in editorial_gate.get("quality_warnings") or []}
        ),
        "standard_editorial_score": editorial_gate.get("standard_editorial_score"),
        "standard_seo_score": editorial_gate.get("standard_seo_score"),
        "owner_public_write_grant_required": True,
        "owner_public_write_grant_present": False,
        "public_write_authority": False,
        "authorizes_second_article": False,
        "authorizes_automation_enablement": False,
        "satisfies_post_launch_4_32_throughput_gate": False,
        "post_launch_throughput_gate": {
            "qualified_article_requirement": 4,
            "derivative_intent_requirement": 32,
            "still_required_before_unattended_production_grade_operation": True,
        },
        "quality_warnings_grant_factual_authority": False,
        "unknown_write_count": int(unknown_write_count),
        "public_write_count": int(public_write_count),
    }
