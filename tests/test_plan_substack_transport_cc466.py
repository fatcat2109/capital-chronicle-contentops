"""Exercise the plan-page branch of the installed Neo transport, including lost clicks."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO

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
            ("checkbox","Send via email and the Substack app"),("button","Publish on web only")]
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
        if phase=="plan_substack_identity":
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
            return {"page_id":page,"gmail_page_id":2,"page_url":self.snapshot(page)["url"]}
        if phase=="plan_substack_published":
            return {"public_object_id":"123","public_object_url":"https://capitalchronicle.substack.com/p/own"}
        if phase=="plan_substack_readback":
            request=self.packet["request"]
            body=plan_neo.body_text(request["native_payload"]["body_markdown"])
            return {"status":"SUCCESS","public_object_url":request["public_object_url"],
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


@pytest.mark.parametrize("fault",["account","body","editor_error"])
def test_failure_before_click_is_a_definite_no_write(packet,fault):
    client=Client(packet,fault)
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="FAILED_BEFORE_WRITE"
    assert result["result"]["definite_no_write"] is True
    assert not client.clicked


def test_lost_publish_return_requires_readback_and_is_never_called_no_write(packet):
    client=Client(packet,"lost_click")
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="UNKNOWN_WRITE"
    assert result["result"]["definite_no_write"] is False
    assert client.clicked and result["dispatched_at_utc"]


def test_email_code_wait_hands_off_only_that_tab_without_reading_mail(packet):
    client=Client(packet,"code")
    result=neo.NeoBrowserDriver(client).perform(packet)
    assert result["result"]["status"]=="PENDING_JIM_EMAIL_CODE"
    handoff=next(i for i,c in enumerate(client.calls) if c[0]=="plan_substack_code_handoff")
    assert handoff==len(client.calls)-1
    assert not any(c[0]=="act" and c[2].get("ref")=="Publish on web only" for c in client.calls)


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
