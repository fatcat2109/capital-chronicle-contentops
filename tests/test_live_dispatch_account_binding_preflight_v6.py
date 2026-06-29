import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.live_dispatch_account_binding_preflight_v6 import (
    make_account_binding_preflight_packet,
    main,
    _canonical_json,
)


def _preflight():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LIVE_DISPATCH_CREDENTIAL_AND_ALLOWLIST_PREFLIGHT_FROM_SCOPE_V0",
        "credential_allowlist_preflight_id": "credential_allowlist_preflight_abc123",
        "endpoint_allowlist_declaration_id": "endpoint_allowlist_decl_abc123",
        "live_dispatch_scope_preflight_id": "scope_preflight_abc123",
        "live_dispatch_scope_preflight_sha256": "scope_sha256_abc123",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "live_dispatch_readiness_preflight_sha256": "readiness_sha256_abc123",
        "official_docs_declaration_id": "docs_decl_abc123",
        "live_scope_declaration_id": "scope_decl_abc123",
        "local_dispatch_execution_payload_manifest_id": "exec_payload_manifest_abc123",
        "operator_supervised_dispatch_review_decision_packet_id": "supervised_decision_abc123",
        "local_destination_binding_preflight_id": "dest_preflight_abc123",
        "destination_binding_id": "dest_binding_abc123",
        "local_dispatch_payload_manifest_id": "payload_manifest_abc123",
        "operator_dispatch_review_decision_packet_id": "op_decision_abc123",
        "local_dispatch_preflight_id": "local_preflight_abc123",
        "local_active_outbox_manifest_id": "outbox_manifest_abc123",
        "operator_active_outbox_review_decision_id": "active_outbox_review_abc123",
        "active_outbox_eligibility_id": "eligibility_abc123",
        "outbox_package_staging_id": "staging_abc123",
        "payload_review_ledger_id": "ledger_abc123",
        "approval_intent_id": "approval_intent_abc123",
        "variant_preview_staging_id": "preview_staging_abc123",
        "metadata_values_review_id": "meta_review_abc123",
        "metadata_values_id": "meta_values_abc123",
        "metadata_proposal_id": "meta_proposal_abc123",
        "source_pack_intake_id": "source_intake_abc123",
        "source_pack_id": "source_pack_abc123",
        "editorial_workflow_id": "workflow_abc123",
        "canonical_slug": "sample-title",
        "canonical_title": "Sample Title",
        "execution_preparation_json_files": ["f1.json", "f2.json"],
        "execution_preparation_json_hashes": {"f1.json": "h1", "f2.json": "h2"},
        "execution_preparation_markdown_files": ["f1.md", "f2.md"],
        "execution_preparation_markdown_hashes": {"f1.md": "m1", "f2.md": "m2"},
        "destinations": [
            {
                "platform": "substack",
                "destination_label": "Production Substack",
                "destination_type": "draft_console_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            },
            {
                "platform": "discord",
                "destination_label": "Announcements Channel",
                "destination_type": "webhook_family_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            }
        ],
        "platforms": ["substack", "discord"],
        "credential_key_names_only": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "credential_presence_mode": "checked_declared_key_names_only",
        "credential_presence_complete": True,
        "credential_presence_rows": [
            {
                "key_name": "SUBSTACK_API_KEY_DRAFT_STAGE",
                "present": True,
                "checked_by_exact_declared_key_name": True,
                "value_observed": False,
                "value_length_observed": False,
                "value_hash_observed": False,
                "value_prefix_observed": False,
                "value_suffix_observed": False
            },
            {
                "key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
                "present": True,
                "checked_by_exact_declared_key_name": True,
                "value_observed": False,
                "value_length_observed": False,
                "value_hash_observed": False,
                "value_prefix_observed": False,
                "value_suffix_observed": False
            }
        ],
        "endpoint_allowlist_rows": [
            {
                "platform": "substack",
                "action_family": "future_supervised_live_dispatch",
                "host_label": "substack_operator_declared_host_label",
                "path_label": "substack_operator_declared_path_label",
                "method_label": "post_method_label_only",
                "endpoint_allowlist_kind": "label_only_no_endpoint_value",
                "request_budget": 2,
                "timeout_policy_label": "fast_ship_timeout_policy",
                "retry_policy_label": "no_hidden_retry",
                "audit_redaction_required": True,
                "manual_fallback_required": True,
                "operator_notes": "Reviewed host labels."
            },
            {
                "platform": "discord",
                "action_family": "future_supervised_live_dispatch",
                "host_label": "discord_operator_declared_webhook_host_label",
                "path_label": "discord_operator_declared_path_label",
                "method_label": "webhook_method_label_only",
                "endpoint_allowlist_kind": "label_only_no_endpoint_value",
                "request_budget": 1,
                "timeout_policy_label": "fast_ship_timeout_policy",
                "retry_policy_label": "no_hidden_retry",
                "audit_redaction_required": True,
                "manual_fallback_required": True,
                "operator_notes": "Reviewed Discord path labels."
            }
        ],
        "live_write_request_budget_confirmed": 2,
        "timeout_policy_confirmed": "fast_ship_timeout_policy",
        "retry_policy_confirmed": "no_hidden_retry",
        "audit_redaction_confirmed": True,
        "combined_payload_hash": "combined_sha256_xyz",
        "credential_allowlist_preflight_available": True,
        "endpoint_allowlist_declared_ready": True,
        "eligible_for_supervised_live_dispatch_request_gate": True,
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
        "warnings": []
    }


def _binding():
    return {
        "schema_version": "6.0.0",
        "account_binding_declaration_id": "binding_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:20:00+07:00",
        "credential_allowlist_preflight_id": "credential_allowlist_preflight_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "account_binding_mode": "operator_declared_account_binding_labels_only_not_verified",
        "platform_binding_rows": [
            {
                "platform": "substack",
                "destination_label": "Production Substack",
                "account_label": "cc_newsletter_staff",
                "permission_label": "staff_member_access",
                "binding_kind": "non_secret_label_only_not_verified",
                "credential_key_name": "SUBSTACK_API_KEY_DRAFT_STAGE",
                "endpoint_host_label": "substack_operator_declared_host_label",
                "endpoint_path_label": "substack_operator_declared_path_label",
                "method_label": "post_method_label_only",
                "operator_confirmed_destination": True,
                "operator_confirmed_account_context": True,
                "operator_notes": "Confirmed Substack access."
            },
            {
                "platform": "discord",
                "destination_label": "Announcements Channel",
                "account_label": "cc_announcements_channel_webhook",
                "permission_label": "staff_webhook_send_access",
                "binding_kind": "non_secret_label_only_not_verified",
                "credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
                "endpoint_host_label": "discord_operator_declared_webhook_host_label",
                "endpoint_path_label": "discord_operator_declared_path_label",
                "method_label": "webhook_method_label_only",
                "operator_confirmed_destination": True,
                "operator_confirmed_account_context": True,
                "operator_notes": "Confirmed Discord webhook access."
            }
        ],
        "account_identity_later_required": True,
        "permission_check_later_required": True,
        "destination_binding_confirmed": True,
        "credential_key_names_only_reviewed": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "endpoint_allowlist_rows_reviewed": [
            {
                "platform": "substack",
                "action_family": "future_supervised_live_dispatch",
                "host_label": "substack_operator_declared_host_label",
                "path_label": "substack_operator_declared_path_label",
                "method_label": "post_method_label_only",
                "endpoint_allowlist_kind": "label_only_no_endpoint_value",
                "request_budget": 2,
                "timeout_policy_label": "fast_ship_timeout_policy",
                "retry_policy_label": "no_hidden_retry",
                "audit_redaction_required": True,
                "manual_fallback_required": True,
                "operator_notes": "Reviewed host labels."
            },
            {
                "platform": "discord",
                "action_family": "future_supervised_live_dispatch",
                "host_label": "discord_operator_declared_webhook_host_label",
                "path_label": "discord_operator_declared_path_label",
                "method_label": "webhook_method_label_only",
                "endpoint_allowlist_kind": "label_only_no_endpoint_value",
                "request_budget": 1,
                "timeout_policy_label": "fast_ship_timeout_policy",
                "retry_policy_label": "no_hidden_retry",
                "audit_redaction_required": True,
                "manual_fallback_required": True,
                "operator_notes": "Reviewed Discord path labels."
            }
        ],
        "live_write_request_budget_confirmed": 2,
        "timeout_policy_confirmed": "fast_ship_timeout_policy",
        "retry_policy_confirmed": "no_hidden_retry",
        "audit_redaction_confirmed": True,
        "declaration_decision": "mark_account_binding_ready_for_future_live_request_gate",
        "approval_phrase": "MARK_ACCOUNT_BINDING_READY_FOR_FUTURE_LIVE_REQUEST_GATE_ONLY_NOT_SEND",
        "approval_scope": "account_binding_preflight_only",
        "notes": "Verified account binding parameters."
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
    packet = make_account_binding_preflight_packet(_preflight(), _binding())
    assert packet.account_binding_preflight_available is True
    assert packet.account_binding_declared_ready is True
    assert packet.eligible_for_live_dispatch_request_package_gate is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_wrong_preflight_task_label_fails_closed():
    pref = _preflight()
    pref["task_label"] = "wrong"
    packet = make_account_binding_preflight_packet(pref, _binding())
    assert packet.account_binding_preflight_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_preflight_unavailable_or_not_ready_or_not_eligible_fails_closed():
    for f in [
        "credential_allowlist_preflight_available",
        "endpoint_allowlist_declared_ready",
        "eligible_for_supervised_live_dispatch_request_gate"
    ]:
        pref = _preflight()
        pref[f] = False
        packet = make_account_binding_preflight_packet(pref, _binding())
        assert packet.account_binding_preflight_available is False
        assert f"preflight_field_{f}_invalid" in packet.blockers


def test_binding_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _binding()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_account_binding_preflight_packet(_preflight(), decl)
        assert packet.account_binding_preflight_available is False
        assert f"binding_declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    decl = _binding()
    decl.pop("notes", None)
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_notes_missing_or_invalid" in packet.blockers


def test_platform_binding_rows_validations():
    # 1. Platform invalid order/count
    decl = _binding()
    decl["platform_binding_rows"] = []
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_rows_count_invalid" in packet.blockers

    # 2. Labels containing URL or domain
    decl = _binding()
    decl["platform_binding_rows"][0]["account_label"] = "https://staff.com"
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_row_index_0_account_label_contains_url_or_domain" in packet.blockers

    # 3. Label containing hex ID-like term
    decl = _binding()
    decl["platform_binding_rows"][0]["account_label"] = "staff_abcdef12345"
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_row_index_0_account_label_contains_hex_id" in packet.blockers

    # 4. Credential key name mismatch
    decl = _binding()
    decl["platform_binding_rows"][0]["credential_key_name"] = "DISCORD_KEY"
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_row_index_0_credential_key_name_mismatch" in packet.blockers

    # 5. Endpoint host label mismatch
    decl = _binding()
    decl["platform_binding_rows"][0]["endpoint_host_label"] = "wrong_host"
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_row_index_0_endpoint_host_label_mismatch" in packet.blockers


def test_operator_confirmation_destination_or_context_false_fails_closed():
    for field_name in ["operator_confirmed_destination", "operator_confirmed_account_context"]:
        decl = _binding()
        decl["platform_binding_rows"][0][field_name] = False
        packet = make_account_binding_preflight_packet(_preflight(), decl)
        assert packet.account_binding_preflight_available is False
        assert f"binding_row_index_0_{field_name}_not_true" in packet.blockers


def test_credential_key_names_only_reviewed_mismatch():
    decl = _binding()
    decl["credential_key_names_only_reviewed"] = ["DIFFERENT_KEY"]
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_credential_key_names_only_reviewed_mismatch" in packet.blockers


def test_endpoint_allowlist_rows_reviewed_mismatch():
    decl = _binding()
    decl["endpoint_allowlist_rows_reviewed"][0]["request_budget"] = 99
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_endpoint_allowlist_rows_reviewed_mismatch" in packet.blockers


def test_budget_timeout_retry_audit_mismatch_fails_closed():
    decl = _binding()
    decl["timeout_policy_confirmed"] = "mismatch_policy"
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_timeout_policy_confirmed_mismatch" in packet.blockers


def test_forbidden_live_claims_safety_gate():
    decl = _binding()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_account_binding_preflight_packet(_preflight(), decl)
    assert packet.account_binding_preflight_available is False
    assert "binding_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    pref = _preflight()
    pref["canonical_slug"] = "private_key = my_secret"
    packet = make_account_binding_preflight_packet(pref, _binding())
    assert packet.account_binding_preflight_available is False
    assert packet.credential_allowlist_preflight_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/live_dispatch_account_binding_preflight_v6.py").read_text(encoding="utf-8")
    forbidden = [
        r"\bos\.environ\b",
        r"\bos\.getenv\b",
        r"\bgetenv\b",
        r"\bimport\s+dotenv\b",
        r"\bload_dotenv\b",
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bimport\s+httpx\b",
    ]
    for pat in forbidden:
        assert not re.search(pat, source)


def test_cli_writes_deterministic_packet(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text(json.dumps(_preflight()), encoding="utf-8")

    b_path = tmp_path / "binding.json"
    b_path.write_text(json.dumps(_binding()), encoding="utf-8")

    output_file = tmp_path / "account_binding_preflight.json"
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
    assert first["account_binding_preflight_id"] == second["account_binding_preflight_id"]
    assert first["account_binding_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST")
    paths = [
        Path("live_contentops/live_dispatch_account_binding_preflight_v6.py"),
        Path("tests/test_live_dispatch_account_binding_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_live_dispatch_account_binding_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_binding_preflight.json"
    exit_code = main([
        str(p_path),
        "A:/binding.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["account_binding_preflight_available"] is False
    assert written["account_binding_declared_ready"] is False
    assert written["eligible_for_live_dispatch_request_package_gate"] is False
