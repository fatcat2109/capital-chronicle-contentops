"""Read the one existing operation and render its exact private React review."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[3]))


def render(folder):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
    from live_contentops.native_desktop_editorial_v1 import final_visual_binding
    binding = json.loads(Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc107-midterm-preview-20261103-v1\binding.json").read_bytes())
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    with sqlite3.connect(Path(binding["store_path"]).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages WHERE work_item_id=? ORDER BY rowid", (work,))]
    final = next(json.loads(r["payload"]) for r in rows if r["message_id"] == "cc-editorial-final-" + sha256_of(binding["run_id"]))
    projection = report_workspace_projection(rows, review_records=[], dispatches=[], reconciliations=[], readiness=[])
    articles = [a for a in projection["native_edition"] if a["run_id"] == binding["run_id"]]
    assert len(articles) == 1
    view = {"native_edition": articles, "owner_edition": {
        "edition_id": binding["run_id"] + "-private-view", "title": "US midterms: frozen event preview",
        "operation_ids": [binding["run_id"]], "ready": 1, "missing": 0, "held": 0,
        "held_candidates": [], "preview_count": 8, "publication_authority": False}}
    target = ROOT / folder
    target.mkdir(exist_ok=True)
    for name, value in [("workspace.json", view), ("final-result.json", final),
                        ("targets.json", final_visual_binding(final, renders=None))]:
        (target / name).write_bytes(canonical_bytes(value))
    subprocess.run(["node", "ui/contentops_v5/scripts/render-report-workspace.mjs",
                    str(target / "workspace.json"), str(target / "index.html"), "--owner-review"],
                   cwd=ROOT.parents[3], check=True)


if __name__ == "__main__":
    render(sys.argv[1])
