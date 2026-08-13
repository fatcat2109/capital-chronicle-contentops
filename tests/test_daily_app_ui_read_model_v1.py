from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor
from live_contentops.daily_app_ui_read_model_v1 import (
    DailyAppReadModelError,
    build_daily_app_snapshot,
    update_daily_app_mode,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    OperatingModeConflictError,
)
from live_contentops.server import make_handler

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _store(tmp_path, name="daily.sqlite3"):
    return ContentOpsDurableStore(tmp_path / name, now_fn=lambda: NOW)


def _seed_dispatch(store, *, suffix, status, object_id=None, reconciliation=None):
    work_id = f"work_{suffix}"
    message_id = f"outbox_{suffix}"
    dispatch_id = f"dispatch_{suffix}"
    store.create_work_item(
        story_id=f"story_{suffix}", title=f"Story {suffix}", target_surface="substack",
        work_item_id=work_id,
    )
    store.register_outbox_message(
        message_id=message_id, work_item_id=work_id, destination="substack",
        payload="{}", status="READY",
    )
    store.register_platform_dispatch(
        dispatch_id=dispatch_id, message_id=message_id, platform="substack",
        status=status, public_object_id=object_id,
    )
    if reconciliation:
        store.register_reconciliation(
            reconciliation_id=f"reconciliation_{suffix}", work_item_id=work_id,
            status=reconciliation,
        )
    return dispatch_id


def _seed_policy(
    store,
    *,
    version,
    parent=None,
    status="ACTIVE",
    decision="BOOTSTRAP",
    sample_count=0,
    confidence=0.0,
    payload=None,
    created_at="2026-08-10T01:00:00Z",
):
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO learning_policy_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                version,
                parent,
                created_at,
                status,
                decision,
                sample_count,
                confidence,
                "formula.v1",
                "[]",
                "rolling",
                "{}",
                "{}",
                None,
                "fixture lineage",
                json.dumps(payload or {}, sort_keys=True),
                f"hash-{version}",
            ),
        )


def _publication(snapshot, dispatch_id):
    return next(row for row in snapshot["published"]["objects"] if row["dispatch_id"] == dispatch_id)


def _lifecycle_counts(store):
    with store.get_connection() as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("outbox_messages", "platform_dispatches", "readbacks", "reconciliations")
        }


