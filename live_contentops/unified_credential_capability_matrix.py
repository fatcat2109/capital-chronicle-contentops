"""Redacted V6 credential capability matrix.

The parser reads env files only structurally. It records key names, source files,
and blank/nonblank status; it never emits values, token lengths, prefixes,
suffixes, hashes, cookies, browser storage, or webhook URLs.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TASK_LABEL = "TASK_CONTENTOPS_V6_CAPABILITY_MATRIX_ALIAS_REPAIR_V0"
SCHEMA_VERSION = "v6_redacted_capability_matrix.v2"

KEY_VALUE_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")
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
PROVIDER_PRESENT_LIVE_GATE_REQUIRED = "provider_present_live_gate_required"
CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED = "credential_present_scope_proof_required"
NEEDS_OAUTH_REFRESH_TOKEN = "needs_oauth_refresh_token"
UNKNOWN = "unknown"

DISCORD_WEBHOOK_KEYS = (
    "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
    "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
    "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
    "DISCORD_WEBHOOK_URL",
    "DISCORD_WEBHOOK_CAPITAL_CHRONICLE",
)

DISCORD_BINDING_KEYS = (
    "DISCORD_SERVER_ID",
    "DISCORD_GUILD_ID",
    "DISCORD_ANNOUNCEMENTS_CHANNEL_ID",
    "DISCORD_SUBSTACK_DROPS_CHANNEL_ID",
    "DISCORD_PRODUCT_UPDATES_CHANNEL_ID",
    "DISCORD_RESEARCH_QUESTIONS_CHANNEL_ID",
    "DISCORD_CONTENT_IDEAS_CHANNEL_ID",
    "DISCORD_ASK_JIM_CHANNEL_ID",
    "DISCORD_FEEDBACK_CHANNEL_ID",
    "DISCORD_OPERATOR_QUEUE_CHANNEL_ID",
    "DISCORD_APPROVAL_CHECKPOINTS_CHANNEL_ID",
    "DISCORD_BROWSER_CHECKPOINTS_CHANNEL_ID",
    "DISCORD_AUDIT_LOG_CHANNEL_ID",
    "DISCORD_MANUAL_FALLBACK_CHANNEL_ID",
    "DISCORD_ROLE_FOUNDER",
    "DISCORD_ROLE_MODERATOR",
    "DISCORD_ROLE_CONTRIBUTOR",
    "DISCORD_ROLE_MEMBER",
    "DISCORD_ROLE_SUBSCRIBER",
)

NINE_ROUTER_KEYS = (
    "NINE_ROUTER_API_KEY",
    "NINE_ROUTER_BASE_URL",
    "NINE_ROUTER_MODEL",
    "CC_UI_PROVIDER_LIVE_BOUNDARY_NINE_ROUTER",
    "NINEROUTER_API_KEY",
    "ROUTER_API_KEY",
    "OPENROUTER_API_KEY",
    "AI_PROVIDER_API_KEY",
)


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
    live_write_eligible_if_present: bool
    deferred_reason: str = ""
    notes: str = ""
    require_all_nonblank: tuple[str, ...] = ()
    any_nonblank_group: tuple[str, ...] = ()


PLATFORMS: tuple[PlatformSpec, ...] = (
    PlatformSpec("Discord webhooks", "community", ADAPTER_WEBHOOK, DISCORD_WEBHOOK_KEYS, READY_WEBHOOK, DEFERRED_MISSING, "discord_webhook_handle", "discord_webhook_destination", True, notes="specific_webhook_aliases_supported", any_nonblank_group=DISCORD_WEBHOOK_KEYS),
    PlatformSpec("Discord guild/server/channel/role IDs", "community", ADAPTER_OFFICIAL_API, DISCORD_BINDING_KEYS, READY_API, DEFERRED_MISSING, "discord_ids_handle", "discord_channel_binding", False, "identity_and_routing_only", "specific_channel_role_aliases_supported", any_nonblank_group=DISCORD_BINDING_KEYS),
    PlatformSpec("Discord bot deferred", "community", ADAPTER_DEFERRED, ("DISCORD_BOT_TOKEN", "DISCORD_CLIENT_ID"), DEFERRED_REVIEW, DEFERRED_REVIEW, "discord_bot_deferred_handle", "discord_bot_deferred_destination", False, "bot_after_final_product"),
    PlatformSpec("Telegram operator inbox", "remote_operator", ADAPTER_OFFICIAL_API, ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPERATOR_CHAT_ID"), READY_API, DEFERRED_MISSING, "telegram_operator_inbox_handle", "telegram_operator_inbox_destination", True, require_all_nonblank=("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPERATOR_CHAT_ID")),
    PlatformSpec("Telegram channel", "remote_operator", ADAPTER_OFFICIAL_API, ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"), READY_API, DEFERRED_MISSING, "telegram_channel_handle", "telegram_channel_destination", True, require_all_nonblank=("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID")),
    PlatformSpec("Substack browser profile/publication metadata", "owned_long_form", ADAPTER_BROWSER_CDP, ("SUBSTACK_PUBLICATION_URL", "SUBSTACK_PUBLICATION_ID", "SUBSTACK_PROFILE_NAME"), READY_BROWSER, DEFERRED_MISSING, "substack_browser_profile_handle", "substack_publication_destination", False, "supervised_browser_only_no_secret_read", require_all_nonblank=("SUBSTACK_PUBLICATION_URL", "SUBSTACK_PUBLICATION_ID")),
    PlatformSpec("Meta Graph", "social_distribution", ADAPTER_OFFICIAL_API, ("META_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET"), CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED, DEFERRED_MISSING, "meta_graph_handle", "meta_graph_destination", False, "scope_proof_required", "meta_graph_kept_separate_from_threads", any_nonblank_group=("META_ACCESS_TOKEN",)),
    PlatformSpec("Facebook Page", "social_distribution", ADAPTER_OFFICIAL_API, ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"), CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED, DEFERRED_MISSING, "facebook_page_handle", "facebook_page_destination", False, "scope_proof_required", require_all_nonblank=("FACEBOOK_PAGE_ID",), any_nonblank_group=("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN")),
    PlatformSpec("Instagram Business", "social_distribution", ADAPTER_OFFICIAL_API, ("INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN"), CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED, DEFERRED_MISSING, "instagram_business_handle", "instagram_business_destination", False, "scope_proof_required", "business_id_plus_meta_token_requires_scope_proof", require_all_nonblank=("INSTAGRAM_BUSINESS_ACCOUNT_ID",), any_nonblank_group=("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN")),
    PlatformSpec("Threads separate app/user", "social_distribution", ADAPTER_OFFICIAL_API, ("THREADS_APP_ID", "THREADS_USER_ID", "THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN"), CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED, DEFERRED_MISSING, "threads_app_user_handle", "threads_user_destination", False, "scope_proof_required", "threads_token_alias_supported_and_kept_separate_from_meta", any_nonblank_group=("THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN")),
    PlatformSpec("YouTube OAuth/client credentials", "video_distribution", ADAPTER_OFFICIAL_API, ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"), READY_API, NEEDS_OAUTH_REFRESH_TOKEN, "youtube_oauth_handle", "youtube_channel_destination", False, require_all_nonblank=("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")),
    PlatformSpec("X manual", "social_distribution", ADAPTER_MANUAL, ("X_USERNAME", "X_PROFILE_URL"), MANUAL_ONLY, MANUAL_ONLY, "x_manual_handle", "x_manual_destination", False, "manual_distribution_lane"),
    PlatformSpec("LinkedIn personal deferred", "social_distribution", ADAPTER_DEFERRED, ("LINKEDIN_PERSONAL_PROFILE_URL", "LINKEDIN_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "linkedin_personal_deferred_handle", "linkedin_personal_destination", False, "deferred_until_verified"),
    PlatformSpec("LinkedIn organization deferred", "social_distribution", ADAPTER_DEFERRED, ("LINKEDIN_ORGANIZATION_ID", "LINKEDIN_ORG_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "linkedin_org_deferred_handle", "linkedin_org_destination", False, "deferred_until_verified"),
    PlatformSpec("TikTok deferred", "social_distribution", ADAPTER_DEFERRED, ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN"), DEFERRED_REVIEW, DEFERRED_REVIEW, "tiktok_deferred_handle", "tiktok_destination", False, "deferred_until_verified"),
    PlatformSpec("9router / AI provider", "ai_provider", ADAPTER_OFFICIAL_API, NINE_ROUTER_KEYS, PROVIDER_PRESENT_LIVE_GATE_REQUIRED, DEFERRED_MISSING, "ai_provider_handle", "ai_generation_destination", False, "live_gate_required", "nine_router_aliases_supported", any_nonblank_group=("NINE_ROUTER_API_KEY", "NINEROUTER_API_KEY", "ROUTER_API_KEY", "OPENROUTER_API_KEY", "AI_PROVIDER_API_KEY")),
    PlatformSpec("Vertex fallback / service account path", "ai_provider", ADAPTER_OFFICIAL_API, ("GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID", "VERTEX_LOCATION"), READY_API, DEFERRED_MISSING, "vertex_fallback_handle", "vertex_generation_destination", False, any_nonblank_group=("GOOGLE_APPLICATION_CREDENTIALS", "VERTEX_PROJECT_ID")),
    PlatformSpec("Browser operator profiles", "operator_local", ADAPTER_BROWSER_CDP, ("EDGE_AUTOMATION_PROFILE", "CHROME_AUTOMATION_PROFILE", "BROWSER_OPERATOR_PROFILE", "BROWSER_PROFILE", "CHROME_PROFILE", "EDGE_PROFILE", "CC_UI_BROWSER_PROFILE"), READY_BROWSER, DEFERRED_MISSING, "browser_operator_profile_handle", "browser_operator_destination", False, "no_cookie_or_storage_read", "profile_aliases_only_no_browser_storage", any_nonblank_group=("EDGE_AUTOMATION_PROFILE", "CHROME_AUTOMATION_PROFILE", "BROWSER_OPERATOR_PROFILE", "BROWSER_PROFILE", "CHROME_PROFILE", "EDGE_PROFILE", "CC_UI_BROWSER_PROFILE")),
    PlatformSpec("Media dirs", "local_assets", ADAPTER_MANUAL, ("CONTENTOPS_MEDIA_DIR", "MEDIA_DIR", "ASSET_EXPORT_DIR"), MANUAL_ONLY, UNKNOWN, "media_dirs_handle", "media_asset_destination", False),
    PlatformSpec("Approval/outbox/audit paths", "governance", ADAPTER_MANUAL, ("CONTENTOPS_APPROVAL_DIR", "CONTENTOPS_OUTBOX_DIR", "CONTENTOPS_AUDIT_DIR"), MANUAL_ONLY, UNKNOWN, "governance_paths_handle", "approval_outbox_audit_destination", False),
)


def _value_state(raw_value: str) -> str:
    stripped = raw_value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        stripped = stripped[1:-1].strip()
    return "blank" if stripped == "" else "nonblank"


def parse_env_files(paths: Iterable[Path]) -> dict:
    key_sources: dict[str, list[str]] = {}
    key_value_states: dict[str, set[str]] = {}
    malformed: list[dict[str, object]] = []
    inspected_files: list[str] = []
    for path in paths:
        inspected_files.append(path.name)
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if COMMENT_RE.match(line):
                continue
            match = KEY_VALUE_RE.match(line)
            if not match:
                malformed.append({"file": path.name, "line_number": line_number, "key_name": "UNPARSEABLE_LINE"})
                continue
            key_name, raw_value = match.groups()
            key_sources.setdefault(key_name, []).append(path.name)
            key_value_states.setdefault(key_name, set()).add(_value_state(raw_value))
    duplicates = [
        {"key_name": key, "source_count": len(sources)}
        for key, sources in sorted(key_sources.items())
        if len(sources) > 1
    ]
    value_status = {
        key: ("nonblank" if "nonblank" in states else "blank")
        for key, states in sorted(key_value_states.items())
    }
    return {
        "present_keys": sorted(key_sources),
        "key_value_status": value_status,
        "duplicates": duplicates,
        "malformed": malformed,
        "malformed_summary": {"count": len(malformed), "files": sorted({item["file"] for item in malformed}), "key_name": "UNPARSEABLE_LINE" if malformed else ""},
        "inspected_files": inspected_files,
    }


def _has_nonblank(parsed: dict, key: str) -> bool:
    return parsed["key_value_status"].get(key) == "nonblank"


def _is_capability_present(parsed: dict, spec: PlatformSpec) -> bool:
    if spec.require_all_nonblank and not all(_has_nonblank(parsed, key) for key in spec.require_all_nonblank):
        return False
    if spec.any_nonblank_group:
        return any(_has_nonblank(parsed, key) for key in spec.any_nonblank_group)
    return any(_has_nonblank(parsed, key) for key in spec.key_names)


def build_matrix(env_paths: Iterable[str | Path] = (".env", ".env.local")) -> dict:
    parsed = parse_env_files(Path(p) for p in env_paths)
    present = set(parsed["present_keys"])
    rows = []
    for spec in PLATFORMS:
        statuses = {key: (key in present) for key in spec.key_names}
        value_statuses = {key: parsed["key_value_status"].get(key, "missing") for key in spec.key_names}
        capability_present = _is_capability_present(parsed, spec)
        capability = spec.capability_if_present if capability_present else spec.capability_if_missing
        blocker = "none" if capability_present or capability in {MANUAL_ONLY, DEFERRED_REVIEW} else "credential_missing"
        if capability == NEEDS_OAUTH_REFRESH_TOKEN:
            blocker = "blank_or_missing_oauth_refresh_token"
        if capability in {PROVIDER_PRESENT_LIVE_GATE_REQUIRED, CREDENTIAL_PRESENT_SCOPE_PROOF_REQUIRED}:
            blocker = "live_gate_or_scope_proof_required"
        if spec.adapter_class == ADAPTER_DEFERRED:
            blocker = "deferred_by_plan"
        rows.append({
            "platform": spec.platform,
            "platform_family": spec.family,
            "adapter_class": spec.adapter_class,
            "key_names": list(spec.key_names),
            "key_status": statuses,
            "key_value_status": value_statuses,
            "credential_handle_id": spec.credential_handle_id,
            "destination_binding_id": spec.destination_binding_id,
            "capability_class": capability,
            "blocker_class": blocker,
            "deferred_reason": spec.deferred_reason,
            "live_write_eligible": spec.live_write_eligible_if_present and capability_present,
            "live_write_allowed_now": False,
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
            "malformed_line_output": False,
        },
        "env_inspection": {
            "files": parsed["inspected_files"],
            "present_key_names": parsed["present_keys"],
            "key_value_status": parsed["key_value_status"],
            "duplicates": parsed["duplicates"],
            "malformed": parsed["malformed"],
            "malformed_summary": parsed["malformed_summary"],
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
