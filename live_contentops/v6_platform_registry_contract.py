"""V6 platform registry and adapter taxonomy overlay contract.

This overlay avoids editing older dirty registry files. It consumes the redacted
capability matrix shape and emits no raw credentials or live-write authority.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from live_contentops.unified_credential_capability_matrix import build_matrix

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_REGISTRY_AND_DISCORD_ENVIRONMENT_CONTRACT_V0"
SCHEMA_VERSION = "v6_platform_registry_contract.v1"

PLATFORM_FAMILIES: tuple[str, ...] = (
    "owned_long_form",
    "community",
    "remote_operator",
    "social_distribution",
    "media_video_later",
    "ai_provider",
    "local_assets",
    "governance",
    "operator_local",
)

ADAPTER_TYPES: tuple[str, ...] = (
    "webhook_adapter",
    "official_api_adapter",
    "browser_cdp_adapter",
    "manual_fallback_adapter",
    "deferred_adapter",
)

EXECUTION_POSTURES: tuple[str, ...] = (
    "ready_webhook_but_live_disabled",
    "ready_api_but_live_disabled",
    "ready_browser_but_live_disabled",
    "manual_only",
    "deferred_after_final_product",
    "scope_proof_required",
    "credential_missing",
    "governance_only",
)


@dataclass(frozen=True)
class PlatformRegistryEntry:
    platform_id: str
    platform_family: str
    display_name: str
    adapter_type: str
    current_execution_posture: str
    matrix_platform: str
    live_write_allowed_now: bool
    rules: tuple[str, ...]


BASE_REGISTRY: tuple[PlatformRegistryEntry, ...] = (
    PlatformRegistryEntry("substack", "owned_long_form", "Substack", "browser_cdp_adapter", "ready_browser_but_live_disabled", "Substack browser profile/publication metadata", False, ("canonical_long_form_authority", "supervised_browser_only_no_secret_read")),
    PlatformRegistryEntry("discord", "community", "Discord", "webhook_adapter", "credential_missing", "Discord webhooks", False, ("webhook_adapter_exists", "bot_deferred_after_final_product", "live_disabled")),
    PlatformRegistryEntry("telegram", "remote_operator", "Telegram", "official_api_adapter", "ready_api_but_live_disabled", "Telegram operator inbox", False, ("remote_operator_lane", "live_disabled")),
    PlatformRegistryEntry("x_manual", "social_distribution", "X manual", "manual_fallback_adapter", "manual_only", "X manual", False, ("manual_only",)),
    PlatformRegistryEntry("linkedin_personal_deferred", "social_distribution", "LinkedIn personal deferred", "deferred_adapter", "deferred_after_final_product", "LinkedIn personal deferred", False, ("deferred_until_future_task",)),
    PlatformRegistryEntry("linkedin_org_deferred", "social_distribution", "LinkedIn organization deferred", "deferred_adapter", "deferred_after_final_product", "LinkedIn organization deferred", False, ("deferred_until_future_task",)),
    PlatformRegistryEntry("threads", "social_distribution", "Threads", "official_api_adapter", "scope_proof_required", "Threads separate app/user", False, ("separate_from_meta_graph", "scope_proof_required", "live_disabled")),
    PlatformRegistryEntry("facebook_page", "social_distribution", "Facebook Page", "official_api_adapter", "scope_proof_required", "Facebook Page", False, ("scope_proof_required", "live_disabled")),
    PlatformRegistryEntry("instagram_business", "social_distribution", "Instagram Business", "official_api_adapter", "scope_proof_required", "Instagram Business", False, ("scope_proof_required", "live_disabled")),
    PlatformRegistryEntry("youtube_later", "media_video_later", "YouTube later", "official_api_adapter", "ready_api_but_live_disabled", "YouTube OAuth/client credentials", False, ("media_video_later", "live_disabled")),
    PlatformRegistryEntry("tiktok_deferred", "social_distribution", "TikTok deferred", "deferred_adapter", "deferred_after_final_product", "TikTok deferred", False, ("deferred_until_future_task",)),
    PlatformRegistryEntry("nine_router", "ai_provider", "9router", "official_api_adapter", "credential_missing", "9router / AI provider", False, ("provider_not_public_authority", "live_gate_required", "live_disabled")),
    PlatformRegistryEntry("vertex_fallback", "ai_provider", "Vertex fallback", "official_api_adapter", "credential_missing", "Vertex fallback / service account path", False, ("fallback_provider", "live_disabled")),
    PlatformRegistryEntry("browser_operator_profiles", "operator_local", "Browser operator profiles", "browser_cdp_adapter", "credential_missing", "Browser operator profiles", False, ("no_cookie_storage_read", "live_disabled")),
    PlatformRegistryEntry("media_dirs", "local_assets", "Media dirs", "manual_fallback_adapter", "manual_only", "Media dirs", False, ("local_assets_only",)),
    PlatformRegistryEntry("approval_outbox_audit_paths", "governance", "Approval/outbox/audit paths", "manual_fallback_adapter", "governance_only", "Approval/outbox/audit paths", False, ("governance_only",)),
)


def _rows_by_platform(capability_packet: dict) -> dict[str, dict]:
    return {row["platform"]: row for row in capability_packet.get("platform_rows", [])}


def _posture_from_matrix(entry: PlatformRegistryEntry, matrix_row: dict | None) -> str:
    if entry.platform_id in {"x_manual", "media_dirs"}:
        return "manual_only"
    if entry.platform_id == "approval_outbox_audit_paths":
        return "governance_only"
    if entry.platform_id in {"linkedin_personal_deferred", "linkedin_org_deferred", "tiktok_deferred"}:
        return "deferred_after_final_product"
    if matrix_row is None:
        return entry.current_execution_posture
    capability = matrix_row.get("capability_class")
    adapter = matrix_row.get("adapter_class")
    if entry.platform_id == "discord" and capability == "ready_webhook" and adapter == "webhook_adapter":
        return "ready_webhook_but_live_disabled"
    if capability == "ready_api":
        return "ready_api_but_live_disabled"
    if capability == "ready_browser":
        return "ready_browser_but_live_disabled"
    if capability in {"credential_present_scope_proof_required", "provider_present_live_gate_required"}:
        return "scope_proof_required"
    if capability == "manual_only":
        return "manual_only"
    if capability == "deferred_review_required":
        return "deferred_after_final_product"
    return "credential_missing"


def build_registry(capability_packet: dict | None = None) -> dict:
    packet = capability_packet or build_matrix([".env", ".env.local"])
    matrix_rows = _rows_by_platform(packet)
    platforms = []
    for entry in BASE_REGISTRY:
        row = matrix_rows.get(entry.matrix_platform)
        data = asdict(entry)
        data["current_execution_posture"] = _posture_from_matrix(entry, row)
        data["live_write_allowed_now"] = False
        data["matrix_capability_class"] = row.get("capability_class") if row else "missing_matrix_row"
        data["matrix_live_write_eligible"] = bool(row.get("live_write_eligible")) if row else False
        platforms.append(data)
    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "platform_families": list(PLATFORM_FAMILIES),
        "adapter_types": list(ADAPTER_TYPES),
        "allowed_current_execution_postures": list(EXECUTION_POSTURES),
        "live_write_allowed_now": False,
        "platforms": platforms,
        "rules": {
            "discord_bot_deferred_after_final_product": True,
            "threads_separate_from_meta_graph": True,
            "x_manual_only": True,
            "linkedin_deferred": True,
            "tiktok_deferred": True,
            "meta_family_scope_proof_required": True,
            "nine_router_provider_not_public_authority": True,
            "all_live_writes_disabled": True,
        },
    }


def write_packet(packet: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V6 platform registry overlay packet")
    parser.add_argument("--matrix-packet", default=None, help="Redacted capability matrix packet path")
    parser.add_argument("--output", default=None, help="Optional output path")
    args = parser.parse_args(argv)
    capability_packet = None
    if args.matrix_packet:
        capability_packet = json.loads(Path(args.matrix_packet).read_text(encoding="utf-8"))
    packet = build_registry(capability_packet)
    if args.output:
        write_packet(packet, args.output)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
