"""Use the existing media owner to bind observed canonical originals by hash."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.media_manifest_authority_v1 import build_delivery_media_manifest
from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

root = Path(__file__).resolve().parent
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
reference = json.loads((root / "cpi-bound-review-reference.json").read_bytes())
observed = json.loads((root / "cpi-canonical-image-readback.json").read_bytes())
with newsroom_lease(store):
    revision, view, acceptance = reader_presentation_acceptance(store, run_id="cc124-prepare-20261103-a", reference=reference)
    if observed["url"] != revision["objects"]["substack"]["public_object_url"] or not observed["titlePresent"]:
        raise ValueError("EXACT_CONFIRMED_CANONICAL_IMAGE_READBACK_REQUIRED")
    full = json.loads((root / "cpi-canonical-delivery-manifest.json").read_bytes())
    selected_ids = {asset_id for ids in revision["channel_media"].values() for asset_id in ids}
    selected_assets = [a for a in view["media_assets"] if a["asset_id"] in selected_ids]
    observed_selected_urls = [a["verified_public_delivery_url"] for a in full["assets"]
        if a["media_asset_id"] in selected_ids and a.get("local_public_hash_continuity") is True]
    manifest = build_delivery_media_manifest(media_packet={"assets": selected_assets},
        public_image_urls=observed_selected_urls, run_id=revision["run_id"])
    (root / "cpi-selected-channel-delivery-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    canonical = store.get_outbox_message(revision["objects"]["substack"]["message_id"])
    output = Path(json.loads(canonical["payload"])["output_dir"]) / "delivery_media_manifest_v1.json"
    previous = sha256(output.read_bytes()).hexdigest() if output.exists() else None
    if manifest["status"] == "PASS":
        output.write_text(json.dumps(manifest, indent=2) + "\n")
    result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": manifest["status"],
        "blockers": manifest["blockers"], "media_count": len(manifest["assets"]),
        "review_revision": acceptance["article_revision"], "delivery_path": str(output),
        "selected_channel_asset_ids": sorted(selected_ids),
        "unselected_canonical_asset_limits": full["blockers"],
        "previous_manifest_sha256": previous, "manifest_bound": manifest["status"] == "PASS",
        "canonical_edited": False, "public_write_performed": False}
    (root / "cpi-selected-delivery-bind-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
