"""Held minute prices reach the real chart/publication consumers; no live stores."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sqlite3

import pytest

from live_contentops import chart_price_reference_v1 as prices
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
MARKETS = tuple(tv.SYMBOLS)


@pytest.fixture
def sources(tmp_path, monkeypatch):
    export, bars = tmp_path / "status.json", tmp_path / "bars.sqlite3"
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", export)
    monkeypatch.setattr(prices, "BAR_STORE", bars)
    monkeypatch.setattr(contract, "QUOTE_ROOT", tmp_path / "captures")
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    with closing(sqlite3.connect(bars)) as db, db:
        db.executescript("""
            CREATE TABLE history_sources(source_id TEXT PRIMARY KEY, source_sha256 TEXT,
                path TEXT, market TEXT, timeframe TEXT, series_id TEXT, known_epoch REAL, metadata_json TEXT);
            CREATE TABLE history_bars(source_id TEXT, open_epoch INTEGER, end_epoch INTEGER,
                session_date TEXT, open REAL, high REAL, low REAL, close REAL,
                PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE history_invalid(source_id TEXT, open_epoch INTEGER, reason TEXT);
        """)
    return export, bars


def export_price(path, market="EURUSD", price=100, at=NOW, **fields):
    row = {"asset_id": market, "last_price": price, "last_price_at_utc": at.isoformat(), **fields}
    body = {"schema": "CapitalChroniclePlanStatusV1", "generated_at_utc": NOW.isoformat(), "plans": [row]}
    body["content_hash"] = sha256(prices._canonical(body)).hexdigest()
    path.write_text(json.dumps(body), encoding="utf-8")


def bar(path, market="EURUSD", price=100, end=NOW, known=NOW, sid="one", **metadata):
    meta = {"source_instrument": market, "contract_id": "EXNESS_DEMO:" + market,
            "account": "PRIVATE_TEST_VALUE", **metadata}
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
            (sid, "b" * 64, "held-capture.json", market, "M1", "NATIVE_BROKER",
             known.timestamp(), json.dumps(meta)))
        db.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
            (sid, int(end.timestamp()) - 60, int(end.timestamp()), end.date().isoformat(),
             price, price + 1, price - 1, price))


def snap(market="EURUSD", price=100, at=NOW):
    return {"tv_symbol": tv.SYMBOLS[market], "sha256": "c" * 64,
            "page_title": "TICKER " + str(price), "captured_at_utc": at.isoformat()}


@pytest.mark.parametrize("market", MARKETS)
def test_minute_export_price_is_compared_for_each_market(sources, market):
    export_price(sources[0], market, at=NOW - timedelta(seconds=30))
    bound = contract.bind_scale(market, snap(market))
    check = contract.validate_scale(market, bound)
    assert check["difference_pct"] == 0
    assert check["quote"]["source_kind"] == "PLAN_STATUS_EXPORT"
    assert check["quote"]["age_seconds"] == 30
    assert check["quote"]["source_sha256"] == sha256(sources[0].read_bytes()).hexdigest()


@pytest.mark.parametrize("market", MARKETS)
def test_m1_store_fills_the_export_gap_for_each_market(sources, market):
    export_price(sources[0], market, last_price=None)
    bar(sources[1], market, end=NOW - timedelta(minutes=1))
    check = contract.bind_scale(market, snap(market))["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE" and check["difference_pct"] == 0
    quote = check["quote"]
    assert quote["source_kind"] == "BAR_STORE_M1_CLOSE" and quote["age_seconds"] == 60
    assert quote["price_basis"] == "plan_bar_close" and quote["source_record_sha256"]
    assert quote["source_attempts"][0]["cause"] == "PLAN_STATUS_LAST_PRICE_NOT_EXPORTED"
    assert "PRIVATE_TEST_VALUE" not in json.dumps(check)


def test_bar_store_price_reaches_real_coordinator_and_existing_image_register(sources, tmp_path):
    from test_publication_image_contract_cc463 import message_with, snapshot
    bar(sources[1], "US500", 7549.51)
    taken = contract.bind_scale("US500", snapshot())
    asset = {**tv.snapshot_asset("US500", "S&P 500", taken, tmp_path),
             "article_inclusion": True, "canonical_article_media": True}
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED" and runtime.publish_calls == ["substack"], result
    from live_contentops.article_publication_quality_v1 import image_register
    held = image_register(coordinator).records()[-1]["images"][0]["price_scale_check"]
    assert held["quote"]["source_kind"] == "BAR_STORE_M1_CLOSE"


def test_measured_mismatch_is_not_replaced_with_a_more_convenient_source(sources):
    export_price(sources[0], price=90)
    bar(sources[1], price=100)
    with pytest.raises(contract.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        contract.bind_scale("EURUSD", snap())


@pytest.mark.parametrize("problem", ["stale", "forming", "future_known", "proxy", "invalid"])
def test_unusable_bar_has_a_cause_and_never_refuses_a_chart(sources, problem):
    end = NOW - timedelta(minutes=3) if problem == "stale" else NOW
    known = NOW
    if problem == "forming":
        end += timedelta(minutes=1)
    if problem == "future_known":
        known += timedelta(seconds=1)
    bar(sources[1], end=end, known=known,
        **({"source_instrument": "6E", "contract_id": "CME:6E"} if problem == "proxy" else {}))
    if problem == "invalid":
        with closing(sqlite3.connect(sources[1])) as db, db:
            db.execute("INSERT INTO history_invalid VALUES(?,?,?)", ("one", int(end.timestamp()) - 60, "BAD"))
    bound = contract.bind_scale("EURUSD", snap())
    check = contract.validate_scale("EURUSD", bound)
    assert check["comparison_basis"] == "NOT_COMPARED" and check["level_offset"] == 0
    assert len(check["quote_source_attempts"]) == 3
    if problem == "stale":
        assert check["quote_source_attempts"][1]["cause"] == "CHART_REFERENCE_STALE"
        assert check["quote_source_attempts"][1]["age_seconds"] == 180


def test_fallback_uses_an_available_saved_main_tick(sources, monkeypatch):
    def saved(market, captured, **kwargs):
        return {"market": market, "instrument": market, "price": 100, "quoted_at_utc": NOW.isoformat(),
                "known_at_utc": NOW.isoformat(), "source_path": "tick.json", "source_sha256": "a" * 64}
    monkeypatch.setattr(contract, "saved_main_quote", saved)
    check = contract.bind_scale("EURUSD", snap())["price_scale_check"]
    assert check["quote"]["source_kind"] == "MAIN_SAVED_TICK"


@pytest.mark.parametrize("fields", [
    {"last_price_at_utc": None, "checked_at_utc": NOW.isoformat()},
    {"last_quote": {"instrument": "6E", "price": 100, "quoted_at_utc": NOW.isoformat()}},
    {"last_quote": {"instrument": "EURUSD", "price": 100, "quoted_at_utc": NOW.isoformat(),
                    "known_at_utc": (NOW - timedelta(seconds=1)).isoformat()}},
])
def test_export_check_time_or_another_contract_cannot_certify_a_price(sources, fields):
    export_price(sources[0], **fields)
    assert contract.bind_scale("EURUSD", snap())["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"


def test_export_hash_failure_uses_bar_and_reads_do_not_mutate_store(sources):
    export_price(sources[0])
    sources[0].write_bytes(sources[0].read_bytes().replace(b'100', b'101'))
    bar(sources[1])
    before = sha256(sources[1].read_bytes()).hexdigest()
    quote = prices.saved_chart_quote("EURUSD", NOW)
    assert quote["source_kind"] == "BAR_STORE_M1_CLOSE"
    assert quote["source_attempts"][0]["cause"] == "PLAN_STATUS_PRICE_HASH_INVALID"
    assert sha256(sources[1].read_bytes()).hexdigest() == before


def test_closed_market_uses_a_close_bar_and_records_both_ages(sources):
    close = NOW.replace(hour=21)
    capture = NOW + timedelta(hours=13)
    bar(sources[1], "US500", end=close, known=close)
    bar(sources[1], "US500", price=120, end=capture, known=capture, sid="overnight")
    check = contract.bind_scale("US500", snap("US500", at=capture))["price_scale_check"]
    assert check["comparison_basis"] == "LAST_CLOSE" and check["difference_pct"] == 0
    assert check["quote"]["age_seconds"] == 0 and check["quote"]["capture_age_seconds"] == 8 * 3600


def test_a_historical_issued_check_still_validates_without_new_fields(sources):
    old = snap()
    old["price_scale_check"] = contract.not_compared("EURUSD", old, contract.QUOTE_ABSENT[0])
    assert "quote_source_attempts" not in contract.validate_scale("EURUSD", old)


def test_missing_store_is_not_created(sources):
    sources[1].unlink()
    assert contract.bind_scale("EURUSD", snap())["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"
    assert not sources[1].exists()
