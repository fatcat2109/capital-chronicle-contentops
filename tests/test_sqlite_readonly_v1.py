r"""Hermetic tests for zero-write WAL-safe read-only SQLite access (`WS2-WAL-CORE`).

Strictly offline (`tmp_path` only; zero live `A:\` opens, zero live writes,
zero network/subprocess/browser calls).
"""
from __future__ import annotations

import ast
from contextlib import closing
from datetime import datetime, timezone
import gc
from hashlib import sha256
from pathlib import Path
import sqlite3
import warnings

import pytest

from live_contentops import call_followups_v1 as followups
from live_contentops import manual_desk_v1 as manual_desk
from live_contentops import native_desktop_workspace_v1 as workspace
from live_contentops import sqlite_readonly_v1 as sro
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from scripts import run_daily_digest_1900 as digest_1900

REPO_ROOT = Path(__file__).resolve().parents[1]

WIRED_MODULES_18 = (
    "live_contentops/call_followups_v1.py",
    "live_contentops/durable_operational_store_v1.py",
    "live_contentops/codex_desktop_newsroom_operator_v1.py",
    "live_contentops/day_readback_v1.py",
    "live_contentops/manual_desk_v1.py",
    "live_contentops/native_desktop_workspace_v1.py",
    "live_contentops/retained_news_read_v1.py",
    "live_contentops/substack_draft_inventory_v1.py",
    "scripts/run_daily_digest_1900.py",
    "scripts/audit_publication_day_cc401.py",
    "scripts/export_contentops_weekly_coverage.py",
    "scripts/export_contentops_weekly_engagement.py",
    "scripts/prove_v1_final_product_four_window_closed_loop_v1.py",
    "scripts/prove_v1_four_window_bounded_correction_v1.py",
    "scripts/replay_cc041_native_window.py",
    "scripts/seed_published_images.py",
    "scripts/verify_contentops_editorial_desk_v1.py",
    "scripts/verify_contentops_story_update_v1.py",
)


def _dir_snapshot(directory: Path) -> dict[str, tuple[int, int, str]]:
    snap: dict[str, tuple[int, int, str]] = {}
    for entry in sorted(directory.iterdir()):
        if entry.is_file():
            st = entry.stat()
            snap[entry.name] = (st.st_size, st.st_mtime_ns, sha256(entry.read_bytes()).hexdigest())
    return snap


