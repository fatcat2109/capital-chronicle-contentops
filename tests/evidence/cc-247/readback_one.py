"""Reconcile one exact existing CC-247 object through the sole coordinator; no send."""
from pathlib import Path
import json, os, sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.run_native_desktop_editorial import _bound_store
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease

here = Path(__file__).resolve().parent
prefix, destination = sys.argv[1:3]
run = "cc124-prepare-20261103-a" if prefix == "cpi" else "cc124-next-article-20261103-b"
binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json").read_bytes())
store = _bound_store(binding, "publication-status")
owner = "cc247-readback-" + uuid4().hex
with newsroom_lease(store):
    lease = store.acquire_lease("internal:native-editorial:" + run, owner, ttl_seconds=900)
    try:
        native = NativeReviewedPublication(store, binding, native_invocation_id=os.environ["CODEX_THREAD_ID"],
            rollout=json.loads((here.parents[2] / "config/native_desktop_rollout_v1.json").read_bytes()))
        plan, _ = native.validate()
        native._authorize_and_bind()
        co = native.coordinator
        original = store.get_platform_dispatch(co._ids(run, plan["plan_hash"], destination)["dispatch_id"])
        effective = (store.get_platform_dispatch(sys.argv[3]) if len(sys.argv) > 3
            else co.effective_dispatch(original, store.get_dispatches_for_work_item(run)))
        assert effective["platform"] == destination
        assert store.get_outbox_message(effective["message_id"])["work_item_id"] == run
        outcome = co.readback_existing_dispatch(effective["dispatch_id"])
        pending = [p for p in native.executor.pending() if p["request"].get("destination") == destination
            and p["request"].get("action") == "READBACK"]
        result = {"coordinator_result": outcome, "pending_requests": pending}
        (here / (prefix + "-" + destination + "-exact-readback.json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"outcome": outcome, "pending": [p["request"]["request_sha256"] for p in pending]}))
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
