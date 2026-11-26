"""CC-711 hermetic offline tests for X_List_Feed PT15M keepalive, BrowserOS Neo
CDP/SSE health & safe recovery, and Windows Task Scheduler XML/installer dry-run.

Zero live Chrome/CDP calls, zero network calls, zero live Task Scheduler mutations,
zero writes outside tmp_path.
"""
from __future__ import annotations

import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops import cc711_xfeed_neo_keepalive_v1 as keepalive


ROOT = Path(__file__).resolve().parents[1]
TASK_XML_DIR = ROOT / "config" / "task_scheduler"
X_FEED_XML_PATH = TASK_XML_DIR / "CapitalChronicle_ContentOps_X_List_Feed_Keepalive_CC711.xml"
NEO_XML_PATH = TASK_XML_DIR / "CapitalChronicle_ContentOps_BrowserOS_Neo_Health_CC711.xml"
INSTALLER_PS1 = ROOT / "scripts" / "Install-ContentOpsCC711Keepalive.ps1"


def _fixed_now() -> datetime:
    return datetime(2026, 11, 25, 15, 30, 0, tzinfo=timezone.utc)


def _fake_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True, exist_ok=True)
    (repo / "scripts" / "run_x_list_feed.py").write_text("# controlled stub\n", encoding="utf-8")
    pythonw = tmp_path / "venv" / "Scripts" / "pythonw.exe"
    pythonw.parent.mkdir(parents=True, exist_ok=True)
    pythonw.write_bytes(b"MZ-controlled-stub")
    return repo, pythonw


def _fake_neo_install(tmp_path: Path) -> tuple[Path, Path, Path]:
    exe = tmp_path / "BrowserClaw" / "Application" / "chrome.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"MZ-controlled-browseros-stub")
    user_data = tmp_path / "BrowserClaw" / "User Data"
    cfg = user_data / ".browseros" / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        json.dumps(
            {
                "instance": {"browseros_version": "0.52.0.0", "chromium_version": "155.0.8317.26"},
                "ports": {"cdp": 9110, "proxy": 9010, "server": 9210},
            }
        ),
        encoding="utf-8",
    )
    return exe, user_data, cfg


class _FakeHttpResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        lines: list[str] | None = None,
        json_body: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._lines = list(lines or [])
        self._json_body = json_body
        self.closed = False

    def iter_lines(self, chunk_size: int = 8192, decode_unicode: bool = True):
        for line in self._lines:
            yield line if decode_unicode else line.encode("utf-8")

    def json(self):
        if self._json_body is None:
            raise ValueError("NO_JSON_BODY")
        return self._json_body

    def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# 1. X_List_Feed OS-lock-guarded PT15M keepalive tests
# ---------------------------------------------------------------------------


def test_os_mutex_and_runner_lock_prevent_duplicate_keepalive_and_runner(tmp_path: Path) -> None:
    """Real OS byte locks serialize concurrent keepalives and detect live run_x_list_feed.py."""
    repo, pythonw = _fake_repo(tmp_path)
    keepalive_lock = tmp_path / "keepalive.lock"
    runner_lock = tmp_path / "runner_v1.lock"
    stop_path = tmp_path / "STOP"
    feed_path = tmp_path / "x_list_feed_v1.json"
    feed_path.write_text(
        json.dumps(
            {
                "generated_at_utc": "2026-11-25T15:29:30+00:00",
                "health": {"state": "OK", "failure_streak": 0},
            }
        ),
        encoding="utf-8",
    )

    spawned: list[list[str]] = []

    # 1) Concurrent keepalive holding keepalive_lock -> skipped immediately.
    with keepalive.os_mutex(keepalive_lock) as held:
        assert held is True
        res = keepalive.keepalive_x_list_feed(
            dry_run=False,
            lock_path=runner_lock,
            keepalive_lock_path=keepalive_lock,
            stop_path=stop_path,
            feed_path=feed_path,
            repo_root=repo,
            python_exe=pythonw,
            cdp_state_probe=lambda _p: pytest.fail("should not probe CDP while keepalive mutex is held"),
            spawner=lambda cmd, _cwd: spawned.append(cmd) or 999,
            now_fn=_fixed_now,
        )
    assert res["action"] == "SKIPPED_KEEPALIVE_LOCK_HELD"
    assert res["launched"] is False
    assert res["chrome_kill_performed"] is False
    assert spawned == []

    # 2) Live runner holding runner_v1.lock -> ALREADY_RUNNING, zero spawn, reads feed summary.
    with keepalive.os_mutex(runner_lock) as runner_held:
        assert runner_held is True
        assert keepalive.probe_os_lock_held(runner_lock) is True
        res2 = keepalive.keepalive_x_list_feed(
            dry_run=False,
            lock_path=runner_lock,
            keepalive_lock_path=keepalive_lock,
            stop_path=stop_path,
            feed_path=feed_path,
            repo_root=repo,
            python_exe=pythonw,
            cdp_state_probe=lambda _p: pytest.fail("should not probe CDP while runner lock is held"),
            spawner=lambda cmd, _cwd: spawned.append(cmd) or 999,
            now_fn=_fixed_now,
        )
    assert res2["action"] == "ALREADY_RUNNING"
    assert res2["runner_alive"] is True
    assert res2["launched"] is False
    assert res2["feed"]["health_state"] == "OK"
    assert res2["feed"]["age_seconds"] == 30.0
    assert spawned == []

    # After release, probe_os_lock_held returns False cleanly.
    assert keepalive.probe_os_lock_held(runner_lock) is False


def test_x_feed_keepalive_honors_stop_sentinel(tmp_path: Path) -> None:
    """Operator STOP sentinel always blocks launch, even when dry_run=False."""
    repo, pythonw = _fake_repo(tmp_path)
    stop_path = tmp_path / "STOP"
    stop_path.write_text("paused\n", encoding="utf-8")

    res = keepalive.keepalive_x_list_feed(
        dry_run=False,
        lock_path=tmp_path / "runner_v1.lock",
        keepalive_lock_path=tmp_path / "keepalive.lock",
        stop_path=stop_path,
        feed_path=tmp_path / "x_list_feed_v1.json",
        repo_root=repo,
        python_exe=pythonw,
        cdp_state_probe=lambda _p: pytest.fail("STOP must short-circuit before CDP probe"),
        spawner=lambda _cmd, _cwd: pytest.fail("STOP must never launch"),
        now_fn=_fixed_now,
    )
    assert res["action"] == "SKIPPED_STOP_FILE_PRESENT"
    assert res["stop_present"] is True
    assert res["launched"] is False


@pytest.mark.parametrize(
    "cdp_state,expected_action",
    [
        (keepalive.STATE_CDP_PROBE_STARVED, "HOLD_CDP_PROBE_STARVED"),
        (keepalive.STATE_RUNNING_WITHOUT_CDP, "HOLD_RUNNING_WITHOUT_CDP"),
        (keepalive.STATE_PORT_OWNER_UNPROVEN, "HOLD_PORT_OWNER_UNPROVEN"),
    ],
)
def test_x_feed_keepalive_respects_d6c0b69a_starved_cdp_and_non_canonical_guards(
    tmp_path: Path, cdp_state: str, expected_action: str
) -> None:
    """Starved CDP (d6c0b69a) and non-canonical Chrome states fail closed with zero spawn and zero kill."""
    repo, pythonw = _fake_repo(tmp_path)
    res = keepalive.keepalive_x_list_feed(
        dry_run=False,
        lock_path=tmp_path / "runner_v1.lock",
        keepalive_lock_path=tmp_path / "keepalive.lock",
        stop_path=tmp_path / "STOP",
        feed_path=tmp_path / "x_list_feed_v1.json",
        repo_root=repo,
        python_exe=pythonw,
        cdp_state_probe=lambda _p: {"state": cdp_state, "detail": "CONTROLLED_STATE", "pid": 14568},
        spawner=lambda _cmd, _cwd: pytest.fail("must never spawn duplicate Chrome/runner on held CDP state"),
        now_fn=_fixed_now,
    )
    assert res["action"] == expected_action
    assert res["launched"] is False
    assert res["chrome_kill_performed"] is False
    assert res["public_write_performed"] is False


