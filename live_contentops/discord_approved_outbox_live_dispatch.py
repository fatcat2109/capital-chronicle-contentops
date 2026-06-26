"""Approved outbox Discord live dispatch pilot wrapper.

This wrapper verifies the approved payload/hash path, then delegates dispatch to
DiscordDispatchAdapter. Dry-run mode attempts zero network requests. Execute mode
is for this explicitly authorized one-request pilot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from live_contentops.discord_dispatch_adapter import (
    DiscordDispatchAdapter,
    DiscordDispatchBlocked,
    REQUEST_BUDGET_MAX,
    RETRY_BUDGET_MAX,
    TIMEOUT_SECONDS,
    USER_AGENT,
    WAIT_QUERY_PARAM,
    diagnostic_interpretation,
    load_payload_packet,
    select_payload,
    status_code_class,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
PLATFORM = "discord"
TARGET_NAME = "announcements"
ENV_KEY_NAME = "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
DESTINATION_BINDING_ID = "discord_announcements_capital_chronicle_01"
CREDENTIAL_HANDLE_ID = "discord_announcements_webhook_01"
PAYLOAD_ID = "discord_dryrun_announcement_001"
PAYLOAD_TYPE = "announcement"
EXPECTED_PAYLOAD_HASH = "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d"
PAYLOAD_PACKET_PATH = Path("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
HASH_PACKET_PATH = Path("docs/automation/DISCORD_PAYLOAD_HASH_APPROVAL_GATE/hash_approval_gate_packet.json")
RESULT_PACKET_PATH = Path(
    "docs/automation/DISCORD_APPROVED_OUTBOX_LIVE_DISPATCH/approved_outbox_live_dispatch_result_packet.json"
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def approval_packets(hash_packet: dict[str, Any]) -> list[dict[str, Any]]:
    packets = hash_packet.get("approval_packets", [])
    return [packet for packet in packets if isinstance(packet, dict)]


def select_hash_approval(hash_packet: dict[str, Any], payload_id: str, expected_payload_hash: str) -> dict[str, Any]:
    for packet in approval_packets(hash_packet):
        if packet.get("payload_id") == payload_id and packet.get("payload_hash") == expected_payload_hash:
            return packet
    raise DiscordDispatchBlocked("payload_hash_approval_not_found")


def validate_payload_and_approval(payload: dict[str, Any], approval: dict[str, Any], expected_payload_hash: str) -> None:
    expected_pairs = {
        "payload_id": PAYLOAD_ID,
        "payload_type": PAYLOAD_TYPE,
        "target_name": TARGET_NAME,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
    }
    for key, expected in expected_pairs.items():
        if payload.get(key) != expected:
            raise DiscordDispatchBlocked(f"payload_{key}_mismatch")
        if approval.get(key) != expected:
            raise DiscordDispatchBlocked(f"approval_{key}_mismatch")
    if approval.get("payload_hash") != expected_payload_hash:
        raise DiscordDispatchBlocked("payload_hash_mismatch")


def redacted_packet_from_result(
    *,
    dispatch_result: dict[str, Any] | None,
    payload_hash: str,
    result_status: str,
    blocker: str | None = None,
    dry_run_precheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dispatch_result = dispatch_result or {}
    http_status_code = dispatch_result.get("http_status_code")
    packet = {
        "task_label": TASK_LABEL,
        "result_status": result_status,
        "platform": PLATFORM,
        "target_name": TARGET_NAME,
        "env_key_name": ENV_KEY_NAME,
        "destination_binding_id": DESTINATION_BINDING_ID,
        "credential_handle_id": CREDENTIAL_HANDLE_ID,
        "payload_id": PAYLOAD_ID,
        "payload_type": PAYLOAD_TYPE,
        "payload_hash": payload_hash,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": int(dispatch_result.get("request_count_attempted", 0)),
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wait_query_param": WAIT_QUERY_PARAM,
        "user_agent_set": USER_AGENT == "CapitalChronicleContentOps/1.0",
        "http_status_code": http_status_code,
        "status_code_class": dispatch_result.get("status_code_class", status_code_class(http_status_code)),
        "diagnostic_interpretation": dispatch_result.get(
            "diagnostic_interpretation",
            "not_attempted" if http_status_code is None else diagnostic_interpretation(http_status_code),
        ),
        "live_write_completed": bool(dispatch_result.get("live_write_completed", False)),
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "public_url": None,
        "webhook_message_id": None,
        "webhook_url_printed": False,
        "adapter_module": ADAPTER_MODULE,
    }
    if blocker is not None:
        packet["blocker"] = blocker
    if dry_run_precheck is not None:
        packet["dry_run_precheck"] = dry_run_precheck
    return packet


def write_packet(packet: dict[str, Any], output_path: str | Path) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_approved_outbox_dispatch(
    *,
    payload_packet_path: str | Path = PAYLOAD_PACKET_PATH,
    hash_packet_path: str | Path = HASH_PACKET_PATH,
    output_path: str | Path = RESULT_PACKET_PATH,
    execute: bool = False,
    expected_payload_hash: str = EXPECTED_PAYLOAD_HASH,
    environ: Any | None = None,
    opener: Callable[..., Any] | None = None,
    adapter_factory: Callable[..., DiscordDispatchAdapter] = DiscordDispatchAdapter,
    dry_run_precheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        payload_packet = load_payload_packet(payload_packet_path)
        payload = select_payload(payload_packet, PAYLOAD_ID)
        hash_packet = load_json(hash_packet_path)
        approval = select_hash_approval(hash_packet, PAYLOAD_ID, expected_payload_hash)
        validate_payload_and_approval(payload, approval, expected_payload_hash)
        adapter = adapter_factory(environ=environ, opener=opener)
        dispatch_result = adapter.dispatch(
            payload,
            target_name=TARGET_NAME,
            destination_binding_id=DESTINATION_BINDING_ID,
            credential_handle_id=CREDENTIAL_HANDLE_ID,
            payload_hash=expected_payload_hash,
            execute=execute,
        )
        packet = redacted_packet_from_result(
            dispatch_result=dispatch_result,
            payload_hash=expected_payload_hash,
            result_status=dispatch_result["result_status"],
            dry_run_precheck=dry_run_precheck,
        )
    except DiscordDispatchBlocked as exc:
        packet = redacted_packet_from_result(
            dispatch_result=None,
            payload_hash=expected_payload_hash,
            result_status="BLOCKED",
            blocker=str(exc),
            dry_run_precheck=dry_run_precheck,
        )
    write_packet(packet, output_path)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Approved outbox Discord dispatch pilot")
    parser.add_argument("--payload-packet", default=str(PAYLOAD_PACKET_PATH))
    parser.add_argument("--hash-packet", default=str(HASH_PACKET_PATH))
    parser.add_argument("--output", default=str(RESULT_PACKET_PATH))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    packet = run_approved_outbox_dispatch(
        payload_packet_path=args.payload_packet,
        hash_packet_path=args.hash_packet,
        output_path=args.output,
        execute=args.execute,
    )
    print(json.dumps({
        "task_label": packet["task_label"],
        "result_status": packet["result_status"],
        "target_name": packet["target_name"],
        "payload_id": packet["payload_id"],
        "payload_hash": packet["payload_hash"],
        "request_count_attempted": packet["request_count_attempted"],
        "retry_count_attempted": packet["retry_count_attempted"],
        "http_status_code": packet["http_status_code"],
        "diagnostic_interpretation": packet["diagnostic_interpretation"],
        "live_write_completed": packet["live_write_completed"],
        "raw_secret_output": False,
        "webhook_url_printed": False,
    }, indent=2, sort_keys=True))
    return 0 if packet["result_status"] in {"PASS", "DRY_RUN", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
