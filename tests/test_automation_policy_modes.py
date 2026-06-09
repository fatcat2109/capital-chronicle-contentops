import json
from pathlib import Path
from live_contentops.automation_policy_modes import validate_automation_capability

def load_fixture(name):
    path = Path(f"fixtures/automation_policy_modes/{name}.json")
    return json.loads(path.read_text())

def test_valid_local_dry_run_allowed():
    req = load_fixture("valid_local_dry_run_allowed")
    decision = validate_automation_capability(req)
    assert decision.decision == "allowed"

def test_valid_telegram_sandbox_one_shot_allowed():
    req = load_fixture("valid_telegram_sandbox_one_shot_allowed")
    decision = validate_automation_capability(req)
    assert decision.decision == "allowed"

def test_blocked_non_telegram_live():
    req = load_fixture("blocked_non_telegram_live")
    decision = validate_automation_capability(req)
    assert decision.decision == "blocked"
    assert any("not allowed for platform x" in r for r in decision.reasons)

def test_blocked_env_file_read():
    req = load_fixture("blocked_env_file_read")
    decision = validate_automation_capability(req)
    assert decision.decision == "blocked"
    assert any("env_file" in r for r in decision.reasons)

def test_blocked_public_target():
    req = load_fixture("blocked_public_target")
    decision = validate_automation_capability(req)
    assert decision.decision == "blocked"
    assert any("public target" in r for r in decision.reasons)

def test_blocked_live_attempt_count_gt_one():
    req = load_fixture("blocked_live_attempt_count_gt_one")
    decision = validate_automation_capability(req)
    assert decision.decision == "blocked"
    assert any("count > 1" in r for r in decision.reasons)

def test_blocked_scheduler_requested():
    req = load_fixture("blocked_scheduler_requested")
    decision = validate_automation_capability(req)
    assert decision.decision == "blocked"
    assert any("scheduler capability" in r for r in decision.reasons)

def test_design_only_approved_batch_live():
    req = load_fixture("design_only_approved_batch_live")
    decision = validate_automation_capability(req)
    assert decision.decision == "design_only_not_currently_allowed"
    assert "QUEUE_IMPLEMENTATION" in decision.required_next_evidence
