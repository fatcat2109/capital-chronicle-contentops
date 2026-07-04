"""V6 canonical approved payload to Discord local outbox bridge, no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_TO_DISCORD_APPROVED_PAYLOAD_OUTBOX_HEAVY_BATCH_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_FINAL_PRE_LIVE_RELEASE_AND_OPERATOR_GO_READINESS_HEAVY_BATCH_NO_SEND_V0"
CONTENT_LANE = "canonical_to_discord_community_drop"
PAYLOAD_MODE = "operator_approved_payload_outbox_bridge_only_no_send"
PAYLOAD_KIND = "discord_community_drop_payload_hash_binding_only"
CREDENTIAL_KEY_NAME = "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
APPROVAL_PHRASE = "MARK_CANONICAL_TO_DISCORD_PAYLOAD_OUTBOX_READY_NO_SEND"
APPROVAL_SCOPE = "canonical_to_discord_approved_payload_outbox_only_no_send"

SAFETY_FALSE_FLAGS = (
    "eligible_for_live_send_now", "live_send_now", "env_read_now", "dot_env_read_now",
    "credential_value_read_now", "network_call_now", "browser_session_now",
    "executable_request_artifact_created_now", "discord_api_call_now", "webhook_send_test_now",
    "endpoint_url_included", "webhook_url_included", "webhook_token_included",
    "channel_identity_included", "account_identity_included", "http_method_included",
    "http_path_included", "http_headers_included", "http_body_included", "curl_command_included",
    "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included",
    "metrics_included", "publication_ready", "dispatch_allowed", "runtime_truth",
)
CONTENT_RISK_FALSE_FLAGS = (
    "payload_text_is_public_postable", "payload_text_contains_financial_advice",
    "payload_text_contains_signal_service_claim", "payload_text_contains_fake_metrics",
    "payload_text_contains_public_url", "payload_text_contains_secret",
    "payload_text_contains_endpoint_or_webhook", "payload_text_contains_channel_or_account_id",
)
DECL_TRUE_FLAGS = (
    "canonical_content_operator_approved", "payload_text_operator_supplied",
    "payload_hash_operator_confirmed", "destination_binding_required_later",
    "credential_presence_membership_only_required_later", "exact_operator_go_required_later",
    "kill_switch_required", "redacted_audit_required", "manual_fallback_required",
)
READINESS_REQUIREMENTS = (
    "future_live_send_task_must_include_exact_operator_go",
    "future_live_send_task_must_include_destination_binding",
    "future_live_send_task_must_include_credential_presence_membership_only",
    "future_live_send_task_must_revalidate_payload_hash",
    "future_live_send_task_must_enforce_kill_switch",
    "future_live_send_task_must_write_redacted_audit",
    "future_live_send_task_must_use_single_request_budget",
    "future_live_send_task_must_use_zero_hidden_retry",
    "future_live_send_task_must_stop_on_uncertainty",
)
DECLARATION_FIELDS = {
    "schema_version", "approved_payload_declaration_id", "operator_id", "created_at_manual",
    "discord_final_pre_live_release_readiness_id", "platform", "content_lane", "payload_mode",
    "payload_kind", "canonical_content_reference_id", "canonical_content_source_type",
    "canonical_content_operator_approved", "payload_text_operator_supplied",
    "payload_text_is_public_postable", "payload_text_contains_financial_advice",
    "payload_text_contains_signal_service_claim", "payload_text_contains_fake_metrics",
    "payload_text_contains_public_url", "payload_text_contains_secret",
    "payload_text_contains_endpoint_or_webhook", "payload_text_contains_channel_or_account_id",
    "payload_preview_hash", "payload_hash_operator_confirmed", "destination_binding_present_now",
    "destination_binding_required_later", "credential_key_name",
    "credential_presence_membership_only_required_later", "exact_operator_go_required_later",
    "kill_switch_required", "redacted_audit_required", "manual_fallback_required",
    "max_request_count", "max_retries", "hidden_retry_allowed", "live_send_now",
    "eligible_for_live_send_now", "env_read_now", "dot_env_read_now", "credential_value_read_now",
    "network_call_now", "browser_session_now", "executable_request_artifact_created_now",
    "discord_api_call_now", "webhook_send_test_now", "endpoint_url_included", "webhook_url_included",
    "webhook_token_included", "channel_identity_included", "account_identity_included",
    "http_method_included", "http_path_included", "http_headers_included", "http_body_included",
    "curl_command_included", "fetch_or_http_client_code_included", "browser_instruction_included",
    "public_url_included", "metrics_included", "publication_ready", "dispatch_allowed",
    "runtime_truth", "operator_payload_decision", "declaration_decision", "approval_phrase",
    "approval_scope", "notes",
}
SECRET_OR_LIVE_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)
FORBIDDEN_TEXT = (
    "send now", "live send", "dispatch allowed", "publication ready", "ready for publication",
    "api call", "platform-live", "fake readiness", "financial advice", "signal service",
    "buy", "sell", "hold", "entries", "exits", "targets", "position sizing",
    "guaranteed prediction", "curl", "fetch call", "http request", "browser instruction",
    "public url", "public metrics", "endpoint value", "webhook value", "channel id", "account id",
    "workspace id", "app id", "http method", "http path", "headers", "body", "cookie",
)

@dataclass(frozen=True)
class CanonicalToDiscordApprovedPayloadOutboxPacket:
    schema_version: str
    task_label: str
    canonical_to_discord_payload_outbox_id: str
    approved_payload_declaration_id: str
    discord_final_pre_live_release_readiness_id: str
    operator_id: str
    created_at_manual: str
    platform: str
    content_lane: str
    payload_mode: str
    payload_kind: str
    canonical_content_reference_id: str
    canonical_content_source_type: str
    canonical_content_operator_approved: bool
    payload_preview_hash: str
    payload_hash_operator_confirmed: bool
    payload_hash_binding_ready: bool
    destination_binding_present_now: bool
    destination_binding_required_later: bool
    credential_key_name: str
    credential_presence_membership_only_required_later: bool
    exact_operator_go_required_later: bool
    kill_switch_required: bool
    redacted_audit_required: bool
    manual_fallback_required: bool
    max_request_count: int
    max_retries: int
    hidden_retry_allowed: bool
    local_outbox_packet_created: bool
    local_outbox_packet_non_executable: bool
    eligible_for_future_explicit_live_send_task: bool
    eligible_for_live_send_now: bool
    live_send_now: bool
    env_read_now: bool
    dot_env_read_now: bool
    credential_value_read_now: bool
    network_call_now: bool
    browser_session_now: bool
    executable_request_artifact_created_now: bool
    discord_api_call_now: bool
    webhook_send_test_now: bool
    endpoint_url_included: bool
    webhook_url_included: bool
    webhook_token_included: bool
    channel_identity_included: bool
    account_identity_included: bool
    http_method_included: bool
    http_path_included: bool
    http_headers_included: bool
    http_body_included: bool
    curl_command_included: bool
    fetch_or_http_client_code_included: bool
    browser_instruction_included: bool
    public_url_included: bool
    metrics_included: bool
    publication_ready: bool
    dispatch_allowed: bool
    runtime_truth: bool
    future_live_send_task_requirements: dict[str, bool]
    redacted_audit_summary: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    packet_sha256: str = ""


def _sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None)
    return hashlib.sha256(json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


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


def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk(obj):
        if isinstance(value, str):
            low = value.lower()
            if value != CREDENTIAL_KEY_NAME and SECRET_OR_LIVE_RE.search(value):
                raise ValueError(f"{label}_forbidden_value:{path}")
            if any(term in low for term in FORBIDDEN_TEXT):
                raise ValueError(f"{label}_forbidden_text:{path}")


def _add(blockers: list[str], condition: bool, message: str) -> None:
    if not condition: blockers.append(message)


def _validate_readiness(readiness: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, readiness.get("schema_version") == SCHEMA_VERSION, "readiness_schema_version_invalid")
    _add(b, readiness.get("task_label") == UPSTREAM_TASK_LABEL, "readiness_task_label_invalid")
    _add(b, readiness.get("eligible_for_future_explicit_live_send_task") is True, "readiness_future_task_not_true")
    _add(b, readiness.get("future_live_send_task_required") is True, "readiness_future_live_send_task_required_not_true")
    _add(b, readiness.get("blockers", []) == [], "readiness_blockers_not_empty")
    _add(b, bool(readiness.get("discord_final_pre_live_release_readiness_id")), "readiness_id_missing")
    for flag in SAFETY_FALSE_FLAGS:
        _add(b, readiness.get(flag) is False, f"readiness_{flag}_not_false")
    reqs = readiness.get("future_live_send_task_requirements")
    _add(b, isinstance(reqs, dict), "readiness_future_requirements_not_dict")
    if isinstance(reqs, dict):
        for key in READINESS_REQUIREMENTS:
            _add(b, reqs.get(key) is True, f"readiness_{key}_not_true")
    return b


def _validate_declaration(readiness: dict[str, Any], declaration: dict[str, Any]) -> list[str]:
    b: list[str] = []
    extra = sorted(set(declaration) - DECLARATION_FIELDS)
    _add(b, not extra, "declaration_extra_fields")
    for key in DECLARATION_FIELDS:
        _add(b, key in declaration, f"missing_declaration_{key}")
    checks = {
        "schema_version": SCHEMA_VERSION,
        "platform": "discord",
        "content_lane": CONTENT_LANE,
        "payload_mode": PAYLOAD_MODE,
        "payload_kind": PAYLOAD_KIND,
        "discord_final_pre_live_release_readiness_id": readiness.get("discord_final_pre_live_release_readiness_id"),
        "credential_key_name": CREDENTIAL_KEY_NAME,
        "approval_phrase": APPROVAL_PHRASE,
        "approval_scope": APPROVAL_SCOPE,
        "operator_payload_decision": "approve_payload_hash_binding_for_future_explicit_live_send_task_only",
        "declaration_decision": "mark_canonical_to_discord_payload_outbox_ready",
    }
    for key, expected in checks.items():
        _add(b, declaration.get(key) == expected, f"declaration_{key}_invalid")
    for key in DECL_TRUE_FLAGS:
        _add(b, declaration.get(key) is True, f"declaration_{key}_not_true")
    for key in CONTENT_RISK_FALSE_FLAGS + SAFETY_FALSE_FLAGS:
        _add(b, declaration.get(key) is False, f"declaration_{key}_not_false")
    _add(b, declaration.get("destination_binding_present_now") is False, "declaration_destination_binding_present_now_not_false")
    _add(b, declaration.get("max_request_count") == 1, "declaration_max_request_count_not_one")
    _add(b, declaration.get("max_retries") == 0, "declaration_max_retries_not_zero")
    _add(b, declaration.get("hidden_retry_allowed") is False, "declaration_hidden_retry_allowed_not_false")
    _add(b, bool(declaration.get("approved_payload_declaration_id")), "declaration_id_missing")
    _add(b, bool(declaration.get("operator_id")), "operator_id_missing")
    _add(b, bool(declaration.get("created_at_manual")), "created_at_manual_missing")
    _add(b, bool(declaration.get("canonical_content_reference_id")), "canonical_content_reference_id_missing")
    _add(b, bool(declaration.get("canonical_content_source_type")), "canonical_content_source_type_missing")
    _add(b, isinstance(declaration.get("notes"), str), "declaration_notes_not_string")
    payload_hash = declaration.get("payload_preview_hash")
    _add(b, isinstance(payload_hash, str) and bool(payload_hash.strip()), "payload_preview_hash_missing")
    if isinstance(payload_hash, str):
        _add(b, not SECRET_OR_LIVE_RE.search(payload_hash), "payload_preview_hash_secret_or_url_like")
    return b


def load_json_packet(path: str | Path, error_label: str) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError(error_label) from exc
    if not isinstance(data, dict): raise ValueError(error_label)
    return data


def make_canonical_to_discord_approved_payload_outbox_packet(readiness: dict[str, Any], declaration: dict[str, Any]) -> CanonicalToDiscordApprovedPayloadOutboxPacket:
    _assert_safe(readiness, "readiness"); _assert_safe(declaration, "declaration")
    blockers = _validate_readiness(readiness) + _validate_declaration(readiness, declaration)
    future_ready = not blockers
    readiness_id = str(readiness.get("discord_final_pre_live_release_readiness_id", ""))
    declaration_id = str(declaration.get("approved_payload_declaration_id", ""))
    outbox_id = "canonical_to_discord_payload_outbox_" + hashlib.sha256((readiness_id + declaration_id).encode("utf-8")).hexdigest()[:16]
    reqs = {key: True for key in READINESS_REQUIREMENTS}
    packet = CanonicalToDiscordApprovedPayloadOutboxPacket(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL, canonical_to_discord_payload_outbox_id=outbox_id,
        approved_payload_declaration_id=declaration_id, discord_final_pre_live_release_readiness_id=readiness_id,
        operator_id=str(declaration.get("operator_id", "")), created_at_manual=str(declaration.get("created_at_manual", "")),
        platform="discord", content_lane=CONTENT_LANE, payload_mode=PAYLOAD_MODE, payload_kind=PAYLOAD_KIND,
        canonical_content_reference_id=str(declaration.get("canonical_content_reference_id", "")),
        canonical_content_source_type=str(declaration.get("canonical_content_source_type", "")),
        canonical_content_operator_approved=declaration.get("canonical_content_operator_approved") is True,
        payload_preview_hash=str(declaration.get("payload_preview_hash", "")),
        payload_hash_operator_confirmed=declaration.get("payload_hash_operator_confirmed") is True,
        payload_hash_binding_ready=future_ready, destination_binding_present_now=False,
        destination_binding_required_later=declaration.get("destination_binding_required_later") is True,
        credential_key_name=CREDENTIAL_KEY_NAME,
        credential_presence_membership_only_required_later=declaration.get("credential_presence_membership_only_required_later") is True,
        exact_operator_go_required_later=declaration.get("exact_operator_go_required_later") is True,
        kill_switch_required=declaration.get("kill_switch_required") is True,
        redacted_audit_required=declaration.get("redacted_audit_required") is True,
        manual_fallback_required=declaration.get("manual_fallback_required") is True,
        max_request_count=1, max_retries=0, hidden_retry_allowed=False,
        local_outbox_packet_created=True, local_outbox_packet_non_executable=True,
        eligible_for_future_explicit_live_send_task=future_ready,
        eligible_for_live_send_now=False, live_send_now=False, env_read_now=False, dot_env_read_now=False,
        credential_value_read_now=False, network_call_now=False, browser_session_now=False,
        executable_request_artifact_created_now=False, discord_api_call_now=False, webhook_send_test_now=False,
        endpoint_url_included=False, webhook_url_included=False, webhook_token_included=False,
        channel_identity_included=False, account_identity_included=False, http_method_included=False,
        http_path_included=False, http_headers_included=False, http_body_included=False,
        curl_command_included=False, fetch_or_http_client_code_included=False,
        browser_instruction_included=False, public_url_included=False, metrics_included=False,
        publication_ready=False, dispatch_allowed=False, runtime_truth=False,
        future_live_send_task_requirements=reqs,
        redacted_audit_summary="Canonical payload hash binding moved to local non-executable Discord outbox packet with no live send, env read, credential read, network, browser, executable request artifact, public URL, metrics, publication readiness, or dispatch.",
        blockers=blockers,
        warnings=["local_only_outbox_no_send", "future_explicit_live_send_task_required", "destination_binding_required_later"],
    )
    data = asdict(packet)
    return CanonicalToDiscordApprovedPayloadOutboxPacket(**{**data, "packet_sha256": _sha(data)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 canonical to Discord approved payload outbox bridge CLI")
    parser.add_argument("--input-final-readiness-packet", required=True)
    parser.add_argument("--operator-approved-payload-declaration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        packet = make_canonical_to_discord_approved_payload_outbox_packet(
            load_json_packet(args.input_final_readiness_packet, "malformed_final_readiness_packet_json"),
            load_json_packet(args.operator_approved_payload_declaration, "malformed_payload_declaration_json"),
        )
    except ValueError as exc:
        packet = CanonicalToDiscordApprovedPayloadOutboxPacket(SCHEMA_VERSION, TASK_LABEL, "canonical_to_discord_payload_outbox_blocked", "", "", "", "", "discord", CONTENT_LANE, PAYLOAD_MODE, PAYLOAD_KIND, "", "", False, "", False, False, False, True, CREDENTIAL_KEY_NAME, True, True, True, True, True, 1, 0, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, reqs if (reqs := {key: True for key in READINESS_REQUIREMENTS}) else {}, "", [str(exc)], ["outbox_packet_blocked_pending_operator_repair"])
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_explicit_live_send_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

