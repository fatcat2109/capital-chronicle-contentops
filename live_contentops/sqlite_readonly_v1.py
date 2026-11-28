"""Zero-write WAL-safe read-only SQLite connector for ContentOps (`WS2-WAL-CORE`).

Eliminates bare ``?mode=ro`` opens on WAL-mode (``0202``) SQLite databases, which
otherwise create or mutate ``-shm`` / ``-wal`` sidecar files on read-only audits,
dry-runs, exports, and paused production stores.

Strictly offline pure Python stdlib (zero network, zero env reads, zero subprocesses):

  1. Pre-connect 100-byte SQLite header inspection (``hdr[18:20]``: ``0101`` rollback
     vs ``0202`` WAL) and sidecar inspection (``-wal``, ``-shm``, ``-journal``).
  2. Fail closed on active hot rollback ``-journal`` (``SQLITE_HOT_JOURNAL_ACTIVE``)
     so readers never serve torn dirty uncommitted rows.
  3. Closed rollback (``0101`` / empty ``0 B``) or clean WAL (``0202`` with
     ``wal_bytes == 0``): connect via RFC-3986 URI-escaped ``?mode=ro&immutable=1``
     with ``PRAGMA query_only=ON`` and ``PRAGMA temp_store=MEMORY`` (``0 B`` copied,
     ``0`` ``-wal``/``-shm`` sidecar mutations).
  4. Active WAL (``0202`` with ``wal_bytes > 0``):
       - When ``db_bytes <= max_snapshot_bytes``: copy ``(db, -wal)`` into a private
         ``TemporaryDirectory`` with ``O(1)`` pre == post header/WAL verification
         (retrying on concurrent writer races, failing closed on persistent race),
         open the isolated snapshot with ``PRAGMA query_only=ON``, and guarantee
         ``conn.close()`` executes BEFORE ``TemporaryDirectory.cleanup()`` to prevent
         Windows ``WinError 32`` lock failures.
       - When ``db_bytes > max_snapshot_bytes``: fail closed by default
         (``SQLITE_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED``) unless the caller explicitly
         opts into ``allow_oversized_live_wal=True`` (emits explicit status + warning;
         never silent bare ``?mode=ro`` mutating ``-shm``).
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
from typing import Any, Iterator, Literal
import warnings
import weakref

SQLITE_MAGIC = b"SQLite format 3\x00"
DEFAULT_MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024  # 256 MiB
DEFAULT_SNAPSHOT_RETRIES = 3
DEFAULT_RETRY_SLEEP_SECONDS = 0.05

MODE_IMMUTABLE_ROLLBACK = "RO_IMMUTABLE_ROLLBACK"
MODE_IMMUTABLE_ZERO_WAL = "RO_IMMUTABLE_ZERO_WAL"
MODE_TEMP_SNAPSHOT_WAL = "RO_TEMP_SNAPSHOT_WAL"
MODE_LIVE_WAL_EXPLICIT = "RO_LIVE_WAL_EXPLICIT"

REASON_DATABASE_MISSING = "SQLITE_DATABASE_MISSING"
REASON_HEADER_INVALID = "SQLITE_HEADER_INVALID"
REASON_HOT_JOURNAL_ACTIVE = "SQLITE_HOT_JOURNAL_ACTIVE"
REASON_SNAPSHOT_CONCURRENT_MUTATION = "SQLITE_SNAPSHOT_CONCURRENT_MUTATION"
REASON_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED = "SQLITE_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED"


class SqliteReadOnlyError(sqlite3.OperationalError):
    """Fail-closed error raised when a SQLite file cannot be read safely without writes."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = str(reason_code)
        self.detail = str(detail)
        message = f"{self.reason_code}: {self.detail}" if self.detail else self.reason_code
        super().__init__(message)


