"""Exactly-one detached process owner for the persistent Simple-Gemini scheduler.

This module owns process lifecycle only. It never schedules editorial work, reads credentials,
opens the publication store, calls a model/source/provider, or crosses a public-write boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
    DETACHED_CREATION_FLAGS,
    RUNTIME_ROOT_DEFAULT,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import (
    ROUTINE_EDITORIAL_OWNER as ROUTINE_EDITORIAL_OWNER,
    _NonBlockingFileLock,
)

SCHEMA_VERSION = "contentops.v1_simple_gemini_scheduler_process.v1"
IDENTITY_SCHEMA_VERSION = "contentops.v1_simple_gemini_scheduler_process_identity.v1"
STOP_REQUEST_SCHEMA_VERSION = "contentops.v1_simple_gemini_scheduler_stop_request.v1"

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER_SCRIPT = REPO_ROOT / "scripts" / "run_v1_simple_gemini_scheduler.py"
CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT = (
    RUNTIME_ROOT_DEFAULT / "simple_gemini_scheduler_v1"
)
PROCESS_RUNTIME_DIR_NAME = "process_runtime_v1"
PROCESS_LOCK_FILENAME = "scheduler_process.lock"
LAUNCH_LOCK_FILENAME = "scheduler_launch.lock"
PROCESS_IDENTITY_FILENAME = "scheduler_process_identity_v1.json"
STOP_REQUEST_FILENAME = "scheduler_stop_request_v1.json"
STDOUT_LOG_FILENAME = "scheduler_stdout.log"
STDERR_LOG_FILENAME = "scheduler_stderr.log"

STATE_RUNNING = "RUNNING"
STATE_STOPPED = "STOPPED"
STATE_OWNER_UNPROVEN = "OWNER_UNPROVEN"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _runtime_dir(scheduler_root: str | Path) -> Path:
    return Path(scheduler_root).resolve() / PROCESS_RUNTIME_DIR_NAME


def _runtime_path(scheduler_root: str | Path, filename: str) -> Path:
    return _runtime_dir(scheduler_root) / filename


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    material = {
        key: value for key, value in dict(payload).items() if key != "record_sha256"
    }
    value = {**material, "record_sha256": _logical_hash(material)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_json_record(path: Path, *, schema_version: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    if not isinstance(value, Mapping):
        return {}
    material = {key: item for key, item in value.items() if key != "record_sha256"}
    if value.get("schema_version") != schema_version or str(
        value.get("record_sha256") or ""
    ) != _logical_hash(material):
        return {}
    return dict(value)


def _remove_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def build_scheduler_process_command(
    *,
    python_executable: str,
    scheduler_root: str | Path = CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    published_memory_store: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    published_memory_output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
    poll_seconds: float = 60.0,
) -> list[str]:
    return [
        str(python_executable),
        str(RUNNER_SCRIPT),
        "--scheduler-root",
        str(Path(scheduler_root).resolve()),
        "--published-memory-store",
        str(Path(published_memory_store).resolve()),
        "--published-memory-output-root",
        str(Path(published_memory_output_root).resolve()),
        "--run-forever",
        "--poll-seconds",
        str(float(poll_seconds)),
    ]


def is_canonical_scheduler_command_line(
    command_line: str, *, scheduler_root: str | Path
) -> bool:
    normalized = str(command_line or "").casefold().replace('"', "")
    root = os.path.normcase(str(Path(scheduler_root).resolve())).casefold()
    return bool(
        "run_v1_simple_gemini_scheduler.py" in normalized
        and "--run-forever" in normalized
        and root in os.path.normcase(normalized)
    )


def _process_command_line(pid: int) -> str | None:
    script = (
        "$ErrorActionPreference='Stop';"
        f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}";'
        "if($null -eq $p){exit 3};"
        "$p.CommandLine"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def scheduler_process_state(
    *,
    scheduler_root: str | Path = CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    command_line_probe: Callable[[int], str | None] = _process_command_line,
) -> dict[str, Any]:
    root = Path(scheduler_root).resolve()
    process_lock = _NonBlockingFileLock(_runtime_path(root, PROCESS_LOCK_FILENAME))
    if process_lock.acquire():
        process_lock.release()
        return {
            "schema_version": SCHEMA_VERSION,
            "state": STATE_STOPPED,
            "scheduler_root": str(root),
            "pid": None,
            "exactly_one_process": False,
        }

    identity_path = _runtime_path(root, PROCESS_IDENTITY_FILENAME)
    identity = _load_json_record(
        identity_path,
        schema_version=IDENTITY_SCHEMA_VERSION,
    )
    try:
        pid = int(identity.get("pid") or 0)
    except (TypeError, ValueError):
        pid = 0
    command_line = command_line_probe(pid) if pid > 0 else None
    if (
        not identity
        or pid <= 0
        or str(identity.get("scheduler_root") or "") != str(root)
        or command_line is None
        or not is_canonical_scheduler_command_line(command_line, scheduler_root=root)
    ):
        return {
            "schema_version": SCHEMA_VERSION,
            "state": STATE_OWNER_UNPROVEN,
            "scheduler_root": str(root),
            "pid": pid or None,
            "exactly_one_process": False,
            "blocker": "ACTIVE_PROCESS_LOCK_OWNER_IDENTITY_UNPROVEN",
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "state": STATE_RUNNING,
        "scheduler_root": str(root),
        "pid": pid,
        "started_at_utc": identity.get("started_at_utc"),
        "exactly_one_process": True,
        "public_write_authority": "ZERO",
    }


def _stop_request_present(scheduler_root: str | Path, *, pid: int) -> bool:
    request = _load_json_record(
        _runtime_path(scheduler_root, STOP_REQUEST_FILENAME),
        schema_version=STOP_REQUEST_SCHEMA_VERSION,
    )
    return bool(request and int(request.get("target_pid") or 0) == int(pid))


def run_owned_scheduler_forever(
    scheduler: Any,
    *,
    scheduler_root: str | Path,
    poll_seconds: float,
    max_ticks: int | None = None,
    on_tick: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Hold the process lock for the entire persistent scheduler lifetime."""
    root = Path(scheduler_root).resolve()
    process_lock = _NonBlockingFileLock(_runtime_path(root, PROCESS_LOCK_FILENAME))
    if not process_lock.acquire():
        return {
            "schema_version": SCHEMA_VERSION,
            "outcome": "ALREADY_RUNNING",
            "scheduler_root": str(root),
            "ticks": 0,
        }
    pid = os.getpid()
    identity_path = _runtime_path(root, PROCESS_IDENTITY_FILENAME)
    try:
        _write_json_atomic(
            identity_path,
            {
                "schema_version": IDENTITY_SCHEMA_VERSION,
                "pid": pid,
                "scheduler_root": str(root),
                "started_at_utc": _iso_now(),
                "runner_script": str(RUNNER_SCRIPT),
                "public_write_authority": "ZERO",
            },
        )
        try:
            ticks = scheduler.run_forever(
                poll_seconds=poll_seconds,
                max_ticks=max_ticks,
                on_tick=on_tick,
                stop_requested=lambda: _stop_request_present(root, pid=pid),
            )
            return {
                "schema_version": SCHEMA_VERSION,
                "outcome": "STOPPED_CLEANLY",
                "scheduler_root": str(root),
                "pid": pid,
                "ticks": ticks,
            }
        finally:
            current = _load_json_record(
                identity_path,
                schema_version=IDENTITY_SCHEMA_VERSION,
            )
            if int(current.get("pid") or 0) == pid:
                _remove_if_exists(identity_path)
            _remove_if_exists(_runtime_path(root, STOP_REQUEST_FILENAME))
    finally:
        process_lock.release()


