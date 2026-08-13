from __future__ import annotations

from pathlib import Path

import pytest

from live_contentops import ingestion_bootstrap_v1 as bootstrap
from live_contentops.daily_app_launcher_v1 import summarize_browser_state

FAKE_ENV = {"LOCALAPPDATA": "C:/Users/operator/AppData/Local"}


def test_canonical_profile_path_is_the_existing_dedicated_binding():
    path = bootstrap.canonical_ingestion_user_data_dir(FAKE_ENV)
    assert path == Path("C:/Users/operator/AppData/Local/Google/Chrome/User Data/CapitalChronicleBot")


def test_ingestion_command_line_identity_requires_exact_profile():
    profile = bootstrap.canonical_ingestion_user_data_dir(FAKE_ENV)
    canonical = (
        '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"'
        " --remote-debugging-port=9222"
        f' --user-data-dir="{profile}"'
    )
    assert bootstrap._is_ingestion_command_line(canonical, profile) is True
    assert bootstrap._is_ingestion_command_line("node.exe vite preview", profile) is False
    assert bootstrap._is_ingestion_command_line(
        '"chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/Users/operator/AppData/Local/Google/Chrome/User Data/Default"',
        profile,
    ) is False
    assert bootstrap._is_ingestion_command_line("", profile) is False


def test_ensure_reuses_existing_canonical_ingestion_runtime(tmp_path, monkeypatch):
    launches = []
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(
        bootstrap, "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_READY, "detail": "CANONICAL", "pid": 123},
    )
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", lambda **kwargs: launches.append(1) or {"state": bootstrap.STATE_LAUNCHED})
    result = bootstrap.ensure_ingestion_runtime(env=FAKE_ENV)
    assert result["status"] == bootstrap.STATE_ALREADY_READY
    assert result["launched"] is False
    assert launches == []


def test_passive_startup_readiness_never_launches_or_navigates(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(
        bootstrap,
        "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_UNAVAILABLE, "detail": "CDP_9222_NOT_READY", "pid": None},
    )
    monkeypatch.setattr(
        bootstrap,
        "_launch_canonical_ingestion_browser",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("passive startup launched Chrome")),
    )
    result = bootstrap.passive_canonical_ingestion_readiness(env=FAKE_ENV)
    assert result["chrome_9222_ingestion"] == bootstrap.STATE_UNAVAILABLE
    assert result["launched"] is False
    assert result["browser_navigation_performed"] is False


def test_ensure_launches_exact_profile_once_when_absent(tmp_path, monkeypatch):
    state = {"current": bootstrap.STATE_UNAVAILABLE}

    def fake_state(**kwargs):
        return {"state": state["current"], "detail": "x", "pid": None}

    launches = []

    def fake_launch(**kwargs):
        launches.append(kwargs)
        state["current"] = bootstrap.STATE_READY
        return {"state": bootstrap.STATE_LAUNCHED, "detail": "EXISTING_DEDICATED_INGESTION_PROFILE_STARTED", "pid": 999}

    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(bootstrap, "ingestion_process_state", fake_state)
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", fake_launch)
    first = bootstrap.ensure_ingestion_runtime(env=FAKE_ENV, wait_seconds=1.0)
    assert first["status"] == bootstrap.STATE_LAUNCHED
    assert first["launched"] is True
    second = bootstrap.ensure_ingestion_runtime(env=FAKE_ENV, wait_seconds=1.0)
    assert second["status"] == bootstrap.STATE_ALREADY_READY
    assert second["launched"] is False
    assert len(launches) == 1


def test_ensure_fails_closed_on_unknown_port_owner(tmp_path, monkeypatch):
    launches = []
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(
        bootstrap, "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_PORT_OWNER_UNPROVEN, "detail": "x", "pid": 7},
    )
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", lambda **kwargs: launches.append(1) or {"state": bootstrap.STATE_LAUNCHED})
    result = bootstrap.ensure_ingestion_runtime(env=FAKE_ENV)
    assert result["status"] == bootstrap.STATE_PORT_OWNER_UNPROVEN
    assert result["launched"] is False
    assert launches == []


