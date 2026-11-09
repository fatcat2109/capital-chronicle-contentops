"""Decision 107: public instrument names in the existing article path.

The map supplies names, never prices or a conversion between instruments.
An internal market id remains valid in source and media binding metadata.
"""
from __future__ import annotations

import html
import re

POLICY = "JIM_DECISION_107"
INSTRUMENTS = {
    "XAUUSD": ("gold", ("GC", "MGC", "GLD", "IAU")),
    "US500": ("S&P 500", ("ES", "MES", "SPY", "VOO")),
    "USOIL": ("WTI", ("CL", "MCL", "USO")),
    "EURUSD": ("EUR/USD", ("6E", "FXE")),
    "USDJPY": ("USD/JPY", ("6J", "FXY")),
    "BTCUSD": ("Bitcoin", ("BTC", "MBT", "IBIT", "FBTC")),
}
MARKET_PATTERNS = {
    "XAUUSD": r"\bgold\b",
    "US500": r"\bS\s*&\s*P\s*500\b",
    "USOIL": r"\bWTI\b|\bcrude oil\b",
    "EURUSD": r"\bEUR\s*/?\s*USD\b|\beuro\s*[/–-]\s*dollar\b",
    "USDJPY": r"\bUSD\s*/?\s*JPY\b|\bdollar\s*[/–-]\s*yen\b",
    "BTCUSD": r"\bBitcoin\b",
}
GUIDANCE = """
CC382_PUBLIC_INSTRUMENTS / Jim decision 107:
Articles, market wraps, event previews and reviews name at least one futures or
ETF instrument for EACH market covered, including markets in the scenarios:
gold: GC or MGC futures, GLD or IAU, spot gold;
S&P 500: ES or MES futures, SPY or VOO, the index;
WTI: CL or MCL futures, USO;
EUR/USD: spot, 6E futures, FXE;
USD/JPY: spot, 6J futures, FXY;
Bitcoin: BTC or MBT futures, IBIT or FBTC, spot Bitcoin.
Identify futures as futures and ETFs as ETFs. A name is not a measured reaction.
Use held Main reports, dossiers and cited sources for instrument-specific moves
and flows when supplied. Without that evidence, name the available instruments
but omit their moves, flows or prices. Never relabel a spot, index or broker price
as a futures or ETF price, or copy one instrument's level onto another. 6J and FXY
express the yen versus the dollar: do not claim their direction equals USD/JPY.
Public prose, SEO, social copy and media captions never say CFD, US500, USOIL,
XAUUSD or BTCUSD, except an article specifically about CFDs. Internal source ids,
article.market_asset, source excerpts and snapshot bindings retain exact values.
Charts use the existing tradingview_snapshot_v1.SYMBOLS decision-107 feeds;
TradingView's own header and attribution remain intact. Do not invent data or
change decision 40's notices, decision 106's cadence, or any publication clock.
"""

_FIELDS = ("title", "subtitle", "dek", "search_title", "meta_description", "social_hook", "attribution",
           "substack_body_markdown", "body_markdown", "text", "caption", "alt_text",
           "full_text", "root_text", "editorial_scope_notice", "social_mechanism_summary",
           "social_policy_summary", "social_cross_asset_summary")
_FORBIDDEN = re.compile(r"\b(?:CFDs?|US500|USOIL|XAUUSD|BTCUSD)\b", re.I)


def public_text(value):
    """Read authored display fields only; never scan source/binding metadata."""
    if not isinstance(value, dict):
        return ""
    text = "\n".join(str(value[k]) for k in _FIELDS if value.get(k))
    for key in ("posts", "social_scenarios", "native_platform_variants", "publisher_light_variants"):
        rows = value.get(key) or []
        if isinstance(rows, dict):
            rows = rows.values()
        text += "\n" + "\n".join(row if isinstance(row, str) else public_text(row) for row in rows)
    # URLs and private SOURCE markers are locators, not instrument claims.
    text = re.sub(r"https?://[^\s)<>]+|\[\[SOURCE:[^\]]+\]\]", "", text)
    return html.unescape(text)


def is_cfd_topic(article):
    return bool(re.search(r"\bCFDs?\b|\bcontracts? for difference\b", str(article.get("title") or ""), re.I))


def _has_instrument(text, market):
    symbols = INSTRUMENTS[market][1]
    # BTC by itself can mean spot Bitcoin; require the futures name for that
    # ambiguous ticker. MBT and the named ETFs already identify the instrument.
    return any(re.search(r"\bBTC\s+(?i:futures)\b" if symbol == "BTC" else
                         r"\b" + symbol + r"\b", text) for symbol in symbols)


def validate_article(article):
    """Only new, request-bound articles adopt the rule; sealed history stays exact."""
    if article.get("public_instrument_policy") != POLICY or is_cfd_topic(article):
        return
    text = public_text({key: article[key] for key in
        ("title", "subtitle", "dek", "substack_body_markdown", "body_markdown") if key in article})
    validate_payload(article, article)
    covered = {m for m, pattern in MARKET_PATTERNS.items() if re.search(pattern, text, re.I)}
    if article.get("market_asset") in INSTRUMENTS:
        covered.add(article["market_asset"])
    for market, (_, symbols) in INSTRUMENTS.items():
        if any(re.search(r"\b" + s + r"\b", text) for s in symbols):
            covered.add(market)
    for market in sorted(covered):
        if not _has_instrument(text, market):
            raise ValueError("PUBLIC_FUTURES_OR_ETF_REQUIRED:" + market)


def validate_payload(article, payload):
    if article.get("public_instrument_policy") != POLICY or is_cfd_topic(article):
        return
    match = _FORBIDDEN.search(public_text(payload))
    if match:
        raise ValueError("PUBLIC_INSTRUMENT_NAME_FORBIDDEN:" + match.group().upper())
