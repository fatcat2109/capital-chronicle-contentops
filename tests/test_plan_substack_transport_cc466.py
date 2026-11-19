"""Exercise the plan-page branch of the installed Neo transport, including lost clicks."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image
import pytest

from live_contentops import plan_substack_neo_v1 as plan_neo
from live_contentops import neo_endpoint_executor_v1 as neo


class Client:
    def __init__(self, packet, fault=None):
        self.packet=packet
        self.fault=fault
        self.calls=[]
        self.clicked=False
        self.email=True

    def open(self, destination, url):
        self.calls.append(("open",destination,url))
        return 1

    def wait(self, page, selector):
        self.calls.append(("wait",selector))

    def wait_text(self, page, text):
        self.calls.append(("wait_text",text))
        if self.fault=="code" and self.clicked:
            raise neo.NeoEndpointError("WAIT_TIMED_OUT")

    def snapshot(self, page):
        controls=[("button","Create"),("menuitem","Article"),("textbox","title"),
            ("textbox","Add a subtitle…"),("button","Insert image"),("menuitem","Image"),
            ("button","CC466 editor upload"),("button","Continue"),
            ("checkbox","Send via email and the Substack app"),("button","Publish on web only"),("tab","Share")]
        return {"text":"Check your email" if self.fault=="code" and self.clicked else "Ready",
            "url":"https://capitalchronicle.substack.com/publish/post/123",
            "refs":[{"role":r,"name":n,"ref":n} for r,n in controls]}

    def act(self, page, kind, **kw):
        self.calls.append(("act",kind,kw))
        if kw.get("ref")=="Send via email and the Substack app":
            self.email=False

    def call(self, name, args):
        self.calls.append((name,args))

    def run(self, page, phase, **kw):
        self.calls.append((phase,kw))
        if phase in {"plan_substack_identity","plan_substack_editor_identity"}:
            return {"authenticated":self.fault!="account","observed_identity":"capitalchronicle.substack.com"}
        if phase=="plan_substack_uploaded":
            return {"src":"https://substack-post-media.s3.amazonaws.com/public/images/own.png"}
        if phase=="plan_substack_check":
            if self.fault=="editor_error":
                raise neo.NeoEndpointError("EDITOR_UNAVAILABLE")
            return {"verified":self.fault!="body"}
        if phase=="plan_substack_email":
            return {"enabled":self.email}
        if phase=="plan_substack_publish":
            self.clicked=True
            if self.fault=="lost_click":
                raise neo.NeoEndpointError("LOST_RETURN")
            return {"status":"CLICKED","dispatched_at_utc":"2026-11-12T01:00:00Z"}
        if phase=="plan_substack_code_handoff":
            return {"page_id":page,"draft_id":"123","page_url":self.snapshot(page)["url"]}
        if phase=="plan_substack_published":
            if self.fault in {"expired_code", "wrong_expired_editor"}:
                return {}
            if kw.get("published_row_draft_id"):
                return {"published_detail_url":"https://capitalchronicle.substack.com/publish/posts/detail/123"}
            return {"public_object_id":"123","public_object_url":"https://capitalchronicle.substack.com/p/own"}
        if phase=="plan_substack_cancel_expired_code":
            return {"closed": True, "draft_url": kw["draft_url"] if self.fault=="expired_code" else kw["draft_url"]+"4"}
        if phase=="plan_substack_readback":
            request=self.packet["request"]
            body=plan_neo.body_text(request["native_payload"]["body_markdown"])
            public_url=next((c[2] for c in self.calls if c[:2]==("open","plan-substack-public")), None)
            return {"status":"SUCCESS","public_object_url":public_url or request["public_object_url"],
                "observed_text":"A sourced page. "+body,
                "article_text":body+(" Extra invented words." if self.fault=="extra_body" else ""),
                "media":[],"public_image_urls":[]}
        return {}


@pytest.fixture
def packet():
    return {"operation_id":"plan-analysis-plan_own","request":{"destination":"substack","action":"PUBLISH",
        "native_payload":{"title":"A sourced page.","subtitle":"The forces behind our view.",
            "body_markdown":"At a glance.\n\n## Macro\n\nWe see a stronger dollar."},
        "substack_delivery_policy":{"email_send_enabled":False},
        "content_binding":{"media_manifest":[],
            "expected_text_segments":["A sourced page.","We see a stronger dollar."]}}}


def test_plan_route_disables_email_and_publishes_bound_body_once(packet):
    client=Client(packet)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="SUCCESS"
    assert result["result"]["delivery_observation"]["email_send_enabled"] is False
    assert not client.email
    phases=[c[0] for c in client.calls]
    assert phases.count("plan_substack_publish")==1
    assert phases.index("plan_substack_check")<phases.index("plan_substack_publish")
    pasted=next(c[1]["html"] for c in client.calls if c[0]=="plan_substack_paste")
    assert pasted=="<p>At a glance.</p><h2>Macro</h2><p>We see a stronger dollar.</p>"
    assert next(i for i,c in enumerate(client.calls) if c==("wait_text","Saved")) < next(
        i for i,c in enumerate(client.calls) if c[0]=="act" and c[2].get("ref")=="Continue")


def test_retained_preclick_draft_is_checked_and_sent_without_creating_another(packet):
    client=Client(packet)
    client.resume_draft_url="https://capitalchronicle.substack.com/publish/post/123"
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="SUCCESS"
    assert not any(c[0]=="act" and c[2].get("ref")=="Create" for c in client.calls)
    assert any(c[0]=="plan_substack_check" for c in client.calls)
    assert sum(c[0]=="plan_substack_publish" for c in client.calls)==1


def test_measured_piece_method_link_reaches_the_editor_paste(packet):
    url="https://capitalchronicle.substack.com/p/how-we-measure-a-trading-rule-before"
    packet["operation_id"]="cc536-measured-odds-2"
    packet["request"]["native_payload"]["body_markdown"]=(
        "Read the [method page]("+url+").\n\n## Source\n\nTable fingerprint: `ce3c11ff`.")
    client=Client(packet)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="SUCCESS"
    pasted=next(c[1]["html"] for c in client.calls if c[0]=="plan_substack_paste")
    assert '<a href="'+url+'">method page</a>' in pasted
    assert '<code>ce3c11ff</code>' in pasted
    assert '[method page]' not in pasted
    assert 'href="javascript:' not in plan_neo.body_html('[bad](javascript:alert(1))')


def test_wrong_retained_draft_cannot_reach_publish(packet):
    client=Client(packet,"body")
    client.resume_draft_url="https://capitalchronicle.substack.com/publish/post/123"
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="FAILED_BEFORE_WRITE"
    assert not client.clicked


@pytest.mark.parametrize("fault",["account","body","editor_error"])
def test_failure_before_click_is_a_definite_no_write(packet,fault):
    client=Client(packet,fault)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="FAILED_BEFORE_WRITE"
    assert result["result"]["definite_no_write"] is True
    assert not client.clicked


@pytest.mark.parametrize("host, account, authenticated", [
    ("capitalchronicle.substack.com", "Capital Chronicle's avatar", True),
    ("capitalchronicle.substack.com", "Capital Chronicle", True),
    ("capitalchronicle.substack.com", "Another account's avatar", False),
    ("another-publication.substack.com", "Capital Chronicle's avatar", False),
])
def test_dashboard_identity_uses_the_bound_publication_and_signed_in_control(host, account, authenticated):
    source = Path(neo.__file__).with_name("neo_endpoint_steps_v1.js")
    snapshot = {
        "url": f"https://{host}/publish/posts/published",
        "text": '- navigation "Publisher dashboard"\n  - image "Capital Chronicle"',
        "refs": [{"role": "button", "name": account}, {"role": "button", "name": "Create"}],
    }
    script = """
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const run = new AsyncFunction('page', 'input', fs.readFileSync(process.argv[1], 'utf8'));
const page = {snapshot: async () => JSON.parse(process.argv[2])};
run(page, {phase: 'plan_substack_identity'}).then(result => console.log(JSON.stringify(result)));
"""
    output = subprocess.check_output(["node", "-e", script, str(source), json.dumps(snapshot)],
                                     text=True, timeout=5)
    result = json.loads(output)
    assert result["authenticated"] is authenticated
    assert result["observed_identity"] == ("capitalchronicle.substack.com" if authenticated else None)


def test_lost_publish_return_requires_readback_and_is_never_called_no_write(packet):
    client=Client(packet,"lost_click")
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="UNKNOWN_WRITE"
    assert result["result"]["definite_no_write"] is False
    assert client.clicked and result["dispatched_at_utc"]


def test_email_code_handoff_returns_only_the_exact_screen_for_recording(packet):
    client=Client(packet,"code")
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="PENDING_JIM_EMAIL_CODE"
    assert result["result"]["observed_identity"]=="capitalchronicle.substack.com"
    handoff=next(i for i,c in enumerate(client.calls) if c[0]=="plan_substack_code_handoff")
    assert handoff==len(client.calls)-1
    assert result["result"]["draft_id"] == "123"
    assert "gmail_page_id" not in result["result"]
    assert not any(c[0]=="act" and c[2].get("ref")=="Publish on web only" for c in client.calls)


@pytest.mark.parametrize("draft_id", ["123", "456"])
def test_code_readback_observes_the_same_tab_before_opening_its_exact_public_page(packet, draft_id):
    packet["request"].update(action="READBACK", pending_owner_screen={
        "page_id": "1", "draft_id": draft_id,
        "page_url": f"https://capitalchronicle.substack.com/publish/post/{draft_id}"})
    client = Client(packet)
    result = neo.NeoBrowserDriver(client).perform(packet)["result"]
    assert client.calls[0] == ("plan_substack_published", {})
    if draft_id == "123":
        assert result["content_verified"] is True
        assert result["public_object_id"] == draft_id
        assert client.calls[1] == ("open", "plan-substack-public", "https://capitalchronicle.substack.com/p/own")
    else:
        assert result["reason_code"] == "SUBSTACK_CODE_TAB_SHARE_CENTER_REQUIRED"
        assert len(client.calls) == 1
    assert not any(c[0] == "act" for c in client.calls)


def test_readback_without_identity_leaves_browser_tabs_untouched(packet):
    packet["request"]["action"] = "READBACK"
    client = Client(packet)
    result = neo.NeoBrowserDriver(client).perform(packet)["result"]
    assert result["reason_code"] == "PLAN_SUBSTACK_EXACT_PUBLIC_URL_REQUIRED"
    assert client.calls == []


@pytest.mark.parametrize("fault,closed", [("expired_code", True), ("wrong_expired_editor", False), (None, False)])
def test_expired_code_closes_only_the_exact_draft_and_preserves_a_public_readback(packet, fault, closed):
    screen = {"page_id": "15", "draft_id": "123", "page_url": "https://capitalchronicle.substack.com/publish/post/123",
              "cancel_on_or_after_utc": "2026-11-18T10:00:00Z"}
    packet["request"].update(action="READBACK", pending_owner_screen=screen)
    client = Client(packet, fault)
    result = neo.NeoBrowserDriver(client).perform(packet)["result"]
    assert client.calls[0] == ("plan_substack_published", {})
    if fault:
        assert client.calls[1] == ("plan_substack_cancel_expired_code", {
            "draft_url": screen["page_url"], "cancel_on_or_after_utc": screen["cancel_on_or_after_utc"],
            "title": packet["request"]["native_payload"]["title"]})
        assert result.get("cancelled_owner_screen") == (screen if closed else None)
        assert not any(c[0] in {"open", "plan_substack_publish"} for c in client.calls)
    else:
        assert result["content_verified"] is True
        assert not any(c[0] == "plan_substack_cancel_expired_code" for c in client.calls)


@pytest.mark.parametrize("phase", ["plan_substack_publish", "plan_substack_confirm"])
def test_browser_publish_controls_apply_the_cutoff_before_clicking(phase):
    source = Path(neo.__file__).with_name("neo_endpoint_steps_v1.js")
    script = """
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const run = new AsyncFunction('page', 'input', fs.readFileSync(process.argv[1], 'utf8'));
Date.now = () => Date.parse('2026-11-18T10:00:00Z');
const clicks = [];
const page = {snapshot: async () => ({refs: [
  {role:'button', name:'Publish now', ref:'publish'}, {role:'button', name:'Publish on web only', ref:'web'}]}),
  evaluateInPage: async () => ({value:true}), click: async ref => clicks.push(ref)};
