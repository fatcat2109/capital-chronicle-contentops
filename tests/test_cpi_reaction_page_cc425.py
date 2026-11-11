import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import desk_evidence
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.cpi_reaction_page_v1 import (
    RECORD_ID, TOKEN, bind_tables, record_projection, tables, validate_bound_tables,
)
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom


def record():
    # Exceeds the ordinary source limit and includes Unicode missing cells.
    first = "| Release | Market | Series | +5m | +30m | Close | Next close | Knowledge basis |\n|---|---|---|---:|---:|---:|---:|---|\n"
    first += "\n".join(f"| 2024-01-{i:02d} | XAUUSD | HISTDATA:XAUUSD | -0.2353% | +0.1000% | 0.0000% | — | RETAINED_LATER_OBSERVATION |"
                       for i in range(1, 29))
    body = ("Computed changes, not isolated CPI effects.\n\n" + first + "\n\n"
            + "Source context. " * 2500
            + "\n\n## Coverage\n\n| Market | observed | eligible |\n|---|---:|---:|\n| US500 | 2 | 33 |"
            + "\n\n## The desk's map\n\nIts result is not yet due at the original source clock.")
    binding = {"record_id": RECORD_ID, "record_type": "published_report", "fixture": False,
        "export_id": "test-cpi", "export_bytes_sha256": "a" * 64,
        "asset_ids": [], "event_ids": [], "sources": [{"source_id": "cc-cpi-calculations",
            "provider": "Capital Chronicle", "url": None,
            "rights_class": "CC_OWN_ANALYSIS",
            "attribution": "Capital Chronicle calculations; price proxies as labelled"}],
        "fields": [{"field_path": "/sections/reaction-tables/body_markdown",
                    "citation": "test-cpi#" + RECORD_ID + "/sections/reaction-tables/body_markdown",
                    "value": body, "display": body, "source_ids": ["cc-cpi-calculations"]}]}
    return {"binding": binding, "headline_id": "cpi", "known_at_utc": "2026-11-10T09:31:46Z",
            "text": body, "headline": {"source_url": "urn:cc-public-report:desk:" + sha256_of(binding)}}


def pack():
    return newsroom._source_pack(desk_evidence([record()], {"headline_ids": ["cpi"]})["evidence_documents"])


def test_real_desk_consumer_keeps_unicode_and_tail_beyond_ordinary_limit():
    source = pack()
    assert len(source) == 1
    assert len(source[0]["canonical_content_text"]) > newsroom.MAX_SOURCE_TEXT_CHARS
    assert source[0]["canonical_content_text"] == record()["text"]
    assert len(source[0]["cpi_reaction_page"]["tables"]) == 2
    assert "[[CPI_REACTION_TABLES]]" in newsroom._worker_prompt({"source_pack": source})
    assert "CC425_CPI_REACTION_PAGE_V1" in newsroom._revision_prompt({"source_pack": source}, {}, [])


def test_unicode_hash_does_not_accept_a_different_binding():
    doc = desk_evidence([record()], {"headline_ids": ["cpi"]})["evidence_documents"][0]
    doc["desk_record_binding"]["fields"][0]["value"] += " altered"
    assert newsroom._source_pack([doc]) == []


def test_tables_are_structured_and_prose_is_the_writers():
    article = bind_tables({"title": "A writer's title", "substack_body_markdown":
                          "We think the sample needs context.\n\n" + TOKEN + "\n\nOur countercase."}, pack())
    body = article["substack_body_markdown"]
    assert body.startswith("We think") and body.endswith("Our countercase.")
    assert "Gold | HistData gold/USD | -0.2353% | +0.1000% | 0.0000% | —" in body
    assert "| S&P 500 | 2 | 33 |" in body
    assert "XAUUSD" not in body and "not yet due" not in body
    assert len(tables(body)) == 2
    assert body.count("[[SOURCE:SOURCE_1]]") == 2
    table_paragraphs = "\n\n".join(p for p in body.split("\n\n") if p.startswith("|"))
    assert newsroom._paragraph_marker_blockers(table_paragraphs, {"SOURCE_1"}) == []
    from live_contentops.capital_chronicle_desk_record_source_v1 import validate_article_citations
    validate_article_citations({**article, "substack_body_markdown": body +
        "\n\nCapital Chronicle offers analysis only, not financial advice or recommendations."}, [record()])
    assert article["cpi_reaction_page"]["export_bytes_sha256"] == "a" * 64
    validate_bound_tables(article)
    assert bind_tables(article, pack()) == article


