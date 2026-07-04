"""V6 Discord supervised live pilot from approved outbox.

Performs exactly one Discord webhook POST only after explicit operator approval,
exact payload hash revalidation, env key presence, inactive kill switch, and a
single-request budget all pass. All persisted outputs are redacted.
"""
from __future__ import annotations

import argparse
import json
import os
import importlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from live_contentops.discord_dry_run_outbox_operator_approval_spine_v6 import (
    DISCORD_REQUIRED_KEY_NAME,
    exact_payload_hash,
)

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_FROM_APPROVED_OUTBOX_HEAVY_BATCH_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_OUTBOX_AND_OPERATOR_APPROVAL_SPINE_HEAVY_BATCH_V0"
DEFAULT_TIMEOUT_SECONDS = 8
SAFE_CONTENT_TYPE = "application/json"
Sender = Callable[[str, str, int], Mapping[str, Any]]


@dataclass(frozen=True)
class DiscordSupervisedLivePilotResult:
    schema_version: str
    task_label: str
    source_outbox_packet_id: str
    exact_payload_hash: str
    approval_status: str
    approved_by_present: bool
    approved_at_present: bool
    env_key_name: str
    env_key_present: bool
    kill_switch_active: bool
    request_budget: int
    request_count: int
    live_send_attempted: bool
    live_send_succeeded: bool
    result_class: str
    redacted_status_class: str | None
    public_url_created: bool
    provider_call_made: bool
    network_call_made: bool
    raw_secret_values_serialized: bool
    env_lines_serialized: bool
    webhook_url_serialized: bool
    response_body_serialized: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_fallback_available: bool = True


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("json_payload_must_be_object")
    return data


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "active"}
    return bool(value)


def env_key_present(env: Mapping[str, str] | None = None) -> bool:
    env_map = getattr(os, "environ") if env is None else env
    return DISCORD_REQUIRED_KEY_NAME in env_map and bool(env_map.get(DISCORD_REQUIRED_KEY_NAME))


def _status_class(status_code: Any) -> str | None:
    if not isinstance(status_code, int):
        return None
    if 200 <= status_code <= 299:
        return "2xx"
    if 300 <= status_code <= 399:
        return "3xx"
    if 400 <= status_code <= 499:
        return "4xx"
    if 500 <= status_code <= 599:
        return "5xx"
    return "other"


def recompute_hash(outbox_packet: Mapping[str, Any]) -> str:
    model = outbox_packet.get("discord_payload_model")
    preview = outbox_packet.get("discord_preview_text")
    if not isinstance(model, dict) or not isinstance(preview, str):
        raise ValueError("missing_preview_or_payload_model")
    from live_contentops.discord_dry_run_outbox_operator_approval_spine_v6 import DiscordPayloadModel

    return exact_payload_hash(preview, DiscordPayloadModel(**model))


def _approval_hashes(outbox_packet: Mapping[str, Any], declaration: Mapping[str, Any] | None) -> set[str]:
    hashes: set[str] = set()
    for container in (outbox_packet.get("operator_approval_record", {}), outbox_packet.get("outbox_dry_run_record", {}), declaration or {}):
        if isinstance(container, Mapping):
            for key in ("exact_payload_hash", "preview_hash", "approved_payload_hash"):
                value = container.get(key)
                if isinstance(value, str) and value:
                    hashes.add(value)
    value = outbox_packet.get("approved_payload_hash")
    if isinstance(value, str) and value:
        hashes.add(value)
    return hashes


