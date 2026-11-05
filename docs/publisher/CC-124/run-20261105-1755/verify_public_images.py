"""Verify exact approved bytes through the existing publication media owner."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import build_delivery_media_manifest
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
packet = json.loads((ROOT / "native-neo/f6f6dd5e1530b0d841cee57042f09698a4553731dd4185dec2d77bf3aeb464cb.request.json").read_bytes())
request = packet["request"]
observed = json.loads((ROOT / "substack-public-observation.json").read_bytes())
assets = json.loads((ROOT / "media-plan-bind-input.json").read_bytes())["assets"]
manifest = build_delivery_media_manifest(media_packet={"assets": assets},
    public_image_urls=[i["src"] for i in observed["images"]],
    run_id=request["work_item_id"])
manifest["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
(ROOT / "substack-public-image-verification.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": manifest["status"], "blockers": manifest["blockers"],
    "assets": [{k:a.get(k) for k in ("media_asset_id","sha256","local_public_hash_continuity","verified_public_delivery_url")} for a in manifest["assets"]]}))
assert manifest["status"] == "PASS", manifest["blockers"]
