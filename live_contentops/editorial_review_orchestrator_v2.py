"""Bounded multi-role editorial review over approved evidence only."""
from __future__ import annotations

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


def _claim_blockers(article: Mapping[str, Any], packet: Mapping[str, Any]) -> list[str]:
    approved = {str(row.get("claim_id")) for row in packet.get("numeric_claims") or [] if row.get("public_claim_allowed")}
    used = {str(value) for value in article.get("claim_ids_used") or []}
    blockers = [f"unapproved_claim:{value}" for value in sorted(used - approved)]
    citations = packet.get("citation_map") or {}
    blockers.extend(f"claim_missing_citation:{value}" for value in sorted(used) if not citations.get(value))
    if article.get("numeric_claims_from_llm"):
        blockers.append("llm_numeric_authority_forbidden")
    if article.get("cross_asset_assertions") and not article.get("cross_asset_claim_ids"):
        blockers.append("generic_cross_asset_assertions_without_evidence")
    return blockers


def run_editorial_review(
    *,
    request: Mapping[str, Any],
    packet: Mapping[str, Any],
    article: Mapping[str, Any],
    freshness_decision: Mapping[str, Any],
    visual_decision: Mapping[str, Any],
    structured_reviewer: Callable[[str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
    revision_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    roles: list[dict[str, Any]] = []
    global_blockers: list[str] = []
    if revision_contract and revision_contract.get("status") == "BLOCK":
        global_blockers.extend(f"editorial_revision_v2:{value}" for value in revision_contract.get("blockers") or [])
    for role in ROLE_ORDER:
        blockers: list[str] = []
        if role == "assignment_editor" and not request.get("story_type"):
            blockers.append("story_type_required")
        elif role == "evidence_planner":
            blockers.extend(packet.get("validation_blockers") or [])
            if packet.get("public_claim_permissions", {}).get("decision") != "ALLOW":
                blockers.append("evidence_packet_public_claim_permission_blocked")
        elif role == "reporter_writer":
            blockers.extend(_claim_blockers(article, packet))
        elif role == "quantitative_editor":
            blockers.extend(article.get("quantitative_blockers") or [])
        elif role == "visual_editor" and visual_decision.get("status") != "PASS":
            blockers.extend(visual_decision.get("blockers") or [])
        elif role == "copy_editor":
            blockers.extend(_source_calibration_blockers(article, packet))
            if request.get("article_mode") and article.get("article_mode") and request.get("article_mode") != article.get("article_mode"):
                blockers.append("article_mode_inconsistent_with_assignment")
            if request.get("market_sensitive") and not article.get("as_of_utc"):
                blockers.append("market_sensitive_article_requires_explicit_as_of")
            if re.search(r"\b(guaranteed return|buy now|sell now|risk-free)\b", str(article.get("rendered_body") or ""), re.IGNORECASE):
                blockers.append("financial_advice_or_promotional_language")
        elif role == "platform_editor" and article.get("hard_truncation_used"):
            blockers.append("hard_truncation_forbidden")
        elif role == "adversarial_final_reviewer":
            if freshness_decision.get("decision") != "PASS":
                blockers.extend(freshness_decision.get("blockers") or [])
            if structured_reviewer is None:
                blockers.append("structured_adversarial_review_unavailable")
            else:
                try:
                    review = dict(structured_reviewer(role, {"request": request, "article": article, "packet_id": packet.get("packet_id")}))
                    if review.get("decision") != "PASS" or review.get("publication_authority") is not False:
                        blockers.append("structured_adversarial_review_failed_or_claimed_authority")
                except Exception:
                    blockers.append("structured_adversarial_review_malformed")
        role_row = {"role": role, "status": "PASS" if not blockers else "BLOCK", "blockers": blockers}
        role_row["output_hash"] = _hash(role_row)
        roles.append(role_row)
        global_blockers.extend(blockers)
    return {
        "schema_version": "contentops.editorial_review_orchestrator.v2",
        "status": "PASS" if not global_blockers else "BLOCK",
        "role_order": list(ROLE_ORDER),
        "roles": roles,
        "writer_self_certification_allowed": False,
        "deterministic_blockers_authoritative": True,
        "final_render_reviewed": bool(article.get("rendered_body")),
        "blockers": list(dict.fromkeys(global_blockers)),
        "revision_contract_status": (revision_contract or {}).get("status", "NOT_REQUESTED"),
        "packet_hash": _hash({"roles": roles, "article": article, "revision_contract": revision_contract or {}}),
    }
