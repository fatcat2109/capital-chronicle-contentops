"""Offline public-copy checks for CC-107 event previews and reviews.

Evidence is a separately pinned admission from the existing source/rights owner,
never a permission supplied by the article. This checker grants no publication
authority and performs no model, transport, store or scheduler operation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping


SCHEMA = "contentops.event_article.v1"
EVIDENCE_SCHEMA = "contentops.event_article_evidence.v1"
DISCLAIMER = "This is general market analysis, not financial advice."
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
_ROOT_KEYS = {"schema_version", "article_type", "event_id", "event_time_utc",
              "cutoff_utc", "written_at_utc", "copy", "numeric_bindings"}
_SHA = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_KEY = re.compile(
    r"(?:^|_)(?:entries|entry|stop|stops|sl|stoploss|takeprofit|tp|targets?|"
    r"sizes?|sizing|lots?|volume|account|demo|mt5|positions?|holdings?|"
    r"balances?|equity|pnl|profit|loss|fills?|orders?|tickets?)(?:_|$)"
)
_PRIVATE_TEXT = re.compile(
    r"\b(?:demo|mt5|stop[ -]?loss|take[ -]?profit|entry price|entry level|"
    r"position siz(?:e|ing)|account (?:id|number|balance|equity)|"
    r"portfolio (?:positions?|results?|returns?)|our (?:positions?|holdings?)|"
    r"p\s*&\s*l|lots?)\b|(?<!\w)[+-]?\d+(?:\.\d+)?\s*r\b", re.I
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


class PublicOutputError(ValueError):
    """A cause and copy location only: never echo private input in diagnostics."""

    def __init__(self, cause: str, location: str):
        self.cause, self.location = cause, location
        super().__init__(cause)


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
    """
    if not isinstance(article, Mapping):
        _fail("ARTICLE_OBJECT_REQUIRED", "article")
    _private_keys(article)
    if set(article) != _ROOT_KEYS or article.get("schema_version") != SCHEMA:
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
    if not isinstance(copy, Mapping) or set(copy) != SECTIONS[kind]:
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
    for path, value in texts.items():
        text = _text(value)
        # Formatting is not a route around an execution/private-content refusal.
        scan = re.sub(r"[`*_]", "", text)
        if not text.strip():
            _fail("EMPTY_EVENT_SECTION", path)
        if _PRIVATE_TEXT.search(scan) or _INSTRUCTION.search(scan):
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
        display = _fact(evidence["facts"].get(binding["evidence_ref"]), cutoff, event_time, location)
        # Exact wording, precision, sign and unit remain source-owned. Only Unicode
        # presentation and digit grouping may differ; numbers are never inferred.
        if _display_text(surface) != _display_text(display) or not _numbers(surface):
            _fail("SOURCE_DISPLAY_MISMATCH", location)
        if any(start < b and a < end for a, b in coverage[path]):
            _fail("OVERLAPPING_NUMERIC_BINDINGS", location)
        coverage[path].append((start, end))
    for path, text in texts.items():
        # Work on original offsets; normalisation above must not move span bounds.
        normalized = _text(text)
        if len(normalized) != len(text) and _numbers(text):
            _fail("NUMERIC_TEXT_REQUIRES_PLAIN_UNICODE", path)
        for match in _NUMBER.finditer(normalized):
            start, end = match.span()
            end = len(normalized[:end].rstrip())
            if not any(a <= start and end <= b for a, b in coverage[path]):
                _fail("UNBOUND_PUBLIC_NUMBER", path)
    return {"status": "PASS", "public_copy_sha256": sha256(
                json.dumps(copy, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest(),
            "checked_surfaces": len(texts), "numeric_bindings": len(bindings),
            "publication_authority": False, "jim_approval_required": True,
            "final_native_render_review_required": True}


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
