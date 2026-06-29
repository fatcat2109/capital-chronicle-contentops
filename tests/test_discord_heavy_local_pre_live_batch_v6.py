import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_heavy_local_pre_live_batch_v6 import (
    make_discord_heavy_local_pre_live_batch_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_EXACT_OPERATOR_LIVE_DISPATCH_APPROVAL_GATE_FROM_MATERIALIZATION_V0",
        "discord_exact_operator_live_dispatch_approval_gate_id": "discord_exact_approval_abc123",
        "discord_exact_operator_live_dispatch_approval_declaration_id": "discord_exact_approval_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:50:00+07:00",
        "discord_supervised_live_pilot_materialization_gate_id": "discord_supervised_live_pilot_materialization_abc123",
        "explicit_discord_live_scope_contract_gate_id": "explicit_discord_live_scope_contract_abc123",
        "discord_supervised_live_pilot_gate_planning_id": "discord_supervised_live_pilot_planning_abc123",
        "discord_final_manual_execution_review_id": "discord_final_manual_execution_review_abc123",
        "discord_supervised_request_package_staging_id": "discord_supervised_request_package_staging_abc123",
        "discord_request_policy_gate_id": "discord_request_policy_gate_abc123",
        "discord_operator_payload_review_gate_id": "discord_operator_payload_review_gate_abc123",
        "discord_dry_run_payload_gate_id": "discord_dry_run_payload_gate_abc123",
        "discord_permission_probe_preflight_id": "discord_permission_probe_preflight_abc123",
        "discord_webhook_value_binding_preflight_id": "discord_webhook_value_binding_preflight_abc123",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "dispatch_request_package_gate_sha256": "gate_sha256_abc123",
        "account_binding_preflight_id": "account_binding_preflight_abc123",
        "account_binding_preflight_sha256": "preflight_sha256_abc123",
        "credential_allowlist_preflight_id": "credential_allowlist_preflight_abc123",
        "credential_allowlist_preflight_sha256": "preflight_sha256_abc123",
        "live_dispatch_scope_preflight_id": "scope_preflight_abc123",
        "live_dispatch_scope_preflight_sha256": "scope_sha256_abc123",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "live_dispatch_readiness_preflight_sha256": "readiness_sha256_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "platform": "discord",
        "approved_action_class_label": "supervised_discord_webhook_send_pilot_exact_approval_record_future_only",
        "approved_platform_family_label": "discord_webhook",
        "approved_endpoint_family_label": "discord_execute_webhook_label_only",
        "approved_credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "approved_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "approved_request_budget_label": "single_supervised_request_future_scope",
        "approved_max_request_count": 1,
        "approved_timeout_seconds": 15,
        "approved_max_retries": 0,
        "approved_hidden_retry_allowed": False,
        "approved_idempotency_required": True,
        "approved_kill_switch_required": True,
        "approved_audit_redaction_required": True,
        "approved_manual_fallback_required": True,
        "approved_permission_probe_required_later": True,
        "approved_payload_hash_revalidation_required": True,
        "approved_destination_binding_required_later": True,
        "approved_request_artifact_creation_required_later": True,
        "approved_package_non_executable": True,
        "approved_contains_webhook_url": False,
        "approved_contains_webhook_token": False,
        "approved_contains_endpoint_url": False,
        "approved_contains_channel_identity": False,
        "approved_contains_http_headers": False,
        "approved_contains_http_body": False,
        "approved_contains_curl_command": False,
        "approved_contains_browser_instruction": False,
        "operator_exact_approval_decision": "record_exact_operator_approval_for_future_request_artifact_draft_only",
        "live_dispatch_approval_granted": False,
        "publication_approval_granted": False,
        "executable_request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "endpoint_url_value_allowed": False,
        "channel_identity_value_allowed": False,
        "http_headers_included": False,
        "http_body_included": False,
        "curl_command_included": False,
        "browser_instruction_included": False,
        "public_url_included": False,
        "metrics_included": False,
        "discord_exact_operator_live_dispatch_approval_gate_available": True,
        "discord_exact_operator_live_dispatch_approval_gate_declared_ready": True,
        "eligible_for_supervised_request_artifact_draft_gate": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
        "next_supervised_request_artifact_draft_gate_required": True,
        "substack_manual_fallback_required": True,
        "all_platforms_endpoint_mapping_ready": False,
        "live_send_request_created": False,
        "approval_for_live_dispatch": False,
        "approval_for_publication": False,
        "approved_canonical_article_available": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
        "generated_citations_allowed": False,
        "citations_verified": False,
        "public_url": None,
        "public_metrics": None,
        "review_only": True,
        "human_review_required": True,
        "kill_switch_active": True,
        "runtime_truth": False,
        "blockers": [],
        "warnings": ["substack_official_api_docs_unverified"]
    }


