"""V6 exact operator approval signature verifier scaffold, local-only no-approval no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0"
APPROVAL_MODE = "exact_operator_approval_signature_verifier_scaffold_only"
APPROVAL_SCOPE = "future_payload_hash_approval_signature_shape_only"
EXACT_PHRASE_REQUIRED_LATER = "JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY"
EXACT_PHRASE_PROVIDED_NOW = "NOT_PROVIDED_IN_THIS_SCAFFOLD"

UPSTREAM_FALSE_FLAGS = (
    "eligible_for_future_outbox_preparation_task", "eligible_for_live_send_now", "approval_granted_now",
    "valid_for_outbox", "valid_for_dispatch", "publication_ready", "dispatch_allowed", "live_send_allowed",
    "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used",
    "executable_request_artifact_created", "public_url_created", "metrics_created", "runtime_truth",
)
UPSTREAM_LEDGER_FALSE_FLAGS = (
    "approval_granted_now", "approval_valid_for_payload_hash_preview_only", "approval_valid_for_outbox",
    "approval_valid_for_dispatch", "approval_valid_for_publication", "approval_valid_for_live_send",
)
DECLARATION_FALSE_FLAGS = (
    "approval_hash_binding_present", "payload_hashes_revalidated_now", "destination_binding_present",
    "credential_handle_present", "approval_granted_now", "publication_approved_now", "outbox_approved_now",
    "dispatch_approved_now", "live_send_approved_now", "provider_call_requested", "env_read_requested",
    "credential_value_read_requested", "network_call_requested", "browser_session_requested",
    "executable_request_artifact_requested", "public_url_requested", "metrics_requested",
)
DECLARATION_TRUE_FLAGS = ("outbox_task_requested_later", "dispatch_task_requested_later", "live_send_task_requested_later", "revocation_supported", "human_review_required")
DECLARATION_EMPTY_LISTS = ("approved_payload_preview_ids", "approved_payload_hashes", "approved_platforms")
DECLARATION_FIELDS = {
    "schema_version", "exact_operator_approval_declaration_id", "source_operator_approval_ledger_gate_scaffold_bundle_id",
    "source_payload_hash_preview_approval_prep_bundle_id", "operator_id", "created_at_manual", "approval_mode",
    "approval_scope", "exact_approval_phrase_required", "exact_approval_phrase_provided", "approved_payload_preview_ids",
    "approved_payload_hashes", "approved_platforms", "approval_hash_binding_present", "payload_hashes_revalidated_now",
    "destination_binding_present", "credential_handle_present", "outbox_task_requested_later",
    "dispatch_task_requested_later", "live_send_task_requested_later", "approval_granted_now",
    "publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now",
    "provider_call_requested", "env_read_requested", "credential_value_read_requested", "network_call_requested",
    "browser_session_requested", "executable_request_artifact_requested", "public_url_requested", "metrics_requested",
    "revocation_supported", "expires_at", "human_review_required", "notes",
}

SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)


@dataclass(frozen=True)
class ExactOperatorApprovalSignatureVerifierScaffoldBundle:
    schema_version: str
    task_label: str
    exact_operator_approval_signature_verifier_scaffold_bundle_id: str
    source_operator_approval_ledger_gate_scaffold_bundle_id: str
    future_exact_operator_approval_declaration_template: dict[str, Any]
    future_exact_operator_approval_shape_status: str
    exact_phrase_required_later: str
    exact_phrase_provided_now: str
    approval_granted_now: bool
    approved_payload_preview_ids: list[str]
    approved_payload_hashes: list[str]
    approved_platforms: list[str]
    approval_valid_for_outbox: bool
    approval_valid_for_dispatch: bool
    approval_valid_for_publication: bool
    approval_valid_for_live_send: bool
    eligible_for_future_exact_operator_approval_task: bool
    eligible_for_future_outbox_preparation_task: bool
    eligible_for_live_send_now: bool
    provider_call_made: bool
    env_read: bool
    credential_value_read: bool
    network_call_made: bool
    browser_session_used: bool
    executable_request_artifact_created: bool
    public_url_created: bool
    metrics_created: bool
    publication_ready: bool
    dispatch_allowed: bool
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
        "browser_session_used", "browser_session_requested", "public_url_created", "public_url_requested",
        "metrics_created", "metrics_requested", "live_send_allowed", "eligible_for_live_send_now",
        "live_send_approved_now", "live_send_task_requested_later", "approval_valid_for_live_send",
        "provider_call_made", "provider_call_requested", "network_call_made", "network_call_requested",
        "executable_request_artifact_created", "executable_request_artifact_requested", "credential_value_read",
        "credential_value_read_requested", "credential_handle_present", "destination_binding_present",
        "publication_ready", "publication_approved_now", "dispatch_allowed", "dispatch_approved_now",
    ):
        low = low.replace(safe, "safe_system_term")
    for phrase in (
        "browser path", "public url", "live send", "live-send", "financial advice", "signal service",
        "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction",
        "trading advice", "fake metric", "fake metrics",
    ):
        if phrase in low:
            return False
    for word in ("endpoint", "webhook", "secret", "channel", "account", "cookie", "session", "signal", "metrics"):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return False
    return True


def safety_blockers(obj: dict[str, Any], label: str) -> list[str]:
    blockers: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value):
            blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers


def validate_future_exact_operator_approval_declaration(decl: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(decl, dict):
        return ["declaration_not_object"]
    extra = sorted(set(decl) - DECLARATION_FIELDS)
    _add(blockers, not extra, "declaration_extra_fields")
    for key in sorted(DECLARATION_FIELDS):
        _add(blockers, key in decl, f"missing_declaration_{key}")
    if blockers:
        return blockers
    _add(blockers, decl.get("schema_version") == SCHEMA_VERSION, "declaration_schema_version_invalid")
    _add(blockers, decl.get("approval_mode") == APPROVAL_MODE, "declaration_approval_mode_invalid")
    _add(blockers, decl.get("approval_scope") == APPROVAL_SCOPE, "declaration_approval_scope_invalid")
    _add(blockers, decl.get("exact_approval_phrase_required") == EXACT_PHRASE_REQUIRED_LATER, "declaration_exact_phrase_required_invalid")
    _add(blockers, decl.get("exact_approval_phrase_provided") == EXACT_PHRASE_PROVIDED_NOW, "declaration_exact_phrase_provided_invalid")
    for key in DECLARATION_EMPTY_LISTS:
        _add(blockers, decl.get(key) == [], f"declaration_{key}_not_empty")
    for key in DECLARATION_FALSE_FLAGS:
        _add(blockers, decl.get(key) is False, f"declaration_{key}_not_false")
    for key in DECLARATION_TRUE_FLAGS:
        _add(blockers, decl.get(key) is True, f"declaration_{key}_not_true")
    _add(blockers, decl.get("expires_at") is None or isinstance(decl.get("expires_at"), str), "declaration_expires_at_invalid")
    _add(blockers, isinstance(decl.get("notes"), str), "declaration_notes_not_string")
    blockers.extend(safety_blockers(decl, "declaration"))
    return blockers


def _source_id(source: dict[str, Any]) -> str:
    seed = source.get("operator_approval_ledger_gate_scaffold_bundle_id") or _sha(source)[:16]
    return str(seed)


def make_future_exact_operator_approval_declaration_template(source: dict[str, Any]) -> dict[str, Any]:
    source_id = _source_id(source)
    short = _sha({"source": source_id, "purpose": "exact_operator_approval_declaration_template"})[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "exact_operator_approval_declaration_id": f"exact_operator_approval_declaration_{short}",
        "source_operator_approval_ledger_gate_scaffold_bundle_id": source_id,
        "source_payload_hash_preview_approval_prep_bundle_id": source.get("source_payload_hash_preview_approval_prep_bundle_id", ""),
        "operator_id": "jim",
        "created_at_manual": "manual_timestamp_required_for_operator_record",
        "approval_mode": APPROVAL_MODE,
        "approval_scope": APPROVAL_SCOPE,
        "exact_approval_phrase_required": EXACT_PHRASE_REQUIRED_LATER,
        "exact_approval_phrase_provided": EXACT_PHRASE_PROVIDED_NOW,
        "approved_payload_preview_ids": [],
        "approved_payload_hashes": [],
        "approved_platforms": [],
        "approval_hash_binding_present": False,
        "payload_hashes_revalidated_now": False,
        "destination_binding_present": False,
        "credential_handle_present": False,
        "outbox_task_requested_later": True,
        "dispatch_task_requested_later": True,
        "live_send_task_requested_later": True,
        "approval_granted_now": False,
        "publication_approved_now": False,
        "outbox_approved_now": False,
        "dispatch_approved_now": False,
        "live_send_approved_now": False,
        "provider_call_requested": False,
        "env_read_requested": False,
        "credential_value_read_requested": False,
        "network_call_requested": False,
        "browser_session_requested": False,
        "executable_request_artifact_requested": False,
        "public_url_requested": False,
        "metrics_requested": False,
        "revocation_supported": True,
        "expires_at": None,
        "human_review_required": True,
        "notes": "",
    }


def validate_operator_approval_ledger_gate_scaffold_bundle(bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(bundle, dict):
        return ["upstream_not_object"]
    blockers.extend(safety_blockers(bundle, "upstream"))
    _add(blockers, bundle.get("schema_version") == SCHEMA_VERSION, "upstream_schema_version_invalid")
    _add(blockers, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "upstream_task_label_invalid")
    _add(blockers, isinstance(bundle.get("operator_approval_declaration_scaffold"), dict), "upstream_declaration_scaffold_missing")
    _add(blockers, isinstance(bundle.get("approval_ledger_record_shell"), dict), "upstream_ledger_shell_missing")
    _add(blockers, bundle.get("eligible_for_future_exact_operator_approval_task") is True, "upstream_future_exact_operator_approval_eligibility_not_true")
    for key in UPSTREAM_FALSE_FLAGS:
        _add(blockers, bundle.get(key) is False, f"upstream_{key}_not_false")
    _add(blockers, bundle.get("human_review_required") is True, "upstream_human_review_required_not_true")
    _add(blockers, bundle.get("blockers", []) == [], "upstream_blockers_not_empty")
    decl = bundle.get("operator_approval_declaration_scaffold")
    if isinstance(decl, dict):
        _add(blockers, decl.get("exact_approval_phrase") == "NOT_APPROVED_IN_THIS_SCAFFOLD", "upstream_declaration_phrase_not_scaffold_not_approved")
    shell = bundle.get("approval_ledger_record_shell")
    if isinstance(shell, dict):
        _add(blockers, shell.get("approval_status") == "not_approved", "upstream_ledger_approval_status_not_not_approved")
        for key in UPSTREAM_LEDGER_FALSE_FLAGS:
            _add(blockers, shell.get(key) is False, f"upstream_ledger_{key}_not_false")
    return blockers


def make_exact_operator_approval_signature_verifier_scaffold_bundle(operator_approval_ledger_gate_scaffold_bundle: dict[str, Any]) -> ExactOperatorApprovalSignatureVerifierScaffoldBundle:
    blockers = validate_operator_approval_ledger_gate_scaffold_bundle(operator_approval_ledger_gate_scaffold_bundle)
    template = make_future_exact_operator_approval_declaration_template(operator_approval_ledger_gate_scaffold_bundle if isinstance(operator_approval_ledger_gate_scaffold_bundle, dict) else {})
    blockers.extend(validate_future_exact_operator_approval_declaration(template))
    source_id = _source_id(operator_approval_ledger_gate_scaffold_bundle if isinstance(operator_approval_ledger_gate_scaffold_bundle, dict) else {})
    short = _sha({"source": source_id, "purpose": "exact_operator_approval_signature_verifier_scaffold_bundle"})[:16]
    status = "shape_valid_review_only_no_approval" if not blockers else "blocked_fail_closed_no_approval"
    bundle = ExactOperatorApprovalSignatureVerifierScaffoldBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        exact_operator_approval_signature_verifier_scaffold_bundle_id=f"exact_operator_approval_signature_verifier_scaffold_bundle_{short}",
        source_operator_approval_ledger_gate_scaffold_bundle_id=source_id,
        future_exact_operator_approval_declaration_template=template,
        future_exact_operator_approval_shape_status=status,
        exact_phrase_required_later=EXACT_PHRASE_REQUIRED_LATER,
        exact_phrase_provided_now=EXACT_PHRASE_PROVIDED_NOW,
        approval_granted_now=False,
        approved_payload_preview_ids=[],
        approved_payload_hashes=[],
        approved_platforms=[],
        approval_valid_for_outbox=False,
        approval_valid_for_dispatch=False,
        approval_valid_for_publication=False,
        approval_valid_for_live_send=False,
        eligible_for_future_exact_operator_approval_task=not blockers,
        eligible_for_future_outbox_preparation_task=False,
        eligible_for_live_send_now=False,
        provider_call_made=False,
        env_read=False,
        credential_value_read=False,
        network_call_made=False,
        browser_session_used=False,
        executable_request_artifact_created=False,
        public_url_created=False,
        metrics_created=False,
        publication_ready=False,
        dispatch_allowed=False,
        runtime_truth=False,
        human_review_required=True,
        blockers=blockers,
        warnings=["scaffold_only", "no_operator_approval_granted", "review_only", "no_outbox_or_dispatch_readiness"],
    )
    data = asdict(bundle)
    return ExactOperatorApprovalSignatureVerifierScaffoldBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> ExactOperatorApprovalSignatureVerifierScaffoldBundle:
    packet = make_exact_operator_approval_signature_verifier_scaffold_bundle({})
    data = asdict(packet)
    data["eligible_for_future_exact_operator_approval_task"] = False
    data["blockers"] = [reason]
    data["future_exact_operator_approval_shape_status"] = "blocked_fail_closed_no_approval"
    data["packet_sha256"] = _packet_sha(data)
    return ExactOperatorApprovalSignatureVerifierScaffoldBundle(**data)


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 exact operator approval signature verifier scaffold CLI")
    parser.add_argument("--operator-approval-ledger-gate-scaffold-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        upstream = load_json_object(args.operator_approval_ledger_gate_scaffold_bundle)
        packet = make_exact_operator_approval_signature_verifier_scaffold_bundle(upstream)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_exact_operator_approval_task else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())