def _create_clean_wal_db(db_path: Path, rows: list[tuple[int, str]]) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")
        conn.executemany("INSERT INTO items (id, label) VALUES (?, ?)", rows)
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.with_name(db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()
    return db_path


def _create_active_wal_db(db_path: Path) -> tuple[Path, sqlite3.Connection]:
    """Create a WAL DB with an open writer holding committed uncheckpointed rows in -wal."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    writer = sqlite3.connect(str(db_path))
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")
    writer.execute("INSERT INTO items (id, label) VALUES (1, 'checkpointed_base')")
    writer.commit()
    writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    writer.execute("INSERT INTO items (id, label) VALUES (2, 'live_uncheckpointed_wal_row')")
    writer.commit()
    wal = db_path.with_name(db_path.name + "-wal")
    assert wal.is_file() and wal.stat().st_size > 0
    return db_path, writer


def test_clean_wal_zero_sidecar_and_uri_special_chars(tmp_path: Path):
    """Clean WAL (0202, wal=0) in a path with spaces, #, %, &, + creates 0 sidecars and is byte-identical."""
    special_dir = tmp_path / "dir #1 %25 &+test"
    db_path = _create_clean_wal_db(special_dir / "store #1 %20.sqlite3", [(1, "alpha"), (2, "beta")])

    info = sro.inspect_sqlite_storage(db_path)
    assert info.journal_mode == "WAL"
    assert (info.format_write_version, info.format_read_version) == (2, 2)
    assert info.wal_bytes == 0
    assert info.shm_exists is False
    assert info.journal_is_hot is False

    before = _dir_snapshot(special_dir)
    assert list(before) == ["store #1 %20.sqlite3"]

    with sro.open_readonly_sqlite(db_path) as conn:
        assert conn.readonly_mode == sro.MODE_IMMUTABLE_ZERO_WAL
        assert conn.readonly_warning is None
        conn.execute("BEGIN")
        rows = [(r["id"], r["label"]) for r in conn.execute("SELECT id, label FROM items ORDER BY id")]
        assert rows == [(1, "alpha"), (2, "beta")]
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO items (id, label) VALUES (3, 'forbidden')")
        conn.execute("ROLLBACK")
        during = _dir_snapshot(special_dir)
        assert during == before

        backup_path = tmp_path / "clean_backup.sqlite3"
        with closing(sqlite3.connect(str(backup_path))) as dst:
            conn.backup(dst)
            assert dst.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2

    after = _dir_snapshot(special_dir)
    assert after == before


def test_closed_rollback_0101_and_empty_db_use_immutable_zero_write(tmp_path: Path):
    rb_dir = tmp_path / "rollback #1"
    rb_dir.mkdir()
    rb_db = rb_dir / "observations.sqlite3"
    conn = sqlite3.connect(str(rb_db))
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("CREATE TABLE obs (k TEXT PRIMARY KEY, v REAL)")
    conn.execute("INSERT INTO obs VALUES ('DGS10', 4.25)")
    conn.commit()
    conn.close()

    info = sro.inspect_sqlite_storage(rb_db)
    assert info.journal_mode == "ROLLBACK"
    assert (info.format_write_version, info.format_read_version) == (1, 1)

    before = _dir_snapshot(rb_dir)
    with sro.open_readonly_sqlite(rb_db) as ro:
        assert ro.readonly_mode == sro.MODE_IMMUTABLE_ROLLBACK
        assert ro.execute("SELECT v FROM obs WHERE k='DGS10'").fetchone()["v"] == pytest.approx(4.25)
        with pytest.raises(sqlite3.OperationalError):
            ro.execute("DELETE FROM obs")
    assert _dir_snapshot(rb_dir) == before

    # 0-byte empty file stays safe and zero-write
    empty_db = tmp_path / "empty.sqlite3"
    empty_db.write_bytes(b"")
    assert sro.inspect_sqlite_storage(empty_db).journal_mode == "EMPTY"
    with sro.open_readonly_sqlite(empty_db) as ro_empty:
        assert ro_empty.readonly_mode == sro.MODE_IMMUTABLE_ROLLBACK
        assert ro_empty.execute("SELECT name FROM sqlite_master").fetchall() == []


def test_active_wal_temp_snapshot_reads_live_wal_with_zero_source_mutation_and_clean_teardown(tmp_path: Path):
    """Active WAL (0202, wal > 0) mutates 0 bytes in source DB/-wal/-shm, sees live rows, and leaks 0 temp dirs."""
    active_dir = tmp_path / "active #2 %25"
    db_path, writer = _create_active_wal_db(active_dir / "live_wal.sqlite3")
    try:
        info = sro.inspect_sqlite_storage(db_path)
        assert info.journal_mode == "WAL"
        assert info.wal_bytes > 0

        before = _dir_snapshot(active_dir)
        snap_dir_path: Path | None = None

        with sro.open_readonly_sqlite(db_path) as conn:
            assert conn.readonly_mode == sro.MODE_TEMP_SNAPSHOT_WAL
            assert conn._readonly_tempdir is not None
            snap_dir_path = Path(conn._readonly_tempdir.name)
            assert snap_dir_path.is_dir()

            conn.execute("BEGIN")
            rows = [(r["id"], r["label"]) for r in conn.execute("SELECT id, label FROM items ORDER BY id")]
            assert rows == [(1, "checkpointed_base"), (2, "live_uncheckpointed_wal_row")]
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("INSERT INTO items (id, label) VALUES (3, 'must_fail')")
            conn.execute("ROLLBACK")

            backup_path = tmp_path / "active_backup.sqlite3"
            with closing(sqlite3.connect(str(backup_path))) as dst:
                conn.backup(dst)
                assert dst.execute("SELECT id, label FROM items ORDER BY id").fetchall() == [
                    (1, "checkpointed_base"),
                    (2, "live_uncheckpointed_wal_row"),
                ]

        # con.close() executed BEFORE TemporaryDirectory.cleanup() -> 0 WinError 32, 0 leaked temp dirs!
        assert snap_dir_path is not None and not snap_dir_path.exists()
        assert _dir_snapshot(active_dir) == before

        # Direct connect_readonly_sqlite() + explicit .close() also cleans temp dir deterministically.
        direct_conn = sro.connect_readonly_sqlite(db_path)
        assert direct_conn._readonly_tempdir is not None
        direct_snap_dir = Path(direct_conn._readonly_tempdir.name)
        assert direct_snap_dir.is_dir()
        assert direct_conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2
        direct_conn.close()
        direct_conn.close()  # idempotent
        assert not direct_snap_dir.exists()
        assert _dir_snapshot(active_dir) == before
    finally:
        writer.close()


def test_active_wal_o1_pre_post_race_retry_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """O(1) pre==post verification retries transient writer races and fails closed on persistent races."""
    db_path, writer = _create_active_wal_db(tmp_path / "race" / "race.sqlite3")
    try:
        real_sig = sro._capture_o1_signature
        calls = {"n": 0}

        def _transient_race(db: Path, wal: Path):
            calls["n"] += 1
            sig = real_sig(db, wal)
            if calls["n"] == 2:
                return (*sig[:-1], ("mutated_during_attempt_1",))
            return sig

        monkeypatch.setattr(sro, "_capture_o1_signature", _transient_race)
        with sro.open_readonly_sqlite(db_path, snapshot_retries=3) as conn:
            assert conn.readonly_mode == sro.MODE_TEMP_SNAPSHOT_WAL
            assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2
            snap_dir = Path(conn._readonly_tempdir.name)
        assert not snap_dir.exists()

        # Persistent concurrent mutation across all retries -> fail closed!
        counter = {"n": 0}

        def _always_mutating(db: Path, wal: Path):
            counter["n"] += 1
            return (counter["n"],)

        monkeypatch.setattr(sro, "_capture_o1_signature", _always_mutating)
        with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
            with sro.open_readonly_sqlite(db_path, snapshot_retries=2):
                pass
        assert exc_info.value.reason_code == sro.REASON_SNAPSHOT_CONCURRENT_MUTATION
    finally:
        writer.close()


def test_hot_rollback_journal_fails_closed_while_cold_journals_pass(tmp_path: Path):
    """Active hot rollback -journal fails closed (SQLITE_HOT_JOURNAL_ACTIVE); never serves torn dirty rows."""
    db_path = tmp_path / "hot.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()

    journal = db_path.with_name(db_path.name + "-journal")
    # Real SQLite rollback journal magic bytes (0xd9d505f920a163d7)
    journal.write_bytes(b"\xd9\xd5\x05\xf9\x20\xa1\x63\xd7" + b"\x01" * 512)

    info = sro.inspect_sqlite_storage(db_path)
    assert info.journal_exists is True
    assert info.journal_is_hot is True

    with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
        with sro.open_readonly_sqlite(db_path):
            pass
    assert exc_info.value.reason_code == sro.REASON_HOT_JOURNAL_ACTIVE
    assert isinstance(exc_info.value, sqlite3.OperationalError)

    # Short non-zero dirty journal also fails closed
    journal.write_bytes(b"dirty")
    with pytest.raises(sro.SqliteReadOnlyError, match=sro.REASON_HOT_JOURNAL_ACTIVE):
        sro.connect_readonly_sqlite(db_path)

    # Committed zeroed PERSIST 28-byte header is inactive (not hot)
    journal.write_bytes(b"\x00" * 28)
    assert sro.inspect_sqlite_storage(db_path).journal_is_hot is False
    with sro.open_readonly_sqlite(db_path) as ro:
        assert ro.execute("SELECT x FROM t").fetchone()["x"] == 42

    # 0-byte TRUNCATE journal is also inactive (not hot)
    journal.write_bytes(b"")
    assert sro.inspect_sqlite_storage(db_path).journal_is_hot is False
    with sro.open_readonly_sqlite(db_path) as ro2:
        assert ro2.execute("SELECT x FROM t").fetchone()["x"] == 42


def test_oversized_active_wal_fails_closed_by_default_and_warns_on_explicit_opt_in(tmp_path: Path):
    db_path, writer = _create_active_wal_db(tmp_path / "oversized" / "big.sqlite3")
    try:
        # Default allow_oversized_live_wal=False fails closed when db_bytes > max_snapshot_bytes
        with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
            with sro.open_readonly_sqlite(db_path, max_snapshot_bytes=1):
                pass
        assert exc_info.value.reason_code == sro.REASON_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED

        # Explicit opt-in warns, tags mode + warning, sees live WAL rows, and still enforces query_only=ON
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with sro.open_readonly_sqlite(
                db_path, max_snapshot_bytes=1, allow_oversized_live_wal=True
            ) as conn:
                assert conn.readonly_mode == sro.MODE_LIVE_WAL_EXPLICIT
                assert conn.readonly_warning == "LIVE_ACTIVE_WAL_SHARED_MEMORY_READ"
                assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2
                with pytest.raises(sqlite3.OperationalError):
                    conn.execute("INSERT INTO items (id, label) VALUES (99, 'blocked')")
        assert any(issubclass(w.category, RuntimeWarning) for w in caught)
    finally:
        writer.close()


def test_missing_and_corrupt_sqlite_files_fail_closed(tmp_path: Path):
    with pytest.raises(sro.SqliteReadOnlyError) as missing_exc:
        sro.connect_readonly_sqlite(tmp_path / "absent.sqlite3")
    assert missing_exc.value.reason_code == sro.REASON_DATABASE_MISSING
    assert isinstance(missing_exc.value, sqlite3.OperationalError)

    bad_magic = tmp_path / "not_sqlite.sqlite3"
    bad_magic.write_bytes(b"NOT A SQLITE DATABASE" * 10)
    with pytest.raises(sro.SqliteReadOnlyError) as magic_exc:
        sro.connect_readonly_sqlite(bad_magic)
    assert magic_exc.value.reason_code == sro.REASON_HEADER_INVALID

    bad_ver = tmp_path / "bad_ver.sqlite3"
    hdr = bytearray(100)
    hdr[:16] = sro.SQLITE_MAGIC
    hdr[18] = 9
    hdr[19] = 9
    bad_ver.write_bytes(bytes(hdr))
    with pytest.raises(sro.SqliteReadOnlyError) as ver_exc:
        sro.connect_readonly_sqlite(bad_ver)
    assert ver_exc.value.reason_code == sro.REASON_HEADER_INVALID


def test_wired_hubs_zero_sidecar_and_active_wal_integration(tmp_path: Path):
    """End-to-end zero-write proof across DurableStore, manual_desk, workspace_snapshot, digest _ro, and call_followups."""
    # 1. DurableOperationalStore clean WAL -> 0 sidecars created across all 4 wired ContentOps store readers!
    store_dir = tmp_path / "store #1"
    store_dir.mkdir()
    db_path = store_dir / "contentops_daily_app_v1.sqlite3"
    init_store = ContentOpsDurableStore(db_path)
    del init_store
    gc.collect()
    with closing(sqlite3.connect(str(db_path))) as w:
        w.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    for suffix in ("-wal", "-shm"):
        p = db_path.with_name(db_path.name + suffix)
        if p.exists():
            p.unlink()
    store = ContentOpsDurableStore(db_path, auto_migrate=False)

    before = _dir_snapshot(store_dir)
    assert list(before) == ["contentops_daily_app_v1.sqlite3"]

    # ContentOpsDurableStore.get_read_only_connection()
    with store.get_read_only_connection() as ro:
        assert ro.readonly_mode == sro.MODE_IMMUTABLE_ZERO_WAL
        assert ro.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0
    assert _dir_snapshot(store_dir) == before

    # manual_desk_v1.open_store_read_only()
    m_conn = manual_desk.open_store_read_only(db_path)
    try:
        assert m_conn.readonly_mode == sro.MODE_IMMUTABLE_ZERO_WAL
        assert m_conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0
    finally:
        m_conn.close()
    assert _dir_snapshot(store_dir) == before

    # native_desktop_workspace_v1.workspace_snapshot() (requires tuple row_factory=None!)
    snap = workspace.workspace_snapshot(db_path)
    assert isinstance(snap, dict) and "outbox_messages" in snap
    assert _dir_snapshot(store_dir) == before

    # scripts/run_daily_digest_1900.py:_ro() + backup() (dry_run pattern -> 0 sidecars!)
    backup_target = tmp_path / "digest_dry_run_copy.sqlite3"
    with closing(digest_1900._ro(db_path)) as src, closing(sqlite3.connect(str(backup_target))) as dst:
        assert src.readonly_mode == sro.MODE_IMMUTABLE_ZERO_WAL
        src.backup(dst)
    assert _dir_snapshot(store_dir) == before

    # 2. call_followups_v1.read_bars() on temp bars.sqlite3 (both clean WAL and active WAL!)
    bars_dir = tmp_path / "bars_store"
    bars_dir.mkdir()
    bars_db = bars_dir / "bars.sqlite3"
    t0 = int(datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc).timestamp())
    bw = sqlite3.connect(str(bars_db))
    bw.execute("PRAGMA journal_mode=WAL")
    bw.execute("PRAGMA wal_autocheckpoint=0")
    bw.execute(
        "CREATE TABLE bars (symbol TEXT, series_id TEXT, open_epoch INTEGER, "
        "open REAL, high REAL, low REAL, close REAL, source_sha256 TEXT, "
        "known_epoch INTEGER, price_basis TEXT)"
    )
    bw.execute(
        "INSERT INTO bars VALUES ('XAUUSD', 'NATIVE_BROKER', ?, 2650.0, 2655.0, 2648.0, 2653.0, 'sha1', ?, 'BID')",
        (t0, t0 + 900),
    )
    bw.commit()
    try:
        bars_before = _dir_snapshot(bars_dir)
        out = followups.read_bars(
            "XAUUSD",
            datetime(2026, 11, 25, 13, 0, tzinfo=timezone.utc),
            datetime(2026, 11, 25, 13, 15, tzinfo=timezone.utc),
            path=bars_db,
            zero_write=True,
        )
        assert len(out) == 1 and out[0]["close"] == pytest.approx(2653.0)
        assert _dir_snapshot(bars_dir) == bars_before
    finally:
        bw.close()


