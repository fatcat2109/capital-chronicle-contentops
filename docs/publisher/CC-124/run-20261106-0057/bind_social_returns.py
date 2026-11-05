"""Bind saved real Neo observations to this operation's existing native requests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import (
    read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file,
)

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
CANONICAL = "https://capitalchronicle.substack.com/p/lower-treasury-yields-leave-bitcoins"

def read(name):
    value = json.loads((HERE / (name + ".json")).read_bytes())
    if value.get("classification") == "TOOL_OUTPUT_IN_FILE":
        value = json.loads(Path(value["output"]["path"]).read_bytes())
    return value

def save(name, value):
    (HERE / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def envelope(begin, observed_at, result, *, dispatched=None, composed=None):
    packet = read(begin)
    value = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"surface": "CODEX_EXEC", "tool_name": "mcp__browseros_neo__run",
            "native_invocation_id": "/root", "observed_at_utc": observed_at,
            "observation_source": "Saved real Neo composer and exact own-object/feed observations; decoded image comparison to the reviewed source."},
        "result": {"request_sha256": packet["request"]["request_sha256"], **result}}
    if dispatched:
        value["tool_observation"]["dispatched_at_utc"] = dispatched
    if composed:
        value["composed"] = composed
    return value

comparisons = []
def compare(destination, object_url, image_url, source):
    raw = read_public_image_bytes(image_url)
    directory = RUN / "media_readback"
    directory.mkdir(exist_ok=True)
    target = directory / (destination + "-treasury-public-image.bin")
    target.write_bytes(raw)
    similarity = visual_similarity_to_local_file(raw, source)
    assert similarity > 0.99, (destination, similarity)
    row = {"destination": destination, "public_object_url": object_url,
        "public_image_url": image_url, "path": str(target), "size_bytes": len(raw),
        "platform_sha256": hashlib.sha256(raw).hexdigest(),
        "source_asset_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "similarity": similarity, "pixels_inspected": True, "source_pixels_match": True,
        "inspection_method": "DECODED_PIXEL_SIMILARITY_TO_APPROVED_SOURCE", **image_metadata_from_bytes(raw)}
    comparisons.append(row)
    return row

x_begin = read("x-publish-begin")
source = Path(x_begin["request"]["content_binding"]["media_manifest"][0]["path"])
x = read("x-public-observed")
x_click = read("x-click-observed")["verified"]["value"]
assert x["canonical_url_verified"] == CANONICAL
posts = [{"observed_text": p["text"], "public_object_id": p["url"].rsplit("/", 1)[-1],
          "public_object_url": p["url"], "public_image_urls": [i["src"] for i in p["images"]]}
         for p in x["posts"]]
assert len(posts) == len(x_click["texts"]) == 4
assert [p["observed_text"] for p in posts[1:]] == x_click["texts"][1:]
x_media = compare("x", x["root_url"], posts[0]["public_image_urls"][0], source)
x_readback = {"status": "SUCCESS", "observed_identity": "@Capitalnicle",
    "public_object_id": posts[0]["public_object_id"], "public_object_url": x["root_url"],
    "observed_text": "\n\n".join(p["observed_text"] for p in posts), "observed_thread": posts,
    "content_verified": True, "public_image_urls": posts[0]["public_image_urls"],
    "observed_link_resolutions": [{"displayed_text": posts[0]["observed_text"].split("\n\n", 1)[-1],
        "short_url": x["short_url"], "target_url": CANONICAL, "target_verified": True,
        "public_object_url": x["root_url"]}],
    "media_comparisons": [x_media], "public_write_performed": False}
save("x-publish-response", envelope("x-publish-begin", datetime.now(timezone.utc).isoformat(),
    {"status": "SUCCESS", "stage": "PUBLISH_CLICK_ATTEMPTED", "observed_identity": "@Capitalnicle",
     "public_object_id": posts[0]["public_object_id"], "public_object_url": x["root_url"], "public_write_performed": True},
    dispatched=x_click["observed_at_utc"], composed={
        "identity": {"authenticated": True, "observed_identity": "@Capitalnicle", "observed_at_utc": x_click["observed_at_utc"],
            "basis": "Own profile Edit profile and @Capitalnicle profile link observed in this composer flow before the one click."},
        "pre_click_posts": x_click["texts"], "readback": x_readback}))

company = read("linkedin-public-observed")["company"]
click = read("linkedin-company-click-observed")["verified"]["value"]
link = read("linkedin-link-resolution-observed")
assert link["links"][0]["url"] == CANONICAL
image = next(i for i in company["images"] if i["alt"].startswith("Nominal 10-year Treasury"))
company_media = compare("linkedin-company", company["url"], image["url"], source)
text = company["text"].split("Follow\n\n", 1)[1].split("\n\n\u200b", 1)[0]
assert "Capital Chronicle may hold positions" in text
company_readback = {"status": "SUCCESS", "observed_identity": "linkedin:company:143198922",
    "public_object_id": "urn:li:share:7524183229864628225", "public_object_url": company["url"],
    "observed_text": text, "content_verified": True, "public_image_urls": [image["url"]],
    "media_comparisons": [company_media], "public_write_performed": False,
    "observed_link_resolutions": [{"displayed_url": link["short_url"], "target_url": CANONICAL,
        "target_verified": True, "public_object_url": company["url"]}]}
save("linkedin-company-publish-response", envelope("linkedin-company-publish-begin", company["observed_at_utc"],
    {"status": "SUCCESS", "stage": "PUBLISH_CLICK_ATTEMPTED", "observed_identity": "linkedin:company:143198922",
        "public_object_id": company_readback["public_object_id"], "public_object_url": company["url"], "public_write_performed": True},
    dispatched=click["identity"]["observed_at_utc"], composed={"identity": click["identity"],
        "pre_click_posts": click["pre_click_posts"], "readback": company_readback}))

personal = read("linkedin-personal-absence-observed")
assert personal["authenticated"] and personal["activity_feed_loaded"] and personal["target_post_absent"]
save("linkedin-personal-readback-response", envelope("linkedin-personal-readback-begin", personal["observed_at_utc"],
    {"status": "SUCCESS", "public_write_performed": False, **personal,
     "observed_profile_url": personal["url"], "content_verified": False}))
save("social-public-image-verification", {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "images": comparisons})
print(json.dumps({"bound": ["x", "linkedin-company", "linkedin-personal-absence"],
    "image_comparisons": [{k: row[k] for k in ("destination", "path", "size_bytes", "platform_sha256", "similarity")} for row in comparisons]}))
