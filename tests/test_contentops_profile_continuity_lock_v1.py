from __future__ import annotations

from pathlib import Path

import pytest

from live_contentops import ingestion_bootstrap_v1 as bootstrap
from live_contentops.daily_app_ui_read_model_v1 import request_operator_cycle
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.daily_app_launcher_v1 import summarize_browser_state

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_canonical_ingestion_binding_is_single_source_and_locked():
    binding = bootstrap.CANONICAL_INGESTION_BINDING
    assert binding["browser_family"] == "CHROME"
    assert binding["profile_id"] == "CapitalChronicleBot"
    assert binding["cdp_port"] == 9222
    assert binding["role"] == "INGESTION_ONLY"
    assert binding["user_data_dir"] == "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\CapitalChronicleBot"
    assert binding["canonical_route"] == "https://x.com/i/lists/1843870469143048642"
    assert binding["profile_binding_locked"] is True
    assert binding["fallback_profile_available"] is False
    assert bootstrap.INGESTION_CDP_PORT == 9222
    assert bootstrap.CANONICAL_INGESTION_ROUTE == "https://x.com/i/lists/1843870469143048642"


def test_missing_profile_directory_fails_closed_and_is_never_created(tmp_path, monkeypatch):
    fake_local = tmp_path / "NoChromeHere"
    fake_local.mkdir()
    env = {"LOCALAPPDATA": str(fake_local)}
    created: list = []

    def _explode_mkdir(self, *args, **kwargs):
        created.append(str(self))
        raise AssertionError("profile directory creation attempted")

    monkeypatch.setattr(Path, "mkdir", _explode_mkdir)
    result = bootstrap.ensure_ingestion_runtime(env=env)
    assert result["status"] == bootstrap.STATE_PROFILE_BINDING_MISSING
    assert result["launched"] is False
    assert created == []
    assert not (fake_local / "Google").exists()
    launch = bootstrap._launch_canonical_ingestion_browser(env=env)
    assert launch["state"] == bootstrap.STATE_PROFILE_BINDING_MISSING


