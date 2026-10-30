"""Decision-16 fallback preserves missing actual configuration and exact native roles."""
import json

import pytest

from live_contentops.native_desktop_editorial_v1 import (
    CONFIGURED_AUTHORITY, CONFIGURED_NOT_OBSERVED, DesktopInputRequired, validate_native_configuration,
)
from test_native_headline_filter_v1 import _turn


def configured(model="gpt-6.1-sol", effort="low"):
    return {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "/root/CONTROLLED_CONFIGURED_ROLE",
        "model": None, "reasoning_effort": None, "speed": "standard",
        "observation_source": "CONTROLLED_TEST_NOT_NATIVE_EXECUTION_PROOF",
        "configuration_status": CONFIGURED_NOT_OBSERVED, "configured_model": model,
        "configured_reasoning_effort": effort, "configuration_authority": CONFIGURED_AUTHORITY,
        "configuration_source": "Exact controlled native task arguments; actual settings unavailable",
        "actual_configuration_unavailable": True}


def test_configured_return_resumes_exact_request_without_claiming_observed_model(tmp_path):
    turn = _turn(tmp_path)
    args = {"logical_invocation_id": turn.run_id + ":select", "prompt": "controlled select",
        "governed_input": {}, "validator": lambda raw: (True, None, json.loads(raw), None)}
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    turn.submit("select", {"request_sha256": pending.value.request["request_sha256"],
        "output": {"selected": "controlled"}, "invocation_observation": configured()})
    output, receipt = turn(**args)
    assert output == {"selected": "controlled"}
    assert receipt["selected_model"] is None and receipt["reasoning_effort"] is None
    assert receipt["configuration_status"] == CONFIGURED_NOT_OBSERVED
    assert receipt["configured_model"] == "gpt-6.1-sol"
    telemetry = turn.telemetry()
    assert telemetry["observed_models"] == telemetry["observed_efforts"] == []
    assert telemetry["configured_not_observed_count"] == 1


@pytest.mark.parametrize("change", [
    {"configuration_status": None}, {"configuration_authority": None}, {"configuration_source": ""},
    {"actual_configuration_unavailable": False}, {"configured_model": "gpt-6-luna"},
    {"configured_reasoning_effort": "max"},
])
def test_fallback_cannot_be_unlabelled_wrong_role_or_unbound(change):
    with pytest.raises(ValueError):
        validate_native_configuration({**configured(), **change}, {"model": "gpt-6.1-sol", "reasoning_effort": "low"})


def test_observed_mismatch_is_not_hidden_by_configured_fallback():
    with pytest.raises(ValueError, match="MODEL_MISMATCH"):
        validate_native_configuration({**configured(), "model": "gpt-6-luna"},
            {"model": "gpt-6.1-sol", "reasoning_effort": "low"})
    with pytest.raises(ValueError, match="REPLACE_FALLBACK"):
        validate_native_configuration({**configured(), "model": "gpt-6.1-sol", "reasoning_effort": "low"},
            {"model": "gpt-6.1-sol", "reasoning_effort": "low"})


def test_final_review_accepts_labelled_max_only_with_same_actual_writer(tmp_path, monkeypatch):
    from test_native_desktop_publication_v1 import seeded
    from native_final_visual_fixture_v1 import visual_request_fixture
    from live_contentops.native_desktop_editorial_v1 import validate_final_visual_return
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    observation = configured(effort="max")
    observation["invocation_id"] = response["invocation_observation"]["invocation_id"]
    response["invocation_observation"] = observation
    validate_final_visual_return(turn, request, response)
    response["invocation_observation"]["invocation_id"] = "WRONG_SAME_CONFIGURED_ROLE"
    with pytest.raises(ValueError, match="SAME_SOL61_MAX"):
        validate_final_visual_return(turn, request, response)
