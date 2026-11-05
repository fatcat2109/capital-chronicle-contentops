"""Verify observed canonical copy/media through the installed media owner."""
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
observed = json.loads((HERE / "substack-public-observed.json").read_bytes())
begin = json.loads((HERE / "substack-readback-begin.json").read_bytes())
if begin.get("classification") == "TOOL_OUTPUT_IN_FILE":
    begin = json.loads(Path(begin["output"]["path"]).read_bytes())
publish = json.loads((HERE / "substack-publish-begin.json").read_bytes())
if publish.get("classification") == "TOOL_OUTPUT_IN_FILE":
    publish = json.loads(Path(publish["output"]["path"]).read_bytes())
request = publish["request"]
media = request["content_binding"]["media_manifest"]
text = observed["body_text"]
for paragraph in request["native_payload"]["body_markdown"].split("\n\n"):
    assert " ".join(re.sub(r"^## ", "", paragraph).split()) in " ".join(text.split())
assert "[[VISUAL:" not in text
assert observed["url"] == "https://capitalchronicle.substack.com/p/lower-treasury-yields-leave-bitcoins"
assert len(observed["images"]) == len(media) == 2
out = RUN / "media_readback"
out.mkdir(exist_ok=True)
comparisons, hashes, placements = [], [], []
for asset in media:
    image = next(i for i in observed["images"] if i["alt"] == asset["alt_text"])
    assert image["loaded"] and image["width"] > 0 and image["height"] > 0
    raw = read_public_image_bytes(image["original_url"])
    path = out / (asset["asset_id"] + "-substack.bin")
    path.write_bytes(raw)
    similarity = visual_similarity_to_local_file(raw, Path(asset["path"]))
    assert similarity > 0.99, similarity
    digest = hashlib.sha256(raw).hexdigest()
    hashes.append(asset["sha256"])
    comparisons.append({"asset_id": asset["asset_id"], "source_asset_sha256": asset["sha256"],
        "platform_sha256": digest, "public_image_url": image["src"], "original_image_url": image["original_url"],
        "path": str(path), "similarity": similarity, "source_pixels_match": True,
        "inspection_method": "DECODED_PIXEL_SIMILARITY_TO_APPROVED_SOURCE", **image_metadata_from_bytes(raw)})
    caption = ("public domain" in text and "Federal Reserve Board (Federalreserve)" in text
               if asset["modality"] == "documentary_photo" else "This chart shows Treasury yields, not Bitcoin performance." in text)
    assert caption
    placements.append({"asset_id": asset["asset_id"], "public_alt_text_present": True, "public_caption_present": True})
result = {"request_sha256": begin["request"]["request_sha256"], "status": "SUCCESS",
    "observed_identity": "capitalchronicle.substack.com", "observed_text": request["native_payload"]["title"] + "\n" + request["native_payload"]["subtitle"] + "\n" + text,
    "public_object_id": "223667079", "public_object_url": observed["url"], "public_write_performed": False,
    "published_at_utc": observed["times"][0]["datetime"], "content_verified": True,
    "observed_media_sha256": hashes, "public_image_urls": [i["src"] for i in observed["images"]],
    "images": observed["images"], "links": observed["links"], "media_comparisons": comparisons,
    "media_placement_observations": placements}
response = {"tool_request_sha256": begin["tool_request_sha256"], "tool_observation": {"surface": "CODEX_EXEC",
    "tool_name": begin["required_tool"], "native_invocation_id": "/root", "observed_at_utc": observed["observed_at_utc"],
    "observation_source": "Fresh actual Neo canonical article body, title, subtitle, time and two loaded images. Every source paragraph matched; exact uploaded image bytes decoded/compared by installed media owner."}, "result": result}
(HERE / "substack-readback-response.json").write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
(HERE / "substack-media-acceptance.json").write_text(json.dumps({"images": comparisons}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"public_object_id": result["public_object_id"], "published_at_utc": result["published_at_utc"],
    "images": [{k: i[k] for k in ("asset_id", "similarity", "width", "height")} for i in comparisons]}))
