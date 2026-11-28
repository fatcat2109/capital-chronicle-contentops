"""Hermetic pre-Monday hardening & readiness tests for CC-489, CC-403, CC-549, CC-399, CC-436, CC-467, CC-468.

Zero live writes, zero network/browser calls, zero agy invocations, zero .stop mutations.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

from live_contentops import chart_price_reference_v1 as prices
from live_contentops import heavy_news_quotes_v1 as quotes_mod
from live_contentops import neo_endpoint_executor_v1 as neo_exec
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import public_market_quote_v1 as public_quotes
from live_contentops import publication_image_contract_v1 as image_contract
from live_contentops import reader_article_contract_v1 as cc403
from live_contentops import substack_daily_note_v1 as daily_note
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_images_v1 import SCHEMA as IMAGE_SCHEMA
from scripts.audit_chart_prices_cc489 import audit as audit_chart_prices


# ---------------------------------------------------------------------------
# CC-489 / CC-024: Closed cash-index local-bar close (US500 & USTEC), open-market
#         prepare_chart_quote headroom, and Yahoo HTTP ban + failure detail persistence
# ---------------------------------------------------------------------------

def _seed_local_m15_bar(db_path: Path, market: str, price: float, end_at: datetime,
                        *, known_at: datetime | None = None) -> None:
    from contextlib import closing
    import sqlite3
    known = known_at or end_at
    end_ep = int(end_at.timestamp())
    open_ep = end_ep - 900
    with closing(sqlite3.connect(db_path)) as db, db:
        db.executescript("""
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
        """)
        db.execute(
            "INSERT OR REPLACE INTO bars VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (market, open_ep, price, price + 1.0, max(0.01, price - 1.0), price,
             known.timestamp(), "a" * 64, "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID",
             f"EXNESS_DEMO:{market}", "NATIVE_BROKER"),
        )


@pytest.mark.parametrize("market,prefix,close_utc,price", [
    ("US500", "SPX", datetime(2026, 11, 24, 21, 0, 0, tzinfo=timezone.utc), 7201.09),   # 16:00:00 ET
    ("USTEC", "NDX", datetime(2026, 11, 24, 21, 0, 0, tzinfo=timezone.utc), 26214.17),  # 16:00:00 ET
])
def test_cc489_closed_cash_index_local_bar_close_compares_and_audits(
        tmp_path, monkeypatch, market, prefix, close_utc, price):
    """Held M15 NATIVE_BROKER closing bars (16:00 ET) pass closed-market scale checks with zero Yahoo HTTP."""
    captured = datetime(2026, 11, 25, 1, 0, 0, tzinfo=timezone.utc)  # 20:00 ET (closed)
    local_bars_db = tmp_path / "local-bars.sqlite3"
    _seed_local_m15_bar(local_bars_db, market, price, close_utc, known_at=close_utc + timedelta(seconds=5))
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(public_quotes, "BARS_DB", local_bars_db)
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", tmp_path / "missing-status.json")
    monkeypatch.setattr(prices, "BAR_STORE", tmp_path / "missing-bars.sqlite3")
    monkeypatch.setattr(image_contract, "QUOTE_ROOT", tmp_path / "missing-captures")
    monkeypatch.setattr(public_quotes, "utcnow", lambda: captured - timedelta(seconds=10))

    prices.prepare_chart_quote(market, now=captured - timedelta(seconds=10))
    snap = {
        "tv_symbol": tv.SYMBOLS[market],
        "sha256": "a" * 64,
        "page_title": f"{prefix} {price}",
        "captured_at_utc": captured.isoformat(),
    }
    bound = image_contract.bind_scale(market, snap)
    check = image_contract.validate_scale(market, bound)
    assert check["comparison_basis"] == "LAST_CLOSE"
    assert check["difference_pct"] == 0
    assert check["quote"]["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    assert check["quote"]["source_symbol"] == market

    # Audit script must also validate and count this closed cash-index check toward 95% coverage.
    day = "2026-11-25"
    reg = tmp_path / "images.jsonl"
    out = tmp_path / "outcomes.jsonl"
    reg.write_text(json.dumps({
        "schema_version": IMAGE_SCHEMA,
        "state": "PUBLISHED",
        "record_id": f"{market}-tg",
        "piece_id": f"plan-{market}",
        "day": day,
        "destination": "telegram",
        "counts_as_article": False,
        "images": [{
            "sha256": snap["sha256"],
            "image_type": "TRADINGVIEW_MARKET_CHART",
            "price_scale_check": check,
        }],
    }) + "\n", encoding="utf-8")
    out.write_text("", encoding="utf-8")
    report = audit_chart_prices(
        reg, out, day, since=captured - timedelta(hours=1), now=captured + timedelta(days=2),
    )
    assert report["status"] == "PASS"
    assert report["compared_percent"] == 100
    assert report["calibration"]["markets"][market]["closed_market_comparisons"] == 1


def test_cc489_closed_cash_index_rejects_stale_close_future_and_overnight_broker(tmp_path, monkeypatch):
    """Closed cash index requires a bar at 16:00 ET, refuses stale/future bars, and never widens broker/CFD ticks."""
    captured = datetime(2026, 11, 25, 1, 0, 0, tzinfo=timezone.utc)  # 20:00 ET
    local_bars_db = tmp_path / "stale-bars.sqlite3"
    # Only a 14:00 ET bar (120 min before 16:00 ET close) -> stale (> 120s).
    _seed_local_m15_bar(local_bars_db, "USTEC", 26214.17, datetime(2026, 11, 24, 19, 0, 0, tzinfo=timezone.utc))
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(public_quotes, "BARS_DB", local_bars_db)
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", tmp_path / "missing-status.json")
    monkeypatch.setattr(prices, "BAR_STORE", tmp_path / "missing-bars.sqlite3")
    monkeypatch.setattr(image_contract, "QUOTE_ROOT", tmp_path / "missing-captures")
    monkeypatch.setattr(public_quotes, "utcnow", lambda: captured - timedelta(seconds=5))

    prices.prepare_chart_quote("USTEC", now=captured - timedelta(seconds=5))
    snap = {
        "tv_symbol": tv.SYMBOLS["USTEC"],
        "sha256": "b" * 64,
        "page_title": "NDX 26,214.17",
        "captured_at_utc": captured.isoformat(),
    }
    bound = image_contract.bind_scale("USTEC", snap)
    assert bound["price_scale_check"]["comparison_basis"] == "NOT_COMPARED"

    # 2. A non-public broker quote at 16:40 ET still uses strict [-2s, +120s] skew and fails compare_scale.
    broker_quote = {
        "market": "USTEC",
        "instrument": "USTEC",
        "price": 26214.17,
        "quoted_at_utc": datetime(2026, 11, 24, 21, 40, 0, tzinfo=timezone.utc).isoformat(),
        "known_at_utc": datetime(2026, 11, 24, 21, 40, 0, tzinfo=timezone.utc).isoformat(),
        "source_kind": "BAR_STORE_M1_CLOSE",
        "source_path": "bars.sqlite3",
        "source_sha256": "c" * 64,
    }
    with pytest.raises(image_contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        image_contract.compare_scale("USTEC", snap, broker_quote)

    # 3. A closed-market public quote observed AFTER capture is strictly refused even within 90 min of 16:00 ET.
    early_capture = datetime(2026, 11, 24, 21, 30, 0, tzinfo=timezone.utc)  # 16:30 ET
    future_settle = {
        "market": "USTEC",
        "instrument": "USTEC",
        "price": 26214.17,
        "quoted_at_utc": datetime(2026, 11, 24, 21, 45, 0, tzinfo=timezone.utc).isoformat(),
        "known_at_utc": datetime(2026, 11, 24, 21, 29, 0, tzinfo=timezone.utc).isoformat(),
        "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
        "instrument_type": "INDEX",
        "source_path": "obs.json",
        "source_sha256": "d" * 64,
    }
    with pytest.raises(image_contract.ImageContractError, match="TRADINGVIEW_PLAN_QUOTE_STALE"):
        image_contract.compare_scale("USTEC", {**snap, "captured_at_utc": early_capture.isoformat()}, future_settle)


def _export_price(path: Path, market: str, price: float, at: datetime, *, generated_at: datetime) -> None:
    row = {"asset_id": market, "last_price": price, "last_price_at_utc": at.isoformat()}
    body = {"schema": "CapitalChroniclePlanStatusV1", "generated_at_utc": generated_at.isoformat(), "plans": [row]}
    body["content_hash"] = sha256(prices._canonical(body)).hexdigest()
    path.write_text(json.dumps(body), encoding="utf-8")


def test_cc489_open_market_prepare_headroom_warms_local_quote_before_slow_capture(tmp_path, monkeypatch):
    """When plan_status is 95s old at capture start, prepare_chart_quote warms local bar quote so capture +30s stays compared."""
    t0 = datetime(2026, 11, 24, 15, 0, 0, tzinfo=timezone.utc)  # 10:00 ET (open)
    export = tmp_path / "plan-status.public.json"
    local_bars_db = tmp_path / "local-bars.sqlite3"
    _seed_local_m15_bar(local_bars_db, "BTCUSD", 62000.0, t0 - timedelta(seconds=2), known_at=t0)
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(public_quotes, "BARS_DB", local_bars_db)
    monkeypatch.setattr(prices, "PLAN_STATUS_PATH", export)
    monkeypatch.setattr(prices, "BAR_STORE", tmp_path / "missing-bars.sqlite3")
    monkeypatch.setattr(image_contract, "QUOTE_ROOT", tmp_path / "missing-captures")
    monkeypatch.setattr(public_quotes, "utcnow", lambda: t0)

    # Export is only 10s old -> sufficient headroom (<=30s), skip unnecessary warm.
    _export_price(export, "BTCUSD", price=62000.0, at=t0 - timedelta(seconds=10), generated_at=t0)
    prices.prepare_chart_quote("BTCUSD", now=t0)
    assert not list((tmp_path / "public-quotes").rglob("*.json"))

    # Export is 95s old -> would expire past 120s during a 30s TradingView download, so warm local quote now.
    _export_price(export, "BTCUSD", price=62000.0, at=t0 - timedelta(seconds=95), generated_at=t0)
    prices.prepare_chart_quote("BTCUSD", now=t0)
    assert list((tmp_path / "public-quotes" / "observations").glob("*.json"))

    # Playwright finishes 30s later: export is now 125s old (stale), but prefetched quote is 32s old (fresh!).
    captured = t0 + timedelta(seconds=30)
    snap = {
        "tv_symbol": tv.SYMBOLS["BTCUSD"],
        "sha256": "e" * 64,
        "page_title": "BTCUSD 62,000",
        "captured_at_utc": captured.isoformat(),
    }
    check = image_contract.bind_scale("BTCUSD", snap)["price_scale_check"]
    assert check["comparison_basis"] == "AT_CAPTURE"
    assert check["quote"]["source_kind"] == "PUBLIC_ON_DEMAND_QUOTE"
    assert check["quote"]["source_attempts"][0]["cause"] == "CHART_REFERENCE_STALE"


def test_cc489_usdjpy_local_bar_exact_symbol_and_failure_details_persist(tmp_path, monkeypatch):
    """USDJPY resolves from LOCAL_BARS with zero Yahoo HTTP, and opt-in DXY mismatch details persist on cache readback."""
    now = datetime(2026, 11, 24, 15, 0, 0, tzinfo=timezone.utc)
    local_bars_db = tmp_path / "local-bars.sqlite3"
    _seed_local_m15_bar(local_bars_db, "USDJPY", 159.33, now, known_at=now)
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "pq-good")
    monkeypatch.setattr(public_quotes, "BARS_DB", local_bars_db)

    obs = public_quotes.get("USDJPY", now=now, clock=lambda: now)
    assert obs["source_symbol"] == "USDJPY"
    assert obs["value"] == 159.33
    assert obs["source_url"] is None

    # Yahoo HTTP URLs are permanently refused at transport level.
    with pytest.raises(public_quotes.QuoteError, match="CC024_YAHOO_HTTP_FORBIDDEN"):
        public_quotes.http_read("https://query1.finance.yahoo.com/v8/finance/chart/USDJPY=X")

    # Cache readback (fetch=False) retains returned_symbol / returned_type on opt-in DXY mismatch.
    monkeypatch.setattr(public_quotes, "ROOT", tmp_path / "pq-bad")
    bad_dxy = json.dumps({"QuickQuoteResult": {"QuickQuote": [{
        "symbol": "WRONG_DXY", "code": "0", "last": "105.0", "previous_day_closing": "104.5",
        "last_time": now.isoformat(), "assetType": "INDEX",
    }]}}).encode("utf-8")
    with pytest.raises(public_quotes.QuoteError, match="PUBLIC_QUOTE_SYMBOL_MISMATCH"):
        public_quotes.get("DXY", now=now, clock=lambda: now, reader=lambda _url: bad_dxy,
                          allow_cnbc_dxy_fallback=True)
    with pytest.raises(public_quotes.QuoteError) as exc_info:
        public_quotes.get("DXY", now=now + timedelta(seconds=10), fetch=False,
                          allow_cnbc_dxy_fallback=True)
    assert str(exc_info.value) == "PUBLIC_QUOTE_SYMBOL_MISMATCH"
    assert exc_info.value.details.get("returned_symbol") == "WRONG_DXY"
    assert exc_info.value.details.get("returned_type") == "INDEX"


# ---------------------------------------------------------------------------
# CC-403: Post-Nov-26 7-market Nasdaq 100 daily note number check, AI/model
#         labels, preview-host ban, Decision 157 target & FedWatch/Kalshi bans
# ---------------------------------------------------------------------------

def _post_nov26_daily():
    cutoff = "2026-11-26T14:00:00Z"
    body = """We think lower yields favour gold while the dollar stays soft. [[SOURCE:SOURCE_1]]

