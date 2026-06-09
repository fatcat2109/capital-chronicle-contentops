import json
from pathlib import Path

BASE_DIR = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")

schema_path = BASE_DIR / "schemas" / "telegram_supervised_live_pilot_gate.schema.json"
fixtures_dir = BASE_DIR / "fixtures" / "telegram_live_pilot_gate"

schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "gate_id": {"type": "string"},
        "platform_id": {"type": "string", "enum": ["telegram"]},
        "gate_status": {"type": "string", "enum": ["design_only", "blocked", "ready_for_explicit_live_go"]},
        "live_execution_allowed_now": {"type": "boolean"},
        "credential_accessed_by_repo": {"type": "boolean"},
        "env_read_performed": {"type": "boolean"},
        "network_accessed": {"type": "boolean"},
        "telegram_api_called": {"type": "boolean"},
        "live_post_sent": {"type": "boolean"},
        "scheduling_enabled": {"type": "boolean"},
        "replies_or_dms_enabled": {"type": "boolean"},
        "scraping_enabled": {"type": "boolean"},
        "metrics_fetched": {"type": "boolean"},
        "public_postable": {"type": "boolean"},
        "requires_explicit_operator_go": {"type": "boolean"},
        "exact_live_go_phrase": {"type": "string"},
        "allowed_live_scope_later": {"type": "string"},
        "forbidden_live_scope": {"type": "string"},
        "required_preflight_evidence": {"type": "array", "items": {"type": "string"}},
        "required_dry_run_evidence": {"type": "array", "items": {"type": "string"}},
        "required_approval_ledger_state": {"type": "string"},
        "required_kill_switch_state": {"type": "string"},
        "required_credential_policy_state": {"type": "string"},
        "required_redaction_state": {"type": "string"},
        "rollback_plan": {"type": "string"},
        "manual_fallback_plan": {"type": "string"},
        "operator_final_checklist": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "gate_id", "platform_id", "gate_status",
        "live_execution_allowed_now", "credential_accessed_by_repo", "env_read_performed",
        "network_accessed", "telegram_api_called", "live_post_sent",
        "scheduling_enabled", "replies_or_dms_enabled", "scraping_enabled",
        "metrics_fetched", "public_postable", "requires_explicit_operator_go",
        "exact_live_go_phrase"
    ],
    "additionalProperties": False
}

valid_fixture = {
    "gate_id": "tg_pilot_gate_001",
    "platform_id": "telegram",
    "gate_status": "ready_for_explicit_live_go",
    "live_execution_allowed_now": False,
    "credential_accessed_by_repo": False,
    "env_read_performed": False,
    "network_accessed": False,
    "telegram_api_called": False,
    "live_post_sent": False,
    "scheduling_enabled": False,
    "replies_or_dms_enabled": False,
    "scraping_enabled": False,
    "metrics_fetched": False,
    "public_postable": False,
    "requires_explicit_operator_go": True,
    "exact_live_go_phrase": "I APPROVE TELEGRAM SUPERVISED LIVE PILOT FOR ONE CHANNEL POST ONLY",
    "allowed_live_scope_later": "Telegram supervised channel post only",
    "forbidden_live_scope": "No autonomous replies, no DMs, no scheduling, no metrics fetching",
    "required_preflight_evidence": ["Verified Telegram credential policy"],
    "required_dry_run_evidence": ["Dry-run payload rendered"],
    "required_approval_ledger_state": "operator_approved_for_live_publish_later",
    "required_kill_switch_state": "permit_only_scoped_telegram_live_pilot",
    "required_credential_policy_state": "no secret printing/logging, redaction tests passing",
    "required_redaction_state": "verified active",
    "rollback_plan": "Delete post manually if sent in error",
    "manual_fallback_plan": "Post via official Telegram app",
    "operator_final_checklist": ["Bot token in external env only", "Minimum required admin permissions"]
}

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_invalid(fixture, key, val):
    data = dict(fixture)
    data[key] = val
    return data

write_json(schema_path, schema)

write_json(fixtures_dir / "valid_design_gate_ready_for_explicit_go.json", valid_fixture)
write_json(fixtures_dir / "invalid_live_execution_allowed_now.json", generate_invalid(valid_fixture, "live_execution_allowed_now", True))
write_json(fixtures_dir / "invalid_credential_accessed.json", generate_invalid(valid_fixture, "credential_accessed_by_repo", True))
write_json(fixtures_dir / "invalid_telegram_api_called.json", generate_invalid(valid_fixture, "telegram_api_called", True))

missing_phrase = dict(valid_fixture)
del missing_phrase["exact_live_go_phrase"]
write_json(fixtures_dir / "invalid_missing_approval_phrase.json", missing_phrase)

write_json(fixtures_dir / "invalid_public_postable.json", generate_invalid(valid_fixture, "public_postable", True))

print("JSON Schema and Fixtures generated successfully.")
