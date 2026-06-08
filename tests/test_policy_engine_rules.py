import json
import pytest
from pathlib import Path
from live_contentops import policy_engine, policy_rules

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "policy" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_safe_evergreen_review_required():
    data = load_fixture("valid_evergreen_review_required.json")
    res = policy_engine.evaluate_policy(data)
    assert res["status"] == policy_rules.PASS_REVIEW_REQUIRED
    assert res["safe_to_continue_to_human_review"] is True
    assert res["safe_for_publish"] is False

def test_source_required_without_sources():
    data = load_fixture("blocked_source_required.json")
    res = policy_engine.evaluate_policy(data)
    assert res["status"] == policy_rules.BLOCKED_SOURCE_REQUIRED
    assert res["safe_to_continue_to_human_review"] is False

def test_source_required_with_sources():
    data = load_fixture("blocked_source_required.json")
    data["source_bundle_ids"] = ["123"]
    res = policy_engine.evaluate_policy(data)
    assert res["status"] == policy_rules.PASS_REVIEW_REQUIRED
    assert res["safe_to_continue_to_human_review"] is True

def test_financial_advice_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_financial_advice.json"))
    assert res["status"] == policy_rules.BLOCKED_FORBIDDEN_FINANCIAL_ADVICE

def test_position_sizing_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_position_sizing.json"))
    assert res["status"] == policy_rules.BLOCKED_POSITION_SIZING

def test_guaranteed_prediction_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_guaranteed_prediction.json"))
    assert res["status"] == policy_rules.BLOCKED_GUARANTEED_PREDICTION

def test_broker_execution_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_broker_execution.json"))
    assert res["status"] == policy_rules.BLOCKED_BROKER_OR_EXECUTION

def test_partisan_persuasion_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_partisan_persuasion.json"))
    assert res["status"] == policy_rules.BLOCKED_PARTISAN_PERSUASION

def test_election_guidance_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_election_guidance.json"))
    assert res["status"] == policy_rules.BLOCKED_ELECTION_GUIDANCE

def test_auto_publish_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_auto_publish.json"))
    assert res["status"] == policy_rules.BLOCKED_AUTO_PUBLISH_REQUEST

def test_secret_like_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_secret_like.json"))
    assert res["status"] == policy_rules.BLOCKED_SECRET_OR_CREDENTIAL

def test_live_flags_true_blocks():
    res = policy_engine.evaluate_policy(load_fixture("blocked_live_flags_true.json"))
    assert res["status"] == policy_rules.BLOCKED_LIVE_FLAGS_TRUE

def test_neutral_policy_passes():
    res = policy_engine.evaluate_policy(load_fixture("neutral_policy_transmission_allowed.json"))
    assert res["status"] == policy_rules.PASS_REVIEW_REQUIRED

def test_high_risk_review_required():
    res = policy_engine.evaluate_policy(load_fixture("high_risk_review_required.json"))
    assert res["status"] == policy_rules.PASS_REVIEW_REQUIRED

def test_no_decision_sets_publish_true():
    res = policy_engine.evaluate_policy(load_fixture("valid_evergreen_review_required.json"))
    assert res["safe_for_publish"] is False
