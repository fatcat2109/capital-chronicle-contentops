"""V6 variant preview/hash approval bridge to Discord dry-run outbox.

Local deterministic dry-run only. Consumes the AI research canonical article
packet, renders platform-native variants, computes exact preview hashes, creates
pending approval records, and hands the Discord seed to the existing Discord
outbox spine without provider calls, network calls, live sends, or secret access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from live_contentops.ai_research_canonical_article_engine_v6 import sample_article_packet
from live_contentops.discord_dry_run_outbox_operator_approval_spine_v6 import make_discord_dry_run_outbox_packet

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_VARIANT_PREVIEW_HASH_APPROVAL_TO_DISCORD_OUTBOX_HEAVY_BATCH_V0"
DETERMINISTIC_TIMESTAMP = "2026-07-01T03:09:15+07:00"
RECOMMENDED_NEXT_TASK = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_QUEUE_AND_EVIDENCE_VAULT_UI_HEAVY_BATCH_V0"

FORBIDDEN_FINANCIAL_TERMS = (
    "financial advice", "buy", "sell", "hold", "price target", "target price",
    "entry", "entries", "exit", "exits", "signal service", "signal-service",
    "trading signal",
)
SECRET_LIKE_TERMS = ("secret", "webhook", "token", "bearer", "sk-", "xoxb-", "never-serialize")


@dataclass(frozen=True)
class VariantRecord:
    variant_id: str
    platform: str
    variant_role: str
    source_article_id: str
    content_hash: str
    title: str
    body: str
    constraints: dict[str, Any]
    created_at: str = DETERMINISTIC_TIMESTAMP


@dataclass(frozen=True)
class PreviewHashRecord:
    preview_id: str
    variant_id: str
    platform: str
    preview_text: str
    exact_preview_hash: str
    hash_algorithm: str = "sha256_json_v6"
    executable_request_artifact_created: bool = False


@dataclass(frozen=True)
class ApprovalRecord:
    approval_record_id: str
    platform: str
    variant_id: str
    preview_id: str
    exact_preview_hash: str
    approval_status: str = "pending_operator_review"
    approved_by: None = None
    approved_at: None = None
    live_dispatch_allowed: bool = False


@dataclass(frozen=True)
class VariantApprovalBridgePacket:
    schema_version: str
    task_label: str
    packet_id: str
    source_article_packet_id: str
    source_article_hash: str
    variants: list[dict[str, Any]]
    preview_hash_records: list[dict[str, Any]]
    approval_records: list[dict[str, Any]]
    discord_summary_seed: dict[str, Any]
    discord_dry_run_outbox_packet: dict[str, Any]
    discord_outbox_compatibility: dict[str, Any]
    redacted_audit_packet: dict[str, Any]
    provider_call_made: bool = False
    network_call_made: bool = False
    browser_call_made: bool = False
    live_send_performed: bool = False
    raw_secret_values_serialized: bool = False
    env_lines_serialized: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_next_task: str = RECOMMENDED_NEXT_TASK


def _sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_safe_text(text: str) -> None:
    low = text.lower()
    words = set(low.replace("/", " ").replace("-", " ").split())
    for term in FORBIDDEN_FINANCIAL_TERMS:
        if " " in term or "-" in term:
            if term in low:
                raise ValueError(f"forbidden_financial_advice_language:{term}")
        elif term in words:
            raise ValueError(f"forbidden_financial_advice_language:{term}")
    for term in SECRET_LIKE_TERMS:
        if term in low:
            raise ValueError("forbidden_secret_like_content")


def _scan_obj(obj: Any) -> None:
    if isinstance(obj, str):
        _assert_safe_text(obj)
    elif isinstance(obj, Mapping):
        allowed_symbolic_keys = {
            "task_label", "schema_version", "recommended_next_task", "platform", "hash_algorithm",
            "discord_required_key_name", "credential_key_name", "destination_binding",
            "source_capability_env_readiness_packet_id", "packet_id", "outbox_id",
            "audit_id", "manual_fallback_id", "approval_record_id", "preview_id",
        }
        for key, value in obj.items():
            if key in allowed_symbolic_keys:
                continue
            _scan_obj(value)
    elif isinstance(obj, list):
        for item in obj:
            _scan_obj(item)


def _article_hash(article_packet: Mapping[str, Any]) -> str:
    draft = article_packet.get("canonical_article_draft", {})
    value = draft.get("canonical_payload_hash") or article_packet.get("operator_idea_id")
    if not value:
        value = _sha256_json(article_packet)
    return str(value)


def _source_article_id(article_packet: Mapping[str, Any], article_hash: str) -> str:
    seed = article_packet.get("discord_summary_seed", {})
    return str(seed.get("source_article_id") or article_packet.get("operator_idea_id") or ("operator_idea_" + article_hash[:16]))


def make_platform_variants(article_packet: Mapping[str, Any]) -> list[VariantRecord]:
    draft = article_packet.get("canonical_article_draft", {})
    seed = article_packet.get("discord_summary_seed", {})
    article_hash = _article_hash(article_packet)
    source_id = _source_article_id(article_packet, article_hash)
    title = str(draft.get("title") or seed.get("title") or "Capital Chronicle Educational Briefing")
    summary = str(seed.get("summary") or draft.get("dek") or "Process-led educational briefing for operator review.")
    key_points = [str(point) for point in seed.get("key_points", [])][:3]
    if not key_points:
        key_points = ["Review source context and methodology before publication."]

    discord_body = "\n".join([summary, "", "Key points:", *(f"- {point}" for point in key_points), "", str(seed.get("call_to_action") or "Review the Chronicle note and keep discussion evidence-led.")])
    telegram_body = " | ".join(["Operator checkpoint", summary, "Review required before any public distribution."])
    substack_body = "\n\n".join([str(draft.get("subtitle") or "Educational briefing"), str(draft.get("intro") or summary), str(draft.get("conclusion") or "Operator review required.")])

    variants = [
        VariantRecord("variant_discord_" + article_hash[:16], "discord", "community_summary_seed", source_id, article_hash, title, discord_body, {"max_key_points": 3, "requires_operator_approval": True}),
        VariantRecord("variant_telegram_" + article_hash[:16], "telegram_operator", "operator_checkpoint", source_id, article_hash, title, telegram_body, {"single_message_checkpoint": True, "requires_operator_approval": True}),
        VariantRecord("variant_substack_" + article_hash[:16], "substack", "canonical_article_preview", source_id, article_hash, title, substack_body, {"manual_export_only": True, "requires_editorial_review": True}),
    ]
    for variant in variants:
        _assert_safe_text(variant.title + "\n" + variant.body)
    return variants


def render_variant_preview(variant: VariantRecord) -> str:
    preview = f"[{variant.platform}] {variant.title}\n\n{variant.body}\n\nSource: {variant.source_article_id}"
    _assert_safe_text(preview)
    return preview


def make_preview_hash_record(variant: VariantRecord) -> PreviewHashRecord:
    preview = render_variant_preview(variant)
    exact_hash = _sha256_json({
        "schema_version": SCHEMA_VERSION,
        "variant_id": variant.variant_id,
        "platform": variant.platform,
        "preview_text": preview,
        "content_hash": variant.content_hash,
    })
    return PreviewHashRecord("preview_" + variant.platform + "_" + exact_hash[:16], variant.variant_id, variant.platform, preview, exact_hash)


def make_approval_record(preview: PreviewHashRecord) -> ApprovalRecord:
    return ApprovalRecord("approval_" + preview.platform + "_" + preview.exact_preview_hash[:16], preview.platform, preview.variant_id, preview.preview_id, preview.exact_preview_hash)


def _discord_seed(article_packet: Mapping[str, Any]) -> dict[str, Any]:
    seed = dict(article_packet.get("discord_summary_seed", {}))
    required = {"title", "canonical_url", "summary", "key_points", "call_to_action", "source_article_id", "content_hash", "created_at"}
    missing = sorted(required - set(seed))
    if missing:
        raise ValueError("discord_summary_seed_missing_fields:" + ",".join(missing))
    _scan_obj(seed)
    return seed


def run_variant_approval_bridge(article_packet: Mapping[str, Any] | None = None) -> VariantApprovalBridgePacket:
    packet = article_packet or sample_article_packet()
    _scan_obj(packet)
    article_hash = _article_hash(packet)
    variants = make_platform_variants(packet)
    previews = [make_preview_hash_record(variant) for variant in variants]
    approvals = [make_approval_record(preview) for preview in previews]
    discord_seed = _discord_seed(packet)
    discord_outbox = make_discord_dry_run_outbox_packet(article=discord_seed)

    discord_preview = next(record for record in previews if record.platform == "discord")
    discord_approval = next(record for record in approvals if record.platform == "discord")
    compatibility = {
        "discord_seed_accepted_by_outbox_spine": True,
        "discord_outbox_packet_id": discord_outbox.packet_id,
        "discord_outbox_approval_status": discord_outbox.operator_approval_record["operator_approval_status"],
        "discord_variant_preview_id": discord_preview.preview_id,
        "discord_variant_approval_record_id": discord_approval.approval_record_id,
        "discord_dry_run_only": True,
        "live_send_performed": False,
    }
    audit = {
        "audit_id": "variant_bridge_audit_" + article_hash[:16],
        "source_article_packet_id": str(packet.get("packet_id", "unknown")),
        "variant_count": len(variants),
        "approval_count": len(approvals),
        "provider_call_made": False,
        "network_call_made": False,
        "browser_call_made": False,
        "live_send_performed": False,
        "raw_secret_values_serialized": False,
        "env_lines_serialized": False,
        "executable_request_artifacts_created": False,
    }
    result = VariantApprovalBridgePacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        packet_id="variant_approval_bridge_" + article_hash[:16],
        source_article_packet_id=str(packet.get("packet_id", "unknown")),
        source_article_hash=article_hash,
        variants=[asdict(v) for v in variants],
        preview_hash_records=[asdict(p) for p in previews],
        approval_records=[asdict(a) for a in approvals],
        discord_summary_seed=discord_seed,
        discord_dry_run_outbox_packet=asdict(discord_outbox),
        discord_outbox_compatibility=compatibility,
        redacted_audit_packet=audit,
    )
    _scan_obj(asdict(result))
    return result


def sample_variant_approval_bridge_packet() -> VariantApprovalBridgePacket:
    return run_variant_approval_bridge(sample_article_packet())


def packet_from_article_packet_file(path: str | Path) -> VariantApprovalBridgePacket:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return run_variant_approval_bridge(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V6 variant preview/hash approval bridge packet without live sends.")
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    packet = packet_from_article_packet_file(args.input) if args.input else sample_variant_approval_bridge_packet()
    text = json.dumps(asdict(packet), indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
