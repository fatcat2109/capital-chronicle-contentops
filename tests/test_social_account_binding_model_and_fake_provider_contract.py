"""Tests for the 0174EB social account binding model + fake-provider contract.

These tests prove the module is deterministic, stdlib-only, secret-free, and
fail-closed, and that:
  * the static import surface is an exact stdlib allow-list (hashlib, json, os,
    re) with no requests/httpx/aiohttp/socket/ssl/http server, no
    selenium/playwright, no dotenv/keyring/sqlite,
  * importing the module performs NO network, NO credential read, and NO file
    write,
  * the deterministic binding id is stable and excludes secret inputs,
  * every platform profile and every binding decision reports
    live_write_enabled = False and autonomous_posting_allowed = False,
  * the fake provider simulates all required failure cases without network or
    credentials and never returns secret values,
  * wrong-account / missing-scope / destination-mismatch / rate-limited /
    docs-unresolved / audit-not-approved / spend-blocked / token-missing /
    credential-source-unavailable / redirect-mismatch / duplicate cases block,
  * a clean success produces a validated candidate (still no live write),
  * the redaction scanner fails closed on tokens/handles/profile URLs/etc.,
  * the packet + contract doc are leak-free, and writing touches only the
    0174EB doc directory.
"""

import ast
import json
import os

import pytest

from live_contentops import social_account_binding_model as model


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "social_account_binding_model.py")


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
              "sqlite3.", "getpass"):
        assert s not in src, f"forbidden credential/env access string: {s}"


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
def test_all_expected_platforms_present():
    expected = {
        "x", "linkedin", "telegram", "facebook", "instagram", "threads",
        "substack", "tiktok", "youtube", "bluesky", "discord", "mastodon",
        "reddit", "medium",
    }
    assert expected <= set(model.SUPPORTED_PLATFORMS)


def test_every_profile_is_live_write_disabled():
    for pid in model.SUPPORTED_PLATFORMS:
        prof = model.get_profile(pid)
        assert prof["live_write_default_enabled"] is False
        assert prof["autonomous_posting_allowed"] is False
        assert prof["manual_fallback_available"] is True
        assert prof["fake_provider_supported"] is True


def test_get_profile_returns_copy():
    a = model.get_profile("telegram")
    a["platform_role"] = "MUTATED"
    b = model.get_profile("telegram")
    assert b["platform_role"] != "MUTATED"


def test_unknown_platform_profile_is_none():
    assert model.get_profile("myspace") is None


def test_meta_family_requires_docs_verification():
    for pid in ("facebook", "instagram", "threads", "substack", "medium"):
        assert model.get_profile(pid)["requires_docs_verification"] is True


def test_audit_required_platforms():
    for pid in ("tiktok", "youtube"):
        assert model.get_profile(pid)["requires_audit"] is True


def test_x_requires_spend_proof():
    assert model.get_profile("x")["requires_spend_proof"] is True


# --------------------------------------------------------------------------- #
# Deterministic binding id
# --------------------------------------------------------------------------- #
def test_binding_id_is_deterministic():
    a = model.compute_binding_id(
        "telegram", "channel", "ops-broadcast", "unlisted_default",
        model.PROOF_IDENTITY)
    b = model.compute_binding_id(
        "telegram", "channel", "ops-broadcast", "unlisted_default",
        model.PROOF_IDENTITY)
    assert a == b
    assert len(a) == 64


def test_binding_id_changes_with_inputs():
    base = model.compute_binding_id(
        "telegram", "channel", "ops-broadcast", "unlisted_default",
        model.PROOF_IDENTITY)
    other = model.compute_binding_id(
        "telegram", "channel", "different-label", "unlisted_default",
        model.PROOF_IDENTITY)
    assert base != other


def test_binding_id_excludes_secret_inputs():
    # The binding id signature has no token/secret parameter at all.
    import inspect
    sig = inspect.signature(model.compute_binding_id)
    params = set(sig.parameters)
    for forbidden in ("token", "secret", "access_token", "bearer",
                      "raw_account_id"):
        assert forbidden not in params


