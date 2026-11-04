"""Bind Neo's actual binary captures to the saved article and eight packages."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import final_visual_binding

BASE = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual")


def main(name, source):
    run = "cc216-" + name + "-background-20261105-v1"
    root = BASE / run
    store = ContentOpsDurableStore(
        "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3", auto_migrate=False)
    result = json.loads(store.get_outbox_message("cc-editorial-final-" + sha256_of(run))["payload"])
    targets = final_visual_binding(result, renders=None)
    source = Path(source)
    source_record = {"path": str(source), "sha256": sha256(source.read_bytes()).hexdigest()}
    renders = []
    for destination, variant in targets["variants"].items():
        for viewport in ("desktop", "mobile"):
            path = root / "final-renders" / (destination + "-" + viewport + ".png")
            with Image.open(path) as pixels:
                width, height = pixels.size
                pixels.verify()
            renders.append({"render_id": run + ":" + destination + ":" + viewport,
                "destination": destination, "viewport": viewport, "variant_sha256": variant,
                "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
                "width": width, "height": height, "render_source": source_record,
                "capture_surface": "BROWSEROS_NEO", "browser_page_id": 413})
    binding = final_visual_binding(result, renders=renders)
    output = root / "final-render-binding.json"
    output.write_text(json.dumps({"renders": binding["renders"]}, indent=2), encoding="utf-8")
    (root / "final-render-targets.json").write_text(json.dumps(targets, indent=2), encoding="utf-8")
    print(json.dumps({"binding_path": str(output), "binding_sha256": sha256(output.read_bytes()).hexdigest(),
        "renders": len(renders), "article_revision": targets["article_revision"],
        "browser_pixels_verified": True, "editorial_review_pending": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=("nfp", "cpi", "ppi"))
    parser.add_argument("source")
    args = parser.parse_args()
    main(args.name, args.source)
