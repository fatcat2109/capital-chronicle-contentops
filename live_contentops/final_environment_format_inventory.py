"""Final environment format redacted inventory contract.

Local-only structural parser for `.env` format compliance.
No platform API calls, provider calls, browser/CDP, or live writes.
Reports key names, booleans, duplicate keys, deferred empty placeholders,
and raw-block detection only. Never returns raw values, token lengths,
prefixes, suffixes, hashes, or digests.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

TASK_LABEL = "TASK_CONTENTOPS_FINAL_ENV_FORMAT_DOC_AND_REDACTED_INVENTORY_CONTRACT_V0"

DEFERRED_EMPTY_KEYS: tuple[str, ...] = (
    "X_CLIENT_ID",
    "X_CLIENT_SECRET",
    "X_ACCESS_TOKEN",
    "X_REFRESH_TOKEN",
    "X_USER_ID",
    "X_ACCESS_TIER_CLASS",
    "LINKEDIN_CLIENT_ID",
    "LINKEDIN_CLIENT_SECRET",
    "LINKEDIN_ACCESS_TOKEN",
    "LINKEDIN_MEMBER_URN",
    "LINKEDIN_ORGANIZATION_URN",
    "TIKTOK_CLIENT_KEY",
    "TIKTOK_CLIENT_SECRET",
    "TIKTOK_ACCESS_TOKEN",
    "TIKTOK_REFRESH_TOKEN",
    "TIKTOK_OPEN_ID",
)

REQUIRED_KEY_FAMILIES: Mapping[str, tuple[str, ...]] = {
    "telegram": (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHANNEL_ID",
        "TELEGRAM_OPERATOR_CHAT_ID",
        "TELEGRAM_OPERATOR_CREDENTIAL_HANDLE_ID",
        "TELEGRAM_CHANNEL_CREDENTIAL_HANDLE_ID",
        "TELEGRAM_OPERATOR_DESTINATION_BINDING_ID",
        "TELEGRAM_CHANNEL_DESTINATION_BINDING_ID",
    ),
    "meta_graph": (
        "META_GRAPH_APP_ID",
        "META_GRAPH_APP_SECRET",
        "META_GRAPH_APP_NAME",
        "META_GRAPH_API_VERSION",
        "META_GRAPH_BASE_URL",
        "META_GRAPH_CREDENTIAL_HANDLE_ID",
        "META_GRAPH_GRANTED_SCOPES",
    ),
    "facebook_page": (
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_PAGE_ACCESS_TOKEN",
        "FACEBOOK_PAGE_CREDENTIAL_HANDLE_ID",
        "FACEBOOK_PAGE_DESTINATION_BINDING_ID",
        "FACEBOOK_PAGE_GRANTED_TASKS",
    ),
    "instagram": (
        "INSTAGRAM_BUSINESS_ACCOUNT_ID",
        "INSTAGRAM_API_VERSION",
        "INSTAGRAM_BASE_URL",
        "INSTAGRAM_CREDENTIAL_HANDLE_ID",
        "INSTAGRAM_DESTINATION_BINDING_ID",
        "INSTAGRAM_USERNAME",
    ),
    "threads": (
        "THREADS_APP_ID",
        "THREADS_APP_SECRET",
        "THREADS_APP_NAME",
        "THREADS_USER_ID",
        "THREADS_USER_ACCESS_TOKEN",
        "THREADS_REDIRECT_URI",
        "THREADS_SCOPES",
        "THREADS_CREDENTIAL_HANDLE_ID",
        "THREADS_DESTINATION_BINDING_ID",
        "THREADS_USERNAME",
        "THREADS_GRANTED_SCOPES",
    ),
    "youtube": (
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_CLIENT_SECRETS_JSON_PATH",
        "YOUTUBE_CHANNEL_ID",
        "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_CREDENTIAL_HANDLE_ID",
        "YOUTUBE_CHANNEL_DESTINATION_BINDING_ID",
    ),
    "substack": (
        "SUBSTACK_PUBLICATION_URL",
        "SUBSTACK_PUBLICATION_ID",
        "SUBSTACK_USER_ID",
        "SUBSTACK_HANDLE",
        "SUBSTACK_EMAIL_OR_ACCOUNT_HINT",
        "SUBSTACK_TEST_PUBLICATION_URL",
        "SUBSTACK_TEST_PUBLICATION_ID",
        "SUBSTACK_CREDENTIAL_HANDLE_ID",
        "SUBSTACK_DESTINATION_BINDING_ID",
        "SUBSTACK_BROWSER_PROFILE_ID",
        "SUBSTACK_BROWSER_PROFILE_PATH",
        "SUBSTACK_DASHBOARD_URL",
        "SUBSTACK_POSTS_LIST_URL",
        "SUBSTACK_COMPOSE_URL",
        "SUBSTACK_AUTOMATION_MODE",
    ),
    "browser_operator": (
        "BROWSER_OPERATOR_ENGINE",
        "BROWSER_OPERATOR_PROFILE_ROOT",
        "BROWSER_OPERATOR_SCREENSHOT_DIR",
        "BROWSER_OPERATOR_AUDIT_DIR",
        "BROWSER_OPERATOR_REQUEST_BUDGET",
        "BROWSER_OPERATOR_AUTO_RETRY_ALLOWED",
        "BROWSER_OPERATOR_REQUIRES_JIM_GO",
    ),
    "ai_provider_metadata": (
        "AI_PROVIDER_SELECTED",
        "AI_PROVIDER_CREDENTIAL_HANDLE_ID",
        "AI_PROVIDER_COST_BUDGET_DAILY_USD",
        "AI_PROVIDER_ALLOWED_CONTEXT_CLASSES",
        "AI_PROVIDER_FORBIDDEN_CONTEXT_CLASSES",
        "AI_PROVIDER_PROMPT_REDACTION_POLICY_ID",
    ),
    "media_dirs": (
        "MEDIA_RIGHTS_MANIFEST_DIR",
        "MEDIA_APPROVED_DOWNLOAD_DIR",
        "MEDIA_GENERATED_CARD_DIR",
        "MEDIA_LICENSE_POLICY_ID",
        "MEDIA_ATTRIBUTION_REQUIRED_DEFAULT",
    ),
    "approval_outbox_audit_paths": (
        "APPROVAL_LEDGER_PATH",
        "DISPATCH_OUTBOX_PATH",
        "AUTOMATION_AUDIT_LOG_PATH",
        "PAYLOAD_HASH_LOCK_DIR",
        "VISUAL_CHECKPOINT_DIR",
    ),
    "x_placeholders": (
        "X_CLIENT_ID",
        "X_CLIENT_SECRET",
        "X_ACCESS_TOKEN",
        "X_REFRESH_TOKEN",
        "X_USER_ID",
        "X_ACCESS_TIER_CLASS",
        "X_AUTOMATION_MODE",
    ),
    "linkedin_placeholders": (
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_MEMBER_URN",
        "LINKEDIN_ORGANIZATION_URN",
        "LINKEDIN_AUTOMATION_MODE",
    ),
    "tiktok_placeholders": (
        "TIKTOK_CLIENT_KEY",
        "TIKTOK_CLIENT_SECRET",
        "TIKTOK_ACCESS_TOKEN",
        "TIKTOK_REFRESH_TOKEN",
        "TIKTOK_OPEN_ID",
        "TIKTOK_AUTOMATION_MODE",
    ),
    "vertex_path_references": (
        "GOOGLE_APPLICATION_CREDENTIALS",
        "VERTEX_PROJECT_ID",
        "VERTEX_SERVICE_ACCOUNT_EMAIL",
    ),
}

REQUIRED_KEYS: tuple[str, ...] = tuple(
    dict.fromkeys(key for keys in REQUIRED_KEY_FAMILIES.values() for key in keys)
)

@dataclass(frozen=True)
class ParsedEnv:
    key_order: tuple[str, ...]
    values_present: Mapping[str, bool]
    duplicate_keys: tuple[str, ...]
    raw_json_block_present: bool
    private_key_block_present: bool


def _strip_optional_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_text(env_text: str) -> ParsedEnv:
    """Parse dotenv text and return only structural redacted facts."""
    key_order: list[str] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    values_present: dict[str, bool] = {}
    raw_json_block_present = False
    private_key_block_present = False

    for raw_line in env_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("{") or stripped.startswith("}") or stripped.startswith('"'):
            raw_json_block_present = True
        if "-----BEGIN" in stripped and "PRIVATE KEY-----" in stripped:
            private_key_block_present = True
        if "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        if not key or any(ch.isspace() for ch in key):
            continue
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
        key_order.append(key)
        values_present[key] = bool(_strip_optional_quotes(raw_value).strip())

    return ParsedEnv(
        key_order=tuple(key_order),
        values_present=values_present,
        duplicate_keys=tuple(sorted(duplicates)),
        raw_json_block_present=raw_json_block_present,
        private_key_block_present=private_key_block_present,
    )


def build_inventory_from_text(env_text: str, *, source_label: str = "injected_env_text_redacted") -> dict[str, object]:
    parsed = parse_env_text(env_text)
    present_keys = set(parsed.values_present)
    missing = tuple(key for key in REQUIRED_KEYS if key not in present_keys)
    deferred_empty = tuple(
        key for key in DEFERRED_EMPTY_KEYS
        if key in present_keys and not parsed.values_present.get(key, False)
    )
    family_key_presence = {
        family: {key: key in present_keys for key in keys}
        for family, keys in REQUIRED_KEY_FAMILIES.items()
    }
    family_present = {
        family: all(key in present_keys for key in keys)
        for family, keys in REQUIRED_KEY_FAMILIES.items()
    }
    report: dict[str, object] = {
        "task_label": TASK_LABEL,
        "mode": "final_environment_format_redacted_inventory_only",
        "source_label": source_label,
        "key_count": len(parsed.key_order),
        "duplicate_keys": list(parsed.duplicate_keys),
        "required_key_missing": list(missing),
        "deferred_empty_keys": list(deferred_empty),
        "raw_json_block_present": parsed.raw_json_block_present,
        "private_key_block_present": parsed.private_key_block_present,
        "known_secret_values_redacted": True,
        "raw_values_returned": False,
        "token_length_prefix_suffix_digest_hash_returned": False,
        "platform_families_present": family_present,
        "platform_family_key_presence": family_key_presence,
    }
    assert_inventory_safe(report)
    return report


def build_inventory(repo_root: str | Path = ".") -> dict[str, object]:
    root = Path(repo_root)
    env_path = root / ".env"
    text = env_path.read_text(encoding="utf-8", errors="replace") if env_path.exists() else ""
    return build_inventory_from_text(text, source_label="repo_dotenv_redacted")


def assert_inventory_safe(report: Mapping[str, object]) -> None:
    serialized = json.dumps(report, sort_keys=True, ensure_ascii=False)
    forbidden_markers = (
        "access_token=",
        "refresh_token=",
        "client_secret=",
        "authorization:",
        "cookie:",
        "sessionStorage",
        "localStorage",
        "-----BEGIN PRIVATE KEY-----",
    )
    lowered = serialized.lower()
    for marker in forbidden_markers:
        if marker.lower() in lowered:
            raise ValueError("unsafe_raw_secret_marker_in_inventory")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redacted final .env format inventory.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = build_inventory(args.repo_root)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
