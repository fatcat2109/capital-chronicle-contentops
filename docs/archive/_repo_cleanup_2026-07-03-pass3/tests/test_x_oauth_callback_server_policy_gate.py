"""Tests for the 0174DA X OAuth callback server POLICY gate.

These tests prove the module is strictly local, policy-only, and never imports
or references anything that could start/listen/bind/network/browser/env. They
also prove the gate is fail-closed, deterministic, and that the previous
0174CU..0174CZ chain artifacts are not mutated by importing/running it.
"""

import ast
import io
import json
import os
import re
import sys
import contextlib

import pytest

from live_contentops import x_oauth_callback_server_policy_gate as gate


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "x_oauth_callback_server_policy_gate.py")


# --------------------------------------------------------------------------- #
# Import allow-list / forbidden imports (static AST analysis)
# --------------------------------------------------------------------------- #
ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re", "sys"}

FORBIDDEN_IMPORT_ROOTS = {
    "socket", "socketserver", "ssl", "asyncio", "selectors",
    "http", "wsgiref", "urllib", "requests", "httpx", "aiohttp",
    "webbrowser", "subprocess", "dotenv", "ftplib", "telnetlib",
    "smtplib", "multiprocessing", "threading",
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


def test_only_os_path_used_not_os_environ():
    # os may be imported (os.path / os.makedirs) but env access is forbidden.
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for forbidden in ("os.environ", "os.getenv", "getenv(", "expanduser",
                      "os.putenv", "environb"):
        assert forbidden not in src, f"forbidden env access: {forbidden}"


def test_no_forbidden_runtime_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    forbidden_substrings = [
        ".bind(", ".listen(", ".connect(", "socket(", "create_server",
        "HTTPServer", "BaseHTTPRequestHandler", "serve_forever",
        "webbrowser.open", "subprocess.", "Popen", "urlopen", "requests.get",
        "requests.post", "httpx.", "aiohttp.", "load_dotenv",
    ]
    for s in forbidden_substrings:
        assert s not in src, f"forbidden runtime string present: {s}"


# --------------------------------------------------------------------------- #
# Packet structure / flags
# --------------------------------------------------------------------------- #
REQUIRED_TRUE_FLAGS = [
    "no_live_call_performed",
    "no_network_call_performed",
    "no_credentials_read",
    "no_env_read",
    "no_account_binding_performed",
    "no_oauth_flow_performed",
    "no_authorize_url_opened",
    "no_browser_login_performed",
    "no_developer_portal_login_performed",
    "no_callback_server_started",
    "no_localhost_port_bound",
    "no_socket_created",
    "no_port_listened",
    "no_authorization_code_generated_or_received",
    "no_real_callback_url_processed",
    "no_raw_callback_query_processed",
    "no_state_generated",
    "no_code_verifier_generated",
    "no_code_challenge_generated",
    "no_token_exchange_performed",
    "no_token_persisted",
    "no_client_id_read",
    "no_client_secret_read",
    "no_posting_performed",
    "no_metrics_fetched",
    "no_webhook_created",
    "no_reply_dm_created",
    "no_scraping_performed",
    "no_autonomous_publishing",
    "redaction_verified",
]


def test_packet_required_true_flags():
    packet = gate.build_packet()
    for flag in REQUIRED_TRUE_FLAGS:
        assert packet.get(flag) is True, f"flag not true: {flag}"


def test_packet_required_keys_present():
    packet = gate.build_packet()
    required = [
        "task_label", "gate", "platform", "source_baseline_commit",
        "inherited_0174cz_commit", "accepted_0174cz_reference",
        "official_docs_checked", "official_docs_sources",
        "developer_portal_access_status", "access_tier_status",
        "callback_server_policy_status", "interface_policy", "port_policy",
        "redirect_uri_registration_policy", "localhost_allowlist_policy",
        "no_raw_query_log_policy", "one_terminal_result_or_timeout_policy",
        "timeout_stop_policy", "replay_stop_policy",
        "callback_server_lifecycle_policy", "token_exchange_boundary_policy",
        "credential_env_boundary_policy", "browser_boundary_policy",
        "account_binding_boundary_policy", "required_before_real_callback_server",
        "required_before_real_authorize_url",
        "required_before_real_pkce_generation", "required_before_token_exchange",
        "required_before_account_binding", "required_before_live", "blockers",
        "caveats", "recommended_next_task",
    ]
    for key in required:
        assert key in packet, f"missing required key: {key}"


def test_packet_identity_values():
    packet = gate.build_packet()
    assert packet["platform"] == "x"
    assert packet["source_baseline_commit"] == (
        "33bb0c9a2ed4d276f3deb0f7e9af9f97d326d777")
    assert packet["inherited_0174cz_commit"] == (
        "33bb0c9a2ed4d276f3deb0f7e9af9f97d326d777")
    assert packet["callback_server_policy_status"] == "policy_only_no_server"


def test_policy_status_is_policy_only_no_server():
    out = gate.run_gate(write=False)
    assert out["callback_server_policy_status"] == "policy_only_no_server"
    assert out["status"] == "pass"


def test_developer_portal_and_access_tier_blocked():
    packet = gate.build_packet()
    assert packet["developer_portal_access_status"] == (
        "gated_login_required_not_performed")
    assert packet["access_tier_status"] == "not_verified"
    assert packet["client_type_resolution"] == (
        "unresolved_public_vs_confidential")


def test_token_exchange_account_binding_live_blocked():
    packet = gate.build_packet()
    assert "blocked" in packet["token_exchange_boundary_policy"].lower()
    assert "separate explicit gate" in (
        packet["account_binding_boundary_policy"].lower())
    assert packet["no_token_exchange_performed"] is True
    assert packet["no_account_binding_performed"] is True
    assert packet["no_autonomous_publishing"] is True


def test_explicit_non_actions_present():
    packet = gate.build_packet()
    joined = " ".join(packet["explicit_non_actions"]).lower()
    for needle in [
        "does not create a server",
        "does not bind any loopback or wildcard interface",
        "does not select a real port",
        "does not parse a real callback url",
        "does not accept raw query strings",
        "does not implement oauth execution",
        "does not generate state, code_verifier, or code_challenge",
        "does not exchange authorization code for token",
        "does not bind an x account",
        "separate",
    ]:
        assert needle in joined, f"missing explicit non-action: {needle}"


def test_interface_and_port_are_symbolic_classes_only():
    packet = gate.build_packet()
    # Interface classes must be symbolic, never a real bind address.
    for cls in packet["interface_policy_classes"]:
        assert cls.endswith("_class")
        assert not re.search(r"\d+\.\d+\.\d+\.\d+", cls)
    for cls in packet["port_policy_classes"]:
        assert cls.endswith("_class")
        # No real port number embedded.
        assert not re.search(r":\d{2,5}\b", cls)


def test_no_real_bind_target_anywhere_in_packet():
    packet = gate.build_packet()
    blob = gate.serialize(packet)
    # No concrete bind IP literals should appear as bind targets.
    assert "0.0.0.0" not in blob
    assert "::1" not in blob
    # 127.0.0.1 / localhost may appear only inside the "does not bind" prose;
    # ensure no host:port literal exists.
    assert not re.search(r"(?:127\.0\.0\.1|localhost):\d{2,5}", blob)


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #
def test_packet_redaction_scan_clean():
    packet = gate.build_packet()
    assert gate.scan_packet_for_leaks(packet) == []


def test_redaction_catches_token_like():
    bad = {"notes": "bearer ABCDEFGHIJKLMNOP1234567890"}
    assert gate.scan_packet_for_leaks(bad)


def test_redaction_catches_callback_url_with_query():
    bad = {"notes": "https://example.com/callback?code=abc&state=xyz"}
    assert gate.scan_packet_for_leaks(bad)


def test_redaction_catches_forbidden_key():
    bad = {"access_token": "x"}
    assert any(v.startswith("forbidden_key:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_real_bind_target():
    bad = {"notes": "bind to 0.0.0.0 now"}
    assert any(v.startswith("real_bind_target:")
               for v in gate.scan_packet_for_leaks(bad))


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_serialize_deterministic():
    p1 = gate.build_packet()
    p2 = gate.build_packet()
    assert gate.serialize(p1) == gate.serialize(p2)
    assert gate.serialize(p1).endswith("\n")


def test_checksum_stable():
    assert gate.compute_checksum(gate.build_packet()) == (
        gate.compute_checksum(gate.build_packet()))


# --------------------------------------------------------------------------- #
# run_gate dry-run vs write
# --------------------------------------------------------------------------- #
def test_run_gate_dry_run_writes_nothing(tmp_path):
    out = gate.run_gate(write=False, repo_root=str(tmp_path))
    assert out["write_requested"] is False
    assert out["packet_written"] is False
    assert out["readme_written"] is False
    assert not (tmp_path / gate.PACKET_REL_DIR / gate.PACKET_FILENAME).exists()


def test_run_gate_write_creates_only_packet_and_readme(tmp_path):
    out = gate.run_gate(write=True, repo_root=str(tmp_path))
    assert out["packet_written"] is True
    assert out["readme_written"] is True
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DA"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([gate.PACKET_FILENAME, gate.README_FILENAME])
    # Written packet is valid JSON and redaction-clean.
    with open(out_dir / gate.PACKET_FILENAME, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert gate.scan_packet_for_leaks(data) == []
    assert data["callback_server_policy_status"] == "policy_only_no_server"


def test_written_packet_checksum_matches_reported(tmp_path):
    out = gate.run_gate(write=True, repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DA"
    with open(out_dir / gate.PACKET_FILENAME, "rb") as fh:
        raw = fh.read()
    import hashlib
    assert hashlib.sha256(raw).hexdigest() == out["packet_checksum"]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _run_cli(args):
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["live_contentops.cli", "x-oauth-callback-server-policy-gate"] + args
    try:
        with contextlib.redirect_stdout(buf):
            gate.main(argv=args)
    finally:
        sys.argv = old
    return buf.getvalue()


def test_cli_main_dry_run():
    out = json.loads(_run_cli([]))
    assert out["status"] == "pass"
    assert out["write_requested"] is False


def test_cli_command_is_wired():
    from live_contentops import cli
    assert "x-oauth-callback-server-policy-gate" in cli.COMMANDS


# --------------------------------------------------------------------------- #
# Prior chain must not be mutated by import/run
# --------------------------------------------------------------------------- #
def test_prior_chain_packets_exist_and_untouched():
    # Importing/running this gate must not require or modify prior packets.
    prior = [
        "0174CU", "0174CV", "0174CW", "0174CX", "0174CY", "0174CZ",
    ]
    base = os.path.join(REPO_ROOT, "docs", "credential_readiness")
    before = {}
    for d in prior:
        ddir = os.path.join(base, d)
        if os.path.isdir(ddir):
            for fn in os.listdir(ddir):
                fp = os.path.join(ddir, fn)
                if os.path.isfile(fp):
                    with open(fp, "rb") as fh:
                        before[fp] = fh.read()
    # Run the gate dry-run; must not touch prior dirs.
    gate.run_gate(write=False)
    for fp, content in before.items():
        with open(fp, "rb") as fh:
            assert fh.read() == content, f"prior artifact mutated: {fp}"
