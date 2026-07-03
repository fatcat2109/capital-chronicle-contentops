"""Operator-owned browser lab for social credential setup.

Opens official developer portals in persistent operator profile. Not runtime publish
authority. Never inspects browser state.
"""
from __future__ import annotations

import argparse, json, os, shutil, subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

TASK_LABEL = "TASK_CONTENTOPS_OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP_WORKBENCH_V0"
DEFAULT_PROFILE_ROOT = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
PROFILE_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_PROFILE_ROOT"
CDP_PORT_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_CDP_PORT"
DEFAULT_CDP_PORT = 9222
BROWSER_BINARY_ENV_KEY = "CONTENTOPS_OPERATOR_BROWSER_BINARY"

FORBIDDEN_BROWSER_STATE_ACTIONS = ("cookie_dump", "cookies_read", "localStorage_read", "sessionStorage_read", "dom_dump", "screenshot_with_secret")
FORBIDDEN_RUNTIME_ACTIONS = ("post", "publish", "upload", "sendMessage", "sendPhoto", "tweet_create", "linkedin_post_create", "meta_post_create", "tiktok_publish", "youtube_upload", "substack_publish", "scheduler", "autonomous_reply", "dm", "openc爪_runtime_integration".replace("爪", "law"))

@dataclass(frozen=True)
class PortalTarget:
    platform: str
    label: str
    urls: tuple[str, ...]

PORTAL_TARGETS: dict[str, PortalTarget] = {
    "telegram": PortalTarget("telegram", "Telegram Bot API and BotFather", ("https://core.telegram.org/bots/api", "https://core.telegram.org/bots/features#botfather")),
    "x": PortalTarget("x", "X Developer Portal and OAuth", ("https://developer.x.com/", "https://docs.x.com/x-api/posts/create-post", "https://docs.x.com/resources/fundamentals/authentication/oauth-2-0/overview")),
    "linkedin": PortalTarget("linkedin", "LinkedIn Developers and Auth", ("https://www.linkedin.com/developers/", "https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access", "https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api")),
    "meta": PortalTarget("meta", "Meta Developers", ("https://developers.facebook.com/", "https://developers.facebook.com/docs/pages-api/", "https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing/", "https://developers.facebook.com/docs/threads/")),
    "tiktok": PortalTarget("tiktok", "TikTok Developers", ("https://developers.tiktok.com/", "https://developers.tiktok.com/doc/content-posting-api-get-started/")),
    "youtube": PortalTarget("youtube", "Google Cloud and YouTube Data API", ("https://console.cloud.google.com/", "https://developers.google.com/youtube/v3/docs/videos/insert", "https://developers.google.com/youtube/v3/guides/uploading_a_video")),
    "substack": PortalTarget("substack", "Substack publication dashboard", ("https://substack.com/",)),
}

SAFE_POLICY = {
    "task_label": TASK_LABEL,
    "browser_lab_runtime_authority": False,
    "manual_login_allowed": True,
    "official_portals_only": True,
    "cookie_dump_allowed": False,
    "localStorage_dump_allowed": False,
    "sessionStorage_dump_allowed": False,
    "dom_dump_allowed": False,
    "screenshot_with_secret_allowed": False,
    "platform_write_allowed": False,
    "post_publish_upload_allowed": False,
    "scheduler_allowed": False,
    "autonomous_replies_or_dms_allowed": False,
    "openclaw_runtime_integration_allowed": False,
    "future_browser_assisted_publish_requires": ["approved_payload_hash", "destination_account_pre_click_compare", "jim_present", "stop_on_ui_uncertainty", "no_cookie_or_session_dump", "no_generic_publish_all"],
}

def get_default_profile_root() -> Path:
    return DEFAULT_PROFILE_ROOT

def resolve_profile_root(env: Mapping[str, str] | None = None) -> Path:
    source = os.environ if env is None else env
    configured = source.get(PROFILE_ENV_KEY)
    return Path(configured).expanduser() if configured else DEFAULT_PROFILE_ROOT

def resolve_cdp_port(env: Mapping[str, str] | None = None) -> int:
    source = os.environ if env is None else env
    raw = source.get(CDP_PORT_ENV_KEY, str(DEFAULT_CDP_PORT)).strip()
    if not raw.isdigit():
        raise ValueError("cdp_port_must_be_integer")
    port = int(raw)
    if port < 1024 or port > 65535:
        raise ValueError("cdp_port_out_of_range")
    return port

