"""Stored outcomes reach the real post/coordinator seam; no live services."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import call_followups_v1 as f
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import tradingview_snapshot_v1 as tv
from test_plan_status_publication_cc306 import fake_host
from test_publication_coordinator_v1 import _coordinator, _set_mode

NOW = datetime(2026,11,14,2,tzinfo=timezone.utc)
START = NOW-timedelta(hours=2)
TERMS = {"market":"Gold","condition":"price trades into 110–112","direction":"bearish",
         "horizon":"14 Nov 03:00 ET","invalidation":"price moves above 120"}


def candidate(kind="AS_WRITTEN"):
    quote = posts.conditional_call_text(TERMS)
    return {"call_id":"stored-public-call","plan_id":"stored-plan","symbol":"XAUUSD",
        "source_kind":kind,"short_id":"a0380280","terms":TERMS,"quote":quote,"original_text":quote,
        "original_url":"https://t.me/CapitalChronicle/169","published_at_utc":START.isoformat(),
        "valid_until_utc":(START+timedelta(hours=6)).isoformat(),"zone_low":110,"zone_high":112,
        "reference_price":115,"resolution_level":90,"direction":"bearish",
        "invalidation":{"field":"high","level":120,"side":"above"},
        "destinations":["telegram","discord","x","substack_notes"]}


def bars():
    return [{"open_epoch":int((START+timedelta(minutes=15*i)).timestamp()),
             "open":115-i,"high":116-i,"low":111-i if i<6 else 89,"close":113-i,
             "source_sha256":"held-source"} for i in range(1,7)]


def register(store,key,row,status="PUBLISHED",destinations=("telegram","discord","threads")):
    row={"schema_version":posts.SCHEMA,"symbol":"XAUUSD",**row}
    store.create_work_item(story_id=key,work_item_id=key,title="Stored public call",target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=key,work_item_id=key,destination=posts.DESTINATION,
                                  payload=json.dumps(row),status=status)
    for d in destinations:
        identity=key+"-"+d
        store.register_outbox_message(message_id=identity,work_item_id=key,destination=d,payload="{}")
        store.register_platform_dispatch(dispatch_id=identity,message_id=identity,platform=d,
            status="DISPATCH_CONFIRMED",public_object_id="134",public_object_url="https://t.me/CapitalChronicle/134")
        store.register_reconciliation(reconciliation_id='reconciliation_'+identity,work_item_id=key,
                                      status='RECONCILED_CONFIRMED')


@pytest.fixture
def ready(tmp_path,monkeypatch):
    store,transport,coordinator = _coordinator(tmp_path)
    _set_mode(store,"AUTONOMOUS_DEFAULT")
    for key in (f.ZONE_CORRECTION,f.GOLD_CORRECTION):
        register(store,key,{"key":key,"text":"Correction."})
    record={"line":"Pinned call record: 1 hits, 5 stopped, 37 expiries; 43 results, 7 scored.",
            "counts":{"HIT":1,"STOPPED":5,"EXPIRED":37,"total":43,"scored":7},
            "url":"https://t.me/CapitalChronicle/134","observed_at_utc":NOW.isoformat(),"text_sha256":"stored"}
    monkeypatch.setattr(f,"observed_record",lambda *a,**k:record)
    monkeypatch.setattr(f,"article_candidates",lambda *a,**k:([],[]))
    return store,transport,coordinator,record


def asset(tmp_path):
    base=Path(__file__).parents[1]/"docs/publisher/CC-603"
    snap=json.loads((base/"original-gold-chart.json").read_bytes())
    snap["path"]=str(base/"media/gold-original.png")
    return tv.snapshot_asset("XAUUSD","Gold",snap,tmp_path/"media")


def test_stored_hit_and_expiry_reach_consumer_exactly_once(ready,tmp_path):
    store,transport,coordinator,record=ready
    hit=candidate()
    checked=f.check_path(hit,bars())
    assert checked["eligible"] and checked["entry_traded"]
    expiry=f.check_path({**hit,"resolution_level":70},bars())
    assert f.queue_followup(store,hit,expiry,record,now=NOW)["status"]=="NOT_ELIGIBLE"
    first=f.queue_followup(store,hit,checked,record,now=NOW)
    assert first["status"]=="QUEUED"
    assert f.queue_followup(store,hit,checked,record,now=NOW)["status"]=="EXISTING"
    row=posts._row_payload(store,first["key"])
    assert hit["quote"] in row["text"] and hit["original_url"] in row["text"]
    assert "13 Nov 2026 19:00 ET" in row["text"] and record["line"] in row["text"]
    assert not row["counts_as_article"] and not f._PRIVATE.search(posts._split(row["text"])[0])
    plan=posts.prepare_post(store,first["key"],root=tmp_path/"posts",host=fake_host,
        destinations=tuple(hit["destinations"]),cc603_asset=asset(tmp_path))
    posts.scope_to_post(coordinator,first["key"],plan)
    coordinator.publish_plan(first["key"],plan)
    coordinator.publish_plan(first["key"],plan)
    assert sorted(transport.publish_calls)==sorted(hit["destinations"])
    intents=[json.loads(r["payload"]) for r in store.list_outbox_messages(work_item_id=first["key"])
             if r["destination"] in hit["destinations"]]
    assert all(record["line"] in r["native_payload"]["full_text"] for r in intents)
    assert all(r["native_payload"]["media_asset_ids"] for r in intents)
    assert all(not r["native_payload"].get("reply_to_id") for r in intents)
    assert len([r for r in store.list_outbox_messages(destination=posts.DESTINATION)
                if r["message_id"].startswith("cc603-followup-")])==1


def test_reconciled_absent_note_recovers_exact_bytes_without_a_canonical_rewrite(ready, tmp_path, monkeypatch):
    store, transport, coordinator, record = ready
    hit = candidate()
    queued = f.queue_followup(store, hit, f.check_path(hit, bars()), record, now=NOW)
    key = queued['key']
    row = posts._row_payload(store, key)
    plan = posts.prepare_post(store, key, root=tmp_path/'posts', host=fake_host,
                              destinations=tuple(row['cc603_destinations']), cc603_asset=asset(tmp_path))
    posts.scope_to_post(coordinator, key, plan)
    coordinator.register_plan(key, plan)
    ids = coordinator._ids(key, plan['plan_hash'], 'substack_notes')
    before = store.get_outbox_message(ids['message_id'])['payload']
    assert json.loads(before)['canonical_url'] is None
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'], message_id=ids['message_id'],
                                      platform='substack_notes', status='RECONCILED_ABSENT_SAFE_TO_RETRY')
    store.set_outbox_status(ids['message_id'], 'RECONCILED_ABSENT_SAFE_TO_RETRY')
    store.register_reconciliation(reconciliation_id=ids['reconciliation_id'], work_item_id=key,
                                   status='RECONCILED_ABSENT_SAFE_TO_RETRY')
    coordinator._record_destination_day_failure(json.loads(before), 'substack_notes', {
        'dispatch_id':ids['dispatch_id'], 'status':'UNKNOWN_WRITE',
        'safe_error_classification':'NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND'})
    monkeypatch.setattr(f, 'discover', lambda *a, **k: [])
    result = f.run_due(store, {'status':{'plans':[]}}, now=NOW, root=tmp_path/'posts', host=fake_host,
                       coordinator_for=lambda *a:coordinator, asset_for=lambda row:asset(tmp_path))
    assert result['posts'][-1]['publication']['per_destination']['substack_notes']['status'] == 'DISPATCH_CONFIRMED'
    assert transport.publish_calls.count('substack_notes') == 1
    assert store.get_outbox_message(ids['message_id'])['payload'] == before
    coordinator.recover_pending()
    assert transport.publish_calls.count('substack_notes') == 1


def test_uncertain_note_readback_failure_still_trips_destination_day_circuit(ready):
    store, transport, coordinator, _ = ready
    key = 'unreconciled-note'
    store.create_work_item(story_id=key, work_item_id=key, title='Uncertain note', target_surface='MULTI_PLATFORM')
    store.register_outbox_message(message_id=key, work_item_id=key, destination='substack_notes', payload='{}')
    ids = coordinator._ids(key, 'bound-plan', 'substack_notes')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'], message_id=key,
                                      platform='substack_notes', status='UNKNOWN_WRITE')
    coordinator._record_destination_day_failure({'work_item_id':key}, 'substack_notes', {
        'dispatch_id':ids['dispatch_id'], 'status':'UNKNOWN_WRITE',
        'safe_error_classification':'NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND'})
    assert coordinator._destination_day_failure('substack_notes')['dispatch_id'] == ids['dispatch_id']
    assert not transport.publish_calls


@pytest.mark.parametrize('status', ['DEFINITE_NO_WRITE','UNKNOWN_WRITE','DISPATCH_CONFIRMED'])
def test_missing_scale_repair_keeps_old_packages_and_never_reposts_an_uncertain_object(ready,tmp_path,monkeypatch,status):
    store,transport,coordinator,record=ready
    hit=candidate();key=f.queue_followup(store,hit,f.check_path(hit,bars()),record,now=NOW)['key']
    row=posts._row_payload(store,key);picture=asset(tmp_path)
    plan=posts.prepare_post(store,key,root=tmp_path/'posts',host=fake_host,
                            destinations=tuple(row['cc603_destinations']),cc603_asset=picture)
    coordinator.register_plan(key,plan)
    before={r['message_id']:r['payload'] for r in store.list_outbox_messages(work_item_id=key)
            if r['destination'] in row['cc603_destinations']}
    for destination in row['cc603_destinations']:
        ids=coordinator._ids(key,plan['plan_hash'],destination)
        store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform=destination,
            status=status,public_object_id='existing' if status=='DISPATCH_CONFIRMED' else None,
            public_object_url='https://t.me/CapitalChronicle/166' if status=='DISPATCH_CONFIRMED' else None)
        store.register_reconciliation(reconciliation_id=ids['reconciliation_id'],work_item_id=key,
                                      status='TRADINGVIEW_PRICE_SCALE_CHECK_REQUIRED')
    repaired=f.delivery_plan(store,row,picture,root=tmp_path/'posts',host=fake_host,destinations=row['cc603_destinations'])
    if status!='DEFINITE_NO_WRITE':
        assert repaired['plan_hash']==plan['plan_hash']
        assert not transport.publish_calls
        return
    assert repaired['plan_hash']!=plan['plan_hash'] and repaired['output_dir']!=plan['output_dir']
    monkeypatch.setattr(f,'discover',lambda *a,**k:[])
    result=f.run_due(store,{'status':{'plans':[]}},now=NOW,root=tmp_path/'posts',host=fake_host,
                     coordinator_for=lambda *a:coordinator,asset_for=lambda row:picture)
    assert all(v['status']=='DISPATCH_CONFIRMED' for v in result['posts'][-1]['publication']['per_destination'].values())
    assert sorted(transport.publish_calls)==sorted(row['cc603_destinations'])
    assert all(store.get_outbox_message(k)['payload']==v for k,v in before.items())
    f.run_due(store,{'status':{'plans':[]}},now=NOW,root=tmp_path/'posts',host=fake_host,
               coordinator_for=lambda *a:coordinator,asset_for=lambda row:picture)
    assert sorted(transport.publish_calls)==sorted(row['cc603_destinations'])


@pytest.mark.parametrize("change,cause",[
    ({"zone_low":130,"zone_high":135},"CONDITION_NOT_PROVEN"),
    ({"invalidation":{"field":"high","level":114,"side":"above"}},"INVALIDATION_FIRST"),
])
def test_no_hit_for_unmet_condition_or_invalidation(change,cause):
    result=f.check_path({**candidate(),**change},bars())
    assert not result["eligible"] and cause in result["cause"]


def test_same_bar_entry_and_move_does_not_prove_order():
    path=bars();path[0]["low"]=80
    assert f.check_path(candidate(),path)["cause"]=="CC603_CONDITION_NOT_PROVEN_BEFORE_MOVE"


def test_cr_view_reports_untraded_entry_without_minting_hit(ready):
    store,_,_,record=ready
    c={**candidate("CR_VIEW"),"zone_low":130,"zone_high":135,"invalidation":{"field":"high","level":140,"side":"above"}}
    check=f.check_path(c,bars())
    result=f.queue_followup(store,c,check,record,now=NOW+timedelta(days=3))
    row=posts._row_payload(store,result["key"])
    assert "entry zone never traded" in row["text"]
    assert "this was a directional view, with no trade" in row["text"]
    assert row["record"]["counts"]==record["counts"]


def test_partial_endpoint_match_is_not_a_hit():
    c={**candidate(),"source_kind":"ARTICLE","condition_met":True,"resolution_test":"AT_DEADLINE",
       "valid_until_utc":(START+timedelta(minutes=105)).isoformat()}
    path=bars();path[-1]["close"]=100  # Intrabar 89, but deadline close is only 100.
    assert not f.check_path(c,path)["eligible"]
    path[-1]["close"]=89
    assert f.check_path(c,path)["eligible"]


def test_missing_price_bar_cannot_hide_invalidation():
    path=bars();del path[2]
    assert f.check_path(candidate(),path)["cause"]=="CC603_HELD_PRICE_GAP"


@pytest.mark.parametrize('incomplete', ['UNKNOWN_WRITE', 'RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE'])
def test_corrections_read_back_before_followup(ready, incomplete):
    store,_,_,record=ready
    identity=f.GOLD_CORRECTION+'-threads'
    if incomplete == 'UNKNOWN_WRITE':
        store.set_dispatch_status(identity, incomplete)
    else:
        store.set_reconciliation_status('reconciliation_'+identity, incomplete)
        assert any(p['destination']=='threads' for p in f.publications(store,f.GOLD_CORRECTION))
    assert f.queue_followup(store,candidate(),f.check_path(candidate(),bars()),record,now=NOW)["status"]=="CORRECTIONS_PENDING"


def test_changed_pinned_record_prevents_wrong_fresh_copy(ready,tmp_path,monkeypatch):
    store,_,coordinator,record=ready
    q=f.queue_followup(store,candidate(),f.check_path(candidate(),bars()),record,now=NOW)
    row=posts._row_payload(store,q["key"])
    a=asset(tmp_path)
    plan=posts.prepare_post(store,q["key"],root=tmp_path/"posts",host=fake_host,
        destinations=tuple(candidate()["destinations"]),cc603_asset=a)
    posts.scope_to_post(coordinator,q["key"],plan)
    coordinator.register_plan(q["key"],plan)
    intent=json.loads(store.list_outbox_messages(work_item_id=q["key"],destination="telegram")[0]["payload"])
    monkeypatch.setattr(f,"observed_record",lambda *a,**k:{**record,"counts":{**record["counts"],"STOPPED":6}})
    with pytest.raises(ValueError,match="PUBLIC_RECORD_CHANGED"):
        posts.validate_status_post_intent(store,intent)


def test_existing_zone_correction_is_reused_and_gold_is_new_post(tmp_path):
    store,_,_=_coordinator(tmp_path)
    register(store,f.ZONE_CORRECTION,{"key":f.ZONE_CORRECTION,"text":"Correction."})
    original={"key":f.GOLD_ORIGINAL,"text":"Our original gold post.","symbol":"XAUUSD"}
    register(store,f.GOLD_ORIGINAL,original)
    before=store.get_outbox_message(f.GOLD_ORIGINAL)["payload"]
    first=f.prepare_gold_correction(store,now=NOW)
    assert f.prepare_gold_correction(store,now=NOW+timedelta(days=1))==first
    assert first["new_post_only"] and not first.get("correction_of")
    assert posts.freshness_limit_minutes(first)==float("inf")
    assert store.get_outbox_message(f.GOLD_ORIGINAL)["payload"]==before


def test_record_is_exact_pinned_object_and_counts(ready,monkeypatch):
    store,_,_,_=ready
    # Exercise the real observer rather than the fixture's network substitution.
    monkeypatch.undo()
    key="score-revision"
    record={"text":"Exact public record.","counts":{"HIT":1,"STOPPED":5,"EXPIRED":37,"total":43,"scored":7}}
    store.create_work_item(story_id=scorecard.WORK,work_item_id=scorecard.WORK,title="Record",target_surface="TELEGRAM")
    store.register_outbox_message(message_id=key,work_item_id=scorecard.WORK,destination=scorecard.DESTINATION,
                                  payload=json.dumps(record),status="CONFIRMED")
    store.register_outbox_message(message_id=scorecard.OBJECT,work_item_id=scorecard.WORK,destination="internal:object",
        payload=json.dumps({"message_id":"134","public_url":"https://t.me/CapitalChronicle/134"}))
    class API:
        def call(self,method):return {"username":"CapitalChronicle","type":"channel",
            "pinned_message":{"message_id":134,"text":record["text"]}}
    observed=f.observed_record(store,api=API(),now=NOW)
    assert observed["counts"]==record["counts"] and observed["observed_at_utc"]==NOW.isoformat()


def test_live_consumer_uses_stored_main_hit_and_ignores_stored_expiry(ready,tmp_path):
    store,transport,coordinator,record=ready
    for plan_id,result in (("stored-plan","HIT"),("stored-expiry","EXPIRED")):
        key="original-"+plan_id
        register(store,key,{"kind":"setup","key":key,"plan_id":plan_id,"symbol":"XAUUSD",
            "conditional_calls":[TERMS],"text":posts.conditional_call_text(TERMS),
            "levels":{"zone_low":110,"zone_high":112,"invalidation_level":120}},
            destinations=("telegram","x","substack_notes"))
        with store.get_connection() as conn:
            conn.execute("update platform_dispatches set dispatched_at=? where message_id in "
                "(select message_id from outbox_messages where work_item_id=?)",(START.isoformat(),key))
    source={"plan_id":"stored-plan","asset_id":"XAUUSD","zone":{"minimum":110,"maximum":112},
        "target_level":90,"invalidation_conditions":[{"field":"high","operator":"GTE","threshold":120}],
        "forecast_probabilities":{"reference_price":115,"horizon_end_utc":(NOW+timedelta(hours=3)).isoformat()},
        "outcome":{"state":"SCORED","result":"HIT","outcome_id":"hit-one",
            "score":{"result":"HIT","plan_id":"stored-plan","outcome_id":"hit-one"}},
        "expires_at_utc":(NOW+timedelta(hours=3)).isoformat()}
    expiry={**source,"plan_id":"stored-expiry","outcome":{"state":"SCORED","result":"EXPIRED"}}
    export={"status":{"plans":[source,expiry],"content_hash":"held-export"}}
    image=asset(tmp_path)
    for _ in range(2):
        result=f.run_due(store,export,now=NOW,root=tmp_path/"posts",coordinator_for=lambda *a:coordinator,
            host=fake_host,asset_for=lambda r:image,bars_reader=lambda *a:bars())
        assert result["corrections_complete"]
    queued=[r for r in store.list_outbox_messages(destination=posts.DESTINATION)
            if r["message_id"].startswith("cc603-followup-")]
    assert len(queued)==1 and queued[0]["status"]=="PUBLISHED"
    assert json.loads(queued[0]["payload"])["record"]["counts"]==record["counts"]
    assert sorted(transport.publish_calls)==["substack_notes","telegram","x"]


def test_published_article_condition_and_full_endpoint_are_both_required(tmp_path,monkeypatch):
    from live_contentops import published_content_v1 as feed
    store,_,_=_coordinator(tmp_path)
    end=START+timedelta(minutes=105)
    terms={**TERMS,"horizon":"13 Nov 20:45 ET"}
    trigger={"kind":"PRICE_PATH_V1","symbol":"XAUUSD","condition_met":False,
        "condition_source_hash":"bound-release-fact","condition_at_utc":START.isoformat(),
        "zone_low":110,"zone_high":112,"resolution_level":90,
        "invalidation":{"field":"high","level":120,"side":"above"},
        "valid_until_utc":end.isoformat(),"reference_price":115,"resolution_test":"AT_DEADLINE"}
    article={"content_id":"substack:stored-article","published_at_utc":START.isoformat(),
        "outlets":[{"name":"substack","url":"https://capitalchronicle.substack.com/p/stored"},
                   {"name":"x","url":"https://x.com/Capitalnicle/status/123"}],
        "conditional_calls":[{**terms,"trigger":trigger}]}
    monkeypatch.setattr(feed,"read_records",lambda *a:[article])
    found,checks=f.article_candidates(store,feed_path=tmp_path/"feed.jsonl")
    assert not found and checks[0]["cause"]=="CC603_ARTICLE_CONDITION_NOT_MET"
    trigger["condition_met"]=True
    found,_=f.article_candidates(store,feed_path=tmp_path/"feed.jsonl")
    assert found[0]["destinations"]==["substack_notes","x"]
    prices=bars();prices[-1]["close"]=100
    assert not f.check_path(found[0],prices)["eligible"]
    prices[-1]["close"]=89
    assert f.check_path(found[0],prices)["eligible"]


def test_first_post_meets_named_substack_x_acceptance_without_fake_originals(ready):
    store,_,_,record=ready
    c={**candidate(),"destinations":["telegram"]}
    result=f.queue_followup(store,c,f.check_path(c,bars()),record,now=NOW)
    row=posts._row_payload(store,result["key"])
    assert row["candidate"]["destinations"]==["telegram"]
    assert row["cc603_destinations"]==["substack_notes","telegram","x"]
    assert row["acceptance_destinations"]==["substack_notes","x"]


def test_old_cpi_article_uses_held_bls_core_and_exact_hour_endpoint(tmp_path):
    from hashlib import sha256
    event="US_CPI_20261114"
    response={"status":"REQUEST_SUCCEEDED","Results":{"series":[{"seriesID":"CUSR0000SA0L1E","data":[
        {"year":"2026","period":"M10","value":"100.3"},
        {"year":"2026","period":"M09","value":"100"},
        {"year":"2026","period":"M08","value":"-"}]}]}}
    raw=json.dumps(response).encode();response_path=tmp_path/"bls.json";response_path.write_bytes(raw)
    capture_path=tmp_path/"capture.json"
    capture_path.write_text(json.dumps({"response_path":str(response_path),"response_sha256":sha256(raw).hexdigest(),
                                       "http_status":200}),encoding="utf-8")
    (tmp_path/(event+"-held.json")).write_text(json.dumps({"api_capture":str(capture_path),"reference_period":"2026-10",
        "released_at_utc":START.isoformat(),"known_at_utc":(START+timedelta(seconds=90)).isoformat()}),encoding="utf-8")
    record={"content_id":"substack:held-cpi","event_id":"bls-cpi-20261114","published_at_utc":(START-timedelta(hours=1)).isoformat(),
        "title":"If October core CPI is 0.3% or higher, gold falls at least 0.7% in 60 minutes: Capital Chronicle model estimate",
        "outlets":[{"name":"substack","url":"https://capitalchronicle.substack.com/p/cpi"}]}
    prices=[{"open_epoch":int((START+timedelta(minutes=15*i)).timestamp()),"open":100,"high":100.1,
        "low":98.9,"close":99.5,"source_sha256":"held-prices"} for i in range(4)]
    c=f.cpi_article_candidate(record,outcomes=tmp_path,bars_reader=lambda *a:prices[:1])
    assert c["actual_core_mom_pct"]=="0.3" and c["condition_met"]
    assert c["original_text"].startswith(c["quote"]) and "model" not in c["quote"]
    assert not f.check_path(c,prices)["eligible"]  # Intrahour >0.7% alone is insufficient.
    prices[-1]["close"]=99.2
    checked=f.check_path(c,prices)
    assert checked["eligible"] and checked["observed_price"]==99.2
    assert not f.check_path({**c,"condition_met":False},prices)["eligible"]


def test_browser_pending_keeps_the_existing_minute_consumer_running(ready,tmp_path,monkeypatch):
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    store,transport,coordinator,record=ready
    c=candidate()
    q=f.queue_followup(store,c,f.check_path(c,bars()),record,now=NOW)
    original_publish=coordinator.publish_plan
    def pending(key,plan):
        api_plan={**plan,"destinations":[d for d in plan["destinations"] if d["destination"] not in {"x","substack_notes"}]}
        original_publish(key,api_plan)
        raise NativeNeoInputRequired({"destination":"substack_notes","request_sha256":"exact-pending"})
    monkeypatch.setattr(coordinator,"publish_plan",pending)
    monkeypatch.setattr(f,"discover",lambda *a:[])
    result=f.run_due(store,{"status":{"plans":[]}},now=NOW,root=tmp_path/"posts",
        coordinator_for=lambda *a:coordinator,host=fake_host,asset_for=lambda r:asset(tmp_path))
    assert result["posts"][-1]["publication"]["request_sha256"]=="exact-pending"
    assert sorted(transport.publish_calls)==["discord","telegram"]
    assert store.get_outbox_message(q["key"])["status"]=="CC603_PREPARED"


def test_stale_main_export_does_not_block_owed_corrections(monkeypatch):
    seen=[]
    monkeypatch.setattr(f,"corrections_complete",lambda s:False)
    monkeypatch.setattr(f,"run_due",lambda s,export,**k:seen.append(export) or {"status":"CORRECTION_PROCESSED"})
    def stale():raise ValueError("PLAN_EXPORT_STALE")
    assert f.minute_due(object(),stale)["status"]=="CORRECTION_PROCESSED"
    assert seen==[{"status":{"plans":[]}}]


def test_correction_continuation_keeps_chart_and_preserves_issued_root(ready,tmp_path):
    from hashlib import sha256
    store,_,coordinator,record=ready
    c={**candidate(),"destinations":["threads"]}
    result=f.queue_followup(store,c,f.check_path(c,bars()),record,now=NOW)
    key=result["key"]
    image=asset(tmp_path)
    plan=posts.prepare_post(store,key,root=tmp_path/"posts",host=fake_host,
        destinations=("threads",),cc603_asset=image)
    root_payload=posts._expected(store,key,plan["output_dir"])[1]["threads"]
    assert root_payload["parts"] if "parts" in root_payload else root_payload["media_asset_ids"]
    assert plan["continuations"]
    for child in plan["continuations"]:
        child_id=child["work_item_id"]
        assert child["plan_hash"]!=sha256(("plan-status-post:"+child_id).encode()).hexdigest()
        store.create_work_item(story_id=child_id,work_item_id=child_id,title="Continuation",target_surface="MULTI_PLATFORM")
        legacy={**child,"plan_hash":sha256(("plan-status-post:"+child_id).encode()).hexdigest()}
        posts.scope_to_post(coordinator,child_id,legacy)
        coordinator.register_plan(child_id,legacy)
        legacy_ids=coordinator._ids(child_id,legacy["plan_hash"],"threads")
        store.register_platform_dispatch(dispatch_id=legacy_ids["dispatch_id"],message_id=legacy_ids["message_id"],
            platform="threads",status="DEFINITE_NO_WRITE")
        posts.scope_to_post(coordinator,child_id,child)
        coordinator.register_plan(child_id,child)
        ids=coordinator._ids(child_id,child["plan_hash"],"threads")
        intent=json.loads(store.get_outbox_message(ids["message_id"])["payload"])
        assert intent["native_payload"]["media_asset_ids"]==[image["asset_id"]]
        result=coordinator.publish_plan(child_id,child)
        assert result["per_destination"]["threads"]["status"]=="DISPATCH_CONFIRMED"
        assert store.get_platform_dispatch(legacy_ids["dispatch_id"])["status"]=="DEFINITE_NO_WRITE"
    assert root_payload==posts._expected(store,key,plan["output_dir"])[1]["threads"]


def test_pythonw_minute_record_keeps_actual_followup_progress_without_media(tmp_path):
    result={"status":"OK","call_followups":{"status":"OK","corrections_complete":False,"posts":[
        {"key":f.GOLD_CORRECTION,"publication":{"status":"NATIVE_NEO_TOOL_PENDING","request_sha256":"exact-request",
            "raw_image":"omitted-media-bytes","copy":"omitted-copy","per_destination":{
                "telegram":{"status":"DISPATCH_CONFIRMED","public_object_url":"https://t.me/CapitalChronicle/184"},
                "substack_notes":{"status":"NATIVE_NEO_TOOL_PENDING","request_copy":"omitted-copy"}}}}]}}
    path=posts.record_run(result,tmp_path,now=NOW)
    stored=json.loads(path.read_text(encoding="utf-8"))
    observed=stored["call_followups"]["posts"][0]
    assert observed["key"]==f.GOLD_CORRECTION
    assert observed["publication"]["request_sha256"]=="exact-request"
    assert observed["publication"]["per_destination"]["telegram"]["status"]=="DISPATCH_CONFIRMED"
    assert "omitted" not in json.dumps(stored)
