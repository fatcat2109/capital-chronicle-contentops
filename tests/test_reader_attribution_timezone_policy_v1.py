"""Reader presentation changes preserve claim/rights bindings and the source instant."""
from copy import deepcopy

import pytest

from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _reader_first_worker_prompt, _reader_safe_native_article, reader_timestamp,
)


def test_default_omits_generated_sources_and_cutoff_without_erasing_attribution_or_authored_credit():
    article = {"title": "Attributed report", "dek": "FirstSquawk, citing WSJ, reports a diplomatic effort.",
        "reader_first_version": "DATA_JOURNALISM_V1", "source_date_notice": "Internal UTC/source clock record.",
        "substack_body_markdown": "FirstSquawk, citing WSJ, reports an effort. [[SOURCE:SOURCE_1]]\n\n"
            "Reuters reported no dialogue on 21 October; a breakthrough remains unconfirmed. [[SOURCE:SOURCE_2]]\n\n"
            "Photo: [Chris](https://commons.wikimedia.org/example), [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/).",
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "FirstSquawk", "url": "https://x.com/example"},
            {"source_id": "SOURCE_2", "publisher": "Reuters", "url": "https://example.org/reuters"}]}
    before = deepcopy(article)
    output = _reader_safe_native_article(article, article_mode="BREAKING_BRIEF")
    assert article == before
    body = output["substack_body_markdown"]
    assert "### Sources" not in body and "https://x.com/example" not in body
    assert "FirstSquawk, citing WSJ" in body and "breakthrough remains unconfirmed" in body
    assert "21 October" in body and "CC BY-SA 2.0" in body and "commons.wikimedia.org" in body
    assert "SOURCE_" not in body and "Internal UTC" not in output["editorial_scope_notice"]
    historical = _reader_safe_native_article(article, article_mode="BREAKING_BRIEF", legacy_presentation=True)
    assert "### Sources" in historical["substack_body_markdown"]


def test_authored_meaningful_notes_and_required_link_are_not_blindly_stripped():
    article = {"reader_first_version": "DATA_JOURNALISM_V1", "title": "Revenue", "dek": "Company report",
        "substack_body_markdown": "The [[CITE:SOURCE_1|company release]] defines the metric. [[SOURCE:SOURCE_1]]\n\n"
            "### Notes\n\nRevenue is USD millions for Q3, actual; excludes the divested business. [[SOURCE:SOURCE_1]]",
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "Company", "url": "https://example.org/terms"}]}
    body = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert "[company release](https://example.org/terms)" in body
    assert "USD millions for Q3, actual" in body and "divested business" in body
    assert "### Sources" not in body


@pytest.mark.parametrize("instant,expected", [
    ("2026-10-27T04:00:52.972454Z", "00:00 EDT on 27 October 2026"),
    ("2026-01-15T04:30:00Z", "23:30 EST on 14 January 2026"),
    ("2026-03-08T06:59:00Z", "01:59 EST on 8 March 2026"),
    ("2026-03-08T07:00:00Z", "03:00 EDT on 8 March 2026"),
    ("2026-11-01T05:30:00Z", "01:30 EDT on 1 November 2026"),
    ("2026-11-01T06:30:00Z", "01:30 EST on 1 November 2026"),
    ("2026-10-27", "2026-10-27"),
])
def test_reader_time_uses_actual_dst_and_preserves_unknown_precision(instant, expected):
    assert reader_timestamp(instant) == expected


def test_utc_alternative_and_no_naive_or_invented_time():
    assert reader_timestamp("2026-10-27T04:00:52Z", zone="UTC") == "04:00 UTC on 27 October 2026"
    with pytest.raises(ValueError, match="AWARE_INSTANT"):
        reader_timestamp("2026-10-27T04:00:52")


def test_actual_writer_prompt_has_default_and_accuracy_exceptions():
    text = _reader_first_worker_prompt("Frozen source/claim contract.", {"reader_first_version": "DATA_JOURNALISM_V1"})
    assert "without discretionary Sources/References" in text
    assert "natural claim attribution, relay qualification" in text and "mandatory quotation/photo/reuse" in text
    assert "America/New_York" in text and "hardcode UTC-5" in text
