"""Discord live pilot authorization gate and official docs lock.

Final pre-live local gate. It locks official Discord Execute Webhook facts,
selects one non-dispatchable announcement candidate, and writes a redacted future
request plan without loading webhook URLs, env values, or sending requests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_LIVE_PILOT_AUTHORIZATION_GATE_AND_OFFICIAL_DOCS_LOCK_V0"
DOCS_LOCK_SCHEMA_VERSION = "discord_execute_webhook_official_docs_lock.v1"
GATE_SCHEMA_VERSION = "discord_live_pilot_authorization_gate.v1"
REQUEST_PLAN_SCHEMA_VERSION = "discord_live_pilot_request_plan_redacted.v1"
DOCS_URL = "https://discord.com/developers/docs/resources/webhook#execute-webhook"
DOCS_REDIRECT_URL = "https://docs.discord.com/developers/resources/webhook"
DOCS_CHECKED_AT = "2026-06-26T19:35:00Z"
ENDPOINT_FAMILY = "discord_execute_webhook"
METHOD = "POST"
PATH_TEMPLATE = "/api/webhooks/{webhook.id}/{webhook.token}"
OPERATOR_PHRASE = "AUTHORIZE_DISCORD_WEBHOOK_TEST_SEND_NOW"
KILL_SWITCH_ENV_KEY = "CONTENTOPS_LIVE_DISPATCH_KILL_SWITCH"
KILL_SWITCH_REQUIRED_VALUE = "ALLOW_DISCORD_TEST_SEND"
ANNOUNCEMENT_CREDENTIAL_HANDLE_ID = "discord_announcements_webhook_01"
ANNOUNCEMENT_DESTINATION_BINDING_ID = "discord_announcements_capital_chronicle_01"
ANNOUNCEMENT_ENV_KEY_NAME = "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
READY_STATUS = "ready_for_explicit_live_authorization_task"
BLOCKED_ANNOUNCEMENT_CANDIDATE_MISSING = "BLOCKED_ANNOUNCEMENT_CANDIDATE_MISSING"
BLOCKED_CANDIDATE_NOT_READY = "blocked_candidate_not_ready"
BLOCKED_CREDENTIAL_BINDING_MISMATCH = "blocked_credential_binding_mismatch"
BLOCKED_FORBIDDEN_MATERIAL = "blocked_secret_or_endpoint_material_present"

FORBIDDEN_VALUE_SUBSTRINGS = (
    "discord.com/api/webhooks",
    "discordapp.com/api/webhooks",
    "token_value",
    "token_length",
    "token_prefix",
    "token_suffix",
    "token_digest",
    "token_hash",
    "cookie",
    "localstorage",
    "sessionstorage",
)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _string_values(obj: Any) -> list[str]:
    if isinstance(obj, dict):
        values: list[str] = []
        for value in obj.values():
            values.extend(_string_values(value))
        return values
    if isinstance(obj, (list, tuple)):
        values: list[str] = []
        for value in obj:
            values.extend(_string_values(value))
        return values
    if isinstance(obj, str):
        return [obj]
    return []


def contains_forbidden_material(obj: Any) -> bool:
    text = "\n".join(_string_values(obj)).lower()
    return any(item in text for item in FORBIDDEN_VALUE_SUBSTRINGS)


def build_official_docs_lock() -> dict:
    return {
        "docs_lock_schema_version": DOCS_LOCK_SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "docs_source_name": "Discord Developer Documentation - Webhook Resource / Execute Webhook",
        "docs_url": DOCS_URL,
        "docs_redirect_url": DOCS_REDIRECT_URL,
        "docs_checked_at": DOCS_CHECKED_AT,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "path_template": PATH_TEMPLATE,
        "host_allowlist": ["discord.com"],
        "secondary_legacy_host": "discordapp.com",
        "secondary_legacy_review_required": True,
        "wait_default": False,
        "allowed_payload_top_level_fields": [
            "content",
            "embeds",
            "components",
            "file",
            "poll",
            "allowed_mentions",
            "attachments",
            "flags",
        ],
        "required_payload_minimum": "one_of_content_embeds_components_file_poll",
        "first_pilot_allowed_payload_mode": "embeds_only_or_content_plus_embed",
        "allowed_mentions_required": {"parse": []},
        "attachments_allowed_first_pilot": False,
        "components_allowed_first_pilot": False,
        "polls_allowed_first_pilot": False,
        "thread_params_allowed_first_pilot": False,
        "raw_webhook_url_stored": False,
        "webhook_id_stored": False,
        "webhook_token_stored": False,
        "bot_required": False,
        "authentication_header_required": False,
        "official_docs_quote_excerpt_short": "Execute Webhook supports wait, content, embeds, components, file, poll.",
        "docs_confidence": "verified_from_official_docs",
    }


def select_announcement_candidate(candidate_packet: dict) -> dict:
    for candidate in candidate_packet.get("dispatch_candidates", []):
        if candidate.get("payload_type") == "announcement" and candidate.get("target_name") == "announcements":
            return candidate
    raise ValueError(BLOCKED_ANNOUNCEMENT_CANDIDATE_MISSING)


def build_credential_binding_plan(candidate: dict) -> dict:
    mismatch = []
    if candidate.get("credential_handle_id") != ANNOUNCEMENT_CREDENTIAL_HANDLE_ID:
        mismatch.append("credential_handle_id_mismatch")
    if candidate.get("destination_binding_id") != ANNOUNCEMENT_DESTINATION_BINDING_ID:
        mismatch.append("destination_binding_id_mismatch")
    return {
        "credential_binding_schema_version": "discord_live_pilot_credential_binding_plan.v1",
        "credential_handle_id": ANNOUNCEMENT_CREDENTIAL_HANDLE_ID,
        "destination_binding_id": ANNOUNCEMENT_DESTINATION_BINDING_ID,
        "env_key_name": ANNOUNCEMENT_ENV_KEY_NAME,
        "env_value_loaded": False,
        "webhook_url_loaded": False,
        "webhook_url_parsed": False,
        "webhook_url_hashed": False,
        "webhook_url_length_counted": False,
        "webhook_id_loaded": False,
        "webhook_token_loaded": False,
        "credential_key_presence_checked": False,
        "credential_key_presence_status": "not_checked_in_this_task",
        "binding_mismatches": mismatch,
    }


def candidate_blockers(candidate: dict, credential_binding: dict) -> list[str]:
    blockers: list[str] = []
    if candidate.get("candidate_status") != "future_live_pilot_candidate_ready":
        blockers.append(BLOCKED_CANDIDATE_NOT_READY)
    if candidate.get("current_task_dispatchable") is not False:
        blockers.append("blocked_source_candidate_current_task_dispatchable_not_false")
    if candidate.get("valid_for_dispatch") is not False:
        blockers.append("blocked_source_candidate_valid_for_dispatch_not_false")
    if candidate.get("future_live_task_required") is not True:
        blockers.append("blocked_future_live_task_not_required")
    if candidate.get("explicit_operator_live_approval_required") is not True:
        blockers.append("blocked_explicit_operator_approval_not_required")
    if candidate.get("live_write_allowed_now") is not False:
        blockers.append("blocked_source_live_write_allowed_now_not_false")
    if candidate.get("webhook_url_loaded") is not False:
        blockers.append("blocked_source_webhook_url_loaded_not_false")
    if candidate.get("network_call_attempted") is not False:
        blockers.append("blocked_source_network_call_attempted_not_false")
    if candidate.get("endpoint_family") is not None:
        blockers.append("blocked_source_endpoint_family_not_null")
    if credential_binding.get("binding_mismatches"):
        blockers.append(BLOCKED_CREDENTIAL_BINDING_MISMATCH)
    if contains_forbidden_material(candidate):
        blockers.append(BLOCKED_FORBIDDEN_MATERIAL)
    return blockers


def build_request_plan(candidate: dict, docs_lock: dict, credential_binding: dict) -> dict:
    return {
        "request_plan_schema_version": REQUEST_PLAN_SCHEMA_VERSION,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "host_allowlist": docs_lock["host_allowlist"],
        "path_template": PATH_TEMPLATE,
        "query_params": {"wait": False},
        "request_body_shape": {
            "payload_mode": "embeds_only_or_content_plus_embed",
            "allowed_mentions_required": {"parse": []},
            "attachments_allowed": False,
            "components_allowed": False,
            "polls_allowed": False,
            "thread_params_allowed": False,
            "source_payload_id": candidate.get("payload_id"),
            "source_payload_hash": candidate.get("payload_hash"),
        },
        "allowed_mentions": {"parse": []},
        "request_budget_max": 1,
        "retry_budget_max": 0,
        "timeout_seconds": 10,
        "credential_source": credential_binding["env_key_name"],
        "credential_value_loaded": False,
        "webhook_url_loaded": False,
        "webhook_id_loaded": False,
        "webhook_token_loaded": False,
        "headers_output": False,
        "response_body_output": False,
        "expected_response_class": "not_attempted_in_this_task",
        "current_task_network_call_attempted": False,
    }


def build_live_pilot_authorization_gate_packet(candidate_packet: dict, docs_lock: dict | None = None, discord_env_packet: dict | None = None) -> dict:
    del discord_env_packet
    docs_lock = docs_lock or build_official_docs_lock()
    candidate = select_announcement_candidate(candidate_packet)
    credential_binding = build_credential_binding_plan(candidate)
    blockers = candidate_blockers(candidate, credential_binding)
    if contains_forbidden_material(docs_lock):
        blockers.append(BLOCKED_FORBIDDEN_MATERIAL)
    future_status = READY_STATUS if not blockers else "blocked_pre_live_gate_failed"
    request_plan = build_request_plan(candidate, docs_lock, credential_binding)
    packet = {
        "gate_schema_version": GATE_SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "docs_lock": docs_lock,
        "selected_dispatch_candidate_id": candidate.get("dispatch_candidate_id"),
        "selected_payload_id": candidate.get("payload_id"),
        "selected_payload_hash": candidate.get("payload_hash"),
        "selected_payload_type": candidate.get("payload_type"),
        "selected_target_name": candidate.get("target_name"),
        "selected_destination_binding_id": candidate.get("destination_binding_id"),
        "selected_credential_handle_id": candidate.get("credential_handle_id"),
        "credential_binding_plan": credential_binding,
        "env_key_name": credential_binding["env_key_name"],
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "host_allowlist": docs_lock["host_allowlist"],
        "path_template": PATH_TEMPLATE,
        "request_budget_max": 1,
        "retry_budget_max": 0,
        "timeout_seconds": 10,
        "wait_query_param": False,
        "allowed_mentions_required": {"parse": []},
        "payload_mode": "embeds_only_or_content_plus_embed",
        "webhook_url_hydration_allowed_now": False,
        "network_dispatch_allowed_now": False,
        "current_task_dispatchable": False,
        "live_write_allowed_now": False,
        "explicit_future_live_authorization_required": True,
        "operator_authorization_phrase_required": OPERATOR_PHRASE,
        "kill_switch_required": True,
        "kill_switch_env_key": KILL_SWITCH_ENV_KEY,
        "kill_switch_required_value": KILL_SWITCH_REQUIRED_VALUE,
        "kill_switch_read_in_this_task": False,
        "idempotency_key": candidate.get("idempotency_key"),
        "duplicate_suppression_key": candidate.get("duplicate_suppression_key"),
        "stop_conditions": [
            "candidate_id_mismatch",
            "payload_hash_mismatch",
            "payload_id_mismatch",
            "target_name_mismatch",
            "destination_binding_id_mismatch",
            "credential_handle_id_mismatch",
            "rendered_payload_preview_mismatch",
            "operator_authorization_phrase_missing",
            "kill_switch_not_allowed",
            "request_budget_exceeded",
            "retry_requested_without_approval",
            "hidden_destination_account_channel_mutation",
            "webhook_url_hydration_not_explicitly_authorized",
        ],
        "blockers": blockers,
        "future_live_task_ready_status": future_status,
        "request_plan": request_plan,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "endpoint_url_loaded": False,
        "discord_bot_required": False,
    }
    if contains_forbidden_material(packet):
        packet["blockers"] = list(dict.fromkeys(packet["blockers"] + [BLOCKED_FORBIDDEN_MATERIAL]))
        packet["future_live_task_ready_status"] = "blocked_pre_live_gate_failed"
    return packet


def render_operator_brief(packet: dict) -> str:
    lines = [
        "# Discord Live Pilot Operator Brief",
        "",
        f"- Task label: `{TASK_LABEL}`",
        f"- Selected dispatch candidate ID: `{packet['selected_dispatch_candidate_id']}`",
        f"- Payload hash: `{packet['selected_payload_hash']}`",
        f"- Payload type: `{packet['selected_payload_type']}`",
        f"- Target name: `{packet['selected_target_name']}`",
        f"- Destination binding ID: `{packet['selected_destination_binding_id']}`",
        f"- Credential handle ID: `{packet['selected_credential_handle_id']}`",
        f"- Env key name only: `{packet['env_key_name']}`",
        f"- Endpoint family: `{packet['endpoint_family']}`",
        f"- Method: `{packet['method']}`",
        f"- Host allowlist: `{', '.join(packet['host_allowlist'])}`",
        f"- Path template only: `{packet['path_template']}`",
        f"- Request budget: `{packet['request_budget_max']}`",
        f"- Retries: `{packet['retry_budget_max']}`",
        f"- Timeout seconds: `{packet['timeout_seconds']}`",
        "- wait=false",
        "- current_task_dispatchable=false",
        "- live_write_allowed_now=false",
        "- webhook_url_hydration_allowed_now=false",
        "- network_dispatch_allowed_now=false",
        f"- Exact future authorization phrase: `{OPERATOR_PHRASE}`",
        f"- Kill switch env key: `{KILL_SWITCH_ENV_KEY}`",
        f"- Kill switch required value: `{KILL_SWITCH_REQUIRED_VALUE}`",
        "- no live send happened",
        "",
        "## Meaning",
        "",
        "This packet prepares a future live authorization task only. It does not authorize dispatch now and does not load any webhook URL.",
    ]
    brief = "\n".join(lines) + "\n"
    if contains_forbidden_material(brief):
        raise ValueError("operator brief contains forbidden material")
    return brief


def write_outputs(candidate_packet_path: str | Path, discord_env_packet_path: str | Path | None, docs_lock_output: str | Path, output_path: str | Path, operator_brief_output: str | Path) -> dict:
    candidate_packet = json.loads(Path(candidate_packet_path).read_text(encoding="utf-8"))
    discord_env_packet = None
    if discord_env_packet_path:
        discord_env_packet = json.loads(Path(discord_env_packet_path).read_text(encoding="utf-8"))
    docs_lock = build_official_docs_lock()
    packet = build_live_pilot_authorization_gate_packet(candidate_packet, docs_lock, discord_env_packet)
    docs_out = Path(docs_lock_output)
    docs_out.parent.mkdir(parents=True, exist_ok=True)
    docs_out.write_text(json.dumps(docs_lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    brief = render_operator_brief(packet)
    brief_out = Path(operator_brief_output)
    brief_out.parent.mkdir(parents=True, exist_ok=True)
    brief_out.write_text(brief, encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Discord live pilot authorization gate packet without dispatch")
    parser.add_argument("--candidate-packet", required=True)
    parser.add_argument("--discord-env-packet", required=False)
    parser.add_argument("--docs-lock-output", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--operator-brief-output", required=True)
    args = parser.parse_args(argv)
    packet = write_outputs(args.candidate_packet, args.discord_env_packet, args.docs_lock_output, args.output, args.operator_brief_output)
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result": "PASS",
        "selected_dispatch_candidate_id": packet["selected_dispatch_candidate_id"],
        "future_live_task_ready_status": packet["future_live_task_ready_status"],
        "request_budget_max": packet["request_budget_max"],
        "retry_budget_max": packet["retry_budget_max"],
        "timeout_seconds": packet["timeout_seconds"],
        "current_task_dispatchable": False,
        "live_write_allowed_now": False,
        "webhook_url_hydration_allowed_now": False,
        "network_dispatch_allowed_now": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "discord_bot_required": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
