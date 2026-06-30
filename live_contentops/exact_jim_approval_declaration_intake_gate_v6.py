"""V6 exact Jim approval declaration intake gate, local-only no-provider no-live-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND_V0"
APPROVAL_MODE = "exact_jim_approval_declaration_intake_only"
APPROVAL_SCOPE = "payload_hashes_for_future_outbox_preparation_only"
EXACT_APPROVAL_PHRASE = "JIM_APPROVES_PAYLOAD_HASHES_FOR_FUTURE_OUTBOX_PREP_ONLY"
DEFAULT_PROVIDED_PHRASE = "NOT_PROVIDED_IN_THIS_INTAKE_SAMPLE"

UPSTREAM_FALSE_FLAGS = (
    "eligible_for_future_outbox_preparation_task", "eligible_for_live_send_now", "approval_granted_now",
    "approval_valid_for_outbox", "approval_valid_for_dispatch", "approval_valid_for_publication", "approval_valid_for_live_send",
    "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used",
    "executable_request_artifact_created", "public_url_created", "metrics_created", "publication_ready",
    "dispatch_allowed", "runtime_truth",
)
DECLARATION_FIELDS = {
    "schema_version", "jim_approval_declaration_id", "source_exact_operator_approval_signature_verifier_scaffold_bundle_id",
    "source_payload_hash_preview_approval_prep_bundle_id", "operator_id", "created_at_manual", "approval_mode",
    "approval_scope", "exact_approval_phrase_required", "exact_approval_phrase_provided", "approved_payload_preview_ids",
    "approved_payload_hashes", "approved_platforms", "approval_hash_binding_present", "payload_hashes_revalidated_now",
    "payload_hash_revalidation_report_id", "destination_binding_present", "destination_binding_id",
    "credential_handle_present", "credential_handle_id", "approval_granted_now", "publication_approved_now",
    "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now", "provider_call_requested",
    "env_read_requested", "credential_value_read_requested", "network_call_requested", "browser_session_requested",
    "executable_request_artifact_requested", "public_url_requested", "metrics_requested", "revocation_supported",
    "expires_at", "human_review_required", "notes",
}
DECLARATION_REQUIRED_NON_EMPTY_LISTS = ("approved_payload_preview_ids", "approved_payload_hashes", "approved_platforms")
DECLARATION_FALSE_FLAGS = (
    "publication_approved_now", "outbox_approved_now", "dispatch_approved_now", "live_send_approved_now",
    "provider_call_requested", "env_read_requested", "credential_value_read_requested", "network_call_requested",
    "browser_session_requested", "executable_request_artifact_requested", "public_url_requested", "metrics_requested",
    "destination_binding_present", "credential_handle_present",
)
DECLARATION_TRUE_FLAGS = (
    "approval_hash_binding_present", "payload_hashes_revalidated_now", "approval_granted_now",
    "revocation_supported", "human_review_required",
)

SECRET_OR_URL_RE = re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)


@dataclass(frozen=True)
class ExactJimApprovalDeclarationIntakeGateBundle:
    schema_version: str
    task_label: str
    exact_jim_approval_declaration_intake_gate_bundle_id: str
    source_exact_operator_approval_signature_verifier_scaffold_bundle_id: str
    approval_declaration_status: str
    approval_declaration_validation_result: dict[str, Any]
    approval_granted_now: bool
    approved_payload_preview_ids: list[str]
    approved_payload_hashes: list[str]
    approved_platforms: list[str]
    approval_valid_for_payload_hashes_only: bool
    eligible_for_future_outbox_preparation_task: bool
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
        "browser_session_used", "browser_session_requested", "public_url_created", "public_url_requested",
        "metrics_created", "metrics_requested", "eligible_for_live_send_now", "live_send_allowed",
        "live_send_approved_now", "approval_valid_for_live_send", "provider_call_made", "provider_call_requested",
        "network_call_made", "network_call_requested", "executable_request_artifact_created",
        "executable_request_artifact_requested", "credential_value_read", "credential_value_read_requested",
        "credential_handle_present", "destination_binding_present", "publication_ready", "publication_approved_now",
        "dispatch_allowed", "dispatch_approved_now",
    ):
        low = low.replace(safe, "safe_system_term")
    for phrase in (
        "browser path", "public url", "live send", "live-send", "financial advice", "signal service",
        "position sizing", "guaranteed prediction", "trading advice", "fake metric", "fake metrics",
    ):
        if phrase in low:
            return False
    for word in ("endpoint", "webhook", "secret", "channel", "account", "cookie", "session", "signal", "metrics", "buy", "sell", "hold", "entries", "exits", "targets"):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return False
    return True


def safety_blockers(obj: dict[str, Any], label: str) -> list[str]:
    blockers: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str) and not is_safe_string(value):
            blockers.append(f"{label}_forbidden_value:{path}" if SECRET_OR_URL_RE.search(value) else f"{label}_forbidden_text:{path}")
    return blockers


def _source_id(verifier_bundle: dict[str, Any]) -> str:
    return str(verifier_bundle.get("exact_operator_approval_signature_verifier_scaffold_bundle_id") or _sha(verifier_bundle)[:16])


def validate_verifier_scaffold_bundle(verifier_bundle: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(verifier_bundle, dict):
        return ["upstream_not_object"]
    blockers.extend(safety_blockers(verifier_bundle, "upstream"))
    _add(blockers, verifier_bundle.get("schema_version") == SCHEMA_VERSION, "upstream_schema_version_invalid")
    _add(blockers, verifier_bundle.get("task_label", UPSTREAM_TASK_LABEL) == UPSTREAM_TASK_LABEL, "upstream_task_label_invalid")
    _add(blockers, isinstance(verifier_bundle.get("future_exact_operator_approval_declaration_template"), dict), "upstream_declaration_template_missing")
    _add(blockers, verifier_bundle.get("eligible_for_future_exact_operator_approval_task") is True, "upstream_future_exact_operator_approval_eligibility_not_true")
    for key in UPSTREAM_FALSE_FLAGS:
        _add(blockers, verifier_bundle.get(key) is False, f"upstream_{key}_not_false")
    _add(blockers, verifier_bundle.get("approved_payload_preview_ids") == [], "upstream_approved_payload_preview_ids_not_empty")
    _add(blockers, verifier_bundle.get("approved_payload_hashes") == [], "upstream_approved_payload_hashes_not_empty")
    _add(blockers, verifier_bundle.get("approved_platforms") == [], "upstream_approved_platforms_not_empty")
    _add(blockers, verifier_bundle.get("human_review_required") is True, "upstream_human_review_required_not_true")
    _add(blockers, verifier_bundle.get("blockers", []) == [], "upstream_blockers_not_empty")
    _add(blockers, verifier_bundle.get("exact_phrase_required_later") == EXACT_APPROVAL_PHRASE, "upstream_exact_phrase_required_later_invalid")
    _add(blockers, verifier_bundle.get("exact_phrase_provided_now") == "NOT_PROVIDED_IN_THIS_SCAFFOLD", "upstream_exact_phrase_provided_now_invalid")
    return blockers


def allowed_platforms_from_upstream(verifier_bundle: dict[str, Any]) -> set[str]:
    previews = verifier_bundle.get("payload_previews")
    if not isinstance(previews, list):
        return set()
    out = set()
    for preview in previews:
        if isinstance(preview, dict) and isinstance(preview.get("platform"), str):
            out.add(preview["platform"])
    return out


def validate_jim_approval_declaration(declaration: dict[str, Any] | None, verifier_bundle: dict[str, Any]) -> list[str]:
    if declaration is None:
        return ["approval_declaration_missing"]
    blockers: list[str] = []
    if not isinstance(declaration, dict):
        return ["approval_declaration_not_object"]
    blockers.extend(safety_blockers(declaration, "declaration"))
    extra = sorted(set(declaration) - DECLARATION_FIELDS)
    _add(blockers, not extra, "declaration_extra_fields")
    for key in sorted(DECLARATION_FIELDS):
        _add(blockers, key in declaration, f"missing_declaration_{key}")
    if blockers:
        return blockers
    _add(blockers, declaration.get("schema_version") == SCHEMA_VERSION, "declaration_schema_version_invalid")
    _add(blockers, declaration.get("source_exact_operator_approval_signature_verifier_scaffold_bundle_id") == _source_id(verifier_bundle), "declaration_source_verifier_id_mismatch")
    _add(blockers, declaration.get("operator_id") == "jim", "declaration_operator_id_not_jim")
    _add(blockers, declaration.get("approval_mode") == APPROVAL_MODE, "declaration_approval_mode_invalid")
    _add(blockers, declaration.get("approval_scope") == APPROVAL_SCOPE, "declaration_approval_scope_invalid")
    _add(blockers, declaration.get("exact_approval_phrase_required") == EXACT_APPROVAL_PHRASE, "declaration_exact_phrase_required_invalid")
    _add(blockers, declaration.get("exact_approval_phrase_provided") == EXACT_APPROVAL_PHRASE, "declaration_exact_phrase_provided_mismatch")
    for key in DECLARATION_REQUIRED_NON_EMPTY_LISTS:
        _add(blockers, isinstance(declaration.get(key), list) and len(declaration[key]) > 0, f"declaration_{key}_empty")
    allowed_platforms = allowed_platforms_from_upstream(verifier_bundle)
    if allowed_platforms and isinstance(declaration.get("approved_platforms"), list):
        unknown = [p for p in declaration["approved_platforms"] if p not in allowed_platforms]
        _add(blockers, not unknown, "declaration_approved_platforms_not_in_upstream_previews")
    for key in DECLARATION_TRUE_FLAGS:
        _add(blockers, declaration.get(key) is True, f"declaration_{key}_not_true")
    for key in DECLARATION_FALSE_FLAGS:
        _add(blockers, declaration.get(key) is False, f"declaration_{key}_not_false")
    _add(blockers, declaration.get("payload_hash_revalidation_report_id") not in (None, ""), "declaration_payload_hash_revalidation_report_id_empty")
    _add(blockers, declaration.get("destination_binding_id") is None, "declaration_destination_binding_id_not_null")
    _add(blockers, declaration.get("credential_handle_id") is None, "declaration_credential_handle_id_not_null")
    _add(blockers, isinstance(declaration.get("expires_at"), str) and declaration.get("expires_at") != "", "declaration_expires_at_missing")
    _add(blockers, isinstance(declaration.get("notes"), str), "declaration_notes_not_string")
    return blockers


def make_default_placeholder_declaration(verifier_bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "jim_approval_declaration_id": "jim_approval_declaration_placeholder_not_approved",
        "source_exact_operator_approval_signature_verifier_scaffold_bundle_id": _source_id(verifier_bundle),
        "source_payload_hash_preview_approval_prep_bundle_id": verifier_bundle.get("future_exact_operator_approval_declaration_template", {}).get("source_payload_hash_preview_approval_prep_bundle_id", "") if isinstance(verifier_bundle.get("future_exact_operator_approval_declaration_template"), dict) else "",
        "operator_id": "jim",
        "created_at_manual": "manual_timestamp_required_for_operator_record",
        "approval_mode": APPROVAL_MODE,
        "approval_scope": APPROVAL_SCOPE,
        "exact_approval_phrase_required": EXACT_APPROVAL_PHRASE,
        "exact_approval_phrase_provided": DEFAULT_PROVIDED_PHRASE,
        "approved_payload_preview_ids": [],
        "approved_payload_hashes": [],
        "approved_platforms": [],
        "approval_hash_binding_present": False,
        "payload_hashes_revalidated_now": False,
        "payload_hash_revalidation_report_id": "",
        "destination_binding_present": False,
        "destination_binding_id": None,
        "credential_handle_present": False,
        "credential_handle_id": None,
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
        "notes": "placeholder_not_approved_no_real_phrase",
    }


def make_exact_jim_approval_declaration_intake_gate_bundle(verifier_bundle: dict[str, Any], jim_approval_declaration: dict[str, Any] | None = None) -> ExactJimApprovalDeclarationIntakeGateBundle:
    upstream_blockers = validate_verifier_scaffold_bundle(verifier_bundle)
    declaration_supplied = jim_approval_declaration is not None
    declaration = jim_approval_declaration if declaration_supplied else make_default_placeholder_declaration(verifier_bundle if isinstance(verifier_bundle, dict) else {})
    declaration_blockers = validate_jim_approval_declaration(declaration, verifier_bundle if isinstance(verifier_bundle, dict) else {}) if declaration_supplied else ["approval_declaration_missing"]
    blockers = upstream_blockers + declaration_blockers
    accepted = declaration_supplied and not blockers
    source_id = _source_id(verifier_bundle if isinstance(verifier_bundle, dict) else {})
    short = _sha({"source": source_id, "declaration": declaration, "accepted": accepted})[:16]
    result = {
        "declaration_supplied": declaration_supplied,
        "valid": accepted,
        "blockers": blockers,
        "synthetic_test_fixture_only": bool(isinstance(declaration, dict) and declaration.get("synthetic_test_fixture_only") is True),
    }
    bundle = ExactJimApprovalDeclarationIntakeGateBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        exact_jim_approval_declaration_intake_gate_bundle_id=f"exact_jim_approval_declaration_intake_gate_bundle_{short}",
        source_exact_operator_approval_signature_verifier_scaffold_bundle_id=source_id,
        approval_declaration_status="accepted_for_future_outbox_preparation_only" if accepted else "not_approved_or_rejected",
        approval_declaration_validation_result=result,
        approval_granted_now=accepted,
        approved_payload_preview_ids=list(declaration.get("approved_payload_preview_ids", [])) if accepted else [],
        approved_payload_hashes=list(declaration.get("approved_payload_hashes", [])) if accepted else [],
        approved_platforms=list(declaration.get("approved_platforms", [])) if accepted else [],
        approval_valid_for_payload_hashes_only=accepted,
        eligible_for_future_outbox_preparation_task=accepted,
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
        warnings=["approval_intake_only", "no_provider", "no_live_send", "future_outbox_preparation_only"],
    )
    data = asdict(bundle)
    return ExactJimApprovalDeclarationIntakeGateBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> ExactJimApprovalDeclarationIntakeGateBundle:
    bundle = make_exact_jim_approval_declaration_intake_gate_bundle({}, None)
    data = asdict(bundle)
    data["blockers"] = [reason]
    data["approval_declaration_status"] = "not_approved_or_rejected"
    data["approval_declaration_validation_result"] = {"declaration_supplied": False, "valid": False, "blockers": [reason], "synthetic_test_fixture_only": False}
    data["packet_sha256"] = _packet_sha(data)
    return ExactJimApprovalDeclarationIntakeGateBundle(**data)


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 exact Jim approval declaration intake gate CLI")
    parser.add_argument("--exact-operator-approval-signature-verifier-scaffold-bundle", required=True)
    parser.add_argument("--jim-approval-declaration", required=False)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        upstream = load_json_object(args.exact_operator_approval_signature_verifier_scaffold_bundle)
        declaration = load_json_object(args.jim_approval_declaration) if args.jim_approval_declaration else None
        packet = make_exact_jim_approval_declaration_intake_gate_bundle(upstream, declaration)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if not packet.blockers else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())