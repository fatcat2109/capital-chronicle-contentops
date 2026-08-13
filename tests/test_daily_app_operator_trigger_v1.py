from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer
from pathlib import Path

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    TRIGGER_OPERATOR_REQUESTED,
    ContentOpsDailyAppSupervisor,
)
from live_contentops.daily_app_ui_read_model_v1 import request_operator_cycle
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    OperatingModeConflictError,
    OperatorTriggerAlreadyPendingError,
)
from live_contentops.server import make_handler

FIXED_NOW = datetime(2026, 8, 10, 4, 30, 0, tzinfo=timezone.utc)


def _fixed_clock():
    return lambda: FIXED_NOW


def _controlled_cycle(calls: list):
    def cycle(**kwargs):
        calls.append(dict(kwargs))
        return {
            "classification": "NO_PUBLICATION",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }
    return cycle


def _supervisor(tmp_path: Path, *, mode: str = "AUTONOMOUS_DEFAULT", cycle_factory=None, clock=None):
    calls: list = []
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "store.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock or _fixed_clock(),
    )
    supervisor._newsroom_cycle = (cycle_factory or _controlled_cycle)(calls)
    return supervisor, calls


def _store(tmp_path: Path, name: str = "store.sqlite3") -> ContentOpsDurableStore:
    store = ContentOpsDurableStore(tmp_path / name)
    assert store.get_current_schema_version() == 9
    return store


def test_schema_v9_is_append_only_operator_triggers_table(tmp_path):
    store = _store(tmp_path)
    with store.get_connection() as conn:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(operator_cycle_triggers)")]
    assert columns == [
        "trigger_id", "trigger_kind", "requested_at_utc", "requested_mode",
        "control_state_version", "state", "consumed_at_utc", "consumed_window_id",
        "consumption_detail",
    ]


def test_record_trigger_is_durable_and_single_pending(tmp_path):
    store = _store(tmp_path)
    record = store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0001",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
    )
    assert record["state"] == "PENDING"
    assert record["trigger_kind"] == "OPERATOR_REQUESTED"
    with pytest.raises(OperatorTriggerAlreadyPendingError):
        store.record_operator_cycle_trigger(
            trigger_id="operator-trigger-test0002",
            requested_mode="AUTONOMOUS_DEFAULT",
            control_state_version=1,
        )
    pending = store.fetch_pending_operator_trigger()
    assert pending is not None and pending["trigger_id"] == "operator-trigger-test0001"


def test_consume_trigger_is_exactly_once(tmp_path):
    store = _store(tmp_path)
    store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0003",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
    )
    assert store.consume_operator_cycle_trigger(
        "operator-trigger-test0003", window_id="operator-requested-operator-trigger-test0003",
        detail="EXECUTED:NO_PUBLICATION",
    ) is True
    assert store.consume_operator_cycle_trigger(
        "operator-trigger-test0003", window_id="x", detail="EXECUTED:NO_PUBLICATION",
    ) is False
    latest = store.latest_operator_cycle_trigger()
    assert latest["state"] == "CONSUMED"
    assert latest["consumed_window_id"] == "operator-requested-operator-trigger-test0003"


def test_operator_trigger_executes_canonical_cycle_exactly_once(tmp_path):
    supervisor, calls = _supervisor(tmp_path)
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0004",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
        requested_at_utc="2026-08-10T09:59:00+00:00",
    )
    report = supervisor.tick(FIXED_NOW)
    assert report["operator_trigger"]["state"] == "CONSUMED"
    assert report["operator_trigger"]["executed"] is True
    assert report["newsroom_cycle_invocations"] == 1
    assert len(calls) == 1
    assert calls[0]["run_id"].startswith("operator-requested-operator-trigger-test0004")
    repeat = supervisor.tick(FIXED_NOW)
    assert "operator_trigger" not in repeat
    assert len(calls) == 1


def test_duplicate_operator_request_is_idempotent(tmp_path):
    store = _store(tmp_path)
    store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0005",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
    )
    supervisor, calls = _supervisor(tmp_path)
    supervisor.tick(FIXED_NOW)
    supervisor.tick(FIXED_NOW)
    supervisor.tick(FIXED_NOW)
    assert len(calls) == 1
    assert store.latest_operator_cycle_trigger()["state"] == "CONSUMED"


