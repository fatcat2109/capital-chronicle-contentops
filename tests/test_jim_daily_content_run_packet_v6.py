from live_contentops.jim_daily_content_run_packet_v6 import (
    build_jim_daily_content_run_packet,
)


def test_jim_daily_run_is_local_review_only():
    packet = build_jim_daily_content_run_packet()

    assert packet["operator_id"] == "jim"
    assert packet["run_status"] == "JIM_FINAL_REVIEW_REQUIRED"
    assert packet["operator_summary"] == "Jim final review required; review-only daily run packet."
    assert packet["safety_flags"]["local_only"] is True
    assert packet["safety_flags"]["jim_final_review_required"] is True
    assert packet["safety_flags"]["public_postable"] is False
    assert packet["safety_flags"]["publish_ready"] is False
    assert packet["safety_flags"]["dispatch_ready"] is False


def test_jim_daily_run_forbids_live_provider_browser_and_credential_paths():
    packet = build_jim_daily_content_run_packet()
    flags = packet["safety_flags"]

    assert flags["provider_api_called"] is False
    assert flags["network_called"] is False
    assert flags["browser_or_cdp_used"] is False
    assert flags["credential_or_env_read"] is False
    assert flags["platform_dispatch_performed"] is False
    assert flags["scheduler_enabled"] is False
    assert flags["public_url_verified"] is False
    assert packet["forbidden_actions"] == [
        "No provider API",
        "No platform dispatch",
        "No browser/CDP action",
        "No credential/env read",
        "No scheduler",
        "No public URL verification",
    ]


def test_lane_c_stays_blocked_without_artifact_evidence():
    packet = build_jim_daily_content_run_packet()
    lane_c = [item for item in packet["ideas"] if item["lane"] == "C_artifact_backed"]

    assert len(lane_c) == 1
    assert lane_c[0]["status"] == "BLOCKED"
    assert lane_c[0]["allowed_transformations"] == []
    assert "Lane C blocked without approved artifact evidence" in lane_c[0]["blockers"]
    assert "public-postable claim" in lane_c[0]["forbidden_transformations"]


def test_packet_hash_is_stable_and_changes_with_content():
    packet_a = build_jim_daily_content_run_packet()
    packet_b = build_jim_daily_content_run_packet()
    packet_c = build_jim_daily_content_run_packet(run_id="different")

    assert packet_a["packet_hash"] == packet_b["packet_hash"]
    assert packet_a["packet_hash"] != packet_c["packet_hash"]
    assert packet_a["packet_hash_algorithm"] == "sha256"
