"""Unit tests for Discord Live Adapter."""
from __future__ import annotations

from live_contentops.discord_live_adapter_v6 import (
    execute_discord_comment,
    execute_discord_edit,
    execute_discord_post,
)


def test_execute_discord_post_dry_run():
    res = execute_discord_post(
        message="Test announcement message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "post"
    assert res["payload_redacted"]["message"] == "Test announcement message"
    assert "discord_mock_msg_" in res["response"]["id"]


def test_execute_discord_comment_dry_run():
    res = execute_discord_comment(
        thread_id_or_url="1519311669216673802",
        message="Test thread comment",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["thread_id"] == "1519311669216673802"


def test_execute_discord_edit_dry_run():
    res = execute_discord_edit(
        message_id="123456789012345678",
        new_message="Updated content message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "discord"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["new_message"] == "Updated content message"
