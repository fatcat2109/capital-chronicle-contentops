"""CC-509: real consumers use an acquired quote; fixtures never reach Runtime."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
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


def answer(market="BRENT", *, at=NOW, value=92.03, prior=92.76, symbol=None, instrument_type=None):
    provider, expected, _, _, expected_type = quotes.SYMBOLS[market]
    if provider == "YAHOO":
        data = {"chart": {"result": [{"meta": {"symbol": symbol or expected,
            "regularMarketPrice": value, "regularMarketTime": at.timestamp(), "previousClose": prior,
            "instrumentType": instrument_type or expected_type}}]}}
    else:
        data = {"QuickQuoteResult": {"QuickQuote": [{"symbol": symbol or expected, "code": "0",
            "last": str(value), "previous_day_closing": str(prior), "last_time": at.isoformat(),
            "assetType": instrument_type or expected_type}]}}
    return json.dumps(data).encode("utf-8")


def get(market="BRENT", *, now=NOW, raw=None, **kwargs):
    return quotes.get(market, now=now, clock=lambda: now, reader=lambda _: raw or answer(market, at=now), **kwargs)


@pytest.mark.parametrize("market", quotes.SYMBOLS)
def test_each_market_keeps_source_symbol_clock_prior_close_and_change(market):
    q = get(market)
    assert q["source_symbol"] == quotes.SYMBOLS[market][1]
    assert q["observed_at_utc"] == NOW.isoformat() and q["known_at_utc"] == NOW.isoformat()
    assert q["prior_close"] == 92.76 and q["day_change"] == -.73
    assert q["fetch_seconds"] >= 0 and q["request_seconds"] >= 0
    assert quotes.resolve(q["observation_path"], q["observation_sha256"])["value"] == 92.03
    if market in {"US2Y", "US10Y"}:
        assert q["unit"] == "percent" and q["change_unit"] == "percentage points"
        assert q["instrument_type"] == "BOND" and "futures" not in q["instrument_name"]


def test_canonical_usdjpy_response_reaches_chart_consumer_without_pair_conversion(monkeypatch):
    calls = []
    def read(url):
        calls.append(url)
        return answer("USDJPY", symbol="USDJPY=X", value=154.5, prior=154.25)
    monkeypatch.setattr(quotes, "http_read", read)
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    quotes.get("USDJPY", now=NOW, clock=lambda: NOW)
    q = prices.public_chart_quote("USDJPY", NOW)
    check = image.compare_scale("USDJPY", {
        "tv_symbol": tv.SYMBOLS["USDJPY"], "sha256": "a" * 64,
        "captured_at_utc": NOW.isoformat(), "page_title": "USDJPY 154.5"}, q)
    assert len(calls) == 1 and "USDJPY%3DX" in calls[0]
    assert q["source_symbol"] == "USDJPY=X" and q["price"] == 154.5
    assert check["difference_pct"] == 0 and check["comparison_basis"] == "AT_CAPTURE"
    with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_SYMBOL_MISMATCH"):
        quotes.parse("USDJPY", answer("USDJPY", symbol="JPYUSD=X"), received_at=NOW, seconds=0)


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
        return answer(at=NOW - timedelta(seconds=4501) if problem == "stale" else
                      NOW + timedelta(seconds=1) if problem == "future" else NOW,
                      symbol="CL=F" if problem == "wrong" else None,
                      instrument_type="INDEX" if problem == "type" else None,
                      value=float("nan") if problem == "nan" else 92.03)
    for second in (0, 59):
        with pytest.raises(quotes.QuoteError, match=cause):
            quotes.get("BRENT", now=NOW + timedelta(seconds=second), clock=lambda: NOW,
                       reader=read)
    assert len(calls) == 1


def test_aliases_and_other_consumers_share_one_minute_and_failures_are_not_retried():
    calls = []
    def read(url):
        calls.append(url)
        return answer("US500")
    first = quotes.get("US500", now=NOW, clock=lambda: NOW, reader=read)
    second = quotes.get("SPX", now=NOW + timedelta(seconds=59), reader=read)
    assert len(calls) == 1 and second["cache_hit"] and second["request_seconds"] == 0
    assert first["observation_sha256"] == second["observation_sha256"]
    quotes.get("SPX", now=NOW + timedelta(seconds=60), clock=lambda: NOW + timedelta(seconds=60), reader=read)
    assert len(calls) == 2


def test_two_callers_cannot_fetch_a_symbol_concurrently():
    def read(url):
        with pytest.raises(quotes.QuoteError, match="PUBLIC_QUOTE_FETCH_IN_PROGRESS"):
            get()
        return answer()
    quotes.get("BRENT", now=NOW, clock=lambda: NOW, reader=read)


def test_original_observation_survives_latest_refresh_and_tampering_is_detected():
    first = get()
    get(now=NOW + timedelta(minutes=1), raw=answer(value=91, at=NOW + timedelta(minutes=1)))
    assert quotes.resolve(first["observation_path"], first["observation_sha256"])["value"] == 92.03
    Path(first["observation_path"]).write_bytes(b"{}")
    with pytest.raises(quotes.QuoteError, match="BINDING_CHANGED"):
        quotes.resolve(first["observation_path"], first["observation_sha256"])


def target(text="BRENT CRUDE; FUTURES FALL 0.3% TO $92.44/BBL", **kwargs):
    return {"post_id": "123", "post_text": text,
            "post_time_utc": (NOW - timedelta(minutes=2)).isoformat(), **kwargs}


def wire(monkeypatch, market="BRENT", *, problem=None):
    calls = []
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    def read(url):
        calls.append(url)
        if problem == "failed":
            raise TimeoutError()
        return answer(market, at=NOW - timedelta(hours=2) if problem == "stale" else NOW,
                      symbol="CL=F" if problem == "wrong" else None)
    monkeypatch.setattr(quotes, "http_read", read)
    return calls


def test_dropped_brent_target_gains_same_session_fact_and_reaches_real_ranking(monkeypatch, tmp_path):
    calls = wire(monkeypatch)
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{
        "handle": "FirstSquawk", "text": target()["post_text"], "tweet_id": "123",
        "url": "https://x.com/FirstSquawk/status/123", "posted_utc": target()["post_time_utc"]}]})
    prepared = packs.prepare(store, feed_path=feed, output_root=tmp_path / "request", now=NOW,
                             reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(prepared["request_path"])
    assert request["candidates"][0]["usable_source_ids"] and len(calls) == 1
    quoted = next(s for s in request["sources"] if s["source_id"] in request["candidates"][0]["usable_source_ids"])
    assert policy.check_fact(target(), quoted, now=NOW)["kind"] == "session"
    assert facts.resolve(quoted)["store_payload_sha256"] == quoted["store_payload_sha256"]
    def rank(prompt, **kw):
        assert "Brent crude oil futures" in prompt and "92.03" in prompt
        assert "today, 11:00 AM ET" in prompt
        return {"ranking": [{"post_id": "123", "quality_score": 79}]}, {"caller": "test"}
    def never_write(*a, **kw):
        pytest.fail("A new fact does not bypass the quality floor")
    result = bot.rank_and_draft(prepared["request_path"], output_dir=tmp_path / "rank", ranker=rank,
                                writer=never_write, now=NOW)
    assert not packs.read_json(result)["items"]


@pytest.mark.parametrize("problem", ["failed", "stale", "wrong"])
def test_fetch_failure_keeps_other_held_facts_and_seven_rule_checks(monkeypatch, problem):
    calls = wire(monkeypatch, problem=problem)
    retained = facts._source("Brent base-rate count: 3 of 5, Jan 2020 to Dec 2025 (desk).",
        {"kind": "base_rate", "markets": ["BRENT"], "count": 3, "sample_count": 5,
         "period_text": "Jan 2020 to Dec 2025", "through_date": "2026-11-11"},
        attribution="desk", known=NOW.isoformat(), artifact={"kind": "test"})
    sources = [retained]
    added, attempts, _ = facts.supplement([target()], sources, now=NOW)
    assert not added and sources == [retained] and len(calls) == 2
    assert len(set(calls)) == 2  # direct and one driver, once each
    assert policy.check_fact(target(), retained, now=NOW)["kind"] == "base_rate"
    assert any(a.get("cause", "").startswith("PUBLIC_QUOTE_") for a in attempts)


def test_acquired_fact_reaches_private_delivery_and_rechecks_its_immutable_source(monkeypatch, tmp_path):
    from test_x_reply_bot_cc464 import FakeBot
    calls = wire(monkeypatch)
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
                "draft_text": "Brent futures traded at 92.03 USD per barrel on 12 Nov (Yahoo Finance). That is below the earlier quote.",
                "fact_text": "92.03 USD per barrel", "source_name": "Yahoo Finance", "date_text": "12 Nov",
                "addition": "A later price", "point": "Later same-session observation", "reply_shape": "priced_in"}]}, {}
        return bot.rank_and_draft(path, output_dir=output_dir, ranker=rank, writer=write, now=NOW)
    result = bot.refresh_due(store, binding_path=binding, feed_path=feed,
        output_root=tmp_path / "out", bot=private_bot, drafter=draft, now=NOW)
    assert result["status"] == "DELIVERED", result
    assert len(calls) == 1 and result["quote_fetches"][-1]["fetch_seconds"] >= 0
    assert result["delivery"]["delivered"][0]["post_to_delivery_minutes"] == 2
    sent = next(payload for method, payload in private_bot.calls if method == "sendMessage")
    assert "Fact age: today, 11:00 AM ET (0 min old)" in sent["text"]
    assert result["public_submit_actions"] == 0


def test_fresh_main_then_native_sources_precede_public_https(monkeypatch, tmp_path):
    from test_chart_price_reference_cc489 import export_price, bar
    # Reuse the source fixtures' setup logic via an explicitly bounded schema.
    import sqlite3
    dbpath = tmp_path / "native.sqlite3"
    with sqlite3.connect(dbpath) as db:
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
    assert added[0]["excerpt"].startswith("EURUSD Main quote: 100")
    assert len(attempts) == 1 and attempts[0]["source_kind"] == "PLAN_STATUS_EXPORT"
    prices.PLAN_STATUS_PATH.unlink()
    added, attempts, _ = facts.supplement([post], [], now=NOW)
    assert "EUR/USD CFD: 101" in added[0]["excerpt"]
    assert attempts[-1]["source_kind"] == "BAR_STORE_M1_CLOSE"
    later, _, _ = facts.supplement([post], [], now=NOW + timedelta(seconds=30))
    assert later[0]["source_id"] == added[0]["source_id"]


def test_topic_and_expired_targets_never_acquire(monkeypatch, tmp_path):
    calls = wire(monkeypatch)
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [
        {"handle": "FirstSquawk", "text": "Good morning", "tweet_id": "1", "url": "https://x.com/FirstSquawk/status/1",
         "posted_utc": NOW.isoformat()},
        {"handle": "FirstSquawk", "text": target()["post_text"], "tweet_id": "2", "url": "https://x.com/FirstSquawk/status/2",
         "posted_utc": (NOW - timedelta(minutes=16)).isoformat()}]})
    p = packs.prepare(store, feed_path=feed, now=NOW, output_root=tmp_path / "out", reply_policy=packs.MOBILE_POLICY)
    assert not calls and not packs.read_json(p["request_path"])["candidates"]


def test_chart_capture_prefetch_is_read_before_image_and_is_compared_with_source(monkeypatch, tmp_path):
    calls = wire(monkeypatch, "EURUSD")
    prices.prepare_chart_quote("EURUSD", now=NOW)
    # This is the same immutable quote that the subsequent image binds.
    snapshot = {"tv_symbol": tv.SYMBOLS["EURUSD"], "page_title": "EURUSD 92.03",
                "captured_at_utc": (NOW + timedelta(seconds=20)).isoformat(), "sha256": "c" * 64}
    check = image.bind_scale("EURUSD", snapshot)["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE" and check["difference_pct"] == 0
    assert check["quote"]["source"] == "Yahoo Finance" and check["quote"]["source_symbol"] == "EURUSD=X"
    assert len(calls) == 1 and image.validate_scale("EURUSD", {**snapshot, "price_scale_check": check}) == check


def test_later_fetch_never_certifies_an_earlier_chart_and_mismatch_is_not_erased(monkeypatch):
    wire(monkeypatch, "EURUSD")
    get("EURUSD")
    snapshot = {"tv_symbol": tv.SYMBOLS["EURUSD"], "page_title": "EURUSD 100",
                "captured_at_utc": (NOW - timedelta(seconds=1)).isoformat(), "sha256": "c" * 64}
    assert image.bind_scale("EURUSD", snapshot)["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"
    snapshot["captured_at_utc"] = NOW.isoformat()
    with pytest.raises(image.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        image.bind_scale("EURUSD", snapshot)


def test_future_is_named_and_existing_chart_limits_stay(monkeypatch):
    wire(monkeypatch, "USOIL")
    get("USOIL")
    reference = prices.public_chart_quote("USOIL", NOW)
    assert reference["instrument_name"] == "WTI crude oil futures" and reference["source_symbol"] == "CL=F"
    snapshot = {"tv_symbol": tv.SYMBOLS["USOIL"], "page_title": "USOIL 100",
                "captured_at_utc": NOW.isoformat(), "sha256": "c" * 64}
    with pytest.raises(image.ImageContractError, match="PRICE_SCALE_MISMATCH"):
        image.bind_scale("USOIL", snapshot)
    assert image.MAX_DIFFERENCE_PCT["XAUUSD"] == .15 and image.MAX_DIFFERENCE_PCT["USOIL"] == .4


def test_closed_index_uses_a_live_yield_driver_with_rule_five_still_enforced(monkeypatch):
    monkeypatch.setattr(quotes, "utcnow", lambda: NOW)
    def read(url):
        return answer("US10Y") if "US10Y" in url else answer("US500", at=NOW-timedelta(days=1))
    monkeypatch.setattr(quotes, "http_read", read)
    post = target("S&P 500 rises")
    added, attempts, _ = facts.supplement([post], [], now=NOW)
    assert len(added) == 1 and added[0]["fact_binding"]["markets"] == ["US10Y"]
    assert any(a.get("cause") == "PUBLIC_QUOTE_STALE" for a in attempts)
    assert policy.check_fact(post, added[0], now=NOW)["kind"] == "session"
    with pytest.raises(ValueError, match="FACT_DRIVER_LINK_NOT_STATED"):
        policy.check_fact(post, added[0], now=NOW, draft={"draft_text": "A different market is moving."})


def test_real_capture_prefetches_before_download_and_binds_that_quote(monkeypatch, tmp_path):
    from test_tradingview_snapshot_cc314 import FIXTURE
    calls = wire(monkeypatch, "EURUSD")
    prepare = prices.prepare_chart_quote
    monkeypatch.setattr(prices, "prepare_chart_quote", lambda market: prepare(market, now=NOW))
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    path = tmp_path / "EURUSD_2026-11-12_16-00-05.png"
    def download(args, **kwargs):
        assert len(calls) == 1  # no quote first acquired after the image
        path.write_bytes(FIXTURE.read_bytes())
        return {"path": str(path), "suggested_filename": path.name, "legend": "EURUSD 4h",
                "page_title": "EURUSD 92.03", "captured_at_utc": (NOW+timedelta(seconds=5)).isoformat()}
    monkeypatch.setattr(tv, "_run_worker", download)
    snapshot = tv.capture("EURUSD", "240", tmp_path)
    check = snapshot["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE" and check["quote"]["source_symbol"] == "EURUSD=X"
    assert json.loads(tv.OUTCOMES.read_text())["price_scale_check"] == check


def test_public_quote_reaches_coordinator_and_existing_publication_image_register(monkeypatch, tmp_path):
    from test_publication_image_contract_cc463 import message_with, snapshot
    wire(monkeypatch, "US500")
    get("US500", raw=answer("US500", value=7549.51))
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
    def read(url):
        return answer("US10Y") if "US10Y" in url else answer("BRENT", at=NOW-timedelta(minutes=70))
    monkeypatch.setattr(quotes, "http_read", read)
    added, attempts, _ = facts.supplement([target()], [], now=NOW)
    assert added[0]["fact_binding"]["markets"] == ["US10Y"]
    assert any(a.get("cause") == "FACT_SESSION_NOT_CURRENT_WITHIN_60_MINUTES" for a in attempts)


def test_a_malformed_held_fact_does_not_hide_the_acquired_same_market_quote(monkeypatch):
    wire(monkeypatch)
    malformed = {"excerpt": "Brent with a broken clock", "known_at_utc": "bad"}
    added, _, _ = facts.supplement([target()], [malformed], now=NOW)
    assert added[0]["fact_binding"]["markets"] == ["BRENT"]


def test_public_chart_quote_precedes_legacy_saved_tick_after_the_first_two_sources(monkeypatch):
    wire(monkeypatch, "EURUSD")
    get("EURUSD")
    def legacy(*a, **kw):
        pytest.fail("CC-509 source order: public quote before legacy saved ticks")
    monkeypatch.setattr(image, "saved_main_quote", legacy)
    assert prices.saved_chart_quote("EURUSD", NOW)["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"


def test_capture_acquires_after_main_and_native_even_with_a_held_legacy_tick(monkeypatch):
    calls = wire(monkeypatch, "EURUSD")
    monkeypatch.setattr(image, "saved_main_quote", lambda *a, **kw: {"price": 100})
    prices.prepare_chart_quote("EURUSD", now=NOW)
    assert len(calls) == 1
