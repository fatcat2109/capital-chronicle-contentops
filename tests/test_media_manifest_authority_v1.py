from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from live_contentops.media_manifest_authority_v1 import (
    PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM,
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
