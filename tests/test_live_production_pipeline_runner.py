import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from live_contentops.live_production_pipeline_runner_v6 import run_live_production_pipeline


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
def test_run_live_production_pipeline(mock_generate_variants, mock_run_article, tmp_path):
    mock_run_article.return_value = {
        "packet_id": "art_test_packet_123",
        "canonical_article_draft": {"title": "Test Title"}
    }
    
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "image_path": "downloads/test_image.jpg",
        "variant_status": "VARIANT_SCAFFOLD_READY"
    }
    
    # Override output paths for test isolation
    test_article_path = tmp_path / "canonical_article_packet.json"
    
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", test_article_path):
        result = run_live_production_pipeline(
            topic="Yield rates drop",
            editorial_angle="No advice",
            live_run=False
        )
        
        assert result["article_packet_id"] == "art_test_packet_123"
        assert result["platform_variant_packet_id"] == "var_test_packet_456"
        assert result["image_path"] == "downloads/test_image.jpg"
        assert result["variant_status"] == "VARIANT_SCAFFOLD_READY"
        
        assert test_article_path.exists()
        saved_data = json.loads(test_article_path.read_text(encoding="utf-8"))
        assert saved_data["packet_id"] == "art_test_packet_123"


@patch("live_contentops.live_production_pipeline_runner_v6.run_article_engine")
@patch("live_contentops.live_production_pipeline_runner_v6.generate_live_platform_variants")
@patch("live_contentops.live_production_pipeline_runner_v6.time.sleep", return_value=None)
@patch("live_contentops.substack_browser_adapter_v6.execute_substack_post")
@patch("live_contentops.linkedin_browser_adapter_v6.execute_linkedin_post")
@patch("live_contentops.x_browser_adapter_v6.execute_x_post")
@patch("live_contentops.x_browser_adapter_v6.execute_x_comment")
@patch("live_contentops.instagram_adapter_v6.execute_instagram_post")
@patch("live_contentops.facebook_page_adapter_v6.execute_facebook_post")
@patch("live_contentops.telegram_live_adapter_v6.execute_telegram_post")
@patch("live_contentops.threads_adapter_v6.execute_threads_post")
@patch("live_contentops.discord_live_adapter_v6.execute_discord_post")
def test_run_live_production_pipeline_with_dispatch(
    mock_discord, mock_threads, mock_tg, mock_fb, mock_ig, mock_x_comment, mock_x_post, mock_linkedin, mock_substack, mock_sleep, mock_generate_variants, mock_run_article, tmp_path
):
    mock_run_article.return_value = {
        "packet_id": "art_test_packet_123",
        "canonical_article_draft": {"title": "Test Title", "subtitle": "Test Subtitle"}
    }
    
    mock_generate_variants.return_value = {
        "platform_variant_packet_id": "var_test_packet_456",
        "image_path": "downloads/test_image.jpg",
        "public_image_url": "https://example.com/test_image.jpg",
        "variant_status": "VARIANT_SCAFFOLD_READY",
        "variants": {
            "substack": "Substack body",
            "linkedin": "LinkedIn text",
            "telegram": "Telegram summary",
            "threads": "Threads text",
            "discord": "Discord text"
        },
        "variant_threads": {
            "x": ["Tweet 1", "Tweet 2"],
            "threads": ["Threads post 1", "Threads reply 2"]
        }
    }
    
    mock_substack.return_value = {"status": "SUCCESS", "url": "https://substack.com/p/1"}
    mock_linkedin.return_value = {"status": "SUCCESS", "response": {"url": "https://linkedin.com/p/2"}}
    mock_x_post.return_value = {"status": "SUCCESS", "response": {"url": "https://x.com/status/3"}}
    mock_x_comment.return_value = {"status": "SUCCESS"}
    mock_ig.return_value = {"status": "SUCCESS"}
    mock_fb.return_value = {"status": "SUCCESS"}
    mock_tg.return_value = {"status": "SUCCESS"}
    mock_threads.return_value = {"status": "SUCCESS", "id": "threads_1"}
    mock_discord.return_value = {"status": "SUCCESS"}
    
    test_article_path = tmp_path / "canonical_article_packet.json"
    
    with patch("live_contentops.live_production_pipeline_runner_v6.ARTICLE_OUTPUT_PATH", test_article_path):
        result = run_live_production_pipeline(
            topic="Yield rates drop",
            editorial_angle="No advice",
            live_run=False,
            dispatch_live=True
        )
        
        assert result["dispatch_live"] is True
        assert result["dispatch_results"]["substack"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["linkedin"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["x_post"]["status"] == "SUCCESS"
        assert len(result["dispatch_results"]["x_replies"]) == 1
        assert result["dispatch_results"]["instagram"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["facebook"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["telegram"]["status"] == "SUCCESS"
        assert result["dispatch_results"]["threads"]["status"] == "SUCCESS"
        assert len(result["dispatch_results"]["threads_replies"]) == 1
        assert result["dispatch_results"]["discord"]["status"] == "SUCCESS"
        assert mock_sleep.call_count >= 1
