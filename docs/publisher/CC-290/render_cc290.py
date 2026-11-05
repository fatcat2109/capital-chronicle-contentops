"""CC-290: before/after renders of the social fact card, side by side.

    python docs/publisher/CC-290/render_cc290.py <out_dir> [before_rev]

"Before" is fact_card_design_v1.py at ``before_rev`` (default f0bab3ff, the live CC-245
renderer), read from git; "after" is the working tree. Writes out_dir/before, out_dir/after,
out_dir/compare (before left, after right) and two overview sheets of every case.
The Southwest facts are the 5 Nov post's admitted text; the PPI facts are the 5 Nov PPI
preview's BLS sentences; "one-fact", "no-figure" and "long-title" are layout fixtures.
"data-card-chart-test-series" is a real card from the data-card path (build_post_data_card
with an admitted series and its chart owner), fed the repository's test series because no
admitted public-domain series in our run files has every value stated in its post.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]

SOUTHWEST = [
    ("Closure cash", "In Q2 2025, Southwest received approximately $40 million from closing its remaining fuel hedges."),
    ("Quarter's premium expense", "Southwest recorded approximately $36 million of fuel-hedging premium expense in "
                                  "Q2 2025, including terminated positions."),
    ("Expense still deferred", "At June 30, 2025, approximately $209 million remained in AOCI, excluding tax and net of "
                               "termination proceeds, for reclassification to fuel expense through end-2027 as the "
                               "originally forecast transactions occur."),
]
CPI = [("Reported fact", "In September 2026, all-items CPI rose 0.6% and CPI excluding food and energy rose 0.3%, "
                         "both seasonally adjusted"),
       ("Reported fact", "Over the twelve months ending September, all-items CPI-U increased 3.7%; CPI-U excluding "
                         "food and energy increased 2.6%. Those annual figures are not seasonally adjusted.")]
PPI = [("Reported fact", "U.S. final-demand producer prices rose 1.3% in September, according to the Bureau of Labor "
                         "Statistics."),
       ("Reported fact", "BLS reported that final-demand goods rose 2.6% in September and services rose 0.8%."),
       ("Reported fact", "The measure excluding foods, energy and trade services increased 0.5%."),
       ("Reported fact", "August's headline increase was initially reported at 0.4%; September's bulletin put it at "
                         "0.5%.")]
SEC = [("Scheduled date", "November 9, 2026"), ("Overall time", "9 a.m. to 3:30 p.m. EST"),
       ("Location", "100 F Street, N.E., Washington, D.C."), ("Webcast", "The discussion will be streamed live on SEC.gov"),
       ("Subject", "machine-understandable data and Super Intelligence (SI)")]
DIGEST_4_NOV = ["US midterms: Capital Chronicle on the result that could surprise markets",
                "U.S. Securities and Exchange Commission plans November 9 data roundtable",
                "September 2026 jobs: private gains beneath a weak headline"]
DIGEST_6 = ["Southwest's 2025 hedge exit", "October CPI preview: does inflation pressure reach beyond energy?",
            "October PPI preview: how broad is the pressure?",
            "US midterms: Capital Chronicle on the result that could surprise markets",
            "ISM services index rises as prices paid climb", "Challenger job cuts: October report"]


def digest(titles, label):
    facts = [("Edition", label), *(("", t) for t in titles[:5])]
    if len(titles) > 5:
        facts.append(("", f"and {len(titles) - 5} more"))
    return dict(title="Capital Chronicle daily digest", facts=facts, kicker="Daily digest", key_label="Edition",
                key_value=label, source_line="Capital Chronicle's own articles", dated_line="Capital Chronicle · " + label)


def cases(module):
    key = module.key_from_facts
    return {
        "southwest": dict(title="Southwest's 2025 hedge exit", facts=SOUTHWEST, kicker="Q2 2025 filing explained",
                          key_label="Historical balance date", key_value="June 30, 2025",
                          source_line="Source: Southwest Airlines Co.", dated_line="Capital Chronicle · November 5, 2026"),
        "cpi-release": dict(title="September CPI: why 0.6% and 3.7% answer different questions", facts=CPI,
                            kicker="U.S. Bureau of Labor Statistics", key_label=key(CPI)[0], key_value=key(CPI)[1],
                            source_line="Source: U.S. Bureau of Labor Statistics, October 14, 2026",
                            dated_line="Capital Chronicle · November 2, 2026"),
        "ppi-four-facts": dict(title="October PPI preview: how broad is the pressure?", facts=PPI, kicker="PPI preview",
                               key_label=key(PPI)[0], key_value=key(PPI)[1],
                               source_line="Source: U.S. Bureau of Labor Statistics, October 15, 2026",
                               dated_line="Capital Chronicle · November 5, 2026"),
        "sec-event": dict(title="SEC roundtable: November 9", facts=SEC, kicker="U.S. Securities and Exchange Commission",
                          key_label=key(SEC)[0], key_value=key(SEC)[1],
                          source_line="Source: U.S. Securities and Exchange Commission, announced October 19, 2026",
                          dated_line="Capital Chronicle · November 3, 2026"),
        "digest-4-nov": digest(DIGEST_4_NOV, "November 4, 2026"),
        "digest-6-items": digest(DIGEST_6, "November 5, 2026"),
        "title-card": dict(title="ISM services index rises as prices paid climb",
                           dated_line="Capital Chronicle · November 5, 2026"),
        "title-card-short": dict(title="Challenger job cuts: October report", dated_line="Capital Chronicle"),
        "one-fact": dict(title="A release", facts=[("Reported fact", "The index rose 0.6% in September.")],
                         key_label="Key figure", key_value="0.6%", source_line="Source: BLS",
                         dated_line="Capital Chronicle · November 5, 2026"),
        "no-figure": dict(title="A scheduled release: what is known",
                          facts=[("What happened", "The next release is still ahead; the agency has not changed its "
                                                   "timetable for the report.")],
                          source_line="Source: Federal agency, November 4, 2026",
                          dated_line="Capital Chronicle · November 5, 2026"),
        "long-title": dict(title="Southwest's 2025 hedge exit: closure cash now, deferred premium expense still to "
                                 "come through 2027 as the forecast fuel purchases occur",
                           facts=SOUTHWEST, kicker="Q2 2025 filing explained", key_label="Historical balance date",
                           key_value="June 30, 2025", source_line="Source: Southwest Airlines Co.",
                           dated_line="Capital Chronicle · November 5, 2026"),
    }


def real_chart_card(out: Path):
    """The live data-card path with the repository's admitted test series (CC-144 owner)."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_reader_first_data_journalism_v1 import chart_packet
    from live_contentops.post_visuals_v1 import build_post_data_card
    series, docs = chart_packet()
    docs[0].update(source_id="SOURCE_1", underlying_reuse_classification="governed_government_public_domain",
                   rights_evidence_sha256="d" * 64)
    text = docs[0]["canonical_content_text"]
    claims = [{"claim_id": "revenue", "source_id": "SOURCE_1", "claim_text": text, "support_excerpt": text}]
    card = build_post_data_card({"substack_body_markdown": text}, claims, docs, output_dir=out / "data-card-path",
                                series_packet=series)
    packet = card["data_card_packet"]
    publishers = list(dict.fromkeys(f["publisher"] for f in packet["facts"]))
    # The spec _render_card builds for this packet (no article title: "Key facts").
    spec = dict(title=packet.get("title") or "Key facts", facts=[("Reported fact", f["text"]) for f in packet["facts"]],
                kicker=" · ".join(publishers), source_line="Source: " + ", ".join(publishers),
                dated_line=packet.get("dated_line") or "Capital Chronicle")
    return Path(card["path"]), packet["series_asset"], spec


