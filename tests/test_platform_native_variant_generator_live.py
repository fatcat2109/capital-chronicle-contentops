import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from live_contentops.platform_native_variant_generator_live_v6 import (
    generate_live_platform_variants,
    compute_packet_hash
)


def test_compute_packet_hash():
    data1 = {"a": 1, "b": 2, "platform_variant_packet_id": "123"}
    data2 = {"a": 1, "b": 2, "platform_variant_packet_id": "456"}
    assert compute_packet_hash(data1) == compute_packet_hash(data2)


@patch("live_contentops.platform_native_variant_generator_live_v6.call_live_provider")
@patch("live_contentops.platform_native_variant_generator_live_v6.execute_google_image_search_and_download")
def test_generate_live_platform_variants(mock_search_download, mock_call_provider, tmp_path):
    # Mock Google Image search downloader
    mock_search_download.return_value = (str(tmp_path / "downloads" / "img_test.jpg"), "https://example.com/img_test.jpg")
    
    # Mock LLM 9router JSON response
    mock_call_provider.return_value = json.dumps({
        "linkedin": "LinkedIn Live Post content",
        "discord": "Discord Announcements content",
        "telegram": "Telegram channel summary",
        "x_thread": [
            "1/ X Tweet initial post",
            "2/ X Tweet comment thread reply"
        ],
        "threads_thread": [
            "1/ Threads conversational initial post",
            "2/ Threads reply post"
        ]
    })
    
    # Pre-write a dummy canonical article JSON
    article_packet_file = tmp_path / "canonical_article_packet.json"
    article_packet_file.write_text(json.dumps({
        "packet_id": "art_test_123",
        "operator_idea_id": "idea_test_456",
        "canonical_article_draft": {
            "title": "Fed Rate Decision and Yields Volatility",
            "subtitle": "Macro briefing",
            "intro": "Yield rates are moving...",
            "sections": [
                {"title": "Section Title", "body": "Treasury yield detail..."}
            ],
            "conclusion": "Conclusion notes..."
        }
    }), encoding="utf-8")
    
    # Set env keys
    with patch.dict("os.environ", {"NINE_ROUTER_API_KEY": "sk-dummy-123"}):
        packet = generate_live_platform_variants(
            article_packet_path=article_packet_file,
            output_dir=tmp_path,
            live_run=True
        )
        
        assert packet["variant_status"] == "VARIANT_VALIDATION_FAILED"
        assert packet["provider_attempts"][0]["status"] == "accepted"
        assert packet["image_path"] == str(tmp_path / "downloads" / "img_test.jpg")
        assert packet["variants"]["linkedin"].startswith("LinkedIn Live Post content")
        assert packet["variants"]["linkedin"].endswith("not investment advice.")
        assert packet["variants"]["discord"] == "Discord Announcements content"
        assert packet["variants"]["telegram"] == "Telegram channel summary"
        assert packet["variants"]["x"] == "1/ X Tweet initial post\n\n---\n\n2/ X Tweet comment thread reply"
        
        assert packet["variant_threads"]["x"] == ["1/ X Tweet initial post", "2/ X Tweet comment thread reply"]
        assert packet["variant_threads"]["threads"] == ["1/ Threads conversational initial post", "2/ Threads reply post"]
        
        assert (tmp_path / "platform_variant_packet.json").exists()
        assert (tmp_path / "linkedin_variant.md").exists()
        assert (tmp_path / "x_variant.md").exists()
        assert (tmp_path / "telegram_operator_preview.md").exists()


