"""Test V6 Canonical Article Studio Placeholder Binding Review."""
from __future__ import annotations

from live_contentops import canonical_article_studio_placeholder_binding_review_v6 as review_builder


def test_make_canonical_article_studio_placeholder_binding_review():
    review = review_builder.make_canonical_article_studio_placeholder_binding_review()

    assert review["review_status"] == "PLACEHOLDER_BINDING_REVIEW_ONLY_BLOCKED"
    assert review["placeholder_count"] == 9
    assert review["all_slots_bound_to_empty_placeholders"] is True
    assert review["all_placeholder_values_null"] is True
    assert review["no_article_copy_generated"] is True
    assert review["no_source_values_materialized"] is True
    assert review["runtime_generation_allowed"] is False
    assert review["publication_allowed"] is False
    assert review["dispatch_allowed"] is False
    assert "real_source_pack_not_approved" in review["blockers"]
    assert "runtime_operator_approval_missing" in review["blockers"]
