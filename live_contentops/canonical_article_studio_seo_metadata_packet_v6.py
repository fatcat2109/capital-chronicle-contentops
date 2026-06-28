"""V6 Canonical Article Studio SEO Metadata Packet.

Defines SEO metadata contract statuses and flags.
"""
from __future__ import annotations

from typing import Any


def make_canonical_article_studio_seo_metadata_packet() -> dict[str, Any]:
    """Generates the SEO metadata packet."""
    return {
        "seo_metadata_status": "SEO_METADATA_BLOCKED_WAITING_FOR_REFINED_DRAFT",
        "runtime_truth": False,
        "refinement_queue_loaded": True,
        "blocked_refinement_output_loaded": True,
        "seo_input_contract_created": True,
        "refined_draft_available": False,
        "seo_metadata_generation_allowed": False,
        "seo_metadata_generation_performed": False,
        "seo_output_created": True,
        "seo_values_materialized": False,
        "seo_title_generated": False,
        "seo_meta_description_generated": False,
        "slug_generated": False,
        "tags_generated": False,
        "social_preview_generated": False,
        "canonical_url_generated": False,
        "editorial_score_generated": False,
        "seo_score_generated": False,
        "readability_score_generated": False,
        "article_copy_generated": False,
        "title_generated": False,
        "dek_generated": False,
        "body_generated": False,
        "citations_generated": False,
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
