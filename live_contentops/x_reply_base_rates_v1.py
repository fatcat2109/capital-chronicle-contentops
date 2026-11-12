"""CC-510: adapt the held statistics producer and market census to reply facts.

Publisher selects a stated historical analogue; the existing CC-481 producer
counts it. No bars, pooled win shares or desk trade records become public copy.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
import importlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sqlite3
import sys

from live_contentops import x_reply_fact_policy_v1 as policy

MAIN = Path(r"A:\Capital Chronicle\main-jim-research-dashboard-20261025")
BINDINGS = MAIN / "tools/product/cc_market_tools/bindings.json"
ODDS = MAIN / "data/research/desk-odds/desk_odds_v1.json"
KIND = "HELD_REPLY_BASE_RATE"
MARKETS = {"SPX": "US500", "WTI": "USOIL", "XAUUSD": "XAUUSD", "EURUSD": "EURUSD",
           "USDJPY": "USDJPY", "BTCUSD": "BTCUSD", "NDX": "NDX", "NASDAQ": "NASDAQ",
           "BRENT": "BRENT", "DXY": "DXY"}
LABELS = {"US500": "S&P 500 futures", "USOIL": "WTI futures", "XAUUSD": "Gold futures",
          "EURUSD": "EUR/USD", "USDJPY": "USD/JPY", "BTCUSD": "Bitcoin", "NDX": "Nasdaq 100",
          "NASDAQ": "Nasdaq", "BRENT": "Brent futures", "DXY": "Dollar index"}
MOVE = re.compile(r"\b(ris(?:e[sn]?|ing)|rose|gain(?:s|ed|ing)?|jump(?:s|ed)?|surge[sd]?|"
                  r"rall(?:y|ies|ied)|up|higher|advance[sd]?|strengthen[sd]?|"
                  r"fall(?:s|ing)?|fell|drop(?:s|ped)?|down|lower|decline[sd]?|slip[sd]?|"
                  r"slide[sd]?|slid|tumble[sd]?|slump[sd]?|lose[sd]?|lost|weaken[sd]?)\b", re.I)
UP = re.compile(r"^(?:ris|rose|gain|jump|surge|rall|up|higher|advance|strengthen)", re.I)
PREFIX = re.compile(r"(?:[\s,:;()\-]|\b(?:futures?|spot|cash|index|crude|oil|prices?|pair|is|are|was|were|has|have|had|"
                    r"now|today|currently|last|still|again|briefly|slightly|sharply|further|extends?|extended|"
                    r"edges?|edged|trades?|trading|at|hits?|sets?|reaches?|reached|a|an|new|fresh)\b)*", re.I)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def conditions(text):
    """Keep each market's own move, sign and percent; never substitute indices/oils."""
    spans = []
    # Unsupported markets still delimit clauses: silver's move cannot become gold's.
    found = policy.markets(text) - {"EQUITIES", "RATES"}
    if "NDX" in found:
        found.discard("NASDAQ")
    for market in found:
        for match in re.finditer(policy.MARKETS[market], text, re.I):
            if market == "WTI" and re.search(r"\bbrent\s*$", text[:match.start()], re.I):
                continue
            if market == "DXY" and re.search(r"\b(?:aussie|australian|canadian|new zealand|nz|taiwan|"
                r"hong kong|singapore|jamaican|fijian|namibian)(?:'s)?\s*$", text[:match.start()], re.I):
                # Preserve a boundary, without treating another dollar as USD.
                spans.append((match.start(), match.end(), "OTHER_DOLLAR"))
                continue
            spans.append((match.start(), match.end(), market))
    spans.sort()
    result = []
    for i, (start, end, market) in enumerate(spans):
        if market not in MARKETS:
            continue
        clause = text[end:spans[i + 1][0] if i + 1 < len(spans) else len(text)]
        clause = re.split(r"[.!?]\s+", clause[:150], maxsplit=1)[0]
        record = re.search(r"\b(?:record|all[ -]time)\s+(high|low)\b", clause, re.I)
        record_high = re.search(r"\bat (?:a |a new |an all[ -]time )?record\b", clause, re.I)
        move = MOVE.search(clause)
        signed = re.search(r"(?<!\w)([+\-−]\d+(?:\.\d+)?)\s*%", clause)
        signal = record_high or record
        if signal and PREFIX.fullmatch(clause[:signal.start()]):
            direction = "down" if record and record[1].lower() == "low" else "up"
            if market == "USDJPY" and re.search(r"\byen\b", text[start:end], re.I):
                direction = "down" if direction == "up" else "up"
            result.append({"market": market, "kind": "record", "direction": direction,
                           "lookback": 252})
            continue
        if not move and not signed:
            continue
        if not PREFIX.fullmatch(clause[:move.start() if move else signed.start()]):
            continue
        if move and re.match(r"\s+(?:if|unless)\b", clause[move.end():], re.I):
            continue
        direction = ("up" if UP.match(move[1]) else "down") if move else ("down" if signed[1][0] in "-−" else "up")
        # A CPI percent later in the sentence is not this market's move.
        amount = re.match(r"\s*(?:by\s+|as much as\s+|at least\s+|more than\s+|over\s+)?"
                          r"([+\-−]?\d+(?:\.\d+)?)\s*%", clause[move.end():]) if move else signed
        if amount and ((amount[1].startswith(("-", "−")) and direction == "up")
                       or (amount[1].startswith("+") and direction == "down")):
            continue
        percent = abs(float(amount[1].replace("−", "-"))) if amount else None
        # A stronger yen is a lower USD/JPY, not a higher USD/JPY.
        if market == "USDJPY" and re.search(r"\byen\b", text[start:end], re.I):
            direction = "down" if direction == "up" else "up"
            # Inverse currency returns do not share the quoted percent magnitude.
            percent = None
        if percent is not None and (not math.isfinite(percent) or percent <= 0 or percent >= 100):
            continue
        result.append({"market": market, "kind": "move", "direction": direction, "minimum_pct": percent})
    return list({digest(c): c for c in result}.values())


