"""Approved outbox Discord live dispatch pilot wrapper.

Verifies an approved payload/hash path, then delegates dispatch to
DiscordDispatchAdapter. Dry-run mode attempts zero network requests. Execute mode
is only for explicitly authorized one-request pilots.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from live_contentops.discord_dispatch_adapter import (
    DiscordDispatchAdapter,
    DiscordDispatchBlocked,
    REQUEST_BUDGET_MAX,
    RETRY_BUDGET_MAX,
    TARGET_CONFIGS,
    TIMEOUT_SECONDS,
    USER_AGENT,
    WAIT_QUERY_PARAM,
    diagnostic_interpretation,
    load_payload_packet,
    select_payload,
    status_code_class,
)

ANNOUNCEMENTS_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0"
SUBSTACK_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUBSTACK_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
PLATFORM = "discord"
PAYLOAD_PACKET_PATH = Path("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
HASH_PACKET_PATH = Path("docs/automation/DISCORD_PAYLOAD_HASH_APPROVAL_GATE/hash_approval_gate_packet.json")
RESULT_PACKET_PATH = Path(
    "docs/automation/DISCORD_APPROVED_OUTBOX_LIVE_DISPATCH/approved_outbox_live_dispatch_result_packet.json"
)
SUBSTACK_RESULT_PACKET_PATH = Path(
    "docs/automation/DISCORD_SUBSTACK_APPROVED_OUTBOX_LIVE_DISPATCH/substack_approved_outbox_live_dispatch_result_packet.json"
)


@dataclass(frozen=True)
class ApprovedOutboxTarget:
    target_name: str
    payload_id: str
    payload_type: str
    expected_payload_hash: str
    task_label: str
    default_output_path: Path

    @property
    def env_key_name(self) -> str:
        return TARGET_CONFIGS[self.target_name].env_key_name

    @property
    def destination_binding_id(self) -> str:
        return TARGET_CONFIGS[self.target_name].destination_binding_id

    @property
    def credential_handle_id(self) -> str:
        return TARGET_CONFIGS[self.target_name].credential_handle_id


APPROVED_TARGETS: dict[str, ApprovedOutboxTarget] = {
    "announcements": ApprovedOutboxTarget(
        target_name="announcements",
        payload_id="discord_dryrun_announcement_001",
        payload_type="announcement",
        expected_payload_hash="b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d",
        task_label=ANNOUNCEMENTS_TASK_LABEL,
        default_output_path=RESULT_PACKET_PATH,
    ),
    "substack_drops": ApprovedOutboxTarget(
        target_name="substack_drops",
        payload_id="discord_dryrun_substack_drop_001",
        payload_type="substack_drop",
        expected_payload_hash="a084ced7249d9b764132e17888c15c5cfd6177329dbe5ce718311e07e849175d",
        task_label=SUBSTACK_TASK_LABEL,
        default_output_path=SUBSTACK_RESULT_PACKET_PATH,
    ),
}

# Backward-compatible constants for existing announcements tests/imports.
TASK_LABEL = ANNOUNCEMENTS_TASK_LABEL
TARGET_NAME = APPROVED_TARGETS["announcements"].target_name
ENV_KEY_NAME = APPROVED_TARGETS["announcements"].env_key_name
DESTINATION_BINDING_ID = APPROVED_TARGETS["announcements"].destination_binding_id
CREDENTIAL_HANDLE_ID = APPROVED_TARGETS["announcements"].credential_handle_id
PAYLOAD_ID = APPROVED_TARGETS["announcements"].payload_id
PAYLOAD_TYPE = APPROVED_TARGETS["announcements"].payload_type
EXPECTED_PAYLOAD_HASH = APPROVED_TARGETS["announcements"].expected_payload_hash
SUBSTACK_PAYLOAD_ID = APPROVED_TARGETS["substack_drops"].payload_id
SUBSTACK_EXPECTED_PAYLOAD_HASH = APPROVED_TARGETS["substack_drops"].expected_payload_hash


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


def resolve_target(target_name: str, payload_id: str | None = None) -> ApprovedOutboxTarget:
    if target_name not in APPROVED_TARGETS:
        raise DiscordDispatchBlocked("approved_outbox_target_not_supported")
    target = APPROVED_TARGETS[target_name]
    if payload_id is not None and payload_id != target.payload_id:
        raise DiscordDispatchBlocked("payload_id_not_supported_for_target")
    return target


def validate_payload_and_approval(
    payload: dict[str, Any],
    approval: dict[str, Any],
    expected_payload_hash: str,
    target: ApprovedOutboxTarget | None = None,
) -> None:
    target = target or APPROVED_TARGETS["announcements"]
    expected_pairs = {
        "payload_id": target.payload_id,
        "payload_type": target.payload_type,
        "target_name": target.target_name,
        "destination_binding_id": target.destination_binding_id,
        "credential_handle_id": target.credential_handle_id,
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
    target: ApprovedOutboxTarget | None = None,
    blocker: str | None = None,
    dry_run_precheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = target or APPROVED_TARGETS["announcements"]
    dispatch_result = dispatch_result or {}
    http_status_code = dispatch_result.get("http_status_code")
    packet = {
        "task_label": target.task_label,
        "result_status": result_status,
        "platform": PLATFORM,
        "target_name": target.target_name,
        "env_key_name": target.env_key_name,
        "destination_binding_id": target.destination_binding_id,
        "credential_handle_id": target.credential_handle_id,
        "payload_id": target.payload_id,
        "payload_type": target.payload_type,
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
    output_path: str | Path | None = None,
    execute: bool = False,
    target_name: str = "announcements",
    payload_id: str | None = None,
    expected_payload_hash: str | None = None,
    environ: Any | None = None,
    opener: Callable[..., Any] | None = None,
    adapter_factory: Callable[..., DiscordDispatchAdapter] = DiscordDispatchAdapter,
    dry_run_precheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        target = resolve_target(target_name, payload_id)
        expected_hash = expected_payload_hash or target.expected_payload_hash
        payload_packet = load_payload_packet(payload_packet_path)
        payload = select_payload(payload_packet, target.payload_id)
        hash_packet = load_json(hash_packet_path)
        approval = select_hash_approval(hash_packet, target.payload_id, expected_hash)
        validate_payload_and_approval(payload, approval, expected_hash, target)
        adapter = adapter_factory(environ=environ, opener=opener)
        dispatch_result = adapter.dispatch(
            payload,
            target_name=target.target_name,
            destination_binding_id=target.destination_binding_id,
            credential_handle_id=target.credential_handle_id,
            payload_hash=expected_hash,
            execute=execute,
        )
        packet = redacted_packet_from_result(
            dispatch_result=dispatch_result,
            payload_hash=expected_hash,
            result_status=dispatch_result["result_status"],
            target=target,
            dry_run_precheck=dry_run_precheck,
        )
    except DiscordDispatchBlocked as exc:
        fallback_target = APPROVED_TARGETS.get(target_name, APPROVED_TARGETS["announcements"])
        packet = redacted_packet_from_result(
            dispatch_result=None,
            payload_hash=expected_payload_hash or fallback_target.expected_payload_hash,
            result_status="BLOCKED",
            target=fallback_target,
            blocker=str(exc),
            dry_run_precheck=dry_run_precheck,
        )
    write_packet(packet, output_path or APPROVED_TARGETS.get(target_name, APPROVED_TARGETS["announcements"]).default_output_path)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Approved outbox Discord dispatch pilot")
    parser.add_argument("--payload-packet", default=str(PAYLOAD_PACKET_PATH))
    parser.add_argument("--hash-packet", default=str(HASH_PACKET_PATH))
    parser.add_argument("--output", default=None)
    parser.add_argument("--target", default="announcements", choices=sorted(APPROVED_TARGETS))
    parser.add_argument("--payload-id", default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    packet = run_approved_outbox_dispatch(
        payload_packet_path=args.payload_packet,
        hash_packet_path=args.hash_packet,
        output_path=args.output,
        execute=args.execute,
        target_name=args.target,
        payload_id=args.payload_id,
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
