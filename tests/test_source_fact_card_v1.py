"""Bound categorical public facts; no network, native role or public writes."""
from hashlib import sha256

import pytest

from live_contentops.native_desktop_editorial_v1 import validate_release_media
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_source_fact_card, validate_source_value_chart,
)


def controlled_card(tmp_path):
    text = "The Commission will host a roundtable on November 9, 2026, on data risks and costs."
    document = {"url": "https://example.test/announcement", "document_id": "controlled-source",
        "publisher": "Controlled public agency", "published_at_utc": "2026-10-19T00:00:00Z",
        "canonical_content_text": text, "underlying_reuse_classification": "governed_government_public_domain",
        "rights_evidence_sha256": "a" * 64}
    packet = {"schema_version": "contentops.source_fact_card.v1", "title": "Roundtable watch",
        "question": "When is the announced discussion?", "source_url": document["url"],
        "source_content_sha256": sha256(text.encode()).hexdigest(),
        "rows": [{"label": "Scheduled date", "value": "November 9, 2026", "support_excerpt": text},
                 {"label": "Topic", "value": "data risks and costs", "support_excerpt": text}]}
    asset = build_source_fact_card(document, packet=packet, asset_id="event-facts",
        placement_after="The announced event", output_dir=tmp_path)
    return document, asset


def test_categorical_card_uses_existing_renderer_and_release_validator(tmp_path):
    document, asset = controlled_card(tmp_path)
    assert asset["quantitative_chart"] is False
    validate_source_value_chart(asset, [document])
    asset["visual_review"] = {"asset_sha256": asset["sha256"], "pixels_inspected": True,
        "labels_and_units_legible": True, "reviewer": "CONTROLLED_FIXTURE_NOT_LIVE_REVIEW"}
    result = validate_release_media({"media_assets": [asset], "evidence": [document]})
    assert result["chart_count"] == 0 and result["fact_card_count"] == 1


@pytest.mark.parametrize("fault", ["fact", "source", "rights", "packet", "bytes", "question"])
def test_card_rejects_unbound_facts_rights_packet_and_changed_pixels(tmp_path, fault):
    document, asset = controlled_card(tmp_path)
    if fault == "fact": asset["fact_card_packet"]["rows"][0]["value"] = "November 10, 2026"
    elif fault == "source": document["canonical_content_text"] += " changed"
    elif fault == "rights": document["underlying_reuse_classification"] = "unknown"
    elif fault == "packet": asset["transform_sha256"] = "0" * 64
    elif fault == "bytes":
        from pathlib import Path
        Path(asset["path"]).write_bytes(b"CONTROLLED CHANGED FILE")
    elif fault == "question": asset["editorial_data_packet"]["question"] = "Another question"
    with pytest.raises(ValueError): validate_source_value_chart(asset, [document])


def test_facts_card_cannot_substitute_for_quantitative_analysis_history(tmp_path):
    document, asset = controlled_card(tmp_path)
    with pytest.raises(ValueError, match="ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED"):
        validate_release_media({"media_assets": [asset], "evidence": [document],
                                "article": {"news_item_kind": "ANALYSIS"}})