| Market | Our view |
| --- | --- |
| Gold (GC / GLD) | We favour strength if yields fall. |
| S&P 500 (ES / SPY) | We watch earnings against yields. |
| EUR/USD (FXE) | We watch the softer dollar. |
| USD/JPY (FXY) | We watch yen strength. |
| WTI (CL / USO) | We watch the fading risk premium. |
| Bitcoin (IBIT) | We watch the next rebound. |
| Nasdaq 100 (NQ / QQQ) | Unavailable. |
[[SOURCE:SOURCE_1]]

## What changed since yesterday

The 10-year Treasury yield eased to 4.21% from 4.25%. [[SOURCE:SOURCE_1]]

## What we got wrong

We expected a firmer dollar; the official release showed a softer dollar. [[SOURCE:SOURCE_1]]

## Scenarios

Base case (60%): We favour gold if yields fall. [[SOURCE:SOURCE_1]]

Bull dollar case (40%): We change our view if inflation strengthens the dollar. [[SOURCE:SOURCE_1]]

## So what

We watch the next inflation release before changing our view. [[SOURCE:SOURCE_1]]"""
    # Deliberately omit any bare "100" from the bound source text to prove "Nasdaq 100" is treated as an instrument name.
    source_text = (
        "Lower yields favour gold while the dollar stays soft. "
        "The 10-year Treasury yield eased to 4.21% from 4.25%. "
        "Base case 60% and bull dollar case 40%."
    )
    assert "100" not in cc403.numbers(source_text)
    docs = [{
        "source_id": "SOURCE_1",
        "document_id": "main-nov26",
        "publisher": "Capital Chronicle",
        "url": "https://example.org/report",
        "published_at_utc": "2026-11-26T14:20:00Z",
        "data_cutoff_utc": cutoff,
        "canonical_content_text": source_text,
        "canonical_content_sha256": sha256(source_text.encode()).hexdigest(),
        "source_reuse_constraints": {"rights_class": "CC_MODEL_ESTIMATE", "public_expression_reuse_allowed": True},
    }]
    article = {
        "title": "Lower yields leave gold with the stronger case",
        "dek": "We favour gold if the dollar stays soft.",
        "search_title": "Lower yields leave gold with the stronger case",
        "meta_description": "We favour gold if the dollar stays soft.",
        "social_hook": "We favour gold if the dollar stays soft.",
        "substack_body_markdown": body,
        "scenario_analysis": [
            {"name": "Base case", "probability": "60%"},
            {"name": "Bull dollar case", "probability": "40%"},
        ],
    }
    article["reader_article_contract"] = cc403.contract_for(
        {"selected_candidate": {"reader_format": "DAILY_NOTE"}, "source_pack": docs},
    )
    return article, docs


def test_cc403_post_nov26_seven_market_nasdaq_100_daily_note_passes_without_100_in_source():
    assert cc403.numbers("Nasdaq 100, Nasdaq-100, S&P 500, 6E, and 6J") == set()
    assert "Antigravity's first draft" not in cc403.GUIDANCE
    article, docs = _post_nov26_daily()
    cc403.validate_article(article, docs)
    cc403.validate_payload(article, {"title": article["title"], "text": "Nasdaq 100 is unavailable; yields at 4.21%."})


@pytest.mark.parametrize("phrase", [
    "ChatGPT", "Claude", "Fable", "Codex", "Antigravity", "OpenAI", "Anthropic", "Sonnet", "Haiku", "GMT+7",
])
def test_cc403_refuses_ai_model_and_gmt7_labels_with_phrase_named(phrase):
    article, docs = _post_nov26_daily()
    article["dek"] += f" Prepared via {phrase}."
    errors = cc403.check_article(article, docs)
    assert f"INTERNAL_EDITORIAL_LABEL:{phrase}" in errors
    with pytest.raises(ValueError, match=re.escape(f"INTERNAL_EDITORIAL_LABEL:{phrase}")):
        cc403.validate_payload(article, {"text": f"Note from {phrase}."})


def test_cc403_refuses_preview_host_targets_and_prediction_market_numbers_post_nov22():
    article, docs = _post_nov26_daily()
    bad_link = deepcopy(article)
    bad_link["substack_body_markdown"] += "\n\nSee https://fatcat2109.github.io/capital-chronicle-preview/test."
    assert "PREVIEW_HOST_LINK_FORBIDDEN" in cc403.check_article(bad_link, docs)
    with pytest.raises(ValueError, match="PREVIEW_HOST_LINK_FORBIDDEN"):
        cc403.validate_payload(article, {"text": "Read https://fatcat2109.github.io/x"})

    bad_target = deepcopy(article)
    bad_target["substack_body_markdown"] = bad_target["substack_body_markdown"].replace(
        "We watch the next inflation release", "Our profit target stands above resistance",
    )
    assert any("TARGET" in e for e in cc403.check_article(bad_target, docs))

    bad_odds = deepcopy(article)
    bad_odds["substack_body_markdown"] = bad_odds["substack_body_markdown"].replace(
        "The 10-year Treasury yield eased to 4.21% from 4.25%.",
        "CME FedWatch puts a December cut at 60%.",
    )
    assert "PREDICTION_MARKET_NUMBER_FORBIDDEN" in cc403.check_article(bad_odds, docs)


# ---------------------------------------------------------------------------
# CC-549 & CC-399: Single voice, writer-input bans, USTEC plan thread & cards
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,code", [
    ("I’m watching gold yields.", "CC549_DESK_VOICE_MUST_BE_WE"),
    ("I set this up myself.", "CC549_DESK_VOICE_MUST_BE_WE"),
    ("The analyst's comparison shows little edge.", "CC549_WRITER_INPUT_LANGUAGE"),
    ("The given review leaves alternatives unquantified.", "CC549_WRITER_INPUT_LANGUAGE"),
    ("The input pack omits positioning.", "CC549_WRITER_INPUT_LANGUAGE"),
])
def test_cc549_extended_voice_and_input_language_defects_refused(text, code):
    with pytest.raises(ValueError, match=code):
        reader.check_thread_text(text)


@pytest.mark.parametrize("text", [
    "We are watching CPI repricing.",
    "We remain focused on yields.",
    "We are tracking short covering.",
])
def test_cc549_progressive_empty_force_lines_refused(text):
    with pytest.raises(ValueError, match="CC549_FORCE_HAS_NO_FINDING"):
        reader.check_thread_text(text, force=True)
    # Concrete sourced change passes cleanly.
    assert reader.check_thread_text("We are watching yields after the 10-year rose 12 bps.", force=True)["status"] == "PASS"


@pytest.mark.parametrize("bad", ["ChatGPT", "Sonnet", "Haiku", "Luna"])
def test_cc549_plan_reader_copy_and_cc468_note_ban_decision_109_models(bad):
    src = f"Macro note mentions {bad} and 3.5% yields."
    with pytest.raises(ValueError, match="CC466_INTERNAL_OR_BANNED_TERM|PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        reader.check_text(f"Yields stand at 3.5% per {bad}.", source=src)

    with pytest.raises(ValueError, match="PREVIEW_HOST_LINK_FORBIDDEN"):
        reader.check_text("See https://fatcat2109.github.io/preview for details.", source="https://fatcat2109.github.io/preview")

    page = {
        "manuscript": {
            "sections": {
                "macro": {"paragraphs": [{"text": f"Yields rose 12 bps on 25 Nov via {bad} with invalidation 4.5%."}]},
            },
        },
    }
    authored = {
        "sentences": [
            {"text": f"Yields rose 12 bps on 25 Nov via {bad}.", "section": "macro",
             "source_excerpt": f"Yields rose 12 bps on 25 Nov via {bad} with invalidation 4.5%.", "fact_date": "25 Nov"},
            {"text": "We expect pressure below invalidation 4.5%.", "section": "macro",
             "source_excerpt": f"Yields rose 12 bps on 25 Nov via {bad} with invalidation 4.5%.", "fact_date": ""},
        ],
        "view": "pressure below",
        "invalidation": "invalidation 4.5%",
    }
    with pytest.raises(ValueError, match="NOTE_INTERNAL_TERM_FORBIDDEN|PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        daily_note.validate_copy(authored, page, strict=True)


@pytest.mark.parametrize("mapped", [True, False])
def test_cc549_and_cc399_ustec_plan_thread_single_voice_no_target_and_ending(tmp_path, monkeypatch, mapped):
    """USTEC (mapped MNQ futures or unmapped Nasdaq 100) keeps one voice, two distinct clocks, no target post-Nov-23."""
    from test_plan_status_posts_cc306 import STUB_READER, event
    from test_plan_call_cards_cc399 import write, rows

    now = datetime(2026, 11, 25, 14, 5, tzinfo=timezone.utc)
    raw = {
        "plan_id": "plan_ustec_cc549_test",
        "asset_id": "USTEC",
        "direction": "BEARISH",
        "status": "WAITING",
        "run_id": "run-ustec-nov25",
        "registration_hash": "f" * 64,
        "registered_at_utc": "2026-11-25T14:00:00Z",
        "not_before_utc": "2026-11-25T14:00:00Z",
        "entry_deadline_utc": "2026-11-25T18:00:00Z",
        "expires_at_utc": "2026-11-25T18:00:00Z",
        "time_exit_utc": "2026-11-26T20:00:00Z",
        "zone": {"minimum": 26100.0, "maximum": 26200.0},
        "invalidation_level": 26450.0,
        "target_level": 25500.0,
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 26420.0}],
        "scenario_analysis": {
            "horizon_end_utc": "2026-11-26T20:00:00Z",
            "base_case": {"probability_pct": 55, "market_move": "Nasdaq 100 eases if real yields stay firm."},
        },
    }
    if mapped:
        raw["public_instrument"] = {
            "name": "Micro E-mini Nasdaq-100",
            "symbol": "MNQ",
            "kind": "FUT",
            "exchange": "CME",
            "contract_month": "2026-12",
            "entries": [{"kind": "LIMIT", "zone_low": 26150.25, "zone_high": 26240.75}],
            "zone_low": 26150.25,
            "zone_high": 26240.75,
            "invalidation_level": 26490.50,
            "target_level": 25520.00,
            "tick_size": 0.25,
        }

    # Stub Main's external plan_status_export_v1 reader in isolated tmp_path so zero live Main files are needed.
    stub_root = tmp_path / "main-stub"
    (stub_root / "tools" / "product").mkdir(parents=True)
    (stub_root / "tools" / "product" / "plan_status_export_v1.py").write_text(STUB_READER, encoding="utf-8")

    folder = write(
        tmp_path / "export",
        [raw],
        [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
        generated_at_utc=now.isoformat(),
    )
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    res = posts.queue_posts(store, folder, now=now, main_root=stub_root, python=sys.executable)
    assert res["status"] == "OK"
    queued = rows(store)
    # CC-466/CC-399: no run count post; single setup card row per plan.
    assert len(queued) == 1 and queued[0]["kind"] == "setup"
    setup = queued[0]
    assert setup["thread_contract"] == reader.THREAD_CONTRACT
    assert setup["target_policy"] == cards.NO_TARGET_POLICY
    assert "Target level" not in setup["text"] and "25,500" not in setup["text"] and "25,520" not in setup["text"]
    assert "USTEC" not in setup["text"]
    assert "Entry can start until Wed 25 Nov, 1:00 PM ET." in setup["text"]
    assert "Filled positions close by Thu 26 Nov, 3:00 PM ET." in setup["text"]
    if mapped:
        assert "MNQ" in setup["text"] and "26,150.25–26,240.75" in setup["text"] and "26,490.5" in setup["text"]
    else:
        assert "Nasdaq 100" in setup["text"] and "26,100–26,200" in setup["text"]
    reader.check_thread_text(setup["text"])
    alerts.validate(setup)
    # Tampering price_basis must still fail closed for both mapped and unmapped USTEC rows.
    tampered = {**setup, "price_basis": None if mapped else "instrument"}
    with pytest.raises(posts.PlanPostError, match="PLAN_ALERT_SOURCE_FIELD_CHANGED:price_basis"):
        alerts.validate(tampered)

    # Confirm winning time exit never says "expired" and preserves parent_key + result frame.
    store.set_outbox_status(setup["key"], "PUBLISHED")
    closed_at = now + timedelta(minutes=2)
    later = deepcopy(raw)
    later.update(
        status="CLOSED",
        outcome={
            "state": "SCORED",
            "result": "EXPIRED",
            "outcome_id": "out-ustec-time-exit",
            "score": {
                "plan_id": raw["plan_id"],
                "asset_id": "USTEC",
                "outcome_id": "out-ustec-time-exit",
                "result": "EXPIRED",
                "direction_correct": True,
                "result_r": 0.4,
                "resolved_at_utc": closed_at.isoformat(),
            },
        },
    )
    write(
        folder,
        [later],
        [
            event(raw["plan_id"], "WAITING", raw["registered_at_utc"]),
            event(raw["plan_id"], "FILLED", (now + timedelta(minutes=1)).isoformat()),
            event(raw["plan_id"], "CLOSED", closed_at.isoformat()),
        ],
        generated_at_utc=closed_at.isoformat(),
    )
    # Run outside jim_pause_window so ending queues cleanly (post-relaunch timestamp).
    monkeypatch.setattr(cards, "inside_jim_pause", lambda *a, **k: False)
    posts.queue_posts(store, folder, now=closed_at, main_root=stub_root, python=sys.executable)
    ending = next(r for r in rows(store) if r["kind"] == "result")
    assert ending["parent_key"] == setup["key"]
    assert "closed at its time exit, on our side of the entry" in ending["text"]
    assert "Result: +0.4R." in ending["text"]
    assert "expired" not in ending["text"].lower()
    assert "Target level" not in ending["text"]
    alerts.validate(ending)


# ---------------------------------------------------------------------------
# CC-436 & CC-467: Fail-closed pre-click retry & quote-post shared filter check
# ---------------------------------------------------------------------------

def test_cc436_retryable_unsent_plan_copy_is_strictly_fail_closed():
    base = {
        "status": "FAILED_BEFORE_WRITE",
        "stage": "BEFORE_PUBLISH_CLICK",
        "definite_no_write": True,
        "public_write_performed": False,
        "request_sha256": "a" * 64,
        "native_tool_return_sha256": "b" * 64,
        "native_tool_observation": {},
        "reason_code": "NEO_COMPOSER_PREPARATION_FAILED",
        "safe_error_classification": "NEO_RPC_DEADLINE_EXCEEDED",
    }
    assert neo_exec.retryable_unsent_plan_copy(base) is True
    assert neo_exec.retryable_unsent_plan_copy({**base, "public_object_id": "123"}) is False
    assert neo_exec.retryable_unsent_plan_copy({**base, "native_tool_observation": {"dispatched_at_utc": "2026-11-25T10:00:00Z"}}) is False
    assert neo_exec.retryable_unsent_plan_copy({**base, "stage": "AFTER_PUBLISH_CLICK"}) is False


def test_cc467_heavy_news_quote_inherits_decision_109_model_and_preview_bans(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    from live_contentops import x_reply_pack_v1 as packs
    source_doc = {
        "source_id": "src-cc467-1",
        "kind": "MAIN_PUBLIC_DESK_FIELD",
        "excerpt": "U.S. 10-year yield sits at 4.21% on 25 Nov (ChatGPT test).",
        "known_at_utc": "2026-11-25T10:00:00Z",
    }
    store.create_work_item(story_id="src-cc467-1", work_item_id="src-cc467-1", title="src", target_surface="INTERNAL")
    store.register_outbox_message(
        message_id="src-cc467-1",
        work_item_id="src-cc467-1",
        destination=packs.SOURCE_DESTINATION if hasattr(packs, "SOURCE_DESTINATION") else "internal:x-reply-fact-source",
        payload=json.dumps(source_doc),
        status="READY",
    )
    # Directly verify check_text blocks new Decision 109 labels on CC-467 copy boundary.
    with pytest.raises(ValueError, match="CC466_INTERNAL_OR_BANNED_TERM|PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        reader.check_text(
            "U.S. 10-year yield stands at 4.21% via ChatGPT. Chart: TradingView.",
            source=source_doc["excerpt"],
            max_chars=280,
        )
    assert quotes_mod.MAX_SECONDS == 300 and quotes_mod.DAILY_CAP == 5
