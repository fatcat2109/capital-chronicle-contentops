"""Deterministic closeout for Discord live dispatch readiness.

Reads existing redacted evidence packets only. Does not read env and does not
perform network requests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVED_OUTBOX_LIVE_DISPATCH_LEDGER_CLOSEOUT_V0"
PLATFORM = "discord"
ADAPTER_MODULE = "live_contentops.discord_dispatch_adapter"
USER_AGENT_REQUIRED = "CapitalChronicleContentOps/1.0"
ANNOUNCEMENTS_PAYLOAD_ID = "discord_dryrun_announcement_001"
ANNOUNCEMENTS_PAYLOAD_HASH = "b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d"


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def is_2xx(packet: dict[str, Any]) -> bool:
    code = packet.get("http_status_code")
    return isinstance(code, int) and 200 <= code <= 299


def smoke_target(smoke_packet: dict[str, Any], target_name: str) -> dict[str, Any] | None:
    for target in smoke_packet.get("targets", []):
        if isinstance(target, dict) and target.get("target_name") == target_name:
            return target
    return None


def build_blocked_packet(reason: str) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "closeout_status": "BLOCKED",
        "platform": PLATFORM,
        "blocker": reason,
        "verified_paths": {},
        "adapter_module": ADAPTER_MODULE,
        "user_agent_required": USER_AGENT_REQUIRED,
        "supervised_use_status": {},
        "no_live_request_in_this_task": True,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "readiness_summary": "blocked_required_input_missing_or_unreadable",
        "remaining_work": ["rerun_closeout_with_required_redacted_input_packets"],
    }


def build_fail_packet(reason: str, partial_verified_paths: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "closeout_status": "FAIL",
        "platform": PLATFORM,
        "failure_reason": reason,
        "verified_paths": partial_verified_paths or {},
        "adapter_module": ADAPTER_MODULE,
        "user_agent_required": USER_AGENT_REQUIRED,
        "supervised_use_status": {},
        "no_live_request_in_this_task": True,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "readiness_summary": "evidence_conflict_detected",
        "remaining_work": ["repair_or_regenerate_conflicting_evidence_packet"],
    }


def build_closeout_packet(approved_dispatch: dict[str, Any], multi_smoke: dict[str, Any]) -> dict[str, Any]:
    verified_paths: dict[str, Any] = {}

    if approved_dispatch.get("result_status") != "PASS":
        return build_fail_packet("announcements_adapter_dispatch_not_pass")
    if not is_2xx(approved_dispatch):
        return build_fail_packet("announcements_adapter_dispatch_not_2xx")
    if approved_dispatch.get("target_name") != "announcements":
        return build_fail_packet("announcements_target_mismatch")
    if approved_dispatch.get("payload_id") != ANNOUNCEMENTS_PAYLOAD_ID:
        return build_fail_packet("announcements_payload_id_mismatch")
    if approved_dispatch.get("payload_hash") != ANNOUNCEMENTS_PAYLOAD_HASH:
        return build_fail_packet("announcements_payload_hash_mismatch")
    if approved_dispatch.get("request_count_attempted") != 1:
        return build_fail_packet("announcements_request_count_mismatch")
    if approved_dispatch.get("retry_count_attempted") != 0:
        return build_fail_packet("announcements_retry_count_mismatch")

    verified_paths["announcements"] = {
        "smoke_verified": True,
        "adapter_dispatch_verified": True,
        "last_http_status_code": approved_dispatch["http_status_code"],
        "last_payload_id": approved_dispatch["payload_id"],
        "last_payload_hash": approved_dispatch["payload_hash"],
        "request_count": approved_dispatch["request_count_attempted"],
        "retry_count": approved_dispatch["retry_count_attempted"],
    }

    for target_name in ("substack_drops", "product_updates"):
        smoke = smoke_target(multi_smoke, target_name)
        if smoke is None:
            return build_fail_packet(f"{target_name}_smoke_missing", verified_paths)
        if not is_2xx(smoke):
            return build_fail_packet(f"{target_name}_smoke_not_2xx", verified_paths)
        verified_paths[target_name] = {
            "smoke_verified": True,
            "adapter_dispatch_verified": False,
            "last_http_status_code": smoke["http_status_code"],
        }

    return {
        "task_label": TASK_LABEL,
        "closeout_status": "PASS",
        "platform": PLATFORM,
        "verified_paths": verified_paths,
        "adapter_module": ADAPTER_MODULE,
        "user_agent_required": USER_AGENT_REQUIRED,
        "supervised_use_status": {
            "announcements": "ready_for_supervised_dispatch",
            "substack_drops": "ready_for_adapter_dispatch_pilot",
            "product_updates": "ready_for_adapter_dispatch_pilot",
        },
        "no_live_request_in_this_task": True,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "readiness_summary": (
            "announcements adapter dispatch verified by approved outbox live result; "
            "substack_drops and product_updates smoke verified and await adapter dispatch pilots"
        ),
        "remaining_work": [
            "run approved-outbox adapter dispatch pilot for substack_drops when authorized",
            "run approved-outbox adapter dispatch pilot for product_updates when authorized",
            "promote successful target evidence into supervised dispatch runbook",
        ],
    }


def closeout_from_files(
    *,
    approved_dispatch_packet: str | Path,
    multi_smoke_packet: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    try:
        approved = load_json(approved_dispatch_packet)
        smoke = load_json(multi_smoke_packet)
        packet = build_closeout_packet(approved, smoke)
    except FileNotFoundError as exc:
        packet = build_blocked_packet(f"required_input_packet_missing:{exc}")
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discord live dispatch readiness closeout")
    parser.add_argument("--approved-dispatch-packet", required=True)
    parser.add_argument("--multi-smoke-packet", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = closeout_from_files(
        approved_dispatch_packet=args.approved_dispatch_packet,
        multi_smoke_packet=args.multi_smoke_packet,
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
