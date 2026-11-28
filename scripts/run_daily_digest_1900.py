"""CC-143 / CC-855: the 19:00 GMT+7 daily email digest route, with zero Claude or agy dependency.

The digest owner is unchanged (live_contentops/substack_daily_digest_v1.py): it copies
confirmed public titles and links only and authors no analysis. After the Fri 04 Dec 2026
permanent Claude Code sunset (CC-855 / Decision 184), this script runs unattended from
Windows Task Scheduler (`CapitalChronicle-ContentOpsDailyDigest1900-V1`) through:

  run        OS-lock-guarded unattended 19:15 GMT+7 runner. Defaults to deterministic
             Python over the local BrowserOS Neo MCP endpoint (`--driver python-neo`,
             surface=NEO_ENDPOINT_EXECUTOR, tool=browseros-neo/run, zero LLM quota).
             Optional `--driver codex-astra` invokes `codex exec` on `gpt-6.2-astra` max
             serialized behind `codex-launch-slot.txt` (surface=CODEX_EXEC). Always runs
             CC-639/CC-690 evening readback after writing `result.json`.
  preflight  Reads only. Is the digest due (19:00 GMT+7 passed today), is the
             publication path open (no LLM operator pause, AUTONOMOUS_DEFAULT,
             live rollout, feed present), and which exact commands continue it.
  resume     Calls the existing digest owner (`prepare_daily_digest` + `continue_daily_digest`),
             guarded against an early wake. Never claims a request.
  dry-run    Copies the production store into a scratch folder, freezes the
             digest there and drives the existing coordinator to its first
             native Neo request. Writes outside the scratch folder and network
             connections are refused and counted. Publishes nothing.
  render-xml Emits the disabled-by-default Windows Task Scheduler XML (`<Enabled>false</Enabled>`).

Zero Claude Desktop / `claude.exe` / `agy` CLI invocations. Honest C5 provenance throughout.
"""
from __future__ import annotations

import argparse
import builtins
import contextlib
import inspect
import io
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time as time_mod
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BANGKOK = timezone(timedelta(hours=7))
DUE_LOCAL = time(19, 0)
DEFAULT_ROLLOUT = ROOT / "config" / "native_desktop_rollout_v1.json"
CLI = "scripts/run_native_desktop_editorial.py"

# Fri 04 Dec 2026 00:00 GMT+7 == 2026-12-03T17:00:00Z (CC-855 permanent Claude Code sunset).
CLAUDE_SUNSET_UTC = datetime(2026, 12, 3, 17, 0, tzinfo=timezone.utc)
DEFAULT_DRIVER = "python-neo"

ROUTE_PROFILES: dict[str, dict[str, str | None]] = {
    "python-neo": {
        "driver": "python-neo",
        "route": "WINDOWS_SCHEDULER_PYTHON_NEO_1900",
        "surface": "NEO_ENDPOINT_EXECUTOR",
        "tool_name": "browseros-neo/run",
        "invocation_prefix": "windows-scheduler-neo:cc143-digest-1900:",
        "observation_source": "BROWSEROS_NEO_LOCAL_MCP_ENDPOINT",
        "model": None,
        "reasoning_effort": None,
    },
    "codex-astra": {
        "driver": "codex-astra",
        "route": "WINDOWS_SCHEDULER_CODEX_ASTRA_1900",
        "surface": "CODEX_EXEC",
        "tool_name": "mcp__browseros_neo__run",
        "invocation_prefix": "codex-exec-astra:cc143-digest-1900:",
        "observation_source": "BROWSEROS_NEO",
        "model": "gpt-6.2-astra",
        "reasoning_effort": "max",
    },
    "codex-desktop": {
        "driver": "codex-desktop",
        "route": "CODEX_DESKTOP_TASK_1900",
        "surface": "CODEX_DESKTOP_CONVERSATION",
        "tool_name": "mcp__browseros_neo__run",
        "invocation_prefix": "codex-desktop:cc143-digest-1900:",
        "observation_source": "BROWSEROS_NEO",
        "model": "gpt-6.2-sol",
        "reasoning_effort": "low",
    },
}

SURFACE = str(ROUTE_PROFILES[DEFAULT_DRIVER]["surface"])
TOOL = str(ROUTE_PROFILES[DEFAULT_DRIVER]["tool_name"])
DEFAULT_ROUTE = str(ROUTE_PROFILES[DEFAULT_DRIVER]["route"])
OBSERVATION_SOURCE = str(ROUTE_PROFILES[DEFAULT_DRIVER]["observation_source"])
SCHEDULED_INVOCATION_PREFIX = str(ROUTE_PROFILES[DEFAULT_DRIVER]["invocation_prefix"])

# Retain historical Claude prefix ONLY for read-only route-1900/<stamp> replay recognition.
_LEGACY_CLAUDE_PREFIX = "claude-code-session:cc143-digest-1900:"
_SCHEDULED_INVOCATION_PREFIXES = tuple(
    dict.fromkeys([*(str(p["invocation_prefix"]) for p in ROUTE_PROFILES.values()), _LEGACY_CLAUDE_PREFIX])
)

DEFAULT_LOCK_PATH = Path(r"A:\Capital Chronicle\Runtime\ContentOps\locks\cc143_digest_1900.lock")
DEFAULT_STOP_PATH = Path(r"A:\Capital Chronicle\Runtime\ContentOps\control\digest-1900.stop")
DEFAULT_NEO_ENDPOINT = "http://127.0.0.1:9010/mcp"
DEFAULT_NEO_GROUP = "Capital Chronicle/CC-143 digest"
MAX_REQUESTS_PER_RUN = 8

CODEX_LAUNCH_SLOT_FILE = Path(
    r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec\codex-launch-slot.txt"
)
CODEX_LAUNCH_SLOT_ENV = "CC_CODEX_LAUNCH_SLOT_FILE"
CODEX_LAUNCH_SLOT_GAP_SECONDS = 90.0
CODEX_LAUNCH_SLOT_GAP_ENV = "CC_CODEX_LAUNCH_SLOT_GAP_SECONDS"
_SLOT_SHARE_RETRIES = 600
_SLOT_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)")


def resolve_profile(driver: str | None = None) -> dict[str, str | None]:
    """Return the validated C5 route profile; refuse retired Claude or forbidden agy routes."""
    chosen = (driver or DEFAULT_DRIVER).strip().lower()
    if chosen in {"claude", "claude-cli", "claude-desktop", "claude-code", "claude-legacy"}:
        raise ValueError("CLAUDE_ROUTE_RETIRED_CC855")
    if chosen in {"agy", "antigravity", "antigravity-cli"}:
        raise ValueError("AGY_BLOCKED_TERMS_OF_SERVICE_20261124")
    if chosen not in ROUTE_PROFILES:
        raise ValueError("DIGEST_1900_DRIVER_INVALID:" + chosen)
    profile = dict(ROUTE_PROFILES[chosen])
    from live_contentops.native_neo_executor_v1 import SURFACE_TOOLS

    if SURFACE_TOOLS.get(str(profile["surface"])) != profile["tool_name"]:
        raise ValueError("DIGEST_1900_SURFACE_TOOL_MISMATCH")
    return profile


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("EXPLICIT_DIGEST_CLOCK_REQUIRED")
    return parsed.astimezone(timezone.utc)


def due_state(now: datetime) -> dict:
    """The digest for day D is frozen at D 19:00 GMT+7. Before that instant the
    owner returns day D-1's packet, so an early wake must not continue it (the
    4 Nov Codex window entered at 18:59:59.78 and saw only the 3 Nov digest)."""
    if now.tzinfo is None:
        raise ValueError("EXPLICIT_DIGEST_CLOCK_REQUIRED")
    local = now.astimezone(BANGKOK)
    due_at = datetime.combine(local.date(), DUE_LOCAL, BANGKOK)
    if local < due_at:
        return {"state": "NOT_YET_DUE", "due_at_gmt7": due_at.isoformat(),
                "due_at_utc": due_at.astimezone(timezone.utc).isoformat(),
                "digest_id": "cc143-digest-" + local.date().isoformat()}
    return {"state": "DUE", "due_at_gmt7": due_at.isoformat(),
            "due_at_utc": due_at.astimezone(timezone.utc).isoformat(),
            "digest_id": "cc143-digest-" + local.date().isoformat()}


def default_invocation_id(now: datetime, *, driver: str = DEFAULT_DRIVER) -> str:
    """A truthful run label carrying the active non-Claude route prefix."""
    profile = resolve_profile(driver)
    return str(profile["invocation_prefix"]) + now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_scheduled_stamp(native_invocation_id: str) -> str | None:
    for prefix in _SCHEDULED_INVOCATION_PREFIXES:
        if native_invocation_id.startswith(prefix):
            stamp = native_invocation_id.removeprefix(prefix)
            try:
                datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
                return stamp
            except ValueError:
                return None
    return None


