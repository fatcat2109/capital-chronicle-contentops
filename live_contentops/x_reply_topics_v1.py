"""CC-511: named market drivers for the existing reply selector.

These links explain relevance, never a price move, a probability or a fact.
The fact owner still checks the observation and the writer must state the link.
"""
from __future__ import annotations

import re

SUBJECTS = {
    "nvidia": r"\b(?:nvidia|nvda)\b", "apple": r"\b(?:apple|aapl)\b",
    "microsoft": r"\b(?:microsoft|msft)\b", "amazon": r"\b(?:amazon|amzn)\b",
    "alphabet": r"\b(?:alphabet|googl?)\b", "meta": r"\bmeta\b",
    "tesla": r"\b(?:tesla|tsla)\b", "broadcom": r"\b(?:broadcom|avgo)\b",
    "mag7": r"\b(?:mag[ -]?7|magnificent seven)\b",
    "chips": r"\b(?:chips?|chipstocks|chipmakers?|semiconductors?)\b",
    "us_sector": r"\b(?:banks?|financials?|energy|retail|industrials?|tech(?:nology)?)\b",
    "dax": r"\bdax\b", "iran": r"\biran\b", "israel": r"\bisrael\b",
    "middle_east": r"\b(?:middle east|gulf|hormuz)\b", "saudi": r"\bsaudi\b",
    "red_sea": r"\b(?:houthis?|red sea)\b", "russia": r"\brussi[an]+\b",
    "ukraine": r"\bukrain\w*\b", "black_sea": r"\bblack sea\b",
    "fed": r"\b(?:fed|fomc|federal reserve|powell|waller|williams|bostic|daly|goolsbee|warsh)\b",
    "ecb": r"\b(?:ecb|european central bank|lagarde)\b",
    "boj": r"\b(?:boj|bank of japan|ueda)\b",
    "treasury": r"\btreasur\w*\b", "jgb": r"\bjgb\b", "bund": r"\bbund\b",
    "government_bonds": r"\bgovernment bonds?\b", "opec": r"\bopec\b",
    "inventory": r"\b(?:eia|api|crude|petroleum|cushing)\b",
    "bitcoin": r"\b(?:bitcoin|btc|ibit|fbtc|gbtc)\b",
    "crypto": r"\b(?:crypto|digital assets?|coinbase)\b",
}
SUBJECT_GROUPS = {
    "US_INDEX_WEIGHTS_AND_SECTORS": {"nvidia", "apple", "microsoft", "amazon", "alphabet", "meta",
                                     "tesla", "broadcom", "mag7", "chips", "us_sector"},
    "DAX_RISK_APPETITE": {"dax"},
    "MIDDLE_EAST_SUPPLY_AND_SAFETY": {"iran", "israel", "middle_east", "saudi", "red_sea"},
    "RUSSIAN_ENERGY_SUPPLY": {"russia", "ukraine", "black_sea"},
    "FED_POLICY": {"fed"}, "ECB_POLICY": {"ecb"}, "BOJ_POLICY": {"boj"},
    "SOVEREIGN_RATES": {"treasury", "jgb", "bund", "government_bonds"},
    "OIL_SUPPLY_AND_INVENTORIES": {"opec", "inventory"},
    "BITCOIN_FLOWS_AND_REGULATION": {"bitcoin", "crypto"},
}


def _has(pattern, text):
    return bool(re.search(pattern, text, re.I))


