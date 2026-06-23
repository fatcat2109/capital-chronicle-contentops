"""Telegram Batch B read-only proof runner."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .credential_redaction_policy import REDACTION_POLICY_ID, contains_secret_shaped_text

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_B_OPERATOR_SETUP_TELEGRAM_READONLY_PROOF_AND_PROBE_HARDENING_V0"
APPROVED_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID", "TELEGRAM_OPERATOR_CHAT_ID")
TELEGRAM_HOST = "api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 10

FORBIDDEN_METHODS = (
    "sendMessage", "sendPhoto", "sendDocument", "sendMediaGroup", "sendRichMessage",
    "sendRichMessageDraft", "copyMessage", "forwardMessage", "editMessageText",
    "deleteMessage", "getUpdates", "setWebhook", "deleteWebhook", "answerCallbackQuery",
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _blocked_probe(endpoint_family: str, reasons: tuple[str, ...]) -> dict[str, Any]:
    return {
        "endpoint_family": endpoint_family,
        "host": TELEGRAM_HOST,
        "scheme": "https",
        "method": "GET",
        "request_budget": 1,
        "request_count": 0,
        "auto_retry": False,
        "redirect_policy": "redirect_disabled_fail_closed",
        "raw_response_persisted": False,
        "result_classification": "blocked_not_attempted",
        "blocked_reasons": list(reasons),
    }


def _base_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "redaction_policy_id": REDACTION_POLICY_ID,
        "docs_source_checked": "https://core.telegram.org/bots/api#getme",
        "raw_values_persisted": False,
        "raw_response_persisted": False,
        "raw_url_persisted": False,
        "headers_persisted": False,
        "auto_retry": False,
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "live_readonly_telegram_requested": False,
        "credential_source_label": "unavailable",
        "credentials": {
            "telegram_bot_token": {"present": False, "shape_class": "missing"},
            "telegram_channel_id": {"present": False, "shape_class": "missing"},
            "telegram_operator_chat_id": {"present": False, "shape_class": "missing"},
        },
        "probes": {
            "getMe": _blocked_probe("telegram_bot_identity", ("not_requested",)),
            "getChat": _blocked_probe("telegram_channel_read", ("not_requested",)),
        },
        "safety_flags": {
            "posting_performed": False,
            "send_message_performed": False,
            "platform_write_performed": False,
            "upload_performed": False,
            "publish_performed": False,
            "scheduler_enabled": False,
            "autonomous_reply_performed": False,
            "dm_performed": False,
            "scraping_performed": False,
            "webhook_registered": False,
            "polling_enabled": False,
            "raw_secret_exposed": False,
        },
        "status": "blocked",
        "blocked_reasons": [],
    }


def _classify_token_shape(value: str | None) -> str:
    if value is None or value.strip() == "":
        return "missing"
    text = value.strip()
    if ":" in text and contains_secret_shaped_text(text):
        return "present_redacted_telegram_bot_token_like"
    return "present_redacted_nonclassifiable"


def _classify_chat_shape(value: str | None) -> str:
    if value is None or value.strip() == "":
        return "missing"
    text = value.strip()
    if text.startswith("@") and len(text) >= 4:
        return "present_redacted_channel_handle_like"
    if text.lstrip("-").isdigit():
        return "present_redacted_integer_like"
    return "present_redacted_nonclassifiable"


def _parse_env_text(text: str) -> dict[str, str | None]:
    parsed: dict[str, str | None] = {key: None for key in APPROVED_KEYS}
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


def _read_repo_env(repo_root: str | Path) -> tuple[dict[str, str | None], str, bool]:
    root = Path(repo_root)
    merged: dict[str, str | None] = {key: None for key in APPROVED_KEYS}
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
    return merged, "+".join(labels) if labels else "unavailable", bool(labels)


def _read_process_env() -> tuple[dict[str, str | None], str, bool]:
    env = getattr(os, "environ")
    values = {key: env.get(key) for key in APPROVED_KEYS}
    return values, "process_env_selected_redacted", any(values.values())


def _credential_summary(values: Mapping[str, str | None]) -> dict[str, Any]:
    return {
        "telegram_bot_token": {"present": bool(values.get("TELEGRAM_BOT_TOKEN")), "shape_class": _classify_token_shape(values.get("TELEGRAM_BOT_TOKEN"))},
        "telegram_channel_id": {"present": bool(values.get("TELEGRAM_CHANNEL_ID")), "shape_class": _classify_chat_shape(values.get("TELEGRAM_CHANNEL_ID"))},
        "telegram_operator_chat_id": {"present": bool(values.get("TELEGRAM_OPERATOR_CHAT_ID")), "shape_class": _classify_chat_shape(values.get("TELEGRAM_OPERATOR_CHAT_ID"))},
    }


def _request_json(url: str, timeout_seconds: int) -> tuple[str, dict[str, Any] | None]:
    req = Request(url, method="GET")
    opener = build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if isinstance(data, dict):
            return "http_2xx_json", data
        return "http_2xx_json_non_object_redacted", None
    except HTTPError as exc:
        return "http_error_redacted_" + str(exc.code), None
    except (URLError, TimeoutError, OSError, ValueError):
        return "transport_or_parse_error_redacted", None


def _redacted_getme_result(classification: str, data: dict[str, Any] | None) -> dict[str, Any]:
    ok = isinstance(data, dict) and data.get("ok") is True
    result = data.get("result") if isinstance(data, dict) else None
    is_bot = isinstance(result, dict) and result.get("is_bot") is True
    has_id = isinstance(result, dict) and "id" in result
    has_username = isinstance(result, dict) and bool(result.get("username"))
    return {
        "endpoint_family": "telegram_bot_identity",
        "host": TELEGRAM_HOST,
        "scheme": "https",
        "method": "GET",
        "request_budget": 1,
        "request_count": 1,
        "auto_retry": False,
        "redirect_policy": "redirect_disabled_fail_closed",
        "raw_response_persisted": False,
        "result_classification": "read_only_probe_pass" if ok and is_bot and has_id else classification,
        "response_ok_redacted": bool(ok),
        "bot_identity_present_class": "present_redacted" if has_id else "absent_or_unverified_redacted",
        "bot_is_bot_class": "present_redacted" if is_bot else "absent_or_unverified_redacted",
        "bot_username_present_class": "present_redacted" if has_username else "absent_or_unverified_redacted",
        "blocked_reasons": [] if ok and is_bot and has_id else ["getme_identity_not_confirmed_redacted"],
    }


def _redacted_getchat_result(classification: str, data: dict[str, Any] | None) -> dict[str, Any]:
    ok = isinstance(data, dict) and data.get("ok") is True
    result = data.get("result") if isinstance(data, dict) else None
    has_id = isinstance(result, dict) and "id" in result
    has_type = isinstance(result, dict) and bool(result.get("type"))
    has_title = isinstance(result, dict) and bool(result.get("title"))
    return {
        "endpoint_family": "telegram_channel_read",
        "host": TELEGRAM_HOST,
        "scheme": "https",
        "method": "GET",
        "request_budget": 1,
        "request_count": 1,
        "auto_retry": False,
        "redirect_policy": "redirect_disabled_fail_closed",
        "raw_response_persisted": False,
        "result_classification": "read_only_probe_pass" if ok and has_id and has_type else classification,
        "response_ok_redacted": bool(ok),
        "chat_identity_present_class": "present_redacted" if has_id else "absent_or_unverified_redacted",
        "chat_type_present_class": "present_redacted" if has_type else "absent_or_unverified_redacted",
        "chat_title_present_class": "present_redacted" if has_title else "absent_or_unverified_redacted",
        "blocked_reasons": [] if ok and has_id and has_type else ["getchat_identity_not_confirmed_redacted"],
    }


def _assert_output_safe(packet: Mapping[str, Any]) -> None:
    text = json.dumps(packet, sort_keys=True, ensure_ascii=False)
    if contains_secret_shaped_text(text):
        raise ValueError("secret_shaped_output_blocked_by_batch_b")
    for forbidden in FORBIDDEN_METHODS:
        if forbidden in text:
            raise ValueError("forbidden_method_output_blocked_by_batch_b")


def run_batch_b_telegram_readonly_proof(*, repo_root: str | Path = ".", live_readonly_telegram: bool = False, include_process_env: bool = False, timeout_seconds: int = REQUEST_TIMEOUT_SECONDS, _transport=None) -> dict[str, Any]:
    packet = _base_packet()
    packet["live_readonly_telegram_requested"] = bool(live_readonly_telegram)
    packet["timeout_seconds"] = int(timeout_seconds)
    values, label, available = _read_repo_env(repo_root)
    if include_process_env and not any(values.values()):
        values, label, available = _read_process_env()
    packet["credential_source_label"] = label
    packet["credentials"] = _credential_summary(values)
    token = values.get("TELEGRAM_BOT_TOKEN")
    channel_id = values.get("TELEGRAM_CHANNEL_ID")
    blockers: list[str] = []
    if not available:
        blockers.append("approved_env_source_unavailable")
    if not live_readonly_telegram:
        blockers.append("live_readonly_telegram_not_requested")
    if not token:
        blockers.append("telegram_bot_token_missing")
    if _classify_token_shape(token) != "present_redacted_telegram_bot_token_like":
        blockers.append("telegram_bot_token_shape_not_accepted")
    if blockers:
        packet["blocked_reasons"] = blockers
        _assert_output_safe(packet)
        return packet
    caller = _transport if _transport is not None else _request_json
    getme_class, getme_data = caller(f"https://{TELEGRAM_HOST}/bot{token}/getMe", int(timeout_seconds))
    packet["probes"]["getMe"] = _redacted_getme_result(getme_class, getme_data)
    if channel_id and _classify_chat_shape(channel_id) in {"present_redacted_integer_like", "present_redacted_channel_handle_like"}:
        query = urlencode({"chat_id": channel_id})
        getchat_class, getchat_data = caller(f"https://{TELEGRAM_HOST}/bot{token}/getChat?{query}", int(timeout_seconds))
        packet["probes"]["getChat"] = _redacted_getchat_result(getchat_class, getchat_data)
    else:
        packet["probes"]["getChat"] = _blocked_probe("telegram_channel_read", ("telegram_channel_id_missing_or_shape_not_accepted",))
    probe_values = packet["probes"].values()
    if all(probe.get("result_classification") == "read_only_probe_pass" for probe in probe_values):
        packet["status"] = "pass"
    elif packet["probes"]["getMe"].get("result_classification") == "read_only_probe_pass":
        packet["status"] = "partial_pass_getchat_blocked_or_unverified"
    else:
        packet["status"] = "blocked"
    packet["blocked_reasons"] = [] if packet["status"] == "pass" else ["one_or_more_readonly_probes_not_confirmed_redacted"]
    _assert_output_safe(packet)
    return packet


def write_evidence(packet: Mapping[str, Any], output_path: str | Path) -> None:
    _assert_output_safe(packet)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Telegram Batch B read-only proof.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--live-readonly-telegram", action="store_true")
    parser.add_argument("--include-process-env", action="store_true")
    parser.add_argument("--write-evidence", default="")
    args = parser.parse_args(argv)
    packet = run_batch_b_telegram_readonly_proof(repo_root=args.repo_root, live_readonly_telegram=args.live_readonly_telegram, include_process_env=args.include_process_env)
    if args.write_evidence:
        write_evidence(packet, args.write_evidence)
    else:
        print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
