"""The one permitted reply can exist while its required original link is absent."""
import json
import subprocess

import pytest

from live_contentops import call_followups_v1 as f
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.neo_endpoint_executor_v1 import NeoBrowserDriver
from test_call_followup_missing_links_cc603 import parent
from test_call_followups_cc603 import ready, NOW
from test_plan_status_publication_cc306 import fake_host


PARENT = "https://substack.com/@capitalchronicle/note/c-603"
PUBLIC = "https://substack.com/@capitalchronicle/note/c-604"
ALIAS = "https://substack.com/profile/356792394-capital-chronicle/note/c-604"
TEXT = ("Original: https://t.me/CapitalChronicle/166\nRecord: https://t.me/CapitalChronicle/134\n\n"
        + posts.PUBLIC_NOTICE + " " + posts.CONFLICTS_NOTICE)
OBSERVED = TEXT.replace("https://t.me/CapitalChronicle/166", "").replace("https://t.me/CapitalChronicle/134", "")


def request():
    return {"action":"READBACK", "destination":"substack_notes", "request_sha256":"bound-readback",
        "work_item_id":"cc603-followup-" + "a" * 32 + "-missing-links", "expected_identity":"@capitalchronicle",
        "entry_url":PARENT, "reply_parent":{"public_object_id":"c-603", "public_object_url":PARENT},
        "content_binding":{"expected_text_segments":[TEXT], "media_manifest":[]}}


@pytest.mark.parametrize("failure", [None, "wrong_parent", "related_note", "changed_copy", "ambiguous", "wrong_author"])
def test_reader_identifies_only_one_exact_parent_reply_and_retains_its_content_failure(failure):
    class Client:
        url = PARENT

        def call(self, name, args):
            assert name == "navigate"
            self.url = args["url"]

        def wait(self, *args):
            pass

        def run(self, page, phase, **kwargs):
            assert phase == "readback"
            reply = {"public_object_url":ALIAS, "public_object_id":"c-604", "observed_text":OBSERVED,
                     "links":[], "public_image_urls":[], "reply_parent_url":PARENT, "reply_parent_id":"c-603"}
            if failure == "wrong_parent":
                reply["reply_parent_url"] = PARENT + "0"
            if failure == "related_note":
                reply.pop("reply_parent_url")
            if failure == "changed_copy":
                reply["observed_text"] += " A different claim."
            if self.url == PARENT:
                notes = [{"public_object_url":PARENT,"public_object_id":"c-603", "observed_text":"Original call."}, reply]
                if failure == "ambiguous":
                    notes.append({**reply,"public_object_id":"c-605","public_object_url":ALIAS.replace("604","605")})
                return {"url":PARENT,"notes":notes}
            assert self.url == ALIAS
            reply["public_object_url"] = PUBLIC if failure != "wrong_author" else PUBLIC.replace("@capitalchronicle", "@other")
            return {"url":reply["public_object_url"],"notes":[reply]}

    result = NeoBrowserDriver(Client()).readback(request(), 1)
    if failure:
        assert result["status"] == "READBACK_UNAVAILABLE"
        assert not result.get("public_object_id")
    else:
        assert result["public_object_id"] == "c-604" and result["public_object_url"] == PUBLIC
        assert result["content_verified"] is False
        assert result["observed_reply_parent_url"] == PARENT


@pytest.mark.parametrize("failure", [None, "parent", "author", "other_words", "request_hash", "object", "known_object"])
def test_unknown_reply_existence_never_counts_as_full_acceptance(failure):
    parent = {"public_object_id":"c-603","public_object_url":PARENT}
    intent = {"work_item_id":request()["work_item_id"], "plan_hash":"bound", "package_identity":"bound",
        "payload":TEXT,"native_payload":{"text":TEXT,"full_text":TEXT,"reply_to_id":"c-603","reply_to_url":PARENT},
        "destination_plan":{"surface":"SUBSTACK_NOTE","payload_hash":"bound-text"}}

    def execute(req):
        result = {"status":"SUCCESS","request_sha256":req["request_sha256"],"content_verified":False,
            "observed_identity":"@capitalchronicle","public_object_id":"c-604","public_object_url":PUBLIC,
            "observed_text":OBSERVED,"observed_reply_parent_id":parent["public_object_id"],
            "observed_reply_parent_url":parent["public_object_url"]}
        if failure == "parent": result["observed_reply_parent_url"] += "0"
        if failure == "author": result["observed_identity"] = "@other"
        if failure == "other_words": result["observed_text"] += " Different."
        if failure == "request_hash": result["request_sha256"] = "other"
        if failure == "object": result["public_object_url"] = PARENT
        return result

    observed = NeoDestinationHandoff(native_executor=execute).readback(destination="substack_notes",intent=intent,
        public_object_id="c-605" if failure == "known_object" else None,
        public_object_url=PUBLIC.replace("604", "605") if failure == "known_object" else None)
    assert observed["verified"] is False and observed["write_absent"] is False
    assert observed["content_binding_checks"]["text_match"] is False
    assert observed["write_exists"] is (failure is None)


