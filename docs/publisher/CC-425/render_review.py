"""Read the existing owner and preview its canonical rich-text renderer locally."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.article_rich_text_v1 import markdown_to_rich_text, rich_text_to_html
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import native_artifact_key, native_review_revision
from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
from live_contentops.cpi_reaction_page_v1 import validate_bound_tables

ROOT = Path(__file__).resolve().parent
OP = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc425-cpi-reaction-history-20261111-v1")


def main():
    binding = json.loads((OP / "binding.json").read_bytes())
    store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
    row = store.get_outbox_message(native_artifact_key(store, binding["run_id"], "cc-editorial-final-"))
    result = json.loads(row["payload"])
    article = _reader_safe_native_article(result["article"], article_mode=result["article"]["resolved_article_mode"])
    validate_bound_tables(article)
    assets = result["media_assets"]
    sections = re.split(r"(?=^#{1,6}\s)", article["substack_body_markdown"], flags=re.M)
    content, links = [], []
    def figure(asset):
        return (f'<figure><a href="{html.escape(Path(asset["path"]).as_uri())}">'
            f'<img src="{html.escape(Path(asset["path"]).as_uri())}" alt="{html.escape(asset["alt_text"])}"></a>'
            f'<figcaption>{html.escape(asset["caption"])}</figcaption></figure>')
    for index, section in enumerate(sections):
        if not section.strip():
            continue
        heading = re.match(r"^#{1,6}\s+([^\n]+)", section)
        name = heading[1] if heading else "introduction"
        rendered = rich_text_to_html(markdown_to_rich_text(section))
        if heading:
            anchor = "section-" + str(index)
            rendered = re.sub(r"<h([2-4])>", lambda m: f'<h{m[1]} id="{anchor}">', rendered, count=1)
            links.append(f'<a href="#{anchor}">{html.escape(name)}</a>')
        rendered = rendered.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
        content.append(rendered)
        content.extend(figure(a) for a in assets if a.get("placement_after") == name)
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(article["title"])}</title><style>'
        'body{margin:0;background:#faf9f5;color:#193b3e;font:18px/1.65 Georgia,serif}'
        'main{max-width:940px;padding:24px;margin:auto}h1{font-size:clamp(30px,5vw,45px);line-height:1.17}'
        'h2{margin-top:48px;line-height:1.3}aside{font:14px/1.5 system-ui;border-bottom:1px solid #c6d0ca;padding-bottom:16px}'
        'nav{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:12px}a{color:#12666a}'
        'figure{margin:28px 0}img{display:block;max-width:100%;height:auto}figcaption{font:14px/1.5 system-ui;margin-top:8px}'
        '.table-scroll{overflow:auto;margin:24px 0;border:1px solid #c6d0ca}table{border-collapse:collapse;min-width:720px;width:100%;font:14px/1.5 system-ui}'
        'th,td{padding:10px;text-align:left;border-bottom:1px solid #dde3dd;white-space:nowrap}th{background:#193b3e;color:white}'
        'tbody tr:nth-child(even){background:#eef2eb}section{scroll-margin-top:15px}'
        '</style></head><body><main><aside>Prepared for Ops Product’s table review. Publication is pending.'
        '<nav>' + ''.join(links) + '</nav></aside><article>'
        f'<h1>{html.escape(article["title"])}</h1><p>{html.escape(article.get("dek") or article.get("subtitle") or "")}</p>'
        + ''.join(content) + '</article></main></body></html>')
    assert 'base64,' not in page and '[[SOURCE:' not in page
    target = ROOT / "review.html"
    target.write_bytes(page.encode("utf-8"))
    reader_text = "\n".join(line.rstrip() for line in article["substack_body_markdown"].splitlines())
    (ROOT / "review-article.md").write_bytes((reader_text + "\n").encode("utf-8"))
    metadata = {"operation_id": binding["run_id"], "article_identity": result["article_identity"],
        "article_revision": native_review_revision(result), "preview_path": str(target),
        "preview_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "tables": page.count('<table>'),
        "media_assets": [{"asset_id": a["asset_id"], "sha256": a["sha256"]} for a in assets],
        "public_write_performed": False}
    (ROOT / "reader-render.json").write_bytes((json.dumps(metadata, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()
