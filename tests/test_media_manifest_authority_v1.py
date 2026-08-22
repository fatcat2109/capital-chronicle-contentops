from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from live_contentops.media_manifest_authority_v1 import (
    PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM,
    build_delivery_only_editorial_card,
    build_delivery_media_manifest,
    select_primary_chart,
    sha256_file,
    validate_chart_media_object,
    visual_similarity_to_local_file,
)


def _png(path: Path, size: tuple[int, int], color: str) -> bytes:
    image = Image.new("RGB", size, color)
    image.save(path, format="PNG")
    value = io.BytesIO()
    image.save(value, format="PNG")
    return value.getvalue()


def test_manifest_selects_exact_chart_by_hash_not_public_image_order(tmp_path: Path):
    chart = tmp_path / "chart.png"
    logo = tmp_path / "logo.png"
    chart_bytes = _png(chart, (1620, 870), "white")
    logo_bytes = _png(logo, (512, 512), "yellow")
    chart_url = "https://substack-post-media.s3.amazonaws.com/public/images/chart.png"
    logo_url = "https://substack-post-media.s3.amazonaws.com/public/images/logo.png"
    packet = {
        "assets": [
            {
                "asset_id": "primary",
                "media_role": "primary_chart",
                "path": str(chart),
                "sha256": sha256_file(chart),
                "provenance_status": "source_backed",
                "source_label": "FRED",
                "source_page_url": "https://fred.stlouisfed.org/series/DFF",
                "caption": "DFF inside the target corridor.",
                "alt_text": "DFF policy-corridor chart.",
            }
        ]
    }

    manifest = build_delivery_media_manifest(
        media_packet=packet,
        public_image_urls=[logo_url, chart_url],
        run_id="manifest-test",
        remote_bytes_by_url={logo_url: logo_bytes, chart_url: chart_bytes},
    )

    primary = select_primary_chart(manifest)
    assert manifest["status"] == "PASS"
    assert primary["verified_public_delivery_url"] == chart_url
    assert primary["sha256"] == sha256_file(chart)
    assert primary["width"] == 1620
    assert primary["height"] == 870
    assert primary["absolute_local_source_path"] == str(chart.resolve())


def test_square_branding_asset_is_rejected_for_primary_chart(tmp_path: Path):
    logo = tmp_path / "logo.png"
    logo_bytes = _png(logo, (1024, 1024), "yellow")
    logo_url = "https://substack-post-media.s3.amazonaws.com/public/images/logo.png"
    packet = {
        "assets": [
            {
                "asset_id": "primary",
                "media_role": "primary_chart",
                "path": str(logo),
                "sha256": sha256_file(logo),
                "provenance_status": "branding",
                "source_label": "Capital Chronicle",
                "source_page_url": "https://capitalchronicle.substack.com",
                "caption": "Logo",
                "alt_text": "Logo",
            }
        ]
    }

    manifest = build_delivery_media_manifest(
        media_packet=packet,
        public_image_urls=[logo_url],
        run_id="logo-test",
        remote_bytes_by_url={logo_url: logo_bytes},
    )

    assert manifest["status"] == "BLOCKED"
    assert "square_branding_or_avatar_rejected" in manifest["blockers"]
    assert "square_branding_or_avatar_rejected" in validate_chart_media_object(manifest["assets"][0])


def test_public_chart_readback_rejects_logo_visual(tmp_path: Path):
    chart = tmp_path / "chart.png"
    logo = tmp_path / "logo.png"
    chart_bytes = _png(chart, (1620, 870), "white")
    logo_bytes = _png(logo, (1620, 870), "yellow")

    assert visual_similarity_to_local_file(chart_bytes, chart) >= PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM
    assert visual_similarity_to_local_file(logo_bytes, chart) < PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM


def test_delivery_card_renders_newsroom_unicode_without_missing_glyphs(tmp_path: Path):
    title = "FT flags lender insurance gap around Meta–BlackRock’s $14bn data centre"
    card = build_delivery_only_editorial_card(
        output_path=tmp_path / "unicode-delivery-card.png",
        title=title,
        source_label="Financial Times",
        source_page_url="https://www.ft.com/",
    )

    assert Path(card["path"]).is_file()
    assert card["source_title"] == title
    assert card["display_replacement_glyph_present"] is False
    assert "�" not in card["display_title"]
    assert "□" not in card["display_title"]
    if card["unicode_font_loaded"]:
        assert card["display_title"] == title
    else:
        assert card["display_title"] == (
            "FT flags lender insurance gap around Meta-BlackRock's $14bn data centre"
        )
        assert card["display_fallback_applied"] is True


def test_delivery_card_uses_reader_facing_source_date_and_full_brief_cta(tmp_path: Path):
    card = build_delivery_only_editorial_card(
        output_path=tmp_path / "delivery-card.png",
        title="State Department Approves Possible APKWS II Sale to Italy",
        source_label="Defense Security Cooperation Agency",
        source_page_url="https://www.dsca.mil/press-media/major-arms-sales/italy-apkws-ii",
        published_at="2026-08-20T14:32:19Z",
    )

    assert card["reader_facing_source_date"] == "August 20, 2026"
    assert card["reader_facing_cta"] == "Read the full brief on Capital Chronicle"
    assert card["canonical_article_media"] is False
    assert card["article_inclusion"] is False
    assert card["delivery_only"] is True
