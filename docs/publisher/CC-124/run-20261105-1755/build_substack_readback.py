"""Build the exact native readback return from saved browser observations."""
import json
from pathlib import Path
ROOT=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
p=json.loads((ROOT/"substack-readback-content-observed.json").read_bytes())
m=json.loads((ROOT/"substack-public-image-verification.json").read_bytes())
assert m["status"]=="PASS"
response={"tool_request_sha256":"3933dcf8ca0c492447dc0044f8db0db2a1e90141df2829df28e67cc39af5feca",
"tool_observation":{"surface":"CODEX_EXEC","tool_name":"mcp__browseros_neo__run","native_invocation_id":"/root",
"observed_at_utc":p["observed_at_utc"],"observation_source":"Neo page 548 exact public article DOM text, loaded images and captions; production media owner independently verified all three original image SHA-256 values."},
"result":{"request_sha256":"387dabc28bcb1cb9338faab0a70c4e724ef0ecf8a3cd290ce3d7b3ba93da16bb",
"status":"SUCCESS","observed_identity":"capitalchronicle.substack.com","public_object_id":"223615409","public_object_url":p["canonical"],
"observed_text":p["observed_text"],"content_verified":True,
"observed_media_sha256":[a["public_delivery_sha256"] for a in m["assets"]],
"public_image_urls":[a["verified_public_delivery_url"] for a in m["assets"]],
"media_placement_observations":[{"asset_id":a["media_asset_id"],"public_alt_text_present":True,"public_caption_present":True} for a in m["assets"]],
"public_write_performed":False}}
(ROOT/"substack-readback-response.json").write_text(json.dumps(response,indent=2),encoding="utf-8")
print(json.dumps({"observed_at_utc":p["observed_at_utc"],"public_image_count":len(m["assets"])}))
