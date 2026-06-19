from pathlib import Path

import pytest

from live_contentops import content_idea_intent_parser_contract as parser


def raw(text: str, **kwargs):
    return parser.build_raw_operator_input(text, **kwargs)


def idea(text: str, **kwargs):
    return parser.build_content_idea_packet(raw(text, **kwargs))


def intent(text: str, **kwargs):
    r = raw(text, **kwargs)
    i = parser.build_content_idea_packet(r)
    return parser.parse_local_intent(r, i)


def assert_all_safety_false(flags: dict[str, bool]):
    for flag in parser.SAFETY_FALSE_FLAGS:
        assert flags[flag] is False
    assert flags["deterministic_local_only"] is True


def test_raw_input_redaction_and_hash_are_deterministic():
    first = raw("Idea from user@example.com token=abc123 about source trust")
    second = raw("Idea from user@example.com token=abc123 about source trust")

    assert first.raw_text_hash == second.raw_text_hash
    assert first.raw_input_id == second.raw_input_id
    assert "user@example.com" not in first.raw_text_redacted
    assert "token=abc123" not in first.raw_text_redacted
    assert "[REDACTED]" in first.raw_text_redacted
    assert_all_safety_false(first.safety_flags)


def test_idea_text_creates_review_only_packet():
    packet = idea("Idea: process note about why limitations stay visible")

    assert packet.idea_id.startswith("idea_")
    assert packet.content_lane == "pre_alpha_general_process"
    assert packet.readiness_state == "idea_ready_for_review"
    assert packet.human_review_required is True
    assert packet.public_postable is False
    assert packet.artifact_backed_claims_allowed is False
    assert_all_safety_false(packet.safety_flags)


def test_linkedin_target_extracted():
    packet = idea("Create a professional LinkedIn post about source trust")

    assert packet.requested_platforms == ("linkedin",)
    assert "linkedin_professional_post" in packet.requested_output_shapes


def test_x_thread_target_and_shape_extracted():
    packet = idea("Create an X thread on trust before forecast")

    assert "x" in packet.requested_platforms
    assert "x_thread" in packet.requested_output_shapes


def test_substack_newsletter_target_and_shape_extracted():
    packet = idea("Draft a Substack newsletter about data sufficiency")

    assert packet.requested_platforms == ("substack_newsletter",)
    assert "substack_newsletter_issue" in packet.requested_output_shapes


def test_telegram_channel_default_vs_remote_operator_distinction():
    channel = idea("Telegram update about process limits")
    remote = idea("Telegram operator inbox review message about process limits")

    assert channel.requested_platforms == ("telegram_channel_destination",)
    assert remote.requested_platforms == ("telegram_remote_operator",)
    assert channel.requested_output_shapes == ("telegram_channel_update",)
    assert remote.requested_output_shapes == ("telegram_operator_review_message",)


def test_process_source_trust_maps_to_pre_alpha_and_no_source_needed():
    packet = idea("Process note: source trust before forecast")

    assert packet.content_lane == "pre_alpha_general_process"
    assert packet.source_requirement_status == "not_required_for_process"
    assert packet.claim_risk_class == "process_claim_low_risk"


def test_grounded_news_terms_need_sources():
    packet = idea("CPI news context for a market education note")

    assert packet.content_lane == "grounded_news_context"
    assert packet.source_requirement_status == "source_needed"
    assert packet.claim_risk_class == "market_context_claim_review_required"
    assert packet.readiness_state == "source_needed"


def test_future_artifact_terms_gate_public_claims():
    packet = idea("Internal alpha artifact DQR readiness report for future audience")

    assert packet.content_lane == "future_artifact_backed"
    assert packet.source_requirement_status == "artifact_required_future_gate"
    assert packet.claim_risk_class == "artifact_backed_claim_requires_packet"
    assert packet.artifact_backed_claims_allowed is False
    assert "artifact_required_future_gate" in packet.blocked_reasons
    assert "artifact_backed_claims_not_allowed_until_future_gate" in packet.blocked_reasons


def test_approval_like_text_cannot_create_approval_and_requires_challenge():
    packet = intent("Approve this X thread about process limits")

    assert packet.intent_class == "approval_like_text_requires_challenge"
    assert packet.can_create_approval is False
    assert packet.can_dispatch is False
    assert "approval_bypass_blocked" in packet.blocked_reasons