def _ro(path: Path, *, snapshot_dir: Path | None = None,
        allow_oversized_live_wal: bool = True) -> sqlite3.Connection:
    from live_contentops.sqlite_readonly_v1 import connect_readonly_sqlite

    return connect_readonly_sqlite(path, timeout=30.0, row_factory=None,
                                   allow_oversized_live_wal=allow_oversized_live_wal,
                                   snapshot_dir=snapshot_dir)


def _operating_mode(store_path: Path) -> str:
    with contextlib.closing(_ro(store_path)) as conn:
        row = conn.execute("SELECT operating_mode FROM operating_controls WHERE singleton_id=1").fetchone()
    return row[0] if row else "MISSING"


def _commands(rollout_arg: str, invocation_id: str, *, driver: str = DEFAULT_DRIVER) -> dict:
    profile = resolve_profile(driver)
    py = f'"{sys.executable}" -B'
    base = f'{py} {CLI} %s --rollout {rollout_arg} --native-invocation-id "{invocation_id}"'
    return {"run": f'{py} scripts/run_daily_digest_1900.py run --rollout {rollout_arg} --driver {profile["driver"]}',
            "resume": f'{py} scripts/run_daily_digest_1900.py resume --driver {profile["driver"]} --native-invocation-id "{invocation_id}"',
            "begin": base % "digest-tool-begin" + " --request-sha256 <request_sha256>",
            "submit": base % "digest-tool-submit" + " --request-sha256 <request_sha256> --response <response.json>",
            "day_readback": f'{py} scripts/run_day_readback.py --run-dir <run_dir>',
            "observation": {"surface": profile["surface"], "tool_name": profile["tool_name"],
                            "native_invocation_id": invocation_id,
                            "observation_source": profile["observation_source"]}}


