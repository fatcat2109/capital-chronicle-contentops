"""Reference projection and checks for the CC-014 desk-record export (schema v1).

Every reader applies ``project`` before showing anything: ``project(doc, {"public"})`` for free
surfaces, ``project(doc, {"public", "pro"})`` for Pro surfaces. Validate the document against
``schemas/publication/CapitalChronicleDeskRecordExportV1.schema.json`` first; the schema cannot see
cross-references, so the projection also drops any Field that cites a private-only source.
"""

from __future__ import annotations

import re
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


def _private_numbers(doc: dict[str, Any]) -> set[str]:
    numbers: set[str] = set()
    for _, field in iter_fields({name: doc[name] for name in RECORD_LISTS}):
        value = field["value"]
        if (
            field["rights_class"] in PRIVATE_ONLY_RIGHTS
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            digits = re.sub(r"[^0-9]", "", f"{abs(value):.10g}").strip("0")
            if len(digits) >= 3:
                numbers.add(f"{abs(value):.10g}")
    return numbers


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
        for number in numbers:
            if number in text:
                problems.append(f"{path}: private number {number}")
    return problems
