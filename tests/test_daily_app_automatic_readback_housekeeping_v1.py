"""Controlled TEMP-store proof for automatic Daily App lifecycle housekeeping.

No real network, browser, publisher, platform, production store, or public write is used.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    READBACK_RECONCILIATION_COOLDOWN_SECONDS,
    RECONCILE_ABSENT_SAFE,
    RECONCILE_CONFIRMED,
    RECONCILE_CONTROLLED_NO_WRITE,
    RECONCILE_PENDING_OPERATOR,
    RECONCILE_PENDING_READBACK,
    STATUS_CONTROLLED_NO_WRITE,
    STATUS_DISPATCH_CONFIRMED,
    STATUS_UNKNOWN_WRITE,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


T0 = datetime(2026, 8, 10, 4, 30, tzinfo=timezone.utc)  # outside editorial windows (policy v2)


def _supervisor(
    tmp_path,
    *,
    now_ref,
    readback=None,
    mode="AUTONOMOUS_DEFAULT",
    store=None,
    performance=False,
    collector=None,
    publisher_calls=None,
):
    store = store or ContentOpsDurableStore(
        tmp_path / "automatic-recovery.sqlite3", now_fn=lambda: now_ref[0]
    )

    def publisher(*args, **kwargs):
        if publisher_calls is not None:
            publisher_calls.append((args, kwargs))
        raise AssertionError("automatic recovery must never invoke publisher")

    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "automatic-recovery.sqlite3",
        store=store,
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=lambda: now_ref[0],
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        enable_publication_lifecycle=False,
        publication_publisher=publisher,
        publication_readback_provider=readback,
        enable_performance_observation=performance,
        performance_collector=collector,
    )


def _seed(
    supervisor,
    *,
    suffix="A",
    dispatch_status=STATUS_DISPATCH_CONFIRMED,
    reconciliation_status=RECONCILE_PENDING_READBACK,
    public_object_id="object-A",
    platform="substack",
    dispatched_at=None,
):
    store = supervisor._store
    window_id = f"wi-recovery-{suffix}"
    message_id = f"outbox-recovery-{suffix}"
    dispatch_id = f"dispatch-recovery-{suffix}"
    package_identity = f"package-recovery-{suffix}"
    store.create_work_item(
        story_id=f"story-recovery-{suffix}",
        title="Automatic recovery fixture",
        target_surface="daily_app_editorial_window",
        work_item_id=window_id,
    )
    store.register_outbox_message(
        message_id=message_id,
        work_item_id=window_id,
        destination=platform,
        payload=json.dumps(
            {
                "window_id": window_id,
                "destination": platform,
                "package_identity": package_identity,
            },
            sort_keys=True,
        ),
        status="READY",
    )
    store.register_platform_dispatch(
        dispatch_id=dispatch_id,
        message_id=message_id,
        platform=platform,
        status=dispatch_status,
        public_object_id=public_object_id,
    )
    reconciliation_id = supervisor._lifecycle_identity(
        window_id, platform, package_identity
    )["reconciliation_id"]
    store.register_reconciliation(
        reconciliation_id=reconciliation_id,
        work_item_id=window_id,
        status=reconciliation_status,
    )
    if dispatched_at is not None:
        with store.get_connection() as conn:
            conn.execute(
                "UPDATE platform_dispatches SET dispatched_at=? WHERE dispatch_id=?",
                (dispatched_at.isoformat(), dispatch_id),
            )
    return window_id, dispatch_id, reconciliation_id


def _reconciliation_status(supervisor, reconciliation_id):
    with supervisor._store.get_connection() as conn:
        return conn.execute(
            "SELECT status FROM reconciliations WHERE reconciliation_id=?",
            (reconciliation_id,),
        ).fetchone()["status"]


def _exact_readback(calls, object_id="object-A", *, write_occurred=None):
    def provider(dispatch_id, destination, durable_object_id):
        calls.append((dispatch_id, destination, durable_object_id))
        result = {
            "verified": True,
            "dispatch_id": dispatch_id,
            "destination": destination,
            "public_object_id": object_id,
        }
        if write_occurred is not None:
            result["write_occurred"] = write_occurred
        return result

    return provider


def test_tick_auto_discovers_pending_confirmed_and_invokes_existing_recovery(tmp_path):
    now_ref = [T0]
    calls = []
    publisher_calls = []
    supervisor = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(calls),
        publisher_calls=publisher_calls,
    )
    _window_id, _dispatch_id, reconciliation_id = _seed(supervisor)
    original = supervisor.perform_safe_readback_and_reconciliation
    method_calls = []

    def existing_recovery(window_id, **kwargs):
        method_calls.append(window_id)
        return original(window_id, **kwargs)

    supervisor.perform_safe_readback_and_reconciliation = existing_recovery
    report = supervisor.tick(now=T0)

    assert method_calls == ["wi-recovery-A"]
    assert len(calls) == 1
    assert publisher_calls == []
    assert report["readback_reconciliation_state"] == "RUN_RECONCILED"
    assert report["recovery_candidates"] == 1
    assert report["recovery_readback_calls"] == 1
    assert report["recovery_publisher_calls"] == 0
    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_CONFIRMED


def test_tick_auto_recovers_unknown_write_exact_object(tmp_path):
    now_ref = [T0]
    calls = []
    publisher_calls = []
    supervisor = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(calls, "recovered-object"),
        publisher_calls=publisher_calls,
    )
    _window_id, _dispatch_id, reconciliation_id = _seed(
        supervisor,
        dispatch_status=STATUS_UNKNOWN_WRITE,
        reconciliation_status=RECONCILE_PENDING_OPERATOR,
        public_object_id=None,
    )

    report = supervisor.tick(now=T0)

    assert len(calls) == 1
    assert publisher_calls == []
    assert report["recovery_reconciled"] == 1
    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_CONFIRMED


def test_unknown_write_proven_absent_is_safe_but_never_redispatched(tmp_path):
    now_ref = [T0]
    calls = []
    publisher_calls = []
    supervisor = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(calls, "", write_occurred=False),
        publisher_calls=publisher_calls,
    )
    _window_id, _dispatch_id, reconciliation_id = _seed(
        supervisor,
        dispatch_status=STATUS_UNKNOWN_WRITE,
        reconciliation_status=RECONCILE_PENDING_OPERATOR,
        public_object_id=None,
    )

    supervisor.tick(now=T0)

    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_ABSENT_SAFE
    assert publisher_calls == []


def test_unknown_write_wrong_preserved_identity_remains_pending(tmp_path):
    now_ref = [T0]

    def contradictory(dispatch_id, destination, durable_object_id):
        return {
            "verified": True,
            "dispatch_id": dispatch_id,
            "destination": destination,
            "public_object_id": "wrong-object",
            "write_occurred": False,
        }

    supervisor = _supervisor(tmp_path, now_ref=now_ref, readback=contradictory)
    _window_id, _dispatch_id, reconciliation_id = _seed(
        supervisor,
        dispatch_status=STATUS_UNKNOWN_WRITE,
        reconciliation_status=RECONCILE_PENDING_OPERATOR,
        public_object_id="preserved-object",
    )

    supervisor.tick(now=T0)

    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_PENDING_OPERATOR


@pytest.mark.parametrize(
    "provider",
    [
        None,
        lambda *args: (_ for _ in ()).throw(RuntimeError("unavailable")),
        lambda *args: "malformed",
        lambda dispatch_id, destination, object_id: {
            "verified": False,
            "dispatch_id": dispatch_id,
            "destination": destination,
            "public_object_id": object_id,
        },
        lambda dispatch_id, destination, object_id: {
            "verified": True,
            "dispatch_id": dispatch_id,
            "destination": destination,
            "public_object_id": "wrong-object",
        },
    ],
    ids=["unavailable", "exception", "malformed", "unverified", "wrong-identity"],
)
def test_ambiguous_confirmed_readback_remains_pending(tmp_path, provider):
    now_ref = [T0]
    supervisor = _supervisor(tmp_path, now_ref=now_ref, readback=provider)
    _window_id, _dispatch_id, reconciliation_id = _seed(supervisor)

    report = supervisor.tick(now=T0)

    assert report["readback_reconciliation_state"] == "RUN_STILL_PENDING"
    assert report["recovery_still_pending"] == 1
    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_PENDING_READBACK


def test_terminal_reconciliation_suppresses_future_provider_calls(tmp_path):
    now_ref = [T0]
    calls = []
    supervisor = _supervisor(tmp_path, now_ref=now_ref, readback=_exact_readback(calls))
    _seed(supervisor)
    supervisor.tick(now=T0)

    now_ref[0] = T0 + timedelta(hours=1)
    second = supervisor.tick(now=now_ref[0])

    assert len(calls) == 1
    assert second["recovery_candidates"] == 0
    assert second["recovery_readback_calls"] == 0


def test_confirmed_dispatch_without_durable_object_id_stays_pending_and_is_cooled_down(
    tmp_path,
):
    now_ref = [T0]
    calls = []
    supervisor = _supervisor(tmp_path, now_ref=now_ref, readback=_exact_readback(calls))
    _window_id, _dispatch_id, reconciliation_id = _seed(
        supervisor, public_object_id=None
    )

    first = supervisor.tick(now=T0)
    second = supervisor.tick(now=T0 + timedelta(seconds=1))

    assert calls == []
    assert first["readback_reconciliation_state"] == "RUN_STILL_PENDING"
    assert second["readback_reconciliation_state"] == "COOLDOWN_NOT_DUE"
    assert _reconciliation_status(supervisor, reconciliation_id) == RECONCILE_PENDING_READBACK


def test_restart_resumes_same_durable_identity_without_duplicate_object(tmp_path):
    now_ref = [T0]
    first_calls = []
    publisher_calls = []
    first = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=lambda *args: first_calls.append(args) or {},
        publisher_calls=publisher_calls,
    )
    _window_id, dispatch_id, reconciliation_id = _seed(first)
    first.tick(now=T0)
    assert _reconciliation_status(first, reconciliation_id) == RECONCILE_PENDING_READBACK

    now_ref[0] = T0 + timedelta(seconds=READBACK_RECONCILIATION_COOLDOWN_SECONDS + 1)
    second_calls = []
    restarted = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(second_calls),
        store=first._store,
        publisher_calls=publisher_calls,
    )
    restarted.tick(now=now_ref[0])

    assert second_calls == [(dispatch_id, "substack", "object-A")]
    assert publisher_calls == []
    assert _reconciliation_status(restarted, reconciliation_id) == RECONCILE_CONFIRMED
    assert len(restarted._store.list_platform_dispatches()) == 1


@pytest.mark.parametrize(
    "mode",
    ["AUTONOMOUS_DEFAULT", "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH"],
)
def test_automatic_recovery_runs_in_every_operating_mode(tmp_path, mode):
    now_ref = [T0]
    calls = []
    publisher_calls = []
    supervisor = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(calls),
        mode=mode,
        publisher_calls=publisher_calls,
    )
    _seed(supervisor)

    report = supervisor.tick(now=T0)

    assert report["recovery_reconciled"] == 1
    assert report["windows_dispatched"] == 0
    assert publisher_calls == []


def test_kill_switch_recovery_precedes_performance_and_schedules_observations(tmp_path):
    now_ref = [T0]
    readback_calls = []
    collector_calls = []

    def collector(dispatch_id, public_object_id, observation_window):
        collector_calls.append((dispatch_id, public_object_id, observation_window))
        return {"status": "COLLECTED", "metrics": {}, "availability": {}}

    supervisor = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=_exact_readback(readback_calls),
        mode="KILL_SWITCH",
        performance=True,
        collector=collector,
    )
    _seed(supervisor, dispatched_at=T0 - timedelta(minutes=20))

    report = supervisor.tick(now=T0)

    assert report["recovery_reconciled"] == 1
    assert report["performance_observation_state"] == "RUN"
    assert report["performance_observations"]["scheduled"] > 0
    assert report["windows_dispatched"] == 0
    assert report["public_write_performed"] is False


def test_cooldown_is_restart_safe_and_bounds_next_recovery_wake(tmp_path):
    now_ref = [T0]
    calls = []
    supervisor = _supervisor(
        tmp_path, now_ref=now_ref, readback=lambda *args: calls.append(args) or {}
    )
    _seed(supervisor)
    first = supervisor.tick(now=T0)
    assert first["recovery_readback_calls"] == 1

    now_ref[0] = T0 + timedelta(seconds=30)
    restarted = _supervisor(
        tmp_path,
        now_ref=now_ref,
        readback=lambda *args: calls.append(args) or {},
        store=supervisor._store,
    )
    second = restarted.tick(now=now_ref[0])
    next_wake = datetime.fromisoformat(
        second["next_wake_utc"].replace("Z", "+00:00")
    )

    assert len(calls) == 1
    assert second["readback_reconciliation_state"] == "COOLDOWN_NOT_DUE"
    assert second["recovery_cooldown_deferred"] == 1
    assert next_wake <= T0 + timedelta(seconds=READBACK_RECONCILIATION_COOLDOWN_SECONDS)

    now_ref[0] = T0 + timedelta(seconds=READBACK_RECONCILIATION_COOLDOWN_SECONDS + 1)
    restarted.tick(now=now_ref[0])
    assert len(calls) == 2


def test_controlled_no_write_and_terminal_reconciliation_never_enter_recovery(tmp_path):
    now_ref = [T0]
    calls = []
    supervisor = _supervisor(tmp_path, now_ref=now_ref, readback=_exact_readback(calls))
    _seed(
        supervisor,
        suffix="controlled",
        dispatch_status=STATUS_CONTROLLED_NO_WRITE,
        reconciliation_status=RECONCILE_CONTROLLED_NO_WRITE,
        public_object_id=None,
    )
    _seed(
        supervisor,
        suffix="terminal",
        reconciliation_status=RECONCILE_CONFIRMED,
    )

    report = supervisor.tick(now=T0)

    assert report["recovery_candidates"] == 0
    assert calls == []


def test_no_schema_migration_is_added(tmp_path):
    now_ref = [T0]
    supervisor = _supervisor(tmp_path, now_ref=now_ref)
    before = supervisor._store.get_current_schema_version()
    supervisor.tick(now=T0)
    after = supervisor._store.get_current_schema_version()
    assert before == after == 9
