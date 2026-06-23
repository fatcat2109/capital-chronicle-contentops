"""Explicit credential hydration gate for Batch A.

Presence-only inventory. No import-time env reads. Raw values never returned.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping
import os

from .credential_redaction_policy import REDACTION_POLICY_ID, redacted_presence
from .platform_docs_registry import registry_by_platform_id

TASK_LABEL = "TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_A_DOCS_CREDENTIALS_BINDINGS_AND_READONLY_PROBES_V0"

CREDENTIAL_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ('telegram_remote_operator', 'telegram_bot_token', 'api_token', 'TELEGRAM_BOT_TOKEN'),
    ('telegram_remote_operator', 'telegram_operator_chat', 'destination_id', 'TELEGRAM_OPERATOR_CHAT_ID'),
    ('telegram_channel_destination', 'telegram_bot_token', 'api_token', 'TELEGRAM_BOT_TOKEN'),
    ('telegram_channel_destination', 'telegram_channel', 'destination_id', 'TELEGRAM_CHANNEL_ID'),
    ('x_profile', 'x_bearer', 'bearer_token', 'X_BEARER_TOKEN'),
    ('x_profile', 'x_api_key', 'api_key', 'X_API_KEY'),
    ('x_profile', 'x_api_secret', 'api_secret', 'X_API_SECRET'),
    ('x_profile', 'x_access_token', 'access_token', 'X_ACCESS_TOKEN'),
    ('x_profile', 'x_access_secret', 'access_token_secret', 'X_ACCESS_TOKEN_SECRET'),
    ('x_profile', 'x_client_id', 'oauth_client_id', 'X_CLIENT_ID'),
    ('x_profile', 'x_client_secret', 'oauth_client_secret', 'X_CLIENT_SECRET'),
    ('linkedin_member_profile', 'linkedin_token', 'access_token', 'LINKEDIN_ACCESS_TOKEN'),
    ('linkedin_member_profile', 'linkedin_member', 'account_urn', 'LINKEDIN_MEMBER_URN'),
    ('linkedin_organization_page', 'linkedin_token', 'access_token', 'LINKEDIN_ACCESS_TOKEN'),
    ('linkedin_organization_page', 'linkedin_org', 'organization_urn', 'LINKEDIN_ORGANIZATION_URN'),
    ('facebook_page', 'meta_token', 'access_token', 'META_ACCESS_TOKEN'),
    ('facebook_page', 'facebook_page', 'page_id', 'FACEBOOK_PAGE_ID'),
    ('instagram_professional_account', 'meta_token', 'access_token', 'META_ACCESS_TOKEN'),
    ('instagram_professional_account', 'instagram_business', 'account_id', 'INSTAGRAM_BUSINESS_ACCOUNT_ID'),
    ('threads_profile', 'meta_token', 'access_token', 'META_ACCESS_TOKEN'),
    ('threads_profile', 'threads_user', 'user_id', 'THREADS_USER_ID'),
    ('tiktok_account', 'tiktok_token', 'access_token', 'TIKTOK_ACCESS_TOKEN'),
    ('tiktok_account', 'tiktok_open', 'open_id', 'TIKTOK_OPEN_ID'),
    ('youtube_channel', 'youtube_access', 'access_token', 'YOUTUBE_ACCESS_TOKEN'),
    ('youtube_channel', 'youtube_refresh', 'refresh_token', 'YOUTUBE_REFRESH_TOKEN'),
    ('youtube_channel', 'youtube_channel', 'channel_id', 'YOUTUBE_CHANNEL_ID'),
    ('substack_newsletter', 'substack_publication', 'publication_url', 'SUBSTACK_PUBLICATION_URL'),
    ('substack_newsletter', 'substack_hint', 'account_hint', 'SUBSTACK_EMAIL_OR_ACCOUNT_HINT'),
)


@dataclass(frozen=True)
class CredentialInventoryRow:
    platform_id: str
    credential_handle_id: str
    credential_kind: str
    env_key_name: str
    configured_symbolic: bool
    env_presence_verified_redacted: str
    hydration_allowed_for_task: bool
    required_scopes: tuple[str, ...]
    verified_scopes: tuple[str, ...]
    missing_scopes: tuple[str, ...]
    redaction_policy_id: str
    status: str
    blocked_reasons: tuple[str, ...]


def _read_env_file_keys(env_path: Path) -> set[str]:
    if not env_path.exists():
        return set()
    keys: set[str] = set()
    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def collect_env_key_presence(repo_root: str | Path, *, include_process_env: bool = False) -> dict[str, bool]:
    root = Path(repo_root)
    keys = _read_env_file_keys(root / ".env") | _read_env_file_keys(root / ".env.local")
    if include_process_env:
        keys |= set(getattr(os, "environ"))
    wanted = {spec[3] for spec in CREDENTIAL_SPECS}
    return {key: key in keys for key in sorted(wanted)}


def build_credential_inventory(repo_root: str | Path, *, include_process_env: bool = False) -> tuple[CredentialInventoryRow, ...]:
    docs = registry_by_platform_id()
    presence = collect_env_key_presence(repo_root, include_process_env=include_process_env)
    rows: list[CredentialInventoryRow] = []
    for platform_id, handle_id, kind, env_key in CREDENTIAL_SPECS:
        present = bool(presence.get(env_key, False))
        docs_row = docs[platform_id]
        blocked = []
        if not present:
            blocked.append("credential_env_key_missing")
        if docs_row.docs_status == "docs_unverified":
            blocked.append("official_docs_unverified")
        if docs_row.re_ground_required_before_live:
            blocked.append("re_ground_required_before_live")
        rows.append(CredentialInventoryRow(
            platform_id=platform_id,
            credential_handle_id=handle_id,
            credential_kind=kind,
            env_key_name=env_key,
            configured_symbolic=present,
            env_presence_verified_redacted=redacted_presence(present, env_key),
            hydration_allowed_for_task=present and docs_row.docs_status != "docs_unverified",
            required_scopes=docs_row.required_scopes,
            verified_scopes=(),
            missing_scopes=docs_row.required_scopes,
            redaction_policy_id=REDACTION_POLICY_ID,
            status="present_redacted_unverified_scope" if present else "missing_blocked",
            blocked_reasons=tuple(blocked),
        ))
    return tuple(rows)


def credential_inventory_packet(repo_root: str | Path, *, include_process_env: bool = False) -> dict[str, object]:
    rows = [asdict(row) for row in build_credential_inventory(repo_root, include_process_env=include_process_env)]
    return {
        "task_label": TASK_LABEL,
        "raw_values_persisted": False,
        "redaction_policy_id": REDACTION_POLICY_ID,
        "include_process_env": include_process_env,
        "rows": rows,
    }
