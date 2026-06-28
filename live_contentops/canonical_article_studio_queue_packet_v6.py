"""V6 Canonical Article Studio Queue Packet.

Defines queue packet schemas for article review queue items.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_queue_packet() -> dict[str, Any]:
    """Generates the canonical article studio queue packet."""
    return {
        "queue_status": "REVIEW_QUEUE_READY_WITH_BLOCKERS",
        "runtime_truth": False,
        "canonical_draft_eligibility_loaded": True,
        "real_source_pack_approved": False,
        "real_operator_approval_created": False,
        "article_copy_generated": False,
        "draft_markdown_created": False,
        "article_studio_item_created": True,
        "editor_review_required": True,
        "jim_review_required": True,
        "source_approval_required": True,
        "canonical_draft_generation_allowed": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }
