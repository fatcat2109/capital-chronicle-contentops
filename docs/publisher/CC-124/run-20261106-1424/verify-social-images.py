"""Inspect retained public-image bytes through the existing media authority."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from live_contentops.media_manifest_authority_v1 import read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / "media/media_assets/post-facts-87d77248283f787c5527.png"
OUTPUT = ROOT / "media/readback"
OUTPUT.mkdir(exist_ok=True)
def verify(name):
    observation = json.loads((ROOT / (name + "-readback-observation.json")).read_text(encoding="utf-8"))
    images = observation.get("images") or observation["posts"][0]["images"]
    url = images[0]["url"]
    raw = read_public_image_bytes(url)
    metadata = image_metadata_from_bytes(raw)
    path = OUTPUT / (name + ("." + metadata["mime_type"].split("/")[-1].replace("jpeg","jpg")))
    path.write_bytes(raw)
    similarity = visual_similarity_to_local_file(raw, LOCAL)
    result = {"destination": name, "public_object_url": observation["url"], "public_image_url": url,
              "binary_path": str(path), "platform_sha256": sha256(raw).hexdigest(),
              "source_asset_sha256": sha256(LOCAL.read_bytes()).hexdigest(),
              "bytes": len(raw), **metadata, "visual_similarity": similarity,
              "dimension_ratio_matches": abs(metadata["width"]/metadata["height"] - 1080/1350) < .005,
              "pixels_inspected": False, "source_pixels_match": False}
    return result
with ThreadPoolExecutor(max_workers=1) as pool:
    results = list(pool.map(verify, ["linkedin_company", "linkedin", "x", "youtube"]))
packet = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "comparisons": results,
          "inspection_state": "BINARY_COMPARISON_COMPLETE_PIXEL_INSPECTION_PENDING"}
(ROOT / "social-image-comparisons.json").write_text(json.dumps(packet, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"results": [{k:r[k] for k in ("destination","binary_path","bytes","width","height","platform_sha256","visual_similarity","dimension_ratio_matches")} for r in results]}))