def preflight(rollout_path: Path, *, now: datetime | None = None,
              native_invocation_id: str | None = None, driver: str = DEFAULT_DRIVER) -> dict:
    """Reads only: SELECTs on the production store, the rollout, the pause marker and the feed."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE
    from live_contentops.substack_daily_digest_v1 import digest_status, packets

    profile = resolve_profile(driver)
    now = now or datetime.now(timezone.utc)
    result = {"item": "CC-143", "route": profile["route"], "driver": profile["driver"],
              "surface": profile["surface"], "tool_name": profile["tool_name"],
              "checked_at_utc": now.isoformat(), "public_write_performed": False, **due_state(now)}
    if profile.get("model"):
        result["configured_model"] = profile["model"]
        result["configured_reasoning_effort"] = profile["reasoning_effort"]
    blockers = []
    rollout = json.loads(Path(rollout_path).read_bytes())
    try:
        live_publication_policy(rollout)
    except ValueError as exc:
        blockers.append("ROLLOUT:" + str(exc))
    store_path = Path(rollout.get("store_path", ""))
    if store_path.resolve() != PRODUCTION_STORE.resolve():
        blockers.append("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    if llm_operator_pause_active():
        blockers.append("LLM_OPERATOR_PAUSED")
    if not DEFAULT_FEED.is_file():
        blockers.append("CONFIRMED_PUBLICATION_FEED_MISSING")
    mode = _operating_mode(store_path) if store_path.is_file() else "STORE_MISSING"
    result["operating_mode"] = mode
    if mode != "AUTONOMOUS_DEFAULT":
        blockers.append("PUBLICATION_OPERATING_MODE_BLOCKED:" + mode)
    digests = []
    if store_path.is_file():
        store = ContentOpsDurableStore(store_path, auto_migrate=False)
        for packet in sorted(packets(store), key=lambda p: p["cutoff_utc"]):
            status = digest_status(store, packet)
            digests.append({k: status.get(k) for k in ("digest_id", "state", "web_confirmed", "email_confirmed",
                                                       "public_object_id", "public_object_url")}
                           | {"articles": len(packet.get("articles", []))})
    result["existing_digests"] = digests
    result["todays_digest_exists"] = any(d["digest_id"] == result["digest_id"] for d in digests)
    invocation = native_invocation_id or default_invocation_id(now, driver=driver)
    result["native_invocation_id"] = invocation
    result["commands"] = _commands("config/native_desktop_rollout_v1.json", invocation, driver=driver)
    result["blockers"] = blockers
    if blockers:
        result["route_state"] = "BLOCKED"
    elif result["state"] == "NOT_YET_DUE":
        result["route_state"] = "NOT_YET_DUE"
    else:
        result["route_state"] = "CONTINUE_WITH_RESUME"
    return result


class _Guard:
    """Refuse and count every write outside the scratch root and every network connection."""

    def __init__(self, scratch: Path, protected: list[Path]):
        self.scratch = Path(scratch).resolve()
        self.protected = [Path(p).resolve() for p in protected]
        self.refused_writes: list[str] = []
        self.refused_connections: list[str] = []

    def _inside(self, path) -> bool:
        try:
            Path(path).resolve().relative_to(self.scratch)
            return True
        except (ValueError, TypeError, OSError):
            return False

    def _check_write(self, path):
        if isinstance(path, int) or self._inside(path):
            return
        self.refused_writes.append(str(path))
        raise PermissionError("DRY_RUN_WRITE_OUTSIDE_SCRATCH: " + str(path))

    @contextlib.contextmanager
    def active(self):
        real_open, real_io_open = builtins.open, io.open
        real_mkdir, real_makedirs, real_replace, real_rename = Path.mkdir, os.makedirs, os.replace, os.rename
        real_connect, real_create = socket.socket.connect, socket.create_connection
        real_sqlite = sqlite3.connect
        guard = self

        def g_open(file, mode="r", *a, **k):
            if any(c in mode for c in "wax+"):
                guard._check_write(file)
            return real_open(file, mode, *a, **k)

        def g_io_open(file, mode="r", *a, **k):
            if any(c in mode for c in "wax+"):
                guard._check_write(file)
            return real_io_open(file, mode, *a, **k)

        def g_mkdir(self_path, *a, **k):
            if not self_path.exists():
                guard._check_write(self_path)
            return real_mkdir(self_path, *a, **k)

        def g_makedirs(name, *a, **k):
            if not Path(name).exists():
                guard._check_write(name)
            return real_makedirs(name, *a, **k)

        def g_replace(src, dst, *a, **k):
            guard._check_write(dst)
            return real_replace(src, dst, *a, **k)

        def g_rename(src, dst, *a, **k):
            guard._check_write(dst)
            return real_rename(src, dst, *a, **k)

        def g_connect(sock, address):
            guard.refused_connections.append(repr(address))
            raise ConnectionRefusedError("DRY_RUN_NETWORK_REFUSED")

        def g_create(address, *a, **k):
            guard.refused_connections.append(repr(address))
            raise ConnectionRefusedError("DRY_RUN_NETWORK_REFUSED")

        def g_sqlite(database, *a, **k):
            text = str(database)
            target = text[5:].split("?", 1)[0] if text.startswith("file:") else text
            read_only = text.startswith("file:") and "mode=ro" in text
            if target != ":memory:" and not read_only:
                guard._check_write(target)
            return real_sqlite(database, *a, **k)

        builtins.open, io.open = g_open, g_io_open
        Path.mkdir, os.makedirs, os.replace, os.rename = g_mkdir, g_makedirs, g_replace, g_rename
        socket.socket.connect, socket.create_connection = g_connect, g_create
        sqlite3.connect = g_sqlite
        try:
            yield self
        finally:
            builtins.open, io.open = real_open, real_io_open
            Path.mkdir, os.makedirs, os.replace, os.rename = real_mkdir, real_makedirs, real_replace, real_rename
            socket.socket.connect, socket.create_connection = real_connect, real_create
            sqlite3.connect = real_sqlite


def _first_pending(continued: dict, *, invocation_id: str | None = None) -> dict:
    """The owner raises the first request, or lists unclaimed ones after a resume."""
    if continued.get("native_tool_request"):
        return continued["native_tool_request"]
    unclaimed = [row for row in (continued.get("pending_requests") or []) if not row.get("action_claimed")]
    if unclaimed:
        # Prefer fresh VERIFY_IDENTITY probes first, then requests bound to the current invocation_id
        # (so stale unclaimed readbacks from an earlier run never shadow the active run's request).
        for row in unclaimed:
            inner = row.get("request") or {}
            if inner.get("action") == "VERIFY_IDENTITY" and (
                not invocation_id or inner.get("native_invocation_id") in {None, invocation_id}
            ):
                return row
        if invocation_id:
            for row in unclaimed:
                inner = row.get("request") or {}
                if invocation_id in {inner.get("owner_readback_invocation"), inner.get("native_invocation_id")}:
                    return row
        return unclaimed[0]
    publication = continued.get("publication") or {}
    for section in (publication.get("recovery_preflight") or {}, publication):
        for value in (section.get("per_destination") or {}).values():
            if isinstance(value, dict) and value.get("native_tool_request"):
                return value["native_tool_request"]
    return {}


def _fingerprint(store_path: Path) -> dict:
    stat = store_path.stat()
    with contextlib.closing(_ro(store_path)) as conn:
        counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("outbox_messages", "platform_dispatches", "work_items")}
        digest_rows = conn.execute("SELECT count(*) FROM outbox_messages WHERE destination=?",
                                   ("internal:substack-daily-digest",)).fetchone()[0]
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "rows": counts, "digest_packets": digest_rows}


def dry_run(rollout_path: Path, scratch: Path, *, now: datetime | None = None,
            native_invocation_id: str = "cc143-route-dry-run", simulate_identity: bool = False,
            driver: str = DEFAULT_DRIVER) -> dict:
    """Freeze and continue the digest on a copied store; nothing shared is written."""
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE

    profile = resolve_profile(driver)
    now = now or datetime.now(timezone.utc)
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=False)  # a fresh folder per run
    rollout = json.loads(Path(rollout_path).read_bytes())
    production = Path(rollout["store_path"])
    if production.resolve() != PRODUCTION_STORE.resolve():
        raise ValueError("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    copy = scratch / "contentops_daily_app_v1.sqlite3"
    before = _fingerprint(production)
    with contextlib.closing(_ro(production)) as source, contextlib.closing(sqlite3.connect(copy)) as target:
        source.backup(target)
    copied = _fingerprint(copy)
    feed_stat = DEFAULT_FEED.stat()
    result = {"item": "CC-143", "mode": "DRY_RUN_COPIED_STORE", "route": profile["route"],
              "driver": profile["driver"], "surface": profile["surface"],
              "clock_utc": now.isoformat(),
              "clock_is_simulated": abs((datetime.now(timezone.utc) - now).total_seconds()) > 120,
              "scratch": str(scratch), "copied_store": str(copy), "production_before": before,
              "copy_at_start": copied, **due_state(now)}
    guard = _Guard(scratch, [production])
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    from live_contentops.substack_daily_digest_v1 import continue_daily_digest, digest_status, prepare_daily_digest
    with guard.active():
        # Any active-WAL private snapshot of the copy stays inside the guarded scratch root.
        store = ContentOpsDurableStore(copy, auto_migrate=False, read_only_snapshot_dir=scratch)
        prepared = _call_prepare_daily_digest(prepare_daily_digest, store, DEFAULT_FEED, now=now)
        packet = prepared.get("packet")
        result["prepare"] = {k: v for k, v in prepared.items() if k != "packet"}
        if packet:
            result["digest"] = {"digest_id": packet["digest_id"], "cutoff_utc": packet["cutoff_utc"],
                "title": packet["native_payload"]["title"], "subtitle": packet["native_payload"]["subtitle"],
                "articles": [{k: a[k] for k in ("title", "url", "published_at_utc")} for a in packet["articles"]],
                "media": [{k: m[k] for k in ("asset_id", "path", "sha256")} for m in packet["media_assets"]]}
            local_rollout = {**rollout, "store_path": str(copy), "editorial_output_root": str(scratch / "outputs")}
            try:
                continued = continue_daily_digest(store, packet,
                    output_dir=scratch / "outputs" / "owner-manual" / packet["digest_id"] / "native-tools",
                    invocation_id=native_invocation_id, rollout=local_rollout, command="resume")
            except NativeNeoInputRequired as pending:  # defensive; the owner normally catches it
                continued = {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
            request = _first_pending(continued)
            inner = request.get("request", {})
            result["continue"] = {"state": continued.get("state"), "web_confirmed": continued.get("web_confirmed"),
                "email_confirmed": continued.get("email_confirmed"),
                "first_native_request": {"action": inner.get("action"), "destination": inner.get("destination"),
                    "surface": inner.get("surface"), "expected_identity": inner.get("expected_identity"),
                    "request_sha256": inner.get("request_sha256"), "required_tool": request.get("required_tool"),
                    "public_write_authorized": request.get("public_write_authorized"),
                    "request_path": request.get("request_path")} if request else None,
                "pending_requests": len(continued.get("pending_requests", []))}
            if simulate_identity and request and inner.get("action") == "VERIFY_IDENTITY":
                # Prove the active non-Claude surface passes the owner's begin/submit binding on
                # the copy only, then stop at the next request without beginning it.
                args = dict(output_dir=scratch / "outputs" / "owner-manual" / packet["digest_id"] / "native-tools",
                            invocation_id=native_invocation_id, rollout=local_rollout)
                continue_daily_digest(store, packet, command="begin", request_hash=inner["request_sha256"], **args)
                response = {"tool_request_sha256": request["tool_request_sha256"],
                    "tool_observation": {"surface": profile["surface"], "tool_name": profile["tool_name"],
                        "native_invocation_id": native_invocation_id,
                        "observation_source": "DRY_RUN_SIMULATED_NOT_BROWSER",
                        "observed_at_utc": datetime.now(timezone.utc).isoformat()},
                    "result": {"request_sha256": inner["request_sha256"], "status": "SUCCESS",
                        "authenticated": True, "observed_identity": inner.get("expected_identity"),
                        "observation_ref": "DRY_RUN_SIMULATED_NOT_BROWSER"}}
                submitted = continue_daily_digest(store, packet, command="submit",
                    request_hash=inner["request_sha256"], response=response, **args)
                following = continue_daily_digest(store, packet, command="resume", **args)
                nxt = _first_pending(following)
                nxt_inner = nxt.get("request", {})
                result["simulated_identity"] = {"submitted": submitted, "next_state": following.get("state"),
                    "publication_status": (following.get("publication") or {}).get("canonical_publication_status"),
                    "next_native_request": {"action": nxt_inner.get("action"), "destination": nxt_inner.get("destination"),
                        "public_write_authorized": nxt.get("public_write_authorized"),
                        "substack_delivery_policy": nxt_inner.get("substack_delivery_policy"),
                        "request_sha256": nxt_inner.get("request_sha256"),
                        "request_path": nxt.get("request_path")} if nxt else None,
                    "next_request_begun": False}
            result["copy_status_after"] = digest_status(store, packet)
    result["production_after"] = _fingerprint(production)
    result["production_unchanged"] = result["production_after"] == before
    result["feed_unchanged"] = DEFAULT_FEED.stat().st_mtime_ns == feed_stat.st_mtime_ns
    result["refused_writes_outside_scratch"] = guard.refused_writes
    result["refused_network_connections"] = guard.refused_connections
    result["public_write_performed"] = False
    return result


def summarize_continuation(continued: dict, *, invocation_id: str | None = None) -> dict:
    """One flat view of the owner's return: the state and the next unclaimed native request."""
    request = _first_pending(continued, invocation_id=invocation_id)
    inner = request.get("request", {}) if request else {}
    return {"state": continued.get("state"), "digest_id": continued.get("digest_id"),
            "confirmed": continued.get("confirmed"), "web_confirmed": continued.get("web_confirmed"),
            "email_confirmed": continued.get("email_confirmed"),
            "public_object_id": continued.get("public_object_id"),
            "public_object_url": continued.get("public_object_url"),
            "next_request": {"action": inner.get("action"), "destination": inner.get("destination"),
                             "request_sha256": inner.get("request_sha256"),
                             "tool_request_sha256": request.get("tool_request_sha256"),
                             "public_write_authorized": request.get("public_write_authorized")} if request else None}


def _empty_digest_readback(rollout, native_invocation_id, digest_id, feed_path, *, now):
    """The evening report is due even when the digest has no issue to send."""
    from live_contentops.day_readback_v1 import build_report, write_report

    stamp = _extract_scheduled_stamp(native_invocation_id)
    if stamp is None:
        return None
    run_dir = Path(rollout["editorial_output_root"]) / "owner-manual" / "route-1900" / stamp
    if not run_dir.is_dir():
        return None
    paths = (run_dir / "day_readback.json", run_dir / "day_readback.md")
    if all(path.is_file() for path in paths):
        return {"state": "READBACK_ALREADY_WRITTEN", "files": [str(path) for path in paths]}
    result = {"digest_id": digest_id, "final_route_state": "NO_CONFIRMED_ARTICLES", "recorded_at_utc": now.isoformat()}
    try:
        report = build_report(run_dir, store_path=Path(rollout["store_path"]), feed_path=feed_path,
                              now=now, run_result=result)
        paths = write_report(run_dir, report)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        return {"state": "READBACK_COMMAND_FAILED", "first_cause": type(exc).__name__}
    return {"state": "READBACK_WRITTEN", "files": [str(path) for path in paths]}


