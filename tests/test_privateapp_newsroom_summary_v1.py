"""Tests for CC-153 store-read hardening and privateapp_newsroom_summary_v1 (Decision 184).

Covers:
1. Optional CC-153 read indexes in ContentOpsDurableStore.ensure_outbox_read_indexes()
   (verifying exact EXPLAIN QUERY PLAN index usage and preserved migration/lineage checks).
2. Zero-N+1 hardened CC-153 store reads across >2,500 historical dispatches & >5,000 readbacks
   on an un-indexed database (proving zero 3.001s timeout and zero MAX_ROWS=2000 cliff).
3. Bounded fail-closed outage handling: SQLITE_INTERRUPT -> CONTENTOPS_STORE_READ_TIMEOUT,
   SQLITE_BUSY -> retry + CONTENTOPS_STORE_BUSY_RETRY_EXHAUSTED, corrupt DB / missing table ->
   immediate CONTENTOPS_STORE_READ_FAILED, missing DB -> CONTENTOPS_STORE_MISSING, non-empty WAL
   refuses immutable=1 fallback.
4. Strictly private-only ContentOpsNewsroomPrivateSummaryV1 generator: zero _private_texts or
   forbidden key/canary echoes, zero raw *_NOT_WRITTEN / debug enums on primary display fields,
   full forensic detail nested under diagnostics, pause/unpause/partial-suspension/kill-switch,
   x_list_feed fast header parsing, CC-711 keepalive/Neo health, CC-817 attention map allow-list,
   wraps/posts/replies/gold_note/audience, and public output path refusal + CR=0/BOM=False.

Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_13
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops import privateapp_newsroom_summary_v1 as summary_mod


def _seed_store_with_history(
    db_path: Path,
    *,
    historical_dispatches: int = 0,
    readbacks_per_dispatch: int = 0,
    with_indexes: bool = False,
) -> ContentOpsDurableStore:
    store = ContentOpsDurableStore(db_path)
    if with_indexes:
        store.ensure_outbox_read_indexes()

    conn = store.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO work_items(work_item_id,story_id,title,current_state,state_version,"
            "target_surface,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                "wi-hist",
                "story-hist",
                "Historical item",
                "PUBLISHED",
                1,
                "SUBSTACK",
                "2026-10-01T00:00:00+00:00",
                "2026-10-01T00:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO work_items(work_item_id,story_id,title,current_state,state_version,"
            "target_surface,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                "wi-today",
                "story-today",
                "Today's Wrap",
                "PUBLISHED",
                1,
                "SUBSTACK",
                "2026-11-26T00:00:00+00:00",
                "2026-11-26T00:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO outbox_messages(message_id,work_item_id,destination,payload,status,created_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                "msg-hist",
                "wi-hist",
                "substack",
                json.dumps({"canonical_url": "https://capitalchronicle.substack.com/p/old-wrap"}),
                "DISPATCH_CONFIRMED",
                "2026-10-15T12:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO outbox_messages(message_id,work_item_id,destination,payload,status,created_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                "msg-today",
                "wi-today",
                "substack",
                json.dumps({"canonical_url": "https://capitalchronicle.substack.com/p/today-wrap"}),
                "DISPATCH_CONFIRMED",
                "2026-11-26T01:00:00+00:00",
            ),
        )
        # Historical dispatches + readbacks (>2,500 dispatches and >5,000 readbacks when requested).
        if historical_dispatches > 0:
            base_dt = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
            disp_rows = []
            rb_rows = []
            for idx in range(historical_dispatches):
                did = f"disp-hist-{idx:05d}"
                ts = (base_dt + timedelta(minutes=idx)).isoformat()
                disp_rows.append((
                    did,
                    "msg-hist",
                    "telegram",
                    "DISPATCH_CONFIRMED",
                    ts,
                    f"https://t.me/CapitalChronicle/{1000 + idx}",
                ))
                for r_idx in range(readbacks_per_dispatch):
                    rb_ts = (base_dt + timedelta(minutes=idx, seconds=10 + r_idx)).isoformat()
                    rb_rows.append((
                        f"rb-hist-{idx:05d}-{r_idx}",
                        did,
                        json.dumps({"verified": True, "seq": r_idx}),
                        rb_ts,
                    ))
            conn.executemany(
                "INSERT INTO platform_dispatches(dispatch_id,message_id,platform,status,dispatched_at,public_object_url) "
                "VALUES (?,?,?,?,?,?)",
                disp_rows,
            )
            if rb_rows:
                conn.executemany(
                    "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
                    rb_rows,
                )

        # Earlier-day dispatch that receives a verified readback on production day 2026-11-26.
        conn.execute(
            "INSERT INTO platform_dispatches(dispatch_id,message_id,platform,status,dispatched_at,public_object_url) "
            "VALUES (?,?,?,?,?,?)",
            (
                "disp-earlier-verified-today",
                "msg-hist",
                "substack",
                "DISPATCH_CONFIRMED",
                "2026-11-20T12:00:00+00:00",
                "https://capitalchronicle.substack.com/p/old-wrap",
            ),
        )
        conn.execute(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            (
                "rb-earlier-1",
                "disp-earlier-verified-today",
                json.dumps({"verified": True}),
                "2026-11-20T12:05:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            (
                "rb-earlier-today",
                "disp-earlier-verified-today",
                json.dumps({"verified": True}),
                "2026-11-26T02:00:00+00:00",
            ),
        )

        # Today's dispatch + verified readback.
        conn.execute(
            "INSERT INTO platform_dispatches(dispatch_id,message_id,platform,status,dispatched_at,public_object_url) "
            "VALUES (?,?,?,?,?,?)",
            (
                "disp-today-1",
                "msg-today",
                "substack",
                "DISPATCH_CONFIRMED",
                "2026-11-26T01:05:00+00:00",
                "https://capitalchronicle.substack.com/p/today-wrap",
            ),
        )
        conn.execute(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            (
                "rb-today-1",
                "disp-today-1",
                json.dumps({"verified": True}),
                "2026-11-26T01:06:00+00:00",
            ),
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return store


def test_durable_store_read_indexes_accelerate_cc153_without_changing_migrations(tmp_path):
    db_path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(db_path)
    version_before = store.get_current_schema_version()

    store.ensure_outbox_read_indexes()
    # Idempotent second call.
    store.ensure_outbox_read_indexes()

    assert store.get_current_schema_version() == version_before
    assert store.verify_applied_migrations()

    with store.get_read_only_connection() as conn:
        assert conn.execute("PRAGMA temp_store").fetchone()[0] == 2  # MEMORY
        rb_plan = [
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT readback_data,read_at FROM readbacks "
                "WHERE dispatch_id=? ORDER BY read_at",
                ("d-1",),
            ).fetchall()
        ]
        disp_plan = [
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT dispatch_id FROM platform_dispatches "
                "WHERE dispatched_at >= ? AND dispatched_at < ? ORDER BY dispatched_at DESC",
                ("2026-11-24", "2026-11-28"),
            ).fetchall()
        ]
        rb_range_plan = [
            row[3]
            for row in conn.execute(
                "EXPLAIN QUERY PLAN SELECT dispatch_id,read_at FROM readbacks "
                "WHERE read_at >= ? AND read_at < ? ORDER BY read_at",
                ("2026-11-24", "2026-11-28"),
            ).fetchall()
        ]

    assert any("idx_readbacks_dispatch_read_at_read" in step for step in rb_plan)
    assert not any("TEMP B-TREE" in step for step in rb_plan)
    assert any("idx_platform_dispatches_dispatched_at_read" in step for step in disp_plan)
    assert any("idx_readbacks_read_at_dispatch_read" in step for step in rb_range_plan)


def test_cc153_hardened_reader_handles_large_unindexed_store_without_timeout_or_row_limit(tmp_path):
    db_path = tmp_path / "large_unindexed.sqlite3"
    # Exceeds legacy MAX_ROWS=2000 dispatches and simulates 5,000+ un-indexed readbacks.
    _seed_store_with_history(db_path, historical_dispatches=2500, readbacks_per_dispatch=2, with_indexes=False)

    store_res, digest_res = summary_mod.read_cc153_store_hardened(
        db_path,
        day="2026-11-26",
        now_utc="2026-11-26T05:00:00Z",
        timeout_seconds=3.0,
    )

    ev = store_res["evidence"]
    assert ev["state"] == "AVAILABLE"
    assert ev["reason"] is None
    assert ev["read_attempts"] == 1
    assert ev["read_elapsed_seconds"] < 1.5
    assert ev["query_strategy"] == "BOUNDED_ZERO_N_PLUS_1_V1"
    assert store_res["indexes_present"]["readbacks_dispatch_index"] is False

    # Both today's dispatch AND the earlier-day dispatch verified today are returned,
    # with exact earliest verified readback timestamp preserved.
    by_id = {d["dispatch_id"]: d for d in store_res["dispatches"]}
    assert set(by_id) == {"disp-today-1", "disp-earlier-verified-today"}
    assert by_id["disp-today-1"]["verified_readback_at_utc"] == "2026-11-26T01:06:00+00:00"
    assert by_id["disp-earlier-verified-today"]["verified_readback_at_utc"] == "2026-11-20T12:05:00+00:00"
    assert digest_res["evidence"]["reason"] == "NO_OWNER_DAILY_DIGEST_RECORD_BOUND_CC143"


def test_cc153_hardened_reader_fails_closed_on_timeout_corrupt_missing_and_busy(tmp_path, monkeypatch):
    # 1. Missing store fails closed as MISSING.
    missing_store, _ = summary_mod.read_cc153_store_hardened(
        tmp_path / "does-not-exist.sqlite3",
        day="2026-11-26",
        now_utc="2026-11-26T05:00:00Z",
    )
    assert missing_store["evidence"]["state"] == "MISSING"
    assert missing_store["evidence"]["reason"] == "CONTENTOPS_STORE_MISSING"
    assert missing_store["dispatches"] is None

    # 2. Corrupt DB fails closed immediately without retry or masking.
    corrupt = tmp_path / "corrupt.sqlite3"
    corrupt.write_bytes(b"not a valid sqlite database header" * 64)
    corrupt_store, _ = summary_mod.read_cc153_store_hardened(
        corrupt,
        day="2026-11-26",
        now_utc="2026-11-26T05:00:00Z",
    )
    assert corrupt_store["evidence"]["state"] == "UNAVAILABLE"
    assert corrupt_store["evidence"]["reason"] == "CONTENTOPS_STORE_READ_FAILED"
    assert corrupt_store["evidence"]["read_attempts"] == 1
    assert corrupt_store["dispatches"] is None

    # 3. Interrupted query (deadline hit) classifies distinctly as CONTENTOPS_STORE_READ_TIMEOUT
    #    with zero retries and never fabricates empty lists.
    valid = tmp_path / "valid.sqlite3"
    _seed_store_with_history(valid, historical_dispatches=10, readbacks_per_dispatch=1)

    ticks = iter([100.0, 100.1, 100.2, 104.5, 104.6, 104.7, 104.8, 104.9, 105.0])
    last_t = [100.0]

    def fake_mono():
        try:
            last_t[0] = next(ticks)
        except StopIteration:
            last_t[0] += 0.1
        return last_t[0]

    def force_interrupt(stage: str):
        if stage == "dispatches_and_readbacks":
            exc = sqlite3.OperationalError("interrupted")
            exc.sqlite_errorcode = sqlite3.SQLITE_INTERRUPT
            raise exc

    timed_out, _ = summary_mod.read_cc153_store_hardened(
        valid,
        day="2026-11-26",
        now_utc="2026-11-26T05:00:00Z",
        timeout_seconds=3.0,
        mono_fn=fake_mono,
        stage_hook=force_interrupt,
    )
    assert timed_out["evidence"]["state"] == "UNAVAILABLE"
    assert timed_out["evidence"]["reason"] == "CONTENTOPS_STORE_READ_TIMEOUT"
    assert timed_out["evidence"]["failed_stage"] == "dispatches_and_readbacks"
    assert timed_out["evidence"]["read_attempts"] == 1
    assert timed_out["dispatches"] is None

    # 4. SQLITE_BUSY retries bounded times then fails closed as CONTENTOPS_STORE_BUSY_RETRY_EXHAUSTED.
    attempts_seen = []

    def always_busy(_stage: str):
        attempts_seen.append(1)
        exc = sqlite3.OperationalError("database is locked")
        exc.sqlite_errorcode = sqlite3.SQLITE_BUSY
        raise exc

    busy_store, _ = summary_mod.read_cc153_store_hardened(
        valid,
        day="2026-11-26",
        now_utc="2026-11-26T05:00:00Z",
        timeout_seconds=3.0,
        retry_delays=(0.0, 0.01, 0.01),
        sleep_fn=lambda _s: None,
        stage_hook=always_busy,
    )
    assert len(attempts_seen) == 3
    assert busy_store["evidence"]["state"] == "UNAVAILABLE"
    assert busy_store["evidence"]["reason"] == "CONTENTOPS_STORE_BUSY_RETRY_EXHAUSTED"
    assert busy_store["evidence"]["read_attempts"] == 3

    # 5. Real un-checkpointed WAL refuses immutable=1 (returns RO_STANDARD); once checkpointed
    #    to 0 bytes, immutable_snapshot=True cleanly selects RO_IMMUTABLE_ZERO_WAL.
    wal_test_db = tmp_path / "wal_check.sqlite3"
    wal_store = _seed_store_with_history(wal_test_db, historical_dispatches=1, readbacks_per_dispatch=1)
    # Keep a reader open while writing or verify real WAL bytes > 0 before truncate.
    writer = wal_store.get_connection()
    try:
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute(
            "INSERT INTO work_items(work_item_id,story_id,title,current_state,state_version,"
            "target_surface,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("wi-wal", "s-wal", "WAL test", "PUBLISHED", 1, "SUBSTACK",
             "2026-11-26T00:00:00+00:00", "2026-11-26T00:00:00+00:00"),
        )
        assert wal_test_db.with_name(wal_test_db.name + "-wal").stat().st_size > 0
        conn_std, mode_std = summary_mod._open_readonly_sqlite(
            wal_test_db, timeout_seconds=1.0, immutable_snapshot=True
        )
        conn_std.close()
        assert mode_std == "RO_STANDARD"
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    finally:
        writer.close()

    conn_imm, mode_imm = summary_mod._open_readonly_sqlite(
        wal_test_db, timeout_seconds=1.0, immutable_snapshot=True
    )
    conn_imm.close()
    assert mode_imm == "RO_IMMUTABLE_ZERO_WAL"


def test_full_summary_strips_private_texts_and_eliminates_raw_debug_enums(tmp_path):
    runtime = tmp_path / "runtime"
    control = runtime / "control"
    pause_dir = control / "pause-20261123"
    pause_dir.mkdir(parents=True)
    x_dir = runtime / "x_list_feed"
    x_dir.mkdir(parents=True)
    codex_exec = tmp_path / "codex-exec"
    codex_exec.mkdir(parents=True)
    priv_data = tmp_path / "privateapp-data"
    priv_data.mkdir(parents=True)

    store_path = runtime / "contentops_daily_app_v1.sqlite3"
    _seed_store_with_history(store_path, historical_dispatches=5, readbacks_per_dispatch=1, with_indexes=True)

    # Pause control state (paused with 3/3 publisher stops + all routes suspended).
    (pause_dir / "manifest.json").write_text(
        json.dumps({
            "paused_at_utc": "2026-11-23T04:56:22Z",
            "resume_at_utc": "2026-11-29T18:00:00Z",
            "cause": "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z",
            "tasks": [{"name": "CapitalChronicle-PlanStatusPosts-V1"}],
        }),
        encoding="utf-8",
    )
    (control / "suspended_routes.json").write_text(
        json.dumps({dest: "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z" for dest in summary_mod.ALL_DESTINATIONS}),
        encoding="utf-8",
    )
    for stop_name in summary_mod.DEFAULT_PUBLISHER_STOP_NAMES:
        (codex_exec / stop_name).write_text("Jim pause\n", encoding="utf-8")

    # Fast-header x_list_feed_v1.json with raw tweet rows that must NOT leak into summary.
    raw_x_header = json.dumps({
        "schema_version": "contentops.x_list_feed.v1",
        "generated_at_utc": "2026-11-26T04:59:45Z",
        "window_hours": 24.0,
        "row_count": 412,
        "newest_posted_utc": "2026-11-26T04:59:20Z",
        "newest_age_seconds": 25.0,
        "ingest_lag_seconds_median_last_hour": 14.5,
        "capture": {"state": "LISTENING"},
        "health": {
            "state": "OK",
            "stale": False,
            "last_good_capture_utc": "2026-11-26T04:59:40Z",
            "last_good_age_seconds": 5.0,
            "stale_after_seconds": 60.0,
            "failure_streak": 0,
            "p1": None,
            "market_hours": True,
        },
        "use": {"source_grant": "JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029"},
    })
    (x_dir / "x_list_feed_v1.json").write_text(
        raw_x_header[:-1]
        + ', "rows": [{"handle": "FirstSquawk", "text": "PRIVATE_X_TWEET_NEVER_DUMP_IN_SUMMARY_9921"}]}\n',
        encoding="utf-8",
    )

    # CC-807 / CC-817 attention map containing _private_texts + private keys + market odds.
    attention_path = tmp_path / "market_attention_map_live_v1.json"
    attention_path.write_text(
        json.dumps({
            "schema_version": "contentops.market_attention_map_public.v1",
            "as_of_utc": "2026-11-26T04:45:00Z",
            "_private_texts": [
                "CANARY_SECRET_BOOK_EXPOSURE_ALPHA_9981",
                "CANARY_INTERNAL_WIRE_RUMOR_7742",
            ],
            "open_positions": [{"symbol": "XAUUSD", "note": "CANARY_OPEN_BOOK_POSITION_4412"}],
            "prepared_responses": ["CANARY_PREPARED_RESPONSE_TRIGGER_8831"],
            "x_list_posts": ["CANARY_RAW_X_LIST_PROSE_5519"],
            "cadence_metadata": {"interval_minutes": 15},
            "themes": [
                {
                    "theme_id": "usdjpy_fed_boj_mof",
                    "name": "USD/JPY Fed-BoJ Divergence & MoF Watch",
                    "one_line": "Rates spread and intervention risk dominate yen trading.",
                    "status": "active",
                    "rank": 1,
                    "lead_market": "USDJPY",
                    "affected_markets": ["USDJPY", "XAUUSD", "US500"],
                    "updated_at_utc": "2026-11-26T04:45:00Z",
                    "market_lean_words": "Market leans modestly hawkish on BoJ",
                    "priced_in_words": "Partial tightening already reflected in 2Y JGBs",
                    "private_notes": "CANARY_THEME_PRIVATE_NOTE_3319",
                    "watch_items": [
                        {"kind": "x_list", "text": "CANARY_PRIVATE_WATCH_ITEM_6610"},
                    ],
                    "branches": [
                        {
                            "kind": "base_case",
                            "summary": "Yield differential keeps yen heavy below 156.",
                            "probability_source": "capital_chronicle",
                            "probability_pct": 55,
                            "invalidation": "BoJ surprise hike",
                        },
                        {
                            "kind": "alternative",
                            "summary": "Market-priced Kalshi odds branch",
                            "probability_source": "kalshi",
                            "probability_pct": 68,
                        },
                    ],
                    "decision_points": [
                        {
                            "id": "boj-dec",
                            "title": "BoJ Policy Decision",
                            "at_utc": "2026-12-18T03:00:00Z",
                            "status": "upcoming",
                        }
                    ],
                }
            ],
        }),
        encoding="utf-8",
    )

    # Desk state fixture deliberately loaded with every raw *_NOT_WRITTEN / VIEWS_UNSUPPORTED enum.
    desk_state_path = priv_data / "desk_state_v1.json"
    desk_state_path.write_text(
        json.dumps({
            "sections": {
                "queues": {
                    "data": {
                        "posts": [
                            {
                                "id": "plan-result-1",
                                "type": "Result",
                                "market": "USDJPY",
                                "title": "USD/JPY call review",
                                "status": "Posted",
                                "at": "2026-11-23T04:23:34Z",
                                "prior_day": True,
                                "qa_score": None,
                                "qa_cause": "IMAGE_QA_SCORE_NOT_WRITTEN",
                                "image": None,
                                "image_cause": "IMAGE_NOT_SUPPLIED",
                                "platforms": {"telegram": "posted", "discord": "posted"},
                                "href": "https://t.me/CapitalChronicle/232",
                                "dispatches": [{"dispatch_id": "d1", "destination": "telegram"}],
                            }
                        ],
                        "replies": [],
                        "reply_cause": "CC464_MOBILE_DRAFT_NOT_WRITTEN",
                        "last_pack_at": "2026-11-23T05:07:32Z",
                        "filter_causes": {
                            "NO_SIX_MARKET_OR_MACRO_TOPIC": 29,
                            "TARGET_OVER_15_MINUTES_AT_SEND": 3092,
                        },
                        "last_post_at": "2026-11-23T04:23:34Z",
                    }
                },
                "gold_note": {
                    "data": {
                        "state": "READ",
                        "item": "CC-406",
                        "date": "2026-11-20",
                        "text": "Vang chiu suc ep tu loi suat thuc\n\nDong USD tang nhe truoc gio mo cua My.",
                        "source": {"path": r"A:\Capital Chronicle\gold-notes\2026-11-20.md"},
                        "chart": {"path": r"A:\Capital Chronicle\gold-notes\2026-11-20.png"},
                    }
                },
                "score": {
                    "data": {
                        "calls_ledger": {
                            "total": 113,
                            "with_result_record": 97,
                            "today": 0,
                            "at_utc": "2026-11-25T18:52:02Z",
                        },
                        "audience": {
                            "updated_at": "2026-11-23T03:08:24Z",
                            "rows": [
                                {"type": "Call", "platform": "telegram", "median_views": 420, "n": 5, "cause": None},
                                {"type": "Call", "platform": "discord", "median_views": None, "n": 0, "cause": "VIEWS_UNSUPPORTED"},
                            ],
                        },
                    }
                },
            }
        }),
        encoding="utf-8",
    )

    # desk.js fixture testing cc689-weekly-* wrap categorization & REVIEWED_PACKAGE_NOT_FOUND hiding.
    desk_js_path = priv_data / "desk.js"
    desk_js_path.write_text(
        "window.__CC_PRIVATE__ = "
        + json.dumps({
            "wraps": {
                "pieces": [
                    {
                        "url": "https://capitalchronicle.substack.com/p/weekend-market-wrap-november-22-2026",
                        "slug": "weekend-market-wrap-november-22-2026",
                        "title": "Weekend market wrap november 22 2026",
                        "kind": "ARTICLE",
                        "work_item": "cc689-weekly-2026-11-22",
                        "published_at_utc": "2026-11-22T13:03:22Z",
                        "in_record": False,
                        "package": None,
                        "package_gap": "REVIEWED_PACKAGE_NOT_FOUND",
                        "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/weekend-market-wrap-november-22-2026"}],
                        "scenario_analysis": [{"name": "Base"}],
                    }
                ]
            }
        })
        + ";\n",
        encoding="utf-8",
    )

    now = datetime(2026, 11, 26, 5, 0, tzinfo=timezone.utc)
    result = summary_mod.build_privateapp_newsroom_summary(
        runtime_root=runtime,
        codex_exec_dir=codex_exec,
        desk_state_path=desk_state_path,
        desk_js_path=desk_js_path,
        attention_map_live_path=attention_path,
        now=now,
        x_keepalive_status_fn=lambda: {
            "state": "RUNNING",
            "runner_alive": True,
            "stop_present": False,
            "feed": {"age_seconds": 15.0, "health_state": "OK"},
        },
        neo_probe_fn=lambda: {
            "state": "HEALTHY",
            "cdp": {"cdp_alive": True, "cdp_port": 9110},
            "mcp": {"mcp_alive": True, "server_version": "0.0.88"},
            "process_alive": True,
            "process_count": 12,
            "process_probe_ok": True,
            "ports": {"cdp_port": 9110, "mcp_port": 9010, "server_port": 9210, "browseros_version": "0.52.0.0"},
        },
    )

    # 1. Strictly private-only metadata.
    assert result["schema_version"] == "ContentOpsNewsroomPrivateSummaryV1"
    assert result["private_only"] is True
    assert result["read_only"] is True
    assert result["public_export"] is False
    assert result["robots"] == "noindex,nofollow"

    # 2. Zero _private_texts key and ZERO private canary echoes anywhere in JSON!
    blob = json.dumps(result, ensure_ascii=False)
    assert "_private_texts" not in blob
    for canary in (
        "CANARY_SECRET_BOOK_EXPOSURE_ALPHA_9981",
        "CANARY_INTERNAL_WIRE_RUMOR_7742",
        "CANARY_OPEN_BOOK_POSITION_4412",
        "CANARY_PREPARED_RESPONSE_TRIGGER_8831",
        "CANARY_RAW_X_LIST_PROSE_5519",
        "CANARY_THEME_PRIVATE_NOTE_3319",
        "CANARY_PRIVATE_WATCH_ITEM_6610",
        "PRIVATE_X_TWEET_NEVER_DUMP_IN_SUMMARY_9921",
    ):
        assert canary not in blob

    # 3. Market-implied Kalshi probability stripped; own Capital Chronicle estimate retained.
    theme = result["attention_map"]["top_themes"][0]
    assert theme["branches"][0]["probability_pct"] == 55.0
    assert theme["branches"][1]["probability_pct"] is None
    assert theme["branches"][1]["probability_label"] is None

    # 4. Zero raw debug enums outside diagnostics; forensic values preserved inside diagnostics.
    summary_mod.assert_clean_primary_display(result)
    post = result["publishing_queue"]["posts"]["items"][0]
    assert post["qa_score"] is None
    assert post["image_pill"]["label"] == "Text Only"
    assert post["diagnostics"]["qa_cause"] == "IMAGE_QA_SCORE_NOT_WRITTEN"
    assert post["diagnostics"]["image_cause"] == "IMAGE_NOT_SUPPLIED"

    # 5. Wrap cc689-weekly-* classification + reply filter summary + Discord VIEWS_UNSUPPORTED display.
    wraps = result["publishing_queue"]["wraps"]
    assert wraps["counts"]["wraps_and_digests"] == 1
    assert wraps["recent"][0]["link_only"] is True
    assert wraps["recent"][0]["diagnostics"]["package_gap"] == "REVIEWED_PACKAGE_NOT_FOUND"
    replies = result["publishing_queue"]["replies"]
    assert replies["filtered_summary"] == "3,121 filtered (29 off-topic · 3,092 older than 15m)"
    assert replies["diagnostics"]["filter_causes"]["TARGET_OVER_15_MINUTES_AT_SEND"] == 3092
    discord_row = next(r for r in result["audience_and_calls"]["audience_7d"]["rows"] if r["platform"] == "discord")
    assert discord_row["display"] == "—"
    assert discord_row["unsupported"] is True
    assert discord_row["diagnostics"]["raw_cause"] == "VIEWS_UNSUPPORTED"

    # 6. Pause state & CC-711 keepalive/Neo health reflected cleanly.
    assert result["publisher_control"]["state"] == "paused"
    assert result["publisher_control"]["pill"]["label"] == "Publishing Paused"
    assert result["publisher_control"]["publisher_lanes"]["stopped_count"] == 3
    assert result["x_list_feed"]["pill"]["label"] == "Live"
    assert result["x_list_feed"]["row_count"] == 412
    assert result["keepalive_and_neo"]["browseros_neo"]["pill"]["label"] == "Healthy"
    assert result["status_strip"]["cc153_store"]["connected"] is True

    # 7. Writer enforces private-only path guard and strict CR=0, BOM=False.
    out_file = tmp_path / "preview" / "data" / "contentops-newsroom-summary.private.json"
    written = summary_mod.write_privateapp_newsroom_summary(out_file, result)
    raw_bytes = written.read_bytes()
    assert raw_bytes.count(b"\r") == 0
    assert not raw_bytes.startswith(b"\xef\xbb\xbf")
    assert json.loads(raw_bytes.decode("utf-8"))["schema_version"] == "ContentOpsNewsroomPrivateSummaryV1"


def test_publisher_control_states_resumed_partial_and_kill_switch(tmp_path):
    now = datetime(2026, 11, 30, 2, 0, tzinfo=timezone.utc)

    # 1. Resumed (restored.json written, 0 stop files, empty suspended_routes).
    ctrl1 = tmp_path / "c1"
    p1 = ctrl1 / "pause-20261123"
    p1.mkdir(parents=True)
    (p1 / "manifest.json").write_text(json.dumps({"paused_at_utc": "2026-11-23T04:56:22Z"}), encoding="utf-8")
    (p1 / "restored.json").write_text(json.dumps({"ended_at_utc": "2026-11-29T18:05:00Z"}), encoding="utf-8")
    (ctrl1 / "suspended_routes.json").write_text("{}", encoding="utf-8")
    res1 = summary_mod.read_publisher_pause_control(control_dir=ctrl1, codex_exec_dir=tmp_path / "e1", now_dt=now)
    assert res1["state"] == "live"
    assert res1["is_paused"] is False
    assert res1["pill"]["label"] == "Live"

    # 2. Single-route restriction (Decision 121): NOT global kill switch, only youtube suspended.
    ctrl2 = tmp_path / "c2"
    ctrl2.mkdir(parents=True)
    (ctrl2 / "suspended_routes.json").write_text(
        json.dumps({"youtube": "YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED"}),
        encoding="utf-8",
    )
    res2 = summary_mod.read_publisher_pause_control(control_dir=ctrl2, codex_exec_dir=tmp_path / "e2", now_dt=now)
    assert res2["state"] == "partial_suspension"
    assert res2["kill_switch_active"] is False
    assert res2["suspended_count"] == 1
    yt = next(d for d in res2["destinations"] if d["destination"] == "youtube")
    tg = next(d for d in res2["destinations"] if d["destination"] == "telegram")
    assert yt["status"] == "suspended" and yt["pill"]["label"] == "Route Suspended"
    assert tg["status"] == "active" and tg["pill"]["label"] == "Active"

    # 3. KILL_SWITCH file present -> rose Kill Switch Active.
    ctrl3 = tmp_path / "c3"
    ctrl3.mkdir(parents=True)
    (ctrl3 / "KILL_SWITCH").write_text("ACTIVE\n", encoding="utf-8")
    res3 = summary_mod.read_publisher_pause_control(control_dir=ctrl3, codex_exec_dir=tmp_path / "e3", now_dt=now)
    assert res3["state"] == "kill_switch"
    assert res3["kill_switch_active"] is True
    assert res3["pill"]["tone"] == "rose"


def test_leak_and_display_guards_fail_closed_and_refuse_public_paths(tmp_path):
    # Private key guard.
    with pytest.raises(summary_mod.PrivateLeakError):
        summary_mod.assert_no_private_text_leaks({"ok": True, "_private_texts": ["secret"]})

    # Canary echo guard (even inside diagnostics).
    with pytest.raises(summary_mod.PrivateLeakError):
        summary_mod.assert_no_private_text_leaks(
            {"diagnostics": {"note": "leaked CANARY_SECRET_LINE_9999 here"}},
            forbidden_texts=["CANARY_SECRET_LINE_9999"],
        )

    # Display hygiene guard catches raw *_NOT_WRITTEN outside diagnostics, allows inside diagnostics.
    summary_mod.assert_clean_primary_display({
        "pill": {"label": "Pending", "tone": "neutral"},
        "diagnostics": {"raw_cause": "CUSTOM_METRIC_NOT_WRITTEN"},
    })
    with pytest.raises(summary_mod.DisplayHygieneError):
        summary_mod.assert_clean_primary_display({
            "pill": {"label": "IMAGE_QA_SCORE_NOT_WRITTEN", "tone": "neutral"},
        })

    # Public output path guards refuse ui/public, ui/dist, and *.public.json.
    valid_payload = {
        "schema_version": summary_mod.SCHEMA_VERSION,
        "private_only": True,
        "public_export": False,
        "pill": {"label": "Live", "tone": "emerald"},
    }
    with pytest.raises(summary_mod.PrivateLeakError):
        summary_mod.write_privateapp_newsroom_summary(tmp_path / "ui" / "public" / "newsroom.private.json", valid_payload)
    with pytest.raises(summary_mod.PrivateLeakError):
        summary_mod.write_privateapp_newsroom_summary(tmp_path / "newsroom.public.json", valid_payload)


def test_cc153_hardened_reader_handles_2500_same_day_readbacks_and_nested_verified_schema(tmp_path):
    """Regression for C-H1 (>2,000 raw same-day readbacks) and C-H2 (nested readback.verified=True)."""
    db_path = tmp_path / "active_day.sqlite3"
    store = _seed_store_with_history(db_path, historical_dispatches=5, readbacks_per_dispatch=1, with_indexes=False)

    conn = store.get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        # Seed a real production-style dispatch on 2026-11-26 plus an earlier-day dispatch
        # verified via nested {"destination": ..., "dispatch_id": ..., "readback": {"verified": True}}.
        conn.execute(
            "INSERT INTO platform_dispatches(dispatch_id,message_id,platform,status,dispatched_at,public_object_url) "
            "VALUES (?,?,?,?,?,?)",
            (
                "disp-nested-today",
                "msg-today",
                "telegram",
                "DISPATCH_CONFIRMED",
                "2026-11-26T02:10:00+00:00",
                "https://t.me/CapitalChronicle/901",
            ),
        )
        conn.execute(
            "INSERT INTO platform_dispatches(dispatch_id,message_id,platform,status,dispatched_at,public_object_url) "
            "VALUES (?,?,?,?,?,?)",
            (
                "disp-nested-earlier",
                "msg-hist",
                "discord",
                "DISPATCH_CONFIRMED",
                "2026-11-21T08:00:00+00:00",
                "https://discord.com/channels/1/2/3",
            ),
        )
        # Earlier-day nested verified readback (tests Step 4 earliest-timestamp resolution on nested schema).
        conn.execute(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            (
                "rb-nested-earlier-first",
                "disp-nested-earlier",
                json.dumps({
                    "destination": "discord",
                    "dispatch_id": "disp-nested-earlier",
                    "readback": {"verified": True, "url": "https://discord.com/channels/1/2/3"},
                }),
                "2026-11-21T08:02:00+00:00",
            ),
        )
        # Same-day nested verified readback for earlier-day dispatch (causes it to appear on 2026-11-26).
        conn.execute(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            (
                "rb-nested-earlier-recheck",
                "disp-nested-earlier",
                json.dumps({
                    "destination": "discord",
                    "dispatch_id": "disp-nested-earlier",
                    "readback": {"verified": True, "url": "https://discord.com/channels/1/2/3"},
                }),
                "2026-11-26T03:00:00+00:00",
            ),
        )
        # Seed 2,600 raw readbacks INSIDE the single 24h target production day (> MAX_CC153_ROWS=2000).
        base_dt = datetime(2026, 11, 25, 19, 5, tzinfo=timezone.utc)  # 2026-11-26 02:05 GMT+7
        rb_bulk = []
        for idx in range(2600):
            ts = (base_dt + timedelta(seconds=idx * 15)).isoformat()
            is_first_verified = idx == 1200
            payload = (
                {
                    "destination": "telegram",
                    "dispatch_id": "disp-nested-today",
                    "readback": {"verified": True, "url": "https://t.me/CapitalChronicle/901"},
                }
                if is_first_verified
                else {
                    "destination": "telegram",
                    "dispatch_id": "disp-nested-today",
                    "readback": {"verified": False, "probe": idx},
                }
            )
            rb_bulk.append((f"rb-heavy-day-{idx:04d}", "disp-nested-today", json.dumps(payload), ts))
        conn.executemany(
            "INSERT INTO readbacks(readback_id,dispatch_id,readback_data,read_at) VALUES (?,?,?,?)",
            rb_bulk,
        )
        conn.execute("COMMIT")
    finally:
        conn.close()

    store_res, _ = summary_mod.read_cc153_store_hardened(
        db_path,
        day="2026-11-26",
        now_utc="2026-11-26T10:00:00Z",
        timeout_seconds=3.0,
    )
    assert store_res["evidence"]["state"] == "AVAILABLE"
    assert store_res["evidence"]["reason"] is None
    by_id = {d["dispatch_id"]: d for d in store_res["dispatches"]}
    assert "disp-nested-today" in by_id
    assert "disp-nested-earlier" in by_id
    expected_today_ts = (base_dt + timedelta(seconds=1200 * 15)).isoformat()
    assert by_id["disp-nested-today"]["verified_readback_at_utc"] == expected_today_ts
    assert by_id["disp-nested-earlier"]["verified_readback_at_utc"] == "2026-11-21T08:02:00+00:00"


def test_attention_map_odds_fail_closed_on_aliases_and_missing_source():
    """Regression for C-M1: odds_source/source_kind aliases and unlabelled probabilities fail closed."""
    projected = summary_mod._project_attention_theme_allowlist({
        "theme_id": "rates_test",
        "name": "Rates Test",
        "status": "active",
        "rank": 1,
        "branches": [
            {"kind": "base_case", "summary": "Odds alias kalshi", "odds_source": "kalshi", "probability_pct": 72},
            {"kind": "alternative", "summary": "Source kind fedwatch", "source_kind": "fedwatch", "probability_pct": 85},
            {"kind": "bull_case", "summary": "Unlabelled prob", "probability_pct": 28},
            {
                "kind": "bear_case",
                "summary": "Already projected CC estimate",
                "probability_pct": 55,
                "probability_label": "Capital Chronicle estimate",
            },
        ],
    })
    by_summary = {b["summary"]: (b["probability_pct"], b["probability_label"]) for b in projected["branches"]}
    assert by_summary["Odds alias kalshi"] == (None, None)
    assert by_summary["Source kind fedwatch"] == (None, None)
    assert by_summary["Unlabelled prob"] == (None, None)
    assert by_summary["Already projected CC estimate"] == (55.0, "55% (Capital Chronicle estimate)")

    # Explicit own source + conflicting market odds_source must STILL fail closed!
    conflict = summary_mod._project_attention_theme_allowlist({
        "theme_id": "conflict_test",
        "name": "Conflict Test",
        "branches": [
            {
                "kind": "base_case",
                "summary": "Conflicting sources",
                "probability_source": "capital_chronicle",
                "odds_source": "kalshi",
                "probability_pct": 72,
            },
            {
                "kind": "alternative",
                "summary": "Clean own estimate",
                "probability_source": "capital_chronicle",
                "probability_pct": 60,
            },
        ],
    })
    by_c = {b["summary"]: (b["probability_pct"], b["probability_label"]) for b in conflict["branches"]}
    assert by_c["Conflicting sources"] == (None, None)
    assert by_c["Clean own estimate"] == (60.0, "60% (Capital Chronicle estimate)")
