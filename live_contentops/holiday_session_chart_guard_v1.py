"""Dec-2026 / Jan-2027 US Holiday & Early-Close Chart Price-Scale and Wrap-Cadence Guard.

Standalone, pure-stdlib, fail-closed guard reading the canonical NYSE session calendar
(``us_session_calendar_v1.json``) to:
1. Resolve exact ET cash open / early-close / holiday / weekend / CME full-day holiday
   session status across all 7 core markets (XAUUSD, US500, USTEC, EURUSD, USDJPY,
   USOIL, BTCUSD).
2. Distinguish lawful closed-market cash-index closing settlement prints
   (PUBLIC_ON_DEMAND_QUOTE INDEX ``^GSPC`` / ``^NDX`` within ``[-120s, +5400s]`` of the
   16:00 ET regular close or 13:00 ET early close, bounded by ``observed <= known <= capture``)
   from post-close / holiday moving CFD drift (Exness ``US500``/``USTEC`` ticks moving
   ``> 0.15%`` while cash charts sit frozen) and genuine live mid-session or closed-session
   scale mismatches (which remain strictly refused with ``TRADINGVIEW_PRICE_SCALE_MISMATCH``).
3. Resolve CC-689 daily / Sunday weekly wrap cadence, cross-year session rollovers
   (24 Dec early close -> 25 Dec closed -> 27 Dec weekly -> 31 Dec regular -> 1 Jan closed
   -> 3 Jan weekly -> 18 Jan MLK Day -> 15 Feb Presidents' Day), morning-map settlement
   windows, and CC-778 follow-up move-chart resolution eligibility.
4. Fail closed on naive timestamps, ``bool`` numbers, ``NaN``/``Inf``, non-positive prices,
   unknown markets, proxy instruments, and missing/malformed calendars (unless explicit
   audited NYSE fallback is requested).

Read-only: zero network calls, zero environment lookups, zero filesystem writes.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

POLICY = "CC_HOLIDAY_SESSION_CHART_GUARD_V1"
IMAGE_CONTRACT_POLICY = "CC463_TRADINGVIEW_FIRST_V1"
CALENDAR_SCHEMA = "IbkrUsSessionCalendarV1"

ET = ZoneInfo("America/New_York")
UTC = timezone.utc

DEFAULT_CALENDAR_PATH = Path(
    r"A:\Capital Chronicle\main-jim-research-dashboard-20261025\config\ibkr_paper\us_session_calendar_v1.json"
)

US_CASH_OPEN_ET = time(9, 30)
US_CASH_REGULAR_CLOSE_ET = time(16, 0)
US_CASH_EARLY_CLOSE_ET = time(13, 0)
CME_WEEKEND_CLOSE_ET = time(17, 0)
CME_WEEKEND_REOPEN_ET = time(18, 0)
CME_EARLY_EVE_CLOSE_ET = time(13, 45)

QUOTE_MAX_AGE_SECONDS = 120
LIVE_MAX_NEGATIVE_SKEW_SECONDS = 2
CASH_INDEX_CLOSE_SETTLE_SECONDS = 5400

WRAP_START_ET = date(2026, 11, 23)
WRAP_DAILY_START_ET = time(8, 0)
WRAP_DAILY_DEADLINE_ET = time(8, 45)
WRAP_WEEKLY_START_UTC = time(15, 0)
WRAP_FIRST_SUNDAY_START_UTC = time(12, 0)
WRAP_WEEKLY_DEADLINE_UTC = time(18, 0)

CORE_MARKETS: Mapping[str, Mapping[str, Any]] = {
    "XAUUSD": {
        "tv_symbol": "FX_IDC:XAUUSD",
        "session_class": "CME_COMMODITY",
        "max_difference_pct": 0.15,
        "public_quote_symbol": "XAU=",
        "public_instrument_type": "INDEX",
    },
    "US500": {
        "tv_symbol": "SP:SPX",
        "session_class": "US_CASH_INDEX",
        "max_difference_pct": 0.15,
        "public_quote_symbol": "^GSPC",
        "public_instrument_type": "INDEX",
    },
    "USTEC": {
        "tv_symbol": "NASDAQ:NDX",
        "session_class": "US_CASH_INDEX",
        "max_difference_pct": 0.15,
        "public_quote_symbol": "^NDX",
        "public_instrument_type": "INDEX",
    },
    "EURUSD": {
        "tv_symbol": "FX_IDC:EURUSD",
        "session_class": "FX_SPOT",
        "max_difference_pct": 0.15,
        "public_quote_symbol": "EURUSD=X",
        "public_instrument_type": "CURRENCY",
    },
    "USDJPY": {
        "tv_symbol": "FX_IDC:USDJPY",
        "session_class": "FX_SPOT",
        "max_difference_pct": 0.15,
        "public_quote_symbol": "USDJPY=X",
        "public_instrument_type": "CURRENCY",
    },
    "USOIL": {
        "tv_symbol": "NYMEX:CL1!",
        "session_class": "CME_COMMODITY",
        "max_difference_pct": 0.40,
        "public_quote_symbol": "CL=F",
        "public_instrument_type": "FUTURE",
    },
    "BTCUSD": {
        "tv_symbol": "COINBASE:BTCUSD",
        "session_class": "CRYPTO_24X7",
        "max_difference_pct": 0.40,
        "public_quote_symbol": "BTC-USD",
        "public_instrument_type": "CRYPTOCURRENCY",
    },
}

CORE_MARKET_ORDER = ("XAUUSD", "US500", "USTEC", "EURUSD", "USDJPY", "USOIL", "BTCUSD")
CASH_INDEX_MARKETS = frozenset({"US500", "USTEC"})
CME_COMMODITY_MARKETS = frozenset({"XAUUSD", "USOIL"})
FX_SPOT_MARKETS = frozenset({"EURUSD", "USDJPY"})
CRYPTO_MARKETS = frozenset({"BTCUSD"})

CFD_SOURCE_KINDS = frozenset({
    "PLAN_STATUS_EXPORT",
    "BAR_STORE_M1_CLOSE",
    "MAIN_SAVED_TICK",
    "HELD_M15_RESOLUTION_CLOSE",
})
ALLOWED_SOURCE_KINDS = frozenset(CFD_SOURCE_KINDS | {"PUBLIC_ON_DEMAND_QUOTE"})
CFD_PRICE_BASES = frozenset({"plan_feed", "plan_bar_close"})
QUOTE_ABSENT_CAUSES = (
    "TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE",
    "TRADINGVIEW_LAST_CLOSE_MAIN_QUOTE_UNAVAILABLE",
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YEAR_KEY_RE = re.compile(r"^\d{4}$")
_PAGE_TITLE_PRICE_RE = re.compile(r"^\S+\s+([\d,]+(?:\.\d+)?)(?:\s|$)")
_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_NORMALIZED_CALENDAR_TOKEN = object()
_MAX_CALENDAR_BYTES = 2 * 1024 * 1024
_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_WIN_RESERVED_DOS_STEMS = frozenset(
    {"con", "prn", "aux", "nul", "conin$", "conout$", "clock$"}
    | {f"com{i}" for i in range(10)}
    | {f"lpt{i}" for i in range(10)}
    | {"com\u00b9", "com\u00b2", "com\u00b3", "lpt\u00b9", "lpt\u00b2", "lpt\u00b3"}
)
_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# Byte-keyed read-only cache so same-size edits invalidate immediately.
_CALENDAR_FILE_CACHE: tuple[str, bytes, dict[str, Any]] | None = None


class HolidayChartGuardError(ValueError):
    """Fail-closed guard refusal with machine-readable cause and structured details."""

    def __init__(self, cause: str, /, **details: Any) -> None:
        super().__init__(cause)
        self.cause = cause
        self.details = details


def _require_clean_utf8_text(value: Any, *, error_code: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HolidayChartGuardError(error_code, missing=field)
    if _CONTROL_CHAR_RE.search(value):
        raise HolidayChartGuardError(error_code, field=field, reason="control_chars_forbidden")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise HolidayChartGuardError(error_code, field=field, reason="invalid_utf8_surrogate") from None
    return value


def _require_sha256_hex(value: Any, *, error_code: str, field: str) -> str:
    text = _require_clean_utf8_text(value, error_code=error_code, field=field).strip()
    if not _SHA256_HEX_RE.fullmatch(text):
        raise HolidayChartGuardError(error_code, field=field, reason="invalid_sha256_hex")
    return text.lower()


def _has_unsafe_windows_path_prefix(slashed: str) -> bool:
    upper = slashed.lstrip().upper()
    return (
        upper == "\\??"
        or upper.startswith(("\\??\\", "\\\\?\\", "\\\\.\\", "\\\\", "\\GLOBAL??\\", "\\DOSDEVICES\\", "\\DEVICE\\"))
        or upper.startswith(("GLOBALROOT\\", "VOLUME{", "HARDDISKVOLUME"))
        or "\\DEVICE\\HARDDISKVOLUME" in upper
        or "GLOBALROOT" in upper
    )


def _require_safe_source_path(value: Any) -> str:
    text = _require_clean_utf8_text(value, error_code="TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED", field="source_path")
    if text != text.strip():
        raise HolidayChartGuardError(
            "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
            field="source_path",
            reason="leading_or_trailing_whitespace",
        )
    slashed = text.replace("/", "\\")
    if _has_unsafe_windows_path_prefix(slashed):
        raise HolidayChartGuardError(
            "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
            field="source_path",
            reason="unsafe_windows_path_prefix",
        )
    if _DRIVE_PREFIX_RE.match(slashed):
        if len(slashed) < 3 or slashed[2] != "\\":
            raise HolidayChartGuardError(
                "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                field="source_path",
                reason="drive_relative_path_forbidden",
            )
        body = slashed[2:]
    else:
        body = slashed
    if ":" in body:
        raise HolidayChartGuardError(
            "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
            field="source_path",
            reason="ntfs_ads_forbidden",
        )
    for seg in (s for s in body.split("\\") if s):
        if seg == "..":
            raise HolidayChartGuardError(
                "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                field="source_path",
                reason="traversal_forbidden",
            )
        if seg == ".":
            continue
        if seg.endswith(".") or seg.endswith(" "):
            raise HolidayChartGuardError(
                "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                field="source_path",
                reason="trailing_dot_or_space",
            )
        stem = seg.rstrip(". ").split(".", 1)[0].rstrip(" ").lower()
        if stem in _WIN_RESERVED_DOS_STEMS:
            raise HolidayChartGuardError(
                "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                field="source_path",
                reason="reserved_dos_device",
            )
    return text


def _to_et(dt_utc: datetime, *, field_name: str = "at_utc") -> datetime:
    try:
        return dt_utc.astimezone(ET)
    except OverflowError:
        raise HolidayChartGuardError("UTC_CLOCK_OUT_OF_RANGE", field=field_name, value=dt_utc.isoformat()) from None


def _combine_et_to_utc(day_obj: date, clock_et: time, *, field_name: str = "day_et") -> datetime:
    try:
        return datetime.combine(day_obj, clock_et, ET).astimezone(UTC)
    except OverflowError:
        raise HolidayChartGuardError("UTC_CLOCK_OUT_OF_RANGE", field=field_name, value=day_obj.isoformat()) from None


def _shift_date(day_obj: date, days: int, *, field_name: str = "day_et") -> date:
    try:
        return day_obj + timedelta(days=days)
    except OverflowError:
        raise HolidayChartGuardError("UTC_CLOCK_OUT_OF_RANGE", field=field_name, value=day_obj.isoformat()) from None


def require_aware_utc(value: Any, *, field_name: str = "timestamp") -> datetime:
    """Parse and return a timezone-aware UTC datetime; reject naive or non-timestamp inputs."""
    if isinstance(value, bool) or value is None:
        raise HolidayChartGuardError("NAIVE_TIMESTAMP_FORBIDDEN", field=field_name, received_type=type(value).__name__)
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise HolidayChartGuardError("NAIVE_TIMESTAMP_FORBIDDEN", field=field_name)
        if _ISO_DATE_RE.fullmatch(text):
            raise HolidayChartGuardError("NAIVE_TIMESTAMP_FORBIDDEN", field=field_name, value=text)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00").replace("z", "+00:00"))
        except ValueError:
            raise HolidayChartGuardError("INVALID_TIMESTAMP_FORMAT", field=field_name, value=text) from None
    else:
        raise HolidayChartGuardError("NAIVE_TIMESTAMP_FORBIDDEN", field=field_name, received_type=type(value).__name__)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise HolidayChartGuardError("NAIVE_TIMESTAMP_FORBIDDEN", field=field_name)
    try:
        return parsed.astimezone(UTC)
    except OverflowError:
        raise HolidayChartGuardError("UTC_CLOCK_OUT_OF_RANGE", field=field_name) from None


def require_date(value: Any, *, field_name: str = "day_et") -> date:
    """Validate a strict calendar date (not bool, not datetime)."""
    if isinstance(value, bool) or isinstance(value, datetime):
        raise HolidayChartGuardError("INVALID_CALENDAR_DATE", field=field_name, received_type=type(value).__name__)
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not _ISO_DATE_RE.fullmatch(text):
            raise HolidayChartGuardError("INVALID_CALENDAR_DATE", field=field_name, value=text)
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise HolidayChartGuardError("INVALID_CALENDAR_DATE", field=field_name, value=text) from None
    raise HolidayChartGuardError("INVALID_CALENDAR_DATE", field=field_name, received_type=type(value).__name__)


def require_positive_finite_number(value: Any, *, field_name: str = "price") -> float:
    """Parse a finite positive float; fail closed on bool, NaN, Inf, <= 0, or non-numeric inputs."""
    if isinstance(value, bool):
        raise HolidayChartGuardError("BOOL_NUMBER_FORBIDDEN", field=field_name)
    if value is None or isinstance(value, (dict, list, tuple, set, bytes, bytearray)):
        raise HolidayChartGuardError("INVALID_NUMERIC_VALUE", field=field_name, received_type=type(value).__name__)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() in {"true", "false"}:
            raise HolidayChartGuardError("INVALID_NUMERIC_VALUE", field=field_name, value=value)
        value = stripped
    try:
        numeric = float(value)
    except (ValueError, TypeError, OverflowError):
        raise HolidayChartGuardError("INVALID_NUMERIC_VALUE", field=field_name) from None
    if not math.isfinite(numeric):
        raise HolidayChartGuardError("NON_FINITE_NUMBER_FORBIDDEN", field=field_name)
    if numeric <= 0.0:
        raise HolidayChartGuardError("NON_POSITIVE_NUMBER_FORBIDDEN", field=field_name, value=numeric)
    return numeric


def require_non_negative_finite_number(value: Any, *, field_name: str = "tolerance") -> float:
    """Parse a finite non-negative float; fail closed on bool, NaN, Inf, or < 0."""
    if isinstance(value, bool):
        raise HolidayChartGuardError("BOOL_NUMBER_FORBIDDEN", field=field_name)
    if value is None or isinstance(value, (dict, list, tuple, set, bytes, bytearray)):
        raise HolidayChartGuardError("INVALID_NUMERIC_VALUE", field=field_name, received_type=type(value).__name__)
    try:
        numeric = float(value)
    except (ValueError, TypeError, OverflowError):
        raise HolidayChartGuardError("INVALID_NUMERIC_VALUE", field=field_name) from None
    if not math.isfinite(numeric):
        raise HolidayChartGuardError("NON_FINITE_NUMBER_FORBIDDEN", field=field_name)
    if numeric < 0.0:
        raise HolidayChartGuardError("NEGATIVE_NUMBER_FORBIDDEN", field=field_name, value=numeric)
    return 0.0 if numeric == 0.0 else numeric


def require_core_market(market: Any) -> str:
    """Validate that market is one of the 7 canonical core markets."""
    if not isinstance(market, str) or market not in CORE_MARKETS:
        raise HolidayChartGuardError("UNSUPPORTED_MARKET", market=market)
    return market


def parse_chart_last_price(page_title: Any) -> float:
    """Extract the displayed last price from a TradingView guest chart title."""
    if not isinstance(page_title, str):
        raise HolidayChartGuardError("TRADINGVIEW_LAST_PRICE_NOT_VISIBLE")
    match = _PAGE_TITLE_PRICE_RE.match(page_title)
    if not match:
        raise HolidayChartGuardError("TRADINGVIEW_LAST_PRICE_NOT_VISIBLE")
    return require_positive_finite_number(match.group(1).replace(",", ""), field_name="chart_price")


def _observed_us_holiday(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _easter_sunday(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    return date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def deterministic_nyse_year_dates(year: int) -> tuple[frozenset[str], frozenset[str]]:
    """Deterministic NYSE full-closed and 13:00 ET early-close dates (matches 2026-2028 JSON)."""
    if isinstance(year, bool) or not isinstance(year, int) or not 1990 <= year <= 2100:
        raise HolidayChartGuardError("INVALID_CALENDAR_YEAR", year=year)
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    memorial_end = date(year, 5, 31)
    closed: set[date] = {
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter_sunday(year) - timedelta(days=2),
        memorial_end - timedelta(days=memorial_end.weekday()),
        _observed_us_holiday(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),
        thanksgiving,
        _observed_us_holiday(date(year, 12, 25)),
    }
    jan1 = date(year, 1, 1)
    if jan1.weekday() < 5:
        closed.add(jan1)
    elif jan1.weekday() == 6:
        closed.add(date(year, 1, 2))
    # NYSE does not observe a Saturday New Year's Day on the preceding Friday Dec 31.
    if year >= 2022:
        closed.add(_observed_us_holiday(date(year, 6, 19)))
    early: set[date] = {thanksgiving + timedelta(days=1)}
    for eve in (date(year, 7, 3), date(year, 12, 24)):
        if eve.weekday() < 5 and eve not in closed:
            early.add(eve)
    return (
        frozenset(d.isoformat() for d in closed),
        frozenset(d.isoformat() for d in early),
    )


def _validate_iso_date_list(items: Any, *, expected_year: int, field_name: str) -> frozenset[str]:
    if not isinstance(items, list):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", field=field_name)
    parsed: set[str] = set()
    for item in items:
        if not isinstance(item, str) or not _ISO_DATE_RE.fullmatch(item):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", field=field_name, value=item)
        try:
            day = date.fromisoformat(item)
        except ValueError:
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", field=field_name, value=item) from None
        if day.year != expected_year:
            raise HolidayChartGuardError(
                "HOLIDAY_CALENDAR_YEAR_MISMATCH",
                field=field_name,
                expected_year=expected_year,
                value=item,
            )
        parsed.add(item)
    return frozenset(parsed)


def _normalize_calendar_payload(
    data: Any,
    *,
    source: str,
    path: str | None,
    digest: str | None,
    allow_fallback: bool,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="root_not_object")
    if "schema" in data and data["schema"] != CALENDAR_SCHEMA:
        raise HolidayChartGuardError(
            "HOLIDAY_CALENDAR_SCHEMA_INVALID",
            expected_schema=CALENDAR_SCHEMA,
            actual_schema=data.get("schema"),
        )
    years_raw = data.get("years")
    if not isinstance(years_raw, dict) or not years_raw:
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="years_missing_or_empty")
    years: dict[int, dict[str, frozenset[str]]] = {}
    for year_key, entry in years_raw.items():
        if not isinstance(year_key, str) or not _YEAR_KEY_RE.fullmatch(year_key):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="invalid_year_key", year=year_key)
        if not isinstance(entry, dict):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="year_entry_not_object", year=year_key)
        year_int = int(year_key)
        closed = _validate_iso_date_list(entry.get("closed"), expected_year=year_int, field_name=f"years.{year_key}.closed")
        early = _validate_iso_date_list(
            entry.get("early_close_13_et"),
            expected_year=year_int,
            field_name=f"years.{year_key}.early_close_13_et",
        )
        # Fail closed: if a date appears in both lists, closed wins.
        years[year_int] = {"closed": closed, "early_close_13_et": early - closed}
    return {
        "schema": data.get("schema", CALENDAR_SCHEMA),
        "source": source,
        "path": path,
        "sha256": digest,
        "years": years,
        "allow_fallback": bool(allow_fallback),
    }


def _validate_calendar_path(raw_path: str | Path) -> Path:
    """Unconditionally refuse NT/device/UNC prefixes, ADS, trailing dot/space, DOS stems, and symlinks/junctions."""
    if not isinstance(raw_path, (str, Path)):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="invalid_path_type")
    raw = str(raw_path)
    if not raw or not raw.strip() or _CONTROL_CHAR_RE.search(raw):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="empty_or_control_chars")
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="invalid_utf8_surrogate") from None
    if raw != raw.strip():
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="leading_or_trailing_whitespace", path=raw)

    slashed = raw.replace("/", "\\")
    if _has_unsafe_windows_path_prefix(slashed):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="device_or_unc_prefix", path=raw)
    if len(slashed) > 3 and slashed.endswith("\\"):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="trailing_separator", path=raw)

    if _DRIVE_PREFIX_RE.match(slashed):
        if len(slashed) < 3 or slashed[2] != "\\":
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="drive_relative_path_forbidden", path=raw)
        body = slashed[2:]
    else:
        body = slashed
    if ":" in body:
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="ntfs_ads_forbidden", path=raw)
    for seg in (s for s in body.split("\\") if s):
        if seg == "..":
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="traversal_forbidden", path=raw)
        if seg == ".":
            continue
        if seg.endswith(".") or seg.endswith(" "):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="trailing_dot_or_space", path=raw)
        stem = seg.rstrip(". ").split(".", 1)[0].rstrip(" ").lower()
        if stem in _WIN_RESERVED_DOS_STEMS:
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="reserved_dos_device", path=raw)

    path = Path(raw)
    abs_path = Path(os.path.abspath(raw))
    seen: set[str] = set()
    for root_candidate in (path, abs_path):
        for candidate in (root_candidate, *root_candidate.parents):
            cand_key = str(candidate)
            if cand_key in seen:
                continue
            seen.add(cand_key)
            try:
                is_sym = candidate.is_symlink()
                is_junc = hasattr(os.path, "isjunction") and os.path.isjunction(candidate)
            except OSError:
                raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="reparse_check_failed", path=raw) from None
            if is_sym or is_junc:
                raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="reparse_or_symlink", path=raw)
            try:
                st = candidate.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="lstat_failed", path=raw) from None
            if stat.S_ISLNK(st.st_mode) or (getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT):
                raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", reason="reparse_point_forbidden", path=raw)
    return path


def _reject_dup_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"DUPLICATE_JSON_KEY:{k}")
        out[k] = v
    return out


def _reject_non_finite(token: str) -> Any:
    raise ValueError(f"NON_FINITE_JSON_CONSTANT:{token}")


def _loads_strict_calendar_json(raw: bytes) -> Any:
    text = raw.decode("utf-8")
    return json.loads(text, object_pairs_hook=_reject_dup_keys, parse_constant=_reject_non_finite)


def _clone_calendar_bundle(bundle: Mapping[str, Any], *, allow_fallback: bool) -> dict[str, Any]:
    for req_key in ("schema", "source", "path", "sha256", "years"):
        if req_key not in bundle:
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="normalized_bundle_missing_key", missing=req_key)
    years_obj = bundle.get("years")
    if not isinstance(years_obj, Mapping):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="normalized_years_corrupt")
    years_copy: dict[int, dict[str, frozenset[str]]] = {}
    for yr, entry in years_obj.items():
        if isinstance(yr, bool) or not isinstance(yr, int) or not isinstance(entry, Mapping):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="normalized_year_entry_corrupt")
        closed = entry.get("closed")
        early = entry.get("early_close_13_et")
        if (
            not isinstance(closed, (frozenset, set, list, tuple))
            or not isinstance(early, (frozenset, set, list, tuple))
            or not all(isinstance(d, str) for d in closed)
            or not all(isinstance(d, str) for d in early)
        ):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="normalized_year_dates_corrupt")
        years_copy[yr] = {
            "closed": frozenset(closed),
            "early_close_13_et": frozenset(early),
        }
    return {
        "schema": bundle["schema"],
        "source": bundle["source"],
        "path": bundle["path"],
        "sha256": bundle["sha256"],
        "years": years_copy,
        "allow_fallback": bool(allow_fallback),
        "_normalized_holiday_calendar": _NORMALIZED_CALENDAR_TOKEN,
    }


def _fallback_calendar_bundle(*, path: str | None) -> dict[str, Any]:
    return {
        "schema": CALENDAR_SCHEMA,
        "source": "FALLBACK_NYSE_RULES",
        "path": path,
        "sha256": None,
        "years": {},
        "allow_fallback": True,
        "_normalized_holiday_calendar": _NORMALIZED_CALENDAR_TOKEN,
    }


def load_us_session_calendar(
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
) -> dict[str, Any]:
    """Load and validate ``us_session_calendar_v1.json`` read-only; fail closed by default."""
    global _CALENDAR_FILE_CACHE
    if calendar is not None:
        if isinstance(calendar, Mapping) and "_normalized_holiday_calendar" in calendar:
            if calendar.get("_normalized_holiday_calendar") is _NORMALIZED_CALENDAR_TOKEN:
                return _clone_calendar_bundle(calendar, allow_fallback=bool(allow_fallback))
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="forged_normalized_marker")
        try:
            raw = json.dumps(calendar, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            raise HolidayChartGuardError("HOLIDAY_CALENDAR_SCHEMA_INVALID", reason="injected_not_json_serializable") from None
        try:
            normalized = _normalize_calendar_payload(
                calendar,
                source="INJECTED",
                path=None,
                digest=sha256(raw).hexdigest(),
                allow_fallback=allow_fallback,
            )
            return _clone_calendar_bundle(normalized, allow_fallback=bool(allow_fallback))
        except HolidayChartGuardError:
            if not allow_fallback:
                raise
            return _fallback_calendar_bundle(path=None)

    path = _validate_calendar_path(DEFAULT_CALENDAR_PATH if calendar_path is None else calendar_path)
    key = str(path)
    try:
        st = path.lstat()
    except FileNotFoundError as exc:
        if allow_fallback:
            return _fallback_calendar_bundle(path=key)
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_UNAVAILABLE", path=key, error=type(exc).__name__) from None
    except OSError as exc:
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", path=key, error=type(exc).__name__) from None
    if not stat.S_ISREG(st.st_mode):
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_PATH_UNSAFE", path=key, reason="non_regular_file")
    if st.st_size > _MAX_CALENDAR_BYTES:
        raise HolidayChartGuardError(
            "HOLIDAY_CALENDAR_PATH_UNSAFE",
            path=key,
            reason="file_too_large",
            size_bytes=st.st_size,
            max_bytes=_MAX_CALENDAR_BYTES,
        )

    try:
        raw = path.read_bytes()
    except OSError as exc:
        if allow_fallback:
            return _fallback_calendar_bundle(path=key)
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_UNAVAILABLE", path=key, error=type(exc).__name__) from None
    if len(raw) > _MAX_CALENDAR_BYTES:
        raise HolidayChartGuardError(
            "HOLIDAY_CALENDAR_PATH_UNSAFE",
            path=key,
            reason="file_too_large",
            size_bytes=len(raw),
            max_bytes=_MAX_CALENDAR_BYTES,
        )

    if _CALENDAR_FILE_CACHE is not None and _CALENDAR_FILE_CACHE[0] == key and _CALENDAR_FILE_CACHE[1] == raw:
        return _clone_calendar_bundle(_CALENDAR_FILE_CACHE[2], allow_fallback=bool(allow_fallback))

    try:
        parsed = _loads_strict_calendar_json(raw)
    except (ValueError, UnicodeDecodeError, RecursionError):
        if allow_fallback:
            return _fallback_calendar_bundle(path=key)
        raise HolidayChartGuardError("HOLIDAY_CALENDAR_CORRUPT_JSON", path=key) from None

    try:
        normalized = _normalize_calendar_payload(
            parsed,
            source="FILE",
            path=key,
            digest=sha256(raw).hexdigest(),
            allow_fallback=allow_fallback,
        )
    except HolidayChartGuardError:
        if allow_fallback:
            return _fallback_calendar_bundle(path=key)
        raise

    _CALENDAR_FILE_CACHE = (key, raw, _clone_calendar_bundle(normalized, allow_fallback=False))
    return _clone_calendar_bundle(normalized, allow_fallback=bool(allow_fallback))


def _year_dates(year: int, bundle: Mapping[str, Any]) -> tuple[frozenset[str], frozenset[str], str]:
    entry = bundle["years"].get(year)
    if entry is not None:
        return entry["closed"], entry["early_close_13_et"], bundle["source"]
    if bundle.get("allow_fallback"):
        closed, early = deterministic_nyse_year_dates(year)
        return closed, early, "FALLBACK_NYSE_RULES"
    raise HolidayChartGuardError("HOLIDAY_CALENDAR_YEAR_MISSING", year=year, path=bundle.get("path"))


def _named_us_holiday_label(day: date, *, is_closed: bool, is_early: bool) -> str | None:
    year = day.year
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    good_friday = _easter_sunday(year) - timedelta(days=2)
    memorial_end = date(year, 5, 31)
    memorial_day = memorial_end - timedelta(days=memorial_end.weekday())
    if is_closed:
        if day in {date(year, 1, 1), date(year, 1, 2)}:
            return "NEW_YEARS_DAY"
        if day == _nth_weekday(year, 1, 0, 3):
            return "MLK_DAY"
        if day == _nth_weekday(year, 2, 0, 3):
            return "PRESIDENTS_DAY"
        if day == good_friday:
            return "GOOD_FRIDAY"
        if day == memorial_day:
            return "MEMORIAL_DAY"
        if year >= 2022 and day == _observed_us_holiday(date(year, 6, 19)):
            return "JUNETEENTH"
        if day == _observed_us_holiday(date(year, 7, 4)):
            return "INDEPENDENCE_DAY"
        if day == _nth_weekday(year, 9, 0, 1):
            return "LABOR_DAY"
        if day == thanksgiving:
            return "THANKSGIVING"
        if day in {date(year, 12, 24), date(year, 12, 25), date(year, 12, 26)}:
            return "CHRISTMAS_DAY"
        return "CUSTOM_CALENDAR_HOLIDAY"
    if is_early:
        if day == thanksgiving + timedelta(days=1):
            return "BLACK_FRIDAY_EARLY_CLOSE"
        if day == date(year, 12, 24):
            return "CHRISTMAS_EVE_EARLY_CLOSE"
        if day == date(year, 7, 3):
            return "INDEPENDENCE_DAY_EVE_EARLY_CLOSE"
        return "CUSTOM_CALENDAR_EARLY_CLOSE"
    if day == date(year, 12, 31) and day.weekday() < 5:
        return "NEW_YEARS_EVE_REGULAR"
    return None


def _is_cme_full_day_holiday(day: date, *, is_closed: bool) -> bool:
    """CME Globex / NYMEX full-day closures (New Year's Day, Good Friday, Christmas Day)."""
    if day.weekday() >= 5 or not is_closed:
        return False
    good_friday = _easter_sunday(day.year) - timedelta(days=2)
    return (
        (day.month == 1 and day.day in {1, 2})
        or day == good_friday
        or (day.month == 12 and day.day in {24, 25, 26})
    )


def classify_us_cash_day(
    day: date | str,
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
) -> dict[str, Any]:
    """Classify one ET calendar date using the canonical NYSE session calendar."""
    day_obj = require_date(day, field_name="day_et")
    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    if day_obj.weekday() >= 5:
        return {
            "day_et": day_obj.isoformat(),
            "weekday": _WEEKDAY_NAMES[day_obj.weekday()],
            "session_state": "WEEKEND",
            "is_open_day": False,
            "is_early_close": False,
            "open_et": None,
            "close_et": None,
            "open_utc": None,
            "close_utc": None,
            "holiday_label": None,
            "is_cme_full_day_holiday": False,
            "calendar_source": bundle["source"],
            "calendar_sha256": bundle["sha256"],
        }
    closed, early, effective_source = _year_dates(day_obj.year, bundle)
    iso = day_obj.isoformat()
    if iso in closed:
        label = _named_us_holiday_label(day_obj, is_closed=True, is_early=False)
        return {
            "day_et": iso,
            "weekday": _WEEKDAY_NAMES[day_obj.weekday()],
            "session_state": "CLOSED_HOLIDAY",
            "is_open_day": False,
            "is_early_close": False,
            "open_et": None,
            "close_et": None,
            "open_utc": None,
            "close_utc": None,
            "holiday_label": label,
            "is_cme_full_day_holiday": _is_cme_full_day_holiday(day_obj, is_closed=True),
            "calendar_source": effective_source,
            "calendar_sha256": bundle["sha256"],
        }
    is_early = iso in early
    close_t = US_CASH_EARLY_CLOSE_ET if is_early else US_CASH_REGULAR_CLOSE_ET
    open_utc = _combine_et_to_utc(day_obj, US_CASH_OPEN_ET, field_name="day_et")
    close_utc = _combine_et_to_utc(day_obj, close_t, field_name="day_et")
    label = _named_us_holiday_label(day_obj, is_closed=False, is_early=is_early)
    return {
        "day_et": iso,
        "weekday": _WEEKDAY_NAMES[day_obj.weekday()],
        "session_state": "EARLY_CLOSE_13_ET" if is_early else "REGULAR_SESSION",
        "is_open_day": True,
        "is_early_close": is_early,
        "open_et": US_CASH_OPEN_ET.strftime("%H:%M"),
        "close_et": close_t.strftime("%H:%M"),
        "open_utc": open_utc.isoformat(),
        "close_utc": close_utc.isoformat(),
        "holiday_label": label,
        "is_cme_full_day_holiday": False,
        "calendar_source": effective_source,
        "calendar_sha256": bundle["sha256"],
    }


def _prior_us_cash_session_info(start_day: date, bundle: Mapping[str, Any]) -> tuple[date, dict[str, Any]]:
    day = start_day
    for _ in range(31):
        info = classify_us_cash_day(day, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        if info["is_open_day"]:
            return day, info
        day = _shift_date(day, -1, field_name="day_et")
    raise HolidayChartGuardError("PRIOR_US_CASH_SESSION_NOT_FOUND", start_day=start_day.isoformat())


def _next_us_cash_session_day(start_day: date, bundle: Mapping[str, Any]) -> date:
    day = start_day
    for _ in range(31):
        info = classify_us_cash_day(day, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        if info["is_open_day"]:
            return day
        day = _shift_date(day, 1, field_name="day_et")
    raise HolidayChartGuardError("NEXT_US_CASH_SESSION_NOT_FOUND", start_day=start_day.isoformat())


def _prior_cme_close_utc(start_day: date, bundle: Mapping[str, Any]) -> datetime:
    day = start_day
    for _ in range(14):
        info = classify_us_cash_day(day, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        if day.weekday() < 5 and not info["is_cme_full_day_holiday"]:
            close_t = CME_EARLY_EVE_CLOSE_ET if info["is_early_close"] else CME_WEEKEND_CLOSE_ET
            return _combine_et_to_utc(day, close_t, field_name="day_et")
        day = _shift_date(day, -1, field_name="day_et")
    raise HolidayChartGuardError("PRIOR_CME_SESSION_NOT_FOUND", start_day=start_day.isoformat())


def resolve_market_session(
    market: str,
    at_utc: Any,
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
    enforce_cme_full_day_holidays: bool = True,
) -> dict[str, Any]:
    """Resolve exact ET session status and comparison anchor across all 7 core markets."""
    market_id = require_core_market(market)
    captured = require_aware_utc(at_utc, field_name="at_utc")
    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    spec = CORE_MARKETS[market_id]
    local = _to_et(captured, field_name="at_utc")
    day_et = local.date()
    clock_et = local.time()
    day_info = classify_us_cash_day(day_et, calendar=bundle, allow_fallback=bundle["allow_fallback"])

    base: dict[str, Any] = {
        "policy": POLICY,
        "market": market_id,
        "tv_symbol": spec["tv_symbol"],
        "session_class": spec["session_class"],
        "max_difference_pct": spec["max_difference_pct"],
        "captured_at_utc": captured.isoformat(),
        "day_et": day_et.isoformat(),
        "time_et": clock_et.strftime("%H:%M:%S"),
        "us_cash_day_state": day_info["session_state"],
        "holiday_label": day_info["holiday_label"],
        "calendar_source": day_info["calendar_source"],
        "calendar_sha256": day_info["calendar_sha256"],
        "quote_max_age_seconds": QUOTE_MAX_AGE_SECONDS,
        "live_max_negative_skew_seconds": LIVE_MAX_NEGATIVE_SKEW_SECONDS,
        "settlement_max_negative_skew_seconds": LIVE_MAX_NEGATIVE_SKEW_SECONDS,
        "settlement_window_allowed": False,
        "cfd_holiday_drift_risk": False,
        "us_equity_holiday_advisory": False,
    }

    if market_id in CRYPTO_MARKETS:
        return {
            **base,
            "is_closed": False,
            "session_status": "OPEN_24X7",
            "comparison_basis": "AT_CAPTURE",
            "comparison_at_utc": captured.isoformat(),
        }

    if market_id in CASH_INDEX_MARKETS:
        if day_info["is_open_day"]:
            close_t = US_CASH_EARLY_CLOSE_ET if day_info["is_early_close"] else US_CASH_REGULAR_CLOSE_ET
            if US_CASH_OPEN_ET <= clock_et < close_t:
                return {
                    **base,
                    "is_closed": False,
                    "session_status": "OPEN_EARLY_CLOSE" if day_info["is_early_close"] else "OPEN_REGULAR",
                    "comparison_basis": "AT_CAPTURE",
                    "comparison_at_utc": captured.isoformat(),
                    "session_open_et": US_CASH_OPEN_ET.strftime("%H:%M"),
                    "session_close_et": close_t.strftime("%H:%M"),
                }
            if clock_et >= close_t:
                close_utc = _combine_et_to_utc(day_et, close_t, field_name="at_utc")
                post_early_window = bool(day_info["is_early_close"] and clock_et < US_CASH_REGULAR_CLOSE_ET)
                return {
                    **base,
                    "is_closed": True,
                    "session_status": "CLOSED_EARLY_CLOSE" if day_info["is_early_close"] else "CLOSED_POST_CLOSE",
                    "comparison_basis": "LAST_CLOSE",
                    "comparison_at_utc": close_utc.isoformat(),
                    "session_open_et": US_CASH_OPEN_ET.strftime("%H:%M"),
                    "session_close_et": close_t.strftime("%H:%M"),
                    "settlement_window_allowed": True,
                    "settlement_max_negative_skew_seconds": CASH_INDEX_CLOSE_SETTLE_SECONDS,
                    "cfd_holiday_drift_risk": post_early_window,
                }
            _, prior_info = _prior_us_cash_session_info(_shift_date(day_et, -1, field_name="at_utc"), bundle)
            return {
                **base,
                "is_closed": True,
                "session_status": "CLOSED_PRE_OPEN",
                "comparison_basis": "LAST_CLOSE",
                "comparison_at_utc": prior_info["close_utc"],
                "session_open_et": US_CASH_OPEN_ET.strftime("%H:%M"),
                "session_close_et": close_t.strftime("%H:%M"),
                "settlement_window_allowed": True,
                "settlement_max_negative_skew_seconds": CASH_INDEX_CLOSE_SETTLE_SECONDS,
                "cfd_holiday_drift_risk": False,
            }

        _, prior_info = _prior_us_cash_session_info(_shift_date(day_et, -1, field_name="at_utc"), bundle)
        is_holiday = day_info["session_state"] == "CLOSED_HOLIDAY"
        return {
            **base,
            "is_closed": True,
            "session_status": "CLOSED_HOLIDAY" if is_holiday else "CLOSED_WEEKEND",
            "comparison_basis": "LAST_CLOSE",
            "comparison_at_utc": prior_info["close_utc"],
            "settlement_window_allowed": True,
            "settlement_max_negative_skew_seconds": CASH_INDEX_CLOSE_SETTLE_SECONDS,
            "cfd_holiday_drift_risk": is_holiday,
        }

    # Common non-crypto weekend closure: Friday 17:00 ET through Sunday 18:00 ET.
    wd = local.weekday()
    if wd == 5 or (wd == 6 and clock_et < CME_WEEKEND_REOPEN_ET) or (wd == 4 and clock_et >= CME_WEEKEND_CLOSE_ET):
        friday = _shift_date(day_et, -((wd - 4) % 7), field_name="at_utc")
        friday_info = classify_us_cash_day(friday, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        if market_id in CME_COMMODITY_MARKETS and enforce_cme_full_day_holidays and friday_info["is_cme_full_day_holiday"]:
            anchor_utc = _prior_cme_close_utc(_shift_date(friday, -1, field_name="at_utc"), bundle)
        else:
            anchor_utc = _combine_et_to_utc(friday, CME_WEEKEND_CLOSE_ET, field_name="at_utc")
        return {
            **base,
            "is_closed": True,
            "session_status": "CLOSED_WEEKEND",
            "comparison_basis": "LAST_CLOSE",
            "comparison_at_utc": anchor_utc.isoformat(),
        }

    # CME/NYMEX commodities: honor full-day global holidays (Christmas Day, New Year's Day, Good Friday)
    # and the preceding holiday-eve evening when Globex stays closed past 18:00 ET.
    if market_id in CME_COMMODITY_MARKETS and enforce_cme_full_day_holidays:
        if day_info["is_cme_full_day_holiday"] and (wd == 4 or clock_et < CME_WEEKEND_REOPEN_ET):
            anchor_utc = _prior_cme_close_utc(_shift_date(day_et, -1, field_name="at_utc"), bundle)
            return {
                **base,
                "is_closed": True,
                "session_status": "CLOSED_CME_FULL_DAY_HOLIDAY",
                "comparison_basis": "LAST_CLOSE",
                "comparison_at_utc": anchor_utc.isoformat(),
                "us_equity_holiday_advisory": True,
            }
        eve_cutoff = CME_EARLY_EVE_CLOSE_ET if day_info["is_early_close"] else CME_WEEKEND_CLOSE_ET
        if clock_et >= eve_cutoff:
            next_day_info = classify_us_cash_day(
                _shift_date(day_et, 1, field_name="at_utc"),
                calendar=bundle,
                allow_fallback=bundle["allow_fallback"],
            )
            if next_day_info["is_cme_full_day_holiday"]:
                if wd == 6:
                    anchor_utc = _prior_cme_close_utc(_shift_date(day_et, -1, field_name="at_utc"), bundle)
                else:
                    anchor_utc = _combine_et_to_utc(day_et, eve_cutoff, field_name="at_utc")
                return {
                    **base,
                    "is_closed": True,
                    "session_status": "CLOSED_CME_HOLIDAY_EVE",
                    "comparison_basis": "LAST_CLOSE",
                    "comparison_at_utc": anchor_utc.isoformat(),
                    "us_equity_holiday_advisory": True,
                }

    advisory = day_info["session_state"] in {"CLOSED_HOLIDAY", "EARLY_CLOSE_13_ET"}
    return {
        **base,
        "is_closed": False,
        "session_status": "OPEN_REGULAR",
        "comparison_basis": "AT_CAPTURE",
        "comparison_at_utc": captured.isoformat(),
        "us_equity_holiday_advisory": advisory,
        **({"fx_global_holiday_advisory": True} if market_id in FX_SPOT_MARKETS and day_info["is_cme_full_day_holiday"] else {}),
    }


def _is_cfd_or_broker_quote(quote: Mapping[str, Any]) -> bool:
    return (
        quote.get("source_kind") in CFD_SOURCE_KINDS
        or quote.get("price_basis") in CFD_PRICE_BASES
    )


def _is_official_cash_settlement_quote(market: str, quote: Mapping[str, Any]) -> bool:
    return (
        market in CASH_INDEX_MARKETS
        and quote.get("source_kind") == "PUBLIC_ON_DEMAND_QUOTE"
        and quote.get("instrument_type") == "INDEX"
    )


def evaluate_quote_for_session(
    market: str,
    chart_price: Any,
    captured_at_utc: Any,
    quote: Mapping[str, Any],
    *,
    tv_symbol: str | None = None,
    visible_to_utc: Any = None,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
    max_difference_pct: Any = None,
    enforce_cme_full_day_holidays: bool = True,
) -> dict[str, Any]:
    """Evaluate one candidate reference quote against a chart price and holiday-aware session.

    Hard data-integrity errors (naive timestamps, bool/NaN/Inf/non-positive numbers,
    mismatched market/symbol/instrument, missing quote provenance, proxy symbol disguised
    as cash settlement) raise ``HolidayChartGuardError`` immediately.

    Clock/holiday inadmissibility (e.g. a moving Exness CFD quote stamped after an early
    or holiday US cash close) returns ``usable=False`` with an explicit cause instead of
    producing a false ``TRADINGVIEW_PRICE_SCALE_MISMATCH``.
    """
    market_id = require_core_market(market)
    spec = CORE_MARKETS[market_id]
    if tv_symbol is not None and tv_symbol != spec["tv_symbol"]:
        raise HolidayChartGuardError(
            "TRADINGVIEW_MARKET_SYMBOL_MISMATCH",
            market=market_id,
            expected_tv_symbol=spec["tv_symbol"],
            actual_tv_symbol=tv_symbol,
        )
    chart_val = require_positive_finite_number(chart_price, field_name="chart_price")
    captured = require_aware_utc(captured_at_utc, field_name="captured_at_utc")
    limit_pct = (
        spec["max_difference_pct"]
        if max_difference_pct is None
        else require_non_negative_finite_number(max_difference_pct, field_name="max_difference_pct")
    )
    if not isinstance(quote, Mapping):
        raise HolidayChartGuardError("TRADINGVIEW_PLAN_QUOTE_INVALID")
    if quote.get("market") != market_id or quote.get("instrument") != market_id:
        raise HolidayChartGuardError(
            "TRADINGVIEW_PLAN_QUOTE_INSTRUMENT_MISMATCH",
            market=market_id,
            quote_market=quote.get("market"),
            quote_instrument=quote.get("instrument"),
        )
    quote_val = require_positive_finite_number(quote.get("price"), field_name="quote.price")
    quoted_at = require_aware_utc(quote.get("quoted_at_utc"), field_name="quote.quoted_at_utc")
    known_at = require_aware_utc(quote.get("known_at_utc"), field_name="quote.known_at_utc")
    _require_safe_source_path(quote.get("source_path"))
    _require_sha256_hex(
        quote.get("source_sha256"),
        error_code="TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
        field="source_sha256",
    )
    for opt_field in ("price_basis", "source_symbol", "instrument_type"):
        opt_val = quote.get(opt_field)
        if opt_val is not None and isinstance(opt_val, str):
            if _CONTROL_CHAR_RE.search(opt_val):
                raise HolidayChartGuardError(
                    "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                    field=opt_field,
                    reason="control_chars_forbidden",
                )
            try:
                opt_val.encode("utf-8")
            except UnicodeEncodeError:
                raise HolidayChartGuardError(
                    "TRADINGVIEW_PLAN_QUOTE_SOURCE_REQUIRED",
                    field=opt_field,
                    reason="invalid_utf8_surrogate",
                ) from None

    source_kind = quote.get("source_kind")
    if source_kind is not None and (not isinstance(source_kind, str) or source_kind not in ALLOWED_SOURCE_KINDS):
        raise HolidayChartGuardError(
            "TRADINGVIEW_PLAN_QUOTE_SOURCE_KIND_INVALID",
            market=market_id,
            source_kind=source_kind,
        )

    official_settlement = _is_official_cash_settlement_quote(market_id, quote)
    if source_kind == "PUBLIC_ON_DEMAND_QUOTE":
        expected_instrument_type = spec["public_instrument_type"]
        actual_instrument_type = quote.get("instrument_type")
        if market_id in CASH_INDEX_MARKETS:
            if actual_instrument_type != expected_instrument_type:
                raise HolidayChartGuardError(
                    "SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN",
                    market=market_id,
                    expected_instrument_type=expected_instrument_type,
                    actual_instrument_type=actual_instrument_type,
                )
        elif actual_instrument_type is not None and actual_instrument_type != expected_instrument_type:
            raise HolidayChartGuardError(
                "SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN",
                market=market_id,
                expected_instrument_type=expected_instrument_type,
                actual_instrument_type=actual_instrument_type,
            )
        source_symbol = quote.get("source_symbol")
        if source_symbol is not None and source_symbol != spec["public_quote_symbol"]:
            raise HolidayChartGuardError(
                "SETTLEMENT_PROXY_INSTRUMENT_FORBIDDEN",
                market=market_id,
                expected_source_symbol=spec["public_quote_symbol"],
                actual_source_symbol=source_symbol,
            )

    historical = visible_to_utc is not None
    session = resolve_market_session(
        market_id,
        captured,
        calendar_path=calendar_path,
        calendar=calendar,
        allow_fallback=allow_fallback,
        enforce_cme_full_day_holidays=enforce_cme_full_day_holidays,
    )
    if historical:
        comparison_at = require_aware_utc(visible_to_utc, field_name="visible_to_utc")
        if comparison_at > captured:
            raise HolidayChartGuardError(
                "TRADINGVIEW_HISTORICAL_WINDOW_INVALID",
                visible_to_utc=comparison_at.isoformat(),
                captured_at_utc=captured.isoformat(),
            )
        closed = False
        comparison_basis = "VISIBLE_WINDOW_CLOSE"
    else:
        comparison_at = require_aware_utc(session["comparison_at_utc"], field_name="comparison_at_utc")
        closed = bool(session["is_closed"])
        comparison_basis = session["comparison_basis"]
    skew_seconds = (comparison_at - quoted_at).total_seconds()
    difference = chart_val - quote_val
    difference_pct = abs(difference) / quote_val * 100.0
    if not (math.isfinite(difference) and math.isfinite(difference_pct)):
        raise HolidayChartGuardError(
            "NON_FINITE_PERCENT_DIFFERENCE",
            market=market_id,
            chart_price=chart_val,
            quote_price=quote_val,
        )
    is_cfd = _is_cfd_or_broker_quote(quote)

    common = {
        "policy": POLICY,
        "market": market_id,
        "tv_symbol": spec["tv_symbol"],
        "session": session,
        "chart_price": chart_val,
        "quote_price": quote_val,
        "quote_source_kind": quote.get("source_kind"),
        "quoted_at_utc": quoted_at.isoformat(),
        "known_at_utc": known_at.isoformat(),
        "comparison_at_utc": comparison_at.isoformat(),
        "comparison_basis": comparison_basis,
        "clock_skew_seconds": skew_seconds,
        "maximum_difference_pct": limit_pct,
        "cfd_drift_suppressed": False,
        "settlement_print_lawful": False,
    }

    # Causality invariants are never relaxed.
    if known_at > captured:
        return {**common, "usable": False, "scale_mismatch": False, "verdict": "REJECTED_QUOTE", "cause": "FUTURE_KNOWN_CLOCK"}
    if quoted_at > known_at:
        return {**common, "usable": False, "scale_mismatch": False, "verdict": "REJECTED_QUOTE", "cause": "OBSERVED_AFTER_KNOWN"}
    if quoted_at > captured:
        return {**common, "usable": False, "scale_mismatch": False, "verdict": "REJECTED_QUOTE", "cause": "FUTURE_OBSERVATION_CLOCK"}

    if closed:
        if official_settlement:
            if skew_seconds < -CASH_INDEX_CLOSE_SETTLE_SECONDS:
                return {
                    **common,
                    "usable": False,
                    "scale_mismatch": False,
                    "verdict": "REJECTED_QUOTE",
                    "cause": "SETTLEMENT_PRINT_TOO_LATE",
                }
            if skew_seconds > QUOTE_MAX_AGE_SECONDS:
                return {
                    **common,
                    "usable": False,
                    "scale_mismatch": False,
                    "verdict": "REJECTED_QUOTE",
                    "cause": "SETTLEMENT_PRINT_TOO_OLD",
                }
            classification = "LAWFUL_CASH_SETTLEMENT_PRINT"
            settlement_lawful = True
        else:
            if skew_seconds < -LIVE_MAX_NEGATIVE_SKEW_SECONDS:
                if market_id in CASH_INDEX_MARKETS and is_cfd:
                    return {
                        **common,
                        "usable": False,
                        "scale_mismatch": False,
                        "verdict": "SKIPPED_HOLIDAY_CFD_DRIFT",
                        "cause": "CFD_QUOTE_AFTER_CASH_CLOSE",
                        "cfd_drift_suppressed": True,
                        "suppressed_cfd_difference_pct": difference_pct,
                    }
                return {
                    **common,
                    "usable": False,
                    "scale_mismatch": False,
                    "verdict": "REJECTED_QUOTE",
                    "cause": "QUOTE_AFTER_SESSION_CLOSE",
                }
            if skew_seconds > QUOTE_MAX_AGE_SECONDS:
                return {
                    **common,
                    "usable": False,
                    "scale_mismatch": False,
                    "verdict": "REJECTED_QUOTE",
                    "cause": "QUOTE_STALE_BEFORE_CLOSE",
                }
            classification = "LAWFUL_CLOSE_ANCHORED_QUOTE"
            settlement_lawful = False
    else:
        # Open session: strictly contemporaneous [-2s, +120s]; settlement window is NEVER active.
        if not -LIVE_MAX_NEGATIVE_SKEW_SECONDS <= skew_seconds <= QUOTE_MAX_AGE_SECONDS:
            return {
                **common,
                "usable": False,
                "scale_mismatch": False,
                "verdict": "REJECTED_QUOTE",
                "cause": "QUOTE_STALE_FOR_LIVE_SESSION",
            }
        classification = "LAWFUL_LIVE_CONTEMPORANEOUS"
        settlement_lawful = False

    mismatch = difference_pct > limit_pct
    if mismatch:
        verdict = "FAIL_CLOSED_SESSION_SCALE_MISMATCH" if closed else "FAIL_LIVE_SCALE_MISMATCH"
        cause = "TRADINGVIEW_PRICE_SCALE_MISMATCH"
    elif settlement_lawful:
        verdict = "PASS_CASH_SETTLEMENT"
        cause = None
    elif closed:
        verdict = "PASS_LAST_CLOSE"
        cause = None
    else:
        verdict = "PASS_LIVE_SESSION"
        cause = None

    return {
        **common,
        "usable": True,
        "quote_classification": classification,
        "settlement_print_lawful": settlement_lawful,
        "difference": difference,
        "difference_pct": difference_pct,
        "level_offset": difference if market_id == "USOIL" and quote.get("price_basis") != "chart_futures" else 0.0,
        "scale_mismatch": mismatch,
        "verdict": verdict,
        "cause": cause,
    }


def guard_chart_scale(
    market: str,
    snapshot: Mapping[str, Any],
    candidate_quotes: Sequence[Mapping[str, Any]],
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
    max_difference_pct: Any = None,
    enforce_cme_full_day_holidays: bool = True,
    raise_on_mismatch: bool = True,
) -> dict[str, Any]:
    """Holiday- and early-close-aware price-scale guard over ordered candidate quotes.

    - Evaluates candidates in exact priority order (e.g. PLAN_STATUS_EXPORT -> BAR_STORE_M1_CLOSE
      -> PUBLIC_ON_DEMAND_QUOTE -> MAIN_SAVED_TICK).
    - During US cash holidays or post-13:00 ET early closes, skips moving post-close Exness CFD
      quotes cleanly (``CFD_QUOTE_AFTER_CASH_CLOSE``) instead of tripping false
      ``TRADINGVIEW_PRICE_SCALE_MISMATCH``, falling through to a lawful cash-index settlement
      print or safe ``NOT_COMPARED``.
    - Never shops past a usable quote that measures a genuine scale mismatch: immediately fails
      closed with ``TRADINGVIEW_PRICE_SCALE_MISMATCH`` (both live mid-session and vs lawful close).
    """
    market_id = require_core_market(market)
    spec = CORE_MARKETS[market_id]
    if not isinstance(snapshot, Mapping):
        raise HolidayChartGuardError("TRADINGVIEW_SNAPSHOT_INVALID")
    if snapshot.get("tv_symbol") != spec["tv_symbol"]:
        raise HolidayChartGuardError(
            "TRADINGVIEW_MARKET_SYMBOL_MISMATCH",
            market=market_id,
            expected_tv_symbol=spec["tv_symbol"],
            actual_tv_symbol=snapshot.get("tv_symbol"),
        )
    chart_sha256 = _require_sha256_hex(
        snapshot.get("sha256"),
        error_code="TRADINGVIEW_SNAPSHOT_SHA256_REQUIRED",
        field="snapshot.sha256",
    )
    captured = require_aware_utc(snapshot.get("captured_at_utc"), field_name="snapshot.captured_at_utc")

    visible_from: datetime | None = None
    visible_to: datetime | None = None
    if snapshot.get("visible_to_utc") is not None:
        visible_from = require_aware_utc(snapshot.get("visible_from_utc"), field_name="snapshot.visible_from_utc")
        visible_to = require_aware_utc(snapshot.get("visible_to_utc"), field_name="snapshot.visible_to_utc")
        if not (visible_from < visible_to <= captured):
            raise HolidayChartGuardError(
                "TRADINGVIEW_HISTORICAL_WINDOW_INVALID",
                visible_from_utc=visible_from.isoformat(),
                visible_to_utc=visible_to.isoformat(),
                captured_at_utc=captured.isoformat(),
            )
        chart_price = require_positive_finite_number(
            snapshot.get("visible_last_price"),
            field_name="snapshot.visible_last_price",
        )
    elif "chart_price" in snapshot and snapshot["chart_price"] is not None:
        chart_price = require_positive_finite_number(snapshot["chart_price"], field_name="snapshot.chart_price")
    else:
        chart_price = parse_chart_last_price(snapshot.get("page_title"))

    if not isinstance(candidate_quotes, Sequence) or isinstance(candidate_quotes, (str, bytes)):
        raise HolidayChartGuardError("CANDIDATE_QUOTES_SEQUENCE_REQUIRED")

    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    session = resolve_market_session(
        market_id,
        captured,
        calendar=bundle,
        allow_fallback=bundle["allow_fallback"],
        enforce_cme_full_day_holidays=enforce_cme_full_day_holidays,
    )

    rejected: list[dict[str, Any]] = []
    cfd_drift_suppressed = False
    for quote in candidate_quotes:
        evaluation = evaluate_quote_for_session(
            market_id,
            chart_price,
            captured,
            quote,
            tv_symbol=snapshot.get("tv_symbol"),
            visible_to_utc=visible_to,
            calendar=bundle,
            allow_fallback=bundle["allow_fallback"],
            max_difference_pct=max_difference_pct,
            enforce_cme_full_day_holidays=enforce_cme_full_day_holidays,
        )
        if not evaluation["usable"]:
            if evaluation.get("cfd_drift_suppressed"):
                cfd_drift_suppressed = True
            rejected.append({
                "source_kind": evaluation["quote_source_kind"],
                "cause": evaluation["cause"],
                "clock_skew_seconds": evaluation["clock_skew_seconds"],
                "cfd_drift_suppressed": evaluation["cfd_drift_suppressed"],
                **(
                    {"suppressed_cfd_difference_pct": evaluation["suppressed_cfd_difference_pct"]}
                    if "suppressed_cfd_difference_pct" in evaluation
                    else {}
                ),
            })
            continue

        result = {
            "policy": POLICY,
            "image_contract_policy": IMAGE_CONTRACT_POLICY,
            "allowed": not evaluation["scale_mismatch"],
            "verdict": evaluation["verdict"],
            "cause": evaluation["cause"],
            "market": market_id,
            "tv_symbol": spec["tv_symbol"],
            "chart_sha256": chart_sha256,
            "chart_price": evaluation["chart_price"],
            "captured_at_utc": captured.isoformat(),
            "comparison_basis": evaluation["comparison_basis"],
            "comparison_at_utc": evaluation["comparison_at_utc"],
            **(
                {
                    "visible_from_utc": visible_from.isoformat(),
                    "visible_to_utc": visible_to.isoformat(),
                }
                if visible_from is not None and visible_to is not None
                else {}
            ),
            "clock_skew_seconds": evaluation["clock_skew_seconds"],
            "difference": evaluation["difference"],
            "difference_pct": evaluation["difference_pct"],
            "maximum_difference_pct": evaluation["maximum_difference_pct"],
            "level_offset": evaluation["level_offset"],
            "quote_classification": evaluation["quote_classification"],
            "settlement_print_lawful": evaluation["settlement_print_lawful"],
            "cfd_drift_suppressed": cfd_drift_suppressed,
            "selected_quote": dict(quote),
            "rejected_candidates": rejected,
            "session": session,
        }
        if evaluation["scale_mismatch"]:
            if raise_on_mismatch:
                raise HolidayChartGuardError("TRADINGVIEW_PRICE_SCALE_MISMATCH", **result)
            return result
        return result

    closed = False if visible_to is not None else bool(session["is_closed"])
    return {
        "policy": POLICY,
        "image_contract_policy": IMAGE_CONTRACT_POLICY,
        "allowed": True,
        "verdict": "NOT_COMPARED_HOLIDAY_CFD_DRIFT_SUPPRESSED" if cfd_drift_suppressed else "NOT_COMPARED",
        "cause": None,
        "market": market_id,
        "tv_symbol": spec["tv_symbol"],
        "chart_sha256": chart_sha256,
        "chart_price": chart_price,
        "captured_at_utc": captured.isoformat(),
        "comparison_basis": "NOT_COMPARED",
        "comparison_at_utc": visible_to.isoformat() if visible_to is not None else session["comparison_at_utc"],
        "quote_absent_cause": QUOTE_ABSENT_CAUSES[int(closed)],
        "level_offset": 0.0,
        "settlement_print_lawful": False,
        "cfd_drift_suppressed": cfd_drift_suppressed,
        "selected_quote": None,
        "rejected_candidates": rejected,
        "session": session,
    }


def evaluate_wrap_cadence(
    at_utc: Any,
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
) -> dict[str, Any]:
    """Resolve CC-689 daily / weekly wrap cadence and settlement windows across holidays & year rollovers."""
    now = require_aware_utc(at_utc, field_name="at_utc")
    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    day_et = _to_et(now, field_name="at_utc").date()
    day_info = classify_us_cash_day(day_et, calendar=bundle, allow_fallback=bundle["allow_fallback"])
    weekly = day_et.weekday() == 6

    try:
        next_open: date | None = _next_us_cash_session_day(_shift_date(day_et, 1, field_name="at_utc"), bundle)
    except HolidayChartGuardError as exc:
        if exc.cause == "HOLIDAY_CALENDAR_YEAR_MISSING" and exc.details.get("year") == day_et.year + 1:
            next_open = None
        else:
            raise

    next_open_iso = next_open.isoformat() if next_open is not None else None

    if day_et < WRAP_START_ET - timedelta(days=1 if weekly else 0):
        last_day, last_info = _prior_us_cash_session_info(day_et, bundle)
        return {
            "policy": POLICY,
            "at_utc": now.isoformat(),
            "day_et": day_et.isoformat(),
            "edition": None,
            "cadence_status": "PRE_START_SUPPRESSED",
            "due": False,
            "slot": None,
            "early_close_day": day_info["is_early_close"],
            "holiday_label": day_info["holiday_label"],
            "last_cash_session_et": last_day.isoformat(),
            "last_cash_close_utc": last_info["close_utc"],
            "prior_weekly_session_et": None,
            "prior_weekly_close_utc": None,
            "next_open_session_et": next_open_iso,
            "morning_map_cash_index_quote_options": None,
            "calendar_source": day_info["calendar_source"],
            "calendar_sha256": day_info["calendar_sha256"],
        }

    if day_et.weekday() == 5:
        last_day, last_info = _prior_us_cash_session_info(_shift_date(day_et, -1, field_name="at_utc"), bundle)
        return {
            "policy": POLICY,
            "at_utc": now.isoformat(),
            "day_et": day_et.isoformat(),
            "edition": None,
            "cadence_status": "WEEKEND_SUPPRESSED",
            "due": False,
            "slot": None,
            "early_close_day": False,
            "holiday_label": None,
            "last_cash_session_et": last_day.isoformat(),
            "last_cash_close_utc": last_info["close_utc"],
            "prior_weekly_session_et": None,
            "prior_weekly_close_utc": None,
            "next_open_session_et": next_open_iso,
            "morning_map_cash_index_quote_options": None,
            "calendar_source": day_info["calendar_source"],
            "calendar_sha256": day_info["calendar_sha256"],
        }

    if not weekly and not day_info["is_open_day"]:
        last_day, last_info = _prior_us_cash_session_info(_shift_date(day_et, -1, field_name="at_utc"), bundle)
        return {
            "policy": POLICY,
            "at_utc": now.isoformat(),
            "day_et": day_et.isoformat(),
            "edition": None,
            "cadence_status": "HOLIDAY_SUPPRESSED",
            "due": False,
            "slot": None,
            "early_close_day": False,
            "holiday_label": day_info["holiday_label"],
            "last_cash_session_et": last_day.isoformat(),
            "last_cash_close_utc": last_info["close_utc"],
            "prior_weekly_session_et": None,
            "prior_weekly_close_utc": None,
            "next_open_session_et": next_open_iso,
            "morning_map_cash_index_quote_options": None,
            "calendar_source": day_info["calendar_source"],
            "calendar_sha256": day_info["calendar_sha256"],
        }

    if weekly:
        start_t = WRAP_FIRST_SUNDAY_START_UTC if day_et == WRAP_START_ET - timedelta(days=1) else WRAP_WEEKLY_START_UTC
        start_utc = datetime.combine(day_et, start_t, UTC)
        deadline_utc = datetime.combine(day_et, WRAP_WEEKLY_DEADLINE_UTC, UTC)
        edition = "weekly"
        last_day, last_info = _prior_us_cash_session_info(_shift_date(day_et, -2, field_name="at_utc"), bundle)
        prior_day, prior_info = _prior_us_cash_session_info(_shift_date(day_et, -9, field_name="at_utc"), bundle)
        prior_session_et: str | None = prior_day.isoformat()
        prior_close_utc: str | None = prior_info["close_utc"]
    else:
        start_utc = _combine_et_to_utc(day_et, WRAP_DAILY_START_ET, field_name="at_utc")
        deadline_utc = _combine_et_to_utc(day_et, WRAP_DAILY_DEADLINE_ET, field_name="at_utc")
        edition = "daily"
        last_day, last_info = _prior_us_cash_session_info(_shift_date(day_et, -1, field_name="at_utc"), bundle)
        prior_session_et = None
        prior_close_utc = None

    slot = {
        "id": f"cc689-{edition}-{day_et.isoformat()}",
        "edition": edition,
        "day_et": day_et.isoformat(),
        "start_utc": start_utc.isoformat(),
        "deadline_utc": deadline_utc.isoformat(),
    }

    if now < start_utc:
        cadence_status = "BEFORE_WINDOW"
        due = False
    elif now < deadline_utc:
        cadence_status = "DUE"
        due = True
    else:
        cadence_status = "PAST_DEADLINE"
        due = False

    last_close_dt = require_aware_utc(last_info["close_utc"], field_name="last_cash_close_utc")
    if weekly:
        morning_map_options = None
    else:
        try:
            settle_end_utc = (last_close_dt + timedelta(seconds=CASH_INDEX_CLOSE_SETTLE_SECONDS)).isoformat()
        except OverflowError:
            raise HolidayChartGuardError("UTC_CLOCK_OUT_OF_RANGE", field="last_cash_close_utc", value=last_close_dt.isoformat()) from None
        morning_map_options = {
            "reference_at_utc": last_close_dt.isoformat(),
            "max_age_seconds": QUOTE_MAX_AGE_SECONDS,
            "closed_cash_index": True,
            "settlement_window_end_utc": settle_end_utc,
        }

    return {
        "policy": POLICY,
        "at_utc": now.isoformat(),
        "day_et": day_et.isoformat(),
        "edition": edition,
        "cadence_status": cadence_status,
        "due": due,
        "slot": slot,
        "early_close_day": day_info["is_early_close"],
        "holiday_label": day_info["holiday_label"],
        "last_cash_session_et": last_day.isoformat(),
        "last_cash_close_utc": last_close_dt.isoformat(),
        "last_cash_session_early_close": last_info["is_early_close"],
        "prior_weekly_session_et": prior_session_et,
        "prior_weekly_close_utc": prior_close_utc,
        "next_open_session_et": next_open_iso,
        "morning_map_cash_index_quote_options": morning_map_options,
        "calendar_source": day_info["calendar_source"],
        "calendar_sha256": day_info["calendar_sha256"],
    }


def comparison_clock(
    market: str,
    captured_at_utc: Any,
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
    enforce_cme_full_day_holidays: bool = False,
) -> tuple[datetime, bool]:
    """Drop-in ``(comparison_at_utc, is_closed)`` adapter compatible with ``publication_image_contract_v1``."""
    session = resolve_market_session(
        market,
        captured_at_utc,
        calendar_path=calendar_path,
        calendar=calendar,
        allow_fallback=allow_fallback,
        enforce_cme_full_day_holidays=enforce_cme_full_day_holidays,
    )
    return require_aware_utc(session["comparison_at_utc"], field_name="comparison_at_utc"), bool(session["is_closed"])


def evaluate_followup_chart_window(
    market: str,
    bar_open_utc: Any,
    bar_end_utc: Any,
    *,
    resolved_at_utc: Any = None,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
) -> dict[str, Any]:
    """Validate CC-778 move-chart cash-session coverage across US holidays and early closes."""
    market_id = require_core_market(market)
    spec = CORE_MARKETS[market_id]
    open_utc = require_aware_utc(bar_open_utc, field_name="bar_open_utc")
    end_utc = require_aware_utc(bar_end_utc, field_name="bar_end_utc")
    if end_utc <= open_utc:
        raise HolidayChartGuardError("INVALID_BAR_WINDOW", bar_open_utc=open_utc.isoformat(), bar_end_utc=end_utc.isoformat())

    resolved_utc = (
        require_aware_utc(resolved_at_utc, field_name="resolved_at_utc")
        if resolved_at_utc is not None
        else None
    )
    if resolved_utc is not None and not (open_utc < resolved_utc <= end_utc):
        raise HolidayChartGuardError(
            "RESOLVED_AT_OUTSIDE_BAR_WINDOW",
            bar_open_utc=open_utc.isoformat(),
            bar_end_utc=end_utc.isoformat(),
            resolved_at_utc=resolved_utc.isoformat(),
        )

    is_coarse_bar = (end_utc - open_utc) > timedelta(minutes=15)
    anchor_utc = resolved_utc if resolved_utc is not None else open_utc
    anchor_field = "resolved_at_utc" if resolved_utc is not None else "bar_open_utc"
    session_day = _to_et(anchor_utc, field_name=anchor_field).date()
    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    day_info = classify_us_cash_day(session_day, calendar=bundle, allow_fallback=bundle["allow_fallback"])

    if market_id not in CASH_INDEX_MARKETS:
        return {
            "policy": POLICY,
            "allowed": True,
            "market": market_id,
            "tv_symbol": spec["tv_symbol"],
            "refusal": None,
            "session_day_et": session_day.isoformat(),
            "holiday_label": day_info["holiday_label"],
            "is_coarse_bar": is_coarse_bar,
            "session_open_et": None,
            "session_close_et": None,
        }

    refusal_code = "CC778_CHART_MARKET_CLOSED_AT_RESOLUTION:" + spec["tv_symbol"]
    if not day_info["is_open_day"]:
        return {
            "policy": POLICY,
            "allowed": False,
            "market": market_id,
            "tv_symbol": spec["tv_symbol"],
            "refusal": refusal_code,
            "session_day_et": session_day.isoformat(),
            "holiday_label": day_info["holiday_label"],
            "is_coarse_bar": is_coarse_bar,
            "session_open_et": None,
            "session_close_et": None,
        }

    opens_utc = require_aware_utc(day_info["open_utc"], field_name="open_utc")
    closes_utc = require_aware_utc(day_info["close_utc"], field_name="close_utc")
    if resolved_utc is not None and is_coarse_bar:
        covered = opens_utc < resolved_utc <= closes_utc
    else:
        covered = opens_utc <= open_utc and end_utc <= closes_utc

    return {
        "policy": POLICY,
        "allowed": covered,
        "market": market_id,
        "tv_symbol": spec["tv_symbol"],
        "refusal": None if covered else refusal_code,
        "session_day_et": session_day.isoformat(),
        "holiday_label": day_info["holiday_label"],
        "is_coarse_bar": is_coarse_bar,
        "session_open_et": day_info["open_et"],
        "session_close_et": day_info["close_et"],
    }


DEC_JAN_FEB_MILESTONE_DATES = (
    "2026-12-24",  # Christmas Eve (13:00 ET early close)
    "2026-12-25",  # Christmas Day (Closed)
    "2026-12-27",  # Sunday weekly wrap post-Christmas
    "2026-12-28",  # Monday post-Christmas daily wrap
    "2026-12-31",  # New Year's Eve (regular equity session)
    "2027-01-01",  # New Year's Day (Closed, 2026->2027 rollover)
    "2027-01-03",  # Sunday weekly wrap post-New Year
    "2027-01-04",  # Monday post-New Year daily wrap
    "2027-01-18",  # MLK Day (Closed)
    "2027-01-19",  # Tuesday post-MLK daily wrap
    "2027-02-15",  # Presidents' Day (Closed)
    "2027-02-16",  # Tuesday post-Presidents' Day daily wrap
)


def dec_jan_holiday_audit_matrix(
    *,
    calendar_path: str | Path | None = None,
    calendar: Mapping[str, Any] | None = None,
    allow_fallback: bool = False,
) -> list[dict[str, Any]]:
    """Return a deterministic audit table for all Dec-2026 / Jan-2027 / Feb-2027 holiday milestones."""
    bundle = load_us_session_calendar(calendar_path=calendar_path, calendar=calendar, allow_fallback=allow_fallback)
    rows: list[dict[str, Any]] = []
    for iso in DEC_JAN_FEB_MILESTONE_DATES:
        day_obj = date.fromisoformat(iso)
        day_info = classify_us_cash_day(day_obj, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        probe_at = (
            datetime.combine(day_obj, time(15, 30), UTC)
            if day_obj.weekday() == 6
            else _combine_et_to_utc(day_obj, time(8, 15), field_name="day_et")
        )
        wrap = evaluate_wrap_cadence(probe_at, calendar=bundle, allow_fallback=bundle["allow_fallback"])
        rows.append({
            "day_et": iso,
            "weekday": day_info["weekday"],
            "us_cash_session_state": day_info["session_state"],
            "holiday_label": day_info["holiday_label"],
            "close_et": day_info["close_et"],
            "wrap_edition": wrap["edition"],
            "wrap_cadence_status": wrap["cadence_status"],
            "wrap_slot_id": wrap["slot"]["id"] if wrap["slot"] else None,
            "last_cash_session_et": wrap["last_cash_session_et"],
            "last_cash_close_utc": wrap["last_cash_close_utc"],
            "prior_weekly_session_et": wrap["prior_weekly_session_et"],
            "prior_weekly_close_utc": wrap["prior_weekly_close_utc"],
        })
    return rows
