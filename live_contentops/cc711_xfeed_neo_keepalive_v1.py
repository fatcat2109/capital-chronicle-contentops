"""CC-711 ContentOps resilience helpers: X_List_Feed PT15M keepalive and BrowserOS Neo health probe.

Strictly dry-run by default: zero live Task Scheduler edits, zero public posts, and zero
forced termination of active Chrome processes when CDP responds.

Design invariants:
1. X_List_Feed keepalive uses non-blocking OS byte locks (msvcrt on Windows, fcntl on POSIX)
   on both its own keepalive mutex and the canonical runner lock (`runner_v1.lock`), honors
   the operator `STOP` file, and respects CC-785 (`d6c0b69a`) `CDP_PROBE_STARVED`,
   `RUNNING_WITHOUT_CDP`, and `PORT_OWNER_UNPROVEN` fail-closed guards so a slow or loaded
   Chrome 9222 never triggers a duplicate Chrome launch or kill.
2. BrowserOS Neo health & recovery probe checks loopback-only CDP `/json/version` and MCP
   Streamable HTTP (`text/event-stream` / `application/json`) JSON-RPC `initialize`, explicitly
   ignoring `browseros-neo v0.0.88` blank SSE priming frames (`data:` / `data: ` / comments).
   Never kills an active Chrome process if CDP responds (or if MCP responds / BrowserClaw
   process is alive and starved); recovery is cold-start-only when process and ports are down.
3. Task Scheduler XML templates default to `<Enabled>false</Enabled>`, `UserId=JP`,
   `LogonType=InteractiveToken`, `MultipleInstancesPolicy=IgnoreNew`, and `PT15M` repetition.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit

SCHEMA_VERSION = "contentops.cc711_keepalive.v1"

# Canonical ContentOps paths (read-only defaults; tests always pass tmp_path overrides).
DEFAULT_REPO_ROOT = Path(r"A:\Capital Chronicle\ContentOps")
DEFAULT_RUNTIME_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
DEFAULT_PYTHONW = DEFAULT_RUNTIME_ROOT / "v1-runtime" / "venv" / "Scripts" / "pythonw.exe"
DEFAULT_X_FEED_DIR = DEFAULT_RUNTIME_ROOT / "x_list_feed"
DEFAULT_X_FEED_LOCK = DEFAULT_X_FEED_DIR / "runner_v1.lock"
DEFAULT_X_FEED_KEEPALIVE_LOCK = DEFAULT_X_FEED_DIR / "keepalive_cc711_v1.lock"
DEFAULT_X_FEED_STOP = DEFAULT_X_FEED_DIR / "STOP"
DEFAULT_X_FEED_JSON = DEFAULT_X_FEED_DIR / "x_list_feed_v1.json"
DEFAULT_X_FEED_CDP_PORT = 9222

DEFAULT_NEO_KEEPALIVE_LOCK = DEFAULT_RUNTIME_ROOT / "control" / "neo_keepalive_cc711_v1.lock"
DEFAULT_NEO_STOP = DEFAULT_RUNTIME_ROOT / "control" / "STOP_NEO_KEEPALIVE"
DEFAULT_NEO_CDP_PORT = 9110
DEFAULT_NEO_MCP_PORT = 9010
DEFAULT_NEO_SERVER_PORT = 9210
DEFAULT_NEO_MCP_PATH = "/mcp"
DEFAULT_NEO_PROTOCOL_VERSION = "2025-03-26"

# CC-785 (d6c0b69a) compatible CDP process states.
STATE_READY = "READY"
STATE_CDP_PROBE_STARVED = "CDP_PROBE_STARVED"
STATE_RUNNING_WITHOUT_CDP = "RUNNING_WITHOUT_CDP"
STATE_PORT_OWNER_UNPROVEN = "PORT_OWNER_UNPROVEN"
STATE_UNAVAILABLE = "UNAVAILABLE"

# Non-launching fail-closed CDP states (never spawn duplicate Chrome or kill active Chrome).
NON_LAUNCHING_CDP_STATES = frozenset(
    {STATE_CDP_PROBE_STARVED, STATE_RUNNING_WITHOUT_CDP, STATE_PORT_OWNER_UNPROVEN}
)

# Task Scheduler defaults (CC-711).
TASK_XML_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
DEFAULT_TASK_USER_ID = "JP"
DEFAULT_TASK_LOGON_TYPE = "InteractiveToken"
DEFAULT_TASK_REPEAT_INTERVAL = "PT15M"
DEFAULT_TASK_START_BOUNDARY = "2026-11-25T00:00:00+07:00"
X_FEED_TASK_NAME = "CapitalChronicle_ContentOps_X_List_Feed"
NEO_HEALTH_TASK_NAME = "CapitalChronicle_ContentOps_BrowserOS_Neo_Health"

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_DETACHED_FLAGS = (
    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    | getattr(subprocess, "DETACHED_PROCESS", 0)
    | getattr(subprocess, "CREATE_NO_WINDOW", 0)
)


def _utc_now(now_fn: Callable[[], datetime] | None = None) -> str:
    moment = (now_fn or (lambda: datetime.now(timezone.utc)))().astimezone(timezone.utc)
    return moment.isoformat()


def _require_loopback_http(url: str) -> str:
    parsed = urlsplit(str(url))
    if parsed.scheme != "http" or parsed.hostname not in _LOOPBACK_HOSTS:
        raise ValueError("NEO_LOCAL_ENDPOINT_REQUIRED")
    if parsed.username or parsed.password:
        raise ValueError("NEO_ENDPOINT_CREDENTIALS_FORBIDDEN")
    return str(url)


def _acquire_os_lock(path: Path) -> Any | None:
    """Acquire a non-blocking exclusive 1-byte OS lock (msvcrt on Windows, fcntl on POSIX)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+b")
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def _release_os_lock(handle: Any | None) -> None:
    if handle is None:
        return
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        try:
            handle.close()
        except OSError:
            pass


@contextmanager
def os_mutex(path: Path):
    """Context manager yielding True if non-blocking OS lock acquired, else False."""
    handle = _acquire_os_lock(path)
    try:
        yield handle is not None
    finally:
        _release_os_lock(handle)