@patch("live_contentops.platform_native_variant_generator_live_v6.call_live_provider", side_effect=TimeoutError("variant timeout"))
@patch("live_contentops.platform_native_variant_generator_live_v6.execute_google_image_search_and_download", return_value=(None, None))
def test_variant_provider_failure_records_recovery_metadata(mock_search_download, mock_call_provider, tmp_path):
    article_packet_file = tmp_path / "canonical_article_packet.json"
    body = " ".join(["Capital Chronicle educational policy liquidity shipping data note with 3.5% source context."] * 180)
    article_packet_file.write_text(json.dumps({
        "packet_id": "art_test_123",
        "operator_idea_id": "idea_test_456",
        "canonical_article_draft": {
            "title": "Fed Rate Decision and Yields Volatility",
            "subtitle": "Macro briefing",
            "intro": body,
            "sections": [{"title": "Policy", "body": body}],
            "conclusion": body,
        }
    }), encoding="utf-8")

    with patch.dict("os.environ", {"NINE_ROUTER_API_KEY": "sk-dummy-123"}):
        packet = generate_live_platform_variants(article_packet_path=article_packet_file, output_dir=tmp_path, live_run=True)

    assert packet["provider_call_made"] is True
    assert packet["provider_recovery_used"] is True
    assert packet["provider_attempts"][0]["failure"].startswith("variant_provider_failed:TimeoutError")
    assert any(f.startswith("variant_provider_failed:TimeoutError") for f in packet["validation_failures"])


@patch("live_contentops.platform_native_variant_generator_live_v6.build_current_macro_visual_pack")
@patch("live_contentops.platform_native_variant_generator_live_v6.execute_google_image_search_and_download")
def test_stale_search_visual_is_replaced_with_source_backed_pack(mock_search_download, mock_source_pack, tmp_path):
    stale_path = tmp_path / "stale_wti.png"
    stale_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 4096)
    stale_path.with_suffix(".json").write_text(json.dumps({
        "url": "https://upload.wikimedia.org/stale-wti.png",
        "source_label": "upload.wikimedia.org",
        "query": "US recession risks oil volatility macro financial chart news",
        "visual_metric": "wti crude oil price chart",
        "time_coverage_end_year": 2023,
        "recent_direction": "down",
    }), encoding="utf-8")
    current_primary = tmp_path / "wti_current.png"
    current_secondary = tmp_path / "wti_recent.png"
    current_primary.write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 4096)
    current_secondary.write_bytes(b"\x89PNG\r\n\x1a\n" + b"2" * 4096)
    mock_search_download.return_value = (str(stale_path), "https://upload.wikimedia.org/stale-wti.png")
    mock_source_pack.return_value = [
        {
            "asset_id": "primary",
            "local_path": str(current_primary),
            "public_url": None,
            "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
            "source_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
            "visual_metric": "oil_volatility wti crude oil current price realized volatility",
            "latest_observation_year": 2026,
            "recent_direction": "up",
            "caption": "WTI price and realized volatility through 2026-07-07.",
        },
        {
            "asset_id": "recent_price",
            "local_path": str(current_secondary),
            "public_url": None,
            "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
            "source_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
            "visual_metric": "wti crude oil current recent price path",
            "latest_observation_year": 2026,
            "recent_direction": "up",
            "caption": "Recent WTI price path through 2026-07-07.",
        },
    ]
    body = " ".join(["source data oil volatility reported 3.5% across 12 months and 75 bps context."] * 220)
    article_packet_file = tmp_path / "canonical_article_packet.json"
    article_packet_file.write_text(json.dumps({
        "packet_id": "art_oil_123",
        "operator_idea_id": "idea_oil_456",
        "canonical_article_draft": {
            "title": "Capital Chronicle Educational Briefing: US recession risks rise as oil volatility spikes",
            "subtitle": "Current oil volatility context",
            "intro": body,
            "sections": [
                {"title": "Macro setup", "body": body},
                {"title": "Market implications", "body": body},
                {"title": "Source review", "body": body},
            ],
            "conclusion": body,
            "visual_slots": [
                {"asset_id": "primary"},
                {"asset_id": "recent_price"},
            ],
        },
    }), encoding="utf-8")

    packet = generate_live_platform_variants(article_packet_path=article_packet_file, output_dir=tmp_path, live_run=False)

    assert packet["image_path"] == str(current_primary)
    audit = packet["media_manifest"]["media_content_audit"]
    assert audit["audit_status"] == "PASS"
    assert "source_backed_chart_pack_selected" in audit["replacement_notes"]
    assert "[[VISUAL:primary]]" in packet["variants"]["substack"]
    assert "[[VISUAL:recent_price]]" in packet["variants"]["substack"]
    assert "upload.wikimedia.org" not in packet["variants"]["substack"]
    assert packet["media_manifest"]["news_image_source_label"].startswith("FRED series DCOILWTICO")
