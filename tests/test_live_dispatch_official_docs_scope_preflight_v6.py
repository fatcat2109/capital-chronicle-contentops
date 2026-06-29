import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.live_dispatch_official_docs_scope_preflight_v6 import (
    make_live_dispatch_scope_preflight_packet,
    main,
    _normalize_path,
    _canonical_json,
)


def _readiness():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LIVE_DISPATCH_READINESS_PREFLIGHT_FROM_EXECUTION_PAYLOADS_V0",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "live_dispatch_readiness_declaration_id": "readiness_declaration_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:10:00+07:00",
        "local_dispatch_execution_payload_manifest_id": "manifest_abc123",
        "local_dispatch_execution_payload_manifest_sha256": "manifest_sha_abc123",
        "operator_supervised_dispatch_review_decision_packet_id": "supervised_decision_abc123",
        "local_destination_binding_preflight_id": "dest_binding_preflight_abc123",
        "destination_binding_id": "dest_binding_abc123",
        "local_dispatch_payload_manifest_id": "dispatch_payload_manifest_abc123",
        "operator_dispatch_review_decision_packet_id": "op_dispatch_decision_abc123",
        "local_dispatch_preflight_id": "local_preflight_abc123",
        "local_active_outbox_manifest_id": "active_outbox_manifest_abc123",
        "operator_active_outbox_review_decision_id": "active_outbox_review_decision_abc123",
        "active_outbox_eligibility_id": "active_outbox_eligibility_abc123",
        "outbox_package_staging_id": "staging_abc123",
        "payload_review_ledger_id": "payload_ledger_abc123",
        "approval_intent_id": "approval_intent_abc123",
        "variant_preview_staging_id": "preview_staging_abc123",
        "metadata_values_review_id": "metadata_review_abc123",
        "metadata_values_id": "metadata_values_abc123",
        "metadata_proposal_id": "metadata_proposal_abc123",
        "source_pack_intake_id": "source_intake_abc123",
        "source_pack_id": "source_pack_abc123",
        "editorial_workflow_id": "workflow_abc123",
        "canonical_slug": "sample-title",
        "canonical_title": "Sample Title",
        "execution_preparation_json_files": [
            "A:/prepared_payloads/substack_execution_preparation.json",
            "A:/prepared_payloads/discord_execution_preparation.json"
        ],
        "execution_preparation_json_hashes": {
            "a:/prepared_payloads/substack_execution_preparation.json": "j1",
            "a:/prepared_payloads/discord_execution_preparation.json": "j2"
        },
        "execution_preparation_markdown_files": [
            "A:/prepared_payloads/substack_execution_preparation.md",
            "A:/prepared_payloads/discord_execution_preparation.md"
        ],
        "execution_preparation_markdown_hashes": {
            "a:/prepared_payloads/substack_execution_preparation.md": "m1",
            "a:/prepared_payloads/discord_execution_preparation.md": "m2"
        },
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
        "platform_action_class": "supervised_dispatch_future_gate",
        "dispatch_family": "substack_discord_dispatch_family",
        "official_docs_required": True,
        "credentials_required_later": True,
        "credential_key_names_only": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "destination_binding_required_later": True,
        "endpoint_allowlist_required_later": True,
        "payload_hash_required_later": True,
        "explicit_operator_approval_required_later": True,
        "kill_switch_required": True,
        "combined_payload_hash": "combined_sha256_xyz",
        "live_dispatch_readiness_preflight_available": True,
        "eligible_for_future_live_dispatch_gate": True,
        "live_dispatch_readiness_preflight_approved": True,
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


def _docs_declaration():
    return {
        "schema_version": "6.0.0",
        "official_docs_declaration_id": "docs_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:10:00+07:00",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "docs_review_mode": "operator_declared_official_docs_review_only",
        "source_rows": [
            {
                "platform": "substack",
                "source_kind": "official_docs_operator_declared_reference",
                "source_label": "Substack API Reference",
                "official_docs_reviewed": True,
                "doc_topics_reviewed": ["auth_model", "permissions"],
                "operator_notes": "Local mapping only."
            },
            {
                "platform": "discord",
                "source_kind": "official_docs_operator_declared_reference",
                "source_label": "Discord Webhook Reference",
                "official_docs_reviewed": True,
                "doc_topics_reviewed": ["webhook_behavior", "rate_limits"],
                "operator_notes": "Reviewed rate limit schedules."
            }
        ],
        "declaration_decision": "mark_official_docs_review_declared",
        "approval_phrase": "DECLARE_OFFICIAL_DOCS_REVIEWED_FOR_FUTURE_GATE_ONLY",
        "approval_scope": "official_docs_scope_preflight_only",
        "notes": "Verified local guidelines."
    }


