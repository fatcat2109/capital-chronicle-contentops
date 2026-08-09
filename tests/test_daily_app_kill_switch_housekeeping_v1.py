"""Focused tests: KILL_SWITCH housekeeping correction (FDA-D metrics continue under KILL_SWITCH).

KILL_SWITCH blocks NEW public dispatch only; read-only performance observation, readback,
reconciliation, and safe recovery all continue. Uses TEMP stores and fixture-only controlled data.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops import daily_app_performance_v1 as perf
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor

from tests import test_daily_app_performance_learning_v1 as PL

AFTER_ALL_WINDOWS = PL.AFTER_ALL_WINDOWS
# Dispatch published 20 minutes before the clock so only the EARLY (T+15m) window is due -> one
# collector call; the INTERMEDIATE (T+2h) window is still future (used for the next-wake check).
DISPATCH_AT = AFTER_ALL_WINDOWS - timedelta(minutes=20)


def _ks_supervisor(tmp_path, *, collector, clock=None, learning=False, store=None, mode="KILL_SWITCH"):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "ks.sqlite3", store=store, output_root=tmp_path / "out",
        clock=clock or (lambda: AFTER_ALL_WINDOWS), operating_mode=mode,
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        enable_performance_observation=True, performance_learning_enabled=learning,
        performance_collector=collector,
        publication_publisher=lambda d, p: {"status": "DISPATCH_CONFIRMED_NO_WRITE"},
        publication_readback_provider=None,
        enable_publication_lifecycle=False,
    )


def _seed_dispatch(sup, *, dispatched_at):
    return PL._seed_confirmed_publication(
        sup, object_id="obj-ks", dispatch_id="pd_ks",
        platform="substack", dispatched_at=dispatched_at,
    )


def _collector_with_calls(calls):
    return PL._collector(calls=calls)


# 1+2. KILL_SWITCH + due observation: collector called exactly once; observation reaches COLLECTED.
def test_kill_switch_due_observation_collected_once(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls))
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    # Only EARLY is due -> exactly one collector call.
    assert len(calls) == 1
    assert report["performance_observation_state"] == "RUN"
    assert report["performance_observations"]["collected"] == 1
    # The due observation reached a normal terminal collection state (NOT SKIPPED_KILL_SWITCH).
    obs = [o for o in sup._store.list_performance_observations(dispatch_id=dispatch_id)
           if o["observation_window"] == "EARLY"]
    assert len(obs) == 1
    assert obs[0]["collection_status"] == "COLLECTED"
    native = json.loads(obs[0]["metrics_native_json"])
    assert native == PL.COLLECTED_METRICS  # real metrics collected, not fabricated zeros


# 3+4. KILL_SWITCH: zero publisher calls, zero new public dispatches.
def test_kill_switch_zero_publisher_and_dispatches(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls))
    _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert report["windows_dispatched"] == 0
    assert report["public_write_performed"] is False
    assert report["newsroom_cycle_invocations"] == 0


# 5+6. KILL_SWITCH: existing UNKNOWN_WRITE recovery + reconciliation still work.
def test_kill_switch_readback_and_reconciliation_continue(tmp_path):
    rb_calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls([]))
    # Seed an UNKNOWN_WRITE dispatch for recovery under KILL_SWITCH.
    PL._seed_confirmed_publication(
        sup, object_id=None, dispatch_id="pd_uw", suffix="uw",
        dispatch_status="UNKNOWN_WRITE", reconciliation_status="RECONCILIATION_PENDING_OPERATOR_RECOVERY",
        platform="substack", url=None,
    )
    ks = _ks_supervisor(tmp_path, collector=_collector_with_calls([]), store=sup._store)
    # Readback/reconciliation/recovery remain available under KILL_SWITCH (no publisher call).
    summary = ks.perform_safe_readback_and_reconciliation(
        "wi_pub_uw", readback_provider=lambda dispatch_id, public_object_id, window: (
            {"verified": True, "dispatch_id": dispatch_id, "destination": "substack",
             "public_object_id": None, "write_occurred": False})
    )
    assert summary["publisher_calls"] == 0


# 7. KILL_SWITCH + no due observation: collector not called.
def test_kill_switch_no_due_observation_zero_calls(tmp_path):
    calls = []
    # Supervisor with observation enabled but no dispatch seeded -> nothing due.
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls), clock=lambda: AFTER_ALL_WINDOWS)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert len(calls) == 0
    assert report["performance_observation_state"] == "RUN"
    assert report["performance_observations"]["collected"] == 0


# 8. KILL_SWITCH + due observation + collector unavailable: fail closed, no fabricated zeros.
def test_kill_switch_collector_unavailable_fails_closed(tmp_path):
    sup = _ks_supervisor(tmp_path, collector=None)  # no collector -> capability unavailable
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert report["performance_observations"]["collected"] >= 1
    obs = [o for o in sup._store.list_performance_observations(dispatch_id=dispatch_id)
           if o["observation_window"] == "EARLY"]
    assert len(obs) == 1
    # Terminal collection state reflects unavailable capability, not fabricated metrics.
    assert obs[0]["collection_status"] == "COLLECTOR_UNAVAILABLE"
    native = json.loads(obs[0]["metrics_native_json"])
    assert native == {}  # no fabricated zeros


# 9. Restart under KILL_SWITCH: already-collected observation not duplicated.
def test_kill_switch_restart_no_duplicate_observation(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls))
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    sup.tick(now=AFTER_ALL_WINDOWS)
    n1 = len(sup._store.list_performance_observations(dispatch_id=dispatch_id))
    # Restart (new supervisor, same store) under KILL_SWITCH.
    restarted = _ks_supervisor(tmp_path, collector=_collector_with_calls([]), store=sup._store)
    restarted.tick(now=AFTER_ALL_WINDOWS)
    n2 = len(sup._store.list_performance_observations(dispatch_id=dispatch_id))
    assert n1 == n2  # no duplicate observation rows after restart


# 10. Next wake under KILL_SWITCH accounts for future due observation time.
def test_kill_switch_next_wake_accounts_future_observation(tmp_path):
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls([]))
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    # After collecting EARLY, the next due observation is INTERMEDIATE (DISPATCH_AT + 2h).
    expected_next_obs = DISPATCH_AT + timedelta(hours=2)
    next_wake = datetime.fromisoformat(report["next_wake_utc"].replace("Z", "+00:00"))
    # The wake must not be later than the next due observation time.
    assert next_wake <= expected_next_obs


# 11. AUTONOMOUS_DEFAULT behavior unchanged (collector runs, dispatch allowed).
def test_autonomous_default_unchanged(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls), mode="AUTONOMOUS_DEFAULT")
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert report["performance_observation_state"] == "RUN"
    assert len(calls) == 1  # due observation collected in default mode too


# 12. SHADOW_ONLY behavior unchanged (observations continue; no public writes).
def test_shadow_only_unchanged(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls), mode="SHADOW_ONLY")
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert report["performance_observation_state"] == "RUN"
    assert len(calls) == 1
    assert report["public_write_performed"] is False


# 13. SUPERVISED_OPERATOR_GATE behavior unchanged.
def test_supervised_operator_gate_unchanged(tmp_path):
    calls = []
    sup = _ks_supervisor(tmp_path, collector=_collector_with_calls(calls), mode="SUPERVISED_OPERATOR_GATE")
    dispatch_id = _seed_dispatch(sup, dispatched_at=DISPATCH_AT)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    assert report["performance_observation_state"] == "RUN"
    assert len(calls) == 1
