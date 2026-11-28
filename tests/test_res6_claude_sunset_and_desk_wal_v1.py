"""Hermetic regression tests for RES-6 post-04 Dec Claude sunset interlock,
RES-7 V6 Anthropic env-probe cleanup, and run_native_desktop_editorial.py:906
(`desk`) SQLite WAL / hot-journal / handle-close hardening (B16 C23b).

Strictly offline and isolated under tmp_path: zero live browser, zero network,
zero writes outside tmp_path, zero live A:\\ opens.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import types
import warnings

import pytest

from live_contentops import ai_provider_gate_v6 as provider_gate
from live_contentops import native_desktop_editorial_v1 as editorial
from live_contentops import unified_capability_env_readiness_v6 as env_readiness
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

REPO_ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_CLI = REPO_ROOT / "scripts" / "run_native_desktop_editorial.py"


@lru_cache(maxsize=1)
def _load_editorial_cli_once():
    spec = importlib.util.spec_from_file_location("run_native_desktop_editorial_res6", EDITORIAL_CLI)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_editorial_cli(_name: str = "run_native_desktop_editorial_res6"):
    return _load_editorial_cli_once()


def _isolated_profile(tmp_path: Path, db_name: str = "state.sqlite3", *, init_store: bool = False) -> dict[str, str]:
    store_path = tmp_path / db_name
    if init_store:
        ContentOpsDurableStore(store_path)
    out_root = tmp_path / "editorial"
    pub_root = tmp_path / "published"
    out_root.mkdir(parents=True, exist_ok=True)
    pub_root.mkdir(parents=True, exist_ok=True)
    pointer = tmp_path / "feed_pointer.json"
    pointer.write_text(json.dumps({"research_root": str(tmp_path / "research")}), encoding="utf-8")
    return {
        "schema_version": "contentops.native_desktop_operator_profile.v1",
        "store_path": str(store_path),
        "editorial_output_root": str(out_root),
        "feed_pointer_path": str(pointer),
        "published_memory_store": str(store_path),
        "published_memory_output_root": str(pub_root),
    }


def _dir_fingerprint(directory: Path) -> dict[str, tuple[int, str]]:
    snap: dict[str, tuple[int, str]] = {}
    for entry in sorted(directory.iterdir(), key=lambda p: p.name):
        if entry.is_file():
            raw = entry.read_bytes()
            snap[entry.name] = (len(raw), hashlib.sha256(raw).hexdigest())
    return snap


def _create_desk_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS outbox_messages (id TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS review_records (id TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS platform_dispatches (id TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS reconciliations (id TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS destination_readiness (id TEXT PRIMARY KEY, payload TEXT);
        """
    )


# ---------------------------------------------------------------------------
# RES-6: Unconditional post-04 Dec wall-clock Claude sunset + OverflowError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wall_now",
    [
        datetime(2026, 12, 3, 17, 0, 0, tzinfo=timezone.utc),
        "2026-12-03T17:00:00Z",
        datetime(2026, 12, 5, 12, 0, 0, tzinfo=timezone.utc),
        "2026-12-05T12:00:00Z",
    ],
)
def test_res6_backdated_cutoff_refused_post_sunset_across_entry_points(tmp_path, monkeypatch, wall_now):
    cli = _load_editorial_cli("run_native_desktop_editorial_res6_backdated")
    profile = _isolated_profile(tmp_path)
    req = "Prepare one clean analysis note covering US Treasury auction demand."
    backdated_dt = datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
    backdated_iso = "2026-12-01T12:00:00Z"
    monkeypatch.delenv(editorial.CLAUDE_SUNSET_ENV, raising=False)

    assert editorial.claude_sunset_active(backdated_iso, wall_now=wall_now, env={}) is True
    assert editorial.claude_sunset_active(None, wall_now=wall_now, env={}) is True

    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        editorial.assert_new_editorial_agent_allowed(
            "claude", now=backdated_iso, wall_now=wall_now, env={}
        )

    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        cli.resolve_owner_operation(
            profile,
            operation_id="claude-backdated-post-sunset",
            request=req,
            now=backdated_dt,
            wall_now=wall_now,
            editorial_agent="claude",
        )
    assert not (Path(profile["editorial_output_root"]) / "claude-backdated-post-sunset").exists()

    forged_new_binding = {
        "schema_version": cli.BINDING_SCHEMA,
        "run_id": "claude-forged-backdated",
        "editorial_agent": "claude",
        "cutoff_utc": backdated_iso,
        "output_dir": str(Path(profile["editorial_output_root"]) / "claude-forged-backdated"),
        "store_path": profile["store_path"],
        "feed_pointer_path": profile["feed_pointer_path"],
        "published_memory_store": profile["published_memory_store"],
        "published_memory_output_root": profile["published_memory_output_root"],
        "owner_manual_validation": True,
    }
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        cli.validate_binding(forged_new_binding, new_binding=True, wall_now=wall_now)

    # Codex remains unaffected under the exact same post-sunset wall_now.
    assert (
        editorial.assert_new_editorial_agent_allowed("codex", now=backdated_iso, wall_now=wall_now, env={})
        == "codex"
    )
    codex_path, codex_binding = cli.resolve_owner_operation(
        profile,
        operation_id="codex-same-wall-now",
        request=req,
        now=backdated_dt,
        wall_now=wall_now,
        editorial_agent="codex",
    )
    assert codex_path.is_file()
    assert "editorial_agent" not in codex_binding


