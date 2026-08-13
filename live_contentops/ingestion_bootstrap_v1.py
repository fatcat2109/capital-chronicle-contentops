"""Canonical Chrome `CapitalChronicleBot` CDP 9222 ingestion bootstrap (read-only safety).

This module reuses the EXISTING dedicated ingestion browser binding accepted in historical
evidence (`current_x_reauthentication_blocker_evidence_v1.json`): the exact dedicated profile
at `%LOCALAPPDATA%\\Google\\Chrome\\User Data\\CapitalChronicleBot`, started with
`--remote-debugging-port=9222` exactly as the accepted `Launch_Dashboard.bat` dedicated
ingestion command does.

Role authority is hardcoded and immutable:

- Chrome `CapitalChronicleBot` on CDP 9222 = HEADLINE/X INGESTION ONLY.
- Microsoft Edge `contentops-social-main` on CDP 9223 = publishing/media/readback only.

This module never creates/clones/resets/deletes a profile, never reads cookies/storage/tokens,
never types credentials, never automates login, and never uses Chrome 9222 for publication.
Authentication state is only observed through canonical visible-URL login-redirect markers,
the same method accepted historical evidence used.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

INGESTION_CDP_PORT = 9222
PUBLISHING_CDP_PORT = 9223
INGESTION_PROFILE_NAME = "CapitalChronicleBot"
CANONICAL_INGESTION_ROUTE = "https://x.com/i/lists/1843870469143048642"
LOGIN_REDIRECT_MARKERS = (
    "/i/jf/onboarding",
    "redirect_after_login",
    "mode=login",
    "x.com/i/flow/login",
    "/login?",
)

#: Permanent single-source canonical X ingestion binding (owner-locked 2026-08-10).
#: ContentOps must ALWAYS reuse this exact operator-owned persistent profile and must NEVER
#: create, clone, migrate, reset, clean, replace, rename, delete, or silently fall back from
#: it. Missing/unusable binding fails closed. There is no alternate path, no fallback profile,
#: no Default/personal Chrome fallback, and no Edge fallback for ingestion. Provider-side
#: session expiration may require operator reauthentication in this same profile only.
CANONICAL_INGESTION_BINDING = {
    "browser_family": "CHROME",
    "profile_id": "CapitalChronicleBot",
    "cdp_port": 9222,
    "role": "INGESTION_ONLY",
    "user_data_dir": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\CapitalChronicleBot",
    "canonical_route": "https://x.com/i/lists/1843870469143048642",
    "profile_binding_locked": True,
    "fallback_profile_available": False,
}

STATE_READY = "READY"
STATE_REAUTH_REQUIRED = "REAUTH_REQUIRED"
STATE_AUTH_UNVERIFIED = "READY_AUTH_UNVERIFIED"
STATE_UNAVAILABLE = "UNAVAILABLE"
STATE_RUNNING_WITHOUT_CDP = "RUNNING_WITHOUT_CDP"
STATE_PORT_OWNER_UNPROVEN = "PORT_OWNER_UNPROVEN"
STATE_LAUNCHED = "LAUNCHED"
STATE_ALREADY_READY = "ALREADY_READY"
STATE_LAUNCH_FAILED = "LAUNCH_FAILED"
STATE_BINARY_NOT_FOUND = "BINARY_NOT_FOUND"
STATE_PROFILE_BINDING_MISSING = "PROFILE_BINDING_MISSING"
BINDING_LOCKED = "LOCKED"


class IngestionBootstrapError(RuntimeError):
    pass


def canonical_ingestion_user_data_dir(env: Optional[Mapping[str, str]] = None) -> Path:
    source = dict(os.environ) if env is None else dict(env)
    local_app_data = source.get("LOCALAPPDATA") or ""
    if not local_app_data:
        raise IngestionBootstrapError("LOCALAPPDATA_UNAVAILABLE")
    return Path(local_app_data) / "Google" / "Chrome" / "User Data" / INGESTION_PROFILE_NAME


def find_chrome_binary(env: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    source = dict(os.environ) if env is None else dict(env)
    candidates = [
        Path(source.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(source.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(source.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe" if source.get("LOCALAPPDATA") else None,
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def _http_get_json(url: str, *, timeout: float) -> Optional[Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def probe_cdp(port: int, *, timeout: float = 3.0) -> dict[str, Any]:
    payload = _http_get_json(f"http://127.0.0.1:{port}/json/version", timeout=timeout)
    if not isinstance(payload, Mapping):
        return {"cdp_alive": False, "browser": None}
    return {"cdp_alive": True, "browser": str(payload.get("Browser") or "")}


def cdp_target_urls(port: int, *, timeout: float = 3.0) -> list[str]:
    payload = _http_get_json(f"http://127.0.0.1:{port}/json/list", timeout=timeout)
    if not isinstance(payload, list):
        return []
    return [str(row.get("url") or "") for row in payload if isinstance(row, Mapping)]


def _powershell_json(script: str, *, timeout: float = 25.0) -> Optional[dict[str, Any]]:
    import subprocess

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


def _is_ingestion_command_line(command_line: str, profile_dir: Path) -> bool:
    if not command_line:
        return False
    lowered = command_line.lower().replace('"', "")
    profile = str(profile_dir).lower().replace('"', "")
    return "chrome" in lowered and profile in lowered


def ingestion_process_state(
    *,
    env: Optional[Mapping[str, str]] = None,
    cdp_port: int = INGESTION_CDP_PORT,
) -> dict[str, Any]:
    """Classify the current Chrome 9222 ingestion runtime without touching any session data."""
    profile_dir = canonical_ingestion_user_data_dir(env)
    cdp = probe_cdp(cdp_port)
    if cdp["cdp_alive"]:
        inventory = _powershell_json(
            "$ErrorActionPreference='SilentlyContinue';"
            f"$conn=Get-NetTCPConnection -LocalPort {int(cdp_port)} -State Listen | Select-Object -First 1;"
            "if($conn){$proc=Get-CimInstance Win32_Process -Filter ('ProcessId='+$conn.OwningProcess);"
            "@{ pid = $conn.OwningProcess; cmd = $proc.CommandLine } | ConvertTo-Json -Compress}"
            "else{@{ pid = $null; cmd = $null } | ConvertTo-Json -Compress}"
        )
        owner_pid = None
        owner_cmd = ""
        if inventory is not None:
            owner_pid = inventory.get("pid")
            owner_cmd = str(inventory.get("cmd") or "")
        if owner_pid is None and owner_cmd == "":
            return {"state": STATE_UNAVAILABLE, "detail": "CDP_LISTENER_OWNER_NOT_RESOLVED", "pid": None}
        if not _is_ingestion_command_line(owner_cmd, profile_dir):
            return {"state": STATE_PORT_OWNER_UNPROVEN, "detail": "PORT_9222_OWNED_BY_NON_CANONICAL_PROCESS", "pid": owner_pid}
        return {"state": STATE_READY, "detail": "CANONICAL_INGESTION_PROFILE_ON_CDP_9222", "pid": owner_pid}
    chrome_processes = _powershell_json(
        "$ErrorActionPreference='SilentlyContinue';"
        "@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\""
        " | Where-Object { $_.CommandLine -like '*CapitalChronicleBot*' }"
        " | Select-Object -ExpandProperty ProcessId) | ConvertTo-Json -Compress"
    )
    pids = chrome_processes if isinstance(chrome_processes, list) else []
    if pids:
        return {"state": STATE_RUNNING_WITHOUT_CDP, "detail": "CANONICAL_PROFILE_ACTIVE_WITHOUT_CDP_9222", "pid": pids[0]}
    return {"state": STATE_UNAVAILABLE, "detail": "NO_CANONICAL_INGESTION_BROWSER_RUNNING", "pid": None}


def _launch_canonical_ingestion_browser(
    *,
    env: Optional[Mapping[str, str]] = None,
    cdp_port: int = INGESTION_CDP_PORT,
) -> dict[str, Any]:
    import subprocess

    from live_contentops.daily_app_launcher_v1 import DETACHED_CREATION_FLAGS

    binary = find_chrome_binary(env)
    if binary is None:
        return {"state": STATE_BINARY_NOT_FOUND, "detail": "GOOGLE_CHROME_BINARY_NOT_FOUND", "pid": None}
    profile_dir = canonical_ingestion_user_data_dir(env)
    if not profile_dir.exists():
        # Fail closed. The exact operator-owned profile must already exist; ContentOps never
        # creates, clones, or replaces it.
        return {"state": STATE_PROFILE_BINDING_MISSING, "detail": "EXISTING_DEDICATED_PROFILE_MISSING_NEVER_CREATED", "pid": None}
    command = [str(binary), f"--remote-debugging-port={int(cdp_port)}", f"--user-data-dir={profile_dir}"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=DETACHED_CREATION_FLAGS,
        close_fds=True,
    )
    return {"state": STATE_LAUNCHED, "detail": "EXISTING_DEDICATED_INGESTION_PROFILE_STARTED", "pid": process.pid}


def ensure_ingestion_runtime(
    *,
    env: Optional[Mapping[str, str]] = None,
    wait_seconds: float = 18.0,
    cdp_port: int = INGESTION_CDP_PORT,
) -> dict[str, Any]:
    """Idempotent bootstrap: reuse a canonical CDP 9222 owner, else start the exact profile once.

    Profile continuity lock: the binding directory must already exist. If it is missing this
    returns PROFILE_BINDING_MISSING and never creates any directory or replacement profile.
    """
    profile_dir = canonical_ingestion_user_data_dir(env)
    if not profile_dir.exists():
        return {
            "state": STATE_PROFILE_BINDING_MISSING,
            "status": STATE_PROFILE_BINDING_MISSING,
            "detail": "EXISTING_DEDICATED_PROFILE_MISSING_NEVER_CREATED",
            "launched": False,
            "pid": None,
        }
    current = ingestion_process_state(env=env, cdp_port=cdp_port)
    if current["state"] == STATE_READY:
        return {**current, "status": STATE_ALREADY_READY, "launched": False}
    if current["state"] in {STATE_PORT_OWNER_UNPROVEN, STATE_RUNNING_WITHOUT_CDP}:
        return {**current, "status": current["state"], "launched": False}
    launched = _launch_canonical_ingestion_browser(env=env, cdp_port=cdp_port)
    if launched["state"] != STATE_LAUNCHED:
        return {**launched, "status": launched["state"], "launched": False}
    deadline = time.monotonic() + max(wait_seconds, 1.0)
    while time.monotonic() < deadline:
        time.sleep(0.75)
        recheck = ingestion_process_state(env=env, cdp_port=cdp_port)
        if recheck["state"] == STATE_READY:
            return {**recheck, "status": STATE_LAUNCHED, "launched": True, "pid": launched["pid"]}
        if recheck["state"] == STATE_PORT_OWNER_UNPROVEN:
            return {**recheck, "status": STATE_PORT_OWNER_UNPROVEN, "launched": True}
    return {"state": STATE_LAUNCH_FAILED, "detail": "CDP_9222_NOT_READY_WITHIN_BOUNDED_WAIT", "launched": True, "pid": launched["pid"]}


def probe_ingestion_session(
    *,
    cdp_port: int = INGESTION_CDP_PORT,
    timeout_seconds: float = 25.0,
) -> dict[str, Any]:
    """Observe the canonical X ingestion route's visible URL for login-redirect markers.

    This mirrors the accepted historical evidence method (`LOGIN_REDIRECT_OBSERVED`). It opens or
    reuses a target on the canonical ingestion route only; it never reads cookies, storage,
    tokens, or typing credentials.
    """
    if not probe_cdp(cdp_port)["cdp_alive"]:
        return {"auth_state": STATE_UNAVAILABLE, "detail": "CDP_NOT_ALIVE"}
    routes = [url for url in cdp_target_urls(cdp_port) if "x.com/i/lists/1843870469143048642" in url]
    if not routes:
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{cdp_port}/json/new?{CANONICAL_INGESTION_ROUTE}",
                method="PUT",
            )
            with urllib.request.urlopen(request, timeout=5.0) as response:
                response.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            return {"auth_state": STATE_AUTH_UNVERIFIED, "detail": "COULD_NOT_OPEN_CANONICAL_INGESTION_ROUTE"}
    deadline = time.monotonic() + max(timeout_seconds, 1.0)
    observed: list[str] = []
    while time.monotonic() < deadline:
        time.sleep(2.0)
        urls = cdp_target_urls(cdp_port)
        list_urls = [url for url in urls if "x.com" in url]
        observed = list_urls
        for url in list_urls:
            if any(marker in url for marker in LOGIN_REDIRECT_MARKERS):
                return {
                    "auth_state": STATE_REAUTH_REQUIRED,
                    "detail": "LOGIN_REDIRECT_OBSERVED",
                    "observed_marker_url_class": "X_LOGIN_REDIRECT",
                }
        if any("x.com/i/lists/1843870469143048642" in url for url in list_urls):
            return {"auth_state": STATE_READY, "detail": "CANONICAL_LIST_ROUTE_ACTIVE_NO_LOGIN_REDIRECT"}
    return {
        "auth_state": STATE_AUTH_UNVERIFIED,
        "detail": "SESSION_PROBE_INCONCLUSIVE_WITHIN_BOUNDED_WAIT",
        "observed_x_target_count": len(observed),
    }


def one_click_ingestion_bootstrap(
    *,
    env: Optional[Mapping[str, str]] = None,
    probe_session: bool = True,
) -> dict[str, Any]:
    """Launcher-facing flow: ensure the exact ingestion browser, then (optionally) check session."""
    runtime = ensure_ingestion_runtime(env=env)
    if runtime.get("status") not in {STATE_ALREADY_READY, STATE_LAUNCHED}:
        return runtime
    if not probe_session:
        return runtime
    session = probe_ingestion_session()
    runtime["auth_state"] = session["auth_state"]
    runtime["auth_detail"] = session.get("detail")
    return runtime


def canonical_ingestion_readiness(
    *,
    env: Optional[Mapping[str, str]] = None,
    session_timeout_seconds: float = 25.0,
) -> dict[str, Any]:
    """Single-source readiness for the locked canonical ingestion binding.

    Returns:
      chrome_profile_binding: LOCKED (always the exact operator-owned binding; never replaced)
        or PROFILE_BINDING_MISSING (fail closed; nothing is ever created).
      chrome_9222_ingestion: READY | REAUTH_REQUIRED | READY_AUTH_UNVERIFIED | UNAVAILABLE |
        RUNNING_WITHOUT_CDP | PORT_OWNER_UNPROVEN | PROFILE_BINDING_MISSING | LAUNCH_FAILED.
      x_ingestion_session: the canonical-route visible-URL auth classification.
    """
    profile_dir = canonical_ingestion_user_data_dir(env)
    binding_state = BINDING_LOCKED if profile_dir.exists() else STATE_PROFILE_BINDING_MISSING
    result: dict[str, Any] = {
        "canonical_ingestion_binding": dict(CANONICAL_INGESTION_BINDING),
        "chrome_profile_binding": binding_state,
        "fallback_profile_available": False,
        "profile_created_or_replaced": False,
    }
    runtime = ensure_ingestion_runtime(env=env)
    status = runtime.get("status") or runtime.get("state")
    if status not in {STATE_ALREADY_READY, STATE_LAUNCHED}:
        result["chrome_9222_ingestion"] = status or STATE_UNAVAILABLE
        result["x_ingestion_session"] = runtime.get("detail") or status or STATE_UNAVAILABLE
        result["detail"] = runtime.get("detail")
        return result
    session = probe_ingestion_session(timeout_seconds=session_timeout_seconds)
    auth_state = session["auth_state"]
    if auth_state == STATE_READY:
        result["chrome_9222_ingestion"] = STATE_READY
    elif auth_state == STATE_REAUTH_REQUIRED:
        result["chrome_9222_ingestion"] = STATE_REAUTH_REQUIRED
    elif auth_state == STATE_AUTH_UNVERIFIED:
        result["chrome_9222_ingestion"] = STATE_AUTH_UNVERIFIED
    else:
        result["chrome_9222_ingestion"] = STATE_UNAVAILABLE
    result["x_ingestion_session"] = auth_state
    result["session_detail"] = session.get("detail")
    result["launched"] = bool(runtime.get("launched"))
    return result


def passive_canonical_ingestion_readiness(
    *, env: Optional[Mapping[str, str]] = None
) -> dict[str, Any]:
    """Startup/audit readiness from process/profile/CDP metadata only.

    Never launches Chrome, opens a tab, classifies a page URL, navigates, reloads, or captures.
    The due low-frequency ingestion iteration owns the JIT ensure/session/capture sequence.
    """

    profile_dir = canonical_ingestion_user_data_dir(env)
    state = ingestion_process_state(env=env)
    return {
        "canonical_ingestion_binding": dict(CANONICAL_INGESTION_BINDING),
        "chrome_profile_binding": BINDING_LOCKED if profile_dir.exists() else STATE_PROFILE_BINDING_MISSING,
        "chrome_9222_ingestion": str(state.get("state") or STATE_UNAVAILABLE),
        "x_ingestion_session": "PASSIVE_NOT_PROBED",
        "detail": str(state.get("detail") or STATE_UNAVAILABLE),
        "launched": False,
        "browser_navigation_performed": False,
        "capture_performed": False,
    }
