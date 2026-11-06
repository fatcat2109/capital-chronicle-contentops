"""Offline public-copy checks for CC-107 event previews and reviews.

Evidence is a separately pinned admission from the existing source/rights owner,
never a permission supplied by the article. This checker grants no publication
authority and performs no model, transport, store or scheduler operation.

Jim's decision 72 b (CC-262, CC-264): consensus, forecast, surprise, beat, miss and
gamma are ordinary words here. A consensus figure is admitted as one
CITED_THIRD_PARTY_FACT whose evidence names its source (``attribution``) and date
(``cited_on``, YYYY-MM-DD), and the section that prints it names both. Our computed
outputs are admitted as CC_MODEL_ESTIMATE facts (``estimate_label`` "Capital
Chronicle model estimate"); the section that prints one carries the label, and the
piece carries decision 40's two notices. DEMO identifiers, broker servers, lot sizes,
R multiples, prediction-market numbers and unconditional calls stay refused.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping
from zoneinfo import ZoneInfo


SCHEMA = "contentops.event_article.v1"
EVIDENCE_SCHEMA = "contentops.event_article_evidence.v1"
DISCLAIMER = "This is general market analysis, not financial advice."
PUBLIC_NOTICE = "Analysis, not financial advice."
CONFLICTS_NOTICE = "Capital Chronicle may hold positions in the markets it covers."
# Decision 72 b: the rights classes of a cited third-party figure and of our computed outputs (schema 1.4, CC-262).
CITED_FACT = "CITED_THIRD_PARTY_FACT"
MODEL_ESTIMATE = "CC_MODEL_ESTIMATE"
MODEL_ESTIMATE_LABEL = "Capital Chronicle model estimate"
# Host rule 7: single facts with their source and date, never a table or series from one source. Four or more
# figures from one source in one piece are its table, as in the canonical check_public_text (BULK_MIN_VALUES = 4).
CITED_FACTS_PER_SOURCE_LIMIT = 3
ARTICLE_TYPES = ("EVENT_PREVIEW", "EVENT_REVIEW")
REACTION_ASSETS = {"rates", "dollar", "gold", "oil", "indices", "sectors"}
SECTIONS = {
    "EVENT_PREVIEW": {"headline", "dek", "context", "scenarios", "probability_basis",
                      "market_reactions", "view_changes", "disclaimer"},
    "EVENT_REVIEW": {"headline", "dek", "what_happened", "scenario_match",
                     "forecast_score", "consensus_comparison",
                     "prediction_market_comparison", "market_reactions", "lesson",
                     "disclaimer"},
}
EVENT_FRAME_SECTIONS = {
    "EVENT_PREVIEW": {"what_is_priced", "pre_event_range", "branch_confirmation"},
    "EVENT_REVIEW": {"what_moved_when"},
}


def event_writer_guidance(governed: Mapping[str, Any]) -> str:
    """Put CC-107's current brief in the existing native writer's request.

    Use explicit event metadata only. Source prose cannot choose a new role.
    Frozen native requests retain their original prompt in the caller.
    """
    candidate = governed.get("selected_candidate") or {}
    metadata = candidate.get("research_metadata") or {}
    tags = candidate.get("candidate_catalyst_tags") or []
    kind = (governed.get("article_type") or candidate.get("article_type")
            or metadata.get("article_type"))
    if kind not in ARTICLE_TYPES:
        kind = next((tag for tag in tags if tag in ARTICLE_TYPES), None)
    if kind not in ARTICLE_TYPES:
        # The candidate compiler keeps source metadata on documents, not tags.
        # Only the preparation owner's explicit type can select this brief.
        for document in governed.get("source_pack", []):
            allowed = (document.get("source_reuse_constraints") or {}).get("article_types")
            if document.get("preview_preparation") and allowed == ["EVENT_PREVIEW"]:
                kind = "EVENT_PREVIEW"
                break
    if kind not in ARTICLE_TYPES:
        return ""
    name = "event_preview.md" if kind == "EVENT_PREVIEW" else "event_review.md"
    brief = Path(__file__).resolve().parents[1] / "docs/publisher/EVENT_ARTICLES_V1/templates" / name
    guidance = "\nCC107_EVENT_RESOLUTION_FRAME\n" + brief.read_text(encoding="utf-8")
    if any(d.get("frozen_public_record") for d in governed.get("source_pack", [])):
        guidance += ("\nCC338_FROZEN_PUBLIC_RECORD\nUse Main's exact frozen public record in source_pack. "
            "Print its full SHA-256 and frozen_at_et verbatim in the article. A preview headline contains "
            "one branch's exact condition, market, bullish/bearish direction, minimum_move and horizon. "
            "Explain comparison with its naive_release_beta, keeping Main's supplied units and scoring rule. "
            "A review includes the complete public_call_scorecard canonical_content_text verbatim. "
            "Include each original scorecard call in article.conditional_calls so the public-copy guard "
            "can match its conditional wording, without changing the original text. "
            "Never omit withdrawn, invalidated, not-triggered or unresolved calls. The transport uploads "
            "the original frozen file; never reconstruct it. Keep the structured metadata outside the "
            "event packet's copy/numeric_bindings. Bind numerical prose to the source's exact offsets.\n")
    return guidance


_ROOT_KEYS = {"schema_version", "article_type", "event_id", "event_time_utc",
              "cutoff_utc", "written_at_utc", "copy", "numeric_bindings"}
_SHA = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_KEY = re.compile(
    r"(?:^|_)(?:entries|entry|stop|stops|sl|stoploss|takeprofit|tp|targets?|"
    r"sizes?|sizing|lots?|volume|account|demo|mt5|positions?|holdings?|"
    r"balances?|equity|pnl|profit|loss|fills?|orders?|tickets?)(?:_|$)"
)
# DEMO and execution identifiers (decision 40, host rule 7). The broker server, DEMO logins and lot sizes follow the
# canonical check_public_text (CC-262): "Exness-MT5Trial8", "279805139", "0.05 lots" and "lot size" are refused,
# while "a lot of" or "lots of" in ordinary prose is not a size.
_PRIVATE_TEXT = re.compile(
    r"\b(?:demo|mt[45]|mt5\s*trial\d*|exness[\w-]*|metatrader\s*\d?|stop[ -]?loss|take[ -]?profit|entry price|"
    r"entry level|position siz(?:e|ing)|account (?:id|number|balance|equity)|"
    r"portfolio (?:positions?|results?|returns?)|our (?:positions?|holdings?)|"
    r"p\s*&\s*l|lot\s+sizes?)\b|"
    r"(?<![\w.])(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|half\s+a|a\s+single)\s*"
    r"(?:standard\s+|mini\s+|micro\s+)?lots?\b|"
    r"(?<!\w)[+-]?\d+(?:\.\d+)?\s*r\b|(?<![\w.])(?:279805139|279779602)(?!\w)", re.I
)
_INSTRUCTION = re.compile(
    r"\b(?:go|stay|remain)\s+(?:long|short)\b|"
    r"\b(?:should|must|please|recommend(?:s|ed)?|advise(?:s|d)?)\s+"
    r"(?:(?:you|we|investors?|traders?)\s+)?(?:to\s+)?(?:buy|sell|buying|selling|"
    r"enter|exit|hold|reduce|increase)\b|"
    r"\b(?:buy|sell|long|short|entry|stop|target|size)\s*[:=@]\s*\S|"
    r"(?:^|[.!?;:\n])\s*(?:[-*]\s*)?(?:buy|sell|enter|exit|short|long)"
    r"\b(?![- ](?:side|off|term|dated|covering)\b)|"
    r"\b(?:price target|target price|stop at|stop below|stop above|"
    r"risk per trade|percent of (?:your |our )?(?:equity|capital))\b|"
    r"\b(?:consider|start)\s+(?:buying|selling|accumulating|shorting)\b|"
    r"\b(?:we|you|investors?|traders?)\s+(?:can|could|would|may|should|must)\s+"
    r"(?:buy|sell|enter|exit|short|hold|accumulate)\b|"
    r"\bwe\s+(?:hold|own|bought|sold)\b|"
    r"\b(?:entry|stop|target|size)\s+(?:at\s+)?[$\d]", re.I
)
# Grouping separators are retained in the match and removed only for comparison.
# Units, signs and decimals remain significant; no rounding or conversion is admitted.
_NUMBER = re.compile(
    r"[+\-\u2212]?(?:\d{1,3}(?:[,\u2009\u202f ]\d{3})+|\d+)"
    r"(?:\.\d+)?(?:[eE][+\-]?\d+)?\s*(?:%|[rR]\b)?"
)
_NEVER_PUBLIC = {"NOT_GRANTED", "UNKNOWN", "UNCLASSIFIED", "LICENSE_REQUIRED",
                 "CONDITIONAL", "INTERNAL_RESEARCH_ONLY"}
# Digits that belong to a name, not a figure: a maturity, a quarter, a group, an index or its CFD symbol ("the 10-year
# yield", "S&P 500", "US500"). A figure written beside a name ("S&P 500 at 6,812") still needs its own binding.
NAMED_NUMBER = re.compile(
    r"(?<![\w.,])\d{1,2}-(?:year|month|week|day)\b|\bQ[1-4]\b|\bG-?(?:7|20)\b|"
    r"\bS&P\s?(?:100|400|500|600)\b|\bNasdaq[- ]?100\b|\bRussell\s?(?:1000|2000|3000)\b|"
    r"\bFTSE\s?(?:100|250|350)\b|\b(?:DAX|CAC)\s?40\b|\bNikkei\s?225\b|"
    r"\b(?:Euro\s)?Stoxx\s?(?:Europe\s)?(?:50|600)\b|\b(?:ASX|KOSPI)\s?200\b|"
    r"\b(?:US500|US30|US100|US2000|SPX500|NAS100|UK100|GER40|DE40|FRA40|EU50|JP225|AUS200|HK50)\b", re.I)
_ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december")


def iso_day(value: Any) -> bool:
    """A calendar date written YYYY-MM-DD, as a cited figure's ``cited_on``."""
    if not isinstance(value, str) or not _ISO_DAY.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def cited_date_pattern(iso_date: str) -> re.Pattern[str]:
    """The ways prose writes one cited date: 2026-11-04, 4 November, 4th Nov. 2026, November 4, Nov 4, 2026.

    The day never joins a longer number and the year is optional. Shared by the event checker and the desk-record
    citation check, so a consensus figure's date is part of its citation, never an unbound number."""
    if not iso_day(iso_date):
        raise ValueError("CITED_DATE_INVALID")
    day = date.fromisoformat(iso_date)
    month = _MONTHS[day.month - 1]
    names = sorted({month, month[:3], *(("sept",) if day.month == 9 else ())}, key=len, reverse=True)
    mon = r"(?:%s)\.?" % "|".join(names)
    num = r"(?<![\d.,])0?%d(?:st|nd|rd|th)?(?!\d)(?![.,]\d)" % day.day
    year = r"(?:,?\s+%d(?!\d))?" % day.year
    return re.compile(r"\b%s\b|%s\s+(?:of\s+)?%s(?![a-z])%s|\b%s\s+%s%s" % (
        re.escape(iso_date), num, mon, year, mon, num, year), re.I)


