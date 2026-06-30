import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_live_capable_supervised_pilot_adapter_v6 import (
    ADAPTER_KIND,
    DECLARATION_MODE,
    TASK_LABEL,
    UPSTREAM_TASK_LABEL,
    main,
    make_discord_live_capable_supervised_pilot_adapter_packet,
)


def _upstream():
    data = {
        "schema_version": "6.0.0",
        "task_label": UPSTREAM_TASK_LABEL,
        "platform": "discord",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T06:00:00+07:00",
        "discord_heavy_local_pre_live_batch_id": "discord_heavy_local_pre_live_batch_abc123",
        "discord_heavy_local_pre_live_batch_declaration_id": "discord_heavy_batch_decl_abc123",
        "discord_exact_operator_live_dispatch_approval_gate_id": "discord_exact_approval_abc123",
        "discord_supervised_live_pilot_materialization_gate_id": "discord_materialization_abc123",
        "explicit_discord_live_scope_contract_gate_id": "explicit_scope_abc123",
        "discord_supervised_live_pilot_gate_planning_id": "discord_planning_abc123",
        "discord_final_manual_execution_review_id": "discord_final_review_abc123",
        "discord_supervised_request_package_staging_id": "discord_staging_abc123",
        "discord_request_policy_gate_id": "discord_policy_abc123",
        "discord_operator_payload_review_gate_id": "discord_payload_review_abc123",
        "discord_dry_run_payload_gate_id": "discord_dry_run_abc123",
        "discord_permission_probe_preflight_id": "discord_probe_abc123",
        "discord_webhook_value_binding_preflight_id": "discord_binding_abc123",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_abc123",
        "dispatch_request_package_gate_id": "dispatch_gate_abc123",
        "account_binding_preflight_id": "account_binding_abc123",
        "credential_allowlist_preflight_id": "credential_allowlist_abc123",
        "live_dispatch_scope_preflight_id": "scope_abc123",
        "live_dispatch_readiness_preflight_id": "readiness_abc123",
        "discord_heavy_local_pre_live_batch_available": True,
        "discord_heavy_local_pre_live_batch_declared_ready": True,
        "eligible_for_future_explicit_scoped_discord_live_pilot_execution_task": True,
        "next_explicit_live_pilot_execution_task_required": True,
        "pre_live_envelope_non_runtime": True,
        "pre_live_ready_for_future_scoped_live_task": True,
        "pre_live_requires_new_explicit_live_task_prompt": True,
        "pre_live_requires_env_scope_contract": True,
        "pre_live_requires_credential_presence_membership_only": True,
        "pre_live_requires_destination_binding": True,
        "pre_live_requires_payload_hash_revalidation": True,
        "pre_live_requires_kill_switch": True,
        "pre_live_requires_redacted_audit": True,
        "pre_live_requires_manual_fallback": True,
        "request_draft_shell_non_executable": True,
        "request_draft_idempotency_required": True,
        "request_draft_kill_switch_required": True,
        "request_draft_audit_redaction_required": True,
        "request_draft_manual_fallback_required": True,
        "final_confirmation_record_only": True,
        "final_confirmation_requires_future_operator_phrase": True,
        "request_draft_max_request_count": 1,
        "request_draft_max_retries": 0,
        "request_draft_hidden_retry_allowed": False,
        "pre_live_request_budget_label": "single_supervised_request_future_scope",
        "pre_live_max_request_count": 1,
        "pre_live_timeout_seconds": 15,
        "pre_live_max_retries": 0,
        "pre_live_hidden_retry_allowed": False,
        "blockers": [],
    }
    for flag in (
        "live_dispatch_approval_granted", "approval_for_live_dispatch", "dispatch_allowed",
        "publication_approval_granted", "approval_for_publication", "publication_ready",
        "executable_request_artifact_created", "executable_request_artifact_creation_allowed",
        "webhook_value_read_allowed", "discord_api_call_allowed", "webhook_send_test_allowed",
        "endpoint_url_value_allowed", "channel_identity_value_allowed", "http_headers_included",
        "http_method_included", "http_path_included", "http_body_included", "curl_command_included",
        "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included",
        "metrics_included",
    ):
        data[flag] = False
    data["public_url"] = None
    data["public_metrics"] = None
    return data


