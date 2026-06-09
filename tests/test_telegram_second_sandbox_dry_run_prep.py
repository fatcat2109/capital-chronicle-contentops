import os
import json
import pytest
import jsonschema
from live_contentops.telegram_second_sandbox_dry_run_prep import SecondSandboxPrepState, validate_prep_state, SCHEMA_PATH

def load_fixture(name):
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "telegram_second_sandbox_dry_run_prep", name)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_prep_schema_valid():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    data = load_fixture("valid_second_sandbox_prep.json")
    jsonschema.validate(instance=data, schema=schema)
    
    state = SecondSandboxPrepState(**data)
    valid, result = validate_prep_state(state)
    assert valid is True
    assert result["status"] == "PREP_PASSED"

def test_prep_blocked_missing_precheck():
    data = load_fixture("blocked_missing_precheck.json")
    state = SecondSandboxPrepState(**data)
    valid, result = validate_prep_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"
    assert "Precheck" in result["error"]

def test_prep_blocked_wrapper():
    data = load_fixture("blocked_wrapper_requested.json")
    state = SecondSandboxPrepState(**data)
    valid, result = validate_prep_state(state)
    assert valid is False
    assert result["status"] == "BLOCKED"
