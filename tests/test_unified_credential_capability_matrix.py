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


def test_matrix_has_required_platform_rows_and_adapter_taxonomy():
    packet = matrix.build_matrix([])
    rows = packet["platform_rows"]
    assert {row["platform"] for row in rows} == REQUIRED_PLATFORMS
    assert {row["adapter_class"] for row in rows} >= {
        "webhook_adapter",
        "official_api_adapter",
        "browser_cdp_adapter",
        "manual_fallback_adapter",
        "deferred_adapter",
    }


def test_env_parser_reports_only_key_names_and_status(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DISCORD_WEBHOOK_URL=secret-url\n"
        "TELEGRAM_BOT_TOKEN=secret-token\n"
        "MALFORMED LINE\n",
        encoding="utf-8",
    )
    packet = matrix.build_matrix([env_file])
    rendered = json.dumps(packet, sort_keys=True)
    assert "secret-url" not in rendered
    assert "secret-token" not in rendered
    assert "DISCORD_WEBHOOK_URL" in packet["env_inspection"]["present_key_names"]
    assert packet["env_inspection"]["malformed"] == [
        {"file": ".env", "line_number": 3, "key_name": "UNPARSEABLE_LINE"}
    ]


def test_deferred_platforms_are_not_failures():
    packet = matrix.build_matrix([])
    deferred = {
        row["platform"]: row
        for row in packet["platform_rows"]
        if row["adapter_class"] == "deferred_adapter"
    }
    assert deferred["LinkedIn personal deferred"]["blocker_class"] == "deferred_by_plan"
    assert deferred["LinkedIn organization deferred"]["blocker_class"] == "deferred_by_plan"
    assert deferred["TikTok deferred"]["blocker_class"] == "deferred_by_plan"
    assert all(row["live_write_eligible"] is False for row in deferred.values())


def test_redaction_policy_forbids_sensitive_outputs():
    packet = matrix.build_matrix([])
    assert packet["redaction_policy"] == {
        "raw_secret_output": False,
        "webhook_url_output": False,
        "token_length_prefix_suffix_hash_output": False,
        "browser_cookie_storage_read": False,
    }
