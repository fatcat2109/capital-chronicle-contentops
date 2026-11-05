"""CC-268: the controlled-test intake switch also covers Run Now's forced sync.

tests/conftest.py sets CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE=1 for every test, but Run Now's
fallback sync ignored it. In the 5 Nov full run, six operator-trigger tests on fresh (stale) stores
drove the live X capture (CDP 9222) and wrote nine raw archives into the live headline root.
"""
from datetime import datetime, timezone

import pytest

from live_contentops import continuous_headline_ingest_v1 as intake
from live_contentops import x_list_ingest_capture_v1 as capture
from tests.test_daily_app_operator_trigger_v1 import _supervisor

NOW = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def no_live_capture(monkeypatch):
    reached = []

    def refuse(*args, **kwargs):
        reached.append(kwargs)
        raise AssertionError("a test reached the live X capture")

    monkeypatch.setattr(intake, "run_ingestion_housekeeping_iteration", refuse)
    monkeypatch.setattr(capture, "run_bounded_x_list_capture", refuse)
    monkeypatch.setattr(capture, "probe_session_visible_state", refuse)
    return reached


def test_run_now_sync_on_a_stale_store_never_captures_under_the_switch(tmp_path, no_live_capture):
    supervisor, _calls = _supervisor(tmp_path, mode="SHADOW_ONLY", clock=lambda: NOW)
    assert intake.intake_is_stale(supervisor._store, now=NOW)
    result = supervisor._run_operator_trigger_intake_sync(NOW)
    assert result["lane_state"] == "DISABLED_FOR_CONTROLLED_TEST"
    assert result["detail"] == "intake_lane_disabled_by_env"
    assert result["llm_or_provider_calls"] == 0
    assert no_live_capture == []


def test_run_now_through_tick_consumes_the_trigger_without_a_capture(tmp_path, no_live_capture):
    supervisor, calls = _supervisor(tmp_path, mode="SHADOW_ONLY", clock=lambda: NOW)
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-cc268-isolation",
        requested_mode="SHADOW_ONLY",
        control_state_version=1,
        requested_at_utc="2026-08-10T11:59:00+00:00",
    )
    report = supervisor.tick(NOW)
    trigger = report["operator_trigger"]
    assert trigger["state"] == "CONSUMED"
    assert trigger["ingestion_capture"]["lane_state"] == "DISABLED_FOR_CONTROLLED_TEST"
    assert len(calls) == 1
    assert no_live_capture == []
