"""CC-469: a TradingView idea pack for each new plan in the six markets, posted by Jim by hand.

The pack rides on the posting desk (manual_desk_v1, CC-748). It is built only from the plan
post's own stored fields: the base, bull and bear cases with their odds and causes, the entry
zone, the invalidation level, and the plan's dates and horizon. Nothing is invented.

TradingView's House Rules (https://www.tradingview.com/house-rules/, read 23 Nov 2026) bind the
public parts (title, description and the labels drawn on the chart):
  - no links or references to any website, social media, messaging or email contact;
  - no company or brand names (our own brand included);
  - the site's language, English;
  - no title in capitals, and real analysis with a description.
Our own rules bind them too: no profit target anywhere (decisions 40 and 157), base, bull and
bear cases with causes (decision 158), no AI label or model name (decision 109), dated lines
instead of "today", public times in ET (decision 90), grouped and rounded numbers.

check_idea() enforces all of it on every pack. The "how to post" note and the chart symbol are
Jim's private instructions, not public copy. No browser, no network, no model call.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from . import scenario_voice_v1 as voice
from .public_time_v1 import public_datetime
from .tradingview_snapshot_v1 import INTERVAL_LABELS, SYMBOLS, interval_for

SCHEMA = "contentops.tradingview_idea_pack.v1"
# Decision 79's six markets and CC-788's Nasdaq 100, by the asset ids Main exports.
MARKETS = {"XAUUSD": "Gold", "US500": "S&P 500", "EURUSD": "EUR/USD", "USDJPY": "USD/JPY",
           "USOIL": "WTI crude oil", "BTCUSD": "Bitcoin", "USTEC": "Nasdaq 100"}
ALIASES = {"GOLD": "XAUUSD", "SPX": "US500", "WTI": "USOIL", "BTC": "BTCUSD", "NDX": "USTEC", "NAS100": "USTEC"}
NEW_PLAN_KINDS = {"setup", "update"}
TIMEFRAMES = {"60": "1-hour", "240": "4-hour", "D": "daily"}
HORIZONS = {"SHORT": "short-term", "MID": "mid-term", "LONG": "long-term", "INVESTMENT": "investment"}
TITLE_LIMIT = 100
NOTICE = ("Analysis only, not financial advice or a recommendation. "
          "The author may hold positions in the markets discussed.")


class IdeaError(ValueError):
    """A fixed cause only."""


# ------------------------------------------------------------------ the check

_URL = re.compile(r"https?://|\bwww\.|\b[\w-]+\.(?:com|net|org|io|co|ai|app|dev|me|tv|xyz|info|biz|news|uk|"
                  r"us|vn|gg|ly|so|to|link|site|online|page|substack|blog)\b(?!\.\d)", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
_HANDLE = re.compile(r"(?<![\w@])@[A-Za-z_]\w{1,}")
_CONTACT = re.compile(r"\b(?:telegram|t\.me|discord|substack|linkedin|youtube|twitter|x\.com|facebook|"
                      r"instagram|threads|whatsapp|wechat|signal group|newsletter|subscribe|e-?mail|"
                      r"dm me|message me|link in (?:bio|profile)|our (?:site|website|channel|blog))\b", re.I)
_BRAND = re.compile(r"capital\s*chronicle|capitalnicle|capitalchronicle", re.I)
_TARGET_WORDS = re.compile(r"\b(?:take[- ]?profit|TP\d?|profit objective|price objective|targets?)\b", re.I)
_POLICY_TARGET = re.compile(r"\b(?:inflation|rates?|yield|federal funds|employment|deficit)\s+targets?\b", re.I)
_AI = re.compile(r"\b(?:AI|A\.I\.|artificial intelligence|LLM|language model|machine learning|neural|"
                 r"GPT[\w.-]*|ChatGPT|Claude|Fable|Opus|Sonnet|Haiku|Codex|Gemini|Antigravity|chatbot|bot)\b")
_RELATIVE = re.compile(r"\b(?:today|tonight|tomorrow|yesterday|this (?:morning|afternoon|evening|week)|"
                       r"next week|last week|right now)(?:'s|’s)?(?!\w)", re.I)
_ALLOWED_NON_ASCII = set("–—’‘“”…·×±≈€£¥°")


def _title_in_capitals(title):
    words = re.findall(r"[A-Za-z][A-Za-z']{3,}", title)
    shouted = [w for w in words if w.isupper()]
    return title.upper() == title or (words and len(shouted) * 2 > len(words))


def check_idea(idea):
    """Refuse a pack whose public parts break the House Rules or our own rules. Returns 'PASS'."""
    from .plan_analysis_pages_v1 import public_filter

    title = str(idea.get("title") or "").strip()
    description = str(idea.get("description") or "").strip()
    labels = [str(d.get("label") or "") for d in (idea.get("chart") or {}).get("draw") or []]
    public = "\n".join([title, description, *labels])
    if not title or len(description) < 200:
        raise IdeaError("TRADINGVIEW_IDEA_DESCRIPTION_REQUIRED")
    if _URL.search(public) or _EMAIL.search(public) or _HANDLE.search(public):
        raise IdeaError("TRADINGVIEW_IDEA_LINK_FORBIDDEN")
    if _BRAND.search(public):
        raise IdeaError("TRADINGVIEW_IDEA_BRAND_FORBIDDEN")
    if _CONTACT.search(public):
        raise IdeaError("TRADINGVIEW_IDEA_CONTACT_REFERENCE_FORBIDDEN")
    try:
        voice.validate_copy(public)
    except ValueError:
        raise IdeaError("TRADINGVIEW_IDEA_TARGET_FORBIDDEN") from None
    if any(not _POLICY_TARGET.search(public[max(0, m.start() - 30):m.end()]) for m in _TARGET_WORDS.finditer(public)):
        raise IdeaError("TRADINGVIEW_IDEA_TARGET_FORBIDDEN")
    if _AI.search(public):
        raise IdeaError("TRADINGVIEW_IDEA_AI_LABEL_FORBIDDEN")
    if _RELATIVE.search(public):
        raise IdeaError("TRADINGVIEW_IDEA_RELATIVE_DAY_FORBIDDEN")
    if any(ord(ch) > 127 and ch not in _ALLOWED_NON_ASCII for ch in public):
        raise IdeaError("TRADINGVIEW_IDEA_NOT_ENGLISH")
    if _title_in_capitals(title):
        raise IdeaError("TRADINGVIEW_IDEA_TITLE_CAPITALS")
    if len(title) > TITLE_LIMIT:
        raise IdeaError("TRADINGVIEW_IDEA_TITLE_TOO_LONG")
    if not (re.search(r"^Base case\b", description, re.M) and re.search(r"^(?:Bull|Bear) case\b", description, re.M)):
        raise IdeaError("TRADINGVIEW_IDEA_SCENARIOS_REQUIRED")
    try:
        public_filter(public)
    except ValueError as exc:
        raise IdeaError("TRADINGVIEW_IDEA_PUBLIC_FILTER_" + str(exc).split(":")[0]) from None
    return "PASS"


# ------------------------------------------------------------- small formats

def num(value):
    """Grouped and rounded to the price's size: 61,941 · 3,733.5 · 159.11 · 1.0969."""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise IdeaError("TRADINGVIEW_IDEA_NUMBER_INVALID") from None
    if not d.is_finite():
        raise IdeaError("TRADINGVIEW_IDEA_NUMBER_INVALID")
    size = abs(d)
    places = 0 if size >= 10000 else 1 if size >= 1000 else 2 if size >= 10 else 4
    text = f"{d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,.{places}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def when(value):
    """Decision 90: 'Fri 20 Nov 2026, 3:15 AM ET'."""
    local = public_datetime(value)
    return f"{local:%a} {local.day} {local:%b %Y}, " + f"{local:%I:%M %p}".lstrip("0") + " ET"


