"""Real writer placement hints never leak into the canonical public consumer."""
from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article


def test_public_article_omits_internal_visual_hints_and_keeps_actual_prose():
    body = ("## Treasury context\n\nThe dated yield was 4.90%. [[SOURCE:SOURCE_1]]\n\n"
            "[[VISUAL:cc124-treasury-chart]] [[SOURCE:SOURCE_1]]\n\n"
            "[[VISUAL:cc124-fed-photo]] [[SOURCE:SOURCE_1]]\n\n"
            "Bitcoin demand remains a separate question. [[SOURCE:SOURCE_1]]")
    article = {"title": "A conditional market watch", "reader_first_version": "DATA_JOURNALISM_V1",
        "substack_body_markdown": body, "public_source_bindings": [{"source_id": "SOURCE_1",
            "url": "https://home.treasury.gov/", "publisher": "U.S. Treasury"}]}
    public = _reader_safe_native_article(article, article_mode="WEEK_AHEAD_OR_WATCH")
    assert public["substack_body_markdown"] == ("## Treasury context\n\nThe dated yield was 4.90%.\n\n"
        "Bitcoin demand remains a separate question.")
    assert article["substack_body_markdown"] == body
