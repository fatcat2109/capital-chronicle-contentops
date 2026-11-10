"""Main-account delivery and original-author recovery use the existing transport."""
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.neo_destination_handoff_v1 import IDENTITIES, ROOTS, NeoDestinationHandoff, _public_url
from test_neo_endpoint_executor_cc436 import copied_store, message


def intent():
    return {"work_item_id": "note", "plan_status_post": "note", "package_identity": "note",
            "native_payload": {"text": "The original conditional plan."},
            "destination_plan": {"payload_hash": "f" * 64}}


def test_new_note_identity_and_registry_use_main_publication():
    from live_contentops.destination_transport_registry_v1 import _SURFACES
    surface = next(s for s in _SURFACES if s.surface == "SUBSTACK_NOTE")
    assert surface.expected_identity == surface.expected_public_handle == IDENTITIES["substack_notes"] == "@capitalchronicle"
    assert ROOTS["substack_notes"] == "https://substack.com/@capitalchronicle"
    assert IDENTITIES["substack"] == "capitalchronicle.substack.com"
    assert not _public_url("substack_notes", "https://substack.com/@deancapitalchronicle/note/c-123")
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1",
            "operating_mode": "AUTONOMOUS_DEFAULT", "destination": "substack_notes",
            "dispatch_attempt_identity": "once", "work_item_id": "note", "payload_hash": "f" * 64}
    request = NeoDestinationHandoff().request(destination="substack_notes", action="PUBLISH",
                                              intent=intent(), authorization_context=auth)
    assert request["expected_identity"] == surface.expected_identity
    assert request["entry_url"] == ROOTS["substack_notes"]


@pytest.mark.parametrize("identity", ["@capitalchronicle", "@deancapitalchronicle"])
def test_exact_historical_note_keeps_url_author_and_content(identity):
    url = f"https://substack.com/{identity}/note/c-123"
    def executor(request):
        assert request["expected_identity"] == identity
        assert request["entry_url"] == f"https://substack.com/{identity}"
        return {"request_sha256": request["request_sha256"], "observed_identity": identity,
                "public_object_id": "c-123", "public_object_url": url,
                "observed_text": intent()["native_payload"]["text"], "content_verified": True}
    result = NeoDestinationHandoff(native_executor=executor).readback(destination="substack_notes",
        intent=intent(), public_object_id="c-123", public_object_url=url)
    assert result["verified"] is True
    assert result["public_object_url"] == url


@pytest.mark.parametrize("claimed", [False, True])
def test_uncertain_secondary_note_never_uses_new_accounts_empty_feed(tmp_path, claimed):
    store = copied_store(tmp_path)
    _, value = message(store, "substack_notes")
    packet = {"operation_id":value["work_item_id"], "request": {"destination": "substack_notes", "action": "PUBLISH",
        "request_sha256":"a"*64, "expected_identity": "@deancapitalchronicle", "intent_sha256": sha256_of(value)}}
    store.register_outbox_message(message_id="frozen-old-request", work_item_id=value["work_item_id"],
        destination="internal:native-neo-tool", payload=json.dumps(packet), status="NATIVE_NEO_INTERNAL")
    before = store.get_outbox_message("frozen-old-request")["payload"]
    if claimed:
        key="native-neo-"+sha256_of([value["work_item_id"],"a"*64,"started"])
        store.register_outbox_message(message_id=key,work_item_id=value["work_item_id"],
            destination="internal:native-neo-tool",payload=json.dumps({"native_invocation_id":"original"}),status="NATIVE_NEO_INTERNAL")
    request = NeoDestinationHandoff(store=store).request(destination="substack_notes", action="READBACK",
        intent=value)
    expected="@deancapitalchronicle" if claimed else "@capitalchronicle"
    assert request["expected_identity"] == expected
    assert request["entry_url"] == "https://substack.com/"+expected
    assert store.get_outbox_message("frozen-old-request")["payload"] == before


@pytest.mark.parametrize("destination,cause", [
    ("x", "X_NON_API_AUTOMATION_PROHIBITED"),
    ("substack", "SUBSTACK_ACCOUNT_SUSPENDED"),
    ("substack_notes", "SUBSTACK_ACCOUNT_SUSPENDED"),
])
def test_reopened_policy_claim_is_atomic_and_preserves_original_bytes(tmp_path, destination, cause):
    store = copied_store(tmp_path)
    ids, value = message(store, destination)
    before = store.get_outbox_message(ids["message_id"])["payload"]
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform=destination, status="DEFINITE_NO_WRITE")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
        work_item_id=value["work_item_id"], status=cause)
    claim = dict(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform=destination,
                 expected_status="DEFINITE_NO_WRITE", policy_no_write_cause=cause)
    assert store.claim_platform_dispatch_attempt(**claim)
    assert not store.claim_platform_dispatch_attempt(**claim)
    assert store.get_outbox_message(ids["message_id"])["payload"] == before


