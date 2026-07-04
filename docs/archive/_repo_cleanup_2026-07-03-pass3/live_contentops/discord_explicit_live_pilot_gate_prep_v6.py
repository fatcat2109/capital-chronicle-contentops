"""V6 Discord explicit live pilot gate prep, local-only and no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_EXPLICIT_LIVE_PILOT_GATE_PREP_HEAVY_BATCH_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_LIVE_CAPABLE_SUPERVISED_PILOT_ADAPTER_HEAVY_BATCH_NO_LIVE_SEND_V0"
PREP_MODE = "operator_declared_discord_explicit_live_pilot_gate_prep_only_no_send"
PREP_KIND = "explicit_live_pilot_execution_contract_shell_no_send"
PAYLOAD_PREVIEW_KIND = "payload_preview_hash_binding_shell_only"
DESTINATION_BINDING_KIND = "destination_binding_declaration_shell_only"
CREDENTIAL_KEY_NAME = "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
APPROVAL_PHRASE = "MARK_DISCORD_EXPLICIT_LIVE_PILOT_GATE_PREP_READY_NO_SEND"
APPROVAL_SCOPE = "discord_explicit_live_pilot_gate_prep_only_no_send"

REQUIRED_FUTURE_BLOCKERS = {
    "future_explicit_live_execution_task_required",
    "exact_operator_confirmation_required_later",
    "credential_presence_membership_only_required_later",
    "destination_binding_required_later",
    "payload_hash_revalidation_required_later",
    "kill_switch_required_later",
    "redacted_audit_required_later",
    "manual_fallback_required_later",
    "live_dispatch_disabled_in_this_packet",
}

DECLARATION_FIELDS = {
    "schema_version", "discord_explicit_live_pilot_gate_prep_declaration_id", "operator_id",
    "created_at_manual", "discord_live_capable_supervised_pilot_adapter_id",
    "discord_heavy_local_pre_live_batch_id", "platform", "prep_mode", "prep_kind",
    "payload_preview_kind", "payload_preview_contains_real_content", "payload_preview_hash",
    "destination_binding_kind", "destination_binding_contains_channel_id",
    "destination_binding_contains_account_id", "destination_binding_contains_webhook_url",
    "credential_key_name", "credential_presence_membership_only_planned",
    "credential_value_read_now", "env_read_now", "dot_env_read_now", "network_call_now",
    "browser_session_now", "executable_request_created_now", "live_send_now",
    "discord_api_call_now", "webhook_send_test_now", "endpoint_url_included",
    "webhook_url_included", "webhook_token_included", "channel_identity_included",
    "account_identity_included", "http_method_included", "http_path_included",
    "http_headers_included", "http_body_included", "curl_command_included",
    "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included",
    "metrics_included", "max_request_count", "timeout_seconds", "max_retries",
    "hidden_retry_allowed", "idempotency_required", "kill_switch_required",
    "redacted_audit_required", "manual_fallback_required",
    "exact_operator_go_phrase_required_later", "future_live_execution_task_required",
    "operator_prep_decision", "declaration_decision", "approval_phrase", "approval_scope", "notes",
}

FALSE_DECL_FLAGS = (
    "payload_preview_contains_real_content", "destination_binding_contains_channel_id",
    "destination_binding_contains_account_id", "destination_binding_contains_webhook_url",
    "credential_value_read_now", "env_read_now", "dot_env_read_now", "network_call_now",
    "browser_session_now", "executable_request_created_now", "live_send_now",
    "discord_api_call_now", "webhook_send_test_now", "endpoint_url_included",
    "webhook_url_included", "webhook_token_included", "channel_identity_included",
    "account_identity_included", "http_method_included", "http_path_included",
    "http_headers_included", "http_body_included", "curl_command_included",
    "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included",
    "metrics_included", "hidden_retry_allowed",
)
TRUE_DECL_FLAGS = (
    "credential_presence_membership_only_planned", "idempotency_required", "kill_switch_required",
    "redacted_audit_required", "manual_fallback_required", "exact_operator_go_phrase_required_later",
    "future_live_execution_task_required",
)
FALSE_UPSTREAM_FLAGS = (
    "live_execution_enabled_now", "live_dispatch_approval_granted", "executable_request_artifact_created",
    "executable_request_artifact_creation_allowed", "webhook_value_read_allowed", "discord_api_call_allowed",
    "webhook_send_test_allowed", "browser_session_allowed", "env_read_allowed", "dot_env_read_allowed",
    "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed",
)
TRUE_UPSTREAM_FLAGS = ("adapter_available", "adapter_declared_ready", "requires_future_explicit_live_execution_task", "requires_exact_operator_confirmation_later")

SECRET_OR_LIVE_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)
FORBIDDEN_TEXT = ("send now", "live send", "dispatch allowed", "publication ready", "ready for publication", "public url", "public metrics", "financial advice", "signal service", "fake readiness", "curl-command", "fetch-call", "http-request", "endpoint url", "webhook url", "channel id", "account id", "http method", "http path", "headers", "body")

@dataclass(frozen=True)
class DiscordExplicitLivePilotGatePrepPacket:
    schema_version: str
    task_label: str
    discord_explicit_live_pilot_gate_prep_id: str
    declaration_id: str
    discord_live_capable_supervised_pilot_adapter_id: str
    discord_heavy_local_pre_live_batch_id: str
    platform: str
    prep_kind: str
    payload_preview_kind: str
    payload_preview_hash: str
    destination_binding_kind: str
    credential_key_name: str
    credential_presence_membership_only_planned: bool
    future_live_execution_task_required: bool
    exact_operator_go_phrase_required_later: bool
    idempotency_required: bool
    kill_switch_required: bool
    redacted_audit_required: bool
    manual_fallback_required: bool
    max_request_count: int
    timeout_seconds: int
    max_retries: int
    hidden_retry_allowed: bool
    live_send_now: bool
    eligible_for_future_operator_go_live_task: bool
    eligible_for_live_send_now: bool
    env_read_now: bool
    dot_env_read_now: bool
    credential_value_read_now: bool
    network_call_now: bool
    browser_session_now: bool
    executable_request_created_now: bool
    discord_api_call_now: bool
    webhook_send_test_now: bool
    endpoint_url_included: bool
    webhook_url_included: bool
    webhook_token_included: bool
    channel_identity_included: bool
    account_identity_included: bool
    http_method_included: bool
    http_path_included: bool
    http_headers_included: bool
    http_body_included: bool
    curl_command_included: bool
    fetch_or_http_client_code_included: bool
    browser_instruction_included: bool
    public_url_included: bool
    metrics_included: bool
    publication_ready: bool
    dispatch_allowed: bool
    review_only: bool
    human_review_required: bool
    runtime_truth: bool
    exact_live_execution_contract_shell: dict[str, Any]
    payload_preview_hash_binding_shell: dict[str, Any]
    destination_binding_declaration_shell: dict[str, Any]
    credential_presence_membership_only_plan: dict[str, Any]
    kill_switch_and_idempotency_plan: dict[str, Any]
    redacted_audit_envelope: dict[str, Any]
    final_operator_go_packet_template: dict[str, Any]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    redacted_audit_summary: str = ""
    packet_sha256: str = ""


def _sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None)
    return hashlib.sha256(json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out: list[tuple[str, Any]] = []
        for key, val in obj.items(): out.extend(_walk(val, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, val in enumerate(obj): out.extend(_walk(val, f"{path}[{idx}]"))
        return out
    return [(path, obj)]


def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, val in _walk(obj):
        if isinstance(val, str):
            low = val.lower()
            if val != CREDENTIAL_KEY_NAME and SECRET_OR_LIVE_RE.search(val):
                raise ValueError(f"{label}_forbidden_value:{path}")
            if any(term in low for term in FORBIDDEN_TEXT):
                raise ValueError(f"{label}_forbidden_text:{path}")


def _add(blockers: list[str], ok: bool, msg: str) -> None:
    if not ok: blockers.append(msg)


def _validate_adapter(adapter: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, adapter.get("schema_version") == SCHEMA_VERSION, "adapter_schema_version_invalid")
    _add(b, adapter.get("task_label") == UPSTREAM_TASK_LABEL, "adapter_task_label_invalid")
    _add(b, adapter.get("platform") == "discord", "adapter_platform_invalid")
    for key in TRUE_UPSTREAM_FLAGS: _add(b, adapter.get(key) is True, f"adapter_{key}_not_true")
    for key in FALSE_UPSTREAM_FLAGS: _add(b, adapter.get(key) is False, f"adapter_{key}_not_false")
    _add(b, set(adapter.get("future_live_execution_blockers", [])) >= REQUIRED_FUTURE_BLOCKERS, "adapter_missing_future_live_execution_blockers")
    _add(b, adapter.get("blockers", []) == [], "adapter_blockers_not_empty")
    _add(b, bool(adapter.get("discord_live_capable_supervised_pilot_adapter_id")), "adapter_id_missing")
    _add(b, bool(adapter.get("discord_heavy_local_pre_live_batch_id")), "heavy_batch_id_missing")
    return b


def _validate_decl(adapter: dict[str, Any], decl: dict[str, Any]) -> list[str]:
    b: list[str] = []
    extra = sorted(set(decl) - DECLARATION_FIELDS)
    _add(b, not extra, "declaration_extra_fields")
    for key in DECLARATION_FIELDS: _add(b, key in decl, f"missing_declaration_{key}")
    checks = {
        "schema_version": SCHEMA_VERSION, "platform": "discord", "prep_mode": PREP_MODE,
        "prep_kind": PREP_KIND, "payload_preview_kind": PAYLOAD_PREVIEW_KIND,
        "destination_binding_kind": DESTINATION_BINDING_KIND, "credential_key_name": CREDENTIAL_KEY_NAME,
        "operator_prep_decision": "approve_explicit_live_pilot_gate_prep_for_future_operator_go_only",
        "declaration_decision": "mark_discord_explicit_live_pilot_gate_prep_ready",
        "approval_phrase": APPROVAL_PHRASE, "approval_scope": APPROVAL_SCOPE,
        "discord_live_capable_supervised_pilot_adapter_id": adapter.get("discord_live_capable_supervised_pilot_adapter_id"),
        "discord_heavy_local_pre_live_batch_id": adapter.get("discord_heavy_local_pre_live_batch_id"),
    }
    for key, expected in checks.items(): _add(b, decl.get(key) == expected, f"declaration_{key}_invalid")
    for key in FALSE_DECL_FLAGS: _add(b, decl.get(key) is False, f"declaration_{key}_not_false")
    for key in TRUE_DECL_FLAGS: _add(b, decl.get(key) is True, f"declaration_{key}_not_true")
    _add(b, bool(decl.get("discord_explicit_live_pilot_gate_prep_declaration_id")), "missing_declaration_id")
    _add(b, bool(decl.get("operator_id")), "missing_operator_id")
    _add(b, bool(decl.get("created_at_manual")), "missing_created_at_manual")
    _add(b, isinstance(decl.get("notes"), str), "declaration_notes_not_string")
    ph = decl.get("payload_preview_hash")
    _add(b, isinstance(ph, str) and bool(ph.strip()), "payload_preview_hash_missing")
    if isinstance(ph, str): _add(b, not SECRET_OR_LIVE_RE.search(ph), "payload_preview_hash_secret_derived")
    _add(b, decl.get("max_request_count") == 1, "max_request_count_not_one")
    _add(b, isinstance(decl.get("timeout_seconds"), int) and 5 <= decl.get("timeout_seconds") <= 30, "timeout_seconds_out_of_range")
    _add(b, decl.get("max_retries") == 0, "max_retries_not_zero")
    return b


def load_json_packet(path: str | Path, error_label: str) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError(error_label) from exc
    if not isinstance(data, dict): raise ValueError(error_label)
    return data


def make_discord_explicit_live_pilot_gate_prep_packet(adapter: dict[str, Any], declaration: dict[str, Any]) -> DiscordExplicitLivePilotGatePrepPacket:
    _assert_safe(adapter, "adapter"); _assert_safe(declaration, "declaration")
    blockers = _validate_adapter(adapter) + _validate_decl(adapter, declaration)
    eligible_future = not blockers
    declaration_id = str(declaration.get("discord_explicit_live_pilot_gate_prep_declaration_id", ""))
    adapter_id = str(adapter.get("discord_live_capable_supervised_pilot_adapter_id", ""))
    heavy_id = str(adapter.get("discord_heavy_local_pre_live_batch_id", ""))
    prep_id = "discord_explicit_live_pilot_gate_prep_" + hashlib.sha256((adapter_id + declaration_id).encode("utf-8")).hexdigest()[:16]
    contract = {"kind": PREP_KIND, "no_send": True, "eligible_for_live_send_now": False, "future_operator_go_task_required": True, "credential_values_allowed": False, "network_calls_allowed": False}
    payload_shell = {"kind": PAYLOAD_PREVIEW_KIND, "contains_real_content": False, "hash_binding_only": True, "payload_preview_hash": str(declaration.get("payload_preview_hash", ""))}
    destination_shell = {"kind": DESTINATION_BINDING_KIND, "contains_channel_id": False, "contains_account_id": False, "contains_webhook_url": False, "future_destination_binding_required": True}
    credential_plan = {"credential_key_name": CREDENTIAL_KEY_NAME, "membership_only_planned": True, "credential_value_read_now": False, "env_read_now": False}
    kill_plan = {"idempotency_required": True, "kill_switch_required": True, "max_request_count": 1, "max_retries": 0, "hidden_retry_allowed": False}
    audit = {"redacted_only": True, "secrets_allowed": False, "secret_hashes_allowed": False, "public_urls_allowed": False, "metrics_allowed": False}
    go_template = {"operator_go_phrase_required_later": True, "future_task_required": True, "template_only_no_send": True, "approval_phrase_for_this_prep": APPROVAL_PHRASE}
    packet = DiscordExplicitLivePilotGatePrepPacket(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL,
        discord_explicit_live_pilot_gate_prep_id=prep_id, declaration_id=declaration_id,
        discord_live_capable_supervised_pilot_adapter_id=adapter_id,
        discord_heavy_local_pre_live_batch_id=heavy_id, platform="discord", prep_kind=PREP_KIND,
        payload_preview_kind=PAYLOAD_PREVIEW_KIND,
        payload_preview_hash=str(declaration.get("payload_preview_hash", "")),
        destination_binding_kind=DESTINATION_BINDING_KIND, credential_key_name=CREDENTIAL_KEY_NAME,
        credential_presence_membership_only_planned=True, future_live_execution_task_required=True,
        exact_operator_go_phrase_required_later=True, idempotency_required=True, kill_switch_required=True,
        redacted_audit_required=True, manual_fallback_required=True, max_request_count=1,
        timeout_seconds=int(declaration.get("timeout_seconds", 0) or 0), max_retries=0,
        hidden_retry_allowed=False, live_send_now=False, eligible_for_future_operator_go_live_task=eligible_future,
        eligible_for_live_send_now=False, env_read_now=False, dot_env_read_now=False,
        credential_value_read_now=False, network_call_now=False, browser_session_now=False,
        executable_request_created_now=False, discord_api_call_now=False, webhook_send_test_now=False,
        endpoint_url_included=False, webhook_url_included=False, webhook_token_included=False,
        channel_identity_included=False, account_identity_included=False, http_method_included=False,
        http_path_included=False, http_headers_included=False, http_body_included=False,
        curl_command_included=False, fetch_or_http_client_code_included=False, browser_instruction_included=False,
        public_url_included=False, metrics_included=False, publication_ready=False, dispatch_allowed=False,
        review_only=True, human_review_required=True, runtime_truth=False,
        exact_live_execution_contract_shell=contract, payload_preview_hash_binding_shell=payload_shell,
        destination_binding_declaration_shell=destination_shell,
        credential_presence_membership_only_plan=credential_plan, kill_switch_and_idempotency_plan=kill_plan,
        redacted_audit_envelope=audit, final_operator_go_packet_template=go_template, blockers=blockers,
        warnings=["local_only_no_send", "future_operator_go_task_required"],
        redacted_audit_summary="Local explicit live pilot prep emitted without live send, env reads, credential reads, network, browser, executable request artifacts, public URLs, or metrics.",
    )
    data = asdict(packet)
    return DiscordExplicitLivePilotGatePrepPacket(**{**data, "packet_sha256": _sha(data)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Discord explicit live pilot gate prep CLI")
    parser.add_argument("--input-adapter-packet", required=True)
    parser.add_argument("--operator-prep-declaration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        packet = make_discord_explicit_live_pilot_gate_prep_packet(load_json_packet(args.input_adapter_packet, "malformed_adapter_packet_json"), load_json_packet(args.operator_prep_declaration, "malformed_prep_declaration_json"))
    except ValueError as exc:
        packet = DiscordExplicitLivePilotGatePrepPacket(SCHEMA_VERSION, TASK_LABEL, "discord_explicit_live_pilot_gate_prep_blocked", "", "", "", "discord", PREP_KIND, PAYLOAD_PREVIEW_KIND, "", DESTINATION_BINDING_KIND, CREDENTIAL_KEY_NAME, True, True, True, True, True, True, True, 1, 0, 0, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, False, {}, {}, {}, {}, {}, {}, {}, [str(exc)], ["prep_packet_blocked_pending_operator_repair"])
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_operator_go_live_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
