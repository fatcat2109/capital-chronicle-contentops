from __future__ import annotations

import json
import threading
from dataclasses import replace
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
    def cycle(**kwargs):
        calls.append({"run_id": kwargs.get("run_id"), "cutoff_utc": kwargs.get("cutoff_utc")})
        return {
            "classification": classification,
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    return cycle


_USE_DEFAULT_CYCLE = object()


def _supervisor(
    tmp_path: Path,
    *,
    mode="AUTONOMOUS_DEFAULT",
    clock=None,
    cycle=_USE_DEFAULT_CYCLE,
    policy=None,
    owner_ref=None,
):
    calls = []
    newsroom_cycle = None if cycle is _USE_DEFAULT_CYCLE else cycle
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock,
        newsroom_cycle=newsroom_cycle,
        policy=policy,
        owner_ref=owner_ref,
    )
    if newsroom_cycle is None:
        # Replace the default canonical facade with a controlled recorder for isolation.
        supervisor._newsroom_cycle = _controlled_cycle(calls)
    return supervisor, calls


# --- Policy: deterministic bootstrap ---------------------------------------------


def test_bootstrap_policy_is_deterministic_configured_defaults_not_learned():
    policy = build_bootstrap_editorial_window_policy(effective_at_utc="2026-08-09T00:00:00Z")
    assert policy.policy_version == "autonomous_daily_output_four_window.v1"
    assert policy.confidence_state == "bootstrap_configured_defaults_not_learned"
    assert "learned" not in policy.confidence_state or "not_learned" in policy.confidence_state
    assert policy.provenance.startswith("owner_locked_autonomous_daily_output")
    assert len(policy.core_windows) == 4
    assert policy.material_event_override_enabled is True
    assert policy.daily_publication_target_band == (5, 8)
    assert policy.publication_minimum == 5
    assert policy.build_qualified_floor == 4
    assert policy.final_published_target_min == 5
    assert policy.final_published_target_max == 8
    assert policy.schedule_owner_locked is True
    assert policy.automatic_schedule_scaling_enabled is False


def test_editorial_window_id_is_deterministic_and_trigger_kind_aware():
    start = datetime(2026, 8, 9, 12, tzinfo=timezone.utc)
    end = datetime(2026, 8, 9, 14, tzinfo=timezone.utc)
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


def test_material_event_priority_survives_restart_and_is_consumed_by_scheduled_window(tmp_path):
    staged_at = datetime(2026, 8, 10, 10, 10, tzinfo=timezone.utc)
    output_root = tmp_path / "out"
    first = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3", output_root=output_root,
        clock=lambda: staged_at, operating_mode="SHADOW_ONLY",
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
    )
    signal = material_event_due(
        {
            "material_event_due": True, "new_material_event_count": 1,
            "new_material_event_identity": "governed-delta-1",
            "new_headline_ids": ["headline-priority"],
            "new_headline_source_refs": ["source-ref-priority"],
            "update_chain_identities": ["chain-priority"],
        },
        first.policy,
        staged_at,
    )
    staged = first._stage_material_event(signal, staged_at)

    captured = []
    scheduled_at = staged_at + timedelta(minutes=20)
    restarted = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3", store=first._store,
        output_root=output_root, clock=lambda: scheduled_at,
        operating_mode="SHADOW_ONLY",
        newsroom_cycle=lambda **kwargs: captured.append(kwargs) or {
            "classification": "NO_PUBLICATION",
            "public_write_performed": False,
            "unknown_write_detected": False,
        },
    )
    outcome = restarted._execute_window(
        {
            "window_id": "scheduled-material-consumer",
            "trigger": TRIGGER_SCHEDULED,
            "start": scheduled_at - timedelta(minutes=5),
            "end": scheduled_at + timedelta(minutes=5),
            "session": "controlled-scheduled",
        },
        scheduled_at,
    )

    assert outcome["executed"] is True
    assert captured[0]["material_event_priority"]["priority_ids"] == [staged["window_id"]]
    assert captured[0]["material_event_priority"]["headline_ids"] == ["headline-priority"]
    assert first._store.get_work_item(staged["window_id"])["current_state"] == "REJECTED"
    assert outcome["material_event_priority_finalization"][staged["window_id"]] == (
        "MATERIAL_EVENT_PRIORITY_CONSUMED"
    )
    assert len(restarted.policy.core_windows) == 4


