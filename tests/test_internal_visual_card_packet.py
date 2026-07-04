import pytest

from live_contentops.internal_visual_card_packet import build_internal_visual_card, stable_hash, validate_internal_visual_card


def test_builds_ready_internal_visual_card_without_render_claim():
    card = build_internal_visual_card(
        card_id="card_test_001",
        card_type="article_quote_card",
        title="Reviewed quote",
        body="Operator-approved excerpt.",
        alt_text="Text card with an operator-approved excerpt.",
        source_refs=["canonical_article_redacted_001"],
    )

    assert card["status"] == "READY_FOR_MEDIA_MANIFEST_REVIEW"
    assert card["render_status"] == "not_rendered_spec_only"
    assert card["safety_flags"]["image_provider_call_made"] is False
    assert card["safety_flags"]["rendered_image_created"] is False
    validate_internal_visual_card(card)


def test_alt_text_required():
    card = build_internal_visual_card(
        card_id="card_missing_alt",
        card_type="article_quote_card",
        title="Quote",
        body="Excerpt.",
        alt_text="",
        source_refs=["canonical_article_redacted_001"],
    )

    assert "alt_text_missing" in card["blockers"]
    with pytest.raises(ValueError, match="alt_text_required"):
        validate_internal_visual_card(card)


def test_blocks_secret_like_keys():
    card = build_internal_visual_card(
        card_id="card_secret",
        card_type="article_quote_card",
        title="Quote",
        body="Excerpt.",
        alt_text="Alt text.",
        source_refs=["canonical_article_redacted_001"],
        claims=[{"api_key": "redacted"}],
    )

    assert "secret_like_key_blocked" in card["blockers"]


def test_blocks_unbacked_numbers():
    card = build_internal_visual_card(
        card_id="card_fake_number",
        card_type="data_sufficiency_card",
        title="90 percent confidence",
        body="This says 90 without source refs.",
        alt_text="Data sufficiency card.",
    )

    assert "unbacked_number_or_metric_blocked" in card["blockers"]


def test_allows_numbers_with_source_refs():
    card = build_internal_visual_card(
        card_id="card_backed_number",
        card_type="data_sufficiency_card",
        title="3 source checks",
        body="Reviewed against 3 operator-selected sources.",
        alt_text="Data sufficiency card with sourced count.",
        source_refs=["source_pack_review_redacted_001"],
    )

    assert card["blockers"] == []
    assert card["status"] == "READY_FOR_MEDIA_MANIFEST_REVIEW"


def test_card_hash_changes_with_content():
    base = build_internal_visual_card(
        card_id="card_hash",
        card_type="source_trust_card",
        title="Source trust",
        body="Neutral source summary.",
        alt_text="Source trust card.",
        source_refs=["source_pack_review_redacted_001"],
    )
    changed = {**base, "body": "Changed source summary."}

    assert base["card_hash"] != stable_hash({k: v for k, v in changed.items() if k != "card_hash"})
