"""Exact-post repair preserves authored text and original media while adding its bound card."""
from copy import deepcopy
import pytest

from live_contentops.event_media_order_repair_v1 import ordered_view
from live_contentops.post_visuals_v1 import _bound_fact


def test_event_repair_keeps_text_and_original_media_and_leads_with_actual_card(monkeypatch):
    checked = []
    monkeypatch.setattr("live_contentops.post_visuals_v1.validate_post_data_card",
        lambda card, article, documents: checked.append(card["asset_id"]))
    original = {"article": {"article_type": "EVENT_PREVIEW", "substack_body_markdown": "Exact authored text.",
        "lead_image_asset_id": "history", "visual_editorial_decision": {"charts": [{"asset_id": "history", "placement_after": "History"}]}},
        "evidence": [], "media_assets": [{"asset_id": "history", "sha256": "a", "modality": "source_backed_chart", "placement_after": "History"},
            {"asset_id": "snapshot", "sha256": "b", "modality": "tradingview_chart_snapshot", "placement_after": "introduction"}]}
    retained = deepcopy(original)
    view = ordered_view(original, {"asset_id": "reaction", "sha256": "c", "modality": "source_bound_data_card"})
    assert checked == ["reaction"] and original == retained
    assert view["article"]["substack_body_markdown"] == retained["article"]["substack_body_markdown"]
    assert [a["asset_id"] for a in view["media_assets"]] == ["reaction", "snapshot", "history"]
    assert view["media_assets"][-1] == retained["media_assets"][0]
    assert view["media_assets"][1]["sha256"] == "b"


def test_event_repair_refuses_an_unbound_card():
    with pytest.raises(ValueError, match="DATA_CARD_PACKET_REQUIRED"):
        ordered_view({"article": {"article_type": "EVENT_PREVIEW"}, "media_assets": []}, {})


def test_bound_bls_calendar_time_reaches_actual_card_consumer_in_et():
    citation = "export#calendar/scheduled_at_utc"
    source = {"source_id": "SOURCE_1", "document_id": "calendar", "publisher": "Capital Chronicle",
        "url": "urn:cc-desk:calendar", "canonical_content_text": citation + " = 2026-11-10T13:30:00Z",
        "desk_record_binding": {"fields": [{"citation": citation, "value": "2026-11-10T13:30:00Z"}],
            "sources": [{"rights_class": "BLS_OFFICIAL_PUBLIC_DERIVED", "url": "https://www.bls.gov/schedule/",
                "raw_sha256": "a" * 64, "provider": "U.S. Bureau of Labor Statistics"}]}}
    text = "CPI is scheduled for 10 November 2026 at 08:30 ET."
    article = {"substack_body_markdown": text}
    claim = {"claim_id": "clock", "claim_text": text, "source_id": "SOURCE_1", "support_excerpt": source["canonical_content_text"]}
    fact = _bound_fact(claim, article, [source])
    assert fact["text"] == text and fact["url"] == "https://www.bls.gov/schedule/"
    assert fact["publisher"] == "U.S. Bureau of Labor Statistics"
    wrong = text.replace("08:30", "08:45")
    with pytest.raises(ValueError, match="FACT_OR_NUMBER"):
        _bound_fact({**claim, "claim_text": wrong}, {"substack_body_markdown": wrong}, [source])
