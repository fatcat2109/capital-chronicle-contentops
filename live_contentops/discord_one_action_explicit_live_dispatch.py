"""Explicit one-action Discord live dispatch authorization/result helpers.

This module validates the prior non-live operator gate, writes current task
live authorization, and can enrich redacted wrapper result packets. It does not
print or store webhook URLs, env values, response bodies, or response headers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops.discord_approved_outbox_live_dispatch import run_approved_outbox_dispatch

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH_V0"
PLATFORM = "discord"
ENDPOINT_FAMILY = "discord_execute_webhook"
METHOD = "POST"
SELECTED_ACTION_ID = "discord_supervised_dispatch_action_announcements"
TARGET_NAME = "announcements"
PAYLOAD_ID = "discord_dryrun_announcement_001"
PAYLOAD_TYPE = "announcement"
PAYLOAD_HASH = "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d"
ENV_KEY_NAME = "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
DESTINATION_BINDING_ID = "discord_announcements_capital_chronicle_01"
CREDENTIAL_HANDLE_ID = "discord_announcements_webhook_01"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
WRAPPER_MODULE = "live_contentops.discord_approved_outbox_live_dispatch"
USER_AGENT_REQUIRED = "CapitalChronicleContentOps/1.0"
REQUEST_BUDGET_MAX = 1
RETRY_BUDGET_MAX = 0
TIMEOUT_SECONDS = 10
WAIT_QUERY_PARAM = False
GATE_PACKET_PATH = Path("docs/automation/DISCORD_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
AUTHORIZATION_PACKET_PATH = Path("docs/automation/DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH/one_action_explicit_live_dispatch_authorization_packet.json")
RESULT_PACKET_PATH = Path("docs/automation/DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH/one_action_explicit_live_dispatch_result_packet.json")
IMPLEMENTATION_REPORT_FILENAME = "implementation_report.md"
NEXT_TASK_POINTER_FILENAME = "next_task_pointer.md"


class ExplicitLiveDispatchBlocked(RuntimeError):
    """Raised when explicit live dispatch preflight blocks before live call."""


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: str | Path, packet: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _path_text(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def validate_gate_packet(gate: dict[str, Any]) -> None:
    expected = {
        "approval_gate_status": "PASS",
        "selected_action_id": SELECTED_ACTION_ID,
        "selected_target_name": TARGET_NAME,
        "selected_payload_id": PAYLOAD_ID,
        "selected_payload_hash": PAYLOAD_HASH,
        "selected_payload_type": PAYLOAD_TYPE,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
    }
    for key, value in expected.items():
        if gate.get(key) != value:
            raise ExplicitLiveDispatchBlocked(f"gate_{key}_mismatch")
    if gate.get("future_live_dispatch_allowed") is not False:
        raise ExplicitLiveDispatchBlocked("prior_gate_historical_state_unexpected")
    binding = gate.get("approval_binding")
    if not isinstance(binding, dict):
        raise ExplicitLiveDispatchBlocked("approval_binding_missing")
    binding_expected = {
        "action_id": SELECTED_ACTION_ID,
        "target_name": TARGET_NAME,
        "payload_id": PAYLOAD_ID,
        "payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "request_budget_required": REQUEST_BUDGET_MAX,
        "retry_budget_required": RETRY_BUDGET_MAX,
        "wait_query_param": WAIT_QUERY_PARAM,
        "user_agent_required": USER_AGENT_REQUIRED,
    }
    for key, value in binding_expected.items():
        if binding.get(key) != value:
            raise ExplicitLiveDispatchBlocked(f"binding_{key}_mismatch")


def authorization_packet(source_operator_gate_packet: str | Path = GATE_PACKET_PATH) -> dict[str, Any]:
    gate = load_json(source_operator_gate_packet)
    validate_gate_packet(gate)
    return {
        "task_label": TASK_LABEL,
        "platform": PLATFORM,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "source_operator_gate_packet": _path_text(source_operator_gate_packet),
        "selected_action_id": SELECTED_ACTION_ID,
        "selected_target_name": TARGET_NAME,
        "selected_payload_id": PAYLOAD_ID,
        "selected_payload_hash": PAYLOAD_HASH,
        "selected_payload_type": PAYLOAD_TYPE,
        "env_key_name": ENV_KEY_NAME,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "prior_gate_future_live_dispatch_allowed": False,
        "prior_gate_operator_authorization_state": gate.get("operator_authorization_state"),
        "current_task_operator_authorization": True,
        "current_task_live_dispatch_allowed": True,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wait_query_param": WAIT_QUERY_PARAM,
        "user_agent_required": USER_AGENT_REQUIRED,
        "no_raw_secret_output": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
    }


def write_authorization_packet(source_operator_gate_packet: str | Path, output: str | Path) -> dict[str, Any]:
    packet = authorization_packet(source_operator_gate_packet)
    write_json(output, packet)
    return packet


def verify_env_key_present(environ: Any) -> bool:
    return bool(environ.get(ENV_KEY_NAME))


def result_packet_from_wrapper(wrapper_packet: dict[str, Any], source_operator_gate_packet: str | Path = GATE_PACKET_PATH) -> dict[str, Any]:
    status = wrapper_packet.get("result_status")
    request_count = int(wrapper_packet.get("request_count_attempted", 0))
    retry_count = int(wrapper_packet.get("retry_count_attempted", 0))
    if request_count > REQUEST_BUDGET_MAX:
        status = "BLOCKED"
        diagnostic = "request_budget_exhausted"
    else:
        diagnostic = wrapper_packet.get("diagnostic_interpretation")
    return {
        "task_label": TASK_LABEL,
        "result_status": status,
        "platform": PLATFORM,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "selected_action_id": SELECTED_ACTION_ID,
        "target_name": TARGET_NAME,
        "payload_id": PAYLOAD_ID,
        "payload_type": PAYLOAD_TYPE,
        "payload_hash": PAYLOAD_HASH,
        "env_key_name": ENV_KEY_NAME,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "adapter_module": ADAPTER_MODULE,
        "wrapper_module": WRAPPER_MODULE,
        "source_operator_gate_packet": _path_text(source_operator_gate_packet),
        "current_task_operator_authorization": True,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": request_count,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": retry_count,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wait_query_param": WAIT_QUERY_PARAM,
        "user_agent_set": wrapper_packet.get("user_agent_set") is True,
        "http_status_code": wrapper_packet.get("http_status_code"),
        "status_code_class": wrapper_packet.get("status_code_class"),
        "diagnostic_interpretation": diagnostic,
        "live_write_completed": bool(wrapper_packet.get("live_write_completed", False)) and status == "PASS",
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "public_url": None,
        "webhook_message_id": None,
    }


def write_result_packet(wrapper_result_path: str | Path, output: str | Path, source_operator_gate_packet: str | Path = GATE_PACKET_PATH) -> dict[str, Any]:
    wrapper_packet = load_json(wrapper_result_path)
    packet = result_packet_from_wrapper(wrapper_packet, source_operator_gate_packet)
    write_json(output, packet)
    return packet


def run_dry_run(output: str | Path = RESULT_PACKET_PATH, source_operator_gate_packet: str | Path = GATE_PACKET_PATH) -> dict[str, Any]:
    gate = load_json(source_operator_gate_packet)
    validate_gate_packet(gate)
    wrapper_packet = run_approved_outbox_dispatch(
        output_path=output,
        execute=False,
        target_name=TARGET_NAME,
        payload_id=PAYLOAD_ID,
        expected_payload_hash=PAYLOAD_HASH,
    )
    packet = result_packet_from_wrapper(wrapper_packet, source_operator_gate_packet)
    write_json(output, packet)
    return packet


def run_live_once(output: str | Path = RESULT_PACKET_PATH, source_operator_gate_packet: str | Path = GATE_PACKET_PATH, environ: Any | None = None, opener: Any | None = None) -> dict[str, Any]:
    gate = load_json(source_operator_gate_packet)
    validate_gate_packet(gate)
    wrapper_packet = run_approved_outbox_dispatch(
        output_path=output,
        execute=True,
        target_name=TARGET_NAME,
        payload_id=PAYLOAD_ID,
        expected_payload_hash=PAYLOAD_HASH,
        environ=environ,
        opener=opener,
    )
    packet = result_packet_from_wrapper(wrapper_packet, source_operator_gate_packet)
    write_json(output, packet)
    return packet


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord One Action Explicit Live Dispatch Implementation Report\n\nStatus: `{packet.get('result_status', 'PENDING')}`\n\n- Selected action: `{SELECTED_ACTION_ID}`\n- Target: `{TARGET_NAME}`\n- Payload: `{PAYLOAD_ID}`\n- Payload hash: `{PAYLOAD_HASH}`\n- Request budget: `1`\n- Retry budget: `0`\n- Raw secret output: `false`\n"""


