from pathlib import Path

import pytest

from live_contentops import idea_to_multi_platform_draft_dry_run_contract as dry


def assert_review_only(packet):
    assert packet.writer_output.public_postable is False
    assert packet.writer_output.approval_ready is False
    assert packet.writer_output.dispatch_ready is False
    assert packet.preview_bundle.public_postable is False
    assert packet.preview_bundle.dispatch_ready is False
    assert packet.review_packet.public_postable is False
    assert packet.review_packet.approval_ready is False
    assert packet.review_packet.dispatch_ready is False
    for flag in dry.SAFETY_FALSE_FLAGS:
        assert packet.safety_flags[flag] is False


def build(text: str, **kwargs):
    return dry.build_dry_run_from_text(text, **kwargs)


def test_x_and_substack_process_dry_run_is_deterministic_and_review_only():
    text = "Draft an X thread and Substack newsletter about source trust during manual review. Limitation: review-only local dry run."
    first = build(text)
    second = build(text)

    assert first.dry_run_hash == second.dry_run_hash
    assert {p.platform_id for p in first.preview_bundle.previews} == {"x", "substack_newsletter"}
    assert first.substack_exports
    assert first.validation.validation_status == "review_only_dry_run_valid"
    assert_review_only(first)


def test_manual_external_llm_paste_preserves_review_only_contract():
    packet = build(
        "Create LinkedIn post about source trust during manual review. Limitation: local review only.",
        writer_mode="manual_external_llm_paste",
        external_title="Manual paste review title",
        external_body="Source trust note with limitations preserved for a local review-only dry run.",
    )

    assert packet.writer_output.writer_mode == "manual_external_llm_paste"
    assert packet.validation.validation_status == "review_only_dry_run_valid"
    assert packet.preview_bundle.previews[0].platform_id == "linkedin"
    assert_review_only(packet)


def test_provider_mode_is_blocked_without_provider_call():
    packet = build("Draft X post about process limits", writer_mode="provider_future_gate_blocked")

    assert packet.validation.validation_status == "blocked"
    assert "writer_output_blocked" in packet.validation.blocked_reasons
    assert packet.safety_flags["llm_provider_called"] is False
    assert_review_only(packet)


def test_advice_signal_language_blocks_pipeline():
    packet = build("Tell people to buy now as a trading signal")

    assert packet.validation.validation_status == "blocked"
    assert "advice_or_signal_forbidden_blocks_editorial_brief" in packet.validation.blocked_reasons
    assert_review_only(packet)


def test_artifact_gate_blocks_pipeline():
    packet = build("Internal alpha artifact DQR readiness report for future audience")

    assert packet.validation.validation_status == "blocked"
    assert "artifact_gate_blocks_editorial_brief" in packet.validation.blocked_reasons
    assert_review_only(packet)


def test_telegram_channel_and_remote_operator_remain_preview_only():
    channel = build("Telegram update about process limits")
    remote = build("Telegram operator inbox review message about process limits")

    assert channel.preview_bundle.previews[0].platform_id == "telegram_channel_destination"
    assert remote.preview_bundle.previews[0].platform_id == "telegram_remote_operator"
    assert "review_control_only_not_public_channel" in remote.preview_bundle.previews[0].blocked_reasons
    assert_review_only(channel)
    assert_review_only(remote)


def test_expansion_platforms_are_preview_only_or_future_blocked():
    cases = [
        ("Threads short post about process limits", "threads"),
        ("Instagram caption asset packet about process limits", "instagram"),
        ("Facebook page post about process limits", "facebook_page"),
        ("TikTok video metadata packet about process limits", "tiktok"),
        ("YouTube video metadata packet about process limits", "youtube"),
    ]
    for text, platform_id in cases:
        packet = build(text)
        assert packet.preview_bundle.previews[0].platform_id == platform_id
        assert_review_only(packet)


def test_artifact_writer_refuses_non_0174u6_path(tmp_path):
    with pytest.raises(ValueError, match="docs_automation_0174U6"):
        dry.write_artifacts(Path.cwd(), tmp_path)