run(page, {phase:process.argv[2], plan_entry_deadline_utc:'2026-11-18T10:00:00Z'})
  .then(result => console.log(JSON.stringify({result,clicks})));
"""
    out = json.loads(subprocess.check_output(["node", "-e", script, str(source), phase], text=True, timeout=5))
    assert out["result"]["reason_code"] == "PLAN_ANALYSIS_ENTRY_WINDOW_ENDED_REVIEW_REQUIRED"
    assert out["result"]["definite_no_write"] is True
    assert out["clicks"] == []


@pytest.mark.parametrize("selection,expected", [("exact", ["e153"]), ("wrong_url", []), ("early", []), ("wrong_title", [])])
def test_browser_cancel_targets_only_the_expired_code_dialog(selection, expected):
    source = Path(neo.__file__).with_name("neo_endpoint_steps_v1.js")
    script = """
const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const run = new AsyncFunction('page', 'input', fs.readFileSync(process.argv[1], 'utf8'));
const selection = process.argv[2];
const draft = 'https://capitalchronicle.substack.com/publish/post/123';
const clicks = [];
Date.now = () => Date.parse(selection === 'early' ? '2026-11-18T09:59:59Z' : '2026-11-18T10:00:00Z');
const page = {
  snapshot: async () => ({url:selection === 'wrong_url' ? draft + '4' : draft,
    text:'- button "Cancel" [ref=unrelated]\\n' + (clicks.length ? '- button "Continue" [ref=e155]'
      : '- dialog "Check your email"\\n  - button "close" [ref=e150]\\n  - button "Cancel" [ref=e153]'),
    refs: clicks.length ? [{role:'button', name:'Continue', ref:'e155'}] : []}),
  evaluateInPage: async () => ({value:selection !== 'wrong_title'}),
  click: async ref => clicks.push(ref)
};
run(page, {phase:'plan_substack_cancel_expired_code', draft_url:draft, title:'A sourced page.',
    cancel_on_or_after_utc:'2026-11-18T10:00:00Z'}).then(result => console.log(JSON.stringify({result,clicks})));