def query_for(condition, horizon, completed_before):
    direction = condition["direction"]
    if condition["kind"] == "record":
        query = {"type": "breakout", "direction": direction, "lookback": condition["lookback"]}
        words = f"daily closes {'above' if direction == 'up' else 'below'} prior {condition['lookback']}-session {'highs' if direction == 'up' else 'lows'}"
    else:
        query = {"type": "return", "direction": direction}
        words = "daily gains" if direction == "up" else "daily losses"
        percent = condition["minimum_pct"]
        if percent is not None:
            # CC-481's return threshold is logarithmic, not percent. This is a
            # unit conversion of the headline, never an outcome computation.
            query["minimum" if direction == "up" else "maximum"] = math.log1p((percent if direction == "up" else -percent) / 100)
            words += " of at least " + str(percent).removesuffix(".0") + "%"
    return {"market": MARKETS[condition["market"]], "condition": {**query, "through_utc": completed_before},
            "horizon": horizon}, words


class Producer:
    """Read the independently installed Data owner; importing writes no pyc in Main."""
    def __init__(self, now, bindings=BINDINGS):
        self.bindings_path = str(bindings)
        bound = json.loads(Path(bindings).read_bytes())
        config = json.loads(Path(bound["statistics_config"]).read_bytes())
        root = Path(bound["statistics_code_root"])
        before = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        try:
            for name in ("tools", "tools.data_foundation", "tools.product"):
                package = importlib.import_module(name)
                extra = str(root.joinpath(*name.split(".")))
                if extra not in package.__path__:
                    package.__path__.append(extra)
            stats = importlib.import_module("tools.product.market_statistics_v1")
            self.history = importlib.import_module("tools.data_foundation.market_history_v1")
            self.stats = stats.StatisticsTools(config["store_path"], series=config.get("series"),
                as_of_utc=policy.utc(now).isoformat(), availability="as_known", events_path=config.get("events_path"))
            self.odds_reader = None
        finally:
            sys.path.pop(0)
            sys.dont_write_bytecode = before

    def stats_after(self, **query):
        return self.stats.stats_after(**query)

    def active_rows(self, market, completed_before):
        series = self.stats.series.get(market, {}).get("D1")
        if not series:
            return []
        if self.odds_reader is None:
            before = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                spec = importlib.util.spec_from_file_location("_cc510_desk_odds", MAIN / "tools/product/desk_odds_v1.py")
                self.odds_reader = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.odds_reader)
            finally:
                sys.dont_write_bytecode = before
        with self.history.MarketHistoryStore(self.stats.store_path, readonly=True) as store:
            result = store.history(market, "D1", series_id=series, as_of_utc=self.stats.as_of_utc,
                                   through_utc=completed_before, availability="as_known")
        return self.odds_reader.active_rows(result["bars"])


