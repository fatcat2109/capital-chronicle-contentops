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
    assert request["surface"] == "X_QUOTE_POST"
    assert request["content_binding"]["media_manifest"][0]["sha256"] == intent["media_assets"][0]["sha256"]
    handoff.native_executor = lambda request:{"request_sha256":request["request_sha256"],"observed_identity":"@Capitalnicle",
        "status":"SUCCESS", "public_object_id":"456", "public_object_url":"https://x.com/Capitalnicle/status/456",
        "content_verified":True, "observed_text":intent["native_payload"]["text"]}
    result = handoff.publish(destination="x", intent=intent, authorization_context=auth)
    assert result["status"] == "UNKNOWN_WRITE" and result["reason_code"] == "X_QUOTE_PARENT_UNVERIFIED"


@pytest.mark.parametrize("expired,card,expected",[(True,True,"CC467_SOURCE_OUTSIDE_FIVE_MINUTES"),
                                                (False,False,"CC467_QUOTED_SOURCE_OR_CHART_MISSING"),
                                                (False,True,"CLICKED")])
def test_actual_final_submit_program_checks_deadline_and_card_before_its_only_click(tmp_path, expired, card, expected):
    # Run the actual shipped JS with a settled composer and a controlled Neo page.
    # A deadline can elapse after Python's dispatch check while the upload settles.
    deadline = datetime.now(timezone.utc)+timedelta(seconds=-1 if expired else 60)
    program = """
const fs=require('fs');const input=JSON.parse(process.argv[2]);
let clicked=0, calls=0;
const page={snapshot:async()=>({text:'',refs:[{role:'button',name:'Post',ref:'submit'}]}),
 evaluateInPage:async()=>{calls++;const value=calls===1?{matches:true,count:1}:calls===2?['Bound text.']:
   calls===3?{marked:true}:{matches:input.card,deadline:Date.parse(input.quote_parent.deadline_at_utc)};return {value}},
 waitForSelector:async()=>({matched:true}),click:async()=>{clicked++}};
const browser={page:()=>page};delete input.card;
const fn=new (Object.getPrototypeOf(async function(){}).constructor)('browser','const input='+JSON.stringify(input)+';\\n'+fs.readFileSync(process.argv[1],'utf8'));
fn(browser).then(result=>console.log(JSON.stringify({result,clicked}))).catch(e=>{console.error(e);process.exit(1)});
"""
    data = {"phase":"publish","page":1,"destination":"x","posts":["Bound text."],"card":card,
        "quote_parent":{"deadline_at_utc":deadline.isoformat()}}
    # Keep the mock's settled quote observation outside the untrusted request.
    program=program.replace("let clicked=0, calls=0;", "let clicked=0, calls=0;const observedCard=input.card;").replace("matches:input.card", "matches:observedCard")
    result = subprocess.run(["node","-e",program,str(STEPS),json.dumps(data)],capture_output=True,timeout=10)
    assert result.returncode == 0, result.stderr.decode()
    value=json.loads(result.stdout)
    assert value["result"].get("reason_code",value["result"]["status"]) == expected
    assert value["clicked"] == (1 if expected=="CLICKED" else 0)


class QuoteClient:
    def __init__(self, *, matches=True):self.matches,self.actions,self.uploads=matches,[],[]
    def call(self,name,data):
        self.actions.append((name,data))
        if name=="upload":self.uploads.extend(data["files"])
    def wait(self,*a):pass
    def snapshot(self,page):
        return {"refs":[{"role":role,"name":name,"ref":name} for role,name in
            [("button","CC467 source quote menu"),("menuitem","Quote"),("textbox","Post text"),("button","Choose Files")]]}
    def run(self,page,phase,**kw):
        return {"matches":self.matches} if phase=="quote_source" else {}
    def act(self,page,kind,**kw):self.actions.append((kind,kw))


def test_prepare_opens_exact_source_quote_and_uploads_without_opening_file_dialog(prepared, tmp_path):
    store,intent,auth=request_for(prepared,tmp_path)
    request=NeoDestinationHandoff(store=store).request(destination="x",action="PUBLISH",intent=intent,authorization_context=auth)
    client=QuoteClient()
    posts=NeoBrowserDriver(client).prepare(request,1)
    assert posts == [intent["native_payload"]["text"]]
    assert client.actions[0][1]["url"]==intent["quote_parent"]["public_object_url"]
    assert [(k,v.get("ref")) for k,v in client.actions if k=="click"] == [
        ("click","CC467 source quote menu"),("click","Quote")]
    assert client.uploads == [intent["media_assets"][0]["path"]]
    client=QuoteClient(matches=False)
    with pytest.raises(NeoEndpointError,match="VISIBLE_SOURCE_CHANGED"):
        NeoBrowserDriver(client).prepare(request,1)
    assert not client.uploads and not any(k=="click" for k,_ in client.actions)


@pytest.mark.parametrize("quote_views,ordinary_views,decision",[(30,10,"KEEP"),(1,10,"STOP"),(None,10,None)])
def test_fourteen_day_decision_consumes_our_actual_daily_views_not_follower_counts(monkeypatch,quote_views,ordinary_views,decision):
    start=datetime.now(timezone.utc)-timedelta(days=15)
    class Store:
        def list_outbox_messages(self,**kw):return [{"payload":json.dumps({"heavy_news_quote":quotes.POLICY,"key":"quote"})}]
        def list_platform_dispatches(self):return [{"platform":"x","status":"DISPATCH_CONFIRMED","dispatched_at":start.isoformat(),
            "work_item_id":key,"message_id":key,"dispatch_id":key} for key in ["quote","ordinary"]]
        def get_outbox_message(self,key):return {"payload":"{}"}
        def list_performance_observations(self):return [{"dispatch_id":key,"observation_window":"DAILY","collected_at_utc":start.isoformat(),
            "metrics_native_json":json.dumps({"views":value})} for key,value in [("quote",quote_views),("ordinary",ordinary_views)]]
    monkeypatch.setattr(replies,"report_one",lambda s,r:{"key":"quote","readback_url":"https://x.com/Capitalnicle/status/1","posted_at_utc":start.isoformat()})
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
