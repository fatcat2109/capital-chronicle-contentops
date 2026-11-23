from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import heavy_news_quotes_v1 as quotes, sourced_replies_v1 as replies
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.neo_endpoint_executor_v1 import NeoBrowserDriver, NeoEndpointError, STEPS
from test_heavy_news_quotes_cc467 import prepared  # noqa: F401


def request_for(prepared, tmp_path):
    store, coordinator, _, raw, now = prepared
    row = quotes.stage(store, raw, now=now)
    coordinator.register_plan(row["key"], replies.plan_for(store, row["key"], root=tmp_path))
    intent = json.loads(store.list_outbox_messages(destination="x")[0]["payload"])
    auth = {"schema_version":"contentops.canonical_machine_authorization.v1", "operating_mode":"AUTONOMOUS_DEFAULT",
        "destination":"x", "dispatch_attempt_identity":"attempt", "work_item_id":row["key"],
        "payload_hash":intent["destination_plan"]["payload_hash"]}
    return store, intent, auth


def test_handoff_requires_exact_stored_quote_and_proves_edge_instead_of_link(prepared, tmp_path):
    store, intent, auth = request_for(prepared, tmp_path)
    handoff = NeoDestinationHandoff(store=store)
    request = handoff.request(destination="x", action="PUBLISH", intent=intent, authorization_context=auth)
    assert request["quote_parent"] == intent["quote_parent"] and "reply_parent" not in request
    assert request["surface"] == "X_POST"
    assert request["content_binding"]["media_manifest"][0]["sha256"] == intent["media_assets"][0]["sha256"]
    handoff.native_executor = lambda request:{"request_sha256":request["request_sha256"],"observed_identity":"@Capitalnicle",
        "status":"SUCCESS", "public_object_id":"456", "public_object_url":"https://x.com/Capitalnicle/status/456",
        "content_verified":True, "observed_text":intent["native_payload"]["text"]}
    result = handoff.publish(destination="x", intent=intent, authorization_context=auth)
    assert result["status"] == "UNKNOWN_WRITE" and result["reason_code"] == "X_QUOTE_PARENT_UNVERIFIED"
    handoff.native_executor = lambda request: {"request_sha256":request["request_sha256"],
        "status":"UNKNOWN_WRITE", "reason_code":"NEO_RUN_FAILED_PUBLISH"}
    result = handoff.publish(destination="x", intent=intent, authorization_context=auth)
    assert result["reason_code"] == "NEO_RUN_FAILED_PUBLISH" and result["retry_permitted"] is False


@pytest.mark.parametrize("variant,matches", [
    ("expanded", True), ("changed_copy", False), ("changed_clock", False), ("wrong_page", False),
])
def test_quote_opens_the_exact_permalink_when_x_expands_its_list_excerpt(variant, matches):
    program = """
const fs = require('fs');
const variant = process.argv[2];
const parent = {public_object_url:'https://x.com/FirstSquawk/status/123',
  source_posted_at_utc:'2026-11-18T19:01:52.788Z', source_text:'The list excerpt'};
const body = {innerText:variant==='changed_copy' ? 'A different story' : 'The list excerpt continues on the permalink.'};
let menuMarked = false;
const menu = {setAttribute:()=>{menuMarked=true;}};
const root = {querySelector:selector=>selector.includes('tweetText') ? body : menu};
const clock = {getClientRects:()=>[{}], closest:selector=>selector==='a' ? {href:parent.public_object_url} : root,
  getAttribute:()=>variant==='changed_clock' ? '2026-11-18T19:01:53.000Z' : '2026-11-18T19:01:52.000Z'};
const document = {querySelectorAll:()=>[clock]};
const location = new URL(variant==='wrong_page' ? 'https://x.com/FirstSquawk/status/124' : parent.public_object_url);
const page = {evaluateInPage:async(fn,arg)=>({value:fn(arg)})};
const run = new (Object.getPrototypeOf(async function(){}).constructor)(
  'input','page','document','location',fs.readFileSync(process.argv[1],'utf8'));
run({phase:'quote_source',quote_parent:parent},page,document,location)
  .then(result=>console.log(JSON.stringify({matches:result.matches,menuMarked})));
"""
    completed = subprocess.run(["node", "-e", program, str(STEPS), variant], capture_output=True, timeout=10, check=True)
    assert json.loads(completed.stdout) == {"matches": matches, "menuMarked": matches}


