"""Prepare exact inputs to the existing media-plan binder, without dispatch."""
import json
from pathlib import Path
from hashlib import sha256
import sys
sys.path.insert(0,r"A:\Capital Chronicle\ContentOps")
from live_contentops.rolling_x_grounded_article_media_builder_v1 import validate_source_value_chart
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo
root=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a")
request=json.loads((root/"desktop_request_media-plan.json").read_bytes())
response=json.loads((root/"desktop_response_media-plan.json").read_bytes())
assets=json.loads((root/"rendered-assets-reviewed.json").read_bytes())
sources=json.loads((root/"editorial_media_plan_required.json").read_bytes())["source_pack"]
assert request["request_sha256"]==response["request_sha256"]
for asset in assets:
    assert sha256(Path(asset["path"]).read_bytes()).hexdigest()==asset["sha256"]
    review=asset["visual_review"]
    assert review["asset_sha256"]==asset["sha256"] and review["pixels_inspected"] is True
    if asset["modality"]=="source_backed_chart":
        validate_source_value_chart(asset,sources)
    else:
        validate_contextual_photo(asset)
value={"plan":{"native_plan_run_id":root.name,"native_plan_stage":"media-plan",
    "native_plan_request_sha256":request["request_sha256"],"story_plan":response["output"]["story_plan"]},"assets":assets}
p=root/"media-plan-binding.json";p.write_text(json.dumps(value,indent=2),encoding="utf-8")
print(json.dumps({"response_path":str(p),"assets":len(assets),"all_source_and_pixel_checks":"PASS"}))
