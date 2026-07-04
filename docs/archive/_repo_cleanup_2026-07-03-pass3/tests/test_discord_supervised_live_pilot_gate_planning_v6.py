import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_supervised_live_pilot_gate_planning_v6 import (
    make_discord_supervised_live_pilot_gate_planning_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_FINAL_MANUAL_EXECUTION_REVIEW_FROM_REQUEST_PACKAGE_STAGING_V0",
        "discord_final_manual_execution_review_id": "discord_final_manual_execution_review_abc123",
        "discord_final_manual_execution_review_declaration_id": "discord_final_manual_execution_review_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:30:00+07:00",
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
        "reviewed_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "reviewed_request_package_kind": "non_executable_discord_supervised_request_package_shell",
        "reviewed_request_package_non_executable": True,
        "reviewed_no_webhook_url": True,
        "reviewed_no_webhook_token": True,
        "reviewed_no_endpoint_url": True,
        "reviewed_no_channel_identity": True,
        "reviewed_no_http_headers": True,
        "reviewed_no_http_body": True,
        "reviewed_no_curl_command": True,
        "reviewed_no_browser_instruction": True,
        "reviewed_no_public_url": True,
        "reviewed_no_metrics": True,
        "reviewed_max_request_count": 1,
        "reviewed_timeout_seconds": 15,
        "reviewed_max_retries": 0,
        "reviewed_hidden_retry_allowed": False,
        "reviewed_kill_switch_confirmed": True,
        "reviewed_audit_redaction_confirmed": True,
        "reviewed_manual_fallback_confirmed": True,
        "reviewed_idempotency_later_confirmed": True,
        "reviewed_payload_hash_revalidation_later_confirmed": True,
        "reviewed_permission_verification_later_confirmed": True,
        "operator_final_review_decision": "approve_final_manual_execution_review_for_future_supervised_live_pilot_gate_only",
        "live_dispatch_approval_granted": False,
        "publication_approval_granted": False,
        "executable_request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "discord_final_manual_execution_review_available": True,
        "discord_final_manual_execution_review_declared_ready": True,
        "eligible_for_discord_supervised_live_pilot_gate_planning": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
        "next_local_gate_later_required": True,
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
        "discord_supervised_live_pilot_gate_planning_declaration_id": "discord_supervised_live_pilot_planning_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:35:00+07:00",
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
        "planning_mode": "operator_declared_discord_supervised_live_pilot_gate_planning_only_not_live",
        "planned_action_class": "future_supervised_discord_webhook_send_pilot_not_now",
        "planned_endpoint_family_label": "discord_execute_webhook_label_only",
        "planned_credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "planned_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "planned_request_budget": "single_supervised_request_future_scope",
        "planned_max_request_count": 1,
        "planned_timeout_seconds": 15,
        "planned_max_retries": 0,
        "planned_hidden_retry_allowed": False,
        "planned_idempotency_required": True,
        "planned_kill_switch_required": True,
        "planned_audit_redaction_required": True,
        "planned_manual_fallback_required": True,
        "planned_permission_probe_required_later": True,
        "planned_payload_hash_revalidation_required": True,
        "planned_exact_operator_approval_required_later": True,
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
        "operator_live_pilot_planning_decision": "approve_live_pilot_plan_for_future_explicit_live_scope_only",
        "next_explicit_live_scope_required": True,
        "declaration_decision": "mark_discord_supervised_live_pilot_gate_planning_ready",
        "approval_phrase": "MARK_DISCORD_SUPERVISED_LIVE_PILOT_GATE_PLANNING_READY_ONLY_NOT_LIVE",
        "approval_scope": "discord_supervised_live_pilot_gate_planning_only",
        "notes": "Verified Discord supervised live pilot planning."
    }


def _assert_no_public_state(packet):
    assert packet.live_send_request_created is False
    assert packet.approval_for_live_dispatch is False
    assert packet.approval_for_publication is False
    assert packet.approved_canonical_article_available is False
    assert packet.publication_ready is False
    assert packet.dispatch_allowed is False
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
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), _declaration())
    assert packet.discord_supervised_live_pilot_gate_planning_available is True
    assert packet.discord_supervised_live_pilot_gate_planning_declared_ready is True
    assert packet.eligible_for_future_explicit_discord_live_scope_contract_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.next_explicit_live_scope_required is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_planned_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["planned_payload_hash"] = "wrong"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False
    assert "declaration_planned_payload_hash_mismatch" in packet.blockers


def test_planned_credential_key_mismatch_fails_closed():
    decl = _declaration()
    decl["planned_credential_key_name"] = "wrong"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False
    assert "declaration_planned_credential_key_name_invalid" in packet.blockers


