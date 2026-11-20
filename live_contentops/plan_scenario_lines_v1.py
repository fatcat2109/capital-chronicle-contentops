"""Ops Product interim, 20 Nov 2026: a new plan's first post quotes the analyst's own scenario text.

Jim, 20 Nov: plan posts showed only the condition, the levels and the target. The analysis copy
(CC-466) waits for the plan's Substack page, which the page writer rarely finishes, so readers saw
no analysis at all. This module quotes Main's export directly: no model, no page, no wait.

Each line is the analyst's own text from `scenario_analysis`. Times become ET. A line that fails
any existing public check (the CC-466 reader rules, the decision 35/40 copy guard, the CC-549
voice check) or carries an internal token is left out, never rewritten. CC-688's layer lines
replace this when they go live.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re

CONTRACT = "OPS_SCENARIO_LINES_V1"
EFFECTIVE = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
MAX_LINE = 240
LAYERS = (("Macro", ("mechanism", "driver")), ("Priced in", ("priced",)), ("Positioning", ("positioning",)))
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ISO_TIME = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]00:00)?")
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
BARE_UTC = re.compile(r"\b\d{1,2}:\d{2}(?:\s*[-–]\s*\d{1,2}:\d{2})?Z\b|\bUTC\b|\bGMT\b")
INTERNAL_CAPS = re.compile(r"\b(?:MIXED|CLEAR|AMBIGUOUS|ACCEPTED|REJECTED|MISSING|UNKNOWN|PENDING|STALE|NONE|NULL|"
                           r"TRUE|FALSE|UP|DOWN|FLAT|LONG|SHORT)\b|\b[A-Z]{3,}:[A-Z]{3,}\b")
INTERNAL_WORDS = re.compile(r"\b[a-z0-9]+_[a-z0-9_]+\b|\bcc[- ]?\d{2,4}\b|\bKB:|\.md\b|@[0-9a-f]{7,}|\b[0-9a-f]{12,}\b|"
                            r"\b(?:digest|slot|capture|candidate|normal days?|the pack|lane|odds|starter|freeze|frozen|"
                            r"yardstick|sweep|proxy|missing|not observed|not read|unconfirmed)\b", re.I)


def _et(value):
    from .plan_reader_copy_v1 import et
    return et(value)


def _clean(text):
    """The analyst's sentence in public form, or None when it cannot be shown as written."""
    if not isinstance(text, str) or not text.strip():
        return None, []
    text = " ".join(text.split())
    converted = []

    def to_et(match):
        value = _et(match.group(0) if match.group(0).endswith(("Z", "00:00")) else match.group(0) + "Z")
        converted.append(value)
        return value

    text = ISO_TIME.sub(to_et, text)

    def to_day(match):
        value = f"{int(match[3])} {MONTHS[int(match[2]) - 1]}"
        converted.append(value)
        return value

    text = ISO_DATE.sub(to_day, text)
    if BARE_UTC.search(text) or INTERNAL_CAPS.search(text) or INTERNAL_WORDS.search(text):
        return None, []
    text = text.rstrip(" ;,")
    if not text.endswith((".", "!", "?")):
        text += "."
    return text[0].upper() + text[1:], converted


def _passes(line, source):
    from .event_article_guard_v1 import check_publication_copy
    from .plan_reader_copy_v1 import check_text, check_thread_text
    if len(line) > MAX_LINE:
        return False
    try:
        check_thread_text(line)
        # Quoted analyst sentences keep their length; the reader rules' other checks all apply.
        check_text(line, source=source, prose=False)
        check_publication_copy({"body": line}, require_notice=False)
    except ValueError:
        return False
    return True


def _odds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < 100:
        return None
    return f"{value:g}"


def analysis_lines(raw):
    """Up to five public lines from this plan's own export, in reading order."""
    scenario = raw.get("scenario_analysis") or {}
    if not isinstance(scenario, dict):
        return []
    source = json.dumps(raw, ensure_ascii=False, sort_keys=True)
    out = []

    def add(label, text, odds=None):
        cleaned, converted = _clean(text)
        if not cleaned:
            return False
        line = f"{label}: {cleaned}"
        # The ET clocks and the odds are transforms of this plan's own fields.
        extra = converted + ([odds + "%"] if odds else [])
        if _passes(line, source + "\n" + "\n".join(extra)):
            out.append(line)
            return True
        return False

    for label, keys in LAYERS:
        for key in keys:
            if add(label, scenario.get(key)):
                break
    base, alt = scenario.get("base_case") or {}, scenario.get("main_alternative") or {}
    base_odds, alt_odds = _odds(base.get("probability_pct")), _odds(alt.get("probability_pct"))
    if base_odds and add(f"Main ({base_odds}%)", base.get("market_move"), base_odds) and alt_odds:
        add(f"Alternative ({alt_odds}%)", alt.get("market_move"), alt_odds)
    return out
