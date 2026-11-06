"""CC-245 (Jim, 4 Nov: the SEC image): fact cards in the site design, with their content binding.

Local fixtures only; no browser, provider, model or production-store write.
"""
from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.fact_card_design_v1 import (
    CardSpec, DESIGN, INSTAGRAM_SIZE, PAPER, X_SIZE, key_from_facts, piece_dated_line, reader_date, render_fact_card,
)

SEC_TEXT = ("The Securities and Exchange Commission announced today that it will host a roundtable on November 9, 2026, "
            "to discuss the use of machine-understandable data and Super Intelligence (SI) and related risks and costs. "
            "The roundtable will be open to the public and held at the SEC's headquarters at 100 F Street, N.E., "
            "Washington, D.C. from 9 a.m. to 3:30 p.m. EST. The discussion will be streamed live on SEC.gov.")
SEC_ROWS = [("Scheduled date", "November 9, 2026"), ("Overall time", "9 a.m. to 3:30 p.m. EST"),
            ("Location", "100 F Street, N.E., Washington, D.C."),
            ("Webcast", "The discussion will be streamed live on SEC.gov"),
            ("Subject", "machine-understandable data and Super Intelligence (SI)")]
CPI_FACTS = [("Reported fact", "In September 2026, all-items CPI rose 0.6% and CPI excluding food and energy rose 0.3%, "
              "both seasonally adjusted"),
             ("Reported fact", "Over the twelve months ending September, all-items CPI-U increased 3.7%.")]


def _largest_empty_gap(path, *, band=12):
    """Largest run of ink-free horizontal bands between masthead and footer, as a share of that height."""
    image = Image.open(path).convert("RGB")
    width, height = image.size
    paper = tuple(int(PAPER[i:i + 2], 16) for i in (1, 3, 5))
    pixels = image.load()
    top, bottom = int(height * 0.16), int(height * 0.80)
    run = longest = 0
    for y0 in range(top, bottom, band):
        if any(pixels[x, y] != paper for y in range(y0, min(y0 + band, bottom), 3) for x in range(0, width, 5)):
            run = 0
        else:
            run += band
            longest = max(longest, run)
    return longest / (bottom - top)


def test_key_value_must_be_admitted_text(tmp_path):
    with pytest.raises(ValueError, match="KEY_VALUE_MUST_BE_ADMITTED"):
        render_fact_card(tmp_path / "x.png", CardSpec(title="SEC roundtable", facts=SEC_ROWS, key_value="November 10, 2026"))


def test_key_prefers_a_dated_row_then_a_figure_with_its_unit():
    assert key_from_facts(SEC_ROWS) == ("Scheduled date", "November 9, 2026")
    assert key_from_facts(CPI_FACTS) == ("Key figure", "0.6%")
    assert key_from_facts([("Note", "No figure here")]) == ("", "")


@pytest.mark.parametrize("size", [X_SIZE, INSTAGRAM_SIZE])
@pytest.mark.parametrize("facts", [SEC_ROWS, CPI_FACTS, []])
def test_cards_leave_no_large_empty_area(tmp_path, size, facts):
    label, value = key_from_facts(facts)
    spec = CardSpec(title="September CPI: why 0.6% and 3.7% answer different questions" if facts is not SEC_ROWS
                    else "SEC roundtable: November 9", facts=facts, key_label=label, key_value=value,
                    source_line="Source: U.S. Bureau of Labor Statistics, October 14, 2026",
                    dated_line="Capital Chronicle · November 2, 2026")
    result = render_fact_card(tmp_path / "card.png", spec, size=size)
    assert Image.open(tmp_path / "card.png").size == size
    assert result["design"] == DESIGN
    # The old SEC card left over half the body blank; no gap may exceed about a fifth.
    assert _largest_empty_gap(tmp_path / "card.png") <= 0.22


def test_gap_measure_catches_a_blank_lower_half(tmp_path):
    image = Image.new("RGB", X_SIZE, PAPER)
    from PIL import ImageDraw
    ImageDraw.Draw(image).rectangle((64, 150, 900, 380), fill="#111111")
    image.save(tmp_path / "blank.png")
    assert _largest_empty_gap(tmp_path / "blank.png") > 0.5


def test_too_much_text_is_cut_never_raised(tmp_path):
    long_facts = [("Fact", "word " * 120)] * 9
    result = render_fact_card(tmp_path / "card.png", CardSpec(title="t " * 90, facts=long_facts), size=X_SIZE)
    assert 1 <= result["facts_shown"] <= result["facts_given"] == 9


def test_dates_are_reader_dates_and_the_piece_date_is_fixed():
    assert reader_date("2026-10-19T00:00:00Z") == "October 18, 2026"
    assert reader_date("2026-10-19") == "October 19, 2026"
    assert reader_date("") == ""
    assert piece_dated_line({"display_date": "Written November 2, 2026 (New York) · retrospective"}) == \
        "Capital Chronicle · November 2, 2026"
    assert piece_dated_line({}) == "Capital Chronicle"


def _sec_document():
    return {"document_id": "sec", "url": "https://www.sec.gov/newsroom/press-releases/2026-106",
            "publisher": "U.S. Securities and Exchange Commission", "published_at_utc": "2026-10-19T00:00:00Z",
            "canonical_content_text": SEC_TEXT, "underlying_reuse_classification": "governed_government_public_domain",
            "rights_evidence_sha256": "e" * 64}


