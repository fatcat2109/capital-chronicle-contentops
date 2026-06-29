import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_permission_probe_preflight_v6 import (
    make_discord_permission_probe_preflight_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_WEBHOOK_VALUE_BINDING_PREFLIGHT_FROM_ENDPOINT_MAPPING_V0",
        "discord_webhook_value_binding_preflight_id": "discord_webhook_value_binding_preflight_abc123",
        "discord_webhook_value_binding_declaration_id": "discord_webhook_value_binding_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T04:00:00+07:00",
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
        "credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "credential_kind": "discord_webhook_url_secret_value_later",
        "credential_presence_checked": True,
        "credential_present": True,
        "credential_presence_mode": "process_env_exact_key_membership_only",
        "webhook_value_source": "process_env_exact_key_membership_only",
        "webhook_value_read_allowed": False,
        "webhook_value_persist_allowed": False,
        "webhook_value_hash_allowed": False,
        "webhook_value_length_allowed": False,
        "webhook_value_prefix_suffix_allowed": False,
        "webhook_url_shape_validation_allowed": False,
        "discord_api_validation_allowed": False,
        "webhook_send_test_allowed": False,
        "webhook_value_observed": False,
        "webhook_value_persisted": False,
        "webhook_value_hash_observed": False,
        "webhook_value_length_observed": False,
        "webhook_value_prefix_suffix_observed": False,
        "webhook_url_shape_validated": False,
        "discord_api_validated": False,
        "webhook_send_test_performed": False,
        "channel_identity_later_required": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "request_budget_later_required": True,
        "timeout_policy_later_required": True,
        "retry_policy_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "substack_manual_fallback_required": True,
        "all_platforms_endpoint_mapping_ready": False,
        "discord_webhook_value_binding_preflight_available": True,
        "discord_webhook_value_binding_preflight_declared_ready": True,
        "eligible_for_discord_permission_probe_gate": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
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
        "discord_permission_probe_declaration_id": "discord_permission_probe_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T04:30:00+07:00",
        "discord_webhook_value_binding_preflight_id": "discord_webhook_value_binding_preflight_abc123",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "permission_probe_mode": "operator_declared_discord_permission_probe_preflight_only_not_call",
        "platform": "discord",
        "credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "probe_kind": "discord_webhook_permission_probe_later_not_now",
        "webhook_value_read_allowed": False,
        "webhook_url_shape_validation_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "channel_identity_value_allowed": False,
        "channel_identity_verification_later_required": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "request_budget_later_required": True,
        "timeout_policy_later_required": True,
        "retry_policy_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "declaration_decision": "mark_discord_permission_probe_preflight_ready",
        "approval_phrase": "MARK_DISCORD_PERMISSION_PROBE_PREFLIGHT_READY_ONLY_NOT_CALL",
        "approval_scope": "discord_permission_probe_preflight_only",
        "notes": "Verified Discord webhook permission probe."
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
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), _declaration())
    assert packet.permission_probe_preflight_available is True
    assert packet.permission_probe_preflight_declared_ready is True
    assert packet.eligible_for_discord_dry_run_payload_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_output_contains_no_secrets_or_allowed_values():
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), _declaration())
    assert packet.webhook_value_read_allowed is False
    assert packet.webhook_url_shape_validation_allowed is False
    assert packet.discord_api_call_allowed is False
    assert packet.webhook_send_test_allowed is False
    assert packet.channel_identity_value_allowed is False


def test_wrong_value_binding_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_permission_probe_preflight_packet(preflight, _declaration())
    assert packet.permission_probe_preflight_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_value_binding_unavailable_or_not_declared_ready_fails_closed():
    for f in ["discord_webhook_value_binding_preflight_available", "discord_webhook_value_binding_preflight_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_permission_probe_preflight_packet(preflight, _declaration())
        assert packet.permission_probe_preflight_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
        assert packet.permission_probe_preflight_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False
    assert "declaration_platform_invalid" in packet.blockers


def test_credential_key_name_mismatch_fails_closed():
    decl = _declaration()
    decl["credential_key_name"] = "wrong"
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False


def test_probe_kind_mismatch_fails_closed():
    decl = _declaration()
    decl["probe_kind"] = "wrong"
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False


def test_permission_probe_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["permission_probe_mode"] = "wrong"
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False


def test_value_flags_true_fails_closed():
    for f in ["webhook_value_read_allowed", "discord_api_call_allowed"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
        assert packet.permission_probe_preflight_available is False


def test_later_required_boolean_false_fails_closed():
    decl = _declaration()
    decl["permission_verification_later_required"] = False
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False


def test_declaration_safety_check_detects_forbidden_claims():
    decl = _declaration()
    decl["notes"] = "Accessing api_endpoint value."
    packet = make_discord_permission_probe_preflight_packet(_preflight_packet(), decl)
    assert packet.permission_probe_preflight_available is False
    assert "declaration_forbidden_live_claim_detected_api_endpoint" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha256():
    preflight = _preflight_packet()
    preflight["discord_webhook_value_binding_preflight_id"] = "private_key = my_secret"
    packet = make_discord_permission_probe_preflight_packet(preflight, _declaration())
    assert packet.permission_probe_preflight_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_permission_probe_preflight_v6.py").read_text(encoding="utf-8")
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

    output_file = tmp_path / "permission_probe_preflight_packet.json"
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
    assert first["discord_permission_probe_preflight_id"] == second["discord_permission_probe_preflight_id"]
    assert first["permission_probe_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_PERMISSION_PROBE_PREFLIGHT_FROM_WEBHOOK_VALUE_BINDING")
    paths = [
        Path("live_contentops/discord_permission_probe_preflight_v6.py"),
        Path("tests/test_discord_permission_probe_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_permission_probe_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
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
    assert written["permission_probe_preflight_available"] is False
    assert written["permission_probe_preflight_declared_ready"] is False
    assert written["eligible_for_discord_dry_run_payload_gate"] is False
