"""Tests for the 0174DE X OAuth live-read-only IDENTITY PROOF gate.

These tests prove the module is fail-closed and that:
  * the static import surface is an exact allow-list -- only hashlib, json, os,
    re, sys at module scope, plus getpass and urllib used ONLY inside the live
    path; no requests/httpx/aiohttp or other broad/unsafe modules,
  * there is no command-line token argument support,
  * no env/.env/config/keyring/browser-store/shell-history/git-history reads,
  * default (no-flag) mode performs no network, reads no token, and writes
    nothing unless the write flag is present,
  * a live request requires BOTH operator-go and execute flags,
  * missing operator-go blocks; missing execute blocks,
  * a fake live execution performs exactly ONE request with no retry,
  * wrong host / wrong method / wrong endpoint family all block,
  * the timeout is explicit,
  * the token is never printed, persisted, hashed, fingerprinted, prefixed,
    suffixed, or placed in the packet,
  * the raw response body / headers / account id / handle / profile URL are
    never persisted,
  * the redacted identity proof contains only boolean/class fields,
  * posting/mutation endpoints are impossible through this command,
  * the CLI command is wired and write touches only the 0174DE packet + README,
  * prior 0174CU..0174DD artifacts are not mutated.
"""

import ast
import io
import json
import os
import re
import sys
import contextlib

import pytest

from live_contentops import (
    x_oauth_live_read_only_identity_proof_gate as gate)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "x_oauth_live_read_only_identity_proof_gate.py")


# --------------------------------------------------------------------------- #
# Fake providers (NO real token, NO real network)
# --------------------------------------------------------------------------- #
def _fake_token_provider():
    return "FAKE-TEST-TOKEN-NOT-REAL"


def _empty_token_provider():
    return ""