@dataclass(frozen=True)
class SqliteStorageInfo:
    path: Path
    db_bytes: int
    format_write_version: int
    format_read_version: int
    journal_mode: str
    wal_exists: bool
    wal_bytes: int
    shm_exists: bool
    shm_bytes: int
    journal_exists: bool
    journal_bytes: int
    journal_is_hot: bool


def _cleanup_tempdir_best_effort(td: tempfile.TemporaryDirectory[str]) -> None:
    try:
        td.cleanup()
    except OSError:
        pass


class ManagedReadOnlyConnection(sqlite3.Connection):
    """``sqlite3.Connection`` subclass enforcing close-before-cleanup for private snapshots."""

    readonly_mode: str = "UNINITIALIZED"
    readonly_warning: str | None = None
    source_path: str = ""
    _readonly_tempdir: tempfile.TemporaryDirectory[str] | None = None
    _readonly_closed: bool = False
    _readonly_finalizer: weakref.finalize | None = None

    def _attach_readonly_metadata(
        self,
        *,
        mode: str,
        source_path: Path,
        tempdir: tempfile.TemporaryDirectory[str] | None = None,
        warning_code: str | None = None,
    ) -> None:
        self.readonly_mode = mode
        self.readonly_warning = warning_code
        self.source_path = str(source_path)
        self._readonly_tempdir = tempdir
        self._readonly_closed = False
        if tempdir is not None:
            self._readonly_finalizer = weakref.finalize(
                self, _cleanup_tempdir_best_effort, tempdir
            )
        else:
            self._readonly_finalizer = None

    def close(self) -> None:
        if self._readonly_closed:
            return
        self._readonly_closed = True
        try:
            super().close()
        finally:
            finalizer = self._readonly_finalizer
            self._readonly_finalizer = None
            if finalizer is not None:
                finalizer.detach()
            td = self._readonly_tempdir
            self._readonly_tempdir = None
            if td is not None:
                td.cleanup()

    def __enter__(self) -> "ManagedReadOnlyConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
        try:
            if self.in_transaction:
                self.rollback()
        except sqlite3.Error:
            pass
        finally:
            self.close()
        return False


def sqlite_file_uri(path: Path | str, *, immutable: bool = False) -> str:
    """Build an RFC-3986 percent-encoded SQLite ``file:`` URI (escapes spaces, ``#``, ``%``, ``?``)."""
    resolved = Path(path).resolve(strict=False)
    base_uri = resolved.as_uri()
    query = "mode=ro&immutable=1" if immutable else "mode=ro"
    return f"{base_uri}?{query}"


def _sidecar_path(db_path: Path, suffix: str) -> Path:
    return db_path.with_name(db_path.name + suffix)


def _is_hot_rollback_journal(journal_path: Path) -> tuple[bool, int, bool]:
    if not journal_path.is_file():
        return False, 0, False
    size = journal_path.stat().st_size
    if size <= 0:
        return True, 0, False
    with journal_path.open("rb") as fh:
        head = fh.read(min(28, size))
    # Zeroed 28-byte header is SQLite PERSIST mode's committed/inactive journal;
    # any non-zero bytes in a non-empty -journal indicate an active/hot rollback journal.
    is_zeroed_persist = size >= 28 and len(head) == 28 and head == (b"\x00" * 28)
    return True, size, not is_zeroed_persist