def test_dispatch_like_text_never_dispatches():
    packet = intent("Publish and send now this Telegram update about process limits")

    assert packet.can_dispatch is False
    assert "dispatch_bypass_blocked" in packet.blocked_reasons
    assert packet.safety_flags["live_dispatch_enabled"] is False
    assert packet.safety_flags["telegram_api_called"] is False


def test_forbidden_advice_signal_language_blocks():
    packet = idea("Buy AAPL now because the model predicts upside")
    intent_packet = intent("Buy AAPL now because the model predicts upside")

    assert packet.claim_risk_class == "advice_or_signal_forbidden"
    assert packet.readiness_state == "blocked"
    assert "forbidden_signal_or_advice_language" in packet.blocked_reasons
    assert intent_packet.can_create_editorial_brief_candidate is False


def test_manual_metric_note_recognized_without_scraping_or_api():
    packet = intent("Manual metric note: recorded 12 impressions from operator screen")

    assert packet.intent_class == "manual_metric_note"
    assert packet.safety_flags["scraping_performed"] is False
    assert packet.safety_flags["platform_api_called"] is False


def test_status_query_recognized_without_live_api():
    packet = intent("What is status of the queue?")

    assert packet.intent_class == "status_query"
    assert packet.safety_flags["platform_api_called"] is False
    assert packet.safety_flags["network_performed"] is False


def test_empty_ambiguous_text_asks_clarification():
    r = raw("   ")
    i = parser.build_content_idea_packet(r)
    p = parser.parse_local_intent(r, i)

    assert p.intent_class == "unknown"
    assert p.requires_clarification is True
    assert "clarification_required" in p.blocked_reasons


def test_unsupported_platform_phrase_fails_closed():
    packet = idea("Create a Reddit post about process limits")

    assert packet.readiness_state == "blocked"
    assert "unknown_platform_target:reddit" in packet.blocked_reasons


def test_all_packets_remain_review_only_not_public_postable():
    r = raw("Substack newsletter about source trust")
    i = parser.build_content_idea_packet(r)
    p = parser.parse_local_intent(r, i)
    v = parser.validate_intent_packet(i, p)

    assert i.human_review_required is True
    assert i.public_postable is False
    assert p.can_create_approval is False
    assert p.can_dispatch is False
    assert v.public_postable_false is True


def test_all_no_provider_no_live_no_ingestion_flags_false():
    r = raw("X thread about source trust")
    i = parser.build_content_idea_packet(r)
    p = parser.parse_local_intent(r, i)

    assert_all_safety_false(r.safety_flags)
    assert_all_safety_false(i.safety_flags)
    assert_all_safety_false(p.safety_flags)


def test_validate_intent_packet_blocks_artifact_gate():
    r = raw("Internal alpha artifact readiness post for X")
    i = parser.build_content_idea_packet(r)
    p = parser.parse_local_intent(r, i)
    result = parser.validate_intent_packet(i, p)

    assert result.validation_status == "blocked"
    assert result.no_live_defaults_pass is True
    assert "source_requirement_not_satisfied_for_current_stage" in result.blocked_reasons


def test_write_artifacts_only_docs_automation_0174u4(tmp_path):
    root = tmp_path
    packet_path, runbook_path = parser.write_artifacts(root)

    assert packet_path == root / "docs" / "automation" / "0174U4" / "content_idea_intent_parser_contract_packet.json"
    assert runbook_path == root / "docs" / "automation" / "0174U4" / "content_idea_intent_parser_contract.md"
    assert packet_path.exists()
    assert runbook_path.exists()
    with pytest.raises(parser.ContentIdeaIntentParserError):
        parser.write_artifacts(root, root / "docs" / "automation" / "0174U4_other")


def test_contract_packet_contains_next_heavy_batch_recommendation():
    packet = parser.build_contract_packet()

    assert packet["next_heavy_batch_recommendation"] == (
        "TASK_CONTENTOPS_0174U5_EDITORIAL_BRIEF_AND_AI_WRITER_OUTPUT_CONTRACT_V0"
    )
    assert packet["parser_rules"]["local_only"] is True
    assert packet["parser_rules"]["dispatch_text_never_dispatches"] is True
    assert packet["sample_idea_packet"]["public_postable"] is False
    assert packet["sample_intent_packet"]["can_dispatch"] is False
