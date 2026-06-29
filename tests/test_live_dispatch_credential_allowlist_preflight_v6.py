import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.live_dispatch_credential_allowlist_preflight_v6 import (
    make_credential_allowlist_preflight_packet,
    main,
    _canonical_json,
)


def _scope():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LIVE_DISPATCH_OFFICIAL_DOCS_AND_SCOPE_PREFLIGHT_FROM_READINESS_V0",
        "live_dispatch_scope_preflight_id": "scope_preflight_abc123",
        "official_docs_declaration_id": "docs_decl_abc123",
        "live_scope_declaration_id": "scope_decl_abc123",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "live_dispatch_readiness_preflight_sha256": "readiness_sha256_abc123",
        "live_dispatch_readiness_declaration_id": "readiness_decl_abc123",
        "local_dispatch_execution_payload_manifest_id": "manifest_abc123",
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
        "action_class": "supervised_live_dispatch_future_gate",
        "dispatch_family": "substack_discord_dispatch_family",
        "platforms": ["substack", "discord"],
        "credential_key_names_only": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "account_binding_later_required": True,
        "endpoint_allowlist_later_required": True,
        "payload_hash_later_required": True,
        "explicit_operator_approval_later_required": True,
        "kill_switch_required": True,
        "manual_fallback_required": True,
        "live_write_request_budget_later": 2,
        "timeout_policy_later": "fast_ship_timeout_policy",
        "retry_policy_later": "no_hidden_retry",
        "audit_redaction_required": True,
        "combined_payload_hash": "combined_sha256_xyz",
        "live_dispatch_scope_preflight_available": True,
        "eligible_for_supervised_live_gate": True,
        "official_docs_scope_declared_ready": True,
        "live_scope_declared_ready": True,
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


