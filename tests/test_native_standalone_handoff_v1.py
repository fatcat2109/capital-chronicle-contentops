import json

import pytest

from live_contentops import native_desktop_schedule_binding_v1 as owner
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes,sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def setup(tmp_path):
    run="standalone-controlled"
    store=ContentOpsDurableStore(tmp_path/"store.sqlite3")
    work="cc-opportunity-"+sha256_of(run)
    store.create_work_item(story_id=work,work_item_id=work,title="Controlled standalone task",target_surface="TEST")
    binding={"run_id":run,"output_dir":str(tmp_path),"store_path":str(tmp_path/"store.sqlite3"),
        "cutoff_utc":"2026-10-30T02:00:00Z","owner_manual_validation":True}
    store.register_outbox_message(message_id="native-operation-binding-"+sha256_of(run),work_item_id=work,
        destination="internal:native-desktop-editorial",payload=canonical_bytes(binding).decode(),status="EDITORIAL_INTERNAL")
    response={"entry_path":"newsroom","source_context":{"source_role":"STANDALONE_TASK",
        "source_thread_id":"01a17cce-4439-7161-b20b-d580b080c068","source_turn_id":"CONTROLLED_TEST"},
        "actual_entry_gmt7":"2026-10-30 09:00:00 GMT+7","next_action":"No remaining task action","next_actor":"L2 ContentOps"}
    return store,binding,response


def finish(store,binding):
    value={"classification":"NATIVE_PRE_WRITER_EDITION_COMPLETE","qualified_article_count":0,
        "candidate_outcomes":[{"candidate_id":"controlled","outcome":"HOLD","primary_cause":"SOURCE_AMBIGUITY"}]}
    store.register_outbox_message(message_id="cc-editorial-final-"+sha256_of(binding["run_id"]),
        work_item_id="cc-opportunity-"+sha256_of(binding["run_id"]),destination="internal:native-desktop-editorial",
        payload=canonical_bytes(value).decode(),status="EDITORIAL_INTERNAL")


def test_standalone_terminal_sender_requires_actual_result_and_fences_one_failure(tmp_path):
    store,binding,response=setup(tmp_path)
    with pytest.raises(ValueError,match="ACTUAL_TERMINAL_STANDALONE_RESULT_REQUIRED"):
        owner.prepare_standalone_result(store,binding,response)
    finish(store,binding)
    saved=owner.prepare_standalone_result(store,binding,response)
    assert saved["classification"]=="WINDOW_RESULT_SAVED" and saved["terminal_result"]["canonical_items"]==[]
    started=owner.window_notice_delivery(store,binding,begin=True)
    assert started["arguments"]["threadId"]==owner.WINDOW_REPORT_L2
    assert response["source_context"]["source_thread_id"] in started["arguments"]["prompt"]
    assert "09:00:00 GMT+7" in started["arguments"]["prompt"]
    assert owner.window_notice_delivery(store,binding,response={"isError":True,"error":"CONTROLLED_FAILURE"})["classification"]=="WINDOW_NOTICE_FAILED"
    assert owner.window_notice_delivery(store,binding,begin=True)["reason"]=="FAILED"
    assert owner.prepare_standalone_result(store,binding,response)["reason"]=="RESULT_ALREADY_SAVED"


def test_distinct_blocked_task_does_not_fence_its_later_terminal_handoff(tmp_path):
    store,binding,response=setup(tmp_path)
    artifact=tmp_path/"actual-blocker.json"
    artifact.write_text(json.dumps({"run_id":binding["run_id"],"observation_source":"CONTROLLED_TEST",
        "source_thread_id":response["source_context"]["source_thread_id"]}))
    blocked={**response,"stage":"source-access","first_cause":"SOURCE_ACCESS_BLOCKED",
        "blocker":"Controlled unavailable source","unable_to_continue":True,"active_native_role":False,
        "smallest_next_action":"Source owner restores exact document","responsible_owner":"Source owner","artifact_path":str(artifact)}
    first=owner.window_blocked_notice(store,binding,blocked)
    ref={"blocker_id":first["blocker_id"]}
    owner.window_blocked_notice(store,binding,ref,begin=True)
    actual={"isError":False,"threadId":owner.WINDOW_REPORT_L2}
    assert owner.window_blocked_notice(store,binding,{**ref,"tool_result":actual},record=True)["classification"]=="WINDOW_BLOCKED_DELIVERED"
    finish(store,binding)
    assert owner.prepare_standalone_result(store,binding,response)["classification"]=="WINDOW_RESULT_SAVED"
    assert owner.window_notice_delivery(store,binding,begin=True)["classification"]=="WINDOW_NOTICE_SEND_ONCE"
    assert owner.window_notice_delivery(store,binding,response=actual)["classification"]=="WINDOW_NOTICE_DELIVERED"
    value=json.loads(store.get_outbox_message(owner._window_result_key(binding))["payload"])
    assert value["blocked_notices"][ref["blocker_id"]]["notice_delivery"]["state"]=="DELIVERED"
    assert value["notice_delivery"]["state"]=="DELIVERED"


def test_engineering_context_cannot_claim_standalone_slice_completion(tmp_path):
    store,binding,response=setup(tmp_path)
    finish(store,binding)
    response["source_context"]["source_role"]="ENGINEERING_BUILDER"
    with pytest.raises(ValueError,match="ACTUAL_STANDALONE_TASK_CONTEXT_REQUIRED"):
        owner.prepare_standalone_result(store,binding,response)