def _declaration():
    return {
        "schema_version": "6.0.0",
        "discord_heavy_local_pre_live_batch_declaration_id": "discord_heavy_batch_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:55:00+07:00",
        "discord_exact_operator_live_dispatch_approval_gate_id": "discord_exact_approval_abc123",
        "discord_supervised_live_pilot_materialization_gate_id": "discord_supervised_live_pilot_materialization_abc123",
        "explicit_discord_live_scope_contract_gate_id": "explicit_discord_live_scope_contract_abc123",
        "discord_supervised_live_pilot_gate_planning_id": "discord_supervised_live_pilot_planning_abc123",
        "discord_final_manual_execution_review_id": "discord_final_manual_execution_review_abc123",
        "discord_supervised_request_package_staging_id": "discord_supervised_request_package_staging_abc123",
        "discord_request_policy_gate_id": "discord_request_policy_gate_abc123",
        "discord_operator_payload_review_gate_id": "discord_operator_payload_review_gate_abc123",
        "discord_dry_run_payload_gate_id": "discord_dry_run_payload_gate_abc123",
        "discord_permission_probe_preflight_id": "discord_permission_probe_preflight_abc123",
        "discord_webhook_value_binding_preflight_id": "discord_webhook_value_binding_preflight_abc123",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "platform": "discord",
        "heavy_batch_mode": "operator_declared_discord_heavy_local_pre_live_batch_only_not_live",
        "request_draft_shell_kind": "redacted_non_executable_discord_request_artifact_draft_shell",
        "request_draft_shell_non_executable": True,
        "request_draft_action_class_label": "supervised_discord_webhook_send_pilot_request_artifact_draft_future_only",
        "request_draft_platform_family_label": "discord_webhook",
        "request_draft_endpoint_family_label": "discord_execute_webhook_label_only",
        "request_draft_credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "request_draft_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "request_draft_request_budget_label": "single_supervised_request_future_scope",
        "request_draft_max_request_count": 1,
        "request_draft_timeout_seconds": 15,
        "request_draft_max_retries": 0,
        "request_draft_hidden_retry_allowed": False,
        "request_draft_idempotency_required": True,
        "request_draft_kill_switch_required": True,
        "request_draft_audit_redaction_required": True,
        "request_draft_manual_fallback_required": True,
        "request_draft_permission_probe_required_later": True,
        "request_draft_payload_hash_revalidation_required": True,
        "request_draft_destination_binding_required_later": True,
        "request_draft_final_operator_send_confirmation_required_later": True,
        "request_draft_contains_webhook_url": False,
        "request_draft_contains_webhook_token": False,
        "request_draft_contains_endpoint_url": False,
        "request_draft_contains_channel_identity": False,
        "request_draft_contains_http_headers": False,
        "request_draft_contains_http_method": False,
        "request_draft_contains_http_path": False,
        "request_draft_contains_http_body": False,
        "request_draft_contains_curl_command": False,
        "request_draft_contains_fetch_or_requests_code": False,
        "request_draft_contains_browser_instruction": False,
        "request_draft_contains_public_url": False,
        "request_draft_contains_metrics": False,
        "final_confirmation_record_kind": "final_operator_send_confirmation_record_shell_only",
        "final_confirmation_record_only": True,
        "final_confirmation_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "final_confirmation_request_count": 1,
        "final_confirmation_timeout_seconds": 15,
        "final_confirmation_max_retries": 0,
        "final_confirmation_hidden_retry_allowed": False,
        "final_confirmation_requires_future_operator_phrase": True,
        "final_confirmation_contains_live_send_instruction": False,
        "final_confirmation_contains_webhook_value": False,
        "final_confirmation_contains_executable_request": False,
        "pre_live_envelope_kind": "discord_pre_live_execution_readiness_envelope_non_runtime",
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
        "pre_live_request_budget_label": "single_supervised_request_future_scope",
        "pre_live_max_request_count": 1,
        "pre_live_timeout_seconds": 15,
        "pre_live_max_retries": 0,
        "pre_live_hidden_retry_allowed": False,
        "live_dispatch_approval_granted": False,
        "approval_for_live_dispatch": False,
        "dispatch_allowed": False,
        "publication_approval_granted": False,
        "approval_for_publication": False,
        "publication_ready": False,
        "executable_request_artifact_created": False,
        "executable_request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "endpoint_url_value_allowed": False,
        "channel_identity_value_allowed": False,
        "http_headers_included": False,
        "http_method_included": False,
        "http_path_included": False,
        "http_body_included": False,
        "curl_command_included": False,
        "fetch_or_requests_code_included": False,
        "browser_instruction_included": False,
        "public_url_included": False,
        "metrics_included": False,
        "operator_heavy_batch_decision": "approve_heavy_local_pre_live_batch_for_future_explicit_live_pilot_task_only",
        "next_explicit_live_pilot_execution_task_required": True,
        "declaration_decision": "mark_discord_heavy_local_pre_live_batch_ready",
        "approval_phrase": "MARK_DISCORD_HEAVY_LOCAL_PRE_LIVE_BATCH_READY_ONLY_NOT_LIVE",
        "approval_scope": "discord_heavy_local_pre_live_batch_only",
        "notes": "Verified Discord heavy local pre-live batch."
    }


