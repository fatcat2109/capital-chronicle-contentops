import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_request_policy_gate_v6 import (
    make_discord_request_policy_gate_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_OPERATOR_PAYLOAD_REVIEW_GATE_FROM_DRY_RUN_PAYLOAD_V0",
        "discord_operator_payload_review_gate_id": "discord_operator_payload_review_gate_abc123",
        "discord_operator_payload_review_declaration_id": "discord_operator_payload_review_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:00:00+07:00",
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
        "reviewed_payload_hash_algorithm": "sha256",
        "reviewed_payload_preview_non_runtime": True,
        "operator_payload_review_decision": "approve_payload_hash_for_next_local_gate_only",
        "discord_operator_payload_review_gate_available": True,
        "discord_operator_payload_review_gate_declared_ready": True,
        "eligible_for_discord_request_policy_gate": True,
        "live_dispatch_approval_granted": False,
        "publication_approval_granted": False,
        "request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "next_local_gate_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "permission_verification_later_required": True,
        "request_budget_later_required": True,
        "timeout_policy_later_required": True,
        "retry_policy_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "substack_manual_fallback_required": True,
        "all_platforms_endpoint_mapping_ready": False,
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
        "discord_request_policy_declaration_id": "discord_request_policy_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T05:10:00+07:00",
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
        "request_policy_mode": "operator_declared_discord_request_policy_gate_only_not_request",
        "reviewed_payload_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "request_budget_policy": "single_supervised_request_later",
        "max_request_count": 1,
        "timeout_policy": "bounded_timeout_required_later",
        "timeout_seconds": 15,
        "retry_policy": "no_hidden_retry",
        "max_retries": 0,
        "hidden_retry_allowed": False,
        "kill_switch_required": True,
        "audit_redaction_required": True,
        "manual_fallback_required": True,
        "idempotency_required_later": True,
        "payload_hash_revalidation_required": True,
        "permission_verification_required": True,
        "live_dispatch_approval_granted": False,
        "publication_approval_granted": False,
        "request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "endpoint_url_value_allowed": False,
        "channel_identity_value_allowed": False,
        "operator_request_policy_decision": "approve_request_policy_for_next_local_gate_only",
        "next_local_gate_later_required": True,
        "declaration_decision": "mark_discord_request_policy_gate_ready",
        "approval_phrase": "MARK_DISCORD_REQUEST_POLICY_GATE_READY_ONLY_NOT_REQUEST",
        "approval_scope": "discord_request_policy_gate_only",
        "notes": "Verified Discord request policy gate."
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
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), _declaration())
    assert packet.discord_request_policy_gate_available is True
    assert packet.discord_request_policy_gate_declared_ready is True
    assert packet.eligible_for_discord_supervised_request_package_staging_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_reviewed_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["reviewed_payload_hash"] = "wrong"
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False
    assert "declaration_reviewed_payload_hash_mismatch" in packet.blockers


def test_max_request_count_not_1_fails_closed():
    decl = _declaration()
    decl["max_request_count"] = 2
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False
    assert "declaration_max_request_count_invalid" in packet.blockers


def test_timeout_seconds_out_of_bounds_fails_closed():
    for val in [4, 31, "15", True]:
        decl = _declaration()
        decl["timeout_seconds"] = val
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_max_retries_not_0_or_hidden_retry_true_fails_closed():
    for k, v in [("max_retries", 1), ("hidden_retry_allowed", True)]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_approvals_granted_true_fails_closed():
    for f in ["live_dispatch_approval_granted", "publication_approval_granted"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_request_artifact_creation_allowed_true_fails_closed():
    decl = _declaration()
    decl["request_artifact_creation_allowed"] = True
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False


def test_webhook_api_send_endpoint_flags_true_fail_closed():
    for f in [
        "webhook_value_read_allowed", "discord_api_call_allowed",
        "webhook_send_test_allowed", "endpoint_url_value_allowed", "channel_identity_value_allowed"
    ]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_wrong_preflight_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_request_policy_gate_packet(preflight, _declaration())
    assert packet.discord_request_policy_gate_available is False


def test_preflight_unavailable_or_not_ready_fails_closed():
    for f in ["discord_operator_payload_review_gate_available", "discord_operator_payload_review_gate_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_request_policy_gate_packet(preflight, _declaration())
        assert packet.discord_request_policy_gate_available is False


def test_operator_request_policy_decision_reject_or_defer_fails_closed():
    for dec in ["reject", "defer"]:
        decl = _declaration()
        decl["operator_request_policy_decision"] = dec
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False


def test_request_policy_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["request_policy_mode"] = "wrong"
    packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
    assert packet.discord_request_policy_gate_available is False


def test_required_policy_boolean_false_fails_closed():
    for f in [
        "kill_switch_required", "audit_redaction_required", "manual_fallback_required",
        "idempotency_required_later", "payload_hash_revalidation_required", "permission_verification_required",
        "next_local_gate_later_required"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_declaration_forbidden_content_fails_closed():
    for text in ["my webhook_url is this", "please buy this equity", "fake_url detected"]:
        decl = _declaration()
        decl["notes"] = text
        packet = make_discord_request_policy_gate_packet(_preflight_packet(), decl)
        assert packet.discord_request_policy_gate_available is False


def test_secret_marker_in_inputs_fails_closed_without_hash_persistence():
    preflight = _preflight_packet()
    preflight["discord_operator_payload_review_gate_id"] = "private_key = my_secret"
    packet = make_discord_request_policy_gate_packet(preflight, _declaration())
    assert packet.discord_request_policy_gate_available is False
    assert packet.reviewed_payload_hash == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_request_policy_gate_v6.py").read_text(encoding="utf-8")
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

    output_file = tmp_path / "request_policy_packet.json"
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
    assert first["discord_request_policy_gate_id"] == second["discord_request_policy_gate_id"]
    assert first["discord_request_policy_gate_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_REQUEST_POLICY_GATE_FROM_OPERATOR_PAYLOAD_REVIEW")
    paths = [
        Path("live_contentops/discord_request_policy_gate_v6.py"),
        Path("tests/test_discord_request_policy_gate_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_request_policy_gate_packet.json").read_text(encoding="utf-8"))
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
    assert written["discord_request_policy_gate_available"] is False
    assert written["discord_request_policy_gate_declared_ready"] is False
    assert written["eligible_for_discord_supervised_request_package_staging_gate"] is False
