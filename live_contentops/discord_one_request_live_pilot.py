"""One-request Discord live webhook pilot.

Executes exactly one authorized Discord Execute Webhook POST only when called with
--execute. Audit output is redacted: no webhook URL, webhook ID, token, request
headers, response headers, response body, env value, or token metadata.
"""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_ONE_REQUEST_LIVE_WEBHOOK_PILOT_V0"
PLATFORM = "discord"
ENDPOINT_FAMILY = "discord_execute_webhook"
METHOD = "POST"
TARGET_NAME = "announcements"
DISPATCH_CANDIDATE_ID = "discord_candidate_discord_outbox_discord_dryrun_announcement_001"
PAYLOAD_ID = "discord_dryrun_announcement_001"
PAYLOAD_TYPE = "announcement"
DESTINATION_BINDING_ID = "discord_announcements_capital_chronicle_01"
CREDENTIAL_HANDLE_ID = "discord_announcements_webhook_01"
ENV_KEY_NAME = "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
PAYLOAD_HASH = "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d"
REQUEST_BUDGET_MAX = 1
RETRY_BUDGET_MAX = 0
TIMEOUT_SECONDS = 10
WAIT_QUERY_PARAM = False

FORBIDDEN_PAYLOAD_KEYS = {"attachments", "attachment", "files", "file", "components", "poll", "thread_id", "thread_name"}
FORBIDDEN_FINANCE_PHRASES = ("buy", "sell", "hold", "price target", "position sizing", "financial advice")


class LivePilotBlocked(RuntimeError):
    """Raised when live pilot preconditions fail before network attempt."""


@dataclass
class RequestBudgetGuard:
    remaining_requests: int = REQUEST_BUDGET_MAX
    attempted_requests: int = 0

    def spend_before_post(self) -> None:
        if self.remaining_requests <= 0:
            raise LivePilotBlocked("request_budget_exhausted")
        self.remaining_requests -= 1
        self.attempted_requests += 1


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def select_payload(sample_payloads: dict[str, Any]) -> dict[str, Any]:
    for payload in sample_payloads.get("payloads", []):
        if payload.get("payload_id") == PAYLOAD_ID:
            if payload.get("payload_type") != PAYLOAD_TYPE:
                raise LivePilotBlocked("payload_type_mismatch")
            if payload.get("target_name") != TARGET_NAME:
                raise LivePilotBlocked("target_name_mismatch")
            if payload.get("destination_binding_id") != DESTINATION_BINDING_ID:
                raise LivePilotBlocked("destination_binding_id_mismatch")
            if payload.get("credential_handle_id") != CREDENTIAL_HANDLE_ID:
                raise LivePilotBlocked("credential_handle_id_mismatch")
            return payload
    raise LivePilotBlocked("payload_missing")


def validate_gate_packet(gate_packet: dict[str, Any]) -> None:
    checks = {
        "candidate_id_mismatch": gate_packet.get("selected_dispatch_candidate_id") == DISPATCH_CANDIDATE_ID,
        "payload_id_mismatch": gate_packet.get("selected_payload_id") == PAYLOAD_ID,
        "payload_hash_mismatch": gate_packet.get("selected_payload_hash") == PAYLOAD_HASH,
        "payload_type_mismatch": gate_packet.get("selected_payload_type") == PAYLOAD_TYPE,
        "target_name_mismatch": gate_packet.get("selected_target_name") == TARGET_NAME,
        "destination_binding_mismatch": gate_packet.get("selected_destination_binding_id") == DESTINATION_BINDING_ID,
        "credential_handle_mismatch": gate_packet.get("selected_credential_handle_id") == CREDENTIAL_HANDLE_ID,
        "env_key_mismatch": gate_packet.get("env_key_name") == ENV_KEY_NAME,
        "endpoint_family_mismatch": gate_packet.get("endpoint_family") == ENDPOINT_FAMILY,
        "method_mismatch": gate_packet.get("method") == METHOD,
        "request_budget_mismatch": gate_packet.get("request_budget_max") == REQUEST_BUDGET_MAX,
        "retry_budget_mismatch": gate_packet.get("retry_budget_max") == RETRY_BUDGET_MAX,
        "timeout_mismatch": gate_packet.get("timeout_seconds") == TIMEOUT_SECONDS,
        "wait_param_mismatch": gate_packet.get("wait_query_param") is WAIT_QUERY_PARAM,
    }
    for name, ok in checks.items():
        if not ok:
            raise LivePilotBlocked(name)


def build_request_body(payload: dict[str, Any]) -> dict[str, Any]:
    body = copy.deepcopy(payload.get("redacted_webhook_json_preview"))
    if not isinstance(body, dict):
        raise LivePilotBlocked("request_body_missing")
    body["allowed_mentions"] = {"parse": []}
    for key in FORBIDDEN_PAYLOAD_KEYS:
        if key in body:
            raise LivePilotBlocked(f"forbidden_payload_key_{key}")
    text = json.dumps(body, sort_keys=True).lower()
    for phrase in FORBIDDEN_FINANCE_PHRASES:
        if phrase in text:
            raise LivePilotBlocked("forbidden_finance_language")
    return body