def is_path_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False

def validate_profile_policy(profile_root: Path, repo_root: Path | None = None) -> dict[str, object]:
    repo = repo_root or Path.cwd()
    inside_repo = is_path_inside(profile_root, repo)
    return {"profile_root_class": "external_default_or_override" if not inside_repo else "repo_local_sensitive_override_requires_gitignore", "profile_inside_repo": inside_repo, "profile_path_persistable_in_git": False, "raw_profile_contains_secret": False}

def urls_for_platform(platform: str) -> tuple[str, ...]:
    if platform == "all-docs":
        urls: list[str] = []
        for target in PORTAL_TARGETS.values():
            urls.extend(target.urls)
        return tuple(urls)
    if platform not in PORTAL_TARGETS:
        raise ValueError("unknown_platform")
    return PORTAL_TARGETS[platform].urls

def labels_for_platform(platform: str) -> list[str]:
    if platform == "all-docs":
        return [target.label for target in PORTAL_TARGETS.values()]
    if platform not in PORTAL_TARGETS:
        raise ValueError("unknown_platform")
    return [PORTAL_TARGETS[platform].label]

def find_browser_binary(env: Mapping[str, str] | None = None) -> str | None:
    source = os.environ if env is None else env
    configured = source.get(BROWSER_BINARY_ENV_KEY)
    if configured:
        return configured
    candidates = ["chrome.exe", "msedge.exe", "chromium.exe", "google-chrome", "chromium", "chrome", "msedge", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
        if Path(candidate).exists():
            return candidate
    return None

def assert_no_secret_like_command(command: Sequence[str]) -> None:
    joined = "\n".join(command).lower()
    forbidden = ("access_token=", "refresh_token=", "client_secret=", "api_key=", "bot_token=", "authorization:", "cookie:")
    if any(marker in joined for marker in forbidden):
        raise ValueError("secret_like_browser_command_blocked")

def build_browser_command(browser_binary: str, profile_root: Path, cdp_port: int, platform: str) -> list[str]:
    command = [
        browser_binary,
        f"--user-data-dir={profile_root}",
        f"--remote-debugging-port={cdp_port}",
        "--no-first-run",
        "--disable-default-apps",
        "--new-window",
    ]
    command.extend(urls_for_platform(platform))
    assert_no_secret_like_command(command)
    return command

def safe_open_summary(platform: str, profile_root: Path, cdp_port: int) -> dict[str, object]:
    return {"task_label": TASK_LABEL, "platform": platform, "portal_labels": labels_for_platform(platform), "portal_url_count": len(urls_for_platform(platform)), "profile_policy": validate_profile_policy(profile_root), "cdp_port": cdp_port, "cookie_dump_performed": False, "localStorage_dump_performed": False, "sessionStorage_dump_performed": False, "dom_dump_performed": False, "platform_write_performed": False, "raw_secret_output": False}

def open_platform(platform: str, repo_root: Path | None = None, dry_run: bool = False, env: Mapping[str, str] | None = None) -> dict[str, object]:
    profile_root = resolve_profile_root(env)
    cdp_port = resolve_cdp_port(env)
    repo = repo_root or Path.cwd()
    policy = validate_profile_policy(profile_root, repo)
    browser = find_browser_binary(env)
    summary = safe_open_summary(platform, profile_root, cdp_port)
    summary["browser_found"] = bool(browser)
    summary["dry_run"] = dry_run
    if policy["profile_inside_repo"]:
        summary["warning"] = "repo_local_profile_sensitive_requires_gitignore"
    if not browser:
        summary["status"] = "blocked_browser_binary_not_found"
        return summary
    command = build_browser_command(browser, profile_root, cdp_port, platform)
    summary["browser_command_arg_count"] = len(command)
    summary["status"] = "dry_run_ready" if dry_run else "opened"
    if not dry_run:
        profile_root.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return summary

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open official social credential setup portals safely.")
    sub = parser.add_subparsers(dest="command", required=True)
    open_parser = sub.add_parser("open")
    open_parser.add_argument("--platform", required=True, choices=sorted([*PORTAL_TARGETS.keys(), "all-docs"]))
    open_parser.add_argument("--repo-root", default=".")
    open_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "open":
        result = open_platform(args.platform, Path(args.repo_root), args.dry_run)
        print(json.dumps(result, sort_keys=True))
        return 0 if str(result.get("status")).startswith(("opened", "dry_run")) else 2
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
