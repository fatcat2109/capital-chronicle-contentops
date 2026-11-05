"""EIA's actual weekly-release host feeds attributed copy to all eight channels."""
import pytest

from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _native_preview_bundle, SimpleGeminiNewsroomError, V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


@pytest.mark.parametrize("host", ["ir.eia.gov", "www.eia.gov"])
def test_official_eia_release_reaches_all_native_previews(host):
    article = {
        "title": "EIA oil inventories: the product split matters",
        "dek": "EIA reports smaller crude and gasoline draws than the distillate draw.",
        "substack_body_markdown": "EIA reports smaller crude and gasoline draws than the distillate draw. [[SOURCE:SOURCE_1]]",
        "reader_first_version": "DATA_JOURNALISM_V1",
        "post_visual_destination_media": {d: ["eia-chart"] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS},
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "U.S. Energy Information Administration",
            "url": "https://" + host + "/wpsr/summary.txt", "published_at_utc": "2026-11-04T00:00:00Z"}],
    }
    bundle, intents = _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="eia-controlled", media_asset_ids=["eia-chart"],
        epistemic_state={"reader_visible_epistemic_label": "CONFIRMED", "event_confirmation_state": "CONFIRMED",
            "primary_reporting_publisher": "U.S. Energy Information Administration"})
    assert bundle["package_count"] == len(intents) == 8
    assert all("EIA" in " ".join(str(v) for k, v in payload.items() if k in {"text", "full_text", "root_text"})
               for payload in bundle["packages"].values())


def test_official_short_name_requires_exact_publisher_and_host():
    article = {"title": "EIA oil inventories", "dek": "EIA reports a product split.",
        "substack_body_markdown": "EIA reports a product split. [[SOURCE:SOURCE_1]]",
        "reader_first_version": "DATA_JOURNALISM_V1",
        "post_visual_destination_media": {d: ["eia-chart"] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS},
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "U.S. Energy Information Administration",
            "url": "https://ir.eia.gov.example.org/wpsr/summary.txt"}]}
    with pytest.raises(SimpleGeminiNewsroomError, match="native_preview_epistemic_state_missing"):
        _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
            article_identity="spoof", media_asset_ids=["eia-chart"],
            epistemic_state={"reader_visible_epistemic_label": "CONFIRMED",
                "primary_reporting_publisher": "U.S. Energy Information Administration"})