def _call_prepare_daily_digest(prepare_fn, store, feed_path, *, now: datetime):
    """Pass explicit `now` when the callable accepts it (preserves zero-kwarg test monkeypatches)."""
    try:
        params = inspect.signature(prepare_fn).parameters
        accepts_now = "now" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except (TypeError, ValueError):
        accepts_now = False
    return prepare_fn(store, feed_path, now=now) if accepts_now else prepare_fn(store, feed_path)


def resume(rollout_path: Path, native_invocation_id: str, *, now: datetime | None = None,
           driver: str = DEFAULT_DRIVER, run_empty_readback: bool = True) -> dict:
    """The CLI's digest-resume through the same owners, guarded against an early wake.
    It never begins a request: only digest-tool-begin claims, and only the active driver acts."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE
    from live_contentops.substack_daily_digest_v1 import continue_daily_digest, prepare_daily_digest

    profile = resolve_profile(driver)
    now = now or datetime.now(timezone.utc)
    due = due_state(now)
    if due["state"] == "NOT_YET_DUE":
        return {"item": "CC-143", "route": profile["route"], "driver": profile["driver"],
                "route_state": "NOT_YET_DUE", **due, "public_write_performed": False}
    rollout = json.loads(Path(rollout_path).read_bytes())
    live_publication_policy(rollout)
    if Path(rollout["store_path"]).resolve() != PRODUCTION_STORE.resolve():
        raise ValueError("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    prepared = _call_prepare_daily_digest(prepare_daily_digest, store, DEFAULT_FEED, now=now)
    packet = prepared.get("packet")
    if not packet:
        state = prepared.get("state")
        result = {"item": "CC-143", "route": profile["route"], "driver": profile["driver"],
                  "route_state": state, **due,
                  "prepare": prepared, "public_write_performed": False}
        if state == "NO_CONFIRMED_ARTICLES" and run_empty_readback:
            readback = _empty_digest_readback(rollout, native_invocation_id, due["digest_id"], DEFAULT_FEED, now=now)
            if readback is not None:
                result["day_readback"] = readback
        return result
    continued = continue_daily_digest(store, packet,
        output_dir=Path(rollout["editorial_output_root"]) / "owner-manual" / packet["digest_id"] / "native-tools",
        invocation_id=native_invocation_id, rollout=rollout, command="resume")
    summary = summarize_continuation({"digest_id": packet["digest_id"], **continued}, invocation_id=native_invocation_id)
    if summary["confirmed"]:
        route_state = "CONFIRMED"
    elif summary["next_request"]:
        route_state = "NATIVE_REQUEST_READY"
    elif summary["web_confirmed"]:
        route_state = "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED"
    else:
        route_state = summary["state"] or "NO_NEXT_REQUEST"
    return {"item": "CC-143", "route": profile["route"], "driver": profile["driver"],
            "surface": profile["surface"], "route_state": route_state, **due, **summary,
            "articles": len(packet.get("articles", [])), "native_invocation_id": native_invocation_id,
            "public_write_performed": False}


def format_codex_slot_line(now_utc: datetime, key: str, what: str) -> bytes:
    """Format 'YYYY-MM-DDTHH:MM:SS.mmmZ <key> <what>\\r\\n' matching lane_runner.ps1 & headless_analysis_v1."""
    utc_dt = now_utc.astimezone(timezone.utc)
    stamp = f"{utc_dt.strftime('%Y-%m-%dT%H:%M:%S.')}{utc_dt.microsecond // 1000:03d}Z"
    safe_key = re.sub(r"\s+", "-", str(key or "cc143-digest").strip())[:64] or "cc143-digest"
    safe_what = re.sub(r"[\r\n]+", " ", str(what or "run_daily_digest_1900").strip())[:80] or "run_daily_digest_1900"
    return f"{stamp} {safe_key} {safe_what}\r\n".encode("ascii", errors="replace")


def parse_codex_slot_timestamp(text: str) -> datetime | None:
    match = _SLOT_TS_RE.match(text.lstrip("\ufeff").strip())
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _win32_kernel32():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.SetFilePointer.argtypes = [
        wintypes.HANDLE, wintypes.LONG, ctypes.POINTER(wintypes.LONG), wintypes.DWORD,
    ]
    kernel32.SetFilePointer.restype = wintypes.DWORD
    kernel32.SetEndOfFile.argtypes = [wintypes.HANDLE]
    kernel32.SetEndOfFile.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _open_slot_exclusive_win32(path: Path):
    import ctypes
    from ctypes import wintypes

    kernel32 = _win32_kernel32()
    raw_handle = kernel32.CreateFileW(str(path), 0x80000000 | 0x40000000, 0, None, 4, 0x80, None)
    if raw_handle == wintypes.HANDLE(-1).value or not raw_handle:
        err = ctypes.get_last_error()
        if err in (32, 33):
            return None
        raise ctypes.WinError(err)
    return kernel32, wintypes.HANDLE(raw_handle)


def acquire_codex_launch_slot(*, key: str, what: str = "run_daily_digest_1900_codex_astra",
                              slot_file: Path | None = None, min_gap_seconds: float | None = None,
                              now_utc=None, sleep=time_mod.sleep) -> dict:
    """Serialize any Codex CLI launch behind shared codex-launch-slot.txt (>= 90 s gap)."""
    env_slot = os.environ.get(CODEX_LAUNCH_SLOT_ENV, "").strip()
    if slot_file is None and not env_slot and os.environ.get("PYTEST_CURRENT_TEST"):
        raise RuntimeError("REFUSING_LIVE_CODEX_SLOT_IN_TEST")
    target = Path(slot_file) if slot_file is not None else Path(env_slot or CODEX_LAUNCH_SLOT_FILE)
    gap = float(min_gap_seconds if min_gap_seconds is not None
                else (os.environ.get(CODEX_LAUNCH_SLOT_GAP_ENV) or CODEX_LAUNCH_SLOT_GAP_SECONDS))

    def _clock() -> datetime:
        return now_utc().astimezone(timezone.utc) if now_utc is not None else datetime.now(timezone.utc)

    target.parent.mkdir(parents=True, exist_ok=True)
    waited = 0.0
    retries = 0
    while True:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            opened = _open_slot_exclusive_win32(target)
            if opened is None:
                retries += 1
                if retries > _SLOT_SHARE_RETRIES:
                    raise TimeoutError("CODEX_LAUNCH_SLOT_LOCK_TIMEOUT")
                sleep(0.25)
                waited += 0.25
                continue
            kernel32, handle = opened
            try:
                buf = ctypes.create_string_buffer(4096)
                read_count = wintypes.DWORD(0)
                if not kernel32.ReadFile(handle, buf, 4096, ctypes.byref(read_count), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                prior = parse_codex_slot_timestamp(buf.raw[:read_count.value].decode("utf-8", errors="replace"))
                current = _clock()
                if prior is not None and gap > 0:
                    remaining = gap - (current - prior).total_seconds()
                    if remaining > 0:
                        sleep(remaining)
                        waited += remaining
                        current = _clock()
                payload = format_codex_slot_line(current, key, what)
                if kernel32.SetFilePointer(handle, 0, None, 0) == 0xFFFFFFFF:
                    raise ctypes.WinError(ctypes.get_last_error())
                if not kernel32.SetEndOfFile(handle):
                    raise ctypes.WinError(ctypes.get_last_error())
                written = wintypes.DWORD(0)
                if not kernel32.WriteFile(handle, payload, len(payload), ctypes.byref(written), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                kernel32.FlushFileBuffers(handle)
                return {
                    "slot_file": str(target),
                    "acquired_at_utc": current.isoformat(),
                    "waited_seconds": round(waited, 3),
                    "min_gap_seconds": gap,
                    "line": payload.decode("ascii").strip(),
                }
            finally:
                kernel32.CloseHandle(handle)
        else:
            import fcntl

            with open(target, "a+b") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                try:
                    stream.seek(0)
                    prior = parse_codex_slot_timestamp(stream.read(4096).decode("utf-8", errors="replace"))
                    current = _clock()
                    if prior is not None and gap > 0:
                        remaining = gap - (current - prior).total_seconds()
                        if remaining > 0:
                            sleep(remaining)
                            waited += remaining
                            current = _clock()
                    payload = format_codex_slot_line(current, key, what)
                    stream.seek(0)
                    stream.truncate(0)
                    stream.write(payload)
                    stream.flush()
                    return {
                        "slot_file": str(target),
                        "acquired_at_utc": current.isoformat(),
                        "waited_seconds": round(waited, 3),
                        "min_gap_seconds": gap,
                        "line": payload.decode("ascii").strip(),
                    }
                finally:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _single_instance_lock(lock_path: Path):
    """Non-blocking OS-held lock so concurrent triggers exit cleanly with LOCK_HELD."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    stream = open(lock_path, "a+b")
    acquired = False
    try:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                acquired = True
            except OSError:
                acquired = False
        else:
            import fcntl

            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                acquired = False
        if acquired:
            stream.seek(0)
            stream.truncate(0)
            stream.write(f"pid={os.getpid()} started_at_utc={datetime.now(timezone.utc).isoformat()}\n".encode("ascii"))
            stream.flush()
        yield acquired
    finally:
        if acquired:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        stream.close()


