"""Invoke the existing coordinator for this run's exact, reviewed dispatch only."""
import json
from pathlib import Path
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

ROOT = Path(__file__).resolve().parent
BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a\binding.json")
binding = json.loads(BINDING.read_bytes())
assert binding["run_id"] == "cc124-next-article-20261105-a"
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="/root",
    rollout=json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes()))
plan, _ = operation.validate()
operation._authorize_and_bind()
destination = sys.argv[1]
assert destination in {"linkedin", "x"}
coordinator = operation.coordinator
ids = coordinator._ids(binding["run_id"], plan["plan_hash"], destination)
dispatch = store.get_platform_dispatch(ids["dispatch_id"])
canonical = coordinator._confirmed_canonical_url_for_work_item(binding["run_id"], plan_hash=plan["plan_hash"])
assert canonical == "https://capitalchronicle.substack.com/p/september-ppi-energy-drove-the-goods"
try:
    if destination == "linkedin":
        # The ordinary resume already spent its one API retry at 01:02:17Z.
        # Observe that exact dispatch after the ten-minute interval; never retry it here.
        outcome = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    else:
        outcome = coordinator.complete_derivative_after_transport_correction(
            ids["dispatch_id"], correction_id="cc124-20261105-complete-missing-retrospective-notice")
except NativeNeoInputRequired as pending:
    outcome = {"status": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
result = {"destination": destination, "dispatch_id": ids["dispatch_id"],
    "coordinator_result": outcome, "publication": operation.projection()}
(ROOT / (destination + "-bounded-recovery.json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
packet = outcome.get("native_tool_request")
print(json.dumps({"status": outcome.get("status"), "destination": destination,
    "request_sha256": packet["request"]["request_sha256"] if packet else None,
    "public_write_performed": outcome.get("public_write_performed"),
    "publish_called": outcome.get("publish_called")}))
