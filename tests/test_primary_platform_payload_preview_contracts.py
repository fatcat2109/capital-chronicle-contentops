import importlib
import inspect
from pathlib import Path

import pytest

from live_contentops import primary_platform_payload_preview_contracts as c


BASE = {
    "source_content_id": "source_content_test",
    "source_draft_id": "source_draft_test",
    "body": "Process note: limitations remain visible before public use.",
    "markdown_body": "## Process note\n\nLimitations remain visible before public use.",
    "citation_refs": ("source:test",),
    "limitation_notes": ("local preview only",),
    "media_manifest_id": "media_manifest_test",
}

BUILDER_EXPECTATIONS = {
    "x_short_post": (c.build_x_short_post_preview, "x"),
    "x_thread": (c.build_x_thread_preview, "x"),
    "telegram_channel_update": (c.build_telegram_channel_update_preview, "telegram_channel_destination"),
    "telegram_operator_review_message": (c.build_telegram_operator_review_message_preview, "telegram_remote_operator"),
    "substack_newsletter_issue": (c.build_substack_newsletter_issue_preview, "substack_newsletter"),
    "substack_longform_post": (c.build_substack_longform_post_preview, "substack_newsletter"),
    "linkedin_professional_post": (c.build_linkedin_professional_post_preview, "linkedin"),
    "threads_short_post": (c.build_threads_short_post_preview, "threads"),
    "instagram_caption_asset_packet": (c.build_instagram_caption_asset_packet_preview, "instagram"),
    "instagram_carousel_script": (c.build_instagram_carousel_script_preview, "instagram"),
    "facebook_page_post": (c.build_facebook_page_post_preview, "facebook_page"),
    "tiktok_video_metadata_packet": (c.build_tiktok_video_metadata_packet_preview, "tiktok"),
    "youtube_video_metadata_packet": (c.build_youtube_video_metadata_packet_preview, "youtube"),
}