def _utc(value):
    try:
        return public_datetime(value) if value else None
    except (TypeError, ValueError):
        return None


_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]00:00)")
_DAY_CLOCK = re.compile(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{2}):(\d{2})Z\b")
_BLOCK = re.compile(r",?\s*\bper block [^\s,;]+", re.I)
# Desk-internal words and codes that never belong in public analysis.
_INTERNAL = re.compile(r"\b[A-Za-z]+_[A-Za-z0-9_]+\b|\b[0-9a-f]{12,}\b|\bcc\d{3,}\b|\bshock-\d|\bPrior:|\bplan [0-9a-f]{8,}|"
                       r"\bbroker\b|\bstate model\b|\bnormal days?\b|\blane(?:'s|’s)?\b|\byardstick\b|\bbar age\b|"
                       r"\bblock\b|\bdesk(?:'s|’s)?\b|\balways-long\b|\d{2}:\d{2}Z\b", re.I)
_SHOUT = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")
_ACRONYMS = {
    "USD", "JPY", "EUR", "GBP", "CHF", "AUD", "CAD", "CNY", "BTC", "ETH", "BTCUSD", "USDJPY", "EURUSD", "XAUUSD",
    "US500", "USOIL", "USTEC", "WTI", "SPX", "NDX", "VIX", "DVOL", "DXY", "ETF", "ETFS", "COT", "CFTC", "CPI", "PPI", "PCE",
    "NFP", "GDP", "PMI", "ISM", "ADP", "JOLTS", "FOMC", "ECB", "BOJ", "BOE", "SNB", "RBA", "MOF", "OPEC", "EIA",
    "IEA", "API", "IMF", "LNG", "OIS", "SOFR", "QT", "QE", "ATH", "YTD", "NYMEX", "CME", "COMEX", "ICE", "SEC",
    "US10Y", "US2Y", "UST", "TIPS", "M15", "H1", "H4", "D1", "W1", "UTC", "ET",
}
_LONG_NUMBER = re.compile(r"(?<![\w.,:/])(\d{4,}(?:\.\d+)?)(?![\w%:/]|\.\d|,\d)")


