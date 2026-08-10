"""Focused tests: public-object identity persistence, v4→v5 lossless migration,
durable-identity readback, restart-safe pending-readback recovery, and regression gates.

Covers TASK_CONTENTOPS_FINAL_DAILY_APP_PUBLIC_OBJECT_IDENTITY_PERSISTENCE_AND_RESTART_RECOVERY_V1
PHASE 14 required focused test matrix.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from live_contentops import historical_schema_compatibility_v1 as hist
from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    RECONCILE_CONFIRMED,
    RECONCILE_CONTROLLED_NO_WRITE,
    RECONCILE_PENDING_READBACK,
    STATUS_CONTROLLED_NO_WRITE,
    STATUS_DISPATCH_CONFIRMED,
    STATUS_UNKNOWN_WRITE,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    DispatchIdentityConflictError,
    SCHEMA_VERSION,
    compute_sha256,
)

INSIDE = datetime(2026, 8, 9, 14, tzinfo=timezone.utc)

# Frozen v1-v4 migration SQL checksums (byte-for-byte immutable evidence).
FROZEN_V1_V4_CHECKSUMS = {
    1: "184298f54e1b6bc4a359d3026d3a249bf85cd46beee1fbcda53d04db5a326cb9",
    2: "d4a35a066a106a705c09fbe1f3df1e8f66b95413936398e4158b55ef4ff3d849",
    3: "553ed20ea3c9d961047362df09e2c538c3269388caf27089da963366b44813cf",
    4: "3c2047f57ad8fa54915844c20196a283dcc21133299eb66e375c88052f1c0583",
}


# ---------------------------------------------------------------------------
# Phase 14 #1 — migrations 1-4 bytes/checksums remain unchanged
# ---------------------------------------------------------------------------


def test_migrations_1_to_4_bytes_and_checksums_unchanged():
    assert set(hist.CURRENT_MIGRATION_SQL.keys()) == {1, 2, 3, 4}
    assert dict(hist.CURRENT_MIGRATION_CHECKSUMS) == FROZEN_V1_V4_CHECKSUMS
    # The canonical schema is now v8 while v1-v4 SQL is untouched.
    assert hist.CANONICAL_SCHEMA_VERSION == SCHEMA_VERSION == 8
    # Frozen historical dependency manifests must NOT reference migrations v5/v6.
    assert set(hist.DEPENDENCY_MANIFEST["migration_sql_checksums"].keys()) == {1, 2, 3, 4}
    assert set(hist.DEPENDENCY_MANIFEST_V2["migration_sql_checksums"].keys()) == {1, 2, 3, 4}
    # Later manifests extend lineage without changing the frozen predecessors.
    assert hist.DEPENDENCY_MANIFEST_V3["migration_sql_checksums"][5] == hist.MIGRATION_V5_CHECKSUM
    assert hist.DEPENDENCY_MANIFEST_V4["migration_sql_checksums"][5] == hist.MIGRATION_V5_CHECKSUM
    assert hist.DEPENDENCY_MANIFEST_V4["migration_sql_checksums"][6] == hist.MIGRATION_V6_CHECKSUM
    assert hist.DEPENDENCY_MANIFEST_V5["migration_sql_checksums"][7] == hist.MIGRATION_V7_CHECKSUM
    assert hist.DEPENDENCY_MANIFEST_V6["migration_sql_checksums"][8] == hist.MIGRATION_V8_CHECKSUM


# ---------------------------------------------------------------------------
# Phase 14 #2-4 — v4→v5 lossless migration (fresh fixture), epoch, NULL identity
# ---------------------------------------------------------------------------


def _make_v4_store(tmp_path, name):
    store = ContentOpsDurableStore(tmp_path / name, auto_migrate=False)
    store.run_migrations(target_version=4)
    return store


def _seed_v4_rows(store):
    conn = store.get_connection()
    try:
        conn.execute("INSERT INTO work_items VALUES (?,?,?,?,?,?,?,?)",
                     ("wi_m", "story_m", "Migration Window", "EVIDENCE_READY", 2, "surf", "2026-08-09T13:00:00Z", "2026-08-09T14:00:00Z"))
        conn.execute("INSERT INTO outbox_messages VALUES (?,?,?,?,?,?)", ("om_m", "wi_m", "substack", "{}", "READY", "2026-08-09T14:00:00Z"))
        conn.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at) VALUES (?,?,?,?,?)",
                     ("pd_m", "om_m", "substack", "DISPATCH_CONFIRMED", "2026-08-09T14:00:00Z"))
        conn.execute("INSERT INTO metrics VALUES (?,?,?,?)",
                     ("metric_contentops_production_epoch_start_utc", "contentops_production_epoch_start_utc", 1786262820.663942, "x"))
    finally:
        conn.close()


def test_v4_to_v5_migration_lossless_epoch_and_null_identity(tmp_path):
    store = _make_v4_store(tmp_path, "lossless.sqlite3")
    _seed_v4_rows(store)
    conn = store.get_connection()
    try:
        pre_dispatch_ids = [r[0] for r in conn.execute("SELECT dispatch_id FROM platform_dispatches")]
        pre_epoch = conn.execute("SELECT metric_value FROM metrics WHERE metric_name='contentops_production_epoch_start_utc'").fetchone()[0]
    finally:
        conn.close()

    # Migrate 4 -> current canonical schema.
    store.run_migrations()
    assert store.get_current_schema_version() == 8
    assert store.verify_schema_integrity() is True

    conn = store.get_connection()
    try:
        post_dispatch_ids = [r[0] for r in conn.execute("SELECT dispatch_id FROM platform_dispatches")]
        post_epoch = conn.execute("SELECT metric_value FROM metrics WHERE metric_name='contentops_production_epoch_start_utc'").fetchone()[0]
        cols = [r[1] for r in conn.execute("PRAGMA table_info(platform_dispatches)")]
        identity = conn.execute("SELECT public_object_id, public_object_url, public_object_url_hash FROM platform_dispatches WHERE dispatch_id='pd_m'").fetchone()
        work_items = conn.execute("SELECT COUNT(*) FROM work_items").fetchone()[0]
    finally:
        conn.close()

    assert post_dispatch_ids == pre_dispatch_ids
    assert post_epoch == pre_epoch  # production epoch survives migration unchanged
    assert {"public_object_id", "public_object_url", "public_object_url_hash"}.issubset(cols)
    # Existing dispatches never had a persisted identity -> remain NULL (never fabricated).
    assert identity[0] is None and identity[1] is None and identity[2] is None
    assert work_items == 1


# ---------------------------------------------------------------------------
# Phase 14 #5-9 — write-once public-object identity
# ---------------------------------------------------------------------------


def _identity_store(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "id.sqlite3", auto_migrate=True)
    conn = store.get_connection()
    try:
        conn.execute("INSERT INTO work_items VALUES (?,?,?,?,?,?,?,?)",
                     ("wi_i", "story_i", "Identity Window", "EVIDENCE_READY", 2, "surf", "2026-08-09T13:00:00Z", "2026-08-09T14:00:00Z"))
        conn.execute("INSERT INTO outbox_messages VALUES (?,?,?,?,?,?)", ("om_i", "wi_i", "substack", "{}", "READY", "2026-08-09T14:00:00Z"))
    finally:
        conn.close()
    return store


def test_confirmed_dispatch_persists_identity_and_url_hash(tmp_path):
    store = _identity_store(tmp_path)
    url = "https://substack.com/@capitalchronicle/p-12345"
    row = store.register_platform_dispatch(
        dispatch_id="pd_identity", message_id="om_i", platform="substack",
        status="DISPATCH_CONFIRMED", public_object_id="object-A", public_object_url=url,
    )
    assert row["public_object_id"] == "object-A"
    assert row["public_object_url"] == url
    assert row["public_object_url_hash"] == hashlib.sha256(url.encode()).hexdigest()

    got = store.get_platform_dispatch("pd_identity")
    assert got["public_object_id"] == "object-A"


def test_url_hash_deterministic_over_exact_url(tmp_path):
    store = _identity_store(tmp_path)
    url = "https://example.com/post/xyz"
    r1 = store.register_platform_dispatch(dispatch_id="pd_u1", message_id="om_i", platform="substack",
                                          status="DISPATCH_CONFIRMED", public_object_id="obj", public_object_url=url)
    r2 = store.register_platform_dispatch(dispatch_id="pd_u2", message_id="om_i", platform="substack",
                                          status="DISPATCH_CONFIRMED", public_object_id="obj2", public_object_url=url)
    assert r1["public_object_url_hash"] == r2["public_object_url_hash"] == compute_sha256(url)


def test_same_identity_replay_idempotent(tmp_path):
    store = _identity_store(tmp_path)
    a = store.register_platform_dispatch(dispatch_id="pd_idem", message_id="om_i", platform="substack",
                                         status="DISPATCH_CONFIRMED", public_object_id="object-X", public_object_url="https://x/a")
    b = store.register_platform_dispatch(dispatch_id="pd_idem", message_id="om_i", platform="substack",
                                         status="DISPATCH_CONFIRMED", public_object_id="object-X", public_object_url="https://x/a")
    assert a["public_object_id"] == b["public_object_id"] == "object-X"
    conn = store.get_connection()
    try:
        n = conn.execute("SELECT COUNT(*) FROM platform_dispatches WHERE dispatch_id='pd_idem'").fetchone()[0]
    finally:
        conn.close()
    assert n == 1


def test_conflicting_public_object_id_fails_closed(tmp_path):
    store = _identity_store(tmp_path)
    store.register_platform_dispatch(dispatch_id="pd_conf", message_id="om_i", platform="substack",
                                     status="DISPATCH_CONFIRMED", public_object_id="object-C1")
    with pytest.raises(DispatchIdentityConflictError):
        store.register_platform_dispatch(dispatch_id="pd_conf", message_id="om_i", platform="substack",
                                         status="DISPATCH_CONFIRMED", public_object_id="object-C2")
    # Original identity unchanged.
    assert store.get_platform_dispatch("pd_conf")["public_object_id"] == "object-C1"


def test_conflicting_public_object_url_fails_closed(tmp_path):
    store = _identity_store(tmp_path)
    store.register_platform_dispatch(dispatch_id="pd_url", message_id="om_i", platform="substack",
                                     status="DISPATCH_CONFIRMED", public_object_id="object-U", public_object_url="https://x/one")
    with pytest.raises(DispatchIdentityConflictError):
        store.register_platform_dispatch(dispatch_id="pd_url", message_id="om_i", platform="substack",
                                         status="DISPATCH_CONFIRMED", public_object_id="object-U", public_object_url="https://x/two")
    assert store.get_platform_dispatch("pd_url")["public_object_url"] == "https://x/one"


# ---------------------------------------------------------------------------
# Supervisor lifecycle fixtures
# ---------------------------------------------------------------------------


def _plan_cycle(destinations=("substack",), package_identity="pkg-1"):
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled, **kwargs):
        return {
            "classification": "PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1",
            "publication_lifecycle_plan": {"ready_destinations": list(destinations), "package_identity": package_identity},
            "public_write_performed": False, "unknown_write_detected": False,
        }
    return cycle


def _life(tmp_path, *, publisher, readback, mode="AUTONOMOUS_DEFAULT"):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3", output_root=tmp_path / "out",
        clock=lambda: INSIDE, operating_mode=mode, newsroom_cycle=_plan_cycle(),
        publication_publisher=publisher, publication_readback_provider=readback,
        enable_publication_lifecycle=True,
    )


def _wid(store):
    conn = store.get_connection()
    try:
        r = conn.execute("SELECT work_item_id FROM work_items ORDER BY updated_at DESC LIMIT 1").fetchone()
        return r["work_item_id"] if r else None
    finally:
        conn.close()


def _recon(store, wid):
    return sorted(r["status"] for r in store.get_reconciliations_for_work_item(wid))


# ---------------------------------------------------------------------------
# Phase 14 #10-16 — durable-identity readback + restart-safe pending recovery
# ---------------------------------------------------------------------------


def _rb_provider(object_id, *, calls, dispatch_mismatch=False, dest_mismatch=False, obj_mismatch=False):
    def provider(dispatch_id, destination, expected_object):
        calls.append((dispatch_id, destination, expected_object))
        return {
            "verified": True,
            "dispatch_id": ("WRONG-DISPATCH" if dispatch_mismatch else dispatch_id),
            "destination": ("WRONG-DEST" if dest_mismatch else destination),
            "public_object_id": ("object-OTHER" if obj_mismatch else object_id),
        }
    return provider


def test_case_a_real_confirmed_persists_identity_and_restart_idempotent(tmp_path):
    pub_calls = []
    rb_calls = []
    def publisher(destination, package_identity):
        pub_calls.append(destination)
        return {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-A", "public_object_url": "https://x/a"}
    sup = _life(tmp_path, publisher=publisher, readback=_rb_provider("object-A", calls=rb_calls))
    report = sup.tick(now=INSIDE)
    wid = _wid(sup._store)
    assert report["public_write_performed"] is True
    assert _recon(sup._store, wid) == [RECONCILE_CONFIRMED]
    disp = sup._store.get_dispatches_for_work_item(wid)[0]
    assert disp["public_object_id"] == "object-A"
    assert disp["public_object_url"] == "https://x/a"
    # Immediate readback resolved the durable identity.
    assert rb_calls and rb_calls[0][2] == "object-A"

    # Restart: no duplicate dispatch/readback/reconciliation.
    before = sup._store.get_dispatches_for_work_item(wid)
    restarted = _life(tmp_path, publisher=publisher, readback=_rb_provider("object-A", calls=[]))
    report2 = restarted.tick(now=INSIDE)
    assert report2["windows_dispatched"] == 0
    assert restarted._store.get_dispatches_for_work_item(wid) == before


def test_case_b_pending_readback_restart_recovery_zero_publisher(tmp_path):
    pub_calls = []
    def publisher(destination, package_identity):
        pub_calls.append(destination)
        return {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-B", "public_object_url": "https://x/b"}
    # Initial readback unavailable -> identity persists but reconciliation stays pending.
    sup = _life(tmp_path, publisher=publisher, readback=None)
    sup.tick(now=INSIDE)
    wid = _wid(sup._store)
    disp = sup._store.get_dispatches_for_work_item(wid)[0]
    assert disp["status"] == STATUS_DISPATCH_CONFIRMED
    assert disp["public_object_id"] == "object-B"
    assert _recon(sup._store, wid) == [RECONCILE_PENDING_READBACK]

    # Restart with readback enabled -> recovery reads back the stored object-B, zero publisher calls.
    rb_calls = []
    restarted = _life(tmp_path, publisher=publisher, readback=_rb_provider("object-B", calls=rb_calls))
    report = restarted.tick(now=INSIDE)
    assert report["windows_dispatched"] == 0
    summary = restarted.perform_safe_readback_and_reconciliation(wid)
    assert summary["publisher_calls"] == 0
    assert summary["readback_calls"] == 1
    # Recovery invoked readback with the exact stored identity (object-B).
    assert rb_calls[0][2] == "object-B"
    assert _recon(restarted._store, wid) == [RECONCILE_CONFIRMED]


def test_immediate_readback_uses_durable_identity(tmp_path):
    rb_calls = []
    def publisher(destination, package_identity):
        return {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-D", "public_object_url": "https://x/d"}
    sup = _life(tmp_path, publisher=publisher, readback=_rb_provider("object-D", calls=rb_calls))
    sup.tick(now=INSIDE)
    assert rb_calls and rb_calls[0][2] == "object-D"  # readback received the durable identity


def test_case_d_wrong_readback_object_cannot_confirm(tmp_path):
    rb_calls = []
    def publisher(destination, package_identity):
        return {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-D1", "public_object_url": "https://x/d1"}
    sup = _life(tmp_path, publisher=publisher, readback=_rb_provider("object-D1", calls=rb_calls, obj_mismatch=True))
    sup.tick(now=INSIDE)
    wid = _wid(sup._store)
    # Readback observed a DIFFERENT object -> cannot confirm.
    assert _recon(sup._store, wid) == [RECONCILE_PENDING_READBACK]


def test_case_e_controlled_no_write_has_no_fake_identity(tmp_path):
    def publisher(destination, package_identity):
        return {"status": "DISPATCH_CONFIRMED_NO_WRITE"}
    sup = _life(tmp_path, publisher=publisher, readback=None)
    sup.tick(now=INSIDE)
    wid = _wid(sup._store)
    disp = sup._store.get_dispatches_for_work_item(wid)[0]
    assert disp["status"] == STATUS_CONTROLLED_NO_WRITE
    assert disp["public_object_id"] is None  # no fabricated external identity
    assert disp["public_object_url"] is None
    assert _recon(sup._store, wid) == [RECONCILE_CONTROLLED_NO_WRITE]
    assert sup.tick(now=INSIDE)["public_write_performed"] is False


def test_case_f_unknown_write_gates_preserved(tmp_path):
    pub_calls = []
    def publisher(destination, package_identity):
        pub_calls.append(destination)
        return {"status": "UNKNOWN_WRITE"}
    sup = _life(tmp_path, publisher=publisher, readback=None)
    sup.tick(now=INSIDE)
    wid = _wid(sup._store)
    disp = sup._store.get_dispatches_for_work_item(wid)[0]
    assert disp["status"] == STATUS_UNKNOWN_WRITE
    assert len(pub_calls) == 1  # exactly one publish attempt, never retried
    # Recovery reads back but never redispatches.
    rb_calls = []
    summary = sup.perform_safe_readback_and_reconciliation(wid, readback_provider=_rb_provider("obj-uw", calls=rb_calls))
    assert summary["publisher_calls"] == 0
    assert len(pub_calls) == 1


# ---------------------------------------------------------------------------
# Phase 14 #19-21 — kill switch, restart, production-store row preservation
# ---------------------------------------------------------------------------


def test_kill_switch_allows_readback_only_recovery(tmp_path):
    pub_calls = []
    def publisher(destination, package_identity):
        pub_calls.append(destination)
        return {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-K", "public_object_url": "https://x/k"}
    sup = _life(tmp_path, publisher=publisher, readback=None)
    sup.tick(now=INSIDE)
    wid = _wid(sup._store)

    # Restart under KILL_SWITCH; recovery reads back, zero publisher calls, zero new dispatch.
    rb_calls = []
    ks = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3", output_root=tmp_path / "out",
        clock=lambda: INSIDE, operating_mode="KILL_SWITCH", newsroom_cycle=_plan_cycle(),
        publication_publisher=publisher, publication_readback_provider=_rb_provider("object-K", calls=rb_calls),
        enable_publication_lifecycle=True,
    )
    report = ks.tick(now=INSIDE)
    assert report["windows_dispatched"] == 0
    summary = ks.perform_safe_readback_and_reconciliation(wid)
    assert summary["publisher_calls"] == 0
    assert summary["readback_calls"] == 1
    assert _recon(ks._store, wid) == [RECONCILE_CONFIRMED]
    assert len(pub_calls) == 1


def test_missing_durable_identity_cannot_be_guessed(tmp_path):
    store = _identity_store(tmp_path)
    # Manually create a confirmed dispatch with NO persisted identity.
    conn = store.get_connection()
    try:
        conn.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id) VALUES (?,?,?,?,?,?)",
                     ("pd_no_id", "om_i", "substack", "DISPATCH_CONFIRMED", "2026-08-09T14:00:00Z", None))
    finally:
        conn.close()
    got = store.get_platform_dispatch("pd_no_id")
    assert got["public_object_id"] is None  # nothing fabricated