def test_probe_x_feed_cdp_state_upgrades_pre_d6c0b69a_starved_chrome() -> None:
    """Even on ce53947a8 before d6c0b69a merges, starved canonical Chrome 9222 classifies as CDP_PROBE_STARVED."""
    starved_via_listener = keepalive.probe_x_feed_cdp_state(
        cdp_port=9222,
        bootstrap_state_fn=lambda cdp_port: {
            "state": keepalive.STATE_RUNNING_WITHOUT_CDP,
            "detail": "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222",
            "pid": 14568,
        },
        listener_probe=lambda _p: {
            "pid": 14568,
            "cmd": '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
            '--remote-debugging-port=9222 "--user-data-dir=C:\\Users\\bullw\\AppData\\Local\\Google\\Chrome\\User Data\\CapitalChronicleBot"',
        },
    )
    assert starved_via_listener["state"] == keepalive.STATE_CDP_PROBE_STARVED
    assert starved_via_listener["pid"] == 14568

    starved_via_proc = keepalive.probe_x_feed_cdp_state(
        cdp_port=9222,
        bootstrap_state_fn=lambda cdp_port: {"state": keepalive.STATE_UNAVAILABLE, "pid": None},
        listener_probe=lambda _p: None,
        chrome_process_probe=lambda: [
            {
                "pid": 14568,
                "cmd": "chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\\Data\\CapitalChronicleBot",
            }
        ],
    )
    assert starved_via_proc["state"] == keepalive.STATE_CDP_PROBE_STARVED

    non_canonical = keepalive.probe_x_feed_cdp_state(
        cdp_port=9222,
        bootstrap_state_fn=lambda cdp_port: {"state": keepalive.STATE_UNAVAILABLE, "pid": None},
        listener_probe=lambda _p: {"pid": 7777, "cmd": "C:\\SomeOtherApp\\browser.exe --remote-debugging-port=9222"},
    )
    assert non_canonical["state"] == keepalive.STATE_PORT_OWNER_UNPROVEN


@pytest.mark.parametrize("cdp_state", [keepalive.STATE_READY, keepalive.STATE_UNAVAILABLE])
def test_x_feed_keepalive_dry_run_default_and_explicit_apply_launch(tmp_path: Path, cdp_state: str) -> None:
    """Default dry_run=True never spawns; explicit dry_run=False spawns run_x_list_feed.py once."""
    repo, pythonw = _fake_repo(tmp_path)
    calls: list[tuple[list[str], Path]] = []

    dry = keepalive.keepalive_x_list_feed(
        lock_path=tmp_path / "runner_v1.lock",
        keepalive_lock_path=tmp_path / "keepalive.lock",
        stop_path=tmp_path / "STOP",
        feed_path=tmp_path / "x_list_feed_v1.json",
        repo_root=repo,
        python_exe=pythonw,
        cdp_state_probe=lambda _p: {"state": cdp_state, "detail": "CONTROLLED"},
        spawner=lambda cmd, cwd: calls.append((cmd, cwd)) or 55555,
        now_fn=_fixed_now,
    )
    assert dry["dry_run"] is True
    assert dry["action"] == "DRY_RUN_WOULD_LAUNCH_RUNNER"
    assert dry["launched"] is False
    assert dry["would_launch"] is True
    assert calls == []

    live = keepalive.keepalive_x_list_feed(
        dry_run=False,
        lock_path=tmp_path / "runner_v1.lock",
        keepalive_lock_path=tmp_path / "keepalive.lock",
        stop_path=tmp_path / "STOP",
        feed_path=tmp_path / "x_list_feed_v1.json",
        repo_root=repo,
        python_exe=pythonw,
        cdp_state_probe=lambda _p: {"state": cdp_state, "detail": "CONTROLLED"},
        spawner=lambda cmd, cwd: calls.append((cmd, cwd)) or 55555,
        now_fn=_fixed_now,
    )
    assert live["dry_run"] is False
    assert live["action"] == "LAUNCHED_RUNNER"
    assert live["launched"] is True
    assert live["pid"] == 55555
    assert len(calls) == 1
    assert calls[0][0] == [str(pythonw), "-B", str(repo / "scripts" / "run_x_list_feed.py")]


# ---------------------------------------------------------------------------
# 2. BrowserOS Neo v0.0.88 SSE priming frames & CDP/MCP health tests
# ---------------------------------------------------------------------------


def test_neo_mcp_sse_tolerates_v0088_blank_priming_frames_comments_and_notifications() -> None:
    """browseros-neo v0.0.88 blank SSE priming frames (`data:`, `data: `) and comments parse cleanly."""
    reply = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2025-03-26",
            "serverInfo": {"name": "browseros-neo", "version": "0.0.88"},
        },
    }
    sse_lines = [
        ": priming keepalive",
        "event: message",
        "id: prime-1",
        "retry: 3000",
        "data:",
        "",
        "event: message",
        "id: prime-2",
        "data: ",
        "",
        "data:   ",
        "",
        "event: message",
        'data: {"jsonrpc":"2.0","method":"notifications/ready"}',
        "",
        "event: message",
        "id: reply-1",
        "data: " + json.dumps(reply),
        # Stream intentionally stays open (no trailing EOF needed after matching id=1).
        ": trailing keepalive never reached",
    ]
    fake_resp = _FakeHttpResponse(
        status_code=200,
        headers={"Content-Type": "text/event-stream; charset=utf-8", "Mcp-Session-Id": "secret-session-id"},
        lines=sse_lines,
    )
    delete_calls: list[tuple[str, dict]] = []
    del_resp = _FakeHttpResponse(status_code=204)

    def fake_delete(url: str, *, headers: dict, timeout: object):
        delete_calls.append((url, dict(headers)))
        return del_resp

    res = keepalive.probe_neo_mcp_sse(
        "http://127.0.0.1:9010/mcp",
        http_post=lambda *_a, **_kw: fake_resp,
        http_delete=fake_delete,
    )
    assert res["mcp_alive"] is True
    assert res["protocol_version"] == "2025-03-26"
    assert res["server_name"] == "browseros-neo"
    assert res["server_version"] == "0.0.88"
    assert res["priming_frames_ignored"] == 3
    assert res["session_header_present"] is True
    assert res["session_cleanup_attempted"] is True
    assert "secret-session-id" not in json.dumps(res)
    assert fake_resp.closed is True
    assert delete_calls == [("http://127.0.0.1:9010/mcp", {"Mcp-Session-Id": "secret-session-id"})]
    assert del_resp.closed is True

    # Best-effort DELETE failure (e.g. HTTP 405 / transport error) never breaks a healthy probe.
    fake_resp2 = _FakeHttpResponse(
        status_code=200,
        headers={"Content-Type": "text/event-stream", "Mcp-Session-Id": "secret-session-2"},
        lines=sse_lines,
    )
    res2 = keepalive.probe_neo_mcp_sse(
        "http://127.0.0.1:9010/mcp",
        http_post=lambda *_a, **_kw: fake_resp2,
        http_delete=lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("HTTP 405")),
    )
    assert res2["mcp_alive"] is True
    assert "secret-session-2" not in json.dumps(res2)


