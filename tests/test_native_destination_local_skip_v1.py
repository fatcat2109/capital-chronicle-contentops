"""The existing compiler's empty Instagram non-send cannot block other media."""
import pytest

from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _native_preview_bundle, SimpleGeminiNewsroomError, V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


@pytest.mark.parametrize("fault", [None, "not_skipped", "image_assigned"])
def test_instagram_skip_uses_its_own_images_not_other_channel_media(monkeypatch, fault):
    payloads = {d: {"text": "CONFIRMED controlled announcement."}
                for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS}
    for destination in ("x", "threads"):
        payloads[destination].update(platform_limit=500,
            quality_metrics={"sentence_boundary_pass": True, "orphan_fragment_count": 0,
                             "hard_character_slicing_used": False})
    payloads["instagram_business"] = {"delivery_state": "SKIPPED_IMAGE_REQUIRED", "media_asset_ids": []}
    if fault == "not_skipped": payloads["instagram_business"]["delivery_state"] = "READY"
    if fault == "image_assigned": payloads["instagram_business"]["media_asset_ids"] = ["event-card"]
    import live_contentops.eight_platform_substack_first_pipeline_v1 as compiler
    monkeypatch.setattr(compiler, "build_native_derivative_payloads", lambda **kwargs: payloads)
    article = {"title": "Controlled event announcement", "dek": "Controlled discussion preview.",
               "substack_body_markdown": "CONFIRMED controlled announcement."}
    kwargs = dict(article=article, article_mode="WEEK_AHEAD_OR_WATCH", article_identity="controlled",
                  epistemic_state={"reader_visible_epistemic_label": "CONFIRMED"},
                  media_asset_ids=["event-card"])
    if fault:
        with pytest.raises(SimpleGeminiNewsroomError, match="native_preview_epistemic_state_missing"):
            _native_preview_bundle(**kwargs)
    else:
        bundle, intents = _native_preview_bundle(**kwargs)
        assert bundle["package_count"] == len(intents) == 8
        assert bundle["packages"]["instagram_business"]["delivery_state"] == "SKIPPED_IMAGE_REQUIRED"
        assert bundle["public_write_performed"] is False
