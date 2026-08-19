from __future__ import annotations

import inspect
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import daily_app_launcher_v1 as launcher
from live_contentops.daily_app_launcher_v1 import (
    LaunchDecision,
    PortInventory,
    build_canonical_daily_app_command,
    build_credential_inventory,
    decide_action,
    is_canonical_daily_app_command_line,
    logical_canonical_supervisor_count,
    preflight_store_safety,
    render_credential_inventory,
    render_summary,
    store_path_is_protected_backup,
    summarize_browser_state,
)

PRODUCTION_STORE = str(launcher.CANONICAL_PRODUCTION_STORE_PATH)
PRODUCTION_OUTPUT = str(launcher.CANONICAL_PRODUCTION_OUTPUT_ROOT)
CANONICAL_CMDLINE = (
    '"python.exe" -m live_contentops.cli daily-app start '
    f'--store-path "{PRODUCTION_STORE}" --output-root "{PRODUCTION_OUTPUT}"'
)


def _healthy_snapshot() -> dict:
    return {
        "schema_version": launcher.SNAPSHOT_SCHEMA,
        "runtime": {
            "app_identity": "Capital Chronicle ContentOps V1 - Daily App",
            "operating_mode": "AUTONOMOUS_DEFAULT",
            "kill_switch_active": False,
            "controller_health": "HEALTHY",
            "next_wake_utc": "2026-08-10T13:00:00Z",
        },
        "published": {"unknown_write_count": 0, "pending_readback_count": 0},
        "authority": {"store_schema_version": 8},
        "platforms": {"destinations": [
            {"platform_id": "substack", "readiness": "READY_AUTHENTICATED"},
        ]},
    }


def _inventory(listeners=None, listener_cmds=None, supervisors=None) -> PortInventory:
    return PortInventory(
        listener_pids=list(listeners or []),
        listener_command_lines=dict(listener_cmds or {}),
        supervisor_processes=list(supervisors or []),
    )


def test_healthy_existing_runtime_no_duplicate_start():
    inventory = _inventory(
        listeners=[51892],
        listener_cmds={51892: CANONICAL_CMDLINE},
        supervisors=[{"pid": 51892, "cmd": CANONICAL_CMDLINE}],
    )
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health={"status": "LOOPBACK_API_HEALTHY", "schema_version": launcher.LOOPBACK_API_SCHEMA},
        snapshot=_healthy_snapshot(),
    )
    assert decision.outcome == "ALREADY_RUNNING"
    assert decision.may_spawn is False
    assert decision.canonical_supervisor_count == 1


def test_absent_runtime_canonical_command_assembled():
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=_inventory(),
        health=None,
        snapshot=None,
    )
    existing = Path(PRODUCTION_STORE).exists()
    if existing:
        assert decision.outcome == "START_REQUIRED"
        assert decision.may_spawn is True
    else:
        assert decision.outcome == "BLOCKED_PRODUCTION_STORE_MISSING_NEVER_CREATE_IMPLICITLY"
        assert decision.may_spawn is False
    command = build_canonical_daily_app_command(
        python_executable="python",
        store_path=PRODUCTION_STORE,
        output_root=PRODUCTION_OUTPUT,
    )
    assert command == [
        "python", "-m", "live_contentops.cli", "daily-app", "start",
        "--store-path", PRODUCTION_STORE,
        "--output-root", PRODUCTION_OUTPUT,
        "--api-port", "5174",
    ]


def test_unknown_port_owner_fails_closed():
    inventory = _inventory(
        listeners=[4242],
        listener_cmds={4242: "node.exe vite --port 5174"},
    )
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health={"status": "LOOPBACK_API_HEALTHY", "schema_version": launcher.LOOPBACK_API_SCHEMA},
        snapshot=_healthy_snapshot(),
    )
    assert decision.outcome == "BLOCKED_PORT_OWNER_UNPROVEN"
    assert decision.may_spawn is False
    no_owner = _inventory(listeners=[4242], listener_cmds={})
    decision2 = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=no_owner,
        health=None,
        snapshot=None,
    )
    assert decision2.outcome == "BLOCKED_PORT_OWNER_UNPROVEN"
    assert decision2.may_spawn is False