def test_neo_mcp_sse_multiline_json_plain_json_and_error_bounds() -> None:
    """Multi-line SSE JSON, plain application/json, non-loopback rejection, and timeouts behave fail-closed."""
    # 1) Multi-line JSON across consecutive data: lines
    parsed = keepalive.parse_mcp_sse_response(
        [
            "data:",
            "",
            'data: {"jsonrpc":"2.0","id":7,',
            'data: "result":{"protocolVersion":"2025-03-26"}}',
            "",
        ],
        request_id=7,
    )
    assert parsed["priming_frames_ignored"] == 1
    assert parsed["message"]["result"]["protocolVersion"] == "2025-03-26"

    # 2) Plain application/json response
    plain = _FakeHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        json_body={"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}},
    )
    res_plain = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", http_post=lambda *_a, **_kw: plain)
    assert res_plain["mcp_alive"] is True
    assert res_plain["priming_frames_ignored"] == 0
    assert plain.closed is True

    # 3) Non-loopback endpoint rejected before any HTTP call
    with pytest.raises(ValueError, match="NEO_LOCAL_ENDPOINT_REQUIRED"):
        keepalive.probe_neo_mcp_sse("https://evil.example/mcp", http_post=lambda *_a, **_kw: pytest.fail("no remote"))

    # 4) SSE stream with only blank priming frames and no reply -> NEO_SSE_REPLY_MISSING
    empty_sse = _FakeHttpResponse(
        status_code=200,
        headers={"Content-Type": "text/event-stream"},
        lines=["data:", "", "data: ", ""],
    )
    res_missing = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", http_post=lambda *_a, **_kw: empty_sse)
    assert res_missing["mcp_alive"] is False
    assert res_missing["error"] == "NEO_SSE_REPLY_MISSING"

    # 5) HTTP 503 -> NEO_MCP_HTTP_503
    err_resp = _FakeHttpResponse(status_code=503, headers={"Content-Type": "text/plain"})
    res_503 = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", http_post=lambda *_a, **_kw: err_resp)
    assert res_503["mcp_alive"] is False
    assert res_503["error"] == "NEO_MCP_HTTP_503"


def test_probe_cdp_version_parses_loopback_response_and_retries_once() -> None:
    """probe_cdp_version succeeds on retry without hitting any real socket."""
    attempts: list[float] = []

    class _FakeUrllibResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            self.close()

    def fake_open(url: str, timeout: float = 3.0):
        attempts.append(timeout)
        assert url == "http://127.0.0.1:9110/json/version"
        if len(attempts) == 1:
            raise TimeoutError("transient stall")
        return _FakeUrllibResp(json.dumps({"Browser": "Chrome/155.0.8317.26", "Protocol-Version": "1.3"}).encode())

    res = keepalive.probe_cdp_version(9110, timeout_seconds=1.5, retry_timeout_seconds=2.5, http_open=fake_open)
    assert res["cdp_alive"] is True
    assert res["attempts"] == 2
    assert res["browser"] == "Chrome/155.0.8317.26"
    assert attempts == [1.5, 2.5]


# ---------------------------------------------------------------------------
# 3. BrowserOS Neo safe recovery (NEVER kills active Chrome if CDP responds!)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cdp_alive,mcp_alive,procs,expected_state,expected_action",
    [
        (True, True, [{"pid": 35688, "name": "chrome.exe"}], "HEALTHY", "NO_ACTION_HEALTHY"),
        (True, False, [{"pid": 35688, "name": "chrome.exe"}], "DEGRADED_MCP_CDP_ALIVE", "HOLD_CDP_ALIVE_NEVER_KILL_CHROME"),
        (False, True, [{"pid": 35688, "name": "chrome.exe"}], "DEGRADED_CDP_MCP_ALIVE", "HOLD_MCP_ALIVE_NEVER_KILL_CHROME"),
        (False, False, [{"pid": 35688, "name": "chrome.exe"}], "NEO_PROBE_STARVED", "HOLD_PROCESS_ALIVE_PROBE_STARVED"),
    ],
)
def test_neo_recovery_never_kills_or_duplicates_active_chrome(
    tmp_path: Path,
    cdp_alive: bool,
    mcp_alive: bool,
    procs: list[dict],
    expected_state: str,
    expected_action: str,
) -> None:
    """When CDP responds (or MCP/BrowserClaw process is alive), recovery NEVER kills or spawns Chrome."""
    exe, user_data, cfg = _fake_neo_install(tmp_path)
    res = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": cdp_alive, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": mcp_alive, "endpoint": u},
        process_probe=lambda: procs,
        spawner=lambda _cmd, _cwd: pytest.fail("must NEVER launch while Chrome/CDP/MCP is alive"),
        now_fn=_fixed_now,
    )
    assert res["health"]["state"] == expected_state
    assert res["action"] == expected_action
    assert res["chrome_kill_performed"] is False
    assert res["killed_pids"] == []
    assert res["launched"] is False


def test_neo_recovery_cold_start_dry_run_default_and_apply_when_down(tmp_path: Path) -> None:
    """Cold-start recovery runs ONLY when CDP=down, MCP=down, and zero BrowserClaw processes exist."""
    exe, user_data, cfg = _fake_neo_install(tmp_path)
    spawned: list[tuple[list[str], Path]] = []

    ports = keepalive.load_browseros_ports(cfg)
    assert (ports["cdp_port"], ports["mcp_port"], ports["server_port"]) == (9110, 9010, 9210)
    assert ports["config_found"] is True

    # Default dry_run=True
    dry = keepalive.recover_browseros_neo(
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: [],
        spawner=lambda cmd, cwd: spawned.append((cmd, cwd)) or 61234,
        now_fn=_fixed_now,
    )
    assert dry["dry_run"] is True
    assert dry["action"] == "DRY_RUN_WOULD_START_NEO"
    assert dry["would_launch"] is True
    assert dry["launched"] is False
    assert dry["chrome_kill_performed"] is False
    assert spawned == []

    # Explicit dry_run=False -> cold start once
    live = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: [],
        spawner=lambda cmd, cwd: spawned.append((cmd, cwd)) or 61234,
        now_fn=_fixed_now,
    )
    assert live["action"] == "LAUNCHED_NEO"
    assert live["launched"] is True
    assert live["pid"] == 61234
    assert live["killed_pids"] == []
    assert live["chrome_kill_performed"] is False
    assert spawned == [([str(exe)], exe.parent)]

    # Missing existing User Data profile fails closed (never creates a blank profile!)
    missing_profile = tmp_path / "absent_user_data"
    blocked = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=missing_profile,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: [],
        spawner=lambda _cmd, _cwd: pytest.fail("must never create a blank profile"),
        now_fn=_fixed_now,
    )
    assert blocked["action"] == "BLOCKED_PROFILE_MISSING"
    assert not missing_profile.exists()


# ---------------------------------------------------------------------------
# 4. Windows Task Scheduler XML templates & PowerShell dry-run installer tests
# ---------------------------------------------------------------------------


