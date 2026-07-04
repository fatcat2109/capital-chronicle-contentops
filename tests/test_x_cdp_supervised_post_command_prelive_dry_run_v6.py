import contextlib
import io
import json
from pathlib import Path

from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import (
    FALSE_SAFETY_FLAGS,
    X_TEXT_LIMIT,
    build_fixture_evidence_bundle,
    build_prelive_post_packet,
    main,
    stable_payload_hash,
)

EXPECTED = Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main")
VALID_PAYLOAD = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
APPROVED_CMD = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{EXPECTED}"'


def _run_cli(args: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(args)
    return code, json.loads(stdout.getvalue())


def test_valid_payload_and_contentops_profile_ready_for_operator_review():
    packet = build_prelive_post_packet(payload_text=VALID_PAYLOAD, cdp_port=9223, command_line=APPROVED_CMD)
    assert packet["prelive_status"] == "PRELIVE_X_POST_READY_FOR_OPERATOR_REVIEW"
    assert packet["ready_for_operator_review"] is True
    assert packet["payload_hash"] == stable_payload_hash(VALID_PAYLOAD)
    assert packet["profile_guard_report"]["profile_guard_status"] == "contentops_profile_ok"
    assert packet["registry_identity_expectation"]["registry_append_allowed_now"] is False
    assert packet["live_click_allowed"] is False
    assert packet["live_click_allowed_after_future_go_phrase_only"] is True


def test_antigravity_profile_blocks_before_click():
    packet = build_prelive_post_packet(
        payload_text=VALID_PAYLOAD,
        command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile",
    )
    assert packet["prelive_status"] == "BLOCKED_PRELIVE_X_POST"
    assert packet["blocked_reason"] == "profile_guard_not_ready:antigravity_profile_blocked"
    assert packet["blocked_before_live_click"] is True
    assert packet["live_click_performed"] is False


def test_builtin_unknown_and_unavailable_profiles_block():
    builtin = build_prelive_post_packet(
        payload_text=VALID_PAYLOAD,
        command_line=r"msedge.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\AppData\Local\Microsoft\Edge\User Data\Default",
    )
    unknown = build_prelive_post_packet(payload_text=VALID_PAYLOAD, command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\tmp\other-profile")
    unavailable = build_prelive_post_packet(payload_text=VALID_PAYLOAD, command_line=None)
    assert builtin["blocked_reason"] == "profile_guard_not_ready:builtin_browser_profile_blocked"
    assert unknown["blocked_reason"] == "profile_guard_not_ready:unknown_profile_blocked"
    assert unavailable["blocked_reason"] == "profile_guard_not_ready:cdp_unavailable_blocked"


def test_payload_validation_blocks_empty_overlength_secret_and_advice():
    assert build_prelive_post_packet(payload_text="   ")["blocked_reason"] == "payload_text_required"
    assert build_prelive_post_packet(payload_text="x" * (X_TEXT_LIMIT + 1))["blocked_reason"] == "payload_text_over_x_limit"
    secret_packet = build_prelive_post_packet(payload_text="bearer abcdefghijklmnop")
    assert secret_packet["blocked_reason"] == "forbidden_secret_or_session_material"
    assert secret_packet["payload_text"] == "[redacted_forbidden_payload]"
    assert build_prelive_post_packet(payload_text="This is not a buy instruction")["blocked_reason"] == "forbidden_financial_advice:buy"


def test_parent_public_url_must_be_x_status_url():
    packet = build_prelive_post_packet(
        payload_text=VALID_PAYLOAD,
        cdp_port=9223,
        command_line=APPROVED_CMD,
        expected_parent_public_url="https://example.com/not-x",
    )
    assert packet["blocked_reason"] == "expected_parent_public_url_must_be_x_status_url"


def test_evidence_never_claims_live_or_secret_actions():
    packet = build_prelive_post_packet(payload_text=VALID_PAYLOAD, cdp_port=9223, command_line=APPROVED_CMD)
    for key, value in FALSE_SAFETY_FLAGS.items():
        assert packet[key] is value
    assert packet["browser_or_cdp_probe_performed"] is False
    assert packet["publication_registry_record_appended"] is False


def test_fixture_bundle_covers_ready_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["case_count"] == 7
    assert bundle["approved_case_ready"] is True
    assert bundle["all_blocked_cases_blocked_before_click"] is True
    assert bundle["live_action_performed"] is False


def test_cli_requires_dry_run_flag():
    code, payload = _run_cli(["--payload-text", VALID_PAYLOAD])
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_cli_returns_ready_for_approved_fixture():
    code, payload = _run_cli([
        "--dry-run",
        "--payload-text",
        VALID_PAYLOAD,
        "--cdp-port",
        "9223",
        "--command-line",
        APPROVED_CMD,
    ])
    assert code == 0
    assert payload["ready_for_operator_review"] is True


def test_cli_fixture_bundle_succeeds():
    code, payload = _run_cli(["--dry-run", "--fixture-bundle"])
    assert code == 0
    assert payload["approved_case_ready"] is True
