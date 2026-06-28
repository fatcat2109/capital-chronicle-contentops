"""V6 Canonical Article Studio Placeholder Binding Review.

Defines review schemas for empty placeholder bindings.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_placeholder_binding_review() -> dict[str, Any]:
    """Generates the placeholder binding review payload."""
    return {
        "review_status": "PLACEHOLDER_BINDING_REVIEW_ONLY_BLOCKED",
        "placeholder_count": 9,
        "all_slots_bound_to_empty_placeholders": True,
        "all_placeholder_values_null": True,
        "no_article_copy_generated": True,
        "no_source_values_materialized": True,
        "runtime_generation_allowed": False,
        "publication_allowed": False,
        "dispatch_allowed": False,
        "blockers": [
            "real_source_pack_not_approved",
            "runtime_operator_approval_missing",
            "placeholder_values_not_materialized",
            "article_copy_generation_blocked",
            "editor_review_required",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }
