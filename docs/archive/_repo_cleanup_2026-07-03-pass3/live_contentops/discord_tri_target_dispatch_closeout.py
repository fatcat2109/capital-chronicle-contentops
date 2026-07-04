"""Deterministic tri-target closeout for Discord approved-outbox dispatch readiness.

Reads existing redacted evidence packets only. Does not read env and does not
perform network requests.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVED_OUTBOX_LIVE_DISPATCH_TRI_TARGET_CLOSEOUT_V0"
PLATFORM = "discord"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
USER_AGENT_REQUIRED = "CapitalChronicleContentOps/1.0"
OUTPUT_PACKET_PATH = Path("docs/automation/DISCORD_TRI_TARGET_DISPATCH_CLOSEOUT/tri_target_dispatch_closeout_packet.json")


@dataclass(frozen=True)
class ExpectedTarget:
    target_name: str
    payload_id: str
    payload_hash: str


EXPECTED_TARGETS: dict[str, ExpectedTarget] = {
    "announcements": ExpectedTarget(
        target_name="announcements",
        payload_id="discord_dryrun_announcement_001",
        payload_hash="b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d",
    ),
    "substack_drops": ExpectedTarget(
        target_name="substack_drops",
        payload_id="discord_dryrun_substack_drop_001",
        payload_hash="a084ced7249d9b764132e17888c15c5cfd6177329dbe5ce718311e07e849175d",
    ),
    "product_updates": ExpectedTarget(
        target_name="product_updates",
        payload_id="discord_dryrun_product_update_001",
        payload_hash="81075439dcafcdc979482d51dd56ce7cb0a704827a9fbe702a2994b3f329efdd",
    ),
}

REMAINING_WORK = [
    "promote adapter into operator runbook / UI readiness panel",
    "connect supervised payload approval queue to dispatch adapter",
    "add non-live Discord dispatch history view if useful",
]


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def is_2xx_status(code: Any) -> bool:
    return isinstance(code, int) and 200 <= code <= 299


def base_packet(closeout_status: str) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "closeout_status": closeout_status,
        "platform": PLATFORM,
        "adapter_module": ADAPTER_MODULE,
        "user_agent_required": USER_AGENT_REQUIRED,
        "no_live_request_in_this_task": True,
        "raw_secret_output": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
    }


def target_ready_packet(source: dict[str, Any], expected: ExpectedTarget) -> dict[str, Any]:
    return {
        "adapter_dispatch_verified": True,
        "result_status": source.get("result_status"),
        "http_status_code": source.get("http_status_code"),
        "status_code_class": source.get("status_code_class"),
        "diagnostic_interpretation": source.get("diagnostic_interpretation"),
        "payload_id": source.get("payload_id"),
        "payload_hash": source.get("payload_hash"),
        "request_count_attempted": source.get("request_count_attempted"),
        "retry_count_attempted": source.get("retry_count_attempted"),
        "ready_for_supervised_dispatch": True,
    }


def target_fail_packet(source: dict[str, Any], expected: ExpectedTarget) -> dict[str, Any]:
    return {
        "adapter_dispatch_verified": False,
        "result_status": source.get("result_status"),
        "http_status_code": source.get("http_status_code"),
        "status_code_class": source.get("status_code_class"),
        "diagnostic_interpretation": source.get("diagnostic_interpretation"),
        "payload_id": source.get("payload_id"),
        "payload_hash": source.get("payload_hash"),
        "request_count_attempted": source.get("request_count_attempted"),
        "retry_count_attempted": source.get("retry_count_attempted"),
        "ready_for_supervised_dispatch": False,
    }


def validate_target_packet(target_key: str, packet: dict[str, Any]) -> str | None:
    expected = EXPECTED_TARGETS[target_key]
    if packet.get("target_name") != expected.target_name:
        return f"{target_key}_target_name_mismatch"
    if packet.get("payload_id") != expected.payload_id:
        return f"{target_key}_payload_id_mismatch"
    if packet.get("payload_hash") != expected.payload_hash:
        return f"{target_key}_payload_hash_mismatch"
    if packet.get("result_status") != "PASS":
        return f"{target_key}_result_status_not_pass"
    if not is_2xx_status(packet.get("http_status_code")):
        return f"{target_key}_http_status_not_2xx"
    if packet.get("request_count_attempted") != 1:
        return f"{target_key}_request_count_mismatch"
    if packet.get("retry_count_attempted") != 0:
        return f"{target_key}_retry_count_mismatch"
    if packet.get("live_write_completed") is not True:
        return f"{target_key}_live_write_not_completed"
    return None


def build_blocked_packet(reason: str) -> dict[str, Any]:
    packet = base_packet("BLOCKED")
    packet.update({
        "blocker": reason,
        "verified_targets": {},
        "readiness_summary": {
            "all_targets_adapter_dispatch_verified": False,
            "supervised_discord_dispatch_ready": False,
            "verified_target_count": 0,
            "remaining_discord_dispatch_pilots": 3,
        },
        "remaining_work": ["rerun_closeout_with_required_redacted_input_packets"],
    })
    return packet


def build_fail_packet(reason: str, verified_targets: dict[str, Any]) -> dict[str, Any]:
    packet = base_packet("FAIL")
    packet.update({
        "failure_reason": reason,
        "verified_targets": verified_targets,
        "readiness_summary": {
            "all_targets_adapter_dispatch_verified": False,
            "supervised_discord_dispatch_ready": False,
            "verified_target_count": sum(
                1 for target in verified_targets.values() if target.get("adapter_dispatch_verified") is True
            ),
            "remaining_discord_dispatch_pilots": 3,
        },
        "remaining_work": ["repair_or_regenerate_conflicting_evidence_packet"],
    })
    return packet


def build_closeout_packet(
    announcements: dict[str, Any],
    substack_drops: dict[str, Any],
    product_updates: dict[str, Any],
) -> dict[str, Any]:
    source_packets = {
        "announcements": announcements,
        "substack_drops": substack_drops,
        "product_updates": product_updates,
    }
    verified_targets: dict[str, Any] = {}
    for target_key, source in source_packets.items():
        failure = validate_target_packet(target_key, source)
        expected = EXPECTED_TARGETS[target_key]
        if failure is not None:
            verified_targets[target_key] = target_fail_packet(source, expected)
            return build_fail_packet(failure, verified_targets)
        verified_targets[target_key] = target_ready_packet(source, expected)

    packet = base_packet("PASS")
    packet.update({
        "verified_targets": verified_targets,
        "readiness_summary": {
            "all_targets_adapter_dispatch_verified": True,
            "supervised_discord_dispatch_ready": True,
            "verified_target_count": 3,
            "remaining_discord_dispatch_pilots": 0,
        },
        "remaining_work": REMAINING_WORK,
    })
    return packet


def closeout_from_files(
    *,
    announcements_packet: str | Path,
    substack_packet: str | Path,
    product_updates_packet: str | Path,
    output: str | Path = OUTPUT_PACKET_PATH,
) -> dict[str, Any]:
    try:
        packet = build_closeout_packet(
            load_json(announcements_packet),
            load_json(substack_packet),
            load_json(product_updates_packet),
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        packet = build_blocked_packet(f"required_input_packet_missing_or_unreadable:{exc}")
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discord tri-target approved-outbox dispatch closeout")
    parser.add_argument("--announcements-packet", required=True)
    parser.add_argument("--substack-packet", required=True)
    parser.add_argument("--product-updates-packet", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = closeout_from_files(
        announcements_packet=args.announcements_packet,
        substack_packet=args.substack_packet,
        product_updates_packet=args.product_updates_packet,
        output=args.output,
    )
    print(json.dumps({
        "task_label": packet["task_label"],
        "closeout_status": packet["closeout_status"],
        "platform": packet["platform"],
        "no_live_request_in_this_task": packet["no_live_request_in_this_task"],
        "raw_secret_output": packet["raw_secret_output"],
    }, indent=2, sort_keys=True))
    return 0 if packet["closeout_status"] in {"PASS", "BLOCKED", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
