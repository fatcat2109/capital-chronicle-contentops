"""V6 Canonical Article Studio Draft Shell Packet.

Defines editor draft shell schemas and statuses.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_draft_shell_packet() -> dict[str, Any]:
    """Generates the editor draft shell packet."""
    return {
        "shell_status": "BROWSERLESS_EDITOR_SHELL_READY_WITH_BLOCKERS",
        "runtime_truth": False,
        "source_review_queue_loaded": True,
        "review_item_status": "BLOCKED_WAITING_FOR_REAL_SOURCE_APPROVAL",
        "shell_instance_created": True,
        "article_copy_generated": False,
        "article_body_generated": False,
        "title_generated": False,
        "dek_generated": False,
        "citations_generated": False,
        "seo_metadata_generated": False,
        "source_pack_approved": False,
        "jim_review_completed": False,
        "ready_for_editor_review": False,
        "ready_for_jim_approval": False,
        "ready_for_publication": False,
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
