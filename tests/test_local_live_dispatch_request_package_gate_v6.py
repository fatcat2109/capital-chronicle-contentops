import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_live_dispatch_request_package_gate_v6 import (
    make_dispatch_request_package_gate_packet,
    main,
    _canonical_json,
)


def _preflight():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST_V0",
        "account_binding_preflight_id": "account_binding_preflight_abc123",
        "account_binding_declaration_id": "binding_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:20:00+07:00",
        "credential_allowlist_preflight_id": "credential_allowlist_preflight_abc123",
        "credential_allowlist_preflight_sha256": "preflight_sha256_abc123",
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
        "live_write_request_budget_confirmed": 2,
        "timeout_policy_confirmed": "fast_ship_timeout_policy",
        "retry_policy_confirmed": "no_hidden_retry",
        "audit_redaction_confirmed": True,
        "combined_payload_hash": "combined_sha256_xyz",
        "account_binding_preflight_available": True,
        "account_binding_declared_ready": True,
        "eligible_for_live_dispatch_request_package_gate": True,
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


def _declaration():
    return {
        "schema_version": "6.0.0",
        "dispatch_request_gate_declaration_id": "dispatch_request_gate_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:30:00+07:00",
        "account_binding_preflight_id": "account_binding_preflight_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "dispatch_request_gate_mode": "operator_declared_dispatch_request_package_gate_only_not_send",
        "requested_platforms": ["substack", "discord"],
        "payload_hash_confirmed": "combined_sha256_xyz",
        "request_budget_confirmed": 2,
        "timeout_policy_confirmed": "fast_ship_timeout_policy",
        "retry_policy_confirmed": "no_hidden_retry",
        "kill_switch_confirmed": True,
        "audit_redaction_confirmed": True,
        "manual_fallback_confirmed": True,
        "account_binding_confirmed": True,
        "permission_check_later_required": True,
        "provider_execution_later_required": True,
        "operator_final_review_later_required": True,
        "declaration_decision": "mark_dispatch_request_package_gate_ready",
        "approval_phrase": "MARK_DISPATCH_REQUEST_PACKAGE_GATE_READY_ONLY_NOT_SEND",
        "approval_scope": "dispatch_request_package_gate_only",
        "notes": "Verified dispatch request gate."
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
    packet = make_dispatch_request_package_gate_packet(_preflight(), _declaration())
    assert packet.dispatch_request_package_gate_available is True
    assert packet.dispatch_request_package_gate_declared_ready is True
    assert packet.eligible_for_future_supervised_dispatch_request_package is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_wrong_preflight_task_label_fails_closed():
    pref = _preflight()
    pref["task_label"] = "wrong"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_preflight_unavailable_or_not_ready_or_not_eligible_fails_closed():
    for f in [
        "account_binding_preflight_available",
        "account_binding_declared_ready",
        "eligible_for_live_dispatch_request_package_gate"
    ]:
        pref = _preflight()
        pref[f] = False
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert f"preflight_field_{f}_invalid" in packet.blockers


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
        assert packet.dispatch_request_package_gate_available is False
        assert f"declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_extra_declaration_field_fails_closed():
    decl = _declaration()
    decl["extra_unsupported_field"] = "value"
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_extra_field_extra_unsupported_field_detected" in packet.blockers


def test_requested_platforms_invalid_fails_closed():
    decl = _declaration()
    decl["requested_platforms"] = ["substack"]
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_requested_platforms_invalid" in packet.blockers


def test_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["payload_hash_confirmed"] = "different_hash"
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_payload_hash_confirmed_mismatch" in packet.blockers


def test_budget_timeout_retry_mismatch_fails_closed():
    decl = _declaration()
    decl["request_budget_confirmed"] = 999
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_request_budget_confirmed_mismatch" in packet.blockers


def test_confirmation_fields_false_fails_closed():
    for f in [
        "kill_switch_confirmed",
        "audit_redaction_confirmed",
        "manual_fallback_confirmed",
        "account_binding_confirmed",
        "permission_check_later_required",
        "provider_execution_later_required",
        "operator_final_review_later_required"
    ]:
        decl = _declaration()
        decl[f] = False
        packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
        assert packet.dispatch_request_package_gate_available is False
        assert f"declaration_field_{f}_not_true" in packet.blockers


def test_safety_check_detects_forbidden_live_claims():
    decl = _declaration()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_dispatch_request_package_gate_packet(_preflight(), decl)
    assert packet.dispatch_request_package_gate_available is False
    assert "declaration_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    pref = _preflight()
    pref["canonical_slug"] = "private_key = my_secret"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert packet.account_binding_preflight_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/local_live_dispatch_request_package_gate_v6.py").read_text(encoding="utf-8")
    forbidden = [
        r"\bos\.environ\b",
        r"\bos\.getenv\b",
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
    p_path.write_text(json.dumps(_preflight()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    output_file = tmp_path / "request_package_gate.json"
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
    assert first["dispatch_request_package_gate_id"] == second["dispatch_request_package_gate_id"]
    assert first["dispatch_request_package_gate_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_LIVE_DISPATCH_REQUEST_PACKAGE_GATE_FROM_ACCOUNT_BINDING")
    paths = [
        Path("live_contentops/local_live_dispatch_request_package_gate_v6.py"),
        Path("tests/test_local_live_dispatch_request_package_gate_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_local_live_dispatch_request_package_gate_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_gate_packet.json"
    exit_code = main([
        str(p_path),
        "A:/declaration.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["dispatch_request_package_gate_available"] is False
    assert written["dispatch_request_package_gate_declared_ready"] is False
    assert written["eligible_for_future_supervised_dispatch_request_package"] is False


def test_endpoint_allowlist_rows_extra_fields_fail_closed():
    for field_name in ["webhook_url", "endpoint_path", "request_payload"]:
        pref = _preflight()
        pref["endpoint_allowlist_rows"][0][field_name] = "value"
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert f"preflight_endpoint_allowlist_row_0_extra_field_{field_name}_detected" in packet.blockers


def test_endpoint_allowlist_rows_host_label_invalid_fails_closed():
    for bad in ["http://domain.com", "domain.com", "host/path"]:
        pref = _preflight()
        pref["endpoint_allowlist_rows"][0]["host_label"] = bad
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert "preflight_endpoint_allowlist_row_0_host_label_contains_url_or_domain" in packet.blockers


def test_endpoint_allowlist_rows_path_label_invalid_fails_closed():
    pref = _preflight()
    pref["endpoint_allowlist_rows"][0]["path_label"] = "/start-with-slash"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_endpoint_allowlist_row_0_path_label_starts_with_slash" in packet.blockers

    for term in ["api", "webhook", "token", "account", "channel", "workspace", "app"]:
        pref = _preflight()
        pref["endpoint_allowlist_rows"][0]["path_label"] = f"safe_{term}_label"
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert "preflight_endpoint_allowlist_row_0_path_label_contains_restricted_terms" in packet.blockers or "preflight_endpoint_allowlist_row_0_path_label_contains_url_or_domain" in packet.blockers


def test_endpoint_allowlist_rows_request_budget_exceeds_fails_closed():
    pref = _preflight()
    pref["endpoint_allowlist_rows"][0]["request_budget"] = 999
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_endpoint_allowlist_row_0_request_budget_invalid" in packet.blockers


def test_endpoint_allowlist_rows_policy_mismatches_fail_closed():
    pref = _preflight()
    pref["endpoint_allowlist_rows"][0]["timeout_policy_label"] = "wrong_timeout"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_endpoint_allowlist_row_0_timeout_policy_mismatch" in packet.blockers


def test_platform_binding_rows_extra_fields_fail_closed():
    for field_name in ["account_id", "channel_id", "live_send_instruction"]:
        pref = _preflight()
        pref["platform_binding_rows"][0][field_name] = "value"
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert f"preflight_platform_binding_row_0_extra_field_{field_name}_detected" in packet.blockers


def test_platform_binding_rows_labels_invalid_fail_closed():
    # URL/domain
    pref = _preflight()
    pref["platform_binding_rows"][0]["account_label"] = "domain.com"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_platform_binding_row_0_account_label_contains_url_or_domain" in packet.blockers

    # hex ID
    pref = _preflight()
    pref["platform_binding_rows"][0]["account_label"] = "account_abcdef12345"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_platform_binding_row_0_account_label_contains_hex_id" in packet.blockers


def test_platform_binding_rows_endpoint_mismatch_fails_closed():
    pref = _preflight()
    pref["platform_binding_rows"][0]["endpoint_host_label"] = "wrong_host"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_platform_binding_row_0_endpoint_host_label_mismatch" in packet.blockers


def test_platform_binding_rows_credential_mismatch_fails_closed():
    pref = _preflight()
    pref["platform_binding_rows"][0]["credential_key_name"] = "DISCORD_KEY"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_platform_binding_row_0_credential_key_name_mismatch" in packet.blockers


def test_destinations_extra_fields_fail_closed():
    for field_name in ["channel_id", "account_id", "webhook_url"]:
        pref = _preflight()
        pref["destinations"][0][field_name] = "value"
        packet = make_dispatch_request_package_gate_packet(pref, _declaration())
        assert packet.dispatch_request_package_gate_available is False
        assert f"preflight_destination_row_0_extra_field_{field_name}_detected" in packet.blockers


def test_destinations_labels_invalid_fail_closed():
    # URL/domain
    pref = _preflight()
    pref["destinations"][0]["destination_label"] = "http://bad.com"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_destination_row_0_destination_label_contains_url_or_domain" in packet.blockers

    # hex ID
    pref = _preflight()
    pref["destinations"][0]["destination_label"] = "dest_abcdef12345"
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_destination_row_0_destination_label_contains_hex_id" in packet.blockers


def test_destinations_manual_confirmed_false_fails_closed():
    pref = _preflight()
    pref["destinations"][0]["manual_operator_confirmed"] = False
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_destination_row_0_manual_operator_confirmed_not_true" in packet.blockers


def test_inherited_row_secret_marker_blocks_sha():
    pref = _preflight()
    pref["endpoint_allowlist_rows"][0]["operator_notes"] = "Accessing private_key term."
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_endpoint_allowlist_row_0_secret_marker_detected" in packet.blockers
    assert packet.account_binding_preflight_sha256 == ""


def test_inherited_row_forbidden_live_claim_fails_closed():
    pref = _preflight()
    pref["endpoint_allowlist_rows"][0]["operator_notes"] = "This is a live_dispatch claim."
    packet = make_dispatch_request_package_gate_packet(pref, _declaration())
    assert packet.dispatch_request_package_gate_available is False
    assert "preflight_endpoint_allowlist_row_0_forbidden_live_claim_detected_live_dispatch" in packet.blockers

