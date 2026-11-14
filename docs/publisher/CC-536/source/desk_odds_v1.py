"""Desk odds for the analyst's pack: what plain trade behaviours have paid on the six first-phase markets.

The measured table is data/research/desk-odds/desk_odds_v1.json, built by desk_odds_census_v1 from ten years of
daily bars. This module adds today's trend yardstick from the pack's own completed D1 bars and the desk's scored
record. Everything here is evidence for the analyst (Jim's decisions 125 and 128): nothing arms, refuses or sizes.
A missing or damaged input leaves the block UNAVAILABLE with its cause and never stops the pack.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

SCHEMA = "DeskOddsContextV1"
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "research" / "desk-odds" / "desk_odds_v1.json"
RECORD = ROOT / "data" / "research" / "desk-odds" / "desk_record_v1.json"
# Each side's own record, split from one table's trades by desk_odds_sides_v1 (W2, 14 Nov 2026).
SIDES = ROOT / "data" / "research" / "desk-odds" / "desk_odds_sides_v1.json"
SIDES_SCHEMA = "DeskOddsSidesV1"
SIDE_COLUMNS = ["n", "win_share", "mean_r", "t", "first_half_r", "second_half_r", "read"]
# These behaviours trade both ways, so their table row pools LONG and SHORT trades.
TWO_SIDED = ("WITH_YARDSTICK_5", "AGAINST_YARDSTICK_5", "BREAKOUT_WITH_TREND_20", "FOLLOW_LARGE_DAY_3", "FADE_LARGE_DAY_3")
ONE_SIDE = {"LONG_WHILE_UP_20": "LONG", "SHORT_WHILE_DOWN_20": "SHORT", "BUY_PULLBACK_IN_UPTREND_10": "LONG",
            "SELL_RALLY_IN_DOWNTREND_10": "SHORT"}
# Trend rows carry the drift control: the same stop and hold taken on every free session.
TREND = ("LONG_WHILE_UP_20", "SHORT_WHILE_DOWN_20", "WITH_YARDSTICK_5", "BUY_PULLBACK_IN_UPTREND_10",
         "SELL_RALLY_IN_DOWNTREND_10", "BREAKOUT_WITH_TREND_20")
RUNTIME_DIR = Path("A:/Capital Chronicle/Runtime/OfficialRates/cc-078-20261101/state/intake/desk-odds")
EXTRA_BLOCKS = ("intraday", "conditioned", "release", "plain_book")
BLOCK_BYTE_LIMIT = 12_000
TABLE_BYTE_LIMIT = 4_000_000
YARDSTICK = ("UP when the 20-session and 60-session changes are positive and price is above its 20-session and "
             "50-session mean close; DOWN when all four are negative; otherwise MIXED.")
INSTRUCTIONS = (
    "Read desk_odds and desk_record before you choose a side, a lane or a level. desk_odds shows what plain "
    "behaviours paid on these markets over up to ten years of daily bars (short histories are named), in R after costs, with both half-periods, and "
    "today's trend yardstick for each market. desk_record shows how this desk's own analyst scored in replay. Both "
    "are evidence, neither is an instruction: every decision stays yours, and standing aside is a full decision. "
    "Further intraday, conditioned, release and plain_book blocks are evidence of the same kind; each states what_this_is.",
    "For each OPEN or WATCH, say in your reasoning which desk_odds row the trade belongs to and what that row paid. "
    "Then name the fact of today that the table does not hold and that moves the odds for you: a release, a "
    "repricing under way, a level whose break forces others to act. A row that lost needs such a fact; a story "
    "about price is not one. State your probability from the measured figures (the row's mean R, the win shares "
    "in desk_odds.construction) plus or minus those reasons.",
    "Construction, per market and pooled (desk_odds.construction_by_market and construction): read the current stop_width, entry, "
    "exit and hold rows, including their sample counts, rather than carrying an old ranking forward. Compare "
    "cost_r (this market's current cost-owner reserve in normal days divided by stop width) with its dated cost source; "
    "both_in_one_bar_share measures the daily-bar path ambiguity, and a pending order includes its fill day "
    "with volatility frozen at the decision close. Read what_this_is for the chance and walk-forward results; "
    "nominal t and mean R are not a calibrated probability. Put the stop where the idea is wrong and keep the "
    "risk within the standing caps; when the stop sits inside a normal day's range, say what keeps ordinary "
    "noise from reaching it. The construction stays your decision: weigh the measured entry, exit and hold "
    "alternatives against today's facts, own costs and the no-trade alternative.",
)


def _mean(values):
    return sum(values) / len(values)


def yardstick(closes, i=None):
    """+1 UP, -1 DOWN, 0 MIXED (or too little history) at index i of a list of closes."""
    i = len(closes) - 1 if i is None else i
    if i < 60:
        return 0
    c = closes[i]
    parts = (c - closes[i - 20], c - closes[i - 60], c - _mean(closes[i - 19:i + 1]), c - _mean(closes[i - 49:i + 1]))
    if all(p > 0 for p in parts):
        return 1
    if all(p < 0 for p in parts):
        return -1
    return 0


def atr14(rows, i=None):
    """Mean true range of the 14 sessions ending at index i; None with too little history."""
    i = len(rows) - 1 if i is None else i
    if i < 14:
        return None
    total = 0.0
    for j in range(i - 13, i + 1):
        high, low, prev = rows[j]["high"], rows[j]["low"], rows[j - 1]["close"]
        total += max(high - low, abs(high - prev), abs(low - prev))
    return total / 14


def yardstick_today(rows):
    """The yardstick and its four parts at the last completed D1 bar."""
    closes = [r["close"] for r in rows]
    if len(closes) < 61:
        return {"state": "UNAVAILABLE", "cause": "FEWER_THAN_61_COMPLETED_D1_BARS", "bars": len(closes)}
    i, c = len(closes) - 1, closes[-1]
    sign = yardstick(closes)
    return {"state": "AVAILABLE", "yardstick": {1: "UP", -1: "DOWN", 0: "MIXED"}[sign],
            "last_completed_bar_utc": dt.datetime.fromtimestamp(rows[-1]["time"], dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "change_20_sessions_pct": round(100 * (c / closes[i - 20] - 1), 2),
            "change_60_sessions_pct": round(100 * (c / closes[i - 60] - 1), 2),
            "price_vs_mean_20_pct": round(100 * (c / _mean(closes[i - 19:]) - 1), 2),
            "price_vs_mean_50_pct": round(100 * (c / _mean(closes[i - 49:]) - 1), 2),
            "normal_day_atr14": atr14(rows)}


def active_rows(rows):
    """Which measured behaviours' conditions hold at the last completed D1 bar, as (behaviour, side) pairs.
    The same conditions as desk_odds_census_v1.signals, read at one bar."""
    closes = [r["close"] for r in rows]
    i = len(closes) - 1
    out = []
    if i < 15:
        return out
    side = yardstick(closes)
    if side:
        name = "LONG" if side > 0 else "SHORT"
        out.append(("LONG_WHILE_UP_20" if side > 0 else "SHORT_WHILE_DOWN_20", name))
        out.append(("WITH_YARDSTICK_5", name))
        out.append(("AGAINST_YARDSTICK_5", "SHORT" if side > 0 else "LONG"))
    normal_day, previous = atr14(rows), atr14(rows, i - 1)
    if normal_day and i >= 121:
        trend, move = closes[i] - closes[i - 120], (closes[i] - closes[i - 3]) / normal_day
        if trend > 0 and move <= -1.5:
            out.append(("BUY_PULLBACK_IN_UPTREND_10", "LONG"))
        if trend < 0 and move >= 1.5:
            out.append(("SELL_RALLY_IN_DOWNTREND_10", "SHORT"))
    if i >= 60:
        change, window = closes[i] - closes[i - 60], closes[i - 20:i]
        if change > 0 and closes[i] > max(window):
            out.append(("BREAKOUT_WITH_TREND_20", "LONG"))
        if change < 0 and closes[i] < min(window):
            out.append(("BREAKOUT_WITH_TREND_20", "SHORT"))
    if previous and abs(closes[i] - closes[i - 1]) >= previous:
        up = closes[i] > closes[i - 1]
        out.append(("FOLLOW_LARGE_DAY_3", "LONG" if up else "SHORT"))
        out.append(("FADE_LARGE_DAY_3", "SHORT" if up else "LONG"))
    return out


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def table_hash(table):
    return hashlib.sha256(encoded({k: v for k, v in table.items() if k != "content_hash"})).hexdigest()


def validate_table(table):
    """Data-only updates use the existing schema and a canonical content hash."""
    if not isinstance(table, dict) or table.get("schema") != "DeskOddsTableV1":
        raise ValueError("DESK_ODDS_SCHEMA_INVALID")
    if table.get("content_hash") != table_hash(table):
        raise ValueError("DESK_ODDS_HASH_INVALID")
    for key in ("what_this_is", "how_measured", "generated_at_utc"):
        if not isinstance(table.get(key), str) or not table[key]:
            raise ValueError("DESK_ODDS_FIELD_INVALID:" + key)
        if len(encoded(table[key])) > BLOCK_BYTE_LIMIT:
            raise ValueError("DESK_ODDS_FIELD_OVER_BYTE_LIMIT:" + key)
    instant = dt.datetime.fromisoformat(table["generated_at_utc"].replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("DESK_ODDS_TABLE_CLOCK_REQUIRES_OFFSET")
    for key in ("by_market", "markets", "behaviours", "read_values", "construction"):
        if not isinstance(table.get(key), dict):
            raise ValueError("DESK_ODDS_FIELD_INVALID:" + key)
    columns = table.get("columns")
    if (not isinstance(columns, list) or not all(isinstance(c, str) for c in columns)
            or len(columns) != len(set(columns)) or not {"behaviour", "n", "mean_r", "t", "first_half_r", "second_half_r", "read"} <= set(columns)):
        raise ValueError("DESK_ODDS_COLUMNS_INVALID")
    for symbol, rows in table["by_market"].items():
        if symbol not in table["markets"] or not isinstance(rows, list):
            raise ValueError("DESK_ODDS_MARKET_ROWS_INVALID:" + symbol)
        for row in rows:
            if (not isinstance(row, list) or len(row) != len(columns)
                    or row[0] not in table["behaviours"] or type(row[1]) is not int or row[1] < 0
                    or row[columns.index("read")] not in table["read_values"]):
                raise ValueError("DESK_ODDS_ROW_INVALID:" + symbol)
            for name in ("mean_r", "t", "first_half_r", "second_half_r", "cost_r"):
                if name in columns and row[columns.index(name)] is not None and type(row[columns.index(name)]) not in (int, float):
                    raise ValueError("DESK_ODDS_NUMERIC_FIELD_INVALID:" + symbol + ":" + name)
    for market in table["markets"].values():
        if not isinstance(market, dict):
            raise ValueError("DESK_ODDS_MARKET_METADATA_INVALID")
        if market.get("known_epoch") is not None and market["known_epoch"] > instant.timestamp():
            raise ValueError("DESK_ODDS_SOURCE_AFTER_TABLE_CLOCK")
    for key in ("stop_width", "entry", "exit", "hold"):
        block = table["construction"].get(key)
        if not isinstance(block, dict) or not isinstance(block.get("rows"), list):
            raise ValueError("DESK_ODDS_CONSTRUCTION_INVALID:" + key)
    if not isinstance(table.get("all_markets", table.get("all_six_markets")), list):
        raise ValueError("DESK_ODDS_POOLED_ROWS_INVALID")
    return table


def load_table(data_path=DATA, runtime_dir=None, *, cutoff=None):
    """Newest valid generated clock wins, regardless of filename or mtime. Bad files cannot hide older data."""
    folder = Path(runtime_dir) if runtime_dir is not None else RUNTIME_DIR
    rejected, candidates = [], []
    if folder.is_dir():
        # The writer uses one immutable filename per weekly rebuild.
        for path in sorted(folder.glob("desk_odds*.json"), reverse=True):
            try:
                if path.stat().st_size > TABLE_BYTE_LIMIT:
                    raise ValueError("DESK_ODDS_TABLE_OVER_BYTE_LIMIT")
                table = validate_table(_load(path))
                at = dt.datetime.fromisoformat(table["generated_at_utc"].replace("Z", "+00:00"))
                if cutoff and at > dt.datetime.fromisoformat(str(cutoff).replace("Z", "+00:00")):
                    raise ValueError("DESK_ODDS_TABLE_AFTER_CUTOFF")
                candidates.append((at, path.name, table, path))
            except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
                if len(rejected) < 5:
                    rejected.append({"path": str(path), "cause": str(exc)[:160]})
    if candidates:
        _, _, table, path = max(candidates, key=lambda c: (c[0], c[1]))
        return table, {"kind": "RUNTIME", "path": str(path), "rejected_runtime": rejected}
    if Path(data_path).stat().st_size > TABLE_BYTE_LIMIT:
        raise ValueError("DESK_ODDS_TABLE_OVER_BYTE_LIMIT")
    return validate_table(_load(data_path)), {"kind": "COMMITTED", "path": str(data_path), "rejected_runtime": rejected}


def extra_blocks(table, byte_limit=BLOCK_BYTE_LIMIT):
    kept, omitted = {}, []
    for name in EXTRA_BLOCKS:
        nested = table.get("blocks") if isinstance(table.get("blocks"), dict) else {}
        block = table.get(name, nested.get(name))
        if block is None:
            continue
        size = len(encoded(block))
        if not isinstance(block, dict) or not isinstance(block.get("what_this_is"), str) or not block["what_this_is"]:
            cause = "WHAT_THIS_IS_REQUIRED"
        elif size > byte_limit:
            cause = "BLOCK_OVER_BYTE_LIMIT"
        else:
            kept[name] = block
            continue
        omitted.append({"block": name, "cause": cause, "bytes": size, "limit_bytes": byte_limit})
    return kept, omitted


def side_split(table, sides_path=SIDES):
    """(split, status) for this table: its own `sides` block, else the side file's entry for its content hash.
    A table the split was not built for gets none: the active rows then name the cause, never another table's sides."""
    own = table.get("sides")
    if isinstance(own, dict) and isinstance(own.get("markets"), dict):
        return own, {"state": "AVAILABLE", "kind": "TABLE"}
    path = Path(sides_path)
    try:
        if path.stat().st_size > TABLE_BYTE_LIMIT:
            raise ValueError("DESK_ODDS_SIDES_OVER_BYTE_LIMIT")
        found = _load(path)
        if (not isinstance(found, dict) or found.get("schema") != SIDES_SCHEMA or not isinstance(found.get("tables"), dict)
                or found.get("content_hash") != table_hash(found)):
            raise ValueError("DESK_ODDS_SIDES_INVALID")
    except (OSError, ValueError, TypeError) as exc:
        return None, {"state": "UNAVAILABLE", "cause": str(exc)[:160], "path": str(path)}
    split = found["tables"].get(table["content_hash"])
    if not isinstance(split, dict) or not isinstance(split.get("markets"), dict):
        return None, {"state": "UNAVAILABLE", "cause": "SIDE_SPLIT_NOT_BUILT_FOR_THIS_TABLE", "path": str(path)}
    return split, {"state": "AVAILABLE", "kind": "SIDE_FILE", "path": str(path),
                   "generated_at_utc": found.get("generated_at_utc")}


