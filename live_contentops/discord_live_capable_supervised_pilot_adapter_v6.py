"""V6 Discord live-capable supervised pilot adapter, disabled by default."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_LIVE_CAPABLE_SUPERVISED_PILOT_ADAPTER_HEAVY_BATCH_NO_LIVE_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_HEAVY_LOCAL_PRE_LIVE_BATCH_FROM_EXACT_OPERATOR_APPROVAL_V0"
SCHEMA_VERSION = "6.0.0"
DECLARATION_MODE = "operator_declared_discord_live_capable_adapter_heavy_batch_only_not_live"
ADAPTER_KIND = "discord_supervised_pilot_adapter_contract_disabled_by_default"

SECRET_VALUE_RE = re.compile(r"(https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{20,})", re.IGNORECASE)
FORBIDDEN_KEY_PARTS = ("webhook_url", "webhook_secret", "webhook_token", "token_value", "secret_value", "credential_value", "authorization", "bearer", "cookie", "password", "private_key", "http_body", "http_headers", "curl_command", "fetch_code", "http_client_code", "public_url", "public_metrics")
FORBIDDEN_LIVE_PHRASES = ("send now", "live send", "perform live dispatch", "dispatch allowed", "publication ready", "ready for publication", "public url", "public metrics", "curl ", "fetch(", "http client call", "http request artifact", "executable request")
EXPECTED_FALSE_FLAGS = ("live_dispatch_approval_granted", "approval_for_live_dispatch", "dispatch_allowed", "publication_approval_granted", "approval_for_publication", "publication_ready", "executable_request_artifact_created", "executable_request_artifact_creation_allowed", "webhook_value_read_allowed", "discord_api_call_allowed", "webhook_send_test_allowed", "endpoint_url_value_allowed", "channel_identity_value_allowed", "http_headers_included", "http_method_included", "http_path_included", "http_body_included", "curl_command_included", "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included", "metrics_included", "public_url", "public_metrics")
REQUIRED_TRUE_UPSTREAM_FLAGS = ("discord_heavy_local_pre_live_batch_available", "discord_heavy_local_pre_live_batch_declared_ready", "eligible_for_future_explicit_scoped_discord_live_pilot_execution_task", "next_explicit_live_pilot_execution_task_required", "pre_live_envelope_non_runtime", "pre_live_ready_for_future_scoped_live_task", "pre_live_requires_new_explicit_live_task_prompt", "pre_live_requires_env_scope_contract", "pre_live_requires_credential_presence_membership_only", "pre_live_requires_destination_binding", "pre_live_requires_payload_hash_revalidation", "pre_live_requires_kill_switch", "pre_live_requires_redacted_audit", "pre_live_requires_manual_fallback", "request_draft_shell_non_executable", "request_draft_idempotency_required", "request_draft_kill_switch_required", "request_draft_audit_redaction_required", "request_draft_manual_fallback_required", "final_confirmation_record_only", "final_confirmation_requires_future_operator_phrase")
LINEAGE_IDS = ("discord_heavy_local_pre_live_batch_id", "discord_exact_operator_live_dispatch_approval_gate_id", "discord_supervised_live_pilot_materialization_gate_id", "explicit_discord_live_scope_contract_gate_id", "discord_supervised_live_pilot_gate_planning_id", "discord_final_manual_execution_review_id", "discord_supervised_request_package_staging_id", "discord_request_policy_gate_id", "discord_operator_payload_review_gate_id", "discord_dry_run_payload_gate_id", "discord_permission_probe_preflight_id", "discord_webhook_value_binding_preflight_id", "discord_endpoint_mapping_preflight_id", "platform_capability_lane_split_id", "official_platform_docs_verification_id", "dispatch_request_package_gate_id", "account_binding_preflight_id", "credential_allowlist_preflight_id", "live_dispatch_scope_preflight_id", "live_dispatch_readiness_preflight_id")

@dataclass(frozen=True)
class DiscordLiveCapableSupervisedPilotAdapterPacket:
    schema_version: str
    task_label: str
    discord_live_capable_supervised_pilot_adapter_id: str
    discord_live_capable_supervised_pilot_adapter_declaration_id: str
    operator_id: str
    created_at_manual: str
    platform: str
    upstream_task_label: str
    discord_heavy_local_pre_live_batch_id: str
    lineage: dict[str, str]
    adapter_contract: dict[str, Any]
    policy_validator: dict[str, Any]
    dry_run_harness: dict[str, Any]
    redacted_audit_schema: dict[str, Any]
    manual_operator_runbook: dict[str, Any]
    future_live_execution_blockers: list[str]
    adapter_available: bool
    adapter_declared_ready: bool
    live_execution_enabled_now: bool
    live_dispatch_approval_granted: bool
    executable_request_artifact_created: bool
    executable_request_artifact_creation_allowed: bool
    webhook_value_read_allowed: bool
    discord_api_call_allowed: bool
    webhook_send_test_allowed: bool
    browser_session_allowed: bool
    env_read_allowed: bool
    dot_env_read_allowed: bool
    public_url_created: bool
    metrics_created: bool
    publication_ready: bool
    dispatch_allowed: bool
    requires_future_explicit_live_execution_task: bool
    requires_exact_operator_confirmation_later: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_summary: str = ""
    packet_sha256: str = ""

def _canonical_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None)
    return hashlib.sha256(json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()

def _walk_values(obj: Any) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items(): walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for idx, child in enumerate(value): walk(child, f"{path}[{idx}]")
        else: out.append((path, value))
    walk(obj, ""); return out

def _assert_safe_payload(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk_values(obj):
        low_path = path.lower()
        if value is None:
            pass
        elif isinstance(value, bool) and low_path.endswith(("_allowed", "_included", "_created", "_ready")):
            pass
        elif any(part in low_path for part in FORBIDDEN_KEY_PARTS):
            raise ValueError(f"{label}_forbidden_key:{path}")
        if isinstance(value, str):
            low_value = value.lower()
            if SECRET_VALUE_RE.search(value):
                raise ValueError(f"{label}_forbidden_value:{path}")
            if any(phrase in low_value for phrase in FORBIDDEN_LIVE_PHRASES):
                raise ValueError(f"{label}_forbidden_live_claim:{path}")

def _add(blockers: list[str], condition: bool, message: str) -> None:
    if not condition: blockers.append(message)

def _validate_upstream(upstream: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    _add(blockers, upstream.get("schema_version") == SCHEMA_VERSION, "invalid_upstream_schema_version")
    _add(blockers, upstream.get("task_label") == UPSTREAM_TASK_LABEL, "invalid_upstream_task_label")
    _add(blockers, upstream.get("platform") == "discord", "upstream_platform_not_discord")
    for key in LINEAGE_IDS: _add(blockers, bool(upstream.get(key)), f"missing_upstream_{key}")
    for key in REQUIRED_TRUE_UPSTREAM_FLAGS: _add(blockers, upstream.get(key) is True, f"upstream_{key}_not_true")
    for key in EXPECTED_FALSE_FLAGS: _add(blockers, upstream.get(key) in (False, None), f"upstream_{key}_not_false")
    _add(blockers, upstream.get("request_draft_max_request_count") == 1, "upstream_request_count_not_one")
    _add(blockers, upstream.get("request_draft_max_retries") == 0, "upstream_retries_not_zero")
    _add(blockers, upstream.get("request_draft_hidden_retry_allowed") is False, "upstream_hidden_retry_not_false")
    _add(blockers, upstream.get("blockers", []) == [], "upstream_blockers_not_empty")
    return blockers

def _validate_declaration(upstream: dict[str, Any], decl: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    checks = {
        "schema_version": SCHEMA_VERSION,
        "platform": "discord",
        "adapter_mode": DECLARATION_MODE,
        "adapter_kind": ADAPTER_KIND,
        "enable_live_execution_now": False,
        "adapter_disabled_by_default": True,
        "requires_future_explicit_live_execution_task": True,
        "requires_exact_operator_confirmation_later": True,
        "env_read_allowed": False,
        "dot_env_read_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "executable_request_artifact_creation_allowed": False,
        "public_url_created": False,
        "metrics_created": False,
        "max_request_count": upstream.get("pre_live_max_request_count"),
        "timeout_seconds": upstream.get("pre_live_timeout_seconds"),
        "max_retries": 0,
        "hidden_retry_allowed": False,
    }
    for key, expected in checks.items(): _add(blockers, decl.get(key) == expected, f"declaration_{key}_invalid")
    _add(blockers, bool(decl.get("discord_live_capable_supervised_pilot_adapter_declaration_id")), "missing_adapter_declaration_id")
    _add(blockers, bool(decl.get("operator_id")), "missing_operator_id")
    _add(blockers, bool(decl.get("created_at_manual")), "missing_created_at_manual")
    for key in LINEAGE_IDS:
        if key in decl: _add(blockers, decl.get(key) == upstream.get(key), f"declaration_{key}_mismatch")
    return blockers

def load_json_packet(path: str | Path, error_label: str) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError(error_label) from exc
    if not isinstance(data, dict): raise ValueError(error_label)
    return data

def make_discord_live_capable_supervised_pilot_adapter_packet(upstream: dict[str, Any], declaration: dict[str, Any]) -> DiscordLiveCapableSupervisedPilotAdapterPacket:
    _assert_safe_payload(upstream, "upstream"); _assert_safe_payload(declaration, "declaration")
    blockers = _validate_upstream(upstream) + _validate_declaration(upstream, declaration)
    available = not blockers
    lineage = {key: str(upstream.get(key, "")) for key in LINEAGE_IDS}
    future_blockers = ["future_explicit_live_execution_task_required", "exact_operator_confirmation_required_later", "credential_presence_membership_only_required_later", "destination_binding_required_later", "payload_hash_revalidation_required_later", "kill_switch_required_later", "redacted_audit_required_later", "manual_fallback_required_later", "live_dispatch_disabled_in_this_packet"]
    adapter_contract = {"kind": ADAPTER_KIND, "platform": "discord", "adapter_disabled_by_default": True, "live_execution_enabled_now": False, "future_live_shape_available": available, "request_budget_label": upstream.get("pre_live_request_budget_label", ""), "max_request_count": upstream.get("pre_live_max_request_count", 0), "timeout_seconds": upstream.get("pre_live_timeout_seconds", 0), "max_retries": 0, "hidden_retry_allowed": False, "idempotency_required": True, "kill_switch_required": True, "manual_fallback_required": True}
    policy_validator = {"kind": "discord_supervised_pilot_policy_validator_local_only", "validates_flags_only": True, "validates_credential_values": False, "env_reads_permitted": False, "provider_calls_permitted": False, "network_calls_permitted": False, "browser_sessions_permitted": False, "blocked_when_any_live_flag_true": True}
    dry_run_harness = {"kind": "discord_supervised_pilot_dry_run_harness_no_provider_call", "emits_local_summary_only": True, "constructs_executable_request": False, "contains_endpoint_value": False, "contains_headers": False, "contains_body": False, "contains_curl": False, "contains_fetch_or_http_client_code": False}
    redacted_audit_schema = {"kind": "discord_redacted_adapter_audit_schema_no_secret_values", "allowed_fields": ["adapter_packet_id", "lineage_ids", "policy_flags", "operator_declaration_id", "future_blockers", "local_validation_result"], "secret_values_allowed": False, "secret_hashes_allowed": False, "public_urls_allowed": False, "metrics_allowed": False}
    manual_operator_runbook = {"kind": "discord_manual_operator_runbook_future_live_task_only", "steps": ["review_adapter_packet_locally", "do_not_send_from_this_packet", "wait_for_future_explicit_live_execution_task", "confirm_kill_switch_and_manual_fallback_later"], "states_publication_readiness": False, "states_live_dispatch_approval": False}
    packet = DiscordLiveCapableSupervisedPilotAdapterPacket(SCHEMA_VERSION, TASK_LABEL, "discord_live_capable_supervised_pilot_adapter_" + hashlib.sha256((upstream.get("discord_heavy_local_pre_live_batch_id", "") + declaration.get("discord_live_capable_supervised_pilot_adapter_declaration_id", "")).encode("utf-8")).hexdigest()[:16], declaration.get("discord_live_capable_supervised_pilot_adapter_declaration_id", ""), declaration.get("operator_id", ""), declaration.get("created_at_manual", ""), "discord", UPSTREAM_TASK_LABEL, upstream.get("discord_heavy_local_pre_live_batch_id", ""), lineage, adapter_contract, policy_validator, dry_run_harness, redacted_audit_schema, manual_operator_runbook, future_blockers, available, available, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, blockers, ["local_only_adapter_no_live_send", "future_live_task_required"], "Local adapter scaffold emitted without env reads, webhook reads, provider calls, public URLs, metrics, or dispatch.")
    data = asdict(packet)
    return DiscordLiveCapableSupervisedPilotAdapterPacket(**{**data, "packet_sha256": _canonical_sha(data)})

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Discord live-capable supervised pilot adapter CLI")
    parser.add_argument("--input-heavy-batch-packet", required=True)
    parser.add_argument("--operator-adapter-declaration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        packet = make_discord_live_capable_supervised_pilot_adapter_packet(load_json_packet(args.input_heavy_batch_packet, "malformed_heavy_batch_packet_json"), load_json_packet(args.operator_adapter_declaration, "malformed_adapter_declaration_json"))
    except ValueError as exc:
        packet = DiscordLiveCapableSupervisedPilotAdapterPacket(SCHEMA_VERSION, TASK_LABEL, "discord_live_capable_supervised_pilot_adapter_blocked", "", "", "", "discord", UPSTREAM_TASK_LABEL, "", {}, {}, {}, {}, {}, {}, ["repair_input_required"], False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, [str(exc)], ["adapter_packet_blocked_pending_operator_repair"])
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.adapter_available else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
