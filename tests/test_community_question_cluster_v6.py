"""Test community question clustering rules and safety enforcement."""
from __future__ import annotations

from live_contentops import community_question_cluster_v6 as clustering


def test_classify_text():
    assert clustering.classify_text("Where can I find the source dataset?") == "source_request"
    assert clustering.classify_text("What is your calculation method?") == "methodology_question"
    assert clustering.classify_text("There is a typo in paragraph 2.") == "correction_request"
    assert clustering.classify_text("Should I buy this asset or hold?") == "unsafe_financial_advice_request"
    assert clustering.classify_text("This looks like spam.") == "spam_or_low_signal"
    assert clustering.classify_text("Please clarify what this concept means.") == "clarification_question"


def test_generate_clusters_safety():
    snaps = [
        {
            "snapshot_id": "s1",
            "raw_feedback_text_redacted": "Should I sell my position now?",
            "blocked_reasons": []
        },
        {
            "snapshot_id": "s2",
            "raw_feedback_text_redacted": "Where is the source link?",
            "blocked_reasons": []
        }
    ]
    clusters = clustering.generate_clusters(snaps)
    # Check that unsafe_financial_advice_request cluster has backlog_candidate_allowed = False
    financial_cluster = next(c for c in clusters if c["cluster_label"] == "unsafe_financial_advice_request")
    assert financial_cluster["backlog_candidate_allowed"] is False
    assert "unsafe_financial_advice_request_detected" in financial_cluster["blocked_reasons"]

    # Check source_request cluster has backlog_candidate_allowed = True
    source_cluster = next(c for c in clusters if c["cluster_label"] == "source_request")
    assert source_cluster["backlog_candidate_allowed"] is True
    assert len(source_cluster["blocked_reasons"]) == 0