def _save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")


def _run_evening_readback(
    run_dir: Path,
    rollout: dict,
    feed_path: Path,
    *,
    now: datetime,
    since: str | None = None,
    stored_only: bool = False,
    fetcher=None,
) -> dict:
    """Run CC-639 / CC-690 read-only evening readback into run_dir after result.json."""
    from live_contentops.day_readback_v1 import DECISION_CHECKS_NAME, build_report, write_report
    from live_contentops.image_quality_v1 import completed_day_sample
    from live_contentops.published_content_v1 import PRODUCTION_STORE

    store_path = Path(rollout["store_path"])
    expected_files = (run_dir / "day_readback.json", run_dir / "day_readback.md", run_dir / DECISION_CHECKS_NAME)
    if all(p.is_file() for p in expected_files):
        return {"state": "READBACK_ALREADY_WRITTEN", "files": [str(p) for p in expected_files]}
    try:
        kwargs: dict = {}
        if since is not None:
            kwargs["since"] = since
        if fetcher is not None:
            kwargs["fetcher"] = fetcher
        elif stored_only:
            kwargs["fetcher"] = None
        report = build_report(run_dir, store_path=store_path, feed_path=feed_path, now=now, **kwargs)
        decisions = report["decision_checks"]
        try:
            decisions["image_templates"] = completed_day_sample(
                feed_path.parent / "published_images_v1.jsonl",
                as_of=report["window"]["until_utc"],
                run_vision=not stored_only and fetcher is None and store_path.resolve() == PRODUCTION_STORE.resolve(),
            )
        except (OSError, ValueError) as exc:
            decisions["image_templates"] = {"state": "IMAGE_SAMPLE_READ_FAILED", "cause": type(exc).__name__}
        paths = (*write_report(run_dir, report), run_dir / DECISION_CHECKS_NAME)
        return {
            "state": "READBACK_WRITTEN",
            "files": [str(p) for p in paths],
            "pieces": len(report["pieces"]),
            "exception_count": report["exception_count"],
            "decision_failure_count": decisions["failure_count"],
        }
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        return {"state": "READBACK_COMMAND_FAILED", "first_cause": type(exc).__name__}


def _codex_executable() -> str:
    found = shutil.which("codex.exe") or shutil.which("codex")
    if not found:
        candidates = list(Path(r"C:\Users\bullw\AppData\Local\OpenAI\Codex\bin").glob("*/codex.exe"))
        found = str(max(candidates, key=lambda p: p.stat().st_mtime)) if candidates else None
    if not found:
        raise ValueError("CODEX_EXECUTABLE_NOT_FOUND")
    return found


def _build_codex_astra_prompt(rollout_path: Path, run_dir: Path, invocation_id: str) -> str:
    return (
        "Capital Chronicle CC-143 / CC-855 daily 19:00 GMT+7 Substack email digest run.\n"
        f"Work directory: {ROOT}\n"
        f"Run folder: {run_dir}\n"
        f"Rollout: {rollout_path}\n"
        f"Native invocation ID (use verbatim): {invocation_id}\n"
        "Surface provenance (C5 mandatory): surface=\"CODEX_EXEC\", tool_name=\"mcp__browseros_neo__run\", "
        "observation_source=\"BROWSEROS_NEO\". Never invoke claude or agy.\n"
        "Steps:\n"
        "1. Continue today's digest via `scripts/run_daily_digest_1900.py resume --driver codex-astra` "
        "and `scripts/run_native_desktop_editorial.py digest-tool-begin` / `digest-tool-submit`.\n"
        "2. Handle VERIFY_IDENTITY, PUBLISH (DAILY_EMAIL_DIGEST: email send ON + web publish ON verified before click; "
        "if Check your email appears record PENDING_JIM_EMAIL_CODE and leave tab untouched; NEVER read Gmail), "
        "and READBACK (public page + Substack post stats).\n"
        "3. Stop at CONFIRMED, WEB_CONFIRMED_EMAIL_READBACK_REQUIRED (after one READBACK), PENDING_JIM_EMAIL_CODE, "
        "NO_CONFIRMED_ARTICLES, or any refusal (max 8 requests; at most 1 CC-548 catch-up pass).\n"
        f"4. Write {run_dir / 'result.json'} with digest_id, route_state, public_object_url, requests_handled, "
        "first_blocking_cause, jim_email_code_pending, and recorded_at_utc.\n"
        f"5. Run paired C1-B evening readback on empty and non-empty days: "
        f"`python -B scripts/run_day_readback.py --run-dir \"{run_dir}\"` (run_daily_digest_1900.py run also verifies/runs it after result.json).\n"
    )


