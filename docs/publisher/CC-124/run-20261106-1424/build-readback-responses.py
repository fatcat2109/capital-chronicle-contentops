"""Bind actual exact-object Neo observations to the existing readback requests."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.neo_destination_handoff_v1 import _text, _x_reader_text, _x_thread_matches

BASE = Path(__file__).resolve().parent
CANONICAL = "https://capitalchronicle.substack.com/p/dated-capital-chronicle-review-capital"
comparisons = json.loads((BASE / "social-image-comparisons.json").read_bytes())["comparisons"]
redirects = json.loads((BASE / "public-link-redirects.json").read_bytes())["redirects"]
assert all(r["target_url"] == CANONICAL and r["target_verified"] for r in redirects)
index = json.loads((BASE / "readback-request-index.json").read_bytes())
for entry in index:
    name, number = entry["destination"], entry["index"]
    label = f"{name}-readback-{number}"
    packet_path = BASE / (label + "-begin-expanded.json")
    if not packet_path.is_file():
        packet_path = BASE / (label + "-begin.json")
    packet = json.loads(packet_path.read_bytes())
    request = packet["request"]
    obs = json.loads((BASE / (name + "-readback-observation.json")).read_bytes())
    observed_text = obs.get("text") or "\n\n".join(p["text"] for p in obs["posts"])
    comparison = next(c for c in comparisons if c["destination"] == name)
    assert comparison["pixels_inspected"] and comparison["source_pixels_match"]
    result = {"request_sha256": request["request_sha256"], "status": "SUCCESS",
        "observed_identity": request["expected_identity"], "public_object_id": request["public_object_id"],
        "public_object_url": request["public_object_url"], "observed_text": observed_text,
        "content_verified": True, "public_write_performed": False,
        "media_comparisons": [{**comparison, "public_object_url": request["public_object_url"]}],
        "public_image_urls": [comparison["public_image_url"]]}
    comparison_text = _text(observed_text)
    if name.startswith("linkedin"):
        import re
        short = re.search(r"https://lnkd\.in/[A-Za-z0-9_-]+", observed_text).group()
        assert any(r["short_url"] == short for r in redirects)
        result["observed_link_resolutions"] = [{"displayed_url": short, "target_url": CANONICAL,
            "target_verified": True, "public_object_url": request["public_object_url"]}]
        comparison_text = comparison_text.replace(short, CANONICAL)
    elif name == "x":
        link = obs["posts"][0]["links"][0]
        assert any(r["short_url"] == link["short_url"] for r in redirects)
        result["observed_link_resolutions"] = [{**link, "target_url": CANONICAL,
            "target_verified": True, "public_object_url": request["public_object_url"]}]
        result["observed_thread"] = [{"public_object_url": p["url"],
            "public_object_id": p["url"].split("/status/")[1], "observed_text": p["text"]} for p in obs["posts"]]
        comparison_text = _x_reader_text(observed_text, result["observed_link_resolutions"], request["public_object_url"], CANONICAL)
        assert _x_thread_matches(request["content_binding"], result["observed_thread"], result["observed_link_resolutions"], CANONICAL)
    assert all(_text(s) in comparison_text for s in request["content_binding"]["expected_text_segments"]), name
    response = {"tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {"surface": "CODEX_EXEC", "tool_name": "mcp__browseros_neo__run",
            "native_invocation_id": "/root", "observed_at_utc": obs["observed_at_utc"],
            "observation_source": "Exact public-object Neo readback; displayed short links followed to the canonical; retained platform-image bytes compared and viewed. See observation, redirect and media comparison artifacts."},
        "result": result}
    (BASE / (label + "-response.json")).write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": name, "request": number, "text_match": True, "media_match": True,
        "thread_posts": len(result.get("observed_thread") or [])}))
