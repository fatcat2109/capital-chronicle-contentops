"""CC-290 (Jim, 5 Nov, on the Southwest card: the black block draws too much attention and
the edges do not line up): one grid, a hero in ink on paper, and a figure that beats a
past date. The content binding is CC-245's and is unchanged.

Local fixtures only; no browser, provider, model or production-store write.
"""
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.fact_card_design_v1 import (
    CardSpec, DESIGN, INSTAGRAM_SIZE, MARGIN, PAPER, X_SIZE, hero_for, key_from_facts, render_fact_card,
)

# The 5 Nov Southwest post card's admitted facts and editorial labels, verbatim.
SOUTHWEST = [
    ("Closure cash", "In Q2 2025, Southwest received approximately $40 million from closing its remaining fuel hedges."),
    ("Quarter's premium expense", "Southwest recorded approximately $36 million of fuel-hedging premium expense in "
                                  "Q2 2025, including terminated positions."),
    ("Expense still deferred", "At June 30, 2025, approximately $209 million remained in AOCI, excluding tax and net "
                               "of termination proceeds, for reclassification to fuel expense through end-2027 as the "
                               "originally forecast transactions occur."),
]
CPI = [("Reported fact", "In September 2026, all-items CPI rose 0.6% and CPI excluding food and energy rose 0.3%, "
                         "both seasonally adjusted"),
       ("Reported fact", "Over the twelve months ending September, all-items CPI-U increased 3.7%; CPI-U excluding "
                         "food and energy increased 2.6%. Those annual figures are not seasonally adjusted.")]
SEC = [("Scheduled date", "November 9, 2026"), ("Overall time", "9 a.m. to 3:30 p.m. EST"),
       ("Location", "100 F Street, N.E., Washington, D.C."), ("Webcast", "The discussion will be streamed live on SEC.gov"),
       ("Subject", "machine-understandable data and Super Intelligence (SI)")]


def southwest(**changes):
    spec = CardSpec(title="Southwest's 2025 hedge exit", facts=SOUTHWEST, kicker="Q2 2025 filing explained",
                    key_label="Historical balance date", key_value="June 30, 2025",
                    source_line="Source: Southwest Airlines Co.", dated_line="Capital Chronicle · November 5, 2026")
    return replace(spec, **changes)


def cards():
    label, value = key_from_facts(CPI)
    return {
        "southwest": southwest(),
        "cpi": CardSpec(title="September CPI: why 0.6% and 3.7% answer different questions", facts=CPI,
                        kicker="U.S. Bureau of Labor Statistics", key_label=label, key_value=value,
                        source_line="Source: U.S. Bureau of Labor Statistics, October 14, 2026",
                        dated_line="Capital Chronicle · November 2, 2026"),
        "sec": CardSpec(title="SEC roundtable: November 9", facts=SEC, key_label="Scheduled date",
                        key_value="November 9, 2026", kicker="U.S. Securities and Exchange Commission",
                        source_line="Source: U.S. Securities and Exchange Commission, announced October 19, 2026",
                        dated_line="Capital Chronicle · November 3, 2026"),
        "digest": CardSpec(title="Capital Chronicle daily digest", kicker="Daily digest", key_label="Edition",
                           key_value="November 4, 2026", source_line="Capital Chronicle's own articles",
                           dated_line="Capital Chronicle · November 4, 2026",
                           facts=[("Edition", "November 4, 2026"),
                                  ("", "US midterms: Capital Chronicle on the result that could surprise markets"),
                                  ("", "September CPI: why 0.6% and 3.7% answer different questions")]),
        "title_only": CardSpec(title="ISM services index rises as prices paid climb",
                               dated_line="Capital Chronicle · November 5, 2026"),
        # Rows that open on a descender's hook ('j', 'y') still start on the edge, by their stems.
        "hooks": CardSpec(title="Jobless claims and yields", dated_line="Capital Chronicle · November 5, 2026",
                          facts=[("Reported fact", "jobless claims rose 12,000 in the week."),
                                 ("Reported fact", "yields climbed 12 basis points after the release.")]),
    }


def _ink(pixel):
    return any(abs(a - b) > 6 for a, b in zip(pixel, (int(PAPER[i:i + 2], 16) for i in (1, 3, 5))))


