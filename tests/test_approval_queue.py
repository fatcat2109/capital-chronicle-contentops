import json
import pytest
from pathlib import Path
from live_contentops import approval_queue, audit_log, policy_rules

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "approval_queue" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_queue_item_builds_from_review_required():
    data = load_fixture("valid_review_required_policy_decision.json")
    item = approval_queue.build_queue_item_from_policy_decision(data)
    assert item["queue_status"] == "REVIEW_REQUIRED"
    assert item["safe_for_publish"] is False

def test_queue_item_builds_from_blocked():
    data = load_fixture("blocked_policy_decision.json")
    item = approval_queue.build_queue_item_from_policy_decision(data)
    assert item["queue_status"] == "BLOCKED"

def test_queue_item_builds_from_source_required():
    data = load_fixture("source_required_policy_decision.json")
    item = approval_queue.build_queue_item_from_policy_decision(data)
    assert item["queue_status"] == "SOURCE_REQUIRED"

def test_approval_for_blocked_fails():
    item = approval_queue.build_queue_item_from_policy_decision(load_fixture("blocked_policy_decision.json"))
    with pytest.raises(ValueError, match="Cannot approve an item that is BLOCKED"):
        approval_queue.apply_human_decision(item, "approve_for_future_dry_run_only", "jim", "looks fine")

def test_approval_for_source_required_fails():
    item = approval_queue.build_queue_item_from_policy_decision(load_fixture("source_required_policy_decision.json"))
    with pytest.raises(ValueError, match="Cannot approve an item that is .* SOURCE_REQUIRED"):
        approval_queue.apply_human_decision(item, "approve_for_future_dry_run_only", "jim", "looks fine")

def test_approval_for_review_required_success():
    item = approval_queue.build_queue_item_from_policy_decision(load_fixture("valid_review_required_policy_decision.json"))
    res = approval_queue.apply_human_decision(item, "approve_for_future_dry_run_only", "jim", "looks fine")
    assert res["updated_item"]["queue_status"] == "APPROVED_FOR_FUTURE_DRY_RUN_ONLY"
    assert res["updated_item"]["safe_for_publish"] is False
    assert res["audit_event"]["actor_id"] == "jim"
    assert res["audit_event"]["secrets_redacted"] is True

def test_forbidden_actions_rejected():
    item = approval_queue.build_queue_item_from_policy_decision(load_fixture("valid_review_required_policy_decision.json"))
    with pytest.raises(ValueError, match="strictly forbidden"):
        approval_queue.apply_human_decision(item, "publish_now", "jim", "looks fine")

def test_audit_event_secret_redaction():
    ev = audit_log.create_audit_event("POLICY_EVALUATED", "SYSTEM", "target1", "eval", "pass", "ok", {"api_key": "123"})
    assert ev["safe_to_log"] is False
    assert ev["redaction_status"] == "REDACTED"
    assert ev["secrets_redacted"] is True
    
def test_audit_event_no_secret():
    ev = audit_log.create_audit_event("POLICY_EVALUATED", "SYSTEM", "target1", "eval", "pass", "ok", {"text": "hello"})
    assert ev["safe_to_log"] is True
    assert ev["redaction_status"] == "CLEAN"

def test_queue_summary_counts():
    items = [
        approval_queue.build_queue_item_from_policy_decision(load_fixture("valid_review_required_policy_decision.json")),
        approval_queue.build_queue_item_from_policy_decision(load_fixture("blocked_policy_decision.json"))
    ]
    summary = approval_queue.summarize_queue(items)
    assert summary["total"] == 2
    assert summary["status_counts"]["REVIEW_REQUIRED"] == 1
    assert summary["status_counts"]["BLOCKED"] == 1
