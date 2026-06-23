import pytest

from live_contentops import platform_universe_registry_v2 as registry

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


def test_registry_is_deterministic():
    first = registry.platform_universe_registry_v2_packet()
    second = registry.platform_universe_registry_v2_packet()
    assert first == second


def test_all_required_platform_ids_exist():
    assert {entry.platform_id for entry in registry.PLATFORMS} == REQUIRED_PLATFORMS


def test_telegram_remote_operator_inbox_and_channel_are_separate():
    inbox = registry.lookup_platform("telegram_remote_operator_inbox")
    channel = registry.lookup_platform("telegram_channel_destination")
    assert inbox.platform_id != channel.platform_id
    assert inbox.platform_role == "remote_operator_review"
    assert channel.platform_role == "controlled_channel_distribution"


def test_linkedin_member_and_organization_are_separate():
    member = registry.lookup_platform("linkedin_member_profile")
    org = registry.lookup_platform("linkedin_organization_page")
    assert member.platform_id != org.platform_id
    assert member.destination_kind == "member_profile"
    assert org.destination_kind == "organization_page"


def test_substack_is_manual_export_first():
    substack = registry.lookup_platform("substack_newsletter")
    assert substack.manual_export_supported is True
    assert substack.browser_assisted_lab_supported is True
    assert substack.default_current_mode == "manual_export_only"


def test_tiktok_and_youtube_are_later_stage():
    for pid in ("tiktok_account", "youtube_channel"):
        p = registry.lookup_platform(pid)
        assert p.strategy_tier == "later"
        assert p.platform_role == "later_video_distribution"


def test_no_live_write_allowed_for_any_platform():
    for p in registry.PLATFORMS:
        assert p.live_write_allowed_now is False
        assert p.dispatchable_now is False
        assert p.public_postable_now is False
        assert p.no_autonomous_reply_dm_scheduler_scraping is True


def test_assert_no_live_write_allowed_helper():
    registry.assert_no_live_write_allowed(registry.platform_universe_registry_v2_packet())

    bad_packet = {
        "platform_entries": [
            {"platform_id": "test", "live_write_allowed_now": True, "dispatchable_now": False, "public_postable_now": False}
        ]
    }
    with pytest.raises(AssertionError):
        registry.assert_no_live_write_allowed(bad_packet)


def test_unsupported_platform_fails_closed():
    with pytest.raises(registry.UnsupportedPlatformError):
        registry.lookup_platform("mastodon")


def test_no_secret_shaped_strings_check():
    registry.assert_no_secret_shaped_material(registry.platform_universe_registry_v2_packet())

    with pytest.raises(AssertionError):
        registry.assert_no_secret_shaped_material("123456789:ABCdefGHijkLMNopqRSTuvwXYZ123456789")