def test_ast_static_scan_zero_bare_mode_ro_across_all_18_wired_modules():
    """AST static scan proving 0 remaining bare `?mode=ro` sqlite3.connect calls across all 18 wired modules."""
    assert len(WIRED_MODULES_18) == 18

    for rel_path in WIRED_MODULES_18:
        full_path = REPO_ROOT / rel_path
        assert full_path.is_file(), f"Missing wired module: {rel_path}"
        source = full_path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=rel_path)

        imported_helper = False
        bare_ro_calls: list[int] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("sqlite_readonly_v1"):
                names = {alias.name for alias in node.names}
                if names & {"open_readonly_sqlite", "connect_readonly_sqlite"}:
                    imported_helper = True
            if isinstance(node, ast.Call):
                func = node.func
                is_sqlite_connect = (
                    isinstance(func, ast.Attribute)
                    and func.attr == "connect"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "sqlite3"
                )
                if not is_sqlite_connect:
                    continue
                has_uri_kw = any(kw.arg == "uri" for kw in node.keywords)
                first_arg_src = ast.get_source_segment(source, node.args[0]) if node.args else ""
                if has_uri_kw or "mode=ro" in (first_arg_src or ""):
                    bare_ro_calls.append(node.lineno)

        assert imported_helper, f"{rel_path} does not import sqlite_readonly_v1 helper"
        assert bare_ro_calls == [], f"{rel_path} still has bare sqlite3.connect(?mode=ro) at lines {bare_ro_calls}"