def _declaration():
    upstream = _upstream()
    decl = {
        "schema_version": "6.0.0",
        "discord_live_capable_supervised_pilot_adapter_declaration_id": "adapter_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T06:05:00+07:00",
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
        "max_request_count": 1,
        "timeout_seconds": 15,
        "max_retries": 0,
        "hidden_retry_allowed": False,
    }
    decl.update({k: upstream[k] for k in upstream if k.endswith("_id") and k.startswith(("discord_", "explicit_", "platform_", "official_", "dispatch_", "account_", "credential_", "live_"))})
    return decl


def test_valid_adapter_packet_is_inert_and_deterministic():
    packet = make_discord_live_capable_supervised_pilot_adapter_packet(_upstream(), _declaration())
    data = asdict(packet)
    assert packet.task_label == TASK_LABEL
    assert packet.adapter_available is True
    assert packet.adapter_declared_ready is True
    assert packet.live_execution_enabled_now is False
    assert packet.discord_api_call_allowed is False
    assert packet.webhook_value_read_allowed is False
    assert packet.executable_request_artifact_creation_allowed is False
    assert packet.public_url_created is False
    assert packet.metrics_created is False
    assert packet.dispatch_allowed is False
    assert packet.publication_ready is False
    assert packet.packet_sha256
    assert packet.packet_sha256 == make_discord_live_capable_supervised_pilot_adapter_packet(_upstream(), _declaration()).packet_sha256
    assert "future_explicit_live_execution_task_required" in data["future_live_execution_blockers"]


def test_rejects_live_flag_from_upstream():
    upstream = _upstream()
    upstream["discord_api_call_allowed"] = True
    packet = make_discord_live_capable_supervised_pilot_adapter_packet(upstream, _declaration())
    assert packet.adapter_available is False
    assert "upstream_discord_api_call_allowed_not_false" in packet.blockers


def test_rejects_secret_like_value_without_echoing_value():
    decl = _declaration()
    decl["operator_note"] = "https://discord.com/api/webhooks/123/abc"
    try:
        make_discord_live_capable_supervised_pilot_adapter_packet(_upstream(), decl)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected ValueError")
    assert "forbidden_value" in message
    assert "discord.com/api/webhooks" not in message


def test_rejects_mismatched_lineage_id():
    decl = _declaration()
    decl["discord_heavy_local_pre_live_batch_id"] = "different"
    packet = make_discord_live_capable_supervised_pilot_adapter_packet(_upstream(), decl)
    assert packet.adapter_available is False
    assert "declaration_discord_heavy_local_pre_live_batch_id_mismatch" in packet.blockers


def test_source_has_no_env_or_network_imports():
    src = Path("live_contentops/discord_live_capable_supervised_pilot_adapter_v6.py").read_text(encoding="utf-8")
    forbidden = [r"^import os$", r"dotenv", r"requests", r"urllib", r"http\.client", r"socket", r"subprocess"]
    for pattern in forbidden:
        assert re.search(pattern, src, re.MULTILINE) is None


def test_cli_writes_packet(tmp_path):
    upstream_path = tmp_path / "upstream.json"
    decl_path = tmp_path / "decl.json"
    out_path = tmp_path / "out.json"
    upstream_path.write_text(json.dumps(_upstream()), encoding="utf-8")
    decl_path.write_text(json.dumps(_declaration()), encoding="utf-8")
    rc = main(["--input-heavy-batch-packet", str(upstream_path), "--operator-adapter-declaration", str(decl_path), "--output", str(out_path)])
    assert rc == 0
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["adapter_available"] is True
    assert data["live_execution_enabled_now"] is False
