from live_contentops.google_image_search_v6 import (
    DRY_RUN_IMAGE_SEARCH_BLOCKED,
    DryRunImageSearchBlocked,
    clean_search_query,
    execute_google_image_search_and_download,
    extract_image_candidates_from_html,
    _google_recency_tbs,
)


def test_clean_search_query_expands_us_for_image_relevance():
    assert clean_search_query("US recession risks: oil volatility!") == "United States recession risks oil volatility"


def test_extract_image_candidates_from_classic_and_escaped_html():
    html = """
    <table><img src="/images?q=tbn:thumb123"/></table>
    <img data-src="https://example.com/news/chart.jpg?width=1200"/>
    <script>{"ou":"https:\\/\\/cdn.example.org\\/macro\\/yield-curve.png"}</script>
    <a href="/imgres?imgurl=https%3A%2F%2Fmedia.example.net%2Foil-chart.webp&imgrefurl=https%3A%2F%2Fexample.net"></a>
    """

    urls = extract_image_candidates_from_html(html)

    assert urls[0] == "https://example.com/news/chart.jpg?width=1200"
    assert "https://cdn.example.org/macro/yield-curve.png" in urls
    assert "https://media.example.net/oil-chart.webp" in urls
    assert urls[-1] == "https://www.google.com/images?q=tbn:thumb123"


def test_google_recency_filter_maps_to_classic_query_ranges():
    assert _google_recency_tbs(7) == "qdr:w"
    assert _google_recency_tbs(31) == "qdr:m"
    assert _google_recency_tbs(365) == "qdr:y"
    assert _google_recency_tbs(None) == ""


def test_execute_image_search_blocks_dry_run_before_network():
    try:
        execute_google_image_search_and_download("oil volatility chart", dry_run=True)
    except DryRunImageSearchBlocked as exc:
        assert DRY_RUN_IMAGE_SEARCH_BLOCKED in str(exc)
    else:
        raise AssertionError("dry-run image search should fail closed before network access")
