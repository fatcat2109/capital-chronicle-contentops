"""Tests for the 0174CY X OAuth redirect ledger + callback fixture contract gate.

These tests enforce the strictly-local, contract-only posture: no network /
browser / subprocess / http-server / env imports, strong redaction,
deterministic output, fail-closed writes, and correct CLI wiring. No OAuth
flow, callback server, port bind, token, state/PKCE material, real callback
URL, or account binding is ever performed.
"""

import ast
import json
import os
import subprocess
import sys

import pytest

from live_contentops import (
    x_oauth_redirect_ledger_callback_fixture_contract_gate as gate)

MODULE_PATH = gate.__file__
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- #
# Static safety: import allow-list
# --------------------------------------------------------------------------- #
_ALLOWED_IMPORTS = {"hashlib", "json", "os.path", "os", "re", "sys"}
_FORBIDDEN_IMPORT_SUBSTRINGS = (
    "urllib", "requests", "httpx", "socket", "http", "dotenv",
    "webbrowser", "subprocess", "ssl", "ftplib", "telnetlib", "aiohttp",
    "socketserver", "wsgiref", "asyncio",
)


def _module_source():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


def _imported_names():
    tree = ast.parse(_module_source())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return names


def test_imports_within_allow_list():
    for name in _imported_names():
        top = name.split(".")[0]
        assert name in _ALLOWED_IMPORTS or top in _ALLOWED_IMPORTS, (
            f"unexpected import: {name}"
        )


def test_no_forbidden_network_browser_or_server_imports():
    names = _imported_names()
    for forbidden in _FORBIDDEN_IMPORT_SUBSTRINGS:
        assert not any(forbidden == n.split(".")[0] for n in names), (
            f"forbidden import present: {forbidden}"
        )


def test_source_has_no_env_network_or_server_calls():
    src = _module_source()
    for needle in (
        "os.environ", "os.getenv", "getenv", "Path.home", "expanduser",
        "urlopen", "requests.", "httpx.", "socket.", "webbrowser.",
        "subprocess.", "Popen", "system(", "HTTPServer", "serve_forever",
        ".bind(", ".listen(",
    ):
        assert needle not in src, f"forbidden runtime call present: {needle}"


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_clean_packet_has_no_violations():
    assert gate.scan_packet_for_leaks(gate.build_x_packet()) == []


def test_scanner_flags_token_like_value():
    assert gate.scan_packet_for_leaks(
        {"note": "ghp_abcdefghijklmnopqrstuvwxyz0123"})


def test_scanner_flags_bearer_token():
    assert gate.scan_packet_for_leaks(
        {"note": "Authorization: Bearer abcdef0123456789abcdef"})


def test_scanner_flags_forbidden_keys():
    for key in ("access_token", "client_secret", "code_verifier", "state",
                "authorization_code", "redirect_uri", "code_challenge",
                "code", "error_description", "raw_query", "query_string",
                "callback_url", "tweet_id", "user_id"):
        assert gate.scan_packet_for_leaks({key: "x"}), key


def test_scanner_flags_callback_url_with_query():
    assert gate.scan_packet_for_leaks(
        {"u": "https://example.com/cb?code=AAA&state=BBB"})


def test_scanner_flags_raw_query_string_with_sensitive_params():
    assert gate.scan_packet_for_leaks({"note": "?code=abc&state=def"})
    assert gate.scan_packet_for_leaks({"note": "&error=access_denied"})


def test_scanner_flags_raw_handle_and_long_digits():
    assert gate.scan_packet_for_leaks({"note": "@somehandle"})
    assert gate.scan_packet_for_leaks({"note": "id 123456789"})


def test_scanner_allows_safe_symbolic_placeholders():
    for ph in ("STATE_SYMBOLIC_MATCH", "CODE_SYMBOLIC_PRESENT",
               "ERROR_SYMBOLIC_ACCESS_DENIED", "CALLBACK_SYMBOLIC_REPLAY",
               "CHALLENGE_SYMBOLIC_S256_CLASS", "VERIFIER_SYMBOLIC_CLASS"):
        assert gate.scan_packet_for_leaks({"v": ph}) == [], ph


def test_scanner_allows_clean_docs_urls():
    ok = {"url": "https://docs.x.com/fundamentals/authentication/oauth-2-0/"
                 "authorization-code"}
    assert gate.scan_packet_for_leaks(ok) == []


def test_scanner_allows_known_git_sha():
    assert gate.scan_packet_for_leaks(
        {"commit": gate.SOURCE_BASELINE_COMMIT}) == []


# --------------------------------------------------------------------------- #
# Deterministic serialization
# --------------------------------------------------------------------------- #
def test_serialize_is_deterministic_and_sorted():
    a = gate.serialize({"b": 1, "a": 2})
    b = gate.serialize({"a": 2, "b": 1})
    assert a == b
    assert a.endswith("\n")
    assert a.index('"a"') < a.index('"b"')


def test_checksum_stable():
    p = gate.build_x_packet()
    assert gate.compute_checksum(p) == gate.compute_checksum(p)


