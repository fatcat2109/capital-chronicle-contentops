"""Tests for the 0174EC social credential handle + redaction boundary.

These tests prove the module is deterministic, stdlib-only, secret-free, and
fail-closed, and that:
  * the static import surface is an exact stdlib allow-list (hashlib, json, os,
    re) with no requests/httpx/aiohttp/socket/ssl/http server, no
    selenium/playwright, no dotenv/keyring/sqlite/getpass,
  * importing the module performs NO network, NO env/.env/keyring/browser/
    credential-file read, NO OAuth, and NO file write,
  * every platform credential profile forbids value/hash/fingerprint/prefix/
    suffix, disables env/dotenv/keyring/browser reads, disables live hydration,
    and supports a fake provider,
  * the deterministic handle id is stable and excludes secret inputs,
  * the fake provider simulates all required cases without network/env/secret,
  * configured_symbolic validates only as a symbolic readiness candidate (never
    enabling live hydration), and every other presence class blocks,
  * forbidden values fail closed,
  * operator_go never enables live hydration,
  * the packet + doc are leak-free, and writing touches only the 0174EC dir,
  * each 0174EB binding platform has a 0174EC credential profile.
"""

import ast
import json
import os

import pytest

from live_contentops import social_credential_handle_boundary as model
from live_contentops import social_account_binding_model as binding_model


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "social_credential_handle_boundary.py")


ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re"}
FORBIDDEN_IMPORT_ROOTS = {
    "requests", "httpx", "aiohttp", "socket", "socketserver", "ssl",
    "asyncio", "selectors", "http", "urllib", "wsgiref", "webbrowser",
    "subprocess", "dotenv", "ftplib", "smtplib", "multiprocessing",
    "threading", "configparser", "keyring", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve", "selenium",
    "playwright", "getpass",
}


def _module_imports():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
    return roots


# --------------------------------------------------------------------------- #
# Import surface
# --------------------------------------------------------------------------- #
def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, (
        f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}")


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_no_network_or_http_client_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("requests.", "httpx.", "aiohttp.", "urllib.", "socket.",
              "import requests", "import httpx", "import aiohttp",
              "urlopen", "http.client", "webbrowser"):
        assert s not in src, f"forbidden network string present: {s}"


def test_no_env_credential_access_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("os.environ", "os.getenv", "getenv(", "load_dotenv",
              "dotenv_values", "keyring.get", "keyring.set", "secretstorage.",
              "netrc(", "configparser.", "ConfigParser", "browser_cookie",
              "sqlite3.", "getpass", "open(\".env", ".env.local"):
        assert s not in src, f"forbidden credential/env access string: {s}"


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
EXPECTED_PLATFORMS = {
    "telegram", "discord", "mastodon", "bluesky", "reddit", "x", "linkedin",
    "tiktok", "youtube", "facebook", "instagram", "threads", "substack",
    "medium",
}


def test_all_expected_platforms_present():
    assert EXPECTED_PLATFORMS <= set(model.SUPPORTED_PLATFORMS)


def test_every_profile_forbids_value_hash_fingerprint_prefix_suffix():
    for pid in model.SUPPORTED_PLATFORMS:
        prof = model.get_profile(pid)
        assert prof["credential_value_allowed_in_artifacts"] is False
        assert prof["credential_hash_allowed"] is False
        assert prof["credential_fingerprint_allowed"] is False
        assert prof["credential_prefix_suffix_allowed"] is False


def test_every_profile_disables_live_hydration_now():
    for pid in model.SUPPORTED_PLATFORMS:
        assert model.get_profile(pid)["live_hydration_allowed_now"] is False


def test_every_profile_disables_env_dotenv_keyring_browser_reads():
    for pid in model.SUPPORTED_PLATFORMS:
        prof = model.get_profile(pid)
        assert prof["env_read_allowed_by_default"] is False
        assert prof["dotenv_read_allowed_by_default"] is False
        assert prof["keyring_read_allowed_by_default"] is False
        assert prof["browser_session_read_allowed_by_default"] is False


def test_every_profile_supports_fake_provider():
    for pid in model.SUPPORTED_PLATFORMS:
        assert model.get_profile(pid)["fake_provider_supported"] is True


def test_every_profile_presence_default_unknown():
    for pid in model.SUPPORTED_PLATFORMS:
        assert model.get_profile(pid)["presence_class_default"] == (
            model.PRESENCE_UNKNOWN)


