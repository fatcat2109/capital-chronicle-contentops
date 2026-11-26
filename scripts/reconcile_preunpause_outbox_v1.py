"""Pre-unpause ContentOps outbox audit & dry-run-default reconciliation CLI (CC-692 / Cycle #31).

Strictly ``--dry-run`` by default (zero SQLite writes; opens read-only). Writes require explicit
``--apply`` AND an explicit operator-supplied ``--db`` path, and fail closed whenever:
- ``restored.json`` already exists under the pause control directory, OR
- any ContentOps writer/supervisor lock (active SQLite lease, fresh heartbeat, held ``.lock``
  file / live PID, or running live supervisor process when targeting the production store) is active.

Reconciliation contract:
- Subgroup A (expired un-dispatched READY Substack ``plan_analysis_page`` rows, e.g. ``#13``):
  retires outbox row to ``PLAN_PAGE_EXPIRED_STALE_NO_WRITE`` and parent internal page to ``SETTLED``
  (only when zero sibling dispatches are active/confirmed/unknown).
- Subgroup B (Substack ``DISPATCH_ATTEMPT_STARTED`` / ``UNKNOWN_WRITE`` / ``NATIVE_NEO_TOOL_PENDING`` /
  ``RECONCILED_ABSENT_SAFE_TO_RETRY``, e.g. ``#14`` ``dispatch_4f58...``): readback-first gate.
  NEVER auto-retires without durable verified absence proof (``RECONCILED_ABSENT_SAFE_TO_RETRY``
  dispatch + reconciliation, zero readbacks observing ``write_exists``/``verified``/public identity,
  and latest readback observing ``write_absent=True``).
- Subgroup D (``NATIVE_NEO_TOOL_PENDING`` under terminal ``SUPERSEDED_NOT_POSTED``/``STALE_NOT_POSTED``/``SETTLED``
  parent, e.g. ``#01``): settles outbox row to ``PLAN_POST_SETTLED`` while preserving exact dispatch state.
- Expired derivative ``READY`` rows (``dispatch is None``): retires to ``DERIVATIVE_EXPIRED_STALE_NO_WRITE``.
- Dead-parent / late ``UNKNOWN_WRITE`` polling targets (``O56/O58/O60/O61``): settles outbox row to
  ``PLAN_POST_SETTLED`` (and late link parent to ``SETTLED``) while preserving ``platform_dispatches.status == 'UNKNOWN_WRITE'``.
- ``CC603_PREPARED`` backfill rows (9 rows): left untouched and reported by default; retired to
  ``SETTLED`` only when explicit ``--retire-cc603-backfill`` is supplied with ``--apply``.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from typing import Any, Callable, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.destination_transport_registry_v1 import (  # noqa: E402
    canonical_transport_registry,
)
from live_contentops.durable_operational_store_v1 import (  # noqa: E402
    ContentOpsDurableStore,
    WorkItemNotFoundError,
)
from live_contentops.publication_coordinator_v1 import (  # noqa: E402
    ATTEMPT_STARTED,
    DEFINITE_NO_WRITE,
    DERIVATIVE_EXPIRED_STALE_NO_WRITE,
    DISPATCH_CONFIRMED,
    DurablePublicationCoordinator,
    NATIVE_NEO_PENDING,
    PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
    RECONCILED_ABSENT_SAFE_TO_RETRY,
    RECONCILED_CONFIRMED,
    UNKNOWN_WRITE,
    _canonical_json,
    _parse_utc,
    _valid_substack_canonical_url,
    substack_plan_page_staleness,
)
from live_contentops.published_content_v1 import PRODUCTION_STORE  # noqa: E402


SCHEMA_VERSION = "contentops.preunpause_outbox_reconciliation.v1"
SETTLED_COPY = "PLAN_POST_SETTLED"
SETTLED_POST = "SETTLED"
DEAD_PARENT_STATUSES = frozenset({
    "SUPERSEDED_NOT_POSTED",
    "STALE_NOT_POSTED",
    SETTLED_POST,
})
SUBSTACK_READBACK_GATED_DISPATCH_STATUSES = frozenset({
    ATTEMPT_STARTED,
    UNKNOWN_WRITE,
    NATIVE_NEO_PENDING,
    RECONCILED_ABSENT_SAFE_TO_RETRY,
})
SUBSTACK_EXCLUDED_OUTBOX_STATUSES = frozenset({
    PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
    "SUPERSEDED_UNSENT_MEDIA_REVISION",
    "UNSENT_MEDIA_SUPERSEDED",
    DEFINITE_NO_WRITE,
    DISPATCH_CONFIRMED,
})
_OTHER_LIVE_WRITER_PROCESS_PATTERN = (
    r"live_contentops\.cli.*daily-app"
    r"|daily_app_supervisor"
    r"|plan_status_posts\.py"
    r"|plan_analysis_pages\.py"
    r"|manual_desk_tick\.py"
    r"|market_wrap_job_v1"
    r"|run_v1_simple_gemini_scheduler\.py"
    r"|run_daily_digest_1900\.py"
    r"|run_native_neo_executor\.py"
    r"|run_sourced_replies\.py"
    r"|substack_growth\.py"
)
LIVE_WRITER_PROCESS_PATTERN = (
    _OTHER_LIVE_WRITER_PROCESS_PATTERN
    + r"|reconcile_preunpause_outbox_v1\.py"
)
_SHELL_WRAPPER_NAMES = frozenset({"cmd.exe", "powershell.exe", "pwsh.exe"})
POLLING_UNKNOWN_WRITE_DESTINATIONS = frozenset({"x", "substack_notes"})
LATE_LINK_HOURS = 24
FRESH_HEARTBEAT_MINUTES = 10

EXIT_OK = 0
EXIT_USAGE_REFUSED = 2
EXIT_INTERLOCK_REFUSED = 3

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _resolve_interlock_clock(
    *,
    now: Optional[datetime] = None,
    interlock_now: Optional[datetime] = None,
) -> datetime:
    """Resolve liveness interlock clock so future --now-utc can never expire live leases/heartbeats."""
    if interlock_now is not None:
        return _ensure_utc(interlock_now)
    wall_now = datetime.now(timezone.utc)
    if now is not None:
        return min(wall_now, _ensure_utc(now))
    return wall_now


def _resolve_apply_expiry_clock(
    *,
    db_path: Path,
    now: Optional[datetime],
    allow_copied_state_clock_override: bool,
    production_store: Optional[Path] = None,
) -> tuple[Optional[datetime], Optional[str], str, bool]:
    """Enforce wall UTC for live --apply; confine clock overrides strictly to explicit copied-state replay."""
    live_db = is_live_production_db(db_path, production_store=production_store)
    if live_db:
        if now is not None or allow_copied_state_clock_override:
            return None, "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE", "REFUSED", True
        return datetime.now(timezone.utc), None, "WALL_UTC", True
    if now is not None:
        if not allow_copied_state_clock_override:
            return None, "APPLY_CLOCK_OVERRIDE_REQUIRES_COPIED_STATE_REPLAY", "REFUSED", False
        return _ensure_utc(now), None, "COPIED_STATE_REPLAY_OVERRIDE", False
    return datetime.now(timezone.utc), None, "WALL_UTC", False


def _parse_json_mapping(raw: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(str(raw or "{}"))
    except (TypeError, ValueError):
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _utc_now(now_utc: str | None = None) -> datetime:
    if not now_utc:
        return datetime.now(timezone.utc)
    parsed = _parse_utc(now_utc)
    if parsed is None:
        raise ValueError(f"INVALID_NOW_UTC:{now_utc}")
    return parsed


def _public_destinations() -> list[str]:
    base = {
        "site",
        "substack",
        "telegram",
        "discord",
        "threads",
        "facebook_page",
        "instagram_business",
        "linkedin",
        "linkedin_company",
        "x",
        "youtube",
        "substack_notes",
    }
    try:
        reg = canonical_transport_registry()
        base.update(str(r["destination_key"]) for r in reg.get("surfaces") or [] if r.get("destination_key"))
    except Exception:
        pass
    return sorted(base)


def _open_readonly_sqlite(db_path: Path) -> sqlite3.Connection:
    """Open SQLite strictly read-only; use immutable=1 when WAL is absent/empty for zero FS touch."""
    wal_path = Path(f"{db_path}-wal")
    use_immutable = (not wal_path.exists()) or wal_path.stat().st_size == 0
    query = "mode=ro&immutable=1" if use_immutable else "mode=ro"
    uri = f"file:{db_path.resolve().as_posix()}?{query}"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0, isolation_level=None, cached_statements=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def is_live_production_db(db_path: Path, *, production_store: Optional[Path] = None) -> bool:
    target_prod = PRODUCTION_STORE if production_store is None else production_store
    try:
        if db_path.exists() and target_prod.exists() and os.path.samefile(db_path, target_prod):
            return True
    except OSError:
        pass
    try:
        return os.path.normcase(str(db_path.resolve())) == os.path.normcase(str(target_prod.resolve()))
    except OSError:
        return os.path.normcase(str(db_path)) == os.path.normcase(str(target_prod))


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        return ctypes.get_last_error() == 5
    try:
        code = wintypes.DWORD(0)
        if kernel32.GetExitCodeProcess(wintypes.HANDLE(handle), ctypes.byref(code)):
            return code.value == STILL_ACTIVE
        return False
    finally:
        kernel32.CloseHandle(wintypes.HANDLE(handle))


def _probe_existing_lock_file(path: Path, *, read_only: bool = False) -> Optional[str]:
    """Probe an ALREADY-EXISTING lock file without creating new files; return blocker reason or None."""
    if not path.is_file():
        return None
    if read_only:
        try:
            raw = path.read_bytes()[:4096].decode("utf-8", errors="replace").strip()
        except PermissionError:
            return "OS_LOCK_OR_SHARE_DENIED"
        except OSError:
            return "OS_LOCK_OPEN_FAILED"
    else:
        # 1. Check OS non-blocking advisory/mandatory lock first.
        fd: Optional[int] = None
        try:
            fd = os.open(str(path), os.O_RDWR | getattr(os, "O_BINARY", 0))
        except PermissionError:
            return "OS_LOCK_OR_SHARE_DENIED"
        except OSError:
            return "OS_LOCK_OPEN_FAILED"
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                except OSError:
                    return "OS_LOCK_HELD"
                try:
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    return "OS_LOCK_HELD"
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except OSError:
                    pass
            # 2. Check if the lock file embeds a currently live PID (excluding our own PID).
            os.lseek(fd, 0, os.SEEK_SET)
            raw = os.read(fd, 4096).decode("utf-8", errors="replace").strip()
        finally:
            os.close(fd)
    if raw:
        pid: Optional[int] = None
        if raw.isdigit():
            pid = int(raw)
        else:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, Mapping) and parsed.get("pid") is not None:
                    pid = int(parsed["pid"])
            except (ValueError, TypeError):
                pid = None
        if pid is not None and pid != os.getpid() and _pid_is_alive(pid):
            return f"LOCK_PID_ALIVE:{pid}"
    return None


def _default_live_writer_process_scanner() -> list[dict[str, Any]]:
    """Detect running ContentOps writer/supervisor processes on Windows (live DB apply only)."""
    if os.name != "nt":
        return []
    ps_pattern = LIVE_WRITER_PROCESS_PATTERN.replace("'", "''")
    ps_cmd = (
        "Get-CimInstance Win32_Process | "
        f"Where-Object {{ $_.ProcessId -ne $PID -and $_.CommandLine -match '{ps_pattern}' }} | "
        "Select-Object ProcessId, Name, CommandLine | ConvertTo-Json -Compress"
    )
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=creationflags,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"PROCESS_SCAN_RC_{proc.returncode}")
    out = proc.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    rows = data if isinstance(data, list) else [data]
    self_pid = os.getpid()
    parent_pid = os.getppid()
    results: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, Mapping):
            continue
        pid = int(r.get("ProcessId") or 0)
        if pid == self_pid:
            continue
        name = str(r.get("Name") or "")
        cmd = str(r.get("CommandLine") or "")
        if (
            pid == parent_pid
            and name.lower() in _SHELL_WRAPPER_NAMES
            and not re.search(_OTHER_LIVE_WRITER_PROCESS_PATTERN, cmd, re.IGNORECASE)
        ):
            continue
        results.append(
            {
                "pid": pid,
                "name": name,
                "command_line": cmd[:240],
            }
        )
    return results


def _collect_sqlite_liveness_blockers(
    conn: sqlite3.Connection, *, liveness_now: datetime
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    has_leases = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='leases'"
    ).fetchone() is not None
    if has_leases:
        for row in conn.execute(
            "SELECT lease_id, lease_key, owner_ref, expires_at FROM leases WHERE status='ACTIVE'"
        ):
            expires_at = _parse_utc(row["expires_at"])
            if expires_at is None or expires_at > liveness_now:
                blockers.append(
                    {
                        "code": "ACTIVE_SQLITE_LEASE",
                        "lease_id": str(row["lease_id"]),
                        "lease_key": str(row["lease_key"]),
                        "owner_ref": str(row["owner_ref"]),
                        "expires_at": str(row["expires_at"]),
                    }
                )
    has_heartbeats = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='heartbeats'"
    ).fetchone() is not None
    if has_heartbeats:
        fresh_cutoff = liveness_now - timedelta(minutes=FRESH_HEARTBEAT_MINUTES)
        for row in conn.execute(
            "SELECT heartbeat_id, worker_id, last_seen_at FROM heartbeats WHERE status='ALIVE'"
        ):
            last_seen = _parse_utc(row["last_seen_at"])
            if last_seen is None or last_seen >= fresh_cutoff:
                blockers.append(
                    {
                        "code": "ACTIVE_SUPERVISOR_HEARTBEAT",
                        "heartbeat_id": str(row["heartbeat_id"]),
                        "worker_id": str(row["worker_id"]),
                        "last_seen_at": str(row["last_seen_at"]),
                    }
                )
    return blockers


def check_apply_interlocks(
    db_path: Path,
    *,
    now: Optional[datetime] = None,
    interlock_now: Optional[datetime] = None,
    control_dir: Optional[Path] = None,
    extra_lock_paths: Sequence[Path] = (),
    production_store: Optional[Path] = None,
    check_live_processes: Optional[bool] = None,
    read_only_lock_probe: bool = False,
    process_scanner: Callable[[], list[dict[str, Any]]] = _default_live_writer_process_scanner,
) -> dict[str, Any]:
    """Fail-closed interlock verification prior to any ``--apply`` write."""
    blockers: list[dict[str, Any]] = []
    target_prod = PRODUCTION_STORE if production_store is None else production_store
    liveness_now = _resolve_interlock_clock(now=now, interlock_now=interlock_now)
    live_db = is_live_production_db(db_path, production_store=target_prod)
    effective_control_dir = control_dir if control_dir is not None else (db_path.parent / "control")

    # 1. restored.json check (pause lifted => refuse pre-unpause mutation).
    control_roots: list[Path] = [effective_control_dir]
    if live_db:
        live_control = target_prod.parent / "control"
        if os.path.normcase(str(live_control)) != os.path.normcase(str(effective_control_dir)):
            control_roots.append(live_control)
    seen_restored: set[str] = set()
    for root in control_roots:
        candidates: list[Path] = [root / "restored.json"]
        if root.is_dir():
            candidates.extend(sorted(root.glob("pause-*/restored.json")))
        for candidate in candidates:
            norm = os.path.normcase(str(candidate))
            if norm not in seen_restored and candidate.exists():
                seen_restored.add(norm)
                blockers.append({"code": "RESTORED_JSON_EXISTS", "path": str(candidate)})

    # 2. Active SQLite leases & fresh supervisor heartbeats (read-only, evaluated on liveness_now).
    conn = _open_readonly_sqlite(db_path)
    try:
        blockers.extend(_collect_sqlite_liveness_blockers(conn, liveness_now=liveness_now))
    finally:
        conn.close()

    # 3. Existing filesystem writer/supervisor lock files (never creates files).
    lock_candidates: list[Path] = list(extra_lock_paths)
    for folder in (db_path.parent, effective_control_dir, db_path.parent / "locks"):
        if folder.is_dir():
            lock_candidates.extend(sorted(folder.glob("*.lock")))
    seen_locks: set[str] = set()
    for lock_file in lock_candidates:
        norm = os.path.normcase(str(lock_file))
        if norm in seen_locks:
            continue
        seen_locks.add(norm)
        reason = _probe_existing_lock_file(lock_file, read_only=read_only_lock_probe)
        if reason:
            blockers.append(
                {
                    "code": "ACTIVE_WRITER_LOCK_FILE",
                    "path": str(lock_file),
                    "reason": reason,
                }
            )

    # 4. Live writer/supervisor OS process check when targeting live DB (or explicitly enabled).
    should_scan_processes = live_db if check_live_processes is None else bool(check_live_processes)
    if should_scan_processes:
        try:
            running = process_scanner()
        except Exception as exc:
            blockers.append(
                {
                    "code": "LIVE_PROCESS_CHECK_UNAVAILABLE",
                    "error": f"{type(exc).__name__}:{str(exc)[:160]}",
                }
            )
        else:
            for proc_info in running:
                blockers.append({"code": "ACTIVE_WRITER_OR_SUPERVISOR_PROCESS", **proc_info})

    return {
        "ok": len(blockers) == 0,
        "live_production_db": live_db,
        "control_dir": str(effective_control_dir),
        "interlock_clock_utc": liveness_now.isoformat().replace("+00:00", "Z"),
        "blockers": blockers,
    }


def _get_outbox_row(conn: sqlite3.Connection, message_id: str) -> Optional[dict[str, Any]]:
    row = conn.execute(
        "SELECT message_id, work_item_id, destination, payload, status, created_at "
        "FROM outbox_messages WHERE message_id=?",
        (message_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def _canonical_publication_clock_ro(
    conn: sqlite3.Connection, intent: Mapping[str, Any]
) -> Optional[datetime]:
    ids = DurablePublicationCoordinator._ids(
        str(intent.get("work_item_id") or ""),
        str(intent.get("plan_hash") or ""),
        "substack",
    )
    disp = conn.execute(
        "SELECT status, public_object_id, public_object_url FROM platform_dispatches WHERE dispatch_id=?",
        (ids["dispatch_id"],),
    ).fetchone()
    if disp is None or disp["status"] != DISPATCH_CONFIRMED:
        return None
    if not _valid_substack_canonical_url(disp["public_object_url"]):
        return None
    for row in conn.execute(
        "SELECT readback_data, read_at FROM readbacks WHERE dispatch_id=? ORDER BY read_at, readback_id",
        (ids["dispatch_id"],),
    ):
        try:
            proof = json.loads(str(row["readback_data"] or "{}")).get("readback", {})
        except (TypeError, ValueError):
            continue
        if not isinstance(proof, Mapping) or proof.get("verified") is not True:
            continue
        if proof.get("observed_public_object_id", disp["public_object_id"]) != disp["public_object_id"]:
            continue
        if proof.get("observed_public_object_url", disp["public_object_url"]) != disp["public_object_url"]:
            continue
        observed = _parse_utc(row["read_at"])
        published = _parse_utc(proof.get("observed_published_at_utc"))
        return published if published and observed and published <= observed else observed
    return None


def _derivative_is_stale_ro(
    conn: sqlite3.Connection,
    message: Mapping[str, Any],
    intent: Mapping[str, Any],
    parent_row: Optional[Mapping[str, Any]],
    *,
    now: datetime,
) -> tuple[bool, Optional[str]]:
    publication_window = intent.get("publication_window") or {}
    if isinstance(publication_window, Mapping):
        explicit_expiry = _parse_utc(
            publication_window.get("expires_at_utc")
            or publication_window.get("fresh_until_utc")
        )
        if explicit_expiry is not None:
            if now >= explicit_expiry:
                return True, "PUBLICATION_WINDOW_EXPIRED"
            return False, None

    if parent_row is not None and str(parent_row.get("status") or "") in DEAD_PARENT_STATUSES:
        return True, f"DEAD_PARENT_STATUS:{parent_row['status']}"

    work_item_id = str(intent.get("work_item_id") or "")
    plan_hash = str(intent.get("plan_hash") or "")
    canonical = DurablePublicationCoordinator._ids(work_item_id, plan_hash, "substack")
    has_canonical = _get_outbox_row(conn, canonical["message_id"]) is not None
    if has_canonical:
        clock_base = _canonical_publication_clock_ro(conn, intent)
    else:
        clock_base = _parse_utc(message.get("created_at"))
    horizon = DurablePublicationCoordinator._freshness_horizon(intent)
    if clock_base is not None and now >= clock_base + horizon:
        return True, f"FRESHNESS_HORIZON_EXPIRED:{int(horizon.total_seconds() // 3600)}H"
    return False, None


def _has_verified_absence_proof(
    conn: sqlite3.Connection,
    dispatch: Mapping[str, Any],
    work_item_id: str,
) -> tuple[bool, str]:
    if dispatch.get("public_object_id") or dispatch.get("public_object_url"):
        return False, "PUBLIC_OBJECT_IDENTITY_PRESENT"
    dispatch_status = str(dispatch.get("dispatch_status") or dispatch.get("status") or "")
    if dispatch_status != RECONCILED_ABSENT_SAFE_TO_RETRY:
        return False, f"DISPATCH_NOT_RECONCILED_ABSENT:{dispatch_status or 'NONE'}"
    dispatch_id = str(dispatch["dispatch_id"])
    reconciliation_id = "reconciliation_" + dispatch_id.removeprefix("dispatch_")
    rec = conn.execute(
        "SELECT status FROM reconciliations WHERE reconciliation_id=? AND work_item_id=?",
        (reconciliation_id, work_item_id),
    ).fetchone()
    if rec is None or str(rec["status"] or "") != RECONCILED_ABSENT_SAFE_TO_RETRY:
        return False, f"RECONCILIATION_NOT_ABSENT:{rec['status'] if rec else 'NONE'}"
    readbacks = conn.execute(
        "SELECT readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at, rowid, readback_id",
        (dispatch_id,),
    ).fetchall()
    if not readbacks:
        return False, "NO_VERIFIED_ABSENCE_READBACK"
    latest_obs: Optional[Mapping[str, Any]] = None
    latest_unparseable = False
    for rb in readbacks:
        try:
            raw = json.loads(str(rb["readback_data"] or "{}"))
        except (TypeError, ValueError):
            latest_obs = None
            latest_unparseable = True
            continue
        if not isinstance(raw, Mapping):
            latest_obs = None
            latest_unparseable = True
            continue
        obs = raw.get("readback") if isinstance(raw.get("readback"), Mapping) else raw
        if obs.get("write_exists") is True:
            return False, "CONFLICTING_READBACK_WRITE_EXISTS"
        if obs.get("verified") is True:
            return False, "CONFLICTING_READBACK_VERIFIED"
        if obs.get("observed_public_object_id") or obs.get("observed_public_object_url"):
            return False, "CONFLICTING_READBACK_PUBLIC_IDENTITY"
        latest_obs = obs
        latest_unparseable = False
    if latest_unparseable or latest_obs is None:
        return False, "LATEST_READBACK_UNPARSEABLE"
    if (
        latest_obs.get("write_absent") is True
        and latest_obs.get("write_exists") is not True
        and latest_obs.get("verified") is not True
    ):
        return True, "VERIFIED_DURABLE_ABSENCE_PROOF"
    return False, "NO_VERIFIED_ABSENCE_READBACK"


def _read_reserved_images_readonly(images_path: Optional[Path]) -> list[dict[str, Any]]:
    if images_path is None or not images_path.is_file():
        return []
    latest: dict[str, dict[str, Any]] = {}
    for line in images_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("record_id"):
            latest[str(row["record_id"])] = row
    reserved: list[dict[str, Any]] = []
    for row in sorted(latest.values(), key=lambda r: (str(r.get("recorded_at_utc") or ""), str(r.get("record_id") or ""))):
        if row.get("state") == "RESERVED":
            reserved.append(
                {
                    "record_id": str(row["record_id"]),
                    "piece_id": str(row.get("piece_id") or ""),
                    "day": str(row.get("day") or ""),
                    "recorded_at_utc": str(row.get("recorded_at_utc") or ""),
                    "image_sha256s": [
                        str(img.get("sha256") or "")
                        for img in (row.get("images") or [])
                        if isinstance(img, Mapping)
                    ],
                }
            )
    return reserved


def audit_preunpause_outbox(
    db_path: Path,
    *,
    now: datetime,
    published_images_path: Optional[Path] = None,
    retire_cc603_backfill: bool = False,
) -> dict[str, Any]:
    """Perform a strictly read-only indexed audit of all pre-unpause outbox targets."""
    conn = _open_readonly_sqlite(db_path)
    try:
        dests = _public_destinations()
        placeholders = ",".join("?" for _ in dests)

        subgroup_a: list[dict[str, Any]] = []
        active_substack_plan_pages: list[dict[str, Any]] = []
        non_plan_substack_ready: list[dict[str, Any]] = []
        subgroup_b: list[dict[str, Any]] = []
        subgroup_c: list[dict[str, Any]] = []
        subgroup_d: list[dict[str, Any]] = []
        expired_derivative_ready: list[dict[str, Any]] = []
        active_derivative_ready: list[dict[str, Any]] = []
        dead_parent_unknown_writes: list[dict[str, Any]] = []
        other_unknown_writes: list[dict[str, Any]] = []
        cc603_prepared: list[dict[str, Any]] = []

        # 1. Indexed scan of READY / NATIVE_NEO_TOOL_PENDING across public destinations.
        pub_rows = conn.execute(
            f"""
            SELECT o.message_id, o.work_item_id, o.destination, o.payload, o.status, o.created_at,
                   d.dispatch_id, d.status AS dispatch_status, d.public_object_id, d.public_object_url,
                   p.destination AS parent_destination, p.status AS parent_status, p.created_at AS parent_created_at
            FROM outbox_messages o
            LEFT JOIN platform_dispatches d ON d.message_id = o.message_id
            LEFT JOIN outbox_messages p ON p.message_id = o.work_item_id
            WHERE o.destination IN ({placeholders})
              AND o.status IN ('READY', 'NATIVE_NEO_TOOL_PENDING')
            ORDER BY o.destination, o.created_at, o.message_id
            """,
            dests,
        ).fetchall()

        seen_substack_dispatches: set[str] = set()

        for row in pub_rows:
            msg = dict(row)
            try:
                intent = json.loads(str(msg["payload"] or "{}"))
            except (TypeError, ValueError):
                intent = {}
            if not isinstance(intent, Mapping):
                intent = {}

            destination = str(msg["destination"])
            status = str(msg["status"])
            dispatch_id = msg["dispatch_id"]
            dispatch_status = msg["dispatch_status"]
            parent_row = (
                {
                    "destination": msg["parent_destination"],
                    "status": msg["parent_status"],
                    "created_at": msg["parent_created_at"],
                }
                if msg["parent_status"] is not None
                else None
            )

            # Substack rows (Subgroup A vs Subgroup B vs active/non-plan preserved).
            if destination == "substack":
                if dispatch_id is not None:
                    seen_substack_dispatches.add(str(dispatch_id))
                    disp_dict = {
                        "dispatch_id": str(dispatch_id),
                        "status": str(dispatch_status or ""),
                        "dispatch_status": str(dispatch_status or ""),
                        "public_object_id": msg["public_object_id"],
                        "public_object_url": msg["public_object_url"],
                    }
                    is_plan_page = bool(intent.get("plan_analysis_page"))
                    stale_plan, stale_reason = substack_plan_page_staleness(
                        lambda mid: _get_outbox_row(conn, mid),
                        msg,
                        intent,
                        now=now,
                    )
                    verified_absent, absence_reason = _has_verified_absence_proof(
                        conn, disp_dict, str(msg["work_item_id"])
                    )
                    can_settle = bool(is_plan_page and verified_absent and stale_plan)
                    subgroup_b.append(
                        {
                            "message_id": str(msg["message_id"]),
                            "work_item_id": str(msg["work_item_id"]),
                            "dispatch_id": str(dispatch_id),
                            "outbox_status": status,
                            "dispatch_status": str(dispatch_status or ""),
                            "created_at": str(msg["created_at"]),
                            "plan_analysis_page": intent.get("plan_analysis_page"),
                            "stale_plan": stale_plan,
                            "stale_reason": stale_reason,
                            "verified_absence_proof": verified_absent,
                            "absence_check_reason": absence_reason,
                            "eligible_for_apply": can_settle,
                            "action": (
                                "SETTLE_VERIFIED_ABSENT_EXPIRED_SUBSTACK_PLAN_PAGE"
                                if can_settle
                                else (
                                    "PRESERVE_ACTIVE_OR_NON_PLAN_SUBSTACK_VERIFIED_ABSENT"
                                    if verified_absent
                                    else "HOLD_READBACK_REQUIRED_NEVER_AUTO_RETIRE"
                                )
                            ),
                        }
                    )
                    continue

                if status == "READY":
                    if intent.get("plan_analysis_page"):
                        stale_plan, stale_reason = substack_plan_page_staleness(
                            lambda mid: _get_outbox_row(conn, mid),
                            msg,
                            intent,
                            now=now,
                        )
                        parent_full = _get_outbox_row(conn, str(intent["plan_analysis_page"]))
                        entry_deadline_utc = None
                        plan_id = None
                        if parent_full:
                            try:
                                parent_payload = json.loads(str(parent_full["payload"] or "{}"))
                                sp = parent_payload.get("source_plan") or {}
                                entry_deadline_utc = sp.get("entry_deadline_utc") or sp.get("expires_at_utc")
                                plan_id = parent_payload.get("plan_id") or sp.get("plan_id")
                            except (TypeError, ValueError):
                                pass
                        entry = {
                            "message_id": str(msg["message_id"]),
                            "work_item_id": str(msg["work_item_id"]),
                            "plan_id": plan_id,
                            "created_at": str(msg["created_at"]),
                            "entry_deadline_utc": entry_deadline_utc,
                            "parent_status": msg["parent_status"],
                            "stale_reason": stale_reason,
                            "target_outbox_status": PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
                            "target_parent_status": SETTLED_POST if parent_full else None,
                        }
                        if stale_plan:
                            subgroup_a.append(entry)
                        else:
                            active_substack_plan_pages.append(entry)
                    else:
                        non_plan_substack_ready.append(
                            {
                                "message_id": str(msg["message_id"]),
                                "work_item_id": str(msg["work_item_id"]),
                                "created_at": str(msg["created_at"]),
                                "resolved_article_mode": intent.get("resolved_article_mode"),
                                "action": "PRESERVE_NON_PLAN_SUBSTACK_ARTICLE",
                            }
                        )
                continue

            # Subgroup D: NATIVE_NEO_TOOL_PENDING under dead parent.
            if status == NATIVE_NEO_PENDING or dispatch_status == NATIVE_NEO_PENDING:
                if (
                    parent_row is not None
                    and str(parent_row.get("status") or "") in DEAD_PARENT_STATUSES
                    and not msg["public_object_id"]
                    and not msg["public_object_url"]
                ):
                    subgroup_d.append(
                        {
                            "message_id": str(msg["message_id"]),
                            "work_item_id": str(msg["work_item_id"]),
                            "destination": destination,
                            "dispatch_id": str(dispatch_id) if dispatch_id else None,
                            "outbox_status": status,
                            "dispatch_status": str(dispatch_status or ""),
                            "parent_status": str(parent_row["status"]),
                            "created_at": str(msg["created_at"]),
                            "target_outbox_status": SETTLED_COPY,
                            "dispatch_status_preserved": str(dispatch_status or ""),
                        }
                    )
                continue

            # Non-substack READY rows with dispatch is None (Subgroups E/F/G/H/I).
            if status == "READY" and dispatch_id is None:
                is_stale, stale_reason = _derivative_is_stale_ro(
                    conn, msg, intent, parent_row, now=now
                )
                entry = {
                    "message_id": str(msg["message_id"]),
                    "work_item_id": str(msg["work_item_id"]),
                    "destination": destination,
                    "created_at": str(msg["created_at"]),
                    "parent_destination": msg["parent_destination"],
                    "parent_status": msg["parent_status"],
                    "stale_reason": stale_reason,
                    "target_outbox_status": DERIVATIVE_EXPIRED_STALE_NO_WRITE,
                }
                if is_stale:
                    expired_derivative_ready.append(entry)
                else:
                    active_derivative_ready.append(entry)

        # 2. Catch any Substack DISPATCH_ATTEMPT_STARTED / UNKNOWN_WRITE / NATIVE_NEO_TOOL_PENDING /
        #    RECONCILED_ABSENT_SAFE_TO_RETRY even if outbox_messages.status already flipped away from READY,
        #    excluding already-retired or superseded outbox rows.
        sub_dispatches = conn.execute(
            """
            SELECT d.dispatch_id, d.message_id, d.status AS dispatch_status,
                   d.public_object_id, d.public_object_url,
                   o.work_item_id, o.destination, o.payload, o.status AS outbox_status, o.created_at
            FROM platform_dispatches d
            JOIN outbox_messages o ON o.message_id = d.message_id
            WHERE d.platform = 'substack'
              AND d.status IN (
                  'DISPATCH_ATTEMPT_STARTED',
                  'UNKNOWN_WRITE',
                  'NATIVE_NEO_TOOL_PENDING',
                  'RECONCILED_ABSENT_SAFE_TO_RETRY'
              )
              AND o.status NOT IN (
                  'PLAN_PAGE_EXPIRED_STALE_NO_WRITE',
                  'SUPERSEDED_UNSENT_MEDIA_REVISION',
                  'UNSENT_MEDIA_SUPERSEDED',
                  'DEFINITE_NO_WRITE',
                  'DISPATCH_CONFIRMED'
              )
            ORDER BY o.created_at, d.dispatch_id
            """
        ).fetchall()
        for row in sub_dispatches:
            if str(row["dispatch_id"]) in seen_substack_dispatches:
                continue
            msg = dict(row)
            try:
                intent = json.loads(str(msg["payload"] or "{}"))
            except (TypeError, ValueError):
                intent = {}
            if not isinstance(intent, Mapping):
                intent = {}
            is_plan_page = bool(intent.get("plan_analysis_page"))
            if str(msg["dispatch_status"]) == RECONCILED_ABSENT_SAFE_TO_RETRY and not is_plan_page:
                continue
            stale_plan, stale_reason = substack_plan_page_staleness(
                lambda mid: _get_outbox_row(conn, mid),
                msg,
                intent,
                now=now,
            )
            verified_absent, absence_reason = _has_verified_absence_proof(
                conn, msg, str(msg["work_item_id"])
            )
            can_settle = bool(is_plan_page and verified_absent and stale_plan)
            subgroup_b.append(
                {
                    "message_id": str(msg["message_id"]),
                    "work_item_id": str(msg["work_item_id"]),
                    "dispatch_id": str(msg["dispatch_id"]),
                    "outbox_status": str(msg["outbox_status"]),
                    "dispatch_status": str(msg["dispatch_status"]),
                    "created_at": str(msg["created_at"]),
                    "plan_analysis_page": intent.get("plan_analysis_page"),
                    "stale_plan": stale_plan,
                    "stale_reason": stale_reason,
                    "verified_absence_proof": verified_absent,
                    "absence_check_reason": absence_reason,
                    "eligible_for_apply": can_settle,
                    "action": (
                        "SETTLE_VERIFIED_ABSENT_EXPIRED_SUBSTACK_PLAN_PAGE"
                        if can_settle
                        else (
                            "PRESERVE_ACTIVE_OR_NON_PLAN_SUBSTACK_VERIFIED_ABSENT"
                            if verified_absent
                            else "HOLD_READBACK_REQUIRED_NEVER_AUTO_RETIRE"
                        )
                    ),
                }
            )

        # 3. Subgroup C (PUBLISHING internal:plan-status-post) & CC603_PREPARED backfill rows.
        for row in conn.execute(
            """
            SELECT message_id, work_item_id, destination, payload, status, created_at
            FROM outbox_messages
            WHERE destination = 'internal:plan-status-post'
              AND status IN ('PUBLISHING', 'CC603_PREPARED')
            ORDER BY status, created_at, message_id
            """
        ):
            try:
                payload = json.loads(str(row["payload"] or "{}"))
            except (TypeError, ValueError):
                payload = {}
            if not isinstance(payload, Mapping):
                payload = {}
            if row["status"] == "PUBLISHING":
                subgroup_c.append(
                    {
                        "message_id": str(row["message_id"]),
                        "work_item_id": str(row["work_item_id"]),
                        "created_at": str(row["created_at"]),
                        "at_utc": payload.get("at_utc"),
                        "plan_id": payload.get("plan_id"),
                        "action": "INFORMATIONAL_AUTO_SETTLES_ON_TICK",
                    }
                )
            elif row["status"] == "CC603_PREPARED":
                cc603_prepared.append(
                    {
                        "message_id": str(row["message_id"]),
                        "work_item_id": str(row["work_item_id"]),
                        "created_at": str(row["created_at"]),
                        "kind": payload.get("kind"),
                        "plan_id": payload.get("plan_id"),
                        "symbol": payload.get("symbol"),
                        "eligible_for_apply": bool(retire_cc603_backfill),
                        "target_outbox_status": SETTLED_POST if retire_cc603_backfill else None,
                        "action": (
                            "RETIRE_CC603_BACKFILL_EXPLICIT_POLICY"
                            if retire_cc603_backfill
                            else "LEAVE_UNTOUCHED_DEFAULT_POLICY"
                        ),
                    }
                )

        # 4. Non-settled non-Substack UNKNOWN_WRITE rows: identify dead-parent / late polling targets (O56/O58/O60/O61).
        #    (Substack UNKNOWN_WRITE rows are already audited and readback-gated in Subgroup B above.)
        uw_rows = conn.execute(
            """
            SELECT d.dispatch_id, d.message_id, d.platform, d.status AS dispatch_status,
                   d.public_object_id, d.public_object_url,
                   o.work_item_id, o.payload, o.status AS outbox_status, o.created_at,
                   p.destination AS parent_destination, p.status AS parent_status,
                   p.payload AS parent_payload, p.created_at AS parent_created_at
            FROM platform_dispatches d
            JOIN outbox_messages o ON o.message_id = d.message_id
            LEFT JOIN outbox_messages p ON p.message_id = o.work_item_id
            WHERE d.status = 'UNKNOWN_WRITE'
              AND d.platform <> 'substack'
              AND o.status <> 'PLAN_POST_SETTLED'
            ORDER BY o.work_item_id, d.platform, d.dispatch_id
            """
        ).fetchall()
        for row in uw_rows:
            try:
                intent = json.loads(str(row["payload"] or "{}"))
            except (TypeError, ValueError):
                intent = {}
            if not isinstance(intent, Mapping):
                intent = {}
            platform = str(row["platform"])
            work_item_id = str(row["work_item_id"])
            parent_status = str(row["parent_status"] or "")
            is_plan_status_post = bool(intent.get("plan_status_post"))
            link_id = str(intent.get("plan_analysis_link") or "")
            is_plan_analysis_link = link_id.startswith("plan-analysis-")

            polling_reason: Optional[str] = None
            settle_parent_link = False
            if platform in POLLING_UNKNOWN_WRITE_DESTINATIONS:
                if is_plan_status_post and parent_status in DEAD_PARENT_STATUSES:
                    polling_reason = f"DEAD_PARENT_UNKNOWN_WRITE_POLL_TARGET:{parent_status}"
                elif is_plan_analysis_link:
                    ref_clock = _parse_utc(row["parent_created_at"]) or _parse_utc(row["created_at"])
                    if row["parent_payload"]:
                        try:
                            parent_json = json.loads(str(row["parent_payload"]))
                            orig_key = parent_json.get("original_key")
                            if orig_key:
                                orig_row = _get_outbox_row(conn, str(orig_key))
                                if orig_row:
                                    orig_payload = json.loads(str(orig_row["payload"] or "{}"))
                                    if orig_payload.get("at_utc"):
                                        ref_clock = _parse_utc(orig_payload["at_utc"]) or ref_clock
                        except (TypeError, ValueError):
                            pass
                    if ref_clock is not None and (now - ref_clock).total_seconds() > LATE_LINK_HOURS * 3600:
                        polling_reason = "LATE_PLAN_ANALYSIS_LINK_UNKNOWN_WRITE_POLL_TARGET"
                        settle_parent_link = True

            record = {
                "dispatch_id": str(row["dispatch_id"]),
                "message_id": str(row["message_id"]),
                "work_item_id": work_item_id,
                "platform": platform,
                "outbox_status": str(row["outbox_status"]),
                "dispatch_status": str(row["dispatch_status"]),
                "parent_destination": row["parent_destination"],
                "parent_status": row["parent_status"],
                "created_at": str(row["created_at"]),
            }
            if polling_reason is not None:
                dead_parent_unknown_writes.append(
                    {
                        **record,
                        "reason": polling_reason,
                        "target_outbox_status": SETTLED_COPY,
                        "settle_parent_link": settle_parent_link,
                        "dispatch_status_preserved": UNKNOWN_WRITE,
                    }
                )
            else:
                other_unknown_writes.append(
                    {
                        **record,
                        "action": "PRESERVE_UNKNOWN_WRITE_FOR_EXPLICIT_READBACK",
                    }
                )

        # 5. Read-only RESERVED image inventory (never mutated by this tool).
        images_file = (
            published_images_path
            if published_images_path is not None
            else (db_path.parent / "published_images_v1.jsonl")
        )
        reserved_images = _read_reserved_images_readonly(images_file)

        return {
            "schema_version": SCHEMA_VERSION,
            "db_path": str(db_path),
            "now_utc": now.isoformat().replace("+00:00", "Z"),
            "retire_cc603_backfill_flag": bool(retire_cc603_backfill),
            "counts": {
                "subgroup_a_expired_substack_plan_pages": len(subgroup_a),
                "active_substack_plan_pages_preserved": len(active_substack_plan_pages),
                "non_plan_substack_ready_preserved": len(non_plan_substack_ready),
                "subgroup_b_substack_readback_gated": len(subgroup_b),
                "subgroup_b_readback_held": sum(1 for r in subgroup_b if not r["eligible_for_apply"]),
                "subgroup_b_verified_absent_eligible": sum(1 for r in subgroup_b if r["eligible_for_apply"]),
                "subgroup_c_late_publishing_parents": len(subgroup_c),
                "subgroup_d_dead_parent_native_neo_pending": len(subgroup_d),
                "expired_derivative_ready_rows": len(expired_derivative_ready),
                "active_derivative_ready_preserved": len(active_derivative_ready),
                "dead_parent_unknown_write_polling_targets": len(dead_parent_unknown_writes),
                "other_unknown_writes_preserved": len(other_unknown_writes),
                "cc603_backfill_prepared": len(cc603_prepared),
                "reserved_images_readonly": len(reserved_images),
            },
            "subgroup_a_expired_substack_plan_pages": subgroup_a,
            "active_substack_plan_pages_preserved": active_substack_plan_pages,
            "non_plan_substack_ready_preserved": non_plan_substack_ready,
            "subgroup_b_substack_readback_gated": subgroup_b,
            "subgroup_c_late_publishing_parents": subgroup_c,
            "subgroup_d_dead_parent_native_neo_pending": subgroup_d,
            "expired_derivative_ready_rows": expired_derivative_ready,
            "active_derivative_ready_preserved": active_derivative_ready,
            "dead_parent_unknown_write_polling_targets": dead_parent_unknown_writes,
            "other_unknown_writes_preserved": other_unknown_writes,
            "cc603_backfill_prepared": cc603_prepared,
            "reserved_images_readonly": reserved_images,
        }
    finally:
        conn.close()


def _parent_has_blocking_sibling_substack_dispatch_conn(
    conn: sqlite3.Connection, work_item_id: str, *, exclude_message_id: str
) -> bool:
    for row in conn.execute(
        """
        SELECT o.message_id, o.status,
               d.status AS dispatch_status, d.public_object_id, d.public_object_url
        FROM outbox_messages o
        LEFT JOIN platform_dispatches d ON d.message_id = o.message_id
        WHERE o.work_item_id = ?
          AND o.destination = 'substack'
          AND o.message_id <> ?
        """,
        (work_item_id, exclude_message_id),
    ):
        if row["dispatch_status"] is not None and (
            row["dispatch_status"] in {DISPATCH_CONFIRMED, ATTEMPT_STARTED, UNKNOWN_WRITE, NATIVE_NEO_PENDING}
            or row["public_object_id"]
            or row["public_object_url"]
        ):
            return True
        if str(row["status"]) == "READY":
            return True
    return False


def _parent_has_blocking_sibling_substack_dispatch(
    store: ContentOpsDurableStore, work_item_id: str, *, exclude_message_id: str
) -> bool:
    with store.get_read_only_connection() as conn:
        return _parent_has_blocking_sibling_substack_dispatch_conn(
            conn, work_item_id, exclude_message_id=exclude_message_id
        )


def _parent_has_blocking_sibling_dispatch_conn(
    conn: sqlite3.Connection, work_item_id: str, *, exclude_message_id: str
) -> bool:
    """Defensive sibling guard before settling any parent internal:plan-analysis-page link row."""
    for row in conn.execute(
        """
        SELECT o.message_id, o.destination, o.status,
               d.status AS dispatch_status, d.public_object_id, d.public_object_url
        FROM outbox_messages o
        LEFT JOIN platform_dispatches d ON d.message_id = o.message_id
        WHERE o.work_item_id = ?
          AND o.message_id <> ?
          AND o.message_id <> ?
          AND o.destination NOT LIKE 'internal:%'
        """,
        (work_item_id, exclude_message_id, work_item_id),
    ):
        if row["dispatch_status"] is not None and (
            row["dispatch_status"] in {DISPATCH_CONFIRMED, ATTEMPT_STARTED, UNKNOWN_WRITE, NATIVE_NEO_PENDING}
            or row["public_object_id"]
            or row["public_object_url"]
        ):
            return True
        if str(row["status"]) in {"READY", NATIVE_NEO_PENDING}:
            return True
    return False


def _work_item_has_active_child_dispatches_conn(conn: sqlite3.Connection, work_item_id: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM platform_dispatches d
        JOIN outbox_messages o ON o.message_id = d.message_id
        WHERE o.work_item_id = ?
          AND (
              d.status IN ('DISPATCH_CONFIRMED', 'DISPATCH_ATTEMPT_STARTED', 'UNKNOWN_WRITE', 'NATIVE_NEO_TOOL_PENDING')
              OR d.public_object_id IS NOT NULL
              OR d.public_object_url IS NOT NULL
          )
        LIMIT 1
        """,
        (work_item_id,),
    ).fetchone()
    return row is not None


