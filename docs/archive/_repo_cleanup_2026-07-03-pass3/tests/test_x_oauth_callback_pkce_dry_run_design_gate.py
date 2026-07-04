"""Tests for the 0174CX X OAuth callback + PKCE dry-run design gate.

These tests enforce the strictly-local, design-only posture: no network /
browser / subprocess / http-server / env imports, strong redaction,
deterministic output, fail-closed writes, and correct CLI wiring. No OAuth
flow, callback server, port bind, token, state/PKCE material, or account
binding is ever performed.
"""

import ast
import json
import os
import subprocess
import sys

import pytest

from live_contentops import x_oauth_callback_pkce_dry_run_design_gate as gate

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
    bad = {"note": "ghp_abcdefghijklmnopqrstuvwxyz0123"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_bearer_token():
    bad = {"note": "Authorization: Bearer abcdef0123456789abcdef"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_auth_code_and_forbidden_keys():
    for key in ("access_token", "client_secret", "code_verifier", "state",
                "authorization_code", "redirect_uri", "code_challenge",
                "code", "error_description", "raw_query", "query_string"):
        assert gate.scan_packet_for_leaks({key: "x"}), key


def test_scanner_flags_callback_url_with_query():
    bad = {"u": "https://example.com/cb?code=AAA&state=BBB"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_raw_query_string_with_sensitive_params():
    assert gate.scan_packet_for_leaks({"note": "?code=abc&state=def"})
    assert gate.scan_packet_for_leaks({"note": "&error=access_denied"})


def test_scanner_flags_raw_handle_and_long_digits():
    assert gate.scan_packet_for_leaks({"note": "@somehandle"})
    assert gate.scan_packet_for_leaks({"note": "id 123456789"})


def test_scanner_allows_safe_symbolic_placeholders():
    for ph in ("STATE_SYMBOLIC_MATCH", "CODE_SYMBOLIC_PRESENT",
               "ERROR_SYMBOLIC_ACCESS_DENIED"):
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
    assert p["callback_pkce_design_status"] == "design_only_no_real_flow"
    assert p["status"] == "pass"
    assert p["inherited_0174cw_commit"] == gate.INHERITED_0174CW_COMMIT


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


def test_callback_server_policy_forbids_starting_now():
    p = gate.build_x_packet()
    assert "starts NO server" in p["callback_server_policy"]
    assert p["no_callback_server_started"] is True


def test_localhost_binding_policy_forbids_binding_now():
    p = gate.build_x_packet()
    assert "no localhost port is bound now" in p["localhost_binding_policy"]
    assert p["no_localhost_port_bound"] is True


def test_browser_open_policy_forbids_now():
    p = gate.build_x_packet()
    assert "no browser opened now" in p["browser_open_policy"]
    assert p["no_browser_login_performed"] is True


def test_authorize_url_policy_forbids_open_and_raw_persist():
    p = gate.build_x_packet()
    pol = p["authorize_url_policy"]
    assert "no authorize URL constructed or opened now" in pol
    assert "never persisted raw" in pol
    assert p["no_authorize_url_opened"] is True


def test_callback_query_policy_forbids_raw_query_persistence():
    p = gate.build_x_packet()
    assert "redact ALL query parameters" in p["callback_query_policy"]


def test_callback_event_classes_include_all_required():
    p = gate.build_x_packet()
    required = {
        "success_code_present_state_match",
        "user_denied_or_declined",
        "missing_code",
        "missing_state",
        "state_mismatch",
        "duplicate_or_replayed_callback",
        "expired_or_used_authorization_code",
        "malformed_callback",
        "timeout_no_callback",
        "unexpected_error_redacted",
    }
    assert required.issubset(set(p["callback_event_classes"]))


def test_state_policy_forbids_generation_and_raw_log():
    p = gate.build_x_packet()
    assert "generates NO state" in p["state_parameter_policy"]
    assert p["no_state_generated"] is True


def test_pkce_policy_forbids_generation_and_raw_log():
    p = gate.build_x_packet()
    assert "NO real PKCE material" in p["pkce_policy"]
    assert "never logged or persisted raw" in p["code_verifier_policy"]
    assert "never stored raw" in p["code_challenge_policy"]
    assert p["no_code_verifier_generated"] is True
    assert p["no_code_challenge_generated"] is True


def test_token_exchange_boundary_blocks_token_endpoint():
    p = gate.build_x_packet()
    pol = p["token_exchange_boundary_policy"]
    assert "OUT OF SCOPE and blocked" in pol
    assert "calls no token endpoint" in pol
    assert p["no_token_exchange_performed"] is True


def test_symbolic_fixtures_only_safe_placeholders():
    p = gate.build_x_packet()
    fixtures = p["symbolic_dry_run_fixtures"]
    assert set(fixtures) == {
        "success_callback_symbolic",
        "denied_callback_symbolic",
        "missing_state_callback_symbolic",
        "state_mismatch_callback_symbolic",
        "duplicate_callback_symbolic",
        "malformed_callback_symbolic",
        "timeout_callback_symbolic",
    }
    # Fixtures must not introduce any redaction violations.
    assert gate.scan_packet_for_leaks(fixtures) == []


def test_required_before_real_callback_server_contains_go_and_allowlist():
    p = gate.build_x_packet()
    joined = " ".join(p["required_before_real_callback_server"]).lower()
    assert "operator" in joined and "go" in joined
    assert "allowlisted localhost" in joined


def test_required_before_real_authorize_url_contains_core_policies():
    p = gate.build_x_packet()
    joined = " ".join(p["required_before_real_authorize_url"]).lower()
    assert "client id" in joined
    assert "redirect uri" in joined
    assert "state policy" in joined
    assert "pkce policy" in joined


def test_required_before_token_exchange_contains_redaction_and_budget():
    p = gate.build_x_packet()
    joined = " ".join(p["required_before_token_exchange"]).lower()
    assert "callback success" in joined
    assert "state match" in joined
    assert "redaction ledger" in joined
    assert "call budget" in joined and "no-retry" in joined


def test_required_before_live_contains_full_gate_chain():
    p = gate.build_x_packet()
    joined = " ".join(p["required_before_live"]).lower()
    for needle in ("credential-readiness", "account-binding", "dry-run",
                   "payload hash", "one-time live go", "duplicate-send",
                   "pre-attempt marker", "request_budget=1", "no retry",
                   "redacted post-send ledger"):
        assert needle in joined, needle


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
         "x-oauth-callback-pkce-dry-run-design-gate"],
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
         "x-oauth-callback-pkce-dry-run-design-gate",
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
