"""Continue the retained CC-179 midterm packet through its existing owner."""
from pathlib import Path
import json, os, sys, faulthandler
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.native_publication_latency_v1 import adopt_approved_text_speed_policy
from live_contentops.contentops_editorial_desk_v1 import record_native_article_review,read_reviews
from live_contentops.native_desktop_publication_v1 import prepare_native_publication
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
root=Path(__file__).resolve().parent
run="cc107-midterm-preview-20261103-v1"
store=ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3",auto_migrate=False)
with (root/"midterm-continuation-stack.txt").open("w") as stack:
 faulthandler.dump_traceback_later(90,file=stack,repeat=False)
 try:
  with newsroom_lease(store):
   basis=adopt_approved_text_speed_policy(store,run_id=run)
   row=store.get_outbox_message("cc-editorial-final-"+sha256_of(run)); result=json.loads(row["payload"])
   old=[r for r in read_reviews(store) if r["work_item_id"]==row["work_item_id"] and r["reviewer_ref"]=="NATIVE_DESKTOP_ARTICLE_REVIEW"][-1]
   review=record_native_article_review(store,run_id=run,article_identity=result["article_identity"],decision="KEEP",expected_review_id=old["review_id"],rationale="Current decision 53 policy applies to this event preview. Accepted native MAX text and all social prose are exactly unchanged; sources match its frozen writer request and lawful media credits remain bound. Record one automated load/dimension check and preserve the first approval clock, canonical and original plan. No new factual or rendered-inspection claim.")
   (root/"midterm-current-review.json").write_text(json.dumps({"policy_application":basis,"review":review},indent=2)+"\n")
   binding=json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual")/run/"binding.json").read_bytes())
   packet=prepare_native_publication(store,binding)
   (root/"midterm-reprepared.json").write_text(json.dumps(packet,indent=2)+"\n")
   print(json.dumps({"review_id":review["review_id"],"plan_hash":packet["plan_hash"],"text_approved_at_utc":review["text_approved_at_utc"],"public_write_performed":False}))
 except Exception as exc:
  (root/"midterm-prepare-cause.json").write_text(json.dumps({"error_class":type(exc).__name__,"cause":str(exc),"public_write_performed":False},indent=2)+"\n")
  raise
 finally:faulthandler.cancel_dump_traceback_later()
