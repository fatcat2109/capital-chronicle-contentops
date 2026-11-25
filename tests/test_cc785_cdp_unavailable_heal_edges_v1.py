"""CC-785: offline CDP_UNAVAILABLE heal backoff, retry escalation, and no-silent-fallback edge tests.

Strictly hermetic: local fakes only, all files under tmp_path, zero live browser/CDP/network/Neo calls,
zero production file writes, zero .stop edits, zero public posts.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote, urlsplit

import pytest

from live_contentops import ingestion_bootstrap_v1 as bootstrap_module
from live_contentops import x_list_feed_v1 as feed
from test_x_list_feed_cc785 import (
    FakeBootstrap,
    FakeCDP,
    FakeIngestion,
    Harness,
    LIST_URL,
    NOW,
    _tweet,
)


class TrackablePageClient:
    """PageClient wrapper that tracks explicit close() calls and can drop mid-listen."""

    def __init__(self, inner, *, raise_on_event=None):
        self.inner = inner
        self.raise_on_event = raise_on_event
        self.closed = 0

    def command(self, method, params=None, *, timeout_seconds=10.0):
        return self.inner.command(method, params, timeout_seconds=timeout_seconds)

    def event(self, *, timeout_seconds):
        if self.raise_on_event is not None:
            raise self.raise_on_event
        return self.inner.event(timeout_seconds=timeout_seconds)

    def close(self):
        self.closed += 1
        self.inner.close()


class FailingHttpCDP(FakeCDP):
    """FakeCDP where HTTP /json/new, /json/version, or target discovery can fail cleanly without side effects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discovery_error = None
        self.new_http_error = None
        self.version_http_error = None
        self.version_payload = {"webSocketDebuggerUrl": "ws://fake/browser"}
        self.browser_create_error = None

    def targets(self, **_):
        if self.discovery_error is not None:
            raise self.discovery_error
        return super().targets()

    def client(self, url, *, timeout_seconds):
        if url == "ws://fake/browser" and self.browser_create_error is not None:
            class FailingBrowser:
                def __init__(self, exc):
                    self.exc = exc

                def command(self, method, params=None, *, timeout_seconds=10.0):
                    raise self.exc

                def close(self):
                    pass

            return FailingBrowser(self.browser_create_error)
        return super().client(url, timeout_seconds=timeout_seconds)

    def http_open(self, request, *, timeout):
        url = urlsplit(request.full_url)
        if url.path == "/json/version":
            self.requests.append((request.get_method(), url.path, unquote(url.query)))
            if self.version_http_error is not None:
                raise self.version_http_error
            payload = json.dumps(self.version_payload).encode("utf-8")

            class _Resp:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def read(self):
                    return payload

            return _Resp()
        if url.path == "/json/new" and self.new_http_error is not None:
            self.requests.append((request.get_method(), url.path, unquote(url.query)))
            raise self.new_http_error
        return super().http_open(request, timeout=timeout)


def test_cdp_discovery_unavailable_skips_blind_tab_heal_raises_p1_and_recovers(tmp_path):
    """When /json/list discovery itself fails (CDP_UNAVAILABLE, no target_id), never create tabs blindly."""
    cdp = FailingHttpCDP()
    cdp.discovery_error = ConnectionRefusedError("cdp port 9222 refused")
    h = Harness(tmp_path, cdp=cdp)

    t0 = h.tick(0)
    assert t0["state"] == "CDP_UNAVAILABLE"
    assert "CDP_TARGET_DISCOVERY" in str(t0["detail"])
    assert "target_id" not in t0
    assert h.runner.failure_streak == 1 and h.runner.p1 is None

    t1 = h.tick(15)
    assert t1["state"] == "CDP_UNAVAILABLE"
    assert "tab_replacement" not in t1
    assert h.runner.failure_streak == 2 and h.exported()["health"]["state"] == "STALE"

    t2 = h.tick(30)
    assert t2["state"] == "CDP_UNAVAILABLE"
    assert "tab_replacement" not in t2
    assert t2["p1_event"] == "RAISED"
    health = h.exported()["health"]
    assert health["state"] == "P1" and health["p1"]["failure_streak"] == 3
    assert health["p1"]["cause"].startswith("CDP_UNAVAILABLE:")
    assert "never 'no news'" in health["reading_rule"]
    assert cdp.requests == [] and cdp.browser_commands == [] and cdp.opens == 0

    # Discovery recovers cleanly -> streak resets and P1 clears.
    cdp.discovery_error = None
    t3 = h.tick(45)
    assert t3["state"] == "CAPTURED" and t3["p1_event"] == "CLEARED"
    assert h.runner.failure_streak == 0 and h.exported()["health"]["state"] == "OK"


