"""Render MAX-authored copy and an original aggregate-data card for CC-427."""
from __future__ import annotations

from decimal import Decimal
from html import escape
import hashlib
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from live_contentops.article_rich_text_v1 import markdown_to_rich_text, rich_text_to_html
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.event_article_guard_v1 import check_publication_copy


def render():
    readback = json.loads((ROOT / "consumer-readback.json").read_bytes())
    edition = Path(readback["public_edition"])
    report = json.loads((edition / "report.json").read_bytes())
    document = json.loads((edition / "source-document.json").read_bytes())
    text = (ROOT / "article.md").read_text(encoding="utf-8")
    title = "Our November FTMO test has not passed yet"
    check_publication_copy({"title": title, "text": text})
    blocks = markdown_to_rich_text(text)
    body = rich_text_to_html(blocks)
    assert body.count("<table>") == 1 and body.count("<tbody>") == 1
    assert len(next(b for b in blocks["blocks"] if b["type"] == "table")["rows"]) == 6
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    prose = "\n".join(line for line in plain.splitlines() if not line.startswith(("|", "#")))
    sentences = [s for s in re.split(r"(?<!\d)[.!?](?!\d)\s+", prose) if s.strip()]
    lengths = [len(s.split()) for s in sentences]
    assert max(lengths) <= 35
    report_hash = sha256_of(report)
    media = ROOT / "media"
    media.mkdir(exist_ok=True)
    image = Image.new("RGB", (1200, 960), "#f7f4eb")
    draw = ImageDraw.Draw(image)
    def font(size, bold=False):
        path = Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
        return ImageFont.truetype(str(path), size)
    def line(x, y, label, size=30, color="#162a3a", bold=False):
        draw.text((x, y), label, font=font(size, bold), fill=color)
    draw.rectangle((0, 0, 1200, 20), fill="#117767")
    line(64, 64, "CAPITAL CHRONICLE  /  MODEL AUDIT", 25, "#117767", True)
    line(64, 122, "November: no Challenge pass yet", 52, bold=True)
    line(64, 205, "Month to date through 11 November ET", 28, "#536675")
    line(64, 274, str(report["trade_count"]), 88, bold=True)
    line(180, 292, "recorded desk positions", 38)
    line(180, 346, f"{report['closed_trade_count']} closed  /  {report['open_trade_count']} still open", 30)
    draw.rounded_rectangle((64, 420, 1136, 575), radius=18, fill="#e8eee9")
    line(94, 442, "Booked model change", 30)
    change = format(Decimal(report["booked_model_change_pct"]), ".2f") + "%"
    line(94, 488, change, 48, bold=True)
    line(480, 468, "Excludes unrealised P/L", 31)
    line(480, 514, "Not an equity return", 28, "#536675")
    line(64, 621, f"Opening days: {report['trading_days']} of 4 required", 34, bold=True)
    line(64, 682, "Daily and overall equity-loss limits: UNKNOWN", 32, "#92622c", True)
    line(64, 742, "News / weekend restriction: evaluation exemptions", 30)
    line(64, 823, "Fixed 0.5% of starting model capital per original risk unit", 26)
    line(64, 874, "Recorded executions scaled into a model; no FTMO certification", 24, "#536675")
    card = media / ("model-audit-" + report_hash[:16] + ".png")
    image.save(card)
    assert card.stat().st_size < 1_000_000
    payload = {"title": title, "dek": "A month-to-date model audit of the desk's recorded trades against FTMO's two-step objectives.",
        "substack_body_markdown": text, "prop_challenge_binding": document["prop_challenge_binding"],
        "public_write_state": "NOT_DISPATCHED", "editorial_review": "OPS_REVIEW_PENDING",
        "source_pack_path": str(edition / "source-pack.json"),
        "authorship": {"configured_model": "gpt-6.1-sol", "configured_effort": "max",
                       "runtime_model": None, "runtime_effort": None,
                       "observation": "CONFIGURED_NOT_OBSERVED", "supported_context_identity": "/root"},
        "media": {"path": str(card), "sha256": hashlib.sha256(card.read_bytes()).hexdigest(),
                  "width": 1200, "height": 960, "rights": "CAPITAL_CHRONICLE_ORIGINAL_DATA_CARD",
                  "source_report_sha256": report_hash}}
    (ROOT / "article.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    style = """body{background:#ebe9e1;color:#162a3a;font-family:Georgia,serif;margin:0;padding:34px 14px}
    article{box-sizing:border-box;background:#fffdf7;margin:0 auto;padding:44px;max-width:840px;line-height:1.64;font-size:20px;container-type:inline-size}
    h1{font-size:42px;line-height:1.13;margin:16px 0 20px}h2{font-size:27px;margin-top:34px}a{color:#117767}
    img{width:100%;height:auto;display:block}.brand{font:700 13px Arial,sans-serif;letter-spacing:2px;color:#117767}
    .table-wrap{max-width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:620px;font:15px/1.5 Arial,sans-serif}
    td,th{padding:12px 10px;text-align:left;vertical-align:top;border-bottom:1px solid #d9dfda}th{background:#e8eee9}
    .caption{font:13px/1.45 Arial,sans-serif;color:#536675;margin-bottom:28px}.preview{font:13px Arial,sans-serif;max-width:840px;margin:0 auto 16px;color:#536675}
    @media(max-width:600px){article{padding:24px 20px;font-size:18px}h1{font-size:34px}}
    @container(max-width:580px){table{min-width:0;font-size:15px}thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
    tbody,tr,td{display:block}tr{margin:0 0 14px;border:1px solid #d9dfda;border-radius:8px;overflow:hidden}td{border:0;padding:9px 12px}
    td:first-child{font-weight:700;background:#e8eee9}td:nth-child(2){font-weight:700;color:#117767;padding-bottom:0}td:last-child{padding-top:5px}}
    """
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    picture = '<figure style="margin:0"><a href="media/' + card.name + '" target="_blank"><img src="media/' + card.name + '" alt="Five recorded positions: four closed, one open; booked change ' + change + ', excluding unrealised results. Equity-loss limits unknown."></a></figure>'
    content = '<article><div class="brand">CAPITAL CHRONICLE</div><h1>' + escape(title) + '</h1>' + picture + '<p class="caption">Capital Chronicle model audit. Booked model change excludes unrealised P/L. Original risk normalised to 0.5% of starting model capital.</p>' + body + '</article>'
    for name, extra in (("review.html", ""), ("review-mobile.html", "article{width:390px;max-width:390px;padding:24px 20px;font-size:18px}h1{font-size:34px}body{padding:18px 0}.preview{max-width:390px}")):
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(title) + '</title><style>' + style + extra + '</style></head><body><div class="preview">Prepared reader draft · Ops review pending</div>' + content + '</body></html>'
        (ROOT / name).write_text(page, encoding="utf-8")
    summary = {"source_report_sha256": report_hash, "article_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "canonical_rich_text_schema": blocks["schema_version"], "rule_table_rows": 6,
        "maximum_sentence_words": max(lengths), "media": payload["media"],
        "public_notice_present": "Capital Chronicle offers analysis only, not financial advice or recommendations." in text,
        "publication_state": "NOT_DISPATCHED"}
    (ROOT / "render-checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    render()
