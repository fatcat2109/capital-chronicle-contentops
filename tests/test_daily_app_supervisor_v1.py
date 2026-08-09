from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    EditorialWindowPolicy,
    build_bootstrap_editorial_window_policy,
    editorial_window_id,
    material_event_due,
    TRIGGER_SCHEDULED,
    TRIGGER_MATERIAL_EVENT,
    WINDOW_EXECUTED_STATES,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def _fixed_clock(dt: datetime):
    return lambda: dt


def _controlled_cycle(calls: list, classification: str = "NO_PUBLICATION"):
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled):
        calls.append({"run_id": run_id, "cutoff_utc": cutoff_utc})
        return {
            "classification": classification,
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    return cycle


_USE_DEFAULT_CYCLE = object()


def _supervisor(tmp_path: Path, *, mode="AUTONOMOUS_DEFAULT", clock=None, cycle=_USE_DEFAULT_CYCLE, policy=None):
    calls = []
    newsroom_cycle = None if cycle is _USE_DEFAULT_CYCLE else cycle
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock,
        newsroom_cycle=newsroom_cycle,
        policy=policy,
    )
    if newsroom_cycle is None:
        # Replace the default canonical facade with a controlled recorder for isolation.
        supervisor._newsroom_cycle = _controlled_cycle(calls)
    return supervisor, calls


# --- Policy: deterministic bootstrap ---------------------------------------------


def test_bootstrap_policy_is_deterministic_configured_defaults_not_learned():
    policy = build_bootstrap_editorial_window_policy(effective_at_utc="2026-08-09T00:00:00Z")
    assert policy.policy_version == "bootstrap.v1"
    assert policy.confidence_state == "bootstrap_configured_defaults_not_learned"
    assert "learned" not in policy.confidence_state or "not_learned" in policy.confidence_state
    assert policy.provenance.startswith("deterministic_configured_bootstrap")
    assert len(policy.core_windows) >= 1
    assert policy.material_event_override_enabled is True


def test_editorial_window_id_is_deterministic_and_trigger_kind_aware():
    start = datetime(2026, 8, 9, 13, tzinfo=timezone.utc)
    end = datetime(2026, 8, 9, 15, tzinfo=timezone.utc)
    a = editorial_window_id(
        policy_version="bootstrap.v1", window_start_utc=start, window_end_utc=end,
        session="core_daily", trigger_kind=TRIGGER_SCHEDULED,
    )
    b = editorial_window_id(
        policy_version="bootstrap.v1", window_start_utc=start, window_end_utc=end,
        session="core_daily", trigger_kind=TRIGGER_SCHEDULED,
    )
    assert a == b
    # Different trigger kind or window time produces a different identity.
    c = editorial_window_id(
        policy_version="bootstrap.v1", window_start_utc=start, window_end_utc=end,
        session="core_daily", trigger_kind=TRIGGER_MATERIAL_EVENT,
    )
    assert a != c


def test_next_wake_is_deterministic_for_fixed_clock_and_policy():
    clock_dt = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)  # before the 13:00 window
    supervisor, _ = _supervisor(Path(_tempdir()), clock=_fixed_clock(clock_dt))
    wake1 = supervisor._next_wake(clock_dt)
    wake2 = supervisor._next_wake(clock_dt)
    assert wake1 == wake2 == datetime(2026, 8, 9, 13, tzinfo=timezone.utc)


def _tempdir():
    import tempfile
    return tempfile.mkdtemp(prefix="cc_daily_app_test_")


# --- Tick behavior -------------------------------------------------------------


def test_due_window_invokes_canonical_cycle_exactly_once_and_persists_terminal(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)  # inside 13-15 window
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["windows_dispatched"] == 1
    assert report["newsroom_cycle_invocations"] == 1
    assert len(calls) == 1
    # Terminal state persisted.
    wid = editorial_window_id(
        policy_version=supervisor.policy.policy_version,
        window_start_utc=datetime(2026, 8, 9, 13, tzinfo=timezone.utc),
        window_end_utc=datetime(2026, 8, 9, 15, tzinfo=timezone.utc),
        session="core_daily", trigger_kind=TRIGGER_SCHEDULED,
    )
    assert supervisor._window_state(wid) in WINDOW_EXECUTED_STATES


