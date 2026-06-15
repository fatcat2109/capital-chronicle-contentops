"""Network-free tests for the 0174CP next-platform account-binding selection gate.

These tests assert the hard guarantees documented in the gate module:
  * no network / env imports are used at runtime (preview + write both offline),
  * the packet is deterministic and redaction-clean,
  * status cannot be ``pass`` without at least one official source,
  * the redaction scanner actually blocks token-like / id-like / handle leaks,
  * all live-behavior flags are False for every candidate,
  * preview-only does not write to disk; --write writes a deterministic file.
"""

import json
import os
import tempfile

from live_contentops import next_platform_account_binding_selection_gate as gate


def test_packet_builds_and_is_redaction_clean():
    packet = gate.build_selection_packet()
    violations = gate.scan_packet_for_leaks(packet)
    assert violations == [], f"unexpected redaction violations: {violations}"


def test_status_pass_requires_official_source():
    packet = gate.build_selection_packet()
    assert packet["official_source_count"] >= 1
    assert packet["status"] == "pass"
    assert packet["blocked_reasons"] == []


def test_recommended_platform_is_telegram_second_gate():
    packet = gate.build_selection_packet()
    assert packet["recommended_next_platform"] == gate.CANDIDATE_TELEGRAM_SECOND
    assert packet["next_task_label"].startswith("TASK_CONTENTOPS_0174CQ")


def test_all_candidates_have_live_flags_false():
    packet = gate.build_selection_packet()
    for name, cand in packet["candidates"].items():
        for flag in (
            "scheduler_enabled",
            "reply_dm_enabled",
            "metrics_fetch_enabled",
            "webhook_enabled",
            "scraping_enabled",
        ):
            assert cand[flag] is False, f"{name}.{flag} must be False"


def test_all_three_candidates_present_and_grounded():
    packet = gate.build_selection_packet()
    for name in (
        gate.CANDIDATE_X,
        gate.CANDIDATE_LINKEDIN,
        gate.CANDIDATE_TELEGRAM_SECOND,
    ):
        cand = packet["candidates"][name]
        assert cand["official_docs_checked"] is True
        assert len(cand["official_docs_sources"]) >= 1


def test_no_live_action_assertions_are_true():
    packet = gate.build_selection_packet()
    for key in (
        "no_live_call_performed",
        "no_credentials_read",
        "no_account_binding_performed",
        "no_oauth_flow_performed",
        "no_token_exchange_performed",
        "no_posting_performed",
        "no_scheduler_created",
        "no_webhook_created",
        "no_reply_dm_created",
        "no_metrics_fetched",
        "no_scraping_performed",
        "redaction_verified",
    ):
        assert packet[key] is True


def test_serialization_is_deterministic():
    p1 = gate.build_selection_packet()
    p2 = gate.build_selection_packet()
    s1 = gate.serialize_packet(p1)
    s2 = gate.serialize_packet(p2)
    assert s1 == s2
    assert s1.endswith("\n")
    # sorted keys => stable checksum
    assert gate.compute_packet_checksum(p1) == gate.compute_packet_checksum(p2)


def test_scanner_blocks_token_like_value():
    bad = {"x": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ab"}
    violations = gate.scan_packet_for_leaks(bad)
    assert any(v.startswith("secret_like_value") for v in violations)


def test_scanner_blocks_raw_handle():
    bad = {"x": "see @somechannel for details"}
    violations = gate.scan_packet_for_leaks(bad)
    assert any(v.startswith("raw_handle") for v in violations)


def test_scanner_blocks_long_digit_id():
    bad = {"x": "chat -1001234567890 target"}
    violations = gate.scan_packet_for_leaks(bad)
    assert any(v.startswith("long_digits_possible_id") for v in violations)


def test_scanner_blocks_telegram_bot_url():
    bad = {"x": "https://api.telegram.org/bot999999:tok/sendMessage"}
    violations = gate.scan_packet_for_leaks(bad)
    assert any(v.startswith("telegram_bot_url") for v in violations)


def test_scanner_blocks_forbidden_keys():
    for key in ("token", "chat_id", "client_secret", "raw_response"):
        violations = gate.scan_packet_for_leaks({key: "x"})
        assert f"forbidden_key:{key}" in violations


def test_scanner_allows_official_doc_urls():
    ok = {
        "url": "https://docs.x.com/x-api/posts/create-post",
        "url2": (
            "https://learn.microsoft.com/en-us/linkedin/marketing/"
            "community-management/shares/posts-api"
        ),
        "url3": "https://core.telegram.org/bots/api#sendmessage",
    }
    assert gate.scan_packet_for_leaks(ok) == []


def test_preview_mode_does_not_write(tmp_path):
    summary = gate.run_gate(write=False, repo_root=str(tmp_path))
    assert summary["status"] == "pass"
    assert summary["packet_written"] is False
    assert summary["network_performed"] is False
    assert summary["env_read_performed"] is False
    # nothing written to disk
    expected = tmp_path / gate.PACKET_REL_DIR / gate.PACKET_FILENAME
    assert not expected.exists()


def test_write_mode_persists_deterministic_packet(tmp_path):
    summary = gate.run_gate(write=True, repo_root=str(tmp_path))
    assert summary["status"] == "pass"
    assert summary["packet_written"] is True
    assert summary["redaction_scan_passed"] is True
    out = tmp_path / gate.PACKET_REL_DIR / gate.PACKET_FILENAME
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.endswith("\n")
    # file must be the exact deterministic serialization
    loaded = json.loads(text)
    assert gate.serialize_packet(loaded) == text
    # round-trip the written file through the scanner
    assert gate.scan_packet_for_leaks(loaded) == []


def test_gate_module_imports_no_network_libraries():
    # The module source must not import any network library.
    src_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "live_contentops",
        "next_platform_account_binding_selection_gate.py",
    )
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    for banned in ("import urllib", "import requests", "import httpx", "import socket"):
        assert banned not in src, f"network import found: {banned}"