def test_store_path_is_exact_canonical_constant():
    assert launcher.canonical_store_path() == Path(PRODUCTION_STORE)
    assert PRODUCTION_STORE.endswith("contentops_daily_app_v1.sqlite3")
    command = build_canonical_daily_app_command(
        python_executable=sys.executable,
        store_path=PRODUCTION_STORE,
        output_root=PRODUCTION_OUTPUT,
    )
    assert PRODUCTION_STORE in command


def test_production_db_never_reset_or_recreated(tmp_path):
    store = tmp_path / "shadow.sqlite3"
    store.write_bytes(b"sentinel-store-bytes")
    before = store.stat().st_mtime_ns
    ok, reason = preflight_store_safety(store, allow_new_store=False)
    assert ok is True
    assert reason == "EXISTING_STORE_REUSED_NEVER_RESET"
    assert store.read_bytes() == b"sentinel-store-bytes"
    assert store.stat().st_mtime_ns == before
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert "import sqlite3" not in source
    assert "sqlite3.connect" not in source
    assert "os.remove" not in source
    assert "unlink" not in source
    assert "DROP TABLE" not in source


def test_kill_switch_preserved_and_no_control_write():
    snapshot = _healthy_snapshot()
    snapshot["runtime"]["operating_mode"] = "KILL_SWITCH"
    snapshot["runtime"]["kill_switch_active"] = True
    inventory = _inventory(
        listeners=[51892],
        listener_cmds={51892: CANONICAL_CMDLINE},
        supervisors=[{"pid": 51892, "cmd": CANONICAL_CMDLINE}],
    )
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health={"status": "LOOPBACK_API_HEALTHY", "schema_version": launcher.LOOPBACK_API_SCHEMA},
        snapshot=snapshot,
    )
    assert decision.outcome == "ALREADY_RUNNING_KILL_SWITCH_ACTIVE"
    assert decision.kill_switch_active is True
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert "method=\"POST\"" not in source and "Request(method=" not in source
    assert "control/mode" not in source
    assert launcher.POST_FORBIDDEN_PROOF


def test_unknown_write_and_pending_reconciliation_never_touched():
    snapshot = _healthy_snapshot()
    snapshot["published"]["unknown_write_count"] = 1
    snapshot["published"]["pending_readback_count"] = 2
    browser_state = {
        "chrome_profile_binding": "LOCKED",
        "chrome_9222_ingestion_only": "UNAVAILABLE",
        "x_ingestion_session": "UNAVAILABLE",
        "edge_9223_publishing_only": "READY",
        "edge_reauth_surfaces": [],
        "edge_ready_surfaces": ["SUBSTACK_ARTICLE"],
        "browser_roles_separated": True,
    }
    summary = render_summary(
        decision=LaunchDecision(outcome="ALREADY_RUNNING", reason="already healthy", canonical_supervisor_count=1),
        snapshot=snapshot,
        browser_state=browser_state,
        ui_state={"status": "SKIPPED", "url": None, "mechanism": None, "pid": None},
        store_path=Path(PRODUCTION_STORE),
        store_exists=True,
        schema_version=8,
        inventory_report="NO_VARS",
    )
    assert "Unknown Write: 1" in summary
    assert "Pending Reconciliation: 2" in summary
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert "reconciliations" not in source
    assert "/api/daily-app/control" not in source
    assert "never reset" in summary or "never reset" in source


def test_credential_inventory_emits_names_and_booleans_only():
    env = {
        "NINE_ROUTER_API_KEY": "sk-super-secret-sentinel-value-1234",
        "TELEGRAM_BOT_TOKEN": "777777777:AAF-secret-sentinel",
        "X_CLIENT_ID": "",
    }
    rows = build_credential_inventory(env)
    rendered = render_credential_inventory(rows)
    states = {row["variable"]: row["state"] for row in rows}
    assert states["NINE_ROUTER_API_KEY"] == "PRESENT"
    assert states["TELEGRAM_BOT_TOKEN"] == "PRESENT"
    assert states["X_CLIENT_ID"] == "MISSING"
    assert "sk-super-secret-sentinel-value-1234" not in rendered
    assert "777777777:AAF-secret-sentinel" not in rendered
    for row in rows:
        assert set(row) == {"group", "scope", "variable", "state"}
        assert row["scope"] in {"V1_NOW", "V2_LATER", "OPTIONAL"}


