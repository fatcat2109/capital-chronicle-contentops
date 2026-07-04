import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_endpoint_mapping_preflight_v6 import (
    make_discord_endpoint_mapping_preflight_packet,
    main,
)


def _lane_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_PLATFORM_CAPABILITY_LANE_SPLIT_FROM_OFFICIAL_DOCS_V0",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "lane_split_declaration_id": "lane_split_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T03:00:00+07:00",
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
        "platforms": ["substack", "discord"],
        "requested_platforms": ["substack", "discord"],
        "platform_lane_rows": [
            {
                "platform": "substack",
                "source_docs_classification": "unclear_requires_operator_decision",
                "source_docs_live_write_allowed_later": False,
                "lane_decision": "manual_browser_or_manual_export_fallback_required",
                "endpoint_mapping_candidate": False,
                "manual_fallback_required": True,
                "blocking_reason": ["substack_official_api_unverified"],
                "caveats": ["Requires publisher-level dashboard access token."],
                "warnings": []
            },
            {
                "platform": "discord",
                "source_docs_classification": "official_webhook_supported_for_required_action",
                "source_docs_live_write_allowed_later": True,
                "lane_decision": "future_webhook_endpoint_mapping_candidate",
                "endpoint_mapping_candidate": True,
                "manual_fallback_required": True,
                "blocking_reason": [],
                "caveats": ["Cannot create webhooks via API without authorization permissions."],
                "warnings": []
            }
        ],
        "discord_endpoint_mapping_candidate": True,
        "substack_manual_fallback_required": True,
        "partial_platform_endpoint_mapping_ready": True,
        "all_platforms_endpoint_mapping_ready": False,
        "all_platforms_endpoint_mapping_required_for_full_live_loop": True,
        "permission_verification_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "lane_split_available": True,
        "lane_split_declared_ready": True,
        "eligible_for_discord_endpoint_mapping_gate": True,
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
        "discord_endpoint_mapping_declaration_id": "discord_endpoint_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T03:30:00+07:00",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "endpoint_mapping_mode": "operator_declared_discord_endpoint_mapping_labels_only_not_request",
        "platform": "discord",
        "endpoint_family": "discord_execute_webhook_label_only",
        "endpoint_host_label": "discord_operator_declared_webhook_host_label",
        "endpoint_path_label": "discord_operator_declared_webhook_path_label",
        "endpoint_method_label": "webhook_method_label_only",
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
        "declaration_decision": "mark_discord_endpoint_mapping_preflight_ready",
        "approval_phrase": "MARK_DISCORD_ENDPOINT_MAPPING_PREFLIGHT_READY_ONLY_NOT_SEND",
        "approval_scope": "discord_endpoint_mapping_preflight_only",
        "notes": "Verified Discord label-only endpoint mapping."
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


def test_valid_inputs_emits_preflight_packet():
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), _declaration())
    assert packet.discord_endpoint_mapping_preflight_available is True
    assert packet.discord_endpoint_mapping_preflight_declared_ready is True
    assert packet.eligible_for_discord_webhook_value_binding_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.substack_manual_fallback_required is True
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_output_contains_only_labels_no_secrets():
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), _declaration())
    # Verify label-only constraints
    assert packet.endpoint_mapping_label_only is True
    assert packet.endpoint_host_label == "discord_operator_declared_webhook_host_label"
    assert packet.endpoint_path_label == "discord_operator_declared_webhook_path_label"
    assert packet.endpoint_method_label == "webhook_method_label_only"


def test_wrong_lane_split_task_label_fails_closed():
    lane = _lane_packet()
    lane["task_label"] = "wrong"
    packet = make_discord_endpoint_mapping_preflight_packet(lane, _declaration())
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "lane_task_label_invalid" in packet.blockers


def test_lane_gating_failures_fail_closed():
    for f in ["lane_split_available", "lane_split_declared_ready", "eligible_for_discord_endpoint_mapping_gate"]:
        lane = _lane_packet()
        lane[f] = False
        packet = make_discord_endpoint_mapping_preflight_packet(lane, _declaration())
        assert packet.discord_endpoint_mapping_preflight_available is False


def test_discord_lane_invalid_fails_closed():
    # Discord row in lane is missing or wrong lane decision
    lane = _lane_packet()
    lane["platform_lane_rows"][1]["lane_decision"] = "wrong"
    packet = make_discord_endpoint_mapping_preflight_packet(lane, _declaration())
    assert packet.discord_endpoint_mapping_preflight_available is False


def test_substack_lane_not_manual_fallback_fails_closed():
    lane = _lane_packet()
    lane["platform_lane_rows"][0]["lane_decision"] = "wrong"
    packet = make_discord_endpoint_mapping_preflight_packet(lane, _declaration())
    assert packet.discord_endpoint_mapping_preflight_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
        assert packet.discord_endpoint_mapping_preflight_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "declaration_platform_invalid" in packet.blockers


def test_endpoint_family_mismatch_fails_closed():
    decl = _declaration()
    decl["endpoint_family"] = "wrong"
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "declaration_endpoint_family_invalid" in packet.blockers


def test_endpoint_labels_mismatch_fails_closed():
    for label in ["endpoint_host_label", "endpoint_path_label", "endpoint_method_label"]:
        decl = _declaration()
        decl[label] = "wrong"
        packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
        assert packet.discord_endpoint_mapping_preflight_available is False


def test_any_later_required_boolean_false_fails_closed():
    for b in ["webhook_url_value_later_required", "kill_switch_later_required"]:
        decl = _declaration()
        decl[b] = False
        packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
        assert packet.discord_endpoint_mapping_preflight_available is False


def test_declaration_safety_check_detects_forbidden_claims():
    decl = _declaration()
    decl["notes"] = "Accessing endpoint_path value."
    packet = make_discord_endpoint_mapping_preflight_packet(_lane_packet(), decl)
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert "declaration_forbidden_live_claim_detected_endpoint_path" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_without_sha():
    lane = _lane_packet()
    lane["platform_capability_lane_split_id"] = "private_key = my_secret"
    packet = make_discord_endpoint_mapping_preflight_packet(lane, _declaration())
    assert packet.discord_endpoint_mapping_preflight_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_environ_or_os_lookups_and_no_dotenv():
    source = Path("live_contentops/discord_endpoint_mapping_preflight_v6.py").read_text(encoding="utf-8")
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
    p_path = tmp_path / "lane.json"
    p_path.write_text(json.dumps(_lane_packet()), encoding="utf-8")

    b_path = tmp_path / "declaration.json"
    b_path.write_text(json.dumps(_declaration()), encoding="utf-8")

    output_file = tmp_path / "preflight_packet.json"
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
    assert first["discord_endpoint_mapping_preflight_id"] == second["discord_endpoint_mapping_preflight_id"]
    assert first["discord_endpoint_mapping_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_ENDPOINT_MAPPING_PREFLIGHT_FROM_CAPABILITY_LANE_SPLIT")
    paths = [
        Path("live_contentops/discord_endpoint_mapping_preflight_v6.py"),
        Path("tests/test_discord_endpoint_mapping_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_endpoint_mapping_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "lane.json"
    p_path.write_text("[]", encoding="utf-8")

    output_file = tmp_path / "blocked_preflight_packet.json"
    exit_code = main([
        str(p_path),
        "A:/declaration.json",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["discord_endpoint_mapping_preflight_available"] is False
    assert written["discord_endpoint_mapping_preflight_declared_ready"] is False
    assert written["eligible_for_discord_webhook_value_binding_gate"] is False
