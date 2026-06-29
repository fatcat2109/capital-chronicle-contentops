import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_webhook_value_binding_preflight_v6 import (
    make_discord_webhook_value_binding_preflight_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_ENDPOINT_MAPPING_PREFLIGHT_FROM_CAPABILITY_LANE_SPLIT_V0",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "discord_endpoint_mapping_declaration_id": "discord_endpoint_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T03:30:00+07:00",
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
        "endpoint_family": "discord_execute_webhook_label_only",
        "endpoint_host_label": "discord_operator_declared_webhook_host_label",
        "endpoint_path_label": "discord_operator_declared_webhook_path_label",
        "endpoint_method_label": "webhook_method_label_only",
        "endpoint_mapping_label_only": True,
        "webhook_url_value_later_required": True,
        "webhook_token_later_required": True,
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
        "discord_endpoint_mapping_preflight_available": True,
        "discord_endpoint_mapping_preflight_declared_ready": True,
        "eligible_for_discord_webhook_value_binding_gate": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
        "live_send_request_created": False,
        "approval_for_live_dispatch": False,
        "approval_for_publication": False,
        "generated_citations_allowed": False,
        "citations_verified": False,
        "approved_canonical_article_available": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
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
        "discord_webhook_value_binding_declaration_id": "discord_webhook_value_binding_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T04:00:00+07:00",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "binding_mode": "operator_declared_discord_webhook_value_binding_presence_only_not_value",
        "platform": "discord",
        "credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "credential_kind": "discord_webhook_url_secret_value_later",
        "webhook_value_source": "process_env_exact_key_membership_only",
        "webhook_value_read_allowed": False,
        "webhook_value_persist_allowed": False,
        "webhook_value_hash_allowed": False,
        "webhook_value_length_allowed": False,
        "webhook_value_prefix_suffix_allowed": False,
        "webhook_url_shape_validation_allowed": False,
        "discord_api_validation_allowed": False,
        "webhook_send_test_allowed": False,
        "channel_identity_later_required": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "request_budget_later_required": True,
        "timeout_policy_later_required": True,
        "retry_policy_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "declaration_decision": "mark_discord_webhook_value_binding_preflight_ready",
        "approval_phrase": "MARK_DISCORD_WEBHOOK_VALUE_BINDING_PREFLIGHT_READY_ONLY_NOT_SEND",
        "approval_scope": "discord_webhook_value_binding_preflight_only",
        "notes": "Verified Discord webhook value presence binding."
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


def test_valid_inputs_no_env_check_emits_deferred_packet():
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), _declaration(), check_env=False)
    assert packet.discord_webhook_value_binding_preflight_available is True
    assert packet.discord_webhook_value_binding_preflight_declared_ready is True
    assert packet.eligible_for_discord_permission_probe_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.credential_presence_checked is False
    assert packet.credential_present is False
    assert packet.credential_presence_mode == "not_checked"
    assert "discord_credential_presence_deferred" in packet.warnings
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_output_contains_no_secrets_or_observed_values():
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), _declaration(), check_env=False)
    assert packet.webhook_value_observed is False
    assert packet.webhook_value_persisted is False
    assert packet.webhook_value_hash_observed is False
    assert packet.webhook_value_length_observed is False
    assert packet.webhook_value_prefix_suffix_observed is False
    assert packet.webhook_url_shape_validated is False
    assert packet.discord_api_validated is False
    assert packet.webhook_send_test_performed is False


class SentinelEnvMapping:
    def __init__(self, allowed_keys):
        self.allowed_keys = set(allowed_keys)

    def __contains__(self, key):
        return key in self.allowed_keys

    def get(self, *args, **kwargs):
        raise AssertionError("get called")

    def __getitem__(self, key):
        raise AssertionError("__getitem__ called")

    def items(self, *args, **kwargs):
        raise AssertionError("items called")

    def values(self, *args, **kwargs):
        raise AssertionError("values called")

    def keys(self, *args, **kwargs):
        raise AssertionError("keys called")

    def __iter__(self):
        raise AssertionError("__iter__ called")


