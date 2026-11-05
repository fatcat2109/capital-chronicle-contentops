"""Refresh this article's exact dispatches with the existing read-only owner API."""
from pathlib import Path
import argparse
import json
import sys
from uuid import uuid4

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

ROOT = Path(__file__).resolve().parent
BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-c\binding.json")
parser = argparse.ArgumentParser()
parser.add_argument("label")
parser.add_argument("--refresh-absence", action="store_true")
args = parser.parse_args()
assert args.label.replace("-", "").isalnum()
binding = json.loads(BINDING.read_bytes())
assert binding["run_id"] == "cc124-next-article-20261105-c"
rollout = json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
publication = NativeReviewedPublication(store, binding,
    native_invocation_id="01a1a9d5-9a22-73a1-ab8d-6c0e1e84c9ee", rollout=rollout)
owner = "native-desktop-" + uuid4().hex
outcomes = []
with newsroom_lease(store):
    lease = store.acquire_lease("internal:native-editorial:" + binding["run_id"], owner, ttl_seconds=900)
    try:
        plan, _ = publication.validate()
        publication._authorize_and_bind()
        for destination in ("linkedin", "linkedin_company", "x", "youtube"):
            dispatch_id = publication.coordinator._ids(binding["run_id"], plan["plan_hash"], destination)["dispatch_id"]
            dispatch = store.get_platform_dispatch(dispatch_id)
            if dispatch and dispatch["status"] == "RECONCILED_ABSENT_SAFE_TO_RETRY" and not args.refresh_absence:
                outcomes.append({"destination": destination, "dispatch_id": dispatch_id,
                    "reconciliation_status": dispatch["status"], "publish_called": False,
                    "public_write_performed": False})
                continue
            try:
                result = publication.coordinator.readback_existing_dispatch(dispatch_id)
            except NativeNeoInputRequired as pending:
                result = {"destination": destination, "status": "NATIVE_NEO_TOOL_PENDING",
                    "native_tool_request": pending.request, "publish_called": False,
                    "public_write_performed": False}
            outcomes.append(result)
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
projection = publication.projection()
result = {"operation_id": binding["run_id"], "outcomes": outcomes,
    "publication": projection, "public_write_performed": False}
(ROOT / (args.label + ".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"outcomes": [{k: r.get(k) for k in ("destination", "status", "reconciliation_status")}
    for r in outcomes], "state": projection["state"], "unknown_write_count": projection["unknown_write_count"],
    "pending": [{"destination": p["request"]["destination"], "hash": p["request"]["request_sha256"],
        "tool_request_sha256": p.get("tool_request_sha256")} for p in projection["pending_requests"]]}))
