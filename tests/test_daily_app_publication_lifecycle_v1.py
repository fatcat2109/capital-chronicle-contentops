"""Hard-gate tests for Final Daily App publication lifecycle.

Covers: production-epoch immutability, no synthetic readback success, strict readback
verification, public-object identity binding, real UNKNOWN_WRITE recovery, kill-switch
safety, restart idempotency, and controlled no-write fixtures never classified as real
public publication.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    ProductionEpochConflictError,
    RECONCILE_CONFIRMED,
    RECONCILE_CONTROLLED_NO_WRITE,
    RECONCILE_PENDING_READBACK,
    RECONCILE_PENDING_OPERATOR,
    RECONCILE_ABSENT_SAFE,
    STATUS_UNKNOWN_WRITE,
    STATUS_CONTROLLED_NO_WRITE,
    STATUS_DISPATCH_CONFIRMED,
)

WINDOW_START = datetime(2026, 8, 9, 13, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 8, 9, 15, tzinfo=timezone.utc)
INSIDE_WINDOW = datetime(2026, 8, 9, 14, tzinfo=timezone.utc)

EPOCH_A = "2026-08-09T13:27:00.663942Z"
EPOCH_DIFFERENT = "2026-08-09T14:00:00.000000Z"


def _fixed_clock(dt):
    return lambda: dt


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _plan_cycle(destinations=("substack",), package_identity="pkg-1"):
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


def _publisher(status="DISPATCH_CONFIRMED", public_object_id="obj-1", raise_exc=None, calls=None):
    def publisher(destination, package_identity):
        if calls is not None:
            calls.append((destination, package_identity))
        if raise_exc is not None:
            raise raise_exc
        result = {"status": status}
        if public_object_id is not None:
            result["public_object_id"] = public_object_id
        return result

    return publisher


def _readback(
    *,
    verified=True,
    public_object_id="obj-1",
    mismatch_dispatch=False,
    mismatch_destination=False,
    mismatch_object=False,
    raise_exc=None,
    empty=False,
    calls=None,
    write_occurred=None,
):
    def provider(dispatch_id, destination, expected_object):
        if calls is not None:
            calls.append((dispatch_id, destination, expected_object))
        if raise_exc is not None:
            raise raise_exc
        if empty:
            return {}
        payload = {
            "verified": verified,
            "dispatch_id": ("OTHER-DISPATCH" if mismatch_dispatch else dispatch_id),
            "destination": ("OTHER-DEST" if mismatch_destination else destination),
            "public_object_id": ("OTHER-OBJ" if mismatch_object else public_object_id),
        }
        if write_occurred is not None:
            payload["write_occurred"] = write_occurred
        return payload

    return provider


def _life(
    tmp_path,
    *,
    publisher,
    readback,
    clock=None,
    destinations=("substack",),
    package_identity="pkg-1",
    mode="AUTONOMOUS_DEFAULT",
    enable=True,
):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock or _fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=_plan_cycle(destinations=destinations, package_identity=package_identity),
        publication_publisher=publisher,
        publication_readback_provider=readback,
        enable_publication_lifecycle=enable,
    )


def _window_id(store):
    conn = store.get_connection()
    try:
        row = conn.execute(
            "SELECT work_item_id FROM work_items ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        return row["work_item_id"] if row else None
    finally:
        conn.close()


def _readback_rows(store):
    conn = store.get_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM readbacks ORDER BY dispatch_id").fetchall()]
    finally:
        conn.close()


def _recon_statuses(store, window_id):
    return sorted(r["status"] for r in store.get_reconciliations_for_work_item(window_id))


# --------------------------------------------------------------------------------------
# Production epoch immutability
# --------------------------------------------------------------------------------------


def _epoch_supervisor(tmp_path, epoch, clock=None):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=clock or _fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        production_epoch_start_utc=epoch,
    )


def test_epoch_initialized_once(tmp_path):
    sup = _epoch_supervisor(tmp_path, EPOCH_A)
    assert sup.production_epoch_start_utc == EPOCH_A
    assert sup._load_production_epoch() is not None


def test_same_epoch_restart_passes(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    # Restart supplying the exact same epoch -> idempotent PASS, no conflict.
    sup = _epoch_supervisor(tmp_path, EPOCH_A)
    assert sup.production_epoch_start_utc == EPOCH_A


def test_conflicting_epoch_fails_closed(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    with pytest.raises(ProductionEpochConflictError):
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)


def test_conflicting_epoch_does_not_mutate_persisted(tmp_path):
    before = _epoch_supervisor(tmp_path, EPOCH_A)._load_production_epoch()
    try:
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)
    except ProductionEpochConflictError:
        pass
    after = _epoch_supervisor(tmp_path, None)._load_production_epoch()
    assert before == after


def test_epoch_survives_restart_without_config(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    restarted = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=_fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
    )
    assert restarted.production_epoch_start_utc == EPOCH_A


def test_conflict_error_reports_both_instances(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    with pytest.raises(ProductionEpochConflictError) as exc:
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)
    msg = str(exc.value)
    assert "13:27:00.663942" in msg
    assert "14:00:00" in msg


# --------------------------------------------------------------------------------------
# Strict readback verification (no synthetic success)
# --------------------------------------------------------------------------------------


def _drive_single(tmp_path, *, publisher, readback, destinations=("substack",)):
    sup = _life(tmp_path, publisher=publisher, readback=readback, destinations=destinations)
    report = sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    return sup, report, wid


def test_matching_verified_readback_confirms(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=True, public_object_id="obj-1"),
    )
    assert report["public_write_performed"] is True
    assert report["unknown_write_detected"] is False
    assert _recon_statuses(sup._store, wid) == [RECONCILE_CONFIRMED]


def test_missing_readback_provider_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=None,
    )
    # A confirmed external write with no readback provider must fail closed.
    assert report["public_write_performed"] is True
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_readback_provider_exception_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(raise_exc=RuntimeError("boom")),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_verified_false_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=False),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_empty_readback_mapping_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(empty=True),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_mismatched_dispatch_identity_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(mismatch_dispatch=True),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_mismatched_destination_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(mismatch_destination=True),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_public_object_identity_mismatch_cannot_confirm(tmp_path):
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(mismatch_object=True),
    )
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_confirmed_without_public_object_id_fails_closed(tmp_path):
    # Publisher claims DISPATCH_CONFIRMED but supplies no public-object identity -> unverifiable.
    sup, report, wid = _drive_single(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, public_object_id=None),
        readback=_readback(verified=True),
    )
    assert report["unknown_write_detected"] is True
    assert report["public_write_performed"] is False
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_OPERATOR]


# --------------------------------------------------------------------------------------
# Controlled no-write is never a real public publication
# --------------------------------------------------------------------------------------


def test_controlled_no_write_never_real_publication(tmp_path):
    for status in ("DISPATCH_CONFIRMED_NO_WRITE", STATUS_CONTROLLED_NO_WRITE):
        sup = _life(
            tmp_path,
            publisher=_publisher(status, public_object_id=None),
            readback=None,
        )
        report = sup.tick(now=INSIDE_WINDOW)
        wid = _window_id(sup._store)
        assert report["public_write_performed"] is False
        assert report["unknown_write_detected"] is False
        statuses = _recon_statuses(sup._store, wid)
        assert statuses == [RECONCILE_CONTROLLED_NO_WRITE]
        # The dispatch row is recorded distinctly, not as a confirmed external write.
        dispatches = sup._store.get_dispatches_for_work_item(wid)
        assert all(d["status"] == STATUS_CONTROLLED_NO_WRITE for d in dispatches)


# --------------------------------------------------------------------------------------
# UNKNOWN_WRITE: single attempt, real recovery, kill-switch safety
# --------------------------------------------------------------------------------------


def test_unknown_write_single_publish_attempt(tmp_path):
    pub_calls = []
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None, calls=pub_calls),
        readback=None,
    )
    report = sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    assert report["unknown_write_detected"] is True
    assert len(pub_calls) == 1  # exactly one publication attempt, never retried
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_OPERATOR]
    dispatches = sup._store.get_dispatches_for_work_item(wid)
    assert all(d["status"] == STATUS_UNKNOWN_WRITE for d in dispatches)


def test_unknown_write_recovery_zero_publisher_calls_and_invokes_readback(tmp_path):
    pub_calls = []
    rb_calls = []
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None, calls=pub_calls),
        readback=_readback(verified=True, public_object_id="recovered-obj", calls=rb_calls),
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)

    summary = sup.perform_safe_readback_and_reconciliation(wid)
    assert summary["publisher_calls"] == 0  # recovery NEVER invokes the publisher
    assert summary["readback_calls"] == 1  # recovery DOES read back
    assert summary["per_dispatch"]
    assert len(pub_calls) == 1  # still only the original attempt
    assert _recon_statuses(sup._store, wid) == [RECONCILE_CONFIRMED]


def test_unknown_write_recovery_no_write_observed_absent_safe(tmp_path):
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None),
        readback=_readback(verified=True, public_object_id=None, write_occurred=False),
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    summary = sup.perform_safe_readback_and_reconciliation(wid)
    assert list(summary["per_dispatch"].values()) == [RECONCILE_ABSENT_SAFE]
    assert _recon_statuses(sup._store, wid) == [RECONCILE_ABSENT_SAFE]


def test_unknown_write_ambiguous_recovery_stays_pending(tmp_path):
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None),
        readback=_readback(verified=True, public_object_id=None),  # no object, no write_occurred
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    summary = sup.perform_safe_readback_and_reconciliation(wid)
    assert list(summary["per_dispatch"].values()) == [RECONCILE_PENDING_OPERATOR]
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_OPERATOR]


def test_unknown_write_recovery_repeated_does_not_duplicate_or_reinvoke(tmp_path):
    rb_calls = []
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None),
        readback=_readback(verified=True, public_object_id="recovered-obj", calls=rb_calls),
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    sup.perform_safe_readback_and_reconciliation(wid)
    rows_after_first = len(_readback_rows(sup._store))

    # Second recovery: dispatch already reconciled -> no provider re-invocation, no new rows.
    summary2 = sup.perform_safe_readback_and_reconciliation(wid)
    assert list(summary2["per_dispatch"].values()) == [RECONCILE_CONFIRMED]
    assert len(rb_calls) == 1
    assert len(_readback_rows(sup._store)) == rows_after_first


# --------------------------------------------------------------------------------------
# Kill switch safety
# --------------------------------------------------------------------------------------


def test_kill_switch_blocks_new_dispatch(tmp_path):
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=True, public_object_id="obj-1"),
        mode="KILL_SWITCH",
    )
    report = sup.tick(now=INSIDE_WINDOW)
    assert report["kill_switch_active"] is True
    assert report["windows_dispatched"] == 0
    assert _window_id(sup._store) is None  # no work item created under kill switch


def test_kill_switch_allows_unknown_write_recovery_never_publisher(tmp_path):
    # Establish an UNKNOWN_WRITE first (before kill switch).
    pub_calls = []
    rb_calls = []
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None, calls=pub_calls),
        readback=_readback(verified=True, public_object_id="obj-x", calls=rb_calls),
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)

    # Restart under KILL_SWITCH with the same store; recovery must read back but never dispatch.
    ks = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3",
        output_root=tmp_path / "out",
        operating_mode="KILL_SWITCH",
        clock=_fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=_plan_cycle(),
        publication_publisher=_publisher(STATUS_UNKNOWN_WRITE, calls=pub_calls),
        publication_readback_provider=_readback(verified=True, public_object_id="obj-x", calls=rb_calls),
        enable_publication_lifecycle=True,
    )
    report = ks.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 0  # kill switch made zero new dispatches

    summary = ks.perform_safe_readback_and_reconciliation(wid)
    assert summary["publisher_calls"] == 0
    assert summary["readback_calls"] == 1
    assert _recon_statuses(ks._store, wid) == [RECONCILE_CONFIRMED]
    assert len(pub_calls) == 1  # never redispatched


# --------------------------------------------------------------------------------------
# Restart idempotency (no duplicate durable rows)
# --------------------------------------------------------------------------------------


def test_restart_no_duplicate_lifecycle_rows(tmp_path):
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=True, public_object_id="obj-1"),
        destinations=("substack", "telegram"),
    )
    report = sup.tick(now=INSIDE_WINDOW)
    assert report["windows_dispatched"] == 1
    conn = sup._store.get_connection()
    try:
        before = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("work_items", "outbox_messages", "platform_dispatches", "readbacks", "reconciliations")
        }
    finally:
        conn.close()

    restarted = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=True, public_object_id="obj-1"),
        destinations=("substack", "telegram"),
    )
    report2 = restarted.tick(now=INSIDE_WINDOW)
    assert report2["windows_dispatched"] == 0
    conn = restarted._store.get_connection()
    try:
        after = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("work_items", "outbox_messages", "platform_dispatches", "readbacks", "reconciliations")
        }
    finally:
        conn.close()
    assert before == after


def test_pending_readback_stays_pending_after_restart(tmp_path):
    # Phase 8.D: an unresolved readback must remain unresolved after restart (fail-closed state
    # is durable, not silently upgraded to confirmed).
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=None,  # confirmed external write but no readback provider -> pending
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    assert _recon_statuses(sup._store, wid) == [RECONCILE_PENDING_READBACK]

    restarted = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=None,
    )
    restarted.tick(now=INSIDE_WINDOW)
    assert _recon_statuses(restarted._store, wid) == [RECONCILE_PENDING_READBACK]


def test_unknown_write_recovery_after_restart_is_readback_only(tmp_path):
    # Phase 8.F: after a restart, UNKNOWN_WRITE recovery performs readback only; the publisher is
    # never re-invoked and no duplicate durable rows are created.
    pub_calls = []
    rb_calls = []
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None, calls=pub_calls),
        readback=_readback(verified=True, public_object_id="post-restart-obj", calls=rb_calls),
    )
    sup.tick(now=INSIDE_WINDOW)
    wid = _window_id(sup._store)
    before_rows = len(_readback_rows(sup._store))

    restarted = _life(
        tmp_path,
        publisher=_publisher(STATUS_UNKNOWN_WRITE, public_object_id=None, calls=pub_calls),
        readback=_readback(verified=True, public_object_id="post-restart-obj", calls=rb_calls),
    )
    summary = restarted.perform_safe_readback_and_reconciliation(wid)
    assert summary["publisher_calls"] == 0
    assert summary["readback_calls"] == 1
    assert len(pub_calls) == 1  # single publish attempt ever
    assert _recon_statuses(restarted._store, wid) == [RECONCILE_CONFIRMED]
    assert len(_readback_rows(restarted._store)) == before_rows + 1
