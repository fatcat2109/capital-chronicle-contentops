"""Main-owned report bytes -> governed input for the existing Simple writer.

No model, scheduler, production-store opening, publication or Main write occurs here.
Persistence uses an explicitly supplied ContentOpsDurableStore and its existing
artifact/work-item/outbox APIs. Internal outbox destinations cannot dispatch publicly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.four_trigger_data_resolution_adapter_v1 import (
    DESTINATIONS,
    build_data_need_plan,
    build_editorial_consumer_packet,
    build_trigger_request,
    prepare_simple_gemini_handoff,
    resolve_data_need_plan,
)

SCHEMA_VERSION = "contentops.capital_chronicle_latest_report_consumer.v1"
MAIN_REPORT_SCHEMA = "CapitalChronicleAssetAnalysisReportV1"
MAIN_ENVELOPE_SCHEMA = "CapitalChronicleLatestAnalysisReportEnvelopeV1"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
CONTRACT_REVISION = "asset-analysis-report-v1.0.0"
CHANGE_KINDS = (
    "NEW_REPORT",
    "NEW_EVENT",
    "THESIS_DELTA",
    "INVALIDATION",
    "CORRECTION",
    "FRESHNESS_REPAIR",
    "NO_MATERIAL_CHANGE",
)
CASES = (
    "FOUNDATION_DEEP_ASSET_ANALYSIS",
    "LATEST_DATA_HEADLINE_UPDATE",
    "PORTFOLIO_MANAGEMENT_REVIEW",
    "JIM_MANUAL_ANALYSIS",
)
LAYER_MAP = {
    "OBSERVED_SOURCE_FACT": "OBSERVED_FACT",
    "CC_ANALYSIS": "CAPITAL_CHRONICLE_ANALYSIS",
    "CONDITIONAL_SCENARIO": "SCENARIO_OR_UNCERTAINTY",
}
PUBLIC_RIGHTS = {"PUBLIC_DOMAIN_EIA_ORIGINAL_WITH_ATTRIBUTION"}
PRIVATE_KEYS = {
    "private_context",
    "account_id",
    "account_number",
    "positions",
    "position_id",
    "holdings",
    "balance",
    "equity",
    "margin",
    "password",
    "cookie",
    "cookies",
    "token",
    "access_token",
    "refresh_token",
    "session_id",
    "credentials",
    "private_key",
    "api_key",
    "api-key",
    "secret",
}
INBOX = "internal:cc-report-receipt"
EDITORIAL_INPUT = "internal:cc-report-editorial-input"


class LatestReportConsumerError(ValueError):
    """Invalid bytes, provenance or durable delivery state."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_of(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _without(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise LatestReportConsumerError("DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def _constant(_value: str) -> None:
    raise LatestReportConsumerError("NONFINITE_JSON_NUMBER")


