"""CC-463 / decision 124: the image contract at the sole write boundary.

This module validates the existing chart service's output. It neither dispatches
posts nor obtains broker data. Saved Main quotes are used only for the displayed
price-scale comparison; no terminal, account or order API is imported.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

POLICY = "CC463_TRADINGVIEW_FIRST_V1"
EFFECTIVE_FROM = datetime(2026, 11, 11, 14, 39, tzinfo=timezone.utc)
QUOTE_SKEW_SECONDS = 120
QUOTE_ROOT = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research")
# Percentage differences, not fractions. Initial limits and the retained
# observations (including their clock separation) are in CC-463/README.md.
# CC-788: the Nasdaq 100 starts at the S&P 500's equity-index limit; no simultaneous USTEC/NDX pair is held yet.
MAX_DIFFERENCE_PCT = {"XAUUSD": .15, "US500": .15, "EURUSD": .15,
                      "USDJPY": .15, "USOIL": .40, "BTCUSD": .40, "USTEC": .15}
CASH_INDEX_MARKETS = frozenset({"US500", "USTEC"})
CASH_CALENDAR = Path(r"A:\Capital Chronicle\main-jim-research-dashboard-20261025\config\ibkr_paper\us_session_calendar_v1.json")
US_CASH_OPEN_ET = time(9, 30)
US_CASH_CLOSE_ET = time(16, 0)
US_CASH_EARLY_CLOSE_ET = time(13, 0)
_US_CASH_CALENDAR_CACHE: tuple[str, bytes, dict] | None = None
# Yahoo Finance's official cash-index closing settlement prints (^GSPC / ^NDX) regularly post
# between 16:00 and 17:20 ET (up to ~76 min past the 16:00 ET regular-session close). Allow up
# to 90 min ONLY for closed-market PUBLIC_ON_DEMAND_QUOTE INDEX checks (still requiring
# observed <= known <= capture, never loosening open-market or 24h CFD/futures broker quotes).
CASH_INDEX_CLOSE_SETTLE_SECONDS = 5400
# Ops Product, 11 Nov 2026: a missing quote is not a mismatch. Main saves a quote only during its own runs, so on the
# first live run (16:24Z) every chart was refused and five posts went out as text. A chart with no quote to compare
# is still the right market's chart: it goes out marked NOT_COMPARED. Only a measured difference refuses an image.
QUOTE_ABSENT = ("TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE", "TRADINGVIEW_LAST_CLOSE_MAIN_QUOTE_UNAVAILABLE")
ET = ZoneInfo("America/New_York")


class ImageContractError(ValueError):
    def __init__(self, cause, **details):
        super().__init__(cause)
        self.details = details


def write_refusal(error):
    if isinstance(error, ImageContractError):
        return error
    details = {"exception_type": type(error).__name__, "first_cause": str(error)}
    if isinstance(error, OSError) and error.filename is not None:
        details["filename"] = str(error.filename)
    return ImageContractError("PUBLICATION_IMAGE_CONTRACT_INVALID", **details)


def utc(value):
    if isinstance(value, datetime):
        at = value
    else:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ImageContractError("TRADINGVIEW_PRICE_CLOCK_REQUIRED")
    return at.astimezone(timezone.utc)


def number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ImageContractError("TRADINGVIEW_PRICE_NOT_VALID") from None
    if isinstance(value, bool) or not math.isfinite(result) or result <= 0:
        raise ImageContractError("TRADINGVIEW_PRICE_NOT_VALID")
    return result


def chart_last_price(title):
    # The displayed last price in the guest chart's title, never a bar series.
    match = re.match(r"^\S+\s+([\d,]+(?:\.\d+)?)(?:\s|$)", str(title))
    if not match:
        raise ImageContractError("TRADINGVIEW_LAST_PRICE_NOT_VISIBLE")
    return number(match[1].replace(",", ""))


def _observed_us_holiday(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _easter_sunday(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    return date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def _fallback_us_cash_year(year: int) -> tuple[frozenset[str], frozenset[str]]:
    """Deterministic NYSE equity holiday & 13:00 ET early-close fallback when the JSON is absent."""
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    memorial_end = date(year, 5, 31)
    closed: set[date] = {
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter_sunday(year) - timedelta(days=2),
        memorial_end - timedelta(days=memorial_end.weekday()),
        _observed_us_holiday(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        thanksgiving,
        _observed_us_holiday(date(year, 12, 25)),
    }
    jan1 = date(year, 1, 1)
    if jan1.weekday() < 5:
        closed.add(jan1)
    elif jan1.weekday() == 6:
        closed.add(date(year, 1, 2))
    # NYSE does not observe a Saturday New Year's Day on the preceding Friday Dec 31.
    if year >= 2022:
        closed.add(_observed_us_holiday(date(year, 6, 19)))
    early: set[date] = {thanksgiving + timedelta(days=1)}
    for eve in (date(year, 7, 3), date(year, 12, 24)):
        if eve.weekday() < 5 and eve not in closed:
            early.add(eve)
    return (
        frozenset(d.isoformat() for d in closed),
        frozenset(d.isoformat() for d in early),
    )


def _valid_iso_date_list(value) -> frozenset[str] | None:
    if not isinstance(value, list):
        return None
    parsed = set()
    for item in value:
        if not isinstance(item, str) or len(item) != 10:
            return None
        try:
            date.fromisoformat(item)
        except ValueError:
            return None
        parsed.add(item)
    return frozenset(parsed)


def _read_us_cash_calendar(calendar_path=None) -> dict | None:
    """Read-only loader for us_session_calendar_v1.json; returns None on missing or invalid file."""
    global _US_CASH_CALENDAR_CACHE
    path = Path(CASH_CALENDAR if calendar_path is None else calendar_path)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    key = str(path)
    if _US_CASH_CALENDAR_CACHE is not None and _US_CASH_CALENDAR_CACHE[0] == key and _US_CASH_CALENDAR_CACHE[1] == raw:
        return _US_CASH_CALENDAR_CACHE[2]
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if "schema" in data and data["schema"] != "IbkrUsSessionCalendarV1":
        return None
    if not isinstance(data.get("years"), dict):
        return None
    _US_CASH_CALENDAR_CACHE = (key, raw, data)
    return data


def _us_cash_year_dates(year: int, *, calendar_path=None, calendar=None) -> tuple[frozenset[str], frozenset[str]]:
    if calendar is not None:
        data = calendar if (isinstance(calendar, dict)
                            and ("schema" not in calendar or calendar["schema"] == "IbkrUsSessionCalendarV1")) else None
    else:
        data = _read_us_cash_calendar(calendar_path)
    if isinstance(data, dict):
        years = data.get("years")
        entry = years.get(str(year)) if isinstance(years, dict) else None
        if isinstance(entry, dict):
            closed = _valid_iso_date_list(entry.get("closed"))
            early = _valid_iso_date_list(entry.get("early_close_13_et"))
            if closed is not None and early is not None:
                return closed, early
    return _fallback_us_cash_year(year)


def us_cash_session_bounds(day: date, *, calendar_path=None, calendar=None) -> tuple[time, time] | None:
    """Return (open_et, close_et) for a US cash equity session day, or None if weekend/holiday closed."""
    if day.weekday() >= 5:
        return None
    closed, early = _us_cash_year_dates(day.year, calendar_path=calendar_path, calendar=calendar)
    iso = day.isoformat()
    if iso in closed:
        return None
    if iso in early:
        return US_CASH_OPEN_ET, US_CASH_EARLY_CLOSE_ET
    return US_CASH_OPEN_ET, US_CASH_CLOSE_ET


def _prior_us_cash_close(start_day: date, *, calendar_path=None, calendar=None) -> datetime:
    day = start_day
    for _ in range(31):
        bounds = us_cash_session_bounds(day, calendar_path=calendar_path, calendar=calendar)
        if bounds is not None:
            return datetime.combine(day, bounds[1], ET).astimezone(timezone.utc)
        day -= timedelta(days=1)
    day = start_day
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return datetime.combine(day, US_CASH_CLOSE_ET, ET).astimezone(timezone.utc)


def comparison_clock(market, captured_at, *, calendar_path=None, calendar=None):
    """Ops Product's 11 Nov closed-market amendment; ET, including DST and US cash holidays.

    Cash SPX and NDX use NYSE cash hours (09:30–16:00 ET weekdays, 09:30–13:00 ET on
    early-close days, closed on US equity holidays per us_session_calendar_v1.json with
    deterministic NYSE fallback when absent). The common weekend closure for the other
    non-crypto charts uses Friday 17:00 through Sunday 18:00. No live broker/chart gap
    is compared while a chart is frozen at that close.
    """
    captured = utc(captured_at)
    local = captured.astimezone(ET)
    if market == "BTCUSD":
        return captured, False
    if market in CASH_INDEX_MARKETS:
        bounds = us_cash_session_bounds(local.date(), calendar_path=calendar_path, calendar=calendar)
        if bounds is not None:
            open_et, close_et = bounds
            if open_et <= local.time() < close_et:
                return captured, False
            if local.time() >= close_et:
                return datetime.combine(local.date(), close_et, ET).astimezone(timezone.utc), True
        return _prior_us_cash_close(local.date() - timedelta(days=1),
                                    calendar_path=calendar_path, calendar=calendar), True
    if (local.weekday() == 5 or local.weekday() == 6 and local.time() < time(18)
            or local.weekday() == 4 and local.time() >= time(17)):
        friday = local.date() - timedelta(days=(local.weekday() - 4) % 7)
        return datetime.combine(friday, time(17), ET).astimezone(timezone.utc), True
    return captured, False


def saved_main_quote(market, captured_at, *, root=None):
    """Use the nearest exact tick already held by Main, with both clocks bound.

    File discovery is bounded to Main's existing preparation paths, and only
    recently written captures are parsed. No account fields leave this reader.
    An injected root keeps tests completely separate from the operating files.
    """
    capture_at, root = utc(captured_at), Path(root or QUOTE_ROOT)
    at, closed = comparison_clock(market, capture_at)
    paths = []
    for pattern in ("t2-runs/*/request/capture.json", "brain-runs/*/request/capture.json",
                    "brain-runs/*/shadow-driver/request/capture.json",
                    "daily-research-portfolio-*/requests/*/capture.json",
                    "daily-research-portfolio-*/.native-preparation/capture.json"):
        paths.extend(root.glob(pattern))
    candidates = []
    for path in sorted(set(paths), key=lambda p: p.stat().st_mtime, reverse=True):
        if abs(path.stat().st_mtime - at.timestamp()) > QUOTE_SKEW_SECONDS + 60:
            continue
        try:
            raw = path.read_bytes()
            data = json.loads(raw)
            if data.get("schema") != "CapitalChroniclePrimaryDemoAccountCaptureV1":
                continue
            if data.get("content_hash") != sha256(json.dumps(
                    {k: v for k, v in data.items() if k != "content_hash"},
                    sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                    allow_nan=False).encode()).hexdigest():
                continue
            tick = data.get("ticks", {}).get(market) or {}
            tick_at = datetime.fromtimestamp(
                tick["time_msc"] / 1000 if tick.get("time_msc") else tick["time"], timezone.utc)
            bid, ask = number(tick["bid"]), number(tick["ask"])
            known = utc(data["known_at_utc"])
            skew = (at - tick_at).total_seconds()
            if bid > ask or not -2 <= skew <= QUOTE_SKEW_SECONDS or known > capture_at:
                continue
            candidates.append((abs(skew), {"market": market, "instrument": market,
                "price": (bid + ask) / 2, "quoted_at_utc": tick_at.isoformat(),
                "known_at_utc": known.isoformat(), "source_path": str(path.resolve()),
                "source_sha256": sha256(raw).hexdigest(), "source_content_hash": data["content_hash"],
                "price_basis": "plan_feed", "comparison_basis": "LAST_CLOSE" if closed else "AT_CAPTURE",
                "comparison_at_utc": at.isoformat()}))
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            continue
        if len(candidates) >= 3:
            break
    if not candidates:
        raise ImageContractError("TRADINGVIEW_LAST_CLOSE_MAIN_QUOTE_UNAVAILABLE" if closed else
                                 "TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE", market=market,
                                 maximum_clock_skew_seconds=QUOTE_SKEW_SECONDS)
    return min(candidates, key=lambda item: item[0])[1]


def max_negative_skew(market, *, closed, quote=None):
    """Allow same-day closing settlement prints only for closed cash-index public quotes."""
    if (closed and market in CASH_INDEX_MARKETS and isinstance(quote, dict)
            and quote.get("source_kind") == "PUBLIC_ON_DEMAND_QUOTE"
            and quote.get("instrument_type") == "INDEX"):
        return CASH_INDEX_CLOSE_SETTLE_SECONDS
    return 2


def compare_scale(market, snapshot, quote):
    from .tradingview_snapshot_v1 import SYMBOLS
    if market not in SYMBOLS or snapshot.get("tv_symbol") != SYMBOLS[market]:
        raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
    if quote.get("market") != market or quote.get("instrument") != market:
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_INSTRUMENT_MISMATCH")
    historical = snapshot.get('visible_to_utc') is not None
    if historical:
        comparison_at = utc(snapshot['visible_to_utc'])
        if not utc(snapshot['visible_from_utc']) < comparison_at <= utc(snapshot['captured_at_utc']):
            raise ImageContractError('TRADINGVIEW_HISTORICAL_WINDOW_INVALID')
        price = number(snapshot.get('visible_last_price'))
        closed = False
    else:
        price = chart_last_price(snapshot.get("page_title"))
        comparison_at, closed = comparison_clock(market, snapshot["captured_at_utc"])
    own = number(quote.get("price"))
    quoted_at = utc(quote["quoted_at_utc"])
    captured_at = utc(snapshot["captured_at_utc"])
    skew = (comparison_at - quoted_at).total_seconds()
    neg_skew = max_negative_skew(market, closed=closed, quote=quote)
    if (not -neg_skew <= skew <= QUOTE_SKEW_SECONDS
            or utc(quote["known_at_utc"]) > captured_at
            or (neg_skew > 2 and quoted_at > captured_at)):
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_STALE", clock_skew_seconds=skew)
    if not quote.get("source_path") or not quote.get("source_sha256"):
        raise ImageContractError("TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED")
    difference = price - own
    difference_pct = abs(difference) / own * 100
    result = {"policy": POLICY, "market": market, "tv_symbol": SYMBOLS[market],
        "chart_sha256": snapshot["sha256"], "chart_price": price, "quote": dict(quote),
        "captured_at_utc": snapshot["captured_at_utc"], "clock_skew_seconds": skew,
        "comparison_basis": "VISIBLE_WINDOW_CLOSE" if historical else "LAST_CLOSE" if closed else "AT_CAPTURE",
        "comparison_at_utc": comparison_at.isoformat(),
        **({'visible_from_utc':utc(snapshot['visible_from_utc']).isoformat(),
            'visible_to_utc':comparison_at.isoformat()} if historical else {}),
        "difference": difference, "difference_pct": difference_pct,
        "maximum_difference_pct": MAX_DIFFERENCE_PCT[market],
        "level_offset": difference if market == "USOIL" and quote.get("price_basis") != "chart_futures" else 0.}
    if difference_pct > MAX_DIFFERENCE_PCT[market]:
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_MISMATCH", **result)
    return result


def not_compared(market, snapshot, cause, source_attempts=None):
    """The binding of a chart that had no quote to compare with: the right symbol, and no level offset."""
    from .tradingview_snapshot_v1 import SYMBOLS
    if market not in SYMBOLS or snapshot.get("tv_symbol") != SYMBOLS[market]:
        raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
    return {"policy": POLICY, "market": market, "tv_symbol": SYMBOLS[market], "chart_sha256": snapshot["sha256"],
            "captured_at_utc": snapshot["captured_at_utc"], "comparison_basis": "NOT_COMPARED",
            "quote_absent_cause": cause, "level_offset": 0.,
            **({"quote_source_attempts": source_attempts} if source_attempts is not None else {})}


def bind_scale(market, snapshot, *, quote=None):
    from .chart_price_reference_v1 import saved_chart_quote
    snapshot = dict(snapshot)
    try:
        snapshot["price_scale_check"] = compare_scale(market, snapshot,
            quote if quote is not None else saved_chart_quote(market, snapshot["captured_at_utc"]))
    except ImageContractError as error:
        if quote is not None or str(error) not in QUOTE_ABSENT:
            raise
        snapshot["price_scale_check"] = not_compared(market, snapshot, str(error),
                                                   error.details.get("source_attempts"))
    return snapshot


def validate_scale(market, snapshot):
    check = snapshot.get("price_scale_check") or {}
    if check.get("policy") != POLICY:
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_CHECK_REQUIRED")
    if check.get("comparison_basis") == "NOT_COMPARED":
        if check != not_compared(market, snapshot, check.get("quote_absent_cause"),
                                check.get("quote_source_attempts")):
            raise ImageContractError("TRADINGVIEW_PRICE_SCALE_BINDING_CHANGED")
        return check
    if check != compare_scale(market, snapshot, check.get("quote") or {}):
        raise ImageContractError("TRADINGVIEW_PRICE_SCALE_BINDING_CHANGED")
    return check


ARTICLE_CARD_FALLBACK = "ARTICLE_FACT_CARD_FALLBACK"


def image_type(asset):
    snapshot = asset.get("tradingview_snapshot") or {}
    symbol = str(snapshot.get("tv_symbol") or "")
    if asset.get("modality") == "tradingview_chart_snapshot":
        return "TRADINGVIEW_ECONOMIC_CHART" if symbol.startswith(("ECONOMICS:", "FRED:")) else "TRADINGVIEW_MARKET_CHART"
    if asset.get("modality") == "fred_graph":
        return "FRED_GRAPH"
    if asset.get("modality") == "documentary_photo":
        return "PHOTO"
    if asset.get("article_chart_fallback"):
        return ARTICLE_CARD_FALLBACK  # CC-777: the article's own card after its capture failed (decision 82)
    if asset.get("card_kind") or asset.get("modality") in {
            "source_bound_data_card", "source_backed_chart", "plan_fact_card", "plan_call_card"}:
        return "DRAWN_CARD"
    return "OTHER"


def _macro(article, intent):
    decision = article.get("visual_editorial_decision") or {}
    return bool(article.get("macro_data_post") or article.get("release_analysis")
        or article.get("article_type") in {"EVENT_PREVIEW", "EVENT_REVIEW"}
        or decision.get("analysis_scope") == "RELEASE_OR_POLICY" or intent.get("event_pack"))


def scope(store, intent, article):
    from .tradingview_snapshot_v1 import SYMBOLS
    if intent.get("plan_status_post"):
        from .plan_status_posts_v1 import _row_payload
        row = _row_payload(store, str(intent["plan_status_post"]))
        members = [_row_payload(store, key) for key in row["card_keys"]] if row.get("kind") == "run" else [row]
        return {m["symbol"]: m for m in members if m.get("symbol") in SYMBOLS}, False
    market = (article.get("market_asset") or intent.get("market_asset")
              or article.get("asset_id") or (article.get("frozen_public_record") or {}).get("asset_id"))
    page_id = intent.get("plan_analysis_page")
    if intent.get("plan_analysis_link"):
        link = store.get_outbox_message(str(intent["plan_analysis_link"]))
        if link:
            page_id = json.loads(link["payload"]).get("page_id")
    if page_id:
        held = store.get_outbox_message(str(page_id))
        if held:
            market = (json.loads(held["payload"]).get("source_plan") or {}).get("asset_id") or market
    if market not in SYMBOLS:
        # Use structured source scope where it exists. Never decide the market
        # from prose or guess one out of a six-market report.
        values = article.get("asset_ids") or intent.get("asset_ids") or []
        values = [values] if isinstance(values, str) else values
        markets = {value for value in values if value in SYMBOLS}
        if len(markets) == 1:
            market = next(iter(markets))
    # Economic releases lead with the source series, even if their analysis also
    # discusses one financial market. Pure market commentary uses its market.
    return ({market: None} if market in SYMBOLS else {}), _macro(article, intent)


def _fred(asset):
    """Accept a source-bound FRED graph, never a locally drawn graph with a label."""
    graph = asset.get("fred_graph") or {}
    url = urlparse(str(graph.get("image_url") or ""))
    series = graph.get("series_ids") or []
    actual = parse_qs(url.query).get("id", [""])[0].split(",")
    source = urlparse(str(asset.get("source_page_url") or ""))
    if (image_type(asset) != "FRED_GRAPH" or url.scheme != "https"
            or url.hostname != "fred.stlouisfed.org" or url.path != "/graph/fredgraph.png"
            or not series or series != actual or source.hostname != "fred.stlouisfed.org"
            or not graph.get("source") or not graph.get("window")
            or "FRED" not in str(asset.get("credit") or "") or not asset.get("rights_basis")
            or not asset.get("sha256") or sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset["sha256"]):
        raise ImageContractError("MACRO_SOURCE_GRAPH_BINDING_INVALID")
    original = Path(str(graph.get("source_path") or ""))
    if not original.is_file() or sha256(original.read_bytes()).hexdigest() != graph.get("source_sha256"):
        raise ImageContractError("MACRO_SOURCE_GRAPH_ORIGINAL_REQUIRED")
    from PIL import Image, ImageChops
    with Image.open(original) as source_image, Image.open(asset["path"]) as delivered:
        if source_image.size != delivered.size or ImageChops.difference(
                source_image.convert("RGB"), delivered.convert("RGB")).getbbox():
            raise ImageContractError("MACRO_SOURCE_GRAPH_PIXELS_CHANGED")


def bounded_text_fallback(article, output_dir, *, now=None):
    if not article.get("tradingview_text_fallback"):
        return None
    return exhausted_capture_state(article, output_dir, now=now)


def exhausted_capture_state(article, output_dir, *, now=None):
    """The article's own bounded capture state, once it ended text-only after its attempts or window."""
    if article.get("publication_image_contract") != POLICY:
        return None
    path =Path(str(article.get("tradingview_capture_state_path") or "")).resolve()
    if not path.is_relative_to(Path(output_dir).resolve()) or not path.is_file():
        return None
    state = json.loads(path.read_bytes())
    market = article.get("macro_chart_symbol") if _macro(article, {}) else article.get("market_asset")
    elapsed = ((now or datetime.now(timezone.utc)) - utc(state["started_at_utc"])).total_seconds()
    if (state.get("key") != article.get("tradingview_capture_key") or state.get("market") != market
            or state.get("status") != "TEXT_ONLY" or not state.get("cause")
            or not (state.get("attempts", 0) >= 2 or elapsed >= 300)):
        return None
    return state


