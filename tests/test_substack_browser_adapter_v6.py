"""Unit tests for Substack Playwright Browser Adapter."""
from __future__ import annotations

from pathlib import Path
from live_contentops.substack_browser_adapter_v6 import (
    copy_essential_profile,
    execute_substack_comment,
    execute_substack_edit,
    execute_substack_post,
    _split_body_visual_markers,
)


def test_execute_substack_post_dry_run():
    res = execute_substack_post(
        title="Test Title",
        subtitle="Test Subtitle",
        body_markdown="Test Body",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "substack"
    assert res["action"] == "post"
    assert res["payload_redacted"]["title"] == "Test Title"
    assert "mock_post_" in res["response"]["id"]


def test_substack_visual_markers_are_split_for_in_body_uploads():
    segments = _split_body_visual_markers("Intro\n\n[[VISUAL:primary]]\n\nBody\n\n[[VISUAL:recent_price]]")
    assert segments == [
        ("text", "Intro\n\n"),
        ("visual", "primary"),
        ("text", "\n\nBody\n\n"),
        ("visual", "recent_price"),
    ]


def test_execute_substack_post_dry_run_counts_visual_assets():
    res = execute_substack_post(
        title="Visual Title",
        body_markdown="Intro\n\n[[VISUAL:primary]]\n\nBody",
        image_assets=[{"asset_id": "primary", "local_path": "downloads/current.png"}],
        dry_run=True,
    )
    assert res["payload_redacted"]["visual_marker_count"] == 1
    assert res["payload_redacted"]["image_asset_count"] == 1


def test_execute_substack_comment_dry_run():
    res = execute_substack_comment(
        post_url_or_slug="beginnings-are-hard",
        message="Test comment content",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "substack"
    assert res["action"] == "comment"
    assert res["payload_redacted"]["target"] == "beginnings-are-hard"


def test_execute_substack_edit_dry_run():
    res = execute_substack_edit(
        post_id_or_url="205178988",
        title="Updated Title",
        dry_run=True
    )
    assert res["status"] == "DRY_RUN_PASS"
    assert res["platform"] == "substack"
    assert res["action"] == "edit"
    assert res["payload_redacted"]["post_id"] == "205178988"


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