@pytest.mark.parametrize("fault,expected,clicks", [
    ("expired", "CC467_SOURCE_OUTSIDE_FIVE_MINUTES", 0),
    ("changed_card", "CC467_QUOTE_CARD_NOT_VERIFIED", 0),
    ("changed_excerpt", "CC467_QUOTE_CARD_NOT_VERIFIED", 0),
    ("avatar_only", "CC467_CHART_PREVIEW_NOT_LOADED", 0),
    ("preview_timeout", "CC467_CHART_PREVIEW_NOT_LOADED", 0),
    ("lost_click_return", "CC467_QUOTE_CLICK_RETURN_INCOMPLETE", 1),
    ("composer_still_open", "CC467_QUOTE_COMPOSER_STILL_OPEN_AFTER_CLICK", 1),
    (None, "CLICKED", 1),
])
def test_actual_final_submit_program_checks_deadline_and_card_before_its_only_click(fault, expected, clicks):
    # Run the actual shipped JS with a settled composer and a controlled Neo page.
    # A deadline can elapse after Python's dispatch check while the upload settles.
    deadline = datetime.now(timezone.utc) + timedelta(seconds=-1 if fault == "expired" else 60)
    program = """
const fs=require('fs');const input=JSON.parse(process.argv[2]);
const {fault, ...request}=input;
let clicked=0, label='Post', chartReady=false;
const visible={getClientRects:()=>[{}]};
const tweet=fault==='changed_card'?'Different.':fault==='changed_excerpt'?'Bound headline. With changed details.':'Bound headline.';
const clock={getAttribute:()=>request.quote_parent.source_posted_at_utc};
const card={...visible,innerText:'@FirstSquawk',getAttribute:()=>'button',contains:()=>false,
  querySelectorAll:selector=>({'[data-testid="tweetText"]':[{innerText:tweet+' https://\\nexample.com/long',
    textContent:tweet+' https://example.com/long'}],time:[clock]})[selector]||[]};
const chart={...visible,complete:true,naturalWidth:1400};
const submit={...visible,disabled:false,getAttribute:()=>null,setAttribute:(_,name)=>{label=name;}};
const dialog={querySelector:()=>submit,querySelectorAll:selector=>selector.startsWith('[data-testid="attachments"]')
  ? (chartReady&&fault!=='avatar_only'?[chart]:[]) : [card]};
const editor={...visible,innerText:'Bound text.',closest:()=>dialog};
const document={querySelectorAll:()=>[editor]};
const page={snapshot:async()=>({refs:[{role:'button',name:label,ref:'submit'}]}),
  evaluateInPage:async(fn,args)=>({value:fn(args)}),waitForSelector:async selector=>{
    if(selector.startsWith('body:not(')) {
      if(clicked!==1)throw Error('Composer settlement checked before the Post click');
      return {matched:fault!=='composer_still_open'};
    }
    if(selector.includes('blob:'))chartReady=fault!=='preview_timeout';return {matched:chartReady};},
  click:async ref=>{if(ref!=='submit')throw Error('Wrong submit control');clicked++;
    if(fault==='lost_click_return')throw Error('Lost return');}};
const fn=new (Object.getPrototypeOf(async function(){}).constructor)('input','page','document',fs.readFileSync(process.argv[1],'utf8'));
fn(request,page,document).then(result=>console.log(JSON.stringify({result,clicked}))).catch(e=>{console.error(e);process.exit(1)});
"""
    data = {"phase":"publish", "destination":"x", "posts":["Bound text."], "fault":fault,
        "quote_parent":{"deadline_at_utc":deadline.isoformat(), "public_object_id":"123",
            "public_object_url":"https://x.com/FirstSquawk/status/123", "source_text":"Bound headline. https://t.co/example",
            "source_posted_at_utc":(deadline-timedelta(minutes=5)).isoformat()}}
    result = subprocess.run(["node","-e",program,str(STEPS),json.dumps(data)],capture_output=True,timeout=10)
    assert result.returncode == 0, result.stderr.decode()
    value=json.loads(result.stdout)
    assert value["result"].get("reason_code",value["result"]["status"]) == expected
    assert value["clicked"] == clicks


