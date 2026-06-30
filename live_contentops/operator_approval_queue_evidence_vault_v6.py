"""V6 operator approval queue + evidence vault view model.

Reads committed local sample packets only and emits a deterministic UI/evidence
view model. No provider calls, network calls, browser sessions, env reads, or
live sends are performed.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_QUEUE_AND_EVIDENCE_VAULT_UI_HEAVY_BATCH_V0"
RECOMMENDED_NEXT_TASK = "TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_AND_ARTICLE_STUDIO_HEAVY_BATCH_V0"
ARTICLE_SAMPLE = Path("docs/automation/V6_AI_RESEARCH_CANONICAL_ARTICLE_ENGINE/sample_ai_research_canonical_article_packet.json")
VARIANT_SAMPLE = Path("docs/automation/V6_VARIANT_PREVIEW_HASH_APPROVAL_TO_DISCORD_OUTBOX/sample_variant_preview_hash_approval_packet.json")
LIVE_PILOT_BLOCKED_SAMPLE = Path("docs/automation/V6_DISCORD_SUPERVISED_LIVE_PILOT_FROM_APPROVED_OUTBOX/sample_discord_supervised_live_pilot_result_blocked.json")
SECRET_TERMS = ("webhook", "bearer", "sk-", "xoxb-", "never-serialize", "provider key", "env line")


@dataclass(frozen=True)
class ApprovalQueueItem:
    queue_item_id: str
    platform: str
    variant_id: str
    preview_id: str
    preview_hash: str
    approval_status: str
    approved_by: Any
    approved_at: Any
    live_dispatch_allowed: bool
    exact_preview_text_excerpt: str
    source_canonical_hash: str
    required_operator_action: str


@dataclass(frozen=True)
class EvidenceVaultItem:
    evidence_id: str
    evidence_type: str
    source_file_path: str
    source_packet_id: str
    source_hash_or_preview_hash: str
    safety_flags: dict[str, Any]
    display_status: str
    caveats: list[str]


@dataclass(frozen=True)
class OperatorApprovalQueueEvidenceVaultPacket:
    schema_version: str
    task_label: str
    packet_id: str
    source_article_packet_id: str
    source_article_packet_hash: str
    approval_queue_items: list[dict[str, Any]]
    evidence_vault_items: list[dict[str, Any]]
    article_preview_summary: dict[str, Any]
    variant_preview_cards: list[dict[str, Any]]
    discord_outbox_card: dict[str, Any]
    live_pilot_status_card: dict[str, Any]
    redacted_audit_summary: dict[str, Any]
    blockers: list[str]
    warnings: list[str]
    provider_call_made: bool = False
    network_call_made: bool = False
    live_send_performed: bool = False
    browser_session_used: bool = False
    raw_secret_values_serialized: bool = False
    env_lines_serialized: bool = False
    recommended_next_task: str = RECOMMENDED_NEXT_TASK


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("json_payload_must_be_object")
    return data


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"missing_required_field:{context}.{key}")
    return mapping[key]


def _excerpt(text: str, limit: int = 220) -> str:
    clean = " ".join(str(text).split())
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def _safe_flags(*packets: Mapping[str, Any]) -> dict[str, bool]:
    keys = ["provider_call_made", "network_call_made", "live_send_performed", "browser_session_used", "browser_call_made", "raw_secret_values_serialized", "raw_provider_key_serialized", "env_lines_serialized", "webhook_url_serialized", "response_body_serialized"]
    return {key: any(bool(packet.get(key, False)) for packet in packets) for key in keys}


def _scan_no_secret_values(obj: Any) -> None:
    if isinstance(obj, str):
        low = obj.lower()
        for term in SECRET_TERMS:
            if term in low:
                raise ValueError("forbidden_secret_like_value")
    elif isinstance(obj, Mapping):
        allowed_symbolic_keys = {
            "env_key_name", "discord_required_key_name", "credential_key_name",
            "source_file_path", "evidence_type", "source_packet_id", "evidence_id",
            "blockers", "caveats", "task_label", "recommended_next_task",
        }
        for key, value in obj.items():
            if key in allowed_symbolic_keys:
                continue
            _scan_no_secret_values(value)
    elif isinstance(obj, list):
        for item in obj:
            _scan_no_secret_values(item)


def build_approval_queue_items(variant_packet: Mapping[str, Any]) -> list[ApprovalQueueItem]:
    approvals = _require(variant_packet, "approval_records", "variant_packet")
    previews = {p["preview_id"]: p for p in _require(variant_packet, "preview_hash_records", "variant_packet")}
    source_hash = str(_require(variant_packet, "source_article_hash", "variant_packet"))
    items: list[ApprovalQueueItem] = []
    for approval in approvals:
        preview_id = str(_require(approval, "preview_id", "approval_record"))
        preview = previews.get(preview_id)
        if not preview:
            raise ValueError(f"missing_preview_for_approval:{preview_id}")
        platform = str(_require(approval, "platform", "approval_record"))
        items.append(ApprovalQueueItem(
            queue_item_id="queue_" + str(_require(approval, "approval_record_id", "approval_record")),
            platform=platform,
            variant_id=str(_require(approval, "variant_id", "approval_record")),
            preview_id=preview_id,
            preview_hash=str(_require(approval, "exact_preview_hash", "approval_record")),
            approval_status=str(_require(approval, "approval_status", "approval_record")),
            approved_by=approval.get("approved_by"),
            approved_at=approval.get("approved_at"),
            live_dispatch_allowed=bool(_require(approval, "live_dispatch_allowed", "approval_record")),
            exact_preview_text_excerpt=_excerpt(str(preview.get("preview_text", ""))),
            source_canonical_hash=source_hash,
            required_operator_action="Review exact preview hash and content in future approval queue; no live dispatch is enabled.",
        ))
    return items


def build_packet(article_packet: Mapping[str, Any], variant_packet: Mapping[str, Any], live_pilot_result: Mapping[str, Any], *, article_source_path: str = str(ARTICLE_SAMPLE), variant_source_path: str = str(VARIANT_SAMPLE), live_pilot_source_path: str = str(LIVE_PILOT_BLOCKED_SAMPLE)) -> OperatorApprovalQueueEvidenceVaultPacket:
    article_id = str(_require(article_packet, "packet_id", "article_packet"))
    draft = _require(article_packet, "canonical_article_draft", "article_packet")
    article_hash = str(_require(draft, "canonical_payload_hash", "canonical_article_draft"))
    variant_id = str(_require(variant_packet, "packet_id", "variant_packet"))
    outbox = _require(variant_packet, "discord_dry_run_outbox_packet", "variant_packet")
    outbox_id = str(_require(outbox, "packet_id", "discord_outbox_packet"))
    outbox_hash = str(_require(outbox, "approved_payload_hash", "discord_outbox_packet"))
    live_status = str(_require(live_pilot_result, "result_class", "live_pilot_result"))
    queue_items = build_approval_queue_items(variant_packet)
    if any(item.approval_status != "pending_operator_review" or item.live_dispatch_allowed for item in queue_items):
        raise ValueError("approval_queue_not_pending_or_live_dispatch_enabled")
    previews = _require(variant_packet, "preview_hash_records", "variant_packet")
    variants = {v["variant_id"]: v for v in _require(variant_packet, "variants", "variant_packet")}
    variant_cards = []
    for preview in previews:
        variant = variants.get(preview["variant_id"], {})
        variant_cards.append({"platform": preview["platform"], "variant_id": preview["variant_id"], "preview_id": preview["preview_id"], "preview_hash": preview["exact_preview_hash"], "title": variant.get("title", ""), "preview_excerpt": _excerpt(preview.get("preview_text", "")), "display_status": "amber_review_pending"})
    sample_key_presence = {"discord_key_present_committed_value": bool(outbox.get("discord_key_present", False)), "credential_present_committed_value": bool(outbox.get("outbox_dry_run_record", {}).get("credential_present", False)), "evidence_scope": "sample_fixture_only", "runtime_proof": False}
    evidence_items = [
        EvidenceVaultItem("evidence_article_" + article_hash[:16], "canonical_article_packet", article_source_path, article_id, article_hash, _safe_flags(article_packet), "green_verified", ["Committed sample packet only."]),
        EvidenceVaultItem("evidence_variant_" + article_hash[:16], "variant_preview_hash_approval_packet", variant_source_path, variant_id, article_hash, _safe_flags(variant_packet), "green_verified", ["Approval records remain pending."]),
        EvidenceVaultItem("evidence_discord_outbox_" + outbox_hash[:16], "discord_dry_run_outbox", variant_source_path, outbox_id, outbox_hash, _safe_flags(outbox), "amber_review", ["Dry-run outbox only; sample credential evidence is sample_fixture_only, not runtime proof."]),
        EvidenceVaultItem("evidence_live_pilot_" + outbox_hash[:16], "discord_live_pilot_blocked_result", live_pilot_source_path, str(live_pilot_result.get("source_outbox_packet_id", "unknown")), str(live_pilot_result.get("exact_payload_hash", "")), _safe_flags(live_pilot_result), "red_blocked", list(live_pilot_result.get("blockers", []))),
    ]
    blockers = ["live_dispatch_controls_disabled", "operator_approval_write_behavior_not_scoped"]
    if live_status == "blocked":
        blockers.extend(str(b) for b in live_pilot_result.get("blockers", []))
    packet = OperatorApprovalQueueEvidenceVaultPacket(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL, packet_id="operator_approval_queue_evidence_vault_" + article_hash[:16], source_article_packet_id=article_id, source_article_packet_hash=article_hash,
        approval_queue_items=[asdict(item) for item in queue_items], evidence_vault_items=[asdict(item) for item in evidence_items],
        article_preview_summary={"title": draft.get("title", ""), "subtitle": draft.get("subtitle", ""), "canonical_article_hash": article_hash, "source_article_packet_id": article_id, "editorial_status": article_packet.get("editorial_review_packet", {}).get("substack_readiness_status", "unknown"), "provider_mode": article_packet.get("provider_mode", "unknown")},
        variant_preview_cards=variant_cards,
        discord_outbox_card={"packet_id": outbox_id, "outbox_id": outbox.get("outbox_dry_run_record", {}).get("outbox_id"), "approved_payload_hash": outbox_hash, "operator_approval_status": outbox.get("operator_approval_record", {}).get("operator_approval_status"), "live_send_allowed": outbox.get("operator_approval_record", {}).get("live_send_allowed"), "live_send_performed": outbox.get("live_send_performed"), "sample_key_presence": sample_key_presence, "display_status": "amber_review_pending"},
        live_pilot_status_card={"result_class": live_status, "source_outbox_packet_id": live_pilot_result.get("source_outbox_packet_id"), "exact_payload_hash": live_pilot_result.get("exact_payload_hash"), "live_send_attempted": live_pilot_result.get("live_send_attempted"), "live_send_succeeded": live_pilot_result.get("live_send_succeeded"), "display_status": "red_blocked" if live_status == "blocked" else "amber_review", "blockers": live_pilot_result.get("blockers", [])},
        redacted_audit_summary={"queue_item_count": len(queue_items), "evidence_vault_item_count": len(evidence_items), "approval_records_all_pending": all(item.approval_status == "pending_operator_review" for item in queue_items), "live_dispatch_allowed_any": any(item.live_dispatch_allowed for item in queue_items), "sample_key_presence_scope": "sample_fixture_only", "runtime_credential_proof": False, "no_enabled_live_controls": True},
        blockers=blockers, warnings=["sample_key_presence_is_fixture_only_not_runtime_proof"],
    )
    _scan_no_secret_values(asdict(packet))
    return packet


def sample_operator_approval_queue_evidence_vault_packet() -> OperatorApprovalQueueEvidenceVaultPacket:
    return build_packet(load_json(ARTICLE_SAMPLE), load_json(VARIANT_SAMPLE), load_json(LIVE_PILOT_BLOCKED_SAMPLE))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V6 operator approval queue evidence vault UI packet.")
    parser.add_argument("--article-packet", default=str(ARTICLE_SAMPLE))
    parser.add_argument("--variant-packet", default=str(VARIANT_SAMPLE))
    parser.add_argument("--live-pilot-result", default=str(LIVE_PILOT_BLOCKED_SAMPLE))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    packet = build_packet(load_json(args.article_packet), load_json(args.variant_packet), load_json(args.live_pilot_result), article_source_path=args.article_packet, variant_source_path=args.variant_packet, live_pilot_source_path=args.live_pilot_result)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
