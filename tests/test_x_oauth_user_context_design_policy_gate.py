"""Tests for the 0174CW X OAuth user-context design and redirection policy gate.

These tests enforce the strictly-local, design-only posture: no network /
browser / subprocess / env imports, strong redaction, deterministic output,
fail-closed writes, and correct CLI wiring. No OAuth flow, token, or account
binding is ever performed.
"""

import ast
import json
import os
import subprocess
import sys

import pytest

from live_contentops import x_oauth_user_context_design_policy_gate as gate

MODULE_PATH = gate.__file__
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- #
# Static safety: import allow-list
# --------------------------------------------------------------------------- #
_ALLOWED_IMPORTS = {"hashlib", "json", "os.path", "os", "re", "sys"}
_FORBIDDEN_IMPORT_SUBSTRINGS = (
    "urllib", "requests", "httpx", "socket", "http", "dotenv",
    "webbrowser", "subprocess", "ssl", "ftplib", "telnetlib", "aiohttp",
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


def test_no_forbidden_network_or_browser_imports():
    names = _imported_names()
    for forbidden in _FORBIDDEN_IMPORT_SUBSTRINGS:
        assert not any(forbidden == n.split(".")[0] for n in names), (
            f"forbidden import present: {forbidden}"
        )


def test_source_has_no_env_or_network_calls():
    src = _module_source()
    for needle in (
        "os.environ", "os.getenv", "getenv", "Path.home", "expanduser",
        "urlopen", "requests.", "httpx.", "socket.", "webbrowser.",
        "subprocess.", "Popen", "system(",
    ):
        assert needle not in src, f"forbidden runtime call present: {needle}"


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_clean_packet_has_no_violations():
    assert gate.scan_packet_for_leaks(gate.build_x_packet()) == []


def test_scanner_flags_bearer_token():
    bad = {"note": "Authorization: Bearer abcdef0123456789abcdef"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_forbidden_keys():
    for key in ("access_token", "client_secret", "code_verifier", "state",
                "authorization_code", "redirect_uri"):
        assert gate.scan_packet_for_leaks({key: "x"}), key


def test_scanner_flags_callback_url_with_query():
    bad = {"u": "https://example.com/cb?code=AAA&state=BBB"}
    assert gate.scan_packet_for_leaks(bad)


def test_scanner_flags_raw_handle_and_long_digits():
    assert gate.scan_packet_for_leaks({"note": "@somehandle"})
    assert gate.scan_packet_for_leaks({"note": "id 123456789"})


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
    assert p["oauth_design_status"] == "design_only_no_flow"
    assert p["status"] == "pass"


def test_packet_no_live_flags_all_true():
    p = gate.build_x_packet()
    for key in (
        "no_live_call_performed", "no_credentials_read", "no_env_read",
        "no_account_binding_performed", "no_oauth_flow_performed",
        "no_authorize_url_opened", "no_browser_login_performed",
        "no_developer_portal_login_performed",
        "no_authorization_code_generated_or_received",
        "no_code_verifier_generated", "no_code_challenge_generated",
        "no_state_generated", "no_token_exchange_performed",
        "no_token_persisted", "no_client_id_read", "no_client_secret_read",
        "no_posting_performed", "no_autonomous_publishing",
    ):
        assert p[key] is True, key


def test_scope_policy_least_privilege():
    p = gate.build_x_packet()
    assert "tweet.write" in p["allowed_scope_classes_for_future_design"]
    assert "dm.write" in p["forbidden_scope_classes_until_scoped"]
    # offline.access must not be silently allowed.
    assert "offline.access" not in p["allowed_scope_classes_for_future_design"]


def test_docs_sources_clean_and_present():
    p = gate.build_x_packet()
    assert p["official_docs_sources"]
    assert gate.scan_packet_for_leaks(p["official_docs_sources"]) == []


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
    # The on-disk packet serialization must hash to the reported checksum.
    import hashlib
    assert hashlib.sha256(on_disk.encode("utf-8")).hexdigest() == \
        res["packet_checksum"]


def test_readme_is_clean():
    assert gate.scan_packet_for_leaks({"readme": gate.build_readme()}) == []


# --------------------------------------------------------------------------- #
# CLI wiring
# --------------------------------------------------------------------------- #
def test_cli_dry_run_outputs_json():
    proc = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "x-oauth-user-context-design-policy-gate"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["platform"] == "x"
    assert payload["write_requested"] is False
    assert payload["packet_written"] is False


def test_cli_write_flag_writes_packet():
    proc = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli",
         "x-oauth-user-context-design-policy-gate",
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
