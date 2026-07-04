from live_contentops.community_signal_intake_v6 import build_community_signal_packet, sample_community_signal_packets
from live_contentops.discord_feedback_summary_v6 import build_discord_feedback_summary, validate_discord_feedback_summary


def test_summary_groups_ready_signals_without_bot_or_scraping():
    summary = build_discord_feedback_summary()

    assert summary["summary_method"] == "deterministic_theme_grouping_no_llm"
    assert summary["summary_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW_ONLY"
    assert summary["safety_flags"]["bot_required"] is False
    assert summary["safety_flags"]["message_scraping_performed"] is False
    assert summary["safety_flags"]["private_message_ingested"] is False
    assert summary["safety_flags"]["platform_api_used"] is False
    assert summary["source_signal_packet_ids"]
    assert summary["requested_topics"] == sorted(summary["requested_topics"])
    validate_discord_feedback_summary(summary)


def test_llm_is_deferred_and_cannot_approve_next_content():
    summary = build_discord_feedback_summary()

    assert summary["llm_summary_allowed_later"] is True
    assert summary["llm_provider_call_made"] is False
    assert summary["llm_cannot_approve_next_content"] is True
    assert summary["safety_flags"]["next_content_approved_by_llm"] is False
    assert summary["safety_flags"]["next_content_approved_by_system"] is False


def test_backlog_candidates_require_research_grounding_before_claim_use():
    summary = build_discord_feedback_summary()

    assert summary["recommended_content_backlog"]
    for candidate in summary["recommended_content_backlog"]:
        assert candidate["research_grounding_required_before_claim_use"] is True
        assert candidate["operator_review_required_before_next_content"] is True
        assert candidate["ready_for_article_claim_use"] is False


def test_summary_hash_changes_when_source_signal_hash_changes():
    signals = sample_community_signal_packets()
    original = build_discord_feedback_summary(signals)
    changed_signal = {**signals[0], "signal_hash": "0" * 64}
    changed = build_discord_feedback_summary([changed_signal, signals[1]])

    assert original["summary_hash"] != changed["summary_hash"]


def test_blocked_signal_is_excluded_from_backlog_and_flagged():
    blocked = build_community_signal_packet(
        source_channel_id="discord_private_operator_supplied",
        input_mode="manual_paste",
        question_text="Private message asks for financial advice",
        theme="blocked_private_financial",
        content_potential="none",
        required_sources=[],
        safe_angle="Do not ingest private messages.",
        unsafe_angle="Use private message as source.",
        recommended_next_action="block",
        backlog_candidate="blocked",
        source_visibility="private_message",
    )
    summary = build_discord_feedback_summary([*sample_community_signal_packets(), blocked])

    assert blocked["signal_packet_id"] in summary["blocked_signal_packet_ids"]
    assert "blocked_signals_present" in summary["moderation_flags"]
    assert all(item["theme"] != "blocked_private_financial" for item in summary["recommended_content_backlog"])


def test_summary_is_deterministic_for_same_input():
    signals = sample_community_signal_packets()

    assert build_discord_feedback_summary(signals) == build_discord_feedback_summary(signals)
