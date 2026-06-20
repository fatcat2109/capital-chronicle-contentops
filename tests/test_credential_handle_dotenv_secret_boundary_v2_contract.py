from pathlib import Path

import pytest

from live_contentops import credential_handle_dotenv_secret_boundary_v2_contract as boundary
from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


EXPECTED_PLATFORMS = {
    "x",
    "telegram_remote_operator",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin",
    "threads",
    "instagram",
    "facebook_page",
    "tiktok",
    "youtube",
}


def test_packet_builds_deterministically_and_covers_all_platform_handles():
    first = boundary.build_credential_boundary_packet()
    second = boundary.build_credential_boundary_packet()

    assert first.packet_hash == second.packet_hash
    assert first.packet_id == second.packet_id
    assert set(first.handles_by_platform) == EXPECTED_PLATFORMS
    assert {handle.platform_id for handle in first.credential_handles} == EXPECTED_PLATFORMS
    assert len(first.credential_handles) == 10


def test_telegram_remote_operator_and_channel_destination_handles_are_distinct():
    packet = boundary.build_credential_boundary_packet()
    operator = next(handle for handle in packet.credential_handles if handle.platform_id == "telegram_remote_operator")
    channel = next(handle for handle in packet.credential_handles if handle.platform_id == "telegram_channel_destination")

    assert operator.credential_handle_id != channel.credential_handle_id
    assert operator.binding_id != channel.binding_id
    assert "TELEGRAM_OPERATOR_CHAT_ID" in operator.dotenv_key_names
    assert "TELEGRAM_CHANNEL_ID" in channel.dotenv_key_names
    assert "telegram_operator_not_public_destination" in operator.blocked_reasons


def test_handle_ids_are_symbolic_and_contain_no_secret_shaped_values():
    packet = boundary.build_credential_boundary_packet()
    text = repr(packet)

    for handle in packet.credential_handles:
        assert handle.credential_handle_id == f"symbolic_credential_handle:{handle.platform_id}"
        assert handle.secret_storage_ref_redacted == f"redacted_secret_storage_ref:{handle.platform_id}"
        assert handle.handle_hash_algorithm == "sha256"
    forbidden_terms = ("REPLACE_WITH_REAL", "bearer ", "token=", "password=", "api_key=", "client_secret=")
    assert not any(term.lower() in text.lower() for term in forbidden_terms)


def test_dotenv_auto_load_only_for_explicitly_approved_future_modes():
    packet = boundary.build_credential_boundary_packet()
    x_handle = next(handle for handle in packet.credential_handles if handle.platform_id == "x")

    approved = boundary.evaluate_task_mode(
        x_handle,
        boundary.APPROVED_WRITE_MODE,
        approved=True,
        granted_scopes=x_handle.required_scopes,
    )
    local = boundary.evaluate_task_mode(x_handle, boundary.LOCAL_CONTRACT_MODE, approved=False)

    assert approved.dotenv_auto_load_allowed is True
    assert approved.runtime_secret_use_allowed is True
    assert local.dotenv_auto_load_allowed is False
    assert local.runtime_secret_use_allowed is False
    assert "fail_closed_unapproved_task" in local.blocked_reasons


def test_this_contract_reads_no_env_and_hydrates_no_credentials():
    packet = boundary.build_credential_boundary_packet()

    assert packet.env_read_count == 0
    assert packet.credential_hydrated_count == 0
    for handle in packet.credential_handles:
        assert handle.safety_flags["env_read"] is False
        assert handle.safety_flags["credential_hydrated"] is False
        assert handle.safety_flags["real_env_file_read"] is False
        assert handle.safety_flags["real_secret_value_seen"] is False


def test_platform_provider_api_and_network_counts_are_zero():
    packet = boundary.build_credential_boundary_packet()

    assert packet.platform_api_called_count == 0
    assert packet.provider_api_called_count == 0
    assert packet.network_performed_count == 0
    for flag in ("platform_api_called", "provider_api_called", "telegram_api_called", "network_performed"):
        assert packet.safety_flags[flag] is False
        assert all(handle.safety_flags[flag] is False for handle in packet.credential_handles)


def test_secret_display_logging_hash_display_commit_and_screenshot_always_false():
    packet = boundary.build_credential_boundary_packet()
    policy = packet.policy

    assert policy.secret_values_must_never_be_printed is True
    assert policy.secret_values_must_never_be_logged is True
    assert policy.secret_values_must_never_be_hashed_for_display is True
    assert policy.secret_values_must_never_be_committed is True
    assert policy.secret_values_must_never_be_screenshotted is True
    assert packet.secret_display_allowed_count == 0
    assert packet.secret_logging_allowed_count == 0
    assert packet.secret_commit_allowed_count == 0
    for handle in packet.credential_handles:
        assert handle.secret_display_allowed is False
        assert handle.secret_hash_display_allowed is False
        assert handle.secret_logging_allowed is False
        assert handle.secret_commit_allowed is False
        assert handle.safety_flags["secret_screenshot_allowed"] is False