# --------------------------------------------------------------------------- #
# Fake provider (no network / no secret)
# --------------------------------------------------------------------------- #
def test_fake_provider_unknown_class_raises():
    with pytest.raises(ValueError):
        model.make_fake_provider_result("not_a_real_class")


def test_fake_provider_results_are_secret_free():
    for rc in model.FAKE_PROVIDER_RESULT_CLASSES:
        result = model.make_fake_provider_result(rc)
        assert result["no_network_performed"] is True
        assert result["no_credential_read_performed"] is True
        assert result["no_secret_returned"] is True
        assert model.scan_for_leaks(result) == []


def test_fake_provider_success_signals():
    r = model.make_fake_provider_result(model.FP_SUCCESS)
    assert r["identity_match"] is True
    assert r["permission_granted"] is True
    assert r["destination_match"] is True


# --------------------------------------------------------------------------- #
# Validation: success path
# --------------------------------------------------------------------------- #
def _ok_destination(pid="telegram", kind="channel"):
    return model.build_destination(
        pid, kind, "ops-broadcast", "unlisted_default", model.PROOF_IDENTITY)


def test_validate_success_telegram():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr,
                                              operator_go=True)
    assert decision["status"] == model.BindingStatus.PASS
    assert decision["account_binding_status"] == (
        model.BINDING_CANDIDATE_VALIDATED)
    assert decision["identity_proof_status"] == "identity_confirmed_redacted"
    assert decision["blocked_reasons"] == []
    assert decision["live_write_enabled"] is False
    assert decision["autonomous_posting_allowed"] is False
    assert len(decision["binding_id"]) == 64


def test_validate_success_still_no_live_write_even_with_go():
    prof = model.get_profile("mastodon")
    dest = _ok_destination("mastodon", "instance_account")
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr,
                                              operator_go=True)
    assert decision["live_write_enabled"] is False
    assert decision["no_live_post_performed"] is True


# --------------------------------------------------------------------------- #
# Validation: failure cases
# --------------------------------------------------------------------------- #
def test_validate_wrong_account_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_WRONG_ACCOUNT)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert decision["status"] == model.BindingStatus.BLOCKED
    assert "wrong_account" in decision["blocked_reasons"]
    assert decision["live_write_enabled"] is False


def test_validate_missing_scope_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_MISSING_SCOPE)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "missing_permission_or_scope" in decision["blocked_reasons"]


def test_validate_destination_mismatch_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_DESTINATION_MISMATCH)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "destination_mismatch" in decision["blocked_reasons"]


def test_validate_token_missing_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_TOKEN_MISSING)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "token_missing" in decision["blocked_reasons"]
    assert decision["identity_proof_status"] == "token_missing_blocked"


def test_validate_credential_source_unavailable_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(
        model.FP_CREDENTIAL_SOURCE_UNAVAILABLE)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "credential_source_unavailable" in decision["blocked_reasons"]


def test_validate_rate_limited_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_RATE_LIMITED)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "rate_limited" in decision["blocked_reasons"]


def test_validate_docs_unresolved_blocks_meta_family():
    prof = model.get_profile("facebook")
    dest = _ok_destination("facebook", "page")
    fpr = model.make_fake_provider_result(model.FP_DOCS_UNRESOLVED)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "docs_unresolved" in decision["blocked_reasons"]


def test_validate_audit_not_approved_blocks_tiktok():
    prof = model.get_profile("tiktok")
    dest = _ok_destination("tiktok", "creator_account")
    fpr = model.make_fake_provider_result(model.FP_AUDIT_NOT_APPROVED)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "audit_not_approved" in decision["blocked_reasons"]


def test_validate_private_test_only_blocks_youtube():
    prof = model.get_profile("youtube")
    dest = _ok_destination("youtube", "channel")
    fpr = model.make_fake_provider_result(model.FP_PRIVATE_TEST_ONLY)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "audit_not_approved" in decision["blocked_reasons"]


def test_validate_spend_blocked_blocks_x():
    prof = model.get_profile("x")
    dest = _ok_destination("x", "account")
    fpr = model.make_fake_provider_result(model.FP_SPEND_BLOCKED)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "spend_budget_blocked" in decision["blocked_reasons"]