def probe_os_lock_held(path: Path) -> bool:
    """Return True if another process holds the exclusive byte lock at ``path``.

    Never creates ``path`` when absent.
    """
    path = Path(path)
    if not path.is_file():
        return False
    try:
        handle = open(path, "r+b")
    except OSError:
        return True
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return True
    _release_os_lock(handle)
    return False


def _default_port_listener_pid(port: int) -> int | None:
    """Native Windows TCP listener PID lookup (iphlpapi, milliseconds, zero WMI)."""
    if os.name != "nt":
        return None
    try:
        from live_contentops import ingestion_bootstrap_v1 as bootstrap

        pid = bootstrap._native_listener_pid(int(port))
        return int(pid) if pid else None
    except Exception:  # noqa: BLE001
        return None


def _default_cdp_listener_probe(cdp_port: int) -> dict[str, Any] | None:
    """Native Windows listener + process identity lookup for starved-CDP classification."""
    if os.name != "nt":
        return None
    try:
        from live_contentops import ingestion_bootstrap_v1 as bootstrap

        pid = bootstrap._native_listener_pid(int(cdp_port))
        if not pid:
            return None
        identity = bootstrap._native_process_identity(pid)
        return dict(identity) if isinstance(identity, Mapping) else None
    except Exception:  # noqa: BLE001
        return None


def _has_cdp_port_flag(command_line: str, cdp_port: int) -> bool:
    if not command_line:
        return False
    lowered = command_line.lower().replace('"', "")
    return f"--remote-debugging-port={int(cdp_port)}" in lowered


def _is_canonical_xfeed_chrome(command_line: str, profile_marker: str = "capitalchroniclebot") -> bool:
    if not command_line:
        return False
    lowered = command_line.lower().replace('"', "")
    return "chrome" in lowered and profile_marker.lower() in lowered