def test_committed_task_scheduler_xml_templates_match_and_validate() -> None:
    """Committed XML templates are exact, COM-safe (no encoding= attr), disabled, UserId=JP, InteractiveToken, PT15M."""
    x_xml = X_FEED_XML_PATH.read_text(encoding="utf-8")
    neo_xml = NEO_XML_PATH.read_text(encoding="utf-8")

    assert x_xml == keepalive.render_x_list_feed_keepalive_xml()
    assert neo_xml == keepalive.render_neo_health_keepalive_xml()
    assert x_xml.splitlines()[0] == '<?xml version="1.0"?>'
    assert neo_xml.splitlines()[0] == '<?xml version="1.0"?>'
    assert "<StartBoundary>2026-11-25T00:00:00+07:00</StartBoundary>" in x_xml
    assert "<StartBoundary>2026-11-25T00:00:00+07:00</StartBoundary>" in neo_xml

    x_meta = keepalive.validate_task_scheduler_xml(x_xml, expected_task_name=keepalive.X_FEED_TASK_NAME)
    assert x_meta["user_id"] == "JP"
    assert x_meta["logon_type"] == "InteractiveToken"
    assert x_meta["enabled"] is False
    assert x_meta["repeat_interval"] == "PT15M"
    assert x_meta["multiple_instances_policy"] == "IgnoreNew"

    neo_meta = keepalive.validate_task_scheduler_xml(neo_xml, expected_task_name=keepalive.NEO_HEALTH_TASK_NAME)
    assert neo_meta["user_id"] == "JP"
    assert neo_meta["logon_type"] == "InteractiveToken"
    assert neo_meta["enabled"] is False
    assert neo_meta["repeat_interval"] == "PT15M"
    assert neo_meta["multiple_instances_policy"] == "IgnoreNew"

    # H1: XML prolog with encoding="UTF-8" fails closed (Task Scheduler COM rejects it).
    bad_prolog = x_xml.replace('<?xml version="1.0"?>', '<?xml version="1.0" encoding="UTF-8"?>', 1)
    with pytest.raises(ValueError, match="XML_PROLOG_ENCODING_ATTR_FORBIDDEN"):
        keepalive.validate_task_scheduler_xml(bad_prolog, expected_task_name=keepalive.X_FEED_TASK_NAME)

    # Enabled=true fails closed when require_disabled=True.
    bad_enabled = keepalive.render_x_list_feed_keepalive_xml(enabled=True)
    with pytest.raises(ValueError, match="ENABLED_MUST_BE_FALSE"):
        keepalive.validate_task_scheduler_xml(bad_enabled, expected_task_name=keepalive.X_FEED_TASK_NAME)

    # Wrong UserId fails closed.
    bad_user = keepalive.render_x_list_feed_keepalive_xml(user_id="SYSTEM")
    with pytest.raises(ValueError, match="USER_ID_MISMATCH"):
        keepalive.validate_task_scheduler_xml(bad_user, expected_task_name=keepalive.X_FEED_TASK_NAME)


def test_cli_render_xml_and_powershell_installer_default_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI render-xml matches committed files, and PS1 installer COM-validates both XMLs in dry-run with zero mutation."""
    import importlib.util

    cli_path = ROOT / "scripts" / "run_cc711_keepalive.py"
    spec = importlib.util.spec_from_file_location("run_cc711_keepalive", cli_path)
    cli = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(cli)

    assert cli.main(["render-xml", "--target", "x-feed"]) == 0
    assert capsys.readouterr().out == X_FEED_XML_PATH.read_text(encoding="utf-8")

    assert cli.main(["render-xml", "--target", "neo-health"]) == 0
    assert capsys.readouterr().out == NEO_XML_PATH.read_text(encoding="utf-8")

    # Execute Install-ContentOpsCC711Keepalive.ps1 in default dry-run mode (no -Apply):
    # exercises real read-only in-memory Schedule.Service COM XML validation with zero live task mutations!
    completed = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(INSTALLER_PS1)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["dry_run"] is True
    assert report["live_task_mutated"] is False
    assert report["public_write_performed"] is False
    assert len(report["tasks"]) == 2
    assert all(
        t["action"] == "DRY_RUN_VALIDATED_NO_MUTATION"
        and t["com_xml_validated"] is True
        and t["user_id"] == "JP"
        and t["logon_type"] == "InteractiveToken"
        and t["enabled"] is False
        and t["repeat_interval"] == "PT15M"
        for t in report["tasks"]
    )


# ---------------------------------------------------------------------------
# 5. Review-hardening regressions (H2 fail-closed process probe, M2 proxy bypass, M3 default listener, L1 read-only status)
# ---------------------------------------------------------------------------


def test_h2_default_neo_process_probe_fails_closed_on_timeout_error_and_bad_json() -> None:
    """H2: _default_neo_process_probe returns None on any error/timeout/empty/bad JSON; [] ONLY on proven ok=true."""
    def _timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd="powershell.exe", timeout=10)

    def _oserr(*_a, **_kw):
        raise OSError("spawn blocked")

    assert keepalive._default_neo_process_probe(run_fn=_timeout, platform_name="nt") is None
    assert keepalive._default_neo_process_probe(run_fn=_oserr, platform_name="nt") is None
    assert (
        keepalive._default_neo_process_probe(
            run_fn=lambda *_a, **_kw: subprocess.CompletedProcess([], 1, "", "WMI failed"),
            platform_name="nt",
        )
        is None
    )
    assert (
        keepalive._default_neo_process_probe(
            run_fn=lambda *_a, **_kw: subprocess.CompletedProcess([], 0, "", ""),
            platform_name="nt",
        )
        is None
    )
    assert (
        keepalive._default_neo_process_probe(
            run_fn=lambda *_a, **_kw: subprocess.CompletedProcess([], 0, "{bad-json", ""),
            platform_name="nt",
        )
        is None
    )
    assert (
        keepalive._default_neo_process_probe(
            run_fn=lambda *_a, **_kw: subprocess.CompletedProcess([], 0, '{"ok":false,"procs":[]}', ""),
            platform_name="nt",
        )
        is None
    )
    assert keepalive._default_neo_process_probe(run_fn=lambda *_a, **_kw: None, platform_name="posix") is None

    # Proven empty envelope -> []
    assert (
        keepalive._default_neo_process_probe(
            run_fn=lambda *_a, **_kw: subprocess.CompletedProcess([], 0, '{"ok":true,"procs":[]}', ""),
            platform_name="nt",
        )
        == []
    )
    # Single dict or list envelope -> normalized list[dict]
    assert keepalive._default_neo_process_probe(
        run_fn=lambda *_a, **_kw: subprocess.CompletedProcess(
            [], 0, '{"ok":true,"procs":{"pid":35688,"name":"chrome.exe"}}', ""
        ),
        platform_name="nt",
    ) == [{"pid": 35688, "name": "chrome.exe"}]
    assert keepalive._default_neo_process_probe(
        run_fn=lambda *_a, **_kw: subprocess.CompletedProcess(
            [], 0, '{"ok":true,"procs":[{"pid":35688,"name":"chrome.exe"}]}', ""
        ),
        platform_name="nt",
    ) == [{"pid": 35688, "name": "chrome.exe"}]


def test_h2_neo_recovery_fails_closed_on_unproven_process_probe_and_active_native_listener(tmp_path: Path) -> None:
    """H2: None/exception process_probe -> HOLD_PROCESS_PROBE_UNPROVEN; active native TCP listener -> NEO_PROBE_STARVED."""
    exe, user_data, cfg = _fake_neo_install(tmp_path)

    # 1) process_probe returns None (e.g. WMI timeout under load) -> fail closed, NEVER launch!
    unproven = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: None,
        listener_pid_probe=lambda _p: None,
        spawner=lambda _cmd, _cwd: pytest.fail("must NEVER cold-start when process_probe is unproven"),
        now_fn=_fixed_now,
    )
    assert unproven["health"]["state"] == "PROCESS_PROBE_UNPROVEN"
    assert unproven["health"]["process_probe_ok"] is False
    assert unproven["action"] == "HOLD_PROCESS_PROBE_UNPROVEN"
    assert unproven["launched"] is False
    assert unproven["would_launch"] is False
    assert unproven["chrome_kill_performed"] is False

    # 2) process_probe raises exception -> fail closed identically.
    raised = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: (_ for _ in ()).throw(RuntimeError("CIM hung")),
        listener_pid_probe=lambda _p: None,
        spawner=lambda _cmd, _cwd: pytest.fail("must NEVER cold-start on process_probe exception"),
        now_fn=_fixed_now,
    )
    assert raised["health"]["state"] == "PROCESS_PROBE_UNPROVEN"
    assert raised["action"] == "HOLD_PROCESS_PROBE_UNPROVEN"
    assert raised["launched"] is False

    # 3) Active native TCP listener on 9110 or 9010 holds as NEO_PROBE_STARVED even if WMI failed or returned [].
    starved_listener = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": False, "cdp_port": p},
        mcp_probe=lambda u: {"mcp_alive": False, "endpoint": u},
        process_probe=lambda: [],
        listener_pid_probe=lambda port: 35688 if port == 9110 else None,
        spawner=lambda _cmd, _cwd: pytest.fail("must NEVER cold-start when native TCP listener is active"),
        now_fn=_fixed_now,
    )
    assert starved_listener["health"]["state"] == "NEO_PROBE_STARVED"
    assert starved_listener["health"]["listener_alive"] is True
    assert starved_listener["health"]["listener_pids"] == {"cdp": 35688}
    assert starved_listener["action"] == "HOLD_PROCESS_ALIVE_PROBE_STARVED"
    assert starved_listener["launched"] is False


def test_m2_probe_cdp_version_bypasses_http_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """M2: default probe_cdp_version builds urllib opener with empty ProxyHandler({})."""
    import urllib.request

    handlers_seen: list[object] = []

    class _FakeOpener:
        def open(self, url: str, timeout: float = 3.0):
            assert url == "http://127.0.0.1:9110/json/version"

            class _Resp(io.BytesIO):
                def __enter__(self):
                    return self

                def __exit__(self, *_a):
                    self.close()

            return _Resp(json.dumps({"Browser": "Chrome/155.0.8317.26"}).encode())

    def fake_build_opener(*handlers):
        handlers_seen.extend(handlers)
        return _FakeOpener()

    monkeypatch.setattr(urllib.request, "build_opener", fake_build_opener)
    res = keepalive.probe_cdp_version(9110)
    assert res["cdp_alive"] is True
    assert len(handlers_seen) == 1
    assert isinstance(handlers_seen[0], urllib.request.ProxyHandler)
    assert handlers_seen[0].proxies == {}


def test_m3_probe_x_feed_cdp_state_wires_default_native_listener_probe_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M3: production probe_x_feed_cdp_state() automatically invokes native listener probe on pre-d6c0b69a states."""
    from live_contentops import ingestion_bootstrap_v1 as bootstrap

    monkeypatch.setattr(
        bootstrap,
        "ingestion_process_state",
        lambda cdp_port=9222: {
            "state": keepalive.STATE_RUNNING_WITHOUT_CDP,
            "detail": "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222",
            "pid": 14568,
        },
    )
    monkeypatch.setattr(bootstrap, "_native_listener_pid", lambda port: 14568 if port == 9222 else None)
    monkeypatch.setattr(
        bootstrap,
        "_native_process_identity",
        lambda pid: {
            "pid": pid,
            "cmd": '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
            '--remote-debugging-port=9222 "--user-data-dir=C:\\Users\\bullw\\AppData\\Local\\Google\\Chrome\\User Data\\CapitalChronicleBot"',
        },
    )
    res = keepalive.probe_x_feed_cdp_state(cdp_port=9222)
    assert res["state"] == keepalive.STATE_CDP_PROBE_STARVED
    assert res["pid"] == 14568


