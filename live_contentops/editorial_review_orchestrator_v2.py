"""Bounded multi-role editorial review over approved evidence only."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any, Callable, Mapping, Sequence

ROLE_ORDER = (
    "assignment_editor", "evidence_planner", "reporter_writer", "quantitative_editor",
    "visual_editor", "copy_editor", "platform_editor", "adversarial_final_reviewer",
)
INTERNAL_TERMS = ("manifest-bound", "chart manifest", "pipeline", "run id", "source packet")
AWKWARD_PATTERNS = (r"\bis\s+Reopened\b", r"\brelevant transmission channel is\b")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _source_calibration_blockers(article: Mapping[str, Any], packet: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    title = str(article.get("title") or "")
    body = str(article.get("rendered_body") or article.get("body") or "")
    public_text = f"{title}\n{body}"
    lowered = public_text.casefold()
    if "pre-war" in lowered:
        source_text = " ".join(str(row.get("title") or row.get("summary") or "") for row in packet.get("official_source_documents") or []).casefold()
        if "pre-war" not in source_text and "pre-conflict" in source_text:
            blockers.append("headline_escalates_pre_conflict_to_pre_war")
    blockers.extend(f"internal_process_vocabulary:{term}" for term in INTERNAL_TERMS if term in lowered)
    blockers.extend(f"awkward_templated_construction:{pattern}" for pattern in AWKWARD_PATTERNS if re.search(pattern, public_text, re.IGNORECASE))
    if public_text.casefold().count("not financial advice") > 1:
        blockers.append("repeated_disclaimer")
    return blockers


def _is_v3(packet: Mapping[str, Any]) -> bool:
    return (
        packet.get("schema_version")
        == "capital_chronicle_content_evidence_packet.v3"
    )


def _approved_claim_map(
    packet: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    if _is_v3(packet):
        graph = packet.get("governed_claim_graph") or {}
        approved_ids = {
            str(value) for value in graph.get("approved_claim_ids") or []
        }
        return {
            str(row["claim_id"]): row
            for row in graph.get("claims") or []
            if row.get("claim_id") and str(row["claim_id"]) in approved_ids
        }
    return {
        str(row["claim_id"]): row
        for row in packet.get("numeric_claims") or []
        if row.get("claim_id") and row.get("public_claim_allowed") is True
    }


def _claim_citation_urls(
    packet: Mapping[str, Any],
    claim: Mapping[str, Any],
) -> list[str]:
    if _is_v3(packet):
        return sorted({
            str(row["url"])
            for row in claim.get("citations") or []
            if row.get("url")
        })
    return sorted({
        str(value)
        for value in (packet.get("citation_map") or {}).get(
            str(claim.get("claim_id") or ""), []
        )
        if value
    })


def _number_tokens(value: Any) -> set[str]:
    number_pattern = re.compile(
        r"(?<![A-Za-z0-9_])[-+]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)"
        r"(?![A-Za-z0-9_])"
    )
    if isinstance(value, Mapping):
        result: set[str] = set()
        for nested in value.values():
            result.update(_number_tokens(nested))
        return result
    if isinstance(value, (list, tuple, set)):
        result = set()
        for nested in value:
            result.update(_number_tokens(nested))
        return result
    if isinstance(value, bool) or value is None:
        return set()
    return {
        match.group(0).replace(",", "")
        for match in number_pattern.finditer(str(value))
    }


def _normalized_number(value: str) -> str:
    try:
        normalized = Decimal(value)
    except InvalidOperation:
        return value
    return format(normalized.normalize(), "f")


def _v3_article_blockers(
    *,
    article: Mapping[str, Any],
    packet: Mapping[str, Any],
    claim_map: Mapping[str, Mapping[str, Any]],
    used: set[str],
) -> list[str]:
    blockers: list[str] = []
    approved = set(claim_map)
    for field in (
        "title_claim_ids_used",
        "summary_claim_ids_used",
        "body_claim_ids_used",
    ):
        if field not in article:
            blockers.append(f"v3_{field}_required")
            continue
        section_ids = {str(value) for value in article.get(field) or []}
        blockers.extend(
            f"v3_{field}_unapproved:{claim_id}"
            for claim_id in sorted(section_ids - approved)
        )
        blockers.extend(
            f"v3_{field}_not_declared_in_article:{claim_id}"
            for claim_id in sorted(section_ids - used)
        )
    if {
        str(value) for value in article.get("body_claim_ids_used") or []
    } != used:
        blockers.append("v3_body_claim_ids_not_exact_article_claim_set")

    article_citations = article.get("claim_citations")
    if not isinstance(article_citations, Mapping):
        blockers.append("v3_article_claim_citations_required")
        article_citations = {}
    authority_used = article.get("claim_authority_used")
    if not isinstance(authority_used, Mapping):
        blockers.append("v3_claim_authority_binding_required")
        authority_used = {}
    permission_used = article.get("claim_permissions_used")
    if not isinstance(permission_used, Mapping):
        blockers.append("v3_claim_permission_binding_required")
        permission_used = {}
    for claim_id in sorted(used):
        claim = claim_map.get(claim_id) or {}
        supplied_urls = sorted({
            str(value)
            for value in article_citations.get(claim_id) or []
            if value
        })
        if supplied_urls != _claim_citation_urls(packet, claim):
            blockers.append(f"v3_article_citation_mismatch:{claim_id}")
        if authority_used.get(claim_id) != claim.get("authority_class"):
            blockers.append(f"v3_claim_authority_mismatch:{claim_id}")
        if permission_used.get(claim_id) != claim.get("permission_state"):
            blockers.append(
                f"v3_claim_permission_upgrade_or_mismatch:{claim_id}"
            )

    rendered_text = " ".join(
        str(article.get(field) or "")
        for field in ("title", "summary", "rendered_body")
    )
    rendered_numbers = {
        _normalized_number(value) for value in _number_tokens(rendered_text)
    }
    governed_numbers: set[str] = set()
    for claim_id in used & approved:
        claim = claim_map[claim_id]
        for field in ("statement", "structured_payload", "numeric"):
            governed_numbers.update(
                _normalized_number(value)
                for value in _number_tokens(claim.get(field))
            )
    blockers.extend(
        f"v3_unevidenced_numeric_token:{value}"
        for value in sorted(rendered_numbers - governed_numbers)
    )

    reaction_ids = {
        str(value) for value in article.get("market_reaction_claim_ids") or []
    }
    reaction_prose = bool(article.get("market_reaction_assertions")) or bool(
        re.search(
            r"\b(?:markets?|shares?|stocks?|bonds?|yields?|prices?|dollar|"
            r"currenc(?:y|ies)|futures)\b.{0,48}\b(?:rose|fell|rallied|"
            r"declined|jumped|dropped|gained|lost|reacted|repriced|moved)\b",
            rendered_text,
            re.IGNORECASE,
        )
    )
    if reaction_prose and not reaction_ids:
        blockers.append("market_reaction_prose_requires_governed_claim_ids")
    for claim_id in sorted(reaction_ids):
        claim = claim_map.get(claim_id)
        if claim_id not in used:
            blockers.append(
                f"market_reaction_claim_not_declared_in_article:{claim_id}"
            )
        if not claim or claim.get("claim_type") != "market_reaction":
            blockers.append(f"market_reaction_claim_type_invalid:{claim_id}")
        elif not claim.get("market_evidence_refs"):
            blockers.append(
                f"market_reaction_separate_evidence_missing:{claim_id}"
            )
    return blockers


def _claim_blockers(
    article: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> list[str]:
    claim_map = _approved_claim_map(packet)
    approved = set(claim_map)
    used = {str(value) for value in article.get("claim_ids_used") or []}
    blockers = [
        f"unapproved_claim:{value}" for value in sorted(used - approved)
    ]
    blockers.extend(
        f"claim_missing_citation:{value}"
        for value in sorted(used)
        if not _claim_citation_urls(packet, claim_map.get(value) or {})
    )
    if article.get("numeric_claims_from_llm"):
        blockers.append("llm_numeric_authority_forbidden")
    if article.get("cross_asset_assertions") and not article.get(
        "cross_asset_claim_ids"
    ):
        blockers.append("generic_cross_asset_assertions_without_evidence")
    if _is_v3(packet):
        blockers.extend(_v3_article_blockers(
            article=article,
            packet=packet,
            claim_map=claim_map,
            used=used,
        ))
    return list(dict.fromkeys(blockers))


def run_editorial_review(
    *,
    request: Mapping[str, Any],
    packet: Mapping[str, Any],
    article: Mapping[str, Any],
    freshness_decision: Mapping[str, Any],
    visual_decision: Mapping[str, Any],
    structured_reviewer: Callable[
        [str, Mapping[str, Any]], Mapping[str, Any]
    ] | None = None,
    revision_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    roles: list[dict[str, Any]] = []
    global_blockers: list[str] = []
    claim_map = _approved_claim_map(packet)
    approved = set(claim_map)
    used = {str(value) for value in article.get("claim_ids_used") or []}
    numeric_ids = sorted(
        claim_id
        for claim_id in used & approved
        if not _is_v3(packet)
        or claim_map[claim_id].get("claim_type") == "numeric_observation"
    )
    if revision_contract and revision_contract.get("status") == "BLOCK":
        global_blockers.extend(
            f"editorial_revision_v2:{value}"
            for value in revision_contract.get("blockers") or []
        )
    context = {
        "request": dict(request),
        "evidence_packet": dict(packet),
        "article": dict(article),
        "freshness_decision": dict(freshness_decision),
        "visual_decision": dict(visual_decision),
        "approved_claim_ids": sorted(approved),
        "reviewed_claim_ids": sorted(used),
        "numeric_claim_ids": numeric_ids,
        "v3_contract": _is_v3(packet),
        "accumulated_blockers": [],
    }
    for role in ROLE_ORDER:
        blockers: list[str] = []
        if role == "assignment_editor" and not request.get("story_type"):
            blockers.append("story_type_required")
        elif role == "evidence_planner":
            blockers.extend(packet.get("validation_blockers") or [])
            permission_key = (
                "generic_claim_permissions"
                if _is_v3(packet)
                else "public_claim_permissions"
            )
            if (packet.get(permission_key) or {}).get("decision") != "ALLOW":
                blockers.append(
                    "evidence_packet_public_claim_permission_blocked"
                )
        elif role == "reporter_writer":
            blockers.extend(_claim_blockers(article, packet))
        elif role == "quantitative_editor":
            if not _is_v3(packet) or numeric_ids:
                blockers.extend(article.get("quantitative_blockers") or [])
        elif role == "visual_editor":
            visual_status = visual_decision.get("status")
            if visual_status != "PASS":
                visual_blockers = list(visual_decision.get("blockers") or [])
                blockers.extend(visual_blockers or [
                    "visual_decision_unavailable"
                    if visual_status is None
                    else "visual_decision_blocked_without_blockers"
                ])
        elif role == "copy_editor":
            blockers.extend(_source_calibration_blockers(article, packet))
            if (
                request.get("article_mode")
                and article.get("article_mode")
                and request.get("article_mode") != article.get("article_mode")
            ):
                blockers.append("article_mode_inconsistent_with_assignment")
            if request.get("market_sensitive") and not article.get("as_of_utc"):
                blockers.append(
                    "market_sensitive_article_requires_explicit_as_of"
                )
            if re.search(
                r"\b(guaranteed return|buy now|sell now|risk-free)\b",
                str(article.get("rendered_body") or ""),
                re.IGNORECASE,
            ):
                blockers.append(
                    "financial_advice_or_promotional_language"
                )
        elif role == "platform_editor" and article.get("hard_truncation_used"):
            blockers.append("hard_truncation_forbidden")
        elif role == "adversarial_final_reviewer":
            freshness_status = freshness_decision.get("decision")
            if freshness_status != "PASS":
                freshness_blockers = list(
                    freshness_decision.get("blockers") or []
                )
                blockers.extend(freshness_blockers or [
                    "freshness_decision_unavailable"
                    if freshness_status is None
                    else "freshness_decision_blocked_without_blockers"
                ])

        structured_review: Mapping[str, Any] | None = None
        if _is_v3(packet) or role == "adversarial_final_reviewer":
            if structured_reviewer is None:
                blockers.append(
                    "structured_adversarial_review_unavailable"
                    if role == "adversarial_final_reviewer"
                    else f"structured_role_review_unavailable:{role}"
                )
            else:
                try:
                    structured_review = dict(
                        structured_reviewer(role, context)
                    )
                    if (
                        structured_review.get("decision") != "PASS"
                        or structured_review.get("publication_authority") is not False
                    ):
                        blockers.append(
                            "structured_adversarial_review_failed_or_claimed_authority"
                            if role == "adversarial_final_reviewer"
                            else f"structured_role_review_failed_or_claimed_authority:{role}"
                        )
                    checks = structured_review.get("checks")
                    substantive = (
                        bool(structured_review.get("review_basis"))
                        and structured_review.get("reviewed_claim_ids")
                        == sorted(used)
                        and isinstance(checks, Mapping)
                        and bool(checks)
                    )
                    if _is_v3(packet):
                        substantive = substantive and structured_review.get(
                            "evidence_packet_logical_hash"
                        ) == packet.get("logical_hash")
                    if (
                        (_is_v3(packet) or role == "adversarial_final_reviewer")
                        and (
                            not substantive
                            or (
                                structured_review.get("decision") == "PASS"
                                and not all(
                                    value is True for value in checks.values()
                                )
                            )
                        )
                    ):
                        blockers.append(
                            "structured_adversarial_review_not_substantive"
                            if role == "adversarial_final_reviewer"
                            else f"structured_role_review_not_substantive:{role}"
                        )
                except Exception:
                    blockers.append(
                        "structured_adversarial_review_malformed"
                        if role == "adversarial_final_reviewer"
                        else f"structured_role_review_malformed:{role}"
                    )
        blockers = list(dict.fromkeys(str(value) for value in blockers))
        role_row: dict[str, Any] = {
            "role": role,
            "status": "PASS" if not blockers else "BLOCK",
            "blockers": blockers,
        }
        if structured_review is not None:
            role_row["structured_review"] = dict(structured_review)
        role_row["output_hash"] = _hash(role_row)
        roles.append(role_row)
        global_blockers.extend(blockers)
        context["accumulated_blockers"] = list(
            dict.fromkeys(global_blockers)
        )
    global_blockers = list(dict.fromkeys(global_blockers))
    return {
        "schema_version": "contentops.editorial_review_orchestrator.v2",
        "status": "PASS" if not global_blockers else "BLOCK",
        "editorial_disposition": (
            "PASS" if not global_blockers else "HOLD"
        ),
        "role_order": list(ROLE_ORDER),
        "roles": roles,
        "approved_claim_ids": sorted(approved),
        "used_claim_ids": sorted(used),
        "numeric_claim_ids_used": numeric_ids,
        "governed_claim_contract": (
            "V3_GENERIC_CLAIM_GRAPH"
            if _is_v3(packet)
            else "V2_NUMERIC_COMPATIBILITY"
        ),
        "writer_self_certification_allowed": False,
        "deterministic_blockers_authoritative": True,
        "final_render_reviewed": bool(article.get("rendered_body")),
        "blockers": global_blockers,
        "revision_contract_status": (
            revision_contract or {}
        ).get("status", "NOT_REQUESTED"),
        "publication_authority": False,
        "packet_hash": _hash({
            "roles": roles,
            "article": article,
            "revision_contract": revision_contract or {},
        }),
    }
