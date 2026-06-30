"""V6 destination binding review scaffold from dispatch gate, no-env no-dispatch no-live."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISPATCH_GATE_SCAFFOLD_FROM_PREPARED_OUTBOX_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
DISPATCH_GATE_STATUS = "ready_for_future_destination_binding_review_only"
DISPATCH_GATE_MODE = "dispatch_gate_scaffold_only"
DISPATCH_REVIEW_STATUS = "ready_for_future_destination_binding_review_only"
DESTINATION_BINDING_MODE = "destination_binding_review_scaffold_only"
DESTINATION_REVIEW_STATUS = "ready_for_future_symbolic_destination_binding_only"

BUNDLE_FALSE_FLAGS = (
    "eligible_for_future_dispatch_execution_task", "eligible_for_live_send_now", "publication_ready", "dispatch_allowed",
    "live_send_allowed", "provider_call_made", "env_read", "credential_value_read", "network_call_made",
    "browser_session_used", "executable_request_artifact_created", "public_url_created", "metrics_created", "runtime_truth",
)
BUNDLE_TRUE_FLAGS = (
    "destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later",
    "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later",
    "kill_switch_required_later", "eligible_for_future_destination_binding_task", "human_review_required",
)
DISPATCH_RECORD_FALSE_FLAGS = (
    "destination_binding_present", "credential_handle_present", "dispatch_allowed", "publication_ready", "live_send_allowed",
    "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used",
    "executable_request_artifact_created", "public_url_created", "metrics_created", "runtime_truth",
)
DISPATCH_RECORD_TRUE_FLAGS = (
    "destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later",
    "exact_operator_dispatch_go_required_later", "human_review_required",
)
DESTINATION_REVIEW_FALSE_FLAGS = (
    "destination_binding_present", "credential_handle_present", "credential_value_read", "env_read", "provider_call_made",
    "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present",
    "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present",
    "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth",
)
DESTINATION_REVIEW_TRUE_FLAGS = (
    "destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later",
    "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later",
    "kill_switch_required_later", "human_review_required",
)
DESTINATION_REVIEW_FIELDS = {
    "schema_version", "destination_binding_review_record_id", "source_dispatch_review_record_id", "source_outbox_record_id",
    "platform", "approved_payload_preview_id", "approved_payload_hash", "destination_binding_mode", "review_status",
    "symbolic_destination_binding_id", "symbolic_credential_handle_id", "destination_binding_present",
    "destination_binding_required_later", "credential_handle_present", "credential_handle_required_later", "credential_value_read",
    "env_read", "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created",
    "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present",
    "payload_body_present", "public_url_created", "metrics_created", "payload_hash_revalidation_required_later",
    "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later",
    "kill_switch_required_later", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth",
    "human_review_required", "blockers", "warnings",
}
SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)


@dataclass(frozen=True)
class DestinationBindingReviewScaffoldBundle:
    schema_version: str
    task_label: str
    destination_binding_review_scaffold_bundle_id: str
    source_dispatch_gate_scaffold_bundle_id: str
    destination_binding_review_status: str
    destination_binding_review_records: list[dict[str, Any]]
    eligible_for_future_credential_presence_membership_task: bool
    eligible_for_future_dispatch_execution_task: bool
    eligible_for_live_send_now: bool
    destination_binding_present: bool
    credential_handle_present: bool
    credential_value_read: bool
    env_read: bool
    provider_call_made: bool
    network_call_made: bool
    browser_session_used: bool
    executable_request_artifact_created: bool
    endpoint_url_present: bool
    webhook_url_present: bool
    channel_id_present: bool
    account_id_present: bool
    token_present: bool
    payload_body_present: bool
    public_url_created: bool
    metrics_created: bool
    publication_ready: bool
    dispatch_allowed: bool
    live_send_allowed: bool
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
        "destination_binding_review", "destination_binding_required", "symbolic_destination_binding_required_later",
        "symbolic_credential_handle_required_later", "credential_handle_required", "credential_value_read", "dispatch_gate_scaffold",
        "dispatch_review_record", "future_credential_presence_membership", "future_dispatch_execution", "eligible_for_live_send_now",
        "dispatch_allowed", "live_send_allowed", "publication_ready", "provider_call_made", "network_call_made",
        "browser_session_used", "executable_request_artifact_created", "public_url_created", "metrics_created",
        "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present",
        "payload_body_present", "runtime_truth", "no_env", "no_credential", "no_provider", "no_dispatch", "no_live_send",
    ):
        low = low.replace(safe, "safe_system_term")
    for phrase in (
        "browser profile", "browser path", "provider config", "env value", "credential value", "public url",
        "payload body", "live send", "live-send", "financial advice", "signal service", "fake metric",
        "fake metrics", "fake citation", "fake citations", "position sizing", "guaranteed prediction", "request pattern",
    ):
        if phrase in low:
            return False
    for word in ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localstorage", "secret", "metrics", "buy", "sell", "hold", "entries", "exits", "targets", "signal", "curl", "fetch", "re" + "quests"):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return False
    return True


def safety_blockers(obj: Any, label: str) -> list[str]:
    blockers: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value):
            blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers


def validate_dispatch_review_record(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(record, dict):
        return ["dispatch_review_record_not_object"]
    blockers.extend(safety_blockers(record, "dispatch_review_record"))
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "dispatch_review_record_schema_version_invalid")
    _add(blockers, record.get("dispatch_gate_mode") == DISPATCH_GATE_MODE, "dispatch_review_record_mode_invalid")
    _add(blockers, record.get("review_status") == DISPATCH_REVIEW_STATUS, "dispatch_review_record_status_invalid")
    for key in DISPATCH_RECORD_FALSE_FLAGS:
        _add(blockers, record.get(key) is False, f"dispatch_review_record_{key}_not_false")
    for key in DISPATCH_RECORD_TRUE_FLAGS:
        _add(blockers, record.get(key) is True, f"dispatch_review_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "dispatch_review_record_blockers_not_empty")
    for key in ("source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash"):
        _add(blockers, isinstance(record.get(key), str) and record.get(key) != "", f"dispatch_review_record_{key}_empty")
    return blockers


def validate_dispatch_gate_scaffold_bundle(bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(bundle, dict):
        return ["dispatch_gate_bundle_not_object"]
    blockers.extend(safety_blockers(bundle, "dispatch_gate_bundle"))
    _add(blockers, bundle.get("schema_version") == SCHEMA_VERSION, "dispatch_gate_bundle_schema_version_invalid")
    _add(blockers, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "dispatch_gate_bundle_task_label_invalid")
    _add(blockers, bundle.get("dispatch_gate_status") == DISPATCH_GATE_STATUS, "dispatch_gate_bundle_status_not_ready")
    records = bundle.get("dispatch_review_records")
    _add(blockers, isinstance(records, list) and len(records) > 0, "dispatch_gate_bundle_records_empty")
    for key in BUNDLE_TRUE_FLAGS:
        _add(blockers, bundle.get(key) is True, f"dispatch_gate_bundle_{key}_not_true")
    for key in BUNDLE_FALSE_FLAGS:
        _add(blockers, bundle.get(key) is False, f"dispatch_gate_bundle_{key}_not_false")
    _add(blockers, bundle.get("blockers") == [], "dispatch_gate_bundle_blockers_not_empty")
    if isinstance(records, list):
        for idx, record in enumerate(records):
            blockers.extend(f"record_{idx}_{b}" for b in validate_dispatch_review_record(record))
    return blockers


def make_destination_binding_review_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    source_id = str(bundle.get("dispatch_gate_scaffold_bundle_id") or _sha(bundle)[:16])
    records: list[dict[str, Any]] = []
    for idx, record in enumerate(bundle.get("dispatch_review_records", [])):
        if not isinstance(record, dict):
            continue
        seed = {"source": source_id, "dispatch_review_record_id": record.get("dispatch_review_record_id"), "idx": idx}
        short = _sha(seed)[:16]
        records.append({
            "schema_version": SCHEMA_VERSION,
            "destination_binding_review_record_id": f"destination_binding_review_record_{short}",
            "source_dispatch_review_record_id": record.get("dispatch_review_record_id", ""),
            "source_outbox_record_id": record.get("source_outbox_record_id", ""),
            "platform": record.get("platform", ""),
            "approved_payload_preview_id": record.get("approved_payload_preview_id", ""),
            "approved_payload_hash": record.get("approved_payload_hash", ""),
            "destination_binding_mode": DESTINATION_BINDING_MODE,
            "review_status": DESTINATION_REVIEW_STATUS,
            "symbolic_destination_binding_id": f"symbolic_destination_binding_required_later_{short}",
            "symbolic_credential_handle_id": f"symbolic_credential_handle_required_later_{short}",
            "destination_binding_present": False,
            "destination_binding_required_later": True,
            "credential_handle_present": False,
            "credential_handle_required_later": True,
            "credential_value_read": False,
            "env_read": False,
            "provider_call_made": False,
            "network_call_made": False,
            "browser_session_used": False,
            "executable_request_artifact_created": False,
            "endpoint_url_present": False,
            "webhook_url_present": False,
            "channel_id_present": False,
            "account_id_present": False,
            "token_present": False,
            "payload_body_present": False,
            "public_url_created": False,
            "metrics_created": False,
            "payload_hash_revalidation_required_later": True,
            "exact_operator_dispatch_go_required_later": True,
            "redacted_audit_required_later": True,
            "manual_fallback_required_later": True,
            "kill_switch_required_later": True,
            "publication_ready": False,
            "dispatch_allowed": False,
            "live_send_allowed": False,
            "runtime_truth": False,
            "human_review_required": True,
            "blockers": [],
            "warnings": ["destination_binding_review_scaffold_only", "future_credential_presence_membership_task_required"],
        })
    return records


def validate_destination_binding_review_record(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(record, dict):
        return ["destination_binding_review_record_not_object"]
    blockers.extend(safety_blockers(record, "destination_binding_review_record"))
    extra = sorted(set(record) - DESTINATION_REVIEW_FIELDS)
    _add(blockers, not extra, "destination_binding_review_record_extra_fields")
    for key in sorted(DESTINATION_REVIEW_FIELDS):
        _add(blockers, key in record, f"missing_destination_binding_review_record_{key}")
    if blockers:
        return blockers
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "destination_binding_review_record_schema_version_invalid")
    _add(blockers, record.get("destination_binding_mode") == DESTINATION_BINDING_MODE, "destination_binding_review_record_mode_invalid")
    _add(blockers, record.get("review_status") == DESTINATION_REVIEW_STATUS, "destination_binding_review_record_status_invalid")
    _add(blockers, str(record.get("symbolic_destination_binding_id", "")).startswith("symbolic_destination_binding_required_later_"), "destination_binding_review_record_symbolic_destination_binding_id_prefix_invalid")
    _add(blockers, str(record.get("symbolic_credential_handle_id", "")).startswith("symbolic_credential_handle_required_later_"), "destination_binding_review_record_symbolic_credential_handle_id_prefix_invalid")
    for key in DESTINATION_REVIEW_FALSE_FLAGS:
        _add(blockers, record.get(key) is False, f"destination_binding_review_record_{key}_not_false")
    for key in DESTINATION_REVIEW_TRUE_FLAGS:
        _add(blockers, record.get(key) is True, f"destination_binding_review_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "destination_binding_review_record_blockers_not_empty")
    return blockers


def make_destination_binding_review_scaffold_bundle(dispatch_bundle: dict[str, Any]) -> DestinationBindingReviewScaffoldBundle:
    blockers = validate_dispatch_gate_scaffold_bundle(dispatch_bundle)
    records = make_destination_binding_review_records(dispatch_bundle) if not blockers else []
    for idx, record in enumerate(records):
        blockers.extend(f"destination_review_{idx}_{b}" for b in validate_destination_binding_review_record(record))
    ready = not blockers and len(records) > 0
    source_id = str(dispatch_bundle.get("dispatch_gate_scaffold_bundle_id") or _sha(dispatch_bundle if isinstance(dispatch_bundle, dict) else {})[:16])
    short = _sha({"source": source_id, "records": records, "ready": ready})[:16]
    bundle = DestinationBindingReviewScaffoldBundle(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL, destination_binding_review_scaffold_bundle_id=f"destination_binding_review_scaffold_bundle_{short}",
        source_dispatch_gate_scaffold_bundle_id=source_id, destination_binding_review_status="ready_for_future_credential_presence_membership_only" if ready else "blocked_no_destination_binding_review_records",
        destination_binding_review_records=records, eligible_for_future_credential_presence_membership_task=ready, eligible_for_future_dispatch_execution_task=False, eligible_for_live_send_now=False,
        destination_binding_present=False, credential_handle_present=False, credential_value_read=False, env_read=False, provider_call_made=False, network_call_made=False, browser_session_used=False,
        executable_request_artifact_created=False, endpoint_url_present=False, webhook_url_present=False, channel_id_present=False, account_id_present=False, token_present=False, payload_body_present=False,
        public_url_created=False, metrics_created=False, publication_ready=False, dispatch_allowed=False, live_send_allowed=False, runtime_truth=False, human_review_required=True, blockers=blockers,
        warnings=["destination_binding_review_scaffold_only", "no_env_read", "no_credential_value_read", "no_provider", "no_dispatch", "no_live_send", "future_dispatch_execution_task_separate"],
    )
    data = asdict(bundle)
    return DestinationBindingReviewScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> DestinationBindingReviewScaffoldBundle:
    bundle = make_destination_binding_review_scaffold_bundle({})
    data = asdict(bundle)
    data["blockers"] = [reason]
    data["destination_binding_review_status"] = "blocked_no_destination_binding_review_records"
    data["packet_sha256"] = _packet_sha(data)
    return DestinationBindingReviewScaffoldBundle(**data)


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 destination binding review scaffold CLI")
    parser.add_argument("--dispatch-gate-scaffold-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        packet = make_destination_binding_review_scaffold_bundle(load_json_object(args.dispatch_gate_scaffold_bundle))
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_credential_presence_membership_task else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