def test_res6_default_wall_now_reads_live_utc_clock_when_omitted(tmp_path, monkeypatch):
    cli = _load_editorial_cli("run_native_desktop_editorial_res6_live_wall")
    profile = _isolated_profile(tmp_path)
    req = "Prepare one clean analysis note covering US Treasury auction demand."
    backdated_dt = datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.delenv(editorial.CLAUDE_SUNSET_ENV, raising=False)

    class _PostSunsetDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            base = datetime(2026, 12, 5, 12, 0, 0, tzinfo=timezone.utc)
            return base if tz is None else base.astimezone(tz)

    monkeypatch.setattr(editorial, "datetime", _PostSunsetDatetime)

    # Without explicit wall_now, live UTC clock blocks backdated cutoff_utc everywhere.
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        editorial.assert_new_editorial_agent_allowed("claude", now="2026-12-01T12:00:00Z", env={})

    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        cli.resolve_owner_operation(
            profile,
            operation_id="claude-live-wall-blocked",
            request=req,
            now=backdated_dt,
            editorial_agent="claude",
        )
    assert not (Path(profile["editorial_output_root"]) / "claude-live-wall-blocked").exists()

    # Explicit pre-sunset wall_now keeps hermetic pre-sunset unit tests green past 04 Dec.
    pre = datetime(2026, 12, 3, 16, 59, 59, tzinfo=timezone.utc)
    assert editorial.assert_new_editorial_agent_allowed("claude", now=pre, wall_now=pre, env={}) == "claude"
    pre_path, pre_binding = cli.resolve_owner_operation(
        profile,
        operation_id="claude-pinned-pre-sunset",
        request=req,
        now=pre,
        wall_now=pre,
        editorial_agent="claude",
    )
    assert pre_path.is_file()
    assert pre_binding["editorial_agent"] == "claude"


@pytest.mark.parametrize(
    "bad_clock",
    [
        "9999-12-31T23:59:59-05:00",
        "0001-01-01T00:00:00+05:00",
        datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=-5))),
        datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=5))),
        "",
        "   ",
        "not-a-timestamp",
        12345,
    ],
)
def test_res6_extreme_iso_overflow_and_malformed_clocks_normalize_to_value_error(bad_clock):
    pre_wall = datetime(2026, 11, 28, 12, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="CLAUDE_SUNSET_CLOCK_INVALID"):
        editorial._parse_utc_moment(bad_clock)

    with pytest.raises(ValueError, match="CLAUDE_SUNSET_CLOCK_INVALID"):
        editorial.claude_sunset_active(bad_clock, env={})

    with pytest.raises(ValueError, match="CLAUDE_SUNSET_CLOCK_INVALID"):
        editorial.claude_sunset_active(pre_wall, wall_now=bad_clock, env={})

    with pytest.raises(ValueError, match="CLAUDE_SUNSET_CLOCK_INVALID"):
        editorial.assert_new_editorial_agent_allowed("claude", now=bad_clock, wall_now=pre_wall, env={})


