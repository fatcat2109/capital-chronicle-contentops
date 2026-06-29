import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.platform_capability_lane_split_v6 import (
    make_platform_capability_lane_split_packet,
    main,
    _canonical_json,
)


def _docs_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OFFICIAL_PLATFORM_DOCS_VERIFICATION_FOR_LIVE_DISPATCH_REQUEST_GATE_V0",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "official_docs_verification_declaration_id": "docs_decl_abc123",
        "official_docs_source_summary_id": "source_summary_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T02:30:00+07:00",
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
        "platforms": ["substack", "discord"],
        "requested_platforms": ["substack", "discord"],
        "platform_docs_rows": [
            {
                "platform": "substack",
                "source_family": "official_platform_documentation",
                "official_source_type": "api_documentation_page",
                "official_source_title": "Substack Publishing API Specs",
                "official_source_url_label": "https://substack.com/help/api",
                "official_source_accessed_at_manual": "2026-06-30T02:00:00+07:00",
                "dispatch_capability_classification": "unclear_requires_operator_decision",
                "supported_dispatch_mechanism": "unclear",
                "auth_or_permission_requirements_summary": "unclear",
                "endpoint_or_surface_summary": "unclear",
                "rate_limit_or_budget_summary": "unclear",
                "media_payload_constraints_summary": "markdown_text_only",
                "error_handling_summary": "json_error_responses",
                "app_review_or_policy_constraints_summary": "terms_of_service",
                "live_write_allowed_later": False,
                "manual_fallback_required": True,
                "blockers": [],
                "caveats": ["Requires publisher-level dashboard access token."],
                "reviewer_notes": "Substack official API publishing documentation not verified from official public docs; manual/browser fallback or later operator-provided official source required."
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
        "docs_verification_available": True,
        "docs_verification_declared_ready": True,
        "eligible_for_future_endpoint_mapping_gate": False,
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
        "warnings": ["sample_packet_non_runtime", "substack_official_api_docs_unverified", "docs_verification_unclear_capability_classifications_detected"]
    }


def _declaration():
    return {
        "schema_version": "6.0.0",
        "lane_split_declaration_id": "lane_split_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T03:00:00+07:00",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "lane_split_mode": "operator_declared_platform_capability_lane_split_only_not_send",
        "platforms_reviewed": ["substack", "discord"],
        "discord_lane_expected": "future_webhook_endpoint_mapping_candidate",
        "substack_lane_expected": "manual_browser_or_manual_export_fallback_required",
        "partial_platform_endpoint_mapping_allowed": True,
        "all_platforms_endpoint_mapping_required_for_full_live_loop": True,
        "substack_manual_fallback_required_confirmed": True,
        "discord_endpoint_mapping_later_required": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "declaration_decision": "mark_platform_capability_lane_split_ready",
        "approval_phrase": "MARK_PLATFORM_CAPABILITY_LANE_SPLIT_READY_ONLY_NOT_SEND",
        "approval_scope": "platform_capability_lane_split_only",
        "notes": "Verified capability split lanes."
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


def test_valid_inputs_emits_lane_split_packet():
    packet = make_platform_capability_lane_split_packet(_docs_packet(), _declaration())
    assert packet.lane_split_available is True
    assert packet.lane_split_declared_ready is True
    assert packet.eligible_for_discord_endpoint_mapping_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.partial_platform_endpoint_mapping_ready is True
    assert not packet.blockers
    assert "substack_official_api_docs_unverified" in packet.warnings
    _assert_no_public_state(packet)


def test_substack_lane_fallback_when_unclear_unsupported():
    for classification in ["unclear_requires_operator_decision", "unsupported_by_official_docs"]:
        docs = _docs_packet()
        docs["platform_docs_rows"][0]["dispatch_capability_classification"] = classification
        packet = make_platform_capability_lane_split_packet(docs, _declaration())
        assert packet.lane_split_available is True
        row = packet.platform_lane_rows[0]
        assert row["platform"] == "substack"
        assert row["lane_decision"] == "manual_browser_or_manual_export_fallback_required"
        assert row["manual_fallback_required"] is True


def test_discord_lane_candidate_when_valid():
    packet = make_platform_capability_lane_split_packet(_docs_packet(), _declaration())
    row = packet.platform_lane_rows[1]
    assert row["platform"] == "discord"
    assert row["lane_decision"] == "future_webhook_endpoint_mapping_candidate"
    assert row["endpoint_mapping_candidate"] is True


def test_discord_lane_unsupported_blocks_discord_eligibility():
    docs = _docs_packet()
    docs["platform_docs_rows"][1]["dispatch_capability_classification"] = "unsupported_by_official_docs"
    docs["platform_docs_rows"][1]["live_write_allowed_later"] = False
    packet = make_platform_capability_lane_split_packet(docs, _declaration())
    assert packet.lane_split_available is True
    assert packet.eligible_for_discord_endpoint_mapping_gate is False


def test_substack_unsupported_incorrect_claims_fails_closed():
    docs = _docs_packet()
    # Attempt to incorrectly set Substack api support true
    docs["platform_docs_rows"][0]["dispatch_capability_classification"] = "official_api_supported_for_required_action"
    docs["platform_docs_rows"][0]["live_write_allowed_later"] = True
    packet = make_platform_capability_lane_split_packet(docs, _declaration())
    assert packet.lane_split_available is False
    assert "substack_official_api_docs_unverified" in packet.blockers


def test_wrong_docs_task_label_fails_closed():
    docs = _docs_packet()
    docs["task_label"] = "wrong"
    packet = make_platform_capability_lane_split_packet(docs, _declaration())
    assert packet.lane_split_available is False
    assert "docs_task_label_invalid" in packet.blockers


def test_docs_gating_failures_fail_closed():
    for field_name in ["docs_verification_available", "docs_verification_declared_ready"]:
        docs = _docs_packet()
        docs[field_name] = False
        packet = make_platform_capability_lane_split_packet(docs, _declaration())
        assert packet.lane_split_available is False
        assert f"docs_verification_not_" in packet.blockers[0]


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
        assert packet.lane_split_available is False
        assert f"declaration_rejected_or_deferred_{val}" in packet.blockers


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
    assert packet.lane_split_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
    assert packet.lane_split_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platforms_reviewed_wrong_order_fails_closed():
    decl = _declaration()
    decl["platforms_reviewed"] = ["discord", "substack"]
    packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
    assert packet.lane_split_available is False
    assert "declaration_platforms_reviewed_invalid" in packet.blockers


def test_lane_expected_mismatch_fails_closed():
    for lane_field in ["discord_lane_expected", "substack_lane_expected"]:
        decl = _declaration()
        decl[lane_field] = "wrong"
        packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
        assert packet.lane_split_available is False
        assert f"declaration_{lane_field}_invalid" in packet.blockers


def test_all_confirmed_later_required_booleans_false_fail_closed():
    for field_name in ["partial_platform_endpoint_mapping_allowed", "kill_switch_later_required"]:
        decl = _declaration()
        decl[field_name] = False
        packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
        assert packet.lane_split_available is False
        assert f"declaration_field_{field_name}_not_true" in packet.blockers


def test_source_id_mismatch_fails_closed():
    decl = _declaration()
    decl["official_platform_docs_verification_id"] = "different_id"
    packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
    assert packet.lane_split_available is False
    assert "declaration_official_platform_docs_verification_id_mismatch" in packet.blockers


def test_declaration_safety_check_detects_forbidden_claims():
    decl = _declaration()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_platform_capability_lane_split_packet(_docs_packet(), decl)
    assert packet.lane_split_available is False
    assert "declaration_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    docs = _docs_packet()
    docs["official_platform_docs_verification_id"] = "private_key = my_secret"
    packet = make_platform_capability_lane_split_packet(docs, _declaration())
    assert packet.lane_split_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/platform_capability_lane_split_v6.py").read_text(encoding="utf-8")
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
    p_path = tmp_path / "docs.json"
    p_path.write_text(json.dumps(_docs_packet()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    output_file = tmp_path / "lane_split_packet.json"
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
    assert first["platform_capability_lane_split_id"] == second["platform_capability_lane_split_id"]
    assert first["lane_split_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_PLATFORM_CAPABILITY_LANE_SPLIT_FROM_OFFICIAL_DOCS")
    paths = [
        Path("live_contentops/platform_capability_lane_split_v6.py"),
        Path("tests/test_platform_capability_lane_split_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_platform_capability_lane_split_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "docs.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_lane_split_packet.json"
    exit_code = main([
        str(p_path),
        "A:/declaration.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["lane_split_available"] is False
    assert written["lane_split_declared_ready"] is False
    assert written["eligible_for_discord_endpoint_mapping_gate"] is False