def _grouped(match):
    text = match.group(1)
    if "." not in text and len(text) == 4 and 1900 <= int(text) <= 2100:
        return text  # a year stays a year
    return num(text)


_BARE_CLOCK = re.compile(r"\b(?:(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day )?(\d{2}):(\d{2})Z\b")


_DATE_ONLY = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _dated(text, year, anchor=None):
    """Source clocks in UTC become public ET dates (decision 90); a clock it cannot place stays and is dropped."""
    text = _ISO.sub(lambda m: when(m.group(0).replace("Z", "+00:00")), text)

    def day_clock(m):
        try:
            return when(f"{year}-{_MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}T{m.group(3)}:{m.group(4)}:00+00:00")
        except ValueError:
            return m.group(0)

    text = _DAY_CLOCK.sub(day_clock, text)
    if anchor is not None:
        # A bare "20:00Z" in a case names the plan's own horizon end when the clock matches it.
        utc = anchor.astimezone(timezone.utc)
        text = _BARE_CLOCK.sub(lambda m: when(utc) if (int(m.group(1)), int(m.group(2))) == (utc.hour, utc.minute)
                               else m.group(0), text)

    def date_only(m):
        month = int(m.group(2))
        if not 1 <= month <= 12 or not 1 <= int(m.group(3)) <= 31:
            return m.group(0)
        return f"{int(m.group(3))} {_MONTH_NAMES[month - 1]} {m.group(1)}"

    return _DATE_ONLY.sub(date_only, text)


_MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_MONTHS = {m: n for n, m in enumerate(_MONTH_NAMES, start=1)}


def clean(text, *, year, anchor=None, keep=2, limit=420):
    """The plan's own words, minus desk-internal codes and relative days; numbers grouped.

    A clause that carries an internal code is left out whole, never rewritten.
    """
    text = _dated(_BLOCK.sub("", " ".join(str(text or "").split())), year, anchor)
    text = re.sub(r"\bGOLD\b", "gold", text)
    kept = []
    for clause in re.split(r"(?<=[.;])\s+", text):
        clause = clause.strip().rstrip(";").strip()
        if (not clause or clause.endswith(":") or len(clause.split()) < 4 or re.match(r"I\b", clause)
                or _INTERNAL.search(clause) or _RELATIVE.search(clause)):
            continue
        if any(word not in _ACRONYMS for word in _SHOUT.findall(clause)):
            continue
        clause = _LONG_NUMBER.sub(_grouped, clause)
        clause = clause[0].upper() + clause[1:]
        if not clause.endswith((".", "!", "?")):
            clause += "."
        if kept and len(" ".join(kept + [clause])) > limit:
            break
        kept.append(clause)
        if len(kept) >= keep:
            break
    return " ".join(kept)


