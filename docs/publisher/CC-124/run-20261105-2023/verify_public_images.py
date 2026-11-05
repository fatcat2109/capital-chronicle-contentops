"""Bind public article images through the installed media owner."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import build_delivery_media_manifest

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
browser_output = Path(r"C:\Users\bullw\AppData\Local\BrowserClaw\Application\155.0.8317.26\.browseros\tool-output\evaluate_in_page-1793890971432-ada5f143-46dd-4bba-9f25-e38088a56cbc.txt")
raw = browser_output.read_text(encoding="utf-8")
observed = json.loads(raw[raw.index("{"):raw.rfind("}")+1])
(ROOT / "substack-public-observation.json").write_text(json.dumps(observed, indent=2), encoding="utf-8")
assets = json.loads((ROOT / "media_assets/media-plan-binding.json").read_bytes())["assets"]
manifest = build_delivery_media_manifest(media_packet={"assets": assets},
    public_image_urls=[i["src"] for i in observed["images"]], run_id=ROOT.name)
manifest["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
(ROOT / "substack-public-image-verification.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": manifest["status"], "blockers": manifest["blockers"],
    "assets": [{k: a.get(k) for k in ("media_asset_id", "sha256", "local_public_hash_continuity", "verified_public_delivery_url")} for a in manifest["assets"]]}))
assert manifest["status"] == "PASS", manifest["blockers"]
