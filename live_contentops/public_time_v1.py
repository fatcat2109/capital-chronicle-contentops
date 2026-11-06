"""Jim decision 90: public dates and times use New York time, labelled ET.

UTC records and Bangkok scheduling are separate from reader presentation.
"""
from datetime import datetime
from html import unescape
import re
from zoneinfo import ZoneInfo

PUBLIC_ZONE = ZoneInfo("America/New_York")
POLICY = "JIM_DECISION_90_PUBLIC_ET"
REASON = "PUBLIC_TIMEZONE_ET_REQUIRED"
WRITER_GUIDANCE = (
    "JIM DECISION 90 PUBLIC TIME: Every public article, social copy, card and dated line "
    "uses New York time (America/New_York), written ET, including date-correct daylight saving. "
    "Convert each supplied instant before choosing its public date; never hardcode UTC-5. "
    "Never print GMT+7, UTC+7, Bangkok time or Vietnam time in public copy. "
    "A source's date-only observation period stays date-only; never invent a clock. "
    "Records keep UTC and internal production calendars stay unchanged. "
    "Do not edit already-published posts for this rule. TradingView's own snapshot header stays as supplied."
)
_FORBIDDEN = re.compile(
    r"\b(?:GMT|UTC)\s*[+＋]\s*0?7(?::?00)?(?!\d)|Asia/Bangkok|"
    r"\bBangkok\s+(?:time|times)|\bVietnam(?:ese)?\s+time|"
    r"\b\d{1,2}:\d{2}\s+Bangkok\b", re.I)


def public_datetime(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if value.tzinfo is None:
        raise ValueError("READER_TIMESTAMP_REQUIRES_AWARE_INSTANT")
    return value.astimezone(PUBLIC_ZONE)


def public_timestamp(value):
    local = public_datetime(value)
    return f"{local:%H:%M} ET on {local.day} {local:%B %Y}"


def public_date(value):
    local = public_datetime(value)
    return f"{local:%B} {local.day}, {local.year}"


def find_forbidden_public_time(*values):
    from live_contentops.preview_link_guard_v1 import _strings
    for text in _strings(list(values)):
        match = _FORBIDDEN.search(unescape(text))
        if match:
            return match.group(0)
    return None


def require_public_time(*values):
    if find_forbidden_public_time(*values):
        raise ValueError(REASON)


def public_media_text(assets):
    # Source clocks, paths, rights records and TradingView's authentic header are not public copy.
    return [{k: a[k] for k in ("caption", "alt_text", "title", "attribution") if k in a}
            for a in assets or []]


def public_article_text(article):
    return {k: article[k] for k in ("title", "subtitle", "dek", "substack_body_markdown",
        "display_date", "social_hook", "social_mechanism_summary", "social_policy_summary",
        "social_cross_asset_summary", "editorial_scope_notice") if k in article}
