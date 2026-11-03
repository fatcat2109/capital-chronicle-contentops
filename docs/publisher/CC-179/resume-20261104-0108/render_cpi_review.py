"""Render the existing local reader component; never connect to a user browser."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from live_contentops.native_desktop_editorial_v1 import final_visual_binding

root = Path(__file__).resolve().parent
view = json.loads((root / "cpi-derivative-view.json").read_bytes())
governed = deepcopy(view)
view["run_id"] = "cc124-prepare-20261103-a"
view["publication"] = {"state": "REVIEW_INPUT_ONLY", "destinations": []}
view["evidence"] = [{**e, "source_id": e.get("source_id", e.get("document_id"))} for e in view["evidence"]]
view["media_assets"] = [{**a, "preview_data_url": Path(a["path"]).as_uri()} for a in view["media_assets"]]
folder = root / "render"
folder.mkdir(exist_ok=True)
workspace = {"native_edition": [view], "owner_edition": {"edition_id": "CC179-CPI-SOCIAL-REVIEW",
    "title": "September CPI: retained article and social correction", "operation_ids": [view["run_id"]],
    "ready": 1, "held": 0, "missing": 0, "held_candidates": [], "preview_count": 8, "publication_authority": False}}
source = folder / "workspace.json"
source.write_text(json.dumps(workspace, ensure_ascii=False) + "\n", encoding="utf-8")
html = folder / "reader.html"
subprocess.run(["node", str(repo / "ui/contentops_v5/scripts/render-report-workspace.mjs"),
    str(source), str(html), "--owner-review"], cwd=repo, check=True, capture_output=True)

from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

variants = final_visual_binding(governed, renders=None)["variants"]
renders = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    try:
        page = browser.new_page(bypass_csp=True)
        for viewport, width in [("desktop", 1265), ("mobile", 390)]:
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(html.as_uri(), wait_until="load")
            page.get_by_label("Choose reading view").wait_for()
            for destination, variant in sorted(variants.items()):
                page.get_by_label("Choose reading view").select_option("canonical" if destination == "substack" else destination)
                article = page.locator("article[data-owner-story]")
                page.wait_for_function("Array.from(document.querySelectorAll('article[data-owner-story] img')).every(i => i.complete && i.naturalWidth > 0)")
                path = folder / f"{destination}-{viewport}.png"
                article.screenshot(path=str(path))
                with Image.open(path) as pixels:
                    dimensions = pixels.size
                renders.append({"render_id": f"cc179-cpi-{destination}-{viewport}", "destination": destination,
                    "viewport": viewport, "variant_sha256": variant, "path": str(path),
                    "sha256": sha256(path.read_bytes()).hexdigest(), "width": dimensions[0], "height": dimensions[1],
                    "render_source": {"path": str(html), "sha256": sha256(html.read_bytes()).hexdigest()}})
    finally:
        browser.close()
binding = final_visual_binding(governed, renders=renders, destinations=set(variants))
(root / "cpi-final-render-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
for viewport in ("desktop", "mobile"):
    selected = [r for r in renders if r["viewport"] == viewport and r["destination"] != "substack"]
    for group in range(2):
        chunks = selected[group * 4:(group + 1) * 4]
        thumbs = []
        for render in chunks:
            with Image.open(render["path"]) as pixels:
                thumb = pixels.convert("RGB")
                thumb.thumbnail((390, 1600))
                thumbs.append((render["destination"], thumb.copy()))
        sheet = Image.new("RGB", (400 * len(thumbs), max(p.size[1] for _, p in thumbs) + 40), "#e9ecea")
        draw = ImageDraw.Draw(sheet)
        for i, (name, thumb) in enumerate(thumbs):
            draw.text((400 * i + 8, 8), name + " " + viewport, fill="#102d31")
            sheet.paste(thumb, (400 * i, 35))
        sheet.save(folder / f"social-{viewport}-{group + 1}.png")
print(json.dumps({"html": str(html), "renders": len(renders), "binding": str(root / "cpi-final-render-binding.json"),
    "observed_at_utc": datetime.now(timezone.utc).isoformat(), "public_write_performed": False}))
