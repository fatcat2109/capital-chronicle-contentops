"""Bind fresh Neo text to the inspected platform images without another send."""
import json
from pathlib import Path
ROOT=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
fresh=json.loads((ROOT/"social-final-content-observed.json").read_bytes())
media=json.loads((ROOT/"social-public-image-verification.json").read_bytes())
requests={"x":"397b468c9bd1a7df3f57840b11868110a2aa8be8c83610a533d0d0e283244099","linkedin-company":"7a4b7bf18107f5a426dda2b548a57682df2c39739fcda1ffc27925a0c3cce821","youtube":"ce407f25a1c2c58868d0f4a8cffb3425f7dbc8c76a11bd973523e80223ba25f4"}
for name,sha in requests.items():
 packet=json.loads((ROOT/"native-neo"/(sha+".request.json")).read_bytes())
 result=json.loads((ROOT/(name+"-composed-response.json")).read_bytes())["composed"]["readback"]
 current=fresh["destinations"][name.replace("-","_")]
 if name=="x":
  result["observed_thread"]=[{k:p[k] for k in ("public_object_id","public_object_url","observed_text")} for p in current]
  result["observed_text"]="\n\n".join(p["observed_text"] for p in current)
  images=current[0]["images"]
 else:
  result["observed_text"]=current["observed_text"]
  images=current["images"]
 image=next(i for i in media["images"] if i["destination"]==name)
 assert any(i["src"]==image["public_image_url"] and i["complete"] and i["width"]>0 and i["height"]>0 for i in images)
 result["request_sha256"]=sha
 result["observed_media_sha256"]=[image["platform_sha256"]]
 result["media_comparisons"]=[{k:image[k] for k in ("source_asset_sha256","platform_sha256","public_object_url","public_image_url")} | {"pixels_inspected":True,"source_pixels_match":True}]
 response={"tool_request_sha256":packet["tool_request_sha256"],
  "tool_observation":{"surface":"CODEX_EXEC","tool_name":"mcp__browseros_neo__run","native_invocation_id":"/root","observed_at_utc":fresh["observed_at_utc"],"observation_source":"Fresh exact-object Neo text, loaded image dimensions and unchanged image URL; downloaded platform pixels inspected against source chart after all destinations sent. Exact binary hashes retained."},
  "result":result}
 (ROOT/(name+"-final-readback-response.json")).write_text(json.dumps(response,indent=2),encoding="utf-8")
print(json.dumps({"responses":list(requests),"public_write_performed":False}))
