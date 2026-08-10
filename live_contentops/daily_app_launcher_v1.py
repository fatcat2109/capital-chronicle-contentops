"""One-click morning launch/resume bootstrap for the canonical Final Daily App.

This module is bootstrap/orchestration glue only.  It never re-implements Daily App
runtime logic, never opens the durable SQLite store, never performs POST/control
requests, never reads secret values, and never kills or resets anything.  It either
proves an existing canonical supervisor is already running, or detaches exactly one
canonical `python -m live_contentops.cli daily-app start ...` process, then reports a
compact redacted operator summary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_ROOT_DEFAULT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
CANONICAL_PRODUCTION_STORE_PATH = RUNTIME_ROOT_DEFAULT / "contentops_daily_app_v1.sqlite3"
CANONICAL_PRODUCTION_OUTPUT_ROOT = RUNTIME_ROOT_DEFAULT / "daily_app_outputs"
LAUNCHER_LOG_ROOT_DEFAULT = RUNTIME_ROOT_DEFAULT / "one_click_launcher"

DEFAULT_API_PORT = 5174
HEALTH_ROUTE = "/api/health"
SNAPSHOT_ROUTE = "/api/daily-app/snapshot"
LOOPBACK_API_SCHEMA = "contentops.daily_app_loopback_api.v1"
SNAPSHOT_SCHEMA = "contentops.daily_app_ui_snapshot.v1"
INGESTION_CDP_PORT = 9222
PUBLISHING_CDP_PORT = 9223
UI_PREVIEW_PORT = 4173
UI_DEV_PORT = 5173
UI_DIR = REPO_ROOT / "ui" / "contentops_v5"
REAUTH_READINESS_STATES = frozenset({
    "REAUTH_REQUIRED",
    "AUTH_INVALID",
    "SESSION_UNAVAILABLE",
    "PERMISSION_MISSING",
    "IDENTITY_MISMATCH",
})
PROTECTED_STORE_MARKERS = ("pre_v8", "byte_exact", "migration-backups", "pre_schema")

CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_CREATION_FLAGS = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

POST_FORBIDDEN_PROOF = "this module performs only HTTP GET probes and detached process starts"


class LauncherError(RuntimeError):
    pass


@dataclass
class PortInventory:
    listener_pids: list[int] = field(default_factory=list)
    listener_command_lines: dict[int, str] = field(default_factory=dict)
    supervisor_processes: list[dict[str, Any]] = field(default_factory=list)
    inventory_error: Optional[str] = None


@dataclass
class LaunchDecision:
    outcome: str
    reason: str
    may_spawn: bool = False
    port_pid: Optional[int] = None
    canonical_supervisor_count: int = 0
    kill_switch_active: bool = False
    store_identity_canonical: bool = False


def canonical_store_path() -> Path:
    return CANONICAL_PRODUCTION_STORE_PATH


def build_canonical_daily_app_command(
    *,
    python_executable: str,
    store_path: str,
    output_root: str,
    api_port: int = DEFAULT_API_PORT,
    skip_edge_bootstrap: bool = False,
) -> list[str]:
    command = [
        str(python_executable),
        "-m",
        "live_contentops.cli",
        "daily-app",
        "start",
        "--store-path",
        str(store_path),
        "--output-root",
        str(output_root),
        "--api-port",
        str(int(api_port)),
    ]
    if skip_edge_bootstrap:
        command.append("--skip-edge-bootstrap")
    return command


def is_canonical_daily_app_command_line(command_line: str, expected_store_path: str) -> bool:
    if not command_line:
        return False
    normalized = command_line.lower().replace("\u201c", '"').replace("\u201d", '"')
    store = str(expected_store_path).lower()
    if "live_contentops.cli" not in normalized or "daily-app" not in normalized:
        return False
    if " start" not in normalized and "--run-forever" not in normalized:
        return False
    return store in normalized.replace('"', "")


def _http_get_json(url: str, *, timeout: float) -> Optional[dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def probe_health(api_base: str, *, timeout: float = 4.0) -> Optional[dict[str, Any]]:
    payload = _http_get_json(f"{api_base}{HEALTH_ROUTE}", timeout=timeout)
    if not isinstance(payload, Mapping):
        return None
    if payload.get("status") != "LOOPBACK_API_HEALTHY":
        return None
    if payload.get("schema_version") != LOOPBACK_API_SCHEMA:
        return None
    return dict(payload)


def probe_snapshot(api_base: str, *, timeout: float = 20.0) -> Optional[dict[str, Any]]:
    payload = _http_get_json(f"{api_base}{SNAPSHOT_ROUTE}", timeout=timeout)
    if not isinstance(payload, Mapping) or payload.get("schema_version") != SNAPSHOT_SCHEMA:
        return None
    return dict(payload)


def probe_cdp(port: int, *, timeout: float = 3.0) -> dict[str, Any]:
    payload = _http_get_json(f"http://127.0.0.1:{port}/json/version", timeout=timeout)
    if not isinstance(payload, Mapping):
        return {"cdp_alive": False, "browser_family": None}
    return {
        "cdp_alive": True,
        "browser_family": str(payload.get("Browser") or ""),
    }


def _powershell_json(script: str, *, timeout: float = 25.0) -> Optional[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    try:
        return json.loads(completed.stdout)
    except ValueError:
        return None


def collect_port_inventory(api_port: int) -> PortInventory:
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"$listeners=@(Get-NetTCPConnection -LocalPort {int(api_port)} -State Listen"
        " | Select-Object -ExpandProperty OwningProcess -Unique);"
        "$details=@{};"
        "foreach($p in $listeners){$c=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$p)).CommandLine;"
        "$details[[string]$p]=$c};"
        "$supervisors=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\""
        " | Where-Object { $_.CommandLine -like '*daily-app*' }"
        " | ForEach-Object { @{ pid = $_.ProcessId; cmd = $_.CommandLine } });"
        "@{ listeners = $listeners; listener_command_lines = $details; supervisors = $supervisors }"
        " | ConvertTo-Json -Compress -Depth 4"
    )
    payload = _powershell_json(script)
    if payload is None:
        return PortInventory(inventory_error="WINDOWS_PROCESS_INVENTORY_UNAVAILABLE")
    listeners = payload.get("listeners") or []
    if isinstance(listeners, int):
        listeners = [listeners]
    command_lines = payload.get("listener_command_lines") or {}
    supervisors = payload.get("supervisors") or []
    if isinstance(supervisors, Mapping):
        supervisors = [supervisors]
    return PortInventory(
        listener_pids=[int(pid) for pid in listeners],
        listener_command_lines={int(key): str(value or "") for key, value in command_lines.items()},
        supervisor_processes=[dict(row) for row in supervisors if isinstance(row, Mapping)],
    )


def store_path_is_protected_backup(store_path: str) -> bool:
    lowered = str(store_path).lower().replace("\\", "/")
    return any(marker.lower() in lowered for marker in PROTECTED_STORE_MARKERS)


def preflight_store_safety(store_path: Path, *, allow_new_store: bool) -> tuple[bool, str]:
    if store_path_is_protected_backup(store_path):
        return False, "BLOCKED_STORE_PATH_IS_PROTECTED_BACKUP"
    if store_path.exists():
        return True, "EXISTING_STORE_REUSED_NEVER_RESET"
    is_production = os.path.normcase(str(store_path)) == os.path.normcase(str(CANONICAL_PRODUCTION_STORE_PATH))
    if is_production:
        return False, "BLOCKED_PRODUCTION_STORE_MISSING_NEVER_CREATE_IMPLICITLY"
    if allow_new_store:
        return True, "ISOLATED_NEW_STORE_AUTHORIZED_BY_SHADOW_FLAG"
    return False, "BLOCKED_STORE_MISSING_NEW_STORE_NOT_AUTHORIZED"


def decide_action(
    *,
    api_base: str,
    store_path: Path,
    inventory: PortInventory,
    allow_new_store: bool = False,
    health: Optional[dict[str, Any]] = None,
    snapshot: Optional[dict[str, Any]] = None,
) -> LaunchDecision:
    if inventory.inventory_error:
        return LaunchDecision(
            outcome="BLOCKED_PROCESS_INVENTORY_UNAVAILABLE",
            reason="The launcher cannot prove who owns the Daily App port; failing closed instead of spawning.",
        )
    store_ok, store_reason = preflight_store_safety(store_path, allow_new_store=allow_new_store)
    canonical_supervisors = [
        row for row in inventory.supervisor_processes
        if is_canonical_daily_app_command_line(str(row.get("cmd") or ""), str(store_path))
    ]
    if len(canonical_supervisors) > 1:
        return LaunchDecision(
            outcome="BLOCKED_MULTIPLE_SUPERVISORS",
            reason="More than one canonical Daily App supervisor process is present; resolve manually, never spawn a third.",
            canonical_supervisor_count=len(canonical_supervisors),
        )
    if inventory.listener_pids:
        port_pid = int(inventory.listener_pids[0])
        command_line = inventory.listener_command_lines.get(port_pid)
        if command_line is None:
            return LaunchDecision(
                outcome="BLOCKED_PORT_OWNER_UNPROVEN",
                reason=f"Port is occupied but the owning process identity (PID {port_pid}) cannot be proven; failing closed.",
                port_pid=port_pid,
                canonical_supervisor_count=len(canonical_supervisors),
            )
        if not is_canonical_daily_app_command_line(command_line, str(store_path)):
            return LaunchDecision(
                outcome="BLOCKED_PORT_OWNER_UNPROVEN",
                reason=f"Port is owned by a process that is not the canonical Daily App for the expected store (PID {port_pid}); failing closed.",
                port_pid=port_pid,
                canonical_supervisor_count=len(canonical_supervisors),
            )
        health = health if health is not None else probe_health(api_base)
        snapshot = snapshot if snapshot is not None else probe_snapshot(api_base)
        kill_switch = bool((snapshot or {}).get("runtime", {}).get("kill_switch_active")) if snapshot else False
        if health and snapshot:
            outcome = "ALREADY_RUNNING_KILL_SWITCH_ACTIVE" if kill_switch else "ALREADY_RUNNING"
            return LaunchDecision(
                outcome=outcome,
                reason="Canonical Daily App is already healthy for the expected production store; no duplicate start.",
                port_pid=port_pid,
                canonical_supervisor_count=max(len(canonical_supervisors), 1),
                kill_switch_active=kill_switch,
                store_identity_canonical=True,
            )
        return LaunchDecision(
            outcome="BLOCKED_SUPERVISOR_PRESENT_API_NOT_HEALTHY",
            reason="A canonical supervisor process owns the port but the loopback API/snapshot is not healthy; not spawning a duplicate. Re-run in a moment or inspect logs.",
            port_pid=port_pid,
            canonical_supervisor_count=max(len(canonical_supervisors), 1),
        )
    if canonical_supervisors:
        return LaunchDecision(
            outcome="BLOCKED_SUPERVISOR_PRESENT_API_NOT_HEALTHY",
            reason="A canonical supervisor process exists but is not listening on the expected port; not spawning a duplicate.",
            canonical_supervisor_count=len(canonical_supervisors),
        )
    if not store_ok:
        return LaunchDecision(outcome=store_reason, reason=f"Start blocked: {store_reason}.")
    return LaunchDecision(
        outcome="START_REQUIRED",
        reason="No canonical Daily App process or port owner detected; one canonical start is safe.",
        may_spawn=True,
        canonical_supervisor_count=0,
    )


def spawn_detached_daily_app(
    command: list[str],
    *,
    working_directory: Path,
    stdout_log: Path,
    stderr_log: Path,
) -> int:
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    with open(stdout_log, "a", encoding="utf-8") as out, open(stderr_log, "a", encoding="utf-8") as err:
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        out.write(f"\n===== one-click launch {stamp} =====\n")
        process = subprocess.Popen(
            [str(part) for part in command],
            cwd=str(working_directory),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            creationflags=DETACHED_CREATION_FLAGS,
            close_fds=True,
        )
    return process.pid


def wait_for_health(api_base: str, *, timeout_seconds: float = 90.0, poll_seconds: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if probe_health(api_base, timeout=3.0):
            return True
        time.sleep(poll_seconds)
    return False


def build_credential_inventory(env: Optional[Mapping[str, str]] = None) -> list[dict[str, Any]]:
    source = dict(os.environ) if env is None else dict(env)

    def presence(name: str) -> bool:
        value = source.get(name)
        return value is not None and str(value).strip() != ""

    groups: list[tuple[str, str, tuple[str, ...]]] = [
        ("9router_gateway", "V1_NOW", ("NINE_ROUTER_API_KEY", "NINE_ROUTER_BASE_URL")),
        ("telegram", "V1_NOW", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID")),
        ("discord_webhook", "V1_NOW", ("DISCORD_SUBSTACK_DROPS_WEBHOOK_URL", "DISCORD_SUBSTACK_DROPS_CHANNEL_ID")),
        ("facebook_page", "V1_NOW", ("FACEBOOK_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID")),
        ("instagram_business", "V1_NOW", ("INSTAGRAM_BUSINESS_ACCOUNT_ID",)),
        ("meta_graph_app", "V1_NOW", ("META_GRAPH_APP_ID", "META_GRAPH_APP_SECRET", "META_GRAPH_BASE_URL", "META_APP_ID", "META_APP_SECRET", "META_USER_ACCESS_TOKEN")),
        ("threads", "V1_NOW", ("THREADS_APP_ID", "THREADS_APP_SECRET", "THREADS_USER_ACCESS_TOKEN", "THREADS_USER_ID")),
        ("substack_nonsecret_binding", "V1_NOW", ("SUBSTACK_PUBLICATION_URL", "SUBSTACK_HANDLE", "SUBSTACK_PUBLICATION_ID", "SUBSTACK_USER_ID")),
        ("youtube_community_nonsecret_binding", "V1_NOW", ("YOUTUBE_CHANNEL_ID",)),
        ("youtube_video_upload_oauth", "V2_LATER", ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_SECRETS_JSON_PATH")),
        ("tiktok_video", "V2_LATER", ("CONTENTOPS_TIKTOK_APP_ID", "CONTENTOPS_TIKTOK_CLIENT_KEY", "CONTENTOPS_TIKTOK_CLIENT_SECRET", "CONTENTOPS_TIKTOK_ACCESS_TOKEN", "CONTENTOPS_TIKTOK_REFRESH_TOKEN")),
        ("x_official_api", "OPTIONAL", ("X_CLIENT_ID", "X_CLIENT_SECRET", "X_ACCESS_TOKEN", "X_REFRESH_TOKEN", "X_USER_ID")),
        ("linkedin_official_api", "OPTIONAL", ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_MEMBER_URN", "LINKEDIN_ORGANIZATION_URN")),
        ("vertex_reference_only", "OPTIONAL", ("GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID", "VERTEX_SERVICE_ACCOUNT_EMAIL")),
    ]
    rows: list[dict[str, Any]] = []
    for group, scope, names in groups:
        for name in names:
            rows.append({
                "group": group,
                "scope": scope,
                "variable": name,
                "state": "PRESENT" if presence(name) else "MISSING",
            })
    return rows


def render_credential_inventory(rows: list[dict[str, Any]]) -> str:
    lines = []
    for row in rows:
        lines.append(f"{row['variable']}={row['state']}  [{row['scope']} {row['group']}]")
    return "\n".join(lines)


def summarize_browser_state(snapshot: Optional[dict[str, Any]]) -> dict[str, Any]:
    chrome = probe_cdp(INGESTION_CDP_PORT)
    edge = probe_cdp(PUBLISHING_CDP_PORT)
    destinations = ((snapshot or {}).get("platforms") or {}).get("destinations") or []
    reauth_surfaces = sorted({
        str(row.get("surface") or row.get("platform_id") or "UNKNOWN")
        for row in destinations
        if str(row.get("readiness") or "") in REAUTH_READINESS_STATES
    })
    ready_surfaces = sorted({
        str(row.get("surface") or row.get("platform_id") or "UNKNOWN")
        for row in destinations
        if str(row.get("readiness") or "") in {"READY_AUTHENTICATED", "READY_NON_BROWSER_BINDING"}
    })
    if edge["cdp_alive"] and not reauth_surfaces and ready_surfaces:
        edge_state = "READY"
    elif edge["cdp_alive"] and reauth_surfaces:
        edge_state = "REAUTH_REQUIRED"
    elif edge["cdp_alive"]:
        edge_state = "READY_NO_DESTINATION_READINESS_RECORDED"
    else:
        edge_state = "UNAVAILABLE"
    return {
        "chrome_9222_ingestion_only": "READY" if chrome["cdp_alive"] else "UNAVAILABLE",
        "edge_9223_publishing_only": edge_state,
        "edge_reauth_surfaces": reauth_surfaces,
        "edge_ready_surfaces": ready_surfaces,
        "browser_roles_separated": True,
    }


def ensure_ui(
    *,
    enabled: bool,
    log_root: Path,
    snapshot_available: bool,
) -> dict[str, Any]:
    if not enabled:
        return {"status": "SKIPPED", "url": None, "mechanism": None, "pid": None}
    for port in (UI_PREVIEW_PORT, UI_DEV_PORT):
        if _http_get_json(f"http://127.0.0.1:{port}/", timeout=2.0) is not None or _url_ok(f"http://127.0.0.1:{port}/"):
            return {"status": "ALREADY_READY", "url": f"http://127.0.0.1:{port}/", "mechanism": "existing_loopback_server", "pid": None}
    if not UI_DIR.exists():
        return {"status": "UNAVAILABLE", "url": None, "mechanism": "UI_DIR_MISSING", "pid": None}
    dist_marker = UI_DIR / "dist" / "index.html"
    if dist_marker.exists():
        script, port = "preview", UI_PREVIEW_PORT
    else:
        script, port = "dev", UI_DEV_PORT
    command = [
        "cmd", "/c", "npm", "run", script, "--",
        "--host", "127.0.0.1", "--port", str(port), "--strictPort",
    ]
    log_root.mkdir(parents=True, exist_ok=True)
    ui_log = log_root / "v5_ui_server.log"
    try:
        with open(ui_log, "a", encoding="utf-8") as out:
            out.write(f"\n===== one-click UI start {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} =====\n")
            process = subprocess.Popen(
                command,
                cwd=str(UI_DIR),
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=subprocess.STDOUT,
                creationflags=DETACHED_CREATION_FLAGS,
                close_fds=True,
            )
    except OSError as exc:
        return {"status": "UNAVAILABLE", "url": None, "mechanism": f"UI_SPAWN_FAILED:{type(exc).__name__}", "pid": None}
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if _url_ok(url):
            return {"status": "READY", "url": url, "mechanism": f"npm_run_{script}_detached", "pid": process.pid}
        time.sleep(1.0)
    return {"status": "UNAVAILABLE", "url": url, "mechanism": f"npm_run_{script}_not_ready_within_30s", "pid": process.pid}


def _url_ok(url: str, *, timeout: float = 2.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def render_summary(
    *,
    decision: LaunchDecision,
    snapshot: Optional[dict[str, Any]],
    browser_state: dict[str, Any],
    ui_state: dict[str, Any],
    store_path: Path,
    store_exists: bool,
    schema_version: Any,
    inventory_report: str,
) -> str:
    runtime = (snapshot or {}).get("runtime") or {}
    published = (snapshot or {}).get("published") or {}
    authority = (snapshot or {}).get("authority") or {}
    unknown_write_count = published.get("unknown_write_count", 0 if snapshot else "UNAVAILABLE")
    pending_count = published.get("pending_readback_count", 0 if snapshot else "UNAVAILABLE")
    kill_switch = "ACTIVE" if (decision.kill_switch_active or runtime.get("kill_switch_active")) else "CLEAR"
    if decision.outcome.startswith("BLOCKED"):
        daily_app_state = "BLOCKED"
    elif decision.outcome == "ALREADY_RUNNING_KILL_SWITCH_ACTIVE":
        daily_app_state = "RUNNING_KILL_SWITCH_ACTIVE"
    elif decision.outcome == "ALREADY_RUNNING":
        daily_app_state = "ALREADY_RUNNING"
    elif decision.outcome == "STARTED":
        daily_app_state = "STARTED"
    elif decision.outcome == "STARTED_KILL_SWITCH_ACTIVE":
        daily_app_state = "STARTED_RUNNING_KILL_SWITCH_ACTIVE"
    elif decision.outcome == "START_REQUIRED":
        daily_app_state = "STARTED" if snapshot else "START_REQUESTED"
    else:
        daily_app_state = decision.outcome
    lines = [
        "Capital Chronicle ContentOps V1",
        "",
        f"Daily App: {daily_app_state}",
        f"Controller: {runtime.get('controller_health', 'UNAVAILABLE' if not snapshot else 'UNKNOWN')}",
        f"Mode: {runtime.get('operating_mode', 'UNAVAILABLE')}",
        f"Kill Switch: {kill_switch}",
        f"Store: schema {authority.get('store_schema_version', schema_version if schema_version is not None else 'unknown')} / integrity NOT_PROBED_BY_LAUNCHER",
        f"Store Path: {store_path} ({'REUSED' if store_exists else 'ABSENT'})",
        f"Next Wake: {runtime.get('next_wake_utc', 'UNAVAILABLE')}",
        f"Chrome 9222 Ingestion: {browser_state['chrome_9222_ingestion_only']}",
        f"Edge 9223 Publishing: {browser_state['edge_9223_publishing_only']}",
        f"V5 UI: {ui_state['status']}" + (f" ({ui_state['url']})" if ui_state.get("url") else ""),
        f"Unknown Write: {unknown_write_count}",
        f"Pending Reconciliation: {pending_count}",
        "",
        f"Decision: {decision.outcome} - {decision.reason}",
        f"Supervisors Detected: {decision.canonical_supervisor_count}",
        "",
        "Credential/capability preflight (names and presence only, no values):",
        inventory_report,
        "",
        "Browser roles: Chrome 9222 = ingestion only; Edge 9223 = publishing/readback only.",
        "Host downtime is external availability loss, not database failure; durable state was never reset.",
    ]
    if decision.outcome.startswith("BLOCKED"):
        lines.append("No process was started or killed by this launcher. Inspect and re-run.")
    return "\n".join(lines)


SECRET_NAME_PATTERN = re.compile(r"(TOKEN|SECRET|API_?KEY|WEBHOOK|PASSWORD|PASSWD|CREDENTIAL)", re.IGNORECASE)


def _redaction_guard(text: str, env: Optional[Mapping[str, str]] = None) -> str:
    source = dict(os.environ) if env is None else dict(env)
    for name, value in source.items():
        if not SECRET_NAME_PATTERN.search(name):
            continue
        if value and len(value) >= 12 and value in text:
            raise LauncherError(f"refusing to emit output containing material resembling env value for {name}")
    return text


def run_launcher(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-click launch/resume for the canonical ContentOps Daily App")
    parser.add_argument("--store-path", default=str(CANONICAL_PRODUCTION_STORE_PATH))
    parser.add_argument("--output-root", default=str(CANONICAL_PRODUCTION_OUTPUT_ROOT))
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    parser.add_argument("--log-root", default=str(LAUNCHER_LOG_ROOT_DEFAULT))
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--no-open-browser", action="store_true")
    parser.add_argument("--allow-new-store", action="store_true", help="Isolated shadow/test stores only; never for the production path")
    parser.add_argument("--shadow-smoke", action="store_true", help="Controlled no-write isolated smoke: implies --allow-new-store --no-ui --no-open-browser and passes --skip-edge-bootstrap")
    parser.add_argument("--start-timeout-seconds", type=float, default=90.0)
    args = parser.parse_args(argv)

    if args.shadow_smoke:
        args.allow_new_store = True
        args.no_ui = True
        args.no_open_browser = True

    store_path = Path(args.store_path)
    output_root = Path(args.output_root)
    log_root = Path(args.log_root)
    api_base = f"http://127.0.0.1:{int(args.api_port)}"

    inventory = collect_port_inventory(args.api_port)
    decision = decide_action(api_base=api_base, store_path=store_path, inventory=inventory, allow_new_store=args.allow_new_store)

    spawned_pid: Optional[int] = None
    snapshot: Optional[dict[str, Any]] = None
    schema_version: Any = None

    if decision.outcome == "START_REQUIRED" and decision.may_spawn:
        command = build_canonical_daily_app_command(
            python_executable=sys.executable,
            store_path=str(store_path),
            output_root=str(output_root),
            api_port=args.api_port,
            skip_edge_bootstrap=bool(args.shadow_smoke),
        )
        stdout_log = log_root / "daily_app.supervisor.stdout.log"
        stderr_log = log_root / "daily_app.supervisor.stderr.log"
        spawned_pid = spawn_detached_daily_app(
            command,
            working_directory=REPO_ROOT,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )
        if wait_for_health(api_base, timeout_seconds=args.start_timeout_seconds):
            snapshot = probe_snapshot(api_base)
            post = collect_port_inventory(args.api_port)
            post_canonical = [row for row in post.supervisor_processes if is_canonical_daily_app_command_line(str(row.get("cmd") or ""), str(store_path))]
            if len(post_canonical) > 1:
                _stop_pid(spawned_pid)
                print(_redaction_guard(
                    "BLOCKED_DUPLICATE_SUPERVISOR_RACE: the launcher-spawned process was stopped; "
                    "exactly-one-supervisor invariant restored. No public write authority was exercised."
                ))
                return 2
            decision = LaunchDecision(
                outcome="STARTED_KILL_SWITCH_ACTIVE" if bool((snapshot or {}).get("runtime", {}).get("kill_switch_active")) else "STARTED",
                reason="Canonical Daily App was started detached by this launcher and is healthy.",
                port_pid=spawned_pid,
                canonical_supervisor_count=max(len(post_canonical), 1),
                kill_switch_active=bool((snapshot or {}).get("runtime", {}).get("kill_switch_active")),
                store_identity_canonical=True,
            )
        else:
            print(_redaction_guard(
                f"BLOCKED_START_NOT_HEALTHY_WITHIN_{int(args.start_timeout_seconds)}S: the detached process (PID {spawned_pid}) "
                f"did not expose a healthy loopback API. See {stderr_log}. The launcher will not retry automatically."
            ))
            return 2
    elif decision.outcome in {"ALREADY_RUNNING", "ALREADY_RUNNING_KILL_SWITCH_ACTIVE"}:
        snapshot = probe_snapshot(api_base)

    if snapshot:
        schema_version = (snapshot.get("authority") or {}).get("store_schema_version")

    browser_state = summarize_browser_state(snapshot)
    ui_state = ensure_ui(enabled=not args.no_ui, log_root=log_root, snapshot_available=snapshot is not None)
    if ui_state["status"] in {"READY", "ALREADY_READY"} and ui_state["url"] and not args.no_open_browser:
        try:
            os.startfile(ui_state["url"])  # noqa: S606 - local URL in operator default browser
        except OSError:
            ui_state["status"] = f"{ui_state['status']}_BROWSER_OPEN_FAILED"

    inventory_report = render_credential_inventory(build_credential_inventory())
    summary = render_summary(
        decision=decision,
        snapshot=snapshot,
        browser_state=browser_state,
        ui_state=ui_state,
        store_path=store_path,
        store_exists=store_path.exists(),
        schema_version=schema_version,
        inventory_report=inventory_report,
    )
    print(_redaction_guard(summary))
    return 0 if decision.outcome in {
        "ALREADY_RUNNING",
        "ALREADY_RUNNING_KILL_SWITCH_ACTIVE",
        "STARTED",
        "STARTED_KILL_SWITCH_ACTIVE",
    } else 2


def _stop_pid(pid: int) -> None:
    try:
        subprocess.run(["taskkill.exe", "/PID", str(int(pid)), "/F"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        pass


if __name__ == "__main__":
    raise SystemExit(run_launcher())