@pytest.mark.parametrize("mutation", ["number", "missing", "duplicate", "zero_fill"])
def test_publication_refuses_changed_cells_or_lost_tables(mutation):
    article = bind_tables({"substack_body_markdown": TOKEN}, pack())
    body = article["substack_body_markdown"]
    if mutation == "number":
        body = body.replace("-0.2353%", "+0.2353%", 1)
    elif mutation == "missing":
        body = body.replace(tables(body)[-1], "")
    elif mutation == "duplicate":
        body += "\n\n" + tables(body)[0]
    else:
        body = body.replace("| — |", "| 0.0000% |", 1)
    with pytest.raises(ValueError, match="CPI_REACTION_TABLE_CHANGED_OR_MISSING"):
        validate_bound_tables({**article, "substack_body_markdown": body})


def test_doubled_placeholder_and_two_sources_fail_before_assembly():
    with pytest.raises(ValueError, match="DUPLICATED"):
        bind_tables({"substack_body_markdown": TOKEN + TOKEN}, pack())
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        bind_tables({"substack_body_markdown": TOKEN}, pack() * 2)


def test_source_validation_receives_expanded_bound_article(monkeypatch):
    from live_contentops import reader_article_contract_v1 as reader
    seen = []

    def inspect(article, documents):
        seen.append(article)
        assert TOKEN not in article["substack_body_markdown"]
        validate_bound_tables(article)
        raise ValueError("SOURCE_VALIDATOR_REACHED")

    monkeypatch.setattr(reader, "validate_article", inspect)
    with pytest.raises(newsroom.SimpleGeminiNewsroomError, match="deterministic_article_validation_failed"):
        newsroom._validate_article_against_source_pack({"article": {
            "substack_body_markdown": TOKEN, "cpi_reaction_page": {"writer_cannot_self_certify": True}}}, pack())
    assert seen[0]["cpi_reaction_page"]["policy"] == "CC425_CPI_REACTION_PAGE_V1"


def test_other_sources_and_old_articles_keep_their_contract():
    value = record()
    value["binding"]["record_id"] = "report:something-else"
    assert record_projection(value) is None
    article = {"substack_body_markdown": "An unchanged historical article."}
    assert bind_tables(article, []) == article
    validate_bound_tables(article)


def test_coordinator_boundary_checks_the_actual_article_tables(monkeypatch):
    from live_contentops import article_publication_quality_v1 as quality
    article = bind_tables({"substack_body_markdown": TOKEN}, pack())
    article["substack_body_markdown"] = article["substack_body_markdown"].replace("-0.2353%", "+0.2353%", 1)
    monkeypatch.setattr(quality, "applies", lambda *a: True)
    monkeypatch.setattr(quality, "article_inputs", lambda *a: (article, [], pack()))
    with pytest.raises(ValueError, match="CPI_REACTION_TABLE_CHANGED_OR_MISSING"):
        quality.before_article_write(None, {}, "substack")


def test_native_compiler_retains_table_binding_and_removes_source_markers():
    article = bind_tables({"title": "The CPI comparison", "reader_first_version": "DATA_JOURNALISM_V1",
                          "substack_body_markdown": "We think the comparison needs context.\n\n" + TOKEN}, pack())
    compiled = newsroom._reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS")
    assert "[[SOURCE:" not in compiled["substack_body_markdown"]
    assert compiled["cpi_reaction_page"] == article["cpi_reaction_page"]
    assert "RETAINED_LATER_OBSERVATION" not in compiled["substack_body_markdown"]
    assert "forecast retrieved later" in compiled["substack_body_markdown"]
    validate_bound_tables(compiled)


