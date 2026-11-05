"""Reference projection and checks for the CC-014 desk-record export (schema v1).

Every reader applies ``project`` before showing anything: ``project(doc, {"public"})`` for free
surfaces, ``project(doc, {"public", "pro"})`` for Pro surfaces. Validate the document against its
``schemas/publication/CapitalChronicleDeskRecordExportV1*.schema.json`` first; the schema cannot see
cross-references, so the projection also drops any Field that cites a private-only source.

This file is the canonical projection copy (CC-262): Codex Web's and Publisher's copies are regenerated
from it. Jim's decision 72 b: ``check_public_text`` blocks only DEMO and execution identifiers, bulk raw
third-party data and secrets. It never fails on a cited price, move or yield, on a consensus figure with
its source, or on a Capital Chronicle model level.
"""

from __future__ import annotations

import re
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from datetime import datetime
from typing import Any, Iterable, Iterator

SCHEMA_NAME = "CapitalChronicleDeskRecordExportV1"
FIELD_KEYS = frozenset(
    {"value", "rights_class", "visibility", "use_label", "source_ids"}
)
RECORD_LISTS = (
    "asset_dossiers",
    "event_cards",
    "decision_records",
    "calendar_entries",
    "reports",
    "data_series",
)
# Must equal the schema's PrivateOnlyField enum; tests/test_desk_record_export_schema_v1.py checks it.
PRIVATE_ONLY_RIGHTS = frozenset(
    {
        "DEMO_DERIVED_PRIVATE",
        "MARKET_CONSENSUS_PRIVATE_ONLY",
        "OPTIONS_GEX_PRIVATE_ONLY",
        "DERIVED_FROM_PRIVATE_ONLY",
        "RIGHTS_MISSING",
        "FRED_SOURCE_RIGHTS_BLOCKED",
        "BROKER_PROXY_RAW_PRIVATE",
        "INTERNAL_PROVENANCE",
        "CODEX_DIGEST_INTERNAL",
        "OFFICIAL_SOURCE_CONTRACT_PENDING",
    }
)
# Jim's decision 72 b (CC-262): our computed outputs are public as Capital Chronicle model estimates with decision
# 40's notices; a consensus figure is public only as one cited fact with its source and date.
MODEL_ESTIMATE = "CC_MODEL_ESTIMATE"
CITED_FACT = "CITED_THIRD_PARTY_FACT"
MODEL_ESTIMATE_LABEL = "Capital Chronicle model estimate"
MODEL_ESTIMATE_NOTICES = ("Analysis, not financial advice.",
                          "Capital Chronicle may hold positions in the markets it covers.")
_DROP = object()
CALL_FIELDS = ("condition", "trigger", "invalidation_level")
_CLOCK_KEYS = (
    "known_at_utc",
    "generated_at_utc",
    "decided_at_utc",
    "updated_at_utc",
    "release_known_at_utc",
)


def is_field(node: Any) -> bool:
    return isinstance(node, dict) and FIELD_KEYS <= node.keys()


