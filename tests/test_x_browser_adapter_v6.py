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


def test_old_transport_success_without_external_identity_remains_unverified():
    from live_contentops.x_browser_adapter_v6 import project_publication_outcome
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    old={"status":"SUCCESS","id":"tweet_localhash","response":{"url":"https://x.com/home"}}
    assert project_publication_outcome(old)["status"]=="UNVERIFIED"
    assert old["status"]=="SUCCESS"  # Historical receipt is not rewritten.
    forged={"status":"DISPATCH_CONFIRMED","public_object_id":"tweet_localhash",
        "reconciliation_status":"RECONCILED_CONFIRMED","public_object_url":"https://x.com/example/status/tweet_localhash"}
    assert not DurablePublicationCoordinator._confirmed_public_object(forged,destination="x")
    actual={**old,"readback":{"verified":True,"observed_public_object_id":"1234567890","observation_source":"CONTROLLED_PLATFORM_READBACK_TEST"}}
    assert project_publication_outcome(actual)["status"]=="SUCCESS"


def test_old_x_telemetry_is_projected_unverified_without_rewriting_receipt(tmp_path):
    import json
    from live_contentops.live_telemetry_v6 import TelemetryRegistry
    path=tmp_path/"telemetry.jsonl"
    raw=json.dumps({"platform_id":"x","action":"post","success":True,"response_summary":"Created post/comment ID: tweet_legacyhash"})+"\n"
    path.write_text(raw)
    event=TelemetryRegistry(str(path)).get_events()[0]
    assert event["success"] is True and event["publication_state"]=="UNVERIFIED"
    assert event["publication_confirmed"] is False and path.read_text()==raw


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
