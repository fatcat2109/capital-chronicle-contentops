from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PureWindowsPath

from live_contentops.v1_simple_gemini_scheduler_process_v1 import (
    CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT,
    PROCESS_IDENTITY_FILENAME,
    PROCESS_LOCK_FILENAME,
    PROCESS_RUNTIME_DIR_NAME,
    ROUTINE_EDITORIAL_OWNER,
    RUNNER_SCRIPT,
    STATE_RUNNING,
    STATE_STOPPED,
    _runtime_path,
    build_scheduler_process_command,
    is_canonical_scheduler_command_line,
    restart_scheduler_process,
    run_owned_scheduler_forever,
    scheduler_process_state,
    start_scheduler_process,
    stop_scheduler_process,
)


def _state(state: str, root: Path, *, pid: int | None = None) -> dict:
    return {
        "state": state,
        "scheduler_root": str(root.resolve()),
        "pid": pid,
        "exactly_one_process": state == STATE_RUNNING,
    }


def test_canonical_root_uses_existing_contentops_runtime_convention():
    assert PureWindowsPath(str(CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT)) == PureWindowsPath(
        r"A:\Capital Chronicle\Runtime\ContentOps\simple_gemini_scheduler_v1"
    )
    assert PROCESS_RUNTIME_DIR_NAME == "process_runtime_v1"
    assert ROUTINE_EDITORIAL_OWNER == "SIMPLE_GEMINI_RUNTIME"


def test_process_command_and_identity_are_bound_to_one_root(tmp_path):
    command = build_scheduler_process_command(
        python_executable=sys.executable,
        scheduler_root=tmp_path,
        poll_seconds=5.0,
    )
    command_line = subprocess.list2cmdline(command)
    assert str(RUNNER_SCRIPT) in command_line
    assert "--run-forever" in command
    assert is_canonical_scheduler_command_line(
        command_line,
        scheduler_root=tmp_path,
    )
    assert not is_canonical_scheduler_command_line(
        command_line,
        scheduler_root=tmp_path / "different",
    )


def test_start_returns_started_then_duplicate_returns_already_running(tmp_path):
    states = iter(
        [
            _state(STATE_STOPPED, tmp_path),
            {
                **_state("OWNER_UNPROVEN", tmp_path),
                "blocker": "ACTIVE_PROCESS_LOCK_OWNER_IDENTITY_UNPROVEN",
            },
            _state(STATE_RUNNING, tmp_path, pid=4321),
        ]
    )
    spawned: list[tuple[list[str], Path]] = []

    def probe(**_kwargs):
        return next(states)

    def spawn(command, *, scheduler_root):
        spawned.append((list(command), Path(scheduler_root)))
        return 4310

    started = start_scheduler_process(
        scheduler_root=tmp_path,
        wait_seconds=0.2,
        state_probe=probe,
        spawn_fn=spawn,
    )
    assert started["outcome"] == "STARTED"
    assert started["pid"] == 4321
    assert len(spawned) == 1

    duplicate = start_scheduler_process(
        scheduler_root=tmp_path,
        state_probe=lambda **_kwargs: _state(STATE_RUNNING, tmp_path, pid=4321),
        spawn_fn=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("duplicate spawn")
        ),
    )
    assert duplicate["outcome"] == "ALREADY_RUNNING"
    assert duplicate["spawned"] is False