def test_active_cycle_defers_operator_trigger(tmp_path):
    supervisor, calls = _supervisor(tmp_path)
    store = supervisor._store
    store.create_work_item(
        story_id="editorial-window-running", title="active", target_surface="daily_app_editorial_window",
        work_item_id="editorial-window-running",
    )
    claim = store.claim_work_item(
        lease_key="editorial-window-running", work_item_id="editorial-window-running",
        owner_ref=supervisor._owner_ref, ttl_seconds=3600,
    )
    store.transition_state(
        work_item_id="editorial-window-running",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="ContentOpsDailyAppSupervisor",
        actor_ref=supervisor._owner_ref,
        reason_code="EDITORIAL_WINDOW_DUE",
        explanation="active",
        lease_key=claim["lease_key"],
        fencing_token=int(claim["fencing_token"]),
        input_artifact_ids=[], output_artifact_ids=[],
        correlation_id="corr_active",
    )
    store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0006",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
    )
    report = supervisor.tick(FIXED_NOW)
    assert report["operator_trigger"]["state"] == "DEFERRED_CYCLE_ALREADY_ACTIVE"
    assert report["operator_trigger"]["executed"] is False
    assert len(calls) == 0
    assert store.fetch_pending_operator_trigger() is not None
    store.release_lease(claim["lease_id"], supervisor._owner_ref, int(claim["fencing_token"]))


def test_operator_trigger_suppresses_same_tick_scheduled_window(tmp_path):
    in_window_now = datetime(2026, 8, 10, 13, 30, 0, tzinfo=timezone.utc)
    supervisor, calls = _supervisor(tmp_path, clock=lambda: in_window_now)
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0007",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
        requested_at_utc="2026-08-10T13:29:00+00:00",
    )
    report = supervisor.tick(in_window_now)
    assert report["newsroom_cycle_invocations"] == 1
    assert len(calls) == 1
    assert any("one_window_per_tick" in skipped for skipped in report["windows_skipped"])


def test_restart_preserves_pending_trigger_for_exactly_one_consumption(tmp_path):
    supervisor, calls = _supervisor(tmp_path)
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0008",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
        requested_at_utc="2026-08-10T09:59:00+00:00",
    )
    restarted, calls2 = _supervisor(tmp_path)
    report = restarted.tick(FIXED_NOW)
    assert report["operator_trigger"]["state"] == "CONSUMED"
    assert report["operator_trigger"]["executed"] is True
    assert len(calls2) == 1
    supervisor.tick(FIXED_NOW)
    assert len(calls) == 0


def test_shadow_only_operator_cycle_performs_zero_public_writes(tmp_path):
    supervisor, calls = _supervisor(tmp_path, mode="SHADOW_ONLY")
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0009",
        requested_mode="SHADOW_ONLY",
        control_state_version=1,
        requested_at_utc="2026-08-10T09:59:00+00:00",
    )
    report = supervisor.tick(FIXED_NOW)
    assert report["operator_trigger"]["executed"] is True
    assert report["public_write_performed"] is False
    assert calls[0]["publication_enabled"] is False


def test_autonomous_default_operator_cycle_keeps_canonical_gate_flag_only(tmp_path):
    supervisor, calls = _supervisor(tmp_path, mode="AUTONOMOUS_DEFAULT")
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0010",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
        requested_at_utc="2026-08-10T09:59:00+00:00",
    )
    supervisor.tick(FIXED_NOW)
    assert calls[0]["publication_enabled"] is True
    assert calls[0]["cutoff_utc"] == "2026-08-10T04:30:00Z"
    allowed = {
        "run_id", "output_dir", "cutoff_utc", "publication_enabled", "sidecar_glob",
        "capital_chronicle_root", "published_corpus", "cc_catalog", "operating_mode",
    }
    assert set(calls[0]) <= allowed
    assert "operator_run_now_override" not in calls[0]