def next_task_pointer() -> str:
    return """# Next Task Pointer\n\nRecommended next task:\n\n`TASK_CONTENTOPS_V6_DISCORD_ONE_ACTION_LIVE_DISPATCH_CLOSEOUT_V0`\n\nGoal: close out explicit one-action live dispatch evidence without another live POST.\n"""


def write_docs(output_dir: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / IMPLEMENTATION_REPORT_FILENAME).write_text(implementation_report(packet), encoding="utf-8")
    (out / NEXT_TASK_POINTER_FILENAME).write_text(next_task_pointer(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discord one-action explicit live dispatch helper")
    parser.add_argument("--operator-gate-packet", default=str(GATE_PACKET_PATH))
    parser.add_argument("--authorization-output", default=str(AUTHORIZATION_PACKET_PATH))
    parser.add_argument("--result-output", default=str(RESULT_PACKET_PATH))
    parser.add_argument("--write-authorization", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--enrich-result", action="store_true")
    args = parser.parse_args(argv)
    if args.write_authorization:
        packet = write_authorization_packet(args.operator_gate_packet, args.authorization_output)
    elif args.dry_run:
        packet = run_dry_run(args.result_output, args.operator_gate_packet)
    elif args.execute:
        packet = run_live_once(args.result_output, args.operator_gate_packet)
    elif args.enrich_result:
        packet = write_result_packet(args.result_output, args.result_output, args.operator_gate_packet)
    else:
        packet = authorization_packet(args.operator_gate_packet)
    write_docs(Path(args.result_output).parent, packet)
    print(json.dumps({
        "task_label": packet["task_label"],
        "result_status": packet.get("result_status", "AUTHORIZED"),
        "selected_action_id": packet["selected_action_id"],
        "target_name": packet.get("target_name", packet.get("selected_target_name")),
        "payload_id": packet.get("payload_id", packet.get("selected_payload_id")),
        "request_count_attempted": packet.get("request_count_attempted", 0),
        "retry_count_attempted": packet.get("retry_count_attempted", 0),
        "http_status_code": packet.get("http_status_code"),
        "diagnostic_interpretation": packet.get("diagnostic_interpretation", "authorized_not_executed"),
        "live_write_completed": packet.get("live_write_completed", False),
        "raw_secret_output": False,
        "webhook_url_printed": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