def test_coordinator_settles_the_observed_gap_without_another_send_or_edit(parent, tmp_path, monkeypatch):
    store, transport, coordinator, original, observed, _ = parent
    original_bytes = store.get_outbox_message(original["key"])["payload"]
    child_key = f.queue_missing_links_reply(store, original["key"], observed_text=observed, now=NOW)["key"]
    child = posts._row_payload(store, child_key)
    child_bytes = store.get_outbox_message(child_key)["payload"]
    plan = posts.prepare_post(store, child_key, root=tmp_path, host=fake_host, destinations=("substack_notes",))
    posts.scope_to_post(coordinator, child_key, plan)
    coordinator.register_plan(child_key, plan)
    ids = coordinator._ids(child_key, plan["plan_hash"], "substack_notes")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack_notes",status="UNKNOWN_WRITE")

    def execute(req):
        text = child["text"].replace(original["candidate"]["original_url"], "").replace(original["record"]["url"], "")
        return {"status":"SUCCESS","request_sha256":req["request_sha256"],"observed_identity":"@capitalchronicle",
            "content_verified":False,"public_object_id":"c-604","public_object_url":PUBLIC,"observed_text":text,
            "observed_reply_parent_id":"c-603","observed_reply_parent_url":PARENT}

    monkeypatch.setattr(transport, "readback", lambda **kw: NeoDestinationHandoff(native_executor=execute).readback(**kw))
    result = coordinator.readback_existing_dispatch(ids["dispatch_id"])
    assert result["reconciliation_status"] == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
    assert store.get_platform_dispatch(ids["dispatch_id"])["public_object_id"] == "c-604"
    proof = json.loads(store.list_readbacks_for_dispatch(ids["dispatch_id"])[-1]["readback_data"])["readback"]
    assert proof["content_binding_checks"]["link_reply_gap"] is True
    assert proof["verified"] is False

    def unexpected(*args, **kwargs):
        raise AssertionError("a recorded copy gap needs no export, media, send or edit")

    monkeypatch.setattr(f, "discover", lambda *a: [])
    first = f.minute_due(store, unexpected, now=NOW, root=tmp_path, coordinator_for=unexpected, asset_for=unexpected)
    assert first["posts"][0]["status"] == "PUBLISHED_WITH_LINK_GAP"
    assert not f.pending_link_replies(store) and not f.post_complete(store, original)
    assert store.get_outbox_message(child_key)["status"] == "SETTLED"
    assert store.get_outbox_message(original["key"])["payload"] == original_bytes
    assert store.get_outbox_message(child_key)["payload"] == child_bytes
    f.run_due(store, {"status":{"plans":[]}}, now=NOW, root=tmp_path, coordinator_for=unexpected, asset_for=unexpected)
    assert transport.publish_calls == []


def test_rendered_note_reader_distinguishes_replies_from_related_articles():
    script = r"""
const fs=require('fs'),assert=require('assert');
const execute=new (Object.getPrototypeOf(async function(){}).constructor)('input','page',
  fs.readFileSync('live_contentops/neo_endpoint_steps_v1.js','utf8'));
const parent='https://substack.com/@capitalchronicle/note/c-603';
const link=url=>({href:url,innerText:'now',getClientRects:()=>[1],getAttribute:()=>null,querySelector:()=>null});
const root=url=>({querySelectorAll:s=>s==='a[href]'?[link(url)]:[],parentElement:null});
const permalink=root(parent),replyRoot=root('https://substack.com/profile/356792394-capital-chronicle/note/c-604');
const relatedRoot=root('https://substack.com/@capitalchronicle/note/c-605');
const node=(r,related=false)=>({innerText:'Original: Record: Notices.',getClientRects:()=>[1],
  closest:s=>s==='article'?(related?relatedRoot:null):r});
const own=node(permalink),reply=node(replyRoot),related=node(relatedRoot,true);
permalink.contains=e=>e===own;
global.location={href:parent};
global.document={querySelector:s=>s==='main [class*="feedPermalinkUnit"]'?permalink:{contains:()=>true},
  querySelectorAll:s=>s==='.FeedProseMirror'?[own,reply,related]:[]};
const page={evaluateInPage:async(fn,arg)=>({value:fn(arg)})};
(async()=>{const r=await execute({phase:'readback',expected_identity:'@capitalchronicle'},page);
  assert.equal(r.notes[0].reply_parent_url,undefined);
  assert.equal(r.notes[1].reply_parent_url,parent);
  assert.equal(r.notes[2].reply_parent_url,undefined);
})().catch(e=>{console.error(e);process.exit(1)});
"""
    subprocess.run(["node","-e",script],check=True,capture_output=True,text=True,timeout=10)
