"""Ask the sole coordinator to restore this exact post's approved photo link."""
import json
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
binding = json.loads((ROOT / "binding.json").read_bytes())
rollout = json.loads(Path(r"A:\Capital Chronicle\ContentOps\config\native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
publication = NativeReviewedPublication(store, binding, native_invocation_id="/root", rollout=rollout)
owner = "native-desktop-" + uuid4().hex
with newsroom_lease(store):
    lease = store.acquire_lease("internal:native-editorial:" + binding["run_id"], owner, ttl_seconds=900)
    try:
        publication.validate()
        publication._authorize_and_bind()
        try:
            result = publication.coordinator.restore_approved_presentation("dispatch_25229cd3d5e4de79c277b7d4db8065d8")
        except NativeNeoInputRequired as pending:
            result = {"pending_request": pending.request}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
(ROOT / "credit-restore-current.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
request = result.get("pending_request", {})
print(json.dumps({"action": request.get("request", {}).get("action"),
    "request_sha256": request.get("request", {}).get("request_sha256"),
    "tool_request_sha256": request.get("tool_request_sha256"), "new_post_calls": result.get("new_post_calls")}))
