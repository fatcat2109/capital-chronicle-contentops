import json
import pytest
from pathlib import Path

from live_contentops.telegram_live_pilot_gate import (
    validate_gate_record,
    PilotGateBlockedException,
    get_design_summary
)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "telegram_live_pilot_gate"

def load_fixture(name: str) -> dict:
    with open(FIXTURE_DIR / f"{name}.json", "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_design_gate_ready_for_explicit_go():
    record = load_fixture("valid_design_gate_ready_for_explicit_go")
    result = validate_gate_record(record)
    assert result["live_posting_allowed"] is False
    assert result["gate_status"] == "READY_FOR_MOCK_ONLY"
    assert result["reason_for_live_blocked"] == "live_authenticated_posting_disabled_until_0084_or_explicit_live_scope_authorization"

def test_invalid_live_execution_allowed_now():
    record = load_fixture("invalid_live_execution_allowed_now")
    with pytest.raises(PilotGateBlockedException) as exc:
        validate_gate_record(record)
    assert "live_execution_allowed_now must be false" in str(exc.value)

def test_invalid_credential_accessed():
    record = load_fixture("invalid_credential_accessed")
    with pytest.raises(PilotGateBlockedException) as exc:
        validate_gate_record(record)
    assert "credential_accessed_by_repo must be false" in str(exc.value)

def test_invalid_telegram_api_called():
    record = load_fixture("invalid_telegram_api_called")
    with pytest.raises(PilotGateBlockedException) as exc:
        validate_gate_record(record)
    assert "telegram_api_called must be false" in str(exc.value)

def test_invalid_missing_approval_phrase():
    record = load_fixture("invalid_missing_approval_phrase")
    with pytest.raises(PilotGateBlockedException) as exc:
        validate_gate_record(record)
    assert "Schema validation failed" in str(exc.value)

def test_invalid_public_postable():
    record = load_fixture("invalid_public_postable")
    with pytest.raises(PilotGateBlockedException) as exc:
        validate_gate_record(record)
    assert "public_postable must be false" in str(exc.value)

def test_design_summary():
    summary = get_design_summary()
    assert summary["live_posting_allowed"] is False
    assert summary["mock_testing_allowed"] is True
    assert summary["exact_approval_phrase_required"] == "I APPROVE TELEGRAM SUPERVISED LIVE PILOT FOR ONE CHANNEL POST ONLY"