def test_stop_and_restart_preserve_the_same_canonical_root(tmp_path):
    stop_states = iter(
        [
            _state(STATE_RUNNING, tmp_path, pid=7001),
            {
                **_state("OWNER_UNPROVEN", tmp_path, pid=7001),
                "blocker": "ACTIVE_PROCESS_LOCK_OWNER_IDENTITY_UNPROVEN",
            },
            _state(STATE_STOPPED, tmp_path),
        ]
    )
    stopped = stop_scheduler_process(
        scheduler_root=tmp_path,
        wait_seconds=0.2,
        state_probe=lambda **_kwargs: next(stop_states),
    )
    assert stopped["outcome"] == "STOPPED"
    assert stopped["scheduler_root"] == str(tmp_path.resolve())

    restart_states = iter(
        [
            _state(STATE_RUNNING, tmp_path, pid=7101),
            {
                **_state("OWNER_UNPROVEN", tmp_path, pid=7101),
                "blocker": "ACTIVE_PROCESS_LOCK_OWNER_IDENTITY_UNPROVEN",
            },
            _state(STATE_STOPPED, tmp_path),
            _state(STATE_STOPPED, tmp_path),
            _state(STATE_RUNNING, tmp_path, pid=7102),
        ]
    )
    spawned: list[Path] = []
    restarted = restart_scheduler_process(
        scheduler_root=tmp_path,
        wait_seconds=0.2,
        state_probe=lambda **_kwargs: next(restart_states),
        spawn_fn=lambda _command, *, scheduler_root: (
            spawned.append(Path(scheduler_root)) or 7100
        ),
    )
    assert restarted["outcome"] == "RESTARTED"
    assert restarted["scheduler_root"] == str(tmp_path.resolve())
    assert restarted["start"]["scheduler_root"] == str(tmp_path.resolve())
    assert spawned == [tmp_path.resolve()]


def test_owned_process_identity_is_running_only_while_process_lock_is_held(tmp_path):
    observations: list[dict] = []

    class FakeScheduler:
        def run_forever(self, **kwargs):
            command = build_scheduler_process_command(
                python_executable=sys.executable,
                scheduler_root=tmp_path,
            )
            observations.append(
                scheduler_process_state(
                    scheduler_root=tmp_path,
                    command_line_probe=lambda _pid: subprocess.list2cmdline(command),
                )
            )
            assert kwargs["stop_requested"]() is False
            return 2

    result = run_owned_scheduler_forever(
        FakeScheduler(),
        scheduler_root=tmp_path,
        poll_seconds=0.01,
        max_ticks=2,
    )
    assert result["outcome"] == "STOPPED_CLEANLY"
    assert result["ticks"] == 2
    assert observations[0]["state"] == STATE_RUNNING
    assert observations[0]["exactly_one_process"] is True
    assert scheduler_process_state(scheduler_root=tmp_path)["state"] == STATE_STOPPED
    assert not _runtime_path(tmp_path, PROCESS_IDENTITY_FILENAME).exists()
    assert _runtime_path(tmp_path, PROCESS_LOCK_FILENAME).exists()


def test_status_cli_needs_no_store_or_proof_directory_creation(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER_SCRIPT),
            "--status",
            "--scheduler-root",
            str(tmp_path),
        ],
        cwd=str(RUNNER_SCRIPT.parent.parent),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0
    assert '"state": "STOPPED"' in completed.stdout


def test_injected_clock_is_forbidden_on_canonical_production_root():
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER_SCRIPT),
            "--tick-utc",
            "2030-01-01T10:00:00Z",
            "--scheduler-root",
            str(CANONICAL_SIMPLE_GEMINI_SCHEDULER_ROOT),
        ],
        cwd=str(RUNNER_SCRIPT.parent.parent),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode != 0
    assert "forbidden on the canonical production scheduler root" in completed.stderr


def test_windows_task_installer_owns_only_the_existing_runner():
    installer = RUNNER_SCRIPT.parent / "Install-ContentOpsV1SimpleScheduler.ps1"
    text = installer.read_text(encoding="utf-8")
    assert "run_v1_simple_gemini_scheduler.py" in text
    assert "--run-forever" in text
    assert "-MultipleInstances IgnoreNew" in text
    assert "-RestartCount 999" in text
    assert "-RepetitionInterval (New-TimeSpan -Minutes 5)" in text
    assert "DurablePublicationCoordinator" not in text
    assert "--tick-utc" not in text
