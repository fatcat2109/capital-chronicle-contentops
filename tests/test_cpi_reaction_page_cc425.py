import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import desk_evidence
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.cpi_reaction_page_v1 import (
    RECORD_ID, TOKEN, bind_tables, record_projection, tables, validate_bound_tables,
)
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom


def record():
    # Exceeds the ordinary source limit and includes Unicode missing cells.
    first = "| Release | Market | Series | +5m | +30m | Close | Next close |\n|---|---|---|---:|---:|---:|---:|\n"
    first += "\n".join(f"| 2024-01-{i:02d} | XAUUSD | HISTDATA:XAUUSD | -0.2353% | +0.1000% | 0.0000% | — |"
                       for i in range(1, 29))
    body = ("Computed changes, not isolated CPI effects.\n\n" + first + "\n\n"
            + "Source context. " * 2500
            + "\n\n## Coverage\n\n| Market | observed | eligible |\n|---|---:|---:|\n| US500 | 2 | 33 |"
            + "\n\n## The desk's map\n\nIts result is not yet due at the original source clock.")
    binding = {"record_id": RECORD_ID, "record_type": "published_report", "fixture": False,
        "export_id": "test-cpi", "export_bytes_sha256": "a" * 64,
        "asset_ids": [], "event_ids": [], "sources": [],
        "fields": [{"field_path": "/sections/reaction-tables/body_markdown",
                    "citation": "test-cpi#" + RECORD_ID + "/sections/reaction-tables/body_markdown",
                    "value": body, "display": body}]}
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
    validate_bound_tables(compiled)


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
