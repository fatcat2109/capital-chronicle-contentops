"""V6 Discord dry-run outbox and operator approval spine.

Local deterministic dispatch-preparation lane only. It renders the exact Discord
preview text, binds a public audit hash, and emits approval/outbox/audit/manual
fallback records without provider, network, browser, or live-send behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from live_contentops.unified_capability_env_readiness_v6 import sample_packet

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_OUTBOX_AND_OPERATOR_APPROVAL_SPINE_HEAVY_BATCH_V0"
DISCORD_REQUIRED_KEY_NAME = "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
DESTINATION_BINDING = "symbolic_discord_live_announcements_destination_binding"
DETERMINISTIC_TIMESTAMP = "2026-07-01T02:25:31+07:00"
NEXT_TASK = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_FROM_APPROVED_OUTBOX_HEAVY_BATCH_V0"
FINANCIAL_ADVICE_TERMS = (
    "financial advice", "buy", "sell", "hold", "price target", "target price",
    "entry", "entries", "exit", "exits", "signal service", "trading signal",
)
SECRET_LIKE_TERMS = ("secret", "webhook", "token", "bearer", "sk-", "xoxb-", "never-serialize")


@dataclass(frozen=True)
class DiscordPayloadModel:
    title: str
    canonical_url: str | None
    summary: str
    key_points: list[str]
    call_to_action: str
    source_article_id: str
    content_hash: str
    created_at: str


@dataclass(frozen=True)
class DiscordDryRunOutboxPacket:
    schema_version: str
    task_label: str
    packet_id: str
    source_capability_env_readiness_packet_id: str | None
    source_capability_env_readiness_packet_status: str
    discord_capability_status: str
    discord_required_key_name: str
    discord_key_present: bool
    canonical_content_id: str
    approved_payload_preview_id: str
    approved_payload_hash: str
    discord_payload_model: dict[str, Any]
    discord_preview_text: str
    operator_approval_record: dict[str, Any]
    outbox_dry_run_record: dict[str, Any]
    redacted_audit_record: dict[str, Any]
    manual_fallback_record: dict[str, Any]
    live_pilot_candidate: bool
    live_send_performed: bool = False
    provider_call_made: bool = False
    network_call_made: bool = False
    browser_call_made: bool = False
    raw_secret_values_serialized: bool = False
    env_lines_serialized: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def sample_article() -> DiscordPayloadModel:
    return DiscordPayloadModel(
        title="Capital Chronicle dry-run briefing: policy watch and market context",
        canonical_url=None,
        summary="A concise operator-reviewed briefing for the community watchlist, focused on context, process, and source review rather than trade direction.",
        key_points=[
            "Macro calendar items remain the main near-term driver for risk appetite.",
            "The editorial desk is tracking policy commentary, liquidity conditions, and earnings-season breadth.",
            "Readers should use the full Chronicle note for source links, assumptions, and follow-up questions.",
        ],
        call_to_action="Review the Chronicle note, add questions for the operator, and keep discussion evidence-led.",
        source_article_id="capital_chronicle_discord_dry_run_article_001",
        content_hash="content_hash_public_fixture_001",
        created_at=DETERMINISTIC_TIMESTAMP,
    )


def _assert_safe_content(parts: list[str]) -> None:
    text = "\n".join(parts).lower()
    for term in FINANCIAL_ADVICE_TERMS:
        if term in text:
            raise ValueError(f"forbidden_financial_advice_language:{term}")
    for term in SECRET_LIKE_TERMS:
        if term in text:
            raise ValueError("forbidden_secret_like_content")


def render_discord_preview(model: DiscordPayloadModel) -> str:
    parts = [model.title, model.summary, *model.key_points, model.call_to_action]
    if model.canonical_url:
        parts.append(model.canonical_url)
    _assert_safe_content(parts)
    lines = [f"**{model.title}**", "", model.summary, "", "Key points:"]
    lines.extend(f"- {point}" for point in model.key_points)
    if model.canonical_url:
        lines.extend(["", f"Read more: {model.canonical_url}"])
    lines.extend(["", model.call_to_action])
    return "\n".join(lines)


def _sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def exact_payload_hash(preview_text: str, model: DiscordPayloadModel) -> str:
    return _sha256_json({
        "schema_version": SCHEMA_VERSION,
        "platform": "discord",
        "preview_text": preview_text,
        "source_article_id": model.source_article_id,
        "content_hash": model.content_hash,
        "created_at": model.created_at,
    })


def _capability_status(capability_packet: Mapping[str, Any]) -> tuple[str, bool, str | None, str, list[str]]:
    packet_id = capability_packet.get("packet_id")
    status = str(capability_packet.get("packet_status", "unknown"))
    for cap in capability_packet.get("capabilities", []):
        if cap.get("capability_id") == "discord_webhook":
            key_present = bool(cap.get("key_presence", {}).get(DISCORD_REQUIRED_KEY_NAME, False))
            return str(cap.get("capability_status", "unavailable")), key_present, packet_id, status, list(cap.get("blockers", []))
    env_scan = capability_packet.get("env_scan", {})
    key_present = bool(env_scan.get("key_presence", {}).get(DISCORD_REQUIRED_KEY_NAME, False))
    cap_status = "configured_for_supervised_live_scope_candidate" if key_present else "unavailable"
    blockers = [] if key_present else [f"missing_required_key_name:{DISCORD_REQUIRED_KEY_NAME}"]
    return cap_status, key_present, packet_id, status, blockers


def make_discord_dry_run_outbox_packet(article: DiscordPayloadModel | Mapping[str, Any] | None = None, capability_packet: Mapping[str, Any] | None = None) -> DiscordDryRunOutboxPacket:
    model = article if isinstance(article, DiscordPayloadModel) else DiscordPayloadModel(**(article or asdict(sample_article())))
    cap_packet = capability_packet or asdict(sample_packet())
    cap_status, key_present, source_id, source_status, cap_blockers = _capability_status(cap_packet)
    preview = render_discord_preview(model)
    payload_hash = exact_payload_hash(preview, model)
    preview_id = "discord_preview_" + payload_hash[:16]
    approval = {
        "approval_record_id": "operator_approval_" + payload_hash[:16],
        "platform": "discord",
        "preview_id": preview_id,
        "preview_hash": payload_hash,
        "operator_approval_status": "pending",
        "approved_by": None,
        "approved_at": None,
        "exact_payload_hash": payload_hash,
        "live_send_allowed": False,
    }
    outbox = {
        "outbox_id": "discord_outbox_dry_run_" + payload_hash[:16],
        "platform": "discord",
        "action_class": "dry_run_outbox",
        "destination_binding": DESTINATION_BINDING,
        "credential_key_name": DISCORD_REQUIRED_KEY_NAME,
        "credential_present": key_present,
        "exact_payload_hash": payload_hash,
        "approval_required": True,
        "approval_status": "pending",
        "ready_for_live_pilot_candidate": False,
        "live_send_performed": False,
    }
    audit = {
        "audit_id": "redacted_audit_" + payload_hash[:16],
        "platform": "discord",
        "raw_secret_values_serialized": False,
        "env_lines_serialized": False,
        "provider_call_made": False,
        "network_call_made": False,
        "live_send_performed": False,
        "exact_payload_hash_present": True,
        "dry_run_outbox_id_present": True,
        "manual_fallback_available": True,
    }
    manual = {
        "manual_fallback_id": "manual_fallback_" + payload_hash[:16],
        "platform": "discord",
        "available": True,
        "copyable_discord_message_preview": preview,
        "operator_instructions": "Jim/operator must manually paste this preview only after reviewing the exact payload hash; this packet performs no live send.",
        "exact_payload_hash": payload_hash,
        "operator_only_warning": "Manual paste must be done by Jim/operator; no automated Discord send is authorized by this packet.",
    }
    blockers: list[str] = []
    warnings = list(cap_blockers)
    records_valid = approval["live_send_allowed"] is False and outbox["exact_payload_hash"] == payload_hash and audit["manual_fallback_available"] is True and manual["available"] is True
    live_candidate = bool(key_present and records_valid and not blockers)
    outbox["ready_for_live_pilot_candidate"] = live_candidate
    if not key_present:
        warnings.append(f"discord_key_absent:{DISCORD_REQUIRED_KEY_NAME}")
    return DiscordDryRunOutboxPacket(
        SCHEMA_VERSION, TASK_LABEL, "discord_dry_run_outbox_" + payload_hash[:16], source_id, source_status,
        cap_status, DISCORD_REQUIRED_KEY_NAME, key_present, model.source_article_id, preview_id, payload_hash,
        asdict(model), preview, approval, outbox, audit, manual, live_candidate,
        False, False, False, False, False, False, blockers, warnings,
    )


def sample_discord_dry_run_outbox_packet() -> DiscordDryRunOutboxPacket:
    return make_discord_dry_run_outbox_packet(sample_article(), asdict(sample_packet()))


def packet_from_capability_packet_file(path: str | Path) -> DiscordDryRunOutboxPacket:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return make_discord_dry_run_outbox_packet(capability_packet=data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build safe Discord dry-run outbox packet without live send.")
    parser.add_argument("--capability-packet", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    packet = packet_from_capability_packet_file(args.capability_packet) if args.capability_packet else sample_discord_dry_run_outbox_packet()
    text = json.dumps(asdict(packet), indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
