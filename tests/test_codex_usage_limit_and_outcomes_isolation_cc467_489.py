"""Hermetic tests for TradingView OUTCOMES test isolation (CC-489) and Codex usage-limit surfacing (CC-467/CC-801)."""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from live_contentops import chart_price_reference_v1 as prices
from live_contentops import heavy_news_quotes_v1 as quotes
from live_contentops import light_model_caller_v1 as light_caller
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import x_reply_bot_v1 as bot
from test_tradingview_snapshot_cc314 import tradingview_worker


USAGE_LIMIT_STDOUT = (
    '{"type":"thread.started","thread_id":"01a206c6-4674-7652-8cbc-1a3cb21abe6c"}\n'
    '{"type":"turn.started"}\n'
    '{"type":"error","message":"You\u2019ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), '
    'visit https://chatgpt.com/settings/usage to purchase more credits or try again at 3:39 PM."}\n'
    '{"type":"turn.failed","error":{"message":"You\u2019ve hit your usage limit. Upgrade to Pro '
    '(https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage to purchase more credits '
    'or try again at 3:39 PM."}}\n'
).encode("utf-8")


def test_conftest_isolates_tradingview_outcomes_from_live_runtime(tmp_path):
    """Autouse conftest fixture redirects tv.OUTCOMES into tmp_path so unpatched tests never touch A:\\Runtime."""
    assert "Runtime" not in str(tv.OUTCOMES)
    assert tv.OUTCOMES.name == "tradingview-snapshot-outcomes.jsonl"
    media = tmp_path / "media"
    tv.capture("US500", "240", media, worker=tradingview_worker([]), quote_provider=lambda _m, _at: None)
    assert tv.OUTCOMES.is_file()
    rows = [json.loads(ln) for ln in tv.OUTCOMES.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(rows) == 1 and rows[0]["market"] == "US500"


def test_x_reply_text_call_surfaces_codex_usage_limit_from_jsonl_stdout(tmp_path):
    """Exact 23 Nov CC-467 failure (stdout JSONL usage limit, empty stderr) surfaces CODEX_USAGE_LIMIT."""
    def fake_codex(args, *, cwd, timeout, input):
        return subprocess.CompletedProcess(args, 1, USAGE_LIMIT_STDOUT, b"")

    out = tmp_path / "filter"
    with pytest.raises(ValueError, match="^CODEX_USAGE_LIMIT$"):
        bot._text_call(
            "Select heavy news.",
            root=out,
            writer=True,
            runner=fake_codex,
            model_config=("gpt-6-luna", "max"),
            timeout=35,
        )
    saved = json.loads((out / "call.json").read_text(encoding="utf-8"))
    assert saved["status"] == "FAILED"
    assert saved["cause"] == "CODEX_USAGE_LIMIT"
    assert saved["returncode"] == 1
    assert saved["observed_session_id"] == "01a206c6-4674-7652-8cbc-1a3cb21abe6c"
    assert "try again at 3:39 PM" in saved["observed_error_message"]


def test_light_model_caller_surfaces_codex_usage_limit_and_preserves_non_quota_exit(tmp_path):
    """call_light() surfaces CODEX_USAGE_LIMIT on quota exhaustion and keeps CODEX_EXIT_1 on non-quota errors."""
    def quota_runner(args, *, cwd, timeout, input):
        return subprocess.CompletedProcess(args, 1, USAGE_LIMIT_STDOUT, b"")

    answer, record = light_caller.call_light(
        "Return JSON.",
        root=tmp_path / "quota",
        timeout_cause="T",
        empty_cause="E",
        runner=quota_runner,
        callers=("codex",),
    )
    assert answer == b""
    assert record["status"] == "FAILED"
    assert record["cause"] == "CODEX_USAGE_LIMIT"
    assert "usage limit" in record["observed_error_message"].lower()
    assert record["attempts"][0]["cause"] == "CODEX_USAGE_LIMIT"

    def plain_error_runner(args, *, cwd, timeout, input):
        out = b'{"type":"turn.failed","error":{"message":"backend transport reset"}}\n'
        return subprocess.CompletedProcess(args, 1, out, b"")

    _, record2 = light_caller.call_light(
        "Return JSON.",
        root=tmp_path / "other",
        timeout_cause="T",
        empty_cause="E",
        runner=plain_error_runner,
        callers=("codex",),
    )
    assert record2["cause"] == "CODEX_EXIT_1"
    assert record2["observed_error_message"] == "backend transport reset"


def test_codex_failure_cause_handles_stderr_quota_fallback():
    rec = {}
    cause = light_caller.codex_failure_cause(b"", 1, rec, stderr=b"Error: rate limit reached")
    assert cause == "CODEX_USAGE_LIMIT"
    assert rec["observed_error_message"] == "Error: rate limit reached"


def test_cc467_filter_policy_and_cc489_no_futures_proxy_invariants_preserved(tmp_path):
    """Keep authorized Luna screening policy (CC-467) and strict no-futures-proxy bar guard (CC-489)."""
    assert quotes.ROLES[0][:3] == ("filter", "gpt-6-luna", "max")

    db_path = tmp_path / "bars.sqlite3"
    now = datetime(2026, 11, 24, 15, 0, tzinfo=timezone.utc)
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript("""
            CREATE TABLE history_sources(source_id TEXT PRIMARY KEY, source_sha256 TEXT,
                path TEXT, market TEXT, timeframe TEXT, series_id TEXT, known_epoch REAL, metadata_json TEXT);
            CREATE TABLE history_bars(source_id TEXT, open_epoch INTEGER, end_epoch INTEGER,
                session_date TEXT, open REAL, high REAL, low REAL, close REAL,
                PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE history_invalid(source_id TEXT, open_epoch INTEGER, reason TEXT);
        """)
        db.execute(
            "INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
            (
                "yf-nq", "a" * 64, "nq.json", "USTEC", "M1", "YAHOO_FINANCE:NQ=F",
                now.timestamp(), json.dumps({"source_instrument": "NQ=F", "contract_id": "YAHOO_FINANCE:NQ=F"}),
            ),
        )
        db.execute(
            "INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
            ("yf-nq", int(now.timestamp()) - 60, int(now.timestamp()), "2026-11-24", 26200, 26210, 26190, 26205),
        )
    with pytest.raises(Exception, match="BAR_STORE_EXACT_M1_PRICE_UNAVAILABLE"):
        prices.bar_store_quote("USTEC", now, db_path)