def _scope_declaration():
    return {
        "schema_version": "6.0.0",
        "live_scope_declaration_id": "scope_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:10:00+07:00",
        "live_dispatch_readiness_preflight_id": "readiness_preflight_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
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
        "declaration_decision": "mark_scope_ready_for_future_supervised_live_gate",
        "approval_phrase": "MARK_SCOPE_READY_FOR_FUTURE_SUPERVISED_LIVE_GATE_ONLY_NOT_SEND",
        "approval_scope": "live_scope_preflight_only",
        "notes": "Scope validated."
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


def test_valid_inputs_emits_scope_preflight_packet():
    ready = _readiness()
    docs = _docs_declaration()
    scope = _scope_declaration()

    packet = make_live_dispatch_scope_preflight_packet(ready, docs, scope)
    assert packet.live_dispatch_scope_preflight_available is True
    assert packet.eligible_for_supervised_live_gate is True
    assert packet.official_docs_scope_declared_ready is True
    assert packet.live_scope_declared_ready is True
    assert not packet.blockers
    assert packet.live_dispatch_readiness_preflight_sha256 != ""

    _assert_no_public_state(packet)


def test_reject_or_defer_in_official_docs_fails_closed():
    for val in ["reject", "defer"]:
        ready = _readiness()
        docs = _docs_declaration()
        docs["declaration_decision"] = val
        docs["approval_phrase"] = "NONE"
        docs["approval_scope"] = "NONE"
        scope = _scope_declaration()

        packet = make_live_dispatch_scope_preflight_packet(ready, docs, scope)
        assert packet.live_dispatch_scope_preflight_available is False
        assert packet.eligible_for_supervised_live_gate is False
        assert packet.official_docs_scope_declared_ready is False
        assert f"docs_declaration_rejected_or_deferred_{val}" in packet.blockers


def test_reject_or_defer_in_live_scope_fails_closed():
    for val in ["reject", "defer"]:
        ready = _readiness()
        docs = _docs_declaration()
        scope = _scope_declaration()
        scope["declaration_decision"] = val
        scope["approval_phrase"] = "NONE"
        scope["approval_scope"] = "NONE"

        packet = make_live_dispatch_scope_preflight_packet(ready, docs, scope)
        assert packet.live_dispatch_scope_preflight_available is False
        assert packet.eligible_for_supervised_live_gate is False
        assert packet.live_scope_declared_ready is False
        assert f"scope_declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    # 1. Missing notes in docs
    docs = _docs_declaration()
    docs.pop("notes", None)
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_notes_missing_or_invalid" in packet.blockers

    # 2. Non-string notes in docs
    docs = _docs_declaration()
    docs["notes"] = 1234
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_notes_missing_or_invalid" in packet.blockers

    # 3. Missing notes in scope
    scope = _scope_declaration()
    scope.pop("notes", None)
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_notes_missing_or_invalid" in packet.blockers

    # 4. Non-string notes in scope
    scope = _scope_declaration()
    scope["notes"] = True
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_notes_missing_or_invalid" in packet.blockers


def test_wrong_readiness_task_label_fails_closed():
    ready = _readiness()
    ready["task_label"] = "wrong"
    packet = make_live_dispatch_scope_preflight_packet(ready, _docs_declaration(), _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "readiness_task_label_invalid" in packet.blockers


def test_readiness_banned_states_fail_closed():
    for field_name, bad_value in [
        ("live_dispatch_readiness_preflight_available", False),
        ("eligible_for_future_live_dispatch_gate", False),
        ("live_dispatch_readiness_preflight_approved", False),
        ("live_send_request_created", True),
        ("approval_for_live_dispatch", True),
        ("dispatch_allowed", True),
        ("publication_ready", True),
    ]:
        ready = _readiness()
        ready[field_name] = bad_value
        packet = make_live_dispatch_scope_preflight_packet(ready, _docs_declaration(), _scope_declaration())
        assert packet.live_dispatch_scope_preflight_available is False
        assert f"readiness_field_{field_name}_invalid" in packet.blockers


def test_official_docs_source_rows_validations():
    # 1. Missing rows
    docs = _docs_declaration()
    docs["source_rows"] = []
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_rows_count_invalid" in packet.blockers

    # 2. Duplicate platform
    docs = _docs_declaration()
    docs["source_rows"][1]["platform"] = "substack"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_rows_platforms_mismatch" in packet.blockers

    # 3. URL in row notes
    docs = _docs_declaration()
    docs["source_rows"][0]["operator_notes"] = "See http://google.com"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_url_detected" in packet.blockers

    # 4. Secret marker in row notes
    docs = _docs_declaration()
    docs["source_rows"][0]["operator_notes"] = "private_key = test"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_secret_marker_detected" in packet.blockers


def test_live_scope_platforms_and_keys_validations():
    # 1. Platform wrong order
    scope = _scope_declaration()
    scope["platforms"] = ["discord", "substack"]
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_platforms_invalid" in packet.blockers

    # 2. Credential key names mismatch with readiness
    scope = _scope_declaration()
    scope["credential_key_names_only"] = ["SOME_OTHER_KEY"]
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_credential_key_names_only_mismatch" in packet.blockers

    # 3. Credential key with token value or hash prefix
    scope = _scope_declaration()
    scope["credential_key_names_only"] = ["abc1234567890abcdef1234567890abcdef"] # too long hex
    ready = _readiness()
    ready["credential_key_names_only"] = ["abc1234567890abcdef1234567890abcdef"]
    packet = make_live_dispatch_scope_preflight_packet(ready, _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert any("hex_value_detected" in b for b in packet.blockers)


def test_timeout_and_retry_policies():
    # 1. Retry policy not no_hidden_retry
    scope = _scope_declaration()
    scope["retry_policy_later"] = "retry_3_times"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_retry_policy_later_invalid" in packet.blockers

    # 2. Timeout policy containing digit
    scope = _scope_declaration()
    scope["timeout_policy_later"] = "timeout_30_secs"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_timeout_policy_later_invalid" in packet.blockers


def test_fake_claims_or_financial_advice_fail_closed():
    # 1. Fake claim in docs notes
    docs = _docs_declaration()
    docs["notes"] = "Supports fake_readiness checks"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_fake_claim_detected_fake_readiness" in packet.blockers

    # 2. Trading advice in scope notes
    scope = _scope_declaration()
    scope["notes"] = "Use buy position strategy"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_financial_advice_or_signal_framing_detected" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    ready = _readiness()
    ready["canonical_slug"] = "private_key = my_secret"
    
    packet = make_live_dispatch_scope_preflight_packet(ready, _docs_declaration(), _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert packet.live_dispatch_readiness_preflight_sha256 == ""


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/live_dispatch_official_docs_scope_preflight_v6.py").read_text(encoding="utf-8")
    import_patterns = [
        r"\bimport\s+requests\b",
        r"\bimport\s+urllib\b",
        r"\bimport\s+httpx\b",
        r"\bimport\s+provider_gateway\b",
        r"\bimport\s+browser\b",
        r"\bimport\s+webbrowser\b",
        r"\bfrom\s+requests\b",
        r"\bfrom\s+urllib\b",
        r"\bfrom\s+httpx\b",
        r"\bfrom\s+provider_gateway\b",
        r"\bfrom\s+browser\b",
        r"\bfrom\s+webbrowser\b",
        r"\bgetenv\b",
        r"\benviron\b",
    ]
    for pat in import_patterns:
        assert not re.search(pat, source)



def test_cli_writes_deterministic_packet(tmp_path):
    r_path = tmp_path / "readiness.json"
    r_path.write_text(json.dumps(_readiness()), encoding="utf-8")

    d_path = tmp_path / "docs.json"
    d_path.write_text(json.dumps(_docs_declaration()), encoding="utf-8")

    s_path = tmp_path / "scope.json"
    s_path.write_text(json.dumps(_scope_declaration()), encoding="utf-8")

    output_file = tmp_path / "scope_preflight.json"
    assert main([
        str(r_path),
        str(d_path),
        str(s_path),
        "--output-file", str(output_file)
    ]) == 0

    first = json.loads(output_file.read_text(encoding="utf-8"))

    assert main([
        str(r_path),
        str(d_path),
        str(s_path),
        "--output-file", str(output_file)
    ]) == 0

    second = json.loads(output_file.read_text(encoding="utf-8"))
    assert first["live_dispatch_scope_preflight_id"] == second["live_dispatch_scope_preflight_id"]
    assert first["live_dispatch_scope_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LIVE_DISPATCH_OFFICIAL_DOCS_AND_SCOPE_PREFLIGHT_FROM_READINESS")
    paths = [
        Path("live_contentops/live_dispatch_official_docs_scope_preflight_v6.py"),
        Path("tests/test_live_dispatch_official_docs_scope_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_live_dispatch_scope_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    r_path = tmp_path / "readiness.json"
    r_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_scope_preflight.json"
    exit_code = main([
        str(r_path),
        "A:/docs.json",
        "A:/scope.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["live_dispatch_scope_preflight_available"] is False
    assert written["eligible_for_supervised_live_gate"] is False
    assert written["official_docs_scope_declared_ready"] is False
    assert written["live_scope_declared_ready"] is False


def test_forbidden_live_claims_gate_source_rows_extra_fields():
    # 1. Official docs source row extra field endpoint_path: "/api/posts" fails closed.
    docs = _docs_declaration()
    docs["source_rows"][0]["endpoint_path"] = "/api/posts"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_extra_field_endpoint_path_detected" in packet.blockers

    # 2. Official docs source row extra field request_payload: {"body": "x"} fails closed.
    docs = _docs_declaration()
    docs["source_rows"][0]["request_payload"] = {"body": "x"}
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_extra_field_request_payload_detected" in packet.blockers

    # 3. Official docs source row extra field raw_copied_docs: "..." fails closed.
    docs = _docs_declaration()
    docs["source_rows"][0]["raw_copied_docs"] = "..."
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_extra_field_raw_copied_docs_detected" in packet.blockers


def test_forbidden_live_claims_gate_notes_and_scope_fields():
    # 1. Official docs source row operator_notes containing live instruction: send now fails closed.
    docs = _docs_declaration()
    docs["source_rows"][0]["operator_notes"] = "live instruction: send now"
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_source_row_index_0_forbidden_live_claim_detected_live_instruction" in packet.blockers

    # 2. Docs declaration notes containing api endpoint fails closed.
    docs = _docs_declaration()
    docs["notes"] = "This is our api endpoint info."
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is False
    assert "docs_forbidden_live_claim_detected_api_endpoint" in packet.blockers

    # 3. Scope declaration notes containing webhook request fails closed.
    scope = _scope_declaration()
    scope["notes"] = "Uses a webhook request configuration."
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_forbidden_live_claim_detected_webhook" in packet.blockers

    # 4. Scope declaration notes containing live dispatch fails closed.
    scope = _scope_declaration()
    scope["notes"] = "Trigger live dispatch sequence."
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is False
    assert "scope_forbidden_live_claim_detected_live_dispatch" in packet.blockers

    # 5. Scope declaration notes containing public_url or public_metrics fails closed.
    for note_val, expected_term in [
        ("has public_url attribute", "public_url"),
        ("checks public_metrics dashboard", "public_metrics"),
    ]:
        scope = _scope_declaration()
        scope["notes"] = note_val
        packet = make_live_dispatch_scope_preflight_packet(_readiness(), _docs_declaration(), scope)
        assert packet.live_dispatch_scope_preflight_available is False
        assert f"scope_forbidden_live_claim_detected_{expected_term}" in packet.blockers


def test_forbidden_live_claims_gate_allowed_phrases_pass():
    # 1. Allowed topic label endpoint_allowlist in doc_topics_reviewed still passes.
    docs = _docs_declaration()
    docs["source_rows"][0]["doc_topics_reviewed"] = ["endpoint_allowlist"]
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is True
    assert not packet.blockers

    # 2. Allowed topic label webhook_behavior in doc_topics_reviewed still passes.
    docs = _docs_declaration()
    docs["source_rows"][0]["doc_topics_reviewed"] = ["webhook_behavior"]
    packet = make_live_dispatch_scope_preflight_packet(_readiness(), docs, _scope_declaration())
    assert packet.live_dispatch_scope_preflight_available is True
    assert not packet.blockers

    # 3. Valid credential key name containing WEBHOOK still passes.
    ready = _readiness()
    ready["credential_key_names_only"] = ["MY_DISCORD_WEBHOOK"]
    scope = _scope_declaration()
    scope["credential_key_names_only"] = ["MY_DISCORD_WEBHOOK"]
    packet = make_live_dispatch_scope_preflight_packet(ready, _docs_declaration(), scope)
    assert packet.live_dispatch_scope_preflight_available is True
    assert not packet.blockers

