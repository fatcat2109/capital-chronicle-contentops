import os
import json
import pytest
import jsonschema
from live_contentops.telegram_live_precheck import PrecheckState, validate_precheck_state, SCHEMA_PATH

def load_fixture(name):
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "telegram_live_precheck", name)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_telegram_live_precheck_schema_valid():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    data = load_fixture("valid_process_env_present_no_wrapper.json")
    jsonschema.validate(instance=data, schema=schema)
    
    state = PrecheckState(**data)
    valid, result = validate_precheck_state(state)
    assert valid is True
    assert result["status"] == "PRECHECK_PASSED"
    assert result["env_caveat"] == "OPERATOR_OWNED_UNTRACKED_SECRET_FILE_PRESENT"

def test_telegram_live_precheck_blocked_missing_go():
    data = load_fixture("blocked_missing_operator_go.json")
    state = PrecheckState(**data)
    valid, result = validate_precheck_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"

def test_telegram_live_precheck_blocked_missing_env():
    data = load_fixture("blocked_missing_process_env.json")
    state = PrecheckState(**data)
    valid, result = validate_precheck_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"

def test_telegram_live_precheck_blocked_wrapper():
    data = load_fixture("blocked_wrapper_requested.json")
    state = PrecheckState(**data)
    valid, result = validate_precheck_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"

def test_telegram_live_precheck_blocked_retry():
    data = load_fixture("blocked_live_attempt_count_gt_zero.json")
    state = PrecheckState(**data)
    valid, result = validate_precheck_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"
