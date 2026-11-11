"""Read held bars, official rates and reaction counts for CC-495's existing bot.

SQLite is opened read-only. Only one cited fact enters a reply (host rule 7,
Jim's decision 72 b); raw bars/tables retain their redistribution restriction.
No acquisition, Main write, account connection or replacement producer occurs.
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
    groups = defaultdict(list)
    for event in data["events"]:
        release = policy.utc(event["release_utc"])
        if release.astimezone(policy.ET).date().isoformat() > through_date:
            continue
        for market in event["markets"]:
            symbol = market["symbol"]
            if symbol not in LABELS:
                continue
            for window in ("5m", "30m"):
                cell = market.get("windows", {}).get(window, {})
                value = cell.get("move_pct")
                if type(value) in (int, float) and math.isfinite(value) and not cell.get("missing_reason"):
                    groups[(symbol, market["series_id"], market["price_basis"], window)].append((release, value))
    sources = []
    for (market, series, basis, window), values in sorted(groups.items()):
        dates = [d for d, _ in values]
        start, end = min(dates), max(dates)
        period = "retained CPI days from " + start.strftime("%d %b %Y").lstrip("0") + " to " + end.strftime("%d %b %Y").lstrip("0")
        count, total = sum(value > 0 for _, value in values), len(values)
        fact = {"kind": "base_rate", "markets": [LABELS[market][0]], "count": count, "sample_count": total,
                "period_text": period, "through_date": through_date, "series_id": series, "price_basis": basis,
                "window": window, "event_dates": sorted(d.isoformat() for d in dates)}
        # Do not pool sources, instruments or reaction windows, or claim a complete calendar.
        provider = series.split(":", 1)[0].replace("_", " ").title()
        excerpt = (f"{LABELS[market][1]} rose after {window[:-1]} minutes in {count} of {total} {period} "
                   f"({provider}; desk count).")
        artifact = {"kind": "reaction_count", "path": str(path), "sha256": sha256(raw).hexdigest(),
                    "through_date": through_date, "market": market, "series_id": series, "price_basis": basis, "window": window}
        sources.append(_source(excerpt, fact, attribution=provider, known=data["as_of_utc"], artifact=artifact))
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
    if artifact["kind"] == "reaction_count":
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