def with_wait_false(raw_url: str) -> str:
    url_parse = __import__("urllib.parse", fromlist=["parse"])
    parts = url_parse.urlsplit(raw_url)
    query = url_parse.parse_qsl(parts.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if k != "wait"]
    query.append(("wait", "false"))
    return url_parse.urlunsplit((parts.scheme, parts.netloc, parts.path, url_parse.urlencode(query), parts.fragment))


def status_code_class(status_code: int | None) -> str:
    if status_code is None:
        return "not_attempted"
    if 200 <= status_code <= 299:
        return "2xx"
    if 400 <= status_code <= 499:
        return "4xx"
    if 500 <= status_code <= 599:
        return "5xx"
    return "other"


def make_result_packet(*, result_status: str, request_count_attempted: int, network_call_attempted: bool, webhook_url_loaded: bool, status_class: str, live_write_completed: bool, live_write_failed: bool, error_class: str | None, audit_notes: list[str]) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "result_status": result_status,
        "platform": PLATFORM,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "target_name": TARGET_NAME,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
        "dispatch_candidate_id": DISPATCH_CANDIDATE_ID,
        "payload_id": PAYLOAD_ID,
        "payload_hash": PAYLOAD_HASH,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": request_count_attempted,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wait_query_param": WAIT_QUERY_PARAM,
        "allowed_mentions_parse_empty": True,
        "network_call_attempted": network_call_attempted,
        "webhook_url_loaded": webhook_url_loaded,
        "webhook_url_printed": False,
        "raw_secret_output": False,
        "status_code_class": status_class,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "public_url": None,
        "webhook_message_id": None,
        "live_write_completed": live_write_completed,
        "live_write_failed": live_write_failed,
        "error_class": error_class,
        "audit_notes": audit_notes,
    }


def execute_post_once(raw_url: str, body: dict[str, Any], guard: RequestBudgetGuard, opener: Callable[..., Any] | None = None) -> tuple[int | None, str | None]:
    guard.spend_before_post()
    url_request = __import__("urllib.request", fromlist=["request"])
    url_error = __import__("urllib.error", fromlist=["error"])
    post_url = with_wait_false(raw_url)
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    req = url_request.Request(post_url, data=data, method=METHOD, headers={"Content-Type": "application/json"})
    opener = opener or url_request.urlopen
    try:
        response = opener(req, timeout=TIMEOUT_SECONDS)
        return int(getattr(response, "status", getattr(response, "code", 0))), None
    except url_error.HTTPError as exc:
        return int(exc.code), exc.__class__.__name__
    except Exception as exc:
        return None, exc.__class__.__name__


def run_live_pilot(gate_packet_path: str | Path, sample_payloads_path: str | Path, output_path: str | Path, *, execute: bool = False, environ: Any | None = None, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    gate_packet = load_json(gate_packet_path)
    sample_payloads = load_json(sample_payloads_path)
    validate_gate_packet(gate_packet)
    payload = select_payload(sample_payloads)
    body = build_request_body(payload)
    guard = RequestBudgetGuard()
    result_status = "BLOCKED"
    network_call_attempted = False
    webhook_url_loaded = False
    status_class = "not_attempted"
    live_write_completed = False
    live_write_failed = False
    error_class = None
    audit_notes = ["dry_run_no_network"]
    if execute:
        env = environ if environ is not None else getattr(__import__("os"), "environ")
        raw_url = env.get(ENV_KEY_NAME)
        webhook_url_loaded = True
        if not raw_url:
            raise LivePilotBlocked("env_key_missing")
        network_call_attempted = True
        status_code, error_class = execute_post_once(raw_url, body, guard, opener)
        status_class = status_code_class(status_code)
        live_write_completed = status_class == "2xx"
        live_write_failed = not live_write_completed
        result_status = "PASS" if live_write_completed else "FAIL"
        audit_notes = ["one_post_attempted", "no_retry_attempted", "redacted_audit_only"]
    packet = make_result_packet(
        result_status=result_status,
        request_count_attempted=guard.attempted_requests,
        network_call_attempted=network_call_attempted,
        webhook_url_loaded=webhook_url_loaded,
        status_class=status_class,
        live_write_completed=live_write_completed,
        live_write_failed=live_write_failed,
        error_class=error_class,
        audit_notes=audit_notes,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run exactly one redacted Discord webhook live pilot")
    parser.add_argument("--gate-packet", required=True)
    parser.add_argument("--sample-payloads", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        packet = run_live_pilot(args.gate_packet, args.sample_payloads, args.output, execute=args.execute)
    except LivePilotBlocked as exc:
        packet = make_result_packet(
            result_status="BLOCKED",
            request_count_attempted=0,
            network_call_attempted=False,
            webhook_url_loaded=False,
            status_class="not_attempted",
            live_write_completed=False,
            live_write_failed=False,
            error_class=exc.__class__.__name__,
            audit_notes=[str(exc)],
        )
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result_status": packet["result_status"],
        "platform": PLATFORM,
        "target_name": TARGET_NAME,
        "payload_id": PAYLOAD_ID,
        "payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
        "request_count_attempted": packet["request_count_attempted"],
        "retry_count_attempted": packet["retry_count_attempted"],
        "timeout_seconds": TIMEOUT_SECONDS,
        "status_code_class": packet["status_code_class"],
        "live_write_completed": packet["live_write_completed"],
        "webhook_url_printed": False,
        "raw_secret_output": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
