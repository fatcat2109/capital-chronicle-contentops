"""Reference projection and checks for the CC-014 desk-record export (schema v1).

Every reader applies ``project`` before showing anything: ``project(doc, {"public"})`` for free
surfaces, ``project(doc, {"public", "pro"})`` for Pro surfaces. Validate the document against
``schemas/publication/CapitalChronicleDeskRecordExportV1.schema.json`` first; the schema cannot see
cross-references, so the projection also drops any Field that cites a private-only source.
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
# Producer rule: public and Pro text never states a consensus-relative judgement or a trading level.
PRIVATE_TERMS = re.compile(
    r"\b(consensus|forecast(?:s|ed)?|in line with|beat(?:s)?|miss(?:ed|es)?|surprise(?:d|s)?|gex|gamma|"
    r"stop[- ]loss|take[- ]profit|armed)\b",
    re.IGNORECASE,
)
_DROP = object()
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


def _private_numbers(doc: dict[str, Any]) -> list[tuple[Decimal, bool]]:
    """Private values to keep out of public text: (absolute value, matched only as an R multiple).

    Numeric private-only Fields of three or more significant digits; DEMO results and R values (keys ending in
    ``_r`` or naming a result) at any digit count, matched as R multiples below three digits so an official 0.8% is
    never refused for a -0.8R result; and the decimal numbers of three or more significant digits written inside
    private-only string Fields (an "entry reference 157.695" in a rationale), which earlier went uncollected."""
    numbers: list[tuple[Decimal, bool]] = []
    for path, field in iter_fields({name: doc[name] for name in RECORD_LISTS}):
        value = field["value"]
        if field["rights_class"] not in PRIVATE_ONLY_RIGHTS:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = abs(Decimal(repr(value)))
            key = path.rsplit(".", 1)[-1]
            r_value = key.endswith("_r") or (field["rights_class"] == "DEMO_DERIVED_PRIVATE" and "result" in key)
            if _significant(number) >= 3:
                numbers.append((number, False))
            elif r_value and number:
                numbers.append((number, True))
        elif isinstance(value, str):
            numbers.extend((number, False) for number, places, _ in _numerals(value)
                           if places >= 1 and _significant(number) >= 3)
    return numbers


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


def check_public_text(
    doc: dict[str, Any], allowed: Iterable[str] = ("public",)
) -> list[str]:
    """Producer rule on what a surface will show: no consensus or trading terms, no private provider
    names, and no private number of three or more significant digits."""
    projected = project(doc, allowed)
    vendor_classes = {
        "MARKET_CONSENSUS_PRIVATE_ONLY",
        "RIGHTS_MISSING",
        "FRED_SOURCE_RIGHTS_BLOCKED",
        "BROKER_PROXY_RAW_PRIVATE",
    }
    providers = {
        s["provider"] for s in doc["sources"] if s["rights_class"] in vendor_classes
    }
    numbers = _private_numbers(doc)
    problems: list[str] = []
    for path, field in iter_fields({name: projected[name] for name in RECORD_LISTS}):
        if not isinstance(field["value"], str):
            continue
        text = field["value"]
        if PRIVATE_TERMS.search(text):
            problems.append(f"{path}: private term")
        for provider in providers:
            if provider.split(" ")[0].lower() in text.lower():
                problems.append(f"{path}: private provider {provider}")
        for number, r_only in numbers:  # numerals compared as numbers, not strings (CC-045's check, 31 Oct)
            if any(_matches(number, r_only, written, places, as_r) for written, places, as_r in _numerals(text)):
                problems.append(f"{path}: private number {number}")
    return problems
