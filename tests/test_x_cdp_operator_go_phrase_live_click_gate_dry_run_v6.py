import contextlib
import io
import json

from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import (
    EXPECTED_GO_PHRASE,
    FALSE_SAFETY_FLAGS,
    PASS_STATUS,
    build_fixture_evidence_bundle,
    build_go_phrase_gate_packet,
    expected_go_phrase_hash,
    main,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import build_prelive_post_packet

VALID_PAYLOAD = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
APPROVED_CMD = r'msedge.exe --remote-debugging-port=9223 --user-data-dir="A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"'


def _approved_prelive():
    return build_prelive_post_packet(payload_text=VALID_PAYLOAD, cdp_port=9223, command_line=APPROVED_CMD)


def _run_cli(args: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(args)
    return code, json.loads(stdout.getvalue())


def test_exact_phrase_and_valid_prelive_packet_ready_for_separate_live_task():
    packet = build_go_phrase_gate_packet(prelive_packet=_approved_prelive(), operator_go_phrase=EXPECTED_GO_PHRASE)
    assert packet["go_packet_status"] == PASS_STATUS
    assert packet["future_live_click_eligible_after_separate_live_task"] is True
    assert packet["live_click_allowed"] is False
    assert packet["blocked_before_live_click"] is True
    assert packet["raw_go_phrase_stored"] is False
    assert packet["expected_go_phrase_hash"] == expected_go_phrase_hash()


def test_phrase_mismatch_blocks_without_raw_phrase_storage():
    packet = build_go_phrase_gate_packet(prelive_packet=_approved_prelive(), operator_go_phrase="not approved")
    assert packet["future_live_click_eligible_after_separate_live_task"] is False
    assert "go_phrase_exact_match" in packet["blocked_reasons"]
    encoded = json.dumps(packet)
    assert "not approved" not in encoded
    assert EXPECTED_GO_PHRASE not in encoded


def test_packet_id_payload_hash_profile_and_registry_mismatches_block():
    approved = _approved_prelive()
    packet_id = build_go_phrase_gate_packet(prelive_packet=dict(approved, prelive_packet_id="x_prelive_bad"), operator_go_phrase=EXPECTED_GO_PHRASE)
    payload_hash = build_go_phrase_gate_packet(prelive_packet=dict(approved, payload_hash="0" * 64), operator_go_phrase=EXPECTED_GO_PHRASE)
    blocked_profile = build_go_phrase_gate_packet(
        prelive_packet=build_prelive_post_packet(
            payload_text=VALID_PAYLOAD,
            command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile",
        ),
        operator_go_phrase=EXPECTED_GO_PHRASE,
    )
    registry = dict(approved["registry_identity_expectation"], account_handle_expected="WrongHandle")
    registry_mismatch = build_go_phrase_gate_packet(prelive_packet=dict(approved, registry_identity_expectation=registry), operator_go_phrase=EXPECTED_GO_PHRASE)
    assert "prelive_packet_id_recomputed_match" in packet_id["blocked_reasons"]
    assert "payload_hash_recomputed_match" in payload_hash["blocked_reasons"]
    assert "profile_guard_status_match" in blocked_profile["blocked_reasons"]
    assert "registry_account_handle_match" in registry_mismatch["blocked_reasons"]


def test_safety_flags_never_claim_live_or_secret_actions():
    packet = build_go_phrase_gate_packet(prelive_packet=_approved_prelive(), operator_go_phrase=EXPECTED_GO_PHRASE)
    for key, value in FALSE_SAFETY_FLAGS.items():
        assert packet[key] is value
    assert packet["publication_registry_record_appended"] is False
    assert packet["live_click_performed"] is False


def test_fixture_bundle_covers_approved_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["case_count"] == 6
    assert bundle["approved_case_future_eligible"] is True
    assert bundle["all_cases_blocked_before_click"] is True
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    assert bundle["live_action_performed"] is False


def test_cli_requires_dry_run_and_fixture_bundle_succeeds():
    code, payload = _run_cli(["--operator-go-phrase", EXPECTED_GO_PHRASE, "--payload-text", VALID_PAYLOAD])
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    code, payload = _run_cli(["--dry-run", "--fixture-bundle"])
    assert code == 0
    assert payload["approved_case_future_eligible"] is True


def test_cli_builds_prelive_packet_from_fixture_args():
    code, payload = _run_cli([
        "--dry-run",
        "--payload-text",
        VALID_PAYLOAD,
        "--operator-go-phrase",
        EXPECTED_GO_PHRASE,
        "--cdp-port",
        "9223",
        "--command-line",
        APPROVED_CMD,
    ])
    assert code == 0
    assert payload["future_live_click_eligible_after_separate_live_task"] is True
    assert payload["live_click_allowed"] is False
