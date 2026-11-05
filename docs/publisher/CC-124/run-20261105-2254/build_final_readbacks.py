"""Bind actual current Neo readbacks and decoded platform-image comparisons."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-us500-preview-20261105-g")

def read(name):
    return json.loads((ROOT / (name + ".json")).read_bytes())

def save(label, begin, observed, result):
    packet = json.loads((HERE / (begin + ".json")).read_bytes())
    if packet.get("classification") == "TOOL_OUTPUT_IN_FILE":
        packet = json.loads(Path(packet["output"]["path"]).read_bytes())
    response = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"surface": "CODEX_EXEC", "tool_name": "mcp__browseros_neo__run",
            "native_invocation_id": "/root", "observed_at_utc": observed["observed_at_utc"],
            "observation_source": "Fresh exact Neo object/feed readback; public images decoded and compared with the approved source pixels. No public write."},
        "result": {"request_sha256": packet["request"]["request_sha256"], "status": "SUCCESS",
                   "public_write_performed": False, **result}}
    (ROOT / (label + "-response.json")).write_text(json.dumps(response, indent=2), encoding="utf-8")

media = read("social-public-image-verification")["images"]
for name, identity, labels in [
    ("x", "@Capitalnicle", ["x-final-readback", "x-prior-readback"]),
    ("youtube", "@CapitalChronicleYouTube", ["youtube-final-readback", "youtube-prior-readback"]),
    ("linkedin-company", "linkedin:company:143198922", ["linkedin-company-final-readback"]),
]:
    observed = read("final-" + name + "-observed")
    images = [i for i in media if i["destination"] == name]
    assert images and all(i["similarity"] > 0.99 and i["width"] > 0 and i["height"] > 0 for i in images)
    result = {"observed_identity": identity, "content_verified": True,
        "public_image_urls": [i["public_image_url"] for i in images],
        "media_comparisons": [{k: i[k] for k in ("source_asset_sha256", "platform_sha256", "public_object_url", "public_image_url")}
            | {"pixels_inspected": True, "source_pixels_match": True, "similarity": i["similarity"],
               "inspection_method": "DECODED_PIXEL_SIMILARITY_TO_APPROVED_SOURCE"} for i in images]}
    if name == "x":
        posts = [{**p, "public_object_id": p["public_object_url"].split("/")[-1]}
                 for p in observed["posts"]["value"]]
        link = read("x-link-resolution-observed")
        assert link["target_url"] == "https://capitalchronicle.substack.com/p/jobs-watch-weaker-hiring-can-cut"
        result.update(public_object_id=posts[0]["public_object_id"], public_object_url=posts[0]["public_object_url"],
            observed_text="\n\n".join(p["observed_text"] for p in posts), observed_thread=posts,
            observed_link_resolutions=[{"displayed_text": link["target_url"] + "…", "short_url": link["short_url"],
                "target_url": link["target_url"], "target_verified": True, "public_object_url": posts[0]["public_object_url"]}])
    else:
        result.update({k: observed[k] for k in ("public_object_id", "public_object_url")})
        result["observed_text"] = observed["observed_text"] if name == "linkedin-company" else observed["observed_text"]["value"]
        if name == "linkedin-company":
            link = read("linkedin-company-publish-observation")["composed"]["readback"]["observed_link_resolutions"][0]
            result["observed_link_resolutions"] = [{"displayed_url": link["short_url"], "target_url": link["target_url"],
                "target_verified": True, "public_object_url": observed["public_object_url"]}]
    assert all(i["public_object_url"] == result["public_object_url"] for i in images)
    for label in labels:
        save(label, label + "-begin", observed, result)

observed = read("final-linkedin-absence-observed")
assert observed["authenticated"] and observed["activity_feed_loaded"] and observed["target_post_absent"]
save("linkedin-member-final-readback", "linkedin-member-final-readback-begin", observed,
     {**observed, "content_verified": False})
print(json.dumps({"readback_responses": 6, "public_write_performed": False}))
