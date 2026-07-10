"""Redacted, non-posting capability audit for TikTok and YouTube video lanes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.video_platform_capability_matrix.v1"
TIKTOK_APP_KEYS = (
    "CONTENTOPS_TIKTOK_CLIENT_KEY",
    "CONTENTOPS_TIKTOK_CLIENT_SECRET",
    "CONTENTOPS_TIKTOK_APP_ID",
)
TIKTOK_OAUTH_KEYS = (
    "CONTENTOPS_TIKTOK_REFRESH_TOKEN",
    "CONTENTOPS_TIKTOK_OPEN_ID",
    "CONTENTOPS_TIKTOK_ACCESS_TOKEN",
)
YOUTUBE_KEYS = (
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
    "YOUTUBE_CHANNEL_ID",
)


def _presence(keys: Sequence[str], environ: Mapping[str, str]) -> dict[str, bool]:
    return {key: bool(str(environ.get(key) or "").strip()) for key in keys}


def _persistent_windows_presence(keys: Sequence[str]) -> dict[str, bool]:
    presence = {key: False for key in keys}
    if os.name != "nt":
        return presence
    try:
        import winreg
    except ImportError:
        return presence
    locations = (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
    )
    for hive, path in locations:
        try:
            with winreg.OpenKey(hive, path) as handle:
                for key in keys:
                    try:
                        value, _kind = winreg.QueryValueEx(handle, key)
                    except FileNotFoundError:
                        continue
                    presence[key] = presence[key] or bool(str(value or "").strip())
        except OSError:
            continue
    return presence


def classify_youtube_surface(*, width: int, height: int, duration_seconds: float) -> str:
    if min(width, height) <= 0 or duration_seconds <= 0:
        return "INVALID_MEDIA_METADATA"
    if width <= height and duration_seconds <= 180:
        return "youtube_short"
    return "youtube_long_form"


def build_youtube_upload_request(
    *,
    title: str,
    description: str,
    width: int,
    height: int,
    duration_seconds: float,
    requested_mode: str,
) -> dict[str, Any]:
    classified = classify_youtube_surface(width=width, height=height, duration_seconds=duration_seconds)
    valid_modes = {"youtube_short", "youtube_long_form"}
    blockers = []
    if requested_mode not in valid_modes:
        blockers.append("explicit_video_mode_required")
    if classified == "INVALID_MEDIA_METADATA":
        blockers.append("valid_media_metadata_required")
    if requested_mode in valid_modes and requested_mode != classified:
        blockers.append(f"surface_classification_mismatch:{classified}")
    if not title.strip() or not description.strip():
        blockers.append("title_and_description_required")
    return {
        "status": "LOCAL_REQUEST_VALID" if not blockers else "LOCAL_REQUEST_BLOCKED",
        "network_call_performed": False,
        "public_write_performed": False,
        "http_method": "POST",
        "endpoint": "https://www.googleapis.com/upload/youtube/v3/videos",
        "parts": ["snippet", "status"],
        "required_scope": "https://www.googleapis.com/auth/youtube.upload",
        "classified_surface": classified,
        "requested_mode": requested_mode,
        "body": {
            "snippet": {"title": title, "description": description, "categoryId": "25"},
            "status": {"privacyStatus": "private"},
        },
        "media": {"width": width, "height": height, "duration_seconds": duration_seconds, "mime_family": "video/*"},
        "blockers": blockers,
    }


def build_video_capability_matrix(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = dict(os.environ if environ is None else environ)
    tiktok_app = _presence(TIKTOK_APP_KEYS, env)
    tiktok_oauth = _presence(TIKTOK_OAUTH_KEYS, env)
    youtube = _presence(YOUTUBE_KEYS, env)
    if environ is None:
        persistent = _persistent_windows_presence((*TIKTOK_APP_KEYS, *TIKTOK_OAUTH_KEYS, *YOUTUBE_KEYS))
        tiktok_app = {key: tiktok_app[key] or persistent[key] for key in TIKTOK_APP_KEYS}
        tiktok_oauth = {key: tiktok_oauth[key] or persistent[key] for key in TIKTOK_OAUTH_KEYS}
        youtube = {key: youtube[key] or persistent[key] for key in YOUTUBE_KEYS}
    tiktok_app_complete = all(tiktok_app.values())
    tiktok_oauth_complete = all(tiktok_oauth.values())
    youtube_oauth_complete = all(youtube[key] for key in YOUTUBE_KEYS[:3])
    youtube_channel_ready = youtube["YOUTUBE_CHANNEL_ID"]
    rows = {
        "tiktok_native": {
            "product_surface": "TikTok native video/photo Content Posting API",
            "adapter_implemented": False,
            "credential_names_expected": list((*TIKTOK_APP_KEYS, *TIKTOK_OAUTH_KEYS)),
            "credential_presence": {**tiktok_app, **tiktok_oauth},
            "app_credentials_present": tiktok_app_complete,
            "oauth_authorization_status": "AUTHORIZED" if tiktok_oauth_complete else "NOT_AUTHORIZED",
            "required_scopes": ["user.info.basic", "video.upload", "video.publish"],
            "account_identity_readiness": False,
            "upload_transport": "NOT_IMPLEMENTED_CONTENT_POSTING_API",
            "test_mode_available": False,
            "public_posting_approval_status": "NOT_APPROVED",
            "current_blocker": "BLOCKED_TIKTOK_OAUTH_ADAPTER_AND_APP_AUDIT_INCOMPLETE",
            "blocker_details": [
                "redirect_callback_not_implemented",
                "account_oauth_authorization_missing",
                "refresh_token_missing",
                "open_id_missing",
                "runtime_access_token_refresh_missing",
                "native_content_posting_adapter_missing",
                "app_audit_approval_missing",
            ],
            "next_operator_action": "Complete redirect/callback registration and TikTok user authorization only after the native adapter and audit plan are reviewed.",
        },
        "youtube_long_form": {
            "product_surface": "YouTube long-form video upload",
            "adapter_implemented": False,
            "credential_names_expected": list(YOUTUBE_KEYS),
            "credential_presence": youtube,
            "oauth_authorization_status": "REFRESH_TOKEN_PRESENT" if youtube_oauth_complete else "NOT_AUTHORIZED",
            "required_scopes": ["https://www.googleapis.com/auth/youtube.upload"],
            "account_identity_readiness": youtube_channel_ready,
            "upload_transport": "videos.insert_resumable_request_not_runtime_wired",
            "test_mode_available": True,
            "public_posting_approval_status": "CAPABILITY_AUDIT_ONLY",
            "current_blocker": "BLOCKED_YOUTUBE_LONG_FORM_EXPLICIT_MODE_AND_AUDIT_REQUIRED",
            "next_operator_action": "Review a private-only videos.insert adapter, verify channel binding, quota, and API project audit before any execution approval.",
        },
        "youtube_shorts": {
            "product_surface": "YouTube Shorts upload",
            "adapter_implemented": True,
            "credential_names_expected": list(YOUTUBE_KEYS),
            "credential_presence": youtube,
            "oauth_authorization_status": "REFRESH_TOKEN_PRESENT" if youtube_oauth_complete else "NOT_AUTHORIZED",
            "required_scopes": ["https://www.googleapis.com/auth/youtube.upload"],
            "account_identity_readiness": youtube_channel_ready,
            "upload_transport": "explicit_non_default_edge_studio_adapter",
            "test_mode_available": True,
            "surface_rule": "square_or_vertical_and_duration_at_most_180_seconds",
            "public_posting_approval_status": "CAPABILITY_AUDIT_ONLY",
            "current_blocker": "BLOCKED_YOUTUBE_SHORTS_PUBLIC_EXECUTION_NOT_AUTHORIZED",
            "next_operator_action": "Keep the adapter outside the article runner and require separate content, rights, metadata, and public-write approval.",
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": "VIDEO_CAPABILITY_AUDIT_COMPLETE_NO_POSTING",
        "default_article_youtube_surface": "youtube_community",
        "video_modes_explicit_non_default": True,
        "network_call_performed": False,
        "public_or_private_upload_performed": False,
        "raw_credential_values_read_or_emitted": False,
        "rows": rows,
        "official_rule_sources": {
            "youtube_shorts": "https://support.google.com/youtube/answer/15424877",
            "youtube_videos_insert": "https://developers.google.com/youtube/v3/docs/videos/insert",
            "tiktok_content_posting": "https://developers.tiktok.com/doc/content-posting-api-get-started/",
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a redacted non-posting video capability matrix.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = build_video_capability_matrix()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": packet["classification"],
        "tiktok": packet["rows"]["tiktok_native"]["current_blocker"],
        "youtube_long_form": packet["rows"]["youtube_long_form"]["current_blocker"],
        "youtube_shorts": packet["rows"]["youtube_shorts"]["current_blocker"],
        "public_or_private_upload_performed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
