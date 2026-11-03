"""One readback through the existing owner; never dispatch or retry."""
from pathlib import Path
import json, os, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

root = Path(__file__).resolve().parent
run, dispatch = sys.argv[1:]
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json").read_bytes())
rollout = json.loads(Path("config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
with newsroom_lease(store):
    owner = NativeReviewedPublication(store, binding, native_invocation_id=os.environ["CODEX_THREAD_ID"], rollout=rollout)
    owner.validate()
    owner._authorize_and_bind()
    try:
        result = owner.coordinator.readback_existing_dispatch(dispatch)
    except NativeNeoInputRequired as pending:
        result = {"status": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request, "publish_called": False}
    (root / (dispatch + "-readback.json")).write_text(json.dumps(result, indent=2) + "\n")
    request = result.get("native_tool_request", {}).get("request", {})
    print(json.dumps({k:v for k,v in result.items() if k != "native_tool_request"} | {
        "request_sha256": request.get("request_sha256"), "action": request.get("action"), "destination": request.get("destination")}))
