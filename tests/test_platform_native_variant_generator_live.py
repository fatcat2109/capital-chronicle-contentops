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
