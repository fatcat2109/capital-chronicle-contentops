"""Compile the existing React review view and retain local desktop/mobile pixels."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
sys.path.insert(0, str(REPO))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, final_visual_binding, native_artifact_key
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

binding = json.loads((OP / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
row = store.get_outbox_message(native_artifact_key(store, binding["run_id"], "cc-editorial-final-"))
result = json.loads(row["payload"])
target = final_visual_binding(result, renders=None)
ROOT = OP / "render-review"
ROOT.mkdir(exist_ok=True)
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
with store.get_read_only_connection() as conn:
    works = (row["work_item_id"], binding["run_id"])
    rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages WHERE work_item_id IN (?,?) ORDER BY rowid", works)]
    reviews = [dict(r) for r in conn.execute("SELECT * FROM review_records WHERE work_item_id IN (?,?) ORDER BY rowid", works)]
data = report_workspace_projection(rows, review_records=reviews, dispatches=[], reconciliations=[], readiness=[])
articles = [a for a in data["native_edition"] if a["run_id"] == binding["run_id"]]
assert len(articles) == 1 and articles[0]["article_identity"] == result["article_identity"]
data = {"native_edition": articles, "owner_edition": {"edition_id": binding["run_id"],
    "title": "The dollar against euro and yen", "operation_ids": [binding["run_id"]], "ready": 1,
    "missing": 0, "held": 0, "held_candidates": [], "preview_count": 8, "publication_authority": False}}
workspace = ROOT / "workspace.json"
workspace.write_text(json.dumps(data, ensure_ascii=True), encoding="utf-8")  # runtime only; never commit encoded media
html = ROOT / "review.html"
done = subprocess.run(["node", str(LIVE / "ui/contentops_v5/scripts/render-report-workspace.mjs"),
                       str(workspace), str(html), "--owner-review"], cwd=LIVE, capture_output=True)
if done.returncode:
    raise RuntimeError(done.stderr.decode(errors="replace")[-2000:])


(ROOT / "targets.json").write_text(json.dumps(target, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"html_path":str(html),"targets":str(ROOT/"targets.json"),"variants":sorted(target["variants"])}))