class QuoteClient:
    def __init__(self, *, matches=True, focused=True):
        self.matches, self.focused = matches, focused
        self.actions, self.uploads = [], []
    def call(self,name,data):
        self.actions.append((name,data))
        if name=="upload":self.uploads.extend(data["files"])
    def wait(self,page,selector):self.actions.append(("wait", {"selector":selector}))
    def snapshot(self,page):
        return {"refs":[{"role":role,"name":name,"ref":name} for role,name in
            [("button","CC467 source quote menu"),("menuitem","Quote"),("textbox","Post text"),("button","Choose Files")]]}
    def run(self,page,phase,**kw):
        if phase == "quote_source":
            return {"matches":self.matches, "menu_available":True}
        if phase == "quote_control_focused":
            return {"focused":self.focused or kw["control"] == "menu"}
        return {}
    def act(self,page,kind,**kw):self.actions.append((kind,kw))


def test_prepare_opens_exact_source_quote_and_uploads_without_opening_file_dialog(prepared, tmp_path):
    store,intent,auth=request_for(prepared,tmp_path)
    request=NeoDestinationHandoff(store=store).request(destination="x",action="PUBLISH",intent=intent,authorization_context=auth)
    client=QuoteClient()
    posts=NeoBrowserDriver(client).prepare(request,1)
    assert posts == [intent["native_payload"]["text"]]
    assert client.actions[0][1]["url"]==intent["quote_parent"]["public_object_url"]
    assert client.actions[1][1]["selector"].endswith('/status/123"] time')
    assert [(k,v.get("ref") or v.get("key")) for k,v in client.actions if k in {"click", "focus", "press"}] == [
        ("focus","CC467 source quote menu"), ("press","Enter"), ("focus","Quote"), ("press","Enter")]
    assert client.uploads == [intent["media_assets"][0]["path"]]
    client=QuoteClient(matches=False)
    with pytest.raises(NeoEndpointError,match="VISIBLE_SOURCE_CHANGED"):
        NeoBrowserDriver(client).prepare(request,1)
    assert not client.uploads and not any(k=="press" for k,_ in client.actions)
    client = QuoteClient(focused=False)
    with pytest.raises(NeoEndpointError, match="QUOTE_CONTROL_FOCUS_NOT_CONFIRMED"):
        NeoBrowserDriver(client).prepare(request, 1)
    assert not client.uploads and sum(k == "press" for k, _ in client.actions) == 1


@pytest.mark.parametrize("reason", ["CC467_QUOTED_SOURCE_OR_CHART_MISSING", "CC467_CHART_PREVIEW_NOT_LOADED"])
def test_another_fresh_quote_dispatches_after_a_local_chart_refusal(prepared, tmp_path, reason):
    store, coordinator, transport, raw, now = prepared
    incident_id, _ = coordinator._destination_failure_key("x")
    store.register_incident(incident_id=incident_id, work_item_id="work-1", severity="DISPATCH_FAILURE",
        description=json.dumps({"status":"DEFINITE_NO_WRITE", "safe_error_classification":reason}))
    row = quotes.stage(store, raw, now=now)
    result = replies.publish(store, row["key"], coordinator=coordinator, root=tmp_path, now=now)
    assert result["reply"]["readback_url"] and transport.publish_calls == ["x"]