def test_expired_material_event_priority_terminalizes_instead_of_remaining_discovered(tmp_path):
    staged_at = datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc)
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3", output_root=tmp_path / "out",
        clock=lambda: staged_at, operating_mode="SHADOW_ONLY",
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
    )
    signal = material_event_due(
        {
            "material_event_due": True,
            "new_material_event_count": 1,
            "new_material_event_identity": "governed-expiring-delta",
            "new_headline_ids": ["headline-expiring"],
        },
        supervisor.policy,
        staged_at,
    )
    staged = supervisor._stage_material_event(signal, staged_at)
    priority_path = Path(staged["priority_artifact"])
    priority = json.loads(priority_path.read_text(encoding="utf-8"))
    priority["expires_at_utc"] = (staged_at + timedelta(minutes=1)).isoformat()
    priority_path.write_text(json.dumps(priority), encoding="utf-8")

    pending = supervisor._pending_material_event_priorities(
        staged_at + timedelta(minutes=2), expire_stale=True
    )

    assert pending == []
    assert supervisor._store.get_work_item(staged["window_id"])["current_state"] == "REJECTED"
    assert len(supervisor.policy.core_windows) == 4


def test_next_wake_is_deterministic_for_fixed_clock_and_policy():
    clock_dt = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)  # Sunday: next is Monday
    supervisor, _ = _supervisor(Path(_tempdir()), clock=_fixed_clock(clock_dt))
    wake1 = supervisor._next_wake(clock_dt)
    wake2 = supervisor._next_wake(clock_dt)
    assert wake1 == wake2 == datetime(2026, 8, 10, 10, tzinfo=timezone.utc)


def test_continuous_checkpoint_carries_unresolved_identity_when_current_input_is_empty(
    tmp_path, monkeypatch,
):
    from live_contentops import newsroom_assignment_scheduler_v1 as scheduler

    prepared_at = datetime(2026, 8, 17, 14, tzinfo=timezone.utc)
    supervisor, _ = _supervisor(tmp_path, clock=_fixed_clock(prepared_at))
    row = {
        "headline_id": "continuity-carry",
        "source_timestamp_utc": "2026-08-17T12:00:00Z",
    }
    rolling_input = {
        "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
        "cutoff_time_utc": "2026-08-17T14:00:00Z",
        "window_start_utc": "2026-08-16T14:00:00Z",
        "window_hours": 24.0,
        "unique_headline_ids": ["continuity-carry"],
        "headlines": [row],
        "counts": {"accepted": 1, "duplicates": 0},
        "canonical_input_hash": "controlled",
        "complete_input_coverage": True,
    }
    prior = scheduler.build_prepared_rolling_x_candidate_state(
        rolling_input=rolling_input,
        prepared_at_utc=prepared_at,
    )
    checkpoint = supervisor._prepared_candidate_checkpoint_path
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(json.dumps(prior), encoding="utf-8")
    empty_input = {
        **rolling_input,
        "cutoff_time_utc": "2026-08-18T13:00:00Z",
        "unique_headline_ids": [],
        "headlines": [],
        "counts": {"accepted": 0, "duplicates": 0},
    }
    monkeypatch.setattr(
        scheduler, "load_rolling_x_headline_sidecars", lambda **_kwargs: empty_input
    )

    result = supervisor._refresh_prepared_candidate_checkpoint(
        datetime(2026, 8, 18, 13, tzinfo=timezone.utc)
    )
    carried = json.loads(checkpoint.read_text(encoding="utf-8"))

    assert result["status"] == "READY"
    assert result["checkpoint_updated"] is True
    assert carried["prepared_candidate_count"] == 0
    retained = carried["prepared_frontier"]["retained_audit_dispositions"]
    assert retained[0]["headline_id"] == "continuity-carry"
    assert retained[0]["disposition"] == "NOT_PROMOTED_BEFORE_EXPIRY"
    assert retained[0]["evidence_walk_evaluated"] is False


def _tempdir():
    import tempfile
    return tempfile.mkdtemp(prefix="cc_daily_app_test_")


