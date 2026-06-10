import os
import json
from live_contentops.approval_ledger import validate_approval_record, validate_kill_switch_state, validate_audit_event, check_action_allowed

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "approval_ledger")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_operator_review_required():
    rec = _load("valid_operator_review_required.json")
    res = validate_approval_record(rec)
    assert res["valid"] is True

def test_valid_operator_approved_for_mock_publish():
    rec = _load("valid_operator_approved_for_mock_publish.json")
    res = validate_approval_record(rec)
    assert res["valid"] is True

def test_valid_revoked_approval():
    rec = _load("valid_revoked_approval.json")
    res = validate_approval_record(rec)
    assert res["valid"] is True

def test_invalid_live_publish_approval_before_gate():
    rec = _load("invalid_live_publish_approval_before_gate.json")
    res = validate_approval_record(rec)
    assert res["valid"] is False
    assert "live_publish_attempt_without_explicit_future_gate" in res["errors"]

def test_invalid_missing_operator_approval_ref():
    rec = _load("invalid_missing_operator_approval_ref.json")
    res = validate_approval_record(rec)
    assert res["valid"] is False
    assert "missing_operator_approval_ref" in res["errors"]

def test_invalid_kill_switch_disabled_for_publish_attempt():
    ks = _load("invalid_kill_switch_disabled_for_publish_attempt.json")
    res = validate_kill_switch_state(ks)
    assert res["valid"] is False
    assert "kill_switch_must_be_enabled" in res["errors"]

def test_invalid_unredacted_secret_in_audit_event():
    aud = _load("invalid_unredacted_secret_in_audit_event.json")
    res = validate_audit_event(aud)
    assert res["valid"] is False
    assert any("unsafe_secret_detected" in e for e in res["errors"])

def test_valid_audit_event():
    aud = _load("valid_audit_event.json")
    res = validate_audit_event(aud)
    assert res["valid"] is True

def test_check_action_allowed_mock():
    rec = _load("valid_operator_approved_for_mock_publish.json")
    ks = _load("valid_kill_switch_for_mock.json")
    res = check_action_allowed(rec, ks)
    assert res["allowed"] is True

def test_check_action_allowed_blocks_revoked():
    rec = _load("valid_revoked_approval.json")
    ks = _load("valid_kill_switch_for_mock.json")
    res = check_action_allowed(rec, ks)
    assert res["allowed"] is False
    assert "approval_revoked" in res["errors"]
