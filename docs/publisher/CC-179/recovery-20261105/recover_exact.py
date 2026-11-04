"""One leased exact-object observation through the installed Publisher owners."""
from pathlib import Path
import json
import os
import sys
from uuid import uuid4

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from scripts.run_native_desktop_editorial import _bound_store
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease

here = Path(__file__).resolve().parent
command, run, target = sys.argv[1:4]
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual")
                      / run / "binding.json").read_bytes())
store = _bound_store(binding, "publication-status")
owner = "cc179-exact-readback-" + uuid4().hex
with newsroom_lease(store):
    lease = store.acquire_lease("internal:native-editorial:" + run, owner, ttl_seconds=900)
    try:
        native = NativeReviewedPublication(store, binding,
            native_invocation_id=os.environ["CODEX_THREAD_ID"],
            rollout=json.loads((LIVE / "config/native_desktop_rollout_v1.json").read_bytes()))
        native._authorize_and_bind()
        if command in {"readback", "readback-dispatch"}:
            originals = [d for d in store.get_dispatches_for_work_item(run) if d["platform"] == target]
            if command == "readback-dispatch":
                dispatch = store.get_platform_dispatch(target)
                assert store.get_outbox_message(dispatch["message_id"])["work_item_id"] == run
            else:
                original = next(d for d in originals if not json.loads(
                    store.get_outbox_message(d["message_id"])["payload"]).get("repost_of_dispatch_id"))
                dispatch = native.coordinator.effective_dispatch(original, store.get_dispatches_for_work_item(run))
            result = native.coordinator.readback_existing_dispatch(dispatch["dispatch_id"])
        elif command in {"begin", "submit"}:
            response = json.loads(Path(sys.argv[4]).read_bytes()) if command == "submit" else None
            result = native.tool(command, request_hash=target, response=response)
        else:
            raise ValueError("EXACT_READBACK_BEGIN_OR_SUBMIT_REQUIRED")
        pending = [p for p in native.executor.pending() if p["request"].get("action") == "READBACK"]
        out = {"coordinator_result": result, "pending_requests": pending,
               "live_module": str(Path(sys.modules[NativeReviewedPublication.__module__].__file__)),
               "native_invocation_id": os.environ["CODEX_THREAD_ID"]}
        path = here / (run + "-" + command + "-" + target + ".json")
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"artifact": str(path),
                          "result": {k: v for k, v in result.items()
                                     if k in {"dispatch_id", "reconciliation_status", "publish_called",
                                              "request_sha256", "tool_return_sha256", "classification"}},
                          "pending": [{"hash": p["request"]["request_sha256"],
                                       "destination": p["request"]["destination"],
                                       "public_object_id": p["request"].get("public_object_id"),
                                       "public_object_url": p["request"].get("public_object_url")}
                                      for p in pending]}))
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