def probe_x_feed_cdp_state(
    *,
    cdp_port: int = DEFAULT_X_FEED_CDP_PORT,
    bootstrap_state_fn: Callable[..., Mapping[str, Any]] | None = None,
    listener_probe: Callable[[int], Mapping[str, Any] | None] | None = None,
    chrome_process_probe: Callable[[], list[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Classify canonical X-list ingestion Chrome CDP state, honoring d6c0b69a's starved guard.

    Works seamlessly both before and after d6c0b69a is merged into ingestion_bootstrap_v1:
    - If ingestion_bootstrap_v1 already returns CDP_PROBE_STARVED, preserves it verbatim.
    - When ``bootstrap_state_fn`` is not mocked and ``listener_probe`` is omitted, wires
      ``_default_cdp_listener_probe`` (native iphlpapi + Win32 identity) so starved canonical
      Chrome 9222 upgrades to STATE_CDP_PROBE_STARVED on pre-d6c0b69a hosts as well.
    """
    if bootstrap_state_fn is None:
        from live_contentops import ingestion_bootstrap_v1 as bootstrap

        raw = dict(bootstrap.ingestion_process_state(cdp_port=cdp_port))
    else:
        raw = dict(bootstrap_state_fn(cdp_port=cdp_port))

    state = str(raw.get("state") or STATE_UNAVAILABLE)
    if state in {STATE_READY, STATE_CDP_PROBE_STARVED, STATE_PORT_OWNER_UNPROVEN}:
        return raw

    # Starved-CDP double-check (handles ce53947a8 pre-d6c0b69a in production and injected tests).
    effective_listener_probe = (
        listener_probe if listener_probe is not None else (_default_cdp_listener_probe if bootstrap_state_fn is None else None)
    )
    if effective_listener_probe is not None:
        native = effective_listener_probe(cdp_port)
        if isinstance(native, Mapping) and native.get("cmd") is not None:
            if _is_canonical_xfeed_chrome(str(native["cmd"])):
                return {
                    "state": STATE_CDP_PROBE_STARVED,
                    "detail": "CANONICAL_CDP_9222_LISTENING_PROBE_TIMED_OUT",
                    "pid": native.get("pid"),
                }
            return {
                "state": STATE_PORT_OWNER_UNPROVEN,
                "detail": "PORT_9222_OWNED_BY_NON_CANONICAL_PROCESS",
                "pid": native.get("pid"),
            }

    if chrome_process_probe is not None:
        for entry in chrome_process_probe():
            if not isinstance(entry, Mapping):
                continue
            cmd = str(entry.get("cmd") or "")
            pid = entry.get("pid")
            if pid is not None and _is_canonical_xfeed_chrome(cmd) and _has_cdp_port_flag(cmd, cdp_port):
                return {
                    "state": STATE_CDP_PROBE_STARVED,
                    "detail": "CANONICAL_CDP_9222_ACTIVE_PROBE_TIMED_OUT",
                    "pid": pid,
                }

    return raw


def status_x_list_feed(
    *,
    lock_path: Path = DEFAULT_X_FEED_LOCK,
    stop_path: Path = DEFAULT_X_FEED_STOP,
    feed_path: Path = DEFAULT_X_FEED_JSON,
    cdp_port: int = DEFAULT_X_FEED_CDP_PORT,
    runner_lock_probe: Callable[[Path], bool] | None = None,
    cdp_state_probe: Callable[..., Mapping[str, Any]] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Strictly read-only X_List_Feed status check (zero lock file creation or disk writes)."""
    moment_fn = now_fn or (lambda: datetime.now(timezone.utc))
    now_dt = moment_fn().astimezone(timezone.utc)
    stop_present = Path(stop_path).exists()
    check_runner = runner_lock_probe or probe_os_lock_held
    runner_alive = bool(check_runner(Path(lock_path)))
    feed_summary = _read_feed_summary(Path(feed_path), now_dt)
    cdp_info = None
    if not stop_present and not runner_alive:
        probe_cdp_fn = cdp_state_probe or (lambda port: probe_x_feed_cdp_state(cdp_port=port))
        cdp_info = dict(probe_cdp_fn(cdp_port))
    state = (
        "STOP_FILE_PRESENT"
        if stop_present
        else ("RUNNING" if runner_alive else str((cdp_info or {}).get("state") or STATE_UNAVAILABLE))
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "component": "x_list_feed_status",
        "checked_at_utc": now_dt.isoformat(),
        "read_only": True,
        "dry_run": True,
        "public_write_performed": False,
        "live_task_mutated": False,
        "stop_present": stop_present,
        "runner_alive": runner_alive,
        "state": state,
        "cdp": cdp_info,
        "feed": feed_summary,
    }


def _read_feed_summary(feed_path: Path, now_dt: datetime) -> dict[str, Any]:
    path = Path(feed_path)
    if not path.is_file():
        return {"present": False, "age_seconds": None, "health_state": None}
    try:
        raw = path.read_bytes()
        # Only parse the compact header object (before `"rows": [` when present) or full JSON.
        head = raw.split(b', "rows": [', 1)[0]
        parsed = json.loads(head + b"}") if b', "rows": [' in raw else json.loads(raw)
        generated = parsed.get("generated_at_utc")
        age = None
        if isinstance(generated, str) and generated:
            gen_dt = datetime.fromisoformat(generated.replace("Z", "+00:00")).astimezone(timezone.utc)
            age = round(max(0.0, (now_dt - gen_dt).total_seconds()), 1)
        health = parsed.get("health") if isinstance(parsed.get("health"), Mapping) else {}
        return {
            "present": True,
            "generated_at_utc": generated,
            "age_seconds": age,
            "health_state": health.get("state"),
            "failure_streak": health.get("failure_streak"),
        }
    except (OSError, ValueError, TypeError):
        return {"present": True, "age_seconds": None, "health_state": "UNREADABLE"}


def _default_spawn_detached(command: list[str], cwd: Path) -> int:
    proc = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_DETACHED_FLAGS if os.name == "nt" else 0,
        close_fds=True,
    )
    return int(proc.pid)


def keepalive_x_list_feed(
    *,
    dry_run: bool = True,
    lock_path: Path = DEFAULT_X_FEED_LOCK,
    keepalive_lock_path: Path = DEFAULT_X_FEED_KEEPALIVE_LOCK,
    stop_path: Path = DEFAULT_X_FEED_STOP,
    feed_path: Path = DEFAULT_X_FEED_JSON,
    repo_root: Path = DEFAULT_REPO_ROOT,
    python_exe: Path = DEFAULT_PYTHONW,
    cdp_port: int = DEFAULT_X_FEED_CDP_PORT,
    runner_lock_probe: Callable[[Path], bool] | None = None,
    cdp_state_probe: Callable[..., Mapping[str, Any]] | None = None,
    spawner: Callable[[list[str], Path], int] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Deterministic, OS-lock-guarded PT15M keepalive for CapitalChronicle_ContentOps_X_List_Feed.

    Defaults to ``dry_run=True`` (never launches anything unless ``dry_run=False``).
    Never launches duplicate runners, never launches duplicate Chrome when CDP is starved or
    non-canonical, and never kills any running Chrome process.
    """
    moment_fn = now_fn or (lambda: datetime.now(timezone.utc))
    now_dt = moment_fn().astimezone(timezone.utc)
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "component": "x_list_feed_keepalive",
        "checked_at_utc": now_dt.isoformat(),
        "dry_run": bool(dry_run),
        "public_write_performed": False,
        "live_task_mutated": False,
        "chrome_kill_performed": False,
        "launched": False,
        "would_launch": False,
        "pid": None,
    }

    with os_mutex(keepalive_lock_path) as acquired:
        if not acquired:
            return {
                **base,
                "action": "SKIPPED_KEEPALIVE_LOCK_HELD",
                "reason": "CONCURRENT_KEEPALIVE_IN_PROGRESS",
            }

        if Path(stop_path).exists():
            return {
                **base,
                "action": "SKIPPED_STOP_FILE_PRESENT",
                "stop_present": True,
                "reason": "OPERATOR_STOP_FILE_ACTIVE",
            }

        check_runner = runner_lock_probe or probe_os_lock_held
        runner_alive = bool(check_runner(Path(lock_path)))
        feed_summary = _read_feed_summary(Path(feed_path), now_dt)
        if runner_alive:
            return {
                **base,
                "action": "ALREADY_RUNNING",
                "runner_alive": True,
                "feed": feed_summary,
                "reason": "RUNNER_OS_LOCK_HELD",
            }

        probe_cdp_fn = cdp_state_probe or (lambda port: probe_x_feed_cdp_state(cdp_port=port))
        cdp_info = dict(probe_cdp_fn(cdp_port))
        cdp_state = str(cdp_info.get("state") or STATE_UNAVAILABLE)

        if cdp_state == STATE_CDP_PROBE_STARVED:
            return {
                **base,
                "action": "HOLD_CDP_PROBE_STARVED",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": "CANONICAL_CDP_9222_PROBE_STARVED_NO_DUPLICATE_LAUNCH",
            }
        if cdp_state == STATE_RUNNING_WITHOUT_CDP:
            return {
                **base,
                "action": "HOLD_RUNNING_WITHOUT_CDP",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222",
            }
        if cdp_state == STATE_PORT_OWNER_UNPROVEN:
            return {
                **base,
                "action": "HOLD_PORT_OWNER_UNPROVEN",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": "PORT_9222_OWNED_BY_NON_CANONICAL_PROCESS",
            }
        if cdp_state not in {STATE_READY, STATE_UNAVAILABLE}:
            return {
                **base,
                "action": "HOLD_UNKNOWN_CDP_STATE",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": f"UNEXPECTED_CDP_STATE:{cdp_state}",
            }

        runner_script = Path(repo_root) / "scripts" / "run_x_list_feed.py"
        if not Path(python_exe).is_file():
            return {
                **base,
                "action": "BLOCKED_PYTHON_MISSING",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": "RUNNER_PYTHON_EXECUTABLE_NOT_FOUND",
            }
        if not runner_script.is_file():
            return {
                **base,
                "action": "BLOCKED_SCRIPT_MISSING",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "reason": "RUNNER_SCRIPT_NOT_FOUND",
            }

        command = [str(python_exe), "-B", str(runner_script)]
        if dry_run:
            return {
                **base,
                "action": "DRY_RUN_WOULD_LAUNCH_RUNNER",
                "runner_alive": False,
                "cdp": cdp_info,
                "feed": feed_summary,
                "would_launch": True,
                "command": command,
                "reason": "RUNNER_NOT_RUNNING_DRY_RUN",
            }

        spawn_fn = spawner or _default_spawn_detached
        pid = spawn_fn(command, Path(repo_root))
        return {
            **base,
            "action": "LAUNCHED_RUNNER",
            "runner_alive": False,
            "cdp": cdp_info,
            "feed": feed_summary,
            "launched": True,
            "would_launch": True,
            "pid": pid,
            "command": command,
            "reason": "RUNNER_STARTED_BY_KEEPALIVE",
        }


# ---------------------------------------------------------------------------
# BrowserOS Neo (BrowserClaw) CDP + SSE MCP health & safe-restart probe
# ---------------------------------------------------------------------------


def default_browseros_paths(env: Mapping[str, str] | None = None) -> dict[str, Path]:
    source = env if env is not None else os.environ
    local_app = Path(source.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    root = local_app / "BrowserClaw"
    return {
        "browser_exe": root / "Application" / "chrome.exe",
        "user_data_dir": root / "User Data",
        "config_path": root / "User Data" / ".browseros" / "config.json",
    }


def load_browseros_ports(
    config_path: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Read non-secret port bindings from BrowserClaw config.json, falling back to canonical defaults."""
    resolved_cfg = Path(config_path) if config_path is not None else default_browseros_paths(env)["config_path"]
    ports = {
        "cdp_port": DEFAULT_NEO_CDP_PORT,
        "mcp_port": DEFAULT_NEO_MCP_PORT,
        "server_port": DEFAULT_NEO_SERVER_PORT,
        "config_found": False,
        "browseros_version": None,
        "chromium_version": None,
    }
    if not resolved_cfg.is_file():
        return ports
    try:
        data = json.loads(resolved_cfg.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            return ports
        raw_ports = data.get("ports") if isinstance(data.get("ports"), Mapping) else {}
        for dst, src in (("cdp_port", "cdp"), ("mcp_port", "proxy"), ("server_port", "server")):
            val = raw_ports.get(src)
            if isinstance(val, int) and not isinstance(val, bool) and 1 <= val <= 65535:
                ports[dst] = val
        inst = data.get("instance") if isinstance(data.get("instance"), Mapping) else {}
        ports["config_found"] = True
        ports["browseros_version"] = inst.get("browseros_version")
        ports["chromium_version"] = inst.get("chromium_version")
    except (OSError, ValueError, TypeError):
        pass
    return ports


def parse_mcp_sse_response(
    lines: Iterable[str | bytes],
    *,
    request_id: int,
    deadline_mono: float | None = None,
    mono_fn: Callable[[], float] = time.monotonic,
    max_lines: int = 2048,
) -> dict[str, Any]:
    """Parse an MCP Streamable HTTP SSE stream, tolerating browseros-neo v0.0.88 blank priming frames.

    W3C SSE + browseros-neo v0.0.88 semantics:
    - Blank lines (`""`), comment/keepalive lines (`: ...`), `event:` / `id:` / `retry:` metadata,
      and **blank priming frames (`data:` or `data: ` with empty payload)** are ignored and counted
      in `priming_frames_ignored` without raising JSONDecodeError.
    - Consecutive non-empty `data:` lines within one event are buffered and decoded either
      immediately (single-line JSON-RPC object) or on event-boundary blank line (multi-line JSON).
    - Stops as soon as the exact matching JSON-RPC `id == request_id` arrives.
    """
    priming_frames = 0
    comment_lines = 0
    data_buf: list[str] = []
    seen_lines = 0

    def _try_decode(payload_text: str) -> dict[str, Any] | None:
        text = payload_text.strip()
        if not text:
            return None
        parsed = json.loads(text)
        if isinstance(parsed, dict) and parsed.get("id") == request_id:
            return parsed
        return None

    for raw in lines:
        if deadline_mono is not None and mono_fn() > deadline_mono:
            raise TimeoutError("NEO_SSE_DEADLINE_EXCEEDED")
        seen_lines += 1
        if seen_lines > max_lines:
            raise ValueError("NEO_SSE_LINE_LIMIT_EXCEEDED")
        line = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
        line = line.rstrip("\r\n")

        if line == "":
            if data_buf:
                joined = "\n".join(data_buf)
                data_buf.clear()
                try:
                    matched = _try_decode(joined)
                except ValueError as exc:
                    raise ValueError("NEO_SSE_INVALID_JSON_PAYLOAD") from exc
                if matched is not None:
                    return {
                        "message": matched,
                        "priming_frames_ignored": priming_frames,
                        "comment_lines_ignored": comment_lines,
                    }
            continue

        if line.startswith(":"):
            comment_lines += 1
            continue

        if line.startswith("data:"):
            payload = line[5:]
            if payload.startswith(" "):
                payload = payload[1:]
            if not payload.strip():
                # browseros-neo v0.0.88 blank SSE priming frame (`data:` or `data: `).
                priming_frames += 1
                continue
            data_buf.append(payload)
            # Fast-path single-line JSON-RPC reply so open SSE streams do not block waiting for a trailing blank line.
            if len(data_buf) == 1:
                try:
                    matched = _try_decode(payload)
                except ValueError:
                    matched = None
                if matched is not None:
                    data_buf.clear()
                    return {
                        "message": matched,
                        "priming_frames_ignored": priming_frames,
                        "comment_lines_ignored": comment_lines,
                    }
            continue

        # Standard SSE event framing metadata (`event:`, `id:`, `retry:`) - benign.
        if line.startswith(("event:", "id:", "retry:")):
            continue

    if data_buf:
        joined = "\n".join(data_buf)
        data_buf.clear()
        try:
            matched = _try_decode(joined)
        except ValueError as exc:
            raise ValueError("NEO_SSE_INVALID_JSON_PAYLOAD") from exc
        if matched is not None:
            return {
                "message": matched,
                "priming_frames_ignored": priming_frames,
                "comment_lines_ignored": comment_lines,
            }

    raise ValueError("NEO_SSE_REPLY_MISSING")


def probe_cdp_version(
    cdp_port: int,
    *,
    timeout_seconds: float = 3.0,
    retry_timeout_seconds: float = 5.0,
    http_open: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Read-only loopback CDP `/json/version` probe with proxy bypass and one bounded retry."""
    url = _require_loopback_http(f"http://127.0.0.1:{int(cdp_port)}/json/version")
    opener = http_open or urllib.request.build_opener(urllib.request.ProxyHandler({})).open
    last_error = None
    attempts = 0
    for timeout in (timeout_seconds, retry_timeout_seconds):
        attempts += 1
        try:
            with opener(url, timeout=timeout) as resp:
                raw = resp.read(65536)
            data = json.loads(raw.decode("utf-8", errors="replace"))
            if isinstance(data, Mapping) and (data.get("Browser") or data.get("webSocketDebuggerUrl")):
                return {
                    "cdp_alive": True,
                    "cdp_port": int(cdp_port),
                    "attempts": attempts,
                    "browser": str(data.get("Browser") or ""),
                    "protocol_version": str(data.get("Protocol-Version") or ""),
                    "error": None,
                }
            last_error = "CDP_VERSION_PAYLOAD_INVALID"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{type(exc).__name__}"
    return {
        "cdp_alive": False,
        "cdp_port": int(cdp_port),
        "attempts": attempts,
        "browser": None,
        "protocol_version": None,
        "error": last_error or "CDP_UNAVAILABLE",
    }


def probe_neo_mcp_sse(
    endpoint: str,
    *,
    timeout_seconds: float = 8.0,
    http_post: Callable[..., Any] | None = None,
    http_delete: Callable[..., Any] | None = None,
    mono_fn: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Read-only MCP JSON-RPC `initialize` probe supporting Streamable HTTP SSE priming frames.

    Bypasses proxies for loopback HTTP, performs zero page actions or tab opens, cleans up
    any allocated `Mcp-Session-Id` via best-effort `DELETE` in `finally`, and never logs
    session tokens or response bodies.
    """
    _require_loopback_http(endpoint)
    request_id = 1
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": DEFAULT_NEO_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "cc711-neo-health-probe", "version": "1.0"},
        },
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    owned_session = None
    response = None
    session_id: str | None = None
    session_cleanup_attempted = False
    try:
        if http_post is None:
            import requests

            owned_session = requests.Session()
            owned_session.trust_env = False
            response = owned_session.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=(min(3.0, timeout_seconds), timeout_seconds),
                stream=True,
            )
        else:
            response = http_post(endpoint, json=payload, headers=headers, timeout=timeout_seconds, stream=True)

        status_code = int(getattr(response, "status_code", 0))
        resp_headers = getattr(response, "headers", {}) or {}
        raw_sid = resp_headers.get("Mcp-Session-Id") or resp_headers.get("mcp-session-id")
        if isinstance(raw_sid, str) and raw_sid.strip():
            session_id = raw_sid.strip()

        if status_code < 200 or status_code >= 300:
            return {
                "mcp_alive": False,
                "endpoint": endpoint,
                "http_status": status_code,
                "error": f"NEO_MCP_HTTP_{status_code}",
                "priming_frames_ignored": 0,
            }

        content_type = str(resp_headers.get("Content-Type") or resp_headers.get("content-type") or "")
        session_present = bool(session_id)
        priming_ignored = 0

        if "text/event-stream" in content_type.lower():
            deadline = mono_fn() + max(1.0, float(timeout_seconds))
            parsed = parse_mcp_sse_response(
                response.iter_lines(chunk_size=8192, decode_unicode=True),
                request_id=request_id,
                deadline_mono=deadline,
                mono_fn=mono_fn,
            )
            message = parsed["message"]
            priming_ignored = parsed["priming_frames_ignored"]
        else:
            message = response.json()

        if not isinstance(message, Mapping) or message.get("error"):
            return {
                "mcp_alive": False,
                "endpoint": endpoint,
                "http_status": status_code,
                "content_type": content_type,
                "session_header_present": session_present,
                "priming_frames_ignored": priming_ignored,
                "error": "NEO_MCP_JSONRPC_ERROR",
            }
        result = message.get("result")
        if not isinstance(result, Mapping) or not result.get("protocolVersion"):
            return {
                "mcp_alive": False,
                "endpoint": endpoint,
                "http_status": status_code,
                "content_type": content_type,
                "session_header_present": session_present,
                "priming_frames_ignored": priming_ignored,
                "error": "NEO_MCP_RESULT_INVALID",
            }
        return {
            "mcp_alive": True,
            "endpoint": endpoint,
            "http_status": status_code,
            "content_type": content_type,
            "protocol_version": str(result.get("protocolVersion")),
            "server_name": str((result.get("serverInfo") or {}).get("name") or ""),
            "server_version": str((result.get("serverInfo") or {}).get("version") or ""),
            "session_header_present": session_present,
            "session_cleanup_attempted": session_present and (http_delete is not None or owned_session is not None),
            "priming_frames_ignored": priming_ignored,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - fixed safe classification only
        code = str(exc) if isinstance(exc, (ValueError, TimeoutError)) and str(exc).startswith("NEO_") else (
            "NEO_ENDPOINT_" + type(exc).__name__.upper()
        )
        return {
            "mcp_alive": False,
            "endpoint": endpoint,
            "http_status": None,
            "error": code,
            "priming_frames_ignored": 0,
        }
    finally:
        close_fn = getattr(response, "close", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception:  # noqa: BLE001
                pass
        if session_id:
            delete_fn = http_delete or (owned_session.delete if owned_session is not None else None)
            if callable(delete_fn):
                session_cleanup_attempted = True
                del_resp = None
                try:
                    del_resp = delete_fn(
                        endpoint,
                        headers={"Mcp-Session-Id": session_id},
                        timeout=(1.5, 2.0),
                    )
                except Exception:  # noqa: BLE001 - best-effort cleanup (405/transport errors ignored)
                    pass
                finally:
                    del_close = getattr(del_resp, "close", None)
                    if callable(del_close):
                        try:
                            del_close()
                        except Exception:  # noqa: BLE001
                            pass
        if owned_session is not None:
            try:
                owned_session.close()
            except Exception:  # noqa: BLE001
                pass
        _ = session_cleanup_attempted


def _default_neo_process_probe(
    *,
    run_fn: Callable[..., Any] | None = None,
    platform_name: str | None = None,
) -> list[dict[str, Any]] | None:
    """Fail-closed Windows process check for active BrowserClaw chrome.exe / server processes.

    Returns:
      - ``list[dict]`` ONLY when PowerShell/CIM succeeded with an explicit ``{"ok": true, "procs": [...]}``
        JSON envelope (including ``[]`` when genuinely zero BrowserClaw processes exist).
      - ``None`` on ANY timeout, OSError, non-zero exit code, empty stdout, malformed JSON,
        or non-Windows host — NEVER collapses a probe failure into ``[]``.
    """
    active_os = platform_name if platform_name is not None else os.name
    if active_os != "nt":
        return None
    script = (
        "$ErrorActionPreference='Stop';"
        "$procs=@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' OR Name='browseros-claw-server.exe'\""
        " | Where-Object { $_.CommandLine -like '*BrowserClaw*' -and $_.CommandLine -notlike '*--type=crashpad-handler*' }"
        " | ForEach-Object { @{ pid = [int]$_.ProcessId; name = [string]$_.Name } });"
        "@{ ok = $true; procs = @($procs) } | ConvertTo-Json -Compress -Depth 3"
    )
    runner = run_fn or subprocess.run
    try:
        completed = runner(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if getattr(completed, "returncode", 1) != 0:
        return None
    stdout = (getattr(completed, "stdout", None) or "").strip()
    if not stdout:
        return None
    try:
        parsed = json.loads(stdout)
    except ValueError:
        return None
    if not isinstance(parsed, dict) or parsed.get("ok") is not True or "procs" not in parsed:
        return None
    raw_procs = parsed["procs"]
    if raw_procs is None:
        return []
    if isinstance(raw_procs, dict):
        return [raw_procs]
    if isinstance(raw_procs, list):
        return [row for row in raw_procs if isinstance(row, dict)]
    return None


def probe_browseros_neo(
    *,
    cdp_port: int | None = None,
    mcp_endpoint: str | None = None,
    config_path: Path | None = None,
    cdp_probe: Callable[[int], Mapping[str, Any]] | None = None,
    mcp_probe: Callable[[str], Mapping[str, Any]] | None = None,
    process_probe: Callable[[], list[Mapping[str, Any]] | None] | None = None,
    listener_pid_probe: Callable[[int], int | None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Strictly read-only BrowserOS Neo CDP + MCP SSE + listener + fail-closed process probe."""
    ports = load_browseros_ports(config_path)
    resolved_cdp_port = int(cdp_port if cdp_port is not None else ports["cdp_port"])
    resolved_mcp_url = _require_loopback_http(
        mcp_endpoint or f"http://127.0.0.1:{int(ports['mcp_port'])}{DEFAULT_NEO_MCP_PATH}"
    )
    resolved_mcp_port = urlsplit(resolved_mcp_url).port or int(ports["mcp_port"])

    cdp = dict((cdp_probe or probe_cdp_version)(resolved_cdp_port))
    mcp = dict((mcp_probe or probe_neo_mcp_sse)(resolved_mcp_url))

    # Native TCP listener check (zero WMI) runs in production (when process_probe is not mocked)
    # or whenever explicitly injected via listener_pid_probe.
    effective_listener = (
        listener_pid_probe
        if listener_pid_probe is not None
        else (_default_port_listener_pid if process_probe is None else None)
    )
    listener_pids: dict[str, int] = {}
    if effective_listener is not None:
        for label, port_num in (("cdp", resolved_cdp_port), ("mcp", int(resolved_mcp_port))):
            try:
                pid = effective_listener(port_num)
            except Exception:  # noqa: BLE001
                pid = None
            if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
                listener_pids[label] = pid

    process_probe_ok = False
    procs: list[Mapping[str, Any]] = []
    try:
        raw_procs = (process_probe or _default_neo_process_probe)()
        if isinstance(raw_procs, (list, tuple)):
            process_probe_ok = True
            procs = list(raw_procs)
    except Exception:  # noqa: BLE001 - fail closed as PROCESS_PROBE_UNPROVEN
        process_probe_ok = False
        procs = []

    cdp_alive = bool(cdp.get("cdp_alive"))
    mcp_alive = bool(mcp.get("mcp_alive"))
    listener_alive = bool(listener_pids)
    process_alive = (process_probe_ok and len(procs) > 0) or listener_alive

    if cdp_alive and mcp_alive:
        state = "HEALTHY"
    elif cdp_alive and not mcp_alive:
        state = "DEGRADED_MCP_CDP_ALIVE"
    elif not cdp_alive and mcp_alive:
        state = "DEGRADED_CDP_MCP_ALIVE"
    elif process_alive:
        state = "NEO_PROBE_STARVED"
    elif not process_probe_ok:
        state = "PROCESS_PROBE_UNPROVEN"
    else:
        state = "DOWN"

    return {
        "schema_version": SCHEMA_VERSION,
        "component": "browseros_neo_health",
        "checked_at_utc": _utc_now(now_fn),
        "state": state,
        "cdp": cdp,
        "mcp": mcp,
        "process_count": len(procs) if process_probe_ok else None,
        "process_probe_ok": process_probe_ok,
        "process_alive": process_alive,
        "listener_pids": listener_pids,
        "listener_alive": listener_alive,
        "ports": ports,
        "public_write_performed": False,
    }


def recover_browseros_neo(
    *,
    dry_run: bool = True,
    keepalive_lock_path: Path = DEFAULT_NEO_KEEPALIVE_LOCK,
    stop_path: Path = DEFAULT_NEO_STOP,
    browser_exe: Path | None = None,
    user_data_dir: Path | None = None,
    config_path: Path | None = None,
    cdp_port: int | None = None,
    mcp_endpoint: str | None = None,
    cdp_probe: Callable[[int], Mapping[str, Any]] | None = None,
    mcp_probe: Callable[[str], Mapping[str, Any]] | None = None,
    process_probe: Callable[[], list[Mapping[str, Any]] | None] | None = None,
    listener_pid_probe: Callable[[int], int | None] | None = None,
    spawner: Callable[[list[str], Path], int] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Lock-guarded BrowserOS Neo health & safe-restart helper.

    HARD SAFETY INVARIANTS:
    - Defaults to ``dry_run=True`` (never starts any process unless ``dry_run=False``).
    - NEVER kills an active Chrome/BrowserClaw process when CDP responds (or when MCP
      responds or a BrowserClaw process/listener is already alive and transiently starved).
    - Fails closed (`HOLD_PROCESS_PROBE_UNPROVEN`) when CDP & MCP are down and process
      presence cannot be proven (e.g., WMI/PowerShell timeout under load).
    - Recovery is strictly cold-start-only when CDP is down, MCP is down, zero listeners
      are active, AND zero BrowserClaw Chrome/server processes are proven alive, using the
      existing BrowserClaw executable and existing User Data profile (never creates a blank profile).
    """
    defaults = default_browseros_paths()
    exe = Path(browser_exe) if browser_exe is not None else defaults["browser_exe"]
    profile = Path(user_data_dir) if user_data_dir is not None else defaults["user_data_dir"]
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "component": "browseros_neo_recovery",
        "checked_at_utc": _utc_now(now_fn),
        "dry_run": bool(dry_run),
        "public_write_performed": False,
        "live_task_mutated": False,
        "chrome_kill_performed": False,
        "killed_pids": [],
        "launched": False,
        "would_launch": False,
        "pid": None,
    }

    with os_mutex(keepalive_lock_path) as acquired:
        if not acquired:
            return {
                **base,
                "action": "SKIPPED_KEEPALIVE_LOCK_HELD",
                "reason": "CONCURRENT_NEO_KEEPALIVE_IN_PROGRESS",
            }

        if Path(stop_path).exists():
            return {
                **base,
                "action": "SKIPPED_STOP_FILE_PRESENT",
                "stop_present": True,
                "reason": "OPERATOR_STOP_FILE_ACTIVE",
            }

        health = probe_browseros_neo(
            cdp_port=cdp_port,
            mcp_endpoint=mcp_endpoint,
            config_path=config_path,
            cdp_probe=cdp_probe,
            mcp_probe=mcp_probe,
            process_probe=process_probe,
            listener_pid_probe=listener_pid_probe,
            now_fn=now_fn,
        )
        state = health["state"]

        if state == "HEALTHY":
            return {
                **base,
                "action": "NO_ACTION_HEALTHY",
                "health": health,
                "reason": "CDP_AND_MCP_SSE_HEALTHY",
            }
        if state == "DEGRADED_MCP_CDP_ALIVE":
            return {
                **base,
                "action": "HOLD_CDP_ALIVE_NEVER_KILL_CHROME",
                "health": health,
                "reason": "CDP_RESPONDS_REFUSE_CHROME_KILL",
            }
        if state == "DEGRADED_CDP_MCP_ALIVE":
            return {
                **base,
                "action": "HOLD_MCP_ALIVE_NEVER_KILL_CHROME",
                "health": health,
                "reason": "MCP_RESPONDS_REFUSE_CHROME_KILL",
            }
        if state == "NEO_PROBE_STARVED":
            return {
                **base,
                "action": "HOLD_PROCESS_ALIVE_PROBE_STARVED",
                "health": health,
                "reason": "BROWSEROS_PROCESS_ALIVE_NO_KILL_NO_DUPLICATE",
            }
        if state == "PROCESS_PROBE_UNPROVEN":
            return {
                **base,
                "action": "HOLD_PROCESS_PROBE_UNPROVEN",
                "health": health,
                "reason": "BROWSEROS_PROCESS_PROBE_UNPROVEN_FAIL_CLOSED",
            }

        # State == DOWN (proven zero listeners & zero BrowserClaw processes): safe cold-start-only path.
        if not exe.is_file():
            return {
                **base,
                "action": "BLOCKED_BINARY_MISSING",
                "health": health,
                "reason": "BROWSEROS_EXECUTABLE_NOT_FOUND",
            }
        if not profile.is_dir():
            return {
                **base,
                "action": "BLOCKED_PROFILE_MISSING",
                "health": health,
                "reason": "EXISTING_BROWSEROS_PROFILE_MISSING_NEVER_CREATED",
            }

        command = [str(exe)]
        if dry_run:
            return {
                **base,
                "action": "DRY_RUN_WOULD_START_NEO",
                "health": health,
                "would_launch": True,
                "command": command,
                "reason": "BROWSEROS_DOWN_DRY_RUN",
            }

        spawn_fn = spawner or _default_spawn_detached
        pid = spawn_fn(command, exe.parent)
        return {
            **base,
            "action": "LAUNCHED_NEO",
            "health": health,
            "launched": True,
            "would_launch": True,
            "pid": pid,
            "command": command,
            "reason": "BROWSEROS_COLD_STARTED_BY_KEEPALIVE",
        }


# ---------------------------------------------------------------------------
# Windows Task Scheduler XML generation & validation (CC-711)
# ---------------------------------------------------------------------------


def _escape_xml(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_task_scheduler_xml(
    *,
    task_name: str,
    description: str,
    command: str,
    arguments: str,
    working_directory: str,
    user_id: str = DEFAULT_TASK_USER_ID,
    logon_type: str = DEFAULT_TASK_LOGON_TYPE,
    repeat_interval: str = DEFAULT_TASK_REPEAT_INTERVAL,
    start_boundary: str = DEFAULT_TASK_START_BOUNDARY,
    enabled: bool = False,
    execution_time_limit: str = "PT5M",
) -> str:
    """Render a deterministic Windows Task Scheduler v1.3 XML template (UTF-8, LF-only).

    Omits ``encoding=`` from the XML prolog so PowerShell's UTF-16 ``Register-ScheduledTask -Xml``
    and Windows Task Scheduler's COM ``NewTask(0).XmlText`` parser accept it without encoding
    switch errors (H1). Defaults strictly to ``enabled=False``, ``user_id='JP'``,
    ``logon_type='InteractiveToken'``, ``repeat_interval='PT15M'``, and ``IgnoreNew``.
    """
    enabled_text = "true" if enabled else "false"
    lines = [
        '<?xml version="1.0"?>',
        f'<Task version="1.3" xmlns="{TASK_XML_NS}">',
        "  <RegistrationInfo>",
        f"    <Description>{_escape_xml(description)}</Description>",
        f"    <URI>\\{_escape_xml(task_name)}</URI>",
        "  </RegistrationInfo>",
        "  <Triggers>",
        "    <LogonTrigger>",
        "      <Enabled>true</Enabled>",
        "      <Delay>PT2M</Delay>",
        f"      <UserId>{_escape_xml(user_id)}</UserId>",
        "    </LogonTrigger>",
        "    <TimeTrigger>",
        "      <Repetition>",
        f"        <Interval>{_escape_xml(repeat_interval)}</Interval>",
        "        <StopAtDurationEnd>false</StopAtDurationEnd>",
        "      </Repetition>",
        f"      <StartBoundary>{_escape_xml(start_boundary)}</StartBoundary>",
        "      <Enabled>true</Enabled>",
        "    </TimeTrigger>",
        "  </Triggers>",
        "  <Principals>",
        '    <Principal id="Author">',
        f"      <UserId>{_escape_xml(user_id)}</UserId>",
        f"      <LogonType>{_escape_xml(logon_type)}</LogonType>",
        "      <RunLevel>LeastPrivilege</RunLevel>",
        "    </Principal>",
        "  </Principals>",
        "  <Settings>",
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>",
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>",
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>",
        "    <AllowHardTerminate>true</AllowHardTerminate>",
        "    <StartWhenAvailable>true</StartWhenAvailable>",
        "    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>",
        "    <IdleSettings>",
        "      <Duration>PT10M</Duration>",
        "      <WaitTimeout>PT1H</WaitTimeout>",
        "      <StopOnIdleEnd>false</StopOnIdleEnd>",
        "      <RestartOnIdle>false</RestartOnIdle>",
        "    </IdleSettings>",
        "    <AllowStartOnDemand>true</AllowStartOnDemand>",
        f"    <Enabled>{enabled_text}</Enabled>",
        "    <Hidden>true</Hidden>",
        "    <RunOnlyIfIdle>false</RunOnlyIfIdle>",
        "    <WakeToRun>false</WakeToRun>",
        f"    <ExecutionTimeLimit>{_escape_xml(execution_time_limit)}</ExecutionTimeLimit>",
        "    <Priority>7</Priority>",
        "    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>",
        "  </Settings>",
        '  <Actions Context="Author">',
        "    <Exec>",
        f"      <Command>{_escape_xml(command)}</Command>",
        f"      <Arguments>{_escape_xml(arguments)}</Arguments>",
        f"      <WorkingDirectory>{_escape_xml(working_directory)}</WorkingDirectory>",
        "    </Exec>",
        "  </Actions>",
        "</Task>",
        "",
    ]
    return "\n".join(lines)


def render_x_list_feed_keepalive_xml(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    pythonw: Path = DEFAULT_PYTHONW,
    user_id: str = DEFAULT_TASK_USER_ID,
    enabled: bool = False,
) -> str:
    script = Path(repo_root) / "scripts" / "run_cc711_keepalive.py"
    return render_task_scheduler_xml(
        task_name=X_FEED_TASK_NAME,
        description=(
            "CC-711 / CC-258: OS-lock-guarded PT15M keepalive + 2-min logon trigger for the "
            "X-list feed runner. Zero duplicate runners or Chrome launches; respects CC-785 "
            "CDP_PROBE_STARVED guard and STOP sentinel. Disabled until Ops installs."
        ),
        command=str(pythonw),
        arguments=f'-B "{script}" x-feed --apply',
        working_directory=str(repo_root),
        user_id=user_id,
        enabled=enabled,
    )


def render_neo_health_keepalive_xml(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    pythonw: Path = DEFAULT_PYTHONW,
    user_id: str = DEFAULT_TASK_USER_ID,
    enabled: bool = False,
) -> str:
    script = Path(repo_root) / "scripts" / "run_cc711_keepalive.py"
    return render_task_scheduler_xml(
        task_name=NEO_HEALTH_TASK_NAME,
        description=(
            "CC-711 / CC-694: OS-lock-guarded PT15M BrowserOS Neo CDP + MCP SSE health and "
            "cold-start-only recovery check (tolerates browseros-neo v0.0.88 blank SSE priming "
            "frames; never kills active Chrome if CDP responds). Disabled until Ops installs."
        ),
        command=str(pythonw),
        arguments=f'-B "{script}" neo-health --apply',
        working_directory=str(repo_root),
        user_id=user_id,
        enabled=enabled,
    )


def validate_task_scheduler_xml(
    xml_text: str,
    *,
    expected_task_name: str,
    expected_user_id: str = DEFAULT_TASK_USER_ID,
    expected_logon_type: str = DEFAULT_TASK_LOGON_TYPE,
    expected_interval: str = DEFAULT_TASK_REPEAT_INTERVAL,
    require_disabled: bool = True,
) -> dict[str, Any]:
    """Parse and fail-closed validate a Windows Task Scheduler XML template."""
    first_line = (xml_text.splitlines()[0] if xml_text else "").strip().lower()
    root = ET.fromstring(xml_text)
    ns = {"t": TASK_XML_NS}

    def _text(xpath: str) -> str:
        node = root.find(xpath, ns)
        return (node.text or "").strip() if node is not None else ""

    uri = _text("t:RegistrationInfo/t:URI")
    user_id = _text("t:Principals/t:Principal/t:UserId")
    logon_type = _text("t:Principals/t:Principal/t:LogonType")
    enabled = _text("t:Settings/t:Enabled")
    multi_policy = _text("t:Settings/t:MultipleInstancesPolicy")
    interval = _text("t:Triggers/t:TimeTrigger/t:Repetition/t:Interval")
    logon_delay = _text("t:Triggers/t:LogonTrigger/t:Delay")
    command = _text("t:Actions/t:Exec/t:Command")
    arguments = _text("t:Actions/t:Exec/t:Arguments")

    errors: list[str] = []
    if first_line.startswith("<?xml") and "encoding=" in first_line:
        errors.append("XML_PROLOG_ENCODING_ATTR_FORBIDDEN")
    if uri != f"\\{expected_task_name}":
        errors.append(f"URI_MISMATCH:{uri}")
    if user_id != expected_user_id:
        errors.append(f"USER_ID_MISMATCH:{user_id}")
    if logon_type != expected_logon_type:
        errors.append(f"LOGON_TYPE_MISMATCH:{logon_type}")
    if require_disabled and enabled != "false":
        errors.append(f"ENABLED_MUST_BE_FALSE:{enabled}")
    if multi_policy != "IgnoreNew":
        errors.append(f"MULTIPLE_INSTANCES_NOT_IGNORENEW:{multi_policy}")
    if interval != expected_interval:
        errors.append(f"REPEAT_INTERVAL_MISMATCH:{interval}")
    if not logon_delay:
        errors.append("LOGON_TRIGGER_MISSING")
    if not command or not arguments:
        errors.append("EXEC_ACTION_INCOMPLETE")

    if errors:
        raise ValueError("TASK_XML_INVALID:" + ",".join(errors))

    return {
        "valid": True,
        "uri": uri,
        "user_id": user_id,
        "logon_type": logon_type,
        "enabled": enabled == "true",
        "multiple_instances_policy": multi_policy,
        "repeat_interval": interval,
        "logon_delay": logon_delay,
        "command": command,
        "arguments": arguments,
    }
