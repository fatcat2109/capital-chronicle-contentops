"""Use the installed media owner to check observed public image pixels and dimensions."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import (
    read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file,
)

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-us500-preview-20261105-g")
OUT = ROOT / "media_readback"
OUT.mkdir(exist_ok=True)
SOURCES = ROOT / "media_assets/jobs-source-bound-r1/media_assets"
rows = []
for name in ("x", "linkedin-company", "youtube"):
    response = json.loads((ROOT / (name + "-publish-response.json")).read_bytes())
    readback = response["composed"]["readback"]
    if name == "youtube":
        # The feed uses a square thumbnail. The exact post displays the full
        # source aspect ratio; bind that observed delivery instead of the crop.
        full = json.loads((ROOT / "youtube-full-image-observation.json").read_bytes())
        assert full["public_object_url"] == readback["public_object_url"]
        readback["public_image_urls"] = [i["src"] for i in full["images"]["value"]]
    for index, url in enumerate(readback["public_image_urls"]):
        local = SOURCES / ("cc124-jobs-payroll-employer-groups.png" if index == 0
                           else "cc124-jobs-treasury-10y-backdrop.png")
        value = read_public_image_bytes(url)
        target = OUT / (name + "-" + str(index) + "-public.png")
        target.write_bytes(value)
        rows.append({"destination": name, "public_object_url": readback["public_object_url"],
            "public_image_url": url, "path": str(target), "platform_sha256": hashlib.sha256(value).hexdigest(),
            "size_bytes": len(value), "source_asset_sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
            "similarity": visual_similarity_to_local_file(value, local), **image_metadata_from_bytes(value)})
report = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "images": rows}
(ROOT / "social-public-image-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"observed_at_utc": report["observed_at_utc"], "images": [
    {k: r[k] for k in ("destination", "path", "size_bytes", "platform_sha256", "similarity", "width", "height")}
    for r in rows]}))
