import importlib
import inspect
from pathlib import Path

import pytest

from live_contentops import platform_universe_registry_v2 as registry


REQUIRED_PLATFORMS = {
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

REQUIRED_PAYLOAD_CLASSES = {
    "x_short_post",
    "x_thread",
    "telegram_channel_update",
    "telegram_operator_review_message",
    "substack_newsletter_issue",
    "substack_longform_post",
    "linkedin_professional_post",
    "threads_short_post",
    "instagram_caption_asset_packet",
    "instagram_carousel_script",
    "facebook_page_post",
    "video_script_metadata_packet",
    "youtube_video_metadata_packet",
    "tiktok_video_metadata_packet",
}

FALSE_PLATFORM_FLAGS = {
    "live_dispatch_enabled",
    "platform_api_called",
    "provider_api_called",
    "credential_hydrated",
    "env_read",
    "scheduler_enabled",
    "autonomous_posting_allowed",
    "scraping_performed",
    "dm_or_reply_automation_allowed",
    "dispatch_ready",
    "public_postable",
}


def test_registry_is_deterministic():
    first = registry.build_registry_packet()
    second = registry.build_registry_packet()
    assert first == second
    assert registry.registry_checksum() == first["registry_checksum"]


def test_all_required_platform_families_exist():
    assert {entry.platform_family for entry in registry.PLATFORMS} == REQUIRED_PLATFORMS
    assert {entry.platform_id for entry in registry.PLATFORMS} == REQUIRED_PLATFORMS


def test_required_primary_brand_channels():
    assert registry.list_primary_triangle() == (
        "x",
        "telegram_channel_destination",
        "substack_newsletter",
    )
    assert registry.lookup_platform("x").priority_tier == "primary_now"
    assert registry.lookup_platform("x").platform_role == "primary_distribution"
    assert registry.lookup_platform("telegram_channel_destination").platform_role == "controlled_channel_distribution"
    assert registry.lookup_platform("substack_newsletter").platform_role == "owned_long_form"


def test_telegram_remote_operator_and_channel_do_not_collapse():
    remote = registry.lookup_platform("telegram_remote_operator")
    channel = registry.lookup_platform("telegram_channel_destination")
    assert remote.platform_id != channel.platform_id
    assert remote.platform_family != channel.platform_family
    assert remote.platform_role == "remote_operator_review"
    assert channel.platform_role == "controlled_channel_distribution"
    assert "telegram_operator_review_message" in remote.payload_classes_supported
    assert "telegram_channel_update" in channel.payload_classes_supported


def test_telegram_remote_operator_is_not_publish_destination():
    remote = registry.lookup_platform("telegram_remote_operator")
    assert remote.default_publish_mode == "remote_review_only"
    assert remote.safety_flags["manual_export_or_preview_only"] is False
    assert remote.safety_flags["future_supervised_dispatch_possible"] is False
    assert "not_publish_destination" in remote.blocked_reasons


def test_substack_manual_export_no_live_api_or_session_automation():
    substack = registry.lookup_platform("substack_newsletter")
    assert substack.priority_tier == "primary_now"
    assert substack.default_publish_mode == "manual_export_only"
    assert substack.manual_export_supported is True
    assert substack.safety_flags["platform_api_called"] is False
    assert "session_automation_blocked" in substack.blocked_reasons


def test_linkedin_secondary_next():
    linkedin = registry.lookup_platform("linkedin")
    assert linkedin.priority_tier == "secondary_next"
    assert linkedin.platform_role == "professional_credibility"


def test_threads_instagram_facebook_are_expansion_later():
    assert registry.list_expansion_platforms() == ("threads", "instagram", "facebook_page")
    for platform_id in registry.list_expansion_platforms():
        assert registry.lookup_platform(platform_id).priority_tier == "expansion_later"


def test_tiktok_youtube_video_later_only():
    for platform_id in ("tiktok", "youtube"):
        entry = registry.lookup_platform(platform_id)
        assert entry.priority_tier == "video_later"
        assert entry.platform_role == "later_video_distribution"
        assert entry.build_phase == "video_future_gate"


def test_every_platform_has_payload_class():
    for entry in registry.PLATFORMS:
        assert entry.payload_classes_supported


def test_all_required_payload_classes_exist_and_map_to_valid_platform():
    payload_ids = {entry.payload_class_id for entry in registry.PAYLOAD_CLASSES}
    assert payload_ids == REQUIRED_PAYLOAD_CLASSES
    for payload in registry.PAYLOAD_CLASSES:
        assert payload.platform_family in REQUIRED_PLATFORMS


def test_no_live_platform_flags_false_across_all_entries():
    for platform in registry.PLATFORMS:
        for flag in FALSE_PLATFORM_FLAGS:
            assert platform.safety_flags[flag] is False, platform.platform_id


def test_payload_dispatch_and_public_postable_defaults_false():
    for payload in registry.PAYLOAD_CLASSES:
        assert payload.dispatch_ready_default is False
        assert payload.public_postable_default is False


def test_unsupported_platform_fails_closed():
    with pytest.raises(registry.UnsupportedPlatformError):
        registry.lookup_platform("mastodon")


def test_unsupported_payload_class_fails_closed():
    with pytest.raises(registry.UnsupportedPayloadClassError):
        registry.lookup_payload_class("unknown_payload")


def test_payload_compatibility_check_is_deterministic():
    first = registry.validate_payload_class_compatibility("x", "x_short_post")
    second = registry.validate_payload_class_compatibility("x", "x_short_post")
    assert first == second
    assert first["compatible"] is True
    incompatible = registry.validate_payload_class_compatibility("x", "telegram_channel_update")
    assert incompatible == {
        "platform_id": "x",
        "payload_class_id": "telegram_channel_update",
        "compatible": False,
        "reason": "payload_class_not_supported_by_platform",
    }


def test_official_docs_refs_are_string_metadata_only():
    for platform in registry.PLATFORMS:
        assert platform.official_docs_refs
        assert all(isinstance(ref, str) for ref in platform.official_docs_refs)
        assert all(ref.startswith("https://") for ref in platform.official_docs_refs)


def test_module_import_has_no_side_effects_or_path_mutation():
    reloaded = importlib.reload(registry)
    assert reloaded.build_registry_packet() == registry.build_registry_packet()
    source = inspect.getsource(reloaded)
    forbidden = ("sys.path", "os.environ", "requests", "urllib", "socket", "telegram_local_adapter_contract")
    for token in forbidden:
        assert token not in source


def test_artifact_writer_writes_only_docs_automation_0174u1(tmp_path):
    packet = registry.write_artifacts(tmp_path)
    out = tmp_path / "docs" / "automation" / "0174U1"
    assert (out / "platform_universe_registry_v2_packet.json").exists()
    assert (out / "platform_universe_registry_v2.md").exists()
    assert packet["artifact_scope"] == "docs/automation/0174U1_only"
    with pytest.raises(ValueError):
        registry.write_artifacts(tmp_path, tmp_path / "docs" / "automation" / "0174U0")


def test_no_env_network_api_provider_behavior_exists():
    source = Path(registry.__file__).read_text(encoding="utf-8")
    forbidden = (
        "getenv",
        "dotenv",
        "requests.",
        "urllib.",
        "socket.",
        "subprocess",
        "TELEGRAM_BOT_TOKEN",
        "api.telegram.org",
        "provider_gateway",
    )
    for token in forbidden:
        assert token not in source
    assert registry.confirm_no_live_safety_flags()["all_clear"] is True
