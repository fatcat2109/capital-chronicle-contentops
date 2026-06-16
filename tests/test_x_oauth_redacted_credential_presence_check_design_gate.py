"""Tests for the 0174DC X OAuth redacted credential presence-check DESIGN gate.

These tests prove the module is strictly local, design-only, and never imports
or references anything that could read credentials / env / env-file / config /
key-ring / browser store / network / browser / server / subprocess / socket /
shell history / source-control history. They also prove the gate is
fail-closed, deterministic, performs NO credential presence check, reads NO
credential source, emits NO real secret / token / hash / fingerprint / prefix /
suffix / source-name-with-value / redacted-from-real string, and that the
previous 0174CU..0174DB chain artifacts are not mutated by importing/running it.
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
    x_oauth_redacted_credential_presence_check_design_gate as gate)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "x_oauth_redacted_credential_presence_check_design_gate.py")


# --------------------------------------------------------------------------- #
# Import allow-list / forbidden imports (static AST analysis)
# --------------------------------------------------------------------------- #
ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re", "sys"}

FORBIDDEN_IMPORT_ROOTS = {
    "socket", "socketserver", "ssl", "asyncio", "selectors",
    "http", "wsgiref", "urllib", "requests", "httpx", "aiohttp",
    "webbrowser", "subprocess", "dotenv", "ftplib", "telnetlib",
    "smtplib", "multiprocessing", "threading",
    "configparser", "keyring", "getpass", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve",
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
        "configparser.", "keyring.", "getpass.", "ConfigParser",
        "open(os.path.expanduser", ".read_text(",
    ]
    for s in forbidden_substrings:
        assert s not in src, f"forbidden runtime string present: {s}"


def test_no_env_dotenv_config_keyring_access_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Access-shaped patterns only: bare descriptive words like "dotenv" /
    # "keyring" legitimately appear in key names and prose, so we ban the
    # call/access shapes, not the descriptive words.
    for s in ("os.environ", "os.getenv", "getenv(", "load_dotenv",
              "dotenv_values", "keyring.get", "keyring.set", "getpass.",
              "secretstorage.", "netrc(", "configparser.", "ConfigParser",
              "expanduser", "browser_cookie", "sqlite3."):
        assert s not in src, f"forbidden credential/env access string: {s}"


# --------------------------------------------------------------------------- #
# Packet structure / flags
# --------------------------------------------------------------------------- #
REQUIRED_TRUE_FLAGS = [
    "no_presence_check_performed",
    "no_credential_source_read",
    "no_live_call_performed",
    "no_network_call_performed",
    "no_credentials_read",
    "no_env_read",
    "no_dotenv_read",
    "no_config_read",
    "no_keyring_read",
    "no_browser_store_read",
    "no_client_id_read",
    "no_client_secret_read",
    "no_access_token_read",
    "no_refresh_token_read",
    "no_bearer_token_read",
    "no_token_exchange_performed",
    "no_token_response_seen",
    "no_token_persisted",
    "no_secret_material_persisted",
    "no_secret_hash_or_fingerprint_created",
    "no_secret_prefix_or_suffix_exposed",
    "no_account_identifier_read",
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
        "inherited_0174db_commit", "accepted_0174db_reference",
        "official_docs_checked", "official_docs_sources",
        "developer_portal_access_status", "access_tier_status",
        "redacted_presence_check_design_status",
        "credential_presence_check_execution_status",
        "credential_source_read_status", "allowed_future_presence_classes",
        "forbidden_future_presence_outputs", "redacted_boolean_output_contract",
        "source_abstraction_policy", "env_dotenv_config_boundary_policy",
        "secret_value_boundary_policy", "no_secret_hashing_policy",
        "no_secret_fingerprint_policy", "no_secret_prefix_suffix_policy",
        "no_env_name_value_pair_policy", "no_account_identifier_policy",
        "no_token_response_policy", "no_raw_error_policy",
        "fail_closed_result_class_policy",
        "future_presence_check_operator_go_policy",
        "future_presence_check_command_boundary",
        "required_before_real_presence_check", "required_before_token_exchange",
        "required_before_account_binding", "required_before_text_only_dry_run",
        "required_before_live", "blockers", "caveats", "recommended_next_task",
    ]
    for key in required:
        assert key in packet, f"missing required key: {key}"


def test_packet_identity_values():
    packet = gate.build_packet()
    assert packet["platform"] == "x"
    assert packet["source_baseline_commit"] == (
        "cc7b82cf23b6436888c3b09c181436fc992f2699")
    assert packet["inherited_0174db_commit"] == (
        "cc7b82cf23b6436888c3b09c181436fc992f2699")
    assert packet["redacted_presence_check_design_status"] == (
        "design_only_no_presence_check")


def test_design_status_and_execution_status():
    out = gate.run_gate(write=False)
    assert out["redacted_presence_check_design_status"] == (
        "design_only_no_presence_check")
    assert out["credential_presence_check_execution_status"] == "not_executed"
    assert out["credential_source_read_status"] == "not_read"
    assert out["status"] == "pass"


def test_developer_portal_and_access_tier_blocked():
    packet = gate.build_packet()
    assert packet["developer_portal_access_status"] == (
        "gated_login_required_not_performed")
    assert packet["access_tier_status"] == "not_verified"
    assert packet["redirect_uri_registration_status"] == (
        "not_verified_blocked")
    assert packet["client_type_resolution"] == (
        "unresolved_public_vs_confidential")


def test_token_exchange_account_binding_live_blocked():
    packet = gate.build_packet()
    assert "blocked" in packet["no_token_response_policy"].lower()
    assert packet["no_token_exchange_performed"] is True
    assert packet["no_account_binding_performed"] is True
    assert packet["no_autonomous_publishing"] is True


def test_no_presence_check_executed():
    packet = gate.build_packet()
    joined = " ".join(packet["explicit_non_actions"]).lower()
    assert "does not perform a credential presence check" in joined
    assert "does not validate that any credential exists" in joined
    assert packet["no_presence_check_performed"] is True
    assert packet["no_credential_source_read"] is True


def test_no_source_name_with_value_disclosure():
    packet = gate.build_packet()
    joined = " ".join(packet["explicit_non_actions"]).lower()
    assert "does not reveal credential source names with values" in joined
    assert "abstract" in packet["source_abstraction_policy"].lower()


def test_no_secret_hash_fingerprint_prefix_suffix():
    packet = gate.build_packet()
    assert packet["no_secret_hash_or_fingerprint_created"] is True
    assert packet["no_secret_prefix_or_suffix_exposed"] is True
    assert "never hashes" in packet["no_secret_hashing_policy"].lower()
    assert "fingerprint" in packet["no_secret_fingerprint_policy"].lower()
    assert "prefix" in packet["no_secret_prefix_suffix_policy"].lower()


def test_explicit_non_actions_present():
    packet = gate.build_packet()
    joined = " ".join(packet["explicit_non_actions"]).lower()
    for needle in [
        "does not perform a credential presence check",
        "does not read client id, client secret",
        "does not validate that any credential exists",
        "does not reveal credential source names with values",
        "does not reveal secret hashes, fingerprints, prefixes",
        "does not see token responses",
        "does not check x app existence",
        "does not check redirect uri registration",
        "does not perform oauth",
        "does not open an authorize url",
        "does not start a callback server",
        "does not exchange authorization code for token",
        "does not bind an x account",
        "separate explicit execution task and operator go",
    ]:
        assert needle in joined, f"missing explicit non-action: {needle}"


def test_allowed_future_presence_classes_are_symbolic():
    packet = gate.build_packet()
    for cls in packet["allowed_future_presence_classes"]:
        assert cls.endswith("_class")
        assert not re.search(r"\d{4,}", cls)


def test_fail_closed_result_classes_symbolic():
    packet = gate.build_packet()
    assert packet["fail_closed_result_classes"]
    for cls in packet["fail_closed_result_classes"]:
        assert cls.endswith("_class")
    assert "fail-closed" in packet["fail_closed_result_class_policy"].lower()
    assert "never falls open" in (
        packet["fail_closed_result_class_policy"].lower())


def test_future_presence_check_requires_separate_task_and_go():
    packet = gate.build_packet()
    assert "separate explicit execution task and operator GO" in (
        packet["future_presence_check_operator_go_policy"])
    pre = packet["required_before_real_presence_check"]
    joined_pre = " ".join(pre).lower()
    assert "operator explicit go" in joined_pre


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


def test_redaction_catches_env_assignment():
    bad = {"notes": "X_CLIENT_SECRET=supersecretvalue123"}
    assert any(v.startswith("env_assignment:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_secret_fingerprint_claim():
    bad = {"notes": "token fingerprint: ab12cd34"}
    assert any(v.startswith("secret_fingerprint_claim:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_redacted_from_real_claim():
    bad = {"notes": "the secret starts with abcd"}
    assert any(v.startswith("redacted_from_real_claim:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_last4_claim():
    bad = {"notes": "token last4: 7890"}
    assert any(v.startswith("redacted_from_real_claim:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_source_name_with_value():
    bad = {"notes": "credential source: vault_path=/secret/x"}
    assert any(v.startswith("source_name_with_value:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_handle():
    bad = {"notes": "bind to @somehandle now"}
    assert any(v.startswith("raw_handle:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_long_numeric_id():
    bad = {"notes": "user 1234567890 bound"}
    assert any(v.startswith("long_digits_possible_id:")
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
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DC"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([gate.PACKET_FILENAME, gate.README_FILENAME])
    # Written packet is valid JSON and redaction-clean.
    with open(out_dir / gate.PACKET_FILENAME, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert gate.scan_packet_for_leaks(data) == []
    assert data["redacted_presence_check_design_status"] == (
        "design_only_no_presence_check")


def test_written_packet_checksum_matches_reported(tmp_path):
    out = gate.run_gate(write=True, repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DC"
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
    sys.argv = ["live_contentops.cli",
                "x-oauth-redacted-credential-presence-check-design-gate"] + args
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
    assert "x-oauth-redacted-credential-presence-check-design-gate" in (
        cli.COMMANDS)


# --------------------------------------------------------------------------- #
# Prior chain must not be mutated by import/run
# --------------------------------------------------------------------------- #
def test_prior_chain_packets_exist_and_untouched():
    # Importing/running this gate must not require or modify prior packets.
    prior = [
        "0174CU", "0174CV", "0174CW", "0174CX", "0174CY", "0174CZ", "0174DA",
        "0174DB",
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