def _work_item_has_active_child_dispatches(store: ContentOpsDurableStore, work_item_id: str) -> bool:
    with store.get_read_only_connection() as conn:
        return _work_item_has_active_child_dispatches_conn(conn, work_item_id)


def _tx_set_outbox_status(conn: sqlite3.Connection, message_id: str, status: str) -> None:
    row = conn.execute(
        "SELECT 1 FROM outbox_messages WHERE message_id=?", (message_id,)
    ).fetchone()
    if row is None:
        raise WorkItemNotFoundError(f"outbox message {message_id} not found")
    conn.execute("UPDATE outbox_messages SET status=? WHERE message_id=?", (status, message_id))


def _tx_set_dispatch_status(conn: sqlite3.Connection, dispatch_id: str, status: str) -> None:
    row = conn.execute(
        "SELECT 1 FROM platform_dispatches WHERE dispatch_id=?", (dispatch_id,)
    ).fetchone()
    if row is None:
        raise WorkItemNotFoundError(f"dispatch {dispatch_id} not found")
    conn.execute("UPDATE platform_dispatches SET status=? WHERE dispatch_id=?", (status, dispatch_id))


def _tx_register_incident(
    conn: sqlite3.Connection,
    *,
    incident_id: str,
    work_item_id: Optional[str],
    severity: str,
    description: str,
    created_at: str,
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO incidents (incident_id, work_item_id, severity, description, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (incident_id, work_item_id, severity, description, created_at),
    )


def _plan_analysis_link_ref_clock(
    conn: sqlite3.Connection,
    parent_row: Optional[Mapping[str, Any]],
    message_row: Mapping[str, Any],
) -> Optional[datetime]:
    parent_created = parent_row.get("created_at") if parent_row is not None else None
    parent_payload = parent_row.get("payload") if parent_row is not None else None
    ref_clock = _parse_utc(parent_created) or _parse_utc(message_row.get("created_at"))
    if parent_payload:
        parent_json = _parse_json_mapping(parent_payload)
        orig_key = parent_json.get("original_key")
        if orig_key:
            orig_row = _get_outbox_row(conn, str(orig_key))
            if orig_row:
                orig_payload = _parse_json_mapping(orig_row.get("payload"))
                if orig_payload.get("at_utc"):
                    ref_clock = _parse_utc(orig_payload["at_utc"]) or ref_clock
    return ref_clock


def apply_preunpause_reconciliation(
    db_path: Path,
    *,
    now: Optional[datetime] = None,
    interlock_now: Optional[datetime] = None,
    allow_copied_state_clock_override: bool = False,
    control_dir: Optional[Path] = None,
    published_images_path: Optional[Path] = None,
    retire_cc603_backfill: bool = False,
    extra_lock_paths: Sequence[Path] = (),
    production_store: Optional[Path] = None,
    check_live_processes: Optional[bool] = None,
    process_scanner: Callable[[], list[dict[str, Any]]] = _default_live_writer_process_scanner,
) -> tuple[int, dict[str, Any]]:
    """Run interlock checks, then apply safe pre-unpause settlements atomically and idempotently.

    Live DB ``--apply`` always enforces real wall-clock UTC for BOTH liveness interlocks and
    staleness/expiry selection (and re-evaluates page/deadline inside ``BEGIN IMMEDIATE``).
    Passing an explicit ``now`` override is refused on the live DB and requires explicit
    ``allow_copied_state_clock_override=True`` on copied SQLite stores.
    """
    expiry_now, clock_refusal, expiry_clock_mode, live_db = _resolve_apply_expiry_clock(
        db_path=db_path,
        now=now,
        allow_copied_state_clock_override=allow_copied_state_clock_override,
        production_store=production_store,
    )
    if clock_refusal is not None or expiry_now is None:
        return (
            EXIT_USAGE_REFUSED,
            {
                "status": "REFUSED_USAGE",
                "mode": "apply",
                "applied": False,
                "reason": clock_refusal or "APPLY_CLOCK_OVERRIDE_REFUSED",
                "live_production_db": live_db,
                "expiry_clock_mode": expiry_clock_mode,
                "mutations": {},
            },
        )

    liveness_now = _resolve_interlock_clock(now=expiry_now, interlock_now=interlock_now)
    interlocks = check_apply_interlocks(
        db_path,
        now=expiry_now,
        interlock_now=liveness_now,
        control_dir=control_dir,
        extra_lock_paths=extra_lock_paths,
        production_store=production_store,
        check_live_processes=check_live_processes,
        process_scanner=process_scanner,
    )
    audit = audit_preunpause_outbox(
        db_path,
        now=expiry_now,
        published_images_path=published_images_path,
        retire_cc603_backfill=retire_cc603_backfill,
    )
    if not interlocks["ok"]:
        return (
            EXIT_INTERLOCK_REFUSED,
            {
                "status": "REFUSED_INTERLOCK",
                "mode": "apply",
                "applied": False,
                "expiry_clock_mode": expiry_clock_mode,
                "expiry_clock_utc": expiry_now.isoformat().replace("+00:00", "Z"),
                "interlocks": interlocks,
                "audit": audit,
                "mutations": {},
            },
        )

    store = ContentOpsDurableStore(db_path, auto_migrate=False)
    mutations: dict[str, list[dict[str, Any]]] = {
        "subgroup_a_retired": [],
        "subgroup_b_verified_absent_retired": [],
        "subgroup_b_held_readback_required": [],
        "subgroup_d_settled": [],
        "expired_derivative_ready_retired": [],
        "dead_parent_unknown_writes_settled": [],
        "cc603_backfill_retired": [],
        "cc603_backfill_skipped_active_child": [],
    }

    conn = store.get_connection()
    tx_expiry_now = expiry_now
    try:
        conn.execute("BEGIN IMMEDIATE")
        tx_wall_now = datetime.now(timezone.utc)
        tx_expiry_now = tx_wall_now if expiry_clock_mode == "WALL_UTC" else expiry_now
        tx_liveness_now = _resolve_interlock_clock(now=tx_expiry_now, interlock_now=interlock_now)
        # Re-verify SQLite lease/heartbeat interlocks inside the exclusive write transaction.
        tx_blockers = _collect_sqlite_liveness_blockers(conn, liveness_now=tx_liveness_now)
        if tx_blockers:
            conn.execute("ROLLBACK")
            refused_interlocks = {
                **interlocks,
                "ok": False,
                "blockers": [*interlocks["blockers"], *tx_blockers],
            }
            return (
                EXIT_INTERLOCK_REFUSED,
                {
                    "status": "REFUSED_INTERLOCK",
                    "mode": "apply",
                    "applied": False,
                    "expiry_clock_mode": expiry_clock_mode,
                    "expiry_clock_utc": expiry_now.isoformat().replace("+00:00", "Z"),
                    "tx_expiry_clock_utc": tx_expiry_now.isoformat().replace("+00:00", "Z"),
                    "interlocks": refused_interlocks,
                    "audit": audit,
                    "mutations": {},
                },
            )

        created_at = tx_wall_now.isoformat()

        # 1. Subgroup A: expired un-dispatched READY Substack plan_analysis_page rows.
        for item in audit["subgroup_a_expired_substack_plan_pages"]:
            mid = item["message_id"]
            wid = item["work_item_id"]
            # Re-verify no dispatch appeared concurrently, row is still READY, AND current page/deadline
            # is still stale against tx_expiry_now (wall UTC on live DB) inside BEGIN IMMEDIATE.
            disp = conn.execute(
                "SELECT dispatch_id FROM platform_dispatches WHERE message_id=?", (mid,)
            ).fetchone()
            cur_outbox = _get_outbox_row(conn, mid)
            if (
                disp is not None
                or cur_outbox is None
                or str(cur_outbox["destination"]) != "substack"
                or str(cur_outbox["status"]) != "READY"
            ):
                continue
            cur_intent = _parse_json_mapping(cur_outbox.get("payload"))
            if not cur_intent.get("plan_analysis_page"):
                continue
            still_stale, tx_stale_reason = substack_plan_page_staleness(
                lambda m: _get_outbox_row(conn, m),
                cur_outbox,
                cur_intent,
                now=tx_expiry_now,
            )
            if not still_stale:
                continue
            _tx_set_outbox_status(conn, mid, PLAN_PAGE_EXPIRED_STALE_NO_WRITE)
            parent_settled = False
            parent_row = _get_outbox_row(conn, wid)
            if (
                parent_row is not None
                and parent_row["destination"] == "internal:plan-analysis-page"
                and not _parent_has_blocking_sibling_substack_dispatch_conn(
                    conn, wid, exclude_message_id=mid
                )
            ):
                _tx_set_outbox_status(conn, wid, SETTLED_POST)
                parent_settled = True
            _tx_register_incident(
                conn,
                incident_id="incident_preunpause_subgroup_a_" + _sha256(mid)[:24],
                work_item_id=wid,
                severity="RECOVERY_AUDIT",
                description=_canonical_json(
                    {
                        "tool": "reconcile_preunpause_outbox_v1",
                        "category": "SUBGROUP_A_EXPIRED_SUBSTACK_PLAN_PAGE",
                        "message_id": mid,
                        "work_item_id": wid,
                        "reason": tx_stale_reason or item["stale_reason"],
                        "new_outbox_status": PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
                        "parent_settled": parent_settled,
                        "public_write_performed": False,
                    }
                ),
                created_at=created_at,
            )
            mutations["subgroup_a_retired"].append(
                {
                    "message_id": mid,
                    "work_item_id": wid,
                    "outbox_status": PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
                    "parent_settled": parent_settled,
                }
            )

        # 2. Subgroup B: readback-first gate (NEVER auto-retire without durable verified absence proof!).
        for item in audit["subgroup_b_substack_readback_gated"]:
            if not item["eligible_for_apply"]:
                mutations["subgroup_b_held_readback_required"].append(
                    {
                        "message_id": item["message_id"],
                        "dispatch_id": item["dispatch_id"],
                        "dispatch_status": item["dispatch_status"],
                        "reason": item["absence_check_reason"],
                    }
                )
                continue
            mid = item["message_id"]
            did = item["dispatch_id"]
            wid = item["work_item_id"]
            # Re-verify current page/deadline staleness AND absence proof inside the write transaction.
            cur_disp = conn.execute(
                "SELECT dispatch_id, status AS dispatch_status, public_object_id, public_object_url "
                "FROM platform_dispatches WHERE dispatch_id=?",
                (did,),
            ).fetchone()
            cur_outbox = _get_outbox_row(conn, mid)
            if (
                cur_disp is None
                or cur_outbox is None
                or str(cur_outbox["destination"]) != "substack"
                or str(cur_outbox["status"]) in SUBSTACK_EXCLUDED_OUTBOX_STATUSES
            ):
                continue
            cur_intent = _parse_json_mapping(cur_outbox.get("payload"))
            if not cur_intent.get("plan_analysis_page"):
                continue
            still_stale, tx_stale_reason = substack_plan_page_staleness(
                lambda m: _get_outbox_row(conn, m),
                cur_outbox,
                cur_intent,
                now=tx_expiry_now,
            )
            if not still_stale:
                continue
            still_absent, recheck_reason = _has_verified_absence_proof(conn, dict(cur_disp), wid)
            if not still_absent:
                mutations["subgroup_b_held_readback_required"].append(
                    {
                        "message_id": mid,
                        "dispatch_id": did,
                        "dispatch_status": str(cur_disp["dispatch_status"]),
                        "reason": recheck_reason,
                    }
                )
                continue
            _tx_set_outbox_status(conn, mid, PLAN_PAGE_EXPIRED_STALE_NO_WRITE)
            _tx_set_dispatch_status(conn, did, PLAN_PAGE_EXPIRED_STALE_NO_WRITE)
            parent_settled = False
            parent_row = _get_outbox_row(conn, wid)
            if (
                parent_row is not None
                and parent_row["destination"] == "internal:plan-analysis-page"
                and not _parent_has_blocking_sibling_substack_dispatch_conn(
                    conn, wid, exclude_message_id=mid
                )
            ):
                _tx_set_outbox_status(conn, wid, SETTLED_POST)
                parent_settled = True
            _tx_register_incident(
                conn,
                incident_id="incident_preunpause_subgroup_b_" + _sha256(did)[:24],
                work_item_id=wid,
                severity="RECOVERY_AUDIT",
                description=_canonical_json(
                    {
                        "tool": "reconcile_preunpause_outbox_v1",
                        "category": "SUBGROUP_B_VERIFIED_ABSENT_SUBSTACK_PLAN_PAGE",
                        "message_id": mid,
                        "dispatch_id": did,
                        "work_item_id": wid,
                        "verified_absence_proof": True,
                        "stale_reason": tx_stale_reason or item["stale_reason"],
                        "new_status": PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
                        "parent_settled": parent_settled,
                        "public_write_performed": False,
                    }
                ),
                created_at=created_at,
            )
            mutations["subgroup_b_verified_absent_retired"].append(
                {
                    "message_id": mid,
                    "dispatch_id": did,
                    "work_item_id": wid,
                    "status": PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
                    "parent_settled": parent_settled,
                }
            )

        # 3. Subgroup D: NATIVE_NEO_TOOL_PENDING under dead parent -> outbox PLAN_POST_SETTLED (preserve dispatch!).
        for item in audit["subgroup_d_dead_parent_native_neo_pending"]:
            mid = item["message_id"]
            wid = item["work_item_id"]
            did = item["dispatch_id"]
            cur_outbox = _get_outbox_row(conn, mid)
            cur_parent = _get_outbox_row(conn, wid)
            cur_disp = (
                conn.execute(
                    "SELECT status, public_object_id, public_object_url FROM platform_dispatches WHERE dispatch_id=?",
                    (did,),
                ).fetchone()
                if did
                else None
            )
            if (
                cur_outbox is None
                or cur_parent is None
                or str(cur_parent["status"]) not in DEAD_PARENT_STATUSES
                or (
                    str(cur_outbox["status"]) != NATIVE_NEO_PENDING
                    and (cur_disp is None or str(cur_disp["status"]) != NATIVE_NEO_PENDING)
                )
                or (cur_disp is not None and (cur_disp["public_object_id"] or cur_disp["public_object_url"]))
            ):
                continue
            _tx_set_outbox_status(conn, mid, SETTLED_COPY)
            _tx_register_incident(
                conn,
                incident_id="incident_preunpause_subgroup_d_" + _sha256(mid)[:24],
                work_item_id=wid,
                severity="RECOVERY_AUDIT",
                description=_canonical_json(
                    {
                        "tool": "reconcile_preunpause_outbox_v1",
                        "category": "SUBGROUP_D_DEAD_PARENT_NATIVE_NEO_PENDING",
                        "message_id": mid,
                        "dispatch_id": did,
                        "destination": item["destination"],
                        "parent_status": str(cur_parent["status"]),
                        "new_outbox_status": SETTLED_COPY,
                        "dispatch_status_preserved": str(cur_disp["status"]) if cur_disp is not None else item["dispatch_status_preserved"],
                        "public_write_performed": False,
                        "automatic_work_closed": True,
                    }
                ),
                created_at=created_at,
            )
            mutations["subgroup_d_settled"].append(
                {
                    "message_id": mid,
                    "dispatch_id": did,
                    "outbox_status": SETTLED_COPY,
                    "dispatch_status_preserved": str(cur_disp["status"]) if cur_disp is not None else item["dispatch_status_preserved"],
                }
            )

        # 4. Expired derivative READY rows -> DERIVATIVE_EXPIRED_STALE_NO_WRITE.
        for item in audit["expired_derivative_ready_rows"]:
            mid = item["message_id"]
            wid = item["work_item_id"]
            disp = conn.execute(
                "SELECT dispatch_id FROM platform_dispatches WHERE message_id=?", (mid,)
            ).fetchone()
            cur_outbox = _get_outbox_row(conn, mid)
            if disp is not None or cur_outbox is None or str(cur_outbox["status"]) != "READY":
                continue
            cur_intent = _parse_json_mapping(cur_outbox.get("payload"))
            cur_parent = _get_outbox_row(conn, wid) if wid else None
            still_stale, tx_stale_reason = _derivative_is_stale_ro(
                conn, cur_outbox, cur_intent, cur_parent, now=tx_expiry_now
            )
            if not still_stale:
                continue
            _tx_set_outbox_status(conn, mid, DERIVATIVE_EXPIRED_STALE_NO_WRITE)
            _tx_register_incident(
                conn,
                incident_id="incident_derivative_stale_" + _sha256(mid)[:24],
                work_item_id=wid or None,
                severity="RECOVERY_AUDIT",
                description="Stale derivative expired with zero public write; prior readback history retained.",
                created_at=created_at,
            )
            mutations["expired_derivative_ready_retired"].append(
                {
                    "message_id": mid,
                    "work_item_id": wid,
                    "destination": item["destination"],
                    "outbox_status": DERIVATIVE_EXPIRED_STALE_NO_WRITE,
                    "reason": tx_stale_reason or item["stale_reason"],
                }
            )

        # 5. Dead-parent / late UNKNOWN_WRITE polling targets (O56/O58/O60/O61) ->
        #    outbox PLAN_POST_SETTLED while preserving platform_dispatches.status == 'UNKNOWN_WRITE'.
        for item in audit["dead_parent_unknown_write_polling_targets"]:
            mid = item["message_id"]
            did = item["dispatch_id"]
            wid = item["work_item_id"]
            cur_disp = conn.execute(
                "SELECT status FROM platform_dispatches WHERE dispatch_id=?", (did,)
            ).fetchone()
            cur_outbox = _get_outbox_row(conn, mid)
            cur_parent = _get_outbox_row(conn, wid)
            if (
                cur_disp is None
                or str(cur_disp["status"]) != UNKNOWN_WRITE
                or cur_outbox is None
                or str(cur_outbox["status"]) == SETTLED_COPY
            ):
                continue
            if item["settle_parent_link"]:
                ref_clock = _plan_analysis_link_ref_clock(conn, cur_parent, cur_outbox)
                if ref_clock is None or (tx_expiry_now - ref_clock).total_seconds() <= LATE_LINK_HOURS * 3600:
                    continue
            elif cur_parent is None or str(cur_parent["status"]) not in DEAD_PARENT_STATUSES:
                continue
            _tx_set_outbox_status(conn, mid, SETTLED_COPY)
            parent_settled = False
            if item["settle_parent_link"]:
                parent_row = cur_parent
                if (
                    parent_row is not None
                    and parent_row["destination"] == "internal:plan-analysis-page"
                    and not _parent_has_blocking_sibling_dispatch_conn(
                        conn, wid, exclude_message_id=mid
                    )
                ):
                    _tx_set_outbox_status(conn, wid, SETTLED_POST)
                    parent_settled = True
            _tx_register_incident(
                conn,
                incident_id="incident_preunpause_unknown_poll_" + _sha256(did)[:24],
                work_item_id=wid,
                severity="RECOVERY_AUDIT",
                description=_canonical_json(
                    {
                        "tool": "reconcile_preunpause_outbox_v1",
                        "category": "DEAD_PARENT_UNKNOWN_WRITE_POLL_TARGET",
                        "message_id": mid,
                        "dispatch_id": did,
                        "platform": item["platform"],
                        "reason": item["reason"],
                        "new_outbox_status": SETTLED_COPY,
                        "dispatch_status_preserved": UNKNOWN_WRITE,
                        "parent_settled": parent_settled,
                        "explicit_readback_still_available": True,
                        "public_write_performed": False,
                        "automatic_work_closed": True,
                    }
                ),
                created_at=created_at,
            )
            mutations["dead_parent_unknown_writes_settled"].append(
                {
                    "message_id": mid,
                    "dispatch_id": did,
                    "platform": item["platform"],
                    "outbox_status": SETTLED_COPY,
                    "dispatch_status_preserved": UNKNOWN_WRITE,
                    "parent_settled": parent_settled,
                }
            )

        # 6. Optional explicit --retire-cc603-backfill policy flag (default: untouched).
        if retire_cc603_backfill:
            for item in audit["cc603_backfill_prepared"]:
                mid = item["message_id"]
                wid = item["work_item_id"]
                cur_outbox = _get_outbox_row(conn, mid)
                if cur_outbox is None or str(cur_outbox["status"]) != "CC603_PREPARED":
                    continue
                if _work_item_has_active_child_dispatches_conn(conn, wid):
                    mutations["cc603_backfill_skipped_active_child"].append(
                        {"message_id": mid, "work_item_id": wid, "reason": "ACTIVE_CHILD_DISPATCH_EXISTS"}
                    )
                    continue
                _tx_set_outbox_status(conn, mid, SETTLED_POST)
                _tx_register_incident(
                    conn,
                    incident_id="incident_preunpause_cc603_" + _sha256(mid)[:24],
                    work_item_id=wid,
                    severity="RECOVERY_AUDIT",
                    description=_canonical_json(
                        {
                            "tool": "reconcile_preunpause_outbox_v1",
                            "category": "CC603_BACKFILL_EXPLICIT_RETIREMENT",
                            "policy_flag": "--retire-cc603-backfill",
                            "message_id": mid,
                            "work_item_id": wid,
                            "previous_status": "CC603_PREPARED",
                            "new_status": SETTLED_POST,
                            "public_write_performed": False,
                        }
                    ),
                    created_at=created_at,
                )
                mutations["cc603_backfill_retired"].append(
                    {"message_id": mid, "work_item_id": wid, "outbox_status": SETTLED_POST}
                )

        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()

    post_audit_now = datetime.now(timezone.utc) if expiry_clock_mode == "WALL_UTC" else expiry_now
    post_audit = audit_preunpause_outbox(
        db_path,
        now=post_audit_now,
        published_images_path=published_images_path,
        retire_cc603_backfill=retire_cc603_backfill,
    )
    return (
        EXIT_OK,
        {
            "status": "APPLIED",
            "mode": "apply",
            "applied": True,
            "expiry_clock_mode": expiry_clock_mode,
            "expiry_clock_utc": expiry_now.isoformat().replace("+00:00", "Z"),
            "tx_expiry_clock_utc": tx_expiry_now.isoformat().replace("+00:00", "Z"),
            "interlocks": interlocks,
            "pre_audit_counts": audit["counts"],
            "post_audit_counts": post_audit["counts"],
            "mutations": mutations,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-unpause ContentOps outbox audit & reconciliation tool (CC-692). "
            "Strictly --dry-run by default (zero DB writes)."
        )
    )
    parser.add_argument(
        "--db",
        "--store",
        dest="db",
        type=Path,
        default=None,
        help="Path to SQLite store (defaults to production store in --dry-run only; required for --apply).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only audit mode (default behavior; performs 0 DB writes).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply safe settlements to the operator-supplied --db after passing all interlock checks.",
    )
    parser.add_argument(
        "--control-dir",
        type=Path,
        default=None,
        help="Optional control directory for restored.json & lock checks (defaults to <db.parent>/control).",
    )
    parser.add_argument(
        "--published-images",
        type=Path,
        default=None,
        help="Optional published_images_v1.jsonl path for read-only RESERVED image reporting.",
    )
    parser.add_argument(
        "--now-utc",
        default=None,
        help=(
            "Optional ISO-8601 UTC timestamp for deterministic --dry-run preview (or copied-state --apply ONLY "
            "when paired with --allow-copied-state-clock-override; NEVER allowed on live production --apply)."
        ),
    )
    parser.add_argument(
        "--allow-copied-state-clock-override",
        action="store_true",
        help=(
            "Explicit copied-state replay opt-in allowing --now-utc during --apply on a non-production SQLite copy "
            "only (always refused when targeting the live production store)."
        ),
    )
    parser.add_argument(
        "--retire-cc603-backfill",
        action="store_true",
        help="Explicit policy flag: also retire CC603_PREPARED backfill rows (default: leave untouched and report).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.apply and args.dry_run:
        print(
            json.dumps(
                {"status": "REFUSED_USAGE", "reason": "CONFLICTING_MODE_FLAGS"},
                indent=2,
            )
        )
        return EXIT_USAGE_REFUSED
    if args.apply and args.db is None:
        print(
            json.dumps(
                {"status": "REFUSED_USAGE", "reason": "APPLY_REQUIRES_EXPLICIT_DB_PATH"},
                indent=2,
            )
        )
        return EXIT_USAGE_REFUSED

    db_path = args.db if args.db is not None else PRODUCTION_STORE
    if not db_path.is_file():
        print(
            json.dumps(
                {"status": "REFUSED_USAGE", "reason": f"DB_NOT_FOUND:{db_path}"},
                indent=2,
            )
        )
        return EXIT_USAGE_REFUSED

    if not args.apply:
        now = _utc_now(args.now_utc)
        interlocks = check_apply_interlocks(
            db_path,
            now=now,
            control_dir=args.control_dir,
            check_live_processes=False,
            read_only_lock_probe=True,
        )
        audit = audit_preunpause_outbox(
            db_path,
            now=now,
            published_images_path=args.published_images,
            retire_cc603_backfill=bool(args.retire_cc603_backfill),
        )
        payload = {
            "status": "DRY_RUN_OK",
            "mode": "dry_run",
            "applied": False,
            "apply_interlocks_preview": interlocks,
            "audit": audit,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK

    override_now = _utc_now(args.now_utc) if args.now_utc else None
    rc, result = apply_preunpause_reconciliation(
        db_path,
        now=override_now,
        allow_copied_state_clock_override=bool(args.allow_copied_state_clock_override),
        control_dir=args.control_dir,
        published_images_path=args.published_images,
        retire_cc603_backfill=bool(args.retire_cc603_backfill),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