def _run_codex_astra_pass(
    *,
    rollout_path: Path,
    run_dir: Path,
    invocation_id: str,
    profile: dict[str, str | None],
    slot_file: Path | None,
    min_gap_seconds: float | None,
    codex_runner=None,
    timeout_seconds: int = 900,
    now_utc=None,
    sleep=time_mod.sleep,
) -> dict:
    """Invoke `codex exec` on `gpt-6.2-astra` max serialized behind codex-launch-slot.txt."""
    stamp = run_dir.name
    slot_info = acquire_codex_launch_slot(
        key=f"cc143-digest-1900-{stamp}",
        what="run_daily_digest_1900_codex_astra",
        slot_file=slot_file,
        min_gap_seconds=min_gap_seconds,
        now_utc=now_utc,
        sleep=sleep,
    )
    prompt = _build_codex_astra_prompt(rollout_path, run_dir, invocation_id)
    (run_dir / "codex-astra-prompt.txt").write_text(prompt, encoding="utf-8")
    last_msg = run_dir / "codex-astra-last-message.txt"
    exe = _codex_executable() if codex_runner is None else "codex"
    args = [
        exe,
        "exec",
        "--model",
        str(profile["model"]),
        "-c",
        f'model_reasoning_effort="{profile["reasoning_effort"]}"',
        "-c",
        'forced_login_method="chatgpt"',
        "-c",
        'approval_policy="never"',
        "--skip-git-repo-check",
        "--json",
        "--output-last-message",
        str(last_msg),
        "-",
    ]
    child_env = {k: v for k, v in os.environ.items() if k not in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}}
    if codex_runner is not None:
        done = codex_runner(args, cwd=str(ROOT), env=child_env, input=prompt.encode("utf-8"), timeout=timeout_seconds)
    else:
        done = subprocess.run(
            args,
            cwd=str(ROOT),
            env=child_env,
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=timeout_seconds,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    stdout_bytes = getattr(done, "stdout", b"") or b""
    stderr_bytes = getattr(done, "stderr", b"") or b""
    (run_dir / "codex-astra-stdout.jsonl").write_bytes(stdout_bytes)
    (run_dir / "codex-astra-stderr.txt").write_bytes(stderr_bytes)
    return {
        "slot": slot_info,
        "configured_model": profile["model"],
        "configured_reasoning_effort": profile["reasoning_effort"],
        "returncode": int(done.returncode),
        "stdout_bytes": len(stdout_bytes),
        "stderr_bytes": len(stderr_bytes),
    }


def _execute_python_neo_pass(
    *,
    rollout_path: Path,
    rollout: dict,
    run_dir: Path,
    preflight_doc: dict,
    invocation_id: str,
    profile: dict[str, str | None],
    now: datetime,
    endpoint_client,
    max_requests: int,
    requests_used: int,
    email_stats_poll_timeout_seconds: float | None = None,
    email_stats_poll_interval_seconds: float | None = None,
    sleep=time_mod.sleep,
    monotonic=time_mod.monotonic,
) -> tuple[dict, int]:
    """Execute one bounded CC-143 pass deterministically over NeoMcpClient."""
    from live_contentops.daily_digest_neo_v1 import (
        DEFAULT_EMAIL_STATS_POLL_INTERVAL_SECONDS,
        DEFAULT_EMAIL_STATS_POLL_TIMEOUT_SECONDS,
        perform_digest_action,
    )
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.published_content_v1 import DEFAULT_FEED
    from live_contentops.substack_daily_digest_v1 import continue_daily_digest, prepare_daily_digest

    poll_timeout = (
        DEFAULT_EMAIL_STATS_POLL_TIMEOUT_SECONDS
        if email_stats_poll_timeout_seconds is None
        else float(email_stats_poll_timeout_seconds)
    )
    poll_interval = (
        DEFAULT_EMAIL_STATS_POLL_INTERVAL_SECONDS
        if email_stats_poll_interval_seconds is None
        else float(email_stats_poll_interval_seconds)
    )

    step = 2
    requests_handled: list[dict] = []
    first_blocking_cause: str | None = None
    jim_email_code_pending = False
    public_write_performed = False
    readback_attempted = False
    final_state = "UNKNOWN"
    digest_id = preflight_doc["digest_id"]
    public_object_id = None
    public_object_url = None
    email_confirmed = False
    articles: list[dict] = []

    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    active_packet: dict | None = None
    due = due_state(now)

    while True:
        if active_packet is None:
            resumed = resume(rollout_path, invocation_id, now=now, driver=str(profile["driver"]), run_empty_readback=False)
            if resumed.get("route_state") not in {"NO_CONFIRMED_ARTICLES", "NOT_YET_DUE"}:
                prepared = _call_prepare_daily_digest(prepare_daily_digest, store, DEFAULT_FEED, now=now)
                active_packet = prepared.get("packet")
                if active_packet:
                    digest_id = active_packet["digest_id"]
                    articles = [{"title": a["title"], "url": a["url"]} for a in active_packet.get("articles", [])]
        else:
            # Pin this pass to active_packet so confirming an older digest never silently
            # advances into today's digest inside Pass 1 (CC-548 requires a separate Pass 2).
            native_dir_active = Path(rollout["editorial_output_root"]) / "owner-manual" / active_packet["digest_id"] / "native-tools"
            continued = continue_daily_digest(
                store,
                active_packet,
                output_dir=native_dir_active,
                invocation_id=invocation_id,
                rollout=rollout,
                command="resume",
            )
            summary = summarize_continuation({"digest_id": active_packet["digest_id"], **continued}, invocation_id=invocation_id)
            if summary["confirmed"]:
                r_state = "CONFIRMED"
            elif summary["next_request"]:
                r_state = "NATIVE_REQUEST_READY"
            elif summary["web_confirmed"]:
                r_state = "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED"
            else:
                r_state = summary["state"] or "NO_NEXT_REQUEST"
            resumed = {
                "item": "CC-143",
                "route": profile["route"],
                "driver": profile["driver"],
                "surface": profile["surface"],
                "route_state": r_state,
                **due,
                **summary,
                "articles": len(active_packet.get("articles", [])),
                "native_invocation_id": invocation_id,
                "public_write_performed": False,
            }

        _save_json(run_dir / f"{step:02d}-resume.json", resumed)
        step += 1

        final_state = str(resumed.get("route_state") or "UNKNOWN")
        digest_id = resumed.get("digest_id") or digest_id
        public_object_id = resumed.get("public_object_id") or public_object_id
        public_object_url = resumed.get("public_object_url") or public_object_url
        email_confirmed = bool(resumed.get("email_confirmed"))
        packet = active_packet

        if final_state in {"CONFIRMED", "NO_CONFIRMED_ARTICLES", "NOT_YET_DUE"}:
            break
        if final_state == "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED" and (
            not resumed.get("next_request") or readback_attempted
        ):
            break
        if final_state != "NATIVE_REQUEST_READY" or not resumed.get("next_request"):
            first_blocking_cause = first_blocking_cause or final_state
            break
        if requests_used >= max_requests:
            first_blocking_cause = "MAX_REQUESTS_PER_RUN_REACHED"
            break
        if not packet:
            first_blocking_cause = "DIGEST_PACKET_MISSING_ON_RESUME"
            break

        next_req = resumed["next_request"]
        req_hash = next_req["request_sha256"]
        action = str(next_req.get("action") or "ACTION")
        if action == "READBACK" and readback_attempted:
            break

        native_dir = Path(rollout["editorial_output_root"]) / "owner-manual" / packet["digest_id"] / "native-tools"

        # D-M2: verify Neo endpoint reachability BEFORE claiming the request via begin()
        # so an unreachable/restarting Neo server never leaves an unsubmitted PUBLISH claim (UNKNOWN_WRITE).
        try:
            endpoint_client.initialize()
        except Exception as exc:
            cause = str(exc)[:160] if isinstance(exc, (ValueError, RuntimeError, OSError)) else type(exc).__name__
            first_blocking_cause = cause or "NEO_ENDPOINT_UNAVAILABLE"
            final_state = "NEO_ENDPOINT_UNAVAILABLE"
            err_path = run_dir / f"{step:02d}-{action.lower()}-init-error.json"
            _save_json(err_path, {"action": action, "stage": "BEFORE_BEGIN", "error": first_blocking_cause,
                                  "observed_at_utc": datetime.now(timezone.utc).isoformat()})
            step += 1
            break

        from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

        try:
            action_packet = continue_daily_digest(
                store,
                packet,
                output_dir=native_dir,
                invocation_id=invocation_id,
                rollout=rollout,
                command="begin",
                request_hash=req_hash,
            )
        except NativeNeoInputRequired as pending_id:
            # A recovered unclaimed PUBLISH under a new invocation_id requires a fresh VERIFY_IDENTITY
            # probe first; satisfy that persisted probe now so the next iteration can begin PUBLISH.
            _save_json(run_dir / f"{step:02d}-begin-needs-identity.json", pending_id.request)
            step += 1
            pending_inner = (pending_id.request or {}).get("request") or {}
            req_hash = str(pending_inner.get("request_sha256") or "")
            action = str(pending_inner.get("action") or "VERIFY_IDENTITY")
            if not req_hash:
                first_blocking_cause = "BEGIN_IDENTITY_REQUEST_MISSING"
                final_state = "BEGIN_REFUSED"
                break
            try:
                action_packet = continue_daily_digest(
                    store,
                    packet,
                    output_dir=native_dir,
                    invocation_id=invocation_id,
                    rollout=rollout,
                    command="begin",
                    request_hash=req_hash,
                )
            except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
                first_blocking_cause = str(exc)[:160]
                final_state = "BEGIN_REFUSED"
                break
        except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
            first_blocking_cause = str(exc)[:160]
            final_state = "BEGIN_REFUSED"
            break
        _save_json(run_dir / f"{step:02d}-begin-{action.lower()}.json", action_packet)
        step += 1

        obs_path = run_dir / f"{step:02d}-{action.lower()}-observation.json"
        if action == "READBACK":
            obs_path = run_dir / f"{step:02d}-readback-observation.json"
        step += 1

        try:
            performed = perform_digest_action(
                endpoint_client,
                action_packet,
                observation_path=obs_path,
                email_stats_poll_timeout_seconds=poll_timeout,
                email_stats_poll_interval_seconds=poll_interval,
                sleep=sleep,
                monotonic=monotonic,
            )
        except Exception as exc:
            cause = str(exc)[:160] if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__
            first_blocking_cause = cause or "NEO_ENDPOINT_UNAVAILABLE"
            final_state = "NEO_ENDPOINT_UNAVAILABLE"
            _save_json(obs_path, {"action": action, "error": first_blocking_cause,
                                  "observed_at_utc": datetime.now(timezone.utc).isoformat()})
            break

        _save_json(obs_path, performed.get("observation") or {"action": action})
        action_result = {"request_sha256": req_hash, **(performed.get("result") or {})}
        observed_now = datetime.now(timezone.utc).isoformat()
        tool_observation: dict = {
            "surface": profile["surface"],
            "tool_name": profile["tool_name"],
            "native_invocation_id": invocation_id,
            "observation_source": profile["observation_source"],
            "observed_at_utc": observed_now,
        }
        if action == "PUBLISH" and performed.get("dispatched_at_utc"):
            tool_observation["dispatched_at_utc"] = performed["dispatched_at_utc"]
            if action_result.get("status") == "SUCCESS":
                public_write_performed = True

        response_doc = {
            "tool_request_sha256": action_packet["tool_request_sha256"],
            "tool_observation": tool_observation,
            "result": action_result,
        }
        resp_path = run_dir / f"{step:02d}-{action.lower()}-response.json"
        _save_json(resp_path, response_doc)
        step += 1

        try:
            submitted = continue_daily_digest(
                store,
                packet,
                output_dir=native_dir,
                invocation_id=invocation_id,
                rollout=rollout,
                command="submit",
                request_hash=req_hash,
                response=response_doc,
            )
        except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
            first_blocking_cause = str(exc)[:160]
            final_state = "SUBMIT_REFUSED"
            break
        _save_json(run_dir / f"{step:02d}-submit-{action.lower()}.json", submitted)
        step += 1

        requests_used += 1
        status_str = str(action_result.get("status") or "UNKNOWN")
        requests_handled.append({"action": action, "request_sha256": req_hash, "status": status_str})

        if action_result.get("public_object_id"):
            public_object_id = action_result["public_object_id"]
        if action_result.get("public_object_url"):
            public_object_url = action_result["public_object_url"]
        if action == "READBACK":
            readback_attempted = True
            if action_result.get("email_delivery_confirmed") is True:
                email_confirmed = True

        if status_str == "PENDING_JIM_EMAIL_CODE":
            # D-H2(a): one non-claiming resume persists SUBSTACK_DRAFT_AWAITING_OWNER and
            # substack-owner-screen-<dispatch_id> immediately in Run 1 (code tab untouched, 0 Gmail).
            try:
                parked = continue_daily_digest(
                    store,
                    packet,
                    output_dir=native_dir,
                    invocation_id=invocation_id,
                    rollout=rollout,
                    command="resume",
                )
                _save_json(run_dir / f"{step:02d}-resume-pending-code.json", parked)
                step += 1
            except (ValueError, OSError, KeyError, sqlite3.Error):
                pass
            jim_email_code_pending = True
            final_state = "PENDING_JIM_EMAIL_CODE"
            first_blocking_cause = "PENDING_JIM_EMAIL_CODE"
            break
        if status_str in {"FAILED_BEFORE_WRITE", "UNKNOWN_WRITE", "READBACK_UNAVAILABLE", "SKIPPED", "BLOCKED"}:
            final_state = status_str
            first_blocking_cause = str(action_result.get("reason_code") or status_str)
            break

    pass_result = {
        "item": "CC-143",
        "route": profile["route"],
        "driver": profile["driver"],
        "surface": profile["surface"],
        "tool_name": profile["tool_name"],
        "digest_id": digest_id,
        "native_invocation_id": invocation_id,
        "route_state": final_state,
        "final_route_state": final_state,
        "public_object_id": public_object_id,
        "public_object_url": public_object_url,
        "email_delivery_confirmed": email_confirmed,
        "articles": articles,
        "requests_handled": requests_handled,
        "first_blocking_cause": first_blocking_cause,
        "jim_email_code_pending": jim_email_code_pending,
        "public_write_performed": public_write_performed,
        "recorded_at_utc": now.astimezone(timezone.utc).isoformat(),
    }
    return pass_result, requests_used


def run_digest_1900(
    rollout_path: Path,
    *,
    driver: str = DEFAULT_DRIVER,
    now: datetime | None = None,
    lock_path: Path = DEFAULT_LOCK_PATH,
    stop_path: Path = DEFAULT_STOP_PATH,
    neo_endpoint: str = DEFAULT_NEO_ENDPOINT,
    endpoint_client=None,
    codex_runner=None,
    codex_slot_file: Path | None = None,
    codex_min_gap_seconds: float | None = None,
    codex_now_utc=None,
    max_requests: int = MAX_REQUESTS_PER_RUN,
    run_day_readback: bool = True,
    stored_only_readback: bool = False,
    readback_fetcher=None,
    is_dry_run: bool = False,
    scratch: Path | None = None,
    email_stats_poll_timeout_seconds: float | None = None,
    email_stats_poll_interval_seconds: float | None = None,
    sleep=time_mod.sleep,
    monotonic=time_mod.monotonic,
) -> dict:
    """Run the bounded 19:15 GMT+7 daily digest and CC-639/CC-690 evening readback without Claude."""
    from live_contentops.published_content_v1 import DEFAULT_FEED

    profile = resolve_profile(driver)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    if Path(stop_path).is_file():
        return {
            "item": "CC-143",
            "route": profile["route"],
            "driver": profile["driver"],
            "route_state": "STOP_SENTINEL_ACTIVE",
            "stop_path": str(stop_path),
            "public_write_performed": False,
            "checked_at_utc": now.isoformat(),
        }

    with _single_instance_lock(lock_path) as acquired:
        if not acquired:
            return {
                "item": "CC-143",
                "route": profile["route"],
                "driver": profile["driver"],
                "route_state": "LOCK_HELD",
                "lock_path": str(lock_path),
                "public_write_performed": False,
                "checked_at_utc": now.isoformat(),
            }

        if is_dry_run:
            target_scratch = scratch or Path(tempfile.mkdtemp(prefix="cc143-digest-dry-run-"))
            if target_scratch.exists() and not any(target_scratch.iterdir()):
                target_scratch.rmdir()
            return dry_run(rollout_path, target_scratch, now=now,
                           native_invocation_id=default_invocation_id(now, driver=driver), driver=driver)

        due = due_state(now)
        if due["state"] == "NOT_YET_DUE":
            return {
                "item": "CC-143",
                "route": profile["route"],
                "driver": profile["driver"],
                "route_state": "NOT_YET_DUE",
                **due,
                "public_write_performed": False,
                "checked_at_utc": now.isoformat(),
            }

        rollout = json.loads(Path(rollout_path).read_bytes())
        route_root = Path(rollout["editorial_output_root"]) / "owner-manual" / "route-1900"

        def _make_run_dir(instant: datetime) -> tuple[Path, str]:
            stamp = instant.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            candidate = route_root / stamp
            if candidate.exists():
                instant = instant + timedelta(seconds=1)
                stamp = instant.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                candidate = route_root / stamp
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate, default_invocation_id(instant, driver=driver)

        run_dir, invocation_id = _make_run_dir(now)
        pre = preflight(rollout_path, now=now, native_invocation_id=invocation_id, driver=driver)
        _save_json(run_dir / "01-preflight.json", pre)

        if pre["route_state"] in {"NOT_YET_DUE", "BLOCKED"}:
            result = {
                "item": "CC-143",
                "route": profile["route"],
                "driver": profile["driver"],
                "surface": profile["surface"],
                "digest_id": pre["digest_id"],
                "native_invocation_id": invocation_id,
                "route_state": pre["route_state"],
                "final_route_state": pre["route_state"],
                "blockers": pre["blockers"],
                "first_blocking_cause": pre["blockers"][0] if pre["blockers"] else pre["route_state"],
                "jim_email_code_pending": False,
                "public_write_performed": False,
                "run_dir": str(run_dir),
                "recorded_at_utc": now.isoformat(),
            }
            _save_json(run_dir / "result.json", result)
            if run_day_readback:
                result["day_readback"] = _run_evening_readback(
                    run_dir, rollout, DEFAULT_FEED, now=now,
                    stored_only=stored_only_readback, fetcher=readback_fetcher,
                )
            return result

        if profile["driver"] == "codex-astra":
            codex_meta = _run_codex_astra_pass(
                rollout_path=rollout_path,
                run_dir=run_dir,
                invocation_id=invocation_id,
                profile=profile,
                slot_file=codex_slot_file,
                min_gap_seconds=codex_min_gap_seconds,
                codex_runner=codex_runner,
                now_utc=codex_now_utc,
                sleep=sleep,
            )
            result_path = run_dir / "result.json"
            if result_path.is_file():
                result = json.loads(result_path.read_bytes())
            else:
                result = {
                    "item": "CC-143",
                    "route": profile["route"],
                    "driver": profile["driver"],
                    "surface": profile["surface"],
                    "tool_name": profile["tool_name"],
                    "digest_id": pre["digest_id"],
                    "native_invocation_id": invocation_id,
                    "route_state": "CODEX_EXEC_COMPLETED" if codex_meta["returncode"] == 0 else "CODEX_EXEC_FAILED",
                    "final_route_state": "CODEX_EXEC_COMPLETED" if codex_meta["returncode"] == 0 else "CODEX_EXEC_FAILED",
                    "first_blocking_cause": None if codex_meta["returncode"] == 0 else f"CODEX_EXIT_{codex_meta['returncode']}",
                    "jim_email_code_pending": False,
                    "public_write_performed": False,
                    "recorded_at_utc": now.isoformat(),
                }
                _save_json(result_path, result)
            result["codex_astra"] = codex_meta
            result["run_dir"] = str(run_dir)
            if run_day_readback:
                result["day_readback"] = _run_evening_readback(
                    run_dir, rollout, DEFAULT_FEED, now=now,
                    stored_only=stored_only_readback, fetcher=readback_fetcher,
                )
            return result

        if profile["driver"] != "python-neo":
            raise ValueError("DIGEST_1900_UNATTENDED_DRIVER_REQUIRES_PYTHON_NEO_OR_CODEX_ASTRA")

        client = endpoint_client
        if client is None:
            from live_contentops.neo_endpoint_executor_v1 import NeoMcpClient

            client = NeoMcpClient(endpoint=neo_endpoint, task_name="CC-143 daily digest", group_title=DEFAULT_NEO_GROUP)

        pass1, requests_used = _execute_python_neo_pass(
            rollout_path=rollout_path,
            rollout=rollout,
            run_dir=run_dir,
            preflight_doc=pre,
            invocation_id=invocation_id,
            profile=profile,
            now=now,
            endpoint_client=client,
            max_requests=max_requests,
            requests_used=0,
            email_stats_poll_timeout_seconds=email_stats_poll_timeout_seconds,
            email_stats_poll_interval_seconds=email_stats_poll_interval_seconds,
            sleep=sleep,
            monotonic=monotonic,
        )

        # CC-548: at most one catch-up pass when pass1 completed an older digest than today's.
        should_catch_up = (
            pass1["route_state"] in {"CONFIRMED", "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED"}
            and bool(pass1.get("digest_id"))
            and str(pass1["digest_id"]) < str(pre["digest_id"])
            and not pass1.get("jim_email_code_pending")
            and not pass1.get("first_blocking_cause")
            and requests_used < max_requests
        )
        pass1["catch_up_pass"] = "triggered" if should_catch_up else "not needed"
        _save_json(run_dir / "result.json", pass1)

        final_run_dir = run_dir
        final_result = {**pass1, "run_dir": str(run_dir), "passes": [pass1]}
        readback_now = now
        readback_since: str | None = None

        if should_catch_up:
            catch_now = now + timedelta(seconds=1)
            inv_2_probe = default_invocation_id(catch_now, driver=driver)
            pre2 = preflight(rollout_path, now=catch_now, native_invocation_id=inv_2_probe, driver=driver)
            if pre2["route_state"] in {"NOT_YET_DUE", "BLOCKED"}:
                # D-M2: honor pause/blockers before launching catch-up Pass 2.
                blocker = pre2["blockers"][0] if pre2.get("blockers") else pre2["route_state"]
                pass1["catch_up_pass"] = f"blocked:{blocker}"
                _save_json(run_dir / "result.json", pass1)
                final_result = {**pass1, "run_dir": str(run_dir), "passes": [pass1], "pass2_preflight": pre2}
            else:
                # D-H1: capture Pass 1's true previous-day report window BEFORE creating run_dir_2
                # so day_readback_v1.report_window(run_dir_2) never truncates to a 1-second window.
                from live_contentops.day_readback_v1 import report_window as _report_window

                try:
                    prior_window, _ = _report_window(run_dir, now=now)
                    readback_since = prior_window["since_utc"]
                except (OSError, ValueError):
                    readback_since = None

                run_dir_2, inv_2 = _make_run_dir(catch_now)
                if inv_2 != inv_2_probe:
                    pre2 = preflight(rollout_path, now=catch_now, native_invocation_id=inv_2, driver=driver)
                _save_json(run_dir_2 / "01-preflight.json", pre2)
                pass2, requests_used = _execute_python_neo_pass(
                    rollout_path=rollout_path,
                    rollout=rollout,
                    run_dir=run_dir_2,
                    preflight_doc=pre2,
                    invocation_id=inv_2,
                    profile=profile,
                    now=catch_now,
                    endpoint_client=client,
                    max_requests=max_requests,
                    requests_used=requests_used,
                    email_stats_poll_timeout_seconds=email_stats_poll_timeout_seconds,
                    email_stats_poll_interval_seconds=email_stats_poll_interval_seconds,
                    sleep=sleep,
                    monotonic=monotonic,
                )
                pass2["catch_up_pass"] = "completed_second_pass"
                _save_json(run_dir_2 / "result.json", pass2)
                final_run_dir = run_dir_2
                readback_now = catch_now
                final_result = {
                    **pass2,
                    "run_dir": str(run_dir_2),
                    "prior_run_dir": str(run_dir),
                    "passes": [pass1, pass2],
                    "public_write_performed": bool(pass1.get("public_write_performed") or pass2.get("public_write_performed")),
                }

        if run_day_readback:
            final_result["day_readback"] = _run_evening_readback(
                final_run_dir,
                rollout,
                DEFAULT_FEED,
                now=readback_now,
                since=readback_since,
                stored_only=stored_only_readback,
                fetcher=readback_fetcher,
            )
        return final_result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("run", "preflight", "resume", "dry-run", "render-xml"))
    parser.add_argument("--rollout", type=Path, default=DEFAULT_ROLLOUT)
    parser.add_argument("--driver", default=DEFAULT_DRIVER,
                        help="Execution surface/driver: python-neo (default, deterministic Python), codex-astra (gpt-6.2-astra max), or codex-desktop")
    parser.add_argument("--now", help="UTC ISO clock; dry-run simulation only")
    parser.add_argument("--native-invocation-id")
    parser.add_argument("--scratch", type=Path, help="dry-run: a new folder on C: for the copied store")
    parser.add_argument("--output", type=Path, help="also write the JSON result here")
    parser.add_argument("--dry-run", action="store_true", help="run: execute copied-store dry-run with zero production or network writes")
    parser.add_argument("--lock-path", type=Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument("--stop-path", type=Path, default=DEFAULT_STOP_PATH)
    parser.add_argument("--neo-endpoint", default=DEFAULT_NEO_ENDPOINT)
    parser.add_argument("--codex-slot-file", type=Path, default=None)
    parser.add_argument("--max-requests", type=int, default=MAX_REQUESTS_PER_RUN)
    parser.add_argument("--email-stats-poll-timeout", type=float, default=None,
                        help="run: bounded seconds to poll Substack post stats for email confirmation (default 1500s / 25m)")
    parser.add_argument("--email-stats-poll-interval", type=float, default=None,
                        help="run: seconds between Substack post stats reloads during readback (default 120s)")
    parser.add_argument("--no-day-readback", action="store_true")
    parser.add_argument("--stored-only-readback", action="store_true")
    parser.add_argument("--simulate-identity", action="store_true",
                        help="dry-run: on the copy, answer the read-only identity request with a labelled simulated return and stop at the next request")
    parser.add_argument("--user-id", default="JP", help="render-xml: Windows Task Scheduler Principal UserId")
    args = parser.parse_args(argv)
    try:
        if args.command == "render-xml":
            from live_contentops.daily_digest_neo_v1 import render_digest_task_xml

            xml_text = render_digest_task_xml(user_id=args.user_id, driver=args.driver, enabled=False)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(xml_text, encoding="utf-8")
            else:
                sys.stdout.write(xml_text)
            return 0
        if args.command == "run":
            if args.now:
                parser.error("run uses the real clock")
            result = run_digest_1900(
                args.rollout,
                driver=args.driver,
                lock_path=args.lock_path,
                stop_path=args.stop_path,
                neo_endpoint=args.neo_endpoint,
                codex_slot_file=args.codex_slot_file,
                max_requests=args.max_requests,
                email_stats_poll_timeout_seconds=args.email_stats_poll_timeout,
                email_stats_poll_interval_seconds=args.email_stats_poll_interval,
                run_day_readback=not args.no_day_readback,
                stored_only_readback=args.stored_only_readback,
                is_dry_run=args.dry_run,
                scratch=args.scratch,
            )
        elif args.command == "preflight":
            if args.now:
                parser.error("preflight uses the real clock")
            result = preflight(args.rollout, native_invocation_id=args.native_invocation_id, driver=args.driver)
        elif args.command == "resume":
            if args.now or not args.native_invocation_id:
                parser.error("resume uses the real clock and needs the preflight's --native-invocation-id")
            result = resume(args.rollout, args.native_invocation_id, driver=args.driver)
        else:
            if not args.scratch:
                parser.error("dry-run requires --scratch")
            result = dry_run(args.rollout, args.scratch, now=_utc(args.now) if args.now else None,
                             native_invocation_id=args.native_invocation_id or "cc143-route-dry-run",
                             simulate_identity=args.simulate_identity, driver=args.driver)
    except (ValueError, OSError, KeyError, sqlite3.Error, RuntimeError) as exc:
        result = {"item": "CC-143", "route_state": "FAILED", "cause": f"{type(exc).__name__}: {exc}",
                  "public_write_performed": False}
        print(json.dumps(result, ensure_ascii=True))
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=True, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
