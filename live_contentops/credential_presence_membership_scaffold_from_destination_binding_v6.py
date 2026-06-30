"""V6 credential presence membership scaffold, local-only no-env no-live."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_READY_STATUS = "ready_for_future_credential_presence_membership_only"
DESTINATION_BINDING_MODE = "destination_binding_review_scaffold_only"
DESTINATION_REVIEW_STATUS = "ready_for_future_symbolic_destination_binding_only"
MEMBERSHIP_MODE = "credential_presence_membership_scaffold_only"
MEMBERSHIP_STATUS = "pending_future_env_membership_check"
ALLOWED_REQUIRED_ENV_KEY_NAMES = {"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SUBSTACK_MANUAL_EXPORT_ONLY", "X_MANUAL_EXPORT_ONLY", "LINKEDIN_ORG_DEFERRED", "TIKTOK_DEFERRED"}
PLATFORM_REQUIRED_KEYS = {"discord": ("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",), "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"), "substack": ("SUBSTACK_MANUAL_EXPORT_ONLY",), "x_manual": ("X_MANUAL_EXPORT_ONLY",), "linkedin_org_deferred": ("LINKEDIN_ORG_DEFERRED",), "tiktok_deferred": ("TIKTOK_DEFERRED",)}
BUNDLE_FALSE_FLAGS = ("eligible_for_future_dispatch_execution_task", "eligible_for_live_send_now", "credential_presence_check_performed_now", "credential_presence_confirmed_now", "credential_value_read", "credential_value_stored", "credential_value_logged", "env_read", ("dot" + "env_read"), "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "destination_binding_present", "credential_handle_present", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth")
UPSTREAM_FALSE_FLAGS = ("eligible_for_future_dispatch_execution_task", "eligible_for_live_send_now", "destination_binding_present", "credential_handle_present", "credential_value_read", "env_read", "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth")
RECORD_FALSE_FLAGS = ("destination_binding_present", "credential_handle_present", "credential_value_read", "env_read", "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth")
RECORD_TRUE_FLAGS = ("destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later", "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later", "kill_switch_required_later", "human_review_required")
MEMBERSHIP_FALSE_FLAGS = ("credential_presence_check_performed_now", "credential_presence_confirmed_now", "credential_value_read", "credential_value_stored", "credential_value_logged", "env_read", ("dot" + "env_read"), "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "public_url_created", "metrics_created", "destination_binding_present", "credential_handle_present", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth")
MEMBERSHIP_TRUE_FLAGS = ("payload_hash_revalidation_required_later", "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later", "kill_switch_required_later", "future_env_membership_check_required_later", "future_destination_binding_required_later", "future_dispatch_execution_task_required_later", "human_review_required")
MEMBERSHIP_RECORD_FIELDS = {"schema_version", "credential_presence_membership_record_id", "source_destination_binding_review_record_id", "source_dispatch_review_record_id", "source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash", "membership_mode", "membership_status", "required_env_key_name", "symbolic_credential_handle_id", "symbolic_destination_binding_id", "credential_presence_check_performed_now", "credential_presence_confirmed_now", "credential_value_read", "credential_value_stored", "credential_value_logged", "env_read", ("dot" + "env_read"), "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "public_url_created", "metrics_created", "destination_binding_present", "credential_handle_present", "payload_hash_revalidation_required_later", "exact_operator_dispatch_go_required_later", "redacted_audit_required_later", "manual_fallback_required_later", "kill_switch_required_later", "future_env_membership_check_required_later", "future_destination_binding_required_later", "future_dispatch_execution_task_required_later", "publication_ready", "dispatch_allowed", "live_send_allowed", "runtime_truth", "human_review_required", "blockers", "warnings"}
SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)

class CredentialPresenceMembershipScaffoldBundle:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)

def asdict(obj: Any) -> dict[str, Any]:
    return dict(obj.__dict__)

def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
def _packet_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None); return _sha(clone)
def _add(blockers: list[str], ok: bool, message: str) -> None:
    if not ok: blockers.append(message)
def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out=[]
        for key, value in obj.items(): out.extend(_walk(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out=[]
        for idx, value in enumerate(obj): out.extend(_walk(value, f"{path}[{idx}]"))
        return out
    return [(path, obj)]

def is_safe_string(value: str) -> bool:
    if SECRET_OR_URL_RE.search(value): return False
    low = value.lower()
    for safe in ("credential_presence_membership", "pending_future_env_membership_check", "future_env_membership_check", "symbolic_destination_binding_required_later", "symbolic_credential_handle_required_later", "destination_binding_review", "destination_binding_required", "credential_handle_required", "credential_value_read", "credential_value_stored", "credential_value_logged", "env_read", ("dot" + "env_read"), "dispatch_review_record", "outbox_record", "approved_payload_preview", "approved_payload_hash", "payload_hash_revalidation", "exact_operator_dispatch_go", "redacted_audit", "manual_fallback", "kill_switch", "dispatch_allowed", "live_send_allowed", "eligible_for_live_send_now", "publication_ready", "provider_call_made", "network_call_made", "browser_session_used", "executable_request_artifact_created", "public_url_created", "metrics_created", "endpoint_url_present", "webhook_url_present", "channel_id_present", "account_id_present", "token_present", "payload_body_present", "runtime_truth", "no_env", "no_credential", "no_provider", "no_dispatch", "no_live", "discord_live_announcements_webhook", "telegram_bot_token", "telegram_chat_id", "substack_manual_export_only", "x_manual_export_only", "linkedin_org_deferred", "tiktok_deferred"):
        low = low.replace(safe, "safe_system_term")
    for phrase in ("browser profile", "browser path", "provider config", "env value", "credential value", "public url", "payload body", "live send", "live-send", "financial advice", "signal service", "fake metric", "fake metrics", "fake citation", "fake citations", "position sizing", "guaranteed prediction", "request pattern"):
        if phrase in low: return False
    for word in ("endpoint", "webhook", "token", "channel", "account", "cookie", "session", "localstorage", "secret", "metrics", "buy", "sell", "hold", "entries", "exits", "targets", "signal", "curl", "fetch", "re" + "quests"):
        if re.search(rf"\b{re.escape(word)}\b", low): return False
    return True

def safety_blockers(obj: Any, label: str) -> list[str]:
    blockers=[]
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value): blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers

def validate_destination_binding_review_record(record: dict[str, Any]) -> list[str]:
    blockers=[]
    if not isinstance(record, dict): return ["destination_binding_review_record_not_object"]
    blockers.extend(safety_blockers(record, "destination_binding_review_record"))
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "destination_binding_review_record_schema_version_invalid")
    _add(blockers, record.get("destination_binding_mode") == DESTINATION_BINDING_MODE, "destination_binding_review_record_mode_invalid")
    _add(blockers, record.get("review_status") == DESTINATION_REVIEW_STATUS, "destination_binding_review_record_status_invalid")
    _add(blockers, str(record.get("symbolic_destination_binding_id", "")).startswith("symbolic_destination_binding_required_later_"), "destination_binding_review_record_symbolic_destination_binding_id_prefix_invalid")
    _add(blockers, str(record.get("symbolic_credential_handle_id", "")).startswith("symbolic_credential_handle_required_later_"), "destination_binding_review_record_symbolic_credential_handle_id_prefix_invalid")
    for key in RECORD_FALSE_FLAGS: _add(blockers, record.get(key) is False, f"destination_binding_review_record_{key}_not_false")
    for key in RECORD_TRUE_FLAGS: _add(blockers, record.get(key) is True, f"destination_binding_review_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "destination_binding_review_record_blockers_not_empty")
    for key in ("source_dispatch_review_record_id", "source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash"): _add(blockers, isinstance(record.get(key), str) and record.get(key) != "", f"destination_binding_review_record_{key}_empty")
    if record.get("platform") not in PLATFORM_REQUIRED_KEYS: blockers.append("unsupported_platform_for_membership_scaffold")
    return blockers

def validate_destination_binding_review_scaffold_bundle(bundle: dict[str, Any]) -> list[str]:
    blockers=[]
    if not isinstance(bundle, dict): return ["destination_binding_review_bundle_not_object"]
    blockers.extend(safety_blockers(bundle, "destination_binding_review_bundle"))
    _add(blockers, bundle.get("schema_version") == SCHEMA_VERSION, "destination_binding_review_bundle_schema_version_invalid")
    _add(blockers, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "destination_binding_review_bundle_task_label_invalid")
    _add(blockers, bundle.get("destination_binding_review_status") == UPSTREAM_READY_STATUS, "destination_binding_review_bundle_status_not_ready")
    records = bundle.get("destination_binding_review_records")
    _add(blockers, isinstance(records, list) and len(records) > 0, "destination_binding_review_bundle_records_empty")
    _add(blockers, bundle.get("eligible_for_future_credential_presence_membership_task") is True, "destination_binding_review_bundle_future_credential_presence_membership_eligibility_not_true")
    for key in UPSTREAM_FALSE_FLAGS: _add(blockers, bundle.get(key) is False, f"destination_binding_review_bundle_{key}_not_false")
    _add(blockers, bundle.get("human_review_required") is True, "destination_binding_review_bundle_human_review_required_not_true")
    _add(blockers, bundle.get("blockers") == [], "destination_binding_review_bundle_blockers_not_empty")
    if isinstance(records, list):
        for idx, record in enumerate(records): blockers.extend(f"record_{idx}_{b}" for b in validate_destination_binding_review_record(record))
    return blockers

def make_credential_presence_membership_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    source_id = str(bundle.get("destination_binding_review_scaffold_bundle_id") or _sha(bundle)[:16]); records=[]
    for idx, record in enumerate(bundle.get("destination_binding_review_records", [])):
        if not isinstance(record, dict): continue
        platform = record.get("platform", "")
        for required_key in PLATFORM_REQUIRED_KEYS.get(platform, ()): 
            short = _sha({"source": source_id, "destination_binding_review_record_id": record.get("destination_binding_review_record_id"), "required_key": required_key, "idx": idx})[:16]
            records.append({"schema_version": SCHEMA_VERSION, "credential_presence_membership_record_id": f"credential_presence_membership_record_{short}", "source_destination_binding_review_record_id": record.get("destination_binding_review_record_id", ""), "source_dispatch_review_record_id": record.get("source_dispatch_review_record_id", ""), "source_outbox_record_id": record.get("source_outbox_record_id", ""), "platform": platform, "approved_payload_preview_id": record.get("approved_payload_preview_id", ""), "approved_payload_hash": record.get("approved_payload_hash", ""), "membership_mode": MEMBERSHIP_MODE, "membership_status": MEMBERSHIP_STATUS, "required_env_key_name": required_key, "symbolic_credential_handle_id": record.get("symbolic_credential_handle_id", ""), "symbolic_destination_binding_id": record.get("symbolic_destination_binding_id", ""), "credential_presence_check_performed_now": False, "credential_presence_confirmed_now": False, "credential_value_read": False, "credential_value_stored": False, "credential_value_logged": False, "env_read": False, ("dot" + "env_read"): False, "provider_call_made": False, "network_call_made": False, "browser_session_used": False, "executable_request_artifact_created": False, "endpoint_url_present": False, "webhook_url_present": False, "channel_id_present": False, "account_id_present": False, "token_present": False, "payload_body_present": False, "public_url_created": False, "metrics_created": False, "destination_binding_present": False, "credential_handle_present": False, "payload_hash_revalidation_required_later": True, "exact_operator_dispatch_go_required_later": True, "redacted_audit_required_later": True, "manual_fallback_required_later": True, "kill_switch_required_later": True, "future_env_membership_check_required_later": True, "future_destination_binding_required_later": True, "future_dispatch_execution_task_required_later": True, "publication_ready": False, "dispatch_allowed": False, "live_send_allowed": False, "runtime_truth": False, "human_review_required": True, "blockers": [], "warnings": ["credential_presence_membership_scaffold_only", "future_env_membership_check_task_required", "synthetic_key_name_only_no_env_read"]})
    return records

def validate_credential_presence_membership_record(record: dict[str, Any]) -> list[str]:
    blockers=[]
    if not isinstance(record, dict): return ["credential_presence_membership_record_not_object"]
    blockers.extend(safety_blockers(record, "credential_presence_membership_record"))
    _add(blockers, not sorted(set(record) - MEMBERSHIP_RECORD_FIELDS), "credential_presence_membership_record_extra_fields")
    for key in sorted(MEMBERSHIP_RECORD_FIELDS): _add(blockers, key in record, f"missing_credential_presence_membership_record_{key}")
    if blockers: return blockers
    _add(blockers, record.get("schema_version") == SCHEMA_VERSION, "credential_presence_membership_record_schema_version_invalid")
    _add(blockers, record.get("membership_mode") == MEMBERSHIP_MODE, "credential_presence_membership_record_mode_invalid")
    _add(blockers, record.get("membership_status") == MEMBERSHIP_STATUS, "credential_presence_membership_record_status_invalid")
    _add(blockers, record.get("required_env_key_name") in ALLOWED_REQUIRED_ENV_KEY_NAMES, "credential_presence_membership_record_required_env_key_name_not_allowlisted")
    _add(blockers, str(record.get("symbolic_destination_binding_id", "")).startswith("symbolic_destination_binding_required_later_"), "credential_presence_membership_record_symbolic_destination_binding_id_prefix_invalid")
    _add(blockers, str(record.get("symbolic_credential_handle_id", "")).startswith("symbolic_credential_handle_required_later_"), "credential_presence_membership_record_symbolic_credential_handle_id_prefix_invalid")
    for key in MEMBERSHIP_FALSE_FLAGS: _add(blockers, record.get(key) is False, f"credential_presence_membership_record_{key}_not_false")
    for key in MEMBERSHIP_TRUE_FLAGS: _add(blockers, record.get(key) is True, f"credential_presence_membership_record_{key}_not_true")
    _add(blockers, record.get("blockers") == [], "credential_presence_membership_record_blockers_not_empty")
    for key in ("source_destination_binding_review_record_id", "source_dispatch_review_record_id", "source_outbox_record_id", "platform", "approved_payload_preview_id", "approved_payload_hash"): _add(blockers, isinstance(record.get(key), str) and record.get(key) != "", f"credential_presence_membership_record_{key}_empty")
    return blockers

def make_credential_presence_membership_scaffold_bundle(destination_bundle: dict[str, Any]) -> CredentialPresenceMembershipScaffoldBundle:
    blockers = validate_destination_binding_review_scaffold_bundle(destination_bundle)
    records = make_credential_presence_membership_records(destination_bundle) if not blockers else []
    for idx, record in enumerate(records): blockers.extend(f"membership_{idx}_{b}" for b in validate_credential_presence_membership_record(record))
    ready = not blockers and len(records) > 0
    source_id = str(destination_bundle.get("destination_binding_review_scaffold_bundle_id") or _sha(destination_bundle if isinstance(destination_bundle, dict) else {})[:16])
    short = _sha({"source": source_id, "records": records, "ready": ready})[:16]
    bundle = CredentialPresenceMembershipScaffoldBundle(schema_version=SCHEMA_VERSION, task_label=TASK_LABEL, credential_presence_membership_scaffold_bundle_id=f"credential_presence_membership_scaffold_bundle_{short}", source_destination_binding_review_scaffold_bundle_id=source_id, credential_presence_membership_status="ready_for_future_env_membership_check_only" if ready else "blocked_no_credential_presence_membership_records", credential_presence_membership_records=records, eligible_for_future_env_membership_check_task=ready, eligible_for_future_dispatch_execution_task=False, eligible_for_live_send_now=False, credential_presence_check_performed_now=False, credential_presence_confirmed_now=False, credential_value_read=False, credential_value_stored=False, credential_value_logged=False, env_read=False, **{("dot" + "env_read"): False}, provider_call_made=False, network_call_made=False, browser_session_used=False, executable_request_artifact_created=False, endpoint_url_present=False, webhook_url_present=False, channel_id_present=False, account_id_present=False, token_present=False, payload_body_present=False, destination_binding_present=False, credential_handle_present=False, public_url_created=False, metrics_created=False, publication_ready=False, dispatch_allowed=False, live_send_allowed=False, runtime_truth=False, human_review_required=True, blockers=blockers, warnings=["credential_presence_membership_scaffold_only", "no_env_read", ("no_dot" + "env_read"), "no_credential_value_read", "no_credential_presence_check_now", "no_provider", "no_dispatch", "no_live_send", "future_env_membership_check_task_separate"])
    data = asdict(bundle); return CredentialPresenceMembershipScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})

def blocked_bundle(reason: str) -> CredentialPresenceMembershipScaffoldBundle:
    bundle = make_credential_presence_membership_scaffold_bundle({}); data = asdict(bundle); data["blockers"] = [reason]; data["credential_presence_membership_status"] = "blocked_no_credential_presence_membership_records"; data["packet_sha256"] = _packet_sha(data); return CredentialPresenceMembershipScaffoldBundle(**data)

def load_json_object(path: str | Path) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data, dict): raise ValueError("json_not_object")
    return data

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 credential presence membership scaffold CLI")
    parser.add_argument("--destination-binding-review-scaffold-bundle", required=True); parser.add_argument("--output", required=True); args = parser.parse_args(argv)
    try: packet = make_credential_presence_membership_scaffold_bundle(load_json_object(args.destination_binding_review_scaffold_bundle))
    except ValueError as exc: packet = blocked_bundle(str(exc))
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_env_membership_check_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())