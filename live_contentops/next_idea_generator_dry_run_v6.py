"""V6 Next Idea Generator Dry-Run.

Refines content backlog candidates into canonical article idea targets without running active LLM models.
"""
from __future__ import annotations

import hashlib
from typing import Any


def refine_idea_candidates(backlog_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transforms content backlog candidates into highly structured review-only refined ideas."""
    refined_ideas = []

    for bc in backlog_candidates:
        backlog_id = bc.get("backlog_id", "stub_backlog_id")
        cluster_id = bc.get("source_cluster_id", "stub_cluster_id")
        priority = bc.get("priority_score", 5.0)
        allowed_for_drafting = bc.get("allowed_for_drafting", True)
        blocked_reasons = list(bc.get("blocked_reasons", []))

        hasher = hashlib.sha256(backlog_id.encode("utf-8"))
        refined_id = f"refined_idea_{hasher.hexdigest()[:12]}"

        angle = bc.get("proposed_canonical_article_angle", "General Angle")
        title_candidate = f"Refined Study: {angle.replace('Deep dive into ', '').replace('Educational analysis ', '')}"
        thesis_candidate = f"Macroeconomic data suggests historical trends are relevant to understanding current yield curves."
        audience_need = "Understanding underlying interest rate structures and data provenance."
        evidence_required = "Verified historical series of Treasury yields and curve metrics."

        refined = {
            "refined_idea_id": refined_id,
            "source_backlog_id": backlog_id,
            "source_cluster_ids": [cluster_id],
            "title_candidate": title_candidate,
            "thesis_candidate": thesis_candidate,
            "audience_need": audience_need,
            "evidence_required": evidence_required,
            "source_verification_required": True,
            "required_caveats": bc.get("required_caveats", [
                "Macroeconomic parameters are highly uncertain and model-dependent."
            ]),
            "outline": bc.get("research_questions", ["What is the historical evidence?"]),
            "platform_variant_targets": bc.get("suggested_platform_variants", ["substack_canonical", "discord_drop"]),
            "priority_score": priority,
            "readiness_state": "REVIEW_ONLY_REQUIRES_SOURCE_VERIFICATION",
            "allowed_for_drafting": allowed_for_drafting,
            "allowed_for_publication": False,
            "public_postable": False,
            "human_review_required": True,
            "no_auto_response": True,
            "blocked_reasons": blocked_reasons
        }

        refined_ideas.append(refined)

    # Sort by priority score descending
    return sorted(refined_ideas, key=lambda r: r["priority_score"], reverse=True)
