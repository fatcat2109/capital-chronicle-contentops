"""One bounded continuation of the existing coordinator's exact CPI edit."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired

root = Path(__file__).resolve().parent
reference = json.loads((root / "native/final-review-reference.json").read_bytes())
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
coordinator, executor = bind_native_neo_coordinator(store, operation_id="cc124-prepare-20261103-a",
    output_dir=r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-prepare-20261103-a\native-neo",
    native_invocation_id="/root", allow_publish=True)
try:
    value = coordinator.amend_reader_presentation("dispatch_61e1c3551501afee92efad2c69c2b1d1", review_reference=reference)
except NativeNeoInputRequired:
    value = {"classification": "NATIVE_NEO_INPUT_REQUIRED", "pending_requests": executor.pending()}
if len(sys.argv) != 2:
    raise ValueError("EXACT_RESULT_PATH_REQUIRED")
path = Path(sys.argv[1]).resolve()
if root.resolve() not in path.parents:
    raise ValueError("ITEM_EVIDENCE_PATH_REQUIRED")
path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print({"status": value.get("status") or value.get("classification"), "new_post_calls": value.get("new_post_calls"),
    "pending": [{"action": p["request"]["action"], "hash": p["request"]["request_sha256"]}
        for p in value.get("pending_requests", [])]})
