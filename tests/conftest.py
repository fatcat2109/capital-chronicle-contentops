import os

import pytest


@pytest.fixture(autouse=True)
def _disable_intake_lane_for_tests(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE", "1")
    # CC-297: tests and the processes they start never read Credential Manager or the live user
    # environment, so a test that removes a key can never post with Jim's real one.
    monkeypatch.setenv("CAPITAL_CHRONICLE_SECRET_STORE", "environment-only")
    # Unit tests must never consume or mutate the operator's canonical Runtime control state.
    from live_contentops import llm_cost_governor_v1, llm_operator_control_v1

    isolated = tmp_path / "llm_controls"
    monkeypatch.setattr(llm_operator_control_v1, "RUNTIME_CONTROL_ROOT", isolated)
    monkeypatch.setattr(llm_cost_governor_v1, "RUNTIME_CONTROL_ROOT", isolated)
    yield