def iter_fields(node: Any, path: str = "$") -> Iterator[tuple[str, dict[str, Any]]]:
    if is_field(node):
        yield path, node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from iter_fields(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_fields(value, f"{path}[{index}]")


def iter_records(doc: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for name in RECORD_LISTS:
        yield from doc[name]


def _blocked_sources(doc: dict[str, Any]) -> set[str]:
    return {
        s["source_id"]
        for s in doc["sources"]
        if s["rights_class"] in PRIVATE_ONLY_RIGHTS
    }


def _project(node: Any, allowed: frozenset[str], blocked: set[str]) -> Any:
    if is_field(node):
        if node["visibility"] not in allowed or blocked & set(node["source_ids"]):
            return _DROP
        return {key: value for key, value in node.items() if key != "missing_cause"}
    if isinstance(node, dict):
        kept = {key: _project(value, allowed, blocked) for key, value in node.items()}
        kept = {key: value for key, value in kept.items() if value is not _DROP}
        if any(True for _ in iter_fields(node)) and not any(
            True for _ in iter_fields(kept)
        ):
            return _DROP
        return kept
    if isinstance(node, list):
        return [
            value
            for value in (_project(item, allowed, blocked) for item in node)
            if value is not _DROP
        ]
    return node


def _is_conditioned_call(record: dict[str, Any]) -> bool:
    condition = record.get("condition", {}).get("value")
    return (record.get("call", {}).get("value") in {"WATCH", "EXPRESS"}
            and record.get("direction", {}).get("value") in {"BULLISH", "BEARISH"}
            and isinstance(condition, str) and bool(condition.strip()))


def project(doc: dict[str, Any], allowed: Iterable[str]) -> dict[str, Any]:
    """Return only what a surface showing ``allowed`` visibilities may show.

    A Field is kept when its visibility is allowed and it cites no private-only source; a kept Field
    loses ``missing_cause``. A container that held Fields and keeps none is dropped whole. Only the
    sources that kept Fields cite remain.
    """
    allowed = frozenset(allowed)
    if not allowed <= {"public", "pro"}:
        raise ValueError("a surface may show only public and pro Fields")
    blocked = _blocked_sources(doc)
    out: dict[str, Any] = {
        key: doc[key]
        for key in (
            "schema",
            "schema_version",
            "export_id",
            "generated_at_utc",
            "fixture",
        )
    }
    for name in RECORD_LISTS:
        out[name] = _project(doc[name], allowed, blocked)
    for record in out["decision_records"]:
        # Rights/source filtering can remove the condition after the producer has
        # admitted a call. Never leave its direction or levels public on their own.
        if record.get("call", {}).get("value") not in {"ABSTAIN", "NO_TRADE", "HOLD"} and not _is_conditioned_call(record):
            if record.get("call", {}).get("value") in {"WATCH", "EXPRESS"}:
                record.pop("summary", None)
            for key in ("call", "direction", "horizon_days", *CALL_FIELDS):
                record.pop(key, None)
            record.get("analytical_outcome", {}).pop("scored_move", None)
    for dossier in out["asset_dossiers"]:
        # The same rule for a dossier's newest call (CC-262): no direction or level without its shown condition.
        analysis = dossier.get("maintained_analysis")
        call = analysis.get("conditional_call") if isinstance(analysis, dict) else None
        if isinstance(call, dict) and not _is_conditioned_call(call):
            analysis.pop("conditional_call")
    cited = {
        sid
        for _, field in iter_fields({name: out[name] for name in RECORD_LISTS})
        for sid in field["source_ids"]
    }
    out["sources"] = [
        source for source in doc["sources"] if source["source_id"] in cited
    ]
    return out


def _t(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_references(doc: dict[str, Any]) -> list[str]:
    """Cross-references the schema cannot see. Returns problems; empty means sound."""
    problems: list[str] = []
    record_ids = [record["record_id"] for record in iter_records(doc)]
    if len(record_ids) != len(set(record_ids)):
        problems.append("duplicate record_id")
    sources = {source["source_id"] for source in doc["sources"]}
    if len(sources) != len(doc["sources"]):
        problems.append("duplicate source_id")
    for path, field in iter_fields({name: doc[name] for name in RECORD_LISTS}):
        missing = set(field["source_ids"]) - sources
        if missing:
            problems.append(f"{path}: unknown source {sorted(missing)}")
    assets = {record["asset_id"] for record in doc["asset_dossiers"]}
    events = {record["event_id"] for record in doc["event_cards"]} | {
        record["event_id"] for record in doc["calendar_entries"]
    }
    decisions = {record["record_id"] for record in doc["decision_records"]}
    for dossier in doc["asset_dossiers"]:
        for event_id in dossier["event_ids"]:
            if event_id not in events:
                problems.append(f"{dossier['record_id']}: unknown event {event_id}")
        for decision_id in dossier["decision_ids"]:
            if decision_id not in decisions:
                problems.append(
                    f"{dossier['record_id']}: unknown decision {decision_id}"
                )
        update_ids = [entry["update_id"] for entry in dossier["update_log"]]
        if len(update_ids) != len(set(update_ids)):
            problems.append(f"{dossier['record_id']}: duplicate update_id")
    for card in doc["event_cards"]:
        for asset_id in card["asset_ids"]:
            if asset_id not in assets:
                problems.append(f"{card['record_id']}: unknown asset {asset_id}")
    for record in doc["decision_records"]:
        if record["asset_id"] not in assets:
            problems.append(f"{record['record_id']}: unknown asset")
        if record["event_id"] is not None and record["event_id"] not in events:
            problems.append(f"{record['record_id']}: unknown event")
    for report in doc["reports"]:
        for section in report["sections"]:
            for cite in section["cites"]:
                if cite not in set(record_ids):
                    problems.append(f"{report['record_id']}: unknown cite {cite}")
    for series in doc["data_series"]:
        periods = [point["period"] for point in series["observations"]["value"]]
        if periods != sorted(set(periods)):
            problems.append(f"{series['record_id']}: periods not unique and ascending")
        if periods and (periods[0], periods[-1]) != (
            series["window"]["start"],
            series["window"]["end"],
        ):
            problems.append(
                f"{series['record_id']}: window is not the first and last period"
            )
    return problems


def check_clocks(doc: dict[str, Any]) -> list[str]:
    """No clock after the export; no record known before any source it cites."""
    problems: list[str] = []
    generated = _t(doc["generated_at_utc"])
    known = {
        source["source_id"]: _t(source["known_at_utc"])
        if source["known_at_utc"]
        else None
        for source in doc["sources"]
    }
    for source_id, clock in known.items():
        if clock and clock > generated:
            problems.append(f"{source_id}: known after the export")
    for record in iter_records(doc):
        for key in _CLOCK_KEYS:
            if record.get(key) and _t(record[key]) > generated:
                problems.append(f"{record['record_id']}.{key}: after the export")
        anchor = record.get("known_at_utc") or record.get("generated_at_utc")
        if not anchor:
            continue
        anchor_t = _t(anchor)
        for entry in record.get("update_log", []):
            if _t(entry["at_utc"]) > anchor_t:
                problems.append(
                    f"{record['record_id']}: update {entry['update_id']} after the record"
                )
        for path, field in iter_fields(record):
            for source_id in field["source_ids"]:
                if known.get(source_id) and known[source_id] > anchor_t:
                    problems.append(
                        f"{record['record_id']} {path}: cites {source_id} known later"
                    )
    return problems


# A numeral in text: thousands separators, a sign and an R suffix (R multiples) are recognised; a year, date, clock or
# identifier (digits joined to letters, "-", ":" or "/") is not a numeral here.
_NUMERAL = re.compile(r"(?<![\w.,:/-])[-+\u2212]?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![0-9A-QS-Za-z_,:/-]|\.\d)(\s?R\b)?")
REFORMATTED_MIN_SIGNIFICANT = 4


def _significant(value: Decimal) -> int:
    digits = format(abs(value), "f").replace(".", "").lstrip("0")
    return len(digits) or 1


def _places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _numerals(text: str) -> Iterator[tuple[Decimal, int, bool]]:
    """(absolute value, decimal places as written, written as an R multiple) for each numeral in ``text``."""
    for match in _NUMERAL.finditer(text):
        raw = match.group(1).replace(",", "")
        yield abs(Decimal(raw)), _places(Decimal(raw)), bool(match.group(2))


def _number(value: Any) -> Decimal | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return abs(Decimal(repr(value)))
    return None


def _execution_numbers(doc: dict[str, Any]) -> list[tuple[Decimal, bool, str]]:
    """DEMO execution values matched by value in public text: (absolute value, matched only as an R multiple, kind).

    Planned risk and DEMO results in R, matched only as R multiples, so an official 0.8% is never refused for a -0.8R
    result. A plan's levels, cited prices, model levels and consensus figures are never matched by value (decision
    72 b): "model support 6,812.5" passes even when a private plan holds 6812.5. The producer keeps a run's own
    profit target out of the analysis it publishes (decision 40; desk_record_analysis_v1)."""
    numbers: list[tuple[Decimal, bool, str]] = []
    for dossier in doc["asset_dossiers"]:
        plans = list(dossier.get("open_plans") or [])
        analysis = dossier.get("maintained_analysis")
        if isinstance(analysis, dict) and isinstance(analysis.get("plan_levels"), dict):
            plans.append(analysis["plan_levels"])
        for plan in plans:
            for key, field in plan.items():
                if not is_field(field) or field["rights_class"] not in PRIVATE_ONLY_RIGHTS:
                    continue
                number = _number(field["value"])
                if number and key.endswith("_r"):
                    numbers.append((number, True, "R value"))
    for record in doc["decision_records"]:
        number = _number(((record.get("demo") or {}).get("result_r") or {}).get("value"))
        if number:
            numbers.append((number, True, "DEMO result"))
    return numbers


# Raw third-party rows that stay private (decision 72 b, host rule 7): a public text that copies a run of their values
# is bulk raw data. One cited figure, or a few, never is.
RAW_ROW_CLASSES = frozenset({"MARKET_CONSENSUS_PRIVATE_ONLY", "OPTIONS_GEX_PRIVATE_ONLY", "BROKER_PROXY_RAW_PRIVATE",
                             "FRED_SOURCE_RIGHTS_BLOCKED", "RIGHTS_MISSING"})
BULK_MIN_VALUES = 4
# Numbers in a pasted list or table ("63.0, 4.2, 0.3"): a comma followed by three digits is a thousands separator.
_LISTED = re.compile(r"(?<![\w.])[-+−]?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?!\d)")


def _values(node: Any) -> Iterator[Decimal]:
    number = _number(node)
    if number is not None:
        yield number
    elif isinstance(node, dict):
        for value in node.values():
            yield from _values(value)
    elif isinstance(node, list):
        for value in node:
            yield from _values(value)


def _raw_tables(doc: dict[str, Any]) -> dict[tuple[str, str], set[Decimal]]:
    """Numeric values held in private raw rows, by (dataset, provider): one table or series per source."""
    owners = {s["source_id"]: (s["dataset"], s["provider"]) for s in doc["sources"]
              if s["rights_class"] in RAW_ROW_CLASSES}
    tables: dict[tuple[str, str], set[Decimal]] = {}
    for _, field in iter_fields({name: doc[name] for name in RECORD_LISTS}):
        if field["rights_class"] not in PRIVATE_ONLY_RIGHTS:
            continue
        for owner in {owners[s] for s in field["source_ids"] if s in owners}:
            tables.setdefault(owner, set()).update(v for v in _values(field["value"]) if _significant(v) >= 2)
    return tables


# DEMO account identities (host AGENTS.md standing facts): the J1 DEMO account and the 26 Oct cost-sample account,
# both on the DEMO server. Matched by value anywhere in public text; callers may add more.
DEMO_ACCOUNT_LOGINS = frozenset({"279805139", "279779602"})
# DEMO and execution identifiers by name (decision 40, host rule 7): login, server, balance, lots, tickets, fills,
# USD P&L, order levels and R multiples.
EXECUTION_TERMS = (
    ("DEMO account", re.compile(r"\b(?:login|account\s*(?:no\.?|number|id|#)?|acct)\s*[:#]?\s*\d{6,}\b", re.I)),
    ("DEMO account", re.compile(r"\bdemo\s+(?:account|login|server|balance|equity|book|portfolio|positions?|orders?|"
                                r"trades?|fills?|p&l|pnl|results?)\b", re.I)),
    ("broker server", re.compile(r"\b(?:exness[\w-]*|mt5\s*trial\d*|metatrader\s*\d?|mt[45])\b", re.I)),
    # A macro "current account balance" or "trade balance" is not an account balance.
    ("account balance", re.compile(r"\b(?:demo|book|portfolio)\s+(?:account\s+)?(?:balance|equity|margin)\b|"
                                   r"\baccount\s+(?:balance|equity)\b(?<!current account balance)"
                                   r"(?<!capital account balance)(?<!financial account balance)|"
                                   r"\bfree\s+margin\b|\bmargin\s+level\b", re.I)),
    ("lot size", re.compile(r"(?<![\w.])\d+(?:\.\d+)?\s*(?:standard\s+|mini\s+|micro\s+)?lots?\b|\blot\s+sizes?\b",
                            re.I)),
    ("ticket", re.compile(r"\b(?:ticket|deal|order|position)\s*(?:id|no\.?|number|#)?\s*[:#]?\s*\d{5,}\b", re.I)),
    ("fill", re.compile(r"\b(?:fill(?:ed)?\s+(?:at|price)|fills?\s+(?:at|of)|execution\s+price|executed\s+at|"
                        r"entry\s+fill)\b", re.I)),
    # A small dollar P&L ("$123.45 profit"); a company's "$5 billion loss" or "unrealized losses" is not one.
    ("USD P&L", re.compile(r"\b(?:p&l|pnl|p/l)\b|(?:US\$|\$)\s?[-+−]?\d[\d,]*(?:\.\d+)?\s*(?:profit|loss|gain)\b",
                           re.I)),
    ("order level", re.compile(r"\b(?:stop[- ]loss|take[- ]profit|profit[- ]target|tp|sl)\b\s*(?:at|of|level|is|was|"
                               r"[:=])?\s*[-+]?\d", re.I)),
    ("R multiple", re.compile(r"(?<![\w.])[-+\u2212]?\d+(?:\.\d+)?\s?R\b|\bR\s*[:/]\s*R\b")),
    # Position sizes stay off public content (decision 40): the DEMO size tier and risk as a share of the account.
    ("position size", re.compile(r"\bSTARTER\b|(?i:\b(?:risk|size)\s+tier\b|\bposition\s+siz(?:e|es|ing)\b|"
                                 r"\d+(?:\.\d+)?\s*%\s+of\s+(?:equity|the\s+book|the\s+account|account|balance|capital)\b|"
                                 r"\bplanned\s+(?:loss|risk)\b)")),
)
# A raw option-chain row: a strike (or "6800C") with its open interest or implied volatility and numbers. A modelled
# regime, flip or wall level is not one.
OPTION_ROW = (re.compile(r"\bstrikes?\b|\b\d{3,5}\s?[CP]\b", re.I),
              re.compile(r"\bopen\s+interest\b|\bimplied\s+vol(?:atility)?\b|\b(?:OI|IV)\b"))
PREDICTION_MARKETS = re.compile(r"\b(?:kalshi|polymarket|predictit|prediction[- ]markets?|betting\s+markets?)\b", re.I)
# Odds written as a number: 62%, 62 cents, 0.62, "odds of 3", "2 in 3". A date or release name beside a market is not.
ODDS = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent\b|per\s+cent\b|cents?\b|¢)|\bodds\s+(?:of|at)\s+\d|"
                  r"\b\d+\s*(?:in|out\s+of)\s+\d+\b|(?<![\w.])0?\.\d+\b", re.I)
SECRETS = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{30,}\b|"
    r"\bgithub_pat_[A-Za-z0-9_]{30,}\b|\bxox[abprs]-[A-Za-z0-9-]{10,}\b|\bsk-[A-Za-z0-9_-]{20,}\b|"
    r"\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|"
    r"\b(?:api[_ -]?key|secret|access[_ -]?token|token|password|passwd|bearer)\b\s*[:=]\s*\S{6,}", re.I)


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?;])\s+|\n", text) if s.strip()]


