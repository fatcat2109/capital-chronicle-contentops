import json
from pathlib import Path

from live_contentops import unified_credential_capability_matrix as matrix


REQUIRED_PLATFORMS = {
    "Discord webhooks",
    "Discord guild/server/channel/role IDs",
    "Discord bot deferred",
    "Telegram operator inbox",
    "Telegram channel",
    "Substack browser profile/publication metadata",
    "Meta Graph",
    "Facebook Page",
    "Instagram Business",
    "Threads separate app/user",
    "YouTube OAuth/client credentials",
    "X manual",
    "LinkedIn personal deferred",
    "LinkedIn organization deferred",
    "TikTok deferred",
    "9router / AI provider",
    "Vertex fallback / service account path",
    "Browser operator profiles",
    "Media dirs",
    "Approval/outbox/audit paths",
}


def row(packet: dict, platform: str) -> dict:
    return next(item for item in packet["platform_rows"] if item["platform"] == platform)


def write_env(tmp_path: Path, text: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(text, encoding="utf-8")
    return env_file


def test_matrix_has_required_platform_rows_and_adapter_taxonomy():
    packet = matrix.build_matrix([])
    rows = packet["platform_rows"]
    assert {item["platform"] for item in rows} == REQUIRED_PLATFORMS
    assert {item["adapter_class"] for item in rows} >= {
        "webhook_adapter",
        "official_api_adapter",
        "browser_cdp_adapter",
        "manual_fallback_adapter",
        "deferred_adapter",
    }
    assert all("live_write_allowed_now" in item for item in rows)


def test_env_parser_reports_only_key_names_and_status(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=secret-url\n"
        "TELEGRAM_BOT_TOKEN=secret-token\n"
        "EMPTY_KEY=\n"
        "MALFORMED LINE\n",
    )
    packet = matrix.build_matrix([env_file])
    rendered = json.dumps(packet, sort_keys=True)
    assert "secret-url" not in rendered
    assert "secret-token" not in rendered
    assert "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL" in packet["env_inspection"]["present_key_names"]
    assert packet["env_inspection"]["key_value_status"]["EMPTY_KEY"] == "blank"
    assert packet["env_inspection"]["malformed"] == [
        {"file": ".env", "line_number": 4, "key_name": "UNPARSEABLE_LINE"}
    ]
    assert packet["env_inspection"]["malformed_summary"] == {
        "count": 1,
        "files": [".env"],
        "key_name": "UNPARSEABLE_LINE",
    }


def test_discord_specific_webhook_aliases_mark_ready_without_leaking_values(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=https://example.invalid/a\n"
        "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL=https://example.invalid/b\n"
        "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL=https://example.invalid/c\n",
    )
    packet = matrix.build_matrix([env_file])
    discord = row(packet, "Discord webhooks")
    rendered = json.dumps(packet, sort_keys=True)
    assert discord["capability_class"] == "ready_webhook"
    assert discord["adapter_class"] == "webhook_adapter"
    assert discord["live_write_eligible"] is True
    assert discord["live_write_allowed_now"] is False
    assert discord["key_status"]["DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"] is True
    assert "https://example.invalid" not in rendered
    assert len("https://example.invalid/a").__str__() not in rendered


def test_generic_missing_discord_webhook_url_no_longer_false_negative(tmp_path: Path):
    env_file = write_env(tmp_path, "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL=https://example.invalid/substack\n")
    discord = row(matrix.build_matrix([env_file]), "Discord webhooks")
    assert discord["key_status"]["DISCORD_WEBHOOK_URL"] is False
    assert discord["capability_class"] == "ready_webhook"
    assert discord["live_write_eligible"] is True


def test_discord_specific_channel_and_role_keys_satisfy_binding_row(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_SERVER_ID=server-id\n"
        "DISCORD_ANNOUNCEMENTS_CHANNEL_ID=channel-id\n"
        "DISCORD_ROLE_FOUNDER=role-id\n",
    )
    discord = row(matrix.build_matrix([env_file]), "Discord guild/server/channel/role IDs")
    assert discord["capability_class"] == "ready_api"
    assert discord["key_status"]["DISCORD_ANNOUNCEMENTS_CHANNEL_ID"] is True
    assert discord["key_status"]["DISCORD_ROLE_FOUNDER"] is True
    assert "DISCORD_CHANNEL_ID" not in discord["key_names"]
    assert "DISCORD_ROLE_ID" not in discord["key_names"]


def test_nine_router_api_key_marks_provider_present_without_leaking_value(tmp_path: Path):
    env_file = write_env(tmp_path, "NINE_ROUTER_API_KEY=nr-secret\nNINE_ROUTER_MODEL=model-name\n")
    packet = matrix.build_matrix([env_file])
    provider = row(packet, "9router / AI provider")
    rendered = json.dumps(packet, sort_keys=True)
    assert provider["capability_class"] == "provider_present_live_gate_required"
    assert provider["blocker_class"] == "live_gate_or_scope_proof_required"
    assert provider["live_write_allowed_now"] is False
    assert provider["key_status"]["NINE_ROUTER_API_KEY"] is True
    assert "nr-secret" not in rendered
    assert "model-name" not in rendered


def test_threads_user_access_token_alias_marks_threads_present(tmp_path: Path):
    env_file = write_env(tmp_path, "THREADS_USER_ACCESS_TOKEN=threads-secret\n")
    packet = matrix.build_matrix([env_file])
    threads = row(packet, "Threads separate app/user")
    meta = row(packet, "Meta Graph")
    rendered = json.dumps(packet, sort_keys=True)
    assert threads["key_status"]["THREADS_USER_ACCESS_TOKEN"] is True
    assert threads["capability_class"] == "credential_present_scope_proof_required"
    assert meta["capability_class"] == "deferred_credentials_missing"
    assert "threads-secret" not in rendered


def test_instagram_business_account_plus_meta_token_requires_scope_proof(tmp_path: Path):
    env_file = write_env(tmp_path, "INSTAGRAM_BUSINESS_ACCOUNT_ID=ig-id\nMETA_ACCESS_TOKEN=meta-secret\n")
    packet = matrix.build_matrix([env_file])
    instagram = row(packet, "Instagram Business")
    assert instagram["capability_class"] == "credential_present_scope_proof_required"
    assert instagram["blocker_class"] == "live_gate_or_scope_proof_required"
    assert instagram["live_write_eligible"] is False
    assert instagram["live_write_allowed_now"] is False


def test_youtube_blank_refresh_token_detection_without_value_output(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "YOUTUBE_CLIENT_ID=yt-client-secret-value\n"
        "YOUTUBE_CLIENT_SECRET=yt-client-secret-material\n"
        "YOUTUBE_REFRESH_TOKEN=\n",
    )
    packet = matrix.build_matrix([env_file])
    youtube = row(packet, "YouTube OAuth/client credentials")
    rendered = json.dumps(packet, sort_keys=True)
    assert youtube["key_value_status"]["YOUTUBE_REFRESH_TOKEN"] == "blank"
    assert youtube["capability_class"] == "needs_oauth_refresh_token"
    assert youtube["blocker_class"] == "blank_or_missing_oauth_refresh_token"
    assert "yt-client-secret-value" not in rendered
    assert "yt-client-secret-material" not in rendered


def test_live_write_allowed_now_is_false_for_all_rows(tmp_path: Path):
    env_file = write_env(
        tmp_path,
        "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL=https://example.invalid/a\n"
        "NINE_ROUTER_API_KEY=nr-secret\n"
        "THREADS_USER_ACCESS_TOKEN=threads-secret\n",
    )
    packet = matrix.build_matrix([env_file])
    assert all(item["live_write_allowed_now"] is False for item in packet["platform_rows"])


def test_deferred_platforms_are_not_failures():
    packet = matrix.build_matrix([])
    deferred = {
        item["platform"]: item
        for item in packet["platform_rows"]
        if item["adapter_class"] == "deferred_adapter"
    }
    assert deferred["LinkedIn personal deferred"]["blocker_class"] == "deferred_by_plan"
    assert deferred["LinkedIn organization deferred"]["blocker_class"] == "deferred_by_plan"
    assert deferred["TikTok deferred"]["blocker_class"] == "deferred_by_plan"
    assert all(item["live_write_eligible"] is False for item in deferred.values())


def test_redaction_policy_forbids_sensitive_outputs():
    packet = matrix.build_matrix([])
    assert packet["redaction_policy"] == {
        "raw_secret_output": False,
        "webhook_url_output": False,
        "token_length_prefix_suffix_hash_output": False,
        "browser_cookie_storage_read": False,
        "malformed_line_output": False,
    }