def test_session_cookie_credential_kind_is_forbidden_and_blocked():
    forbidden = boundary.build_forbidden_session_cookie_handle("x")
    packet = boundary.build_credential_boundary_packet(handles=(forbidden,))

    assert forbidden.credential_kind == "session_cookie_forbidden"
    assert forbidden.hydration_status == "forbidden"
    assert forbidden.dotenv_auto_load_allowed is False
    assert forbidden.runtime_secret_use_allowed is False
    assert "session_cookie_forbidden_for_platform_automation" in forbidden.blocked_reasons
    assert packet.blocked_handle_count == 1


def test_substack_is_manual_export_no_api():
    packet = boundary.build_credential_boundary_packet()
    substack = next(handle for handle in packet.credential_handles if handle.platform_id == "substack_newsletter")

    assert substack.credential_kind == "manual_export_no_api"
    assert substack.dotenv_key_names == ()
    assert substack.allowed_task_modes == (boundary.MANUAL_EXPORT_MODE,)
    assert substack.dotenv_auto_load_allowed is False
    assert substack.runtime_secret_use_allowed is False
    assert "manual_export_no_api" in substack.blocked_reasons


def test_evidence_policy_allows_key_names_scopes_presence_but_forbids_values():
    policy = boundary.build_credential_boundary_policy()

    assert policy.evidence_may_report_key_names is True
    assert policy.evidence_may_report_presence is True
    assert policy.evidence_may_report_scopes is True
    assert policy.evidence_may_report_endpoint_family is True
    assert policy.evidence_may_report_request_budget is True
    assert policy.evidence_may_report_redaction_status is True
    assert policy.secret_values_must_never_be_printed is True
    assert policy.secret_values_must_never_be_logged is True


def test_unapproved_task_mode_fails_closed():
    handle = next(h for h in boundary.build_default_credential_handles() if h.platform_id == "youtube")
    result = boundary.evaluate_task_mode(handle, "local_contract_no_env", approved=False)

    assert result.hydration_status == "blocked"
    assert result.dotenv_auto_load_allowed is False
    assert result.runtime_secret_use_allowed is False
    assert "fail_closed_unapproved_task" in result.blocked_reasons


def test_missing_scope_policy_fails_closed():
    handle = next(h for h in boundary.build_default_credential_handles() if h.platform_id == "linkedin")
    result = boundary.evaluate_task_mode(handle, boundary.APPROVED_WRITE_MODE, approved=True, granted_scopes=("openid",))

    assert result.hydration_status == "blocked"
    assert result.dotenv_auto_load_allowed is False
    assert result.runtime_secret_use_allowed is False
    assert "fail_closed_scope_mismatch" in result.blocked_reasons


def test_secret_output_detector_fails_closed_for_secret_shaped_output():
    detected, status = boundary.detect_secret_shaped_output("bot token=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
    clean_detected, clean_status = boundary.detect_secret_shaped_output("redacted presence only")

    assert detected is True
    assert status == "fail_closed_secret_output_detected"
    assert clean_detected is False
    assert clean_status == "pass"


def test_u9_audit_entries_use_credential_boundary_future_and_are_redacted():
    packet = boundary.build_credential_boundary_packet()
    entries = boundary.build_u9_audit_entries(packet)

    assert entries
    assert {entry.entry_family for entry in entries} == {"credential_boundary_future"}
    assert packet.u9_audit_entry_families == tuple("credential_boundary_future" for _ in entries)
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert all(entry.redacted_summary for entry in entries)
    assert not audit.scan_for_forbidden_material([entry.redacted_summary for entry in entries])


def test_artifact_writer_touches_only_docs_automation_0174uh(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0174UH"):
        boundary.write_artifacts(repo_root=repo_root, output_dir=tmp_path)


def test_artifact_writer_outputs_packet_and_runbook_in_0174uh():
    repo_root = Path(__file__).resolve().parents[1]
    result = boundary.write_artifacts(repo_root=repo_root)

    assert result["packet_path"].endswith("docs\\automation\\0174UH\\credential_handle_dotenv_secret_boundary_v2_contract_packet.json") or result["packet_path"].endswith("docs/automation/0174UH/credential_handle_dotenv_secret_boundary_v2_contract_packet.json")
    assert result["runbook_path"].endswith("docs\\automation\\0174UH\\credential_handle_dotenv_secret_boundary_v2_contract.md") or result["runbook_path"].endswith("docs/automation/0174UH/credential_handle_dotenv_secret_boundary_v2_contract.md")


def test_cross_contract_0174ug_still_exposes_required_binding_coverage():
    registry = binding.build_platform_account_binding_registry_packet()
    packet = boundary.build_credential_boundary_packet()

    assert set(registry.bindings_by_platform) == set(packet.handles_by_platform)
    assert registry.credential_hydrated_count == 0
    assert packet.next_required_gate == "TASK_CONTENTOPS_0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V0"
