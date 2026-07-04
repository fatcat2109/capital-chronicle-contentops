import contextlib
import io
import json
from pathlib import Path

from live_contentops.x_cdp_profile_guard_v6 import (
    build_fixture_evidence_bundle,
    build_guard_report,
    build_profile_guard_evidence,
    classify_cdp_profile,
    command_line_for_port,
    extract_user_data_dir,
    main,
    recommend_contentops_port,
)

EXPECTED = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")


def _run_cli(args: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(args)
    return code, json.loads(stdout.getvalue())


def test_accepts_standard_contentops_profile():
    cmd = rf'"C:\Program Files\Microsoft\Edge\Application\msedge.exe" --user-data-dir="{EXPECTED}" --remote-debugging-port=9223'
    assert classify_cdp_profile(cmd, EXPECTED) == "contentops_profile_ok"
    evidence = build_profile_guard_evidence(9223, cmd, EXPECTED)
    assert evidence["live_click_allowed"] is True
    assert evidence["blocked_before_live_click"] is False
    assert evidence["observed_user_data_dir"] == str(EXPECTED)


def test_blocks_antigravity_profile_before_live_click():
    cmd = r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile'
    evidence = build_profile_guard_evidence(9222, cmd, EXPECTED)
    assert evidence["profile_guard_status"] == "antigravity_profile_blocked"
    assert evidence["live_click_allowed"] is False
    assert evidence["blocked_before_live_click"] is True


def test_blocks_builtin_browser_profile_before_live_click():
    cmd = r'"C:\Program Files\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\AppData\Local\Microsoft\Edge\User Data\Default'
    assert classify_cdp_profile(cmd, EXPECTED) == "builtin_browser_profile_blocked"


def test_unknown_profile_blocks():
    cmd = r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\tmp\other-profile"
    assert classify_cdp_profile(cmd, EXPECTED) == "unknown_profile_blocked"


def test_unavailable_cdp_metadata_blocks():
    evidence = build_profile_guard_evidence(9222, None, EXPECTED)
    assert evidence["profile_guard_status"] == "cdp_unavailable_blocked"
    assert evidence["live_click_allowed"] is False


def test_recommends_free_port_when_9222_is_antigravity():
    processes = [{"CommandLine": r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"}]
    assert recommend_contentops_port(processes, EXPECTED, (9222, 9223)) == 9223


def test_recommends_existing_contentops_port():
    processes = [{"CommandLine": rf"msedge.exe --remote-debugging-port=9223 --user-data-dir={EXPECTED}"}]
    assert recommend_contentops_port(processes, EXPECTED, (9222, 9223)) == 9222
    assert recommend_contentops_port(processes, EXPECTED, (9223, 9224)) == 9223


def test_command_line_for_port_finds_matching_process():
    processes = [{"CommandLine": "msedge.exe --remote-debugging-port=9223"}]
    assert command_line_for_port(processes, 9223) == "msedge.exe --remote-debugging-port=9223"


def test_extract_user_data_dir_handles_quoted_and_unquoted_values():
    assert extract_user_data_dir(r'edge.exe --user-data-dir="C:\profiles\contentops"') == r"C:\profiles\contentops"
    assert extract_user_data_dir(r"edge.exe --user-data-dir C:\profiles\contentops") == r"C:\profiles\contentops"


def test_guard_report_is_dry_run_only_and_recommends_port():
    report = build_guard_report(
        cdp_port=9222,
        command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\tmp\other-profile",
        expected_profile_root=EXPECTED,
    )
    assert report["dry_run_only"] is True
    assert report["live_click_allowed"] is False
    assert report["blocked_before_live_click"] is True
    assert report["go_phrase_required_for_future_live_click"] is True


def test_evidence_never_claims_secret_reads():
    evidence = build_profile_guard_evidence(9222, None, EXPECTED)
    assert evidence["cookie_read_performed"] is False
    assert evidence["local_storage_read_performed"] is False
    assert evidence["session_storage_read_performed"] is False
    assert evidence["token_or_header_read_performed"] is False
    assert evidence["dom_read_performed"] is False
    assert evidence["raw_secret_output"] is False
    assert evidence["browser_or_cdp_probe_performed"] is False
    assert evidence["live_click_performed"] is False


def test_cli_requires_dry_run_flag():
    code, payload = _run_cli(["--cdp-port", "9222"])
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_cli_blocks_antigravity_with_nonzero_exit():
    code, payload = _run_cli([
        "--dry-run",
        "--cdp-port",
        "9222",
        "--command-line",
        r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile",
    ])
    assert code == 2
    assert payload["profile_guard_status"] == "antigravity_profile_blocked"
    assert payload["blocked_before_live_click"] is True


def test_cli_allows_only_contentops_profile_fixture():
    code, payload = _run_cli([
        "--dry-run",
        "--cdp-port",
        "9223",
        "--command-line",
        rf"msedge.exe --remote-debugging-port=9223 --user-data-dir={EXPECTED}",
    ])
    assert code == 0
    assert payload["profile_guard_status"] == "contentops_profile_ok"
    assert payload["live_click_allowed"] is True


def test_fixture_bundle_covers_safe_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["case_count"] == 5
    assert bundle["approved_case_allows_click"] is True
    assert bundle["all_unsafe_cases_blocked"] is True
    assert bundle["live_action_performed"] is False
    assert bundle["cases"]["builtin_browser_profile"]["profile_guard_status"] == "builtin_browser_profile_blocked"
