"""Focused tests for Final Daily App publication lifecycle, production epoch, and store binding."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    build_bootstrap_editorial_window_policy,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


WINDOW_START = datetime(2026, 8, 9, 13, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 8, 9, 15, tzinfo=timezone.utc)
INSIDE_WINDOW = datetime(2026, 8, 9, 14, tzinfo=timezone.utc)


def _fixed_clock(dt):
    return lambda: dt


def _fixture_cycle(destinations=("substack", "telegram"), package_identity="pkg-fixed-1"):
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled, **kwargs):
        return {
            "classification": "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1",
            "publication_lifecycle_plan": {
                "ready_destinations": list(destinations),
                "package_identity": package_identity,
            },
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    return cycle


def _fixture_publisher(status="DISPATCH_CONFIRMED_NO_WRITE"):
    calls = []

    def publisher(destination, package_identity):
        calls.append((destination, package_identity))
        return {"status": status, "public_object_id": f"obj-{destination}"}

    publisher.calls = calls
    return publisher


def _fixture_readback():
    def readback(dispatch_id, destination):
        return {"dispatch_id": dispatch_id, "destination": destination, "verified": True}

    return readback


def _lifecycle_supervisor(tmp_path, *, mode="AUTONOMOUS_DEFAULT", publisher_status="DISPATCH_CONFIRMED_NO_WRITE", clock=None):
    publisher = _fixture_publisher(publisher_status)
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "production.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock or _fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=_fixture_cycle(),
        publication_publisher=publisher,
        publication_readback_provider=_fixture_readback(),
        enable_publication_lifecycle=True,
    )
    return supervisor, publisher


def _counts(store):
    conn = store.get_connection()
    try:
        return {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("work_items", "outbox_messages", "platform_dispatches", "readbacks", "reconciliations", "incidents")
        }
    finally:
        conn.close()


# --- Production store initializes canonical schema, zero state, no import ----


def test_new_production_store_initializes_canonical_schema_and_zero_state(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "prod.sqlite3", auto_migrate=True)
    assert store.get_current_schema_version() == 4
    assert store.verify_applied_migrations() is True
    assert store.verify_schema_integrity() is True
    counts = _counts(store)
    # Fresh epoch must begin with zero operational/history rows (nothing imported).
    assert counts["work_items"] == 0
    assert counts["outbox_messages"] == 0
    assert counts["platform_dispatches"] == 0
    assert counts["readbacks"] == 0
    assert counts["reconciliations"] == 0
    assert counts["incidents"] == 0


# --- Controlled lifecycle: outbox -> dispatch -> readback -> reconciliation ----


def test_controlled_lifecycle_drives_full_chain_zero_public_write(tmp_path):
    supervisor, publisher = _lifecycle_supervisor(tmp_path)
    report = supervisor.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 1
    assert len(publisher.calls) == 2  # one per READY destination

    assert report["unknown_write_detected"] is False
    assert report["public_write_performed"] is False

    store = supervisor._store
    rows = _counts(store)
    assert rows["work_items"] == 1
    assert rows["outbox_messages"] == 2
    assert rows["platform_dispatches"] == 2
    assert rows["readbacks"] == 2
    assert rows["reconciliations"] == 2

    conn = store.get_connection()
    try:
        wid = conn.execute("SELECT work_item_id FROM work_items").fetchone()[0]
    finally:
        conn.close()
    dispatches = store.get_dispatches_for_work_item(wid)
    statuses = sorted(d["status"] for d in dispatches)
    assert statuses == ["DISPATCH_CONFIRMED_NO_WRITE", "DISPATCH_CONFIRMED_NO_WRITE"]
    # Terminal reconciliation confirmed for every destination.
    recons = store.get_reconciliations_for_work_item(wid)
    assert sorted(r["status"] for r in recons) == ["RECONCILED_CONFIRMED", "RECONCILED_CONFIRMED"]


def test_restart_does_not_duplicate_lifecycle_or_redispatch(tmp_path):
    supervisor, publisher = _lifecycle_supervisor(tmp_path)
    report = supervisor.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 1
    store_path = supervisor.store_path
    before = _counts(supervisor._store)

    # Restart: fresh supervisor instance over the SAME explicit production store.
    restarted, restarted_publisher = _lifecycle_supervisor(tmp_path)
    report2 = restarted.tick(now=INSIDE_WINDOW)
    assert report2["windows_dispatched"] == 0
    assert len(restarted_publisher.calls) == 0

    assert restarted.store_path == store_path
    after = _counts(restarted._store)
    # No duplicate durable rows after restart.
    for key in ("work_items", "outbox_messages", "platform_dispatches", "readbacks", "reconciliations"):
        assert after[key] == before[key], key


def test_unknown_write_stops_retry_and_requires_reconciliation(tmp_path):
    supervisor, publisher = _lifecycle_supervisor(tmp_path, publisher_status="UNKNOWN_WRITE")
    report = supervisor.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 1
    assert len(publisher.calls) == 2  # single attempt per destination, never blind-retried

    store = supervisor._store
    conn = store.get_connection()
    try:
        wid = conn.execute("SELECT work_item_id FROM work_items").fetchone()[0]
    finally:
        conn.close()
    dispatches = store.get_dispatches_for_work_item(wid)
    assert sorted(d["status"] for d in dispatches) == ["UNKNOWN_WRITE", "UNKNOWN_WRITE"]
    # No readback-derived reconciliation confirmed; reconciliation is pending operator recovery.
    assert _counts(store)["readbacks"] == 0
    recons = store.get_reconciliations_for_work_item(wid)
    assert sorted(r["status"] for r in recons) == [
        "RECONCILIATION_PENDING_OPERATOR_RECOVERY",
        "RECONCILIATION_PENDING_OPERATOR_RECOVERY",
    ]


def test_unknown_write_not_retried_on_restart(tmp_path):
    supervisor, publisher = _lifecycle_supervisor(tmp_path, publisher_status="UNKNOWN_WRITE")
    supervisor.tick(now=INSIDE_WINDOW)
    before_calls = len(publisher.calls)

    restarted, restarted_publisher = _lifecycle_supervisor(tmp_path, publisher_status="UNKNOWN_WRITE")
    report = restarted.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 0
    assert len(restarted_publisher.calls) == 0
    assert before_calls == 2  # unchanged; restart did not redispatch


def test_kill_switch_blocks_new_writes_but_allows_safe_readback(tmp_path):
    supervisor, publisher = _lifecycle_supervisor(tmp_path, mode="KILL_SWITCH")
    report = supervisor.tick(now=INSIDE_WINDOW)
    # Kill switch blocks dispatch of due windows.
    assert report["kill_switch_active"] is True
    assert report["windows_dispatched"] == 0
    assert len(publisher.calls) == 0

    # Direct lifecycle drive is also blocked under kill switch.
    outcome = supervisor.drive_canonical_publication_lifecycle(
        "editorial-window-ks", ["substack"], "pkg-ks"
    )
    assert outcome["kill_switch_blocked"] is True
    assert _counts(supervisor._store)["outbox_messages"] == 0

    # Safe read-back/reconciliation/recovery remains allowed.
    summary = supervisor.perform_safe_readback_and_reconciliation("editorial-window-ks")
    assert summary["window_id"] == "editorial-window-ks"


# --- Production epoch replay guard ------------------------------------------------


def _controlled_epoch_supervisor(tmp_path, *, epoch, clock_dt, calls):
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled, **kwargs):
        calls.append(run_id)
        return {"classification": "NO_PUBLICATION", "public_write_performed": False}

    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=_fixed_clock(clock_dt),
        newsroom_cycle=cycle,
        production_epoch_start_utc=epoch,
    )


def test_epoch_guard_blocks_window_started_before_epoch(tmp_path):
    calls = []
    # Window starts 13:00; epoch is 14:30 (after window start). The open window must not run.
    epoch = "2026-08-09T14:30:00Z"
    supervisor = _controlled_epoch_supervisor(tmp_path, epoch=epoch, clock_dt=INSIDE_WINDOW, calls=calls)
    report = supervisor.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 0
    assert calls == []


def test_epoch_guard_allows_window_started_after_epoch(tmp_path):
    calls = []
    # Epoch 12:00 is before the 13:00 window start -> window is eligible and runs.
    epoch = "2026-08-09T12:00:00Z"
    supervisor = _controlled_epoch_supervisor(tmp_path, epoch=epoch, clock_dt=INSIDE_WINDOW, calls=calls)
    report = supervisor.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 1
    assert len(calls) == 1


def test_epoch_persisted_and_survives_restart(tmp_path):
    calls = []
    epoch = "2026-08-09T14:30:00Z"
    first = _controlled_epoch_supervisor(tmp_path, epoch=epoch, clock_dt=INSIDE_WINDOW, calls=calls)
    assert first.production_epoch_start_utc == "2026-08-09T14:30:00Z"

    # Restart without passing the epoch: it must load from the durable store and still block.
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled, **kwargs):
        calls.append(run_id)
        return {"classification": "NO_PUBLICATION"}

    restarted = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=_fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=cycle,
    )
    assert restarted.production_epoch_start_utc == "2026-08-09T14:30:00Z"
    report = restarted.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 0


def test_no_deep_historical_backfill(tmp_path):
    calls = []
    # No epoch configured; the supervisor only ever considers today/yesterday windows, so a
    # window many days in the past can never become due or be backfilled.
    supervisor = _controlled_epoch_supervisor(
        tmp_path, epoch=None, clock_dt=datetime(2026, 8, 9, 14, tzinfo=timezone.utc), calls=calls
    )
    due = supervisor._due_windows(datetime(2026, 8, 9, 14, tzinfo=timezone.utc), None)
    assert len(due) == 1
    # The single due window is today's, not a deep-historical one.
    assert due[0]["start"].date().isoformat() == "2026-08-09"


# --- Architecture: no second state / publisher / orchestrator --------------------


def test_supervisor_reuses_canonical_durable_store_not_a_second_store(tmp_path):
    supervisor, _ = _lifecycle_supervisor(tmp_path)
    assert isinstance(supervisor._store, ContentOpsDurableStore)


def test_default_newsroom_cycle_is_canonical_facade(tmp_path):
    base = tmp_path / "default"
    base.mkdir(parents=True, exist_ok=True)
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=base / "store.sqlite3",
        output_root=base / "out",
        newsroom_cycle=None,
    )
    from live_contentops.eight_platform_substack_first_pipeline_v1 import (
        run_rolling_x_newsroom_cycle,
    )

    assert supervisor._newsroom_cycle is run_rolling_x_newsroom_cycle