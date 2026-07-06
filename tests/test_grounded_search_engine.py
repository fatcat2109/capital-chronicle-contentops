import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from live_contentops.grounded_search_engine_v6 import execute_grounded_search, clean_query


def test_clean_query():
    assert clean_query("US Non-Farm Payrolls (NFP) Volatility!") == "US Non-Farm Payrolls NFP Volatility"
    assert clean_query("Geopolitical crisis - Middle East & oil?") == "Geopolitical crisis - Middle East  oil"


@patch("urllib.request.urlopen")
def test_execute_grounded_search_mock(mock_urlopen, tmp_path):
    # Set cache dir to temp path
    with patch("live_contentops.grounded_search_engine_v6.CACHE_DIR", tmp_path):
        # Mock GDELT response
        mock_resp_gdelt = MagicMock()
        mock_resp_gdelt.read.return_value = json.dumps({
            "articles": [
                {
                    "title": "Fed Rates Decision Impact",
                    "source": "Reuters",
                    "url": "https://reuters.com/fed-decision-impact",
                    "seendate": "2026-07-06T12:00:00Z"
                }
            ]
        }).encode("utf-8")
        
        mock_context_gdelt = MagicMock()
        mock_context_gdelt.__enter__.return_value = mock_resp_gdelt
        
        # Mock Yahoo Finance response
        mock_resp_yahoo = MagicMock()
        mock_resp_yahoo.read.return_value = json.dumps({
            "news": [
                {
                    "title": "Tech Stocks Volatility Review",
                    "publisher": "Yahoo Finance",
                    "link": "https://finance.yahoo.com/tech-stocks-volatility",
                    "providerPublishTime": 1783327000
                }
            ]
        }).encode("utf-8")
        
        mock_context_yahoo = MagicMock()
        mock_context_yahoo.__enter__.return_value = mock_resp_yahoo
        
        mock_urlopen.side_effect = [mock_context_gdelt, mock_context_yahoo]
        
        results = execute_grounded_search("mock test query", limit_per_source=2)
        
        assert len(results) == 2
        assert results[0]["title"] == "Fed Rates Decision Impact"
        assert results[0]["publisher_or_origin"] == "Reuters"
        assert results[0]["url_or_local_reference"] == "https://reuters.com/fed-decision-impact"
        assert results[0]["synthetic_fixture"] is False
        
        assert results[1]["title"] == "Tech Stocks Volatility Review"
        assert results[1]["publisher_or_origin"] == "Yahoo Finance"
        assert results[1]["url_or_local_reference"] == "https://finance.yahoo.com/tech-stocks-volatility"
        assert results[1]["synthetic_fixture"] is False
        
        # Verify cache file was created
        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 1
        
        # Next run should load from cache and urlopen should not be called again
        mock_urlopen.reset_mock()
        results_cached = execute_grounded_search("mock test query", limit_per_source=2)
        assert len(results_cached) == 2
        mock_urlopen.assert_not_called()
