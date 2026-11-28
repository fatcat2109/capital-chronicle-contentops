import json
from unittest.mock import patch, MagicMock
from live_contentops.grounded_search_engine_v6 import (
    execute_grounded_search,
    clean_query,
    query_yahoo_finance,
)


def test_clean_query():
    assert clean_query("US Non-Farm Payrolls (NFP) Volatility!") == "US Non-Farm Payrolls NFP Volatility"
    assert clean_query("Geopolitical crisis - Middle East & oil?") == "Geopolitical crisis - Middle East  oil"


@patch("urllib.request.urlopen")
def test_execute_grounded_search_mock(mock_urlopen, tmp_path):
    # Set cache dir to temp path
    with patch("live_contentops.grounded_search_engine_v6.CACHE_DIR", tmp_path):
        # Mock GDELT response (CC-024: Yahoo Finance search is retired; only GDELT is called)
        mock_resp_gdelt = MagicMock()
        mock_resp_gdelt.read.return_value = json.dumps({
            "articles": [
                {
                    "title": "Fed Rates Decision Impact",
                    "source": "Reuters",
                    "url": "https://reuters.com/fed-decision-impact",
                    "seendate": "2026-07-06T12:00:00Z",
                }
            ]
        }).encode("utf-8")

        mock_context_gdelt = MagicMock()
        mock_context_gdelt.__enter__.return_value = mock_resp_gdelt
        mock_urlopen.side_effect = [mock_context_gdelt]

        results = execute_grounded_search("mock test query", limit_per_source=2)

        assert len(results) == 1
        assert mock_urlopen.call_count == 1
        assert results[0]["title"] == "Fed Rates Decision Impact"
        assert results[0]["publisher_or_origin"] == "Reuters"
        assert results[0]["url_or_local_reference"] == "https://reuters.com/fed-decision-impact"
        assert results[0]["synthetic_fixture"] is False

        # Verify cache file was created
        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 1

        # Next run should load from cache and urlopen should not be called again
        mock_urlopen.reset_mock()
        results_cached = execute_grounded_search("mock test query", limit_per_source=2)
        assert len(results_cached) == 1
        mock_urlopen.assert_not_called()

        # Retired Yahoo Finance helper must make zero HTTP calls and return []
        assert query_yahoo_finance("Fed rates") == []
        mock_urlopen.assert_not_called()
