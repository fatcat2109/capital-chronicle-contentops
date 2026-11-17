"""Ask the sole coordinator to observe CC-425's existing Substack dispatch only."""
from datetime import datetime, timezone
import faulthandler
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path.cwd()))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication

root = Path(__file__).resolve().parent
label = sys.argv[1] if len(sys.argv) > 1 else "exact-readback"
binding = json.loads(Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc425-cpi-reaction-history-20261111-v1\binding.json").read_bytes())
with (root / (label + ".stderr.txt")).open("w", encoding="utf-8") as err:
    faulthandler.dump_traceback_later(90, repeat=False, file=err)
    try:
        store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
        operation = NativeReviewedPublication(store, binding,
            rollout=json.loads(Path("config/native_desktop_rollout_v1.json").read_bytes()),
            native_invocation_id=os.environ["CODEX_THREAD_ID"])
        operation._authorize_and_bind()
        result = operation.coordinator.readback_existing_dispatch("dispatch_873dddf89422b103efe92b1b5f469f1c")
        result["pending_requests"] = operation.executor.pending(work_item_id=binding["run_id"])
    except Exception as exc:
        traceback.print_exc(file=err)
        result = {"error": type(exc).__name__, "detail": str(exc)}
    faulthandler.cancel_dump_traceback_later()
(root / (label + ".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
(root / (label + "-end.json")).write_text(json.dumps({"pid": os.getpid(),
    "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    **{k:v for k,v in result.items() if k in {"error", "detail", "reconciliation_status", "public_write_performed"}}}, indent=2), encoding="utf-8")
