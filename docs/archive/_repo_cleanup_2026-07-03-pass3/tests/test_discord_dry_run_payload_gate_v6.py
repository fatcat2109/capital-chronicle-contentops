import json
import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_dry_run_payload_gate_v6 import (
    make_discord_dry_run_payload_gate_packet,
    main,
)


def _preflight_packet():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_PERMISSION_PROBE_PREFLIGHT_FROM_WEBHOOK_VALUE_BINDING_V0",
        "discord_permission_probe_preflight_id": "discord_permission_probe_preflight_abc123",
        "discord_permission_probe_declaration_id": "discord_permission_probe_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T04:30:00+07:00",
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
        "credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "probe_kind": "discord_webhook_permission_probe_later_not_now",
        "permission_probe_preflight_available": True,
        "permission_probe_preflight_declared_ready": True,
        "eligible_for_discord_dry_run_payload_gate": True,
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
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
        "substack_manual_fallback_required": True,
        "all_platforms_endpoint_mapping_ready": False,
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


def _preview_text():
    return "This is a clean non-advice announcement test."


def _declaration(preview=None):
    if preview is None:
        preview = _preview_text()
    p_hash = hashlib.sha256(preview.encode("utf-8")).hexdigest()
    return {
        "schema_version": "6.0.0",
        "discord_dry_run_payload_declaration_id": "discord_dry_run_payload_decl_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T04:50:00+07:00",
        "discord_permission_probe_preflight_id": "discord_permission_probe_preflight_abc123",
        "discord_webhook_value_binding_preflight_id": "discord_webhook_value_binding_preflight_abc123",
        "discord_endpoint_mapping_preflight_id": "discord_endpoint_preflight_abc123",
        "platform_capability_lane_split_id": "lane_split_abc123",
        "official_platform_docs_verification_id": "docs_verification_abc123",
        "dispatch_request_package_gate_id": "dispatch_request_gate_abc123",
        "combined_payload_hash": "combined_sha256_xyz",
        "dry_run_payload_mode": "operator_declared_discord_dry_run_payload_gate_only_not_send",
        "platform": "discord",
        "payload_kind": "discord_text_or_embed_preview_non_runtime",
        "payload_source_kind": "operator_supplied_preview_text_only",
        "payload_text_preview": preview,
        "payload_text_preview_hash": p_hash,
        "payload_text_preview_hash_algorithm": "sha256",
        "payload_text_preview_non_runtime": True,
        "payload_contains_financial_advice": False,
        "payload_contains_signal_service_framing": False,
        "payload_contains_public_url": False,
        "payload_contains_metrics": False,
        "payload_contains_raw_source_urls": False,
        "payload_contains_citations": False,
        "payload_contains_webhook_url": False,
        "payload_contains_token": False,
        "payload_contains_channel_id": False,
        "payload_contains_account_or_workspace_id": False,
        "payload_http_request_artifact_created": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "operator_payload_review_later_required": True,
        "payload_hash_revalidation_later_required": True,
        "permission_verification_later_required": True,
        "request_budget_later_required": True,
        "timeout_policy_later_required": True,
        "retry_policy_later_required": True,
        "kill_switch_later_required": True,
        "audit_redaction_later_required": True,
        "manual_fallback_later_required": True,
        "declaration_decision": "mark_discord_dry_run_payload_gate_ready",
        "approval_phrase": "MARK_DISCORD_DRY_RUN_PAYLOAD_GATE_READY_ONLY_NOT_SEND",
        "approval_scope": "discord_dry_run_payload_gate_only",
        "notes": "Verified Discord dry-run payload gate."
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
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), _declaration())
    assert packet.discord_dry_run_payload_gate_available is True
    assert packet.discord_dry_run_payload_gate_declared_ready is True
    assert packet.eligible_for_operator_payload_review_gate is True
    assert packet.eligible_for_full_live_dispatch_endpoint_mapping_gate is False
    assert packet.all_platforms_endpoint_mapping_ready is False
    assert packet.payload_length_observed == len(_preview_text())
    assert packet.payload_preview_redacted is True
    assert "clean" not in packet.payload_preview_stored
    assert not packet.blockers
    _assert_no_public_state(packet)


def test_preview_hash_mismatch_fails_closed():
    decl = _declaration()
    decl["payload_text_preview_hash"] = "wrong"
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
    assert packet.discord_dry_run_payload_gate_available is False
    assert "declaration_payload_text_preview_hash_mismatch" in packet.blockers


def test_payload_text_preview_empty_or_too_long_fails_closed():
    decl_empty = _declaration(preview="")
    packet_empty = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl_empty)
    assert packet_empty.discord_dry_run_payload_gate_available is False

    decl_long = _declaration(preview="a" * 2001)
    packet_long = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl_long)
    assert packet_long.discord_dry_run_payload_gate_available is False
    assert "declaration_payload_text_preview_too_long" in packet_long.blockers


