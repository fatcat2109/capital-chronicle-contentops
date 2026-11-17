"""Build the desk odds table: plain trade behaviours measured on ten years of daily bars for the six markets.

Reads the history store read-only and writes data/research/desk-odds/desk_odds_v1.json, which desk_odds_v1 puts in
every analyst pack. Results are in R (the stop distance) after a cost stated in normal days (D1 ATR14).
Method, the same for every row:
- a decision is taken at a session's close and entered at the next session's open;
- inside one daily bar the stop is taken before the target; a gap through the stop fills at the open;
- "one at a time" rows take the next trade only after the previous one's full hold has passed;
- continuous futures can contain roll discontinuities; signed oil prices are retained, not silently dropped.

Usage: python -B -m tools.product.desk_odds_census_v1 --store <bars.sqlite3> [--out <json>] [--generated-at <UTC>]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sqlite3
from pathlib import Path

from .desk_odds_v1 import DATA, yardstick

SCHEMA = "DeskOddsTableV1"
SERIES = {"EURUSD": "YAHOO_FINANCE:EURUSD=X", "USDJPY": "YAHOO_FINANCE:JPY=X", "XAUUSD": "YAHOO_FINANCE:GC=F",
          "USOIL": "YAHOO_FINANCE:CL=F", "US500": "YAHOO_FINANCE:ES=F", "BTCUSD": "YAHOO_FINANCE:BTC-USD"}
COST = 0.05          # round trip, in normal days
WARMUP = 130
BEHAVIOURS = {
    "LONG_WHILE_UP_20": "Long while the yardstick is UP; stop 1.5 normal days, trailed on closes; up to 20 sessions.",
    "SHORT_WHILE_DOWN_20": "Short while the yardstick is DOWN; stop 1.5 normal days, trailed; up to 20 sessions.",
    "WITH_YARDSTICK_5": "With the yardstick, either side; stop 1.5 normal days; target 2R; up to 5 sessions.",
    "AGAINST_YARDSTICK_5": "Against the yardstick; stop 1 normal day; target 2R; up to 5 sessions.",
    "BUY_PULLBACK_IN_UPTREND_10": "Price above its level of 120 sessions ago and down 1.5 normal days or more in 3 sessions: long; stop 1.5 trailed; up to 10 sessions.",
    "SELL_RALLY_IN_DOWNTREND_10": "Price below its level of 120 sessions ago and up 1.5 normal days or more in 3 sessions: short; stop 1.5 trailed; up to 10 sessions.",
    "BREAKOUT_WITH_TREND_20": "A close beyond the 20-session closing range in the direction of the 60-session change; stop 2 normal days trailed; up to 20 sessions.",
    "FOLLOW_LARGE_DAY_3": "After a session of 1 normal day or more, trade the same way; stop 1 normal day; 3 sessions.",
    "FADE_LARGE_DAY_3": "After a session of 1 normal day or more, trade against it; stop 1 normal day; 3 sessions.",
}
READ_VALUES = {
    "PAID_BOTH_HALVES": "mean above +0.03R, above 0 in each fixed calendar half, nominal t 2 or more",
    "PAID": "mean above +0.03R, but one half was not positive or t is under 2",
    "FLAT": "mean within 0.03R of zero",
    "LOST": "mean below -0.03R, one half not negative",
    "LOST_BOTH_HALVES": "mean below -0.03R and below 0 in each half",
    "THIN": "fewer than 30 trades",
}


def load(store, source_ids=None):
    db = sqlite3.connect(Path(store).resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    out, meta = {}, {}
    try:
        for market, series in SERIES.items():
            query = "select source_id,source_sha256,known_epoch,metadata_json from history_sources where market=? and timeframe='D1' and series_id=? "
            params = (market, series)
            if source_ids is not None:
                query += "and source_id=? "
                params += (source_ids[market],)
            source = db.execute(query + "order by known_epoch desc,source_id desc limit 1", params).fetchone()
            if source is None:
                raise ValueError(f"DESK_ODDS_HISTORY_ABSENT:{market}")
            raw = list(db.execute(
                "select session_date, open, high, low, close from history_bars where source_id=? order by open_epoch",
                (source[0],)))
            rows, sundays = [], 0
            for r in raw:
                if not all(math.isfinite(v) for v in r[1:]) or not r[3] <= min(r[1], r[4]) <= max(r[1], r[4]) <= r[2]:
                    raise ValueError(f"DESK_ODDS_OHLC_CONFLICT:{market}:{r[0]}")
                if min(r[1:]) <= 0 and market not in {"XAUUSD", "USOIL", "US500"}:
                    raise ValueError(f"DESK_ODDS_NONPOSITIVE_SPOT:{market}:{r[0]}")
                if market != "BTCUSD" and dt.date.fromisoformat(r[0]).weekday() == 6:
                    sundays += 1
                    continue
                rows.append(dict(zip(("date", "open", "high", "low", "close"), r)))
            if not rows:
                raise ValueError(f"DESK_ODDS_HISTORY_EMPTY:{market}")
            out[market] = rows
            meta[market] = {"series_id": series, "source_id": source[0], "bars": len(rows),
                            "from": rows[0]["date"], "through": rows[-1]["date"],
                            "source_sha256": source[1], "known_epoch": source[2],
                            "exchange_timezone": json.loads(source[3]).get("exchange_timezone"),
                            "sunday_stubs_removed": sundays,
                            "signed_price_bars": sum(min(r[k] for k in ("open", "high", "low", "close")) <= 0 for r in rows)}
    finally:
        db.close()
    return out, meta


def atr_series(rows, n=14):
    ranges = [None] + [max(rows[i]["high"] - rows[i]["low"], abs(rows[i]["high"] - rows[i - 1]["close"]),
                           abs(rows[i]["low"] - rows[i - 1]["close"])) for i in range(1, len(rows))]
    return [None] * n + [sum(ranges[i - n + 1:i + 1]) / n for i in range(n, len(rows))]


def trade_path(rows, atr, i, side, stop_nd, target_nd=None, hold=10, trail=False, entry=None, *,
               entry_index=None, cost_nd=COST, optimistic=False):
    """The census fill arithmetic, with dated marks for the plain-book ledger.

    An unfinished hold is marked at the last completed close, never liquidated there.
    A mark's stop applies after that close; the preceding stop is used inside its bar.
    """
    start = i + 1 if entry_index is None else entry_index
    if start >= len(rows) or start <= i or not atr[i]:
        return None
    price = rows[start]["open"] if entry is None else entry
    risk = stop_nd * atr[i]
    stop = price - side * risk
    target = price + side * target_nd * atr[i] if target_nd else None
    best, cost, path = price, cost_nd / stop_nd, []
    result = {"signal_index": i, "entry_index": start, "entry_day": rows[start]["date"],
              "entry": price, "initial_stop": stop, "risk_price": risk, "cost_r": cost,
              "target": target, "side": side, "hold_sessions": hold, "path": path}
    for j in range(start, min(start + hold, len(rows))):
        bar, fill, cause, ambiguous, at_open = rows[j], None, None, False, False
        if j > start and side * (bar["open"] - stop) < 0:
            fill, cause, at_open = bar["open"], "GAP_STOP", True
        elif j > start and target is not None and side * (bar["open"] - target) >= 0:
            fill, cause, at_open = target, "TARGET_AT_OPEN", True
        else:
            hit_stop = bar["low"] <= stop if side > 0 else bar["high"] >= stop
            hit_target = target is not None and (bar["high"] >= target if side > 0 else bar["low"] <= target)
            if hit_stop:
                fill, cause, ambiguous = target if hit_target and optimistic else stop, "STOP", bool(hit_target)
            elif hit_target:
                fill, cause = target, "TARGET"
            elif j == start + hold - 1:
                fill, cause = bar["close"], "HORIZON"
        if fill is None and trail:
            best = max(best, bar["close"]) if side > 0 else min(best, bar["close"])
            stop = max(stop, best - risk) if side > 0 else min(stop, best + risk)
        net_r = side * ((bar["close"] if fill is None else fill) - price) / risk - cost
        mark = {"index": j, "date": bar["date"], "net_r": net_r, "stop": stop,
                "exit_price": fill, "exit_reason": cause, "at_open": at_open, "ambiguous": ambiguous}
        path.append(mark)
        if fill is not None:
            break
    result.update(net_r=path[-1]["net_r"], stop=path[-1]["stop"], closed=path[-1]["exit_price"] is not None,
                  exit_index=path[-1]["index"] if path[-1]["exit_price"] is not None else None,
                  ambiguous=path[-1]["ambiguous"])
    return result



def trade(rows, atr, i, side, stop_nd, target_nd=None, hold=10, trail=False, entry=None, *,
          entry_index=None, cost_nd=COST, optimistic=False):
    """One census trade: (R after costs, same-bar ambiguity), including a terminal close mark."""
    result = trade_path(rows, atr, i, side, stop_nd, target_nd, hold, trail, entry,
                        entry_index=entry_index, cost_nd=cost_nd, optimistic=optimistic)
    return None if result is None else (result["net_r"], result["ambiguous"])



def summary(results, split_date=None):
    """results: list of (R, date). Returns [n, mean, t, first half, second half, read]."""
    n = len(results)
    if not n:
        return [n, None, None, None, None, "THIN"]
    values = [r for r, _ in results]
    mean = sum(values) / n
    spread = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    t = mean / (spread / math.sqrt(n)) if spread else 0.0
    middle = split_date or sorted(d for _, d in results)[n // 2]
    first = [r for r, d in results if d < middle]
    second = [r for r, d in results if d >= middle]
    h1, h2 = (sum(v) / len(v) if v else None for v in (first, second))
    if n < 30:
        read = "THIN"
    elif abs(mean) <= 0.03:      # including tiny positive rows with a high nominal t (CC-506 review)
        read = "FLAT"
    elif mean > 0 and h1 is not None and h2 is not None and h1 > 0 and h2 > 0 and t >= 2:
        read = "PAID_BOTH_HALVES"
    elif mean < 0 and h1 is not None and h2 is not None and h1 < 0 and h2 < 0:
        read = "LOST_BOTH_HALVES"
    else:
        read = "PAID" if mean > 0 else "LOST"
    return [n, round(mean, 3), round(t, 1), round(h1, 2) if h1 is not None else None,
            round(h2, 2) if h2 is not None else None, read]


def trend_sign(closes, i, lookback):
    change = closes[i] - closes[i - lookback]
    return (change > 0) - (change < 0)


def signals(closes, rows, atr):
    """Each behaviour as: (function of i -> side, stop, target, hold, trail)."""
    def large(i):
        if not atr[i - 1]:
            return 0
        move = (closes[i] - closes[i - 1]) / atr[i - 1]
        return (1 if move > 0 else -1) if abs(move) >= 1.0 else 0

    def pullback(i, want):
        if not atr[i] or trend_sign(closes, i, 120) != want:
            return 0
        return want if want * (closes[i] - closes[i - 3]) / atr[i] <= -1.5 else 0

    def breakout(i):
        side = trend_sign(closes, i, 60)
        window = closes[i - 20:i]
        if side > 0 and closes[i] > max(window):
            return 1
        if side < 0 and closes[i] < min(window):
            return -1
        return 0

    return {
        "LONG_WHILE_UP_20": (lambda i: 1 if yardstick(closes, i) > 0 else 0, 1.5, None, 20, True),
        "SHORT_WHILE_DOWN_20": (lambda i: -1 if yardstick(closes, i) < 0 else 0, 1.5, None, 20, True),
        "WITH_YARDSTICK_5": (lambda i: yardstick(closes, i), 1.5, 3.0, 5, False),
        "AGAINST_YARDSTICK_5": (lambda i: -yardstick(closes, i), 1.0, 2.0, 5, False),
        "BUY_PULLBACK_IN_UPTREND_10": (lambda i: pullback(i, 1), 1.5, None, 10, True),
        "SELL_RALLY_IN_DOWNTREND_10": (lambda i: pullback(i, -1), 1.5, None, 10, True),
        "BREAKOUT_WITH_TREND_20": (breakout, 2.0, None, 20, True),
        "FOLLOW_LARGE_DAY_3": (large, 1.0, None, 3, False),
        "FADE_LARGE_DAY_3": (lambda i: -large(i), 1.0, None, 3, False),
    }


def one_at_a_time(rows, atr, rule, *, cost_nd=COST, warmup=WARMUP):
    pick, stop_nd, target_nd, hold, trail = rule
    out, free_from = [], 0
    for i in range(warmup, len(rows) - hold):
        if i < free_from or not atr[i]:
            continue
        side = pick(i)
        if not side:
            continue
        result = trade(rows, atr, i, side, stop_nd, target_nd, hold, trail, cost_nd=cost_nd)
        if result is None:
            continue
        out.append((result[0], rows[i]["date"]))
        free_from = i + hold
    return out



def construction(history):
    """Pooled over the six markets, a trade with the yardstick on every fifth session."""
    series = {m: ([r["close"] for r in rows], rows, atr_series(rows)) for m, rows in history.items()}

    def sample(hold):
        for closes, rows, atr in series.values():
            for i in range(60, len(rows) - hold - 6, 5):
                side = yardstick(closes, i)
                if side and atr[i]:
                    yield closes, rows, atr, i, side

    def pooled(values):
        n = len(values)
        mean = sum(values) / n
        return n, round(mean, 3), round(sum(v > 0 for v in values) / n, 2)

    stop_rows = []
    for stop_nd in (0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        got = [trade(rows, atr, i, side, stop_nd, 2 * stop_nd, 5) for _, rows, atr, i, side in sample(5)]
        got = [g for g in got if g is not None]
        n, mean, win = pooled([g[0] for g in got])
        stop_rows.append([stop_nd, n, mean, win, round(sum(g[0] <= -1 for g in got) / n, 2),
                          round(sum(g[1] for g in got) / n, 2), round(COST / stop_nd, 2)])
    exit_rows = []
    for target_r in (1.0, 1.5, 2.0, 3.0):
        values = [g[0] for g in (trade(rows, atr, i, side, 1.5, 1.5 * target_r, 10) for _, rows, atr, i, side in sample(10)) if g]
        exit_rows.append([f"target {target_r}R", *pooled(values)])
    values = [g[0] for g in (trade(rows, atr, i, side, 1.5, None, 10, True) for _, rows, atr, i, side in sample(10)) if g]
    exit_rows.append(["no target, stop trailed on closes", *pooled(values)])
    hold_rows = []
    for hold in (3, 5, 10, 20, 40):
        values = [g[0] for g in (trade(rows, atr, i, side, 1.5, None, hold, True) for _, rows, atr, i, side in sample(hold)) if g]
        hold_rows.append([hold, *pooled(values)])
    entry_rows = []
    for label, offset in (("at the next open", None), ("limit 0.5 normal day better, good for 3 sessions", -0.5),
                          ("limit 1 normal day better, 3 sessions", -1.0),
                          ("stop entry 0.5 normal day further, 3 sessions", 0.5),
                          ("stop entry 1 normal day further, 3 sessions", 1.0)):
        per_signal, per_fill, count = [], [], 0
        for closes, rows, atr, i, side in sample(10):
            count += 1
            if offset is None:
                got = trade(rows, atr, i, side, 1.5, None, 10, True)
                if got:
                    per_signal.append(got[0])
                    per_fill.append(got[0])
                continue
            level, fill = closes[i] + side * offset * atr[i], None
            for j in range(i + 1, i + 4):
                bar = rows[j]
                if offset < 0 and (bar["low"] <= level if side > 0 else bar["high"] >= level):
                    fill = (j, min(bar["open"], level) if side > 0 else max(bar["open"], level))
                    break
                if offset > 0 and (bar["high"] >= level if side > 0 else bar["low"] <= level):
                    fill = (j, max(bar["open"], level) if side > 0 else min(bar["open"], level))
                    break
            if fill is None:
                per_signal.append(0.0)
                continue
            got = trade(rows, atr, i, side, 1.5, None, 10, True, entry=fill[1], entry_index=fill[0])
            if got:
                per_signal.append(got[0])
                per_fill.append(got[0])
        entry_rows.append([label, round(len(per_fill) / count, 2), round(sum(per_signal) / len(per_signal), 3),
                           round(sum(per_fill) / len(per_fill), 3), len(per_fill)])
    return {
        "basis": "All six markets pooled; one trade with the yardstick on every fifth session (trades overlap).",
        "stop_width": {"note": "Target 2R, up to 5 sessions. The cost is a fixed part of a normal day, so it weighs "
                               "more on a tight stop. both_in_one_bar: stop and target lay inside one daily bar and "
                               "the stop was taken, so a tight stop's result is a floor.",
                       "columns": ["stop_normal_days", "n", "mean_r", "win_share", "stopped_share", "both_in_one_bar_share", "cost_r"],
                       "rows": stop_rows},
        "entry": {"note": "Decision-close ATR is frozen; fill bar counts as session 1 and can stop the trade (D1 adverse-path floor). Stop 1.5 normal days trailed, up to 10 sessions. per_signal counts an order that never filled as 0.",
                  "columns": ["entry", "filled_share", "mean_r_per_signal", "mean_r_per_fill", "fills"], "rows": entry_rows},
        "exit": {"note": "Stop 1.5 normal days, up to 10 sessions.", "columns": ["exit", "n", "mean_r", "win_share"], "rows": exit_rows},
        "hold": {"note": "Stop 1.5 normal days trailed, no target.", "columns": ["sessions", "n", "mean_r", "win_share"], "rows": hold_rows},
    }


def build(store, generated_at=None, *, source_ids=None, audit=None):
    history, meta = load(store, source_ids)
    audit_path = DATA.parent / "audit" / "summary.json"
    if audit is None and audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    first = min(dt.date.fromisoformat(v["from"]) for v in meta.values())
    last = max(dt.date.fromisoformat(v["through"]) for v in meta.values())
    split = (first + (last - first) // 2).isoformat()
    by_market, pooled = {}, {code: [] for code in BEHAVIOURS}
    for market, rows in history.items():
        closes, atr = [r["close"] for r in rows], atr_series(rows)
        rules = signals(closes, rows, atr)
        table = []
        for code in BEHAVIOURS:
            results = one_at_a_time(rows, atr, rules[code])
            pooled[code] += results
            table.append([code, *summary(results, split)])
        by_market[market] = table
    body = {
        "schema": SCHEMA,
        "what_this_is": "What plain trade behaviours paid on the desk's six markets from November 2016 to November "
                        "2026. Evidence about base rates, not a rule: the decade was a bull market in gold, shares "
                        "and Bitcoin, and a row with few trades or one bad half deserves little weight.",
        "how_measured": f"Daily bars; R is the stop distance; cost {COST} of a normal day (D1 ATR14) per round trip; a "
                        "decision at a close is entered at the next open; inside one bar the stop is taken before "
                        "the target; one trade at a time per market and behaviour. t is the mean over its standard "
                        "error using sample standard deviation (nominal IID, not a dependence-adjusted significance claim). "
                        "Halves split at the fixed midpoint of the calendar window, not the median trade. "
                        "BTC sessions include weekends; futures are unadjusted continuous proxies with roll risk. "
                        "Signed oil prices are retained; pending entries use decision-close ATR and include the fill bar.",
        "generated_at_utc": generated_at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "tools.product.desk_odds_census_v1",
        "markets": meta,
        "behaviours": BEHAVIOURS,
        "columns": ["behaviour", "n", "mean_r", "t", "first_half_r", "second_half_r", "read"],
        "read_values": READ_VALUES,
        "half_split_date": split,
        "by_market": by_market,
        "all_six_markets": [[code, *summary(pooled[code], split)] for code in BEHAVIOURS],
        "construction": construction(history),
    }
    if audit is not None:
        body["audit"] = {**audit, "same_source_ids_as_audit": audit.get("audited_source_ids") == {
            m: v["source_id"] for m, v in meta.items()}}
        body["what_this_is"] = audit["what_this_is"]
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {**body, "content_hash": hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--out", default=str(DATA))
    parser.add_argument("--generated-at")
    parser.add_argument("--source-manifest", help="Table/manifest whose markets bind exact held source IDs")
    parser.add_argument("--audit", help="Quantified CC-521 audit summary to carry to the analyst")
    args = parser.parse_args(argv)
    sources = json.loads(Path(args.source_manifest).read_text(encoding="utf-8")) if args.source_manifest else None
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8")) if args.audit else None
    table = build(args.store, args.generated_at,
                  source_ids={m: v["source_id"] for m, v in sources["markets"].items()} if sources else None, audit=audit)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"state": "WRITTEN", "path": str(out), "content_hash": table["content_hash"],
                      "markets": {m: v["bars"] for m, v in table["markets"].items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
