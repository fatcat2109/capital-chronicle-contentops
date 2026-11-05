"""Read one existing dispatch through the bound sole coordinator, without retrying it."""
import json
from pathlib import Path
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

ROOT = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-b")
binding = json.loads((RUN / "binding.json").read_bytes())
rollout = json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="/root", rollout=rollout)
plan, _ = operation.validate()
operation._authorize_and_bind()
destination = sys.argv[1]
assert destination in {"linkedin", "threads", "discord"}
dispatch = operation.coordinator._ids(binding["run_id"], plan["plan_hash"], destination)["dispatch_id"]
try:
    result = operation.coordinator.readback_existing_dispatch(dispatch)
except NativeNeoInputRequired as pending:
    (ROOT / "pending-native-tool.json").write_text(json.dumps(pending.request, indent=2), encoding="utf-8")
    q = pending.request["request"]
    result = {"status": "NATIVE_NEO_TOOL_PENDING", "destination": q["destination"],
        "action": q["action"], "request_sha256": q["request_sha256"]}
(ROOT / (destination + "-exact-readback.json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result))