def test_every_profile_family_recognized():
    for pid in model.SUPPORTED_PLATFORMS:
        assert model.get_profile(pid)["credential_family"] in (
            model.CREDENTIAL_FAMILIES)


def test_get_profile_returns_copy():
    a = model.get_profile("telegram")
    a["credential_use_class"] = "MUTATED"
    b = model.get_profile("telegram")
    assert b["credential_use_class"] != "MUTATED"


def test_unknown_platform_profile_is_none():
    assert model.get_profile("myspace") is None


def test_unsupported_platforms_use_manual_only_family():
    for pid in ("substack", "medium"):
        assert model.get_profile(pid)["credential_family"] == (
            model.FAM_UNSUPPORTED)


# --------------------------------------------------------------------------- #
# Deterministic handle id
# --------------------------------------------------------------------------- #
def test_handle_id_is_deterministic():
    a = model.compute_handle_id(
        "telegram", model.FAM_BOT_TOKEN, "bot_channel_message_future",
        "ops-bot", model.FUTURE_SOURCE_INTERACTIVE_PROMPT)
    b = model.compute_handle_id(
        "telegram", model.FAM_BOT_TOKEN, "bot_channel_message_future",
        "ops-bot", model.FUTURE_SOURCE_INTERACTIVE_PROMPT)
    assert a == b
    assert len(a) == 64


def test_handle_id_changes_with_inputs():
    base = model.compute_handle_id(
        "telegram", model.FAM_BOT_TOKEN, "bot_channel_message_future",
        "ops-bot", model.FUTURE_SOURCE_INTERACTIVE_PROMPT)
    other = model.compute_handle_id(
        "telegram", model.FAM_BOT_TOKEN, "bot_channel_message_future",
        "different-label", model.FUTURE_SOURCE_INTERACTIVE_PROMPT)
    assert base != other


def test_handle_id_excludes_secret_inputs():
    import inspect
    sig = inspect.signature(model.compute_handle_id)
    params = set(sig.parameters)
    for forbidden in ("token", "secret", "access_token", "bearer",
                      "refresh_token", "api_key", "webhook_url", "account_id",
                      "username", "handle"):
        assert forbidden not in params


# --------------------------------------------------------------------------- #
# Fake provider (no network / no env / no secret)
# --------------------------------------------------------------------------- #
def test_fake_provider_unknown_class_raises():
    with pytest.raises(ValueError):
        model.make_fake_credential_provider_result("not_a_real_class")


def test_fake_provider_results_are_secret_free():
    for rc in model.FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES:
        result = model.make_fake_credential_provider_result(rc)
        assert result["no_network_performed"] is True
        assert result["no_env_read_performed"] is True
        assert result["no_dotenv_read_performed"] is True
        assert result["no_keyring_read_performed"] is True
        assert result["no_browser_session_read_performed"] is True
        assert result["no_credential_file_read_performed"] is True
        assert result["no_oauth_performed"] is True
        assert result["no_secret_returned"] is True
        assert model.scan_for_leaks(result) == []


def test_fake_provider_configured_symbolic_signals():
    r = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    assert r["presence_class"] == model.PRESENCE_CONFIGURED_SYMBOLIC
    assert r["source_policy_ok"] is True
    assert r["live_hydration_attempted"] is False


# --------------------------------------------------------------------------- #
# Validation: symbolic readiness candidate
# --------------------------------------------------------------------------- #
def _ok_handle(pid="telegram", family=model.FAM_BOT_TOKEN,
               use="bot_channel_message_future"):
    return model.build_handle(pid, family, use, "ops-handle",
                              model.FUTURE_SOURCE_INTERACTIVE_PROMPT)


def test_configured_symbolic_is_readiness_candidate_only():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    decision = model.validate_credential_handle(prof, handle, fpr,
                                                 operator_go=True)
    assert decision["status"] == model.CredentialStatus.PASS
    assert decision["credential_readiness_status"] == (
        model.READINESS_SYMBOLIC_CANDIDATE)
    assert decision["blocked_reasons"] == []
    # Even a clean candidate never enables hydration or live write.
    assert decision["live_hydration_allowed"] is False
    assert decision["live_write_enabled"] is False
    assert decision["autonomous_posting_allowed"] is False
    assert len(decision["credential_handle_id"]) == 64


