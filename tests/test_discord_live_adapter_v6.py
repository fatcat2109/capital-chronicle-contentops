"""Unit tests for Discord Live Adapter."""
from __future__ import annotations

import json

from live_contentops.discord_live_adapter_v6 import (
    execute_discord_comment,
    execute_discord_edit,
    execute_discord_post,
    readback_discord_post,
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


def test_readback_discord_post_proves_exact_object(monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps(
                {
                    "id": "1537129462486007910",
                    "channel_id": "1519311669216673802",
                    "guild_id": "1000000000000000000",
                    "content": "Exact text https://capitalchronicle.substack.com/p/article",
                    "embeds": [{"image": {"url": "https://example.test/image.png"}}],
                }
            ).encode()

    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *_a, **_k: Response())
    result = readback_discord_post(
        message_id="1537129462486007910",
        expected_text="Exact text",
        canonical_url="https://capitalchronicle.substack.com/p/article",
        webhook_url="https://discord.test/api/webhooks/id/token",
    )

    assert result["status"] == "SUCCESS"
    assert result["verified"] is True
    assert result["write_exists"] is True
    assert result["meaningful_media_visible"] is True
