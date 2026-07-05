"""Unit tests for Telegram Live Adapter."""
from __future__ import annotations

from live_contentops.telegram_live_adapter_v6 import (
    execute_telegram_comment,
    execute_telegram_edit,
    execute_telegram_post,
)


def test_execute_telegram_post_dry_run():
    res = execute_telegram_post(
        message="Test Telegram message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "post"
    assert res["payload_redacted"]["message"] == "Test Telegram message"
    assert "telegram_mock_msg_" in res["response"]["id"]


def test_execute_telegram_comment_dry_run():
    res = execute_telegram_comment(
        reply_to_message_id=123,
        message="Test reply text",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["reply_to_message_id"] == 123


def test_execute_telegram_edit_dry_run():
    res = execute_telegram_edit(
        message_id=123,
        new_message="Updated text message",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "telegram"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["new_message"] == "Updated text message"
