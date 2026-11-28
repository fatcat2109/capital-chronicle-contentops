"""CC-509 / CC-024: real consumers use held local bars / US Treasury rates; zero Yahoo HTTP."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from urllib.error import HTTPError

import pytest

from live_contentops import public_market_quote_v1 as quotes
from live_contentops import chart_price_reference_v1 as prices
from live_contentops import publication_image_contract_v1 as image
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import x_reply_fact_sources_v1 as facts
from live_contentops import x_reply_fact_policy_v1 as policy
from live_contentops import x_reply_pack_v1 as packs
from live_contentops import x_reply_bot_v1 as bot
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)


def _init_bars_db(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS sources(
                sha256 TEXT PRIMARY KEY, path TEXT, capture_hash TEXT, known_at_utc TEXT, imported_at_utc TEXT);
            CREATE TABLE IF NOT EXISTS bars(
                symbol TEXT NOT NULL, open_epoch INTEGER NOT NULL,
                open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
                known_epoch REAL NOT NULL, source_sha256 TEXT NOT NULL,
                price_basis TEXT NOT NULL, contract_id TEXT NOT NULL,
                series_id TEXT NOT NULL DEFAULT 'NATIVE_BROKER',
                PRIMARY KEY(symbol, open_epoch, source_sha256));
            CREATE TABLE IF NOT EXISTS invalid_bars(
                source_sha256 TEXT NOT NULL, symbol TEXT NOT NULL, open_epoch INTEGER NOT NULL, reason TEXT NOT NULL,
                PRIMARY KEY(source_sha256, symbol, open_epoch));
            CREATE TABLE IF NOT EXISTS history_sources(
                source_id TEXT PRIMARY KEY, source_sha256 TEXT, path TEXT, market TEXT,
                timeframe TEXT, series_id TEXT, known_epoch REAL, metadata_json TEXT);
            CREATE TABLE IF NOT EXISTS history_bars(
                source_id TEXT, open_epoch INTEGER, end_epoch INTEGER, session_date TEXT,
                open REAL, high REAL, low REAL, close REAL, PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE IF NOT EXISTS history_points(
                source_id TEXT, open_epoch INTEGER, end_epoch INTEGER, session_date TEXT, value REAL,
                PRIMARY KEY(source_id, open_epoch));
            CREATE TABLE IF NOT EXISTS history_invalid(
                source_id TEXT, open_epoch INTEGER, reason TEXT, PRIMARY KEY(source_id, open_epoch));
        """)