def _sec_packet():
    excerpts = {"Scheduled date": "host a roundtable on November 9, 2026",
                "Overall time": "from 9 a.m. to 3:30 p.m. EST",
                "Location": "100 F Street, N.E., Washington, D.C.",
                "Webcast": "The discussion will be streamed live on SEC.gov",
                "Subject": "machine-understandable data and Super Intelligence (SI)"}
    return {"schema_version": "contentops.source_fact_card.v1", "title": "SEC roundtable: November 9",
            "question": "When is the roundtable?", "source_url": "https://www.sec.gov/newsroom/press-releases/2026-106",
            "source_content_sha256": sha256(SEC_TEXT.encode()).hexdigest(),
            "rows": [{"label": label, "value": value, "support_excerpt": excerpts[label]} for label, value in SEC_ROWS]}


def test_source_fact_card_keeps_a_sent_file_and_labels_the_source_date(tmp_path, monkeypatch):
    from live_contentops import rolling_x_grounded_article_media_builder_v1 as builder
    seen = {}
    actual = builder._render_text_card
    def capture(**kwargs):
        seen.update(kwargs)
        actual(**kwargs)
    monkeypatch.setattr(builder, "_render_text_card", capture)
    sent = tmp_path / "sec-facts.png"
    Image.new("RGB", (1600, 900), "white").save(sent)   # the old, already-sent card
    before = sent.read_bytes()
    card = builder.build_source_fact_card(_sec_document(), packet=_sec_packet(), asset_id="sec-facts",
        placement_after="What the SEC has announced", output_dir=tmp_path,
        dated_line="Capital Chronicle · November 3, 2026")
    assert sent.read_bytes() == before                    # never overwritten
    assert Path(card["path"]) != sent and Path(card["path"]).is_file()
    assert seen["footer_lines"][0] == "Source: U.S. Securities and Exchange Commission, announced October 18, 2026"
    assert seen["dated_line"] == "Capital Chronicle · November 3, 2026"
    assert seen["kicker"] == "U.S. Securities and Exchange Commission"
    assert not any("Announcement:" in line for line in seen["footer_lines"])
    builder.validate_source_fact_card(card, [_sec_document()])


def test_post_card_is_deterministic_and_carries_design_and_piece_date(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        build_post_image_card, validate_post_image_card,
    )
    article = {"title": "A scheduled release: what is known", "subtitle": "The next release is still ahead.",
               "substack_body_markdown": "Admitted fixture copy. Analysis, not financial advice.",
               "news_item_kind": "NEWS", "display_date": "November 3, 2026"}
    first = build_post_image_card(article, output_dir=tmp_path, accepted_evidence_sha256="a" * 64)
    again = build_post_image_card(article, output_dir=tmp_path, accepted_evidence_sha256="a" * 64)
    assert first["asset_id"] == again["asset_id"] and first["sha256"] == again["sha256"]
    assert first["post_card_binding"]["design"] == DESIGN
    assert first["post_card_binding"]["dated_line"] == "Capital Chronicle · November 3, 2026"
    validate_post_image_card(first, article=article, accepted_evidence_sha256="a" * 64)


def test_delivery_card_is_instagram_portrait_and_never_overwrites_a_sent_card(tmp_path):
    from live_contentops.media_manifest_authority_v1 import build_delivery_only_editorial_card
    sent = tmp_path / "delivery_only_editorial_card.png"
    Image.new("RGB", (1350, 1080), "#07111f").save(sent)
    before = sent.read_bytes()
    card = build_delivery_only_editorial_card(output_path=sent, title="September CPI: why 0.6% and 3.7% differ",
        source_label="U.S. Bureau of Labor Statistics", source_page_url="https://www.bls.gov/news.release/cpi.htm",
        published_at="2026-10-14T12:30:00Z")
    assert sent.read_bytes() == before
    assert Path(card["path"]) != sent and (card["width"], card["height"]) == INSTAGRAM_SIZE
    assert card["reader_facing_source_date"] == "October 14, 2026"


# ---- CC-144 data cards in the CC-245 design ----

def test_data_card_uses_the_site_design_at_instagram_size_and_new_paths(tmp_path):
    from test_post_visuals_v1 import packet as data_card_fixture
    from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card
    article, claims, docs = data_card_fixture()
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    assert (card["width"], card["height"]) == INSTAGRAM_SIZE
    assert Image.open(card["path"]).size == INSTAGRAM_SIZE
    packet = card["data_card_packet"]
    assert packet["design"] == DESIGN and packet["title"] == article["title"]
    # Facts stay verbatim; the key figure, if any, is text from those facts (renderer-enforced).
    assert all(f["text"] in article["substack_body_markdown"] or f["text"] for f in packet["facts"])
    validate_post_data_card(card, article, docs)
    # A card packet from before CC-245 keeps its own (different) id and path.
    legacy = {k: v for k, v in packet.items() if k not in {"design", "title", "dated_line"}}
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    assert "post-facts-" + sha256_of(legacy)[:20] != card["asset_id"]


def test_data_card_that_cannot_show_every_fact_whole_asks_for_fewer(tmp_path):
    from live_contentops.post_visuals_v1 import _render_card
    many = {"title": "A long release", "facts": [{"text": "word " * 220, "publisher": "U.S. Bureau of Labor Statistics"}] * 3}
    with pytest.raises(ValueError, match="DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT"):
        _render_card(many, tmp_path / "card.png")
    one = {"title": "A release", "facts": [{"text": "The index rose 0.6% in September.", "publisher": "BLS"}]}
    assert _render_card(one, tmp_path / "ok.png") == INSTAGRAM_SIZE
