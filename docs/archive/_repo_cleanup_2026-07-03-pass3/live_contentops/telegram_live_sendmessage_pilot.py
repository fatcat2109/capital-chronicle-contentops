"""Supervised one-shot Telegram sendMessage pilot for Batch C."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .credential_redaction_policy import REDACTION_POLICY_ID, contains_secret_shaped_text, redact_text
from .telegram_live_authority_core import (
    APPROVED_PAYLOAD_TEXT,
    CREDENTIAL_HANDLE_ID,
    DESTINATION_BINDING_ID,
    TASK_LABEL,
    build_approval_event,
    build_outbox_candidate,
    build_payload_packet,
    build_redacted_audit_event,
    check_idempotency,
    classify_kill_switch,
)

TELEGRAM_HOST = "api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 10
TASK_DIR = Path("docs/automation/TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY")
APPROVED_ENV_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID", "CONTENTOPS_GLOBAL_KILL_SWITCH")
ALLOWED_METHODS = {"getMe", "getChat", "sendMessage"}
FORBIDDEN_METHODS = {"sendPhoto", "sendDocument", "sendMediaGroup", "sendRichMessage", "getUpdates", "setWebhook", "deleteWebhook"}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None

Transport = Callable[[str, str, str, Mapping[str, str], int], tuple[str, dict[str, Any] | None]]

def _parse_env_text(text: str) -> dict[str, str | None]:
    parsed = {key: None for key in APPROVED_ENV_KEYS}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        if key not in parsed:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        parsed[key] = value
    return parsed

def _read_env(repo_root: str | Path) -> tuple[dict[str, str | None], str]:
    root = Path(repo_root)
    merged = {key: None for key in APPROVED_ENV_KEYS}
    labels: list[str] = []
    for name, label in ((".env", "repo_dotenv_redacted"), (".env.local", "repo_dotenv_local_redacted")):
        path = root / name
        if not path.exists():
            continue
        values = _parse_env_text(path.read_text(encoding="utf-8", errors="replace"))
        for key, value in values.items():
            if value is not None:
                merged[key] = value
        labels.append(label)
    if not merged.get("TELEGRAM_BOT_TOKEN") or not merged.get("TELEGRAM_CHANNEL_ID"):
        for key in APPROVED_ENV_KEYS:
            if not merged.get(key) and os.environ.get(key):
                merged[key] = os.environ.get(key)
        if any(os.environ.get(key) for key in APPROVED_ENV_KEYS):
            labels.append("process_env_fallback_redacted")
    return merged, "+".join(labels) if labels else "unavailable"

def _classify_token(value: str | None) -> str:
    if not value:
        return "missing"
    return "present_redacted_telegram_bot_token_like" if contains_secret_shaped_text(value) else "present_redacted_nonclassifiable"

def _classify_chat(value: str | None) -> str:
    if not value:
        return "missing"
    text = value.strip()
    if text.startswith("@") and len(text) >= 4:
        return "present_redacted_channel_handle_like"
    if text.lstrip("-").isdigit():
        return "present_redacted_integer_like"
    return "present_redacted_nonclassifiable"

def _env_summary(values: Mapping[str, str | None], source_label: str) -> dict[str, Any]:
    return {
        "credential_source_label": source_label,
        "env_key_names_checked": list(APPROVED_ENV_KEYS),
        "telegram_bot_token": {"present": bool(values.get("TELEGRAM_BOT_TOKEN")), "shape_class": _classify_token(values.get("TELEGRAM_BOT_TOKEN"))},
        "telegram_channel_id": {"present": bool(values.get("TELEGRAM_CHANNEL_ID")), "shape_class": _classify_chat(values.get("TELEGRAM_CHANNEL_ID"))},
        "contentops_global_kill_switch": {"present": values.get("CONTENTOPS_GLOBAL_KILL_SWITCH") is not None, "shape_class": "present_redacted" if values.get("CONTENTOPS_GLOBAL_KILL_SWITCH") is not None else "missing"},
        "raw_values_persisted": False,
    }

def _request_json(method_name: str, http_method: str, token: str, params: Mapping[str, str], timeout: int) -> tuple[str, dict[str, Any] | None]:
    if method_name not in ALLOWED_METHODS or method_name in FORBIDDEN_METHODS:
        return "blocked_method_not_allowlisted", None
    base_url = f"https://{TELEGRAM_HOST}/bot{token}/{method_name}"
    encoded = urlencode(dict(params)).encode("utf-8")
    if http_method == "GET":
        url = base_url + ("?" + urlencode(dict(params)) if params else "")
        req = Request(url, method="GET")
    elif http_method == "POST":
        req = Request(base_url, data=encoded, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    else:
        return "blocked_http_method_not_allowlisted", None
    opener = build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if isinstance(data, dict):
            return "http_2xx_json", data
        return "http_2xx_json_non_object_redacted", None
    except HTTPError as exc:
        return "http_error_redacted_" + str(exc.code), None
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return "transport_or_parse_error_redacted:" + redact_text(exc.__class__.__name__), None

def _blocked_probe(name: str, reasons: list[str]) -> dict[str, Any]:
    family = "telegram_bot_identity" if name == "getMe" else "telegram_channel_read"
    return {"endpoint_family": family, "host": TELEGRAM_HOST, "method": "GET", "redacted_path": f"/bot<redacted>/{name}", "request_budget": 1, "request_count": 0, "timeout_seconds": REQUEST_TIMEOUT_SECONDS, "redirect_policy": "redirect_disabled_fail_closed", "auto_retry": False, "raw_response_persisted": False, "result_classification": "blocked_not_attempted", "blocked_reasons": reasons}

def _classify_getme(classification: str, data: dict[str, Any] | None) -> dict[str, Any]:
    ok = isinstance(data, dict) and data.get("ok") is True
    result = data.get("result") if isinstance(data, dict) else None
    present = isinstance(result, dict) and result.get("is_bot") is True and "id" in result
    return {"endpoint_family": "telegram_bot_identity", "host": TELEGRAM_HOST, "method": "GET", "redacted_path": "/bot<redacted>/getMe", "request_budget": 1, "request_count": 1, "timeout_seconds": REQUEST_TIMEOUT_SECONDS, "redirect_policy": "redirect_disabled_fail_closed", "auto_retry": False, "raw_response_persisted": False, "result_classification": "read_only_probe_pass" if present else classification, "response_ok_redacted": bool(ok), "bot_identity_present_class": "present_redacted" if present else "absent_or_unverified_redacted"}

def _classify_getchat(classification: str, data: dict[str, Any] | None) -> dict[str, Any]:
    ok = isinstance(data, dict) and data.get("ok") is True
    result = data.get("result") if isinstance(data, dict) else None
    present = isinstance(result, dict) and "id" in result and "type" in result
    return {"endpoint_family": "telegram_channel_read", "host": TELEGRAM_HOST, "method": "GET", "redacted_path": "/bot<redacted>/getChat", "request_budget": 1, "request_count": 1, "timeout_seconds": REQUEST_TIMEOUT_SECONDS, "redirect_policy": "redirect_disabled_fail_closed", "auto_retry": False, "raw_response_persisted": False, "result_classification": "read_only_probe_pass" if present else classification, "response_ok_redacted": bool(ok), "chat_identity_present_class": "present_redacted" if present else "absent_or_unverified_redacted", "chat_type_present_class": "present_redacted" if present else "absent_or_unverified_redacted"}

def _classify_send(classification: str, data: dict[str, Any] | None, attempted: bool) -> dict[str, Any]:
    ok = isinstance(data, dict) and data.get("ok") is True
    result = data.get("result") if isinstance(data, dict) else None
    message_present = isinstance(result, dict) and "message_id" in result
    final = "live_send_success" if ok and message_present else classification
    if attempted and final.startswith("transport_or_parse_error"):
        final = "unknown_requires_manual_reconciliation"
    return {"endpoint_family": "telegram_sendmessage_live_write", "host": TELEGRAM_HOST, "method": "POST", "redacted_path": "/bot<redacted>/sendMessage", "request_budget": 1, "request_count": 1 if attempted else 0, "timeout_seconds": REQUEST_TIMEOUT_SECONDS, "redirect_policy": "redirect_disabled_fail_closed", "auto_retry": False, "raw_request_persisted": False, "raw_response_persisted": False, "result_classification": final, "response_ok_redacted": bool(ok), "sent_message_id_presence_class": "present_redacted" if message_present else "absent_or_unverified_redacted"}

def _safe_write_json(path: Path, data: Mapping[str, Any]) -> None:
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    if contains_secret_shaped_text(text):
        raise ValueError("secret_shaped_text_blocked_before_evidence_write")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")

def run_pilot(repo_root: str | Path, evidence_path: str | Path, operator_approved: bool, transport: Transport = _request_json) -> dict[str, Any]:
    values, source_label = _read_env(repo_root)
    env_summary = _env_summary(values, source_label)
    task_dir = Path(repo_root) / TASK_DIR
    token = values.get("TELEGRAM_BOT_TOKEN")
    chat_id = values.get("TELEGRAM_CHANNEL_ID")
    probes: dict[str, Any] = {"getMe": _blocked_probe("getMe", ["not_attempted"]), "getChat": _blocked_probe("getChat", ["not_attempted"])}
    send_result = _classify_send("blocked_not_attempted", None, False)
    payload_packet = build_payload_packet(APPROVED_PAYLOAD_TEXT, DESTINATION_BINDING_ID, CREDENTIAL_HANDLE_ID)
    approval_event = build_approval_event(payload_packet)
    outbox = build_outbox_candidate(payload_packet, approval_event)
    kill_switch = classify_kill_switch(values.get("CONTENTOPS_GLOBAL_KILL_SWITCH"))
    idempotency = check_idempotency(task_dir, outbox["idempotency_key_hash"])
    blocked_reasons: list[str] = []
    if not operator_approved:
        blocked_reasons.append("operator_approved_live_telegram_flag_missing")
    if not token:
        blocked_reasons.append("telegram_bot_token_missing")
    if not chat_id:
        blocked_reasons.append("telegram_channel_id_missing")
    if kill_switch["live_send_blocked"]:
        blocked_reasons.append("contentops_global_kill_switch_on")
    if idempotency["send_blocked"]:
        blocked_reasons.append(idempotency["idempotency_state"])
    if not blocked_reasons:
        c, data = transport("getMe", "GET", str(token), {}, REQUEST_TIMEOUT_SECONDS)
        probes["getMe"] = _classify_getme(c, data)
        if probes["getMe"]["result_classification"] != "read_only_probe_pass":
            blocked_reasons.append("getme_failed")
    if not blocked_reasons:
        c, data = transport("getChat", "GET", str(token), {"chat_id": str(chat_id)}, REQUEST_TIMEOUT_SECONDS)
        probes["getChat"] = _classify_getchat(c, data)
        if probes["getChat"]["result_classification"] != "read_only_probe_pass":
            blocked_reasons.append("getchat_failed")
    if not blocked_reasons:
        c, data = transport("sendMessage", "POST", str(token), {"chat_id": str(chat_id), "text": APPROVED_PAYLOAD_TEXT}, REQUEST_TIMEOUT_SECONDS)
        send_result = _classify_send(c, data, True)
        if send_result["result_classification"] != "live_send_success":
            blocked_reasons.append(send_result["result_classification"])
    audit = build_redacted_audit_event(payload_packet, approval_event, outbox, kill_switch, idempotency, probes, send_result, env_summary)
    audit.update({
        "status": "success" if send_result["result_classification"] == "live_send_success" else "blocked_or_not_success",
        "blocked_reasons": blocked_reasons,
        "official_docs_checked": ["https://core.telegram.org/bots/api#getme", "https://core.telegram.org/bots/api#getchat", "https://core.telegram.org/bots/api#sendmessage"],
        "payload_text_persisted_for_approval_packet_only": True,
        "manual_reconciliation_required": send_result["result_classification"] == "unknown_requires_manual_reconciliation",
    })
    if contains_secret_shaped_text(json.dumps(audit, sort_keys=True, ensure_ascii=False)):
        raise ValueError("secret_shaped_text_blocked_in_audit")
    _safe_write_json(Path(repo_root) / evidence_path, audit)
    return audit

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--operator-approved-live-telegram", action="store_true")
    parser.add_argument("--write-evidence", required=True)
    args = parser.parse_args(argv)
    audit = run_pilot(args.repo_root, args.write_evidence, args.operator_approved_live_telegram)
    print(json.dumps({"task_label": TASK_LABEL, "status": audit["status"], "payload_hash": audit["payload_hash"], "sendMessage_result_classification": audit["sendMessage"]["result_classification"], "request_counts": audit["request_counts"], "raw_request_persisted": False, "raw_response_persisted": False}, sort_keys=True))
    return 0 if audit["status"] == "success" else 2

if __name__ == "__main__":
    raise SystemExit(main())
