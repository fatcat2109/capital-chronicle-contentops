"""V6 dispatch gate scaffold from prepared outbox, local-only no-provider no-dispatch no-live."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
OUTBOX_MODE = "local_outbox_preparation_only"
OUTBOX_RECORD_STATUS = "prepared_for_future_dispatch_gate_only"
DISPATCH_GATE_MODE = "dispatch_gate_scaffold_only"
REVIEW_STATUS = "ready_for_future_destination_binding_review_only"

UPSTREAM_FALSE_FLAGS = (
    "eligible_for_live_send_now", "publication_ready", "dispatch_allowed", "live_send_allowed", "provider_call_made",
    "env_read", "credential_value_read", "network_call_made", "browser_session_used", "executable_request_artifact_created",
    "public_url_created", "metrics_created", "runtime_truth",
)
OUTBOX_RECORD_FALSE_FLAGS = (
    "payload_body_included", "destination_binding_present", "credential_handle_present", "dispatch_allowed",
    "publication_ready", "live_send_allowed", "provider_call_made", "env_read", "credential_value_read",
    "network_call_made", "browser_session_used", "executable_request_artifact_created", "public_url_created",
    "metrics_created", "runtime_truth",
)
OUTBOX_RECORD_TRUE_FLAGS = (
    "payload_body_non_executable", "payload_hash_bound", "destination_binding_required_later",
    "credential_handle_required_later", "human_review_required",
)
REVIEW_FIELDS = {
    "schema_version", "dispatch_review_record_id", "source_outbox_record_id", "platform", "approved_payload_preview_id",
    "approved_payload_hash", "dispatch_gate_mode", "review_status", "destination_binding_present",
    "destination_binding_required_later", "credential_handle_present", "credential_handle_required_later",
    "payload_hash_revalidation_required_later", "exact_operator_dispatch_go_required_later", "dispatch_allowed",
    "publication_ready", "live_send_allowed", "provider_call_made", "env_read", "credential_value_read",
    "network_call_made", "browser_session_used", "executable_request_artifact_created", "public_url_created",
    "metrics_created", "runtime_truth", "human_review_required", "blockers", "warnings",
}
REVIEW_FALSE_FLAGS = (
    "destination_binding_present", "credential_handle_present", "dispatch_allowed", "publication_ready", "live_send_allowed",
    "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used",
    "executable_request_artifact_created", "public_url_created", "metrics_created", "runtime_truth",
)
REVIEW_TRUE_FLAGS = (
    "destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later",
    "exact_operator_dispatch_go_required_later", "human_review_required",
)
SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)


@dataclass(frozen=True)
class DispatchGateScaffoldBundle:
    schema_version: str
    task_label: str
    dispatch_gate_scaffold_bundle_id: str
    source_outbox_preparation_gate_bundle_id: str
    dispatch_gate_status: str
    dispatch_review_records: list[dict[str, Any]]
    destination_binding_required_later: bool
    credential_handle_required_later: bool
    payload_hash_revalidation_required_later: bool
    exact_operator_dispatch_go_required_later: bool
    redacted_audit_required_later: bool
    manual_fallback_required_later: bool
    kill_switch_required_later: bool
    eligible_for_future_destination_binding_task: bool
    eligible_for_future_dispatch_execution_task: bool
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
        "dispatch_gate_scaffold", "dispatch_review_record", "future_destination_binding_review",
        "future_dispatch_execution", "exact_operator_dispatch_go", "dispatch_allowed", "live_send_allowed",
        "eligible_for_live_send_now", "publication_ready", "provider_call_made", "network_call_made",
        "browser_session_used", "executable_request_artifact_created", "public_url_created", "metrics_created",
        "credential_value_read", "credential_handle_required", "destination_binding_required", "payload_body_included",
    ):
        low = low.replace(safe, "safe_system_term")
    for phrase in (
        "browser profile", "browser path", "provider config", "env value", "credential value", "public url",
        "payload body", "live send", "live-send", "financial advice", "signal service", "fake metric",
        "fake metrics", "fake citation", "fake citations", "position sizing", "guaranteed prediction",
    ):
        if phrase in low:
            return False
    for word in ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localstorage", "secret", "metrics", "buy", "sell", "hold", "entries", "exits", "targets", "signal", "curl"):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return False
    return True


def safety_blockers(obj: dict[str, Any], label: str) -> list[str]:
    blockers: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value):
            blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers


def _source_id(outbox_bundle: dict[str, Any]) -> str:
    return str(outbox_bundle.get("outbox_preparation_gate_bundle_id") or _sha(outbox_bundle)[:16])


def validate_outbox_record(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(record, dict):
        return ["outbox_record_not_object"]
    blockers.extend(safety_blockers(record, "outbox_record"))
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "outbox_record_schema_version_invalid")
    _add(blockers, record.get("outbox_mode") == OUTBOX_MODE, "outbox_record_mode_invalid")
    _add(blockers, record.get("record_status") == OUTBOX_RECORD_STATUS, "outbox_record_status_invalid")
    for key in OUTBOX_RECORD_FALSE_FLAGS:
        _add(blockers, record.get(key) is False, f"outbox_record_{key}_not_false")
    for key in OUTBOX_RECORD_TRUE_FLAGS:
        _add(blockers, record.get(key) is True, f"outbox_record_{key}_not_true")
    _add(blockers, record.get("blockers", []) == [], "outbox_record_blockers_not_empty")
    for key in ("approved_payload_preview_id", "approved_payload_hash", "platform"):
        _add(blockers, isinstance(record.get(key), str) and record.get(key) != "", f"outbox_record_{key}_empty")
    return blockers


def validate_outbox_preparation_bundle(outbox_bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(outbox_bundle, dict):
        return ["outbox_bundle_not_object"]
    blockers.extend(safety_blockers(outbox_bundle, "outbox_bundle"))
    _add(blockers, outbox_bundle.get("schema_version") == SCHEMA_VERSION, "outbox_bundle_schema_version_invalid")
    _add(blockers, outbox_bundle.get("task_label") == UPSTREAM_TASK_LABEL, "outbox_bundle_task_label_invalid")
    _add(blockers, outbox_bundle.get("outbox_preparation_status") == "prepared_for_future_dispatch_gate_only", "outbox_bundle_status_not_prepared")
    _add(blockers, isinstance(outbox_bundle.get("outbox_records"), list) and len(outbox_bundle.get("outbox_records", [])) > 0, "outbox_bundle_records_empty")
    _add(blockers, outbox_bundle.get("eligible_for_future_dispatch_gate_task") is True, "outbox_bundle_future_dispatch_gate_eligibility_not_true")
    for key in UPSTREAM_FALSE_FLAGS:
        _add(blockers, outbox_bundle.get(key) is False, f"outbox_bundle_{key}_not_false")
    _add(blockers, outbox_bundle.get("human_review_required") is True, "outbox_bundle_human_review_required_not_true")
    _add(blockers, outbox_bundle.get("blockers", []) == [], "outbox_bundle_blockers_not_empty")
    if isinstance(outbox_bundle.get("outbox_records"), list):
        for idx, record in enumerate(outbox_bundle["outbox_records"]):
            blockers.extend(f"record_{idx}_{b}" for b in validate_outbox_record(record))
    return blockers


def make_dispatch_review_records(outbox_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source_id = _source_id(outbox_bundle)
    for idx, record in enumerate(outbox_bundle.get("outbox_records", [])):
        if not isinstance(record, dict):
            continue
        seed = {"source": source_id, "outbox_record_id": record.get("outbox_record_id"), "idx": idx}
        records.append({
            "schema_version": SCHEMA_VERSION,
            "dispatch_review_record_id": f"dispatch_review_record_{_sha(seed)[:16]}",
            "source_outbox_record_id": record.get("outbox_record_id", ""),
            "platform": record.get("platform", ""),
            "approved_payload_preview_id": record.get("approved_payload_preview_id", ""),
            "approved_payload_hash": record.get("approved_payload_hash", ""),
            "dispatch_gate_mode": DISPATCH_GATE_MODE,
            "review_status": REVIEW_STATUS,
            "destination_binding_present": False,
            "destination_binding_required_later": True,
            "credential_handle_present": False,
            "credential_handle_required_later": True,
            "payload_hash_revalidation_required_later": True,
            "exact_operator_dispatch_go_required_later": True,
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
            "warnings": ["dispatch_gate_scaffold_only", "future_dispatch_execution_task_required"],
        })
    return records


def validate_dispatch_review_record(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(record, dict):
        return ["dispatch_review_record_not_object"]
    blockers.extend(safety_blockers(record, "dispatch_review_record"))
    extra = sorted(set(record) - REVIEW_FIELDS)
    _add(blockers, not extra, "dispatch_review_record_extra_fields")
    for key in sorted(REVIEW_FIELDS):
        _add(blockers, key in record, f"missing_dispatch_review_record_{key}")
    if blockers:
        return blockers
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "dispatch_review_record_schema_version_invalid")
    _add(blockers, record.get("dispatch_gate_mode") == DISPATCH_GATE_MODE, "dispatch_review_record_mode_invalid")
    _add(blockers, record.get("review_status") == REVIEW_STATUS, "dispatch_review_record_status_invalid")
    for key in REVIEW_FALSE_FLAGS:
        _add(blockers, record.get(key) is False, f"dispatch_review_record_{key}_not_false")
    for key in REVIEW_TRUE_FLAGS:
        _add(blockers, record.get(key) is True, f"dispatch_review_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "dispatch_review_record_blockers_not_empty")
    for key in ("source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash"):
        _add(blockers, isinstance(record.get(key), str) and record.get(key) != "", f"dispatch_review_record_{key}_empty")
    return blockers


def make_dispatch_gate_scaffold_bundle(outbox_bundle: dict[str, Any]) -> DispatchGateScaffoldBundle:
    blockers = validate_outbox_preparation_bundle(outbox_bundle)
    records = make_dispatch_review_records(outbox_bundle) if not blockers else []
    for idx, record in enumerate(records):
        blockers.extend(f"review_{idx}_{b}" for b in validate_dispatch_review_record(record))
    ready = not blockers and len(records) > 0
    source_id = _source_id(outbox_bundle if isinstance(outbox_bundle, dict) else {})
    short = _sha({"source": source_id, "records": records, "ready": ready})[:16]
    bundle = DispatchGateScaffoldBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        dispatch_gate_scaffold_bundle_id=f"dispatch_gate_scaffold_bundle_{short}",
        source_outbox_preparation_gate_bundle_id=source_id,
        dispatch_gate_status="ready_for_future_destination_binding_review_only" if ready else "blocked_no_dispatch_review_records",
        dispatch_review_records=records,
        destination_binding_required_later=True,
        credential_handle_required_later=True,
        payload_hash_revalidation_required_later=True,
        exact_operator_dispatch_go_required_later=True,
        redacted_audit_required_later=True,
        manual_fallback_required_later=True,
        kill_switch_required_later=True,
        eligible_for_future_destination_binding_task=ready,
        eligible_for_future_dispatch_execution_task=False,
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
        warnings=["dispatch_gate_scaffold_only", "no_provider", "no_dispatch", "no_live_send", "future_dispatch_execution_task_separate"],
    )
    data = asdict(bundle)
    return DispatchGateScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> DispatchGateScaffoldBundle:
    bundle = make_dispatch_gate_scaffold_bundle({})
    data = asdict(bundle)
    data["blockers"] = [reason]
    data["dispatch_gate_status"] = "blocked_no_dispatch_review_records"
    data["packet_sha256"] = _packet_sha(data)
    return DispatchGateScaffoldBundle(**data)


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 dispatch gate scaffold CLI")
    parser.add_argument("--outbox-preparation-gate-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        outbox_bundle = load_json_object(args.outbox_preparation_gate_bundle)
        packet = make_dispatch_gate_scaffold_bundle(outbox_bundle)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_destination_binding_task else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())