def test_cdp_connect_unavailable_escalates_http_to_browser_and_enforces_exact_300s_cooldown(tmp_path):
    """When CDP connect + HTTP heal + browser heal all fail, enforce exact 300s cooldown with zero fallback."""
    cdp = FailingHttpCDP(connect_fails=True)
    cdp.failing_targets.add("list")
    cdp.new_http_error = ConnectionRefusedError("http /json/new refused")
    cdp.version_http_error = ConnectionRefusedError("http /json/version refused")
    h = Harness(tmp_path, cdp=cdp)

    t0 = h.tick(0)
    assert t0["state"] == "CDP_UNAVAILABLE" and t0["target_id"] == "list"
    assert "tab_replacement" not in t0 and h.runner.failure_streak == 1

    # Failure 2: step-1 http heal fails cleanly without fabricating a target or mutating preferred_target_id.
    t1 = h.tick(15)
    assert t1["state"] == "CDP_UNAVAILABLE" and h.runner.failure_streak == 2
    heal1 = t1["tab_replacement"]
    assert heal1["method"] == "http" and heal1["state"] == "TAB_REPLACEMENT_FAILED"
    assert "new_target_id" not in heal1 and h.capture.preferred_target_id is None

    # Failure 3: step-2 browser heal runs immediately (bypasses 60s gate) and raises P1 when it also fails.
    t2 = h.tick(30)
    assert t2["state"] == "CDP_UNAVAILABLE" and h.runner.failure_streak == 3
    heal2 = t2["tab_replacement"]
    assert heal2["method"] == "browser" and heal2["state"] == "TAB_REPLACEMENT_FAILED"
    assert t2["p1_event"] == "RAISED" and h.exported()["health"]["state"] == "P1"

    # At 299s after t=30 (t=329): cooldown strictly blocks another heal retry.
    t_before = h.tick(329)
    assert "tab_replacement" not in t_before and h.runner.failure_streak == 4

    # At exact 300s boundary (t=330): browser heal retries once.
    t_at = h.tick(330)
    assert t_at["tab_replacement"]["method"] == "browser"
    assert t_at["tab_replacement"]["state"] == "TAB_REPLACEMENT_FAILED"
    assert h.runner.failure_streak == 5

    # Next tick (t=345) is back inside cooldown.
    t_after = h.tick(345)
    assert "tab_replacement" not in t_after


def test_step1_http_heal_respects_60s_reload_cooldown_while_failure_3_still_escalates(tmp_path):
    """After a recent heal (<60s ago), a fresh streak of 2 suppresses step-1 thrashing; streak 3 still escalates."""
    cdp = FakeCDP(connect_fails=True)
    cdp.failing_targets.add("list")
    h = Harness(tmp_path, cdp=cdp)

    # First outage heals via http at t=15 and recovers at t=30.
    h.tick(0)
    assert h.tick(15)["tab_replacement"]["state"] == "TAB_REPLACED"
    assert h.tick(30)["state"] == "CAPTURED" and h.runner.failure_streak == 0

    # Fresh target fails immediately at t=45 and t=60 (only 45s since t=15 heal < 60s RELOAD_AFTER_SECONDS).
    cdp.failing_targets.add("fresh-1")
    h.capture.close_session()
    assert h.tick(45)["state"] == "CDP_UNAVAILABLE" and h.runner.failure_streak == 1
    t60 = h.tick(60)
    assert t60["state"] == "CDP_UNAVAILABLE" and h.runner.failure_streak == 2
    assert "tab_replacement" not in t60  # suppressed by 60s step-1 cooldown
    assert cdp.opens == 1

    # Failure 3 at t=75 bypasses cooldown, escalates directly to browser heal, and raises P1.
    t75 = h.tick(75)
    assert t75["tab_replacement"]["method"] == "browser"
    assert t75["tab_replacement"]["state"] == "TAB_REPLACED"
    assert t75["p1_event"] == "RAISED"


