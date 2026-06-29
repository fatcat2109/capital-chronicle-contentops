import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.official_platform_docs_verification_v6 import (
    make_official_platform_docs_verification_packet,
    main,
    _canonical_json,
)


def _request_gate():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_LIVE_DISPATCH_REQUEST_PACKAGE_GATE_FROM_ACCOUNT_BINDING_V0",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "dispatch_request_gate_declaration_id": "decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:30:00+07:00",
        "account_binding_preflight_id": "account_binding_preflight_abc123",
        "account_binding_preflight_sha256": "preflight_sha256_abc123",
        "account_binding_declaration_id": "binding_decl_abc123",
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
        "requested_platforms": ["substack", "discord"],
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
        "combined_payload_hash": "combined_sha256_xyz",
        "dispatch_request_package_gate_available": True,
        "dispatch_request_package_gate_declared_ready": True,
        "eligible_for_future_supervised_dispatch_request_package": True,
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


def _source_summary():
    return {
        "schema_version": "6.0.0",
        "official_docs_source_summary_id": "source_summary_abc123",
        "created_at_manual": "2026-06-30T02:00:00+07:00",
        "reviewer_id": "jim",
        "docs_review_scope": "live_dispatch_v6_evaluation",
        "platform_rows": [
            {
                "platform": "substack",
                "source_family": "official_platform_documentation",
                "official_source_type": "api_documentation_page",
                "official_source_title": "Substack Publishing API Specs",
                "official_source_url_label": "https://substack.com/help/api",
                "official_source_accessed_at_manual": "2026-06-30T02:00:00+07:00",
                "dispatch_capability_classification": "official_api_supported_for_required_action",
                "supported_dispatch_mechanism": "api_post_draft",
                "auth_or_permission_requirements_summary": "requires_token_header",
                "endpoint_or_surface_summary": "post_endpoint",
                "rate_limit_or_budget_summary": "100_per_hour",
                "media_payload_constraints_summary": "markdown_text_only",
                "error_handling_summary": "json_error_responses",
                "app_review_or_policy_constraints_summary": "terms_of_service",
                "live_write_allowed_later": True,
                "manual_fallback_required": True,
                "blockers": [],
                "caveats": ["Requires publisher-level dashboard access token."],
                "reviewer_notes": "All checks passed on Substack API."
            },
            {
                "platform": "discord",
                "source_family": "official_platform_documentation",
                "official_source_type": "api_documentation_page",
                "official_source_title": "Discord Webhook Reference Documentation",
                "official_source_url_label": "https://discord.com/developers/docs/resources/webhook",
                "official_source_accessed_at_manual": "2026-06-30T02:00:00+07:00",
                "dispatch_capability_classification": "official_webhook_supported_for_required_action",
                "supported_dispatch_mechanism": "execute_webhook",
                "auth_or_permission_requirements_summary": "webhook_token_in_url",
                "endpoint_or_surface_summary": "webhook_post_endpoint",
                "rate_limit_or_budget_summary": "5_per_5_seconds",
                "media_payload_constraints_summary": "embed_json_content",
                "error_handling_summary": "standard_http_error_codes",
                "app_review_or_policy_constraints_summary": "discord_developer_policy",
                "live_write_allowed_later": True,
                "manual_fallback_required": True,
                "blockers": [],
                "caveats": ["Cannot create webhooks via API without authorization permissions."],
                "reviewer_notes": "Discord webhook docs verified."
            }
        ],
        "notes": "Verified Substack and Discord capability classifications."
    }


def _declaration():
    return {
        "schema_version": "6.0.0",
        "official_docs_verification_declaration_id": "docs_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T02:30:00+07:00",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "official_docs_source_summary_id": "source_summary_abc123",
        "platforms_reviewed": ["substack", "discord"],
        "official_sources_only_confirmed": True,
        "no_credentials_used_confirmed": True,
        "no_live_calls_confirmed": True,
        "no_browser_login_confirmed": True,
        "endpoint_mapping_later_required": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "declaration_decision": "mark_official_docs_verified_for_future_dispatch_request_mapping",
        "approval_phrase": "MARK_OFFICIAL_DOCS_VERIFIED_FOR_FUTURE_MAPPING_ONLY_NOT_SEND",
        "approval_scope": "official_docs_verification_only",
        "notes": "Verified official docs."
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
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), _source_summary())
    assert packet.docs_verification_available is True
    assert packet.docs_verification_declared_ready is True
    assert packet.eligible_for_future_endpoint_mapping_gate is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_unsupported_by_official_docs_on_one_platform_emits_available_but_not_eligible():
    summary = _source_summary()
    summary["platform_rows"][0]["dispatch_capability_classification"] = "unsupported_by_official_docs"
    summary["platform_rows"][0]["live_write_allowed_later"] = False
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is True
    assert packet.eligible_for_future_endpoint_mapping_gate is False


def test_unclear_requires_operator_decision_emits_available_but_not_eligible():
    summary = _source_summary()
    summary["platform_rows"][0]["dispatch_capability_classification"] = "unclear_requires_operator_decision"
    summary["platform_rows"][0]["live_write_allowed_later"] = False
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is True
    assert packet.eligible_for_future_endpoint_mapping_gate is False
    assert "docs_verification_unclear_capability_classifications_detected" in packet.warnings