def test_res6_native_desktop_turn_normalizes_forged_extreme_and_malformed_cutoffs(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "turn.sqlite3")
    for idx, bad_clock in enumerate(
        (
            "9999-12-31T23:59:59-05:00",
            "0001-01-01T00:00:00+05:00",
            "",
            "   ",
            "not-a-timestamp",
            12345,
        )
    ):
        run = f"forged-bad-clock-{idx}"
        work = "cc-opportunity-" + sha256_of(run)
        store.create_work_item(story_id=work, work_item_id=work, title="bad", target_surface="CONTENTOPS_EDITORIAL_ONLY")
        forged = {"run_id": run, "output_dir": str(tmp_path), "editorial_agent": "claude", "cutoff_utc": bad_clock}
        store.register_outbox_message(
            message_id="native-operation-binding-" + sha256_of(run),
            work_item_id=work,
            destination="internal:native-desktop-editorial",
            payload=canonical_bytes(forged).decode("utf-8"),
            status="EDITORIAL_INTERNAL",
        )
        with pytest.raises(ValueError, match="CLAUDE_SUNSET_CLOCK_INVALID"):
            editorial.NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)


@pytest.mark.parametrize(
    "cutoff_utc,known_at",
    [
        ("9999-12-31T23:59:59-05:00", "2026-11-05T10:00:00Z"),
        ("0001-01-01T00:00:00+05:00", "2026-11-05T10:00:00Z"),
        ("2026-11-05T10:00:00Z", "9999-12-31T23:59:59-05:00"),
        ("2026-11-05T10:00:00Z", "0001-01-01T00:00:00+05:00"),
        ("9999-12-31T23:59:59-05:00", "9999-12-31T23:59:59-05:00"),
        ("2026-11-05T10:00:00", "2026-11-05T09:59:00Z"),
        ("2026-11-05T10:00:00Z", "2026-11-05T09:59:00"),
        ("2026-11-05T10:00:00Z", 12345),
        (12345, "2026-11-05T09:59:00Z"),
    ],
)
def test_res6_validate_binding_known_at_cutoff_normalizes_overflow_and_type_errors(tmp_path, cutoff_utc, known_at):
    cli = _load_editorial_cli("run_native_desktop_editorial_res6_known_at")
    profile = _isolated_profile(tmp_path)
    binding = {
        "schema_version": cli.BINDING_SCHEMA,
        "run_id": "known-at-overflow",
        "cutoff_utc": cutoff_utc,
        "input_known_at_cutoff_utc": known_at,
        "output_dir": str(Path(profile["editorial_output_root"]) / "known-at-overflow"),
        "store_path": profile["store_path"],
        "feed_pointer_path": profile["feed_pointer_path"],
        "published_memory_store": profile["published_memory_store"],
        "published_memory_output_root": profile["published_memory_output_root"],
        "owner_manual_validation": True,
    }
    with pytest.raises(ValueError, match="NATIVE_INPUT_KNOWN_AT_CUTOFF_INVALID"):
        cli.validate_binding(binding)


def test_res6_cc300_missing_cutoff_and_historical_replay_preserved_post_sunset(tmp_path, monkeypatch):
    cli = _load_editorial_cli()
    profile = _isolated_profile(tmp_path, init_store=True)
    req = "Historical pre-sunset Claude editorial operation for readback proof."
    hist_now = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)
    hist_path, hist_binding = cli.resolve_owner_operation(
        profile,
        operation_id="hist-claude-replay",
        request=req,
        now=hist_now,
        wall_now=hist_now,
        editorial_agent="claude",
    )

    class _PostSunsetDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            base = datetime(2026, 12, 10, 12, 0, 0, tzinfo=timezone.utc)
            return base if tz is None else base.astimezone(tz)

    monkeypatch.setattr(editorial, "datetime", _PostSunsetDatetime)

    # Resuming an existing pre-sunset Claude binding remains intact post-sunset.
    resumed_path, resumed_binding = cli.resolve_owner_operation(profile, operation_id="hist-claude-replay")
    assert resumed_path == hist_path
    assert resumed_binding == hist_binding

    # Historical CC-300 fixture WITHOUT cutoff_utc remains compatible in NativeDesktopTurn.
    store = ContentOpsDurableStore(profile["store_path"])
    run = "cc300-missing-cutoff"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="cc300", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    cc300_binding = {"run_id": run, "output_dir": str(tmp_path), "editorial_agent": "claude"}
    store.register_outbox_message(
        message_id="native-operation-binding-" + sha256_of(run),
        work_item_id=work,
        destination="internal:native-desktop-editorial",
        payload=canonical_bytes(cc300_binding).decode("utf-8"),
        status="EDITORIAL_INTERNAL",
    )
    turn = editorial.NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    assert turn.editorial_agent == "claude"


