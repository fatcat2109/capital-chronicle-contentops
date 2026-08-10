import os

import pytest


@pytest.fixture(autouse=True)
def _disable_intake_lane_for_tests(monkeypatch):
    monkeypatch.setenv("CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE", "1")
    yield
