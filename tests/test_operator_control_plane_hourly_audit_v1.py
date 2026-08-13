from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.hourly_runtime_audit_v1 import (
    _classify,
    _recent_stderr_signal,
    write_audit_artifacts,
)
from live_contentops import server as loopback_server
from live_contentops.operator_control_plane_v1 import (
    MAX_LOG_LINES,
    OperatorControlError,
    prepare_safe_shutdown,
    read_allowlisted_log,
    redact_log_text,
)


def test_allowlisted_log_tail_is_bounded_redacted_and_has_no_path_input(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    logs = tmp_path / "one_click_launcher"
    logs.mkdir()
    secret = "sk-live-sentinel-abcdefghijklmnopqrstuvwxyz"
    (logs / "daily_app.supervisor.stderr.log").write_text(
        "old\n" + "\n".join(f"line-{index}" for index in range(450)) + f"\nAuthorization: Bearer {secret}\n",
        encoding="utf-8",
    )
    result = read_allowlisted_log(store.db_path, stream="supervisor_stderr", lines=12)
    assert result["line_count"] == 12
    assert result["truncated"] is True
    assert secret not in result["content"]
    assert "[REDACTED]" in result["content"]
    with pytest.raises(OperatorControlError, match="NOT_ALLOWLISTED"):
        read_allowlisted_log(store.db_path, stream="../../private", lines=12)
    with pytest.raises(OperatorControlError, match="LINE_LIMIT"):
        read_allowlisted_log(store.db_path, stream="supervisor_stderr", lines=MAX_LOG_LINES + 1)


def test_redaction_covers_assignment_and_bearer_forms():
    value = "token=abc123456789-secret Authorization: Bearer abcdefghijklmnop sk-test-abcdefghijklmnop"
    clean = redact_log_text(value)
    assert "abc123456789" not in clean
    assert "abcdefghijklmnop" not in clean
    assert clean.count("[REDACTED]") >= 3


def test_shutdown_preflight_establishes_kill_switch_by_cas_without_stopping_processes(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    before = store.get_operating_control()
    assert before["operating_mode"] == "AUTONOMOUS_DEFAULT"
    result = prepare_safe_shutdown(store.db_path, expected_state_version=before["state_version"])
    after = store.get_operating_control()
    assert result["status"] == "SAFE_TO_STOP_PROVEN_BACKGROUND_PROCESSES"
    assert after["operating_mode"] == "KILL_SWITCH"
    assert after["state_version"] == before["state_version"] + 1
    # Idempotent only when the caller proves the current state version.
    again = prepare_safe_shutdown(store.db_path, expected_state_version=after["state_version"])
    assert again["state_version"] == after["state_version"]


def test_shutdown_preflight_fails_closed_on_unknown_write(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    store.create_work_item(story_id="story", title="Story", target_surface="substack", work_item_id="work")
    store.register_outbox_message(message_id="message", work_item_id="work", destination="substack", payload="{}", status="READY")
    store.register_platform_dispatch(dispatch_id="dispatch", message_id="message", platform="substack", status="UNKNOWN_WRITE")
    before = store.get_operating_control()
    with pytest.raises(OperatorControlError, match="UNKNOWN_WRITE_PRESENT"):
        prepare_safe_shutdown(store.db_path, expected_state_version=before["state_version"])
    assert store.get_operating_control()["operating_mode"] == "AUTONOMOUS_DEFAULT"


def _audit_report(*, reauth=False, reauth_platform="linkedin", duplicate=False, ambiguity=False):
    return {
        "runtime": {
            "supervisor_count": 2 if duplicate else 1,
            "api_health": "LOOPBACK_API_HEALTHY",
            "source_sha_match": True,
            "controller_health": "HEALTHY",
            "heartbeat_age_seconds": 5,
            "headline_lane_state": "RUNNING",
            "headline_ingest_age_seconds": 5,
        },
        "safety": {
            "unknown_write_count": 1 if ambiguity else 0,
            "pending_readback_count": 0,
            "pending_lifecycle_recovery_count": 0,
        },
        "destinations": [{
            "platform_id": reauth_platform,
            "readiness": "REAUTH_REQUIRED" if reauth else "READY_AUTHENTICATED",
        }],
        "browsers": {"chrome_9222": {"state": "READY"}, "edge_9223": {"state": "READY"}},
        "stderr_signal": {"error_lines": 0, "warning_lines": 0},
    }


def test_hourly_classification_is_deterministic_and_fail_visible():
    assert _classify(_audit_report())[0] == "PASS"
    assert _classify(_audit_report(reauth=True))[0] == "DEGRADED"
    assert _classify(_audit_report(reauth=True, reauth_platform="substack"))[0] == "ACTION_REQUIRED"
    assert _classify(_audit_report(duplicate=True)) == ("ACTION_REQUIRED", ["DUPLICATE_CANONICAL_SUPERVISOR"])
    assert _classify(_audit_report(ambiguity=True)) == ("ACTION_REQUIRED", ["WRITE_OR_READBACK_AMBIGUITY_PRESENT"])


def test_kill_switch_paused_ingestion_and_linkedin_exclusion_are_degraded_not_blocked():
    report = _audit_report(reauth=True)
    report["runtime"].update({
        "operating_mode": "KILL_SWITCH",
        "headline_lane_state": "PAUSED_KILL_SWITCH",
        "headline_ingest_age_seconds": 10_000,
    })
    classification, reasons = _classify(report)
    assert classification == "DEGRADED"
    assert "HEADLINE_INGESTION_PAUSED_BY_KILL_SWITCH" in reasons


def test_known_node_dep0169_warning_is_informational_not_warning(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    logs = tmp_path / "one_click_launcher"
    logs.mkdir()
    (logs / "daily_app.supervisor.stderr.log").write_text(
        "(node:42) [DEP0169] DeprecationWarning: `url.parse()` behavior is not standardized\n"
        "(Use `node --trace-deprecation ...` to show where the warning was created)\n",
        encoding="utf-8",
    )
    signal = _recent_stderr_signal(store.db_path)
    assert signal["error_lines"] == 0
    assert signal["warning_lines"] == 0
    assert signal["informational_noise_lines"] == 2


def test_real_exception_and_unknown_warning_remain_actionable_or_degraded(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    logs = tmp_path / "one_click_launcher"
    logs.mkdir()
    stderr = logs / "daily_app.supervisor.stderr.log"
    stderr.write_text(
        "RuntimeError: controlled fixture failure\n"
        "Warning: destination clock drift requires review\n",
        encoding="utf-8",
    )
    signal = _recent_stderr_signal(store.db_path)
    assert signal["error_lines"] == 1
    assert signal["warning_lines"] == 1
    assert signal["informational_noise_lines"] == 0


def test_hourly_artifacts_are_compact_latest_plus_bounded_jsonl(tmp_path):
    runtime_root = tmp_path / "runtime"
    for hour in range(4):
        report = {
            "schema_version": "contentops.hourly_runtime_audit.v1",
            "generated_at_utc": datetime(2026, 8, 13, hour, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "classification": "PASS",
        }
        paths = write_audit_artifacts(report, runtime_root=runtime_root)
    latest = json.loads((runtime_root / "hourly_audit" / "latest.json").read_text(encoding="utf-8"))
    history = (runtime_root / "hourly_audit" / "audit_history.jsonl").read_text(encoding="utf-8").splitlines()
    assert paths["latest"].endswith("latest.json")
    assert latest["generated_at_utc"].endswith("03:00:00Z")
    # Historical fixture timestamps older than retention are pruned; current writes stay bounded.
    assert len(history) <= 4


def test_loopback_shutdown_requires_origin_exact_payload_and_reuses_fallback(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    spawned = []
    monkeypatch.setattr(loopback_server, "spawn_shutdown_fallback", lambda **kwargs: spawned.append(kwargs) or 4321)
    httpd = HTTPServer(("127.0.0.1", 0), loopback_server.make_handler(store.db_path, repo_root=tmp_path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{httpd.server_port}"
    try:
        payload = json.dumps({"action": "SHUTDOWN_ALL_BACKGROUND", "expected_state_version": 1}).encode()
        denied = Request(root + "/api/daily-app/control/shutdown-all-background", data=payload, method="POST", headers={"Content-Type": "application/json"})
        with pytest.raises(HTTPError) as exc:
            urlopen(denied, timeout=5)
        assert exc.value.code == 403
        accepted = Request(root + "/api/daily-app/control/shutdown-all-background", data=payload, method="POST", headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:4173"})
        with urlopen(accepted, timeout=5) as response:
            result = json.loads(response.read())
        assert response.status == 202
        assert result["status"] == "SAFE_SHUTDOWN_STARTED"
        assert len(spawned) == 1
        assert store.get_operating_control()["operating_mode"] == "KILL_SWITCH"
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join(timeout=5)


def test_loopback_log_api_rejects_path_like_stream(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "daily.sqlite3")
    httpd = HTTPServer(("127.0.0.1", 0), loopback_server.make_handler(store.db_path, repo_root=tmp_path))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
    try:
        with pytest.raises(HTTPError) as exc:
            urlopen(f"http://127.0.0.1:{httpd.server_port}/api/daily-app/background-logs?stream=../../private&lines=20", timeout=5)
        assert exc.value.code == 400
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join(timeout=5)