def test_payload_containing_forbidden_claims_fails_closed():
    for text, blocker_suffix in [
        ("This is my webhook_url value", "webhook_url"),
        ("Please buy this equity.", "financial_advice_or_signal_framing_detected"),
        ("This is my fake_url value", "fake_claim_detected_fake_url"),
        ("This is a live_dispatch action", "live_dispatch")
    ]:
        decl = _declaration(preview=text)
        packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
        assert packet.discord_dry_run_payload_gate_available is False
        assert any(blocker_suffix in b for b in packet.blockers)


def test_wrong_permission_probe_task_label_fails_closed():
    preflight = _preflight_packet()
    preflight["task_label"] = "wrong"
    packet = make_discord_dry_run_payload_gate_packet(preflight, _declaration())
    assert packet.discord_dry_run_payload_gate_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_permission_probe_unavailable_or_not_declared_ready_fails_closed():
    for f in ["permission_probe_preflight_available", "permission_probe_preflight_declared_ready"]:
        preflight = _preflight_packet()
        preflight[f] = False
        packet = make_discord_dry_run_payload_gate_packet(preflight, _declaration())
        assert packet.discord_dry_run_payload_gate_available is False


def test_declaration_reject_or_defer_fails_closed():
    for val in ["reject", "defer"]:
        decl = _declaration()
        decl["declaration_decision"] = val
        decl["approval_phrase"] = "NONE"
        decl["approval_scope"] = "NONE"
        packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
        assert packet.discord_dry_run_payload_gate_available is False


def test_missing_or_non_string_notes_fails_closed():
    decl = _declaration()
    decl.pop("notes", None)
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
    assert packet.discord_dry_run_payload_gate_available is False
    assert "declaration_notes_missing_or_invalid" in packet.blockers


def test_declaration_extra_field_fails_closed():
    decl = _declaration()
    decl["extra_field"] = "value"
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
    assert packet.discord_dry_run_payload_gate_available is False
    assert "declaration_extra_field_extra_field_detected" in packet.blockers


def test_platform_not_discord_fails_closed():
    decl = _declaration()
    decl["platform"] = "substack"
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
    assert packet.discord_dry_run_payload_gate_available is False
    assert "declaration_platform_invalid" in packet.blockers


def test_mismatched_kinds_fails_closed():
    for k, v in [("payload_kind", "wrong"), ("payload_source_kind", "wrong"), ("dry_run_payload_mode", "wrong")]:
        decl = _declaration()
        decl[k] = v
        packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
        assert packet.discord_dry_run_payload_gate_available is False


def test_safety_flags_true_fails_closed():
    for f in ["payload_contains_financial_advice", "webhook_value_read_allowed", "payload_http_request_artifact_created"]:
        decl = _declaration()
        decl[f] = True
        packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
        assert packet.discord_dry_run_payload_gate_available is False


def test_later_required_boolean_false_fails_closed():
    decl = _declaration()
    decl["operator_payload_review_later_required"] = False
    packet = make_discord_dry_run_payload_gate_packet(_preflight_packet(), decl)
    assert packet.discord_dry_run_payload_gate_available is False


def test_secret_marker_in_inputs_fails_closed_without_sha256():
    preflight = _preflight_packet()
    preflight["discord_permission_probe_preflight_id"] = "private_key = my_secret"
    packet = make_discord_dry_run_payload_gate_packet(preflight, _declaration())
    assert packet.discord_dry_run_payload_gate_available is False
    assert packet.dispatch_request_package_gate_sha256 == ""


def test_module_contains_no_os_or_env_reads_and_no_dotenv():
    source = Path("live_contentops/discord_dry_run_payload_gate_v6.py").read_text(encoding="utf-8")
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

    output_file = tmp_path / "dry_run_payload_gate_packet.json"
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
    assert first["discord_dry_run_payload_gate_id"] == second["discord_dry_run_payload_gate_id"]
    assert first["discord_dry_run_payload_gate_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_DISCORD_DRY_RUN_PAYLOAD_GATE_FROM_PERMISSION_PROBE_PREFLIGHT")
    paths = [
        Path("live_contentops/discord_dry_run_payload_gate_v6.py"),
        Path("tests/test_discord_dry_run_payload_gate_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_discord_dry_run_payload_gate_packet.json").read_text(encoding="utf-8"))
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
    assert written["discord_dry_run_payload_gate_available"] is False
    assert written["discord_dry_run_payload_gate_declared_ready"] is False
    assert written["eligible_for_operator_payload_review_gate"] is False