def _assert_no_public_state(packet):
    assert packet.live_send_request_created is False
    assert packet.live_dispatch_approval_granted is False
    assert packet.approval_for_live_dispatch is False
    assert packet.dispatch_allowed is False
    assert packet.publication_approval_granted is False
    assert packet.approval_for_publication is False
    assert packet.publication_ready is False
    assert packet.executable_request_artifact_created is False
    assert packet.executable_request_artifact_creation_allowed is False
    assert packet.webhook_value_read_allowed is False
    assert packet.discord_api_call_allowed is False
    assert packet.webhook_send_test_allowed is False
    assert packet.endpoint_url_value_allowed is False
    assert packet.channel_identity_value_allowed is False
    assert packet.http_headers_included is False
    assert packet.http_method_included is False
    assert packet.http_path_included is False
    assert packet.http_body_included is False
    assert packet.curl_command_included is False
    assert packet.fetch_or_requests_code_included is False
    assert packet.browser_instruction_included is False
    assert packet.public_url_included is False
    assert packet.metrics_included is False
    assert packet.approved_canonical_article_available is False
    assert packet.platform_variant_generation_allowed is False
    assert packet.outbox_creation_allowed is False
    assert packet.generated_citations_allowed is False
    assert packet.citations_verified is False
    assert packet.public_url is None
    assert packet.public_metrics is None
    assert packet.review_only is True
    assert packet.human_review_required is True
    assert packet.kill_switch_active is True
    assert packet.runtime_truth is False