# --- Tick behavior -------------------------------------------------------------


def test_due_window_invokes_canonical_cycle_exactly_once_and_persists_terminal(tmp_path):
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["windows_dispatched"] == 1
    assert report["newsroom_cycle_invocations"] == 1
    assert len(calls) == 1
    # Terminal state persisted.
    wid = editorial_window_id(
        policy_version=supervisor.policy.policy_version,
        window_start_utc=datetime(2026, 8, 10, 14, tzinfo=timezone.utc),
        window_end_utc=datetime(2026, 8, 10, 15, tzinfo=timezone.utc),
        session="new_york_2100_bangkok", trigger_kind=TRIGGER_SCHEDULED,
    )
    assert supervisor._window_state(wid) in WINDOW_EXECUTED_STATES


def test_later_window_runs_bounded_catchup_only_after_each_qualified_article(
    tmp_path, monkeypatch
):
    from live_contentops import newsroom_production_day_v1 as production

    # One minute past 23:00 Bangkok excludes the prior 21:00 window's grace boundary.
    clock_dt = datetime(2026, 8, 10, 16, 1, tzinfo=timezone.utc)
    calls = []

    def controlled_cycle(**kwargs):
        calls.append(kwargs["run_id"])
        return {
            "run_id": kwargs["run_id"],
            "classification": "PASS_PUBLICATION_PLAN_READY",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    supervisor, _ = _supervisor(
        tmp_path,
        mode="SHADOW_ONLY",
        clock=_fixed_clock(clock_dt),
        cycle=controlled_cycle,
    )
    before = production.NewsroomProductionDaySnapshot(
        newsroom_production_day_id=production.newsroom_production_day_id(clock_dt),
        build_qualified_floor=4,
        final_published_target_min=5,
        final_published_target_max=8,
        qualified_articles_today=1,
        published_articles_today=0,
        remaining_build_deficit=3,
        production_day_state=production.STATE_DEFICIT_RECOVERABLE,
        hard_external_block_reason=None,
        routine_opportunities_used=2,
        routine_opportunities_remaining=2,
    )
    after = replace(
        before,
        qualified_articles_today=3,
        remaining_build_deficit=1,
        routine_opportunities_used=3,
        routine_opportunities_remaining=1,
        production_day_state=production.STATE_ON_TRACK,
    )
    snapshots = iter((before, after))
    monkeypatch.setattr(production, "build_production_day_snapshot", lambda **_kwargs: next(snapshots))
    monkeypatch.setattr(
        production,
        "qualify_zero_write_article",
        lambda **kwargs: {
            "qualified": True,
            "article_identity": kwargs["result"]["run_id"],
        },
    )
    monkeypatch.setattr(production, "persist_qualified_article_record", lambda *_args: None)
    monkeypatch.setattr(production, "qualified_records_as_published_memory", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(production, "persist_production_day_snapshot", lambda *_args: None)

    report = supervisor.tick(now=clock_dt)

    assert report["windows_dispatched"] == 1
    assert report["newsroom_cycle_invocations"] == 1
    assert len(calls) == 2
    assert calls[1].endswith("-catchup-02")


def test_duplicate_tick_does_not_invoke_cycle_twice(tmp_path):
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor.tick(now=clock_dt)
    second = supervisor.tick(now=clock_dt)
    assert second["windows_dispatched"] == 0
    assert second["newsroom_cycle_invocations"] == 0
    assert len(calls) == 1  # still exactly one invocation


def test_restart_does_not_rerun_completed_window(tmp_path):
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor.tick(now=clock_dt)
    assert len(calls) == 1
    # Simulate a restart: new supervisor instance over the SAME store.
    supervisor2, calls2 = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor2.tick(now=clock_dt)
    assert report["windows_dispatched"] == 0
    assert len(calls2) == 0  # restart did not re-invoke


def test_not_due_window_makes_zero_newsroom_calls(tmp_path):
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)  # outside any window
    cycle_calls = []

    def cycle_should_not_run(**kwargs):
        cycle_calls.append(kwargs)
        return {"classification": "NO_PUBLICATION"}

    supervisor, _ = _supervisor(tmp_path, clock=_fixed_clock(clock_dt), cycle=cycle_should_not_run)
    report = supervisor.tick(now=clock_dt)
    assert report["newsroom_cycle_invocations"] == 0
    assert cycle_calls == []


def test_idle_tick_makes_zero_provider_calls(tmp_path):
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["provider_calls"] == 0
    assert report["newsroom_cycle_invocations"] == 0
    assert report["performance_observation_state"] == "NOT_IMPLEMENTED_NOT_DUE"
    assert report["learning_evaluation_state"] == "NOT_IMPLEMENTED_NOT_DUE"


def test_tick_refreshes_one_stable_durable_supervisor_heartbeat_across_restart(tmp_path):
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)
    supervisor, _ = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))

    first = supervisor.tick(now=clock_dt)
    restarted, _ = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    second = restarted.tick(now=clock_dt)

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    with store.get_read_only_connection() as conn:
        rows = [dict(row) for row in conn.execute(
            "SELECT worker_id,last_seen_at,status FROM heartbeats ORDER BY worker_id"
        ).fetchall()]

    assert first["heartbeat_worker_id"] == second["heartbeat_worker_id"]
    assert first["heartbeat_at_utc"]
    assert second["heartbeat_at_utc"]
    assert rows == [{
        "worker_id": second["heartbeat_worker_id"],
        "last_seen_at": second["heartbeat_at_utc"],
        "status": "ALIVE",
    }]