# ---------------------------------------------------------------------------
# RES-7: Dormant V6 env-probe cleanup (ANTHROPIC_API_KEY removed)
# ---------------------------------------------------------------------------


def test_res7_v6_env_probes_exclude_retired_anthropic_api_key():
    creds = provider_gate.inspect_provider_credentials()
    assert "ANTHROPIC_API_KEY" not in creds
    assert {"OPENAI_API_KEY", "VERTEX_CREDENTIALS", "NINE_ROUTER_API_KEY"} == set(creds)

    assert "ANTHROPIC_API_KEY" not in env_readiness.known_key_names()
    pkt = env_readiness.make_unified_capability_env_readiness_packet(
        env={"ANTHROPIC_API_KEY": "retired-key-must-not-enable"},
        dotenv_path="missing.env",
        scan_mode="process_env_only",
    )
    caps = {c["capability_id"]: c for c in pkt.capabilities}
    assert caps["ai_provider_research_writer"]["capability_status"] == "unavailable"
    assert "missing_ai_provider_key_name" in caps["ai_provider_research_writer"]["blockers"]
    assert "ANTHROPIC_API_KEY" not in caps["ai_provider_research_writer"]["optional_key_names"]


# ---------------------------------------------------------------------------
# L906 (`desk`): SQLite WAL / Hot -journal / URI #% / Handle-Close Hardening
# ---------------------------------------------------------------------------


def test_desk_sqlite_clean_wal_0202_special_uri_zero_sidecars_and_handle_closed(tmp_path):
    cli = _load_editorial_cli("run_native_desktop_editorial_wal_clean")
    db_dir = tmp_path / "wal #100% clean"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "desk #100% clean.sqlite3"

    writer = sqlite3.connect(str(db_path))
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        _create_desk_tables(writer)
        writer.execute("INSERT INTO outbox_messages VALUES ('m1', '{\"ok\":true}')")
        writer.commit()
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        writer.close()

    hdr = db_path.read_bytes()[:100]
    assert hdr[18:20] == b"\x02\x02"
    assert sorted(p.name for p in db_dir.iterdir()) == [db_path.name]
    before = _dir_fingerprint(db_dir)

    with cli._open_desk_readonly_sqlite(db_path, use_shared_helper=False) as conn:
        during = _dir_fingerprint(db_dir)
        assert during == before
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY rowid")]
        assert rows == [{"id": "m1", "payload": '{"ok":true}'}]
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO outbox_messages VALUES ('m2', '{}')")

    after = _dir_fingerprint(db_dir)
    assert after == before
    assert sorted(p.name for p in db_dir.iterdir()) == [db_path.name]

    # Connection handle MUST be closed (0 leaked handles -> unlinks cleanly on Windows).
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
    db_path.unlink()
    assert not db_path.exists()


def test_desk_sqlite_active_wal_reads_uncheckpointed_rows_zero_shm_mutation(tmp_path):
    cli = _load_editorial_cli("run_native_desktop_editorial_wal_active")
    db_dir = tmp_path / "wal #active% dir"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "desk #active% wal.sqlite3"

    writer = sqlite3.connect(str(db_path))
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        writer.execute("PRAGMA wal_autocheckpoint=0")
        _create_desk_tables(writer)
        writer.execute("INSERT INTO outbox_messages VALUES ('base_row', '{\"v\":1}')")
        writer.commit()
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        # Commit an uncheckpointed row into -wal while keeping writer open.
        writer.execute("INSERT INTO outbox_messages VALUES ('wal_frame_2', '{\"v\":2}')")
        writer.commit()

        wal_path = db_path.with_name(db_path.name + "-wal")
        shm_path = db_path.with_name(db_path.name + "-shm")
        assert wal_path.is_file() and wal_path.stat().st_size > 0
        assert shm_path.is_file() and shm_path.stat().st_size > 0
        before = _dir_fingerprint(db_dir)

        snap_dir: Path | None = None
        with cli._open_desk_readonly_sqlite(db_path, use_shared_helper=False) as conn:
            # Verify snapshot lives in a private temp directory, NOT db_dir.
            db_list = conn.execute("PRAGMA database_list").fetchall()
            opened_file = Path(db_list[0]["file"])
            snap_dir = opened_file.parent
            assert snap_dir != db_dir
            assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
            rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY rowid")]
            assert [r["id"] for r in rows] == ["base_row", "wal_frame_2"]
            assert _dir_fingerprint(db_dir) == before
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("INSERT INTO outbox_messages VALUES ('bad', '{}')")

        assert _dir_fingerprint(db_dir) == before
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
        assert snap_dir is not None and not snap_dir.exists()
    finally:
        writer.close()


