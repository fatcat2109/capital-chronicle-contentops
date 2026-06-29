"""V6 Next Article Planning From Feedback Packet.

Defines the next article planning packet structure and default status flags.
"""
from __future__ import annotations

from typing import Any


def make_next_article_planning_from_feedback_packet() -> dict[str, Any]:
    """Generates the next article planning from feedback packet."""
    return {
        "next_article_planning_status": "NEXT_ARTICLE_PLANNING_BLOCKED_WAITING_FOR_FEEDBACK_SUMMARY_BACKLOG",
        "runtime_truth": False,
        "feedback_summary_backlog_contract_loaded": True,
        "blocked_summary_backlog_output_loaded": True,
        "planning_input_contract_created": True,
        "blocked_planning_template_created": True,
        "feedback_summary_available": False,
        "backlog_items_available": False,
        "next_article_signals_available": False,
        "redacted_feedback_records_available": False,
        "public_url_proof_available": False,
        "platform_publication_id_available": False,
        "planning_policy_available": False,
        "source_research_policy_available": False,
        "jim_planning_review_completed": False,
        "operator_planning_authorization_present": False,
        "article_planning_allowed": False,
        "article_planning_performed": False,
        "article_idea_created": False,
        "research_question_created": False,
        "source_pack_request_created": False,
        "canonical_draft_requested": False,
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