def test_real_native_begin_uses_the_registered_x_surface_and_bad_surface_never_claims(prepared, tmp_path):
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator, NativeNeoInputRequired
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store,_,_,raw,now=prepared
    row=quotes.stage(store,raw,now=now)
    coordinator,executor=bind_native_neo_coordinator(store,operation_id=row["key"],output_dir=tmp_path/"native",
        native_invocation_id="fixture-cc467",allow_publish=True)
    coordinator.register_plan(row["key"],replies.plan_for(store,row["key"],root=tmp_path))
    _,intent,auth=request_for(prepared,tmp_path)
    ids=DurablePublicationCoordinator._ids(row["key"],replies.digest(row),"x")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"],message_id=ids["message_id"],platform="x",status="DISPATCH_ATTEMPT_STARTED")
    executor.inline_transport=True
    auth["dispatch_attempt_identity"]=ids["dispatch_id"]
    request=NeoDestinationHandoff(store=store).request(destination="x",action="PUBLISH",intent=intent,authorization_context=auth)
    with pytest.raises(NativeNeoInputRequired):executor(request)
    packet=executor.begin(request["request_sha256"])
    assert packet["composed_run"]["1_identity"]["expected_identity"]=="@Capitalnicle"
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    bad={**request,"surface":"UNREGISTERED_QUOTE_SURFACE"}
    bad["request_sha256"]=sha256_of({k:v for k,v in bad.items() if k!="request_sha256"})
    with pytest.raises(NativeNeoInputRequired):executor(bad)
    with pytest.raises(ValueError,match="SURFACE_UNREGISTERED"):executor.begin(bad["request_sha256"])
    assert executor._get(bad["request_sha256"],"started") is None


@pytest.mark.parametrize("kind", ["quote", "plan-root", "plan-reply"])
def test_x_absence_reader_requires_loaded_own_profile_and_older_last_post(kind):
    from live_contentops.neo_destination_handoff_v1 import ROOTS
    class Reader:
        def call(self,*a):pass
        def wait(self,*a):pass
        def snapshot(self,p):return {"url":ROOTS["x"]}
        def run(self,p,phase,**kw):
            if phase=="identity":return {"authenticated":True,"observed_identity":"@Capitalnicle"}
            return {"tweets":[{"public_object_id":"1","public_object_url":ROOTS["x"]+"/status/1",
                "observed_text":"An earlier, different ordinary post.","published_at_utc":"2026-11-17T12:00:00Z"}]}
    request={"destination":"x","action":"READBACK","entry_url":ROOTS["x"],"expected_identity":"@Capitalnicle",
        "native_payload":{"text":"The exact missing post."},
        "content_binding":{},"latest_dispatch_attempt_at_utc":"2026-11-17T13:00:00Z"}
    if kind == "quote":
        request["quote_parent"] = {"public_object_id": "source"}
    else:
        request["plan_status_root_readback"] = True
    if kind == "plan-reply":
        request["reply_parent"] = {"public_object_id": "parent"}
    result=NeoBrowserDriver(Reader()).readback(request,1)
    if kind == "plan-reply":
        assert result["status"] == "READBACK_UNAVAILABLE"
        assert "target_post_absent" not in result
        return
    assert result["target_post_absent"] and result["authenticated"] and result["observed_feed_post_ids"]==["1"]
    from live_contentops.native_neo_executor_v1 import _readback_absence_evidence
    result["native_tool_observation"]={"observed_at_utc":"2026-11-17T13:09:59Z"}
    assert not _readback_absence_evidence(request,result)
    result["native_tool_observation"]["observed_at_utc"]="2026-11-17T13:10:00Z"
    assert _readback_absence_evidence(request,result)
    request["latest_dispatch_attempt_at_utc"]="2026-11-17T11:00:00Z"
    assert "target_post_absent" not in NeoBrowserDriver(Reader()).readback(request,1)


