"""Test content backlog loop generation rules."""
from __future__ import annotations

from live_contentops import content_backlog_loop_v6 as backlog


def test_generate_backlog_candidates():
    clusters = [
        {
            "cluster_id": "c1",
            "cluster_label": "source_request",
            "backlog_candidate_allowed": True,
            "blocked_reasons": []
        },
        {
            "cluster_id": "c2",
            "cluster_label": "methodology_question",
            "backlog_candidate_allowed": True,
            "blocked_reasons": ["private_identifier_detected"]
        },
        {
            "cluster_id": "c3",
            "cluster_label": "unsafe_financial_advice_request",
            "backlog_candidate_allowed": False,
            "blocked_reasons": ["unsafe_financial_advice_request_detected"]
        }
    ]

    candidates = backlog.generate_backlog_candidates(clusters)

    # Cluster c3 should be excluded because backlog_candidate_allowed is False
    assert not any(c["source_cluster_id"] == "c3" for c in candidates)

    # Candidate for c1 should be allowed for drafting since c1 is not blocked
    c1_cand = next(c for c in candidates if c["source_cluster_id"] == "c1")
    assert c1_cand["allowed_for_drafting"] is True
    assert c1_cand["allowed_for_publication"] is False
    assert c1_cand["source_verification_required"] is True
    assert len(c1_cand["required_sources"]) > 0
    assert len(c1_cand["required_caveats"]) > 0

    # Candidate for c2 should NOT be allowed for drafting since c2 has blockers
    c2_cand = next(c for c in candidates if c["source_cluster_id"] == "c2")
    assert c2_cand["allowed_for_drafting"] is False


def test_generate_article_idea_candidates():
    backlog_candidates = [
        {
            "backlog_id": "b1",
            "source_cluster_id": "c1",
            "proposed_canonical_article_angle": "Deep dive into source validation.",
            "research_questions": ["Q1?"],
            "allowed_for_drafting": True
        },
        {
            "backlog_id": "b2",
            "source_cluster_id": "c2",
            "proposed_canonical_article_angle": "Drafting blocked angle.",
            "research_questions": ["Q2?"],
            "allowed_for_drafting": False
        }
    ]

    ideas = backlog.generate_article_idea_candidates(backlog_candidates)
    assert len(ideas) == 1
    assert ideas[0]["source_backlog_id"] == "b1"
    assert ideas[0]["allowed_for_publication"] is False
    assert ideas[0]["human_review_required"] is True