def _plan_capture_states(row, folder, ratio):
    member = folder.parent / row["key"]
    suffix = "_4x5" if ratio == "4:5" else ""
    for template in ("", "_cc465"):
        path = member / f"tradingview_capture{suffix}{template}_v1.json"
        if path.is_file():
            state = json.loads(path.read_bytes())
            if state.get("key") == row["key"] and state.get("market") == row["symbol"]:
                yield state


def _validate_plan_card(asset, row, folder, destination):
    from PIL import Image
    from .plan_status_posts_v1 import plan_facts
    from .tradingview_snapshot_v1 import _sha256

    binding = asset.get("plan_chart_fallback") or {}
    ratio = ("4:5" if destination == "instagram_business" or
             (destination == "threads" and binding.get("ratio") == "4:5") else "16:9")
    if (not row or row.get("format") != 4 or binding.get("key") != row["key"]
            or binding.get("market") != row["symbol"] or binding.get("ratio") != ratio):
        raise ImageContractError("PLAN_CHART_FALLBACK_BINDING_INVALID")
    member = folder.parent / row["key"]
    if not any(state.get("status") == "PLAN_CARD" and state.get("cause") == binding.get("cause")
               for state in _plan_capture_states(row, folder, ratio)):
        raise ImageContractError("PLAN_CHART_FALLBACK_CAPTURE_UNBOUND")
    packet = asset.get("data_card_packet") or {}
    path = Path(asset["path"]).resolve()
    if (packet.get("facts") != [list(fact) for fact in plan_facts(row)]
            or not path.is_relative_to((member / "media_assets").resolve())
            or _sha256(path) != asset["sha256"]):
        raise ImageContractError("PLAN_CHART_FALLBACK_CARD_CHANGED")
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != (asset["width"], asset["height"]) or (
                ratio == "4:5" and image.width * 5 != image.height * 4):
            raise ImageContractError("PLAN_CHART_FALLBACK_IMAGE_INVALID")
    return binding


