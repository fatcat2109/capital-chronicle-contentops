"""V6 Discord final pre-live release readiness, local-only and no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_FINAL_PRE_LIVE_RELEASE_AND_OPERATOR_GO_READINESS_HEAVY_BATCH_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_EXPLICIT_LIVE_PILOT_GATE_PREP_HEAVY_BATCH_NO_SEND_V0"
READINESS_MODE = "operator_declared_discord_final_pre_live_release_readiness_only_no_send"
READINESS_KIND = "final_pre_live_release_readiness_packet_no_send"
APPROVAL_PHRASE = "MARK_DISCORD_FINAL_PRE_LIVE_RELEASE_READINESS_READY_NO_SEND"
APPROVAL_SCOPE = "discord_final_pre_live_release_readiness_only_no_send"
CREDENTIAL_KEY_NAME = "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"

FALSE_FLAGS = (
    "eligible_for_live_send_now", "live_send_now", "env_read_now", "dot_env_read_now",
    "credential_value_read_now", "network_call_now", "browser_session_now",
    "executable_request_created_now", "discord_api_call_now", "webhook_send_test_now",
    "endpoint_url_included", "webhook_url_included", "webhook_token_included",
    "channel_identity_included", "account_identity_included", "http_method_included",
    "http_path_included", "http_headers_included", "http_body_included", "curl_command_included",
    "fetch_or_http_client_code_included", "browser_instruction_included", "public_url_included",
    "metrics_included", "publication_ready", "dispatch_allowed", "runtime_truth",
)
TRUE_DECL_FLAGS = (
    "docs_hygiene_reviewed", "docs_bom_removed", "docs_literal_backtick_n_removed",
    "evidence_chain_consolidated", "future_live_task_template_created", "future_live_send_task_required",
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
TRUE_PREP_FLAGS = (
    "idempotency_required", "kill_switch_required", "redacted_audit_required", "manual_fallback_required",
    "exact_operator_go_phrase_required_later", "future_live_execution_task_required",
)
DECLARATION_FIELDS = {
    "schema_version", "discord_final_pre_live_release_readiness_declaration_id", "operator_id",
    "created_at_manual", "discord_explicit_live_pilot_gate_prep_id",
    "discord_live_capable_supervised_pilot_adapter_id", "discord_heavy_local_pre_live_batch_id",
    "platform", "readiness_mode", "readiness_kind", "docs_hygiene_reviewed",
    "docs_bom_removed", "docs_literal_backtick_n_removed", "evidence_chain_consolidated",
    "future_live_task_template_created", "live_send_now", "eligible_for_live_send_now",
    "env_read_now", "dot_env_read_now", "credential_value_read_now", "network_call_now",
    "browser_session_now", "executable_request_created_now", "discord_api_call_now",
    "webhook_send_test_now", "endpoint_url_included", "webhook_url_included",
    "webhook_token_included", "channel_identity_included", "account_identity_included",
    "http_method_included", "http_path_included", "http_headers_included", "http_body_included",
    "curl_command_included", "fetch_or_http_client_code_included", "browser_instruction_included",
    "public_url_included", "metrics_included", "publication_ready", "dispatch_allowed",
    "runtime_truth", "future_live_send_task_required",
    "future_live_send_task_must_include_exact_operator_go",
    "future_live_send_task_must_include_destination_binding",
    "future_live_send_task_must_include_credential_presence_membership_only",
    "future_live_send_task_must_revalidate_payload_hash",
    "future_live_send_task_must_enforce_kill_switch",
    "future_live_send_task_must_write_redacted_audit",
    "future_live_send_task_must_use_single_request_budget",
    "future_live_send_task_must_use_zero_hidden_retry",
    "future_live_send_task_must_stop_on_uncertainty", "operator_readiness_decision",
    "declaration_decision", "approval_phrase", "approval_scope", "notes",
}
SECRET_OR_LIVE_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)
FORBIDDEN_TEXT = ("send now", "live send", "dispatch allowed", "publication ready", "ready for publication", "api call", "platform-live", "fake readiness", "financial advice", "signal service", "curl-command", "fetch-call", "request code", "browser instruction", "public url", "public metrics", "endpoint value", "webhook value", "channel id", "account id", "http method", "http path", "headers", "body")

@dataclass(frozen=True)
class DiscordFinalPreLiveReleaseReadinessPacket:
    schema_version: str
    task_label: str
    discord_final_pre_live_release_readiness_id: str
    declaration_id: str
    discord_explicit_live_pilot_gate_prep_id: str
    discord_live_capable_supervised_pilot_adapter_id: str
    discord_heavy_local_pre_live_batch_id: str
    platform: str
    readiness_kind: str
    docs_hygiene_reviewed: bool
    docs_bom_removed: bool
    docs_literal_backtick_n_removed: bool
    evidence_chain_consolidated: bool
    future_live_task_template_created: bool
    eligible_for_future_explicit_live_send_task: bool
    eligible_for_live_send_now: bool
    live_send_now: bool
    env_read_now: bool
    dot_env_read_now: bool
    credential_value_read_now: bool
    network_call_now: bool
    browser_session_now: bool
    executable_request_created_now: bool
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
    future_live_send_task_required: bool
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
        for key, val in obj.items(): out.extend(_walk(val, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, val in enumerate(obj): out.extend(_walk(val, f"{path}[{idx}]"))
        return out
    return [(path, obj)]


def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, val in _walk(obj):
        if isinstance(val, str):
            low = val.lower()
            if val != CREDENTIAL_KEY_NAME and SECRET_OR_LIVE_RE.search(val):
                raise ValueError(f"{label}_forbidden_value:{path}")
            if any(term in low for term in FORBIDDEN_TEXT):
                raise ValueError(f"{label}_forbidden_text:{path}")


def _add(blockers: list[str], ok: bool, msg: str) -> None:
    if not ok: blockers.append(msg)


def _validate_prep(prep: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, prep.get("schema_version") == SCHEMA_VERSION, "prep_schema_version_invalid")
    _add(b, prep.get("task_label") == UPSTREAM_TASK_LABEL, "prep_task_label_invalid")
    _add(b, prep.get("eligible_for_future_operator_go_live_task") is True, "prep_future_operator_go_not_true")
    for key in FALSE_FLAGS: _add(b, prep.get(key) is False, f"prep_{key}_not_false")
    for key in TRUE_PREP_FLAGS: _add(b, prep.get(key) is True, f"prep_{key}_not_true")
    _add(b, prep.get("max_request_count") == 1, "prep_max_request_count_not_one")
    _add(b, prep.get("max_retries") == 0, "prep_max_retries_not_zero")
    _add(b, prep.get("hidden_retry_allowed") is False, "prep_hidden_retry_allowed_not_false")
    _add(b, prep.get("blockers", []) == [], "prep_blockers_not_empty")
    for key in ("discord_explicit_live_pilot_gate_prep_id", "discord_live_capable_supervised_pilot_adapter_id", "discord_heavy_local_pre_live_batch_id"):
        _add(b, bool(prep.get(key)), f"prep_{key}_missing")
    return b


def _validate_decl(prep: dict[str, Any], decl: dict[str, Any]) -> list[str]:
    b: list[str] = []
    extra = sorted(set(decl) - DECLARATION_FIELDS)
    _add(b, not extra, "declaration_extra_fields")
    for key in DECLARATION_FIELDS: _add(b, key in decl, f"missing_declaration_{key}")
    checks = {
        "schema_version": SCHEMA_VERSION, "platform": "discord", "readiness_mode": READINESS_MODE,
        "readiness_kind": READINESS_KIND, "approval_phrase": APPROVAL_PHRASE, "approval_scope": APPROVAL_SCOPE,
        "discord_explicit_live_pilot_gate_prep_id": prep.get("discord_explicit_live_pilot_gate_prep_id"),
        "discord_live_capable_supervised_pilot_adapter_id": prep.get("discord_live_capable_supervised_pilot_adapter_id"),
        "discord_heavy_local_pre_live_batch_id": prep.get("discord_heavy_local_pre_live_batch_id"),
        "operator_readiness_decision": "approve_final_pre_live_release_readiness_for_future_explicit_live_send_task_only",
        "declaration_decision": "mark_discord_final_pre_live_release_readiness_ready",
    }
    for key, expected in checks.items(): _add(b, decl.get(key) == expected, f"declaration_{key}_invalid")
    for key in FALSE_FLAGS: _add(b, decl.get(key) is False, f"declaration_{key}_not_false")
    for key in TRUE_DECL_FLAGS: _add(b, decl.get(key) is True, f"declaration_{key}_not_true")
    _add(b, bool(decl.get("discord_final_pre_live_release_readiness_declaration_id")), "missing_declaration_id")
    _add(b, bool(decl.get("operator_id")), "missing_operator_id")
    _add(b, bool(decl.get("created_at_manual")), "missing_created_at_manual")
    _add(b, isinstance(decl.get("notes"), str), "declaration_notes_not_string")
    return b


def load_json_packet(path: str | Path, error_label: str) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError(error_label) from exc
    if not isinstance(data, dict): raise ValueError(error_label)
    return data


def make_discord_final_pre_live_release_readiness_packet(prep: dict[str, Any], declaration: dict[str, Any]) -> DiscordFinalPreLiveReleaseReadinessPacket:
    _assert_safe(prep, "prep"); _assert_safe(declaration, "declaration")
    blockers = _validate_prep(prep) + _validate_decl(prep, declaration)
    eligible = not blockers
    declaration_id = str(declaration.get("discord_final_pre_live_release_readiness_declaration_id", ""))
    prep_id = str(prep.get("discord_explicit_live_pilot_gate_prep_id", ""))
    readiness_id = "discord_final_pre_live_release_readiness_" + hashlib.sha256((prep_id + declaration_id).encode("utf-8")).hexdigest()[:16]
    reqs = {key: True for key in TRUE_DECL_FLAGS if key.startswith("future_live_send_task_must_")}
    packet = DiscordFinalPreLiveReleaseReadinessPacket(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL,
        discord_final_pre_live_release_readiness_id=readiness_id, declaration_id=declaration_id,
        discord_explicit_live_pilot_gate_prep_id=prep_id,
        discord_live_capable_supervised_pilot_adapter_id=str(prep.get("discord_live_capable_supervised_pilot_adapter_id", "")),
        discord_heavy_local_pre_live_batch_id=str(prep.get("discord_heavy_local_pre_live_batch_id", "")),
        platform="discord", readiness_kind=READINESS_KIND,
        docs_hygiene_reviewed=True, docs_bom_removed=True, docs_literal_backtick_n_removed=True,
        evidence_chain_consolidated=True, future_live_task_template_created=True,
        eligible_for_future_explicit_live_send_task=eligible, eligible_for_live_send_now=False,
        live_send_now=False, env_read_now=False, dot_env_read_now=False, credential_value_read_now=False,
        network_call_now=False, browser_session_now=False, executable_request_created_now=False,
        discord_api_call_now=False, webhook_send_test_now=False, endpoint_url_included=False,
        webhook_url_included=False, webhook_token_included=False, channel_identity_included=False,
        account_identity_included=False, http_method_included=False, http_path_included=False,
        http_headers_included=False, http_body_included=False, curl_command_included=False,
        fetch_or_http_client_code_included=False, browser_instruction_included=False, public_url_included=False,
        metrics_included=False, publication_ready=False, dispatch_allowed=False, runtime_truth=False,
        future_live_send_task_required=True, future_live_send_task_requirements=reqs,
        redacted_audit_summary="Final pre-live release readiness consolidated locally with no live send, env read, credential read, network, browser, executable request artifact, public URL, or metrics.",
        blockers=blockers, warnings=["local_only_no_send", "future_explicit_live_send_task_required"],
    )
    data = asdict(packet)
    return DiscordFinalPreLiveReleaseReadinessPacket(**{**data, "packet_sha256": _sha(data)})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Discord final pre-live release readiness CLI")
    parser.add_argument("--input-prep-packet", required=True)
    parser.add_argument("--operator-readiness-declaration", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        packet = make_discord_final_pre_live_release_readiness_packet(load_json_packet(args.input_prep_packet, "malformed_prep_packet_json"), load_json_packet(args.operator_readiness_declaration, "malformed_readiness_declaration_json"))
    except ValueError as exc:
        packet = DiscordFinalPreLiveReleaseReadinessPacket(SCHEMA_VERSION, TASK_LABEL, "discord_final_pre_live_release_readiness_blocked", "", "", "", "", "discord", READINESS_KIND, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, {}, "", [str(exc)], ["readiness_packet_blocked_pending_operator_repair"])
    out_path = Path(args.output); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_explicit_live_send_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
