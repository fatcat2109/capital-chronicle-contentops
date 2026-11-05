"""Ask the existing native review owner for this exact dated LinkedIn recovery."""
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, request_final_visual_review, DesktopInputRequired
from live_contentops.native_finished_publication_v1 import newsroom_lease

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
binding = json.loads((RUN / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=RUN, owner_manual_validation=False)
recovery = json.loads((RUN / "linkedin-recovery/distribution-recovery.json").read_bytes())
renders = json.loads((RUN / "linkedin-recovery/render-manifest.json").read_bytes())["renders"]
with newsroom_lease(store):
    try:
        request_final_visual_review(turn, renders=renders, distribution_recovery=recovery)
    except DesktopInputRequired as pending:
        packet = pending.request
        (HERE / "linkedin-recovery-review-request.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
        print(json.dumps({k: packet[k] for k in ("stage", "request_sha256", "request_path")}))