class PublicOutputError(ValueError):
    """A cause and copy location only: never echo private input in diagnostics."""

    def __init__(self, cause: str, location: str):
        self.cause, self.location = cause, location
        super().__init__(cause)


def public_execution_copy_forbidden(text: str) -> bool:
    """Keep position calls private while allowing a central bank's policy target."""
    if _PRIVATE_TEXT.search(text):
        return True
    for match in _INSTRUCTION.finditer(text):
        before = text[max(0, match.start() - 65):match.start()]
        policy_target = (match.group().lower().startswith("target") and re.search(
            r"(?:federal funds|inflation|policy rate|the Fed held its)\s+$", before, re.I))
        if not policy_target:
            return True
    return False


def conditional_call_text(call: Mapping[str, Any]) -> str:
    """Decision 40's general, impersonal form; no numeric computation or advice."""
    return (f"If {call['condition']}, the desk is {call['direction']} on {call['market']} "
            f"over {call['horizon']}. Invalidated if {call['invalidation']}.")


def check_publication_copy(copy: Mapping[str, Any], *, conditional_calls=None,
                           require_notice: bool = True, require_call_text: bool = True) -> dict[str, Any]:
    """Shared Substack/feed gate: decision 35 as amended by decision 40.

    Source/number admission remains with the existing evidence owner. Structured
    calls must appear verbatim in the authored copy; this function never writes one.
    """
    calls = [] if conditional_calls is None else conditional_calls
    if not isinstance(calls, list):
        _fail("CONDITIONAL_CALLS_ARRAY_REQUIRED", "conditional_calls")
    _private_keys(copy, "copy")
    _private_keys(calls, "conditional_calls")
    texts = []

    def collect(value):
        if isinstance(value, str):
            texts.append(re.sub(r"[`*_]", "", _text(value)))
        elif isinstance(value, Mapping):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(copy)
    combined = "\n".join(texts)
    if require_notice and not re.search(r"analysis,?\s+not financial advice", combined, re.I):
        _fail("PUBLIC_ANALYSIS_NOTICE_REQUIRED", "copy")
    remainder = combined
    for call in calls:
        required = {"condition", "direction", "market", "horizon", "invalidation"}
        optional = {"call_id", "trigger", "score"}
        if (not isinstance(call, Mapping) or not required <= set(call)
                or set(call) - required - optional
                or any(not isinstance(call[k], str) or not call[k].strip() for k in required)
                or call["direction"] not in {"bullish", "bearish"}):
            _fail("CONDITIONAL_CALL_FIELDS_REQUIRED", "conditional_calls")
        for key in required - {"direction"}:
            if re.search(r"\b(?:bullish|bearish|buy|sell)\b", call[key], re.I):
                _fail("CALL_CONDITION_OR_INVALIDATION_INVALID", "conditional_calls")
        if call["condition"].strip().casefold() in {"always", "true", "none", "n/a", "no condition", "unconditional"}:
            _fail("CALL_CONDITION_OR_INVALIDATION_INVALID", "conditional_calls")
        wording = conditional_call_text(call)
        if require_call_text and wording not in combined:
            _fail("CONDITIONAL_CALL_NOT_IN_AUTHORED_COPY", "conditional_calls")
        remainder = remainder.replace(wording, "")
    if calls and CONFLICTS_NOTICE not in combined:
        _fail("CONFLICTS_NOTICE_REQUIRED", "copy")
    if re.search(r"\b(?:bullish|bearish)\b", remainder, re.I):
        _fail("UNCONDITIONAL_CALL_FORBIDDEN", "copy")
    for call in calls:
        collect({k: v for k, v in call.items() if k != "direction"})
    for text in texts:
        if public_execution_copy_forbidden(text):
            _fail("PRIVATE_OR_EXECUTION_COPY_FORBIDDEN", "copy")
        if re.search(r"(?:PRIVATE[_ ]*ONLY|INTERNAL[_ ]*PROVENANCE|BROKER[_ ]*PROXY[_ ]*RAW[_ ]*PRIVATE|"
                     r"CODEX[_ ]*DIGEST[_ ]*INTERNAL|DEMO[_ ]*DERIVED[_ ]*PRIVATE)", text, re.I):
            _fail("PRIVATE_LABEL_IN_PUBLIC_COPY", "copy")
        for sentence in re.split(r"[\n.!?](?!\d)", text):
            # Odds stay in words (decision 40); an index or maturity name beside a market is not a number.
            if (re.search(r"\b(?:Kalshi|Polymarket|prediction.market|market odds)\b", sentence, re.I)
                    and _NUMBER.search(NAMED_NUMBER.sub(" ", sentence))):
                _fail("PREDICTION_MARKET_NUMBER_FORBIDDEN", "copy")
    return {"status": "PASS", "policy": "JIM_DECISIONS_35_40", "conditional_call_count": len(calls)}


