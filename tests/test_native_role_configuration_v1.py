"""CC-067: the app default cannot substitute for an explicit native role setting."""
from copy import deepcopy
import json

import pytest

from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
from live_contentops.native_desktop_editorial_v1 import validate_native_configuration
from live_contentops.native_editorial_continuation_v1 import next_editorial_action
from test_native_configured_provenance_v1 import configured


def request(stage, model="gpt-6.1-sol", effort="max"):
    return {"stage": stage, "run_id": "issued-run", "request_sha256": "b" * 64,
        "request_path": "frozen-request.json", "requested_model": model,
        "requested_reasoning_effort": effort, "prompt": "Frozen role request",
        "governed_input": {"records": []}}


def binding(tmp_path):
    # A coordinator can run on another model; its roles must not inherit that setting.
    return {"run_id": "issued-run", "output_dir": str(tmp_path),
        "model": "gpt-6-astra", "reasoning_effort": "ultra"}


def continuation():
    return {**configured(effort="max"), "invocation_id": "/root/designated_writer"}


@pytest.mark.parametrize("stage,model,effort", [
    ("filter-" + "a" * 64, "gpt-6-luna", "max"),
    ("select", "gpt-6.1-sol", "low"), ("media-plan", "gpt-6.1-sol", "low"),
    ("feedback", "gpt-6.1-sol", "low"), ("visual-edit", "gpt-6.1-sol", "max"),
    ("write", "gpt-6.1-sol", "max"),
])
def test_fresh_role_cannot_inherit_the_coordinators_model(tmp_path, stage, model, effort):
    call = native_role_call(request(stage, model, effort), binding(tmp_path), binding_path="binding.json")
    assert call["arguments"]["model"] == model
    assert call["arguments"]["reasoning_effort"] == effort
    assert call["arguments"]["fork_turns"] == "none"


@pytest.mark.parametrize("change", [
    {"model": "gpt-6-astra"}, {"reasoning_effort": "ultra"},
    {"model": None}, {"reasoning_effort": None}, {"fork_turns": "all"},
])
def test_wrong_or_inherited_role_is_rejected_before_execution(tmp_path, change):
    call = native_role_call(request("write"), binding(tmp_path), binding_path="binding.json")
    call["arguments"].update(change)
    with pytest.raises(ValueError, match="EXPLICIT_APPROVED_NATIVE_ROLE_REQUIRED"):
        next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "next_native_call": call})


@pytest.mark.parametrize("stage", ["write", "revise", "visual-edit-amend", "final-visual-" + "a" * 64])
def test_same_writer_requires_its_configuration_not_just_its_name(tmp_path, stage):
    with pytest.raises(ValueError, match="EXACT_SAME_WRITER_CONFIGURATION_REQUIRED"):
        native_role_call(request(stage), binding(tmp_path), binding_path="binding.json",
            same_writer_invocation="/root/designated_writer")
    call = native_role_call(request(stage), binding(tmp_path), binding_path="binding.json",
        same_writer_invocation="/root/designated_writer", same_writer_configuration=continuation())
    assert call["arguments"]["target"] == "/root/designated_writer"
    assert next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED",
        "next_native_call": call})["action"] == "EXECUTE_AND_COLLECT_NATIVE_ROLES"
    wrong = deepcopy(call)
    wrong["continuation_observation"].update(configured_model="gpt-6-astra", configured_reasoning_effort="ultra")
    with pytest.raises(ValueError, match="EXACT_LABELLED_NATIVE_CONFIGURATION_REQUIRED"):
        next_editorial_action({"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "next_native_call": wrong})


@pytest.mark.parametrize("change", [
    {"invocation_id": "/root/some_other_writer"},
    {"surface": "CODEX_DESKTOP_CONVERSATION"},
])
def test_continuation_cannot_route_another_writer_or_the_parent(tmp_path, change):
    with pytest.raises(ValueError, match="EXACT_SAME_WRITER_CONFIGURATION_REQUIRED"):
        native_role_call(request("revise"), binding(tmp_path), binding_path="binding.json",
            same_writer_invocation="/root/designated_writer", same_writer_configuration={**continuation(), **change})


@pytest.mark.parametrize("source_kind", ["JIM_CONFIRMED_THREAD_SETTINGS", "JIM_CONFIRMED_PERIOD_DEFAULT"])
def test_parent_app_default_requires_a_scoped_owner_confirmation(source_kind):
    observation = {**configured(effort="max"), "surface": "CODEX_DESKTOP_CONVERSATION"}
    target = {"model": "gpt-6.1-sol", "reasoning_effort": "max"}
    with pytest.raises(ValueError, match="THREAD_SPECIFIC_NATIVE_CONFIGURATION_REQUIRED"):
        validate_native_configuration(observation, target)
    observation.update(configuration_source_kind=source_kind,
        configuration_thread_id="01a18b78-45a3-73a3-90d1-539b3fc45eae")
    validate_native_configuration(observation, target)
    observation["configuration_thread_id"] = "app-default"
    with pytest.raises(ValueError, match="EXACT_NATIVE_CONFIGURATION_THREAD_REQUIRED"):
        validate_native_configuration(observation, target)


def test_cli_continues_only_the_saved_approved_writer_configuration(tmp_path, monkeypatch):
    from test_native_newsroom_owner_operation_v1 import entry
    module = entry()
    frozen = request("write")
    path = tmp_path / "request.json"
    path.write_text(json.dumps(frozen), encoding="utf-8")
    pending = {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "request_path": str(path),
        "stage": frozen["stage"], "request_sha256": frozen["request_sha256"]}
    monkeypatch.setattr(module, "_operation", lambda *a, **kw: dict(pending))
    observation = continuation()
    monkeypatch.setattr(module.NativeDesktopTurn, "_get", lambda *a, **kw: {
        "invocation_observation": dict(observation)})
    local = {**binding(tmp_path), "store_path": str(tmp_path / "isolated.sqlite3")}
    call = module.operation(local)["next_native_call"]
    assert call["arguments"]["target"] == observation["invocation_id"]
    assert call["continuation_observation"] == observation
    observation.update(configured_model="gpt-6-astra", configured_reasoning_effort="ultra")
    with pytest.raises(ValueError, match="EXACT_LABELLED_NATIVE_CONFIGURATION_REQUIRED"):
        module.operation(local)