def load_before(rev: str, out: Path):
    source = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:live_contentops/fact_card_design_v1.py"],
                            check=True, capture_output=True).stdout
    path = out / f"fact_card_design_{rev}.py"
    path.write_bytes(source)
    spec = importlib.util.spec_from_file_location("fact_card_design_before", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fact_card_design_before"] = module
    spec.loader.exec_module(module)
    return module


def font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def compare(title, left: Path, right: Path, out: Path):
    a, b = Image.open(left).convert("RGB"), Image.open(right).convert("RGB")
    gap, head = 40, 70
    canvas = Image.new("RGB", (a.width + b.width + gap * 3, max(a.height, b.height) + head + gap), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    draw.text((gap, 18), title + " · before (live, CC-245)", font=font(34), fill="#55554F")
    draw.text((a.width + gap * 2, 18), "after (CC-290)", font=font(34), fill="#111111")
    canvas.paste(a, (gap, head))
    canvas.paste(b, (a.width + gap * 2, head))
    canvas.save(out, optimize=True)


def sheet(cells, out: Path, columns: int):
    """Every case at half size, each under its own caption."""
    images = [(caption, Image.open(p).convert("RGB")) for caption, p in cells]
    w, h = images[0][1].width // 2, images[0][1].height // 2
    head, rows = 44, (len(images) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * (w + 24) + 24, rows * (h + head + 24) + 24), "#8A8A84")
    draw = ImageDraw.Draw(canvas)
    for index, (caption, image) in enumerate(images):
        x, y = 24 + index % columns * (w + 24), 24 + index // columns * (h + head + 24)
        draw.text((x, y + 4), caption, font=font(26), fill="#FFFFFF")
        canvas.paste(image.resize((w, h), Image.Resampling.LANCZOS), (x, y + head))
    canvas.save(out, optimize=True)


def main():
    out = Path(sys.argv[1]).resolve()
    rev = sys.argv[2] if len(sys.argv) > 2 else "f0bab3ff"
    for folder in ("before", "after", "compare"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from live_contentops import fact_card_design_v1 as after
    before = load_before(rev, out)
    card_path, chart, chart_spec = real_chart_card(out)
    chart_case = "data-card-chart-test-series"
    for size_name, size in (("1080x1350", after.INSTAGRAM_SIZE), ("1600x900", after.X_SIZE)):
        cells = []
        for name, kwargs in cases(after).items():
            left, right = out / "before" / f"{name}-{size_name}.png", out / "after" / f"{name}-{size_name}.png"
            before.render_fact_card(left, before.CardSpec(**cases(before)[name]), size=size)
            result = after.render_fact_card(right, after.CardSpec(**kwargs), size=size)
            compare(f"{name} · {size_name}", left, right, out / "compare" / f"{name}-{size_name}.png")
            cells.append((name, right))
            print(name, size_name, "hero", result["hero"], "facts", result["facts_shown"], "/", result["facts_given"],
                  "at", result["facts_size"], "px")
        # The data card with its chart: "before" shrank the chart owner's 1440x1040 picture into
        # the slot; "after" draws the same bound chart for the slot. The 1080x1350 card is the
        # data-card path's own file; the X size is the same spec rendered at 1600x900.
        left, right = out / "before" / f"{chart_case}-{size_name}.png", out / "after" / f"{chart_case}-{size_name}.png"
        before.render_fact_card(left, before.CardSpec(**chart_spec, image_path=chart["path"]), size=size)
        if size == after.INSTAGRAM_SIZE:
            right.write_bytes(card_path.read_bytes())
        else:
            after.render_fact_card(right, after.CardSpec(**chart_spec, chart=chart), size=size)
        compare(f"{chart_case} · {size_name}", left, right, out / "compare" / f"{chart_case}-{size_name}.png")
        cells.append(("data card with chart · test series", right))
        print(chart_case, size_name, "chart", chart["editorial_data_packet"]["title"])
        sheet(cells, out / f"all-cases-after-{size_name}.png", 4 if size_name == "1080x1350" else 3)


if __name__ == "__main__":
    main()