def test_heal_target_fails_closed_on_invalid_new_url_or_missing_browser_ws_url(tmp_path):
    """No silent fallback to unrelated URLs (about:blank / x.com/home) or empty /json/version payloads."""
    cdp = FailingHttpCDP()
    cdp.new_url = "https://x.com/home"
    h = Harness(tmp_path, cdp=cdp)

    heal_bad_url = h.capture.heal_target("list", method="http")
    assert heal_bad_url["state"] == "TAB_REPLACEMENT_FAILED"
    assert heal_bad_url["detail"] == "NEW_LIST_TARGET_INVALID"
    assert h.capture.preferred_target_id is None
    # Existing list tab must NOT be closed when replacement is invalid.
    assert any(row["id"] == "list" for row in cdp.pages)
    assert not any(path.startswith("/json/close/") for _, path, _ in cdp.requests)

    # Browser target missing webSocketDebuggerUrl fails closed cleanly without raising.
    cdp.version_payload = {"Browser": "Chrome/142"}
    heal_missing_ws = h.capture.heal_target("list", method="browser")
    assert heal_missing_ws["state"] == "TAB_REPLACEMENT_FAILED"
    assert heal_missing_ws["detail"] == "TAB_REPLACEMENT_FAILED:IngestCaptureError"
    assert any(row["id"] == "list" for row in cdp.pages)


def test_browser_cdp_loss_closes_kept_session_enforces_exact_120s_relaunch_backoff_and_stop_short_circuits_probes(tmp_path):
    """CDP loss tears down the kept session, enforces exact 120s relaunch backoff, and STOP short-circuits probes."""
    class ProbeTrackingBootstrap(FakeBootstrap):
        def __init__(self):
            super().__init__(alive=True)
            self.probe_timeouts = []

        def probe_cdp(self, port, *, timeout=3.0):
            self.probe_timeouts.append(timeout)
            return {"cdp_alive": self.alive}

    cdp = FakeCDP()
    tracked_clients = []
    orig_client = cdp.client

    def wrapped_client(url, *, timeout_seconds):
        client = TrackablePageClient(orig_client(url, timeout_seconds=timeout_seconds))
        tracked_clients.append(client)
        return client

    cdp.client = wrapped_client
    boot = ProbeTrackingBootstrap()
    h = Harness(tmp_path, cdp=cdp, bootstrap=boot)

    # Tick 0 succeeds and keeps an open session.
    assert h.tick(0)["state"] == "CAPTURED"
    assert h.capture.session is tracked_clients[0] and tracked_clients[0].closed == 0

    # Browser CDP vanishes: runner retries [3.0, 6.0, 12.0], closes kept session, attempts launch once.
    boot.alive = False
    boot.probe_timeouts.clear()
    t15 = h.tick(15)
    assert boot.probe_timeouts == [3.0, 6.0, feed.PROBE_RETRY_TIMEOUT_SECONDS]
    assert tracked_clients[0].closed == 1 and h.capture.session is None
    assert t15["state"] == "BROWSER_NOT_READY" and boot.launches == 1 and h.runner.failure_streak == 1

    # At 119s after t=15 launch (t=134 < 135): still in 120s backoff, zero extra launches.
    t134 = h.tick(134)
    assert t134["state"] == "BROWSER_NOT_READY"
    assert t134["detail"] == "WAITING_BEFORE_NEXT_LAUNCH"
    assert boot.launches == 1 and h.runner.failure_streak == 2
    assert h.exported()["health"]["state"] == "STALE"

    # At exact 120s boundary (t=135): relaunch retries and streak 3 raises P1.
    t135 = h.tick(135)
    assert t135["state"] == "BROWSER_NOT_READY" and boot.launches == 2
    assert t135["p1_event"] == "RAISED" and h.exported()["health"]["state"] == "P1"

    # When STOP file is present during dead-CDP check, probe loop breaks after the first 3.0s probe.
    stop_file = tmp_path / "STOP"
    stop_file.write_text("stop", encoding="utf-8")
    h.runner.stop_path = stop_file
    boot.probe_timeouts.clear()
    h.t[0] = 150.0  # within 120s backoff of t=135 launch
    ready = h.runner._browser_ready()
    assert ready["ready"] is False and ready["detail"] == "WAITING_BEFORE_NEXT_LAUNCH"
    assert boot.probe_timeouts == [3.0] and boot.launches == 2