def validate_live_gates(
    outbox_packet: Mapping[str, Any],
    approval_declaration: Mapping[str, Any] | None,
    *,
    env: Mapping[str, str] | None = None,
    kill_switch_active: bool = False,
    request_budget: int = 1,
) -> tuple[list[str], str, bool, bool, bool, str]:
    blockers: list[str] = []
    if outbox_packet.get("task_label") != UPSTREAM_TASK_LABEL:
        blockers.append("invalid_source_outbox_task_label")
    try:
        recomputed_hash = recompute_hash(outbox_packet)
    except Exception:
        recomputed_hash = ""
        blockers.append("exact_payload_hash_recompute_failed")
    declaration = approval_declaration or {}
    approval_status = str(declaration.get("operator_approval_status") or declaration.get("approval_status") or "missing")
    approved_by_present = bool(declaration.get("approved_by"))
    approved_at_present = bool(declaration.get("approved_at"))
    present = env_key_present(env)
    if approval_declaration is None:
        blockers.append("operator_approval_declaration_missing")
    if approval_status != "approved":
        blockers.append("operator_approval_status_not_approved")
    if not approved_by_present:
        blockers.append("approved_by_missing")
    if not approved_at_present:
        blockers.append("approved_at_missing")
    if not recomputed_hash or declaration.get("exact_payload_hash") != recomputed_hash:
        blockers.append("operator_approval_exact_payload_hash_mismatch")
    hashes = _approval_hashes(outbox_packet, declaration)
    if recomputed_hash and any(h != recomputed_hash for h in hashes):
        blockers.append("outbox_or_approval_hash_link_mismatch")
    if not present:
        blockers.append(f"env_key_missing:{DISCORD_REQUIRED_KEY_NAME}")
    if kill_switch_active:
        blockers.append("kill_switch_active")
    if request_budget != 1:
        blockers.append("request_budget_not_one")
    if outbox_packet.get("manual_fallback_record", {}).get("available") is not True:
        blockers.append("manual_fallback_unavailable")
    return blockers, recomputed_hash, approved_by_present, approved_at_present, present, approval_status


def discord_webhook_sender(webhook_url: str, content: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Mapping[str, Any]:
    body = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
    url_request = importlib.import_module("urllib.request")
    url_error = importlib.import_module("urllib.error")
    request = url_request.Request(webhook_url, data=body, headers={"Content-Type": SAFE_CONTENT_TYPE}, method="POST")
    try:
        with url_request.urlopen(request, timeout=timeout_seconds) as response:
            return {"status_code": int(getattr(response, "status", 0) or response.getcode())}
    except url_error.HTTPError as exc:
        return {"status_code": int(exc.code)}


def make_supervised_live_pilot_result(
    outbox_packet: Mapping[str, Any],
    approval_declaration: Mapping[str, Any] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    kill_switch_active: bool = False,
    request_budget: int = 1,
    sender: Sender | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> DiscordSupervisedLivePilotResult:
    blockers, payload_hash, approved_by_present, approved_at_present, present, approval_status = validate_live_gates(
        outbox_packet, approval_declaration, env=env, kill_switch_active=kill_switch_active, request_budget=request_budget
    )
    source_id = str(outbox_packet.get("packet_id", ""))
    manual_available = bool(outbox_packet.get("manual_fallback_record", {}).get("available", True))
    if blockers:
        return DiscordSupervisedLivePilotResult(
            SCHEMA_VERSION, TASK_LABEL, source_id, payload_hash, approval_status, approved_by_present,
            approved_at_present, DISCORD_REQUIRED_KEY_NAME, present, kill_switch_active, request_budget, 0,
            False, False, "blocked", None, False, False, False, False, False, False, False,
            blockers, [], manual_available,
        )
    env_map = getattr(os, "environ") if env is None else env
    webhook_value = env_map[DISCORD_REQUIRED_KEY_NAME]
    send = sender or discord_webhook_sender
    response = send(webhook_value, str(outbox_packet["discord_preview_text"]), timeout_seconds)
    status_class = _status_class(response.get("status_code"))
    succeeded = status_class == "2xx"
    return DiscordSupervisedLivePilotResult(
        SCHEMA_VERSION, TASK_LABEL, source_id, payload_hash, approval_status, approved_by_present,
        approved_at_present, DISCORD_REQUIRED_KEY_NAME, True, False, 1, 1,
        True, succeeded, "success" if succeeded else "failed_redacted", status_class, False,
        True, True, False, False, False, False, [], [], manual_available,
    )


def blocked_sample_result() -> DiscordSupervisedLivePilotResult:
    path = Path("docs/automation/V6_DISCORD_DRY_RUN_OUTBOX_OPERATOR_APPROVAL_SPINE/sample_discord_dry_run_outbox_packet.json")
    return make_supervised_live_pilot_result(load_json(path), None, env={}, kill_switch_active=False, request_budget=1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V6 Discord supervised live pilot if exact approval gates pass.")
    parser.add_argument("--outbox-packet", required=True)
    parser.add_argument("--approval-declaration", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--kill-switch-active", action="store_true")
    parser.add_argument("--request-budget", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    outbox = load_json(args.outbox_packet)
    approval = load_json(args.approval_declaration) if args.approval_declaration else None
    result = make_supervised_live_pilot_result(
        outbox,
        approval,
        kill_switch_active=args.kill_switch_active,
        request_budget=args.request_budget,
        timeout_seconds=args.timeout_seconds,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if result.result_class == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