class _RecordingCaller:
    """Fake HTTP caller that records calls and returns a canned response."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, method, url, token, timeout_seconds):
        self.calls.append({
            "method": method,
            "url": url,
            "timeout_seconds": timeout_seconds,
            "token_len": len(token) if token else 0,
        })
        return self.response


def _identity_ok_response():
    # Mimics GET /2/users/me success; identity values are inspected transiently
    # by the gate and must never be persisted.
    return {"ok": True, "status_code": 200,
            "json": {"data": {"id": "2244994945", "username": "TwitterDev",
                              "name": "X Dev"}},
            "error_class": None}


# --------------------------------------------------------------------------- #
# Import allow-list / forbidden imports (static AST analysis)
# --------------------------------------------------------------------------- #
# This module is allowed getpass + urllib, but ONLY for the gated live path.
ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re", "sys",
                        "getpass", "urllib"}

FORBIDDEN_IMPORT_ROOTS = {
    "requests", "httpx", "aiohttp", "socket", "socketserver", "ssl",
    "asyncio", "selectors", "http", "wsgiref", "webbrowser", "subprocess",
    "dotenv", "ftplib", "telnetlib", "smtplib", "multiprocessing",
    "threading", "configparser", "keyring", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve", "selenium",
    "playwright",
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


def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, (
        f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}")


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_no_requests_httpx_aiohttp_anywhere():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("requests.", "httpx.", "aiohttp.", "import requests",
              "import httpx", "import aiohttp"):
        assert s not in src, f"forbidden http client present: {s}"


def test_getpass_and_urllib_used_only_inside_functions():
    """getpass and urllib must be lazily imported inside functions, never at
    module scope, so importing the module performs no such side effects."""
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    module_scope_roots = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_scope_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_scope_roots.add(node.module.split(".")[0])
    assert "getpass" not in module_scope_roots
    assert "urllib" not in module_scope_roots


def test_no_env_dotenv_config_keyring_access_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("os.environ", "os.getenv", "getenv(", "load_dotenv",
              "dotenv_values", "keyring.get", "keyring.set",
              "secretstorage.", "netrc(", "configparser.", "ConfigParser",
              "expanduser", "browser_cookie", "sqlite3."):
        assert s not in src, f"forbidden credential/env access string: {s}"


def test_no_command_line_token_argument():
    """The CLI must never accept a token via argv."""
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("--token", "--access-token", "--bearer", "--bearer-token",
              "--client-secret", "--secret"):
        assert s not in src, f"command-line token argument present: {s}"


def test_no_mutating_endpoint_strings():
    """Posting/mutation endpoints must be impossible through this command."""
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("/2/tweets", "/2/dm_", "/2/likes", "method=\"POST\"",
              "method='POST'", "\"DELETE\"", "'DELETE'", "\"PUT\"", "'PUT'",
              "\"PATCH\"", "'PATCH'"):
        assert s not in src, f"mutating endpoint/method present: {s}"


# --------------------------------------------------------------------------- #
# Policy constants
# --------------------------------------------------------------------------- #
def test_policy_constants():
    assert gate.ALLOWED_HOST == "api.x.com"
    assert gate.ALLOWED_METHOD == "GET"
    assert gate.REQUEST_BUDGET == 1
    assert gate.ENDPOINT_URL == "https://api.x.com/2/users/me"
    assert isinstance(gate.TIMEOUT_SECONDS, int)
    assert 0 < gate.TIMEOUT_SECONDS <= 30


# --------------------------------------------------------------------------- #
# Dry-run (default) mode
# --------------------------------------------------------------------------- #
def test_dry_run_default_blocks_no_operator_go():
    result = gate.run_gate()
    assert result["live_request_performed"] is False
    assert result["request_count"] == 0
    assert result["no_live_network_call_performed"] is True
    assert result["live_network_call_performed"] is False
    assert result["live_read_only_identity_proof_status"] == (
        "blocked_no_operator_go")
    assert result["status"] == "pass"


def test_dry_run_performs_no_network_and_reads_no_token():
    calls = _RecordingCaller(_identity_ok_response())
    provider_called = {"n": 0}

    def _provider():
        provider_called["n"] += 1
        return "SHOULD-NOT-BE-CALLED"

    result = gate.run_gate(token_provider=_provider, http_caller=calls)
    assert calls.calls == []
    assert provider_called["n"] == 0
    assert result["request_count"] == 0


def test_execute_without_operator_go_blocks():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    assert result["live_request_performed"] is False
    assert calls.calls == []
    assert result["live_read_only_identity_proof_status"] == (
        "blocked_no_operator_go")


def test_operator_go_without_execute_blocks():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    assert result["live_request_performed"] is False
    assert calls.calls == []
    assert result["live_read_only_identity_proof_status"] == (
        "blocked_not_executed")


def test_dry_run_does_not_write_without_write_flag(tmp_path):
    gate.run_gate(repo_root=str(tmp_path))
    packet = tmp_path / "docs" / "credential_readiness" / "0174DE" / \
        gate.PACKET_FILENAME
    assert not packet.exists()


# --------------------------------------------------------------------------- #
# Live execution (fake provider + fake caller) -- exactly one request
# --------------------------------------------------------------------------- #
def test_live_execution_requires_both_flags_and_makes_one_request():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    assert result["live_request_performed"] is True
    assert result["live_network_call_performed"] is True
    assert result["no_live_network_call_performed"] is False
    assert result["request_count"] == 1
    assert result["retry_count"] == 0
    assert len(calls.calls) == 1
    assert result["live_read_only_call_only"] is True


def test_live_execution_uses_get_and_correct_url():
    calls = _RecordingCaller(_identity_ok_response())
    gate.run_gate(operator_go=True, execution_requested=True,
                  token_provider=_fake_token_provider, http_caller=calls)
    assert calls.calls[0]["method"] == "GET"
    assert calls.calls[0]["url"] == "https://api.x.com/2/users/me"
    assert calls.calls[0]["timeout_seconds"] == gate.TIMEOUT_SECONDS


def test_live_execution_identity_proof_is_redacted_booleans_only():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    proof = result["redacted_identity_proof"]
    allowed_keys = {
        "identity_endpoint_reachable_boolean",
        "authenticated_user_context_boolean",
        "account_identity_seen_boolean",
        "account_identifier_exposed_boolean",
        "account_handle_exposed_boolean",
        "token_exposed_boolean",
        "response_redaction_passed_boolean",
        "identity_proof_status_class",
    }
    assert set(proof.keys()) == allowed_keys
    # All non-class values are booleans.
    for k, v in proof.items():
        if k == "identity_proof_status_class":
            assert isinstance(v, str)
        else:
            assert isinstance(v, bool)
    assert proof["account_identifier_exposed_boolean"] is False
    assert proof["account_handle_exposed_boolean"] is False
    assert proof["token_exposed_boolean"] is False
    assert proof["identity_endpoint_reachable_boolean"] is True
    assert proof["authenticated_user_context_boolean"] is True
    assert proof["account_identity_seen_boolean"] is True


def test_live_execution_no_retry_on_error():
    calls = _RecordingCaller({"ok": False, "status_code": 401, "json": None,
                              "error_class": "http_error_redacted"})
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    assert len(calls.calls) == 1
    assert result["retry_count"] == 0
    assert result["request_count"] == 1
    assert result["live_read_only_identity_proof_status"] == (
        "http_error_redacted")


def test_missing_token_source_blocks_fail_closed():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_empty_token_provider,
                           http_caller=calls)
    assert calls.calls == []
    assert result["live_request_performed"] is False
    assert result["live_read_only_identity_proof_status"] == (
        "blocked_pending_operator_go_or_token_source")


def test_raw_identity_values_never_appear_in_result():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    blob = json.dumps(result)
    for forbidden in ("2244994945", "TwitterDev", "X Dev",
                      "FAKE-TEST-TOKEN-NOT-REAL"):
        assert forbidden not in blob, f"raw value leaked: {forbidden}"


# --------------------------------------------------------------------------- #
# Default HTTP caller host/method/endpoint guards (NO network)
# --------------------------------------------------------------------------- #
def test_default_http_caller_blocks_wrong_method():
    out = gate._default_http_caller("POST", gate.ENDPOINT_URL, "t", 5)
    assert out["ok"] is False
    assert out["error_class"] == "method_mismatch_blocked"
    assert out["status_code"] is None


def test_default_http_caller_blocks_wrong_host():
    out = gate._default_http_caller(
        "GET", "https://evil.example.com/2/users/me", "t", 5)
    assert out["ok"] is False
    assert out["error_class"] == "host_mismatch_blocked"


def test_default_http_caller_blocks_wrong_endpoint():
    out = gate._default_http_caller(
        "GET", "https://api.x.com/2/tweets", "t", 5)
    assert out["ok"] is False
    assert out["error_class"] == "endpoint_mismatch_blocked"


def test_default_http_caller_blocks_non_https():
    out = gate._default_http_caller(
        "GET", "http://api.x.com/2/users/me", "t", 5)
    assert out["ok"] is False
    assert out["error_class"] == "host_mismatch_blocked"


# --------------------------------------------------------------------------- #
# redact_identity_response mapping
# --------------------------------------------------------------------------- #
def test_redact_identity_response_unexpected_shape():
    out = gate.redact_identity_response(
        {"ok": True, "status_code": 200, "json": {"foo": "bar"}})
    assert out["authenticated_user_context_boolean"] is False
    assert out["account_identity_seen_boolean"] is False
    assert out["identity_proof_status_class"] == (
        "unexpected_response_shape_redacted")


def test_redact_identity_response_never_contains_raw_values():
    out = gate.redact_identity_response(_identity_ok_response())
    blob = json.dumps(out)
    for forbidden in ("2244994945", "TwitterDev", "X Dev"):
        assert forbidden not in blob


# --------------------------------------------------------------------------- #
# Packet structure / required keys / invariants
# --------------------------------------------------------------------------- #
REQUIRED_PACKET_KEYS = [
    "task_label", "gate", "platform", "source_baseline_commit",
    "inherited_0174dd_commit", "accepted_0174dd_reference",
    "live_read_only_identity_proof_status", "operator_go_status",
    "execution_requested", "live_request_performed", "request_budget",
    "request_count", "retry_count", "timeout_seconds", "allowed_host",
    "allowed_method", "official_endpoint_family_verified", "endpoint_family",
    "official_docs_checked", "official_docs_sources", "redacted_identity_proof",
    "redacted_response_contract", "redacted_error_contract",
    "token_handling_contract", "no_token_persistence_contract",
    "account_binding_status", "posting_status", "blocker_status",
    "current_blockers", "cleared_blockers_if_any", "next_required_gate",
    "exact_next_task_recommendation", "caveats",
]

REQUIRED_TRUE_FLAGS = [
    "no_posting_performed", "no_mutating_x_api_call_performed",
    "no_token_exchange_performed", "no_refresh_flow_performed",
    "no_token_persisted", "no_token_logged",
    "no_token_hash_or_fingerprint_created",
    "no_token_prefix_or_suffix_exposed", "no_account_identifier_persisted",
    "no_account_handle_persisted", "no_profile_url_persisted",
    "no_raw_response_persisted", "no_response_headers_persisted",
    "no_metrics_fetched", "no_webhook_created", "no_reply_dm_created",
    "no_scraping_performed", "no_autonomous_publishing", "redaction_verified",
]


def test_packet_required_keys_present():
    packet = gate.build_packet()
    for key in REQUIRED_PACKET_KEYS:
        assert key in packet, f"missing required key: {key}"


def test_packet_required_true_flags():
    packet = gate.build_packet()
    for flag in REQUIRED_TRUE_FLAGS:
        assert packet.get(flag) is True, f"flag not true: {flag}"


def test_packet_invariants():
    packet = gate.build_packet()
    assert packet["platform"] == "x"
    assert packet["request_budget"] == 1
    assert packet["retry_count"] == 0
    assert packet["allowed_host"] == "api.x.com"
    assert packet["allowed_method"] == "GET"
    assert packet["posting_status"] == "blocked"
    assert packet["account_binding_status"] == "not_bound_by_this_task"
    assert packet["no_token_persistence_contract"] is True
    assert packet["token_exchange_status"] == "not_performed"
    assert packet["source_baseline_commit"] == (
        "0354581e83e4c2d1008e2f601635d7da8722a669")
    assert packet["inherited_0174dd_commit"] == (
        "0354581e83e4c2d1008e2f601635d7da8722a669")


def test_dry_run_packet_network_flags():
    packet = gate.build_packet(live_request_performed=False, request_count=0)
    assert packet["no_live_network_call_performed"] is True
    assert packet["live_network_call_performed"] is False
    assert packet["request_count"] == 0


def test_executed_packet_network_flags():
    packet = gate.build_packet(live_request_performed=True, request_count=1)
    assert packet["live_network_call_performed"] is True
    assert packet["no_live_network_call_performed"] is False
    assert packet["request_count"] == 1
    assert packet["live_read_only_call_only"] is True


def test_token_handling_contract_safe():
    packet = gate.build_packet()
    thc = packet["token_handling_contract"]
    assert thc["command_line_token_argument_supported"] is False
    assert thc["env_or_dotenv_read_by_default"] is False
    assert thc["token_printed"] is False
    assert thc["token_logged"] is False
    assert thc["token_persisted"] is False
    assert thc["token_hashed_or_fingerprinted"] is False
    assert thc["token_prefix_or_suffix_exposed"] is False


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_packet_passes_redaction_scan():
    packet = gate.build_packet()
    assert gate.scan_packet_for_leaks(packet) == []


def test_executed_packet_passes_redaction_scan():
    calls = _RecordingCaller(_identity_ok_response())
    result = gate.run_gate(operator_go=True, execution_requested=True,
                           token_provider=_fake_token_provider,
                           http_caller=calls)
    packet = gate.build_packet(
        live_request_performed=True, request_count=1,
        operator_go=True, execution_requested=True,
        proof=result["redacted_identity_proof"],
        proof_status=result["live_read_only_identity_proof_status"])
    assert gate.scan_packet_for_leaks(packet) == []


def test_scanner_flags_bearer_token():
    bad = {"note": "Authorization: Bearer AAAAabcdefghij1234567890"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_forbidden_key():
    bad = {"access_token": "x"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_raw_handle():
    bad = {"note": "logged in as @SomeRealHandle"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_long_numeric_id():
    bad = {"note": "user id 2244994945 seen"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_allows_git_sha():
    ok = {"source_baseline_commit": gate.SOURCE_BASELINE_COMMIT}
    assert gate.scan_packet_for_leaks(ok) == []


# --------------------------------------------------------------------------- #
# Serialization / checksum determinism
# --------------------------------------------------------------------------- #
def test_serialize_deterministic():
    packet = gate.build_packet()
    assert gate.serialize(packet) == gate.serialize(packet)


def test_checksum_matches_serialization():
    import hashlib
    packet = gate.build_packet()
    expected = hashlib.sha256(
        gate.serialize(packet).encode("utf-8")).hexdigest()
    assert gate.compute_checksum(packet) == expected


# --------------------------------------------------------------------------- #
# Official docs sources
# --------------------------------------------------------------------------- #
def test_official_docs_sources_present_and_clean():
    sources = gate.build_official_docs_sources()
    assert len(sources) >= 2
    families = {s["source_family"] for s in sources}
    assert "x_api_v2_users_me" in sources[0]["source_family"] or (
        "x_api_v2_users_me" in families)
    assert gate.scan_packet_for_leaks(sources) == []


# --------------------------------------------------------------------------- #
# Write behavior (write flag) -- only 0174DE packet + README
# --------------------------------------------------------------------------- #
def test_write_creates_only_0174de_packet_and_readme(tmp_path):
    result = gate.run_gate(write=True, repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DE"
    packet = out_dir / gate.PACKET_FILENAME
    readme = out_dir / gate.README_FILENAME
    assert packet.exists()
    assert readme.exists()
    assert result["packet_written"] is True
    assert result["readme_written"] is True
    # Only these two files exist in the 0174DE dir.
    assert sorted(os.listdir(out_dir)) == sorted(
        [gate.PACKET_FILENAME, gate.README_FILENAME])


def test_written_packet_is_valid_json_and_clean(tmp_path):
    gate.run_gate(write=True, repo_root=str(tmp_path))
    packet = tmp_path / "docs" / "credential_readiness" / "0174DE" / \
        gate.PACKET_FILENAME
    with open(packet, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert gate.scan_packet_for_leaks(data) == []
    assert data["request_budget"] == 1
    assert data["allowed_host"] == "api.x.com"


def test_write_does_not_touch_prior_chain_dirs(tmp_path):
    # Create sibling prior-chain dirs with sentinel files.
    base = tmp_path / "docs" / "credential_readiness"
    for prior in ("0174CY", "0174CZ", "0174DA", "0174DB", "0174DC", "0174DD"):
        d = base / prior
        d.mkdir(parents=True)
        (d / "sentinel.txt").write_text("KEEP", encoding="utf-8")
    gate.run_gate(write=True, repo_root=str(tmp_path))
    for prior in ("0174CY", "0174CZ", "0174DA", "0174DB", "0174DC", "0174DD"):
        sentinel = base / prior / "sentinel.txt"
        assert sentinel.read_text(encoding="utf-8") == "KEEP"


# --------------------------------------------------------------------------- #
# CLI main()
# --------------------------------------------------------------------------- #
def test_main_dry_run_prints_blocked_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = gate.main(argv=[])
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert data["live_request_performed"] is False
    assert data["request_count"] == 0


def test_main_recognizes_flags_without_real_network(monkeypatch):
    # Force the default provider to raise so no token is obtained; the gate
    # must fail closed WITHOUT a real network call.
    monkeypatch.setattr(gate, "_default_token_provider",
                        lambda: (_ for _ in ()).throw(RuntimeError("no tty")))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = gate.main(argv=[gate.FLAG_OPERATOR_GO, gate.FLAG_EXECUTE])
    assert rc == 0
    data = json.loads(buf.getvalue())
    assert data["live_request_performed"] is False
    assert data["live_read_only_identity_proof_status"] == (
        "blocked_pending_operator_go_or_token_source")

