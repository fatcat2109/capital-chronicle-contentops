"""CC-495: section 7 of Jim's voice guide, enforced before private delivery.

The rejected 11 November draft is the measured failure behind these checks.
Source clocks describe the observation, never the report's generation time.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from zoneinfo import ZoneInfo

from live_contentops.x_reply_topics_v1 import driver_links

ET = ZoneInfo("America/New_York")
POLICY = "CC495_REPLY_FACT_V1"
SEND_SECONDS = 15 * 60
MARKETS = {
    "NDX": r"\b(?:nasdaq[ -]?100|ndx|nq(?:=f)?)\b",
    "NASDAQ": r"\bnasdaq\b",
    "SPX": r"\b(?:s&p(?:\s*500)?|s\s*&\s*p(?:\s*500)?|spx|us500|es=f)\b",
    "DOW": r"\b(?:dow|djia|us30)\b",
    "XAUUSD": r"\b(?:gold|xauusd|gc=f)\b",
    "XAGUSD": r"\b(?:silver|xagusd)\b",
    "WTI": r"\b(?:wti|usoil|crude oil|cl=f)\b",
    "BRENT": r"\bbrent\b",
    "BTCUSD": r"\b(?:bitcoin|btc(?:usd|usdt|-usd)?)\b",
    "EURUSD": r"\b(?:eur\s*/?\s*usd|euro)\b",
    "USDJPY": r"\b(?:usd\s*/?\s*jpy|yen|boj)\b",
    "US2Y": r"\b(?:us2y|2[ -]year|two[ -]year)\b",
    "US10Y": r"\b(?:us10y|10[ -]year|ten[ -]year)\b",
    "US30Y": r"\b(?:us30y|30[ -]year|thirty[ -]year)\b",
    "JP2Y": r"\b(?:jp2y|japan(?:ese)? 2[ -]year)\b",
    "JP10Y": r"\b(?:jp10y|japan(?:ese)? 10[ -]year)\b",
    "EA2Y": r"\b(?:ea2y|euro area 2[ -]year)\b",
    "EA10Y": r"\b(?:ea10y|euro area 10[ -]year)\b",
    "RATES": r"\b(?:yields?|treasur\w*|rates?|fed|fomc)\b",
    "DXY": r"\b(?:dxy|dollar(?: index)?)\b",
    "EQUITIES": r"\b(?:stocks?|equities|indices)\b",
}
POSITIONING = re.compile(r"\b(?:cftc|cot|positioning|speculators?|net (?:long|short))\b", re.I)
DRIVERS = {"US2Y", "US10Y", "US30Y", "JP2Y", "JP10Y", "EA2Y", "EA10Y", "RATES", "DXY"}
RELATION = re.compile(r"\b(?:weighs?|weights?|pressures?|supports?|headwinds?|tailwinds?|lifts?|"
                      r"helps?|hurts?|costs?|discount|sensitive|sensitivity|limits?|caps?|"
                      r"drives?|driver|makes?|leaves?|raises?|lowers?|means?)\b", re.I)


def utc(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("NO_USABLE_FACT_OBSERVATION_CLOCK")
    return result.astimezone(timezone.utc)


def markets(text):
    found = {key for key, pattern in MARKETS.items() if re.search(pattern, text, re.I)}
    if "NDX" in found:
        found.discard("NASDAQ")
    if found & {"US2Y", "US10Y", "US30Y"}:
        found.discard("RATES")
    if found & {"JP2Y", "EA2Y"}:
        found.discard("US2Y")
    if found & {"JP10Y", "EA10Y"}:
        found.discard("US10Y")
    if found & {"SPX", "NDX", "NASDAQ", "DOW"}:
        found.discard("EQUITIES")
    return found


def target_markets(post):
    """Keep explicit instruments distinct; otherwise include the named driver map."""
    direct = markets(post["post_text"])
    if direct - {"EQUITIES", "RATES"}:
        return direct
    return direct | {market for link in driver_links(post["post_text"]) for market in link["markets"]}


def _day(text, reference):
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if match:
        return date.fromisoformat(match[1])
    match = re.search(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+(20\d{2}))?\b", text, re.I)
    if not match:
        match = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})(?:,?\s+(20\d{2}))?\b", text, re.I)
        if not match:
            return None
        day, month, year = match[2], match[1], match[3]
    else:
        day, month, year = match[1], match[2], match[3]
    month = next(i for i, name in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)
                 if name.casefold() == month[:3].casefold())
    result = date(int(year or reference.year), month, int(day))
    if not year and result > reference:
        result = result.replace(year=result.year - 1)
    return result


def describe(source, fact_text=None):
    """Derive legacy facts from their own sentence; typed owners supply exact clocks."""
    excerpt = source["excerpt"]
    sentences = re.split(r"(?<=[.!?])\s+|\n", excerpt)
    sentence = next((s for s in sentences if fact_text and fact_text in s), excerpt)
    typed = source.get("fact_binding")
    if typed:
        return {**typed, "sentence": sentence}
    reference = utc(source["known_at_utc"]).astimezone(ET).date()
    kind = "positioning" if POSITIONING.search(sentence) else (
        "daily" if re.search(r"\b(?:close[ds]?|daily|official yield)\b", sentence, re.I) else "session")
    # A report date in the same sentence cannot replace the data's own date.
    explicit = re.search(r"\b(?:CFTC|COT|positioning|positions?|data)\b.{0,45}?\b(?:for|as of|dated)\s+", sentence, re.I)
    if explicit:
        observation = _day(sentence[explicit.end():], reference)
    else:
        date_pattern = (r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+20\d{2})?\b|"
                        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+20\d{2})?\b")
        dates = {_day(m[0], reference) for m in re.finditer(date_pattern, sentence, re.I)}
        observation = next(iter(dates)) if len(dates) == 1 else None
    return {"kind": kind, "markets": sorted(markets(sentence) or markets(source.get("label", ""))),
            "as_of_date": observation.isoformat() if observation else None, "sentence": sentence}


def _trading_age(start, end, market_ids):
    """Count completed market dates, including the US cash/bond holiday calendar."""
    if start > end:
        return -1
    if "BTCUSD" in market_ids:
        return (end - start).days
    from live_contentops.x_reply_trading_dates_v1 import trading_date
    return sum(trading_date(start + timedelta(days=n), market_ids) for n in range(1, (end-start).days+1))


def check_fact(post, source, *, now, draft=None):
    """Return the source-bound age description, or one specific rule's refusal."""
    if not source or not source.get("excerpt"):
        raise ValueError("NO_USABLE_FACT")  # rule 6
    now, posted = utc(now), utc(post["post_time_utc"])
    if utc(source["known_at_utc"]) > now:
        raise ValueError("NO_USABLE_FACT_KNOWN_AFTER_CHECK")
    fact = describe(source, (draft or {}).get("fact_text"))
    kind = fact.get("kind")
    explicit = markets(post["post_text"])
    targets, fact_markets = target_markets(post), set(fact.get("markets", []))
    if not targets or not fact_markets:
        raise ValueError("FACT_MARKET_UNIDENTIFIED")  # rule 5
    direct = bool(explicit & fact_markets) or (
        "EQUITIES" in explicit and bool(fact_markets & {"SPX", "NDX", "NASDAQ", "DOW"}))
    linked = not direct and bool((targets - explicit) & fact_markets)
    if linked:
        drivers = {link["driver"] for link in driver_links(post["post_text"])
                   if set(link["markets"]) & fact_markets}
        if draft and not any(markets(sentence) & fact_markets and RELATION.search(sentence)
                             and drivers & {link["driver"] for link in driver_links(sentence)}
                             for sentence in re.split(r"(?<=[.!?])\s+", draft["draft_text"])):
            raise ValueError("FACT_DRIVER_LINK_NOT_STATED")
    elif not direct:
        # Another index never substitutes, even if the writer invents a link.
        if fact_markets & {"SPX", "NDX", "NASDAQ", "DOW"} or not fact_markets & DRIVERS:
            raise ValueError("FACT_MARKET_MISMATCH")
        if draft and not any(markets(s) & targets and markets(s) & fact_markets and RELATION.search(s)
                             for s in re.split(r"(?<=[.!?])\s+", draft["draft_text"])):
            raise ValueError("FACT_DRIVER_LINK_NOT_STATED")
    day = now.astimezone(ET).date()
    if kind == "base_rate":  # rule 4
        if fact.get("headline_condition"):
            from live_contentops.x_reply_base_rates_v1 import check_condition
            check_condition(post, fact, draft)
        through = date.fromisoformat(fact["through_date"]) if fact.get("through_date") else None
        if (type(fact.get("count")) is not int or type(fact.get("sample_count")) is not int
                or not 0 <= fact["count"] <= fact["sample_count"] or fact["sample_count"] < 1
                or not fact.get("period_text") or not through or through >= day):
            raise ValueError("FACT_BASE_RATE_COUNT_PERIOD_OR_COMPLETION_INVALID")
        if draft and not (re.search(r"\b" + str(fact["count"]) + r"\s+(?:of|out of)\s+(?:the\s+)?(?:last\s+)?"
                                   + str(fact["sample_count"]) + r"\b", draft["draft_text"], re.I)
                          and fact["period_text"].casefold() in draft["draft_text"].casefold()):
            raise ValueError("FACT_BASE_RATE_COUNT_AND_PERIOD_NOT_STATED")
        if draft and fact.get("condition_text") and fact["condition_text"].casefold() not in draft["draft_text"].casefold():
            raise ValueError("FACT_BASE_RATE_CONDITION_NOT_STATED")
        if draft and fact.get("window") and not re.search(r"\b" + re.escape(fact["window"][:-1]) + r"[ -]?(?:minutes?|mins?|m)\b", draft["draft_text"], re.I):
            raise ValueError("FACT_BASE_RATE_REACTION_WINDOW_NOT_STATED")
        age_text = ("historical count; last observation " + date.fromisoformat(fact["sample_end_date"]).strftime("%d %b %Y")
                    if fact.get("sample_end_date") else "historical count through " + through.strftime("%d %b %Y"))
    elif kind == "positioning":  # rule 3
        if not fact.get("as_of_date"):
            raise ValueError("FACT_POSITIONING_AS_OF_DATE_REQUIRED")
        asof = date.fromisoformat(fact["as_of_date"])
        age = (day - asof).days
        if not 0 <= age <= 3:
            raise ValueError("FACT_POSITIONING_OVER_THREE_CALENDAR_DAYS")
        if not POSITIONING.search(post["post_text"]):
            raise ValueError("FACT_POSITIONING_TARGET_NOT_POSITIONING")
        if re.search(r"\b(?:rises?|rall(?:y|ies)|falls?|drops?|session high|today.?s move)\b", post["post_text"], re.I):
            raise ValueError("FACT_POSITIONING_CANNOT_EXPLAIN_SESSION_MOVE")
        age_text = f"{age} calendar day{'s' if age != 1 else ''} old"
    elif kind == "daily":  # rule 2
        if not fact.get("as_of_date"):
            raise ValueError("FACT_DAILY_OBSERVATION_DAY_REQUIRED")
        asof = date.fromisoformat(fact["as_of_date"])
        age = _trading_age(asof, day, fact_markets)
        if not 0 <= age <= 1:
            raise ValueError("FACT_DAILY_OVER_ONE_TRADING_DAY")
        if draft and _day(draft["draft_text"], day) != asof:
            raise ValueError("FACT_DAILY_SENTENCE_DAY_NOT_STATED")
        age_text = f"{age} trading day{'s' if age != 1 else ''} old"
    elif kind == "session":  # rule 1
        if not fact.get("observed_at_utc"):
            raise ValueError("FACT_SESSION_OBSERVATION_CLOCK_REQUIRED")
        observed = utc(fact["observed_at_utc"])
        if (observed > now or observed.astimezone(ET).date() != posted.astimezone(ET).date()
                or (posted - observed).total_seconds() > 3600):
            raise ValueError("FACT_SESSION_NOT_CURRENT_WITHIN_60_MINUTES")
        local = observed.astimezone(ET)
        age_text = ("today, " if local.date() == day else local.strftime("%d %b %Y, ")) + local.strftime("%I:%M %p ET").lstrip("0")
    else:
        raise ValueError("NO_USABLE_FACT_KIND")
    return {**fact, "age_text": age_text, "checked_at_utc": now.isoformat(), "policy": POLICY}


def check_send_time(post, *, now):
    age = (utc(now) - utc(post["post_time_utc"])).total_seconds()
    if not 0 <= age <= SEND_SECONDS:  # rule 7; checked again after optional media
        raise ValueError("TARGET_OVER_15_MINUTES_AT_SEND")
    return age / 60