def public_text_problems(text: str, *, execution: Iterable[tuple[Decimal, bool, str]] = (),
                         raw_tables: dict[tuple[str, str], set[Decimal]] | None = None,
                         demo_identity: Iterable[str] = ()) -> list[str]:
    """What decision 72 b refuses in one public text: DEMO and execution identifiers (by name and by value), bulk raw
    third-party data and secrets. Empty means the text may be shown."""
    problems: list[str] = []
    for value in sorted(DEMO_ACCOUNT_LOGINS | {str(v) for v in demo_identity if str(v).strip()}):
        if re.search(r"(?<![\w.])" + re.escape(value) + r"(?![\w])", text):
            problems.append("DEMO or execution identifier (DEMO identity value)")
    for kind, pattern in EXECUTION_TERMS:
        if pattern.search(text):
            problems.append("DEMO or execution identifier (%s)" % kind)
    written = list(_numerals(text))
    for number, r_only, kind in execution:
        if any(_matches(number, r_only, w, places, as_r) for w, places, as_r in written):
            problems.append("DEMO or execution identifier (%s %s)" % (kind, number))
    shown = {abs(Decimal(m.group(1).replace(",", ""))) for m in _LISTED.finditer(text)}
    shown = {w for w in shown if _significant(w) >= 2}
    for (dataset, provider), values in sorted((raw_tables or {}).items()):
        if len(shown & values) >= BULK_MIN_VALUES:
            problems.append("bulk raw third-party data (%s, %s)" % (dataset, provider))
    if OPTION_ROW[0].search(text) and OPTION_ROW[1].search(text) and len(written) >= 2:
        problems.append("bulk raw third-party data (option-chain row)")
    for sentence in _sentences(text):
        if PREDICTION_MARKETS.search(sentence) and ODDS.search(sentence):
            problems.append("bulk raw third-party data (prediction-market number)")
            break
    if SECRETS.search(text):
        problems.append("secret")
    return sorted(set(problems))


