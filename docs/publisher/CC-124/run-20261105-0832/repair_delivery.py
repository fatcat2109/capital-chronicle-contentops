"""Use the existing coordinator's one exact, proven-absent transport correction."""
import json
from pathlib import Path
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication

ROOT = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-b")
binding = json.loads((RUN / "binding.json").read_bytes())
rollout = json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="/root", rollout=rollout)
operation.validate()
operation._authorize_and_bind()
dispatch = "dispatch_5d227c8c47a0f0608899d2778668c7df"
row = store.get_platform_dispatch(dispatch)
assert row and row["platform"] == "facebook_page" and not row.get("public_object_id")
result = operation.coordinator.complete_derivative_after_transport_correction(dispatch,
    correction_id="cc124-source-bound-card-delivery-6b83091e")
(ROOT / "facebook-transport-correction.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "publish_called", "public_object_url", "reconciliation_status") if k in result}))
