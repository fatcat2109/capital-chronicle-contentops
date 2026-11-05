"""Render this one retained article with the installed React preview owner."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import final_visual_binding, native_artifact_key, NativeDesktopTurn, build_dated_distribution_recovery, dated_distribution_recovery_view

RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
binding = json.loads((RUN / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=RUN, owner_manual_validation=False)
rows = store.list_outbox_messages(work_item_id=turn.work)
workspace = report_workspace_projection(rows)
articles = [a for a in workspace["native_edition"] if a["run_id"] == binding["run_id"] and a.get("article")]
assert len(articles) == 1
result = json.loads(store.get_outbox_message(native_artifact_key(store, binding["run_id"], "cc-editorial-final-"))["payload"])
recovery = build_dated_distribution_recovery(store, run_id=binding['run_id'], owner_authority_ref='human:BACKLOG_CC124_JIM_DECISIONS_39_88_IN_FLIGHT_DISTRIBUTION', destinations=['linkedin'])
result = dated_distribution_recovery_view(store, run_id=binding['run_id'], result=result, recovery=recovery)
articles[0]['previews'] = result['previews']
targets = final_visual_binding(result, renders=None, destinations={'linkedin'})
out = RUN / (sys.argv[1] if len(sys.argv) > 1 else "linkedin-recovery")
out.mkdir(exist_ok=True)
(out / "distribution-recovery.json").write_text(json.dumps(recovery, indent=2), encoding="utf-8")
data = {"native_edition": articles, "owner_edition": {"edition_id": binding["run_id"],
    "title": "Bitcoin and the rate backdrop", "operation_ids": [binding["run_id"]], "ready": 1,
    "missing": 0, "held": 0, "held_candidates": [], "preview_count": 8, "publication_authority": False}}
(out / "workspace.json").write_text(json.dumps(data), encoding="utf-8")
(out / "targets.json").write_text(json.dumps(targets, indent=2) + "\n", encoding="utf-8")
process = subprocess.run(["node", "ui/contentops_v5/scripts/render-report-workspace.mjs",
    str(out / "workspace.json"), str(out / "review-desktop.html"), "--owner-review"],
    cwd=OPERATING, capture_output=True, check=True)
desktop = (out / "review-desktop.html").read_text(encoding="utf-8")
# Apply the owner's exact mobile presentation rules to an explicit 414px canvas.
# Neo captures actual rendered pixels; the manifest records the distinct source.
mobile_css = """<style>html,body{width:414px;min-width:414px;max-width:414px}body{font-size:16px}main{width:414px;padding:16px 12px 50px;margin:0}h1{font-size:1.9rem}h2{font-size:1.55rem}.report-copy{padding:20px 17px}.reading-controls{padding:16px}button{font-size:.85rem;padding:9px}.story-step span{font-size:.8rem}.release-decision{padding:16px}figure>img{max-height:400px}</style>"""
(out / "review-mobile.html").write_text(desktop.replace("</head>", mobile_css + "</head>"), encoding="utf-8")
print(json.dumps({"article_identity": targets["article_identity"], "variants": len(targets["variants"]),
    "desktop_html": str(out / "review-desktop.html"), "mobile_html": str(out / "review-mobile.html"),
    "html_bytes": len(desktop.encode()), "public_write_performed": False}))
