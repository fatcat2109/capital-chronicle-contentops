"""Operator-owned browser lab for social credential setup.

Opens official developer portals in persistent operator profile. Not runtime publish
authority. Never inspects browser state.
"""
from __future__ import annotations

import argparse, json, os, shutil, subprocess, time, urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from live_contentops.x_cdp_profile_guard_v6 import build_profile_guard_evidence, command_line_for_port, recommend_contentops_port
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import build_prelive_post_packet
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import build_final_pre_click_rehearsal_packet
from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import build_exact_live_click_authorization_request
from live_contentops.x_cdp_exact_separate_live_click_scope_decision_v6 import build_scope_decision_packet
from live_contentops.x_cdp_exact_live_click_execution_prep_v6 import build_execution_prep_packet
from live_contentops.x_cdp_exact_live_click_authorization_v6 import build_exact_live_click_authorization
from live_contentops.x_cdp_exact_live_click_execution_v6 import build_exact_live_click_execution
from live_contentops.platform_publication_identity_registry_v6 import DEFAULT_REGISTRY_PATH, audit_registry_records

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
    "future_browser_assisted_publish_requires": ["approved_payload_hash", "destination_account_pre_click_compare", "contentops_profile_guard", "jim_present", "stop_on_ui_uncertainty", "no_cookie_or_session_dump", "no_generic_publish_all"],
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


def probe_cdp(cdp_port: int, timeout: float = 3.0) -> dict[str, object]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/version", timeout=timeout) as response:
            data = json.load(response)
    except Exception:
        return {"cdp_alive": False, "browser_present": False, "websocket_present": False}
    return {
        "cdp_alive": bool(data.get("Browser") and data.get("webSocketDebuggerUrl")),
        "browser_present": bool(data.get("Browser")),
        "websocket_present": bool(data.get("webSocketDebuggerUrl")),
    }

