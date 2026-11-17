"""The existing source, writer, compiler and write boundary consume all families."""
from copy import deepcopy
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import desk_evidence
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.cpi_reaction_page_v1 import (
    EVENT_PAGES, TOKEN, bind_tables, validate_bound_tables, writer_guidance,
)
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom
from test_cpi_reaction_page_cc425 import record
from live_contentops import event_reaction_source_v1 as held


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


def held_table():
    rows, events = [], []
    for family in ("NFP", "FOMC_DECISION", "FOMC_PRESS_CONFERENCE", "PPI"):
        event_id = family + "-20240105"
        events.append({"event_id": event_id, "family": family, "event_date": "2024-01-05"})
        rows.append({"event_id": event_id, "family": family, "symbol": "XAUUSD", "series_id": "HISTDATA:XAUUSD",
            "released_at_utc": "2024-01-05T13:30:00Z" if family in {"NFP", "PPI"} else None,
            "price_basis": "BID", "surprises": [{"private_raw_consensus": 987654321}],
            "windows": {key: {"move_bps": -23.537841 if family in {"NFP", "PPI"} else None,
                              "missing_reason": None if family in {"NFP", "PPI"} else "EXACT_RELEASE_CLOCK_NOT_HELD"}
                        for key in held.HORIZONS}})
    return {"schema": "EventWeightDecayTableV1", "as_of_utc": "2026-11-10T11:30:00Z", "events": events, "rows": rows}


def test_held_cells_feed_the_existing_desk_writer_with_original_clock_and_separate_fomc_windows(tmp_path):
    import json
    from live_contentops.capital_chronicle_desk_record_source_v1 import read_export
    from live_contentops.reader_article_contract_v1 import source_clock
    path = tmp_path / "table.json"
    path.write_text(json.dumps(held_table()))
    results = held.prepare(path, tmp_path / "sources", generated_at_utc="2026-11-11T18:00:00+00:00", producer_commit="a" * 40)
    assert {r["family"] for r in results} == {"NFP", "FOMC", "PPI"}
    before = {}
    for result in results:
        pointer = json.loads(Path(result["binding_path"]).read_bytes())
        spec, = pointer["desk_record_exports"]
        records = read_export(spec, cutoff_utc="2026-11-11T18:01:00Z")
        evidence = desk_evidence(records, {"headline_ids": [records[0]["headline_id"]]})
        pack = newsroom._source_pack(evidence["evidence_documents"])
        assert source_clock(pack).startswith("2026-11-10T11:30:00")
        article = bind_tables({"substack_body_markdown": TOKEN}, pack)
        validate_bound_tables(article)
        assert "987654321" not in article["substack_body_markdown"]
        assert "UTC" not in article["substack_body_markdown"]
        if result["family"] == "FOMC":
            assert "Fed statement" in article["substack_body_markdown"]
            assert "Fed press conference" in article["substack_body_markdown"]
            assert result["observed_moves"] == 0 and "—" in article["substack_body_markdown"]
        else:
            assert "-23.5378" in article["substack_body_markdown"] and "8:30 AM ET" in article["substack_body_markdown"]
        before[spec["path"]] = Path(spec["path"]).read_bytes()
    held.prepare(path, tmp_path / "sources", generated_at_utc="2026-11-12T18:00:00Z", producer_commit="a" * 40)
    assert all(Path(p).read_bytes() == b for p, b in before.items())