def test_planned_action_class_or_endpoint_family_mismatch_fails_closed():
    for k, v in [("planned_action_class", "wrong"), ("planned_endpoint_family_label", "wrong")]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_planned_max_request_count_not_1_fails_closed():
    decl = _declaration()
    decl["planned_max_request_count"] = 2
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_planned_timeout_seconds_mismatch_or_out_of_bounds_fails_closed():
    decl1 = _declaration()
    decl1["planned_timeout_seconds"] = 16  # mismatch with preflight 15
    packet1 = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl1)
    assert packet1.discord_supervised_live_pilot_gate_planning_available is False

    decl2 = _declaration()
    decl2["planned_timeout_seconds"] = 4  # out of bounds
    preflight = _preflight_packet()
    preflight["reviewed_timeout_seconds"] = 4
    packet2 = make_discord_supervised_live_pilot_gate_planning_packet(preflight, decl2)
    assert packet2.discord_supervised_live_pilot_gate_planning_available is False


def test_planned_max_retries_not_0_or_planned_hidden_retry_true_fails_closed():
    for k, v in [("planned_max_retries", 1), ("planned_hidden_retry_allowed", True)]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_any_planned_required_boolean_false_fails_closed():
    for f in [
        "planned_idempotency_required", "planned_kill_switch_required", "planned_audit_redaction_required",
        "planned_manual_fallback_required", "planned_permission_probe_required_later",
        "planned_payload_hash_revalidation_required", "planned_exact_operator_approval_required_later"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False
        assert f"declaration_field_{f}_not_true" in packet.blockers


def test_approvals_granted_true_fails_closed():
    for f in ["live_dispatch_approval_granted", "publication_approval_granted"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_executable_request_artifact_creation_allowed_true_fails_closed():
    decl = _declaration()
    decl["executable_request_artifact_creation_allowed"] = True
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_discord_api_send_flags_true_fail_closed():
    for f in [
        "discord_api_call_allowed", "webhook_send_test_allowed", "endpoint_url_value_allowed", "channel_identity_value_allowed",
        "http_headers_included", "http_body_included", "curl_command_included", "browser_instruction_included",
        "public_url_included", "metrics_included"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_wrong_preflight_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(preflight, _declaration())
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_preflight_unavailable_or_not_ready_fails_closed():
    for f in ["discord_final_manual_execution_review_available", "discord_final_manual_execution_review_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_supervised_live_pilot_gate_planning_packet(preflight, _declaration())
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_operator_live_pilot_planning_decision_reject_or_defer_fails_closed():
    for dec in ["reject", "defer"]:
        decl = _declaration()
        decl["operator_live_pilot_planning_decision"] = dec
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_planning_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["planning_mode"] = "wrong"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
    assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_declaration_forbidden_content_fails_closed():
    for text in ["my webhook_url is this", "please buy this equity", "fake_url detected"]:
        decl = _declaration()
        decl["notes"] = text
        packet = make_discord_supervised_live_pilot_gate_planning_packet(_preflight_packet(), decl)
        assert packet.discord_supervised_live_pilot_gate_planning_available is False


def test_secret_marker_in_inputs_fails_closed_without_hash_persistence():
    preflight = _preflight_packet()
    preflight["discord_final_manual_execution_review_id"] = "private_key = my_secret"
    packet = make_discord_supervised_live_pilot_gate_planning_packet(preflight, _declaration())
    assert packet.discord_supervised_live_pilot_gate_planning_available is False
    assert packet.planned_payload_hash == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_supervised_live_pilot_gate_planning_v6.py").read_text(encoding="utf-8")
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

    output_file = tmp_path / "planning_packet.json"
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
    assert first["discord_supervised_live_pilot_gate_planning_id"] == second["discord_supervised_live_pilot_gate_planning_id"]
    assert first["discord_supervised_live_pilot_gate_planning_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_SUPERVISED_LIVE_PILOT_GATE_PLANNING_FROM_FINAL_MANUAL_REVIEW")
    paths = [
        Path("live_contentops/discord_supervised_live_pilot_gate_planning_v6.py"),
        Path("tests/test_discord_supervised_live_pilot_gate_planning_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_supervised_live_pilot_gate_planning_packet.json").read_text(encoding="utf-8"))
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
    assert written["discord_supervised_live_pilot_gate_planning_available"] is False
    assert written["discord_supervised_live_pilot_gate_planning_declared_ready"] is False
    assert written["eligible_for_future_explicit_discord_live_scope_contract_gate"] is False