def inspect_sqlite_storage(path: Path | str) -> SqliteStorageInfo:
    """Inspect a SQLite file's 100-byte header and sidecars without opening SQLite."""
    resolved = Path(path).resolve(strict=False)
    if not resolved.is_file():
        raise SqliteReadOnlyError(REASON_DATABASE_MISSING, str(resolved))

    db_bytes = resolved.stat().st_size
    if db_bytes == 0:
        write_ver, read_ver, mode = 1, 1, "EMPTY"
    else:
        with resolved.open("rb") as fh:
            header = fh.read(100)
        if len(header) < 100 or header[:16] != SQLITE_MAGIC:
            raise SqliteReadOnlyError(
                REASON_HEADER_INVALID,
                f"{resolved} (size={db_bytes}, magic_ok={header[:16] == SQLITE_MAGIC})",
            )
        write_ver = header[18]
        read_ver = header[19]
        if (write_ver, read_ver) == (1, 1):
            mode = "ROLLBACK"
        elif (write_ver, read_ver) == (2, 2):
            mode = "WAL"
        else:
            raise SqliteReadOnlyError(
                REASON_HEADER_INVALID,
                f"{resolved} (unsupported format versions {write_ver:02x}{read_ver:02x})",
            )

    wal_path = _sidecar_path(resolved, "-wal")
    shm_path = _sidecar_path(resolved, "-shm")
    journal_path = _sidecar_path(resolved, "-journal")

    wal_exists = wal_path.is_file()
    wal_bytes = wal_path.stat().st_size if wal_exists else 0
    shm_exists = shm_path.is_file()
    shm_bytes = shm_path.stat().st_size if shm_exists else 0
    journal_exists, journal_bytes, journal_is_hot = _is_hot_rollback_journal(journal_path)

    return SqliteStorageInfo(
        path=resolved,
        db_bytes=db_bytes,
        format_write_version=write_ver,
        format_read_version=read_ver,
        journal_mode=mode,
        wal_exists=wal_exists,
        wal_bytes=wal_bytes,
        shm_exists=shm_exists,
        shm_bytes=shm_bytes,
        journal_exists=journal_exists,
        journal_bytes=journal_bytes,
        journal_is_hot=journal_is_hot,
    )


def _capture_o1_signature(db_path: Path, wal_path: Path) -> tuple[Any, ...]:
    """O(1) pre/post consistency fingerprint of DB header + WAL header/tail."""
    db_stat = db_path.stat()
    with db_path.open("rb") as fh:
        db_hdr = fh.read(100)
    if wal_path.is_file():
        wal_stat = wal_path.stat()
        with wal_path.open("rb") as wfh:
            wal_hdr = wfh.read(32)
            if wal_stat.st_size > 32:
                wfh.seek(wal_stat.st_size - 32)
                wal_tail = wfh.read(32)
            else:
                wal_tail = b""
        wal_sig: Any = (wal_stat.st_size, wal_stat.st_mtime_ns, wal_hdr, wal_tail)
    else:
        wal_sig = None
    return (db_stat.st_size, db_stat.st_mtime_ns, db_hdr, wal_sig)


def _configure_readonly_pragmas(
    conn: sqlite3.Connection,
    *,
    row_factory: Any,
    foreign_keys: bool,
    busy_timeout_ms: int | None,
) -> None:
    if row_factory is not None:
        conn.row_factory = row_factory
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA temp_store=MEMORY")
    if foreign_keys:
        conn.execute("PRAGMA foreign_keys=ON")
    if busy_timeout_ms is not None:
        conn.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")