def _init_rates_db(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS observations(
                family TEXT NOT NULL, series TEXT NOT NULL, observation_date TEXT NOT NULL,
                known_at TEXT NOT NULL, version TEXT PRIMARY KEY, payload TEXT NOT NULL)
        """)


def seed_bar(db_path: Path, market: str, *, at: datetime = NOW, value: float = 92.03,
             prior: float = 92.76, known: datetime | None = None, series_id: str = "NATIVE_BROKER",
             src_sha: str | None = None) -> None:
    _init_bars_db(db_path)
    db_sym = quotes.SYMBOLS[market][1]
    known = known or at
    end_ep = int(at.timestamp())
    open_ep = end_ep - 900
    prior_day = (at - timedelta(days=1)).astimezone(quotes.ET).date().isoformat()
    sha = src_sha or ("a" * 60 + f"{abs(hash((db_sym, open_ep, value))) % 10000:04d}")
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute(
            "INSERT OR REPLACE INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (db_sym, open_ep, value, value + 0.5, max(0.01, value - 0.5), value,
             known.timestamp(), sha, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
             f"EXNESS_DEMO:{db_sym}", series_id),
        )
        if prior is not None:
            sid = f"d1-{db_sym}"
            prior_end = int((at - timedelta(days=1)).timestamp())
            db.execute(
                "INSERT OR REPLACE INTO history_sources VALUES(?,?,?,?,?,?,?,?)",
                (sid, "d" * 64, f"{db_sym}.json", db_sym, "D1", "NATIVE_DAILY_ROUTE",
                 known.timestamp(), json.dumps({"provider": "NATIVE_DAILY_ROUTE"})),
            )
            db.execute(
                "INSERT OR REPLACE INTO history_bars VALUES(?,?,?,?,?,?,?,?)",
                (sid, prior_end - 86400, prior_end, prior_day, prior, prior + 0.5, max(0.01, prior - 0.5), prior),
            )


def seed_rate(db_path: Path, market: str, *, obs_date: str = "2026-11-12", prior_date: str = "2026-11-11",
              value: float = 4.25, prior: float = 4.30, known: datetime = NOW) -> None:
    _init_rates_db(db_path)
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve"
    with closing(sqlite3.connect(db_path)) as db, db:
        for idx, (day, val) in enumerate(((obs_date, value), (prior_date, prior))):
            if val is None:
                continue
            payload = {
                "store_available_at_utc": known.isoformat(),
                "record": {
                    "alias": market, "value": val, "unit": "percent", "reference_period": day,
                    "official_url": url, "rights": {"attribution": "U.S. Department of the Treasury"},
                },
            }
            db.execute(
                "INSERT OR REPLACE INTO observations VALUES(?,?,?,?,?,?)",
                ("direct_rates", market, day, known.isoformat(), f"ver-{market}-{day}-{idx}", json.dumps(payload)),
            )


def seed_all(bars_db: Path, rates_db: Path, *, at: datetime = NOW, value: float = 92.03, prior: float = 92.76):
    for m, spec in quotes.SYMBOLS.items():
        if spec[0] == "LOCAL_OFFICIAL_RATES":
            seed_rate(rates_db, m, obs_date=at.astimezone(quotes.ET).date().isoformat(),
                      prior_date=(at - timedelta(days=1)).astimezone(quotes.ET).date().isoformat(),
                      value=value, prior=prior, known=at)
        else:
            seed_bar(bars_db, m, at=at, value=value, prior=prior, known=at)


def cnbc_dxy_json(*, at: datetime = NOW, value: float = 105.5, prior: float = 105.0,
                  symbol: str = ".DXY", asset_type: str = "INDEX") -> bytes:
    return json.dumps({"QuickQuoteResult": {"QuickQuote": [{
        "symbol": symbol, "code": "0", "last": str(value), "previous_day_closing": str(prior),
        "last_time": at.isoformat(), "assetType": asset_type,
    }]}}).encode("utf-8")


@pytest.mark.parametrize("market", list(quotes.SYMBOLS))
def test_each_market_keeps_source_symbol_clock_prior_close_and_change(market):
    if quotes.SYMBOLS[market][0] == "LOCAL_OFFICIAL_RATES":
        seed_rate(quotes.RATES_DB, market, obs_date="2026-11-12", prior_date="2026-11-11",
                  value=92.03, prior=92.76, known=NOW)
    else:
        seed_bar(quotes.BARS_DB, market, at=NOW, value=92.03, prior=92.76, known=NOW)
    q = quotes.get(market, now=NOW, clock=lambda: NOW)
    assert q["source_symbol"] == quotes.SYMBOLS[market][1]
    assert q["known_at_utc"] == NOW.isoformat()
    assert q["prior_close"] == 92.76 and q["day_change"] == pytest.approx(-0.73)
    assert q["fetch_seconds"] >= 0 and q["request_seconds"] >= 0
    assert quotes.resolve(q["observation_path"], q["observation_sha256"])["value"] == 92.03
    assert "yahoo" not in str(q.get("source") or "").casefold()
    assert "yahoo" not in str(q.get("source_url") or "").casefold()
    if market in {"US2Y", "US10Y"}:
        assert q["unit"] == "percent" and q["change_unit"] == "percentage points"
        assert q["instrument_type"] == "BOND" and "futures" not in q["instrument_name"]
        assert "Treasury" in q["source"]


def test_canonical_usdjpy_local_bar_reaches_chart_consumer_without_pair_conversion(monkeypatch):
    seed_bar(quotes.BARS_DB, "USDJPY", at=NOW, value=154.5, prior=154.25, known=NOW)
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    quotes.get("USDJPY", now=NOW, clock=lambda: NOW)
    q = prices.public_chart_quote("USDJPY", NOW)
    check = image.compare_scale("USDJPY", {
        "tv_symbol": tv.SYMBOLS["USDJPY"], "sha256": "a" * 64,
        "captured_at_utc": NOW.isoformat(), "page_title": "USDJPY 154.5"}, q)
    assert q["source_symbol"] == "USDJPY" and q["price"] == 154.5
    assert check["difference_pct"] == 0 and check["comparison_basis"] == "AT_CAPTURE"
    with pytest.raises(quotes.QuoteError, match="CC024_YAHOO_SCRAPER_RETIRED"):
        quotes.parse("USDJPY", b"{}", received_at=NOW, seconds=0)


@pytest.mark.parametrize("problem,cause", [
    ("failed", "PUBLIC_QUOTE_HTTP_503"), ("stale", "PUBLIC_QUOTE_STALE"),
    ("wrong", "PUBLIC_QUOTE_SYMBOL_MISMATCH"), ("future", "PUBLIC_QUOTE_FUTURE_CLOCK"),
    ("nan", "PUBLIC_QUOTE_VALUE_INVALID"), ("type", "PUBLIC_QUOTE_SYMBOL_MISMATCH")])
def test_failed_stale_wrong_and_invalid_answers_keep_cause_and_consume_minute(problem, cause):
    calls = []

    def read(url):
        calls.append(url)
        if problem == "failed":
            raise HTTPError(url, 503, "unavailable", None, None)
        return cnbc_dxy_json(
            at=NOW - timedelta(seconds=4501) if problem == "stale" else
            NOW + timedelta(seconds=1) if problem == "future" else NOW,
            symbol="WRONG" if problem == "wrong" else ".DXY",
            asset_type="BOND" if problem == "type" else "INDEX",
            value=float("nan") if problem == "nan" else 105.5,
        )

    for second in (0, 59):
        with pytest.raises(quotes.QuoteError, match=cause):
            quotes.get("DXY", now=NOW + timedelta(seconds=second), clock=lambda: NOW,
                       reader=read, allow_cnbc_dxy_fallback=True)
    assert len(calls) == 1


def test_aliases_and_other_consumers_share_one_minute_and_failures_are_not_retried():
    seed_bar(quotes.BARS_DB, "US500", at=NOW, value=6000.0, prior=5990.0, known=NOW)
    first = quotes.get("US500", now=NOW, clock=lambda: NOW)
    second = quotes.get("SPX", now=NOW + timedelta(seconds=59))
    assert second["cache_hit"] and second["request_seconds"] == 0
    assert first["observation_sha256"] == second["observation_sha256"]
    third = quotes.get("SPX", now=NOW + timedelta(seconds=60), clock=lambda: NOW + timedelta(seconds=60))
    assert third["cache_hit"] is False


def test_two_callers_cannot_fetch_a_symbol_concurrently():
    def read(url):
        with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_FETCH_IN_PROGRESS"):
            quotes.get("DXY", now=NOW, clock=lambda: NOW, allow_cnbc_dxy_fallback=True)
        return cnbc_dxy_json()
    quotes.get("DXY", now=NOW, clock=lambda: NOW, reader=read, allow_cnbc_dxy_fallback=True)


def test_original_observation_survives_latest_refresh_and_tampering_is_detected():
    seed_bar(quotes.BARS_DB, "BRENT", at=NOW, value=92.03, prior=92.76, known=NOW)
    first = quotes.get("BRENT", now=NOW, clock=lambda: NOW)
    seed_bar(quotes.BARS_DB, "BRENT", at=NOW + timedelta(minutes=1), value=91.0, prior=92.76,
             known=NOW + timedelta(minutes=1))
    quotes.get("BRENT", now=NOW + timedelta(minutes=1), clock=lambda: NOW + timedelta(minutes=1))
    assert quotes.resolve(first["observation_path"], first["observation_sha256"])["value"] == 92.03
    Path(first["observation_path"]).write_bytes(b"{}")
    with pytest.raises(quotes.QuoteError, match="BINDING_CHANGED"):
        quotes.resolve(first["observation_path"], first["observation_sha256"])


def target(text="BRENT CRUDE; FUTURES FALL 0.3% TO $92.44/BBL", **kwargs):
    return {"post_id": "123", "post_text": text,
            "post_time_utc": (NOW - timedelta(minutes=2)).isoformat(), **kwargs}


def wire_local(monkeypatch, market="BRENT", *, problem=None, value=92.03, prior=92.76):
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    if problem == "failed":
        return
    bar_at = NOW - timedelta(hours=2) if problem == "stale" else NOW
    if quotes.SYMBOLS[market][0] == "LOCAL_OFFICIAL_RATES":
        obs_d = (NOW - timedelta(days=10)).date().isoformat() if problem == "stale" else NOW.astimezone(quotes.ET).date().isoformat()
        seed_rate(quotes.RATES_DB, market, obs_date=obs_d, value=value, prior=prior, known=NOW)
    else:
        seed_bar(quotes.BARS_DB, market, at=bar_at, value=value, prior=prior, known=NOW)


def test_dropped_brent_target_gains_same_session_fact_and_reaches_real_ranking(monkeypatch, tmp_path):
    wire_local(monkeypatch, "BRENT")
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{
        "handle": "FirstSquawk", "text": target()["post_text"], "tweet_id": "123",
        "url": "https://x.com/FirstSquawk/status/123", "posted_utc": target()["post_time_utc"]}]})
    prepared = packs.prepare(store, feed_path=feed, output_root=tmp_path / "request", now=NOW,
                             reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(prepared["request_path"])
    assert request["candidates"][0]["usable_source_ids"]
    quoted = next(s for s in request["sources"] if s["source_id"] in request["candidates"][0]["usable_source_ids"])
    assert policy.check_fact(target(), quoted, now=NOW)["kind"] == "session"
    assert facts.resolve(quoted)["store_payload_sha256"] == quoted["store_payload_sha256"]

    def rank(prompt, **kw):
        assert "Brent crude oil proxy" in prompt and "92.03" in prompt
        assert "today, 11:00 AM ET" in prompt
        return {"ranking": [{"post_id": "123", "quality_score": 79}]}, {"caller": "test"}

    def never_write(*a, **kw):
        pytest.fail("A new fact does not bypass the quality floor")

    result = bot.rank_and_draft(prepared["request_path"], output_dir=tmp_path / "rank", ranker=rank,
                                writer=never_write, now=NOW)
    assert not packs.read_json(result)["items"]


@pytest.mark.parametrize("problem", ["failed", "stale"])
def test_fetch_failure_keeps_other_held_facts_and_seven_rule_checks(monkeypatch, problem):
    wire_local(monkeypatch, "BRENT", problem=problem)
    retained = facts._source("Brent base-rate count: 3 of 5, Jan 2020 to Dec 2025 (desk).",
        {"kind": "base_rate", "markets": ["BRENT"], "count": 3, "sample_count": 5,
         "period_text": "Jan 2020 to Dec 2025", "through_date": "2026-11-11"},
        attribution="desk", known=NOW.isoformat(), artifact={"kind": "test"})
    sources = [retained]
    added, attempts, _ = facts.supplement([target()], sources, now=NOW)
    assert not added and sources == [retained]
    assert policy.check_fact(target(), retained, now=NOW)["kind"] == "base_rate"
    assert any(a.get("cause", "").startswith("PUBLIC_QUOTE_") for a in attempts)


def test_acquired_fact_reaches_private_delivery_and_rechecks_its_immutable_source(monkeypatch, tmp_path):
    from test_x_reply_bot_cc464 import FakeBot
    wire_local(monkeypatch, "BRENT")
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    binding, feed = tmp_path / "control/x_reply_bot_binding.json", tmp_path / "feed.json"
    packs.save_json(binding, {"bound_chat_id": 123456789})
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{
        "handle": "FirstSquawk", "text": target()["post_text"], "tweet_id": "123",
        "url": "https://x.com/FirstSquawk/status/123", "posted_utc": target()["post_time_utc"]}]})

    class PrivateBot(FakeBot):
        def call(self, method, payload=None):
            result = super().call(method, payload)
            if method == "sendMessage":
                result["date"] = int(NOW.timestamp())
            return result

    private_bot = PrivateBot()

    def rank(prompt, **kw):
        assert "92.03" in prompt
        return {"ranking": [{"post_id": "123", "quality_score": 90}]}, {}

    def draft(path, *, output_dir):
        request = packs.read_json(path)
        source_id = request["candidates"][0]["usable_source_ids"][0]

        def write(prompt, **kw):
            return {"items": [{"post_id": "123", "source_id": source_id,
                "draft_text": "Brent crude oil proxy traded at 92.03 USD per barrel on 12 Nov (Held market data). That is below the earlier quote.",
                "fact_text": "92.03 USD per barrel", "source_name": "Held market data", "date_text": "12 Nov",
                "addition": "A later price", "point": "Later same-session observation", "reply_shape": "priced_in"}]}, {}

        return bot.rank_and_draft(path, output_dir=output_dir, ranker=rank, writer=write, now=NOW)

    result = bot.refresh_due(store, binding_path=binding, feed_path=feed,
        output_root=tmp_path / "out", bot=private_bot, drafter=draft, now=NOW)
    assert result["status"] == "DELIVERED", result
    assert result["quote_fetches"][-1]["fetch_seconds"] >= 0
    assert result["delivery"]["delivered"][0]["post_to_delivery_minutes"] == 2
    sent = next(payload for method, payload in private_bot.calls if method == "sendMessage")
    assert "Fact age: today, 11:00 AM ET (0 min old)" in sent["text"]
    assert result["public_submit_actions"] == 0


def test_fresh_main_then_native_sources_precede_public_https(monkeypatch, tmp_path):
    from test_chart_price_reference_cc489 import export_price, bar
    dbpath = tmp_path / "native.sqlite3"
    with closing(sqlite3.connect(dbpath)) as db, db:
        db.executescript("""CREATE TABLE history_sources(source_id TEXT PRIMARY KEY, source_sha256 TEXT,
            path TEXT, market TEXT, timeframe TEXT, series_id TEXT, known_epoch REAL, metadata_json TEXT);
            CREATE TABLE history_bars(source_id TEXT, open_epoch INTEGER, end_epoch INTEGER,
            session_date TEXT, open REAL, high REAL, low REAL, close REAL);
            CREATE TABLE history_invalid(source_id TEXT, open_epoch INTEGER);""")
    monkeypatch.setattr(prices, "BAR_STORE", dbpath)
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", tmp_path / "main.json")
    export_price(prices.PLAN_STATUS_PATH, at=NOW, price=100)
    bar(dbpath, price=101, end=NOW)
    post = target("EUR/USD rises")
    added, attempts, _ = facts.supplement([post], [], now=NOW)
    # Pre-relaunch audit: never the internal "Main" name; the price at EUR/USD's five places.
    assert added[0]["excerpt"].startswith("EUR/USD price: 100.00000 ")
    assert "Main" not in added[0]["excerpt"]
    assert len(attempts) == 1 and attempts[0]["source_kind"] == "PLAN_STATUS_EXPORT"
    prices.PLAN_STATUS_PATH.unlink()
    added, attempts, _ = facts.supplement([post], [], now=NOW)
    assert "EUR/USD price proxy: 101" in added[0]["excerpt"]
    assert "CFD" not in added[0]["excerpt"] and "Exness" not in added[0]["excerpt"]
    assert attempts[-1]["source_kind"] == "BAR_STORE_M1_CLOSE"
    later, _, _ = facts.supplement([post], [], now=NOW + timedelta(seconds=30))
    assert later[0]["source_id"] == added[0]["source_id"]


def test_topic_and_expired_targets_never_acquire(monkeypatch, tmp_path):
    wire_local(monkeypatch, "BRENT")
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [
        {"handle": "FirstSquawk", "text": "Good morning", "tweet_id": "1", "url": "https://x.com/FirstSquawk/status/1",
         "posted_utc": NOW.isoformat()},
        {"handle": "FirstSquawk", "text": target()["post_text"], "tweet_id": "2", "url": "https://x.com/FirstSquawk/status/2",
         "posted_utc": (NOW - timedelta(minutes=16)).isoformat()}]})
    p = packs.prepare(store, feed_path=feed, now=NOW, output_root=tmp_path / "out", reply_policy=packs.MOBILE_POLICY)
    assert not packs.read_json(p["request_path"])["candidates"]


def test_chart_capture_prefetch_is_read_before_image_and_is_compared_with_source(monkeypatch, tmp_path):
    wire_local(monkeypatch, "EURUSD")
    prices.prepare_chart_quote("EURUSD", now=NOW)
    snapshot = {"tv_symbol": tv.SYMBOLS["EURUSD"], "page_title": "EURUSD 92.03",
                "captured_at_utc": (NOW + timedelta(seconds=20)).isoformat(), "sha256": "c" * 64}
    check = image.bind_scale("EURUSD", snapshot)["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE" and check["difference_pct"] == 0
    assert check["quote"]["source"] == "Held market data"
    assert check["quote"]["source_symbol"] == "EURUSD"
    assert image.validate_scale("EURUSD", {**snapshot, "price_scale_check": check}) == check


def test_later_fetch_never_certifies_an_earlier_chart_and_mismatch_is_not_erased(monkeypatch):
    wire_local(monkeypatch, "EURUSD")
    quotes.get("EURUSD", now=NOW, clock=lambda: NOW)
    snapshot = {"tv_symbol": tv.SYMBOLS["EURUSD"], "page_title": "EURUSD 100",
                "captured_at_utc": (NOW - timedelta(seconds=1)).isoformat(), "sha256": "c" * 64}
    assert image.bind_scale("EURUSD", snapshot)["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"
    snapshot["captured_at_utc"] = NOW.isoformat()
    with pytest.raises(image.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        image.bind_scale("EURUSD", snapshot)


def test_wti_proxy_is_named_and_existing_chart_limits_stay(monkeypatch):
    wire_local(monkeypatch, "USOIL")
    quotes.get("USOIL", now=NOW, clock=lambda: NOW)
    reference = prices.public_chart_quote("USOIL", NOW)
    assert reference["instrument_name"] == "WTI crude oil proxy" and reference["source_symbol"] == "USOIL"
    snapshot = {"tv_symbol": tv.SYMBOLS["USOIL"], "page_title": "USOIL 100",
                "captured_at_utc": NOW.isoformat(), "sha256": "c" * 64}
    with pytest.raises(image.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        image.bind_scale("USOIL", snapshot)
    assert image.MAX_DIFFERENCE_PCT["XAUUSD"] == .15 and image.MAX_DIFFERENCE_PCT["USOIL"] == .4


def test_closed_index_uses_a_live_yield_driver_with_rule_five_still_enforced(monkeypatch):
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    seed_bar(quotes.BARS_DB, "US500", at=NOW - timedelta(days=1), value=6000.0, prior=5990.0, known=NOW)
    seed_rate(quotes.RATES_DB, "US10Y", obs_date="2026-11-11", prior_date="2026-11-10", value=4.35, prior=4.30, known=NOW)
    post = target("S&P 500 rises")
    added, attempts, _ = facts.supplement([post], [], now=NOW)
    assert len(added) == 1 and added[0]["fact_binding"]["markets"] == ["US10Y"]
    assert any(a.get("cause") == "PUBLIC_QUOTE_STALE" for a in attempts)
    assert policy.check_fact(post, added[0], now=NOW)["kind"] == "daily"
    with pytest.raises(ValueError, match="FACT_DRIVER_LINK_NOT_STATED"):
        policy.check_fact(post, added[0], now=NOW, draft={"draft_text": "A different market is moving on 11 Nov."})


def test_real_capture_prefetches_before_download_and_binds_that_quote(monkeypatch, tmp_path):
    from test_tradingview_snapshot_cc314 import FIXTURE
    wire_local(monkeypatch, "EURUSD")
    prepare = prices.prepare_chart_quote
    monkeypatch.setattr(prices, "prepare_chart_quote", lambda market: prepare(market, now=NOW))
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    path = tmp_path / "EURUSD_2026-11-12_16-00-05.png"

    def download(args, **kwargs):
        path.write_bytes(FIXTURE.read_bytes())
        return {"path": str(path), "suggested_filename": path.name, "legend": "EURUSD 4h",
                "page_title": "EURUSD 92.03", "captured_at_utc": (NOW + timedelta(seconds=5)).isoformat()}

    monkeypatch.setattr(tv, "_run_worker", download)
    snapshot = tv.capture("EURUSD", "240", tmp_path)
    check = snapshot["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE" and check["quote"]["source_symbol"] == "EURUSD"
    assert json.loads(tv.OUTCOMES.read_text())["price_scale_check"] == check


def test_public_quote_reaches_coordinator_and_existing_publication_image_register(monkeypatch, tmp_path):
    from test_publication_image_contract_cc463 import message_with, snapshot
    wire_local(monkeypatch, "US500", value=7549.51, prior=7500.0)
    quotes.get("US500", now=NOW, clock=lambda: NOW)
    taken = image.bind_scale("US500", snapshot())
    asset = {**tv.snapshot_asset("US500", "S&P 500", taken, tmp_path),
             "article_inclusion": True, "canonical_article_media": True}
    _, runtime, coordinator, message = message_with(tmp_path / "run", [asset])
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DISPATCH_CONFIRMED" and runtime.publish_calls == ["substack"]
    from live_contentops.article_publication_quality_v1 import image_register
    check = image_register(coordinator).records()[-1]["images"][0]["price_scale_check"]
    assert check["quote"]["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"


def test_fact_rule_one_searches_a_driver_when_direct_quote_is_too_old_for_post(monkeypatch):
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    seed_bar(quotes.BARS_DB, "BRENT", at=NOW - timedelta(minutes=70), value=92.03, prior=92.76, known=NOW)
    seed_rate(quotes.RATES_DB, "US10Y", obs_date="2026-11-11", prior_date="2026-11-10", value=4.35, prior=4.30, known=NOW)
    added, attempts, _ = facts.supplement([target()], [], now=NOW)
    assert added[0]["fact_binding"]["markets"] == ["US10Y"]
    assert any(a.get("cause") == "FACT_SESSION_NOT_CURRENT_WITHIN_60_MINUTES" for a in attempts)


def test_a_malformed_held_fact_does_not_hide_the_acquired_same_market_quote(monkeypatch):
    wire_local(monkeypatch, "BRENT")
    malformed = {"excerpt": "Brent with a broken clock", "known_at_utc": "bad"}
    added, _, _ = facts.supplement([target()], [malformed], now=NOW)
    assert added[0]["fact_binding"]["markets"] == ["BRENT"]


def test_public_chart_quote_precedes_legacy_saved_tick_after_the_first_two_sources(monkeypatch):
    wire_local(monkeypatch, "EURUSD")
    quotes.get("EURUSD", now=NOW, clock=lambda: NOW)

    def legacy(*a, **kw):
        pytest.fail("CC-509 source order: public quote before legacy saved ticks")

    monkeypatch.setattr(image, "saved_main_quote", legacy)
    assert prices.saved_chart_quote("EURUSD", NOW)["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"


def test_capture_acquires_after_main_and_native_even_with_a_held_legacy_tick(monkeypatch):
    wire_local(monkeypatch, "EURUSD")
    monkeypatch.setattr(image, "saved_main_quote", lambda *a, **kw: {"price": 100})
    prices.prepare_chart_quote("EURUSD", now=NOW)
    q = prices.public_chart_quote("EURUSD", NOW)
    assert q["price"] == 92.03 and q["source_symbol"] == "EURUSD"