def test_idle_listen_cdp_drop_closes_session_records_idle_detail_and_reattaches_cleanly(tmp_path):
    """A mid-idle socket drop closes the kept session, records idle_detail, and recovers without duplicates."""
    cdp = FakeCDP()
    drop_once = {"armed": False}
    orig_client = cdp.client

    def wrapped_client(url, *, timeout_seconds):
        inner = orig_client(url, timeout_seconds=timeout_seconds)

        class DropOnceClient(TrackablePageClient):
            def event(self, *, timeout_seconds):
                if drop_once["armed"]:
                    drop_once["armed"] = False
                    raise ConnectionResetError("cdp socket dropped during idle listen")
                return super().event(timeout_seconds=timeout_seconds)

        return DropOnceClient(inner)

    cdp.client = wrapped_client
    h = Harness(tmp_path, cdp=cdp)

    first = h.tick(0)
    assert first["state"] == "CAPTURED" and first["new_rows"] == 2
    drop_once["armed"] = True

    # Idle listen absorbs the drop cleanly, closes the broken session, and returns False.
    assert h.runner.idle(0.1) is False
    assert h.capture.session is None

    # Next tick within 60s reload cap reattaches cleanly, surfaces idle_detail, and respects 1-reload/min.
    cdp.tweets = [_tweet(30), _tweet(5, "FirstSquawk", "FRESH HEADLINE AFTER REATTACH")]
    second = h.tick(15)
    assert second["state"] == "LISTENING" and second["attached"] is True and second["refresh"] == "light"
    assert "IDLE_LISTEN" in str(second.get("idle_detail")) and h.runner.failure_streak == 0

    # At t=60 (>= 60s reload window), reload runs on the reattached session and appends only the new post.
    third = h.tick(60)
    assert third["state"] == "CAPTURED" and third["refresh"] == "reload" and third["new_rows"] == 1
    assert len(h.sidecar_ids()) == len(set(h.sidecar_ids())) == 3


