import pytest

from live_contentops.campaign_v6 import build_campaign, validate_campaign, write_sample_campaign


def test_ready_manual_and_deferred_platforms_can_coexist():
    packet = build_campaign()

    assert packet["packet_kind"] == "campaign_object_v0"
    assert packet["status"] == "REVIEW_WITH_MANUAL_OR_DEFERRED_PLATFORMS"
    assert packet["platform_state_counts"] == {"ready": 1, "manual": 2, "deferred": 1}
    assert set(packet["selected_platforms"]) == {"substack", "discord", "x", "linkedin"}


def test_discord_drop_is_first_class_for_discord_campaign():
    packet = build_campaign(selected_platforms=["discord"], outbox_entries=[{
        "outbox_entry_id": "outbox_discord_drop_001",
        "platform": "discord",
        "platform_state": "ready",
        "payload_hash_locked": True,
        "dispatchable": False,
    }])

    assert packet["discord_drop_ids"] == ["discord_drop_redacted_001"]
    assert packet["status"] == "READY_FOR_OPERATOR_CAMPAIGN_REVIEW"


def test_missing_discord_drop_blocks_review_status():
    packet = build_campaign(discord_drop_ids=[])

    assert packet["status"] == "REVIEW_WITH_MANUAL_OR_DEFERRED_PLATFORMS"
    assert "discord_drop_missing" in packet["blockers"]
    with pytest.raises(ValueError, match="discord_drop_missing"):
        bad = dict(packet)
        bad["discord_drop_ids"] = []
        validate_campaign(bad)


def test_bundle_review_requires_all_hashes_locked():
    entries = [{
        "outbox_entry_id": "outbox_discord_drop_001",
        "platform": "discord",
        "platform_state": "ready",
        "payload_hash_locked": False,
        "dispatchable": False,
    }]

    packet = build_campaign(selected_platforms=["discord"], outbox_entries=entries)

    assert packet["status"] == "BLOCKED_MISSING_EXACT_HASH_LOCKS"
    assert "exact_hash_locks_missing_for_bundle_review" in packet["blockers"]


def test_per_payload_review_can_remain_review_only_with_manual_platforms():
    entries = [{
        "outbox_entry_id": "outbox_x_manual_001",
        "platform": "x",
        "platform_state": "manual",
        "payload_hash_locked": False,
        "dispatchable": False,
    }]

    packet = build_campaign(selected_platforms=["x"], discord_drop_ids=[], outbox_entries=entries, approval_mode="per_payload_review")

    assert packet["status"] == "REVIEW_WITH_MANUAL_OR_DEFERRED_PLATFORMS"
    assert "exact_hash_locks_missing_for_bundle_review" not in packet["blockers"]


def test_missing_canonical_article_blocks():
    packet = build_campaign(canonical_article_id=None)

    assert packet["status"] == "BLOCKED_MISSING_CANONICAL_ARTICLE"
    assert "canonical_article_missing" in packet["blockers"]


def test_secret_like_input_key_blocks_and_does_not_leak_value():
    packet = build_campaign(metrics_records=[{"api_token": "do-not-output"}])

    assert packet["status"] == "BLOCKED_UNSAFE_OR_SECRET_LIKE_INPUT"
    assert "secret_like_input_key_blocked" in packet["blockers"]
    assert "do-not-output" not in str(packet)


def test_forbidden_financial_advice_wording_blocks():
    packet = build_campaign(feedback_summary={"note": "Reader asked for a buy signal."})

    assert packet["status"] == "BLOCKED_UNSAFE_OR_SECRET_LIKE_INPUT"
    assert "forbidden_financial_advice_or_signal_wording" in packet["blockers"]


def test_output_asserts_no_live_network_provider_browser_env_credential_claims():
    packet = build_campaign()

    for key, value in packet["safety_flags"].items():
        assert value is False, key
    for key, value in packet["non_readiness_claims"].items():
        assert value is False, key
    assert packet["blocked_controls"] == ["approve", "dispatch", "publish", "schedule", "send", "scrape", "reply", "dm", "react"]


def test_sample_writer_creates_deterministic_packet_and_report(tmp_path, monkeypatch):
    import live_contentops.campaign_v6 as campaign_v6

    out_dir = tmp_path / "campaign"
    monkeypatch.setattr(campaign_v6, "OUT_DIR", out_dir)
    monkeypatch.setattr(campaign_v6, "SAMPLE_PATH", out_dir / "sample_campaign.json")
    monkeypatch.setattr(campaign_v6, "REPORT_PATH", out_dir / "implementation_report.md")

    packet = write_sample_campaign()

    assert packet["campaign_id"].startswith("campaign_")
    assert (out_dir / "sample_campaign.json").exists()
    assert (out_dir / "implementation_report.md").exists()
    assert "TASK_CONTENTOPS_V6_MEDIA_RIGHTS_AND_INTERNAL_VISUAL_CARD_SYSTEM_V0" in (out_dir / "implementation_report.md").read_text(encoding="utf-8")