def test_operator_go_does_not_enable_live_hydration():
    prof = model.get_profile("mastodon")
    handle = _ok_handle("mastodon", model.FAM_INSTANCE_OAUTH,
                        "instance_status_write_future")
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    go = model.validate_credential_handle(prof, handle, fpr, operator_go=True)
    nogo = model.validate_credential_handle(prof, handle, fpr,
                                            operator_go=False)
    assert go["live_hydration_allowed"] is False
    assert nogo["live_hydration_allowed"] is False
    assert go["operator_go_status"] == "operator_go_present"
    assert nogo["operator_go_status"] == "operator_go_absent"


def test_no_result_enables_live_write_or_autonomous_posting():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    for rc in model.FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES:
        fpr = model.make_fake_credential_provider_result(rc)
        decision = model.validate_credential_handle(prof, handle, fpr,
                                                     operator_go=True)
        assert decision["live_hydration_allowed"] is False
        assert decision["live_write_enabled"] is False
        assert decision["autonomous_posting_allowed"] is False


# --------------------------------------------------------------------------- #
# Validation: blocking cases
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rc,reason", [
    (model.FCP_NOT_CONFIGURED, "presence_not_configured"),
    (model.FCP_UNKNOWN, "presence_unknown"),
    (model.FCP_EXPIRED_SYMBOLIC, "presence_expired_symbolic"),
    (model.FCP_REVOKED_SYMBOLIC, "presence_revoked_symbolic"),
    (model.FCP_INSUFFICIENT_SCOPE_SYMBOLIC,
     "presence_insufficient_scope_symbolic"),
    (model.FCP_WRONG_ACCOUNT_SYMBOLIC, "presence_wrong_account_symbolic"),
])
def test_presence_blocking_cases(rc, reason):
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(rc)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert decision["status"] == model.CredentialStatus.BLOCKED
    assert reason in decision["blocked_reasons"]
    assert decision["credential_readiness_status"] == (
        model.READINESS_NOT_READY)
    assert decision["live_hydration_allowed"] is False


def test_source_policy_blocked_blocks():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(
        model.FCP_SOURCE_POLICY_BLOCKED)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert decision["status"] == model.CredentialStatus.BLOCKED
    assert "source_policy_blocked" in decision["blocked_reasons"]


def test_live_hydration_attempt_blocked_blocks():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(
        model.FCP_LIVE_HYDRATION_ATTEMPT_BLOCKED)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert decision["status"] == model.CredentialStatus.BLOCKED
    assert "live_hydration_attempt_blocked" in decision["blocked_reasons"]
    assert decision["live_hydration_allowed"] is False


def test_profile_handle_platform_mismatch_blocks():
    prof = model.get_profile("telegram")
    handle = _ok_handle("x", model.FAM_OAUTH2_USER_CONTEXT,
                        "short_form_post_future_paid")
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert "profile_handle_platform_mismatch" in decision["blocked_reasons"]