def test_snapshot_healthy_idle_no_fixture_and_no_second_store(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    before = {path.name for path in tmp_path.iterdir()}
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    after = {path.name for path in tmp_path.iterdir()}
    assert snapshot["runtime"]["controller_health"] == "HEALTHY"
    assert snapshot["authority"]["fixture_fallback"] is False
    assert snapshot["authority"]["snapshot_mutates_lifecycle"] is False
    # SQLite may materialize its own WAL companions while another collected test keeps a
    # connection alive; those files are part of daily.sqlite3, not a second authority store.
    assert after - before <= {"daily.sqlite3-wal", "daily.sqlite3-shm"}
    assert {name for name in after if name.endswith(".sqlite3")} == {"daily.sqlite3"}


def test_historical_unlinked_and_terminal_incidents_are_not_active(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    store.register_incident(
        incident_id="historical-unlinked", work_item_id=None, severity="HIGH",
        description="Historical safe failure",
    )
    store.create_work_item(
        story_id="story-terminal", title="Terminal", target_surface="substack",
        work_item_id="work-terminal",
    )
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE work_items SET current_state='COMPLETE' WHERE work_item_id='work-terminal'"
        )
    store.register_incident(
        incident_id="historical-terminal", work_item_id="work-terminal", severity="MEDIUM",
        description="Resolved lifecycle incident",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["incidents"]["active_count"] == 0
    assert snapshot["incidents"]["items"] == []
    assert snapshot["incidents"]["history_count"] == 2
    assert all(not row["current_actionable"] for row in snapshot["incidents"]["recent_history"])


def test_linkedin_persisted_browser_readiness_is_overridden_by_official_api_auth_state(tmp_path):
    store = _store(tmp_path)
    store.upsert_destination_readiness(row={
        "surface": "LINKEDIN_POST",
        "platform": "linkedin",
        "transport_registry_version": "contentops.destination_transport_registry.v1",
        "transport_type": "EDGE_CDP",
        "readiness_state": "READY_AUTHENTICATED",
        "destination_identity": "historical-browser-identity",
        "identity_match": True,
        "write_eligible": True,
        "probe_kind": "EDGE_CDP_IDENTITY",
        "probed_at_utc": "2026-08-10T11:00:00Z",
        "sanitized_detail": {},
    })
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    linkedin = next(
        row for row in snapshot["platforms"]["destinations"]
        if row["platform_id"] == "linkedin"
    )
    assert linkedin["readiness"] == "AUTH_UNAVAILABLE"
    assert linkedin["transport_type"] == "OFFICIAL_MEMBER_API"
    assert linkedin["write_eligible"] is False
    incident = next(
        row["incident_id"] == "derived:readiness:LINKEDIN_POST"
        and row
        for row in snapshot["incidents"]["items"]
    )
    assert incident["what_happened"] == "AUTH_UNAVAILABLE"
    assert "official-member OAuth" in incident["operator_action"]


def test_linkedin_official_member_api_auth_projection_is_sanitized(tmp_path):
    store = _store(tmp_path)
    store.upsert_destination_readiness(row={
        "surface": "LINKEDIN_POST",
        "platform": "linkedin",
        "transport_registry_version": "contentops.destination_transport_registry.v2",
        "transport_type": "OFFICIAL_MEMBER_API",
        "readiness_state": "READY_NON_BROWSER_BINDING",
        "destination_identity": "Jim Pham",
        "identity_match": True,
        "write_eligible": True,
        "probe_kind": "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA",
        "probed_at_utc": "2026-08-13T11:00:00Z",
        "sanitized_detail": {
            "authenticated": True,
            "official_api_state": "READY_OFFICIAL_MEMBER_API",
            "expiry_at_utc": "2026-10-12T11:00:00Z",
            "days_remaining": 60,
            "readback_capability": "READBACK_CAPABILITY_LIMITED",
            "secure_store_binding": "WINDOWS_DPAPI_CURRENT_USER:contentops.linkedin.member.v1",
            "cdp_navigation_performed": False,
            "network_probe_performed": False,
        },
    })
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    linkedin = next(row for row in snapshot["platforms"]["destinations"] if row["platform_id"] == "linkedin")
    assert linkedin["readiness"] == "READY_OFFICIAL_MEMBER_API"
    assert linkedin["write_eligible"] is True
    assert linkedin["authenticated"] is True
    assert linkedin["auth_expiry_at_utc"] == "2026-10-12T11:00:00Z"
    assert linkedin["auth_days_remaining"] == 60
    assert linkedin["safe_identity"] == "Jim Pham"
    assert linkedin["transport_type"] == "OFFICIAL_MEMBER_API"
    assert linkedin["readback_capability"] == "READBACK_CAPABILITY_LIMITED"


def test_publication_lifecycle_classes_are_exact(tmp_path):
    store = _store(tmp_path)
    real = _seed_dispatch(
        store, suffix="real", status="DISPATCH_CONFIRMED", object_id="public-123",
        reconciliation="RECONCILED_CONFIRMED",
    )
    pending = _seed_dispatch(
        store, suffix="pending", status="DISPATCH_CONFIRMED", object_id="public-456",
        reconciliation="RECONCILIATION_PENDING_READBACK",
    )
    incomplete = _seed_dispatch(
        store, suffix="incomplete", status="DISPATCH_CONFIRMED", object_id="public-789",
        reconciliation="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE",
    )
    unknown = _seed_dispatch(
        store, suffix="unknown", status="UNKNOWN_WRITE",
        reconciliation="RECONCILIATION_PENDING_OPERATOR_RECOVERY",
    )
    controlled = _seed_dispatch(
        store, suffix="controlled", status="CONTROLLED_NO_PUBLIC_WRITE",
        reconciliation="RECONCILED_CONTROLLED_NO_WRITE",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert _publication(snapshot, real)["lifecycle_classification"] == "REAL_PUBLICATION_CONFIRMED"
    assert _publication(snapshot, real)["public_object_id"] == "public-123"
    assert _publication(snapshot, pending)["lifecycle_classification"] == "CONFIRMED_DISPATCH_PENDING_READBACK"
    assert _publication(snapshot, incomplete)["lifecycle_classification"] == (
        "CONFIRMED_PUBLICATION_CONTENT_INCOMPLETE"
    )
    assert _publication(snapshot, unknown)["lifecycle_classification"] == "UNKNOWN_WRITE"
    assert _publication(snapshot, controlled)["lifecycle_classification"] == "CONTROLLED_NO_PUBLIC_WRITE"
    assert snapshot["published"]["real_publication_count"] == 1
    assert snapshot["published"]["controlled_no_public_write_count"] == 1
    # The pending dispatch and UNKNOWN_WRITE require recovery; the terminal incomplete object
    # does not.
    assert snapshot["published"]["pending_readback_count"] == 2
    assert any(item["what_happened"] == "UNKNOWN_WRITE" for item in snapshot["incidents"]["items"])


def test_confirmed_dispatch_without_readback_is_counted_for_recovery(tmp_path):
    store = _store(tmp_path)
    pending = _seed_dispatch(
        store, suffix="no-readback", status="DISPATCH_CONFIRMED", object_id="public-pending"
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert _publication(snapshot, pending)["lifecycle_classification"] == "CONFIRMED_DISPATCH_PENDING_READBACK"
    assert snapshot["published"]["pending_readback_count"] == 1
    assert any(item["kind"] == "LIFECYCLE_RECOVERY" for item in snapshot["queue"]["items"])


def test_no_publication_and_platform_unavailable_are_truthful(tmp_path):
    store = _store(tmp_path)
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["published"]["empty_reason"] == "NO_REAL_PUBLICATIONS_YET"
    assert snapshot["published"]["real_publication_count"] == 0
    assert {row["readiness"] for row in snapshot["platforms"]["destinations"]} == {
        "READINESS_NOT_PROBED",
    }
    assert not any(row["write_eligible"] for row in snapshot["platforms"]["destinations"])


def test_due_observation_preserves_unavailable_metric_not_zero(tmp_path):
    store = _store(tmp_path)
    dispatch = _seed_dispatch(
        store, suffix="metric", status="DISPATCH_CONFIRMED", object_id="public-metric",
        reconciliation="RECONCILED_CONFIRMED",
    )
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO performance_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "obs_due", "contentops.performance_observation.v1", dispatch, "work_metric",
                "substack", "public-metric", None, "EARLY", "2026-08-10T11:00:00Z",
                None, "collector.v1", "SCHEDULED", "{}",
                json.dumps({"shares": "UNAVAILABLE"}), "canonical", "hash", 1,
            ),
        )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    observation = snapshot["performance"]["observations"][0]
    assert observation["metric_availability"]["shares"] == "UNAVAILABLE"
    assert "shares" not in observation["native_metrics"]
    assert snapshot["queue"]["due_performance_observation_count"] == 1


def test_learning_bootstrap_child_and_rollback_lineage(tmp_path):
    store = _store(tmp_path)
    rows = [
        ("bootstrap", None, "RETIRED", "HOLD_NO_POLICY_CHANGE", 0, 0.0, None),
        ("child", "bootstrap", "RETIRED", "ACCEPT_BOUNDED_UPDATE", 8, 0.9, "bootstrap"),
        ("rollback", "child", "ACTIVE", "ROLLBACK", 16, 0.95, "child"),
    ]
    with store.get_connection() as conn:
        for index, (version, parent, status, decision, sample, confidence, rollback) in enumerate(rows):
            payload = json.dumps({"timing_offset_minutes": index * 5})
            conn.execute(
                "INSERT INTO learning_policy_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (version, parent, f"2026-08-10T0{index}:00:00Z", status, decision, sample,
                 confidence, "formula.v1", "[]", "rolling", "{}", "{}", rollback,
                 "fixture lineage", payload, f"hash-{index}"),
            )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["learning"]["active_policy"]["policy_version"] == "rollback"
    assert snapshot["learning"]["active_policy"]["parent_policy_version"] == "child"
    assert snapshot["learning"]["active_policy"]["rollback_reference"] == "child"
    bootstrap = next(row for row in snapshot["learning"]["policy_history"] if row["policy_version"] == "bootstrap")
    child = next(row for row in snapshot["learning"]["policy_history"] if row["policy_version"] == "child")
    assert bootstrap["provenance"] == "CONFIGURED_DEFAULT"
    assert child["provenance"] == "LEARNED"
    assert snapshot["learning"]["active_policy"]["provenance"] == "LEARNED"
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "LEARNED_ACTIVE_POLICY"


def test_active_bootstrap_policy_remains_configured_default_everywhere(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.bootstrap.v1",
        decision="BOOTSTRAP",
        sample_count=0,
        confidence=0.0,
        payload={
            "timing": {"offset_minutes": 0},
            "provenance": "CONFIGURED_DEFAULT",
        },
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    active = snapshot["learning"]["active_policy"]
    assert active["status"] == "ACTIVE"
    assert active["sample_count"] == 0
    assert active["confidence"] == 0.0
    assert active["provenance"] == "CONFIGURED_DEFAULT"
    assert {row["provenance"] for row in snapshot["queue"]["upcoming_editorial_windows"]} == {
        "CONFIGURED_DEFAULT"
    }
    assert {row["state"] for row in snapshot["queue"]["items"]} == {"CONFIGURED_DEFAULT"}
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "CONFIGURED_DEFAULT"


def test_active_status_and_sample_count_cannot_create_learned_lineage(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.configured.v2",
        status="ACTIVE",
        decision="HOLD_NO_POLICY_CHANGE",
        sample_count=99,
        confidence=0.99,
        payload={"timing": {"offset_minutes": 0}},
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["learning"]["active_policy"]["provenance"] == "CONFIGURED_DEFAULT"
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "CONFIGURED_DEFAULT"


def test_genuine_learned_child_controls_window_provenance_and_nested_offset(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.bootstrap.v1",
        status="SUPERSEDED",
        payload={"timing": {"offset_minutes": 0}, "provenance": "CONFIGURED_DEFAULT"},
    )
    _seed_policy(
        store,
        version="policy.learned.v2",
        parent="policy.bootstrap.v1",
        decision="ACCEPT_BOUNDED_UPDATE",
        sample_count=8,
        confidence=0.9,
        payload={"timing": {"offset_minutes": 15}, "provenance": "LEARNED_BOUNDED_UPDATE"},
        created_at="2026-08-10T02:00:00Z",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    active = snapshot["learning"]["active_policy"]
    assert active["provenance"] == "LEARNED"
    assert active["timing_offset_minutes"] == 15
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "LEARNED_ACTIVE_POLICY"
    assert snapshot["runtime"]["next_editorial_window"]["window_start_utc"] == "2026-08-10T12:15:00Z"


def test_kill_switch_cas_restart_and_zero_calls(tmp_path):
    store = _store(tmp_path)
    initial = store.get_operating_control()
    updated = update_daily_app_mode(
        store.db_path, expected_state_version=initial["state_version"], operating_mode="KILL_SWITCH"
    )
    assert updated["operating_mode"] == "KILL_SWITCH"
    with pytest.raises(OperatingModeConflictError):
        update_daily_app_mode(store.db_path, expected_state_version=initial["state_version"], operating_mode="SHADOW_ONLY")
    with pytest.raises(ValueError):
        update_daily_app_mode(store.db_path, expected_state_version=updated["state_version"], operating_mode="UNSAFE")

    calls = {"newsroom": 0, "publisher": 0}
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=store.db_path, output_root=tmp_path / "output", store=store,
        newsroom_cycle=lambda **_: calls.__setitem__("newsroom", calls["newsroom"] + 1),
        publication_publisher=lambda *_: calls.__setitem__("publisher", calls["publisher"] + 1),
    )
    assert supervisor.operating_mode == "KILL_SWITCH"
    result = supervisor.drive_canonical_publication_lifecycle("not-created", ["substack"], "pkg")
    assert result["kill_switch_blocked"] is True
    assert calls == {"newsroom": 0, "publisher": 0}


def test_malformed_store_fails_closed(tmp_path):
    malformed = tmp_path / "malformed.sqlite3"
    malformed.touch()
    with pytest.raises(DailyAppReadModelError):
        build_daily_app_snapshot(malformed, now=NOW)


def test_snapshot_and_mode_api_are_bounded_and_launcher_stays_quarantined(tmp_path):
    store = _store(tmp_path)
    before = _lifecycle_counts(store)
    server = HTTPServer(("127.0.0.1", 0), make_handler(store.db_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{root}/api/daily-app/snapshot") as response:
            assert response.status == 200
            assert json.load(response)["authority"]["fixture_fallback"] is False
        request = Request(f"{root}/api/run-pipeline", method="POST")
        with pytest.raises(HTTPError) as blocked:
            urlopen(request)
        assert blocked.value.code == 423
        malformed = Request(
            f"{root}/api/daily-app/control/mode", method="POST", data=b'{"operating_mode":"KILL_SWITCH"}',
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5173"},
        )
        with pytest.raises(HTTPError) as bad:
            urlopen(malformed)
        assert bad.value.code == 400
        valid = Request(
            f"{root}/api/daily-app/control/mode", method="POST",
            data=json.dumps({"operating_mode": "SHADOW_ONLY", "expected_state_version": 1}).encode(),
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5173"},
        )
        with urlopen(valid) as changed:
            assert changed.status == 200
            assert json.load(changed)["control"]["operating_mode"] == "SHADOW_ONLY"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    after = _lifecycle_counts(store)
    assert server.server_address[0] == "127.0.0.1"
    assert before == after
    assert store.get_operating_control()["operating_mode"] == "SHADOW_ONLY"


def test_snapshot_keyspace_contains_no_secret_shapes(tmp_path):
    snapshot = build_daily_app_snapshot(_store(tmp_path).db_path, now=NOW)
    encoded = json.dumps(snapshot).lower()
    for forbidden in ('"token"', '"password"', '"cookie"', '"authorization"', 'private_key'):
        assert forbidden not in encoded