def test_desk_sqlite_hot_rollback_journal_fails_closed_zero_dirty_rows(tmp_path):
    cli = _load_editorial_cli("run_native_desktop_editorial_hot_journal")
    live_dir = tmp_path / "live_writer"
    crashed_dir = tmp_path / "crashed_copy"
    live_dir.mkdir(parents=True)
    crashed_dir.mkdir(parents=True)
    live_db = live_dir / "desk.sqlite3"
    crashed_db = crashed_dir / "desk.sqlite3"

    writer = sqlite3.connect(str(live_db), isolation_level=None)
    try:
        assert writer.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower() == "delete"
        writer.execute("PRAGMA page_size=4096")
        writer.execute("PRAGMA cache_size=2")
        _create_desk_tables(writer)
        writer.execute("BEGIN")
        writer.executemany(
            "INSERT INTO outbox_messages VALUES (?, ?)",
            [(f"row_{i:04d}", "CLEAN_" + "A" * 2000) for i in range(400)],
        )
        writer.execute("COMMIT")

        # Start an uncommitted in-place update spilling dirty pages and populating hot -journal.
        writer.execute("BEGIN IMMEDIATE")
        writer.executemany(
            "UPDATE outbox_messages SET payload = ? WHERE id = ?",
            [("DIRTY_" + "X" * 2000, f"row_{i:04d}") for i in range(400)],
        )
        live_journal = live_db.with_name(live_db.name + "-journal")
        assert live_journal.is_file() and live_journal.stat().st_size > 0
        assert live_journal.read_bytes()[:28] != b"\x00" * 28

        # Snapshot crashed (db, -journal) mid-transaction before rolling back the writer.
        shutil.copy2(live_db, crashed_db)
        shutil.copy2(live_journal, crashed_db.with_name(crashed_db.name + "-journal"))
        writer.execute("ROLLBACK")
    finally:
        writer.close()

    before = _dir_fingerprint(crashed_dir)

    # Confirm unguarded immutable=1 WOULD leak uncommitted dirty rows (e.g. 399/400) on this fixture.
    naive = sqlite3.connect(crashed_db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        dirty_count = naive.execute(
            "SELECT COUNT(*) FROM outbox_messages WHERE payload LIKE 'DIRTY_%'"
        ).fetchone()[0]
    finally:
        naive.close()
    assert dirty_count >= 350

    # Hardened reader MUST fail closed with OperationalError and mutate 0 bytes.
    with pytest.raises(
        sqlite3.OperationalError,
        match=r"SQLITE_HOT_JOURNAL_ACTIVE.*SQLITE_HOT_ROLLBACK_JOURNAL_PRESENT",
    ):
        with cli._open_desk_readonly_sqlite(crashed_db, use_shared_helper=False):
            pytest.fail("Hot rollback journal must never yield a connection")

    assert _dir_fingerprint(crashed_dir) == before


def test_desk_sqlite_persist_zeroed_journal_succeeds_zero_write(tmp_path):
    cli = _load_editorial_cli("run_native_desktop_editorial_persist_journal")
    db_dir = tmp_path / "persist_dir"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "persist.sqlite3"

    writer = sqlite3.connect(str(db_path))
    try:
        assert writer.execute("PRAGMA journal_mode=PERSIST").fetchone()[0].lower() == "persist"
        _create_desk_tables(writer)
        writer.execute("INSERT INTO outbox_messages VALUES ('persisted_1', 'ok')")
        writer.commit()
    finally:
        writer.close()

    journal_path = db_path.with_name(db_path.name + "-journal")
    assert journal_path.is_file() and journal_path.stat().st_size >= 28
    assert journal_path.read_bytes()[:28] == b"\x00" * 28
    before = _dir_fingerprint(db_dir)

    with cli._open_desk_readonly_sqlite(db_path, use_shared_helper=False) as conn:
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages")]
        assert rows == [{"id": "persisted_1", "payload": "ok"}]

    assert _dir_fingerprint(db_dir) == before
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_desk_sqlite_oversized_active_wal_limit_and_explicit_ro(tmp_path):
    cli = _load_editorial_cli("run_native_desktop_editorial_oversized_wal")
    db_path = tmp_path / "oversized.sqlite3"

    writer = sqlite3.connect(str(db_path))
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        _create_desk_tables(writer)
        writer.execute("INSERT INTO outbox_messages VALUES ('big_row', 'ok')")
        writer.commit()

        with pytest.raises(sqlite3.OperationalError, match="SQLITE_ACTIVE_WAL_SNAPSHOT_LIMIT_EXCEEDED"):
            with cli._open_desk_readonly_sqlite(
                db_path,
                max_snapshot_bytes=1,
                allow_oversized_live_wal=False,
                use_shared_helper=False,
            ):
                pytest.fail("Oversized active WAL must fail closed when allow_oversized_live_wal=False")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with cli._open_desk_readonly_sqlite(
                db_path,
                max_snapshot_bytes=1,
                allow_oversized_live_wal=True,
                use_shared_helper=False,
            ) as conn:
                assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
                rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages")]
                assert rows == [{"id": "big_row", "payload": "ok"}]
        assert any("LIVE_ACTIVE_WAL_SHARED_MEMORY_READ" in str(w.message) for w in caught)
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
    finally:
        writer.close()


def test_desk_sqlite_header_validation_concurrent_mutation_and_b11_c39_delegation(tmp_path, monkeypatch):
    cli = _load_editorial_cli("run_native_desktop_editorial_edge_cases")

    # Missing DB fails closed.
    with pytest.raises(sqlite3.OperationalError, match="SQLITE_DATABASE_MISSING"):
        with cli._open_desk_readonly_sqlite(tmp_path / "missing.sqlite3", use_shared_helper=False):
            pass

    # Invalid header fails closed.
    bad_db = tmp_path / "corrupt.sqlite3"
    bad_db.write_bytes(b"NOT_A_SQLITE_FILE" * 10)
    with pytest.raises(sqlite3.OperationalError, match="SQLITE_HEADER_INVALID"):
        with cli._open_desk_readonly_sqlite(bad_db, use_shared_helper=False):
            pass

    # Concurrent mutation during double-SHA-256 verification fails closed cleanly after retries.
    active_db = tmp_path / "racing.sqlite3"
    writer = sqlite3.connect(str(active_db))
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        _create_desk_tables(writer)
        writer.execute("INSERT INTO outbox_messages VALUES ('r1', 'v1')")
        writer.commit()

        call_counter = {"n": 0}

        def _mutating_sha256(_path: Path) -> str:
            call_counter["n"] += 1
            return f"changing-digest-{call_counter['n']}"

        monkeypatch.setattr(cli, "_desk_file_sha256", _mutating_sha256)
        monkeypatch.setattr(cli, "_DESK_SQLITE_RETRY_SLEEP_SECONDS", 0.0)
        with pytest.raises(sqlite3.OperationalError, match="SQLITE_SNAPSHOT_CONCURRENT_MUTATION"):
            with cli._open_desk_readonly_sqlite(active_db, snapshot_retries=2, use_shared_helper=False):
                pass
    finally:
        writer.close()

    # When live_contentops.sqlite_readonly_v1.open_readonly_sqlite is present (B11 C39),
    # _open_desk_readonly_sqlite delegates directly with matching keyword arguments.
    delegated_calls: list[tuple[Path | str, dict[str, object]]] = []
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.row_factory = sqlite3.Row

    @contextmanager
    def _fake_open_readonly_sqlite(path, **kwargs):
        delegated_calls.append((path, kwargs))
        try:
            yield mem_conn
        finally:
            mem_conn.close()

    fake_mod = types.ModuleType("live_contentops.sqlite_readonly_v1")
    fake_mod.open_readonly_sqlite = _fake_open_readonly_sqlite  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "live_contentops.sqlite_readonly_v1", fake_mod)

    with cli._open_desk_readonly_sqlite(active_db, max_snapshot_bytes=12345, snapshot_retries=2) as conn:
        assert conn is mem_conn
    assert len(delegated_calls) == 1
    assert delegated_calls[0][0] == active_db
    assert delegated_calls[0][1] == {
        "row_factory": sqlite3.Row,
        "max_snapshot_bytes": 12345,
        "allow_oversized_live_wal": True,
        "snapshot_retries": 2,
    }