def side_row(code, side, own, cost, market_split):
    """One condition that holds now, with the record of the side it trades. A two-sided behaviour's pooled row
    appears only beside it as both_sides_together; a trend row carries always-long with the same stop and hold."""
    split = market_split if isinstance(market_split, dict) and market_split.get("state") == "SPLIT" else {}
    mine = ((split.get("sides") or {}).get(code) or {}).get(side)
    row = {"behaviour": code, "side": side}
    if own is None:
        row["this_side"] = None
    elif code in TWO_SIDED:
        row["this_side"] = mine
        if mine is None:
            row["this_side_cause"] = "SIDE_SPLIT_UNAVAILABLE_FOR_THIS_MARKET"
        row["both_sides_together"] = own
    else:
        row["this_side"] = mine or [own[0], None, *own[1:]]
    row["cost_r"] = cost
    always = (split.get("always") or {}).get(code) or {}
    if own is not None and code in TREND and always:
        row["always_long_same_stop_and_hold"] = always.get("ALWAYS_LONG")
        if side == "SHORT":
            row["always_short_same_stop_and_hold"] = always.get("ALWAYS_SHORT")
    return row


def sides_by_market(split, symbols):
    """Each market's side records for the two-sided rows and always-long beside each trend row. Always-short
    appears on an active SHORT trend row only, to keep the block within its reads (CC-552)."""
    out = {}
    for symbol in symbols:
        market = (split or {}).get("markets", {}).get(symbol)
        if not isinstance(market, dict) or market.get("state") != "SPLIT":
            continue
        rows = {code: dict(market["sides"][code]) for code in TWO_SIDED if code in market.get("sides", {})}
        for code in TREND:
            always = ((market.get("always") or {}).get(code) or {}).get("ALWAYS_LONG")
            if always:
                rows.setdefault(code, {})["ALWAYS_LONG"] = always
        out[symbol] = rows
    return out