# --------------------------------------------------------------------------- #
# Packet invariants
# --------------------------------------------------------------------------- #
def test_packet_core_fields():
    p = gate.build_x_packet()
    assert p["platform"] == "x"
    assert p["gate"] == gate.GATE
    assert p["official_docs_checked"] is True
    assert p["redirect_ledger_contract_status"] == "contract_only_no_real_flow"
    assert p["status"] == "pass"
    assert p["inherited_0174cx_commit"] == gate.INHERITED_0174CX_COMMIT


def test_official_docs_sources_present_and_clean():
    p = gate.build_x_packet()
    assert p["official_docs_sources"]
    assert gate.scan_packet_for_leaks(p["official_docs_sources"]) == []


def test_developer_portal_remains_blocker():
    p = gate.build_x_packet()
    assert p["developer_portal_access_status"] == \
        "gated_login_required_not_performed"
    assert p["access_tier_status"] == "not_verified"
    assert p["access_tier_blocker"]


# --------------------------------------------------------------------------- #
# Redirect ledger schema + allowed/forbidden fields
# --------------------------------------------------------------------------- #
def test_redirect_ledger_schema_contains_only_allowed_fields():
    p = gate.build_x_packet()
    schema_keys = set(p["redirect_ledger_schema"].keys())
    allowed = set(p["redirect_ledger_allowed_fields"])
    assert schema_keys == allowed


def test_redirect_ledger_forbidden_fields_complete():
    p = gate.build_x_packet()
    forbidden = set(p["redirect_ledger_forbidden_fields"])
    required_forbidden = {
        "raw_url", "callback_url", "raw_query", "query_string",
        "authorization_code", "auth_code", "code", "state",
        "error_description", "token", "access_token", "refresh_token",
        "bearer_token", "token_response", "client_id", "client_secret",
        "redirect_uri", "code_verifier", "code_challenge", "account_id",
        "user_id", "username", "screen_name", "handle", "post_id",
        "tweet_id", "community_id", "media_id", "place_id",
    }
    assert required_forbidden.issubset(forbidden)


def test_allowed_and_forbidden_fields_disjoint():
    p = gate.build_x_packet()
    allowed = set(p["redirect_ledger_allowed_fields"])
    forbidden = set(p["redirect_ledger_forbidden_fields"])
    assert allowed.isdisjoint(forbidden)


# --------------------------------------------------------------------------- #
# Callback fixture contract
# --------------------------------------------------------------------------- #
def test_callback_fixture_classes_complete():
    p = gate.build_x_packet()
    required = {
        "success_callback_symbolic",
        "denied_callback_symbolic",
        "missing_code_callback_symbolic",
        "missing_state_callback_symbolic",
        "state_mismatch_callback_symbolic",
        "duplicate_callback_symbolic",
        "expired_or_used_code_callback_symbolic",
        "malformed_callback_symbolic",
        "timeout_callback_symbolic",
        "unexpected_error_callback_symbolic",
    }
    assert set(p["callback_fixture_classes"]) == required
    assert set(p["callback_fixture_contract"].keys()) == required


def test_every_fixture_is_symbolic_only_and_safe():
    p = gate.build_x_packet()
    contract = p["callback_fixture_contract"]
    for name, fx in contract.items():
        assert fx["symbolic_inputs_only"] is True, name
        assert fx["expected_ledger_allowed_fields_only"] is True, name
        assert fx["expected_no_raw_url"] is True, name
        assert fx["expected_no_raw_query"] is True, name
        assert fx["expected_no_code"] is True, name
        assert fx["expected_no_state"] is True, name
        assert fx["expected_no_token"] is True, name
        assert fx["expected_token_exchange_blocked"] is True, name
    assert gate.scan_packet_for_leaks(contract) == []


def test_fixtures_have_complete_expected_class_keys():
    p = gate.build_x_packet()
    required_keys = {
        "fixture_name", "callback_class", "expected_terminal_result_class",
        "expected_state_match_class", "expected_code_present_class",
        "expected_denial_or_error_class", "expected_timeout_class",
        "expected_replay_detected_class", "expected_malformed_class",
        "expected_ledger_allowed_fields_only", "expected_no_raw_url",
        "expected_no_raw_query", "expected_no_code", "expected_no_state",
        "expected_no_token", "expected_token_exchange_blocked",
        "symbolic_inputs_only",
    }
    for name, fx in p["callback_fixture_contract"].items():
        assert required_keys.issubset(set(fx.keys())), name


def test_success_fixture_requires_match_and_present():
    p = gate.build_x_packet()
    fx = p["callback_fixture_contract"]["success_callback_symbolic"]
    assert fx["expected_state_match_class"] == "match"
    assert fx["expected_code_present_class"] == "present"


def test_duplicate_and_timeout_fixture_classes():
    p = gate.build_x_packet()
    dup = p["callback_fixture_contract"]["duplicate_callback_symbolic"]
    assert dup["expected_replay_detected_class"] == "replay_detected"
    tmo = p["callback_fixture_contract"]["timeout_callback_symbolic"]
    assert tmo["expected_timeout_class"] == "timed_out"


