from __future__ import annotations

import html
import json
import re
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARTICLE = ROOT / "article.md"
OUTPUT = ROOT / "article.html"


def inline(value: str) -> str:
    value = html.escape(value, quote=False)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
    return value


def article_body(markdown: str) -> tuple[str, dict[str, str]]:
    lines = markdown.splitlines()
    metadata = {
        "title": lines[0].removeprefix("# ").strip(),
        "dek": lines[2].strip().strip("*"),
        "byline": lines[4].strip().replace("**", ""),
    }
    output: list[str] = []
    paragraph: list[str] = []
    list_mode: str | None = None
    quote: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_mode
        if list_mode:
            output.append(f"</{list_mode}>")
            list_mode = None

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            content = "<br>".join(inline(row.strip()) for row in quote)
            output.append(
                '<aside class="analysis-card">'
                '<img src="assets/kevin_warsh_official_federal_reserve.png" '
                'alt="Official portrait of Federal Reserve Chair Kevin Warsh">'
                f'<blockquote>{content}</blockquote>'
                '<span>Official portrait: Federal Reserve Board · Analysis is Capital Chronicle’s own</span>'
                '</aside>'
            )
            quote = []

    for raw in lines[6:]:
        line = raw.strip()
        if line.startswith(">"):
            flush_paragraph()
            close_list()
            quote.append(line.removeprefix(">").strip().rstrip("  "))
            continue
        if quote:
            flush_quote()
        if not line:
            flush_paragraph()
            close_list()
            continue
        if line == "---":
            flush_paragraph()
            close_list()
            output.append('<hr class="end-rule">')
            continue
        if line.startswith("## "):
            flush_paragraph()
            close_list()
            output.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        image_match = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph()
            close_list()
            alt, src = image_match.groups()
            output.append(
                f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}">'
                f'<figcaption>{html.escape(alt)} · Native Capital Chronicle chart</figcaption></figure>'
            )
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)", line)
        bullet = re.match(r"^-\s+(.*)", line)
        if numbered or bullet:
            flush_paragraph()
            desired = "ol" if numbered else "ul"
            if list_mode != desired:
                close_list()
                output.append(f"<{desired}>")
                list_mode = desired
            item = numbered.group(2) if numbered else bullet.group(1)
            output.append(f"<li>{inline(item)}</li>")
            continue
        paragraph.append(line)

    flush_paragraph()
    close_list()
    flush_quote()
    return "\n".join(output), metadata