def test_valid_inputs_emits_eligible_packet():
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), _declaration())
    assert packet.discord_heavy_local_pre_live_batch_available is True
    assert packet.discord_heavy_local_pre_live_batch_declared_ready is True
    assert packet.eligible_for_future_explicit_scoped_discord_live_pilot_execution_task is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_exact_approval_packet_label_mismatch_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_heavy_local_pre_live_batch_packet(preflight, _declaration())
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_exact_approval_unavailable_not_declared_ready_fails_closed():
    for f in ["discord_exact_operator_live_dispatch_approval_gate_available", "discord_exact_operator_live_dispatch_approval_gate_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_heavy_local_pre_live_batch_packet(preflight, _declaration())
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["request_draft_payload_hash"] = "wrong"
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_mismatches_fail_closed():
    for k, v in [
        ("request_draft_action_class_label", "wrong"),
        ("request_draft_platform_family_label", "wrong"),
        ("request_draft_endpoint_family_label", "wrong"),
        ("request_draft_credential_key_name", "wrong"),
        ("request_draft_shell_kind", "wrong"),
    ]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_non_executable_false_fails_closed():
    decl = _declaration()
    decl["request_draft_shell_non_executable"] = False
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_contains_any_flag_true_fails_closed():
    for f in [
        "request_draft_contains_webhook_url", "request_draft_contains_webhook_token",
        "request_draft_contains_endpoint_url", "request_draft_contains_channel_identity",
        "request_draft_contains_http_headers", "request_draft_contains_http_method",
        "request_draft_contains_http_path", "request_draft_contains_http_body",
        "request_draft_contains_curl_command", "request_draft_contains_fetch_or_requests_code",
        "request_draft_contains_browser_instruction", "request_draft_contains_public_url",
        "request_draft_contains_metrics"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_parameters_fail_closed():
    for k, v in [
        ("request_draft_max_request_count", 2),
        ("request_draft_timeout_seconds", 4),  # too small
        ("request_draft_timeout_seconds", 31),  # too large
        ("request_draft_max_retries", 1),
        ("request_draft_hidden_retry_allowed", True)
    ]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_request_draft_booleans_fail_closed():
    for f in [
        "request_draft_idempotency_required", "request_draft_kill_switch_required",
        "request_draft_audit_redaction_required", "request_draft_manual_fallback_required",
        "request_draft_permission_probe_required_later", "request_draft_payload_hash_revalidation_required",
        "request_draft_destination_binding_required_later", "request_draft_final_operator_send_confirmation_required_later"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_final_confirmation_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["final_confirmation_payload_hash"] = "wrong"
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_final_confirmation_violations_fail_closed():
    for k, v in [
        ("final_confirmation_request_count", 2),
        ("final_confirmation_timeout_seconds", 35),
        ("final_confirmation_max_retries", 1),
        ("final_confirmation_hidden_retry_allowed", True),
        ("final_confirmation_requires_future_operator_phrase", False),
        ("final_confirmation_contains_live_send_instruction", True),
        ("final_confirmation_contains_webhook_value", True),
        ("final_confirmation_contains_executable_request", True),
    ]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_pre_live_envelope_non_runtime_false_fails_closed():
    decl = _declaration()
    decl["pre_live_envelope_non_runtime"] = False
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_pre_live_envelope_missing_requirements_fail_closed():
    for f in [
        "pre_live_requires_new_explicit_live_task_prompt", "pre_live_requires_env_scope_contract",
        "pre_live_requires_credential_presence_membership_only", "pre_live_requires_destination_binding",
        "pre_live_requires_payload_hash_revalidation", "pre_live_requires_kill_switch",
        "pre_live_requires_redacted_audit", "pre_live_requires_manual_fallback"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_global_safety_flags_true_fail_closed():
    for f in [
        "live_dispatch_approval_granted", "approval_for_live_dispatch", "dispatch_allowed",
        "publication_approval_granted", "approval_for_publication", "publication_ready",
        "executable_request_artifact_created", "executable_request_artifact_creation_allowed",
        "webhook_value_read_allowed", "discord_api_call_allowed", "webhook_send_test_allowed",
        "endpoint_url_value_allowed", "channel_identity_value_allowed", "http_headers_included",
        "http_method_included", "http_path_included", "http_body_included", "curl_command_included",
        "fetch_or_requests_code_included", "browser_instruction_included", "public_url_included",
        "metrics_included"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_operator_heavy_batch_decision_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["operator_heavy_batch_decision"] = val
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_declaration_decision_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_heavy_batch_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["heavy_batch_mode"] = "wrong"
    packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
    assert packet.discord_heavy_local_pre_live_batch_available is False


def test_forbidden_words_in_declaration_fail_closed():
    for term in ["my webhook_url is this", "please buy this equity", "fake_url detected"]:
        decl = _declaration()
        decl["notes"] = term
        packet = make_discord_heavy_local_pre_live_batch_packet(_preflight_packet(), decl)
        assert packet.discord_heavy_local_pre_live_batch_available is False


def test_secret_marker_fails_closed_without_derived_hash_persistence():
    preflight = _preflight_packet()
    preflight["discord_exact_operator_live_dispatch_approval_gate_id"] = "private_key = my_secret"
    packet = make_discord_heavy_local_pre_live_batch_packet(preflight, _declaration())
    assert packet.discord_heavy_local_pre_live_batch_available is False
    assert packet.approved_payload_hash == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_heavy_local_pre_live_batch_v6.py").read_text(encoding="utf-8")
    forbidden = [
        r"\bimport\s+os\b",
        r"\benviron\b",
        r"\bgetenv\b",
        r"\bimport\s+dotenv\b",
        r"\bload_dotenv\b",
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bimport\s+httpx\b",
        r"\bimport\s+webbrowser\b",
        r"\bimport\s+selenium\b",
        r"\bimport\s+playwright\b",
    ]
    for pat in forbidden:
        assert not re.search(pat, source)


def test_cli_writes_deterministic_packet(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text(json.dumps(_preflight_packet()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    output_file = tmp_path / "batch_packet.json"
    assert main([
        str(p_path),
        str(b_path),
        "--output-file", str(output_file)
    ]) == 0

    first = json.loads(output_file.read_text(encoding="utf-8"))

    assert main([
        str(p_path),
        str(b_path),
        "--output-file", str(output_file)
    ]) == 0

    second = json.loads(output_file.read_text(encoding="utf-8"))
    assert first["discord_heavy_local_pre_live_batch_id"] == second["discord_heavy_local_pre_live_batch_id"]
    assert first["discord_heavy_local_pre_live_batch_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_HEAVY_LOCAL_PRE_LIVE_BATCH_FROM_EXACT_OPERATOR_APPROVAL")
    paths = [
        Path("live_contentops/discord_heavy_local_pre_live_batch_v6.py"),
        Path("tests/test_discord_heavy_local_pre_live_batch_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_heavy_local_pre_live_batch_packet.json").read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "6.0.0"
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_preflight_packet.json"
    exit_code = main([
        str(p_path),
        "A:/declaration.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["discord_heavy_local_pre_live_batch_available"] is False
    assert written["discord_heavy_local_pre_live_batch_declared_ready"] is False
    assert written["eligible_for_future_explicit_scoped_discord_live_pilot_execution_task"] is False
