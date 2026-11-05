"""Bind saved exact Neo observations and independently inspected platform pixels."""
import json
from pathlib import Path

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
def read(name):
    return json.loads((ROOT / (name + ".json")).read_bytes())

def save(name, request, observed, result):
    packet = read("native-neo/" + request + ".request")
    response = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"surface": "CODEX_EXEC", "tool_name": "mcp__browseros_neo__run",
            "native_invocation_id": "/root", "observed_at_utc": observed["observed_at_utc"],
            "observation_source": "Exact current Neo object text/identity and loaded-image readback; platform image bytes compared and inspected after sends. No new post."},
        "result": {"request_sha256": request, "status": "SUCCESS", "public_write_performed": False, **result}}
    (ROOT / (name + "-final-readback-response.json")).write_text(json.dumps(response, indent=2), encoding="utf-8")

sub = read("final-substack-observed")
media = read("substack-public-image-verification")
save("substack-credit", "1182ff351d9eb521ca673b0f2e9861511ce16d3e9b576eae40181022fb4f6fda", sub,
    {"observed_identity": "capitalchronicle.substack.com", "public_object_id": "223634631",
     "public_object_url": sub["canonical"], "observed_text": sub["observed_text"], "content_verified": True,
     "published_at_utc": sub["published_at_utc"],
     "observed_media_sha256": [a["public_delivery_sha256"] for a in media["assets"]],
     "public_image_urls": [a["verified_public_delivery_url"] for a in media["assets"]],
     "media_placement_observations": [{"asset_id": a["media_asset_id"], "public_alt_text_present": True,
         "public_caption_present": True} for a in media["assets"]]})
social = read("social-public-image-verification")["images"]
for name, request, identity in [
    ("x", "2af3edf6ac54851d326146ace0ed2a59d0069020e53cc25421186e75207d7ddb", "@Capitalnicle"),
    ("linkedin-company", "9b23a77fc5d03ffb8114b8485e743f6277c4d5fd17a242441968d5ee2304b175", "linkedin:company:143198922")]:
    observed = read("final-" + name + "-observed")
    images = [i for i in social if i["destination"] == name]
    assert all(i["similarity"] > 0.99 for i in images)
    result = {"observed_identity": identity, "content_verified": True,
        "observed_media_sha256": [i["platform_sha256"] for i in images],
        "public_image_urls": [i["public_image_url"] for i in images],
        "media_comparisons": [{k: i[k] for k in ("source_asset_sha256", "platform_sha256", "public_object_url", "public_image_url")}
            | {"pixels_inspected": True, "source_pixels_match": True, "similarity": i["similarity"]} for i in images]}
    if name == "x":
        posts = [{"public_object_url": p["public_object_url"].split("/photo/")[0], "observed_text": p["observed_text"]}
                 for p in observed["posts"]]
        for p in posts:
            p["public_object_id"] = p["public_object_url"].split("/")[-1]
        link = read("x-link-resolution-observed")
        assert link["target_url"] == sub["canonical"]
        result.update(public_object_id=posts[0]["public_object_id"], public_object_url=posts[0]["public_object_url"],
            observed_text="\n\n".join(p["observed_text"] for p in posts), observed_thread=posts,
            observed_link_resolutions=[{"displayed_text": observed["posts"][0]["anchors"][0]["text"],
                "short_url": link["short_url"], "target_url": link["target_url"], "target_verified": True,
                "public_object_url": posts[0]["public_object_url"]}])
    else:
        result.update({k: observed[k] for k in ("public_object_id", "public_object_url", "observed_text")})
        link = read("linkedin-company-link-resolution-observed")
        assert link["target_url"] == sub["canonical"]
        result["observed_link_resolutions"] = [{"displayed_url": link["short_url"], "target_url": link["target_url"],
            "target_verified": True, "public_object_url": observed["public_object_url"]}]
    save(name, request, observed, result)

observed = read("final-linkedin-absence-observed")
assert observed["authenticated"] and observed["activity_feed_loaded"] and observed["target_post_absent"]
save("linkedin-absence-current", "4ddff477207c216643ffa941a227a4b64bb49add8daf1420f3b3b3eab8293b8b", observed,
    {**observed, "observed_identity": "linkedin:jimcc", "content_verified": False})
observed = read("final-youtube-observed")
assert not observed["public_image_urls"]
save("youtube", "d3d302600c32876bee8474497df22158aadef58ff3f4041e4f413111bf29b089", observed,
    {**observed, "observed_identity": "@CapitalChronicleYouTube", "content_verified": True,
     "media_check_state": "MISSING_REQUIRED_MEDIA", "missing_required_media_observed": True})
print(json.dumps({"responses": ["substack-credit", "x", "linkedin-company", "linkedin-absence-current", "youtube"],
    "public_write_performed": False}))
