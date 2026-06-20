from pathlib import Path

import pytest

from live_contentops import platform_account_binding_registry_v2_contract as binding
from live_contentops import primary_platform_payload_preview_contracts as previews
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


def test_registry_builds_deterministically_and_covers_all_platforms():
    first = binding.build_platform_account_binding_registry_packet()
    second = binding.build_platform_account_binding_registry_packet()

    assert first.packet_hash == second.packet_hash
    assert first.packet_id == second.packet_id
    assert set(first.bindings_by_platform) == EXPECTED_PLATFORMS
    assert {row.platform_id for row in first.bindings} == EXPECTED_PLATFORMS
    assert len(first.bindings) == 11


def test_telegram_operator_and_channel_destinations_are_distinct():
    packet = binding.build_platform_account_binding_registry_packet()
    operator = [row for row in packet.bindings if row.platform_id == "telegram_remote_operator"]
    channel = [row for row in packet.bindings if row.platform_id == "telegram_channel_destination"]

    assert len(operator) == 1
    assert len(channel) == 1
    assert operator[0].destination_kind == "operator_inbox"
    assert channel[0].destination_kind == "channel"
    assert operator[0].binding_id != channel[0].binding_id
    assert "not_public_destination" in operator[0].blocked_reasons


def test_linkedin_member_profile_and_org_page_distinction_exists():
    packet = binding.build_platform_account_binding_registry_packet()
    linkedin = [row for row in packet.bindings if row.platform_id == "linkedin"]

    assert {row.destination_kind for row in linkedin} == {"user_profile", "organization_page"}
    org = next(row for row in linkedin if row.destination_kind == "organization_page")
    member = next(row for row in linkedin if row.destination_kind == "user_profile")
    assert org.binding_status == "missing_binding"
    assert "linkedin_organization_page_binding_missing" in org.blocked_reasons
    assert member.binding_status == "needs_identity_proof"
    assert "linkedin" in packet.missing_binding_platforms


def test_no_live_read_write_public_post_or_hydrated_credentials():
    packet = binding.build_platform_account_binding_registry_packet()

    assert packet.live_read_allowed_count == 0
    assert packet.live_write_allowed_count == 0
    assert packet.public_post_allowed_count == 0
    assert packet.credential_hydrated_count == 0
    assert packet.platform_api_called_count == 0
    for row in packet.bindings:
        assert row.live_read_allowed is False
        assert row.live_write_allowed is False
        assert row.public_post_allowed is False
        assert row.safety_flags["credential_hydrated"] is False
        assert row.safety_flags["platform_api_called"] is False
        assert row.safety_flags["network_performed"] is False
        assert row.safety_flags["env_read"] is False


def test_binding_ids_are_deterministic_and_no_secret_shaped_material_present():
    packet = binding.build_platform_account_binding_registry_packet()
    packet_text = repr(packet)

    assert binding.registry_checksum() == packet.packet_hash
    for row in packet.bindings:
        assert row.binding_id.startswith("platform_account_binding_")
        assert row.binding_hash_algorithm == "sha256"
        assert row.credential_handle_id.startswith("symbolic_credential_handle:")
    forbidden_terms = ("REPLACE_WITH_REAL", "api_key=", "token=", "password=", "bearer ", ".env")
    assert not any(term.lower() in packet_text.lower() for term in forbidden_terms)


def test_wrong_destination_preview_binding_mismatch_fails_closed():
    packet = binding.build_platform_account_binding_registry_packet()
    x_binding = next(row for row in packet.bindings if row.platform_id == "x")
    preview = previews.build_telegram_channel_update_preview(
        source_content_id="source_0174UG_mismatch",
        source_draft_id="draft_0174UG_mismatch",
        body="Local preview text.",
        citation_refs=("source:0174UG",),
        limitation_notes=("review only",),
        destination_binding_id=x_binding.binding_id,
    )

    mismatch_packet = binding.build_platform_account_binding_registry_packet(mismatch_previews=(preview,))
    updated = next(row for row in mismatch_packet.bindings if row.binding_id == x_binding.binding_id)
    assert updated.binding_status == "wrong_destination_blocked"
    assert mismatch_packet.wrong_destination_block_count == 1
    assert "wrong_destination_blocked" in updated.blocked_reasons
    assert "preview_destination_binding_mismatch" in updated.blocked_reasons


def test_u9_audit_entries_use_platform_account_binding_future_and_are_redacted():
    packet = binding.build_platform_account_binding_registry_packet()
    entries = binding.build_u9_audit_entries(packet)

    assert entries
    assert {entry.entry_family for entry in entries} == {"platform_account_binding_future"}
    assert packet.u9_audit_entry_families == tuple("platform_account_binding_future" for _ in entries)
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert all(entry.redacted_summary for entry in entries)
    assert not audit.scan_for_forbidden_material([entry.redacted_summary for entry in entries])


def test_artifact_writer_is_locked_to_0174ug(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="artifact_writer_refuses_paths_outside_docs_automation_0174UG"):
        binding.write_artifacts(repo_root=repo_root, output_dir=tmp_path)


def test_packet_safety_flags_block_provider_api_network_browser_scheduler_scraping_dm():
    packet = binding.build_platform_account_binding_registry_packet()
    forbidden_true_flags = (
        "provider_api_called",
        "platform_api_called",
        "telegram_api_called",
        "network_performed",
        "env_read",
        "browser_session_used",
        "scheduler_enabled",
        "scraping_performed",
        "dm_or_reply_automation_allowed",
        "dispatch_ready",
        "public_postable",
        "ui_generated",
    )
    for flag in forbidden_true_flags:
        assert packet.safety_flags[flag] is False
        assert all(row.safety_flags[flag] is False for row in packet.bindings)
    assert packet.all_bindings_symbolic_or_blocked is True
    assert packet.next_required_gate == "TASK_CONTENTOPS_0174UH_CREDENTIAL_HANDLE_AND_DOTENV_SECRET_BOUNDARY_V2_CONTRACT_V0"