def _allowlist():
    return {
        "schema_version": "6.0.0",
        "endpoint_allowlist_declaration_id": "allowlist_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:10:00+07:00",
        "live_dispatch_scope_preflight_id": "scope_preflight_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "allowlist_mode": "operator_declared_endpoint_allowlist_only_not_request",
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
        "credential_key_names_only_reviewed": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "live_write_request_budget_confirmed": 2,
        "timeout_policy_confirmed": "fast_ship_timeout_policy",
        "retry_policy_confirmed": "no_hidden_retry",
        "audit_redaction_confirmed": True,
        "declaration_decision": "mark_credential_allowlist_ready_for_future_live_gate",
        "approval_phrase": "MARK_CREDENTIAL_ALLOWLIST_READY_FOR_FUTURE_LIVE_GATE_ONLY_NOT_SEND",
        "approval_scope": "credential_allowlist_preflight_only",
        "notes": "Verified allowlist configuration."
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


def test_valid_inputs_and_env_mapping_emits_eligible_packet():
    scope = _scope()
    decl = _allowlist()
    env = {
        "SUBSTACK_API_KEY_DRAFT_STAGE": "secret_substack",
        "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK": "secret_discord"
    }
    packet = make_credential_allowlist_preflight_packet(scope, decl, check_env=True, env_mapping=env)
    assert packet.credential_allowlist_preflight_available is True
    assert packet.endpoint_allowlist_declared_ready is True
    assert packet.eligible_for_supervised_live_dispatch_request_gate is True
    assert not packet.blockers
    assert packet.credential_presence_complete is True
    assert packet.credential_presence_mode == "checked_declared_key_names_only"
    assert len(packet.credential_presence_rows) == 2

    # Verify no details leaked
    for row in packet.credential_presence_rows:
        assert row["present"] is True
        assert row["checked_by_exact_declared_key_name"] is True
        assert row["value_observed"] is False
        assert row["value_length_observed"] is False
        assert row["value_hash_observed"] is False
        assert row["value_prefix_observed"] is False
        assert row["value_suffix_observed"] is False

    _assert_no_public_state(packet)


def test_valid_inputs_no_env_check_emits_not_checked_packet():
    scope = _scope()
    decl = _allowlist()
    packet = make_credential_allowlist_preflight_packet(scope, decl, check_env=False)
    assert packet.credential_allowlist_preflight_available is True
    assert packet.endpoint_allowlist_declared_ready is True
    assert packet.eligible_for_supervised_live_dispatch_request_gate is False
    assert not packet.blockers
    assert packet.credential_presence_complete is False
    assert packet.credential_presence_mode == "not_checked"
    assert len(packet.credential_presence_rows) == 0


def test_missing_one_declared_credential_fails_eligibility():
    scope = _scope()
    decl = _allowlist()
    env = {
        "SUBSTACK_API_KEY_DRAFT_STAGE": "secret_substack"
        # DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK is missing
    }
    packet = make_credential_allowlist_preflight_packet(scope, decl, check_env=True, env_mapping=env)
    assert packet.credential_allowlist_preflight_available is True
    assert packet.eligible_for_supervised_live_dispatch_request_gate is False
    assert packet.credential_presence_complete is False
    assert "credential_presence_incomplete" in packet.blockers


def test_wrong_scope_task_label_fails_closed():
    scope = _scope()
    scope["task_label"] = "wrong"
    packet = make_credential_allowlist_preflight_packet(scope, _allowlist())
    assert packet.credential_allowlist_preflight_available is False
    assert "scope_task_label_invalid" in packet.blockers


def test_scope_preflight_unavailable_or_not_eligible_fails_closed():
    for f in [
        "live_dispatch_scope_preflight_available",
        "eligible_for_supervised_live_gate",
        "official_docs_scope_declared_ready",
        "live_scope_declared_ready"
    ]:
        scope = _scope()
        scope[f] = False
        packet = make_credential_allowlist_preflight_packet(scope, _allowlist())
        assert packet.credential_allowlist_preflight_available is False
        assert f"scope_field_{f}_invalid" in packet.blockers


def test_endpoint_allowlist_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _allowlist()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_credential_allowlist_preflight_packet(_scope(), decl)
        assert packet.credential_allowlist_preflight_available is False
        assert f"allowlist_declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    decl = _allowlist()
    decl.pop("notes", None)
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_notes_missing_or_invalid" in packet.blockers

    decl = _allowlist()
    decl["notes"] = 1234
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_notes_missing_or_invalid" in packet.blockers


def test_endpoint_rows_validations():
    # 1. Platform invalid order/count
    decl = _allowlist()
    decl["endpoint_allowlist_rows"] = []
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_rows_count_invalid" in packet.blockers

    # 2. Host label containing URL or domain
    decl = _allowlist()
    decl["endpoint_allowlist_rows"][0]["host_label"] = "https://substack.com"
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_row_index_0_host_label_contains_url_or_domain" in packet.blockers

    # 3. Path label starting with slash
    decl = _allowlist()
    decl["endpoint_allowlist_rows"][0]["path_label"] = "/api/v1/posts"
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_row_index_0_path_label_starts_with_slash" in packet.blockers

    # 4. Path label containing forbidden term 'webhook'
    decl = _allowlist()
    decl["endpoint_allowlist_rows"][0]["path_label"] = "my_webhook_path"
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_row_index_0_path_label_contains_forbidden_term_webhook" in packet.blockers

    # 5. Budget exceeding scope budget
    decl = _allowlist()
    decl["endpoint_allowlist_rows"][0]["request_budget"] = 999
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_row_index_0_request_budget_invalid" in packet.blockers


def test_timeout_retry_audit_mismatch_fails_closed():
    decl = _allowlist()
    decl["timeout_policy_confirmed"] = "mismatch_policy"
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_timeout_policy_confirmed_mismatch" in packet.blockers


def test_credential_key_names_only_reviewed_mismatch():
    decl = _allowlist()
    decl["credential_key_names_only_reviewed"] = ["DIFFERENT_KEY"]
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_credential_key_names_only_reviewed_mismatch" in packet.blockers


def test_forbidden_live_claims_safety_gate():
    # 1. Notes containing endpoint value/url
    decl = _allowlist()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_credential_allowlist_preflight_packet(_scope(), decl)
    assert packet.credential_allowlist_preflight_available is False
    assert "allowlist_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    scope = _scope()
    scope["canonical_slug"] = "private_key = my_secret"
    
    packet = make_credential_allowlist_preflight_packet(scope, _allowlist())
    assert packet.credential_allowlist_preflight_available is False
    assert packet.live_dispatch_scope_preflight_sha256 == ""


def test_module_contains_no_provider_browser_network_imports_and_no_dotenv():
    source = Path("live_contentops/live_dispatch_credential_allowlist_preflight_v6.py").read_text(encoding="utf-8")
    import_patterns = [
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bimport\s+httpx\b",
        r"\bimport\s+provider\b",
        r"\bimport\s+browser\b",
        r"\bimport\s+dotenv\b",
        r"\bload_dotenv\b",
    ]
    for pat in import_patterns:
        assert not re.search(pat, source)


def test_cli_writes_deterministic_packet(tmp_path):
    s_path = tmp_path / "scope.json"
    s_path.write_text(json.dumps(_scope()), encoding="utf-8")

    a_path = tmp_path / "allowlist.json"
    a_path.write_text(json.dumps(_allowlist()), encoding="utf-8")

    output_file = tmp_path / "allowlist_preflight.json"
    assert main([
        str(s_path),
        str(a_path),
        "--output-file", str(output_file)
    ]) == 0

    first = json.loads(output_file.read_text(encoding="utf-8"))

    assert main([
        str(s_path),
        str(a_path),
        "--output-file", str(output_file)
    ]) == 0

    second = json.loads(output_file.read_text(encoding="utf-8"))
    assert first["credential_allowlist_preflight_id"] == second["credential_allowlist_preflight_id"]
    assert first["credential_allowlist_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LIVE_DISPATCH_CREDENTIAL_AND_ALLOWLIST_PREFLIGHT_FROM_SCOPE")
    paths = [
        Path("live_contentops/live_dispatch_credential_allowlist_preflight_v6.py"),
        Path("tests/test_live_dispatch_credential_allowlist_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_live_dispatch_credential_allowlist_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    s_path = tmp_path / "scope.json"
    s_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_allowlist_preflight.json"
    exit_code = main([
        str(s_path),
        "A:/allowlist.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["credential_allowlist_preflight_available"] is False
    assert written["endpoint_allowlist_declared_ready"] is False
    assert written["eligible_for_supervised_live_dispatch_request_gate"] is False
