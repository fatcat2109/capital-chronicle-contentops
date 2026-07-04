import pytest

from live_contentops.community_signal_intake_v6 import build_community_signal_packet, stable_hash, validate_community_signal_packet


def _signal(**overrides):
    base = {
        "source_channel_id": "discord_channel_operator_supplied",
        "input_mode": "manual_paste",
        "question_text": "How should readers understand real yields?",
        "theme": "real_yields_education",
        "content_potential": "high",
        "required_sources": ["treasury_yield_data"],
        "safe_angle": "Explain definitions and caveats.",
        "unsafe_angle": "Treat audience confusion as market proof.",
        "recommended_next_action": "add_to_research_backlog",
        "backlog_candidate": "real_yields_explainer",
    }
    base.update(overrides)
    return build_community_signal_packet(**base)


def test_ready_signal_needs_no_bot_scraping_or_private_messages():
    packet = _signal()

    assert packet["status"] == "READY_FOR_FEEDBACK_SUMMARY_REVIEW"
    assert packet["safety_flags"]["bot_required"] is False
    assert packet["safety_flags"]["message_scraping_performed"] is False
    assert packet["safety_flags"]["private_message_ingested"] is False
    assert packet["safety_flags"]["platform_api_used"] is False
    assert packet["community_input_is_factual_claim"] is False
    assert packet["research_grounding_required_before_claim_use"] is True
    validate_community_signal_packet(packet)


@pytest.mark.parametrize("mode", ["manual_paste", "operator_note", "future_slash_command", "future_bot_export"])
def test_allowed_input_modes(mode):
    packet = _signal(input_mode=mode)

    assert packet["blockers"] == []
    assert packet["input_mode_deferred"] is (mode.startswith("future_"))


def test_blocks_private_message_ingestion():
    packet = _signal(source_visibility="private_message")

    assert "private_message_ingestion_blocked" in packet["blockers"]
    with pytest.raises(ValueError, match="blocked_signal_packet"):
        validate_community_signal_packet(packet)


def test_blocks_secret_like_keys():
    packet = _signal(required_sources=[{"api_key": "redacted"}])

    assert "secret_like_key_blocked" in packet["blockers"]


def test_blocks_unsupported_claim_without_grounding():
    packet = _signal(question_text="Fact: this policy will happen", required_sources=[])

    assert "unsupported_claim_requires_research_grounding" in packet["blockers"]


def test_blocks_forbidden_financial_or_private_message_wording():
    packet = _signal(question_text="Reader asked for a buy signal")

    assert "forbidden_financial_or_private_message_wording_blocked" in packet["blockers"]


def test_signal_hash_changes_with_content():
    packet = _signal()
    changed = {**packet, "question_text": "Changed question"}

    assert packet["signal_hash"] != stable_hash({k: v for k, v in changed.items() if k != "signal_hash"})
