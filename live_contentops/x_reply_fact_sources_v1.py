"""Read held bars, official rates and reaction counts for CC-495's existing bot.

SQLite is opened read-only. Only one cited fact enters a reply (host rule 7,
Jim's decision 72 b); raw bars/tables retain their redistribution restriction.
CC-509 adds a bounded public quote only after held sources have been searched.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from live_contentops import x_reply_fact_policy_v1 as policy

INTAKE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake")
LABELS = {"US500": ("SPX", "S&P 500"), "XAUUSD": ("XAUUSD", "Gold"),
          "EURUSD": ("EURUSD", "EUR/USD"), "USDJPY": ("USDJPY", "USD/JPY"),
          "USOIL": ("WTI", "WTI crude oil"), "BTCUSD": ("BTCUSD", "Bitcoin"),
          "DXY": ("DXY", "Dollar index"), "US2Y": ("US2Y", "US 2-year yield"),
          "US10Y": ("US10Y", "US 10-year yield"), "US10Y_REAL": ("US10Y", "US 10-year real yield")}
FUTURES = {"US500": "S&P 500 futures", "XAUUSD": "Gold futures", "USOIL": "WTI crude oil futures"}
RATE_LABELS = {"US2Y": ("US2Y", "US 2-year yield"), "US10Y": ("US10Y", "US 10-year yield"),
               "US30Y": ("US30Y", "US 30-year yield"), "US_REAL10Y": ("US10Y", "US 10-year real yield"),
               "EFFR": ("RATES", "Effective federal funds rate"), "SOFR": ("RATES", "Secured overnight financing rate"),
               "JP2Y": ("JP2Y", "Japan 2-year yield"), "JP10Y": ("JP10Y", "Japan 10-year yield"),
               "EA2Y": ("EA2Y", "Euro area 2-year yield"), "EA10Y": ("EA10Y", "Euro area 10-year yield")}


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _connect(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def _source(excerpt, fact, *, attribution, known, artifact):
    identity = _digest({"excerpt": excerpt, "fact": fact, "artifact": artifact})
    return {"source_id": "held-reply-fact-" + identity, "kind": "HELD_MARKET_FACT",
            "label": excerpt, "excerpt": excerpt, "known_at_utc": known,
            "rights_class": "CC_OWN_ANALYSIS" if fact["kind"] == "base_rate" else "CITED_THIRD_PARTY_FACT",
            "source_attribution": [{"attribution": attribution}], "fact_binding": fact,
            "context": [{"path": "/public_use", "display": "One attributed fact; host rule 7 and Jim decision 72 b. Raw source redistribution remains restricted."}],
            "store_payload_sha256": identity, "artifact_binding": artifact}


def _bar_source(db, artifact, *, native=False):
    if native:
        row = db.execute("SELECT * FROM bars WHERE symbol=? AND open_epoch=? AND source_sha256=?",
                         (artifact["market"], artifact["open_epoch"], artifact["source_sha256"])).fetchone()
        if not row or db.execute("SELECT 1 FROM invalid_bars WHERE source_sha256=? AND symbol=? AND open_epoch=?",
                                  (row["source_sha256"], row["symbol"], row["open_epoch"])).fetchone():
            raise ValueError("REPLY_HELD_BAR_ABSENT_OR_INVALID")
        observed, known, value = row["open_epoch"] + 900, row["known_epoch"], row["close"]
        market = row["symbol"]
        label, attribution, unit = LABELS[market][1] + " CFD", "Exness", "USD"
        if market == "USDJPY":
            unit = "JPY per USD"
        elif market == "EURUSD":
            unit = "USD per EUR"
    else:
        source = db.execute("SELECT * FROM history_sources WHERE source_id=?", (artifact["source_id"],)).fetchone()
        if not source:
            raise ValueError("REPLY_HELD_HISTORY_SOURCE_ABSENT")
        market = source["market"]
        table = "history_points" if artifact["kind"] == "history_point" else "history_bars"
        row = db.execute("SELECT * FROM " + table + " WHERE source_id=? AND open_epoch=?",
                         (source["source_id"], artifact["open_epoch"])).fetchone()
        if not row or db.execute("SELECT 1 FROM history_invalid WHERE source_id=? AND open_epoch=?",
                                 (source["source_id"], artifact["open_epoch"])).fetchone():
            raise ValueError("REPLY_HELD_HISTORY_POINT_ABSENT_OR_INVALID")
        meta = json.loads(source["metadata_json"])
        observed, known = row["end_epoch"], source["known_epoch"]
        value = row["value"] if table == "history_points" else row["close"]
        treasury = source["series_id"].startswith("US_TREASURY:")
        if not treasury and not source["series_id"].startswith("YAHOO_FINANCE:"):
            raise ValueError("REPLY_HELD_SOURCE_ATTRIBUTION_UNRESOLVED")
        label = LABELS[market][1] if treasury else FUTURES.get(market, LABELS[market][1])
        attribution, unit = ("US Treasury", "percent") if treasury else ("Yahoo Finance", "USD")
        if market == "DXY":
            unit = "points"
        elif market == "USDJPY":
            unit = "JPY per USD"
        elif market == "EURUSD":
            unit = "USD per EUR"
        if meta.get("unit") and treasury and meta["unit"] != "percent":
            raise ValueError("REPLY_HELD_RATE_UNIT_UNSUPPORTED")
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("REPLY_HELD_VALUE_INVALID")
    observed = datetime.fromtimestamp(observed, timezone.utc)
    known = datetime.fromtimestamp(known, timezone.utc)
    day = row["session_date"] if not native and artifact["kind"] == "history_point" else observed.astimezone(policy.ET).date().isoformat()
    fact = {"kind": "daily" if artifact["kind"] == "history_point" else "session",
            "markets": [LABELS[market][0]], "as_of_date": day,
            "observed_at_utc": observed.isoformat()}
    date_words = datetime.fromisoformat(day).strftime("%d %b %Y").lstrip("0")
    stamp = date_words if fact["kind"] == "daily" else observed.astimezone(policy.ET).strftime("%d %b %Y, %I:%M %p ET").lstrip("0")
    excerpt = f"{label}: {value} {unit} ({attribution}, {stamp})."
    return _source(excerpt, fact, attribution=attribution, known=known.isoformat(), artifact=artifact)


def _reaction_sources(path, *, through_date):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    sources, used = [], defaultdict(int)
    # Reuse the producer's counts. Publisher never recomputes its base rates.
    rows = sorted(enumerate(data.get("summary", [])), key=lambda pair: (
        -pair[1].get("n", 0), pair[1].get("window") != "30m", pair[0]))
    for index, row in rows:
        market, window = row["symbol"], row["window"]
        count, total, dates = row["positive_n"], row["n"], row["release_dates"]
        if (market not in LABELS or used[market] >= 3 or window not in {"5m", "30m"}
                or type(count) is not int or type(total) is not int or not 0 <= count <= total or total < 1
                or len(set(dates)) != total or any(day > through_date for day in dates)):
            continue
        start, end = datetime.fromisoformat(min(dates)), datetime.fromisoformat(max(dates))
        period = start.strftime("%b %Y") + " to " + end.strftime("%d %b %Y").lstrip("0")
        series, basis = row["series_id"], row["price_basis"]
        condition = {"HOT": "hot", "COOL": "cool", "IN_LINE": "in-line"}.get(row["bucket"])
        measure = {"CPI_CORE_MOM": "core CPI", "CPI_HEADLINE_MOM": "headline CPI"}.get(row["measure"])
        if not condition or not measure:
            continue
        fact = {"kind": "base_rate", "markets": [LABELS[market][0]], "count": count, "sample_count": total,
                "period_text": period, "through_date": through_date, "series_id": series, "price_basis": basis,
                "window": window, "event_dates": sorted(dates), "condition_text": condition + " " + measure,
                "producer_summary_row": index, "consensus_source": row["consensus_source"], "sample_end_date": max(dates)}
        provider = {"HISTDATA": "HistData", "DUKASCOPY": "Dukascopy", "YAHOO_FINANCE": "Yahoo Finance",
                    "BINANCE": "Binance"}.get(series.split(":", 1)[0], series.split(":", 1)[0])
        excerpt = (f"{LABELS[market][1]} rose after {window[:-1]} minutes in {count} of {total} "
                   f"retained {condition} {measure} days, {period} ({provider}; desk count).")
        artifact = {"kind": "reaction_count", "path": str(path), "sha256": sha256(raw).hexdigest(),
                    "through_date": through_date, "producer_summary_row": index}
        sources.append(_source(excerpt, fact, attribution=provider, known=data["as_of_utc"], artifact=artifact))
        used[market] += 1
    return sources


def _rate_source(db, artifact):
    row = db.execute("SELECT * FROM observations WHERE version=?", (artifact["version"],)).fetchone()
    if not row:
        raise ValueError("REPLY_HELD_RATE_ROW_ABSENT")
    payload = json.loads(row["payload"])
    record = payload["record"]
    market, label = RATE_LABELS[record["alias"]]
    hostname = urlsplit(record["official_url"]).hostname or ""
    official = ("treasury.gov", "newyorkfed.org", "ecb.europa.eu", "mof.go.jp", "boj.or.jp")
    if not any(hostname == h or hostname.endswith("." + h) for h in official):
        raise ValueError("REPLY_HELD_RATE_OFFICIAL_ATTRIBUTION_UNRESOLVED")
    attribution = record.get("rights", {}).get("attribution")
    value, unit, day = record["value"], record["unit"], record["reference_period"]
    if (not attribution or type(value) not in (int, float) or not math.isfinite(value)
            or not str(unit).startswith("percent")):
        raise ValueError("REPLY_HELD_RATE_VALUE_UNIT_OR_ATTRIBUTION_INVALID")
    date_words = datetime.fromisoformat(day).strftime("%d %b %Y").lstrip("0")
    # Preserve the source's rate convention; never convert it into another rate.
    unit_words = str(unit).replace("_", " ")
    excerpt = f"{label}: {value} {unit_words} ({attribution}, {date_words})."
    known = max(policy.utc(row["known_at"]), policy.utc(payload.get("store_available_at_utc", row["known_at"])))
    return _source(excerpt, {"kind": "daily", "markets": [market], "as_of_date": day},
                   attribution=attribution, known=known.isoformat(), artifact=artifact)


def load(*, now, root=INTAKE):
    root, now = Path(root), policy.utc(now)
    path = root / "completed-bars/bars.sqlite3"
    sources, gaps = [], []
    if path.is_file():
        try:
            with _connect(path) as db:
                for market in LABELS:
                    for table, kind in (("history_bars", "history_bar"), ("history_points", "history_point")):
                        source = db.execute("SELECT * FROM history_sources WHERE market=? AND known_epoch<=? "
                                            "AND timeframe=? ORDER BY known_epoch DESC LIMIT 1",
                                            (market, now.timestamp(), "M1" if kind == "history_bar" else "D1")).fetchone()
                        if not source:
                            continue
                        row = db.execute("SELECT open_epoch FROM " + table + " WHERE source_id=? AND end_epoch<=? "
                                         "ORDER BY open_epoch DESC LIMIT 1", (source["source_id"], now.timestamp())).fetchone()
                        if row:
                            sources.append(_bar_source(db, {"kind": kind, "path": str(path), "source_id": source["source_id"],
                                                           "open_epoch": row["open_epoch"]}))
                    if market in {"US500", "XAUUSD", "EURUSD", "USDJPY", "USOIL", "BTCUSD"}:
                        row = db.execute("SELECT open_epoch,source_sha256 FROM bars WHERE symbol=? AND series_id='NATIVE_BROKER' "
                                         "AND known_epoch<=? AND open_epoch<=? ORDER BY open_epoch DESC,known_epoch LIMIT 1",
                                         (market, now.timestamp(), now.timestamp()-900)).fetchone()
                        if row:
                            sources.append(_bar_source(db, {"kind": "native_bar", "path": str(path), "market": market,
                                "open_epoch": row["open_epoch"], "source_sha256": row["source_sha256"]}, native=True))
        except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
            gaps.append({"source": str(path), "cause": str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
    else:
        gaps.append({"source": str(path), "cause": "HELD_BAR_AND_OFFICIAL_RATE_STORE_ABSENT"})
    rate_path = root / "rates-implied/observations.sqlite3"
    try:
        with _connect(rate_path) as db:
            seen = set()
            rows = db.execute("SELECT version,payload FROM observations WHERE known_at<=? ORDER BY known_at DESC LIMIT 250",
                              (now.isoformat().replace("+00:00", "Z"),)).fetchall()
            for row in rows:
                alias = json.loads(row["payload"]).get("record", {}).get("alias")
                if alias not in RATE_LABELS or alias in seen:
                    continue
                seen.add(alias)
                try:
                    sources.append(_rate_source(db, {"kind": "rate_row", "path": str(rate_path), "version": row["version"]}))
                except (ValueError, KeyError, TypeError) as exc:
                    gaps.append({"source": str(rate_path), "market": alias,
                                 "cause": str(exc) if isinstance(exc, ValueError) else "HELD_RATE_SCHEMA_UNUSABLE"})
            families = [r[0] for r in db.execute("SELECT DISTINCT family FROM observations")]
            if not any("priced" in f or "policy_path" in f for f in families):
                gaps.append({"cause": "SAME_SESSION_PRICED_IN_PATH_NOT_HELD", "searched": str(rate_path), "held_families": families})
    except (OSError, sqlite3.Error, ValueError) as exc:
        gaps.append({"source": str(rate_path), "cause": "HELD_RATE_ROWS_UNAVAILABLE", "error": type(exc).__name__})
    reaction = root / "cpi-reactions/latest/publisher.json"
    try:
        sources.extend(_reaction_sources(reaction, through_date=(now.astimezone(policy.ET).date()-timedelta(days=1)).isoformat()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        gaps.append({"source": str(reaction), "cause": "HELD_REACTION_COUNTS_UNAVAILABLE", "error": type(exc).__name__})
    for market in ("NDX", "NASDAQ", *sorted({v[0] for v in LABELS.values()})):
        recent = [s for s in sources if s["fact_binding"]["kind"] == "session" and market in s["fact_binding"]["markets"]
                  and 0 <= (now-policy.utc(s["fact_binding"]["observed_at_utc"])).total_seconds() <= 4500]
        if not recent:
            gaps.append({"market": market, "cause": "SAME_SESSION_PRICE_OR_YIELD_NOT_HELD_WITHIN_75_MINUTES",
                         "searched": str(path)})
    return sources, gaps


def resolve(bound):
    artifact = bound["artifact_binding"]
    if artifact["kind"] == "quote_observation":
        from . import public_market_quote_v1 as public
        observation = public.resolve(artifact["path"], artifact["sha256"])
        source = _quote_source({**observation, "observation_path": artifact["path"],
                               "observation_sha256": artifact["sha256"]})
    elif artifact["kind"] == "reaction_count":
        raw = Path(artifact["path"]).read_bytes()
        if sha256(raw).hexdigest() != artifact["sha256"]:
            raise ValueError("REPLY_SOURCE_BINDING_CHANGED")
        source = next((s for s in _reaction_sources(artifact["path"], through_date=artifact["through_date"])
                       if s["source_id"] == bound["source_id"]), None)
    elif artifact["kind"] == "rate_row":
        with _connect(artifact["path"]) as db:
            source = _rate_source(db, artifact)
    else:
        with _connect(artifact["path"]) as db:
            source = _bar_source(db, artifact, native=artifact["kind"] == "native_bar")
    if not source or source["source_id"] != bound["source_id"] or source["store_payload_sha256"] != bound["store_payload_sha256"]:
        raise ValueError("REPLY_SOURCE_BINDING_CHANGED")
    return source


def _quote_source(observation):
    observed, known = policy.utc(observation["observed_at_utc"]), policy.utc(observation["known_at_utc"])
    market = observation["market"]
    fact_market = {"US500": "SPX", "USOIL": "WTI"}.get(market, market)
    stamp = observed.astimezone(policy.ET).strftime("%d %b %Y, %I:%M %p ET").lstrip("0")
    value = observation.get("value_text", str(observation["value"]))
    change = observation.get("day_change")
    change_text = (f", change from prior close {observation.get('day_change_text', str(change))} {observation.get('change_unit', observation['unit'])}"
                   if change is not None else "")
    excerpt = (f"{observation['instrument_name']}: {value} {observation['unit']}{change_text} "
               f"({observation['source']}, {stamp}).")
    fact = {"kind": "session", "markets": [fact_market], "as_of_date": observed.astimezone(policy.ET).date().isoformat(),
            "observed_at_utc": observed.isoformat()}
    artifact = {"kind": "quote_observation", "path": observation["observation_path"],
                "sha256": observation["observation_sha256"]}
    return _source(excerpt, fact, attribution=observation["source"], known=known.isoformat(), artifact=artifact)


def supplement(posts, sources, *, now):
    """Search Main, native M1, held same-session facts, then one public symbol.

    Topic/age filtering has already happened. Failed acquisitions leave every
    other held fact available and retain their own first cause and elapsed time.
    """
    from . import public_market_quote_v1 as public
    from . import chart_price_reference_v1 as prices
    now = policy.utc(now)
    attempts, additions, done = [], [], set()
    for post in posts:
        requested = policy.target_markets(post)
        markets = sorted({public.ALIASES.get(m, m) for m in requested} & public.SYMBOLS.keys())
        if not markets and requested & {"RATES", "EQUITIES"}:
            markets = ["US10Y"]
        if not markets and requested:
            # A same-session dollar/yield can be tied to an unsupported target
            # market by the existing rule 5; the writer must state that link.
            markets = ["DXY"]
        for market in markets:
            if market in done:
                continue
            done.add(market)
            fact_market = {"US500": "SPX", "USOIL": "WTI"}.get(market, market)
            observation = None
            for kind, read in (
                ("PLAN_STATUS_EXPORT", lambda: prices.plan_status_quote(market, now, prices.PLAN_STATUS_PATH,
                    max_age_seconds=4500, comparison_at=now)),
                ("BAR_STORE_M1_CLOSE", lambda: prices.bar_store_quote(market, now, prices.BAR_STORE,
                    max_age_seconds=4500, comparison_at=now)),
            ):
                try:
                    q = read()
                    observed = policy.utc(q["quoted_at_utc"])
                    if observed.astimezone(policy.ET).date() != policy.utc(post["post_time_utc"]).astimezone(policy.ET).date():
                        raise ValueError("FACT_SESSION_NOT_CURRENT_WITHIN_60_MINUTES")
                    _, _, label, unit, _ = public.SYMBOLS[market]
                    # Native prices are named as CFDs; a future keeps its own name.
                    if kind == "BAR_STORE_M1_CLOSE":
                        label = LABELS.get(market, (market, market))[1] + " CFD"
                    candidate = {"market": market, "value": q["price"], "unit": unit,
                        "instrument_name": label if kind != "PLAN_STATUS_EXPORT" else market + " Main quote",
                        "source": "Exness" if kind == "BAR_STORE_M1_CLOSE" else "Capital Chronicle Main",
                        "source_kind": kind, "observed_at_utc": q["quoted_at_utc"], "known_at_utc": q["known_at_utc"],
                        "source_binding": {k: v for k, v in q.items() if k not in {
                            "age_seconds", "capture_age_seconds", "comparison_at_utc", "comparison_basis"}},
                        "prior_close": None, "day_change": None}
                    # A fresh source can still be too old relative to this post.
                    provisional = {**candidate, "observation_path": "not-saved", "observation_sha256": "not-saved"}
                    policy.check_fact(post, _quote_source(provisional), now=now)
                    observation = public.freeze(candidate)
                    attempts.append({"market": market, "source_kind": kind, "status": "USED", "fetch_seconds": 0.})
                    break
                except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
                    attempts.append({"market": market, "source_kind": kind,
                                     "cause": str(exc) if isinstance(exc, ValueError) else type(exc).__name__, "fetch_seconds": 0.})
            if observation is None:
                held = []
                for source in sources:
                    try:
                        described = policy.describe(source)
                        if described.get("kind") == "session" and (
                                fact_market in described.get("markets", [])
                                or set(described.get("markets", [])) & policy.DRIVERS):
                            held.append(source)
                    except (ValueError, KeyError, TypeError):
                        continue
                usable = False
                for source in held:
                    try:
                        policy.check_fact(post, source, now=now)
                        usable = True
                        break
                    except (ValueError, KeyError, TypeError):
                        pass
                if usable:
                    attempts.append({"market": market, "source_kind": "HELD_SAME_SESSION_FACT", "status": "USED", "fetch_seconds": 0.})
                    continue
                try:
                    observation = public.get(market, now=now)
                    now = max(now, policy.utc(observation["known_at_utc"]))
                    policy.check_fact(post, _quote_source(observation), now=now)
                    attempts.append({"market": market, "source_kind": "PUBLIC_ON_DEMAND_QUOTE", "status": "USED",
                        "source": observation["source"], "source_symbol": observation["source_symbol"],
                        "observed_at_utc": observation["observed_at_utc"], "fetch_seconds": observation["request_seconds"],
                        "cache_hit": observation["cache_hit"]})
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    attempts.append({"market": market, "source_kind": "PUBLIC_ON_DEMAND_QUOTE",
                        "cause": str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                        **(exc.details if isinstance(exc, public.QuoteError) else {})})
                    # A closed cash index or failed direct source can still use
                    # a current yield driver. Rule 5 checks its explicit link.
                    if market not in policy.DRIVERS and "US10Y" not in done and "US10Y" not in markets:
                        markets.append("US10Y")
                    continue
            additions.append(_quote_source(observation))
    return additions, attempts, now
