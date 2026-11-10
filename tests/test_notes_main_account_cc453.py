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


def test_uncertain_secondary_note_never_uses_new_accounts_empty_feed(tmp_path):
    store = copied_store(tmp_path)
    _, value = message(store, "substack_notes")
    packet = {"request": {"destination": "substack_notes", "action": "PUBLISH",
        "expected_identity": "@deancapitalchronicle", "intent_sha256": sha256_of(value)}}
    store.register_outbox_message(message_id="frozen-old-request", work_item_id=value["work_item_id"],
        destination="internal:native-neo-tool", payload=json.dumps(packet), status="NATIVE_NEO_INTERNAL")
    before = store.get_outbox_message("frozen-old-request")["payload"]
    request = NeoDestinationHandoff(store=store).request(destination="substack_notes", action="READBACK",
        intent=value)
    assert request["expected_identity"] == "@deancapitalchronicle"
    assert request["entry_url"] == "https://substack.com/@deancapitalchronicle"
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
