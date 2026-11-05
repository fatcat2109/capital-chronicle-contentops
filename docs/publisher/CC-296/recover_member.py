"""CC-296: invoke only the retained article's existing publication coordinator."""
import json
from pathlib import Path
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

ROOT = Path(__file__).resolve().parent
RUNS = {"ppi": "cc124-next-article-20261105-a", "next": "cc124-next-article-20261105-b"}
label, action = sys.argv[1:3]
run_id = RUNS[label]
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual")
    / run_id / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="cc296-publisher-exec-20261106",
    rollout=json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes()))
operation._authorize_and_bind()
coordinator = operation.coordinator
dispatches = [d for d in store.get_dispatches_for_work_item(run_id) if d["platform"] == "linkedin"]
assert len(dispatches) == 1
ids = {"dispatch_id": dispatches[0]["dispatch_id"]}
try:
    if action == "readback":
        result = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    elif action == "complete":
        result = coordinator.complete_derivative_after_transport_correction(ids["dispatch_id"],
            correction_id="cc296-pre-http-tls-recovery-v1")
    elif action == "begin":
        result = operation.tool("begin", request_hash=sys.argv[3])
    elif action == "submit":
        result = operation.tool("submit", request_hash=sys.argv[3],
            response=json.loads(Path(sys.argv[4]).read_bytes()))
    elif action == "status":
        result = {"dispatch": store.get_platform_dispatch(ids["dispatch_id"]),
            "publication": operation.projection()}
    else:
        raise ValueError("EXACT_CC296_ACTION_REQUIRED")
except NativeNeoInputRequired as pending:
    result = {"status": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
(ROOT / (label + "-" + action + ".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
packet = result.get("native_tool_request")
print(json.dumps({"run_id": run_id, "action": action, "status": result.get("status"),
    "reconciliation_status": result.get("reconciliation_status"),
    "publish_called": result.get("publish_called"),
    "request_sha256": packet["request"]["request_sha256"] if packet else None,
    "artifact": str(ROOT / (label + "-" + action + ".json"))}))
