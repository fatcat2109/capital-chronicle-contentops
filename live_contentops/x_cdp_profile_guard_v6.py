"""Reusable X CDP profile/port guard for supervised browser-assisted publishing.

Never reads cookies, localStorage, sessionStorage, tokens, headers, DOM, or raw
browser profile files. It only classifies operator-supplied/process command-line
metadata before any live click.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_PROFILE_GUARD_REUSABLE_OPERATOR_COMMAND_V0"
DEFAULT_EXPECTED_PROFILE_ROOT = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
ANTIGRAVITY_PROFILE_MARKERS = (
    r".gemini\antigravity-browser-profile",
    r".gemini/antigravity-browser-profile",
)
BUILT_IN_PROFILE_MARKERS = (
    r"\user data\default",
    r"\user data\profile ",
    r"\chrome\user data\default",
    r"\chrome\user data\profile ",
    r"\edge\user data\default",
    r"\edge\user data\profile ",
)
SECRET_EVIDENCE_FLAGS = {
    "cookie_read_performed": False,
    "local_storage_read_performed": False,
    "session_storage_read_performed": False,
    "token_or_header_read_performed": False,
    "dom_read_performed": False,
    "raw_secret_output": False,
    "browser_or_cdp_probe_performed": False,
    "live_click_performed": False,
}


def _norm(value: str | Path) -> str:
    return str(value).strip().strip('"').replace("/", "\\").lower()


def _port_markers(port: int) -> tuple[str, ...]:
    return (f"--remote-debugging-port={port}", f"remote-debugging-port={port}")


def command_line_for_port(processes: Iterable[Mapping[str, object]], port: int) -> str | None:
    for proc in processes:
        command = str(proc.get("CommandLine") or proc.get("command_line") or "")
        if any(marker in command for marker in _port_markers(port)):
            return command
    return None


def extract_user_data_dir(command_line: str | None) -> str | None:
    if not command_line:
        return None
    match = re.search(r"--user-data-dir(?:=|\s+)(\"[^\"]+\"|'[^']+'|.*?)(?=\s+--|$)", command_line, re.IGNORECASE)
    return match.group(1).strip('"\'') if match else None


def _is_built_in_profile(command: str, profile: str | None, expected: str) -> bool:
    haystack = " ".join(part for part in (command, profile or "") if part)
    if expected and expected in haystack:
        return False
    return any(marker in haystack for marker in BUILT_IN_PROFILE_MARKERS)


def classify_cdp_profile(command_line: str | None, expected_profile_root: str | Path) -> str:
    if not command_line:
        return "cdp_unavailable_blocked"
    command = _norm(command_line)
    expected = _norm(expected_profile_root)
    profile = extract_user_data_dir(command_line)
    normalized_profile = _norm(profile) if profile else None
    if any(_norm(marker) in command for marker in ANTIGRAVITY_PROFILE_MARKERS):
        return "antigravity_profile_blocked"
    if normalized_profile and expected in normalized_profile:
        return "contentops_profile_ok"
    if expected in command:
        return "contentops_profile_ok"
    if _is_built_in_profile(command, normalized_profile, expected):
        return "builtin_browser_profile_blocked"
    return "unknown_profile_blocked"


def live_click_allowed_for_status(status: str) -> bool:
    return status == "contentops_profile_ok"


def build_profile_guard_evidence(port: int, command_line: str | None, expected_profile_root: str | Path) -> dict[str, object]:
    status = classify_cdp_profile(command_line, expected_profile_root)
    return {
        "task_label": TASK_LABEL,
        "cdp_port": port,
        "expected_profile_root": str(expected_profile_root),
        "observed_user_data_dir": extract_user_data_dir(command_line),
        "command_line_present": bool(command_line),
        "profile_guard_status": status,
        "live_click_allowed": live_click_allowed_for_status(status),
        "blocked_before_live_click": not live_click_allowed_for_status(status),
        **SECRET_EVIDENCE_FLAGS,
    }


def recommend_contentops_port(
    processes: Iterable[Mapping[str, object]],
    expected_profile_root: str | Path,
    preferred_ports: Iterable[int] = (9222, 9223, 9224, 9225),
) -> int | None:
    process_list = list(processes)
    for port in preferred_ports:
        command_line = command_line_for_port(process_list, port)
        status = classify_cdp_profile(command_line, expected_profile_root) if command_line else "free_port"
        if status in {"free_port", "contentops_profile_ok"}:
            return port
    return None


def build_guard_report(
    *,
    cdp_port: int,
    command_line: str | None,
    expected_profile_root: str | Path = DEFAULT_EXPECTED_PROFILE_ROOT,
    processes: Iterable[Mapping[str, object]] = (),
    preferred_ports: Iterable[int] = (9222, 9223, 9224, 9225),
) -> dict[str, object]:
    process_list = list(processes)
    if command_line is None:
        command_line = command_line_for_port(process_list, cdp_port)
    evidence = build_profile_guard_evidence(cdp_port, command_line, expected_profile_root)
    evidence.update(
        {
            "operator_command": "x_cdp_profile_guard_v6",
            "dry_run_only": True,
            "recommended_cdp_port": recommend_contentops_port(process_list, expected_profile_root, preferred_ports),
            "preferred_ports": list(preferred_ports),
            "process_metadata_source": "operator_supplied_or_fixture",
            "go_phrase_required_for_future_live_click": True,
        }
    )
    return evidence


def build_fixture_evidence_bundle() -> dict[str, object]:
    expected = DEFAULT_EXPECTED_PROFILE_ROOT
    cases = {
        "approved_contentops_profile": build_guard_report(
            cdp_port=9223,
            command_line=rf'"C:\Program Files\Microsoft\Edge\Application\msedge.exe" --user-data-dir="{expected}" --remote-debugging-port=9223',
        ),
        "antigravity_profile": build_guard_report(
            cdp_port=9222,
            command_line=r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile',
            processes=[{"CommandLine": r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"}],
        ),
        "builtin_browser_profile": build_guard_report(
            cdp_port=9222,
            command_line=r'"C:\Program Files\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\AppData\Local\Microsoft\Edge\User Data\Default',
        ),
        "unknown_profile": build_guard_report(
            cdp_port=9222,
            command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\tmp\other-profile",
        ),
        "cdp_unavailable": build_guard_report(cdp_port=9222, command_line=None),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_profile_guard_reusable_operator_command_evidence_v0",
        "expected_profile_root": str(expected),
        "case_count": len(cases),
        "cases": cases,
        "all_unsafe_cases_blocked": all(
            case["blocked_before_live_click"] for name, case in cases.items() if name != "approved_contentops_profile"
        ),
        "approved_case_allows_click": cases["approved_contentops_profile"]["live_click_allowed"],
        "safety_boundary": SECRET_EVIDENCE_FLAGS,
        "live_action_performed": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run X CDP profile guard report. Does not probe browsers or read secrets.")
    parser.add_argument("--dry-run", action="store_true", help="Required acknowledgement that this command is evidence-only.")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_EXPECTED_PROFILE_ROOT)
    parser.add_argument("--command-line", default=None, help="Operator-supplied process command line fixture/metadata.")
    parser.add_argument("--fixture-bundle", action="store_true", help="Emit deterministic local fixture evidence bundle.")
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
        return 2
    result = build_fixture_evidence_bundle() if args.fixture_bundle else build_guard_report(
        cdp_port=args.cdp_port,
        command_line=args.command_line,
        expected_profile_root=args.expected_profile_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("live_click_allowed") is True or args.fixture_bundle else 2


if __name__ == "__main__":
    raise SystemExit(main())
