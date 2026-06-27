"""Closeout for first full-path Discord supervised live dispatch.

Reads prior evidence packets only. Does not read environment variables, send
network requests, mutate source packets, or create live controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_ONE_ACTION_LIVE_DISPATCH_CLOSEOUT_V0"
PLATFORM = "discord"
SELECTED_ACTION_ID = "discord_supervised_dispatch_action_announcements"
TARGET_NAME = "announcements"
PAYLOAD_ID = "discord_dryrun_announcement_001"
PAYLOAD_TYPE = "announcement"
PAYLOAD_HASH = "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d"
DESTINATION_BINDING_ID = "discord_announcements_capital_chronicle_01"
CREDENTIAL_HANDLE_ID = "discord_announcements_webhook_01"
ENV_KEY_NAME = "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
OPERATOR_GATE_PACKET_PATH = Path("docs/automation/DISCORD_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json")
AUTHORIZATION_PACKET_PATH = Path("docs/automation/DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH/one_action_explicit_live_dispatch_authorization_packet.json")
RESULT_PACKET_PATH = Path("docs/automation/DISCORD_ONE_ACTION_EXPLICIT_LIVE_DISPATCH/one_action_explicit_live_dispatch_result_packet.json")
OUTPUT_PACKET_PATH = Path("docs/automation/DISCORD_ONE_ACTION_LIVE_DISPATCH_CLOSEOUT/one_action_live_dispatch_closeout_packet.json")
IMPLEMENTATION_REPORT_FILENAME = "implementation_report.md"
NEXT_TASK_POINTER_FILENAME = "next_task_pointer.md"


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, packet: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _path_text(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _http_2xx(status: Any) -> bool:
    return isinstance(status, int) and 200 <= status <= 299


def _matches(packet: dict[str, Any], pairs: dict[str, Any]) -> bool:
    return all(packet.get(key) == value for key, value in pairs.items())


def evaluate_packets(gate: dict[str, Any], authorization: dict[str, Any], result: dict[str, Any]) -> tuple[str, dict[str, bool], list[str]]:
    failures: list[str] = []
    gate_expected = {
        "approval_gate_status": "PASS",
        "selected_action_id": SELECTED_ACTION_ID,
        "selected_target_name": TARGET_NAME,
        "selected_payload_id": PAYLOAD_ID,
        "selected_payload_type": PAYLOAD_TYPE,
        "selected_payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
    }
    action_record_verified = _matches(gate, gate_expected) and gate.get("action_status_from_source") == "READY"
    operator_gate_verified = action_record_verified and gate.get("future_live_dispatch_allowed") is False
    if not action_record_verified:
        failures.append("operator_gate_action_evidence_conflict")
    if not operator_gate_verified:
        failures.append("operator_gate_historical_state_conflict")

    auth_expected = {
        "selected_action_id": SELECTED_ACTION_ID,
        "selected_target_name": TARGET_NAME,
        "selected_payload_id": PAYLOAD_ID,
        "selected_payload_type": PAYLOAD_TYPE,
        "selected_payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
        "current_task_operator_authorization": True,
        "current_task_live_dispatch_allowed": True,
    }
    current_task_authorization_verified = _matches(authorization, auth_expected)
    if not current_task_authorization_verified:
        failures.append("current_task_authorization_conflict")

    result_expected = {
        "result_status": "PASS",
        "selected_action_id": SELECTED_ACTION_ID,
        "target_name": TARGET_NAME,
        "payload_id": PAYLOAD_ID,
        "payload_type": PAYLOAD_TYPE,
        "payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
        "request_count_attempted": 1,
        "retry_count_attempted": 0,
        "live_write_completed": True,
    }
    live_result_verified = _matches(result, result_expected) and _http_2xx(result.get("http_status_code"))
    if not live_result_verified:
        failures.append("live_result_evidence_conflict")

    redacted_audit_verified = (
        result.get("response_body_recorded") is False
        and result.get("response_headers_recorded") is False
        and result.get("raw_secret_output") is False
        and result.get("webhook_url_printed") is False
        and result.get("public_url") is None
        and result.get("webhook_message_id") is None
    )
    if not redacted_audit_verified:
        failures.append("redacted_audit_conflict")

    chain_steps = {
        "action_record_verified": action_record_verified,
        "operator_gate_verified": operator_gate_verified,
        "current_task_authorization_verified": current_task_authorization_verified,
        "live_result_verified": live_result_verified,
        "redacted_audit_verified": redacted_audit_verified,
    }
    status = "PASS" if all(chain_steps.values()) else "FAIL"
    return status, chain_steps, failures


def closeout_packet(
    *,
    operator_gate_packet: str | Path = OPERATOR_GATE_PACKET_PATH,
    authorization_packet: str | Path = AUTHORIZATION_PACKET_PATH,
    result_packet: str | Path = RESULT_PACKET_PATH,
) -> dict[str, Any]:
    try:
        gate = load_json(operator_gate_packet)
        authorization = load_json(authorization_packet)
        result = load_json(result_packet)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        return {
            "task_label": TASK_LABEL,
            "closeout_status": "BLOCKED",
            "platform": PLATFORM,
            "blocker": exc.__class__.__name__,
            "source_operator_gate_packet": _path_text(operator_gate_packet),
            "source_current_authorization_packet": _path_text(authorization_packet),
            "source_live_result_packet": _path_text(result_packet),
            "full_supervised_dispatch_chain_verified": False,
            "safety": safety_packet(),
        }
    status, chain_steps, failures = evaluate_packets(gate, authorization, result)
    packet = {
        "task_label": TASK_LABEL,
        "closeout_status": status,
        "platform": PLATFORM,
        "source_operator_gate_packet": _path_text(operator_gate_packet),
        "source_current_authorization_packet": _path_text(authorization_packet),
        "source_live_result_packet": _path_text(result_packet),
        "selected_action_id": SELECTED_ACTION_ID,
        "target_name": TARGET_NAME,
        "payload_id": PAYLOAD_ID,
        "payload_type": PAYLOAD_TYPE,
        "payload_hash": PAYLOAD_HASH,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "env_key_name": ENV_KEY_NAME,
        "full_supervised_dispatch_chain_verified": status == "PASS",
        "chain_steps": chain_steps,
        "live_result": {
            "result_status": result.get("result_status"),
            "http_status_code": result.get("http_status_code"),
            "status_code_class": result.get("status_code_class"),
            "diagnostic_interpretation": result.get("diagnostic_interpretation"),
            "request_count_attempted": result.get("request_count_attempted"),
            "retry_count_attempted": result.get("retry_count_attempted"),
            "live_write_completed": result.get("live_write_completed"),
        },
        "safety": safety_packet(),
        "readiness_update": {
            "supervised_live_loop_verified": status == "PASS",
            "next_real_content_dispatch_requires_real_approved_payload": True,
            "dryrun_payload_should_not_be_used_for_public_content_repetition": True,
        },
    }
    if failures:
        packet["failures"] = failures
    return packet


def safety_packet() -> dict[str, bool]:
    return {
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "old_packets_mutated": False,
    }


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord One Action Live Dispatch Closeout\n\nStatus: `{packet.get('closeout_status')}`\n\n- Selected action: `{SELECTED_ACTION_ID}`\n- Target: `{TARGET_NAME}`\n- Payload: `{PAYLOAD_ID}`\n- Payload hash: `{PAYLOAD_HASH}`\n- Full supervised chain verified: `{str(packet.get('full_supervised_dispatch_chain_verified')).lower()}`\n- No live request in this task: `true`\n- No env read in this task: `true`\n"""


