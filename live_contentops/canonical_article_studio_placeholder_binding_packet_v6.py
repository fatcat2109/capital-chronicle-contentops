"""V6 Canonical Article Studio Placeholder Binding Packet.

Defines placeholder binding schemas and statuses.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_placeholder_binding_packet() -> dict[str, Any]:
    """Generates the placeholder binding packet."""
    return {
        "binding_status": "PLACEHOLDER_BINDING_READY_WITH_BLOCKERS",
        "runtime_truth": False,
        "draft_shell_loaded": True,
        "slot_schema_loaded": True,
        "placeholder_binding_created": True,
        "placeholder_binding_review_only": True,
        "approved_placeholder_binding_for_runtime": False,
        "source_pack_approved": False,
        "jim_review_completed": False,
        "article_copy_generated": False,
        "title_generated": False,
        "dek_generated": False,
        "body_generated": False,
        "citations_generated": False,
        "seo_metadata_generated": False,
        "slot_values_materialized": False,
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
