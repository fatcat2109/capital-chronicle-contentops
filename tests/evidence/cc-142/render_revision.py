"""Render the MAX-authored exact revision for local inspection; no public action."""
from pathlib import Path
from copy import deepcopy
import hashlib
import html
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart

ROOT = Path(__file__).resolve().parent
writer = json.loads((ROOT / "native/max-result.json").read_bytes())
review = json.loads((ROOT / "native/asset-review-r2.json").read_bytes())
docs = json.loads((ROOT / "cpi-chart-source-documents.json").read_bytes())
assets = json.loads((ROOT / "chart-assets-unreviewed.json").read_bytes())
for i in range(2):
    old = assets[i]
    finding = next(a for a in review["assets"] if a["asset_id"] == old["asset_id"])
    packet = deepcopy(old["editorial_data_packet"])
    packet["asset_id"] = old["asset_id"].replace("-r2", "-r3")
    packet["source_caption"] = finding["repair"]["public_footer"]
    assets[i] = build_editorial_data_chart(packet, docs, output_dir=ROOT / "render-r3")
    assert assets[i]["computed_values"] == old["computed_values"]
(ROOT / "chart-assets-r3-unreviewed.json").write_text(json.dumps(assets, indent=2)+"\n", encoding="utf-8")
photo = json.loads((ROOT / "media/photo-asset-unreviewed.json").read_bytes())


def inline(text):
    text = html.escape(text)
    return re.sub(r"\[([^\]]+)\]\((https://[^)]+)\)", r'<a href="\2">\1</a>', text)


def figure(asset):
    path = Path(asset["path"]).as_uri()
    credit = asset.get("attribution", "") if asset["modality"] == "documentary_photo" else ""
    return (f'<figure><a href="{path}" target="_blank"><img src="{path}" alt="{html.escape(asset["alt_text"])}"></a>'
        f'<figcaption>{inline(asset["caption"])}'
        + (f' <span class="credit">{inline(credit)}</span>' if credit else "") + '</figcaption></figure>')


blocks = writer["revised_article_markdown"].strip().split("\n\n")
rendered = []
photo_added = False
for block in blocks:
    if block.startswith("# "):
        rendered.append("<h1>"+inline(block[2:])+"</h1>")
    elif block.startswith("## "):
        rendered.append("<h2>"+inline(block[3:])+"</h2>")
    else:
        rendered.append("<p>"+inline(block)+"</p>")
        if not photo_added:
            rendered.append(figure(photo))
            photo_added = True
        for asset, choice in zip(assets, writer["visual_decision"]["charts"]):
            if block == choice["placement"]["after_paragraph"]:
                rendered.append(figure(asset))
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>September CPI: why 0.6% and 3.7% answer different questions</title><style>
*{box-sizing:border-box}body{margin:0;background:#fffdf9;color:#222;font:19px/1.6 Georgia,serif}main{max-width:760px;margin:auto;padding:36px 28px 70px}header{font:600 14px/1.4 system-ui;letter-spacing:.08em;border-bottom:1px solid #ddd;padding-bottom:18px;margin-bottom:30px}h1{font-size:40px;line-height:1.15;margin:0 0 30px}h2{font-size:27px;line-height:1.25;margin:38px 0 18px}p{margin:0 0 21px}a{color:#175957}figure{margin:25px 0 30px}figure img{display:block;width:100%;height:auto}figcaption{font:14px/1.5 system-ui;color:#555;margin-top:9px}.credit{font-size:12px} @media(max-width:600px){main{padding:24px 20px 45px}h1{font-size:32px}h2{font-size:25px}body{font-size:18px}figcaption{font-size:13px}}
</style></head><body><main><header>CAPITAL CHRONICLE</header>'''+"\n".join(rendered)+"</main></body></html>"
path = ROOT / "render-r3/reader.html"
path.write_text(page, encoding="utf-8")
(ROOT / "render-r3/reader-source.json").write_text(json.dumps({"path": str(path),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "writer_result_sha256": hashlib.sha256((ROOT / "native/max-result.json").read_bytes()).hexdigest(),
    "asset_sha256": [a["sha256"] for a in assets]+[photo["sha256"]], "public_write_performed": False}, indent=2)+"\n", encoding="utf-8")
print(path)
