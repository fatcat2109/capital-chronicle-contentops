import json
import os
import pytest
from live_contentops import editorial_quality

def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_unsafe_financial_advice_is_blocked():
    req = load_fixture("unsafe_financial_advice.json")
    res = editorial_quality.evaluate_quality(req)
    assert res["score_summary"]["safety_risk"] >= 10
    assert "buy" in res["blocked_claims_detected"]
    assert "guaranteed prediction" in res["blocked_claims_detected"]
    assert res["not_public_postable_reason"] is not None
    assert "forbidden claims" in res["not_public_postable_reason"].lower()

def test_synthetic_demo_is_not_postable():
    req = load_fixture("synthetic_demo_threads.json")
    res = editorial_quality.evaluate_quality(req)
    assert res["not_public_postable_reason"] is not None
    assert "synthetic" in res["not_public_postable_reason"].lower()
    assert res["is_advisory_only"] is True

def test_safe_good_linkedin_scores_well():
    req = load_fixture("safe_good_linkedin.json")
    res = editorial_quality.evaluate_quality(req)
    # Limitation is present
    assert res["score_summary"]["limitation_visibility"] == 10
    # Professional spacing
    assert res["score_summary"]["platform_fit"] == 10
    # No forbidden claims
    assert res["score_summary"]["safety_risk"] == 0
    assert res["not_public_postable_reason"] is None
    assert res["is_advisory_only"] is True

def test_missing_limitation_lowers_score():
    req = {
        "text": "Are large language models shifting quant strategies?\n\nRecent data suggests a 15% increase in NLP-driven signals.",
        "platform": "linkedin",
        "audience": "quant_systematic_trader",
        "is_synthetic_demo": False
    }
    res = editorial_quality.evaluate_quality(req)
    assert res["score_summary"]["limitation_visibility"] < 10

def test_source_discipline_failure():
    req = {
        "text": "Check out this source: fakeurl.com.",
        "platform": "x"
    }
    res = editorial_quality.evaluate_quality(req)
    assert res["score_summary"]["source_discipline"] == 0
    assert "fake url" in res["not_public_postable_reason"].lower() or "source discipline" in res["not_public_postable_reason"].lower()
