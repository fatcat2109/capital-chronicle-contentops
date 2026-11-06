"""Capture bounded acceptance evidence from the live store, with no external write."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE
BASE=Path(__file__).resolve().parent
WORK="cc323-midterm-lesson-20261106-v1"
store=ContentOpsDurableStore(PRODUCTION_STORE,auto_migrate=False)
packet=json.loads((BASE/"publication-resume-07-expanded.json").read_text(encoding="utf-8"))
publication=packet["publication"]
assert publication["state"]=="RECONCILED"
assert not publication["pending_requests"] and publication["unknown_write_count"]==0
rows=[]
with store.get_read_only_connection() as conn:
    records=conn.execute("SELECT d.dispatch_id,d.platform,d.status,d.public_object_id,d.public_object_url "
        "FROM platform_dispatches d JOIN outbox_messages m ON d.message_id=m.message_id "
        "WHERE m.work_item_id=? ORDER BY d.platform",(WORK,)).fetchall()
    for record in records:
        item=dict(record)
        readbacks=[]
        for r in conn.execute("SELECT read_at,readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at",(item["dispatch_id"],)):
            observed=json.loads(r["readback_data"])
            rb=observed.get("readback") or observed
            readbacks.append({"read_at_utc":r["read_at"],**{k:rb[k] for k in ["verified","source_status","identity_match",
                "meaningful_media_visible","observed_public_object_id","observed_public_object_url","content_binding_checks"] if k in rb}})
        item["readbacks"]=readbacks
        assert item["status"]=="DISPATCH_CONFIRMED" and readbacks
        assert readbacks[-1].get("verified") is True, item["platform"]
        rows.append(item)
assert len(rows)==10
result={"observed_at_utc":datetime.now(timezone.utc).isoformat(),"operation_id":WORK,
    "state":publication["state"],"canonical_url":publication["canonical_url"],
    "unknown_write_count":0,"pending_requests":[],"confirmed_destinations":rows,
    "source_trace":"source-claim-trace.json","bar_direction_check":"bar-check.json",
    "email_digest_consumer":"digest-live-consumer.json","telegram_public_readback":"telegram-public-readback.json",
    "top_level_launch":"top-level-launch.json","editorial_roles":"editorial-execution.json",
    "clock_correction":{"supersedes":"substack-publish-response.json: result.step_clocks.draft_ready_utc",
        "recorded_unverified_value":"2026-11-06T04:17:01Z","verified_draft_ready_utc":None,
        "reason":"The exact draft-ready clock was not retained as an observation. Do not use the prior value as measured timing.",
        "text_approved_utc":"2026-11-06T04:14:34.467820+00:00","canonical_published_utc":"2026-11-06T04:25:26.791Z",
        "latest_observed_send_click_utc":"2026-11-06T04:46:16.366Z",
        "all_channels_within_15_minutes":False},
    "site_published":False,"schedule_changed":False}
(BASE/"live-acceptance.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"state":result["state"],"verified_destinations":len(rows),
    "destinations":[r["platform"] for r in rows],"email_digest":"Wired to existing 19:00 GMT+7 consumer; email not yet sent."}))
