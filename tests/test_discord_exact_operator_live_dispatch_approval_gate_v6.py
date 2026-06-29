import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_exact_operator_live_dispatch_approval_gate_v6 import (
    make_discord_exact_operator_live_dispatch_approval_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_MATERIALIZATION_GATE_FROM_EXPLICIT_LIVE_SCOPE_CONTRACT_V0",
        "discord_supervised_live_pilot_materialization_gate_id": "discord_supervised_live_pilot_materialization_abc123",
        "discord_supervised_live_pilot_materialization_declaration_id": "discord_supervised_live_pilot_materialization_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:45:00+07:00",
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
        "materialized_action_class": "supervised_discord_webhook_send_pilot_materialization_future_only",
        "materialized_platform_family": "discord_webhook",
        "materialized_endpoint_family_label": "discord_execute_webhook_label_only",
        "materialized_credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "materialized_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "materialized_request_budget": "single_supervised_request_future_scope",
        "materialized_max_request_count": 1,
        "materialized_timeout_seconds": 15,
        "materialized_max_retries": 0,
        "materialized_hidden_retry_allowed": False,
        "materialized_idempotency_required": True,
        "materialized_kill_switch_required": True,
        "materialized_audit_redaction_required": True,
        "materialized_manual_fallback_required": True,
        "materialized_permission_probe_required_later": True,
        "materialized_payload_hash_revalidation_required": True,
        "materialized_exact_operator_approval_required_later": True,
        "materialized_destination_binding_required_later": True,
        "materialized_request_artifact_creation_required_later": True,
        "materialized_package_non_executable": True,
        "materialized_contains_webhook_url": False,
        "materialized_contains_webhook_token": False,
        "materialized_contains_endpoint_url": False,
        "materialized_contains_channel_identity": False,
        "materialized_contains_http_headers": False,
        "materialized_contains_http_body": False,
        "materialized_contains_curl_command": False,
        "materialized_contains_browser_instruction": False,
        "operator_materialization_decision": "approve_supervised_live_pilot_materialization_for_future_exact_operator_approval_only",
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
        "discord_supervised_live_pilot_materialization_gate_available": True,
        "discord_supervised_live_pilot_materialization_gate_declared_ready": True,
        "eligible_for_exact_operator_live_dispatch_approval_gate": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
        "next_exact_operator_live_dispatch_approval_required": True,
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
        "warnings": ["sample_packet_non_runtime", "substack_official_api_docs_unverified"]
    }


def _declaration():
    return {
        "schema_version": "6.0.0",
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
        "combined_payload_hash": "combined_sha256_xyz",
        "platform": "discord",
        "exact_approval_mode": "operator_declared_discord_exact_live_dispatch_approval_record_only_not_live",
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
        "live_dispatch_approval_granted": False,
        "approval_for_live_dispatch": False,
        "dispatch_allowed": False,
        "publication_approval_granted": False,
        "approval_for_publication": False,
        "publication_ready": False,
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
        "operator_exact_approval_decision": "record_exact_operator_approval_for_future_request_artifact_draft_only",
        "next_supervised_request_artifact_draft_gate_required": True,
        "declaration_decision": "mark_discord_exact_operator_live_dispatch_approval_gate_ready",
        "approval_phrase": "MARK_DISCORD_EXACT_OPERATOR_LIVE_DISPATCH_APPROVAL_RECORDED_ONLY_NOT_LIVE",
        "approval_scope": "discord_exact_operator_live_dispatch_approval_record_gate_only",
        "notes": "Verified Discord exact operator live dispatch approval."
    }


def _assert_no_public_state(packet):
    assert packet.live_send_request_created is False
    assert packet.approval_for_live_dispatch is False
    assert packet.dispatch_allowed is False
    assert packet.publication_ready is False
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
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), _declaration())
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is True
    assert packet.discord_exact_operator_live_dispatch_approval_gate_declared_ready is True
    assert packet.eligible_for_supervised_request_artifact_draft_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.next_supervised_request_artifact_draft_gate_required is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_approved_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["approved_payload_hash"] = "wrong"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False
    assert "declaration_approved_payload_hash_mismatch" in packet.blockers


def test_approved_credential_key_mismatch_fails_closed():
    decl = _declaration()
    decl["approved_credential_key_name"] = "wrong"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False
    assert "declaration_approved_credential_key_name_invalid" in packet.blockers