def _leftmost_ink(image, box, bottom=None):
    """The first inked column of a block, between its cap top and ``bottom`` (its first
    baseline for type, so a descender's hook is not mistaken for the edge)."""
    pixels = image.load()
    x0, y0, x1, y1 = box
    bottom = y1 if bottom is None else bottom
    for x in range(max(0, x0 - 16), min(image.width, x1 + 1)):
        if any(_ink(pixels[x, y]) for y in range(max(0, y0 - 1), min(image.height, bottom))):
            return x
    return None


# ---- hero choice --------------------------------------------------------------------

def test_a_figure_beats_a_past_date_and_is_quoted_from_its_fact(tmp_path):
    assert hero_for(southwest()) == ("Closure cash", "$40 million")
    result = render_fact_card(tmp_path / "southwest.png", southwest(), size=INSTAGRAM_SIZE)
    assert result["hero"] == ["Closure cash", "$40 million"]
    assert result["hero"][1] in SOUTHWEST[0][1]
    # Every admitted fact is still on the card, the hero's own sentence included.
    assert result["facts_shown"] == result["facts_given"] == 3
    # A quarter or a year names a period just as a date does.
    assert hero_for(southwest(key_label="Quarter", key_value="Q2 2025")) == ("Closure cash", "$40 million")
    # A generic label reads as the key figure.
    assert hero_for(CardSpec(title="CPI", facts=CPI, key_label="Reported fact", key_value="September 2026",
                             dated_line="Capital Chronicle · November 2, 2026")) == ("Key figure", "0.6%")


def test_a_date_still_ahead_keeps_the_hero_and_a_passed_one_gives_way():
    sec = cards()["sec"]
    assert hero_for(sec) == ("Scheduled date", "November 9, 2026")
    assert hero_for(replace(sec, dated_line="Capital Chronicle")) == ("Scheduled date", "November 9, 2026")
    preview = CardSpec(title="PPI preview", key_label="Release date", key_value="November 13, 2026",
                       facts=[("Release date", "The next report is due on November 13, 2026."),
                              ("Last reading", "Producer prices rose 1.3% in September.")],
                       dated_line="Capital Chronicle · November 5, 2026")
    assert hero_for(preview) == ("Release date", "November 13, 2026")       # after the piece's own date
    assert hero_for(replace(preview, dated_line="Capital Chronicle · November 20, 2026")) == ("Last reading", "1.3%")


def test_titles_in_a_digest_never_supply_the_hero_and_a_figure_key_stays():
    assert hero_for(cards()["digest"]) == ("Edition", "November 4, 2026")
    assert hero_for(cards()["cpi"]) == ("Key figure", "0.6%")
    assert hero_for(southwest(key_label="Expense still deferred", key_value="$209 million")) == \
        ("Expense still deferred", "$209 million")


# ---- one grid -----------------------------------------------------------------------

@pytest.mark.parametrize("size", [INSTAGRAM_SIZE, X_SIZE])
@pytest.mark.parametrize("name", ["southwest", "cpi", "sec", "digest", "title_only", "hooks"])
def test_every_block_starts_on_one_left_edge_and_ends_inside_the_right_edge(tmp_path, name, size):
    path = tmp_path / f"{name}.png"
    result = render_fact_card(path, cards()[name], size=size)
    image = Image.open(path).convert("RGB")
    width, height = size
    columns = result["columns"]
    assert columns[0] == MARGIN and (len(columns) == 1 or height < width)   # portrait is one column
    for block in result["blocks"]:
        if block["name"].startswith("chart"):
            continue                       # a chart's own labels sit over its marks
        assert block["box"][0] in columns, block
        # The ink, not the pen position, sits on the edge: large type is set by its glyphs.
        bottom = block.get("baseline", block["box"][3] + 1)
        assert abs(_leftmost_ink(image, block["box"], bottom) - block["box"][0]) <= 1, block
    # Nothing crosses the right margin; the masthead and footer rules end exactly on it.
    pixels = image.load()
    right = width - MARGIN
    assert not any(_ink(pixels[x, y]) for x in range(right, width) for y in range(0, height, 3))
    for name_ in ("masthead", "footer"):
        box = next(b["box"] for b in result["blocks"] if b["name"] == name_)
        assert box[0] == MARGIN and box[2] == right