def spawn_detached_scheduler(
    command: list[str],
    *,
    scheduler_root: str | Path,
    working_directory: str | Path = REPO_ROOT,
) -> int:
    runtime_dir = _runtime_dir(scheduler_root)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    with (
        _runtime_path(scheduler_root, STDOUT_LOG_FILENAME).open(
            "a", encoding="utf-8"
        ) as stdout_log,
        _runtime_path(scheduler_root, STDERR_LOG_FILENAME).open(
            "a", encoding="utf-8"
        ) as stderr_log,
    ):
        process = subprocess.Popen(
            [str(value) for value in command],
            cwd=str(Path(working_directory).resolve()),
            stdin=subprocess.DEVNULL,
            stdout=stdout_log,
            stderr=stderr_log,
            creationflags=DETACHED_CREATION_FLAGS,
            close_fds=True,
        )
    return int(process.pid)


def start_scheduler_process(
    *,
    scheduler_root: str | Path = CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    published_memory_store: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    published_memory_output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
    python_executable: str = sys.executable,
    poll_seconds: float = 60.0,
    wait_seconds: float = 20.0,
    state_probe: Callable[..., Mapping[str, Any]] = scheduler_process_state,
    spawn_fn: Callable[..., int] = spawn_detached_scheduler,
) -> dict[str, Any]:
    root = Path(scheduler_root).resolve()
    launch_lock = _NonBlockingFileLock(_runtime_path(root, LAUNCH_LOCK_FILENAME))
    if not launch_lock.acquire():
        return {
            "schema_version": SCHEMA_VERSION,
            "outcome": "START_IN_PROGRESS",
            "scheduler_root": str(root),
            "spawned": False,
        }
    try:
        state = dict(state_probe(scheduler_root=root))
        if state.get("state") == STATE_RUNNING:
            return {
                **state,
                "outcome": "ALREADY_RUNNING",
                "spawned": False,
            }
        if state.get("state") == STATE_OWNER_UNPROVEN:
            return {
                **state,
                "outcome": "BLOCKED_OWNER_UNPROVEN",
                "spawned": False,
            }
        _remove_if_exists(_runtime_path(root, STOP_REQUEST_FILENAME))
        command = build_scheduler_process_command(
            python_executable=python_executable,
            scheduler_root=root,
            published_memory_store=published_memory_store,
            published_memory_output_root=published_memory_output_root,
            poll_seconds=poll_seconds,
        )
        spawned_pid = int(spawn_fn(command, scheduler_root=root))
        deadline = time.monotonic() + max(0.1, float(wait_seconds))
        last_observed = state
        while time.monotonic() < deadline:
            observed = dict(state_probe(scheduler_root=root))
            last_observed = observed
            if observed.get("state") == STATE_RUNNING:
                return {
                    **observed,
                    "outcome": "STARTED",
                    "spawned": True,
                    "launcher_pid": spawned_pid,
                }
            # The child acquires the OS process lock before its atomic PID identity write.
            # OWNER_UNPROVEN is therefore a bounded startup edge, never spawn authority.
            time.sleep(0.1)
        if last_observed.get("state") == STATE_OWNER_UNPROVEN:
            return {
                **last_observed,
                "outcome": "BLOCKED_OWNER_UNPROVEN_AFTER_START",
                "spawned": True,
                "launcher_pid": spawned_pid,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "outcome": "BLOCKED_START_TIMEOUT",
            "scheduler_root": str(root),
            "spawned": True,
            "launcher_pid": spawned_pid,
        }
    finally:
        launch_lock.release()