def test_kill_switch_defers_operator_trigger_and_never_clears_mode(tmp_path):
    supervisor, calls = _supervisor(tmp_path, mode="KILL_SWITCH")
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0011",
        requested_mode="KILL_SWITCH",
        control_state_version=2,
        requested_at_utc="2026-08-10T09:59:00+00:00",
    )
    report = supervisor.tick(FIXED_NOW)
    assert report["kill_switch_active"] is True
    assert "operator_trigger" not in report
    assert len(calls) == 0
    assert supervisor._store.fetch_pending_operator_trigger() is not None
    assert supervisor._store.get_operating_control()["operating_mode"] == "KILL_SWITCH"


@pytest.fixture()
def server_env(tmp_path):
    store_path = tmp_path / "server_store.sqlite3"
    store = ContentOpsDurableStore(store_path)
    assert store.get_current_schema_version() == 9
    httpd = HTTPServer(("127.0.0.1", 0), make_handler(store_path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield base, store_path, store
    httpd.shutdown()
    httpd.server_close()


def _post(base: str, route: str, *, payload=None, origin="http://127.0.0.1:5173", content_type="application/json", method="POST"):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base}{route}", data=body, method=method,
        headers={"Content-Type": content_type, "Origin": origin, "Content-Length": str(len(body))},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"raw": raw}


def test_historical_run_pipeline_remains_quarantined(server_env, monkeypatch):
    base, _, _ = server_env
    status, payload = _post(base, "/api/run-pipeline", payload={})
    assert status == 423
    assert payload["live_launch_authorized"] is False
    assert payload["thread_created"] is False
    assert payload["subprocess_created"] is False


