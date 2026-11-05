"""The Fed's full official publisher name reaches the actual channel compiler."""
import pytest

from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _native_preview_bundle, SimpleGeminiNewsroomError, V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


def article(host, publisher):
    return {"title": "Gold before jobs: beyond the Fed's target range",
        "dek": "The Fed's target range and the real Treasury yield are different measures.",
        "substack_body_markdown": "The Fed's target range is a different measure. [[SOURCE:SOURCE_1]]",
        "reader_first_version": "DATA_JOURNALISM_V1",
        "post_visual_destination_media": {d: ["yield-chart"] for d in V1_REQUIRED_DERIVATIVE_DESTINATIONS},
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": publisher,
            "url": "https://" + host + "/newsevents/pressreleases/monetary20261028a.htm"}]}


@pytest.mark.parametrize("publisher", ["Federal Reserve Board", "Board of Governors of the Federal Reserve System"])
def test_fed_full_publisher_name_feeds_all_eight_native_previews(publisher):
    bundle, intents = _native_preview_bundle(article=article("www.federalreserve.gov", publisher),
        article_mode="WEEK_AHEAD_OR_WATCH", article_identity="controlled-fed-watch", media_asset_ids=["yield-chart"],
        epistemic_state={"reader_visible_epistemic_label": "CONFIRMED", "event_confirmation_state": "CONFIRMED",
                         "primary_reporting_publisher": publisher})
    assert bundle["package_count"] == len(intents) == 8
    assert all("Fed" in " ".join(str(v) for k, v in payload.items() if k in {"text", "full_text", "root_text"})
               for payload in bundle["packages"].values())


def test_fed_alias_cannot_cross_a_different_host():
    publisher = "Board of Governors of the Federal Reserve System"
    with pytest.raises(SimpleGeminiNewsroomError, match="native_preview_epistemic_state_missing"):
        _native_preview_bundle(article=article("www.federalreserve.gov.example.org", publisher),
            article_mode="WEEK_AHEAD_OR_WATCH", article_identity="spoof", media_asset_ids=["yield-chart"],
            epistemic_state={"reader_visible_epistemic_label": "CONFIRMED",
                             "primary_reporting_publisher": publisher})


@pytest.mark.parametrize("host,confirmed", [("www.federalreserve.gov", True),
    ("www.federalreserve.gov.example.org", True), ("www.federalreserve.gov", False)])
def test_official_comparison_attributes_relevant_agency_without_first_document_order(host, confirmed):
    value = article(host, "Board of Governors of the Federal Reserve System")
    treasury = "U.S. Department of the Treasury"
    value["public_source_bindings"].insert(0, {"source_id": "SOURCE_2", "publisher": treasury,
        "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates"})
    state = {"reader_visible_epistemic_label": "CONFIRMED" if confirmed else "UNCONFIRMED REPORT — Treasury",
        "event_confirmation_state": "CONFIRMED" if confirmed else "UNCONFIRMED",
        "primary_reporting_publisher": treasury, "source_multiplicity": "MULTI_SOURCE",
        "evidence_basis": "PRIMARY_EVENT_EVIDENCE"}
    kwargs = {"article": value, "article_mode": "WEEK_AHEAD_OR_WATCH", "article_identity": "controlled-multi-agency",
        "media_asset_ids": ["yield-chart"], "epistemic_state": state}
    if host == "www.federalreserve.gov" and confirmed:
        bundle, intents = _native_preview_bundle(**kwargs)
        assert bundle["package_count"] == len(intents) == 8
    else:
        with pytest.raises(SimpleGeminiNewsroomError, match="native_preview_epistemic_state_missing"):
            _native_preview_bundle(**kwargs)
