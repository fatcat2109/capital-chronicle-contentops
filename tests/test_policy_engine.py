from live_contentops.policy_engine import evaluate_policy
from live_contentops import policy_rules

def test_policy_engine_source_required():
    res = evaluate_policy({"source_state": "source_required"})
    assert res["status"] == policy_rules.BLOCKED_SOURCE_REQUIRED

def test_policy_engine_forbidden_strings():
    res = evaluate_policy({"text": "we must buy this"})
    assert res["status"] == policy_rules.BLOCKED_FORBIDDEN_FINANCIAL_ADVICE