def test_run_now_requires_allowed_origin(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    control = store.get_operating_control()
    status, payload = _post(
        base, "/api/daily-app/control/run-now",
        payload={"trigger": "OPERATOR_REQUESTED", "expected_state_version": int(control["state_version"])},
        origin="http://evil.example",
    )
    assert status == 403
    assert payload == {"error": "ORIGIN_NOT_ALLOWED"}
    assert store.fetch_pending_operator_trigger() is None


def test_run_now_rejects_malformed_and_extra_fields(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    control = store.get_operating_control()
    version = int(control["state_version"])
    for payload in (
        {},
        {"trigger": "OPERATOR_REQUESTED"},
        {"expected_state_version": version},
        {"trigger": "SOMETHING_ELSE", "expected_state_version": version},
        {"trigger": "OPERATOR_REQUESTED", "expected_state_version": version, "shell": "calc.exe"},
        {"trigger": "OPERATOR_REQUESTED", "expected_state_version": "1"},
        {"trigger": "OPERATOR_REQUESTED", "expected_state_version": True},
        {"trigger": "OPERATOR_REQUESTED", "expected_state_version": 0},
    ):
        status, body = _post(base, "/api/daily-app/control/run-now", payload=payload)
        assert status == 400, payload
        assert "error" in body
    assert store.fetch_pending_operator_trigger() is None


def test_run_now_accepts_durable_trigger_and_is_idempotent(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    control = store.get_operating_control()
    payload = {"trigger": "OPERATOR_REQUESTED", "expected_state_version": int(control["state_version"])}
    status, body = _post(base, "/api/daily-app/control/run-now", payload=payload)
    assert status == 200
    assert body["status"] == "OPERATOR_TRIGGER_ACCEPTED"
    assert body["publication_claimed"] is False
    trigger_id = body["trigger"]["trigger_id"]
    repeat_status, repeat_body = _post(base, "/api/daily-app/control/run-now", payload=payload)
    assert repeat_status == 200
    assert repeat_body["status"] == "OPERATOR_TRIGGER_ALREADY_PENDING"
    assert repeat_body["trigger"]["trigger_id"] == trigger_id
    pending = store.fetch_pending_operator_trigger()
    assert pending is not None and pending["trigger_id"] == trigger_id


def test_run_now_state_version_conflict_fails_closed(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    status, body = _post(
        base, "/api/daily-app/control/run-now",
        payload={"trigger": "OPERATOR_REQUESTED", "expected_state_version": 999},
    )
    assert status == 409
    assert body == {"error": "CONTROL_STATE_CONFLICT"}
    assert store.fetch_pending_operator_trigger() is None


def test_run_now_active_cycle_prevents_parallel_trigger(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    store.create_work_item(
        story_id="editorial-window-active", title="active", target_surface="daily_app_editorial_window",
        work_item_id="editorial-window-active",
    )
    claim = store.claim_work_item(
        lease_key="editorial-window-active", work_item_id="editorial-window-active",
        owner_ref="test_owner", ttl_seconds=3600,
    )
    store.transition_state(
        work_item_id="editorial-window-active",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="ContentOpsDailyAppSupervisor",
        actor_ref="test_owner",
        reason_code="EDITORIAL_WINDOW_DUE",
        explanation="active",
        lease_key=claim["lease_key"],
        fencing_token=int(claim["fencing_token"]),
        input_artifact_ids=[], output_artifact_ids=[],
        correlation_id="corr_active_http",
    )
    control = store.get_operating_control()
    status, body = _post(
        base, "/api/daily-app/control/run-now",
        payload={"trigger": "OPERATOR_REQUESTED", "expected_state_version": int(control["state_version"])},
    )
    assert status == 409
    assert body["status"] == "CYCLE_ALREADY_ACTIVE"
    assert body["publication_claimed"] is False
    assert store.fetch_pending_operator_trigger() is None


def test_run_now_kill_switch_blocks_and_never_clears(server_env, monkeypatch):
    monkeypatch.setattr("live_contentops.ingestion_bootstrap_v1.ensure_ingestion_runtime", lambda **kwargs: {"status": "ALREADY_READY", "state": "READY"})
    base, _, store = server_env
    store.update_operating_control(
        expected_state_version=int(store.get_operating_control()["state_version"]),
        operating_mode="KILL_SWITCH",
        control_source="LOCAL_DAILY_APP_UI",
    )
    control = store.get_operating_control()
    status, body = _post(
        base, "/api/daily-app/control/run-now",
        payload={"trigger": "OPERATOR_REQUESTED", "expected_state_version": int(control["state_version"])},
    )
    assert status == 409
    assert body["status"] == "KILL_SWITCH_ACTIVE_PUBLIC_WRITES_BLOCKED"
    assert store.get_operating_control()["operating_mode"] == "KILL_SWITCH"
    assert store.fetch_pending_operator_trigger() is None


def test_run_now_ingestion_unavailable_stays_passive_and_records_trigger(server_env, monkeypatch):
    monkeypatch.setattr(
        "live_contentops.ingestion_bootstrap_v1.passive_canonical_ingestion_readiness",
        lambda **kwargs: {
            "chrome_9222_ingestion": "UNAVAILABLE", "detail": "CDP_9222_NOT_READY",
            "launched": False, "browser_navigation_performed": False,
        },
    )
    base, _, store = server_env
    control = store.get_operating_control()
    status, body = _post(
        base, "/api/daily-app/control/run-now",
        payload={"trigger": "OPERATOR_REQUESTED", "expected_state_version": int(control["state_version"])},
    )
    assert status == 200
    assert body["status"] == "OPERATOR_TRIGGER_ACCEPTED"
    assert body["ingestion_browser_interaction_performed"] is False
    assert store.fetch_pending_operator_trigger() is not None


def test_snapshot_exposes_operator_trigger_and_run_now_controls(tmp_path):
    from live_contentops.daily_app_ui_read_model_v1 import build_daily_app_snapshot

    store = ContentOpsDurableStore(tmp_path / "snap.sqlite3")
    store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-test0012",
        requested_mode="AUTONOMOUS_DEFAULT",
        control_state_version=1,
    )
    snapshot = build_daily_app_snapshot(tmp_path / "snap.sqlite3")
    assert snapshot["runtime"]["operator_cycle_trigger"]["trigger_id"] == "operator-trigger-test0012"
    assert snapshot["runtime"]["operator_cycle_trigger"]["grants_publication_authority"] is False
    assert snapshot["controls"]["run_now_endpoint"] == "/api/daily-app/control/run-now"
    assert snapshot["controls"]["run_now_allowed"] is True
    assert "governed" in snapshot["controls"]["run_now_mode_consequence"].lower() or "cycle" in snapshot["controls"]["run_now_mode_consequence"].lower()


def test_trigger_kind_constant_is_operator_requested():
    assert TRIGGER_OPERATOR_REQUESTED == "OPERATOR_REQUESTED"