def test_valid_inputs_with_env_check_succeeds_using_sentinel():
    sentinel = SentinelEnvMapping(["DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"])
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), _declaration(), check_env=True, env_mapping=sentinel)
    assert packet.discord_webhook_value_binding_preflight_available is True
    assert packet.discord_webhook_value_binding_preflight_declared_ready is True
    assert packet.credential_presence_checked is True
    assert packet.credential_present is True
    assert packet.credential_presence_mode == "process_env_exact_key_membership_only"
    assert packet.eligible_for_discord_permission_probe_gate is True
    assert not packet.blockers


def test_env_check_missing_key_fails_probe_gate():
    sentinel = SentinelEnvMapping([])
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), _declaration(), check_env=True, env_mapping=sentinel)
    assert packet.discord_webhook_value_binding_preflight_available is True
    assert packet.discord_webhook_value_binding_preflight_declared_ready is False
    assert packet.credential_presence_checked is True
    assert packet.credential_present is False
    assert packet.eligible_for_discord_permission_probe_gate is False
    assert "discord_credential_presence_missing" in packet.blockers


def test_wrong_endpoint_mapping_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_webhook_value_binding_preflight_packet(preflight, _declaration())
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_preflight_not_available_or_not_declared_ready_fails_closed():
    for f in ["discord_endpoint_mapping_preflight_available", "discord_endpoint_mapping_preflight_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_webhook_value_binding_preflight_packet(preflight, _declaration())
        assert packet.discord_webhook_value_binding_preflight_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
        assert packet.discord_webhook_value_binding_preflight_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert "declaration_platform_invalid" in packet.blockers


def test_credential_key_name_mismatch_fails_closed():
    decl = _declaration()
    decl["credential_key_name"] = "wrong"
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False


def test_credential_kind_mismatch_fails_closed():
    decl = _declaration()
    decl["credential_kind"] = "wrong"
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False


def test_binding_mode_mismatch_fails_closed():
    decl = _declaration()
    decl["binding_mode"] = "wrong"
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False


def test_value_flags_true_fails_closed():
    for f in ["webhook_value_read_allowed", "webhook_send_test_allowed"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
        assert packet.discord_webhook_value_binding_preflight_available is False


def test_later_required_boolean_false_fails_closed():
    decl = _declaration()
    decl["channel_identity_later_required"] = False
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False


def test_declaration_safety_check_detects_forbidden_claims():
    decl = _declaration()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_discord_webhook_value_binding_preflight_packet(_preflight_packet(), decl)
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert "declaration_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    preflight = _preflight_packet()
    preflight["discord_endpoint_mapping_preflight_id"] = "private_key = my_secret"
    packet = make_discord_webhook_value_binding_preflight_packet(preflight, _declaration())
    assert packet.discord_webhook_value_binding_preflight_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/discord_webhook_value_binding_preflight_v6.py").read_text(encoding="utf-8")
    forbidden = [
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


def test_source_process_env_usage_only():
    source = Path("live_contentops/discord_webhook_value_binding_preflight_v6.py").read_text(encoding="utf-8")
    # Verify that os.environ or environ is checked only with 'in' and not get/keys/dict(os.environ)/etc.
    match = re.search(r"if check_env:.*?(?=prepared =)", source, re.DOTALL)
    assert match is not None
    presence_section = match.group(0)
    assert ".get(" not in presence_section
    assert "__getitem__" not in presence_section
    assert ".items(" not in presence_section
    assert ".values(" not in presence_section
    assert ".keys(" not in presence_section
    assert "dict(os.environ)" not in source


def test_cli_writes_deterministic_packet(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text(json.dumps(_preflight_packet()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    output_file = tmp_path / "binding_preflight_packet.json"
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
    assert first["discord_webhook_value_binding_preflight_id"] == second["discord_webhook_value_binding_preflight_id"]
    assert first["discord_webhook_value_binding_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_WEBHOOK_VALUE_BINDING_PREFLIGHT_FROM_ENDPOINT_MAPPING")
    paths = [
        Path("live_contentops/discord_webhook_value_binding_preflight_v6.py"),
        Path("tests/test_discord_webhook_value_binding_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_webhook_value_binding_preflight_packet.json").read_text(encoding="utf-8"))
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
    assert written["discord_webhook_value_binding_preflight_available"] is False
    assert written["discord_webhook_value_binding_preflight_declared_ready"] is False
    assert written["eligible_for_discord_permission_probe_gate"] is False
