import pytest

from live_contentops.audit_backed_feedback_backlog_bridge_v6 import (
    build_audit_backed_feedback_backlog_packet,
    make_sample_identity_link,
)


def test_ready_identity_link_and_operator_feedback_produces_backlog_and_brief():
    packet = build_audit_backed_feedback_backlog_packet()

    assert packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW"
    assert packet["feedback_items"]
    assert packet["backlog_candidates"]
    assert packet["selected_next_article_brief"]
    assert packet["final_product_loop_position"] == "audit_to_feedback_to_next_idea"
    assert packet["safety_flags"]["network_call_made"] is False
    assert packet["safety_flags"]["scraping_performed"] is False


def test_missing_feedback_returns_review_status():
    packet = build_audit_backed_feedback_backlog_packet(feedback_items=[])

    assert packet["bridge_status"] == "REVIEW_MISSING_FEEDBACK_ITEMS"
    assert "feedback_items_missing" in packet["blockers"]
    assert packet["selected_next_article_brief"] is None


def test_missing_audit_backing_blocks():
    link = make_sample_identity_link()
    link["ready_for_publication_audit_record"] = False
    packet = build_audit_backed_feedback_backlog_packet(identity_link=link, audit_record_ref=None)

    assert packet["bridge_status"] == "BLOCKED_MISSING_AUDIT_BACKING"
    assert "audit_backing_missing" in packet["blockers"]


def test_secret_like_feedback_key_blocks():
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": "operator_note",
        "operator_supplied_text": "Safe public channel summary.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
        "raw_secret_value": "do-not-output",
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "secret_like_input_key_blocked" in packet["blockers"]
    assert "do-not-output" not in str(packet)


def test_forbidden_financial_advice_wording_blocks():
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": "operator_note",
        "operator_supplied_text": "Reader asked for a buy signal.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "forbidden_financial_advice_or_signal_wording" in packet["blockers"]


@pytest.mark.parametrize("source_kind", ["dm", "direct_message", "private_message", "private_chat"])
def test_private_message_source_kind_blocks(source_kind):
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": source_kind,
        "operator_supplied_text": "Private message should not enter the backlog.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "private_message_feedback_source_blocked" in packet["blockers"]


def test_metrics_note_with_secret_like_key_blocks():
    packet = build_audit_backed_feedback_backlog_packet(metrics_notes=[{"api_token": "do-not-output"}])

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "secret_like_input_key_blocked" in packet["blockers"]
    assert "do-not-output" not in str(packet)


def test_output_asserts_no_live_network_provider_browser_or_scrape_flags():
    packet = build_audit_backed_feedback_backlog_packet()

    for key, value in packet["safety_flags"].items():
        assert value is False, key
    assert packet["non_readiness_claims"]["community_scrape_claimed"] is False
    assert packet["non_readiness_claims"]["bot_or_slash_command_claimed"] is False
