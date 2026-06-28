"""V6 Feedback to Article Backlog Refiner.

Refines content backlog candidates safely, preserving blockers and review-only states.
"""
from __future__ import annotations

from typing import Any


def refine_backlog_candidates(backlog_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Refines backlog entries, ensuring safety flags and blockers are strictly preserved."""
    refined = []

    for bc in backlog_candidates:
        bc_copy = dict(bc)

        # Enforce safety invariants
        bc_copy["source_verification_required"] = True
        bc_copy["allowed_for_publication"] = False
        bc_copy["no_auto_response"] = True
        bc_copy["human_review_required"] = True

        # Check if the backlog entry has any blockers or contains unsafe markers
        blocked_reasons = list(bc_copy.get("blocked_reasons", []))
        
        # If it was not allowed for drafting or cluster was unsafe, ensure it remains blocked
        if bc_copy.get("allowed_for_drafting") is False:
            if "source_verification_required" not in blocked_reasons:
                blocked_reasons.append("source_verification_required")
            if "publication_blocked_until_source_verification" not in blocked_reasons:
                blocked_reasons.append("publication_blocked_until_source_verification")

        bc_copy["blocked_reasons"] = sorted(list(set(blocked_reasons)))

        # Ensure no auto-response or reply drafts are created
        bc_copy["auto_reply_created"] = False
        bc_copy["public_ready"] = False

        refined.append(bc_copy)

    return refined