def build() -> None:
    markdown = ARTICLE.read_text(encoding="utf-8")
    body, meta = article_body(markdown)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(meta['title'])} · Capital Chronicle</title>
  <style>
    :root {{--ink:#17252d;--paper:#f7f3eb;--muted:#5c6a70;--line:#d4cec2;--rust:#b64f38;--gold:#dc9a65;--green:#3f7566;}}
    *{{box-sizing:border-box}} html{{background:#d9d4ca}} body{{margin:0;color:var(--ink);background:var(--paper);font-family:Georgia,'Times New Roman',serif}}
    .topbar{{height:74px;background:var(--ink);color:#fffaf0;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;border-bottom:4px solid var(--rust);position:relative;z-index:2}}
    .brand{{font:700 25px/1 Arial,sans-serif;letter-spacing:3px}} .edition{{font:12px/1.4 Arial,sans-serif;letter-spacing:1.5px;text-transform:uppercase;color:#cbd3d6}}
    .hero{{display:grid;grid-template-columns:1.08fr .92fr;min-height:650px;background:#efe9de}}
    .hero-copy{{padding:80px 5vw 66px 8vw;display:flex;flex-direction:column;justify-content:center}}
    .kicker{{font:700 14px/1 Arial,sans-serif;color:var(--rust);letter-spacing:2.2px;text-transform:uppercase;margin-bottom:25px}}
    h1{{font-size:clamp(48px,5.4vw,82px);line-height:.99;letter-spacing:-2.6px;margin:0 0 30px;max-width:900px}}
    .dek{{font-size:23px;line-height:1.45;color:#40525a;max-width:760px;margin:0 0 32px}}
    .byline{{font:700 13px/1.5 Arial,sans-serif;letter-spacing:.5px;text-transform:uppercase;color:#52636c}}
    .hero-photo{{position:relative;min-height:650px;overflow:hidden;background:#bec8ca}}
    .hero-photo img{{width:100%;height:100%;object-fit:cover;object-position:60% center;filter:saturate(.82) contrast(1.03)}}
    .hero-photo:after{{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(23,37,45,.12),transparent 40%)}}
    .photo-credit{{position:absolute;bottom:0;left:0;right:0;padding:12px 18px;background:rgba(23,37,45,.82);color:#fff;font:11px/1.4 Arial,sans-serif;z-index:1}}
    .stats{{max-width:1120px;margin:-36px auto 58px;position:relative;display:grid;grid-template-columns:repeat(4,1fr);background:#fff;border:1px solid var(--line);box-shadow:0 14px 34px rgba(23,37,45,.12)}}
    .stat{{padding:26px 27px;border-right:1px solid var(--line)}} .stat:last-child{{border-right:0}} .stat strong{{display:block;font:700 34px/1 Georgia,serif;margin-bottom:9px}} .stat span{{font:12px/1.4 Arial,sans-serif;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}
    .source-desk{{max-width:1010px;margin:0 auto 70px;padding:0 24px}} .source-desk h3{{font:700 12px/1 Arial,sans-serif;letter-spacing:2px;color:var(--rust);text-transform:uppercase;margin:0 0 18px}}
    .documents{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .document{{position:relative;background:#ece7dd;border:1px solid #cfc7ba;padding:24px 28px 22px 64px;min-height:145px}}
    .document:before{{content:'§';position:absolute;left:24px;top:24px;font:700 27px/1 Georgia,serif;color:var(--rust)}} .document b{{font:700 12px/1 Arial,sans-serif;letter-spacing:1.2px;text-transform:uppercase}} .document q{{display:block;font-size:19px;line-height:1.45;margin:14px 0 9px}} .document small{{font:11px/1.4 Arial,sans-serif;color:var(--muted)}}
    main{{max-width:790px;margin:0 auto;padding:0 24px 110px}} main p{{font-size:20px;line-height:1.72;margin:0 0 28px}} main p:first-child{{font-size:27px;line-height:1.5;color:#263a43}} main p:first-child:first-letter{{float:left;font:700 75px/.82 Georgia,serif;color:var(--rust);padding:10px 10px 0 0}}
    main h2{{font-size:38px;line-height:1.14;letter-spacing:-.7px;margin:72px 0 24px;padding-top:22px;border-top:1px solid var(--line)}} main a{{color:#8b3d2c;text-decoration-color:#c9a89f;text-underline-offset:3px}}
    figure{{margin:48px -180px 56px}} figure img{{display:block;width:100%;height:auto;box-shadow:0 12px 28px rgba(23,37,45,.13)}} figcaption{{font:12px/1.5 Arial,sans-serif;color:var(--muted);margin-top:10px}}
    ul,ol{{font-size:19px;line-height:1.6;margin:0 0 34px;padding-left:28px}} li{{padding:6px 0 6px 8px}} li::marker{{color:var(--rust);font-weight:700}}
    .analysis-card{{margin:50px -90px;padding:35px 42px;display:grid;grid-template-columns:110px 1fr;gap:30px;background:var(--ink);color:#fffaf0;border-left:7px solid var(--gold)}} .analysis-card img{{width:104px;height:134px;object-fit:cover;grid-row:1/3;image-rendering:auto}} blockquote{{font-size:23px;line-height:1.5;margin:0}} .analysis-card span{{font:10px/1.4 Arial,sans-serif;color:#aebbc0;letter-spacing:.4px;text-transform:uppercase}}
    .end-rule{{border:0;border-top:3px solid var(--ink);margin:70px 0 28px}} main hr + p,main .end-rule + p{{font-size:14px;line-height:1.65;color:var(--muted);font-family:Arial,sans-serif}}
    footer{{background:var(--ink);color:#cbd3d6;padding:55px 8vw;display:flex;justify-content:space-between;gap:40px;font:12px/1.6 Arial,sans-serif}} footer b{{color:#fffaf0;letter-spacing:1.5px}}
    @media(max-width:1000px){{.hero{{grid-template-columns:1fr}}.hero-photo{{min-height:430px}}.stats{{margin:0;grid-template-columns:1fr 1fr}}.documents{{grid-template-columns:1fr}}figure{{margin:44px 0}}.analysis-card{{margin:44px 0}}}}
  </style>
</head>
<body>
  <header class="topbar"><div class="brand">CAPITAL CHRONICLE</div><div class="edition">Macro · Consumer · Monetary policy</div></header>
  <section class="hero">
    <div class="hero-copy"><div class="kicker">The American consumer · Analysis</div><h1>{html.escape(meta['title'])}</h1><p class="dek">{html.escape(meta['dek'])}</p><div class="byline">{html.escape(meta['byline'])}</div></div>
    <div class="hero-photo"><img src="assets/retail_checkout_vitaly_gariev_unsplash.jpg" alt="Customer receiving a shopping bag at a store checkout"><div class="photo-credit">Context photograph—not evidence of July sales. Photo: Vitaly Gariev / Unsplash</div></div>
  </section>
  <section class="stats">
    <div class="stat"><strong>−0.6%</strong><span>July retail sales<br>month over month</span></div>
    <div class="stat"><strong>+$49.8bn</strong><span>Extra 2026 refunds<br>through May 8</span></div>
    <div class="stat"><strong>3.4%</strong><span>July CPI<br>year over year</span></div>
    <div class="stat"><strong>3.5–3.75%</strong><span>Federal-funds<br>target range</span></div>
  </section>
  <section class="source-desk"><h3>Primary-source desk</h3><div class="documents">
    <div class="document"><b>U.S. Census Bureau · Aug. 14</b><q>July 2026 sales were $763.6 billion, down 0.6 percent from June.</q><small>Advance estimate; seasonally adjusted; not adjusted for prices.</small></div>
    <div class="document"><b>Federal Open Market Committee · July 29</b><q>The Committee decided to maintain the target range at 3½ to 3¾ percent.</q><small>9–3 vote; three dissents favored a 25-basis-point increase.</small></div>
  </div></section>
  <main>{body}</main>
  <footer><div><b>CAPITAL CHRONICLE</b><br>Evidence-first macroeconomic analysis.</div><div>Research cutoff: August 15, 2026 · Zero public writes<br>Full source and rights ledgers accompany this artifact.</div></footer>
</body>
</html>
"""
    OUTPUT.write_text(page, encoding="utf-8", newline="\n")
    manifest = {
        "schema_version": "capital_chronicle.blind_publication_candidate.v1",
        "candidate": "HIGH",
        "requested_model": "gpt-5.6-sol",
        "requested_reasoning_effort": "HIGH",
        "research_cutoff": "2026-08-15 Asia/Saigon",
        "canonical_article": str(ARTICLE.relative_to(ROOT)),
        "publication_html": str(OUTPUT.relative_to(ROOT)),
        "article_sha256": sha256(ARTICLE.read_bytes()).hexdigest(),
        "html_sha256": sha256(OUTPUT.read_bytes()).hexdigest(),
        "public_write_authority": False,
        "public_writes": 0,
        "headless_codex_editorial_brain_used": False,
        "subagents_or_other_tasks_contacted": False,
    }
    (ROOT / "candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    build()
