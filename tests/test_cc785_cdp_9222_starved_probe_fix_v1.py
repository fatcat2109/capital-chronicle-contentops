"""CC-785 starved CDP 9222 probe diagnostics & discovery-failure heal tests.

Strictly hermetic (tmp_path + fakes only): zero live Chrome/CDP/network/Neo calls, zero .stop edits,
zero public posts.
"""
from __future__ import annotations

import json
import subprocess
from urllib.parse import unquote, urlsplit

import pytest

from live_contentops import daily_app_launcher_v1 as launcher
from live_contentops import ingestion_bootstrap_v1 as bootstrap
from live_contentops import x_list_feed_v1 as feed
from test_x_list_feed_cc785 import FakeCDP, Harness, LIST_URL, NOW


class StarvedDiscoveryCDP(FakeCDP):
    """FakeCDP where /json/list discovery can time out while /json/new or browser WS still works."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discovery_error = None
        self.new_http_error = None

    def targets(self, **_):
        if self.discovery_error is not None:
            raise self.discovery_error
        return super().targets()

    def http_open(self, request, *, timeout):
        url = urlsplit(request.full_url)
        if url.path == "/json/new" and self.new_http_error is not None:
            self.requests.append((request.get_method(), url.path, unquote(url.query)))
            raise self.new_http_error
        return super().http_open(request, timeout=timeout)


def test_starved_cdp_9222_probe_with_native_canonical_listener_is_not_mislabelled_without_cdp(monkeypatch, tmp_path):
    """When Chrome 9222 is alive & listening on port 9222 but /json/version times out, report CDP_PROBE_STARVED."""
    env = {"LOCALAPPDATA": str(tmp_path / "LocalAppData")}
    profile_dir = bootstrap.canonical_ingestion_user_data_dir(env)
    profile_dir.mkdir(parents=True)

    popen_calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))
    monkeypatch.setattr(bootstrap, "probe_cdp", lambda port, **kw: {"cdp_alive": False, "browser": None})
    monkeypatch.setattr(bootstrap, "_native_listener_pid", lambda port: 4321)
    monkeypatch.setattr(
        bootstrap,
        "_native_process_identity",
        lambda pid: {
            "pid": pid,
            "start": 987654,
            "cmd": f'"chrome.exe" --remote-debugging-port=9222 --user-data-dir="{profile_dir}"',
        },
    )
    monkeypatch.setattr(bootstrap, "_powershell_json", lambda *a, **k: pytest.fail("native check should avoid PowerShell"))

    state = bootstrap.ingestion_process_state(env=env)
    assert state["state"] == bootstrap.STATE_CDP_PROBE_STARVED
    assert state["detail"] == "CANONICAL_CDP_9222_LISTENING_PROBE_TIMED_OUT"
    assert state["pid"] == 4321 and state["owner_check"] == "NATIVE"

    ensured = bootstrap.ensure_ingestion_runtime(env=env)
    assert ensured["status"] == bootstrap.STATE_CDP_PROBE_STARVED
    assert ensured["detail"] != "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222"
    assert ensured["launched"] is False and popen_calls == []

    # Launcher summary surfaces CDP_PROBE_STARVED distinctly from RUNNING_WITHOUT_CDP.
    monkeypatch.setattr(launcher, "probe_cdp", lambda port, **kw: {"cdp_alive": False, "browser": None})
    summary = launcher.summarize_browser_state(None, ingestion_runtime=ensured)
    assert summary["chrome_9222_ingestion_only"] == "CDP_PROBE_STARVED"


def test_starved_cdp_9222_probe_powershell_fallback_distinguishes_cdp_flag_from_no_cdp(monkeypatch, tmp_path):
    """PowerShell fallback distinguishes Chrome started WITH --remote-debugging-port=9222 from true non-CDP Chrome."""
    env = {"LOCALAPPDATA": str(tmp_path / "LocalAppData")}
    profile_dir = bootstrap.canonical_ingestion_user_data_dir(env)
    profile_dir.mkdir(parents=True)

    popen_calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))
    monkeypatch.setattr(bootstrap, "probe_cdp", lambda port, **kw: {"cdp_alive": False, "browser": None})
    monkeypatch.setattr(bootstrap, "_native_listener_pid", lambda port: None)

    # Case 1: Chrome launched WITH --remote-debugging-port=9222 -> CDP_PROBE_STARVED, 0 duplicate launches.
    monkeypatch.setattr(
        bootstrap,
        "_powershell_json",
        lambda *a, **k: [{
            "pid": 7001,
            "cmd": f'"chrome.exe" --remote-debugging-port=9222 --user-data-dir="{profile_dir}"',
        }],
    )
    ensured_starved = bootstrap.ensure_ingestion_runtime(env=env)
    assert ensured_starved["status"] == bootstrap.STATE_CDP_PROBE_STARVED
    assert ensured_starved["detail"] == "CANONICAL_CDP_9222_ACTIVE_PROBE_TIMED_OUT"
    assert ensured_starved["pid"] == 7001 and ensured_starved["launched"] is False and popen_calls == []

    # Case 2: Chrome launched WITHOUT --remote-debugging-port=9222 -> genuine RUNNING_WITHOUT_CDP, 0 launches.
    monkeypatch.setattr(
        bootstrap,
        "_powershell_json",
        lambda *a, **k: [{
            "pid": 7002,
            "cmd": f'"chrome.exe" --user-data-dir="{profile_dir}"',
        }],
    )
    ensured_no_cdp = bootstrap.ensure_ingestion_runtime(env=env)
    assert ensured_no_cdp["status"] == bootstrap.STATE_RUNNING_WITHOUT_CDP
    assert ensured_no_cdp["detail"] == "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222"
    assert ensured_no_cdp["pid"] == 7002 and ensured_no_cdp["launched"] is False and popen_calls == []

    # Case 3: Legacy int-list mock [8888] stays backward compatible as RUNNING_WITHOUT_CDP.
    monkeypatch.setattr(bootstrap, "_powershell_json", lambda *a, **k: [8888])
    ensured_legacy = bootstrap.ensure_ingestion_runtime(env=env)
    assert ensured_legacy["status"] == bootstrap.STATE_RUNNING_WITHOUT_CDP
    assert ensured_legacy["pid"] == 8888 and ensured_legacy["launched"] is False and popen_calls == []


def test_discovery_cdp_unavailable_after_prior_attach_preserves_target_id_and_heals_at_streak_2(tmp_path):
    """When /json/list times out after a known list tab was attached, preserve target_id so streak=2 heals."""
    cdp = StarvedDiscoveryCDP()
    h = Harness(tmp_path, cdp=cdp)

    # Tick 0 attaches cleanly and records the verified list tab ID ("list").
    t0 = h.tick(0)
    assert t0["state"] == "CAPTURED" and t0["target_id"] == "list"
    assert h.capture.last_list_target_id == "list"

    # Session drops and /json/list discovery becomes starved (TimeoutError), matching 24 Nov 22:48Z.
    h.capture.close_session()
    cdp.discovery_error = TimeoutError("fixture /json/list discovery timed out")

    # Failure 1: target_id is preserved as "list", no heal yet.
    t1 = h.tick(15)
    assert t1["state"] == "CDP_UNAVAILABLE"
    assert "CDP_TARGET_DISCOVERY" in str(t1["detail"])
    assert t1["target_id"] == "list" and h.runner.failure_streak == 1
    assert "tab_replacement" not in t1

    # Failure 2 (streak=2 == HEAL_AFTER_FAILURES): MUST NOT skip heal! Runs step-1 http heal even with /json/list starved.
    t2 = h.tick(30)
    assert t2["state"] == "CDP_UNAVAILABLE" and t2["target_id"] == "list" and h.runner.failure_streak == 2
    heal = t2["tab_replacement"]
    assert heal["method"] == "http" and heal["state"] == "TAB_REPLACED"
    assert heal["old_target_id"] == "list" and heal["new_target_id"] == "fresh-1"
    assert "CDP_TARGET_DISCOVERY" in str(heal["before_list_detail"])
    assert heal["closed_target_ids"] == ["list"]
    assert h.capture.preferred_target_id == "fresh-1" and h.capture.last_list_target_id == "fresh-1"
    assert {row["id"] for row in cdp.pages} == {"fresh-1", "unrelated"}

    # Discovery recovers -> next tick attaches to "fresh-1" cleanly and resets streak.
    cdp.discovery_error = None
    t3 = h.tick(45)
    assert t3["state"] == "CAPTURED" and t3["target_id"] == "fresh-1" and h.runner.failure_streak == 0


def test_discovery_cdp_unavailable_escalates_from_failed_http_to_browser_heal_at_streak_3(tmp_path):
    """If both /json/list and /json/new fail at streak=2, streak=3 escalates to browser Target.createTarget + P1."""
    cdp = StarvedDiscoveryCDP()
    h = Harness(tmp_path, cdp=cdp)
    assert h.tick(0)["state"] == "CAPTURED"

    h.capture.close_session()
    cdp.discovery_error = TimeoutError("fixture /json/list starved")
    cdp.new_http_error = TimeoutError("fixture /json/new starved")

    h.tick(15)  # streak=1
    t2 = h.tick(30)  # streak=2 -> http fails
    assert t2["tab_replacement"]["method"] == "http"
    assert t2["tab_replacement"]["state"] == "TAB_REPLACEMENT_FAILED"

    t3 = h.tick(45)  # streak=3 -> browser WS Target.createTarget succeeds and closes "list", P1 raised
    heal3 = t3["tab_replacement"]
    assert heal3["method"] == "browser" and heal3["state"] == "TAB_REPLACED"
    assert heal3["new_target_id"] == "browser-1" and heal3["closed_target_ids"] == ["list"]
    assert t3["p1_event"] == "RAISED"

    cdp.discovery_error = None
    t4 = h.tick(60)
    assert t4["state"] == "CAPTURED" and t4["target_id"] == "browser-1" and t4["p1_event"] == "CLEARED"


def test_cold_start_discovery_unavailable_with_no_known_list_tab_still_avoids_blind_tab_creation(tmp_path):
    """Fail-closed safety: when no list tab was ever observed, discovery failure never creates blind tabs."""
    cdp = StarvedDiscoveryCDP()
    cdp.discovery_error = ConnectionRefusedError("cdp 9222 down on cold start")
    h = Harness(tmp_path, cdp=cdp)

    assert h.tick(0)["state"] == "CDP_UNAVAILABLE" and "target_id" not in h.log()[-1]["capture"]
    t2 = h.tick(15)
    assert t2["state"] == "CDP_UNAVAILABLE" and "tab_replacement" not in t2
    t3 = h.tick(30)
    assert t3["state"] == "CDP_UNAVAILABLE" and "tab_replacement" not in t3 and t3["p1_event"] == "RAISED"
    assert cdp.requests == [] and cdp.browser_commands == [] and cdp.opens == 0
