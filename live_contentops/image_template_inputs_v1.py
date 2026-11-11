"""CC-465: the single ledger -> image_input_v1 map. No editorial numbers are made here."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

MARKETS = {"XAUUSD": "Gold", "US500": "S&P 500", "EURUSD": "EUR/USD",
           "USDJPY": "USD/JPY", "USOIL": "WTI crude oil", "BTCUSD": "Bitcoin"}
ORDER = tuple(MARKETS)
HORIZONS = {"SHORT": "Short-term", "MID": "Mid-term", "LONG": "Long-term"}
STATES = {"ARMED": "Waiting for entry", "PENDING": "Waiting for entry", "REGISTERED": "Waiting for entry",
          "TRIGGERED": "In position", "FILLED": "In position", "CLOSED": "Closed",
          "EXPIRED": "Expired, no entry", "NOT_TRIGGERED": "Expired, no entry"}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":")).encode()).hexdigest()


def et(value):
    if not value:
        return ""
    at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("IMAGE_TIMEZONE_REQUIRED")
    at = at.astimezone(ZoneInfo("America/New_York"))
    return f"{at.day} {at:%b}, {at.hour % 12 or 12}:{at:%M %p} ET"


def from_plan(row):
    """Map an existing public plan row; preserve absent alternatives and targets."""
    levels = row.get("levels") or {}
    raw = row.get("source_plan") or {}
    scenario = raw.get("scenario_analysis") or row.get("scenario_analysis") or {}
    main = (scenario.get("base_case") or {}).get("probability_pct", levels.get("chance_pct"))
    alternative = (scenario.get("alternative") or scenario.get("alternative_case") or {}).get("probability_pct")
    targets = levels.get("target") or []
    horizon = row.get("horizon") or raw.get("horizon") or levels.get("horizon")
    if horizon in HORIZONS:
        horizon = HORIZONS[horizon]
    plan = {"market": row["symbol"], "market_name": MARKETS[row["symbol"]],
            "direction": {"bullish": "LONG", "bearish": "SHORT"}.get(levels.get("direction"), levels.get("direction")),
            "horizon_label": horizon, "status_label": STATES.get(row.get("state")),
            "entry_low": levels.get("zone_low"), "entry_high": levels.get("zone_high"),
            "invalidation": levels.get("invalidation_level"),
            "target": targets[0] if isinstance(targets, list) and targets else targets or None,
            "main_probability_pct": main, "alt_probability_pct": alternative,
            "time_exit_et": et(row.get("time_exit_utc") or levels.get("time_exit_utc") or levels.get("valid_until_utc")),
            "entry_window_ends_et": et(row.get("entry_deadline_utc"))}
    return bind({"schema": "image_input_v1", "post_id": row["key"], "template": "call",
                 "market": row["symbol"], "plan": plan}, row)


def bind(image_input, source_record):
    """Bind the projection and original record, outside reader-facing pixels."""
    value = deepcopy(image_input)
    value.pop("source_binding", None)
    return {**value, "source_binding": {"input_sha256": digest(value),
            "source_sha256": digest(source_record), "record": deepcopy(source_record)}}


def validate_binding(value):
    binding = value.get("source_binding") or {}
    projection = {k: v for k, v in value.items() if k != "source_binding"}
    if (binding.get("input_sha256") != digest(projection)
            or binding.get("source_sha256") != digest(binding.get("record"))):
        raise ValueError("IMAGE_SOURCE_BINDING_CHANGED")

