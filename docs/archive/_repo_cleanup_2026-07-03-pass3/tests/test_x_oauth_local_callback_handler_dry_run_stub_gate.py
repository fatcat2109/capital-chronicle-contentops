"""Tests for the 0174CZ X OAuth local callback handler dry-run stub gate.

These tests enforce the strictly-local, dry-run-stub-only posture: no network /
browser / subprocess / http-server / env imports, strong redaction,
deterministic output, fail-closed writes, a pure-function symbolic callback
handler, and correct CLI wiring. No OAuth flow, callback server, port bind,
token, state/PKCE material, real callback URL, raw query, or account binding is
ever performed.
"""

import ast
import json
import os
import subprocess
import sys

import pytest

from live_contentops import (
    x_oauth_local_callback_handler_dry_run_stub_gate as gate)

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
    assert gate.scan_packet_for_leaks(gate.build_packet()) == []


def test_scanner_flags_token_like_value():
    assert gate.scan_packet_for_leaks(
        {"note": "ghp_abcdefghijklmnopqrstuvwxyz0123"})


def test_scanner_flags_bearer_token():
    assert gate.scan_packet_for_leaks(
        {"note": "Authorization: Bearer abcdef0123456789abcdef"})


def test_scanner_flags_auth_code_value_as_forbidden_key():
    assert gate.scan_packet_for_leaks({"authorization_code": "x"})


def test_scanner_flags_raw_state_key():
    assert gate.scan_packet_for_leaks({"state": "x"})


def test_scanner_flags_code_verifier_and_challenge_keys():
    assert gate.scan_packet_for_leaks({"code_verifier": "x"})
    assert gate.scan_packet_for_leaks({"code_challenge": "x"})


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
    p = gate.build_packet()
    assert gate.compute_checksum(p) == gate.compute_checksum(p)


# --------------------------------------------------------------------------- #
# Packet invariants
# --------------------------------------------------------------------------- #
def test_packet_core_fields():
    p = gate.build_packet()
    assert p["platform"] == "x"
    assert p["gate"] == gate.GATE
    assert p["official_docs_checked"] is True
    assert p["local_callback_handler_stub_status"] == \
        "dry_run_stub_only_no_real_callback"
    assert p["status"] == "pass"
    assert p["inherited_0174cy_commit"] == gate.INHERITED_0174CY_COMMIT


def test_official_docs_sources_present_and_clean():
    p = gate.build_packet()
    assert p["official_docs_sources"]
    assert gate.scan_packet_for_leaks(p["official_docs_sources"]) == []


def test_developer_portal_remains_blocker():
    p = gate.build_packet()
    assert p["developer_portal_access_status"] == \
        "gated_login_required_not_performed"
    assert p["access_tier_status"] == "not_verified"
    assert p["access_tier_blocker"]


def test_accepted_0174cy_contract_reference_present():
    p = gate.build_packet()
    assert "0174CY" in p["accepted_0174cy_contract_reference"]
    assert "X_OAUTH_REDIRECT_LEDGER_CALLBACK_FIXTURE_CONTRACT_0174CY" in \
        p["accepted_0174cy_contract_reference"]


# --------------------------------------------------------------------------- #
# Symbolic callback events + handler outputs
# --------------------------------------------------------------------------- #
def test_symbolic_callback_events_include_all_classes():
    events = gate.build_symbolic_callback_events()
    classes = {e["callback_class"] for e in events}
    assert classes == set(gate.CALLBACK_CLASSES)


def test_handler_outputs_include_all_classes():
    outputs = gate.build_symbolic_handler_outputs()
    classes = {o["callback_class"] for o in outputs.values()}
    assert classes == set(gate.CALLBACK_CLASSES)


def test_handler_outputs_use_only_allowed_ledger_fields():
    allowed = set(gate.ALLOWED_LEDGER_OUTPUT_FIELDS)
    for name, out in gate.build_symbolic_handler_outputs().items():
        assert set(out.keys()) == allowed, name
        assert gate.validate_ledger_output(out) == [], name


def test_handler_outputs_have_no_forbidden_ledger_fields():
    forbidden = set(gate.FORBIDDEN_LEDGER_OUTPUT_FIELDS)
    for name, out in gate.build_symbolic_handler_outputs().items():
        assert set(out.keys()).isdisjoint(forbidden), name


def test_handler_maps_success():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "success_callback_symbolic",
        "callback_class": "success_code_present_state_match",
        "state_match_class": "match",
        "code_present_class": "present",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "success_terminal"
    assert out["state_match_class"] == "match"
    assert out["code_present_class"] == "present"
    assert out["token_exchange_blocked"] is True
    assert out["status"] == "pass"


def test_handler_maps_denial():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "denied_callback_symbolic",
        "callback_class": "user_denied_or_declined",
        "denial_or_error_class": "user_denied",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "denied_terminal"
    assert out["denial_or_error_class"] == "user_denied"
    assert out["token_exchange_blocked"] is True


def test_handler_maps_missing_code():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["code_present_class"] == "missing"


def test_handler_maps_missing_state():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_state",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["state_match_class"] == "missing"


def test_handler_maps_state_mismatch():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "state_mismatch",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["state_match_class"] == "mismatch"


def test_handler_maps_duplicate_replay():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x",
        "callback_class": "duplicate_or_replayed_callback",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "replay_terminal"
    assert out["replay_detected_class"] == "replay_detected"


