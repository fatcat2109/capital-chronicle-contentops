"""Test V6 Canonical Article Studio SEO Metadata Packet."""
from __future__ import annotations

from live_contentops import canonical_article_studio_seo_metadata_packet_v6 as packet_builder


def test_make_canonical_article_studio_seo_metadata_packet():
    packet = packet_builder.make_canonical_article_studio_seo_metadata_packet()

    assert packet["seo_metadata_status"] == "SEO_METADATA_BLOCKED_WAITING_FOR_REFINED_DRAFT"
    assert packet["runtime_truth"] is False
    assert packet["refinement_queue_loaded"] is True
    assert packet["blocked_refinement_output_loaded"] is True
    assert packet["seo_input_contract_created"] is True
    assert packet["refined_draft_available"] is False
    assert packet["seo_metadata_generation_allowed"] is False
    assert packet["seo_metadata_generation_performed"] is False
    assert packet["seo_output_created"] is True
    assert packet["seo_values_materialized"] is False
    assert packet["seo_title_generated"] is False
    assert packet["seo_meta_description_generated"] is False
    assert packet["slug_generated"] is False
    assert packet["tags_generated"] is False
    assert packet["social_preview_generated"] is False
    assert packet["canonical_url_generated"] is False
    assert packet["editorial_score_generated"] is False
    assert packet["seo_score_generated"] is False
    assert packet["readability_score_generated"] is False
    assert packet["article_copy_generated"] is False
    assert packet["title_generated"] is False
    assert packet["dek_generated"] is False
    assert packet["body_generated"] is False
    assert packet["citations_generated"] is False
    assert packet["allowed_for_publication"] is False
    assert packet["public_postable"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["outbox_entry_created"] is False
    assert packet["provider_call_performed"] is False
    assert packet["browser_session_started"] is False
    assert packet["env_read_performed"] is False
    assert packet["credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["kill_switch_active"] is True