def test_l1_status_x_list_feed_is_strictly_read_only_and_creates_zero_files(tmp_path: Path) -> None:
    """L1: status_x_list_feed creates zero lock or state files on disk."""
    isolated = tmp_path / "ro_check"
    isolated.mkdir()
    res = keepalive.status_x_list_feed(
        lock_path=isolated / "runner_v1.lock",
        stop_path=isolated / "STOP",
        feed_path=isolated / "x_list_feed_v1.json",
        cdp_port=9222,
        cdp_state_probe=lambda _p: {"state": keepalive.STATE_READY, "pid": 14568},
        now_fn=_fixed_now,
    )
    assert res["read_only"] is True
    assert res["dry_run"] is True
    assert res["public_write_performed"] is False
    assert res["live_task_mutated"] is False
    assert res["runner_alive"] is False
    assert res["state"] == keepalive.STATE_READY
    assert list(isolated.iterdir()) == []


# ---------------------------------------------------------------------------
# 6. Post-Wave-1 installer guard (-PreserveExistingEnabled) & security-scan comment hygiene
# ---------------------------------------------------------------------------


def _run_shadowed_installer_apply(
    *,
    existing_map: dict[str, bool | str],
    extra_args: str = "",
) -> tuple[subprocess.CompletedProcess[str], list[dict[str, object]]]:
    """Run Install-ContentOpsCC711Keepalive.ps1 -Apply in a disposable pwsh scope with shadowed Task Scheduler cmdlets.

    Zero live Windows Task Scheduler calls are ever performed.
    """
    existing_json = json.dumps(existing_map)
    ps_script = f"""
$ErrorActionPreference = 'Stop'
$global:cc711ExistingMap = ConvertFrom-Json -InputObject @'
{existing_json}
'@
$global:cc711Registered = @()

function Get-ScheduledTask {{
    param([string]$TaskName, [string]$ErrorAction)
    $prop = $global:cc711ExistingMap.PSObject.Properties[$TaskName]
    if ($null -eq $prop) {{
        throw "No MSFT_ScheduledTask objects found with property 'TaskName' equal to '$TaskName'."
    }}
    if ($prop.Value -is [string] -and $prop.Value -eq 'PROBE_ERROR') {{
        throw 'Simulated CIM/WMI transport error'
    }}
    return [pscustomobject]@{{
        TaskName = $TaskName
        Settings = [pscustomobject]@{{ Enabled = [bool]$prop.Value }}
    }}
}}

function Register-ScheduledTask {{
    param([string]$TaskName, [string]$Xml, [switch]$Force)
    $global:cc711Registered += [pscustomobject]@{{
        task_name = $TaskName
        xml = $Xml
        force = [bool]$Force
    }}
}}

$installerOut = & '{str(INSTALLER_PS1)}' -Apply {extra_args} | Out-String
[pscustomobject]@{{
    report = ($installerOut | ConvertFrom-Json)
    registered = $global:cc711Registered
}} | ConvertTo-Json -Depth 8
"""
    completed = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return completed, []
    envelope = json.loads(completed.stdout)
    reg = envelope.get("registered") or []
    if isinstance(reg, dict):
        reg = [reg]
    return completed, reg


