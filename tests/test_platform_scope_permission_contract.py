from live_contentops import platform_scope_permission_contract as contract

REQUIRED_PLATFORMS = {
    "x_profile",
    "telegram_remote_operator_inbox",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin_member_profile",
    "linkedin_organization_page",
    "threads_profile",
    "instagram_professional_account",
    "facebook_page",
    "tiktok_account",
    "youtube_channel",
}


def test_all_platform_contracts_exist_and_are_deterministic():
    first = contract.platform_scope_permission_contract_packet()
    second = contract.platform_scope_permission_contract_packet()
    assert first == second
    assert {row.platform_id for row in contract.build_platform_scope_permission_contracts()} == REQUIRED_PLATFORMS
    assert set(first["platform_ids"]) == REQUIRED_PLATFORMS
    assert first["all_platforms_covered"] is True


def test_no_live_probe_or_credential_hydration_allowed():
    for row in contract.build_platform_scope_permission_contracts():
        assert row.live_write_allowed_now is False
        assert row.read_only_probe_allowed_in_this_task is False
        assert row.credential_hydration_allowed_in_this_task is False
        assert row.no_secret_output is True
        assert "scheduler" in row.forbidden_actions_now


def test_telegram_inbox_and_channel_contracts_are_separate():
    rows = contract.contracts_by_platform_id()
    inbox = rows["telegram_remote_operator_inbox"]
    channel = rows["telegram_channel_destination"]
    assert inbox.destination_kind == "operator_inbox"
    assert inbox.public_destination_allowed_future is False
    assert "not_public_publish_destination" in inbox.required_destination_proof
    assert channel.destination_kind == "channel"
    assert channel.public_destination_allowed_future is True
    assert "bot_admin" in channel.required_permission_proofs
    assert "private_dm_route" in channel.forbidden_actions_now


def test_linkedin_member_and_organization_scope_separation():
    rows = contract.contracts_by_platform_id()
    member = rows["linkedin_member_profile"]
    org = rows["linkedin_organization_page"]
    assert member.destination_kind == "member_profile"
    assert org.destination_kind == "organization_page"
    assert "w_member_social" in member.required_scope_names_symbolic
    assert "w_organization_social" in org.required_scope_names_symbolic
    assert "organization_page_write" in member.forbidden_actions_now
    assert "member_profile_write" in org.forbidden_actions_now


def test_facebook_page_is_not_profile_or_group():
    facebook = contract.contracts_by_platform_id()["facebook_page"]
    assert facebook.destination_kind == "page"
    assert "not_personal_profile" in facebook.required_destination_proof
    assert "not_group" in facebook.required_destination_proof
    assert "personal_profile_posting" in facebook.forbidden_actions_now
    assert "group_posting" in facebook.forbidden_actions_now


def test_media_gated_platforms_are_explicit():
    rows = contract.contracts_by_platform_id()
    for platform_id in ("instagram_professional_account", "tiktok_account", "youtube_channel", "threads_profile"):
        row = rows[platform_id]
        assert row.media_permission_required is True
        assert row.later_stage_media_gated is True
    assert "instagram_content_publish" in rows["instagram_professional_account"].required_scope_names_symbolic
    assert "video.upload" in rows["tiktok_account"].required_scope_names_symbolic
    assert "youtube.upload" in rows["youtube_channel"].required_scope_names_symbolic


def test_contract_packet_is_json_safe_shape():
    packet = contract.platform_scope_permission_contract_packet()
    assert packet["live_write_allowed_now"] is False
    assert packet["read_only_probe_allowed_in_this_task"] is False
    assert packet["credential_hydration_allowed_in_this_task"] is False
    assert packet["no_secret_output"] is True