def test_reader_wording_update_resumes_the_unchanged_evidence_file(tmp_path, monkeypatch):
    from live_contentops.cpi_reaction_page_v1 import PUBLIC_LABELS
    original = pack()
    path = tmp_path / "simple_gemini_evidence_v1.json"
    newsroom._write_json(path, {"source_pack": original})
    frozen_bytes = path.read_bytes()
    monkeypatch.setitem(PUBLIC_LABELS, "RETAINED_LATER_OBSERVATION", "forecast observed later")
    resumed = pack()
    assert resumed == original
    newsroom._write_json(path, {"source_pack": resumed})
    assert path.read_bytes() == frozen_bytes
    article = bind_tables({"substack_body_markdown": TOKEN}, resumed)
    assert "forecast observed later" in article["substack_body_markdown"]
    validate_bound_tables(article)


def test_validated_revision_replaces_failed_receipt_and_retains_its_history(tmp_path):
    from types import SimpleNamespace
    original = {"run_id": "cpi", "cutoff_utc": "2026-11-11T07:03:57Z",
                "qualified_article_count": 0, "public_write_performed": False}
    current = {**original, "qualified_article_count": 1}
    path = tmp_path / "simple_gemini_newsroom_receipt_v1.json"
    newsroom._write_json(path, original)
    old_bytes = path.read_bytes()
    # Qualification is persisted before the final receipt in the real owner.
    (tmp_path / "qualified_article_record_v1.json").write_text("{}")
    request = {"request_sha256": "a" * 64}
    response = {**request, "invocation_observation": {"invocation_id": "same-writer"}}
    turn = SimpleNamespace(frozen_request=lambda _: request, native_response=lambda _: response)
    newsroom._preserve_unqualified_revision_artifact(path, current, turn)
    newsroom._write_json(path, current)
    assert (tmp_path / "editorial-revision-history" / ("a" * 64) / path.name).read_bytes() == old_bytes
    assert newsroom._write_json(path, current) is None
    with pytest.raises(newsroom.SimpleGeminiNewsroomError):
        changed = {**current, "cutoff_utc": "2026-11-11T08:00:00Z"}
        newsroom._preserve_unqualified_revision_artifact(path, changed, turn)
        newsroom._write_json(path, changed)


def test_cpi_tables_reach_canonical_html_with_every_cell_and_gap():
    from html import unescape
    from html.parser import HTMLParser
    from live_contentops.article_rich_text_v1 import markdown_to_rich_text, rich_text_to_html, rich_text_to_plain_text
    article = bind_tables({"title": "CPI history", "reader_first_version": "DATA_JOURNALISM_V1",
        "substack_body_markdown": "We think each horizon needs its own sample.\n\n" + TOKEN}, pack())
    reader = newsroom._reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS")
    semantic = markdown_to_rich_text(reader["substack_body_markdown"])
    rendered = rich_text_to_html(semantic)
    expected = [[cell.strip() for cell in row.strip('|').split('|')]
        for table in tables(reader["substack_body_markdown"]) for row in table.splitlines()[2:]]
    class Cells(HTMLParser):
        def __init__(self):
            super().__init__(); self.rows=[]; self.row=None; self.cell=None
        def handle_starttag(self, tag, attrs):
            if tag=='tr': self.row=[]
            if tag=='td': self.cell=''
        def handle_data(self, data):
            if self.cell is not None:self.cell+=data
        def handle_endtag(self, tag):
            if tag=='td':self.row.append(self.cell);self.cell=None
            if tag=='tr' and self.row:self.rows.append(self.row)
    parsed=Cells();parsed.feed(rendered)
    assert rendered.count('<table>') == 2
    assert parsed.rows == expected
    assert "—" in rich_text_to_plain_text(semantic)
    assert '[[SOURCE:' not in rendered and '|---' not in rendered