def _validate_page_card(store, intent, article, asset, folder, now):
    """A plan page's fact card stands in for its chart only after the page's own capture ended text-only."""
    from PIL import Image
    from .tradingview_snapshot_v1 import _sha256, page_card_facts

    held = store.get_outbox_message(str(intent.get("plan_analysis_page") or ""))
    packet = json.loads(held["payload"]) if held else {}
    plan = packet.get("source_plan") or {}
    key = "plan-analysis-" + str(plan.get("plan_id"))
    binding = asset.get("plan_chart_fallback") or {}
    state = bounded_text_fallback(article, folder, now=now)
    if (not state or state.get("key") != key or binding.get("key") != key or binding.get("market") != plan.get("asset_id")
            or binding.get("ratio") != "16:9" or binding.get("cause") != state.get("cause")):
        raise ImageContractError("PLAN_PAGE_CHART_FALLBACK_BINDING_INVALID")
    path = Path(asset["path"]).resolve()
    try:
        facts = page_card_facts(plan, packet.get("active_status") or packet.get("final_status"))
    except (ValueError, KeyError, TypeError):
        facts = None
    if (facts is None or (asset.get("data_card_packet") or {}).get("facts") != facts
            or not path.is_relative_to((Path(folder) / "media_assets").resolve())
            or not path.is_file() or _sha256(path) != asset["sha256"]):
        raise ImageContractError("PLAN_PAGE_CHART_FALLBACK_CARD_CHANGED")
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != (asset["width"], asset["height"]):
            raise ImageContractError("PLAN_PAGE_CHART_FALLBACK_IMAGE_INVALID")
    return binding