def next_task_pointer() -> str:
    return """# Next Task Pointer\n\nRecommended next task:\n\n`TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_APPROVED_PAYLOAD_QUEUE_V0`\n\nGoal: create fresh real-content approved payload/action records before any future live dispatch.\n"""


def write_docs(output: str | Path, packet: dict[str, Any]) -> None:
    out_dir = Path(output).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / IMPLEMENTATION_REPORT_FILENAME).write_text(implementation_report(packet), encoding="utf-8")
    (out_dir / NEXT_TASK_POINTER_FILENAME).write_text(next_task_pointer(), encoding="utf-8")


def generate_closeout(
    *,
    operator_gate_packet: str | Path,
    authorization_packet: str | Path,
    result_packet: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    packet = closeout_packet(
        operator_gate_packet=operator_gate_packet,
        authorization_packet=authorization_packet,
        result_packet=result_packet,
    )
    write_json(output, packet)
    write_docs(output, packet)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Close out Discord one-action live dispatch evidence")
    parser.add_argument("--operator-gate-packet", default=str(OPERATOR_GATE_PACKET_PATH))
    parser.add_argument("--authorization-packet", default=str(AUTHORIZATION_PACKET_PATH))
    parser.add_argument("--result-packet", default=str(RESULT_PACKET_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PACKET_PATH))
    args = parser.parse_args(argv)
    packet = generate_closeout(
        operator_gate_packet=args.operator_gate_packet,
        authorization_packet=args.authorization_packet,
        result_packet=args.result_packet,
        output=args.output,
    )
    print(json.dumps({
        "task_label": packet["task_label"],
        "closeout_status": packet["closeout_status"],
        "selected_action_id": packet.get("selected_action_id"),
        "target_name": packet.get("target_name"),
        "payload_id": packet.get("payload_id"),
        "payload_hash": packet.get("payload_hash"),
        "full_supervised_dispatch_chain_verified": packet.get("full_supervised_dispatch_chain_verified"),
        "no_live_request_in_this_task": packet.get("safety", {}).get("no_live_request_in_this_task"),
        "no_env_read_in_this_task": packet.get("safety", {}).get("no_env_read_in_this_task"),
    }, indent=2, sort_keys=True))
    return 0 if packet["closeout_status"] in {"PASS", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
