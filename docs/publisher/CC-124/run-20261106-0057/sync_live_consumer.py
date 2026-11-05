"""Project the already-confirmed canonical through the existing publication owner."""
import json
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
binding = json.loads((RUN / "binding.json").read_bytes())
rollout = json.loads(Path(r"A:\Capital Chronicle\ContentOps\config\native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
publication = NativeReviewedPublication(store, binding, native_invocation_id="/root", rollout=rollout)
owner = "cc124-confirmed-feed-" + uuid4().hex
lease = store.acquire_lease("internal:native-editorial:" + binding["run_id"], owner, ttl_seconds=60)
try:
    plan, _ = publication.validate()
    publication._authorize_and_bind()
    canonical = next(d for d in publication.projection()["destinations"] if d["destination"] == "substack")
    assert canonical["status"] == "DISPATCH_CONFIRMED" and canonical["reconciliation_status"] == "RECONCILED_CONFIRMED"
    result = publication.coordinator.sync_published_content(binding["run_id"])
finally:
    store.release_lease(lease["lease_id"], owner, lease["fencing_token"])
(HERE / "canonical-consumer-sync.json").write_text(json.dumps({"result": result, "public_write_performed": False}, indent=2), encoding="utf-8")
print(json.dumps({"result": result, "public_write_performed": False}))
