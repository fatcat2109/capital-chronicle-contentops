"""Test V6 Canonical Article Studio Draft Slot Schema."""
from __future__ import annotations

from live_contentops import canonical_article_studio_draft_slot_schema_v6 as schema_builder


def test_make_canonical_article_studio_draft_slot_schema():
    schema = schema_builder.make_canonical_article_studio_draft_slot_schema()

    assert len(schema) == 9
    slot_types = [slot["slot_type"] for slot in schema]
    expected_types = [
        "title",
        "dek",
        "thesis",
        "claim_summary",
        "evidence_placeholder",
        "risk_and_limitations",
        "conclusion",
        "seo_title",
        "seo_meta_description"
    ]
    assert slot_types == expected_types

    for slot in schema:
        assert slot["current_value"] is None
        assert slot["generated"] is False
        assert isinstance(slot["source_binding_required"], bool)
        assert slot["blocks_publication"] is True