def test_summary_never_contains_secret_shaped_material():
    env = {
        "NINE_ROUTER_API_KEY": "sk-live-sentinel-abcdef123456",
        "TELEGRAM_BOT_TOKEN": "123456789:AAHsentinelvalue",
        "THREADS_USER_ACCESS_TOKEN": "IGQVJ-sentinel-longvalue",
    }
    for name, value in env.items():
        os.environ[name] = value
    try:
        inventory_report = render_credential_inventory(build_credential_inventory(env))
        summary = render_summary(
            decision=LaunchDecision(outcome="ALREADY_RUNNING", reason="already healthy", canonical_supervisor_count=1),
            snapshot=_healthy_snapshot(),
            browser_state={
                "chrome_profile_binding": "LOCKED",
                "chrome_9222_ingestion_only": "UNAVAILABLE",
                "x_ingestion_session": "UNAVAILABLE",
                "edge_9223_publishing_only": "READY",
                "edge_reauth_surfaces": [],
                "edge_ready_surfaces": ["SUBSTACK_ARTICLE"],
                "browser_roles_separated": True,
            },
            ui_state={"status": "READY", "url": "http://127.0.0.1:4173/", "mechanism": "npm_run_preview_detached", "pid": 1},
            store_path=Path(PRODUCTION_STORE),
            store_exists=True,
            schema_version=8,
            inventory_report=inventory_report,
        )
        guarded = launcher._redaction_guard(summary, env)
        for value in env.values():
            assert value not in guarded
    finally:
        for name in env:
            os.environ.pop(name, None)


def test_repeated_invocation_is_idempotent():
    inventory = _inventory(
        listeners=[51892],
        listener_cmds={51892: CANONICAL_CMDLINE},
        supervisors=[{"pid": 51892, "cmd": CANONICAL_CMDLINE}],
    )
    decisions = []
    for _ in range(2):
        decisions.append(decide_action(
            api_base="http://127.0.0.1:5174",
            store_path=Path(PRODUCTION_STORE),
            inventory=inventory,
            health={"status": "LOOPBACK_API_HEALTHY", "schema_version": launcher.LOOPBACK_API_SCHEMA},
            snapshot=_healthy_snapshot(),
        ))
    assert all(decision.outcome == "ALREADY_RUNNING" for decision in decisions)
    assert all(decision.may_spawn is False for decision in decisions)
    assert all(decision.canonical_supervisor_count == 1 for decision in decisions)