def census_context(table, market, active):
    """Use only this market's producer-selected active rows, largest sample first."""
    names = {code: side for code, side in active}
    columns = table["columns"]
    rows = [dict(zip(columns, row)) for row in table["by_market"].get(market, []) if row[0] in names]
    rows.sort(key=lambda r: -r["n"])
    return {"market": market, "period": table.get("markets", {}).get(market),
            "content_hash": table["content_hash"], "generated_at_utc": table["generated_at_utc"],
            "active_market_rows": [{**row, "side": names[row["behaviour"]],
                "condition": table["behaviours"][row["behaviour"]]} for row in rows],
            "count_note": "The census publishes n and mean R, not a market win numerator. Outcome counts below come from stats_after."}


def source_from_answer(answer, *, condition, query, condition_text, now, completed_before, census=None, bindings=BINDINGS):
    if answer.get("state") != "AVAILABLE":
        raise ValueError(answer.get("cause", "BASE_RATE_NO_COMPLETED_CASES"))
    if (answer.get("market") != query["market"] or answer.get("timeframe") != "D1"
            or answer.get("horizon_bars") != query["horizon"]
            or answer.get("condition") != {k: v for k, v in query["condition"].items() if k != "through_utc"}):
        raise ValueError("BASE_RATE_PRODUCER_MARKET_CONDITION_OR_HORIZON_MISMATCH")
    count, total = answer["terminal_up"]["hits"], answer["terminal_up"]["n"]
    if type(count) is not int or type(total) is not int or not 0 <= count <= total or total < 1 or total != answer["case_count"]:
        raise ValueError("BASE_RATE_PRODUCER_COUNT_INVALID")
    start, end = policy.utc(answer["sample_from_utc"]), policy.utc(answer["sample_through_utc"])
    known = max(policy.utc(s["known_at_utc"]) for s in answer["sources"])
    if start >= end or end > policy.utc(completed_before) or known > policy.utc(now):
        raise ValueError("BASE_RATE_PRODUCER_COMPLETION_OR_KNOWLEDGE_CLOCK_INVALID")
    through = (end - timedelta(microseconds=1)).astimezone(policy.ET).date().isoformat()
    period = start.astimezone(policy.ET).date().isoformat() + " to " + through
    horizon_text = "next-session" if query["horizon"] == 1 else "five-session"
    fact = {"kind": "base_rate", "markets": [condition["market"]], "count": count, "sample_count": total,
            "period_text": period, "through_date": through, "sample_end_date": through,
            "condition_text": condition_text, "headline_condition": condition,
            "horizon_sessions": query["horizon"], "horizon_text": horizon_text,
            "outcome_text": f"higher {horizon_text} closes",
            "series_id": answer["series_id"], "producer_tool": "stats_after",
            "rate_interval_95_pct": answer.get("rate_interval_95_pct"),
            "selection": answer.get("selection"), "zero_returns_in_denominator": answer.get("zero_returns_in_denominator")}
    label = LABELS[query["market"]]
    # A configured different source instrument must retain its own name.
    instruments = sorted({s["source_instrument"] for s in answer["sources"] if s.get("source_instrument")})
    expected = {"XAUUSD": "GC=F", "US500": "ES=F", "USOIL": "CL=F"}
    if query["market"] in expected and instruments != [expected[query["market"]]]:
        raise ValueError("BASE_RATE_SOURCE_INSTRUMENT_LABEL_UNRESOLVED")
    excerpt = f"{label}: {count} of {total} higher {horizon_text} closes after {condition_text}, {period} (desk count)."
    evidence = {"fact": fact, "excerpt": excerpt, "sources": answer["sources"], "census": census}
    identity = digest(evidence)
    return {"source_id": "reply-base-rate-" + identity, "kind": KIND, "label": label + " historical base rate",
            "excerpt": excerpt, "known_at_utc": known.isoformat(), "rights_class": "CC_OWN_ANALYSIS",
            "fact_binding": fact, "store_payload_sha256": identity,
            "source_attribution": [{"attribution": "desk count", "series_id": answer["series_id"]}],
            "context": [{"path": "/desk_odds", "display": json.dumps(census, sort_keys=True)}] if census else [],
            "artifact_binding": {"kind": "cc510_statistics", "bindings": str(bindings), "query": query,
                "condition": condition, "condition_text": condition_text, "as_of_utc": policy.utc(now).isoformat(),
                "completed_before_utc": completed_before, "producer_answer": answer, "census": census}}