def _open_temp_wal_snapshot(
    resolved: Path,
    *,
    timeout: float,
    row_factory: Any,
    isolation_level: str | None,
    cached_statements: int,
    foreign_keys: bool,
    busy_timeout_ms: int | None,
    snapshot_retries: int,
) -> ManagedReadOnlyConnection:
    wal_path = _sidecar_path(resolved, "-wal")
    journal_path = _sidecar_path(resolved, "-journal")
    attempts = max(1, int(snapshot_retries))

    for attempt in range(attempts):
        pre_sig = _capture_o1_signature(resolved, wal_path)
        td = tempfile.TemporaryDirectory(prefix="cc_sqlite_ro_snap_")
        try:
            snap_db = Path(td.name) / resolved.name
            shutil.copyfile(resolved, snap_db)
            if wal_path.is_file() and wal_path.stat().st_size > 0:
                shutil.copyfile(wal_path, _sidecar_path(snap_db, "-wal"))
            _, _, hot_after = _is_hot_rollback_journal(journal_path)
            if hot_after:
                td.cleanup()
                raise SqliteReadOnlyError(REASON_HOT_JOURNAL_ACTIVE, str(journal_path))
            post_sig = _capture_o1_signature(resolved, wal_path)
            if pre_sig != post_sig:
                td.cleanup()
                if attempt + 1 < attempts:
                    time.sleep(DEFAULT_RETRY_SLEEP_SECONDS)
                    continue
                raise SqliteReadOnlyError(
                    REASON_SNAPSHOT_CONCURRENT_MUTATION,
                    f"{resolved} changed during all {attempts} snapshot attempts",
                )
            # Open the isolated temp snapshot RW so SQLite recovers the copied -wal into
            # a private -shm inside TemporaryDirectory, then immediately enforce query_only=ON.
            conn = sqlite3.connect(
                str(snap_db),
                timeout=max(0.0, float(timeout)),
                isolation_level=isolation_level,
                cached_statements=cached_statements,
                factory=ManagedReadOnlyConnection,
            )
            try:
                _configure_readonly_pragmas(
                    conn,
                    row_factory=row_factory,
                    foreign_keys=foreign_keys,
                    busy_timeout_ms=busy_timeout_ms,
                )
                conn._attach_readonly_metadata(
                    mode=MODE_TEMP_SNAPSHOT_WAL,
                    source_path=resolved,
                    tempdir=td,
                )
            except Exception:
                try:
                    conn.close()
                finally:
                    td.cleanup()
                raise
            return conn
        except SqliteReadOnlyError:
            raise
        except Exception:
            _cleanup_tempdir_best_effort(td)
            raise

    raise SqliteReadOnlyError(REASON_SNAPSHOT_CONCURRENT_MUTATION, str(resolved))


