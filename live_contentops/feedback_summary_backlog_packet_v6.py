"""V6 Feedback Summary Backlog Packet.

Defines the feedback summary backlog packet structure and default status flags.
"""
from __future__ import annotations

from typing import Any


def make_feedback_summary_backlog_packet() -> dict[str, Any]:
    """Generates the feedback summary backlog packet."""
    return {
        "feedback_summary_backlog_status": "FEEDBACK_SUMMARY_BACKLOG_BLOCKED_WAITING_FOR_FEEDBACK_CAPTURE",
        "runtime_truth": False,
        "community_feedback_capture_contract_loaded": True,
        "blocked_feedback_output_loaded": True,
        "summary_backlog_input_contract_created": True,
        "blocked_summary_template_created": True,
        "community_feedback_capture_available": False,
        "redacted_feedback_records_available": False,
        "comments_available": False,
        "reactions_available": False,
        "metrics_available": False,
        "public_url_proof_available": False,
        "platform_publication_id_available": False,
        "feedback_summarization_policy_available": False,
        "backlog_routing_policy_available": False,
        "jim_feedback_review_completed": False,
        "operator_summary_authorization_present": False,
        "summary_generation_allowed": False,
        "summary_generation_performed": False,
        "backlog_item_creation_allowed": False,
        "backlog_item_created": False,
        "next_article_signal_created": False,
        "model_provider_call_performed": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "platform_api_request_performed": False,
        "webhook_request_performed": False,
        "scraping_performed": False,
        "audit_record_mutated": False,
        "live_write_attempted": False,
        "retry_attempted": False,
        "public_url_created": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