def test_kill_switch_blocks_dispatch_allows_recovery_and_pauses_default_browser_intake(
    tmp_path, monkeypatch,
):
    monkeypatch.delenv("CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE", raising=False)
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, mode="KILL_SWITCH", clock=_fixed_clock(clock_dt))
    report = supervisor.tick(now=clock_dt)
    assert report["kill_switch_active"] is True
    assert report["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    assert report["headline_ingestion"] == {
        "lane_state": "PAUSED_KILL_SWITCH",
        "detail": "NETWORK_INTAKE_PAUSED_BY_OPERATOR_KILL_SWITCH",
        "capture_attempted": False,
        "llm_or_provider_calls": 0,
        "public_write_performed": False,
    }
    assert "next_wake_utc" in report  # supervision/recovery continue


def test_competing_supervisors_preserve_single_logical_owner(tmp_path):
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    supervisor_a, calls_a = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    supervisor_b, calls_b = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    report_a = supervisor_a.tick(now=clock_dt)
    report_b = supervisor_b.tick(now=clock_dt)
    assert report_a["windows_dispatched"] == 1
    assert report_b["windows_dispatched"] == 0
    assert len(calls_a) == 1
    assert len(calls_b) == 0


def test_competing_supervisor_cannot_recover_an_active_pending_window(tmp_path):
    clock_dt = datetime(2026, 8, 10, 14, 0, tzinfo=timezone.utc)
    cycle_started = threading.Event()
    allow_cycle_to_finish = threading.Event()
    calls_a = []
    errors = []

    def blocking_cycle(**kwargs):
        calls_a.append(kwargs.get("run_id"))
        cycle_started.set()
        assert allow_cycle_to_finish.wait(timeout=10)
        return {
            "classification": "NO_PUBLICATION",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    supervisor_a, _ = _supervisor(
        tmp_path,
        clock=_fixed_clock(clock_dt),
        cycle=blocking_cycle,
        owner_ref="daily-app-supervisor-a",
    )
    supervisor_b, calls_b = _supervisor(
        tmp_path,
        clock=_fixed_clock(clock_dt),
        owner_ref="daily-app-supervisor-b",
    )

    def run_a():
        try:
            supervisor_a.tick(now=clock_dt)
        except Exception as exc:  # pragma: no cover - assertion reports the exact failure
            errors.append(exc)

    worker = threading.Thread(target=run_a)
    worker.start()
    assert cycle_started.wait(timeout=10)

    window_id = editorial_window_id(
        policy_version=supervisor_a.policy.policy_version,
        window_start_utc=datetime(2026, 8, 10, 14, tzinfo=timezone.utc),
        window_end_utc=datetime(2026, 8, 10, 15, tzinfo=timezone.utc),
        session="new_york_2100_bangkok",
        trigger_kind=TRIGGER_SCHEDULED,
    )
    assert supervisor_b._window_state(window_id) == "EVIDENCE_PENDING"

    competing = supervisor_b.tick(now=clock_dt)
    assert competing["windows_dispatched"] == 0
    assert competing["newsroom_cycle_invocations"] == 0
    assert any("active_window_owned_elsewhere" in row for row in competing["windows_skipped"])
    assert supervisor_b._window_state(window_id) == "EVIDENCE_PENDING"
    assert calls_b == []

    allow_cycle_to_finish.set()
    worker.join(timeout=10)
    assert not worker.is_alive()
    assert errors == []
    assert calls_a == [window_id]
    assert supervisor_a._window_state(window_id) == "REJECTED"


def test_default_supervisor_owner_identity_is_unique_per_instance(tmp_path):
    supervisor_a, _ = _supervisor(tmp_path)
    supervisor_b, _ = _supervisor(tmp_path)
    assert supervisor_a._owner_ref != supervisor_b._owner_ref


def test_stale_pending_claim_recovered_without_rerun(tmp_path):
    # Recovery must not depend on the abandoned scheduled window becoming due again.
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    wid = editorial_window_id(
        policy_version=supervisor.policy.policy_version,
        window_start_utc=datetime(2026, 8, 8, 12, tzinfo=timezone.utc),
        window_end_utc=datetime(2026, 8, 8, 14, tzinfo=timezone.utc),
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
    assert report["stale_pending_recovered"] == 1
    assert report["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    assert supervisor._window_state(wid) == "REJECTED"


def test_stale_pending_opportunity_resumes_from_durable_checkpoint(tmp_path):
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    window = {
        "window_id": "scheduled-resumable-opportunity",
        "trigger": TRIGGER_SCHEDULED,
        "start": datetime(2026, 8, 9, 3, 0, tzinfo=timezone.utc),
        "end": datetime(2026, 8, 9, 4, 0, tzinfo=timezone.utc),
        "session": "core_daily",
    }
    wid = window["window_id"]
    supervisor._store.create_work_item(
        story_id=wid,
        title=f"Daily App editorial window {wid}",
        target_surface="daily_app_editorial_window",
        work_item_id=wid,
    )
    supervisor._persist_editorial_opportunity_checkpoint(window)
    lease = supervisor._store.acquire_lease(
        lease_key=wid,
        owner_ref=supervisor._owner_ref,
        ttl_seconds=5,
        work_item_id=wid,
    )
    supervisor._transition(
        window_id=wid,
        to_state="EVIDENCE_PENDING",
        lease_key=lease["lease_key"],
        fencing_token=int(lease["fencing_token"]),
        reason_code="EDITORIAL_WINDOW_DUE",
        explanation="claimed before controlled interruption",
    )
    supervisor._store.release_lease(
        lease["lease_id"], supervisor._owner_ref, int(lease["fencing_token"])
    )

    report = supervisor.tick(now=clock_dt)

    assert report["stale_pending_resumed"] == 1
    assert [call["run_id"] for call in calls] == [wid]
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


def test_material_event_outside_scheduled_window_queues_without_llm_cycle(tmp_path):
    clock_dt = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)  # outside scheduled windows
    supervisor, calls = _supervisor(tmp_path, clock=_fixed_clock(clock_dt))
    metadata = {
        "material_event_due": True,
        "new_material_event_count": 1,
        "new_material_event_identity": "breaking-material-event",
    }
    report = supervisor.tick(now=clock_dt, materiality_metadata=metadata)
    assert report["windows_dispatched"] == 0
    assert report["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    assert report["material_event_wake"]["state"] == "DISCOVERED"
    assert report["material_event_wake"]["grants_evidence_or_publication_authority"] is False
    # Second identical tick remains the same durable queued priority signal and still does not
    # wake the expensive newsroom.
    report2 = supervisor.tick(now=clock_dt, materiality_metadata=metadata)
    assert report2["windows_dispatched"] == 0
    assert report2["newsroom_cycle_invocations"] == 0
    assert report2["material_event_wake"]["window_id"] == report["material_event_wake"]["window_id"]
    assert len(calls) == 0


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
