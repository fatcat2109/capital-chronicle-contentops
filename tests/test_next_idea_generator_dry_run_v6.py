"""Test next idea generator candidate refinement rules."""
from __future__ import annotations

from live_contentops import next_idea_generator_dry_run_v6 as generator


def test_refine_idea_candidates():
    backlog_candidates = [
        {
            "backlog_id": "b1",
            "source_cluster_id": "c1",
            "proposed_canonical_article_angle": "Test Angle",
            "research_questions": ["Q1"],
            "suggested_platform_variants": ["substack_canonical"],
            "priority_score": 8.0,
            "allowed_for_drafting": True,
            "blocked_reasons": []
        }
    ]

    refined = generator.refine_idea_candidates(backlog_candidates)

    assert len(refined) == 1
    idea = refined[0]
    assert idea["source_backlog_id"] == "b1"
    assert idea["source_verification_required"] is True
    assert idea["allowed_for_publication"] is False
    assert idea["public_postable"] is False
    assert idea["human_review_required"] is True
    assert idea["no_auto_response"] is True
    assert "c1" in idea["source_cluster_ids"]
    assert idea["readiness_state"] == "REVIEW_ONLY_REQUIRES_SOURCE_VERIFICATION"