def test_validate_redirect_mismatch_blocks_reddit():
    prof = model.get_profile("reddit")
    dest = _ok_destination("reddit", "subreddit")
    fpr = model.make_fake_provider_result(model.FP_REDIRECT_MISMATCH)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "redirect_mismatch" in decision["blocked_reasons"]


def test_validate_duplicate_destination_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_DUPLICATE_DESTINATION)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "duplicate_destination_candidate" in decision["blocked_reasons"]


def test_validate_profile_destination_platform_mismatch_blocks():
    prof = model.get_profile("telegram")
    dest = _ok_destination("x", "account")
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "profile_destination_platform_mismatch" in (
        decision["blocked_reasons"])


def test_validate_unsupported_destination_kind_blocks():
    prof = model.get_profile("telegram")
    dest = model.build_destination(
        "telegram", "carrier_pigeon", "ops-broadcast")
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert "destination_kind_not_supported_by_profile" in (
        decision["blocked_reasons"])


# --------------------------------------------------------------------------- #
# Fail-closed redaction
# --------------------------------------------------------------------------- #
def test_validate_fails_closed_on_forbidden_token_value():
    prof = model.get_profile("telegram")
    dest = model.build_destination(
        "telegram", "channel",
        "bearer AAAAfakebearertokenvalue1234567890")
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr)
    assert decision["status"] == model.BindingStatus.FAIL_CLOSED
    assert decision["forbidden_fields_detected"] is True
    assert decision["redaction_verified"] is False


def test_scan_catches_handle():
    assert model.scan_for_leaks({"label": "@realhandle"})


def test_scan_catches_profile_url():
    assert model.scan_for_leaks(
        {"label": "https://t.me/some_channel_handle"})


def test_scan_catches_forbidden_key():
    assert any(v.startswith("forbidden_key:")
               for v in model.scan_for_leaks({"access_token": "x"}))


def test_scan_passes_clean_decision():
    prof = model.get_profile("telegram")
    dest = _ok_destination()
    fpr = model.make_fake_provider_result(model.FP_SUCCESS)
    decision = model.validate_account_binding(prof, dest, fpr,
                                              operator_go=True)
    assert model.scan_for_leaks(decision) == []


# --------------------------------------------------------------------------- #
# Packet + doc
# --------------------------------------------------------------------------- #
def test_packet_is_leak_free_and_deterministic():
    p1 = model.build_packet()
    p2 = model.build_packet()
    assert model.scan_for_leaks(p1) == []
    assert p1["packet_checksum"] == p2["packet_checksum"]


def test_packet_safety_flags():
    p = model.build_packet()
    flags = p["safety_flags"]
    assert flags["live_write_enabled"] is False
    assert flags["autonomous_posting_allowed"] is False
    assert flags["no_network_performed"] is True
    assert flags["stdlib_only"] is True


def test_packet_strategic_posture():
    p = model.build_packet()
    posture = p["strategic_posture"]
    assert posture["manual_posting"] == "fallback"
    assert posture["automation"] == "main_build_path"
    assert posture["autonomous_posting"] == "forbidden"
    assert posture["supervised_publishing"] == "final_product"


def test_contract_doc_is_leak_free():
    doc = model.build_contract_doc()
    assert model.scan_for_leaks(doc) == []
    assert "0174EB" in doc


def test_write_artifacts_touches_only_0174eb_dir(tmp_path):
    paths = model.write_artifacts(repo_root=str(tmp_path))
    assert paths["packet_path"] == (
        "docs/automation/0174EB/social_account_binding_model_packet.json")
    out_dir = tmp_path / "docs" / "automation" / "0174EB"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([
        "social_account_binding_model_packet.json",
        "social_account_binding_model_and_fake_provider_contract.md",
    ])
    # Round-trip the written packet and re-scan it.
    with open(out_dir / "social_account_binding_model_packet.json",
              "r", encoding="utf-8") as fh:
        packet = json.load(fh)
    assert model.scan_for_leaks(packet) == []


def test_source_baseline_commit_recorded():
    assert model.SOURCE_BASELINE_COMMIT == (
        "6c1e01c1238ca930b97fde1c4513ebc2c819da76")