def _load(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > 4_000_000:
        raise LatestReportConsumerError("BYTES_EMPTY_OR_OVERSIZED")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
        )
    except (ValueError, UnicodeError) as exc:
        raise LatestReportConsumerError("JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise LatestReportConsumerError("JSON_OBJECT_REQUIRED")
    return value


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LatestReportConsumerError("UTC_TIME_REQUIRED")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LatestReportConsumerError("UTC_TIME_INVALID") from exc
    return result


def _private(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).casefold() in PRIVATE_KEYS or _private(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_private(item) for item in value)
    if isinstance(value, str):
        # Do not reflect suspected private values in diagnostics.
        return any(
            marker in value.casefold()
            for marker in (
                "access_token=",
                "api_key=",
                "password=",
                "-----begin private key",
            )
        )
    return False


def _seal_errors(value: Mapping[str, Any], schema: str, field: str) -> list[str]:
    errors = []
    if value.get("schema") != schema or value.get("version") != "1.0.0":
        errors.append("SCHEMA_OR_VERSION_MISMATCH")
    if value.get("contract_revision") != CONTRACT_REVISION:
        errors.append("CONTRACT_REVISION_MISMATCH")
    if value.get("canonicalization") != CANONICALIZATION:
        errors.append("CANONICALIZATION_MISMATCH")
    if not _hash(value.get(field)) or value.get(field) != sha256_of(
        _without(value, field)
    ):
        errors.append("SEALED_HASH_MISMATCH")
    flags = value.get("authority_flags")
    if (
        not isinstance(flags, dict)
        or not flags
        or any(
            (type(item) is not bool or item is not False)
            if key != "external_effects"
            else (type(item) is not int or item != 0)
            for key, item in flags.items()
        )
    ):
        errors.append("AUTHORITY_FLAGS_INVALID")
    return errors


def _unsafe_authority(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            (
                (
                    str(key).endswith("_authority")
                    or key in {"unknown_write", "write_performed", "order_send_called"}
                )
                and item not in (False, 0, None)
            )
            or _unsafe_authority(item)
            for key, item in value.items()
        )
    return isinstance(value, list) and any(_unsafe_authority(item) for item in value)


def _schema_errors(
    value: dict[str, Any], schema_bytes: bytes | None, label: str
) -> list[str]:
    if schema_bytes is None:
        return [f"{label}_MAIN_SCHEMA_EXPORT_UNAVAILABLE"]
    from jsonschema import Draft202012Validator

    schema = _load(schema_bytes)

    def external_ref(value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                (
                    key in {"$ref", "$dynamicRef"}
                    and isinstance(item, str)
                    and not item.startswith("#")
                )
                or external_ref(item)
                for key, item in value.items()
            )
        return isinstance(value, list) and any(external_ref(item) for item in value)

    if external_ref(schema):
        return [f"{label}_EXTERNAL_SCHEMA_REFERENCE_FORBIDDEN"]
    Draft202012Validator.check_schema(schema)
    return (
        [f"{label}_MAIN_SCHEMA_VALIDATION_FAILED"]
        if not Draft202012Validator(schema).is_valid(value)
        else []
    )


def validate_latest_report_bytes(
    raw_bytes: bytes,
    *,
    report_bytes: Sequence[bytes] = (),
    expected_cutoff_utc: str,
    now_utc: str | None = None,
    envelope_schema_bytes: bytes | None = None,
    report_schema_bytes: bytes | None = None,
    producer_binding: Mapping[str, Any] | None = None,
    require_machine_schema: bool = True,
    required_claim_ids: Sequence[str] = (),
    optional_claim_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Validate Main's exact flat envelope and hash-addressed report bodies.

    ``now_utc`` is injectable for deterministic tests. The CLI uses the real clock.
    Missing optional claims are omitted locally; malformed seals and privacy errors
    remain hard failures. A stale evidence row can support dated context, never a
    current market fact, and carries that restriction into the writer input.
    """
    envelope = _load(raw_bytes)
    now = _time(now_utc) if now_utc is not None else datetime.now(timezone.utc)
    cutoff = _time(expected_cutoff_utc)
    errors = _seal_errors(envelope, MAIN_ENVELOPE_SCHEMA, "envelope_sha256")
    if _unsafe_authority(envelope):
        errors.append("UNAUTHORIZED_AUTHORITY_OR_UNKNOWN_WRITE")
    schema_errors = _schema_errors(envelope, envelope_schema_bytes, "ENVELOPE")
    if require_machine_schema:
        errors.extend(schema_errors)
        binding = producer_binding or {}
        for key, raw_schema in (
            ("envelope_schema_sha256", envelope_schema_bytes),
            ("report_schema_sha256", report_schema_bytes),
        ):
            if raw_schema is None or hashlib.sha256(
                raw_schema
            ).hexdigest() != binding.get(key):
                errors.append("MAIN_CONTRACT_IDENTITY_UNBOUND")
        if (
            not _text(binding.get("producer_revision"))
            or binding.get("contract_revision") != CONTRACT_REVISION
        ):
            errors.append("MAIN_CONTRACT_REVISION_UNBOUND")
    if _private(envelope):
        # Never return/copy the offending input.
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "blockers": ["PRIVATE_CONTEXT_EXCLUDED"],
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "claims": [],
            "missing_claims": [],
            "public_write_performed": False,
        }
    for key in ("event_id", "report_id", "materiality_rationale"):
        if not _text(envelope.get(key)):
            errors.append(f"{key.upper()}_REQUIRED")
    if (
        type(envelope.get("report_version")) is not int
        or envelope["report_version"] < 1
    ):
        errors.append("REPORT_VERSION_INVALID")
    if (
        envelope.get("case") not in CASES
        or envelope.get("change_kind") not in CHANGE_KINDS
    ):
        errors.append("CASE_OR_CHANGE_KIND_INVALID")
    event_identity = {
        key: envelope.get(key)
        for key in (
            "report_id",
            "report_version",
            "report_sha256",
            "change_kind",
            "changed_claim_ids",
        )
    }
    if envelope.get("event_id") != "report-event:" + sha256_of(event_identity):
        errors.append("EVENT_IDENTITY_MISMATCH")
    if envelope.get("publication_authority", False) is not False:
        errors.append("PUBLIC_PROJECTION_FLAGS_INVALID")
    for key in (
        "asset_ids",
        "affected_symbols",
        "horizon_blocks",
        "public_safe_claims",
        "limitations",
        "hold_conditions",
        "invalidation_conditions",
        "changed_claim_ids",
    ):
        if not isinstance(envelope.get(key), list):
            errors.append(f"{key.upper()}_ARRAY_REQUIRED")
    if (
        not envelope.get("asset_ids")
        or not envelope.get("run_id")
        or not envelope.get("source_snapshot")
    ):
        errors.append("ASSET_RUN_SNAPSHOT_IDENTITY_REQUIRED")
    try:
        generated, as_of, known = (
            _time(envelope.get(key))
            for key in ("generated_at_utc", "as_of_utc", "known_at_cutoff_utc")
        )
        if generated > now or known > now or as_of > now:
            errors.append("REPORT_CLOCK_IN_FUTURE")
        if known > cutoff or as_of > known or known > generated:
            errors.append("REPORT_CUTOFF_ORDER_INVALID")
    except LatestReportConsumerError:
        errors.append("REPORT_CLOCK_INVALID")
    reports: dict[str, dict[str, Any]] = {}
    report_raw_hashes = []
    for raw in report_bytes:
        report = _load(raw)
        errors.extend(
            "REPORT_" + error
            for error in _seal_errors(report, MAIN_REPORT_SCHEMA, "report_sha256")
        )
        if require_machine_schema:
            errors.extend(_schema_errors(report, report_schema_bytes, "REPORT"))
        report_hash = report.get("report_sha256")
        if not _hash(report_hash):
            continue
        reports[report_hash] = report
        report_raw_hashes.append(hashlib.sha256(raw).hexdigest())
        try:
            if (
                _time(report.get("known_at_cutoff_utc")) > cutoff
                or _time(report.get("generated_at_utc")) > now
            ):
                errors.append("REPORT_BODY_CUTOFF_OR_FUTURE")
        except LatestReportConsumerError:
            errors.append("REPORT_BODY_CLOCK_INVALID")
    wanted_hashes = [envelope.get("report_sha256")]
    if not wanted_hashes or any(
        not _hash(item) or item not in reports for item in wanted_hashes
    ):
        errors.append("HASH_BOUND_REPORT_BODY_MISSING")
    for digest, report in reports.items():
        if digest not in wanted_hashes:
            continue
        asset = report.get("asset") or {}
        if not isinstance(asset, dict) or asset.get("asset_id") not in (
            envelope.get("asset_ids") or []
        ):
            errors.append("REPORT_ASSET_SCOPE_MISMATCH")
        if report.get("case") != envelope.get("case"):
            errors.append("REPORT_CASE_SCOPE_MISMATCH")
        if report.get("run_id") != envelope.get("run_id"):
            errors.append("REPORT_RUN_ID_MISMATCH")
    claims = []
    missing: list[str] = []
    gaps = []
    seen: set[str] = set()
    required = set(required_claim_ids)
    optional = set(optional_claim_ids)
    raw_claims = envelope.get("public_safe_claims") or []
    if not isinstance(raw_claims, list):
        raw_claims = []
    for claim in raw_claims:
        if not isinstance(claim, dict):
            errors.append("CLAIM_OBJECT_REQUIRED")
            continue
        cid = claim.get("claim_id")
        if not _text(cid) or cid in seen:
            errors.append("CLAIM_ID_MISSING_OR_DUPLICATE")
            continue
        seen.add(cid)
        local_errors = []
        refs = claim.get("evidence_refs")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(_text(ref) for ref in refs)
        ):
            local_errors.append("EVIDENCE_REFS_MISSING")
            refs = []
        expected_hash = sha256_of(_without(claim, "claim_hash"))
        if claim.get("claim_hash") != expected_hash or not _text(claim.get("text")):
            local_errors.append("CLAIM_HASH_OR_TEXT_INVALID")
        layer = LAYER_MAP.get(claim.get("epistemic_layer"))
        if not layer:
            local_errors.append("EPISTEMIC_LAYER_UNMAPPED")
        if (
            claim.get("public_safe") is not True
            or claim.get("rights_state") not in PUBLIC_RIGHTS
        ):
            local_errors.append("CLAIM_PUBLIC_RIGHTS_BLOCKED")
        if claim.get("exact_or_proxy") not in {"EXACT", "PROXY"} or (
            claim.get("exact_or_proxy") == "PROXY"
            and not _text(claim.get("basis_risk"))
        ):
            local_errors.append("EXACT_PROXY_OR_BASIS_RISK_INVALID")
        owning = [
            report
            for digest, report in reports.items()
            if digest in wanted_hashes and claim in (report.get("claims") or [])
        ]
        if not owning:
            local_errors.append("CLAIM_NOT_BOUND_TO_REPORT")
        evidence = []
        for ref in refs:
            rows = [
                row
                for report in owning
                for row in report.get("evidence") or []
                if isinstance(row, dict) and row.get("evidence_id") == ref
            ]
            if not rows or len({sha256_of(row) for row in rows}) != 1:
                local_errors.append("EVIDENCE_MISSING_OR_CONFLICTING")
                gaps.append(
                    {
                        "claim_id": cid,
                        "evidence_id": ref,
                        "reason": "MISSING_OR_CONFLICTING_EVIDENCE",
                    }
                )
                continue
            row = rows[0]
            reasons = []
            projection_keys = (
                "evidence_id",
                "source_identity",
                "source_url",
                "source_hash",
                "query_sha256",
                "observation_time_utc",
                "retrieval_time_utc",
                "known_at_utc",
                "unit",
                "currency",
                "rights_evidence_sha256",
            )
            if {key: row.get(key) for key in projection_keys} not in (
                claim.get("supporting_evidence") or []
            ):
                reasons.append("SUPPORTING_EVIDENCE_PROJECTION_MISMATCH")
            if not _text(row.get("source_identity")) or not _hash(
                row.get("source_hash")
            ):
                reasons.append("SOURCE_IDENTITY_OR_HASH_MISSING")
            if row.get("rights_state") not in PUBLIC_RIGHTS:
                reasons.append("EVIDENCE_PUBLIC_RIGHTS_BLOCKED")
            if row.get("public_claim_use") is not True or not _hash(
                row.get("rights_evidence_sha256")
            ):
                reasons.append("PUBLIC_CLAIM_PERMISSION_OR_RIGHTS_EVIDENCE_MISSING")
            if not _text(row.get("query_id")) or not _hash(row.get("query_sha256")):
                reasons.append("QUERY_LINEAGE_MISSING")
            if row.get("freshness_state") in {None, "", "UNKNOWN", "NOT_VERIFIED"}:
                reasons.append("EVIDENCE_FRESHNESS_UNVERIFIED")
            if row.get("pit_state") in {
                None,
                "",
                "UNKNOWN",
                "NOT_VERIFIED",
                "UNAVAILABLE",
                "FAIL",
            }:
                reasons.append("EVIDENCE_PIT_UNVERIFIED")
            try:
                known = _time(row.get("known_at_utc"))
                observed = _time(row.get("observation_time_utc"))
                retrieved = _time(row.get("retrieval_time_utc"))
                if known > cutoff or known > now or retrieved > now or observed > known:
                    reasons.append("EVIDENCE_CLOCK_ORDER_INVALID")
            except LatestReportConsumerError:
                reasons.append("EVIDENCE_PIT_CLOCK_UNAVAILABLE")
            if reasons:
                local_errors.extend(reasons)
                gaps.append(
                    {"claim_id": cid, "evidence_id": ref, "reason": ",".join(reasons)}
                )
            # Only approved fields flow to the public editorial packet.
            evidence.append(
                {
                    key: deepcopy(row.get(key))
                    for key in (
                        "evidence_id",
                        "source_identity",
                        "source_url",
                        "source_hash",
                        "observation_time_utc",
                        "known_at_utc",
                        "retrieval_time_utc",
                        "rights_state",
                        "freshness_state",
                        "exact_or_proxy",
                        "rights_evidence_sha256",
                        "query_sha256",
                        "pit_state",
                    )
                }
            )
        if local_errors:
            if cid in optional and cid not in required:
                missing.append(cid)
                continue
            errors.extend(f"{cid}:{error}" for error in sorted(set(local_errors)))
            continue
        claims.append(
            {
                "claim_id": cid,
                "claim_hash": claim["claim_hash"],
                "text": claim["text"],
                "layer": layer,
                "producer_layer": claim["epistemic_layer"],
                "exact_or_proxy": claim["exact_or_proxy"],
                "basis_risk": claim.get("basis_risk"),
                "rights_state": claim["rights_state"],
                "evidence": evidence,
                "source_report_ids": sorted({report["report_id"] for report in owning}),
                "context_only": any(
                    row.get("freshness_state") not in {"FRESH", "CURRENT"}
                    for row in evidence
                ),
            }
        )
    for cid in required - seen:
        errors.append(f"{cid}:REQUIRED_CLAIM_ABSENT")
    missing.extend(optional - seen)
    if not claims and envelope.get("change_kind") != "NO_MATERIAL_CHANGE":
        errors.append("NO_ADMISSIBLE_PUBLIC_CLAIMS")
    parent = envelope.get("supersedes_report_id")
    if envelope.get("change_kind") in {"CORRECTION", "INVALIDATION"} and not _text(
        parent
    ):
        errors.append("CORRECTION_INVALIDATION_PARENT_REQUIRED")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "BLOCKED" if errors else "ADMITTED",
        "validated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "blockers": sorted(set(errors)),
        "schema_diagnostics": schema_errors,
        "machine_schema_verified": envelope_schema_bytes is not None
        and report_schema_bytes is not None
        and not any("SCHEMA" in error for error in errors),
        "producer_binding": deepcopy(dict(producer_binding or {})),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "report_raw_sha256": sorted(report_raw_hashes),
        "envelope_sha256": envelope.get("envelope_sha256"),
        "source_report_sha256": envelope.get("report_sha256"),
        "parent_report_sha256": envelope.get("parent_report_sha256"),
        "event_id": envelope.get("event_id"),
        "report_id": envelope.get("report_id"),
        "report_version": envelope.get("report_version"),
        "case": envelope.get("case"),
        "change_kind": envelope.get("change_kind"),
        "parent_report_id": parent,
        "asset_ids": envelope.get("asset_ids"),
        "affected_symbols": envelope.get("affected_symbols"),
        "known_at_cutoff_utc": envelope.get("known_at_cutoff_utc"),
        "claims": claims,
        "claim_set_hash": sha256_of(
            sorted((claim["claim_id"], claim["claim_hash"]) for claim in claims)
        ),
        "missing_claims": sorted(set(missing)),
        "research_gaps": gaps,
        "horizon_blocks": deepcopy(envelope.get("horizon_blocks") or []),
        "limitations": deepcopy(envelope.get("limitations") or []),
        "hold_and_invalidation_conditions": deepcopy(
            envelope.get("hold_conditions") or []
        )
        + deepcopy(envelope.get("invalidation_conditions") or []),
        "materiality_rationale": envelope.get("materiality_rationale"),
        "changed_claim_ids": deepcopy(envelope.get("changed_claim_ids") or []),
        "writer_invoked": False,
        "public_write_performed": False,
    }


class LatestReportDeliveryTracker:
    """Version/delivery projection over the existing store, with a serial lease."""

    def __init__(self, store: ContentOpsDurableStore):
        self.store = store

    def receipts(self) -> list[dict[str, Any]]:
        return [
            {
                **json.loads(row["payload"]),
                "delivery_status": row["status"],
                "message_id": row["message_id"],
            }
            for row in self.store.list_outbox_messages()
            if row["destination"] == INBOX
        ]

    @staticmethod
    def _related(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        return (
            left.get("event_id") == right.get("event_id")
            or left.get("report_id") == right.get("report_id")
            or left.get("report_id") == right.get("parent_report_id")
        )

    def consume(
        self, validation: Mapping[str, Any], *, receipt_id: str
    ) -> dict[str, Any]:
        if not _text(receipt_id) or _private(validation):
            raise LatestReportConsumerError("RECEIPT_ID_OR_PRIVACY_INVALID")
        owner = "cc-report-consumer-" + sha256_of(receipt_id)[:20]
        lease = self.store.acquire_lease(
            "internal:cc-report-consume", owner, ttl_seconds=60
        )
        try:
            rows = self.receipts()
            message_id = "cc-receipt-" + sha256_of(receipt_id)
            same_receipt = next(
                (row for row in rows if row["message_id"] == message_id), None
            )
            if same_receipt:
                if same_receipt["raw_sha256"] != validation["raw_sha256"]:
                    raise LatestReportConsumerError("RECEIPT_ID_CONFLICT")
                return same_receipt
            related = [
                row
                for row in rows
                if row["status"] in {"ADMITTED", "NO_MATERIAL_CHANGE_NOOP"}
                and self._related(row, validation)
            ]
            status = validation["status"]
            latest = max(related, key=lambda row: row["report_version"], default=None)
            if status == "ADMITTED" and latest:
                if validation["report_version"] < latest["report_version"]:
                    status = "OUT_OF_ORDER_NOOP"
                elif validation["report_version"] == latest["report_version"]:
                    status = (
                        "DUPLICATE_NOOP"
                        if validation["raw_sha256"] == latest["raw_sha256"]
                        else "CONFLICT_EQUAL_VERSION_DIFFERENT_BYTES"
                    )
                elif (
                    validation.get("parent_report_id")
                    and validation["parent_report_id"] != latest["report_id"]
                ):
                    status = "LINEAGE_CONFLICT"
                elif validation.get("parent_report_sha256") and validation[
                    "parent_report_sha256"
                ] != latest.get("source_report_sha256"):
                    status = "LINEAGE_HASH_CONFLICT"
            if (
                status == "ADMITTED"
                and validation["change_kind"] == "NO_MATERIAL_CHANGE"
            ):
                status = "NO_MATERIAL_CHANGE_NOOP"
            if (
                status == "ADMITTED"
                and validation["change_kind"] in {"CORRECTION", "INVALIDATION"}
                and not any(
                    row["report_id"] == validation.get("parent_report_id")
                    for row in related
                )
            ):
                status = "LINEAGE_PARENT_NOT_RECEIVED"
            record = {
                **deepcopy(dict(validation)),
                "status": status,
                "receipt_id": receipt_id,
                "affected_prior_inputs": [row["message_id"] for row in related]
                if validation.get("change_kind") in {"CORRECTION", "INVALIDATION"}
                else [],
            }
            work_id = "cc-report-" + sha256_of(receipt_id)
            artifact = "cc-admission-" + sha256_of(record)
            self.store.register_artifact(
                artifact_id=artifact,
                artifact_type="CC_REPORT_ADMISSION",
                storage_class="INTERNAL_READ_PROJECTION",
                schema_version=SCHEMA_VERSION,
                producer_ref="ContentOps.latest_report_consumer",
                content_bytes=canonical_bytes(record),
            )
            self.store.create_work_item(
                story_id="cc-report:"
                + str(record.get("event_id") or record["raw_sha256"]),
                title="Capital Chronicle report input",
                target_surface="CONTENTOPS_EDITORIAL_ONLY",
                work_item_id=work_id,
                input_artifact_ids=[artifact],
            )
            self.store.register_outbox_message(
                message_id=message_id,
                work_item_id=work_id,
                destination=INBOX,
                payload=canonical_bytes(record).decode(),
                status="REPORT_PENDING" if status == "ADMITTED" else "REPORT_TERMINAL",
            )
            if status in {"ADMITTED", "NO_MATERIAL_CHANGE_NOOP"}:
                for row in related:
                    if row["delivery_status"] in {"REPORT_PENDING", "REPORT_FAILED"}:
                        self.store.set_outbox_status(
                            row["message_id"], "REPORT_SUPERSEDED"
                        )
            return next(
                row for row in self.receipts() if row["message_id"] == message_id
            )
        finally:
            self.store.release_lease(lease["lease_id"], owner, lease["fencing_token"])

    def prepare_input(
        self,
        receipt_id: str,
        *,
        output_dir: str | Path,
        cutoff_utc: str,
        rolling_input: Mapping[str, Any] | None = None,
        published_memory: Sequence[Any] = (),
    ) -> dict[str, Any]:
        """Persist reconstructable writer input once; never invoke its writer."""
        owner = "cc-report-delivery-" + sha256_of(receipt_id)[:20]
        lease = self.store.acquire_lease(
            "internal:cc-report-consume", owner, ttl_seconds=60
        )
        try:
            rows = self.receipts()
            record = next(
                (row for row in rows if row["receipt_id"] == receipt_id), None
            )
            if (
                record is None
                or record["status"] != "ADMITTED"
                or record["delivery_status"] == "REPORT_SUPERSEDED"
            ):
                raise LatestReportConsumerError("REPORT_NOT_DELIVERABLE")
            if any(
                row["status"] in {"ADMITTED", "NO_MATERIAL_CHANGE_NOOP"}
                and self._related(record, row)
                and row["report_version"] > record["report_version"]
                for row in rows
            ):
                raise LatestReportConsumerError("NEWER_REPORT_ALREADY_RECEIVED")
            message_id = "cc-input-" + record["envelope_sha256"]
            previous = next(
                (
                    row
                    for row in self.store.list_outbox_messages()
                    if row["message_id"] == message_id
                ),
                None,
            )
            if previous:
                self.store.set_outbox_status(record["message_id"], "REPORT_INPUT_READY")
                return json.loads(previous["payload"])
            result = build_report_editorial_input(
                record,
                output_dir=output_dir,
                cutoff_utc=cutoff_utc,
                rolling_input=rolling_input,
                published_memory=published_memory,
            )
            self.store.register_outbox_message(
                message_id=message_id,
                work_item_id="cc-report-" + sha256_of(receipt_id),
                destination=EDITORIAL_INPUT,
                payload=canonical_bytes(result).decode(),
                status="INPUT_READY",
            )
            self.store.set_outbox_status(record["message_id"], "REPORT_INPUT_READY")
            return result
        finally:
            self.store.release_lease(lease["lease_id"], owner, lease["fencing_token"])

    def counts(self) -> dict[str, int]:
        rows = self.receipts()
        return {
            "report_events_received": len(rows),
            "report_events_consumed": sum(
                row["status"] in {"ADMITTED", "NO_MATERIAL_CHANGE_NOOP"} for row in rows
            ),
            "no_ops": sum(
                row["status"]
                in {"DUPLICATE_NOOP", "OUT_OF_ORDER_NOOP", "NO_MATERIAL_CHANGE_NOOP"}
                for row in rows
            ),
            "editorial_inputs": sum(
                row["delivery_status"] == "REPORT_INPUT_READY" for row in rows
            ),
            "drafts": 0,
            "writer_calls": 0,
            "missing_claims": sum(len(row.get("missing_claims") or []) for row in rows),
            "blocked_results": sum(
                row["status"]
                in {
                    "BLOCKED",
                    "CONFLICT_EQUAL_VERSION_DIFFERENT_BYTES",
                    "LINEAGE_CONFLICT",
                    "LINEAGE_HASH_CONFLICT",
                    "LINEAGE_PARENT_NOT_RECEIVED",
                }
                for row in rows
            ),
        }


def build_report_editorial_input(
    admission: Mapping[str, Any],
    *,
    output_dir: str | Path,
    cutoff_utc: str,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Any] = (),
) -> dict[str, Any]:
    if (
        admission.get("status") != "ADMITTED"
        or not admission.get("claims")
        or admission.get("change_kind") == "NO_MATERIAL_CHANGE"
    ):
        raise LatestReportConsumerError("ADMITTED_MATERIAL_REPORT_REQUIRED")
    if (
        _private(admission)
        or _private(rolling_input or {})
        or _private(list(published_memory))
    ):
        raise LatestReportConsumerError("PRIVATE_EDITORIAL_CONTEXT_EXCLUDED")
    claims = deepcopy(admission["claims"])
    mode = (
        "FOLLOW_UP_UPDATE"
        if admission["change_kind"] in {"CORRECTION", "INVALIDATION"}
        else "DATA_OR_DOCUMENT_LENS"
        if any(claim["context_only"] for claim in claims)
        else "CAPITAL_CHRONICLE_VIEW"
    )
    request = build_trigger_request(
        request_id="cc-report-" + admission["envelope_sha256"],
        idempotency_key=admission["envelope_sha256"],
        trigger_kind="SCHEDULED_LATEST_INTELLIGENCE",
        requester="SIMPLE_GEMINI_RUNTIME",
        target_assets=admission["asset_ids"],
        decision_purpose="Explain the admitted report change, its evidence and limits.",
        requested_at_utc=cutoff_utc,
        editorial_mode=mode,
        publication_intent="RESEARCH_ONLY",
        required_epistemic_state="ATTRIBUTED_REPORT_OR_INTERPRETATION",
    )
    plan = build_data_need_plan(
        request,
        [
            {
                "need_id": "admitted-main-report",
                "data_class": "capital_chronicle_report",
                "required_fields": ["public_claims"],
                "pit_required": True,
                "permitted_routes": ["EXISTING_MARKET_READ_MODEL"],
                "unit": "TEXT",
                "currency": "NONE",
            }
        ],
        as_of_utc=cutoff_utc,
    )
    resolution = resolve_data_need_plan(
        plan,
        source_layers={
            "read_models": [
                {
                    "need_id": "admitted-main-report",
                    "source_identity": admission["report_id"],
                    "source_hash": admission["envelope_sha256"],
                    "values": {"public_claims": claims},
                    "epistemic_state": "ATTRIBUTED_REPORT_OR_INTERPRETATION",
                    "rights_state": "PUBLIC_READ_ONLY",
                    "freshness_state": "CURRENT",
                    "pit_state": "PASS",
                }
            ]
        },
    )
    packet = build_editorial_consumer_packet(request, plan, resolution)
    handoff = prepare_simple_gemini_handoff(
        packet, output_dir=output_dir, cutoff_utc=cutoff_utc
    )
    sections = []
    for claim in claims:
        sections.append(
            {
                "section_id": "claim:" + claim["claim_id"],
                "purpose": "Explain what Main reports and why its scope matters.",
                "report_id": admission["report_id"],
                "source_report_ids": claim["source_report_ids"],
                "claim_id": claim["claim_id"],
                "claim_hash": claim["claim_hash"],
                "evidence_ids": [row["evidence_id"] for row in claim["evidence"]],
                "layer": claim["layer"],
                "source_text": claim["text"],
                "reader_caveat": claim.get("basis_risk")
                or "Capital Chronicle analysis is not independent event confirmation.",
            }
        )
    brief = {
        "what_changed": admission.get("materiality_rationale"),
        "change_kind": admission.get("change_kind"),
        "correction_lineage": {
            "report_id": admission.get("report_id"),
            "report_version": admission.get("report_version"),
            "supersedes_report_id": admission.get("parent_report_id"),
            "parent_report_sha256": admission.get("parent_report_sha256"),
            "affected_prior_inputs": deepcopy(
                admission.get("affected_prior_inputs") or []
            ),
            "workflow_owner": "existing published-memory/update-chain and DurablePublicationCoordinator",
            "automatic_public_update": False,
        },
        "changed_claim_ids": admission.get("changed_claim_ids"),
        "angle": "Explain the documented change and its causal limits for readers.",
        "mode": mode,
        "sections": sections,
        "why_it_matters_instruction": "Explain only evidence-supported mechanisms; label qualitative inference separately.",
        "horizon_blocks": admission["horizon_blocks"],
        "what_to_watch": admission["hold_and_invalidation_conditions"],
        "limitations": admission["limitations"],
        "report_truth": "HASH_BOUND_MAIN_REPORT",
        "underlying_event_truth": "NOT_UPGRADED_BY_REPORT_IMPORT",
        "private_context_included": False,
        "publication_authority": False,
    }
    context = handoff["runner_arguments"]["capital_chronicle_context"]
    context["latest_analysis_report"] = {
        "report_id": admission["report_id"],
        "report_version": admission["report_version"],
        "envelope_sha256": admission["envelope_sha256"],
        "claims": claims,
    }
    context["editorial_brief"] = brief
    handoff["runner_arguments"]["published_memory"] = deepcopy(list(published_memory))
    source_urls = sorted(
        {
            str(row.get("source_url") or row.get("source_identity"))
            for claim in claims
            for row in claim["evidence"]
            if str(row.get("source_url") or row.get("source_identity")).startswith(
                "https://"
            )
        }
    )
    report_candidate = {
        "headline_id": "cc-report:" + admission["envelope_sha256"],
        "headline_text": "Capital Chronicle report update: " + claims[0]["text"],
        "source_timestamp_utc": admission["known_at_cutoff_utc"],
        "source_account": "Capital Chronicle analysis report",
        "source_url": "",
        "official_source_urls": source_urls,
        "external_content": {
            "source_platform": "CAPITAL_CHRONICLE_REPORT_INPUT",
            "report_id": admission["report_id"],
            "report_version": admission["report_version"],
            "envelope_sha256": admission["envelope_sha256"],
            "report_truth_does_not_establish_event_truth": True,
        },
    }
    rolling = deepcopy(dict(rolling_input or {}))
    rolling["headlines"] = [report_candidate, *list(rolling.get("headlines") or [])]
    handoff["runner_arguments"]["rolling_input"] = rolling
    return {
        "schema_version": SCHEMA_VERSION,
        "disposition": "EDITORIAL_INPUT_READY",
        "brief": brief,
        "simple_gemini_handoff": handoff,
        "derivative_intents": [
            {
                "destination": destination,
                "state": "PLANNED_INPUT_NOT_COMPILED",
                "report_id": admission["report_id"],
                "claim_section_mapping": deepcopy(sections),
            }
            for destination in DESTINATIONS
        ],
        "editorial_input_count": 1,
        "draft_count": 0,
        "compiled_derivative_count": 0,
        "writer_invoked": False,
        "public_write_performed": False,
    }


def resolve_report_research_gaps(
    *,
    request_id: str,
    cutoff_utc: str,
    needs: Sequence[Mapping[str, Any]],
    source_layers: Mapping[str, Any],
    browser_recovery: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Use existing DB-first resolution. Fresh evidence needs a new Main version."""
    request = build_trigger_request(
        request_id=request_id,
        idempotency_key=request_id,
        trigger_kind="SCHEDULED_LATEST_INTELLIGENCE",
        requester="SIMPLE_GEMINI_RUNTIME",
        decision_purpose="Resolve named report evidence gaps without editing Main truth.",
        requested_at_utc=cutoff_utc,
    )
    plan = build_data_need_plan(request, needs, as_of_utc=cutoff_utc)
    receipt = resolve_data_need_plan(
        plan, source_layers=source_layers, browser_recovery=browser_recovery
    )
    return {
        "request": request,
        "plan": plan,
        "resolution": receipt,
        "main_report_mutated": False,
        "fresh_evidence_requires_new_main_version": True,
    }


class NeoNamedGapRecovery:
    """Adapt the existing Neo startup/MCP rendered-source seam to named needs.

    Captured text is context-only. It does not acquire redistribution/PIT rights
    or replace a Main claim. Explicit needs must request ``rendered_context``.
    """

    def __init__(
        self,
        *,
        allowed_hosts: Sequence[str],
        preflight: Any = None,
        recovery: Any = None,
    ):
        from live_contentops.browser_rendered_source_recovery_v1 import (
            BrowserOSNeoReadOnlyPreflight,
            BrowserOSNeoRenderedSourceRecovery,
        )

        self.preflight = preflight or BrowserOSNeoReadOnlyPreflight()
        self.recovery = recovery or BrowserOSNeoRenderedSourceRecovery(
            allowed_hosts=allowed_hosts
        )
        self.calls = 0

    def __call__(self, need: Mapping[str, Any]) -> dict[str, Any]:
        if (
            self.calls
            or need.get("required_fields") != ["rendered_context"]
            or not need.get("browseros_url")
        ):
            raise LatestReportConsumerError("NEO_NAMED_GAP_OR_BUDGET_INVALID")
        self.calls += 1
        preflight = self.preflight.run(auto_open=True, reconnect_once=True)
        if preflight.get("status") != "PASS":
            raise LatestReportConsumerError("BROWSER_UNAVAILABLE")
        captured = self.recovery(need["browseros_url"], 12.0, 200_000)
        return {
            **captured,
            "source_identity": captured["final_url"],
            "retrieved_at_utc": captured["observed_at_utc"],
            "known_at_utc": captured["observed_at_utc"],
            "values": {"rendered_context": captured["canonical_content_text"]},
            "rights_state": "PUBLIC_READ_ONLY",
            "pit_state": "UNAVAILABLE",
            "freshness_state": "CURRENT",
            "exact_or_proxy": "PROXY",
            "epistemic_state": "ATTRIBUTED_REPORT_OR_INTERPRETATION",
            "contradiction_state": "NONE",
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument(
        "--reports",
        type=Path,
        required=True,
        help="Main report JSON, report JSONL, or reports directory (read only)",
    )
    parser.add_argument("--cutoff-utc", required=True)
    parser.add_argument("--envelope-schema", type=Path)
    parser.add_argument("--report-schema", type=Path)
    parser.add_argument("--producer-binding", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise LatestReportConsumerError("OUTPUT_ALREADY_EXISTS")
    raw = args.envelope.read_bytes()
    wanted = {_load(raw).get("report_sha256")}
    candidates = (
        [path.read_bytes() for path in sorted(args.reports.glob("*.json"))]
        if args.reports.is_dir()
        else args.reports.read_bytes().splitlines()
        if args.reports.suffix == ".jsonl"
        else [args.reports.read_bytes()]
    )
    reports = [
        line
        for line in candidates
        if line.strip() and _load(line).get("report_sha256") in wanted
    ]
    result = validate_latest_report_bytes(
        raw,
        report_bytes=reports,
        expected_cutoff_utc=args.cutoff_utc,
        envelope_schema_bytes=args.envelope_schema.read_bytes()
        if args.envelope_schema
        else None,
        report_schema_bytes=args.report_schema.read_bytes()
        if args.report_schema
        else None,
        producer_binding=_load(args.producer_binding.read_bytes())
        if args.producer_binding
        else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(canonical_bytes(result) + b"\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "blocker_count": len(result["blockers"]),
                "raw_sha256": result["raw_sha256"],
                "output": str(args.output),
            }
        )
    )
    return 0 if result["status"] == "ADMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