"""
    out = json.loads(subprocess.check_output(["node", "-e", script, str(source), selection], text=True, timeout=5))
    assert out["clicks"] == expected
    assert out["result"]["closed"] is bool(expected)


def test_legacy_code_readback_reopens_only_the_observed_published_row(packet):
    packet["request"].update(action="READBACK", pending_owner_screen={
        "page_id": "1", "draft_id": "123", "legacy_published_dashboard_readback": True,
        "page_url": "https://capitalchronicle.substack.com/publish/post/123"})
    client = Client(packet)
    result = neo.NeoBrowserDriver(client).perform(packet)["result"]
    assert result["content_verified"] is True
    assert client.calls[1] == ("open", "plan-substack-owner-detail",
                               "https://capitalchronicle.substack.com/publish/posts/detail/123")
    assert [c[2]["ref"] for c in client.calls if c[0] == "act"] == ["Share"]
    assert any(c[:2] == ("open", "plan-substack-public") for c in client.calls)


@pytest.mark.parametrize("email",[True,None])
def test_email_or_missing_delivery_policy_makes_no_editor_action(packet,email):
    packet["request"]["substack_delivery_policy"]["email_send_enabled"]=email
    client=Client(packet)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="FAILED_BEFORE_WRITE"
    assert not any(c[0]=="act" for c in client.calls)


def test_upload_uses_interception_and_the_exact_bound_binary_path(packet,tmp_path):
    chart=tmp_path/"media_assets"/"chart.png"
    chart.parent.mkdir()
    Image.new("RGB",(800,450),"white").save(chart)
    asset={"path":str(chart),"sha256":sha256(chart.read_bytes()).hexdigest(),
        "caption":"Chart: TradingView.","alt_text":"The euro chart."}
    packet["request"]["content_binding"]["media_manifest"]=[asset]
    client=Client(packet)
    assert neo.NeoBrowserDriver(client).perform(packet)["result"]["status"]=="SUCCESS"
    phases=[c[0] for c in client.calls]
    assert phases.index("plan_substack_intercept")<next(i for i,c in enumerate(client.calls)
        if c[0]=="act" and c[2].get("ref")=="Insert image")
    assert next(c[1]["files"] for c in client.calls if c[0]=="upload")==[str(chart)]
    pasted=next(c[1]["html"] for c in client.calls if c[0]=="plan_substack_paste")
    assert pasted.index("<figure>")<pasted.index("<h2>Macro</h2>")


@pytest.mark.parametrize("fault,verified",[(None,True),("extra_body",False)])
def test_readback_requires_the_complete_body_without_extra_copy(packet,fault,verified):
    packet["request"].update(action="READBACK",public_object_id="123",
        public_object_url="https://capitalchronicle.substack.com/p/own")
    client=Client(packet,fault)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["content_verified"] is verified
    assert result["result"]["public_object_id"]=="123"
    assert not client.clicked


def test_table_and_minus_sign_survive_render_and_comparison():
    body="## Scenarios\n\n| Case | Odds |\n|---|---|\n| Main | 50% |\n| Alternative | 35% |\n\nResult: -1.0R."
    assert "<td>Main</td><td>50%</td>" in plan_neo.body_html(body)
    assert plan_neo.body_text(body)=="Scenarios Case Odds Main 50% Alternative 35% Result: -1.0R."


def test_measured_tables_reach_the_editor_as_native_rows(packet):
    packet["operation_id"]="cc536-measured-odds-2"
    packet["request"]["native_payload"]["body_markdown"]=(
        "Our historical record.\n\n## Short side\n\n| Rule | Trades | Mean R |\n|---|---|---|\n| Gold | 41 | -0.197 |")
    client=Client(packet)
    assert neo.NeoBrowserDriver(client).perform(packet)["result"]["status"]=="SUCCESS"
    pasted=next(c[1]["html"] for c in client.calls if c[0]=="plan_substack_paste")
    assert '<table>' not in pasted
    assert '<p><strong>Gold</strong> &emsp; 41 &emsp; -0.197</p>' in pasted


@pytest.mark.parametrize("spacing_only",[True,False])
def test_retained_measured_draft_repairs_only_proven_cell_spacing(packet,spacing_only):
    packet["operation_id"]="cc536-measured-odds-2"
    packet["request"]["native_payload"]["body_markdown"]="## Record\n\n| Rule | R |\n|---|---|\n| Gold | -0.197 |"
    client=Client(packet)
    client.resume_draft_url="https://capitalchronicle.substack.com/publish/post/123"
    original=client.run
    checks=[]
    def run(page,phase,**kw):
        if phase=="plan_substack_check":
            checks.append(1)
            return {"verified":len(checks)>1,"spacing_only_mismatch":spacing_only}
        return original(page,phase,**kw)
    client.run=run
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]==("SUCCESS" if spacing_only else "FAILED_BEFORE_WRITE")
    assert client.clicked is spacing_only
    assert not any(c[0]=="act" and c[2].get("ref")=="Create" for c in client.calls)


def test_plan_client_reuses_its_named_group_and_leaves_other_tasks_alone():
    client=neo.NeoMcpClient(task_name="cc466 plan pages",group_title="codex/cc466-plan-pages")
    calls=[]
    def call(name,args):
        calls.append((name,args))
        if name=='tabs':
            value='[50] https://capitalchronicle.substack.com/p/own (Own page)\n[48] https://x.com/Capitalnicle/status/old (Other task)'
        elif name=='tab_groups':
            value='[own] "codex/cc466-plan-pages" (green) pages: 50\n[other] "codex/cc436-automatic-posts" (pink) pages: 48'
        else:
            value='ok'
        return {'content':[{'type':'text','text':value}]}
    client.call=call
    assert client.open('plan-substack','https://capitalchronicle.substack.com/p/own')==50
    assert client.group=='own'
    assert not any(args.get('page')==48 or args.get('action')=='new' for _,args in calls)
    assert not any(name=='windows' for name,_ in calls)