def test_approved_action_class_family_mismatch_fails_closed():
    for k, v in [
        ("approved_action_class_label", "wrong"),
        ("approved_platform_family_label", "wrong"),
        ("approved_endpoint_family_label", "wrong")
    ]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_approved_package_non_executable_false_fails_closed():
    decl = _declaration()
    decl["approved_package_non_executable"] = False
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_approved_contains_webhook_url_token_endpoint_channel_header_body_curl_browser_true_fails_closed():
    for f in [
        "approved_contains_webhook_url",
        "approved_contains_webhook_token",
        "approved_contains_endpoint_url",
        "approved_contains_channel_identity",
        "approved_contains_http_headers",
        "approved_contains_http_body",
        "approved_contains_curl_command",
        "approved_contains_browser_instruction"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False
        assert f"declaration_field_{f}_not_false" in packet.blockers


def test_approved_max_request_count_not_1_fails_closed():
    decl = _declaration()
    decl["approved_max_request_count"] = 2
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_approved_timeout_seconds_mismatch_or_out_of_bounds_fails_closed():
    decl1 = _declaration()
    decl1["approved_timeout_seconds"] = 16  # mismatch with preflight 15
    packet1 = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl1)
    assert packet1.discord_exact_operator_live_dispatch_approval_gate_available is False

    decl2 = _declaration()
    decl2["approved_timeout_seconds"] = 4  # out of bounds
    preflight = _preflight_packet()
    preflight["materialized_timeout_seconds"] = 4
    packet2 = make_discord_exact_operator_live_dispatch_approval_packet(preflight, decl2)
    assert packet2.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_approved_max_retries_not_0_or_approved_hidden_retry_true_fails_closed():
    for k, v in [("approved_max_retries", 1), ("approved_hidden_retry_allowed", True)]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_any_approved_required_boolean_false_fails_closed():
    for f in [
        "approved_idempotency_required", "approved_kill_switch_required", "approved_audit_redaction_required",
        "approved_manual_fallback_required", "approved_permission_probe_required_later",
        "approved_payload_hash_revalidation_required", "approved_destination_binding_required_later",
        "approved_request_artifact_creation_required_later"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False
        assert f"declaration_field_{f}_not_true" in packet.blockers


def test_live_dispatch_approval_granted_true_fails_closed():
    for f in ["live_dispatch_approval_granted", "approval_for_live_dispatch", "dispatch_allowed"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_publication_approval_granted_true_fails_closed():
    for f in ["publication_approval_granted", "approval_for_publication", "publication_ready"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_executable_request_artifact_creation_allowed_true_fails_closed():
    decl = _declaration()
    decl["executable_request_artifact_creation_allowed"] = True
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_discord_api_send_flags_true_fail_closed():
    for f in [
        "discord_api_call_allowed", "webhook_send_test_allowed", "endpoint_url_value_allowed", "channel_identity_value_allowed",
        "http_headers_included", "http_body_included", "curl_command_included", "browser_instruction_included",
        "public_url_included", "metrics_included"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_wrong_preflight_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(preflight, _declaration())
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_preflight_unavailable_or_not_ready_fails_closed():
    for f in ["discord_supervised_live_pilot_materialization_gate_available", "discord_supervised_live_pilot_materialization_gate_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_exact_operator_live_dispatch_approval_packet(preflight, _declaration())
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_operator_exact_approval_decision_reject_or_defer_fails_closed():
    for dec in ["reject", "defer"]:
        decl = _declaration()
        decl["operator_exact_approval_decision"] = dec
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_exact_approval_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["exact_approval_mode"] = "wrong"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_declaration_forbidden_content_fails_closed():
    for text in ["my webhook_url is this", "please buy this equity", "fake_url detected"]:
        decl = _declaration()
        decl["notes"] = text
        packet = make_discord_exact_operator_live_dispatch_approval_packet(_preflight_packet(), decl)
        assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False


def test_secret_marker_in_inputs_fails_closed_without_hash_persistence():
    preflight = _preflight_packet()
    preflight["discord_supervised_live_pilot_materialization_gate_id"] = "private_key = my_secret"
    packet = make_discord_exact_operator_live_dispatch_approval_packet(preflight, _declaration())
    assert packet.discord_exact_operator_live_dispatch_approval_gate_available is False
    assert packet.approved_payload_hash == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_exact_operator_live_dispatch_approval_gate_v6.py").read_text(encoding="utf-8")
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

    output_file = tmp_path / "approval_packet.json"
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
    assert first["discord_exact_operator_live_dispatch_approval_gate_id"] == second["discord_exact_operator_live_dispatch_approval_gate_id"]
    assert first["discord_exact_operator_live_dispatch_approval_gate_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_EXACT_OPERATOR_LIVE_DISPATCH_APPROVAL_GATE_FROM_MATERIALIZATION")
    paths = [
        Path("live_contentops/discord_exact_operator_live_dispatch_approval_gate_v6.py"),
        Path("tests/test_discord_exact_operator_live_dispatch_approval_gate_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_exact_operator_live_dispatch_approval_gate_packet.json").read_text(encoding="utf-8"))
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
    assert written["discord_exact_operator_live_dispatch_approval_gate_available"] is False
    assert written["discord_exact_operator_live_dispatch_approval_gate_declared_ready"] is False
    assert written["eligible_for_supervised_request_artifact_draft_gate"] is False
