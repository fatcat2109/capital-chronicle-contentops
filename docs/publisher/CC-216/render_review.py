"""Render CC-216's actual saved newsroom results with the existing React reader."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.contentops_editorial_desk_v1 import read_reviews, record_owner_edition
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

BASE = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual")
OPERATIONS = ["cc216-" + name + "-background-20261105-v1" for name in ("nfp", "cpi", "ppi")]
OUTPUT = BASE / "cc216-background-review-20261105-v1"


def main():
    store = ContentOpsDurableStore(
        "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3", auto_migrate=False)
    edition = record_owner_edition(store, edition_id="cc216-backgrounds-20261105-v1",
        title="NFP, CPI and PPI preview backgrounds", operation_ids=OPERATIONS)
    rows = []
    for operation in OPERATIONS:
        rows.extend(store.list_outbox_messages(work_item_id="cc-opportunity-" + sha256_of(operation)))
    rows.append({"destination": "internal:native-owner-edition", "payload": json.dumps(edition)})
    projection = report_workspace_projection(rows, review_records=read_reviews(store))
    assert {a["run_id"] for a in projection["native_edition"]} <= set(OPERATIONS)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    projection_path = OUTPUT / "workspace.json"
    projection_path.write_text(json.dumps(projection, ensure_ascii=False), encoding="utf-8")
    context_path = OUTPUT / "context.json"
    context_path.write_text(json.dumps({"captured_at_utc": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    html_path = OUTPUT / "preview.html"
    subprocess.run(["node", "ui/contentops_v5/scripts/render-report-workspace.mjs", str(projection_path),
        str(html_path), "--owner-review", "--context", str(context_path)], check=True)
    summary = {"html_path": str(html_path), "html_sha256": sha256(html_path.read_bytes()).hexdigest(),
        "articles": [{"run_id": a["run_id"], "article_identity": a["article_identity"],
            "title": a["article"]["title"], "previews": len(a["previews"])} for a in projection["native_edition"]],
        "publication_performed": False, "projection_from_existing_live_store": True}
    (OUTPUT / "render-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