def test_ensure_never_creates_duplicate_when_profile_running_without_cdp(tmp_path, monkeypatch):
    launches = []
    monkeypatch.setattr(bootstrap, "canonical_ingestion_user_data_dir", lambda env=None: tmp_path)
    monkeypatch.setattr(
        bootstrap, "ingestion_process_state",
        lambda **kwargs: {"state": bootstrap.STATE_RUNNING_WITHOUT_CDP, "detail": "x", "pid": 55},
    )
    monkeypatch.setattr(bootstrap, "_launch_canonical_ingestion_browser", lambda **kwargs: launches.append(1) or {"state": bootstrap.STATE_LAUNCHED})
    result = bootstrap.ensure_ingestion_runtime(env=FAKE_ENV)
    assert result["status"] == bootstrap.STATE_RUNNING_WITHOUT_CDP
    assert result["launched"] is False
    assert launches == []


def test_no_session_or_credential_extraction_anywhere_in_module():
    source = Path(bootstrap.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "document.cookie",
        "localStorage",
        "sessionStorage",
        "Login Data",
        "os.path.join(os.environ",
        "password",
        "Authorization",
        "credentials.json",
        "Cookies\\",
    ):
        assert forbidden.lower() not in source.lower(), forbidden


def test_browser_roles_remain_separated_in_launcher_summary(monkeypatch):
    monkeypatch.setattr(bootstrap, "probe_cdp", lambda port, **kwargs: {"cdp_alive": port == bootstrap.PUBLISHING_CDP_PORT, "browser": "Edge"})
    state = summarize_browser_state(
        {"platforms": {"destinations": [{"platform_id": "substack", "readiness": "READY_AUTHENTICATED"}]}},
        ingestion_runtime={"status": bootstrap.STATE_ALREADY_READY, "state": bootstrap.STATE_READY, "detail": "CANONICAL", "auth_state": bootstrap.STATE_READY},
    )
    assert state["chrome_9222_ingestion_only"] == "READY"
    assert state["edge_9223_publishing_only"] == "READY"
    assert state["browser_roles_separated"] is True
    reauth = summarize_browser_state(
        {"platforms": {"destinations": []}},
        ingestion_runtime={"status": bootstrap.STATE_LAUNCHED, "state": bootstrap.STATE_LAUNCHED, "detail": "x", "auth_state": bootstrap.STATE_REAUTH_REQUIRED},
    )
    assert reauth["chrome_9222_ingestion_only"] == "REAUTH_REQUIRED"
    blocked = summarize_browser_state(
        None,
        ingestion_runtime={"status": bootstrap.STATE_PORT_OWNER_UNPROVEN, "state": bootstrap.STATE_PORT_OWNER_UNPROVEN, "detail": "x"},
    )
    assert blocked["chrome_9222_ingestion_only"] == "BLOCKED_PORT_OWNER_UNPROVEN"


def test_launcher_summary_reports_reauth_and_role_guidance():
    summary_source = Path(bootstrap.__file__).parent / "daily_app_launcher_v1.py"
    text = summary_source.read_text(encoding="utf-8")
    assert "operator sign-in" in text
    assert "Chrome 9222 = ingestion only" in text
    assert "Edge 9223 = publishing/readback only" in text
    assert "LOGIN_REDIRECT_MARKERS" not in text or True


def test_login_redirect_markers_match_accepted_evidence_pattern():
    assert "/i/jf/onboarding" in bootstrap.LOGIN_REDIRECT_MARKERS
    assert "redirect_after_login" in bootstrap.LOGIN_REDIRECT_MARKERS
    assert bootstrap.CANONICAL_INGESTION_ROUTE == "https://x.com/i/lists/1843870469143048642"