def collect(posts, *, now, producer=None, odds_path=ODDS, bindings=BINDINGS):
    """One fact-collection hook; no acquisition, publication or replacement store."""
    now = policy.utc(now)
    selected = list({digest(c): c for post in posts for c in conditions(post["post_text"])}.values())
    if not selected:
        return [], []
    completed = datetime.combine(now.astimezone(policy.ET).date(), time.min, policy.ET).astimezone(timezone.utc).isoformat()
    sources, gaps, contexts = [], [], {}
    try:
        producer = producer or Producer(now, bindings)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        return [], [{"cause": "BASE_RATE_STATISTICS_READER_UNAVAILABLE", "error": type(exc).__name__}]
    try:
        table = json.loads(Path(odds_path).read_bytes())
        if policy.utc(table["generated_at_utc"]) > now:
            raise ValueError("DESK_ODDS_NOT_KNOWN_AT_CHECK")
        for market in {MARKETS[c["market"]] for c in selected}:
            active = producer.active_rows(market, completed)
            contexts[market] = census_context(table, market, active)
    except (OSError, ValueError, KeyError, TypeError, ImportError, sqlite3.Error) as exc:
        gaps.append({"cause": str(exc) if isinstance(exc, ValueError) else "DESK_ODDS_CONTEXT_UNAVAILABLE", "source": str(odds_path)})
    for condition in selected:
        for horizon in (1, 5):
            query, words = query_for(condition, horizon, completed)
            try:
                answer = producer.stats_after(**query)
                sources.append(source_from_answer(answer, condition=condition, query=query, condition_text=words,
                    now=now, completed_before=completed, census=contexts.get(query["market"]), bindings=bindings))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                gaps.append({"market": condition["market"], "horizon_sessions": horizon,
                             "cause": str(exc) if isinstance(exc, ValueError) else "BASE_RATE_PRODUCER_ANSWER_UNUSABLE"})
    sources.sort(key=lambda s: -s["fact_binding"]["sample_count"])
    return sources, gaps


def check_condition(post, fact, draft=None):
    """A source selected for one move never becomes a different move's count."""
    bound = fact["headline_condition"]
    matches = []
    for candidate in conditions(post["post_text"]):
        if any(candidate.get(k) != bound.get(k) for k in ("market", "kind", "direction")):
            continue
        if bound["kind"] == "move" and bound["minimum_pct"] is not None:
            if candidate["minimum_pct"] is None or candidate["minimum_pct"] < bound["minimum_pct"]:
                continue
        matches.append(candidate)
    if not matches or fact["markets"] != [bound["market"]]:
        raise ValueError("FACT_BASE_RATE_TARGET_CONDITION_NOT_MET")
    if draft and fact["horizon_text"] not in draft["draft_text"]:
        raise ValueError("FACT_BASE_RATE_FORWARD_HORIZON_NOT_STATED")
    if draft and fact.get("outcome_text") and fact["outcome_text"] not in draft["draft_text"]:
        raise ValueError("FACT_BASE_RATE_FORWARD_OUTCOME_CHANGED")


def resolve(bound):
    artifact = bound["artifact_binding"]
    producer = Producer(artifact["as_of_utc"], artifact["bindings"])
    answer = producer.stats_after(**artifact["query"])
    source = source_from_answer(answer, condition=artifact["condition"], query=artifact["query"],
        condition_text=artifact["condition_text"], now=artifact["as_of_utc"],
        completed_before=artifact["completed_before_utc"], census=artifact.get("census"), bindings=artifact["bindings"])
    if source["source_id"] != bound["source_id"] or source["store_payload_sha256"] != bound["store_payload_sha256"]:
        raise ValueError("REPLY_SOURCE_BINDING_CHANGED")
    return source
