"""One explicit media-transport correction on the same confirmed-absent attempt."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease

root = Path(__file__).resolve().parent
binding = json.loads(Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-prepare-20261103-a\binding.json").read_bytes())
rollout = json.loads(Path("config/native_desktop_rollout_v1.json").read_bytes())
delivery = json.loads((root / "cpi-selected-delivery-bind-result.json").read_bytes())
if not delivery["manifest_bound"] or delivery["status"] != "PASS":
    raise ValueError("EXACT_REVIEWED_DELIVERY_MEDIA_REQUIRED")
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
with newsroom_lease(store):
    owner = NativeReviewedPublication(store, binding, rollout=rollout, native_invocation_id=os.environ["CODEX_THREAD_ID"])
    owner.validate()
    owner._authorize_and_bind()
    result = owner.coordinator.complete_derivative_after_transport_correction(
        "dispatch_d01bbafa38b1b14dba9ee60b7ef9f93b", correction_id="CC179_CPI_ACCEPTED_HISTORY_MEDIA_3ad21a45_20261104")
    (root / "cpi-instagram-explicit-correction.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
