"""Redacted social credential setup inventory workbench."""
from __future__ import annotations

import argparse, json, os, re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .credential_redaction_policy import contains_secret_shaped_text

TASK_LABEL = "TASK_CONTENTOPS_OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP_WORKBENCH_V0"

@dataclass(frozen=True)
class CredentialKey:
    platform: str
    key_name: str
    setup_priority: str
    expected_shape: str

MATRIX: tuple[CredentialKey, ...] = (
    CredentialKey("telegram", "TELEGRAM_BOT_TOKEN", "p0", "telegram_bot_token"),
    CredentialKey("telegram", "TELEGRAM_CHANNEL_ID", "p0", "channel_identifier"),
    CredentialKey("telegram", "TELEGRAM_OPERATOR_CHAT_ID", "p1", "chat_identifier"),
    CredentialKey("x", "X_CLIENT_ID", "p0", "oauth_client_id"),
    CredentialKey("x", "X_CLIENT_SECRET", "p0", "oauth_client_secret"),
    CredentialKey("x", "X_ACCESS_TOKEN", "p1", "oauth_access_token"),
    CredentialKey("x", "X_REFRESH_TOKEN", "p1", "oauth_refresh_token"),
    CredentialKey("x", "X_USER_ID", "p1", "user_identifier"),
    CredentialKey("x", "X_ACCESS_TIER_CLASS", "p2", "tier_label"),
    CredentialKey("linkedin", "LINKEDIN_CLIENT_ID", "p0", "oauth_client_id"),
    CredentialKey("linkedin", "LINKEDIN_CLIENT_SECRET", "p0", "oauth_client_secret"),
    CredentialKey("linkedin", "LINKEDIN_ACCESS_TOKEN", "p1", "oauth_access_token"),
    CredentialKey("linkedin", "LINKEDIN_MEMBER_URN", "p1", "urn"),
    CredentialKey("linkedin", "LINKEDIN_ORGANIZATION_URN", "p2", "urn"),
    CredentialKey("meta", "META_APP_ID", "p0", "app_id"),
    CredentialKey("meta", "META_APP_SECRET", "p0", "app_secret"),
    CredentialKey("meta", "META_ACCESS_TOKEN", "p1", "oauth_access_token"),
    CredentialKey("meta", "FACEBOOK_PAGE_ID", "p1", "page_identifier"),
    CredentialKey("meta", "FACEBOOK_PAGE_ACCESS_TOKEN", "p1", "page_access_token"),
    CredentialKey("meta", "INSTAGRAM_BUSINESS_ACCOUNT_ID", "p2", "account_identifier"),
    CredentialKey("meta", "THREADS_USER_ID", "p2", "user_identifier"),
    CredentialKey("tiktok", "TIKTOK_CLIENT_KEY", "p0", "oauth_client_key"),
    CredentialKey("tiktok", "TIKTOK_CLIENT_SECRET", "p0", "oauth_client_secret"),
    CredentialKey("tiktok", "TIKTOK_ACCESS_TOKEN", "p1", "oauth_access_token"),
    CredentialKey("tiktok", "TIKTOK_REFRESH_TOKEN", "p1", "oauth_refresh_token"),
    CredentialKey("tiktok", "TIKTOK_OPEN_ID", "p1", "open_id"),
    CredentialKey("youtube", "YOUTUBE_CLIENT_ID", "p0", "oauth_client_id"),
    CredentialKey("youtube", "YOUTUBE_CLIENT_SECRET", "p0", "oauth_client_secret"),
    CredentialKey("youtube", "YOUTUBE_REFRESH_TOKEN", "p1", "oauth_refresh_token"),
    CredentialKey("youtube", "YOUTUBE_CHANNEL_ID", "p1", "channel_identifier"),
    CredentialKey("youtube", "YOUTUBE_CLIENT_SECRETS_JSON_PATH", "p0", "local_path_reference"),
    CredentialKey("substack", "SUBSTACK_PUBLICATION_URL", "p2", "publication_url"),
    CredentialKey("substack", "SUBSTACK_EMAIL_OR_ACCOUNT_HINT", "p2", "account_hint"),
)

TOKEN_PATTERNS = (
    re.compile(r"^\d{6,}:[A-Za-z0-9_-]{20,}$"),
    re.compile(r"^ya29\.[A-Za-z0-9_-]{20,}$"),
    re.compile(r"^[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$"),
    re.compile(r"^[A-Za-z0-9._~+\-/=]{32,}$"),
)
INTEGER_LIKE = re.compile(r"^-?\d+$")
URN_LIKE = re.compile(r"^urn:[A-Za-z0-9:_-]+$")
URL_LIKE = re.compile(r"^https://[^\s]+$")
OAUTH_CALLBACK_CONTRACTS = {
    "x": "http://127.0.0.1:8765/oauth/x/callback",
    "linkedin": "http://127.0.0.1:8765/oauth/linkedin/callback",
    "meta": "http://127.0.0.1:8765/oauth/meta/callback",
    "tiktok": "http://127.0.0.1:8765/oauth/tiktok/callback",
    "youtube": "http://127.0.0.1:8765/oauth/youtube/callback",
}

def approved_key_names() -> tuple[str, ...]:
    return tuple(item.key_name for item in MATRIX)