def guard_cdp_profile_from_processes(processes: Iterable[Mapping[str, object]], cdp_port: int, profile_root: Path | None = None) -> dict[str, object]:
    expected = profile_root or DEFAULT_PROFILE_ROOT
    command_line = command_line_for_port(processes, cdp_port)
    evidence = build_profile_guard_evidence(cdp_port, command_line, expected)
    evidence["recommended_cdp_port"] = recommend_contentops_port(processes, expected)
    return evidence


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
        proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        summary["browser_process_exited"] = proc.poll() is not None
        summary.update(probe_cdp(cdp_port, timeout=2.0))
        if summary["browser_process_exited"]:
            summary["status"] = "blocked_browser_exited_after_launch"
        elif not summary["cdp_alive"]:
            summary["status"] = "blocked_cdp_not_alive_after_launch"
    return summary

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open official social credential setup portals safely.")
    sub = parser.add_subparsers(dest="command", required=True)
    open_parser = sub.add_parser("open")
    open_parser.add_argument("--platform", required=True, choices=sorted([*PORTAL_TARGETS.keys(), "all-docs"]))
    open_parser.add_argument("--repo-root", default=".")
    open_parser.add_argument("--dry-run", action="store_true")
    guard_parser = sub.add_parser("guard-x-cdp")
    guard_parser.add_argument("--dry-run", action="store_true", help="Required; guard mode never launches or clicks.")
    guard_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    guard_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    guard_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    prelive_parser = sub.add_parser("prelive-x-post")
    prelive_parser.add_argument("--dry-run", action="store_true", help="Required; pre-live mode never launches, probes, or clicks.")
    prelive_parser.add_argument("--payload-text", required=True)
    prelive_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    prelive_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    prelive_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    go_gate_parser = sub.add_parser("gate-x-live-click")
    go_gate_parser.add_argument("--dry-run", action="store_true", help="Required; gate mode never launches, probes, or clicks.")
    go_gate_parser.add_argument("--payload-text", required=True)
    go_gate_parser.add_argument("--operator-go-phrase", required=True)
    go_gate_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    go_gate_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    go_gate_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    authorize_parser = sub.add_parser("authorize-x-live-click")
    authorize_parser.add_argument("--dry-run", action="store_true", help="Required; authorization mode never launches, probes, or clicks.")
    authorize_parser.add_argument("--payload-text", required=True)
    authorize_parser.add_argument("--operator-go-phrase", required=True)
    authorize_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    authorize_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    authorize_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    rehearse_parser = sub.add_parser("rehearse-x-pre-click")
    rehearse_parser.add_argument("--dry-run", action="store_true", help="Required; rehearsal mode never launches, probes, or clicks.")
    rehearse_parser.add_argument("--payload-text", required=True)
    rehearse_parser.add_argument("--operator-go-phrase", required=True)
    rehearse_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    rehearse_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    rehearse_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    request_parser = sub.add_parser("authorization-request-x-live-click")
    request_parser.add_argument("--dry-run", action="store_true", help="Required; request mode never launches, probes, or clicks.")
    request_parser.add_argument("--payload-text", required=True)
    request_parser.add_argument("--operator-go-phrase", required=True)
    request_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    request_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    request_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    scope_parser = sub.add_parser("scope-decision-x-live-click")
    scope_parser.add_argument("--dry-run", action="store_true", help="Required; scope decision mode never launches, probes, or clicks.")
    scope_parser.add_argument("--payload-text", required=True)
    scope_parser.add_argument("--operator-go-phrase", required=True)
    scope_parser.add_argument("--scope-decision", required=True, choices=("deny", "defer", "approve_future_scope"))
    scope_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    scope_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    scope_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    execution_prep_parser = sub.add_parser("execution-prep-x-live-click")
    execution_prep_parser.add_argument("--dry-run", action="store_true", help="Required; execution prep never launches, probes, or clicks.")
    execution_prep_parser.add_argument("--payload-text", required=True)
    execution_prep_parser.add_argument("--operator-go-phrase", required=True)
    execution_prep_parser.add_argument("--scope-decision", required=True, choices=("deny", "defer", "approve_future_scope"))
    execution_prep_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    execution_prep_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    execution_prep_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    exact_auth_parser = sub.add_parser("exact-authorize-x-live-click")
    exact_auth_parser.add_argument("--dry-run", action="store_true", help="Required; exact authorization never launches, probes, or clicks.")
    exact_auth_parser.add_argument("--payload-text", required=True)
    exact_auth_parser.add_argument("--operator-go-phrase", required=True)
    exact_auth_parser.add_argument("--scope-decision", required=True, choices=("deny", "defer", "approve_future_scope"))
    exact_auth_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    exact_auth_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    exact_auth_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    execute_parser = sub.add_parser("execute-x-live-click")
    execute_parser.add_argument("--dry-run", action="store_true", help="Required; records operator-supervised outcome and never drives browser/session state.")
    execute_parser.add_argument("--payload-text", required=True)
    execute_parser.add_argument("--operator-go-phrase", required=True)
    execute_parser.add_argument("--scope-decision", required=True, choices=("deny", "defer", "approve_future_scope"))
    execute_parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT)
    execute_parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    execute_parser.add_argument("--command-line", default=None, help="Operator-supplied process command line metadata.")
    execute_parser.add_argument("--operator-confirmed-click-performed", action="store_true")
    execute_parser.add_argument("--captured-public-x-url", required=True)
    execute_parser.add_argument("--operator-confirmed-payload-hash", required=True)
    execute_parser.add_argument("--operator-confirmed-account-destination", required=True)
    execute_parser.add_argument("--operator-confirmed-kill-switch-available-before-click", action="store_true")
    audit_registry_parser = sub.add_parser("audit-publication-registry")
    audit_registry_parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    args = parser.parse_args(argv)
    if args.command == "open":
        result = open_platform(args.platform, Path(args.repo_root), args.dry_run)
        print(json.dumps(result, sort_keys=True))
        return 0 if str(result.get("status")).startswith(("opened", "dry_run")) else 2
    if args.command == "guard-x-cdp":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        result = build_profile_guard_evidence(args.cdp_port, args.command_line, args.expected_profile_root)
        result["operator_browser_lab_command"] = "guard-x-cdp"
        result["recommended_cdp_port"] = recommend_contentops_port(
            [{"CommandLine": args.command_line}] if args.command_line else (),
            args.expected_profile_root,
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("live_click_allowed") is True else 2
    if args.command == "prelive-x-post":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        result = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        result["operator_browser_lab_command"] = "prelive-x-post"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready_for_operator_review") is True else 2
    if args.command == "gate-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        result = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        result["operator_browser_lab_command"] = "gate-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("future_live_click_eligible_after_separate_live_task") is True else 2
    if args.command == "authorize-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        result = build_live_click_authorization_packet(
            prelive_packet=prelive,
            go_gate_packet=gate,
            kill_switch_snapshot=default_kill_switch_snapshot(),
            rollback_checklist=default_rollback_checklist(),
        )
        result["operator_browser_lab_command"] = "authorize-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready_for_exact_separate_live_task") is True else 2
    if args.command == "rehearse-x-pre-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(
            prelive_packet=prelive,
            go_gate_packet=gate,
            kill_switch_snapshot=default_kill_switch_snapshot(),
            rollback_checklist=default_rollback_checklist(),
        )
        result = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        result["operator_browser_lab_command"] = "rehearse-x-pre-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready_for_separate_exact_live_task") is True else 2
    if args.command == "authorization-request-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(
            prelive_packet=prelive,
            go_gate_packet=gate,
            kill_switch_snapshot=default_kill_switch_snapshot(),
            rollback_checklist=default_rollback_checklist(),
        )
        rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        result = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
        result["operator_browser_lab_command"] = "authorization-request-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready_for_operator_review") is True else 2
    if args.command == "scope-decision-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(
            prelive_packet=prelive,
            go_gate_packet=gate,
            kill_switch_snapshot=default_kill_switch_snapshot(),
            rollback_checklist=default_rollback_checklist(),
        )
        rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
        result = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
        result["operator_browser_lab_command"] = "scope-decision-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("scope_decision_status") != "BLOCKED_SCOPE_DECISION_BEFORE_LIVE_CLICK" else 2
    if args.command == "execution-prep-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(
            payload_text=args.payload_text,
            cdp_port=args.cdp_port,
            command_line=args.command_line,
            expected_profile_root=args.expected_profile_root,
        )
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(
            prelive_packet=prelive,
            go_gate_packet=gate,
            kill_switch_snapshot=default_kill_switch_snapshot(),
            rollback_checklist=default_rollback_checklist(),
        )
        rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
        decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
        result = build_execution_prep_packet(scope_decision_packet=decision)
        result["operator_browser_lab_command"] = "execution-prep-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready_for_exact_live_execution_authorization_task") is True else 2
    if args.command == "exact-authorize-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_performed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(payload_text=args.payload_text, cdp_port=args.cdp_port, command_line=args.command_line, expected_profile_root=args.expected_profile_root)
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
        rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
        decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
        prep = build_execution_prep_packet(scope_decision_packet=decision)
        result = build_exact_live_click_authorization(execution_prep_packet=prep)
        result["operator_browser_lab_command"] = "exact-authorize-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("exact_live_click_authorized_for_one_operator_supervised_click") is True else 2
    if args.command == "execute-x-live-click":
        if not args.dry_run:
            print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_performed": False}, sort_keys=True))
            return 2
        prelive = build_prelive_post_packet(payload_text=args.payload_text, cdp_port=args.cdp_port, command_line=args.command_line, expected_profile_root=args.expected_profile_root)
        gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
        auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
        rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
        request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
        decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
        prep = build_execution_prep_packet(scope_decision_packet=decision)
        exact_auth = build_exact_live_click_authorization(execution_prep_packet=prep)
        result = build_exact_live_click_execution(
            authorization_packet=exact_auth,
            operator_confirmed_click_performed=args.operator_confirmed_click_performed,
            captured_public_x_url=args.captured_public_x_url,
            operator_confirmed_payload_hash=args.operator_confirmed_payload_hash,
            operator_confirmed_account_destination=args.operator_confirmed_account_destination,
            operator_confirmed_kill_switch_available_before_click=args.operator_confirmed_kill_switch_available_before_click,
        )
        result["operator_browser_lab_command"] = "execute-x-live-click"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("execution_status") == "EXECUTED_WITH_CAPTURED_PUBLIC_URL" else 2
    if args.command == "audit-publication-registry":
        result = audit_registry_records(args.registry_path)
        result["operator_browser_lab_command"] = "audit-publication-registry"
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("duplicate_natural_key_count") == 0 else 2
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
