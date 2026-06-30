"""V6 outbox preparation gate from exact Jim approval intake, local-only no-provider no-dispatch no-live."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND_V0"
OUTBOX_MODE = "local_outbox_preparation_only"
RECORD_STATUS = "prepared_for_future_dispatch_gate_only"

INTAKE_FALSE_FLAGS = (
    "eligible_for_live_send_now", "publication_ready", "dispatch_allowed", "live_send_allowed", "provider_call_made",
    "env_read", "credential_value_read", "network_call_made", "browser_session_used", "executable_request_artifact_created",
    "public_url_created", "metrics_created", "runtime_truth",
)
OUTBOX_RECORD_FIELDS = {
    "schema_version", "outbox_record_id", "source_exact_jim_approval_intake_gate_bundle_id",
    "approved_payload_preview_id", "approved_payload_hash", "platform", "outbox_mode", "record_status",
    "payload_body_included", "payload_body_non_executable", "payload_hash_bound", "destination_binding_present",
    "destination_binding_required_later", "credential_handle_present", "credential_handle_required_later",
    "dispatch_allowed", "publication_ready", "live_send_allowed", "provider_call_made", "env_read",
    "credential_value_read", "network_call_made", "browser_session_used", "executable_request_artifact_created",
    "public_url_created", "metrics_created", "runtime_truth", "human_review_required", "blockers", "warnings",
}
RECORD_FALSE_FLAGS = (
    "payload_body_included", "destination_binding_present", "credential_handle_present", "dispatch_allowed",
    "publication_ready", "live_send_allowed", "provider_call_made", "env_read", "credential_value_read",
    "network_call_made", "browser_session_used", "executable_request_artifact_created", "public_url_created",
    "metrics_created", "runtime_truth",
)
RECORD_TRUE_FLAGS = (
    "payload_body_non_executable", "payload_hash_bound", "destination_binding_required_later",
    "credential_handle_required_later", "human_review_required",
)
SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)


@dataclass(frozen=True)
class OutboxPreparationGateBundle:
    schema_version: str
    task_label: str
    outbox_preparation_gate_bundle_id: str
    source_exact_jim_approval_intake_gate_bundle_id: str
    outbox_preparation_status: str
    outbox_records: list[dict[str, Any]]
    eligible_for_future_dispatch_gate_task: bool
    eligible_for_live_send_now: bool
    publication_ready: bool
    dispatch_allowed: bool
    live_send_allowed: bool
    provider_call_made: bool
    env_read: bool
    credential_value_read: bool
    network_call_made: bool
    browser_session_used: bool
    executable_request_artifact_created: bool
    public_url_created: bool
    metrics_created: bool
    runtime_truth: bool
    human_review_required: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    packet_sha256: str = ""


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _packet_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("packet_sha256", None)
    return _sha(clone)


def _add(blockers: list[str], ok: bool, message: str) -> None:
    if not ok:
        blockers.append(message)


def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out: list[tuple[str, Any]] = []
        for key, value in obj.items():
            out.extend(_walk(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, value in enumerate(obj):
            out.extend(_walk(value, f"{path}[{idx}]"))
        return out
    return [(path, obj)]


def is_safe_string(value: str) -> bool:
    if SECRET_OR_URL_RE.search(value):
        return False
    low = value.lower()
    for safe in (
        "outbox_preparation", "outbox_record", "outbox_mode", "future_dispatch_gate", "dispatch_allowed",
        "publication_ready", "live_send_allowed", "eligible_for_live_send_now", "provider_call_made",
        "network_call_made", "browser_session_used", "executable_request_artifact_created", "public_url_created",
        "metrics_created", "credential_value_read", "credential_handle_required", "destination_binding_required",
    ):
        low = low.replace(safe, "safe_system_term")
    for phrase in (
        "browser profile", "browser path", "public url", "env value", "env_value", "live send", "live-send", "financial advice",
        "signal service", "fake metric", "fake metrics", "fake citation", "fake citations", "position sizing",
        "guaranteed prediction",
    ):
        if phrase in low:
            return False
    for word in ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localstorage", "secret", "metrics", "buy", "sell", "hold", "entries", "exits", "targets", "signal"):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return False
    return True


def safety_blockers(obj: dict[str, Any], label: str) -> list[str]:
    blockers: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value):
            blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers


def _source_id(intake_bundle: dict[str, Any]) -> str:
    return str(intake_bundle.get("exact_jim_approval_declaration_intake_gate_bundle_id") or _sha(intake_bundle)[:16])


def validate_intake_bundle(intake_bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(intake_bundle, dict):
        return ["intake_not_object"]
    blockers.extend(safety_blockers(intake_bundle, "intake"))
    _add(blockers, intake_bundle.get("schema_version") == SCHEMA_VERSION, "intake_schema_version_invalid")
    _add(blockers, intake_bundle.get("task_label") == UPSTREAM_TASK_LABEL, "intake_task_label_invalid")
    _add(blockers, intake_bundle.get("approval_declaration_status") == "accepted_for_future_outbox_preparation_only", "intake_status_not_accepted")
    validation = intake_bundle.get("approval_declaration_validation_result")
    _add(blockers, isinstance(validation, dict), "intake_validation_result_missing")
    if isinstance(validation, dict):
        _add(blockers, validation.get("valid") is True, "intake_validation_result_valid_not_true")
        _add(blockers, validation.get("declaration_supplied") is True, "intake_validation_result_declaration_supplied_not_true")
    _add(blockers, intake_bundle.get("approval_granted_now") is True, "intake_approval_granted_now_not_true")
    _add(blockers, intake_bundle.get("approval_valid_for_payload_hashes_only") is True, "intake_approval_valid_for_payload_hashes_only_not_true")
    _add(blockers, intake_bundle.get("eligible_for_future_outbox_preparation_task") is True, "intake_future_outbox_preparation_eligibility_not_true")
    for key in INTAKE_FALSE_FLAGS:
        _add(blockers, intake_bundle.get(key) is False, f"intake_{key}_not_false")
    _add(blockers, intake_bundle.get("human_review_required") is True, "intake_human_review_required_not_true")
    _add(blockers, intake_bundle.get("blockers", []) == [], "intake_blockers_not_empty")
    for key in ("approved_payload_preview_ids", "approved_payload_hashes", "approved_platforms"):
        _add(blockers, isinstance(intake_bundle.get(key), list) and len(intake_bundle[key]) > 0, f"intake_{key}_empty")
    return blockers


def make_outbox_records(intake_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    source_id = _source_id(intake_bundle)
    preview_ids = list(intake_bundle.get("approved_payload_preview_ids", []))
    hashes = list(intake_bundle.get("approved_payload_hashes", []))
    platforms = list(intake_bundle.get("approved_platforms", []))
    count = min(len(preview_ids), len(hashes), len(platforms))
    records: list[dict[str, Any]] = []
    for idx in range(count):
        seed = {"source": source_id, "preview": preview_ids[idx], "hash": hashes[idx], "platform": platforms[idx], "idx": idx}
        record = {
            "schema_version": SCHEMA_VERSION,
            "outbox_record_id": f"local_outbox_record_{_sha(seed)[:16]}",
            "source_exact_jim_approval_intake_gate_bundle_id": source_id,
            "approved_payload_preview_id": preview_ids[idx],
            "approved_payload_hash": hashes[idx],
            "platform": platforms[idx],
            "outbox_mode": OUTBOX_MODE,
            "record_status": RECORD_STATUS,
            "payload_body_included": False,
            "payload_body_non_executable": True,
            "payload_hash_bound": True,
            "destination_binding_present": False,
            "destination_binding_required_later": True,
            "credential_handle_present": False,
            "credential_handle_required_later": True,
            "dispatch_allowed": False,
            "publication_ready": False,
            "live_send_allowed": False,
            "provider_call_made": False,
            "env_read": False,
            "credential_value_read": False,
            "network_call_made": False,
            "browser_session_used": False,
            "executable_request_artifact_created": False,
            "public_url_created": False,
            "metrics_created": False,
            "runtime_truth": False,
            "human_review_required": True,
            "blockers": [],
            "warnings": ["local_non_executable_outbox_record", "future_dispatch_gate_required"],
        }
        records.append(record)
    return records


def validate_outbox_record(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(record, dict):
        return ["outbox_record_not_object"]
    blockers.extend(safety_blockers(record, "outbox_record"))
    extra = sorted(set(record) - OUTBOX_RECORD_FIELDS)
    _add(blockers, not extra, "outbox_record_extra_fields")
    for key in sorted(OUTBOX_RECORD_FIELDS):
        _add(blockers, key in record, f"missing_outbox_record_{key}")
    if blockers:
        return blockers
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "outbox_record_schema_version_invalid")
    _add(blockers, record.get("outbox_mode") == OUTBOX_MODE, "outbox_record_mode_invalid")
    _add(blockers, record.get("record_status") == RECORD_STATUS, "outbox_record_status_invalid")
    for key in RECORD_FALSE_FLAGS:
        _add(blockers, record.get(key) is False, f"outbox_record_{key}_not_false")
    for key in RECORD_TRUE_FLAGS:
        _add(blockers, record.get(key) is True, f"outbox_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "outbox_record_blockers_not_empty")
    return blockers


def make_outbox_preparation_gate_bundle(intake_bundle: dict[str, Any]) -> OutboxPreparationGateBundle:
    blockers = validate_intake_bundle(intake_bundle)
    records = make_outbox_records(intake_bundle) if not blockers else []
    for idx, record in enumerate(records):
        blockers.extend(f"record_{idx}_{b}" for b in validate_outbox_record(record))
    prepared = not blockers and len(records) > 0
    source_id = _source_id(intake_bundle if isinstance(intake_bundle, dict) else {})
    short = _sha({"source": source_id, "records": records, "prepared": prepared})[:16]
    bundle = OutboxPreparationGateBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        outbox_preparation_gate_bundle_id=f"outbox_preparation_gate_bundle_{short}",
        source_exact_jim_approval_intake_gate_bundle_id=source_id,
        outbox_preparation_status="prepared_for_future_dispatch_gate_only" if prepared else "blocked_not_prepared",
        outbox_records=records,
        eligible_for_future_dispatch_gate_task=prepared,
        eligible_for_live_send_now=False,
        publication_ready=False,
        dispatch_allowed=False,
        live_send_allowed=False,
        provider_call_made=False,
        env_read=False,
        credential_value_read=False,
        network_call_made=False,
        browser_session_used=False,
        executable_request_artifact_created=False,
        public_url_created=False,
        metrics_created=False,
        runtime_truth=False,
        human_review_required=True,
        blockers=blockers,
        warnings=["outbox_preparation_only", "no_provider", "no_dispatch", "no_live_send", "future_dispatch_gate_required"],
    )
    data = asdict(bundle)
    return OutboxPreparationGateBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> OutboxPreparationGateBundle:
    bundle = make_outbox_preparation_gate_bundle({})
    data = asdict(bundle)
    data["blockers"] = [reason]
    data["outbox_preparation_status"] = "blocked_not_prepared"
    data["packet_sha256"] = _packet_sha(data)
    return OutboxPreparationGateBundle(**data)


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 outbox preparation gate CLI")
    parser.add_argument("--exact-jim-approval-intake-gate-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        intake = load_json_object(args.exact_jim_approval_intake_gate_bundle)
        packet = make_outbox_preparation_gate_bundle(intake)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_dispatch_gate_task else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())