def context(markets, *, cutoff, data_path=DATA, record_path=RECORD, runtime_dir=None, plain_book_path=None,
            sides_path=SIDES):
    """The desk_odds and desk_record blocks for one role pack. `markets` maps a broker symbol to its captured
    market row (known_at_utc and D1 bars), as analysis_base_rates_v1.build_sheet receives it."""
    from .analysis_base_rates_v1 import completed_rows
    today, active = {}, {}
    for symbol, market in (markets or {}).items():
        try:
            rows, _, _ = completed_rows(market, symbol, cutoff)
            today[symbol] = yardstick_today(rows)
            active[symbol] = active_rows(rows)
        except (ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError) as exc:
            today[symbol] = {"state": "UNAVAILABLE", "cause": str(exc)}
    try:
        table, source = load_table(data_path, runtime_dir, cutoff=cutoff)
        further, omitted = extra_blocks(table)
        # CC-533 supplies a separate data artifact so integrating it also reaches
        # packs while a newer runtime table carries other lanes' measured blocks.
        from .plain_book_v1 import BLOCK, INSTRUCTION as plain_book_instruction, read_block
        candidate = BLOCK if plain_book_path is None else Path(plain_book_path)
        if candidate.is_file():
            try:
                plain = read_block(cutoff=cutoff, path=candidate)
                if len(encoded(plain)) > BLOCK_BYTE_LIMIT:
                    raise ValueError("PLAIN_BOOK_BLOCK_OVER_BYTE_LIMIT")
                existing = further.get("plain_book", {})
                if not existing or plain["generated_at_utc"] >= existing.get("generated_at_utc", table["generated_at_utc"]):
                    further["plain_book"] = plain
            except (OSError, ValueError, TypeError, KeyError) as exc:
                omitted.append({"block": "plain_book", "cause": str(exc)[:160], "path": str(candidate)})
        if "plain_book" in further:
            plain_at = further["plain_book"].get("generated_at_utc", table["generated_at_utc"])
            if dt.datetime.fromisoformat(plain_at.replace("Z", "+00:00")) > dt.datetime.fromisoformat(str(cutoff).replace("Z", "+00:00")):
                del further["plain_book"]
                omitted.append({"block": "plain_book", "cause": "PLAIN_BOOK_AFTER_CUTOFF"})
        measured = set(table["by_market"])
        indexes = {name: table["columns"].index(name) for name in table["columns"]}
        shown = [s for s in table["by_market"] if not today or s in today]

        def with_sides(split):
            rows = {}
            for symbol, pairs in active.items():
                own = {row[0]: [row[indexes[name]] for name in ("n", "mean_r", "t", "first_half_r", "second_half_r", "read")]
                       for row in table["by_market"].get(symbol, [])}
                cost_rows = {row[0]: row[indexes["cost_r"]] for row in table["by_market"].get(symbol, [])} if "cost_r" in indexes else {}
                market_split = ((split or {}).get("markets") or {}).get(symbol)
                rows[symbol] = [side_row(code, side, own.get(code), cost_rows.get(code), market_split) for code, side in pairs]
            return rows, sides_by_market(split, shown)

        split, split_state = side_split(table, sides_path)
        try:
            rows_now, by_sides = with_sides(split)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:   # a damaged split never costs the block
            split, split_state = None, {"state": "UNAVAILABLE", "cause": f"DESK_ODDS_SIDES_DAMAGED: {type(exc).__name__}: {exc}"[:160]}
            rows_now, by_sides = with_sides(None)
        if split is not None:
            held = {s: split["markets"].get(s) if isinstance(split["markets"].get(s), dict) else {} for s in shown}
            split_state["not_split"] = {s: str(v.get("cause", "MARKET_NOT_IN_SPLIT"))[:120]
                                        for s, v in held.items() if v.get("state") != "SPLIT"}
        for symbol, rows in rows_now.items():
            today[symbol]["rows_whose_condition_holds_now"] = rows
        odds = {"schema": SCHEMA, "state": "AVAILABLE",
                "what_this_is": table["what_this_is"], "how_measured": table["how_measured"],
                "yardstick_rule": YARDSTICK, "behaviours": table["behaviours"], "columns": table["columns"],
                "read_values": table["read_values"],
                "by_market": {s: table["by_market"][s] for s in table["by_market"] if not today or s in today},
                "two_sided_behaviours": list(TWO_SIDED),
                "sides_note": "by_market, all_markets and all_six_markets pool both sides of the two_sided_behaviours "
                              "in one row, and the construction tables pool a trade with the yardstick on both sides. "
                              "by_market_sides holds each side's own record of those rows (side_columns), and beside "
                              "each trend row ALWAYS_LONG: the same stop and hold taken long on every free session, "
                              "after the same cost, the drift control for what the trend condition adds. "
                              "For each OPEN or WATCH, name the side the trade takes and what that side paid "
                              "(this_side, or by_market_sides), not the pooled both_sides_together, and beside a "
                              "trend row what always-long with the same stop and hold paid.",
                "side_columns": SIDE_COLUMNS, "side_split": split_state, "by_market_sides": by_sides,
                "all_markets_sides": (split or {}).get("all_markets_sides"),
                "all_markets": table.get("all_markets", table.get("all_six_markets")),
                "pooled_columns": table.get("pooled_columns", table["columns"]),
                "all_six_markets": table.get("all_six_markets"), "construction": table["construction"],
                "construction_by_market": {s: v for s, v in table.get("construction_by_market", {}).items()
                                           if not today or s in today},
                "markets": {s: v for s, v in table["markets"].items() if not today or s in today},
                "table_source": source, "omitted_blocks": omitted, **further,
                "not_measured": sorted(s for s in today if s not in measured),
                "not_measured_causes": {s: table["markets"].get(s, {}).get("cause", "MARKET_NOT_IN_TABLE")
                                        for s in today if s not in measured},
                "not_measured_note": "Each absent market names its own fetch, history or cost cause; another market's rows do not replace it.",
                "table_generated_at_utc": table["generated_at_utc"], "table_content_hash": table["content_hash"],
                "today_note": "yardstick_today reads the last completed D1 bar, not the live price. "
                              "rows_whose_condition_holds_now lists the measured behaviours that would trade today "
                              "and, in this_side (side_columns), what the side named in the row paid in this market; "
                              "null means this market is not measured. both_sides_together is the two-sided row "
                              "(columns without cost_r), shown only beside its side. always_long_same_stop_and_hold "
                              "(and always_short_ beside a short) is the drift control for a trend row.",
                "yardstick_today": today}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        odds = {"schema": SCHEMA, "state": "UNAVAILABLE", "cause": f"{type(exc).__name__}: {exc}"[:200],
                "yardstick_rule": YARDSTICK, "yardstick_today": today}
    try:
        record = {"state": "AVAILABLE", **_load(record_path)}
    except (OSError, ValueError, TypeError) as exc:
        record = {"state": "UNAVAILABLE", "cause": f"{type(exc).__name__}: {exc}"[:200]}
    instructions = list(INSTRUCTIONS)
    if odds.get("plain_book"):
        instructions.append(plain_book_instruction)
    return {"desk_odds": odds, "desk_record": record, "instructions": instructions}
