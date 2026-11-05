"""CC-300 (Jim, 5 Nov: Codex is over its weekly quota): a Claude Code session runs an operation's
editorial stages through the same gates, under its own true labels. Controlled protocol checks
only; these fixtures do not prove a model invocation."""
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    CLAUDE_MODEL, CONFIGURED_NOT_OBSERVED, DesktopInputRequired, NativeDesktopTurn, editorial_agent_of,
)
from live_contentops.native_editorial_continuation_v1 import next_editorial_action
from test_native_configured_provenance_v1 import configured

SESSION = "claude-code-session:7e6d9e4c-70b1-4f8d-a990-2f964934227e"


def claude(**change):
    """A Claude Code session's labels: model as its system prompt states it, effort as configured."""
    return {"surface": "CLAUDE_CODE_SESSION", "invocation_id": SESSION, "speed": "standard",
            "observation_source": "CONTROLLED_TEST_NOT_NATIVE_EXECUTION_PROOF",
            "model": CLAUDE_MODEL, "reasoning_effort": None,
            "configuration_status": CONFIGURED_NOT_OBSERVED, "configured_model": CLAUDE_MODEL,
            "configured_reasoning_effort": "max", "configuration_source": "Claude Code session effort setting",
            "actual_configuration_unavailable": True, **change}


def turn_for(tmp_path, agent):
    run = "cc300-" + agent
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    binding = {"run_id": run, "output_dir": str(tmp_path), **({"editorial_agent": agent} if agent != "codex" else {})}
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of(run), work_item_id=work,
        destination="internal:native-desktop-editorial", payload=canonical_bytes(binding).decode(),
        status="EDITORIAL_INTERNAL")
    return NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)


def pending(turn, stage="select"):
    args = {"logical_invocation_id": turn.run_id + ":" + stage, "prompt": "controlled " + stage,
            "governed_input": {}, "validator": lambda raw: (True, None, json.loads(raw), None)}
    with pytest.raises(DesktopInputRequired) as raised:
        turn(**args)
    return args, raised.value.request


def test_a_claude_operation_runs_its_stages_under_claude_labels(tmp_path):
    turn = turn_for(tmp_path, "claude")
    assert turn.editorial_agent == "claude"
    args, request = pending(turn)
    assert request["editorial_agent"] == "claude"
    assert (request["requested_model"], request["requested_reasoning_effort"]) == (CLAUDE_MODEL, "max")
    turn.submit("select", {"request_sha256": request["request_sha256"], "output": {"selected": "controlled"},
                           "invocation_observation": claude()})
    output, receipt = turn(**args)
    assert output == {"selected": "controlled"}
    assert receipt["provider"] == "NATIVE_CLAUDE_CODE" and receipt["selected_model"] == CLAUDE_MODEL
    assert receipt["configured_reasoning_effort"] == "max" and receipt["reasoning_effort"] is None
    telemetry = turn.telemetry()
    assert telemetry["owner"] == "NATIVE_CLAUDE_CODE" and telemetry["requested_model"] == CLAUDE_MODEL


@pytest.mark.parametrize("change,error", [
    ({"surface": "CODEX_NATIVE_SUBAGENT"}, "NATIVE_DESKTOP_SURFACE_REQUIRED"),  # never recorded as Codex
    ({"model": "gpt-6.1-sol"}, "NATIVE_DESKTOP_MODEL_MISMATCH"),
    ({"configured_reasoning_effort": "low"}, "EXACT_LABELLED_NATIVE_CONFIGURATION_REQUIRED"),
    ({"invocation_id": None}, "NATIVE_DESKTOP_INVOCATION_OBSERVATION_REQUIRED"),
    ({"observation_source": ""}, "NATIVE_DESKTOP_INVOCATION_OBSERVATION_REQUIRED"),
])
def test_a_claude_return_without_true_labels_or_invocation_evidence_is_refused(tmp_path, change, error):
    turn = turn_for(tmp_path, "claude")
    _, request = pending(turn)
    with pytest.raises(ValueError, match=error):
        turn.submit("select", {"request_sha256": request["request_sha256"], "output": {"selected": "x"},
                               "invocation_observation": claude(**change)})


def test_a_codex_operation_is_unchanged_and_refuses_a_claude_return(tmp_path):
    turn = turn_for(tmp_path, "codex")
    _, request = pending(turn)
    assert "editorial_agent" not in request and request["requested_model"] == "gpt-6.1-sol"
    with pytest.raises(ValueError, match="NATIVE_DESKTOP_SURFACE_REQUIRED"):
        turn.submit("select", {"request_sha256": request["request_sha256"], "output": {"selected": "x"},
                               "invocation_observation": claude()})
    turn.submit("select", {"request_sha256": request["request_sha256"], "output": {"selected": "x"},
                           "invocation_observation": configured()})


def test_the_next_role_call_has_the_same_claude_session_run_the_stage(tmp_path):
    turn = turn_for(tmp_path, "claude")
    _, request = pending(turn)
    binding = {"run_id": turn.run_id, "output_dir": str(tmp_path)}
    call = native_role_call({**request, "request_path": str(tmp_path / "desktop_request_select.json")}, binding,
                            binding_path="binding.json")
    assert call["tool"] == "claude.session" and call["editorial_agent"] == "claude"
    assert (call["arguments"]["model"], call["arguments"]["reasoning_effort"]) == (CLAUDE_MODEL, "max")
    assert "never record Claude as Codex" in call["arguments"]["message"]
    assert next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED",
                                  "next_native_call": call})["action"] == "EXECUTE_AND_COLLECT_NATIVE_ROLES"
    revise = {**request, "stage": "revise", "request_path": "r.json"}
    with pytest.raises(ValueError, match="ACTUAL_SAME_MAX_CONTINUATION_ID_REQUIRED"):
        native_role_call(revise, binding, binding_path="binding.json")
    call = native_role_call(revise, binding, binding_path="binding.json",
                            same_writer_invocation=SESSION, same_writer_configuration=claude())
    assert call["arguments"]["same_writer_invocation_id"] == SESSION
    for wrong in ({"surface": "CODEX_NATIVE_SUBAGENT"}, {"configured_model": "gpt-6.1-sol"}):
        with pytest.raises(ValueError):
            native_role_call(revise, binding, binding_path="binding.json",
                             same_writer_invocation=SESSION, same_writer_configuration=claude(**wrong))


def test_a_claude_call_cannot_be_relabelled_codex_or_widened(tmp_path):
    turn = turn_for(tmp_path, "claude")
    _, request = pending(turn)
    call = native_role_call({**request, "request_path": "q.json"}, {"run_id": turn.run_id, "output_dir": str(tmp_path)},
                            binding_path="binding.json")
    for change in ({"tool": "collaboration.spawn_agent"}, {"editorial_agent": "codex"}):
        with pytest.raises(ValueError):
            next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED",
                                   "next_native_call": {**call, **change}})
    widened = json.loads(json.dumps(call))
    widened["arguments"]["reasoning_effort"] = "low"
    with pytest.raises(ValueError, match="EXPLICIT_APPROVED_CLAUDE_ROLE_REQUIRED"):
        next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "next_native_call": widened})


def test_an_unknown_editorial_agent_is_refused():
    with pytest.raises(ValueError, match="EDITORIAL_AGENT_INVALID"):
        editorial_agent_of({"editorial_agent": "gemini"})
    assert editorial_agent_of({}) == "codex" and editorial_agent_of(None) == "codex"
