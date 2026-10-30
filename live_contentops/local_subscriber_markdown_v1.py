"""Four deterministic subscriber formats; local files and the existing outbox only.

This module has no transport, browser, model or runtime activation path. It reads the
upstream publication allowlist as data, never imports or executes Main's runtime.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
from string import Formatter
import tempfile
from typing import Any, Mapping

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.idempotency_policy import compute_idempotency_key


SCHEMA = "contentops.local_subscriber_piece.v1"
VERSION = "local_subscriber_markdown_v1"
FORMATS = ("event_card", "auto_delta", "saturday_ledger", "week_ahead")
_FIELD = re.compile(r"^[a-z][a-z0-9_]*$")
_PIECE = re.compile(r"^[a-z][a-z0-9-]{0,79}$")
_INSTRUCTION = re.compile(
    r"\b(?:enter|entry|buy|sell|stop[ -]?loss|take[ -]?profit|target|order|lot|position sizing)\b",
    re.I,
)
_UNSAFE = re.compile(
    r"(?:\b(?:FRED|ALFRED|VIXCLS)\b|raw[_ -]?(?:broker|mt5|provider)[_ -]?(?:quote|response|table)"
    r"|\b(?:system|developer|user)[_ -]?prompt\b|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|\bBearer\s|<[^>]*>)",
    re.I,
)


class RenderError(ValueError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class SubscriberPolicy:
    fields: frozenset[str]
    contracts: tuple[dict[str, Any], ...]
    source_sha256: str
    version: str

    @classmethod
    def from_source(cls, path: Path) -> "SubscriberPolicy":
        """Read Main's literal contracts without executing code or loading runtime state."""
        raw = path.read_bytes()
        tree = ast.parse(raw.decode("utf-8-sig"))
        constants: dict[str, Any] = {}

        def literal(node: ast.AST) -> Any:
            if isinstance(node, ast.Name) and node.id in constants:
                return constants[node.id]
            if isinstance(node, (ast.Tuple, ast.List)):
                values = [literal(item) for item in node.elts]
                return tuple(values) if isinstance(node, ast.Tuple) else values
            if isinstance(node, ast.Dict):
                return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
            return ast.literal_eval(node)

        for node in tree.body:
            names = [n.id for n in node.targets if isinstance(n, ast.Name)] if isinstance(node, ast.Assign) else []
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            if not names:
                continue
            try:
                value = literal(node.value)
            except (ValueError, TypeError, KeyError):
                continue
            constants.update({name: value for name in names})
        try:
            fields = constants["FIELD_ALLOWLIST"]
            contracts = constants["PUBLICATION_SOURCE_RIGHTS_CONTRACTS"]
            version = constants["FIELD_ALLOWLIST_VERSION"]
        except KeyError as exc:
            raise RenderError("SUBSCRIBER_CONTRACT_MISSING") from exc
        if not isinstance(fields, tuple) or not all(isinstance(p, str) for p in fields):
            raise RenderError("SUBSCRIBER_ALLOWLIST_INVALID")
        if not isinstance(contracts, tuple) or not contracts:
            raise RenderError("SUBSCRIBER_RIGHTS_CONTRACT_INVALID")
        return cls(frozenset(fields), contracts, _sha(raw), str(version))

    def source_contract(self, source: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """The upstream contracts own admissible classes; an input tag grants no rights."""
        if source.get("subscriber_or_public_projection_allowed") is False:
            return None
        identity = _json(dict(source)).casefold()
        if any(word in identity for word in ("fred", "alfred", "raw_quote", "quote_table", "raw_tick", "order_book", "market_depth", "raw_provider")):
            return None
        if not isinstance(source.get("source_ref"), str) or not source["source_ref"].strip():
            return None
        provider = str(source.get("provider", "")).strip().casefold()
        dataset = str(source.get("dataset_family", "")).strip().casefold()
        authority = str(source.get("authority_class", "")).strip().casefold()
        for contract in self.contracts:
            if (provider in contract["providers"]
                    and any(dataset.startswith(p) for p in contract["dataset_prefixes"])
                    and authority in contract["allowed_authorities"]):
                return contract
        return None


@dataclass(frozen=True)
class RenderedPiece:
    piece_id: str
    format: str
    markdown: str
    diagnostics: dict[str, Any]


def _plain(value: str) -> str:
    # Single-line plain text only; JSON values cannot introduce HTML, links or new headings.
    text = re.sub(r"[\r\n\t]+", " ", value)
    for char in "\\`*_{}[]<>|#":
        text = text.replace(char, "\\" + char)
    return text


class _Renderer:
    def __init__(self, record: Mapping[str, Any], policy: SubscriberPolicy):
        self.record, self.policy = record, policy
        self.fields = record.get("fields", {})
        self.sources = record.get("sources", {})
        if not isinstance(self.fields, Mapping) or not isinstance(self.sources, Mapping):
            raise RenderError("FIELDS_AND_SOURCES_MUST_BE_OBJECTS")
        self.omissions: list[dict[str, str]] = []
        self.used: dict[str, dict[str, str]] = {}

    def omit(self, location: str, cause: str, field: str = "") -> None:
        item = {"location": location, "cause": cause}
        if field:
            item["field"] = field
        if item not in self.omissions:
            self.omissions.append(item)

    def cell(self, name: str, location: str, *, official: bool = False) -> tuple[str, Mapping[str, Any]] | None:
        cell = self.fields.get(name)
        if not isinstance(cell, Mapping) or cell.get("value") is None:
            self.omit(location, "MISSING_VALUE", name)
            return None
        if not isinstance(cell.get("publication_field"), str) or cell["publication_field"] not in self.policy.fields:
            self.omit(location, "FIELD_NOT_ALLOWLISTED", name)
            return None
        source_id = cell.get("source")
        source = self.sources.get(source_id) if isinstance(source_id, str) else None
        if not isinstance(source, Mapping):
            self.omit(location, "SOURCE_MISSING", name)
            return None
        contract = self.policy.source_contract(source)
        if not contract or cell.get("rights_tag") != contract["source_class"]:
            self.omit(location, "SOURCE_RIGHTS_NOT_ADMITTED", name)
            return None
        if official and (source.get("authority_class") != "official_actual" or cell.get("derivation")):
            self.omit(location, "OFFICIAL_ACTUAL_REQUIRED", name)
            return None
        value = cell["value"]
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            self.omit(location, "SCALAR_VALUE_REQUIRED", name)
            return None
        if isinstance(value, (int, float)):
            try:
                number = Decimal(str(value))
                if not number.is_finite():
                    raise InvalidOperation
                value = format(number, "f").rstrip("0").rstrip(".") if "." in format(number, "f") else format(number, "f")
            except InvalidOperation:
                self.omit(location, "NONFINITE_VALUE", name)
                return None
        value = str(value)
        if len(value) > 4000 or _UNSAFE.search(value) or _INSTRUCTION.search(value):
            self.omit(location, "UNSAFE_OR_EXECUTION_TEXT", name)
            return None
        self.used[name] = {"publication_field": str(cell["publication_field"]), "source": str(cell["source"]), "rights_tag": str(cell["rights_tag"])}
        return _plain(value), cell

    def statement(self, item: Any, location: str, *, official: bool = False) -> str | None:
        if not isinstance(item, Mapping) or not isinstance(item.get("template"), str):
            self.omit(location, "STATEMENT_MISSING")
            return None
        template = item["template"]
        if len(template) > 4000 or _UNSAFE.search(template) or _INSTRUCTION.search(template):
            self.omit(location, "UNSAFE_OR_EXECUTION_TEXT")
            return None
        try:
            parts = list(Formatter().parse(template))
        except ValueError:
            self.omit(location, "TEMPLATE_INVALID")
            return None
        output: list[str] = []
        before = dict(self.used)
        for literal, name, spec, conversion in parts:
            if any(c.isdigit() for c in literal):
                self.omit(location, "UNTAGGED_DIGIT_SENTENCE_DROPPED")
                self.used = before
                return None
            output.append(_plain(literal))
            if name is not None:
                if not _FIELD.fullmatch(name) or spec or conversion:
                    self.omit(location, "TEMPLATE_REFERENCE_INVALID")
                    self.used = before
                    return None
                value = self.cell(name, location, official=official)
                if value is None:
                    self.used = before
                    return None
                output.append(value[0])
        return "".join(output).strip() or None

    def statements(self, values: Any, location: str, *, official: bool = False) -> list[str]:
        if not isinstance(values, list):
            self.omit(location, "SECTION_MISSING")
            return []
        return [text for i, item in enumerate(values) if (text := self.statement(item, f"{location}[{i}]", official=official))]

    def section(self, heading: str, values: Any, location: str, *, missing: str, official: bool = False) -> list[str]:
        text = self.statements(values, location, official=official)
        return [f"## {heading}", "", *(text or [missing]), ""]

    def probability(self, name: Any, location: str) -> str | None:
        value = self.cell(str(name), location)
        if value is None:
            return None
        try:
            number = Decimal(str(value[1]["value"]))
            if value[1].get("unit") != "%" or not number.is_finite() or not 0 <= number <= 100:
                raise InvalidOperation
        except InvalidOperation:
            self.omit(location, "PROBABILITY_PERCENT_INVALID", str(name))
            return None
        return value[0] + "%"

    def render(self) -> RenderedPiece:
        if self.record.get("schema") != SCHEMA or self.record.get("format") not in FORMATS:
            raise RenderError("SCHEMA_OR_FORMAT_INVALID")
        piece_id = self.record.get("piece_id")
        if not isinstance(piece_id, str) or not _PIECE.fullmatch(piece_id):
            raise RenderError("PIECE_ID_INVALID")
        kind = self.record["format"]
        title = self.statement(self.record.get("title"), "title")
        lines = ["# " + (title or kind.replace("_", " ").title()), ""]
        if self.record.get("synthetic_fixture") is True:
            lines += ["*Illustrative fixture only; these are fictional figures, not a market report.*", ""]
        content = self.record.get("content", {})
        if not isinstance(content, Mapping):
            raise RenderError("CONTENT_MUST_BE_OBJECT")
        if kind == "event_card":
            lines += self.section("Before the release", content.get("overview"), "overview", missing="Release context is not available.")
            lines += ["## Scenarios", ""]
            scenarios = content.get("scenarios", [])
            if not isinstance(scenarios, list):
                raise RenderError("SCENARIOS_MUST_BE_LIST")
            probabilities = []
            for i, row in enumerate(scenarios):
                if not isinstance(row, Mapping):
                    raise RenderError("SCENARIO_OBJECT_REQUIRED")
                loc = f"scenarios[{i}]"
                name = self.statement(row.get("name"), loc + ".name")
                condition = self.statement(row.get("condition"), loc + ".condition")
                probability = self.probability(row.get("probability"), loc + ".probability")
                if probability:
                    probabilities.append(Decimal(probability[:-1]))
                if name and condition:
                    lines += [f"### {name}", "", f"Probability: {probability or 'unavailable from the supplied evidence.'}", "", condition, ""]
            if not scenarios:
                self.omit("scenarios", "SCENARIOS_MISSING")
                lines += ["No supported scenario set is available.", ""]
            if scenarios and len(probabilities) == len(scenarios) and sum(probabilities) != 100:
                raise RenderError("SCENARIO_PROBABILITIES_DO_NOT_SUM_TO_PERCENT_WHOLE")
            lines += self.section("What is priced", content.get("priced_in"), "priced_in", missing="No sourced priced-in estimate is available.")
            lines += self.section("Levels of interest", content.get("levels_of_interest"), "levels_of_interest", missing="No supported reference levels are available.")
            lines += self.section("What would invalidate the view", content.get("invalidation"), "invalidation", missing="No supported invalidation is available.")
        elif kind == "auto_delta":
            lines += self.section("Which scenario happened", content.get("matched_scenario"), "matched_scenario", missing="The supplied evidence does not identify a matched scenario.")
            lines += self.section("The official release", content.get("official_numbers"), "official_numbers", official=True, missing="Official figures are not available from an admitted source.")
            lines += self.section("What changed versus pricing", content.get("delta_vs_priced"), "delta_vs_priced", missing="A sourced comparison with prior pricing is unavailable.")
        elif kind == "saturday_ledger":
            lines += ["*DEMO and research outcomes only. Risk units require a documented denominator; no-trade is not a zero-risk return.*", ""]
            entries = content.get("entries", [])
            if not isinstance(entries, list):
                raise RenderError("LEDGER_ENTRIES_MUST_BE_LIST")
            for i, row in enumerate(entries):
                if not isinstance(row, Mapping):
                    raise RenderError("LEDGER_ENTRY_OBJECT_REQUIRED")
                loc = f"entries[{i}]"
                label = self.statement(row.get("label"), loc + ".label")
                cause = self.statement(row.get("cause"), loc + ".cause")
                outcome = self.statement(row.get("outcome"), loc + ".outcome")
                entry_kind = row.get("kind")
                if entry_kind not in {"call", "demo_trade", "loss", "no_trade"}:
                    self.omit(loc, "LEDGER_KIND_INVALID")
                    continue
                lines += [f"## {label or entry_kind.replace('_', ' ').title()}", "", f"Type: {entry_kind.replace('_', ' ')}.", "", outcome or "Outcome is unavailable.", "", cause or "The cause is unavailable.", ""]
                if entry_kind == "no_trade":
                    lines += ["Risk-unit result: not applicable; no risk was allocated.", ""]
                    if row.get("result_r") is not None:
                        self.omit(loc + ".result_r", "NO_TRADE_HAS_NO_REALIZED_R")
                    continue
                result = self.cell(str(row.get("result_r")), loc + ".result_r")
                denominator = self.cell(str(row.get("risk_denominator")), loc + ".risk_denominator")
                valid = False
                if result and denominator:
                    try:
                        r_value = Decimal(str(result[1]["value"]))
                        risk = Decimal(str(denominator[1]["value"]))
                        valid = (result[1].get("unit") == "R" and r_value.is_finite()
                                 and risk.is_finite() and risk > 0
                                 and denominator[1].get("role") == "initial_risk"
                                 and isinstance(denominator[1].get("unit"), str)
                                 and denominator[1]["unit"].strip() not in ("", "R"))
                        if valid and entry_kind == "loss" and r_value >= 0:
                            valid = False
                            self.omit(loc + ".result_r", "LOSS_SIGN_CONFLICT")
                    except InvalidOperation:
                        pass
                if valid:
                    lines += [f"Risk-unit result: {result[0]}R.", ""]
                else:
                    self.omit(loc + ".result_r", "R_OR_POSITIVE_RISK_DENOMINATOR_MISSING")
                    lines += ["Risk-unit result: unavailable; a sourced result and positive risk denominator are required.", ""]
        else:
            events = content.get("events", [])
            if not isinstance(events, list):
                raise RenderError("WEEK_EVENTS_MUST_BE_LIST")
            for i, row in enumerate(events):
                if not isinstance(row, Mapping):
                    raise RenderError("WEEK_EVENT_OBJECT_REQUIRED")
                loc = f"events[{i}]"
                event = self.statement(row.get("event"), loc + ".event")
                time = self.statement(row.get("time"), loc + ".time")
                lines += ["## " + (event or "Event details unavailable"), "", time or "Release time is unavailable.", ""]
                lines += self.section("What is priced", row.get("priced_in"), loc + ".priced_in", missing="No sourced priced-in estimate is available.")
                lines += self.section("What to watch", row.get("watch"), loc + ".watch", missing="The supplied record does not establish a watch condition.")
        # Rights-contract credits are retained; discretionary per-paragraph sources are not added.
        contracts = {str(item["source_class"]): item for item in self.policy.contracts}
        disclaimers = sorted({str(contracts[item["rights_tag"]]["disclaimer"]) for item in self.used.values()})
        if disclaimers:
            lines += [" ".join(disclaimers), ""]
        markdown = "\n".join(lines).rstrip() + "\n"
        return RenderedPiece(piece_id, kind, markdown, {
            "schema": SCHEMA, "renderer_version": VERSION, "format": kind,
            "field_allowlist_version": self.policy.version,
            "publication_contract_sha256": self.policy.source_sha256,
            "used_fields": self.used, "omissions": self.omissions,
            "synthetic_fixture": self.record.get("synthetic_fixture") is True,
            "publication_performed": False, "external_readback_proven": False,
        })


def render_piece(record: Mapping[str, Any], policy: SubscriberPolicy) -> RenderedPiece:
    return _Renderer(record, policy).render()


def _immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise RenderError(f"LOCAL_ARTIFACT_CONFLICT:{path.name}")
        return
    # Publish a fully flushed same-volume file exclusively. A disk/turn interruption
    # never leaves a partially written final artifact, nor overwrites an existing one.
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".local-render-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise RenderError(f"LOCAL_ARTIFACT_CONFLICT:{path.name}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_local_piece(piece: RenderedPiece, output_dir: Path) -> dict[str, Any]:
    """Reuse canonical outbox/readback tables in an isolated local output directory.

    No dispatch adapter/coordinator is instantiated. Local readback is explicitly NOT
    a platform confirmation. Interrupted local file writes resume through the same key.
    """
    output_dir = output_dir.resolve()
    normalized = output_dir.as_posix().casefold()
    if str(output_dir).startswith("\\\\") or "://" in str(output_dir) or any(p in normalized for p in (
        "/capital chronicle/runtime", "/appdata/local/capitalchronicle",
    )):
        raise RenderError("ISOLATED_LOCAL_OUTPUT_REQUIRED")
    markdown = piece.markdown.encode("utf-8")
    diagnostics = (_json(piece.diagnostics) + "\n").encode("utf-8")
    payload_hash = _sha(markdown + b"\0" + diagnostics)
    key = compute_idempotency_key({
        "payload_hash": payload_hash, "platform_id": "local_file_only",
        "payload_class_id": piece.format, "destination_binding_id": output_dir.as_uri(),
        "credential_handle_id": "NOT_APPLICABLE_LOCAL_ONLY", "media_manifest_hash": "NO_MEDIA",
        "policy_snapshot_id": piece.diagnostics["publication_contract_sha256"],
        "approval_ledger_entry_id": "NO_EXTERNAL_APPROVAL_LOCAL_ONLY",
        "approval_event_id": "NO_EXTERNAL_APPROVAL_LOCAL_ONLY", "dispatch_intent_class": "LOCAL_RENDER_ONLY",
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{piece.piece_id}-{key[:12]}.md"
    report = path.with_suffix(".qa.json")
    db_path = output_dir / "local-render-outbox.sqlite3"
    if any(p.resolve().parent != output_dir for p in (path, report, db_path)):
        raise RenderError("LOCAL_OUTPUT_LINK_ESCAPES_DIRECTORY")
    # The existing store also resolves relocation markers. Validate its resolved path
    # before allowing migrations, so a local alias cannot reach a live/private store.
    store = ContentOpsDurableStore(db_path, auto_migrate=False)
    if store.db_path.resolve().parent != output_dir:
        raise RenderError("LOCAL_STORE_RELOCATION_ESCAPES_DIRECTORY")
    store.run_migrations()
    work_id, message_id, dispatch_id = f"wi_local_{key}", f"msg_local_{key}", f"local_render_{key}"
    payload = _json({"markdown_sha256": _sha(markdown), "diagnostics_sha256": _sha(diagnostics), "file": path.name, "format": piece.format, "external_write": False})
    old = store.get_outbox_message(message_id)
    if old and old["payload"] != payload:
        raise RenderError("LOCAL_OUTBOX_PAYLOAD_CONFLICT")
    store.create_work_item(story_id=piece.piece_id, title="Local subscriber Markdown", target_surface="LOCAL_FILE_ONLY", work_item_id=work_id)
    store.register_outbox_message(message_id=message_id, work_item_id=work_id, destination="LOCAL_FILE_ONLY", payload=payload, status="LOCAL_ONLY_NOT_DISPATCHABLE")
    store.register_platform_dispatch(dispatch_id=dispatch_id, message_id=message_id, platform="local_file_only", status="LOCAL_RENDER_ONLY_NO_PUBLIC_WRITE")
    _immutable(path, markdown)
    _immutable(report, diagnostics)
    # Read exact bytes, even on replay; an old successful observation cannot mask tampering.
    if path.read_bytes() != markdown or report.read_bytes() != diagnostics:
        raise RenderError("LOCAL_READBACK_MISMATCH")
    readback = {"kind": "LOCAL_FILE_ONLY", "file": path.name, "markdown_sha256": _sha(path.read_bytes()), "status": "LOCAL_FILE_VERIFIED", "platform_publication_proven": False}
    store.register_readback(readback_id=f"rb_local_{key}", dispatch_id=dispatch_id, readback_data=_json(readback))
    store.register_reconciliation(reconciliation_id=f"rec_local_{key}", work_item_id=work_id, status="LOCAL_FILE_VERIFIED_NOT_PUBLISHED")
    return {"piece_id": piece.piece_id, "format": piece.format, "markdown_path": str(path), "diagnostics_path": str(report), "idempotency_key": key, "idempotent_replay": bool(old), "local_readback": "VERIFIED", "publication_performed": False, "omission_count": len(piece.diagnostics["omissions"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--publication-contract", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if not isinstance(record, Mapping):
            raise RenderError("INPUT_OBJECT_REQUIRED")
        piece = render_piece(record, SubscriberPolicy.from_source(args.publication_contract))
        print(json.dumps(write_local_piece(piece, args.output_dir), sort_keys=True))
        return 0
    except (OSError, ValueError, SyntaxError) as exc:
        print(json.dumps({"status": "REFUSED", "cause": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