def test_refresh_consumes_new_producer_cells_without_a_second_publisher():
    first = pack()
    value = record()
    value["binding"]["fields"][0]["value"] = value["binding"]["fields"][0]["value"].replace("-0.2353%", "-0.2453%")
    value["binding"]["fields"][0]["display"] = value["binding"]["fields"][0]["value"]
    value["text"] = value["binding"]["fields"][0]["value"]
    value["binding"]["export_bytes_sha256"] = "b" * 64
    value["headline"]["source_url"] = "urn:cc-public-report:desk:" + sha256_of(value["binding"])
    refreshed = newsroom._source_pack(desk_evidence([value], {"headline_ids": ["cpi"]})["evidence_documents"])
    before = bind_tables({"substack_body_markdown": TOKEN}, first)
    after = bind_tables({"substack_body_markdown": TOKEN}, refreshed)
    assert after["cpi_reaction_page"]["export_bytes_sha256"] == "b" * 64
    assert "-0.2453%" in after["substack_body_markdown"]
    assert before["cpi_reaction_page"]["table_sha256"] != after["cpi_reaction_page"]["table_sha256"]
    with pytest.raises(ValueError, match="CHANGED_OR_MISSING"):
        bind_tables(before, refreshed)


def chart_packet():
    source = pack()[0]
    projection = source["cpi_reaction_page"]
    line = tables(source["canonical_content_text"])[0].splitlines()[2]
    operand = {"document_id": source["document_id"], "support_excerpt": line,
        "value_text": "-0.2353%", "metric": "+5m", "unit": "percent",
        "source_period_text": "2024-01-01", "prepared_period": "5 minutes",
        "source_content_sha256": source["canonical_content_sha256"],
        "period_basis": {"basis": "CC425_EXACT_TABLE_CELL", "row_index": 0,
            "column_index": 3, "source_table_sha256": projection["tables"][0]["source_table_sha256"]}}
    return {"asset_id": "cpi-reaction-test", "title": "The exact observed change",
        "question": "What did gold do?", "chart_type": "grouped_bar", "unit": "percent",
        "source_caption": "Capital Chronicle calculations; HistData gold/USD, 1 January 2024.",
        "cpi_reaction_source": {k: projection[k] for k in ("record_id", "export_bytes_sha256", "source_body_sha256")},
        "series": [{"name": "Gold", "points": [{"period": "5 minutes", "value": -0.2353,
            "observation_kind": "REPORTED_ACTUAL", "transform": "IDENTITY", "inputs": [operand]}]}]}


def test_held_report_cell_reaches_existing_chart_renderer(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        build_editorial_data_chart, validate_source_value_chart,
    )
    chart = build_editorial_data_chart(chart_packet(), pack(), output_dir=tmp_path)
    assert chart["computed_values"] == [[-0.2353]]
    assert chart["modality"] == "source_backed_chart"
    validate_source_value_chart(chart, pack())


@pytest.mark.parametrize("mutation", ["value", "row", "column", "export", "gap", "scale"])
def test_chart_report_cell_cannot_drift_or_fill_a_gap(mutation):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values
    packet = chart_packet()
    point = packet["series"][0]["points"][0]
    operand = point["inputs"][0]
    if mutation == "value":
        point["value"] *= -1
    elif mutation == "row":
        operand["period_basis"]["row_index"] = 1
    elif mutation == "column":
        operand["period_basis"]["column_index"] = 4
    elif mutation == "export":
        packet["cpi_reaction_source"]["export_bytes_sha256"] = "b" * 64
    elif mutation == "gap":
        operand["period_basis"]["column_index"] = 6
        operand["value_text"] = "0.0000%"
        point["value"] = 0
    else:
        point["scale"] = 100
    with pytest.raises(ValueError, match="CPI_REACTION_CHART"):
        _editorial_data_values(packet, pack())
