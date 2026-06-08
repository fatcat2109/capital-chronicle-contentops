from live_contentops.policy_engine import evaluate_policy

def test_policy_engine_source_required():
    assert evaluate_policy({"source_state": "source_required"}) == "blocked"
    assert evaluate_policy({"source_state": "source_required", "source_bundle_ids": ["123"]}) == "review_required"

def test_policy_engine_forbidden_strings():
    assert evaluate_policy({"text": "we must buy this"}) == "blocked"
    assert evaluate_policy({"text": "position sizing is key"}) == "blocked"
    assert evaluate_policy({"text": "partisan hack"}) == "blocked"
    assert evaluate_policy({"text": "this is fine"}) == "review_required"
