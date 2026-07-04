import json
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "telegram_supervised_live_pilot_gate.schema.json"

EXACT_LIVE_GO_PHRASE = "I APPROVE TELEGRAM SUPERVISED LIVE PILOT FOR ONE CHANNEL POST ONLY"

class PilotGateBlockedException(Exception):
    pass

def load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_gate_record(record: dict) -> dict:
    schema = load_schema()
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise PilotGateBlockedException(f"Schema validation failed: {e.message}")

    if record.get("live_execution_allowed_now", True):
        raise PilotGateBlockedException("live_execution_allowed_now must be false")
    if record.get("credential_accessed_by_repo", True):
        raise PilotGateBlockedException("credential_accessed_by_repo must be false")
    if record.get("env_read_performed", True):
        raise PilotGateBlockedException("env_read_performed must be false")
    if record.get("network_accessed", True):
        raise PilotGateBlockedException("network_accessed must be false")
    if record.get("telegram_api_called", True):
        raise PilotGateBlockedException("telegram_api_called must be false")
    if record.get("live_post_sent", True):
        raise PilotGateBlockedException("live_post_sent must be false")
    if record.get("scheduling_enabled", True):
        raise PilotGateBlockedException("scheduling_enabled must be false")
    if record.get("replies_or_dms_enabled", True):
        raise PilotGateBlockedException("replies_or_dms_enabled must be false")
    if record.get("scraping_enabled", True):
        raise PilotGateBlockedException("scraping_enabled must be false")
    if record.get("metrics_fetched", True):
        raise PilotGateBlockedException("metrics_fetched must be false")
    if record.get("public_postable", True):
        raise PilotGateBlockedException("public_postable must be false")
    if not record.get("requires_explicit_operator_go", False):
        raise PilotGateBlockedException("requires_explicit_operator_go must be true")

    if record.get("exact_live_go_phrase") != EXACT_LIVE_GO_PHRASE:
        raise PilotGateBlockedException("exact_live_go_phrase does not match required string")

    return {
        "gate_status": "BLOCKED" if record.get("gate_status") == "blocked" else "READY_FOR_MOCK_ONLY",
        "live_posting_allowed": False,
        "reason_for_live_blocked": "live_authenticated_posting_disabled_until_0084_or_explicit_live_scope_authorization"
    }

def get_design_summary() -> dict:
    return {
        "status": "Telegram Live Pilot Design Gate Active",
        "wait_state_status": "WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS",
        "design_gate_active": True,
        "live_posting_allowed": False,
        "mock_testing_allowed": True,
        "checklist_rules_enabled": True,
        "exact_approval_phrase_required": EXACT_LIVE_GO_PHRASE
    }
