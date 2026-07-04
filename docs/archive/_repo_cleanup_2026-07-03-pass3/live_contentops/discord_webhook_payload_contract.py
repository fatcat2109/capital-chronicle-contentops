"""Discord webhook payload schema and dry-run renderer contract.

Local-only. Emits credential handle IDs and destination binding IDs, never raw
webhook URLs, token material, secret lengths, hashes, prefixes, or suffixes.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from live_contentops.discord_environment_contract import OPERATOR_BINDING_ID, WEBHOOK_DESTINATIONS

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_WEBHOOK_PAYLOAD_SCHEMA_AND_DRY_RUN_RENDERER_V0"
SCHEMA_VERSION = "discord_webhook_payload_contract.v1"
OPERATOR_CREDENTIAL_HANDLE_ID = "discord_operator_private_manual_no_webhook_01"

PAYLOAD_TARGETS = {
    "announcement": "announcements",
    "substack_drop": "substack_drops",
    "product_update": "product_updates",
    "operator_private_summary": "operator_private",
    "manual_fallback_notice": "operator_private",
    "audit_summary_redacted": "operator_private",
}

DISCORD_DROP_LABELS = (
    "Title",
    "One-line thesis",
    "Why it matters",
    "Read the full article",
    "Discussion question",
    "Disclosure",
)

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("unsafe_finance_trading_language", re.compile(r"\b(buy|sell|hold|price target|position sizing|guaranteed prediction|trading signal|financial advice)\b", re.I)),
    ("webhook_url_like_value", re.compile(r"https://(?:discord(?:app)?\.com|canary\.discord\.com)/api/webhooks/", re.I)),
    ("raw_secret_like_value", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,}|[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{20,})\b")),
    ("cookie_session_local_storage_or_selfbot", re.compile(r"\b(cookie|cookies|session|sessions|localStorage|sessionStorage|selfbot|user token|discord user token)\b", re.I)),
    ("unapproved_live_write_or_dispatch_claim", re.compile(r"\b(live write enabled|webhook sent|sent to discord|posted to discord|dispatch happened|published to discord|live dispatch)\b", re.I)),
    ("hidden_scheduler_or_autonomous_posting", re.compile(r"\b(hidden scheduler|autonomous posting|auto[- ]?post(?:ing)?|unattended publish(?:ing)?)\b", re.I)),
    ("dm_reply_engagement_automation", re.compile(r"\b(auto[- ]?reply|automated reply|dm automation|auto dm|mass dm|engagement automation)\b", re.I)),
)


@dataclass(frozen=True)
class DiscordPayload:
    payload_id: str
    payload_type: str
    target_name: str
    destination_binding_id: str
    credential_handle_id: str
    title: str
    body: str
    disclosure: str
    discussion_question: str | None = None
    source_url: str | None = None
    content_refs: tuple[str, ...] = ()
    dry_run_only: bool = True
    live_write_allowed_now: bool = False
    validation_status: str = "valid"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def target_binding_catalog() -> dict[str, dict[str, str]]:
    catalog = {
        item.target_name: {
            "destination_binding_id": item.destination_binding_id,
            "credential_handle_id": item.credential_handle_id,
        }
        for item in WEBHOOK_DESTINATIONS
    }
    catalog["operator_private"] = {
        "destination_binding_id": OPERATOR_BINDING_ID,
        "credential_handle_id": OPERATOR_CREDENTIAL_HANDLE_ID,
    }
    return catalog


def _text_fields(data: dict) -> str:
    chunks: list[str] = []
    for key in ("payload_id", "payload_type", "target_name", "title", "body", "disclosure", "discussion_question", "source_url"):
        value = data.get(key)
        if value:
            chunks.append(str(value))
    chunks.extend(str(item) for item in data.get("content_refs") or ())
    return "\n".join(chunks)


def safety_blockers(data: dict) -> tuple[str, ...]:
    text = _text_fields(data)
    blockers: list[str] = []
    for blocker, pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            blockers.append(blocker)
    return tuple(dict.fromkeys(blockers))


def validate_payload_data(data: dict) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    blockers: list[str] = []
    warnings: list[str] = []
    payload_type = data.get("payload_type")
    if payload_type not in PAYLOAD_TARGETS:
        blockers.append("unsupported_payload_type")
    for key in ("payload_id", "payload_type", "title", "body", "disclosure"):
        if not data.get(key):
            blockers.append(f"missing_required_field:{key}")
    if payload_type == "substack_drop" and not data.get("discussion_question"):
        blockers.append("substack_drop_requires_discussion_question")
    if data.get("dry_run_only") is False:
        blockers.append("dry_run_only_must_remain_true")
    if data.get("live_write_allowed_now") is True:
        blockers.append("live_write_allowed_now_must_remain_false")
    blockers.extend(safety_blockers(data))
    if not data.get("source_url"):
        warnings.append("source_url_absent")
    return ("blocked" if blockers else "valid", tuple(dict.fromkeys(blockers)), tuple(warnings))


def build_payload(
    *,
    payload_id: str,
    payload_type: str,
    title: str,
    body: str,
    disclosure: str,
    discussion_question: str | None = None,
    source_url: str | None = None,
    content_refs: Iterable[str] | None = None,
) -> DiscordPayload:
    catalog = target_binding_catalog()
    target_name = PAYLOAD_TARGETS.get(payload_type, "unsupported")
    binding = catalog.get(target_name, {"destination_binding_id": "unsupported", "credential_handle_id": "unsupported"})
    base = {
        "payload_id": payload_id,
        "payload_type": payload_type,
        "target_name": target_name,
        "destination_binding_id": binding["destination_binding_id"],
        "credential_handle_id": binding["credential_handle_id"],
        "title": title,
        "body": body,
        "disclosure": disclosure,
        "discussion_question": discussion_question,
        "source_url": source_url,
        "content_refs": tuple(content_refs or ()),
        "dry_run_only": True,
        "live_write_allowed_now": False,
    }
    validation_status, blockers, warnings = validate_payload_data(base)
    return DiscordPayload(validation_status=validation_status, blockers=blockers, warnings=warnings, **base)


def _render_human_preview(payload: DiscordPayload) -> str:
    lines = [
        "[DISCORD DRY RUN ONLY]",
        f"Payload ID: {payload.payload_id}",
        f"Payload type: {payload.payload_type}",
        f"Target: {payload.target_name}",
        f"Destination binding ID: {payload.destination_binding_id}",
        f"Credential handle ID: {payload.credential_handle_id}",
        f"Title: {payload.title}",
        f"One-line thesis: {payload.body.splitlines()[0] if payload.body else ''}",
        f"Why it matters: {payload.body}",
        f"Read the full article: {payload.source_url or 'not_provided'}",
        f"Discussion question: {payload.discussion_question or 'not_required'}",
        f"Disclosure: {payload.disclosure}",
        f"Validation status: {payload.validation_status}",
    ]
    if payload.blockers:
        lines.append("Blockers: " + ", ".join(payload.blockers))
    if payload.warnings:
        lines.append("Warnings: " + ", ".join(payload.warnings))
    return "\n".join(lines)


def render_dry_run(payload: DiscordPayload) -> dict:
    payload_dict = asdict(payload)
    redacted_webhook_json_preview = {
        "username": "Capital Chronicle ContentOps",
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": payload.title,
                "description": payload.body,
                "fields": [
                    {"name": "Read the full article", "value": payload.source_url or "not_provided", "inline": False},
                    {"name": "Discussion question", "value": payload.discussion_question or "not_required", "inline": False},
                    {"name": "Disclosure", "value": payload.disclosure, "inline": False},
                ],
                "footer": {"text": "Dry-run preview only. Not sent."},
            }
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        **payload_dict,
        "human_readable_preview": _render_human_preview(payload),
        "redacted_webhook_json_preview": redacted_webhook_json_preview,
        "secret_output_policy": {
            "webhook_url_output": False,
            "token_output": False,
            "token_metadata_output": False,
            "browser_or_session_storage_output": False,
        },
    }


def sample_payloads() -> list[DiscordPayload]:
    disclosure = "Educational content only. Not investment, legal, tax, or personal finance guidance."
    return [
        build_payload(payload_id="discord_dryrun_announcement_001", payload_type="announcement", title="Capital Chronicle briefing room open", body="New editorial workflow is ready for operator review.", disclosure=disclosure, source_url="https://capitalchronicle.example/briefing"),
        build_payload(payload_id="discord_dryrun_substack_drop_001", payload_type="substack_drop", title="Macro note published", body="A new research note explains liquidity conditions and market structure context.", disclosure=disclosure, discussion_question="Which data point should we expand in the next issue?", source_url="https://capitalchronicle.example/research-note"),
        build_payload(payload_id="discord_dryrun_product_update_001", payload_type="product_update", title="ContentOps V6 dry-run renderer ready", body="Discord payload previews now validate safety rules before any live send gate exists.", disclosure=disclosure),
        build_payload(payload_id="discord_dryrun_operator_summary_001", payload_type="operator_private_summary", title="Operator summary", body="Dry-run packet generated locally with live writes disabled.", disclosure=disclosure),
        build_payload(payload_id="discord_dryrun_manual_fallback_001", payload_type="manual_fallback_notice", title="Manual fallback notice", body="Manual review remains available when automation is blocked by policy.", disclosure=disclosure),
        build_payload(payload_id="discord_dryrun_audit_summary_001", payload_type="audit_summary_redacted", title="Redacted audit summary", body="Audit surface lists key names and binding IDs only.", disclosure=disclosure),
    ]


def write_sample_payloads(output_path: str | Path) -> dict:
    packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "dry_run_only": True,
        "live_write_allowed_now": False,
        "discord_bot_required": False,
        "drop_format_labels": list(DISCORD_DROP_LABELS),
        "target_mappings": PAYLOAD_TARGETS,
        "payloads": [render_dry_run(payload) for payload in sample_payloads()],
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Discord webhook dry-run sample payloads")
    parser.add_argument("--sample-output", required=True, help="Path for redacted dry-run sample payload packet")
    args = parser.parse_args(argv)
    packet = write_sample_payloads(args.sample_output)
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result": "PASS",
        "sample_output": args.sample_output,
        "payload_count": len(packet["payloads"]),
        "dry_run_only": True,
        "live_write_allowed_now": False,
        "webhook_url_output": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