def test_installer_preserve_existing_enabled_default_true_and_opt_out_and_fail_closed() -> None:
    """Sweeper #4: -PreserveExistingEnabled (default $true) preserves live Enabled=True atomically; never mutates XML on disk."""
    x_before = X_FEED_XML_PATH.read_bytes()
    neo_before = NEO_XML_PATH.read_bytes()

    # 1) Default -Apply (PreserveExistingEnabled=$true): live X_List_Feed (Enabled=True) stays Enabled=True atomically,
    # while uninstalled NeoHealth stays Enabled=False.
    proc_default, reg_default = _run_shadowed_installer_apply(
        existing_map={keepalive.X_FEED_TASK_NAME: True},
    )
    assert proc_default.returncode == 0, proc_default.stderr
    report_default = json.loads(proc_default.stdout)["report"]
    assert report_default["preserve_existing_enabled"] is True
    assert report_default["live_task_mutated"] is True
    by_name = {t["task_name"]: t for t in report_default["tasks"]}
    assert by_name[keepalive.X_FEED_TASK_NAME]["existing_task_found"] is True
    assert by_name[keepalive.X_FEED_TASK_NAME]["existing_enabled"] is True
    assert by_name[keepalive.X_FEED_TASK_NAME]["effective_enabled"] is True
    assert by_name[keepalive.X_FEED_TASK_NAME]["enabled"] is False  # template remains disabled
    assert by_name[keepalive.X_FEED_TASK_NAME]["action"] == "REGISTERED_PRESERVED_ENABLED"
    assert by_name[keepalive.NEO_HEALTH_TASK_NAME]["existing_task_found"] is False
    assert by_name[keepalive.NEO_HEALTH_TASK_NAME]["effective_enabled"] is False
    assert by_name[keepalive.NEO_HEALTH_TASK_NAME]["action"] == "REGISTERED_DISABLED"

    reg_by_name = {r["task_name"]: r for r in reg_default}
    assert "<Enabled>true</Enabled>" in str(reg_by_name[keepalive.X_FEED_TASK_NAME]["xml"])
    assert "<Enabled>false</Enabled>" not in str(reg_by_name[keepalive.X_FEED_TASK_NAME]["xml"])
    assert str(reg_by_name[keepalive.X_FEED_TASK_NAME]["xml"]).startswith('<?xml version="1.0"?>')
    assert "<Enabled>false</Enabled>" in str(reg_by_name[keepalive.NEO_HEALTH_TASK_NAME]["xml"])

    # 2) Explicit -PreserveExistingEnabled:$false forces disabled registration even when existing task is Enabled=True.
    proc_opt_out, reg_opt_out = _run_shadowed_installer_apply(
        existing_map={keepalive.X_FEED_TASK_NAME: True},
        extra_args="-PreserveExistingEnabled:$false",
    )
    assert proc_opt_out.returncode == 0, proc_opt_out.stderr
    report_opt_out = json.loads(proc_opt_out.stdout)["report"]
    assert report_opt_out["preserve_existing_enabled"] is False
    x_opt_out = next(t for t in report_opt_out["tasks"] if t["task_name"] == keepalive.X_FEED_TASK_NAME)
    assert x_opt_out["effective_enabled"] is False
    assert x_opt_out["action"] == "REGISTERED_DISABLED"
    x_reg_opt_out = next(r for r in reg_opt_out if r["task_name"] == keepalive.X_FEED_TASK_NAME)
    assert "<Enabled>false</Enabled>" in str(x_reg_opt_out["xml"])

    # 3) Existing task that is already Disabled stays Disabled even with default -PreserveExistingEnabled=$true.
    proc_disabled, reg_disabled = _run_shadowed_installer_apply(
        existing_map={keepalive.X_FEED_TASK_NAME: False},
        extra_args="-Target XFeed",
    )
    assert proc_disabled.returncode == 0, proc_disabled.stderr
    x_dis = json.loads(proc_disabled.stdout)["report"]["tasks"][0]
    assert x_dis["existing_task_found"] is True
    assert x_dis["existing_enabled"] is False
    assert x_dis["effective_enabled"] is False
    assert x_dis["action"] == "REGISTERED_DISABLED"
    assert "<Enabled>false</Enabled>" in str(reg_disabled[0]["xml"])

    # 4) Non-ObjectNotFound probe failure under default -Apply fails closed (never silently disables a live task).
    proc_err, reg_err = _run_shadowed_installer_apply(
        existing_map={keepalive.X_FEED_TASK_NAME: "PROBE_ERROR"},
        extra_args="-Target XFeed",
    )
    assert proc_err.returncode != 0
    assert "CC711_EXISTING_TASK_STATE_UNPROVEN" in (proc_err.stderr + proc_err.stdout)
    assert reg_err == []

    # 5) Dry-run with -PreserveExistingEnabled:$false stays strictly read-only.
    dry_opt_out = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(INSTALLER_PS1), "-PreserveExistingEnabled:$false"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert dry_opt_out.returncode == 0, dry_opt_out.stderr
    dry_report = json.loads(dry_opt_out.stdout)
    assert dry_report["dry_run"] is True
    assert dry_report["live_task_mutated"] is False
    assert dry_report["preserve_existing_enabled"] is False
    assert all(t["effective_enabled"] is False and t["planned_apply_action"] == "REGISTERED_DISABLED" for t in dry_report["tasks"])

    # Committed XML files on disk are byte-for-byte untouched.
    assert X_FEED_XML_PATH.read_bytes() == x_before
    assert NEO_XML_PATH.read_bytes() == neo_before


def test_security_scans_cc711_comment_references_port_9010_not_9128() -> None:
    """CC Reviewer Batch #10 cosmetic hygiene: keepalive allowlist comment cites actual Neo MCP port 9010."""
    text = (ROOT / "tests" / "test_security_scans.py").read_text(encoding="utf-8")
    assert "9128" not in text
    assert "127.0.0.1:9010/mcp" in text


# ---------------------------------------------------------------------------
# 7. Pure-stdlib http.client Neo MCP SSE probe tests (v1-runtime\venv zero-requests parity)
# ---------------------------------------------------------------------------


class _FakeSocket:
    def __init__(self) -> None:
        self.timeouts: list[float] = []

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)


class _FakeStdlibHttpResponse:
    def __init__(
        self,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
        body: bytes = b"",
        use_read1: bool = True,
    ) -> None:
        import email.message

        self.status = status
        msg = email.message.Message()
        for k, v in (headers or {}).items():
            msg[k] = v
        self.headers = msg
        self._chunks = list(chunks or [])
        self._chunk_idx = 0
        self._body = body
        self._lines_stream = io.BytesIO(b"".join(self._chunks) if self._chunks else body)
        self.closed = False
        self.read_calls = 0
        if not use_read1:
            self.read1 = None  # type: ignore[assignment]

    def read1(self, size: int = 8192) -> bytes:
        self.read_calls += 1
        if self._chunk_idx >= len(self._chunks):
            return b""
        chunk = self._chunks[self._chunk_idx]
        self._chunk_idx += 1
        return chunk

    def readline(self, limit: int = -1) -> bytes:
        self.read_calls += 1
        return self._lines_stream.readline(limit)

    def read(self, amt: int = -1) -> bytes:
        self.read_calls += 1
        return self._body[:amt] if amt >= 0 else self._body

    def close(self) -> None:
        self.closed = True


