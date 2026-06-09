import json
from pathlib import Path
from live_contentops.telegram_one_shot_go_gate import validate_go_gate

def load_fixture(name):
    path = Path(f"fixtures/telegram_one_shot_go_gate/{name}.json")
    return json.loads(path.read_text())

def test_valid_go_gate():
    g = load_fixture("valid_go_gate_dry_run_allowed")
    res = validate_go_gate(g)
    assert res["status"] == "GO_GATE_DRY_RUN_ALLOWED"

def test_invalid_missing_exact_go_phrase():
    g = load_fixture("invalid_missing_exact_go_phrase")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("Exact GO phrase is missing" in r for r in res["reasons"])

def test_invalid_missing_packet_ready():
    g = load_fixture("invalid_missing_packet_ready")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("source_packet_dry_run_ready must be true" in r for r in res["reasons"])

def test_invalid_missing_approval_ledger():
    g = load_fixture("invalid_missing_approval_ledger")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("approval_ledger_state must be" in r for r in res["reasons"])

def test_invalid_kill_switch_not_permitting():
    g = load_fixture("invalid_kill_switch_not_permitting")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("kill_switch_state must be" in r for r in res["reasons"])

def test_invalid_unredacted_target():
    g = load_fixture("invalid_unredacted_target")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("target must be redacted" in r for r in res["reasons"])

def test_invalid_attempt_count_gt_one():
    g = load_fixture("invalid_attempt_count_gt_one")
    res = validate_go_gate(g)
    assert res["status"] == "BLOCKED"
    assert any("live_attempt_count must be 0" in r for r in res["reasons"])
