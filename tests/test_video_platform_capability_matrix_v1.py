from __future__ import annotations

from live_contentops.video_platform_capability_matrix_v1 import (
    build_video_capability_matrix,
    build_youtube_upload_request,
    classify_youtube_surface,
)


def test_tiktok_three_app_credentials_still_not_ready() -> None:
    packet = build_video_capability_matrix({
        "CONTENTOPS_TIKTOK_CLIENT_KEY": "present",
        "CONTENTOPS_TIKTOK_CLIENT_SECRET": "present",
        "CONTENTOPS_TIKTOK_APP_ID": "present",
    })
    row = packet["rows"]["tiktok_native"]
    assert row["app_credentials_present"] is True
    assert row["oauth_authorization_status"] == "NOT_AUTHORIZED"
    assert row["adapter_implemented"] is False
    assert row["current_blocker"] == "BLOCKED_TIKTOK_OAUTH_ADAPTER_AND_APP_AUDIT_INCOMPLETE"
    assert packet["public_or_private_upload_performed"] is False


def test_youtube_short_and_long_form_classification_rules() -> None:
    assert classify_youtube_surface(width=1080, height=1920, duration_seconds=180) == "youtube_short"
    assert classify_youtube_surface(width=1080, height=1080, duration_seconds=179.9) == "youtube_short"
    assert classify_youtube_surface(width=1920, height=1080, duration_seconds=60) == "youtube_long_form"
    assert classify_youtube_surface(width=1080, height=1920, duration_seconds=181) == "youtube_long_form"


def test_youtube_upload_request_is_local_private_and_mode_bound() -> None:
    request = build_youtube_upload_request(
        title="Local capability fixture",
        description="No upload is performed.",
        width=1080,
        height=1920,
        duration_seconds=90,
        requested_mode="youtube_short",
    )
    assert request["status"] == "LOCAL_REQUEST_VALID"
    assert request["network_call_performed"] is False
    assert request["public_write_performed"] is False
    assert request["body"]["status"]["privacyStatus"] == "private"


def test_default_article_surface_remains_youtube_community() -> None:
    packet = build_video_capability_matrix({})
    assert packet["default_article_youtube_surface"] == "youtube_community"
    assert packet["video_modes_explicit_non_default"] is True
    assert packet["raw_credential_values_read_or_emitted"] is False