def test_interrupted_quote_begin_keeps_its_claim_without_stopping_x(prepared,tmp_path):
    from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator,NativeNeoInputRequired
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store,_,_,raw,now=prepared
    row=quotes.stage(store,raw,now=now)
    c,e=bind_native_neo_coordinator(store,operation_id=row["key"],output_dir=tmp_path/"native",native_invocation_id="fixture",allow_publish=True)
    c.register_plan(row["key"],replies.plan_for(store,row["key"],root=tmp_path))
    _,intent,auth=request_for(prepared,tmp_path)
    ids=DurablePublicationCoordinator._ids(row["key"],replies.digest(row),"x")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"],message_id=ids["message_id"],platform="x",status="UNKNOWN_WRITE")
    auth["dispatch_attempt_identity"]=ids["dispatch_id"]
    request=NeoDestinationHandoff(store=store).request(destination="x",action="PUBLISH",intent=intent,authorization_context=auth)
    request["surface"]="X_QUOTE_POST"
    request["request_sha256"]=sha256_of({k:v for k,v in request.items() if k!="request_sha256"})
    with pytest.raises(NativeNeoInputRequired):e(request)
    e._put(request["request_sha256"],"started",{"begun_at_utc":now.isoformat()},row["key"])
    incident, _ = c._destination_failure_key("x")
    store.register_incident(incident_id=incident, work_item_id=row["key"], severity="DISPATCH_FAILURE",
        description=json.dumps({"dispatch_id": ids["dispatch_id"], "safe_error_classification": "KeyError",
                                "status": "UNKNOWN_WRITE"}))
    assert c._destination_day_failure("x") is None
    outcome = c._dispatch_message(store.get_outbox_message(ids["message_id"]), canonical_url=None)
    assert not outcome["publish_called"]
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "UNKNOWN_WRITE"
    assert e._get(request["request_sha256"], "response") is None


@pytest.mark.parametrize("quote_views,ordinary_views,decision",[(30,10,"KEEP"),(1,10,"STOP"),(None,10,None)])
def test_fourteen_day_decision_consumes_our_actual_daily_views_not_follower_counts(monkeypatch,quote_views,ordinary_views,decision):
    start=datetime.now(timezone.utc)-timedelta(days=15)
    class Store:
        def list_outbox_messages(self,**kw):return [{"payload":json.dumps({"heavy_news_quote":quotes.POLICY,"key":"quote"})}]
        def list_platform_dispatches(self):return [{"platform":"x","status":"DISPATCH_CONFIRMED","dispatched_at":at.isoformat(),
            "work_item_id":key,"message_id":key,"dispatch_id":key}
            for key,at in [("quote",start-timedelta(seconds=5)),("ordinary",start)]]
        def get_outbox_message(self,key):return {"payload":"{}"}
        def list_performance_observations(self):return [{"dispatch_id":key,"observation_window":"DAILY","collected_at_utc":start.isoformat(),
            "metrics_native_json":json.dumps({"views":value})} for key,value in [("quote",quote_views),("ordinary",ordinary_views)]]
    monkeypatch.setattr(quotes,"quote_report",lambda s,r:{"key":"quote","readback_url":"https://x.com/Capitalnicle/status/1",
        "observed_published_at_utc":start.isoformat()})
    result=quotes.audience_review(Store())
    assert result.get("decision")==decision
    assert result["views_per_post"]["quotes"]==quote_views
    assert result["unavailable_views"]["quotes"]==(1 if quote_views is None else 0)


@pytest.mark.parametrize("role,model,effort,timeout",quotes.ROLES)
def test_native_role_calls_record_exact_model_and_effort_without_a_label_gate(tmp_path, monkeypatch, role, model, effort, timeout):
    from live_contentops import light_model_caller_v1 as caller
    def runner(args, **kw):
        assert args[args.index("--model")+1] == model
        assert 'model_reasoning_effort="'+effort+'"' in args and kw["timeout"]==timeout
        assert "--disable" in args and "shell_tool" in args
        return subprocess.CompletedProcess(args,0,b'{"text":"Bound native answer."}',b'')
    monkeypatch.setattr(caller,"_run_codex",runner)
    answer,record=quotes.native_call(role,"Bound source text",tmp_path/role)
    assert answer["text"]=="Bound native answer."
    assert (record["configured_model"],record["configured_effort"])==(model,effort)
    assert json.loads((tmp_path/role/"call.json").read_bytes())["configuration_status"]=="CONFIGURED_NOT_OBSERVED"