def test_logical_supervisor_count_collapses_only_proven_canonical_ancestry():
    standalone = [{"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE}]
    wrapper_child = [
        {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
        {"pid": 101, "parent_pid": 100, "cmd": CANONICAL_CMDLINE},
    ]
    nested = wrapper_child + [
        {"pid": 102, "parent_pid": 101, "cmd": CANONICAL_CMDLINE},
    ]
    independent = [
        {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
        {"pid": 200, "parent_pid": 19, "cmd": CANONICAL_CMDLINE},
    ]
    two_trees = wrapper_child + [
        {"pid": 200, "parent_pid": 19, "cmd": CANONICAL_CMDLINE},
        {"pid": 201, "parent_pid": 200, "cmd": CANONICAL_CMDLINE},
    ]
    assert logical_canonical_supervisor_count(standalone, PRODUCTION_STORE) == 1
    assert logical_canonical_supervisor_count(wrapper_child, PRODUCTION_STORE) == 1
    assert logical_canonical_supervisor_count(nested, PRODUCTION_STORE) == 1
    assert logical_canonical_supervisor_count(independent, PRODUCTION_STORE) == 2
    assert logical_canonical_supervisor_count(two_trees, PRODUCTION_STORE) == 2


def test_logical_supervisor_count_is_conservative_for_unknown_or_malformed_ancestry():
    missing_parent = [
        {"pid": 100, "cmd": CANONICAL_CMDLINE},
        {"pid": 101, "cmd": CANONICAL_CMDLINE},
    ]
    duplicate_pid = [
        {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
        {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
    ]
    cyclic = [
        {"pid": 100, "parent_pid": 101, "cmd": CANONICAL_CMDLINE},
        {"pid": 101, "parent_pid": 100, "cmd": CANONICAL_CMDLINE},
    ]
    assert logical_canonical_supervisor_count(missing_parent, PRODUCTION_STORE) == 2
    assert logical_canonical_supervisor_count(duplicate_pid, PRODUCTION_STORE) == 2
    assert logical_canonical_supervisor_count(cyclic, PRODUCTION_STORE) == 2


def test_healthy_listener_child_of_canonical_wrapper_is_one_running_supervisor():
    inventory = _inventory(
        listeners=[101],
        listener_cmds={101: CANONICAL_CMDLINE},
        supervisors=[
            {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
            {"pid": 101, "parent_pid": 100, "cmd": CANONICAL_CMDLINE},
        ],
    )
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health={"status": "LOOPBACK_API_HEALTHY", "schema_version": launcher.LOOPBACK_API_SCHEMA},
        snapshot=_healthy_snapshot(),
    )
    assert decision.outcome == "ALREADY_RUNNING"
    assert decision.canonical_supervisor_count == 1


def test_multiple_supervisors_fails_closed():
    inventory = _inventory(
        listeners=[51892],
        listener_cmds={51892: CANONICAL_CMDLINE},
        supervisors=[
            {"pid": 51892, "cmd": CANONICAL_CMDLINE},
            {"pid": 61000, "cmd": CANONICAL_CMDLINE},
        ],
    )
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health=None,
        snapshot=None,
    )
    assert decision.outcome == "BLOCKED_MULTIPLE_SUPERVISORS"
    assert decision.may_spawn is False


def test_two_independent_wrapper_child_trees_fail_closed():
    inventory = _inventory(supervisors=[
        {"pid": 100, "parent_pid": 9, "cmd": CANONICAL_CMDLINE},
        {"pid": 101, "parent_pid": 100, "cmd": CANONICAL_CMDLINE},
        {"pid": 200, "parent_pid": 19, "cmd": CANONICAL_CMDLINE},
        {"pid": 201, "parent_pid": 200, "cmd": CANONICAL_CMDLINE},
    ])
    decision = decide_action(
        api_base="http://127.0.0.1:5174",
        store_path=Path(PRODUCTION_STORE),
        inventory=inventory,
        health=None,
        snapshot=None,
    )
    assert decision.outcome == "BLOCKED_MULTIPLE_SUPERVISORS"
    assert decision.canonical_supervisor_count == 2


def test_post_start_wrapper_child_topology_does_not_trigger_duplicate_race(
    tmp_path, monkeypatch, capsys,
):
    store = tmp_path / "shadow.sqlite3"
    output = tmp_path / "outputs"
    logs = tmp_path / "logs"
    inventories = iter([
        _inventory(),
        _inventory(supervisors=[
            {"pid": 100, "parent_pid": 9, "cmd": (
                '"python.exe" -m live_contentops.cli daily-app start '
                f'--store-path "{store}" --output-root "{output}"'
            )},
            {"pid": 101, "parent_pid": 100, "cmd": (
                '"python.exe" -m live_contentops.cli daily-app start '
                f'--store-path "{store}" --output-root "{output}"'
            )},
        ]),
    ])
    stopped: list[int] = []
    monkeypatch.setattr(launcher, "collect_port_inventory", lambda _port: next(inventories))
    monkeypatch.setattr(launcher, "spawn_detached_daily_app", lambda *_, **__: 100)
    monkeypatch.setattr(launcher, "wait_for_health", lambda *_, **__: True)
    monkeypatch.setattr(launcher, "probe_snapshot", lambda *_: _healthy_snapshot())
    monkeypatch.setattr(launcher, "probe_cdp", lambda _port: {"cdp_alive": False})
    monkeypatch.setattr(launcher, "_stop_pid", stopped.append)
    result = launcher.run_launcher([
        "--store-path", str(store),
        "--output-root", str(output),
        "--log-root", str(logs),
        "--allow-new-store",
        "--no-ui",
        "--no-open-browser",
        "--no-ingestion-bootstrap",
    ])
    assert result == 0
    assert stopped == []
    assert "Decision: STARTED" in capsys.readouterr().out
    identity = json.loads((logs / "runtime_identity_v1.json").read_text(encoding="utf-8"))
    assert identity["supervisor_pid"] == 100


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-native detached spawn")
def test_detached_spawn_survives_launcher_exit(tmp_path):
    marker = tmp_path / "marker.txt"
    command = [
        sys.executable, "-c",
        f"import time; open(r'{marker}', 'w').close(); time.sleep(4)",
    ]
    pid = launcher.spawn_detached_daily_app(
        command,
        working_directory=tmp_path,
        stdout_log=tmp_path / "out.log",
        stderr_log=tmp_path / "err.log",
    )
    assert pid > 0
    deadline = time.monotonic() + 5.0
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert marker.exists()
    flags = launcher.DETACHED_CREATION_FLAGS
    assert flags & launcher.CREATE_NO_WINDOW


def test_ui_bootstrap_is_local_only():
    assert launcher.UI_PREVIEW_PORT == 4173
    assert launcher.UI_DEV_PORT == 5173
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert '"--host", "127.0.0.1"' in source
    assert "0.0.0.0" not in source


def test_ui_build_epoch_rebuilds_stale_dist_then_reuses_current_source(tmp_path, monkeypatch):
    ui_dir = tmp_path / "ui"
    (ui_dir / "src").mkdir(parents=True)
    (ui_dir / "src" / "main.tsx").write_text("export const cockpit = 'V1 LIVE';\n", encoding="utf-8")
    (ui_dir / "package.json").write_text('{"scripts":{"build":"vite build"}}\n', encoding="utf-8")
    (ui_dir / "dist").mkdir()
    (ui_dir / "dist" / "index.html").write_text("stale", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(list(command))
        (ui_dir / "dist" / "index.html").write_text("current", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)
    first = launcher.ensure_current_ui_build(
        log_root=tmp_path / "logs", ui_dir=ui_dir, source_sha="a" * 40,
    )
    assert first["status"] == "READY"
    assert first["reason"] == "BUILT_CURRENT_SOURCE_EPOCH"
    assert calls == [["cmd", "/c", "npm", "run", "build"]]
    marker = json.loads((ui_dir / "dist" / launcher.UI_EPOCH_FILE).read_text(encoding="utf-8"))
    assert marker["source_epoch"] == launcher.compute_ui_source_epoch(ui_dir)
    assert marker["source_sha"] == "a" * 40

    second = launcher.ensure_current_ui_build(
        log_root=tmp_path / "logs", ui_dir=ui_dir, source_sha="b" * 40,
    )
    assert second["reason"] == "REUSED_CURRENT_SOURCE_EPOCH"
    assert len(calls) == 1
    refreshed = json.loads((ui_dir / "dist" / launcher.UI_EPOCH_FILE).read_text(encoding="utf-8"))
    assert refreshed["source_sha"] == "b" * 40


def test_existing_ui_is_reused_only_for_the_current_source_epoch(tmp_path, monkeypatch):
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    epoch = "c" * 64
    monkeypatch.setattr(launcher, "UI_DIR", ui_dir)
    monkeypatch.setattr(
        launcher, "ensure_current_ui_build",
        lambda **_: {"status": "READY", "reason": "BUILT_CURRENT_SOURCE_EPOCH", "source_epoch": epoch, "source_sha": "d" * 40},
    )
    monkeypatch.setattr(launcher, "_url_ok", lambda url, **_: url.endswith(":4173/"))
    monkeypatch.setattr(
        launcher, "_http_get_json",
        lambda url, **_: {"schema_version": launcher.UI_EPOCH_SCHEMA, "source_epoch": epoch},
    )
    current = launcher.ensure_ui(
        enabled=True, log_root=tmp_path / "logs", snapshot_available=True,
        source_sha="d" * 40,
    )
    assert current["status"] == "ALREADY_READY"
    assert current["mechanism"] == "existing_preview_current_source_epoch"

    monkeypatch.setattr(
        launcher, "_http_get_json",
        lambda url, **_: {"schema_version": launcher.UI_EPOCH_SCHEMA, "source_epoch": "stale"},
    )
    stale = launcher.ensure_ui(
        enabled=True, log_root=tmp_path / "logs", snapshot_available=True,
        source_sha="d" * 40,
    )
    assert stale["status"] == "UNAVAILABLE"
    assert stale["mechanism"] == "EXISTING_UI_SOURCE_EPOCH_MISMATCH"


def test_dashboard_opens_once_in_normal_default_browser_after_ui_health(tmp_path):
    opened: list[str] = []
    ui_state = {
        "status": "READY",
        "url": "http://127.0.0.1:4173/",
        "mechanism": "npm_run_preview_detached",
        "pid": 123,
    }
    first = launcher.open_operator_dashboard(
        ui_state=ui_state,
        log_root=tmp_path,
        opener=opened.append,
        now_epoch=1_000.0,
    )
    second = launcher.open_operator_dashboard(
        ui_state=ui_state,
        log_root=tmp_path,
        opener=opened.append,
        now_epoch=1_010.0,
    )
    assert first == {
        "status": "OPENED", "url": "http://127.0.0.1:4173/", "deduplicated": False,
    }
    assert second == {
        "status": "SUPPRESSED_RECENT_OPEN",
        "url": "http://127.0.0.1:4173/",
        "deduplicated": True,
    }
    assert opened == ["http://127.0.0.1:4173/"]
    marker = (tmp_path / launcher.DASHBOARD_OPEN_MARKER).read_text(encoding="utf-8")
    assert '"browser_mechanism":"NORMAL_DEFAULT_BROWSER"' in marker
    assert '"cdp_used":false' in marker
    assert "9222" not in marker and "9223" not in marker


def test_dashboard_never_opens_before_runtime_or_ui_health(tmp_path):
    opened: list[str] = []
    result = launcher.open_operator_dashboard(
        ui_state={"status": "WAITING_FOR_RUNTIME_HEALTH", "url": None},
        log_root=tmp_path,
        opener=opened.append,
    )
    assert result["status"] == "NOT_OPENED_UI_NOT_HEALTHY"
    assert opened == []


def test_browser_role_separation_is_hardcoded():
    assert launcher.INGESTION_CDP_PORT == 9222
    assert launcher.PUBLISHING_CDP_PORT == 9223
    snapshot = _healthy_snapshot()
    state = summarize_browser_state(snapshot)
    assert state["browser_roles_separated"] is True
    summary = render_summary(
        decision=LaunchDecision(outcome="ALREADY_RUNNING", reason="ok", canonical_supervisor_count=1),
        snapshot=snapshot,
        browser_state=state,
        ui_state={"status": "SKIPPED", "url": None, "mechanism": None, "pid": None},
        store_path=Path(PRODUCTION_STORE),
        store_exists=True,
        schema_version=8,
        inventory_report="NO_VARS",
    )
    assert "Chrome 9222 = ingestion only" in summary
    assert "Edge 9223 = publishing/readback only" in summary


def test_protected_backup_store_paths_are_rejected(tmp_path):
    protected = tmp_path / "contentops_daily_app_v1.pre_v8_backup.sqlite3"
    assert store_path_is_protected_backup(str(protected)) is True
    ok, reason = preflight_store_safety(Path(str(protected)), allow_new_store=True)
    assert ok is False
    assert reason == "BLOCKED_STORE_PATH_IS_PROTECTED_BACKUP"
    assert store_path_is_protected_backup(str(tmp_path / "migration-backups" / "x.sqlite3")) is True
    assert store_path_is_protected_backup(PRODUCTION_STORE) is False


def test_isolated_shadow_store_requires_explicit_flag(tmp_path):
    shadow = tmp_path / "shadow.sqlite3"
    ok, reason = preflight_store_safety(shadow, allow_new_store=False)
    assert ok is False
    assert reason == "BLOCKED_STORE_MISSING_NEW_STORE_NOT_AUTHORIZED"
    ok2, reason2 = preflight_store_safety(shadow, allow_new_store=True)
    assert ok2 is True
    assert reason2 == "ISOLATED_NEW_STORE_AUTHORIZED_BY_SHADOW_FLAG"
    assert not shadow.exists()


def test_command_line_identity_matching():
    assert is_canonical_daily_app_command_line(CANONICAL_CMDLINE, PRODUCTION_STORE) is True
    assert is_canonical_daily_app_command_line(
        CANONICAL_CMDLINE, str(launcher.RUNTIME_ROOT_DEFAULT / "other.sqlite3")
    ) is False
    assert is_canonical_daily_app_command_line("node.exe some-server.js", PRODUCTION_STORE) is False
    assert is_canonical_daily_app_command_line("", PRODUCTION_STORE) is False