def test_credential_family_mismatch_blocks():
    prof = model.get_profile("telegram")
    handle = _ok_handle("telegram", model.FAM_OAUTH2_USER_CONTEXT,
                        "bot_channel_message_future")
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert "credential_family_mismatch" in decision["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Fail-closed redaction
# --------------------------------------------------------------------------- #
def test_validate_fails_closed_on_forbidden_value_class():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(
        model.FCP_FORBIDDEN_VALUE_DETECTED)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert decision["status"] == model.CredentialStatus.FAIL_CLOSED
    assert "forbidden_value_detected" in decision["blocked_reasons"]
    assert decision["credential_readiness_status"] == (
        model.READINESS_FAIL_CLOSED)


def test_validate_fails_closed_on_token_embedded_in_handle():
    prof = model.get_profile("telegram")
    handle = model.build_handle(
        "telegram", model.FAM_BOT_TOKEN, "bot_channel_message_future",
        "bearer AAAAfakebearertokenvalue1234567890",
        model.FUTURE_SOURCE_INTERACTIVE_PROMPT)
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    decision = model.validate_credential_handle(prof, handle, fpr)
    assert decision["status"] == model.CredentialStatus.FAIL_CLOSED
    assert decision["forbidden_fields_detected"] is True
    assert decision["redaction_verified"] is False


# --------------------------------------------------------------------------- #
# Redaction scanner coverage
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("payload", [
    {"v": "bearer AAAAabcdefghij1234567890klmno"},
    {"v": "123456789:AAEhBqfakeTelegramTokenValue1234567890abc"},
    {"v": "xoxb-1234567890-abcdefghijklmnop"},
    {"v": "ghp_abcdefghijklmnopqrstuvwxyz0123456789"},
    {"v": "AKIAABCDEFGHIJKLMNOP"},
    {"v": "eyJhbGciOi.eyJzdWIiOiI.SflKxwRJSMeKK"},
    {"v": "https://example.com/cb?code=abc123&state=xyz"},
    {"v": "access_token=abcdef123456"},
    {"v": "export API_KEY=supersecretvalue123"},
    {"v": "https://x.com/some_account"},
    {"v": "https://discord.com/api/webhooks/123456789/abcDEF"},
    {"v": "@realhandle"},
    {"v": "secret prefix: abcd1234"},
    {"v": "token last4: 9999"},
    {"v": "urn:li:person:"},
])
def test_scan_catches_forbidden_examples(payload):
    assert model.scan_for_leaks(payload), f"missed: {payload}"


def test_scan_catches_forbidden_key():
    assert any(v.startswith("forbidden_key:")
               for v in model.scan_for_leaks({"client_secret": "x"}))


def test_scan_passes_clean_decision():
    prof = model.get_profile("telegram")
    handle = _ok_handle()
    fpr = model.make_fake_credential_provider_result(
        model.FCP_CONFIGURED_SYMBOLIC)
    decision = model.validate_credential_handle(prof, handle, fpr,
                                                 operator_go=True)
    assert model.scan_for_leaks(decision) == []


# --------------------------------------------------------------------------- #
# Packet + doc
# --------------------------------------------------------------------------- #
def test_packet_is_leak_free_and_deterministic():
    p1 = model.build_packet()
    p2 = model.build_packet()
    assert model.scan_for_leaks(p1) == []
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert p1["status"] == model.CredentialStatus.PASS


def test_packet_safety_flags():
    p = model.build_packet()
    flags = p["safety_flags"]
    assert flags["live_hydration_allowed"] is False
    assert flags["live_write_enabled"] is False
    assert flags["autonomous_posting_allowed"] is False
    assert flags["no_network_performed"] is True
    assert flags["no_env_read_performed"] is True
    assert flags["no_oauth_performed"] is True


def test_packet_strategic_posture():
    p = model.build_packet()
    posture = p["strategic_posture"]
    assert posture["manual_posting"] == "fallback"
    assert posture["automation"] == "main_build_path"
    assert posture["autonomous_posting"] == "forbidden"
    assert posture["supervised_publishing"] == "final_product"


def test_packet_next_task_recommendation():
    p = model.build_packet()
    assert p["exact_next_task_recommendation"] == (
        "TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0")


def test_doc_is_leak_free():
    doc = model.build_doc()
    assert model.scan_for_leaks(doc) == []
    assert "0174EC" in doc


def test_write_artifacts_touches_only_0174ec_dir(tmp_path):
    paths = model.write_artifacts(repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "automation" / "0174EC"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([
        "social_credential_handle_boundary_packet.json",
        "social_credential_handle_and_redaction_boundary.md",
    ])
    # Only the 0174EC dir was created under docs/automation.
    automation_dir = tmp_path / "docs" / "automation"
    assert sorted(p.name for p in automation_dir.iterdir()) == ["0174EC"]
    # Round-trip the written packet and re-scan it.
    with open(out_dir / "social_credential_handle_boundary_packet.json",
              "r", encoding="utf-8") as fh:
        packet = json.load(fh)
    assert model.scan_for_leaks(packet) == []
    assert len(paths) == 2


def test_source_baseline_commit_recorded():
    assert model.SOURCE_BASELINE_COMMIT == (
        "c5763167bee79f41381465af517039498c219f63")


# --------------------------------------------------------------------------- #
# Integration with 0174EB binding model
# --------------------------------------------------------------------------- #
def test_every_0174eb_platform_has_credential_profile():
    for pid in binding_model.SUPPORTED_PLATFORMS:
        assert model.get_profile(pid) is not None, (
            f"missing 0174EC credential profile for 0174EB platform: {pid}")