def test_duplicate_tick_does_not_invoke_cycle_twice(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor.tick(now=clock_dt)
    second = supervisor.tick(now=clock_dt)
    assert second["windows_dispatched"] == 0
    assert second["newsroom_cycle_invocations"] == 0
    assert len(calls) == 1  # still exactly one invocation


def test_restart_does_not_rerun_completed_window(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor.tick(now=clock_dt)
    assert len(calls) == 1
    # Simulate a restart: new supervisor instance over the SAME store.
    supervisor2, calls2 = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor2.tick(now=clock_dt)
    assert report["windows_dispatched"] == 0
    assert len(calls2) == 0  # restart did not re-invoke


def test_not_due_window_makes_zero_newsroom_calls(tmp_path):
    clock_dt = datetime(2026, 8, 9, 2, 0, tzinfo=timezone.utc)  # outside any window
    cycle_calls = []

    def cycle_should_not_run(**kwargs):
        cycle_calls.append(kwargs)
        return {"classification": "NO_PUBLICATION"}

    supervisor, _ = _supervisor(tmp_path, clock=_fixed_clock(clock_dt), cycle=cycle_should_not_run)
    report = supervisor.tick(now=clock_dt)
    assert report["newsroom_cycle_invocations"] == 0
    assert cycle_calls == []


def test_idle_tick_makes_zero_provider_calls(tmp_path):
    clock_dt = datetime(2026, 8, 9, 2, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["provider_calls"] == 0
    assert report["newsroom_cycle_invocations"] == 0
    assert report["performance_observation_state"] == "NOT_IMPLEMENTED_NOT_DUE"
    assert report["learning_evaluation_state"] == "NOT_IMPLEMENTED_NOT_DUE"


def test_kill_switch_blocks_dispatch_but_allows_safe_recovery(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, mode="KILL_SWITCH", clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["kill_switch_active"] is True
    assert report["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    assert "next_wake_utc" in report  # supervision/recovery continue


def test_competing_supervisors_preserve_single_logical_owner(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)
    supervisor_a, calls_a = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor_b, calls_b = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report_a = supervisor_a.tick(now=clock_dt)
    report_b = supervisor_b.tick(now=clock_dt)
    assert report_a["windows_dispatched"] == 1
    assert report_b["windows_dispatched"] == 0
    assert len(calls_a) == 1
    assert len(calls_b) == 0


def test_stale_pending_claim_recovered_without_rerun(tmp_path):
    clock_dt = datetime(2026, 8, 9, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    wid = editorial_window_id(
        policy_version=supervisor.policy.policy_version,
        window_start_utc=datetime(2026, 8, 9, 13, tzinfo=timezone.utc),
        window_end_utc=datetime(2026, 8, 9, 15, tzinfo=timezone.utc),
        session="core_daily", trigger_kind=TRIGGER_SCHEDULED,
    )
    # Simulate a claim-before-completion crash: create work item, transition to EVIDENCE_PENDING
    # under the supervisor's own owner identity, then release the lease (the "crash").
    supervisor._store.create_work_item(
        story_id=wid, title=f"Daily App editorial window {wid}",
        target_surface="daily_app_editorial_window", work_item_id=wid,
    )
    lease = supervisor._store.acquire_lease(
        lease_key=wid, owner_ref=supervisor._owner_ref, ttl_seconds=5, work_item_id=wid
    )
    supervisor._transition(
        window_id=wid, to_state="EVIDENCE_PENDING", lease_key=lease["lease_key"],
        fencing_token=int(lease["fencing_token"]), reason_code="EDITORIAL_WINDOW_DUE",
        explanation="claim before crash",
    )
    supervisor._store.release_lease(lease["lease_id"], supervisor._owner_ref, int(lease["fencing_token"]))
    assert supervisor._window_state(wid) == "EVIDENCE_PENDING"
    # New supervisor tick recovers the stale pending window without re-invoking the cycle.
    report = supervisor.tick(now=clock_dt)
    assert report["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    assert supervisor._window_state(wid) == "REJECTED"


def test_material_event_trigger_gets_stable_unique_identity(tmp_path):
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    policy = build_bootstrap_editorial_window_policy()
    metadata = {
        "material_event_due": True,
        "new_material_event_count": 2,
        "new_material_event_identity": "gov-policy-announcement-xyz",
    }
    signal1 = material_event_due(metadata, policy, now)
    signal2 = material_event_due(metadata, policy, now)
    assert signal1 is not None and signal2 is not None
    assert signal1["trigger_identity"] == signal2["trigger_identity"]
    assert signal1["trigger_kind"] == TRIGGER_MATERIAL_EVENT
    assert signal1["grants_evidence_or_publication_authority"] is False
    # Not due when below threshold.
    assert material_event_due({"material_event_due": True, "new_material_event_count": 0}, policy, now) is None


def test_material_event_window_invokes_cycle_once(tmp_path):
    clock_dt = datetime(2026, 8, 9, 2, 0, tzinfo=timezone.utc)  # outside scheduled windows
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    metadata = {
        "material_event_due": True,
        "new_material_event_count": 1,
        "new_material_event_identity": "breaking-material-event",
    }
    report = supervisor.tick(now=clock_dt, materiality_metadata=metadata)
    assert report["windows_dispatched"] == 1
    assert len(calls) == 1
    # Second identical tick does not re-trigger the same material event.
    report2 = supervisor.tick(now=clock_dt, materiality_metadata=metadata)
    assert report2["windows_dispatched"] == 0
    assert len(calls) == 1


def test_supervisor_uses_existing_durable_store_not_new_persistence(tmp_path):
    supervisor, _ = _supervisor(tmp_path)
    assert isinstance(supervisor._store, ContentOpsDurableStore)
    # The sqlite path is the one supplied; no second hidden database file type is created.
    supervisor.tick(now=datetime(2026, 8, 9, 2, tzinfo=timezone.utc))
    store_files = list(Path(tmp_path).glob("*.sqlite3"))
    assert len(store_files) == 1


def test_default_newsroom_cycle_is_the_canonical_facade():
    base = Path(_tempdir())
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=base / "store.sqlite3",
        output_root=base / "out",
        newsroom_cycle=None,
    )
    from live_contentops.eight_platform_substack_first_pipeline_v1 import (
        run_rolling_x_newsroom_cycle,
    )

    assert supervisor._newsroom_cycle is run_rolling_x_newsroom_cycle