def test_handler_maps_expired_used_code():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x",
        "callback_class": "expired_or_used_authorization_code",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["code_present_class"] == "expired"


def test_handler_maps_malformed():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "malformed_callback",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["malformed_class"] == "malformed"


def test_handler_maps_timeout():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "timeout_no_callback",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "timeout_terminal"
    assert out["timeout_class"] == "timed_out"
    assert out["callback_received"] is False


def test_handler_maps_unexpected_error():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "unexpected_error_redacted",
        "symbolic_inputs_only": True,
    })
    assert out["terminal_result_class"] == "error_terminal"
    assert out["denial_or_error_class"] == "unexpected"


def test_every_output_sets_one_terminal_and_no_raw_and_token_blocked():
    for name, out in gate.build_symbolic_handler_outputs().items():
        assert out["one_terminal_result_or_timeout"] is True, name
        assert out["token_exchange_blocked"] is True, name
        for flag in (
            "redaction_verified", "no_raw_callback_url_persisted",
            "no_raw_query_persisted", "no_authorization_code_persisted",
            "no_state_persisted", "no_error_description_persisted",
            "no_token_persisted", "no_account_identifier_persisted",
        ):
            assert out[flag] is True, f"{name}:{flag}"


# --------------------------------------------------------------------------- #
# Handler rejection (fail-closed, no raw echo)
# --------------------------------------------------------------------------- #
def test_handler_rejects_forbidden_input_key_without_echo():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
        "authorization_code": "SUPERSECRETCODEVALUE",
    })
    assert out["status"] == "fail_closed"
    assert out["callback_class"] == "rejected_redacted"
    assert gate.scan_packet_for_leaks(out) == []
    assert "SUPERSECRETCODEVALUE" not in json.dumps(out)


def test_handler_rejects_raw_callback_url_with_query():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "success_code_present_state_match",
        "symbolic_inputs_only": True,
        "code_present_class": "https://cb.example/x?code=AAA&state=BBB",
    })
    assert out["status"] == "fail_closed"
    assert gate.scan_packet_for_leaks(out) == []


def test_handler_rejects_raw_query_string():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
        "state_match_class": "?code=abc&state=def",
    })
    assert out["status"] == "fail_closed"
    assert gate.scan_packet_for_leaks(out) == []


def test_handler_rejects_token_like_value():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
        "denial_or_error_class": "ghp_abcdefghijklmnopqrstuvwxyz0123",
    })
    assert out["status"] == "fail_closed"
    assert gate.scan_packet_for_leaks(out) == []


def test_handler_rejects_raw_handle():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
        "denial_or_error_class": "@realhandle",
    })
    assert out["status"] == "fail_closed"
    assert gate.scan_packet_for_leaks(out) == []


def test_handler_rejects_long_numeric_id():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True,
        "denial_or_error_class": "1234567890",
    })
    assert out["status"] == "fail_closed"
    assert gate.scan_packet_for_leaks(out) == []


def test_handler_rejects_missing_symbolic_flag():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
    })
    assert out["status"] == "fail_closed"
    assert "symbolic_inputs_only_not_true" in out["blocked_reasons"]


def test_handler_rejects_unknown_callback_class():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "totally_unknown",
        "symbolic_inputs_only": True,
    })
    assert out["status"] == "fail_closed"
    assert "unknown_callback_class" in out["blocked_reasons"]


def test_rejected_output_still_uses_allowed_fields_only():
    out = gate.handle_symbolic_callback_event({
        "fixture_name": "x", "callback_class": "missing_code",
        "symbolic_inputs_only": True, "token": "x",
    })
    assert set(out.keys()) == set(gate.ALLOWED_LEDGER_OUTPUT_FIELDS)


# --------------------------------------------------------------------------- #
# No-live flags
# --------------------------------------------------------------------------- #
def test_all_no_live_flags_true():
    p = gate.build_packet()
    for key in (
        "no_live_call_performed", "no_credentials_read", "no_env_read",
        "no_account_binding_performed", "no_oauth_flow_performed",
        "no_authorize_url_opened", "no_browser_login_performed",
        "no_developer_portal_login_performed", "no_callback_server_started",
        "no_localhost_port_bound",
        "no_authorization_code_generated_or_received",
        "no_real_callback_url_processed", "no_raw_callback_query_processed",
        "no_state_generated", "no_code_verifier_generated",
        "no_code_challenge_generated", "no_token_exchange_performed",
        "no_token_persisted", "no_client_id_read", "no_client_secret_read",
        "no_posting_performed", "no_metrics_fetched", "no_webhook_created",
        "no_reply_dm_created", "no_scraping_performed",
        "no_autonomous_publishing", "redaction_verified",
    ):
        assert p[key] is True, key


def test_token_exchange_boundary_blocks_token_endpoint():
    p = gate.build_packet()
    pol = p["token_exchange_boundary_policy"]
    assert "remains blocked" in pol
    assert "never calls the token" in pol
    assert p["no_token_exchange_performed"] is True


def test_pkce_boundary_blocks_real_generation():
    p = gate.build_packet()
    pol = p["pkce_boundary_policy"]
    assert "out of scope" in pol
    assert "no real state/code_verifier/code_challenge generated" in pol


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
         "x-oauth-local-callback-handler-dry-run-stub-gate"],
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
         "x-oauth-local-callback-handler-dry-run-stub-gate",
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