# --------------------------------------------------------------------------- #
# Policies
# --------------------------------------------------------------------------- #
def test_one_terminal_result_or_timeout_policy_present():
    p = gate.build_x_packet()
    pol = p["one_terminal_result_or_timeout_policy"]
    assert "exactly one terminal" in pol
    assert "never trigger token exchange" in pol


def test_replay_detection_policy_records_class_only():
    p = gate.build_x_packet()
    assert "only replay_detected_class" in p["replay_detection_policy"]


def test_state_match_policy_records_class_only():
    p = gate.build_x_packet()
    assert "never raw state" in p["state_match_policy"]


def test_code_presence_policy_records_class_only():
    p = gate.build_x_packet()
    assert "never the raw authorization code" in p["code_presence_policy"]


def test_denial_error_policy_records_class_only():
    p = gate.build_x_packet()
    assert "never raw" in p["denial_error_policy"]


def test_token_exchange_boundary_blocks_token_endpoint():
    p = gate.build_x_packet()
    pol = p["token_exchange_boundary_policy"]
    assert "remains blocked" in pol
    assert "must not call the token endpoint" in pol
    assert p["no_token_exchange_performed"] is True


def test_pkce_boundary_blocks_real_generation():
    p = gate.build_x_packet()
    pol = p["pkce_boundary_policy"]
    assert "out of scope" in pol
    assert "no real state/code_verifier/code_challenge generated" in pol
    assert p["no_state_generated"] is True
    assert p["no_code_verifier_generated"] is True
    assert p["no_code_challenge_generated"] is True


def test_all_no_live_flags_true():
    p = gate.build_x_packet()
    for key in (
        "no_live_call_performed", "no_credentials_read", "no_env_read",
        "no_account_binding_performed", "no_oauth_flow_performed",
        "no_authorize_url_opened", "no_browser_login_performed",
        "no_developer_portal_login_performed", "no_callback_server_started",
        "no_localhost_port_bound",
        "no_authorization_code_generated_or_received",
        "no_real_callback_url_processed", "no_state_generated",
        "no_code_verifier_generated", "no_code_challenge_generated",
        "no_token_exchange_performed", "no_token_persisted",
        "no_client_id_read", "no_client_secret_read", "no_posting_performed",
        "no_metrics_fetched", "no_webhook_created", "no_reply_dm_created",
        "no_scraping_performed", "no_autonomous_publishing",
        "redaction_verified",
    ):
        assert p[key] is True, key


def test_readme_is_clean():
    assert gate.scan_packet_for_leaks({"readme": gate.build_readme()}) == []


# --------------------------------------------------------------------------- #
# run_gate: fail-closed write behavior
# --------------------------------------------------------------------------- #
def test_run_gate_no_write_by_default(tmp_path):
    res = gate.run_gate(write=False, repo_root=str(tmp_path))
    assert res["write_requested"] is False
    assert res["packet_written"] is False
    assert res["readme_written"] is False
    assert not os.path.exists(
        os.path.join(str(tmp_path), gate.PACKET_REL_DIR, gate.PACKET_FILENAME))


def test_run_gate_writes_when_requested(tmp_path):
    res = gate.run_gate(write=True, repo_root=str(tmp_path))
    assert res["packet_written"] is True
    assert res["readme_written"] is True
    assert res["status"] == "pass"
    packet_path = os.path.join(
        str(tmp_path), gate.PACKET_REL_DIR, gate.PACKET_FILENAME)
    assert os.path.exists(packet_path)
    with open(packet_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["platform"] == "x"
    assert gate.scan_packet_for_leaks(data) == []


def test_run_gate_checksum_matches_serialized_packet(tmp_path):
    res = gate.run_gate(write=True, repo_root=str(tmp_path))
    packet_path = os.path.join(
        str(tmp_path), gate.PACKET_REL_DIR, gate.PACKET_FILENAME)
    with open(packet_path, "r", encoding="utf-8") as fh:
        on_disk = fh.read()
    import hashlib
    assert hashlib.sha256(on_disk.encode("utf-8")).hexdigest() == \
        res["packet_checksum"]


# --------------------------------------------------------------------------- #
# CLI wiring
# --------------------------------------------------------------------------- #
def test_cli_dry_run_outputs_json():
    proc = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "x-oauth-redirect-ledger-callback-fixture-contract-gate"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["platform"] == "x"
    assert payload["write_requested"] is False
    assert payload["packet_written"] is False
    assert payload["status"] == "pass"


def test_cli_write_flag_writes_packet():
    proc = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "x-oauth-redirect-ledger-callback-fixture-contract-gate",
         gate.FLAG_WRITE],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["write_requested"] is True
    assert payload["packet_written"] is True
    assert payload["status"] == "pass"
    written = os.path.join(
        REPO_ROOT, gate.PACKET_REL_DIR, gate.PACKET_FILENAME)
    assert os.path.exists(written)