def test_sqlite_readonly_v1_zero_forbidden_imports():
    """Confirm shared sqlite_readonly_v1.py stays strictly offline stdlib (security scan compliant)."""
    src = (REPO_ROOT / "live_contentops" / "sqlite_readonly_v1.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {"urllib", "requests", "http", "subprocess", "socket", "os"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden), f"Unexpected imports in sqlite_readonly_v1.py: {imported & forbidden}"


def _pin_live_wal_frame(db_path: Path) -> sqlite3.Connection:
    """Hold an open writer with one committed uncheckpointed WAL frame (a live post-15 Dec writer)."""
    writer = sqlite3.connect(str(db_path))
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE IF NOT EXISTS b11c39_probe (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")
    writer.execute("INSERT INTO b11c39_probe (id, label) VALUES (1, 'live_uncheckpointed_wal_row')")
    writer.commit()
    return writer


def test_b11c39_m1_durable_store_oversized_active_wal_defaults_to_explicit_live_read(tmp_path: Path):
    """B11C39-M1: an oversized operational store with wal > 0 stays readable; wal == 0 stays immutable/0-sidecar."""
    store_dir = tmp_path / "m1 store #1"
    db_path = store_dir / "contentops_daily_app_v1.sqlite3"

    # Literal 2-line single-process repro (max_snapshot_bytes=1024 mirrors 1.32 GiB > 256 MiB).
    store = ContentOpsDurableStore(db_path)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        repro_wal = sro.inspect_sqlite_storage(db_path).wal_bytes
        with store.get_read_only_connection(max_snapshot_bytes=1024) as ro:
            expected = sro.MODE_LIVE_WAL_EXPLICIT if repro_wal > 0 else sro.MODE_IMMUTABLE_ZERO_WAL
            assert ro.readonly_mode == expected
            assert ro.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0

    # Deterministic active WAL: wal_bytes > 0 and db_bytes > max_snapshot_bytes.
    writer = _pin_live_wal_frame(db_path)
    try:
        info = sro.inspect_sqlite_storage(db_path)
        assert info.journal_mode == "WAL" and info.wal_bytes > 0 and info.db_bytes > 1024
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with store.get_read_only_connection(max_snapshot_bytes=1024) as ro:
                assert ro.readonly_mode == sro.MODE_LIVE_WAL_EXPLICIT
                assert ro.readonly_warning == "LIVE_ACTIVE_WAL_SHARED_MEMORY_READ"
                assert [row["label"] for row in ro.execute("SELECT label FROM b11c39_probe").fetchall()] == [
                    "live_uncheckpointed_wal_row"
                ]
                with pytest.raises(sqlite3.OperationalError):
                    ro.execute("INSERT INTO b11c39_probe (id, label) VALUES (2, 'blocked')")
        assert any(issubclass(w.category, RuntimeWarning) for w in caught)

        # Explicit per-call override keeps the low-level fail-closed contract available.
        with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
            store.get_read_only_connection(max_snapshot_bytes=1024, allow_oversized_live_wal=False)
        assert exc_info.value.reason_code == sro.REASON_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED

        # Operational module readers carry the same opt-in (static proof in the AST test below).
        m_conn = manual_desk.open_store_read_only(db_path)
        try:
            assert m_conn.readonly_mode == sro.MODE_TEMP_SNAPSHOT_WAL  # small fixture: within cap
        finally:
            m_conn.close()
        # The low-level connector itself stays fail-closed by default.
        with pytest.raises(sro.SqliteReadOnlyError):
            sro.connect_readonly_sqlite(db_path, max_snapshot_bytes=1024)
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        writer.close()

    # Checkpointed to wal_bytes == 0 -> RO_IMMUTABLE_ZERO_WAL with 0 sidecars created or mutated.
    del store
    gc.collect()
    with closing(sqlite3.connect(str(db_path))) as w:
        w.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.with_name(db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()
    store = ContentOpsDurableStore(db_path, auto_migrate=False)
    before = _dir_snapshot(store_dir)
    assert list(before) == ["contentops_daily_app_v1.sqlite3"]
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # the zero-WAL path never emits the live-WAL warning
        with store.get_read_only_connection(max_snapshot_bytes=1024) as ro:
            assert ro.readonly_mode == sro.MODE_IMMUTABLE_ZERO_WAL
            assert ro.readonly_warning is None
            assert ro.execute("SELECT COUNT(*) FROM b11c39_probe").fetchone()[0] == 1
            assert _dir_snapshot(store_dir) == before
    assert _dir_snapshot(store_dir) == before


def test_b11c39_m2_snapshot_dir_hosts_private_active_wal_snapshot(tmp_path: Path):
    """B11C39-M2: snapshot_dir places the private snapshot under the caller's root and cleans it up."""
    db_path, writer = _create_active_wal_db(tmp_path / "src" / "live.sqlite3")
    snap_root = tmp_path / "scratch root #1"
    snap_root.mkdir()
    try:
        before = _dir_snapshot(db_path.parent)
        with sro.open_readonly_sqlite(db_path, snapshot_dir=snap_root) as conn:
            assert conn.readonly_mode == sro.MODE_TEMP_SNAPSHOT_WAL
            snap_dir = Path(conn._readonly_tempdir.name)
            assert snap_dir.parent.resolve() == snap_root.resolve()
            assert conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 2
        assert not snap_dir.exists()
        assert list(snap_root.iterdir()) == []
        assert _dir_snapshot(db_path.parent) == before
    finally:
        writer.close()


def test_b11c39_m2_digest_status_inside_dry_run_guard_with_active_wal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """B11C39-M2: digest_status() on an active-WAL scratch copy succeeds inside _Guard with 0 outside writes."""
    from live_contentops import substack_daily_digest_v1 as digest_owner

    scratch = tmp_path / "dry run scratch #1"
    production = tmp_path / "production" / "contentops_daily_app_v1.sqlite3"
    production.parent.mkdir()
    production.write_bytes(b"")  # protected sentinel; never opened
    copy = scratch / "contentops_daily_app_v1.sqlite3"
    seeded = ContentOpsDurableStore(copy)
    del seeded
    gc.collect()
    packet = {"digest_id": "cc143-digest-2026-12-15", "plan": {"plan_hash": "b11c39" + "0" * 58}}

    snapshot_parents: list[str | None] = []
    real_snapshot = sro._open_temp_wal_snapshot

    def _spy(resolved, **kwargs):
        snapshot_parents.append(None if kwargs.get("snapshot_dir") is None else str(kwargs["snapshot_dir"]))
        return real_snapshot(resolved, **kwargs)

    monkeypatch.setattr(sro, "_open_temp_wal_snapshot", _spy)
    writer = _pin_live_wal_frame(copy)
    try:
        info = sro.inspect_sqlite_storage(copy)
        assert info.wal_bytes > 0 and info.db_bytes <= sro.DEFAULT_MAX_SNAPSHOT_BYTES

        # Control: without a scratch-bound snapshot_dir the private snapshot lands in %TEMP% and is refused.
        unbound_guard = digest_1900._Guard(scratch, [production])
        unbound = ContentOpsDurableStore(copy, auto_migrate=False)
        with unbound_guard.active():
            with pytest.raises(PermissionError, match="DRY_RUN_WRITE_OUTSIDE_SCRATCH"):
                digest_owner.digest_status(unbound, packet)
        assert any("cc_sqlite_ro_snap_" in path for path in unbound_guard.refused_writes)

        # Fix: dry_run binds read_only_snapshot_dir=scratch -> zero writes outside scratch.
        guard = digest_1900._Guard(scratch, [production])
        store = ContentOpsDurableStore(copy, auto_migrate=False, read_only_snapshot_dir=scratch)
        snapshot_parents.clear()
        with guard.active():
            status = digest_owner.digest_status(store, packet)
        assert status["digest_id"] == packet["digest_id"]
        assert status["confirmed"] is False and status["web_confirmed"] is False
        assert guard.refused_writes == [] and guard.refused_connections == []
        assert snapshot_parents and set(snapshot_parents) == {str(scratch)}
        assert not any(p.name.startswith("cc_sqlite_ro_snap_") for p in scratch.iterdir())
        assert production.read_bytes() == b""
    finally:
        writer.close()


def test_b11c39_l1_non_regular_journal_entry_fails_closed(tmp_path: Path):
    """B11C39-L1: non-regular entries (directories/junctions) at -journal or -wal fail closed."""
    db_path = tmp_path / "rb.sqlite3"
    with closing(sqlite3.connect(str(db_path))) as conn:
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (7)")
        conn.commit()
    journal = db_path.with_name(db_path.name + "-journal")
    journal.mkdir()
    info = sro.inspect_sqlite_storage(db_path)
    assert info.journal_exists is True and info.journal_is_hot is True
    with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
        sro.connect_readonly_sqlite(db_path)
    assert exc_info.value.reason_code == sro.REASON_HOT_JOURNAL_ACTIVE
    journal.rmdir()

    wal_dir = db_path.with_name(db_path.name + "-wal")
    wal_dir.mkdir()
    with pytest.raises(sro.SqliteReadOnlyError) as wal_exc:
        sro.connect_readonly_sqlite(db_path)
    assert wal_exc.value.reason_code == sro.REASON_HEADER_INVALID
    wal_dir.rmdir()

    with sro.open_readonly_sqlite(db_path) as ro:
        assert ro.execute("SELECT x FROM t").fetchone()["x"] == 7


def test_b11c39_l2_exotic_win32_uri_open_failure_raises_sqlite_readonly_error(tmp_path: Path):
    """B11C39-L2: exotic Win32 extended/UNC prefixes fail closed with SqliteReadOnlyError (0 sidecars)."""
    clean_dir = tmp_path / "l2_clean"
    db_path = _create_clean_wal_db(clean_dir / "clean.sqlite3", [(1, "ok")])
    before = _dir_snapshot(clean_dir)

    drive = db_path.drive
    if drive and len(drive) >= 2 and drive[1] == ":":
        rest = str(db_path)[2:]
        exotic_paths = [
            f"\\\\?\\{db_path}",
            f"\\\\?\\UNC\\localhost\\{drive[0]}${rest}",
            f"\\\\localhost\\{drive[0]}${rest}",
            f"\\\\127.0.0.1\\{drive[0]}${rest}",
        ]
        for exotic in exotic_paths:
            with pytest.raises(sro.SqliteReadOnlyError) as exc_info:
                with sro.open_readonly_sqlite(exotic):
                    pass
            assert exc_info.value.reason_code in {
                sro.REASON_URI_OPEN_FAILED,
                sro.REASON_DATABASE_MISSING,
            }
        assert _dir_snapshot(clean_dir) == before


def test_b11c39_m1_every_operational_reader_opts_into_oversized_live_wal():
    """B11C39-M1 static proof: all 17 operational store readers pass allow_oversized_live_wal; the store defaults True."""
    import inspect as _inspect

    sig = _inspect.signature(ContentOpsDurableStore.get_read_only_connection)
    assert sig.parameters["allow_oversized_live_wal"].default is True
    assert sig.parameters["snapshot_dir"].default is None
    for fn in (sro.connect_readonly_sqlite, sro.open_readonly_sqlite):
        params = _inspect.signature(fn).parameters
        assert params["allow_oversized_live_wal"].default is False  # low-level stays fail-closed
        assert params["snapshot_dir"].default is None

    readers = [m for m in WIRED_MODULES_18 if m not in {
        "live_contentops/call_followups_v1.py",  # bars.sqlite3: allow_oversized_live_wal=not zero_write
        "live_contentops/durable_operational_store_v1.py",  # forwards its own True default
    }]
    assert len(readers) == 16
    total_calls = 0
    for rel_path in readers:
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel_path)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in {"open_readonly_sqlite", "connect_readonly_sqlite"}
        ]
        assert calls, rel_path
        for node in calls:
            kw = {k.arg: k.value for k in node.keywords}
            assert "allow_oversized_live_wal" in kw, f"{rel_path}:{node.lineno}"
            value = kw["allow_oversized_live_wal"]
            assert (isinstance(value, ast.Constant) and value.value is True) or isinstance(value, ast.Name), (
                f"{rel_path}:{node.lineno}")
        total_calls += len(calls)
    assert total_calls == 17  # retained_news_read_v1 holds two readers