class _FakeStdlibHttpConnection:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        *,
        response_or_exc: object = None,
        event_log: list[dict[str, object]] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = _FakeSocket()
        self._response_or_exc = response_or_exc
        self._event_log = event_log if event_log is not None else []
        self.requests_made: list[tuple[str, str, bytes | None, dict[str, str]]] = []
        self.closed = False
        self._event_log.append({"event": "open", "host": host, "port": port, "timeout": timeout})

    def request(
        self,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        hdrs = dict(headers or {})
        self.requests_made.append((method, url, body, hdrs))
        self._event_log.append({"event": "request", "method": method, "url": url, "headers": hdrs})
        if isinstance(self._response_or_exc, Exception):
            raise self._response_or_exc

    def getresponse(self):
        if callable(self._response_or_exc):
            return self._response_or_exc()
        return self._response_or_exc

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            self._event_log.append({"event": "close", "host": self.host, "port": self.port})


def test_cc711_keepalive_module_has_zero_requests_import() -> None:
    """CC-711 keepalive runtime and CLI must remain 100% pure stdlib (v1-runtime venv has no requests)."""
    import ast

    for rel in ("live_contentops/cc711_xfeed_neo_keepalive_v1.py", "scripts/run_cc711_keepalive.py"):
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "requests" and not alias.name.startswith("requests."), rel
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert mod != "requests" and not mod.startswith("requests."), rel


def test_cc711_stdlib_http_client_sse_priming_frames_no_proxy_and_session_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default probe_neo_mcp_sse uses pure stdlib http.client, bypasses proxies, ignores v0.0.88 priming frames, and DELETEs session."""
    import http.client
    import sys

    # Simulate v1-runtime\venv where `requests` is not installed.
    monkeypatch.setitem(sys.modules, "requests", None)
    # Poison proxy env vars to prove direct loopback http.client ignores them completely.
    monkeypatch.setenv("HTTP_PROXY", "http://198.51.100.99:8888")
    monkeypatch.setenv("HTTPS_PROXY", "http://198.51.100.99:8888")
    monkeypatch.setenv("ALL_PROXY", "http://198.51.100.99:8888")

    reply = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2025-03-26",
            "serverInfo": {"name": "browseros-neo", "version": "0.0.88"},
        },
    }
    reply_bytes = json.dumps(reply).encode("utf-8")
    split_at = len(reply_bytes) // 2
    post_resp = _FakeStdlibHttpResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream; charset=utf-8",
            "Mcp-Session-Id": "neo-stdlib-secret-sid",
        },
        chunks=[
            b": keepalive\r\nevent: message\r\nid: prime-1\r\ndata:\r\n\r\n",
            b"event: message\ndata: \n\n",
            b"event: message\ndata: " + reply_bytes[:split_at],
            reply_bytes[split_at:] + b"\n\n",
            # Open-stream trailing chunk that must never be pulled once id=1 matches.
            b": unread-open-stream-chunk\n",
        ],
    )
    del_resp = _FakeStdlibHttpResponse(status=204, headers={}, body=b"")
    events: list[dict[str, object]] = []
    conns: list[_FakeStdlibHttpConnection] = []
    queue: list[object] = [post_resp, del_resp]

    def fake_http_connection(host: str, port: int, timeout: float | None = None):
        conn = _FakeStdlibHttpConnection(
            host,
            port,
            timeout=timeout,
            response_or_exc=queue.pop(0),
            event_log=events,
        )
        conns.append(conn)
        return conn

    monkeypatch.setattr(http.client, "HTTPConnection", fake_http_connection)

    res = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp?mode=probe", timeout_seconds=8.0)

    assert res["mcp_alive"] is True
    assert res["http_status"] == 200
    assert res["protocol_version"] == "2025-03-26"
    assert res["server_name"] == "browseros-neo"
    assert res["server_version"] == "0.0.88"
    assert res["priming_frames_ignored"] == 2
    assert res["session_header_present"] is True
    assert res["session_cleanup_attempted"] is True
    assert res["error"] is None
    assert "neo-stdlib-secret-sid" not in json.dumps(res)

    # Exactly 2 connections: POST first (closed before DELETE opens), then fresh DELETE.
    assert len(conns) == 2
    post_conn, del_conn = conns
    assert (post_conn.host, post_conn.port, post_conn.timeout) == ("127.0.0.1", 9010, 3.0)
    assert post_conn.closed is True
    assert post_resp.closed is True
    # Stopped immediately after chunk #4 matched id=1; never blocked on chunk #5.
    assert post_resp.read_calls == 4
    post_method, post_target, post_body, post_hdrs = post_conn.requests_made[0]
    assert post_method == "POST"
    assert post_target == "/mcp?mode=probe"
    assert post_hdrs["Accept"] == "application/json, text/event-stream"
    assert post_hdrs["Content-Type"] == "application/json"
    assert post_hdrs["Connection"] == "close"
    parsed_req = json.loads((post_body or b"{}").decode("utf-8"))
    assert parsed_req["method"] == "initialize"
    assert parsed_req["params"]["protocolVersion"] == "2025-03-26"

    assert (del_conn.host, del_conn.port, del_conn.timeout) == ("127.0.0.1", 9010, 1.5)
    assert del_conn.closed is True
    assert del_resp.closed is True
    del_method, del_target, _del_body, del_hdrs = del_conn.requests_made[0]
    assert del_method == "DELETE"
    assert del_target == "/mcp?mode=probe"
    assert del_hdrs == {"Mcp-Session-Id": "neo-stdlib-secret-sid", "Connection": "close"}

    # Ordering proof: POST connection closed BEFORE DELETE connection opened.
    event_seq = [e["event"] for e in events]
    assert event_seq == ["open", "request", "close", "open", "request", "close"]


def test_cc711_stdlib_http_client_plain_json_readline_fallback_and_delete_error_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stdlib transport handles application/json, readline()-only streams, and best-effort DELETE errors."""
    import http.client
    import sys

    monkeypatch.setitem(sys.modules, "requests", None)

    # 1) Plain application/json + DELETE raises RemoteDisconnected -> still healthy, all handles closed.
    json_payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "browseros-neo", "version": "0.0.88"},
            },
        }
    ).encode("utf-8")
    post_resp = _FakeStdlibHttpResponse(
        status=200,
        headers={"content-type": "application/json", "mcp-session-id": "sid-json-1"},
        body=json_payload,
    )
    conns: list[_FakeStdlibHttpConnection] = []
    queue: list[object] = [post_resp, http.client.RemoteDisconnected("closed")]

    def factory_json(host: str, port: int, timeout: float | None = None):
        c = _FakeStdlibHttpConnection(host, port, timeout=timeout, response_or_exc=queue.pop(0))
        conns.append(c)
        return c

    res = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", connection_factory=factory_json)
    assert res["mcp_alive"] is True
    assert res["priming_frames_ignored"] == 0
    assert res["session_cleanup_attempted"] is True
    assert "sid-json-1" not in json.dumps(res)
    assert all(c.closed for c in conns)
    assert post_resp.closed is True

    # 2) readline()-only response stub (no read1) still parses priming frames + JSON-RPC reply cleanly.
    sse_resp = _FakeStdlibHttpResponse(
        status=200,
        headers={"Content-Type": "text/event-stream"},
        chunks=[
            b"data:\n\n",
            b"data: " + json_payload + b"\n\n",
        ],
        use_read1=False,
    )
    rl_conn_box: list[_FakeStdlibHttpConnection] = []

    def factory_rl(host: str, port: int, timeout: float | None = None):
        c = _FakeStdlibHttpConnection(host, port, timeout=timeout, response_or_exc=sse_resp)
        rl_conn_box.append(c)
        return c

    res_rl = keepalive.probe_neo_mcp_sse("http://localhost:9010/mcp", connection_factory=factory_rl)
    assert res_rl["mcp_alive"] is True
    assert res_rl["priming_frames_ignored"] == 1
    assert res_rl["server_version"] == "0.0.88"
    assert rl_conn_box[0].closed is True
    assert sse_resp.closed is True