def test_wrong_request_gate_task_label_fails_closed():
    gate = _request_gate()
    gate["task_label"] = "wrong"
    packet = make_official_platform_docs_verification_packet(gate, _declaration(), _source_summary())
    assert packet.docs_verification_available is False
    assert "gate_task_label_invalid" in packet.blockers


def test_request_gate_gating_failures_fail_closed():
    for field_name in ["dispatch_request_package_gate_available", "dispatch_request_package_gate_declared_ready", "eligible_for_future_supervised_dispatch_request_package"]:
        gate = _request_gate()
        gate[field_name] = False
        packet = make_official_platform_docs_verification_packet(gate, _declaration(), _source_summary())
        assert packet.docs_verification_available is False
        assert f"gate_field_{field_name}_invalid" in packet.blockers


def test_docs_source_summary_missing_field_fails_closed():
    summary = _source_summary()
    summary.pop("reviewer_id", None)
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is False
    assert "summary_field_missing_reviewer_id" in packet.blockers


def test_platform_row_non_official_source_family_fails_closed():
    summary = _source_summary()
    summary["platform_rows"][0]["source_family"] = "third_party_docs"
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is False
    assert "summary_platform_row_0_source_family_invalid" in packet.blockers


def test_platform_row_raw_url_with_token_fails_closed():
    summary = _source_summary()
    summary["platform_rows"][0]["official_source_url_label"] = "https://substack.com/api?token=secret123"
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is False
    assert "summary_platform_row_0_url_label_contains_restricted_term" in packet.blockers or "summary_platform_row_0_url_label_not_generic" in packet.blockers


def test_platform_row_live_write_allowed_later_incompatible_fails_closed():
    summary = _source_summary()
    summary["platform_rows"][0]["dispatch_capability_classification"] = "unsupported_by_official_docs"
    summary["platform_rows"][0]["live_write_allowed_later"] = True
    packet = make_official_platform_docs_verification_packet(_request_gate(), _declaration(), summary)
    assert packet.docs_verification_available is False
    assert "summary_platform_row_0_live_write_allowed_later_incompatible_with_classification" in packet.blockers


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
        assert packet.docs_verification_available is False
        assert f"declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platforms_reviewed_wrong_order_fails_closed():
    decl = _declaration()
    decl["platforms_reviewed"] = ["discord", "substack"]
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_platforms_reviewed_invalid" in packet.blockers


def test_confirmed_later_required_booleans_false_fail_closed():
    for field_name in ["official_sources_only_confirmed", "endpoint_mapping_later_required"]:
        decl = _declaration()
        decl[field_name] = False
        packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
        assert packet.docs_verification_available is False
        assert f"declaration_field_{field_name}_not_true" in packet.blockers


def test_source_summary_id_mismatch_fails_closed():
    decl = _declaration()
    decl["official_docs_source_summary_id"] = "different_summary_id"
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_official_docs_source_summary_id_mismatch" in packet.blockers


def test_combined_payload_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["combined_payload_hash"] = "different_hash"
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_combined_payload_hash_mismatch" in packet.blockers


def test_declaration_safety_check_detects_forbidden_claims():
    decl = _declaration()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_official_platform_docs_verification_packet(_request_gate(), decl, _source_summary())
    assert packet.docs_verification_available is False
    assert "declaration_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    gate = _request_gate()
    gate["canonical_slug"] = "private_key = my_secret"
    packet = make_official_platform_docs_verification_packet(gate, _declaration(), _source_summary())
    assert packet.docs_verification_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/official_platform_docs_verification_v6.py").read_text(encoding="utf-8")
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
    p_path = tmp_path / "gate.json"
    p_path.write_text(json.dumps(_request_gate()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    s_path = tmp_path / "summary.json"
    s_path.write_text(json.dumps(_source_summary()), encoding="utf-8")

    output_file = tmp_path / "verification_packet.json"
    assert main([
        str(p_path),
        str(b_path),
        str(s_path),
        "--output-file", str(output_file)
    ]) == 0

    first = json.loads(output_file.read_text(encoding="utf-8"))

    assert main([
        str(p_path),
        str(b_path),
        str(s_path),
        "--output-file", str(output_file)
    ]) == 0

    second = json.loads(output_file.read_text(encoding="utf-8"))
    assert first["official_platform_docs_verification_id"] == second["official_platform_docs_verification_id"]
    assert first["docs_verification_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_OFFICIAL_PLATFORM_DOCS_VERIFICATION_FOR_LIVE_DISPATCH_REQUEST_GATE")
    paths = [
        Path("live_contentops/official_platform_docs_verification_v6.py"),
        Path("tests/test_official_platform_docs_verification_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_official_platform_docs_verification_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "gate.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_verification_packet.json"
    exit_code = main([
        str(p_path),
        "A:/declaration.json",
        "A:/summary.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["docs_verification_available"] is False
    assert written["docs_verification_declared_ready"] is False
    assert written["eligible_for_future_endpoint_mapping_gate"] is False
