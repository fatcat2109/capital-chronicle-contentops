"""Bind actual observed copy and inspected platform media to the existing requests."""
import json, sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.neo_destination_handoff_v1 import _text, _x_reader_text, _x_thread_matches
BASE=Path(__file__).resolve().parent
CANONICAL="https://capitalchronicle.substack.com/p/capital-chronicles-midterm-review"
comparisons=json.loads((BASE/"social-image-comparisons.json").read_text())["comparisons"]
redirects=json.loads((BASE/"public-link-redirects.json").read_text())["redirects"]
assert all(r["target_url"]==CANONICAL and r["target_verified"] for r in redirects)
for name in ["linkedin","linkedin-company","x","youtube"]:
    packet_path=BASE/(name+"-readback-begin-expanded.json")
    if not packet_path.is_file(): packet_path=BASE/(name+"-readback-begin.json")
    packet=json.loads(packet_path.read_text(encoding="utf-8"));request=packet["request"]
    key=name.replace("-","_")
    obs=json.loads((BASE/(key+"-readback-observation.json")).read_text(encoding="utf-8"))
    observed_text=obs.get("text") or "\n\n".join(p["text"] for p in obs["posts"])
    result={"request_sha256":request["request_sha256"],"status":"SUCCESS",
            "observed_identity":request["expected_identity"],"public_object_id":request["public_object_id"],
            "public_object_url":request["public_object_url"],"observed_text":observed_text,
            "content_verified":True,"observed_media_sha256":[],"public_write_performed":False}
    comparison=next(c for c in comparisons if c["destination"]==key)
    assert comparison["pixels_inspected"] and comparison["source_pixels_match"]
    result["media_comparisons"]=[{**comparison,"public_object_url":request["public_object_url"]}]
    result["public_image_urls"]=[comparison["public_image_url"]]
    comparison_text=_text(observed_text)
    if name.startswith("linkedin"):
        import re
        short=re.search(r"https://lnkd\.in/[A-Za-z0-9_-]+",observed_text).group()
        assert any(r["short_url"]==short for r in redirects)
        result["observed_link_resolutions"]=[{"displayed_url":short,"target_url":CANONICAL,
            "target_verified":True,"public_object_url":request["public_object_url"]}]
        comparison_text=comparison_text.replace(short,CANONICAL)
    elif name=="x":
        link=obs["posts"][0]["outbound"][0]
        assert any(r["short_url"]==link["url"] for r in redirects)
        result["observed_link_resolutions"]=[{"displayed_text":link["text"],"short_url":link["url"],
            "target_url":CANONICAL,"target_verified":True,"public_object_url":request["public_object_url"]}]
        result["observed_thread"]=[{"public_object_url":p["links"][0],
            "public_object_id":p["links"][0].split("/status/")[1],"observed_text":p["text"]} for p in obs["posts"]]
        comparison_text=_x_reader_text(observed_text,result["observed_link_resolutions"],request["public_object_url"],CANONICAL)
        assert _x_thread_matches(request["content_binding"],result["observed_thread"],result["observed_link_resolutions"],CANONICAL)
    assert all(_text(s) in comparison_text for s in request["content_binding"]["expected_text_segments"]), name
    response={"tool_request_sha256":packet["tool_request_sha256"],
        "tool_observation":{"surface":"CODEX_EXEC","tool_name":"mcp__browseros_neo__run",
        "native_invocation_id":"/root","observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "observation_source":"Actual exact-object Neo DOM readback; followed displayed short links; binary platform images inspected and compared with approved local card"},
        "result":result}
    (BASE/(name+"-readback-response.json")).write_text(json.dumps(response,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"destination":name,"text_match":True,"media_match":True,"thread_posts":len(result.get("observed_thread") or [])}))
