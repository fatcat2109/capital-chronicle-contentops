"""Controlled terminal-window/result routing; no live message or publication."""
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

import live_contentops.native_desktop_schedule_binding_v1 as schedule
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired

AUTO = "v1-newsroom-london-1700"


def at(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setattr(schedule, "llm_operator_pause_active", lambda:False)
    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only", lambda **_:([], {}))
    monkeypatch.setattr(schedule, "observed_quota_stop", lambda *_a, **_k:None)
    rollout={"schema_version":schedule.SCHEMA,"store_path":str(tmp_path/"state.sqlite3"),
        "published_output_root":str(tmp_path/"published"),"editorial_output_root":str(tmp_path/"output"),
        "feed_pointer_path":str(tmp_path/"feed.json"),"public_write_authority":False}
    entry=schedule.scheduled_binding(rollout,AUTO,now=at("2026-10-29T10:01:00Z"))
    binding=json.loads(Path(entry["binding_path"]).read_bytes())
    store=ContentOpsDurableStore(rollout["store_path"],auto_migrate=False)
    return store,rollout,entry,binding


def finish(store,binding,cause="SOURCE_AMBIGUITY"):
    work="cc-opportunity-"+sha256_of(binding["run_id"])
    store.create_work_item(story_id=work,work_item_id=work,title="Controlled terminal story",target_surface="TEST")
    result={"classification":"NATIVE_PRE_WRITER_EDITION_COMPLETE","qualified_article_count":0,
        "candidate_outcomes":[{"candidate_id":"controlled-"+str(binding["slot_ordinal"]),
            "outcome":"HOLD","primary_cause":cause}]}
    store.register_outbox_message(message_id="cc-editorial-final-"+sha256_of(binding["run_id"]),
        work_item_id=work,destination="internal:native-desktop-editorial",status="EDITORIAL_INTERNAL",
        payload=canonical_bytes(result).decode())
    Path(binding["output_dir"],"native_desktop_result.json").write_bytes(canonical_bytes(result))


def finish_window(window):
    store,rollout,entry,binding=window
    finish(store,binding)
    second=schedule.scheduled_binding(rollout,AUTO,now=at("2026-10-29T10:05:00Z"),continue_after=binding["run_id"])
    binding=json.loads(Path(second["binding_path"]).read_bytes())
    finish(store,binding,"SOURCE_MISSING")
    return store,rollout,entry,binding


def prepare(data,**response):
    store,rollout,entry,binding=data
    return schedule.prepare_window_result(store,rollout,binding,{"startup_result":entry,**response},
        now=at("2026-10-29T10:15:00Z"))


def test_candidate_hold_cannot_finish_an_eligible_window(window):
    store,_,_,binding=window
    finish(store,binding)
    result=prepare(window)
    assert result["reason"]=="ANOTHER_ADMITTED_CANDIDATE_OR_SLOT_ELIGIBLE"
    assert not store.get_outbox_message(schedule._window_result_key(binding))


def pending_role(window):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn,DesktopInputRequired
    store,_,_,binding=window
    work="cc-opportunity-"+sha256_of(binding["run_id"])
    store.create_work_item(story_id=work,work_item_id=work,title="Controlled pending role",target_surface="TEST")
    turn=NativeDesktopTurn(store,run_id=binding["run_id"],output_dir=binding["output_dir"],owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=binding["run_id"]+":select",prompt="Controlled role",governed_input={},validator=lambda raw:None)
    return turn,pending.value.request


def test_expired_stopped_process_saves_real_window_result_without_native_return(window,tmp_path):
    store,rollout,entry,binding=window
    turn,request=pending_role(window)
    path=tmp_path/"observed-stop.json"
    evidence={"run_id":binding["run_id"],"turn_status":"completed","active_native_role":False,
        "source_thread_id":"CONTROLLED_TEST_THREAD","source_turn_id":"CONTROLLED_TEST_TURN",
        "observation_source":"CONTROLLED_TEST_NOT_LIVE_THREAD","pending_stage":"select",
        "pending_request_sha256":request["request_sha256"]}
    path.write_text(json.dumps(evidence))
    response={"artifact_path":str(path),"outcome":"PROCESS_FAILURE","first_cause":"COORDINATOR_STOPPED_WITH_EXECUTABLE_STAGE",
        "reason":"Controlled completed coordinator left a request unassigned. No quota or tool error was recorded.","startup_result":entry}
    with pytest.raises(ValueError,match="EXPIRED_EXACT_LAST_WINDOW_REQUIRED"):
        schedule.close_expired_window(store,rollout,binding,response,now=at("2026-10-29T10:15:00Z"))
    result=schedule.close_expired_window(store,rollout,binding,response,now=at("2026-10-29T13:15:00Z"))
    assert result["classification"]=="WINDOW_RESULT_SAVED"
    assert result["terminal_result"]["outcome"]=="TERMINAL_PROCESS_FAILURE"
    assert result["terminal_result"]["canonical_items"]==[]
    assert turn._get("select","response") is None
    assert turn.frozen_request("select")["request_sha256"]==request["request_sha256"]
    assert schedule.close_expired_window(store,rollout,binding,response,now=at("2026-10-29T13:16:00Z"))["reason"]=="RESULT_ALREADY_SAVED"


def test_real_blocker_dedupes_in_existing_window_and_records_one_actual_send(window,tmp_path):
    store,_,_,binding=window
    turn,request=pending_role(window)
    path=tmp_path/"failure.json"
    path.write_text(json.dumps({"run_id":binding["run_id"],"observation_source":"CONTROLLED_TEST"}))
    response={"stage":"select","request_sha256":request["request_sha256"],"first_cause":"NATIVE_PLATFORM_UNAVAILABLE",
        "blocker":"Controlled native result transport unavailable","unable_to_continue":True,"active_native_role":False,
        "smallest_next_action":"Restore the supported native return tool","responsible_owner":"L2 platform owner",
        "artifact_path":str(path),"delivered":"Input frozen, no model result"}
    result=schedule.window_blocked_notice(store,binding,response)
    assert result["classification"]=="WINDOW_BLOCKED_SAVED"
    assert not schedule._window_result_path(binding).exists()
    same=schedule.window_blocked_notice(store,binding,{**response,"blocker":"Same blocker with clearer explanation"})
    assert same["reason"]=="BLOCKER_ALREADY_SAVED"
    ref={"blocker_id":result["blocker_id"]}
    started=schedule.window_blocked_notice(store,binding,ref,begin=True)
    assert started["arguments"]["threadId"]==schedule.WINDOW_REPORT_L2
    assert "BLOCKED" in started["arguments"]["prompt"] and "not a terminal" in started["arguments"]["prompt"]
    assert schedule.window_blocked_notice(store,binding,ref,begin=True)["reason"]=="ATTEMPT_STARTED"
    actual={"isError":False,"content":[{"type":"text","text":json.dumps({"threadId":schedule.WINDOW_REPORT_L2})}]}
    assert schedule.window_blocked_notice(store,binding,{**ref,"tool_result":actual},record=True)["classification"]=="WINDOW_BLOCKED_DELIVERED"
    assert schedule.window_blocked_notice(store,binding,ref,begin=True)["reason"]=="DELIVERED"
    assert turn._get("select","response") is None
    other=schedule.window_blocked_notice(store,binding,{**response,"first_cause":"OTHER_LANE"})
    assert other["classification"]=="WINDOW_BLOCKED_SAVED" and other["blocker_id"]!=ref["blocker_id"]


@pytest.mark.parametrize("kind",["QUOTA","TURN_END","GUARD","DUPLICATE","EARLY"])
def test_blocked_owner_suppresses_nonactionable_interruptions(window,kind):
    store,_,_,binding=window
    assert schedule.window_blocked_notice(store,binding,{"interruption_kind":kind})["classification"]=="WINDOW_BLOCKED_SUPPRESSED"


def test_functioning_pending_child_cannot_become_blocked(window):
    store,_,_,binding=window
    with pytest.raises(ValueError,match="GENUINE_BLOCKED_WINDOW_EVIDENCE_REQUIRED"):
        schedule.window_blocked_notice(store,binding,{"active_native_role":True,"unable_to_continue":False})


def test_one_saved_aggregate_precedes_tool_attempt_and_success_deduplicates(window):
    data=finish_window(window)
    store,rollout,entry,binding=data
    binding_bytes=Path(binding["output_dir"],"native_operation_binding.json").read_bytes()
    result=prepare(data)
    assert result["classification"]=="WINDOW_RESULT_SAVED"
    assert result["terminal_result"]["outcome"]=="NO_ARTICLE"
    assert len(result["terminal_result"]["run_ids"])==2
    assert result["terminal_result"]["first_blocking_causes"]=={"SOURCE_AMBIGUITY":1,"SOURCE_MISSING":1}
    saved=json.loads(Path(result["artifact_path"]).read_bytes())
    assert saved["notice_delivery"]["state"]=="READY"
    started=schedule.window_notice_delivery(store,binding,begin=True)
    assert started["arguments"]["threadId"]==schedule.WINDOW_REPORT_L2
    assert started["arguments"]["hostId"]=="local" and "GMT+7" in started["arguments"]["prompt"]
    assert result["artifact_path"] in started["arguments"]["prompt"]
    assert schedule.window_notice_delivery(store,binding,begin=True)["reason"]=="ATTEMPT_STARTED"
    actual={"isError":False,"content":[{"type":"text","text":json.dumps({"threadId":schedule.WINDOW_REPORT_L2})}]}
    assert schedule.window_notice_delivery(store,binding,response=actual)["classification"]=="WINDOW_NOTICE_DELIVERED"
    assert schedule.window_notice_delivery(store,binding,begin=True)["reason"]=="DELIVERED"
    assert prepare(data)["reason"]=="RESULT_ALREADY_SAVED"
    assert Path(binding["output_dir"],"native_operation_binding.json").read_bytes()==binding_bytes


@pytest.mark.parametrize("entry_class",["NOT_YET_EFFECTIVE","OUTSIDE_EXACT_NATIVE_WINDOW",
    "NATIVE_WINDOW_COMPLETE","CODEX_QUOTA_STOP","NATIVE_DESKTOP_INPUT_REQUIRED"])
def test_guard_stale_partial_and_quota_entries_never_prepare_notice(window,entry_class):
    store,rollout,entry,binding=finish_window(window)
    entry={**entry,"classification":entry_class}
    assert prepare((store,rollout,entry,binding))["classification"]=="WINDOW_NOTICE_SUPPRESSED"
    assert not schedule._window_result_path(binding).exists()


def test_terminal_duplicate_and_stale_callback_do_not_wake_l2(window):
    store,rollout,entry,binding=finish_window(window)
    duplicate={**entry,"classification":"NATIVE_WINDOW_OPERATION_COMPLETE","run_id":binding["run_id"]}
    assert prepare((store,rollout,duplicate,binding))["reason"]=="DUPLICATE_OR_UNCHANGED_TERMINAL_CALLBACK"
    stale={**entry,"actual_entry_utc":"2026-10-28T10:01:00Z"}
    assert prepare((store,rollout,stale,binding))["reason"]=="STALE_CALLBACK"


@pytest.mark.parametrize("tool_result",[{"isError":True,"error":"controlled transport failure"},
    {"isError":False,"threadId":"wrong-target"}, {"error":"transport raised before a return"}])
def test_failure_is_saved_and_never_retried_or_called_success(window,tool_result):
    data=finish_window(window)
    store,_,_,binding=data
    prepare(data)
    schedule.window_notice_delivery(store,binding,begin=True)
    result=schedule.window_notice_delivery(store,binding,response=tool_result)
    assert result["classification"]=="WINDOW_NOTICE_FAILED" and result["retry_allowed"] is False
    saved=json.loads(schedule._window_result_path(binding).read_bytes())
    assert saved["notice_delivery"]["tool_result"]==tool_result
    assert schedule.window_notice_delivery(store,binding,begin=True)["reason"]=="FAILED"


def test_unfinished_native_child_is_not_a_terminal_process_failure(window):
    store,rollout,entry,binding=window
    work="cc-opportunity-"+sha256_of(binding["run_id"])
    store.create_work_item(story_id=work,work_item_id=work,title="Controlled pending child",target_surface="TEST")
    turn=NativeDesktopTurn(store,run_id=binding["run_id"],output_dir=binding["output_dir"])
    with pytest.raises(DesktopInputRequired):
        turn(logical_invocation_id=binding["run_id"]+":select",prompt="Controlled pending role",
            governed_input={"cutoff_utc":binding["cutoff_utc"]},validator=lambda raw:(True,None,json.loads(raw),None))
    result=prepare(window)
    assert result["reason"]=="UNFINISHED_NATIVE_ROLE"


def test_actual_terminal_process_error_reports_its_cause_but_quota_does_not(window,tmp_path):
    store,_,_,binding=window
    artifact=tmp_path/"actual-cli-error.json"
    artifact.write_text(json.dumps({"classification":"NATIVE_DESKTOP_BLOCKED","blocker":"CONTROLLED_DECODER_ERROR",
        "run_id":binding["run_id"],"command":"advance"}))
    response={"terminal_failure":{"operation":"advance","artifact_path":str(artifact),
        "why_terminal":"Controlled persistent decoder defect prevents further slots in this window.","continuation_possible":False}}
    result=prepare(window,**response)
    assert result["terminal_result"]["outcome"]=="TERMINAL_PROCESS_FAILURE"
    assert result["terminal_result"]["first_blocking_causes"]=={"SOFTWARE_PROCESS_DEFECT":1}


def test_wrong_run_or_quota_error_cannot_be_relabelled_as_terminal_failure(window,tmp_path):
    _,_,_,binding=window
    artifact=tmp_path/"error.json"
    response={"terminal_failure":{"operation":"advance","artifact_path":str(artifact),
        "why_terminal":"Controlled persistent defect.","continuation_possible":False}}
    artifact.write_text(json.dumps({"classification":"NATIVE_DESKTOP_BLOCKED","blocker":"CONTROLLED_ERROR",
        "run_id":"other-run","command":"advance"}))
    assert prepare(window,**response)["reason"]=="EXACT_TERMINAL_PROCESS_ERROR_REQUIRED"
    artifact.write_text(json.dumps({"classification":"NATIVE_DESKTOP_BLOCKED","blocker":"CODEX_QUOTA_STOP",
        "run_id":binding["run_id"],"command":"advance"}))
    assert prepare(window,**response)["reason"]=="CODEX_QUOTA_STOP"


def test_real_europe_guard_classification_has_no_reporting_side_effect(window):
    store,rollout,entry,binding=window
    guarded={**binding,"automation_id":"v1-newsroom-brief-europe-1500"}
    before=len(store.list_outbox_messages())
    assert schedule.prepare_window_result(store,rollout,guarded,{"startup_result":{
        "classification":"NOT_YET_EFFECTIVE","actual_entry_utc":"2026-10-29T08:01:03.250817+00:00"}},
        now=at("2026-10-29T08:01:04Z"))["reason"]=="NOT_YET_EFFECTIVE"
    assert len(store.list_outbox_messages())==before


def test_old_quota_observation_does_not_hide_a_later_genuine_terminal_result(window,monkeypatch):
    data=finish_window(window)
    monkeypatch.setattr(schedule,"observed_quota_stop",lambda *_a,**_k:{"cause":"CODEX_QUOTA_STOP"})
    assert prepare(data)["classification"]=="WINDOW_RESULT_SAVED"


def test_canonical_ids_are_distinct_and_channel_states_keep_their_actual_meaning(window,monkeypatch):
    data=finish_window(window)
    entries=[{"destination":"substack","status":"DISPATCH_CONFIRMED","reconciliation_status":"RECONCILED_CONFIRMED",
        "public_object_id":"controlled-123","public_object_url":"https://capitalchronicle.substack.com/p/controlled-fixture"},
        {"destination":"telegram","status":"DISPATCH_CONFIRMED","reconciliation_status":"RECONCILED_CONFIRMED","public_object_id":"tg-1"},
        {"destination":"instagram_business","status":"SKIPPED_PHOTOLESS_NEWS_POLICY"},
        {"destination":"facebook_page","status":"DELIVERY_FAILED"},
        {"destination":"linkedin","status":"UNKNOWN_WRITE"}]
    monkeypatch.setattr("live_contentops.native_desktop_publication_v1.publication_projection",lambda *_a,**_k:{"destinations":entries})
    result=prepare(data)["terminal_result"]
    assert len(result["canonical_items"])==1
    assert result["channels"]["confirmed"]=={"substack":1,"telegram":1}
    assert result["channels"]["skipped"]=={"instagram_business":2}
    assert result["channels"]["failed"]=={"facebook_page":2}
    assert result["channels"]["unresolved"]=={"linkedin":2}


def test_prompt_only_amendment_keeps_issued_slot_and_real_policy_identity(window):
    store,rollout,entry,binding=window
    finish(store,binding)
    before=Path(binding["output_dir"],"native_operation_binding.json").read_bytes()
    changed={**rollout,"tasks":[{"id":AUTO,"prompt":"new reporting clause"}]}
    # Original task metadata must be in the old routing, not invented by compatibility.
    original={**rollout,"tasks":[{"id":AUTO,"prompt":"old prompt"}]}
    checkpoint=store.get_outbox_message("native-window-"+sha256_of(binding["window_id"]))
    value=json.loads(checkpoint["payload"])
    value["rollout_sha256"]=sha256_of(original)
    store.finalize_outbox_payload_before_dispatch(message_id=checkpoint["message_id"],payload=canonical_bytes(value).decode(),status="EDITORIAL_INTERNAL")
    routing={**changed,"tasks":[{"id":AUTO}]}
    changed["terminal_reporting_prompt_compatibility"]={"previous_rollout_sha256":sha256_of(original),
        "unchanged_routing_sha256":sha256_of(routing)}
    next_slot=schedule.scheduled_binding(changed,AUTO,now=at("2026-10-29T10:05:00Z"),continue_after=binding["run_id"])
    assert next_slot["slot_ordinal"]==2
    assert Path(binding["output_dir"],"native_operation_binding.json").read_bytes()==before
    changed["public_write_authority"]=True
    with pytest.raises(ValueError,match="ROLLOUT_CHANGED"):
        schedule._issue_due_slot(store,changed,AUTO,value["window"],value["production_day_id"],[],
            binding["run_id"],now=at("2026-10-29T10:06:00Z"))
