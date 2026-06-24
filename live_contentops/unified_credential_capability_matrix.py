"""Redacted V6 credential capability matrix."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TASK_LABEL = "TASK_CONTENTOPS_V6_BOOTSTRAP_ENV_RECON_AND_CAPABILITY_MATRIX_V0"
SCHEMA_VERSION = "v6_redacted_capability_matrix.v1"

KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
COMMENT_RE = re.compile(r"^\s*(?:#|$)")

ADAPTER_WEBHOOK = "webhook_adapter"
ADAPTER_OFFICIAL_API = "official_api_adapter"
ADAPTER_BROWSER_CDP = "browser_cdp_adapter"
ADAPTER_MANUAL = "manual_fallback_adapter"
ADAPTER_DEFERRED = "deferred_adapter"
READY_WEBHOOK = "ready_webhook"
READY_API = "ready_api"
READY_BROWSER = "ready_browser"
MANUAL_ONLY = "manual_only"
DEFERRED_MISSING = "deferred_credentials_missing"
DEFERRED_REVIEW = "deferred_review_required"
UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlatformSpec:
    platform: str
    family: str
    adapter_class: str
    key_names: tuple[str, ...]
    capability_if_present: str
    capability_if_missing: str
    credential_handle_id: str
    destination_binding_id: str
    live_write_eligible: bool
    deferred_reason: str = ""
    notes: str = ""


PLATFORMS: tuple[PlatformSpec, ...] = (
    PlatformSpec("Discord webhooks", "community", ADAPTER_WEBHOOK, ("DISCORD_WEBHOOK_URL", "DISCORD_WEBHOOK_CAPITAL_CHRONICLE"), READY_WEBHOOK, DEFERRED_MISSING, "discord_webhook_handle", "discord_webhook_destination", True),
    PlatformSpec("Discord guild/server/channel/role IDs", "community", ADAPTER_OFFICIAL_API, ("DISCORD_GUILD_ID", "DISCORD_SERVER_ID", "DISCORD_CHANNEL_ID", "DISCORD_ROLE_ID"), READY_API, DEFERRED_MISSING, "discord_ids_handle", "discord_channel_binding", False, "identity_and_routing_only"),
    PlatformSpec("Discord bot deferred", "community", ADAPTER_DEFERRED, ("DISCORD_BOT_TOKEN", "DISCORD_CLIENT_ID"), DEFERRED_REVIEW, DEFERRED_REVIEW, "discord_bot_deferred_handle", "discord_bot_deferred_destination", False, "bot_after_final_product"),
    PlatformSpec("Telegram operator inbox", "remote_operator", ADAPTER_OFFICIAL_API, ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPERATOR_CHAT_ID"), READY_API, DEFERRED_MISSING, "telegram_operator_inbox_handle", "telegram_operator_inbox_destination", True),
    PlatformSpec("Telegram channel", "remote_operator", ADAPTER_OFFICIAL_API, ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"), READY_API, DEFERRED_MISSING, "telegram_channel_handle", "telegram_channel_destination", True),
    PlatformSpec("Substack browser profile/publication metadata", "owned_long_form", ADAPTER_BROWSER_CDP, ("SUBSTACK_PUBLICATION_URL", "SUBSTACK_PUBLICATION_ID", "SUBSTACK_PROFILE_NAME"), READY_BROWSER, DEFERRED_MISSING, "substack_browser_profile_handle", "substack_publication_destination", False, "supervised_browser_only_no_secret_read"),
    PlatformSpec("Meta Graph", "social_distribution", ADAPTER_OFFICIAL_API, ("META_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET"), READY_API, DEFERRED_MISSING, "meta_graph_handle", "meta_graph_destination", False),
    PlatformSpec("Facebook Page", "social_distribution", ADAPTER_OFFICIAL_API, ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"), READY_API, DEFERRED_MISSING, "facebook_page_handle", "facebook_page_destination", False),
    PlatformSpec("Instagram Business", "social_distribution", ADAPTER_OFFICIAL_API, ("INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_ACCESS_TOKEN"), READY_API, DEFERRED_MISSING, "instagram_business_handle", "instagram_business_destination", False),
    PlatformSpec("Threads separate app/user", "social_distribution", ADAPTER_OFFICIAL_API, ("THREADS_APP_ID", "THREADS_USER_ID", "THREADS_ACCESS_TOKEN"), READY_API, DEFERRED_MISSING, "threads_app_user_handle", "threads_user_destination", False),
    PlatformSpec("YouTube OAuth/client credentials", "video_distribution", ADAPTER_OFFICIAL_API, ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"), READY_API, DEFERRED_MISSING, "youtube_oauth_handle", "youtube_channel_destination", False),
    PlatformSpec("X manual", "social_distribution", ADAPTER_MANUAL, ("X_USERNAME", "X_PROFILE_URL"), MANUAL_ONLY, MANUAL_ONLY, "x_manual_handle", "x_manual_destination", False, "manual_distribution_lane"),
    PlatformSpec("LinkedIn personal deferred", "social_distribution", ADAPTER_DEFERRED, ("LINKEDIN_PERSONAL_PROFILE_URL", "LINKEDIN_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "linkedin_personal_deferred_handle", "linkedin_personal_destination", False, "deferred_until_verified"),
    PlatformSpec("LinkedIn organization deferred", "social_distribution", ADAPTER_DEFERRED, ("LINKEDIN_ORGANIZATION_ID", "LINKEDIN_ORG_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "linkedin_org_deferred_handle", "linkedin_org_destination", False, "deferred_until_verified"),
    PlatformSpec("TikTok deferred", "social_distribution", ADAPTER_DEFERRED, ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "tiktok_deferred_handle", "tiktok_destination", False, "deferred_until_verified"),
    PlatformSpec("9router / AI provider", "ai_provider", ADAPTER_OFFICIAL_API, ("ROUTER_API_KEY", "NINEROUTER_API_KEY", "OPENROUTER_API_KEY", "AI_PROVIDER_API_KEY"), READY_API, DEFERRED_MISSING, "ai_provider_handle", "ai_generation_destination", False),
    PlatformSpec("Vertex fallback / service account path", "ai_provider", ADAPTER_OFFICIAL_API, ("GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID", "VERTEX_LOCATION"), READY_API, DEFERRED_MISSING, "vertex_fallback_handle", "vertex_generation_destination", False),
    PlatformSpec("Browser operator profiles", "operator_local", ADAPTER_BROWSER_CDP, ("EDGE_AUTOMATION_PROFILE", "CHROME_AUTOMATION_PROFILE", "BROWSER_OPERATOR_PROFILE"), READY_BROWSER, DEFERRED_MISSING, "browser_operator_profile_handle", "browser_operator_destination", False, "no_cookie_or_storage_read"),
    PlatformSpec("Media dirs", "local_assets", ADAPTER_MANUAL, ("CONTENTOPS_MEDIA_DIR", "MEDIA_DIR", "ASSET_EXPORT_DIR"), MANUAL_ONLY, UNKNOWN, "media_dirs_handle", "media_asset_destination", False),
    PlatformSpec("Approval/outbox/audit paths", "governance", ADAPTER_MANUAL, ("CONTENTOPS_APPROVAL_DIR", "CONTENTOPS_OUTBOX_DIR", "CONTENTOPS_AUDIT_DIR"), MANUAL_ONLY, UNKNOWN, "governance_paths_handle", "approval_outbox_audit_destination", False),
)


def parse_env_files(paths: Iterable[Path]) -> dict:
    key_sources: dict[str, list[str]] = {}
    malformed: list[dict[str, object]] = []
    inspected_files: list[str] = []
    for path in paths:
        inspected_files.append(path.name)
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if COMMENT_RE.match(line):
                continue
            match = KEY_RE.match(line)
            if not match:
                malformed.append({"file": path.name, "line_number": line_number, "key_name": "UNPARSEABLE_LINE"})
                continue
            key_sources.setdefault(match.group(1), []).append(path.name)
    duplicates = [
        {"key_name": key, "source_count": len(sources)}
        for key, sources in sorted(key_sources.items())
        if len(sources) > 1
    ]
    return {"present_keys": sorted(key_sources), "duplicates": duplicates, "malformed": malformed, "inspected_files": inspected_files}


def build_matrix(env_paths: Iterable[str | Path] = (".env", ".env.local")) -> dict:
    parsed = parse_env_files(Path(p) for p in env_paths)
    present = set(parsed["present_keys"])
    rows = []
    for spec in PLATFORMS:
        statuses = {key: (key in present) for key in spec.key_names}
        any_present = any(statuses.values())
        capability = spec.capability_if_present if any_present else spec.capability_if_missing
        blocker = "none" if any_present or capability in {MANUAL_ONLY, DEFERRED_REVIEW} else "credential_missing"
        if spec.adapter_class == ADAPTER_DEFERRED:
            blocker = "deferred_by_plan"
        rows.append({
            "platform": spec.platform,
            "platform_family": spec.family,
            "adapter_class": spec.adapter_class,
            "key_names": list(spec.key_names),
            "key_status": statuses,
            "credential_handle_id": spec.credential_handle_id,
            "destination_binding_id": spec.destination_binding_id,
            "capability_class": capability,
            "blocker_class": blocker,
            "deferred_reason": spec.deferred_reason,
            "live_write_eligible": spec.live_write_eligible and any_present,
            "notes": spec.notes,
        })
    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "redaction_policy": {
            "raw_secret_output": False,
            "webhook_url_output": False,
            "token_length_prefix_suffix_hash_output": False,
            "browser_cookie_storage_read": False,
        },
        "env_inspection": {
            "files": parsed["inspected_files"],
            "present_key_names": parsed["present_keys"],
            "duplicates": parsed["duplicates"],
            "malformed": parsed["malformed"],
        },
        "platform_rows": rows,
    }


def write_packet(packet: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build redacted V6 credential capability matrix")
    parser.add_argument("--env-file", action="append", default=None, help="Env file to inspect structurally")
    parser.add_argument("--output", default=None, help="Optional packet output path")
    args = parser.parse_args(argv)
    packet = build_matrix(args.env_file or [".env", ".env.local"])
    if args.output:
        write_packet(packet, args.output)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