def test_cc711_stdlib_http_client_errors_timeouts_bounds_and_hold_cdp_alive(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Stdlib transport enforces timeouts, bounds, safe error codes, and HOLD_CDP_ALIVE_NEVER_KILL_CHROME."""
    import http.client
    import sys

    monkeypatch.setitem(sys.modules, "requests", None)

    # 1) ConnectionRefusedError -> safe error classification, zero ModuleNotFoundError, conn closed.
    refused_conns: list[_FakeStdlibHttpConnection] = []

    def factory_refused(host: str, port: int, timeout: float | None = None):
        c = _FakeStdlibHttpConnection(host, port, timeout=timeout, response_or_exc=ConnectionRefusedError("refused"))
        refused_conns.append(c)
        return c

    res_refused = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", connection_factory=factory_refused)
    assert res_refused["mcp_alive"] is False
    assert res_refused["error"] == "NEO_ENDPOINT_CONNECTIONREFUSEDERROR"
    assert refused_conns[0].closed is True

    # 2) Socket TimeoutError during getresponse() -> NEO_ENDPOINT_TIMEOUTERROR, conn closed.
    to_conns: list[_FakeStdlibHttpConnection] = []

    def factory_timeout(host: str, port: int, timeout: float | None = None):
        c = _FakeStdlibHttpConnection(
            host,
            port,
            timeout=timeout,
            response_or_exc=lambda: (_ for _ in ()).throw(TimeoutError("timed out")),
        )
        to_conns.append(c)
        return c

    res_to = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", timeout_seconds=1.5, connection_factory=factory_timeout)
    assert res_to["mcp_alive"] is False
    assert res_to["error"] == "NEO_ENDPOINT_TIMEOUTERROR"
    assert to_conns[0].closed is True

    # 3) Synthetic monotonic clock crossing deadline mid-SSE -> NEO_SSE_DEADLINE_EXCEEDED.
    clock = iter([100.0, 100.5, 102.5, 103.0])
    slow_resp = _FakeStdlibHttpResponse(
        status=200,
        headers={"Content-Type": "text/event-stream"},
        chunks=[b": keepalive\n", b": still-waiting\n"],
    )
    res_deadline = keepalive.probe_neo_mcp_sse(
        "http://127.0.0.1:9010/mcp",
        timeout_seconds=2.0,
        connection_factory=lambda h, p, timeout=None: _FakeStdlibHttpConnection(h, p, timeout=timeout, response_or_exc=slow_resp),
        mono_fn=lambda: next(clock, 200.0),
    )
    assert res_deadline["mcp_alive"] is False
    assert res_deadline["error"] == "NEO_SSE_DEADLINE_EXCEEDED"
    assert slow_resp.closed is True

    # 4) HTTP 503 with Mcp-Session-Id -> NEO_MCP_HTTP_503 and still runs best-effort DELETE after closing POST.
    err_503 = _FakeStdlibHttpResponse(status=503, headers={"Mcp-Session-Id": "sid-503"})
    del_503 = _FakeStdlibHttpResponse(status=204)
    q503: list[object] = [err_503, del_503]
    conns_503: list[_FakeStdlibHttpConnection] = []

    def factory_503(host: str, port: int, timeout: float | None = None):
        c = _FakeStdlibHttpConnection(host, port, timeout=timeout, response_or_exc=q503.pop(0))
        conns_503.append(c)
        return c

    res_503 = keepalive.probe_neo_mcp_sse("http://127.0.0.1:9010/mcp", connection_factory=factory_503)
    assert res_503["mcp_alive"] is False
    assert res_503["http_status"] == 503
    assert res_503["error"] == "NEO_MCP_HTTP_503"
    assert len(conns_503) == 2
    assert conns_503[1].requests_made[0][0] == "DELETE"
    assert all(c.closed for c in conns_503)

    # 5) Bounded SSE line and JSON response size limits fail closed.
    monkeypatch.setattr(keepalive, "_MAX_NEO_SSE_LINE_BYTES", 64)
    big_sse = _FakeStdlibHttpResponse(
        status=200,
        headers={"Content-Type": "text/event-stream"},
        chunks=[b"data: " + (b"x" * 100) + b"\n"],
    )
    res_big_sse = keepalive.probe_neo_mcp_sse(
        "http://127.0.0.1:9010/mcp",
        connection_factory=lambda h, p, timeout=None: _FakeStdlibHttpConnection(h, p, timeout=timeout, response_or_exc=big_sse),
    )
    assert res_big_sse["mcp_alive"] is False
    assert res_big_sse["error"] == "NEO_SSE_LINE_TOO_LARGE"
    assert big_sse.closed is True

    monkeypatch.setattr(keepalive, "_MAX_NEO_JSON_BYTES", 32)
    big_json = _FakeStdlibHttpResponse(
        status=200,
        headers={"Content-Type": "application/json"},
        body=b'{"jsonrpc":"2.0","padding":"' + (b"a" * 64) + b'"}',
    )
    res_big_json = keepalive.probe_neo_mcp_sse(
        "http://127.0.0.1:9010/mcp",
        connection_factory=lambda h, p, timeout=None: _FakeStdlibHttpConnection(h, p, timeout=timeout, response_or_exc=big_json),
    )
    assert res_big_json["mcp_alive"] is False
    assert res_big_json["error"] == "NEO_MCP_RESPONSE_TOO_LARGE"
    assert big_json.closed is True

    # 6) End-to-end recover_browseros_neo with live default probe_neo_mcp_sse hitting BadStatusLine
    #    while CDP is alive -> DEGRADED_MCP_CDP_ALIVE + HOLD_CDP_ALIVE_NEVER_KILL_CHROME.
    exe, user_data, cfg = _fake_neo_install(tmp_path)
    monkeypatch.setattr(
        http.client,
        "HTTPConnection",
        lambda h, p, timeout=None: _FakeStdlibHttpConnection(
            h, p, timeout=timeout, response_or_exc=http.client.BadStatusLine("bad")
        ),
    )
    recovery = keepalive.recover_browseros_neo(
        dry_run=False,
        keepalive_lock_path=tmp_path / "neo.lock",
        stop_path=tmp_path / "STOP_NEO",
        browser_exe=exe,
        user_data_dir=user_data,
        config_path=cfg,
        cdp_probe=lambda p: {"cdp_alive": True, "cdp_port": p, "browser": "Chrome/155.0.8317.26"},
        process_probe=lambda: [{"pid": 35688, "name": "chrome.exe"}],
        spawner=lambda _cmd, _cwd: pytest.fail("must NEVER kill or spawn Chrome when CDP responds"),
        now_fn=_fixed_now,
    )
    assert recovery["health"]["state"] == "DEGRADED_MCP_CDP_ALIVE"
    assert recovery["health"]["mcp"]["error"] == "NEO_ENDPOINT_BADSTATUSLINE"
    assert recovery["action"] == "HOLD_CDP_ALIVE_NEVER_KILL_CHROME"
    assert recovery["chrome_kill_performed"] is False
    assert recovery["launched"] is False