# ------------------------------------------------------------------ the pack

def market_of(payload):
    source = payload.get("source_plan") if isinstance(payload.get("source_plan"), Mapping) else {}
    asset = str(payload.get("symbol") or source.get("asset_id") or "").upper()
    asset = ALIASES.get(asset, asset)
    return asset if asset in MARKETS else None


def wanted(payload):
    """A new plan (its setup, or the update that replaced an unsent setup) in one of the six markets."""
    return payload.get("kind") in NEW_PLAN_KINDS and bool(payload.get("plan_id")) and market_of(payload) is not None


def _case_line(label, branch, side):
    probability = branch.get("probability_pct")
    odds = ""
    if type(probability) in (int, float) and 0 <= probability <= 100:
        odds = format(Decimal(str(probability)).normalize(), "f") + "%"
    if label == "Base case":
        head = f"Base case ({', '.join(p for p in (side, odds) if p)})" if side or odds else "Base case"
    else:
        head = f"{label} ({odds})" if odds else label
    return head


def build_idea(payload):
    """The idea pack for one stored plan post, or None when the post is not a new six-market plan."""
    if not wanted(payload):
        return None
    asset = market_of(payload)
    market = MARKETS[asset]
    levels = payload.get("levels") if isinstance(payload.get("levels"), Mapping) else {}
    source = payload.get("source_plan") if isinstance(payload.get("source_plan"), Mapping) else {}
    scenario = levels.get("scenario_analysis") or source.get("scenario_analysis") or {}
    direction = str(levels.get("direction") or source.get("direction") or "").lower()
    if direction not in {"bearish", "bullish"}:
        raise IdeaError("TRADINGVIEW_IDEA_DIRECTION_REQUIRED")
    low, high = levels.get("zone_low"), levels.get("zone_high")
    if low is None or high is None:
        zone = source.get("zone") or {}
        low, high = zone.get("minimum"), zone.get("maximum")
    invalidation = levels.get("invalidation_level")
    if low is None or high is None or invalidation is None:
        raise IdeaError("TRADINGVIEW_IDEA_ZONE_OR_INVALIDATION_REQUIRED")
    low, high = sorted((Decimal(str(low)), Decimal(str(high))))
    written = _utc(payload.get("registered_at_utc") or levels.get("registered_at_utc")
                   or source.get("registered_at_utc") or payload.get("at_utc"))
    if written is None:
        raise IdeaError("TRADINGVIEW_IDEA_PLAN_DATE_REQUIRED")
    year = written.year
    deadline = _utc(levels.get("valid_until_utc") or levels.get("entry_deadline_utc")
                    or payload.get("entry_deadline_utc") or source.get("entry_deadline_utc"))
    horizon_end = None
    for value in (levels.get("time_exit_utc"), payload.get("time_exit_utc"), scenario.get("horizon_end_utc")):
        moment = _utc(value)
        if moment and moment > written:
            horizon_end = moment
            break
    lane = str(source.get("horizon_lane") or (levels.get("image_source_plan") or {}).get("horizon_lane") or "").upper()

    side = "bear" if direction == "bearish" else "bull"
    cases = voice.case_records({"scenario_analysis": scenario, "direction": direction.upper()})
    if not cases or cases[0][0] != "base_case":
        raise IdeaError("TRADINGVIEW_IDEA_BASE_CASE_REQUIRED")
    lines = []
    for key, label, branch in cases:
        move = clean(branch.get("market_move"), year=year, anchor=horizon_end, keep=2)
        if key == "base_case" and not move:
            raise IdeaError("TRADINGVIEW_IDEA_BASE_CASE_REQUIRED")
        if not move or label not in {"Base case", "Bull case", "Bear case"}:
            continue
        cause_text = branch.get("cause") or branch.get("mechanism") or (
            scenario.get("mechanism") if key == "base_case" else
            scenario.get("opposite_mechanism") if key == "main_alternative" else None)
        lines.append(_case_line(label, branch, side if key == "base_case" else "") + ": " + move)
        cause = clean(cause_text, year=year, anchor=horizon_end, keep=2)
        if cause:
            lines.append("Why: " + cause)
    if not any(line.startswith(("Bull case", "Bear case")) for line in lines):
        raise IdeaError("TRADINGVIEW_IDEA_ALTERNATIVE_CASE_REQUIRED")
    for field, label in (("priced", "Priced in"), ("positioning", "Positioning and sentiment"),
                         ("confirmations", "What confirms the base case")):
        text = clean(scenario.get(field) or levels.get(field), year=year, keep=2)
        if text:
            lines.append(f"{label}: {text}")

    zone_text = num(low) if low == high else f"{num(low)}–{num(high)}"
    calls = payload.get("conditional_calls") or []
    call = calls[0] if calls and isinstance(calls[0], Mapping) else {}
    condition = clean(call.get("condition"), year=year, keep=1).rstrip(".")
    plan_line = f"The plan: {direction} on {market}"
    plan_line += f" if {condition[0].lower() + condition[1:]}." if condition else "."
    plan_line += f" Entry zone {zone_text}."
    lines.append(plan_line)
    invalid_line = f"Invalidation: {num(invalidation)}."
    call_invalidation = clean(call.get("invalidation"), year=year, keep=1)
    if call_invalidation:
        invalid_line += " " + call_invalidation
    reason = clean(scenario.get("invalidation_text"), year=year, keep=1)
    if reason:
        invalid_line += " The view is wrong on " + reason[0].lower() + reason[1:]
    lines.append(invalid_line)
    dates = [f"Plan of {when(written)}"]
    if deadline and deadline > written:
        dates.append(f"entry window open until {when(deadline)}")
    if horizon_end:
        dates.append(f"the view runs to {when(horizon_end)}")
    horizon = HORIZONS.get(lane)
    lines.append("Dates: " + "; ".join(dates) + (f" ({horizon} horizon)." if horizon else "."))
    lines.append(NOTICE)

    interval = interval_for((horizon_end or deadline or written).isoformat(), written.isoformat())
    against = "above" if direction == "bearish" else "below"
    title = f"{market}: {direction} at {zone_text}, wrong {against} {num(invalidation)} ({written.day} {written:%b %Y})"
    idea = {
        "schema_version": SCHEMA, "plan_id": payload["plan_id"], "market": asset, "title": title,
        "description": "\n\n".join(lines),
        "chart": {"symbol": SYMBOLS[asset], "interval": interval,
                  "timeframe": TIMEFRAMES.get(interval, INTERVAL_LABELS.get(interval, interval)),
                  "draw": [{"tool": "rectangle", "low": num(low), "high": num(high), "label": "Entry zone"},
                           {"tool": "horizontal line", "level": num(invalidation), "label": "Invalidation"}]},
    }
    idea["how_to_post"] = (f"In TradingView open {idea['chart']['symbol']} on the {idea['chart']['timeframe']} chart, "
                           f"shade the entry zone {zone_text} and draw the invalidation line at {num(invalidation)} "
                           "(nothing else), press Publish idea, paste the title and description, and post it yourself.")
    return idea


def idea_entry(payload):
    """A desk entry: READY with its check, WITHHELD with a fixed cause, or None for other posts."""
    try:
        idea = build_idea(payload)
        if idea is None:
            return None
        idea["check"] = check_idea(idea)
    except IdeaError as exc:
        return {"status": "WITHHELD", "cause": str(exc), "plan_id": payload.get("plan_id")}
    except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
        return {"status": "WITHHELD", "cause": "TRADINGVIEW_IDEA_" + type(exc).__name__.upper(),
                "plan_id": payload.get("plan_id")}
    idea["status"] = "READY"
    return idea
