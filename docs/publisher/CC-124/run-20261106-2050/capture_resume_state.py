"""Read exact operation and live counts after the decision-93 amendment."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
from live_contentops.native_finished_publication_v1 import confirmed_canonicals
from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
from live_contentops.published_content_v1 import DEFAULT_FEED, read_records

RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-arrival-review-20261106-v1")
binding = json.loads((RUN / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
now = datetime.now(timezone.utc)
turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
selection = turn._get("select", "response")
request = turn.frozen_request("write")
assert selection and request and not turn._get("write", "response")
assert request["request_sha256"] == sha256_of({k:v for k,v in request.items() if k != "request_sha256"})
assert not (RUN / "desktop_response_write.json").exists()
day_id = newsroom_production_day_id(now)
published = [p for p in confirmed_canonicals(store)
    if newsroom_production_day_id(p.get("published_at_utc") or p["first_readback_utc"]) == day_id]
identities = {p["article_identity"] for p in published}
assert len(identities) >= 2
with store.get_read_only_connection() as conn:
    dispatches = [dict(r) for r in conn.execute(
        "SELECT d.dispatch_id,d.platform,d.status,d.public_object_id,d.public_object_url "
        "FROM platform_dispatches d JOIN outbox_messages m ON d.message_id=m.message_id "
        "WHERE m.work_item_id=?", (binding["run_id"],))]
assert not dispatches
feed = [r for r in read_records(DEFAULT_FEED) if newsroom_production_day_id(r["published_at_utc"]) == day_id]
record_path = RUN.parent.parent / day_id / "newsroom_production_day_v1.json"
day = json.loads(record_path.read_bytes())
measured = day["native_volume_measurement"]["distinct_canonical_items_published"]
assert measured == len(identities)
live_sources = RetainedSourceResearch(Path(r"A:\Capital Chronicle\ContentOps\docs\publisher\CC-124\run-20261106-2050\source"))
assert not live_sources.gaps and len(live_sources.records) == 3
next_due = datetime.fromisoformat("2026-11-06T13:50:00+00:00") + timedelta(hours=6)
continuation = {
    "item": "CC-124", "observed_at_utc": now.isoformat(),
    "operation_id": binding["run_id"], "binding_path": str(RUN / "binding.json"),
    "binding_sha256": sha256((RUN / "binding.json").read_bytes()).hexdigest(),
    "run_result": "JIM_DECISION_93_DAILY_ARTICLE_CAP_REACHED",
    "decision_source": r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\JIM_DECISIONS_20261030.md#93",
    "decision_known_on_resume": True, "current_policy_daily_cap": 2, "current_policy_cadence_minutes": 360,
    "policy_choice": "Apply the newly recorded publication cap at this resumed entry; preserve the original operation and accepted roles. No additional public article today.",
    "production_day_id": day_id, "confirmed_distinct_articles": len(identities),
    "production_record": str(record_path), "production_record_sha256": sha256(record_path.read_bytes()).hexdigest(),
    "saved_record_count": measured,
    "confirmed_canonicals": [{k:(v.isoformat() if isinstance(v,datetime) else v) for k,v in p.items()} for p in published],
    "published_feed": [{k:r.get(k) for k in ("content_id","title","published_at_utc")} for r in feed],
    "source_consumer": {"path": str(live_sources.root), "revision": live_sources.revision,
        "verified_records": list(live_sources.records), "gaps": live_sources.gaps},
    "accepted_selection_sha256": selection["request_sha256"],
    "pending_stage": "write", "pending_request_path": str(RUN / "desktop_request_write.json"),
    "pending_request_sha256": request["request_sha256"],
    "writer_invoked": False, "new_public_dispatches": dispatches, "public_write_performed": False,
    "article_completed": False, "new_publication_count": 0,
    "next_due_utc": next_due.isoformat(), "next_due_gmt7": "7 Nov 2026 02:50 GMT+7",
    "next_actor": "Codex Publisher",
    "next_action": "At the next eligible run, resume this exact operation. Recheck held Main facts and current policy. Before writing, attach the held official supporting data and Main's full scenarios through the existing selected-story context owner; prepare new data charts and use an unpublished lead image. No private probability, market response or performance is invented.",
    "test_runs_started": 0, "test_reason": "6 November 18:30-22:30 GMT+7 machine-load restriction",
    "schedules_changed": False, "chat_messages_sent": False, "native_desktop_control_used": False,
}
(HERE / "resume-state.json").write_text(json.dumps(continuation,indent=2)+"\n",encoding="utf-8",newline="\n")
(HERE / "pending-native-request.json").write_text(json.dumps(request,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"state":continuation["run_result"],"day":day_id,"confirmed":len(identities),
    "cap":2,"pending_stage":"write","pending_request_sha256":request["request_sha256"],"new_dispatches":len(dispatches),
    "source_records":len(live_sources.records),"next_due_gmt7":continuation["next_due_gmt7"]}))
