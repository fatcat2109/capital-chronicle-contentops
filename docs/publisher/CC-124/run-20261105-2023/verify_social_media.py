"""Compare exact observed platform images with the approved local charts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
OUT = ROOT / "media_readback"
OUT.mkdir(exist_ok=True)
source = ROOT / "media_assets/fx-source-bound-r2/media_assets/cc124-fx-dollar-directions.png"
rows = []
for name in ("x", "linkedin-company"):
    response = json.loads((ROOT / (name + "-composed-response.json")).read_bytes())
    readback = response["composed"]["readback"]
    for index, url in enumerate(readback["public_image_urls"]):
        local = source if index == 0 else source.with_name("cc124-fx-matched-treasury.png")
        value = read_public_image_bytes(url)
        target = OUT / (name + "-" + str(index) + "-public.png")
        target.write_bytes(value)
        rows.append({"destination": name, "public_object_url": readback["public_object_url"],
            "public_image_url": url, "path": str(target), "platform_sha256": hashlib.sha256(value).hexdigest(),
            "size_bytes": len(value), "source_asset_sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
            "similarity": visual_similarity_to_local_file(value, local), **image_metadata_from_bytes(value)})
report = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "images": rows}
(ROOT / "social-public-image-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