def _validate_article_card(article, asset, folder, now):
    """CC-777: an article's own data card stands in for its chart only after its own capture ended text-only."""
    from PIL import Image
    from .tradingview_snapshot_v1 import article_card_refusal

    state = exhausted_capture_state(article, folder, now=now)
    binding = asset.get("article_chart_fallback") or {}
    recorded = article.get("tradingview_card_fallback") or {}
    if (not state or binding.get("key") != state.get("key") or binding.get("market") != article.get("market_asset")
            or binding.get("ratio") != "16:9" or binding.get("cause") != state.get("cause")
            or recorded.get("asset_id") != asset.get("asset_id") or recorded.get("cause") != state.get("cause")):
        raise ImageContractError("ARTICLE_CHART_FALLBACK_BINDING_INVALID")
    refusal = article_card_refusal(asset)
    if refusal:
        raise ImageContractError(refusal)
    with Image.open(asset["path"]) as image:
        if image.format != "PNG" or image.size != (asset.get("width", image.width), asset.get("height", image.height)):
            raise ImageContractError("ARTICLE_CHART_FALLBACK_IMAGE_INVALID")
    return binding


def validate_write(coordinator, intent, destination):
    """Check actual transport-selected media, once, for every fresh post type."""
    if coordinator._clock() < EFFECTIVE_FROM:
        return None
    if intent.get("daily_trend_board"):
        from .daily_trend_board_v1 import validate_media
        return validate_media(coordinator.store, intent)
    if intent.get("output_dir"):
        from .article_publication_quality_v1 import article_inputs
        article, _, _ = article_inputs(intent)
    else:
        article = intent.get("article") or {}
    row = None
    late_chart = False
    if intent.get("plan_status_post"):
        from .plan_call_cards_v1 import ANALYSIS_FIRST_PART, LATE_CHART_PART, _reference
        from .plan_reader_copy_v1 import NINE_LAYER_COPY
        from .plan_status_posts_v1 import _row_payload, validate_status_post_intent
        row = _row_payload(coordinator.store, intent["plan_status_post"])
        part = intent.get("plan_status_part", 0)
        late_chart = row.get("format") == 4 and part == LATE_CHART_PART
        if late_chart:
            validate_status_post_intent(coordinator.store, intent)
        elif row.get("analysis_copy_contract") == NINE_LAYER_COPY and part >= ANALYSIS_FIRST_PART:
            # The exact continuation belongs to the already illustrated plan post.
            # Check the frozen text and confirmed parent before reusing that binding.
            validate_status_post_intent(coordinator.store, intent)
            parent = _reference(coordinator.store, row["key"], destination)
            return {"policy": POLICY, "illustrated_parent_url": parent["public_object_url"]}
        if row.get("kind") == "missing_links_reply" and row.get("cc603_contract") == "CC603_V1":
            # CC-603, Ops Product 16 Nov: one missing-line reply under the
            # already illustrated Note, preserving the original and its chart.
            from .call_followups_v1 import validate_link_reply, destination_payloads
            parent = validate_link_reply(coordinator.store, row)
            if destination != "substack_notes" or intent.get("native_payload") != destination_payloads(row, card_id=None)[destination]:
                raise ImageContractError("CC603_LINK_REPLY_COPY_OR_PARENT_CHANGED")
            return {"policy": "CC603_MISSING_LINK_REPLY", "illustrated_parent_url": parent["public_object_url"]}
    markets, macro = scope(coordinator.store, intent, article)
    if intent.get("output_dir"):
        from ._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
        assets = _durable_intent_inputs(intent)["media_assets"]
    else:
        # CC-548: digests carry their frozen media in the intent and have no
        # article run folder. Keep all scope/template checks below, including
        # the chart requirement for folderless market/release posts.
        assets = intent.get("media_assets") or []
    if intent.get("plan_analysis_link") and not assets:
        # CC-432's exact replies and canonical link previews already point to
        # the illustrated page/card. CC-466 also keeps link/notice replies
        # separate from the chart root. Validate that binding before accepting
        # text; a new root or an attached image keeps the full image contract.
        from .plan_analysis_pages_v1 import validate_link_intent
        link = validate_link_intent(coordinator.store, intent)
        if not link.get("original_analysis_root"):
            return {"policy": POLICY, "confirmed_analysis_link": link["canonical_url"]}
    if destination == "substack":
        assets = [a for a in assets if a.get("article_inclusion") is not False
                  and a.get("canonical_article_media") is not False]
    # CC-465 checks the exact transport-selected PNGs, including table-only
    # scorecards, at the same sole publication boundary as CC-463.
    templates = [a for a in assets if a.get("image_template")]
    if templates:
        if (any(a["image_template"].get("chart") for a in templates)
                and (article.get("paid") or article.get("paywall") or article.get("audience") in {"paid", "paid_subscribers"})):
            raise ImageContractError("PUBLIC_REDISTRIBUTION_NOT_LICENSED")
        from .image_quality_v1 import SINGLE_IMAGE_DESTINATIONS, SAMPLE_NOT_SCORED, sampled_review, validate_asset
        reviewed = []
        for asset in templates:
            needs_vision = True
            bound = article.get("image_input_v1")
            if bound and asset["image_template"]["input"] != bound:
                raise ImageContractError("IMAGE_TEMPLATE_ARTICLE_SOURCE_CHANGED")
            if row and row.get("state_alert_contract") == "CC543_V1":
                from .image_template_inputs_v1 import for_plan_post
                if for_plan_post(row) != asset["image_template"]["input"]:
                    raise ImageContractError("IMAGE_TEMPLATE_PLAN_SOURCE_CHANGED")
                quality = asset.get("image_quality") or {}
                if (quality.get("vision") or {}).get("status") in SAMPLE_NOT_SCORED:
                    review = sampled_review(asset)
                    needs_vision = (review.get("vision") or {}).get("status") in {"REVIEWED", "CODE_REFUSED"}
                    if needs_vision:
                        asset = {**asset, "image_quality": review}
            try:
                result = validate_asset(asset, destination=destination, require_vision=needs_vision)
                reviewed.append(result["score"] if needs_vision else None)
            except ValueError as exc:
                raise ImageContractError(str(exc), image_sha256=asset.get("sha256")) from exc
        first = assets[0].get("image_template") or {}
        if (markets or macro) and first.get("template") == "weekly":
            raise ImageContractError("TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE")
        if first.get("template") != "weekly" and not first.get("chart"):
            raise ImageContractError("TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE")
        single_image = len(assets) == 1 and destination in SINGLE_IMAGE_DESTINATIONS
        if first.get("template") in {"event", "map"} and not single_image:
            second = (assets[1].get("image_template") or {}) if len(assets) > 1 else {}
            if (second.get("template") != first["template"] or second.get("input") != first["input"]
                    or second.get("chart") or second.get("image_number") != 2):
                raise ImageContractError("IMAGE_TEMPLATE_SECOND_TABLE_REQUIRED")
        for asset in templates:
            meta = asset["image_template"]
            if meta["chart"] and markets and meta["input"].get("market") not in markets:
                raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
        return {"policy": "CC465_IMAGE_TEMPLATES_V1", "images": len(templates),
                "scores": reviewed}
    if not markets and not macro:
        return None
    if not assets:
        if not intent.get("output_dir"):
            raise ImageContractError("MACRO_SOURCE_GRAPH_REQUIRED" if macro else "TRADINGVIEW_FIRST_IMAGE_REQUIRED")
        # Only the existing bounded capture owner can establish exhaustion.
        folder = Path(str(intent.get("output_dir") or ""))
        article_state = bounded_text_fallback(article, folder, now=coordinator._clock())
        if destination != "instagram_business" and article_state:
            return {"policy": POLICY, "text_fallback": True,
                    "first_causes": [article_state.get("first_cause") or article_state["cause"]]}
        rows = list(markets.values())
        states = []
        for row in rows:
            path = (folder.parent / row["key"] if row else folder) / "tradingview_capture_v1.json"
            state = json.loads(path.read_bytes()) if path.is_file() else {}
            if row and (state.get("key") != row["key"] or state.get("market") != row["symbol"]):
                state = {}
            states.append(state)
        if (destination != "instagram_business" and states and all(
                s.get("status") == "TEXT_ONLY" and (s.get("attempts", 0) >= 2
                or (coordinator._clock() - utc(s["started_at_utc"])).total_seconds() >= 300) for s in states)):
            return {"policy": POLICY, "text_fallback": True,
                    "first_causes": [s.get("first_cause") or s.get("cause") for s in states]}
        raise ImageContractError("MACRO_SOURCE_GRAPH_REQUIRED" if macro else "TRADINGVIEW_FIRST_IMAGE_REQUIRED")
    from . import tradingview_snapshot_v1 as tv
    lead = assets[0]
    fallbacks, article_fallbacks = [], []
    plan_folder =Path(intent["output_dir"]) if intent.get("plan_status_post") else None
    for asset in assets:
        if plan_folder and asset.get("modality") == "plan_fact_card":
            binding = asset.get("plan_chart_fallback") or {}
            fallbacks.append(_validate_plan_card(asset, markets.get(binding.get("market")),
                                                  plan_folder, destination))
        elif (intent.get("plan_analysis_page") and intent.get("output_dir")
              and asset.get("modality") == "plan_fact_card" and asset.get("plan_chart_fallback")):
            fallbacks.append(_validate_page_card(coordinator.store, intent, article, asset,
                                                 Path(intent["output_dir"]), coordinator._clock()))
        elif intent.get("output_dir") and not intent.get("plan_status_post") and asset.get("article_chart_fallback"):
            article_fallbacks.append(_validate_article_card(article, asset, Path(intent["output_dir"]),
                                                            coordinator._clock()))
    if macro and not templates:
        if image_type(lead) == "FRED_GRAPH":
            _fred(lead)
        elif image_type(lead) == "TRADINGVIEW_ECONOMIC_CHART":
            tv.validate_snapshot_asset(lead)
        else:
            raise ImageContractError("MACRO_SOURCE_GRAPH_REQUIRED")
        if destination == "instagram_business" and image_type(lead) == "FRED_GRAPH":
            from PIL import Image
            with Image.open(lead["path"]) as original:
                if abs(original.width / original.height - .8) > .003 or lead.get("fred_graph", {}).get("padded"):
                    raise ImageContractError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
            return {"policy": POLICY, "markets": sorted(markets), "macro": True,
                    "first_image_type": "FRED_GRAPH"}
    else:
        lead_is_plan_card = lead.get("modality") == "plan_fact_card" and bool(fallbacks)
        lead_is_article_card = bool(article_fallbacks) and bool(lead.get("article_chart_fallback"))
        if ((image_type(lead) != "TRADINGVIEW_MARKET_CHART" and not lead_is_plan_card and not lead_is_article_card)
                or lead.get("preceding_card")):
            raise ImageContractError("TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE")
        for asset in assets:
            if image_type(asset) != "TRADINGVIEW_MARKET_CHART":
                continue
            snap = asset.get("tradingview_snapshot") or {}
            market = next((m for m in markets if tv.SYMBOLS[m] == snap.get("tv_symbol")), None)
            if not market:
                raise ImageContractError("TRADINGVIEW_MARKET_SYMBOL_MISMATCH")
            tv.validate_snapshot_asset(asset, {"market_asset": market})
            if (plan_folder and markets[market] and markets[market].get("format") == 4
                    and snap.get("plain_price_scale_cause") == tv.PRICE_SCALE_MISMATCH
                    and not asset.get("plan_overlay") and not asset.get("image_template")):
                if not any(state.get("status") == "PLAIN_SNAPSHOT"
                           and (state.get("plain_snapshot") or {}).get("sha256") == snap.get("sha256")
                           for state in _plan_capture_states(markets[market], plan_folder, snap["capture_ratio"])):
                    raise ImageContractError("PLAN_PLAIN_TRADINGVIEW_SNAPSHOT_UNBOUND")
                continue
            check = validate_scale(market, snap)
            if late_chart:
                continue  # The reply shows the market without any plan-price overlay.
            row = markets[market]
            if row:
                levels = row.get("levels") or {}
                instrument = levels.get("public_instrument") or {}
                if levels.get("price_basis") == "instrument" and instrument.get("kind") == "FUT" and market != "USOIL":
                    from .plan_reader_copy_v1 import CURRENT_LEVEL_CONTRACT, LEVEL_CONTRACT

                    overlay = asset.get("plan_overlay") or {}
                    source = overlay.get("source") or {}
                    contract = source.get("level_contract")
                    legacy_annotations = (contract == LEVEL_CONTRACT and source.get("annotations_only")
                                          and not overlay.get("markers"))
                    if contract != CURRENT_LEVEL_CONTRACT and not legacy_annotations:
                        raise ImageContractError("TRADINGVIEW_PLAN_PRICE_BASIS_MISMATCH")
                    # The overlay validator re-derives the plotted levels from
                    # the original market or verifies the legacy annotation.
                    from .tradingview_plan_overlay_v1 import validate as validate_overlay
                    validate_overlay(asset, row)
            if check["level_offset"] and row:
                overlay = asset.get("plan_overlay") or {}
                if overlay.get("price_scale_check") != check or not overlay.get("basis_label"):
                    raise ImageContractError("TRADINGVIEW_WTI_BASIS_LABEL_REQUIRED")
            if market == "USOIL" and row and (asset.get("plan_overlay") or {}).get("basis_from_plan"):
                from .tradingview_plan_overlay_v1 import validate as validate_overlay
                validate_overlay(asset, row)
        if intent.get("plan_status_post") and not (intent.get("native_payload") or {}).get("reuse_run_carousel"):
            # A multi-market root represents every member, not an arbitrary
            # first market. Single-image routes keep their established lead.
            if destination == "instagram_business" and set(markets) != ({
                    m for m in markets for a in assets if (a.get("tradingview_snapshot") or {}).get("tv_symbol") == tv.SYMBOLS[m]}
                    | {binding["market"] for binding in fallbacks}):
                raise ImageContractError("TRADINGVIEW_RUN_MARKET_CHART_MISSING")
    if destination == "instagram_business":
        for asset in assets:
            if asset.get("image_template") or asset.get("plan_chart_fallback") or asset.get("article_chart_fallback"):
                continue  # The native T master and chart box were checked above.
            snap = asset.get("tradingview_snapshot") or {}
            framing = snap.get("framing") or {}
            if (framing.get("mode") != "NATIVE_VIEWPORT" or snap.get("capture_ratio") != "4:5"
                    or abs(asset["width"] / asset["height"] - .8) > .003
                    or framing.get("original_box") != [0, 0, asset["width"], asset["height"]]):
                raise ImageContractError("INSTAGRAM_NATIVE_4X5_CHART_REQUIRED")
    return {"policy": POLICY, "markets": sorted(markets), "macro": macro,
            "first_image_type": image_type(lead),
            **({"plan_chart_fallback_causes": sorted({item["cause"] for item in fallbacks})} if fallbacks else {}),
            **({"article_chart_fallback_causes": sorted({item["cause"] for item in article_fallbacks})}
               if article_fallbacks else {})}
