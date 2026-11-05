"""CC-253: hosted article media keeps the fields its readers decide on; post cards stay off the site.

Since CC-186 (48d152a6) the hosting step rewrote each article asset without `modality` or the
photo rights fields, so the newsroom reader refused every new piece (NEWSROOM_MEDIA_TYPE_REFUSED,
5 Nov: PPI, SEC, FOMC, CPI). Generated post cards were also hosted as article media.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

import live_contentops.cloudinary_delivery_media_v1 as cloudinary
import live_contentops.visual_asset_discovery_v1 as discovery
from live_contentops.media_manifest_authority_v1 import (
    image_metadata_from_file,
    sha256_file,
    validate_delivery_media_object,
)

ENVIRONMENT = {"CLOUDINARY_CLOUD_NAME": "test-cloud", "CLOUDINARY_API_KEY": "test-key",
               "CLOUDINARY_API_SECRET": "test-secret"}


def _image(tmp_path: Path, name: str, size=(1350, 1080)) -> dict:
    path = tmp_path / name
    Image.new("RGB", size, "#07111f").save(path, format="PNG")
    return {"path": str(path), "absolute_local_source_path": str(path), "sha256": sha256_file(path),
            **image_metadata_from_file(path)}


def _host(monkeypatch, *assets):
    # Each asset's deterministic object already holds its exact local bytes, so nothing uploads.
    monkeypatch.setattr(cloudinary, "read_public_image_bytes",
                        lambda url: next(Path(a["path"]).read_bytes() for a in assets
                                         if cloudinary.deterministic_cloudinary_public_id(
                                             work_item_id="cc253", asset_sha256=a["sha256"]) in url))
    monkeypatch.setattr(cloudinary, "_upload_asset",
                        lambda **_: (_ for _ in ()).throw(AssertionError("reuse the exact object")))
    result = cloudinary.prepare_cloudinary_delivery_media(
        work_item_id="cc253", delivery_only_assets=[], article_assets=list(assets), environment=ENVIRONMENT)
    assert result["status"] == cloudinary.READY, result
    return {row["media_asset_id"]: row for row in result["manifest"]["assets"]}


def _chart(tmp_path):
    return {**_image(tmp_path, "chart.png"), "asset_id": "ppi_headline_core_24m",
            "media_role": "editorial_data_journalism", "modality": "source_backed_chart",
            "underlying_source_rights_status": "attributed_facts_independent_chart",
            "source_reuse_basis": "Independent chart of attributed original-source facts",
            "source_page_url": "https://www.bls.gov/news.release/archives/ppi_10152026.htm",
            "alt_text": "Two years of first-reported monthly PPI changes.",
            "caption": "October 2024 to September 2026, first releases."}


def test_a_hosted_chart_keeps_the_fields_the_reader_decides_on(tmp_path, monkeypatch):
    chart = {**_chart(tmp_path), "chart_title": "PPI final demand, first releases"}
    row = _host(monkeypatch, chart)["ppi_headline_core_24m"]
    for key in ("modality", "underlying_source_rights_status", "source_reuse_basis", "source_page_url",
                "alt_text", "chart_title"):
        assert row[key] == chart[key], key
    assert row["media_role"] == "editorial_data_journalism"
    assert row["article_inclusion"] is True and row["canonical_article_media"] is True
    assert row["delivery_only"] is False
    assert row["source_provenance"]["caption"] == chart["caption"]
    # Before CC-253 this row failed here with delivery_media_role_invalid.
    assert validate_delivery_media_object(row) == []


def test_a_hosted_documentary_photo_keeps_its_rights_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery, "validate_contextual_photo", lambda asset, **_: None)
    photo = {**_image(tmp_path, "photo.png", size=(1200, 800)), "asset_id": "documentary_oil",
             "media_role": "contextual_photo", "modality": "documentary_photo",
             "rights_status": "OPEN_LICENSED", "rights_evidence_sha256": "f" * 64,
             "license_url": "https://creativecommons.org/licenses/by-sa/2.0",
             "source_page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
             "alt_text": "Archive aerial view of a refinery.", "caption": "Photo: Example, CC BY-SA 2.0."}
    row = _host(monkeypatch, photo)["documentary_oil"]
    for key in ("modality", "rights_status", "rights_evidence_sha256", "license_url", "source_page_url",
                "alt_text"):
        assert row[key] == photo[key], key
    assert row["media_role"] == "contextual_photo" and row["article_inclusion"] is True
    assert validate_delivery_media_object(row) == []


def test_a_generated_post_card_is_hosted_delivery_only(tmp_path, monkeypatch):
    card = {**_chart(tmp_path), "asset_id": "post-card-e06e6bbbb2b3545f9cf5",
            "visual_type": "ADMITTED_HEADLINE_FACTS_CARD", "post_card_binding": {"title": "The Fed held"}}
    row = _host(monkeypatch, card)["post-card-e06e6bbbb2b3545f9cf5"]
    assert row["media_role"] == "delivery_only"
    assert row["article_inclusion"] is False and row["canonical_article_media"] is False
    assert row["delivery_only"] is True
    assert "modality" not in row  # the reader skips it as delivery media; it never enters the site
    assert validate_delivery_media_object(row) == []


def test_a_field_the_input_row_lacks_is_never_added(tmp_path, monkeypatch):
    chart = _chart(tmp_path)
    row = _host(monkeypatch, chart)["ppi_headline_core_24m"]
    for key in ("chart_title", "license_url", "rights_status", "rights_evidence_sha256"):
        assert key not in chart and key not in row, key