def stop_scheduler_process(
    *,
    scheduler_root: str | Path = CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    wait_seconds: float = 20.0,
    state_probe: Callable[..., Mapping[str, Any]] = scheduler_process_state,
) -> dict[str, Any]:
    root = Path(scheduler_root).resolve()
    state = dict(state_probe(scheduler_root=root))
    if state.get("state") == STATE_STOPPED:
        return {**state, "outcome": "ALREADY_STOPPED"}
    if state.get("state") != STATE_RUNNING:
        return {**state, "outcome": "BLOCKED_OWNER_UNPROVEN"}
    pid = int(state["pid"])
    _write_json_atomic(
        _runtime_path(root, STOP_REQUEST_FILENAME),
        {
            "schema_version": STOP_REQUEST_SCHEMA_VERSION,
            "target_pid": pid,
            "scheduler_root": str(root),
            "requested_at_utc": _iso_now(),
        },
    )
    deadline = time.monotonic() + max(0.1, float(wait_seconds))
    last_observed = state
    while time.monotonic() < deadline:
        observed = dict(state_probe(scheduler_root=root))
        last_observed = observed
        if observed.get("state") == STATE_STOPPED:
            _remove_if_exists(_runtime_path(root, STOP_REQUEST_FILENAME))
            return {
                **observed,
                "outcome": "STOPPED",
                "stopped_pid": pid,
            }
        # The child removes its PID identity immediately before releasing the OS process lock.
        # That bounded shutdown edge is briefly OWNER_UNPROVEN; keep polling for STOPPED, but
        # never treat it as authority to spawn or force-kill anything.
        time.sleep(0.1)
    if last_observed.get("state") == STATE_OWNER_UNPROVEN:
        return {
            **last_observed,
            "outcome": "BLOCKED_OWNER_UNPROVEN_DURING_STOP",
            "stop_request_persisted": True,
        }
    return {
        **state,
        "outcome": "BLOCKED_STOP_TIMEOUT",
        "stop_request_persisted": True,
    }


def restart_scheduler_process(**kwargs: Any) -> dict[str, Any]:
    root = Path(
        kwargs.get("scheduler_root") or CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT
    ).resolve()
    stop_result = stop_scheduler_process(
        scheduler_root=root,
        wait_seconds=float(kwargs.get("wait_seconds") or 20.0),
        state_probe=kwargs.get("state_probe", scheduler_process_state),
    )
    if stop_result.get("outcome") not in {"STOPPED", "ALREADY_STOPPED"}:
        return {
            "schema_version": SCHEMA_VERSION,
            "outcome": "BLOCKED_RESTART_STOP_FAILED",
            "scheduler_root": str(root),
            "stop": stop_result,
        }
    start_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key
        in {
            "published_memory_store",
            "published_memory_output_root",
            "python_executable",
            "poll_seconds",
            "wait_seconds",
            "state_probe",
            "spawn_fn",
        }
    }
    start_result = start_scheduler_process(scheduler_root=root, **start_kwargs)
    return {
        "schema_version": SCHEMA_VERSION,
        "outcome": (
            "RESTARTED"
            if start_result.get("outcome") == "STARTED"
            else "BLOCKED_RESTART_START_FAILED"
        ),
        "scheduler_root": str(root),
        "stop": stop_result,
        "start": start_result,
    }