def connect_readonly_sqlite(
    path: Path | str,
    *,
    timeout: float = 5.0,
    row_factory: Any = sqlite3.Row,
    isolation_level: str | None = None,
    cached_statements: int = 0,
    foreign_keys: bool = False,
    busy_timeout_ms: int | None = None,
    max_snapshot_bytes: int = DEFAULT_MAX_SNAPSHOT_BYTES,
    allow_oversized_live_wal: bool = False,
    snapshot_retries: int = DEFAULT_SNAPSHOT_RETRIES,
) -> ManagedReadOnlyConnection:
    """Open a SQLite database strictly read-only without mutating live WAL/SHM sidecars."""
    info = inspect_sqlite_storage(path)
    resolved = info.path

    if info.journal_is_hot:
        raise SqliteReadOnlyError(
            REASON_HOT_JOURNAL_ACTIVE,
            f"{_sidecar_path(resolved, '-journal')} ({info.journal_bytes} bytes)",
        )

    # Closed rollback (0101 / EMPTY) or clean WAL (0202 with wal_bytes == 0):
    # open via immutable=1 for zero disk copy and zero -wal/-shm sidecar creation.
    if info.journal_mode in {"ROLLBACK", "EMPTY"} or info.wal_bytes == 0:
        wal_path = _sidecar_path(resolved, "-wal")
        pre_sig = _capture_o1_signature(resolved, wal_path)
        uri = sqlite_file_uri(resolved, immutable=True)
        conn = sqlite3.connect(
            uri,
            uri=True,
            timeout=max(0.0, float(timeout)),
            isolation_level=isolation_level,
            cached_statements=cached_statements,
            factory=ManagedReadOnlyConnection,
        )
        try:
            _configure_readonly_pragmas(
                conn,
                row_factory=row_factory,
                foreign_keys=foreign_keys,
                busy_timeout_ms=busy_timeout_ms,
            )
            post_sig = _capture_o1_signature(resolved, wal_path)
        except Exception:
            conn.close()
            raise
        if post_sig == pre_sig:
            mode = (
                MODE_IMMUTABLE_ZERO_WAL
                if info.journal_mode == "WAL"
                else MODE_IMMUTABLE_ROLLBACK
            )
            conn._attach_readonly_metadata(mode=mode, source_path=resolved)
            return conn
        # A concurrent writer raced and populated the WAL while opening; close and re-evaluate.
        conn.close()
        info = inspect_sqlite_storage(resolved)
        if info.journal_is_hot:
            raise SqliteReadOnlyError(
                REASON_HOT_JOURNAL_ACTIVE,
                f"{_sidecar_path(resolved, '-journal')} ({info.journal_bytes} bytes)",
            )

    # Active WAL (wal_bytes > 0): prefer isolated temp-copy snapshot within size cap.
    if info.db_bytes <= max(0, int(max_snapshot_bytes)):
        return _open_temp_wal_snapshot(
            resolved,
            timeout=timeout,
            row_factory=row_factory,
            isolation_level=isolation_level,
            cached_statements=cached_statements,
            foreign_keys=foreign_keys,
            busy_timeout_ms=busy_timeout_ms,
            snapshot_retries=snapshot_retries,
        )

    # Oversized active WAL (> max_snapshot_bytes): fail closed unless explicitly opted in.
    if not allow_oversized_live_wal:
        raise SqliteReadOnlyError(
            REASON_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED,
            f"{resolved} ({info.db_bytes} B > max_snapshot_bytes={max_snapshot_bytes}, "
            f"wal={info.wal_bytes} B); pass allow_oversized_live_wal=True or raise max_snapshot_bytes",
        )

    warning_code = "LIVE_ACTIVE_WAL_SHARED_MEMORY_READ"
    warnings.warn(
        f"Opening oversized active WAL database in explicit live ?mode=ro fallback "
        f"({resolved}, db={info.db_bytes} B, wal={info.wal_bytes} B)",
        RuntimeWarning,
        stacklevel=2,
    )
    effective_busy_ms = busy_timeout_ms if busy_timeout_ms is not None else max(1000, int(float(timeout) * 1000))
    uri = sqlite_file_uri(resolved, immutable=False)
    conn = sqlite3.connect(
        uri,
        uri=True,
        timeout=max(0.0, float(timeout)),
        isolation_level=isolation_level,
        cached_statements=cached_statements,
        factory=ManagedReadOnlyConnection,
    )
    try:
        _configure_readonly_pragmas(
            conn,
            row_factory=row_factory,
            foreign_keys=foreign_keys,
            busy_timeout_ms=effective_busy_ms,
        )
        conn._attach_readonly_metadata(
            mode=MODE_LIVE_WAL_EXPLICIT,
            source_path=resolved,
            warning_code=warning_code,
        )
    except Exception:
        conn.close()
        raise
    return conn


@contextmanager
def open_readonly_sqlite(
    path: Path | str,
    *,
    timeout: float = 5.0,
    row_factory: Any = sqlite3.Row,
    isolation_level: str | None = None,
    cached_statements: int = 0,
    foreign_keys: bool = False,
    busy_timeout_ms: int | None = None,
    max_snapshot_bytes: int = DEFAULT_MAX_SNAPSHOT_BYTES,
    allow_oversized_live_wal: bool = False,
    snapshot_retries: int = DEFAULT_SNAPSHOT_RETRIES,
) -> Iterator[ManagedReadOnlyConnection]:
    """Context manager guaranteeing ``conn.close()`` runs BEFORE temp snapshot cleanup."""
    conn = connect_readonly_sqlite(
        path,
        timeout=timeout,
        row_factory=row_factory,
        isolation_level=isolation_level,
        cached_statements=cached_statements,
        foreign_keys=foreign_keys,
        busy_timeout_ms=busy_timeout_ms,
        max_snapshot_bytes=max_snapshot_bytes,
        allow_oversized_live_wal=allow_oversized_live_wal,
        snapshot_retries=snapshot_retries,
    )
    try:
        yield conn
    finally:
        conn.close()
