from pathlib import Path

from live_contentops.media_diversification_audit_v6 import audit_media_manifest


def _asset(asset_id: str, media_class: str, path: str, **extra):
    base = {
        "asset_id": asset_id,
        "media_class": media_class,
        "local_path": path,
        "source_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
        "source_page_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
        "source_label": "FRED / EIA",
        "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
        "source_domain": "fred.stlouisfed.org",
        "rights_status": "source_backed_generated_visual_cc_owned",
        "provenance_status": "source_backed_generated_from_public_data",
        "operator_review_required": False,
        "why_selected": "Supports the oil volatility thesis with source-backed evidence.",
        "latest_observation_year": 2026,
        "latest_observation_date": "2026-06-29",
        "visual_metric": "oil_volatility wti crude oil current price realized volatility",
        "recent_direction": "up",
    }
    base.update(extra)
    return base


def test_media_manifest_passes_with_chart_context_and_supporting_visual(tmp_path):
    assets = [
        _asset("primary", "data_chart", str(tmp_path / "primary.png")),
        _asset("recent_price", "data_chart", str(tmp_path / "recent.png"), visual_metric="wti crude oil recent price path"),
        _asset(
            "hormuz_context",
            "map_or_geography",
            str(tmp_path / "hormuz.png"),
            source_url="https://www.eia.gov/todayinenergy/detail.php?id=65504",
            source_page_url="https://www.eia.gov/todayinenergy/detail.php?id=65504",
            source_domain="eia.gov",
            source_label="U.S. Energy Information Administration",
            canonical_source_label="EIA Strait of Hormuz oil chokepoint context",
            visual_metric="oil geopolitics strait hormuz chokepoint energy supply risk",
            recent_direction="contextual",
            why_selected="Adds contextual geopolitical map evidence for the oil-volatility thesis.",
        ),
    ]

    audit = audit_media_manifest(
        {"media_assets": assets},
        article_title="US recession risks rise as oil volatility spikes",
        article_text="Current oil volatility and geopolitics shape the macro evidence map.",
        as_of_date="2026-07-08",
    )

    assert audit["audit_status"] == "PASS"
    assert audit["auto_publication_safe"] is True
    assert audit["asset_count"] == 3
    assert "map_or_geography" in audit["media_classes"]


def test_media_manifest_rejects_chart_only_package(tmp_path):
    assets = [
        _asset("primary", "data_chart", str(tmp_path / "primary.png")),
        _asset("recent_price", "data_chart", str(tmp_path / "recent.png"), visual_metric="wti crude oil recent price path"),
        _asset("third_chart", "data_chart", str(tmp_path / "third.png"), visual_metric="wti crude oil chart"),
    ]

    audit = audit_media_manifest(
        {"media_assets": assets},
        article_title="US recession risks rise as oil volatility spikes",
        article_text="Oil volatility rises in a geopolitical macro setup.",
        as_of_date="2026-07-08",
    )

    assert audit["audit_status"] == "FAIL"
    assert "media_mix_missing_contextual_image_or_map" in audit["blockers"]
    assert "media_mix_repeated_chart_only" in audit["blockers"]


def test_media_manifest_passes_with_fed_funds_policy_diagram(tmp_path):
    assets = [
        _asset(
            "primary",
            "data_chart",
            str(tmp_path / "fed_funds_primary.png"),
            source_url="https://fred.stlouisfed.org/series/DFF",
            source_page_url="https://fred.stlouisfed.org/series/DFF",
            source_label="FRED / Federal Reserve Board",
            canonical_source_label="FRED series DFF; source Board of Governors of the Federal Reserve System H.15",
            visual_metric="fed funds policy rates effective federal funds rate policy corridor iorb interest rate context",
            why_selected="Primary source-backed chart for the effective fed funds rate and policy corridor.",
            recent_direction="flat",
            latest_observation_date="2026-07-07",
        ),
        _asset(
            "policy_corridor",
            "policy_diagram",
            str(tmp_path / "policy_corridor.png"),
            source_url="https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
            source_page_url="https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
            source_label="Federal Reserve Board",
            canonical_source_label="Federal Reserve policy corridor, IORB, ON RRP, standing repo, and primary credit context",
            visual_metric="fed funds policy corridor iorb on rrp standing repo administered rates",
            why_selected="Adds contextual policy-corridor evidence for the fed-funds article.",
            recent_direction="contextual",
        ),
        _asset(
            "sofr_context",
            "data_chart",
            str(tmp_path / "sofr_context.png"),
            source_url="https://www.newyorkfed.org/markets/reference-rates/sofr",
            source_page_url="https://www.newyorkfed.org/markets/reference-rates/sofr",
            source_label="Federal Reserve Bank of New York",
            canonical_source_label="NY Fed SOFR methodology context and Federal Reserve H.15 selected interest rates",
            visual_metric="fed funds sofr treasury rates overnight policy interest rate context",
            why_selected="Adds SOFR and Treasury-rates context without commodity-family visuals.",
            recent_direction="contextual",
        ),
    ]

    audit = audit_media_manifest(
        {"media_assets": assets},
        article_title="Fed Funds at 3.63 Percent: Reading the Policy Corridor Without Overreach",
        article_text="The article explains DFF, policy corridor, IORB, SOFR, and Treasury rates.",
        as_of_date="2026-07-09",
    )

    assert audit["audit_status"] == "PASS"
    assert audit["auto_publication_safe"] is True
    assert "policy_diagram" in audit["media_classes"]


def test_search_like_asset_requires_recency_and_rights_metadata(tmp_path):
    assets = [
        _asset("primary", "data_chart", str(tmp_path / "primary.png")),
        {
            "asset_id": "google_candidate",
            "media_class": "news_context_image",
            "local_path": str(tmp_path / "news.png"),
            "retrieval_method": "google_image_or_public_fallback",
            "query": "oil volatility hormuz news image",
            "source_url": "https://example.com/news-photo.jpg",
            "source_label": "example.com",
        },
        _asset("recent_price", "data_chart", str(tmp_path / "recent.png"), visual_metric="wti crude oil recent price path"),
    ]

    audit = audit_media_manifest(
        {"media_assets": assets},
        article_title="US recession risks rise as oil volatility spikes",
        article_text="Oil volatility and Hormuz risk are current topics.",
        as_of_date="2026-07-08",
    )

    assert audit["audit_status"] == "FAIL"
    assert any(item.startswith("search_image_metadata_missing:google_candidate:") for item in audit["blockers"])
    assert "media_rights_operator_review_required:google_candidate" in audit["review_items"]
