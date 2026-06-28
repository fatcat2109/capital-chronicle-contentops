"""Test feedback to article backlog refiner rules."""
from __future__ import annotations

from live_contentops import feedback_to_article_backlog_refiner_v6 as refiner


def test_refine_backlog_candidates():
    backlog_candidates = [
        {
            "backlog_id": "b1",
            "allowed_for_drafting": True,
            "blocked_reasons": []
        },
        {
            "backlog_id": "b2",
            "allowed_for_drafting": False,
            "blocked_reasons": ["unsafe_financial_advice_request_detected"]
        }
    ]

    refined = refiner.refine_backlog_candidates(backlog_candidates)

    assert len(refined) == 2
    r1 = next(r for r in refined if r["backlog_id"] == "b1")
    assert r1["source_verification_required"] is True
    assert r1["allowed_for_publication"] is False
    assert r1["no_auto_response"] is True
    assert r1["human_review_required"] is True

    r2 = next(r for r in refined if r["backlog_id"] == "b2")
    assert "unsafe_financial_advice_request_detected" in r2["blocked_reasons"]
    assert r2["allowed_for_publication"] is False
    assert r2["no_auto_response"] is True
    assert r2["public_ready"] is False