def test_no_fallback_profile_or_substitution_paths_in_canonical_code():
    sources = [
        REPO_ROOT / "live_contentops" / "ingestion_bootstrap_v1.py",
        REPO_ROOT / "live_contentops" / "daily_app_launcher_v1.py",
        REPO_ROOT / "live_contentops" / "server.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    lowered = text.lower()
    for forbidden in (
        "--profile-directory",
        "--guest",
        "--incognito",
        "--temp-profile",
        "--ephemeral-profile",
    ):
        assert forbidden not in lowered, forbidden
    for line in text.splitlines():
        if "--user-data-dir" in line:
            assert ("CapitalChronicleBot" in line) or ("{profile_dir}" in line), (
                f"non-canonical user-data-dir launch: {line}"
            )
    ingestion_source = (REPO_ROOT / "live_contentops" / "ingestion_bootstrap_v1.py").read_text(encoding="utf-8")
    assert "msedge" not in ingestion_source.lower(), "Edge binary must never be used for ingestion"
    assert "find_edge_binary" not in ingestion_source, "Edge launcher must never be used for ingestion"
    profile_dirs = [line for line in text.splitlines() if "profile_dir =" in line]
    assert profile_dirs, "profile_dir binding missing"
    for line in profile_dirs:
        assert "canonical_ingestion_user_data_dir" in line, f"profile_dir not bound to canonical dir: {line}"


def test_launcher_runtime_contains_no_profile_destruction_or_clone_paths():
    sources = [
        REPO_ROOT / "live_contentops" / "ingestion_bootstrap_v1.py",
        REPO_ROOT / "live_contentops" / "daily_app_launcher_v1.py",
        REPO_ROOT / "scripts" / "Start-ContentOpsDailyApp.ps1",
        REPO_ROOT / "Start_ContentOps_Daily_App.cmd",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    lowered = text.lower()
    for forbidden in (
        "rmtree",
        "copytree",
        "remove-item",
        "taskkill /f /im chrome",
        "taskkill /f /im \"chrome",
        "rd /s",
        "rmdir /s",
        "del /f",
        "--restore-last-session",
        "os.remove",
        "shutil.rmtree",
        "shutil.copytree",
        "shutil.move",
    ):
        assert forbidden not in lowered, forbidden


def test_exact_9222_owner_is_reused_without_launch(monkeypatch):
    launches = []
    monkeypatch.setattr(
        bootstrap, "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_READY, "detail": "CANONICAL", "pid": 4242},
    )
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", lambda **kwargs: launches.append(1) or {"state": bootstrap.STATE_LAUNCHED})
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: Path("C:/exists"))
    monkeypatch.setattr(Path, "exists", lambda self: True)
    result = bootstrap.ensure_ingestion_runtime()
    assert result["status"] == bootstrap.STATE_ALREADY_READY
    assert result["launched"] is False
    assert launches == []


def test_wrong_9222_owner_is_blocked_without_launch_or_kill(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(
        bootstrap, "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_PORT_OWNER_UNPROVEN, "detail": "x", "pid": 7},
    )
    launches = []
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", lambda **kwargs: launches.append(1) or {"state": bootstrap.STATE_LAUNCHED})
    result = bootstrap.ensure_ingestion_runtime()
    assert result["status"] == bootstrap.STATE_PORT_OWNER_UNPROVEN
    assert result["launched"] is False
    assert launches == []


def test_authenticated_visible_x_list_is_ready_and_login_redirect_is_reauth(monkeypatch):
    monkeypatch.setattr(bootstrap, "probe_cdp", lambda port, **kwargs: {"cdp_alive": True, "browser": "Chrome"})
    monkeypatch.setattr(
        bootstrap, "cdp_target_urls",
        lambda port, **kwargs: ["https://x.com/i/lists/1843870469143048642"],
    )
    ready = bootstrap.probe_ingestion_session(timeout_seconds=2)
    assert ready["auth_state"] == bootstrap.STATE_READY
    monkeypatch.setattr(
        bootstrap, "cdp_target_urls",
        lambda port, **kwargs: [
            "https://x.com/i/jf/onboarding/web?redirect_after_login=%2Fi%2Flists%2F1843870469143048642&mode=login"
        ],
    )
    reauth = bootstrap.probe_ingestion_session(timeout_seconds=2)
    assert reauth["auth_state"] == bootstrap.STATE_REAUTH_REQUIRED


def _shadow_store(tmp_path: Path) -> Path:
    store_path = tmp_path / "runnow.sqlite3"
    store = ContentOpsDurableStore(store_path)
    assert store.get_current_schema_version() == 9
    return store_path


def test_run_now_is_passive_and_does_not_probe_reauth_or_bypass_cadence(tmp_path, monkeypatch):
    store_path = _shadow_store(tmp_path)
    monkeypatch.setattr(
        "live_contentops.ingestion_bootstrap_v1.passive_canonical_ingestion_readiness",
        lambda **kwargs: {
            "chrome_profile_binding": bootstrap.BINDING_LOCKED,
            "chrome_9222_ingestion": bootstrap.STATE_REAUTH_REQUIRED,
            "x_ingestion_session": bootstrap.STATE_REAUTH_REQUIRED,
            "session_detail": "LOGIN_REDIRECT_OBSERVED",
        },
    )
    control = ContentOpsDurableStore(store_path, auto_migrate=False).get_operating_control()
    result = request_operator_cycle(store_path, expected_state_version=int(control["state_version"]))
    assert result["status"] == "OPERATOR_TRIGGER_ACCEPTED"
    assert result["governed_cycle_requested"] is True
    assert result["publication_claimed"] is False
    assert result["ingestion_browser_interaction_performed"] is False
    assert ContentOpsDurableStore(store_path, auto_migrate=False).fetch_pending_operator_trigger() is not None


def test_run_now_accepts_durable_cycle_without_active_ingestion_session_probe(tmp_path, monkeypatch):
    store_path = _shadow_store(tmp_path)
    monkeypatch.setattr(
        "live_contentops.ingestion_bootstrap_v1.passive_canonical_ingestion_readiness",
        lambda **kwargs: {
            "chrome_profile_binding": bootstrap.BINDING_LOCKED,
            "chrome_9222_ingestion": bootstrap.STATE_AUTH_UNVERIFIED,
            "x_ingestion_session": bootstrap.STATE_AUTH_UNVERIFIED,
            "session_detail": "SESSION_PROBE_INCONCLUSIVE_WITHIN_BOUNDED_WAIT",
        },
    )
    control = ContentOpsDurableStore(store_path, auto_migrate=False).get_operating_control()
    result = request_operator_cycle(store_path, expected_state_version=int(control["state_version"]))
    assert result["status"] == "OPERATOR_TRIGGER_ACCEPTED"
    assert result["ingestion_browser_interaction_performed"] is False
    assert ContentOpsDurableStore(store_path, auto_migrate=False).fetch_pending_operator_trigger() is not None


def test_run_now_accepts_ready_ingestion(tmp_path, monkeypatch):
    store_path = _shadow_store(tmp_path)
    monkeypatch.setattr(
        "live_contentops.ingestion_bootstrap_v1.passive_canonical_ingestion_readiness",
        lambda **kwargs: {
            "chrome_profile_binding": bootstrap.BINDING_LOCKED,
            "chrome_9222_ingestion": bootstrap.STATE_READY,
            "x_ingestion_session": bootstrap.STATE_READY,
            "session_detail": "CANONICAL_LIST_ROUTE_ACTIVE_NO_LOGIN_REDIRECT",
        },
    )
    control = ContentOpsDurableStore(store_path, auto_migrate=False).get_operating_control()
    result = request_operator_cycle(store_path, expected_state_version=int(control["state_version"]))
    assert result["status"] == "OPERATOR_TRIGGER_ACCEPTED"
    pending = ContentOpsDurableStore(store_path, auto_migrate=False).fetch_pending_operator_trigger()
    assert pending is not None and pending["trigger_kind"] == "OPERATOR_REQUESTED"


def test_historical_run_pipeline_remains_quarantined():
    from live_contentops.live_entrypoint_registry_v1 import HTTP_LAUNCH_QUARANTINED

    assert HTTP_LAUNCH_QUARANTINED == "BLOCKED_HTTP_LIVE_LAUNCH_QUARANTINED"
    server_source = (REPO_ROOT / "live_contentops" / "server.py").read_text(encoding="utf-8")
    assert "423" in server_source


def test_launcher_summary_reports_binding_lock_and_session_state():
    ready = summarize_browser_state(
        None,
        ingestion_runtime={
            "chrome_profile_binding": bootstrap.BINDING_LOCKED,
            "chrome_9222_ingestion": bootstrap.STATE_READY,
            "x_ingestion_session": bootstrap.STATE_READY,
            "session_detail": "CANONICAL_LIST_ROUTE_ACTIVE_NO_LOGIN_REDIRECT",
        },
    )
    assert ready["chrome_profile_binding"] == "LOCKED"
    assert ready["chrome_9222_ingestion_only"] == "READY"
    assert ready["x_ingestion_session"] == "READY"
    reauth = summarize_browser_state(
        None,
        ingestion_runtime={
            "chrome_profile_binding": bootstrap.BINDING_LOCKED,
            "chrome_9222_ingestion": bootstrap.STATE_REAUTH_REQUIRED,
            "x_ingestion_session": bootstrap.STATE_REAUTH_REQUIRED,
            "session_detail": "LOGIN_REDIRECT_OBSERVED",
        },
    )
    assert reauth["chrome_profile_binding"] == "LOCKED"
    assert reauth["chrome_9222_ingestion_only"] == "REAUTH_REQUIRED"
    from live_contentops.daily_app_launcher_v1 import render_summary, LaunchDecision

    text = render_summary(
        decision=LaunchDecision(outcome="ALREADY_RUNNING", reason="ok", canonical_supervisor_count=1),
        snapshot=None,
        browser_state=reauth,
        ui_state={"status": "READY", "url": "http://127.0.0.1:4173/", "mechanism": "x", "pid": 1},
        store_path=Path("x.sqlite3"),
        store_exists=True,
        schema_version=9,
        inventory_report="NONE",
    )
    assert "Chrome Profile Binding: LOCKED" in text
    assert "X Ingestion Session: REAUTH_REQUIRED" in text
    assert "never creates/clones/resets/replaces/deletes" in text


def test_no_secret_or_session_material_in_readiness_output():
    source = Path(bootstrap.__file__).read_text(encoding="utf-8")
    for forbidden in ("document.cookie", "localStorage", "sessionStorage", "Login Data", "Authorization"):
        assert forbidden.lower() not in source.lower(), forbidden
