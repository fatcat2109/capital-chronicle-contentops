from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.media_manifest_authority_v1 import (
    PUBLIC_CHART_VISUAL_SIMILARITY_MINIMUM,
    build_delivery_only_editorial_card,
    build_delivery_media_manifest,
    select_primary_chart,
    select_primary_delivery_media,
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


def test_native_data_journalism_chart_keeps_its_role_in_delivery(tmp_path):
    from copy import deepcopy
    chart = tmp_path / "chart.png"
    raw = _png(chart, (1500, 1300), "white")
    url = "https://substack-post-media.s3.amazonaws.com/public/images/chart.png"
    asset = {"asset_id": "native-chart", "media_role": "editorial_data_journalism",
        "modality": "source_backed_chart", "path": str(chart), "sha256": sha256_file(chart),
        "source_page_url": "https://example.org/official", "alt_text": "Controlled native chart."}
    original = deepcopy(asset)
    manifest = build_delivery_media_manifest(media_packet={"assets": [asset]}, public_image_urls=[url],
        run_id="native-role", remote_bytes_by_url={url: raw})
    assert manifest["status"] == "PASS"
    delivery = select_primary_delivery_media(manifest)
    assert delivery["media_role"] == "editorial_data_journalism"
    assert delivery["sha256"] == asset["sha256"] and asset == original
    wrong = {**asset, "modality": "branding"}
    refused = build_delivery_media_manifest(media_packet={"assets": [wrong]}, public_image_urls=[url],
        run_id="wrong-role", remote_bytes_by_url={url: raw})
    assert refused["status"] == "BLOCKED"


def test_retained_public_domain_photo_without_old_delivery_role_uses_exact_rights(tmp_path):
    photo = tmp_path / "photo.png"
    raw = _png(photo, (640, 427), "gray")
    url = "https://substack-post-media.s3.amazonaws.com/public/images/photo.png"
    asset = {"asset_id": "photo", "modality": "documentary_photo", "path": str(photo),
        "sha256": sha256_file(photo), "rights_status": "PUBLIC_DOMAIN",
        "rights_evidence_sha256": "controlled-existing-admission", "source_page_url": "https://example.org/photo",
        "license_url": "https://example.org/public-domain", "alt_text": "Controlled documentary photo."}
    manifest = build_delivery_media_manifest(media_packet={"assets": [asset]}, public_image_urls=[url],
        run_id="retained-photo", remote_bytes_by_url={url: raw})
    assert select_primary_delivery_media(manifest)["media_role"] == "contextual_photo"
    refused = build_delivery_media_manifest(media_packet={"assets": [{**asset, "rights_evidence_sha256": None}]},
        public_image_urls=[url], run_id="no-rights", remote_bytes_by_url={url: raw})
    assert "documentary_photo_rights_binding_required" in refused["blockers"]


def test_admitted_photo_keeps_its_role_and_rights_when_canonical_bytes_match(tmp_path):
    photo = tmp_path / "controlled-photo.png"
    raw = _png(photo, (640, 427), "gray")
    url = "https://substack-post-media.s3.amazonaws.com/public/images/controlled-photo.png"
    asset = {"asset_id": "photo", "media_role": "contextual_photo", "modality": "documentary_photo",
        "path": str(photo), "sha256": sha256_file(photo), "rights_status": "OPEN_LICENSED",
        "rights_evidence_sha256": "controlled-rights", "source_page_url": "https://example.org/photo",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0", "alt_text": "Controlled photo fixture."}
    manifest = build_delivery_media_manifest(media_packet={"assets": [asset]}, public_image_urls=[url],
        run_id="controlled-photo", remote_bytes_by_url={url: raw})
    delivery = select_primary_delivery_media(manifest)
    assert delivery["sha256"] == asset["sha256"]
    assert delivery["media_role"] == "contextual_photo"
    assert delivery["rights_evidence_sha256"] == asset["rights_evidence_sha256"]
    with pytest.raises(ValueError, match="approved_primary_chart"):
        select_primary_chart(manifest)

    no_rights = build_delivery_media_manifest(media_packet={"assets": [{**asset, "rights_evidence_sha256": ""}]},
        public_image_urls=[url], run_id="controlled-photo", remote_bytes_by_url={url: raw})
    assert "documentary_photo_rights_binding_required" in no_rights["blockers"]
    with pytest.raises(ValueError, match="manifest_not_pass"):
        select_primary_delivery_media(no_rights)


def test_native_canonical_readback_binds_photo_for_existing_derivative_delivery(tmp_path, monkeypatch):
    import json
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1

    photo = tmp_path / "controlled-photo.png"
    raw = _png(photo, (640, 427), "gray")
    url = "https://substack-post-media.s3.amazonaws.com/public/images/controlled-photo.png"
    asset = {"asset_id": "photo", "media_role": "contextual_photo", "modality": "documentary_photo",
        "path": str(photo), "sha256": sha256_file(photo), "rights_status": "OPEN_LICENSED",
        "rights_evidence_sha256": "controlled-rights", "source_page_url": "https://example.org/photo",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0", "alt_text": "Controlled photo fixture."}
    monkeypatch.setattr('live_contentops._eight_platform_substack_first_pipeline_impl_v1._durable_intent_inputs',
        lambda _: {"output_dir": tmp_path, "media_assets": [asset]})
    monkeypatch.setattr('live_contentops.media_manifest_authority_v1.read_public_image_bytes', lambda _: raw)

    class ActualReadbackFixture:
        def readback(self, **kwargs):
            return {"verified": True, "public_image_urls": [url]}

    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=ActualReadbackFixture())
    runtime.readback(destination="substack", public_object_id="controlled", public_object_url="https://example.org/p/post",
        intent={"work_item_id": "controlled"})
    manifest = json.loads((tmp_path / "delivery_media_manifest_v1.json").read_bytes())
    delivery = select_primary_delivery_media(manifest)
    assert delivery["verified_public_delivery_url"] == url
    assert delivery["sha256"] == asset["sha256"]
    assert delivery["rights_evidence_sha256"] == asset["rights_evidence_sha256"]


def test_transport_keeps_frozen_text_and_explicit_no_photo_choice(tmp_path, monkeypatch):
    import json
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as owner

    photo = tmp_path / "photo.png"
    _png(photo, (640, 427), "gray")
    context = {"article": {}, "selection": {}, "media": {"assets": [
        {"asset_id": "photo", "path": str(photo)}]}}
    (tmp_path / "run_context_v1.json").write_text(json.dumps(context), encoding="utf-8")
    monkeypatch.setattr(owner, "build_native_derivative_payloads", lambda **_: {
        "threads": {"text": "Rebuilt copy differs", "media_asset_ids": ["photo"]}})
    frozen = {"text": "@attributed-source: Exact accepted copy.", "media_asset_ids": []}
    result = owner._durable_intent_inputs({"output_dir": str(tmp_path),
        "canonical_url": "https://example.org/p/confirmed", "destination_plan": {"destination": "threads"},
        "native_payload": frozen})
    assert result["payloads"]["threads"] == frozen
    assert result["local_media"] == ""
    assert result["media_assets"] == []


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


def test_delivery_fallback_uses_admitted_facts_and_publisher_not_epistemic_state(tmp_path: Path, monkeypatch):
    from live_contentops import rolling_x_grounded_article_media_builder_v1 as builder
    rendered = {}
    actual = builder._render_text_card
    def render(**kwargs):
        rendered.update(kwargs)
        actual(**kwargs)
    monkeypatch.setattr(builder, "_render_text_card", render)
    article = {"title": "The agency scheduled a hearing", "subtitle": "The public hearing will address the submitted proposal.",
        "public_source_bindings": [{"publisher": "Federal agency", "url": "https://example.org/release",
            "published_at_utc": "2026-11-04T12:00:00Z"}]}
    card = build_delivery_only_editorial_card(output_path=tmp_path / "card.png", title=article["title"],
        source_label="CONFIRMED", source_page_url="https://example.org/", article=article)
    assert card["source_label"] == "Federal agency"
    assert card["source_page_url"] == "https://example.org/release"
    assert rendered["body_lines"] == [["What happened", article["subtitle"]]]
    assert rendered["footer_lines"][0] == "Source: Federal agency, November 4, 2026"
    # CC-245: the delivery card is Instagram's portrait size in the site design.
    assert card["width"] == 1080 and card["height"] == 1350


def test_enriched_fallback_preserves_legacy_dispatched_image_bytes(tmp_path: Path):
    from PIL import Image
    target = tmp_path / "delivery_only_editorial_card.png"
    Image.new("RGB", (1350, 1080), "#07111f").save(target)  # a legacy card already sent
    before = target.read_bytes()
    plain = build_delivery_only_editorial_card(output_path=target, title="Retained title",
        source_label="Federal agency", source_page_url="https://example.org/release")
    fresh = build_delivery_only_editorial_card(output_path=target, title="Retained title",
        source_label="Federal agency", source_page_url="https://example.org/release",
        article={"title": "Retained title", "subtitle": "The agency published the retained facts."})
    # CC-245: every new rendering takes a content-bound name; sent bytes never change.
    assert target not in {Path(plain["path"]), Path(fresh["path"])}
    assert Path(plain["path"]) != Path(fresh["path"])
    assert target.read_bytes() == before
    assert Path(fresh["path"]).read_bytes() != before