@pytest.mark.parametrize("protected", ["different_cause", "public_object", "uncertain"])
def test_reopening_policy_never_releases_a_different_or_ambiguous_attempt(tmp_path, protected):
    store = copied_store(tmp_path)
    ids, value = message(store, "substack_notes")
    status = "UNKNOWN_WRITE" if protected == "uncertain" else "DEFINITE_NO_WRITE"
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack_notes", status=status,
        public_object_id="c-123" if protected == "public_object" else None)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
        work_item_id=value["work_item_id"],
        status="OTHER_FAILURE" if protected == "different_cause" else "SUBSTACK_ACCOUNT_SUSPENDED")
    assert not store.claim_platform_dispatch_attempt(dispatch_id=ids["dispatch_id"],
        message_id=ids["message_id"], platform="substack_notes", expected_status=status,
        policy_no_write_cause="SUBSTACK_ACCOUNT_SUSPENDED")


@pytest.mark.parametrize("reconciled", [False, True])
def test_destination_failure_consumes_the_current_exact_readback(tmp_path, reconciled):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store = copied_store(tmp_path)
    ids, value = message(store, "substack_notes")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack_notes", status="DISPATCH_CONFIRMED", public_object_id="c-123",
        public_object_url="https://substack.com/@capitalchronicle/note/c-123")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],
        work_item_id=value["work_item_id"], status="RECONCILED_CONFIRMED" if reconciled else "RECONCILIATION_PENDING")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    detail = {"dispatch_id": ids["dispatch_id"], "status": "UNKNOWN_WRITE"}
    coordinator._record_destination_day_failure(value, "substack_notes", detail)
    incident_id, _ = coordinator._destination_failure_key("substack_notes")
    with store.get_read_only_connection() as conn:
        original = conn.execute("SELECT description FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()[0]
    failure = coordinator._destination_day_failure("substack_notes")
    assert (failure is None) is reconciled
    if failure:
        assert failure["dispatch_id"] == ids["dispatch_id"]
    with store.get_read_only_connection() as conn:
        assert conn.execute("SELECT description FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()[0] == original


@pytest.mark.parametrize("status", ["DEFINITE_NO_WRITE", "UNKNOWN_WRITE"])
def test_composer_refusal_never_poses_as_a_platform_outage(tmp_path, status):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store = copied_store(tmp_path)
    _, value = message(store, "substack_notes")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    detail = {"status": status, "safe_error_classification": "NEO_COMPOSER_PAYLOAD_MISMATCH"}
    coordinator._record_destination_day_failure(value, "substack_notes", detail)
    assert (coordinator._destination_day_failure("substack_notes") is None) is (status == "DEFINITE_NO_WRITE")
    # Historical incidents are also interpreted without changing their bytes.
    incident_id, _ = coordinator._destination_failure_key("substack_notes")
    if status == "DEFINITE_NO_WRITE":
        store.register_incident(incident_id=incident_id, work_item_id=value["work_item_id"],
                                severity="DISPATCH_FAILURE", description=json.dumps(detail))
        assert coordinator._destination_day_failure("substack_notes") is None


@pytest.mark.parametrize("cause,resolved", [("ValueError",True),("TRANSPORT_TIMEOUT",False)])
def test_proven_absence_clears_a_local_validation_failure_only(tmp_path,cause,resolved):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],
        platform='substack_notes',status='RECONCILED_ABSENT_SAFE_TO_RETRY')
    store.register_reconciliation(reconciliation_id=ids['reconciliation_id'],work_item_id=value['work_item_id'],
        status='RECONCILED_ABSENT_SAFE_TO_RETRY')
    c=DurablePublicationCoordinator(store=store,transport_runtime=None)
    c._record_destination_day_failure(value,'substack_notes',{'dispatch_id':ids['dispatch_id'],
        'status':'UNKNOWN_WRITE','safe_error_classification':cause})
    assert (c._destination_day_failure('substack_notes') is None) is resolved


def test_absence_clock_includes_the_latest_actual_native_action_claim(tmp_path):
    from datetime import datetime,timedelta
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    dispatch=store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],
        platform='substack_notes',status='UNKNOWN_WRITE')
    begun=(datetime.fromisoformat(dispatch['dispatched_at'])+timedelta(minutes=2)).isoformat()
    packet={'operation_id':value['work_item_id'],'request':{'action':'PUBLISH','destination':'substack_notes',
        'request_sha256':'b'*64,'dispatch_attempt_identity':ids['dispatch_id']}}
    store.register_outbox_message(message_id='actual-native-request',work_item_id=value['work_item_id'],
        destination='internal:native-neo-tool',payload=json.dumps(packet),status='NATIVE_NEO_INTERNAL')
    key='native-neo-'+sha256_of([value['work_item_id'],'b'*64,'started'])
    store.register_outbox_message(message_id=key,work_item_id=value['work_item_id'],destination='internal:native-neo-tool',
        payload=json.dumps({'begun_at_utc':begun}),status='NATIVE_NEO_INTERNAL')
    assert NeoDestinationHandoff(store=store)._absence_dispatch_clock(value,'substack_notes')[1]==begun


