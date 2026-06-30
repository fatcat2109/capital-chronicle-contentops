"""V6 Operator Approval Ledger Gate Scaffold, local-only no-approval no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
APPROVAL_MODE = "operator_approval_gate_scaffold_only"
APPROVAL_SCOPE = "payload_hash_preview_review_only"
RECORD_MODE = "scaffold_only_no_approval"

HARD_FALSE_FLAGS = ("eligible_for_live_send_now", "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "runtime_truth")
DECLARATION_FALSE_FLAGS = ("approval_granted_now", "publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now", "provider_call_requested", "env_read_requested", "credential_value_read_requested", "network_call_requested", "browser_session_requested", "executable_request_artifact_requested", "public_url_requested", "metrics_requested", "destination_binding_present", "credential_handle_present", "payload_hash_revalidation_performed")
LEDGER_FALSE_FLAGS = ("approval_granted_now", "approval_valid_for_payload_hash_preview_only", "approval_valid_for_outbox", "approval_valid_for_dispatch", "approval_valid_for_publication", "approval_valid_for_live_send")
LEDGER_TRUE_FLAGS = ("destination_binding_required_later", "credential_handle_required_later", "payload_hash_revalidation_required_later", "explicit_outbox_task_required_later", "explicit_live_send_task_required_later", "revocation_supported", "human_review_required")

DECLARATION_FIELDS = {
    "schema_version", "operator_approval_declaration_id", "source_payload_hash_preview_approval_prep_bundle_id",
    "operator_id", "created_at_manual", "approval_mode", "approval_scope", "exact_approval_phrase",
    "approved_payload_preview_ids", "approved_payload_hashes", "approved_platforms", "approval_granted_now",
    "publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now",
    "provider_call_requested", "env_read_requested", "credential_value_read_requested", "network_call_requested",
    "browser_session_requested", "executable_request_artifact_requested", "public_url_requested", "metrics_requested",
    "destination_binding_present", "credential_handle_present", "payload_hash_revalidation_performed", "expires_at",
    "revocation_supported", "human_review_required", "notes"
}

SECRET_OR_URL_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)

@dataclass(frozen=True)
class OperatorApprovalDeclarationScaffold:
    schema_version: str
    operator_approval_declaration_id: str
    source_payload_hash_preview_approval_prep_bundle_id: str
    operator_id: str
    created_at_manual: str
    approval_mode: str
    approval_scope: str
    exact_approval_phrase: str
    approved_payload_preview_ids: list[str]
    approved_payload_hashes: list[str]
    approved_platforms: list[str]
    approval_granted_now: bool
    publication_approved_now: bool
    outbox_approved_now: bool
    dispatch_approved_now: bool
    live_send_approved_now: bool
    provider_call_requested: bool
    env_read_requested: bool
    credential_value_read_requested: bool
    network_call_requested: bool
    browser_session_requested: bool
    executable_request_artifact_requested: bool
    public_url_requested: bool
    metrics_requested: bool
    destination_binding_present: bool
    credential_handle_present: bool
    payload_hash_revalidation_performed: bool
    expires_at: str | None
    revocation_supported: bool
    human_review_required: bool
    notes: str

@dataclass(frozen=True)
class ApprovalLedgerRecordShell:
    schema_version: str
    approval_ledger_record_shell_id: str
    source_payload_hash_preview_approval_prep_bundle_id: str
    source_approval_ledger_prep_id: str
    operator_approval_declaration_id: str
    approval_record_mode: str
    approval_status: str
    approval_granted_now: bool
    approval_valid_for_payload_hash_preview_only: bool
    approval_valid_for_outbox: bool
    approval_valid_for_dispatch: bool
    approval_valid_for_publication: bool
    approval_valid_for_live_send: bool
    approved_payload_preview_ids: list[str]
    approved_payload_hashes: list[str]
    approved_platforms: list[str]
    destination_binding_required_later: bool
    credential_handle_required_later: bool
    payload_hash_revalidation_required_later: bool
    explicit_outbox_task_required_later: bool
    explicit_live_send_task_required_later: bool
    revocation_supported: bool
    human_review_required: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class OperatorApprovalLedgerGateScaffoldBundle:
    schema_version: str
    task_label: str
    operator_approval_ledger_gate_scaffold_bundle_id: str
    source_payload_hash_preview_approval_prep_bundle_id: str
    operator_approval_declaration_scaffold: dict[str, Any]
    approval_ledger_record_shell: dict[str, Any]
    eligible_for_future_exact_operator_approval_task: bool
    eligible_for_future_outbox_preparation_task: bool
    eligible_for_live_send_now: bool
    approval_granted_now: bool
    valid_for_outbox: bool
    valid_for_dispatch: bool
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
    clone = dict(payload); clone.pop("packet_sha256", None)
    return _sha(clone)

def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out: list[tuple[str, Any]] = []
        for key, value in obj.items(): out.extend(_walk(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, value in enumerate(obj): out.extend(_walk(value, f"{path}[{idx}]"))
        return out
    return [(path, obj)]

def is_safe_string(val: str) -> bool:
    low = val.lower()
    
    if SECRET_OR_URL_RE.search(val):
        return False
        
    clean_low = low
    safe_terms = (
        "browser_session",
        "webhook_adapter",
        "announcements_webhook",
        "webhook_url_included",
        "webhook_token_included",
        "endpoint_url_included",
        "endpoint_or_webhook",
        "live_send_now",
        "live_send_allowed",
        "live_send_approved",
        "live_send_task",
        "valid_for_live_send",
        "approval_valid_for_live_send",
        "publication_approved",
        "publication_ready",
        "dispatch_allowed",
        "dispatch_approved",
        "dispatch_ready",
        "provider_call_made",
        "provider_call_requested",
        "executable_request_artifact_created",
        "executable_request_artifact_requested",
        "public_url_created",
        "public_url_requested",
        "metrics_created",
        "metrics_requested",
        "env_read_requested",
        "credential_value_read_requested",
        "not_approved_in_this_scaffold",
        "operator_approval_gate_scaffold_only",
        "payload_hash_preview_review_only",
        "scaffold_only_no_approval",
        "not_approved",
    )
    for term in safe_terms:
        clean_low = clean_low.replace(term, "safe_system_term")
        
    # Check substrings
    substring_forbidden = (
        "fake citation", "fake metric", "fake metrics", "financial advice", "signal service",
        "position sizing", "guaranteed prediction", "model says", "ai guarantees", "publication approved",
        "dispatch allowed", "live send", "executable request", "public url", "publication ready",
        "dispatch ready", "live send ready", "model authority", "live dispatch claim"
    )
    for f in substring_forbidden:
        if f in clean_low:
            return False
            
    # Check whole words only using word boundary regex
    whole_word_forbidden = (
        "buy", "sell", "hold", "entries", "exits", "targets", "cookie", "session",
        "localstorage", "webhook", "endpoint", "secret", "live-send"
    )
    for w in whole_word_forbidden:
        pattern = rf"\b{re.escape(w)}\b"
        if re.search(pattern, clean_low):
            return False
            
    return True

def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk(obj):
        if isinstance(value, str):
            if not is_safe_string(value):
                if SECRET_OR_URL_RE.search(value):
                    raise ValueError(f"{label}_forbidden_value:{path}")
                else:
                    raise ValueError(f"{label}_forbidden_text:{path}")

def _add(blockers: list[str], ok: bool, message: str) -> None:
    if not ok: blockers.append(message)

def _upstream_blockers(bundle: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, bundle.get("schema_version") == SCHEMA_VERSION, "upstream_schema_version_invalid")
    _add(b, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "upstream_task_label_invalid")
    _add(b, isinstance(bundle.get("payload_previews"), list) and len(bundle.get("payload_previews", [])) > 0, "upstream_previews_missing_or_empty")
    _add(b, isinstance(bundle.get("approval_ledger_preparation_candidate"), dict), "upstream_approval_candidate_missing")
    _add(b, bundle.get("eligible_for_future_operator_approval_task") is True, "upstream_operator_approval_eligibility_not_true")
    _add(b, bundle.get("eligible_for_future_outbox_preparation_task") is False, "upstream_outbox_prep_eligibility_not_false")
    for flag in HARD_FALSE_FLAGS:
        _add(b, bundle.get(flag) is False, f"upstream_{flag}_not_false")
    _add(b, bundle.get("human_review_required") is True, "upstream_human_review_required_not_true")
    _add(b, bundle.get("blockers", []) == [], "upstream_blockers_not_empty")
    
    cand = bundle.get("approval_ledger_preparation_candidate", {})
    if isinstance(cand, dict):
        _add(b, cand.get("approval_status") == "not_approved", "upstream_candidate_status_not_not_approved")
        for flag in ("approval_granted_now", "valid_for_outbox", "valid_for_dispatch", "publication_ready", "dispatch_allowed", "live_send_allowed"):
            _add(b, cand.get(flag) is False, f"upstream_candidate_{flag}_not_false")
            
    return b


def validate_operator_approval_declaration(decl: dict[str, Any]) -> list[str]:
    b: list[str] = []
    extra = sorted(set(decl) - DECLARATION_FIELDS)
    _add(b, not extra, "declaration_extra_fields")
    for key in DECLARATION_FIELDS:
        _add(b, key in decl, f"missing_declaration_{key}")
    return b

def make_operator_approval_ledger_gate_scaffold_bundle(
    payload_hash_prep_bundle: dict[str, Any]
) -> OperatorApprovalLedgerGateScaffoldBundle:
    _assert_safe(payload_hash_prep_bundle, "payload_hash_prep_bundle")
    
    upstream = _upstream_blockers(payload_hash_prep_bundle)
    blockers = upstream[:]
    
    prep_bundle_id = str(payload_hash_prep_bundle.get("payload_hash_preview_approval_prep_bundle_id", ""))
    cand = payload_hash_prep_bundle.get("approval_ledger_preparation_candidate", {})
    cand_prep_id = str(cand.get("approval_ledger_prep_id", "")) if isinstance(cand, dict) else ""
    
    decl_id = "operator_approval_declaration_" + _sha(prep_bundle_id)[:16]
    decl = OperatorApprovalDeclarationScaffold(
        schema_version=SCHEMA_VERSION,
        operator_approval_declaration_id=decl_id,
        source_payload_hash_preview_approval_prep_bundle_id=prep_bundle_id,
        operator_id="jim",
        created_at_manual="manual_timestamp_required_for_operator_record",
        approval_mode=APPROVAL_MODE,
        approval_scope=APPROVAL_SCOPE,
        exact_approval_phrase="NOT_APPROVED_IN_THIS_SCAFFOLD",
        approved_payload_preview_ids=[],
        approved_payload_hashes=[],
        approved_platforms=[],
        approval_granted_now=False,
        publication_approved_now=False,
        outbox_approved_now=False,
        dispatch_approved_now=False,
        live_send_approved_now=False,
        provider_call_requested=False,
        env_read_requested=False,
        credential_value_read_requested=False,
        network_call_requested=False,
        browser_session_requested=False,
        executable_request_artifact_requested=False,
        public_url_requested=False,
        metrics_requested=False,
        destination_binding_present=False,
        credential_handle_present=False,
        payload_hash_revalidation_performed=False,
        expires_at=None,
        revocation_supported=True,
        human_review_required=True,
        notes=""
    )
    
    shell_id = "approval_ledger_record_shell_" + _sha(prep_bundle_id)[:16]
    shell = ApprovalLedgerRecordShell(
        schema_version=SCHEMA_VERSION,
        approval_ledger_record_shell_id=shell_id,
        source_payload_hash_preview_approval_prep_bundle_id=prep_bundle_id,
        source_approval_ledger_prep_id=cand_prep_id,
        operator_approval_declaration_id=decl_id,
        approval_record_mode=RECORD_MODE,
        approval_status="not_approved",
        approval_granted_now=False,
        approval_valid_for_payload_hash_preview_only=False,
        approval_valid_for_outbox=False,
        approval_valid_for_dispatch=False,
        approval_valid_for_publication=False,
        approval_valid_for_live_send=False,
        approved_payload_preview_ids=[],
        approved_payload_hashes=[],
        approved_platforms=[],
        destination_binding_required_later=True,
        credential_handle_required_later=True,
        payload_hash_revalidation_required_later=True,
        explicit_outbox_task_required_later=True,
        explicit_live_send_task_required_later=True,
        revocation_supported=True,
        human_review_required=True,
        blockers=[],
        warnings=["not_approved", "scaffold_only_no_approval", "human_review_required"]
    )
    
    decl_dict = asdict(decl)
    shell_dict = asdict(shell)
    
    if blockers:
        shell_dict = {
            **shell_dict,
            "blockers": blockers[:],
            "approval_status": "blocked"
        }
        
    eligible = not blockers
    bundle_id = "operator_approval_ledger_gate_scaffold_bundle_" + _sha(prep_bundle_id)[:16]
    
    bundle = OperatorApprovalLedgerGateScaffoldBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        operator_approval_ledger_gate_scaffold_bundle_id=bundle_id,
        source_payload_hash_preview_approval_prep_bundle_id=prep_bundle_id,
        operator_approval_declaration_scaffold=decl_dict,
        approval_ledger_record_shell=shell_dict,
        eligible_for_future_exact_operator_approval_task=eligible,
        eligible_for_future_outbox_preparation_task=False,
        eligible_for_live_send_now=False,
        approval_granted_now=False,
        valid_for_outbox=False,
        valid_for_dispatch=False,
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
        warnings=["scaffold_only", "no_operator_approval_granted", "human_review_required"]
    )
    
    data = asdict(bundle)
    return OperatorApprovalLedgerGateScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})

def blocked_bundle(reason: str) -> OperatorApprovalLedgerGateScaffoldBundle:
    empty: dict[str, Any] = {}
    bundle = OperatorApprovalLedgerGateScaffoldBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        operator_approval_ledger_gate_scaffold_bundle_id="operator_approval_ledger_gate_scaffold_bundle_blocked",
        source_payload_hash_preview_approval_prep_bundle_id="",
        operator_approval_declaration_scaffold=empty,
        approval_ledger_record_shell=empty,
        eligible_for_future_exact_operator_approval_task=False,
        eligible_for_future_outbox_preparation_task=False,
        eligible_for_live_send_now=False,
        approval_granted_now=False,
        valid_for_outbox=False,
        valid_for_dispatch=False,
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
        blockers=[reason],
        warnings=["blocked_fail_closed"]
    )
    data = asdict(bundle)
    return OperatorApprovalLedgerGateScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})

def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator approval ledger gate scaffold CLI")
    parser.add_argument("--payload-hash-prep-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    
    try:
        prep_bundle = load_json_object(args.payload_hash_prep_bundle)
        packet = make_operator_approval_ledger_gate_scaffold_bundle(prep_bundle)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
        
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_exact_operator_approval_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