def test_no_silent_fallback_when_profile_missing_port_owner_unproven_or_running_without_cdp(monkeypatch, tmp_path):
    """Fail-closed profile continuity lock: never create profile, never fall back to Edge/Default, never launch."""
    env = {"LOCALAPPDATA": str(tmp_path / "LocalAppData")}
    profile_dir = bootstrap_module.canonical_ingestion_user_data_dir(env)
    popen_calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))
    monkeypatch.setattr(bootstrap_module, "find_chrome_binary", lambda env=None: tmp_path / "chrome.exe")

    # 1. Missing dedicated profile -> PROFILE_BINDING_MISSING, never created, zero Popen calls.
    assert not profile_dir.exists()
    rt_missing = bootstrap_module.ensure_ingestion_runtime(env=env)
    assert rt_missing["status"] == bootstrap_module.STATE_PROFILE_BINDING_MISSING
    assert rt_missing["launched"] is False
    readiness_missing = bootstrap_module.canonical_ingestion_readiness(env=env)
    assert readiness_missing["chrome_profile_binding"] == bootstrap_module.STATE_PROFILE_BINDING_MISSING
    assert readiness_missing["fallback_profile_available"] is False
    assert readiness_missing["profile_created_or_replaced"] is False
    assert not profile_dir.exists() and popen_calls == []

    # Create the canonical profile directory for cases 2 and 3.
    profile_dir.mkdir(parents=True)

    # 2. Port 9222 owned by non-canonical browser (e.g. Edge or Default Chrome) -> PORT_OWNER_UNPROVEN, zero launches.
    monkeypatch.setattr(bootstrap_module, "probe_cdp", lambda port, **kw: {"cdp_alive": True, "browser": "Edg/142"})
    monkeypatch.setattr(bootstrap_module, "_native_listener_pid", lambda port: 5555)
    monkeypatch.setattr(
        bootstrap_module,
        "_native_process_identity",
        lambda pid: {"pid": pid, "start": 77, "cmd": '"msedge.exe" --remote-debugging-port=9222'},
    )
    rt_unproven = bootstrap_module.ensure_ingestion_runtime(env=env)
    assert rt_unproven["status"] == bootstrap_module.STATE_PORT_OWNER_UNPROVEN
    assert rt_unproven["launched"] is False and popen_calls == []

    # FeedRunner must also fail closed and refuse to invoke capture_factory on PORT_OWNER_UNPROVEN.
    class UnprovenBootstrap(FakeBootstrap):
        def ingestion_process_state(self):
            return {"state": bootstrap_module.STATE_PORT_OWNER_UNPROVEN, "detail": "PORT_9222_OWNED_BY_NON_CANONICAL_PROCESS"}

    runner_unproven = feed.FeedRunner(
        feed_path=tmp_path / "feed-unproven.json",
        log_path=tmp_path / "runner-unproven.log",
        bootstrap=UnprovenBootstrap(alive=True),
        capture_factory=lambda: pytest.fail("must never attach capture when port owner is unproven"),
        clock=lambda: 0.0,
        now_fn=lambda: NOW,
        sidecar_dir=tmp_path / "sidecars",
    )
    rec = runner_unproven.iterate()
    assert rec["capture"]["state"] == "BROWSER_NOT_READY"
    assert rec["capture"]["browser"] == bootstrap_module.STATE_PORT_OWNER_UNPROVEN
    assert runner_unproven.owner_checked is None and runner_unproven.owner_key is None

    # 3. Canonical profile running without CDP 9222 -> RUNNING_WITHOUT_CDP, zero launches.
    monkeypatch.setattr(bootstrap_module, "probe_cdp", lambda port, **kw: {"cdp_alive": False, "browser": None})
    monkeypatch.setattr(bootstrap_module, "_powershell_json", lambda script, **kw: [8888])
    rt_no_cdp = bootstrap_module.ensure_ingestion_runtime(env=env)
    assert rt_no_cdp["status"] == bootstrap_module.STATE_RUNNING_WITHOUT_CDP
    assert rt_no_cdp["launched"] is False and popen_calls == []


def test_relaunch_requiring_reauth_fails_closed_without_attaching_capture(tmp_path):
    """If relaunch succeeds but session probe sees a login redirect, stay not-ready and never capture."""
    class ReauthAfterLaunchBootstrap(FakeBootstrap):
        def __init__(self):
            super().__init__(alive=False)

        def ensure_ingestion_runtime(self):
            self.launches += 1
            return {"status": self.STATE_LAUNCHED, "detail": "fixture launched"}

        def probe_ingestion_session(self):
            return {"auth_state": self.STATE_REAUTH_REQUIRED, "detail": "LOGIN_REDIRECT_OBSERVED"}

    boot = ReauthAfterLaunchBootstrap()
    runner = feed.FeedRunner(
        feed_path=tmp_path / "feed-reauth.json",
        log_path=tmp_path / "runner-reauth.log",
        bootstrap=boot,
        capture_factory=lambda: pytest.fail("must never attach capture while REAUTH_REQUIRED"),
        clock=lambda: 0.0,
        now_fn=lambda: NOW,
        sidecar_dir=tmp_path / "sidecars",
    )
    rec = runner.iterate()
    assert boot.launches == 1
    assert rec["capture"]["state"] == "BROWSER_NOT_READY"
    assert rec["capture"]["detail"] == "LOGIN_REDIRECT_OBSERVED"
    assert runner.failure_streak == 1
