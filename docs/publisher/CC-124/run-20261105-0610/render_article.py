"""Render this saved article and native packages with the existing reader."""
import json
from pathlib import Path
import subprocess
import sys
from hashlib import sha256
sys.path.insert(0,r"A:\Capital Chronicle\ContentOps")
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.contentops_editorial_desk_v1 import record_owner_edition,read_reviews
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
root=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a")
store=ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3",auto_migrate=False)
edition=record_owner_edition(store,edition_id="cc124-september-ppi-20261105",title="September producer-price retrospective",operation_ids=[root.name])
rows=store.list_outbox_messages(work_item_id="cc-opportunity-"+sha256_of(root.name))
rows.append({"destination":"internal:native-owner-edition","payload":json.dumps(edition)})
data=report_workspace_projection(rows,review_records=read_reviews(store))
p=root/"workspace.json";p.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
html=root/"preview.html"
r=subprocess.run(["node","ui/contentops_v5/scripts/render-report-workspace.mjs",str(p),str(html),"--owner-review"],cwd=r"A:\Capital Chronicle\ContentOps",capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stderr[:1500])
print(json.dumps({"html_path":str(html),"html_sha256":sha256(html.read_bytes()).hexdigest(),"articles":[{"id":a.get("article_identity"),"title":a["article"]["title"],"previews":len(a["previews"])} for a in data["native_edition"]],"public_write_performed":False}))