def _fail(cause: str, location: str) -> None:
    raise PublicOutputError(cause, location)


def _text(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", value)
                   if unicodedata.category(c) != "Cf")


def _key(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", _text(value).casefold()).strip("_")


def _time(value: Any, location: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
            raise ValueError
        return result.astimezone(timezone.utc)
    except (AttributeError, TypeError, ValueError, OverflowError):
        _fail("UTC_CLOCK_REQUIRED", location)


def _strings(node: Any, location: str = "copy"):
    if isinstance(node, str):
        yield location, node
    elif isinstance(node, Mapping):
        for key, value in node.items():
            if not isinstance(key, str):
                _fail("COPY_KEY_INVALID", location)
            yield from _strings(value, location + "." + key)
    else:
        _fail("AUTHORED_TEXT_REQUIRED", location)


def _private_keys(node: Any, location: str = "article") -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if not isinstance(key, str):
                _fail("ARTICLE_KEY_INVALID", location)
            if _PRIVATE_KEY.search(_key(key)):
                _fail("PRIVATE_FIELD_FORBIDDEN", location)
            _private_keys(value, location + "." + key)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _private_keys(value, f"{location}[{index}]")


def _numbers(text: str) -> list[str]:
    result = []
    for match in _NUMBER.finditer(_text(text)):
        token = re.sub(r"[,\s\u2009\u202f]", "", match.group()).replace("\u2212", "-")
        unit = token[-1] if token[-1:] in {"%", "r", "R"} else ""
        try:
            value = Decimal(token[:-1] if unit else token)
            if not value.is_finite():
                raise InvalidOperation
        except InvalidOperation:
            _fail("NUMBER_INVALID", "copy")
        result.append(str(value.normalize()) + unit.upper())
    return result


def _display_text(text: str) -> str:
    return re.sub(r"(?<=\d)[,\u2009\u202f](?=\d)", "", _text(text)).strip()


def _fact(fact: Any, cutoff: datetime, event_time: datetime, location: str) -> str:
    if not isinstance(fact, Mapping):
        _fail("PUBLIC_EVIDENCE_MISSING", location)
    rights = fact.get("rights_class")
    if (not isinstance(rights, str) or not rights.strip()
            or rights.upper() in _NEVER_PUBLIC or "PRIVATE_ONLY" in rights.upper()
            or fact.get("public_use_allowed") is not True
            or not isinstance(fact.get("rights_evidence_ref"), str)
            or not fact["rights_evidence_ref"].strip()):
        _fail("PUBLIC_REUSE_RIGHTS_NOT_ADMITTED", location)
    if (not isinstance(fact.get("source_ref"), str) or not fact["source_ref"].strip()
            or not _SHA.fullmatch(str(fact.get("source_sha256", "")))
            or not isinstance(fact.get("display"), str) or not fact["display"].strip()
            or not isinstance(fact.get("use_label"), str) or not fact["use_label"].strip()):
        _fail("SOURCE_BINDING_REQUIRED", location)
    # Decision 72 b: a cited third-party figure names its source and date; our model output carries its label.
    if rights.strip().upper() == CITED_FACT and (
            not isinstance(fact.get("attribution"), str) or not fact["attribution"].strip()
            or not iso_day(fact.get("cited_on"))):
        _fail("CITED_FACT_SOURCE_AND_DATE_REQUIRED", location)
    if rights.strip().upper() == MODEL_ESTIMATE and fact.get("estimate_label") != MODEL_ESTIMATE_LABEL:
        _fail("MODEL_ESTIMATE_LABEL_REQUIRED", location)
    known = _time(fact.get("known_at_utc"), location)
    if known > cutoff:
        _fail("EVIDENCE_AFTER_CUTOFF", location)
    if fact.get("kind") == "PRE_EVENT_FORECAST" and known >= event_time:
        _fail("FORECAST_NOT_FROZEN_BEFORE_EVENT", location)
    return fact["display"]


def check_public_event_article(article: Mapping[str, Any], *,
                               evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Check all authored surfaces against a separately trusted owner admission.

    The caller must pin evidence from project(public) or the existing dossier
    source/rights owner. A writer must never author that context. In particular,
    CC-104's public terms decision is required before market odds enter it.

    A CITED_THIRD_PARTY_FACT (a consensus figure) is one fact: its evidence carries
    ``attribution`` and ``cited_on``, the section printing it names both, and its date
    there is part of the citation. At most three figures from one source appear in a
    piece; four are its table. A CC_MODEL_ESTIMATE carries ``estimate_label``; the
    section printing it says "Capital Chronicle model estimate", and the piece carries
    decision 40's notices.
    """
    if not isinstance(article, Mapping):
        _fail("ARTICLE_OBJECT_REQUIRED", "article")
    _private_keys(article)
    if (set(article) - {"conditional_calls"} != _ROOT_KEYS
            or article.get("schema_version") != SCHEMA):
        _fail("ARTICLE_SCHEMA_INVALID", "article")
    kind = article.get("article_type")
    if kind not in ARTICLE_TYPES:
        _fail("EVENT_ARTICLE_TYPE_INVALID", "article.article_type")
    if not isinstance(article.get("event_id"), str) or not article["event_id"].strip():
        _fail("EVENT_ID_REQUIRED", "article.event_id")
    event_time = _time(article.get("event_time_utc"), "article.event_time_utc")
    cutoff = _time(article.get("cutoff_utc"), "article.cutoff_utc")
    written = _time(article.get("written_at_utc"), "article.written_at_utc")
    if cutoff > written or (kind == "EVENT_PREVIEW" and written >= event_time):
        _fail("PREVIEW_OR_WRITING_CLOCK_INVALID", "article.written_at_utc")
    if kind == "EVENT_REVIEW" and cutoff < event_time:
        _fail("REVIEW_BEFORE_EVENT", "article.cutoff_utc")
    copy = article.get("copy")
    if (not isinstance(copy, Mapping) or not SECTIONS[kind] <= set(copy)
            or set(copy) - SECTIONS[kind] not in (set(), EVENT_FRAME_SECTIONS[kind])):
        _fail("EVENT_SECTIONS_REQUIRED", "copy")
    if (not isinstance(copy.get("market_reactions"), Mapping)
            or set(copy["market_reactions"]) != REACTION_ASSETS
            or not all(isinstance(v, str) for v in copy["market_reactions"].values())):
        _fail("ALL_MARKET_REACTION_ASSETS_REQUIRED", "copy.market_reactions")
    for key, value in copy.items():
        if key != "market_reactions" and not isinstance(value, str):
            _fail("AUTHORED_TEXT_REQUIRED", "copy." + key)
    if copy.get("disclaimer") != DISCLAIMER:
        _fail("GENERAL_ANALYSIS_DISCLAIMER_REQUIRED", "copy.disclaimer")
    if (not isinstance(evidence, Mapping) or evidence.get("schema_version") != EVIDENCE_SCHEMA
            or evidence.get("event_id") != article["event_id"]
            or not isinstance(evidence.get("facts"), Mapping)
            or not isinstance(evidence.get("private_text"), list)
            or not all(isinstance(v, str) and v.strip() for v in evidence["private_text"])):
        _fail("PINNED_EVENT_EVIDENCE_REQUIRED", "evidence")
    texts = dict(_strings(copy))
    check_publication_copy(copy, conditional_calls=article.get("conditional_calls", []))
    for path, value in texts.items():
        text = _text(value)
        # Formatting is not a route around an execution/private-content refusal.
        scan = re.sub(r"[`*_]", "", text)
        if not text.strip():
            _fail("EMPTY_EVENT_SECTION", path)
        if public_execution_copy_forbidden(scan):
            _fail("PRIVATE_OR_EXECUTION_COPY_FORBIDDEN", path)
        if re.search(r"<[^>]*>|!\[", scan):
            _fail("UNREVIEWED_EMBEDDED_MEDIA_FORBIDDEN", path)
        for private in evidence["private_text"]:
            if _text(private).casefold() in text.casefold():
                _fail("PRIVATE_TEXT_IN_PUBLIC_COPY", path)
    bindings = article.get("numeric_bindings")
    if not isinstance(bindings, list):
        _fail("NUMERIC_BINDINGS_REQUIRED", "article.numeric_bindings")
    coverage = {path: [] for path in texts}
    cited_dates = {path: [] for path in texts}  # a cited figure's own date, part of its citation
    cited_by_source: dict[str, set[str]] = {}
    model_estimate_bound = False
    for index, binding in enumerate(bindings):
        location = f"numeric_bindings[{index}]"
        if not isinstance(binding, Mapping) or set(binding) != {"copy_path", "start", "end", "evidence_ref"}:
            _fail("NUMERIC_BINDING_INVALID", location)
        path, start, end = binding["copy_path"], binding["start"], binding["end"]
        if (not isinstance(path, str) or path not in texts
                or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(texts[path])
                or not isinstance(binding["evidence_ref"], str)):
            _fail("NUMERIC_BINDING_SPAN_INVALID", location)
        surface = texts[path][start:end]
        fact = evidence["facts"].get(binding["evidence_ref"])
        display = _fact(fact, cutoff, event_time, location)
        # Exact wording, precision, sign and unit remain source-owned. Only Unicode
        # presentation and digit grouping may differ; numbers are never inferred.
        if _display_text(surface) != _display_text(display) or not _numbers(surface):
            _fail("SOURCE_DISPLAY_MISMATCH", location)
        if any(start < b and a < end for a, b in coverage[path]):
            _fail("OVERLAPPING_NUMERIC_BINDINGS", location)
        coverage[path].append((start, end))
        rights = fact["rights_class"].strip().upper()
        section = _text(texts[path])
        if rights == CITED_FACT:
            dates = [m.span() for m in cited_date_pattern(fact["cited_on"]).finditer(section)]
            if _text(fact["attribution"]).strip().casefold() not in section.casefold() or not dates:
                _fail("CITED_FACT_SOURCE_AND_DATE_REQUIRED", location)
            cited_dates[path].extend(dates)
            cited_by_source.setdefault(_text(fact["attribution"]).strip().casefold(), set()).add(
                _display_text(display))
        elif rights == MODEL_ESTIMATE:
            if MODEL_ESTIMATE_LABEL.casefold() not in section.casefold():
                _fail("MODEL_ESTIMATE_LABEL_REQUIRED", location)
            model_estimate_bound = True
    if any(len(figures) > CITED_FACTS_PER_SOURCE_LIMIT for figures in cited_by_source.values()):
        _fail("THIRD_PARTY_TABLE_OR_SERIES_FORBIDDEN", "article.numeric_bindings")
    if model_estimate_bound and CONFLICTS_NOTICE not in "\n".join(
            re.sub(r"[`*_]", "", _text(value)) for value in texts.values()):
        _fail("CONFLICTS_NOTICE_REQUIRED", "copy")
    for path, text in texts.items():
        # Work on original offsets; normalisation above must not move span bounds.
        normalized = _text(text)
        if len(normalized) != len(text) and _numbers(text):
            _fail("NUMERIC_TEXT_REQUIRES_PLAIN_UNICODE", path)
        names = [m.span() for m in NAMED_NUMBER.finditer(normalized)]
        for match in _NUMBER.finditer(normalized):
            start, end = match.span()
            end = len(normalized[:end].rstrip())
            if not any(a <= start and end <= b for a, b in coverage[path] + cited_dates[path] + names):
                _fail("UNBOUND_PUBLIC_NUMBER", path)
    return {"status": "PASS", "public_copy_sha256": sha256(
                json.dumps(copy, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
            "checked_surfaces": len(texts), "numeric_bindings": len(bindings),
            "publication_authority": False, "jim_approval_required": False,
            "standing_approval": "JIM_DECISION_36",
            "final_native_render_review_required": True}


def check_source_bound_event_article(article: Mapping[str, Any], source_pack) -> dict[str, Any]:
    """Resolve numeric refs from the actual admitted writer packet, never writer facts.

    A ref is SOURCE_n:start:end in the source's exact canonical text. Rights,
    source clocks and hashes come from that admitted document. This reuses the
    existing source and event guards rather than requiring a second admission.
    """
    documents = {d["source_id"]: d for d in source_pack}
    facts = {}
    for binding in article.get("numeric_bindings", []):
        ref = binding.get("evidence_ref", "")
        match = re.fullmatch(r"(SOURCE_\d+):(\d+):(\d+)", ref)
        if not match or match[1] not in documents:
            _fail("SOURCE_BOUND_EVENT_REF_REQUIRED", "numeric_bindings")
        doc = documents[match[1]]
        if doc.get("public_claim_allowed") is False:
            _fail("SOURCE_BOUND_EVENT_PUBLIC_RIGHTS_REQUIRED", "numeric_bindings")
        text = doc["canonical_content_text"]
        start, end = int(match[2]), int(match[3])
        if (not 0 <= start < end <= len(text)
                or sha256(text.encode()).hexdigest() != doc["canonical_content_sha256"]):
            _fail("SOURCE_BOUND_EVENT_BYTES_CHANGED", "numeric_bindings")
        constraints = doc.get("source_reuse_constraints") or {}
        scope = constraints.get("scope", "")
        authority = doc.get("source_authority_class", "")
        if scope.startswith("SINGLE_ATTRIBUTED_CONSENSUS_FACT"):
            rights = CITED_FACT
        elif authority == "governed_capital_chronicle_report_only":
            rights = MODEL_ESTIMATE
        elif (authority == "official_release_history_from_cc010"
                or (authority == "official_public_primary_source"
                    and (scope.startswith("BLS_")
                         or scope == "AGENCY_AUTHORED_TEXT_ONLY_EXCLUDES_LOGOS_PHOTOS_THIRD_PARTY"
                         or constraints.get("public_expression_reuse_allowed") is True))):
            rights = "PUBLIC_DOMAIN_OFFICIAL_FACT"
        else:
            _fail("SOURCE_BOUND_EVENT_PUBLIC_RIGHTS_REQUIRED", "numeric_bindings")
        known = doc.get("known_at_utc") or doc.get("published_at_utc")
        fact = {"display": text[start:end], "source_ref": doc.get("url") or doc.get("source_url"),
            "source_sha256": doc["canonical_content_sha256"], "known_at_utc": known,
            "rights_class": rights, "public_use_allowed": True, "use_label": "PUBLIC",
            "rights_evidence_ref": (constraints.get("authority_ref") or constraints.get("policy_capture_sha256")
                                   or constraints.get("source_capture_sha256"))}
        if rights == CITED_FACT:
            fact.update(attribution=doc["publisher"],
                        cited_on=_time(known, ref).astimezone(ZoneInfo("America/New_York")).date().isoformat())
        if rights == MODEL_ESTIMATE:
            fact["estimate_label"] = MODEL_ESTIMATE_LABEL
        facts[ref] = fact
    evidence = {"schema_version": EVIDENCE_SCHEMA, "event_id": article["event_id"],
                "facts": facts, "private_text": []}
    return check_public_event_article(article, evidence=evidence)


def _load(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("DUPLICATE_JSON_KEY", "input")
            result[key] = value
        return result
    def constant(_value):
        _fail("NONFINITE_JSON_VALUE", "input")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--evidence-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        raw = args.evidence.read_bytes()
        if sha256(raw).hexdigest() != args.evidence_sha256:
            _fail("EVIDENCE_BYTES_MISMATCH", "evidence")
        report = check_public_event_article(_load(args.article.read_bytes()), evidence=_load(raw))
        report["evidence_sha256"] = sha256(raw).hexdigest()
        print(json.dumps(report, sort_keys=True))
        return 0
    except PublicOutputError as exc:
        print(json.dumps({"status": "REFUSED", "cause": exc.cause, "location": exc.location,
                          "publication_authority": False}))
    except (OSError, ValueError, TypeError):
        # Input exceptions may contain private text or local paths; never echo them.
        print(json.dumps({"status": "REFUSED", "cause": "INPUT_UNREADABLE_OR_INVALID",
                          "publication_authority": False}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
