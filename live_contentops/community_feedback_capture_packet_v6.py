"""V6 Community Feedback Capture Packet.

Defines the community feedback capture packet structure and default status flags.
"""
from __future__ import annotations

from typing import Any


def make_community_feedback_capture_packet() -> dict[str, Any]:
    """Generates the community feedback capture packet."""
    return {
        "community_feedback_capture_status": "COMMUNITY_FEEDBACK_CAPTURE_BLOCKED_WAITING_FOR_PUBLICATION_AUDIT_RECORD",
        "runtime_truth": False,
        "publication_audit_record_contract_loaded": True,
        "blocked_publication_audit_output_loaded": True,
        "feedback_input_contract_created": True,
        "blocked_feedback_template_created": True,
        "publication_audit_record_available": False,
        "publication_confirmed": False,
        "public_url_proof_available": False,
        "platform_publication_id_available": False,
        "destination_binding_completed": False,
        "account_binding_completed": False,
        "feedback_capture_policy_available": False,
        "feedback_source_binding_completed": False,
        "community_channel_binding_completed": False,
        "operator_feedback_capture_authorization_present": False,
        "jim_feedback_review_completed": False,
        "feedback_capture_allowed": False,
        "feedback_capture_performed": False,
        "comment_capture_performed": False,
        "reaction_capture_performed": False,
        "metric_capture_performed": False,
        "feedback_summary_created": False,
        "backlog_item_created": False,
        "audit_record_mutation_allowed": False,
        "audit_record_mutated": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "platform_api_request_performed": False,
        "webhook_request_performed": False,
        "scraping_performed": False,
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
