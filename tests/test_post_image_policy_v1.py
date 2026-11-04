"""Decision 61's owned fallback; fixture facts are not publication evidence."""
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_post_image_card, post_image_view, validate_post_image_card,
)
from live_contentops.native_desktop_editorial_v1 import validate_release_media


def packet():
    return {"article": {"title": "A scheduled release: what is known", "subtitle": "The next release is still ahead.",
            "substack_body_markdown": "Admitted fixture copy. Analysis, not financial advice.",
            "news_item_kind": "NEWS"}, "evidence": [], "media_assets": [],
            "accepted_evidence_sha256": "a" * 64}


def test_missing_or_uncleared_optional_media_gets_owned_card_on_all_eight_channels(tmp_path):
    result = packet()
    result["media_assets"] = [{"asset_id": "uncleared-photo", "modality": "documentary_photo", "sha256": "b" * 64}]
    original = deepcopy(result)
    view = post_image_view(result, output_dir=tmp_path / "media")
    assert result == original
    assert len(view["media_assets"]) == 1
    card = view["media_assets"][0]
    assert set(view["article"]["native_destination_media"]) == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert all(ids == [card["asset_id"]] for ids in view["article"]["native_destination_media"].values())
    assert view["post_image_policy"]["excluded_optional_assets"][0]["asset_id"] == "uncleared-photo"
    validate_post_image_card(card, article=result["article"], accepted_evidence_sha256="a" * 64)
    assert validate_release_media(view, require_pixel_review=False)["fact_card_count"] == 1
    assert card["post_card_binding"]["title"] == result["article"]["title"]


def test_card_rejects_missing_admission_changed_copy_changed_bytes_and_prediction_numbers(tmp_path):
    result = packet()
    with pytest.raises(ValueError, match="ADMITTED_ARTICLE_AND_EVIDENCE"):
        build_post_image_card(result["article"], output_dir=tmp_path, accepted_evidence_sha256=None)
    card = build_post_image_card(result["article"], output_dir=tmp_path, accepted_evidence_sha256="a" * 64)
    with pytest.raises(ValueError, match="ADMITTED_COPY_CHANGED"):
        validate_post_image_card(card, article={**result["article"], "title": "Different facts"})
    with pytest.raises(ValueError, match="ADMITTED_EVIDENCE_CHANGED"):
        validate_post_image_card(card, accepted_evidence_sha256="c" * 64)
    with pytest.raises(ValueError, match="PREDICTION_MARKET_NUMBER_FORBIDDEN"):
        build_post_image_card({**result["article"], "title": "Polymarket odds are 55%"}, output_dir=tmp_path,
                              accepted_evidence_sha256="a" * 64)
    from pathlib import Path
    Path(card["path"]).write_bytes(b"changed image")
    with pytest.raises(ValueError, match="ADMISSION_OR_BYTES_CHANGED"):
        validate_post_image_card(card)


def test_owned_card_does_not_replace_required_official_history_for_release_analysis(tmp_path):
    result = packet()
    result["article"]["news_item_kind"] = "ANALYSIS"
    view = post_image_view(result, output_dir=tmp_path)
    with pytest.raises(ValueError, match="ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED"):
        validate_release_media(view, require_pixel_review=False)


def test_owned_card_is_deterministic_and_retains_only_admitted_headline_facts(tmp_path):
    result = packet()
    first = post_image_view(result, output_dir=tmp_path)
    second = post_image_view(result, output_dir=tmp_path)
    assert first == second
    card = first["media_assets"][0]
    assert card["quantitative_chart"] is False
    assert card["post_card_binding"]["article_body_sha256"] == sha256(result["article"]["substack_body_markdown"].encode()).hexdigest()
    assert card["underlying_source_rights_status"] != "public_domain"


def test_current_editor_channel_choices_survive_image_selection(tmp_path):
    result = packet()
    first = build_post_image_card(result["article"], output_dir=tmp_path / "first", accepted_evidence_sha256="a" * 64)
    second = deepcopy(first)
    second["asset_id"] = "second-current-card"
    from pathlib import Path
    second_path = tmp_path / "second.png"
    second_path.write_bytes(Path(first["path"]).read_bytes())
    second["path"] = str(second_path)
    result["media_assets"] = [first, second]
    result["visual_editorial_decision"] = {
        "channel_media": {d: [second["asset_id"]] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS},
        "charts": [],
    }
    view = post_image_view(result, output_dir=tmp_path)
    assert all(ids == [second["asset_id"]] for ids in view["article"]["native_destination_media"].values())


def test_fact_card_renders_admitted_periods_units_and_real_source(tmp_path, monkeypatch):
    from pathlib import Path
    import json
    from live_contentops import rolling_x_grounded_article_media_builder_v1 as builder
    article = json.loads((Path(__file__).parent / "evidence/cc-142/reader-chart-revision.json").read_text(encoding="utf-8"))["article"]
    actual_render = builder._render_text_card
    captured = {}
    def render(**kwargs):
        captured.update(kwargs)
        actual_render(**kwargs)
    monkeypatch.setattr(builder, "_render_text_card", render)
    card = build_post_image_card(article, output_dir=tmp_path, accepted_evidence_sha256="a" * 64)
    observed = [c["text"] for c in article["epistemic_claims"] if c["layer"] == "OBSERVED_FACT"][:2]
    assert [text for _, text in captured["body_lines"]] == observed
    assert "0.6%" in captured["body_lines"][0][1] and "seasonally adjusted" in captured["body_lines"][0][1]
    assert "3.7%" in captured["body_lines"][1][1] and "not seasonally adjusted" in captured["body_lines"][1][1]
    assert captured["footer_lines"][0] == "Source: U.S. Bureau of Labor Statistics"
    assert card["source_label"] == "U.S. Bureau of Labor Statistics"
    validate_post_image_card(card, article=article, accepted_evidence_sha256="a" * 64)
    changed = deepcopy(article)
    changed["epistemic_claims"][0]["text"] = "A changed admitted fact"
    with pytest.raises(ValueError, match="ADMITTED_FACTS_OR_SOURCE_CHANGED"):
        validate_post_image_card(card, article=changed)


def test_article_without_numbers_still_supplies_its_admitted_context(tmp_path):
    result = packet()
    result["article"]["subtitle"] = ""
    result["article"]["substack_body_markdown"] = "The agency announced a scheduled hearing.\n\nAnalysis, not financial advice."
    card = build_post_image_card(result["article"], output_dir=tmp_path, accepted_evidence_sha256="a" * 64)
    assert card["post_card_binding"]["display_content"]["body_lines"] == [
        ["What happened", "The agency announced a scheduled hearing."]]