NO_LIVE_FALSE_FLAGS = {
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


def test_every_supported_payload_class_can_build_preview():
    assert set(c.BUILDER_BY_PAYLOAD_CLASS) == set(BUILDER_EXPECTATIONS)
    for payload_class_id, (builder, platform_id) in BUILDER_EXPECTATIONS.items():
        preview = builder(**BASE)
        assert preview.payload_class_id == payload_class_id
        assert preview.platform_id == platform_id
        assert len(preview.payload_hash) == 64
        assert preview.payload_hash_algorithm == "sha256"


def test_preview_hash_is_deterministic():
    first = c.build_x_short_post_preview(**BASE)
    second = c.build_x_short_post_preview(**BASE)
    assert first.payload_hash == second.payload_hash
    assert first.preview_id == second.preview_id


def test_body_text_change_changes_hash():
    first = c.build_x_short_post_preview(**BASE)
    changed = c.build_x_short_post_preview(**{**BASE, "body": "Changed body text."})
    assert changed.payload_hash != first.payload_hash


def test_destination_binding_change_changes_hash():
    first = c.build_x_short_post_preview(**BASE)
    changed = c.build_x_short_post_preview(**{**BASE, "destination_binding_id": "destination_changed"})
    assert changed.payload_hash != first.payload_hash


def test_credential_handle_change_changes_hash():
    first = c.build_x_short_post_preview(**BASE)
    changed = c.build_x_short_post_preview(**{**BASE, "credential_handle_id": "credential_changed"})
    assert changed.payload_hash != first.payload_hash


def test_payload_class_change_changes_hash():
    short = c.build_x_short_post_preview(**BASE)
    thread = c.build_x_thread_preview(**{**BASE, "thread_parts": ("part one", "part two")})
    assert thread.payload_hash != short.payload_hash


def test_unsupported_platform_fails_closed():
    with pytest.raises(c.UnsupportedPlatformError):
        c.build_platform_payload_preview(platform_id="mastodon", payload_class_id="x_short_post", **BASE)


def test_unsupported_payload_class_fails_closed():
    with pytest.raises(c.UnsupportedPayloadClassError):
        c.build_platform_payload_preview(platform_id="x", payload_class_id="unknown_payload", **BASE)


def test_incompatible_platform_payload_class_fails_closed():
    with pytest.raises(c.IncompatiblePayloadClassError):
        c.build_platform_payload_preview(platform_id="x", payload_class_id="telegram_channel_update", **BASE)


def test_x_short_post_and_thread_use_x_platform():
    assert c.build_x_short_post_preview(**BASE).platform_id == "x"
    assert c.build_x_thread_preview(**{**BASE, "thread_parts": ("one", "two")}).platform_id == "x"


def test_telegram_remote_operator_and_channel_previews_are_separate():
    remote = c.build_telegram_operator_review_message_preview(**BASE)
    channel = c.build_telegram_channel_update_preview(**BASE)
    assert remote.platform_id == "telegram_remote_operator"
    assert channel.platform_id == "telegram_channel_destination"
    assert remote.payload_class_id != channel.payload_class_id
    assert "review_control_only_not_public_channel" in remote.blocked_reasons


def test_substack_previews_support_markdown_manual_export_and_block_session_automation():
    for builder in (c.build_substack_newsletter_issue_preview, c.build_substack_longform_post_preview):
        preview = builder(**BASE)
        assert preview.markdown_body
        assert preview.manual_export_supported is True
        assert preview.safety_flags["platform_api_called"] is False
        assert "session_automation_blocked" in preview.blocked_reasons


def test_linkedin_is_professional_preview_only():
    preview = c.build_linkedin_professional_post_preview(**BASE)
    assert preview.platform_id == "linkedin"
    assert "institutional_credibility" in preview.platform_warnings
    assert preview.dispatch_ready is False


def test_threads_instagram_facebook_are_expansion_previews_only():
    previews = [
        c.build_threads_short_post_preview(**BASE),
        c.build_instagram_caption_asset_packet_preview(**BASE),
        c.build_instagram_carousel_script_preview(**BASE),
        c.build_facebook_page_post_preview(**BASE),
    ]
    assert {p.platform_id for p in previews} == {"threads", "instagram", "facebook_page"}
    for preview in previews:
        assert preview.safety_flags["platform_api_called"] is False
        assert preview.preview_supported is True


def test_tiktok_youtube_are_video_metadata_only_and_future_gated():
    for builder in (c.build_tiktok_video_metadata_packet_preview, c.build_youtube_video_metadata_packet_preview):
        preview = builder(**BASE)
        assert preview.media_shape == "video_rights_metadata"
        assert "video_future_gate" in preview.blocked_reasons
        assert preview.dispatch_ready is False


def test_claimed_facts_without_citations_block():
    preview = c.build_x_short_post_preview(**{**BASE, "citation_refs": (), "source_claims_exist": True})
    result = c.validate_platform_payload_preview(preview)
    assert "missing_citation_refs_for_claimed_facts" in preview.blocked_reasons
    assert result.citation_requirements_satisfied is False
    assert result.validation_status == "blocked"


def test_grounded_or_artifact_content_without_limitations_blocks():
    preview = c.build_x_short_post_preview(
        **{**BASE, "content_lane": "grounded_news_context", "limitation_notes": ()}
    )
    result = c.validate_platform_payload_preview(preview)
    assert "missing_limitation_notes_for_grounded_or_artifact_content" in preview.blocked_reasons
    assert result.limitation_requirements_satisfied is False
    assert result.validation_status == "blocked"


def test_signal_and_advice_language_blocks():
    preview = c.build_x_short_post_preview(**{**BASE, "body": "Buy now: this is a trading signal."})
    result = c.validate_platform_payload_preview(preview)
    assert "forbidden_signal_or_advice_language" in preview.blocked_reasons
    assert result.no_signal_pass is False
    assert result.no_advice_pass is False


def test_safe_no_buy_sell_hold_signal_language_passes():
    preview = c.build_x_short_post_preview(**BASE)
    result = c.validate_platform_payload_preview(preview)
    assert result.no_signal_pass is True
    assert result.no_advice_pass is True


def test_dispatch_ready_and_public_postable_always_false():
    for builder in c.BUILDER_BY_PAYLOAD_CLASS.values():
        preview = builder(**BASE)
        assert preview.dispatch_ready is False
        assert preview.public_postable is False


def test_no_live_api_provider_credential_env_scheduler_scraping_dm_behavior_exists():
    reloaded = importlib.reload(c)
    source = inspect.getsource(reloaded)
    forbidden = (
        "os.environ",
        "getenv",
        "dotenv",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "api.telegram.org",
        "TELEGRAM_BOT_TOKEN",
        "provider_gateway",
        "sys.path",
    )
    for token in forbidden:
        assert token not in source
    preview = reloaded.build_x_short_post_preview(**BASE)
    for flag in NO_LIVE_FALSE_FLAGS:
        assert preview.safety_flags[flag] is False


def test_artifact_writer_touches_only_docs_automation_0174u2(tmp_path):
    packet = c.write_artifacts(tmp_path)
    out = tmp_path / "docs" / "automation" / "0174U2"
    assert (out / "primary_platform_payload_preview_contracts_packet.json").exists()
    assert (out / "primary_platform_payload_preview_contracts.md").exists()
    assert packet["artifact_scope"] == "docs/automation/0174U2_only"
    with pytest.raises(ValueError):
        c.write_artifacts(tmp_path, tmp_path / "docs" / "automation" / "0174U1")


def test_contract_packet_is_deterministic_and_registry_linked():
    first = c.build_contract_packet()
    second = c.build_contract_packet()
    assert first == second
    assert c.preview_contract_checksum() == first["preview_contract_checksum"]
    assert first["registry_checksum"]


def test_validation_result_model_fields_are_populated():
    preview = c.build_x_short_post_preview(**BASE)
    result = c.validate_platform_payload_preview(preview)
    assert result.preview_id == preview.preview_id
    assert result.registry_platform_match is True
    assert result.registry_payload_match is True
    assert result.payload_class_compatible is True
    assert result.body_shape_valid is True
    assert result.no_live_defaults_pass is True