@pytest.mark.parametrize("size", [INSTAGRAM_SIZE, X_SIZE])
def test_rows_share_one_spacing_scale(tmp_path, size):
    result = render_fact_card(tmp_path / "card.png", cards()["sec"], size=size)
    blocks = result["blocks"]
    above, below = [], []
    for index, block in enumerate(blocks):
        if block["name"] == "rule":
            above.append(block["box"][1] - blocks[index - 1]["box"][3])
            below.append(blocks[index + 1]["box"][1] - block["box"][3])
    assert len(above) >= 2
    assert max(above) - min(above) <= 1 and max(below) - min(below) <= 1 and abs(above[0] - below[0]) <= 1
    labels = [(blocks[i + 1]["box"][1] - b["box"][3]) for i, b in enumerate(blocks[:-1]) if b["name"] == "fact_label"]
    assert max(labels) - min(labels) <= 1


# ---- hierarchy and the hero's weight -------------------------------------------------

@pytest.mark.parametrize("size", [INSTAGRAM_SIZE, X_SIZE])
def test_title_then_figure_then_facts_then_footer_and_no_dark_slab(tmp_path, size):
    path = tmp_path / "southwest.png"
    result = render_fact_card(path, southwest(), size=size)
    top = {}
    for block in result["blocks"]:
        top.setdefault(block["name"], block["box"][1])
    assert top["masthead"] < top["title"] < top["accent"] < top["hero_label"] < top["hero_value"] < top["footer"]
    # The facts come after the accent (beside the hero on the X card) and end above the footer.
    for block in result["blocks"]:
        if block["name"] in {"fact", "fact_label", "hero_fact"}:
            assert top["accent"] < block["box"][1] and block["box"][3] < top["footer"]
    assert result["title_size"] > result["facts_size"]
    assert result["figure_size"] <= 1.3 * result["title_size"]
    # The old card's black slab made a fifth of the card dark; ink on paper is type only.
    grey = Image.open(path).convert("L")
    assert sum(grey.histogram()[:60]) / (size[0] * size[1]) < 0.12
    assert result["design"] == DESIGN == "CC290_SITE_FACT_CARD_V2"


# ---- every shape of card holds --------------------------------------------------------

LONG_TITLE = ("Southwest's 2025 hedge exit: closure cash now, deferred premium expense still to come through 2027 "
              "as the forecast fuel purchases occur")


@pytest.mark.parametrize("size", [INSTAGRAM_SIZE, X_SIZE])
@pytest.mark.parametrize("count", [1, 2, 3, 4])
@pytest.mark.parametrize("title", ["Southwest", LONG_TITLE])
def test_short_and_long_titles_with_one_to_four_facts(tmp_path, size, count, title):
    facts = (SOUTHWEST + [("Reported fact", CPI[0][1])])[:count]
    label, value = key_from_facts(facts)
    spec = southwest(title=title, facts=facts, key_label=label, key_value=value)
    result = render_fact_card(tmp_path / "card.png", spec, size=size)
    assert result["facts_shown"] == result["facts_given"] == count
    assert result["facts_size"] >= (28 if size == INSTAGRAM_SIZE else 22)
    assert all(block["box"][2] <= size[0] - MARGIN for block in result["blocks"])


@pytest.mark.parametrize("size", [INSTAGRAM_SIZE, X_SIZE])
def test_title_card_and_figureless_card(tmp_path, size):
    title_only = render_fact_card(tmp_path / "title.png", cards()["title_only"], size=size)
    assert title_only["hero"] is None and title_only["facts_given"] == 0
    assert [b["name"] for b in title_only["blocks"]][-2:] == ["accent", "title"]
    plain = CardSpec(title="A scheduled release: what is known",
                     facts=[("What happened", "The next release is still ahead; the agency has not changed its "
                                              "timetable for the report.")],
                     source_line="Source: Federal agency, November 4, 2026",
                     dated_line="Capital Chronicle · November 5, 2026")
    result = render_fact_card(tmp_path / "plain.png", plain, size=size)
    assert result["hero"] is None and result["facts_shown"] == result["facts_given"] == 1


def test_edge_measure_catches_an_indented_block():
    from PIL import ImageDraw
    image = Image.new("RGB", INSTAGRAM_SIZE, PAPER)
    ImageDraw.Draw(image).rectangle((100, 300, 400, 340), fill="#111111")   # the old slab's inner text edge
    assert _leftmost_ink(image, [MARGIN, 300, 400, 340]) == 100


