import json
from pathlib import Path
from live_contentops.telegram_one_shot_execution_packet import validate_one_shot_packet

def load_fixture(name):
    path = Path(f"fixtures/telegram_one_shot_execution_packet/{name}.json")
    return json.loads(path.read_text())

def test_valid_dry_run_packet():
    p = load_fixture("valid_dry_run_packet")
    res = validate_one_shot_packet(p)
    assert res["status"] == "DRY_RUN_READY"

def test_invalid_live_execution_allowed_now():
    p = load_fixture("invalid_live_execution_allowed_now")
    res = validate_one_shot_packet(p)
    assert res["status"] == "BLOCKED"
    assert any("Live/network capability flags must be false" in r for r in res["reasons"])

def test_invalid_missing_approval():
    p = load_fixture("invalid_missing_approval")
    res = validate_one_shot_packet(p)
    assert res["status"] == "BLOCKED"
    assert any("approval_state must be" in r for r in res["reasons"])

def test_invalid_missing_kill_switch():
    p = load_fixture("invalid_missing_kill_switch")
    res = validate_one_shot_packet(p)
    assert res["status"] == "BLOCKED"
    assert any("kill_switch_state_required must be" in r for r in res["reasons"])

def test_invalid_missing_policy_allow():
    p = load_fixture("invalid_missing_policy_allow")
    res = validate_one_shot_packet(p)
    assert res["status"] == "BLOCKED"
    assert any("automation_policy_decision must be" in r for r in res["reasons"])

def test_invalid_unredacted_target():
    p = load_fixture("invalid_unredacted_target")
    res = validate_one_shot_packet(p)
    assert res["status"] == "BLOCKED"
    assert any("target_channel_placeholder must be a safe REDACTED placeholder" in r for r in res["reasons"])

def test_invalid_forbidden_language():
    p = load_fixture("valid_dry_run_packet")
    res = validate_one_shot_packet(p, post_text_override="Let's buy some stocks")
    assert res["status"] == "BLOCKED"
    assert any("Forbidden financial/signal language found: buy" in r for r in res["reasons"])
