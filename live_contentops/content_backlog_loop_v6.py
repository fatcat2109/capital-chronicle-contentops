"""V6 Content Backlog Loop.

Generates content backlog candidates from classified clusters.
"""
from __future__ import annotations

import hashlib
from typing import Any


def generate_backlog_candidates(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transforms safe question clusters into review-only content backlog candidates."""
    candidates = []

    for cluster in clusters:
        # Check if backlog candidate is allowed for this cluster
        if not cluster.get("backlog_candidate_allowed", True):
            continue

        label = cluster.get("cluster_label", "clarification_question")
        cluster_id = cluster.get("cluster_id", "")

        # Deterministic generation of angles and research questions based on label
        if label == "source_request":
            proposed_canonical_article_angle = "Deep dive into source verification and data provenance of recent macroeconomic reports."
            research_questions = [
                "Which primary sources ground our recent yield volatility analysis?",
                "What database or index matches the cited unverified sample metrics?"
            ]
            priority_score = 8.0
        elif label == "methodology_question":
            proposed_canonical_article_angle = "Educational breakdown of calculation models and methodology used in yield curve parsing."
            research_questions = [
                "What is the mathematical structure behind historical yield curve adjustments?",
                "How do different models weigh interest rate volatility over a multi-decade horizon?"
            ]
            priority_score = 7.0
        elif label == "content_topic_request":
            proposed_canonical_article_angle = "Educational analysis covering proposed user topic on interest rate structures."
            research_questions = [
                "What is the historical basis for the requested macroeconomic topic?",
                "How does this topic relate to the broader Treasury market ecosystem?"
            ]
            priority_score = 9.0
        elif label == "correction_request":
            proposed_canonical_article_angle = "Editorial review and corrective analysis of key macroeconomic indices."
            research_questions = [
                "Where do our recent data mappings diverge from verified primary documentation?",
                "What updates are required to reconcile the historical yield series?"
            ]
            priority_score = 9.5
        elif label == "disagreement_or_challenge":
            proposed_canonical_article_angle = "Reconciling conflicting perspectives on interest rate trends."
            research_questions = [
                "What are the primary counter-arguments to our yield volatility hypothesis?",
                "Does empirical data support or refute the challenger's claim?"
            ]
            priority_score = 6.0
        else:
            proposed_canonical_article_angle = f"Macroeconomic educational analysis addressing {label}."
            research_questions = [
                f"What clarifications are requested regarding {label}?",
                "How can we explain this concept more clearly in future updates?"
            ]
            priority_score = 5.0

        # Required caveats list
        required_caveats = [
            "Macroeconomic parameters are highly uncertain and model-dependent.",
            "This analysis is for educational purposes only; consult licensed financial professionals."
        ]

        # Generate backlog ID
        hasher = hashlib.sha256(f"{cluster_id}_{label}".encode("utf-8"))
        backlog_id = f"backlog_{hasher.hexdigest()[:12]}"

        # Check if allowed for drafting
        cluster_blocked = bool(cluster.get("blocked_reasons", []))
        allowed_for_drafting = not cluster_blocked

        candidate = {
            "backlog_id": backlog_id,
            "source_cluster_id": cluster_id,
            "proposed_canonical_article_angle": proposed_canonical_article_angle,
            "research_questions": research_questions,
            "required_sources": ["operator_verified_data_ref"],
            "required_caveats": required_caveats,
            "suggested_platform_variants": ["substack_canonical", "discord_drop"],
            "priority_score": priority_score,
            "source_verification_required": True,
            "allowed_for_drafting": allowed_for_drafting,
            "allowed_for_publication": False,
            "human_review_required": True,
            "no_auto_response": True
        }
        candidates.append(candidate)

    # Sort backlog candidates by priority score descending
    return sorted(candidates, key=lambda c: c["priority_score"], reverse=True)


def generate_article_idea_candidates(backlog_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transforms content backlog candidates into next canonical article idea candidates."""
    ideas = []

    for index, bc in enumerate(backlog_candidates):
        # Only allow drafting-safe candidates
        if not bc.get("allowed_for_drafting", False):
            continue

        hasher = hashlib.sha256(bc["backlog_id"].encode("utf-8"))
        idea_id = f"idea_{hasher.hexdigest()[:12]}"

        idea = {
            "idea_id": idea_id,
            "source_backlog_id": bc["backlog_id"],
            "title_candidate": bc["proposed_canonical_article_angle"].replace("Deep dive into", "Deep Dive:").replace("Educational breakdown of", "Breakdown:"),
            "target_word_count": 800,
            "suggested_outline": bc["research_questions"],
            "required_verification_checklist": [
                "Verify primary sources are documented",
                "Ensure no forward-looking signal language",
                "Review against compliance guidelines"
            ],
            "allowed_for_publication": False,
            "human_review_required": True
        }
        ideas.append(idea)

    return ideas
