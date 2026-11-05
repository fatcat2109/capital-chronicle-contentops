"""Read exact observed platform image objects through the existing media owner."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,r"A:\Capital Chronicle\ContentOps")
from live_contentops.media_manifest_authority_v1 import read_public_image_bytes, image_metadata_from_bytes, visual_similarity_to_local_file
ROOT=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
OUT=ROOT/"media_readback"
OUT.mkdir(exist_ok=True)
source=ROOT/"media_assets/cc124-treasury-latest-daily-change-20261104.png"
rows=[]
for name in ("x","linkedin-company","youtube"):
 p=json.loads((ROOT/(name+"-composed-response.json")).read_bytes())["composed"]["readback"]
 url=p["public_image_urls"][0]
 value=read_public_image_bytes(url)
 path=OUT/(name+"-public.png")
 path.write_bytes(value)
 rows.append({"destination":name,"public_object_url":p["public_object_url"],"public_image_url":url,
     "path":str(path),"platform_sha256":hashlib.sha256(value).hexdigest(),"size_bytes":len(value),
     "source_asset_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
     "similarity":visual_similarity_to_local_file(value,source),**image_metadata_from_bytes(value)})
report={"observed_at_utc":datetime.now(timezone.utc).isoformat(),"images":rows}
(ROOT/"social-public-image-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