def driver_links(text):
    """Return bounded, named relationships; a country/company name is not enough."""
    links = []

    def add(key, markets, relationship):
        links.append({"driver": key, "markets": markets, "relationship": relationship,
                      "subjects": [name for name, pattern in SUBJECTS.items()
                                   if name in SUBJECT_GROUPS[key] and _has(pattern, text)]})

    equity_event = _has(
        r"\b(?:shares?|stocks?|chipstocks|semiconductors?|chipmakers?|earnings|revenues?|"
        r"profits?|guidance|sales|premarket|after[ -]?hours|slides?|falls?|fell|drops?|"
        r"rall(?:y|ies)|rises?|rose|gains?|sell[ -]?off|drawdown|exports?|"
        r"board|ceo|chief executive|merger|acquisition|buyback|dividend)\b", text)
    weights = _has(
        r"\b(?:nvidia|nvda|apple|aapl|microsoft|msft|amazon|amzn|alphabet|googl?|"
        r"meta|tesla|tsla|broadcom|avgo|magnificent seven|mag[ -]?7)\b", text)
    chips = _has(r"\b(?:chipstocks|semiconductors?|chipmakers?)\b", text)
    us_sector = (_has(r"(?:\bU\.?S\.?\b|\bAmerican\b|\bWall Street\b)", text)
                 and _has(r"\b(?:tech(?:nology)?|banks?|financials?|energy|retail|industrials?)\b", text))
    if equity_event and (weights or chips or us_sector):
        index_markets = ["NDX", "SPX"] if weights or chips or _has(r"\btech(?:nology)?\b", text) else ["SPX"]
        add("US_INDEX_WEIGHTS_AND_SECTORS", index_markets,
            "Large US index weights and their sectors feed the named US equity indices.")

    if (_has(r"\bdax\b", text)
            and _has(r"\b(?:record|highs?|lows?|rises?|rose|falls?|fell|gains?|drops?|up|down|rall(?:y|ies))\b", text)):
        add("DAX_RISK_APPETITE", ["EURUSD", "SPX"],
            "Germany's DAX is a euro-area equity and cross-market risk-appetite driver for the euro and S&P 500.")

    if (_has(r"\b(?:iran|israel|middle east|gulf|saudi|houthis?|hormuz|red sea)\b", text)
            and _has(r"\b(?:strikes?|war|attacks?|missiles?|military|escalat\w*|blockad\w*|"
                     r"shipping|tankers?|exports?|pipelines?|refiner\w*|production|supply|"
                     r"sanctions?|ceasefire|truce|conflict|tensions?)\b", text)):
        add("MIDDLE_EAST_SUPPLY_AND_SAFETY", ["WTI", "BRENT", "XAUUSD"],
            "Middle East conflict changes oil supply risk and demand for gold as a haven.")
    if (_has(r"\b(?:russia|russian|ukraine|black sea)\b", text)
            and _has(r"\b(?:supply|exports?|tankers?|pipelines?|refiner\w*|oil|gas|"
                     r"energy|embargo|sanctions?)\b", text)):
        add("RUSSIAN_ENERGY_SUPPLY", ["WTI", "BRENT", "XAUUSD"],
            "Russian energy supply disruption changes oil supply risk and gold's haven demand.")

    if (_has(r"\b(?:fed|fomc|federal reserve)\b", text)
            or (_has(r"\b(?:powell|waller|williams|bostic|daly|goolsbee|warsh)\b", text)
                and _has(r"\b(?:rates?|inflation|monetary|policy|yields?|speaks?|speech|testif\w*)\b", text))):
        add("FED_POLICY", ["DXY", "EURUSD", "USDJPY", "XAUUSD"],
            "Fed policy and speakers change dollar rate expectations and the relative-rate outlook for euro, yen and gold.")
    if _has(r"\b(?:ecb|european central bank)\b", text) or (
            _has(r"\blagarde\b", text) and _has(r"\b(?:rates?|inflation|policy|speaks?|speech)\b", text)):
        add("ECB_POLICY", ["EURUSD", "DXY", "XAUUSD"],
            "ECB policy and speakers change euro-dollar rate differences and gold's opportunity cost.")
    if _has(r"\b(?:boj|bank of japan)\b", text) or (
            _has(r"\bueda\b", text) and _has(r"\b(?:rates?|inflation|policy|speaks?|speech)\b", text)):
        add("BOJ_POLICY", ["USDJPY", "DXY", "XAUUSD"],
            "BoJ policy and speakers change yen-dollar rate differences and gold's opportunity cost.")
    if (_has(r"\b(?:treasur\w*|jgb|bund|government bonds?)\b", text)
            and _has(r"\b(?:auctions?|yields?|bids?|bid.to.cover|tails?|stop.through)\b", text)):
        add("SOVEREIGN_RATES", ["DXY", "EURUSD", "USDJPY", "XAUUSD"],
            "Government-bond auctions and yields change relative rates for dollar, euro, yen and gold.")

    if ((_has(r"\bopec\b", text) and _has(r"\b(?:production|output|cuts?|hikes?|meeting|quotas?|supply|demand|oil|barrels?|bpd)\b", text))
            or (_has(r"\b(?:eia|api|crude|petroleum|cushing)\b", text)
                and _has(r"\b(?:inventor\w*|stocks?|stockpiles?|draws?|builds?)\b", text))):
        add("OIL_SUPPLY_AND_INVENTORIES", ["WTI", "BRENT"],
            "OPEC supply decisions and petroleum inventories change the supply balance for WTI and Brent oil.")
    if (_has(r"\b(?:bitcoin|btc|crypto|digital assets?|ibit|fbtc|gbtc|coinbase)\b", text)
            and _has(r"\b(?:etfs?|funds?|flows?|inflows?|outflows?|regulat\w*|sec|"
                     r"cftc|bans?|licen[sc]\w*|approv\w*)\b", text)):
        add("BITCOIN_FLOWS_AND_REGULATION", ["BTCUSD"],
            "Bitcoin fund flows and digital-asset regulation change demand and access for Bitcoin.")
    return links


def names_link_subject(link, sentence):
    """A relation sentence can name the original driver without repeating its event."""
    return any(_has(SUBJECTS[name], sentence) for name in link["subjects"])