def _matches(private: Decimal, r_only: bool, written: Decimal, places: int, as_r: bool) -> bool:
    """Whether a numeral written in text states a private value.

    Exactly, after separators, sign and suffix are stripped. Reformatted (rounded half-up or truncated to 0-4 decimals),
    only while it keeps at least REFORMATTED_MIN_SIGNIFICANT significant digits and, for a private value with decimals,
    at least one decimal: 2412.35 as 2412.4 is refused, while an official 4.68 beside a private 4.6812, or a whole 2412,
    is not (those shorter forms collide with ordinary public levels). An R value matches only as an R multiple."""
    if r_only and not as_r:
        return False
    if written == private:
        return True
    if places > 4 or places >= _places(private):
        return False
    if not r_only and (_significant(written) < REFORMATTED_MIN_SIGNIFICANT or (_places(private) and places == 0)):
        return False
    step = Decimal(1).scaleb(-places)
    return written in {private.quantize(step, rounding=ROUND_HALF_UP), private.quantize(step, rounding=ROUND_DOWN)}


def public_text_context(doc: dict[str, Any]) -> dict[str, Any]:
    """The document-wide inputs of ``public_text_problems``."""
    return {"execution": _execution_numbers(doc), "raw_tables": _raw_tables(doc)}


def check_public_text(
    doc: dict[str, Any], allowed: Iterable[str] = ("public",), demo_identity: Iterable[str] = ()
) -> list[str]:
    """Producer rule on what a surface will show (Jim's decision 72 b): no DEMO or execution identifier, matched by
    name and by value (login, server, balance, lots, tickets, fills, USD P&L, order levels named as such, R
    multiples), no bulk raw third-party data (a run of values from one private table or series, an option-chain
    row, a prediction-market number) and no secret. Cited prices, moves and yields, a consensus figure with its
    source, and Capital Chronicle model levels in any wording pass, whatever private value they equal."""
    projected = project(doc, allowed)
    context = {**public_text_context(doc), "demo_identity": tuple(demo_identity)}
    problems: list[str] = []
    for path, field in iter_fields({name: projected[name] for name in RECORD_LISTS}):
        if isinstance(field["value"], str):
            problems += [f"{path}: {problem}" for problem in public_text_problems(field["value"], **context)]
    return problems
