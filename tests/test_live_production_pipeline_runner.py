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