def test_desk_cli_subcommand_zero_write_wal_and_hot_journal_refusal(tmp_path, monkeypatch, capsys):
    cli = _load_editorial_cli("run_native_desktop_editorial_desk_cli")
    from live_contentops import capital_chronicle_report_editorial_workspace_v1 as workspace
    from live_contentops import native_newsroom_learning_v1 as learning

    db_dir = tmp_path / "desk #cli% store"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "state #100%.sqlite3"
    # Build a Clean WAL 0202 store with the 5 desk tables and zero sidecars on disk.
    w = sqlite3.connect(str(db_path))
    try:
        assert w.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        _create_desk_tables(w)
        w.execute("INSERT INTO outbox_messages VALUES ('desk_m1', '{\"ok\":true}')")
        w.commit()
        w.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        w.close()
    assert db_path.read_bytes()[18:20] == b"\x02\x02"
    assert sorted(p.name for p in db_dir.iterdir()) == [db_path.name]
    before = _dir_fingerprint(db_dir)

    seen_counts: dict[str, int] = {}

    def _fake_projection(rows, *, review_records, dispatches, reconciliations, readiness):
        seen_counts["rows"] = len(rows)
        seen_counts["reviews"] = len(review_records)
        seen_counts["dispatches"] = len(dispatches)
        seen_counts["reconciliations"] = len(reconciliations)
        seen_counts["readiness"] = len(readiness)
        return {"audience_learning": {}, "native_edition": []}

    monkeypatch.setattr(workspace, "report_workspace_projection", _fake_projection)
    monkeypatch.setattr(learning, "learning_context", lambda *_args, **_kwargs: {"sample_count": 0})
    monkeypatch.setattr(cli.subprocess, "run", lambda *_args, **_kwargs: types.SimpleNamespace(returncode=0))

    profile_path = tmp_path / "profile.json"
    out_root = tmp_path / "desk_out"
    profile_path.write_text(
        json.dumps(
            {
                "store_path": str(db_path),
                "published_memory_store": str(db_path),
                "editorial_output_root": str(out_root),
            }
        ),
        encoding="utf-8",
    )

    rc = cli.main(["desk", "--profile", str(profile_path)])
    assert rc == 0
    assert _dir_fingerprint(db_dir) == before
    assert (out_root / "desk" / "workspace.json").is_file()
    assert seen_counts == {"rows": 1, "reviews": 0, "dispatches": 0, "reconciliations": 0, "readiness": 0}
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["mode"] == "OFFLINE_READ_ONLY_OWNER_REVIEW"
    assert out["publication_authority"] is False

    # Hot rollback -journal on the desk store causes `desk` CLI to fail closed cleanly.
    hot_dir = tmp_path / "hot_desk_store"
    hot_dir.mkdir(parents=True)
    hot_db = hot_dir / "state.sqlite3"
    shutil.copy2(db_path, hot_db)
    # Prove desk closed its handle on db_path cleanly (0 leaked handles -> unlink succeeds).
    db_path.unlink()
    assert not db_path.exists()
    # Write a non-zero rollback journal beside hot_db.
    hot_db.with_name(hot_db.name + "-journal").write_bytes(b"\xd9\xd5\x05\xf9\x20\xa1\x63\xd7" + b"\x01" * 4088)
    hot_out = tmp_path / "hot_desk_out"
    hot_profile = tmp_path / "hot_profile.json"
    hot_profile.write_text(
        json.dumps(
            {
                "store_path": str(hot_db),
                "published_memory_store": str(hot_db),
                "editorial_output_root": str(hot_out),
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        sqlite3.OperationalError,
        match=r"SQLITE_HOT_JOURNAL_ACTIVE.*SQLITE_HOT_ROLLBACK_JOURNAL_PRESENT",
    ):
        cli.main(["desk", "--profile", str(hot_profile)])
    assert not (hot_out / "desk" / "workspace.json").exists()
