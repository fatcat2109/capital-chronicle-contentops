"""Unit tests for X (Twitter) Playwright Browser Adapter."""
from __future__ import annotations

from pathlib import Path
from live_contentops.x_browser_adapter_v6 import (
    copy_essential_profile,
    execute_x_comment,
    execute_x_edit,
    execute_x_post,
)


def test_execute_x_post_dry_run():
    res = execute_x_post(
        text="Test tweet text",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "x"
    assert res["action"] == "post"
    assert res["payload_redacted"]["text"] == "Test tweet text"
    assert "x_mock_tweet_" in res["response"]["id"]


def test_execute_x_comment_dry_run():
    res = execute_x_comment(
        tweet_url_or_id="1234567890",
        text="Test reply text",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "x"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["tweet_url_or_id"] == "1234567890"


def test_execute_x_edit_dry_run():
    res = execute_x_edit(
        tweet_url_or_id="1234567890",
        new_text="Updated tweet text",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "x"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["new_text"] == "Updated tweet text"


def test_copy_essential_profile(tmp_path: Path):
    src = tmp_path / "src_profile"
    src.mkdir()
    (src / "Local State").write_text("{}", encoding="utf-8")
    default_dir = src / "Default"
    default_dir.mkdir()
    (default_dir / "Preferences").write_text("{}", encoding="utf-8")

    dest = tmp_path / "dest_profile"
    copy_essential_profile(src, dest)

    assert (dest / "Local State").exists()
    assert (dest / "Default" / "Preferences").exists()
