"""The three installed consumers recover the same request once, without writes."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import pytest

from live_contentops import light_model_caller_v1 as light
from live_contentops import image_quality_v1 as quality
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import x_reply_bot_v1 as replies
from test_image_templates_cc465 import asset
from copy import deepcopy


@pytest.fixture(autouse=True)
def installed_cli(monkeypatch):
    monkeypatch.setattr(light, "codex_executable", lambda: "codex.exe")


def fallback_runner(value, failure, calls):
    def run(args, *, cwd, timeout, input=None):
        calls.append({"args":args, "prompt":input, "cwd":cwd, "timeout":timeout})
        assert list(Path(cwd).iterdir()) == []
        if len(calls) == 1:
            assert args[0] == light.AGY
            message = json.loads(input)
            assert message["message"]["content"][0]["text"].startswith("Do not call any tool")
            if failure == "timeout":
                raise subprocess.TimeoutExpired(args, timeout, output=b"", stderr=b"partial error")
            if failure == "blank":
                return subprocess.CompletedProcess(args, 0, b" \n", b"")
            return subprocess.CompletedProcess(args, 0, json.dumps({"event":"result", "result":{
                "status":"SUCCESS", "response":"", "duration_seconds":timeout}}).encode(), b"")
        assert len(calls) == 2 and args[0] == "codex.exe"
        assert input.decode() == json.loads(calls[0]["prompt"])["message"]["content"][0]["text"]
        assert args[args.index("--model")+1] == "gpt-6.1-sol"
        assert 'model_reasoning_effort="low"' in args and 'forced_login_method="chatgpt"' in args
        assert args[args.index("--sandbox")+1] == "read-only" and args[-1] == "-"
        assert "--ignore-user-config" in args and "--ephemeral" in args
        for feature in ("shell_tool", "multi_agent", "view_image", "apps", "remote_plugin", "hooks"):
            assert any(args[i:i+2] == ["--disable",feature] for i in range(len(args)-1))
        assert not any("bypass" in arg for arg in args)
        Path(args[args.index("--output-last-message")+1]).write_text(json.dumps(value),encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, b'{"type":"turn.completed","usage":{"input_tokens":10}}', b"")
    return run


@pytest.mark.parametrize("role", ["image", "variants", "ranking"])
@pytest.mark.parametrize("failure", ["timeout", "empty", "blank"])
def test_each_consumer_uses_the_second_answer_and_records_caller_seconds(tmp_path, role, failure):
    calls=[]
    if role == "image":
        image=asset(tmp_path)
        output={"image_seen":True, "points":{str(i):True for i in range(1,11)},
            "reasons":{str(i):"Observed in the attached PNG." for i in range(1,11)}}
        record=quality.review_vision(image,runner=fallback_runner(output,failure,calls))
        assert record["status"] == "REVIEWED" and record["points"] == output["points"]
        args=calls[1]["args"]
        assert Path(args[args.index("--image")+1]) == Path(image["path"]).resolve()
        assert record["image_sha256"] == sha256(Path(image["path"]).read_bytes()).hexdigest()
        # The model cannot turn a failed deterministic check into a pass.
        checked=quality.code_check(image); checked["points"]["7"] = False
        assert not quality.combine(checked,record)["passed"]
    elif role == "variants":
        output={"hook":{"text":"Rates drive the market.","source_ids":["s0"]}}
        record=editorial.text_call("Return bound fields.",root=tmp_path,runner=fallback_runner(output,failure,calls))
        assert record["status"] == "RETURNED" and record["output"] == output
        assert editorial.text_call("Return bound fields.",root=tmp_path,runner=lambda *a,**k:pytest.fail("cached")) == record
    else:
        output={"ranking":[{"post_id":"source-post","quality_score":81,"reason":"Adds a relevant fact."}]}
        returned,record=replies._text_call("Return ranking.",root=tmp_path,runner=fallback_runner(output,failure,calls))
        assert returned == output and record["status"] == "RETURNED"
    saved=record["light_call"]
    assert len(calls) == 2 and saved["answered_by"] == record["answered_by"] == "codex"
    assert saved["configured_model"] == "gpt-6.1-sol" and saved["configured_effort"] == "low"
    assert saved["answer_seconds"] >= 0 and saved["elapsed_seconds"] >= saved["answer_seconds"]
    assert saved["first_cause"].startswith("AGY_") and saved["attempts"][0]["status"] != "RETURNED"
    assert json.loads(Path(saved["artifact_path"]).read_bytes()) == saved


@pytest.mark.parametrize("first", ["timeout", "empty"])
def test_second_failure_keeps_the_first_named_cause_and_never_retries(tmp_path, first):
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if first == "empty" and len(calls)==1:
            return subprocess.CompletedProcess(args,0,b'{"status":"SUCCESS","response":""}',b"")
        raise subprocess.TimeoutExpired(args,kwargs["timeout"],output=b"partial",stderr=b"partial error")
    answer,record=light.call_light("Exact request.",root=tmp_path,runner=run,
        timeout_cause="AGY_RANK_TIMEOUT_90S",empty_cause="AGY_RANK_EMPTY_RESPONSE")
    assert answer == b"" and len(calls)==2 and record["answered_by"] is None
    assert record["cause"] == ("AGY_RANK_TIMEOUT_90S" if first=="timeout" else "AGY_RANK_EMPTY_RESPONSE")
    assert record["fallback_cause"] == "CODEX_LIGHT_TIMEOUT_65S"
    assert (tmp_path/"antigravity-stdout.txt").read_bytes() == (b"partial" if first=="timeout" else b'{"status":"SUCCESS","response":""}')


@pytest.mark.parametrize("output,code", [(b'{"broken":',0), (b'{"status":"ERROR","response":"Denied"}',0), (b'bad',1)])
def test_invalid_or_rejected_nonempty_output_does_not_call_a_second_model(tmp_path,output,code):
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args,code,output,b"")
    _,record=light.call_light("Exact.",root=tmp_path,runner=run,timeout_cause="TIMEOUT",empty_cause="EMPTY")
    assert len(calls)==1


def test_an_empty_codex_jsonl_turn_cannot_reuse_a_previous_answer(tmp_path):
    (tmp_path/"codex-answer.txt").write_text('{"old":true}')
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        raw=b'{"status":"SUCCESS","response":""}' if len(calls)==1 else b'{"type":"turn.completed"}'
        return subprocess.CompletedProcess(args,0,raw,b"")
    answer,record=light.call_light("Exact.",root=tmp_path,runner=run,timeout_cause="TIMEOUT",empty_cause="EMPTY")
    assert answer==b"" and record["fallback_cause"]=="CODEX_LIGHT_EMPTY_RESPONSE"


def test_tool_action_is_not_accepted_as_a_codex_light_answer(tmp_path):
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        raw=b'' if len(calls)==1 else b'{"type":"item.completed","item":{"type":"mcp_tool_call"}}'
        return subprocess.CompletedProcess(args,0,raw,b"")
    _,record=light.call_light("Exact.",root=tmp_path,runner=run,timeout_cause="TIMEOUT",empty_cause="EMPTY")
    assert record["fallback_cause"]=="CODEX_LIGHT_TOOL_USE_REFUSED" and record["answered_by"] is None


def test_variant_consumer_still_checks_the_fallback_source_and_copy(tmp_path,monkeypatch):
    from test_plan_reader_copy_cc466 import source_and_fields
    source,fields=source_and_fields()
    calls=[]
    def checked(value,basis):
        calls.append(value)
        raise ValueError("SOURCE_NUMBER_MISMATCH")
    monkeypatch.setattr(editorial.reader,"validate_fields",checked)
    monkeypatch.setattr(editorial.reader,"attach_call",lambda row:{"reader_call_line":"Bound call.","conditional_calls":[]})
    def call(prompt,*,root,**kwargs):
        return editorial.text_call(prompt,root=root,runner=fallback_runner(fields,"empty",[]))
    result=editorial.prepare_variants({"reader_source":source},{"kind":"plan"},output_dir=tmp_path,call=call)
    assert result["status"]=="VARIANT_COPY_NEEDS_REPAIR" and result["cause"]=="SOURCE_NUMBER_MISMATCH"
    assert len(calls)==2 and all(r["answered_by"]=="codex" for r in result["calls"])


def test_next_variants_call_resumes_a_legacy_failure_once_without_rewriting_it(tmp_path):
    prompt="Retained exact prompt."
    key=sha256(("cc466-text-v4:writer300:variants-direct120\n"+prompt).encode()).hexdigest()
    path=tmp_path/key/"result.json";path.parent.mkdir()
    original=b'{"status":"FAILED","cause":"AGY_VARIANTS_TIMEOUT_120S"}'
    path.write_bytes(original)
    returned=editorial.text_call(prompt,root=tmp_path,runner=fallback_runner({"bound":True},"empty",[]))
    assert returned["status"]=="RETURNED" and returned["answered_by"]=="codex"
    assert path.read_bytes()==original and returned["artifact_path"]!=str(path)
    assert editorial.text_call(prompt,root=tmp_path,runner=lambda *a,**k:pytest.fail("already returned"))==returned


def test_changed_image_is_not_attached_after_the_first_timeout(tmp_path):
    image=tmp_path/"exact.png";image.write_bytes(b"original")
    calls=[]
    def run(args,**kwargs):
        calls.append(args);image.write_bytes(b"changed")
        raise subprocess.TimeoutExpired(args,kwargs["timeout"])
    _,record=light.call_light("Exact image.",root=tmp_path/"calls",image=image,runner=run,
        timeout_cause="AGY_VISION_TIMEOUT_125S",empty_cause="EMPTY")
    assert len(calls)==1 and record["fallback_cause"]=="IMAGE_REVIEW_BYTES_CHANGED"


def test_native_codex_adapter_uses_completed_turn_and_closed_stdin_instead_of_hanging_on_exit(tmp_path):
    program=("import json,sys,time; data=sys.stdin.read(); "
        "print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':data}}),flush=True); "
        "print(json.dumps({'type':'turn.completed'}),flush=True); time.sleep(20)")
    started=perf_counter()
    done=light._run_codex([sys.executable,'-c',program],cwd=str(tmp_path),timeout=8,input=b'{"eof":true}')
    assert done.returncode==0 and done.turn_completed
    assert light._codex_observations(done.stdout,{})==b'{"eof":true}'
    assert done.completion_seconds < 8 and perf_counter()-started < 15


def test_next_image_preparation_continues_legacy_failure_once_and_keeps_original_bytes(tmp_path,monkeypatch):
    from live_contentops import image_templates_v1 as templates
    image=asset(tmp_path)
    old_review={"status":"REVIEW_UNAVAILABLE","cause":"AGY_VISION_TIMEOUT_125S","points":{}}
    image["image_quality"]=quality.combine(quality.code_check(image),old_review)
    path=Path(image["path"]).with_suffix('.json')
    original=json.dumps(image).encode();path.write_bytes(original)
    monkeypatch.setattr(templates,'render',lambda *a,**k:deepcopy(image))
    monkeypatch.setattr(quality,'ACCEPTANCE_CONTROL',tmp_path/'absent-control.json')
    output={"image_seen":True,"points":{str(i):True for i in range(1,11)},
        "reasons":{str(i):"Observed attached image." for i in range(1,11)}}
    calls=[]
    returned=quality.prepare_asset({},'W',tmp_path,vision_runner=fallback_runner(output,'timeout',calls))
    review=returned['image_quality']['vision']
    assert review['answered_by']=='codex' and len(calls)==2
    assert Path(review['retained_prior_failure_path']).read_bytes()==original
    again=quality.prepare_asset({},'W',tmp_path,vision_runner=lambda *a,**k:pytest.fail('already reviewed'))
    assert again['image_quality']['vision']==review