# ---- a chart that reaches a card is legible (CC-290, decision 74) ----------------------

def _ink_height_above_baseline(image, block):
    """Rows of ink in a label's box, from just above its cap line down to its baseline."""
    pixels = image.load()
    x0, top, x1, baseline = block["box"][0], block["box"][1], block["box"][2], block["baseline"]
    rows = [y for y in range(max(0, top - 8), baseline + 1)
            if any(_ink(pixels[x, y]) for x in range(max(0, x0), min(image.width, x1 + 1)))]
    return rows[-1] - rows[0] + 1 if rows else 0


def test_a_chart_on_a_card_is_drawn_for_its_slot_with_every_label_at_the_fact_floor(tmp_path, monkeypatch):
    """The real data-card path with the admitted test series: the card draws the bound chart
    (no shrunk 1440x1040 picture), and every number, unit, period and legend measures at
    least as tall on the card as the same words set at 28px, the fact-text floor."""
    from test_reader_first_data_journalism_v1 import chart_packet
    from live_contentops import fact_card_design_v1 as design
    from live_contentops.fact_card_design_v1 import _bbox
    from live_contentops.post_visuals_v1 import build_post_data_card
    series, docs = chart_packet()
    docs[0].update(source_id="SOURCE_1", underlying_reuse_classification="governed_government_public_domain",
                   rights_evidence_sha256="d" * 64)
    text = docs[0]["canonical_content_text"]
    claims = [{"claim_id": "revenue", "source_id": "SOURCE_1", "claim_text": text, "support_excerpt": text}]
    seen, real = [], design.render_fact_card

    def capture(path, spec, *, size=X_SIZE):
        seen.append((Path(path), spec, size))
        return real(path, spec, size=size)

    monkeypatch.setattr(design, "render_fact_card", capture)
    card = build_post_data_card({"substack_body_markdown": text}, claims, docs, output_dir=tmp_path,
                                series_packet=series)
    _, spec, size = seen[-1]
    chart = card["data_card_packet"]["series_asset"]
    assert size == INSTAGRAM_SIZE and spec.chart == chart
    for card_size in (INSTAGRAM_SIZE, X_SIZE):
        path = tmp_path / f"chart-{card_size[0]}x{card_size[1]}.png"
        result = real(path, spec, size=card_size)
        image = Image.open(path).convert("RGB")
        labels = [b for b in result["blocks"] if b["name"].startswith("chart_")]
        names = {b["name"] for b in labels}
        assert {"chart_title", "chart_legend", "chart_unit", "chart_value", "chart_period", "chart_axis",
                "chart_source"} <= names
        # The packet's words and the owner's values, exactly.
        packet = chart["editorial_data_packet"]
        shown = [b["text"] for b in labels]
        assert packet["title"] in shown and packet["unit"] in shown and packet["source_caption"] in shown
        assert {"2025", "2026", "100", "120", "Revenue"} <= set(shown)
        for block in labels:
            assert block["size"] >= 28, block
            floor = -_bbox(block["text"], block["weight"], 28)[1]       # the same words at 28px
            assert _ink_height_above_baseline(image, block) >= floor - 1, (block, floor)
        # Nothing of the chart leaves its column or crosses the footer.
        footer = next(b["box"] for b in result["blocks"] if b["name"] == "footer")
        frame = next(b["box"] for b in result["blocks"] if b["name"] == "chart")
        assert frame[0] == result["columns"][-1] and frame[2] <= card_size[0] - MARGIN and frame[3] < footer[1]


def test_a_chart_the_card_cannot_set_legibly_never_reaches_it():
    from test_reader_first_data_journalism_v1 import chart_packet
    series, _ = chart_packet()
    crowded = {"editorial_data_packet": {**series, "chart_type": "stacked_bar"}, "computed_values": [[100, 120]]}
    with pytest.raises(ValueError, match="DATA_CARD_CHART_NOT_CARD_LEGIBLE:TYPE"):
        render_fact_card("unused.png", CardSpec(title="Key facts", facts=[("Reported fact", "Revenue was 120.")],
                                                chart=crowded), size=INSTAGRAM_SIZE)
