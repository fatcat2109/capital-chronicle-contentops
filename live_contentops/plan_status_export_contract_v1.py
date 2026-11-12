"""CC-400: the public export formats exercised by Publisher's composer.

Main still validates hashes, joins, rights and source bindings. This consumer
contract catches a changed field before Main's current reader can hide it behind
a generic schema error. CC-355/CC-325 demonstrated that failure on 9 November.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from jsonschema import Draft202012Validator, FormatChecker


# CC-398's versioned producer and the still-installed, pre-version producer.
# A new semantic version is added only with a composer regression fixture.
TESTED_CONTRACT_VERSIONS = frozenset({"2.0.0"})
LEGACY_CONTRACT = "legacy/schema-1.0.0"

TEXT = {"type": "string", "minLength": 1}
CLOCK = {**TEXT, "format": "date-time"}
NUMBER = {"type": "number"}
STATES = ["WAITING", "TRIGGERED", "FILLED", "CLOSED", "CANCELLED", "INVALIDATED", "EXPIRED", "VIEW_CHANGED"]


def _object(required, properties):
    return {"type": "object", "required": required, "properties": properties}


PLAN = _object(
    ["plan_id", "asset_id", "direction", "status", "zone", "expires_at_utc", "invalidation_conditions"],
    {"plan_id": TEXT, "asset_id": TEXT, "direction": {"enum": ["BULLISH", "BEARISH"]},
     "status": {"enum": [*STATES, None]}, "expires_at_utc": CLOCK,
     "zone": _object(["minimum", "maximum"], {"minimum": NUMBER, "maximum": NUMBER}),
     "invalidation_conditions": {"type": "array", "items": _object(
         ["field", "operator", "threshold"], {"field": TEXT, "operator": TEXT, "threshold": NUMBER})},
     "entries": {"type": ["array", "null"], "items": _object(["kind"], {
         "kind": {"enum": ["LIMIT", "BREAKOUT"]}, "zone_low": NUMBER, "zone_high": NUMBER, "level": NUMBER})},
     **{key: {"type": ["object", "null"]} for key in ("public_instrument", "scenario_analysis", "outcome")},
     **{key: {"anyOf": [CLOCK, {"type": "null"}]} for key in (
         "entry_deadline_utc", "time_exit_utc", "horizon_end_utc", "registered_at_utc", "not_before_utc")}})

# Main deliberately retains unreadable records with their first cause. Those
# records have no market or transitions and do not suppress the available plans.
PLAN_ROW = {"if": {"type": "object", "required": ["asset_id"],
                    "properties": {"asset_id": {"type": "null"}}},
            "then": _object(["plan_id", "asset_id", "status", "data_state", "first_cause"], {
                "plan_id": TEXT, "asset_id": {"type": "null"}, "status": {"type": "null"},
                "data_state": {"const": "UNAVAILABLE"}, "first_cause": TEXT}),
            "else": PLAN}

CONTRACT = _object(["status", "transitions"], {
    "status": _object(["schema", "schema_version", "generated_at_utc", "content_hash", "plans"], {
        "schema": {"const": "CapitalChroniclePlanStatusV1"}, "schema_version": {"const": "1.0.0"},
        "generated_at_utc": CLOCK, "content_hash": TEXT,
        "plans": {"type": "array", "items": PLAN_ROW}}),
    "transitions": _object(["schema", "schema_version", "generated_at_utc", "status_content_hash", "transitions"], {
        "schema": {"const": "CapitalChroniclePlanTransitionsV1"}, "schema_version": {"const": "1.0.0"},
        "generated_at_utc": CLOCK, "status_content_hash": TEXT,
        "transitions": {"type": "array", "items": _object(["plan_id", "status", "at_utc", "reason_code"], {
            "plan_id": TEXT, "status": {"enum": STATES}, "at_utc": CLOCK, "reason_code": TEXT})}})})
_VALIDATOR = Draft202012Validator(CONTRACT, format_checker=FormatChecker())


class PlanExportContractError(ValueError):
    def __init__(self, cause, field, version, detail):
        self.cause, self.field, self.version, self.detail = cause, field, version, detail
        super().__init__(f"{cause}: {field}: {detail}; contract={version}")


def contract_version(export):
    if not isinstance(export, Mapping) or not isinstance(export.get("status"), Mapping):
        raise PlanExportContractError("PLAN_EXPORT_CONTRACT_FIELD_INVALID", "status", "unknown", "invalid object")
    status = export.get("status") or {}
    if "contract_version" not in status:
        schema = status.get("schema_version")
        if schema == "1.0.0":
            return LEGACY_CONTRACT
        raise PlanExportContractError("PLAN_EXPORT_CONTRACT_UNKNOWN", "status.schema_version",
                                      str(schema)[:80], "untested legacy schema version")
    version = status["contract_version"]
    if not isinstance(version, str) or version not in TESTED_CONTRACT_VERSIONS:
        raise PlanExportContractError("PLAN_EXPORT_CONTRACT_UNKNOWN", "status.contract_version",
                                      str(version)[:80], "untested contract version")
    return version


def validate_export_contract(export):
    """Return the tested semantic version, or a precise consumer field path."""
    version = contract_version(export)
    error = next(_VALIDATOR.iter_errors(export), None)
    if error:
        path = list(error.absolute_path)
        if error.validator == "required":
            path.append(next(key for key in error.validator_value if key not in error.instance))
        field = "".join(f"[{part}]" if isinstance(part, int) else ("." if i else "") + part
                        for i, part in enumerate(path))
        raise PlanExportContractError("PLAN_EXPORT_CONTRACT_FIELD_INVALID", field, version,
                                      "missing required field" if error.validator == "required" else
                                      "invalid " + error.validator)
    # JSON accepts non-finite values by default; they must never reach a card.
    try:
        json.dumps(export, allow_nan=False)
    except ValueError as exc:
        raise PlanExportContractError("PLAN_EXPORT_CONTRACT_FIELD_INVALID", "export", version,
                                      "non-finite number") from exc
    return version


def export_row_failures(export):
    """CC-515: refuse envelope drift; isolate row drift by its original path.

    This does not admit a snapshot. Main must still verify both original seals,
    their join, and the remaining rows before the composer can use them.
    """
    version = contract_version(export)
    envelope = dict(export)
    for document, field in (("status", "plans"), ("transitions", "transitions")):
        value = export.get(document)
        if isinstance(value, Mapping) and isinstance(value.get(field), list):
            envelope[document] = {**value, field: []}
    validate_export_contract(envelope)
    failures = []
    for error in _VALIDATOR.iter_errors(export):
        path = list(error.absolute_path)
        if (len(path) < 3 or (path[0], path[1]) not in
                {("status", "plans"), ("transitions", "transitions")} or not isinstance(path[2], int)):
            # Preserve the existing exact envelope/version error.
            validate_export_contract(export)
        if any(r["document"] == path[0] and r["index"] == path[2] for r in failures):
            continue  # Retain the first cause for a row.
        if error.validator == "required":
            path.append(next(key for key in error.validator_value if key not in error.instance))
        field = "".join(f"[{part}]" if isinstance(part, int) else ("." if i else "") + part
                        for i, part in enumerate(path))
        row = export[path[0]][path[1]][path[2]]
        failures.append({"document": path[0], "index": path[2],
            "plan_id": row.get("plan_id") if isinstance(row, Mapping) else None,
            "field": field, "detail": "missing required field" if error.validator == "required"
            else "invalid " + error.validator, "contract_version": version})
    # Non-finite numbers in a row are also local; elsewhere they corrupt the file.
    for document, field in (("status", "plans"), ("transitions", "transitions")):
        for index, row in enumerate(export[document][field]):
            try:
                json.dumps(row, allow_nan=False)
            except ValueError:
                failures.append({"document": document, "index": index,
                    "plan_id": row.get("plan_id") if isinstance(row, Mapping) else None,
                    "field": f"{document}.{field}[{index}]", "detail": "non-finite number",
                    "contract_version": version})
    return failures


def record_row_failures(store, export, *, dry_run):
    """Keep the first row cause in the existing incident table, never a new queue."""
    failures = []
    for row in export.get("quarantined_rows") or []:
        error = PlanExportContractError("PLAN_EXPORT_CONTRACT_ROW_INVALID", row["field"],
            row["contract_version"], f"plan_id={row.get('plan_id')}; {row['detail']}")
        incident = rejected_export(store, error, dry_run=dry_run)
        failures.append({**row, "cause": str(error), "incident_id": incident["incident_id"],
                         "incident_recorded": incident["incident_recorded"]})
    return failures


def rejected_export(store, error, *, dry_run):
    """One existing-store incident per unknown version (or failed field), no post."""
    identity = error.cause + "|" + error.version
    if error.cause != "PLAN_EXPORT_CONTRACT_UNKNOWN":
        identity += "|" + error.field + "|" + error.detail
    incident_id = "plan-export-contract-" + hashlib.sha256(identity.encode()).hexdigest()[:32]
    if not dry_run:
        store.register_incident(incident_id=incident_id, work_item_id=None,
                                severity="ERROR", description=str(error))
    return {"status": "EXPORT_CONTRACT_REJECTED", "cause": str(error), "failed_field": error.field,
            "contract_version": error.version, "incident_id": incident_id,
            "incident_recorded": not dry_run, "dry_run": dry_run}