def parse_env_text(text: str) -> dict[str, str | None]:
    values = {key: None for key in approved_key_names()}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        if key not in values:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values

def read_local_env(repo_root: Path) -> tuple[dict[str, str | None], list[str]]:
    merged = {key: None for key in approved_key_names()}
    sources: list[str] = []
    for name, label in ((".env", "repo_dotenv_redacted"), (".env.local", "repo_dotenv_local_redacted")):
        path = repo_root / name
        if not path.exists():
            continue
        parsed = parse_env_text(path.read_text(encoding="utf-8", errors="replace"))
        for key, value in parsed.items():
            if value is not None:
                merged[key] = value
        sources.append(label)
    return merged, sources

def merge_process_env(values: dict[str, str | None], env: Mapping[str, str] | None = None) -> dict[str, str | None]:
    source = os.environ if env is None else env
    merged = dict(values)
    for key in approved_key_names():
        if not merged.get(key) and source.get(key):
            merged[key] = source.get(key)
    return merged

def classify_shape(key: CredentialKey, value: str | None) -> str:
    if value is None:
        return "missing"
    stripped = value.strip()
    if not stripped:
        return "present_redacted_empty_or_whitespace"
    if key.expected_shape in {"telegram_bot_token", "oauth_access_token", "oauth_refresh_token", "page_access_token"}:
        return "present_redacted_token_like" if any(pattern.match(stripped) for pattern in TOKEN_PATTERNS) else "present_redacted_nonempty_nonclassifiable"
    if key.expected_shape in {"oauth_client_secret", "app_secret", "oauth_client_key"}:
        return "present_redacted_secret_or_key_like" if len(stripped) >= 8 else "present_redacted_nonempty_nonclassifiable"
    if key.expected_shape in {"channel_identifier", "chat_identifier", "user_identifier", "page_identifier", "account_identifier", "app_id"}:
        return "present_redacted_identifier_like" if INTEGER_LIKE.match(stripped) or len(stripped) >= 2 else "present_redacted_nonempty_nonclassifiable"
    if key.expected_shape == "urn":
        return "present_redacted_urn_like" if URN_LIKE.match(stripped) else "present_redacted_nonempty_nonclassifiable"
    if key.expected_shape == "publication_url":
        return "present_redacted_url_like" if URL_LIKE.match(stripped) else "present_redacted_nonempty_nonclassifiable"
    if key.expected_shape == "local_path_reference":
        return "present_redacted_local_path_reference"
    return "present_redacted_nonempty_nonclassifiable"

def row_blockers(key: CredentialKey, value: str | None) -> list[str]:
    blockers = ["runtime_live_ready_forbidden_in_setup_workbench"]
    if value is None or not value.strip():
        blockers.append("credential_missing")
    if key.key_name.endswith("SECRET") or key.key_name.endswith("TOKEN") or "SECRET" in key.key_name or "TOKEN" in key.key_name:
        blockers.append("manual_secret_storage_required")
    return blockers

def build_inventory(repo_root: str | Path = ".", include_process_env: bool = False, env: Mapping[str, str] | None = None) -> dict[str, object]:
    root = Path(repo_root)
    values, sources = read_local_env(root)
    if include_process_env:
        values = merge_process_env(values, env)
        sources.append("process_env_explicit_flag_redacted")
    rows = []
    for item in MATRIX:
        value = values.get(item.key_name)
        rows.append({"platform": item.platform, "key_name": item.key_name, "present": bool(value and value.strip()), "shape_class": classify_shape(item, value), "setup_priority": item.setup_priority, "live_ready": False, "blockers": row_blockers(item, value)})
    report: dict[str, object] = {"task_label": TASK_LABEL, "mode": "redacted_social_credential_inventory_only", "repo_env_sources_checked": sources or ["none_found_redacted"], "process_env_checked": include_process_env, "credential_values_printed": False, "token_snippets_printed": False, "secret_hashes_printed": False, "live_ready": False, "platform_count": len({item.platform for item in MATRIX}), "key_count": len(MATRIX), "oauth_callback_scaffold_only": True, "oauth_callbacks": OAUTH_CALLBACK_CONTRACTS, "rows": rows}
    assert_report_safe(report)
    return report

def assert_report_safe(report: object) -> None:
    text = json.dumps(report, sort_keys=True, ensure_ascii=False)
    if contains_secret_shaped_text(text):
        raise ValueError("secret_shaped_text_blocked_in_inventory_report")
    lowered = text.lower()
    forbidden = ("123456:", "ya29.", "access_token=", "refresh_token=", "client_secret=", "authorization:", "cookie:")
    if any(marker in lowered for marker in forbidden):
        raise ValueError("raw_secret_marker_blocked_in_inventory_report")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redacted social credential setup workbench.")
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--repo-root", default=".")
    inv.add_argument("--include-process-env", action="store_true")
    inv.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "inventory":
        report = build_inventory(args.repo_root, args.include_process_env)
        if args.json:
            print(json.dumps(report, sort_keys=True))
        else:
            for row in report["rows"]:  # type: ignore[index]
                print(f"{row['platform']} {row['key_name']} {row['shape_class']} live_ready=false")
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