@pytest.mark.parametrize("actual,expected,authenticated", [
    ("@capitalchronicle", "@capitalchronicle", True),
    ("@deancapitalchronicle", "@capitalchronicle", False),
    ("@capitalchronicle", "@deancapitalchronicle", False),
])
def test_real_browser_identity_step_rejects_the_other_account(actual, expected, authenticated):
    source = Path(__file__).parents[1] / "live_contentops" / "neo_endpoint_steps_v1.js"
    code = """
const fs=require('fs');
const fn=new (Object.getPrototypeOf(async function(){}).constructor)('input','page',fs.readFileSync(process.argv[1],'utf8'));
const actual=process.argv[2], expected=process.argv[3];
fn({phase:'identity',destination:'substack_notes',expected_identity:expected},
   {snapshot:async()=>({url:'https://substack.com/'+actual,text:actual,
     refs:[{role:'link',name:actual},{role:'button',name:'Edit profile'}]})})
 .then(value=>console.log(JSON.stringify(value)));
"""
    result = subprocess.run(["node", "-e", code, str(source), actual, expected],
                            capture_output=True, text=True, check=True, timeout=10)
    observed = json.loads(result.stdout)
    assert observed["authenticated"] is authenticated
    assert observed["observed_identity"] == (expected if authenticated else None)


@pytest.mark.parametrize("author,expected,count", [
    ("@capitalchronicle", "@capitalchronicle", 1),
    ("@deancapitalchronicle", "@deancapitalchronicle", 1),
    ("@deancapitalchronicle", "@capitalchronicle", 0),
])
def test_real_note_dom_readback_uses_the_bound_author(author, expected, count):
    source = Path(__file__).parents[1] / "live_contentops" / "neo_endpoint_steps_v1.js"
    code = """
const fs=require('fs');
const fn=new (Object.getPrototypeOf(async function(){}).constructor)('input','page',fs.readFileSync(process.argv[1],'utf8'));
const url='https://substack.com/'+process.argv[2]+'/note/c-123';
const link={innerText:'time',href:url,getAttribute:()=>null,getClientRects:()=>[1],querySelector:()=>null};
const owner={parentElement:null,querySelectorAll:s=>s==='a[href]'?[link]:[]};
const note={innerText:'Bound original copy',getClientRects:()=>[1],closest:()=>owner};
global.location={href:url};
global.document={querySelectorAll:s=>s==='main .FeedProseMirror'?[note]:[]};
fn({phase:'readback',expected_identity:process.argv[3]},
   {evaluateInPage:async(f,arg)=>({value:f(arg)})}).then(value=>console.log(JSON.stringify(value)));
"""
    result = subprocess.run(["node", "-e", code, str(source), author, expected],
                            capture_output=True, text=True, check=True, timeout=10)
    observed = json.loads(result.stdout)
    assert len(observed["notes"]) == count
    if count:
        assert observed["notes"][0]["public_object_url"] == f"https://substack.com/{author}/note/c-123"


@pytest.mark.parametrize("changed", [False, True])
def test_long_note_publish_checks_every_word_before_the_click(changed):
    source = Path(__file__).parents[1] / "live_contentops" / "neo_endpoint_steps_v1.js"
    code = """
const fs=require('fs');
const fn=new (Object.getPrototypeOf(async function(){}).constructor)('input','page',fs.readFileSync(process.argv[1],'utf8'));
const expected='Condition 1.1234. '+('The original full analysis remains bound. '.repeat(180));
const actual=process.argv[2]==='changed'?expected.replace('1.1234','9.8765'):expected+'\\n\\n';
const editor={innerText:actual,getClientRects:()=>[1]};
const dialog={querySelectorAll:()=>[editor]};
global.document={querySelector:()=>dialog,querySelectorAll:()=>[editor]};
let clicks=0;
fn({phase:'publish',destination:'substack_notes',posts:[expected]}, {
 snapshot:async()=>({refs:[{role:'button',name:'Post',ref:'post'}]}),
 evaluateInPage:async(f,arg)=>{const value=f(arg);return Array.isArray(value)?
   {writtenToFile:true,path:'documented-long-editor-output'}:{value};},
 click:async()=>{clicks++;}
}).then(value=>console.log(JSON.stringify({status:value.status,clicks})));
"""
    result = subprocess.run(["node", "-e", code, str(source), "changed" if changed else "same"],
                            capture_output=True, text=True, check=True, timeout=10)
    observed = json.loads(result.stdout)
    assert observed["clicks"] == (0 if changed else 1)
    assert observed["status"] == ("FAILED_BEFORE_WRITE" if changed else "CLICKED")
