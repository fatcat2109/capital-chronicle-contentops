"""The existing source, writer, compiler and write boundary consume all families."""
from copy import deepcopy

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import desk_evidence
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.cpi_reaction_page_v1 import (
    EVENT_PAGES, TOKEN, bind_tables, validate_bound_tables, writer_guidance,
)
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom
from test_cpi_reaction_page_cc425 import record


def event_pack(family):
    value = deepcopy(record())
    binding = value["binding"]
    binding["record_id"] = EVENT_PAGES[family]["record_id"]
    binding["fields"][0]["citation"] = "cc468#" + binding["record_id"] + "/sections/reaction-tables/body_markdown"
    value["headline"]["source_url"] = "urn:cc-public-report:desk:" + sha256_of(binding)
    return newsroom._source_pack(desk_evidence([value], {"headline_ids": ["cpi"]})["evidence_documents"])


@pytest.mark.parametrize("family", ["NFP", "FOMC", "PPI"])
def test_families_reach_existing_writer_and_exact_rendered_table_consumer(family):
    from live_contentops.article_rich_text_v1 import markdown_to_rich_text, rich_text_to_html
    pack = event_pack(family)
    assert len(pack[0]["canonical_content_text"]) > newsroom.MAX_SOURCE_TEXT_CHARS
    assert EVENT_PAGES[family]["title"] in writer_guidance(pack)
    assert EVENT_PAGES[family]["title"] in newsroom._worker_prompt({"source_pack": pack})
    article = bind_tables({"substack_body_markdown": "We think the sample needs context.\n\n" + TOKEN}, pack)
    assert article["cpi_reaction_page"]["record_id"] == EVENT_PAGES[family]["record_id"]
    validate_bound_tables(article)
    html = rich_text_to_html(markdown_to_rich_text(article["substack_body_markdown"]))
    assert html.count("<table>") == 2
    assert "-0.2353%" in html and "—" in html
    changed = {**article, "substack_body_markdown": article["substack_body_markdown"].replace("-0.2353%", "0.2353%", 1)}
    with pytest.raises(ValueError, match="TABLE_CHANGED_OR_MISSING"):
        validate_bound_tables(changed)


def test_cross_family_source_cannot_relabel_the_original_tables():
    article = bind_tables({"substack_body_markdown": TOKEN}, event_pack("NFP"))
    # The original table bytes happen to match this fixture, but the binding
    # always names the actual source record, never the caller's claimed family.
    article["cpi_reaction_page"]["record_id"] = EVENT_PAGES["FOMC"]["record_id"]
    rebound = bind_tables(article, event_pack("NFP"))
    assert rebound["cpi_reaction_page"]["record_id"] == EVENT_PAGES["NFP"]["record_id"]
